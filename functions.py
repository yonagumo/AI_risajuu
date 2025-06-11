import random

from google.genai import types
from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    Tool,
)


def declarations_without_wait_event():
    return [get_weather_forecast_declaration, memorize_declaration, request_new_feature_declaration, oracle_declaration]


def declarations() -> list[dict[str, any]]:
    # return declarations_without_wait_event().append(wait_event_declaration)
    ds = declarations_without_wait_event()
    ds.append(add_event_listener_declaration)
    return ds


def functions():
    # return {"get_weather_forecast": get_weather_forecast, "wait_event": wait_event}
    return {
        "get_weather_forecast": get_weather_forecast,
        "memorize": memorize,
        "add_event_listener": add_event_listener,
        "request_new_feature": request_new_feature,
        "oracle": oracle,
    }


wait_event_declaration = {
    "name": "wait_event",
    "description": "ユーザーからのメッセージなどのイベント発生を待機する。戻り値はイベントの種類と内容",
}


def wait_event() -> dict[str, str]:
    raise Exception


add_event_listener_declaration = {
    "name": "add_event_listener",
    "description": "ユーザーからのメッセージなどのイベント発生時の通知を有効化する。戻り値はイベントの種類と内容",
    # "behavior": "NON_BLOCKING",
}


def add_event_listener() -> dict[str, str]:
    raise Exception("登録済み")


memorize_declaration = {
    "name": "memorize",
    "description": "大切なことを忘れないように記憶に刻み付ける。戻り値はこれまで記憶した内容",
    "parameters": {
        "type": "object",
        "properties": {"body": {"type": "string", "description": "記憶する内容"}},
        "required": ["body"],
    },
}


def memorize(body) -> str:
    return body


oracle_declaration = {
    "name": "oracle",
    "description": "わからないことを聞くと答えてくれる",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "質問内容"},
        },
        "required": ["question"],
    },
}


def oracle(client, model, prompt):
    google_search_tool = Tool(google_search=GoogleSearch())
    url_context_tool = Tool(url_context=types.UrlContext())
    tools = [google_search_tool, url_context_tool]
    answer = client.models.generate_content(model=model, contents=[prompt], config=GenerateContentConfig(tools=tools))
    return answer.text


request_new_feature_declaration = {
    "name": "request_new_feature",
    "description": "できることを増やすために、開発者に新機能を要求する。戻り値は検討ステータス",
    "parameters": {
        "type": "object",
        "properties": {
            "feature": {"type": "string", "description": "要求する新機能"},
            "description": {"type": "string", "description": "その関数の使い方や引数、戻り値の説明"},
        },
        "required": ["feature"],
    },
}


def request_new_feature(feature: str, description: str):
    return {"status": "検討中"}


get_weather_forecast_declaration = {
    "name": "get_weather_forecast",
    "description": "天気予報を取得する。内容は天気と気温",
    "parameters": {
        "type": "object",
        "properties": {"location": {"type": "string", "description": "天気予報を取得したい地域。市区町村単位"}},
        "required": ["location"],
    },
}


def get_weather_forecast(location: str) -> dict[str, str | int]:
    if random.random() < 0.1:
        if location in ["調布", "調布市"]:
            raise Exception("データ取得に失敗")
        else:
            raise Exception("非対応の地域")

    temperature = random.randint(-10, 40)

    match random.randint(1, 3):
        case 1:
            weather = "晴れ"
        case 2:
            if random.random() < 0.1:
                weather = "濃霧"
            else:
                weather = "曇り"
        case 3:
            if temperature <= -3:
                weather = "雪"
            elif temperature <= 3:
                weather = "みぞれ"
            else:
                if random.random() < 0.1:
                    weather = "雷雨"
                else:
                    weather = "雨"

    return {"weather": weather, "temperature": temperature}
