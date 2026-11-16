# Stock Reconciliation

Compare a warehouse inventory snapshot with a sales channel export before
synchronizing stock. The CLI reports quantities that disagree and SKUs missing
from either export. It never writes to either inventory system.

## Quick start

Requires Python 3.10+ and no third-party packages. From the project directory:

```sh
python3 reconcile.py examples/warehouse.csv examples/channel.csv
```

To save the report, append `> discrepancies.csv`. Use a new file name rather
than redirecting to either input file.

Both inputs are UTF-8 CSV files with `sku` and `quantity` headers. Extra
columns are ignored. Each snapshot must have one row per SKU. The program trims
outer whitespace and matches SKUs case-sensitively. Quantities must be
non-negative whole numbers. Use snapshots from the same time and for the same
stock scope (e.g., sellable units); the CLI cannot detect timing or scope drift.

## Example output

```csv
sku,warehouse_qty,channel_qty,delta,status
DEMO-BELT-M,,2,,missing_in_warehouse
DEMO-SOCK-PACK,12,,,missing_in_channel
DEMO-TEE-S,18,14,4,quantity_mismatch
```

The example checks five distinct SKUs; two match and are omitted. A blank
quantity means the SKU was absent and is different from zero stock.
When both snapshots have a quantity, delta is warehouse minus channel.
Review discrepancies before updating either system. If opening reports from
untrusted exports in a spreadsheet, import the SKU column as text without
formula interpretation.

Exit codes: `0` = no discrepancies, `1` = discrepancies found and report
produced, `2` = bad input (no CSV report is emitted). The run summary goes to
standard error so it does not contaminate the report.

## Verification

```sh
python3 -m unittest discover -s tests -v
```

The test suite checks the sample output, the distinction between zero and
a missing SKU, a clean run, malformed input, and signed adjustments in the
report. The sample snapshots are synthetic.
