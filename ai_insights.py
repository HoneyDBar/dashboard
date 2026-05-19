"""
AI insights via Claude API.
Generates:
  1. Executive summary  — plain-language MoM commentary (3-5 sentences)
  2. SKU spotlight      — 3-5 products that need attention and why
  3. Natural-language Q&A — answer ad-hoc questions about the data
"""

import os
import json
import textwrap
from typing import Optional

import pandas as pd
import anthropic
from dotenv import load_dotenv

load_dotenv()

_MODEL = "claude-haiku-4-5-20251001"


def _get_client() -> Optional[anthropic.Anthropic]:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        return None
    return anthropic.Anthropic(api_key=key)


def _build_portfolio_context(data: dict) -> str:
    """Serialise the key numbers into a compact text block for the prompt."""
    delta = data["delta_portfolio"]
    lines = ["## Portfolio summary: March → April 2026\n"]

    fmt = lambda v: f"{v:,.2f}" if v is not None and not (isinstance(v, float) and pd.isna(v)) else "n/a"
    pct = lambda v: f"{v:+.1f}%" if v is not None and not (isinstance(v, float) and pd.isna(v)) else ""

    for metric, vals in delta.items():
        if metric == "Margin_wavg":
            continue
        m = vals.get("march")
        a = vals.get("april")
        d = vals.get("delta_pct")
        lines.append(f"- {metric}: March={fmt(m)} → April={fmt(a)}  ({pct(d)})")

    # weighted-average margin
    wm = delta.get("Margin_wavg", {})
    if wm:
        lines.append(f"- Margin (weighted avg): March={fmt(wm.get('march'))}% → April={fmt(wm.get('april'))}%")

    return "\n".join(lines)


def _build_sku_context(march: pd.DataFrame, april: pd.DataFrame, top_n: int = 30) -> str:
    """Build a compact product-level delta table for the prompt."""
    key_cols = ["ASIN", "SKU", "Marketplace", "Sales", "Net profit", "Margin", "Units", "Ads"]

    def _prep(df, suffix):
        cols = [c for c in key_cols if c in df.columns]
        return df[cols].rename(columns={c: f"{c}_{suffix}" for c in cols if c not in ("ASIN", "SKU", "Marketplace")})

    m = _prep(march, "mar")
    a = _prep(april, "apr")

    merged = pd.merge(
        m, a,
        on=[c for c in ("ASIN", "SKU", "Marketplace") if c in m.columns and c in a.columns],
        how="outer",
        suffixes=("", ""),
    )

    for base in ("Sales", "Net profit", "Units"):
        mc, ac = f"{base}_mar", f"{base}_apr"
        if mc in merged.columns and ac in merged.columns:
            merged[f"{base}_delta_pct"] = (
                (merged[ac] - merged[mc]) / merged[mc].abs() * 100
            ).round(1)

    if "Sales_apr" in merged.columns:
        merged = merged.sort_values("Sales_apr", ascending=False)

    # keep top products by april sales + worst performers
    top = merged.head(top_n)

    # convert to compact JSON
    records = []
    for _, row in top.iterrows():
        rec = {
            "ASIN": row.get("ASIN", ""),
            "SKU": row.get("SKU", ""),
            "Marketplace": row.get("Marketplace", ""),
        }
        for col in ["Sales_mar", "Sales_apr", "Sales_delta_pct",
                    "Net profit_mar", "Net profit_apr", "Net profit_delta_pct",
                    "Margin_mar", "Margin_apr", "Units_mar", "Units_apr",
                    "Ads_mar", "Ads_apr"]:
            if col in row.index:
                val = row[col]
                rec[col] = round(float(val), 2) if pd.notna(val) else None
        records.append(rec)

    return json.dumps(records, ensure_ascii=False, indent=2)


# ── public API ────────────────────────────────────────────────────────────────

def generate_executive_summary(data: dict) -> str:
    """3-5 sentence plain-language MoM summary."""
    client = _get_client()
    if client is None:
        return "⚠️  Set ANTHROPIC_API_KEY in .env to enable AI commentary."

    portfolio_ctx = _build_portfolio_context(data)
    sku_ctx = _build_sku_context(data["march_products"], data["april_products"])

    prompt = textwrap.dedent(f"""
        You are a senior e-commerce analyst. Below is real Amazon sales data comparing March and April 2026
        across 7 European marketplaces. Write a concise executive summary (3-5 sentences) in plain English
        that a non-technical sales manager can immediately understand. Focus on:
        - Whether the overall business improved or declined and by how much
        - The single most important positive development
        - The single most important concern
        Use concrete numbers from the data. Be direct, no fluff.

        {portfolio_ctx}

        Top products delta (JSON):
        {sku_ctx[:3000]}
    """).strip()

    resp = client.messages.create(
        model=_MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def generate_sku_spotlight(data: dict, n: int = 5) -> list[dict]:
    """
    Returns a list of dicts, each with keys:
      sku, asin, marketplace, headline, reason, action
    """
    client = _get_client()
    if client is None:
        return []

    sku_ctx = _build_sku_context(data["march_products"], data["april_products"], top_n=50)

    prompt = textwrap.dedent(f"""
        You are a senior Amazon marketplace analyst. Based on the product-level March→April delta data below,
        identify exactly {n} products that deserve immediate attention (can be good outliers, bad outliers,
        or anomalies). For each product return a JSON object with:
          - "sku": the SKU string
          - "asin": the ASIN
          - "marketplace": the marketplace name
          - "headline": one bold sentence (max 12 words) naming the issue or opportunity
          - "reason": 1-2 sentences explaining the underlying data signal
          - "action": one concrete recommended action for a sales manager
          - "type": one of "risk", "opportunity", "anomaly"

        Return ONLY a valid JSON array of {n} objects, no markdown, no explanation outside the array.

        Product data:
        {sku_ctx[:4000]}
    """).strip()

    resp = client.messages.create(
        model=_MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = resp.content[0].text.strip()
    # strip accidental markdown fences
    raw = raw.strip("```json").strip("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # try to extract array substring
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start:end])
            except Exception:
                pass
        return [{"sku": "parse error", "asin": "", "marketplace": "",
                 "headline": "Could not parse AI response", "reason": raw[:200],
                 "action": "", "type": "anomaly"}]


def answer_question(data: dict, question: str) -> str:
    """Natural-language Q&A: answer a question about the data."""
    client = _get_client()
    if client is None:
        return "⚠️  Set ANTHROPIC_API_KEY in .env to enable AI Q&A."

    portfolio_ctx = _build_portfolio_context(data)
    sku_ctx = _build_sku_context(data["march_products"], data["april_products"], top_n=60)

    prompt = textwrap.dedent(f"""
        You are an Amazon marketplace data analyst. You have access to March and April 2026 sales data
        for 7 European countries. Answer the user's question concisely and accurately using the data.
        If the data does not contain enough information to answer, say so clearly.
        Use specific numbers where possible.

        Portfolio summary:
        {portfolio_ctx}

        Product-level data (top 60 by April sales):
        {sku_ctx[:4000]}

        User question: {question}
    """).strip()

    resp = client.messages.create(
        model=_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()
