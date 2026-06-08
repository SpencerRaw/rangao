# 燃稿 · API Reference

This document describes the Python API for programmatic use. For CLI usage, see [README.md](../README.md).

---

## Core Pipeline

### `rangao.pipeline.run_pipeline()`

The one-stop function. Runs all stages in sequence.

```python
from rangao.pipeline import run_pipeline

result = run_pipeline(
    doi="10.1038/s41467-020-15562-9",  # or pdf_path="paper.pdf"
    style="academic_carbon_dots",
    auto_publish=False,
    skip_download=False,
)

print(result.article.markdown)   # generated article text
print(result.rendered.html)      # WeChat HTML
print(result.duration_seconds)   # total time
```

**Returns:** `PipelineResult` with all intermediate outputs.

---

## Stage 1: Discover

### `rangao.discover.search_crossref()`

```python
from rangao.discover import search_crossref

papers = search_crossref(
    issn="1521-4095",           # Advanced Materials ISSN
    query="carbon dots",
    days_back=10,
    journal_name="Adv. Mater.",
)
# Returns list[dict] with keys: title, doi, published_date, authors, url, journal
```

### `rangao.discover.fetch_papers_by_journal()`

```python
from rangao.discover import fetch_papers_by_journal

papers = fetch_papers_by_journal(
    journals=[("Advanced Materials", "1521-4095")],
    keywords=["carbon dots", "carbon quantum dots"],
    days_back=30,
    output_csv="papers.csv",
)
# Returns list[Paper]
```

### `rangao.discover.ai_filter_papers()`

```python
from rangao.discover import ai_filter_papers, is_research_article

# Remove corrections, editorials, etc.
research_papers = [p for p in papers if is_research_article(p.title)]

# AI-based relevance filtering
filtered = ai_filter_papers(research_papers, "carbon dots for cancer therapy")
```

---

## Stage 2: Download

### `rangao.download.download_from_doi()`

```python
from rangao.download import download_from_doi

pdf_path = download_from_doi("10.1038/s41467-020-15562-9")
# Returns Path to PDF or None
# Strategy order: Sci-Hub → Unpaywall OA → doi.org direct
```

### `rangao.download.download_via_scihub()`

```python
from rangao.download import download_via_scihub

pdf_path = download_via_scihub(
    doi="10.1038/s41467-020-15562-9",
    timeout=15,
    max_mirrors=4,
)
```

### `rangao.download.fetch_paper_metadata()`

```python
from rangao.download import fetch_paper_metadata, fetch_and_download

# Get metadata only
paper = fetch_paper_metadata("10.1038/s41467-020-15562-9")
print(paper.title, paper.authors, paper.journal)

# Get metadata + download PDF
paper = fetch_and_download("10.1038/s41467-020-15562-9")
print(paper.pdf_path)  # Path to downloaded PDF
```

### `rangao.download.fetch_latest_from_journal()`

```python
from rangao.download import fetch_latest_from_journal

papers = fetch_latest_from_journal(
    issn="1521-4095",
    journal_name="Advanced Materials",
    keywords=["carbon dots"],
    days_back=7,
    max_papers=10,
    download_pdfs=True,  # also download PDFs!
)
```

### `rangao.download.refresh_mirrors()` / `get_mirror_status()`

```python
from rangao.download import refresh_mirrors, get_mirror_status

mirrors = refresh_mirrors(force=True)
status = get_mirror_status()
# {"https://sci-hub.st": 0.44, "https://sci-hub.ru": 1.16, ...}
```

---

## Stage 3: Extract

### `rangao.extract.extract_pdf()`

```python
from rangao.extract import extract_pdf

content = extract_pdf(Path("paper.pdf"))
print(content.full_text[:500])   # first 500 chars
print(content.page_count)        # number of pages
print(len(content.images))       # number of extracted images
```

### `rangao.extract.crop_header()`

```python
from rangao.extract import crop_header

header = crop_header(
    Path("paper.pdf"),
    output_path=Path("header.png"),
    top_keyword="Advanced Materials",
    bottom_keyword="Received",
)
```

---

## Stage 4: Generate

### `rangao.generate.generate_article()`

```python
from rangao.generate import generate_article

article = generate_article(
    content,                           # ExtractedContent from extract_pdf()
    style_name="academic_carbon_dots",
    model="deepseek-chat",             # or "" for default
)
print(article.markdown)
print(article.tokens_used)
```

### `rangao.generate.StyleEngine`

```python
from rangao.generate import StyleEngine

engine = StyleEngine(Path("styles"))
styles = engine.list_styles()       # ["academic_carbon_dots", ...]
style = engine.load("quick_news")   # dict with prompt, language, etc.
```

---

## Stage 5: Render

### `rangao.render.md_to_wechat_html()`

```python
from rangao.render import md_to_wechat_html

rendered = md_to_wechat_html(article)
print(len(rendered.html))
```

### `rangao.render.inline_all_styles()`

```python
from rangao.render import inline_all_styles

html = "<html><style>p{color:red}</style><body><p>Hello</p></body></html>"
wechat_html = inline_all_styles(html)
# <style> removed, styles inlined to <p style="color:red">
```

---

## Stage 6: Publish

### `rangao.publish.DraftPublisher`

```python
from rangao.publish import DraftPublisher

publisher = DraftPublisher()

if publisher.is_ready:
    result = publisher.publish(rendered)
    print(result.draft_id)
```

### `rangao.publish.ImageUploader`

```python
from rangao.publish import ImageUploader

uploader = ImageUploader(use_wechat=True)
url = uploader.upload(Path("figure1.png"))
# Returns public URL (WeChat CDN or fallback)
```
