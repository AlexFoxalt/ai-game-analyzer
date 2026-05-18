import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

import discord

from src.logger import log


class DiscordClient(discord.Client):
    async def on_ready(self) -> None:
        user_name = self.user.name if self.user else "unknown"
        log.info(f"Discord bot connected as {user_name}.")


def create_bot() -> discord.Client:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = DiscordClient(intents=intents)
    return bot


class DiscordMessenger:
    def __init__(self, token: str, channel_id: int):
        self._token = token
        self._channel_id = channel_id
        self._bot: discord.Client | None = None
        self._ready_event = asyncio.Event()
        self._is_ready = False

    async def start(self) -> None:
        self._ready_event = asyncio.Event()
        self._is_ready = False
        self._bot = create_bot()

        async def _on_ready() -> None:
            user_name = self._bot.user.name if self._bot and self._bot.user else "unknown"
            log.info(f"Discord bot connected as {user_name}.")
            self._is_ready = True
            self._ready_event.set()

        self._bot.on_ready = _on_ready
        await self._bot.start(self._token)

    async def _get_default_text_channel(self) -> discord.TextChannel:
        if not self._bot:
            raise RuntimeError("Discord bot is not ready.")
        await self._ready_event.wait()
        if not self._is_ready:
            raise RuntimeError("Discord bot is not ready.")

        channel = self._bot.get_channel(self._channel_id)
        if channel is None:
            channel = await self._bot.fetch_channel(self._channel_id)
        if not isinstance(channel, discord.TextChannel):
            raise RuntimeError("Configured Discord channel is not a text channel.")
        return channel

    async def build_mentions(self, identifiers: list[str]) -> str:
        channel = await self._get_default_text_channel()
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

    async def send_message(self, msg: str) -> int:
        channel = await self._get_default_text_channel()
        sent_message = await channel.send(msg)
        return sent_message.id

    async def append_to_message(self, msg_id: int, text_to_append: str) -> None:
        channel = await self._get_default_text_channel()
        message = await channel.fetch_message(msg_id)
        await message.edit(content=f"{message.content}{text_to_append}")

    async def attach_images_to_message(self, msg_id: int, image_paths: list[str]) -> None:
        channel = await self._get_default_text_channel()
        message = await channel.fetch_message(msg_id)
        limited_paths = image_paths[:10]
        discord_files = [discord.File(Path(path)) for path in limited_paths]
        await message.edit(attachments=discord_files)

        if len(image_paths) > len(limited_paths):
            log.warning("Discord supports up to 10 attachments per message. Extra images were skipped.")

    @asynccontextmanager
    async def typing_status(self):
        channel = await self._get_default_text_channel()
        async with channel.typing():
            yield


def create_discord_messenger(bot_token: str | None, channel_id_raw: str | None) -> DiscordMessenger | None:
    if not bot_token:
        log.warning("DISCORD_BOT_TOKEN is not set. Discord bot is disabled.")
        return None
    if not channel_id_raw:
        log.warning("DISCORD_CHANNEL_ID is not set. Discord messaging actions are disabled.")
        return None
    return DiscordMessenger(token=bot_token, channel_id=int(channel_id_raw))
