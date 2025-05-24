import io
import datetime
import discord

class Manager_discord(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def test_message(self, user, channel_id):
        await self.get_channel(channel_id).send(f"{user.name}によって呼び出されました")


class Risajuu_discord(discord.Client):
    def __init__(self, risajuu, manager):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.risajuu = risajuu
        self.manager = manager

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_message(self, message):
        if message.author == self.user or message.author.bot:
            return
        
        if message.channel.name == "yonagumo" or self.user.mentioned_in(message):
            if message.content.startswith("呼び出し"):
                display_name = message.author.nick or message.author.global_name or message.author.name
                await message.channel.send(f"お～い！{display_name}が呼んでるじゅう！")
                await self.manager.test_message(self.user, message.channel.id)
                return

            reply = self.risajuu.chat(message.content)

            for chunk in reply.text:
                await message.channel.send(chunk)

            if reply.export_history:
                with io.StringIO(reply.export_history) as file:
                    await message.channel.send(
                        file=discord.File(
                            file,
                            "chat_history_" + str(datetime.datetime.now()) + ".txt",
                        )
                    )