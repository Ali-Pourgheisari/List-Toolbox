import streamlit as st
import pandas as pd
import re
import io
import csv
import zipfile
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
MOVED_SESSION_KEY   = "screener_moved_match_ids"
DUP_RESCUED_KEY     = "screener_rescued_dup_ids"

APPEND_RESULTS_KEY = "appender_results"
APPEND_RESCUED_KEY = "appender_rescued_row_ids"

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

def detect_company_col(columns) -> str:
    # Checked strongest-hint-first across ALL columns, not first-column-first —
    # otherwise a "Full Name" column ahead of "Company Name" wins on the bare
    # "name" substring, and headers like "...Company Filter" false-match "company".
    priority_hints = ['company name', 'company', 'organisation', 'organization', 'account name', 'firm']
    fallback_hints = ['name', 'account']
    lower_cols = [c.lower() for c in columns]
    for hint in priority_hints + fallback_hints:
        for col, lc in zip(columns, lower_cols):
            if hint in lc:
                return col
    return columns[0]

def _unwrap_double_encoded_csv(text):
    """Some exports wrap every row in an extra layer of CSV quoting, so each
    row parses as a single field whose content is itself a full CSV row.
    Detect that pattern, strip the outer layer, and return the rows already
    split into fields (as a list of lists) rather than reassembled text:
    the leading field of the inner row is sometimes left unquoted even when
    it contains a literal comma, which a second blind CSV parse can't tell
    apart from an actual column boundary. Any such stray split is merged
    back into the leading field using the header's column count as the
    source of truth."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) < 2:
        return None
    outer = []
    for ln in lines:
        try:
            fields = next(csv.reader([ln]))
        except csv.Error:
            return None
        if len(fields) != 1:
            return None
        outer.append(fields[0])
    if not any(re.search(r'[,;]', u) for u in outer[:5]):
        return None
    rows = [next(csv.reader([u])) for u in outer]
    n_cols = len(rows[0])
    for row in rows[1:]:
        while len(row) > n_cols:
            row[0:2] = [row[0] + ',' + row[1]]
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
        rows = _unwrap_double_encoded_csv(text)
        if rows is not None:
            df = pd.DataFrame(rows[1:], columns=rows[0])
            if nrows is not None:
                df = df.head(nrows)
            return normalize_country_cols(df)
        try:
            sep = csv.Sniffer().sniff(text[:4096], delimiters=',;').delimiter
        except csv.Error:
            sep = ','
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
    previous_payload  = st.session_state.get(RESULTS_SESSION_KEY)
    previous_moved    = list(st.session_state.get(MOVED_SESSION_KEY, []))
    previous_rescued  = list(st.session_state.get(DUP_RESCUED_KEY, []))
    st.session_state[RESULTS_SESSION_KEY] = payload
    if previous_payload and previous_payload.get("signature") == payload.get("signature"):
        st.session_state[MOVED_SESSION_KEY] = previous_moved
        st.session_state[DUP_RESCUED_KEY]   = previous_rescued
    else:
        st.session_state[MOVED_SESSION_KEY] = []
        st.session_state[DUP_RESCUED_KEY]   = []


def get_visible_results():
    payload = st.session_state.get(RESULTS_SESSION_KEY)
    if not payload:
        return None

    moved_ids = set(st.session_state.get(MOVED_SESSION_KEY, []))
    promoted = [item for item in payload["matches"] if item["id"] in moved_ids]
    remaining_matches = [item for item in payload["matches"] if item["id"] not in moved_ids]

    internal_dups    = payload.get("internal_dups", [])
    rescued_dup_ids  = set(st.session_state.get(DUP_RESCUED_KEY, []))
    dup_ids          = {item["id_dup"] for item in internal_dups if item["id_dup"] not in rescued_dup_ids}
    clean_unique     = [idx for idx in payload["unique_new"] if idx not in dup_ids]
    rescued_indices  = [item["id_dup"] for item in internal_dups if item["id_dup"] in rescued_dup_ids]
    unique_indices   = clean_unique + [item["id"] for item in promoted] + rescued_indices

    return {
        "signature": payload["signature"],
        "main_names": payload["main_names"],
        "new_names": payload["new_names"],
        "matches": remaining_matches,
        "promoted": promoted,
        "unique_indices": unique_indices,
        "df_new_valid": payload["df_new_valid"],
        "new_col": payload["new_col"],
        "internal_dups": internal_dups,
        "rescued_dup_ids": rescued_dup_ids,
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


def rescue_dup(dup_id: int) -> None:
    rescued = list(st.session_state.get(DUP_RESCUED_KEY, []))
    if dup_id not in rescued:
        rescued.append(dup_id)
        st.session_state[DUP_RESCUED_KEY] = rescued


def unrescue_dup(dup_id: int) -> None:
    rescued = list(st.session_state.get(DUP_RESCUED_KEY, []))
    if dup_id in rescued:
        rescued.remove(dup_id)
        st.session_state[DUP_RESCUED_KEY] = rescued


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


def rescue_append_row(main_name: str, row_id: str) -> None:
    rescued = {k: set(v) for k, v in st.session_state.get(APPEND_RESCUED_KEY, {}).items()}
    rescued.setdefault(main_name, set()).add(row_id)
    st.session_state[APPEND_RESCUED_KEY] = rescued


def unrescue_append_row(main_name: str, row_id: str) -> None:
    rescued = {k: set(v) for k, v in st.session_state.get(APPEND_RESCUED_KEY, {}).items()}
    rescued.setdefault(main_name, set()).discard(row_id)
    st.session_state[APPEND_RESCUED_KEY] = rescued


def compute_append_payload(main_name, main_file, main_sheet, mappings, email_col, new_files, sheets_map, ranges_map):
    """
    Map every file's rows onto the main list's columns and flag duplicate emails
    without dropping anything yet — the caller decides what stays out based on
    which flagged rows the user has since rescued.
    Returns {main_name, df_main, mapped_rows, skip_map}.
    mapped_rows carries two bookkeeping columns, "_row_id" and "_source_file",
    which the renderer strips before the final concat.
    skip_map: {row_id: {reason, email, comparison, label, row_num, file}}
    """
    main_file.seek(0)
    df_main = read_file(main_file, sheet_name=main_sheet)
    main_name_col = detect_company_col(df_main.columns.tolist())

    # email -> display label, seeded from the main list, then extended with
    # every newly-kept row so later files also dedupe against earlier ones.
    existing_email_map = {}
    if email_col and email_col in df_main.columns:
        for _, r in df_main.dropna(subset=[email_col]).iterrows():
            key = str(r[email_col]).strip().lower()
            if key and key not in existing_email_map:
                label = r.get(main_name_col)
                existing_email_map[key] = str(label).strip() if pd.notna(label) else key

    mapped_chunks = []
    skip_map = {}

    for ap_file in new_files:
        if ap_file.name not in mappings:
            continue
        ap_file.seek(0)
        df_ap_new = read_file(ap_file, sheet_name=sheets_map.get(ap_file.name, 0))
        file_mapping = mappings[ap_file.name]
        from_r, to_r = ranges_map.get(ap_file.name, (1, len(df_ap_new)))
        df_slice = df_ap_new.iloc[from_r - 1:to_r].reset_index(drop=True)

        email_source = file_mapping.get(email_col, APPEND_SKIP) if email_col else APPEND_SKIP
        name_source  = file_mapping.get(main_name_col, APPEND_SKIP)

        row_ids = [f"{main_name}||{ap_file.name}||{from_r + i}" for i in range(len(df_slice))]
        mapped_full = pd.DataFrame({
            mc: (df_slice[src].values if src != APPEND_SKIP and src in df_slice.columns
                 else [None] * len(df_slice))
            for mc, src in file_mapping.items()
        })
        mapped_full["_row_id"]      = row_ids
        mapped_full["_source_file"] = ap_file.name

        if email_col and email_source != APPEND_SKIP and email_source in df_slice.columns:
            seen_in_batch = {}
            for i in range(len(df_slice)):
                val = df_slice[email_source].iloc[i]
                key = str(val).strip().lower() if pd.notna(val) else ""
                if not key:
                    continue
                label = None
                if name_source != APPEND_SKIP and name_source in df_slice.columns:
                    nv = df_slice[name_source].iloc[i]
                    if pd.notna(nv) and str(nv).strip():
                        label = str(nv).strip()
                if key in existing_email_map:
                    skip_map[row_ids[i]] = {
                        "reason": "existing", "email": val,
                        "comparison": existing_email_map[key],
                        "label": label or key, "row_num": from_r + i, "file": ap_file.name,
                    }
                elif key in seen_in_batch:
                    skip_map[row_ids[i]] = {
                        "reason": "internal", "email": val,
                        "comparison": seen_in_batch[key],
                        "label": label or key, "row_num": from_r + i, "file": ap_file.name,
                    }
                else:
                    seen_in_batch[key] = label or key
            # Fold this file's unique emails into the cross-file map only now —
            # doing it inline above would make same-file dupes match "existing"
            # (checked first) instead of "internal" before they're ever compared.
            existing_email_map.update(seen_in_batch)

        for col in mapped_full.columns:
            if col in ("_row_id", "_source_file"):
                continue
            if _is_website_col(col):
                mapped_full[col] = mapped_full[col].apply(_norm_website)
            elif _is_emaildomain_col(col):
                mapped_full[col] = mapped_full[col].apply(_norm_emaildomain)

        mapped_chunks.append(mapped_full)

    mapped_rows = pd.concat(mapped_chunks, ignore_index=True) if mapped_chunks else pd.DataFrame()

    return {
        "main_name":   main_name,
        "df_main":     df_main,
        "mapped_rows": mapped_rows,
        "skip_map":    skip_map,
    }


def render_append_payload(payload):
    """Render one main list's append result, applying the current rescue state,
    and return the final combined DataFrame for download."""
    main_name   = payload["main_name"]
    df_main     = payload["df_main"]
    mapped_rows = payload["mapped_rows"]
    skip_map    = payload["skip_map"]

    rescued         = st.session_state.get(APPEND_RESCUED_KEY, {}).get(main_name, set())
    active_skip_ids = {rid for rid in skip_map if rid not in rescued}

    if len(mapped_rows):
        keep_mask = ~mapped_rows["_row_id"].isin(active_skip_ids)
        kept_rows = mapped_rows[keep_mask].drop(columns=["_row_id", "_source_file"]).reset_index(drop=True)
    else:
        kept_rows = mapped_rows

    df_result     = pd.concat([df_main, kept_rows], ignore_index=True) if len(kept_rows) else df_main.copy()
    original_rows = len(df_main)
    appended_rows = len(kept_rows)
    skipped_count = len(active_skip_ids)

    st.markdown(f'<div class="section-header">&#9632;&nbsp; Result — {main_name}</div>', unsafe_allow_html=True)
    stat_cols = st.columns(4 if skip_map else 3, gap="small")
    stat_cols[0].markdown(f'<div class="stat-box"><div class="stat-num">{original_rows:,}</div><div class="stat-label">Main rows</div></div>', unsafe_allow_html=True)
    stat_cols[1].markdown(f'<div class="stat-box"><div class="stat-num">{appended_rows:,}</div><div class="stat-label">Appended rows</div></div>', unsafe_allow_html=True)
    if skip_map:
        stat_cols[2].markdown(f'<div class="stat-box"><div class="stat-num warn">{skipped_count:,}</div><div class="stat-label">Skipped (email)</div></div>', unsafe_allow_html=True)
    stat_cols[-1].markdown(f'<div class="stat-box"><div class="stat-num">{len(df_result):,}</div><div class="stat-label">Total rows</div></div>', unsafe_allow_html=True)

    st.markdown("")
    st.dataframe(kept_rows.head(200), use_container_width=True, hide_index=True)
    if len(kept_rows) > 200:
        st.markdown(f"<small style='color:#3a4a5e'>Showing first 200 of {len(kept_rows):,} new rows.</small>", unsafe_allow_html=True)

    if skip_map:
        st.markdown("")
        st.markdown('<div class="section-header">&#9664;&#9654;&nbsp; Skipped rows (duplicate email)</div>', unsafe_allow_html=True)
        st.markdown("<small style='color:#3a4a5e'>These rows were left out because their email already exists. Click <strong>Include anyway</strong> if it's not actually a duplicate.</small>", unsafe_allow_html=True)
        st.markdown("")
        for rid, info in sorted(skip_map.items(), key=lambda kv: kv[1]["row_num"]):
            is_rescued = rid in rescued
            row_l, row_r = st.columns([0.82, 0.18])
            reason_txt = "already in main list" if info["reason"] == "existing" else "duplicate within this file"
            with row_l:
                st.markdown(f"""
                <div class="match-card" style="{'opacity:0.45' if is_rescued else ''}">
                  <span class="match-names"><span class="match-main">{info['label']}</span><span class="match-arrow"> {reason_txt} &mdash; </span>{info['comparison']} <span style="color:var(--tx-lo)">({info['email']})</span></span>
                  <span class="match-score">{info['file']} &middot; row {info['row_num']}</span>
                </div>""", unsafe_allow_html=True)
            with row_r:
                if is_rescued:
                    if st.button("Remove", key=f"unrescue_ap_{main_name}_{rid}", type="secondary"):
                        unrescue_append_row(main_name, rid)
                        st.rerun()
                else:
                    if st.button("Include anyway", key=f"rescue_ap_{main_name}_{rid}", type="secondary"):
                        rescue_append_row(main_name, rid)
                        st.rerun()

    return df_result


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

tab1, tab2, tab3 = st.tabs(["  Unique Rows Finder  ", "  List Appender  ", "  List Diff  "])

# ── Tab 1: Unique Rows Finder ───────────────────────────────────────────────────
with tab1:

    st.markdown("""
