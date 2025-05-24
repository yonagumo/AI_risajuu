import datetime
import json
import os
import tempfile

from google import genai
from google.genai import types
from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    Tool,
)


def split_message_text(text, chunk_size=1500):
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


class Reply:
    def __init__(self):
        self.text = []
        self.attachments = []


class AI_risajuu:
    def __init__(self, api_key, system_instruction, common_instruction):
        self.model_name = os.getenv("MAIN_MODEL_NAME")
        self.google_search_tool = Tool(google_search=GoogleSearch())
        self.url_context_tool = Tool(url_context=types.UrlContext())
        self.client = genai.Client(api_key=api_key)
        self.chat_history = []
        self.system_instruction = system_instruction
        self.current_system_instruction = system_instruction
        self.common_instruction = common_instruction

    def custom(self, custom_instruction):
        self.current_instruction = custom_instruction + self.common_instruction
        reply = Reply()
        reply.text = [
            "カスタム履歴を追加して新たなチャットで開始したじゅう！いつものりさじゅうに戻ってほしくなったら、「リセット」って言うじゅう！"
        ]
        return reply

    def export_history(self):
        reply = Reply()
        reply.text = ["履歴をエクスポートするじゅう！"]
        json_data = json.dumps(self.chat_history, ensure_ascii=False, indent=2)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"risajuu_history_{timestamp}_"
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".json", prefix=prefix, mode="w", encoding="utf-8"
        ) as file:
            file.write(json_data)
            file.flush()
            reply.attachments.append(file.name)
        return reply

    def import_history(self, history):
        reply = Reply()
        if history:
            self.chat_history.extend(history)
            reply.text = ["履歴をインポートしたじゅう！"]
        else:
            reply.text = ["インポートするには、1つのJSONファイルを添付してほしいじゅう！"]
        return reply

    def chat(self, input_text, _attachments):
        if input_text.startswith("あ、これはりさじゅう反応しないでね"):
            return

        reply = Reply()

        self.chat_history.append({"role": "user", "parts": [input_text]})
        answer = self.generate_answer(str(self.chat_history))
        self.chat_history.append({"role": "model", "parts": [answer.text.strip()]})

        reply.text = split_message_text(answer.text)

        if input_text.endswith("リセット"):
            self.chat_history = []
            self.current_instruction = self.system_instruction
            reply.text.append("履歴をリセットしたじゅう！")

        return reply

    def generate_answer(self, history):
        return self.client.models.generate_content(
            model=self.model_name,
            contents=history,
            config=GenerateContentConfig(
                system_instruction=self.current_system_instruction,
                tools=[self.google_search_tool, self.url_context_tool],
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
