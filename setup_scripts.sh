mkdir -p scripts
mkdir -p data/processed

echo "Creating extract_calories.py..."
cat > scripts/extract_calories.py <<'EOPY'
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
EOPY

echo "Creating filter_calories.py..."
cat > scripts/filter_calories.py <<'EOPY'
import pandas as pd

INPUT = "data/processed/recipes_with_calories.csv"
OUTPUT = "data/processed/recipes_final.csv"

df = pd.read_csv(INPUT)

df = df[df["clean_calories"].notna()]
df = df[(df["clean_calories"] > 50) & (df["clean_calories"] < 2000)]

df.to_csv(OUTPUT, index=False)
print("Saved:", OUTPUT)
EOPY

echo "Creating estimate_nutrition_local.py..."
cat > scripts/estimate_nutrition_local.py <<'EOPY'
import pandas as pd

INPUT = "data/processed/recipes_final.csv"
OUTPUT = "data/recipes_enriched.csv"

df = pd.read_csv(INPUT)

def estimate(row):
    text = str(row.get("ingredients", "")).lower()

    protein = text.count("chicken") * 25 + text.count("beef") * 30
    carbs = text.count("rice") * 40 + text.count("pasta") * 45
    fat = text.count("cheese") * 20 + text.count("oil") * 15
    sodium = text.count("salt") * 300
    fiber = text.count("beans") * 10

    return pd.Series({
        "estimated_protein_g": protein,
        "estimated_carbs_g": carbs,
        "estimated_fat_g": fat,
        "estimated_sodium_mg": sodium,
        "estimated_fiber_g": fiber,
    })

df = pd.concat([df, df.apply(estimate, axis=1)], axis=1)

df.to_csv(OUTPUT, index=False)
print("Saved:", OUTPUT)
EOPY

echo "All scripts created!"
