import json
from openai import OpenAI


class LLMClient:
    def __init__(self):
        self.client = OpenAI()

    def call(
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
                    "content": (
                        "You are a grounded student visa assistant. "
                        "Always return clean JSON when requested."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content.strip()

    def parse_json(self, raw_output: str) -> dict:
        """
        Safely parse structured LLM JSON output.
        """

        try:
            parsed = json.loads(raw_output)

            answer = parsed.get("answer", "")
            sources = parsed.get("sources", [])
            highlights = parsed.get("highlights", {})

            if not isinstance(sources, list):
                sources = []

            if not isinstance(highlights, dict):
                highlights = {}

            return {
                "answer": answer,
                "sources": sources,
                "highlights": highlights
            }

        except Exception:
            return {
                "answer": raw_output,
                "sources": [],
                "highlights": {}
            }