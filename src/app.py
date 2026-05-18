import asyncio
import datetime as dt
import json
import os

import httpx
from openai import AsyncOpenAI
from scheduler.asyncio import Scheduler
from scheduler.trigger import Monday

from src.ai import generate_russian_match_report
from src.discord_bot import (
    append_to_message,
    attach_images_to_message,
    send_message,
    start_bot as start_discord_bot,
    typing_status,
)
from src.kb import refresh_kb_data as refresh_kb_data_files
from src.logger import log
from src.models import NormalizedPlayerData, PlayerData
from src.report_export import render_pdf_pages_to_png, save_match_report
from src.requests import opendota
from src.storage import DataStorage


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.strip()


def _load_player_config() -> tuple[str, set[str], dict[str, str]]:
    player_id = _require_env("PLAYER_ID")
    tracked_players_raw = _require_env("TRACKED_PLAYER_IDS")
    discord_map_raw = _require_env("PLAYER_ID_DISCORD_ID_JSON")

    tracked_players = {item.strip() for item in tracked_players_raw.split(",") if item.strip()}
    tracked_players.add(player_id)

    try:
        parsed_map = json.loads(discord_map_raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("PLAYER_ID_DISCORD_ID_JSON must be valid JSON.") from exc

    if not isinstance(parsed_map, dict):
        raise RuntimeError("PLAYER_ID_DISCORD_ID_JSON must be a JSON object.")

    player_id_discord_id = {str(key): str(value) for key, value in parsed_map.items()}
    return player_id, tracked_players, player_id_discord_id


PLAYER_ID, PLAYERS, PLAYER_ID_DISCORD_ID = _load_player_config()
AI_MODEL = "gpt-5.5"


def _tracked_players_heroes_text(tracked_players_data: list[NormalizedPlayerData]) -> str:
    lines: list[str] = []
    for player in tracked_players_data:
        if player.account_id is None:
            continue

        player_id = str(player.account_id)
        discord_user_id = PLAYER_ID_DISCORD_ID.get(player_id)
        if discord_user_id is None:
            discord_user_id = PLAYER_ID_DISCORD_ID.get(player.account_id)

        player_label = f"<@{discord_user_id}>" if discord_user_id else f"`{player_id}`"
        lines.append(f"- {player_label}: `{player.hero_name}`")

    return "\n".join(lines)


async def main(client: httpx.AsyncClient, storage: DataStorage, ai: AsyncOpenAI) -> None:
    try:
        match = await opendota.get_last_match(client, PLAYER_ID)
    except httpx.HTTPError as exc:
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
    except httpx.HTTPError as exc:
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
    tracked_heroes_text = _tracked_players_heroes_text(tracked_normalized_players_data)
    heroes_section = f"Герои:\n{tracked_heroes_text}" if tracked_heroes_text else ""
    discord_message_id: int | None = None

    log.info(f"Found [{len(filtered_players_data)} / {len(PLAYERS)}] players in the match.")
    try:
        discord_message_id = await send_message(
            f"🟡 Новый матч `{match.match_id}`\nИгроки: `{len(filtered_players_data)}/{len(PLAYERS)}`\n{heroes_section}"
        )
    except Exception as exc:
        log.warning(f"Failed to send Discord status message: {exc}")

    if not matched_friend_ids:
        log.info("No tracked friends found in this match. Skipping LLM analysis.")
        if discord_message_id is not None:
            try:
                await append_to_message(
                    discord_message_id,
                    "\n⚪ Нет отслеживаемых игроков. Пропускаю ИИ-анализ.",
                )
            except Exception as exc:
                log.warning(f"Failed to update Discord status message: {exc}")
        return

    log.info(f"Generating AI match analysis via {AI_MODEL}...")
    if discord_message_id is not None:
        try:
            await append_to_message(
                discord_message_id,
                f"\n🤖 ИИ анализирует (`{AI_MODEL}`)...",
            )
        except Exception as exc:
            log.warning(f"Failed to update Discord status message: {exc}")

    async with typing_status():
        translated_text = await generate_russian_match_report(
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
        )

    log.info("AI Agent match analysis is ready. Saving report...")
    markdown_path, pdf_path = save_match_report(
        markdown_text=translated_text,
        match_id=match.match_id,
        match_start_time=match.start_time,
    )
    if discord_message_id is not None:
        try:
            await append_to_message(
                discord_message_id,
                "\n✅ Готово. Страницы отчета прикреплены.",
            )
            image_paths = render_pdf_pages_to_png(pdf_path)
            await attach_images_to_message(discord_message_id, [str(path) for path in image_paths])
        except Exception as exc:
            log.warning(f"Failed to update Discord status message: {exc}")

    log.info(f"Report saved: {markdown_path}")
    log.info(f"PDF saved: {pdf_path}")


async def refresh_kb_data(client: httpx.AsyncClient) -> None:
    await refresh_kb_data_files(client)
    log.info("KB data refreshed and mappings reloaded.")


async def start() -> None:
    tz = dt.UTC
    sched = Scheduler(tzinfo=tz)
    client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))
    ai = AsyncOpenAI()
    storage = DataStorage("data.json")
    bot_token = os.getenv("DISCORD_BOT_TOKEN")

    if bot_token:
        asyncio.create_task(start_discord_bot(bot_token))
        log.info("Discord bot startup task created.")
    else:
        log.warning("DISCORD_BOT_TOKEN is not set. Discord bot is disabled.")

    sched.cyclic(timing=dt.timedelta(seconds=10), handle=main, args=(client, storage, ai))
    sched.weekly(timing=Monday(dt.time(tzinfo=tz)), handle=refresh_kb_data, args=(client,))

    while True:
        await asyncio.sleep(1)
