"""
Shared design system for every page of the site.

Pages build their UI only from these helpers so both models look like one
product: navigation, page header, metric strip, panels, section tabs, tables,
badges and one Plotly style. Fonts are system fonts (no web-font downloads) and
the only motion is a short hover/focus transition, so the site stays light on
older hardware.
"""

from __future__ import annotations

from html import escape
from typing import Iterable, Optional, Sequence

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

HOME_PAGE = "views/home.py"
GITHUB_URL = "https://github.com/dozpiskin"

# Palette
BG = "#0B0F14"
SURFACE = "#111821"
SURFACE_2 = "#161F2A"
SURFACE_3 = "#1B2633"
BORDER = "#283442"
DIVIDER = "#202B37"
TEXT = "#F1F5F9"
TEXT_2 = "#A0AEC0"
MUTED = "#718096"
MINT = "#34D399"
BLUE = "#60A5FA"
GOLD = "#D6B36A"
UP = "#34D399"
DOWN = "#F87171"
WARN = "#FBBF24"

FONT_SANS = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

GLOBAL_CSS = """
<style>
:root {
  --bg: #0B0F14; --surface: #111821; --surface-2: #161F2A; --surface-3: #1B2633;
  --border: #283442; --divider: #202B37;
  --text: #F1F5F9; --text-2: #A0AEC0; --muted: #718096;
  --mint: #34D399; --blue: #60A5FA; --gold: #D6B36A; --up: #34D399; --down: #F87171; --warn: #FBBF24;
  --sans: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  --serif: 'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, serif;
  --mono: ui-monospace, 'SF Mono', 'Cascadia Mono', Consolas, monospace;
  --radius: 10px;
}
.stApp { background: var(--bg); color: var(--text); }
.stApp, .stApp p, .stApp li, .stApp label, .stApp button, .stApp input, .stApp textarea, .stApp td, .stApp th,
.stApp [data-testid="stMarkdownContainer"] { font-family: var(--sans); }
.stApp p { color: var(--text-2); }
.stApp a:focus-visible, .stApp button:focus-visible, .stApp [role="radio"]:focus-visible { outline: 2px solid var(--mint); outline-offset: 2px; }
::selection { background: rgba(52, 211, 153, 0.25); }
header[data-testid="stHeader"], #MainMenu, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stMainBlockContainer"], .block-container { max-width: 1200px; padding: 0 32px 48px; }
.kt-num { font-variant-numeric: tabular-nums; font-feature-settings: "tnum"; }
.kt-up { color: var(--up) !important; } .kt-down { color: var(--down) !important; } .kt-warn { color: var(--warn) !important; }
.kt-mint { color: var(--mint) !important; } .kt-blue { color: var(--blue) !important; } .kt-gold { color: var(--gold) !important; }
.kt-muted { color: var(--muted) !important; }

/* navigation */
.st-key-topnav { position: sticky; top: 0; z-index: 50; background: rgba(11, 15, 20, 0.94); border-bottom: 1px solid var(--divider);
  padding: 16px 0; margin-bottom: 8px; }
.st-key-topnav [data-testid="stPageLink"] a { padding: 4px 0; background: transparent !important; border-radius: 0; }
.st-key-topnav [data-testid="stPageLink"] a p { font-size: 14px; color: var(--text-2); transition: color 120ms; }
.st-key-topnav [data-testid="stPageLink"] a:hover p { color: var(--text); }
.st-key-navbrand [data-testid="stPageLink"] a p { font-size: 13px; font-weight: 700; letter-spacing: 0.22em; color: var(--text) !important; }
.st-key-navbrand [data-testid="stPageLink"] a p::before { content: ""; display: inline-block; width: 8px; height: 8px; background: var(--mint);
  border-radius: 2px; margin-right: 12px; vertical-align: 1px; }
.st-key-navbrand [data-testid="stPageLink"] a p::after { content: "Financial Models"; font-weight: 400; letter-spacing: 0.02em; color: var(--muted);
  margin-left: 12px; padding-left: 12px; border-left: 1px solid var(--border); }
[class*="st-key-navon"] [data-testid="stPageLink"] a p { color: var(--text) !important; box-shadow: inset 0 -2px 0 var(--mint); padding-bottom: 6px; }

/* breadcrumb */
.st-key-crumb { margin-top: 16px; }
.st-key-crumb [data-testid="stPageLink"] a { padding: 0; background: transparent !important; }
.st-key-crumb [data-testid="stPageLink"] a p { font-size: 13px; color: var(--muted); transition: color 120ms; }
.st-key-crumb [data-testid="stPageLink"] a:hover p { color: var(--mint); }
.st-key-crumb .kt-crumb-sep, .st-key-crumb .kt-crumb-here { font-size: 13px; color: var(--muted); }
.st-key-crumb .kt-crumb-here { color: var(--text-2); }

/* page header */
.kt-cat { font-size: 11px; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; color: var(--mint); }
.kt-title { font-size: 34px; font-weight: 650; line-height: 1.15; letter-spacing: -0.02em; color: var(--text); margin: 8px 0 0; }
.stApp [data-testid="stMarkdownContainer"] p.kt-lead { font-size: 15px; line-height: 1.6; color: var(--text-2); max-width: 70ch; margin: 8px 0 0; }
.stApp [data-testid="stMarkdownContainer"] p.kt-meta { font-size: 12px; line-height: 1.6; color: var(--muted); margin: 0; }
.kt-status { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text-2); margin-top: 16px; }
.kt-status i { width: 6px; height: 6px; border-radius: 50%; background: var(--mint); display: inline-block; }

/* metric strip: one surface, divided cells */
.kt-metrics { display: grid; background: var(--surface); border: 1px solid var(--divider); border-radius: var(--radius); margin: 24px 0 16px; overflow: hidden; }
.kt-metric { padding: 16px 24px; border-left: 1px solid var(--divider); min-width: 0; }
.kt-metric:first-child { border-left: 0; }
.kt-metric-l { font-size: 11px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kt-metric-v { font-size: 24px; font-weight: 600; color: var(--text); margin-top: 8px; white-space: nowrap; font-variant-numeric: tabular-nums; letter-spacing: -0.01em; }
.kt-metric-d { font-size: 12px; color: var(--muted); margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-variant-numeric: tabular-nums; }
.kt-metrics.compact .kt-metric { padding: 16px; } .kt-metrics.compact .kt-metric-v { font-size: 18px; }

/* panels (surface cards around charts / tables) */
[class*="st-key-ktpanel"] { background: var(--surface); border: 1px solid var(--divider); border-radius: var(--radius); padding: 24px; }
.kt-panel-h { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; flex-wrap: wrap; }
.kt-panel-t { font-size: 15px; font-weight: 600; color: var(--text); }
.kt-panel-n { font-size: 12px; color: var(--muted); }

/* section label */
.kt-sec { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; margin: 32px 0 8px; }
.kt-sec-t { font-size: 11px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-2); }
.kt-sec-n { font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; }

/* section tabs */
.st-key-subnav { margin: 40px 0 16px; }
.st-key-subnav [data-baseweb="button-group"] { gap: 12px; flex-wrap: wrap; }
.st-key-subnav button { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 8px !important;
  box-shadow: none !important; padding: 10px 20px !important; min-height: 0 !important; transition: border-color 120ms, background 120ms; }
.st-key-subnav button p { font-size: 14px; font-weight: 500; color: var(--text-2); }
.st-key-subnav button:hover { border-color: var(--mint) !important; } .st-key-subnav button:hover p { color: var(--text); }
.st-key-subnav button[kind="segmented_controlActive"] { background: rgba(52, 211, 153, 0.12) !important; border-color: var(--mint) !important; }
.st-key-subnav button[kind="segmented_controlActive"] p { color: var(--mint); font-weight: 600; }

/* range selector */
[class*="st-key-range"] [data-baseweb="button-group"] { gap: 4px; }
[class*="st-key-range"] button { min-height: 0 !important; padding: 4px 12px !important; border-radius: 6px !important; border: 1px solid var(--border) !important;
  background: transparent !important; }
[class*="st-key-range"] button p { font-size: 12px; color: var(--text-2); font-variant-numeric: tabular-nums; }
[class*="st-key-range"] button[kind="segmented_controlActive"] { background: rgba(52, 211, 153, 0.12) !important; border-color: rgba(52, 211, 153, 0.5) !important; }
[class*="st-key-range"] button[kind="segmented_controlActive"] p { color: var(--mint); }

/* tables */
.kt-tbl-wrap { overflow-x: auto; }
.kt-tbl { width: 100%; border-collapse: collapse; font-size: 13px; border: 0 !important; margin: 0 !important; }
.kt-tbl th, .kt-tbl td { border-left: 0 !important; border-right: 0 !important; border-top: 0 !important; background: transparent; }
.kt-tbl th { font-size: 11px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); text-align: left;
  padding: 8px 16px 8px 0; border-bottom: 1px solid var(--border) !important; white-space: nowrap; }
.kt-tbl td { padding: 12px 16px 12px 0; border-bottom: 1px solid var(--divider) !important; color: var(--text-2); vertical-align: top; }
.kt-tbl tr:last-child td { border-bottom: 0 !important; }
.kt-tbl tbody tr:hover td { background: rgba(255, 255, 255, 0.02); }
.kt-tbl th:last-child, .kt-tbl td:last-child { padding-right: 0; }
.kt-tbl .num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
.kt-tbl .strong { color: var(--text); font-weight: 500; }
.kt-tbl .sub { display: block; font-size: 12px; color: var(--muted); margin-top: 2px; }
.kt-tbl details { margin-top: 4px; }
.kt-tbl summary { font-size: 12px; color: var(--muted); cursor: pointer; list-style: none; }
.kt-tbl summary::-webkit-details-marker { display: none; }
.kt-tbl summary::before { content: "+ "; color: var(--mint); }
.kt-tbl details[open] summary::before { content: "− "; }
.kt-tbl details p, .kt-tbl details div { font-size: 12px; line-height: 1.6; color: var(--text-2); margin: 4px 0 0; max-width: 60ch; white-space: normal; }

/* badges: always text + colour, never colour alone */
.kt-badge { display: inline-block; font-size: 11px; font-weight: 600; letter-spacing: 0.04em; padding: 2px 8px; border-radius: 6px;
  border: 1px solid var(--border); color: var(--text-2); background: var(--surface-2); white-space: nowrap; }
.kt-badge.up, .kt-badge.mint { color: var(--up); border-color: rgba(52, 211, 153, 0.35); background: rgba(52, 211, 153, 0.08); }
.kt-badge.down { color: var(--down); border-color: rgba(248, 113, 113, 0.35); background: rgba(248, 113, 113, 0.08); }
.kt-badge.warn { color: var(--warn); border-color: rgba(251, 191, 36, 0.35); background: rgba(251, 191, 36, 0.08); }
.kt-badge.blue { color: var(--blue); border-color: rgba(96, 165, 250, 0.35); background: rgba(96, 165, 250, 0.08); }

/* numbered methodology */
.kt-steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 8px; }
.kt-step { background: var(--surface); border: 1px solid var(--divider); border-radius: var(--radius); padding: 24px; }
.kt-step-n { font-size: 12px; font-weight: 600; color: var(--mint); font-variant-numeric: tabular-nums; }
.kt-step-t { font-size: 16px; font-weight: 600; color: var(--text); margin: 8px 0; }
.kt-step-b { font-size: 13px; line-height: 1.65; color: var(--text-2); }
.kt-step-b code { font-family: var(--mono); font-size: 12px; color: var(--text); background: var(--surface-3); padding: 1px 6px; border-radius: 4px; }

/* notes */
.kt-notes { margin: 16px 0 0; padding: 0; list-style: none; }
.kt-notes li { font-size: 12px; color: var(--muted); line-height: 1.6; padding-left: 16px; position: relative; margin-bottom: 4px; }
.kt-notes li::before { content: ""; position: absolute; left: 0; top: 9px; width: 6px; height: 1px; background: var(--muted); }

/* buttons */
.stApp button[kind="primary"] { background: var(--mint) !important; border-color: var(--mint) !important; border-radius: 8px !important; }
.stApp button[kind="primary"] p { color: #06281c !important; font-weight: 600; }
.stApp button[kind="secondary"] { background: transparent !important; border: 1px solid var(--border) !important; border-radius: 8px !important; }
.stApp button[kind="secondary"]:hover { border-color: var(--mint) !important; }
.stApp button[kind="tertiary"] p { color: var(--text-2); font-size: 13px; } .stApp button[kind="tertiary"]:hover p { color: var(--mint); }
[data-testid="stPopoverBody"] { background: var(--surface-2) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }

/* footer */
.kt-foot { display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; border-top: 1px solid var(--divider); margin-top: 64px; padding-top: 24px;
  font-size: 12px; color: var(--muted); }
.kt-foot a { color: var(--text-2); text-decoration: none; } .kt-foot a:hover { color: var(--mint); }

@media (prefers-reduced-motion: reduce) { .stApp * { transition: none !important; } }
@media (max-width: 760px) {
  [data-testid="stMainBlockContainer"], .block-container { padding: 0 16px 32px; }
  .st-key-navbrand [data-testid="stPageLink"] a p::after { display: none; }
  .kt-title { font-size: 28px; }
  .kt-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; }
  .kt-metric { border-left: 0; border-top: 1px solid var(--divider); padding: 16px; }
  .kt-metric:nth-child(-n+2) { border-top: 0; } .kt-metric:nth-child(even) { border-left: 1px solid var(--divider); }
  [class*="st-key-ktpanel"] { padding: 16px; }
  .st-key-subnav [data-baseweb="button-group"] { gap: 8px; } .st-key-subnav button { padding: 8px 14px !important; }
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


def signed_money(value: Optional[float], digits: int = 0, currency: str = "$") -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else "−" if value < 0 else ""
    return f"{sign}{currency}{abs(value):,.{digits}f}"


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
        return date(value)


def date(value: Optional[str]) -> str:
    if not value:
        return "—"
    try:
        return pd.Timestamp(value).strftime("%d %b %Y")
    except Exception:
        return str(value)


# ── Navigation ──────────────────────────────────────────────────────────────
def top_nav(pages: Sequence[tuple[str, "st.Page"]], home_page: "st.Page", current: "st.Page") -> None:
    with st.container(key="topnav", horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
        with st.container(key="navbrand", width="content"):
            st.page_link(home_page, label="OZPISKIN")
        with st.container(key="navlinks", horizontal=True, width="content", gap="large", vertical_alignment="center"):
            for slug, page in pages:
                state = "on" if page.url_path == current.url_path else "off"
                with st.container(key=f"nav{state}_{slug}", width="content"):
                    st.page_link(page)


# ── Building blocks ─────────────────────────────────────────────────────────
def page_header(category: str, title: str, lead: Optional[str] = None, status: Optional[str] = None) -> None:
    with st.container(key="crumb", horizontal=True, gap="small", vertical_alignment="center"):
        st.page_link(HOME_PAGE, label="Models")
        html(f'<span class="kt-crumb-sep">/</span>&nbsp;&nbsp;<span class="kt-crumb-here">{title}</span>')
    lead_html = f'<p class="kt-lead">{lead}</p>' if lead else ""
    status_html = f'<div class="kt-status"><i></i>{status}</div>' if status else ""
    html(f'<div class="kt-cat">{category}</div><div class="kt-title">{title}</div>{lead_html}{status_html}')


def metrics(items: Sequence[tuple], compact: bool = False) -> None:
    """items: (label, value, detail=None, tone='') — tone is up/down/warn/mint/blue/gold."""
    cells = []
    for item in items:
        label, value = item[0], item[1]
        detail = item[2] if len(item) > 2 else None
        item_tone = item[3] if len(item) > 3 else ""
        value_cls = f" kt-{item_tone}" if item_tone else ""
        detail_html = f'<div class="kt-metric-d">{detail}</div>' if detail else ""
        cells.append(
            f'<div class="kt-metric"><div class="kt-metric-l">{label}</div>'
            f'<div class="kt-metric-v{value_cls}">{value}</div>{detail_html}</div>'
        )
    size = " compact" if compact else ""
    html(f'<div class="kt-metrics{size}" style="grid-template-columns:repeat({len(cells)}, minmax(0, 1fr))">{"".join(cells)}</div>')


def panel(key: str):
    """A surface card. Use as a context manager: `with kit.panel("price"): ...`."""
    return st.container(key=f"ktpanel_{key}")


def panel_header(title: str, note: Optional[str] = None) -> None:
    note_html = f'<span class="kt-panel-n">{note}</span>' if note else ""
    html(f'<div class="kt-panel-h"><span class="kt-panel-t">{title}</span>{note_html}</div>')


def section(title: str, note: Optional[str] = None) -> None:
    note_html = f'<span class="kt-sec-n">{note}</span>' if note else ""
    html(f'<div class="kt-sec"><span class="kt-sec-t">{title}</span>{note_html}</div>')


def badge(text: str, badge_tone: str = "") -> str:
    return f'<span class="kt-badge {badge_tone}">{escape(str(text))}</span>'


def table(headers: Optional[Sequence[str]], rows: Iterable[Sequence[str]], numeric: Sequence[int] = (), max_height: Optional[int] = None) -> None:
    """Render an HTML table. Cells are trusted HTML; `numeric` lists right-aligned tabular columns."""
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


def _sticky_choice(options: Sequence[str], key: str, container_key: str, default: str) -> str:
    """Single-select segmented control that never ends up empty (clicking the active option keeps it)."""
    last_key = f"{key}__last"

    def keep_selection() -> None:
        if st.session_state.get(key) is None:
            st.session_state[key] = st.session_state.get(last_key, default)
        st.session_state[last_key] = st.session_state[key]

    if st.session_state.get(key) not in options:
        st.session_state[key] = st.session_state.get(last_key, default)
    with st.container(key=container_key, width="content"):
        st.segmented_control("Select", options, key=key, on_change=keep_selection, label_visibility="collapsed")
    return st.session_state.get(key) or default


def subnav(options: Sequence[str], key: str) -> str:
    """Underlined section tabs; only the selected section is rendered."""
    with st.container(key="subnav"):
        return _sticky_choice(options, key, f"{key}_tabs", options[0])


def range_selector(options: Sequence[str], key: str, default: Optional[str] = None) -> str:
    """Small pill buttons for a chart's visible range (display only — never refetches data)."""
    return _sticky_choice(options, key, f"range_{key}", default or options[-1])


