"""Tab 1 — Screen & Append.

One pass: upload the main list and the new lists, fuzzy-match the new company
names against the main list and against each other, map whatever survives onto
the main list's columns, and download the combined result.

Screening runs only on the Run button; everything below it is recomputed from the
cached result on every rerun, so a Keep click or a changed mapping feeds straight
through to the download without re-reading a file.
"""

import pandas as pd
import streamlit as st

from ..core.columns import default_key_cols, detect_company_col
from ..core.combine import (
    BOOKKEEPING_COLS,
    MAIN_LIST_ORIGIN,
    NAME_COL,
    SRC_FILE_COL,
    SRC_ROW_COL,
    build_combined,
    name_findings,
)
from ..core.files import get_excel_sheets, read_file
from ..core.matching import find_internal_duplicates, find_matches
from ..core.text import clean_for_output, output_filename
from . import widgets as w
from .state import (
    DOWNLOAD_KEY,
    DUPS_OPEN_KEY,
    exempt_row,
    get_visible_results,
    store_results,
    unexempt_row,
)

TAB_DESCRIPTION = """
  <strong>Screen &amp; Append</strong> — upload your main list and the new lists once.
  A fuzzy company-name match flags what already exists, and everything that survives
  is mapped straight onto the main list's columns. Review the name matches, in-list
  duplicates and duplicate emails, then download the combined list — no intermediate
  download and re-upload.
"""

THRESHOLD_CAPTION = (
    "Scores &ge; {threshold} are flagged as matches &nbsp;&mdash;&nbsp; lower threshold "
    "catches more variations like <em>Acme Corp</em> vs <em>Acme Corporation</em>")

PREVIEW_LIMIT = 200


def _upload_inputs():
    """Step 01/02 — the main list and the new lists. Returns (main_file, new_files)."""
    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        w.upload_label("01", "Main list")
        w.caption("Screened against <em>and</em> appended to.")
        main_file = st.file_uploader("Main list", type=["xlsx", "xls", "csv"], key="main",
                                     label_visibility="collapsed")
        if isinstance(main_file, list):
            if len(main_file) > 1:
                st.warning("Only one file is allowed here. Using the first file.")
            main_file = main_file[0] if main_file else None

    with col_b:
        w.upload_label("02", "New lists")
        w.caption("Screened, then appended.")
        new_files = st.file_uploader("New lists to screen and append", type=["xlsx", "xls", "csv"],
                                     key="new", accept_multiple_files=True,
                                     label_visibility="collapsed")
        if not isinstance(new_files, list):
            new_files = [new_files] if new_files else []

    st.markdown("")
    return main_file, new_files


def _sheet_pickers(main_file, new_files):
    """A sheet selector per multi-sheet Excel upload. Returns (main_sheet, {filename: sheet})."""
    main_sheet, new_sheets = 0, {}

    picks = []   # (label, sheets, widget_key, target, filename)
    if main_file and not main_file.name.lower().endswith('.csv'):
        sheets = get_excel_sheets(main_file)
        if sheets:
            picks.append(("Sheet — Main list", sheets, "main_sheet", "main", None))
    for nf in new_files:
        if not nf.name.lower().endswith('.csv'):
            sheets = get_excel_sheets(nf)
            if sheets:
                picks.append((f"Sheet — {nf.name}", sheets, f"sa_sheet_{nf.name}", "new", nf.name))

    if picks:
        for i in range(0, len(picks), 3):
            row = picks[i:i + 3]
            cols = st.columns(len(row), gap="small")
            for col, (label, sheets, key, target, fname) in zip(cols, row):
                with col:
                    chosen = st.selectbox(label, sheets, key=key)
                    if target == "main":
                        main_sheet = chosen
                    else:
                        new_sheets[fname] = chosen
        st.markdown("")

    return main_sheet, new_sheets


