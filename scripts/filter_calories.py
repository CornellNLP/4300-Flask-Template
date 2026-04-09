import pandas as pd

INPUT = "data/processed/recipes_with_calories.csv"
OUTPUT = "data/processed/recipes_final.csv"

df = pd.read_csv(INPUT)

df = df[df["clean_calories"].notna()]
df = df[(df["clean_calories"] > 50) & (df["clean_calories"] < 2000)]

df.to_csv(OUTPUT, index=False)
print("Saved:", OUTPUT)
