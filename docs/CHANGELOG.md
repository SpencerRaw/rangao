# 燃稿 · Changelog

## v0.1.0 (2026-06-08)

### Core Pipeline
- ✅ End-to-end pipeline: DOI/PDF → article → WeChat HTML → draft box
- ✅ CLI: `python -m rangao.pipeline --doi ...` and `--pdf ...`
- ✅ Streamlit web UI
- ✅ 9 writing style templates covering major research domains
- ✅ 17 integration tests, all passing

### Discover
- ✅ Crossref API search with journal × keyword × date range filtering
- ✅ AI-powered paper relevance verification via LLM
- ✅ Automatic deduplication and non-article removal (corrections, retractions, etc.)

### Download
- ✅ Multi-mirror Sci-Hub downloader with concurrent health probing (4/8 healthy)
- ✅ Auto-failover: Unpaywall OA → doi.org direct
- ✅ Crossref metadata fetch (`fetch_paper_metadata`)
- ✅ Journal batch fetch with optional PDF download (`fetch_latest_from_journal`)
- ✅ OpenAlex citation tracking (`fetch_citing_papers`)

### Extract
- ✅ PyMuPDF text + per-page image extraction
- ✅ Smart header crop from PDF page 1 (keyword-based)
- ✅ Automatic output directory management

### Generate
- ✅ DeepSeek-powered article generation with configurable style
- ✅ YAML-based style template engine with built-in fallbacks
- ✅ Style-aware system prompts with image handling rules
- ✅ Token usage tracking

### Render
- ✅ LLM-driven Markdown → WeChat HTML conversion
- ✅ Battle-tested WeChat rules: `<section>` for visual blocks, `<p>` for section headers, no `<style>` tags
- ✅ Keyword highlighting (red/green/blue) in background sections
- ✅ Deterministic CSS→inline converter (`inline_styler.py`) as fallback

### Publish
- ✅ WeChat access token management with file caching
- ✅ Permanent material image upload
- ✅ Draft box push API integration
- ✅ 3-tier image CDN fallback: WeChat → sm.ms → imgbb → data URI

### Infrastructure
- ✅ MIT License
- ✅ Bilingual README (EN + zh-CN)
- ✅ Full API reference documentation
- ✅ Outreach email templates (Hormozi value equation-based)
- ✅ `.env`-based configuration (zero hardcoded secrets)
- ✅ `pyproject.toml` with `pip install -e .` support
- ✅ `.gitignore` protecting all sensitive files

---

## Roadmap

### v0.2.0 (planned)
- [ ] Web UI: deploy to Streamlit Cloud for public demo
- [ ] WeChat draft auto-publish end-to-end test (needs AppID/Secret)
- [ ] PDF download queue with parallel Sci-Hub mirror probing
- [ ] Article history / version management
- [ ] Custom CSS themes for WeChat HTML rendering

### v0.3.0 (planned)
- [ ] Multi-article batch mode (process a CSV of DOIs)
- [ ] Scheduled cron jobs (auto-fetch latest papers from journals)
- [ ] Email/Telegram notifications when articles are ready
- [ ] WeChat "mass send" preview mode

### v1.0.0 (planned)
- [ ] SaaS deployment with user accounts
- [ ] Paid subscription tiers
- [ ] Analytics dashboard (articles generated, tokens used, etc.)
