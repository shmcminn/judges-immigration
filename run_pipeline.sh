#!/usr/bin/env bash
set -euo pipefail

# Run from this folder (or any folder if you pass explicit paths)
INPUT_XLSX="${1:-1225.xlsx}"
COMBINED_OUT="${2:-1225_combined.csv}"

uv run -- python combine_1225_tabs.py --input "$INPUT_XLSX" --output "$COMBINED_OUT"

echo
echo "Pipeline complete"
echo "Combined table: $COMBINED_OUT"
