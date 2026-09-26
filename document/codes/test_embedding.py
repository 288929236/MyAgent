"""测试 BGE Embedding 模型"""

from sentence_transformers import SentenceTransformer
import numpy as np

# 加载模型（本地相对路径）
model = SentenceTransformer('../../models/bge-base-zh')

# 预设的文本库
texts = [
    "员工请假流程是什么？",
    "怎么申请年假？",
    "财务报销需要什么材料？",
    "银行流水怎么查？",
    "员工信息在哪里查？",
]

print("=" * 50)
print("Embedding 相似度测试（输入 q 退出）")
print("=" * 50)
print(f"文本库共 {len(texts)} 条")
print()

# 预计算文本库向量
doc_embs = model.encode(texts)

while True:
    user_query = input("\n请输入要查询的文本：").strip()
    
    if user_query.lower() == 'q':
        print("退出测试")
        break
    
    if not user_query:
        continue
    
    # 转向量
    query_emb = model.encode([user_query])[0]
    
    # 计算相似度
    scores = []
    for i, text in enumerate(texts):
        sim = np.dot(query_emb, doc_embs[i]) / (
            np.linalg.norm(query_emb) * np.linalg.norm(doc_embs[i])
        )
        scores.append((sim, text))
    
    # 按相似度排序
    scores.sort(reverse=True)
    
    print("\n最相关的结果：")
    for rank, (sim, text) in enumerate(scores, 1):
        print(f"  {rank}. [{sim:.4f}] {text}")
