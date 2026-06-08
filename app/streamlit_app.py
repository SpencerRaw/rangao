"""燃稿 (RánGǎo) — Streamlit Web UI.

Interactive demo: upload a PDF or enter a DOI, pick a style,
and generate a WeChat article in one click.

Run:
    cd rangao && streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import streamlit as st

from rangao.config import get_config
from rangao.models import ArticleStyle
from rangao.pipeline import run_pipeline


st.set_page_config(
    page_title="燃稿 · RánGǎo",
    page_icon="🔥",
    layout="wide",
)

st.title("🔥 燃稿 · RánGǎo")
st.caption("一篇论文进来，一篇公众号文章出去。One paper in, one WeChat article out.")

# ---- Sidebar: Configuration ----
with st.sidebar:
    st.header("⚙️ 配置")
    config = get_config()

    st.markdown(f"LLM: `{config.llm_model}` @ `{config.llm_base_url}`")
    st.markdown(f"Provider: `{config.llm_provider}`")

    if config.has_wechat_credentials:
        st.success("✅ WeChat credentials found")
    else:
        st.warning("⚠️ WeChat credentials not set — publish disabled")

    st.divider()

    auto_publish = st.checkbox("自动发布到微信草稿箱", value=False, disabled=not config.has_wechat_credentials)
    skip_download = st.checkbox("跳过论文下载（使用已有PDF）", value=False)

    st.divider()
    st.caption("Made with ❤️ | [GitHub](https://github.com/SpencerRaw/rangao)")

# ---- Main Content ----
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📄 输入")
    input_mode = st.radio("选择输入方式", ["📎 上传 PDF", "🔗 输入 DOI", "📋 粘贴文本"], horizontal=True)

    pdf_file = None
    doi = ""
    pasted_text = ""

    if input_mode == "📎 上传 PDF":
        pdf_file = st.file_uploader("上传论文 PDF", type=["pdf"])
        if pdf_file:
            st.success(f"已上传: {pdf_file.name} ({pdf_file.size / 1024:.0f} KB)")
    elif input_mode == "🔗 输入 DOI":
        doi = st.text_input("DOI", placeholder="10.1002/adfm.2025075092")
    else:
        pasted_text = st.text_area("粘贴论文全文", height=300, placeholder="将论文全文粘贴到这里...")

with col2:
    st.subheader("🎨 风格与设置")
    style_name = st.selectbox(
        "写作风格",
        ["academic_carbon_dots", "academic_general"],
        format_func=lambda x: {
            "academic_carbon_dots": "碳点人学术解读",
            "academic_general": "通用学术科普",
        }.get(x, x),
    )
    st.caption("风格模板位于 `styles/` 目录，可自定义编辑")

# ---- Action Button ----
st.divider()

can_generate = bool(pdf_file or doi or pasted_text)
generate_btn = st.button(
    "🚀 生成公众号文章",
    type="primary",
    disabled=not can_generate,
    use_container_width=True,
)

if generate_btn:
    # Save uploaded PDF to temp
    pdf_path = ""
    if pdf_file:
        temp_dir = config.output_dir / "upload"
        temp_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = str(temp_dir / pdf_file.name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.getbuffer())

    status = st.status("正在处理...", expanded=True)

    with status:
        result = run_pipeline(
            doi=doi,
            pdf_path=pdf_path,
            style=style_name,
            auto_publish=auto_publish,
            skip_download=skip_download,
        )

    # ---- Show Results ----
    if result.article:
        st.success(f"✅ 文章生成完成！耗时 {result.duration_seconds:.1f}s")

        # Tabs for preview
        tab1, tab2, tab3 = st.tabs(["📝 Markdown", "🎨 HTML 预览", "📊 详情"])

        with tab1:
            if result.article:
                st.text_area("Markdown", result.article.markdown, height=600)

        with tab2:
            if result.rendered:
                st.components.v1.html(result.rendered.html, height=800, scrolling=True)
            else:
                st.info("HTML 尚未生成")

        with tab3:
            if result.article:
                st.metric("字数", len(result.article.markdown))
                st.metric("Tokens", result.article.tokens_used)
                st.metric("模型", result.article.model)
            if result.published:
                if result.published.success:
                    st.success(f"已推送到草稿箱！Draft ID: `{result.published.draft_id}`")
                else:
                    st.error(f"发布失败: {result.published.error}")

        # Download buttons
        st.divider()
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            if result.article:
                st.download_button(
                    "⬇️ 下载 Markdown",
                    result.article.markdown,
                    file_name="article.md",
                    mime="text/markdown",
                )
        with dl_col2:
            if result.rendered:
                st.download_button(
                    "⬇️ 下载 HTML",
                    result.rendered.html,
                    file_name="article.html",
                    mime="text/html",
                )

    elif result.errors:
        st.error("❌ 处理失败")
        for err in result.errors:
            st.error(f"- {err}")
    else:
        st.warning("⚠️ 无输出。请检查输入。")
