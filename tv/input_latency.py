# -*- coding: utf-8 -*-
"""Click-to-paint as the page measured it.

The beat carries ``{p50, p95, maxLongtask, n}``. A missing beat is None.
None is UNKNOWN, never instant and never zero.

Budgets are the v3769 (38f15023) measurement plus headroom. They are filled
once that run has numbers; until then they stay None and a check that needs
them says the budget has not been entered.
"""

# v3769 (38f15023), both 1440x900 and 1280x720, three clicks per control, a vault
# repaint every 500ms. Peak click-to-paint p95 was 392ms (TV-D, 1280x720).
# The idle long task was 62ms once and otherwise under Chrome's 50ms floor.
# Headroom clears that peak and still refuses the v3771 vault clicks, which
# measured 838-950ms on the same probe, and its 362ms idle long task.
P95_BUDGET_MS = 750
LONGTASK_BUDGET_MS = 250
BASELINE = {
    "rev": "38f15023",
    "version": "v3769",
    "p95_ms": 392,
    "longtask_ms": 62,
    "headroom": "p95 750ms (under twice the v3769 peak); long task 250ms",
}

# v3773 - the guard's budget is a COUNT, because a loaded box moves any clock. Per tab switch and
# per vault repaint: getComputedStyle calls and whole-document walks. v3771 measured 28,480-39,402
# getComputedStyle calls per vault switch or repaint; the fix measures 0.
COUNT_BUDGET = 20

_LAST = {"sample": None}


def _num(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    if v != v:  # NaN
        return None
    return float(v)


def record(sample):
    """Store one beat payload. -> dict | None.

    None means the page did not say. A number that is absent stays None;
    it is not stored as 0.
    """
    if not isinstance(sample, dict):
        _LAST["sample"] = None
        return None
    n = sample.get("n")
    stored = {
        "p50": _num(sample.get("p50")),
        "p95": _num(sample.get("p95")),
        "maxLongtask": _num(sample.get("maxLongtask")),
        "n": (int(n) if isinstance(n, (int, float)) and not isinstance(n, bool) and n >= 0 else None),
    }
    _LAST["sample"] = stored
    return stored


def read():
    """The last beat this process recorded, or None if the page has not said."""
    return _LAST["sample"]
