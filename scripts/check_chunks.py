import pandas as pd

df = pd.read_csv("data/chunked/chunks.csv")

df["word_count"] = df["chunk_text"].fillna("").apply(
    lambda x: len(str(x).split())
)

print(df["word_count"].describe())

print(df[df["word_count"] > 500][
    ["chunk_id", "section", "word_count"]
].head(20))