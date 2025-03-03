import discord
import os
from keep_alive import keep_alive

import google.generativeai as genai
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash-latest')
chat = model.start_chat(history=[])

### discord initial
intents = discord.Intents.default()
intents.message_content = True
discord = discord.Client(intents=intents)

def split_text(text, chunk_size=1500):
  # テキスト文字列をchunk_sizeで指定した大きさに分割し、リストに格納する
  return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

@discord.event
async def on_ready():
  print(f'We have logged in as {discord.user}')


@discord.event
async def on_message(message):
  if message.author == discord.user:
    return
  if message.author.bot == True:
    return
  if all([
    message.channel.name != "ai試験場",
    discord.user.mentioned_in(message) == False
  ]):
    return

  await message.channel.send("---")
  input_text = message.content

  answer = chat.send_message(input_text)

  splitted_text = split_text(answer.text)
  for chunk in splitted_text:
    await message.channel.send(chunk)

'''
discord.run(os.environ['BOT_KEY'])

@client.event
async def on_ready():
    print('ログインしました')

@client.event
async def on_message(message):
    emoji ="👍"
    await message.add_reaction(emoji)
client = discord.Client(intents=discord.Intents.default())
'''


TOKEN = os.getenv("DISCORD_TOKEN")

# Web サーバの立ち上げ
keep_alive()
discord.run(TOKEN)