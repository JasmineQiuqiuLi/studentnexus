from __future__ import annotations

import logging
import pandas as pd

from ingestion.embedder.factory import get_embedder
from vectorstore.pgvector_client import PGVectorClient
from scripts.path import CHUNKED_DIR


# ==================================================
# logging
# ==================================================
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ==================================================
# config
# ==================================================
MODEL_NAME = "bge-base"          # openai-small / openai-large / bge-base / bge-large
CSV_PATH = CHUNKED_DIR / "chunks.csv"
LIMIT_ROWS = 5                  # None = all rows


# ==================================================
# MAIN
# ==================================================
def main():

    logger.info(f"Starting ingestion with model: {MODEL_NAME}")

    # ----------------------------------------------
    # Load CSV
    # ----------------------------------------------
    df = pd.read_csv(CSV_PATH)

    if LIMIT_ROWS:
        df = df.head(LIMIT_ROWS)

    logger.info(f"Loaded {len(df)} rows from {CSV_PATH}")

    # ----------------------------------------------
    # Required columns
    # ----------------------------------------------
    required_columns = {"doc_id", "chunk_text"}

    missing = required_columns - set(df.columns)

    if missing:
        logger.error(f"Missing required columns: {missing}")
        return

    # ----------------------------------------------
    # Init systems
    # ----------------------------------------------
    embedder = get_embedder(MODEL_NAME)

    logger.info(
        f"Initialized embedder: "
        f"{embedder.provider()} "
        f"dim={embedder.dimension()}"
    )

    db = PGVectorClient()

    inserted = 0

    try:
        total = len(df)

        # ------------------------------------------
        # Process rows
        # ------------------------------------------
        for idx, row in df.iterrows():

            doc_id = str(row["doc_id"])
            chunk_text = str(row["chunk_text"])

            # --------------------------------------
            # Build metadata from CSV row
            # --------------------------------------
            metadata = {}

            optional_fields = [
                "chunk_id",      # original csv id
                "title",
                "topic",
                "url",
                "source_type",
                "source_name",
                "section",
                "chunk_order",
                "last_edited",
                "retrieved",
            ]

            for field in optional_fields:
                if field in df.columns:
                    val = row[field]

                    if pd.notna(val):
                        metadata[field] = val

            logger.info(
                f"[{idx+1}/{total}] "
                f"Embedding doc_id={doc_id}"
            )

            # --------------------------------------
            # 1 Insert chunk row
            # returns DB chunk_id
            # --------------------------------------
            new_chunk_id = db.insert_chunk(
                doc_id=doc_id,
                chunk_text=chunk_text,
                metadata=metadata
            )

            # --------------------------------------
            # 2 Generate embedding
            # --------------------------------------
            vector = embedder.embed_query(
                chunk_text
            )

            # --------------------------------------
            # 3 Insert vector
            # --------------------------------------
            db.insert_embedding(
                model_name=MODEL_NAME,
                chunk_id=new_chunk_id,
                embedding=vector
            )

            inserted += 1

        logger.info(
            f"Ingestion complete. "
            f"Total inserted: {inserted}"
        )

    except Exception as e:
        logger.exception(
            f"Error during ingestion: {e}"
        )

    finally:
        db.close()


# ==================================================
# RUN
# ==================================================
if __name__ == "__main__":
    main()