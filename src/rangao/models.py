"""Data models for the 燃稿 pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class PaperStatus(Enum):
    NEW = "new"
    DOWNLOADED = "downloaded"
    EXTRACTED = "extracted"
    GENERATED = "generated"
    RENDERED = "rendered"
    PUBLISHED = "published"
    FAILED = "failed"


class ArticleStyle(Enum):
    ACADEMIC_CARBON_DOTS = "academic_carbon_dots"
    ACADEMIC_GENERAL = "academic_general"
    NEWS_BRIEF = "news_brief"
    DEEP_DIVE = "deep_dive"


@dataclass
class Paper:
    """A research paper discovered or provided by the user."""
    title: str
    doi: str
    authors: str = ""
    journal: str = ""
    published_date: str = ""
    url: str = ""
    pdf_path: Optional[Path] = None
    status: PaperStatus = PaperStatus.NEW
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)

    @property
    def citation(self) -> str:
        parts = [self.authors, f"*{self.journal}*" if self.journal else "", self.published_date]
        return ", ".join(p for p in parts if p)


@dataclass
class ExtractedContent:
    """Output of PDF extraction."""
    full_text: str
    images: list[Path] = field(default_factory=list)
    header_image: Optional[Path] = None
    paper: Optional[Paper] = None
    page_count: int = 0


@dataclass
class Article:
    """A generated article in markdown format."""
    paper: Paper
    markdown: str
    style: ArticleStyle = ArticleStyle.ACADEMIC_GENERAL
    model: str = ""
    tokens_used: int = 0
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RenderedArticle:
    """Article converted to WeChat-compatible HTML."""
    article: Article
    html: str
    image_urls: dict[str, str] = field(default_factory=dict)  # local_path → wechat_url
    rendered_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PublishResult:
    """Result of pushing to WeChat draft box."""
    success: bool
    media_id: str = ""
    draft_id: str = ""
    error: str = ""
    published_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""
    paper: Paper
    extracted: Optional[ExtractedContent] = None
    article: Optional[Article] = None
    rendered: Optional[RenderedArticle] = None
    published: Optional[PublishResult] = None
    errors: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: Optional[str] = None

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    @property
    def duration_seconds(self) -> float:
        if self.finished_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.finished_at)
            return (end - start).total_seconds()
        return 0.0
