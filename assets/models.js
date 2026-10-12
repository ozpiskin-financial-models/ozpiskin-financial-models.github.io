/*
 * ─────────────────────────────────────────────────────────────────────────
 *  OZPISKIN FINANCIAL MODELS — site configuration
 * ─────────────────────────────────────────────────────────────────────────
 *  This is the only file you need to edit to add, update or remove a model.
 *
 *  liveUrl   → the URL where the model's app is running (Render, Streamlit
 *              Cloud, ...). Leave it "" until the app is deployed; the page
 *              will show a "coming online soon" notice instead of the embed.
 *  status    → "live" | "beta" | "in-development"
 *  embed     → true  : the app is shown inside the site (iframe)
 *              false : the page shows a button that opens the app instead
 * ─────────────────────────────────────────────────────────────────────────
 */

window.SITE = {
  name: "Ozpiskin Financial Models",
  owner: "Derin Özpişkin",
  github: "https://github.com/dozpiskin",
};

window.MODELS = [
  {
    slug: "crude-oil-valuation",
    name: "WTI Crude Oil Valuation Model",
    short: "Crude Oil Fair Value",
    tagline:
      "A temperature gauge that scores crude-oil fundamentals, estimates fair value and maps the valuation gap from Very Cold to Very Hot.",
    status: "live",
    assetClass: "Commodities",
    stack: ["FastAPI", "Dash", "Plotly", "yfinance", "EIA API"],
    liveUrl: "", // e.g. "https://crude-oil-fairvalue-model.onrender.com"
    embed: true,
    sourceUrl: "https://github.com/dozpiskin/Crude_Oil_Fairvalue_Model",
    coldStartNote:
      "Hosted on a free tier — if the server has been idle, the first load can take up to a minute.",
    highlights: [
      { label: "Weighted drivers", value: "8" },
      { label: "Signal regimes", value: "5" },
      { label: "Refresh", value: "5 min" },
    ],
    methodology: [
      {
        title: "Eight weighted fundamental drivers",
        body:
          "Inventories vs. 5-year average (17%), USD strength via DXY (12%), price vs. 200-day SMA (8%), oil volatility OVX (12%), geopolitical risk (13%), implied inflation from TIPS/Treasuries (13%), growth expectations from credit spreads (13%) and substitution risk from natural gas (12%).",
      },
      {
        title: "Fair value & valuation gap",
        body:
          "The weighted score, adjusted by a volatility factor, produces a fair-value estimate. The gap between spot WTI and fair value is mapped to a temperature: Very Cold, Cold, Neutral, Hot, Very Hot.",
      },
      {
        title: "Macro regime overlays",
        body:
          "A demand-destruction profile tracks distance to the $120 / $150 thresholds, and a stagflation monitor combines inflation, growth, China equities and oil momentum to adjust the signal.",
      },
      {
        title: "Historical signal backtest",
        body:
          "The model is replayed over history and forward returns are measured for each temperature regime to check whether the signals point in the expected direction.",
      },
    ],
  },
  {
    slug: "macro-floor-model",
    name: "Macro Floor Model",
    short: "Forced Liquidation Engine",
    tagline:
      "An autonomous fund engine that values equities against their opportunity-cost floors and buys crisis bottoms after margin-call exhaustion.",
    status: "live",
    assetClass: "Equities · US & BIST",
    stack: ["Streamlit", "Plotly", "yfinance", "MongoDB"],
    liveUrl: "", // e.g. "https://macro-floor-model.streamlit.app"
    embed: true,
    sourceUrl:
      "https://github.com/dozpiskin/Macro-Floor-Forced-Liquidation-Model",
    coldStartNote:
      "Hosted on Streamlit Community Cloud — if the app is asleep, click “Yes, get this app back up” inside the frame.",
    highlights: [
      { label: "Valuation phases", value: "6" },
      { label: "Tracked tickers", value: "20+" },
      { label: "Paper capital", value: "$100K" },
    ],
    methodology: [
      {
        title: "Six-phase valuation floors",
        body:
          "Technical retracement, inflation bottom, bond fair value (10Y yield), bank-borrowing bottom (US10Y + CDS + local premium), FX-carry bottom and the margin-call limit — each one a layer of opportunity cost under the price.",
      },
      {
        title: "Margin-call exhaustion signal",
        body:
          "The engine does not buy the first touch of the crisis zone. It waits until price is below both the bond and borrowing floors and, for two consecutive days, intraday rallies fail and close lower — the sign that forced sellers are running out.",
      },
      {
        title: "Exit discipline",
        body:
          "Take profit at the locked target (the larger of bond fair value or +25%), a 12% trailing stop from the post-entry high, and a 126-trading-day time stop.",
      },
      {
        title: "Autonomous paper portfolio",
        body:
          "Autopilot scans the universe, sizes positions as a share of capital and tracks live P&L, with the portfolio persisted in MongoDB so it survives restarts.",
      },
    ],
  },
];

/*
 * Research pipeline — upcoming work shown on the home page.
 * Move an item into MODELS above when it goes live.
 */
window.PIPELINE = [
  {
    name: "Next model",
    note: "Placeholder — replace with the title and one-line idea of your next model.",
    stage: "Research",
  },
];
