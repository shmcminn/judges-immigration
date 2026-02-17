# 1225 Update Steps (Mac)

Use this guide to turn a new Excel file into the CSV used in Datawrapper.

## What this does

Running `Run_1225_Pipeline.command` creates:
- `1225_combined.csv`

If `1225_combined.csv` already exists, a backup is saved first in:
- `archive/`
- Example backup name: `1225_combined_archived_20260213_143000.csv`

## Every time you get a new Excel file

1. Put the new Excel file in this folder.
2. Rename the file to `1225.xlsx` (if it's not already).
3. Double-click `Run_1225_Pipeline.command`.
4. Wait for the message that says **Done.**
5. Close the terminal window.
6. Confirm that `1225_combined.csv` is in this folder.

## Upload to Datawrapper

1. Open this link:
   https://app.datawrapper.de/politico/edit/e7pkn/upload
2. In Datawrapper Step 1 (**Upload Data**), click **XLS/CSV upload**.
3. Select `1225_combined.csv`.
4. Go to Step 3 (**Visualize**).
5. Open the **Annotate** tab (left side).
6. Update the end date in the **Notes** field.
7. Check the table preview on the righthand side.
8. Go to Step 4 (**Publish & Embed**) and click **Republish**.



## Troubleshooting

- Excel file is open: close the Excel file, then run again.
- File type is wrong: it must be a real `.xlsx` file.
- Quick check for file type: in Finder, right-click the file, click **Get Info**, and check **Kind**.
- If needed, re-save from Excel: **File > Save As** and choose `.xlsx`.
- Make sure the Excel file and `Run_1225_Pipeline.command` are in the same folder.

### If the .command file is blocked by Mac

1. Right-click `Run_1225_Pipeline.command`.
2. Click **Open**.
3. In the security popup, click **Open** again.

### If the script says `python3` is missing:
1. Open **Terminal**.
2. Run:

```
xcode-select --install
```

3. When install finishes, run `Run_1225_Pipeline.command` again.