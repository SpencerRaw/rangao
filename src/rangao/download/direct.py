"""Direct PDF download and DOI resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import requests

from ..config import get_config


def download_direct(
    url: str,
    output_path: Optional[Path] = None,
    timeout: int = 60,
) -> Optional[Path]:
    """Download a PDF directly from a URL.

    Args:
        url: Direct URL to the PDF.
        output_path: Where to save. Auto-generated if None.
        timeout: Request timeout.

    Returns:
        Path to downloaded file, or None.
    """
    config = get_config()

    if output_path is None:
        output_dir = config.output_dir / "pdfs"
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = url.rstrip("/").split("/")[-1] or "paper.pdf"
        if not filename.endswith(".pdf"):
            filename += ".pdf"
        output_path = output_dir / filename

    try:
        resp = requests.get(url, timeout=timeout, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")
        if "application/pdf" not in content_type and not url.endswith(".pdf"):
            # Might still be a PDF, check first bytes
            first_bytes = resp.content[:5]
            if first_bytes != b"%PDF-":
                return None

        output_path.write_bytes(resp.content)
        return output_path
    except Exception:
        return None


def download_from_doi(
    doi: str,
    output_dir: Optional[Path] = None,
) -> Optional[Path]:
    """Try multiple strategies to download a paper by DOI.

    Order: Sci-Hub, Unpaywall OA, direct DOI resolution.

    Args:
        doi: Paper DOI.
        output_dir: Save directory.

    Returns:
        Path to PDF or None.
    """
    from .scihub import download_via_scihub

    # Strategy 1: Sci-Hub
    result = download_via_scihub(doi, output_dir)
    if result:
        return result

    # Strategy 2: Unpaywall (open access)
    result = _try_unpaywall(doi, output_dir)
    if result:
        return result

    # Strategy 3: Direct doi.org resolution
    result = _try_doi_direct(doi, output_dir)
    if result:
        return result

    return None


def _try_unpaywall(doi: str, output_dir: Optional[Path]) -> Optional[Path]:
    """Check Unpaywall for open-access PDF."""
    try:
        url = f"https://api.unpaywall.org/v2/{doi}?email=mail@example.com"
        resp = requests.get(url, timeout=15)
        data = resp.json()
        oa_url = data.get("best_oa_location", {}).get("url_for_pdf")
        if oa_url:
            return download_direct(oa_url, output_dir)
    except Exception:
        pass
    return None


def _try_doi_direct(doi: str, output_dir: Optional[Path]) -> Optional[Path]:
    """Try doi.org → publisher PDF redirect."""
    try:
        doi_url = f"https://doi.org/{doi}"
        headers = {"Accept": "application/pdf"}
        resp = requests.get(doi_url, headers=headers, allow_redirects=True, timeout=30)
        if resp.status_code == 200 and len(resp.content) > 1000:
            config = get_config()
            out = (output_dir or config.output_dir / "pdfs")
            out.mkdir(parents=True, exist_ok=True)
            path = out / f"{doi.replace('/', '_')}.pdf"
            path.write_bytes(resp.content)
            return path
    except Exception:
        pass
    return None
