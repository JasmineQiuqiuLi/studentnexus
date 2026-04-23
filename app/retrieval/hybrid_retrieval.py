from app.retrieval.dense import DenseRetriever
from app.retrieval.sparse import SparseRetriever

class HybridRetriever:
    def __init__(self):
        self.dense_retriever=DenseRetriever()
        self.sparse_retriever=SparseRetriever()

    def search(self,query_text,query_vector,model_name,top_k=5):
        sparse_results=self.sparse_retriever.search(query_text,top_k=20)
        dense_results=self.dense_retriever.search(model_name,query_vector,top_k=20)

        fused=self.reciprocal_rank_fusion(sparse_results,dense_results)

        return fused[:top_k]

    def reciprocal_rank_fusion(self,dense_results,sparse_results,k=60):
        scores={}
        docs={}
        for rank, item in enumerate(dense_results,start=1):
            cid=item['chunk_id']
            scores[cid]=scores.get(cid,0)+1/(rank+k)
            docs[cid]=item
        for rank, item in enumerate(sparse_results,start=1):
            cid=item['chunk_id']
            scores[cid]=scores.get(cid,0)+1/(rank+k)
            docs[cid]=item

        ranked=sorted(scores.items(),key=lambda x:x[1],reverse=True)
        final=[]

        for cid,score in ranked:
            item=docs[cid]
            item['fused_score']=score
            final.append(item)
        
        return final
    