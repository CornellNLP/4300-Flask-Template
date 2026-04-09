#!/bin/bash

echo "=== Running mealmap.py baseline test ==="
python3 mealmap.py

echo
echo "=== Starting Flask app ==="
python3 src/app.py
