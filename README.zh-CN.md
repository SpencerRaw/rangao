> 🌐 [English](README.md) | **中文**

# 🔥 燃稿 · RánGǎo

> **一篇论文进来，一篇公众号文章出去。**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-17%2F17%20passing-brightgreen.svg)](tests/)

燃稿是一个端到端自动化管道——把学术论文变成排版精美的微信公众号文章。不需要手动复制粘贴，不需要调试 CSS，不需要周日晚上熬夜赶稿。

```
DOI 或 PDF → [下载] → [提取] → [AI写稿] → [微信HTML] → [草稿箱]
```

**实测数据：** *Nature Communications* 论文 → 5000 字中文解读 → 微信兼容 HTML —— **54 秒，全自动。**

---

## ✨ 功能

| 步骤 | 做什么 |
|------|--------|
| 🔍 **文献发现** | Crossref API 按期刊/关键词/日期范围搜论文，AI 二次过滤相关性 |
| 📥 **论文下载** | 三级下载策略：Sci-Hub（4 镜像自动切换）→ Unpaywall OA → DOI 直链 |
| 📑 **内容提取** | PyMuPDF 拆出全文 + 所有图片 + 自动裁剪首页标题图 |
| ✍️ **AI 写稿** | DeepSeek（或任何 OpenAI 兼容 API）按你的风格模板写完整解读 |
| 🎨 **微信排版** | 生成微信兼容的内联样式 HTML——无 `<style>` 标签、无 class、踩过所有坑 |
| 📤 **一键发布** | 上传图片到微信 CDN（或免费图床降级），推送到公众号草稿箱 |

---

## 🚀 30 秒快速开始

```bash
git clone https://github.com/SpencerRaw/rangao.git
cd rangao
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
# 编辑 .env → 填入你的 DeepSeek API Key

# 输入 DOI，一键运行
python -m rangao.pipeline --doi 10.1038/s41467-020-15562-9
```

**你会看到：**
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
```

打开 `output/article.html` → 全选复制 → 粘贴到微信公众号编辑器。完成。

---

## 📋 命令参考

```bash
# 从 DOI 生成（自动下载论文）
python -m rangao.pipeline --doi 10.1038/s41467-020-15562-9

# 从本地 PDF
python -m rangao.pipeline --pdf paper.pdf

# 选择写作风格
python -m rangao.pipeline --pdf paper.pdf --style biomed_breakthrough

# 一键推送到微信草稿箱（需配置微信凭据）
python -m rangao.pipeline --doi 10.1038/... --publish

# 工具命令
python -m rangao.pipeline --list-styles      # 列出全部 9 套风格
python -m rangao.pipeline --mirror-status    # 检查 Sci-Hub 镜像健康状态
```

### Web 界面

```bash
pip install "rangao[web]"
streamlit run app/streamlit_app.py
```

上传 PDF → 选风格 → 一键生成 → 预览 HTML → 下载。不需要命令行。

---

## 🎨 风格模板（9 套内置）

写作风格是 `styles/` 下的 YAML 文件。每套模板编码了语气、结构、术语约定和排版规则，针对特定研究领域优化。

| 模板 | 领域 | 篇幅 |
|------|------|------|
| `academic_carbon_dots` | 碳点 / 纳米材料 | 3000-5000 字 |
| `academic_general` | 通用科学 | 2000-4000 字 |
| `biomed_breakthrough` | 生物医学 / 临床转化 | 3000-5000 字 |
| `energy_catalysis` | 电催化 / 电池 / CO₂还原 | 2500-4000 字 |
| `physics_quantum` | 凝聚态物理 / 量子材料 | 2500-4000 字 |
| `ai_ml_cs` | AI / 机器学习 / 计算机 | 2000-3500 字 |
| `earth_climate` | 气候 / 地质 / 生态 | 2000-3500 字 |
| `social_science` | 经济学 / 心理学 / 政策 | 1500-3000 字 |
| `quick_news` | 快讯简报 | 800-1500 字 |

**自建模板：**

```yaml
# styles/my_journal.yaml
name: "我的期刊风格"
language: zh-CN
prompt: |
  以轻松、引人入胜的语气写作。结构：研究背景→核心发现→领域影响。
  始终提及机构和通讯作者。使用第三人称。
