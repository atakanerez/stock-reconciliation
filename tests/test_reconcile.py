import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReconciliationTest(unittest.TestCase):
    def run_cli(self, warehouse, channel):
        return subprocess.run(
            [sys.executable, str(ROOT / "reconcile.py"), str(warehouse), str(channel)],
            capture_output=True, text=True, check=False,
        )

    def inline(self, warehouse, channel):
        with tempfile.TemporaryDirectory() as tmp:
            paths = [Path(tmp) / name for name in ("warehouse.csv", "channel.csv")]
            for path, data in zip(paths, (warehouse, channel)):
                path.write_text(data, encoding="utf-8")
            return self.run_cli(*paths)

    def test_demo_output_matches_expected(self):
        examples = ROOT / "examples"
        result = self.run_cli(examples / "warehouse.csv", examples / "channel.csv")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, (examples / "discrepancies.csv").read_text())
        self.assertIn("Checked 5 SKU(s); found 3", result.stderr)

    def test_zero_quantity_is_not_a_missing_sku(self):
        result = self.inline("sku,quantity\nSKU-A,0\n", "sku,quantity\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("SKU-A,0,,,missing_in_channel\n", result.stdout)

    def test_clean_input_outputs_only_header(self):
        data = "sku,quantity\nSKU-A,0\nSKU-B,4\n"
        result = self.inline(data, data)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("\n"), 1)

    def test_rejects_invalid_input_without_report(self):
        cases = {
            "duplicate SKU": "sku,quantity\nSKU-A,1\n SKU-A ,2\n",
            "non-negative integer": "sku,quantity\nSKU-A,-1\n",
            "expected unique headers": "sku,qty\nSKU-A,1\n",
            "row does not match": "sku,quantity\nSKU-A,1,extra\n",
        }
        for message, data in cases.items():
            with self.subTest(message=message):
                result = self.inline(data, "sku,quantity\n")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn(message, result.stderr)

    def test_channel_excess_has_negative_delta(self):
        result = self.inline("sku,quantity\nSKU-A,2\n", "sku,quantity\nSKU-A,5\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("SKU-A,2,5,-3,quantity_mismatch\n", result.stdout)
