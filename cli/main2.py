"""文件夹操作 Agent - 导入文件夹，对 md 文档进行增删改查。"""

import os
import sqlite3
from pathlib import Path
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from paths import get_env_file, get_data_dir
from client_config import CLIENT_ID, THREAD_ID
from tools_registry import init_workspace, modify_log, get_tools, start_new_session

# 加载环境变量
load_dotenv(get_env_file())

console = Console()

# .venv\Scripts\Activate.ps1
# python cli/main2.py


def setup_workspace():
    """初始化工作目录。"""
    print("=" * 50)
    print("📁 文件夹操作 Agent")
    print("=" * 50)
    
    work_dir = Path.cwd()
    
    while True:
        path_input = input("请输入要接管的文件夹路径（直接回车使用当前目录）: ").strip()
        
        if not path_input:
            work_dir = Path.cwd()
            break
        
        path = Path(path_input)
        if path.exists() and path.is_dir():
            work_dir = path.resolve()
            break
        else:
            print("路径不存在或不是文件夹，请重新输入。")
    
    # 初始化工具的工作目录
    init_workspace(work_dir)
    
    print(f"\n✅ 已接管目录：{work_dir}")
    
    # 列出目录下的 md 文件
    md_files = list(work_dir.glob("*.md"))
    if md_files:
        print(f"\n📄 当前目录下的 md 文件：")
        for f in md_files:
            print(f"  - {f.name}")
    else:
        print("\n📄 当前目录下还没有 md 文件。")
    
    print("\n" + "=" * 50)
    print("你现在可以让我：")
    print("  - 查看有哪些 md 文件")
    print("  - 读取某个 md 文件的内容")
    print("  - 新建一个 md 文件")
    print("  - 修改某个 md 文件的内容")
    print("  - 删除某个 md 文件")
    print("=" * 50)


def main():
    # 初始化工作目录
    setup_workspace()
    
    # 创建 db 数据库连接
    data_dir = get_data_dir()
    db_dir = data_dir / CLIENT_ID
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / f"{THREAD_ID}.db"
    
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    
    # 创建模型
    model = ChatDeepSeek(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        temperature=0.7,
    )
    
    # 自动发现所有工具
    tools = get_tools()
    
    # 创建 Agent（带 db 持久化）
    agent = create_agent(model, tools, checkpointer=checkpointer)
    
    config = {"configurable": {"thread_id": THREAD_ID}}
    
    # 加载历史记忆并统计
    try:
        tuple_data = checkpointer.get_tuple(config)
        if tuple_data and tuple_data.checkpoint and "channel_values" in tuple_data.checkpoint:
            channel_values = tuple_data.checkpoint["channel_values"]
            if "messages" in channel_values:
                messages = channel_values["messages"]
                # 统计用户消息轮数（HumanMessage 数量）
                user_turns = sum(1 for m in messages if m.type == "human")
                # 统计工具调用次数（ToolMessage 数量）
                tool_calls = sum(1 for m in messages if m.type == "tool")
                print(f"\n[记忆] 已加载历史对话：{user_turns} 轮对话，调用过 {tool_calls} 次工具")
            else:
                print("\n[记忆] 没有历史对话，开始新的会话")
        else:
            print("\n[记忆] 没有历史对话，开始新的会话")
    except Exception as e:
        print(f"\n[记忆] 加载历史对话失败: {e}")
        # 调试用：打印错误类型
        # import traceback
        # traceback.print_exc()
    
    print("=" * 50)
    
    # 对话循环
    while True:
        try:
            user_input = input("\n你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["退出", "exit", "quit", "再见"]:
                # 打印修改记录
                if modify_log:
                    print("\n" + "=" * 50)
                    print("📝 本次修改记录：")
                    for log in modify_log:
                        print(f"  [{log['time']}] {log['action']} {log['file']}")
                    print("=" * 50)
                
                print("再见！")
                break
            
            # 开始新的一轮对话，生成会话时间戳
            start_new_session()
            
            # 调用 Agent
            result = agent.invoke(
                {"messages": [("user", user_input)]},
                config=config,
            )

            # 检查是否调用了搜索知识库工具，如果有就打印来源
            last_messages = result['messages']
            for msg in last_messages:
                if msg.type == "tool" and "search_knowledge" in str(msg.name):
                    # 从工具返回结果里提取来源文档
                    content = msg.content
                    # 打印检索来源
                    console.print("\n[dim]📚 知识库检索来源：[/dim]")
                    for line in content.split("\n"):
                        if "来源文档" in line:
                            console.print(f"[dim]  {line.strip()}[/dim]")
                    console.print()

            # 打印最后一条消息（渲染 Markdown）
            print()
            console.print(Markdown(result['messages'][-1].content))
            
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            break
    
    conn.close()


if __name__ == "__main__":
    main()
