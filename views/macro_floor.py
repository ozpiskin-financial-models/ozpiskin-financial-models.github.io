"""
Macro Floor — Streamlit page.

Every number comes from models/macro_floor_engine.py (the original model's
calculation code). This file only lays the results out with the shared design
system in ui/kit.py.
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

ACTION_TONE = {"BUY": "gold", "SELL": "up", "STOP": "down", "TIME": ""}

kit.page_header(
    "Equities · US & BIST",
    "Macro Floor",
    "Buys crisis bottoms once forced selling below sovereign-yield floors is exhausted.",
)

with st.spinner("Loading macro feed and portfolio…"):
    macros = fetch_macros()
    pf = load_pf(macros)

md = macros["margin_discount"]
tr10 = macros["tr_10y"]

hv = sum(h["qty"] * (deep_analyze(t, tr10, md) or {}).get("price", h["cost"]) for t, h in pf.get("holdings", {}).items())
cash = pf.get("cash", 100_000)
total_eq = cash + hv
total_pnl = total_eq - 100_000
pnl_pct = total_pnl / 100_000 * 100
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

pnl_tone = kit.tone(total_pnl)
kit.kpi_strip(
    [
        ("Fund value", f"${total_eq:,.0f}", f"{kit.signed_money(total_pnl)} · {pnl_pct:+.1f}%", pnl_tone),
        ("Cash", f"${cash:,.0f}", f"{cash / total_eq * 100:.0f}% of fund"),
        ("Open positions", str(len(pf.get("holdings", {}))), f"${hv:,.0f} invested"),
        ("Win rate", wr, f"{n_wins} / {n_trades} trades"),
        ("Max drawdown", f"{pf.get('max_dd', 0):.1f}%", "peak to trough"),
        ("Sharpe", sharpe_val, "annualised"),
    ]
)

with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
    kit.html(f'<span class="kt-meta">Paper fund since {inception} · $100,000 start · engine v4.1</span>')
    with st.popover("Parameters", type="tertiary", icon=":material/tune:"):
        pos_pct = st.slider("Position size", 5, 50, 25, format="%d%%", key="mf_pos") / 100
        trail_stop = st.slider("Trailing stop", 5, 25, 12, format="%d%%", key="mf_trail") / 100
        time_stop = st.slider("Time stop", 30, 365, 90, format="%d days", key="mf_time")
        universe = st.text_area("Universe", ", ".join(DEFAULT_TICKERS), height=120, key="mf_universe")
        if st.button("Reset & rebuild portfolio", type="secondary", width="stretch"):
            with st.spinner("Rebuilding the 5-year simulation…"):
                save_pf(_run_full_backtest(macros))
            st.session_state.pop("mf_scan", None)
            st.rerun()

tickers = [t.strip().upper() for t in universe.split(",") if t.strip()]


def equity_figure() -> go.Figure:
    frame = pd.DataFrame(list(eq_curve.items()), columns=["Date", "Equity"])
    frame["Date"] = pd.to_datetime(frame["Date"])
    peak = np.maximum.accumulate(frame["Equity"].values)
    frame["Drawdown"] = (frame["Equity"].values - peak) / peak * 100

    figure = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.74, 0.26], vertical_spacing=0.05)
    figure.add_trace(
        go.Scatter(x=frame["Date"], y=frame["Equity"], name="Fund value", mode="lines", line={"color": kit.GOLD, "width": 1.5},
                   hovertemplate="$%{y:,.0f}"),
        row=1, col=1,
    )
    figure.add_trace(
        go.Scatter(x=frame["Date"], y=frame["Drawdown"], name="Drawdown", mode="lines", line={"color": kit.DOWN, "width": 1},
                   fill="tozeroy", fillcolor="rgba(226, 109, 90, 0.10)", hovertemplate="%{y:.1f}%"),
        row=2, col=1,
    )
    kit.style_figure(figure, 440)
    low, high = float(frame["Equity"].min()), float(frame["Equity"].max())
    figure.update_yaxes(tickprefix="$", tickformat=",.0f", range=[low * 0.94, high * 1.03], row=1, col=1)
    figure.update_xaxes(showticklabels=False, row=1, col=1)
    figure.update_yaxes(ticksuffix="%", row=2, col=1)
    return figure


def render_overview() -> None:
    kit.section("Macro environment", "Live")
    kit.kpi_strip(
        [
            ("US 10Y treasury", f"{macros['us_10y'] * 100:.2f}%", "Yahoo Finance"),
            ("TR 10Y sovereign", f"{macros['tr_10y'] * 100:.2f}%", "TradingView"),
            ("Total borrowing cost", f"{macros['tbc'] * 100:.1f}%", "US 10Y + risk premia"),
            ("Margin-call discount", f"{macros['margin_discount'] * 100:.1f}%", "below bond floor"),
        ],
        small=True,
    )
    if eq_curve:
        kit.section("Fund value & drawdown", f"Since {inception}")
        kit.chart(equity_figure())

    allocation = [("Cash", cash)] + [(t, h["qty"] * h["cost"]) for t, h in pf.get("holdings", {}).items()]
    total_alloc = sum(value for _, value in allocation) or 1
    kit.section("Allocation", "At cost")
    kit.table(
        ["Asset", "Value", "Weight"],
        [(f'<span class="strong">{name}</span>', f"${value:,.0f}", f"{value / total_alloc * 100:.1f}%") for name, value in allocation],
        numeric=[1, 2],
    )


def proximity_cell(proximity: float, color: str) -> str:
    return (
        '<div style="display:flex;align-items:center;justify-content:flex-end;gap:10px">'
        f"<span>{proximity:.0f}</span>"
        f'<div style="width:72px;height:2px;background:#1d1d1d"><div style="width:{proximity}%;height:2px;background:{color}"></div></div></div>'
    )


def render_radar() -> None:
    with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
        run = st.button("Run scan", type="primary", icon=":material/radar:")
        kit.html(f'<span class="kt-meta">{len(tickers)} instruments · opens and closes paper positions on signal</span>')

    if run:
        progress = st.progress(0.0, text="Scanning…")
        results, actions = run_scan(
            pf, tickers, tr10, md, pos_pct, trail_stop, time_stop,
            on_progress=lambda share, ticker: progress.progress(share, text=f"Analysing {ticker}"),
        )
        st.session_state["mf_scan"] = {"results": results, "actions": actions, "at": datetime.now().strftime("%d %b %Y, %H:%M")}
        st.rerun()

    scan = st.session_state.get("mf_scan")
    if not scan:
        kit.section("Signal proximity")
        kit.html('<p class="kt-meta">Run a scan to rank every instrument by its distance to the crisis buy zone.</p>')
        return

    if scan["actions"]:
        kit.section("Executions", scan["at"])
        kit.table(
            ["Action", "Instrument", "Price", "P&L"],
            [
                (kit.badge(kind, ACTION_TONE.get(kind, "")), f'<span class="strong">{ticker}</span>', f"${price:,.2f}",
                 "—" if kind == "BUY" else f'<span class="kt-{kit.tone(pnl)}">{kit.signed_money(pnl)}</span>')
                for kind, ticker, price, pnl in scan["actions"]
            ],
            numeric=[2, 3],
        )

    rows = []
    for rank, r in enumerate(scan["results"], start=1):
        prox = r["proximity"]
        if prox >= 80:
            status, status_tone, color = ("Active" if r["signal"] else "Alert"), "up", kit.UP
        elif prox >= 50:
            status, status_tone, color = "Watchlist", "gold", kit.GOLD
        elif prox >= 25:
            status, status_tone, color = "Distant", "", kit.MUTED
        else:
            status, status_tone, color = "Far", "", "#3a3a3a"
        rows.append(
            (
                f'<span class="kt-muted">{rank:02d}</span>',
                f'<span class="strong">{r["ticker"]}</span>',
                f"${r['price']:.2f}",
                f"${r['bond_fv']:.2f}",
                f"${r['bank_bot']:.2f}",
                f'<span class="kt-{"up" if r["dist_bond"] < 0 else "down"}">{r["dist_bond"]:+.1f}%</span>',
                f"{r['from_high']:.1f}%",
                f"{r['vol_20d']}%",
                proximity_cell(prox, color),
                kit.badge(status, status_tone),
            )
        )
    kit.section("Signal proximity", f"Scanned {scan['at']}")
    kit.table(
        ["#", "Instrument", "Price", "Bond floor", "Bank bottom", "vs floor", "52W high", "Vol 20D", "Proximity", "Status"],
        rows,
        numeric=[2, 3, 4, 5, 6, 7, 8],
    )


def render_portfolio() -> None:
    holdings = pf.get("holdings", {})
    kit.section("Open positions", f"{len(holdings):02d}")
    if not holdings:
        kit.html('<p class="kt-meta">No open positions — waiting for crisis entry conditions.</p>')
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
                    f"${h['cost']:.2f}",
                    f"${h['target']:.2f}",
                    f"${lp:.2f}",
                    f'<span class="kt-{kit.tone(u)}">{kit.signed_money(u)} · {pc:+.1f}%</span>',
                    str(days),
                )
            )
        kit.table(["Instrument", "Entry", "Target", "Last", "Unrealised P&L", "Days"], rows, numeric=[1, 2, 3, 4, 5])

    kit.section("Trade history", f"{len(hist)} entries")
    if not hist:
        kit.html('<p class="kt-meta">No trades recorded yet.</p>')
        return
    rows = []
    for entry in reversed(hist):
        parts = [p.strip() for p in entry.split("|")]
        if len(parts) >= 3:
            details = " · ".join(parts[3:]).replace("$+", "+$").replace("$-", "−$")
            rows.append(
                (f'<span class="kt-muted">{parts[0]}</span>', kit.badge(parts[1], ACTION_TONE.get(parts[1], "")),
                 f'<span class="strong">{parts[2]}</span>', details)
            )
    kit.table(["Date", "Action", "Instrument", "Details"], rows, max_height=520)


def render_methodology() -> None:
    kit.steps(
        [
            ("Bond floor", "<code>52-week low × (1 + live TR 10Y yield)</code> — the price at which a stock only matches the risk-free sovereign return."),
            ("Bank bottom", "<code>Bond floor × (1 − margin-call discount)</code>, with the discount derived live from the TR–US 10Y spread."),
            ("Entry", "Buy only below the bank bottom after two consecutive exhaustion candles: high above the open, close below both the open and the prior close."),
            ("Exit", "Target is the larger of the bond floor and entry +25%, with a 12% trailing stop and a time stop (90 days by default)."),
        ]
    )


tab = kit.subnav(["Overview", "Signal Radar", "Portfolio", "Methodology"], key="macro_tab")
if tab == "Overview":
    render_overview()
elif tab == "Signal Radar":
    render_radar()
elif tab == "Portfolio":
    render_portfolio()
else:
    render_methodology()
