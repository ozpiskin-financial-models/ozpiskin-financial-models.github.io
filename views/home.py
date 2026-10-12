"""Landing page: the collection of models, the research pipeline and an about block."""

import streamlit as st

GITHUB_URL = "https://github.com/dozpiskin"

MODELS = [
    {
        "page": "views/crude_oil.py",
        "name": "WTI Crude Oil Valuation Model",
        "asset_class": "Commodities",
        "status": "Live",
        "tagline": (
            "A temperature gauge that scores eight crude-oil drivers, estimates fair value and maps "
            "the valuation gap from Very Cold to Very Hot."
        ),
        "stats": [("8", "Weighted drivers"), ("5", "Temperature regimes"), ("90D", "Fair-value history")],
        "stack": ["Python", "Plotly", "yfinance", "EIA API"],
        "source": "https://github.com/dozpiskin/Crude_Oil_Fairvalue_Model",
    },
    {
        "page": "views/macro_floor.py",
        "name": "Macro Floor Model",
        "asset_class": "Equities · US & BIST",
        "status": "Live",
        "tagline": (
            "An autonomous fund engine that values stocks against sovereign-yield floors and buys "
            "crisis bottoms only after forced-liquidation exhaustion."
        ),
        "stats": [("20", "Tracked tickers"), ("5Y", "Backtest window"), ("$100K", "Paper capital")],
        "stack": ["Python", "yfinance", "TradingView", "MongoDB"],
        "source": "https://github.com/dozpiskin/Macro-Floor-Forced-Liquidation-Model",
    },
]

# Upcoming work. Move an item into MODELS when it goes live.
PIPELINE = [
    ("Next model", "Placeholder — replace with the title and one-line idea of your next model.", "Research"),
]

