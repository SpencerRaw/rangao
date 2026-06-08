"""DOI paper fetcher — metadata + PDF acquisition from DOI.

Given a DOI, fetches full metadata from Crossref and downloads
the PDF through the best available channel.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from ..config import get_config
from ..models import Paper


def fetch_paper_metadata(doi: str) -> Optional[Paper]:
    """Fetch paper metadata from Crossref by DOI.

    Args:
        doi: Paper DOI.

    Returns:
        Paper object with populated metadata, or None if not found.
    """
    config = get_config()
    url = f"{config.crossref_base_url}/works/{doi}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json().get("message", {})
    except Exception:
        return None

    # Extract fields
    title_list = data.get("title", [])
    title = title_list[0] if title_list else "Unknown Title"

    authors_list = data.get("author", [])
    author_names = []
    for a in authors_list[:5]:
        family = a.get("family", "")
        given = a.get("given", "")
        author_names.append(f"{given} {family}".strip())
    authors = "; ".join(author_names)
    if len(authors_list) > 5:
        authors += "; et al."

    journal = data.get("container-title", [""])[0] or ""

    # Published date
    published_str = ""
    date_parts = data.get("published-print", {}).get("date-parts", [[]])[0]
    if not date_parts:
        date_parts = data.get("created", {}).get("date-parts", [[]])[0]
    if date_parts:
        published_str = "-".join(str(p) for p in date_parts)

    # URL
    url = data.get("URL", f"https://doi.org/{doi}")

    # Abstract
    abstract = data.get("abstract", "")

    return Paper(
        title=title,
        doi=doi,
        authors=authors,
        journal=journal,
        published_date=published_str,
        url=url,
        metadata={"abstract": abstract},
    )


def fetch_and_download(doi: str) -> Optional[Paper]:
    """Fetch metadata + download PDF for a DOI. One-stop shop.

    Args:
        doi: Paper DOI.

    Returns:
        Paper with metadata populated and pdf_path set, or None.
    """
    # Step 1: Get metadata
    paper = fetch_paper_metadata(doi)
    if paper is None:
        # Minimal paper with just the DOI
        paper = Paper(title="Unknown", doi=doi)

    # Step 2: Download PDF
    from .direct import download_from_doi

    pdf_path = download_from_doi(doi)
    if pdf_path:
        paper.pdf_path = pdf_path

    return paper


def fetch_latest_from_journal(
    issn: str,
    journal_name: str = "",
    keywords: Optional[list[str]] = None,
    days_back: int = 7,
    max_papers: int = 10,
    download_pdfs: bool = False,
) -> list[Paper]:
    """Fetch the latest papers from a journal, optionally downloading PDFs.

    A convenience wrapper that combines Crossref search + AI filtering
    + optional PDF download into one call.

    Args:
        issn: Journal ISSN (e.g., '1521-4095' for Advanced Materials).
        journal_name: Human-readable journal name.
        keywords: Optional keywords to filter by.
        days_back: How many days back to search.
        max_papers: Maximum papers to return.
        download_pdfs: If True, attempt to download each paper's PDF.

    Returns:
        List of Paper objects, sorted by publication date (newest first).
    """
    from ..discover.crossref import search_crossref
    from ..discover.filter import ai_filter_papers, deduplicate_by_doi, is_research_article

    if keywords is None:
        keywords = [""]  # empty keyword = return all

    # Collect raw results
    all_raw: list[dict] = []
    for kw in keywords:
        papers = search_crossref(issn, kw, days_back, journal_name)
        all_raw.extend(papers)
        time.sleep(1.0)

    # Deduplicate
    seen: set[str] = set()
    unique: list[dict] = []
    for p in all_raw:
        if p["doi"] not in seen and p["doi"] != "N/A":
            seen.add(p["doi"])
            unique.append(p)

    # Filter non-research articles
    unique = [p for p in unique if is_research_article(p["title"])]

    # AI filter if keywords provided
    if keywords and keywords != [""]:
        from ..discover.filter import ai_filter_papers
        papers_list = [
            Paper(title=p["title"], doi=p["doi"], authors=p["authors"],
                  journal=p["journal"], published_date=p["published_date"], url=p["url"])
            for p in unique
        ]
        papers_list = ai_filter_papers(papers_list, " ".join(keywords))
    else:
        papers_list = [
            Paper(title=p["title"], doi=p["doi"], authors=p["authors"],
                  journal=p["journal"], published_date=p["published_date"], url=p["url"])
            for p in unique
        ]

    # Sort by date (newest first) and limit
    papers_list.sort(key=lambda p: p.published_date or "", reverse=True)
    papers_list = papers_list[:max_papers]

    # Optionally download PDFs
    if download_pdfs:
        from .direct import download_from_doi
        for paper in papers_list:
            pdf = download_from_doi(paper.doi)
            if pdf:
                paper.pdf_path = pdf

    return papers_list


def fetch_citing_papers(
    doi: str,
    max_results: int = 20,
) -> list[Paper]:
    """Find papers that cite a given DOI.

    Uses OpenAlex API (free, no key required).

    Args:
        doi: The DOI of the cited paper.
        max_results: Maximum citing papers to return.

    Returns:
        List of citing Paper objects.
    """
    import urllib.parse

    encoded_doi = urllib.parse.quote(doi, safe="")
    url = f"https://api.openalex.org/works?filter=cites:{encoded_doi}&per_page={max_results}"

    try:
        resp = requests.get(url, timeout=20)
        data = resp.json()
    except Exception:
        return []

    papers: list[Paper] = []
    for item in data.get("results", []):
        title = item.get("title", "Unknown")
        item_doi = item.get("doi", "").replace("https://doi.org/", "")
        authors = "; ".join(
            a.get("author", {}).get("display_name", "")
            for a in item.get("authorships", [])[:3]
        )
        journal = item.get("primary_location", {}).get("source", {}).get("display_name", "")
        pub_date = item.get("publication_date", "")

        papers.append(Paper(
            title=title,
            doi=item_doi,
            authors=authors,
            journal=journal,
            published_date=pub_date,
            url=f"https://doi.org/{item_doi}" if item_doi else "",
        ))

    return papers
