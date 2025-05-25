import os
import discord
from dotenv import load_dotenv
from keep_alive import keep_alive

from ai_risajuu import AI_risajuu


def main():
    load_dotenv()

    google_api_key = os.environ["GOOGLE_API_KEY"]
    with open("prompt.md", "r", encoding="utf-8") as f:
        system_prompt = f.read()
    risajuu = AI_risajuu(google_api_key, system_prompt)

    # Web サーバの立ち上げ
    keep_alive()

    discord_token = os.getenv("DISCORD_TOKEN")
    client = Risaju_discord_client(risajuu)
    client.run(discord_token)


class Risaju_discord_client(discord.Client):
    def __init__(self, risajuu):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.risajuu = risajuu

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_message(self, message):
        if message.author == self.user or message.content.startswith(
            "あ、これはりさじゅう反応しないでね"
        ):
            return

        if message.author.bot:
            return

        if message.channel.name in os.getenv("TARGET_CHANNEL_NAME").split(
            ","
        ) or self.user.mentioned_in(message):
            reply = self.risajuu.chat(
                message.content, message.attachments if len(message.attachments) > 0 else None
            )

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


if __name__ == "__main__":
    main()
