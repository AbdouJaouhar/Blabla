import argparse
import json
import os
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

load_dotenv()
# -----------------------------
# OpenAI / ChatGPT config
# -----------------------------
# FAST + CHEAP MODELS:
#   gpt-4.1-mini
#   gpt-4o-mini
#   gpt-4.1
OPENAI_MODEL = "gpt-4.1-mini"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -----------------------------
# BAD PATTERNS (chunk filters)
# -----------------------------
BAD_CHUNK_PATTERNS = [
    "in this paper",
    "in this work",
    "we propose",
    "we present",
    "our contributions",
    "the rest of this paper",
    "this study",
    "related work",
    "this paper aims",
    "the experiment shows",
    "researchers have been",
    "study demonstrates",
]


def is_bad_chunk(chunk: str) -> bool:
    lo = chunk.lower()
    return any(p in lo for p in BAD_CHUNK_PATTERNS)


# -----------------------------
# BAD QUESTION PATTERNS
# -----------------------------
BAD_Q_PATTERNS = [
    "how does the proposed",
    "how does this study",
    "what do the authors",
    "what does this paper",
    "what did the experiment",
    "what is the contribution",
    "how do the results",
]


def is_bad_question(q: str) -> bool:
    lo = q.lower()
    return any(p in lo for p in BAD_Q_PATTERNS)


# -----------------------------
# DB helpers
# -----------------------------
def load_chunks(conn) -> Dict[str, List[Dict[str, Any]]]:
    cur = conn.cursor()
    cur.execute("""
        SELECT arxiv_id, chunk_index, content
        FROM pdf_chunks
        ORDER BY arxiv_id, chunk_index
    """)
    rows = cur.fetchall()

    grouped = defaultdict(list)
    for arxiv_id, chunk_index, content in rows:
        grouped[arxiv_id].append({"chunk_index": chunk_index, "content": content})
    return grouped


# -----------------------------
# Build context windows
# -----------------------------
def make_context_windows(chunks, max_chunks_per_context=3):
    contexts = []
    current = []
    for c in chunks:
        ch = c["content"]

        # pre-filter chunks
        if is_bad_chunk(ch):
            continue

        current.append(ch)

        if len(current) >= max_chunks_per_context:
            contexts.append(current)
            current = []

    if current:
        contexts.append(current)

    return contexts


# -----------------------------
# OpenAI call: generate Q/A
# -----------------------------
def generate_qa(context_chunks: List[str]) -> Dict[str, str]:
    """
    Generate Q/A using a FAST OpenAI model.
    Includes strong scientific constraints.
    """

    context_text = "\n\n".join(context_chunks)

    system_prompt = (
        "You generate ONLY scientific and technical questions.\n"
        "STRICT RULES:\n"
        " - The question must require real technical/scientific reasoning.\n"
        " - NO questions about the paper, authors, contributions, or experiments.\n"
        " - NO meta-academic content.\n"
        " - If the context is not suitable for scientific Q/A, return:\n"
        '   {"question": "SKIP", "answer": "SKIP"}\n'
        " - Answer must use ONLY the provided context.\n"
    )

    user_prompt = (
        "Context:\n"
        "---------------------\n"
        f"{context_text}\n"
        "---------------------\n\n"
        "Generate a JSON object:\n"
        "{\n"
        '  "question": "a technical, scientific question answerable from the context only",\n'
        '  "answer": "the correct answer"\n'
        "}\n"
    )

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=300,
        )
        content = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] OpenAI call failed: {e}")
        return {}

    # Try to parse JSON
    try:
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:]

        data = json.loads(content)
    except Exception:
        print(f"[WARN] Bad JSON: {content[:200]}...")
        return {}

    q = data.get("question", "").strip()
    a = data.get("answer", "").strip()

    # Filtering
    if q.upper() == "SKIP" or a.upper() == "SKIP":
        return {}

    if not q or not a:
        return {}

    if is_bad_question(q):
        return {}

    # skip useless questions
    if len(q) < 10 or len(a) < 10:
        return {}

    return {"question": q, "answer": a}


# -----------------------------
# Main dataset builder
# -----------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Build Dataset C (question, contexts, answer) using fast OpenAI model with filtering."
    )
    parser.add_argument("db_path")
    parser.add_argument("--output", "-o", default="rag_dataset_c_clean.jsonl")
    parser.add_argument("--max-contexts-per-paper", type=int, default=5)
    parser.add_argument("--max-chunks-per-context", type=int, default=3)
    parser.add_argument("--max-papers", type=int, default=0)

    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing")

    conn = sqlite3.connect(args.db_path)
    groups = load_chunks(conn)
    conn.close()

    arxiv_ids = list(groups.keys())
    if args.max_papers > 0:
        arxiv_ids = arxiv_ids[: args.max_papers]

    out = Path(args.output)
    count = 0

    with out.open("w", encoding="utf-8") as f:
        for aid in tqdm(arxiv_ids, desc="Papers"):
            chunks = groups[aid]

            contexts = make_context_windows(
                chunks, max_chunks_per_context=args.max_chunks_per_context
            )

            # limit number of contexts per paper
            contexts = contexts[: args.max_contexts_per_paper]

            for ctx in contexts:
                qa = generate_qa(ctx)
                if not qa:
                    continue

                record = {
                    "arxiv_id": aid,
                    "question": qa["question"],
                    "contexts": ctx,
                    "answer": qa["answer"],
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1

    print(f"Completed: {count} high-quality scientific Q/A written to {out}")


if __name__ == "__main__":
    main()
