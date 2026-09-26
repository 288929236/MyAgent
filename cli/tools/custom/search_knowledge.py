"""搜索知识库工具，内部按类别路由到不同的数据库。"""

import json
import numpy as np
from pathlib import Path
from langchain_core.tools import tool
from sentence_transformers import SentenceTransformer


# 知识库根目录
DOC_ROOT = Path(__file__).parent.parent.parent.parent / "document"
MODEL_PATH = Path(__file__).parent.parent.parent.parent / "models" / "bge-base-zh"

# 类别映射
CATEGORY_MAP = {
    "制度": "policy",
    "账本": "ledger",
    "流水": "transaction",
    "人员": "employee",
}

# 全局模型（只加载一次）
_model = None


def get_model():
    """懒加载 BGE 模型"""
    global _model
    if _model is None:
        _model = SentenceTransformer(str(MODEL_PATH))
    return _model


def load_db(db_name: str):
    """加载知识库的文本块和向量"""
    db_path = DOC_ROOT / db_name
    chunks_file = db_path / "chunks" / "chunks.jsonl"
    vectors_file = db_path / "vectors" / "embeddings.bin"

    if not chunks_file.exists() or chunks_file.stat().st_size == 0:
        return None, None

    # 加载文本块
    chunks = []
    with open(chunks_file, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))

    # 加载向量
    vectors = np.fromfile(str(vectors_file), dtype=np.float32)
    vectors = vectors.reshape(len(chunks), -1)

    return chunks, vectors


@tool
def search_knowledge(category: str, query: str) -> str:
    """搜索公司知识库，根据类别从对应的数据库中查询相关内容。

    Args:
        category: 知识类别，可选值：制度、账本、流水、人员
            - 制度：请假、报销、考勤等公司规章制度
            - 账本：财务账目、收支、预算等数据
            - 流水：银行流水、交易记录、转账明细
            - 人员：员工信息、部门、人员调度记录
        query: 要查询的问题或关键词
    """
    # 检查类别是否有效
    if category not in CATEGORY_MAP:
        return f"错误：未知类别 '{category}'，可选：制度、账本、流水、人员"

    db_name = CATEGORY_MAP[category]

    # 加载知识库
    chunks, vectors = load_db(db_name)
    if chunks is None:
        return f"{category}知识库暂无数据，请先在 document/{db_name}/raw/ 中放入文档并运行处理脚本。"

    # 查询转向量
    model = get_model()
    query_emb = model.encode([query])[0]

    # 计算余弦相似度
    query_norm = np.linalg.norm(query_emb)
    doc_norms = np.linalg.norm(vectors, axis=1)
    similarities = np.dot(vectors, query_emb) / (doc_norms * query_norm + 1e-10)

    # 取 top 3
    top_indices = np.argsort(similarities)[::-1][:3]

    # 拼接结果
    results = []
    for idx in top_indices:
        chunk = chunks[idx]
        sim = similarities[idx]
        results.append(f"📄 来源文档：《{chunk['source']}》（相似度: {sim:.4f}）\n{chunk['text']}\n")

    return f"【{category}知识库检索结果】\n\n" + "\n---\n".join(results) + "\n\n⚠️ 回答时请注明信息来源文档。"