def _read_headers(main_file, new_files, main_sheet, new_sheets):
    """Column names only (nrows=0), so the pickers below can be built cheaply."""
    main_cols, new_cols_map = [], {}

    if main_file:
        try:
            main_file.seek(0)
            main_cols = read_file(main_file, nrows=0, sheet_name=main_sheet).columns.tolist()
            main_file.seek(0)
        except Exception:
            st.warning(f"Could not read columns from {main_file.name}.")

    for nf in new_files:
        try:
            nf.seek(0)
            new_cols_map[nf.name] = read_file(
                nf, nrows=0, sheet_name=new_sheets.get(nf.name, 0)).columns.tolist()
            nf.seek(0)
        except Exception:
            new_cols_map[nf.name] = []

    # Every column offered by any new list, in first-file-first order.
    union = []
    for nf in new_files:
        for c in new_cols_map.get(nf.name, []):
            if c not in union and c not in BOOKKEEPING_COLS:
                union.append(c)

    return main_cols, new_cols_map, union


def _screening_settings(main_cols, new_cols_map, new_files):
    """Steps 03/04 — company columns and match sensitivity.

    Returns (do_screening, main_col_choice, {filename: company column}, threshold).
    """
    do_screening, main_col_choice, new_col_choices, threshold = True, None, {}, 70

    w.section_header("03", "Columns to compare")
    do_screening = st.checkbox(
        "Screen the new rows against the main list (fuzzy company-name match)",
        value=True,
        key="sa_do_screen",
        help="Uncheck to append everything without name screening — the email duplicate check still runs.",
    )

    if do_screening:
        w.caption("The company column is picked per list, so the new lists do not have to name it the same way.")
        st.markdown("")

        # main list first, then one picker per new list, laid out two per row
        pickers = [("Main list — company column", main_cols, None)]
        for nf in new_files:
            file_cols = [c for c in new_cols_map.get(nf.name, []) if c not in BOOKKEEPING_COLS]
            if file_cols:
                pickers.append((f"{nf.name} — company column", file_cols, nf.name))

        for i in range(0, len(pickers), 2):
            pair = pickers[i:i + 2]
            cols = st.columns(2, gap="medium")
            for col, (label, options, fname) in zip(cols, pair):
                with col:
                    default = detect_company_col(options)
                    picked = st.selectbox(label, options, index=options.index(default))
                    if fname is None:
                        main_col_choice = picked
                    else:
                        new_col_choices[fname] = picked

        if len(new_files) > 1:
            st.info(f"{len(new_files)} files are screened together — against the main list and "
                    f"against each other — then each file's rows are mapped with its own mapping below.")

        st.markdown("")
        w.section_header("04", "Match sensitivity")
        threshold = w.threshold_slider("sa_threshold", THRESHOLD_CAPTION)

    st.markdown("")
    return do_screening, main_col_choice, new_col_choices, threshold


def _mapping_settings(main_file, main_cols, new_files, new_cols_map,
                      main_col_choice, new_col_choices):
    """Steps 05/06 — per-file column mapping and the identity key columns."""
    w.section_header("05", "Column mapping")
    w.caption("For every column in the main list, pick the matching column from the new list — "
              "or skip it. Identically named columns are matched automatically.")
    st.markdown("")

    mappings = {}
    for nf in new_files:
        file_cols = [c for c in new_cols_map.get(nf.name, []) if c not in BOOKKEEPING_COLS]
        with st.expander(f"**{nf.name}**", expanded=len(new_files) == 1):
            if not file_cols:
                st.warning(f"Could not read columns from {nf.name}.")
                continue

            preselect = ({main_col_choice: new_col_choices[nf.name]}
                         if main_col_choice and new_col_choices.get(nf.name) else None)
            mappings[nf.name] = w.render_column_mapping(
                f"Mapping to {main_file.name}", main_cols, file_cols, f"sa_map_{nf.name}",
                preselect=preselect,
            )

    st.markdown("")
    w.section_header("06", "Duplicate keys")
    w.caption("Besides the company name, treat these main-list columns as identity: a new row whose "
              "value is already present is a duplicate. Email-domain columns ignore anything before "
              "the @, and websites and profile links ignore http/https, www and trailing paths.")
    key_cols = st.multiselect(
        "Columns that identify a company",
        main_cols,
        default=default_key_cols(main_cols),
        label_visibility="collapsed",
    )
    if not key_cols:
        w.caption("No identity keys selected &mdash; only the company name is compared.")
    st.markdown("")

    return mappings, key_cols


