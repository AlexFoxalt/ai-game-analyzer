import httpx

from src.models import Match

_API_URL = "https://api.opendota.com/api"
_MATCHES = f"{_API_URL}/matches"
_PLAYERS = f"{_API_URL}/players"


async def get_last_match(client: httpx.AsyncClient, player_id: int) -> Match:
    url = f"{_PLAYERS}/{player_id}/recentMatches?limit=1"
    response = await client.get(url)
    if not response.is_success:
        raise Exception(f"Failed to get last match for player {player_id}. Status: {response.status_code}")
    resp = response.json()
    return Match.model_validate(resp[0])


async def get_match_details(client: httpx.AsyncClient, match_id: int) -> dict:
    url = f"{_MATCHES}/{match_id}"
    response = await client.get(url)
    if not response.is_success:
        raise Exception(f"Failed to get match details for match {match_id}. Status: {response.status_code}")
    return response.json()