<div class="tab-desc">
  <strong>Unique Rows Finder</strong> — upload your main database and a new list, then
  run a fuzzy company-name match to flag entries that already exist. Move confirmed
  matches out, keep clean records in.
</div>""", unsafe_allow_html=True)

    # ── Upload ─────────────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        st.markdown('<div class="upload-label">&#9632;&nbsp; 01 &mdash; Main database</div>', unsafe_allow_html=True)
        main_file = st.file_uploader("Main database", type=["xlsx", "xls", "csv"], key="main",
                                      label_visibility="collapsed")
        if isinstance(main_file, list):
            if len(main_file) > 1:
                st.warning("Only one file is allowed here. Using the first file.")
            main_file = main_file[0] if main_file else None

    with col_b:
        st.markdown('<div class="upload-label">&#9632;&nbsp; 02 &mdash; New companies</div>', unsafe_allow_html=True)
        new_files = st.file_uploader("New companies to check", type=["xlsx", "xls", "csv"], key="new",
                                      accept_multiple_files=True, label_visibility="collapsed")
        if not isinstance(new_files, list):
            new_files = [new_files] if new_files else []
        new_file = new_files[0] if new_files else None

    st.markdown("")

    # ── Sheet selection (Excel only) ────────────────────────────────────────────
    main_sheet = 0
    new_sheet  = 0

    if main_file and not main_file.name.lower().endswith('.csv'):
        _ms = get_excel_sheets(main_file)
        if _ms:
            main_sheet = st.selectbox("Sheet — Main database", _ms, key="main_sheet")
            st.markdown("")

    if new_file and not new_file.name.lower().endswith('.csv'):
        _ns = get_excel_sheets(new_file)
        if _ns:
            new_sheet = st.selectbox("Sheet — New companies", _ns, key="new_sheet")
            st.markdown("")

    # ── Column selection ────────────────────────────────────────────────────────
    main_col_choice    = None
    new_col_choice     = None
    output_col_choices = None

    if main_file and new_files:
        if len(new_files) > 1:
            st.info(f"{len(new_files)} files will be combined and screened together. Column configuration is based on the first file.")
        try:
            main_cols = read_file(main_file, nrows=0, sheet_name=main_sheet).columns.tolist()
            new_cols  = read_file(new_files[0], nrows=0, sheet_name=new_sheet).columns.tolist()
            main_file.seek(0)
            for _nf in new_files:
                _nf.seek(0)

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
        if not main_file or not new_files:
            st.error("Please upload both files before running.")
        else:
            try:
                with st.spinner("Reading files…"):
                    df_main = read_file(main_file, sheet_name=main_sheet)
                    if len(new_files) == 1:
                        df_new = read_file(new_files[0], sheet_name=new_sheet)
                    else:
                        _dfs_new = []
                        for _i, _nf in enumerate(new_files):
                            _nf.seek(0)
                            _dfs_new.append(read_file(_nf, sheet_name=new_sheet if _i == 0 else 0))
                        df_new = pd.concat(_dfs_new, ignore_index=True)

                main_col = main_col_choice or detect_company_col(df_main.columns.tolist())
                new_col  = new_col_choice  or detect_company_col(df_new.columns.tolist())

                main_names   = df_main[main_col].dropna().astype(str).tolist()
                df_new_valid = df_new.dropna(subset=[new_col]).reset_index(drop=True)
                new_names    = df_new_valid[new_col].astype(str).tolist()

                with st.spinner("Screening against main database…"):
                    matches, unique_new = find_matches(main_names, new_names, threshold)

                with st.spinner("Checking for within-list duplicates…"):
                    internal_dups = find_internal_duplicates(new_names, threshold)

                store_results({
                    "signature": {
                        "main_file": getattr(main_file, "name", ""),
                        "main_size": getattr(main_file, "size", None),
                        "new_file": new_files[0].name if new_files else "",
                        "new_size": sum(getattr(_nf, "size", 0) for _nf in new_files),
                        "threshold": threshold,
                    },
                    "main_names": main_names,
                    "new_names": new_names,
                    "matches": matches,
                    "unique_new": unique_new,
                    "internal_dups": internal_dups,
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
        internal_dups     = visible_results.get("internal_dups", [])
        rescued_dup_ids   = visible_results.get("rescued_dup_ids", set())

        st.markdown('<div class="section-header">&#9632;&nbsp; Results</div>', unsafe_allow_html=True)

        _active_dups = len([d for d in internal_dups if d["id_dup"] not in rescued_dup_ids])
        s1, s2, s3, s4, s5 = st.columns(5, gap="small")
        with s1:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{len(visible_results["main_names"]):,}</div><div class="stat-label">Main DB</div></div>', unsafe_allow_html=True)
        with s2:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{len(visible_results["new_names"]):,}</div><div class="stat-label">Checked</div></div>', unsafe_allow_html=True)
        with s3:
            st.markdown(f'<div class="stat-box"><div class="stat-num warn">{len(remaining_matches):,}</div><div class="stat-label">In Main DB</div></div>', unsafe_allow_html=True)
        with s4:
            st.markdown(f'<div class="stat-box"><div class="stat-num warn">{_active_dups:,}</div><div class="stat-label">List Dups</div></div>', unsafe_allow_html=True)
        with s5:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{len(unique_indices):,}</div><div class="stat-label">Clean &amp; Unique</div></div>', unsafe_allow_html=True)

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
                _src_name = visible_results["signature"].get("main_file", "output")
                st.download_button(
                    label="&#11015;  Download CSV",
                    data=df_out.to_csv(index=False).encode("utf-8-sig"),
                    file_name=_output_filename(_src_name, ".csv"),
                    mime="text/csv",
                    use_container_width=True,
                    key="screener_dl_csv",
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

        if internal_dups:
            st.markdown("")
            st.markdown('<div class="section-header">&#9664;&#9654;&nbsp; Duplicates within the new list</div>', unsafe_allow_html=True)
            st.markdown("<small style='color:#3a4a5e'>These pairs are fuzzy duplicates of each other. Only the first occurrence is kept — click <strong>Keep Both</strong> if they are not actually the same company.</small>", unsafe_allow_html=True)
            st.markdown("")
            for dup in sorted(internal_dups, key=lambda d: -d["score"]):
                is_rescued  = dup["id_dup"] in rescued_dup_ids
                score_class = "high" if dup["score"] >= 90 else ""
                dup_l, dup_r = st.columns([0.82, 0.18])
                with dup_l:
                    st.markdown(f"""
                    <div class="match-card" style="{'opacity:0.45' if is_rescued else ''}">
                      <span class="match-names">
                        <span class="match-main">{dup["name_keeper"]}</span>
                        <span class="match-arrow"> &lArr; dup &mdash; </span>
                        {dup["name_dup"]}
                      </span>
                      <span class="match-score {score_class}">{dup["score"]}%</span>
                    </div>""", unsafe_allow_html=True)
                with dup_r:
                    if is_rescued:
                        if st.button("Return", key=f"unrescue_dup_{dup['id_dup']}", type="secondary"):
                            unrescue_dup(dup["id_dup"])
                            st.rerun()
                    else:
                        if st.button("Keep Both", key=f"rescue_dup_{dup['id_dup']}", type="secondary"):
                            rescue_dup(dup["id_dup"])
                            st.rerun()

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

    st.markdown("""
