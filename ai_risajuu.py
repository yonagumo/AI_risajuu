import copy
import datetime
import json
import tempfile
from typing import Any, Optional

from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig, Tool
from pydantic import BaseModel

import test_function


class Message(BaseModel):
    bot: bool
    author_display_name: str
    author_name: str
    created_at: str
    body: str


class FunctionCalling(BaseModel):
    call: types.FunctionCall
    result: dict[str, Any]


class Savedata(BaseModel):
    custom_instruction: Optional[str]
    history: list[Message | FunctionCalling]


class Reply(BaseModel):
    texts: list[str] = []
    logs: list[str] = []
    attachments: list[str] = []


class TextBuffer:
    def __init__(self):
        self.text = None

    def append(self, text):
        self.text = (self.text or "") + text

    def pop(self, created_at):
        if self.text is None:
            return None
        else:
            texts = self.text.rsplit(sep="\n", maxsplit=1)
            if len(texts) >= 2:
                self.text = texts[1]
                message = Message(
                    bot=True,
                    author_display_name="AIりさじゅう",
                    author_name="AIりさじゅう#2535",
                    created_at=created_at,
                    body=texts[0],
                )
                return message
            else:
                return None

    def flush(self, created_at):
        message = Message(
            bot=True,
            author_display_name="AIりさじゅう",
            author_name="AIりさじゅう#2535",
            created_at=created_at,
            body=self.text,
        )
        self.text = None
        return message


def split_message_text(text, chunk_size=1500) -> list[str]:
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


