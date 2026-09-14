"""Application entry point.

st.set_page_config must be the first Streamlit call of the run, so it happens at
the top of main() — importing the tab modules only defines functions, it does not
draw anything.
"""

import streamlit as st

from .theme import apply_theme, render_footer, render_header
from .ui import list_diff, screen_append


def main() -> None:
    st.set_page_config(
        page_title="List Toolbox",
        page_icon="⚡",
        layout="wide",
    )

    apply_theme()
    render_header()

    tab_screen, tab_diff = st.tabs(["  Screen & Append  ", "  List Diff  "])
    with tab_screen:
        screen_append.render()
    with tab_diff:
        list_diff.render()

    render_footer()
