"""
compute_nutrition.py

Reads a recipe CSV, matches each ingredient to the USDA database, and estimates
nutrition (calories, protein, fat, carbs, fiber, sodium) for the whole recipe.
Outputs a standalone CSV with the original recipe data plus nutrition columns.

Usage:
    python compute_nutrition.py
    python compute_nutrition.py --input recipes_subset.csv --limit 50
"""

import ast
import argparse
import os
import re
import time
import pandas as pd
from difflib import get_close_matches

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
USDA_DIR = os.path.join(SCRIPT_DIR, "USDA_data")

# The nutrient IDs we want from the USDA database
NUTRIENT_IDS = {
    1008: "calories",
    1003: "protein_g",
    1004: "fat_g",
    1005: "carbs_g",
    1079: "fiber_g",
    1093: "sodium_mg",
}

# ---- Volume to mL conversions ----

UNIT_TO_ML = {
    "cup": 240, "cups": 240, "c": 240, "c.": 240,
    "tbsp": 15, "tbsp.": 15, "tablespoon": 15, "tablespoons": 15,
    "tsp": 5, "tsp.": 5, "teaspoon": 5, "teaspoons": 5,
    "fl oz": 30, "fl. oz": 30, "fluid ounce": 30, "fluid ounces": 30,
    "quart": 960, "quarts": 960, "qt": 960, "qt.": 960,
    "pint": 480, "pints": 480, "pt": 480, "pt.": 480,
    "gallon": 3840, "gallons": 3840, "gal": 3840, "gal.": 3840,
    "liter": 1000, "liters": 1000, "l": 1000,
    "ml": 1, "milliliter": 1, "milliliters": 1,
}

# ---- Weight to grams conversions ----

UNIT_TO_GRAMS = {
    "oz": 28.35, "oz.": 28.35, "ounce": 28.35, "ounces": 28.35,
    "lb": 453.6, "lb.": 453.6, "lbs": 453.6, "lbs.": 453.6,
    "pound": 453.6, "pounds": 453.6,
    "g": 1, "gram": 1, "grams": 1,
    "kg": 1000, "kilogram": 1000, "kilograms": 1000,
}

# ---- Densities (g/mL) for converting volume -> weight ----
# Most foods are close to water (1.0), but some differ a lot

DENSITY_MAP = {
    # Fats & oils
    "oil": 0.92, "olive oil": 0.92, "vegetable oil": 0.92, "canola oil": 0.92,
    "coconut oil": 0.92, "sesame oil": 0.92,
    "butter": 0.91, "margarine": 0.91, "shortening": 0.82, "lard": 0.92,
    # Liquids
    "water": 1.0, "milk": 1.03, "cream": 1.01, "buttermilk": 1.03,
    "broth": 1.0, "stock": 1.0, "juice": 1.05, "wine": 0.99,
    "vinegar": 1.01, "soy sauce": 1.17, "honey": 1.42, "maple syrup": 1.33,
    "molasses": 1.42, "corn syrup": 1.38,
    # Dry goods
    "flour": 0.53, "all-purpose flour": 0.53, "bread flour": 0.55,
    "whole wheat flour": 0.51, "cake flour": 0.49,
    "sugar": 0.85, "granulated sugar": 0.85, "brown sugar": 0.83,
    "powdered sugar": 0.56, "confectioners sugar": 0.56,
    "cornstarch": 0.54, "baking powder": 0.77, "baking soda": 0.92,
    "cocoa powder": 0.42, "cocoa": 0.42,
    "salt": 1.22, "kosher salt": 1.12,
    # Grains
    "rice": 0.75, "oats": 0.34, "breadcrumbs": 0.45,
    "cornmeal": 0.64, "semolina": 0.68,
    # Nuts
    "nuts": 0.55, "pecans": 0.45, "walnuts": 0.47, "almonds": 0.55,
    "peanuts": 0.58, "cashews": 0.52, "peanut butter": 1.09,
    # Dairy
    "cheese": 0.45, "cream cheese": 0.97, "sour cream": 0.97,
    "yogurt": 1.03, "cottage cheese": 0.96,
    "parmesan": 0.42, "cheddar": 0.45, "mozzarella": 0.45,
    # Produce (chopped)
    "onion": 0.67, "garlic": 0.78, "celery": 0.6, "carrot": 0.64,
    "tomato": 0.67, "potato": 0.67, "bell pepper": 0.58, "pepper": 0.58,
    "mushroom": 0.38, "mushrooms": 0.38, "spinach": 0.18, "lettuce": 0.18,
    "corn": 0.62, "peas": 0.67, "beans": 0.67, "lentils": 0.77,
    # Proteins
    "chicken": 0.56, "beef": 0.56, "pork": 0.56, "turkey": 0.56,
    "ground beef": 0.56, "ground turkey": 0.56,
    "shrimp": 0.56, "fish": 0.56, "tuna": 0.56, "salmon": 0.56,
    "egg": 50.0, "eggs": 50.0,  # special case: 1 egg ~ 50g
}

