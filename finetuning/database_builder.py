#!/usr/bin/env python
"""
Deep Learning Educational Paper Curator (arXiv + Dash + SQLite)

Features:
- Relational SQLite schema:
    searches (search args)
    papers (unique arxiv_id, status: undecided|kept|ignored)
    paper_searches (many-to-many link)
- Search arXiv for tutorial/survey/overview/intro-style deep learning papers
- Store ALL retrieved papers as 'undecided'
- Skip already 'kept' or 'ignored' papers in new results
- Let user mark papers as KEPT or IGNORED from the UI
"""

import sqlite3
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

import arxiv
from arxiv import HTTPError
from dash import Dash, Input, Output, State, ctx, dash_table, dcc, html

# =========================
# Config
# =========================

DB_PATH = Path("papers.db")

SUBDOMAIN_QUERIES: Dict[str, str] = {
    "foundations_mlp": '"neural network" OR "multilayer perceptron" OR MLP OR backpropagation',
    "optimization_training": '"stochastic gradient descent" OR SGD OR Adam OR "learning rate schedule" OR "batch normalization"',
    "regularization": 'dropout OR "weight decay" OR "L2 regularization" OR "data augmentation"',
    "cnn": '"convolutional neural network" OR "convolutional networks" OR CNN OR convnet',
    "rnn_sequence": '"recurrent neural network" OR RNN OR LSTM OR GRU OR "sequence model"',
    "transformers": 'transformer OR "self-attention" OR "attention is all you need"',
    "gnn": '"graph neural network" OR GNN OR "graph convolutional network" OR GCN',
    "autoencoders_representation": 'autoencoder OR "denoising autoencoder" OR "variational autoencoder" OR VAE OR "representation learning"',
    "gans": '"generative adversarial network" OR GAN OR DCGAN OR WGAN OR StyleGAN',
    "diffusion_models": '"diffusion model" OR "score-based generative" OR "denoising diffusion"',
    "self_supervised": '"self-supervised learning" OR contrastive OR SimCLR OR MoCo OR BYOL OR "masked language modeling"',
    "dl_vision": '"deep learning" AND (vision OR "image classification" OR "object detection" OR segmentation)',
    "dl_nlp": '"deep learning" AND (NLP OR "natural language processing" OR transformer OR "language model")',
    "deep_rl": '"deep reinforcement learning" OR DQN OR "policy gradient" OR "actor-critic"',
    "probabilistic_dl": '"Bayesian neural network" OR "Bayesian deep learning" OR "uncertainty estimation"',
}

# Educational bias
EDU_KEYWORDS = [
    "tutorial",
    "survey",
    "overview",
    "review",
    '"lecture notes"',
    "primer",
    "introduction",
]

DEFAULT_CATEGORIES = ["cs.LG", "stat.ML", "cs.CV", "cs.CL", "cs.NE"]


# =========================
# DB helpers (SQLite)
# =========================


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Unique searches
    cur.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_query TEXT,
            categories TEXT,
            subdomain TEXT,
            created_at TEXT
        )
    """)

    # Unique papers
    cur.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arxiv_id TEXT UNIQUE,
            title TEXT,
            authors TEXT,
            summary TEXT,
            pdf_url TEXT,
            categories TEXT,
            subdomain TEXT,
            status TEXT DEFAULT 'undecided',
            created_at TEXT
        )
    """)

    # Many-to-many link between papers and searches
    cur.execute("""
        CREATE TABLE IF NOT EXISTS paper_searches (
            paper_id INTEGER,
            search_id INTEGER,
            PRIMARY KEY (paper_id, search_id),
            FOREIGN KEY (paper_id) REFERENCES papers(id),
            FOREIGN KEY (search_id) REFERENCES searches(id)
        )
    """)

    conn.commit()
    conn.close()


