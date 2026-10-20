"""Landing page: the research platform and its two models."""

import streamlit as st

from models.macro_floor_engine import DEFAULT_TICKERS
from ui import kit

MODELS = [
    {
        "page": "views/crude_oil.py",
        "asset_class": "Commodities",
        "name": "WTI Crude Oil Valuation",
        "description": "Estimates a fair value for WTI crude from eight weighted market and macro drivers and measures how far the market price sits from it.",
        "facts": [
            ("Drivers", "8 weighted"),
            ("Fair-value history", "90 sessions"),
            ("Data refresh", "Every 5 min"),
        ],
    },
    {
        "page": "views/macro_floor.py",
        "asset_class": "US Equities · Macro",
        "name": "Macro Floor",
        "description": "Prices US large-cap stocks against sovereign-yield floors and simulates buying only after forced selling below those floors is exhausted.",
        "facts": [
            ("Universe", f"{len(DEFAULT_TICKERS)} US stocks · USD"),
            ("Backtest", "5 years, simulated"),
            ("Paper portfolio", "$100,000 start"),
        ],
    },
]

PRINCIPLES = [
    ("Transparent rules", "Every signal comes from documented formulas, thresholds and weights that can be read in the source code."),
    ("Historical testing", "Crude-oil signals are scored on 5- and 10-day forward returns; Macro Floor is replayed over five years of prices."),
    ("Explicit assumptions", "Inputs are named with their sources — sovereign yields, inventories, ETFs and futures — and shown with their latest values."),
]

kit.html(
    """
<style>
.hm-hero { padding: 48px 0 32px; }
.hm-title { font-size: clamp(34px, 5vw, 52px); font-weight: 650; line-height: 1.08; letter-spacing: -0.03em; color: var(--text); margin: 16px 0 0; }
.hm-title span { color: var(--text-2); font-weight: 500; }
.stApp [data-testid="stMarkdownContainer"] p.hm-lead { font-size: 16px; line-height: 1.6; color: var(--text-2); max-width: 56ch; margin: 16px 0 0; }
[class*="st-key-mcard"] { position: relative; background: var(--surface); border: 1px solid var(--divider); border-radius: 12px; padding: 32px;
  transition: border-color 120ms, background 120ms; height: 100%; }
[class*="st-key-mcard"]:hover { border-color: rgba(52, 211, 153, 0.55); background: var(--surface-2); }
[class*="st-key-mcard"] [data-testid="stElementContainer"], [class*="st-key-mcard"] [data-testid="stPageLink"], [class*="st-key-mcard"] a { position: static !important; }
[class*="st-key-mcard"] [data-testid="stPageLink"] a::after { content: ""; position: absolute; inset: 0; z-index: 2; border-radius: 12px; }
[class*="st-key-mcard"] [data-testid="stPageLink"] a { padding: 0; background: transparent !important; }
[class*="st-key-mcard"] [data-testid="stPageLink"] a p, [class*="st-key-mcard"] [data-testid="stIconMaterial"] { font-size: 14px; font-weight: 600; color: var(--mint); }
.mc-top { display: flex; justify-content: space-between; align-items: center; }
.mc-idx { font-size: 12px; font-weight: 600; color: var(--muted); font-variant-numeric: tabular-nums; }
.mc-name { font-size: 24px; font-weight: 650; letter-spacing: -0.02em; color: var(--text); margin: 32px 0 8px; }
.stApp [data-testid="stMarkdownContainer"] p.mc-desc { font-size: 14px; line-height: 1.6; color: var(--text-2); margin: 0 0 24px; max-width: 52ch; }
.mc-facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-top: 1px solid var(--divider); padding-top: 16px; margin-bottom: 24px; gap: 16px; }
.mc-facts div span { display: block; font-size: 11px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); }
.mc-facts div b { display: block; font-size: 13px; font-weight: 500; color: var(--text); margin-top: 4px; font-variant-numeric: tabular-nums; }
.hm-phil { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 32px; border-top: 1px solid var(--divider); padding-top: 24px; }
.hm-phil b { display: block; font-size: 15px; font-weight: 600; color: var(--text); margin-bottom: 8px; }
.hm-phil span { font-size: 13px; line-height: 1.65; color: var(--text-2); }
.hm-phil-h { font-size: 20px; font-weight: 600; color: var(--text); letter-spacing: -0.01em; margin: 64px 0 24px; }
.hm-phil-h span { color: var(--muted); font-weight: 400; }
@media (max-width: 760px) {
  .hm-hero { padding: 32px 0 24px; } [class*="st-key-mcard"] { padding: 24px; }
  .mc-facts, .hm-phil { grid-template-columns: 1fr; gap: 12px; } .mc-name { margin-top: 24px; }
}
</style>
"""
)

kit.html(
    '<div class="hm-hero"><div class="kt-cat">Independent research</div>'
    '<div class="hm-title">Quantitative Research.<br><span>Financial Models.</span></div>'
    '<p class="hm-lead">Independent, rule-based research across energy markets and global equities — '
    "every model running on live market data.</p></div>"
)

columns = st.columns(len(MODELS), gap="medium")
for index, (column, model) in enumerate(zip(columns, MODELS), start=1):
    with column, st.container(key=f"mcard{index}"):
        facts = "".join(f"<div><span>{label}</span><b>{value}</b></div>" for label, value in model["facts"])
        kit.html(
            f'<div class="mc-top"><span class="kt-cat">{model["asset_class"]}</span><span class="mc-idx">{index:02d}</span></div>'
            f'<div class="mc-name">{model["name"]}</div>'
            f'<p class="mc-desc">{model["description"]}</p>'
            f'<div class="mc-facts">{facts}</div>'
        )
        st.page_link(model["page"], label="Explore model", icon=":material/arrow_forward:", icon_position="right")

principles = "".join(f"<div><b>{title}</b><span>{body}</span></div>" for title, body in PRINCIPLES)
kit.html(
    '<div class="hm-phil-h">Research philosophy <span>· Transparent rules. Historical testing. Explicit assumptions.</span></div>'
    f'<div class="hm-phil">{principles}</div>'
)
