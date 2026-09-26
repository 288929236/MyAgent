"""Markdown 文件操作工具，内部按操作类型路由。"""

import shutil
from datetime import datetime
from pathlib import Path
from langchain_core.tools import tool

from tools_registry import work_dir, snapshot_dir, current_session_timestamp


def _check_safe(file_path: Path) -> str | None:
    """安全检查：只能操作 .md 文件，不能访问工作目录外。"""
    if not file_path.name.endswith(".md"):
        return "错误：只能操作 .md 文件。"
    if not file_path.resolve().is_relative_to(work_dir.resolve()):
        return "错误：不能访问工作目录外的文件。"
    return None


def _backup_file(file_path: Path) -> str:
    """修改/删除前自动备份到快照目录。"""
    if not file_path.exists():
        return ""
    tool_timestamp = datetime.now().strftime("%H%M%S")
    snapshot_name = f"{current_session_timestamp}_{tool_timestamp}_{file_path.name}"
    snapshot_path = snapshot_dir / snapshot_name
    shutil.copy2(file_path, snapshot_path)
    return f"已备份到快照：{snapshot_name}"


def _list_files() -> str:
    """列出当前目录下所有 md 文件。"""
    md_files = list(work_dir.glob("*.md"))
    if not md_files:
        return "当前目录下没有 md 文件。"
    result = "当前目录下的 md 文件：\n"
    for f in md_files:
        result += f"  - {f.name}\n"
    return result


def _read_file(filename: str) -> str:
    """读取指定 md 文件内容。"""
    file_path = work_dir / filename
    err = _check_safe(file_path)
    if err:
        return err
    if not file_path.exists():
        return f"错误：文件 {filename} 不存在。"
    try:
        text = file_path.read_text(encoding="utf-8")
        return f"文件 {filename} 的内容：\n\n{text}"
    except Exception as e:
        return f"读取文件失败：{e}"


def _create_file(filename: str, content: str) -> str:
    """新建 md 文件。"""
    file_path = work_dir / filename
    err = _check_safe(file_path)
    if err:
        return err
    if file_path.exists():
        return f"错误：文件 {filename} 已存在。"
    try:
        file_path.write_text(content, encoding="utf-8")
        return f"已创建文件：{filename}"
    except Exception as e:
        return f"创建文件失败：{e}"


def _edit_file(filename: str, content: str) -> str:
    """修改 md 文件内容，修改前自动备份。"""
    file_path = work_dir / filename
    err = _check_safe(file_path)
    if err:
        return err
    if not file_path.exists():
        return f"错误：文件 {filename} 不存在。"
    backup_msg = _backup_file(file_path)
    try:
        file_path.write_text(content, encoding="utf-8")
        return f"已修改文件：{filename}\n{backup_msg}"
    except Exception as e:
        return f"修改文件失败：{e}"


def _delete_file(filename: str) -> str:
    """删除 md 文件，删除前自动备份。"""
    file_path = work_dir / filename
    err = _check_safe(file_path)
    if err:
        return err
    if not file_path.exists():
        return f"错误：文件 {filename} 不存在。"
    backup_msg = _backup_file(file_path)
    try:
        file_path.unlink()
        return f"已删除文件：{filename}\n{backup_msg}"
    except Exception as e:
        return f"删除文件失败：{e}"


@tool
def md_operation(operation: str, filename: str = "", content: str = "") -> str:
    """对 Markdown 文件进行操作，包括列出、读取、新建、修改、删除。

    Args:
        operation: 操作类型，可选值：
            - list: 列出当前目录下所有 md 文件
            - read: 读取指定 md 文件内容
            - create: 新建 md 文件
            - edit: 修改 md 文件内容
            - delete: 删除 md 文件
        filename: 文件名（list 操作时不需要）
        content: 文件内容（create 和 edit 操作时需要）
    """
    operations = {
        "list": lambda: _list_files(),
        "read": lambda: _read_file(filename),
        "create": lambda: _create_file(filename, content),
        "edit": lambda: _edit_file(filename, content),
        "delete": lambda: _delete_file(filename),
    }

    if operation not in operations:
        return f"错误：未知操作 '{operation}'，可选：list、read、create、edit、delete"

    return operations[operation]()
