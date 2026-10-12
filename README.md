# Ozpiskin Financial Models

One website for all of my quantitative models. The site is a single Streamlit
app with a page per model.

| Page | Model | Original repository |
|------|-------|---------------------|
| WTI Crude Oil | Crude-oil fair value & temperature gauge | [Crude_Oil_Fairvalue_Model](https://github.com/dozpiskin/Crude_Oil_Fairvalue_Model) |
| Macro Floor | Forced-liquidation crisis-bottom fund | [Macro-Floor-Forced-Liquidation-Model](https://github.com/dozpiskin/Macro-Floor-Forced-Liquidation-Model) |

## Structure

```
streamlit_app.py            entry point: page config, logo, top navigation
views/home.py               landing page (model cards, research pipeline, about)
views/crude_oil.py          WTI Crude Oil dashboard (Dash layout ported to Streamlit)
views/macro_floor.py        Macro Floor dashboard (from live_uncle_tracker.py)
models/crude_oil_engine.py  crude-oil calculation engine (main.py without the FastAPI server)
.streamlit/config.toml      dark theme
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
4. Advanced settings → Secrets:
   ```toml
   MONGO_URI = "mongodb+srv://..."   # Macro Floor portfolio storage
   EIA_API_KEY = "..."               # optional: live EIA crude inventories
   ```

## Adding a new model

1. Put the model's calculation code in `models/`.
2. Create `views/<model>.py` for its dashboard.
3. Register it with `st.Page(...)` in `streamlit_app.py` and add a card in `views/home.py`.
4. Push — Streamlit Cloud redeploys automatically.

---

For research and educational purposes only. Not investment advice.
