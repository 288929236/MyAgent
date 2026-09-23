"""FastAPI 接口服务。

提供 /chat 接口，接收前端消息并返回 AI 回复。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pathlib import Path
import sqlite3
import json
import os

from agent import build_agent
from user_db import login
from paths import get_data_dir, get_env_file

# .venv\Scripts\Activate.ps1
# python backend/api.py

# 创建 FastAPI 应用
app = FastAPI(title="MyAgent API", version="1.0")

# 添加 CORS 中间件，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== 数据模型 =====

class LoginRequest(BaseModel):
    """登录请求模型。"""
    username: str
    password: str
    api_key: str = ""


class ChatRequest(BaseModel):
    """聊天请求模型。"""
    message: str
    client_id: str
    thread_id: str


# ===== 接口定义 =====

@app.post("/login")
async def login_api(request: LoginRequest):
    """登录接口：验证用户名密码，返回用户信息。"""
    # 如果提供了 API Key，保存到 .env 文件
    if request.api_key:
        env_file = get_env_file()
        env_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 读取现有配置
        env_dict = {}
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        key, value = line.split("=", 1)
                        env_dict[key.strip()] = value.strip()
        
        # 修改 API Key
        env_dict["DEEPSEEK_API_KEY"] = request.api_key
        
        # 写回文件
        with open(env_file, "w", encoding="utf-8") as f:
            for key, value in env_dict.items():
                f.write(f"{key}={value}\n")
        
        # 更新环境变量
        os.environ["DEEPSEEK_API_KEY"] = request.api_key
    
    user = login(request.username, request.password)
    if user:
        return {
            "success": True,
            "username": user["username"],
            "client_id": user["client_id"]
        }
    return {"success": False, "username": "", "client_id": ""}


@app.get("/conversations/{client_id}")
async def get_conversations(client_id: str):
    """获取指定用户的所有对话历史。"""
    user_dir = get_data_dir() / client_id
    
    conversations = []
    if user_dir.exists():
        for db_file in user_dir.glob("*.db"):
            thread_id = db_file.stem
            conversations.append({
                "thread_id": thread_id,
                "title": f"对话 {thread_id}",
                "created_at": "",
            })
    
    return {"conversations": conversations}


@app.delete("/conversations/{client_id}/{thread_id}")
async def delete_conversation(client_id: str, thread_id: str):
    """删除指定对话。"""
    db_path = get_data_dir() / client_id / f"{thread_id}.db"
    
    try:
        if db_path.exists():
            db_path.unlink()
            return {"success": True, "message": "对话已删除"}
        return {"success": False, "message": "对话不存在"}
    except Exception as e:
        return {"success": False, "message": f"删除失败: {str(e)}"}


@app.post("/conversations/{client_id}")
async def create_conversation(client_id: str):
    """创建新对话。"""
    user_dir = get_data_dir() / client_id
    
    user_dir.mkdir(parents=True, exist_ok=True)
    
    max_num = 0
    for db_file in user_dir.glob("*.db"):
        try:
            num = int(db_file.stem)
            if num > max_num:
                max_num = num
        except:
            pass
    
    new_thread_id = f"{max_num + 1:03d}"
    db_path = user_dir / f"{new_thread_id}.db"
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.close()
        return {"success": True, "thread_id": new_thread_id}
    except Exception as e:
        return {"success": False, "message": f"创建失败: {str(e)}"}


@app.get("/history/{client_id}/{thread_id}")
async def get_conversation_history(client_id: str, thread_id: str):
    """获取指定会话的历史消息。"""
    db_path = get_data_dir() / client_id / f"{thread_id}.db"
    
    if not db_path.exists():
        return {"messages": []}
    
    conn = None
    try:
        agent, model, stats, conn = build_agent(str(db_path))
        
        config = {"configurable": {"thread_id": thread_id}}
        state = agent.get_state(config)
        
        messages = []
        if state and state.values and "messages" in state.values:
            for msg in state.values["messages"]:
                msg_type = type(msg).__name__
                if msg_type == "HumanMessage":
                    role = "user"
                elif msg_type == "AIMessage":
                    role = "assistant"
                else:
                    continue
                
                messages.append({
                    "role": role,
                    "content": msg.content
                })
        
        return {"messages": messages}
    except Exception as e:
        return {"messages": []}
    finally:
        if conn:
            conn.close()


@app.post("/chat")
async def chat(request: ChatRequest):
    """聊天接口：流式返回 AI 回复。"""
    db_path = get_data_dir() / request.client_id / f"{request.thread_id}.db"
    
    agent, model, stats, conn = build_agent(str(db_path))
    
    def generate():
        try:
            config = {"configurable": {"thread_id": request.thread_id}}
            full_content = ""
            
            for chunk in agent.stream(
                {"messages": [("user", request.message)]},
                config=config,
                stream_mode="values",
            ):
                if "messages" in chunk and chunk["messages"]:
                    last_msg = chunk["messages"][-1]
                    if hasattr(last_msg, "content") and last_msg.content:
                        full_content = last_msg.content
                        yield f"data: {json.dumps({'content': full_content})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            conn.close()
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/")
async def root():
    """根路径。"""
    return {"message": "MyAgent API 服务运行中", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