def get_or_create_search(
    base_query: str, categories: str, subdomain: Optional[str]
) -> int:
    """
    Return search_id for (base_query, categories, subdomain).
    Create a new row if needed.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id FROM searches
        WHERE base_query = ? AND categories = ? AND subdomain IS ?
        """,
        (base_query, categories, subdomain),
    )
    row = cur.fetchone()
    if row:
        conn.close()
        return row[0]

    cur.execute(
        """
        INSERT INTO searches (base_query, categories, subdomain, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (base_query, categories, subdomain, datetime.utcnow().isoformat()),
    )
    search_id = cur.lastrowid
    conn.commit()
    conn.close()
    return search_id


def insert_or_update_paper(
    arxiv_id: str, paper_data: dict, subdomain: Optional[str]
) -> int:
    """
    Insert a new paper with status='undecided', or update existing metadata while preserving status.
    Returns paper_id.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id, status FROM papers WHERE arxiv_id = ?", (arxiv_id,))
    row = cur.fetchone()

    if row:
        paper_id = row[0]
        # Update metadata but keep existing status
        cur.execute(
            """
            UPDATE papers
            SET title=?, authors=?, summary=?, pdf_url=?, categories=?, subdomain=?
            WHERE id=?
            """,
            (
                paper_data["title"],
                paper_data["authors"],
                paper_data["summary"],
                paper_data["pdf_url"],
                paper_data["categories"],
                subdomain,
                paper_id,
            ),
        )
    else:
        cur.execute(
            """
            INSERT INTO papers
            (arxiv_id, title, authors, summary, pdf_url, categories, subdomain, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'undecided', ?)
            """,
            (
                arxiv_id,
                paper_data["title"],
                paper_data["authors"],
                paper_data["summary"],
                paper_data["pdf_url"],
                paper_data["categories"],
                subdomain,
                datetime.utcnow().isoformat(),
            ),
        )
        paper_id = cur.lastrowid

    conn.commit()
    conn.close()
    return paper_id


def link_paper_to_search(paper_id: int, search_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO paper_searches (paper_id, search_id)
        VALUES (?, ?)
        """,
        (paper_id, search_id),
    )
    conn.commit()
    conn.close()


def get_arxiv_ids_by_status(status: str) -> Set[str]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT arxiv_id FROM papers WHERE status = ?", (status,))
    rows = cur.fetchall()
    conn.close()
    return {r[0] for r in rows}


def get_status_for_arxiv_ids(arxiv_ids: List[str]) -> dict:
    """
    Returns dict {arxiv_id: status}
    """
    if not arxiv_ids:
        return {}

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    placeholders = ",".join("?" for _ in arxiv_ids)
    cur.execute(
        f"SELECT arxiv_id, status FROM papers WHERE arxiv_id IN ({placeholders})",
        arxiv_ids,
    )
    rows = cur.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


def load_saved_papers(limit: int = 200) -> List[dict]:
    """
    Load 'kept' papers for the bottom table.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT arxiv_id, title, authors, categories, subdomain, pdf_url, status, created_at
        FROM papers
        WHERE status = 'kept'
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()

    cols = [
        "arxiv_id",
        "title",
        "authors",
        "categories",
        "subdomain",
        "pdf_url",
        "status",
        "created_at",
    ]
    return [dict(zip(cols, r)) for r in rows]


def update_papers_status(arxiv_ids: List[str], new_status: str):
    """
    Update status for a list of arxiv_ids.
    """
    if not arxiv_ids:
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    placeholders = ",".join("?" for _ in arxiv_ids)
    cur.execute(
        f"UPDATE papers SET status=? WHERE arxiv_id IN ({placeholders})",
        [new_status] + arxiv_ids,
    )
    conn.commit()
    conn.close()


# =========================
# arXiv search helpers
# =========================


def build_query(base_query: str, edu_keywords: List[str], categories: List[str]) -> str:
    """
    Build full arXiv query:
        (base_query)
        AND (ti:kw OR abs:kw for any kw in edu_keywords)
        AND (cat:...)
    """
    base = f"({base_query})" if base_query else "all"

    edu_parts = []
    for kw in edu_keywords:
        edu_parts.append(f"ti:{kw}")
        edu_parts.append(f"abs:{kw}")
    edu_clause = "(" + " OR ".join(edu_parts) + ")"

    cat_clause = ""
    if categories:
        cat_clause = " AND (" + " OR ".join(f"cat:{c}" for c in categories) + ")"

    return f"{base} AND {edu_clause}{cat_clause}"


def search_arxiv_new_only(
    base_query: str,
    subdomain_name: Optional[str],
    max_new_results: int,
    categories: List[str],
    search_id: int,
) -> Tuple[List[dict], str]:
    """
    Search arXiv for educational papers matching base_query, but:
    - store all retrieved papers in DB (if not already)
    - skip papers whose status is 'kept' or 'ignored'
    - return at most max_new_results 'undecided' papers for review
    """
    kept_ids = get_arxiv_ids_by_status("kept")
    ignored_ids = get_arxiv_ids_by_status("ignored")
    skip_ids = kept_ids | ignored_ids

    full_query = build_query(base_query, EDU_KEYWORDS, categories)

    client = arxiv.Client(
        page_size=50,
        delay_seconds=3,
        num_retries=5,
    )

    search = arxiv.Search(
        query=full_query,
        max_results=max_new_results * 5,  # overshoot, we filter later
        sort_by=arxiv.SortCriterion.Relevance,
        sort_order=arxiv.SortOrder.Descending,
    )

    new_results: List[dict] = []

    try:
        for res in client.results(search):
            arxiv_id = res.get_short_id()

            # Prepare paper metadata
            authors = ", ".join(a.name for a in res.authors)
            cats = ", ".join(res.categories) if res.categories else ""
            summary = (res.summary or "").replace("\n", " ")
            summary_short = textwrap.shorten(summary, width=350, placeholder="…")
            published_str = res.published.strftime("%Y-%m-%d") if res.published else ""

            paper_data = {
                "title": res.title,
                "authors": authors,
                "summary": summary_short,
                "pdf_url": res.pdf_url,
                "categories": cats,
            }

            # Insert/update in DB
            paper_id = insert_or_update_paper(arxiv_id, paper_data, subdomain_name)
            # Link to search
            link_paper_to_search(paper_id, search_id)

            # Skip if already marked kept or ignored
            if arxiv_id in skip_ids:
                continue

            # For undecided ones, add to result list
            new_results.append(
                {
                    "arxiv_id": arxiv_id,
                    "title": res.title,
                    "authors": authors,
                    "published": published_str,
                    "categories": cats,
                    "summary": summary_short,
                    "pdf_url": res.pdf_url,
                    "subdomain": subdomain_name or "",
                    "status": "undecided",
                }
            )

            if len(new_results) >= max_new_results:
                break

    except HTTPError as e:
        return [], f"HTTP error during arXiv search: {e}"
    except Exception as e:
        return [], f"Search failed: {e}"

    msg = f"Found {len(new_results)} new undecided papers."
    return new_results, msg


# =========================
# Dash app
# =========================

init_db()

app = Dash(__name__)
app.title = "Deep Learning Educational Paper Curator"

subdomain_options = [
    {"label": f"{name} → {q}", "value": name} for name, q in SUBDOMAIN_QUERIES.items()
]

category_options = [{"label": c, "value": c} for c in DEFAULT_CATEGORIES]

app.layout = html.Div(
    style={"fontFamily": "sans-serif", "margin": "2rem"},
    children=[
        html.H1("Deep Learning Educational Paper Curator (arXiv)"),
        html.P(
            "Search arXiv for tutorial/survey/overview/intro-style deep learning papers, "
            "review them, and mark them as KEPT or IGNORED. All papers and searches "
            "are stored in a local SQLite database."
        ),
        html.H2("Search"),
        html.Div(
            style={"display": "flex", "gap": "1rem", "flexWrap": "wrap"},
            children=[
                html.Div(
                    style={"minWidth": "350px"},
                    children=[
                        html.Label("Subdomain (optional)"),
                        dcc.Dropdown(
                            id="subdomain-dropdown",
                            options=subdomain_options,
                            placeholder="Choose a predefined deep learning subdomain",
                        ),
                    ],
                ),
                html.Div(
                    style={"minWidth": "350px"},
                    children=[
                        html.Label("Custom base query (optional, overrides subdomain)"),
                        dcc.Input(
                            id="custom-query",
                            type="text",
                            placeholder='e.g. "transformer" AND "self-attention"',
                            style={"width": "100%"},
                        ),
                    ],
                ),
            ],
        ),
        html.Br(),
        html.Div(
            style={"display": "flex", "gap": "1rem", "flexWrap": "wrap"},
            children=[
                html.Div(
                    children=[
                        html.Label("Categories"),
                        dcc.Dropdown(
                            id="category-dropdown",
                            options=category_options,
                            value=DEFAULT_CATEGORIES,
                            multi=True,
                        ),
                    ],
                    style={"minWidth": "300px"},
                ),
                html.Div(
                    children=[
                        html.Label("Max NEW papers (undecided)"),
                        dcc.Input(
                            id="max-results",
                            type="number",
                            value=30,
                            min=5,
                            max=200,
                            step=5,
                        ),
                    ],
                    style={"minWidth": "200px"},
                ),
                html.Div(
                    children=[
                        html.Button("Search arXiv", id="search-button", n_clicks=0),
                    ],
                    style={"display": "flex", "alignItems": "flex-end"},
                ),
            ],
        ),
        html.Br(),
        html.Div(id="search-status", style={"marginBottom": "0.5rem", "color": "#555"}),
        html.H2("Results (status = 'undecided')"),
        dash_table.DataTable(
            id="results-table",
            columns=[
                {"name": "arxiv_id", "id": "arxiv_id"},
                {"name": "title", "id": "title"},
                {"name": "authors", "id": "authors"},
                {"name": "published", "id": "published"},
                {"name": "categories", "id": "categories"},
                {"name": "summary", "id": "summary"},
                {"name": "pdf_url", "id": "pdf_url"},
                {"name": "subdomain", "id": "subdomain"},
                {"name": "status", "id": "status"},
            ],
            data=[],
            page_size=10,
            row_selectable="multi",
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "left",
                "whiteSpace": "normal",
                "height": "auto",
                "fontSize": 12,
            },
            style_header={
                "backgroundColor": "#f0f0f0",
                "fontWeight": "bold",
            },
        ),
        html.Br(),
        html.Div(
            style={"display": "flex", "gap": "1rem"},
            children=[
                html.Button("Mark selected as KEPT", id="mark-kept", n_clicks=0),
                html.Button("Mark selected as IGNORED", id="mark-ignored", n_clicks=0),
            ],
        ),
        html.Div(id="save-status", style={"marginTop": "0.5rem", "color": "green"}),
        html.H2("Saved papers (status = 'kept')"),
        dash_table.DataTable(
            id="saved-table",
            columns=[
                {"name": "arxiv_id", "id": "arxiv_id"},
                {"name": "title", "id": "title"},
                {"name": "authors", "id": "authors"},
                {"name": "categories", "id": "categories"},
                {"name": "subdomain", "id": "subdomain"},
                {"name": "pdf_url", "id": "pdf_url"},
                {"name": "status", "id": "status"},
                {"name": "created_at", "id": "created_at"},
            ],
            data=load_saved_papers(),
            page_size=10,
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "left",
                "whiteSpace": "normal",
                "height": "auto",
                "fontSize": 12,
            },
            style_header={
                "backgroundColor": "#f0f0f0",
                "fontWeight": "bold",
            },
        ),
    ],
)


