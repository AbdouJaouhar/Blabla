import argparse
import os
import sqlite3
from pathlib import Path

import requests
from tqdm import tqdm

TIMEOUT = 20  # seconds


def ensure_output_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)


def get_papers_with_pdf(conn):
    cur = conn.cursor()
    cur.execute("SELECT arxiv_id, pdf_url FROM papers WHERE pdf_url IS NOT NULL")
    return cur.fetchall()


def download_pdf(arxiv_id: str, pdf_url: str, output_dir: str):
    filename = f"{arxiv_id}.pdf"
    filepath = os.path.join(output_dir, filename)

    if os.path.exists(filepath):
        return "[SKIP] Already exists"

    try:
        response = requests.get(pdf_url, timeout=TIMEOUT)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            return "[OK]"
        else:
            return f"[ERROR HTTP {response.status_code}]"
    except Exception as e:
        return f"[ERROR {e}]"


def main():
    parser = argparse.ArgumentParser(description="Download PDFs from SQLite database")
    parser.add_argument("db_path", help="Path to SQLite database")
    parser.add_argument(
        "--output", "-o", default="pdfs", help="Directory to store downloaded PDFs"
    )

    args = parser.parse_args()

    ensure_output_dir(args.output)

    conn = sqlite3.connect(args.db_path)
    papers = get_papers_with_pdf(conn)

    print(f"Found {len(papers)} papers with PDFs")

    for arxiv_id, pdf_url in tqdm(papers, desc="Downloading PDFs"):
        if pdf_url:
            result = download_pdf(arxiv_id, pdf_url, args.output)
            tqdm.write(f"{arxiv_id}: {result}")

    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