<div class="tab-desc">
  <strong>List Appender</strong> — merge one or more files into up to two main lists.
  Map each file's columns independently per main list, detect duplicate emails,
  and download each combined result separately.
</div>""", unsafe_allow_html=True)

    # ── Upload ─────────────────────────────────────────────────────────────────
    if "ap_num_main" not in st.session_state:
        st.session_state["ap_num_main"] = 1

    ap_col_main, ap_col_new = st.columns(2, gap="medium")

    with ap_col_main:
        st.markdown('<div class="upload-label">&#9632;&nbsp; 01 &mdash; Main list(s)</div>', unsafe_allow_html=True)
        ap_main_file_1 = st.file_uploader("Main list 1", type=["xlsx", "xls", "csv"], key="ap_main_1",
                                           label_visibility="collapsed")
        if st.session_state["ap_num_main"] >= 2:
            st.markdown("<div style='margin-top:0.3rem'></div>", unsafe_allow_html=True)
            ap_main_file_2 = st.file_uploader("Main list 2", type=["xlsx", "xls", "csv"], key="ap_main_2",
                                               label_visibility="collapsed")
            if st.button("✕  Remove second list", key="ap_remove_main", use_container_width=True):
                st.session_state["ap_num_main"] = 1
                st.session_state.pop("ap_main_2", None)
                st.rerun()
        else:
            ap_main_file_2 = None
            if st.button("＋  Add second main list", key="ap_add_main", use_container_width=True):
                st.session_state["ap_num_main"] = 2
                st.rerun()

    with ap_col_new:
        st.markdown('<div class="upload-label">&#9632;&nbsp; 02 &mdash; Files to append</div>', unsafe_allow_html=True)
        ap_new_files = st.file_uploader("Files to append", type=["xlsx", "xls", "csv"], key="ap_new",
                                         accept_multiple_files=True, label_visibility="collapsed")

    st.markdown("")

    # ── Sheet selection (Excel only) ────────────────────────────────────────────
    ap_main_sheet_1 = 0
    ap_main_sheet_2 = 0

    _sheet_selectors = []
    if ap_main_file_1 and not ap_main_file_1.name.lower().endswith('.csv'):
        _ams1 = get_excel_sheets(ap_main_file_1)
        if _ams1:
            _sheet_selectors.append(("Sheet — Main list 1", _ams1, "ap_main_sheet_1", 1))
    if ap_main_file_2 and not ap_main_file_2.name.lower().endswith('.csv'):
        _ams2 = get_excel_sheets(ap_main_file_2)
        if _ams2:
            _sheet_selectors.append(("Sheet — Main list 2", _ams2, "ap_main_sheet_2", 2))

    if _sheet_selectors:
        _sc = st.columns(len(_sheet_selectors), gap="small")
        for _i, (_lbl, _sheets, _key, _which) in enumerate(_sheet_selectors):
            with _sc[_i]:
                _sel = st.selectbox(_lbl, _sheets, key=_key)
                if _which == 1:
                    ap_main_sheet_1 = _sel
                else:
                    ap_main_sheet_2 = _sel
        st.markdown("")

    # ── Per-file column mapping ─────────────────────────────────────────────────
    ap_mappings_1 = {}   # {filename: {main1_col: source_col | APPEND_SKIP}}
    ap_mappings_2 = {}   # {filename: {main2_col: source_col | APPEND_SKIP}}
    ap_ranges     = {}   # {filename: (from_row, to_row)}
    ap_sheets     = {}   # {filename: sheet_name}
    ap_email_col_1 = None
    ap_email_col_2 = None

    if ap_main_file_1 and ap_new_files:
        try:
            ap_main_cols_1 = read_file(ap_main_file_1, nrows=0, sheet_name=ap_main_sheet_1).columns.tolist()
            ap_main_file_1.seek(0)
        except Exception:
            ap_main_cols_1 = []

        try:
            ap_main_cols_2 = (
                read_file(ap_main_file_2, nrows=0, sheet_name=ap_main_sheet_2).columns.tolist()
                if ap_main_file_2 else []
            )
            if ap_main_file_2:
                ap_main_file_2.seek(0)
        except Exception:
            ap_main_cols_2 = []

        if ap_main_cols_1:
            st.markdown('<div class="section-header">&#9632;&nbsp; 03 &mdash; Column mapping</div>', unsafe_allow_html=True)
            st.markdown("<small style='color:#3a4a5e'>For every column in each main list, pick the matching column from the file to append — or skip it.</small>", unsafe_allow_html=True)
            st.markdown("")

            for ap_file in ap_new_files:
                with st.expander(f"**{ap_file.name}**", expanded=True):
                    _ap_sheet = 0
                    if not ap_file.name.lower().endswith('.csv'):
                        _ap_file_sheets = get_excel_sheets(ap_file)
                        if _ap_file_sheets:
                            _ap_sheet = st.selectbox(
                                "Sheet to use",
                                _ap_file_sheets,
                                key=f"ap_sheet_{ap_file.name}",
                            )
                            st.markdown("")
                    ap_sheets[ap_file.name] = _ap_sheet

                    try:
                        _ap_df_preview = read_file(ap_file, sheet_name=_ap_sheet)
                        ap_file.seek(0)
                        ap_new_cols   = _ap_df_preview.columns.tolist()
                        _ap_row_count = len(_ap_df_preview)
                    except Exception:
                        st.warning(f"Could not read columns from {ap_file.name}.")
                        continue

                    MAP_OPTIONS = [APPEND_SKIP] + ap_new_cols

                    # ── Mapping → Main list 1 ──────────────────────────────────
                    file_mapping_1 = {}
                    st.markdown(f"<small style='color:#3a4a5e;font-family:JetBrains Mono,monospace;text-transform:uppercase;letter-spacing:0.08em'>&#9654;&nbsp; Mapping to {ap_main_file_1.name}</small>", unsafe_allow_html=True)
                    hdr_l, hdr_r = st.columns([1, 2])
                    with hdr_l:
                        st.markdown("<small style='color:#2a3a4e;font-family:JetBrains Mono,monospace'>Main list 1 column</small>", unsafe_allow_html=True)
                    with hdr_r:
                        st.markdown("<small style='color:#2a3a4e;font-family:JetBrains Mono,monospace'>Column from this file</small>", unsafe_allow_html=True)
                    for mc in ap_main_cols_1:
                        auto_match = next((c for c in ap_new_cols if col_key(c) == col_key(mc)), None)
                        default_idx = ap_new_cols.index(auto_match) + 1 if auto_match else 0
                        map_l, map_r = st.columns([1, 2])
                        with map_l:
                            st.markdown(f"<div style='padding:0.45rem 0;font-family:JetBrains Mono,monospace;font-size:0.8rem;color:#c9d1e0'>{mc}</div>", unsafe_allow_html=True)
                        with map_r:
                            file_mapping_1[mc] = st.selectbox(
                                mc,
                                MAP_OPTIONS,
                                index=default_idx,
                                key=f"ap_map_1_{ap_file.name}_{mc}",
                                label_visibility="collapsed",
                            )
                    ap_mappings_1[ap_file.name] = file_mapping_1

                    # ── Mapping → Main list 2 (if uploaded) ───────────────────
                    if ap_main_cols_2:
                        st.markdown("")
                        file_mapping_2 = {}
                        st.markdown(f"<small style='color:#3a4a5e;font-family:JetBrains Mono,monospace;text-transform:uppercase;letter-spacing:0.08em'>&#9654;&nbsp; Mapping to {ap_main_file_2.name}</small>", unsafe_allow_html=True)
                        hdr_l2, hdr_r2 = st.columns([1, 2])
                        with hdr_l2:
                            st.markdown("<small style='color:#2a3a4e;font-family:JetBrains Mono,monospace'>Main list 2 column</small>", unsafe_allow_html=True)
                        with hdr_r2:
                            st.markdown("<small style='color:#2a3a4e;font-family:JetBrains Mono,monospace'>Column from this file</small>", unsafe_allow_html=True)
                        for mc2 in ap_main_cols_2:
                            auto_match2 = next((c for c in ap_new_cols if col_key(c) == col_key(mc2)), None)
                            default_idx2 = ap_new_cols.index(auto_match2) + 1 if auto_match2 else 0
                            map_l2, map_r2 = st.columns([1, 2])
                            with map_l2:
                                st.markdown(f"<div style='padding:0.45rem 0;font-family:JetBrains Mono,monospace;font-size:0.8rem;color:#c9d1e0'>{mc2}</div>", unsafe_allow_html=True)
                            with map_r2:
                                file_mapping_2[mc2] = st.selectbox(
                                    mc2,
                                    MAP_OPTIONS,
                                    index=default_idx2,
                                    key=f"ap_map_2_{ap_file.name}_{mc2}",
                                    label_visibility="collapsed",
                                )
                        ap_mappings_2[ap_file.name] = file_mapping_2

                    st.markdown("<div style='margin-top:0.8rem;margin-bottom:0.2rem'><small style='color:#3a4a5e;font-family:JetBrains Mono,monospace;text-transform:uppercase;letter-spacing:0.1em'>&#9632;&nbsp; Row range</small></div>", unsafe_allow_html=True)
                    _range_l, _range_r = st.columns(2, gap="small")
                    with _range_l:
                        _from = st.number_input("From row", min_value=1, max_value=_ap_row_count, value=1, step=1,
                                                key=f"ap_from_{ap_file.name}",
                                                help="First row to include (1 = first data row)")
                    with _range_r:
                        _to = st.number_input("To row", min_value=1, max_value=_ap_row_count, value=_ap_row_count, step=1,
                                              key=f"ap_to_{ap_file.name}",
                                              help="Last row to include")
                    ap_ranges[ap_file.name] = (int(_from), int(_to))

            st.markdown("")
            st.markdown('<div class="section-header">&#9632;&nbsp; 04 &mdash; Email duplicate check</div>', unsafe_allow_html=True)
            EMAIL_SKIP = "— No email check —"
            _email_cols = st.columns(2 if ap_main_cols_2 else 1, gap="small")

            with _email_cols[0]:
                if ap_main_cols_2:
                    st.markdown("<small style='color:#3a4a5e'>Main list 1</small>", unsafe_allow_html=True)
                email_auto_1 = next((c for c in ap_main_cols_1 if 'email' in col_key(c) or col_key(c) == 'mail'), None)
                email_options_1 = [EMAIL_SKIP] + ap_main_cols_1
                email_default_1 = email_options_1.index(email_auto_1) if email_auto_1 else 0
                ap_email_col_choice_1 = st.selectbox(
                    "Email col — Main list 1",
                    email_options_1,
                    index=email_default_1,
                    key="ap_email_col_1",
                    label_visibility="collapsed",
                )
                ap_email_col_1 = None if ap_email_col_choice_1 == EMAIL_SKIP else ap_email_col_choice_1

            if ap_main_cols_2:
                with _email_cols[1]:
                    st.markdown("<small style='color:#3a4a5e'>Main list 2</small>", unsafe_allow_html=True)
                    email_auto_2 = next((c for c in ap_main_cols_2 if 'email' in col_key(c) or col_key(c) == 'mail'), None)
                    email_options_2 = [EMAIL_SKIP] + ap_main_cols_2
                    email_default_2 = email_options_2.index(email_auto_2) if email_auto_2 else 0
                    ap_email_col_choice_2 = st.selectbox(
                        "Email col — Main list 2",
                        email_options_2,
                        index=email_default_2,
                        key="ap_email_col_2",
                        label_visibility="collapsed",
                    )
                    ap_email_col_2 = None if ap_email_col_choice_2 == EMAIL_SKIP else ap_email_col_choice_2

            st.markdown("")

    ap_run = st.button("&#9889;  Append Lists", type="primary", use_container_width=True)

    if ap_run:
        if not ap_main_file_1 or not ap_new_files:
            st.error("Please upload at least Main list 1 and one file to append.")
        elif not ap_mappings_1:
            st.error("Column mapping could not be determined. Check your files.")
        else:
            try:
                _runs = [(ap_main_file_1.name, ap_main_file_1, ap_main_sheet_1, ap_mappings_1, ap_email_col_1)]
                if ap_main_file_2 and ap_mappings_2:
                    _runs.append((ap_main_file_2.name, ap_main_file_2, ap_main_sheet_2, ap_mappings_2, ap_email_col_2))

                _payloads = []
                for _name, _mf, _ms, _maps, _ecol in _runs:
                    with st.spinner(f"Merging into {_name}…"):
                        _payloads.append(
                            compute_append_payload(_name, _mf, _ms, _maps, _ecol, ap_new_files, ap_sheets, ap_ranges)
                        )
                st.session_state[APPEND_RESULTS_KEY] = _payloads
                st.session_state[APPEND_RESCUED_KEY] = {}

            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.exception(e)

    _append_payloads = st.session_state.get(APPEND_RESULTS_KEY)

    if _append_payloads:
        _results = []
        for _payload in _append_payloads:
            _df_res = render_append_payload(_payload)
            _results.append((_payload["main_name"], _df_res))
            st.markdown("")

        # ── Serialise download data into session state ─────────────────
        if len(_results) == 1:
            _sn, _df = _results[0]
            st.session_state["ap_dl"] = {
                "data":  _df.to_csv(index=False).encode("utf-8-sig"),
                "name":  _output_filename(_sn, ".csv"),
                "mime":  "text/csv",
                "label": "&#11015;  Download CSV",
            }
        else:
            _zip_buf = io.BytesIO()
            with zipfile.ZipFile(_zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as _zf:
                for _sn, _df in _results:
                    _zf.writestr(
                        _output_filename(_sn, ".csv"),
                        _df.to_csv(index=False).encode("utf-8-sig"),
                    )
            st.session_state["ap_dl"] = {
                "data":  _zip_buf.getvalue(),
                "name":  "appended_lists.zip",
                "mime":  "application/zip",
                "label": "&#11015;  Download all (ZIP)",
            }

    if st.session_state.get("ap_dl"):
        _dl = st.session_state["ap_dl"]
        st.download_button(
            label=_dl["label"],
            data=_dl["data"],
            file_name=_dl["name"],
            mime=_dl["mime"],
            use_container_width=True,
            key="appender_dl",
        )
        st.markdown("")

    elif not (ap_main_file_1 and ap_new_files):
        st.markdown("""
        <div style='background:linear-gradient(135deg,#0d1117,#0c1520);border:1px dashed #1e2d3d;border-radius:10px;padding:2.5rem;text-align:center;margin-top:1rem'>
          <div style='font-family:JetBrains Mono,monospace;font-size:2rem;color:#1a2d3e;margin-bottom:0.8rem'>&#9632;</div>
          <div style='color:#3a4a5e;font-size:0.9rem'>Upload your main list and one or more files to append, then hit <strong style="color:#00ff8866">Append Lists</strong>.</div>
          <div style='color:#1e2d3d;font-size:0.78rem;margin-top:0.5rem'>Supports .xlsx, .xls, and .csv</div>
        </div>
        """, unsafe_allow_html=True)

# ── Tab 3: List Diff ─────────────────────────────────────────────────────────────
with tab3:

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

    st.markdown('<div class="section-header">&#9632;&nbsp; 05 &mdash; Match sensitivity</div>', unsafe_allow_html=True)

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

                    source_col_name = "Source"
                    existing_cols_ld = set(df_main_valid.columns) | set(df_sec_merged.columns)
                    while source_col_name in existing_cols_ld:
                        source_col_name = f"List Diff {source_col_name}"

                    df_main_result = df_main_valid.iloc[keep_main_idx].copy()
                    df_main_result.insert(0, source_col_name, "Main")

                    df_sec_result = df_sec_merged.iloc[keep_sec_idx].drop(columns=["__ld_compare__"]).copy()
                    df_sec_result.insert(0, source_col_name, "Secondary")

                    df_diff_result = pd.concat([df_main_result, df_sec_result], ignore_index=True, sort=False)

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
