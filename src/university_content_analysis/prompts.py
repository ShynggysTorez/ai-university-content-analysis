"""
Prompt templates for LLM classification.

Keeping prompts separate from business logic makes them easier to
maintain, test, and improve independently.
"""

from __future__ import annotations

DEFAULT_MAX_CHARS = 12000

DEFAULT_CATEGORIES = [
    "Educational Programs and Curricula",
    "Teaching and Faculty Development",
    "Artificial Intelligence in Education",
    "Data Science and Analytics",
    "Software Development and Programming",
    "Cybersecurity and Information Protection",
    "Digital Transformation and E-Government",
    "Research and Academic Events",
    "Innovation and Startups",
    "Healthcare Technology",
    "Natural Language Processing",
    "Institutional News and Announcements",
]


def format_categories(categories: list[str]) -> str:
    """Return a formatted category list."""

    return "\n".join(f"- {category}" for category in categories)


def build_classification_prompt(
    text: str,
    categories: list[str] | None = None,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """
    Build the prompt sent to the language model.
    """

    if categories is None:
        categories = DEFAULT_CATEGORIES

    text = (text or "").strip()

    if len(text) > max_chars:
        text = text[:max_chars]

    return f"""
You are classifying documents from an academic dataset.

Categories:
{format_categories(categories)}

Text:
\"\"\"
{text}
\"\"\"

Task:
Assign the MOST relevant categories.

Rules:

- Select no more than THREE categories.
- Prefer one or two categories whenever possible.
- Do not invent categories.
- Do not assign irrelevant labels.
- Return ONLY valid JSON.
- The "labels" field must be a JSON array.

Example:

{{"labels": ["Research and Academic Events"]}}
""".strip()