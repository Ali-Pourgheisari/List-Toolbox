"""Session state for the Screen & Append tab.

Screening is the expensive step, so its result is cached under
RESULTS_SESSION_KEY and every rerun reads from there. The user's "keep this one
anyway" decisions live alongside it as a set of row ids, applied on read by
`get_visible_results` — so a Keep click never re-runs the match.
"""

import streamlit as st

RESULTS_SESSION_KEY = "screener_results"

# Every duplicate — matched by name or by an identity key — is overridden the same
# way: one set of row ids the user has forced into the output.
DUP_EXEMPT_KEY = "dup_exempt_row_ids"

# Streamlit gives an expander no state of its own, so remember that the user is
# working inside one and re-open it on the next rerun.
DUPS_OPEN_KEY = "sa_dups_open"

DOWNLOAD_KEY = "sa_dl"


def store_results(payload: dict) -> None:
    """Cache a screening result, keeping exemptions only if the inputs are unchanged."""
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
