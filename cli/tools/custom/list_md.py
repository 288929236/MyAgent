"""列出 md 文件工具。"""

from langchain_core.tools import tool
from tools_registry import work_dir


@tool
def list_md_files() -> str:
    """列出当前工作目录下所有的 .md 文件。"""
    md_files = list(work_dir.glob("*.md"))
    if not md_files:
        return "当前目录下没有 md 文件。"
    return "当前目录下的 md 文件：\n" + "\n".join([f"- {f.name}" for f in md_files])
