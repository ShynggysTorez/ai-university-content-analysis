import pandas as pd

df = pd.read_csv("parsed_results_labeled.csv")

# берём первую категорию как основную
df["main_category"] = df["llm_labels"].str.split(", ").str[0]

print(df["main_category"].value_counts())

df.to_csv("parsed_results_final.csv", index=False)