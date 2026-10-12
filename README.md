# Ozpiskin Financial Models

The home site for all of my quantitative models. Each model keeps running on its
own server; this site gathers them under one address and shows each live
dashboard on its own page, together with its methodology and source code.

| Model | Stack | Source |
|-------|-------|--------|
| WTI Crude Oil Valuation Model | FastAPI · Dash · Plotly | [Crude_Oil_Fairvalue_Model](https://github.com/dozpiskin/Crude_Oil_Fairvalue_Model) |
| Macro Floor Model | Streamlit · MongoDB | [Macro-Floor-Forced-Liquidation-Model](https://github.com/dozpiskin/Macro-Floor-Forced-Liquidation-Model) |

## Structure

```
index.html          page shell
assets/models.js    ← the only file to edit: models, live URLs, research pipeline
assets/app.js       rendering and routing (#/models/<slug>)
assets/style.css    styles
```

## Adding a new model

1. Deploy the model anywhere (Render, Streamlit Cloud, ...).
2. Add a new entry to `window.MODELS` in `assets/models.js` with its `liveUrl`.
3. Commit and push — GitHub Pages updates the site automatically.

## Hosting (GitHub Pages, free)

1. Create a repository named **`dozpiskin.github.io`** and push this folder to it.
2. The site is published at `https://dozpiskin.github.io`.
3. Optional: buy a domain (e.g. `ozpiskinfinancialmodels.com`) and set it under
   *Settings → Pages → Custom domain*.

---

For research and educational purposes only. Not investment advice.
