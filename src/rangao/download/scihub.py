"""Sci-Hub PDF downloader.

Attempts to download a paper PDF from Sci-Hub mirrors.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

from ..config import get_config


def download_via_scihub(
    doi: str,
    output_dir: Optional[Path] = None,
    timeout: int = 30,
) -> Optional[Path]:
    """Try to download a paper PDF from Sci-Hub using its DOI.

    Args:
        doi: The DOI of the paper (e.g., '10.1002/adfm.2025075092').
        output_dir: Directory to save the PDF. Defaults to config.output_dir.
        timeout: Request timeout in seconds.

    Returns:
        Path to the downloaded PDF, or None if download failed.
    """
    config = get_config()
    if output_dir is None:
        output_dir = config.output_dir / "pdfs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize DOI for filename
    safe_doi = re.sub(r"[^\w\-.]", "_", doi)
    output_path = output_dir / f"{safe_doi}.pdf"

    if output_path.exists():
        return output_path  # already downloaded

    # Try multiple Sci-Hub mirrors
    mirrors = [
        config.scihub_mirror,
        "https://sci-hub.ru",
        "https://sci-hub.st",
    ]

    for mirror in mirrors:
        try:
            pdf_path = _try_scihub_mirror(mirror, doi, output_path, timeout)
            if pdf_path:
                return pdf_path
        except Exception:
            continue

    return None


def _try_scihub_mirror(
    mirror: str,
    doi: str,
    output_path: Path,
    timeout: int,
) -> Optional[Path]:
    """Attempt download from a single Sci-Hub mirror."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    })

    # Step 1: Visit the DOI page
    url = f"{mirror.rstrip('/')}/{doi}"
    resp = session.get(url, timeout=timeout)
    if resp.status_code != 200:
        return None

    # Step 2: Find the PDF URL in the page
    soup = BeautifulSoup(resp.text, "html.parser")

    # Sci-Hub embeds the PDF in an <iframe> or <embed> tag
    pdf_url = None
    for tag in soup.find_all(["iframe", "embed"]):
        src = tag.get("src", "")
        if src.endswith(".pdf") or "pdf" in src.lower():
            pdf_url = src
            if pdf_url.startswith("//"):
                pdf_url = "https:" + pdf_url
            elif pdf_url.startswith("/"):
                pdf_url = mirror.rstrip("/") + pdf_url
            break

    if not pdf_url:
        # Fallback: try to find PDF link by searching for "download" or ".pdf"
        for a in soup.find_all("a"):
            href = a.get("href", "")
            if href.endswith(".pdf") or ".pdf?" in href:
                pdf_url = href
                if pdf_url.startswith("//"):
                    pdf_url = "https:" + pdf_url
                break

    if not pdf_url:
        return None

    # Step 3: Download the PDF
    time.sleep(1)  # be polite
    pdf_resp = session.get(pdf_url, timeout=timeout * 2)
    if pdf_resp.status_code == 200 and len(pdf_resp.content) > 1000:
        output_path.write_bytes(pdf_resp.content)
        return output_path

    return None
