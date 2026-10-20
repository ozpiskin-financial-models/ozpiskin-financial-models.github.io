"""
WTI Crude Oil Valuation — Streamlit page.

Every number comes from models/crude_oil_engine.py (the original model's
calculation code, unchanged). This file only lays the results out with the
shared design system in ui/kit.py. Display controls (range, tabs) only slice
the cached snapshot; they never refetch data or rerun the model.
"""

from __future__ import annotations

from html import escape
from typing import Any, Dict, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from models.crude_oil_engine import load_crude_oil_valuation_snapshot
from ui import kit

REFRESH_SECONDS = 5 * 60

TEMPERATURE_TONE = {"Very Hot": "down", "Hot": "warn", "Neutral": "", "Cold": "blue", "Very Cold": "blue"}
RISK_TONE = {"low": "", "elevated": "warn", "high": "down", "extreme": "down", "unknown": ""}
SIGNAL_TONE = {"bullish": "up", "bearish": "down", "oversold": "up", "overbought": "down", "neutral": ""}

# Which market series each driver is observed on (for its "as of" date).
DRIVER_SERIES = {
    "usd_strength": "dxy",
    "trend_context": "crude_oil",
    "ovx": "ovx",
    "geopolitical_risk": "geopolitical_risk",
    "implied_inflation": "tips",
    "growth_expectations": "high_yield_credit",
    "substitution_risk": "substitution_proxy",
}
DATA_SOURCES = [
    ("WTI crude futures", "crude_oil"),
    ("US dollar index", "dxy"),
    ("Crude-oil volatility (OVX)", "ovx"),
    ("Aerospace & defense ETF", "geopolitical_risk"),
    ("TIPS ETF", "tips"),
    ("7–10Y Treasury ETF", "treasury"),
    ("High-yield credit ETF", "high_yield_credit"),
    ("Investment-grade credit ETF", "investment_grade_credit"),
    ("Natural gas fund", "substitution_proxy"),
    ("China large-cap ETF", "china_market"),
]

RANGES = {"1M": pd.DateOffset(months=1), "3M": pd.DateOffset(months=3), "All": None}

# Valuation-gap zones from map_temperature() in the engine, drawn on a -30%..+30% scale.
SCALE_MIN, SCALE_MAX = -30.0, 30.0
SCALE_ZONES = [
    ("Very Cold", -30.0, -20.0, "#60A5FA"),
    ("Cold", -20.0, -10.0, "rgba(96, 165, 250, 0.45)"),
    ("Neutral", -10.0, 10.0, "#283442"),
    ("Hot", 10.0, 20.0, "rgba(251, 191, 36, 0.6)"),
    ("Very Hot", 20.0, 30.0, "#F87171"),
]
SCALE_CSS = """
<style>
.co-scale { margin: 48px 0 8px; }
.co-track { position: relative; display: flex; height: 4px; border-radius: 2px; overflow: visible; }
.co-zone { height: 4px; }
.co-zone:first-child { border-radius: 2px 0 0 2px; } .co-zone:last-child { border-radius: 0 2px 2px 0; }
.co-marker { position: absolute; top: -36px; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; }
.co-marker span { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 4px; white-space: nowrap; font-variant-numeric: tabular-nums; }
.co-tick { display: block; width: 2px; height: 40px; background: var(--text); border-radius: 1px; flex: none; }
.co-labels { display: flex; margin-top: 16px; }
.co-labels div { font-size: 11px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); text-align: center; }
.co-labels div.on { color: var(--text); }
</style>
"""


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def get_snapshot() -> Dict[str, Any]:
    return load_crude_oil_valuation_snapshot()


def temperature_scale(gap: float, label: str) -> str:
    span = SCALE_MAX - SCALE_MIN
    position = (min(SCALE_MAX, max(SCALE_MIN, gap)) - SCALE_MIN) / span * 100
    track = "".join(f'<div class="co-zone" style="width:{(hi - lo) / span * 100}%;background:{color}"></div>' for _, lo, hi, color in SCALE_ZONES)
    labels = "".join(
        f'<div class="{"on" if name == label else ""}" style="width:{(hi - lo) / span * 100}%">{name}</div>'
        for name, lo, hi, _ in SCALE_ZONES
    )
    return (
        f'{SCALE_CSS}<div class="co-scale"><div class="co-track">{track}'
        f'<div class="co-marker" style="left:{position}%"><span>{kit.pct(gap)}</span><span class="co-tick"></span></div></div>'
        f'<div class="co-labels">{labels}</div></div>'
    )


