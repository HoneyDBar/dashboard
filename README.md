# Amazon Europe P&L Dashboard

Interactive analytics dashboard for Amazon EU sales data — March vs April 2026 across 7 countries.

---

## Quick Start (under 2 minutes)

```bash
# 1. Install dependencies (one-time)
pip install -r requirements.txt

# 2. Add your Anthropic API key (required for AI features)
cp .env.example .env
# edit .env and paste your key: ANTHROPIC_API_KEY=sk-ant-...

# 3. Launch the dashboard
streamlit run app.py
```

The browser opens automatically at `http://localhost:8501`.

**The `data/` folder already contains the CSV files.** If you want to use new reports,
replace the files in `data/` — the naming convention is flexible (the loader normalises it).

---

## What's in the dashboard

### Block 1 — Portfolio Overview
Five KPI cards (Revenue, Net Profit, Avg Margin, Units, Ad Spend) with colour-coded
MoM deltas. A grouped bar chart gives a one-glance view of Sales / Gross Profit /
Net Profit side by side for both months.

### Block 2 — Breakdown by Marketplace or SKU
Configurable (sidebar) horizontal bar chart of the top N items by any metric.
Colour: green = positive, red = negative.
A "Biggest drops" panel shows the 5 worst performers immediately.
A full table is available via an expandable section.

### Block 3 — PPC Overview
Country-level PPC table (Spend, ACOS, ROAS) plus a grouped bar chart.
Integrated automatically from the 14 country PPC CSV files — no manual joining needed.

### Block 4 — ✨ SKU Spotlight (AI feature)
One click surfaces 3–7 products that deserve immediate attention — risks, opportunities,
and anomalies — each with a concrete recommended action for the sales manager.

---

## Why SKU Spotlight — and why only one AI feature

The task asked for **one** AI feature. Three options were offered as examples:
auto-commentary, product spotlight, and natural-language Q&A.

I chose **SKU Spotlight** because it is the most directly actionable for a
non-technical sales manager:

- An **auto-summary** tells you what changed — but the numbers on the dashboard
  already do that. It adds a layer of interpretation without changing what you do next.
- **Q&A** is powerful but requires the user to know what to ask — which defeats the
  purpose of automation when the goal is to surface what you *don't know to look for*.
- **Spotlight** goes straight to decisions: here are the 3–5 things that need your
  attention, here is why, here is what to do. No prior knowledge of the data required.

**Note on scope:** I built and tested all three features during development to validate
the approach. The executive summary and Q&A are fully working in `ai_insights.py` and
took roughly the same effort as Spotlight. I removed them from the UI intentionally —
not because they aren't useful, but because shipping one focused, well-justified feature
is better than shipping three features that dilute each other. If the team finds value in
Spotlight, adding the other two is a one-session task.

---

## Stack choices and why

| Layer | Choice | Reason |
|-------|--------|--------|
| Framework | **Streamlit** | Zero front-end code; non-technical users run it with one command; rapid iteration |
| Data | **pandas** | Best-in-class for CSV wrangling; handles European notation, BOM, mixed separators |
| Charts | **Plotly** | Interactive, light-theme native, no extra JS |
| AI | **Claude Haiku** | Fastest + cheapest Claude model; sufficient for structured data commentary; low latency means the UI stays snappy |
| Config | **python-dotenv** | Keeps the API key out of code; easy for non-devs to configure |

---

## Data engineering notes

- **European number notation** (`1 234,56`) is normalised by stripping non-breaking spaces and
  swapping the decimal comma for a dot before any arithmetic.
- **BOM** on some files is stripped via `encoding="utf-8-sig"`.
- **Inconsistent filenames** (`NL_march_2026.csv`, `DE_April__2026.csv`) are handled by
  lower-casing the stem and scanning for month-name substrings rather than parsing
  a strict pattern.
- **Row structure**: Each P&L file has marketplace subtotal rows (empty ASIN) and product rows.
  The loader forward-fills the marketplace name so every product row carries its country.
- **PPC join**: Products column (`ASIN-SKU`) is split on the first `-` to recover ASIN and SKU
  separately. PPC data is kept in a separate frame and shown as a standalone block; merging with
  P&L is intentionally not done (different granularities would require assumptions about
  attribution that could mislead).

---

## What I'd add with more time

1. **Incremental import**: a SQLite backend (via `duckdb` or `sqlite3`) where each month's CSV
   is upserted on load — identified by `(ASIN, Marketplace, month)`. The dashboard would query
   the DB instead of reading files on every load.
2. **Trend view**: sparklines per SKU showing 3-month rolling history once more months are loaded.
3. **PPC ↔ P&L merge**: join on ASIN + country to show blended ACOS and true net profit after
   ad spend at the SKU level; currently the P&L `Ads` column gives totals but not the
   per-ASIN PPC breakdown.
4. **AI-powered anomaly detection**: flag SKUs where Sessions dropped but conversion held (listing
   issue) vs Sessions held but conversion dropped (pricing / content issue).
5. **Export button**: one-click Excel export of the full delta table for sharing in Slack.
6. **Executive summary + Q&A**: as noted above, both features are already built in `ai_insights.py`
   and can be re-enabled with minimal effort once the team validates the core Spotlight flow.