class AI_risajuu:
    def __init__(self, api_key, model_name, system_instruction, common_instruction):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.tools = [Tool(url_context=types.UrlContext), Tool(google_search=types.GoogleSearch)]
        self.chat_history = []
        self.system_instruction = system_instruction
        self.current_system_instruction = system_instruction
        self.common_instruction = common_instruction
        self.include_thoughts = False
        self.logging = False

    def log(self, log: str):
        if self.logging:
            print(log)

    def custom(self, custom_instruction: str) -> Reply:
        self.current_system_instruction = custom_instruction
        text = "カスタム履歴を追加して新たなチャットで開始したじゅう！いつものりさじゅうに戻ってほしくなったら、「リセット」って言うじゅう！"
        return Reply(texts=[text])

    def export_savedata(self) -> Reply:
        text = "履歴をエクスポートするじゅう！"
        attachments = []
        # json_data = json.dumps(self.chat_history, ensure_ascii=False, indent=2)
        instruction = (
            None if self.current_system_instruction == self.system_instruction else self.current_system_instruction
        )
        json_data = Savedata(custom_instruction=instruction, history=self.chat_history).model_dump_json(indent=2)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"risajuu_history_{timestamp}_"
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".json", prefix=prefix, mode="w", encoding="utf-8"
        ) as file:
            file.write(json_data)
            file.flush()
            attachments.append(file.name)
        return Reply(texts=[text], attachments=attachments)

    def import_savedata(self, savedata: Savedata) -> Reply:
        if savedata:
            self.current_system_instruction = savedata.custom_instruction or self.system_instruction
            self.chat_history = savedata.history
            text = "履歴をインポートしたじゅう！"
        else:
            text = "インポートするには、1つのJSONファイルを添付してほしいじゅう！"
        return Reply(texts=[text])

    def chat(self, input: Message, _attachments=[]) -> Reply:
        if input.body.startswith("あ、これはりさじゅう反応しないでね"):
            return Reply()

        self.log(f"回答生成開始：{input.body}")
        self.chat_history.append(input)
        response = self.generate_answer(self.chat_history)

        self.log("応答開始")
        reply = self.call_and_response(response, input.created_at)

        self.log("リセット確認")
        if input.body.endswith("リセット"):
            self.chat_history = []
            self.current_system_instruction = self.system_instruction
            reply.texts.append("履歴をリセットしたじゅう！")

        self.log("回答生成完了")
        return reply

    def poke(self, created_at) -> Reply:
        response = self.generate_answer(self.chat_history)
        reply = self.call_and_response(response, created_at)
        return reply

    def call_and_response(self, response, created_at):
        self.log("call_and_response")
        reply = Reply()
        remain = TextBuffer()
        for ci, chunk in enumerate(response):
            self.log(f"chunk: {ci}")
            self.log(chunk.model_dump_json())
            call = False
            for pi, part in enumerate(chunk.candidates[0].content.parts):
                self.log(f"part: {pi}")
                if not part.text:
                    self.log("not text")
                    tool_call = part.function_call
                    if tool_call:
                        self.log("関数呼び出し")
                        call = True
                        if remain.text is not None:
                            message = remain.flush(created_at)
                            self.chat_history.append(message)
                            reply.texts.extend(split_message_text(message.body))
                        # reply.logs.append("call: " + tool_call.model_dump_json())
                        log = "call: " + tool_call.model_dump_json()
                        if tool_call.name == "get_weather_forecast":
                            self.log("get_weather_forecast")
                            result = test_function.get_weather_forecast(**tool_call.args)
                            # reply.logs.append(f"result: {result}")
                            log += f"\nresult: {result}"
                        self.log(log)
                        log = "```" + log + "```"
                        reply.texts.append(log)
                        call_contents = FunctionCalling(call=tool_call, result=result)
                        self.chat_history.append(call_contents)
                    else:
                        self.log("*unreachable* not function calling")
                        continue
                elif part.thought:
                    self.log("思考")
                    if remain.text is not None:
                        message = remain.flush(created_at)
                        self.chat_history.append(message)
                        reply.texts.extend(split_message_text(message.body))
                    # reply.logs.append("thought: " + part.text)
                    reply.texts.append("```thought: " + part.text + "```")
                else:
                    self.log("メッセージ本体：" + chunk.text)
                    remain.append(chunk.text)
                    message = remain.pop(created_at)
                    if message:
                        self.chat_history.append(message)
                        reply.texts.extend(split_message_text(message.body))
            if call:
                if remain.text is not None:
                    message = remain.flush(created_at)
                    self.chat_history.append(message)
                    reply.texts.append(message.body)
                self.log("関数の戻り値をもとに回答生成")
                call_response = self.generate_answer(self.chat_history)
                self.log("再帰")
                r = self.call_and_response(call_response, created_at)
                self.log("再帰完了")
                reply.texts.extend(r.texts)
                reply.logs.extend(r.logs)
                reply.attachments.extend(r.attachments)
        if remain.text is not None:
            message = remain.flush(created_at)
            self.chat_history.append(message)
            reply.texts.append(message.body)
        self.log("return from call_and_response")
        return reply

    def generate_answer(self, history):
        contents = []
        for h in history:
            if isinstance(h, Message):
                role = "model" if h.bot else "user"
                dic = copy.copy(h.model_dump())
                del dic["bot"]
                jsonstr = json.dumps(dic, ensure_ascii=False)
                content = types.Content(role=role, parts=[types.Part.from_text(text=jsonstr)])
                contents.append(content)
            elif isinstance(h, FunctionCalling):
                function_response_part = types.Part.from_function_response(
                    name=h.call.name, response={"result": h.result}
                )
                append_contents = [
                    types.Content(role="model", parts=[types.Part(function_call=h.call)]),
                    types.Content(role="user", parts=[function_response_part]),
                ]
                contents.extend(append_contents)
            else:
                self.log("*unreachable* broken history")

        return self.client.models.generate_content_stream(
            model=self.model_name,
            contents=contents,
            config=GenerateContentConfig(
                system_instruction=self.common_instruction + self.current_system_instruction,
                # tools=self.tools,
                tools=[types.Tool(function_declarations=[test_function.get_weather_forecast_declaration])],
                thinking_config=types.ThinkingConfig(include_thoughts=self.include_thoughts),
                safety_settings=[
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
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
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                ],
            ),
        )
