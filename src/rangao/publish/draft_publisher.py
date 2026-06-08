"""Draft publisher — pushes rendered articles to WeChat draft box."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models import PublishResult, RenderedArticle
from .image_uploader import ImageUploader
from .wechat_api import WeChatAPI


class DraftPublisher:
    """Publish rendered articles to WeChat Official Account draft box."""

    def __init__(self):
        self.api: Optional[WeChatAPI] = None
        self.uploader = ImageUploader()

    @property
    def is_ready(self) -> bool:
        """Check if WeChat credentials are configured."""
        try:
            self._ensure_api()
            return True
        except Exception:
            return False

    def _ensure_api(self):
        if self.api is None:
            self.api = WeChatAPI()
            # Trigger token fetch to validate credentials
            _ = self.api.access_token

    def publish(self, rendered: RenderedArticle) -> PublishResult:
        """Publish a rendered article to WeChat draft box.

        Steps:
        1. Upload local images to WeChat CDN
        2. Replace image URLs in HTML
        3. Push to draft box

        Args:
            rendered: The rendered article with HTML content.

        Returns:
            PublishResult with success status and draft ID.
        """
        try:
            self._ensure_api()
        except Exception as e:
            return PublishResult(success=False, error=f"WeChat auth failed: {e}")

        try:
            # Upload images and replace URLs
            html = self._replace_image_urls(rendered)

            # Push to draft box
            article = rendered.article
            title = self._extract_title(html) or article.paper.title

            response = self.api.create_draft([{
                "title": title,
                "content": html,
                "content_source_url": article.paper.url or "",
                "need_open_comment": 0,
                "only_fans_can_comment": 0,
            }])

            return PublishResult(
                success=True,
                media_id=response.get("media_id", ""),
                draft_id=response.get("media_id", ""),
            )

        except Exception as e:
            return PublishResult(success=False, error=str(e))

    def publish_html_file(
        self,
        html_path: Path,
        title: str = "",
    ) -> PublishResult:
        """Publish an HTML file directly to WeChat draft box.

        Args:
            html_path: Path to the WeChat-compatible HTML file.
            title: Article title. Extracted from HTML if empty.

        Returns:
            PublishResult.
        """
        try:
            self._ensure_api()
        except Exception as e:
            return PublishResult(success=False, error=f"WeChat auth failed: {e}")

        try:
            # Upload images in HTML and replace
            output = self.api.upload_image_and_replace(html_path)
            html = output.read_text(encoding="utf-8")

            # Push
            article_title = title or self._extract_title(html) or html_path.stem
            response = self.api.create_draft([{
                "title": article_title,
                "content": html,
                "need_open_comment": 0,
                "only_fans_can_comment": 0,
            }])

            return PublishResult(
                success=True,
                media_id=response.get("media_id", ""),
                draft_id=response.get("media_id", ""),
            )
        except Exception as e:
            return PublishResult(success=False, error=str(e))

    def _replace_image_urls(self, rendered: RenderedArticle) -> str:
        """Upload images and replace local paths with CDN URLs in HTML."""
        import re
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(rendered.html, "html.parser")

        for img in soup.find_all("img"):
            src = img.get("src", "")
            if not src or src.startswith(("http://", "https://", "data:")):
                continue

            # Try to resolve the local path
            local_path = Path(src)
            if local_path.exists():
                uploaded_url = self.uploader.upload(local_path)
                img["src"] = uploaded_url

        return str(soup)

    @staticmethod
    def _extract_title(html: str) -> Optional[str]:
        """Extract article title from HTML h1 tag."""
        import re
        match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
        if match:
            # Strip HTML tags inside h1
            title = re.sub(r"<[^>]+>", "", match.group(1)).strip()
            return title
        return None
