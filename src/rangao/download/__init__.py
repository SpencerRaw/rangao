"""Paper download — acquire PDFs via Sci-Hub, Unpaywall, or direct URLs.

Multi-mirror Sci-Hub with health-check rotation for maximum availability.
"""

from .scihub import download_via_scihub, refresh_mirrors, get_mirror_status
from .direct import download_direct, download_from_doi
from .doi_fetcher import (
    fetch_paper_metadata,
    fetch_and_download,
    fetch_latest_from_journal,
    fetch_citing_papers,
)

__all__ = [
    "download_via_scihub",
    "refresh_mirrors",
    "get_mirror_status",
    "download_direct",
    "download_from_doi",
    "fetch_paper_metadata",
    "fetch_and_download",
    "fetch_latest_from_journal",
    "fetch_citing_papers",
]
