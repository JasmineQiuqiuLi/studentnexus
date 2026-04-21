# ingestion/embedder.py
# Unified embedding architecture:
# - BaseEmbedder (interface)
# - OpenAIEmbedder
# - LocalHFEmbedder

from __future__ import annotations

import os
import time
import math
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dotenv import load_dotenv

from openai import OpenAI
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")

class BaseEmbedder(ABC):
    def __init__(self, model:str=None, batch_size: int=50, max_retries: int=5, sleep_seconds: float=2.0):
        self.model=model
        self.batch_size=batch_size
        self.max_retries=max_retries
        self.sleep_seconds=sleep_seconds
    
    @abstractmethod
    def embed_query(self, query:str) -> List[float]:
        pass
    @abstractmethod
    def embed_texts(self, batch:List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def provider(self) -> str:
        pass

    @abstractmethod
    def dimensions(self) -> int:
        pass

