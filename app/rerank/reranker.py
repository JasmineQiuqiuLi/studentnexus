from __future__ import annotations

import os
import logging
from typing import List, Any, Dict, Optional

import cohere
from dotenv import load_dotenv

load_dotenv()

logger=logging.getLogger(__name__)

class CohereReranker:
    """
    Reranks retrieved chunks using Cohere Rerank
    """
    def __init__(self, model:str='rerank-v3.5',api_key:Optional[str]=None,max_tokens_per_doc:int=4096):
        self.api_key=api_key or os.getenv("COHERE_API_KEY")
        if not self.api_key:
            raise ValueError("COHERE_API_KEY not found in environment variables.")
        self.client=cohere.ClientV2(api_key=self.api_key)
        self.model=model
        self.max_tokens_per_doc=max_tokens_per_doc

    def rerank(
            self,
            query:str,
            candidates: List[Dict[str, Any]],
            top_n: int = 5
    ) -> List[Dict[str,Any]]:
        """
        reranks candidates based on relevance to the query
        """

        if not query or not query.strip():
            logger.warning("Empty query provided to reranker.")
            return candidates[:top_n]
        if not candidates:
            logger.warning("No candidates provided to reranker.")
            return []
        # Prepare inputs for Cohere Rerank
        documents=[
            self._format_document(candidate) for candidate in candidates
        ]

        try:
            response=self.client.rerank(
                model=self.model,
                query=query,
                documents=documents,
                top_n=min(top_n, len(candidates)),
                max_tokens_per_doc=self.max_tokens_per_doc
            )
        except Exception as e:
            logger.error(f"Cohere rerank API call failed: {e}")
            return candidates[:top_n]
        
        reranked_results=[]

        for rank, result in enumerate(response.results):
            original_idx=result.index
            candidate=candidates[original_idx].copy()

            candidate['rerank_score']=result.relevance_score
            candidate['rerank_rank']=rank + 1
            reranked_results.append(candidate)
        return reranked_results
    
    def _format_document(self, candidate: Dict[str, Any]) -> str:
        """
        Convertt a candidate chunk into text format for cohere reranking
        Including metadata can help the reranker understand context and relevance better
        """

        metadata=candidate.get('metadata',{})
        title=metadata.get('title','')
        source_name=metadata.get('source_name','')
        section=metadata.get('section','')
        chunk_text=candidate.get('chunk_text','')

        return f"""
        Title: {title}
        Source: {source_name}
        Section: {section}
        Text: {chunk_text}
        """.strip()
    

