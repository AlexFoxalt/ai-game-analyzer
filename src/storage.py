import json
from pathlib import Path

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
        data["matches"][match_id] = match.model_dump()
        data["last_match_id"] = match.match_id
        self._write_db(data)

    def get_match_by_id(self, match_id: int) -> dict:
        data = self._read_db()
        match = data["matches"].get(str(match_id))
        if match is None:
            raise KeyError(f"Match with id {match_id} was not found")
        return Match.model_validate(match).model_dump(mode="json")

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
        return raw_data

    def _write_db(self, data: dict) -> None:
        with self._db_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    @staticmethod
    def _default_db() -> dict:
        return {"last_match_id": 0, "matches": {}}
