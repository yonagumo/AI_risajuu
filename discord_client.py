import io
import os
import datetime
import discord


class Risajuu_discord_client(discord.Client):
    def __init__(self, risajuu):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.risajuu = risajuu

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_message(self, message):

        if message.author.bot:
            return

        if message.channel.name in os.getenv("TARGET_CHANNEL_NAME").split(
            ","
        ) or self.user.mentioned_in(message):
            reply = await self.risajuu.chat(
                message.content, message.attachments
            )

            if reply.text is None:
                return

            if len(reply.text) > 0:
                for chunk in reply.text:
                    await message.channel.send(chunk)

            if len(reply.attachments) > 0:
                for attachment in reply.attachments:
                    await message.channel.send(
                        file=discord.File(
                            attachment, filename=os.path.basename(attachment)
                        )
                    )
                    os.remove(attachment)
