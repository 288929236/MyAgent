"""读取 md 文件工具。"""

from langchain_core.tools import tool
from tools_registry import work_dir


@tool
def read_md(filename: str) -> str:
    """读取指定 md 文件的内容。
    
    Args:
        filename: 要读取的文件名（例如 README.md）
    """
    # 安全检查：只能操作 .md 文件
    if not filename.endswith(".md"):
        return "错误：只能操作 .md 文件。"
    
    file_path = work_dir / filename
    
    # 安全检查：不能访问上级目录
    if not file_path.resolve().is_relative_to(work_dir.resolve()):
        return "错误：不能访问工作目录外的文件。"
    
    if not file_path.exists():
        return f"错误：文件 {filename} 不存在。"
    
    try:
        content = file_path.read_text(encoding="utf-8")
        return f"文件 {filename} 的内容：\n\n{content}"
    except Exception as e:
        return f"读取文件失败：{e}"
