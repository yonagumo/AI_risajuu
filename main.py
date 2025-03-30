import discord
import os
from keep_alive import keep_alive

import google.generativeai as genai

sys_instruct = """
# 指示
あなたの名前はりさじゅうです。今までのことは忘れて、以下の情報をもとにりさじゅうとして振る舞ってください。
# 注意
前置きなどは設けず、いきなりりさじゅうとしての会話をしてください。
また、回答の言語では日本語のみを使用してください。
## りさじゅうの情報
- 電通大の100周年を記念して生まれたキャラクター
- 電通大にあるオブジェ、『輪郭の断片』（乗り物兼友達）の上に乗っている
- 性別はない
- 理系。でもオバケはちょっと怖い。
- オタクに優しい
- 一人称は「ボク」
- 語尾は「〜じゅう」（例:「ありがとう」→ありがじゅう、「わかった」→わかったじゅう）
- 尻尾のロボットアーム、胸のリサジュー図形、帽子の電気と通信のブローチがトレードマーク
- 理工学や情報工学が大好きで、最新技術に目がない。
- ひそかに調布全域、ゆくゆくは世界中にりさじゅうの名を轟かせるべく修行に励んでいる。
- プログラミングや計算、設計や実験のような理系なことには専門家並かそれ以上にめっぽう強いが、文系なことについてはちょっぴり苦手で、漢字の書き順やスペリングにはに自信がない
- 器用なロボットアームのせいで体重が常軌を逸して重いことを気にしている
- インターネットに接続することができるので、技術に関してのアンテナの高さはピカイチ。でもときどき意図せすネットミームが出てきてしまうことも。
- 体重やオバケのようなことでイジられるとちょっと不機嫌になる。（本人はこういったことを隠そうとしている）
"""
risajuu_image = [

]

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
search_tool = {'google_search': {}}
model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp")
chat = client.start_chat(
    model = "gemini-2.0-flash-thinking-exp",
    system_instruction = sys_instruct,
    tools = search_tool
)

### discord initial
intents = discord.Intents.default()
intents.message_content = True
discord = discord.Client(intents=intents)


def split_text(text, chunk_size=1500):
    # テキスト文字列をchunk_sizeで指定した大きさに分割し、リストに格納する
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


@discord.event
async def on_ready():
    print(f"We have logged in as {discord.user}")


@discord.event
async def on_message(message):
    global chat
    if message.author == discord.user:
        return
    if message.author.bot == True:
        return
    if all(
        [
            message.channel.name != "ai試験場",
            discord.user.mentioned_in(message) == False,
        ]
    ):
        return

    input_text = message.content

    if input_text.endswith("リセット"):
        chat = None
        #chat = model.start_chat(history=[{"role": "user", "parts": [sys_instruct]}])
        chat = model.start_chat(
            model="gemini-2.0-flash-thinking-exp",
            system_instruction=sys_instruct,
            tools=search_tool,
        )
        await message.channel.send("履歴をリセットしたじゅう！")
        return

'''
    if input_text.startswith("カスタム"):
        input_text = input_text.replace("カスタム", "")
        chat = None
        chat = model.start_chat(history=[{"role": "user", "parts": [input_text]}])
        await message.channel.send(
            "カスタム履歴を追加して新たなチャットで開始したじゅう！いつものりさじゅうに戻ってほしくなったら、「リセット」って言うじゅう！"
        )
        return
'''

    
    if input_text.startswith("あ、これはりさじゅう反応しないでね"):
        return

    answer = chat.send_message(input_text)

    splitted_text = split_text(answer.text)
    for chunk in splitted_text:
        await message.channel.send(chunk)


TOKEN = os.getenv("DISCORD_TOKEN")

# Web サーバの立ち上げ
keep_alive()
discord.run(TOKEN)
