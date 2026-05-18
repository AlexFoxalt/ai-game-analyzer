import asyncio

import httpx

from src.requests.opendota import get_last_match, get_match_details

match_id = "8814936330"
player_id = "124410279"

client = httpx.AsyncClient(timeout=30.0)


async def last_match():
    return await get_last_match(client, player_id)


async def match_details():
    return await get_match_details(client, match_id)


async def main():
    if player_id:
        lm = await last_match()
        print(f"Last match ID: {lm.match_id}")

    if match_id:
        md = await match_details()
        print(f"Match with ID {match_id} found: {bool(md)}")


if __name__ == "__main__":
    asyncio.run(main())
