import json


def parse_metadata(chunk: dict) -> dict:
    metadata = chunk.get("metadata", {})

    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {}

    return metadata


def build_sources(chunks: list) -> list:
    sources = []

    for i, chunk in enumerate(chunks, start=1):
        metadata = parse_metadata(chunk)

        sources.append({
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
        })

    return sources


def filter_sources(all_sources: list, used_ids: list) -> list:
    if not used_ids:
        return all_sources[:2]

    return [
        s for s in all_sources
        if s["source_id"] in used_ids
    ]