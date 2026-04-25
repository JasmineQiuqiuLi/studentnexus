def format_context(sources: list) -> str:
    blocks = []

    for source in sources:
        block = f"""
[Source {source["source_id"]}]
Title: {source["title"]}
Section: {source["section"]}
Last Updated: {source["last_edited"]}

Content:
{source["chunk_text"]}
"""
        blocks.append(block.strip())

    return "\n\n".join(blocks)


def build_prompt(query: str, context: str) -> str:
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

Return ONLY valid JSON:

{{
  "answer": "your final answer",
  "sources": [1,2]
}}

Context:
{context}

Student Question:
{query}
""".strip()