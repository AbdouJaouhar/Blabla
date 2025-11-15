import json
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import callback_context, dcc, html
from dash.dependencies import Input, Output, State

# ================================================
# Configuration
# ================================================
INPUT_DATASET = "rag_dataset_c_clean.jsonl"
OUTPUT_DATASET = "rag_dataset_c_moderated.jsonl"

# Load dataset
records = []
with open(INPUT_DATASET, "r", encoding="utf-8") as f:
    for line in f:
        try:
            records.append(json.loads(line))
        except:
            pass

TOTAL = len(records)

output_path = Path(OUTPUT_DATASET)
output_path.touch(exist_ok=True)


# ================================================
# Dash UI
# ================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])

app.layout = dbc.Container(
    [
        html.H2("🔍 Dataset Moderation Interface"),
        html.Hr(),
        dcc.Store(id="current-index", data=0),
        html.Div(id="progress-bar", style={"marginBottom": "20px"}),
        # Context
        html.H4("Context Chunks"),
        html.Div(
            id="context-display",
            style={
                "whiteSpace": "pre-wrap",
                "border": "1px solid #ccc",
                "padding": "10px",
                "borderRadius": "6px",
                "backgroundColor": "#F9F9F9",
            },
        ),
        html.Br(),
        # Question
        html.H4("Question"),
        dcc.Textarea(
            id="question-input",
            style={"width": "100%", "height": "100px"},
        ),
        html.Br(),
        # Answer
        html.H4("Answer"),
        dcc.Textarea(
            id="answer-input",
            style={"width": "100%", "height": "150px"},
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "❌ Reject", id="btn-reject", color="danger", className="me-2"
                    ),
                    width="auto",
                ),
                dbc.Col(
                    dbc.Button("✔ Approve", id="btn-approve", color="success"),
                    width="auto",
                ),
                dbc.Col(
                    dbc.Button(
                        "➡ Next (skip)",
                        id="btn-skip",
                        color="secondary",
                        className="ms-2",
                    ),
                    width="auto",
                ),
            ],
            justify="start",
            align="center",
        ),
        html.Br(),
        html.Div(id="status-msg", style={"fontWeight": "bold"}),
    ],
    fluid=True,
)


# ================================================
# Helper to save moderated sample
# ================================================
def save_record(record):
    with open(OUTPUT_DATASET, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ================================================
# Update page content
# ================================================
@app.callback(
    [
        Output("context-display", "children"),
        Output("question-input", "value"),
        Output("answer-input", "value"),
        Output("progress-bar", "children"),
        Output("status-msg", "children"),
        Output("current-index", "data"),
    ],
    [
        Input("btn-approve", "n_clicks"),
        Input("btn-reject", "n_clicks"),
        Input("btn-skip", "n_clicks"),
    ],
    [
        State("current-index", "data"),
        State("question-input", "value"),
        State("answer-input", "value"),
    ],
)
def update_page(btn_approve, btn_reject, btn_skip, idx, q_text, a_text):
    triggered = callback_context.triggered[0]["prop_id"].split(".")[0]

    # Save if approved or rejected
    if triggered in ["btn-approve", "btn-reject"]:
        record = records[idx]
        record["question"] = q_text.strip()
        record["answer"] = a_text.strip()
        record["moderation"] = "approved" if triggered == "btn-approve" else "rejected"
        save_record(record)

    # Move to next index
    next_idx = idx + 1
    if next_idx >= TOTAL:
        return (
            "END OF DATASET",
            "",
            "",
            f"Completed {TOTAL}/{TOTAL}",
            "🎉 All records processed!",
            idx,
        )

    # Load next item
    rec = records[next_idx]
    context_text = "\n\n---\n\n".join(rec["contexts"])

    progress = f"Progress: {next_idx}/{TOTAL} ({round(next_idx / TOTAL * 100, 1)}%)"

    return (
        context_text,
        rec["question"],
        rec["answer"],
        progress,
        "",
        next_idx,
    )


# ================================================
# Run server
# ================================================
if __name__ == "__main__":
    print("Starting moderation dashboard at http://127.0.0.1:8050")
    app.run(host="127.0.0.1", port=8050, debug=True)
