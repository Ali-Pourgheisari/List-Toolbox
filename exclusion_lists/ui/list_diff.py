"""Tab 2 — List Diff.

Merge several secondary lists, dedup the merged result on a column, then compare
it against the main list. Anything found on both sides is redundant and is
dropped from both, so the output holds only entries unique to one side.
"""

import io

import pandas as pd
import streamlit as st

from ..core.columns import detect_company_col
from ..core.files import get_excel_sheets, read_file
from ..core.matching import find_internal_duplicates, find_symmetric_overlap
from ..core.text import output_filename
from . import widgets as w

TAB_DESCRIPTION = """
  <strong>List Diff</strong> — merge several secondary lists together, dedup the result on
  a column you choose, then compare it against your main list. Any entry found in
  <em>both</em> is redundant and gets removed from both sides — what's left is only in
  the main list, or only in the secondary lists, never both.
"""

THRESHOLD_CAPTION = ("Entries scoring &ge; {threshold} against each other are treated as the "
                     "same company and dropped from both lists.")

RESULT_KEY = "ld_result"
COMPARE_COL = "__ld_compare__"   # the chosen company column, copied under one name
EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _upload_inputs():
    """Steps 01/02 — the main list and the secondary lists."""
    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        w.upload_label("01", "Main list")
        main_file = st.file_uploader("Main list", type=["xlsx", "xls", "csv"], key="ld_main",
                                     label_visibility="collapsed")

    with col_b:
        w.upload_label("02", "Secondary lists")
        secondary_files = st.file_uploader("Secondary lists", type=["xlsx", "xls", "csv"],
                                           key="ld_secondary", accept_multiple_files=True,
                                           label_visibility="collapsed")

    st.markdown("")
    return main_file, secondary_files


def _main_sheet_picker(main_file):
    if main_file and not main_file.name.lower().endswith('.csv'):
        sheets = get_excel_sheets(main_file)
        if sheets:
            chosen = st.selectbox("Sheet — Main list", sheets, key="ld_main_sheet")
            st.markdown("")
            return chosen
    return 0


def _secondary_column_pickers(secondary_files):
    """One expander per secondary file: its sheet and its company column.

    Returns ({filename: column}, {filename: sheet}, union of all columns seen).
    """
    sec_cols, sec_sheets, col_union = {}, {}, []

    for f in secondary_files:
        with st.expander(f"**{f.name}**", expanded=True):
            sheet = 0
            if not f.name.lower().endswith('.csv'):
                sheets = get_excel_sheets(f)
                if sheets:
                    sheet = st.selectbox("Sheet to use", sheets, key=f"ld_sheet_{f.name}")
                    st.markdown("")
            sec_sheets[f.name] = sheet

            try:
                cols = read_file(f, nrows=0, sheet_name=sheet).columns.tolist()
                f.seek(0)
            except Exception:
                st.warning(f"Could not read columns from {f.name}.")
                continue

            default = detect_company_col(cols)
            sec_cols[f.name] = st.selectbox(
                "Company column in this file",
                cols,
                index=cols.index(default),
                key=f"ld_col_{f.name}",
            )

            for c in cols:
                if c not in col_union:
                    col_union.append(c)

    return sec_cols, sec_sheets, col_union


