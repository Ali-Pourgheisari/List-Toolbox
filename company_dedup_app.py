import streamlit as st
import pandas as pd
import re
import io
import csv
from rapidfuzz import fuzz, process

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="List Screener",
    page_icon="🏢",
    layout="wide",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
  }

  .stApp {
    background: #080b12;
    color: #c9d1e0;
  }

  h1, h2, h3 { font-family: 'JetBrains Mono', monospace !important; }

  /* ── Hero ── */
  .hero {
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, #0d1117 0%, #0f1923 60%, #0a1a14 100%);
    border: 1px solid #1e2d3d;
    border-radius: 12px;
    padding: 2.4rem 2.8rem;
    margin-bottom: 2.2rem;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(0,255,136,0.12) 0%, transparent 70%);
    pointer-events: none;
  }
  .hero-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #00e07a;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
  }
  .hero h1 {
    color: #f0f4ff;
    font-size: 1.85rem;
    margin: 0 0 0.5rem 0;
    letter-spacing: -0.02em;
  }
  .hero h1 span { color: #00ff88; }
  .hero p { color: #5a6a7e; margin: 0; font-size: 0.92rem; line-height: 1.6; }

  /* ── Upload panels ── */
  .upload-panel {
    background: linear-gradient(160deg, #0d1117 0%, #0c1520 100%);
    border: 1px solid #1e2d3d;
    border-radius: 10px;
    padding: 1.4rem 1.6rem 1rem;
    height: 100%;
  }
  .upload-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #00e07a;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  /* ── Section headers ── */
  .section-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #3a4a5e;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    border-bottom: 1px solid #141e2a;
    padding-bottom: 0.55rem;
    margin: 1.8rem 0 1.1rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  /* ── Stat boxes ── */
  .stat-box {
    background: linear-gradient(160deg, #0d1420 0%, #0a1018 100%);
    border: 1px solid #1a2535;
    border-radius: 10px;
    padding: 1.3rem 1rem;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .stat-box::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #00ff8833, transparent);
  }
  .stat-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.1rem;
    font-weight: 700;
    color: #00ff88;
    line-height: 1;
    margin-bottom: 0.35rem;
  }
  .stat-num.warn { color: #ff6b35; }
  .stat-label {
    font-size: 0.7rem;
    color: #3a4a5e;
    text-transform: uppercase;
    letter-spacing: 0.14em;
  }

  /* ── Match cards ── */
  .match-card {
    background: linear-gradient(135deg, #0d1520 0%, #0a1018 100%);
    border: 1px solid #1a2535;
    border-radius: 8px;
    padding: 0.65rem 1rem;
    margin-bottom: 0.35rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: border-color 0.15s;
  }
  .match-card:hover { border-color: #2a3d52; }
  .match-score {
    color: #ff6b35;
    font-weight: 600;
    background: rgba(255,107,53,0.1);
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    white-space: nowrap;
    margin-left: 0.8rem;
    flex-shrink: 0;
  }
  .match-score.high { color: #00ff88; background: rgba(0,255,136,0.08); }
  .match-names { color: #7a8a9e; overflow: hidden; }
  .match-main  { color: #c9d1e0; font-weight: 500; }
  .match-arrow { color: #2a3a4e; margin: 0 0.4rem; }

  /* ── Threshold panel ── */
  .threshold-panel {
    background: linear-gradient(160deg, #0d1117 0%, #0c1520 100%);
    border: 1px solid #1e2d3d;
    border-radius: 10px;
    padding: 1.2rem 1.6rem 0.8rem;
    margin-bottom: 0.5rem;
  }

  /* ── Streamlit overrides ── */
  div[data-testid="stFileUploader"] {
    background: transparent !important;
    border: 1px dashed #1e2d3d !important;
    border-radius: 8px !important;
    padding: 0.6rem !important;
  }
  div[data-testid="stFileUploader"]:hover {
    border-color: #00ff8844 !important;
  }

  .stSlider > div > div > div { background: #00ff88 !important; }
  [data-testid="stSlider"] [data-testid="stTickBarMin"],
  [data-testid="stSlider"] [data-testid="stTickBarMax"] { color: #3a4a5e !important; }

  .stButton > button {
    background: linear-gradient(135deg, #00ff88, #00cc6e) !important;
    color: #060a0e !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.2rem !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.04em !important;
    width: auto !important;
    box-shadow: 0 0 20px rgba(0,255,136,0.15) !important;
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, #00ff99, #00e07a) !important;
    box-shadow: 0 0 28px rgba(0,255,136,0.25) !important;
  }

  .stButton > button[data-testid="baseButton-primary"] {
    min-height: 2.4rem !important;
  }

  .stButton > button[data-testid="baseButton-secondary"] {
    background: #0d1520 !important;
    color: #7a8a9e !important;
    border: 1px solid #1e2d3d !important;
    box-shadow: none !important;
    padding: 0.22rem 0.5rem !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.02em !important;
    min-height: 1.8rem !important;
    width: 100% !important;
    border-radius: 6px !important;
  }
  .stButton > button[data-testid="baseButton-secondary"]:hover {
    background: #131e2e !important;
    color: #c9d1e0 !important;
    border-color: #2a3d52 !important;
  }

  .stDataFrame {
    border: 1px solid #1a2535 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
  }

  .stAlert { border-radius: 8px !important; }

  div[data-testid="stDownloadButton"] button {
    background: #0d1520 !important;
    color: #00ff88 !important;
    border: 1px solid #1e3a28 !important;
    box-shadow: none !important;
    border-radius: 7px !important;
    font-size: 0.78rem !important;
  }
  div[data-testid="stDownloadButton"] button:hover {
    background: #0f1e2a !important;
    border-color: #00ff8844 !important;
  }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

SUFFIXES = re.compile(
    r'\b(inc|incorporated|ltd|limited|llc|llp|lp|plc|gmbh|ag|sa|sas|bv|nv|'
    r'corp|corporation|co|company|group|holding|holdings|international|intl|'
    r'ug|kgaa|kg|eg|oy|ab|as|aps|srl|sro|sl|bvba|sprl|'
    r'technologies|technology|tech|solutions|services|systems|'
    r'consulting|ventures|partners|associates|enterprises)\b',
    re.IGNORECASE
)

RESULTS_SESSION_KEY = "screener_results"
MOVED_SESSION_KEY = "screener_moved_match_ids"

def clean_for_output(name: str) -> str:
    """Remove numbers and demo tags for the output file."""
    if not isinstance(name, str):
        return ""
    n = name.strip()
    n = re.sub(r'\(\s*[Dd]emo[^)]*\)', '', n)   # (Demo Account), (Demo: 34708)
    n = re.sub(r'\b\d{4,}\b', '', n)             # standalone 4+ digit IDs
    n = re.sub(r'\s*\d+\s*$', '', n)             # trailing numbers
    n = re.sub(r'\(\s*\)', '', n)                # leftover empty parentheses
    n = re.sub(r'\s+', ' ', n).strip()
    return n

def normalize(name: str) -> str:
    if not isinstance(name, str):
        return ""
    n = name.lower().strip()
    n = re.sub(r'[^\w\s]', ' ', n)   # punctuation → space
    n = SUFFIXES.sub('', n)           # remove legal suffixes
    n = re.sub(r'\s*\d+\s*$', '', n) # trailing numbers
    n = re.sub(r'\b\d{4,}\b', '', n) # standalone ID numbers
    n = re.sub(r'\s+', ' ', n).strip()
    return n

def detect_company_col(columns) -> str:
    hints = ['company', 'name', 'organisation', 'organization', 'firm', 'account']
    for col in columns:
        if any(h in col.lower() for h in hints):
            return col
    return columns[0]

def read_file(f, nrows=None):
    if f.name.endswith('.csv'):
        sample = f.read(4096).decode('utf-8', errors='replace')
        f.seek(0)
        try:
            sep = csv.Sniffer().sniff(sample, delimiters=',;').delimiter
        except csv.Error:
            sep = ','
        for encoding in ('utf-8', 'cp1252', 'latin-1'):
            try:
                df = pd.read_csv(f, sep=sep, nrows=nrows, encoding=encoding)
                return df
            except UnicodeDecodeError:
                f.seek(0)
        return pd.read_csv(f, sep=sep, nrows=nrows, encoding='latin-1', encoding_errors='replace')
    return pd.read_excel(f, nrows=nrows)

def find_matches(main_names, new_names, threshold):
    """
    For each name in new_names, check if a fuzzy match exists in main_names.
    Returns:
      matches    – list of dicts with id, raw_name, matched_main_name, score
      unique_new – list of new_names with no match
    """
    norm_main = [normalize(n) for n in main_names]
    matches, unique_new = [], []

    for idx, raw in enumerate(new_names):
        norm = normalize(raw)
        if not norm:
            continue
        result = process.extractOne(norm, norm_main, scorer=fuzz.token_sort_ratio)
        if result and result[1] >= threshold:
            matched_original = main_names[result[2]]
            matches.append({
                "id": idx,
                "raw_name": raw,
                "matched_main_name": matched_original,
                "score": result[1],
            })
        else:
            unique_new.append(idx)

    return matches, unique_new


def store_results(payload: dict) -> None:
    previous_payload = st.session_state.get(RESULTS_SESSION_KEY)
    previous_moved = list(st.session_state.get(MOVED_SESSION_KEY, []))
    st.session_state[RESULTS_SESSION_KEY] = payload
    if previous_payload and previous_payload.get("signature") == payload.get("signature"):
        st.session_state[MOVED_SESSION_KEY] = previous_moved
    else:
        st.session_state[MOVED_SESSION_KEY] = []


def get_visible_results():
    payload = st.session_state.get(RESULTS_SESSION_KEY)
    if not payload:
        return None

    moved_ids = set(st.session_state.get(MOVED_SESSION_KEY, []))
    promoted = [item for item in payload["matches"] if item["id"] in moved_ids]
    remaining_matches = [item for item in payload["matches"] if item["id"] not in moved_ids]
    unique_indices = payload["unique_new"] + [item["id"] for item in promoted]

    return {
        "signature": payload["signature"],
        "main_names": payload["main_names"],
        "new_names": payload["new_names"],
        "matches": remaining_matches,
        "promoted": promoted,
        "unique_indices": unique_indices,
        "df_new_valid": payload["df_new_valid"],
        "new_col": payload["new_col"],
    }


def promote_match(match_id: int) -> None:
    moved_ids = list(st.session_state.get(MOVED_SESSION_KEY, []))
    if match_id not in moved_ids:
        moved_ids.append(match_id)
        st.session_state[MOVED_SESSION_KEY] = moved_ids


def demote_match(match_id: int) -> None:
    moved_ids = list(st.session_state.get(MOVED_SESSION_KEY, []))
    if match_id in moved_ids:
        moved_ids.remove(match_id)
        st.session_state[MOVED_SESSION_KEY] = moved_ids


APPEND_NEW  = "— Add as new column —"
APPEND_SKIP = "— Skip —"

def append_lists(df_main, df_new, mapping):
    new_rows = {}
    for new_col, action in mapping.items():
        if action == APPEND_SKIP:
            continue
        elif action == APPEND_NEW:
            new_rows[new_col] = df_new[new_col].values
        else:
            new_rows[action] = df_new[new_col].values
    return pd.concat([df_main, pd.DataFrame(new_rows)], ignore_index=True)


# ── UI ────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">&#9632; Exclusion List Automation</div>
  <h1>List <span>Tools</span></h1>
  <p>Screen new entries against your database, or append and merge two lists with custom column mapping.</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["List Screener", "List Appender"])

# ── Tab 1: List Screener ───────────────────────────────────────────────────────
with tab1:

    # ── Upload ─────────────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        st.markdown('<div class="upload-label">&#9632;&nbsp; 01 &mdash; Main database</div>', unsafe_allow_html=True)
        main_file = st.file_uploader("Main database", type=["xlsx", "xls", "csv"], key="main",
                                      label_visibility="collapsed")

    with col_b:
        st.markdown('<div class="upload-label">&#9632;&nbsp; 02 &mdash; New companies</div>', unsafe_allow_html=True)
        new_file  = st.file_uploader("New companies to check", type=["xlsx", "xls", "csv"], key="new",
                                      label_visibility="collapsed")

    st.markdown("")

    # ── Column selection ────────────────────────────────────────────────────────
    main_col_choice    = None
    new_col_choice     = None
    output_col_choices = None

    if main_file and new_file:
        try:
            main_cols = read_file(main_file, nrows=0).columns.tolist()
            new_cols  = read_file(new_file,  nrows=0).columns.tolist()
            main_file.seek(0)
            new_file.seek(0)

            st.markdown('<div class="section-header">&#9632;&nbsp; 03 &mdash; Column to compare</div>', unsafe_allow_html=True)
            col_sel_a, col_sel_b = st.columns(2, gap="medium")
            with col_sel_a:
                default_main = detect_company_col(main_cols)
                main_col_choice = st.selectbox(
                    "Main database — company column",
                    main_cols,
                    index=main_cols.index(default_main),
                )
            with col_sel_b:
                default_new = detect_company_col(new_cols)
                new_col_choice = st.selectbox(
                    "New list — company column",
                    new_cols,
                    index=new_cols.index(default_new),
                )

            st.markdown("")
            st.markdown('<div class="section-header">&#9632;&nbsp; 04 &mdash; Output columns</div>', unsafe_allow_html=True)
            output_col_choices = st.multiselect(
                "Columns from the new list to include in the output",
                new_cols,
                default=[new_col_choice],
            )
            st.markdown("")
        except Exception:
            pass

    st.markdown('<div class="section-header">&#9632;&nbsp; 05 &mdash; Match sensitivity</div>', unsafe_allow_html=True)

    thresh_col, hint_col = st.columns([3, 1])
    with thresh_col:
        threshold = st.slider(
            "Match threshold",
            min_value=50, max_value=100, value=70,
            help="Lower = catches more variations. 70 is a good default.",
            label_visibility="collapsed"
        )
    with hint_col:
        st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:1.4rem;font-weight:700;color:#00ff88;text-align:center;padding-top:0.3rem'>{threshold}<span style='font-size:0.7rem;color:#3a4a5e;margin-left:2px'>/ 100</span></div>", unsafe_allow_html=True)

    st.markdown(f"<small style='color:#2a3a4e'>Scores &ge; {threshold} are flagged as matches &nbsp;&mdash;&nbsp; lower threshold catches more variations like <em>Acme Corp</em> vs <em>Acme Corporation</em></small>", unsafe_allow_html=True)
    st.markdown("")

    run = st.button("&#9889;  Run Screening", type="primary", use_container_width=True)

    if run:
        if not main_file or not new_file:
            st.error("Please upload both files before running.")
        else:
            try:
                with st.spinner("Reading files…"):
                    df_main = read_file(main_file)
                    df_new  = read_file(new_file)

                main_col = main_col_choice or detect_company_col(df_main.columns.tolist())
                new_col  = new_col_choice  or detect_company_col(df_new.columns.tolist())

                main_names   = df_main[main_col].dropna().astype(str).tolist()
                df_new_valid = df_new.dropna(subset=[new_col]).reset_index(drop=True)
                new_names    = df_new_valid[new_col].astype(str).tolist()

                with st.spinner("Screening…"):
                    matches, unique_new = find_matches(main_names, new_names, threshold)

                store_results({
                    "signature": {
                        "main_file": getattr(main_file, "name", ""),
                        "main_size": getattr(main_file, "size", None),
                        "new_file": getattr(new_file, "name", ""),
                        "new_size": getattr(new_file, "size", None),
                        "threshold": threshold,
                    },
                    "main_names": main_names,
                    "new_names": new_names,
                    "matches": matches,
                    "unique_new": unique_new,
                    "df_new_valid": df_new_valid,
                    "new_col": new_col,
                })

            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.exception(e)

    visible_results = get_visible_results()

    if visible_results:
        remaining_matches = visible_results["matches"]
        promoted          = visible_results["promoted"]
        unique_indices    = visible_results["unique_indices"]
        df_new_valid      = visible_results["df_new_valid"]
        new_col           = visible_results["new_col"]

        st.markdown('<div class="section-header">&#9632;&nbsp; Results</div>', unsafe_allow_html=True)

        s1, s2, s3, s4 = st.columns(4, gap="small")
        with s1:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{len(visible_results["main_names"]):,}</div><div class="stat-label">Main DB</div></div>', unsafe_allow_html=True)
        with s2:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{len(visible_results["new_names"]):,}</div><div class="stat-label">Checked</div></div>', unsafe_allow_html=True)
        with s3:
            st.markdown(f'<div class="stat-box"><div class="stat-num warn">{len(remaining_matches):,}</div><div class="stat-label">Matches</div></div>', unsafe_allow_html=True)
        with s4:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{len(unique_indices):,}</div><div class="stat-label">New &amp; Unique</div></div>', unsafe_allow_html=True)

        st.markdown("")

        if promoted:
            st.markdown(f"<small style='color:#777'>Manually promoted from matches: {len(promoted)}</small>", unsafe_allow_html=True)
            st.markdown("")

        left, right = st.columns([1.2, 1])

        with left:
            st.markdown('<div class="section-header">&#10003;&nbsp; Not matched &mdash; ready to add</div>', unsafe_allow_html=True)
            if unique_indices:
                cols = [c for c in (output_col_choices or [new_col]) if c in df_new_valid.columns] or [new_col]
                df_out = df_new_valid.iloc[unique_indices][cols].copy().reset_index(drop=True)
                df_out[new_col] = df_out[new_col].apply(clean_for_output)
                df_out = df_out[df_out[new_col].str.strip() != ""].reset_index(drop=True)
                st.dataframe(df_out, use_container_width=True, hide_index=True)

                if promoted:
                    st.markdown('<div class="section-header" style="margin-top:1.2rem">&#8626;&nbsp; Manually promoted from matches</div>', unsafe_allow_html=True)
                    for item in sorted(promoted, key=lambda row: -row["score"]):
                        p_left, p_right = st.columns([0.82, 0.18])
                        score_class = "high" if item["score"] >= 90 else ""
                        with p_left:
                            st.markdown(f"""
                            <div class="match-card">
                              <span class="match-names"><span class="match-main">{item["raw_name"]}</span><span class="match-arrow"> matched </span>{item["matched_main_name"]}</span>
                              <span class="match-score {score_class}">{item["score"]}%</span>
                            </div>""", unsafe_allow_html=True)
                        with p_right:
                            if st.button("Return", key=f"return_match_{item['id']}", type="secondary"):
                                demote_match(item["id"])
                                st.rerun()

                st.markdown("")
                dl_a, dl_b = st.columns(2, gap="small")
                csv_bytes = df_out.to_csv(index=False).encode("utf-8")
                with dl_a:
                    st.download_button(
                        label="&#11015;  Download CSV",
                        data=csv_bytes,
                        file_name="new_unique_companies.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                with dl_b:
                    excel_buf = io.BytesIO()
                    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                        df_out.to_excel(writer, index=False, sheet_name="Unique Companies")
                    st.download_button(
                        label="&#11015;  Download Excel",
                        data=excel_buf.getvalue(),
                        file_name="new_unique_companies.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
            else:
                st.info("All companies in the new file already exist in the main list.")

        with right:
            st.markdown('<div class="section-header">&#8635;&nbsp; Already in main list</div>', unsafe_allow_html=True)
            if remaining_matches:
                for match in sorted(remaining_matches, key=lambda item: -item["score"]):
                    row_left, row_right = st.columns([0.82, 0.18])
                    score_class = "high" if match["score"] >= 90 else ""
                    with row_left:
                        st.markdown(f"""
                        <div class="match-card">
                          <span class="match-names"><span class="match-main">{match["raw_name"]}</span><span class="match-arrow"> &rarr; </span>{match["matched_main_name"]}</span>
                          <span class="match-score {score_class}">{match["score"]}%</span>
                        </div>""", unsafe_allow_html=True)
                    with row_right:
                        if st.button("Move", key=f"move_match_{match['id']}", type="secondary"):
                            promote_match(match["id"])
                            st.rerun()
            else:
                st.success("No matches found.")

    else:
        st.markdown("""
        <div style='background:linear-gradient(135deg,#0d1117,#0c1520);border:1px dashed #1e2d3d;border-radius:10px;padding:2.5rem;text-align:center;margin-top:1rem'>
          <div style='font-family:JetBrains Mono,monospace;font-size:2rem;color:#1a2d3e;margin-bottom:0.8rem'>&#9632;</div>
          <div style='color:#3a4a5e;font-size:0.9rem'>Upload both files and hit <strong style="color:#00ff8866">Run Screening</strong> to get started.</div>
          <div style='color:#1e2d3d;font-size:0.78rem;margin-top:0.5rem'>Supports .xlsx, .xls, and .csv</div>
        </div>
        """, unsafe_allow_html=True)

# ── Tab 2: List Appender ───────────────────────────────────────────────────────
with tab2:

    # ── Upload ─────────────────────────────────────────────────────────────────
    ap_col_a, ap_col_b = st.columns(2, gap="medium")

    with ap_col_a:
        st.markdown('<div class="upload-label">&#9632;&nbsp; 01 &mdash; Main list</div>', unsafe_allow_html=True)
        ap_main_file = st.file_uploader("Main list", type=["xlsx", "xls", "csv"], key="ap_main",
                                         label_visibility="collapsed")

    with ap_col_b:
        st.markdown('<div class="upload-label">&#9632;&nbsp; 02 &mdash; List to append</div>', unsafe_allow_html=True)
        ap_new_file = st.file_uploader("List to append", type=["xlsx", "xls", "csv"], key="ap_new",
                                        label_visibility="collapsed")

    st.markdown("")

    # ── Column mapping ──────────────────────────────────────────────────────────
    ap_mapping = {}

    if ap_main_file and ap_new_file:
        try:
            ap_main_cols = read_file(ap_main_file, nrows=0).columns.tolist()
            ap_new_cols  = read_file(ap_new_file,  nrows=0).columns.tolist()
            ap_main_file.seek(0)
            ap_new_file.seek(0)

            st.markdown('<div class="section-header">&#9632;&nbsp; 03 &mdash; Column mapping</div>', unsafe_allow_html=True)
            st.markdown("<small style='color:#3a4a5e'>For each column in the file to append, choose the matching column in the main list — or add it as a new column.</small>", unsafe_allow_html=True)
            st.markdown("")

            MAP_OPTIONS = [APPEND_NEW, APPEND_SKIP] + ap_main_cols

            hdr_l, hdr_r = st.columns([1, 2])
            with hdr_l:
                st.markdown("<small style='color:#2a3a4e;font-family:JetBrains Mono,monospace;text-transform:uppercase;letter-spacing:0.1em'>Column in appended file</small>", unsafe_allow_html=True)
            with hdr_r:
                st.markdown("<small style='color:#2a3a4e;font-family:JetBrains Mono,monospace;text-transform:uppercase;letter-spacing:0.1em'>Maps to (in main list)</small>", unsafe_allow_html=True)

            for nc in ap_new_cols:
                auto_match = next((c for c in ap_main_cols if c.lower() == nc.lower()), None)
                default_idx = ap_main_cols.index(auto_match) + 2 if auto_match else 0
                map_l, map_r = st.columns([1, 2])
                with map_l:
                    st.markdown(f"<div style='padding:0.45rem 0;font-family:JetBrains Mono,monospace;font-size:0.8rem;color:#c9d1e0'>{nc}</div>", unsafe_allow_html=True)
                with map_r:
                    ap_mapping[nc] = st.selectbox(
                        nc,
                        MAP_OPTIONS,
                        index=default_idx,
                        key=f"ap_map_{nc}",
                        label_visibility="collapsed",
                    )

            st.markdown("")
        except Exception:
            pass

    ap_run = st.button("&#9889;  Append Lists", type="primary", use_container_width=True)

    if ap_run:
        if not ap_main_file or not ap_new_file:
            st.error("Please upload both files before running.")
        elif not ap_mapping:
            st.error("Column mapping could not be determined. Check your files.")
        else:
            try:
                with st.spinner("Reading files…"):
                    df_ap_main = read_file(ap_main_file)
                    df_ap_new  = read_file(ap_new_file)

                with st.spinner("Merging…"):
                    df_result = append_lists(df_ap_main, df_ap_new, ap_mapping)

                st.markdown('<div class="section-header">&#9632;&nbsp; Result</div>', unsafe_allow_html=True)
                ap_s1, ap_s2, ap_s3 = st.columns(3, gap="small")
                with ap_s1:
                    st.markdown(f'<div class="stat-box"><div class="stat-num">{len(df_ap_main):,}</div><div class="stat-label">Main rows</div></div>', unsafe_allow_html=True)
                with ap_s2:
                    st.markdown(f'<div class="stat-box"><div class="stat-num">{len(df_ap_new):,}</div><div class="stat-label">Appended rows</div></div>', unsafe_allow_html=True)
                with ap_s3:
                    st.markdown(f'<div class="stat-box"><div class="stat-num">{len(df_result):,}</div><div class="stat-label">Total rows</div></div>', unsafe_allow_html=True)

                st.markdown("")
                st.dataframe(df_result.head(200), use_container_width=True, hide_index=True)
                if len(df_result) > 200:
                    st.markdown(f"<small style='color:#3a4a5e'>Showing first 200 of {len(df_result):,} rows.</small>", unsafe_allow_html=True)

                st.markdown("")
                ap_dl_a, ap_dl_b = st.columns(2, gap="small")
                ap_csv = df_result.to_csv(index=False).encode("utf-8")
                with ap_dl_a:
                    st.download_button(
                        label="&#11015;  Download CSV",
                        data=ap_csv,
                        file_name="appended_list.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                with ap_dl_b:
                    ap_excel_buf = io.BytesIO()
                    with pd.ExcelWriter(ap_excel_buf, engine="openpyxl") as writer:
                        df_result.to_excel(writer, index=False, sheet_name="Appended List")
                    st.download_button(
                        label="&#11015;  Download Excel",
                        data=ap_excel_buf.getvalue(),
                        file_name="appended_list.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.exception(e)

    elif not (ap_main_file and ap_new_file):
        st.markdown("""
        <div style='background:linear-gradient(135deg,#0d1117,#0c1520);border:1px dashed #1e2d3d;border-radius:10px;padding:2.5rem;text-align:center;margin-top:1rem'>
          <div style='font-family:JetBrains Mono,monospace;font-size:2rem;color:#1a2d3e;margin-bottom:0.8rem'>&#9632;</div>
          <div style='color:#3a4a5e;font-size:0.9rem'>Upload both files to configure column mapping, then hit <strong style="color:#00ff8866">Append Lists</strong>.</div>
          <div style='color:#1e2d3d;font-size:0.78rem;margin-top:0.5rem'>Supports .xlsx, .xls, and .csv</div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("<br><hr style='border-color:#0d1520;margin-top:2rem'>", unsafe_allow_html=True)
st.markdown("<small style='color:#1e2d3d;font-family:JetBrains Mono,monospace;font-size:0.68rem'>RapidFuzz token_sort_ratio &mdash; handles reordering, abbreviations &amp; legal suffix differences. Promoted matches appear in downloads immediately.</small>", unsafe_allow_html=True)