st.markdown(
    """
<style>
.hm-hero { padding: 48px 0 28px; }
.hm-eyebrow { font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase; color: #67e8f9; margin-bottom: 16px; }
.hm-title { font-size: clamp(36px, 6vw, 60px); line-height: 1.05; letter-spacing: -0.035em; color: #fff; font-weight: 800; margin: 0 0 18px; max-width: 16ch; }
.hm-lead { font-size: 18px; color: #94a3b8; max-width: 60ch; margin: 0; line-height: 1.6; }
.hm-h2 { font-size: 24px; letter-spacing: -0.02em; color: #fff; font-weight: 700; margin: 36px 0 4px; }
.hm-sub { color: #94a3b8; font-size: 15px; margin-bottom: 18px; }
.hm-top { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.hm-tag { font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; }
.hm-status { display: inline-flex; align-items: center; gap: 7px; font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 999px; color: #6ee7b7; background: rgba(110, 231, 183, 0.1); }
.hm-status::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.hm-status.dev { color: #a78bfa; background: rgba(167, 139, 250, 0.1); }
.hm-card-title { font-size: 21px; letter-spacing: -0.02em; color: #fff; font-weight: 700; margin: 16px 0 6px; }
.hm-card-text { color: #94a3b8; font-size: 15px; line-height: 1.6; margin: 0 0 16px; }
.hm-stats { display: grid; grid-template-columns: repeat(3, 1fr); border: 1px solid rgba(148, 163, 184, 0.14); border-radius: 12px; overflow: hidden; margin-bottom: 14px; }
.hm-stats div { padding: 12px 14px; }
.hm-stats div + div { border-left: 1px solid rgba(148, 163, 184, 0.14); }
.hm-stats b { display: block; font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 20px; color: #fff; font-weight: 600; }
.hm-stats span { font-size: 12px; color: #94a3b8; }
.hm-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.hm-chip { font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 12px; color: #94a3b8; padding: 3px 9px; border: 1px solid rgba(148, 163, 184, 0.14); border-radius: 8px; }
.hm-pipe { border: 1px dashed rgba(148, 163, 184, 0.3); border-radius: 16px; padding: 18px 20px; }
.hm-pipe h4 { margin: 10px 0 4px; font-size: 16px; color: #fff; }
.hm-pipe p { margin: 0; font-size: 14px; color: #94a3b8; }
.hm-about { border-top: 1px solid rgba(148, 163, 184, 0.14); margin-top: 40px; padding-top: 32px; color: #94a3b8; line-height: 1.7; }
.hm-about li { margin-bottom: 8px; }
.hm-about b { color: #e2e8f0; }
.hm-foot { color: #64748b; font-size: 13px; border-top: 1px solid rgba(148, 163, 184, 0.14); margin-top: 40px; padding-top: 18px; }
[class*="st-key-hmcard"] { background: rgba(15, 23, 42, 0.72); border: 1px solid rgba(148, 163, 184, 0.14); border-radius: 16px; padding: 24px; transition: border-color 0.2s; }
[class*="st-key-hmcard"]:hover { border-color: rgba(148, 163, 184, 0.32); }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hm-hero">'
    '<div class="hm-eyebrow">Quantitative research · Live models</div>'
    '<h1 class="hm-title">Ozpiskin Financial Models</h1>'
    '<p class="hm-lead">Rule-based valuation models for commodities and equities — each one running live on '
    "market data, with its methodology and source code in the open.</p>"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="hm-h2">Models</div><div class="hm-sub">{len(MODELS)} models in the collection</div>',
    unsafe_allow_html=True,
)

columns = st.columns(len(MODELS), gap="medium")
for index, (column, model) in enumerate(zip(columns, MODELS)):
    with column, st.container(key=f"hmcard{index}"):
        stats = "".join(f"<div><b>{value}</b><span>{label}</span></div>" for value, label in model["stats"])
        chips = "".join(f'<span class="hm-chip">{item}</span>' for item in model["stack"])
        st.markdown(
            f'<div class="hm-top"><span class="hm-tag">{model["asset_class"]}</span>'
            f'<span class="hm-status">{model["status"]}</span></div>'
            f'<div class="hm-card-title">{model["name"]}</div>'
            f'<p class="hm-card-text">{model["tagline"]}</p>'
            f'<div class="hm-stats">{stats}</div>'
            f'<div class="hm-chips">{chips}</div>',
            unsafe_allow_html=True,
        )
        link_col, source_col = st.columns(2)
        with link_col:
            st.page_link(model["page"], label="Open model", icon=":material/arrow_forward:")
        with source_col:
            st.link_button("Source code", model["source"], icon=":material/code:", type="tertiary")

if PIPELINE:
    st.markdown(
        '<div class="hm-h2">Research pipeline</div><div class="hm-sub">What is being built next</div>',
        unsafe_allow_html=True,
    )
    pipe_columns = st.columns(3, gap="medium")
    for column, (name, note, stage) in zip(pipe_columns, PIPELINE):
        column.markdown(
            f'<div class="hm-pipe"><span class="hm-status dev">{stage}</span><h4>{name}</h4><p>{note}</p></div>',
            unsafe_allow_html=True,
        )

st.markdown(
    '<div class="hm-about">'
    '<div class="hm-h2" style="margin-top:0">About</div>'
    "<p>Ozpiskin Financial Models is the home of the quantitative models built by Derin Özpişkin. "
    "Each model is a self-contained research project with its own live dashboard and open-source code.</p>"
    "<ul>"
    "<li><b>Macro first.</b> Prices are measured against opportunity cost — rates, inflation, FX and credit.</li>"
    "<li><b>Transparent rules.</b> Every signal comes from explicit, documented formulas and weights.</li>"
    "<li><b>Tested on history.</b> Signals are backtested before they are trusted.</li>"
    f'<li><b>Open source.</b> All code is public on <a href="{GITHUB_URL}" target="_blank">GitHub</a>.</li>'
    "</ul></div>"
    '<div class="hm-foot">For research and educational purposes only. Nothing on this site is investment advice.</div>',
    unsafe_allow_html=True,
)
