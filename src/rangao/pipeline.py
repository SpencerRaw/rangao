"""One-click pipeline — DOI → WeChat draft in one command.

Usage:
    python -m rangao.pipeline --doi 10.1002/adfm.2025075092
    python -m rangao.pipeline --pdf paper.pdf
    python -m rangao.pipeline --discover "carbon dots" --publish
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from .config import get_config
from .models import Paper, PipelineResult


def run_pipeline(
    doi: str = "",
    pdf_path: str = "",
    style: str = "academic_carbon_dots",
    auto_publish: bool = False,
    skip_download: bool = False,
) -> PipelineResult:
    """Run the full pipeline: paper → article → WeChat draft.

    Args:
        doi: Paper DOI to download and process.
        pdf_path: Local PDF to process (skip download).
        style: Style template name.
        auto_publish: If True, push to WeChat draft box after rendering.
        skip_download: If True, skip PDF download step.

    Returns:
        PipelineResult with all intermediate outputs.
    """
    config = get_config()
    result = PipelineResult(paper=Paper(title="", doi=doi))

    try:
        # ---- Stage 1: Discover / Load ----
        if pdf_path:
            result.paper.pdf_path = Path(pdf_path)
            print(f"📄 Using local PDF: {pdf_path}")
        elif doi and not skip_download:
            print(f"🔍 Downloading paper: {doi}")
            from .download.direct import download_from_doi
            pdf = download_from_doi(doi)
            if pdf:
                result.paper.pdf_path = pdf
                print(f"   ✅ Downloaded: {pdf}")
            else:
                result.errors.append(f"Failed to download DOI: {doi}")
                print(f"   ❌ Could not download. Provide PDF manually with --pdf")

        if not result.paper.pdf_path:
            result.errors.append("No PDF available. Provide --pdf or a downloadable --doi")
            result.finished_at = datetime.now().isoformat()
            return result

        # ---- Stage 2: Extract ----
        print("📑 Extracting PDF...")
        from .extract.pdf_extractor import extract_pdf
        from .extract.header_cropper import crop_header

        extracted = extract_pdf(result.paper.pdf_path, paper=result.paper)
        result.extracted = extracted

        # Try to crop header image
        header = crop_header(result.paper.pdf_path)
        if header:
            extracted.header_image = header
            print(f"   ✅ Header cropped: {header}")

        print(f"   ✅ Extracted {extracted.page_count} pages, {len(extracted.images)} images")

        # ---- Stage 3: Generate Article ----
        print(f"✍️  Generating article (style: {style})...")
        from .generate.writer import generate_article

        article = generate_article(extracted, style_name=style)
        result.article = article
        print(f"   ✅ Generated {len(article.markdown)} chars, {article.tokens_used} tokens")

        # Save markdown
        md_path = config.output_dir / "result.md"
        md_path.write_text(article.markdown, encoding="utf-8")
        print(f"   📝 Markdown saved: {md_path}")

        # ---- Stage 4: Render HTML ----
        print("🎨 Rendering WeChat HTML...")
        from .render.wechat_html import md_to_wechat_html

        rendered = md_to_wechat_html(article)
        result.rendered = rendered
        print(f"   ✅ HTML rendered ({len(rendered.html)} chars)")

        # ---- Stage 5: Publish (optional) ----
        if auto_publish and config.has_wechat_credentials:
            print("📤 Publishing to WeChat draft box...")
            from .publish.draft_publisher import DraftPublisher

            publisher = DraftPublisher()
            publish_result = publisher.publish(rendered)
            result.published = publish_result

            if publish_result.success:
                print(f"   ✅ Draft created! ID: {publish_result.draft_id}")
            else:
                print(f"   ❌ Publish failed: {publish_result.error}")
                result.errors.append(f"Publish failed: {publish_result.error}")

    except Exception as e:
        result.errors.append(str(e))
        print(f"❌ Pipeline error: {e}")

    result.finished_at = datetime.now().isoformat()
    elapsed = result.duration_seconds
    print(f"\n⏱️  Pipeline completed in {elapsed:.1f}s")
    if result.errors:
        print(f"⚠️  Errors: {', '.join(result.errors)}")
    else:
        print("✅ All stages successful!")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="燃稿 (RánGǎo) — One paper in, one WeChat article out.",
    )
    parser.add_argument("--doi", help="Paper DOI to download and process")
    parser.add_argument("--pdf", help="Local PDF file path")
    parser.add_argument("--style", default="academic_carbon_dots", help="Style template name")
    parser.add_argument("--publish", action="store_true", help="Auto-publish to WeChat draft box")
    parser.add_argument("--skip-download", action="store_true", help="Skip PDF download")
    parser.add_argument("--output-dir", help="Override output directory")

    args = parser.parse_args()

    if not args.doi and not args.pdf:
        parser.print_help()
        print("\n❌ Must provide --doi or --pdf")
        sys.exit(1)

    config = get_config()
    if args.output_dir:
        config.output_dir = Path(args.output_dir)
        config.output_dir.mkdir(parents=True, exist_ok=True)

    result = run_pipeline(
        doi=args.doi or "",
        pdf_path=args.pdf or "",
        style=args.style,
        auto_publish=args.publish,
        skip_download=args.skip_download,
    )

    if result.rendered:
        print(f"\n📋 Output: {config.output_dir}")
        print(f"   Markdown: {config.output_dir / 'result.md'}")
        print(f"   HTML:     {config.output_dir / 'article.html'}")

    if result.published and result.published.success:
        print(f"\n📱 WeChat Draft ID: {result.published.draft_id}")
        print("   Open WeChat Official Account backend → Drafts → Edit & Publish")


if __name__ == "__main__":
    main()
