from dotenv import load_dotenv

from app.retrieval.search_pipeline import SearchPipeline
from ingestion.embedder.factory import get_embedder

from app.generation.llm_client import LLMClient
from app.generation.prompt_builder import build_prompt, format_context
from app.generation.source_formatter import build_sources, filter_sources

load_dotenv()


class GenerationPipeline:
    def __init__(self):
        self.search_pipeline = SearchPipeline()
        self.llm = LLMClient()

    # -----------------------------------
    # Retrieval
    # -----------------------------------
    def retrieve_context(
        self,
        query: str,
        strategy: str = "hybrid_rerank",
        model_name: str = "openai-small",
        top_k: int = 5
    ):

        embedder = get_embedder(model_name)
        query_vector = embedder.embed_query(query)

        return self.search_pipeline.search(
            strategy=strategy,
            query_text=query,
            query_vector=query_vector,
            model_name=model_name,
            top_k=top_k
        )

    # -----------------------------------
    # Attach highlights to sources
    # -----------------------------------
    def add_highlights(
        self,
        sources: list,
        highlights: dict
    ) -> list:

        for source in sources:
            sid = str(source["source_id"])
            source["highlights"] = highlights.get(sid, [])

        return sources

    # -----------------------------------
    # Main Generation
    # -----------------------------------
    def generate(
        self,
        query: str,
        strategy: str = "hybrid_rerank",
        embedding_model: str = "openai-small",
        llm_model: str = "gpt-4o-mini",
        top_k: int = 5
    ):

        # 1. Retrieve chunks
        chunks = self.retrieve_context(
            query=query,
            strategy=strategy,
            model_name=embedding_model,
            top_k=top_k
        )

        # 2. Convert to sources
        all_sources = build_sources(chunks)

        # 3. Build context
        context = format_context(all_sources)

        # 4. Build prompt
        prompt = build_prompt(
            query=query,
            context=context
        )

        # 5. Call model
        raw_output = self.llm.call(
            prompt=prompt,
            model=llm_model
        )

        # 6. Parse JSON
        parsed = self.llm.parse_json(raw_output)

        answer = parsed["answer"]
        used_ids = parsed["sources"]
        highlights = parsed["highlights"]

        # 7. Keep only cited sources
        final_sources = filter_sources(
            all_sources=all_sources,
            used_ids=used_ids
        )

        # 8. Add highlight spans
        final_sources = self.add_highlights(
            sources=final_sources,
            highlights=highlights
        )

        return {
            "query": query,
            "strategy": strategy,
            "answer": answer,
            "sources": final_sources
        }