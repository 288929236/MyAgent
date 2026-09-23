"""简易完整流程演示：模型调通 → 工具调用 → 多轮记忆。

运行前请确认：
  1. 已在项目根目录激活 .venv
  2. backend/.env 里填好了 DEEPSEEK_API_KEY
  3. 已安装依赖：pip install langgraph langchain-deepseek python-dotenv
"""

from agent import build_agent
from agent_config import LOG_TOKEN_PER_TURN
from client_config import CLIENT_ID, THREAD_ID, MODE
from loader.memory_loader import load_user_memory
from loader.db_loader import load_conversation_from_db, import_to_memory
from pathlib import Path

# .venv\Scripts\Activate.ps1
# python backend/main.py

def print_token_stats(stats):
    """根据 config 打印每轮 token 统计。"""
    if not LOG_TOKEN_PER_TURN:
        return
    last = stats.get("turns", [])[-1] if stats.get("turns") else {}
    print(
        f"  [Token] 本轮输入={last.get('prompt', 0)}, "
        f"本轮输出={last.get('completion', 0)}, "
        f"累计总={stats.get('total_tokens', 0)}"
    )


def call_agent(agent, message, config):
    """根据模式调用 agent：chat 用 invoke，work 用 stream。"""
    if MODE == "work":
        print(f"[work 流式模式] 调用 agent...")
        for chunk in agent.stream(
            {"messages": [("user", message)]},
            config=config,
            stream_mode="values",
        ):
            chunk["messages"][-1].pretty_print()
    else:
        print(f"[chat 正常模式] 调用 agent...")
        result = agent.invoke(
            {"messages": [("user", message)]},
            config=config,
        )
        print(result["messages"][-1].content)


def main():
    # 从 SQLite 数据库加载对话记录并导入到记忆系统
    db_path = Path(__file__).parent.parent / "data" / CLIENT_ID / f"{THREAD_ID}.db"
    
    agent, model, stats = build_agent(str(db_path))
    config = {"configurable": {"thread_id": THREAD_ID}}
    try:
        # 从数据库加载对话记录
        conversations = load_conversation_from_db(str(db_path))
        # 将对话记录导入到记忆系统
        memory_data = import_to_memory(conversations)
        
        print(f"[记忆] 已从数据库加载 {len(conversations)} 条对话记录")
        print(f"[记忆] 记忆系统已导入: {memory_data['memory']['summary']}")
    except Exception as e:
        # 如果数据库不存在或没有对话记录，跳过
        print(f"[记忆] 数据库加载失败: {e}")
    
    print(f"[当前模式] {MODE}")
    print("=" * 50)

    # 交互式对话循环
    while True:
        try:
            # 获取用户输入
            user_input = input("你: ").strip()
            
            # 退出条件
            if user_input.lower() in ["退出", "exit", "quit", "再见"]:
                print("再见！")
                break
            
            # 如果用户输入为空，继续循环
            if not user_input:
                continue
            
            # 调用 agent 处理用户输入
            call_agent(agent, user_input, config)
            print_token_stats(stats)
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            break


if __name__ == "__main__":
    main()
