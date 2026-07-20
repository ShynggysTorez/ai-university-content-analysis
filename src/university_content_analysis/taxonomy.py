"""Classification taxonomy used by the project."""

from __future__ import annotations

DEFAULT_CATEGORIES: tuple[str, ...] = (
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
)


def validate_labels(
    labels: list[object],
    allowed_labels: tuple[str, ...] = DEFAULT_CATEGORIES,
    maximum: int = 3,
) -> list[str]:
    """Return unique, valid labels while preserving their original order."""

    allowed = set(allowed_labels)
    validated: list[str] = []

    for value in labels:
        label = str(value).strip()

        if label in allowed and label not in validated:
            validated.append(label)

        if len(validated) >= maximum:
            break

    return validated
