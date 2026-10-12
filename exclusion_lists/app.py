"""Application entry point.

st.set_page_config must be the first Streamlit call of the run, so it happens at
the top of main() — importing the page module only defines functions, it does not
draw anything.
"""

import streamlit as st

from .theme import apply_theme, render_footer, render_header
from .ui import screen_append


def main() -> None:
    st.set_page_config(
        page_title="List Toolbox",
        page_icon="⚡",
        layout="wide",
    )

    apply_theme()
    render_header()
    screen_append.render()
    render_footer()
