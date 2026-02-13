#!/bin/bash

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

COMBINED_OUT="1225_combined.csv"
ARCHIVE_DIR="$SCRIPT_DIR/archive"

print_line() {
  printf '%s\n' "$1"
}

pause_and_exit() {
  exit_code="${1:-0}"
  print_line ""
  if [ -r /dev/tty ]; then
    printf "Press Enter to close this window..."
    read -r _ < /dev/tty
    print_line ""
  fi
  if command -v osascript >/dev/null 2>&1; then
    osascript -e 'tell application "Terminal" to try' \
              -e 'close front window' \
              -e 'end try' >/dev/null 2>&1
  fi
  exit "$exit_code"
}

print_line "----------------------------------------"
print_line "1225 Data Pipeline"
print_line "This will create:"
print_line "  - $COMBINED_OUT"
print_line "----------------------------------------"
print_line ""

if ! command -v uv >/dev/null 2>&1; then
  print_line "I could not find 'uv' on this Mac."
  print_line ""
  print_line "Please install uv once, then run this again:"
  print_line "  1) Open Terminal"
  print_line "  2) Run: curl -LsSf https://astral.sh/uv/install.sh | sh"
  print_line "  3) Close Terminal and double-click this file again"
  pause_and_exit 1
fi

INPUT_XLSX=""

# Option 1: file was dragged onto this .command file
if [ "${1:-}" != "" ]; then
  INPUT_XLSX="$1"
fi

# Option 2: default expected filename in this folder
if [ "$INPUT_XLSX" = "" ] && [ -f "1225.xlsx" ]; then
  INPUT_XLSX="$SCRIPT_DIR/1225.xlsx"
fi

# Option 3: exactly one xlsx file in this folder
if [ "$INPUT_XLSX" = "" ]; then
  shopt -s nullglob
  xlsx_files=("$SCRIPT_DIR"/*.xlsx)
  shopt -u nullglob

  # Ignore Excel temporary lock files like "~$file.xlsx"
  filtered_files=()
  for file in "${xlsx_files[@]}"; do
    base="$(basename "$file")"
    if [[ "$base" != '~$'* ]]; then
      filtered_files+=("$file")
    fi
  done

  if [ "${#filtered_files[@]}" -eq 1 ]; then
    INPUT_XLSX="${filtered_files[0]}"
  elif [ "${#filtered_files[@]}" -gt 1 ]; then
    print_line "I found multiple Excel files in this folder."
    print_line "Please drag the file you want onto this .command file."
    print_line ""
    print_line "Files found:"
    for file in "${filtered_files[@]}"; do
      print_line "  - $(basename "$file")"
    done
    pause_and_exit 1
  fi
fi

if [ "$INPUT_XLSX" = "" ] || [ ! -f "$INPUT_XLSX" ]; then
  print_line "No Excel file found."
  print_line ""
  print_line "Please do ONE of these, then try again:"
  print_line "  - Put your Excel file in this folder and name it 1225.xlsx"
  print_line "  - OR drag your Excel file onto this .command file"
  pause_and_exit 1
fi

print_line "Using Excel file: $(basename "$INPUT_XLSX")"
print_line ""

if [ -f "$SCRIPT_DIR/$COMBINED_OUT" ]; then
  mkdir -p "$ARCHIVE_DIR"
  timestamp="$(date +%Y%m%d_%H%M%S)"
  archived_file="$ARCHIVE_DIR/${COMBINED_OUT%.csv}_archived_${timestamp}.csv"
  cp "$SCRIPT_DIR/$COMBINED_OUT" "$archived_file"
  print_line "Backed up existing $COMBINED_OUT to:"
  print_line "  - archive/$(basename "$archived_file")"
  print_line ""
fi

print_line "Step 1/1: Building $COMBINED_OUT ..."
if ! uv run -- python "$SCRIPT_DIR/scripts/combine_1225_tabs.py" --input "$INPUT_XLSX" --output "$SCRIPT_DIR/$COMBINED_OUT"; then
  print_line ""
  print_line "The step failed. Please check that your Excel file is not open, then try again."
  pause_and_exit 1
fi

print_line ""
print_line "Done."
print_line "Created files in this folder:"
print_line "  - $COMBINED_OUT"
pause_and_exit 0
