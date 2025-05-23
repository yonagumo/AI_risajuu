import io
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
        if message.author == self.user or message.author.bot:
            return
        
        if message.channel.name == "yonagumo" or self.user.mentioned_in(message):
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