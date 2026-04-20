from path import REGISTRY_DIR, LOG_DIR, PROCESSED_DIR, CLEANED_DIR
from log_error import log_error
import pandas as pd
from datetime import datetime
import re
from pathlib import Path

csv_path=REGISTRY_DIR / "documents.csv"
log_path=LOG_DIR / f"process_cleaned_{datetime.now().strftime('%Y-%m-%d')}.csv"



def replace_markdown_tables(md_text):
    pattern = r'(\|.+\|\n\|[-| ]+\|\n(?:\|.*\|\n?)*)'

    tables = re.findall(pattern, md_text)

    for table in tables:
        plain = markdown_table_to_text(table)
        md_text = md_text.replace(table, plain)

    return md_text


def markdown_table_to_text(table_text):
    lines = [line.strip() for line in table_text.strip().splitlines()]

    headers = [x.strip() for x in lines[0].strip("|").split("|")]
    rows = lines[2:]   # skip separator row

    output = []

    for row in rows:
        cells = [x.strip() for x in row.strip("|").split("|")]

        parts = []
        for h, c in zip(headers, cells):
            parts.append(f"{h}: {c}")

        output.append("- " + " | ".join(parts))

    return "\n".join(output) + "\n"

# 
df=pd.read_csv(csv_path)
for index, row in df.iterrows():
    cleaned_path_value=row['filepath_cleaned']

    if pd.isna(cleaned_path_value):
        continue

    cleaned_path=Path(cleaned_path_value)

    try:
        md_text=cleaned_path.read_text(encoding='utf-8')
        md_text=replace_markdown_tables(md_text)
        relative_path = cleaned_path.relative_to(CLEANED_DIR)
        processed_path = PROCESSED_DIR / relative_path
        processed_path.parent.mkdir(parents=True, exist_ok=True)
        processed_path.write_text(md_text, encoding='utf-8')
        df.loc[index,'filepath_processed']=str(processed_path)
    except Exception as e:
        log_error(log_path, row['url'], e)

df.to_csv(REGISTRY_DIR / "documents.csv", index=False, encoding="utf-8")