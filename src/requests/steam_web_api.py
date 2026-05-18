import os

import httpx

_API_URL = "https://api.steampowered.com/IDOTA2Match_570"


def _get_api_key(api_key: str | None) -> str:
    key = api_key or os.getenv("STEAM_WEB_API_KEY")
    if not key:
        raise ValueError("STEAM_WEB_API_KEY is not set")
    return key


async def get_last_match(
    client: httpx.AsyncClient,
    player_id: int | str,
    api_key: str | None = None,
) -> dict:
    url = f"{_API_URL}/GetMatchHistory/v1/"
    params = {
        "key": _get_api_key(api_key),
        "account_id": str(player_id),
        "matches_requested": 1,
    }
    response = await client.get(url, params=params)
    if not response.is_success:
        raise Exception(f"Failed to get last match for player {player_id}. Status: {response.status_code}")

    payload = response.json()
    matches = payload.get("result", {}).get("matches", [])
    if not matches:
        return {}
    return matches[0]


async def get_match_details(
    client: httpx.AsyncClient,
    match_id: int | str,
    api_key: str | None = None,
) -> dict:
    url = f"{_API_URL}/GetMatchDetails/v1/"
    params = {
        "key": _get_api_key(api_key),
        "match_id": str(match_id),
    }
    response = await client.get(url, params=params)
    if not response.is_success:
        raise Exception(f"Failed to get match details for match {match_id}. Status: {response.status_code}")

    payload = response.json()
    return payload.get("result", {})
