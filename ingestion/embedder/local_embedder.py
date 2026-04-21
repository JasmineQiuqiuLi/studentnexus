from __future__ import annotations
import logging
from typing import List
from sentence_transformers import SentenceTransformer
from ingestion.embedder.base import BaseEmbedder

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class LocalHFEmbedder(BaseEmbedder):
    def __init__(self, model_name:str="BAAI/bge-base-en-v1.5", batch_size:int=32):
        super().__init__(model_name, batch_size)
        self.model = SentenceTransformer(model_name)
    
        logger.info(f"Initialized LocalHFEmbedder with model: {model_name}")

    def provider(self):
        return "local huggingface"
    
    def dimension(self):
        test=self.model.encode(['Hello world'])
        return len(test[0]) if len(test) > 0 else -1
    
    def embed_query(self, query:str) -> List[float]:
        vec=self.model.encode([query],normalize_embeddings=True)
        return vec[0].tolist() if len(vec) > 0 else []
    
    def embed_texts(self, texts:List[str]) -> List[List[float]]:
        if not texts:
            return []
        vecs=self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        return [vec.tolist() for vec in vecs] if len(vecs) > 0 else []
    