def _column_settings(main_file, secondary_files, main_sheet):
    """Steps 03/04/05 — compare columns, dedup column, output columns."""
    settings = {
        "main_col": None, "dedup_col": None, "output_cols": None,
        "sec_cols": {}, "sec_sheets": {},
    }

    try:
        main_cols = read_file(main_file, nrows=0, sheet_name=main_sheet).columns.tolist()
        main_file.seek(0)
    except Exception:
        main_cols = []

    if not main_cols:
        return settings

    w.section_header("03", "Column to compare")
    settings["main_col"] = st.selectbox(
        "Main list — company column",
        main_cols,
        index=main_cols.index(detect_company_col(main_cols)),
    )
    st.markdown("")
    w.caption("Pick the matching column in each secondary file &mdash; they don't need the same header name.")
    st.markdown("")

    sec_cols, sec_sheets, col_union = _secondary_column_pickers(secondary_files)
    settings["sec_cols"], settings["sec_sheets"] = sec_cols, sec_sheets
    st.markdown("")

    if col_union:
        w.section_header("04", "Deduplicate secondary lists")
        w.caption("After merging, rows whose value in this column fuzzy-match each other are "
                  "collapsed to one &mdash; the first occurrence is kept.")
        st.markdown("")
        settings["dedup_col"] = st.selectbox(
            "Deduplicate merged secondary list on column",
            col_union,
            index=col_union.index(detect_company_col(col_union)),
        )
        st.markdown("")

    output_col_union = main_cols + [c for c in col_union if c not in main_cols]
    w.section_header("05", "Output columns")
    w.caption("Columns to keep in the result.")
    st.markdown("")
    settings["output_cols"] = st.multiselect(
        "Columns to include in the output",
        output_col_union,
        default=[],
    )
    st.markdown("")

    return settings


def _merge_secondary(secondary_files, sec_cols, sec_sheets):
    """Every secondary list, concatenated, with the chosen company column copied to COMPARE_COL."""
    frames = []
    for f in secondary_files:
        if f.name not in sec_cols:
            continue
        df = read_file(f, sheet_name=sec_sheets.get(f.name, 0))
        sec_col = sec_cols[f.name]
        df = df.dropna(subset=[sec_col]).reset_index(drop=True)
        df[COMPARE_COL] = df[sec_col].astype(str)
        frames.append(df)
    return frames


def _run(main_file, secondary_files, main_sheet, settings, threshold):
    """Merge, dedup, diff, and cache the result under RESULT_KEY."""
    if not main_file or not secondary_files:
        st.error("Please upload the main list and at least one secondary list.")
        return
    if not settings["sec_cols"]:
        st.error("Column selection could not be determined. Check your files.")
        return

    try:
        with st.spinner("Reading files…"):
            df_main = read_file(main_file, sheet_name=main_sheet)

        main_col = settings["main_col"] or detect_company_col(df_main.columns.tolist())
        df_main_valid = df_main.dropna(subset=[main_col]).reset_index(drop=True)
        main_values = df_main_valid[main_col].astype(str).tolist()

        with st.spinner("Merging secondary lists…"):
            frames = _merge_secondary(secondary_files, settings["sec_cols"], settings["sec_sheets"])

        if not frames:
            st.error("Could not read any of the secondary files.")
            return

        df_sec = pd.concat(frames, ignore_index=True, sort=False)
        sec_count_before_dedup = len(df_sec)

        with st.spinner("Deduping merged secondary list…"):
            dedup_col = (settings["dedup_col"] if settings["dedup_col"] in df_sec.columns
                         else COMPARE_COL)
            dedup_values = df_sec[dedup_col].fillna("").astype(str).tolist()
            internal_dups = find_internal_duplicates(dedup_values, threshold)
            dup_ids = {d["id_dup"] for d in internal_dups}
            df_sec = df_sec.iloc[[i for i in range(len(df_sec)) if i not in dup_ids]].reset_index(drop=True)

        with st.spinner("Comparing against main list…"):
            keep_main_idx, keep_sec_idx, overlaps = find_symmetric_overlap(
                main_values, df_sec[COMPARE_COL].tolist(), threshold
            )

        df_result = pd.concat(
            [df_main_valid.iloc[keep_main_idx].copy(),
             df_sec.iloc[keep_sec_idx].drop(columns=[COMPARE_COL]).copy()],
            ignore_index=True, sort=False,
        )

        if settings["output_cols"]:
            df_result = df_result[[c for c in settings["output_cols"] if c in df_result.columns]]

        st.session_state[RESULT_KEY] = {
            "df": df_result,
            "main_count": len(main_values),
            "sec_count": sec_count_before_dedup,
            "internal_dups": internal_dups,
            "overlaps": overlaps,
            "main_file_name": getattr(main_file, "name", "list_diff"),
        }

    except Exception as e:
        st.error(f"Something went wrong: {e}")
        st.exception(e)


