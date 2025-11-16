#!/usr/bin/env python3
"""
generate_metadata.py

Generate a CSV metadata catalog from a rooted data folder. This module is written in
English with clear docstrings, type annotations and a small CLI for reuse in pipelines.

Primary function:
- generate_metadata(root_dir: str | Path, out_csv: str | Path) -> int

It detects whether each unit folder contains a data.json and screenshot file(s),
collects top-level JSON keys, and writes a metadata CSV containing one row per unit.

Notes:
- Avoids hard-coded secrets/paths; supply arguments or environment variables when
  invoking from CI or production.
"""
from __future__ import annotations

import csv
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

# Mappings and defaults (kept from original repository)
SOURCE_SYSTEM = os.environ.get("SOURCE_SYSTEM", "vncredittrust")

# Organization mapping (category -> Vietnamese uppercase display name)
organization_name_mapping = {
    "cong_ty_tai_chinh": "CÔNG TY TÀI CHÍNH",
    "nh_100_von_nuoc_ngoai": "NGÂN HÀNG 100% VỐN NƯỚC NGOÀI",
    "nh_chinh_sach": "NGÂN HÀNG CHÍNH SÁCH",
    "nh_hop_tac_xa": "NGÂN HÀNG HỢP TÁC XÃ",
    "nh_lien_doanh": "NGÂN HÀNG LIÊN DOANH",
    "nhtm_nha_nuoc": "NGÂN HÀNG THƯƠNG MẠI NHÀ NƯỚC",
    "nhtmcp_trong_nuoc": "NGÂN HÀNG TMCP TRONG NƯỚC",
}

# Unit name mapping
unit_name_mapping = {
    # cong_ty_tai_chinh
    "evfnc": "EVFNC",
    "fe_credit": "FE_CREDIT",
    "hafic": "HAFIC",
    "hd_saigon": "HD_SAIGON",
    "home_credit": "HOME_CREDIT",
    "jivf": "JIVF",
    "lotte_finance": "LOTTE_FINANCE",
    "mafc": "MAFC",
    "ms_finance": "MS_FINANCE",
    "ptf": "PTF",
    "sbic_finance": "SBIC_FINANCE",
    "shbfinance": "SHBFINANCE",
    "svfc": "SVFC",
    "tfsvn": "TFSVN",
    "tnex": "TNEX",
    "vietcredit": "VIETCREDIT",

    # nh_100_von_nuoc_ngoai
    "anzvl": "ANZVL",
    "cimb_vn": "CIMB_VN",
    "hlbvn": "HLBVN",
    "hsbc_vn": "HSBC_VN",
    "pbvn": "PBVN",
    "shbvn": "SHBVN",
    "standard_chartered": "STANDARD_CHARTERED",
    "uob_vn": "UOB_VN",
    "woori_vn": "WOORI_VN",

    # nh_chinh_sach
    "vbsp": "VBSP",
    "vdb": "VDB",

    # nh_hop_tac_xa
    "ccf": "CCF",

    # nh_lien_doanh
    "ivb": "IVB",
    "vrb": "VRB",

    # nhtm_nha_nuoc
    "argibank": "ARGIBANK",

    # nhtmcp_trong_nuoc
    "abbank": "ABBANK",
    "acb": "ACB",
    "bac_a_bank": "BAC_A_BANK",
    "baoviet_bank": "BAOVIET_BANK",
    "bidv": "BIDV",
    "bvbank": "BVBANK",
    "eximbank": "EXIMBANK",
    "gpbank": "GPBANK",
    "hdbank": "HDBANK",
    "kienlongbank": "KIENLONGBANK",
    "lbbank": "LBBANK",
    "mb_bank": "MB_BANK",
    "mbv": "MBV",
    "msb": "MSB",
    "nam_a_bank": "NAM_A_BANK",
    "ncb": "NCB",
    "ocb": "OCB",
    "pgbank": "PGBANK",
    "pvcombank": "PVCOMBANK",
    "sacombank": "SACOMBANK",
    "saigonbank": "SAIGONBANK",
    "scb": "SCB",
    "seabank": "SEABANK",
    "shb": "SHB",
    "techcombank": "TECHCOMBANK",
    "tpbank": "TPBANK",
    "vabank": "VABANK",
    "vib": "VIB",
    "vietbank": "VIETBANK",
    "vietcombank": "VIETCOMBANK",
    "vietinbank": "VIETINBANK",
    "vikki_bank": "VIKKI_BANK",
    "vpbank": "VPBANK",
}


# Configure simple logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("generate_metadata")


def find_json_keys(json_path: str | Path) -> List[str]:
    """Return a sorted list of top-level keys found in a JSON file.

    Handles both dict and list-of-dict JSON structures. Returns an empty list
    when file is missing or cannot be parsed.
    """
    path = Path(json_path)
    if not path.is_file():
        return []

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []

    keys = set()
    if isinstance(data, dict):
        keys.update(data.keys())
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                keys.update(item.keys())
    return sorted(keys)


def generate_metadata(root_dir: str | Path, out_csv: str | Path) -> int:
    """Walk the root_dir and generate a metadata CSV stored at out_csv.

    Returns the number of rows written.
    Raises FileNotFoundError if root_dir does not exist.
    """
    root = Path(root_dir)
    out = Path(out_csv)

    if not root.is_dir():
        raise FileNotFoundError(f"root_dir not found: {root}")

    rows = []
    ingestion_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    id_counter = 1

    for category in sorted(p for p in root.iterdir() if p.is_dir()):
        category_name = category.name
        organization_code = category_name
        organization_name = organization_name_mapping.get(category_name, category_name.upper())

        for unit in sorted(p for p in category.iterdir() if p.is_dir()):
            unit_name_on_disk = unit.name
            rel_unit_path = f"{category_name}/{unit_name_on_disk}/"

            data_json_path = unit / "data.json"
            has_json = data_json_path.exists()

            has_screenshot = any(
                (f.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and 'screenshot' in f.name.lower())
                for f in unit.iterdir()
                if f.is_file()
            )

            json_keys = find_json_keys(data_json_path) if has_json else []

            unit_display_name = unit_name_mapping.get(unit_name_on_disk, unit_name_on_disk.upper())

            rows.append({
                "id": id_counter,
                "organization_code": organization_code,
                "organization_name": organization_name,
                "unit_code": unit_name_on_disk,
                "unit_name": unit_display_name,
                "source_system": SOURCE_SYSTEM,
                "ingestion_date": ingestion_date,
                "relative_path": rel_unit_path,
                "has_json": str(has_json),
                "has_screenshot": str(has_screenshot),
                "json_keys": json.dumps(json_keys, ensure_ascii=False),
            })

            id_counter += 1

    fieldnames = [
        "id",
        "organization_code",
        "organization_name",
        "unit_code",
        "unit_name",
        "source_system",
        "ingestion_date",
        "relative_path",
        "has_json",
        "has_screenshot",
        "json_keys",
    ]

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info("metadata written to: %s (rows: %d)", out, len(rows))
    return len(rows)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate metadata CSV from a folder tree")
    parser.add_argument("root_dir", nargs="?", default=str(Path.cwd() / "data"), help="Root folder containing categories")
    parser.add_argument("out_csv", nargs="?", default=str(Path.cwd() / "metadata.csv"), help="Output CSV path")
    args = parser.parse_args()

    try:
        rows = generate_metadata(args.root_dir, args.out_csv)
        print(f"Wrote {rows} rows to {args.out_csv}")
    except Exception as exc:
        logger.error("Failed to generate metadata: %s", exc)
        raise
