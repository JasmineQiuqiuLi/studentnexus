from __future__ import annotations

from ingestion.embedder.base import BaseEmbedder
from ingestion.embedder.local_embedder import LocalHFEmbedder
from ingestion.embedder.openai_embedder import OpenAIEmbedder


MODEL_REGISTRY = {
    "openai_small": {
        "class": OpenAIEmbedder,
        "kwargs": {
            "model_name": "text-embedding-3-small"
        }
    },
    "bge-base":{
        "class": LocalHFEmbedder,
        "kwargs": {
            "model_name": "BAAI/bge-base-en-v1.5"
        }
    },
    "bge-large":{
        "class": LocalHFEmbedder,
        "kwargs": {
            "model_name": "BAAI/bge-large-en-v1.5"
        }
    }
}

def get_embedder(name:str) -> BaseEmbedder:
    key=name.lower().strip()
    if key not in MODEL_REGISTRY:
        raise ValueError(f"Embedder '{name}' not found in registry.")
    embedder_config = MODEL_REGISTRY[key]
    return embedder_config["class"](**embedder_config["kwargs"])

def available_embedders() -> list[str]:
    return list(MODEL_REGISTRY.keys())