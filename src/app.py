import asyncio
import datetime as dt
import os

import httpx
from langsmith.wrappers import wrap_openai
from openai import AsyncOpenAI
from scheduler.asyncio import Scheduler
from scheduler.trigger import Monday

from src.ai.reporting import (
    generate_en_match_report,
    generate_match_overview,
    generate_report_tts_audio,
    translate_match_report,
)
from src.discord_bot import DiscordMessenger, create_discord_messenger
from src.kb import refresh_kb_data as refresh_kb_data_files
from src.logger import log
from src.models import NormalizedPlayerData, PlayerData
from src.report_export import render_pdf_pages_to_png, save_match_report
from src.requests import opendota
from src.storage import DataStorage
from src.utils import (
    build_match_report_dir,
    load_player_config,
    require_env,
    tracked_players_heroes_text,
)

PLAYER_ID, PLAYERS, PLAYER_ID_DISCORD_ID = load_player_config()
AI_MODEL = "gpt-5.5"
OVERVIEW_MODEL = "gpt-5.4-mini"
RECENT_MATCHES_CONTEXT_LIMIT = int(require_env("RECENT_MATCHES_CONTEXT_LIMIT"))
VOICE_CHANNEL_ID = int(require_env("VOICE_CHANNEL_ID"))


async def main(
    client: httpx.AsyncClient,
    storage: DataStorage,
    ai: AsyncOpenAI,
    discord_messenger: DiscordMessenger,
) -> None:
    try:
        match = await opendota.get_last_match(client, PLAYER_ID)
    except opendota.OpenDotaRequestError as exc:
        log.warning(f"Failed to fetch last match: {exc!s}")
        return

    last_match_id = storage.get_last_match_id()

    if last_match_id == match.match_id:
        log.debug(f"Match {match.match_id} already processed.")
        return

    log.info(f"New match ID={match.match_id} at {dt.datetime.fromtimestamp(match.start_time)} found.")

    storage.add_match(match)
    try:
        match_details = await opendota.get_match_details(client, match.match_id)
    except opendota.OpenDotaRequestError as exc:
        log.warning(f"Failed to fetch match details for {match.match_id}: {exc}")
        return

    players_data = [PlayerData.model_validate(p) for p in match_details["players"]]
    target_player_ids = {str(player_id) for player_id in PLAYERS}
    filtered_players_data = [
        p for p in players_data if p.account_id is not None and str(p.account_id) in target_player_ids
    ]
    all_normalized_players_data = [NormalizedPlayerData.from_player_data(p) for p in players_data]
    tracked_normalized_players_data = [NormalizedPlayerData.from_player_data(p) for p in filtered_players_data]
    matched_friend_ids = [str(p.account_id) for p in filtered_players_data if p.account_id is not None]
    tracked_players_context = [
        {
            "account_id": str(player.account_id),
            "personaname": player.personaname,
            "hero_name": player.hero_name,
        }
        for player in tracked_normalized_players_data
        if player.account_id is not None
    ]
    tracked_heroes_text = tracked_players_heroes_text(
        tracked_players_data=tracked_normalized_players_data,
        player_id_discord_id=PLAYER_ID_DISCORD_ID,
    )
    heroes_section = f"Герои:\n{tracked_heroes_text}" if tracked_heroes_text else ""
    discord_message_id: int

    log.info(f"Found [{len(filtered_players_data)} / {len(PLAYERS)}] players in the match.")
    try:
        discord_message_id = await discord_messenger.send_message(
            f"🟡 Новый матч `{match.match_id}`\nИгроки: `{len(filtered_players_data)}/{len(PLAYERS)}`\n{heroes_section}"
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to send initial Discord status message: {exc}") from exc

    if not matched_friend_ids:
        log.info("No tracked friends found in this match. Skipping LLM analysis.")
        try:
            await discord_messenger.append_to_message(
                discord_message_id,
                "\n⚪ Нет отслеживаемых игроков. Пропускаю ИИ-анализ.",
            )
        except Exception as exc:
            log.warning(f"Failed to update Discord status message: {exc}")
        return

    log.info(f"Generating AI match analysis via {AI_MODEL}...")
    recent_overviews_by_player = storage.get_recent_player_overviews(
        player_ids=matched_friend_ids,
        limit=RECENT_MATCHES_CONTEXT_LIMIT,
    )
    recent_games_briefs = {
        player_id: "\n".join(f"- {overview}" for overview in overviews)
        for player_id, overviews in recent_overviews_by_player.items()
        if overviews
    } or None
    try:
        await discord_messenger.append_to_message(
            discord_message_id,
            f"\n[1/4] 🤖 ИИ анализирует (`{AI_MODEL}`)...",
        )
    except Exception as exc:
        log.warning(f"Failed to update Discord status message: {exc}")

    async with discord_messenger.typing_status():
        en_report = await generate_en_match_report(
            ai=ai,
            model=AI_MODEL,
            target_player_ids=PLAYERS,
            matched_friend_ids=matched_friend_ids,
            all_players_data=[
                player.model_dump(mode="json", exclude_none=True) for player in all_normalized_players_data
            ],
            match_metadata={
                "match_id": match.match_id,
                "start_time": match.start_time,
                "duration_seconds": match.duration,
                "radiant_win": match.radiant_win,
                "game_mode": "turbo",  # always turbo
                "objectives": match_details.get("objectives"),
            },
            recent_games_briefs=recent_games_briefs,
        )
        try:
            await discord_messenger.append_to_message(
                discord_message_id,
                "\n[2/4] 📥 Отчет получен.",
            )
        except Exception as exc:
            log.warning(f"Failed to update Discord status message: {exc}")
        translated_text = await translate_match_report(
            ai=ai,
            model=AI_MODEL,
            text=en_report,
        )
        try:
            await discord_messenger.append_to_message(
                discord_message_id,
                "\n[3/4] 🌐 Отчет переведен.",
            )
        except Exception as exc:
            log.warning(f"Failed to update Discord status message: {exc}")

    log.info("AI Agent match analysis is ready. Saving report...")
    report_dir = build_match_report_dir(match_id=match.match_id, match_start_time=match.start_time)
    report_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = report_dir / "report.md"
    pdf_path = report_dir / "report.pdf"
    markdown_path, pdf_path = save_match_report(
        markdown_text=translated_text,
        markdown_path=markdown_path,
        pdf_path=pdf_path,
    )
    try:
        await discord_messenger.append_to_message(
            discord_message_id,
            "\n[4/4] ✅ Готово. Файлы прикреплены. Тренируйтесь!",
        )
        image_paths = render_pdf_pages_to_png(pdf_path=pdf_path, output_dir=report_dir)
        await discord_messenger.attach_images_to_message(discord_message_id, [str(path) for path in image_paths])
    except Exception as exc:
        log.warning(f"Failed to update Discord status message: {exc}")

    report_wav_path = report_dir / "report.wav"
    try:
        report_wav_path = await generate_report_tts_audio(
            ai=ai,
            text=translated_text,
            output_path=report_wav_path,
        )
        log.info(f"Voice report audio saved: {report_wav_path}")
    except Exception as exc:
        report_wav_path = None
        log.warning(f"Failed to generate voice report for match {match.match_id}: {exc}")

    if report_wav_path is not None:
        try:
            await discord_messenger.play_wav_in_voice_channel(
                voice_channel_id=VOICE_CHANNEL_ID,
                wav_path=report_wav_path,
            )
            log.info(f"Voice report playback completed: {report_wav_path}")
        except Exception as exc:
            log.warning(f"Failed to play voice report for match {match.match_id}: {exc}")

    log.info(f"Report saved: {markdown_path}")
    log.info(f"PDF saved: {pdf_path}")
    # post-process report
    try:
        overview = await generate_match_overview(
            ai=ai,
            model=OVERVIEW_MODEL,
            en_report=en_report,
            tracked_players=tracked_players_context,
        )
        if overview:
            storage.set_match_overview(match.match_id, overview)
            log.info(f"Match overview saved for {match.match_id}")
        else:
            log.warning(f"No valid player overviews generated for {match.match_id}")
    except Exception as exc:
        log.warning(f"Failed to generate/save match overview for {match.match_id}: {exc}")


async def refresh_kb_data(client: httpx.AsyncClient) -> None:
    await refresh_kb_data_files(client)
    log.info("KB data refreshed and mappings reloaded.")


async def start() -> None:
    tz = dt.UTC
    sched = Scheduler(tzinfo=tz)
    client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))
    ai = wrap_openai(AsyncOpenAI())
    storage = DataStorage("data.json")
    discord_messenger = create_discord_messenger(
        bot_token=os.getenv("DISCORD_BOT_TOKEN"),
        channel_id_raw=os.getenv("DISCORD_CHANNEL_ID"),
    )
    if discord_messenger is None:
        raise RuntimeError("Discord messenger creation failed. Check DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID.")
    asyncio.create_task(discord_messenger.start())
    log.info("Discord bot startup task created.")

    sched.cyclic(
        timing=dt.timedelta(seconds=30),
        handle=main,
        args=(client, storage, ai, discord_messenger),
        skip_missing=True,
    )
    sched.weekly(timing=Monday(dt.time(tzinfo=tz)), handle=refresh_kb_data, args=(client,))

    while True:
        await asyncio.sleep(1)
