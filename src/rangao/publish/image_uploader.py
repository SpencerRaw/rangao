"""Image uploader — handles uploading images to WeChat and other CDNs.

Addresses the IP whitelist problem by supporting:
- Direct WeChat material upload (requires IP whitelist)
- Free image CDN fallback (sm.ms, imgbb)
- Proxy support for stable outgoing IP
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

import requests

from ..config import get_config


class ImageUploader:
    """Upload images to WeChat or fallback CDNs."""

    def __init__(self, use_wechat: bool = True):
        self.config = get_config()
        self.use_wechat = use_wechat and self.config.has_wechat_credentials
        self._wechat_api = None

    def upload(self, image_path: Path) -> str:
        """Upload an image and return its public URL.

        Strategy: WeChat (primary) → sm.ms (fallback) → imgbb (fallback).

        Args:
            image_path: Local image file.

        Returns:
            Public URL of the uploaded image.
        """
        if self.use_wechat:
            try:
                return self._upload_to_wechat(image_path)
            except Exception:
                pass

        # Fallback to free CDNs
        url = self._upload_to_smms(image_path)
        if url:
            return url

        url = self._upload_to_imgbb(image_path)
        if url:
            return url

        # Absolute last resort: return local path as data URI for small images
        return self._as_data_uri(image_path)

    def upload_batch(self, image_paths: list[Path]) -> dict[Path, str]:
        """Upload multiple images. Returns mapping of local_path → public_url."""
        results: dict[Path, str] = {}
        for path in image_paths:
            try:
                results[path] = self.upload(path)
            except Exception as e:
                results[path] = f"<!-- upload failed: {e} -->"
        return results

    def _upload_to_wechat(self, image_path: Path) -> str:
        if self._wechat_api is None:
            from .wechat_api import WeChatAPI
            self._wechat_api = WeChatAPI()
        result = self._wechat_api.upload_permanent_image(image_path)
        return result["url"]

    @staticmethod
    def _upload_to_smms(image_path: Path) -> Optional[str]:
        """Upload to sm.ms (free image hosting)."""
        try:
            with open(image_path, "rb") as f:
                files = {"smfile": f}
                resp = requests.post(
                    "https://sm.ms/api/v2/upload",
                    files=files,
                    timeout=30,
                )
            data = resp.json()
            if data.get("success"):
                return data["data"]["url"]
        except Exception:
            pass
        return None

    @staticmethod
    def _upload_to_imgbb(image_path: Path) -> Optional[str]:
        """Upload to imgbb.com (free, no API key needed for basic use)."""
        try:
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            resp = requests.post(
                "https://api.imgbb.com/1/upload",
                data={"image": b64},
                timeout=30,
            )
            data = resp.json()
            if data.get("success"):
                return data["data"]["url"]
        except Exception:
            pass
        return None

    @staticmethod
    def _as_data_uri(image_path: Path, max_size: int = 100_000) -> str:
        """Convert small images to data URIs as absolute last resort."""
        size = image_path.stat().st_size
        if size > max_size:
            return f"<!-- image too large for data URI: {image_path.name} -->"
        ext = image_path.suffix.lower().replace(".", "")
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif"}.get(ext, "image/png")
        b64 = base64.b64encode(image_path.read_bytes()).decode()
        return f"data:{mime};base64,{b64}"
