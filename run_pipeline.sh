echo "Step 1: Extract calories"
python3 scripts/extract_calories.py

echo "Step 2: Filter recipes"
python3 scripts/filter_calories.py

echo "Step 3: Estimate nutrition"
python3 scripts/estimate_nutrition_local.py

echo "Done. Final file at data/recipes_enriched.csv"
