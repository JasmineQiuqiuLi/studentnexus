import pandas as pd

df = pd.read_csv("data/registry/documents.csv", sep="\t")
df.to_csv("data/registry/documents.csv", index=False, encoding="utf-8")