import httpx

from src.models import Match

_API_URL = "https://api.opendota.com/api"
_MATCHES = f"{_API_URL}/matches"
_PLAYERS = f"{_API_URL}/players"


class OpenDotaRequestError(RuntimeError):
    pass


async def get_last_match(client: httpx.AsyncClient, player_id: int) -> Match:
    url = f"{_PLAYERS}/{player_id}/recentMatches?limit=1"
    try:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise OpenDotaRequestError(f"Failed to get last match for player {player_id}.") from exc

    if not payload:
        raise OpenDotaRequestError(f"No recent matches found for player {player_id}.")

    try:
        return Match.model_validate(payload[0])
    except (IndexError, TypeError, ValueError) as exc:
        raise OpenDotaRequestError(f"Failed to parse last match for player {player_id}.") from exc


async def get_match_details(client: httpx.AsyncClient, match_id: int) -> dict:
    url = f"{_MATCHES}/{match_id}"
    try:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise OpenDotaRequestError(f"Failed to get match details for match {match_id}.") from exc

    if not isinstance(payload, dict):
        raise OpenDotaRequestError(f"Unexpected match details format for match {match_id}.")

    return payload