DEFAULT_DENSITY = 0.75

# ---- How much common "count" items weigh ----
# For when someone writes "4 eggs" or "1 onion" with no unit

COUNT_ITEM_GRAMS = {
    "egg": 50, "eggs": 50,
    "banana": 118, "bananas": 118,
    "apple": 182, "apples": 182,
    "orange": 131, "oranges": 131,
    "lemon": 58, "lemons": 58,
    "lime": 67, "limes": 67,
    "onion": 150, "onions": 150,
    "potato": 213, "potatoes": 213,
    "tomato": 123, "tomatoes": 123,
    "carrot": 72, "carrots": 72,
    "celery": 40,
    "garlic clove": 5, "garlic cloves": 5, "clove garlic": 5, "cloves garlic": 5,
    "chicken breast": 174, "chicken breasts": 174,
    "chicken thigh": 125, "chicken thighs": 125,
    "tortilla": 49, "tortillas": 49,
    "slice bread": 30, "slices bread": 30,
}

# Unicode fraction characters -> decimal
FRACTIONS = {
    "½": 0.5, "¼": 0.25, "¾": 0.75, "⅓": 0.333, "⅔": 0.667,
    "⅛": 0.125, "⅜": 0.375, "⅝": 0.625, "⅞": 0.875,
}


# ---- Quantity parsing ----

def parse_quantity(ingredient_str: str) -> tuple[float, str, str]:
    """
    Pulls the amount, unit, and food name out of an ingredient string.
    Returns (estimated_grams, unit, food_name).

    Examples:
        '2 c. crushed pretzels'       -> (360.0, 'cup', 'pretzels')
        '1 (8 oz.) pkg. cream cheese' -> (226.8, 'oz', 'cream cheese')
        '4 boned chicken breasts'     -> (696.0, 'count', 'chicken breasts')
        'salt and pepper to taste'    -> (1.0, 'pinch', 'salt and pepper')
    """
    s = ingredient_str.lower().strip()

    # Check for parenthetical weight like (8 oz.)
    paren_match = re.search(r'\((\d+[\d./]*)\s*(oz|ounce|lb|g|ml|kg)\.?\)', s)
    if paren_match:
        amount = _parse_number(paren_match.group(1))
        unit = paren_match.group(2)
        s = s[:paren_match.start()] + s[paren_match.end():]
        food_name = _clean_food_name(s)
        return (_convert_to_grams(amount, unit, food_name), unit, food_name)

    # Try to grab a number from the start (handles "2", "1/2", "1 1/2", "½", "2-3")
    qty_pattern = r'^([\d½¼¾⅓⅔⅛⅜⅝⅞]+(?:\s*[/-]\s*[\d½¼¾⅓⅔⅛⅜⅝⅞]+)?(?:\s+[\d½¼¾⅓⅔⅛⅜⅝⅞]+(?:/[\d]+)?)?)\s*'
    qty_match = re.match(qty_pattern, s)

    if qty_match:
        amount = _parse_number(qty_match.group(1))
        remainder = s[qty_match.end():].strip()
    else:
        # Stuff like "a pinch of salt" or "to taste"
        if any(phrase in s for phrase in ["to taste", "pinch", "dash", "splash"]):
            return (1.0, "pinch", _clean_food_name(s))
        amount = 1.0
        remainder = s

    # Try to match a unit (cups, tbsp, oz, etc.)
    all_units = list(UNIT_TO_ML.keys()) + list(UNIT_TO_GRAMS.keys())
    all_units.sort(key=len, reverse=True)  # match longest first
    unit_pattern = r'^(' + '|'.join(re.escape(u) for u in all_units) + r')\.?\s+'
    unit_match = re.match(unit_pattern, remainder)

    if unit_match:
        unit = unit_match.group(1)
        food_name = _clean_food_name(remainder[unit_match.end():])
        return (_convert_to_grams(amount, unit, food_name), unit, food_name)

    # No unit found — treat it as a countable item (like "4 chicken breasts")
    food_name = _clean_food_name(remainder)
    for item_key, item_grams in COUNT_ITEM_GRAMS.items():
        if item_key in food_name:
            return (amount * item_grams, "count", food_name)

    # Unknown item with no unit — just guess 100g each
    return (amount * 100.0, "count", food_name)


