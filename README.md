# Run This Pipeline (Mac, Non-Technical Steps)

This folder includes a file named `Run_1225_Pipeline.command`.

When you run it, it creates:
- `1225_combined.csv`

## Before your first run (one-time setup)

1. Install `uv` (only once on each Mac):
   - Open **Terminal**
   - Paste and run (without the tick marks):

   curl -LsSf https://astral.sh/uv/install.sh | sh

2. Close Terminal when it finishes.

## Every time you get a new Excel file

1. Put the new Excel file in this same folder.
2. Rename it to `1225.xlsx`, then double-click `Run_1225_Pipeline.command`
3. Wait until you see **Done.**
4. Now you can close the terminal window.
5. Use these output files in this folder for Datawrapper:
   - `1225_combined.csv`

## Upload to Datawrapper

After `1225_combined.csv` is created:

1. Open this chart:
   - https://app.datawrapper.de/politico/edit/e7pkn/publish
2. In Datawrapper Step 1 (Upload Data), click "XLS/CSV upload".
3. Choose `1225_combined.csv`.
4. Click Step 3 (Visualize)
5. Click the Annotate tab on the left.
6. Change the dates in the "Notes" field to make sure it is up to date.
7. Check the table preview to make sure everything looks right.
8. Click Step 4 (Publish & Embed), then click "Republish".

## If Mac blocks opening the .command file

1. Right-click `Run_1225_Pipeline.command`
2. Click **Open**
3. Click **Open** again in the security popup

## If something goes wrong

- Make sure the Excel file is not currently open in Excel.
- Make sure it is a real `.xlsx` Excel file (not just renamed):
  - In Finder, right-click the file, click **Get Info**, and check **Kind**.
  - If needed, open the file in Excel and use **File > Save As** to save a true `.xlsx` file.
- Make sure you are running the `.command` file from this same folder.
