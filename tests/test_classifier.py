from university_content_analysis.classifier import (
    ContentClassifier,
    extract_json_object,
)


class FakeClient:
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return (
            '{"labels": ["Artificial Intelligence in Education", "Invalid Category"]}'
        )


def test_extract_json_from_markdown() -> None:
    response = '```json\n{"labels": ["Example"]}\n```'

    assert extract_json_object(response) == '{"labels": ["Example"]}'


def test_classifier_keeps_only_allowed_labels() -> None:
    classifier = ContentClassifier(client=FakeClient())

    result = classifier.classify_text("AI course")

    assert result.labels == ("Artificial Intelligence in Education",)
    assert result.error == ""
