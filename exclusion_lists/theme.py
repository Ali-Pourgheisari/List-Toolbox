"""Theme state and CSS injection.

The stylesheet lives in assets/base.css as CSS custom properties with dark
defaults; assets/light.css redefines only those properties, so switching themes
is one extra <style> block rather than a second full stylesheet.
"""

from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).parent / "assets"

THEME_KEY = "theme"
DEFAULT_THEME = "dark"


def _read_css(name: str) -> str:
    return (ASSETS / name).read_text(encoding="utf-8")


def _toggle_theme():
    st.session_state[THEME_KEY] = 'light' if st.session_state[THEME_KEY] == 'dark' else 'dark'


def is_dark() -> bool:
    return st.session_state.get(THEME_KEY, DEFAULT_THEME) == 'dark'


def apply_theme() -> None:
    """Set up theme state and inject the stylesheet. Call once, before any UI."""
    if THEME_KEY not in st.session_state:
        st.session_state[THEME_KEY] = DEFAULT_THEME

    st.markdown(f"<style>\n{_read_css('base.css')}\n</style>", unsafe_allow_html=True)
    if not is_dark():
        st.markdown(f"<style>\n{_read_css('light.css')}\n</style>", unsafe_allow_html=True)


def render_header() -> None:
    """App logo on the left, theme toggle on the right."""
    col_logo, _, col_btn = st.columns([5, 7, 2])
    with col_logo:
        st.markdown('<div class="app-logo"><span class="dot">◼</span> List Toolbox</div>',
                    unsafe_allow_html=True)
    with col_btn:
        st.markdown('<span id="_theme_anchor"></span>', unsafe_allow_html=True)
        label = "☀ Light" if is_dark() else "☾ Dark"
        st.button(label, on_click=_toggle_theme, key="_theme_btn")

    st.markdown("<div style='margin-bottom:0.2rem'></div>", unsafe_allow_html=True)


def render_footer() -> None:
    st.markdown("<br><hr style='border-color:#0d1520;margin-top:2rem'>", unsafe_allow_html=True)
    st.markdown(
        "<small style='color:#1e2d3d;font-family:JetBrains Mono,monospace;font-size:0.68rem'>"
        "RapidFuzz token_sort_ratio &mdash; handles reordering, abbreviations &amp; legal suffix "
        "differences. Promoted matches appear in downloads immediately.</small>",
        unsafe_allow_html=True)
