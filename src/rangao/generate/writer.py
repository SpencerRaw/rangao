"""AI article writer — generates WeChat articles from paper content.

Uses DeepSeek (or compatible OpenAI API) to generate academic
WeChat articles following a configurable style template.
"""

from __future__ import annotations

from pathlib import Path

from openai import OpenAI

from ..config import get_config
from ..models import Article, ArticleStyle, ExtractedContent, Paper
from .style_engine import StyleEngine


def generate_article(
    content: ExtractedContent,
    style_name: str = "academic_carbon_dots",
    model: str = "",
) -> Article:
    """Generate a WeChat article from extracted paper content.

    Args:
        content: Extracted PDF content (text + images).
        style_name: Name of the style template to use
            (matches a YAML file in styles/).
        model: LLM model override. Uses config default if empty.

    Returns:
        Article with generated markdown.
    """
    config = get_config()

    if not model:
        model = config.llm_model

    # Load style
    style = StyleEngine(config.styles_dir).load(style_name)

    # Build system prompt from style
    system_prompt = _build_system_prompt(style)

    # Build user prompt with paper content and image list
    user_prompt = _build_user_prompt(content)

    # Call LLM
    client = OpenAI(api_key=config.llm_api_key, base_url=config.llm_base_url)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=config.llm_temperature,
        max_tokens=config.llm_max_tokens,
    )

    markdown = response.choices[0].message.content

    article = Article(
        paper=content.paper or Paper(title="Untitled", doi=""),
        markdown=markdown,
        style=ArticleStyle.ACADEMIC_GENERAL,
        model=model,
        tokens_used=response.usage.total_tokens if response.usage else 0,
    )

    return article


def _build_system_prompt(style: dict) -> str:
    """Build system prompt from style template."""
    style_text = style.get("prompt", "")
    images_section = style.get("images", {})

    # Build image handling rules
    image_rules = ""
    if images_section:
        header_img = images_section.get("header", "")
        if header_img:
            image_rules += f"- Article header should include the title card image: ![{header_img}]({header_img})\n"

    prompt = f"""You are a professional academic WeChat article writer. Generate a complete article based on the provided paper and style.

【Style Requirements】
{style_text}

【Image Rules】
{image_rules}
- Insert images naturally where the content they depict is discussed.
- Each image MUST have a caption in the format: ![{style.get('figure_caption_format', 'Figure N. Description')}](image_path)
- Do NOT list all images at the end of the article.

【Output Format】
- Output ONLY the complete Markdown article.
- Do NOT add any explanations, notes, or commentary outside the article.
- Use proper Markdown: ## for sections, **bold** for emphasis, ![](path) for images.
"""

    return prompt


def _build_user_prompt(content: ExtractedContent) -> str:
    """Build user prompt with paper text and image list."""
    image_list = "\n".join(
        f"- {img}" for img in content.images
        if not img.name.startswith("page1_")  # skip page 1 junk images
    ) if content.images else "(no images available)"

    prompt = f"""Here is the full paper text:

{content.full_text}

Available images (in order):
{image_list}

Please generate the complete WeChat article following the style guidelines.
"""
    return prompt
