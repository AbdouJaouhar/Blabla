import argparse
import sqlite3
from pathlib import Path

import nltk
import numpy as np
import torch
import torch.nn.functional as F
from GrobidArticleExtractor.app import GrobidArticleExtractor
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer

# -----------------------------
# Load embedding model (BGE-M3)
# -----------------------------
print("Loading embedding model BAAI/bge-m3...")

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)

model = SentenceTransformer("BAAI/bge-m3", device=device)

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

# -----------------------------------
# SECTION FILTERING PARAMETERS
# -----------------------------------
ALLOWED_SECTIONS = [
    "abstract",
    "introduction",
    "background",
    "related work",
    "method",
    "methods",
    "experiment",
    "experiments",
    "results",
    "discussion",
    "conclusion",
    "conclusions",
    "analysis",
]


def normalize_header(h):
    return h.lower().strip() if h else ""


# -----------------------------------
# RESET DATABASE TABLE
# -----------------------------------
def reset_table(conn):
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS pdf_chunks")
    cur.execute("""
        CREATE TABLE pdf_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arxiv_id TEXT,
            chunk_index INTEGER,
            content TEXT
        )
    """)
    conn.commit()


# -----------------------------------
# SEMANTIC CHUNKING (CUDA-optimized)
# -----------------------------------
def semantic_chunk_text(text, max_tokens=200, similarity_threshold=0.55):
    """
    CUDA-based semantic chunking:
      - sentence splitting
      - GPU embeddings (batched)
      - cosine similarity on GPU
    """

    sentences = sent_tokenize(text)
    if not sentences:
        return []

    # GPU-accelerated embedding
    embeddings = model.encode(
        sentences,
        batch_size=8,
        convert_to_tensor=True,
        device=device,
        normalize_embeddings=False,
    )

    chunks = []
    current_chunk = []
    current_embs = []

    def approx_tokens(s):
        return len(s.split())

    for sent, emb in zip(sentences, embeddings):
        if not current_chunk:
            current_chunk.append(sent)
            current_embs.append(emb)
            continue

        # GPU cosine similarity
        sim = F.cosine_similarity(emb, current_embs[-1], dim=0).item()

        merged = " ".join(current_chunk + [sent])
        too_large = approx_tokens(merged) > max_tokens

        if sim < similarity_threshold or too_large:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sent]
            current_embs = [emb]
        else:
            current_chunk.append(sent)
            current_embs.append(emb)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# -----------------------------------
# EXTRACT RELEVANT CONTENT FROM GROBID
# -----------------------------------
def extract_relevant_content(article: dict):
    result = []

    # --- ABSTRACT ---
    meta = article.get("metadata", {}) or {}
    abstract = meta.get("abstract")
    if abstract:
        result.append(("abstract", abstract.strip()))

    # --- SECTIONS + SUBSECTIONS ---
    def collect(sec, acc):
        header = normalize_header(sec.get("heading"))
        paras = sec.get("content") or []
        text = "\n\n".join(p.strip() for p in paras if p and p.strip())

        if text and any(header.startswith(ok) for ok in ALLOWED_SECTIONS):
            acc.append((header or "section", text))

        for sub in sec.get("subsections", []) or []:
            collect(sub, acc)

    for sec in article.get("sections", []) or []:
        collect(sec, result)

    return result


def arxiv_id_from_filename(fname: str):
    return fname.replace(".pdf", "")


# -----------------------------------
# MAIN
# -----------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Parse PDFs with GROBID + CUDA semantic chunking."
    )
    parser.add_argument("pdf_dir")
    parser.add_argument("db_path")
    parser.add_argument("--chunk-size", type=int, default=350)
    parser.add_argument("--similarity", type=float, default=0.55)

    args = parser.parse_args()
    pdf_dir = Path(args.pdf_dir)
    pdf_files = list(pdf_dir.glob("*.pdf"))

    conn = sqlite3.connect(args.db_path)
    # reset_table(conn)
    cur = conn.cursor()

    extractor = GrobidArticleExtractor()

    print(f"Found {len(pdf_files)} PDFs")

    for index, pdf_path in enumerate(pdf_files):
        arxiv_id = arxiv_id_from_filename(pdf_path.name)
        print(f"\n[PROCESS {index + 1}/{len(pdf_files)}] {arxiv_id}")

        try:
            xml = extractor.process_pdf(str(pdf_path))
            article = extractor.extract_content(xml)
        except Exception as e:
            print(f"[ERROR] GROBID failed on {pdf_path}: {e}")
            continue

        sections = extract_relevant_content(article)
        print(f"  -> Relevant sections: {len(sections)}")

        if not sections:
            print(f"[WARN] No relevant sections for {arxiv_id}")
            continue

        chunk_index = 0

        for header, text in sections:
            chunks = semantic_chunk_text(
                text,
                max_tokens=args.chunk_size,
                similarity_threshold=args.similarity,
            )

            for chunk in chunks:
                cur.execute(
                    "INSERT INTO pdf_chunks (arxiv_id, chunk_index, content) VALUES (?, ?, ?)",
                    (arxiv_id, chunk_index, chunk),
                )
                chunk_index += 1

        conn.commit()
        print(f"[OK] {arxiv_id}: saved {chunk_index} semantic chunks")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
