from vectorstore.pgvector_client import PGVectorClient

class SparseRetriever:
    def __init__(self):
        self.db=PGVectorClient()
    
    def search(self,query,top_k=10):
        sql="""
        SELECT 
            chunk_id,
            doc_id, 
            chunk_text,
            metadata,
            ts_rank(to_tsvector('english', chunk_text), plainto_tsquery('english', %s)) AS score
        FROM chunks
        WHERE to_tsvector('english', chunk_text) @@ plainto_tsquery('english', %s)
        ORDER BY score DESC
        LIMIT %s;
        """

        with self.db.conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    query,
                    query,
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
                    "score": float(row[4]),
                }
            )
        return results