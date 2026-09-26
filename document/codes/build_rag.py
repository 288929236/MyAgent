"""
RAG 文档处理脚本
功能：读取各库 raw/ 下的文档 → 切分文本块 → 向量化 → 存到 chunks/ 和 vectors/
"""

import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# .venv\Scripts\Activate.ps1
# cd document/codes
# python build_rag.py

# 目录路径
DOC_ROOT = Path(__file__).parent.parent
MODEL_PATH = DOC_ROOT.parent / "models" / "bge-base-zh"

# 四个知识库
DBS = ["policy", "ledger", "transaction", "employee"]

# 全局模型（只加载一次）
_model = None


def get_model():
    """懒加载 BGE 模型"""
    global _model
    if _model is None:
        print(f"加载 Embedding 模型：{MODEL_PATH}")
        _model = SentenceTransformer(str(MODEL_PATH))
    return _model


def load_md(file_path: Path) -> str:
    """读取 md 文件内容"""
    return file_path.read_text(encoding="utf-8")


def split_text(text: str, chunk_size: int = 500):
    """按 md 标题切分文本块

    遇到 # 开头的标题行就切分，每个标题下的内容作为一个块。
    如果一个块太大，再按段落拆。

    Args:
        text: 原始文本
        chunk_size: 最大块大小（字符），超过就再拆
    """
    lines = text.split("\n")
    chunks = []
    current_chunk_lines = []

    for line in lines:
        # 遇到 ## 或更多 # 开头的标题行，先把之前的内容存起来
        stripped = line.lstrip()
        is_heading = stripped.startswith("##")  # ## 或 ### 等
        if is_heading and current_chunk_lines:
            chunk_text = "\n".join(current_chunk_lines).strip()
            if chunk_text:
                chunks.append(chunk_text)
            current_chunk_lines = [line]  # 新块从标题开始
        else:
            current_chunk_lines.append(line)

    # 最后一块
    if current_chunk_lines:
        chunk_text = "\n".join(current_chunk_lines).strip()
        if chunk_text:
            chunks.append(chunk_text)

    # 如果块太大，再按段落拆
    result = []
    for chunk in chunks:
        if len(chunk) <= chunk_size:
            result.append(chunk)
        else:
            # 太大，按段落拆
            paragraphs = chunk.split("\n\n")
            current = ""
            for p in paragraphs:
                if len(current) + len(p) > chunk_size and current:
                    result.append(current.strip())
                    current = p
                else:
                    current += "\n\n" + p
            if current.strip():
                result.append(current.strip())

    return result


def embed_texts(texts: list[str]) -> np.ndarray:
    """文本向量化"""
    model = get_model()
    embeddings = model.encode(texts)
    return np.array(embeddings)


def process_db(db_name: str):
    """处理单个知识库"""
    raw_dir = DOC_ROOT / db_name / "raw"
    chunks_dir = DOC_ROOT / db_name / "chunks"
    vectors_dir = DOC_ROOT / db_name / "vectors"

    chunks_dir.mkdir(parents=True, exist_ok=True)
    vectors_dir.mkdir(parents=True, exist_ok=True)

    # 1. 读取文档
    md_files = list(raw_dir.glob("*.md"))
    if not md_files:
        print(f"[{db_name}] raw/ 下没有 md 文件，跳过")
        return

    print(f"\n[{db_name}] 发现 {len(md_files)} 个文档")

    # 2. 切分文本
    all_chunks = []
    chunk_id = 1

    for file_path in md_files:
        print(f"  处理：{file_path.name}")
        text = load_md(file_path)
        chunks = split_text(text)

        for chunk in chunks:
            all_chunks.append({
                "id": chunk_id,
                "text": chunk,
                "source": file_path.name,
            })
            chunk_id += 1

    print(f"  切分完成，共 {len(all_chunks)} 个文本块")

    # 3. 向量化
    print(f"  开始向量化...")
    texts = [c["text"] for c in all_chunks]
    vectors = embed_texts(texts)
    print(f"  向量化完成，向量维度：{vectors.shape}")

    # 4. 保存文本块
    chunks_file = chunks_dir / "chunks.jsonl"
    with open(chunks_file, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"  已保存文本块：{chunks_file}")

    # 5. 保存向量
    vectors_file = vectors_dir / "embeddings.bin"
    vectors.tofile(str(vectors_file))
    print(f"  已保存向量：{vectors_file}")

    # 6. 保存向量元数据
    meta = [{"chunk_id": c["id"], "source": c["source"]} for c in all_chunks]
    meta_file = vectors_dir / "embedding_meta.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"  已保存元数据：{meta_file}")


def main():
    print("=" * 50)
    print("RAG 文档处理")
    print("=" * 50)

    for db_name in DBS:
        process_db(db_name)

    print("\n" + "=" * 50)
    print("全部处理完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
