"""新建 md 文件工具。"""

from datetime import datetime
from langchain_core.tools import tool
from tools_registry import work_dir, modify_log


@tool
def create_md(filename: str, content: str) -> str:
    """新建一个 md 文件并写入内容。
    
    Args:
        filename: 新文件名（例如 notes.md）
        content: 文件内容
    """
    if not filename.endswith(".md"):
        return "错误：只能创建 .md 文件。"
    
    file_path = work_dir / filename
    
    if not file_path.resolve().is_relative_to(work_dir.resolve()):
        return "错误：不能在工作目录外创建文件。"
    
    if file_path.exists():
        return f"错误：文件 {filename} 已存在。"
    
    try:
        file_path.write_text(content, encoding="utf-8")
        
        # 记录修改
        modify_log.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": "create",
            "file": filename
        })
        
        return f"成功创建文件 {filename}。"
    except Exception as e:
        return f"创建文件失败：{e}"
