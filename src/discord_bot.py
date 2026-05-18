import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

import discord

from src.logger import log

_bot: discord.Client | None = None
_default_channel_id: int | None = None
_ready_event: asyncio.Event | None = None
_is_ready = False


class DiscordClient(discord.Client):
    async def on_ready(self) -> None:
        global _is_ready

        user_name = self.user.name if self.user else "unknown"
        log.info(f"Discord bot connected as {user_name}.")
        _is_ready = True
        if _ready_event is not None:
            _ready_event.set()


def create_bot() -> discord.Client:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = DiscordClient(intents=intents)
    return bot


async def start_bot(token: str) -> None:
    global _bot, _default_channel_id, _ready_event, _is_ready

    channel_id_raw = os.getenv("DISCORD_CHANNEL_ID")
    if not channel_id_raw:
        log.warning("DISCORD_CHANNEL_ID is not set. Discord messaging actions are disabled.")
        return

    _default_channel_id = int(channel_id_raw)
    _ready_event = asyncio.Event()
    _is_ready = False
    _bot = create_bot()
    await _bot.start(token)


async def _get_default_text_channel() -> discord.TextChannel:
    if not _bot or _default_channel_id is None or not _ready_event:
        raise RuntimeError("Discord bot is not ready.")
    await _ready_event.wait()
    if not _is_ready:
        raise RuntimeError("Discord bot is not ready.")

    channel = _bot.get_channel(_default_channel_id)
    if channel is None:
        channel = await _bot.fetch_channel(_default_channel_id)
    if not isinstance(channel, discord.TextChannel):
        raise RuntimeError("Configured Discord channel is not a text channel.")
    return channel


async def build_mentions(identifiers: list[str]) -> str:
    channel = await _get_default_text_channel()
    guild = channel.guild
    mentions: list[str] = []

    for identifier in dict.fromkeys(identifiers):
        if not identifier:
            continue
        if identifier.isdigit():
            mentions.append(f"<@{identifier}>")
            continue

        identifier_lower = identifier.lower()
        member = discord.utils.find(
            lambda m: (
                m.name.lower() == identifier_lower
                or (m.global_name is not None and m.global_name.lower() == identifier_lower)
                or m.display_name.lower() == identifier_lower
            ),
            guild.members,
        )
        if member is not None:
            mentions.append(member.mention)
        else:
            mentions.append(f"@{identifier}")

    return " ".join(mentions)


async def send_message(msg: str) -> int:
    channel = await _get_default_text_channel()
    sent_message = await channel.send(msg)
    return sent_message.id


async def append_to_message(msg_id: int, text_to_append: str) -> None:
    channel = await _get_default_text_channel()
    message = await channel.fetch_message(msg_id)
    await message.edit(content=f"{message.content}{text_to_append}")


async def attach_images_to_message(msg_id: int, image_paths: list[str]) -> None:
    channel = await _get_default_text_channel()
    message = await channel.fetch_message(msg_id)
    limited_paths = image_paths[:10]
    discord_files = [discord.File(Path(path)) for path in limited_paths]
    await message.edit(attachments=discord_files)

    if len(image_paths) > len(limited_paths):
        log.warning("Discord supports up to 10 attachments per message. Extra images were skipped.")


@asynccontextmanager
async def typing_status():
    channel = await _get_default_text_channel()
    async with channel.typing():
        yield
