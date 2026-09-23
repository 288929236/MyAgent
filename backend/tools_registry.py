"""工具自动发现 + 智能筛选入口。

1. _discover_tools()：自动扫描 tools/ 下所有 .py，收集全部 @tool 工具。
2. select_relevant_tools()：根据用户文本从所有工具中挑出相关的。
3. get_tools()：auto_select=False 时返回全部工具；True 时先筛选再返回。
"""

import importlib
from difflib import SequenceMatcher
from pathlib import Path

from langchain_core.tools import BaseTool


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
