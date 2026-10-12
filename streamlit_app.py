"""
Ozpiskin Financial Models — one Streamlit site for every model.

Run locally with:
    streamlit run streamlit_app.py

Each model has a calculation engine in models/ and a page in views/. To add a
model: create both, register the page in PAGES below and add it to
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

current = st.navigation([home, crude_oil, macro_floor], position="hidden")

with st.container(key="topnav", horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
    with st.container(key="navbrand", width="content"):
        st.page_link(home, label="Ozpiskin")
    with st.container(key="navlinks", horizontal=True, width="content", gap="large", vertical_alignment="center"):
        for slug, page in (("home", home), ("crude", crude_oil), ("macro", macro_floor)):
            state = "on" if page.url_path == current.url_path else "off"
            with st.container(key=f"nav{state}_{slug}", width="content"):
                st.page_link(page)

current.run()
kit.footer()
