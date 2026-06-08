> 🌐 [中文文档](README.zh-CN.md) | **English**

# 🔥 燃稿 · RánGǎo

> **One paper in, one WeChat article out.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-17%2F17%20passing-brightgreen.svg)](tests/)

RánGǎo is an end-to-end pipeline that transforms an academic paper into a beautifully formatted WeChat Official Account article — no manual copy-paste, no CSS debugging, no 4-hour Sunday night grind.

```
DOI or PDF → [Download] → [Extract] → [AI Write] → [WeChat HTML] → [Draft Box]
```

**Real benchmark:** *Nature Communications* paper → 5,000-character Chinese article → WeChat-compatible HTML — **54 seconds, fully automatic.**

---

## ✨ Features

| Step | What It Does |
|------|-------------|
| 🔍 **Discover** | Search Crossref for recent papers by journal, keywords, and date range. AI-powered relevance filtering. |
| 📥 **Download** | Multi-strategy PDF acquisition: Sci-Hub (4-mirror auto-failover), Unpaywall OA, direct DOI resolution. |
| 📑 **Extract** | PyMuPDF rips out full text + all images + crops the title-card header from page 1. |
| ✍️ **Generate** | DeepSeek (or any OpenAI-compatible LLM) writes a complete article following your style template. |
| 🎨 **Render** | Produces WeChat-compatible inline-style HTML — no `<style>` tags, no classes, battle-tested against WeChat's quirks. |
| 📤 **Publish** | Uploads images to WeChat CDN (or free fallback CDNs) and pushes the article to your draft box. |

---

## 🚀 30-Second Quick Start

```bash
git clone https://github.com/SpencerRaw/rangao.git
cd rangao
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
# Edit .env → paste your DeepSeek API key

# Run with a DOI
python -m rangao.pipeline --doi 10.1038/s41467-020-15562-9
```

**What you'll see:**
```
🔍 Downloading paper: 10.1038/s41467-020-15562-9
   📋 Characterization of spike glycoprotein of SARS-CoV-2...
   ✅ Downloaded: output/pdfs/10.1038_s41467-020-15562-9.pdf (2.0MB)
📑 Extracting PDF...
   ✅ Extracted 12 pages, 9 images
✍️  Generating article (style: academic_carbon_dots)...
   ✅ Generated 5041 chars, 21799 tokens
🎨 Rendering WeChat HTML...
   ✅ HTML rendered (12423 chars)

⏱️  Pipeline completed in 54.5s
✅ All stages successful!

📋 Output: output/
   Markdown: output/result.md
   HTML:     output/article.html
```

Open `output/article.html` → copy everything → paste into WeChat editor. Done.

---

## 📋 CLI Reference

```bash
# From a DOI (auto-download + process)
python -m rangao.pipeline --doi 10.1038/s41467-020-15562-9

# From a local PDF
python -m rangao.pipeline --pdf paper.pdf

# Pick a writing style
python -m rangao.pipeline --pdf paper.pdf --style biomed_breakthrough

# Push directly to WeChat draft box
python -m rangao.pipeline --doi 10.1038/... --publish

# Utility commands
python -m rangao.pipeline --list-styles      # Show all 9 style templates
python -m rangao.pipeline --mirror-status    # Check Sci-Hub mirror health
```

### Web UI

```bash
pip install "rangao[web]"
streamlit run app/streamlit_app.py
```

Upload a PDF → pick a style → click generate → preview the HTML → download. No terminal needed.

---

## 🎨 Style Templates (9 built-in)

Writing styles are YAML files in `styles/`. Each one encodes tone, structure, terminology conventions, and formatting rules for a specific research domain.

| Template | Domain | Length |
|----------|--------|--------|
| `academic_carbon_dots` | Carbon dots / nanomaterials | 3000-5000 chars |
| `academic_general` | General science | 2000-4000 chars |
| `biomed_breakthrough` | Biomedical / clinical translation | 3000-5000 chars |
| `energy_catalysis` | Electrocatalysis / batteries / CO₂RR | 2500-4000 chars |
| `physics_quantum` | Condensed matter / quantum materials | 2500-4000 chars |
| `ai_ml_cs` | AI / ML / computer science | 2000-3500 chars |
| `earth_climate` | Climate / geology / ecology | 2000-3500 chars |
| `social_science` | Economics / psychology / policy | 1500-3000 chars |
| `quick_news` | Rapid news brief | 800-1500 chars |

**Create your own:**

```yaml
# styles/my_journal.yaml
name: "My Journal Style"
language: zh-CN
prompt: |
  Write in an engaging, accessible tone. Structure: background → discovery → impact.
  Always mention the institution and lead author. Use third person.
```

