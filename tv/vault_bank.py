# -*- coding: utf-8 -*-
"""The STASH-SIDE BANK — one reader, so four organs cannot drift apart.

HIS ORDER, 2026-09-15: *"all information that can be extracted should be backend tallied
regardless of the ledger.. like there should be a backend ledger already architured im pretty
sure mayb enot in the way im explaining it... but like the backend that approves and routes it
eventuall to the front end"* — and then: *"fix it first architure it properly"*, *"fix the gaps
for everything else and connect it to the heart of the console all 4 organs"*.

★ HE WAS RIGHT THAT IT EXISTS. There are TWO banks, and only one of them is healthy:

    tv/chron_evidence.json   2.2 MB   324 uniques, up to 53 sightings each, conf .90-.95,
                                      126 sets, 46 setGroups, 262 REFUSED kept on purpose,
                                      2714 pages read.   <- the CHRONICLE lane. Exactly the
                                      accumulate-everything-and-route-later shape he described.
    tv/vault_accum.json     27 KB    12 keys.            <- the STASH lane. The same idea,
    tv/vault_seen.json      20 KB    40 rows.                starved.

  MEASURED 2026-09-15 across tv/vault_swept.json: 45 sessions swept, 36 of them (80%) yielded
  NOTHING, 39 rows banked in total. So the stash bank is thin because the sweep rarely takes
  anything - NOT because the file is overwritten per run (its _prov shows control_app maintaining
  it, and vault_swept accumulates per session id).

★ THE GAPS THIS MODULE MAKES VISIBLE (it reports; it never writes):
  1. FIVE sweeps recorded `extractedWhy: None`. A sweep with no reason cannot be told apart from
     a sweep that examined and honestly found nothing. That is UNKNOWN wearing the clothes of a
     clean zero, and it is the difference between "the lane works and the stash was empty" and
     "the lane broke and nobody noticed". [[zero-needs-a-denominator]] [[unknown-stays-unknown]]
  2. TWO WORDINGS FOR ONE OUTCOME - 21x "examined and there was nothing to take - recorded as a
     fact" and 15x "nothing was taken". Counting them as different states would overstate the
     number of distinct failures; counting them as one without saying so would hide a real
     vocabulary drift. This module folds them and REPORTS that it folded them.
  3. NOTHING WATCHED ANY OF IT. check_vault_receipts and check_vault_removals watch the front-end
     vault; no organ watched the bank that is supposed to feed it. [[the-unjoined-end]]

⚠ ONE READER, FOUR SURFACES. The doctor, the heart, the watchdog and the eagle all call state()
  rather than each re-deriving these numbers. Four copies of this arithmetic would disagree the
  first time a field is renamed, and the console would then hold four answers to one question.
  [[copy-drift]]

⚠ IT NEVER WRITES. Banking is gated on witnesses deliberately (console_doctor.py:721) and footage
  has no un-delete. This makes the stall legible; the existing witnessed machinery stays the only
  thing that writes.
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

#: the two phrasings the sweeper has used for the same outcome. Folded, and the fold is REPORTED
#: by state()["whyFolded"] so a reader can see that two labels were treated as one.
_EMPTY_WHYS = (
    "examined and there was nothing to take",
    "nothing was taken",
)


def _load(name):
    """-> (obj, why). UNREADABLE IS NOT EMPTY: a missing or broken bank must never read as a
    clean zero, because every count below would then look healthy at its floor."""
    p = os.path.join(HERE, name)
    if not os.path.isfile(p):
        return None, "%s does not exist" % name
    try:
        with io.open(p, encoding="utf-8") as fh:
            return json.load(fh), None
    except Exception as exc:
        return None, "%s would not parse (%s)" % (name, type(exc).__name__)


def _is_empty_why(why):
    if why is None:
        return False
    w = str(why).strip().lower()
    return any(w.startswith(e) for e in _EMPTY_WHYS)


def state():
    """The whole stash-side bank in one dict. -> dict

    Every count carries the thing it is a count OF, so no caller has to guess a denominator.
    """
    out = {"ok": True, "why": None}

    swept, w1 = _load("vault_swept.json")
    accum, w2 = _load("vault_accum.json")
    seen, w3 = _load("vault_seen.json")
    chron, w4 = _load("chron_evidence.json")
    unreadable = [w for w in (w1, w2, w3, w4) if w]
    if unreadable:
        out["ok"] = False
        out["why"] = "; ".join(unreadable)

    # ── the sweep, session by session ──
    sessions = swept if isinstance(swept, dict) else {}
    yielded, silent, no_reason, rows = [], [], [], 0
    for sid, v in sessions.items():
        if not isinstance(v, dict):
            no_reason.append(sid)
            continue
        n = v.get("rows") or 0
        rows += n if isinstance(n, int) else 0
        took = bool(v.get("extracted")) or bool(n)
        why = v.get("extractedWhy")
        if took:
            yielded.append(sid)
        elif _is_empty_why(why):
            silent.append(sid)          # examined, honestly nothing there
        else:
            no_reason.append(sid)       # ⚠ UNKNOWN — no reason recorded at all
    out["sweptN"] = len(sessions)
    out["yieldedN"] = len(yielded)
    out["silentN"] = len(silent)
    out["noReasonN"] = len(no_reason)
    out["noReason"] = sorted(no_reason)[:12]
    out["rowsBanked"] = rows
    out["whyFolded"] = list(_EMPTY_WHYS)

    # ── the accumulator ──
    bk = (accum or {}).get("byKey")
    out["accumKeys"] = len(bk) if isinstance(bk, dict) else None
    for f in ("owned", "added", "raised", "held"):
        v = (accum or {}).get(f)
        out["accum_" + f] = len(v) if isinstance(v, (list, dict)) else None

    # ── what reached vault_seen ──
    rws = (seen or {}).get("rows")
    rws = rws if isinstance(rws, list) else []
    out["seenRows"] = len(rws) if seen is not None else None
    out["seenWithFrame"] = sum(
        1 for r in rws
        if isinstance(r, dict) and any((w or {}).get("frame") for w in (r.get("witnesses") or []))
    ) if seen is not None else None
    out["seenZeroConf"] = sum(
        1 for r in rws if isinstance(r, dict) and not (r.get("conf") or 0)
    ) if seen is not None else None

    # ── the healthy sibling, for scale ──
    cu = (chron or {}).get("uniques")
    out["chronUniques"] = len(cu) if isinstance(cu, dict) else None
    cr = (chron or {}).get("refused")
    out["chronRefused"] = len(cr) if isinstance(cr, (list, dict)) else None
    # ⚠ TWO SHAPES IN ONE STORE. A name maps either to a LIST of sightings or to a dict with a
    # "sightings" key, depending on when it was written. Assuming one shape raises AttributeError
    # inside a caller's except and the whole bank then reads as unreadable. Measured, not guessed.
    def _sightings(v):
        if isinstance(v, list):
            return v
        if isinstance(v, dict):
            return v.get("sightings") or []
        return []
    out["chronSightings"] = sum(len(_sightings(v)) for v in cu.values()) \
        if isinstance(cu, dict) else None

    return out


def headline():
    """One sentence a surface can print, with the figures inline. -> (state_word, line)"""
    s = state()
    if not s["ok"]:
        return "UNKNOWN", ("the stash bank could not be read (%s), so its yield is UNKNOWN "
                           "rather than zero" % s["why"])
    n = s["sweptN"]
    if not n:
        return "UNKNOWN", ("no sweep has ever been recorded, so whether the stash lane banks "
                           "anything is UNKNOWN - there is no denominator yet")
    line = ("stash bank: %d of %d sweep(s) took something (%d rows, %d key(s) accumulated, "
            "%d row(s) in vault_seen)" % (s["yieldedN"], n, s["rowsBanked"],
                                          s["accumKeys"], s["seenRows"]))
    if s["noReasonN"]:
        return "WARN", (line + "; and %d sweep(s) recorded NO reason at all, so those are "
                        "UNKNOWN rather than honestly empty" % s["noReasonN"])
    if s["yieldedN"] == 0:
        return "WARN", (line + "; every sweep came back empty, which is a stalled lane unless "
                        "his stash really is untouched")
    return "OK", line
