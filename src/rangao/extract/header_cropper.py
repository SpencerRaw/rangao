"""Crop the header region from a PDF's first page.

Used to create the "title card" image that appears at the top of WeChat articles.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF


def crop_header(
    pdf_path: Path,
    output_path: Optional[Path] = None,
    top_keyword: str = "Advanced Functional Materials",
    bottom_keyword: str = "Received",
) -> Optional[Path]:
    """Crop the header region from page 1 of a PDF.

    Finds the region between two keywords on the first page and renders it as a PNG.

    Args:
        pdf_path: Path to the PDF.
        output_path: Output image path. Defaults to <stem>_header.png.
        top_keyword: Text marking the top boundary (e.g., journal name).
        bottom_keyword: Text marking the bottom boundary (e.g., "Received").

    Returns:
        Path to the cropped image, or None if keywords not found.
    """
    if output_path is None:
        output_path = pdf_path.parent / f"{pdf_path.stem}_header.png"

    doc = fitz.open(str(pdf_path))
    page = doc[0]

    # Search for top keyword
    top_rects = page.search_for(top_keyword)
    if not top_rects:
        doc.close()
        return None

    # Search for bottom keyword
    bottom_rects = page.search_for(bottom_keyword)
    if not bottom_rects:
        doc.close()
        return None

    top_rect = top_rects[0]
    bottom_rect = bottom_rects[0]

    page_width = page.rect.width
    margin = 10
    clip_rect = fitz.Rect(
        margin,
        top_rect.y0,
        page_width - margin,
        bottom_rect.y1,
    )

    pix = page.get_pixmap(clip=clip_rect, dpi=200)
    pix.save(str(output_path))
    doc.close()

    return output_path
