"""PDF content extraction — text + images using PyMuPDF."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from ..models import ExtractedContent, Paper


def extract_pdf(
    pdf_path: Path,
    output_dir: Optional[Path] = None,
    paper: Optional[Paper] = None,
) -> ExtractedContent:
    """Extract text and images from a PDF.

    Args:
        pdf_path: Path to the PDF file.
        output_dir: Directory for extracted images and text.
            Defaults to <pdf_stem>_extracted/.
        paper: Optional Paper metadata.

    Returns:
        ExtractedContent with full_text and image paths.
    """
    if output_dir is None:
        output_dir = pdf_path.parent / f"{pdf_path.stem}_extracted"
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    all_text: list[str] = []
    images: list[Path] = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        text = page.get_text()
        all_text.append(f"===== Page {page_index + 1} =====\n{text}")

        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            img_filename = f"page{page_index + 1}_img{img_index + 1}.{ext}"
            img_path = output_dir / img_filename
            img_path.write_bytes(image_bytes)
            images.append(img_path)

    doc.close()

    # Save full text
    text_path = output_dir / "full_text.txt"
    text_path.write_text("\n\n".join(all_text), encoding="utf-8")

    return ExtractedContent(
        full_text="\n\n".join(all_text),
        images=images,
        paper=paper,
        page_count=len(doc) if hasattr(doc, "page_count") else 0,
    )
