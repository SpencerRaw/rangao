"""Crossref API paper discovery.

Fetches papers from specific journals filtered by keywords and date range.
Port of the proven fetch_carbon_dots_multi.py logic.
"""

from __future__ import annotations

import csv
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

from ..config import get_config
from ..models import Paper


def search_crossref(
    issn: str,
    query: str,
    days_back: int = 10,
    journal_name: str = "",
    rows_per_page: int = 100,
) -> list[dict]:
    """Search Crossref for papers matching query in a journal.

    Returns raw paper dicts with keys: title, doi, published_date, authors, url, journal.
    """
    config = get_config()
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    base_url = config.crossref_base_url + "/works"
    papers: list[dict] = []
    cursor = "*"
    page = 0

    while True:
        params = {
            "filter": f"issn:{issn},from-pub-date:{start_date}",
            "query": query,
            "rows": rows_per_page,
            "cursor": cursor,
        }
        resp = requests.get(base_url, params=params, timeout=30)
        if resp.status_code != 200:
            break

        data = resp.json()
        items = data.get("message", {}).get("items", [])
        if not items:
            break

        for item in items:
            title_list = item.get("title", [])
            title = title_list[0] if title_list else "N/A"
            doi = item.get("DOI", "N/A")
            published = item.get("published-print", {}).get("date-parts", [[]])[0]
            published_str = "-".join(str(y) for y in published) if published else "N/A"

            authors_list = item.get("author", [])
            author_names = []
            for a in authors_list[:3]:
                family = a.get("family", "")
                given = a.get("given", "")
                author_names.append(f"{given} {family}".strip())
            authors = "; ".join(author_names)
            if len(authors_list) > 3:
                authors += "; et al."

            url = item.get("URL", f"https://doi.org/{doi}" if doi != "N/A" else "N/A")

            papers.append({
                "title": title,
                "doi": doi,
                "published_date": published_str,
                "authors": authors,
                "url": url,
                "journal": journal_name,
            })

        next_cursor = data.get("message", {}).get("next-cursor")
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
        page += 1
        time.sleep(1.5)

    return papers


def fetch_papers_by_journal(
    journals: list[tuple[str, str]],
    keywords: list[str],
    days_back: int = 10,
    output_csv: Optional[str] = None,
) -> list[Paper]:
    """Fetch papers from multiple journals × keywords.

    Args:
        journals: List of (name, issn) tuples.
        keywords: List of search keywords (OR logic).
        days_back: How many days back to search.
        output_csv: Optional path to save CSV.

    Returns:
        List of Paper objects.
    """
    all_raw: list[dict] = []

    for journal_name, issn in journals:
        for kw in keywords:
            papers = search_crossref(issn, kw, days_back, journal_name)
            all_raw.extend(papers)
            time.sleep(1.5)

    # Deduplicate by DOI
    seen: set[str] = set()
    unique: list[dict] = []
    for p in all_raw:
        if p["doi"] not in seen and p["doi"] != "N/A":
            seen.add(p["doi"])
            unique.append(p)

    papers = [
        Paper(
            title=p["title"],
            doi=p["doi"],
            authors=p["authors"],
            journal=p["journal"],
            published_date=p["published_date"],
            url=p["url"],
        )
        for p in unique
    ]

    if output_csv:
        _save_csv(papers, output_csv)

    return papers


def _save_csv(papers: list[Paper], path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "doi", "published_date", "authors", "url", "journal"])
        writer.writeheader()
        for p in papers:
            writer.writerow({
                "title": p.title,
                "doi": p.doi,
                "published_date": p.published_date,
                "authors": p.authors,
                "url": p.url,
                "journal": p.journal,
            })
