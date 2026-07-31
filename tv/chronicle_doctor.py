#!/usr/bin/env python3
"""v1533 — 📜 CHRONICLE DOCTOR: is the whole arc actually wired, on THIS machine?

    python3 tv/chronicle_doctor.py

The arc spans four files, two lanes, a subscription CLI, a background job and the board. Every piece
has tests; none of that tells him whether it works on the machine in front of him RIGHT NOW — whether
Grok is logged in, whether there is any footage to sweep, whether the board build is new enough to
apply. Those are the things that differ between his Mac, his Windows PC and his cousin's box, and
they are exactly the things a test suite cannot know.

DOCTRINE: it reports, it never fixes, and it never guesses. Each check answers one of three ways —
OK, MISSING (with what to do), or UNKNOWN (with why it could not be determined). An UNKNOWN is not a
failure and must never be dressed as one; "I could not check" and "it is broken" are different
sentences, and collapsing them is how a health check starts lying.
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

OK, MISSING, UNKNOWN = "ok", "missing", "unknown"


def _check(name, fn):
    try:
        state, detail = fn()
    except Exception as e:                       # a check that crashes is UNKNOWN, never "broken"
        return {"name": name, "state": UNKNOWN, "detail": "the check itself failed: %s" % str(e)[:120]}
    return {"name": name, "state": state, "detail": detail}


def _reader_prompts():
    import tv_diablo as tv
    if "chronicle" not in tv.READ_PROMPT:
        return MISSING, "the classifier has no `chronicle` scene — reinstall tv_diablo.py (v1509+)"
    if "chronicleTab" not in tv.READ_PROMPT:
        return MISSING, "the reader cannot name WHICH ledger — needs v1509+"
    return OK, "the reader knows the Chronicle and both its ledgers (%s)" % tv.PROMPT_VER


def _claude_lane():
    import tv_diablo as tv
    if not hasattr(tv, "claude_chronicle_read"):
        return MISSING, "the primary lane is absent — needs v1519+"
    return OK, "primary lane present (Claude, on your subscription)"


def _grok_lane():
    try:
        import g5_grok_eyes as g5
    except Exception:
        return MISSING, "g5_grok_eyes.py not importable — the second eye is unavailable"
    if not hasattr(g5, "g5_chronicle_read"):
        return MISSING, "the Grok lane cannot read a Chronicle page — needs v1514+"
    try:
        if not g5.has_subscription():
            # NOT a failure: one lane is a working system, it just scores lower at the gate
            return MISSING, ("grok is installed but not signed in — cross-lane agreement, the "
                             "STRONGEST witness the gate has, is unavailable until it is")
    except Exception as e:
        return UNKNOWN, "could not ask grok whether it is signed in: %s" % str(e)[:80]
    return OK, "second eye ready — cross-lane agreement is available"


def _footage():
    import chronicle_retro as cr
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
    if not os.path.isdir(hist):
        return MISSING, "no hist directory at %s — play a session and it seals one" % hist
    reels = cr.reel_dirs(hist)
    if not reels:
        return MISSING, "no sealed reels yet — the retro sweep has nothing to read"
    frames = 0
    for r in reels:
        try:
            with io.open(os.path.join(r, "index.json"), encoding="utf-8") as fh:
                frames += len(json.load(fh).get("frames") or [])
        except Exception:
            pass
    return OK, "%d sealed reel(s) · %d frames of footage to sweep" % (len(reels), frames)


def _grouping():
    try:
        from PIL import Image  # noqa: F401
    except Exception:
        return MISSING, ("Pillow is absent — frames cannot be fingerprinted, so every frame would "
                         "be read as its own page. `pip3 install Pillow`")
    return OK, "Pillow present — a held panel costs ONE read, not forty"


def _memory():
    import control_app as ca
    swept = ca._chron_swept_load()
    if not swept:
        return OK, "nothing swept yet — the first sweep will read everything"
    return OK, "%d reel(s) already swept and will not be paid for twice" % len(swept)


def _visits():
    import control_app as ca
    v = (ca.chronicle_visits(limit=40) or {}).get("visits") or []
    if not v:
        return MISSING, ("no in-game Chronicle visits recorded — open the Chronicle while the "
                         "console is watching and it will capture one for free")
    unread = [x for x in v if not x.get("ledger")]
    d = "%d visit(s) captured" % len(v)
    if unread:
        d += " · %d with an UNREAD ledger (those cannot be swept safely — re-open them in game)" % len(unread)
    return OK, d


def _board_apply():
    """The board is the only thing that can write his ledger, and it is a separate file that can be
    older than the console — the exact case this check exists for."""
    p = os.path.join(os.path.dirname(HERE), "bible.html")
    if not os.path.isfile(p):
        return UNKNOWN, "bible.html not found beside the console — cannot check the board build"
    try:
        with io.open(p, encoding="utf-8") as fh:
            src = fh.read()
    except Exception as e:
        return UNKNOWN, "could not read bible.html: %s" % str(e)[:80]
    if "chronicleApply" not in src:
        return MISSING, "this board build cannot APPLY a sweep — it needs v1521+"
    if "completeSets" not in src:
        return MISSING, "the board cannot expand a COMPLETE set into its pieces — needs v1530+"
    return OK, "the board can apply a sweep, and undo it"


def _gate():
    import chronicle_retro as cr
    return OK, ("grounding needs %d independent witnesses, confidence floor %.2f "
                "(tune for free: /api/chronicle_gate?floor=&witnesses=)"
                % (cr.MIN_WITNESSES, cr.CONF_FLOOR))


CHECKS = [
    ("reader prompts", _reader_prompts),
    ("claude lane", _claude_lane),
    ("grok lane", _grok_lane),
    ("footage", _footage),
    ("frame grouping", _grouping),
    ("sweep memory", _memory),
    ("in-game visits", _visits),
    ("board apply", _board_apply),
    ("the gate", _gate),
]


def diagnose():
    rows = [_check(n, f) for n, f in CHECKS]
    # READY means the arc can do its job end to end. The Grok lane deliberately does NOT block it:
    # one eye is a working system, it just scores lower at the gate — and calling that "broken"
    # would push him to fix something that is not wrong.
    blocking = {"reader prompts", "claude lane", "frame grouping", "board apply"}
    bad = [r for r in rows if r["state"] == MISSING and r["name"] in blocking]
    return {"ready": not bad, "checks": rows,
            "blocking": [r["name"] for r in bad],
            "unknown": [r["name"] for r in rows if r["state"] == UNKNOWN]}


if __name__ == "__main__":
    import console_safe  # noqa: F401  — the glyphs below must survive a non-UTF-8 console

    d = diagnose()
    icon = {OK: "🟢", MISSING: "🟠", UNKNOWN: "⚪"}
    print("\n📜 CHRONICLE DOCTOR — this machine\n")
    for r in d["checks"]:
        print("  %s %-16s %s" % (icon.get(r["state"], "?"), r["name"], r["detail"]))
    print()
    if d["ready"]:
        print("✅ READY — the arc can sweep, gate and register end to end.")
    else:
        print("⛔ NOT READY — %s" % ", ".join(d["blocking"]))
    if d["unknown"]:
        # said separately, on purpose: an unknown is not a failure
        print("⚪ could not check: %s" % ", ".join(d["unknown"]))
    raise SystemExit(0 if d["ready"] else 1)
