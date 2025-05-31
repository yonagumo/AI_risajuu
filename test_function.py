import random

get_weather_forecast_declaration = {
    "name": "get_weather_forecast",
    "description": "天気予報を取得する",
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

    return {"whether": weather, "temperature": temperature}
