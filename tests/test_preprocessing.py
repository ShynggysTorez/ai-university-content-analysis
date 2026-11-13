from university_content_analysis.preprocessing import (
    build_document,
    normalize_text,
    truncate_text,
)


def test_normalize_text_removes_extra_whitespace() -> None:
    assert normalize_text(" Hello\n\n  world ") == "Hello world"


def test_normalize_text_handles_none() -> None:
    assert normalize_text(None) == ""


def test_truncate_text() -> None:
    assert truncate_text("abcdef", 3) == "abc"


def test_build_document() -> None:
    document = build_document(
        title="Test title",
        url="https://example.com",
        content="Hello\nWorld",
    )

    assert "Title: Test title" in document
    assert "URL: https://example.com" in document
    assert "Hello World" in document
