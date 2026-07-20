University Content Intelligence

A Python toolkit for collecting, classifying, and analyzing university web content using large language models (LLMs) and natural language processing (NLP).

This project was developed to support research into how universities communicate about artificial intelligence, digital technologies, research, and educational initiatives. It combines automated content processing with AI-assisted classification to transform large collections of web pages into structured datasets suitable for statistical analysis.

⸻

Why this project exists

Universities publish thousands of pages covering research, education, events, and institutional news. While collecting this information is relatively straightforward, understanding it at scale is much more difficult.

This project addresses that challenge by providing a reproducible workflow that:

* processes university website content;
* prepares multilingual text for analysis;
* classifies documents using LLMs;
* validates generated labels;
* produces structured datasets for further statistical analysis.

The repository was originally created for academic research and has evolved into a reusable Python package.

⸻

Features

* AI-powered multi-label document classification
* Support for multilingual university content
* Configurable taxonomy
* Automated dataset processing
* Built-in validation of generated labels
* Analytical summaries of classified data
* Modular package architecture
* Reusable Python API

⸻

Example workflow

University Websites
        │
        ▼
Content Collection
        │
        ▼
Text Cleaning
        │
        ▼
LLM Classification
        │
        ▼
Label Validation
        │
        ▼
Dataset Generation
        │
        ▼
Statistical Analysis

⸻

Project structure

src/
└── university_content_analysis/
    ├── analytics.py
    ├── classifier.py
    ├── cli.py
    ├── config.py
    ├── refiner.py
    ├── taxonomy.py
    └── utils.py
data/
docs/
notebooks/
outputs/
tests/

⸻

Installation

git clone https://github.com/<your-username>/ai-university-content-analysis.git
cd ai-university-content-analysis
python -m venv .venv
source .venv/bin/activate
pip install -e .

⸻

Quick Start

Classify a dataset:

python classify_dataset.py

Import the package:

from university_content_analysis.analytics import calculate_label_counts

⸻

Technologies

* Python 3.11+
* OpenAI API
* pandas
* Natural Language Processing
* Large Language Models (LLMs)

⸻

Roadmap

* Package-based classification pipeline
* Command-line interface
* Automated testing
* GitHub Actions
* Documentation website
* Performance benchmarking
* Additional language support
* Interactive dashboards

⸻

Research Applications

This project can support:

* computational social science;
* higher education research;
* university benchmarking;
* science policy analysis;
* digital transformation studies;
* AI adoption research.

⸻

License

Released under the MIT License.