#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""♥♥ HEART 2.0 — the instruments watch themselves.

    python3 tv/heart2.py --report      the census: proven · blind · unproven · unprovable
    python3 tv/heart2.py --prove       re-tamper every guard that declares a proof, in a SANDBOX
    python3 tv/heart2.py --prove NAME  just this one
    python3 tv/heart2.py --detect      what no gate covers, dropping what is already covered
    python3 tv/heart2.py --ratchet     the unproven backlog may only ever shrink

═══════════════════════════════════════════════════════════════════════════════════════════════
THE DISTINCTION THAT MAKES IT v2
═══════════════════════════════════════════════════════════════════════════════════════════════

    heart v1   is the SYSTEM healthy?      — lanes, routes, stores, the console
    heart v2   are my own INSTRUMENTS      — the gates and the locks themselves
               still alive?

**MEASURED 2026-09-08, and this is the whole argument.** The heart was GREEN while 12 of 238 gates
were red, 8 of those were blind instruments, and the full set had been failing in CI since
2026-09-07 06:12 — 28 of the last 40 runs. Every check the heart made was working. Nothing was
checking the checkers, so nobody knew.

Three of the eight were laws that had silently STOPPED MEASURING what they claimed while staying
green — q-level probes written when set pieces had no data, still passing, grading nothing.

═══════════════════════════════════════════════════════════════════════════════════════════════
THE NUMBER THAT SETTLES "isn't it basically built?"
═══════════════════════════════════════════════════════════════════════════════════════════════

    gates registered                          247
    Wilson locks with a re-runnable harness     19
    gates with an EXECUTABLE red-proof           0      <- before this file
    test files even STATING a red-proof           1

Every one of those gates was proven red exactly once, by hand, in a shell, and that proof survives
only as prose in a docstring. It cannot be re-run. **So the number of gates that can still go red
is UNKNOWN — not zero, not fine. Unknown.** [[unknown-stays-unknown]]

═══════════════════════════════════════════════════════════════════════════════════════════════
THE PROTOCOL
═══════════════════════════════════════════════════════════════════════════════════════════════

A gate declares its own defeat, executably, beside itself:

    RED_PROOF = [{
        "why":     "what the law is FOR — the defect, in one line",
        "file":    "control_app.py",        # relative to tv/
        "find":    "<the exact bytes that make the law hold>",
        "replace": "<the bytes that reintroduce the defect>",
        "matches": 1,                       # EXACT count expected
    }]

and `--prove` does four things per proof, in this order, because each one catches a different lie:

  1. **CLEAN RUN in the sandbox.** The gate must PASS untampered. If it fails clean, the sandbox is
     wrong and nothing after it means anything — reported UNPROVABLE, never BLIND.
  2. **MATCH COUNT.** `find` must occur exactly `matches` times. A sabotage that matches 0 times
     changes nothing and the gate stays green for the most boring reason there is. Six times in one
     day the sabotage was the broken thing, not the law. **PRINT THE MATCH COUNT.**
     [[sabotage-is-usually-the-wrong-one]]
  3. **TAMPER AND RE-RUN.** The gate must now FAIL.
  4. **RESTORE**, so the next proof starts from clean bytes.

A gate that survives its own defeat is **BLIND** — the finding this whole file exists to produce.

⚠⚠ THE SANDBOX IS THE SAFETY STORY, AND IT IS NOT OPTIONAL. Achilles corrupted real journals by
tampering in place (its REG-011). Here the same mistake is worse: `tv/` holds 5.8 GB of his footage,
and a `cp -R` of it already caused an ENOSPC that broke every Bash call in a session — nobody could
run `df`, let alone `rm`. So: `safe_copy.py`, which excludes frames/.render_shots/.git/node_modules,
refuses above 400 MB and refuses any copy leaving under 4 GB free. Measured: tv/ is 5,865 MB, the
safe copy is 43.7 MB. **Never `cp -R`.**

⛔ IT PROPOSES INTO A FILE. IT NEVER EDITS A GUARD. Achilles' reason stands verbatim: *"In one night
working this tree I introduced three defects while fixing others, and I can read a diff."* A tool
that repairs its own instruments can talk itself into anything.

