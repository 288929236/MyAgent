# Agent 开发指南（从零到跑通）

> 本文以 **DeepSeek + LangGraph** 为例，把"调模型 → 写工具 → 建图 → 跑起来 → 加记忆 → 测试"串成一条完整可照着敲的路径。
> 适用：已建好隔离虚拟环境，装好了 `langgraph` 和模型客户端。

---

## 0. 环境准备

```powershell
# 建项目 + 虚拟环境（如已做可跳过）
mkdir C:\Users\bywdy\Desktop\MyAgent
cd C:\Users\bywdy\Desktop\MyAgent
python -m venv .venv
.venv\Scripts\Activate.ps1

# 安装依赖
pip install langgraph langchain-deepseek
```

`.env` 里放 key（建议用 `python-dotenv`）：
```
DEEPSEEK_API_KEY=你的key
```

---

## 1. 第一步：先单独把模型调通

在写任何图之前，先确认模型能调：

```python
from langchain_deepseek import ChatDeepSeek

model = ChatDeepSeek(model="deepseek-chat", api_key="你的key")

resp = model.invoke("用一句话介绍你自己")
print(resp.content)
```

跑通这步，说明 key、网络、模型都没问题。**这一步不涉及 agent，只是确认大脑在线。**

---

## 2. 第二步：写工具（手脚）

工具就是一个加了 `@tool` 装饰器的普通函数，docstring 是给模型看的说明书：

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """查询某个城市的实时天气。

    Args:
        city: 城市名，例如"北京"
    """
    # 这里换成你真实的业务逻辑 / API
    return f"{city}今天晴，25℃"
```

要点：
- 函数名 = 工具名；
- docstring 第一段 = 用途说明；
- `Args:` 部分 = 参数说明；
- 函数体 = 真正干活的地方（调 API、查数据库、读文件都行）。

---

## 3. 第三步：用预建组件快速跑通（推荐入门）

不想一开始就画复杂图，直接用 `create_react_agent`——它内部已经把"模型 ↔ 工具"循环写好了：

```python
from langchain_deepseek import ChatDeepSeek
from langgraph.prebuilt import create_react_agent

model = ChatDeepSeek(model="deepseek-chat", api_key="你的key")
tools = [get_weather]

agent = create_react_agent(model, tools)

# 跑
for chunk in agent.stream(
    {"messages": [("user", "北京天气怎么样？")]},
    stream_mode="values",
):
    chunk["messages"][-1].pretty_print()
```

它内部做的事，就是你第 0 步手写的那个 while 循环：
> 模型要调工具 → 执行工具 → 结果喂回模型 → 直到模型给出最终回答。

---

## 4. 第四步：自己画一张图（理解底层）

要完全掌控流程，就用 `StateGraph` 自己搭。一个最小结构：

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# ① 定义状态：节点之间传什么数据
class State(TypedDict):
    messages: list   # 对话消息列表

# ② 定义节点函数：接收 state，返回 state 的更新
def call_model(state: State):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

def call_tool(state: State):
    # 这里用 ToolNode 自动执行模型要求的工具
    return {"messages": [tool_node.invoke(state)]}

# ③ 建图：加节点、加边
builder = StateGraph(State)
builder.add_node("model", call_model)
builder.add_node("tools", call_tool)

builder.add_edge(START, "model")      # 从入口先走模型
builder.add_edge("model", "tools")     # 模型之后走工具
builder.add_edge("tools", END)         # 工具之后结束

# ④ 编译成能跑的图
graph = builder.compile()
```

> 实际项目里"模型 ↔ 工具"之间会有一条判断边：模型说要调工具就去 `tools`，否则就 `END`。入门先用 `create_react_agent`，需要精细控制再画这种图。

---

## 5. 第五步：加记忆（多轮对话）

编译时挂一个 checkpointer，同一个 `thread_id` 就能跨调用记住对话：

```python
from langgraph.checkpoint.memory import MemorySaver   # 本地开发用
# 生产可换：from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = MemorySaver()
agent = create_react_agent(model, tools, checkpointer=checkpointer)

config = {"configurable": {"thread_id": "用户001"}}

# 第一轮
agent.invoke({"messages": [("user", "我叫小明")]}, config)
# 第二轮——它还记得你叫小明
agent.invoke({"messages": [("user", "我叫什么？")]}, config)
```

- 改本地持久化：`SqliteSaver.from_conn_string("chat.db")`；
- 改生产多用户：`PostgresSaver`。

---

## 6. 第六步：加人在回路（interrupt）

关键操作前暂停等人确认：

```python
from langgraph.types import interrupt, Command

# 在某个节点里：
def approve():
    user_decision = interrupt({"question": "确认执行吗？"})
    # 等人给了答复后继续
    return {"approved": user_decision == "yes"}
```

运行时它会停在中断点，你用 `Command(resume="yes")` 让它继续。

---

## 7. 第七步：测试你的 agent

测试的核心原则：**别在单测里真调大模型**（慢、贵、结果不稳定）。用"假模型"按剧本返回，真跑图、断言状态。

```python
from unittest.mock import Mock
from langchain_core.messages import AIMessage

def test_agent_calls_tool():
    # ① 造一个假模型：第一次要求调工具，第二次直接回答
    fake_model = Mock()
    fake_model.invoke.side_effect = [
        AIMessage(content="", tool_calls=[
            {"name": "get_weather", "args": {"city": "北京"}, "id": "1"}
        ]),
        AIMessage(content="北京今天晴，25℃。"),
    ]

    # ② 用假模型 + 真工具组装 agent
    agent = create_react_agent(fake_model, [get_weather])

    # ③ 跑
    result = agent.invoke({"messages": [("user", "北京天气？")]})

    # ④ 断言：工具被调了、结果进了消息
    assert len(result["messages"]) == 3
    assert result["messages"][-1].content == "北京今天晴，25℃。"
```

测试分层建议：
1. **工具层**：把工具当普通函数 `assert`，mock 外部 API；
2. **图层**：用假模型验证流程和状态；
3. **端到端**：接真模型跑几条标准用例，攒成回归集。

---

## 8. 完整文件结构参考

```
codes/
├── .env
├── main.py            # 入口：组装并跑 agent
├── agent.py           # 图/agent 组装
├── tools/
│   └── weather.py     # 你的工具
└── tests/
    └── test_agent.py
```

---

## 9. 常见坑

| 现象 | 原因 |
|---|---|
| 模型不调工具 | docstring 写得不清楚，模型不知道何时用 |
| 工具参数错 | `Args:` 说明缺失，模型瞎猜参数 |
| 多轮对话失忆 | 没传 `thread_id` 或没挂 checkpointer |
| Windows 上装不上 uvloop | 只在开发框架时才会碰到，普通 `pip install langgraph` 不会 |
| 改了代码没生效 | 没激活虚拟环境 / 跑错了解释器 |

---

## 心法

1. **先调通模型，再写图**——大脑不通，别的都白搭；
2. **先用 `create_react_agent` 跑起来**，需要精细控制再自己画 `StateGraph`；
3. **测试用假模型**，别在单测里真花钱调 API；
4. **工具说明书（docstring）决定 agent 智商**，写清楚比写代码还重要。
