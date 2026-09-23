"""用户数据库操作。

管理用户信息和对话历史。
"""

import sqlite3
from pathlib import Path
from datetime import datetime

from paths import get_data_dir

# 数据库文件路径
DB_PATH = get_data_dir() / "users.db"


def init_user_db():
    """初始化用户数据库，创建用户表和对话表。"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 创建用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            client_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建对话表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            thread_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def login(username: str, password: str) -> dict | None:
    """用户登录。

    如果用户不存在，自动创建新用户。
    返回用户信息，如果登录失败返回 None。
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 检查用户是否存在
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user is None:
        # 用户不存在，自动创建新用户
        client_id = f"user_{username}"
        cursor.execute(
            "INSERT INTO users (username, password, client_id) VALUES (?, ?, ?)",
            (username, password, client_id)
        )
        conn.commit()
        user = (cursor.lastrowid, username, password, client_id, datetime.now())

    conn.close()

    # 返回用户信息
    return {
        "id": user[0],
        "username": user[1],
        "client_id": user[3],
    }


def get_user_conversations(client_id: str) -> list:
    """获取指定用户的所有对话历史。"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute(
        "SELECT thread_id, title, created_at FROM conversations WHERE client_id = ? ORDER BY updated_at DESC",
        (client_id,)
    )
    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "thread_id": row[0],
            "title": row[1],
            "created_at": row[2],
        }
        for row in rows
    ]


def create_conversation(client_id: str, thread_id: str, title: str = "新对话"):
    """创建新对话。"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO conversations (client_id, thread_id, title) VALUES (?, ?, ?)",
        (client_id, thread_id, title)
    )

    conn.commit()
    conn.close()


# 初始化数据库
init_user_db()
