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
    hints = ['company', 'name', 'organisation', 'organization', 'firm', 'account']
    for col in columns:
        if any(h in col.lower() for h in hints):
            return col
    return columns[0]

def read_file(f, nrows=None, sheet_name=0):
    raw = f.read()
    if f.name.lower().endswith('.csv'):
        sample = raw[:4096].decode('utf-8', errors='replace')
        try:
            sep = csv.Sniffer().sniff(sample, delimiters=',;').delimiter
        except csv.Error:
            sep = ','
        for encoding in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
            try:
                return normalize_country_cols(pd.read_csv(io.BytesIO(raw), sep=sep, nrows=nrows, encoding=encoding))
            except (UnicodeDecodeError, LookupError):
                pass
        return normalize_country_cols(pd.read_csv(io.BytesIO(raw), sep=sep, nrows=nrows, encoding='latin-1', encoding_errors='replace'))
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


def append_lists(df_main, df_new, mapping):
    # mapping: {main_col: source_col_in_df_new | APPEND_SKIP}
    new_rows = {}
    for main_col, source in mapping.items():
        if source == APPEND_SKIP:
            new_rows[main_col] = [None] * len(df_new)
        else:
            new_rows[main_col] = df_new[source].values
    return pd.concat([df_main, pd.DataFrame(new_rows)], ignore_index=True)


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

tab1, tab2 = st.tabs(["  List Screener  ", "  List Appender  "])

# ── Tab 1: List Screener ───────────────────────────────────────────────────────
with tab1:

    st.markdown("""
<div class="tab-desc">
  <strong>List Screener</strong> — upload your main database and a new list, then
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
                def _do_append(main_file, main_sheet, mappings, email_col):
                    main_file.seek(0)
                    df_result = read_file(main_file, sheet_name=main_sheet)
                    original_rows  = len(df_result)
                    total_appended = 0
                    total_skipped  = 0
                    for ap_file in ap_new_files:
                        if ap_file.name not in mappings:
                            continue
                        with st.spinner(f"Merging {ap_file.name} → {main_file.name}…"):
                            ap_file.seek(0)
                            df_ap_new    = read_file(ap_file, sheet_name=ap_sheets.get(ap_file.name, 0))
                            file_mapping = mappings[ap_file.name]

                            _from_r, _to_r = ap_ranges.get(ap_file.name, (1, len(df_ap_new)))
                            df_ap_new = df_ap_new.iloc[_from_r - 1:_to_r].reset_index(drop=True)

                            if email_col and email_col in df_result.columns:
                                email_source = file_mapping.get(email_col, APPEND_SKIP)
                                if email_source != APPEND_SKIP and email_source in df_ap_new.columns:
                                    existing_emails = set(
                                        df_result[email_col].dropna().astype(str).str.lower().str.strip()
                                    )
                                    mask = ~df_ap_new[email_source].astype(str).str.lower().str.strip().isin(existing_emails)
                                    total_skipped += (~mask).sum()
                                    df_ap_new = df_ap_new[mask].reset_index(drop=True)
                                    before_internal = len(df_ap_new)
                                    df_ap_new = df_ap_new.drop_duplicates(subset=[email_source], keep='first').reset_index(drop=True)
                                    total_skipped += before_internal - len(df_ap_new)

                            rows_before = len(df_result)
                            df_result = append_lists(df_result, df_ap_new, file_mapping)
                            for _col in df_result.columns:
                                if _is_website_col(_col):
                                    df_result.loc[rows_before:, _col] = (
                                        df_result.loc[rows_before:, _col].apply(_norm_website)
                                    )
                                elif _is_emaildomain_col(_col):
                                    df_result.loc[rows_before:, _col] = (
                                        df_result.loc[rows_before:, _col].apply(_norm_emaildomain)
                                    )
                            total_appended += len(df_result) - rows_before
                    return df_result, original_rows, total_appended, total_skipped

                _runs = [(ap_main_file_1, ap_main_sheet_1, ap_mappings_1, ap_email_col_1)]
                if ap_main_file_2 and ap_mappings_2:
                    _runs.append((ap_main_file_2, ap_main_sheet_2, ap_mappings_2, ap_email_col_2))

                _results = []
                for _mf, _ms, _maps, _ecol in _runs:
                    with st.spinner(f"Reading {_mf.name}…"):
                        _df_res, _orig_rows, _appended, _skipped = _do_append(_mf, _ms, _maps, _ecol)
                    _results.append((_mf.name, _df_res, _orig_rows, _appended, _skipped))

                for _src_name, _df_res, _orig_rows, _appended, _skipped in _results:
                    st.markdown(f'<div class="section-header">&#9632;&nbsp; Result — {_src_name}</div>', unsafe_allow_html=True)
                    _stat_cols = st.columns(4 if _skipped else 3, gap="small")
                    _stat_cols[0].markdown(f'<div class="stat-box"><div class="stat-num">{_orig_rows:,}</div><div class="stat-label">Main rows</div></div>', unsafe_allow_html=True)
                    _stat_cols[1].markdown(f'<div class="stat-box"><div class="stat-num">{_appended:,}</div><div class="stat-label">Appended rows</div></div>', unsafe_allow_html=True)
                    if _skipped:
                        _stat_cols[2].markdown(f'<div class="stat-box"><div class="stat-num warn">{_skipped:,}</div><div class="stat-label">Skipped (email)</div></div>', unsafe_allow_html=True)
                    _stat_cols[-1].markdown(f'<div class="stat-box"><div class="stat-num">{len(_df_res):,}</div><div class="stat-label">Total rows</div></div>', unsafe_allow_html=True)

                    st.markdown("")
                    _df_new_rows = _df_res.iloc[_orig_rows:].reset_index(drop=True)
                    st.dataframe(_df_new_rows.head(200), use_container_width=True, hide_index=True)
                    if len(_df_new_rows) > 200:
                        st.markdown(f"<small style='color:#3a4a5e'>Showing first 200 of {len(_df_new_rows):,} new rows.</small>", unsafe_allow_html=True)
                    st.markdown("")

                # ── Serialise download data into session state ─────────────────
                if len(_results) == 1:
                    _sn, _df = _results[0][0], _results[0][1]
                    st.session_state["ap_dl"] = {
                        "data":  _df.to_csv(index=False).encode("utf-8-sig"),
                        "name":  _output_filename(_sn, ".csv"),
                        "mime":  "text/csv",
                        "label": "&#11015;  Download CSV",
                    }
                else:
                    _zip_buf = io.BytesIO()
                    with zipfile.ZipFile(_zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as _zf:
                        for _sn, _df, _, _, _ in _results:
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

            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.exception(e)

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

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("<br><hr style='border-color:#0d1520;margin-top:2rem'>", unsafe_allow_html=True)
st.markdown("<small style='color:#1e2d3d;font-family:JetBrains Mono,monospace;font-size:0.68rem'>RapidFuzz token_sort_ratio &mdash; handles reordering, abbreviations &amp; legal suffix differences. Promoted matches appear in downloads immediately.</small>", unsafe_allow_html=True)
