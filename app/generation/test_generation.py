from app.generation.generation import GenerationPipeline


def main():
    pipeline = GenerationPipeline()

    while True:
        query = input("\nAsk StudentNexus > ")

        if query.lower() in ["exit", "quit"]:
            break

        result = pipeline.generate(
            query=query,
            strategy="hybrid_rerank",
            top_k=5
        )

        print("\n====================")
        print("ANSWER")
        print("====================")
        print(result["answer"])

        print("\n====================")
        print("SOURCES")
        print("====================")

        for source in result["sources"]:
            print(f"[{source['source_id']}] {source['title']}")
            print(f"URL: {source['url']}")
            print(f"Section: {source['section']}")
            print(f"Preview: {source['chunk_text'][:150]}")
            print()
            print(source)


if __name__ == "__main__":
    main()