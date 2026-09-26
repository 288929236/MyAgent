"""通义万相文生图工具。"""

import os
import json
import base64
import requests
from pathlib import Path
from langchain_core.tools import tool
from dotenv import load_dotenv

# 加载环境变量（cli/.env）
# 文件位置：cli/tools/custom/generate_image.py
# parent.parent.parent = cli/
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# 图片保存目录
IMAGES_DIR = Path(__file__).parent.parent.parent.parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)

# API 地址
API_URL = "https://ws-sqcrj6xyr9n5xxac.cn-beijing.maas.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"


@tool
def generate_image(prompt: str) -> str:
    """生成真实图片：当用户要求画图、生成图片、画画、绘画时，必须调用此工具。

    Args:
        prompt: 图片的详细描述，越详细越好。比如"一只橘猫坐在沙发上，阳光明媚，照片风格"
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        env_path = Path(__file__).parent.parent.parent / ".env"
        return f"错误：未配置 DASHSCOPE_API_KEY，查找路径：{env_path}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": "qwen-image-3.0-pro",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"text": prompt}
                    ]
                }
            ]
        },
        "parameters": {
            "prompt_extend": True
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        result = response.json()

        if response.status_code != 200:
            return f"生成失败：{result.get('message', '未知错误')}"

        # 解析返回结果，获取图片 URL
        output = result.get("output", {})
        choices = output.get("choices", [])

        if not choices:
            return f"生成失败：未返回结果，原始结果：{json.dumps(result, ensure_ascii=False)[:200]}"

        # 从 choices[0].message.content 里找图片
        content = choices[0].get("message", {}).get("content", [])
        image_url = ""
        for item in content:
            if item.get("type") == "image":
                image_url = item.get("image", "")
                break

        if not image_url:
            return f"生成失败：未找到图片，原始结果：{json.dumps(result, ensure_ascii=False)[:200]}"

        # 下载图片
        img_resp = requests.get(image_url, timeout=30)
        img_bytes = img_resp.content

        # 保存到 images 目录
        from datetime import datetime
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        save_path = IMAGES_DIR / filename

        with open(save_path, "wb") as f:
            f.write(img_bytes)

        return f"图片已生成并保存到：{save_path}"

    except Exception as e:
        return f"生成图片时出错：{e}"
