import asyncio
import datetime
import random
import tempfile
from enum import Enum
from typing import Any

from pydantic import BaseModel

from ai_manager import AIConfig, AIManager, Reply, ReplyType
from discord_client import MessageInfo


class RisajuuConfig(BaseModel):
    ai_config: AIConfig
    reaction_probability: float


# Event：Risajuuがloopで受け取る
# Action：Risajuuがmessage_routerに送る


# イベントの種類
class EventType(str, Enum):
    DISCORD = "discord"
    RESPONSE = "response"
    REACTION = "reaction"
    REPLY_BEGIN = "reply_begin"


# イベントの種類と内容
class Event(BaseModel):
    type: EventType
    trigger: object | None
    body: Any


# アクションの種類
class ActionType(str, Enum):
    MESSAGE = "message"
    REACTION = "reaction"
    REPLY_BEGIN = "reply_begin"


class MessageAction(BaseModel):
    destination: object
    content: Reply
    will_continue: bool


class ReactionAction(BaseModel):
    message: object
    emoji: str


# アクションの種類と内容
class Action(BaseModel):
    type: ActionType
    body: Any


class Risajuu:
    def __init__(self, tg: asyncio.TaskGroup, config: RisajuuConfig):
        self.tg = tg
        self.config = config
        self.ai_manager = AIManager(config.ai_config)
        self.receiver = asyncio.Queue()
        self.sender = asyncio.Queue()

    async def boot(self):
        while True:
            event: Event = await self.receiver.get()

            match event.type:
                case EventType.DISCORD:
                    info: MessageInfo = event.body
                    self.tg.create_task(self.add_reaction(info))
                    self.tg.create_task(self.reply_to_message(info))
                case EventType.RESPONSE:
                    (reply, will_continue) = event.body
                    action = Action(
                        type=ActionType.MESSAGE,
                        body=MessageAction(
                            destination=event.trigger.source, content=reply, will_continue=will_continue
                        ),
                    )
                    await self.sender.put(action)
                case EventType.REACTION:
                    emoji = event.body
                    action = Action(
                        type=ActionType.REACTION, body=ReactionAction(message=event.trigger.message, emoji=emoji)
                    )
                    await self.sender.put(action)
                case EventType.REPLY_BEGIN:
                    action = Action(type=ActionType.REPLY_BEGIN, body=event.body)
                    await self.sender.put(action)

    async def add_reaction(self, info: MessageInfo):
        # 指定した確率でリアクションを付ける
        if random.random() < self.config.reaction_probability:
            reaction = await self.ai_manager.react(info.message.content)
            event = Event(type=EventType.REACTION, body=reaction, trigger=info)
            await self.receiver.put(event)

    async def reply_to_message(self, info: MessageInfo):
        # メッセージへの返答を生成してキューに登録する
        message = info.message
        input_text = message.content
        risajuu = self.ai_manager

        if input_text.startswith("あ、これはりさじゅう反応しないでね"):
            return

        if input_text.startswith("カスタム\n"):
            custom_instruction = input_text.replace("カスタム\n", "")
            risajuu.set_custom_instruction(custom_instruction)
            text = "カスタム履歴を追加して新たなチャットで開始したじゅう！いつものりさじゅうに戻ってほしくなったら、「リセット」って言うじゅう！"
            # await message.channel.send(text)
            reply = Reply(type=ReplyType.TEXT, body=text)
            event = Event(type=EventType.RESPONSE, trigger=info, body=(reply, False))
            await self.receiver.put(event)
            return

        if input_text.startswith("インポート"):
            if len(message.attachments) == 1 and message.attachments[0].filename.endswith(".json"):
                json_data = await message.attachments[0].read()
                json_str = json_data.decode("utf-8").replace("\n", "")
                risajuu.import_history(json_str)
                text = "履歴をインポートしたじゅう！"
            else:
                text = "インポートするには、1つのJSONファイルを添付してほしいじゅう！"
            # await message.channel.send(text)
            reply = Reply(type=ReplyType.TEXT, body=text)
            event = Event(type=EventType.RESPONSE, trigger=info, body=(reply, False))
            await self.receiver.put(event)
            return

        if input_text.endswith("エクスポート"):
            text = "履歴をエクスポートするじゅう！"
            # await message.channel.send(text)
            reply = Reply(type=ReplyType.TEXT, body=text)
            event = Event(type=EventType.RESPONSE, trigger=info, body=(reply, False))
            await self.receiver.put(event)

            json_str = risajuu.export_history()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = f"risajuu_history_{timestamp}_"
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".json", prefix=prefix, mode="w", encoding="utf-8"
            ) as file:
                file.write(json_str)
                file.flush()
                # await message.channel.send(file=discord.File(file.name, filename=os.path.basename(file.name)))
                reply = Reply(type=ReplyType.FILE, body=file.name)
                event = Event(type=EventType.RESPONSE, trigger=info, body=(reply, False))
                await self.receiver.put(event)
            return

        if input_text.endswith("リセット"):
            risajuu.current_system_instruction = risajuu.config.system_instruction
            risajuu.chat = risajuu.client.aio.chats.create(model=risajuu.config.main_model_name)
            risajuu.reset_files()
            reply = Reply(type=ReplyType.TEXT, body="履歴をリセットしたじゅう！")
            event = Event(type=EventType.RESPONSE, trigger=info, body=(reply, False))
            await self.receiver.put(event)
            return

        # if message.content == "file_list":
        #     text = ""
        #     for file in risajuu.client.files.list():
        #         meta = risajuu.client.files.get(name=file.name)
        #         text += f"・{file.name}: {meta}\n"
        #     for t in split_message_text(text, chunk_size=2000):
        #         await message.channel.send(t)
        #     return

        # 生成された回答を順次送信する
        # 入力中表示のために１回分先に生成する
        gen = risajuu.reply(message.content, message.attachments)
        try:
            buffer = await gen.__anext__()
        except StopAsyncIteration:
            pass
        else:
            await self.receiver.put(Event(type=EventType.REPLY_BEGIN, trigger=None, body=info.source))
            async for reply in gen:
                event = Event(type=EventType.RESPONSE, trigger=info, body=(buffer, True))
                await self.receiver.put(event)
                buffer = reply
            event = Event(type=EventType.RESPONSE, trigger=info, body=(buffer, False))
            await self.receiver.put(event)