def _parse_number(s: str) -> float:
    """Handles fractions, mixed numbers, and ranges like '2-3'."""
    s = s.strip()

    for frac_char, frac_val in FRACTIONS.items():
        if frac_char in s:
            s = s.replace(frac_char, str(frac_val))

    # Ranges like "2-3" -> average
    if '-' in s and not s.startswith('-'):
        parts = s.split('-')
        try:
            return sum(_parse_number(p) for p in parts) / len(parts)
        except (ValueError, ZeroDivisionError):
            pass

    # Mixed numbers like "1 1/2"
    parts = s.strip().split()
    total = 0.0
    for part in parts:
        if '/' in part:
            try:
                num, den = part.split('/')
                total += float(num) / float(den)
            except (ValueError, ZeroDivisionError):
                pass
        else:
            try:
                total += float(part)
            except ValueError:
                pass

    return total if total > 0 else 1.0


def _get_density(food_name: str) -> float:
    """Look up how dense a food is (g/mL). Defaults to 0.75 if we don't know."""
    food_lower = food_name.lower()
    if food_lower in DENSITY_MAP:
        return DENSITY_MAP[food_lower]
    for key, density in DENSITY_MAP.items():
        if key in food_lower:
            return density
    return DEFAULT_DENSITY


def _convert_to_grams(amount: float, unit: str, food_name: str) -> float:
    """Turn an amount + unit into grams."""
    unit = unit.lower().strip().rstrip('.')

    if unit in UNIT_TO_GRAMS:
        return amount * UNIT_TO_GRAMS[unit]

    if unit in UNIT_TO_ML:
        ml = amount * UNIT_TO_ML[unit]
        return ml * _get_density(food_name)

    return amount * 100.0


