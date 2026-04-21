from __future__ import annotations

import os
import time
import math
import logging

from typing import List

from dotenv import load_dotenv
from openai import OpenAI

from ingestion.embedder.base import BaseEmbedder

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class OpenAIEmbedder(BaseEmbedder):

    def __init__(
        self,
        model_name: str,
        batch_size: int = 50,
        max_retries: int = 3,
        sleep_seconds: int = 2
    ):
        super().__init__(model_name, batch_size)
        self.max_retries = max_retries
        self.sleep_seconds = sleep_seconds

        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def provider(self):
        return "OpenAI"
    
    def dimension(self):
        if self.model_name=='text-embedding-3-small':
            return 1536
        elif self.model_name=='text-embedding-3-large':
            return 3072
        return -1
    
    def embed_query(self, query):
        result=self.client.embeddings.create(
            model=self.model_name,
            input=[query]
        )
        return result.data[0].embedding if result.data else None
    
    def _embed_with_retry(self, batch):
        for attempt in range(1, self.max_retries + 1):
            try:
                result = self.client.embeddings.create(
                    model=self.model_name,
                    input=batch
                )
                return [item.embedding for item in result.data]
            except Exception as e:
                logger.warning(
                    f"Embedding batch failed on attempt {attempt}/{self.max_retries}: {e}"
                )
                if attempt == self.max_retries:
                    logger.error("Max retries reached. Embedding failed.")
                else:
                    time.sleep(self.sleep_seconds)

    def embed_texts(self, texts):
        if not texts:
            return []
        vectors = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_vectors = self._embed_with_retry(batch)
            vectors.extend(batch_vectors)
        
        return vectors