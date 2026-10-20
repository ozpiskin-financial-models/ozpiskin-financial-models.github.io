"""
Calculation engine for the Macro Floor Model.

Copied unchanged from live_uncle_tracker.py in the
Macro-Floor-Forced-Liquidation-Model repository (macro feed, MongoDB storage,
signal engine and 5-year backtest). run_scan() is the Signal Radar loop from
the same file, moved into a function so the page can call it. The default
universe is BIST-only (see DEFAULT_TICKERS); the calculations are unchanged.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
import pymongo
import requests
import streamlit as st
import urllib3
import yfinance as yf

urllib3.disable_warnings()


# ═══════════════════════════════════════════════════════════════════════════
# WATCHLIST
# ═══════════════════════════════════════════════════════════════════════════
# Borsa Istanbul stocks only: the floors use the Turkey 10Y yield, so the model
# stays in one market and one currency (TRY). The original universe also held
# 12 US stocks, which mixed USD and TRY prices in one portfolio.
DEFAULT_TICKERS = [
    "THYAO.IS", "AKBNK.IS", "ISCTR.IS", "TUPRS.IS", "GARAN.IS",
    "SISE.IS", "KCHOL.IS", "SAHOL.IS",
]


# ═══════════════════════════════════════════════════════════════════════════
# 100% DYNAMIC MACRO ENGINE
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800)
def fetch_macros() -> dict:
    # 100% Dynamic Engine (0 static configurations)
    us10 = 0.045
    tr10 = 0.320

    # 1. Fetch US 10Y Live (Yahoo Finance)
    try:
        d = yf.download("^TNX", period="5d", progress=False)
        if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
        if not d.empty: us10 = float(d["Close"].dropna().iloc[-1]) / 100.0
    except: pass

    # 2. Fetch Turkey 10Y Live (TradingView Scanner API - Unauthenticated)
    try:
        url = 'https://scanner.tradingview.com/global/scan'
        payload = {'symbols': {'tickers': ['TVC:TR10Y']}, 'columns': ['close']}
        r = requests.post(url, json=payload, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5, verify=False)
        if r.status_code == 200:
            data = r.json()
            if data.get('data'):
                tr10 = float(data['data'][0]['d'][0]) / 100.0
    except: pass

    # 3. Derive Implied Risk Metrics Dynamically
    crp = max(0.0, tr10 - us10)               # Implied Country Risk Premium (Spread)
    banking_margin = crp * 0.25               # Implied Banking Liquidity Premium
    tbc = us10 + crp + banking_margin         # True Dynamic Total Borrowing Cost
    
    # 4. Bank Bottom Penalty (Discount required to trigger margin liquidation capitulation)
    margin_discount = us10 + (crp * 0.35)

    return {
        "us_10y": us10,
        "tr_10y": tr10,
        "crp": crp,
        "tbc": tbc,
        "margin_discount": margin_discount
    }


# ═══════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_resource
def _mongo():
    try: uri = st.secrets["MONGO_URI"]
    except: uri = "mongodb://localhost:27017/"
    return pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)

def _col(): return _mongo()["macro_floor_db"]["portfolio"]

def load_pf(macros: dict) -> dict:
    try:
        doc = _col().find_one({"_id": "main_fund"})
        if doc: return doc
    except: pass
    if "pf" not in st.session_state:
        st.session_state.pf = _run_full_backtest(macros)
    return st.session_state.pf

def save_pf(pf: dict):
    try: _col().update_one({"_id": "main_fund"}, {"$set": pf}, upsert=True)
    except: st.session_state.pf = pf


# ═══════════════════════════════════════════════════════════════════════════
# SIGNAL ENGINE V4.1 — Dynamic Margin Bottom
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=900, show_spinner=False)
def deep_analyze(ticker: str, tr_10y: float, margin_discount: float) -> dict | None:
    """
    Computes bond floor and the dynamic margin bottom based on live spread discount.
    """
    try:
        df = yf.download(ticker, period="1y", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.reset_index().dropna(subset=["Close"])
        if len(df) < 20: return None

        close = df["Close"].values.astype(float)
        opn = df["Open"].values.astype(float)
        high = df["High"].values.astype(float)
        low = df["Low"].values.astype(float)
        vol = df["Volume"].values.astype(float) if "Volume" in df.columns else np.ones(len(close))

        cur = float(close[-1])
        yr_high = float(np.max(high))
        yr_low = float(np.min(low))
        rolling_base = yr_low

        bond_fv = rolling_base * (1 + tr_10y)
        bank_bot = bond_fv * (1 - margin_discount)  # The math is now correct: Bank_Bot is BELOW Bond_FV
        target = max(bond_fv, cur * 1.25)

        # Signal proximity score (0 = far above, 100 = deep below bank bottom)
        if cur >= bond_fv:
            proximity = max(0, 100 - ((cur - bank_bot) / bank_bot * 100))
            proximity = max(0, min(proximity, 50))
        elif cur >= bank_bot:
            proximity = 50 + ((bond_fv - cur) / (bond_fv - bank_bot) * 30)
        else:
            proximity = 80 + min(20, ((bank_bot - cur) / bank_bot * 100))
        proximity = round(min(100, max(0, proximity)), 1)

        # Bearish exhaustion pattern
        prev_close = np.roll(close, 1); prev_close[0] = np.nan
        cond_below = (close < bond_fv) & (close < bank_bot)
        bearish = (high > opn) & (close < prev_close) & (close < opn)
        b_prev = np.roll(bearish, 1); b_prev[0] = False
        signal = bool(cond_below[-1] & bearish[-1] & b_prev[-1])

        # Volatility (20-day)
        returns = np.diff(close) / close[:-1]
        vol_20d = float(np.std(returns[-20:]) * np.sqrt(252) * 100) if len(returns) >= 20 else 0

        # Trend (50-day SMA direction)
        sma50 = float(np.mean(close[-50:])) if len(close) >= 50 else cur
        trend = "Uptrend" if cur > sma50 else "Downtrend"

        # Distance metrics
        dist_bond = round((cur - bond_fv) / bond_fv * 100, 2)
        dist_bank = round((cur - bank_bot) / bank_bot * 100, 2)
        from_high = round((cur - yr_high) / yr_high * 100, 1)

        # Average volume
        avg_vol = float(np.mean(vol[-20:])) if len(vol) >= 20 else 0

        return {
            "price": cur, "bond_fv": bond_fv, "bank_bot": bank_bot,
            "target": target, "signal": signal, "proximity": proximity,
            "dist_bond": dist_bond, "dist_bank": dist_bank,
            "from_high": from_high, "yr_high": yr_high, "yr_low": yr_low,
            "vol_20d": round(vol_20d, 1), "trend": trend,
            "avg_vol": avg_vol,
        }
    except: return None


# ═══════════════════════════════════════════════════════════════════════════
# 5-YEAR BACKTEST ENGINE
# ═══════════════════════════════════════════════════════════════════════════
def _run_full_backtest(macros: dict) -> dict:
    tr_10y = macros["tr_10y"]
    md = macros["margin_discount"]

    dfs = {}
    for t in DEFAULT_TICKERS:
        try:
            df = yf.download(t, period="5y", progress=False)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna(subset=['Close'])
            if len(df) < 252: continue

            df['Rolling_Base'] = df['Low'].rolling(252, min_periods=252).min()
            df['Bond_FV'] = df['Rolling_Base'] * (1 + tr_10y)
            df['Bank_Bot'] = df['Bond_FV'] * (1 - md)

            close = df['Close'].values.astype(float)
            opn = df['Open'].values.astype(float)
            high = df['High'].values.astype(float)

            prev_close = np.roll(close, 1); prev_close[0] = np.nan
            cond1 = (close < df['Bond_FV'].values) & (close < df['Bank_Bot'].values)
            bearish = (high > opn) & (close < prev_close) & (close < opn)
            b_prev = np.roll(bearish, 1); b_prev[0] = False

            df['Signal'] = cond1 & bearish & b_prev
            dfs[t] = df
        except: pass

    all_dates = sorted(set(d for df in dfs.values() for d in df.index.tolist()))
    cash, holdings, history = 100_000.0, {}, []
    equity_curve = {}
    pos_pct, trail, time_days = 0.25, 0.12, 90
    peak_equity = 100_000.0
    max_dd = 0.0

    for d in all_dates:
        h_val = sum(
            h['qty'] * float(dfs[t].loc[d, 'Close']) if d in dfs[t].index else h['qty'] * h['cost']
            for t, h in holdings.items()
        )
        equity = cash + h_val
        peak_equity = max(peak_equity, equity)
        dd = (peak_equity - equity) / peak_equity * 100
        max_dd = max(max_dd, dd)
        equity_curve[d.strftime('%Y-%m-%d')] = round(equity, 2)

        sold = set()
        for t, h in list(holdings.items()):
            if d not in dfs[t].index: continue
            row = dfs[t].loc[d]
            price, hi = float(row['Close']), float(row['High'])
            buy_d = pd.to_datetime(h['buy_date'])

            if (d - buy_d).days >= time_days:
                prof = h['qty'] * price - h['qty'] * h['cost']
                cash += h['qty'] * price
                history.append(f"{d.strftime('%Y-%m-%d')} | TIME | {t:<12} | Exit: ${price:.2f} | P&L: ${prof:>+,.0f}")
                del holdings[t]; sold.add(t)
            elif hi >= h['target']:
                prof = h['qty'] * h['target'] - h['qty'] * h['cost']
                cash += h['qty'] * h['target']
                history.append(f"{d.strftime('%Y-%m-%d')} | SELL | {t:<12} | Exit: ${h['target']:.2f} | P&L: ${prof:>+,.0f}")
                del holdings[t]; sold.add(t)
            elif price <= h['trailing_high'] * (1 - trail):
                prof = h['qty'] * price - h['qty'] * h['cost']
                cash += h['qty'] * price
                history.append(f"{d.strftime('%Y-%m-%d')} | STOP | {t:<12} | Exit: ${price:.2f} | P&L: ${prof:>+,.0f}")
                del holdings[t]; sold.add(t)
            else:
                holdings[t]['trailing_high'] = max(h['trailing_high'], hi)

        for t, df in dfs.items():
            if t in holdings or t in sold or d not in df.index: continue
            row = df.loc[d]
            if bool(row['Signal']):
                invest = equity * pos_pct
                if cash >= invest >= 100:
                    price = float(row['Close'])
                    if pd.isna(row['Bond_FV']) or pd.isna(price): continue
                    tgt = max(float(row['Bond_FV']), price * 1.25)
                    qty = invest / price
                    cash -= invest
                    holdings[t] = {'qty': qty, 'cost': price, 'target': tgt,
                                   'trailing_high': price, 'buy_date': d.strftime('%Y-%m-%d %H:%M')}
                    history.append(f"{d.strftime('%Y-%m-%d')} | BUY  | {t:<12} | Entry: ${price:.2f}")

    return {
        "_id": "main_fund", "cash": round(cash, 2), "holdings": holdings,
        "history": history, "equity_curve": equity_curve,
        "max_dd": round(max_dd, 2),
        "inception": all_dates[0].strftime('%Y-%m-%d') if all_dates else "2021-10-01"
    }


# ═══════════════════════════════════════════════════════════════════════════
# SIGNAL RADAR SCAN (same trade logic as the original Signal Radar page)
# ═══════════════════════════════════════════════════════════════════════════
def run_scan(pf: dict, tickers: list, tr10: float, md: float, pos_pct: float, trail_stop: float,
             time_stop: int, on_progress=None) -> tuple[list, list]:
    """Analyse every ticker, apply exits/entries to `pf` in place and save it.

    Returns (results, actions): results are deep_analyze() rows plus "ticker",
    actions are (kind, ticker, price, pnl) tuples for this scan.
    """
    results, actions = [], []
    for idx, t in enumerate(tickers):
        if on_progress:
            on_progress((idx + 1) / len(tickers), t)
        d = deep_analyze(t, tr10, md)
        if not d: continue

        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M")

        if t in pf["holdings"]:
            h = pf["holdings"][t]
            bd = h.get("buy_date","")[:10]
            bd = datetime.strptime(bd, "%Y-%m-%d") if len(bd)>=10 else datetime.now()

            if (datetime.now()-bd).days >= time_stop:
                prof = h["qty"]*d["price"] - h["qty"]*h["cost"]
                pf["cash"] += h["qty"]*d["price"]
                pf["history"].append(f"{now_ts} | TIME | {t:<12} | Exit: ${d['price']:.2f} | P&L: ${prof:>+,.0f}")
                del pf["holdings"][t]; actions.append(("TIME",t,d["price"],prof))
            elif d["price"] >= h["target"]:
                prof = h["qty"]*d["price"] - h["qty"]*h["cost"]
                pf["cash"] += h["qty"]*d["price"]
                pf["history"].append(f"{now_ts} | SELL | {t:<12} | Exit: ${d['price']:.2f} | P&L: ${prof:>+,.0f}")
                del pf["holdings"][t]; actions.append(("SELL",t,d["price"],prof))
            elif d["price"] <= h.get("trailing_high",h["cost"])*(1-trail_stop):
                prof = h["qty"]*d["price"] - h["qty"]*h["cost"]
                pf["cash"] += h["qty"]*d["price"]
                pf["history"].append(f"{now_ts} | STOP | {t:<12} | Exit: ${d['price']:.2f} | P&L: ${prof:>+,.0f}")
                del pf["holdings"][t]; actions.append(("STOP",t,d["price"],prof))
            else:
                pf["holdings"][t]["trailing_high"] = max(h.get("trailing_high",h["cost"]), d["price"])

        if d["signal"] and t not in pf["holdings"]:
            invest = pf["cash"] * pos_pct
            if invest >= 100:
                qty = invest/d["price"]
                pf["cash"] -= invest
                pf["holdings"][t] = {"qty":qty,"cost":d["price"],"target":d["target"],"trailing_high":d["price"],"buy_date":now_ts}
                pf["history"].append(f"{now_ts} | BUY  | {t:<12} | Entry: ${d['price']:.2f}")
                actions.append(("BUY",t,d["price"],0))

        results.append(d | {"ticker": t})

    save_pf(pf)
    results.sort(key=lambda x: x["proximity"], reverse=True)
    return results, actions
