import datetime as dt
import json
import os
from pathlib import Path

from src.models import NormalizedPlayerData


def jprint(data: dict) -> None:
    print(json.dumps(data, indent=4))


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.strip()


def build_match_report_dir(match_id: int, match_start_time: int, reports_dir: Path = Path("reports")) -> Path:
    match_date = dt.datetime.fromtimestamp(match_start_time).strftime("%Y-%m-%d")
    return reports_dir / f"{match_id}_{match_date}"


def load_player_config() -> tuple[str, set[str], dict[str, str]]:
    player_id = require_env("PLAYER_ID")
    tracked_players_raw = require_env("TRACKED_PLAYER_IDS")
    discord_map_raw = require_env("PLAYER_ID_DISCORD_ID_JSON")

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


def tracked_players_heroes_text(
    tracked_players_data: list[NormalizedPlayerData], player_id_discord_id: dict[str, str]
) -> str:
    lines: list[str] = []
    for player in tracked_players_data:
        if player.account_id is None:
            continue

        player_id = str(player.account_id)
        discord_user_id = player_id_discord_id.get(player_id)
        if discord_user_id is None:
            discord_user_id = player_id_discord_id.get(player.account_id)

        player_label = f"<@{discord_user_id}>" if discord_user_id else f"`{player_id}`"
        lines.append(f"- {player_label}: `{player.hero_name}`")

    return "\n".join(lines)
