from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class BaseEmbedder(ABC):

    def __init__(
        self,
        model_name: str,
        batch_size: int = 50
    ):
        self.model_name = model_name
        self.batch_size = batch_size

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def provider(self) -> str:
        pass

    @abstractmethod
    def dimension(self) -> int:
        pass