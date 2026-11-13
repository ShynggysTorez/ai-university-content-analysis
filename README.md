# University Content Intelligence

A Python toolkit for collecting, classifying, and analyzing university web content using Large Language Models (LLMs).

I built this project while working on research focused on how universities communicate about artificial intelligence, research, digital transformation, and education. After using the code on several datasets, I decided to refactor it into a reusable Python package that can be applied to similar research projects.

The goal of the project is simple: automate the process of turning large collections of university web pages into structured datasets that are ready for statistical analysis.

---

## What it does

The workflow consists of several steps:

- collect university web content;
- clean and prepare multilingual text;
- classify documents using an LLM;
- validate generated labels;
- export a structured dataset for further analysis.

---

## Features

- AI-powered multi-label document classification
- Support for multilingual university content
- Configurable taxonomy
- Automated dataset processing
- Label validation
- Analytical summaries
- Command-line interface
- Reusable Python package

---

## Workflow

```text
University Websites
        │
        ▼
Content Collection
        │
        ▼
Text Preprocessing
        │
        ▼
LLM Classification
        │
        ▼
Label Validation
        │
        ▼
Structured Dataset
        │
        ▼
Statistical Analysis
```

---

## Project Structure

```text
ai-university-content-analysis/
│
├── src/
│   └── university_content_analysis/
│       ├── analytics.py
│       ├── classifier.py
│       ├── cli.py
│       ├── config.py
│       ├── llm_client.py
│       ├── refiner.py
│       ├── taxonomy.py
│       └── utils.py
│
├── data/
├── docs/
├── notebooks/
├── outputs/
├── tests/
│
├── classify_dataset.py
├── analyze.py
├── refine.py
├── pyproject.toml
└── README.md
```

---

## Installation

```bash
git clone https://github.com/ShynggysTorez/ai-university-content-analysis.git

cd ai-university-content-analysis

python -m venv .venv

source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

pip install -e .
```

---

## Quick Start

Classify a dataset:

```bash
python classify_dataset.py
```

or use the CLI:

```bash
uca classify
```

Analyze the classified dataset:

```bash
uca analyze
```

Example of using the package in Python:

```python
from university_content_analysis.analytics import calculate_label_counts

calculate_label_counts("classified_dataset.csv")
```

---

## Technologies

- Python 3.11+
- OpenAI API
- pandas
- pytest
- Ruff
- GitHub Actions

---

## Typical Use Cases

Although I originally developed this project for university research, it can also be useful for:

- Computational Social Science
- Higher Education Analytics
- Science Policy Research
- AI Adoption Studies
- Digital Transformation Research
- Content Analysis Projects

---

## Current Status

**Version:** 1.0.0

Implemented:

- Modular package architecture
- LLM-based document classification
- Dataset analytics
- Command-line interface
- Automated testing
- Continuous Integration (GitHub Actions)

Planned improvements:

- Better benchmarking
- Additional language support
- Interactive visualizations
- Extended taxonomy management

---

## License

This project is released under the MIT License.
