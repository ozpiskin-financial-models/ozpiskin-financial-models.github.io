"""
WTI Crude Oil Valuation Model — Streamlit page.

Ported from the Dash dashboard (dashboard.py) in the Crude_Oil_Fairvalue_Model
repository. Colours, formatting helpers and Plotly figures are carried over
unchanged; only the layout layer is rewritten for Streamlit. All numbers come
from models/crude_oil_engine.py.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from models.crude_oil_engine import load_crude_oil_valuation_snapshot


logger = logging.getLogger(__name__)

REFRESH_INTERVAL_SECONDS = 5 * 60

COLOR_BG = "#050816"
COLOR_PANEL = "rgba(8, 15, 31, 0.82)"
COLOR_PANEL_SUBTLE = "rgba(10, 18, 32, 0.62)"
COLOR_BORDER = "rgba(255, 255, 255, 0.10)"
COLOR_TEXT = "#d9e3f0"
COLOR_MUTED = "#94a3b8"
COLOR_WHITE = "#ffffff"
COLOR_CYAN = "#67e8f9"
COLOR_CYAN_SOFT = "rgba(103, 232, 249, 0.12)"
COLOR_ROSE = "#fb7185"
COLOR_ROSE_SOFT = "rgba(251, 113, 133, 0.12)"
COLOR_EMERALD = "#6ee7b7"
COLOR_ORANGE = "#fb923c"
COLOR_SLATE = "#cbd5e1"

TEMPERATURE_THEMES = {
    "Very Hot": {
        "accent": COLOR_ROSE,
        "accent_soft": "rgba(251, 113, 133, 0.18)",
        "badge_bg": "rgba(251, 113, 133, 0.15)",
        "border": "rgba(251, 113, 133, 0.32)",
        "emoji": "\U0001F525",
    },
    "Hot": {
        "accent": COLOR_ORANGE,
        "accent_soft": "rgba(251, 146, 60, 0.18)",
        "badge_bg": "rgba(251, 146, 60, 0.15)",
        "border": "rgba(251, 146, 60, 0.30)",
        "emoji": "\U0001F321\uFE0F",
    },
    "Neutral": {
        "accent": COLOR_SLATE,
        "accent_soft": "rgba(203, 213, 225, 0.12)",
        "badge_bg": "rgba(203, 213, 225, 0.10)",
        "border": "rgba(203, 213, 225, 0.24)",
        "emoji": "\u2696\uFE0F",
    },
    "Cold": {
        "accent": COLOR_CYAN,
        "accent_soft": "rgba(103, 232, 249, 0.16)",
        "badge_bg": "rgba(103, 232, 249, 0.12)",
        "border": "rgba(103, 232, 249, 0.28)",
        "emoji": "\U0001F9CA",
    },
    "Very Cold": {
        "accent": "#a5f3fc",
        "accent_soft": "rgba(165, 243, 252, 0.18)",
        "badge_bg": "rgba(165, 243, 252, 0.14)",
        "border": "rgba(165, 243, 252, 0.30)",
        "emoji": "\u2744\uFE0F\u2744\uFE0F",
    },
}

BIAS_THEMES = {
    "bullish": {"bg": "rgba(103, 232, 249, 0.12)", "text": "#cffafe"},
    "bearish": {"bg": "rgba(251, 113, 133, 0.12)", "text": "#ffe4e6"},
    "neutral": {"bg": "rgba(203, 213, 225, 0.10)", "text": "#e2e8f0"},
}

STATUS_THEMES = {
    "bullish": {"bg": "rgba(103, 232, 249, 0.12)", "text": "#cffafe"},
    "bearish": {"bg": "rgba(251, 113, 133, 0.12)", "text": "#ffe4e6"},
    "neutral": {"bg": "rgba(203, 213, 225, 0.10)", "text": "#e2e8f0"},
    "oversold": {"bg": "rgba(103, 232, 249, 0.12)", "text": "#cffafe"},
    "overbought": {"bg": "rgba(251, 113, 133, 0.12)", "text": "#ffe4e6"},
}

RISK_THEMES = {
    "low": {"bg": "rgba(103, 232, 249, 0.12)", "text": "#cffafe", "accent": COLOR_CYAN},
    "elevated": {"bg": "rgba(251, 146, 60, 0.12)", "text": "#fed7aa", "accent": COLOR_ORANGE},
    "high": {"bg": "rgba(251, 113, 133, 0.12)", "text": "#ffe4e6", "accent": COLOR_ROSE},
    "extreme": {"bg": "rgba(244, 63, 94, 0.16)", "text": "#ffe4e6", "accent": COLOR_ROSE},
    "unknown": {"bg": "rgba(203, 213, 225, 0.10)", "text": "#e2e8f0", "accent": COLOR_SLATE},
}



def format_currency(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    return f"${value:,.2f}"


def format_number(value: Optional[float], digits: int = 2) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.{digits}f}"


def format_percent(value: Optional[float], digits: int = 2, signed: bool = True) -> str:
    if value is None:
        return "N/A"
    sign = "+" if signed and value > 0 else ""
    return f"{sign}{value:.{digits}f}%"


def format_score(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value > 0 else ""
    if float(value).is_integer():
        return f"{sign}{int(value)}"
    return f"{sign}{value:.1f}"


def format_weight_pct(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    if float(value).is_integer():
        return f"{int(value)}%"
    return f"{value:.1f}%"


def format_timestamp(value: Optional[str]) -> str:
    if not value:
        return "N/A"
    try:
        timestamp = pd.Timestamp(value).tz_convert("UTC")
        return timestamp.strftime("%b %d, %Y %H:%M UTC")
    except Exception:
        return str(value)


def get_temperature_theme(label: str) -> Dict[str, str]:
    return TEMPERATURE_THEMES.get(label, TEMPERATURE_THEMES["Neutral"])


def get_bias_theme(bias: str) -> Dict[str, str]:
    return BIAS_THEMES.get(bias, BIAS_THEMES["neutral"])


def get_status_theme(status: str) -> Dict[str, str]:
    return STATUS_THEMES.get(status, STATUS_THEMES["neutral"])


def get_risk_theme(risk_level: str) -> Dict[str, str]:
    return RISK_THEMES.get(risk_level, RISK_THEMES["unknown"])


def return_color(value: Optional[float]) -> str:
    if value is None:
        return COLOR_MUTED
    if value > 0:
        return COLOR_EMERALD
    if value < 0:
        return COLOR_ROSE
    return COLOR_WHITE


def win_rate_color(value: Optional[float]) -> str:
    if value is None:
        return COLOR_MUTED
    if value > 50:
        return COLOR_EMERALD
    if value < 50:
        return COLOR_ROSE
    return COLOR_WHITE


def build_temperature_gauge_figure(valuation: Dict[str, Any]) -> go.Figure:
    clipped_gap = max(-20.0, min(20.0, valuation["valuation_gap_pct"]))
    theme = get_temperature_theme(valuation["temperature"]["label"])

    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=clipped_gap,
            number={"suffix": "%", "font": {"size": 42, "color": COLOR_WHITE}},
            title={"text": "Valuation Gap", "font": {"size": 18, "color": COLOR_MUTED}},
            gauge={
                "axis": {
                    "range": [-20, 20],
                    "tickvals": [-20, -10, 0, 10, 20],
                    "ticktext": ["Very Cold", "Cold", "Neutral", "Hot", "Very Hot"],
                    "tickcolor": COLOR_MUTED,
                    "tickfont": {"color": COLOR_MUTED, "size": 11},
                },
                "bar": {"color": theme["accent"], "thickness": 0.36},
                "borderwidth": 0,
                "bgcolor": "rgba(15, 23, 42, 0.82)",
                "steps": [
                    {"range": [-20, -10], "color": "rgba(34, 211, 238, 0.18)"},
                    {"range": [-10, 10], "color": "rgba(203, 213, 225, 0.12)"},
                    {"range": [10, 20], "color": "rgba(251, 113, 133, 0.18)"},
                ],
                "threshold": {
                    "line": {"color": COLOR_WHITE, "width": 4},
                    "thickness": 0.85,
                    "value": clipped_gap,
                },
            },
        )
    )
    figure.update_layout(
        margin={"l": 20, "r": 20, "t": 40, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
    )
    return figure


def build_demand_destruction_figure(demand_profile: Dict[str, Any]) -> go.Figure:
    current_price = demand_profile.get("current_price")
    if current_price is None:
        figure = go.Figure()
        figure.add_annotation(
            text="Demand destruction data unavailable",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"color": COLOR_MUTED, "size": 16},
        )
        figure.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=220,
            margin={"l": 10, "r": 10, "t": 10, "b": 10},
            xaxis={"visible": False},
            yaxis={"visible": False},
        )
        return figure

    theme = get_risk_theme(demand_profile.get("risk_level", "unknown"))
    clipped_price = max(0.0, min(180.0, float(current_price)))
    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=clipped_price,
            number={"prefix": "$", "font": {"size": 30, "color": COLOR_WHITE}},
            title={"text": "Demand Destruction Risk", "font": {"size": 16, "color": COLOR_MUTED}},
            gauge={
                "axis": {
                    "range": [0, 180],
                    "tickvals": [0, 60, 120, 150, 180],
                    "ticktext": ["0", "60", "120", "150", "180"],
                    "tickcolor": COLOR_MUTED,
                    "tickfont": {"color": COLOR_MUTED, "size": 10},
                },
                "bar": {"color": theme["accent"], "thickness": 0.34},
                "borderwidth": 0,
                "bgcolor": "rgba(15, 23, 42, 0.82)",
                "steps": [
                    {"range": [0, 120], "color": "rgba(103, 232, 249, 0.12)"},
                    {"range": [120, 150], "color": "rgba(251, 146, 60, 0.16)"},
                    {"range": [150, 180], "color": "rgba(251, 113, 133, 0.22)"},
                ],
                "threshold": {
                    "line": {"color": COLOR_WHITE, "width": 4},
                    "thickness": 0.85,
                    "value": clipped_price,
                },
            },
        )
    )
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        height=220,
    )
    return figure


def build_price_vs_fair_value_figure(history: List[Dict[str, Any]]) -> go.Figure:
    frame = pd.DataFrame(history)

    figure = go.Figure()
    if frame.empty:
        figure.add_annotation(
            text="Historical model data unavailable",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"color": COLOR_MUTED, "size": 16},
        )
        figure.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=360,
            margin={"l": 10, "r": 10, "t": 10, "b": 10},
            xaxis={"visible": False},
            yaxis={"visible": False},
        )
        return figure

    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["actual_price"],
            mode="lines",
            name="Actual Price",
            line={"color": COLOR_CYAN, "width": 3},
            hovertemplate="Date: %{x}\nActual: $%{y:.2f}\nGap: %{customdata:.2f}%",
            customdata=frame["valuation_gap_pct"],
        )
    )
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["fair_value"],
            mode="lines",
            name="Model Fair Value",
            line={"color": "#fda4af", "width": 2.5, "dash": "dash"},
            hovertemplate="Date: %{x}\nFair Value: $%{y:.2f}",
        )
    )
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": COLOR_MUTED},
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        hovermode="x unified",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        xaxis={"showgrid": False, "tickfont": {"color": COLOR_MUTED}, "title": ""},
        yaxis={
            "gridcolor": "rgba(148, 163, 184, 0.14)",
            "zeroline": False,
            "tickprefix": "$",
            "tickfont": {"color": COLOR_MUTED},
            "title": "",
        },
        height=360,
    )
    return figure


def build_gap_history_figure(history: List[Dict[str, Any]]) -> go.Figure:
    frame = pd.DataFrame(history)
    figure = go.Figure()
    if frame.empty:
        figure.add_annotation(
            text="Historical gap data unavailable",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"color": COLOR_MUTED, "size": 16},
        )
        figure.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=360,
            margin={"l": 10, "r": 10, "t": 10, "b": 10},
            xaxis={"visible": False},
            yaxis={"visible": False},
        )
        return figure

    frame["hot_gap"] = frame["valuation_gap_pct"].where(frame["valuation_gap_pct"] > 10)
    frame["neutral_gap"] = frame["valuation_gap_pct"].where(
        frame["valuation_gap_pct"].between(-10, 10)
    )
    frame["cold_gap"] = frame["valuation_gap_pct"].where(frame["valuation_gap_pct"] < -10)

    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["hot_gap"],
            mode="lines",
            line={"width": 0},
            fill="tozeroy",
            fillcolor="rgba(251, 113, 133, 0.30)",
            name="Hot Zone",
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["neutral_gap"],
            mode="lines",
            line={"width": 0},
            fill="tozeroy",
            fillcolor="rgba(148, 163, 184, 0.18)",
            name="Neutral Zone",
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["cold_gap"],
            mode="lines",
            line={"width": 0},
            fill="tozeroy",
            fillcolor="rgba(34, 211, 238, 0.28)",
            name="Cold Zone",
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["valuation_gap_pct"],
            mode="lines",
            name="Valuation Gap",
            line={"color": COLOR_WHITE, "width": 2.2},
            hovertemplate=(
                "Date: %{x}\nGap: %{y:.2f}%\nTemperature: %{customdata}"
            ),
            customdata=frame["temperature_label"],
        )
    )
    figure.add_hline(y=10, line={"color": COLOR_ROSE, "dash": "dash", "width": 1.4})
    figure.add_hline(y=0, line={"color": "rgba(148, 163, 184, 0.35)", "dash": "dot", "width": 1.2})
    figure.add_hline(y=-10, line={"color": COLOR_CYAN, "dash": "dash", "width": 1.4})
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": COLOR_MUTED},
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        hovermode="x unified",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        xaxis={"showgrid": False, "title": ""},
        yaxis={
            "gridcolor": "rgba(148, 163, 184, 0.14)",
            "ticksuffix": "%",
            "zeroline": False,
            "title": "",
        },
        height=360,
    )
    return figure

def format_threshold_distance(distance: Optional[float], threshold: float) -> tuple[str, str]:
    if distance is None:
        return "N/A", f"vs ${threshold:.0f}"
    if distance >= 0:
        return format_currency(abs(distance)), f"above ${threshold:.0f}"
    return format_currency(abs(distance)), f"below ${threshold:.0f}"



# ═══════════════════════════════════════════════════════════════════════════
# STREAMLIT RENDERING (replaces the Dash layout and callbacks)
# ═══════════════════════════════════════════════════════════════════════════
CHART_CONFIG = {"displayModeBar": False, "responsive": True}

st.markdown(
    f"""
