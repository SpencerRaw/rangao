"""WeChat HTML renderer — converts Markdown to WeChat-compatible HTML.

Uses DeepSeek to generate inline-style HTML that works in WeChat's
restricted editor (no <style> tags, no external CSS, no class-based styling).
"""

from __future__ import annotations

import re
from pathlib import Path

from openai import OpenAI

from ..config import get_config
from ..models import Article, RenderedArticle


def md_to_wechat_html(
    article: Article,
    output_path: str = "",
    model: str = "",
) -> RenderedArticle:
    """Convert a Markdown article to WeChat-compatible inline-style HTML.

    Uses an LLM with a detailed prompt that encodes all WeChat quirks
    (learned through painful trial and error — see playground.txt).

    Args:
        article: The generated article (must have markdown content).
        output_path: Where to save the HTML. Auto-generated if empty.
        model: LLM model override.

    Returns:
        RenderedArticle with HTML and metadata.
    """
    config = get_config()

    if not output_path:
        output_path = str(config.output_dir / "article.html")

    html = _generate_html_via_llm(article.markdown, model or config.llm_model)

    # Post-process: extract clean HTML
    html = _clean_html_output(html)

    # Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(html, encoding="utf-8")

    return RenderedArticle(article=article, html=html)


def _generate_html_via_llm(markdown: str, model: str) -> str:
    """Call LLM to convert markdown to WeChat HTML."""
    config = get_config()
    client = OpenAI(api_key=config.llm_api_key, base_url=config.llm_base_url)

    prompt = f"""
You are a WeChat Official Account typesetting expert. Convert the following markdown into WeChat-compatible HTML.

⚠️ WeChat STRICT restrictions:
- NO <style> tags or external stylesheets
- NO class or id for visual styling (class has zero effect in WeChat)
- ALL fonts, colors, margins, borders, backgrounds MUST be inline style attributes

Follow these rules precisely:

### 1. Overall Structure
Wrap the entire article in:
```html
<div style="max-width: 677px; margin: 0 auto; padding: 8px; background: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <!-- article here -->
</div>
```

### 2. Body Paragraphs
Each paragraph uses `<p style="...">` with:
- font-size: 16px; color: #333333; line-height: 1.8; text-align: justify; text-indent: 2em; margin-bottom: 1em

### 3. Section Headers (e.g., "背景介绍", "图文导览", "结论与展望")
MUST use this exact structure:
```html
<p style="text-align:center; margin:10px 0;">
  <span style="background-color:#C93C3C; color:#FFFFFF; font-size:16px; font-weight:bold; padding:6px 32px; display:inline-block; border-radius:4px;">背景介绍</span>
</p>
```
NEVER use <div> wrapper, NEVER use margin:auto.

### 4. Images
All <img> tags MUST have:
- border: 2px dashed #AAAAAA; border-radius: 8px; display: block; margin: 20px auto; max-width: 100%
- Image captions below: `<div style="font-size:14px; color:#888888; text-align:center; margin-top:-10px; margin-bottom:20px;">Figure N. Description</div>`
- Images wrapped in `<section style="margin:0 3%;">` for WeChat compatibility

### 5. Headings
- h1 (main title): font-size:22px; color:#222222; font-weight:bold; text-align:center; margin-bottom:20px
- h2: color:#349971; font-weight:bold; margin:1.5em 3%; border-bottom:1px solid #eee; font-size:20px

### 6. Keywords Highlighting (ONLY in "背景介绍" section)
Highlight complete sentences containing these keywords:
- RED (#D32F2F): 提出, 设计, 合成, 构建, 策略, 制备
- GREEN (#388E3C): 揭示, 证实, 机制, 催化, 清除, 动力学, 增强
- BLUE (#1976D2): 实现, 达成, 杀伤, 抑制, 诊疗, 应用
Use `<span style="color:#D32F2F; font-weight:bold;">sentence...</span>`

### 7. Reference Section
Use `<section>` (NOT <div>) for the grey background container:
```html
<section style="background-color:#F5F5F5; padding:15px; border-radius:4px; margin:10px 0;">
  <p style="font-size:14px; color:#666666; text-indent:0; margin-bottom:0.5em;"><strong>Paper Link:</strong></p>
  <p style="font-size:14px; color:#666666; text-indent:0; margin-bottom:0.5em;">...</p>
</section>
```

### 8. Other Rules
- Links: `<a style="color:#1976D2; text-decoration:none; border-bottom:1px solid #1976D2;" href="...">text</a>`
- Blockquotes: use `<blockquote style="line-height:1.8em; text-align:left; margin:auto 3%; border:2px dotted #ddd; border-radius:0.7em; color:#999; padding:0 10px;">`
- Tables: wrapped in `<section class="tbl-wrapper" style="margin:0 3%;">` with inline border styles
- ALL visual blocks (cards, info boxes, references) use `<section>`, NEVER `<div>`
- Output ONLY the raw HTML code — no ```html markers, no explanations

Convert this markdown:
---
{markdown}
---
"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You output WeChat-compatible HTML only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )
    return response.choices[0].message.content


def _clean_html_output(raw: str) -> str:
    """Extract clean HTML from LLM output (strip markdown fences, fix structure)."""
    # Remove ```html ... ``` wrappers
    raw = re.sub(r"```html\s*", "", raw)
    raw = re.sub(r"```\s*$", "", raw)

    # Extract <html>...</html> or <!DOCTYPE...>...</html>
    match = re.search(r"(<!DOCTYPE html>.*?</html>)", raw, re.DOTALL | re.IGNORECASE)
    if match:
        raw = match.group(1)
    else:
        match = re.search(r"(<html.*?>.*?</html>)", raw, re.DOTALL | re.IGNORECASE)
        if match:
            raw = match.group(1)

    # Ensure DOCTYPE and charset
    if "<!DOCTYPE html>" not in raw.lower():
        raw = f'<!DOCTYPE html>\n<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head><body>{raw}</body></html>'

    return raw.strip()
