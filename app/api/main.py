from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.generation.generation import GenerationPipeline

app=FastAPI(
    title='StudentNexus API',
    version='0.0.1'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = GenerationPipeline()

class AskRequest(BaseModel):
    question: str
    strategy: str = "hybrid_rerank"
    top_k: int = 5

@app.get("/")
def root():
    return {"message":"Student Nexus API running"}

@app.get('/health')
def health():
    return {"status":"ok"}

@app.post("/ask")
def ask_question(payload:AskRequest):
    result=pipeline.generate(
        query=payload.question,
        strategy=payload.strategy,
        top_k=payload.top_k
    )

    # print(result)

    return result