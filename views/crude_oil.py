"""
WTI Crude Oil Valuation — Streamlit page.

Every number comes from models/crude_oil_engine.py (the original model's
calculation code). This file only lays the results out with the shared design
system in ui/kit.py.
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

TEMPERATURE_TONE = {"Very Hot": "hot", "Hot": "hot", "Neutral": "", "Cold": "cold", "Very Cold": "cold"}
RISK_TONE = {"low": "", "elevated": "gold", "high": "down", "extreme": "down", "unknown": ""}
SIGNAL_TONE = {"bullish": "up", "bearish": "down", "oversold": "up", "overbought": "down", "neutral": ""}

# Valuation-gap zones from map_temperature() in the engine, drawn on a -30%..+30% scale.
SCALE_MIN, SCALE_MAX = -30.0, 30.0
SCALE_ZONES = [
    ("Very Cold", -30.0, -20.0, "#8fb4d8"),
    ("Cold", -20.0, -10.0, "rgba(143, 180, 216, 0.45)"),
    ("Neutral", -10.0, 10.0, "#2b2b2b"),
    ("Hot", 10.0, 20.0, "rgba(224, 138, 95, 0.5)"),
    ("Very Hot", 20.0, 30.0, "#e08a5f"),
]

SCALE_CSS = """
<style>
.co-scale { margin: 46px 0 10px; }
.co-track { position: relative; display: flex; height: 2px; }
.co-zone { height: 2px; }
.co-marker { position: absolute; top: -34px; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; }
.co-marker span { font-family: var(--mono); font-size: 13px; color: var(--text); margin-bottom: 6px; white-space: nowrap; }
.co-tick { display: block; width: 1px; height: 40px; background: var(--gold); flex: none; }
.co-labels { display: flex; margin-top: 18px; }
.co-labels div { font-size: 10.5px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--muted); text-align: center; }
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


def threshold_distance(distance: float | None, threshold: int) -> str:
    if distance is None:
        return "—"
    side = "above" if distance >= 0 else "below"
    return f'{kit.money(abs(distance))} <span class="kt-muted">{side} ${threshold}</span>'


def price_vs_fair_value_figure(history: List[Dict[str, Any]]) -> go.Figure:
    frame = pd.DataFrame(history)
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(x=frame["date"], y=frame["actual_price"], name="WTI", mode="lines",
                   line={"color": kit.TEXT, "width": 1.6}, hovertemplate="$%{y:.2f}")
    )
    figure.add_trace(
        go.Scatter(x=frame["date"], y=frame["fair_value"], name="Fair value", mode="lines",
                   line={"color": kit.GOLD, "width": 1.4, "dash": "dot"}, hovertemplate="$%{y:.2f}")
    )
    kit.style_figure(figure, 380)
    figure.update_yaxes(tickprefix="$")
    return figure


def gap_history_figure(history: List[Dict[str, Any]]) -> go.Figure:
    frame = pd.DataFrame(history)
    figure = go.Figure()
    top = max(25.0, float(frame["valuation_gap_pct"].max()) + 5)
    bottom = min(-25.0, float(frame["valuation_gap_pct"].min()) - 5)
    figure.add_hrect(y0=10, y1=top, fillcolor="rgba(224, 138, 95, 0.06)", line_width=0)
    figure.add_hrect(y0=bottom, y1=-10, fillcolor="rgba(143, 180, 216, 0.06)", line_width=0)
    for level in (-10, 10):
        figure.add_hline(y=level, line={"color": "#2b2b2b", "width": 1, "dash": "dot"})
    figure.add_hline(y=0, line={"color": "#2b2b2b", "width": 1})
    figure.add_trace(
        go.Scatter(x=frame["date"], y=frame["valuation_gap_pct"], name="Valuation gap", mode="lines",
                   line={"color": kit.TEXT, "width": 1.6}, customdata=frame["temperature_label"],
                   hovertemplate="%{y:.2f}%  ·  %{customdata}")
    )
    kit.style_figure(figure, 320)
    figure.update_layout(showlegend=False)
    figure.update_yaxes(ticksuffix="%", range=[bottom, top])
    return figure


def render_overview(snapshot: Dict[str, Any]) -> None:
    valuation = snapshot["valuation"]
    technicals = snapshot["technicals"]
    demand = valuation["demand_destruction"]
    stagflation = valuation["stagflation_monitor"]
    temperature = valuation["temperature"]

    kit.section("Valuation gap", f'{temperature["label"]} · {temperature["description"]}')
    kit.html(temperature_scale(valuation["valuation_gap_pct"], temperature["label"]))

    left, right = st.columns(2, gap="large")
    with left:
        kit.section("Regime overlays")
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
                ("Volatility factor (OVX)", kit.num(valuation["volatility_factor"])),
            ],
            numeric=[1],
        )
        kit.notes(valuation.get("regime_notes", []))
    with right:
        rsi, macd, averages = technicals["rsi_14"], technicals["macd"], technicals["moving_averages"]
        kit.section("Technicals")
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


