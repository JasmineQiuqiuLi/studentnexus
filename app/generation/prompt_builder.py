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
2. If partial information exists, explain limitations.
3. If unsure, state uncertainty clearly.
4. Do NOT invent policies.
5. Only cite sources directly supporting the answer.
6. Highlights must be exact phrases copied from source content.
7. Keep highlights short and relevant.

Return ONLY valid JSON.

Every key in "highlights" must exactly match a source listed in "sources".
Do not include highlights for unselected sources.
Every selected source must have at least one highlight.

Format:
{{
  "answer": "final answer",
  "sources": [1,2],
  "highlights": {{
    "1": ["exact phrase from Source 1"],
    "2": ["exact phrase from Source 2"]
  }}
}}

Context:
{context}

Student Question:
{query}
""".strip()