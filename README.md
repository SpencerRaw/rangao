> 🌐 [中文文档](README.zh-CN.md) | **English**

# 🔥 燃稿 · RánGǎo

**One paper in, one WeChat article out.**

RánGǎo is an end-to-end pipeline that turns an academic paper into a beautifully formatted WeChat Official Account article — with a single command.

```
DOI/PDF → [Download] → [Extract] → [AI Write] → [WeChat HTML] → [Draft Box]
```

## ✨ What It Does

- 🔍 **Discover** — Search Crossref for recent papers by journal + keywords
- 📥 **Download** — Get PDFs from Sci-Hub, Unpaywall, or direct DOI
- 📑 **Extract** — Pull out text + images + header from PDFs
- ✍️ **Generate** — AI writes a full WeChat article following your style
- 🎨 **Render** — Converts to WeChat-compatible inline-style HTML (no `<style>` tags!)
- 📤 **Publish** — Push directly to your WeChat draft box

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/SpencerRaw/rangao.git
cd rangao

# 2. Install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env → add your DeepSeek API key

# 4. Run!
python -m rangao.pipeline --doi 10.1002/adfm.2025075092
```

## 📋 Usage

```bash
# From a DOI
python -m rangao.pipeline --doi 10.1002/adfm.2025075092

# From a local PDF
python -m rangao.pipeline --pdf paper.pdf

# With auto-publish to WeChat (requires WeChat credentials)
python -m rangao.pipeline --doi 10.1002/adfm.2025075092 --publish

# Choose a different style
python -m rangao.pipeline --pdf paper.pdf --style academic_general
```

## 🖥️ Web UI

```bash
streamlit run app/streamlit_app.py
```

Opens a browser interface: upload PDF → pick style → generate → preview → download.

## 🎨 Style Templates

Writing styles are YAML files in `styles/`. Edit `academic_carbon_dots.yaml` or create your own:

```yaml
name: "My Journal Style"
language: zh-CN
prompt: |
  Write in a casual, engaging tone...
images:
  header: "header.png"
```

## 🏗️ Architecture

```
rangao/
├── src/rangao/
│   ├── discover/    ← Paper search (Crossref)
│   ├── download/    ← PDF acquisition (Sci-Hub)
│   ├── extract/     ← PDF → text + images
│   ├── generate/    ← AI article writing
│   ├── render/      ← MD → WeChat HTML
│   ├── publish/     ← WeChat API (drafts)
│   └── pipeline.py  ← One-click orchestration
├── styles/          ← Writing style templates
├── app/             ← Streamlit web UI
└── PLAN.md          ← Full product plan
```

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `RANGAO_LLM_API_KEY` | Yes | Your DeepSeek/OpenAI API key |
| `RANGAO_WECHAT_APPID` | For publish | WeChat Official Account AppID |
| `RANGAO_WECHAT_APPSECRET` | For publish | WeChat Official Account AppSecret |
| `RANGAO_SCIHUB_MIRROR` | No | Sci-Hub mirror URL |

See `.env.example` for all options.

## 🤝 Contributing

Issues and PRs welcome. See [PLAN.md](PLAN.md) for roadmap.

## 📜 License

MIT License — see [LICENSE](LICENSE).

---

*Built for academic WeChat accounts that want their Sunday nights back.*
