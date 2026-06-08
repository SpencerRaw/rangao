# 燃稿 (RánGǎo) — AI-Powered WeChat Article Pipeline

> **Tagline**: One paper in, one WeChat article out.  
> **Status**: MVP — multi-step pipeline functional, auto-publish via draft API in development.

---

## Thesis

学术公众号运营者每周花 4-8 小时把一篇论文变成一篇排版精美的公众号文章：下载PDF、读论文、写解读、配图、调HTML、上传素材、复制粘贴到微信后台。燃稿把这个流程压缩到一条命令：**输入DOI或PDF，输出微信草稿箱里的待发文章。**

Why now? LLM 的文本生成质量已经到了可以写学术解读的水平（DeepSeek, Claude），微信开放了草稿箱 API，Sci-Hub 解决了论文下载的付费墙。三股力量交汇。

---

## Core Pipeline

```
DOI/PDF → [Discover] → [Download] → [Extract] → [Generate] → [Render] → [Publish]
          文献检索       论文下载        图文拆分       AI写稿       微信HTML      推草稿箱
```

| Stage | Input | Output | Engine |
|-------|-------|--------|--------|
| Discover | Keywords, journals | Paper list (CSV) | Crossref API + DeepSeek filter |
| Download | DOI | PDF file | Sci-Hub / Unpaywall / direct |
| Extract | PDF | text + images + header | PyMuPDF |
| Generate | Full text + style | Markdown article | DeepSeek / Claude / OpenAI |
| Render | Markdown | WeChat-compatible HTML | DeepSeek + cssutils inline-styler |
| Publish | HTML + images | WeChat draft box | wechatpy SDK |

---

## Architecture

```
rangao/
├── PLAN.md                    ← this file
├── README.md / README.zh-CN.md
├── .env.example               ← template, never committed
├── .gitignore
├── requirements.txt
├── src/rangao/
│   ├── config.py              ← unified config from .env
│   ├── models.py              ← Paper, Article, Style dataclasses
│   ├── discover/              ← paper discovery (Crossref, web scraping)
│   ├── download/              ← PDF acquisition (Sci-Hub, Unpaywall)
│   ├── extract/               ← PDF → text + images
│   ├── generate/              ← LLM article writing
│   ├── render/                ← MD → WeChat inline-style HTML
│   ├── publish/               ← WeChat API integration
│   └── pipeline.py            ← one-click orchestration
├── app/streamlit_app.py       ← web UI (demo/prototype)
├── styles/                    ← user-editable style templates
└── tests/
```

### Design principles

1. **Each stage is independently callable** — you can skip to any step
2. **Style is data, not code** — writing style templates in `styles/*.yaml`, easy to swap
3. **Dual-track** — real API when credentials present, simulated fallback for demo
4. **No hardcoded secrets** — everything from `.env`
5. **Plain Python, no framework** — single-file install, zero-config where possible

---

## Competitive Landscape

| Project | Scope | Gap |
|---------|-------|-----|
| weflow (twwch) | Full pipeline, AI writing + draft publish | No Sci-Hub, no multi-style |
| wechat-publisher (jiji262) | Auto-creation + publish | Generic articles, not academic |
| wechatpy (wechatpy) | WeChat SDK only | No pipeline, just API wrappers |
| **燃稿** | **End-to-end academic paper → WeChat draft** | **Vertical focus + Sci-Hub + multi-style** |

---

## Monetization (Hormozi Value Equation)

```
Value = (Dream Outcome × Perceived Likelihood) / (Time Delay × Effort & Sacrifice)
```

| Lever | 燃稿 |
|-------|------|
| ⬆️ Dream Outcome | "I wake up, my WeChat draft is ready" |
| ⬆️ Perceived Likelihood | Open-source + live demo, see it work before paying |
| ⬇️ Time Delay | 6 manual steps → 1 command, 4 hours → 3 minutes |
| ⬇️ Effort & Sacrifice | User provides DOI, everything else automated |

### Revenue stages (ai-money-2026 aligned)

1. **Freelance** (now): Ghost-write articles ¥500-2000/piece
2. **Consulting** (Q3 2026): Set up pipeline for labs, ¥5000-20K/project
3. **SaaS** (Q4 2026): Monthly subscription ¥99-299, auto-publish
4. **Education** (2027): Course "Academic WeChat AI Automation"

---

## MVP Scope (this repo)

- [x] Paper discovery via Crossref API + AI filtering
- [x] PDF extraction (text + images + header crop)
- [x] AI article generation with configurable style
- [x] WeChat-compatible inline-style HTML rendering
- [x] Image upload to WeChat permanent materials
- [ ] Sci-Hub PDF download
- [ ] WeChat draft box auto-publish
- [ ] Multi-style template library

---

## Roadmap

| Milestone | Target | Deliverable |
|-----------|--------|-------------|
| M1: Core Pipeline | Week 1-2 | DOI→HTML, all stages function |
| M2: Auto-Publish | Week 3 | Draft box push works end-to-end |
| M3: Web UI | Week 4 | Streamlit demo for customers |
| M4: First Paying User | Month 2 | ¥500/article ghost-writing |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Sci-Hub goes down | Fallback to Unpaywall + manual download prompt |
| WeChat API rate limits | Token caching, exponential backoff |
| LLM hallucination in articles | Style enforces fact-check + mandatory DOI link |
| IP whitelist keeps changing | VPS with fixed IP (¥30/mo) or ngrok tunnel |
| Academic clients won't pay | Target journal editors + science media, not professors |

---

## Why Now

- DeepSeek V4 quality matches GPT-4 for Chinese academic writing at 1/10th cost
- WeChat opened Draft API (2024) — no more manual copy-paste
- Sci-Hub still operational — paywall bypass works
- AI content tools are exploding (weflow, wechat-publisher) — market timing is right
- 燃稿's vertical focus (academic papers only) creates defensible positioning

---

## Inspirations

- Alex Hormozi, *$100M Offers* — value equation + grand slam offer design
- Nate Herk, *AI Money 2026* — 4-stage AI monetization ladder
- Sahil Lavingia, *The Minimalist Entrepreneur* — profit > growth, ship fast
- `twwch/weflow` — reference architecture for WeChat pipeline
- `wechatpy/wechatpy` — battle-tested WeChat SDK
- The original `aiWechatFlow/` scripts that proved the concept works
