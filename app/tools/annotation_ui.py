# app/tools/annotation_ui.py

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="RAG Retrieval Comparison Tool",
    layout="wide"
)

# =====================================================
# PATHS
# =====================================================
DATA_DIR = Path("data/eval")
DATA_DIR.mkdir(parents=True, exist_ok=True)

QUERIES_PATH = DATA_DIR / "questions_test.csv"
LABELS_PATH = DATA_DIR / "labels.csv"

# =====================================================
# LOAD QUERIES
# =====================================================
def load_queries():
    if QUERIES_PATH.exists():
        df = pd.read_csv(
            QUERIES_PATH,
            encoding="utf-8-sig"
        )

        df.columns = (
            df.columns
            .str.strip()
            .str.replace("\ufeff", "", regex=False)
            .str.replace("\r", "", regex=False)
            .str.replace("\n", "", regex=False)
        )

        return df

    return pd.DataFrame([
        {
            "query_id": 1,
            "query": "What is OPT?",
            "category": "OPT",
            "difficulty": "easy"
        }
    ])

# =====================================================
# MOCK RETRIEVAL
# Replace later with real retrieval pipelines
# =====================================================
def fake_retrieve(query, system_name):

    rows = []

    for i in range(1, 6):

        rows.append({
            "rank": i,
            "chunk_id": f"{system_name[:2].upper()}_{100+i}",
            "source": f"Source {((i-1)%3)+1}",
            "score": round(1/(i+1), 4),
            "chunk_text":
                f"[{system_name}] Rank {i} result for query: {query}. "
                f"Replace fake_retrieve() with your real pipeline."
        })

    return pd.DataFrame(rows)

# =====================================================
# SAVE LABELS
# =====================================================
def save_annotations(rows):

    df = pd.DataFrame(rows)

    header = not LABELS_PATH.exists()

    df.to_csv(
        LABELS_PATH,
        mode="a",
        index=False,
        header=header
    )

# =====================================================
# SESSION STATE
# =====================================================
queries = load_queries()

if "idx" not in st.session_state:
    st.session_state.idx = 0

# =====================================================
# CURRENT QUERY
# =====================================================
row = queries.iloc[st.session_state.idx]

query_id = row.get("query_id", st.session_state.idx + 1)
query = row.get("query", "")
category = row.get("category", "")
difficulty = row.get("difficulty", "")

# =====================================================
# HEADER
# =====================================================
st.title("RAG Retrieval Comparison Tool")

h1, h2, h3 = st.columns([4,1,1])

with h1:
    st.subheader(f"Query #{query_id}: {query}")

with h2:
    st.metric("Category", category)

with h3:
    st.metric("Difficulty", difficulty)

st.markdown("---")

# =====================================================
# RUN ALL 3 SYSTEMS
# =====================================================
dense_df = fake_retrieve(query, "dense")
hybrid_df = fake_retrieve(query, "hybrid")
rerank_df = fake_retrieve(query, "hybrid_rerank")

# =====================================================
# UI COLUMNS
# =====================================================
col1, col2, col3 = st.columns(3)

all_annotations = []

# =====================================================
# RENDER FUNCTION
# =====================================================
def render_column(container, title, df, system_name):

    global all_annotations

    with container:

        st.markdown(f"## {title}")

        for _, r in df.iterrows():

            with st.container(border=True):

                st.markdown(
                    f"**Rank {int(r['rank'])}** | "
                    f"Chunk: `{r['chunk_id']}`"
                )

                st.caption(
                    f"{r['source']} | Score: {r['score']}"
                )

                st.write(r["chunk_text"])

                rel = st.radio(
                    "Relevance",
                    options=[0,1,2,3],
                    horizontal=True,
                    format_func=lambda x: {
                        0: "Irrelevant",
                        1: "Slight",
                        2: "Helpful",
                        3: "Direct"
                    }[x],
                    key=f"{query_id}_{system_name}_{r['chunk_id']}"
                )

                all_annotations.append({
                    "timestamp":
                        datetime.utcnow().isoformat(),
                    "query_id": query_id,
                    "query": query,
                    "system": system_name,
                    "rank": int(r["rank"]),
                    "chunk_id": r["chunk_id"],
                    "source": r["source"],
                    "score": r["score"],
                    "relevance": rel
                })

# =====================================================
# DRAW 3 MODELS
# =====================================================
render_column(
    col1,
    "Dense",
    dense_df,
    "dense"
)

render_column(
    col2,
    "Hybrid",
    hybrid_df,
    "hybrid"
)

render_column(
    col3,
    "Hybrid + Rerank",
    rerank_df,
    "hybrid_rerank"
)

# =====================================================
# ACTION BUTTONS
# =====================================================
st.markdown("---")

b1, b2, b3 = st.columns(3)

if b1.button(
    "Save Labels",
    use_container_width=True
):
    save_annotations(all_annotations)
    st.success(
        f"Saved {len(all_annotations)} labels "
        f"to {LABELS_PATH}"
    )

if b2.button(
    "Previous Query",
    use_container_width=True
):
    st.session_state.idx = max(
        0,
        st.session_state.idx - 1
    )
    st.rerun()

if b3.button(
    "Next Query",
    use_container_width=True
):
    st.session_state.idx = min(
        len(queries)-1,
        st.session_state.idx + 1
    )
    st.rerun()

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")

st.caption(
    "Replace fake_retrieve() with real dense / hybrid / rerank pipelines."
)