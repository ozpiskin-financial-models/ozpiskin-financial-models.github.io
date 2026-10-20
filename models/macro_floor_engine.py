"""
Calculation engine for the Macro Floor Model.

Copied unchanged from live_uncle_tracker.py in the
Macro-Floor-Forced-Liquidation-Model repository (macro feed, MongoDB storage,
signal engine and 5-year backtest). run_scan() is the Signal Radar loop from
the same file, moved into a function so the page can call it. The default
universe is BIST-only (see DEFAULT_TICKERS).

One addition to the original (requested by the author, Oct 2026): idle cash
is no longer left at 0%. Each day it earns the TCMB overnight borrowing rate in
force on that day (data/tcmb_overnight.csv), compounded daily (ACT/365), so the
backtest never applies today's rate to past years. See grow_cash(),
accrue_cash() and the interest lines in _run_full_backtest().
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

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
# INTEREST ON IDLE CASH — TCMB overnight borrowing rate, as in force each day
# ═══════════════════════════════════════════════════════════════════════════
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RATES_FILE = DATA_DIR / "tcmb_overnight.csv"
TCMB_RATES_URL = (
    "https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Temel+Faaliyetler/"
    "Para+Politikasi/Merkez+Bankasi+Faiz+Oranlari/faiz-oranlari"
)


def _fetch_tcmb_overnight() -> pd.Series | None:
    """Read the O/N borrowing-rate table from TCMB's website; None if unavailable or malformed."""
    try:
        page = requests.get(TCMB_RATES_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text
        cells = [re.sub(r"<[^>]+>", "", c).replace("&nbsp;", "").strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", page, re.S)]
        rates = {}
        for i, cell in enumerate(cells[:-2]):
            m = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{2})", cell)
            if m:
                rates[pd.Timestamp(2000 + int(m[3]), int(m[2]), int(m[1]))] = float(cells[i + 1].replace(",", ".")) / 100.0
        return pd.Series(rates).sort_index() if len(rates) >= 100 else None
    except Exception:
        return None


@st.cache_data(ttl=12 * 3600, show_spinner=False)
def overnight_table() -> tuple[pd.Series, str]:
    """(TCMB O/N borrowing rate as decimals indexed by effective date, source label).

    Fetched live from TCMB twice a day; data/tcmb_overnight.csv is the fallback and fills any gaps.
    """
    frame = pd.read_csv(RATES_FILE, comment="#", parse_dates=["date"])
    saved = (frame.set_index("date")["borrowing"] / 100.0).sort_index()
    live = _fetch_tcmb_overnight()
    if live is None:
        return saved, "data/tcmb_overnight.csv"
    return live.combine_first(saved).sort_index(), "tcmb.gov.tr (live)"


def overnight_rates() -> pd.Series:
    return overnight_table()[0]


def overnight_rate_on(day) -> float:
    rates = overnight_rates()
    in_force = rates[rates.index <= pd.Timestamp(day)]
    return float(in_force.iloc[-1]) if len(in_force) else float(rates.iloc[0])


def grow_cash(amount: float, start, end) -> float:
    """Value at `end` of `amount` held from `start`, compounding daily (ACT/365) at the rate in force each day."""
    start, end = pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize()
    if amount <= 0 or end <= start:
        return amount
    rates = overnight_rates()
    changes = [d for d in rates.index if start < d < end]
    value, cursor = amount, start
    for boundary in changes + [end]:
        value *= (1 + overnight_rate_on(cursor)) ** ((boundary - cursor).days / 365)
        cursor = boundary
    return value


# ═══════════════════════════════════════════════════════════════════════════
# TR 10Y DAILY HISTORY — seed file + one live observation per day in MongoDB
# ═══════════════════════════════════════════════════════════════════════════
TR10Y_FILE = DATA_DIR / "tr10y_history.csv"
LIVE_FALLBACK_TR10 = 0.320  # fetch_macros() default when TradingView is unreachable — never recorded


@st.cache_data(ttl=3600, show_spinner=False)
def record_daily_tr10(day: str, tr10: float) -> bool:
    """Store the day's live TR 10Y in MongoDB (at most once an hour) so the history grows by itself."""
    if abs(tr10 - LIVE_FALLBACK_TR10) < 1e-12:
        return False
    try:
        _mongo()["macro_floor_db"]["tr10y_daily"].update_one(
            {"_id": day}, {"$set": {"yield": round(tr10 * 100, 3), "source": "TradingView"}}, upsert=True
        )
        return True
    except Exception:
        return False


@st.cache_data(ttl=3600, show_spinner=False)
def tr10y_history() -> pd.Series:
    """Daily TR 10Y yield (decimal): the seed file, extended by the live observations stored in MongoDB."""
    frame = pd.read_csv(TR10Y_FILE, comment="#", parse_dates=["date"])
    series = (frame.set_index("date")["yield"] / 100.0).sort_index()
    try:
        docs = list(_mongo()["macro_floor_db"]["tr10y_daily"].find())
        recorded = pd.Series({pd.Timestamp(d["_id"]): d["yield"] / 100.0 for d in docs})
        series = series.combine_first(recorded).sort_index()
    except Exception:
        pass
    return series


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
    interest_earned, prev_d = 0.0, None

    for d in all_dates:
        # Idle cash earns the TCMB overnight rate in force on each day (ACT/365).
        if prev_d is not None:
            interest = grow_cash(cash, prev_d, d) - cash
            cash += interest
            interest_earned += interest
        prev_d = d

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
        "inception": all_dates[0].strftime('%Y-%m-%d') if all_dates else "2021-10-01",
        "cash_as_of": all_dates[-1].strftime('%Y-%m-%d') if all_dates else datetime.now().strftime('%Y-%m-%d'),
        "interest_earned": round(interest_earned, 2),
    }


def accrue_cash(pf: dict, as_of: date | None = None) -> float:
    """Grow idle cash from pf["cash_as_of"] to `as_of` at the TCMB overnight rates in force.

    Updates pf in place (cash, cash_as_of, interest_earned) and returns the interest added.
    A portfolio saved before this feature has no cash_as_of; it starts accruing from today.
    """
    today = as_of or datetime.now().date()
    start = pf.get("cash_as_of")
    pf["cash_as_of"] = today.strftime("%Y-%m-%d")
    if not start:
        return 0.0
    if (today - datetime.strptime(start[:10], "%Y-%m-%d").date()).days <= 0:
        return 0.0
    interest = grow_cash(pf.get("cash", 0.0), start[:10], today) - pf.get("cash", 0.0)
    pf["cash"] = round(pf.get("cash", 0.0) + interest, 2)
    pf["interest_earned"] = round(pf.get("interest_earned", 0.0) + interest, 2)
    return interest


# ═══════════════════════════════════════════════════════════════════════════
# SIGNAL RADAR SCAN (same trade logic as the original Signal Radar page)
# ═══════════════════════════════════════════════════════════════════════════
def run_scan(pf: dict, tickers: list, tr10: float, md: float, pos_pct: float, trail_stop: float,
             time_stop: int, on_progress=None) -> tuple[list, list]:
    """Analyse every ticker, apply exits/entries to `pf` in place and save it.

    Returns (results, actions): results are deep_analyze() rows plus "ticker",
    actions are (kind, ticker, price, pnl) tuples for this scan.
    """
    accrue_cash(pf)  # bring idle cash up to date before sizing new positions
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
