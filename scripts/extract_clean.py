
from bs4 import BeautifulSoup
import trafilatura
from pathlib import Path
from datetime import datetime
import pandas as pd
from path import REGISTRY_DIR, LOG_DIR, CLEANED_DIR
from log_error import log_error
import re


# documents.csv
csv_path=REGISTRY_DIR / "documents.csv"
log_path=LOG_DIR / f"extract_{datetime.now().strftime('%Y-%m-%d')}.csv"

# Registry of known CMS patterns → how to normalize them before extraction
# Each handler receives the soup object and mutates it in place.

import json

def _normalize_columbia(soup):
    # 1. Reconstruct Angular-rendered tables from their JSON data attribute
    for wrapper in soup.find_all(attrs={'table-field': True}):
        try:
            headers = json.loads(wrapper.get('header', '[]'))
            rows = json.loads(wrapper.get('rows', '[]'))
        except (json.JSONDecodeError, TypeError):
            continue

        table = soup.new_tag('table')

        header_texts = [
            BeautifulSoup(h.get('data', ''), 'html.parser').get_text(strip=True)
            for h in headers
        ]
        if any(header_texts):
            thead = soup.new_tag('thead')
            tr = soup.new_tag('tr')
            for text in header_texts:
                th = soup.new_tag('th')
                th.string = text
                tr.append(th)
            thead.append(tr)
            table.append(thead)

        tbody = soup.new_tag('tbody')
        for row in rows:
            tr = soup.new_tag('tr')
            for cell in row:
                td = soup.new_tag('td')
                td.string = BeautifulSoup(
                    cell.get('data', ''), 'html.parser'
                ).get_text(strip=True)
                tr.append(td)
            tbody.append(tr)
        table.append(tbody)

        wrapper.replace_with(table)

    # 2. Unhide accordion panels (display:none)
    for tag in soup.find_all(style=re.compile(r'display\s*:\s*none', re.I)):
        tag['style'] = re.sub(r'display\s*:\s*none\s*;?', '', tag['style'], flags=re.I).strip()
        if not tag['style']:
            del tag['style']

    # 3. Promote accordion buttons → semantic headings
    for btn in soup.find_all('button', class_='accordion'):
        h = btn.find(['h2', 'h3', 'h4', 'strong'])
        text = h.get_text(strip=True) if h else btn.get_text(strip=True)
        new_tag = soup.new_tag('h3')
        new_tag.string = text
        btn.replace_with(new_tag)


def _normalize_berkeley(soup):
    """Berkeley/OpenBerkeley: collapsible sections with controller+target divs.
    Content is already visible; just ensure headings are preserved."""
    # openberkeley-collapsible-controller is already an h2/h3, nothing to do.
    # Remove the expand/collapse toggle links (noise)
    for a in soup.find_all('a', class_=re.compile(r'openberkeley-collapsible-(collapse|expand)')):
        a.decompose()


def _normalize_tabs(soup):
    """Generic tab pattern (e.g. NJIT): <nav class='tabbed-nav'> for labels,
    <div class='tab-content' rel='tab-N'> for panels.
    Inject tab label as a heading before each panel so trafilatura sees it."""
    nav = soup.find(class_='tabbed-nav')
    if not nav:
        return

    # Collect ordered tab labels from the nav
    labels = []
    for el in nav.find_all(['a', 'li', 'button', 'span']):
        text = el.get_text(strip=True)
        if text and text not in labels:
            labels.append(text)

    # Match labels to tab-content panels by order (rel="tab-0", "tab-1", ...)
    panels = soup.find_all(class_='tab-content')
    for i, panel in enumerate(panels):
        if i < len(labels):
            heading = soup.new_tag('h2')
            heading.string = labels[i]
            panel.insert(0, heading)

    # Remove the nav itself so it doesn't produce duplicate text
    nav.decompose()


