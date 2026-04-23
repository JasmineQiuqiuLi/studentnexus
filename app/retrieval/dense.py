from vectorstore.pgvector_client import PGVectorClient

class DenseRetriever:
    def __init__(self):
        self.db=PGVectorClient()
    
    def search(self,model_name,query,top_k=10):
        return self.db.search(
            model_name=model_name,
            query_vector=query,
            top_k=top_k
        )