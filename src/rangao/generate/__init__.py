"""Article generation — AI writing with configurable style."""

from .writer import generate_article
from .style_engine import StyleEngine, load_style

__all__ = ["generate_article", "StyleEngine", "load_style"]
