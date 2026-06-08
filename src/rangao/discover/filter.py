"""AI-based paper filtering and deduplication."""

from __future__ import annotations

import time
from openai import OpenAI

from ..config import get_config
from ..models import Paper


NON_ARTICLE_PREFIXES = [
    "correction to", "erratum", "retraction", "retracted",
    "reply to", "comment on", "response to", "addendum",
    "editorial", "book review", "corrigendum",
]


def is_research_article(title: str) -> bool:
    """Filter out corrections, retractions, editorials, etc."""
    lower = title.lower().strip()
    for prefix in NON_ARTICLE_PREFIXES:
        if lower.startswith(prefix):
            return False
    if "[erratum]" in lower or "[retraction]" in lower:
        return False
    return True


def deduplicate_by_doi(papers: list[Paper]) -> list[Paper]:
    """Remove duplicate papers by DOI."""
    seen: set[str] = set()
    unique: list[Paper] = []
    for p in papers:
        if p.doi not in seen:
            seen.add(p.doi)
            unique.append(p)
    return unique


def ai_filter_papers(
    papers: list[Paper],
    topic_description: str = "",
) -> list[Paper]:
    """Use LLM to filter papers relevant to a specific topic.

    First pass: quick keyword match. Second pass: AI verification.

    Args:
        papers: List of papers to filter.
        topic_description: Natural language description of the topic
            (e.g., "carbon dots for biomedical applications").

    Returns:
        Filtered list of relevant papers.
    """
    config = get_config()
    if not config.has_llm_credentials:
        return papers  # no AI, return all

    # Quick keyword pre-filter
    keywords = _extract_keywords(topic_description)
    if keywords:
        papers = [p for p in papers if any(kw.lower() in p.title.lower() for kw in keywords)]

    if not papers:
        return []

    # AI verification
    client = OpenAI(api_key=config.llm_api_key, base_url=config.llm_base_url)
    filtered: list[Paper] = []

    system_prompt = (
        "You are a research scientist. Given a paper title and a topic description, "
        "determine if the paper genuinely belongs to that research area. "
        "Answer ONLY 'yes' or 'no'."
    )

    for i, paper in enumerate(papers):
        try:
            resp = client.chat.completions.create(
                model=config.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Topic: {topic_description}\nTitle: \"{paper.title}\""},
                ],
                max_tokens=5,
                temperature=0.0,
            )
            answer = resp.choices[0].message.content.strip().lower()
            if answer == "yes":
                filtered.append(paper)
            time.sleep(0.2)  # rate limit
        except Exception:
            filtered.append(paper)  # on error, keep paper

    return filtered


def _extract_keywords(topic_description: str) -> list[str]:
    """Extract likely keyword stems from a topic description."""
    if not topic_description:
        return []
    # Simple: split on spaces/common separators, keep unique words > 3 chars
    words = topic_description.lower().replace(",", " ").replace(";", " ").split()
    return list(set(w for w in words if len(w) > 3 and w not in ("based", "with", "that", "this", "from", "into")))
