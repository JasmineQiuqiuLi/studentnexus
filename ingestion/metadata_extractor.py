import re
from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
from scripts.path import REGISTRY_DIR, LOG_DIR
from scripts.log_error import log_error
from datetime import datetime

log_path=LOG_DIR / f"extract_metadata_{datetime.now().strftime('%Y-%m-%d')}.csv"

def extract_title(html):
    soup = BeautifulSoup(html, "html.parser")

    if soup.title:
        return soup.title.get_text(strip=True)

    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)

    return None

def extract_last_updated(html):
    soup = BeautifulSoup(html, "html.parser")

    # meta tags
    for attr in [
        ("property", "article:modified_time"),
        ("name", "last-modified"),
        ("name", "date"),
        ("name", "modified")
    ]:
        tag = soup.find("meta", attrs={attr[0]: attr[1]})
        if tag:
            return tag.get("content")

    # visible text fallback
    text = soup.get_text(" ", strip=True)

    match = re.search(
        r'(Last updated|Updated)\s*:?\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})',
        text
    )

    if match:
        return match.group(2)

    return None


df=pd.read_csv(REGISTRY_DIR / "documents.csv")
for index, row in df.iterrows():
    raw_path_value=row['filepath_raw']

    if pd.isna(raw_path_value):
        continue

    raw_path=Path(raw_path_value)

    try:
        html=raw_path.read_text(encoding='utf-8')

        title=extract_title(html)
        last_updated=extract_last_updated(html)

        df.loc[index,'title']=title
        df.loc[index,'last_edited']=last_updated

    except Exception as e:
        log_error(log_path, raw_path, e)

df.to_csv(REGISTRY_DIR / "documents.csv", index=False, encoding="utf-8")