def history_frame(history: List[Dict[str, Any]], window: str) -> pd.DataFrame:
    """Display slice of the model's history — the analytical series itself is untouched."""
    frame = pd.DataFrame(history)
    frame["date"] = pd.to_datetime(frame["date"])
    offset = RANGES[window]
    if offset is not None:
        frame = frame[frame["date"] >= frame["date"].max() - offset]
    return frame


def price_vs_fair_value_figure(frame: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(x=frame["date"], y=frame["actual_price"], name="WTI market price", mode="lines",
                   line={"color": kit.BLUE, "width": 2}, hovertemplate="$%{y:.2f}")
    )
    figure.add_trace(
        go.Scatter(x=frame["date"], y=frame["fair_value"], name="Estimated fair value", mode="lines",
                   line={"color": kit.MINT, "width": 2}, hovertemplate="$%{y:.2f}")
    )
    kit.style_figure(figure, 380)
    figure.update_yaxes(tickprefix="$")
    return figure


def gap_history_figure(frame: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    top = max(25.0, float(frame["valuation_gap_pct"].max()) + 5)
    bottom = min(-25.0, float(frame["valuation_gap_pct"].min()) - 5)
    figure.add_hrect(y0=10, y1=top, fillcolor="rgba(248, 113, 113, 0.06)", line_width=0)
    figure.add_hrect(y0=bottom, y1=-10, fillcolor="rgba(96, 165, 250, 0.06)", line_width=0)
    for level in (-10, 10):
        figure.add_hline(y=level, line={"color": kit.BORDER, "width": 1, "dash": "dot"})
    figure.add_hline(y=0, line={"color": kit.BORDER, "width": 1})
    figure.add_trace(
        go.Scatter(x=frame["date"], y=frame["valuation_gap_pct"], name="Valuation gap", mode="lines",
                   line={"color": kit.TEXT_2, "width": 2}, customdata=frame["temperature_label"],
                   hovertemplate="%{y:.2f}%  ·  %{customdata}")
    )
    kit.style_figure(figure, 300)
    figure.update_layout(showlegend=False)
    figure.update_yaxes(ticksuffix="%", range=[bottom, top])
    return figure


def threshold_distance(distance: float | None, threshold: int) -> str:
    if distance is None:
        return "—"
    side = "above" if distance >= 0 else "below"
    return f'{kit.money(abs(distance))} <span class="kt-muted">{side} ${threshold}</span>'


def render_valuation_gap(snapshot: Dict[str, Any], frame: pd.DataFrame, window: str) -> None:
    valuation = snapshot["valuation"]
    temperature = valuation["temperature"]
    history = snapshot["history"]
    widest = max(history, key=lambda row: abs(row["valuation_gap_pct"]))["valuation_gap_pct"]
    with kit.panel("gap"):
        kit.panel_header("Valuation gap", f'{temperature["label"]} — {temperature["description"]}')
        kit.html(temperature_scale(valuation["valuation_gap_pct"], temperature["label"]))
        kit.html(f'<p class="kt-meta" style="margin-top:24px">Gap history · {window} · widest over 90 sessions {kit.pct(widest)}</p>')
        kit.chart(gap_history_figure(frame))


def render_drivers(snapshot: Dict[str, Any]) -> None:
    fundamentals = snapshot["fundamentals"]
    market = snapshot["market_data"]
    inventory = market["inventory_snapshot"]
    rows = []
    for parameter in fundamentals["parameters"]:
        digits = int(parameter.get("display_digits", 2))
        benchmark = "Rule-based" if parameter["benchmark_value"] is None else kit.num(parameter["benchmark_value"], digits)
        deviation = (
            kit.pct(parameter["deviation_pct"]) if parameter["deviation_pct"] is not None else kit.score(parameter["weighted_contribution"])
        )
        if parameter["key"] == "inventories":
            observed = inventory.get("last_updated")
        else:
            observed = market.get(DRIVER_SERIES.get(parameter["key"], ""), {}).get("last_timestamp")
        details = escape(parameter["rationale"])
        if parameter.get("source_note"):
            details += f'<br><span class="kt-muted">Source: {escape(parameter["source_note"])}</span>'
        rows.append(
            (
                f'<span class="strong">{parameter["name"]}</span><span class="sub">{parameter["unit"]}</span>'
                f"<details><summary>Rationale</summary><div>{details}</div></details>",
                f'{parameter["weight_pct"]:g}%',
                kit.num(parameter["current_value"], digits),
                f'{benchmark}<span class="sub">{parameter["benchmark_label"]}</span>',
                deviation,
                f'<span class="kt-{kit.tone(parameter["score"])}">{kit.score(parameter["score"])}</span>',
                kit.badge(parameter["bias"], SIGNAL_TONE.get(parameter["bias"], "")),
                kit.date(observed),
            )
        )
    with kit.panel("drivers"):
        kit.panel_header(f'{fundamentals["parameter_count"]} weighted drivers', "Each scored −2 to +2 · composite range −100 to +100")
        kit.table(["Driver", "Weight", "Current", "Benchmark", "Deviation", "Score", "Bias", "As of"], rows, numeric=[1, 2, 3, 4, 5, 7])


def render_regime(snapshot: Dict[str, Any]) -> None:
    valuation = snapshot["valuation"]
    technicals = snapshot["technicals"]
    demand = valuation["demand_destruction"]
    stagflation = valuation["stagflation_monitor"]
    rsi, macd, averages = technicals["rsi_14"], technicals["macd"], technicals["moving_averages"]

    left, right = st.columns(2, gap="medium")
    with left, kit.panel("overlays"):
        kit.panel_header("Regime overlays", "Applied to fair value")
        kit.table(
            None,
            [
                ("Demand destruction", kit.badge(demand["status_label"], RISK_TONE.get(demand["risk_level"], ""))),
                ("Stagflation monitor", kit.badge(stagflation["status_label"], RISK_TONE.get(stagflation["risk_level"], ""))),
                ("Distance to $120", threshold_distance(demand.get("distance_to_120"), 120)),
                ("Distance to $150", threshold_distance(demand.get("distance_to_150"), 150)),
                ("Demand discount", kit.pct(-demand["fair_value_discount_pct"])),
                ("Recession discount", kit.pct(-stagflation["fair_value_discount_pct"])),
                ("Overlay gap push", kit.pct(valuation["valuation_gap_pct"] - valuation["base_valuation_gap_pct"])),
                ("Base fair value (before overlays)", kit.money(valuation["base_estimated_fair_value"])),
                ("Volatility factor (OVX)", kit.num(valuation["volatility_factor"])),
            ],
            numeric=[1],
        )
        kit.notes(valuation.get("regime_notes", []))
    with right, kit.panel("technicals"):
        kit.panel_header("Technicals", "Context only — not a model input")
        kit.table(
            None,
            [
                ("RSI (14)", f'{kit.num(rsi["value"])} &nbsp;{kit.badge(rsi["status"], SIGNAL_TONE.get(rsi["status"], ""))}'),
                ("MACD", f'{kit.num(macd["line"], 3)} &nbsp;{kit.badge(macd["status"], SIGNAL_TONE.get(macd["status"], ""))}'),
                ("MACD signal / histogram", f'{kit.num(macd["signal"], 3)} / {kit.num(macd["histogram"], 3)}'),
                ("50-day SMA", kit.money(averages["sma_50"])),
                ("200-day SMA", kit.money(averages["sma_200"])),
                ("Price vs 50-day", f'<span class="kt-{kit.tone(averages["price_vs_sma_50_pct"])}">{kit.pct(averages["price_vs_sma_50_pct"])}</span>'),
                ("Price vs 200-day", f'<span class="kt-{kit.tone(averages["price_vs_sma_200_pct"])}">{kit.pct(averages["price_vs_sma_200_pct"])}</span>'),
            ],
            numeric=[1],
        )


def render_backtest(snapshot: Dict[str, Any]) -> None:
    summary = snapshot["backtest_summary"]
    rows = []
    for signal in summary["signal_order"]:
        stats = summary["signals"][signal]
        win = stats["win_rate_pct"]
        win_cls = "" if win is None else ("kt-up" if win > 50 else "kt-down" if win < 50 else "")
        rows.append(
            (
                f'<span class="strong">{signal}</span>',
                "Upside" if stats["expected_direction"] == "positive" else "Downside",
                str(stats["occurrence_count"]),
                f'<span class="kt-{kit.tone(stats["avg_5d_return_pct"])}">{kit.pct(stats["avg_5d_return_pct"])}</span>'
                f'<span class="sub">{stats["valid_5d_samples"]} windows</span>',
                f'<span class="kt-{kit.tone(stats["avg_10d_return_pct"])}">{kit.pct(stats["avg_10d_return_pct"])}</span>'
                f'<span class="sub">{stats["valid_10d_samples"]} windows</span>',
                f'<span class="{win_cls}">{"—" if win is None else f"{win:.1f}%"}</span>',
            )
        )
    with kit.panel("backtest"):
        kit.panel_header("Forward returns after each signal", "Historical validation over the last 90 sessions")
        kit.table(["Signal", "Expected reversion", "Signals", "Avg 5D return", "Avg 10D return", "Win rate"], rows, numeric=[2, 3, 4, 5])
        kit.html(f'<p class="kt-meta" style="margin-top:16px">{summary["win_rate_definition"]}</p>')


def render_methodology(snapshot: Dict[str, Any]) -> None:
    kit.steps(
        [
            ("Drivers", "Eight market and macro inputs are each scored from −2 to +2 and weighted into a composite score between −100 and +100."),
            ("Fair value", "<code>50D SMA × (1 + score / 100 × volatility factor)</code>, with the volatility factor derived from OVX."),
            ("Overlays", "Above $120 a demand-destruction overlay, and a stagflation monitor on inflation, credit and China, discount fair value."),
            ("Signal", "A gap above +10% reads Hot (above +20% Very Hot), below −10% Cold (below −20% Very Cold)."),
        ]
    )
    market = snapshot["market_data"]
    inventory = market["inventory_snapshot"]
    rows = [
        (name, market[key]["ticker"], f'{kit.num(market[key]["current_price"])} <span class="kt-muted">{market[key]["currency"] or ""}</span>',
         kit.date(market[key]["last_timestamp"]))
        for name, key in DATA_SOURCES
    ]
    rows.append(("US crude inventories", inventory["source"], f'{kit.num(inventory["current_inventory_million_bbl"])} <span class="kt-muted">mn bbl</span>',
                 kit.date(inventory["last_updated"])))
    kit.section("Data sources", "Yahoo Finance prices may be delayed")
    with kit.panel("sources"):
        kit.table(["Input", "Series", "Latest value", "As of"], rows, numeric=[2, 3])
        kit.notes(snapshot["meta"]["notes"])


kit.page_header(
    "Commodities · Energy",
    "WTI Crude Oil Valuation",
    "Estimated fair value for WTI crude from eight weighted drivers, compared with the observed market price.",
)


@st.fragment(run_every=REFRESH_SECONDS)
def dashboard() -> None:
    try:
        with st.spinner("Loading market data…"):
            snapshot = get_snapshot()
    except Exception as exc:  # pragma: no cover - interactive runtime path
        kit.section("Data unavailable")
        kit.html(f'<p class="kt-meta">{escape(str(exc))}</p>')
        if st.button("Try again", type="secondary"):
            get_snapshot.clear()
            st.rerun(scope="fragment")
        return

    asset = snapshot["asset"]
    valuation = snapshot["valuation"]
    temperature = valuation["temperature"]
    temperature_tone = TEMPERATURE_TONE.get(temperature["label"], "")

    with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
        kit.html(
            f'<div class="kt-status" style="margin-top:0"><i></i>Price as of {kit.date(asset["last_updated"])} (Yahoo Finance, may be delayed)'
            f' · model run {kit.timestamp(snapshot["meta"]["generated_at"])}</div>'
        )
        if st.button("Refresh", type="tertiary", icon=":material/refresh:"):
            get_snapshot.clear()
            st.rerun(scope="fragment")

    kit.metrics(
        [
            ("WTI market price", kit.money(asset["current_price"]), f'{asset["ticker"]} · $/bbl', "blue"),
            ("Estimated fair value", kit.money(valuation["estimated_fair_value"]), "$/bbl after overlays", "mint"),
            ("Valuation gap", kit.pct(valuation["valuation_gap_pct"]), "market vs fair value", temperature_tone),
            ("Signal", temperature["label"], temperature["description"], temperature_tone),
            ("Composite score", kit.score(snapshot["fundamentals"]["normalized_score"]), "range −100 to +100"),
        ]
    )

    history = snapshot["history"]
    with kit.panel("price"):
        with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
            kit.panel_header("Market price vs. estimated fair value", "Daily close · last 90 sessions")
            window = kit.range_selector(list(RANGES), key="crude_range", default="All")
        if history:
            frame = history_frame(history, window)
            kit.chart(price_vs_fair_value_figure(frame))
        else:
            kit.html('<p class="kt-meta">Historical model data unavailable.</p>')

    tab = kit.subnav(["Valuation gap", "Drivers", "Regime & technicals", "Backtest", "Methodology & data"], key="crude_tab")
    if tab == "Valuation gap" and history:
        render_valuation_gap(snapshot, frame, window)
    elif tab == "Drivers":
        render_drivers(snapshot)
    elif tab == "Regime & technicals":
        render_regime(snapshot)
    elif tab == "Backtest":
        render_backtest(snapshot)
    elif tab == "Methodology & data":
        render_methodology(snapshot)


dashboard()
