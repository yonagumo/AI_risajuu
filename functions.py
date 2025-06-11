import random


def declarations_without_wait_event():
    return [get_weather_forecast_declaration]


def declarations():
    return declarations_without_wait_event().append(wait_event_declaration)


def functions():
    return {"get_weather_forecast": get_weather_forecast, "wait_event": wait_event}


wait_event_declaration = {
    "name": "wait_event",
    "description": "ユーザーからのメッセージなどのイベント発生を待機する。戻り値はイベントの種類と内容",
}


def wait_event() -> dict[str, str]:
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
    if random.random() < 0.1:
        if location in ["調布", "調布市"]:
            raise Exception("データ取得に失敗")
        else:
            raise Exception("未対応の地域")

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
