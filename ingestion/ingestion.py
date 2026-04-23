from __future__ import annotations

import argparse
import logging
import pandas as pd

from ingestion.embedder.factory import get_embedder
from vectorstore.pgvector_client import PGVectorClient
from scripts.path import CHUNKED_DIR
from ingestion.embedder.factory import MoDEL_CHOICES

logger=logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

csv_path=CHUNKED_DIR / "chunks.csv"
csv_path_embedded=CHUNKED_DIR / "chunks_embedded.csv"

# ==================================================
# Helper functions
# ==================================================
def load_csv(path):
    df=pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def save_df(df, path=csv_path_embedded):
    df.to_csv(path, index=False)
    logger.info(f"Saved {len(df)} rows to {path}")


# ==================================================
# stage 1: store chunk text + metadata in pgvector
# ==================================================
def store_chunk():
    df=load_csv(csv_path)
    if "db_chunk_id" not in df.columns:
        df["db_chunk_id"] = pd.NA
    client=PGVectorClient()
    logger.info("Storing chunks and metadata in pgvector...")
    inserted=0

    try:

        for idx, row in df.iterrows():

            doc_id = row["doc_id"]
            chunk_text = row["chunk_text"]

            metadata = {}

            for col in df.columns:
                if col not in [
                    "doc_id",
                    "chunk_text",
                    "db_chunk_id",
                    "chunk_id"
                ]:
                    val = row[col]

                    if pd.notna(val):
                        metadata[col] = val

            new_chunk_id = client.insert_chunk(
                doc_id,
                chunk_text,
                metadata
            )

            if new_chunk_id:
                df.at[idx, "db_chunk_id"] = int(new_chunk_id)
                inserted += 1
            
        save_df(df)
        logger.info(f"Inserted {inserted} chunks into pgvector.")
    except Exception as e:
        logger.error(f"Error inserting chunks: {e}")
    finally:
        client.close()


# ==================================================
# stage 2: embed chunks and update pgvector entries
# ==================================================
def store_embeddings(model_name):
    df=load_csv(csv_path_embedded)
    if 'db_chunk_id' not in df.columns:
        logger.error("db_chunk_id column not found in CSV. Please run store_chunk() first.")
        return
    
    db=PGVectorClient()
    embedder=get_embedder(model_name)

    inserted=0

    try:
        for idx,row in df.iterrows():
            chunk_id=row['db_chunk_id']
            chunk_text=row['chunk_text']

            vector=embedder.embed_query(chunk_text)
            db.insert_embedding( chunk_id=chunk_id, model_name=model_name, embedding=vector)
            inserted+=1
        logger.info(f"Embedded and updated {inserted} chunks with model {model_name}.")
    except Exception as e:
        logger.error(f"Error embedding chunks: {e}")
    finally:
        db.close()


# ==================================================
# main
# ==================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        type=str,
        choices=["store_chunk", "store_embeddings"],
        required=True
    )

    parser.add_argument(
        "--model_name",
        type=str,
        choices=MoDEL_CHOICES,
        default="bge-base"
    )

    args=parser.parse_args()

    if args.stage=="store_chunk":
        store_chunk()
    elif args.stage=="store_embeddings":
        store_embeddings(args.model_name)


if __name__=="__main__":
    main()