def _normalize_njit(soup):
    """NJIT: two issues to fix:
    1. Content is inside .sidebar-content — the sidebar nav must be stripped
       so trafilatura doesn't score nav text against real content.
    2. Tabbed panels: trafilatura picks only the largest tab (by text density)
       and drops the rest. Fix by injecting each tab's label as an <h2>
       so all panels are treated as content sections, not competing candidates.
    """
    # 1. Remove the sidebar nav — keep only sidebar-content
    sidebar_nav = soup.find(class_='sidebar-first')
    if sidebar_nav:
        sidebar_nav.decompose()

    # 2. Inject tab labels as headings before each panel
    tabbed = soup.find(class_='tabbed-content')
    if not tabbed:
        return

    nav = tabbed.find(class_='tabbed-nav')
    if not nav:
        return

    # Collect ordered labels from the nav
    labels = []
    for el in nav.find_all(['a', 'li', 'button', 'span']):
        text = el.get_text(strip=True)
        if text and text not in labels:
            labels.append(text)

    # Pair each label with its tab-content panel by position
    panels = tabbed.find_all(class_='tab-content')
    for i, panel in enumerate(panels):
        if i < len(labels):
            heading = soup.new_tag('h2')
            heading.string = labels[i]
            panel.insert(0, heading)

    # Remove the nav itself to avoid duplicate label text
    nav.decompose()


def _detect_and_normalize(soup):
    if soup.find(class_=re.compile(r'paragraph--type--cu-')):
        _normalize_columbia(soup)

    if soup.find(class_=re.compile(r'openberkeley-collapsible')):
        _normalize_berkeley(soup)

    # NJIT detection: has both sidebar-content and tabbed-content
    if soup.find(class_='sidebar-content') and soup.find(class_='tabbed-content'):
        _normalize_njit(soup)
    # Pages with tabs but no sidebar (other CMSs)
    elif soup.find(class_='tabbed-content'):
        _normalize_tabs(soup)

    for tag in soup.find_all(attrs={'aria-hidden': 'true'}):
        del tag['aria-hidden']


def extract_content(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Remove universal boilerplate
    for tag in soup.select(
        'header, nav, footer, script, style, noscript, '
        '.menu, .navigation, #site-nav-wrapper, #utility-menu, '
        '.header-wrapper, .accordion-checkboxes, .cu-privacy-notice, '
        '.breadcrumb, .sr-only, .visible-xs-block'
    ):
        tag.decompose()

    # Normalize CMS-specific interactive widgets
    _detect_and_normalize(soup)

    # Extract main content area
    # main = (
    #     soup.find('main') or
    #     soup.find('article') or
    #     soup.select_one('#main-content, .main-content, #content, .content') or
    #     soup.body
    # )

    extracted = trafilatura.extract(
        str(soup),
        output_format='markdown',
        include_links=True,
        include_tables=True,
        include_images=False,
        no_fallback=False,
    )
    return extracted


# get the path of the raw html files
df=pd.read_csv(csv_path)

# iterate through the raw html files, extract the main content, 
# and save it to a new file in the cleaned directory. 
# also update the registry with the path to the cleaned file and the last updated timestamp.
for index, row in df.iterrows():
    raw_path=row['filepath_raw']

    clean_dir=CLEANED_DIR / row['source_type']
    clean_dir.mkdir(parents=True, exist_ok=True)
    clean_path=clean_dir / Path(raw_path).with_suffix('.md').name
    
    try:
        html=Path(raw_path).read_text(encoding="utf-8")
        extracted=extract_content(html)

        if extracted:
            clean_path.write_text(extracted, encoding="utf-8")
            df.loc[index,'filepath_cleaned']=str(clean_path)
            df.loc[index,'last_updated']=datetime.now().isoformat()
        else:
            log_error(log_path, raw_path, ValueError("No content extracted"))
    except Exception as e:
        log_error(log_path, raw_path, e)

df.to_csv(REGISTRY_DIR / "documents.csv", index=False, encoding="utf-8")