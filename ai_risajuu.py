import os
from enum import Enum

from google import genai
from google.genai import types
from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    Tool,
)
from pydantic import BaseModel

from functions import declarations, declarations_without_wait_event, functions


# AIりさじゅうの基本設定
class RisajuuConfig(BaseModel):
    google_api_key: str
    main_model_name: str
    sub_model_name: str
    common_instruction: str
    system_instruction: str


# 履歴インポート・エクスポート用の構造体
class History(BaseModel):
    contents: list[types.Content]


# 返答メッセージの種類
class ReplyType(str, Enum):
    text = "text"
    log = "log"
    thought = "thought"
    file = "file"


# 返答メッセージの種類と内容
class Reply(BaseModel):
    type: ReplyType
    body: str


# 履歴の保持と回答の生成を担当するクラス
# Discordのサーバー・DMごとにインスタンス化される
class AI_risajuu:
    def __init__(self, config):
        self.config = config
        self.client = genai.Client(api_key=config.google_api_key)
        self.chat = self.client.aio.chats.create(model=config.main_model_name)
        self.google_search_tool = Tool(google_search=GoogleSearch())
        self.url_context_tool = Tool(url_context=types.UrlContext())
        self.my_tools = Tool(function_declarations=declarations())
        # self.tools = [self.google_search_tool, self.url_context_tool]
        self.tools = [self.my_tools]
        self.my_tools_no_wait = Tool(function_declarations=declarations_without_wait_event())
        self.tools_no_wait = [self.my_tools_no_wait]
        self.current_system_instruction = config.system_instruction
        self.files = []
        self.include_thoughts = False
        self.logging = False
        self.memo = ""

    def log(self, text):
        if self.logging:
            print(text)

    def toggle_thinking(self):
        new = not self.include_thoughts
        self.include_thoughts = new
        return new

    def toggle_logging(self):
        new = not self.logging
        self.logging = new
        return new

    def add_history(self, content):
        self.chat._comprehensive_history.append(content)
        self.chat._curated_history.append(content)

    def reset_files(self):
        for file in self.files:
            self.client.files.delete(name=file.name)
        self.files = []

    def import_history(self, json_str):
        # 履歴の読み込み
        history = History.model_validate_json(json_str)
        self.chat = self.client.aio.chats.create(model=self.config.main_model_name, history=history.contents)
        self.memo = ""
        self.reset_files()

    def export_history(self):
        # 履歴の書き出し
        history = History(contents=self.chat.get_history())
        return history.model_dump_json(indent=2)

    def set_custom_instruction(self, custom_instruction):
        # プロンプトのカスタム
        self.current_system_instruction = custom_instruction
        self.memo = ""

    async def react(self, input_text):
        # リアクションをサブのモデルで生成
        emoji = await self.client.aio.models.generate_content(
            model=self.config.sub_model_name,
            contents=[
                """
                    # 指示
                    「"""
                + input_text
                + """」というメッセージへのリアクションとして適切な絵文字を一つだけ選んでください。
                # 注意
                出力には**絵文字一文字のみ**を取ってください。余計なテキストや説明は**絶対に**含めず、**絵文字一文字のみ**を出力してください。
                """
            ],
            config=GenerateContentConfig(safety_settings=get_safety_settings()),
        )
        return emoji.text.strip()

    async def reply(
        self,
        input_text=None,
        attachments=[],
        function_response=[],
    ):
        # テキストと添付ファイルに対する返答を生成する
        if input_text and input_text.startswith("あ、これはりさじゅう反応しないでね"):
            pass
        else:
            text_parts = [types.Part.from_text(text=input_text)] if input_text else []
            files = []
            for attachment in attachments:
                await attachment.save(attachment.filename)
                files.append(
                    self.client.files.upload(
                        file="./" + attachment.filename,
                    )
                )
                os.remove(attachment.filename)
            parts = text_parts
            parts.extend(files)
            parts.extend(function_response)
            solo = False
            if parts == []:
                solo = True
                parts = types.Part.from_text(text="")

            self.files.extend(files)

            config = GenerateContentConfig(
                system_instruction=f"{self.config.common_instruction}\n{self.current_system_instruction}\n{self.memo}",
                thinking_config=types.ThinkingConfig(include_thoughts=self.include_thoughts),
                tools=self.tools if not solo else self.tools_no_wait,
                safety_settings=get_safety_settings(),
                # tool_config=types.ToolConfig(function_calling_config=types.FunctionCallingConfig(mode="ANY")),
            )
            # 返答をストリーミングで生成する
            # そのままだと区切りが中途半端なため、改行区切りでyieldする
            buffer = ""
            function_calls = []
            self.log("start")
            async for chunk in await self.chat.send_message_stream(message=parts, config=config):
                self.log("chunk")
                for part in chunk.candidates[0].content.parts or []:
                    self.log("part")
                    if not part.text:
                        if buffer != "":
                            yield Reply(type=ReplyType.text, body=buffer)
                            buffer = ""

                        if part.function_call:
                            self.log("function_call")
                            function_calls.append(part.function_call)
                        else:
                            self.log("*unreachable* not function_call")

                        continue

                    if part.thought:
                        self.log("thought")
                        if buffer != "":
                            yield Reply(type=ReplyType.text, body=buffer)
                            buffer = ""
                        yield Reply(type=ReplyType.thought, body=part.text)
                    else:
                        self.log("text")
                        buffer += part.text
                        pop = buffer.rsplit(sep="\n", maxsplit=1)
                        if len(pop) == 2:
                            yield Reply(type=ReplyType.text, body=pop[0])
                            buffer = pop[1]

            if buffer != "":
                yield Reply(type=ReplyType.text, body=buffer)

            if function_calls:
                results = []
                for function_call in function_calls:
                    # if function_call.name == "add_event_listener":
                    # Reply(type=ReplyType.log, body="add_event_listener")
                    # continue
                    if function_call.name == "memorize":
                        body = function_call.args["body"]
                        if self.memo and body:
                            self.memo += "\n"
                        self.memo += body
                        response = {"output": self.memo}
                    else:
                        try:
                            if function_call.name == "oracle":
                                prompt = function_call.args["question"]
                                response = {
                                    "output": functions()["oracle"](self.client, self.config.main_model_name, prompt)
                                }
                            else:
                                response = {"output": functions()[function_call.name](**function_call.args)}
                        except Exception as e:
                            response = {"error": repr(e)}

                    part = types.Part.from_function_response(name=function_call.name, response=response)

                    silent = function_call.name in ["add_event_listener", "memorize", "request_new_feature"]
                    if silent:
                        self.add_history(types.ModelContent(part))
                    else:
                        results.append(part)

                    log = function_call.name + "\n"
                    log += str(function_call.args) + "\n"
                    log += str(response)
                    yield Reply(type=ReplyType.log, body=log)

                if results != []:
                    self.log("recurse")
                    async for reply in self.reply(function_response=results):
                        yield reply
                    self.log("recurse end")

            self.log("reset check")
            if input_text and input_text.endswith("リセット"):
                self.current_system_instruction = self.config.system_instruction
                self.chat = self.client.aio.chats.create(model=self.config.main_model_name)
                self.reset_files()
                self.memo = ""
                yield Reply(type=ReplyType.text, body="履歴をリセットしたじゅう！")
            self.log("end")


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
