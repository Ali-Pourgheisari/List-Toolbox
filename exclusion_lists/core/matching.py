"""Fuzzy company-name comparison.

Three shapes of the same question, all scored with RapidFuzz token_sort_ratio
over `normalize`d names: does this name exist in that list, does this list repeat
itself, and which entries do two lists share.
"""

from rapidfuzz import fuzz, process

from .text import normalize


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
