import os
import io
import datetime
import discord
from dotenv import load_dotenv
from keep_alive import keep_alive

from ai_risajuu import AI_risajuu

def main():
    load_dotenv()

    google_api_key = os.environ["GOOGLE_API_KEY"]
    with open('prompt.md','r') as f:
        system_prompt = f.read()
    risajuu = AI_risajuu(google_api_key, system_prompt)

    discord_token = os.getenv("DISCORD_TOKEN")
    client = Risaju_discord_client(risajuu)
    client.run(discord_token)

    # Web サーバの立ち上げ
    keep_alive()


class Risaju_discord_client(discord.Client):
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
        
        if message.channel.name == "ai試験場" or self.user.mentioned_in(message):
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


if __name__ == "__main__":
    main()