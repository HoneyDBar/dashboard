"""
Amazon Europe P&L Dashboard — Clean White Modern SaaS design
Run: streamlit run app.py
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from data_loader import (
    load_combined, list_pnl_months, list_ppc_months,
    detect_upload_type, save_upload, key_to_label, is_pnl_file, ppc_month_key,
)
from ai_insights import generate_sku_spotlight

load_dotenv()

st.set_page_config(
    page_title="Amazon EU — P&L Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #f5f6f8 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
#MainMenu, footer { display: none !important; }
[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
    height: 44px !important;
    min-height: 44px !important;
}
[data-testid="stToolbar"] {
    background: transparent !important;
    display: flex !important;
    align-items: center !important;
    padding: 6px 0 0 6px !important;
}
/* Hide deploy / share buttons but keep the sidebar toggle */
[data-testid="stAppDeployButton"],
[data-testid="stStatusWidget"],
[data-testid="stDecoration"] { display: none !important; }

/* ── Sidebar toggle buttons (both << and >>) ── */
[data-testid="stExpandSidebarButton"],
[data-testid="stBaseButton-headerNoPadding"] {
    background: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.10) !important;
    width: 32px !important;
    height: 32px !important;
    color: #374151 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    transition: background 0.15s, border-color 0.15s !important;
}
[data-testid="stExpandSidebarButton"]:hover,
[data-testid="stBaseButton-headerNoPadding"]:hover {
    background: #f3f4f6 !important;
    border-color: #9ca3af !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e5e7eb !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }
[data-testid="stSidebarContent"] { padding: 0 !important; }

/* Main container */
[data-testid="block-container"] {
    padding: 16px 36px 60px !important;
    max-width: 1400px;
}

/* ── KPI card ── */
.kpi-card {
    background: #fff; border: 1px solid #e5e7eb;
    border-radius: 12px; padding: 20px 20px 18px;
    position: relative;
}
.kpi-icon {
    position: absolute; top: 16px; right: 16px;
    width: 32px; height: 32px; border-radius: 8px;
    background: #f3f4f6; display: flex;
    align-items: center; justify-content: center; font-size: 15px;
}
.kpi-label { font-size: 11px; font-weight: 600; color: #6b7280;
    text-transform: uppercase; letter-spacing: .06em; margin-bottom: 6px; }
.kpi-value { font-size: 26px; font-weight: 700; color: #111827;
    line-height: 1.1; margin-bottom: 7px; }
.kpi-delta { font-size: 12px; }

.badge-up   { background:#f0fdf4; color:#16a34a; border-radius:99px;
    padding:2px 8px; font-size:11px; font-weight:700; display:inline-block; }
.badge-down { background:#fef2f2; color:#dc2626; border-radius:99px;
    padding:2px 8px; font-size:11px; font-weight:700; display:inline-block; }
.badge-neu  { background:#f3f4f6; color:#6b7280; border-radius:99px;
    padding:2px 8px; font-size:11px; font-weight:600; display:inline-block; }

/* ── Content card (pure HTML sections) ── */
.card {
    background: #fff; border: 1px solid #e5e7eb;
    border-radius: 12px; padding: 20px 22px; margin-bottom: 0;
}
.card-title  { font-size: 14px; font-weight: 600; color: #111827; margin-bottom: 14px; }
.card-sub    { font-size: 12px; color: #9ca3af; margin-top: -10px; margin-bottom: 14px; }

/* ── Rank table ── */
.rank-table { width: 100%; border-collapse: collapse; }
.rank-table th { font-size: 11px; font-weight: 600; color: #9ca3af;
    text-transform: uppercase; letter-spacing: .05em;
    padding: 0 10px 10px; text-align: left; }
.rank-table td { font-size: 13px; color: #374151;
    padding: 9px 10px; border-top: 1px solid #f3f4f6; }
.rank-table tr.neg td { background: #fef9f9 !important; }
.rn { color: #9ca3af; font-size: 12px; font-weight: 600; }
.up   { color: #16a34a; font-weight: 600; }
.down { color: #dc2626; font-weight: 600; }

/* ── Plotly chart wrappers → card look ── */
[data-testid="stPlotlyChart"] > div {
    background: #fff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 12px !important;
    padding: 16px 18px !important;
}
/* ── Section title above chart ── */
.chart-title {
    font-size: 14px; font-weight: 600; color: #111827;
    margin-bottom: 8px; margin-top: 4px;
}

/* ── Dataframe wrapper → card look ── */
[data-testid="stDataFrame"] > div {
    background: #fff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ── Page header ── */
.ph-title { font-size: 24px; font-weight: 700; color: #111827; }
.ph-sub   { font-size: 13px; color: #6b7280; margin-top: 3px; }

/* ── Sidebar nav brand ── */
.nav-brand {
    padding: 18px 18px 12px;
    border-bottom: 1px solid #f3f4f6;
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 6px;
}
.nb-icon { font-size: 22px; }
.nb-name { font-size: 13px; font-weight: 700; color: #111827; line-height: 1.2; }
.nb-sub  { font-size: 11px; color: #9ca3af; }
.nav-footer {
    padding: 14px 18px;
    border-top: 1px solid #f3f4f6;
    font-size: 11px; color: #9ca3af; margin-top: 20px;
}

/* Sidebar radio */
[data-testid="stSidebar"] .stRadio > label { display: none; }
[data-testid="stSidebar"] .stRadio > div {
    display: flex; flex-direction: column; gap: 2px; padding: 0 10px;
}
[data-testid="stSidebar"] .stRadio > div > label {
    display: flex !important; align-items: center; gap: 8px;
    padding: 8px 12px; border-radius: 8px;
    font-size: 13px; font-weight: 500; cursor: pointer;
    color: #374151 !important;
}
/* Force text colour on all inner elements (p, span, div) */
[data-testid="stSidebar"] .stRadio > div > label p,
[data-testid="stSidebar"] .stRadio > div > label span,
[data-testid="stSidebar"] .stRadio > div > label div {
    color: #374151 !important;
    opacity: 1 !important;
}
[data-testid="stSidebar"] .stRadio > div > label:hover { background: #f3f4f6; }
[data-testid="stSidebar"] .stRadio > div > label > div:first-child { display: none; }
/* Sidebar all text — prevent theme leaking */
[data-testid="stSidebar"] * { color: #374151; }
[data-testid="stSidebar"] .nb-name,
[data-testid="stSidebar"] .nb-sub { color: inherit; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { opacity: 1 !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important; border-bottom: 1px solid #e5e7eb;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: #6b7280 !important;
    font-size: 13px !important; font-weight: 500 !important; padding: 8px 14px !important;
}
.stTabs [aria-selected="true"] {
    color: #1d4ed8 !important; border-bottom: 2px solid #1d4ed8 !important;
}

/* Buttons */
.stButton > button {
    border-radius: 8px !important; font-size: 13px !important;
    font-weight: 500 !important; font-family: 'Inter', sans-serif !important;
}
.stButton > button[kind="primary"] {
    background: #1d4ed8 !important; border: none !important; color: #fff !important;
}
.stButton > button[kind="primary"]:hover { background: #1e40af !important; }

/* AI summary box */
.ai-box {
    background: #f8faff; border: 1px solid #dde8ff;
    border-radius: 10px; padding: 16px 18px;
    font-size: 13px; color: #374151; line-height: 1.7;
}
.ai-box ul { margin: 8px 0 0; padding-left: 18px; }
.ai-box li { margin-bottom: 4px; }

/* Spotlight cards */
.spot { border: 1px solid #e5e7eb; border-radius: 10px;
    padding: 14px 16px; margin-bottom: 10px; background: #fff; }
.spot.risk        { border-left: 3px solid #ef4444; }
.spot.opportunity { border-left: 3px solid #22c55e; }
.spot.anomaly     { border-left: 3px solid #f59e0b; }
.stag { display:inline-block; font-size:10px; font-weight:700;
    letter-spacing:.05em; padding:2px 8px; border-radius:99px;
    text-transform:uppercase; margin-bottom:5px; }
.stag.risk        { background:#fef2f2; color:#dc2626; }
.stag.opportunity { background:#f0fdf4; color:#16a34a; }
.stag.anomaly     { background:#fffbeb; color:#d97706; }
.sh { font-size:13px; font-weight:600; color:#111827; margin-bottom:4px; }
.sm { font-size:11px; color:#9ca3af; margin-bottom:5px; }
.sr { font-size:12px; color:#4b5563; margin-bottom:5px; line-height:1.5; }
.sa { font-size:12px; color:#2563eb; font-weight:500; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Data + helpers
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading data…")
def get_data(prev_key: str, curr_key: str):
    return load_combined(prev_key, curr_key)

ai_on = bool(os.getenv("ANTHROPIC_API_KEY", ""))


def eur(v):
    if v is None or (isinstance(v, float) and pd.isna(v)): return "—"
    return f"€{v:,.0f}"

def pct_fmt(v, digits=1):
    if v is None or (isinstance(v, float) and pd.isna(v)): return "—"
    return f"{v:.{digits}f}%"

def _safe_float(v):
    """Return None for NaN/None, otherwise the float."""
    if v is None: return None
    try:
        f = float(v)
        return None if pd.isna(f) else f
    except Exception:
        return None

def badge(v, invert=False, suffix="%", label=""):
    v = _safe_float(v)
    if v is None:
        return f'<span class="badge-neu">— {label}</span>'
    positive = (v > 0) if not invert else (v < 0)
    cls   = "badge-up" if positive else "badge-down"
    arrow = "▲" if v > 0 else "▼"
    return f'<span class="{cls}">{arrow} {abs(v):.1f}{suffix} {label}</span>'

def kpi_card(label, value, delta_pct, icon, invert=False, suffix="%", vs_label=""):
    return f"""
    <div class="kpi-card">
      <div class="kpi-icon">{icon}</div>
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-delta">{badge(delta_pct, invert=invert, suffix=suffix, label=vs_label)}</div>
    </div>"""

_CHART_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=12, color="#374151"),
)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="nav-brand">
      <div class="nb-icon">📦</div>
      <div><div class="nb-name">Amazon Europe</div>
           <div class="nb-sub">P&amp;L Dashboard</div></div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "nav",
        ["🏠  Overview", "🌍  Marketplaces", "📦  Products (ASIN)",
         "📢  PPC Overview", "✨  AI Insights", "📤  Upload Data"],
        label_visibility="collapsed",
    )

    st.divider()

    # ── Month selector ────────────────────────────────────────────────────────
    available = list_pnl_months()
    if len(available) < 2:
        st.warning("Need at least 2 P&L files in data/ to compare months.")
        prev_key = available[0] if available else "march 2026"
        curr_key = available[0] if available else "april 2026"
    else:
        labels = [key_to_label(k) for k in available]
        st.markdown('<span style="font-size:12px;font-weight:600;color:#374151">Compare months</span>', unsafe_allow_html=True)
        prev_idx = st.selectbox("Baseline month", range(len(labels)),
                                format_func=lambda i: labels[i],
                                index=max(0, len(available)-2),
                                key="sel_prev")
        curr_idx = st.selectbox("Current month", range(len(labels)),
                                format_func=lambda i: labels[i],
                                index=len(available)-1,
                                key="sel_curr")
        prev_key = available[prev_idx]
        curr_key = available[curr_idx]

        if prev_key == curr_key:
            st.warning("Select two different months.")

    st.divider()
    st.markdown('<span style="font-size:12px;font-weight:600;color:#374151">Settings</span>', unsafe_allow_html=True)
    top_n          = st.slider("Top N items", 5, 30, 10)
    primary_metric = st.selectbox("Primary metric", ["Net profit", "Sales", "Gross profit", "Units", "Margin"])

    st.markdown(f"""
    <div class="nav-footer">
      AI: {'<b style="color:#16a34a">● Enabled</b>' if ai_on else '<span style="color:#9ca3af">○ No API key</span>'}
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Load data for the selected month pair
# ─────────────────────────────────────────────────────────────────────────────
if "Upload" not in page and prev_key != curr_key:
    data   = get_data(prev_key, curr_key)
    march  = data["march_products"]
    april  = data["april_products"]
    delta  = data["delta_portfolio"]
    ppc    = data["ppc"]
    PREV_LABEL = data.get("prev_label", key_to_label(prev_key))
    CURR_LABEL = data.get("curr_label", key_to_label(curr_key))
