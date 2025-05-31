import json
import os
from datetime import timedelta, timezone

import discord

from ai_risajuu import Message, Savedata


class Manager_discord_client(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def logging(self, channel_id, log):
        await self.get_channel(channel_id).send(f"```{log}```")


class Risajuu_discord_client(discord.Client):
    def __init__(self, risajuu, manager):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.risajuu = risajuu
        self.manager = manager

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.name in os.getenv("TARGET_CHANNEL_NAME").split(",") or self.user.mentioned_in(message):
            if message.content.startswith("thinking:on"):
                self.risajuu.include_thoughts = True
                await self.manager.logging(message.channel.id, "self.risajuu.include_thoughts = True")
                return
            elif message.content.startswith("thinking:off"):
                self.risajuu.include_thoughts = False
                await self.manager.logging(message.channel.id, "self.risajuu.include_thoughts = False")
                return

            async with message.channel.typing():
                await self.reply_to_message(message)

    async def reply_to_message(self, message):
        input_text = message.content
        if input_text.startswith("カスタム"):
            reply = self.risajuu.custom(input_text.replace("カスタム", ""))
        elif input_text.endswith("エクスポート"):
            reply = self.risajuu.export_savedata()
        elif input_text.endswith("インポート"):
            history = None
            if len(message.attachments) == 1 and message.attachments[0].filename.lower().endswith(".json"):
                json_data = await message.attachments[0].read()
                try:
                    json_str = json_data.decode("utf-8").replace("\n", "")
                    history = Savedata.model_validate_json(json_str)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            reply = self.risajuu.import_savedata(history)
        else:
            created = message.created_at.astimezone(timezone(timedelta(hours=9))).isoformat()
            content = Message(
                bot=False,
                author_display_name=message.author.display_name,
                author_name=message.author.name,
                created_at=created,
                body=input_text,
            )
            reply = self.risajuu.chat(content, message.attachments)

        if reply.texts is None:
            return

        for t in reply.logs:
            await self.manager.logging(message.channel.id, t)

        for chunk in reply.texts:
            await message.channel.send(chunk)

        if len(reply.attachments) > 0:
            for attachment in reply.attachments:
                await message.channel.send(file=discord.File(attachment, filename=os.path.basename(attachment)))
                os.remove(attachment)
