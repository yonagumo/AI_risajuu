import os

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
    text = []
    export_history = None

class AI_risajuu:
    def __init__(self, api_key, system_instruction):
        self.model_name = "gemini-2.5-flash-preview-05-20"
        self.google_search_tool = Tool(google_search=GoogleSearch())
        self.client = genai.Client(api_key=api_key)
        self.chat_history = []
        self.system_instruction = system_instruction
        self.current_instruction = system_instruction
    
    def custom(self, instruction):
        self.chat_history = []
        self.current_instruction = instruction
        reply = Reply()
        reply.text = ["カスタムインストラクションで新たなチャットを開始したじゅう！いつものりさじゅうに戻ってほしくなったら、「リセット」って言うじゅう！"]
        return reply
    
    def export_history(self):
        reply = Reply()
        reply.text = ["履歴をエクスポートするじゅう！"]
        reply.export_history = self.chat_history
        return reply
    
    def import_history(self, history):
        reply = Reply()
        if history:
            self.chat_history = history
            reply.text = ["履歴をインポートしたじゅう！"]
        else:
            reply.text = ["JSONファイルを添付してほしいじゅう！"]
        return reply

    def chat(self, input_text):
        if input_text.startswith("あ、これはりさじゅう反応しないでね"):
            return
        
        reply = Reply()

        self.chat_history.append({"role": "user", "parts": [input_text]})
        answer = self.generate_answer(str(self.chat_history))
        self.chat_history.append({"role": "model", "parts": [answer.text]})

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
                system_instruction = self.current_instruction,
                #tools=[self.google_search_tool],
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