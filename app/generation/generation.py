"""
generation.py

Purpose:
    StudentNexus Generation Layer

Flow:
    1. User query
    2. Retrieve chunks
    3. Build grounded prompt
    4. Ask LLM for structured JSON response
    5. Return only cited sources

LLM Output Format:
{
  "answer": "...",
  "sources": [1, 3]
}
"""

import json
from typing import List, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

from app.retrieval.search_pipeline import SearchPipeline
from ingestion.embedder.factory import get_embedder

load_dotenv()


class GenerationPipeline:
    def __init__(self):
        self.search_pipeline = SearchPipeline()
        self.client = OpenAI()

    # ==================================================
    # Retrieval
    # ==================================================
    def retrieve_context(
        self,
        query: str,
        strategy: str = "hybrid_rerank",
        model_name: str = "openai-small",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:

        embedder = get_embedder(model_name)
        query_vector = embedder.embed_query(query)

        results = self.search_pipeline.search(
            strategy=strategy,
            query_text=query,
            query_vector=query_vector,
            model_name=model_name,
            top_k=top_k
        )

        return results

    # ==================================================
    # Metadata Utilities
    # ==================================================
    def parse_metadata(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        metadata = chunk.get("metadata", {})

        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}

        return metadata

    def build_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build frontend-ready sources.
        Each source gets source_id = 1..N
        """

        sources = []

        for i, chunk in enumerate(chunks, start=1):
            metadata = self.parse_metadata(chunk)

            source = {
                "source_id": i,
                "rank": chunk.get("rank", i),
                "chunk_id": chunk.get("chunk_id"),
                "doc_id": chunk.get("doc_id"),

                "title": metadata.get("title", f"Source {i}"),
                "url": metadata.get("url"),
                "section": metadata.get("section"),
                "last_edited": metadata.get("last_edited"),
                "retrieved": metadata.get("retrieved"),

                "chunk_text": chunk.get("chunk_text", "")
            }

            sources.append(source)

        return sources

    # ==================================================
    # Prompt Context
    # ==================================================
    def format_context(self, sources: List[Dict[str, Any]]) -> str:
        """
        Use only helpful metadata inside prompt.
        """

        context_parts = []

        for source in sources:
            block = f"""
[Source {source["source_id"]}]
Title: {source["title"]}
Section: {source["section"]}
Last Updated: {source["last_edited"]}

Content:
{source["chunk_text"]}
"""
            context_parts.append(block.strip())

        return "\n\n".join(context_parts)

    # ==================================================
    # Prompt
    # ==================================================
    def build_prompt(self, query: str, context: str) -> str:

        return f"""
You are StudentNexus AI Assistant.

You help university students answer F1 / OPT / CPT / H1B related visa questions.

Use ONLY the provided context.

Rules:
1. If answer exists, answer clearly.
2. If partial information exists, explain limits.
3. If unsure, say uncertainty clearly.
4. Do NOT invent policies.
5. Select ONLY sources that directly support the final answer.

Return ONLY valid JSON.

Format:
{{
  "answer": "your final answer",
  "sources": [1,2]
}}

Context:
{context}

Student Question:
{query}
""".strip()

    # ==================================================
    # LLM Call
    # ==================================================
    def call_llm(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2
    ) -> str:

        response = self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": "You are a grounded student visa assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content.strip()

    # ==================================================
    # Parse JSON Output
    # ==================================================
    def parse_llm_json(self, raw_output: str) -> Dict[str, Any]:
        """
        Safely parse model JSON output.
        """

        try:
            parsed = json.loads(raw_output)

            answer = parsed.get("answer", "")
            source_ids = parsed.get("sources", [])

            if not isinstance(source_ids, list):
                source_ids = []

            return {
                "answer": answer,
                "sources": source_ids
            }

        except Exception:
            # fallback if model returns plain text
            return {
                "answer": raw_output,
                "sources": []
            }

    # ==================================================
    # Filter Sources
    # ==================================================
    def filter_sources(
        self,
        all_sources: List[Dict[str, Any]],
        used_ids: List[int]
    ) -> List[Dict[str, Any]]:

        if not used_ids:
            # fallback: top 2 sources
            return all_sources[:2]

        return [
            source
            for source in all_sources
            if source["source_id"] in used_ids
        ]

    # ==================================================
    # Main Pipeline
    # ==================================================
    def generate(
        self,
        query: str,
        strategy: str = "hybrid_rerank",
        embedding_model: str = "openai-small",
        llm_model: str = "gpt-4o-mini",
        top_k: int = 5
    ) -> Dict[str, Any]:

        # 1. Retrieve
        chunks = self.retrieve_context(
            query=query,
            strategy=strategy,
            model_name=embedding_model,
            top_k=top_k
        )

        # 2. Build frontend sources
        all_sources = self.build_sources(chunks)

        # 3. Prompt context
        context = self.format_context(all_sources)

        # 4. Prompt
        prompt = self.build_prompt(
            query=query,
            context=context
        )

        # 5. LLM
        raw_output = self.call_llm(
            prompt=prompt,
            model=llm_model
        )

        # 6. Parse JSON
        parsed = self.parse_llm_json(raw_output)

        answer = parsed["answer"]
        used_ids = parsed["sources"]

        # 7. Only cited sources
        final_sources = self.filter_sources(
            all_sources=all_sources,
            used_ids=used_ids
        )

        return {
            "query": query,
            "strategy": strategy,
            "answer": answer,
            "sources": final_sources,

            # Optional debugging
            "used_source_ids": used_ids,
            "raw_llm_output": raw_output
        }


# ==================================================
# CLI Test
# ==================================================
if __name__ == "__main__":

    pipeline = GenerationPipeline()

    while True:
        query = input("\nAsk StudentNexus > ")

        if query.lower() in ["exit", "quit"]:
            break

        result = pipeline.generate(query=query)

        print("\n==============================")
        print("ANSWER")
        print("==============================")
        print(result["answer"])

        print("\n==============================")
        print("DISPLAY SOURCES")
        print("==============================")

        for source in result["sources"]:
            print(
                f"[{source['source_id']}] "
                f"{source['title']} | "
                f"{source['section']} | "
                f"{source['url']}"
            )