"""Backward-compatible entry point for dataset classification."""

from __future__ import annotations

import os

import pandas as pd

from university_content_analysis import ContentClassifier, OpenAIClient

INPUT_FILE = "parsed_results_clean.csv"
OUTPUT_FILE = "parsed_results_labeled.csv"
MODEL = os.getenv("UCA_MODEL", "gpt-5.4-mini")


def main() -> None:
    dataframe = pd.read_csv(INPUT_FILE)
    classifier = ContentClassifier(OpenAIClient(model=MODEL))

    classifier.classify_dataframe(
        dataframe=dataframe,
        output_file=OUTPUT_FILE,
        save_every=20,
        sleep_seconds=0.3,
    )

    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
