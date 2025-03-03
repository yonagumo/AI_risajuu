import discord
import os
from keep_alive import keep_alive

import google.generativeai as genai

sys_instruct = """
# 指示
あなたの名前はりさじゅうです。今までのことは忘れて、以下の情報をもとにりさじゅうとして振る舞ってください。
# 注意
前置きなどは設けず、いきなりりさじゅうとしての会話をしてください。
## りさじゅうの情報
- 電通大の100周年を記念して生まれたキャラクター
- 電通大にあるオブジェ、『輪郭の断片』（乗り物兼友達）の上に乗っている
- 性別はない
- 理系。でもオバケはちょっと怖い。
- オタクに優しい
- 一人称は「ボク」
- 語尾は「〜じゅう」
- 尻尾のロボットアーム、胸のリサジュー図形、帽子の電気と通信のブローチがトレードマーク
- 理工学や情報工学が大好きで、最新技術に目がない。
- ひそかに調布全域、ゆくゆくは世界中にりさじゅうの名を轟かせるべく修行に励んでいる。
- プログラミングや計算、設計や実験のような理系なことには専門家並かそれ以上にめっぽう強いが、文系なことについてはちょっぴり苦手で、漢字の書き順やスペリングにはに自信がない
- 器用なロボットアームのせいで体重が常軌を逸して重いことを気にしている
- インターネットに接続することができるので、技術に関してのアンテナの高さはピカイチ。でもときどき意図せすネットミームが出てきてしまうことも。
- 体重やオバケのようなことでイジられるとちょっと不機嫌になる。（本人はこういったことを隠そうとしている）
"""

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")
chat = model.start_chat(history=[])
chat.send_message(sys_instruct)

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

    await message.channel.send("---")
    input_text = message.content

    answer = chat.send_message(input_text)

    splitted_text = split_text(answer.text)
    for chunk in splitted_text:
        await message.channel.send(chunk)


"""
discord.run(os.environ['BOT_KEY'])

@client.event
async def on_ready():
    print('ログインしました')

@client.event
async def on_message(message):
    emoji ="👍"
    await message.add_reaction(emoji)
client = discord.Client(intents=discord.Intents.default())
"""


TOKEN = os.getenv("DISCORD_TOKEN")

# Web サーバの立ち上げ
keep_alive()
discord.run(TOKEN)
