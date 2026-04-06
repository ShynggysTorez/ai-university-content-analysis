import pandas as pd

df = pd.read_csv("parsed_results_labeled.csv")

# разбивка категорий
labels = (
    df["llm_labels"]
    .fillna("")
    .str.split(", ")
    .explode()
)

counts = labels.value_counts()

print("\nТОП категории:")
print(counts.head(10))

print("\nВсего строк:", len(df))

print("\nПустые категории:", (df["llm_labels"] == "").sum())