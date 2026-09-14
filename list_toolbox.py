import streamlit as st
import pandas as pd
import re
import io
import csv
from datetime import date
from rapidfuzz import fuzz, process

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="List Toolbox",
    page_icon="⚡",
    layout="wide",
)

# ── Styling ───────────────────────────────────────────────────────────────────

# Theme state (must be set before CSS injection)
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

def _toggle_theme():
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'

_is_dark = st.session_state.theme == 'dark'

# Base CSS with CSS variables (dark defaults)
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

  /* ── CSS Variables — dark defaults ── */
  :root {
    --bg:         #080b12;
    --bg-card:    #0d1117;
    --bg-card-b:  #0c1520;
    --bg-inset:   #0a1018;
    --bd:         #1e2d3d;
    --bd-dim:     #141e2a;
    --bd-hover:   #2a3d52;
    --tx:         #c9d1e0;
    --tx-h:       #f0f4ff;
    --tx-dim:     #5a6a7e;
    --tx-lo:      #3a4a5e;
    --tx-mid:     #7a8a9e;
    --accent:     #00ff88;
    --accent-2:   #00e07a;
    --accent-3:   #00cc6e;
    --accent-bg:  rgba(0,255,136,0.08);
    --accent-gl:  rgba(0,255,136,0.15);
    --accent-gl2: rgba(0,255,136,0.25);
    --accent-bd:  #1e3a28;
    --warn:       #ff6b35;
    --warn-bg:    rgba(255,107,53,0.1);
    --btn-tx:     #060a0e;
    --sec-bg:     #0d1520;
    --sec-bg-h:   #131e2e;
  }

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .stApp { background: var(--bg); color: var(--tx); }

  /* Reduce top padding so tabs appear high */
  .main .block-container { padding-top: 0.8rem !important; padding-bottom: 2rem !important; }
  header[data-testid="stHeader"] { height: 0 !important; visibility: hidden !important; }

  h1, h2, h3 { font-family: 'JetBrains Mono', monospace !important; }

  /* ── App logo ── */
  .app-logo {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--tx-h);
    letter-spacing: 0.04em;
    padding: 0.45rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    white-space: nowrap;
  }
  .app-logo .dot { color: var(--accent); }

  /* ── Tab description ── */
  .tab-desc {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-card-b) 100%);
    border: 1px solid var(--bd);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 0.85rem 1.2rem;
    margin-bottom: 1.6rem;
    font-size: 0.86rem;
    color: var(--tx-dim);
    line-height: 1.6;
  }
  .tab-desc strong { color: var(--tx); font-weight: 600; }

  /* ── Upload label ── */
  .upload-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--accent-2);
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
    color: var(--tx-lo);
    text-transform: uppercase;
    letter-spacing: 0.18em;
    border-bottom: 1px solid var(--bd-dim);
    padding-bottom: 0.55rem;
    margin: 1.8rem 0 1.1rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  /* ── Stat boxes ── */
  .stat-box {
    background: linear-gradient(160deg, var(--bg-card) 0%, var(--bg-inset) 100%);
    border: 1px solid var(--bd);
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
    background: linear-gradient(90deg, transparent, var(--accent-bg), transparent);
  }
  .stat-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.1rem;
    font-weight: 700;
    color: var(--accent);
    line-height: 1;
    margin-bottom: 0.35rem;
  }
  .stat-num.warn { color: var(--warn); }
  .stat-label {
    font-size: 0.7rem;
    color: var(--tx-lo);
    text-transform: uppercase;
    letter-spacing: 0.14em;
  }

  /* ── Match cards ── */
  .match-card {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-inset) 100%);
    border: 1px solid var(--bd);
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
  .match-card:hover { border-color: var(--bd-hover); }
  .match-score {
    color: var(--warn);
    font-weight: 600;
    background: var(--warn-bg);
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    white-space: nowrap;
    margin-left: 0.8rem;
    flex-shrink: 0;
  }
  .match-score.high { color: var(--accent); background: var(--accent-bg); }
  .match-names { color: var(--tx-mid); overflow: hidden; }
  .match-main  { color: var(--tx); font-weight: 500; }
  .match-arrow { color: var(--bd-hover); margin: 0 0.4rem; }

  /* ── Threshold panel ── */
  .threshold-panel {
    background: linear-gradient(160deg, var(--bg-card) 0%, var(--bg-card-b) 100%);
    border: 1px solid var(--bd);
    border-radius: 10px;
    padding: 1.2rem 1.6rem 0.8rem;
    margin-bottom: 0.5rem;
  }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--bd) !important;
    gap: 3px;
    padding-bottom: 0;
    margin-bottom: 0;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--tx-lo) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.5rem 1.5rem !important;
    border-radius: 6px 6px 0 0 !important;
    border: 1px solid transparent !important;
    border-bottom: none !important;
  }
  .stTabs [aria-selected="true"] {
    background: var(--bg-card) !important;
    color: var(--accent) !important;
    border-color: var(--bd) !important;
    border-bottom-color: var(--bg-card) !important;
  }
  .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
  .stTabs [data-baseweb="tab-border"]    { display: none !important; }
  .stTabs [data-baseweb="tab-panel"]     { padding-top: 1.2rem !important; }

  /* ── Streamlit overrides ── */
  div[data-testid="stFileUploader"] {
    background: transparent !important;
    border: 1px dashed var(--bd) !important;
    border-radius: 8px !important;
    padding: 0.6rem !important;
  }
  div[data-testid="stFileUploader"]:hover { border-color: var(--accent-bd) !important; }

  .stSlider > div > div > div { background: var(--accent) !important; }
  [data-testid="stSlider"] [data-testid="stTickBarMin"],
  [data-testid="stSlider"] [data-testid="stTickBarMax"] { color: var(--tx-lo) !important; }

  .stButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent-3)) !important;
    color: var(--btn-tx) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.2rem !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.04em !important;
    width: auto !important;
    box-shadow: 0 0 20px var(--accent-gl) !important;
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, var(--accent-2), var(--accent)) !important;
    box-shadow: 0 0 28px var(--accent-gl2) !important;
  }
  .stButton > button[data-testid="baseButton-primary"] { min-height: 2.4rem !important; }

  .stButton > button[data-testid="baseButton-secondary"] {
    background: var(--sec-bg) !important;
    color: var(--tx-mid) !important;
    border: 1px solid var(--bd) !important;
    box-shadow: none !important;
    padding: 0.22rem 0.5rem !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.02em !important;
    min-height: 1.8rem !important;
    width: 100% !important;
    border-radius: 6px !important;
  }
  .stButton > button[data-testid="baseButton-secondary"]:hover {
    background: var(--sec-bg-h) !important;
    color: var(--tx) !important;
    border-color: var(--bd-hover) !important;
  }

  /* Theme toggle button — pill shape, subtle */
  #_theme_anchor + div .stButton > button {
    background: var(--sec-bg) !important;
    color: var(--tx-dim) !important;
    border: 1px solid var(--bd) !important;
    box-shadow: none !important;
    font-size: 0.74rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.04em !important;
    padding: 0.3rem 1rem !important;
    min-height: 1.8rem !important;
    border-radius: 20px !important;
    width: 100% !important;
  }
  #_theme_anchor + div .stButton > button:hover {
    background: var(--sec-bg-h) !important;
    border-color: var(--bd-hover) !important;
    color: var(--tx) !important;
    box-shadow: none !important;
  }

  .stDataFrame {
    border: 1px solid var(--bd) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
  }
  .stAlert { border-radius: 8px !important; }

  div[data-testid="stDownloadButton"] button {
    background: var(--sec-bg) !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent-bd) !important;
    box-shadow: none !important;
    border-radius: 7px !important;
    font-size: 0.78rem !important;
  }
  div[data-testid="stDownloadButton"] button:hover {
    background: var(--sec-bg-h) !important;
    border-color: var(--accent-bg) !important;
  }
</style>
""", unsafe_allow_html=True)

# Inject light theme variable overrides when active
if not _is_dark:
    st.markdown("""
