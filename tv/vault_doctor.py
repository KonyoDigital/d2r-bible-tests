#!/usr/bin/env python3
"""v2012 — 🗄 VAULT DOCTOR: why is the vault empty, answered from his own film, for free.

    python3 tv/vault_doctor.py

`tv/vault_accum.json` has been 72 bytes of empty since 2026-08-20, and there was no way to find out
WHY without paying for a sweep. Empty has three completely different causes and they need completely
different actions:

    no footage                → record a reel
    footage, no stash panels  → open the stash while the reel is rolling
    panels, no readable names → FILM THE TOOLTIP. D2R prints no names in a grid.

The third is the one that is actually true on his machine, and it is invisible from the ledger: an
empty file looks identical whichever cause produced it. Proven on his reels overnight — the template
gate fires, the paid read runs and correctly returns `items: []`, so nothing accumulates and nothing
seals. The chain works; the film has no names in it.

DOCTRINE, borrowed wholesale from chronicle_doctor: it reports, it never fixes, and it never guesses.
Every check answers OK, MISSING (with what to do) or UNKNOWN (with why it could not be determined).
An UNKNOWN is not a failure and must never be dressed as one — "I could not check" and "it is broken"
are different sentences.

FREE BY CONSTRUCTION: local pixel work only. No model turn, no console, no network. It can be run
while the console is down, which is exactly when someone wants to know what their footage holds.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

OK, MISSING, UNKNOWN = "ok", "missing", "unknown"

SAMPLE_EVERY = 12      # every 12th frame of a reel — enough to find a panel, cheap enough to run
SAMPLE_CAP = 240       # hard ceiling on frames examined, so a big corpus cannot make this crawl


def _hist():
    return os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")


def _check(name, fn):
    try:
        state, detail = fn()
    except Exception as e:                      # a check that crashes is UNKNOWN, never "broken"
        return {"name": name, "state": UNKNOWN, "detail": "the check itself failed: %s" % str(e)[:120]}
    return {"name": name, "state": state, "detail": detail}


def _frames():
    """A bounded, MID-REEL sample. Never the first frames of a reel: those are loading screens, and
    sampling them found ZERO stash panels on footage that had ten — a biased sample that nearly
    produced a false 'your film has no stash in it'."""
    out = []
    for d in sorted(glob.glob(os.path.join(_hist(), "reel_*"))):
        fr = sorted(glob.glob(os.path.join(d, "*.jpg")))
        if len(fr) < 8:
            continue
        out += fr[len(fr) // 6::SAMPLE_EVERY]
    return out[:SAMPLE_CAP]


_CACHE = {}


def _measure():
    """One pass, cached: how many sampled frames are stash panels, and what the pixels say is in them."""
    if _CACHE:
        return _CACHE
    import control_app as ca
    import vault_corpus as vc
    frames = _frames()
    gated, measured, occupied, free_cells, refused = [], 0, 0, 0, 0
    for p in frames:
        try:
            if ca.stash_screen_open(p) is None:
                continue
        except Exception:
            continue
        gated.append(p)
        try:
            lat = vc.inventory_lattice(p)
            if not lat.get("ok"):
                refused += 1
                continue
            occ = vc.inventory_occupancy(p, lat)
            if not occ.get("ok"):
                refused += 1
                continue
            measured += 1
            occupied += int(occ.get("occupied") or 0)
            free_cells += int(occ.get("free") or 0)
        except Exception:
            refused += 1
    _CACHE.update({"sampled": len(frames), "gated": len(gated), "measured": measured,
                   "occupied": occupied, "free": free_cells, "refused": refused,
                   "frames": gated})
    return _CACHE


def _footage():
    reels = glob.glob(os.path.join(_hist(), "reel_*"))
    if not reels:
        return MISSING, "no reels in %s — record one: open TV DIABLO and press ON AIR" % _hist()
    return OK, "%d reel(s) on disk" % len(reels)


def _stash_panels():
    m = _measure()
    if not m["sampled"]:
        return UNKNOWN, "no frames sampled — the reels hold fewer than 8 frames each"
    if not m["gated"]:
        return MISSING, ("%d frame(s) sampled and NONE is a stash panel. The gate wants the stash "
                         "chrome on screen — open your stash while the reel is rolling."
                         % m["sampled"])
    return OK, "%d of %d sampled frame(s) are a stash panel" % (m["gated"], m["sampled"])


def _panels_measure():
    m = _measure()
    if not m["gated"]:
        return UNKNOWN, "no stash panel to measure — see the check above"
    if not m["measured"]:
        return MISSING, ("%d stash panel(s) and the lattice refused every one (%d refusal(s)). That "
                         "is a reading about the FRAMES, not about your stash."
                         % (m["gated"], m["refused"]))
    return OK, ("%d of %d panel(s) measured%s"
                % (m["measured"], m["gated"],
                   " (%d refused honestly)" % m["refused"] if m["refused"] else ""))


def _anything_there():
    m = _measure()
    if not m["measured"]:
        return UNKNOWN, "nothing measured — see above"
    if not m["occupied"]:
        return OK, "%d cell(s) measured and every one is EMPTY — your stash really is empty here" % m["free"]
    return OK, ("%d occupied cell(s) across %d panel(s) — there IS loot in this footage"
                % (m["occupied"], m["measured"]))


def _names():
    """THE ANSWER. A grid prints no names; only the hover tooltip does."""
    m = _measure()
    try:
        with open(os.path.join(HERE, "vault_accum.json"), encoding="utf-8") as fh:
            led = json.load(fh) or {}
    except Exception:
        return UNKNOWN, "vault_accum.json is unreadable — cannot say what has been named"
    rows = len(led.get("owned") or []) + len(led.get("byKey") or {})
    if rows:
        return OK, "%d row(s) in the ledger — the readers have named things" % rows
    if m.get("occupied"):
        return MISSING, ("ZERO named items, and %d cell(s) are visibly full. D2R prints NO names in "
                         "a stash grid — a name exists only in the HOVER TOOLTIP. Film one pass with "
                         "the tooltip up over the items you care about and the same sweep will name "
                         "them." % m["occupied"])
    return UNKNOWN, "nothing named and nothing measured as occupied — no evidence either way"


def _seals():
    p = os.path.join(HERE, "vault_swept.json")
    if not os.path.isfile(p):
        return MISSING, ("vault_swept.json does not exist — no vault sweep has ever sealed a reel, "
                         "so retention has nothing it may delete (that is correct, not a fault)")
    try:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh) or {}
    except Exception:
        return UNKNOWN, "vault_swept.json is unreadable"
    prod = sum(1 for v in d.values() if isinstance(v, dict) and (v.get("rows") or 0) > 0)
    return OK, "%d reel(s) sealed, %d of them with rows" % (len(d), prod)


def diagnose():
    rows = [
        _check("footage", _footage),
        _check("stash panels", _stash_panels),
        _check("panels measure", _panels_measure),
        _check("anything there", _anything_there),
        _check("readable names", _names),
        _check("sealed reels", _seals),
    ]
    # only the first three BLOCK: without footage, a panel and a measurement there is nothing to say.
    # "no readable names" is the normal state of his film and must never read as a broken system.
    blocking = {"footage", "stash panels", "panels measure"}
    bad = [r for r in rows if r["state"] == MISSING and r["name"] in blocking]
    return {"ready": not bad, "checks": rows,
            "blocking": [r["name"] for r in bad],
            "unknown": [r["name"] for r in rows if r["state"] == UNKNOWN]}


if __name__ == "__main__":
    import console_safe  # noqa: F401 — the glyphs below must survive a non-UTF-8 console

    d = diagnose()
    icon = {OK: "🟢", MISSING: "🟠", UNKNOWN: "⚪"}
    print("\n🗄 VAULT DOCTOR — what your own film can and cannot tell me\n")
    _w = max([len(r["name"]) for r in d["checks"]] + [12])
    for r in d["checks"]:
        print("  %s %-*s %s" % (icon.get(r["state"], "?"), _w, r["name"], r["detail"]))
    print()
    if d["ready"]:
        print("✅ the chain can read this footage — anything orange above is about the FILM, not the code.")
    else:
        print("⛔ nothing to read yet — %s" % ", ".join(d["blocking"]))
    if d["unknown"]:
        print("⚪ could not check: %s" % ", ".join(d["unknown"]))
    raise SystemExit(0 if d["ready"] else 1)
