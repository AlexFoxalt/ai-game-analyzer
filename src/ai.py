from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from typing import Any

from openai import AsyncOpenAI

from src.logger import log

SYSTEM_PROMPT = """
You are a world-class Dota 2 performance analyst.

Your task:
1) Analyze ALL 10 players to understand full match context (draft, tempo, itemization, role matchups, farm patterns, teamfight impact).
2) Produce final player-by-player insights ONLY for matched_friend_ids (friends that actually played in this match).
3) Select one MVP (Most Valuable Player) from all players in the match (friend or non-friend).
4) Select one Shit player (opposite of MVP) from all players in the match (friend or non-friend).

Hard rules:
- Be factual and data-grounded. Do not invent stats.
- Use evidence from heroes, items, KDA, GPM/XPM, net worth, damage, objectives, and win/loss context.
- Strengths: 0-3 points per player.
- Weaknesses: 0-3 points per player.
- Improvement advice: 0-3 concrete points per player, future-focused and actionable.
- Do not include friends who are absent in this match.
- Do not include non-friends in final output.
- If data is missing, state uncertainty briefly and continue with best-available evidence.
- Output must be Discord-ready markdown.
- Use emojis with moderate frequency: helpful and clear, never spammy.
- Keep the tone smart, concise, and actionable.
""".strip()

TRANSLATION_SYSTEM_PROMPT = """
You are a professional Dota 2 analyst and RU esports localization editor.
Translate the provided Dota 2 match report into natural Russian used by CIS Dota players/coaches.
Preserve markdown structure exactly: same headings, bullets, line breaks, ordering, and emoji placement.
Keep all player IDs, numbers, and symbols unchanged.
Keep standard Dota entities in commonly used form: hero names, item names, abilities.
Do not add or remove content; translation only.
""".strip()


def build_dota_match_messages(
    target_player_ids: Iterable[int | str],
    matched_friend_ids: Iterable[int | str],
    all_players_data: Sequence[dict[str, Any]],
    match_metadata: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """
    Build OpenAI-ready messages for deep Dota 2 match analysis.

    The model should use all 10 players for context but output insights only
    for matched friends who actually appeared in the match.
    """
    normalized_target_ids = [str(player_id) for player_id in target_player_ids]
    normalized_matched_friend_ids = [str(player_id) for player_id in matched_friend_ids]
    metadata = match_metadata or {}

    user_prompt = f"""
Analyze this Dota 2 match deeply.

TARGET FRIEND IDS (friend pool, may include absent friends):
{json.dumps(normalized_target_ids, ensure_ascii=False, indent=2)}

MATCHED FRIEND IDS (final output only for these IDs):
{json.dumps(normalized_matched_friend_ids, ensure_ascii=False, indent=2)}

MATCH METADATA:
{json.dumps(metadata, ensure_ascii=False, indent=2)}

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

## MVP 🏆
- Pick exactly one MVP from all players in this match and explain why in 2-4 bullets.

## Shit player 💀
- Pick exactly one Shit player (opposite of MVP) from all players in this match and explain why in 2-4 bullets.
- Base it on lowest impact, biggest mistakes, poor itemization, bad positioning, feeding, or missed objectives.

Formatting and logic rules:
- Do not create sections for absent friends.
- Do not include detailed analysis sections for non-friends.
- Use markdown only (no JSON, no code blocks).
- Use emojis in moderation (about 1 emoji per section is enough).
- Keep advice practical: laning, map movement, objective calls, itemization, positioning, teamfight execution.
""".strip()

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


async def generate_match_analysis(
    ai: AsyncOpenAI,
    model: str,
    target_player_ids: Iterable[int | str],
    matched_friend_ids: Iterable[int | str],
    all_players_data: Sequence[dict[str, Any]],
    match_metadata: dict[str, Any] | None = None,
) -> str:
    messages = build_dota_match_messages(
        target_player_ids=target_player_ids,
        matched_friend_ids=matched_friend_ids,
        all_players_data=all_players_data,
        match_metadata=match_metadata,
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


async def generate_russian_match_report(
    ai: AsyncOpenAI,
    model: str,
    target_player_ids: Iterable[int | str],
    matched_friend_ids: Iterable[int | str],
    all_players_data: Sequence[dict[str, Any]],
    match_metadata: dict[str, Any] | None = None,
) -> str:
    analysis_text = await generate_match_analysis(
        ai=ai,
        model=model,
        target_player_ids=target_player_ids,
        matched_friend_ids=matched_friend_ids,
        all_players_data=all_players_data,
        match_metadata=match_metadata,
    )
    translated_text = await translate_analysis_to_russian(ai=ai, model=model, text=analysis_text)
    return translated_text or analysis_text