def _signature(main_file, new_files, threshold, do_screening,
               main_col_choice, new_col_choices, key_cols):
    """What a stored result was computed from — used both to reset the review
    state on a genuinely new run and to warn when the inputs have moved on."""
    return {
        "main_file":  getattr(main_file, "name", ""),
        "main_size":  getattr(main_file, "size", None),
        "new_files":  [getattr(f, "name", "") for f in new_files],
        "new_size":   sum(getattr(f, "size", 0) for f in new_files),
        "threshold":  threshold if do_screening else None,
        "screened":   do_screening,
        "main_col":   main_col_choice,
        "new_cols":   new_col_choices,
        "key_cols":   list(key_cols),
    }


def _read_new_lists(new_files, new_sheets, new_col_choices):
    """Read every new list and stamp on the bookkeeping columns.

    Returns (df_new, {filename: the company column it was screened on}).
    """
    frames, new_cols_by_file = [], {}
    for nf in new_files:
        nf.seek(0)
        df = read_file(nf, sheet_name=new_sheets.get(nf.name, 0))
        df[SRC_FILE_COL] = nf.name
        df[SRC_ROW_COL]  = list(range(1, len(df) + 1))

        company_col = new_col_choices.get(nf.name)
        if company_col is None:
            company_col = detect_company_col([c for c in df.columns if c not in BOOKKEEPING_COLS])
        new_cols_by_file[nf.name] = company_col
        df[NAME_COL] = df[company_col] if company_col in df.columns else None
        frames.append(df)

    df_new = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
    return df_new, new_cols_by_file


def _run(main_file, new_files, main_sheet, new_sheets, mappings,
         do_screening, main_col_choice, new_col_choices, threshold, key_cols):
    """Read, screen and cache. Everything downstream reads from session state."""
    if not main_file or not new_files:
        st.error("Please upload the main list and at least one new list before running.")
        return
    if not mappings:
        st.error("Column mapping could not be determined. Check your files.")
        return

    try:
        with st.spinner("Reading files…"):
            main_file.seek(0)
            df_main = read_file(main_file, sheet_name=main_sheet)
            df_new, new_cols_by_file = _read_new_lists(new_files, new_sheets, new_col_choices)

        main_col = main_col_choice or detect_company_col(df_main.columns.tolist())

        if do_screening:
            main_names   = df_main[main_col].dropna().astype(str).tolist()
            df_new_valid = df_new.dropna(subset=[NAME_COL]).reset_index(drop=True)
            new_names    = df_new_valid[NAME_COL].astype(str).tolist()

            with st.spinner("Screening against the main list…"):
                matches, unique_new = find_matches(main_names, new_names, threshold)

            with st.spinner("Checking for duplicates within the new lists…"):
                internal_dups = find_internal_duplicates(new_names, threshold)
        else:
            main_names    = []
            df_new_valid  = df_new.reset_index(drop=True)
            new_names     = (df_new_valid[NAME_COL].astype(str).tolist()
                             if NAME_COL in df_new_valid.columns else [""] * len(df_new_valid))
            matches       = []
            unique_new    = list(range(len(df_new_valid)))
            internal_dups = []

        # store_results clears the exemptions itself when the inputs move on
        store_results({
            "signature":        _signature(main_file, new_files, threshold, do_screening,
                                           main_col_choice, new_col_choices, key_cols),
            "main_names":       main_names,
            "new_names":        new_names,
            "matches":          matches,
            "unique_new":       unique_new,
            "internal_dups":    internal_dups,
            "df_new_valid":     df_new_valid,
            "new_cols_by_file": new_cols_by_file,
            "main_col":         main_col,
            "screened":         do_screening,
            "df_main":          df_main,
            "main_name":        main_file.name,
            "main_row_count":   len(df_main),
        })

    except Exception as e:
        st.error(f"Something went wrong: {e}")
        st.exception(e)


