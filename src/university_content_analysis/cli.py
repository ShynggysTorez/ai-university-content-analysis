"""Command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .analytics import summary_statistics, top_categories
from .classifier import ContentClassifier
from .llm_client import OpenAIClient


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""

    parser = argparse.ArgumentParser(
        prog="uca",
        description="Classify and analyze university website content.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    classify_parser = subparsers.add_parser(
        "classify",
        help="Classify documents in a CSV dataset.",
    )
    classify_parser.add_argument("input_file", type=Path)
    classify_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("outputs/classified_content.csv"),
    )
    classify_parser.add_argument(
        "--model",
        default="gpt-5.4-mini",
    )
    classify_parser.add_argument(
        "--save-every",
        type=int,
        default=20,
    )
    classify_parser.add_argument(
        "--sleep",
        type=float,
        default=0.3,
    )
    classify_parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Summarize an already classified CSV dataset.",
    )
    analyze_parser.add_argument("input_file", type=Path)
    analyze_parser.add_argument("--top", type=int, default=10)

    return parser


def run_classification(args: argparse.Namespace) -> int:
    """Execute the classification command."""

    dataframe = pd.read_csv(args.input_file)

    if args.limit is not None:
        dataframe = dataframe.head(args.limit).copy()

    client = OpenAIClient(model=args.model)
    classifier = ContentClassifier(client=client)

    classifier.classify_dataframe(
        dataframe=dataframe,
        output_file=args.output,
        save_every=args.save_every,
        sleep_seconds=args.sleep,
    )

    print(f"Saved classified dataset to: {args.output}")
    return 0


def run_analysis(args: argparse.Namespace) -> int:
    """Execute the analytics command."""

    dataframe = pd.read_csv(args.input_file)

    print("\nSummary")
    for name, value in summary_statistics(dataframe).items():
        print(f"{name}: {value}")

    print("\nTop categories")
    print(top_categories(dataframe, top_n=args.top).to_string())

    return 0


def main() -> int:
    """Run the command-line application."""

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "classify":
        return run_classification(args)

    if args.command == "analyze":
        return run_analysis(args)

    parser.error("Unknown command.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
