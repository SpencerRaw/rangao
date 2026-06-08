"""Paper download — acquire PDFs via Sci-Hub, Unpaywall, or direct URLs."""

from .scihub import download_via_scihub
from .direct import download_direct, download_from_doi

__all__ = [
    "download_via_scihub",
    "download_direct",
    "download_from_doi",
]