<style>
.stApp {{
  background:
    radial-gradient(circle at top left, rgba(8, 145, 178, 0.14), transparent 28%),
    radial-gradient(circle at top right, rgba(244, 63, 94, 0.12), transparent 26%),
    linear-gradient(180deg, #07111f 0%, #040814 45%, #050816 100%);
}}
[class*="st-key-copanel"] {{
  border: 1px solid {COLOR_BORDER}; background: {COLOR_PANEL}; border-radius: 28px; padding: 22px;
  box-shadow: 0 24px 80px rgba(2, 6, 23, 0.38);
}}
.co-panel {{ border: 1px solid {COLOR_BORDER}; background: {COLOR_PANEL}; border-radius: 28px; padding: 22px; box-shadow: 0 24px 80px rgba(2, 6, 23, 0.38); margin-bottom: 1rem; }}
.co-sub {{ border: 1px solid {COLOR_BORDER}; background: {COLOR_PANEL_SUBTLE}; border-radius: 22px; padding: 16px; }}
.co-eyebrow {{ font-size: 12px; letter-spacing: 0.26em; text-transform: uppercase; color: #bae6fd; font-weight: 700; }}
.co-label {{ font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: {COLOR_MUTED}; }}
.co-h1 {{ margin: 10px 0 0; font-size: 42px; line-height: 1.05; color: {COLOR_WHITE}; font-weight: 800; }}
.co-h2 {{ margin: 14px 0 0; font-size: 40px; line-height: 1.08; color: {COLOR_WHITE}; font-weight: 800; }}
.co-h3 {{ margin: 12px 0 0; font-size: 30px; color: {COLOR_WHITE}; font-weight: 700; line-height: 1.2; }}
.co-p {{ font-size: 15px; line-height: 1.7; color: #cbd5e1; margin: 10px 0 0; }}
.co-muted {{ font-size: 13px; color: {COLOR_MUTED}; }}
.co-grid {{ display: grid; gap: 12px; }}
.co-grid-180 {{ grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }}
.co-grid-210 {{ grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); }}
.co-grid-280 {{ grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
.co-grid-320 {{ grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px; }}
.co-badge {{ display: inline-block; padding: 6px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; letter-spacing: 0.08em; }}
.co-row {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }}
.co-mt {{ margin-top: 16px; }}
</style>
""",
    unsafe_allow_html=True,
)


def badge_html(text: str, theme: Dict[str, str]) -> str:
    return f'<span class="co-badge" style="background:{theme["bg"]};color:{theme["text"]}">{text.upper()}</span>'


def metric_html(
    label: str,
    value: str,
    subtitle: Optional[str] = None,
    value_color: str = COLOR_WHITE,
    value_font_size: str = "30px",
    extra_style: str = "",
) -> str:
    sub = f'<div class="co-muted" style="margin-top:4px">{subtitle}</div>' if subtitle else ""
    return (
        f'<div class="co-sub" style="{extra_style}"><div class="co-label">{label}</div>'
        f'<div style="font-size:{value_font_size};font-weight:700;color:{value_color};margin-top:8px">{value}</div>{sub}</div>'
    )


def grid_html(items: List[str], min_width: int = 180, extra_style: str = "") -> str:
    return f'<div class="co-grid co-grid-{min_width}" style="{extra_style}">{"".join(items)}</div>'


def html(content: str) -> None:
    st.markdown(content, unsafe_allow_html=True)


def render_header(snapshot: Dict[str, Any]) -> None:
    asset = snapshot["asset"]
    valuation = snapshot["valuation"]
    temperature = valuation["temperature"]
    theme = get_temperature_theme(temperature["label"])

    live_price = (
        '<div class="co-sub"><div class="co-label">Live Price</div>'
        '<div style="margin-top:10px;display:flex;align-items:center;flex-wrap:wrap;gap:12px">'
        f'<span style="font-size:42px;font-weight:800;color:{COLOR_WHITE}">{format_currency(asset["current_price"])}</span>'
        f'<span style="padding:8px 14px;border-radius:999px;background:{theme["badge_bg"]};color:{COLOR_WHITE};font-weight:700">'
        f'{temperature["label"]} {theme["emoji"]}</span></div>'
        f'<div class="co-muted" style="margin-top:10px;font-size:14px">Valuation gap {format_percent(valuation["valuation_gap_pct"])}</div></div>'
    )
    updated = (
        '<div class="co-sub">'
        f'<div style="font-size:14px;color:#cbd5e1">Last updated {format_timestamp(asset["last_updated"])}</div>'
        f'<div style="font-size:14px;color:#cbd5e1;margin-top:10px">{temperature["description"]}</div>'
        f'<div class="co-muted" style="margin-top:12px">Dashboard snapshot generated {format_timestamp(snapshot["meta"]["generated_at"])}</div></div>'
    )
    html(
        '<div class="co-panel">'
        '<div class="co-eyebrow">Quantitative Dashboard</div>'
        '<div class="co-h1">WTI Crude Oil Valuation Model</div>'
        '<p class="co-p" style="max-width:980px;font-size:16px">A Python-native valuation dashboard blending crude inventories, DXY, '
        "oil volatility, TIPS-implied inflation, credit growth expectations, substitution pressure, and geopolitical risk "
        "into a transparent fair-value estimate.</p>"
        + grid_html([live_price, updated], 280, "margin-top:22px;gap:14px")
        + "</div>"
    )


def render_temperature_section(snapshot: Dict[str, Any]) -> None:
    asset = snapshot["asset"]
    valuation = snapshot["valuation"]
    fundamentals = snapshot["fundamentals"]
    theme = get_temperature_theme(valuation["temperature"]["label"])
    demand_profile = valuation["demand_destruction"]
    stagflation_monitor = valuation["stagflation_monitor"]
    demand_120_value, demand_120_subtitle = format_threshold_distance(demand_profile.get("distance_to_120"), 120.0)
    demand_150_value, demand_150_subtitle = format_threshold_distance(demand_profile.get("distance_to_150"), 150.0)
    regime_notes = valuation.get("regime_notes", [])

    left, right = st.columns(2, gap="medium")

    with left, st.container(key="copanel_temperature"):
        html(
            f'<style>.st-key-copanel_temperature {{ border-color: {theme["border"]} !important; }}</style>'
            '<div class="co-eyebrow">Temperature Gauge</div>'
            f'<div class="co-h2">{valuation["temperature"]["label"]} {theme["emoji"]}</div>'
            '<p class="co-p">The model compares WTI spot price with an estimated fair value derived from the 50-day average, '
            "the weighted demand/supply macro score, and an OVX-based volatility factor, then applies price-regime overlays "
            "for demand destruction and recession risk.</p>"
        )
        st.plotly_chart(build_temperature_gauge_figure(valuation), config=CHART_CONFIG, width="stretch")
        html(
            grid_html(
                [
                    metric_html("Current Price", format_currency(asset["current_price"])),
                    metric_html("Estimated Fair Value", format_currency(valuation["estimated_fair_value"])),
                    metric_html("Valuation Gap", format_percent(valuation["valuation_gap_pct"])),
                    metric_html("Base Fair Value", format_currency(valuation["base_estimated_fair_value"])),
                ],
                210,
                "gap:14px",
            )
        )

    with right, st.container(key="copanel_lens"):
        html(
            '<div class="co-label">Model Lens</div>'
            '<p class="co-p" style="line-height:1.75;margin-top:12px">This gauge is deliberately valuation-oriented rather than '
            "purely trend-following. It now separates supply-risk premia, TIPS-implied inflation pressure, forward credit growth "
            "expectations, and substitution risk before applying demand-destruction and stagflation overlays.</p>"
            '<div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:10px">'
            + badge_html(demand_profile["status_label"], get_risk_theme(demand_profile["risk_level"]))
            + badge_html(stagflation_monitor["status_label"], get_risk_theme(stagflation_monitor["risk_level"]))
            + "</div>"
            + grid_html(
                [
                    metric_html("Composite Score", format_score(fundamentals["normalized_score"])),
                    metric_html("Base Score", format_score(fundamentals["base_normalized_score"])),
                    metric_html("Volatility Factor", format_number(valuation["volatility_factor"], 2)),
                    metric_html("Demand Discount", format_percent(-demand_profile["fair_value_discount_pct"], signed=True)),
                    metric_html("Recession Discount", format_percent(-stagflation_monitor["fair_value_discount_pct"], signed=True)),
                    metric_html("50D Reference", format_currency(valuation["reference_sma_50"])),
                    metric_html(
                        "Overlay Gap Push",
                        format_percent(valuation["valuation_gap_pct"] - valuation["base_valuation_gap_pct"]),
                    ),
                ],
                180,
                "margin-top:18px;gap:14px",
            )
        )
        st.plotly_chart(build_demand_destruction_figure(demand_profile), config=CHART_CONFIG, width="stretch")
        notes = "".join(f'<div style="font-size:13px;line-height:1.7;color:#cbd5e1">- {note}</div>' for note in regime_notes)
        html(
            grid_html(
                [
                    metric_html("Distance to $120", demand_120_value, demand_120_subtitle, value_font_size="24px"),
                    metric_html("Distance to $150", demand_150_value, demand_150_subtitle, value_font_size="24px"),
                    metric_html(
                        "Demand Score Penalty",
                        format_percent(-demand_profile["composite_score_penalty"], signed=True),
                        "normalized score impact",
                        value_font_size="24px",
                    ),
                ],
                180,
            )
            + '<div class="co-sub co-mt">'
            f'<div style="font-size:14px;font-weight:700;color:{COLOR_WHITE}">Regime Notes</div>'
            f'<div style="display:grid;gap:6px;margin-top:8px">{notes}</div></div>'
        )


def render_technical_panel(technicals: Dict[str, Any]) -> None:
    rsi = technicals["rsi_14"]
    macd = technicals["macd"]
    averages = technicals["moving_averages"]
    rsi_width = max(0, min(100, rsi["value"] or 0))

    rsi_block = (
        '<div class="co-sub"><div class="co-row"><div>'
        '<div class="co-label">RSI (14)</div>'
        f'<div style="font-size:38px;font-weight:800;color:{COLOR_WHITE};margin-top:8px">{format_number(rsi["value"])}</div></div>'
        f'{badge_html(rsi["status"], get_status_theme(rsi["status"]))}</div>'
        '<div style="height:8px;border-radius:999px;background:linear-gradient(90deg, #67e8f9 0%, #fcd34d 50%, #fb7185 100%);'
        f'margin-top:16px;width:{rsi_width}%"></div></div>'
    )
    macd_block = (
        '<div class="co-sub"><div class="co-row"><div>'
        '<div class="co-label">MACD</div>'
        f'<div style="font-size:28px;font-weight:700;color:{COLOR_WHITE};margin-top:8px">{format_number(macd["line"], 3)}</div></div>'
        f'{badge_html(macd["status"], get_status_theme(macd["status"]))}</div>'
        + grid_html(
            [
                metric_html("Signal Line", format_number(macd["signal"], 3)),
                metric_html("Histogram", format_number(macd["histogram"], 3)),
            ],
            180,
            "margin-top:16px",
        )
        + "</div>"
    )
    trend_block = grid_html(
        [
            metric_html("50D SMA", format_currency(averages["sma_50"])),
            metric_html("200D SMA", format_currency(averages["sma_200"])),
            metric_html("vs 50D SMA", format_percent(averages["price_vs_sma_50_pct"])),
            metric_html("vs 200D SMA", format_percent(averages["price_vs_sma_200_pct"])),
        ],
        180,
    )
    html(
        '<div class="co-panel">'
        '<div class="co-eyebrow">Technical Overlay</div>'
        '<div class="co-h3">RSI, MACD, and Trend Levels</div>'
        '<p class="co-p">These signals do not drive the full model on their own, but they help frame whether valuation extremes '
        "are occurring alongside momentum strength or stress.</p>"
        + grid_html([rsi_block, macd_block], 280, "margin-top:18px;gap:14px")
        + f'<div class="co-mt">{trend_block}</div>'
        + "</div>"
    )


def render_charts_section(snapshot: Dict[str, Any]) -> None:
    history = snapshot["history"]
    latest_gap = history[-1]["valuation_gap_pct"] if history else None
    max_divergence = None
    if history:
        max_divergence = max(history, key=lambda row: abs(row["valuation_gap_pct"]))["valuation_gap_pct"]

    left, right = st.columns(2, gap="medium")
    with left, st.container(key="copanel_price"):
        html(
            '<div class="co-eyebrow">Historical Performance</div>'
            '<div class="co-h3">Price vs. Model Fair Value</div>'
            "<p class=\"co-p\">This chart reconstructs the model's fair value over the last 90 days after demand-destruction and "
            "stagflation overlays, making it easy to inspect where price diverged from the regime-adjusted estimate and whether "
            "it later converged.</p>"
            + grid_html(
                [
                    metric_html("Latest Gap", format_percent(latest_gap)),
                    metric_html("Largest 90D Divergence", format_percent(max_divergence)),
                ],
                210,
                "margin-top:18px",
            )
        )
        st.plotly_chart(build_price_vs_fair_value_figure(history), config=CHART_CONFIG, width="stretch")

    with right, st.container(key="copanel_gap"):
        html(
            '<div class="co-eyebrow">Historical Performance</div>'
            '<div class="co-h3">Temperature and Gap History</div>'
            '<p class="co-p">Hot zones mark periods when the market ran far above model fair value, while Cold zones highlight '
            "pricing that fell materially below the model estimate.</p>"
        )
        st.plotly_chart(build_gap_history_figure(history), config=CHART_CONFIG, width="stretch")


def backtest_card_html(signal: str, stats: Dict[str, Any]) -> str:
    expects_positive = stats["expected_direction"] == "positive"
    direction_text = "Expect upside reversion" if expects_positive else "Expect downside reversion"
    direction_color = COLOR_CYAN if expects_positive else COLOR_ROSE

    avg_5d = format_percent(stats["avg_5d_return_pct"]) if stats["avg_5d_return_pct"] is not None else "Insufficient data"
    avg_10d = format_percent(stats["avg_10d_return_pct"]) if stats["avg_10d_return_pct"] is not None else "Insufficient data"
    win_rate = f'{stats["win_rate_pct"]:.1f}%' if stats["win_rate_pct"] is not None else "Insufficient data"
    explanation = (
        f"{signal} is treated as undervaluation, so positive forward returns count as successful reversion toward fair value."
        if expects_positive
        else f"{signal} is treated as overvaluation, so negative forward returns count as successful downside mean reversion."
    )

    return (
        '<div class="co-panel" style="margin:0"><div class="co-row"><div>'
        f'<div style="font-size:28px;font-weight:800;color:{COLOR_WHITE}">{signal}</div>'
        f'<div style="margin-top:10px;display:inline-block;padding:7px 12px;border-radius:999px;background:{direction_color}22;'
        f'color:{COLOR_WHITE};font-size:11px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase">{direction_text}</div></div>'
        '<div class="co-sub" style="text-align:center;min-width:100px"><div class="co-label">Count</div>'
        f'<div style="font-size:32px;font-weight:800;color:{COLOR_WHITE};margin-top:8px">{stats["occurrence_count"]}</div></div></div>'
        + grid_html(
            [
                metric_html("Avg 5D Return", avg_5d, f'{stats["valid_5d_samples"]} valid windows',
                            value_color=return_color(stats["avg_5d_return_pct"]), value_font_size="26px"),
                metric_html("Avg 10D Return", avg_10d, f'{stats["valid_10d_samples"]} valid windows',
                            value_color=return_color(stats["avg_10d_return_pct"]), value_font_size="26px"),
                metric_html("Win Rate", win_rate, "10D mean-reversion test",
                            value_color=win_rate_color(stats["win_rate_pct"]), value_font_size="26px"),
            ],
            180,
            "margin-top:18px",
        )
        + f'<div style="margin-top:16px;padding:14px 16px;border-radius:18px;background:rgba(2, 6, 23, 0.55);'
        f'border:1px solid {COLOR_BORDER};font-size:14px;line-height:1.7;color:#cbd5e1">{explanation}</div></div>'
    )


def render_backtest_section(snapshot: Dict[str, Any]) -> None:
    summary = snapshot["backtest_summary"]
    html(
        '<div class="co-panel">'
        '<div class="co-eyebrow">Backtest Summary</div>'
        '<div class="co-h3">Forward Returns by Temperature Signal</div>'
        '<p class="co-p">This panel measures what happened after the model flashed a non-neutral valuation signal. Cold signals '
        "seek positive forward returns, while Hot signals seek negative returns as price mean-reverts toward fair value.</p>"
        + grid_html(
            [
                f'<div class="co-sub" style="background:{COLOR_CYAN_SOFT}"><div style="font-size:14px;font-weight:700;color:{COLOR_WHITE}">'
                'Win Rate Logic</div><div style="font-size:13px;line-height:1.6;color:#cbd5e1;margin-top:8px">'
                "Win Rate indicates % of time price reverted towards fair value within 10 days.</div></div>",
                f'<div class="co-sub"><div style="font-size:14px;font-weight:700;color:{COLOR_WHITE}">Interpretation</div>'
                '<div style="font-size:13px;line-height:1.6;color:#cbd5e1;margin-top:8px">Hot signals should ideally be followed '
                "by negative returns, while Cold signals should ideally be followed by positive returns.</div></div>",
            ],
            280,
            "margin-top:18px;gap:14px",
        )
        + f'<div class="co-sub" style="margin-top:14px;font-size:14px;line-height:1.7;color:#cbd5e1">{summary["win_rate_definition"]}</div>'
        + "</div>"
    )
    cards = [backtest_card_html(signal, summary["signals"][signal]) for signal in summary["signal_order"]]
    html(grid_html(cards, 320, "margin-bottom:1rem"))


def parameter_card_html(parameter: Dict[str, Any]) -> str:
    display_digits = int(parameter.get("display_digits", 2))
    deviation_display = (
        format_percent(parameter["deviation_pct"])
        if parameter["deviation_pct"] is not None
        else format_score(parameter["weighted_contribution"])
    )
    benchmark_display = (
        "Rule-based" if parameter["benchmark_value"] is None else format_number(parameter["benchmark_value"], display_digits)
    )
    extras = ""
    if parameter.get("auxiliary_label"):
        extras = metric_html(
            parameter["auxiliary_label"], format_percent(parameter["auxiliary_value"]), value_font_size="20px", extra_style="margin-top:12px"
        )

    return (
        '<div class="co-panel" style="margin:0"><div class="co-row"><div>'
        f'<div style="font-size:16px;font-weight:700;color:{COLOR_WHITE}">{parameter["name"]}</div>'
        f'<div class="co-label" style="margin-top:4px">Weight {format_weight_pct(parameter["weight_pct"])}</div></div>'
        f'{badge_html(parameter["bias"], get_bias_theme(parameter["bias"]))}</div>'
        '<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:12px;margin-top:18px"><div>'
        '<div class="co-label">Current Value</div>'
        f'<div style="font-size:34px;font-weight:800;color:{COLOR_WHITE};margin-top:10px">{format_number(parameter["current_value"], display_digits)}</div>'
        f'<div class="co-muted" style="margin-top:4px">{parameter["unit"]}</div></div>'
        f'<div class="co-sub" style="min-width:110px;text-align:center;background:{get_bias_theme(parameter["bias"])["bg"]}">'
        '<div class="co-label">Score</div>'
        f'<div style="font-size:34px;font-weight:800;color:{COLOR_WHITE};margin-top:8px">{format_score(parameter["score"])}</div></div></div>'
        + grid_html(
            [metric_html(parameter["benchmark_label"], benchmark_display), metric_html("Deviation / Contribution", deviation_display)],
            180,
            "margin-top:16px",
        )
        + extras
        + f'<p class="co-p" style="font-size:14px;margin-top:16px">{parameter["rationale"]}</p></div>'
    )


def render_fundamentals_section(snapshot: Dict[str, Any]) -> None:
    parameters = snapshot["fundamentals"]["parameters"]
    inventory_snapshot = snapshot["market_data"]["inventory_snapshot"]
    driver_count = snapshot["fundamentals"].get("parameter_count", len(parameters))
    html(
        '<div class="co-panel">'
        '<div class="co-eyebrow">Fundamental Dashboard</div>'
        f'<div class="co-h3">{driver_count}-Driver Scoring Framework</div>'
        '<p class="co-p">Each parameter is scored from -2 to +2, weighted into a normalized macro score, and then fed into the '
        "fair-value equation to estimate how stretched current WTI pricing may be across inventories, dollar strength, trend "
        "context, volatility, geopolitical risk, implied inflation, forward growth expectations, and substitution pressure.</p>"
        f'<div class="co-sub" style="margin-top:18px"><div style="font-size:14px;font-weight:700;color:{COLOR_WHITE}">'
        f'Inventory source: {inventory_snapshot["source"]}</div>'
        f'<div class="co-muted" style="line-height:1.6;margin-top:8px">{inventory_snapshot["note"]}</div></div>'
        "</div>"
    )
    html(grid_html([parameter_card_html(parameter) for parameter in parameters], 320, "margin-bottom:1rem"))


@st.cache_data(ttl=REFRESH_INTERVAL_SECONDS, show_spinner=False)
def get_snapshot() -> Dict[str, Any]:
    return load_crude_oil_valuation_snapshot()


toolbar_left, toolbar_right = st.columns([4, 1], vertical_alignment="center")
with toolbar_left:
    html(
        '<div style="padding-top:8px"><div style="font-size:12px;letter-spacing:0.22em;text-transform:uppercase;color:#bae6fd;font-weight:700">'
        'Live market data</div><div class="co-muted" style="font-size:14px;margin-top:6px">'
        "Auto refresh every 5 minutes · Yahoo Finance + EIA</div></div>"
    )
with toolbar_right:
    if st.button("Refresh Data", icon=":material/refresh:", width="stretch"):
        get_snapshot.clear()


@st.fragment(run_every=REFRESH_INTERVAL_SECONDS)
def dashboard() -> None:
    try:
        with st.spinner(
            "Pulling live WTI, DXY, OVX, defense ETF, TIPS, Treasury, credit ETF, UNG, and China ETF data, then rebuilding the "
            "demand-destruction and recession-adjusted fair-value history…"
        ):
            snapshot = get_snapshot()
    except Exception as exc:  # pragma: no cover - interactive runtime path
        logger.exception("Dashboard refresh failed.")
        html(
            '<div class="co-panel" style="text-align:center;padding:48px 22px">'
            f'<div class="co-h2" style="margin:0;font-size:34px">Unable to load data</div><p class="co-p">{exc}</p></div>'
        )
        return

    render_header(snapshot)
    render_temperature_section(snapshot)
    render_technical_panel(snapshot["technicals"])
    render_charts_section(snapshot)
    render_backtest_section(snapshot)
    render_fundamentals_section(snapshot)
    html(
        f'<div class="co-panel" style="border-left:4px solid {COLOR_CYAN}">'
        f'<div style="font-size:14px;line-height:1.7;color:#cbd5e1">{snapshot["disclaimer"]}</div></div>'
    )


dashboard()
