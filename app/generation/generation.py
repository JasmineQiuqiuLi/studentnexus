"""
Purpose: Convert user query + retrieved chunks into grounded answers
Flow: 
    1. user query
    2. retrieval layer (dense/hybrid/rerank)
    3. build prompt
    4. llm generation
    5. output final answer
"""
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from app.retrieval.search_pipeline import SearchPipeline
from ingestion.embedder.factory import get_embedder

load_dotenv()

class GenerationPipeline:
    def __init__(self):
        self.search_pipeline=SearchPipeline()
        self.client=OpenAI()

    def retrieve_context(
        self,
        query:str,
        strategy:str='hybrid_rerank',
        model_name:str='openai-small',
        top_k: int=5
    )-> List[Dict[str,Any]]:
        
        # create embedding vector
        embedder=get_embedder(model_name)
        query_vector=embedder.embed_query(query)

        # run retrieval pipeline
        results=self.search_pipeline.search(
            strategy=strategy,
            query_text=query,
            query_vector=query_vector,
            model_name=model_name,
            top_k=top_k
        )
        return results
    
    def format_context(self, chunks:List[Dict[str,Any]]) -> str:
        context_parts=[]
        for i, chunk in enumerate(chunks,start=1):
            text=chunk.get("chunk_text","")
            doc_id=chunk.get("doc_id","unknow_doc")
            rank=chunk.get("rank",i)
            block=f"""
                [source {i}]
                rank: {rank}
                Document: {doc_id}
                Content: {text}
            """
            context_parts.append(block.strip())
        return "\n\n".join(context_parts)
    
    def build_prompt(self,query:str,context:str) -> str:
        prompt=f"""
            You are StudentNexus AI Assistant.
            You help university students answer F1/OPT/CPT/H1b-related visa questions.
            Use ONLY the provided context.
            Rules:
                1. If answer is in context, answer clearly.
                2. If partial info exists, mention limitations.
                3. If missing, say you are unsure.
                4. Do NOT invent policies.
                5. Cite sources like (Source 1).
            Context:
                {context}
            Student Question:
                {query}
            Answer:
        """
        return prompt.strip()
    
    def call_llm(
            self,
            prompt:str,
            model:str='gpt-4o-mini',
            temperature:float=0.2
    ) -> str:
        response=self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {
                    "role":"system",
                    "content":"You are a grounded education support assistant on student visa"
                },
                {
                    "role":"user",
                    "content":prompt
                }
            ]
        )
        return response.choices[0].message.content.strip()
    
    def generate(
        self,
        query:str,
        strategy:str='hybrid_rerank',
        embedding_model:str='openai-small',
        llm_model:str='gpt-4o-mini',
        top_k: int=5
    ) -> Dict[str,Any]:
        
        # retrieve
        chunks=self.retrieve_context(
            query=query,
            strategy=strategy,
            model_name=embedding_model,
            top_k=top_k
        )
        # format context
        context=self.format_context(chunks)

        # build prompt
        prompt=self.build_prompt(query=query,context=context)

        # generate answer
        answer=self.call_llm(
            prompt=prompt,
            model=llm_model
        )

        return {
            "query":query,
            "strategy":strategy,
            "retrieved_chunks":chunks,
            "answer": answer
        }


# =======================
# CLI Testing
# =======================

if __name__=="__main__":
    pipeline=GenerationPipeline()

    while True:
        query=input("\nAsk StudentNexus > ")

        if query.lower() in ["exit", "quit"]:
            break

        result = pipeline.generate(
            query=query,
            strategy="hybrid_rerank",
            top_k=5
        )

        print("\n==============================")
        print("FINAL ANSWER")
        print("==============================")
        print(result["answer"])

        print("\n==============================")
        print("RETRIEVED CHUNKS")
        print("==============================")

        for item in result["retrieved_chunks"]:
            print(f"[Rank {item['rank']}] {item['chunk_text'][:200]}")