"""Country-name normalisation.

Any column whose header hints at country data is mapped through COUNTRY_MAP, so
"Deutschland", "DE" and "Germany" all compare and export as one value.
"""

import pandas as pd

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
