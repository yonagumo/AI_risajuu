import os
import asyncio
from dotenv import load_dotenv

#from keep_alive import keep_alive

from discord_client import (
    Manager_discord,
    Risajuu_discord,
)
from ai_risajuu import AI_risajuu

async def main():
    load_dotenv()

    with open('prompt.md','r') as f:
        system_prompt = f.read()

    # Webサーバの立ち上げ
    # keep_alive()

    google_api_key = os.environ["GOOGLE_API_KEY"]
    risajuu = AI_risajuu(google_api_key, system_prompt)

    manager_discord = Manager_discord()
    manager_token = os.getenv("DISCORD_TOKEN_MANAGER")
    
    risajuu_discord = Risajuu_discord(risajuu, manager_discord)
    risajuu_token = os.getenv("DISCORD_TOKEN_RISAJUU")
    
    try:
        await asyncio.gather(
            manager_discord.start(manager_token),
            risajuu_discord.start(risajuu_token)
        )
    except asyncio.CancelledError:
        print("exit")


if __name__ == "__main__":
    asyncio.run(main())