def _kept_rows(results):
    """The rows that got past the name comparison, cleaned for output.

    Cleaned the way the old Unique Rows download was, but only when screening
    ran: only then is the company column one the user actually picked.
    """
    kept = results["df_new_valid"].loc[results["kept_ids"]].copy()
    if results.get("screened", True) and NAME_COL in kept.columns:
        kept[NAME_COL] = kept[NAME_COL].apply(clean_for_output)
        kept = kept[kept[NAME_COL].astype(str).str.strip() != ""]
        # Push the cleaned name back into each file's own company column —
        # that is the column this file's mapping reads from.
        for fname, company_col in results.get("new_cols_by_file", {}).items():
            if company_col in kept.columns:
                mask = kept[SRC_FILE_COL] == fname
                kept.loc[mask, company_col] = kept.loc[mask, NAME_COL]
    return kept.sort_index()


def _collect_findings(results, built, was_screened, exempt):
    """Name findings plus key findings, one verdict per row."""
    findings = (name_findings(results, exempt) if was_screened else []) + built["findings"]
    by_row = {}
    for f in findings:
        by_row.setdefault(f["row_id"], f)   # one verdict per row: the first check that fired
    return list(by_row.values())


def _render_summary(results, kept, appended, active, forced):
    checked = len(results["new_names"])
    # Two ways a row can carry no usable name: find_matches never bucketed it
    # (its normalised name was empty), or clean_for_output emptied it later.
    no_name = ((len(results["kept_ids"]) - len(kept))
               + (checked - len(results["usable_ids"])))
    vs_main = len([f for f in active if f["match_origin"] is MAIN_LIST_ORIGIN])
    vs_new  = len(active) - vs_main

    bits = [f"<strong>{len(active):,}</strong> duplicates "
            f"({vs_main:,} against the main list, {vs_new:,} within the new lists)"]
    if no_name:
        bits.append(f"<strong>{no_name:,}</strong> with no usable company name")
    if forced:
        bits.append(f"<strong>{len(forced):,}</strong> forced in")

    w.caption(f"{checked:,} new rows checked against "
              f"{results.get('main_row_count', 0):,} in the main list and against each other &mdash; "
              + ", ".join(bits)
              + f", <strong>{len(appended):,}</strong> appended.")


def _render_review_list(findings, active, forced):
    """The one review list: every flagged row, with a Keep / Remove toggle."""
    label = f"Duplicates left out ({len(active)})"
    if forced:
        label += f" — {len(forced)} forced in"

    with st.expander(label, expanded=bool(st.session_state.get(DUPS_OPEN_KEY))):
        w.caption("Each row is listed with the check that caught it and the entry it collided with. "
                  "<strong>Keep</strong> forces one into the output, whichever check flagged it.")
        st.markdown("")
        for f in sorted(findings, key=lambda f: (f["kind"] != "key", -(f["score"] or 100), f["row_id"])):
            where = ("the main list" if f["match_origin"] is MAIN_LIST_ORIGIN
                     else f["match_origin"])
            chip = f"{f['key']} {f['score']:.0f}%" if f["score"] is not None else f["key"]
            left, right = st.columns([0.82, 0.18])
            with left:
                w.match_card(
                    f["row_label"], " &rarr; ",
                    f'{f["match_label"]} <span style="color:var(--tx-lo)">in {where}</span>',
                    chip, dim=f["exempt"])
            with right:
                if f["exempt"]:
                    st.button("Remove", key=f"unexempt_{f['row_id']}", type="secondary",
                              on_click=unexempt_row, args=(f["row_id"],))
                else:
                    st.button("Keep", key=f"exempt_{f['row_id']}", type="secondary",
                              on_click=exempt_row, args=(f["row_id"],))
    st.markdown("")


def _render_result(df_main, df_result, appended, active, main_name):
    w.plain_header(f"Result &mdash; {main_name}")
    s1, s2, s3, s4 = st.columns(4, gap="small")
    w.stat_box(s1, len(df_main), "Main rows")
    w.stat_box(s2, len(appended), "Appended rows")
    w.stat_box(s3, len(active), "Duplicates out", warn=True)
    w.stat_box(s4, len(df_result), "Total rows")

    st.markdown("")
    w.caption(f"The new rows as they are written into <strong>{main_name}</strong> &mdash; its columns, "
              f"filled from your mapping. Anything you left on &ldquo;skip&rdquo; stays empty, and "
              f"columns that exist only in the new lists are not carried over.")
    st.dataframe(appended.head(PREVIEW_LIMIT), use_container_width=True, hide_index=True)
    if len(appended) > PREVIEW_LIMIT:
        w.caption(f"Showing first {PREVIEW_LIMIT} of {len(appended):,} new rows.")

    # Kept in session state so the button always has its bytes to hand,
    # whichever rerun it ends up being clicked on.
    st.session_state[DOWNLOAD_KEY] = {
        "data": df_result.to_csv(index=False).encode("utf-8-sig"),
        "name": output_filename(main_name, ".csv"),
        "mime": "text/csv",
    }

    download = st.session_state.get(DOWNLOAD_KEY)
    if download:
        st.markdown("")
        st.download_button(
            label="&#11015;  Download combined list (CSV)",
            data=download["data"],
            file_name=download["name"],
            mime=download["mime"],
            use_container_width=True,
            key="sa_combined_dl",
        )
        st.markdown("")


