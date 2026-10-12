# Ozpiskin Financial Models

One website for all of my quantitative models. The site is a single Streamlit
app with a page per model.

| Page | Model | Original repository |
|------|-------|---------------------|
| WTI Crude Oil | Crude-oil fair value & temperature gauge | [Crude_Oil_Fairvalue_Model](https://github.com/dozpiskin/Crude_Oil_Fairvalue_Model) |
| Macro Floor | Forced-liquidation crisis-bottom fund | [Macro-Floor-Forced-Liquidation-Model](https://github.com/dozpiskin/Macro-Floor-Forced-Liquidation-Model) |

## Structure

```
streamlit_app.py              entry point: page config, top navigation, footer
ui/kit.py                     shared design system (theme, KPI strip, tables, tabs, chart style)
views/home.py                 landing page
views/crude_oil.py            WTI Crude Oil page
views/macro_floor.py          Macro Floor page
models/crude_oil_engine.py    crude-oil calculations (main.py without the FastAPI server)
models/macro_floor_engine.py  Macro Floor calculations (from live_uncle_tracker.py)
.streamlit/config.toml        theme
requirements.txt
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy (Streamlit Community Cloud, free)

1. share.streamlit.io → **Create app** → deploy from GitHub.
2. Repository `ozpiskin-financial-models/ozpiskin-financial-models.github.io`,
   branch `main`, main file `streamlit_app.py`.
3. App URL: `ozpiskin-financial-models` → `https://ozpiskin-financial-models.streamlit.app`.
   `https://ozpiskin-financial-models.github.io` redirects there (index.html).
4. Advanced settings → Secrets:
   ```toml
   MONGO_URI = "mongodb+srv://..."   # Macro Floor portfolio storage
   EIA_API_KEY = "..."               # optional: live EIA crude inventories
   ```

## Adding a new model

1. Put the model's calculation code in `models/`.
2. Create `views/<model>.py` using the helpers in `ui/kit.py` (page_header, kpi_strip, subnav, section, table, chart).
3. Register it with `st.Page(...)` in `streamlit_app.py` (page list and nav links) and add a card in `views/home.py`.
4. Push — Streamlit Cloud redeploys automatically.

---

For research and educational purposes only. Not investment advice.
