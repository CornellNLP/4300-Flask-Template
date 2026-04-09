import pandas as pd
import re

INPUT = "data/raw/recipes_data.csv"
OUTPUT = "data/processed/recipes_with_calories.csv"

def extract_calories(text):
    if not isinstance(text, str):
        return None
    match = re.search(r'(\d+)\s*cal', text.lower())
    if match:
        return int(match.group(1))
    return None

df = pd.read_csv(INPUT)
df["clean_calories"] = df["directions"].apply(extract_calories)

df.to_csv(OUTPUT, index=False)
print("Saved:", OUTPUT)
