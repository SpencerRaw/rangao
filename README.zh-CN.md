> 🌐 [English](README.md) | **中文**

# 🔥 燃稿 · RánGǎo

**一篇论文进来，一篇公众号文章出去。**

燃稿是一个端到端自动化管道：把学术论文变成排版精美的微信公众号文章——一条命令，全自动。

```
DOI/PDF → [下载] → [提取] → [AI写稿] → [微信HTML] → [草稿箱]
```

## ✨ 功能

- 🔍 **文献发现** — Crossref API 按期刊+关键词搜论文
- 📥 **论文下载** — Sci-Hub / Unpaywall / DOI直链，多源尝试
- 📑 **内容提取** — PyMuPDF 拆出文字+图片+头图
- ✍️ **AI写稿** — DeepSeek 按你的风格写完整解读文章
- 🎨 **微信排版** — 生成微信兼容的内联样式HTML（踩过所有坑）
- 📤 **一键发布** — 推送到微信公众号草稿箱

## 🚀 快速开始

```bash
# 1. 克隆
git clone https://github.com/SpencerRaw/rangao.git
cd rangao

# 2. 安装
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. 配置
cp .env.example .env
# 编辑 .env → 填入 DeepSeek API Key

# 4. 运行！
python -m rangao.pipeline --doi 10.1002/adfm.2025075092
```

## 📋 使用方式

```bash
# 从 DOI 生成
python -m rangao.pipeline --doi 10.1002/adfm.2025075092

# 从本地 PDF
python -m rangao.pipeline --pdf paper.pdf

# 自动发布到微信草稿箱（需要配置微信凭据）
python -m rangao.pipeline --doi 10.1002/adfm.2025075092 --publish

# 换风格
python -m rangao.pipeline --pdf paper.pdf --style academic_general
```

## 🖥️ Web界面

```bash
streamlit run app/streamlit_app.py
```

打开浏览器：上传PDF → 选风格 → 一键生成 → 预览 → 下载。

## 🎨 风格模板

写作风格是 `styles/` 下的 YAML 文件。编辑 `academic_carbon_dots.yaml` 或新建你自己的：

```yaml
name: "我的期刊风格"
language: zh-CN
prompt: |
  以轻松、引人入胜的语气写作...
```

## 🏗️ 架构

```
rangao/
├── src/rangao/
│   ├── discover/    ← 文献检索 (Crossref)
│   ├── download/    ← PDF下载 (Sci-Hub)
│   ├── extract/     ← PDF→文字+图片
│   ├── generate/    ← AI写稿
│   ├── render/      ← MD→微信HTML
│   ├── publish/     ← 微信API (草稿箱)
│   └── pipeline.py  ← 一键管道
├── styles/          ← 风格模板
├── app/             ← Streamlit网页UI
└── PLAN.md          ← 完整产品计划
```

## 🔧 环境变量

| 变量 | 必需 | 说明 |
|----------|----------|-------------|
| `RANGAO_LLM_API_KEY` | 是 | DeepSeek/OpenAI API密钥 |
| `RANGAO_WECHAT_APPID` | 发布时需要 | 微信公众号AppID |
| `RANGAO_WECHAT_APPSECRET` | 发布时需要 | 微信公众号AppSecret |
| `RANGAO_SCIHUB_MIRROR` | 否 | Sci-Hub镜像地址 |

详见 `.env.example`。

## 🤝 贡献

欢迎 Issue 和 PR。路线图见 [PLAN.md](PLAN.md)。

## 📜 许可证

MIT License — 详见 [LICENSE](LICENSE)。

---

*为想夺回周日夜晚的学术公众号运营者而建。*
