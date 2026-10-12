"""
Ozpiskin Financial Models — one Streamlit site for every model.

Run locally with:
    streamlit run streamlit_app.py

Each model lives in its own page under views/. To add a new model, create
views/<model>.py, add an st.Page for it below and a card in views/home.py.
"""

import streamlit as st

st.set_page_config(
    page_title="Ozpiskin Financial Models",
    page_icon="assets/favicon.svg",
    layout="wide",
    initial_sidebar_state="auto",
)

st.logo("assets/logo.svg", size="large", icon_image="assets/favicon.svg")

# Site-wide chrome: hide Streamlit's own menu/footer, keep the top navigation bar.
st.markdown(
    """
<style>
#MainMenu, footer, .stDeployButton, [data-testid="stToolbar"] { display: none !important; }
.stApp {
  background:
    radial-gradient(circle at top left, rgba(8, 145, 178, 0.12), transparent 28%),
    radial-gradient(circle at top right, rgba(167, 139, 250, 0.08), transparent 26%),
    #070b16;
}
header[data-testid="stHeader"] { background: rgba(7, 11, 22, 0.85); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(148, 163, 184, 0.12); }
</style>
""",
    unsafe_allow_html=True,
)

home = st.Page("views/home.py", title="Home", icon=":material/home:", default=True)
crude_oil = st.Page("views/crude_oil.py", title="WTI Crude Oil", icon=":material/oil_barrel:", url_path="crude-oil")
macro_floor = st.Page("views/macro_floor.py", title="Macro Floor", icon=":material/monitoring:", url_path="macro-floor")

st.navigation([home, crude_oil, macro_floor], position="top").run()
