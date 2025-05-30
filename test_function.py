import random

get_whether_forecast_declaration = {
    "name": "get_whether_forecast",
    "description": "天気予報を取得する",
    "parameters": {
        "type": "object",
        "properties": {"location": {"type": "string", "description": "天気予報を取得したい地域。市区町村単位"}},
        "required": ["location"],
    },
}


def get_whether_forecast(location: str) -> dict[str, str | int]:
    r = {"whether": None, "temperature": None}
    match random.randint(1, 4):
        case 1:
            r["whether"] = "晴れ"
        case 2:
            r["whether"] = "曇り"
        case 3:
            r["whether"] = "雨"
        case 4:
            r["whether"] = "雪"
    r["temperature"] = random.randint(-10, 50)
    return r
