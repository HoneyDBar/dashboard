"""
Loads and normalises Amazon P&L and PPC CSVs.

P&L files  : semicolon-delimited, European number notation (space=thousands, comma=decimal)
             Naming convention: "[month] [year].csv"  e.g. "march 2026.csv", "may 2026.csv"

PPC files  : comma-delimited, regular notation, Products column = "ASIN-SKU"
             Naming convention: "[CC]_[month]_[year].csv"  e.g. "DE_May_2026.csv"

Auto-discovery: the loader scans DATA_DIR for available months — no hardcoding required.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

_MONTH_NAMES = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]
_MONTH_ORDER = {m: i for i, m in enumerate(_MONTH_NAMES)}

_PPC_COUNTRIES = {"BE", "DE", "ES", "FR", "IT", "NL", "PL"}


# ── file classification ───────────────────────────────────────────────────────

def is_pnl_file(path: Path) -> bool:
    """True if the file is a P&L aggregate (starts with a month name)."""
    stem = path.stem.lower().strip()
    return any(stem.startswith(m) for m in _MONTH_NAMES)


def is_ppc_file(path: Path) -> bool:
    """True if the file is a country-level PPC report (starts with a country code)."""
    prefix = path.stem.split("_")[0].upper()
    return prefix in _PPC_COUNTRIES


# ── month key helpers ─────────────────────────────────────────────────────────

def pnl_key(path: Path) -> str:
    """Return the month key for a P&L file: 'march 2026', 'may 2026', etc."""
    return path.stem.lower().strip()          # e.g. "march 2026"


def ppc_month_key(path: Path) -> str | None:
    """Extract 'may 2026' style key from a PPC filename like DE_May_2026.csv."""
    parts = path.stem.lower().replace("__", "_").split("_")
    month = next((p for p in parts if p in _MONTH_NAMES), None)
    year  = next((p for p in parts if re.fullmatch(r"\d{4}", p)), None)
    if month and year:
        return f"{month} {year}"
    return None


def key_to_label(key: str) -> str:
    """'march 2026'  →  'March 2026'"""
    parts = key.split()
    return " ".join(p.capitalize() for p in parts)


# ── discovery ─────────────────────────────────────────────────────────────────

def list_pnl_months() -> list[str]:
    """
    Return available P&L month keys sorted chronologically.
    E.g. ['march 2026', 'april 2026', 'may 2026']
    """
    keys = []
    for f in DATA_DIR.glob("*.csv"):
        if is_pnl_file(f):
            keys.append(pnl_key(f))

    def _sort_key(k):
        parts = k.split()
        month_name = parts[0] if parts else ""
        year = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        return (year, _MONTH_ORDER.get(month_name, 99))

    return sorted(set(keys), key=_sort_key)


def list_ppc_months() -> list[str]:
    """Return available PPC month keys sorted chronologically."""
    keys = set()
    for f in DATA_DIR.glob("*.csv"):
        if is_ppc_file(f):
            k = ppc_month_key(f)
            if k:
                keys.add(k)

    def _sort_key(k):
        parts = k.split()
        month_name = parts[0] if parts else ""
        year = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        return (year, _MONTH_ORDER.get(month_name, 99))

    return sorted(keys, key=_sort_key)


# ── helpers ───────────────────────────────────────────────────────────────────

def _eu_to_float(val):
    if pd.isna(val) or str(val).strip() in ("", "-", "–"):
        return float("nan")
    s = re.sub(r"[\s ]", "", str(val).strip())   # remove all space variants
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def _normalise_eu_columns(df, skip=("Marketplace / Product", "ASIN", "SKU", "Marketplace")):
    for col in df.columns:
        if col not in skip:
            df[col] = df[col].apply(_eu_to_float)
    return df


# ── P&L loader ────────────────────────────────────────────────────────────────

def load_pnl(month_key: str) -> pd.DataFrame:
    """
    Load the P&L file for a given month key (e.g. 'march 2026', 'may 2026').
    The file must exist at DATA_DIR / f"{month_key}.csv".
    """
    path = DATA_DIR / f"{month_key}.csv"
    if not path.exists():
        raise FileNotFoundError(f"P&L file not found: {path}")

    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str, on_bad_lines="skip")
    df.columns = [c.strip().lstrip("﻿") for c in df.columns]
    if df.columns[0] != "Marketplace / Product":
        df = df.rename(columns={df.columns[0]: "Marketplace / Product"})

    # Forward-fill marketplace names (rows where ASIN is empty and name starts with "Amazon.")
    is_mkt_row = (
        (df["ASIN"].isna() | (df["ASIN"].str.strip() == "")) &
        df["Marketplace / Product"].str.strip().str.startswith("Amazon.", na=False)
    )
    df["Marketplace"] = df["Marketplace / Product"].where(is_mkt_row)
    df["Marketplace"] = df["Marketplace"].ffill()

    # Subtotal rows = any row with empty ASIN
    is_subtotal = (df["ASIN"].isna() | (df["ASIN"].str.strip() == "")).astype(bool)

    df["ASIN"] = df["ASIN"].fillna("").str.strip()
    df["SKU"]  = df["SKU"].fillna("").str.strip()

    # Save non-numeric cols before normalisation (normalisation would corrupt them)
    marketplace = df["Marketplace"].copy()
    _normalise_eu_columns(df, skip=("Marketplace / Product", "ASIN", "SKU", "Marketplace"))
    df["is_subtotal"] = is_subtotal
    df["Marketplace"] = marketplace
    df["month"] = month_key
    return df


def load_pnl_products(month_key: str) -> pd.DataFrame:
    return load_pnl(month_key)[lambda d: ~d["is_subtotal"]].copy()


def load_pnl_marketplace_totals(month_key: str) -> pd.DataFrame:
    return load_pnl(month_key)[lambda d: d["is_subtotal"]].copy()


# ── PPC loader ────────────────────────────────────────────────────────────────

def load_ppc_all(month_keys: Optional[list] = None) -> pd.DataFrame:
    """
    Load country-level PPC files.
    If month_keys is provided (e.g. ['march 2026', 'april 2026']),
    only files whose month key matches are loaded.
    """
    frames = []
    for path in sorted(DATA_DIR.glob("*.csv")):
        if not is_ppc_file(path):
            continue
        mk = ppc_month_key(path)
        if mk is None:
            continue
        if month_keys and mk not in month_keys:
            continue

        country = path.stem.split("_")[0].upper()
        try:
            df = pd.read_csv(path, encoding="utf-8-sig", dtype=str, on_bad_lines="skip")
        except Exception:
            continue
        df.columns = [c.strip() for c in df.columns]
        df["country"] = country
        df["month"]   = mk

        if "Products" in df.columns:
            split = df["Products"].str.split("-", n=1, expand=True)
            df["ASIN"]    = split[0].str.strip()
            df["SKU_ppc"] = split[1].str.strip() if split.shape[1] > 1 else ""

        for col in ["Sales(EUR)", "Spend(EUR)", "ROAS", "ACOS", "Clicks",
                    "Impressions", "CTR", "Orders", "CPC(EUR)", "Conversion rate"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        frames.append(df)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ── upload helpers ────────────────────────────────────────────────────────────

def detect_upload_type(filename: str) -> str:
    """
    Returns 'pnl' or 'ppc' based on the filename.
    A file is PPC if it starts with a known country code followed by '_'.
    """
    prefix = filename.split("_")[0].upper()
    return "ppc" if prefix in _PPC_COUNTRIES else "pnl"


def save_upload(file_bytes: bytes, filename: str) -> Path:
    """Save uploaded file bytes to DATA_DIR and return the saved path."""
    dest = DATA_DIR / filename
    dest.write_bytes(file_bytes)
    return dest


# ── combined loader ───────────────────────────────────────────────────────────

def load_combined(prev_key: str, curr_key: str) -> dict:
    """
    Load and combine data for two months.
    prev_key : 'march 2026'  (the "baseline" month — labelled 'march' internally)
    curr_key : 'april 2026'  (the "current" month  — labelled 'april' internally)
    """
    prev = load_pnl_products(prev_key)
    curr = load_pnl_products(curr_key)
    prev_tot = load_pnl_marketplace_totals(prev_key)
    curr_tot = load_pnl_marketplace_totals(curr_key)
    ppc  = load_ppc_all(month_keys=[prev_key, curr_key])

    # Normalise internal month labels so app.py can stay unchanged
    prev["month"] = "march"
    curr["month"] = "april"

    def _sum(df, col):
        return df[col].sum(min_count=1)

    metrics = ["Sales", "Net profit", "Gross profit", "Units", "Refunds",
               "Amazon fees", "Cost of Goods", "Margin", "Ads"]

    delta = {}
    for m in metrics:
        if m in prev.columns and m in curr.columns:
            vm = _sum(prev, m);  va = _sum(curr, m)
            delta[m] = {
                "march": vm, "april": va,
                "delta": va - vm,
                "delta_pct": (va - vm) / abs(vm) * 100 if vm else None,
            }

    for label, df in [("march", prev), ("april", curr)]:
        sales = df["Sales"].sum()
        if sales and "Margin" in df.columns:
            delta.setdefault("Margin_wavg", {})[label] = (
                (df["Margin"] * df["Sales"]).sum() / sales
            )

    # Normalise PPC month labels to match prev/curr
    if not ppc.empty:
        ppc["month"] = ppc["month"].map({prev_key: "march", curr_key: "april"}).fillna(ppc["month"])

    return {
        "march_products": prev,
        "april_products": curr,
        "march_totals":   prev_tot,
        "april_totals":   curr_tot,
        "ppc":            ppc,
        "delta_portfolio": delta,
        "prev_label": key_to_label(prev_key),
        "curr_label": key_to_label(curr_key),
    }