def _render_results(results, mappings, key_cols, main_file, new_files, current_signature):
    """Rebuild the combined list from the cached screening and render everything below Run."""
    was_screened = results.get("screened", True)
    exempt       = results["exempt"]
    df_main      = results.get("df_main")
    main_name    = results.get("main_name") or "main list"

    if main_file and new_files and results["signature"] != current_signature:
        st.warning("Inputs or settings have changed since this result was produced — "
                   "hit **Run** again to refresh it.")

    kept = _kept_rows(results)

    if df_main is None:
        st.info("Hit **Run** to build the combined list.")
        return
    if not mappings:
        st.info("Re-upload the new lists to restore the column mapping, then run again.")
        return

    # ── One duplicate pass: names from the cached screening, identity keys from
    #    the mapped rows. Recomputed every rerun, so a Keep click or a changed
    #    mapping feeds straight through to the download.
    if SRC_FILE_COL in kept.columns:
        sources = [(str(fname), group) for fname, group in kept.groupby(SRC_FILE_COL, sort=False)]
    else:
        sources = [(new_files[0].name if new_files else "new list", kept)]

    main_name_col = results.get("main_col") or detect_company_col(df_main.columns.tolist())
    built = build_combined(df_main, main_name_col, mappings, key_cols, sources, exempt)

    findings = _collect_findings(results, built, was_screened, exempt)
    active   = [f for f in findings if not f["exempt"]]
    forced   = [f for f in findings if f["exempt"]]

    _render_summary(results, kept, built["appended"], active, forced)
    if not was_screened:
        w.caption("Name comparison is switched off for this run — only the identity keys above were compared.")
    st.markdown("")

    if findings:
        _render_review_list(findings, active, forced)

    _render_result(df_main, built["df_result"], built["appended"], active, main_name)


def render() -> None:
    """Draw the whole Screen & Append tab."""
    w.tab_description(TAB_DESCRIPTION)

    main_file, new_files = _upload_inputs()
    main_sheet, new_sheets = _sheet_pickers(main_file, new_files)
    main_cols, new_cols_map, new_cols_union = _read_headers(
        main_file, new_files, main_sheet, new_sheets)

    do_screening, main_col_choice, new_col_choices, threshold = True, None, {}, 70
    if main_cols and new_cols_union:
        do_screening, main_col_choice, new_col_choices, threshold = _screening_settings(
            main_cols, new_cols_map, new_files)

    mappings, key_cols = {}, []
    if main_cols and new_files:
        mappings, key_cols = _mapping_settings(
            main_file, main_cols, new_files, new_cols_map, main_col_choice, new_col_choices)

    if st.button("&#9889;  Run &mdash; Screen &amp; Append", type="primary", use_container_width=True):
        _run(main_file, new_files, main_sheet, new_sheets, mappings,
             do_screening, main_col_choice, new_col_choices, threshold, key_cols)

    results = get_visible_results()
    if results:
        _render_results(
            results, mappings, key_cols, main_file, new_files,
            _signature(main_file, new_files, threshold, do_screening,
                       main_col_choice, new_col_choices, key_cols),
        )
    else:
        w.empty_state(
            'Upload your main list and the new lists, then hit '
            '<strong style="color:#00ff8866">Run &mdash; Screen &amp; Append</strong>.',
            'Screening, duplicate checks and the merge all happen in one pass '
            '&nbsp;&middot;&nbsp; .xlsx, .xls, .csv')
