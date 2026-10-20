"""
Ozpiskin Financial Models — one Streamlit site for every model.

Run locally with:
    streamlit run streamlit_app.py

Each model has a calculation engine in models/ and a page in views/. To add a
model: create both, register the page in NAV_PAGES below and add it to
views/home.py.
"""

import streamlit as st

from ui import kit

st.set_page_config(
    page_title="Ozpiskin Financial Models",
    page_icon="assets/favicon.svg",
    layout="wide",
    initial_sidebar_state="collapsed",
)
kit.inject_global_css()

home = st.Page("views/home.py", title="Models", default=True)
crude_oil = st.Page("views/crude_oil.py", title="WTI Crude Oil", url_path="crude-oil")
macro_floor = st.Page("views/macro_floor.py", title="Macro Floor", url_path="macro-floor")
NAV_PAGES = [("home", home), ("crude", crude_oil), ("macro", macro_floor)]

current = st.navigation([page for _, page in NAV_PAGES], position="hidden")
kit.top_nav(NAV_PAGES, home, current)
current.run()
kit.footer()
