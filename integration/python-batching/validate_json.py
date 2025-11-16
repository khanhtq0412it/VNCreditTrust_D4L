"""
validate_json.py

Read the metadata CSV (produced by generate_metadata.py), extract JSON key sets
per unit, and provide a simple comparison report to highlight differences.
"""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Dict, Set

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("validate_json")


def parse_metadata_json_keys(metadata_csv: str | Path) -> Dict[str, Set[str]]:
    """Parse the metadata CSV and return a mapping unit_code -> set(json_keys).

    The CSV is expected to contain a column named 'json_keys' which holds a JSON
    array encoded as a string. When parsing fails for a row, the function falls
    back to an empty set for that unit.
    """
    path = Path(metadata_csv)
    if not path.is_file():
        raise FileNotFoundError(f"metadata file not found: {path}")

    unit_keys: Dict[str, Set[str]] = {}
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            keys_json = row.get("json_keys", "[]")
            try:
                keys = set(json.loads(keys_json))
            except json.JSONDecodeError:
                keys = set()
            unit_keys[row.get("unit_code", "")] = keys
    return unit_keys


def compare_units(unit_keys: Dict[str, Set[str]]) -> str:
    """Return a human-readable comparison report for unit JSON keys."""
    lines = []
    lines.append("===== JSON KEY SUMMARY =====")
    for unit, keys in unit_keys.items():
        lines.append(f"\n--- {unit} ---")
        for k in sorted(keys):
            lines.append(f"  {k}")

    lines.append("\n===== KEY DIFFERENCE CHECK =====")
    all_units = list(unit_keys.keys())
    if len(all_units) <= 1:
        lines.append("Only one unit found. Nothing to compare.")
        return "\n".join(lines)

    base_unit = all_units[0]
    base_keys = unit_keys[base_unit]

    for unit in all_units[1:]:
        diff1 = base_keys - unit_keys[unit]
        diff2 = unit_keys[unit] - base_keys

        if diff1 or diff2:
            lines.append(f"\n⚠️ Difference detected between {base_unit} and {unit}:")
            if diff1:
                lines.append(f"  Keys only in {base_unit}: {sorted(diff1)}")
            if diff2:
                lines.append(f"  Keys only in {unit}: {sorted(diff2)}")
        else:
            lines.append(f"\n✔ {unit} matches {base_unit} exactly (same keys)")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate JSON key sets using a metadata CSV")
    parser.add_argument("metadata_csv", nargs="?", default=str(Path.cwd() / "metadata.csv"), help="Path to metadata.csv produced by generate_metadata.py")
    args = parser.parse_args()

    try:
        unit_keys = parse_metadata_json_keys(args.metadata_csv)
        report = compare_units(unit_keys)
        print(report)
    except Exception as exc:
        logger.error("Failed to validate JSON keys: %s", exc)
        raise
