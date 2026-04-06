import os
import json
import time
import re
import pandas as pd
from openai import OpenAI

# =========================
# НАСТРОЙКИ
# =========================
INPUT_FILE = "parsed_results_clean.csv"
OUTPUT_FILE = "parsed_results_labeled.csv"

MODEL = "gpt-5.4-mini"
SLEEP_SECONDS = 0.3
MAX_CHARS = 12000
SAVE_EVERY = 20
TEST_MODE = False      # True = только первые 20 строк, False = весь файл

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# ФИНАЛЬНЫЕ КАТЕГОРИИ
# =========================
CATEGORIES_TEXT = """Pick applicable labels from:
- Educational Programs and Curricula
- Teaching and Faculty Development
- Artificial Intelligence in Education
- Data Science and Analytics
- Software Development and Programming
- Cybersecurity and Information Protection
- Digital Transformation and E-Government
- Research and Academic Events
- Innovation and Startups
- Healthcare Technology
- Natural Language Processing
- Institutional News and Announcements
"""

ALLOWED_LABELS = {
    "Educational Programs and Curricula",
    "Teaching and Faculty Development",
    "Artificial Intelligence in Education",
    "Data Science and Analytics",
    "Software Development and Programming",
    "Cybersecurity and Information Protection",
    "Digital Transformation and E-Government",
    "Research and Academic Events",
    "Innovation and Startups",
    "Healthcare Technology",
    "Natural Language Processing",
    "Institutional News and Announcements",
}

# =========================
# ФУНКЦИИ
# =========================
def build_prompt(text: str) -> str:
    text = (text or "").strip()
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]

    return f"""
You are classifying documents from an academic dataset.

Categories:
{CATEGORIES_TEXT}

Text:
\"\"\"
{text}
\"\"\"

Task:
Assign the MOST relevant categories.

STRICT RULES:
- Choose MAXIMUM 3 categories
- Prefer 1–2 if possible
- Do NOT assign irrelevant categories
- Avoid over-classification
- Return ONLY JSON
- labels must be a list

Return:
{{"labels": ["Research and Academic Events"]}}
"""


def extract_json(text: str):
    if not text:
        return None

    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else None


def classify_text(text: str):
    try:
        response = client.responses.create(
            model=MODEL,
            input=[
                {
                    "role": "system",
                    "content": "You are a strict multi-label classifier. Return JSON only."
                },
                {
                    "role": "user",
                    "content": build_prompt(text)
                }
            ],
            temperature=0
        )

        raw = response.output_text.strip()
        json_str = extract_json(raw)

        if not json_str:
            return "", "No JSON found in response", raw

        obj = json.loads(json_str)
        labels = obj.get("labels", [])

        if not isinstance(labels, list):
            return "", "labels is not a list", raw

        cleaned_labels = []
        for label in labels:
            label = str(label).strip()
            if label in ALLOWED_LABELS:
                cleaned_labels.append(label)

        return ", ".join(cleaned_labels), "", raw

    except Exception as e:
        return "", str(e), ""


def build_text(row):
    title = str(row.get("title", "") or "").strip()
    content = str(row.get("content_text", "") or "").strip()
    url = str(row.get("final_url", "") or "").strip()

    return f"""Title: {title}

URL: {url}

Content:
{content}
""".strip()


def main():
    print("Loading dataset...")
    df = pd.read_csv(INPUT_FILE)

    print("Columns found:")
    print(df.columns.tolist())
    print("Total rows:", len(df))

    if TEST_MODE:
        df = df.head(20).copy()
        print("TEST MODE: processing first 20 rows only")

    # создаём колонки, если их нет
    for col in ["llm_labels", "llm_error", "llm_raw"]:
        if col not in df.columns:
            df[col] = ""

    for i, row in df.iterrows():
        text = build_text(row)
        labels, error, raw = classify_text(text)

        df.at[i, "llm_labels"] = labels
        df.at[i, "llm_error"] = error
        df.at[i, "llm_raw"] = raw

        print(f"{i + 1}/{len(df)} -> {labels if labels else '[NO LABELS]'}")

        if (i + 1) % SAVE_EVERY == 0:
            df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
            print(f"Intermediate save: {OUTPUT_FILE}")

        time.sleep(SLEEP_SECONDS)

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print("DONE")
    print("Saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()