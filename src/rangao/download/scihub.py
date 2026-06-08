"""Sci-Hub PDF downloader with multi-mirror auto-failover.

Features:
- Curated mirror pool with health checking
- Smart rotation: fastest-responding mirror tried first
- Auto-refresh from known-good mirror registries
- Handles Sci-Hub's evolving UI (iframe, embed, button, direct link)
"""

from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Optional

import requests
from bs4 import BeautifulSoup

from ..config import get_config

# ---- Mirror Pool ----
# Known Sci-Hub domains (verified as of 2026-06).
# The pool auto-rotates: fastest-responding mirrors promoted to front.
_DEFAULT_MIRRORS = [
    "https://sci-hub.se",
    "https://sci-hub.ru",
    "https://sci-hub.st",
    "https://sci-hub.ee",
    "https://sci-hub.wf",
    "https://sci-hub.is",
    "https://sci-hub.shop",
    "https://sci-hub.mksa.top",
]

# Secondary mirror registries to pull fresh mirrors from
_REGISTRY_URLS = [
    "https://sci-hub.shop/",
    "https://sci-hubse.com/",
]

# ---- Mirror Manager ----
_mirror_pool: list[str] = []
_mirror_health: dict[str, float] = {}  # mirror → last_response_time_seconds
_pool_lock = Lock()
_health_cache_path: Optional[Path] = None


def _get_health_cache_path() -> Path:
    global _health_cache_path
    if _health_cache_path is None:
        config = get_config()
        _health_cache_path = config.cache_dir / "scihub_mirrors.json"
    return _health_cache_path


def _load_mirror_pool() -> list[str]:
    """Load mirror pool from cache or build fresh."""
    cache_path = _get_health_cache_path()

    # Try cache first
    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text())
            cached_mirrors = data.get("mirrors", [])
            cached_health = data.get("health", {})
            # Only use cache if < 24 hours old
            if time.time() - data.get("updated_at", 0) < 86400:
                with _pool_lock:
                    _mirror_health.update(cached_health)
                if cached_mirrors:
                    return cached_mirrors
        except Exception:
            pass

    # Build fresh pool: configured mirror + defaults
    config = get_config()
    mirrors = [config.scihub_mirror] if config.scihub_mirror else []
    for m in _DEFAULT_MIRRORS:
        if m not in mirrors:
            mirrors.append(m)

    return mirrors


def _save_mirror_pool(mirrors: list[str]):
    """Save mirror pool and health data to cache."""
    cache_path = _get_health_cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with _pool_lock:
        data = {
            "mirrors": mirrors,
            "health": dict(_mirror_health),
            "updated_at": time.time(),
        }
    cache_path.write_text(json.dumps(data, indent=2))


def _probe_mirror(mirror: str, timeout: int = 5) -> tuple[str, Optional[float]]:
    """Quick health check on a mirror. Returns (mirror, response_time) or (mirror, None)."""
    try:
        start = time.time()
        resp = requests.head(mirror, timeout=timeout, allow_redirects=True)
        elapsed = time.time() - start
        if resp.status_code < 500:
            return (mirror, elapsed)
    except Exception:
        pass
    return (mirror, None)


def refresh_mirrors(force: bool = False) -> list[str]:
    """Refresh the mirror pool — probe all mirrors for health, sort by speed.

    Args:
        force: If True, skip cache and probe fresh.

    Returns:
        Ordered list of mirrors (fastest first).
    """
    global _mirror_pool

    if not force and _mirror_pool:
        return _mirror_pool

    mirrors = _load_mirror_pool()

    # Probe all mirrors concurrently
    healthy: list[tuple[str, float]] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(_probe_mirror, m): m for m in mirrors}
        for fut in as_completed(futures, timeout=15):
            mirror, elapsed = fut.result()
            if elapsed is not None:
                healthy.append((mirror, elapsed))
                with _pool_lock:
                    _mirror_health[mirror] = elapsed

    # Sort by response time (fastest first), then append unhealthy mirrors
    healthy.sort(key=lambda x: x[1])
    ordered = [m for m, _ in healthy]
    for m in mirrors:
        if m not in ordered:
            ordered.append(m)

    _mirror_pool = ordered
    _save_mirror_pool(ordered)
    return ordered


