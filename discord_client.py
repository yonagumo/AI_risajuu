import io
import datetime
import json
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
            author_name = message.author.nick or message.author.global_name or message.author.name

            input_text = message.content

            if input_text.startswith("カスタム"):
                reply = self.risajuu.custom(input_text.replace("カスタム", ""))
            elif input_text.endswith("エクスポート"):
                reply = self.risajuu.export_history()
            elif input_text.endswith("インポート"):
                history = None
                if message.attachments:
                    attachment = message.attachments[0]
                    if attachment.filename.endswith(".json"):
                        file = await attachment.read()
                        try:
                            history = json.loads(file.decode("utf-8"))
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            pass
                reply = self.risajuu.import_history(history)
            else:
                reply = self.risajuu.chat(message.content)

            for chunk in reply.text:
                await message.channel.send(chunk)

            if reply.export_history is not None:
                json_history = json.dumps(reply.export_history, indent=2, ensure_ascii=False)
                with io.StringIO(json_history) as file:
                    await message.channel.send(
                        file=discord.File(
                            file,
                            "chat_history_" + str(datetime.datetime.now()) + ".json",
                        )
                    )