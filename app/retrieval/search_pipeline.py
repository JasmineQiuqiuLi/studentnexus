from typing import List, Dict, Any

from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid_retrieval import HybridRetriever
from app. rerank.reranker import CohereReranker


class SearchPipeline:
    def __init__(self):
        self.dense=DenseRetriever()
        self.hybrid=HybridRetriever()
        self.reranker=CohereReranker()

    def search(
        self,
        strategy:str,
        query_text:str,
        query_vector:List[float],
        model_name:str = "text-embedding-3-small",
        top_k:int=5
    ) -> List[Dict[str,Any]]:
        
        strategy=strategy.lower()

        if strategy=='dense':
            return self.run_dense(
                model_name=model_name,
                query_vector=query_vector,
                top_k=top_k
            )
        elif strategy=='hybrid':
            return self.run_hybrid(
                query_text=query_text,
                query_vector=query_vector,
                model_name=model_name,
                top_k=top_k
            )
        elif strategy=='hybrid_rerank':
            return self.run_hybrid_rerank(
                query_text=query_text,
                query_vector=query_vector,
                model_name=model_name,
                top_k=top_k
            )
        
    # ==================
    # Dense
    # ==================
    def run_dense(self,model_name,query_vector,top_k):
        results=self.dense.search(
            model_name=model_name,
            query=query_vector,
            top_k=top_k
        )
        return self.add_rank(results)

    # =================
    # Hybrid
    # ===================
    def run_hybrid(self,query_text,query_vector,model_name,top_k):
        results=self.hybrid.search(
            query_text=query_text,
            query_vector=query_vector,
            model_name=model_name,
            top_k=top_k
        )
        return self.add_rank(results)


    # ===================
    # Hybrid + Rerank
    # ===================
    def run_hybrid_rerank(self,query_text,query_vector,model_name,top_k):
        candidates=self.hybrid.search(
            query_text=query_text,
            query_vector=query_vector,
            model_name=model_name,
            top_k=20
        )
        reranked=self.reranker.rerank(
            query=query_text,
            candidates=candidates,
            top_n=top_k
        )

        return self.add_rank(reranked)


    # ======================
    # Utility
    # =======================
    def add_rank(self,results):
        for idx,item in enumerate(results,start=1):
            item["rank"]=idx
        
        return results
    
