"""Markup fragments and input blocks used across the page.

The stylesheet defines the classes (.section-header, .stat-box, .match-card …);
these helpers are the only places that write them, so the markup lives in one
spot rather than being retyped at every call site.
"""

import streamlit as st

from ..core.combine import APPEND_SKIP
from ..core.text import col_key

DIM = "#3a4a5e"     # secondary caption colour
DIMMER = "#2a3a4e"  # tertiary caption colour

# Where the match-sensitivity slider starts. Also the fallback the page uses when
# screening is switched off and the slider is never drawn, so it lives here once.
DEFAULT_THRESHOLD = 85


def caption(text: str, color: str = DIM) -> None:
    """Small muted explanatory line."""
    st.markdown(f"<small style='color:{color}'>{text}</small>", unsafe_allow_html=True)


def section_header(title: str, step: str = "") -> None:
    """Section heading, optionally numbered — e.g. "03 — Columns to compare"."""
    label = f"{step} &mdash; {title}" if step else title
    st.markdown(f'<div class="section-header">&#9632;&nbsp; {label}</div>', unsafe_allow_html=True)


def upload_label(step: str, title: str) -> None:
    st.markdown(f'<div class="upload-label">&#9632;&nbsp; {step} &mdash; {title}</div>',
                unsafe_allow_html=True)


def page_description(html: str) -> None:
    """The intro blurb at the top of the page."""
    st.markdown(f'<div class="page-desc">{html}</div>', unsafe_allow_html=True)


def stat_box(container, value: int, label: str, warn: bool = False) -> None:
    container.markdown(
        f'<div class="stat-box"><div class="stat-num{" warn" if warn else ""}">{value:,}</div>'
        f'<div class="stat-label">{label}</div></div>',
        unsafe_allow_html=True)


def match_card(left: str, arrow: str, right: str, score: str, dim: bool = False) -> None:
    """One "name → matched name — score" row in the review list."""
    st.markdown(f"""
    <div class="match-card"{' style="opacity:0.6"' if dim else ''}>
      <span class="match-names"><span class="match-main">{left}</span>"""
                f"""<span class="match-arrow">{arrow}</span>{right}</span>
      <span class="match-score">{score}</span>
    </div>""", unsafe_allow_html=True)


def empty_state(body: str, hint: str) -> None:
    """The dashed placeholder panel shown before there is anything to display."""
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#0d1117,#0c1520);border:1px dashed #1e2d3d;border-radius:10px;padding:2.5rem;text-align:center;margin-top:1rem'>
      <div style='font-family:JetBrains Mono,monospace;font-size:2rem;color:#1a2d3e;margin-bottom:0.8rem'>&#9632;</div>
      <div style='color:#3a4a5e;font-size:0.9rem'>{body}</div>
      <div style='color:#1e2d3d;font-size:0.78rem;margin-top:0.5rem'>{hint}</div>
    </div>
    """, unsafe_allow_html=True)


def threshold_slider(key: str, caption_html: str) -> int:
    """The match-sensitivity slider with its live score readout."""
    slider_col, hint_col = st.columns([3, 1])
    with slider_col:
        threshold = st.slider(
            "Match threshold",
            min_value=50, max_value=100, value=DEFAULT_THRESHOLD,
            help=f"Lower = catches more variations. {DEFAULT_THRESHOLD} is a good default.",
            label_visibility="collapsed",
            key=key,
        )
    with hint_col:
        st.markdown(
            f"<div style='font-family:JetBrains Mono,monospace;font-size:1.4rem;font-weight:700;"
            f"color:#00ff88;text-align:center;padding-top:0.3rem'>{threshold}"
            f"<span style='font-size:0.7rem;color:#3a4a5e;margin-left:2px'>/ 100</span></div>",
            unsafe_allow_html=True)
    caption(caption_html.format(threshold=threshold), DIMMER)
    return threshold


def render_column_mapping(title, main_columns, new_columns, key_prefix, preselect=None):
    """One "main list column <- column from this file" mapping block.
    preselect: {main_col: source_col} defaults that win over name auto-matching —
    used for the company column, which the user has already paired up in step 03.
    Returns {main_col: source_col | APPEND_SKIP}."""
    options = [APPEND_SKIP] + new_columns
    st.markdown(
        f"<small style='color:#3a4a5e;font-family:JetBrains Mono,monospace;text-transform:uppercase;"
        f"letter-spacing:0.08em'>&#9654;&nbsp; {title}</small>", unsafe_allow_html=True)

    hdr_l, hdr_r = st.columns([1, 2])
    with hdr_l:
        st.markdown("<small style='color:#2a3a4e;font-family:JetBrains Mono,monospace'>Main list column</small>", unsafe_allow_html=True)
    with hdr_r:
        st.markdown("<small style='color:#2a3a4e;font-family:JetBrains Mono,monospace'>Column from this file</small>", unsafe_allow_html=True)

    mapping = {}
    for mc in main_columns:
        forced      = (preselect or {}).get(mc)
        auto_match  = (forced if forced in new_columns
                       else next((c for c in new_columns if col_key(c) == col_key(mc)), None))
        default_idx = new_columns.index(auto_match) + 1 if auto_match else 0
        map_l, map_r = st.columns([1, 2])
        with map_l:
            st.markdown(f"<div style='padding:0.45rem 0;font-family:JetBrains Mono,monospace;font-size:0.8rem;color:#c9d1e0'>{mc}</div>", unsafe_allow_html=True)
        with map_r:
            mapping[mc] = st.selectbox(
                mc,
                options,
                index=default_idx,
                key=f"{key_prefix}_{mc}_{forced}" if forced else f"{key_prefix}_{mc}",
                label_visibility="collapsed",
            )
    return mapping
