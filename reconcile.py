"""Compare two inventory snapshots by SKU and report discrepancies."""
import argparse
import csv
import re
import sys
from pathlib import Path

HEADER = ["sku", "warehouse_qty", "channel_qty", "delta", "status"]


def read_snapshot(path):
    rows = {}
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source, strict=True)
        fields = reader.fieldnames or []
        if len(set(fields)) != len(fields) or not {"sku", "quantity"} <= set(fields):
            raise ValueError(f"{path}: expected unique headers including sku and quantity")
        for row in reader:
            location = f"{path}:{reader.line_num}"
            sku = (row.get("sku") or "").strip()
            quantity = (row.get("quantity") or "").strip()
            if None in row or None in row.values():
                raise ValueError(f"{location}: row does not match the header")
            if not sku:
                raise ValueError(f"{location}: empty SKU")
            if sku in rows:
                raise ValueError(f"{location}: duplicate SKU {sku!r}")
            if not re.fullmatch(r"[0-9]{1,18}", quantity):
                raise ValueError(f"{location}: quantity must be a non-negative integer (up to 18 digits)")
            rows[sku] = int(quantity)
    return rows


def discrepancies(warehouse, channel):
    for sku in sorted(warehouse.keys() | channel.keys()):
        expected, recorded = warehouse.get(sku), channel.get(sku)
        if expected is None:
            yield sku, "", recorded, "", "missing_in_warehouse"
        elif recorded is None:
            yield sku, expected, "", "", "missing_in_channel"
        elif expected != recorded:
            yield sku, expected, recorded, expected - recorded, "quantity_mismatch"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("warehouse", type=Path, help="warehouse snapshot CSV")
    parser.add_argument("channel", type=Path, help="sales channel snapshot CSV")
    args = parser.parse_args()
    try:
        warehouse = read_snapshot(args.warehouse)
        channel = read_snapshot(args.channel)
        report = list(discrepancies(warehouse, channel))
    except (OSError, ValueError, csv.Error) as error:
        print(f"Input error: {error}", file=sys.stderr)
        return 2
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(report)
    checked = len(warehouse.keys() | channel.keys())
    print(f"Checked {checked} SKU(s); found {len(report)} discrepancy row(s).", file=sys.stderr)
    return int(bool(report))


if __name__ == "__main__":
    sys.exit(main())
