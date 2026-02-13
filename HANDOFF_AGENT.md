# 1225 Pipeline Handoff

## What this bundle contains
- `1225.xlsx`: source workbook (maintained by non-technical teammates)
- `combine_1225_tabs.py`: formats all rows for Datawrapper table output
- `run_pipeline.sh`: one-command runner
- `1225_combined.csv`: latest generated table CSV

## How to run
From this folder:

```bash
./run_pipeline.sh
```

Equivalent explicit commands:

```bash
uv run -- python combine_1225_tabs.py --input 1225.xlsx --output 1225_combined.csv
```

## Output intent
### `1225_combined.csv`
- Column order: `Judge`, `For/Against`, `State / District`, `Appointed by`, `Notable ruling` (or `Most notable ruling` depending on source header)
- `Judge` is bold HTML
- `For/Against` is bold HTML with colors:
  - For: `#2FC0B7`
  - Against: `#FD892F`
- `Appointed by` is full president name with party color HTML:
  - Blue (`#3a71b7`): Joe Biden, Barack Obama, Bill Clinton
  - Red (`#f05d45`): Donald Trump, Ronald Reagan, George W. Bush, George H. W. Bush
- Ruling links are converted to emoji hyperlinks: `🔗`
- Rows sorted by president block in this order:
  1. Donald Trump
  2. Joe Biden
  3. Barack Obama
  4. George W. Bush
  5. Bill Clinton
  6. George H. W. Bush
  7. Ronald Reagan
- Within each president block, judges are alphabetical

## Notes for next agent
- Use `uv run -- python ...` for script execution.
- If the ruling header changes between `Notable ruling` and `Most notable ruling`, the script handles both.
