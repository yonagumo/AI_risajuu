import copy
import datetime
import json
import tempfile
from typing import Optional

from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig, Tool
from pydantic import BaseModel


class Message(BaseModel):
    bot: bool
    author_display_name: str
    author_name: str
    created_at: str
    body: str


class Savedata(BaseModel):
    custom_instruction: Optional[str]
    history: list[Message]


class Reply(BaseModel):
    texts: list[str] = []
    thoughts: list[str] = []
    attachments: list[str] = []


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

    def custom(self, custom_instruction: str) -> Reply:
        self.current_system_instruction = custom_instruction
        text = ["カスタム履歴を追加して新たなチャットで開始したじゅう！いつものりさじゅうに戻ってほしくなったら、「リセット」って言うじゅう！"]
        return Reply(texts=[text])

    def export_savedata(self) -> Reply:
        text = "履歴をエクスポートするじゅう！"
        attachments = []
        # json_data = json.dumps(self.chat_history, ensure_ascii=False, indent=2)
        instruction = None if self.current_system_instruction == self.system_instruction else self.current_system_instruction
        json_data = Savedata(custom_instruction=instruction, history=self.chat_history).model_dump_json(indent=2)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"risajuu_history_{timestamp}_"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", prefix=prefix, mode="w", encoding="utf-8") as file:
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

    def chat(self, input: Message, _attachments: Optional[str]) -> Reply:
        if input.body.startswith("あ、これはりさじゅう反応しないでね"):
            return Reply()

        reply = Reply()

        self.chat_history.append(input)
        response = self.generate_answer(self.chat_history)
        message = Message(
            bot=True,
            author_display_name="AIりさじゅう",
            author_name="AIりさじゅう#2535",
            created_at=input.created_at,
            body=response.text,
        )
        self.chat_history.append(message)

        for part in response.candidates[0].content.parts:
            if part.thought:
                reply.thoughts.append(part.text)

        reply.texts = split_message_text(message.body)

        if input.body.endswith("リセット"):
            self.chat_history = []
            self.current_system_instruction = self.system_instruction
            reply.texts.append("履歴をリセットしたじゅう！")

        return reply

    def generate_answer(self, history):
        contents = []
        for h in history:
            role = "model" if h.bot else "user"
            dic = copy.copy(h.model_dump())
            del dic["bot"]
            jsonstr = json.dumps(dic, ensure_ascii=False)
            content = types.Content(role=role, parts=[types.Part.from_text(text=jsonstr)])
            contents.append(content)

        return self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=GenerateContentConfig(
                system_instruction=self.common_instruction + self.current_system_instruction,
                # tools=self.tools,
                # thinking_config=types.ThinkingConfig(include_thoughts=True),
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
