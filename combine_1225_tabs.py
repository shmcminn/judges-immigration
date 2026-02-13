#!/usr/bin/env python3
"""Combine all tabs from an .xlsx workbook into one CSV with a source tab column.

This script uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS_MAIN = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL_DOC = {
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
}
NS_REL_PKG = {"pr": "http://schemas.openxmlformats.org/package/2006/relationships"}
BLUE = "#3a71b7"
RED = "#f05d45"
FOR_COLOR = "#2FC0B7"
AGAINST_COLOR = "#FD892F"
FOR_AGAINST_FIELD = "For/Against"

DEMOCRATIC_APPOINTEES = {"Biden", "Obama", "Clinton"}
REPUBLICAN_APPOINTEES = {"Trump", "Reagan", "George W. Bush", "George H. W. Bush", "George H.W. Bush"}
PRESIDENT_FULL_NAMES = {
    "Biden": "Joe Biden",
    "Obama": "Barack Obama",
    "Clinton": "Bill Clinton",
    "Reagan": "Ronald Reagan",
    "Trump": "Donald Trump",
    "George W. Bush": "George W. Bush",
    "George H. W. Bush": "George H. W. Bush",
    "George H.W. Bush": "George H. W. Bush",
}
PRESIDENT_SORT_ORDER = {
    "Donald Trump": 0,
    "Joe Biden": 1,
    "Barack Obama": 2,
    "George W. Bush": 3,
    "Bill Clinton": 4,
    "George H. W. Bush": 5,
    "Ronald Reagan": 6,
}


def col_ref_to_index(cell_ref: str) -> int:
    """Convert Excel column reference (A, AB, ...) to 1-based index."""
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        return 1
    letters = match.group(1)
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx


def shared_string_text(si_el: ET.Element) -> str:
    return "".join((t.text or "") for t in si_el.findall(".//main:t", NS_MAIN))


def load_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    sst_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    return [shared_string_text(si) for si in sst_root.findall("main:si", NS_MAIN)]


def load_sheets_and_paths(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook_root = ET.fromstring(zf.read("xl/workbook.xml"))
    wb_rels_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))

    rel_map: dict[str, str] = {}
    for rel in wb_rels_root.findall("pr:Relationship", NS_REL_PKG):
        rel_map[rel.attrib["Id"]] = rel.attrib["Target"]

    sheets: list[tuple[str, str]] = []
    for sheet in workbook_root.findall("main:sheets/main:sheet", NS_MAIN):
        name = sheet.attrib["name"]
        rel_id = sheet.attrib.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        if not rel_id:
            continue
        target = rel_map.get(rel_id)
        if not target:
            continue
        if target.startswith("/"):
            sheet_path = target.lstrip("/")
        else:
            sheet_path = posixpath.normpath(posixpath.join("xl", target))
        sheets.append((name, sheet_path))
    return sheets


def read_cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "s":
        idx_text = cell.findtext("main:v", default="", namespaces=NS_MAIN)
        if not idx_text:
            return ""
        idx = int(idx_text)
        return shared_strings[idx] if 0 <= idx < len(shared_strings) else ""
    if cell_type == "inlineStr":
        return "".join((t.text or "") for t in cell.findall(".//main:t", NS_MAIN))
    if cell_type == "b":
        return "TRUE" if cell.findtext("main:v", default="", namespaces=NS_MAIN) == "1" else "FALSE"
    return cell.findtext("main:v", default="", namespaces=NS_MAIN)


def parse_sheet_rows(
    zf: zipfile.ZipFile, sheet_path: str, shared_strings: list[str]
) -> tuple[list[str], list[list[str]]]:
    sheet_root = ET.fromstring(zf.read(sheet_path))

    raw_rows: list[tuple[int, dict[int, str]]] = []
    max_col = 0
    for row_el in sheet_root.findall(".//main:sheetData/main:row", NS_MAIN):
        row_num = int(row_el.attrib.get("r", "0"))
        row_map: dict[int, str] = {}
        for cell in row_el.findall("main:c", NS_MAIN):
            cell_ref = cell.attrib.get("r", "")
            col_idx = col_ref_to_index(cell_ref)
            value = read_cell_value(cell, shared_strings)
            # Ignore cells that exist only for styling/formatting and hold no value.
            if is_blank(value):
                continue
            row_map[col_idx] = value
            if col_idx > max_col:
                max_col = col_idx
        if row_map:
            raw_rows.append((row_num, row_map))

    if not raw_rows:
        return [], []

    raw_rows.sort(key=lambda item: item[0])
    expanded_rows: list[list[str]] = []
    for _, row_map in raw_rows:
        expanded = [""] * max_col
        for col_idx, value in row_map.items():
            expanded[col_idx - 1] = value
        expanded_rows.append(expanded)

    header_raw = expanded_rows[0]
    headers: list[str] = []
    seen: dict[str, int] = {}
    for i, h in enumerate(header_raw, start=1):
        key = (h or "").strip()
        if not key:
            key = f"column_{i}"
        if key in seen:
            seen[key] += 1
            key = f"{key}_{seen[key]}"
        else:
            seen[key] = 1
        headers.append(key)

    return headers, expanded_rows[1:]


def is_blank(value: str) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def merge_sparse_unnamed_into_notes(
    field_order: list[str], records: list[dict[str, str]]
) -> list[str]:
    """Move sparse unnamed columns into Notes, then drop those columns."""
    if "Notes" not in field_order:
        return field_order

    unnamed_fields = [f for f in field_order if re.fullmatch(r"column_\d+", f)]
    drop_fields: set[str] = set()
    for field in unnamed_fields:
        populated_rows = [r for r in records if not is_blank(r.get(field, ""))]
        if not populated_rows:
            drop_fields.add(field)
            continue
        if len(populated_rows) <= 3:
            for row in populated_rows:
                val = row.get(field, "").strip()
                notes = row.get("Notes", "").strip()
                row["Notes"] = val if not notes else f"{notes} | {val}"
            drop_fields.add(field)

    return [f for f in field_order if f not in drop_fields]


def normalize_for_against(source_tab: str) -> str:
    value = (source_tab or "").strip().lower()
    if "against" in value:
        return "Against"
    if re.search(r"\bfor\b", value):
        return "For"
    return source_tab


def color_for_against_html(value: str) -> str:
    clean = (value or "").strip()
    if clean == "For":
        return f'<b><span style="color:{FOR_COLOR};">{clean}</span></b>'
    if clean == "Against":
        return f'<b><span style="color:{AGAINST_COLOR};">{clean}</span></b>'
    return clean


def color_appointed_by_html(name: str) -> str:
    clean_name = (name or "").strip()
    clean_name = PRESIDENT_FULL_NAMES.get(clean_name, clean_name)
    if not clean_name:
        return ""
    if clean_name in {PRESIDENT_FULL_NAMES.get(n, n) for n in DEMOCRATIC_APPOINTEES}:
        return f'<span style="color:{BLUE};">{clean_name}</span>'
    if clean_name in {PRESIDENT_FULL_NAMES.get(n, n) for n in REPUBLICAN_APPOINTEES}:
        return f'<span style="color:{RED};">{clean_name}</span>'
    return clean_name


def ruling_link_emoji_html(value: str) -> str:
    url = (value or "").strip()
    if not url or not re.match(r"^https?://", url, flags=re.IGNORECASE):
        return value
    return f'<a href="{url}" target="_blank">🔗</a>'


def apply_output_transforms(field_order: list[str], records: list[dict[str, str]]) -> list[str]:
    for record in records:
        if "Judge" in record:
            judge = (record.get("Judge", "") or "").strip()
            record["Judge"] = f"<b>{judge}</b>" if judge else ""
        if "Appointed by" in record:
            record["Appointed by"] = color_appointed_by_html(record.get("Appointed by", ""))
        for ruling_field in ("Most notable ruling", "Notable ruling"):
            if ruling_field in record:
                record[ruling_field] = ruling_link_emoji_html(record.get(ruling_field, ""))
        if "source_tab" in record:
            normalized = normalize_for_against(record.get("source_tab", ""))
            record[FOR_AGAINST_FIELD] = color_for_against_html(normalized)
            del record["source_tab"]
        if "Notes" in record:
            del record["Notes"]

    new_field_order: list[str] = []
    for field in field_order:
        if field == "source_tab":
            if FOR_AGAINST_FIELD not in new_field_order:
                new_field_order.append(FOR_AGAINST_FIELD)
            continue
        if field == "Notes":
            continue
        if field not in new_field_order:
            new_field_order.append(field)
    preferred_front = ["Judge", FOR_AGAINST_FIELD]
    ordered = [f for f in preferred_front if f in new_field_order]
    ordered.extend(f for f in new_field_order if f not in ordered)
    return ordered


def strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value or "").strip()


def sort_records(records: list[dict[str, str]]) -> None:
    def sort_key(record: dict[str, str]) -> tuple[int, str, str]:
        president = strip_html(record.get("Appointed by", ""))
        judge = strip_html(record.get("Judge", ""))
        for_against = strip_html(record.get(FOR_AGAINST_FIELD, ""))
        return (
            PRESIDENT_SORT_ORDER.get(president, 999),
            judge.lower(),
            for_against.lower(),
        )

    records.sort(key=sort_key)


def combine_workbook(input_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    records: list[dict[str, str]] = []
    field_order: list[str] = []

    with zipfile.ZipFile(input_path) as zf:
        shared_strings = load_shared_strings(zf)
        sheets = load_sheets_and_paths(zf)

        for sheet_name, sheet_path in sheets:
            headers, rows = parse_sheet_rows(zf, sheet_path, shared_strings)
            if not headers:
                continue
            for row in rows:
                record = {
                    headers[i]: (row[i] if i < len(row) else "")
                    for i in range(len(headers))
                }
                record["source_tab"] = sheet_name
                records.append(record)
                for key in record.keys():
                    if key not in field_order:
                        field_order.append(key)

    field_order = merge_sparse_unnamed_into_notes(field_order, records)
    field_order = apply_output_transforms(field_order, records)
    sort_records(records)

    # Drop columns that are blank for every merged row, except source_tab.
    kept_fields = [
        field
        for field in field_order
        if field == FOR_AGAINST_FIELD
        or any(not is_blank(record.get(field, "")) for record in records)
    ]
    return kept_fields, records


def write_csv(output_path: Path, fieldnames: list[str], records: list[dict[str, str]]) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Combine all tabs in an .xlsx into one CSV with a source_tab column."
    )
    parser.add_argument(
        "--input", default="1225.xlsx", help="Path to input XLSX file (default: 1225.xlsx)"
    )
    parser.add_argument(
        "--output",
        default="1225_combined.csv",
        help="Path to output CSV file (default: 1225_combined.csv)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    fieldnames, records = combine_workbook(input_path)
    write_csv(output_path, fieldnames, records)

    tabs = sorted({record[FOR_AGAINST_FIELD] for record in records}) if records else []
    print(f"Input: {input_path.resolve()}")
    print(f"Output: {output_path.resolve()}")
    print(f"Rows written: {len(records)}")
    print(f"Columns written: {len(fieldnames)}")
    print(f"Source tabs: {tabs}")


if __name__ == "__main__":
    main()
