"""
Macro Floor — Streamlit page.

Every number comes from models/macro_floor_engine.py (the original model's
calculation code, unchanged). This file only lays the results out with the
shared design system in ui/kit.py. The universe table is read-only; only the
"Run paper scan" button opens or closes simulated positions, as before.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from models.macro_floor_engine import DEFAULT_TICKERS, _run_full_backtest, deep_analyze, fetch_macros, load_pf, run_scan, save_pf
from ui import kit

START_CAPITAL = 100_000
ACTION_TONE = {"BUY": "blue", "SELL": "up", "STOP": "down", "TIME": "warn"}
RANGES = {"1Y": pd.DateOffset(years=1), "3Y": pd.DateOffset(years=3), "All": None}


CUR = "₺"  # BIST-only universe: every price, position and P&L is in Turkish lira.


def price(value: float) -> str:
    return f"{CUR}{value:,.2f}"


def proximity_state(proximity: float, signal: bool) -> tuple[str, str, str]:
    """Same bands as the original Signal Radar: (label, badge tone, bar colour)."""
    if proximity >= 80:
        return ("Active signal" if signal else "Alert"), "up", kit.UP
    if proximity >= 50:
        return "Watchlist", "warn", kit.WARN
    if proximity >= 25:
        return "Distant", "", kit.MUTED
    return "Far", "", kit.BORDER


def proximity_cell(proximity: float, color: str) -> str:
    return (
        '<div style="display:flex;align-items:center;justify-content:flex-end;gap:8px">'
        f"<span>{proximity:.0f}</span>"
        f'<div style="width:64px;height:4px;border-radius:2px;background:var(--surface-3)">'
        f'<div style="width:{proximity}%;height:4px;border-radius:2px;background:{color}"></div></div></div>'
    )


kit.page_header(
    "Borsa Istanbul · Macro",
    "Macro Floor",
    "Values BIST stocks against a floor set by the Turkish 10-year bond yield and simulates entries only after forced selling below it is exhausted.",
)

with st.spinner("Loading macro inputs and the simulated portfolio…"):
    macros = fetch_macros()
    pf = load_pf(macros)

md = macros["margin_discount"]
tr10 = macros["tr_10y"]

hv = sum(h["qty"] * (deep_analyze(t, tr10, md) or {}).get("price", h["cost"]) for t, h in pf.get("holdings", {}).items())
cash = pf.get("cash", START_CAPITAL)
total_eq = cash + hv
total_pnl = total_eq - START_CAPITAL
pnl_pct = total_pnl / START_CAPITAL * 100
inception = pf.get("inception", "2021-10-01")

hist = pf.get("history", [])
exits = [h for h in hist if "| SELL |" in h or "| STOP |" in h or "| TIME |" in h]
n_trades = len(exits)
n_wins = len([h for h in exits if "P&L: $+" in h])
wr = f"{n_wins / n_trades * 100:.0f}%" if n_trades else "—"

eq_curve = pf.get("equity_curve", {})
sharpe_val = "—"
if eq_curve and len(eq_curve) > 30:
    eqvals = list(eq_curve.values())
    rets = np.diff(eqvals) / eqvals[:-1]
    if np.std(rets) > 0:
        sharpe_val = f"{(np.mean(rets) / np.std(rets)) * np.sqrt(252):.2f}"

with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
    kit.html(
        f'<div class="kt-status" style="margin-top:0"><i></i>Simulated paper portfolio · backtest from {inception}, '
        "then updated by paper scans · not a live strategy</div>"
    )
    with st.popover("Parameters", type="tertiary", icon=":material/tune:"):
        pos_pct = st.slider("Position size", 5, 50, 25, format="%d%%", key="mf_pos") / 100
        trail_stop = st.slider("Trailing stop", 5, 25, 12, format="%d%%", key="mf_trail") / 100
        time_stop = st.slider("Time stop", 30, 365, 90, format="%d days", key="mf_time")
        universe = st.text_area("Universe", ", ".join(DEFAULT_TICKERS), height=120, key="mf_universe")
        st.caption("Applied to paper scans. The 5-year rebuild uses the model's fixed backtest settings.")
        if st.button("Reset & rebuild portfolio", type="secondary", width="stretch"):
            with st.spinner("Rebuilding the 5-year simulation…"):
                save_pf(_run_full_backtest(macros))
            st.session_state.pop("mf_scan", None)
            st.rerun()

tickers = [t.strip().upper() for t in universe.split(",") if t.strip()]

kit.metrics(
    [
        ("Simulated value", f"{CUR}{total_eq:,.0f}", f"from {CUR}{START_CAPITAL:,.0f}", kit.tone(total_pnl)),
        ("Total return", f"{pnl_pct:+.1f}%", kit.signed_money(total_pnl, currency=CUR), kit.tone(total_pnl)),
        ("Max drawdown", f"{pf.get('max_dd', 0):.1f}%", "peak to trough"),
        ("Win rate", wr, f"{n_wins} of {n_trades} closed trades"),
        ("Sharpe", sharpe_val, "annualised, daily"),
        ("Open positions", str(len(pf.get("holdings", {}))), f"{CUR}{hv:,.0f} invested"),
    ]
)

kit.section("Live macro inputs", "Floors are recomputed from these")
kit.metrics(
    [
        ("TR 10Y sovereign", f"{macros['tr_10y'] * 100:.2f}%", "TradingView · bond-floor yield", "mint"),
        ("US 10Y treasury", f"{macros['us_10y'] * 100:.2f}%", "Yahoo Finance ^TNX"),
        ("Country risk spread", f"{macros['crp'] * 100:.2f}%", "TR 10Y − US 10Y"),
        ("Margin-call discount", f"{macros['margin_discount'] * 100:.1f}%", "bank bottom below floor"),
    ],
    compact=True,
)


def equity_figure(window: str) -> go.Figure:
    frame = pd.DataFrame(list(eq_curve.items()), columns=["Date", "Equity"])
    frame["Date"] = pd.to_datetime(frame["Date"])
    peak = np.maximum.accumulate(frame["Equity"].values)
    frame["Drawdown"] = (frame["Equity"].values - peak) / peak * 100
    offset = RANGES[window]
    if offset is not None:
        frame = frame[frame["Date"] >= frame["Date"].max() - offset]

    figure = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.74, 0.26], vertical_spacing=0.06)
    figure.add_trace(
        go.Scatter(x=frame["Date"], y=frame["Equity"], name="Simulated portfolio value", mode="lines",
                   line={"color": kit.MINT, "width": 2}, hovertemplate="₺%{y:,.0f}"),
        row=1, col=1,
    )
    figure.add_hline(y=START_CAPITAL, line={"color": kit.BORDER, "width": 1, "dash": "dot"}, row=1, col=1)
    figure.add_trace(
        go.Scatter(x=frame["Date"], y=frame["Drawdown"], name="Drawdown from peak", mode="lines", line={"color": kit.DOWN, "width": 1.5},
                   fill="tozeroy", fillcolor="rgba(248, 113, 113, 0.10)", hovertemplate="%{y:.1f}%"),
        row=2, col=1,
    )
    kit.style_figure(figure, 440)
    low, high = float(frame["Equity"].min()), float(frame["Equity"].max())
    figure.update_yaxes(tickprefix=CUR, tickformat=",.0f", range=[min(low, START_CAPITAL) * 0.94, high * 1.03], row=1, col=1)
    figure.update_yaxes(ticksuffix="%", row=2, col=1)
    figure.update_xaxes(showticklabels=False, row=1, col=1)
    return figure


with kit.panel("equity"):
    with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
        kit.panel_header("Simulated portfolio value & drawdown", f"Daily · since {inception} · dotted line = ₺100,000 start")
        window = kit.range_selector(list(RANGES), key="macro_range", default="All")
    if eq_curve:
        kit.chart(equity_figure(window))
    else:
        kit.html('<p class="kt-meta">No equity history yet — rebuild the portfolio from Parameters.</p>')


def render_universe() -> None:
    with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
        kit.html(f'<p class="kt-meta">{len(tickers)} Borsa Istanbul instruments · all prices and P&amp;L in TRY</p>')
        run = st.button("Run paper scan", type="primary", icon=":material/radar:",
                        help="Applies the entry and exit rules to every instrument and updates the simulated portfolio.")

    if run:
        progress = st.progress(0.0, text="Scanning…")
        results, actions = run_scan(
            pf, tickers, tr10, md, pos_pct, trail_stop, time_stop,
            on_progress=lambda share, ticker: progress.progress(share, text=f"Analysing {ticker}"),
        )
        st.session_state["mf_scan"] = {"actions": actions, "at": datetime.now().strftime("%d %b %Y, %H:%M")}
        st.rerun()

    scan = st.session_state.get("mf_scan")
    if scan and scan["actions"]:
        with kit.panel("executions"):
            kit.panel_header("Paper executions from the last scan", scan["at"])
            kit.table(
                ["Action", "Instrument", "Price", "P&L"],
                [
                    (kit.badge(kind, ACTION_TONE.get(kind, "")), f'<span class="strong">{ticker}</span>', price(px),
                     "—" if kind == "BUY" else f'<span class="kt-{kit.tone(pnl)}">{kit.signed_money(pnl, currency=CUR)}</span>')
                    for kind, ticker, px, pnl in scan["actions"]
                ],
                numeric=[2, 3],
            )
    elif scan:
        kit.html(f'<p class="kt-meta">Last paper scan {scan["at"]}: no entries or exits triggered.</p>')

    with st.spinner("Computing floors for the universe…"):
        rows_data = []
        for ticker in tickers:
            analysis = deep_analyze(ticker, tr10, md)
            if analysis:
                rows_data.append(analysis | {"ticker": ticker})
    rows_data.sort(key=lambda r: r["proximity"], reverse=True)

    holdings = pf.get("holdings", {})
    rows = []
    for r in rows_data:
        label, state_tone, color = proximity_state(r["proximity"], r["signal"])
        held = kit.badge("Held", "blue") if r["ticker"] in holdings else ""
        rows.append(
            (
                f'<span class="strong">{r["ticker"]}</span> {held}',
                price(r["price"]),
                price(r["bond_fv"]),
                price(r["bank_bot"]),
                f'<span class="kt-{"up" if r["dist_bond"] < 0 else "down"}">{r["dist_bond"]:+.1f}%</span>',
                f"{r['from_high']:.1f}%",
                f"{r['vol_20d']}%",
                proximity_cell(r["proximity"], color),
                kit.badge(label, state_tone),
            )
        )
    with kit.panel("universe"):
        kit.panel_header("Instrument universe", f"{len(rows)} instruments · ranked by proximity to the buy zone (0–100)")
        kit.table(
            ["Instrument", "Price", "Bond floor", "Bank bottom", "vs floor", "vs 52W high", "Vol 20D", "Proximity", "State"],
            rows,
            numeric=[1, 2, 3, 4, 5, 6, 7],
        )
        kit.html('<p class="kt-meta" style="margin-top:16px">Read-only view: floors and states are recomputed from the latest prices '
                 "(cached for 15 minutes). Only “Run paper scan” changes the simulated portfolio.</p>")


def render_positions() -> None:
    holdings = pf.get("holdings", {})
    with kit.panel("positions"):
        kit.panel_header("Open positions", f"{len(holdings)} held")
        if not holdings:
            kit.html('<p class="kt-meta" style="margin-top:8px">No open positions — waiting for crisis entry conditions.</p>')
        else:
            rows = []
            for t, h in holdings.items():
                lp = (deep_analyze(t, tr10, md) or {}).get("price", h["cost"])
                u = (lp - h["cost"]) * h["qty"]
                pc = (lp / h["cost"] - 1) * 100
                bd = h.get("buy_date", "")[:10]
                days = (datetime.now() - datetime.strptime(bd, "%Y-%m-%d")).days if len(bd) >= 10 else 0
                rows.append(
                    (
                        f'<span class="strong">{t}</span>',
                        price(h["cost"]),
                        price(h["target"]),
                        price(lp),
                        f'<span class="kt-{kit.tone(u)}">{kit.signed_money(u, currency=CUR)}</span><span class="sub">{pc:+.1f}%</span>',
                        str(days),
                    )
                )
            kit.table(["Instrument", "Entry", "Target", "Last", "Unrealised P&L", "Days held"], rows, numeric=[1, 2, 3, 4, 5])

    allocation = [("Cash", cash)] + [(t, h["qty"] * h["cost"]) for t, h in holdings.items()]
    total_alloc = sum(value for _, value in allocation) or 1
    left, right = st.columns([1, 2], gap="medium")
    with left, kit.panel("allocation"):
        kit.panel_header("Allocation", "At cost")
        kit.table(
            None,
            [(f'<span class="strong">{name}</span>', f"{CUR}{value:,.0f}", f"{value / total_alloc * 100:.1f}%") for name, value in allocation],
            numeric=[1, 2],
        )
    with right, kit.panel("trades"):
        kit.panel_header("Trade history", f"{len(hist)} simulated entries")
        rows = []
        for entry in reversed(hist):
            parts = [p.strip() for p in entry.split("|")]
            if len(parts) >= 3:
                details = " · ".join(parts[3:]).replace("$+", f"+{CUR}").replace("$-", f"−{CUR}").replace("$", CUR)
                rows.append((f'<span class="kt-muted">{parts[0]}</span>', kit.badge(parts[1], ACTION_TONE.get(parts[1], "")),
                             f'<span class="strong">{parts[2]}</span>', details))
        if rows:
            kit.table(["Date", "Action", "Instrument", "Details"], rows, max_height=480)
        else:
            kit.html('<p class="kt-meta" style="margin-top:8px">No trades recorded yet.</p>')


def render_methodology() -> None:
    kit.steps(
        [
            ("Bond floor", "<code>52-week low × (1 + TR 10Y yield)</code> — the price at which a stock only matches the risk-free sovereign return."),
            ("Bank bottom", "<code>Bond floor × (1 − margin-call discount)</code>, with the discount <code>US 10Y + 0.35 × (TR 10Y − US 10Y)</code>."),
            ("Entry", "Below both floors, after two consecutive exhaustion candles: high above the open, close below the open and the prior close."),
            ("Exit", "Target is the larger of the bond floor and entry +25%; trailing stop and time stop as set in Parameters (12%, 90 days by default)."),
        ]
    )
    kit.section("Inputs & assumptions")
    with kit.panel("inputs"):
        kit.table(
            ["Input", "Source", "Note"],
            [
                ("Stock prices", "Yahoo Finance", "Daily bars; 1 year for live floors, 5 years for the backtest."),
                ("US 10Y yield", "Yahoo Finance ^TNX", "Falls back to 4.5% if the feed is unavailable."),
                ("TR 10Y yield", "TradingView TVC:TR10Y", "Falls back to 32.0% if the feed is unavailable."),
                ("Portfolio state", "MongoDB Atlas", "Session-only if the database is unreachable."),
                ("Backtest", "Model engine", "₺100,000 start, 25% position size, 12% trailing stop, 90-day time stop."),
                ("Universe & currency", "Model engine", "8 Borsa Istanbul stocks; every price, position and P&L is in Turkish lira (TRY)."),
            ],
        )


tab = kit.subnav(["Universe & signals", "Positions & trades", "Methodology"], key="macro_tab")
if tab == "Universe & signals":
    render_universe()
elif tab == "Positions & trades":
    render_positions()
else:
    render_methodology()
