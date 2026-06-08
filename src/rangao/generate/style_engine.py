"""Style engine — loads and manages writing style templates.

Styles are YAML files in the styles/ directory. Each style defines:
- A writing prompt (tone, structure, formatting rules)
- Image handling preferences
- Color scheme and typography preferences for rendering
"""

from __future__ import annotations

from pathlib import Path


class StyleEngine:
    """Load and cache writing style templates."""

    def __init__(self, styles_dir: Path):
        self.styles_dir = Path(styles_dir)
        self._cache: dict[str, dict] = {}

    def load(self, name: str) -> dict:
        """Load a style by name (without .yaml extension).

        Falls back to built-in default if the file doesn't exist.
        """
        if name in self._cache:
            return self._cache[name]

        style_path = self.styles_dir / f"{name}.yaml"
        if style_path.exists():
            style = _parse_yaml_simple(style_path.read_text(encoding="utf-8"))
        else:
            style = _builtin_style(name)

        self._cache[name] = style
        return style

    def list_styles(self) -> list[str]:
        """List available style template names."""
        if not self.styles_dir.exists():
            return []
        return [
            p.stem for p in self.styles_dir.glob("*.yaml")
        ]


def load_style(styles_dir: Path, name: str) -> dict:
    """Convenience function to load a style."""
    return StyleEngine(styles_dir).load(name)


def _parse_yaml_simple(text: str) -> dict:
    """Simple YAML parser — handles the flat structure we need.

    For production, use `pip install pyyaml`.
    """
    result: dict = {}
    current_key: str | None = None
    current_value: list[str] = []

    for line in text.split("\n"):
        # Skip comments and empty
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if ":" in stripped and not stripped.startswith(" "):
            # New top-level key
            if current_key and current_value:
                result[current_key] = "\n".join(current_value).strip()
            current_key, _, val = stripped.partition(":")
            current_key = current_key.strip()
            val = val.strip()
            current_value = [val] if val else []
        elif current_key and stripped.startswith("- "):
            current_value.append(stripped[2:])
        elif current_key:
            current_value.append(stripped)

    if current_key and current_value:
        result[current_key] = "\n".join(current_value).strip()

    return result


def _builtin_style(name: str) -> dict:
    """Minimal built-in style when no YAML file is found."""
    return {
        "prompt": (
            "Write a professional Chinese academic WeChat article. "
            "Structure: background introduction, illustrated walkthrough, conclusion and outlook. "
            "Use third-person perspective. Tone: rigorous, data-driven, positive but objective."
        ),
        "figure_caption_format": "Figure {n}. {description}",
        "language": "zh-CN",
        "images": {},
    }
