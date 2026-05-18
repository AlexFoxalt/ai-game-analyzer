# This example requires the 'message_content' intent.

import os

import discord
from dotenv import load_dotenv

load_dotenv()


class MyClient(discord.Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")

        channel_id_raw = os.getenv("DISCORD_CHANNEL_ID")
        if not channel_id_raw:
            raise RuntimeError("DISCORD_CHANNEL_ID is not set.")

        channel_id = int(channel_id_raw)
        channel = self.get_channel(channel_id)
        if channel is None:
            channel = await self.fetch_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            raise RuntimeError("Configured channel is not a text channel.")

        sent_message = await channel.send("Test message from test_bot.py")
        await sent_message.edit(content=f"{sent_message.content}\nAppended text works.")
        print(f"Sent and appended test message. ID={sent_message.id}")

        await self.close()

    async def on_message(self, message):
        print(f"Message from {message.author}: {message.content}")


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(os.getenv("DISCORD_BOT_TOKEN"))
