import asyncio
import os

from dotenv import load_dotenv

from ai_risajuu import AI_risajuu

# from keep_alive import keep_alive
from discord_client import (
    Manager_discord_client,
    Risajuu_discord_client,
)


async def main():
    load_dotenv()

    with open("default_prompt.md", "r", encoding="utf-8") as f:
        system_prompt = f.read()
    with open("common_prompt.md", "r", encoding="utf-8") as f:
        common_prompt = f.read()
        system_prompt = system_prompt + common_prompt

    # Webサーバの立ち上げ
    # keep_alive()

    google_api_key = os.getenv("GOOGLE_API_KEY")
    model_name = os.getenv("MAIN_MODEL_NAME")
    risajuu = AI_risajuu(google_api_key, model_name, system_prompt, common_prompt)

    manager_discord = Manager_discord_client()
    manager_token = os.getenv("DISCORD_TOKEN_MANAGER")

    risajuu_discord = Risajuu_discord_client(risajuu, manager_discord)
    risajuu_token = os.getenv("DISCORD_TOKEN_RISAJUU")

    try:
        await asyncio.gather(manager_discord.start(manager_token), risajuu_discord.start(risajuu_token))
    except asyncio.CancelledError:
        print("exit")


if __name__ == "__main__":
    asyncio.run(main())
