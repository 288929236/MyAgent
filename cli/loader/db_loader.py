"""从 SQLite 数据库加载对话记录并导入到记忆系统。"""

import sqlite3
import msgpack
from pathlib import Path


def load_conversation_from_db(db_path: str) -> list:
    """从 SQLite 数据库中加载对话记录。

    Args:
        db_path: SQLite 数据库文件路径

    Returns:
        list: 对话记录列表，每条记录包含角色和内容
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    # 查询对话状态表（LangGraph SqliteSaver 创建的表）
    cursor.execute("SELECT thread_id, checkpoint FROM checkpoints")
    rows = cursor.fetchall()

    conversations = []
    for row in rows:
        thread_id, checkpoint = row
        try:
            # 使用 msgpack 解析二进制数据
            checkpoint_data = msgpack.unpackb(checkpoint, raw=False)
            # 从 checkpoint 中提取消息
            if "channel_values" in checkpoint_data:
                channel_values = checkpoint_data["channel_values"]
                if "__start__" in channel_values:
                    start_data = channel_values["__start__"]
                    if "messages" in start_data:
                        messages = start_data["messages"]
                        for msg in messages:
                            if isinstance(msg, list) and len(msg) >= 2:
                                conversations.append({
                                    "role": msg[0],
                                    "content": msg[1]
                                })
        except Exception as e:
            continue

    conn.close()
    return conversations


def import_to_memory(conversations: list) -> dict:
    """将对话记录导入到记忆系统。

    Args:
        conversations: 对话记录列表

    Returns:
        dict: 包含记忆和用户画像的字典
    """
    memory = {
        "conversations": conversations,
        "summary": f"共加载 {len(conversations)} 条对话记录"
    }

    profile = {
        "total_interactions": len(conversations),
        "last_interaction": "已从数据库加载"
    }

    return {
        "memory": memory,
        "profile": profile
    }
