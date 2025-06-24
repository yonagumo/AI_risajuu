import asyncio
import os

from dotenv import load_dotenv

from ai_risajuu import RisajuuConfig
from discord_client import (
    Risajuu_discord_client,
)


async def main():
    # .envファイルの内容を環境変数として取り込む
    load_dotenv()

    # システムプロンプトの読み込み
    # 「カスタム」してもcommon_promptは残る
    with open("default_prompt.md", "r", encoding="utf-8") as f:
        system_prompt = f.read()
    with open("common_prompt.md", "r", encoding="utf-8") as f:
        common_prompt = f.read()

    # AIりさじゅうの基本設定
    risajuu_config = RisajuuConfig(
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        main_model_name=os.getenv("MAIN_MODEL_NAME"),
        sub_model_name=os.getenv("SUB_MODEL_NAME"),
        system_instruction=system_prompt,
        common_instruction=common_prompt,
    )

    # Discordクライアントの初期化
    risajuu_discord = Risajuu_discord_client(risajuu_config)

    # Discordクライアントの起動
    risajuu_token = os.getenv("DISCORD_TOKEN_RISAJUU")

    try:
        await risajuu_discord.start(risajuu_token)
    except asyncio.CancelledError:
        print("\n=== exit ===")


if __name__ == "__main__":
    asyncio.run(main())
