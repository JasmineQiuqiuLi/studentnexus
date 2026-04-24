# app/tools/annotation_ui.py

import sys
import time
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

import streamlit as st
import pandas as pd

from app.retrieval.search_pipeline import SearchPipeline
from ingestion.embedder.factory import get_embedder

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="RAG Retrieval Comparison Tool",
    layout="wide"
)

# =====================================================
# CONFIG
# =====================================================
EMBED_MODEL_KEY = "openai-small"
TOP_K = 5

# =====================================================
# PATHS
# =====================================================
DATA_DIR = Path("data/eval")
DATA_DIR.mkdir(parents=True, exist_ok=True)

QUERIES_PATH = DATA_DIR / "questions_benchmark.csv"
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
# SAVE LABELS
# =====================================================
def save_annotations(rows):

    if not rows:
        return

    df = pd.DataFrame(rows)

    header = not LABELS_PATH.exists()

    df.to_csv(
        LABELS_PATH,
        mode="a",
        index=False,
        header=header
    )

# =====================================================
# CACHE
# =====================================================
@st.cache_resource
def get_pipeline():
    return SearchPipeline()

@st.cache_resource
def get_embedder_cached():
    return get_embedder(EMBED_MODEL_KEY)

# =====================================================
# RETRIEVAL
# =====================================================
def run_strategy(
    query_text,
    strategy_name,
    top_k=TOP_K
):

    pipeline = get_pipeline()
    embedder = get_embedder_cached()

    query_vector = embedder.embed_query(query_text)

    start = time.perf_counter()

    results = pipeline.search(
        strategy=strategy_name,
        query_text=query_text,
        query_vector=query_vector,
        model_name=EMBED_MODEL_KEY,
        top_k=top_k
    )

    elapsed_ms = round(
        (time.perf_counter() - start) * 1000,
        2
    )

    if not results:
        return pd.DataFrame(), elapsed_ms

    return pd.DataFrame(results), elapsed_ms

# =====================================================
# SESSION STATE
# =====================================================
queries = load_queries()

if "idx" not in st.session_state:
    st.session_state.idx = 0

if "label_cache" not in st.session_state:
    st.session_state.label_cache = {}

# =====================================================
# CURRENT QUERY
# =====================================================
row = queries.iloc[st.session_state.idx]

query_id = row.get(
    "query_id",
    st.session_state.idx + 1
)

query = row.get("query", "")
category = row.get("category", "")
difficulty = row.get("difficulty", "")

# =====================================================
# HEADER
# =====================================================
st.title("RAG Retrieval Comparison Tool")

h1, h2, h3 = st.columns([5,1,1])

with h1:
    st.subheader(
        f"Query #{query_id}: {query}"
    )

with h2:
    st.metric("Category", category)

with h3:
    st.metric("Difficulty", difficulty)

st.caption(
    f"Embedding Model: {EMBED_MODEL_KEY}"
)

st.markdown("---")

# =====================================================
# RUN STRATEGIES
# =====================================================
with st.spinner("Running retrieval systems..."):

    dense_df, dense_ms = run_strategy(
        query,
        "dense"
    )

    hybrid_df, hybrid_ms = run_strategy(
        query,
        "hybrid"
    )

    rerank_df, rerank_ms = run_strategy(
        query,
        "hybrid_rerank"
    )

# =====================================================
# LATENCY
# =====================================================
m1, m2, m3 = st.columns(3)

m1.metric("Dense ms", dense_ms)
m2.metric("Hybrid ms", hybrid_ms)
m3.metric("Hybrid + Rerank ms", rerank_ms)

st.markdown("---")

# =====================================================
# MAIN LAYOUT
# =====================================================
col1, col2, col3 = st.columns(3)

all_annotations = []

# =====================================================
# RENDER COLUMN
# =====================================================
def render_column(
    container,
    title,
    df,
    system_name,
    latency_ms
):

    global all_annotations

    with container:

        st.markdown(f"## {title}")

        if df.empty:
            st.warning("No results.")
            return

        for i, r in df.iterrows():

            rank = int(r.get("rank", i + 1))
            chunk_id = str(r.get("chunk_id", ""))
            doc_id = r.get("doc_id", "")

            score = r.get(
                "rerank_score",
                r.get(
                    "fused_score",
                    r.get(
                        "score",
                        ""
                    )
                )
            )

            chunk_text = r.get(
                "chunk_text",
                "[No chunk text found]"
            )

            metadata = r.get(
                "metadata",
                {}
            )

            # ------------------------------------------------
            # SAME QUERY + SAME CHUNK SHARES LABEL
            # ------------------------------------------------
            cache_key = (
                str(query_id),
                chunk_id
            )

            widget_key = (
                f"rel_{query_id}_"
                f"{system_name}_"
                f"{chunk_id}"
            )

            # current shared value
            shared_val = st.session_state.label_cache.get(
                cache_key,
                -1
            )

            # force widget state to sync with shared cache
            if shared_val != -1:
                # Always push the shared label into the widget,
                # regardless of whether it was already initialized.
                st.session_state[widget_key] = shared_val
            elif widget_key not in st.session_state:
                st.session_state[widget_key] = -1

            label_options = [-1,0,1,2,3]

            with st.container(border=True):

                st.markdown(
                    f"**Rank {rank}** | "
                    f"Chunk `{chunk_id}`"
                )

                st.caption(
                    f"Doc: {doc_id} | "
                    f"Score: {score}"
                )

                if shared_val != -1:
                    st.success(
                        "✓ already labeled in another strategy"
                    )

                st.text_area(
                    "Chunk Text",
                    value=chunk_text,
                    height=220,
                    key=f"text_{query_id}_{system_name}_{chunk_id}"
                )

                if metadata:
                    with st.expander("Metadata"):
                        st.json(metadata)

                rel = st.radio(
                    "Relevance",
                    options=label_options,
                    horizontal=True,
                    format_func=lambda x: {
                        -1: "Not labeled",
                        0: "Irrelevant",
                        1: "Slight",
                        2: "Helpful",
                        3: "Direct"
                    }[x],
                    key=widget_key
                )

                # update shared cache
                if rel != -1:
                    st.session_state.label_cache[
                        cache_key
                    ] = rel

                    all_annotations.append({
                        "timestamp":
                            datetime.utcnow().isoformat(),
                        "query_id":
                            query_id,
                        "query":
                            query,
                        "system":
                            system_name,
                        "rank":
                            rank,
                        "chunk_id":
                            chunk_id,
                        "doc_id":
                            doc_id,
                        "score":
                            score,
                        "relevance":
                            rel,
                        "latency_ms":
                            latency_ms
                    })

# =====================================================
# DRAW 3 COLUMNS
# =====================================================
render_column(
    col1,
    "Dense",
    dense_df,
    "dense",
    dense_ms
)

render_column(
    col2,
    "Hybrid",
    hybrid_df,
    "hybrid",
    hybrid_ms
)

render_column(
    col3,
    "Hybrid + Rerank",
    rerank_df,
    "hybrid_rerank",
    rerank_ms
)

# =====================================================
# BUTTONS
# =====================================================
st.markdown("---")

b1, b2, b3 = st.columns(3)

if b1.button(
    "Save Labels",
    use_container_width=True
):

    save_annotations(
        all_annotations
    )

    st.success(
        f"Saved {len(all_annotations)} rows "
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
    "Dense vs Hybrid vs Hybrid+Rerank "
    "evaluation UI with synced shared labels."
    "latency and doc coverage"
)