def _clean_food_name(s: str) -> str:
    """Strip out packaging words (pkg, can, jar) and prep words (chopped, melted, etc.)."""
    packaging = [
        r'\bpkg\.?\b', r'\bpackage[s]?\b', r'\bcan[s]?\b', r'\bjar[s]?\b',
        r'\bcontainer[s]?\b', r'\bcarton[s]?\b', r'\bbottle[s]?\b',
        r'\bbag[s]?\b', r'\bbox(es)?\b', r'\broll[s]?\b', r'\bbar[s]?\b',
        r'\bstick[s]?\b', r'\benvelope[s]?\b', r'\bsachet[s]?\b',
    ]
    for p in packaging:
        s = re.sub(p, '', s)

    prep = [
        r'\bchopped\b', r'\bminced\b', r'\bdiced\b', r'\bsliced\b',
        r'\bcrushed\b', r'\bmelted\b', r'\bsoftened\b', r'\bthawed\b',
        r'\bfresh\b', r'\bdried\b', r'\bfrozen\b', r'\bcanned\b',
        r'\bcooked\b', r'\braw\b', r'\bboned\b', r'\bpeeled\b',
        r'\bseeded\b', r'\bpitted\b', r'\bdrained\b', r'\brinsed\b',
        r'\bfinely\b', r'\bthinly\b', r'\broughly\b', r'\bcoarsely\b',
        r'\boptional\b', r'\bto taste\b', r'\bof\b',
        r'\bor\b', r'\bplus\b', r'\bfor\b', r'\bserving\b',
    ]
    for p in prep:
        s = re.sub(p, '', s)

    s = re.sub(r'[,;()\[\]]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


# ---- USDA data loading ----

def load_usda_data():
    """Load the USDA food + nutrient CSVs and build a lookup: food description -> macros."""
    print("Loading USDA food database...")
    food_df = pd.read_csv(os.path.join(USDA_DIR, "food.csv"))

    # Skip branded foods (they're noisy) — keep foundation, legacy, and survey foods
    food_df = food_df[
        food_df["data_type"].isin(["sr_legacy_food", "foundation_food", "survey_fndds_food"])
    ].copy()
    print(f"  {len(food_df)} non-branded foods loaded")

    fdc_to_desc = dict(zip(food_df["fdc_id"], food_df["description"]))

    print("Loading nutrient data (this may take a minute)...")
    nutrient_df = pd.read_csv(
        os.path.join(USDA_DIR, "food_nutrient.csv"),
        usecols=["fdc_id", "nutrient_id", "amount"],
    )

    # Only keep the foods and nutrients we actually need
    valid_fdc_ids = set(food_df["fdc_id"])
    valid_nutrient_ids = set(NUTRIENT_IDS.keys())
    nutrient_df = nutrient_df[
        (nutrient_df["fdc_id"].isin(valid_fdc_ids))
        & (nutrient_df["nutrient_id"].isin(valid_nutrient_ids))
    ]

    # Build fdc_id -> {calories: X, protein_g: Y, ...}
    nutrient_lookup = {}
    for fdc_id, group in nutrient_df.groupby("fdc_id"):
        macros = {}
        for _, row in group.iterrows():
            col_name = NUTRIENT_IDS.get(row["nutrient_id"])
            if col_name:
                macros[col_name] = row["amount"]
        nutrient_lookup[fdc_id] = macros

    # Final lookup: lowercase food description -> macros
    desc_to_nutrients = {}
    for fdc_id, desc in fdc_to_desc.items():
        key = desc.lower().strip()
        if key not in desc_to_nutrients and fdc_id in nutrient_lookup:
            desc_to_nutrients[key] = nutrient_lookup[fdc_id]

    print(f"  {len(desc_to_nutrients)} foods with nutrient data indexed")
    return desc_to_nutrients


# ---- Ingredient matching ----

def match_ingredient(ingredient: str, usda_descriptions: list[str], cutoff: float = 0.4) -> str | None:
    """
    Try to find the best USDA match for an ingredient name.
    Tries exact match, then substring, then reverse substring, then fuzzy.
    Returns the matched USDA description or None.
    """
    ingredient = ingredient.lower().strip()

    # Exact match
    if ingredient in usda_descriptions:
        return ingredient

    # Our ingredient appears inside a USDA name (pick the shortest/most generic)
    substring_matches = [d for d in usda_descriptions if ingredient in d]
    if substring_matches:
        return min(substring_matches, key=len)

    # A USDA name's first word appears in our ingredient
    # (e.g., "sour cream" -> finds "Cream, sour, cultured")
    for desc in usda_descriptions:
        first_word = desc.split(",")[0].strip()
        if first_word in ingredient:
            return desc

    # Last resort: fuzzy matching
    matches = get_close_matches(ingredient, usda_descriptions, n=1, cutoff=cutoff)
    return matches[0] if matches else None


# ---- Nutrition computation ----

def compute_recipe_nutrition(
    raw_ingredients: list[str],
    desc_to_nutrients: dict,
    usda_descriptions: list[str],
    has_quantities: bool = False,
) -> dict:
    """
    Estimate total nutrition for a recipe by matching each ingredient to the USDA.

    If has_quantities is True, we parse the amounts from strings like "2 cups flour"
    and scale accordingly. Otherwise we just assume 100g per ingredient.

    USDA values are per 100g, so: contribution = usda_value * (grams / 100)
    """
    totals = {col: 0.0 for col in NUTRIENT_IDS.values()}
    matched = 0
    unmatched = []
    match_pairs = []

    for raw in raw_ingredients:
        if has_quantities:
            grams, unit, food_name = parse_quantity(raw)
        else:
            grams = 100.0
            food_name = raw

        match = match_ingredient(food_name, usda_descriptions)
        if match and match in desc_to_nutrients:
            macros = desc_to_nutrients[match]
            scale = grams / 100.0
            for col in totals:
                totals[col] += macros.get(col, 0.0) * scale
            matched += 1
            match_pairs.append((raw, match, round(grams, 1)))
        else:
            unmatched.append(food_name)
            match_pairs.append((raw, None, round(grams, 1)))

    totals["ingredient_matches"] = str(match_pairs)
    totals["ingredients_matched"] = matched
    totals["ingredients_total"] = len(raw_ingredients)
    totals["match_rate"] = matched / len(raw_ingredients) if raw_ingredients else 0
    totals["unmatched_ingredients"] = "; ".join(unmatched) if unmatched else ""

    return totals


# ---- Ingredient extraction ----

def parse_ner(ner_str: str) -> list[str]:
    """Parse the NER column (it's stored as a stringified list)."""
    try:
        result = ast.literal_eval(ner_str)
        if isinstance(result, list):
            return [str(item).strip() for item in result]
    except (ValueError, SyntaxError):
        pass
    return []


def extract_ingredients(row: pd.Series) -> tuple[list[str], bool]:
    """
    Get ingredient strings from a recipe row.
    Prefers the 'ingredients' column (has quantities) over 'NER' (just names).
    Returns (ingredient_list, has_quantities).
    """
    # Try the full ingredients column first (has amounts we can parse)
    ing_str = str(row.get("ingredients", ""))
    if ing_str and ing_str not in ("nan", "", "[]"):
        try:
            ingredients = ast.literal_eval(ing_str)
            if isinstance(ingredients, list) and len(ingredients) > 0:
                return ([str(item).strip() for item in ingredients], True)
        except (ValueError, SyntaxError):
            pass

    # Fall back to NER (just food names, no quantities)
    ner_str = str(row.get("NER", ""))
    if ner_str and ner_str not in ("nan", "", "[]"):
        parsed = parse_ner(ner_str)
        if parsed:
            return (parsed, False)

    return ([], False)


# ---- Main ----

def main():
    parser = argparse.ArgumentParser(description="Add nutrition info to a recipe CSV using the USDA database")
    parser.add_argument("--input", default=os.path.join(SCRIPT_DIR, "recipes_data.csv"),
                        help="Input recipe CSV (default: recipes_data.csv)")
    parser.add_argument("--output", default=os.path.join(SCRIPT_DIR, "recipes_with_nutrition.csv"),
                        help="Output CSV path")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only process first N recipes (for testing)")
    args = parser.parse_args()

    desc_to_nutrients = load_usda_data()
    usda_descriptions = list(desc_to_nutrients.keys())

    print(f"\nLoading recipes from {args.input}...")
    recipes_df = pd.read_csv(args.input, nrows=args.limit)
    print(f"  {len(recipes_df)} recipes loaded")

    print("\nEstimating nutrition...")
    results = []
    start_time = time.time()
    original_cols = list(recipes_df.columns)

    for i, row in recipes_df.iterrows():
        ingredients, has_quantities = extract_ingredients(row)
        nutrition = compute_recipe_nutrition(
            ingredients, desc_to_nutrients, usda_descriptions, has_quantities
        )

        # Keep all original columns and add nutrition on top
        result = {col: row.get(col, "") for col in original_cols}
        result.update(nutrition)
        results.append(result)

        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            print(f"  Processed {i + 1}/{len(recipes_df)} recipes ({rate:.1f}/sec)")

    output_df = pd.DataFrame(results)

    # Round for readability
    numeric_cols = list(NUTRIENT_IDS.values())
    output_df[numeric_cols] = output_df[numeric_cols].round(1)
    output_df["match_rate"] = output_df["match_rate"].round(2)

    output_df.to_csv(args.output, index=False)
    elapsed = time.time() - start_time
    print(f"\nDone! Wrote {len(output_df)} recipes to {args.output}")
    print(f"Total time: {elapsed:.1f}s")

    print("\n--- Summary ---")
    print(f"Match rate: {output_df['match_rate'].mean():.0%}")
    print(f"Median calories: {output_df['calories'].median():.0f}")
    print(f"Median protein: {output_df['protein_g'].median():.1f}g")
    print(f"Median fat: {output_df['fat_g'].median():.1f}g")
    print(f"Median carbs: {output_df['carbs_g'].median():.1f}g")


if __name__ == "__main__":
    main()
