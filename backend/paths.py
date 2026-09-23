"""路径配置。

统一管理开发环境和打包环境的路径。
"""

import sys
import os
from pathlib import Path


def get_data_dir() -> Path:
    """获取数据目录。
    
    开发环境：项目根目录/data/
    打包环境：AppData/Roaming/MyAgent/data/
    """
    if getattr(sys, 'frozen', False):
        # 打包后，使用 Windows 标准位置
        app_data = os.environ.get('APPDATA', '')
        data_dir = Path(app_data) / "MyAgent" / "data"
    else:
        # 开发环境，使用项目根目录
        data_dir = Path(__file__).parent.parent / "data"
    
    # 自动创建目录
    data_dir.mkdir(parents=True, exist_ok=True)
    
    return data_dir


def get_env_file() -> Path:
    """获取 .env 文件路径。
    
    开发环境：backend/.env
    打包环境：AppData/Roaming/MyAgent/.env
    """
    if getattr(sys, 'frozen', False):
        app_data = os.environ.get('APPDATA', '')
        env_file = Path(app_data) / "MyAgent" / ".env"
    else:
        env_file = Path(__file__).parent / ".env"
    
    return env_file
