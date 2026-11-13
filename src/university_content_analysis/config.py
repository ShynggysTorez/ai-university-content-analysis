"""Application configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ClassificationConfig:
    """Settings used when processing a dataset."""

    input_file: Path = Path("parsed_results_clean.csv")
    output_file: Path = Path("parsed_results_labeled.csv")
    model: str = "gpt-5.4-mini"
    max_chars: int = 12_000
    save_every: int = 20
    sleep_seconds: float = 0.3
    test_rows: int | None = None

    def __post_init__(self) -> None:
        if self.max_chars <= 0:
            raise ValueError("max_chars must be greater than zero.")

        if self.save_every <= 0:
            raise ValueError("save_every must be greater than zero.")

        if self.sleep_seconds < 0:
            raise ValueError("sleep_seconds cannot be negative.")

        if self.test_rows is not None and self.test_rows <= 0:
            raise ValueError("test_rows must be greater than zero.")
