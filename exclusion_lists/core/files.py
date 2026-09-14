"""Turning an uploaded .csv/.xlsx/.xls into a DataFrame.

Most of the work here is CSV: real exports arrive semicolon-separated, in a
handful of encodings, and sometimes wrapped in an extra layer of quoting. Excel
needs only a sheet name.
"""

import csv
import io

import pandas as pd

from .countries import normalize_country_cols

CSV_DELIMITERS = (',', ';', '\t', '|')
CSV_ENCODINGS = ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1')


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


def _decode_csv(raw: bytes) -> str:
    """Decode CSV bytes with the first encoding that accepts them."""
    for encoding in CSV_ENCODINGS:
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            pass
    return raw.decode('latin-1', errors='replace')


def read_file(f, nrows=None, sheet_name=0):
    """Read an uploaded file into a DataFrame, with country columns normalised.

    Pass nrows=0 to read the header only, which is how the UI lists columns
    without paying for the whole file.
    """
    raw = f.read()
    if f.name.lower().endswith('.csv'):
        text = _decode_csv(raw)
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
