"""记忆加载器：根据客户 ID 和会话 ID 加载对应记忆。"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_user_memory(client_id: str, thread_id: str) -> dict:
    """加载指定客户的记忆数据。

    目录结构：
        data/{client_id}/{thread_id}/memory/      记忆文件
        data/{client_id}/{thread_id}/profile/      用户画像

    如：data/user-001/001/memory/

    返回：
        {
            "memory": [...],      # 记忆列表
            "profile": {...},     # 用户画像
        }
    """
    user_dir = DATA_DIR / client_id / thread_id
    memory_dir = user_dir / "memory"
    profile_dir = user_dir / "profile"

    memory_files = []
    if memory_dir.exists():
        memory_files = list(memory_dir.glob("*.json"))

    memories = []
    for f in memory_files:
        with open(f, "r", encoding="utf-8") as fp:
            memories.append(json.load(fp))

    profile = {}
    profile_file = profile_dir / "profile.json"
    if profile_file.exists():
        with open(profile_file, "r", encoding="utf-8") as fp:
            profile = json.load(fp)

    return {
        "memory": memories,
        "profile": profile,
    }
