import copy
import datetime
import json
import tempfile

from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig, Tool

# class Message:
#     bot: bool
#     author_display_name: str
#     author_name: str
#     created_at: str
#     body: str
#     def __init__(self, bot, author_display_name, author_name, created_at, body):
#         self.bot = bot
#         self.author_display_name = author_display_name
#         self.author_name = author_name
#         self.created_at = created_at
#         self.body = body


def newMessage(bot, author_display_name, author_name, created_at, body):
    message = {}
    message["bot"] = bot
    message["author_display_name"] = author_display_name
    message["author_name"] = author_name
    message["created_at"] = created_at
    message["body"] = body
    return message


class Reply:
    def __init__(self):
        self.texts = []
        self.attachments = []


def split_message_text(text, chunk_size=1500):
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

    def custom(self, custom_instruction):
        self.current_system_instruction = custom_instruction + self.common_instruction
        reply = Reply()
        reply.texts = [
            "カスタム履歴を追加して新たなチャットで開始したじゅう！いつものりさじゅうに戻ってほしくなったら、「リセット」って言うじゅう！"
        ]
        return reply

    def export_history(self):
        reply = Reply()
        reply.texts = ["履歴をエクスポートするじゅう！"]
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
            reply.texts = ["履歴をインポートしたじゅう！"]
        else:
            reply.texts = ["インポートするには、1つのJSONファイルを添付してほしいじゅう！"]
        return reply

    def chat(self, input, _attachments):
        if input["body"].startswith("あ、これはりさじゅう反応しないでね"):
            return

        reply = Reply()

        self.chat_history.append(input)
        response = self.generate_answer(self.chat_history)
        message = newMessage(True, "AIりさじゅう", "AIりさじゅう#2535", input["created_at"], response.text)
        self.chat_history.append(message)
        reply.texts = split_message_text(message["body"])

        if input["body"].endswith("リセット"):
            self.chat_history = []
            self.current_system_instruction = self.system_instruction
            reply.texts.append("履歴をリセットしたじゅう！")

        return reply

    def generate_answer(self, history):
        contents = []
        for h in history:
            role = "model" if h["bot"] else "user"
            dic = copy.copy(h)
            del dic["bot"]
            jsonstr = json.dumps(dic, ensure_ascii=False)
            content = types.Content(role=role, parts=[types.Part.from_text(text=jsonstr)])
            contents.append(content)

        return self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=GenerateContentConfig(
                system_instruction=self.current_system_instruction,
                tools=self.tools,
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
