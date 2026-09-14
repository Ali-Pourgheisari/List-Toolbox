"""Name and header text normalisation.

`normalize` produces the comparison form used by every fuzzy match;
`clean_for_output` produces the display form written into the result file.
They are deliberately different: the first strips legal suffixes so "Acme Ltd"
and "Acme" collide, the second keeps them so the export stays readable.
"""

import re
from datetime import date

SUFFIXES = re.compile(
    r'\b(inc|incorporated|ltd|limited|llc|llp|lp|plc|gmbh|ag|sa|sas|bv|nv|'
    r'corp|corporation|co|company|group|holding|holdings|international|intl|'
    r'ug|kgaa|kg|eg|oy|ab|as|aps|srl|sro|sl|bvba|sprl|'
    r'technologies|technology|tech|solutions|services|systems|'
    r'consulting|ventures|partners|associates|enterprises)\b',
    re.IGNORECASE
)


def output_filename(source_name: str, ext: str) -> str:
    """Name the download after the source file, minus any trailing date, plus today's."""
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
    """The comparison form of a company name: lowercase, unpunctuated, suffix-free."""
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