@app.callback(
    Output("results-table", "data"),
    Output("search-status", "children"),
    Output("save-status", "children"),
    Output("saved-table", "data"),
    Input("search-button", "n_clicks"),
    Input("mark-kept", "n_clicks"),
    Input("mark-ignored", "n_clicks"),
    State("subdomain-dropdown", "value"),
    State("custom-query", "value"),
    State("category-dropdown", "value"),
    State("max-results", "value"),
    State("results-table", "data"),
    State("results-table", "selected_rows"),
    prevent_initial_call=True,
)
def unified_callback(
    search_clicks,
    kept_clicks,
    ignored_clicks,
    subdomain_value,
    custom_query,
    categories,
    max_results,
    results_data,
    selected_rows,
):
    trigger = ctx.triggered_id

    # =========================
    # 1. SEARCH
    # =========================
    if trigger == "search-button":
        if not max_results:
            max_results = 30
        if not categories:
            categories = DEFAULT_CATEGORIES

        # Determine base query
        if custom_query and custom_query.strip():
            base_query = custom_query.strip()
            subdomain_name = None
        elif subdomain_value:
            base_query = SUBDOMAIN_QUERIES[subdomain_value]
            subdomain_name = subdomain_value
        else:
            return (
                [],
                "Please choose a subdomain or provide a custom query.",
                "",
                load_saved_papers(),
            )

        categories_str = ",".join(categories)

        # Create search row
        search_id = get_or_create_search(
            base_query=base_query,
            categories=categories_str,
            subdomain=subdomain_name,
        )

        # Perform search
        results, msg = search_arxiv_new_only(
            base_query=base_query,
            subdomain_name=subdomain_name,
            max_new_results=int(max_results),
            categories=categories,
            search_id=search_id,
        )

        return results, msg, "", load_saved_papers()

    # =========================
    # 2. MARK AS KEPT / MARK AS IGNORED
    # =========================
    if trigger in ["mark-kept", "mark-ignored"]:
        if not results_data or not selected_rows:
            return results_data, "", "No rows selected.", load_saved_papers()

        new_status = "kept" if trigger == "mark-kept" else "ignored"
        message_prefix = (
            "Marked as KEPT: " if trigger == "mark-kept" else "Marked as IGNORED: "
        )

        # Get selected arxiv_ids
        selected_ids = [results_data[i]["arxiv_id"] for i in selected_rows]

        # Update in DB
        update_papers_status(selected_ids, new_status)

        # Remove changed rows from visible table
        updated_results = [
            row for i, row in enumerate(results_data) if i not in selected_rows
        ]

        message = message_prefix + ", ".join(selected_ids)

        return updated_results, "", message, load_saved_papers()

    # Default fallback (shouldn't happen)
    return results_data, "", "", load_saved_papers()


if __name__ == "__main__":
    # Run with: python app.py
    app.run(debug=True, host="0.0.0.0", port=8050)
