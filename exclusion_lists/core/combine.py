"""Mapping the surviving new rows onto the main list, and the duplicate findings.

A "finding" is one row that collided with something, whichever check caught it.
Name collisions come from the cached screening result (`name_findings`), identity
key collisions from the merge itself (`build_combined`); both produce the same
shape so the UI can review them as one list.
"""

import pandas as pd

from .columns import (
    is_emaildomain_col,
    is_website_col,
    key_kind,
    match_key,
    norm_emaildomain,
    norm_website,
)

APPEND_SKIP = "— Skip / leave empty —"

SRC_FILE_COL = "_src_file"
SRC_ROW_COL  = "_src_row"
# Each list names its company column whatever it likes, so the chosen one is
# copied here as well: screening then has a single column to work across files.
NAME_COL     = "_company"
BOOKKEEPING_COLS = (SRC_FILE_COL, SRC_ROW_COL, NAME_COL)

MAIN_LIST_ORIGIN = None   # a finding whose origin is None collided with the main list


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


def _build_key_index(df_main, main_name_col, key_cols, kinds):
    """key value -> (label, origin) per key column; origin None means the main list."""
    index = {c: {} for c in key_cols}
    labels = df_main[main_name_col] if main_name_col in df_main.columns else None
    for c in key_cols:
        for val, label in zip(df_main[c], labels if labels is not None else df_main[c]):
            k = match_key(c, val, kinds[c])
            if k and k not in index[c]:
                index[c][k] = (str(label).strip() if pd.notna(label) else k, MAIN_LIST_ORIGIN)
    return index


def _map_sources(mappings, sources):
    """Each source file's rows, rewritten into the main list's columns."""
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
            if is_website_col(col):
                chunk[col] = chunk[col].apply(norm_website)
            elif is_emaildomain_col(col):
                chunk[col] = chunk[col].apply(norm_emaildomain)
        chunk["_source_file"] = src_name
        chunk["_source_row"]  = (df_src[SRC_ROW_COL].values if SRC_ROW_COL in df_src.columns
                                 else range(1, len(df_src) + 1))
        mapped_chunks.append(chunk)
    return mapped_chunks


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
    kinds    = {c: key_kind(c) for c in key_cols}
    index    = _build_key_index(df_main, main_name_col, key_cols, kinds)

    mapped_chunks = _map_sources(mappings, sources)
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
