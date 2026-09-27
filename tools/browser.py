"""Zero-dependency web scraping & browser automation engine using httpx and stdlib."""

import re
import html
import httpx
from urllib.parse import quote_plus

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def scrape_url(url: str, max_chars: int = 3000) -> str:
    """Scrapes raw web page and extracts readable text without heavy headless browser overhead."""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True, headers=HEADERS) as client:
            resp = client.get(url)
            resp.raise_for_status()
            text = resp.text
    except Exception as e:
        return f"[SCRAPE ERROR] {e}"

    # Strip scripts, styles, and tags
    text = re.sub(r'<(script|style).*?>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    clean = re.sub(r'\s+', ' ', text).strip()
    return clean[:max_chars] if clean else "[Empty page content]"

def search_web(query: str, max_results: int = 3) -> str:
    """Searches the live web via DuckDuckGo HTML without requiring API keys."""
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True, headers=HEADERS) as client:
            resp = client.post(url, data={"q": query})
            resp.raise_for_status()
            raw = resp.text
    except Exception as e:
        return f"[SEARCH ERROR] {e}"

    # Extract result snippets
    results = []
    snippets = re.findall(r'<a class="result__snippet[^"]*".*?>(.*?)</a>', raw, re.DOTALL)
    titles = re.findall(r'<a class="result__url[^"]*" href="([^"]+)".*?>(.*?)</a>', raw, re.DOTALL)
    
    for i in range(min(max_results, len(snippets))):
        snippet = html.unescape(re.sub(r'<[^>]+>', '', snippets[i])).strip()
        link = titles[i][0] if i < len(titles) else "N/A"
        results.append(f"{i+1}. {snippet}\n   Link: {link}")

    return "\n\n".join(results) if results else "[No search results found]"