else:
    data = march = april = delta = ppc = None
    PREV_LABEL = key_to_label(prev_key) if prev_key else "—"
    CURR_LABEL = key_to_label(curr_key) if curr_key else "—"


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
if "Overview" in page and data is not None:

    col_h, col_btn = st.columns([6, 1])
    with col_h:
        st.markdown(f'<div class="ph-title">Overview</div><div class="ph-sub">{PREV_LABEL} vs {CURR_LABEL} · 7 European marketplaces</div>', unsafe_allow_html=True)
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("↓ Export", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # KPIs
    d_sales  = delta.get("Sales", {})
    d_profit = delta.get("Net profit", {})
    d_units  = delta.get("Units", {})
    d_ads    = delta.get("Ads", {})
    wm       = delta.get("Margin_wavg", {})
    mar_m = _safe_float(wm.get("march")); apr_m = _safe_float(wm.get("april"))
    d_margin_pp = (apr_m - mar_m) if (apr_m is not None and mar_m is not None) else None

    c1, c2, c3, c4, c5 = st.columns(5)
    u = _safe_float(d_units.get("april"))
    _vs = f"vs {PREV_LABEL}"
    with c1: st.markdown(kpi_card("Revenue",    eur(d_sales.get("april")),  d_sales.get("delta_pct"),  "€",  vs_label=_vs), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Net Profit", eur(d_profit.get("april")), d_profit.get("delta_pct"), "📈", vs_label=_vs), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Avg Margin", pct_fmt(apr_m),             d_margin_pp,               "%",  suffix="pp", vs_label=_vs), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("Units Sold", f"{u:,.0f}" if u else "—", d_units.get("delta_pct"),  "🛍", vs_label=_vs), unsafe_allow_html=True)
    with c5: st.markdown(kpi_card("Ad Spend",   eur(abs(_safe_float(d_ads.get("april")) or 0)), d_ads.get("delta_pct"), "📢", invert=True, vs_label=_vs), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Chart + marketplace table
    left, right = st.columns([3, 2], gap="large")

    with left:
        bar_data = []
        for m in ["Sales", "Gross profit", "Net profit"]:
            d = delta.get(m, {})
            bar_data += [
                {"Metric": m, "Month": PREV_LABEL, "Value": d.get("march", 0) or 0},
                {"Metric": m, "Month": CURR_LABEL, "Value": d.get("april", 0) or 0},
            ]
        fig = px.bar(
            pd.DataFrame(bar_data), x="Metric", y="Value", color="Month", barmode="group",
            color_discrete_map={PREV_LABEL: "#818cf8", CURR_LABEL: "#22c55e"},
            template="plotly_white", labels={"Value": "", "Metric": ""},
            title="Performance Overview",
        )
        fig.update_layout(
            **_CHART_BASE,
            legend=dict(orientation="h", y=1.0, x=0, yanchor="bottom", font=dict(size=11), title_text=""),
            height=300, margin=dict(t=70, b=20, l=10, r=30),
            yaxis=dict(gridcolor="#f3f4f6", tickformat="€,.0f", tickfont=dict(size=11)),
            title_font=dict(size=14, color="#111827"),
            title_x=0,
            title_y=0.97,
        )
        fig.update_traces(marker_line_width=0, marker_cornerradius=4)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with right:
        mar_agg = march.groupby("Marketplace")["Net profit"].sum().reset_index().rename(columns={"Net profit": "np_mar"})
        apr_agg = april.groupby("Marketplace")["Net profit"].sum().reset_index().rename(columns={"Net profit": "np_apr"})
        mkt_df  = pd.merge(mar_agg, apr_agg, on="Marketplace", how="outer").fillna(0)
        mkt_df["dp"] = ((mkt_df["np_apr"] - mkt_df["np_mar"]) / mkt_df["np_mar"].abs().replace(0, float("nan")) * 100).round(1)
        mkt_df = mkt_df.sort_values("np_apr", ascending=False).reset_index(drop=True)

        rows = ""
        for i, row in mkt_df.iterrows():
            neg   = row["np_apr"] < 0
            tr    = ' class="neg"' if neg else ""
            dp    = _safe_float(row["dp"])
            if dp is None:   dh = '<span style="color:#9ca3af">—</span>'
            elif dp > 0:     dh = f'<span class="up">▲ {dp:.1f}%</span>'
            else:            dh = f'<span class="down">▼ {abs(dp):.1f}%</span>'
            val_color = "color:#dc2626" if neg else "color:#111827"
            rows += f"""<tr{tr}>
              <td><span class="rn">{i+1}</span></td>
              <td>{row['Marketplace']}</td>
              <td style="text-align:right;font-weight:600;{val_color}">{eur(row['np_apr'])}</td>
              <td style="text-align:right">{dh}</td>
            </tr>"""

        st.markdown(f"""
        <div class="card">
          <div class="card-title">Top Marketplaces by Net Profit ({CURR_LABEL})</div>
          <table class="rank-table">
            <thead><tr>
              <th>#</th><th>Marketplace</th>
              <th style="text-align:right">Net Profit</th>
              <th style="text-align:right">vs {PREV_LABEL}</th>
            </tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # PPC table + AI panel
    col_ppc, col_ai = st.columns([3, 2], gap="large")

    with col_ppc:
        if not ppc.empty and "Sales(EUR)" in ppc.columns:
            agg = ppc.groupby(["country","month"])[["Spend(EUR)","Sales(EUR)"]].sum().reset_index()
            agg["ACOS"] = (agg["Spend(EUR)"] / agg["Sales(EUR)"].replace(0, float("nan")) * 100).round(1)
            agg["ROAS"] = (agg["Sales(EUR)"] / agg["Spend(EUR)"].replace(0, float("nan"))).round(2)
            am = agg[agg["month"]=="march"].set_index("country")
            aa = agg[agg["month"]=="april"].set_index("country")

            def _gv(df, c, col):
                v = df.loc[c, col] if c in df.index else None
                return _safe_float(v)

            rows_ppc = []
            _pm = PREV_LABEL.split()[0]; _cm = CURR_LABEL.split()[0]
            for c in sorted(set(am.index) | set(aa.index)):
                roas_m = _gv(am, c, "ROAS"); roas_a = _gv(aa, c, "ROAS")
                rows_ppc.append({
                    "Country":          c,
                    f"Spend {_pm}":    eur(_gv(am,c,"Spend(EUR)")),
                    f"Spend {_cm}":    eur(_gv(aa,c,"Spend(EUR)")),
                    f"ACOS {_pm}":     pct_fmt(_gv(am,c,"ACOS")),
                    f"ACOS {_cm}":     pct_fmt(_gv(aa,c,"ACOS")),
                    f"ROAS {_pm}":     f"{roas_m:.2f}" if (roas_m is not None and roas_m > 0) else "—",
                    f"ROAS {_cm}":     f"{roas_a:.2f}" if (roas_a is not None and roas_a > 0) else "—",
                })

            st.markdown('<p class="chart-title">PPC Overview (by Country)</p>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(rows_ppc), use_container_width=True, hide_index=True)

    with col_ai:
        st.markdown("""
        <div class="card" style="padding-bottom:12px">
          <div style="display:flex;align-items:center;gap:7px;margin-bottom:3px">
            <span>✨</span>
            <span class="card-title" style="margin:0">SKU Spotlight</span>
          </div>
          <div class="card-sub">Products that need your attention right now</div>
        </div>
        """, unsafe_allow_html=True)

        n_sp = st.slider("Products", 3, 7, 5, key="n_sp_ov")
        if st.button("Find Products to Watch", key="sp_ov", type="primary"):
            with st.spinner("Scanning with Claude…"):
                st.session_state["spots"] = generate_sku_spotlight(data, n=n_sp)
        for s in st.session_state.get("spots", []):
            t = s.get("type","anomaly").lower()
            tags = {"risk":"⚠ Risk","opportunity":"✅ Opportunity","anomaly":"🔍 Anomaly"}
            st.markdown(f"""
            <div class="spot {t}">
              <span class="stag {t}">{tags.get(t,t)}</span>
              <div class="sh">{s.get('headline','')}</div>
              <div class="sm">{s.get('marketplace','')} · {s.get('asin','')} · {s.get('sku','')}</div>
              <div class="sr">{s.get('reason','')}</div>
              <div class="sa">→ {s.get('action','')}</div>
            </div>""", unsafe_allow_html=True)
        if not st.session_state.get("spots"):
            st.caption("Click the button to find products that need attention.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: MARKETPLACES
# ─────────────────────────────────────────────────────────────────────────────
elif "Marketplace" in page and data is not None:
    st.markdown(f'<div class="ph-title">Marketplaces</div><div class="ph-sub">Performance by Amazon marketplace · {PREV_LABEL} vs {CURR_LABEL}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    metric = primary_metric
    mar_a = march.groupby("Marketplace")[metric].sum().reset_index().rename(columns={metric:"mar"})
    apr_a = april.groupby("Marketplace")[metric].sum().reset_index().rename(columns={metric:"apr"})
    df = pd.merge(mar_a, apr_a, on="Marketplace", how="outer").fillna(0)
    df["dp"] = (( df["apr"]-df["mar"]) / df["mar"].abs().replace(0,float("nan")) * 100).round(1)
    df = df.sort_values("apr", ascending=False).reset_index(drop=True)

    col_c, col_t = st.columns([3, 2], gap="large")

    with col_c:
        df_plot = df.sort_values("apr").copy()
        df_plot["_sign"] = df_plot["apr"].apply(lambda x: "positive" if x >= 0 else "negative")
        fig = px.bar(
            df_plot, x="apr", y="Marketplace", orientation="h",
            color="_sign",
            color_discrete_map={"positive": "#22c55e", "negative": "#ef4444"},
            template="plotly_white",
            labels={"apr": f"{metric}", "_sign": ""},
            title=f"{metric} by Marketplace — {CURR_LABEL}",
        )
        fig.update_layout(**_CHART_BASE, height=320,
            margin=dict(t=50, b=10, l=0, r=30),
            title_font=dict(size=14, color="#111827"), title_x=0,
            showlegend=False)
        fig.update_traces(marker_line_width=0, marker_cornerradius=4)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

    with col_t:
        rows = ""
        for i, row in df.iterrows():
            neg = row["apr"] < 0
            tr  = ' class="neg"' if neg else ""
            dp  = _safe_float(row["dp"])
            dh  = (f'<span class="up">▲ {dp:.1f}%</span>' if dp and dp>0
                   else f'<span class="down">▼ {abs(dp):.1f}%</span>' if dp
                   else '<span style="color:#9ca3af">—</span>')
            v   = eur(row["apr"]) if metric != "Units" else f"{int(row['apr']):,}"
            rows += f"""<tr{tr}>
              <td><span class="rn">{i+1}</span></td>
              <td>{row['Marketplace']}</td>
              <td style="text-align:right;font-weight:600;{'color:#dc2626' if neg else ''}">{v}</td>
              <td style="text-align:right">{dh}</td>
            </tr>"""
        fmt_m = eur if metric != "Units" else lambda x: f"{int(x):,}"
        col_label = metric
        st.markdown(f"""
        <div class="card">
          <div class="card-title">{metric} — All Marketplaces</div>
          <table class="rank-table">
            <thead><tr><th>#</th><th>Marketplace</th>
              <th style="text-align:right">{CURR_LABEL}</th>
              <th style="text-align:right">vs {PREV_LABEL}</th>
            </tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: PRODUCTS
# ─────────────────────────────────────────────────────────────────────────────
elif "Products" in page and data is not None:
    st.markdown(f'<div class="ph-title">Products (ASIN)</div><div class="ph-sub">Top products by metric · {PREV_LABEL} vs {CURR_LABEL}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    metric = primary_metric
    mp = march.groupby(["ASIN","SKU","Marketplace"])[metric].sum().reset_index().rename(columns={metric:"mar"})
    ap = april.groupby(["ASIN","SKU","Marketplace"])[metric].sum().reset_index().rename(columns={metric:"apr"})
    df = pd.merge(mp, ap, on=["ASIN","SKU","Marketplace"], how="outer").fillna(0)
    df["dp"] = ((df["apr"]-df["mar"]) / df["mar"].abs().replace(0,float("nan")) * 100).round(1)
    df = df.sort_values("apr", ascending=False)
    top   = df.head(top_n)
    worst = df[df["dp"].notna() & (df["dp"] < 0)].sort_values("dp").head(5)

    col_c, col_w = st.columns([3, 2], gap="large")

    with col_c:
        labels = top["SKU"].replace("", pd.NA).fillna(top["ASIN"]).str[:22]
        fig = px.bar(
            top.assign(label=labels).sort_values("apr"),
            x="apr", y="label", orientation="h",
            template="plotly_white",
            labels={"apr": metric, "label": ""},
            title=f"Top {top_n} Products — {CURR_LABEL} {metric}",
        )
        fig.update_layout(**_CHART_BASE, height=max(280, top_n*34),
            margin=dict(t=50, b=10, l=0, r=30),
            title_font=dict(size=14, color="#111827"), title_x=0)
        fig.update_traces(marker_color="#22c55e", marker_line_width=0, marker_cornerradius=4)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

    with col_w:
        rows = ""
        for _, row in worst.iterrows():
            dp = _safe_float(row["dp"])
            v  = eur(row["apr"]) if metric!="Units" else f"{int(row['apr']):,}"
            mkt = str(row["Marketplace"]).replace("Amazon.","")
            rows += f"""<tr class="neg">
              <td style="font-weight:600;color:#111827">{str(row['SKU'] or row['ASIN'])[:24]}</td>
              <td style="font-size:11px;color:#9ca3af">{mkt}</td>
              <td style="text-align:right;color:#dc2626;font-weight:600">▼ {abs(dp):.1f}%</td>
              <td style="text-align:right">{v}</td>
            </tr>""" if dp is not None else ""
        st.markdown(f"""
        <div class="card">
          <div class="card-title">Biggest Drops ({CURR_LABEL} vs {PREV_LABEL})</div>
          <div class="card-sub">Products with largest % decline</div>
          <table class="rank-table">
            <thead><tr><th>SKU</th><th>Country</th><th style="text-align:right">Δ%</th><th style="text-align:right">{CURR_LABEL}</th></tr></thead>
            <tbody>{rows or '<tr><td colspan="4" style="color:#9ca3af;text-align:center;padding:16px">No significant drops</td></tr>'}</tbody>
          </table>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="chart-title">Full Product Table</p>', unsafe_allow_html=True)
    fmt = eur if metric != "Units" else lambda x: f"{int(x):,}"
    disp = top[["ASIN","SKU","Marketplace","mar","apr","dp"]].copy()
    disp.columns = ["ASIN","SKU","Marketplace",PREV_LABEL,CURR_LABEL,"Δ %"]
    disp[PREV_LABEL] = disp[PREV_LABEL].map(fmt)
    disp[CURR_LABEL] = disp[CURR_LABEL].map(fmt)
    disp["Δ %"]   = disp["Δ %"].map(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
    st.dataframe(disp, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: PPC
# ─────────────────────────────────────────────────────────────────────────────
elif "PPC" in page and data is not None:
    st.markdown(f'<div class="ph-title">PPC Overview</div><div class="ph-sub">Sponsored advertising performance by country · {PREV_LABEL} vs {CURR_LABEL}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if ppc.empty:
        st.info("No PPC data loaded.")
    else:
        agg = ppc.groupby(["country","month"])[["Spend(EUR)","Sales(EUR)","Orders","Clicks","Impressions"]].sum().reset_index()
        agg["ACOS"] = (agg["Spend(EUR)"] / agg["Sales(EUR)"].replace(0,float("nan")) * 100).round(1)
        agg["ROAS"] = (agg["Sales(EUR)"] / agg["Spend(EUR)"].replace(0,float("nan"))).round(2)

        am = agg[agg["month"]=="march"].set_index("country")
        aa = agg[agg["month"]=="april"].set_index("country")

        def _v(df, c, col):
            return _safe_float(df.loc[c, col] if c in df.index else None)

        ts_m = am["Spend(EUR)"].sum();  ts_a = aa["Spend(EUR)"].sum()
        tsl_m = am["Sales(EUR)"].sum(); tsl_a = aa["Sales(EUR)"].sum()
        acos_m_t = ts_m/tsl_m*100 if tsl_m else None
        acos_a_t = ts_a/tsl_a*100 if tsl_a else None
        roas_m_t = tsl_m/ts_m if ts_m else None
        roas_a_t = tsl_a/ts_a if ts_a else None

        c1,c2,c3,c4 = st.columns(4)
        _vs = f"vs {PREV_LABEL}"
        with c1: st.markdown(kpi_card(f"PPC Spend ({CURR_LABEL})",  eur(ts_a),  (ts_a-ts_m)/ts_m*100 if ts_m else None,  "💰", invert=True, vs_label=_vs), unsafe_allow_html=True)
        with c2: st.markdown(kpi_card(f"PPC Sales ({CURR_LABEL})",  eur(tsl_a), (tsl_a-tsl_m)/tsl_m*100 if tsl_m else None, "📊", vs_label=_vs), unsafe_allow_html=True)
        with c3: st.markdown(kpi_card(f"Avg ACOS ({CURR_LABEL})",   pct_fmt(acos_a_t), (acos_a_t-acos_m_t) if (acos_a_t and acos_m_t) else None, "🎯", invert=True, suffix="pp", vs_label=_vs), unsafe_allow_html=True)
        with c4: st.markdown(kpi_card(f"Avg ROAS ({CURR_LABEL})",   f"{roas_a_t:.2f}x" if roas_a_t else "—", (roas_a_t-roas_m_t)/roas_m_t*100 if (roas_a_t and roas_m_t) else None, "🔁", vs_label=_vs), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_fig, col_tbl = st.columns([3, 2], gap="large")

        with col_fig:
            agg_plot = agg.copy()
            agg_plot["month"] = agg_plot["month"].map({"march": PREV_LABEL, "april": CURR_LABEL})
            fig = px.bar(
                agg_plot, x="country", y="Spend(EUR)", color="month", barmode="group",
                color_discrete_map={PREV_LABEL: "#818cf8", CURR_LABEL: "#22c55e"},
                template="plotly_white", title="PPC Spend by Country",
                labels={"Spend(EUR)":"Spend (EUR)","country":"Country","month":""},
            )
            fig.update_layout(**_CHART_BASE, height=290,
                margin=dict(t=50,b=10,l=0,r=0),
                legend=dict(orientation="h",y=1.12,x=0,font=dict(size=11)),
                title_font=dict(size=14,color="#111827"), title_x=0)
            fig.update_traces(marker_line_width=0, marker_cornerradius=4)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

        with col_tbl:
            countries = sorted(set(am.index)|set(aa.index))
            rows_ppc = []
            _pm = PREV_LABEL.split()[0]; _cm = CURR_LABEL.split()[0]
            for c in countries:
                roas_m = _v(am,c,"ROAS"); roas_a = _v(aa,c,"ROAS")
                rows_ppc.append({
                    "Country":              c,
                    f"Spend {_pm}":        eur(_v(am,c,"Spend(EUR)")),
                    f"Spend {_cm}":        eur(_v(aa,c,"Spend(EUR)")),
                    f"ACOS {_pm}":         pct_fmt(_v(am,c,"ACOS")),
                    f"ACOS {_cm}":         pct_fmt(_v(aa,c,"ACOS")),
                    f"ROAS {_pm}":         f"{roas_m:.2f}" if (roas_m is not None and roas_m > 0) else "—",
                    f"ROAS {_cm}":         f"{roas_a:.2f}" if (roas_a is not None and roas_a > 0) else "—",
                })
            st.markdown('<p class="chart-title">Country Detail</p>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(rows_ppc), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: AI INSIGHTS
# ─────────────────────────────────────────────────────────────────────────────
elif "AI" in page and data is not None:
    st.markdown('<div class="ph-title">✨ SKU Spotlight</div><div class="ph-sub">Claude finds the products that need your attention — with a concrete action for each</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if not ai_on:
        st.warning("Add `ANTHROPIC_API_KEY` to `.env` to enable AI features.", icon="⚠️")

    n_sp = st.slider("Products to highlight", 3, 7, 5, key="n_sp_full")
    if st.button("Find Products to Watch", key="sp_full", type="primary"):
        with st.spinner("Scanning with Claude…"):
            st.session_state["spots_full"] = generate_sku_spotlight(data, n=n_sp)

    spots = st.session_state.get("spots_full", [])
    if spots:
        cols = st.columns(2)
        for i, s in enumerate(spots):
            t = s.get("type","anomaly").lower()
            tags = {"risk":"⚠ Risk","opportunity":"✅ Opportunity","anomaly":"🔍 Anomaly"}
            with cols[i % 2]:
                st.markdown(f"""
                <div class="spot {t}">
                  <span class="stag {t}">{tags.get(t,t)}</span>
                  <div class="sh">{s.get('headline','')}</div>
                  <div class="sm">{s.get('marketplace','')} · ASIN: {s.get('asin','')} · SKU: {s.get('sku','')}</div>
                  <div class="sr">{s.get('reason','')}</div>
                  <div class="sa">→ {s.get('action','')}</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.caption("Click the button above to find products that need attention.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: UPLOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
elif "Upload" in page:
    from pathlib import Path
    from data_loader import DATA_DIR, is_pnl_file, is_ppc_file, ppc_month_key, pnl_key

    st.markdown('<div class="ph-title">📤 Upload Data</div><div class="ph-sub">Add new monthly reports — they are saved automatically and the dashboard reloads</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Instructions card ─────────────────────────────────────────────────────
    st.markdown("""
    <div class="card" style="margin-bottom:20px">
      <div class="card-title">Naming rules</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;font-size:13px;color:#374151">
        <div>
          <b style="color:#1d4ed8">P&amp;L files (aggregate)</b><br>
          <code style="background:#f3f4f6;padding:2px 6px;border-radius:4px">may 2026.csv</code><br>
          <code style="background:#f3f4f6;padding:2px 6px;border-radius:4px">june 2026.csv</code><br>
          <span style="color:#6b7280;font-size:12px">Format: [month] [year].csv — all lowercase</span>
        </div>
        <div>
          <b style="color:#1d4ed8">PPC files (per country)</b><br>
          <code style="background:#f3f4f6;padding:2px 6px;border-radius:4px">DE_May_2026.csv</code><br>
          <code style="background:#f3f4f6;padding:2px 6px;border-radius:4px">FR_June_2026.csv</code><br>
          <span style="color:#6b7280;font-size:12px">Format: [CC]_[Month]_[Year].csv — country code first</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── File uploader ─────────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "Drop your CSV files here or click to browse",
        type=["csv"],
        accept_multiple_files=True,
        help="You can upload multiple files at once — mix P&L and PPC files freely.",
        label_visibility="visible",
    )

    if uploaded:
        st.markdown("<br>", unsafe_allow_html=True)
        results = []

        for f in uploaded:
            fname = f.name.strip()
            fpath = Path(fname)
            ftype = detect_upload_type(fname)

            # ── Detect what this file is ──────────────────────────────────────
            if ftype == "ppc":
                mk = ppc_month_key(fpath)
                country = fname.split("_")[0].upper()
                if mk:
                    description = f"PPC · {country} · {key_to_label(mk)}"
                    status = "ok"
                else:
                    description = f"PPC · {country} · ⚠ could not detect month from filename"
                    status = "warn"
            else:
                # P&L: the stem should be "[month] [year]"
                from data_loader import _MONTH_NAMES
                stem = fpath.stem.lower().strip()
                has_month = any(stem.startswith(m) for m in _MONTH_NAMES)
                if has_month:
                    description = f"P&L · {key_to_label(stem)}"
                    status = "ok"
                else:
                    description = f"P&L · ⚠ rename to e.g. 'may 2026.csv' — current name not recognised"
                    status = "warn"

            results.append({"file": f, "fname": fname, "type": ftype,
                             "desc": description, "status": status})

        # ── Preview table ─────────────────────────────────────────────────────
        rows_html = ""
        for r in results:
            icon  = "✅" if r["status"] == "ok" else "⚠️"
            badge_cls = "badge-up" if r["status"] == "ok" else "badge-neu"
            type_label = "P&L" if r["type"] == "pnl" else "PPC"
            rows_html += f"""<tr>
              <td style="font-weight:600;color:#111827">{r['fname']}</td>
              <td><span class="{badge_cls}" style="font-size:11px">{type_label}</span></td>
              <td style="color:#374151">{r['desc']}</td>
              <td style="text-align:center;font-size:16px">{icon}</td>
            </tr>"""

        st.markdown(f"""
        <div class="card">
          <div class="card-title">Files ready to save ({len(results)})</div>
          <table class="rank-table">
            <thead><tr>
              <th>Filename</th><th>Type</th><th>Detected as</th><th style="text-align:center">Ready?</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Save button ───────────────────────────────────────────────────────
        ok_count   = sum(1 for r in results if r["status"] == "ok")
        warn_count = sum(1 for r in results if r["status"] == "warn")

        if warn_count:
            st.warning(f"{warn_count} file(s) have naming issues (see table above). They will still be saved but may not be recognised by the dashboard.", icon="⚠️")

        col_btn, col_info = st.columns([2, 5])
        with col_btn:
            save_clicked = st.button(
                f"💾 Save {ok_count + warn_count} file(s) & Reload",
                type="primary",
                use_container_width=True,
            )

        if save_clicked:
            saved, failed = [], []
            for r in results:
                try:
                    dest = save_upload(r["file"].getvalue(), r["fname"])
                    saved.append(r["fname"])
                except Exception as e:
                    failed.append((r["fname"], str(e)))

            if saved:
                st.success(f"✅ Saved {len(saved)} file(s): {', '.join(saved)}", icon="✅")

            if failed:
                for name, err in failed:
                    st.error(f"❌ {name}: {err}")

            if saved:
                # Clear cache so data reloads with new files
                get_data.clear()
                st.info("Cache cleared — go to Overview or switch months in the sidebar to see the new data.", icon="🔄")
                st.balloons()

    else:
        # ── Empty state ───────────────────────────────────────────────────────
        st.markdown("""
        <div style="text-align:center;padding:60px 0;color:#9ca3af">
          <div style="font-size:48px;margin-bottom:12px">📂</div>
          <div style="font-size:15px;font-weight:500;color:#374151">Drag &amp; drop your CSV files above</div>
          <div style="font-size:13px;margin-top:6px">You can upload P&amp;L and PPC files at the same time</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Current data inventory ────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="chart-title">Files currently in data/</p>', unsafe_allow_html=True)

    all_files = sorted(DATA_DIR.glob("*.csv"))
    inv_rows = []
    for f in all_files:
        if is_pnl_file(f):
            ftype = "P&L"
            detail = key_to_label(pnl_key(f))
        elif is_ppc_file(f):
            ftype = "PPC"
            mk = ppc_month_key(f)
            country = f.stem.split("_")[0].upper()
            detail = f"{country} · {key_to_label(mk)}" if mk else f"{country} · unknown month"
        else:
            ftype = "Other"
            detail = "—"
        size_kb = round(f.stat().st_size / 1024, 1)
        inv_rows.append({"File": f.name, "Type": ftype, "Period": detail, "Size": f"{size_kb} KB"})

    if inv_rows:
        st.dataframe(pd.DataFrame(inv_rows), use_container_width=True, hide_index=True)
    else:
        st.caption("No CSV files found in data/ folder.")
