import os

from google import genai
from google.genai import types
from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    Tool,
)
from httpx import ReadTimeout
from pydantic import BaseModel


class LLMConfig(BaseModel):
    google_api_key: str
    main_model_name: str
    sub_model_name: str
    common_instruction: str
    system_instruction: str


# 履歴インポート・エクスポート用の構造体
class History(BaseModel):
    contents: list[types.Content]


# 履歴の保持と回答の生成を担当するクラス
# Discordのサーバー・DMごとにインスタンス化される
class LLMChat:
    def __init__(self, config):
        self.config = config
        self.client = genai.Client(api_key=config.google_api_key)
        self.chat = self.client.aio.chats.create(model=config.main_model_name)
        self.google_search_tool = Tool(google_search=GoogleSearch())
        self.url_context_tool = Tool(url_context=types.UrlContext())
        self.current_system_instruction = config.system_instruction
        self.files = []
        # TODO: チャットに初期履歴（addEventListener）を入れる

    # def reset_files(self):
    #     for file in self.files:
    #         self.client.files.delete(name=file.name)
    #     self.files = []

    def get_files(self) -> str:
        # アップロード済みファイルのリストを取得
        text = ""
        for file in self.client.files.list():
            meta = self.client.files.get(name=file.name)
            text += f"・{file.name}: {meta}\n"
        return text if text else "アップロード済みファイルはありません。"

    def import_history(self, json_str):
        # 履歴の読み込み
        history = History.model_validate_json(json_str)
        self.chat = self.client.aio.chats.create(model=self.config.main_model_name, history=history.contents)
        # self.reset_files()

    def export_history(self):
        # 履歴の書き出し
        history = History(contents=self.chat.get_history())
        return history.model_dump_json(indent=2)

    def set_custom_instruction(self, custom_instruction):
        # プロンプトのカスタム
        self.current_system_instruction = custom_instruction

    async def react(self, input_text):
        # リアクションをサブのモデルで生成
        emoji = await self.client.aio.models.generate_content(
            model=self.config.sub_model_name,
            contents=[reaction_prompt(input_text)],
            config=GenerateContentConfig(safety_settings=get_safety_settings()),
        )
        return emoji.text.strip()

    async def reply(self, input_text: str, attachments=[]):
        # テキストと添付ファイルに対する返答を生成する
        parts = []
        if input_text:
            # テキストがある場合はテキストをパーツに追加
            parts.append(types.Part.from_text(text=input_text))

        files = []
        for attachment in attachments:
            await attachment.save(attachment.filename)
            files.append(
                self.client.files.upload(
                    file="./" + attachment.filename,
                )
            )
            # 一時ファイルを削除
            os.remove(attachment.filename)
        parts.extend(files)

        self.files.extend(files)

        # タイムアウトを１分に設定
        config = GenerateContentConfig(
            system_instruction=self.config.common_instruction + "\n" + self.current_system_instruction,
            tools=[self.google_search_tool, self.url_context_tool],
            safety_settings=get_safety_settings(),
            http_options=types.HttpOptions(timeout=60000),
        )

        # 返答をストリーミングで生成する
        # そのままだと区切りが中途半端なため、改行区切りでyieldする
        buffer = ""
        error = None
        try:
            async for chunk in await self.chat.send_message_stream(message=parts, config=config):
                # print(chunk.candidates[0].finish_reason)
                if chunk.text:
                    buffer += chunk.text
                    pop = buffer.rsplit(sep="\n", maxsplit=1)
                    if len(pop) == 2:
                        yield pop[0]
                        buffer = pop[1]
                else:
                    if buffer != "":
                        yield buffer
                        buffer = ""
        except Exception as err:
            error = type(err)
        finally:
            if buffer != "":
                yield buffer
            if error:
                yield error


def reaction_prompt(input_text):
    # リアクションを生成するためのプロンプト
    return (
        "# 指示\n"
        "「" + input_text + "」というメッセージへのリアクションとして適切な絵文字を一つだけ選んでください。\n"
        "# 注意\n"
        "出力には**絵文字一文字のみ**を取ってください。余計なテキストや説明は**絶対に**含めず、**絵文字一文字のみ**を出力してください。"
    )


def get_safety_settings():
    # 安全フィルタ設定：ブロックなし
    safety_settings = [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
    ]
    return safety_settings