```

---

## 🏗️ 架构

```
rangao/
├── src/rangao/
│   ├── discover/         Crossref API 搜索 + AI 论文过滤
│   │   ├── crossref.py       期刊×关键词分页搜索
│   │   └── filter.py         去重 + 剔除非研究文章 + LLM 相关性验证
│   │
│   ├── download/         PDF 获取（三级策略 + 降级链）
│   │   ├── scihub.py         8 镜像池 + 并发健康探测 + 5 种 URL 提取策略
│   │   ├── direct.py         Unpaywall OA + doi.org 直链
│   │   └── doi_fetcher.py    Crossref 元数据 + OpenAlex 引用追踪
│   │
│   ├── extract/          PDF → 结构化内容
│   │   ├── pdf_extractor.py  PyMuPDF 提取文字 + 逐页图片
│   │   └── header_cropper.py 首页标题区智能裁剪
│   │
│   ├── generate/         AI 文章生成
│   │   ├── writer.py         LLM 调用 + 分段 prompt 工程
│   │   └── style_engine.py   YAML 风格加载器 + 内置后备
│   │
│   ├── render/           Markdown → 微信兼容 HTML
│   │   ├── wechat_html.py    LLM 驱动的转换 + 实战验证的微信排版规则
│   │   └── inline_styler.py  确定性 CSS→内联样式转换器（无需 LLM）
│   │
│   ├── publish/          微信公众号集成
│   │   ├── wechat_api.py     Token 管理 + 素材上传 + 草稿 API
│   │   ├── image_uploader.py 微信 → sm.ms → imgbb → data URI（三级降级）
│   │   └── draft_publisher.py 完整发布流程：上传图片 → 推送草稿
│   │
│   ├── config.py         从 .env 统一加载配置
│   ├── models.py         Paper, Article, PipelineResult 数据类
│   └── pipeline.py       一键编排器 + CLI
│
├── styles/               9 套 YAML 风格模板
├── app/                  Streamlit 网页界面
├── tests/                17 个集成测试
├── docs/                 Outreach 模板、API 参考
└── PLAN.md               产品策略与路线图
```

---

## 📊 性能基准

MacBook Pro M 系列 + DeepSeek V4 API + 20 Mbps 网络。

| 管道阶段 | 耗时 | 说明 |
|---------|------|------|
| Sci-Hub 下载 | 2-8s | 取决于镜像速度（最快 0.44s 响应） |
| PDF 提取 | 1-3s | 随页数和图片密度增加 |
| 文章生成 | 15-40s | ~20K tokens；DeepSeek chat 模式 |
| HTML 渲染 | 8-15s | ~16K 输出 tokens |
| **总计（DOI→HTML）** | **30-60s** | 完整管道 |

**单篇成本：** DeepSeek API 约 ¥0.3-0.5（输入+输出 tokens）。

---

## 🔧 配置

所有配置通过环境变量或 `.env` 文件设置。详见 `.env.example`。

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `RANGAO_LLM_API_KEY` | **是** | — | DeepSeek/OpenAI API 密钥 |
| `RANGAO_LLM_MODEL` | 否 | `deepseek-chat` | 文章生成模型 |
| `RANGAO_WECHAT_APPID` | 发布时需要 | — | 微信公众号 AppID |
| `RANGAO_WECHAT_APPSECRET` | 发布时需要 | — | 微信公众号 AppSecret |
| `RANGAO_SCIHUB_MIRROR` | 否 | `https://sci-hub.se` | 首选 Sci-Hub 镜像 |
| `RANGAO_OUTPUT_DIR` | 否 | `output/` | 文章输出目录 |

---

## ❓ 常见问题

**"No PDF available"——下载失败？**
1. 检查 Sci-Hub 状态：`python -m rangao.pipeline --mirror-status`
2. 如果所有镜像不可用，手动提供 PDF：`--pdf`
3. 尝试其他 DOI——部分论文 Sci-Hub 未收录

**文章质量不理想？**
1. 换风格试试：`--style academic_general`
2. 编辑 `styles/` 下的 YAML 文件，调整语气和结构
3. 需要更强的推理能力：`.env` 中设 `RANGAO_LLM_MODEL=deepseek-reasoner`

**HTML 图片在微信里不显示？**
1. 微信要求图片托管在微信 CDN 或白名单域名上
2. 用 `--publish` 自动上传到微信 CDN
3. 或手动上传图片到微信素材库

**Sci-Hub 镜像都挂了怎么办？**
1. 编辑 `.env`：`RANGAO_SCIHUB_MIRROR=https://新镜像域名`
2. 或者直接提供 PDF：`--pdf paper.pdf`
3. 镜像健康数据缓存 24 小时，`--mirror-status` 会实时探测

---

## 🤝 贡献

欢迎 Issue 和 PR。路线图见 [PLAN.md](PLAN.md)。

提交 PR 前：
```bash
pip install "rangao[test]"
python -m pytest tests/ -v
```

---

## 📜 许可证

MIT — 详见 [LICENSE](LICENSE)。

---

*为想夺回周日夜晚的学术公众号运营者而建。*
