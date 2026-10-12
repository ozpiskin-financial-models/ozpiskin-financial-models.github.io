"""
Shared design system for every page of the site.

All pages build their UI from these helpers so the models look like one site:
page header, KPI strip, section labels, sub-navigation, tables, badges and a
common Plotly style.
"""

from __future__ import annotations

from html import escape
from typing import Iterable, Optional, Sequence

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

HOME_PAGE = "views/home.py"

GOLD = "#c9a96e"
TEXT = "#ededec"
TEXT_2 = "#a1a1a0"
MUTED = "#6b6b6a"
LINE = "#1d1d1d"
GRID = "#151515"
UP = "#5fbf8f"
DOWN = "#e26d5a"
COLD = "#8fb4d8"
HOT = "#e08a5f"

FONT_SANS = "Geist, 'Helvetica Neue', Arial, sans-serif"
FONT_MONO = "'Geist Mono', ui-monospace, monospace"

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600&family=Geist+Mono:wght@400;500&family=Instrument+Serif:ital@0;1&display=swap');
:root {
  --bg: #050505; --surface: #0b0b0b; --surface-2: #111111;
  --line: #1d1d1d; --line-strong: #2b2b2b;
  --text: #ededec; --text-2: #a1a1a0; --muted: #6b6b6a;
  --gold: #c9a96e; --gold-soft: rgba(201, 169, 110, 0.10);
  --up: #5fbf8f; --down: #e26d5a; --cold: #8fb4d8; --hot: #e08a5f;
  --serif: 'Instrument Serif', 'Times New Roman', serif;
  --sans: Geist, 'Helvetica Neue', Arial, sans-serif;
  --mono: 'Geist Mono', ui-monospace, monospace;
}
.stApp { background: var(--bg); color: var(--text); }
.stApp, .stApp p, .stApp li, .stApp label, .stApp button, .stApp input, .stApp textarea,
.stApp [data-testid="stMarkdownContainer"] { font-family: var(--sans); }
.stApp p { color: var(--text-2); }
::selection { background: rgba(201, 169, 110, 0.25); }
header[data-testid="stHeader"], #MainMenu, footer, .stDeployButton, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stMainBlockContainer"], .block-container { max-width: 1240px; padding: 0 2rem 3rem; }
/* top navigation */
.st-key-topnav { position: sticky; top: 0; z-index: 50; background: rgba(5, 5, 5, 0.86); backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--line); padding: 14px 0; margin-bottom: 8px; }
.st-key-topnav [data-testid="stPageLink"] a { padding: 0; background: transparent !important; border-radius: 0; }
.st-key-topnav [data-testid="stPageLink"] a p { font-size: 13px; letter-spacing: 0.02em; color: var(--text-2); transition: color .2s; }
.st-key-topnav [data-testid="stPageLink"] a:hover p { color: var(--text); }
.st-key-navbrand [data-testid="stPageLink"] a p { font-family: var(--serif) !important; font-size: 24px; letter-spacing: 0; color: var(--text) !important; }
.st-key-navbrand [data-testid="stPageLink"] a p::after { content: "Financial Models"; font-family: var(--sans); font-size: 10px; letter-spacing: 0.24em;
  text-transform: uppercase; color: var(--muted); margin-left: 12px; vertical-align: 4px; }
