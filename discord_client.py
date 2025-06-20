import asyncio
import os

import discord
from discord import Message
from pydantic import BaseModel

from ai_manager import Reply, ReplyType


# Discord用の設定項目
class DiscordConfig(BaseModel):
    token: str
    targets: list[tuple[str, str]]


# place: インスタンス作成判定に使用。サーバーまたはDM
# source: 送信先判定に使用。チャンネルまたはユーザー
class MessageInfo(BaseModel):
    message: object
    is_dm: bool
    place: object
    source: object


def split_message_text(text, chunk_size=1500):
    # 文字列をchunk_size文字ごとのリストにする
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


# Discordのイベントを監視するメインのクラス
class DiscordClient(discord.Client):
    def __init__(self, config: DiscordConfig, sender: asyncio.Queue):
        # メッセージイベントを受信するための設定
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

        self.config = config
        self.sender = sender

    async def on_ready(self):
        # Discordクライアントの準備が完了した
        print(f"We have logged in as {self.user}")

    async def on_message(self, message: Message):
        # メッセージが飛んできたら内部メッセージキューに追加
        # 送信者がボットなら無視
        if message.author.bot:
            return

        # DM判定
        is_dm = message.channel.type == discord.ChannelType.private

        if (
            is_dm
            or (message.guild.name, message.channel.name) in self.config.targets
            or self.user.mentioned_in(message)
        ):
            # TODO: 現状targetsに入っていないチャンネルにはリアクションも付けれない
            # DM判定をもとにMessageInfo.place, MessageInfo.sourceを設定
            if is_dm:
                place = message.channel
                source = message.author
            else:
                place = message.guild
                source = message.channel

            info = MessageInfo(message=message, is_dm=is_dm, place=place, source=source)
            await self.sender.put(info)

    async def send_message(self, destination, reply: Reply):
        body = reply.body
        match reply.type:
            case ReplyType.TEXT:
                # Discordは一度に2,000文字まで送信できる
                # 余裕をもって1,500文字に制限
                for chunk in split_message_text(body):
                    await destination.send(chunk)
            case ReplyType.FILE:
                await destination.send(file=discord.File(body, filename=os.path.basename(body)))
                os.remove(body)

    async def add_reaction(self, message: Message, reaction: str):
        # リアクションを付ける
        if reaction is not None:
            try:
                await message.add_reaction(reaction)
            except TypeError:
                print(f"reaction error: <{reaction}>")
