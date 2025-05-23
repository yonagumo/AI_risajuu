import os
from keep_alive import keep_alive

from dotenv import load_dotenv

from discord_client import Risajuu_discord_client
from ai_risajuu import AI_risajuu

def main():
    load_dotenv()

    with open('prompt.md','r') as f:
        system_prompt = f.read()

    google_api_key = os.environ["GOOGLE_API_KEY"]
    risajuu = AI_risajuu(google_api_key, system_prompt)

    discord_token = os.getenv("DISCORD_TOKEN")
    client = Risajuu_discord_client(risajuu)
    client.run(discord_token)

    # Webサーバの立ち上げ
    keep_alive()


if __name__ == "__main__":
    main()