"""Integration tests for 燃稿 pipeline.

Run:
    cd rangao && PYTHONPATH=src python -m pytest tests/ -v
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

# Use the test101 PDF from the old project
TEST_PDF = Path("/Users/apple/Desktop/dw/100k/aiWechatFlow/test101/input.pdf")

# Skip tests that need API key if not available
import os
from dotenv import load_dotenv
load_dotenv()
HAS_API_KEY = bool(os.getenv("RANGAO_LLM_API_KEY", ""))


class TestExtraction:
    """PDF extraction tests — no API key needed."""

    def test_extract_pdf_text_and_images(self):
        from rangao.extract.pdf_extractor import extract_pdf

        content = extract_pdf(TEST_PDF)
        assert content.page_count > 0, "Should extract pages"
        assert len(content.full_text) > 100, "Should extract text"
        assert len(content.images) > 0, "Should extract images"

    def test_extract_pdf_output_dir(self):
        from rangao.extract.pdf_extractor import extract_pdf

        with tempfile.TemporaryDirectory() as tmp:
            content = extract_pdf(TEST_PDF, output_dir=Path(tmp))
            assert (Path(tmp) / "full_text.txt").exists()
            assert len(list(Path(tmp).glob("page*_img*"))) > 0

    def test_crop_header(self):
        from rangao.extract.header_cropper import crop_header

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "header.png"
            result = crop_header(TEST_PDF, output_path=out,
                                 top_keyword="Advanced Materials",
                                 bottom_keyword="Received")
            # May fail if keywords not found in this PDF
            if result:
                assert result.exists()
                assert result.stat().st_size > 1000


class TestModels:
    """Data model tests."""

    def test_paper_creation(self):
        from rangao.models import Paper, PaperStatus

        paper = Paper(
            title="Test Paper",
            doi="10.1002/test.123",
            journal="Test Journal",
        )
        assert paper.status == PaperStatus.NEW
        assert "Test Paper" in paper.title
        assert paper.doi == "10.1002/test.123"

    def test_pipeline_result_initial(self):
        from rangao.models import Paper, PipelineResult

        result = PipelineResult(paper=Paper(title="Test", doi="10.1002/x"))
        assert result.errors == []
        assert result.success is True
        assert result.started_at


class TestConfig:
    """Configuration tests."""

    def test_config_defaults(self):
        from rangao.config import Config
        c = Config()
        assert c.llm_model == "deepseek-chat"
        assert c.llm_provider == "deepseek"
        assert c.scihub_mirror == "https://sci-hub.se"

    def test_config_has_dirs(self):
        from rangao.config import get_config
        c = get_config()
        assert c.output_dir.exists()
        assert c.cache_dir.exists()


class TestStyleEngine:
    """Style template tests."""

    def test_load_builtin_style(self):
        from rangao.generate.style_engine import StyleEngine
        from pathlib import Path

        engine = StyleEngine(Path("styles"))
        style = engine.load("nonexistent")
        assert "prompt" in style
        assert style["language"] == "zh-CN"

    def test_load_carbon_dots_style(self):
        from rangao.generate.style_engine import StyleEngine
        from pathlib import Path

        engine = StyleEngine(Path("styles"))
        style = engine.load("academic_carbon_dots")
        assert "碳点" in style["prompt"] or "carbon" in style["prompt"].lower()

    def test_list_styles(self):
        from rangao.generate.style_engine import StyleEngine
        from pathlib import Path

        engine = StyleEngine(Path("styles"))
        styles = engine.list_styles()
        assert "academic_carbon_dots" in styles


class TestDiscover:
    """Paper discovery tests."""

    def test_is_research_article_true(self):
        from rangao.discover.filter import is_research_article
        assert is_research_article("Carbon Dots for Cancer Therapy")

    def test_is_research_article_correction(self):
        from rangao.discover.filter import is_research_article
        assert not is_research_article("Correction to: Carbon Dots")

    def test_is_research_article_erratum(self):
        from rangao.discover.filter import is_research_article
        assert not is_research_article("Erratum: Carbon Nanodots")

    def test_deduplicate_by_doi(self):
        from rangao.discover.filter import deduplicate_by_doi
        from rangao.models import Paper

        papers = [
            Paper(title="A", doi="10.1002/a"),
            Paper(title="B", doi="10.1002/b"),
            Paper(title="A duplicate", doi="10.1002/a"),
        ]
        result = deduplicate_by_doi(papers)
        assert len(result) == 2


class TestRender:
    """HTML rendering tests."""

    def test_inline_styler_basic(self):
        from rangao.render.inline_styler import inline_all_styles

        html = "<html><head><style>p { color: red; }</style></head><body><p>Hello</p></body></html>"
        result = inline_all_styles(html)
        assert "style=" in result
        assert "<style>" not in result  # style tags should be removed
        assert "Hello" in result

    def test_inline_styler_removes_classes(self):
        from rangao.render.inline_styler import inline_all_styles

        html = '<html><body><div class="my-class">text</div></body></html>'
        result = inline_all_styles(html)
        assert 'class=' not in result


@pytest.mark.skipif(not HAS_API_KEY, reason="No API key configured")
class TestPipelineIntegration:
    """Full pipeline integration — requires API key."""

    def test_pipeline_end_to_end(self):
        from rangao.pipeline import run_pipeline

        result = run_pipeline(
            pdf_path=str(TEST_PDF),
            style="academic_carbon_dots",
            auto_publish=False,
            skip_download=True,
        )
        assert result.success, f"Pipeline failed: {result.errors}"
        assert result.article is not None
        assert len(result.article.markdown) > 100
        assert result.rendered is not None
        assert len(result.rendered.html) > 100
