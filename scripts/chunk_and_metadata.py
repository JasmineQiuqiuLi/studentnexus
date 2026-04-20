import re
import pandas as pd
from pathlib import Path
from path import REGISTRY_DIR, LOG_DIR, CHUNKED_DIR, PROCESSED_DIR,DATA_DIR
from log_error import log_error
from datetime import datetime

# -----------------------------
# paths
# -----------------------------
csv_path=REGISTRY_DIR / "documents.csv"
chunks_output=CHUNKED_DIR / "chunks.csv"
chunks_output.parent.mkdir(parents=True, exist_ok=True)
log_path=LOG_DIR / f"chunk_and_metadata_{datetime.now().strftime('%Y-%m-%d')}.csv"

# -----------------------------
# load registry
# -----------------------------
df=pd.read_csv(csv_path)
chunks=[]

# -----------------------------
# split markdown by headings
# keeps headings in each block
# -----------------------------
def split_markdown(md_text):
    pattern = r'(?=^#{1,6}\s.+$)'
    parts = re.split(pattern, md_text, flags=re.MULTILINE)
    return [p.strip() for p in parts if p.strip()]

# -----------------------------
# parse heading level + title
# -----------------------------
def parse_heading(line):
    match = re.match(r'^(#{1,6})\s+(.*)', line.strip())
    if match:
        level = len(match.group(1))
        title = match.group(2).strip()
        return level, title
    return None, None

# -----------------------------
# Split large text blocks
# ------------------------------
def split_large_body_overlap(text, max_words=500, overlap=100):
    words = text.split()

    chunks = []
    start = 0

    while start < len(words):
        end = start + max_words
        chunk_words = words[start:end]

        chunks.append(" ".join(chunk_words))

        if end >= len(words):
            break

        start = end - overlap

    return chunks





# -----------------------------
# chunk each document
# -----------------------------
for _, row in df.iterrows():

    processed_value = row["filepath_processed"]

    if pd.isna(processed_value):
        continue

    processed_path = Path(processed_value)

    if not processed_path.exists():
        continue

    md_text = processed_path.read_text(encoding="utf-8")

    sections = split_markdown(md_text)

    # heading stack:
    # headings[0] = h1
    # headings[1] = h2
    # ...
    headings = [None] * 6

    chunk_num = 0

    for sec in sections:

        lines = sec.splitlines()
        first = lines[0].strip()

        level, title = parse_heading(first)

        # -------------------------
        # if section starts with heading
        # -------------------------
        if level:

            # update current heading level
            headings[level - 1] = title

            # clear lower levels
            for i in range(level, 6):
                headings[i] = None

            # build full path title
            section_title = " > ".join(
                h for h in headings if h
            )

            body = "\n".join(lines[1:]).strip()

        else:
            # no heading found
            section_title = row["title"]
            body = sec.strip()

        # skip empty body chunks
        if not body:
            continue

        sub_bodies = split_large_body_overlap(
            body,
            max_words=500,
            overlap=100
        )

        for sub in sub_bodies:

            chunk_num += 1

            chunks.append({
                "chunk_id": f"{row['doc_id']}_{chunk_num:03}",
                "doc_id": row["doc_id"],
                "title": row["title"],
                "topic": row["topic"],
                "url": row["url"],
                "source_type": row["source_type"],
                "source_name": row["source_name"],
                "section": section_title,
                "chunk_order": chunk_num,
                "last_edited": row["last_edited"],
                "retrieved": row["retrieved"],
                "chunk_text": sub
            })

# -----------------------------
# save chunks
# -----------------------------
chunk_df = pd.DataFrame(chunks)
chunk_df.to_csv(chunks_output, index=False, encoding="utf-8")

print(f"Saved {len(chunk_df)} chunks to {chunks_output}")