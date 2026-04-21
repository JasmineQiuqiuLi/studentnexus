import re
import pandas as pd
from pathlib import Path
from scripts.path import REGISTRY_DIR, LOG_DIR, CHUNKED_DIR
from scripts.log_error import log_error
from datetime import datetime
import time

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

def split_large_body_smart(text, max_words=500, overlap=80, debug=False):

    def wc(s):
        return len(s.split())

    def log(msg):
        if debug:
            print(msg, flush=True)

    def split_word_window(paragraph):
        words = paragraph.split()
        out = []
        start = 0
        while start < len(words):
            end = start + max_words
            out.append(" ".join(words[start:end]))
            if end >= len(words):
                break
            start = end - overlap
        return out

    paragraphs = [
        p.strip()
        for p in re.split(r"\n\s*\n", text)
        if p.strip()
    ]

    if len(paragraphs) == 1 and wc(paragraphs[0]) > max_words:
        paragraphs = [p.strip() for p in text.splitlines() if p.strip()]

    log(f"  [split] {len(paragraphs)} paragraph(s), total words: {wc(text)}")

    chunks = []
    current_paras = []
    current_words = 0
    i = 0

    while i < len(paragraphs):
        para = paragraphs[i]
        para_words = wc(para)

        log(f"  [i={i}] para_words={para_words} | current_words={current_words} | current_paras={len(current_paras)} | chunks_so_far={len(chunks)}")

        if para_words > max_words:
            log(f"  [i={i}] → GIANT FALLBACK")
            if current_paras:
                chunks.append("\n\n".join(current_paras))
                log(f"  [i={i}] → flushed current before giant (chunk #{len(chunks)})")
                current_paras = []
                current_words = 0

            giant_parts = split_word_window(para)
            log(f"  [i={i}] → split giant into {len(giant_parts)} parts")
            chunks.extend(giant_parts)
            i += 1
            continue

        if current_words + para_words <= max_words or not current_paras:
            current_paras.append(para)
            current_words += para_words
            log(f"  [i={i}] → COMBINED (new current_words={current_words})")
            i += 1

        else:
            # flush finished chunk
            chunks.append("\n\n".join(current_paras))
            log(f"  [i={i}] → FLUSHED chunk #{len(chunks)} ({current_words} words)")

            # -----------------------------
            # build overlap paragraphs
            # -----------------------------
            overlap_paras = []
            overlap_count = 0

            for p in reversed(current_paras):
                overlap_paras.insert(0, p)
                overlap_count += wc(p)
                if overlap_count >= overlap:
                    break

            # -----------------------------
            # trim overlap so new para fits
            # -----------------------------
            while overlap_paras and (
                sum(wc(x) for x in overlap_paras) + para_words > max_words
            ):
                overlap_paras.pop(0)   # remove oldest overlap paragraph

            current_paras = overlap_paras[:]
            current_words = sum(wc(x) for x in current_paras)

            # if still cannot fit, start fresh
            if current_words + para_words > max_words:
                current_paras = []
                current_words = 0

            # add incoming paragraph
            current_paras.append(para)
            current_words += para_words

            log(f"  [i={i}] → NEW current_words={current_words}")
            i += 1

    if current_paras:
        chunks.append("\n\n".join(current_paras))
        log(f"  [final] remaining chunk #{len(chunks)} ({current_words} words)")

    log(f"  [done] total chunks: {len(chunks)}")
    return chunks


# -----------------------------
# chunk each document
# -----------------------------
total = len(df)
for idx, (_, row) in enumerate(df.iterrows(), start=1):
    doc_id = row["doc_id"]
    start = time.time()
    print(f"[{idx}/{total}] Processing {doc_id}...", flush=True)

    try:
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

            sub_bodies = split_large_body_smart(
                body,
                max_words=500,
                overlap=80,
                debug=(doc_id == "gov_010") 
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
    except Exception as e:
        elapsed = round(time.time() - start, 2)
        print(f"   FAILED after {elapsed}s: {e}")
        log_error(log_path, row["url"], e)

# -----------------------------
# save chunks
# -----------------------------
chunk_df = pd.DataFrame(chunks)
chunk_df.to_csv(chunks_output, index=False, encoding="utf-8")

print(f"Saved {len(chunk_df)} chunks to {chunks_output}")