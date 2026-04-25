from pydantic import BaseModel
from typing import Optional, List


class Source(BaseModel):
    source_id: int
    rank: int
    title: Optional[str] = None
    url: Optional[str] = None
    section: Optional[str] = None
    last_edited: Optional[str] = None
    chunk_text: str


class GenerationResponse(BaseModel):
    query: str
    strategy: str
    answer: str
    sources: List[Source]