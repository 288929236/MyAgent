from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """查询某个城市的实时天气。

    Args:
        city: 城市名，例如"北京"
    """
    # 这里换成你真实的业务逻辑 / API
    return f"{city}今天晴，25℃"
