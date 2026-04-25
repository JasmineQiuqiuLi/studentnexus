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

    def generate(
        self,
        query: str,
        strategy: str = "hybrid_rerank",
        embedding_model: str = "openai-small",
        llm_model: str = "gpt-4o-mini",
        top_k: int = 5
    ):

        chunks = self.retrieve_context(
            query=query,
            strategy=strategy,
            model_name=embedding_model,
            top_k=top_k
        )

        all_sources = build_sources(chunks)

        context = format_context(all_sources)

        prompt = build_prompt(
            query=query,
            context=context
        )

        raw_output = self.llm.call(
            prompt=prompt,
            model=llm_model
        )

        parsed = self.llm.parse_json(raw_output)

        answer = parsed["answer"]
        used_ids = parsed["sources"]

        final_sources = filter_sources(
            all_sources=all_sources,
            used_ids=used_ids
        )

        return {
            "query": query,
            "strategy": strategy,
            "answer": answer,
            "sources": final_sources
        }