"""修改 md 文件工具。"""

from datetime import datetime
from langchain_core.tools import tool
from tools_registry import work_dir, snapshot_dir, modify_log, current_session_timestamp


def save_snapshot(filename: str, content: str):
    """保存文件快照：格式 = 对话时间戳_工具时间戳_文件名"""
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    tool_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 文件名：对话时间戳_工具时间戳_文件名
    snapshot_name = f"{current_session_timestamp}_{tool_timestamp}_{filename}"
    snapshot_path = snapshot_dir / snapshot_name
    
    try:
        snapshot_path.write_text(content, encoding="utf-8")
    except Exception as e:
        print(f"保存快照失败：{e}")


@tool
def edit_md(filename: str, old_text: str, new_text: str) -> str:
    """修改 md 文件中的内容（替换指定文本）。
    
    Args:
        filename: 要修改的文件名
        old_text: 要被替换的原文
        new_text: 新的内容
    """
    if not filename.endswith(".md"):
        return "错误：只能修改 .md 文件。"
    
    file_path = work_dir / filename
    
    if not file_path.resolve().is_relative_to(work_dir.resolve()):
        return "错误：不能修改工作目录外的文件。"
    
    if not file_path.exists():
        return f"错误：文件 {filename} 不存在。"
    
    try:
        # 先保存快照
        save_snapshot(filename, file_path.read_text(encoding="utf-8"))
        
        # 读取并修改
        content = file_path.read_text(encoding="utf-8")
        if old_text not in content:
            return f"错误：在文件中找不到要替换的内容。"
        
        new_content = content.replace(old_text, new_text)
        file_path.write_text(new_content, encoding="utf-8")
        
        # 记录修改
        modify_log.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": "edit",
            "file": filename
        })
        
        return f"成功修改文件 {filename}。"
    except Exception as e:
        return f"修改文件失败：{e}"
