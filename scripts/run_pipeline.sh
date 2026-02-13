#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Run from anywhere; defaults point to the project root.
INPUT_XLSX="${1:-$PROJECT_DIR/1225.xlsx}"
COMBINED_OUT="${2:-$PROJECT_DIR/1225_combined.csv}"
ARCHIVE_DIR="$PROJECT_DIR/archive"

if [ -f "$COMBINED_OUT" ]; then
  mkdir -p "$ARCHIVE_DIR"
  timestamp="$(date +%Y%m%d_%H%M%S)"
  base_name="$(basename "$COMBINED_OUT" .csv)"
  archived_file="$ARCHIVE_DIR/${base_name}_archived_${timestamp}.csv"
  cp "$COMBINED_OUT" "$archived_file"
  echo "Backed up existing $(basename "$COMBINED_OUT") to: $archived_file"
fi

uv run -- python "$SCRIPT_DIR/combine_1225_tabs.py" --input "$INPUT_XLSX" --output "$COMBINED_OUT"

echo
echo "Pipeline complete"
echo "Combined table: $COMBINED_OUT"
