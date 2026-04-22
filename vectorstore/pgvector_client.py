# vectorstore/pgvector_client.py
# Supabase + PostgreSQL + pgvector client

from __future__ import annotations

import os
import json
import logging
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()

logger=logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DATABASE_URL=os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables.")

# ===================================================
# MODEL -> TABLE MAP
# ===================================================

MODEL_TABLES = {
    "openai-small": "emb_openai_small",
    "bge-base": "emb_bge_base",
    "bge-large": "emb_bge_large",
}

class PGVectorClient:
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL)
        self.conn.autocommit = True
        logger.info("Connected to PostgreSQL database.")

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("PostgreSQL connection closed.")
    
    def insert_chunk(
            self,
            doc_id: str,
            chunk_text: str,
            metadata: Optional[Dict[str, Any]] = None
        ) -> int:

        sql="""
            INSERT INTO chunks (doc_id, chunk_text, metadata)
            VALUES (%s, %s, %s)
            RETURNING chunk_id;
        """

        with self.conn.cursor() as cur:
            cur.execute(sql, (doc_id, chunk_text, Json(metadata)))
            chunk_id = cur.fetchone()[0]
            logger.info(f"Inserted chunk with ID: {chunk_id}")
            return chunk_id

    def insert_embedding(
            self,
            chunk_id: int,
            model_name: str,
            embedding: List[float]
        ) -> None:

        table_name = MODEL_TABLES.get(model_name)
        if not table_name:
            raise ValueError(f"Unsupported model name: {model_name}")

        sql=f"""
            INSERT INTO {table_name} (chunk_id, embedding)
            VALUES (%s, %s);
        """

        with self.conn.cursor() as cur:
            cur.execute(sql, (chunk_id, embedding))
            logger.info(f"Inserted embedding for chunk ID: {chunk_id} into table: {table_name}")
    
    def search(
            self,
            model_name: str,
            query_vector: List[float],
            top_k: int = 5
        ) -> List[Dict[str, Any]]:
        table_name = MODEL_TABLES.get(model_name)
        if not table_name:
            raise ValueError(f"Unsupported model name: {model_name}")
        
        sql = f"""
        SELECT
            c.chunk_id,
            c.doc_id,
            c.chunk_text,
            c.metadata,
            e.embedding <=> %s AS distance
        FROM {table_name} e
        JOIN chunks c ON e.chunk_id = c.chunk_id
        ORDER BY e.embedding <=> %s
        LIMIT %s;
        """

        # vector_str = json.dumps(query_vector)
        vector_str = self._vector_to_pg(query_vector)
        with self.conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    vector_str,
                    vector_str,
                    top_k
                )
            )

            rows = cur.fetchall()

        results = []

        for row in rows:
            results.append(
                {
                    "chunk_id": row[0],
                    "doc_id": row[1],
                    "chunk_text": row[2],
                    "metadata": row[3],
                    "distance": float(row[4]),
                }
            )

        return results
    
    def bulk_insert_chunks(
            self,
            chunks: List[Dict]
    ) -> List[int]:
        
        ids=[]

        for row in chunks:
            cid=self.insert_chunk(
                doc_id=row["doc_id"],
                chunk_text=row["chunk_text"],
                metadata=row.get("metadata",{})
            )
            ids.append(cid)
        return ids
    
    # ------------------------------------------------
    # HELPER
    # ------------------------------------------------
    def _vector_to_pg(
        self,
        vector: List[float]
    ) -> str:
        """
        Convert Python list -> pgvector string

        [0.1,0.2,0.3]
        """
        return "[" + ",".join(map(str, vector)) + "]"
    

    
# ===================================================
# TEST
# ===================================================

if __name__ == "__main__":

    db = PGVectorClient()

    try:

        # 1 insert chunk
        cid = db.insert_chunk(
            doc_id="demo_doc",
            chunk_text="STEM OPT allows eligible students to work.",
            metadata={"source": "manual_test"}
        )

        # fake vector for testing only
        vec = [0.01] * 1536

        # 2 insert embedding
        db.insert_embedding(
            model_name="openai-small",
            chunk_id=cid,
            embedding=vec
        )

        # 3 search
        results = db.search(
            model_name="openai-small",
            query_vector=vec,
            top_k=3
        )

        print(results)

    finally:
        db.close()