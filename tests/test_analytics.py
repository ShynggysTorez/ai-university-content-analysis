import pandas as pd

from university_content_analysis.analytics import (
    calculate_label_counts,
    summary_statistics,
)


def test_calculate_label_counts() -> None:
    dataframe = pd.DataFrame(
        {
            "llm_labels": [
                "Category A, Category B",
                "Category A",
                "",
            ]
        }
    )

    counts = calculate_label_counts(dataframe)

    assert counts["Category A"] == 2
    assert counts["Category B"] == 1


def test_summary_statistics() -> None:
    dataframe = pd.DataFrame({"llm_labels": ["Category A", "", None]})

    result = summary_statistics(dataframe)

    assert result["total_documents"] == 3
    assert result["documents_with_labels"] == 1
    assert result["documents_without_labels"] == 2
