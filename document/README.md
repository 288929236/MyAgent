# document/ 向量数据库说明

## 目录结构

```
document/
├── policy/                # 制度库
│   ├── raw/               # 制度文档放这里（请假、报销、考勤等）
│   ├── chunks/            # 切分后的文本块
│   └── vectors/          # 向量数据
│
├── ledger/                # 账本库
│   ├── raw/               # 财务账本文档
│   ├── chunks/
│   └── vectors/
│
├── transaction/           # 流水库
│   ├── raw/               # 银行流水、交易记录
│   ├── chunks/
│   └── vectors/
│
├── employee/               # 人员库
│   ├── raw/               # 员工信息、调度记录
│   ├── chunks/
│   └── vectors/
│
├── codes/                  # 处理脚本
│   └── build_rag.py
│
└── README.md
```

---

## 每个库的内部结构

每个库内部都是一样的：

```
{db_name}/
├── raw/                    # 原始文档（PDF、Word、md）
│   └── *.pdf
├── chunks/
│   ├── chunks.jsonl       # 切分后的文本块（JSONL 格式）
│   └── index.json         # 文档索引
└── vectors/
    ├── embeddings.bin      # 向量二进制数据
    └── embedding_meta.json # 向量元数据
```

---

## 对应工具

| 库目录 | 对应 Agent 工具 |
|--------|----------------|
| policy/ | search_policy() |
| ledger/ | search_ledger() |
| transaction/ | search_transaction() |
| employee/ | search_employee() |

---

## 使用流程

### 1. 放入文档
把对应类型的文档放到对应库的 `raw/` 目录下

### 2. 运行处理脚本
```bash
python document/codes/build_rag.py
```
自动完成：读取文档 → 切分 → 向量化 → 存到对应库

### 3. Agent 自动检索
Agent 根据用户问题，自动选择对应的搜索工具查询

---

## 文件格式说明

### chunks.jsonl 每行格式
```json
{
  "id": 1,
  "text": "员工请假需要提前3天申请...",
  "source": "员工手册.pdf",
  "chapter": "3.1.1 事假申请",
  "page": 15
}
```

### embedding_meta.json 格式
```json
[
  {"chunk_id": 1, "source": "员工手册.pdf", "chapter": "3.1.1 事假申请"},
  {"chunk_id": 2, "source": "考勤制度.docx", "chapter": "2.3 病假"}
]
```

---

## 更新文档

1. 把新文档放到对应库的 `raw/`
2. 重新运行处理脚本
3. 自动增量更新（只处理新文件）