[class*="st-key-navon"] [data-testid="stPageLink"] a p { color: var(--text) !important; border-bottom: 1px solid var(--gold); padding-bottom: 3px; }
/* back link */
.st-key-backlink [data-testid="stPageLink"] a { padding: 0; background: transparent !important; }
.st-key-backlink [data-testid="stPageLink"] a p, .st-key-backlink [data-testid="stIconMaterial"] { font-size: 13px; color: var(--muted); transition: color .2s; }
.st-key-backlink [data-testid="stPageLink"] a:hover p, .st-key-backlink [data-testid="stPageLink"] a:hover [data-testid="stIconMaterial"] { color: var(--gold); }
/* typography */
.kt-eyebrow { font-size: 11px; letter-spacing: 0.24em; text-transform: uppercase; color: var(--gold); }
.kt-title { font-family: var(--serif); font-weight: 400; font-size: clamp(40px, 5.5vw, 64px); line-height: 1.02; color: var(--text); margin: 14px 0 0; letter-spacing: -0.01em; }
.kt-lead { font-size: 16px; line-height: 1.6; color: var(--text-2); max-width: 62ch; margin: 14px 0 0; }
.kt-meta { font-size: 12px; color: var(--muted); letter-spacing: 0.02em; }
.kt-mono { font-family: var(--mono) !important; font-variant-numeric: tabular-nums; }
.kt-up { color: var(--up) !important; } .kt-down { color: var(--down) !important; } .kt-gold { color: var(--gold) !important; }
.kt-cold { color: var(--cold) !important; } .kt-hot { color: var(--hot) !important; } .kt-muted { color: var(--muted) !important; }
.stApp [data-testid="stMarkdownContainer"] p.kt-meta { font-size: 12px; line-height: 1.6; color: var(--muted); }
.stApp [data-testid="stMarkdownContainer"] p.kt-lead { font-size: 16px; line-height: 1.6; }
/* KPI strip */
.kt-kpis { display: grid; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); margin: 28px 0 8px; }
.kt-kpi { padding: 20px 20px 18px; border-left: 1px solid var(--line); min-width: 0; }
.kt-kpi:first-child { border-left: 0; padding-left: 0; }
.kt-kpi-l { font-size: 10.5px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kt-kpi-v { font-family: var(--mono); font-variant-numeric: tabular-nums; font-size: 24px; font-weight: 400; color: var(--text); margin-top: 10px; white-space: nowrap; }
.kt-kpi-d { font-family: var(--mono); font-size: 12px; color: var(--muted); margin-top: 6px; white-space: nowrap; }
.kt-kpis.small { margin-top: 0; border-top: 0; } .kt-kpis.small .kt-kpi { padding-top: 16px; padding-bottom: 16px; } .kt-kpis.small .kt-kpi-v { font-size: 18px; margin-top: 8px; }
/* sections */
.kt-sec { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; border-bottom: 1px solid var(--line); padding-bottom: 10px; margin: 30px 0 6px; }
.kt-sec-t { font-size: 11px; letter-spacing: 0.2em; text-transform: uppercase; color: var(--text-2); }
.kt-sec-n { font-family: var(--mono); font-size: 12px; color: var(--muted); }
/* sub navigation */
.st-key-subnav { border-bottom: 1px solid var(--line); margin-top: 18px; }
.st-key-subnav [data-baseweb="button-group"] { gap: 28px; }
.st-key-subnav button { background: transparent !important; border: 0 !important; border-radius: 0 !important; box-shadow: none !important;
  padding: 10px 0 12px !important; min-height: 0 !important; margin-bottom: -1px; border-bottom: 1px solid transparent !important; }
.st-key-subnav button p { font-size: 13px; color: var(--muted); letter-spacing: 0.02em; }
.st-key-subnav button:hover p { color: var(--text); }
.st-key-subnav button[kind="segmented_controlActive"], .st-key-subnav button[aria-checked="true"] { border-bottom: 1px solid var(--gold) !important; }
.st-key-subnav button[kind="segmented_controlActive"] p, .st-key-subnav button[aria-checked="true"] p { color: var(--text); }
/* tables */
.kt-tbl-wrap { overflow-x: auto; }
.kt-tbl { width: 100%; border-collapse: collapse; font-size: 13px; border: 0 !important; margin: 0 !important; }
.kt-tbl th, .kt-tbl td { border-left: 0 !important; border-right: 0 !important; border-top: 0 !important; background: transparent; }
.kt-tbl th { font-size: 10.5px; font-weight: 400; letter-spacing: 0.16em; text-transform: uppercase; color: var(--muted); text-align: left;
  padding: 12px 14px 10px 0; border-bottom: 1px solid var(--line) !important; white-space: nowrap; }
.kt-tbl td { padding: 13px 14px 13px 0; border-bottom: 1px solid #161616 !important; color: var(--text-2); vertical-align: middle; }
.kt-tbl tr:hover td { background: rgba(255, 255, 255, 0.015); }
.kt-tbl th:last-child, .kt-tbl td:last-child { padding-right: 0; }
.kt-tbl .num { font-family: var(--mono); font-variant-numeric: tabular-nums; text-align: right; white-space: nowrap; }
.kt-tbl th.num { text-align: right; }
.kt-tbl .strong { color: var(--text); }
.kt-tbl .sub { display: block; font-size: 11.5px; color: var(--muted); margin-top: 2px; }
/* badges */
.kt-badge { display: inline-block; font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; padding: 4px 9px; border: 1px solid var(--line-strong);
  color: var(--text-2); white-space: nowrap; }
.kt-badge.up { color: var(--up); border-color: rgba(95, 191, 143, 0.35); } .kt-badge.down { color: var(--down); border-color: rgba(226, 109, 90, 0.35); }
.kt-badge.gold { color: var(--gold); border-color: rgba(201, 169, 110, 0.4); } .kt-badge.cold { color: var(--cold); border-color: rgba(143, 180, 216, 0.35); }
.kt-badge.hot { color: var(--hot); border-color: rgba(224, 138, 95, 0.4); }
/* numbered list (methodology) */
.kt-steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); border-top: 1px solid var(--line); margin-top: 18px; }
.kt-step { padding: 22px 22px 22px 0; border-bottom: 1px solid var(--line); }
.kt-step-n { font-family: var(--mono); font-size: 11px; color: var(--gold); }
.kt-step-t { font-family: var(--serif); font-size: 24px; color: var(--text); margin: 10px 0 8px; }
.kt-step-b { font-size: 13.5px; line-height: 1.65; color: var(--text-2); }
.kt-step-b code { font-family: var(--mono); font-size: 12px; color: var(--text); background: var(--surface-2); padding: 1px 6px; }
/* notes */
.kt-notes { margin: 12px 0 0; padding: 0; list-style: none; }
.kt-notes li { font-size: 12.5px; color: var(--muted); line-height: 1.6; padding-left: 14px; position: relative; margin-bottom: 4px; }
.kt-notes li::before { content: ""; position: absolute; left: 0; top: 9px; width: 6px; height: 1px; background: var(--gold); }
/* buttons & inputs */
.stApp button[kind="primary"] { background: var(--gold) !important; border-color: var(--gold) !important; color: #0a0a0a !important; border-radius: 0 !important; }
.stApp button[kind="primary"] p { color: #0a0a0a !important; font-weight: 500; }
.stApp button[kind="secondary"] { background: transparent !important; border: 1px solid var(--line-strong) !important; border-radius: 0 !important; }
.stApp button[kind="secondary"]:hover { border-color: var(--gold) !important; }
.stApp button[kind="tertiary"] p { color: var(--muted); font-size: 13px; } .stApp button[kind="tertiary"]:hover p { color: var(--gold); }
[data-testid="stPopoverBody"] { background: var(--surface) !important; border: 1px solid var(--line-strong) !important; border-radius: 0 !important; }
/* site footer */
.kt-foot { display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; border-top: 1px solid var(--line); margin-top: 64px; padding-top: 20px;
  font-size: 12px; color: var(--muted); }
@media (max-width: 760px) {
  [data-testid="stMainBlockContainer"], .block-container { padding: 0 1rem 2rem; }
  .st-key-navbrand [data-testid="stPageLink"] a p::after { display: none; }
  .kt-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; }
  .kt-kpi, .kt-kpi:first-child { border-left: 0; padding-left: 0; border-top: 1px solid var(--line); }
  .st-key-subnav [data-baseweb="button-group"] { gap: 18px; flex-wrap: wrap; }
}
</style>
"""


def inject_global_css() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def html(content: str) -> None:
    st.markdown(content, unsafe_allow_html=True)


# ── Formatting ──────────────────────────────────────────────────────────────
def money(value: Optional[float], digits: int = 2) -> str:
    return "—" if value is None else f"${value:,.{digits}f}"


def pct(value: Optional[float], digits: int = 2, signed: bool = True) -> str:
    if value is None:
        return "—"
    if round(value, digits) == 0:
        value = 0.0
    sign = "+" if signed and value > 0 else ""
    return f"{sign}{value:.{digits}f}%"


def signed_money(value: Optional[float], digits: int = 0) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else "−" if value < 0 else ""
    return f"{sign}${abs(value):,.{digits}f}"


def num(value: Optional[float], digits: int = 2) -> str:
    return "—" if value is None else f"{value:,.{digits}f}"


def score(value: Optional[float]) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{int(value)}" if float(value).is_integer() else f"{sign}{value:.1f}"


def tone(value: Optional[float]) -> str:
    if value is None or value == 0:
        return ""
    return "up" if value > 0 else "down"


def timestamp(value: Optional[str]) -> str:
    if not value:
        return "—"
    try:
        return pd.Timestamp(value).tz_convert("UTC").strftime("%d %b %Y, %H:%M UTC")
    except Exception:
        try:
            return pd.Timestamp(value).strftime("%d %b %Y")
        except Exception:
            return str(value)


# ── Building blocks ─────────────────────────────────────────────────────────
def page_header(eyebrow: str, title: str, lead: Optional[str] = None, back: bool = True) -> None:
    if back:
        with st.container(key="backlink"):
            st.page_link(HOME_PAGE, label="All models", icon=":material/arrow_back:")
    lead_html = f'<p class="kt-lead">{lead}</p>' if lead else ""
    html(f'<div class="kt-eyebrow">{eyebrow}</div><div class="kt-title">{title}</div>{lead_html}')


def kpi_strip(items: Sequence[tuple], small: bool = False) -> None:
    """items: (label, value, detail=None, tone='') — tone is up/down/gold/cold/hot."""
    cells = []
    for item in items:
        label, value = item[0], item[1]
        detail = item[2] if len(item) > 2 else None
        item_tone = item[3] if len(item) > 3 else ""
        value_cls = f" kt-{item_tone}" if item_tone else ""
        detail_html = f'<div class="kt-kpi-d">{detail}</div>' if detail else ""
        cells.append(
            f'<div class="kt-kpi"><div class="kt-kpi-l">{label}</div>'
            f'<div class="kt-kpi-v{value_cls}">{value}</div>{detail_html}</div>'
        )
    size = " small" if small else ""
    html(f'<div class="kt-kpis{size}" style="grid-template-columns:repeat({len(cells)}, minmax(0, 1fr))">{"".join(cells)}</div>')


def section(title: str, note: Optional[str] = None) -> None:
    note_html = f'<span class="kt-sec-n">{note}</span>' if note else ""
    html(f'<div class="kt-sec"><span class="kt-sec-t">{title}</span>{note_html}</div>')


def badge(text: str, badge_tone: str = "") -> str:
    return f'<span class="kt-badge {badge_tone}">{escape(str(text))}</span>'


def table(headers: Optional[Sequence[str]], rows: Iterable[Sequence[str]], numeric: Sequence[int] = (), max_height: Optional[int] = None) -> None:
    """Render an HTML table. Cells are trusted HTML; `numeric` lists right-aligned mono columns."""
    numeric = set(numeric)
    head = "".join(f'<th class="{"num" if i in numeric else ""}">{h}</th>' for i, h in enumerate(headers or []))
    thead = f"<thead><tr>{head}</tr></thead>" if headers else ""
    body = "".join(
        "<tr>" + "".join(f'<td class="{"num" if i in numeric else ""}">{cell}</td>' for i, cell in enumerate(row)) + "</tr>"
        for row in rows
    )
    style = f' style="max-height:{max_height}px;overflow-y:auto"' if max_height else ""
    html(f'<div class="kt-tbl-wrap"{style}><table class="kt-tbl">{thead}<tbody>{body}</tbody></table></div>')


def steps(items: Sequence[tuple[str, str]]) -> None:
    cells = "".join(
        f'<div class="kt-step"><div class="kt-step-n">{i:02d}</div><div class="kt-step-t">{title}</div><div class="kt-step-b">{body}</div></div>'
        for i, (title, body) in enumerate(items, start=1)
    )
    html(f'<div class="kt-steps">{cells}</div>')


def notes(lines: Iterable[str]) -> None:
    items = "".join(f"<li>{escape(line)}</li>" for line in lines)
    if items:
        html(f'<ul class="kt-notes">{items}</ul>')


def subnav(options: Sequence[str], key: str) -> str:
    """Underlined section tabs. Always returns a selection (clicking the active tab keeps it)."""
    last_key = f"{key}__last"

    def keep_selection() -> None:
        if st.session_state.get(key) is None:
            st.session_state[key] = st.session_state.get(last_key, options[0])
        st.session_state[last_key] = st.session_state[key]

    if st.session_state.get(key) not in options:
        st.session_state[key] = st.session_state.get(last_key, options[0])
    with st.container(key="subnav"):
        st.segmented_control("Section", options, key=key, on_change=keep_selection, label_visibility="collapsed")
    return st.session_state.get(key) or options[0]


def style_figure(figure: go.Figure, height: int = 360) -> go.Figure:
    figure.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT_SANS, "color": TEXT_2, "size": 11},
        margin={"l": 4, "r": 64, "t": 28, "b": 32},
        hovermode="x unified",
        hoverlabel={"bgcolor": "#111111", "bordercolor": "#2b2b2b", "font": {"family": FONT_MONO, "color": TEXT, "size": 12}},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.0, "x": 0, "font": {"size": 11, "color": TEXT_2}, "bgcolor": "rgba(0,0,0,0)"},
    )
    figure.update_xaxes(showgrid=False, zeroline=False, linecolor=LINE, tickcolor=LINE, tickfont={"color": MUTED}, automargin=True, showticklabels=True)
    figure.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=LINE, tickfont={"family": FONT_MONO, "color": MUTED}, side="right", automargin=True, showticklabels=True)
    return figure


def chart(figure: go.Figure) -> None:
    st.plotly_chart(figure, theme=None, config={"displayModeBar": False, "responsive": True}, width="stretch")


def footer() -> None:
    html(
        '<div class="kt-foot"><span>© Ozpiskin Financial Models</span>'
        "<span>Research and educational use only. Not investment advice.</span></div>"
    )
