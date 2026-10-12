"""Landing page: the collection of models."""

import streamlit as st

from ui import kit

GITHUB_URL = "https://github.com/dozpiskin"

MODELS = [
    {
        "page": "views/crude_oil.py",
        "asset_class": "Commodities",
        "name": "WTI Crude Oil Valuation",
        "description": "Fair value from eight weighted macro drivers, mapped to a five-level temperature signal.",
        "meta": ["8 drivers", "90-day fair-value history", "Refreshed every 5 min"],
    },
    {
        "page": "views/macro_floor.py",
        "asset_class": "Equities · US & BIST",
        "name": "Macro Floor",
        "description": "Buys crisis bottoms once forced selling below sovereign-yield floors is exhausted.",
        "meta": ["20 instruments", "5-year backtest", "$100K paper fund"],
    },
]

# Upcoming work, shown under the models when not empty: (name, one-line idea).
PIPELINE: list[tuple[str, str]] = []

kit.html(
    """
<style>
.hm-hero { padding: 72px 0 40px; }
.hm-title { font-family: var(--serif); font-weight: 400; font-size: clamp(52px, 8vw, 104px); line-height: 0.95; letter-spacing: -0.02em; color: var(--text); margin: 18px 0 0; }
.hm-title em { color: var(--gold); }
.stApp [data-testid="stMarkdownContainer"] p.hm-lead { font-size: 17px; line-height: 1.6; color: var(--text-2); max-width: 52ch; margin: 26px 0 0; }
[class*="st-key-mcard"] { position: relative; border: 1px solid var(--line); background: var(--surface); padding: 34px 34px 28px; transition: border-color .3s, background .3s; }
[class*="st-key-mcard"]:hover { border-color: rgba(201, 169, 110, 0.45); background: #0d0d0d; }
[class*="st-key-mcard"] [data-testid="stElementContainer"], [class*="st-key-mcard"] [data-testid="stPageLink"], [class*="st-key-mcard"] a { position: static !important; }
[class*="st-key-mcard"] [data-testid="stPageLink"] a::after { content: ""; position: absolute; inset: 0; z-index: 2; }
[class*="st-key-mcard"] [data-testid="stPageLink"] a { padding: 0; background: transparent !important; }
[class*="st-key-mcard"] [data-testid="stPageLink"] a p { font-size: 13px; color: var(--text-2); letter-spacing: 0.02em; }
[class*="st-key-mcard"]:hover [data-testid="stPageLink"] a p, [class*="st-key-mcard"]:hover [data-testid="stIconMaterial"] { color: var(--gold); }
.mc-top { display: flex; justify-content: space-between; font-size: 11px; letter-spacing: 0.2em; text-transform: uppercase; color: var(--muted); }
.mc-top span:first-child { font-family: var(--mono); letter-spacing: 0; color: var(--gold); }
.mc-name { font-family: var(--serif); font-size: 40px; line-height: 1.05; color: var(--text); margin: 48px 0 12px; }
.stApp [data-testid="stMarkdownContainer"] p.mc-desc { font-size: 14.5px; line-height: 1.6; color: var(--text-2); margin: 0 0 26px; max-width: 46ch; }
.mc-meta { display: flex; flex-wrap: wrap; gap: 8px 18px; font-family: var(--mono); font-size: 11.5px; color: var(--muted); border-top: 1px solid var(--line); padding-top: 16px; margin-bottom: 18px; }
.hm-about { display: grid; grid-template-columns: 1fr 2fr; gap: 32px; margin-top: 8px; padding-top: 20px; }
.stApp [data-testid="stMarkdownContainer"] .hm-about p { font-size: 15px; line-height: 1.7; color: var(--text-2); margin: 0; max-width: 60ch; }
.hm-about a { color: var(--text); text-decoration: none; border-bottom: 1px solid var(--gold); }
@media (max-width: 760px) { .hm-about { grid-template-columns: 1fr; gap: 8px; } [class*="st-key-mcard"] { padding: 26px 22px 22px; } .mc-name { margin-top: 32px; } }
</style>
"""
)

kit.html(
    '<div class="hm-hero"><div class="kt-eyebrow">Quantitative research</div>'
    '<div class="hm-title">Ozpiskin<br><em>Financial Models</em></div>'
    '<p class="hm-lead">Rule-based valuation models for commodities and equities, running live on market data.</p></div>'
)

kit.section("Models", f"{len(MODELS):02d}")
columns = st.columns(len(MODELS), gap="medium")
for index, (column, model) in enumerate(zip(columns, MODELS), start=1):
    with column, st.container(key=f"mcard{index}"):
        meta = "".join(f"<span>{item}</span>" for item in model["meta"])
        kit.html(
            f'<div class="mc-top"><span>{index:02d}</span><span>{model["asset_class"]}</span></div>'
            f'<div class="mc-name">{model["name"]}</div>'
            f'<p class="mc-desc">{model["description"]}</p>'
            f'<div class="mc-meta">{meta}</div>'
        )
        st.page_link(model["page"], label="Open model", icon=":material/arrow_forward:", icon_position="right")

if PIPELINE:
    kit.section("In development", f"{len(PIPELINE):02d}")
    kit.table(["Model", "Idea"], [(f'<span class="strong">{name}</span>', idea) for name, idea in PIPELINE])

kit.section("About")
kit.html(
    '<div class="hm-about"><div class="kt-meta">Derin Özpişkin</div>'
    "<p>Each model is a self-contained research project: transparent rules, tested on history, measured against "
    f'macro opportunity cost. All code is open on <a href="{GITHUB_URL}" target="_blank">GitHub</a>.</p></div>'
)
