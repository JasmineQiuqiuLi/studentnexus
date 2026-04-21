import pandas as pd
import requests
from datetime import datetime
from scripts.path import RAW_DIR, REGISTRY_DIR, LOG_DIR
from scripts.log_error import log_error
from playwright.sync_api import sync_playwright

csv_path=REGISTRY_DIR / "documents.csv"
log_path=LOG_DIR / f"fetch_raw_{datetime.now().strftime('%Y-%m-%d')}.csv"

def download_html(url, raw_path, timeout=20):
    """
    Method 1: use requests to download the HTML content. 
    Method 2: if method 1 fails, use Playwright to render the page and get the HTML content.
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    # First try with requests
    try:
        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        html=response.text
        raw_path.write_text(html,encoding='utf-8')
        return html
    except requests.exceptions.RequestException as e:
        print(f"requests failed for {url}, trying Playwright...")

    # If requests fails, try with Playwright
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False   # important: many bot systems dislike headless
            )

            context = browser.new_context(
                user_agent=headers["User-Agent"],
                locale="en-US",
                viewport={"width": 1366, "height": 768}
            )

            page = context.new_page()

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=timeout * 1000
            )

            # wait for javascript challenge
            page.wait_for_timeout(8000)

            # wait until network mostly settles
            page.wait_for_load_state("networkidle", timeout=15000)

            html = page.content()

            # detect challenge page
            if "security verification" in html.lower():
                page.wait_for_timeout(8000)
                html = page.content()

            raw_path.write_text(html, encoding="utf-8")

            browser.close()
            return html
    except Exception as e:
        print(f"Playwright also failed for {url}")
        log_error(log_path, url, e)



df=pd.read_csv(csv_path)

for index, row in df.iterrows():
    url=row['url']
    last_part=url.split("/")[-1]
    doc_id=row['doc_id']
    source_type=row['source_type']

    raw_dir=RAW_DIR / source_type
    # cleaned_dir=CLEANED_DIR / source_type

    raw_dir.mkdir(parents=True, exist_ok=True)
    # cleaned_dir.mkdir(parents=True, exist_ok=True)

    raw_path=raw_dir / f"{doc_id}_{last_part}.html"
    # cleaned_path=cleaned_dir / f"{doc_id}_{last_part}.md"

    try:
        
        html=download_html(url, raw_path)

        # the content extraction is more complicated and will be done in a separate step, so we just save the raw HTML for now.

        #extracted=trafilatura.extract(
        #     html, 
        #     output_format='markdown',
        #     include_links=True,
        #     include_tables=True
        # )

        #if extracted:
            #cleaned_path.write_text(extracted, encoding='utf-8')
            # df.loc[index,'status']='processed'
        # else:
        #     df.loc[index,'status']='no content extracted'
        #     log_error(log_path, url, ValueError("No content extracted"))

        df.loc[index,'filepath_raw']=str(raw_path)
        # df.loc[index,'filepath_cleaned']=str(cleaned_path)
        df.loc[index,'last_updated']=datetime.now().isoformat()

    except requests.exceptions.RequestException as e:
        # Log the error with timestamp and URL
        log_error(log_path, url, e)
        continue

df.to_csv(REGISTRY_DIR / "documents.csv", index=False, encoding="utf-8")
print("Processing completed. Updated registry saved to documents.csv")


