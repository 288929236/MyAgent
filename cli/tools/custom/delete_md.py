"""删除 md 文件工具。"""

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
def delete_md(filename: str) -> str:
    """删除指定的 md 文件。
    
    Args:
        filename: 要删除的文件名
    """
    if not filename.endswith(".md"):
        return "错误：只能删除 .md 文件。"
    
    file_path = work_dir / filename
    
    if not file_path.resolve().is_relative_to(work_dir.resolve()):
        return "错误：不能删除工作目录外的文件。"
    
    if not file_path.exists():
        return f"错误：文件 {filename} 不存在。"
    
    try:
        # 先保存快照
        save_snapshot(filename, file_path.read_text(encoding="utf-8"))
        
        # 删除文件
        file_path.unlink()
        
        # 记录修改
        modify_log.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": "delete",
            "file": filename
        })
        
        return f"成功删除文件 {filename}。"
    except Exception as e:
        return f"删除文件失败：{e}"