---

## 🏗️ Architecture

```
rangao/
├── src/rangao/
│   ├── discover/         Crossref API search + AI paper filtering
│   │   ├── crossref.py       Journal × keyword search with pagination
│   │   └── filter.py         Dedup, non-article removal, LLM relevance check
│   │
│   ├── download/         PDF acquisition (3 strategies + fallback chain)
│   │   ├── scihub.py         8-mirror pool, concurrent health probe, 5 URL extraction strategies
│   │   ├── direct.py         Unpaywall OA + doi.org resolution
│   │   └── doi_fetcher.py    Crossref metadata + OpenAlex citation tracking
│   │
│   ├── extract/          PDF → structured content
│   │   ├── pdf_extractor.py  PyMuPDF text + per-page image extraction
│   │   └── header_cropper.py Smart title-card crop from page 1
│   │
│   ├── generate/         AI article writing
│   │   ├── writer.py         LLM call with multi-section prompts
│   │   └── style_engine.py   YAML style loader + built-in fallbacks
│   │
│   ├── render/           Markdown → WeChat-compatible inline HTML
│   │   ├── wechat_html.py    LLM-driven conversion with battle-tested WeChat rules
│   │   └── inline_styler.py  Deterministic CSS→inline converter (no LLM needed)
│   │
│   ├── publish/          WeChat Official Account integration
│   │   ├── wechat_api.py     Token management + material upload + draft API
│   │   ├── image_uploader.py WeChat → sm.ms → imgbb → data URI (3-tier fallback)
│   │   └── draft_publisher.py Full publish workflow: upload images → push draft
│   │
│   ├── config.py         Single-source configuration from .env
│   ├── models.py         Paper, Article, PipelineResult dataclasses
│   └── pipeline.py       One-click orchestrator + CLI
│
├── styles/               9 YAML style templates
├── app/                  Streamlit web UI
├── tests/                17 integration tests
├── docs/                 Outreach templates, API reference
└── PLAN.md               Product strategy & roadmap
```

---

## 📊 Benchmarks

All measurements on MacBook Pro M-series, DeepSeek V4 API, 20 Mbps connection.

| Pipeline Stage | Time | Notes |
|---------------|------|-------|
| Sci-Hub download | 2-8s | Depends on mirror speed (fastest: 0.44s response) |
| PDF extraction | 1-3s | Scales with page count and image density |
| Article generation | 15-40s | ~20K tokens; DeepSeek chat model |
| HTML rendering | 8-15s | ~16K output tokens |
| **Total (DOI → HTML)** | **30-60s** | Complete pipeline |

**Per-article cost:** ~¥0.3–0.5 via DeepSeek API (input + output tokens).

---

## 🔧 Configuration

All settings via environment variables or `.env` file. See `.env.example` for the full list.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RANGAO_LLM_API_KEY` | **Yes** | — | DeepSeek/OpenAI API key |
| `RANGAO_LLM_MODEL` | No | `deepseek-chat` | Model for article generation |
| `RANGAO_WECHAT_APPID` | For publish | — | WeChat Official Account AppID |
| `RANGAO_WECHAT_APPSECRET` | For publish | — | WeChat Official Account AppSecret |
| `RANGAO_SCIHUB_MIRROR` | No | `https://sci-hub.se` | Preferred Sci-Hub mirror |
| `RANGAO_OUTPUT_DIR` | No | `output/` | Where articles are saved |

---

## ❓ Troubleshooting

**"No PDF available" — download failed?**
1. Check Sci-Hub health: `python -m rangao.pipeline --mirror-status`
2. If all mirrors down, provide the PDF manually with `--pdf`
3. Try a different DOI — some papers aren't on Sci-Hub

**Article quality is off?**
1. Try a different style: `--style academic_general`
2. Edit the style YAML in `styles/` to match your voice
3. For better reasoning, set `RANGAO_LLM_MODEL=deepseek-reasoner` in `.env`

**Images in HTML don't display in WeChat?**
1. WeChat requires images hosted on their CDN or a whitelisted domain
2. Use `--publish` to auto-upload to WeChat CDN
3. Or manually upload images to WeChat's material library

---

## 🤝 Contributing

Issues and PRs welcome. See [PLAN.md](PLAN.md) for the roadmap.

Before submitting a PR:
```bash
pip install "rangao[test]"
python -m pytest tests/ -v
```

---

## 📜 License

MIT — see [LICENSE](LICENSE).

---

*Built for academic WeChat accounts that want their Sunday nights back.*
