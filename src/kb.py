import json
from pathlib import Path
from typing import Any

import httpx

_KB_DATA_DIR = Path(__file__).parent / "kb_data"
_API_URL = "https://api.opendota.com/api"
_CONSTANTS = f"{_API_URL}/constants"
_KB_REFRESH_ENDPOINTS = {
    "heroes.json": f"{_CONSTANTS}/heroes",
    "items.json": f"{_CONSTANTS}/items",
}

HERO_ID_TO_NAME: dict[str, str] = {}
ITEM_ID_TO_NAME: dict[str, str] = {}


def _load_json(file_name: str) -> dict[str, Any]:
    with (_KB_DATA_DIR / file_name).open(encoding="utf-8") as data_file:
        return json.load(data_file)


def _sorted_mapping(mapping: dict[str, str]) -> dict[str, str]:
    return dict(
        sorted(
            mapping.items(),
            key=lambda item: (0, int(item[0])) if item[0].isdigit() else (1, item[0]),
        )
    )


def _normalize_heroes_payload(raw_data: dict[str, Any]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key, value in raw_data.items():
        if isinstance(value, str):
            cleaned[str(key)] = value
            continue

        if not isinstance(value, dict):
            continue

        hero_id = value.get("id", key)
        localized_name = value.get("localized_name")
        if localized_name:
            cleaned[str(hero_id)] = str(localized_name)
    return _sorted_mapping(cleaned)


def _normalize_items_payload(raw_data: dict[str, Any]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key, value in raw_data.items():
        if isinstance(value, str):
            cleaned[str(key)] = value
            continue

        if not isinstance(value, dict):
            continue

        item_id = value.get("id", key)
        display_name = value.get("dname")
        if display_name:
            cleaned[str(item_id)] = str(display_name)
    return _sorted_mapping(cleaned)


def _write_mapping(file_name: str, mapping: dict[str, str]) -> None:
    with (_KB_DATA_DIR / file_name).open("w", encoding="utf-8") as data_file:
        json.dump(mapping, data_file, ensure_ascii=False, indent=2)
        data_file.write("\n")


def clean_heroes_file() -> dict[str, str]:
    cleaned = _normalize_heroes_payload(_load_json("heroes.json"))
    _write_mapping("heroes.json", cleaned)
    return cleaned


def clean_items_file() -> dict[str, str]:
    cleaned = _normalize_items_payload(_load_json("items.json"))
    _write_mapping("items.json", cleaned)
    return cleaned


def clean_kb_data_files() -> None:
    clean_heroes_file()
    clean_items_file()


async def refresh_kb_data(client: httpx.AsyncClient) -> None:
    for file_name, url in _KB_REFRESH_ENDPOINTS.items():
        response = await client.get(url)
        if not response.is_success:
            raise Exception(f"Failed to refresh KB data {file_name}. Status: {response.status_code}")

        target_file = _KB_DATA_DIR / file_name
        target_file.write_text(response.text, encoding="utf-8")

    clean_kb_data_files()
    refresh_mappings()


def refresh_mappings() -> None:
    HERO_ID_TO_NAME.clear()
    HERO_ID_TO_NAME.update(_normalize_heroes_payload(_load_json("heroes.json")))

    ITEM_ID_TO_NAME.clear()
    ITEM_ID_TO_NAME.update(_normalize_items_payload(_load_json("items.json")))


refresh_mappings()
