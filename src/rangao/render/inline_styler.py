"""Programmatic inline style converter.

A deterministic, non-LLM approach to convert HTML with <style> tags
into WeChat-compatible inline-styled HTML.

Based on the proven convert_to_wechat.py logic.
"""

from __future__ import annotations

import cssutils
from bs4 import BeautifulSoup

# Suppress cssutils log noise
cssutils.log.setLevel(50)


def inline_all_styles(html: str) -> str:
    """Convert an HTML string with <style> tags to fully inline-styled HTML.

    Handles:
    - CSS rule extraction and inlining
    - <ul>/<ol>/<li> → <p> manual lists
    - Table, image, code block enhancement
    - WeChat-compatible base styles on headings, paragraphs, etc.
    - Cleanup of class/id attributes and external stylesheet links
    """
    soup = BeautifulSoup(html, "lxml")

    # 1. Parse and inline CSS from <style> tags
    _inline_css_from_style_tags(soup)

    # 2. Convert list structures
    _convert_lists(soup)

    # 3. Enhance code blocks, tables, images
    _enhance_code_blocks(soup)
    _enhance_tables(soup)
    _enhance_images(soup)

    # 4. Apply base styles to common elements
    _apply_base_styles(soup)

    # 5. Clean up
    _clean_up(soup)

    # 6. Wrap body in a container div
    body = soup.find("body")
    if body:
        wrapper = soup.new_tag("div", style=(
            "color:#555; font-family:Consolas, Menlo, monospace; "
            "font-size:16px; letter-spacing:0.05em; margin:auto 20%; text-align:justify;"
        ))
        wrapper.extend(body.contents)
        body.append(wrapper)

    # Ensure charset meta
    head = soup.find("head")
    if not head:
        head = soup.new_tag("head")
        soup.html.insert(0, head) if soup.html else None
    if head and not head.find("meta", charset=True):
        meta = soup.new_tag("meta", charset="UTF-8")
        head.insert(0, meta)

    return str(soup)


def _inline_css_from_style_tags(soup):
    """Parse <style> tags and apply rules as inline styles."""
    for style_tag in soup.find_all("style"):
        css_text = style_tag.string or ""
        rules = _parse_css(css_text)
        for selector, props in rules:
            try:
                elements = soup.select(selector)
            except Exception:
                continue
            for el in elements:
                _apply_styles_to_element(el, props)
        style_tag.decompose()


def _parse_css(style_str: str) -> list:
    sheet = cssutils.parseString(style_str)
    rules = []
    for rule in sheet:
        if rule.type == rule.STYLE_RULE:
            selector = rule.selectorText
            props = {prop.name: prop.value for prop in rule.style}
            rules.append((selector, props))
    return rules


def _apply_styles_to_element(el, props: dict):
    if not props:
        return
    existing = el.get("style", "")
    new_style = ";".join(f"{k}:{v}" for k, v in props.items())
    if existing:
        existing = existing.rstrip(";") + ";"
    el["style"] = existing + new_style


def _convert_lists(soup):
    """Convert ul/ol/li to <p>-based manual lists."""
    for ul in soup.find_all(["ul", "ol"]):
        is_ordered = ul.name == "ol"
        items = ul.find_all("li", recursive=False)
        if not items:
            continue
        for idx, li in enumerate(items, start=1):
            text = li.get_text().strip()
            prefix = "○ " if not is_ordered else f"{idx}. "
            p = soup.new_tag("p")
            p.string = prefix + text
            p["style"] = "line-height:1.8em; text-align:left; margin:0.5em 3%;"
            ul.insert_before(p)
        ul.decompose()


def _enhance_code_blocks(soup):
    for pre in soup.find_all("pre"):
        pre["style"] = pre.get("style", "") + (
            ";background-color:white; font-size:14px; display:block; line-height:1.7em;"
        )
        for code in pre.find_all("code"):
            code["style"] = code.get("style", "") + (
                ";border:1px solid #ddd; border-radius:3px; display:block; "
                "padding:3px; white-space:pre; overflow:auto; font-size:14px; "
                "margin:auto 3%; color:#999;"
            )


def _enhance_tables(soup):
    for table in soup.find_all("table"):
        section = soup.new_tag("section", style="margin:0 3%;", **{"class": "tbl-wrapper"})
        table.wrap(section)
        table["style"] = table.get("style", "") + (
            ";margin:0 auto; border:0; border-collapse:collapse; border-spacing:0; "
            "font:inherit; font-size:1em; padding:0;"
        )
        for tr in table.find_all("tr"):
            tr["style"] = tr.get("style", "") + (
                ";background-color:white; border:0; border-top:1px solid #ccc; "
                "margin:0; padding:0;"
            )
        for th in table.find_all("th"):
            th["style"] = th.get("style", "") + (
                ";border:1px solid #349971; font-size:14px; margin:0; "
                "padding:5px 10px; background-color:#349971; color:#eee; font-weight:bold;"
            )
        for td in table.find_all("td"):
            td["style"] = td.get("style", "") + (
                ";border:1px solid #ccc; font-size:14px; margin:0; padding:5px 10px;"
            )


def _enhance_images(soup):
    for img in soup.find_all("img"):
        img["style"] = img.get("style", "") + ";display:block; margin:0 auto; max-width:100%;"
        if img.parent and img.parent.name != "section":
            section = soup.new_tag("section", style="margin:0 3%;", **{"class": "img-wrapper"})
            img.wrap(section)


def _apply_base_styles(soup):
    for p in soup.find_all("p"):
        p["style"] = p.get("style", "") + ";line-height:1.8em; text-align:left; margin:1.5em 3%;"
    for h1 in soup.find_all("h1"):
        h1["style"] = h1.get("style", "") + (
            ";color:#349971; font-weight:bold; margin:1.5em 3%; "
            "border-bottom:1px solid #ddd; font-size:24px; text-align:left;"
        )
    for h2 in soup.find_all("h2"):
        h2["style"] = h2.get("style", "") + (
            ";color:#349971; font-weight:bold; margin:1.5em 3%; "
            "border-bottom:1px solid #eee; font-size:20px; text-align:left;"
        )
    for bq in soup.find_all("blockquote"):
        bq["style"] = bq.get("style", "") + (
            ";line-height:1.8em; text-align:left; margin:auto 3%; "
            "border:2px dotted #ddd; border-radius:0.7em; color:#999; padding:0 10px;"
        )
    for a in soup.find_all("a"):
        a["style"] = a.get("style", "") + ";color:#349971; text-decoration:none;"


def _clean_up(soup):
    for el in soup.find_all(True):
        if "class" in el.attrs:
            del el["class"]
    for link in soup.find_all("link", rel="stylesheet"):
        link.decompose()
    for el in soup.find_all(attrs={"align": True}):
        del el["align"]