def _download_stem(main_file_name: str) -> str:
    stem = main_file_name
    for ext in ('.xlsx', '.xls', '.csv'):
        if stem.lower().endswith(ext):
            stem = stem[:-len(ext)]
            break
    return f"{stem}_list_diff"


def _render_downloads(df_result, main_file_name):
    col_csv, col_excel = st.columns(2, gap="small")
    stem = _download_stem(main_file_name)

    with col_csv:
        st.download_button(
            label="&#11015;  Download CSV",
            data=df_result.to_csv(index=False).encode("utf-8-sig"),
            file_name=output_filename(stem, ".csv"),
            mime="text/csv",
            use_container_width=True,
        )
    with col_excel:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df_result.to_excel(writer, index=False, sheet_name="List Diff")
        st.download_button(
            label="&#11015;  Download Excel",
            data=buf.getvalue(),
            file_name=output_filename(stem, ".xlsx"),
            mime=EXCEL_MIME,
            use_container_width=True,
        )


def _render_pair_list(title, marker, pairs, left_key, right_key, arrow):
    """A scored-pair review list — the dedup pairs and the redundant pairs share this shape."""
    st.markdown("")
    w.plain_header(title, marker)
    for pair in sorted(pairs, key=lambda p: -p["score"]):
        w.match_card(pair[left_key], arrow, pair[right_key], f'{pair["score"]}%',
                     score_class="high" if pair["score"] >= 90 else "")


def _render_results(result):
    df_result = result["df"]

    w.plain_header("Result")
    s1, s2, s3, s4, s5 = st.columns(5, gap="small")
    w.stat_box(s1, result["main_count"], "Main rows")
    w.stat_box(s2, result["sec_count"], "Secondary rows (merged)")
    w.stat_box(s3, len(result["internal_dups"]), "Secondary dups removed", warn=True)
    w.stat_box(s4, len(result["overlaps"]), "Redundant pairs removed", warn=True)
    w.stat_box(s5, len(df_result), "Unique rows")

    st.markdown("")
    w.preview_table(df_result)

    st.markdown("")
    _render_downloads(df_result, result["main_file_name"])

    if result["internal_dups"]:
        _render_pair_list("Duplicates merged within the secondary lists", "&#9664;&#9654;",
                          result["internal_dups"], "name_keeper", "name_dup",
                          " &lArr; dup &mdash; ")

    if result["overlaps"]:
        _render_pair_list("Redundant entries removed from both lists", "&#8635;",
                          result["overlaps"], "name_a", "name_b", " &harr; ")


def render() -> None:
    """Draw the whole List Diff tab."""
    w.tab_description(TAB_DESCRIPTION)

    main_file, secondary_files = _upload_inputs()
    main_sheet = _main_sheet_picker(main_file)

    settings = {"main_col": None, "dedup_col": None, "output_cols": None,
                "sec_cols": {}, "sec_sheets": {}}
    if main_file and secondary_files:
        settings = _column_settings(main_file, secondary_files, main_sheet)

    w.section_header("06", "Match sensitivity")
    threshold = w.threshold_slider("ld_threshold", THRESHOLD_CAPTION)
    st.markdown("")

    if st.button("&#9889;  Run List Diff", type="primary", use_container_width=True):
        _run(main_file, secondary_files, main_sheet, settings, threshold)

    result = st.session_state.get(RESULT_KEY)
    if result:
        _render_results(result)
    elif not (main_file and secondary_files):
        w.empty_state(
            'Upload your main list and two or more secondary lists, then hit '
            '<strong style="color:#00ff8866">Run List Diff</strong>.',
            'Supports .xlsx, .xls, and .csv')
