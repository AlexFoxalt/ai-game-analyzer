from __future__ import annotations

import json
import os
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from langsmith import traceable
from openai import AsyncOpenAI

from src.ai.prompts import (
    OVERVIEW_SYSTEM_PROMPT,
    TRANSLATION_SYSTEM_PROMPT,
    get_system_prompt,
    get_user_rules,
    resolve_prompt_version,
)
from src.logger import log


def _get_prompt_version() -> str:
    requested_version = os.getenv("PROMPT_VERSION")
    resolved_version = resolve_prompt_version(requested_version)
    if requested_version and requested_version.strip().lower() != resolved_version:
        log.warning(
            "Unsupported PROMPT_VERSION '{}', fallback to '{}'",
            requested_version,
            resolved_version,
        )
    return resolved_version


def build_dota_match_messages(
    target_player_ids: Iterable[int | str],
    matched_friend_ids: Iterable[int | str],
    all_players_data: Sequence[dict[str, Any]],
    match_metadata: dict[str, Any] | None = None,
    recent_games_briefs: dict[int | str, str] | None = None,
    prompt_version: str | None = None,
) -> list[dict[str, str]]:
    """
    Build OpenAI-ready messages for deep Dota 2 match analysis.

    The model should use all 10 players for context but output insights only
    for matched friends who actually appeared in the match.
    """
    normalized_target_ids = [str(player_id) for player_id in target_player_ids]
    normalized_matched_friend_ids = [str(player_id) for player_id in matched_friend_ids]
    metadata = match_metadata or {}
    normalized_recent_games_briefs = {str(player_id): brief for player_id, brief in (recent_games_briefs or {}).items()}
    selected_prompt_version = resolve_prompt_version(prompt_version) if prompt_version else _get_prompt_version()
    user_rules = get_user_rules(selected_prompt_version)
    mvp_bullets_range = "1-2" if selected_prompt_version == "v2" else "2-4"

    user_prompt = f"""
Analyze this Dota 2 match deeply.

TARGET FRIEND IDS (friend pool, may include absent friends):
{json.dumps(normalized_target_ids, ensure_ascii=False, indent=2)}

MATCHED FRIEND IDS (final output only for these IDs):
{json.dumps(normalized_matched_friend_ids, ensure_ascii=False, indent=2)}

MATCH METADATA:
{json.dumps(metadata, ensure_ascii=False, indent=2)}

PREVIOUS GAMES BRIEF (OPTIONAL, up to 5 recent games per player, short text facts):
{json.dumps(normalized_recent_games_briefs, ensure_ascii=False, indent=2)}

ALL PLAYERS DATA (usually 10 players; use all of them for context):
{json.dumps(all_players_data, ensure_ascii=False, indent=2)}

Write a Discord-ready markdown report with this structure:

## Match Overview
- 2-4 bullets about game flow and key context.

## Game Analysis
For EACH matched friend ID, include:
### Player `<personaname if known>` — `<hero_name if known>`
**Strengths**
- 0 to 3 bullets
**Weaknesses**
- 0 to 3 bullets
**How to Improve Next Games**
- 0 to 3 bullets

## MVP
- Pick exactly one MVP (Most Valuable Player) from all players in this match and explain why in {mvp_bullets_range} bullets.

## Shit player
- Pick exactly one Shit player (opposite of MVP) from all players in this match and explain why in {mvp_bullets_range} bullets.

{user_rules}
""".strip()

    return [
        {"role": "system", "content": get_system_prompt(selected_prompt_version)},
        {"role": "user", "content": user_prompt},
    ]


@traceable(name="translate_analysis_to_russian")
async def translate_analysis_to_russian(ai: AsyncOpenAI, model: str, text: str) -> str:
    response = await ai.responses.create(
        model=model,
        reasoning={"effort": "high"},
        input=[
            {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return response.output_text.strip()


@traceable(name="generate_en_match_report")
async def generate_en_match_report(
    ai: AsyncOpenAI,
    model: str,
    target_player_ids: Iterable[int | str],
    matched_friend_ids: Iterable[int | str],
    all_players_data: Sequence[dict[str, Any]],
    match_metadata: dict[str, Any] | None = None,
    recent_games_briefs: dict[int | str, str] | None = None,
    prompt_version: str | None = None,
) -> str:
    messages = build_dota_match_messages(
        target_player_ids=target_player_ids,
        matched_friend_ids=matched_friend_ids,
        all_players_data=all_players_data,
        match_metadata=match_metadata,
        recent_games_briefs=recent_games_briefs,
        prompt_version=prompt_version,
    )
    log.debug(
        "Final LLM analysis payload:\n{}",
        json.dumps(
            {"model": model, "reasoning": {"effort": "high"}, "input": messages},
            ensure_ascii=False,
            indent=2,
        ),
    )
    response = await ai.responses.create(
        model=model,
        reasoning={"effort": "high"},
        input=messages,
    )
    return response.output_text.strip()


async def translate_match_report(
    ai: AsyncOpenAI,
    model: str,
    text: str,
) -> str:
    return await translate_analysis_to_russian(ai=ai, model=model, text=text)


@traceable(name="generate_report_tts_audio")
async def generate_report_tts_audio(
    ai: AsyncOpenAI,
    text: str,
    output_path: Path,
    model: str = "gpt-4o-mini-tts",
    voice: str = "echo",
) -> Path:
    # OpenAI TTS input is limited to 4096 chars.
    tts_text = text.strip()
    if len(tts_text) > 4096:
        log.warning("TTS input is too long ({}), truncating to 4096 chars.", len(tts_text))
        tts_text = tts_text[:4096]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    async with ai.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=tts_text,
        response_format="wav",
    ) as response:
        await response.stream_to_file(output_path)
    return output_path


@traceable(name="generate_match_overview")
async def generate_match_overview(
    ai: AsyncOpenAI,
    model: str,
    en_report: str,
    tracked_players: Sequence[dict[str, Any]],
) -> dict[str, str]:
    user_prompt = f"""
Build player-specific compact notes from this match report.

TRACKED PLAYERS:
{json.dumps(tracked_players, ensure_ascii=False, indent=2)}

MATCH REPORT:
{en_report}
""".strip()
    response = await ai.responses.create(
        model=model,
        reasoning={"effort": "medium"},
        input=[
            {"role": "system", "content": OVERVIEW_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw_output = response.output_text.strip()
    if raw_output.startswith("```"):
        raw_output = raw_output.strip("`")
        if raw_output.lower().startswith("json"):
            raw_output = raw_output[4:].strip()
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError:
        log.warning("Failed to parse overview payload as JSON")
        return {}
    if not isinstance(payload, dict):
        return {}

    allowed_ids = {
        str(player.get("account_id"))
        for player in tracked_players
        if isinstance(player, dict) and player.get("account_id") is not None
    }
    normalized: dict[str, str] = {}
    for player_id, overview in payload.items():
        player_id_str = str(player_id)
        if player_id_str not in allowed_ids:
            continue
        if isinstance(overview, str) and overview.strip():
            normalized[player_id_str] = overview.strip()
    return normalized
