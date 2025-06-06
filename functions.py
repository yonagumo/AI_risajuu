import random


def declarations():
    return [send_message_declaration, wait_event_declaration, get_weather_forecast_declaration]


def functions():
    return {"send_message": send_message, "get_weather_forecast": get_weather_forecast, "wait_event": wait_event}


wait_event_declaration = {
    "name": "wait_event",
    "description": "ユーザーからのメッセージなどのイベント発生を待機する。戻り値はイベントの種類と内容",
}


def wait_event() -> dict[str, str]:
    raise Exception


send_message_declaration = {
    "name": "send_message",
    "description": "Discordを使用してメッセージを送る。戻り値は送信ステータス",
    "parameters": {
        "type": "object",
        "properties": {"body": {"type": "string", "description": "送信するメッセージの本文"}},
        "required": ["body"],
    },
}


def send_message(body) -> dict[str, str]:
    raise Exception


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
    temperature = random.randint(-10, 40)
    match random.randint(1, 3):
        case 1:
            weather = "晴れ"
        case 2:
            weather = "曇り"
            raise Exception
        case 3:
            if temperature <= -3:
                weather = "雪"
            elif temperature <= 3:
                weather = "みぞれ"
            else:
                if random.random() < 0.9:
                    weather = "雨"
                else:
                    weather = "雷雨"

    return {"weather": weather, "temperature": temperature}
