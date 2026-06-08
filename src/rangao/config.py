"""Unified configuration from environment variables."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env at import time (safe to call multiple times)
load_dotenv()


@dataclass
class Config:
    """All configuration loaded from environment variables with sensible defaults."""

    # --- LLM ---
    llm_provider: str = os.getenv("RANGAO_LLM_PROVIDER", "deepseek")
    llm_api_key: str = os.getenv("RANGAO_LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
    llm_base_url: str = os.getenv("RANGAO_LLM_BASE_URL", "https://api.deepseek.com")
    llm_model: str = os.getenv("RANGAO_LLM_MODEL", "deepseek-chat")
    llm_reasoning_model: str = os.getenv("RANGAO_LLM_REASONING_MODEL", "deepseek-reasoner")
    llm_temperature: float = float(os.getenv("RANGAO_LLM_TEMPERATURE", "0.7"))
    llm_max_tokens: int = int(os.getenv("RANGAO_LLM_MAX_TOKENS", "8000"))

    # --- WeChat ---
    wechat_appid: str = os.getenv("RANGAO_WECHAT_APPID", "")
    wechat_appsecret: str = os.getenv("RANGAO_WECHAT_APPSECRET", "")
    wechat_token_cache: str = os.getenv("RANGAO_WECHAT_TOKEN_CACHE", ".wechat_token.json")

    # --- Sci-Hub ---
    scihub_mirror: str = os.getenv("RANGAO_SCIHUB_MIRROR", "https://sci-hub.se")

    # --- Crossref ---
    crossref_email: str = os.getenv("RANGAO_CROSSREF_EMAIL", "mail@example.com")
    crossref_base_url: str = "https://api.crossref.org"

    # --- Paths ---
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    styles_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "styles")
    output_dir: Path = field(default_factory=lambda: Path(os.getenv("RANGAO_OUTPUT_DIR", str(Path(__file__).resolve().parent.parent.parent / "output"))))
    cache_dir: Path = field(default_factory=lambda: Path(os.getenv("RANGAO_CACHE_DIR", str(Path(__file__).resolve().parent.parent.parent / ".cache"))))

    # --- Pipeline ---
    auto_publish: bool = os.getenv("RANGAO_AUTO_PUBLISH", "false").lower() == "true"
    skip_download: bool = os.getenv("RANGAO_SKIP_DOWNLOAD", "false").lower() == "true"
    skip_render: bool = False  # set by CLI args, not env

    @property
    def has_wechat_credentials(self) -> bool:
        return bool(self.wechat_appid and self.wechat_appsecret)

    @property
    def has_llm_credentials(self) -> bool:
        return bool(self.llm_api_key)

    def ensure_dirs(self):
        """Create output and cache directories if they don't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


# Singleton
_config: Optional[Config] = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
        _config.ensure_dirs()
    return _config
