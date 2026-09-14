# List Toolbox

A Streamlit app for screening new company lists against a main list and merging them.

```bash
pip install -r requirements.txt
streamlit run list_toolbox.py
```

## Features

**Screen & Append** — upload the main list and one or more new lists, and get the
combined file back in one pass:

- Fuzzy company-name matching (RapidFuzz) with an adjustable threshold, ignoring
  legal suffixes, word order and abbreviations — `Acme Corp` matches `ACME Corporation Ltd`
- Flags rows that already exist in the main list *and* duplicates within the new lists
- Extra duplicate checks on identity columns you pick: email domains ignore anything
  before the `@`, websites and LinkedIn URLs ignore `http(s)`, `www` and trailing paths
- Review every flagged row and **Keep** any of them — the download updates instantly,
  without re-running the match
- Maps each file onto the main list's columns separately, so the new lists don't need
  matching headers

**List Diff** — merge several secondary lists, dedup them, then compare against the
main list. Entries found on both sides are dropped from *both*, leaving only what is
unique to one. Downloads as CSV or Excel.

**Throughout** — `.xlsx` / `.xls` / `.csv` with sheet selection, automatic CSV
delimiter and encoding detection, country-name normalisation (`Deutschland`, `DE`,
`Germany` → one value), and a light/dark theme.

## Layout

```
list_toolbox.py          entry point
exclusion_lists/
  app.py                 page config, theme, tabs
  theme.py + assets/     CSS
  core/                  pure logic, no Streamlit — importable and testable
    text.py              name normalisation
    countries.py         country-name map
    columns.py           header detection, identity keys
    files.py             CSV/Excel reading, delimiter sniffing
    matching.py          the fuzzy matchers
    combine.py           merge + duplicate findings
  ui/                    Streamlit layer
    state.py             session state
    widgets.py           shared markup
    screen_append.py     tab 1
    list_diff.py         tab 2
```
