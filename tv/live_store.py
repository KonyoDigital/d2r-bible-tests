# -*- coding: utf-8 -*-
"""A gate that reads one of HIS live stores must say so, and be counted when it cannot.

⚠⚠ WHY THIS EXISTS. Eleven gates were RED on origin and GREEN on his Mac, and neither verdict was
about the shipped code. They read stores that live only on his machine:

    tv/chron_evidence.json    2,210,553 bytes locally · NOT tracked -> absent in CI
    tv/vault_accum.json          96,485 bytes locally · NOT tracked -> absent in CI
    ~/d2r_ledger_backups/            73 files        · outside the repo entirely

In CI those reads return None or 0, and the gate fails with `AssertionError: None != 100.0`,
`the vault bank holds no named rows`, `no ledger backup exists yet` — sentences that read as
product defects and are statements about a runner having no data.

⚠ AND THEY CANNOT SIMPLY BE COMMITTED. `chron_evidence.json` is 2.2 MB of HIS ledger evidence and
this repo is PUBLIC. The data is his; the gate is ours.

⚠⚠ A SKIP IS NOT A PASS — which is the whole reason this is a marked, COUNTED skip and not a bare
`return`. `tv/test_a_live_store_skip_is_counted.py` globs for `LIVE_STORE_MARK` and reports how
many gates stand down for want of his data, so the number is on a screen instead of dissolving
into a green run. It is the same shape as `node unavailable — a skip is NOT a pass`, which this
repo already uses for the node venue. [[regression-guard]] [[unknown-stays-unknown]]
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

#: The literal the watchdog globs for. Changing it silently uncounts every skip that uses it.
LIVE_STORE_MARK = "his live store is absent"


def missing(*paths):
    """Which of these do not exist here. -> [path]  (absolute or repo-relative)"""
    out = []
    for p in paths:
        full = p if os.path.isabs(p) else os.path.join(HERE, p)
        if not os.path.exists(os.path.expanduser(full)):
            out.append(p)
    return out


def require(case, *paths, **kw):
    """Stand the gate down — with a REASON and the mark — when his data is not here.

    Never call this to excuse a failure on a machine that HAS the store: the point is to tell
    "nobody could look" apart from "it looked and the answer was wrong", and a skip taken where
    the data exists destroys exactly that distinction.
    """
    gone = missing(*paths)
    if gone:
        case.skipTest("%s — %s — a skip is NOT a pass%s"
                      % (LIVE_STORE_MARK, ", ".join(gone),
                         (": " + kw["why"]) if kw.get("why") else ""))
    return True
