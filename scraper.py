"""
scraper.py  —  Generic program page scraper
Works for ANY college program URL — auto-discovers sub-pages.
Usage:
    python scraper.py https://mastersunion.org/pgp-in-applied-ai-and-agentic-systems
    python scraper.py https://someother.edu/some-program
"""

import asyncio
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright

OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:

    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped or len(stripped) < 3:
            cleaned.append("")
            continue
        if re.match(r'^https?://', stripped) and len(stripped) < 120:
            continue
        cleaned.append(stripped)
    return "\n".join(cleaned).strip()


def get_program_links(all_links: list, base_url: str) -> list:
    base_parsed = urlparse(base_url)
    base_domain  = base_parsed.netloc
    base_path    = base_parsed.path.rstrip("/")

    seen   = set([base_url])
    result = []

    for link in all_links:
        if not link or link.startswith("#"):
            continue
        full = urljoin(base_url, link)
        parsed = urlparse(full)

        if parsed.netloc != base_domain:
            continue
        if not parsed.path.startswith(base_path):
            continue
        clean = full.split("#")[0].rstrip("/")
        if clean in seen:
            continue

        seen.add(clean)
        result.append(clean)

    return result


async def scrape_page(page, url: str) -> str:
    print(f"  Scraping: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(10)

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)

        try:
            expanders = await page.query_selector_all(
                "button[aria-expanded='false'], .accordion-header, "
                ".expand-btn, [data-toggle='collapse'], details summary"
            )
            for btn in expanders[:30]:
                try:
                    await btn.click(timeout=1000)
                    await asyncio.sleep(0.4)
                except Exception:
                    pass
        except Exception:
            pass

        content = await page.evaluate("""
            () => {
                const remove = [
                    'nav', 'header', 'footer', '.navbar', '.nav',
                    '.preloader', '.loader', 'script', 'style',
                    '[class*="menu"]', '[class*="modal"]',
                    '[class*="cookie"]', '[class*="popup"]',
                    'noscript', 'iframe'
                ];
                remove.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => el.remove());
                });
                return document.body.innerText;
            }
        """)
        return clean_text(content)

    except Exception as e:
        print(f"    ERROR: {e}")
        return ""


async def discover_links(page, base_url: str) -> list:
    print(f"Discovering sub-pages from: {base_url}")
    await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(5)

    raw_links = await page.evaluate("""
        () => Array.from(document.querySelectorAll('a[href]'))
                   .map(a => a.getAttribute('href'))
    """)

    links = get_program_links(raw_links, base_url)
    print(f"  Found {len(links)} sub-pages:")
    for l in links:
        print(f"    {l}")
    return links


async def scrape_all(base_url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        sub_pages = await discover_links(page, base_url)
        all_pages = [base_url] + sub_pages

        all_text_parts = []

        for url in all_pages:
            slug = urlparse(url).path.strip("/").split("/")[-1] or "home"
            text = await scrape_page(page, url)

            if text:
                out_path = OUTPUT_DIR / f"{slug}.txt"
                out_path.write_text(text, encoding="utf-8")
                print(f"    Saved {len(text)} chars -> {out_path}")
                all_text_parts.append(
                    f"\n\n{'='*60}\nSOURCE: {slug.upper()} ({url})\n{'='*60}\n\n{text}"
                )
            else:
                print(f"    Skipped (empty): {url}")

        await browser.close()

        if not all_text_parts:
            print("\nNo content scraped. The site may be fully dynamic.")
            return

        combined = "\n".join(all_text_parts)
        combined_path = OUTPUT_DIR / "combined_corpus.txt"
        combined_path.write_text(combined, encoding="utf-8")
        print(f"\nDone! Combined corpus: {combined_path} ({len(combined):,} chars)")
        print(f"Pages scraped: {len(all_text_parts)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        url = "https://mastersunion.org/pgp-in-applied-ai-and-agentic-systems"
        print(f"No URL provided. Using default: {url}")
        print("Tip: python scraper.py <any-program-url>")
    else:
        url = sys.argv[1].strip()

    print(f"\nStarting scraper for: {url}\n")
    asyncio.run(scrape_all(url))