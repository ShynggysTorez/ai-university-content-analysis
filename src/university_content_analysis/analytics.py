"""Analytical functions for classified datasets."""

from __future__ import annotations

import pandas as pd


def _require_column(dataframe: pd.DataFrame, column: str) -> None:
    if column not in dataframe.columns:
        raise KeyError(f"Required column not found: {column}")


def calculate_label_counts(
    dataframe: pd.DataFrame,
    column: str = "llm_labels",
) -> pd.Series:
    """Count individual labels stored in a comma-separated column."""

    _require_column(dataframe, column)

    labels = (
        dataframe[column]
        .fillna("")
        .astype(str)
        .str.split(r",\s*")
        .explode()
        .str.strip()
    )

    labels = labels[labels.ne("")]

    return labels.value_counts()


def top_categories(
    dataframe: pd.DataFrame,
    top_n: int = 10,
    column: str = "llm_labels",
) -> pd.Series:
    """Return the most common categories."""

    if top_n <= 0:
        raise ValueError("top_n must be greater than zero.")

    return calculate_label_counts(dataframe, column).head(top_n)


def summary_statistics(
    dataframe: pd.DataFrame,
    column: str = "llm_labels",
) -> dict[str, int]:
    """Calculate basic classification statistics."""

    _require_column(dataframe, column)

    normalized = dataframe[column].fillna("").astype(str).str.strip()
    counts = calculate_label_counts(dataframe, column)

    return {
        "total_documents": int(len(dataframe)),
        "documents_with_labels": int(normalized.ne("").sum()),
        "documents_without_labels": int(normalized.eq("").sum()),
        "unique_categories": int(len(counts)),
    }