⚠ A RATCHET, NOT A BAN. 247 gates cannot grow proofs in one pass, and a law that fails on all of
them is one nobody can ship. Mandatory for every NEW gate; the backlog burns down.
"""
import argparse
import ast
import hashlib
import io
import json
import os
import time
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
except Exception:
    pass

STATE = os.path.join(HERE, ".heart2.json")
PROPOSALS = os.path.join(HERE, ".heart2_proposals.md")

PROVEN, BLIND, UNPROVEN, UNPROVABLE, INVALID = "PROVEN", "BLIND", "UNPROVEN", "UNPROVABLE", "INVALID"


# ── finding the gates ────────────────────────────────────────────────────────────────────────
def _stale_say(v):
    """What the ratchet cannot see, in words a reader can act on. -> str

    ⚠ A NUMBER WITH NO SENTENCE IS A NUMBER NOBODY ACTS ON. `coverageStaleNodes: 30` means thirty
    watched nodes could disappear and every automated check would still read clean, and that is not
    obvious from the integer. UNKNOWN is said out loud rather than rendered as a quiet zero.
    """
    n = v.get("coverageStaleNodes")
    if not isinstance(n, int):
        return ("how much slack this ratchet carries is UNKNOWN — the render verdict predates the "
                "measurement, so nothing here says whether a watched node could vanish unseen")
    if not isinstance(v.get("coverageFloorKnown"), bool):
        return ("%d node(s) of slack were counted, but whether a floor exists at all is UNKNOWN, "
                "so this number has no denominator" % n)
    if not v.get("coverageFloorKnown"):
        return "there is no coverage floor yet, so the ratchet cannot fire for any target"
    if n <= 0:
        return "no slack: every floor sits at what a clean run actually photographs"
    return ("%d node(s) of slack — that many watched nodes could vanish and this ratchet would "
            "still read clean, because each floor sits below what a clean run photographs" % n)


def _fan_state(rec):
    """What one width's payload actually IS. -> 'reading' | 'threw' | 'unread'

    ⚠⚠ v2928 — THE WRITER HAS THREE STATES AND v2926's READER HAD TWO. Caught by the cross-family
    eye and reproduced: `control_ui.html` writes `{ok:false, threw:"..."}` when `_hrtFanFit` raises,
    and `{ok:false, reverted:false, ...}` for its own `no fan` / `no layout yet` refusals. NEITHER
    carries `error`/`unread`/`unparsed`, so v2926 counted both as readings, found `reverted` not
    True, and printed **"the lock fan kept its placement"**. MEASURED: a payload of
    `{"ok": false, "threw": "TypeError"}` produced `fanRevertedAt: []` and that exact sentence.

    The page's own `catch` exists to stop a crash and a keep looking alike — its comment says so in
    as many words — and the reader built to answer #53 reintroduced the collapse one layer up.
    [[unknown-stays-unknown]] [[zero-needs-a-denominator]]

    ⚠ A MISSING `ok` IS NOT A PASS. Anything that is not explicitly `ok: true` is refused, so an
    older or unexpected shape reads UNMEASURED rather than clean.
    """
    if not isinstance(rec, dict):
        return "unread"
    if any(k in rec for k in ("error", "unread", "unparsed")):
        return "unread"
    if rec.get("ok") is True:
        return "reading"
    # ⚠⚠ v2931 — A CRASH AND A REFUSAL ARE DIFFERENT ANSWERS, and v2928 printed one sentence for
    # both. control_ui.html writes `{ok:false, threw:"..."}` when `_hrtFanFit` RAISES, and
    # `{ok:false, why:"the fan has no layout yet"}` when the solver RAN and declined — a timing or
    # layout miss, not an exception. v2928's rule was "ok present and not True -> threw", so the
    # heart told the operator THE SOLVER FAILED for what is really "the overlay opened before the
    # SVG had layout". The page's own comment says the two need different fixes.
    # Caught by the cross-family eye on v2928, one ship after it fixed the keep-lie.
    # [[unknown-stays-unknown]] [[label-outlived-referent]]
    if "threw" in rec:
        return "threw"
    if "ok" in rec:
        return "refused"
    return "unread"


def _fan_buckets(v):
    """Every width sorted into what it actually said. -> (reported, reading, threw, unread, refused)

    ⚠ v2936 — THE ARITY IS FIVE AND THE DOCSTRING SAID FOUR. v2931 split `refused` out of `threw`
    and updated every unpacker in the tree, but not the sentence that tells the next editor how
    many names to unpack — so following the docstring is a runtime ValueError. Caught by the
    cross-family eye, and it is the same [[label-outlived-referent]] class that ship just fixed
    on `_fan_counts`."""
    fan = (v.get("reports") or {}).get("heart-fan")
    if not isinstance(fan, dict) or not fan:
        # ⚠ v2928 — NOT `.get("heart-fan", {})`. The eye flagged a fabricated 0 here; measured, the
        # isinstance guard already caught two of its three cases, but the third — `heart-fan`
        # PRESENT AND EMPTY — really did publish `fanWidths: 0` beside `fanRevertedAt: None`, two
        # different answers to "did anybody measure". `not fan` closes it for good.
        return (None, [], [], [], [])
    rep = sorted(fan)
    by = {}
    for w in rep:
        by.setdefault(_fan_state(fan[w]), []).append(w)
    # ⚠⚠ A REFUSAL GETS ITS OWN BUCKET — it rides with NEITHER unread nor threw. None of the
    # three produced a placement, but they are three different reasons and `_fan_say` prints a
    # different sentence for each. This comment said "rides with unread" and the code has never
    # done that; an editor tidying the code to match would have deleted the declined-solver
    # sentence v2931 added. The eye caught the comment, not the code.
    return (rep, by.get("reading", []), by.get("threw", []),
            by.get("unread", []), by.get("refused", []))


def _fan_reverted(v):
    """Widths where the fan put everything back, or None if nothing was readable. -> list|None

    ⚠ None and [] ARE DIFFERENT ANSWERS. [] means every READABLE width kept its placement; None
    means no width produced a reading at all — absent, empty, failed, or thrown.
    Collapsing them is how #53 would read solved. [[unknown-stays-unknown]]
    """
    rep, reading, _threw, _unread, _refused = _fan_buckets(v)
    if rep is None or not reading:
        return None
    fan = v["reports"]["heart-fan"]
    return [w for w in reading if fan[w].get("reverted") is True]


def _fan_counts(v):
    """(reported, readable) — None when NOTHING WAS REPORTED; readable may legitimately be 0. -> tuple

    ⚠ v2931 — the v2928 docstring said "never 0" and the body returns 0 whenever heart-fan
    reported widths and none of them produced a reading. The eye judged it right: the published 0
    is the correct unknown-stays-unknown answer (widths WERE looked at, none was readable) and the
    DOCSTRING was the lie. A caller writing `readable or fallback` on the strength of that sentence
    would treat a measured zero as missing. [[label-outlived-referent]]
    """
    rep, reading, _t, _u, _r = _fan_buckets(v)
    return (None if rep is None else len(rep), None if rep is None else len(reading))


def _fan_say(v):
    """#53's answer in one sentence, or UNKNOWN said out loud. -> str

    ⚠⚠ v2926 — THE HEART DID NOT READ THE ONE THING BUILT TO ANSWER #53. v2924 added a per-width
    `report` tap and wrote `reports` into .render_verdict.json; MEASURED 2026-09-11, heart2.py
    contained the string "fanfit" ZERO times and "report" ZERO times. The fan could revert its
    placement at every photographed width and every automated supervisor still read OK.
    That is the identical shape this file already paid for at v2917 with `coverageStaleNodes` —
    a write whose only reader is its own writer. [[the-unjoined-end]] [[plumbing-with-no-tap]]

    ⚠ IT REPORTS, IT DOES NOT REFUSE. `state` keeps meaning "did every target report"; this rides
    beside it under its own name, for the same reason LAW 5 gives.
    """
    if not isinstance(v.get("reports"), dict):
        return ("whether the heart's lock fan kept or reverted its placement is UNKNOWN — this "
                "render verdict predates the per-width report tap, so nothing here measured it")
    rep, reading, threw, unread, refused = _fan_buckets(v)
    if rep is None:
        return ("whether the lock fan kept or reverted is UNKNOWN — heart-fan handed back no "
                "reading in the last render, which is not the same as a clean one")
    # ⚠ THE CAVEAT TRAVELS WITH THE NUMBER, or the heart re-creates the over-claim the tap was
    # rewritten to remove: the fan solves ONCE at open and never re-solves on resize, so a reading
    # filed under a width names where it was READ, never where it was SOLVED. [[stale-reading]]
    stale = (" (each reading names the width it was READ at; the fan solves once at open, so the "
             "width it was SOLVED at is UNKNOWN)")
    tail = ""
    if threw:
        tail += (" · the solver FAILED at %d width(s) (%s) — ok:false, which is not a placement"
                 % (len(threw), ", ".join(threw)))
    if refused:
        tail += (" · the solver RAN AND DECLINED at %d width(s) (%s) — ok:false with a reason, "
                 "which is a timing or layout miss and not a crash"
                 % (len(refused), ", ".join(refused)))
    if unread:
        tail += " · %d width(s) handed back no reading (%s)" % (len(unread), ", ".join(unread))
    if not reading:
        return ("the lock fan reported at %d width(s) and NONE produced a reading — UNMEASURED, "
                "not clean%s" % (len(rep), tail))
    rev = _fan_reverted(v) or []
    head = ("the lock fan REVERTED at %d of %d readable width(s): %s"
            % (len(rev), len(reading), ", ".join(rev))) if rev else \
           ("the lock fan kept its placement at all %d readable width(s)" % len(reading))
    return head + tail + stale


def surface_verdict(path=None):
    """What the LAST render run actually reported. -> dict

    v2859 — the heart counted GATES and never the SURFACES. render_check now records which targets
    reported; this reads that record and refuses to guess when it is absent or stale.
    `state` is one of: OK (a full run reported every target), PARTIAL (a subset run — cannot speak
    for the rest), UNMEASURED (no record, or unreadable). UNMEASURED IS NOT ZERO. [[stale-reading]]
    """
    # ⚠ `path` EXISTS SO A LAW CAN ASK THE REAL QUESTION. Without it the only way to test
    # "an absent verdict reads UNMEASURED" is to move the real file out from under a live
    # console, or to assert on the SHAPE of this function instead of its behaviour — and a
    # law that reads source instead of running the code is the weaker kind this repo keeps
    # having to strengthen. [[feedback-blind-fixture-green-gate]]
    p = path or os.path.join(HERE, ".render_verdict.json")
    if not os.path.exists(p):
        return {"state": "UNMEASURED", "why": "render_check has never written a verdict here — "
                                              "run `python3 tv/render_check.py`"}
    try:
        with io.open(p, encoding="utf-8") as fh:
            v = json.load(fh)
    except Exception as e:
        return {"state": "UNMEASURED", "why": "the render verdict would not parse (%s)"
                                              % type(e).__name__}
    rep = list(v.get("reported") or [])
    tot = int(v.get("totalTargets") or 0)
    age = None
    if v.get("ranAt"):
        age = int((time.time() * 1000 - float(v["ranAt"])) / 1000)
    return {"state": ("OK" if (v.get("full") and tot and len(rep) >= tot) else
                      "PARTIAL" if rep else "UNMEASURED"),
            "reported": len(rep), "totalTargets": tot, "ageS": age,
            "coverageMissing": int(v.get("coverageMissing") or 0),
            # ⚠⚠ v2917 (#72) — THE HEART CLAIMED TO SUPERVISE THIS AND DID NOT READ IT.
            # v2916 recorded the ratchet's own blind spot into .render_verdict.json and dropped the
            # heart join (P7) because `surfaces` had no UI consumer — then shipped FOUR assertions
            # that the heart was watching: render_check.py's two comments, this gate's header, and
            # LAW 7 itself. Found by the cross-family eye twenty minutes after it shipped.
            # MEASURED on his tree: .render_verdict.json carried `coverageStaleNodes: 30` while
            # `surface_verdict()` returned state OK / coverageMissing 0, and grep for a consumer of
            # coverageStale* outside render_check and its own gate returned ZERO. Thirty watched
            # nodes could vanish and every automated supervisor still read clean.
            # Moving a fact from scrollback into a file nobody opens is a better grave, not
            # supervision. [[the-unjoined-end]] [[label-outlived-referent]]
            # ⚠ IT REPORTS, IT DOES NOT REFUSE. LAW 5 of that gate is deliberate: a stale floor must
            # not by itself red a run, because a gate that is only ever red gets switched off. So
            # `state` keeps meaning "did every target report", and the slack rides beside it under
            # its own name with its own words.
            "coverageStaleNodes": (int(v["coverageStaleNodes"])
                                   if isinstance(v.get("coverageStaleNodes"), int) else None),
            # ⚠ THREE ANSWERS. None = an older render_check wrote this file and never measured
            # slack, which is UNKNOWN and not zero. False = there is no floor at all. True = a floor
            # exists, so a 0 beside it is MEASURED. [[unknown-stays-unknown]]
            "coverageFloorKnown": (bool(v["coverageFloorKnown"])
                                   if isinstance(v.get("coverageFloorKnown"), bool) else None),
            "coverageStaleSay": _stale_say(v),
            # ⚠⚠ v2926 (#53) — THE JOIN. Counts first so a law can assert on them, then the
            # sentence, because a number with no sentence is a number nobody acts on.
            # `fanRevertedAt` is None, never 0, when nothing was readable: UNMEASURED is not zero.
            # ⚠⚠ v2928 — TWO NAMES, BECAUSE THERE ARE TWO NUMBERS. v2926 published one `fanWidths`
            # = len(all keys) while `_fan_say` divided by len(readable). MEASURED: five widths all
            # returning {"error": …} gave `fanWidths: 5` beside a sentence saying NONE could be
            # read — a consumer dividing by the published denominator gets a different answer from
            # the published sentence. A name that promises the sentence's denominator must BE it.
            # [[zero-needs-a-denominator]] [[label-outlived-referent]]
            "fanWidthsReported": _fan_counts(v)[0],
            "fanWidthsReadable": _fan_counts(v)[1],
            "fanRevertedAt": _fan_reverted(v),
            "fanSay": _fan_say(v),
            "renderFailures": int(v.get("renderFailures") or 0)}


def gates_fingerprint(gates=None):
    """A content digest of every gate file. -> str

    ⚠⚠ v2862 — MTIME IS NOT A PORTABLE STALENESS SIGNAL, and the sandbox proved it. The first cut
    of the lock's staleness rule compared each gate file's mtime against the census `ranAt`. Correct
    on the machine that ran the prove — and WRONG everywhere else: safe_copy, a git checkout, CI and
    the Windows machine all stamp fresh mtimes, so every gate looks newer than the census, the lock
    closes on every surface, and `--prove` reported the lock gate UNPROVABLE because it was already
    red in its own sandbox. A rule that only holds in the tree that wrote it is not a rule.

    CONTENT survives copying. This is what "the instruments have not changed since they were proved"
    actually means. [[stale-reading]] [[the-harness-isolates-the-port-not-the-world]]
    """
    # ⚠⚠ v2869 — READ IT WHERE IT LIVES, NOT WHERE THE PROCESS HAPPENS TO STAND. `gate_files()`
    # returns BARE BASENAMES (it checks existence against HERE, so it is cwd-independent) and this
    # loop passed one straight to `_read_text`, which opens relative to the CURRENT DIRECTORY.
    # MEASURED: from the repo root, 273 of 273 gates read as UNREADABLE and the digest came out
    # 4d640d7d instead of 55330cec — so `_heart_says_watched()` called a freshly written census
    # STALE and `may()` refused EVERY lock, permanently, for any caller not standing in tv/.
    # The v2864 sentinel is what made it visible rather than silent, and it is exactly the class
    # v2862 replaced mtime to escape: a rule that only holds where it was run.
    # ⚠ The SENTINEL keeps the bare name on purpose — an absolute path differs per machine and
    # would undo the portability the content digest exists for. [[stale-reading]] [[copy-drift]]
    h = hashlib.sha256()
    for n, f in sorted(gates if gates is not None else gate_files()):
        h.update(n.encode("utf-8"))
        src = _read_text(f if os.path.isabs(f) else os.path.join(HERE, f))
        if src is None:
            # ⚠ v2864 — UNREADABLE IS NOT EMPTY, and a cross-family review caught the collapse:
            # hashing None as "" made every unreadable file digest identically to every empty one,
            # so the set of readable gates could change while the fingerprint held still. The path
            # goes into the sentinel so two different unreadable files differ. [[unknown-stays-unknown]]
            h.update(b"\x00UNREADABLE\x00" + f.encode("utf-8", "replace"))
            continue
        h.update(hashlib.sha256(src.encode("utf-8", "replace")).digest())
    # ⚠⚠ AND THE PROVER ITSELF. Same review: the digest covered gate FILES only, so a change to
    # gate_files(), to how the sabotage is injected, or to any decision heart2 makes about RED would
    # leave the fingerprint identical and the lock would still call a stale proof current. The proof
    # is only as true as the thing that produced it, so this file is folded in too.
    # [[the-unjoined-end]]
    _self = _read_text(os.path.join(HERE, "heart2.py"))
    h.update(hashlib.sha256((_self or "").encode("utf-8", "replace")).digest())
    return h.hexdigest()[:32]


def pixel_gates(gates=None, unclassified=None):
    """The gates that actually LOOK AT PIXELS, by their IMPORTS. -> set[str]

    v2858 — ONE NUMBER WAS HIDING A 93/7 SPLIT. Konyo: "when we hit 100% on heart 2.0 its also a
    VISUAL PASS right? like its not just backend". MEASURED the moment he asked: 269 gates, only TEN
    import render_check or playwright, so 100% on the single number would be ~96% backend — true as
    a count and a lie as a label. [[label-outlived-referent]]

    ⚠ IMPORTS, NOT A TEXT SCAN. The first cut grepped for 'render_check' / 'playwright' /
    '.render_shots' and answered 18, because prose and comments naming the harness counted as
    looking at pixels. Parsing answers 10. [[source-reading-guard]]

    ⚠⚠ v2860 — IT SWALLOWED THE GATES IT COULD NOT READ, and a cross-family review caught it. Both
    the unreadable case and the SyntaxError case did a bare `continue`, so a gate that really does
    import render_check but was momentarily unreadable — permissions, a half-written checkout, a
    syntax error the day the census ran — silently left the pixel set and landed in the BACKEND
    count. The owner would read an inflated backend share, and a later "100%" would quietly include
    a visual gate nobody classified. A failed read handed back as data, inside the thing that
    measures the heart. `unclassified` collects those names so the census can SAY so.
    [[unknown-stays-unknown]]

    ⚠ AND IT UNDER-COUNTS, IN THE DANGEROUS DIRECTION. Same review: top-level Import/ImportFrom
    names miss importlib, __import__, exec/compile, and any gate that reaches the renderer through
    a helper instead of importing it. So pixelTotal is a FLOOR — the visual share is at best this
    good and possibly worse, never better. Recorded because this number answers "is 100% also a
    visual pass", and a bias that flatters that answer is the one bias that must not go unsaid.
    """
    out = set()
    _unk = unclassified if unclassified is not None else []
    for n, f in (gates if gates is not None else gate_files()):
        # ⚠ v2869 — SAME BARE-NAME BUG AS gates_fingerprint, same cause: gate_files() hands back
        # basenames and _read_text opens relative to cwd. From the repo root this made every gate
        # UNREADABLE, so pixelTotal would read 0 and pixelUnclassified 273 — a census that answers
        # "how much of this is pixels" with a number produced by the reader's working directory.
        src = _read_text(f if os.path.isabs(f) else os.path.join(HERE, f))
        if src is None:
            _unk.append(n)                # UNREADABLE is not "backend"
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            _unk.append(n)                # UNPARSEABLE is not "backend" either
            continue
        mods = set()
        for x in ast.walk(tree):
            if isinstance(x, ast.Import):
                for a in x.names:
                    mods.add(a.name.split(".")[0])
            elif isinstance(x, ast.ImportFrom):
                if x.module:
                    mods.add(x.module.split(".")[0])
        if mods & {"render_check", "playwright"}:
            out.add(n)
    return out


def _read_text(path):
    try:
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except Exception:
        return None


def gate_files(say=print):
    # ⚠ `say` IS A PARAMETER HERE, NOT A GLOBAL. heart2 threads its printer through
    # (make_sandbox(say=print), prove(..., say=print)); there is no module-level `say`.
    # v2882 added the dropped-gate warning below WITHOUT this parameter, so the one line that
    # exists to make a silent omission loud would have raised NameError the first time a gate
    # was actually dropped — a warning that cannot fire, inside the fix for a warning that was
    # never written. Caught because --triage hit the same mistake and crashed immediately.
    # [[plumbing-with-no-tap]] [[feedback-blind-fixture-green-gate]]
    """Every registered gate that is a python test file here. -> [(name, filename)]"""
    out, _dropped = [], []
    try:
        import run_gates
    except Exception as e:
        print("  run_gates will not import: %s" % e)
        return out
    for g in getattr(run_gates, "GATES", []):
        # ⚠ THE FIELD IS `argv`, NOT `cmd`. The first cut guessed `cmd`, found nothing, and
        # printed "0 gates" — a zero produced by my own parser, wearing the clothes of a
        # measurement. Every percentage under it would have been 0.0% of nothing.
        # [[zero-needs-a-denominator]] [[feedback-suspect-the-instrument]]
        cmd = list(getattr(g, "argv", None) or getattr(g, "cmd", None) or [])
        fn = None
        for part in cmd:
            if isinstance(part, str) and part.endswith(".py") and os.path.basename(part) != "":
                base = os.path.basename(part)
                if os.path.exists(os.path.join(HERE, base)):
                    fn = base
                # ⚠⚠ v2882 — A GATE WHOSE FILE IS NOT IN tv/ WAS DROPPED SILENTLY, AND COUNTED
                # NOWHERE. `visual-lock` runs REPO/visual_lock_invariant.py; the check above only
                # looked in HERE, so it failed and the gate vanished from the heart's scope with no
                # line saying so. Measured: run_gates registers 279 gates, the heart reported 278 —
                # and "0 blind of 278" read as "every gate is accounted for" while one was not even
                # asked about. The heart's own premise is that the instruments must watch
                # themselves; a census that quietly omits a row is the first thing that premise
                # forbids. Root files are addressed ".."-relative so every consumer keeps working:
                # red_proofs_in and _run_gate both os.path.join(<tv>, filename), which resolves to
                # the repo root, and make_sandbox places the file there.
                # [[unknown-stays-unknown]] [[zero-needs-a-denominator]] [[heart-v2-instruments-watch-themselves]]
                elif os.path.exists(os.path.join(REPO, base)):
                    fn = os.path.join("..", base)
        if fn:
            out.append((getattr(g, "name", fn), fn))
        else:
            _dropped.append(getattr(g, "name", "?"))
    if _dropped:
        say("  ⚠ %d registered gate(s) have no python file this heart can read, so they are NOT in "
            "the census below — UNKNOWN, not clean: %s" % (len(_dropped), ", ".join(_dropped)))
    return out


def red_proofs_in(filename):
    """The RED_PROOF list a gate file declares, read WITHOUT importing it.

    Parsed rather than imported: importing 247 test modules to ask a question about their source
    would execute 247 modules' import-time side effects, and several of them read his live console.
    [[source-reading-guard]]
    """
    import ast
    p = os.path.join(HERE, filename)
    try:
        with io.open(p, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
    except Exception:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "RED_PROOF":
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:
                        return None
    return None


# ── the sandbox ──────────────────────────────────────────────────────────────────────────────
def proof_needs_in(filename):
    """The data a gate's proof needs beside the source. -> [relative path under tv/]

    ⚠⚠ v2888 — A GATE WHOSE SUBJECT IS ABSENT SKIPS, AND A SKIP IS NOT A PASS.
    test_chronicle_template came back BLIND with the reason "ALL 12 law(s) SKIPPED in the sandbox —
    the tamper was never judged". That was not a bad anchor: every one of its 12 laws is decorated
    `@unittest.skipUnless(_HAVE_FOOTAGE)`, MEASURED 12 of 12, so with no footage the whole gate is a
    no-op that exits 0. safe_copy deliberately leaves tv/'s 5.8 GB of footage behind — correctly,
    that rule exists because copying it hit ENOSPC once — so the sandbox could never judge it.
    This is the narrow door: a gate names the ONE data path its proof needs, by hand, and only that
    path is brought across. Read by AST, never imported. [[regression-guard]] [[zero-needs-a-denominator]]
    """
    # ⚠⚠ None MEANS "I COULD NOT READ THIS". IT NEVER MEANS []. The first cut answered [] on a
    # parse failure and the swallow ratchet caught it ON CI THE SAME DAY — RANK 1, "a failed read
    # handed back as DATA", baseline 74 -> 75, `tv/heart2.py 0 -> 1`. [] says "this gate declares
    # no needs"; a file that will not parse says nothing at all, and those are opposite facts. Get
    # it wrong and a gate is silently deprived of the data its proof requires, then reported BLIND
    # for a reason that names none of it. A non-.py target still answers [] and that is correct:
    # PROOF_NEEDS is a python declaration, so a file that cannot hold one genuinely declares none.
    # [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
    p = os.path.join(REPO, "tv", filename) if not os.path.isabs(filename) else filename
    if not os.path.isfile(p) or not p.endswith(".py"):
        return []
    try:
        tree = ast.parse(io.open(p, encoding="utf-8", errors="replace").read())
    except Exception:
        return None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "PROOF_NEEDS" for t in node.targets):
            continue
        try:
            v = ast.literal_eval(node.value)
        except Exception:
            return None            # it DECLARES needs and they cannot be read — UNKNOWN, not none
        return [str(x) for x in v] if isinstance(v, (list, tuple)) else []
    return []


def make_sandbox(say=print):
    """A throwaway copy of the repo via safe_copy.py. -> (tv_path, root) | (None, None)

    ⚠⚠ TWO OF MY OWN MISTAKES LIVE IN THIS FUNCTION'S HISTORY, and both produced a confident
    wrong answer rather than an error:

      1. `safe_copy.copy()` REFUSES when the destination already exists — "Remove it yourself,
         deliberately" — and `tempfile.mkdtemp()` CREATES the directory. So it was handed a path
         it was designed to reject, every time.
      2. Its RETURN CODE was ignored. It answered 2, wrote nothing, and the code sailed on to
         report five gates UNPROVABLE with the reason "control_app.py is not in the sandbox" —
         true, and about a sandbox that did not exist. A refusal read as success.
         [[exit-status-of-the-block]]

    The protocol is what saved it: because a clean run is required BEFORE any tamper, an empty
    sandbox came out as UNPROVABLE and never as BLIND or PROVEN. A missing file could not be
    mistaken for a passing gate. That ordering is the whole reason the verdicts are trustworthy.
    """
    root = tempfile.mkdtemp(prefix="heart2.")
    dest = os.path.join(root, "repo")          # must NOT exist — safe_copy refuses if it does
    try:
        import safe_copy
    except Exception as e:
        say("  safe_copy will not import (%s) — refusing to tamper anywhere else" % e)
        shutil.rmtree(root, ignore_errors=True)
        return None, None
    try:
        rc = safe_copy.copy(REPO, dest, False, lambda *a, **k: None)
    except Exception as e:
        say("  the sandbox could not be built: %s" % type(e).__name__)
        shutil.rmtree(root, ignore_errors=True)
        return None, None
    if rc not in (0, None):
        say("  safe_copy REFUSED the sandbox (exit %s) — nothing was copied, so nothing can be "
            "proven. That is UNKNOWN, not clean." % rc)
        shutil.rmtree(root, ignore_errors=True)
        return None, None
    # ⚠⚠ v2821 — SAFE_COPY COPIES `tv/` ONLY, AND 59 OF 259 GATES READ `bible.html`.
    # That file lives in the repo ROOT, so every law about the bible came back UNPROVABLE with
    # "bible.html is not in the sandbox" — 23% of the suite structurally unable to prove itself,
    # for want of one 6.1 MB file. Measured, not estimated: 59 gates name it.
    #
    # ⚠ ONE FILE, BY NAME. NEVER `cp -R` of the repo or of tv/ — tv/ holds ~5.8 GB of footage and
    # copying it caused an ENOSPC once already. safe_copy exists precisely to avoid that, and this
    # adds a single named file beside its output rather than widening what it copies.
    # v2882 — visual_lock_invariant.py joins bible.html here: it is the one GATE whose file lives
    # in the repo root, and without it in the sandbox `visual-lock` cannot be proven.
    # ⚠⚠ v2888 — BRING ACROSS THE DATA A GATE DECLARED, AND NOTHING ELSE.
    # `cp -c` is an APFS CLONE: no bytes are copied and no disk is spent, and a write inside the
    # sandbox lands on the copy rather than on his real footage — which matters here because these
    # ARE his screenshots. Only paths a gate names in PROOF_NEEDS come over; there is no glob and
    # no recursion into tv/ at large, because that is the ENOSPC that safe_copy exists to prevent.
    _needs, _unreadable = set(), []
    for _gn, _fn in gate_files(say=lambda *a, **k: None):
        _got = proof_needs_in(_fn)
        if _got is None:
            _unreadable.append(_gn)     # NOT "declares nothing" — nobody could tell
            continue
        _needs.update(_got)
    if _unreadable:
        say("  ⚠ %d gate file(s) would not parse, so whether they declare PROOF_NEEDS is UNKNOWN, "
            "not none: %s" % (len(_unreadable), ", ".join(_unreadable[:6])))
    for _need in sorted(_needs):
        # ⚠ v2888 — A NEED MAY REACH ABOVE tv/ ("../.git"), BECAUSE NOT EVERY SUBJECT LIVES IN tv/.
        # test_tasks_ships_are_recorded reads GIT HISTORY, and a sandbox is a copy with no .git, so
        # it failed with "git named 0 shipped versions on a FULL clone" — a sentence that asserts
        # it is NOT a venue problem while standing in exactly that venue. Both sides are normalised
        # and checked for containment, so a need can never escape the repo or the sandbox.
        _s = os.path.normpath(os.path.join(REPO, "tv", _need))
        _inside = os.path.normpath(REPO) + os.sep
        if not (_s + os.sep).startswith(_inside):
            say("  PROOF_NEEDS %r points outside the repo — refusing to bring it across" % _need)
            continue
        if not os.path.exists(_s):
            say("  a gate declares PROOF_NEEDS %r and it is not on this machine — that gate stays "
                "UNPROVABLE here, which is the honest verdict" % _need)
            continue
        _d = os.path.normpath(os.path.join(dest, "tv", _need))
        if not (_d + os.sep).startswith(os.path.normpath(dest) + os.sep):
            say("  PROOF_NEEDS %r would land outside the sandbox — refused" % _need)
            continue
        try:
            os.makedirs(os.path.dirname(_d), exist_ok=True)
            _rc = subprocess.run(["cp", "-c", "-R", _s, _d],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT).returncode
            if _rc != 0:      # not APFS, or clones unavailable — say so rather than silently copying GBs
                say("  could not CLONE %r (cp -c exit %s) — not copying it by hand; the gate stays "
                    "UNPROVABLE rather than risking the disk" % (_need, _rc))
        except Exception as _e:
            say("  PROOF_NEEDS %r could not be brought across: %s" % (_need, type(_e).__name__))
    for _root_file in ("bible.html", "visual_lock_invariant.py"):
        _srcf = os.path.join(REPO, _root_file)
        if os.path.isfile(_srcf):
            try:
                shutil.copy2(_srcf, os.path.join(dest, _root_file))
            except Exception as _e:
                # not fatal: the bible-reading gates will simply report UNPROVABLE as before,
                # which is the honest outcome. It must never silently look like a pass.
                say("  could not place %s in the sandbox (%s) — gates that read it stay UNPROVABLE"
                    % (_root_file, type(_e).__name__))
    tv = os.path.join(dest, "tv")
    if not os.path.isfile(os.path.join(tv, "control_app.py")):
        say("  the sandbox is missing control_app.py — refusing to report verdicts about it")
        shutil.rmtree(root, ignore_errors=True)
        return None, None
    return tv, root


def blind_reason(why, matches, tail):
    """The sentence a BLIND verdict prints. -> str

    ⚠⚠ v2866 — A SKIP IS NOT A PASS, AND THE BLIND LINE COULD NOT TELL THEM APART.
    `test_the_lock_derives_from_the_heart[1]` came back BLIND and shipped that way in v2865's own
    census. The cause was not a weak law: the law called `self.skipTest()` because `.heart2.json` is
    gitignored and therefore absent from every sandbox, so the tampered run printed
    `OK (skipped=5)` — green, because nothing ran. "stayed GREEN through its own defeat" is exactly
    wrong about that: it never reached its own defeat.

    The two cases need different work — a real BLIND needs a stronger law, a skipped one needs the
    law to stop opting out — and the line that reports them said the same thing about both. It cost
    a shipped `blind: 1` and a deduction that the tail had been carrying the answer all along.
    [[zero-needs-a-denominator]] [[unknown-stays-unknown]]
    """
    _base = ("stayed GREEN through its own defeat (%d match(es)): %s" % (matches, str(why)[:70]))
    _sk = re.search(r"skipped=(\d+)", tail or "")
    _rn = re.search(r"Ran (\d+) test", tail or "")
    n_skipped = int(_sk.group(1)) if _sk else 0
    if not n_skipped:
        return _base
    if _rn is None:
        return (_base + "  ⚠ %d law(s) SKIPPED and the run did not say how many it ran (%s), so "
                        "whether the tamper was judged AT ALL is UNKNOWN."
                % (n_skipped, (tail or "").strip()[:60]))
    n_ran = int(_rn.group(1))
    if n_skipped >= n_ran:
        return (_base + "  ⚠ ALL %d law(s) SKIPPED in the sandbox — the tamper was never judged. "
                        "Fix the SKIP; the law itself has not been tested." % n_ran)
    return (_base + "  ⚠ %d of %d law(s) SKIPPED, but the other %d DID run and stayed green — so "
                    "the law IS weak, and separately some laws opted out. Both jobs, not one."
            % (n_skipped, n_ran, n_ran - n_skipped))


def _run_gate(sandbox_tv, filename, timeout=180, extra=(), script=None):
    # v2882 — `extra` carries the registered gate's argv tail (e.g. `--selftest`). Without
    # it a gate runs a command the suite never issues, and its verdict is about something
    # else. Default empty keeps every existing caller identical.
    """-> (passed: bool, tail: str)"""
    p = os.path.join(sandbox_tv, filename)
    if not os.path.exists(p):
        return None, "the gate file is not in the sandbox"
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"      # no stale .pyc can outlive a tamper
    # ⚠⚠ v2888 — AN ABSOLUTE ARGUMENT POINTS AT THE REAL TREE, WHICH THE TAMPER NEVER TOUCHED.
    # A gate handed /Users/.../tv/x.py reads the ORIGINAL x.py no matter what this sandbox says,
    # so its proof can only ever come back green. Re-root every repo-absolute argument onto the
    # copy before running. [[feedback-blind-fixture-green-gate]]
    _root = os.path.dirname(os.path.abspath(sandbox_tv))
    def _resite(a):
        if isinstance(a, str) and os.path.isabs(a) and a.startswith(REPO + os.sep):
            return os.path.join(_root, os.path.relpath(a, REPO))
        return a
    _args = [_resite(a) for a in extra]
    _cmd = ([sys.executable, "-c", script] + _args) if script else ([sys.executable, p] + _args)
    try:
        r = subprocess.run(_cmd, cwd=sandbox_tv, env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "timed out after %ss" % timeout
    # ⚠⚠ v2870 — THE LAST LINE ALONE IS A NUMERATOR WITH NO DENOMINATOR. unittest prints
    # "Ran 10 tests in 0.1s", a blank, then "OK (skipped=4)" — and keeping only the last line threw
    # away the one number that says whether a skip covered the WHOLE file or part of it. A
    # cross-family review of v2868: five laws skipping while three run and stay green is a WEAK
    # LAW, and blind_reason was instructing the reader to go delete skips instead.
    # [[zero-needs-a-denominator]]
    # ⚠⚠ v2872 — AND THE RESULT LINE IS NOT ALWAYS LAST EITHER. v2870 fixed the DENOMINATOR by
    # hunting backwards for `Ran N tests` and then kept taking `skipped=K` from whatever printed
    # last — the same last-line bug, applied to the half it was written to interpret. A cross-family
    # review of v2870: one `atexit` print, a DeprecationWarning on stderr (merged here via
    # stderr=STDOUT), any shutdown line, and `OK (skipped=5)` is no longer last. `n_skipped` reads 0
    # and a WHOLE-FILE skip reports as a weak law. Both lines are hunted now, and whatever really
    # printed last is kept beside them, because it may be the actual news.
    # ⚠⚠⚠ v2874 — AND THE RESULT IS THE ONE THAT FOLLOWS `Ran`, NOT THE LAST ONE THAT LOOKS LIKE
    # IT. Third round of this same class, each caught by the cross-family eye and not by me. v2872
    # hunted BACKWARDS for a result-shaped line, so anything printed afterwards that happens to look
    # like a result STEALS it and unittest's real one is dropped from the tail entirely. MEASURED on
    # the v2872 parser, a two-test whole-file skip that should read ALL 2:
    #     atexit print('DeprecationWarning: ...')  -> 'Ran 2 tests | OK (skipped=2) | Deprecation…'  ALL 2   ✔
    #     atexit print('OK')                       -> 'Ran 2 tests | OK'                             no warning ✘
    #     atexit print('FAILED to cleanup')        -> 'Ran 2 tests | FAILED to cleanup'              no warning ✘
    # v2872's own behavioural law could not catch it because its fixture printed a WARNING-shaped
    # line, which the predicate does not match — the blind-fixture shape that commit quoted while
    # shipping it. unittest prints `Ran N tests`, a blank, then the result; noise comes after. So
    # find `Ran` and take the NEXT result line going FORWARD.
    # ⚠ And the two matchers are now symmetric. `FAILED` was a PREFIX while `OK` was exact-or-`OK (`,
    # so `FAILED to cleanup` could steal where `OK to cleanup` could not.
    # [[feedback-generalize-fixes]] [[feedback-blind-fixture-green-gate]]
    def _is_result(s):
        return s in ("OK", "FAILED") or s.startswith("OK (") or s.startswith("FAILED (")
    _lines = (r.stdout or b"").decode("utf-8", "replace").strip().splitlines()
    _last = _lines[-1].strip() if _lines else ""
    _ran, _res, _ran_i = "", "", -1
    for _i in range(len(_lines) - 1, -1, -1):
        _s = _lines[_i].strip()
        if _s.startswith("Ran ") and " test" in _s:
            _ran, _ran_i = _s, _i
            break
    if _ran_i >= 0:
        for _l in _lines[_ran_i + 1:]:
            _s = _l.strip()
            if _is_result(_s):
                _res = _s
                break
    _parts = [_p for _p in (_ran, _res) if _p]
    if _last and _last not in _parts:
        _parts.append(_last)
    return r.returncode == 0, (" | ".join(_parts) if _parts else _last)


# ── the proving loop ─────────────────────────────────────────────────────────────────────────
def prove(only=None, say=print):
    gates = gate_files()
    todo = [(n, f) for n, f in gates if (not only or n in only or f in only)]
    with_proofs = [(n, f, red_proofs_in(f)) for n, f in todo]
    have = [(n, f, p) for n, f, p in with_proofs if p]
    say("  %d gate(s) in scope · %d declare a red-proof · %d do not"
        % (len(todo), len(have), len(todo) - len(have)))
    if not have:
        say("  nothing to prove. That is the BACKLOG, not a clean bill of health.")
        return {}
    sandbox, root = make_sandbox(say)
    if not sandbox:
        return {}
    say("  sandbox: %s" % sandbox)
    results = {}
    try:
        for name, filename, proofs in have:
            verdicts = []
            for i, pr in enumerate(proofs):
                v = _prove_one(sandbox, name, filename, pr, i, say)
                verdicts.append(v)
            results[name] = (BLIND if BLIND in verdicts
                             else INVALID if INVALID in verdicts
                             else UNPROVABLE if UNPROVABLE in verdicts
                             else PROVEN)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    _write_state(results)
    return results


def _write_state(results):
    """⚠ THE JOIN. Without this the whole loop is plumbing with no tap: `--prove` would measure
    beautifully and `_heart2_census()` in control_app.py would read an absent file and report
    UNKNOWN for ever, so the heart could never carry what the proving loop learned. This repo's
    single most repeated defect is two halves each built right and never joined.
    [[the-unjoined-end]] [[plumbing-with-no-tap]]"""
    gates = gate_files()
    have = [n for n, f in gates if red_proofs_in(f)]
    blind = sorted(n for n, v in (results or {}).items() if v in (BLIND, INVALID))
    # ⚠⚠ AN UNREADABLE STATE FILE IS NOT AN EMPTY ONE, AND THE DIFFERENCE IS THE WHOLE CENSUS.
    # This used to swallow a parse failure into `prior = {}`, which the merge below then treats as
    # "nothing was ever proven" — silently erasing `provedGates` and the `blind` list and writing
    # the wipe back over the only copy. Caught by tv/swallow_census.py (RANK 1: a failed read
    # handed back as DATA), which is this repo's own unknown-stays-unknown law mechanised.
    # A file that will not parse is a REFUSAL to write: the accumulated record survives, and the
    # next run says why. Losing the ledger is far worse than not updating it.
    # [[unknown-stays-unknown]] [[feedback-suspect-the-instrument]]
    prior = {}
    if os.path.exists(STATE):
        try:
            with io.open(STATE, encoding="utf-8") as fh:
                prior = json.load(fh)
        except Exception as _e:
            print("  ⚠ %s exists but would not parse (%s) — REFUSING to write, because merging "
                  "from an empty prior would erase every standing proof. Fix or remove the file."
                  % (os.path.basename(STATE), type(_e).__name__))
            return
    # ⚠⚠ MERGE, NEVER CLOBBER — and say when the run was PARTIAL. Two ways this erased real
    # findings: `--prove NAME` produced a one-gate `results` and rewrote the global `blind` list
    # from it, so checking one fix deleted every blind instrument the last full run found; and
    # `--ratchet` wrote a two-key dict that dropped `blind` entirely, flipping a DARK heart back
    # to WATCHED. A supervision layer that forgets its own findings is worse than one that never
    # made them. Partial runs now keep the prior blind list and mark themselves.
    _partial = bool(results) and len(results) < len(have)
    out = dict(prior)
    if _partial:
        _keep = [b for b in (prior.get("blind") or []) if b not in (results or {})]
        blind = sorted(set(blind) | set(_keep))
    # ⚠⚠ v2829 — A BLIND NAME MUST LEAVE WHEN ITS PROOF DOES, and it did not. The merge above keeps
    # a prior blind entry that this run did not re-test, which is right for a partial run — but it
    # never asked whether the gate still DECLARES a proof at all. #52's own workflow deletes a
    # RED_PROOF block whose tampers came back BLIND, precisely because a proof that survives its
    # own defeat is counted as coverage. Those five gates then sat in `blind` forever, so the heart
    # reported DARK over instruments that no longer claim anything. Measured 2026-09-09: blind 5,
    # every one a block that had just been removed.
    # This is the same defect `provedGates` had and was fixed for, in the neighbouring key.
    # [[label-outlived-referent]] [[the-unjoined-end]]
    blind = sorted(set(blind) & set(have))
    # ⚠⚠ `proved` IS DERIVED FROM A NAMED SET, NOT COUNTED PER RUN — AND THE MERGE ABOVE DID NOT
    # COVER IT. The comment beside it says "MERGE, NEVER CLOBBER" and then `proved` was recomputed
    # from THIS run's results alone, so `--prove ONE_GATE` rewrote the total from 20 to 1.
    # Measured 2026-09-09: proving a single new gate dropped the census to `proved: 1` while 20
    # gates were standing proven, and #52 is worked in exactly that batch-by-batch way — so the
    # one number he watches would have walked backwards every time progress was made.
    # A set of NAMES is the right model: partial runs accumulate, a gate that goes BLIND leaves,
    # and a gate whose file is gone leaves too. A COUNT cannot express any of that.
    _known = {n for n, _f in gates}
    _proved = set(prior.get("provedGates") or []) if _partial else set()
    for _n, _v in (results or {}).items():
        if _v == PROVEN:
            _proved.add(_n)
        else:
            _proved.discard(_n)          # BLIND/INVALID/UNPROVABLE revokes a standing proof
    _proved &= _known                    # a gate that no longer exists is not proven
    _pixel_unk = []
    _pixel = pixel_gates(gates, _pixel_unk)   # v2858 — by imports, not by grep
    # ⚠⚠ v2847 — EVERY VERDICT CARRIES ITS OWN AGE, BECAUSE ONE `ranAt` FOR THE WHOLE FILE IS A
    # DATE ON THE FETCH AND NOT ON THE THING. The merge above deliberately keeps a prior blind
    # entry the current run did not re-test — correct, and until now indistinguishable from one
    # measured seconds ago. MEASURED 2026-09-09: the file said `blind: 4` and `partial: true`, I
    # reported four blind instruments, and a re-prove returned **three of them PROVEN**. Their
    # verdicts had been carried forward across partial runs since before the fixes that closed
    # them, and nothing in the record could say so.
    #
    # `verdictAt` stamps each gate the run actually tested, so a reader can subtract: a blind name
    # with a fresh stamp is a live defect, a blind name with an old one is a claim nobody has
    # rechecked. Kept entries simply keep their old stamp — which is the point.
    # [[stale-reading]] [[inherited-claim-is-not-evidence]] [[unknown-stays-unknown]]
    _now_ms = int(__import__("time").time() * 1000)
    _seen = dict(prior.get("verdictAt") or {})
    for _n in (results or {}):
        _seen[_n] = _now_ms
    _seen = {k: v for k, v in _seen.items() if k in _known}   # a gate that is gone keeps no stamp
    out.update({
        "proved": len(_proved),
        "provedGates": sorted(_proved),
        # v2858 — THE SPLIT, because one number hid a 93/7 one. See pixel_gates().
        "pixelTotal": len(_pixel),
        "pixelProved": len(_proved & _pixel),
        "pixelUnclassified": sorted(_pixel_unk),   # v2860 — NOT silently counted as backend
        "gatesFingerprint": gates_fingerprint(gates),   # v2862 — content, not mtime
        "backendTotal": len(gates) - len(_pixel) - len(_pixel_unk),
        # ⚠⚠ v2862 — MINUS THE UNCLASSIFIED TOO, or these two disagree. A cross-family review
        # found it: a gate that is PROVED and is now unreadable leaves backendTotal (which
        # subtracts _pixel_unk) but stays in backendProved (which did not), so backendProved
        # could exceed backendTotal. Zero unclassified today, so it has never fired — a
        # latent inconsistency in the one number he reads is exactly the kind that ships.
        "backendProved": len(_proved - _pixel - set(_pixel_unk)),
        "surfaces": surface_verdict(),   # v2859 — the PIXEL side, from the render run itself
        "declared": len(have),
        "unproven": len(gates) - len(have),
        "total": len(gates),
        "blind": blind,
        "blindUnchecked": sorted(b for b in blind if b not in (results or {})),
        "partial": _partial,
        "verdictAt": _seen,
        "ranAt": _now_ms,
    })
    with io.open(STATE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)


def resolve_proof_target(base, rel):
    """Where a RED_PROOF's `file` actually lives. -> str

    tv/ first, then the repo root one level up — because 59 of 259 gates name `bible.html`, which
    sits at the root, and resolving it only against tv/ made 23% of the suite UNPROVABLE for want
    of a path (v2821).

    ⚠⚠ IT IS A FUNCTION BECAUSE THE SECOND COPY OF THIS RULE WENT STALE. v2821 fixed the resolution
    inside `_prove_one` and left `test_the_heart_can_see_its_own_instruments` joining against tv/
    only — so the engine could apply a proof that its own well-formedness law called malformed.
    MEASURED on CI: 8 red-proofs reported as "names a file that does not exist: 'bible.html'",
    every one of them applyable and correct. Two resolvers for one question, one of them fixed.
    [[copy-drift]] [[feedback-contradiction-is-the-finding]]
    """
    tgt = os.path.join(base, rel)
    if rel and not os.path.exists(tgt):
        alt = os.path.join(os.path.dirname(os.path.abspath(base)), rel)
        if os.path.exists(alt):
            return alt
    return tgt


def gate_spec(name):
    """The registered gate's argv tail, timeout and -c script. -> ([extra], timeout, script|None)

    ⚠⚠ v2887 — REG-856 WAS FIXED IN triage() AND NOT IN prove(), AND THE BUG ENTRY SAID SO.
    It recorded "prove() calls the same _run_gate" as a known consequence and then threaded the
    spec through only the new command. MEASURED two versions later, proving 47 gates:
        js-syntax             UNPROVABLE — clean run: timed out after 180s   (registered: 300s)
        corroborate-selftest  UNPROVABLE — ALREADY RED untampered            (registered: --selftest)
    Both are the dropped spec, not the gates. A fix applied to one of two call sites is a fix that
    has not been generalised, and naming the second site in prose is not the same as covering it.
    [[feedback-generalize-fixes]] [[the-unjoined-end]]
    """
    try:
        import run_gates as _rg
    except Exception:
        return [], 180, None
    for g in getattr(_rg, "GATES", []):
        if getattr(g, "name", None) == name:
            argv = list(getattr(g, "argv", []) or [])
            # ⚠⚠ v2888 — `-c` IS NOT A FILE, AND argv[2:] IS ITS SCRIPT BODY.
            # hover-wilson registers as [python, "-c", <2.4KB verdict script>, <abs path>]. The
            # blanket argv[2:] handed that whole script back as an ARGUMENT, so the proof ran
            # `python3 <sandbox>/hover_wilson.py "<script text>" "<REAL tree path>"` — i.e. the
            # module's own main() instead of the gate, pointed at UNTAMPERED source. It reported
            # BLIND, and BLIND was the honest verdict: nothing the tamper touched was ever
            # executed. Measured 2026-09-10: 1 of 281 gates uses -c, and 1 of 281 forwards an
            # absolute real-tree path — the same one. [[the-unjoined-end]] [[source-reading-guard]]
            if len(argv) > 2 and argv[1] == "-c":
                return [a for a in argv[3:] if isinstance(a, str)], getattr(g, "timeout", 180), argv[2]
            return [a for a in argv[2:] if isinstance(a, str)], getattr(g, "timeout", 180), None
    return [], 180, None


def _prove_one(sandbox, name, filename, pr, idx, say):
    tgt_rel = str(pr.get("file") or "")
    # ⚠⚠ v2821 — RESOLVE AGAINST tv/ FIRST, THEN THE REPO COPY'S ROOT.
    # `sandbox` is the copied tv/ directory, so a proof naming "bible.html" resolved to
    # <sandbox>/tv/bible.html and came back UNPROVABLE — while the file sits one level up at the
    # repo root. MEASURED: 59 of 259 gates read bible.html, so 23% of the suite could never prove
    # itself for want of a path.
    #
    # ⚠ THE CONTAINMENT CHECK IS WIDENED TO THE REPO COPY, NOT WEAKENED. It still refuses anything
    # resolving outside the throwaway copy — an absolute path, or ../.. climbing to the real tree.
    # tv/ is inside the repo copy, so every previously-legal target stays legal and nothing new is
    # reachable except files the copy itself contains.
    _repo_copy = os.path.dirname(os.path.abspath(sandbox))
    tgt = resolve_proof_target(sandbox, tgt_rel)
    # ⚠⚠⚠ THE SANDBOX WAS A CLAIM, NOT A FACT. os.path.join DISCARDS its prefix when the second
    # argument is absolute, and normalises `..` straight out of the tree:
    #     join(sandbox, "control_app.py")           -> <sandbox>/control_app.py
    #     join(sandbox, "/Users/.../control_app.py")-> /Users/.../control_app.py   ESCAPED
    #     join(sandbox, "../../BUGS.md")            -> /tmp/BUGS.md                ESCAPED
    # So one RED_PROOF written with an absolute path — a natural copy-paste out of an error
    # message — and this function TRUNCATES AND REWRITES a file in his real tree. The restore
    # lives in a `finally`; a SIGKILL or the 10-minute push ceiling (three recorded kills in this
    # repo) would leave the defect in place, and his console execs the working tree, so it would
    # be live on screen. The docstring said "the ORIGINAL tree must never be touched" and nothing
    # enforced it. Found by a cross-family review of the shipped bytes.
    # [[unknown-stays-unknown]] [[feedback-blind-fixture-green-gate]]
    try:
        _root = os.path.realpath(_repo_copy)
        _real = os.path.realpath(tgt)
        _contained = (os.path.commonpath([_root, _real]) == _root)
    except Exception:
        # ⚠ THE DEFAULT *IS* THE FAILURE HERE, DELIBERATELY — and swallow_census asks that such a
        # site say so in a comment rather than be silently exempt. If the path cannot be resolved
        # at all, the honest answer is "not proven to be inside the sandbox", and the only safe
        # action on that is to REFUSE this one tamper. Raising would abort the whole proving run
        # over a single unresolvable target. [[unknown-stays-unknown]]
        _contained = False
    if not _contained:
        say("     %-52s %s — %r resolves OUTSIDE the sandbox (%s). REFUSED: a proof may only "
            "tamper inside the copy." % ("%s[%d]" % (name, idx), INVALID, tgt_rel, _real))
        return INVALID
    find, repl = str(pr.get("find") or ""), str(pr.get("replace") or "")
    want = int(pr.get("matches") or 1)
    label = "%s[%d]" % (name, idx)

    if not tgt_rel or not os.path.exists(tgt):
        say("     %-52s %s — %s is not in the sandbox" % (label, UNPROVABLE, tgt_rel or "(no file)"))
        return UNPROVABLE

    # 1. CLEAN RUN. A gate that is already red in the sandbox can prove nothing.
    _extra, _to, _script = gate_spec(name)
    ok_clean, tail = _run_gate(sandbox, filename, timeout=_to, extra=_extra, script=_script)
    if ok_clean is None:
        say("     %-52s %s — clean run: %s" % (label, UNPROVABLE, tail))
        return UNPROVABLE
    if not ok_clean:
        say("     %-52s %s — it is ALREADY RED untampered in the sandbox (%s)"
            % (label, UNPROVABLE, tail[:60]))
        return UNPROVABLE

    with io.open(tgt, encoding="utf-8") as fh:
        original = fh.read()
    got = original.count(find) if find else 0
    if got != want:
        # THE CARVED SCAR: a green sabotage is usually the sabotage's fault. Print the count.
        say("     %-52s %s — the tamper matched %d time(s), expected %d. The SABOTAGE is wrong, "
            "not the law." % (label, INVALID, got, want))
        return INVALID

    # 2. TAMPER
    _tampered = original.replace(find, repl, want)
    # ⚠⚠ A NON-ZERO EXIT IS NOT PROOF THE LAW FIRED. `_run_gate` reduces the tampered run to
    # `returncode == 0`, so a SyntaxError or ImportError the tamper introduced would be credited
    # as "the law caught the defect" — the gate would be praised for a crash it never inspected.
    # A tamper that does not even parse cannot be evidence about anything. Checked for python
    # only; html has no cheap equivalent and is left as a known limit rather than a false claim.
    if tgt_rel.endswith(".py"):
        import ast as _ast
        try:
            _ast.parse(_tampered)
        except SyntaxError as _se:
            say("     %-52s %s — the tamper does not parse (%s). A gate reddened by a "
                "SyntaxError proves nothing about the law."
                % ("%s[%d]" % (name, idx), INVALID, str(_se)[:60]))
            return INVALID
    with io.open(tgt, "w", encoding="utf-8") as fh:
        fh.write(_tampered)
    try:
        ok_tampered, tail2 = _run_gate(sandbox, filename, timeout=_to, extra=_extra, script=_script)
    finally:
        with io.open(tgt, "w", encoding="utf-8") as fh:
            fh.write(original)

    if ok_tampered is None:
        say("     %-52s %s — tampered run: %s" % (label, UNPROVABLE, tail2))
        return UNPROVABLE
    if ok_tampered:
        say("     %-52s %s ← %s" % (label, BLIND, blind_reason(pr.get("why"), got, tail2)))
        return BLIND
    say("     %-52s %s (%d match(es) tampered → red)" % (label, PROVEN, got))
    return PROVEN


# ── the census ───────────────────────────────────────────────────────────────────────────────
def report(say=print):
    gates = gate_files()
    have, missing = [], []
    for n, f in gates:
        (have if red_proofs_in(f) else missing).append((n, f))
    total = len(gates)
    say("♥ HEART 2.0 — can my own instruments still go red?")
    say("")
    say("    gates with a python file         %4d" % total)
    say("    declare an executable red-proof  %4d   (%.1f%%)"
        % (len(have), (100.0 * len(have) / total) if total else 0.0))
    say("    no proof — UNKNOWN, not clean    %4d" % len(missing))
    say("")
    if have:
        say("  proofs declared by:")
        for n, f in have:
            say("    · %s" % n)
    # ⚠⚠ v2853 — `len(have)` IS "DECLARES A PROOF", AND IT WAS RETURNED UNDER THE KEY `proved`.
    # Those are different questions and the whole of #52 is the gap between them: a gate can declare
    # a RED_PROOF that has never been executed, or one that came back BLIND, and this key called
    # both of them proven. MEASURED 2026-09-09: report() said proved=98 while 97 gates had actually
    # been tampered red — and `--ratchet` wrote that 98 into the census as the verified count.
    # The printed line above has always said "declare an executable red-proof". The KEY now agrees
    # with it. A verified count lives in `.heart2.json` under `provedGates`, written only by prove().
    # [[label-outlived-referent]] [[the-unjoined-end]]
    return {"total": total, "declared": len(have), "unproven": len(missing),
            "unprovenNames": [n for n, _ in missing]}


# ── the detector ─────────────────────────────────────────────────────────────────────────────
# Signatures of defects this repo has actually paid for. A detector that re-reports covered ground
# is noise, and noise is how a real finding gets scrolled past — so anything a gate already covers
# is DROPPED, not listed.
SIGNATURES = [
    ("fixed-size source window",
     re.compile(r"\[\s*\w+\s*:\s*\w+\s*\+\s*\d{2,}\s*\]"),
     "src[i:i+N] past the region reads as ABSENT — anchor both ends"),
    ("bare except that swallows a verdict",
     re.compile(r"except\s*:\s*\n\s*pass"),
     "a swallowed exception is UNKNOWN reported as fine"),
    ("open for write before the value exists",
     re.compile(r"open\(([^)]+),\s*[\"']w[\"']\)\.write\("),
     "open(p,'w').write(f()) empties p BEFORE f() runs"),
    # ⚠ BOTH FORMS, OR THE SIGNATURE ONLY SEES HALF THE REPO. Written first as `pkill\s+-f`,
    # which matches the shell string `pkill -f x` and MISSES `subprocess.run(["pkill", "-f", x])`
    # — and the argv list is how this repo actually spawns things. A signature that only knows one
    # spelling reports a clean file and means "I looked for the other one".
    ("cp -R of the repo or tv/",
     re.compile(r"""\bcp\b[^\n]{0,14}-R\b[^\n]{0,40}\b(tv|repo)\b"""),
     "tv/ holds 5.8 GB of footage; this caused an ENOSPC"),
    ("pkill by pattern",
     re.compile(r"""\bpkill\b[^\n]{0,14}-f\b"""),
     "cannot tell his process from mine — kill by port or PID"),
]


def _code_only(src):
    """Source with comments and DOCSTRINGS blanked out, everything else byte-for-byte. -> str

    ⚠⚠ THIS FUNCTION HAS BEEN WRONG TWICE, IN OPPOSITE DIRECTIONS, AND BOTH TIMES IT PRODUCED A
    CONFIDENT GREEN.

    First cut GREPPED RAW TEXT and returned ten hits, every one prose — it flagged safe_copy.py for
    "cp -R of the repo", a phrase that only appears in the docstring explaining why cp -R is
    forbidden, and it flagged THIS FILE twice for the comments warning against the very patterns it
    hunts. A detector whose findings are its own warnings is pure noise.

    Second cut over-corrected: it rebuilt the source by joining tokens with "\n" and dropped every
    STRING. That broke the detector in a way its own output could not show. MEASURED against a file
    containing a real `open(p, "w").write(g())`:

        raw text                    the open-for-write signature matches 1
        after the token rebuild     matches 0

    because the source became `open\n(\np\n,\n)\n.\nwrite\n(` — adjacency destroyed, and the
    `"w"` literal deleted outright. THREE of the five signatures were structurally dead:
    `open(...,'w').write(`, `pkill -f` and `cp -R ...` all live inside string literals or
    subprocess argument lists, which is precisely what it was deleting. So "no uncovered signature
    found — a measurement over 5 signature(s)" was a green produced by the instrument, not by the
    code: the exact failure this file exists to catch, inside the file that catches it.

    THE FIX IS TO BLANK, NOT TO REBUILD. Comment and docstring spans are overwritten with spaces
    (newlines kept), so every other byte stays where it was: adjacency holds, string literals
    survive, and prose still cannot match. [[source-reading-guard]] [[feedback-comments-vs-code]]
    """
    import tokenize
    import ast as _ast
    try:
        lines = src.splitlines(keepends=True)
        offsets, run = [], 0
        for ln in lines:
            offsets.append(run)
            run += len(ln)

        def _pos(row, col):
            return offsets[row - 1] + col if 0 < row <= len(offsets) else None

        spans = []
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                a, b = _pos(*tok.start), _pos(*tok.end)
                if a is not None and b is not None:
                    spans.append((a, b))
        # docstrings: a bare string expression at the head of a module, class or function
        tree = _ast.parse(src)
        for node in _ast.walk(tree):
            if not isinstance(node, (_ast.Module, _ast.ClassDef,
                                     _ast.FunctionDef, _ast.AsyncFunctionDef)):
                continue
            body = getattr(node, "body", None) or []
            if not body:
                continue
            first = body[0]
            if isinstance(first, _ast.Expr) and isinstance(first.value, _ast.Constant) \
               and isinstance(first.value.value, str):
                a = _pos(first.lineno, first.col_offset)
                b = _pos(first.end_lineno, first.end_col_offset)
                if a is not None and b is not None:
                    spans.append((a, b))
    except Exception:
        # ⚠⚠ None, NOT "". The comment below was right and the VALUE contradicted it. Caught by
        # tv/swallow_census.py (RANK 1: a failed read handed back as DATA) — this repo's own
        # unknown-stays-unknown law mechanised, catching it in the DETECTOR.
        # The caller does `src = _code_only(src)` and runs the signature regexes over the result.
        # An empty string yields ZERO hits, so a file that will not parse reads as a CLEAN file:
        # the exact defect this scanner exists to find, inside the scanner.
        # [[unknown-stays-unknown]] [[feedback-suspect-the-instrument]]
        return None
    out = list(src)
    for a, b in spans:
        for i in range(max(0, a), min(len(out), b)):
            if out[i] != "\n":
                out[i] = " "
    return "".join(out)


def detect(say=print):
    covered = set()
    for n, f in gate_files():
        covered.add(f)
    hits = []
    unscanned = []
    for fn in sorted(os.listdir(HERE)):
        if not fn.endswith(".py") or fn in covered:
            continue
        p = os.path.join(HERE, fn)
        try:
            with io.open(p, encoding="utf-8") as fh:
                src = fh.read()
        except Exception:
            continue
        src = _code_only(src)
        if src is None:
            unscanned.append(fn)          # UNSCANNED is not CLEAN
            continue
        for label, rx, why in SIGNATURES:
            n_hits = len(rx.findall(src))
            if n_hits:
                hits.append((fn, label, n_hits, why))
    say("  scanned %d file(s) outside the gate set" % (len(os.listdir(HERE))))
    if unscanned:
        say("  ⚠ %d file(s) could not be parsed and were NOT scanned — UNKNOWN, not clean: %s"
            % (len(unscanned), ", ".join(sorted(unscanned)[:6])))
    if not hits:
        say("  no uncovered signature found. That is a measurement over %d signature(s), "
            "not a claim that nothing is wrong." % len(SIGNATURES))
    for fn, label, n_hits, why in hits:
        say("    %-34s %-30s x%-3d %s" % (fn, label, n_hits, why))
    return hits


# ── propose, never apply ─────────────────────────────────────────────────────────────────────
def propose(results, census, hits):
    """Write what a person should do. Never touch a guard. [[achilles-self-carving-system]]"""
    lines = ["# ♥ HEART 2.0 — proposals", "",
             "Written by `tv/heart2.py`. **It proposes; it never edits a guard.**", ""]
    blind = [n for n, v in (results or {}).items() if v == BLIND]
    invalid = [n for n, v in (results or {}).items() if v == INVALID]
    if blind:
        lines += ["## BLIND — survived its own defeat", ""]
        # ⚠ v2870 — AND IT MUST NOT CONTRADICT THE PROVE OUTPUT. Same review: after blind_reason
        # split "the law is weak" from "the laws never ran", stdout said one thing and this file
        # said the other about the same verdict — two writers, opposite jobs. It cannot re-run the
        # gate, so it names BOTH causes in the order the reader should check them, and points at
        # the line that already knows which. [[copy-drift]] [[the-unjoined-end]]
        # ⚠⚠ v2872 — THREE STATES, NOT TWO. v2870 stopped this contradicting the prove output and
        # then wrote an EXCLUSIVE sentence — "if it reports SKIPPED, the skip is the job,
        # OTHERWISE the law reads prose" — which is false for the case blind_reason exists to name:
        # five laws skipping while three RUN and stay green is BOTH jobs. The reader saw the word
        # SKIPPED and stopped at "fix the skip", which is the v2868 misdirection this was supposed
        # to close, left standing in the writer that cannot re-run the gate. [[copy-drift]]
        lines += ["- `%s` — the tamper reintroduced the defect and the gate stayed GREEN. Read the "
                  "`--prove` line for this gate; it reports one of three states. ALL laws skipped: "
                  "the tamper was never judged, fix the SKIP. SOME skipped: the laws that ran are "
                  "weak AND others opted out — both jobs. No skips: the law reads prose instead of "
                  "code, or asserts something the tamper does not touch." % n for n in blind] + [""]
    if invalid:
        lines += ["## INVALID PROOF — the sabotage, not the law", ""]
        lines += ["- `%s` — the tamper did not match the expected count. A sabotage that changes "
                  "nothing proves nothing." % n for n in invalid] + [""]
    if census.get("unproven"):
        lines += ["## UNPROVEN — the backlog (UNKNOWN, not clean)", "",
                  "%d gate(s) declare no executable red-proof. Each was proven red once, by hand, "
                  "and that proof survives only as prose." % census["unproven"], ""]
        # ⚠⚠ v2818 — A LIST OF NAMES IS A BACKLOG, NOT A PROPOSAL, AND THAT IS WHY 242 NEVER MOVED.
        # This wrote "these 242 gates declare no red-proof" and called it proposing. Every one of
        # them still required a person to re-derive by hand the sabotage the gate's OWN assertions
        # already state: a law that says assertIn("X", src_of_Y) IS the sabotage — remove X from Y
        # and it must go red. That derivation is mechanical, and leaving it manual is the whole
        # reason the number sat still while the engine around it worked.
        #
        # It still PROPOSES and never applies. What changed is that a proposal is now something a
        # person can paste, PRE-MEASURED: the anchor is counted in the real target file and only
        # an unambiguous one (exactly one occurrence) is offered. [[achilles-self-carving-system]]
        try:
            import heart2_candidates as _hc
        except Exception as _e:
            _hc = None
            lines += ["_(the candidate deriver could not be imported: %s)_" % type(_e).__name__, ""]
        _yield, _why_counts = 0, {}
        for n in census.get("unprovenNames", []):
            _f = None
            for _gn, _gf in gate_files():
                if _gn == n:
                    _f = _gf
                    break
            if _hc is None or not _f:
                lines.append("- `%s`" % n)
                continue
            _p, _status, _note = _hc.candidates_for(os.path.join(HERE, _f))
            _why_counts[_status] = _why_counts.get(_status, 0) + 1
            if _p:
                _yield += 1
                lines += ["", "### `%s`" % n, "", "```python", _hc.render_block(n, _p).strip(),
                          "```", ""]
            else:
                lines.append("- `%s` — no candidate: %s" % (n, _note))
        # ⚠ THE DENOMINATOR, ALWAYS. A proposals file that lists only what it managed to derive
        # would read as "this is the work", when the undeliverable remainder is also the work.
        lines += ["", "**%d of %d unproven gates yielded a pre-measured candidate.** The rest are "
                  "named above with the reason: %s" % (_yield, census.get("unproven"),
                  ", ".join("%s=%d" % kv for kv in sorted(_why_counts.items()))), ""]
    if hits:
        lines += ["## UNCOVERED SIGNATURES", ""]
        lines += ["- `%s` — %s x%d — %s" % (f, l, n, w) for f, l, n, w in hits] + [""]
    with io.open(PROPOSALS, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return PROPOSALS


def triage(say=print):
    """Split the gates that carry NO red-proof into 'writable' and 'not provable here'.

    ⚠⚠ THE CENSUS COUNTED TWO DIFFERENT THINGS AS ONE. `proved / total` leaves a remainder, and
    every gate in it was reported the same way: unproven. But that remainder holds two populations
    that mean opposite things —

      • a gate nobody has written a sabotage for yet   -> WRITABLE, the number is a to-do list
      • a gate that CANNOT go red in this sandbox      -> a ceiling, and no amount of work moves it

    MEASURED 2026-09-10: `test_tasks_ships_are_recorded` is green on his Mac and red the moment it
    runs in a sandbox, because `safe_copy` copies files and not `.git`, so the gate's own subject
    ("git named 0 shipped versions; 12 are needed") cannot exist there. Writing a red-proof for it
    would have produced UNPROVABLE — work spent to learn something the census could have told me.

    A gate with no proof is never RUN by --prove, so nothing ever discovers which population it is
    in. This runs each one untampered, once, and asks. That is a measurement, not a heuristic: the
    first attempt at this counted `git` mentions with a regex, which would have put a gate that
    merely says the word git in the wrong column. [[unknown-stays-unknown]]
    [[zero-needs-a-denominator]] [[feedback-suspect-the-instrument]]
    """
    files = gate_files()
    todo = [(n, f) for n, f in files if not red_proofs_in(f)]
    say("")
    say("  %d gate(s) carry no red-proof — running each untampered to see which COULD be proven"
        % len(todo))
    # ⚠ make_sandbox RETURNS (tv_dir, root) — the FIRST element is already the tv/ directory,
    # which is why prove() hands it straight to _run_gate. Joining "tv" onto it again produced
    # TypeError on a tuple. Mirrored from prove()'s own two lines rather than guessed a second time.
    sandbox, _root = make_sandbox(say)
    if not sandbox:
        say("  no sandbox — the split is UNKNOWN, not empty")
        return {"writable": [], "unprovable": [], "why": "no sandbox"}
    # ⚠⚠ RUN THE GATE THE WAY THE SUITE RUNS IT, OR THE VERDICT IS ABOUT A COMMAND NOBODY ISSUES.
    # The first cut called _run_gate(sandbox, filename), which builds [python3, <file>] — dropping
    # the gate's ARGV TAIL and ignoring its registered TIMEOUT. Measured: 3 of the 8 gates this
    # reported as "not provable" were my own instrument.
    #   corroborate-selftest  real argv ends in `--selftest`; without it the LIVE corroboration ran
    #                         and reported real disagreements. With it: exit 0, "🟢 every invariant
    #                         can both hold and refuse".
    #   js-syntax (300s), test_control (900s)  — given _run_gate's 180s default, both timed out and
    #                         a timeout was filed as a property of the gate rather than of the clock.
    # [[feedback-suspect-the-instrument]] [[zero-needs-a-denominator]]
    writable, unprovable = [], []
    for name, fn_ in todo:
        _tail, _to, _scr = gate_spec(name)    # ONE reader, shared with _prove_one
        ok, out = _run_gate(sandbox, fn_, timeout=_to, extra=_tail, script=_scr)
        (writable if ok else unprovable).append((name, (out or "").strip().splitlines()[-1][:70]
                                                 if out else ""))
    say("  WRITABLE      %3d — green in the sandbox, so a sabotage would mean something" % len(writable))
    say("  NOT PROVABLE  %3d — already red untampered; a red-proof here can only say UNPROVABLE"
        % len(unprovable))
    for n, why in unprovable[:12]:
        say("     %-46s %s" % (n[:46], why))
    if len(unprovable) > 12:
        say("     ... and %d more" % (len(unprovable) - 12))
    return {"writable": [n for n, _ in writable], "unprovable": [n for n, _ in unprovable]}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--prove", nargs="*", default=None)
    ap.add_argument("--detect", action="store_true")
    ap.add_argument("--ratchet", action="store_true")
    ap.add_argument("--triage", action="store_true",
                    help="split the no-red-proof gates into WRITABLE vs NOT PROVABLE HERE")
    a = ap.parse_args(argv)
    if a.triage:
        triage()
        return 0
    if not any([a.report, a.prove is not None, a.detect, a.ratchet]):
        a.report = True

    census, results, hits = {}, {}, []
    if a.report or a.ratchet:
        census = report()
    if a.prove is not None:
        print("")
        results = prove(only=set(a.prove) or None)
    if a.detect:
        print("")
        hits = detect()
    if census or results or hits:
        p = propose(results, census, hits)
        print("\n  proposals written to %s (it never edits a guard)" % os.path.relpath(p, REPO))

    if a.ratchet:
        # ⚠ SAME RULE AS _write_state: an unreadable ledger is UNKNOWN, not an empty one. The
        # ratchet compares against `prev`; reading a broken file as {} would make every gate look
        # newly proven and the comparison meaningless. [[unknown-stays-unknown]]
        prev = {}
        if os.path.exists(STATE):
            try:
                with io.open(STATE, encoding="utf-8") as fh:
                    prev = json.load(fh)
            except Exception as _e:
                print("  ⚠ %s exists but would not parse (%s) — the ratchet has nothing to compare "
                      "against, so it reports UNKNOWN rather than a clean run."
                      % (os.path.basename(STATE), type(_e).__name__))
                return 2
        # ⚠⚠ A BROKEN PARSER MUST NOT PRODUCE A GREEN LOCK. If run_gates will not import,
        # gate_files() returns [] and the census reads total=0, unproven=0 — which sails past the
        # ratchet AND writes a baseline of 0 that every honest run afterwards fails forever, so
        # the fix would look like the regression. This is the same zero-with-no-denominator the
        # file already recorded making once, one function along. [[zero-needs-a-denominator]]
        if int(census.get("total") or 0) < 100:
            print("\n  ✗ RATCHET REFUSED: the census found %s gate(s). run_gates registers "
                  "hundreds, so this is the parser failing, not a clean tree. UNKNOWN is not a "
                  "pass, and a baseline written from it would poison every later run."
                  % census.get("total"))
            return 1
        base = int(prev.get("unproven", 10 ** 9))
        now = int(census.get("unproven", 0))
        if now > base:
            print("\n  ✗ RATCHET: unproven went %d → %d. A new gate must arrive with its proof."
                  % (base, now))
            return 1
        # ⚠⚠ v2853 — THIS WROTE A TWO-KEY DICT OVER THE WHOLE CENSUS, AND THE SCAR ABOVE SAYS SO
        # ALREADY: "`--ratchet` wrote a two-key dict that dropped `blind` entirely, flipping a DARK
        # heart back to WATCHED". That was fixed in the prove path and left standing HERE.
        # MEASURED 2026-09-09 in a sandbox, with a baseline loose enough for the ratchet to pass:
        #     keys 10 -> 2 · provedGates 97 -> 0 · verdictAt 45 -> 0 · blind/declared/partial gone
        #     proved 97 -> 98, the verified count replaced by the DECLARATION count
        # One --ratchet erased every proof the heart had ever banked. MERGE, NEVER CLOBBER — and do
        # not write `proved` from the census at all, because report() counts declarations.
        # [[the-unjoined-end]] [[label-outlived-referent]]
        _out = dict(prev)
        _out["unproven"] = now
        with io.open(STATE, "w", encoding="utf-8") as fh:
            json.dump(_out, fh)
        print("\n  ✓ RATCHET: unproven %d (was %s)" % (now, base if base < 10 ** 9 else "unset"))
    if results and BLIND in results.values():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