def style_figure(figure: go.Figure, height: int = 360) -> go.Figure:
    figure.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT_SANS, "color": TEXT_2, "size": 12},
        margin={"l": 8, "r": 64, "t": 32, "b": 32},
        hovermode="x unified",
        hoverlabel={"bgcolor": SURFACE_3, "bordercolor": BORDER, "font": {"family": FONT_SANS, "color": TEXT, "size": 12}},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0, "font": {"size": 12, "color": TEXT_2}, "bgcolor": "rgba(0,0,0,0)"},
        transition={"duration": 0},
    )
    figure.update_xaxes(showgrid=False, zeroline=False, linecolor=BORDER, tickcolor=BORDER, tickfont={"color": MUTED},
                        automargin=True, showticklabels=True, showspikes=True, spikecolor=BORDER, spikethickness=1, spikedash="solid")
    figure.update_yaxes(gridcolor=DIVIDER, zeroline=False, showline=False, tickfont={"color": MUTED}, side="right",
                        automargin=True, showticklabels=True)
    return figure


CHART_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "displayModeBar": "hover",
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d", "toImage", "pan2d", "zoomIn2d", "zoomOut2d"],
}


def chart(figure: go.Figure) -> None:
    """Plotly chart: hover values, legend click toggles series, drag to zoom, double-click to reset."""
    st.plotly_chart(figure, theme=None, config=CHART_CONFIG, width="stretch")


def footer() -> None:
    html(
        '<div class="kt-foot"><span>© Ozpiskin Financial Models · '
        f'<a href="{GITHUB_URL}" target="_blank" rel="noopener">GitHub</a></span>'
        "<span>Research and educational use only. Simulated results are not investment advice.</span></div>"
    )
