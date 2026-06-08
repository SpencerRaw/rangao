"""WeChat Official Account API wrapper.

Handles access token management, material uploads, and draft operations.
Uses wechatpy for the underlying API calls.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

import requests

from ..config import get_config


class WeChatAPI:
    """Minimal WeChat Official Account API client.

    Handles token lifecycle and provides material/draft operations.
    Uses wechatpy internally when available, falls back to direct HTTP.
    """

    def __init__(self, appid: str = "", appsecret: str = ""):
        config = get_config()
        self.appid = appid or config.wechat_appid
        self.appsecret = appsecret or config.wechat_appsecret
        self._token: Optional[str] = None
        self._token_expires: float = 0.0
        self._cache_path = Path(config.wechat_token_cache)

        # Try to load cached token
        self._load_cache()

    # ---- Token Management ----

    @property
    def access_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if self._token and time.time() < self._token_expires - 300:
            return self._token
        return self._refresh_token()

    def _refresh_token(self) -> str:
        """Fetch a new access token from WeChat."""
        url = (
            "https://api.weixin.qq.com/cgi-bin/token"
            f"?grant_type=client_credential&appid={self.appid}&secret={self.appsecret}"
        )
        resp = requests.get(url, timeout=15)
        data = resp.json()

        if "access_token" not in data:
            raise RuntimeError(f"Failed to get access_token: {data}")

        self._token = data["access_token"]
        self._token_expires = time.time() + data.get("expires_in", 7200)
        self._save_cache()
        return self._token

    def _load_cache(self):
        if self._cache_path.exists():
            try:
                cache = json.loads(self._cache_path.read_text())
                if time.time() < cache.get("expires_at", 0) - 300:
                    self._token = cache["access_token"]
                    self._token_expires = cache["expires_at"]
            except Exception:
                pass

    def _save_cache(self):
        if self._token:
            cache = {
                "access_token": self._token,
                "expires_at": self._token_expires,
            }
            self._cache_path.write_text(json.dumps(cache))

    # ---- Material Management ----

    def upload_permanent_image(self, image_path: Path) -> dict:
        """Upload a permanent image material to WeChat.

        Args:
            image_path: Local path to the image file.

        Returns:
            Dict with 'url' and 'media_id' on success.

        Raises:
            RuntimeError: If upload fails.
        """
        url = (
            "https://api.weixin.qq.com/cgi-bin/material/add_material"
            f"?access_token={self.access_token}&type=image"
        )
        with open(image_path, "rb") as f:
            resp = requests.post(url, files={"media": f}, timeout=60)

        data = resp.json()
        if "url" not in data:
            raise RuntimeError(f"Image upload failed: {data}")

        return {"url": data["url"], "media_id": data["media_id"]}

    def upload_image_and_replace(
        self,
        html_path: Path,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Replace local image paths in HTML with WeChat CDN URLs.

        Reads an HTML file, uploads all local images to WeChat,
        and replaces their src attributes with CDN URLs.

        Args:
            html_path: Path to the HTML file with local image refs.
            output_path: Where to save the updated HTML.

        Returns:
            Path to the updated HTML.
        """
        from bs4 import BeautifulSoup

        if output_path is None:
            output_path = html_path.parent / f"published_{html_path.name}"

        soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
        base_dir = html_path.parent

        for img in soup.find_all("img"):
            src = img.get("src", "")
            if not src or src.startswith(("http://", "https://", "data:")):
                continue

            local_path = Path(src)
            if not local_path.is_absolute():
                local_path = base_dir / src

            if local_path.exists():
                try:
                    result = self.upload_permanent_image(local_path)
                    img["src"] = result["url"]
                except Exception as e:
                    print(f"  ⚠️ Failed to upload {local_path.name}: {e}")

        output_path.write_text(str(soup), encoding="utf-8")
        return output_path

    # ---- Draft Management ----

    def create_draft(self, articles: list[dict]) -> dict:
        """Create a draft in WeChat draft box.

        Args:
            articles: List of article dicts, each with at minimum:
                - title: Article title
                - content: HTML content string
                - thumb_media_id: Cover image media_id (optional)

        Returns:
            API response dict with 'media_id' (draft ID).
        """
        url = (
            "https://api.weixin.qq.com/cgi-bin/draft/add"
            f"?access_token={self.access_token}"
        )
        payload = {"articles": articles}
        resp = requests.post(url, json=payload, timeout=30)
        data = resp.json()

        if "media_id" not in data:
            raise RuntimeError(f"Draft creation failed: {data}")

        return data

    def list_drafts(self, offset: int = 0, count: int = 20) -> dict:
        """List drafts in the draft box."""
        url = (
            "https://api.weixin.qq.com/cgi-bin/draft/batchget"
            f"?access_token={self.access_token}"
        )
        resp = requests.post(url, json={"offset": offset, "count": count}, timeout=30)
        return resp.json()
