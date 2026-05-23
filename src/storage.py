import json
from collections.abc import Iterable
from pathlib import Path

from pydantic import ValidationError

from src.models import Match


class DataStorage:
    def __init__(self, db_path: str | Path = "data.json") -> None:
        self._db_path = Path(db_path)
        self._ensure_db_exists()
        self._normalize_db()

    def get_last_match_id(self) -> int | None:
        data = self._read_db()
        return data["last_match_id"]

    def set_last_match_id(self, match_id: int) -> None:
        data = self._read_db()
        data["last_match_id"] = match_id
        self._write_db(data)

    def add_match(self, match: Match) -> None:
        self.upsert_match(match)

    def upsert_match(self, match: Match) -> None:
        data = self._read_db()
        match_id = str(match.match_id)
        existing_match = data["matches"].get(match_id, {})
        payload = Match.model_validate(match.model_dump(mode="json")).model_dump(mode="json")
        if isinstance(existing_match, dict) and existing_match.get("overview") and payload.get("overview") is None:
            payload["overview"] = existing_match["overview"]
        data["matches"][match_id] = payload
        data["last_match_id"] = match.match_id
        self._write_db(data)

    def set_match_overview(self, match_id: int, overview: dict[str, str]) -> None:
        data = self._read_db()
        match_key = str(match_id)
        match = data["matches"].get(match_key)
        if not isinstance(match, dict):
            raise KeyError(f"Match with id {match_id} was not found")
        match["overview"] = {
            str(player_id): text.strip()
            for player_id, text in overview.items()
            if isinstance(text, str) and text.strip()
        }
        self._write_db(data)

    def get_match_by_id(self, match_id: int) -> dict:
        data = self._read_db()
        match = data["matches"].get(str(match_id))
        if match is None:
            raise KeyError(f"Match with id {match_id} was not found")
        return Match.model_validate(match).model_dump(mode="json")

    def get_recent_player_overviews(
        self,
        player_ids: Iterable[int | str],
        limit: int = 5,
    ) -> dict[str, list[str]]:
        data = self._read_db()
        normalized_player_ids = [str(player_id) for player_id in player_ids]
        result: dict[str, list[str]] = {player_id: [] for player_id in normalized_player_ids}
        matches = []
        for match_payload in data["matches"].values():
            if not isinstance(match_payload, dict):
                continue
            start_time = match_payload.get("start_time")
            start_time_int = start_time if isinstance(start_time, int) else 0
            matches.append((start_time_int, match_payload))
        matches.sort(key=lambda item: item[0], reverse=True)
        for _, match_payload in matches:
            overview = match_payload.get("overview")
            if not isinstance(overview, dict):
                continue
            for player_id in normalized_player_ids:
                if len(result[player_id]) >= limit:
                    continue
                text = overview.get(player_id)
                if isinstance(text, str) and text.strip():
                    result[player_id].append(text.strip())
            if all(len(result[player_id]) >= limit for player_id in normalized_player_ids):
                break
        return {player_id: overviews for player_id, overviews in result.items() if overviews}

    def _ensure_db_exists(self) -> None:
        if self._db_path.exists():
            return
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_db(self._default_db())

    def _normalize_db(self) -> None:
        self._write_db(self._read_db())

    def _read_db(self) -> dict:
        with self._db_path.open("r", encoding="utf-8") as file:
            try:
                raw_data = json.load(file)
            except json.JSONDecodeError:
                raw_data = self._default_db()
                with self._db_path.open("w", encoding="utf-8") as writable_file:
                    json.dump(raw_data, writable_file, indent=2)
        if not isinstance(raw_data, dict):
            raw_data = self._default_db()
        raw_data.setdefault("last_match_id", 0)
        raw_data.setdefault("matches", {})
        if not isinstance(raw_data["matches"], dict):
            raw_data["matches"] = {}

        # Normalize keys to strings to keep stable upsert behavior.
        raw_data["matches"] = {str(key): value for key, value in raw_data["matches"].items()}
        normalized_matches: dict[str, dict] = {}
        for match_id, match_payload in raw_data["matches"].items():
            if not isinstance(match_payload, dict):
                continue
            try:
                normalized_match = Match.model_validate(match_payload).model_dump(mode="json")
            except ValidationError:
                continue
            overview = normalized_match.get("overview")
            if isinstance(overview, dict):
                normalized_match["overview"] = {
                    str(player_id): text.strip()
                    for player_id, text in overview.items()
                    if isinstance(text, str) and text.strip()
                }
            elif isinstance(overview, str):
                normalized_match["overview"] = {"global": overview.strip()} if overview.strip() else None
            else:
                normalized_match["overview"] = None
            normalized_matches[match_id] = normalized_match
        raw_data["matches"] = normalized_matches
        return raw_data

    def _write_db(self, data: dict) -> None:
        with self._db_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    @staticmethod
    def _default_db() -> dict:
        return {"last_match_id": 0, "matches": {}}