<style>
  :root {
    --bg:         #f2f5fb;
    --bg-card:    #ffffff;
    --bg-card-b:  #eef2fa;
    --bg-inset:   #e8edf8;
    --bd:         #cdd5e8;
    --bd-dim:     #e2e8f4;
    --bd-hover:   #a0b0cc;
    --tx:         #252e42;
    --tx-h:       #0f1623;
    --tx-dim:     #647088;
    --tx-lo:      #8898b4;
    --tx-mid:     #506078;
    --accent:     #00835a;
    --accent-2:   #007050;
    --accent-3:   #006044;
    --accent-bg:  rgba(0,131,90,0.09);
    --accent-gl:  rgba(0,131,90,0.14);
    --accent-gl2: rgba(0,131,90,0.22);
    --accent-bd:  #a8d8c0;
    --warn:       #c94510;
    --warn-bg:    rgba(201,69,16,0.1);
    --btn-tx:     #ffffff;
    --sec-bg:     #eef2fa;
    --sec-bg-h:   #e2e8f4;
  }
  .stApp { background: var(--bg) !important; color: var(--tx) !important; }
  .stTabs [aria-selected="true"] {
    border-bottom-color: var(--bg) !important;
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

# Every duplicate — matched by name or by an identity key — is overridden the same
# way: one set of row ids the user has forced into the output.
DUP_EXEMPT_KEY = "dup_exempt_row_ids"

# Streamlit gives an expander no state of its own, so remember that the user is
# working inside one and re-open it on the next rerun.
DUPS_OPEN_KEY = "sa_dups_open"

# ── Country normalisation ─────────────────────────────────────────────────────
# Maps every known variant (lowercase) → canonical short code.
# Column headers containing any COUNTRY_COL_HINTS word trigger normalisation.
COUNTRY_COL_HINTS = {'country', 'land', 'nation', 'staat', 'pays', 'pais', 'paese', 'kraj'}

COUNTRY_MAP: dict[str, str] = {
    # Rule: single-word countries → proper English name; well-known multi-word
    # countries → their standard abbreviation (US, UK, UAE …).
    # All keys are lowercase; values are the canonical display form.

    # ── United States ──────────────────────────────────────────
    'united states': 'US', 'united states of america': 'US',
    'usa': 'US', 'us': 'US', 'u.s.': 'US', 'u.s.a.': 'US', 'america': 'US',
    # ── United Kingdom ─────────────────────────────────────────
    'united kingdom': 'UK', 'uk': 'UK', 'u.k.': 'UK',
    'great britain': 'UK', 'britain': 'UK', 'gb': 'UK',
    'england': 'UK', 'scotland': 'UK', 'wales': 'UK', 'northern ireland': 'UK',
    # ── United Arab Emirates ───────────────────────────────────
    'united arab emirates': 'UAE', 'uae': 'UAE', 'ae': 'UAE',
    # ── Germany ────────────────────────────────────────────────
    'germany': 'Germany', 'deutschland': 'Germany', 'de': 'Germany', 'ger': 'Germany',
    # ── France ─────────────────────────────────────────────────
    'france': 'France', 'fr': 'France', 'fra': 'France',
    # ── Netherlands ────────────────────────────────────────────
    'netherlands': 'Netherlands', 'the netherlands': 'Netherlands',
    'holland': 'Netherlands', 'nederland': 'Netherlands', 'nl': 'Netherlands',
    # ── Sweden ─────────────────────────────────────────────────
    'sweden': 'Sweden', 'sverige': 'Sweden', 'se': 'Sweden', 'swe': 'Sweden',
    # ── Norway ─────────────────────────────────────────────────
    'norway': 'Norway', 'norge': 'Norway', 'noreg': 'Norway',
    'no': 'Norway', 'nor': 'Norway',
    # ── Denmark ────────────────────────────────────────────────
    'denmark': 'Denmark', 'danmark': 'Denmark', 'dk': 'Denmark', 'dnk': 'Denmark',
    # ── Finland ────────────────────────────────────────────────
    'finland': 'Finland', 'suomi': 'Finland', 'fi': 'Finland', 'fin': 'Finland',
    # ── Turkey ─────────────────────────────────────────────────
    'turkey': 'Turkey', 'türkiye': 'Turkey', 'turkiye': 'Turkey',
    'tr': 'Turkey', 'tur': 'Turkey',
    # ── Austria ────────────────────────────────────────────────
    'austria': 'Austria', 'österreich': 'Austria', 'oesterreich': 'Austria',
    'at': 'Austria', 'aut': 'Austria',
    # ── Switzerland ────────────────────────────────────────────
    'switzerland': 'Switzerland', 'schweiz': 'Switzerland', 'suisse': 'Switzerland',
    'svizzera': 'Switzerland', 'svizra': 'Switzerland', 'ch': 'Switzerland', 'che': 'Switzerland',
    # ── Belgium ────────────────────────────────────────────────
    'belgium': 'Belgium', 'belgië': 'Belgium', 'belgie': 'Belgium',
    'belgique': 'Belgium', 'belgien': 'Belgium', 'be': 'Belgium', 'bel': 'Belgium',
    # ── Spain ──────────────────────────────────────────────────
    'spain': 'Spain', 'españa': 'Spain', 'espana': 'Spain', 'es': 'Spain', 'esp': 'Spain',
    # ── Italy ──────────────────────────────────────────────────
    'italy': 'Italy', 'italia': 'Italy', 'it': 'Italy', 'ita': 'Italy',
    # ── Portugal ───────────────────────────────────────────────
    'portugal': 'Portugal', 'pt': 'Portugal', 'por': 'Portugal',
    # ── Poland ─────────────────────────────────────────────────
    'poland': 'Poland', 'polska': 'Poland', 'pl': 'Poland', 'pol': 'Poland',
    # ── Czechia ────────────────────────────────────────────────
    'czechia': 'Czechia', 'czech republic': 'Czechia', 'česká republika': 'Czechia',
    'ceska republika': 'Czechia', 'cz': 'Czechia', 'cze': 'Czechia',
    # ── Hungary ────────────────────────────────────────────────
    'hungary': 'Hungary', 'magyarország': 'Hungary', 'magyarorszag': 'Hungary',
    'hu': 'Hungary', 'hun': 'Hungary',
    # ── Romania ────────────────────────────────────────────────
    'romania': 'Romania', 'românia': 'Romania', 'ro': 'Romania', 'rou': 'Romania',
    # ── Greece ─────────────────────────────────────────────────
    'greece': 'Greece', 'hellas': 'Greece', 'ελλάδα': 'Greece',
    'gr': 'Greece', 'gre': 'Greece',
    # ── Ireland ────────────────────────────────────────────────
    'ireland': 'Ireland', 'éire': 'Ireland', 'eire': 'Ireland',
    'republic of ireland': 'Ireland', 'ie': 'Ireland', 'irl': 'Ireland',
    # ── Luxembourg ─────────────────────────────────────────────
    'luxembourg': 'Luxembourg', 'luxemburg': 'Luxembourg',
    'lu': 'Luxembourg', 'lux': 'Luxembourg',
    # ── Slovakia ───────────────────────────────────────────────
    'slovakia': 'Slovakia', 'slovensko': 'Slovakia', 'sk': 'Slovakia', 'svk': 'Slovakia',
    # ── Slovenia ───────────────────────────────────────────────
    'slovenia': 'Slovenia', 'slovenija': 'Slovenia', 'si': 'Slovenia', 'svn': 'Slovenia',
    # ── Croatia ────────────────────────────────────────────────
    'croatia': 'Croatia', 'hrvatska': 'Croatia', 'hr': 'Croatia', 'hrv': 'Croatia',
    # ── Bulgaria ───────────────────────────────────────────────
    'bulgaria': 'Bulgaria', 'българия': 'Bulgaria', 'bg': 'Bulgaria', 'bul': 'Bulgaria',
    # ── Serbia ─────────────────────────────────────────────────
    'serbia': 'Serbia', 'srbija': 'Serbia', 'rs': 'Serbia', 'srb': 'Serbia',
    # ── Ukraine ────────────────────────────────────────────────
    'ukraine': 'Ukraine', 'україна': 'Ukraine', 'ua': 'Ukraine', 'ukr': 'Ukraine',
    # ── Russia ─────────────────────────────────────────────────
    'russia': 'Russia', 'россия': 'Russia', 'russian federation': 'Russia',
    'ru': 'Russia', 'rus': 'Russia',
    # ── Estonia ────────────────────────────────────────────────
    'estonia': 'Estonia', 'eesti': 'Estonia', 'ee': 'Estonia', 'est': 'Estonia',
    # ── Latvia ─────────────────────────────────────────────────
    'latvia': 'Latvia', 'latvija': 'Latvia', 'lv': 'Latvia', 'lva': 'Latvia',
    # ── Lithuania ──────────────────────────────────────────────
    'lithuania': 'Lithuania', 'lietuva': 'Lithuania', 'lt': 'Lithuania', 'ltu': 'Lithuania',
    # ── Canada ─────────────────────────────────────────────────
    'canada': 'Canada', 'ca': 'Canada', 'can': 'Canada',
    # ── Australia ──────────────────────────────────────────────
    'australia': 'Australia', 'au': 'Australia', 'aus': 'Australia',
    # ── New Zealand ────────────────────────────────────────────
    'new zealand': 'New Zealand', 'nz': 'New Zealand', 'nzl': 'New Zealand',
    # ── Japan ──────────────────────────────────────────────────
    'japan': 'Japan', '日本': 'Japan', 'jp': 'Japan', 'jpn': 'Japan',
    # ── China ──────────────────────────────────────────────────
    'china': 'China', 'prc': 'China', "people's republic of china": 'China',
    '中国': 'China', 'cn': 'China', 'chn': 'China',
    # ── India ──────────────────────────────────────────────────
    'india': 'India', 'भारत': 'India', 'in': 'India', 'ind': 'India',
    # ── Brazil ─────────────────────────────────────────────────
    'brazil': 'Brazil', 'brasil': 'Brazil', 'br': 'Brazil', 'bra': 'Brazil',
    # ── South Africa ───────────────────────────────────────────
    'south africa': 'South Africa', 'rsa': 'South Africa',
    'za': 'South Africa', 'zaf': 'South Africa',
    # ── Saudi Arabia ───────────────────────────────────────────
    'saudi arabia': 'Saudi Arabia', 'ksa': 'Saudi Arabia', 'sa': 'Saudi Arabia',
    # ── Israel ─────────────────────────────────────────────────
    'israel': 'Israel', 'ישראל': 'Israel', 'il': 'Israel', 'isr': 'Israel',
    # ── Singapore ──────────────────────────────────────────────
    'singapore': 'Singapore', 'sg': 'Singapore', 'sgp': 'Singapore',
    # ── Mexico ─────────────────────────────────────────────────
    'mexico': 'Mexico', 'méxico': 'Mexico', 'mx': 'Mexico', 'mex': 'Mexico',
    # ── Argentina ──────────────────────────────────────────────
    'argentina': 'Argentina', 'ar': 'Argentina', 'arg': 'Argentina',
    # ── Colombia ───────────────────────────────────────────────
    'colombia': 'Colombia', 'co': 'Colombia', 'col': 'Colombia',
    # ── Chile ──────────────────────────────────────────────────
    'chile': 'Chile', 'cl': 'Chile', 'chl': 'Chile',
    # ── Iceland ────────────────────────────────────────────────
    'iceland': 'Iceland', 'ísland': 'Iceland', 'island': 'Iceland',
    'is': 'Iceland', 'isl': 'Iceland',
    # ── Cyprus ─────────────────────────────────────────────────
    'cyprus': 'Cyprus', 'κύπρος': 'Cyprus', 'kıbrıs': 'Cyprus',
    'cy': 'Cyprus', 'cyp': 'Cyprus',
    # ── Malta ──────────────────────────────────────────────────
    'malta': 'Malta', 'mt': 'Malta', 'mlt': 'Malta',
    # ── Bosnia ─────────────────────────────────────────────────
    'bosnia': 'Bosnia', 'bosnia and herzegovina': 'Bosnia',
    'bosna i hercegovina': 'Bosnia', 'ba': 'Bosnia', 'bih': 'Bosnia',
    # ── North Macedonia ────────────────────────────────────────
    'north macedonia': 'North Macedonia', 'macedonia': 'North Macedonia',
    'mk': 'North Macedonia', 'mkd': 'North Macedonia',
    # ── Albania ────────────────────────────────────────────────
    'albania': 'Albania', 'shqipëri': 'Albania', 'al': 'Albania', 'alb': 'Albania',
    # ── Kosovo ─────────────────────────────────────────────────
    'kosovo': 'Kosovo', 'xk': 'Kosovo', 'xkx': 'Kosovo',
    # ── Belarus ────────────────────────────────────────────────
    'belarus': 'Belarus', 'by': 'Belarus', 'blr': 'Belarus',
    # ── Moldova ────────────────────────────────────────────────
    'moldova': 'Moldova', 'md': 'Moldova', 'mda': 'Moldova',
    # ── Georgia ────────────────────────────────────────────────
    'georgia': 'Georgia', 'საქართველო': 'Georgia', 'ge': 'Georgia', 'geo': 'Georgia',
    # ── Armenia ────────────────────────────────────────────────
    'armenia': 'Armenia', 'հայաստան': 'Armenia', 'am': 'Armenia', 'arm': 'Armenia',
    # ── Azerbaijan ─────────────────────────────────────────────
    'azerbaijan': 'Azerbaijan', 'azərbaycan': 'Azerbaijan',
    'az': 'Azerbaijan', 'aze': 'Azerbaijan',
    # ── Kazakhstan ─────────────────────────────────────────────
    'kazakhstan': 'Kazakhstan', 'kz': 'Kazakhstan', 'kaz': 'Kazakhstan',
    # ── South Korea ────────────────────────────────────────────
    'south korea': 'South Korea', 'korea': 'South Korea',
    '한국': 'South Korea', 'kr': 'South Korea', 'kor': 'South Korea',
}

def _is_country_col(col_name: str) -> bool:
    """Return True when the column header suggests it holds country values."""
    normalized = col_name.lower().strip()
    return any(hint in normalized for hint in COUNTRY_COL_HINTS)

def _norm_country(val) -> str:
    """Map one country value to its canonical short code; leave unknown values unchanged."""
    if not isinstance(val, str):
        return val
    key = val.strip().lower()
    return COUNTRY_MAP.get(key, val)

def normalize_country_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize country-name variants in any column whose header implies country data."""
    for col in df.columns:
        if _is_country_col(col):
            df[col] = df[col].apply(_norm_country)
    return df

def _output_filename(source_name: str, ext: str) -> str:
    stem = source_name
    for e in ('.xlsx', '.xls', '.csv'):
        if stem.lower().endswith(e):
            stem = stem[:-len(e)]
            break
    stem = re.sub(r'[\s_\-]+\d{4}[\-_\.]\d{2}[\-_\.]\d{2}$', '', stem)
    stem = re.sub(r'[\s_\-]+\d{2}[\-_\.]\d{2}[\-_\.]\d{4}$', '', stem)
    stem = re.sub(r'[\s_\-]+\d{8}$', '', stem)
    stem = re.sub(r'[^\w]', '_', stem)
    stem = re.sub(r'_+', '_', stem).strip('_') or 'output'
    return f"{stem}_{date.today().strftime('%Y-%m-%d')}{ext}"


def clean_for_output(name: str) -> str:
    """Remove numbers and demo tags for the output file."""
    if not isinstance(name, str):
        return ""
    n = name.strip()
    n = re.sub(r'\(\s*[Dd]emo[^)]*\)', '', n)   # (Demo Account), (Demo: 34708)
    n = re.sub(r'\b\d{4,}\b', '', n)             # standalone 4+ digit IDs
    n = re.sub(r'\s*\d+\s*$', '', n)             # trailing numbers
    n = re.sub(r'^\s*\d+\s*', '', n)             # leading numbers
    n = re.sub(r'\(\s*\)', '', n)                # leftover empty parentheses
    n = re.sub(r'^\s*[-–—]\s*', '', n)           # leading dash left after number removal
    n = re.sub(r'\s*[-–—]\s*$', '', n)           # trailing dash left after number removal
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

def col_key(s: str) -> str:
    """Normalize a column name for loose matching: lowercase, strip spaces/underscores/hyphens."""
    return re.sub(r'[\s_\-]+', '', s.lower())

# Headers that contain a company hint but hold something other than its name:
# "companywebsite" and "companyemaildomain" would otherwise win on "company".
NON_NAME_HINTS = ('website', 'webpage', 'url', 'email', 'mail', 'domain', 'country',
                  'phone', 'street', 'city', 'zip', 'postcode', 'linkedin', 'revenue',
                  'employee')

EXACT_NAME_HEADERS = ('company name', 'company', 'organisation', 'organization',
                      'account name', 'name', 'account')


def detect_company_col(columns) -> str:
    # Checked strongest-hint-first across ALL columns, not first-column-first —
    # otherwise a "Full Name" column ahead of "Company Name" wins on the bare
    # "name" substring, and headers like "...Company Filter" false-match "company".
    priority_hints = ['company name', 'company', 'organisation', 'organization', 'account name', 'firm']
    fallback_hints = ['name', 'account']
    lower_cols = [c.lower().strip() for c in columns]

    # An exact header beats any substring match.
    for exact in EXACT_NAME_HEADERS:
        for col, lc in zip(columns, lower_cols):
            if lc == exact:
                return col

    # Substring matches, skipping headers that clearly hold something else.
    for hint in priority_hints + fallback_hints:
        for col, lc in zip(columns, lower_cols):
            if hint in lc and not any(bad in lc for bad in NON_NAME_HINTS):
                return col

    # Nothing clean matched, so fall back to the original laxer sweep.
    for hint in priority_hints + fallback_hints:
        for col, lc in zip(columns, lower_cols):
            if hint in lc:
                return col
    return columns[0]

CSV_DELIMITERS = (',', ';', '\t', '|')


def sniff_delimiter(text: str, _depth: int = 0) -> str:
    """The delimiter that splits this file's header row into the most columns.

    csv.Sniffer guesses from a text sample and gets semicolon exports wrong often
    enough to matter, and a wrong guess is indistinguishable from a one-column
    file. The header row is the reliable evidence: parsed with csv.reader per
    candidate, so a delimiter sitting inside a quoted value doesn't count. Comma
    wins a tie, being the most common.
    """
    header = next((ln for ln in text.splitlines() if ln.strip()), "")
    best, best_cols = ',', 0
    for delim in CSV_DELIMITERS:
        try:
            cols = len(next(csv.reader([header], delimiter=delim)))
        except (csv.Error, StopIteration):
            continue
        if cols > best_cols:
            best, best_cols = delim, cols

    # A double-encoded export hides its real delimiter inside one quoted field,
    # where no candidate can see it. Peel that layer off and look again.
    if best_cols <= 1 and _depth == 0:
        try:
            inner = next(csv.reader([header]))
        except (csv.Error, StopIteration):
            inner = []
        if len(inner) == 1 and inner[0] != header:
            return sniff_delimiter(inner[0], _depth=1)
    return best


def _unwrap_double_encoded_csv(text, sep=','):
    """Some exports wrap every row in an extra layer of CSV quoting, so each
    row parses as a single field whose content is itself a full CSV row.
    Detect that pattern, strip the outer layer, and return the rows already
    split into fields (as a list of lists) rather than reassembled text:
    the leading field of the inner row is sometimes left unquoted even when
    it contains a literal separator, which a second blind CSV parse can't tell
    apart from an actual column boundary. Any such stray split is merged
    back into the leading field using the header's column count as the
    source of truth.

    sep is the file's real delimiter. Without it every semicolon-separated file
    matches the pattern - each line holds no comma, so it reads as one field -
    and comes back as a single column."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) < 2:
        return None
    outer = []
    for ln in lines:
        try:
            fields = next(csv.reader([ln], delimiter=sep))
        except csv.Error:
            return None
        if len(fields) != 1:
            return None
        outer.append(fields[0])
    if not any(sep in u for u in outer[:5]):
        return None
    rows = [next(csv.reader([u], delimiter=sep)) for u in outer]
    n_cols = len(rows[0])
    if n_cols < 2:
        # one column either way, so there was no extra layer to strip
        return None
    for row in rows[1:]:
        while len(row) > n_cols:
            row[0:2] = [row[0] + sep + row[1]]
    return rows

def read_file(f, nrows=None, sheet_name=0):
    raw = f.read()
    if f.name.lower().endswith('.csv'):
        text = None
        for encoding in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
            try:
                text = raw.decode(encoding)
                break
            except (UnicodeDecodeError, LookupError):
                pass
        if text is None:
            text = raw.decode('latin-1', errors='replace')
        sep = sniff_delimiter(text)
        rows = _unwrap_double_encoded_csv(text, sep)
        if rows is not None:
            df = pd.DataFrame(rows[1:], columns=rows[0])
            if nrows is not None:
                df = df.head(nrows)
            return normalize_country_cols(df)
        return normalize_country_cols(pd.read_csv(io.StringIO(text), sep=sep, nrows=nrows))
    return normalize_country_cols(pd.read_excel(io.BytesIO(raw), nrows=nrows, sheet_name=sheet_name))


def get_excel_sheets(f):
    """Return list of sheet names if Excel file has >1 sheet, else None."""
    if f.name.lower().endswith('.csv'):
        return None
    try:
        raw = f.read()
        f.seek(0)
        sheets = pd.ExcelFile(io.BytesIO(raw)).sheet_names
        return sheets if len(sheets) > 1 else None
    except Exception:
        return None

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


def find_internal_duplicates(names: list, threshold: int) -> list:
    """
    Within-list fuzzy dedup.
    Returns [{id_keeper, id_dup, name_keeper, name_dup, score}].
    Lower-index entry is the keeper; higher-index duplicates are flagged.
    """
    norm = [normalize(n) for n in names]
    duplicates = []
    dup_ids: set = set()

    for i, norm_i in enumerate(norm):
        if not norm_i or i in dup_ids:
            continue
        for j in range(i + 1, len(norm)):
            if j in dup_ids:
                continue
            norm_j = norm[j]
            if not norm_j:
                continue
            score = fuzz.token_sort_ratio(norm_i, norm_j)
            if score >= threshold:
                dup_ids.add(j)
                duplicates.append({
                    "id_keeper": i,
                    "id_dup": j,
                    "name_keeper": names[i],
                    "name_dup": names[j],
                    "score": score,
                })

    return duplicates


def find_symmetric_overlap(names_a: list, names_b: list, threshold: int) -> tuple:
    """
    Cross-compare two lists. Any pair scoring >= threshold is treated as the same
    entity and dropped from BOTH sides (not just flagged on one side).
    Returns (keep_a, keep_b, overlaps) where keep_a/keep_b are indices with no
    match on the other side, and overlaps is [{id_a, id_b, name_a, name_b, score}].
    """
    norm_a = [normalize(n) for n in names_a]
    norm_b = [normalize(n) for n in names_b]
    matched_a: set = set()
    matched_b: set = set()
    overlaps = []

    for j, norm_bj in enumerate(norm_b):
        if not norm_bj:
            continue
        result = process.extractOne(norm_bj, norm_a, scorer=fuzz.token_sort_ratio)
        if result and result[1] >= threshold:
            i = result[2]
            matched_a.add(i)
            matched_b.add(j)
            overlaps.append({
                "id_a": i, "id_b": j,
                "name_a": names_a[i], "name_b": names_b[j],
                "score": result[1],
            })

    keep_a = [i for i in range(len(names_a)) if i not in matched_a]
    keep_b = [j for j in range(len(names_b)) if j not in matched_b]
    return keep_a, keep_b, overlaps


def store_results(payload: dict) -> None:
    previous_payload = st.session_state.get(RESULTS_SESSION_KEY)
    previous_exempt  = list(st.session_state.get(DUP_EXEMPT_KEY, []))
    st.session_state[RESULTS_SESSION_KEY] = payload
    same_inputs = bool(previous_payload) and previous_payload.get("signature") == payload.get("signature")
    st.session_state[DUP_EXEMPT_KEY] = previous_exempt if same_inputs else []
    if not same_inputs:
        st.session_state[DUPS_OPEN_KEY] = False


def get_visible_results():
    """The cached screening result, with the user's exemptions applied."""
    payload = st.session_state.get(RESULTS_SESSION_KEY)
    if not payload:
        return None

    exempt = set(st.session_state.get(DUP_EXEMPT_KEY, []))

    # Rows with a usable company name: everything find_matches sorted into one
    # bucket or the other. Rows whose name normalises to nothing are in neither.
    usable = sorted(set(payload["unique_new"]) | {m["id"] for m in payload["matches"]})

    name_flagged = ({m["id"] for m in payload["matches"]}
                    | {d["id_dup"] for d in payload.get("internal_dups", [])}) - exempt
    kept_ids = [i for i in usable if i not in name_flagged]

    return {
        "signature": payload["signature"],
        "new_names": payload["new_names"],
        "matches": payload["matches"],
        "internal_dups": payload.get("internal_dups", []),
        "exempt": exempt,
        "usable_ids": usable,
        "kept_ids": kept_ids,
        "df_new_valid": payload["df_new_valid"],
        "new_cols_by_file": payload.get("new_cols_by_file", {}),
        # Carried through so the append step can rebuild the combined list on every
        # rerun without re-reading (or re-screening) any file.
        "main_col": payload.get("main_col"),
        "screened": payload.get("screened", True),
        "df_main": payload.get("df_main"),
        "main_name": payload.get("main_name"),
        "main_row_count": payload.get("main_row_count", 0),
    }


# These run as on_click callbacks, i.e. before the script reruns, so everything
# rendered below picks up the new state without a second forced rerun.
def exempt_row(row_id) -> None:
    """Force one row into the output, whichever check flagged it."""
    ids = list(st.session_state.get(DUP_EXEMPT_KEY, []))
    if row_id not in ids:
        ids.append(row_id)
        st.session_state[DUP_EXEMPT_KEY] = ids
    st.session_state[DUPS_OPEN_KEY] = True


def unexempt_row(row_id) -> None:
    ids = list(st.session_state.get(DUP_EXEMPT_KEY, []))
    if row_id in ids:
        ids.remove(row_id)
        st.session_state[DUP_EXEMPT_KEY] = ids
    st.session_state[DUPS_OPEN_KEY] = True


APPEND_SKIP = "— Skip / leave empty —"

WEBSITE_COL_HINTS     = ('website', 'webpage', 'weburl', 'homepage', 'siteurl')
EMAILDOMAIN_COL_HINTS = ('emaildomain', 'maildomain', 'domainemail')

def _is_website_col(col_name: str) -> bool:
    k = col_key(col_name)
    return any(h in k for h in WEBSITE_COL_HINTS)

def _is_emaildomain_col(col_name: str) -> bool:
    k = col_key(col_name)
    return any(h in k for h in EMAILDOMAIN_COL_HINTS)

def _norm_website(val) -> str:
    """Ensure https://domain.tld — strips path, upgrades http, adds https if missing."""
    if not isinstance(val, str) or not val.strip():
        return val
    v = val.strip()
    if v.startswith('http://'):
        v = 'https://' + v[7:]
    elif not v.startswith('https://'):
        v = 'https://' + v
    rest = v[8:]  # after 'https://'
    rest = rest.split('/')[0].split('?')[0].split('#')[0]
    return 'https://' + rest

def _norm_emaildomain(val) -> str:
    """Return bare domain.tld — handles full emails (after @), URLs, or plain domains."""
    if not isinstance(val, str) or not val.strip():
        return val
    v = val.strip()
    if '@' in v:
        v = v.split('@', 1)[1]
    if '://' in v:
        v = v.split('://', 1)[1]
    if v.lower().startswith('www.'):
        v = v[4:]
    v = v.split('/')[0].split('?')[0].split('#')[0]
    return v


SRC_FILE_COL = "_src_file"
SRC_ROW_COL  = "_src_row"
# Each list names its company column whatever it likes, so the chosen one is
# copied here as well: screening then has a single column to work across files.
NAME_COL     = "_company"
BOOKKEEPING_COLS = (SRC_FILE_COL, SRC_ROW_COL, NAME_COL)

MAIN_LIST_ORIGIN = None   # a finding whose origin is None collided with the main list


def _key_kind(col_name: str) -> str:
    """How the values in one main-list column identify a company."""
    k = col_key(col_name)
    if _is_emaildomain_col(col_name):
        return "domain"
    if "email" in k or k == "mail":
        return "email"
    if _is_website_col(col_name):
        return "website"
    if "linkedin" in k:
        return "url"
    return "text"


def default_key_cols(main_columns) -> list:
    """Columns that identify a company on their own, so they make good keys."""
    return [c for c in main_columns if _key_kind(c) in ("domain", "email", "website", "url")]


def match_key(col_name, val, kind=None) -> str:
    """Normalise one cell into a comparison key, or "" when it identifies nothing.

    Compared in the same shape it is written in: an email-domain column ignores
    the part before the @, websites and profile urls ignore scheme and www. A
    plain email column keeps the full address, otherwise two contacts at one
    company would count as the same company.
    """
    if not pd.notna(val):
        return ""
    text = str(val).strip()
    if not text:
        return ""
    kind = kind or _key_kind(col_name)
    if kind == "domain":
        text = str(_norm_emaildomain(text) or text)
    elif kind in ("website", "url"):
        text = text.split("://", 1)[-1]
        if text.lower().startswith("www."):
            text = text[4:]
        text = text.split("?")[0].split("#")[0].rstrip("/")
    return text.strip().lower()


def name_findings(payload, exempt) -> list:
    """The fuzzy company-name duplicates, as findings.

    Cached with the screening result, because matching every new name against the
    whole main list is the expensive part of the run.
    """
    out = []
    for m in payload.get("matches", []):
        out.append({
            "row_id": m["id"], "kind": "name", "key": "company name",
            "score": m["score"], "row_label": m["raw_name"],
            "match_label": m["matched_main_name"], "match_origin": MAIN_LIST_ORIGIN,
            "value": m["raw_name"], "exempt": m["id"] in exempt,
        })
    for d in payload.get("internal_dups", []):
        out.append({
            "row_id": d["id_dup"], "kind": "name", "key": "company name",
            "score": d["score"], "row_label": d["name_dup"],
            "match_label": d["name_keeper"], "match_origin": "an earlier new row",
            "value": d["name_dup"], "exempt": d["id_dup"] in exempt,
        })
    return out


def build_combined(df_main, main_name_col, mappings, key_cols, sources, exempt):
    """Map the surviving rows onto the main list's columns and drop the ones whose
    identity keys already exist, either in the main list or in a row already kept.

    mappings – {source file: {main_col: source_col | APPEND_SKIP}}
    key_cols – main-list columns to compare on, in the order given
    sources  – [(source file, rows)] indexed by their position in df_new_valid
    exempt   – row ids the user forced in; they are appended and their keys are
               registered, so a later duplicate still collides with them

    Returns {df_result, appended, findings}, findings sharing the shape used by
    name_findings so both kinds can be reviewed as one list.
    """
    key_cols = [c for c in key_cols if c in df_main.columns]
    kinds    = {c: _key_kind(c) for c in key_cols}

    # key value -> (label, origin); origin None means the main list
    index = {c: {} for c in key_cols}
    _labels = df_main[main_name_col] if main_name_col in df_main.columns else None
    for c in key_cols:
        for val, label in zip(df_main[c], _labels if _labels is not None else df_main[c]):
            k = match_key(c, val, kinds[c])
            if k and k not in index[c]:
                index[c][k] = (str(label).strip() if pd.notna(label) else k, MAIN_LIST_ORIGIN)

    mapped_chunks = []
    for src_name, df_src in sources:
        file_mapping = mappings.get(src_name)
        if not file_mapping or not len(df_src):
            continue
        chunk = pd.DataFrame(
            {mc: (df_src[src].values if src != APPEND_SKIP and src in df_src.columns
                  else [None] * len(df_src))
             for mc, src in file_mapping.items()},
            index=df_src.index,
        )
        for col in chunk.columns:
            if _is_website_col(col):
                chunk[col] = chunk[col].apply(_norm_website)
            elif _is_emaildomain_col(col):
                chunk[col] = chunk[col].apply(_norm_emaildomain)
        chunk["_source_file"] = src_name
        chunk["_source_row"]  = (df_src[SRC_ROW_COL].values if SRC_ROW_COL in df_src.columns
                                 else range(1, len(df_src) + 1))
        mapped_chunks.append(chunk)

    if not mapped_chunks:
        return {"df_result": df_main.copy(), "appended": df_main.iloc[0:0].copy(), "findings": []}

    mapped = pd.concat(mapped_chunks)
    findings, keep_ids = [], []

    for row_id, row in mapped.iterrows():
        is_exempt = row_id in exempt
        hit = None
        # Evaluated for forced-in rows too, so the review list can still show what
        # they collided with - and offer to un-force them.
        for c in key_cols:
            k = match_key(c, row.get(c), kinds[c])
            if k and k in index[c]:
                label, origin = index[c][k]
                hit = {
                    "row_id": row_id, "kind": "key", "key": c,
                    "score": None,
                    "row_label": (str(row.get(main_name_col)).strip()
                                  if pd.notna(row.get(main_name_col)) else k),
                    "match_label": label, "match_origin": origin,
                    "value": k, "exempt": is_exempt,
                    "file": row["_source_file"], "row_num": row["_source_row"],
                }
                break
        if hit:
            findings.append(hit)
            if not is_exempt:
                continue
        keep_ids.append(row_id)
        # a kept row becomes something later rows can collide with
        for c in key_cols:
            k = match_key(c, row.get(c), kinds[c])
            if k and k not in index[c]:
                label = row.get(main_name_col)
                index[c][k] = (str(label).strip() if pd.notna(label) else k, row["_source_file"])

    appended = mapped.loc[keep_ids].drop(columns=["_source_file", "_source_row"])
    appended = appended.reindex(columns=[c for c in df_main.columns if c in appended.columns])
    df_result = (pd.concat([df_main, appended], ignore_index=True) if len(appended)
                 else df_main.copy())

    return {"df_result": df_result, "appended": appended, "findings": findings}


def render_column_mapping(title, main_columns, new_columns, key_prefix, preselect=None):
    """One "main list column <- column from this file" mapping block.
    preselect: {main_col: source_col} defaults that win over name auto-matching —
    used for the company column, which the user has already paired up in step 03.
    Returns {main_col: source_col | APPEND_SKIP}."""
    options = [APPEND_SKIP] + new_columns
    st.markdown(f"<small style='color:#3a4a5e;font-family:JetBrains Mono,monospace;text-transform:uppercase;letter-spacing:0.08em'>&#9654;&nbsp; {title}</small>", unsafe_allow_html=True)
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


# ── UI ────────────────────────────────────────────────────────────────────────

# Header row: logo left, theme toggle right
_hcol_logo, _, _hcol_btn = st.columns([5, 7, 2])
with _hcol_logo:
    st.markdown('<div class="app-logo"><span class="dot">◼</span> List Toolbox</div>',
                unsafe_allow_html=True)
with _hcol_btn:
    st.markdown('<span id="_theme_anchor"></span>', unsafe_allow_html=True)
    _theme_label = "☀ Light" if _is_dark else "☾ Dark"
    st.button(_theme_label, on_click=_toggle_theme, key="_theme_btn")

st.markdown("<div style='margin-bottom:0.2rem'></div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["  Screen & Append  ", "  List Diff  "])

# ── Tab 1: Screen & Append ────────────────────────────────────────────────────
with tab1:

    st.markdown("""
<div class="tab-desc">
  <strong>Screen &amp; Append</strong> — upload your main list and the new lists once.
  A fuzzy company-name match flags what already exists, and everything that survives
  is mapped straight onto the main list's columns. Review the name matches, in-list
  duplicates and duplicate emails, then download the combined list — no intermediate
  download and re-upload.
</div>""", unsafe_allow_html=True)

    # ── Upload ─────────────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        st.markdown('<div class="upload-label">&#9632;&nbsp; 01 &mdash; Main list</div>', unsafe_allow_html=True)
        st.markdown("<small style='color:#3a4a5e'>Screened against <em>and</em> appended to.</small>", unsafe_allow_html=True)
        main_file = st.file_uploader("Main list", type=["xlsx", "xls", "csv"], key="main",
                                      label_visibility="collapsed")
        if isinstance(main_file, list):
            if len(main_file) > 1:
                st.warning("Only one file is allowed here. Using the first file.")
            main_file = main_file[0] if main_file else None

    with col_b:
        st.markdown('<div class="upload-label">&#9632;&nbsp; 02 &mdash; New lists</div>', unsafe_allow_html=True)
        st.markdown("<small style='color:#3a4a5e'>Screened, then appended.</small>", unsafe_allow_html=True)
        new_files = st.file_uploader("New lists to screen and append", type=["xlsx", "xls", "csv"], key="new",
                                      accept_multiple_files=True, label_visibility="collapsed")
        if not isinstance(new_files, list):
            new_files = [new_files] if new_files else []

    st.markdown("")

    # ── Sheet selection (Excel only) ────────────────────────────────────────────
    main_sheet = 0
    new_sheets = {}   # {filename: sheet_name}

    _sheet_picks = []   # (label, sheets, widget_key, target, filename)
    if main_file and not main_file.name.lower().endswith('.csv'):
        _ms = get_excel_sheets(main_file)
        if _ms:
            _sheet_picks.append(("Sheet — Main list", _ms, "main_sheet", "main", None))
    for _nf in new_files:
        if not _nf.name.lower().endswith('.csv'):
            _nfs = get_excel_sheets(_nf)
            if _nfs:
                _sheet_picks.append((f"Sheet — {_nf.name}", _nfs, f"sa_sheet_{_nf.name}", "new", _nf.name))

    if _sheet_picks:
        for _i in range(0, len(_sheet_picks), 3):
            _row = _sheet_picks[_i:_i + 3]
            _sc  = st.columns(len(_row), gap="small")
            for _c, (_lbl, _sheets, _key, _target, _fname) in zip(_sc, _row):
                with _c:
                    _sel = st.selectbox(_lbl, _sheets, key=_key)
                    if _target == "main":
                        main_sheet = _sel
                    else:
                        new_sheets[_fname] = _sel
        st.markdown("")

    # ── Read the column names of everything uploaded ────────────────────────────
    main_cols    = []
    new_cols_map = {}   # {filename: [columns]}

    if main_file:
        try:
            main_file.seek(0)
            main_cols = read_file(main_file, nrows=0, sheet_name=main_sheet).columns.tolist()
            main_file.seek(0)
        except Exception:
            st.warning(f"Could not read columns from {main_file.name}.")
    for _nf in new_files:
        try:
            _nf.seek(0)
            new_cols_map[_nf.name] = read_file(_nf, nrows=0, sheet_name=new_sheets.get(_nf.name, 0)).columns.tolist()
            _nf.seek(0)
        except Exception:
            new_cols_map[_nf.name] = []

    # Every column offered by any new list, in first-file-first order.
    new_cols_union = []
    for _nf in new_files:
        for _c in new_cols_map.get(_nf.name, []):
            if _c not in new_cols_union and _c not in BOOKKEEPING_COLS:
                new_cols_union.append(_c)

    # ── Screening settings ──────────────────────────────────────────────────────
    do_screening      = True
    main_col_choice   = None
    new_col_choices   = {}   # {filename: that file's company column}
    threshold         = 70

    if main_cols and new_cols_union:
        st.markdown('<div class="section-header">&#9632;&nbsp; 03 &mdash; Columns to compare</div>', unsafe_allow_html=True)
        do_screening = st.checkbox(
            "Screen the new rows against the main list (fuzzy company-name match)",
            value=True,
            key="sa_do_screen",
            help="Uncheck to append everything without name screening — the email duplicate check still runs.",
        )

        if do_screening:
            st.markdown("<small style='color:#3a4a5e'>The company column is picked per list, so the new lists do not have to name it the same way.</small>", unsafe_allow_html=True)
            st.markdown("")

            # main list first, then one picker per new list, laid out two per row
            _pickers = [("Main list — company column", main_cols, None)]
            for _nf in new_files:
                _fcols = [c for c in new_cols_map.get(_nf.name, []) if c not in BOOKKEEPING_COLS]
                if _fcols:
                    _pickers.append((f"{_nf.name} — company column", _fcols, _nf.name))

            for _i in range(0, len(_pickers), 2):
                _pair = _pickers[_i:_i + 2]
                _pc = st.columns(2, gap="medium")
                for _c, (_lbl, _opts, _fname) in zip(_pc, _pair):
                    with _c:
                        _default = detect_company_col(_opts)
                        _pick = st.selectbox(_lbl, _opts, index=_opts.index(_default))
                        if _fname is None:
                            main_col_choice = _pick
                        else:
                            new_col_choices[_fname] = _pick

            if len(new_files) > 1:
                st.info(f"{len(new_files)} files are screened together — against the main list and against each other — then each file's rows are mapped with its own mapping below.")

            st.markdown("")
            st.markdown('<div class="section-header">&#9632;&nbsp; 04 &mdash; Match sensitivity</div>', unsafe_allow_html=True)
            thresh_col, hint_col = st.columns([3, 1])
            with thresh_col:
                threshold = st.slider(
                    "Match threshold",
                    min_value=50, max_value=100, value=70,
                    help="Lower = catches more variations. 70 is a good default.",
                    label_visibility="collapsed",
                    key="sa_threshold",
                )
            with hint_col:
                st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:1.4rem;font-weight:700;color:#00ff88;text-align:center;padding-top:0.3rem'>{threshold}<span style='font-size:0.7rem;color:#3a4a5e;margin-left:2px'>/ 100</span></div>", unsafe_allow_html=True)
            st.markdown(f"<small style='color:#2a3a4e'>Scores &ge; {threshold} are flagged as matches &nbsp;&mdash;&nbsp; lower threshold catches more variations like <em>Acme Corp</em> vs <em>Acme Corporation</em></small>", unsafe_allow_html=True)

        st.markdown("")

    # ── Per-file column mapping ─────────────────────────────────────────────────
    mappings  = {}   # {filename: {main_col: source_col | APPEND_SKIP}}
    key_cols  = []

    if main_cols and new_files:
        st.markdown('<div class="section-header">&#9632;&nbsp; 05 &mdash; Column mapping</div>', unsafe_allow_html=True)
        st.markdown("<small style='color:#3a4a5e'>For every column in the main list, pick the matching column from the new list — or skip it. Identically named columns are matched automatically.</small>", unsafe_allow_html=True)
        st.markdown("")

        for _nf in new_files:
            _ncols = [c for c in new_cols_map.get(_nf.name, []) if c not in BOOKKEEPING_COLS]
            with st.expander(f"**{_nf.name}**", expanded=len(new_files) == 1):
                if not _ncols:
                    st.warning(f"Could not read columns from {_nf.name}.")
                    continue

                _preselect = ({main_col_choice: new_col_choices[_nf.name]}
                              if main_col_choice and new_col_choices.get(_nf.name) else None)
                mappings[_nf.name] = render_column_mapping(
                    f"Mapping to {main_file.name}", main_cols, _ncols, f"sa_map_{_nf.name}",
                    preselect=_preselect,
                )

        # ── Identity keys ───────────────────────────────────────────────────────
        st.markdown("")
        st.markdown('<div class="section-header">&#9632;&nbsp; 06 &mdash; Duplicate keys</div>', unsafe_allow_html=True)
        st.markdown("<small style='color:#3a4a5e'>Besides the company name, treat these main-list columns as identity: a new row whose value is already present is a duplicate. Email-domain columns ignore anything before the @, and websites and profile links ignore http/https, www and trailing paths.</small>", unsafe_allow_html=True)
        key_cols = st.multiselect(
            "Columns that identify a company",
            main_cols,
            default=default_key_cols(main_cols),
            label_visibility="collapsed",
        )
        if not key_cols:
            st.markdown("<small style='color:#3a4a5e'>No identity keys selected &mdash; only the company name is compared.</small>", unsafe_allow_html=True)
        st.markdown("")

    # ── Run ─────────────────────────────────────────────────────────────────────
    def _current_signature():
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

    run = st.button("&#9889;  Run &mdash; Screen &amp; Append", type="primary", use_container_width=True)

    if run:
        if not main_file or not new_files:
            st.error("Please upload the main list and at least one new list before running.")
        elif not mappings:
            st.error("Column mapping could not be determined. Check your files.")
        else:
            try:
                with st.spinner("Reading files…"):
                    main_file.seek(0)
                    df_main = read_file(main_file, sheet_name=main_sheet)

                    _dfs_new = []
                    new_cols_by_file = {}   # {filename: the company column it was screened on}
                    for _nf in new_files:
                        _nf.seek(0)
                        _d = read_file(_nf, sheet_name=new_sheets.get(_nf.name, 0))
                        _d[SRC_FILE_COL] = _nf.name
                        _d[SRC_ROW_COL]  = list(range(1, len(_d) + 1))
                        _ccol = new_col_choices.get(_nf.name)
                        if _ccol is None:
                            _ccol = detect_company_col([c for c in _d.columns if c not in BOOKKEEPING_COLS])
                        new_cols_by_file[_nf.name] = _ccol
                        _d[NAME_COL] = _d[_ccol] if _ccol in _d.columns else None
                        _dfs_new.append(_d)
                    df_new = pd.concat(_dfs_new, ignore_index=True) if len(_dfs_new) > 1 else _dfs_new[0]

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

                _sig      = _current_signature()
                _prev_sig = (st.session_state.get(RESULTS_SESSION_KEY) or {}).get("signature")

                store_results({
                    "signature":      _sig,
                    "main_names":     main_names,
                    "new_names":      new_names,
                    "matches":        matches,
                    "unique_new":     unique_new,
                    "internal_dups":  internal_dups,
                    "df_new_valid":   df_new_valid,
                    "new_cols_by_file": new_cols_by_file,
                    "main_col":       main_col,
                    "screened":       do_screening,
                    "df_main":        df_main,
                    "main_name":      main_file.name,
                    "main_row_count": len(df_main),
                })

                # store_results clears the exemptions itself when the inputs move on

            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.exception(e)

    visible_results = get_visible_results()

    if visible_results:
        was_screened      = visible_results.get("screened", True)
        df_new_valid      = visible_results["df_new_valid"]
        new_cols_by_file  = visible_results.get("new_cols_by_file", {})
        exempt            = visible_results["exempt"]
        df_main_p         = visible_results.get("df_main")
        main_col_p        = visible_results.get("main_col")
        main_name_p       = visible_results.get("main_name") or "main list"

        if main_file and new_files and visible_results["signature"] != _current_signature():
            st.warning("Inputs or settings have changed since this result was produced — hit **Run** again to refresh it.")

        # ── The rows that got past the name comparison ──────────────────────────
        # Cleaned the way the old Unique Rows download was, but only when screening
        # ran: only then is the company column one the user actually picked.
        _kept = df_new_valid.loc[visible_results["kept_ids"]].copy()
        if was_screened and NAME_COL in _kept.columns:
            _kept[NAME_COL] = _kept[NAME_COL].apply(clean_for_output)
            _kept = _kept[_kept[NAME_COL].astype(str).str.strip() != ""]
            # Push the cleaned name back into each file's own company column —
            # that is the column this file's mapping reads from.
            for _fname, _ccol in new_cols_by_file.items():
                if _ccol in _kept.columns:
                    _m = _kept[SRC_FILE_COL] == _fname
                    _kept.loc[_m, _ccol] = _kept.loc[_m, NAME_COL]
        _kept = _kept.sort_index()

        if df_main_p is None:
            st.info("Hit **Run** to build the combined list.")
        elif not mappings:
            st.info("Re-upload the new lists to restore the column mapping, then run again.")
        else:
            # ── One duplicate pass: names from the cached screening, identity keys
            #    from the mapped rows. Recomputed every rerun, so a Keep click or a
            #    changed mapping feeds straight through to the download.
            if SRC_FILE_COL in _kept.columns:
                _sources = [(str(_fname), _grp) for _fname, _grp in _kept.groupby(SRC_FILE_COL, sort=False)]
            else:
                _sources = [(new_files[0].name if new_files else "new list", _kept)]

            _main_name_col = main_col_p or detect_company_col(df_main_p.columns.tolist())
            _built = build_combined(df_main_p, _main_name_col, mappings, key_cols, _sources, exempt)
            _df_result = _built["df_result"]
            _appended  = _built["appended"]

            _findings = (name_findings(visible_results, exempt) if was_screened else []) + _built["findings"]
            _by_row = {}
            for _f in _findings:
                _by_row.setdefault(_f["row_id"], _f)   # one verdict per row: the first check that fired
            _findings = list(_by_row.values())
            _active   = [f for f in _findings if not f["exempt"]]
            _forced   = [f for f in _findings if f["exempt"]]
            _vs_main  = len([f for f in _active if f["match_origin"] is MAIN_LIST_ORIGIN])
            _vs_new   = len(_active) - _vs_main

            # ── Summary ─────────────────────────────────────────────────────────
            _checked = len(visible_results["new_names"])
            # Two ways a row can carry no usable name: find_matches never bucketed it
            # (its normalised name was empty), or clean_for_output emptied it later.
            _no_name = ((len(visible_results["kept_ids"]) - len(_kept))
                        + (_checked - len(visible_results["usable_ids"])))
            _bits = [f"<strong>{len(_active):,}</strong> duplicates ({_vs_main:,} against the main list, {_vs_new:,} within the new lists)"]
            if _no_name:
                _bits.append(f"<strong>{_no_name:,}</strong> with no usable company name")
            if _forced:
                _bits.append(f"<strong>{len(_forced):,}</strong> forced in")
            st.markdown(
                f"<small style='color:#3a4a5e'>{_checked:,} new rows checked against "
                f"{visible_results.get('main_row_count', 0):,} in the main list and against each other &mdash; "
                + ", ".join(_bits)
                + f", <strong>{len(_appended):,}</strong> appended.</small>",
                unsafe_allow_html=True)
            if not was_screened:
                st.markdown("<small style='color:#3a4a5e'>Name comparison is switched off for this run — only the identity keys above were compared.</small>", unsafe_allow_html=True)
            st.markdown("")

            # ── The one review list ─────────────────────────────────────────────
            if _findings:
                _label = f"Duplicates left out ({len(_active)})"
                if _forced:
                    _label += f" — {len(_forced)} forced in"
                with st.expander(_label, expanded=bool(st.session_state.get(DUPS_OPEN_KEY))):
                    st.markdown("<small style='color:#3a4a5e'>Each row is listed with the check that caught it and the entry it collided with. <strong>Keep</strong> forces one into the output, whichever check flagged it.</small>", unsafe_allow_html=True)
                    st.markdown("")
                    for _f in sorted(_findings, key=lambda f: (f["kind"] != "key", -(f["score"] or 100), f["row_id"])):
                        _where = ("the main list" if _f["match_origin"] is MAIN_LIST_ORIGIN
                                  else _f["match_origin"])
                        _chip = (f"{_f['key']} {_f['score']:.0f}%" if _f["score"] is not None
                                 else _f["key"])
                        _l, _r = st.columns([0.82, 0.18])
                        with _l:
                            st.markdown(f"""
                            <div class="match-card" style="{'opacity:0.6' if _f['exempt'] else ''}">
                              <span class="match-names"><span class="match-main">{_f['row_label']}</span><span class="match-arrow"> &rarr; </span>{_f['match_label']} <span style="color:var(--tx-lo)">in {_where}</span></span>
                              <span class="match-score">{_chip}</span>
                            </div>""", unsafe_allow_html=True)
                        with _r:
                            if _f["exempt"]:
                                st.button("Remove", key=f"unexempt_{_f['row_id']}", type="secondary",
                                          on_click=unexempt_row, args=(_f["row_id"],))
                            else:
                                st.button("Keep", key=f"exempt_{_f['row_id']}", type="secondary",
                                          on_click=exempt_row, args=(_f["row_id"],))
                st.markdown("")

            # ── Result ──────────────────────────────────────────────────────────
            st.markdown(f'<div class="section-header">&#9632;&nbsp; Result &mdash; {main_name_p}</div>', unsafe_allow_html=True)
            _s1, _s2, _s3, _s4 = st.columns(4, gap="small")
            _s1.markdown(f'<div class="stat-box"><div class="stat-num">{len(df_main_p):,}</div><div class="stat-label">Main rows</div></div>', unsafe_allow_html=True)
            _s2.markdown(f'<div class="stat-box"><div class="stat-num">{len(_appended):,}</div><div class="stat-label">Appended rows</div></div>', unsafe_allow_html=True)
            _s3.markdown(f'<div class="stat-box"><div class="stat-num warn">{len(_active):,}</div><div class="stat-label">Duplicates out</div></div>', unsafe_allow_html=True)
            _s4.markdown(f'<div class="stat-box"><div class="stat-num">{len(_df_result):,}</div><div class="stat-label">Total rows</div></div>', unsafe_allow_html=True)

            st.markdown("")
            st.markdown(f"<small style='color:#3a4a5e'>The new rows as they are written into <strong>{main_name_p}</strong> &mdash; its columns, filled from your mapping. Anything you left on &ldquo;skip&rdquo; stays empty, and columns that exist only in the new lists are not carried over.</small>", unsafe_allow_html=True)
            st.dataframe(_appended.head(200), use_container_width=True, hide_index=True)
            if len(_appended) > 200:
                st.markdown(f"<small style='color:#3a4a5e'>Showing first 200 of {len(_appended):,} new rows.</small>", unsafe_allow_html=True)

            # Kept in session state so the button always has its bytes to hand,
            # whichever rerun it ends up being clicked on.
            st.session_state["sa_dl"] = {
                "data": _df_result.to_csv(index=False).encode("utf-8-sig"),
                "name": _output_filename(main_name_p, ".csv"),
                "mime": "text/csv",
            }

            _dl = st.session_state.get("sa_dl")
            if _dl:
                st.markdown("")
                st.download_button(
                    label="&#11015;  Download combined list (CSV)",
                    data=_dl["data"],
                    file_name=_dl["name"],
                    mime=_dl["mime"],
                    use_container_width=True,
                    key="sa_combined_dl",
                )
                st.markdown("")

    else:
        st.markdown("""
        <div style='background:linear-gradient(135deg,#0d1117,#0c1520);border:1px dashed #1e2d3d;border-radius:10px;padding:2.5rem;text-align:center;margin-top:1rem'>
          <div style='font-family:JetBrains Mono,monospace;font-size:2rem;color:#1a2d3e;margin-bottom:0.8rem'>&#9632;</div>
          <div style='color:#3a4a5e;font-size:0.9rem'>Upload your main list and the new lists, then hit <strong style="color:#00ff8866">Run &mdash; Screen &amp; Append</strong>.</div>
          <div style='color:#1e2d3d;font-size:0.78rem;margin-top:0.5rem'>Screening, duplicate checks and the merge all happen in one pass &nbsp;&middot;&nbsp; .xlsx, .xls, .csv</div>
        </div>
        """, unsafe_allow_html=True)

# ── Tab 2: List Diff ─────────────────────────────────────────────────────────────
with tab2:

    st.markdown("""
<div class="tab-desc">
  <strong>List Diff</strong> — merge several secondary lists together, dedup the result on
  a column you choose, then compare it against your main list. Any entry found in
  <em>both</em> is redundant and gets removed from both sides — what's left is only in
  the main list, or only in the secondary lists, never both.
</div>""", unsafe_allow_html=True)

    # ── Upload ─────────────────────────────────────────────────────────────────
    ld_col_a, ld_col_b = st.columns(2, gap="medium")

    with ld_col_a:
        st.markdown('<div class="upload-label">&#9632;&nbsp; 01 &mdash; Main list</div>', unsafe_allow_html=True)
        ld_main_file = st.file_uploader("Main list", type=["xlsx", "xls", "csv"], key="ld_main",
                                         label_visibility="collapsed")

    with ld_col_b:
        st.markdown('<div class="upload-label">&#9632;&nbsp; 02 &mdash; Secondary lists</div>', unsafe_allow_html=True)
        ld_secondary_files = st.file_uploader("Secondary lists", type=["xlsx", "xls", "csv"], key="ld_secondary",
                                               accept_multiple_files=True, label_visibility="collapsed")

    st.markdown("")

    # ── Sheet selection (main, Excel only) ──────────────────────────────────────
    ld_main_sheet = 0
    if ld_main_file and not ld_main_file.name.lower().endswith('.csv'):
        _lds = get_excel_sheets(ld_main_file)
        if _lds:
            ld_main_sheet = st.selectbox("Sheet — Main list", _lds, key="ld_main_sheet")
            st.markdown("")

    # ── Column selection ────────────────────────────────────────────────────────
    ld_main_col_choice = None
    ld_dedup_col_choice = None
    ld_output_cols_choice = None
    ld_sec_cols   = {}   # {filename: compare_col}
    ld_sec_sheets = {}   # {filename: sheet_name}
    ld_sec_col_union = []   # union of all secondary files' columns, in first-seen order

    if ld_main_file and ld_secondary_files:
        try:
            ld_main_cols = read_file(ld_main_file, nrows=0, sheet_name=ld_main_sheet).columns.tolist()
            ld_main_file.seek(0)
        except Exception:
            ld_main_cols = []

        if ld_main_cols:
            st.markdown('<div class="section-header">&#9632;&nbsp; 03 &mdash; Column to compare</div>', unsafe_allow_html=True)
            default_ld_main = detect_company_col(ld_main_cols)
            ld_main_col_choice = st.selectbox(
                "Main list — company column",
                ld_main_cols,
                index=ld_main_cols.index(default_ld_main),
            )
            st.markdown("")
            st.markdown("<small style='color:#3a4a5e'>Pick the matching column in each secondary file &mdash; they don't need the same header name.</small>", unsafe_allow_html=True)
            st.markdown("")

            for ld_file in ld_secondary_files:
                with st.expander(f"**{ld_file.name}**", expanded=True):
                    _ld_sheet = 0
                    if not ld_file.name.lower().endswith('.csv'):
                        _ld_file_sheets = get_excel_sheets(ld_file)
                        if _ld_file_sheets:
                            _ld_sheet = st.selectbox(
                                "Sheet to use",
                                _ld_file_sheets,
                                key=f"ld_sheet_{ld_file.name}",
                            )
                            st.markdown("")
                    ld_sec_sheets[ld_file.name] = _ld_sheet

                    try:
                        ld_cols_preview = read_file(ld_file, nrows=0, sheet_name=_ld_sheet).columns.tolist()
                        ld_file.seek(0)
                    except Exception:
                        st.warning(f"Could not read columns from {ld_file.name}.")
                        continue

                    default_ld_sec = detect_company_col(ld_cols_preview)
                    ld_sec_cols[ld_file.name] = st.selectbox(
                        "Company column in this file",
                        ld_cols_preview,
                        index=ld_cols_preview.index(default_ld_sec),
                        key=f"ld_col_{ld_file.name}",
                    )

                    for _c in ld_cols_preview:
                        if _c not in ld_sec_col_union:
                            ld_sec_col_union.append(_c)

            st.markdown("")

            if ld_sec_col_union:
                st.markdown('<div class="section-header">&#9632;&nbsp; 04 &mdash; Deduplicate secondary lists</div>', unsafe_allow_html=True)
                st.markdown("<small style='color:#3a4a5e'>After merging, rows whose value in this column fuzzy-match each other are collapsed to one &mdash; the first occurrence is kept.</small>", unsafe_allow_html=True)
                st.markdown("")
                default_ld_dedup = detect_company_col(ld_sec_col_union)
                ld_dedup_col_choice = st.selectbox(
                    "Deduplicate merged secondary list on column",
                    ld_sec_col_union,
                    index=ld_sec_col_union.index(default_ld_dedup),
                )
                st.markdown("")

            ld_output_col_union = ld_main_cols + [c for c in ld_sec_col_union if c not in ld_main_cols]
            st.markdown('<div class="section-header">&#9632;&nbsp; 05 &mdash; Output columns</div>', unsafe_allow_html=True)
            st.markdown("<small style='color:#3a4a5e'>Columns to keep in the result.</small>", unsafe_allow_html=True)
            st.markdown("")
            ld_output_cols_choice = st.multiselect(
                "Columns to include in the output",
                ld_output_col_union,
                default=[],
            )
            st.markdown("")

    st.markdown('<div class="section-header">&#9632;&nbsp; 06 &mdash; Match sensitivity</div>', unsafe_allow_html=True)

    ld_thresh_col, ld_hint_col = st.columns([3, 1])
    with ld_thresh_col:
        ld_threshold = st.slider(
            "Match threshold",
            min_value=50, max_value=100, value=70,
            help="Lower = catches more variations. 70 is a good default.",
            label_visibility="collapsed",
            key="ld_threshold",
        )
    with ld_hint_col:
        st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:1.4rem;font-weight:700;color:#00ff88;text-align:center;padding-top:0.3rem'>{ld_threshold}<span style='font-size:0.7rem;color:#3a4a5e;margin-left:2px'>/ 100</span></div>", unsafe_allow_html=True)

    st.markdown(f"<small style='color:#2a3a4e'>Entries scoring &ge; {ld_threshold} against each other are treated as the same company and dropped from both lists.</small>", unsafe_allow_html=True)
    st.markdown("")

    ld_run = st.button("&#9889;  Run List Diff", type="primary", use_container_width=True)

    if ld_run:
        if not ld_main_file or not ld_secondary_files:
            st.error("Please upload the main list and at least one secondary list.")
        elif not ld_sec_cols:
            st.error("Column selection could not be determined. Check your files.")
        else:
            try:
                with st.spinner("Reading files…"):
                    df_main_ld = read_file(ld_main_file, sheet_name=ld_main_sheet)

                main_col_ld = ld_main_col_choice or detect_company_col(df_main_ld.columns.tolist())
                df_main_valid = df_main_ld.dropna(subset=[main_col_ld]).reset_index(drop=True)
                main_values = df_main_valid[main_col_ld].astype(str).tolist()

                with st.spinner("Merging secondary lists…"):
                    sec_frames = []
                    for ld_file in ld_secondary_files:
                        if ld_file.name not in ld_sec_cols:
                            continue
                        df_sec = read_file(ld_file, sheet_name=ld_sec_sheets.get(ld_file.name, 0))
                        sec_col = ld_sec_cols[ld_file.name]
                        df_sec = df_sec.dropna(subset=[sec_col]).reset_index(drop=True)
                        df_sec["__ld_compare__"] = df_sec[sec_col].astype(str)
                        sec_frames.append(df_sec)

                if not sec_frames:
                    st.error("Could not read any of the secondary files.")
                else:
                    df_sec_merged = pd.concat(sec_frames, ignore_index=True, sort=False)
                    sec_count_before_dedup = len(df_sec_merged)

                    with st.spinner("Deduping merged secondary list…"):
                        dedup_col_ld = ld_dedup_col_choice if ld_dedup_col_choice in df_sec_merged.columns else "__ld_compare__"
                        dedup_values_ld = df_sec_merged[dedup_col_ld].fillna("").astype(str).tolist()
                        internal_dups_ld = find_internal_duplicates(dedup_values_ld, ld_threshold)
                        dup_ids_ld = {d["id_dup"] for d in internal_dups_ld}
                        dedup_idx_ld = [i for i in range(len(df_sec_merged)) if i not in dup_ids_ld]
                        df_sec_merged = df_sec_merged.iloc[dedup_idx_ld].reset_index(drop=True)

                    sec_values = df_sec_merged["__ld_compare__"].tolist()

                    with st.spinner("Comparing against main list…"):
                        keep_main_idx, keep_sec_idx, overlaps = find_symmetric_overlap(
                            main_values, sec_values, ld_threshold
                        )

                    df_main_result = df_main_valid.iloc[keep_main_idx].copy()
                    df_sec_result = df_sec_merged.iloc[keep_sec_idx].drop(columns=["__ld_compare__"]).copy()

                    df_diff_result = pd.concat([df_main_result, df_sec_result], ignore_index=True, sort=False)

                    if ld_output_cols_choice:
                        _keep_cols_ld = [c for c in ld_output_cols_choice if c in df_diff_result.columns]
                        df_diff_result = df_diff_result[_keep_cols_ld]

                    st.session_state["ld_result"] = {
                        "df": df_diff_result,
                        "main_count": len(main_values),
                        "sec_count": sec_count_before_dedup,
                        "internal_dups": internal_dups_ld,
                        "overlaps": overlaps,
                        "main_file_name": getattr(ld_main_file, "name", "list_diff"),
                    }

            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.exception(e)

    ld_result = st.session_state.get("ld_result")

    if ld_result:
        df_diff_result = ld_result["df"]

        st.markdown('<div class="section-header">&#9632;&nbsp; Result</div>', unsafe_allow_html=True)

        ld_s1, ld_s2, ld_s3, ld_s4, ld_s5 = st.columns(5, gap="small")
        with ld_s1:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{ld_result["main_count"]:,}</div><div class="stat-label">Main rows</div></div>', unsafe_allow_html=True)
        with ld_s2:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{ld_result["sec_count"]:,}</div><div class="stat-label">Secondary rows (merged)</div></div>', unsafe_allow_html=True)
        with ld_s3:
            st.markdown(f'<div class="stat-box"><div class="stat-num warn">{len(ld_result["internal_dups"]):,}</div><div class="stat-label">Secondary dups removed</div></div>', unsafe_allow_html=True)
        with ld_s4:
            st.markdown(f'<div class="stat-box"><div class="stat-num warn">{len(ld_result["overlaps"]):,}</div><div class="stat-label">Redundant pairs removed</div></div>', unsafe_allow_html=True)
        with ld_s5:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{len(df_diff_result):,}</div><div class="stat-label">Unique rows</div></div>', unsafe_allow_html=True)

        st.markdown("")
        st.dataframe(df_diff_result.head(200), use_container_width=True, hide_index=True)
        if len(df_diff_result) > 200:
            st.markdown(f"<small style='color:#3a4a5e'>Showing first 200 of {len(df_diff_result):,} rows.</small>", unsafe_allow_html=True)

        st.markdown("")
        ld_dl_a, ld_dl_b = st.columns(2, gap="small")
        ld_csv = df_diff_result.to_csv(index=False).encode("utf-8-sig")
        _ld_stem = ld_result["main_file_name"]
        for _e in ('.xlsx', '.xls', '.csv'):
            if _ld_stem.lower().endswith(_e):
                _ld_stem = _ld_stem[:-len(_e)]
                break
        _ld_filename_base = f"{_ld_stem}_list_diff"
        with ld_dl_a:
            st.download_button(
                label="&#11015;  Download CSV",
                data=ld_csv,
                file_name=_output_filename(_ld_filename_base, ".csv"),
                mime="text/csv",
                use_container_width=True,
            )
        with ld_dl_b:
            ld_excel_buf = io.BytesIO()
            with pd.ExcelWriter(ld_excel_buf, engine="openpyxl") as writer:
                df_diff_result.to_excel(writer, index=False, sheet_name="List Diff")
            st.download_button(
                label="&#11015;  Download Excel",
                data=ld_excel_buf.getvalue(),
                file_name=_output_filename(_ld_filename_base, ".xlsx"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        if ld_result["internal_dups"]:
            st.markdown("")
            st.markdown('<div class="section-header">&#9664;&#9654;&nbsp; Duplicates merged within the secondary lists</div>', unsafe_allow_html=True)
            for dup in sorted(ld_result["internal_dups"], key=lambda d: -d["score"]):
                score_class = "high" if dup["score"] >= 90 else ""
                st.markdown(f"""
                <div class="match-card">
                  <span class="match-names">
                    <span class="match-main">{dup["name_keeper"]}</span>
                    <span class="match-arrow"> &lArr; dup &mdash; </span>
                    {dup["name_dup"]}
                  </span>
                  <span class="match-score {score_class}">{dup["score"]}%</span>
                </div>""", unsafe_allow_html=True)

        if ld_result["overlaps"]:
            st.markdown("")
            st.markdown('<div class="section-header">&#8635;&nbsp; Redundant entries removed from both lists</div>', unsafe_allow_html=True)
            for ov in sorted(ld_result["overlaps"], key=lambda d: -d["score"]):
                score_class = "high" if ov["score"] >= 90 else ""
                st.markdown(f"""
                <div class="match-card">
                  <span class="match-names">
                    <span class="match-main">{ov["name_a"]}</span>
                    <span class="match-arrow"> &harr; </span>
                    {ov["name_b"]}
                  </span>
                  <span class="match-score {score_class}">{ov["score"]}%</span>
                </div>""", unsafe_allow_html=True)

    elif not (ld_main_file and ld_secondary_files):
        st.markdown("""
        <div style='background:linear-gradient(135deg,#0d1117,#0c1520);border:1px dashed #1e2d3d;border-radius:10px;padding:2.5rem;text-align:center;margin-top:1rem'>
          <div style='font-family:JetBrains Mono,monospace;font-size:2rem;color:#1a2d3e;margin-bottom:0.8rem'>&#9632;</div>
          <div style='color:#3a4a5e;font-size:0.9rem'>Upload your main list and two or more secondary lists, then hit <strong style="color:#00ff8866">Run List Diff</strong>.</div>
          <div style='color:#1e2d3d;font-size:0.78rem;margin-top:0.5rem'>Supports .xlsx, .xls, and .csv</div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("<br><hr style='border-color:#0d1520;margin-top:2rem'>", unsafe_allow_html=True)
st.markdown("<small style='color:#1e2d3d;font-family:JetBrains Mono,monospace;font-size:0.68rem'>RapidFuzz token_sort_ratio &mdash; handles reordering, abbreviations &amp; legal suffix differences. Promoted matches appear in downloads immediately.</small>", unsafe_allow_html=True)
