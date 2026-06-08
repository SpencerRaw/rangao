"""Paper discovery — find papers via Crossref API and web scraping."""

from .crossref import search_crossref, fetch_papers_by_journal
from .filter import ai_filter_papers, deduplicate_by_doi, is_research_article

__all__ = [
    "search_crossref",
    "fetch_papers_by_journal",
    "ai_filter_papers",
    "deduplicate_by_doi",
    "is_research_article",
]
