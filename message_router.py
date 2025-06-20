import asyncio
from enum import Enum

from pydantic import BaseModel

from discord_client import DiscordClient, DiscordConfig, MessageInfo
from risajuu import Action, ActionType, Event, EventType, Risajuu, RisajuuConfig


# 基本設定
class AppConfig(BaseModel):
    discord_config: DiscordConfig
    risajuu_config: RisajuuConfig


# りさじゅうインスタンス辞書のキーのための現在の場所の種類
class InstanceType(str, Enum):
    SERVER = "server"
    DM = "dm"


# りさじゅうインスタンス辞書のキー
class InstanceID(BaseModel):
    type: InstanceType
    id: int

    class Config:
        frozen = True


class MessageRouter:
    def __init__(self, tg: asyncio.TaskGroup, config: AppConfig):
        self.tg = tg
        self.config = config
        self.message_queue = asyncio.Queue()
        # りさじゅうインスタンス
        # いつか再起動時に復旧できるようになるかも
        self.risajuu_instances = {}
        # Discordクライアントの初期化
        self.client = DiscordClient(self.config.discord_config, self.message_queue)

    def start(self):
        # メインループ
        self.tg.create_task(self.client.start(self.config.discord_config.token))
        self.tg.create_task(self.discord_loop())
        # りさじゅうインスタンスを起動時に復旧するなら下をアンコメントする
        # for risajuu_id in self.risajuu.instances.keys():
        #     tg.create_task(self.wait_risajuu(risajuu_id))

    async def discord_loop(self):
        # Discordからのメッセージを待機するループ
        while True:
            info: MessageInfo = await self.message_queue.get()

            # DMならチャンネルid、そうでなければサーバーidを使用する
            instance_type = InstanceType.DM if info.is_dm else InstanceType.SERVER
            risajuu_id = InstanceID(type=instance_type, id=info.place.id)

            # サーバー・DMごとのりさじゅうインスタンスを指定
            if risajuu_id in self.risajuu_instances:
                risajuu = self.risajuu_instances[risajuu_id]
            else:
                # メッセージが送られてきた場所にりさじゅうのインスタンスがまだ無いときは作成する
                risajuu = Risajuu(self.tg, self.config.risajuu_config)
                self.risajuu_instances[risajuu_id] = risajuu
                # 並行処理用のタスクグループに登録
                self.tg.create_task(self.wait_risajuu(risajuu_id))
                self.tg.create_task(risajuu.boot())

            # りさじゅうインスタンスにメッセージイベントを送信
            event = Event(type=EventType.DISCORD, body=info, trigger=None)
            await risajuu.receiver.put(event)

    async def wait_risajuu(self, risajuu_id: InstanceID):
        # りさじゅうの行動を待機するループ
        risajuu = self.risajuu_instances[risajuu_id]
        while True:
            action: Action = await risajuu.sender.get()

            body = action.body
            match action.type:
                case ActionType.MESSAGE:
                    await self.client.send_message(body.destination, body.content)
                    # TODO continue判定を付ける
                    if body.will_continue:
                        await body.destination.typing()
                case ActionType.REACTION:
                    await self.client.add_reaction(body.message, body.emoji)
                case ActionType.REPLY_BEGIN:
                    await body.typing()
