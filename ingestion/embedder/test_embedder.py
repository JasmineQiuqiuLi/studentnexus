from ingestion.embedder.openai_embedder import OpenAIEmbedder


def main():

    emb = OpenAIEmbedder(
        model_name="text-embedding-3-small",
        batch_size=2
    )

    texts = [
        "What is machine learning?",
        "Explain vector databases."
    ]

    vecs = emb.embed_texts(texts)

    print("Provider:")
    print(emb.provider())

    print("\nModel:")
    print(emb.model_name)

    print("\nDimension:")
    print(emb.dimension())

    print("\nRows Returned:")
    print(len(vecs))

    print("\nFirst Vector (first 5 nums):")
    print(vecs[0][:5])


if __name__ == "__main__":
    main()