def render_history(snapshot: Dict[str, Any]) -> None:
    history = snapshot["history"]
    if not history:
        kit.section("History")
        kit.html('<p class="kt-meta">Historical model data unavailable.</p>')
        return
    latest = history[-1]["valuation_gap_pct"]
    widest = max(history, key=lambda row: abs(row["valuation_gap_pct"]))["valuation_gap_pct"]
    kit.section("Price vs. fair value", "Last 90 days")
    kit.chart(price_vs_fair_value_figure(history))
    kit.section("Valuation gap", f"Latest {kit.pct(latest)} · Widest {kit.pct(widest)}")
    kit.chart(gap_history_figure(history))


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
                f'<span class="kt-{kit.tone(stats["avg_5d_return_pct"])}">{kit.pct(stats["avg_5d_return_pct"])}</span>',
                f'<span class="kt-{kit.tone(stats["avg_10d_return_pct"])}">{kit.pct(stats["avg_10d_return_pct"])}</span>',
                f'<span class="{win_cls}">{"—" if win is None else f"{win:.1f}%"}</span>',
            )
        )
    kit.section("Forward returns by signal", "Last 90 days")
    kit.table(["Signal", "Expected reversion", "Signals", "Avg 5D", "Avg 10D", "Win rate"], rows, numeric=[2, 3, 4, 5])
    kit.html(f'<p class="kt-meta" style="margin-top:14px">{summary["win_rate_definition"]}</p>')


def render_drivers(snapshot: Dict[str, Any]) -> None:
    fundamentals = snapshot["fundamentals"]
    inventory = snapshot["market_data"]["inventory_snapshot"]
    rows = []
    for parameter in fundamentals["parameters"]:
        digits = int(parameter.get("display_digits", 2))
        benchmark = "Rule-based" if parameter["benchmark_value"] is None else kit.num(parameter["benchmark_value"], digits)
        deviation = (
            kit.pct(parameter["deviation_pct"]) if parameter["deviation_pct"] is not None else kit.score(parameter["weighted_contribution"])
        )
        rows.append(
            (
                f'<span class="strong" title="{escape(parameter["rationale"], quote=True)}">{parameter["name"]}</span>'
                f'<span class="sub">{parameter["unit"]}</span>',
                f'{parameter["weight_pct"]:g}%',
                kit.num(parameter["current_value"], digits),
                f'{benchmark}<span class="sub">{parameter["benchmark_label"]}</span>',
                deviation,
                f'<span class="kt-{kit.tone(parameter["score"])}">{kit.score(parameter["score"])}</span>',
                kit.badge(parameter["bias"], SIGNAL_TONE.get(parameter["bias"], "")),
            )
        )
    kit.section(f'{fundamentals["parameter_count"]} weighted drivers', "Score range −2 to +2")
    kit.table(["Driver", "Weight", "Current", "Benchmark", "Deviation", "Score", "Bias"], rows, numeric=[1, 2, 3, 4, 5])
    kit.html(f'<p class="kt-meta" style="margin-top:14px">Inventories: {inventory["source"]}. {inventory["note"]}</p>')


def render_methodology() -> None:
    kit.steps(
        [
            ("Drivers", "Eight market and macro inputs are each scored from −2 to +2 and weighted into a composite score between −100 and +100."),
            ("Fair value", "<code>50D SMA × (1 + score / 100 × volatility factor)</code>, where the volatility factor is derived from OVX."),
            ("Overlays", "Above $120 a demand-destruction overlay, and a stagflation monitor on inflation, credit and China, discount fair value."),
            ("Signal", "A gap above +10% reads Hot (+20% Very Hot), below −10% Cold (−20% Very Cold). Signals are backtested on 5- and 10-day returns."),
        ]
    )


kit.page_header(
    "Commodities · WTI crude",
    "Crude Oil Valuation",
    "Fair value from eight weighted macro drivers, mapped to a five-level temperature signal.",
)


@st.fragment(run_every=REFRESH_SECONDS)
def dashboard() -> None:
    try:
        with st.spinner("Loading live market data…"):
            snapshot = get_snapshot()
    except Exception as exc:  # pragma: no cover - interactive runtime path
        kit.section("Data unavailable")
        kit.html(f'<p class="kt-meta">{exc}</p>')
        if st.button("Try again", type="secondary"):
            get_snapshot.clear()
            st.rerun(scope="fragment")
        return

    asset = snapshot["asset"]
    valuation = snapshot["valuation"]
    temperature = valuation["temperature"]
    temperature_tone = TEMPERATURE_TONE.get(temperature["label"], "")

    kit.kpi_strip(
        [
            ("WTI spot", kit.money(asset["current_price"]), asset["ticker"]),
            ("Fair value", kit.money(valuation["estimated_fair_value"]), f'50D ref {kit.money(valuation["reference_sma_50"])}'),
            ("Valuation gap", kit.pct(valuation["valuation_gap_pct"]), "vs fair value", temperature_tone),
            ("Signal", temperature["label"], temperature["description"], temperature_tone),
            ("Composite score", kit.score(snapshot["fundamentals"]["normalized_score"]), "−100 to +100"),
        ]
    )

    with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
        kit.html(f'<span class="kt-meta">Updated {kit.timestamp(snapshot["meta"]["generated_at"])} · refreshes every 5 minutes</span>')
        if st.button("Refresh", type="tertiary", icon=":material/refresh:"):
            get_snapshot.clear()
            st.rerun(scope="fragment")

    tab = kit.subnav(["Overview", "History", "Backtest", "Drivers", "Methodology"], key="crude_tab")
    if tab == "Overview":
        render_overview(snapshot)
    elif tab == "History":
        render_history(snapshot)
    elif tab == "Backtest":
        render_backtest(snapshot)
    elif tab == "Drivers":
        render_drivers(snapshot)
    else:
        render_methodology()


dashboard()