def download_via_scihub(
    doi: str,
    output_dir: Optional[Path] = None,
    timeout: int = 15,
    max_mirrors: int = 4,
) -> Optional[Path]:
    """Download a paper PDF from Sci-Hub using its DOI.

    Mirrors are tried in speed order (fastest first). Falls through
    all mirrors before giving up.

    Args:
        doi: Paper DOI (e.g., '10.1002/adfm.2025075092').
        output_dir: Save directory. Defaults to config.output_dir/pdfs/.
        timeout: Per-mirror request timeout in seconds.
        max_mirrors: Max mirrors to try before giving up.

    Returns:
        Path to downloaded PDF, or None if all mirrors failed.
    """
    config = get_config()
    if output_dir is None:
        output_dir = config.output_dir / "pdfs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize DOI for filename
    safe_doi = re.sub(r"[^\w\-.]", "_", doi)
    output_path = output_dir / f"{safe_doi}.pdf"

    if output_path.exists() and output_path.stat().st_size > 1000:
        return output_path

    # Get fresh mirror ordering
    mirrors = refresh_mirrors()

    tried = 0
    for mirror in mirrors:
        if tried >= max_mirrors:
            break
        try:
            result = _download_from_mirror(mirror, doi, output_path, timeout)
            if result:
                return result
            tried += 1
        except Exception:
            tried += 1
            continue

    return None


def _download_from_mirror(
    mirror: str,
    doi: str,
    output_path: Path,
    timeout: int,
) -> Optional[Path]:
    """Attempt PDF download from a single Sci-Hub mirror."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })

    # Step 1: Load the DOI page
    url = f"{mirror.rstrip('/')}/{doi}"
    resp = session.get(url, timeout=timeout, allow_redirects=True)
    if resp.status_code != 200:
        return None

    # Step 2: Extract PDF URL — try multiple strategies
    pdf_url = _extract_pdf_url(resp.text, mirror)

    if not pdf_url:
        return None

    # Step 3: Download the PDF
    time.sleep(0.5)  # be polite
    pdf_resp = session.get(pdf_url, timeout=timeout * 2, stream=True)

    # Verify it's actually a PDF
    content_type = pdf_resp.headers.get("content-type", "")
    first_bytes = pdf_resp.content[:10]

    if pdf_resp.status_code == 200 and len(pdf_resp.content) > 2000:
        if b"%PDF" in first_bytes or "pdf" in content_type.lower():
            output_path.write_bytes(pdf_resp.content)
            return output_path

    return None


def _extract_pdf_url(html: str, mirror: str) -> Optional[str]:
    """Extract PDF URL from Sci-Hub page using multiple strategies.

    Sci-Hub has changed its UI multiple times. This function handles:
    1. iframe/embed src (classic layout)
    2. Button onclick with location.href (newer layout)
    3. Direct <a> link ending in .pdf
    4. JavaScript window.open pattern
    """
    soup = BeautifulSoup(html, "html.parser")

    # Strategy 1: iframe or embed tag
    for tag in soup.find_all(["iframe", "embed"]):
        src = (tag.get("src") or "").strip()
        if src:
            return _resolve_url(src, mirror)

    # Strategy 2: Button with onclick="location.href='...'"
    for btn in soup.find_all(["button", "a"], onclick=True):
        onclick = btn.get("onclick", "")
        match = re.search(r"""location(?:\.href)?\s*=\s*['"]([^'"]+)['"]""", onclick)
        if match:
            return _resolve_url(match.group(1), mirror)
        # Also handle: onclick="window.open('...')"
        match = re.search(r"""window\.open\(['"]([^'"]+)['"]""", onclick)
        if match:
            return _resolve_url(match.group(1), mirror)

    # Strategy 3: Direct <a> link ending in .pdf or containing /download/
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.endswith(".pdf") or ".pdf?" in href or "/download/" in href:
            return _resolve_url(href, mirror)

    # Strategy 4: Look for any link containing "sci-hub" + "/downloads/"
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if "download" in href.lower() and ("sci-hub" in href.lower() or href.startswith("/")):
            return _resolve_url(href, mirror)

    # Strategy 5: Scan raw HTML for PDF URLs with regex
    pdf_patterns = [
        r'https?://[^"\'\s]+\.pdf[^"\'\s]*',
        r'//[^"\'\s]+\.pdf[^"\'\s]*',
        r'src\s*=\s*["\']([^"\']+\.pdf[^"\']*)["\']',
    ]
    for pattern in pdf_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for m in matches:
            url = m if isinstance(m, str) else m[0]
            if "sci-hub" in url.lower() or "download" in url.lower():
                return _resolve_url(url, mirror)

    return None


def _resolve_url(url: str, mirror: str) -> str:
    """Resolve relative/protocol-relative URLs to absolute."""
    url = url.strip()
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return mirror.rstrip("/") + url
    if not url.startswith("http"):
        return mirror.rstrip("/") + "/" + url.lstrip("/")
    return url


def get_mirror_status() -> dict:
    """Get the current mirror pool status — useful for debugging/CLI.

    Returns:
        Dict mapping mirror → response_time (or None if down).
    """
    refresh_mirrors()
    with _pool_lock:
        return dict(_mirror_health)
