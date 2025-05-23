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


class AI_risajuu:
    def __init__(self, api_key, system_instruction):
        self.model_name = "gemini-2.0-flash" #"gemini-2.5-flash-preview-05-20"
        self.google_search_tool = Tool(google_search=GoogleSearch())
        self.client = genai.Client(api_key=api_key)
        self.chat_history = []
        self.system_instruction = system_instruction

    def chat(self, input_text):
        if input_text.startswith("あ、これはりさじゅう反応しないでね"):
            return

        if input_text.endswith("リセット"):
            self.chat_history = []
            return ["履歴をリセットしたじゅう！"]

        #if input_text.startswith("カスタム"):
        #    system_instruction = input_text.replace("カスタム", "") + initial_message
        #    chat_history = []
        #    await message.channel.send(
        #        "カスタム履歴を追加して新たなチャットで開始したじゅう！いつものりさじゅうに戻ってほしくなったら、「リセット」って言うじゅう！"
        #    )
        #    return

        # if input_text.endswith("エクスポート"):
        #     await message.channel.send("履歴をエクスポートするじゅう！")
        #     with io.StringIO(str(chat_history)) as file:
        #         await message.channel.send(
        #             file=discord.File(
        #                 file,
        #                 "chat_history_" + str(datetime.datetime.now()) + ".txt",
        #             )
        #         )
        #     return

        # if input_text.endswith("インポート"):
        #     await message.channel.send("履歴をインポートするじゅう！")
        #     if message.attachments:
        #         attachment = message.attachments[0]
        #         if attachment.filename.endswith(".txt"):
        #             file = await attachment.read()
        #             chat_history = eval(file.decode("utf-8"))
        #             await message.channel.send("履歴をインポートしたじゅう！")
        #         else:
        #             await message.channel.send("テキストファイルを添付してほしいじゅう！")
        #             return
        #     else:
        #         await message.channel.send("テキストファイルを添付してほしいじゅう！")
        #     return

        self.chat_history.append({"role": "user", "parts": [input_text]})
        answer = self.generate_answer(str(self.chat_history))
        self.chat_history.append({"role": "model", "parts": [answer.text]})

        return split_message_text(answer.text)
    
    def generate_answer(self, history):
        return self.client.models.generate_content(
            model = self.model_name,
            contents = history,
            config = GenerateContentConfig(
                system_instruction = self.system_instruction,
                #tools = [self.google_search_tool],
                safety_settings = [
                    types.SafetySetting(
                        category = types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold = types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category = types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold = types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category = types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold = types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category = types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold = types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                ],
            ),
        )