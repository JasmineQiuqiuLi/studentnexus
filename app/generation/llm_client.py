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
                    "content": "You are a grounded student visa assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content.strip()

    def parse_json(self, raw_output: str) -> dict:
        try:
            parsed = json.loads(raw_output)

            return {
                "answer": parsed.get("answer", ""),
                "sources": parsed.get("sources", [])
            }

        except:
            return {
                "answer": raw_output,
                "sources": []
            }