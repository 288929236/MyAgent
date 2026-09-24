"""工具自动发现 + 智能筛选入口。

1. _discover_tools()：自动扫描 tools/ 下所有 .py，收集全部 @tool 工具。
2. select_relevant_tools()：根据用户文本从所有工具中挑出相关的。
3. get_tools()：auto_select=False 时返回全部工具；True 时先筛选再返回。
4. 工作目录管理：work_dir / modify_log / init_workspace()
5. 快照管理：按用户/会话分组，按对话时间戳+工具时间戳命名
"""

import importlib
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from langchain_core.tools import BaseTool


# ===== 工作目录状态 =====
work_dir = Path.cwd()
modify_log = []

# ===== 用户与会话 =====
username = "user_ljy"
thread_id = "thread_001"
current_session_timestamp = ""

# 快照根目录：项目根目录下的 .snapshots/
snapshot_root = Path(__file__).parent.parent / ".snapshots"
snapshot_dir = snapshot_root / username / thread_id


def init_workspace(workspace_path: Path, user_name: str = "user_ljy", thread_name: str = "thread_001"):
    """初始化工作目录和快照目录。"""
    global work_dir, snapshot_dir, username, thread_id
    work_dir = workspace_path
    username = user_name
    thread_id = thread_name
    # 快照目录：.snapshots/{username}/{thread_id}/
    snapshot_dir = snapshot_root / username / thread_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)


def start_new_session():
    """开始新的一轮对话，生成新的对话时间戳。"""
    global current_session_timestamp
    current_session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


def _discover_tools():
    """扫描 tools/ 下所有 .py 文件，返回里面定义的全部工具。"""
    tools = []
    backend_dir = Path(__file__).parent
    tools_dir = backend_dir / "tools"

    for py_file in tools_dir.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue

        rel = py_file.relative_to(backend_dir).with_suffix("")
        module_path = ".".join(rel.parts)
        module = importlib.import_module(module_path)

        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, BaseTool):
                tools.append(obj)

    return tools


def select_relevant_tools(query: str, all_tools: list[BaseTool], top_k: int | None = None):
    """根据用户文本，从所有工具中挑出相关的。

    目前用字符串相似度做简单筛选，后续可替换为 embedding 向量检索
    或调用小模型判断。
    """
    query_lower = (query or "").lower().strip()
    if not query_lower:
        return list(all_tools)

    scored = []
    for tool in all_tools:
        # 工具名 + 描述拼在一起作为工具的"名片"
        text = f"{tool.name} {tool.description}".lower()
        score = SequenceMatcher(None, query_lower, text).ratio()
        scored.append((score, tool))

    scored.sort(key=lambda x: x[0], reverse=True)

    if top_k is None:
        top_k = len(all_tools)
    return [tool for _, tool in scored[:top_k]]


def get_tools(query: str = "", auto_select: bool = False):
    """返回工具列表。

    Args:
        query: 用户输入文本，auto_select=True 时用它筛选工具。
        auto_select: False=返回全部工具；True=先按 query 筛选相关工具。
    """
    all_tools = _discover_tools()
    if auto_select and query:
        return select_relevant_tools(query, all_tools)
    return all_tools
