"""Reusable university-content classification pipeline."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pandas as pd

from .preprocessing import build_document
from .prompts import build_classification_prompt
from .taxonomy import DEFAULT_CATEGORIES, validate_labels


class LanguageModelClient(Protocol):
    """Interface required by the classifier."""

    def generate(self, prompt: str, system_prompt: str = ...) -> str:
        """Generate a text response."""


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    """Result produced for one document."""

    labels: tuple[str, ...]
    raw_response: str
    error: str = ""

    @property
    def labels_text(self) -> str:
        """Return labels in CSV-compatible form."""

        return ", ".join(self.labels)


def extract_json_object(text: str) -> str | None:
    """Extract the first JSON object from a model response."""

    if not text:
        return None

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    match = re.search(r"\{[\s\S]*\}", cleaned)

    return match.group(0) if match else None


class ContentClassifier:
    """Classify university documents with a language model."""

    def __init__(
        self,
        client: LanguageModelClient,
        categories: Sequence[str] = DEFAULT_CATEGORIES,
        max_chars: int = 12_000,
    ) -> None:
        if max_chars <= 0:
            raise ValueError("max_chars must be greater than zero.")

        if not categories:
            raise ValueError("At least one category is required.")

        self.client = client
        self.categories = tuple(categories)
        self.max_chars = max_chars

    def classify_text(self, text: str) -> ClassificationResult:
        """Classify one prepared document."""

        prompt = build_classification_prompt(
            text=text,
            categories=self.categories,
            max_chars=self.max_chars,
        )

        try:
            raw_response = self.client.generate(prompt)
            json_text = extract_json_object(raw_response)

            if json_text is None:
                return ClassificationResult(
                    labels=(),
                    raw_response=raw_response,
                    error="No JSON object found in response.",
                )

            payload = json.loads(json_text)
            labels = payload.get("labels", [])

            if not isinstance(labels, list):
                return ClassificationResult(
                    labels=(),
                    raw_response=raw_response,
                    error='"labels" must be a JSON array.',
                )

            validated = validate_labels(
                labels,
                allowed_labels=self.categories,
                maximum=3,
            )

            return ClassificationResult(
                labels=tuple(validated),
                raw_response=raw_response,
            )

        except Exception as exc:
            return ClassificationResult(
                labels=(),
                raw_response="",
                error=str(exc),
            )

    def classify_dataframe(
        self,
        dataframe: pd.DataFrame,
        output_file: str | Path | None = None,
        save_every: int = 20,
        sleep_seconds: float = 0.0,
        title_column: str = "title",
        content_column: str = "content_text",
        url_column: str = "final_url",
        show_progress: bool = True,
    ) -> pd.DataFrame:
        """Classify every row in a dataframe."""

        if save_every <= 0:
            raise ValueError("save_every must be greater than zero.")

        if sleep_seconds < 0:
            raise ValueError("sleep_seconds cannot be negative.")

        result_df = dataframe.copy()

        for column in ("llm_labels", "llm_error", "llm_raw"):
            if column not in result_df.columns:
                result_df[column] = ""

        total_rows = len(result_df)

        for position, (index, row) in enumerate(
            result_df.iterrows(),
            start=1,
        ):
            document = build_document(
                title=row.get(title_column, ""),
                url=row.get(url_column, ""),
                content=row.get(content_column, ""),
                max_chars=self.max_chars,
            )

            result = self.classify_text(document)

            result_df.at[index, "llm_labels"] = result.labels_text
            result_df.at[index, "llm_error"] = result.error
            result_df.at[index, "llm_raw"] = result.raw_response

            if show_progress:
                display = result.labels_text or "[NO LABELS]"
                print(f"{position}/{total_rows} -> {display}")

            if output_file and position % save_every == 0:
                self.save_dataframe(result_df, output_file)

            if sleep_seconds:
                time.sleep(sleep_seconds)

        if output_file:
            self.save_dataframe(result_df, output_file)

        return result_df

    @staticmethod
    def save_dataframe(
        dataframe: pd.DataFrame,
        output_file: str | Path,
    ) -> None:
        """Write classified data to a UTF-8 CSV file."""

        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_csv(path, index=False, encoding="utf-8-sig")
