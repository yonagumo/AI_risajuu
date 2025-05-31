from google import genai
import os

class Gemma_reaction:
    def __init__(self, api_key):
        self.model_name = os.getenv("SUB_MODEL_NAME")
        self.client = genai.Client(api_key=api_key)
        self.emojis = os.open("emoji_list.md", "r", encoding="utf-8").read().splitlines()