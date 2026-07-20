"""Backward-compatible entry point for classification analytics."""

from __future__ import annotations

import pandas as pd

from university_content_analysis import (
    summary_statistics,
    top_categories,
)

INPUT_FILE = "parsed_results_labeled.csv"


def main() -> None:
    dataframe = pd.read_csv(INPUT_FILE)

    print("\nSummary:")
    for name, value in summary_statistics(dataframe).items():
        print(f"{name}: {value}")

    print("\nTop categories:")
    print(top_categories(dataframe, top_n=10).to_string())


if __name__ == "__main__":
    main()
