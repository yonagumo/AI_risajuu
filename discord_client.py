import os

import discord


class Manager_discord_client(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def test_message(self, user, channel_id):
        await self.get_channel(channel_id).send(f"{user.name}によって呼び出されました")


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
            async with message.channel.typing():
                await self.reply_to_message(message)

    async def reply_to_message(self, message):
        if message.content.startswith("呼び出し"):
            await message.channel.send(f"お～い！{message.author.display_name}が呼んでるじゅう！")
            await self.manager.test_message(self.user, message.channel.id)
            return

        reply = await self.risajuu.chat(message.content, message.attachments)

        if reply.text is None:
            return

        if len(reply.text) > 0:
            for chunk in reply.text:
                await message.channel.send(chunk)

        if len(reply.attachments) > 0:
            for attachment in reply.attachments:
                await message.channel.send(file=discord.File(attachment, filename=os.path.basename(attachment)))
                os.remove(attachment)
