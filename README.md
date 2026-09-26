# MyAgent

基于 DeepSeek + LangGraph 的 AI Agent 桌面应用，支持 Web 界面和 CLI 两种模式，集成 RAG 向量检索知识库。

---

## ✨ 功能特性

- 🤖 **AI 对话**：接入 DeepSeek 大模型，支持多轮对话
- 🔧 **工具调用**：自动识别并调用自定义工具（文件操作、知识库检索等）
- 💾 **记忆持久化**：对话历史存到 SQLite，下次打开继续聊
- 📁 **文件夹操作**：Agent 接管指定文件夹，对 md 文档进行增删改查
- 📸 **快照备份**：修改文件前自动保存快照，改坏了可以回滚
- 📚 **RAG 知识库**：向量检索公司制度、账本、流水、人员信息
- 🧠 **BGE 向量模型**：本地 Embedding，语义相似度搜索
- 🎨 **AI 生图**：调用通义万相文生图，根据文字描述生成图片
- 🖥️ **桌面应用**：Electron 打包成 Windows exe，双击就能用

---

## 📸 效果展示

### 桌面端登录
![桌面端登录](images/桌面端登录.jpg)

### 桌面端 Chat 模式
![桌面端 Chat 模式](images/桌面端CHat模式.jpg)

### CLI 终端 Work 模式
![CLI 终端 Work 模式](images/CLI终端Work模式.jpg)

---

## 🛠️ 技术栈

### 前端
- **Electron** - 桌面应用框架
- **React + TypeScript** - UI 开发
- **Vite** - 构建工具
- **ReactMarkdown** - Markdown 渲染

### 后端
- **Python + FastAPI** - Web API
- **LangChain + LangGraph** - Agent 框架
- **DeepSeek** - 大语言模型
- **通义万相 qwen-image-3.0-pro** - 文生图模型
- **SQLite** - 对话状态存储

### RAG 向量检索
- **BGE-base-zh** - 中文 Embedding 模型
- **sentence-transformers** - 向量计算
- **余弦相似度** - 语义检索

### CLI
- **Rich** - 终端美化输出

---

## 📂 目录结构

```
MyAgent/
├── .venv/                 # Python 虚拟环境
├── models/                # BGE 向量模型（git忽略）
│
├── backend/              # 后端服务（FastAPI + Agent）
│   ├── api.py            # Web 接口
│   ├── agent.py          # Agent 核心逻辑
│   ├── agent_config.py   # Agent 配置
│   ├── tools_registry.py # 工具自动发现
│   ├── tools/            # 工具集
│   ├── .env              # 后端 API Key 配置
│   └── requirements.txt  # Python 依赖
│
├── cli/                  # CLI 命令行工具（独立运行）
│   ├── main1.py          # 基础对话测试
│   ├── main2.py          # 文件夹操作 Agent + RAG 检索
│   ├── agent.py          # Agent 核心
│   ├── client_config.py   # 客户配置
│   ├── tools_registry.py # 工具自动发现
│   ├── tools/            # 工具集
│   │   └── custom/       # 自定义工具
│   │       ├── md_operation.py      # md 文件操作
│   │       ├── search_knowledge.py # 知识库检索
│   │       └── generate_image.py  # AI 生图（通义万相）
│   ├── .env              # CLI API Key 配置
│   └── requirements.txt  # Python 依赖
│
├── document/             # RAG 向量数据库
│   ├── README.md         # 说明文档
│   ├── codes/            # 处理脚本
│   │   ├── build_rag.py  # 文档切分+向量化
│   │   └── test_embedding.py # 向量测试
│   ├── policy/           # 制度库（请假、报销等）
│   ├── ledger/           # 账本库（财务收支）
│   ├── transaction/      # 流水库（银行交易）
│   └── employee/         # 人员库（员工信息）
│
├── frontend/             # 前端（Electron + React）
│   ├── node_modules/     # npm 依赖包
│   ├── src/              # 源代码
│   ├── package.json     # 前端依赖配置
│   └── electron-builder.yml  # 打包配置
│
├── data/                 # 数据存储（db 文件）
├── docs/                 # 项目文档
├── images/               # 项目图片
└── .gitignore            # Git 忽略规则
```

---

## 📝 API Key 配置

分别在 `cli/` 和 `backend/` 目录下创建 `.env` 文件：

### cli/.env（CLI 模式用）
```env
# DeepSeek 大模型 API Key（必须）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx

# 通义万相生图 API Key（可选，需要生图功能时配置）
# 阿里云百炼平台申请：https://bailian.console.aliyun.com/
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### backend/.env（桌面端后端用）
```env
# DeepSeek 大模型 API Key（必须）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\Activate.ps1
# Mac/Linux:
source .venv/bin/activate
```

### 2. 安装依赖

```bash
# 后端依赖
pip install -r backend/requirements.txt

# CLI 依赖
pip install -r cli/requirements.txt
```

### 3. 下载 BGE 向量模型

```bash
# ModelScope 下载（国内推荐）
pip install modelscope
python -c "from modelscope import snapshot_download; snapshot_download('BAAI/bge-base-zh-v1.5', cache_dir='./models')"
```

### 4. 处理知识库文档

```bash
# 把文档放到 document/policy/raw/ 等目录
# 运行切分+向量化
cd document/codes
python build_rag.py
```

### 5. 启动 CLI 模式

```bash
python cli/main2.py
```

### 6. 启动后端服务

```bash
cd backend
python api.py
```

### 7. 启动前端

```bash
cd frontend
npm install
npm run dev
```

---

## 📦 打包发布

### 打包后端
```bash
pyinstaller --onefile --name MyAgentServer backend/api.py
```

### 打包前端
```bash
cd frontend
npm run build:win
```

---

## 📝 开发说明

- **后端和 CLI 独立**：各自有独立的 Agent 逻辑，互不影响
- **工具自动发现**：放在 `tools/custom/` 下的 `@tool` 函数会自动被加载
- **RAG 架构**：文档按 md 标题切分 → BGE 向量化 → 余弦相似度检索 → top3 返回
- **多知识库**：制度、账本、流水、人员四个库，通过 `search_knowledge(category, query)` 路由
- **数据存储**：对话历史在 `data/`，快照在 `.snapshots/`，向量在 `document/`
