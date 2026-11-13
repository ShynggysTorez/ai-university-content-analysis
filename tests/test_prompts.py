from university_content_analysis.prompts import (
    build_classification_prompt,
)


def test_prompt_contains_document_and_categories() -> None:
    prompt = build_classification_prompt("The university opened an AI laboratory.")

    assert "AI laboratory" in prompt
    assert "Artificial Intelligence in Education" in prompt
    assert '"labels"' in prompt


def test_prompt_truncates_text() -> None:
    prompt = build_classification_prompt(
        "abcdefghij",
        categories=("Category A",),
        max_chars=5,
    )

    assert "abcde" in prompt
    assert "abcdefghij" not in prompt
