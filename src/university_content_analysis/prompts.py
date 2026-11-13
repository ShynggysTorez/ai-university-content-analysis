"""Prompt construction for multi-label classification."""

from __future__ import annotations

from collections.abc import Sequence

from .taxonomy import DEFAULT_CATEGORIES


def format_categories(categories: Sequence[str]) -> str:
    """Format category names as a readable bullet list."""

    return "\n".join(f"- {category}" for category in categories)


def build_classification_prompt(
    text: str,
    categories: Sequence[str] = DEFAULT_CATEGORIES,
    max_chars: int = 12_000,
) -> str:
    """Create the user prompt sent to the language model."""

    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero.")

    clean_text = (text or "").strip()[:max_chars]

    return f"""
You are classifying documents from an academic dataset.

Choose labels only from this taxonomy:
{format_categories(categories)}

Document:
\"\"\"
{clean_text}
\"\"\"

Assign the most relevant categories.

Rules:
- Select no more than three categories.
- Prefer one or two categories when possible.
- Do not invent categories.
- Do not include irrelevant labels.
- Return only valid JSON.
- The "labels" value must be a JSON array.

Required format:
{{"labels": ["Research and Academic Events"]}}
""".strip()
