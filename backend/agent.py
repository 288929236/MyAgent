import os
import sqlite3
import atexit
from pathlib import Path
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver

from tools_registry import get_tools
from agent_config import (
    MODEL_NAME,
    TEMPERATURE,
    MAX_TOKENS,
    ENABLE_TOKEN_STATS,
    LOG_TOKEN_PER_TURN,
    LOG_TOKEN_TOTAL,
)
from client_config import CLIENT_ID, THREAD_ID

# 加载 .env（在 backend/ 目录下运行时会自动读到 backend/.env）
load_dotenv()


def _wrap_token_stats(agent, stats):
    """包装 agent.invoke，自动统计每轮 token 使用。"""
    original_invoke = agent.invoke

    def tracked_invoke(*args, **kwargs):
        result = original_invoke(*args, **kwargs)

        # 从本轮最后一条 AI 消息里提取 token 使用情况
        messages = result.get("messages", [])
        usage = {}
        for msg in reversed(messages):
            meta = getattr(msg, "response_metadata", {}) or {}
            usage = meta.get("token_usage") or meta.get("usage") or {}
            if usage:
                break

        if usage:
            stats["prompt_tokens"] += usage.get("prompt_tokens", 0)
            stats["completion_tokens"] += usage.get("completion_tokens", 0)
            stats["total_tokens"] += usage.get("total_tokens", 0)
            stats["turn_count"] += 1
            # 记录每轮明细
            stats.setdefault("turns", []).append({
                "prompt": usage.get("prompt_tokens", 0),
                "completion": usage.get("completion_tokens", 0),
            })

        return result

    agent.invoke = tracked_invoke
    return agent


def build_agent(db_path: str):
    """组装并返回一个带记忆的 ReAct agent。"""
    model = ChatDeepSeek(
        model=MODEL_NAME,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )

    tools = get_tools()

    # 确保目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # SqliteSaver 需要传入连接对象，使用 sqlite3 连接
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    agent = create_react_agent(model, tools, checkpointer=checkpointer)

    # ===== 上下文 Token 统计 =====
    stats = {
        "prompt_tokens": 0,      # 累计用户输入 token
        "completion_tokens": 0,  # 累计模型输出 token
        "total_tokens": 0,       # 累计总 token
        "turn_count": 0,         # 对话轮数
    }

    if ENABLE_TOKEN_STATS:
        _wrap_token_stats(agent, stats)

    # 注册清理函数，确保程序退出时关闭数据库连接
    def cleanup():
        try:
            conn.close()
        except:
            pass
    atexit.register(cleanup)

    return agent, model, stats
