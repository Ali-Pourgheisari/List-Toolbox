"""Reading meaning out of column headers.

Two jobs: guessing which column holds the company name, and deciding what kind
of identity a column carries (email domain, website, profile url, plain text) so
its values can be normalised into a comparable key.
"""

import pandas as pd

from .text import col_key

# Headers that contain a company hint but hold something other than its name:
# "companywebsite" and "companyemaildomain" would otherwise win on "company".
NON_NAME_HINTS = ('website', 'webpage', 'url', 'email', 'mail', 'domain', 'country',
                  'phone', 'street', 'city', 'zip', 'postcode', 'linkedin', 'revenue',
                  'employee')

EXACT_NAME_HEADERS = ('company name', 'company', 'organisation', 'organization',
                      'account name', 'name', 'account')

WEBSITE_COL_HINTS     = ('website', 'webpage', 'weburl', 'homepage', 'siteurl')
EMAILDOMAIN_COL_HINTS = ('emaildomain', 'maildomain', 'domainemail')


def detect_company_col(columns) -> str:
    """The column most likely to hold the company name."""
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


def is_website_col(col_name: str) -> bool:
    k = col_key(col_name)
    return any(h in k for h in WEBSITE_COL_HINTS)


def is_emaildomain_col(col_name: str) -> bool:
    k = col_key(col_name)
    return any(h in k for h in EMAILDOMAIN_COL_HINTS)


def norm_website(val) -> str:
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


def norm_emaildomain(val) -> str:
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


def key_kind(col_name: str) -> str:
    """How the values in one main-list column identify a company."""
    k = col_key(col_name)
    if is_emaildomain_col(col_name):
        return "domain"
    if "email" in k or k == "mail":
        return "email"
    if is_website_col(col_name):
        return "website"
    if "linkedin" in k:
        return "url"
    return "text"


def default_key_cols(main_columns) -> list:
    """Columns that identify a company on their own, so they make good keys."""
    return [c for c in main_columns if key_kind(c) in ("domain", "email", "website", "url")]


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
    kind = kind or key_kind(col_name)
    if kind == "domain":
        text = str(norm_emaildomain(text) or text)
    elif kind in ("website", "url"):
        text = text.split("://", 1)[-1]
        if text.lower().startswith("www."):
            text = text[4:]
        text = text.split("?")[0].split("#")[0].rstrip("/")
    return text.strip().lower()
