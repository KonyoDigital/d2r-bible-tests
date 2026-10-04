#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""♥♥ HEART 2.0 — the instruments watch themselves.

    python3 tv/heart2.py --report      the census: proven · blind · unproven · unprovable
    python3 tv/heart2.py --prove       re-tamper every guard that declares a proof, in a SANDBOX
    python3 tv/heart2.py --prove NAME  just this one
    python3 tv/heart2.py --prove NAMES --push
                                       what hooks/pre-push runs (#42): a proof that declares "widths" runs its clean
                                       AND tampered runs only at those viewports; the proofs likeliest to fail run
                                       first and the run STOPS at the first BLIND / INVALID / clean-run red; a gate
                                       that starts a browser is proved one at a time, whatever the lane count; and
                                       (P3) a PROVEN is reused from tv/.heart2_cache.json when every byte it depends
                                       on is identical - HEART2_PROVE_CACHE=0 runs everything
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
import threading

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
#: REG-1686 — a red-proof whose tamper can only be judged on a PC that HAS something (`"needs": "<capability>"`) is
#: ELSEWHERE on a PC without it: measured where the thing is, never BLIND here. MEASURED 2026-10-01: his ALT (no local
#: D2R install - it plays through a cloud client) filed test_the_character_builder_is_their_builder BLIND on proofs [9]
#: and [10]; the one case that drives the generator skips in BOTH runs there ("UNMEASURED here, not passed"), so the
#: tampered run stayed green about nothing - and that one BLIND record shut every lock on the PC, the river with it.
ELSEWHERE = "ELSEWHERE"
#: capability -> (module, probe, his words for it). A name not listed here is INVALID: a typo must never excuse a proof.
PROOF_NEEDS_HOST = {
    "d2r-install": ("affix_lexicon", "install_present", "the D2R install (its CASC data and the extractor)"),
    # REG-1688 — the ALT filed test_a_stub_agent_never_films_his_screen BLIND on [2] and [3]: the film loop it guards
    # starts only on macOS (start_film_thread returns unless sys.platform == "darwin"), and the law reaches the farewell
    # look with SIGTERM, which on Windows ends the process before any handler runs.
    "macos": ("heart2", "_host_is_macos", "macOS (the code it guards runs only there)"),
    "posix-signals": ("heart2", "_host_has_posix_signals",
                      "a SIGTERM that reaches the process's handler (Windows ends the process instead)"),
    # REG-1719 — the ALT on v3556 filed four gates BLIND; three judged code its Windows PC never runs. numpy: the ALT
    # has none, so the inventory lattice cannot read a frame there and every lattice law skips (all 7 cases, both
    # tamper and clean). posix: the prover's birth read runs `ps` through fork_exec only off Windows.
    "numpy": ("heart2", "_host_has_numpy", "numpy (the inventory lattice reads a frame only with it)"),
    "posix": ("heart2", "_host_is_posix", "a POSIX process table (ps through fork_exec; Windows reads births another way)"),
}


def _host_is_macos():
    """REG-1688 — the PROOF_NEEDS_HOST probe for "macos". -> bool"""
    return sys.platform == "darwin"


def _host_has_posix_signals():
    """REG-1688 — the PROOF_NEEDS_HOST probe for "posix-signals". -> bool"""
    return not sys.platform.startswith("win")


def _host_has_numpy():
    """REG-1719 — the PROOF_NEEDS_HOST probe for "numpy". -> bool (asks the import system; imports nothing)"""
    import importlib.util as _ilu
    return _ilu.find_spec("numpy") is not None


def _host_is_posix():
    """REG-1719 — the PROOF_NEEDS_HOST probe for "posix". -> bool"""
    return os.name == "posix"


def host_lacks(need):
    """REG-1686 — does THIS PC lack what a red-proof declared it needs? -> (True | False | None, words)

    True: the proof is ELSEWHERE here. False: judge it as usual. None: the name is not a declared capability (the proof
    is INVALID) or the probe itself failed - judged as usual then, so a broken probe can never soften a verdict."""
    spec = PROOF_NEEDS_HOST.get(str(need or ""))
    if spec is None:
        return None, "an undeclared capability %r" % (need,)
    mod, fn, words = spec
    try:
        import importlib
        return (not bool(getattr(importlib.import_module(mod), fn)())), words
    except Exception as e:
        return False, "%s (its probe failed: %s - judged as usual)" % (words, type(e).__name__)


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


def gate_shas(gates=None):
    """#99 — each gate file's OWN content digest: the per-gate half of gates_fingerprint(). -> {name: sha | None}

    None = the file would not read. UNKNOWN, never an empty file's digest - so an unreadable gate is owed a proof,
    never counted as proved for a file nobody could read. [[unknown-stays-unknown]]"""
    out = {}
    for n, f in (gates if gates is not None else gate_files()):
        src = _read_text(f if os.path.isabs(f) else os.path.join(HERE, f))
        out[n] = None if src is None else hashlib.sha256(src.encode("utf-8", "replace")).hexdigest()[:16]
    return out


def slice_owed(gates=None, state=None):
    """#99 — which gates that DECLARE a proof this census has not proved against the file on disk now. -> dict

    {"owed": [(name, n_proofs)], "declared": int, "covered": int, "why": str}. `state` is a parsed census; None reads
    STATE. An absent census owes every declaring gate; one that will not parse owes them all too and SAYS so - the
    slices then rebuild it, and heart2 refuses to write over a file it cannot read, so that case is named, not hidden.
    A census from before per-gate digests (no `gateShas`) owes everything once: nothing in it can say which gate
    files changed since it ran."""
    gates = gates if gates is not None else gate_files()
    why = ""
    if state is None:
        state = {}
        if os.path.exists(STATE):
            try:
                with io.open(STATE, encoding="utf-8") as fh:
                    state = json.load(fh)
            except Exception as e:
                state, why = {}, "the census would not parse (%s)" % type(e).__name__
    recorded = state.get("gateShas") if isinstance(state, dict) else None
    recorded = recorded if isinstance(recorded, dict) else {}
    shas = gate_shas(gates)
    owed, declared = [], 0
    for n, f in gates:
        proofs = red_proofs_in(f)
        if not proofs:
            continue
        declared += 1
        if not shas.get(n) or recorded.get(n) != shas.get(n):
            owed.append((n, len(proofs)))
    owed.sort(key=lambda t: t[0])
    return {"owed": owed, "declared": declared, "covered": declared - len(owed),
            "why": why or ("%d of %d declaring gate(s) proved for the files on disk" % (declared - len(owed), declared))}


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


#: #42 — what starts a browser: the harness module in tv/ and the one package outside it.
_RENDERERS = ("render_check", "playwright")


def _imported_names(tree):
    """#42 — every top-level module name one parsed file can import. -> set[str]

    `import a.b` / `from a.b import c` anywhere in the file (a lazy import inside a function starts the same browser the
    day that function runs), `from tv import x` as x, and `__import__("x")` / `importlib.import_module("x")` when the
    name is a literal. A name built at run time is not seen - the same floor pixel_gates states, one level down."""
    out = set()
    for x in ast.walk(tree):
        if isinstance(x, ast.Import):
            for a in x.names:
                out.add(a.name.split(".")[0])
        elif isinstance(x, ast.ImportFrom) and x.module:
            head = x.module.split(".")[0]
            out.add(head)
            if head == "tv":
                out.update(a.name.split(".")[0] for a in x.names)
        elif (isinstance(x, ast.Call) and x.args and isinstance(x.args[0], ast.Constant)
              and isinstance(x.args[0].value, str)):
            fn = x.func
            called = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else None
            if called in ("__import__", "import_module"):
                out.add(x.args[0].value.split(".")[0])
    return out


def browser_gates(gates=None, tv_dir=None, unclassified=None):
    """#42 — the gates whose IMPORT GRAPH reaches a browser (render_check / playwright), however many helpers deep.
    -> set[str]

    ⚠ pixel_gates READS ONE FILE, AND THE ONE-BROWSER LOCK WAS BUILT ON IT. It answers "does this gate import the
    harness itself", which misses a gate that reaches it through a helper - test_the_rails_fold_is_a_chevron_not_a_dot
    does `import test_the_character_builder_fits_at_every_width as FT; RC = FT.RC` and calls RC._chrome_up(), so at push
    time it could start a second Chrome beside a width law while the lock said one. Found by the adversarial review of
    #42. The lock set is the CLOSURE: follow every name the gate imports that is a module in tv/ (tv/<name>.py), then
    every name those import, and so on; the gate is in the set when any of them imports render_check or playwright.

    ⚠ UNKNOWN GOES UNDER THE LOCK. A gate - or a helper anywhere in its closure - that cannot be read or parsed may
    reach a browser and nobody can say it does not: it is in the set (the safe side costs time, never a second Chrome)
    and its name goes into `unclassified`. Over-inclusion is the only error this may make on purpose.

    CACHED PER RUN: each tv/ file is parsed at most once per call, however many gates share it, and only the files some
    gate actually reaches are parsed. `tv_dir` lets the law build its fixture modules in a temp dir. [[the-unjoined-end]]
    [[unknown-stays-unknown]]"""
    d = tv_dir or HERE
    _unk = unclassified if unclassified is not None else []
    try:
        local = set(f[:-3] for f in os.listdir(d) if f.endswith(".py"))
    except OSError:
        # ⚠ NOT an empty tree: read as "no helpers" it would follow nothing and let every helper-reached browser out of
        # the lock. Nobody can say what the gates import, so each one is UNKNOWN below - locked and named.
        local = None
    parsed = {}                       # module -> set of names it imports | None (unreadable / unparseable)

    def _names(mod, path=None):
        if mod not in parsed:
            src = _read_text(path or os.path.join(d, mod + ".py"))
            try:
                parsed[mod] = None if src is None else _imported_names(ast.parse(src))
            except (SyntaxError, ValueError):      # ValueError: a NUL byte in the source - unparseable all the same
                parsed[mod] = None                  # UNKNOWN, never "imports nothing": the caller locks it and names it
        return parsed[mod]

    out = set()
    for n, f in (gates if gates is not None else gate_files()):
        path = f if os.path.isabs(f) else os.path.join(d, f)
        if not os.path.exists(path):
            # ABSENT is not UNREADABLE: a gate file that is not there runs nothing, so it starts no browser (and its
            # proof is refused on its own line: "the gate file is not in the sandbox"). Every helper followed below
            # exists - they come from the directory listing.
            continue
        start = os.path.basename(path)[:-3] if path.endswith(".py") else os.path.basename(path)
        seen, stack, verdict = set(), [(start, path)], (False if local is not None else "unknown")
        while stack and not verdict:
            mod, p = stack.pop()
            if mod in seen:
                continue
            seen.add(mod)
            names = _names(mod, p)
            if names is None:
                verdict = "unknown"
                break
            if names & set(_RENDERERS):
                verdict = True
                break
            for dep in names & local:
                stack.append((dep, None))
        if verdict:
            out.add(n)
            if verdict == "unknown":
                _unk.append(n)
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
    return _red_proofs_of_tree(tree)


def _red_proofs_of_tree(tree):
    """red_proofs_in's reader, on a tree already parsed - #42 reads a gate's RED_PROOF as the push BASE holds it through
    this same function, never a second copy of the rule below. [[copy-drift]]"""
    import ast
    # ⚠⚠ #220 — IT RETURNED INSIDE THE FIRST MATCHING ASSIGN. Two defects from one early return:
    # (1) the eye on v3476: a literal list followed by an unreadable one landed in `have` (its first
    # list's proofs ran) AND in red_proof_unreadable's bucket, so prove()'s "do not" went -1 and the
    # warning said none of it had run; (2) MEASURED 2026-09-24, the live one the eye did not name:
    # test_the_ledger_cannot_lie_about_what_it_saw.py bound RED_PROOF twice — 1 proof at line 82,
    # 11 at line 519 — and this proved the FIRST, which `import` overwrites. The 11 had never run.
    # Now ONE walker for every caller: any unreadable binding -> None (the declaration is
    # unreadable as a whole, exactly what red_proof_unreadable says); otherwise the LAST binding,
    # which is what the module holds. The census refuses more than one binding outright.
    vals = []
    for node in _red_proof_bindings(tree):
        try:
            vals.append(ast.literal_eval(node.value))
        except Exception:
            return None
    if not vals:
        return None
    return _normalise_proofs(vals[-1])


def _red_proof_bindings(tree):
    """Every top-level binding of RED_PROOF — `=` and `x: T = ...` — in file order. -> [ast node]"""
    import ast
    out = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "RED_PROOF" for t in node.targets):
                out.append(node)
        elif isinstance(node, ast.AnnAssign):
            if (isinstance(node.target, ast.Name) and node.target.id == "RED_PROOF"
                    and node.value is not None):
                out.append(node)
    return out


def red_proof_binding_count(filename):
    """#220 — how many top-level RED_PROOF bindings a gate file has. -> int | None (will not parse)

    More than one is a malformed declaration: only the LAST exists at import, so an author who
    wrote two lists believes proofs run that never do. The census refuses it."""
    import ast
    p = os.path.join(HERE, filename)
    try:
        with io.open(p, encoding="utf-8") as fh:
            return len(_red_proof_bindings(ast.parse(fh.read())))
    except Exception:
        return None


def red_proof_unreadable(filename):
    """v3473 — does this file DECLARE a RED_PROOF the prover cannot read? -> True | False | None

    ⚠⚠ red_proofs_in() answers None for FOUR different states — no file, no declaration, a file
    that will not parse, and a list ast.literal_eval refuses — and every caller reads None as "this
    gate declares no proof". MEASURED 2026-09-24: test_a_cut_off_gate_set_is_not_a_verdict declared
    eleven proofs whose `file` was the NAME `WF_REL`; literal_eval threw, the prover printed
    "0 declare a red-proof", and not one of the eleven had ever run. Once literal, all eleven were
    PROVEN. An unreadable declaration is not an absent one. [[unknown-stays-unknown]]
    None means the FILE would not parse, which is UNKNOWN too — never False.
    """
    import ast
    p = os.path.join(HERE, filename)
    try:
        with io.open(p, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
    except Exception:
        return None
    # ⚠ v3476 — EVERY top-level assignment, `x: T = ...` included. The v3473 cut returned on the
    # FIRST Assign to RED_PROOF, so a literal list followed by a `WF_REL` one read as readable and the
    # unreadable one was invisible; an AnnAssign was never looked at. Found by the eye on v3473.
    for node in _red_proof_bindings(tree):    # #220 — the same walker red_proofs_in uses
        try:
            ast.literal_eval(node.value)
        except Exception:
            return True
    return False


def _normalise_proofs(raw):
    """Every declared proof as the dict `_prove_one` reads. -> [dict]

    ⚠⚠ TWO SHAPES WERE IN THE TREE AND THE PROVER COULD ONLY READ ONE, SO THE WHOLE LOOP DIED.
    374 gates declare `RED_PROOF` as dicts; **12 declare 4-tuples** `(file, find, replace,
    breaks)`. `_prove_one` does `pr.get("file")` with no isinstance check, and `prove()`'s loop is
    `try: ... finally:` with NO `except` — so the first tuple raised AttributeError straight out
    of `prove()`, **`_write_state(results)` never ran**, and `_heart2_census()` in control_app.py
    went on reading a file nothing had refreshed.

    So the organ whose entire purpose is asking "can my own gates still go red" aborted on gate
    number one of twelve, and reported through a census it had stopped writing. MEASURED
    2026-09-17: 32 proofs across 12 gates, every one of arity 4, none of them ever executed.

    ⚠ NORMALISE AT THE READER, NOT AT THE PROVER. Both the engine and every law that inspects
    proofs go through this function, so a second shape can never again be legal for one reader and
    unreadable to another. The tuple's 4th slot names the law that must break, which is what the
    dict calls `why`; `matches` is absent from the tuple form and stays None — UNKNOWN, so a
    tuple proof can never claim a match count nobody wrote. [[the-unjoined-end]]
    [[unknown-stays-unknown]] [[copy-drift]]
    """
    out = []
    for pr in (raw or []):
        if isinstance(pr, dict):
            out.append(pr)
            continue
        if isinstance(pr, (tuple, list)) and len(pr) == 4:
            out.append({"file": pr[0], "find": pr[1], "replace": pr[2],
                        "why": pr[3], "matches": None})
            continue
        # a shape nobody has taught this reader: keep it, so the well-formedness law SEES it and
        # says so, rather than it vanishing here and reading as "no proof declared".
        out.append({"file": None, "find": None, "replace": None,
                    "why": "unreadable proof shape: %r" % (pr,), "matches": None})
    return out


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
        with io.open(p, encoding="utf-8", errors="replace") as _fh:      # closed: this ran ~700 times per prove unclosed
            tree = ast.parse(_fh.read())
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


# ⚠⚠ 2026-09-26 — A KILLED PROVER LEFT ITS SANDBOX BEHIND, ELEVEN TIMES. Every sandbox is removed in a `finally`,
# and a `finally` never runs when the process is killed by a signal: the pre-push gate's bound, a `perl alarm`, a
# closed terminal. MEASURED that morning: 11 heart2.* repo copies in the temp dir, Sep 23 -> Sep 26, one per
# interrupted run, the newest from a proof I bounded at 50 minutes myself. So every sandbox is REGISTERED the moment it
# exists and carries its owner's pid; SIGTERM / SIGALRM / SIGHUP remove the registered ones before the process dies; and
# every run first sweeps a heart2.* sandbox whose owner is dead (or, written before the owner file existed, a day old).
# A sandbox whose owner is ALIVE is never touched - it is another prover, mid-run. [[i-own-everything-i-start]]
_SANDBOXES = set()
_SANDBOX_OWNER = ".heart2-owner"
SANDBOX_STALE_S = 24 * 3600


def _pid_alive(pid):
    # ⚠⚠ #50 (REG-1447) — os.kill(pid, 0) IS A CTRL-C ON WINDOWS (signal 0 == CTRL_C_EVENT), not a probe.
    # Now that every PC proves itself, this runs on Windows: ask the way control_app does. An import
    # failure answers ALIVE - keeping a sandbox is safe, removing a live prover's sandbox is not.
    if os.name == "nt":
        try:
            import self_prove as _sp
            return _sp.pid_alive(pid)
        except Exception:
            return True
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True                          # it exists, it is simply not ours to signal
    except (OSError, ValueError, TypeError):
        return False
    return True


#: Off the Mac there is no free clone, so a need is COPIED - and only below these sizes. Above them the gate
#: stays UNPROVABLE, which is honest, rather than a prover filling his disk one sandbox at a time.
_NEED_COPY_MAX_FILE = 50 * 1024 * 1024
_NEED_COPY_MAX_TREE = 200 * 1024 * 1024


def _bring_across(src, dst, need, say):
    """Place one PROOF_NEEDS item in a sandbox. Never escapes the sandbox, never fills the disk.

    ⚠⚠ #50 (REG-1448) — THIS WAS `cp -c -R` ON EVERY PLATFORM, AND `cp` DOES NOT EXIST ON WINDOWS. Every
    need raised FileNotFoundError there, so no sandbox on the ALT carried `.git` or the spec file, and the
    laws that read them SKIPPED through their own sabotage - `test_eye_declares_reach` read BLIND on the
    ALT while it goes red on the Mac. Now that every PC proves itself (REG-1447), that is a lock held shut
    on every Windows PC by the prover's own plumbing.
    The Mac keeps the APFS clone, byte for byte. Elsewhere: `.git` (1.8 GB on his Mac) becomes a
    `git clone --shared` - the objects are BORROWED read-only through alternates, the refs and the index
    are the sandbox's own, so nothing a law runs in there can write into the real repository; its index
    is rebuilt from HEAD, which on an installed console is the working tree. Anything else is copied only
    under the size caps above.
    """
    if sys.platform == "darwin":
        _rc = subprocess.run(["cp", "-c", "-R", src, dst],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT).returncode
        if _rc != 0:      # not APFS, or clones unavailable — say so rather than silently copying GBs
            say("  could not CLONE %r (cp -c exit %s) — not copying it by hand; the gate stays "
                "UNPROVABLE rather than risking the disk" % (need, _rc))
        return
    if os.path.basename(os.path.normpath(src)) == ".git" and os.path.isdir(src):
        tmp = dst + ".shared"
        env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
        r = subprocess.run(["git", "clone", "-q", "--shared", "--no-checkout",
                            os.path.dirname(os.path.normpath(src)), tmp],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300, env=env)
        if r.returncode != 0:
            _rmtree_hard(tmp)
            say("  could not share the git history into the sandbox (git clone --shared exit %s) — gates "
                "that read it stay UNPROVABLE" % r.returncode)
            return
        os.replace(os.path.join(tmp, ".git"), dst)
        _rmtree_hard(tmp)
        subprocess.run(["git", "read-tree", "HEAD"], cwd=os.path.dirname(dst),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, env=env)
        return
    if os.path.isfile(src):
        if os.path.getsize(src) > _NEED_COPY_MAX_FILE:
            say("  PROOF_NEEDS %r is too large to copy without a clone — the gate stays UNPROVABLE" % need)
            return
        shutil.copy2(src, dst)
        return
    total = 0
    for _r, _ds, _fs in os.walk(src):
        for _f in _fs:
            try:
                total += os.path.getsize(os.path.join(_r, _f))
            except OSError:
                pass
            if total > _NEED_COPY_MAX_TREE:
                say("  PROOF_NEEDS %r is over %d MB — not copied without a clone; the gate stays UNPROVABLE"
                    % (need, _NEED_COPY_MAX_TREE // (1024 * 1024)))
                return
    shutil.copytree(src, dst)


def _track_sandbox(root):
    """Register a sandbox the moment it exists, and stamp it with this process as its owner."""
    _SANDBOXES.add(root)
    try:
        with open(os.path.join(root, _SANDBOX_OWNER), "w") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass
    return root


def _rmtree_hard(path):
    """REG-1746 — remove a tree even where a permission bit stands in the way. -> True when it is GONE.

    MEASURED on the ALT, 2026-10-02: 72 heart2 sandboxes in its TEMP since 09-29, 20,345 MB, with 25.8 GB free.
    Each held three files - the git pack (.idx/.pack/.rev, ~280 MB) - because git writes packs READ-ONLY and
    Windows refuses to unlink a read-only file ("[WinError 5] Access is denied"). rmtree(ignore_errors=True)
    swallowed that, after deleting the owner file first, so the stale sweep then read every leftover as "no
    owner" and failed on the same pack every time it tried. The Mac never saw it: POSIX unlinks a read-only file
    in a writable directory. So: a plain pass, then clear the bits on whatever is left and pass again - and the
    answer is whether the path still exists, never that the call returned. [[unknown-stays-unknown]]
    """
    shutil.rmtree(path, ignore_errors=True)
    if not os.path.exists(path):
        return True
    for dp, dns, fns in os.walk(path):
        for n in dns:
            try:
                os.chmod(os.path.join(dp, n), 0o700)
            except OSError:
                pass
        for n in fns:
            try:
                os.chmod(os.path.join(dp, n), 0o600)
            except OSError:
                pass
    shutil.rmtree(path, ignore_errors=True)
    return not os.path.exists(path)


def _drop_sandbox(root):
    _SANDBOXES.discard(root)
    if not _rmtree_hard(root):
        sys.stderr.write("  a sandbox could not be removed (it stays on disk until the next sweep): %s\n" % root)


def _remove_all_sandboxes():
    for root in list(_SANDBOXES):
        _drop_sandbox(root)


def _on_fatal_signal(signum, frame):
    """A signal that would kill the prover removes its sandboxes first, then exits the way the signal meant to."""
    _remove_all_sandboxes()
    os._exit(128 + int(signum))


def install_sandbox_cleanup():
    """-> the signals now covered. Only the main thread may install a handler; anywhere else this is a no-op."""
    import signal
    done = []
    for name in ("SIGTERM", "SIGALRM", "SIGHUP"):
        sig = getattr(signal, name, None)
        if sig is None:
            continue
        try:
            signal.signal(sig, _on_fatal_signal)
            done.append(name)
        except (ValueError, OSError):
            pass
    return done


def sweep_stale_sandboxes(tmp=None, now=None):
    """Remove every heart2.* sandbox whose owner is dead, or that is older than a day whoever its owner file names.
    -> [(path, why)] removed. A live owner's sandbox is kept for a day - no proof run lives that long (the gate bounds one
    near 70 minutes), so past SANDBOX_STALE_S a "live" owner is a REUSED pid, not a prover (#231 on v3507). ⚠ This line
    said "kept, whatever its age" after that rule shipped, and the eye on v3508 read the docstring against the code."""
    tmp = tmp or tempfile.gettempdir()
    now = time.time() if now is None else now
    gone = []
    try:
        names = os.listdir(tmp)
    except OSError:
        return gone
    for n in sorted(names):
        if not n.startswith("heart2."):
            continue
        root = os.path.join(tmp, n)
        if not os.path.isdir(root) or root in _SANDBOXES:
            continue
        owner = None
        try:
            with open(os.path.join(root, _SANDBOX_OWNER)) as f:
                owner = f.read().strip()
        except OSError:
            pass
        try:
            age = now - os.path.getmtime(root)
        except OSError:
            continue
        # the #231 eye on v3507: a pid is REUSED - an owner that died without its signal handler (SIGKILL) leaves a
        # number some unrelated long-lived process may carry next, and "alive" would keep the copy forever. No proof
        # run lives a day, so past SANDBOX_STALE_S a sandbox is stale whoever its owner file names.
        if owner and _pid_alive(owner) and age < SANDBOX_STALE_S:
            continue
        if owner and age < SANDBOX_STALE_S:
            why = "its owner (pid %s) is dead" % owner
        elif age >= SANDBOX_STALE_S:
            why = "%.0f h old - no proof run lives that long%s" % (age / 3600.0, (" (owner pid %s)" % owner) if owner else "")
        else:
            continue
        if _rmtree_hard(root):                  # REG-1746 — a read-only git pack kept 71 of these on the ALT
            gone.append((root, why))
    return gone


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
    root = _track_sandbox(tempfile.mkdtemp(prefix="heart2."))
    dest = os.path.join(root, "repo")          # must NOT exist — safe_copy refuses if it does
    try:
        import safe_copy
    except Exception as e:
        say("  safe_copy will not import (%s) — refusing to tamper anywhere else" % e)
        _drop_sandbox(root)
        return None, None
    try:
        rc = safe_copy.copy(REPO, dest, False, lambda *a, **k: None)
    except Exception as e:
        say("  the sandbox could not be built: %s" % type(e).__name__)
        _drop_sandbox(root)
        return None, None
    if rc not in (0, None):
        say("  safe_copy REFUSED the sandbox (exit %s) — nothing was copied, so nothing can be "
            "proven. That is UNKNOWN, not clean." % rc)
        _drop_sandbox(root)
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
        if os.path.isfile(_s) and os.path.basename(_s) == ".git":
            # ⚠ A `.git` FILE IS A POINTER INTO ANOTHER CHECKOUT, NOT A HISTORY. In a linked worktree `.git` is one
            # line - `gitdir: <the main checkout's .git/worktrees/...>` - and cloned into the sandbox it makes every
            # git command a law runs there read, and could make it WRITE, that real worktree's index and HEAD (found
            # by the second eye through the #42 P3 key, which listed `.git` among a law's inputs: a stable string,
            # but a door). safe_copy already drops a file named .git; this is the one copier that brought it. A
            # sandbox holds no door to the real repo: the need stays out, said, and the gate that declared it reads
            # UNPROVABLE here. Where .git is a directory (his main checkout, where the push runs) the clone is a
            # full private copy, exactly as before. [[feedback-fixtures-never-touch-live-data]]
            say("  PROOF_NEEDS %r is a worktree POINTER (a file naming another checkout's git dir), not a history "
                "- not brought across, so the gate that declared it stays UNPROVABLE in this sandbox" % _need)
            continue
        _d = os.path.normpath(os.path.join(dest, "tv", _need))
        if not (_d + os.sep).startswith(os.path.normpath(dest) + os.sep):
            say("  PROOF_NEEDS %r would land outside the sandbox — refused" % _need)
            continue
        try:
            os.makedirs(os.path.dirname(_d), exist_ok=True)
            _bring_across(_s, _d, _need, say)
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
        _drop_sandbox(root)
        return None, None
    return tv, root


def blind_reason(why, matches, tail, widths=None):
    """The sentence a BLIND verdict prints. -> str

    #42 — `widths` is the restriction a push-time proof DECLARED (None everywhere else). Under it a width law skips every
    case measured at other viewports BY DESIGN, so its `skipped=N` is the declaration's doing, never the law opting out:
    those skips are named as the restriction's, and the work they point at is the declaration, not a skipTest. Without
    it every sentence below reads exactly as it did. Found by the adversarial review of #42. [[unknown-stays-unknown]]

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
    if widths:
        import law_widths as _LW
        _at = _LW.label(widths)
        _of = int(_rn.group(1)) if _rn else None
        if _of is not None and _of <= n_skipped:
            return (_base + "  ⚠ ALL %d law(s) SKIPPED under the proof's DECLARED restriction to %s: no case of this law "
                            "measures there, so the declaration measured nothing - re-measure where the defect shows "
                            "(the skips are the restriction's, not the law opting out)." % (_of, _at))
        return (_base + "  (%d%s law(s) SKIPPED under the proof's DECLARED restriction to %s - cases measured at other "
                        "viewports skip there by design, not the law opting out; the ones that ran at %s stayed green.)"
                % (n_skipped, (" of %d" % _of) if _of is not None else "", _at, _at))
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


_LANE_LOCAL = threading.local()


def _stamp_lane_ports(env, lane):
    """#144 — write this prove lane's port base into the gate's environment."""
    import lane_ports as _lp
    return _lp.stamp(env, lane)


def _run_gate(sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
    # v2882 — `extra` carries the registered gate's argv tail (e.g. `--selftest`). Without
    # it a gate runs a command the suite never issues, and its verdict is about something
    # else. Default empty keeps every existing caller identical.
    """-> (passed: bool, tail: str)"""
    p = os.path.join(sandbox_tv, filename)
    if not os.path.exists(p):
        return None, "the gate file is not in the sandbox"
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"      # no stale .pyc can outlive a tamper
    # ⚠ #42 — THE RESTRICTION BELONGS TO THE PROOF, NEVER TO THE ENVIRONMENT. `widths` is handed in only by a push-time
    # proof that DECLARED them (_prove_push_one); every other run — every run without --push, every proof that declares
    # none, triage — has TV_LAW_WIDTHS REMOVED, so a value left in a shell can never quietly turn a full sweep into a
    # sample that still prints OK. [[regression-guard]]
    env.pop("TV_LAW_WIDTHS", None)
    # REG-1729 (#156) - a law never asks his live console: the same door run_gates uses (a dead free port unless the
    # gate needs his console). A sandboxed proof is a law run like any other.
    import run_gates as _rg_env
    env = _rg_env.law_env(_rg_env.needs_app_of(filename), env)
    # #144 — this lane's own ports. Suites that pin 17971/17972 derive from TV_LANE_PORT_BASE.
    # needs_app keeps whatever law_env left, so a gate that must ask his console still can.
    # No lane (a direct _run_gate, triage) stamps nothing.
    _ln = getattr(_LANE_LOCAL, "n", None)
    if _ln and not _rg_env.needs_app_of(filename):
        env = _stamp_lane_ports(env, _ln)
    if widths:
        import law_widths as _LW
        env[_LW.ENV] = _LW.label(widths)
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
    _LAST_RED[threading.get_ident()] = _red_ids(_lines)     # #42 lever 1 — which cases went red, for the red memory
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
# ══ HOW MANY PROOFS RUN AT ONCE, AND WHY EVERY LANE GETS ITS OWN SANDBOX ═══════════════════════
# The loop below used to be doubly serial — per gate, then per proof — and one proof is
# "sabotage a file → run that gate in a subprocess → restore". MEASURED on his pushes: this step
# was ~24 min of a 38m42s push and ~26 min of a 41m25s one, 60%+ of EVERY push, with ONE child
# process alive at a time and load ~2.2 on a 10-core machine. It was never CPU-bound. It was
# serialised, and it GROWS with every law added.
#
# ⚠⚠⚠ THE OBVIOUS SPLIT — one worker per GATE inside ONE SHARED sandbox — IS UNSAFE, and this is
# the measurement that settles it, taken 2026-09-23 over the whole registry:
#       537 gate files readable · 497 declare a red-proof · 1,302 declared proofs
#       149 distinct tampered files once resolved · 67 of them claimed by MORE THAN ONE gate
#       446 of 497 gates (90%) tamper a file that another gate also tampers
#       control_app.py alone: 124 gates tamper it — and a further 110 gates NAME it without
#       tampering it at all, so they would read a neighbour's sabotage and go red for it
# Two lanes in one sandbox is a false verdict in BOTH directions: a neighbour's sabotage reddens
# an innocent gate (which reports UNPROVABLE, "already red untampered" — a sentence that would be
# a lie), and a neighbour's restore can hand a gate CLEAN bytes at the exact moment it is supposed
# to be judging tampered ones, which reads as PROVEN. Grouping by tampered FILE does not fix it
# either: a gate reads far more than it tampers, which is what that 110 measures.
#
# So: ONE THROWAWAY SANDBOX PER LANE, gates pulled from a shared queue, every proof of a gate run
# serially inside the one lane that owns it. A lane is then EXACTLY the old serial loop over a
# subset of the gates; nothing is shared between lanes but the queue and the printer's lock. This
# changes WHEN work happens and never WHETHER: the same proofs run, in the same order within a
# gate, against the same bytes.
#
# ⚠ AND A LANE THAT DIES CANNOT CORRUPT ANYTHING. _prove_one restores in a `finally`, but a lane
# killed outright — the 10-minute foreground ceiling has killed pushes in this repo three times —
# leaves its sabotage inside a throwaway copy that no other lane and nothing in the real tree ever
# reads. The real tree is never written at all.
#
# DERIVATION OF THE DEFAULT, measured on his 10-core Mac, not estimated:
#   · one sandbox = safe_copy + the PROOF_NEEDS clones: 2.7s alone, 6.1s for 4 built at once,
#     ~384 MB of real disk each (1,534 MB for four, all of it reclaimed by rmtree)
#   · 4 lanes leave 6 cores for the gate subprocesses the lanes spend their time waiting on
#   · ⚠⚠ THE CEILING IS NOT THE CORE COUNT, IT IS THE GATES THAT ASSERT DURATIONS. test_control
#     takes 19.5s idle and 565.9s under concurrent load — a 29x slowdown that once produced a
#     FALSE RED and refused a legitimate push. Parallel proving MANUFACTURES exactly that load on
#     purpose, so the number stays low and can be turned DOWN without an edit.
# HEART2_PROVE_WORKERS=1 is the old single-sandbox behaviour, unchanged, for a loaded machine.
PROVE_WORKERS = 4
LANE_DISK_MB = 400            # measured ~384 MB of real disk per sandbox, rounded up
LANE_DISK_FLOOR_MB = 4096     # the same floor safe_copy itself refuses to copy below

# ══ AND THE DEADLINE HAS TO GROW WITH THE LOAD THE LANES THEMSELVES MANUFACTURE ═══════════════
# ⚠⚠ MEASURED, AND IT IS THE ONE THING THE A/B FOUND. Proving the same 25 gates (74 proofs) in a
# frozen copy of the tree, serial versus lanes:
#       serial 1 lane (cold 766.6s / warm 606.3s) · 2 lanes 286.3s · 4 lanes 258.4s
#       25 of 25 GATE verdicts identical at every lane count · 0 bytes of tree drift in all four
#       73 of 74 PROOF verdicts identical — and ONE flipped:
#           test_a_cached_absence_is_not_an_absence[0]  PROVEN -> UNPROVABLE
# It did not flip because a lane corrupted anything. Its CLEAN run takes ~110 s against a
# registered timeout of 120 s — measured at 230.3 s for clean+tampered in the SERIAL control, and
# that same control already reports its OTHER proof UNPROVABLE for the identical timeout reason.
# The gate sits on its own deadline, serially, on an idle machine. Any load at all tips it.
#
# ⚠ AND THE FLIP IS NOT HARMLESS. `UNPROVABLE` makes _write_state DISCARD a standing proof, so a
# deadline that expired because of MY concurrency would quietly delete a proof the heart had
# banked — a number walking backwards for a reason that is nothing to do with the law.
#
# The honest fix is not a smaller lane count: 2 lanes flips the SAME proof, measured. The deadline
# is an INSTRUMENT parameter — how long this prover waits before giving up — and it must not be
# what decides whether a law can be measured. So when more than one lane is running, every gate's
# registered timeout is multiplied by this. The number is measured, not guessed: the worst
# per-proof inflation observed at 4 lanes was 1.75x (1.2s -> 2.1s on a short gate, where fixed
# start-up contention dominates); long gates ran at 0.98x-1.01x. 2 covers that with margin.
# ⚠ IT APPLIES ONLY WHEN LANES > 1, so the single-lane path keeps the exact deadline it always
# had, and a genuinely hung gate still gives up — at 2x a bounded budget, never never.
LANE_DEADLINE_SCALE = 2
DEADLINE_SCALE = 1            # what _prove_one actually multiplies in; set by _prove_gates
#: ⚠⚠ #50 (REG-1454) — A BACKGROUND PROOF ON A SLOWER PC IS THE SAME CASE AS A BUSY LANE. On the ALT the
#: self-prove lane runs this at BELOW_NORMAL priority beside a console that is filming, and
#: `test_screen_parity` timed out at its 120 s on every proof - UNPROVABLE - while the same law passes in a
#: plain copy there given time. The deadline is this prover's patience, not the law, so the caller that
#: KNOWS it is running slow says so: heart2 reads HEART2_DEADLINE_SCALE (a number >= 1, capped at 8; junk
#: is ignored and said). A genuinely hung gate still gives up, at most 8x a bounded budget.
DEADLINE_SCALE_MAX = 8


def _deadline_scale(n_lanes, env=None, say=None):
    """The factor every gate's registered timeout is multiplied by in this run. -> int >= 1"""
    base = LANE_DEADLINE_SCALE if n_lanes > 1 else 1
    raw = (env if env is not None else os.environ).get("HEART2_DEADLINE_SCALE")
    if not raw:
        return base
    try:
        asked = int(float(raw))
    except (TypeError, ValueError):
        if say:
            say("  HEART2_DEADLINE_SCALE=%r is not a number - ignored" % raw)
        return base
    return max(base, min(DEADLINE_SCALE_MAX, max(1, asked)))


def prove_workers(n_gates=None, say=None):
    """How many lanes `--prove` may run at once. -> int >= 1

    ⚠ IT MUST BE TURNABLE DOWN WITHOUT AN EDIT, because the reason to turn it down is a machine
    that is already loaded — the condition under which editing a file and re-running is worst.
    An unreadable or absurd value falls back to the default AND SAYS SO: a number nobody asked
    for, chosen silently, is how a gate ends up measuring something else. [[unknown-stays-unknown]]

    ⚠ AND IT IS CAPPED BY FREE DISK, because each lane is a real copy. safe_copy refuses below
    4 GB free one copy at a time, but four lanes build CONCURRENTLY and that check would race.
    Answering 1 rather than 0 is deliberate: one lane is the old behaviour, and safe_copy still
    gets to refuse it honestly.
    """
    n = PROVE_WORKERS
    raw = os.environ.get("HEART2_PROVE_WORKERS")
    if raw is not None:
        try:
            n = int(str(raw).strip())
        except Exception:
            n = PROVE_WORKERS
            if say:
                say("  ⚠ HEART2_PROVE_WORKERS=%r is not a number — falling back to %d lane(s)"
                    % (raw, n))
        if n < 1:
            if say:
                say("  ⚠ HEART2_PROVE_WORKERS=%r is below 1 — using 1 lane (the serial loop)" % raw)
            n = 1
    n = max(1, min(int(n), 16))
    if n_gates:
        n = min(n, int(n_gates))
    try:
        free_mb = shutil.disk_usage(tempfile.gettempdir()).free / (1024.0 * 1024.0)
        room = int((free_mb - LANE_DISK_FLOOR_MB) // LANE_DISK_MB)
        if room < n:
            if say:
                say("  ⚠ only %d MB free: %d lane(s) would leave less than %d MB, so this run uses "
                    "%d. Fewer lanes, never a skipped proof." % (int(free_mb), n,
                                                                 LANE_DISK_FLOOR_MB, max(1, room)))
            n = max(1, room)
    except Exception:
        pass
    return max(1, n)


#: REG-1683 (the v3544 eye) — a BUFFERED lane says it is alive at most this often, so the prover's log moves while a
#: gate's verdicts are still held. self_prove ends a prover whose log stands still past silent_bound_s, and that bound
#: assumes a line per proof - a multi-lane gate held every line until the WHOLE gate ended.
LANE_BEAT_EVERY_S = 60


class _LaneSay(object):
    """One lane's printer: it buffers, and flushes a whole gate's lines at once under a lock.

    ⚠ WITHOUT IT THE VERDICT LINES INTERLEAVE and the log stops being evidence — and the log is
    the only thing `--prove` produces. Flushed per gate rather than per run, so output still
    arrives while the proving is going on instead of all at the end.

    ⚠ AND WITH ONE LANE IT DOES NOT BUFFER AT ALL. HEART2_PROVE_WORKERS=1 is offered as "the old
    loop, unchanged", and a single lane that withheld its lines until a gate finished would not be
    that — a proof can take minutes, and somebody watching a stuck run needs the line for the proof
    it is stuck on. Nothing can interleave with itself, so there is nothing to buffer for.
    """

    def __init__(self, sink, lock, buffered=True, clock=None):
        self._buf, self._sink, self._lock, self._buffered = [], sink, lock, buffered
        self._clock, self._beat = clock or time.monotonic, None

    def __call__(self, *a):
        line = " ".join(str(x) for x in a)
        if not self._buffered:
            self._sink(line)
            return
        self._buf.append(line)
        # REG-1683 — ONE short line, straight through, at most every LANE_BEAT_EVERY_S: the gate's own lines stay
        # together (they flush at its end), and the log still moves, so a working prover never reads as a silent one.
        # A two-lane slice with one gate of three proofs at a scaled 480 s per run held its log 2,400 s against a
        # 2,040 s bound - ended mid-law, booked stalled, and the next slice repeated it.
        now = self._clock()
        if self._beat is None or now - self._beat >= LANE_BEAT_EVERY_S:
            self._beat = now
            with self._lock:
                self._sink("  · a proving lane is working - %d line(s) of its gate held until the gate ends"
                           % len(self._buf))

    def flush(self):
        if not self._buf:
            return
        buf, self._buf = self._buf, []
        with self._lock:
            for line in buf:
                self._sink(line)


# ══ #42 — PUSH TIME: PROVE EACH RED-PROOF WHERE ITS DEFECT SHOWS, LIKELIEST FAILURE FIRST, ONE BROWSER AT A TIME ════════
# His words, 2026-09-28: pushes take too long — "do #42 right after v3522 lands". MEASURED on the v3522 push: a lane
# takes a whole GATE and runs all its proofs back to back, so the character builder's width law (41 proofs, each a
# clean AND a tampered run of a law that renders ~33 viewports at ~100 s a run) was ONE ~105-minute thread, the mule
# window's (25 proofs) the other long pole, and the push gate took ~2h50m. Attempt 1 of that push ran 159 min and was
# refused on ONE blind proof that a targeted run finds in ~3 min. `--push` (hooks/pre-push passes it, nothing else
# does) changes three things, and without it not one line of the path below runs:
#   1. WHERE (P1): a proof that declares "widths" runs its clean AND its tampered run with TV_LAW_WIDTHS naming them
#      (tv/law_widths.py); a proof that declares none runs at every width, exactly as without --push - never skipped.
#      ⚠ FAIL CLOSED: a declared width at which the tamper stays green reads BLIND and the push refuses as it always
#      has - a wrong declaration can never read PROVEN. An UNPROVABLE at the declared widths is re-proved at EVERY
#      width and that verdict stands. run_gates and CI never set the variable: the full sweep stays the verdict of record.
#   2. WHEN (P2): the proofs likeliest to fail run FIRST - an anchor that no longer matches as declared, an entry new or
#      changed since the push base (@{push}, else origin/main - the hook's own order), a proof whose tampered file
#      changed - and the run STOPS at the first BLIND / INVALID / clean-run red, printed the moment it is found. Every
#      proof it did not reach is NOT RUN: never banked, never PROVEN, and the exit is non-zero - a stop is a refusal,
#      never a pass. With no failure every proof still runs.
#   3. ONE BROWSER AT A TIME: a gate that starts a browser (its import graph reaches render_check / playwright through
#      any number of helpers - browser_gates(), not pixel_gates()' one file - or it declares widths) holds ONE lock
#      while it is proved, whatever the lane count - four parallel Chrome lanes drove his Mac to load 100 on 2026-09-28.
#      Every other gate keeps its lane.
# The law: test_a_push_proof_runs_only_where_its_defect_shows. [[regression-guard]] [[unknown-stays-unknown]]
NOT_RUN = "NOT RUN"     # a push-time proof the run STOPPED before reaching - never a verdict, never banked
_PUSH = None            # the running push-time context (_PushRun) while prove(push=True) runs; None otherwise
# REG-1669 (#42) — ONE CLEAN RUN SERVES A GATE'S PROOFS. Every proof ran the untampered law first, so a gate with N
# proofs paid 2N runs where N+2 do: MEASURED on his ALT 2026-10-01, a 40-gate census slice took 82 minutes. While
# _prove_gate holds a gate, its lane thread keeps that gate's clean verdict here and every later proof reuses it; a
# CLOSING clean run after the last proof must still be green, or no PROVEN of the gate is kept (the sandbox did not
# stay clean across its proofs). Per thread, because lanes run gates side by side. None outside a gate: a direct
# _prove_one call still runs its own clean run, as it always has.
_CLEAN = threading.local()


class _PushRun(object):
    """#42 — what the lanes of ONE `--prove --push` run share: the order, the browser lock, the stop."""

    def __init__(self, order=None, browser=(), cache=None):
        self.order = dict(order or {})          # {gate: [proof index, ...]}, the likeliest to fail first
        self.browser = set(browser or ())       # the gates proved one at a time: they start a browser
        self.browser_lock = threading.Lock()
        self.stop = threading.Event()
        self.first = None                       # (gate, index, verdict, reason): the failure that stopped the run
        self._lock = threading.Lock()
        self.cache = cache                      # P3: the verdict cache prove(push=True) opened, or None (every proof runs)

    def fail(self, name, idx, verdict, reason):
        """Record the FIRST failure and stop the run. -> True for the call that stopped it"""
        with self._lock:
            first = self.first is None
            if first:
                self.first = (name, idx, verdict, reason)
        self.stop.set()
        return first

    def browser_slot(self, name):
        """The lock a browser gate is proved under; for every other gate a context that holds nothing."""
        import contextlib
        return self.browser_lock if name in self.browser else contextlib.nullcontext()


# ══ #42 P3 — THE VERDICT CACHE: A PROVEN IS REUSED ONLY OVER BYTE-IDENTICAL INPUTS ═════════════════════════════════
# MEASURED 2026-09-29 on the v3523 push: the render gate refused at minute 95 (twice), and every retry re-proved the
# same ~40 changed laws (~83 min) over a tree that had not changed by one byte - three times. His order, 2026-09-28:
# "this is CRITICAL we need to optimize clock time". So a push-time PROVEN is banked under a KEY that digests every byte
# the verdict can depend on, and the next push re-runs only the proofs whose key changed:
#   · the law file itself and every module it imports - TRANSITIVELY, by the same AST walk browser_gates() uses for the
#     one-browser lock (_imported_names): a helper the law reaches through two others is still what it runs;
#   · every file a literal string anywhere in that closure names (bible.html, control_ui.html, hooks/pre-push, a data
#     file). Over-inclusion is the only error this may make on purpose - a file named in an error message costs one
#     re-prove, never a stale PROVEN;
#   · the proof's tampered target - #41 rank 8: PROVEN was keyed to the GATE file alone (gates_fingerprint), so an edit
#     to the SUBJECT could make a proof BLIND while the census still read proven - and every PROOF_NEEDS that is a file;
#   · the proof entry itself (find / replace / matches / widths), the gate's registered spec (argv tail, -c script,
#     timeout) and the prover (this file, law_widths.py): a proof is only as true as the thing that produced it.
# ⚠ THE KEY IS TAKEN FROM THE SANDBOX, NOT THE REAL TREE. The sandbox is the exact tree the proof ran in (safe_copy of
#   the repo minus footage and .git), so a file the law names that is not in it was never read, and a target resolves
#   through the same resolve_proof_target the tamper uses. It is taken BEFORE the proof and AGAIN after: when the two
#   differ the tree moved under the proof and nothing is banked. The record carries repo-relative paths only.
# ⚠ UNKEYABLE IS NEVER CACHED. A closure module nobody can read or parse, a PROOF_NEEDS that is a directory (his footage,
#   .git), a target that is not a file inside the sandbox, a named file that cannot be read: the proof runs every push
#   and the line says why. A miss runs. Only PROVEN is ever stored - BLIND / INVALID / UNPROVABLE are findings, never
#   shortcuts - and only a stored PROVEN is ever reused, whatever else lands in the file.
# ⚠ ITS REACH, STATED: a file the law reaches by a COMPUTED path (an env var, a join of variables) is outside the key -
#   the same floor pixel_gates states for imports, one level down. A law about such a file names it in PROOF_NEEDS.
#   AND A LAW THAT LISTS A DIRECTORY ITSELF HAS AN INPUT NO BYTE KEY CAN NAME (second eye on the first cut): a law
#   calling os.listdir / os.walk / os.scandir / glob.glob / Path.glob / rglob / iterdir reads whatever is THERE at run
#   time - a law file added or removed between two pushes over otherwise identical bytes could turn it red - so such a
#   law is UNKEYABLE, said once, and runs every push (57 of 628 red-proof laws on 2026-09-29). The LAW FILE ONLY is
#   scanned: heart2, run_gates and control_app all list directories, and scanning the closure would make every heart
#   law unkeyable. A listing reached THROUGH the closure (gate_files() and the like) is outside the key - stated, not
#   solved; the anchors gate runs at every push regardless.
# ⚠ A REUSED PROOF KEEPS THE TIME IT WAS MEASURED. A hit is a verdict from an EARLIER run over the same bytes, so the
#   census stamps that gate with the OLDEST provedAt among its reused proofs (verdictAt), never this run's clock - the
#   first cut stamped every hit "now", the exact defect control_app's oldestProofMs was built against. [[stale-reading]]
#   A stored PROVEN with no readable provedAt is not reused: a verdict nobody can age cannot keep its age.
# ⚠ THE CACHE MAY COST A RE-PROVE, NEVER A VERDICT. Its own bookkeeping raising (a RecursionError from ast.parse on a
#   pathological module, a relpath across volumes, anything unforeseen) makes the proof unkeyable before the run and
#   "moved" after it; the verdict the run produced stands either way.
# ⚠ PUSH TIME ONLY. prove(push=True) - hooks/pre-push's `--prove NAMES --push` - is the only opener; _prove_push takes
#   the cache as a parameter and every other caller (the plain --prove path, run_gates, CI, a law driving _prove_push
#   with a fixture) hands none and runs every proof. The file is per machine, gitignored, beside .heart2.json.
#   HEART2_PROVE_CACHE=0 leaves it closed for one run (the cold half of a measurement) and says so.
# The law: test_a_proven_verdict_is_reused_only_on_identical_bytes. [[regression-guard]] [[unknown-stays-unknown]]
CACHE = os.path.join(HERE, ".heart2_cache.json")
CACHE_MAX = 4000          # entries kept; the oldest leave first - a cache, not a ledger
_NAME_MAX = 240           # a string constant longer than this is prose, not a path
#: the run's OWN records - written by the prove / render that reads them. Keyed, every law whose closure names heart2
#: (which names all of them) would miss on every push, and this cache would invalidate itself by being written. A record
#: of a run cannot make a tamper stay green, so these are the one named exclusion; every other named file is keyed.
_SELF_RECORDS = frozenset((".heart2.json", ".heart2_cache.json", ".heart2_cache.json.tmp", ".heart2_proposals.md",
                           ".render_verdict.json", ".heart2_red.json", ".heart2_red.json.tmp"))

# ══ #42 lever 1 (REG-1710) — THE RED MEMORY: A PROOF REMEMBERS WHICH CASES CAUGHT IT ══════════════════════════════════
# MEASURED 2026-10-02: pushes went from 17-20 minutes to 100+ because every batch touched tv/test_control.py, and each of
# its 6 sabotages re-ran ALL 2,259 cases (8-14 min apiece) to learn what one or two cases already said. Now, at push time,
# a tampered run that goes red writes down WHICH cases failed; the next push asks only those - untampered first (must be
# green), then tampered (must be red). Both hold -> PROVEN in seconds. Anything else - a renamed case, a subset that
# stays green, a run that cannot finish - falls back to today's FULL proof, so the memory can only ever save time, never
# grant a verdict the full proof would refuse. Per machine, gitignored, beside .heart2_cache.json.
#   HEART2_RED_MEMORY=0 closes it for one run (the cold half of a measurement).
# The law: test_a_proof_remembers_where_it_went_red. [[regression-guard]] [[unknown-stays-unknown]]
RED_MEMORY = os.path.join(HERE, ".heart2_red.json")
RED_MEMORY_MAX = 2000      # entries kept; the oldest leave first
RED_IDS_MAX = 60           # a sabotage that reddens more cases than this is asked in full anyway
_RED_ID_RX = re.compile(r"^(?:FAIL|ERROR): (\w+) \(([\w.]+)\)")
_RED_CASE_RX = re.compile(r"^[A-Za-z_]\w*\.test\w*$")
_RED_LOCK = threading.Lock()
_LAST_RED = {}             # thread id -> the red cases of that thread's last _run_gate (a side channel: stand-ins stay valid)


def _red_ids(lines):
    """The test cases a unittest run reported red. -> sorted ["Class.test_name", ...]

    Reads both shapes unittest prints - `FAIL: test_x (__main__.Class)` (3.9) and `(__main__.Class.test_x)` (3.11+).
    A class-level error (setUpClass, a module import) names no case a narrowed run could ask for, so it is dropped."""
    out = set()
    for ln in lines or ():
        m = _RED_ID_RX.match(str(ln).strip())
        if not m:
            continue
        test, where = m.group(1), m.group(2)
        if where.startswith("__main__."):
            where = where[len("__main__."):]
        if not test.startswith("test"):
            continue
        cid = where if where.endswith("." + test) else "%s.%s" % (where, test)
        if _RED_CASE_RX.match(cid):
            out.add(cid)
    return sorted(out)


def _red_key(name, idx, pr):
    """One sabotage's identity: the gate, the proof's place, and the exact bytes it tampers. -> hex | None"""
    try:
        blob = json.dumps([str(name), int(idx), str(pr.get("file") or ""), str(pr.get("find") or ""),
                           str(pr.get("replace") or "")], ensure_ascii=False)
    except Exception:
        return None
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


def _red_load():
    """-> the memory dict, {} when there is none yet, or None when it is closed (HEART2_RED_MEMORY=0)."""
    if os.environ.get("HEART2_RED_MEMORY") == "0":
        return None
    if not os.path.exists(RED_MEMORY):
        return {}                  # nothing learned on this machine yet: every proof runs in full
    try:
        with io.open(RED_MEMORY, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception as _re:
        # said, never silent: an unreadable memory costs this push its narrowed proofs, and the reason is in the log
        print("  ⚠ the red memory would not read (%s) - every proof runs in full this push" % type(_re).__name__)
        return {}
    return d if isinstance(d, dict) else {}


def _red_recall(key):
    d = _red_load()
    e = (d or {}).get(key) if key else None
    ids = e.get("ids") if isinstance(e, dict) else None
    ids = [str(i) for i in ids if _RED_CASE_RX.match(str(i))] if isinstance(ids, list) else []
    return ids[:RED_IDS_MAX] or None


def _red_remember(key, name, idx, ids):
    if not key or not ids or len(ids) > RED_IDS_MAX:
        return
    with _RED_LOCK:
        d = _red_load()
        if d is None:
            return
        d[key] = {"gate": str(name), "proof": int(idx), "ids": list(ids), "at": int(time.time() * 1000)}
        if len(d) > RED_MEMORY_MAX:
            for k in sorted(d, key=lambda k: (d[k] or {}).get("at") or 0)[:len(d) - RED_MEMORY_MAX]:
                d.pop(k, None)
        if os.path.basename(RED_MEMORY) != ".heart2_red.json":
            return                 # the one file this writer may touch, by name - like CACHE's writer
        tmp = RED_MEMORY + ".tmp"
        try:
            with io.open(tmp, "w", encoding="utf-8") as fh:
                json.dump(d, fh, sort_keys=True)
            os.replace(tmp, RED_MEMORY)
        except Exception:
            pass                   # a memory that cannot be written costs the next push time, never a verdict


def _prove_narrow(sandbox, label, tgt, tgt_rel, find, repl, want, filename, timeout, w, ids, widths, say):
    """#42 lever 1 — ONE proof, asked only of the cases that caught it before. -> PROVEN | None (decide in full)

    Untampered, those cases must be GREEN (a renamed case, a red case or a run that cannot finish answers None); tampered,
    they must be RED. Only that pair is a proof. Every other outcome returns None and the full proof decides - so a
    BLIND law can never be called PROVEN here: its tampered subset stays green and the full run says BLIND."""
    t0 = time.time()
    args = list(ids)
    ok_c, _tc = _run_gate(sandbox, filename, timeout=timeout, extra=args, script=None, **w)
    if ok_c is not True:
        return None
    try:
        with io.open(tgt, encoding="utf-8") as fh:
            _orig = fh.read()
    except Exception:
        return None
    got = _orig.count(find) if find else 0
    if got < 1 or (want is not None and got != want):
        return None
    tampered = _orig.replace(find, repl) if want is None else _orig.replace(find, repl, want)
    if tgt_rel.endswith(".py"):
        try:
            ast.parse(tampered)
        except SyntaxError:
            return None
    with io.open(tgt, "w", encoding="utf-8") as fh:
        fh.write(tampered)
    try:
        ok_t, _tt = _run_gate(sandbox, filename, timeout=timeout, extra=args, script=None, **w)
    finally:
        with io.open(tgt, "w", encoding="utf-8") as fh:
            fh.write(_orig)
    if ok_t is False:
        say("     %-52s %s (%d match(es) tampered → red in the %d case(s) that caught it before, %.0f s)%s"
            % (label, PROVEN, got, len(ids), time.time() - t0, _at_widths(widths)))
        return PROVEN
    return None


def _sha_file(path, memo=None):
    """sha256 of a file's bytes -> hex | None (unreadable). `memo` (one run) keys on (path, size, mtime_ns), so a
    target the tamper rewrote and restored is hashed again, never served from before the tamper."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    k = (path, st.st_size, st.st_mtime_ns)
    if memo is not None and k in memo:
        return memo[k]
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
    except OSError:
        return None
    d = h.hexdigest()
    if memo is not None:
        memo[k] = d
    return d


def _inside(root, path):
    try:
        return os.path.commonpath([os.path.realpath(root), os.path.realpath(path)]) == os.path.realpath(root)
    except Exception:
        return False


def _named_files(tree, sandbox, repo):
    """The existing FILES the string constants of one parsed module name, relative to tv/ or the repo root. -> set
    An absolute constant is skipped: it points outside the sandbox (Chrome's binary, a home path) - the environment,
    not the tree - and a constant that climbs out of the repo is skipped for the same reason."""
    out = set()
    for x in ast.walk(tree):
        if not (isinstance(x, ast.Constant) and isinstance(x.value, str)):
            continue
        s = x.value
        if not s or len(s) > _NAME_MAX or "\n" in s or "\x00" in s or os.path.isabs(s):
            continue
        if os.path.basename(s) in _SELF_RECORDS:
            continue
        for base in (sandbox, repo):
            p = os.path.normpath(os.path.join(base, s))
            if _inside(repo, p) and os.path.isfile(p):
                out.add(p)
    return out


#: the calls that LIST A DIRECTORY, by the module that owns them. The receiver decides, never the bare name:
#: `ast.walk` is a walk over a syntax tree and 195 laws call it (measured 2026-09-29); `os.walk` lists a directory.
_LISTS_OS = frozenset(("listdir", "scandir", "walk"))
_LISTS_GLOB = frozenset(("glob", "iglob"))
_LISTS_PATH = frozenset(("glob", "rglob", "iterdir"))     # pathlib's, on any receiver that is not a module alias


def _lists_a_directory(tree):
    """The FIRST call in `tree` that lists a directory -> ("os.listdir", line) | None.

    Reads the module's own imports so `import glob as _g; _g.glob(...)` and `from os import listdir` count and a
    helper that happens to be named `walk` does not. Over-inclusion (a method named `glob` on some other object)
    costs one re-prove per push, never a stale PROVEN - the only error this may make on purpose. Its reach: a
    directory listed through a subprocess (`ls`, `find`, `git ls-files`) is outside it."""
    mods, froms = {"os": "os", "glob": "glob"}, {}
    for x in ast.walk(tree):
        if isinstance(x, ast.Import):
            for a in x.names:
                if a.name in ("os", "glob"):
                    mods[a.asname or a.name] = a.name
        elif isinstance(x, ast.ImportFrom) and x.module in ("os", "glob"):
            for a in x.names:
                froms[a.asname or a.name] = (x.module, a.name)
    hits = []
    for x in ast.walk(tree):
        if not isinstance(x, ast.Call):
            continue
        f = x.func
        if isinstance(f, ast.Attribute):
            recv = mods.get(f.value.id) if isinstance(f.value, ast.Name) else None
            if (recv == "os" and f.attr in _LISTS_OS) or (recv == "glob" and f.attr in _LISTS_GLOB):
                hits.append(("%s.%s" % (recv, f.attr), x.lineno))
            elif recv is None and f.attr in _LISTS_PATH:
                hits.append(("%s()" % f.attr, x.lineno))
        elif isinstance(f, ast.Name) and f.id in froms:
            m, n = froms[f.id]
            if (m == "os" and n in _LISTS_OS) or (m == "glob" and n in _LISTS_GLOB):
                hits.append(("%s.%s" % (m, n), x.lineno))
    return min(hits, key=lambda h: h[1]) if hits else None


def law_inputs(sandbox, filename, proofs, parsed=None):
    """#42 P3 — every file in `sandbox` (a copied tv/) that a law's verdict can depend on. -> (sorted [abs path], why)

    `why` is None when every input could be found and read; otherwise the reason this law is UNKEYABLE (the list then
    holds what was found before that reason, for the line that says so). The closure walk is browser_gates()'s: the
    law, every tv/ or repo-root module it imports, and so on. Each proof's tampered target and every PROOF_NEEDS file
    join it; a PROOF_NEEDS directory makes the law unkeyable (his footage and .git are never hashed).
    `parsed` (one run) memoises each module's imports and named files on (path, size, mtime_ns): control_app.py is in
    most closures and costs ~1 s to walk, and a target the tamper rewrote and restored is walked again, never served
    from before the tamper."""
    repo = os.path.dirname(os.path.abspath(sandbox))
    law = os.path.normpath(os.path.join(sandbox, filename))
    if not os.path.isfile(law):
        return [], "the gate file is not in the sandbox"
    local = {}
    for d in (repo, sandbox):                      # tv/ listed last, so a tv/ module wins over a root one
        try:
            for f in os.listdir(d):
                if f.endswith(".py"):
                    local[f[:-3]] = os.path.join(d, f)
        except OSError:
            return [], "the sandbox could not be listed, so what this law imports is UNKNOWN"
    inputs, seen, stack = set(), set(), [law]
    while stack:
        p = os.path.normpath(stack.pop())
        if p in seen:
            continue
        seen.add(p)
        try:
            st = os.stat(p)
            mk = (p, st.st_size, st.st_mtime_ns)
        except OSError:
            mk = None
        if parsed is not None and mk is not None and mk in parsed:
            names, named, lists = parsed[mk]
        else:
            src = _read_text(p)
            if src is None:
                return sorted(inputs), "%s cannot be read" % os.path.relpath(p, repo)
            try:
                tree = ast.parse(src)
            except (SyntaxError, ValueError):
                return sorted(inputs), "%s will not parse" % os.path.relpath(p, repo)
            names, named, lists = _imported_names(tree), _named_files(tree, sandbox, repo), _lists_a_directory(tree)
            if parsed is not None and mk is not None:
                parsed[mk] = (names, named, lists)
        # the floor: a law that lists a directory ITSELF reads what is there at run time - no byte key can name that.
        # Only the law file is asked (the closure lists directories everywhere; see the block comment above).
        if p == law and lists:
            return sorted(inputs), ("the law lists a directory itself (%s at line %d) - what it reads is decided at "
                                    "run time, so no byte key can name it" % lists)
        inputs.add(p)
        for dep in names & set(local):
            stack.append(local[dep])
        inputs |= named
    for pr in (proofs or []):
        rel = str(pr.get("file") or "") if isinstance(pr, dict) else ""
        if not rel:
            return sorted(inputs), "a proof names no file"
        tgt = os.path.normpath(resolve_proof_target(sandbox, rel))
        if not (_inside(repo, tgt) and os.path.isfile(tgt)):
            return sorted(inputs), "the tampered target %r is not a file inside the sandbox" % rel
        inputs.add(tgt)
    needs = proof_needs_in(law)
    if needs is None:
        return sorted(inputs), "its PROOF_NEEDS cannot be read"
    for need in needs:
        s = os.path.normpath(os.path.join(sandbox, need))
        if os.path.isdir(s):
            return sorted(inputs), "PROOF_NEEDS %r is a directory - his footage and .git are never hashed" % need
        if os.path.isfile(s):
            inputs.add(s)
        # absent: the sandbox never brought it, so the gate reads UNPROVABLE there and this proof is never PROVEN
    for prover in ("heart2.py", "law_widths.py"):
        p = os.path.join(sandbox, prover)
        if os.path.isfile(p):
            inputs.add(p)
    return sorted(inputs), None


def _load_cache(path):
    """-> (entries, None) | (None, why). An absent file is an EMPTY cache; a file that will not parse or has the wrong
    shape is UNREADABLE - said, never read as empty - and the first store rewrites it (a cache, not a ledger)."""
    if not os.path.exists(path):
        return {}, None
    try:
        with io.open(path, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception as _e:
        return None, "it would not parse (%s)" % type(_e).__name__
    ent = d.get("entries") if isinstance(d, dict) else None
    if not isinstance(ent, dict):
        return None, "it has no 'entries' map"
    return ent, None


class _VerdictCache(object):
    """#42 P3 — the PROVEN verdicts one machine may reuse at push time, and the counts a run prints beside them."""

    def __init__(self, path=None, say=print):
        self.path = path or CACHE
        self.say = say
        self.lock = threading.Lock()
        self.memo = {}                   # (path, size, mtime_ns) -> sha256, this run only
        self.parsed = {}                 # (path, size, mtime_ns) -> (imports, named files), this run only
        self.closures = {}               # (sandbox, filename) -> (inputs, why): one closure walk per law per lane
        self.hits = self.misses = self.stores = self.unkeyable = self.moved = 0
        self.dirty = False               # stores since the last flush - written per GATE, not per proof
        self._said = set()               # (gate, why): an unkeyable law's reason is said once, not once per proof
        self.reused = {}                 # (gate, proof) -> provedAt ms of the entry a hit served, this run
        self.measured = {}               # gate -> the OLDEST provedAt among its reused proofs; the census stamp
        ent, why = _load_cache(self.path)
        self.readable = why is None
        if not self.readable:
            say("  #42 P3 CACHE: %s is UNREADABLE (%s) - every proof runs, and the first PROVEN rewrites it"
                % (os.path.basename(self.path), why))
        self.entries = ent if ent is not None else {}

    def key_for(self, sandbox, name, filename, pr):
        """-> (key | None, [repo-relative inputs], why-unkeyable | None), from the SANDBOX's bytes now."""
        repo = os.path.dirname(os.path.abspath(sandbox))
        with self.lock:
            ck = (sandbox, filename)
            if ck not in self.closures:
                self.closures[ck] = law_inputs(sandbox, filename, [], parsed=self.parsed)
            base, why = self.closures[ck]
        if why:
            return None, [], why
        # the closure is shared by every proof of the law (walked once per lane); the target is this proof's own,
        # resolved exactly as _prove_one resolves it before tampering
        rel = str(pr.get("file") or "") if isinstance(pr, dict) else ""
        if not rel:
            return None, [], "the proof names no file"
        tgt = os.path.normpath(resolve_proof_target(sandbox, rel))
        if not (_inside(repo, tgt) and os.path.isfile(tgt)):
            return None, [], "the tampered target %r is not a file inside the sandbox" % rel
        inputs = sorted(set(base) | {tgt})
        h = hashlib.sha256(b"heart2 P3 key v1\0")
        h.update(str(filename).encode("utf-8", "replace") + b"\0")
        h.update(_proof_key(pr).encode("utf-8", "replace") + b"\0")
        h.update(json.dumps(gate_spec(name), sort_keys=True, default=str).encode("utf-8", "replace") + b"\0")
        rels = []
        for p in inputs:
            with self.lock:
                d = _sha_file(p, self.memo)
            rel = os.path.relpath(p, repo).replace(os.sep, "/")
            if d is None:
                return None, [], "%s cannot be read" % rel
            h.update(rel.encode("utf-8", "replace") + b"\0" + d.encode("ascii") + b"\0")
            rels.append(rel)
        return h.hexdigest(), rels, None

    def count(self, what):
        with self.lock:
            setattr(self, what, getattr(self, what) + 1)

    def say_once(self, name, why, line):
        with self.lock:
            first = (name, why) not in self._said
            self._said.add((name, why))
        if first:
            self.say(line)

    def reused_at(self, name, idx, ms):
        """Record that proof `idx` of `name` was served from an entry measured at `ms` (epoch ms)."""
        with self.lock:
            self.reused[(name, idx)] = ms

    def lookup(self, key):
        """The stored entry for `key`, only when it says PROVEN and carries a readable provedAt; anything else in the
        file is not a shortcut. A verdict nobody can date cannot keep its age in the census, so it is re-proved."""
        with self.lock:
            e = self.entries.get(key)
        if not (isinstance(e, dict) and isinstance(e.get("provedAt"), (int, float))
                and not isinstance(e.get("provedAt"), bool)):
            return None
        return e if isinstance(e, dict) and e.get("verdict") == PROVEN else None

    def store(self, key, entry):
        """Bank one PROVEN in memory; flush() writes the file (once per gate, and at the end of the run)."""
        with self.lock:
            self.entries[key] = entry
            if len(self.entries) > CACHE_MAX:
                for k in sorted(self.entries, key=lambda k: self.entries[k].get("provedAt") or 0)[
                        :len(self.entries) - CACHE_MAX]:
                    self.entries.pop(k, None)
            self.dirty = True

    def flush(self):
        """Write the file atomically when something was banked since the last write. -> True when written"""
        with self.lock:
            if not self.dirty:
                return False
            body = {"_why": "#42 P3 - PROVEN verdicts this machine may reuse at push time, keyed by a digest of every "
                            "byte each depends on (tv/heart2.py law_inputs). Per machine, never committed.",
                    "entries": self.entries}
            tmp = self.path + ".tmp"
            # ⛔ IT NEVER EDITS A GUARD: the only file this object may write is one named like CACHE - the real one
            # beside .heart2.json, or a law's fixture copy of it. Any other path is refused, and said. The refusal sits
            # DIRECTLY above the write because the instruments law admits this write on the guard expression, read
            # from the lines just before the open - the first cut left it eight lines up, outside that window.
            if os.path.basename(self.path) != os.path.basename(CACHE):
                self.say("  #42 P3 CACHE: refusing to write %s - a verdict cache is only ever named %s"
                         % (self.path, os.path.basename(CACHE)))
                return False
            try:
                with io.open(tmp, "w", encoding="utf-8") as fh:
                    json.dump(body, fh, sort_keys=True)
                os.replace(tmp, self.path)
                self.readable, self.dirty = True, False
                return True
            except Exception as _e:
                # a cache that cannot be written costs the next push a re-prove, never this push its verdict - said
                self.say("  #42 P3 CACHE: could not write %s (%s) - what this run proved is not banked"
                         % (os.path.basename(self.path), type(_e).__name__))
                return False

    def summary(self, n_total):
        return ("#42 P3 CACHE: %d of %d proof(s) reused from the cache (byte-identical inputs, not re-run) · %d proved "
                "and banked · %d missed and re-proved · %d not cacheable (ran, never banked) · %d moved under their "
                "proof (not banked)" % (self.hits, n_total, self.stores, self.misses, self.unkeyable, self.moved))


def open_cache(say=print):
    """The cache prove(push=True) hands to _prove_push -> _VerdictCache | None (HEART2_PROVE_CACHE=0: closed, said)."""
    if str(os.environ.get("HEART2_PROVE_CACHE", "1")).strip().lower() in ("0", "no", "off", "false"):
        say("  #42 P3 CACHE: OFF for this run (HEART2_PROVE_CACHE=0) - every proof runs, nothing is banked")
        return None
    return _VerdictCache(say=say)


def _age_say(ms):
    try:
        s = max(0, int(time.time() - float(ms) / 1000.0))
    except (TypeError, ValueError):
        return "an UNKNOWN time"
    return "%dm" % (s // 60) if s < 3600 else "%.1fh" % (s / 3600.0) if s < 86400 else "%.1fd" % (s / 86400.0)


def _declares_widths(proofs):
    """#42 — does any proof of this gate declare the viewports its defect shows at?"""
    return any(isinstance(pr, dict) and "widths" in pr for pr in (proofs or []))


def _proof_key(pr):
    """#42 — one red-proof as a comparable string: two entries are the same declaration exactly when these agree."""
    return json.dumps(pr, sort_keys=True, default=str)


def push_order(have, base_proofs=None, changed=None, anchor_off=None):
    """#42 P2 — the order a push-time run proves in, the likeliest to fail FIRST. -> ({gate: [idx]}, [gate], counts)

    have         [(name, filename, proofs)]
    base_proofs  {filename: [proof] | None} as the push base holds them - [] for a gate file the base does not have
                 (every entry NEW), None for one whose base RED_PROOF cannot be read (nothing counts as changed there);
                 the whole argument None = the base is unknown, so no entry ranks as changed (the caller says so)
    changed      set of repo-relative paths changed since the base, or None (unknown)
    anchor_off   callable(proof) -> True when its anchor does not match as declared in the tree being proved

    Score per proof: 4 anchor off · 2 entry new or changed · 1 its tampered file changed. Ties keep RED_PROOF order;
    gates go by their best-scored proof, ties in the order given. It ORDERS - it decides no verdict (_prove_one does).
    Pure, so the law drives it with fixtures."""
    order, rank, counts = {}, {}, {"anchor": 0, "entry": 0, "target": 0}
    for pos, (name, filename, proofs) in enumerate(have):
        base = None if base_proofs is None else base_proofs.get(filename)
        seen = None if base is None else set(_proof_key(x) for x in base)
        scores = []
        for i, pr in enumerate(proofs or []):
            sc = 0
            if anchor_off is not None and anchor_off(pr):
                sc += 4
                counts["anchor"] += 1
            if seen is not None and _proof_key(pr) not in seen:
                sc += 2
                counts["entry"] += 1
            tgt = _proof_target_rel(pr)
            if changed is not None and tgt and tgt in changed:
                sc += 1
                counts["target"] += 1
            scores.append((-sc, i))
        order[name] = [i for _s, i in sorted(scores)]
        rank[name] = (min([s for s, _i in scores] or [0]), pos)
    return order, sorted(order, key=lambda n: rank[n]), counts


def _proof_target_rel(pr):
    """#42 — a proof's tampered file as a repo-relative path (tv/ first, then the root: resolve_proof_target's rule)."""
    rel = str((pr or {}).get("file") or "") if isinstance(pr, dict) else ""
    if not rel:
        return None
    return os.path.relpath(resolve_proof_target(HERE, rel), REPO).replace(os.sep, "/")


def _git(*args):
    """#42 — one read-only git question about this repo. -> (ok, stdout)"""
    try:
        r = subprocess.run(["git", "-C", REPO] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=30)
    except Exception as _e:
        # the question could not be asked: said as a failed answer (ok False), which the caller reports as UNKNOWN
        return False, "git %s: %s" % (args[0] if args else "", type(_e).__name__)
    return r.returncode == 0, (r.stdout or b"").decode("utf-8", "replace")


def _push_facts(have, say):
    """#42 — what push_order needs, read from git and the tree being proved. -> (base | None, order, gates, counts)"""
    base = None
    for ref in ("@{push}", "origin/main"):          # the hook's own order for "what this push changes"
        ok, out = _git("rev-parse", "--verify", "--quiet", ref)
        if ok and out.strip():
            base = ref
            break
    changed, base_proofs = None, None
    if base:
        ok, out = _git("diff", "--name-only", base)   # the base against the tree being proved (the sandbox copies it)
        changed = set(l.strip() for l in out.splitlines() if l.strip()) if ok else None
        base_proofs = {}
        for _n, filename, _p in have:
            rel = os.path.relpath(os.path.join(HERE, filename), REPO).replace(os.sep, "/")
            ok, src = _git("show", "%s:%s" % (base, rel))
            if not ok:
                base_proofs[filename] = []           # the base has no such file: every entry is NEW
                continue
            try:
                # the SAME reader the prover uses, never a second one; read in memory - nothing is written
                base_proofs[filename] = _red_proofs_of_tree(ast.parse(src))
            except SyntaxError:
                base_proofs[filename] = None         # the base's file will not parse: UNKNOWN, nothing ranks as changed
    texts = {}

    def _anchor_off(pr):
        # ⚠ AN ORDERING HINT, NOT A VERDICT: _prove_one alone decides INVALID. This only puts the proof it will decide
        # INVALID first, so a rotted anchor refuses the push in one clean run instead of after every other proof.
        rel, find = str(pr.get("file") or ""), str(pr.get("find") or "")
        if not rel or not find:
            return True
        tgt = resolve_proof_target(HERE, rel)
        if tgt not in texts:
            texts[tgt] = _read_text(tgt)
        if texts[tgt] is None:
            return True
        got, want = texts[tgt].count(find), pr.get("matches")
        try:
            return got < 1 or (want is not None and got != int(want))
        except (TypeError, ValueError):
            return True        # a count nobody can read: _prove_one will refuse it, so it goes first

    order, gates, counts = push_order(have, base_proofs, changed, _anchor_off)
    return base, order, gates, counts


def _browser_slot(name):
    """#42 — the lock a gate is proved under at push time (a browser gate's), or a context that holds nothing."""
    import contextlib
    return _PUSH.browser_slot(name) if _PUSH is not None else contextlib.nullcontext()


def _prove_push_one(sandbox, name, filename, pr, idx, say, why):
    """#42 — ONE proof at push time: reused from the verdict cache when every keyed byte is identical (P3), otherwise
    run at the widths it declares and banked only when it came back PROVEN. -> verdict (the PUSH TIME block above)"""
    cache = _PUSH.cache if _PUSH is not None else None
    key = None
    if cache is not None:
        label = "%s[%d]" % (name, idx)
        # ⚠ THE CACHE MAY COST A RE-PROVE, NEVER A VERDICT. key_for raising here (a RecursionError from ast.parse on a
        # pathological module, a relpath across volumes, anything unforeseen) would have been recorded BLIND by
        # _prove_gate_push and refused the push over the cache's own bookkeeping. Caught: UNKEYABLE, said, and the
        # proof runs exactly as it would with no cache at all.
        try:
            key, rels, kwhy = cache.key_for(sandbox, name, filename, pr)
        except Exception as _ke:
            key, rels, kwhy = None, [], "taking its key raised %s (%s)" % (type(_ke).__name__, str(_ke)[:80])
        if key is None:
            cache.count("unkeyable")
            cache.say_once(name, kwhy, "     %-52s   ↳ #42 P3: not cacheable - %s; every proof of this law runs on "
                                       "every push" % (label, kwhy))
        else:
            hit = cache.lookup(key)
            if hit is not None:
                cache.count("hits")
                # the census keeps the age this proof was MEASURED at, never this run's clock [[stale-reading]]
                cache.reused_at(name, idx, hit["provedAt"])
                say("     %-52s %s (cached %s: %d byte-identical input(s), proved %s ago%s - not re-run)"
                    % (label, PROVEN, key[:8], len(hit.get("inputs") or rels), _age_say(hit.get("provedAt")),
                       (" at %s" % hit["at"]) if hit.get("at") else ""))
                return PROVEN
            cache.count("misses")
    v = _prove_push_one_run(sandbox, name, filename, pr, idx, say, why)
    if key is not None and v == PROVEN:
        # ⚠ KEYED AGAIN AFTER THE RUN: the tamper wrote and restored the target, and a law may write beside itself; a key
        # that moved means the bytes proved are not the bytes on disk, and a PROVEN banked under them would be a lie.
        # And the same rule as above: a key that cannot be taken again is a tree that moved - PROVEN stands.
        _how = "its key changed while it ran"
        try:
            again, rels2, _w2 = cache.key_for(sandbox, name, filename, pr)
        except Exception as _ke:
            again, _how = None, "its key could not be taken again: %s" % type(_ke).__name__
        if again == key:
            try:
                import law_widths as _LW
                try:
                    _at = _LW.declared(pr)
                except ValueError:
                    _at = None
                cache.store(key, {"verdict": PROVEN, "gate": name, "proof": idx, "why": str(pr.get("why") or "")[:120],
                                  "at": _LW.label(_at) if _at else "", "provedAt": int(time.time() * 1000),
                                  "target": str(pr.get("file") or ""), "inputs": rels})
                cache.count("stores")
            except Exception as _se:
                cache.count("moved")
                say("     %-52s   ↳ #42 P3: could not be banked (%s) - PROVEN stands, nothing is banked"
                    % ("%s[%d]" % (name, idx), type(_se).__name__))
        else:
            cache.count("moved")
            say("     %-52s   ↳ #42 P3: the tree moved under this proof (%s) - PROVEN stands, "
                "nothing is banked" % ("%s[%d]" % (name, idx), _how))
    return v


def _prove_push_one_run(sandbox, name, filename, pr, idx, say, why):
    """#42 — the run itself: ONE proof at the widths it declares (the PUSH TIME block above). -> verdict"""
    label = "%s[%d]" % (name, idx)
    widths = None
    if isinstance(pr, dict) and "widths" in pr:
        import law_widths as _LW
        try:
            widths = _LW.declared(pr)
        except ValueError as _we:
            say("     %-52s %s — its 'widths' cannot be read (%s): a declaration nobody can read is refused, never "
                "guessed at" % (label, INVALID, _we))
            return INVALID
    if not widths:
        return _prove_one(sandbox, name, filename, pr, idx, say, why=why)
    v = _prove_one(sandbox, name, filename, pr, idx, say, widths=widths, why={})
    if v != UNPROVABLE:
        return v
    # ⚠ AN UNPROVABLE AT A SAMPLE IS NOT KEPT: it is not failed, so keeping it would let a restriction that broke the
    # clean run wave through a proof the full run might find BLIND. The full run's verdict is the one that stands.
    say("     %-52s   ↳ #42: its declared widths could not judge it - re-proved at EVERY width; that verdict stands"
        % label)
    return _prove_one(sandbox, name, filename, pr, idx, say, why=why)


def _push_gate_verdict(per):
    """#42 — a push-time gate's verdict from its proofs' (None = NOT RUN). A failure counts wherever it was found; a
    gate the stop cut short is NOT_RUN - never PROVEN on the proofs that happened to run first."""
    got = [v for v in per if v is not None]
    if BLIND in got:
        return BLIND
    if INVALID in got:
        return INVALID
    if len(got) < len(per):
        return NOT_RUN
    # #145 (the v3546 eye) - every proof judged only elsewhere is UNPROVABLE here, on the push path as on _prove_gate's:
    # this list fell through to PROVEN, and a push banked a gate no proof had judged on this PC
    if got and all(v == ELSEWHERE for v in got):
        return UNPROVABLE
    return UNPROVABLE if UNPROVABLE in got else PROVEN


def _prove_gate_push(sandbox, name, filename, proofs, say, run):
    """#42 — one gate's proofs at push time: in the run's order, each at its declared widths, the whole run stopped at
    the first failure. -> (verdict | NOT_RUN, [verdict | None per proof, in RED_PROOF order])

    The per-proof rule is _prove_gate's - a proof that raises is BLIND and is recorded - only the order, the widths and
    the stop are new."""
    got = {}
    for i in (run.order.get(name) or list(range(len(proofs)))):
        if run.stop.is_set():
            break
        why = {}
        try:
            got[i] = _prove_push_one(sandbox, name, filename, proofs[i], i, say, why)
        except Exception as _pe:
            say("    proof %d raised %s — recorded BLIND: %s" % (i, type(_pe).__name__, str(_pe)[:120]))
            got[i] = BLIND
        reason = {BLIND: "the tamper ran and the law stayed GREEN",
                  INVALID: "the red-proof cannot tamper as declared"}.get(got[i])
        if got[i] == UNPROVABLE and why.get("red"):
            reason = "the law is ALREADY RED untampered, so no proof of it can be judged"
        if reason:
            if run.fail(name, i, got[i], reason):
                say("  ⛔ #42 FAIL FAST — %s[%d] %s: %s. The run stops here: every proof not yet run is NOT RUN, and "
                    "the push is refused on this one." % (name, i, got[i], reason))
            break
    per = [got.get(i) for i in range(len(proofs))]
    if run.cache is not None:
        run.cache.flush()          # P3: what this gate proved reaches the disk now, not only at the end of the run
    return _push_gate_verdict(per), per


def _prove_push(have, say, stopped=None, cache=None, blank=None):
    """#42 — prove() at push time. -> ({name: verdict}, {name: [verdict | None]}) | (None, None); NOT_RUN gates are left
    OUT of the verdicts (never banked), and a stop is appended to `stopped` for main() to refuse on.
    `cache` (P3) is the _VerdictCache prove(push=True) opened; None - every other caller - runs every proof."""
    global _PUSH
    _nw = sum(1 for _n, _f, _p in have for _pr in _p if isinstance(_pr, dict) and "widths" in _pr)
    _np = sum(len(_p) for _n, _f, _p in have)
    say("  #42 PUSH TIME: %d of %d proof(s) declare the widths their defect shows at and run only there; the other %d "
        "run at every width. The full sweep stays run_gates' and CI's." % (_nw, _np, _np - _nw))
    base, order, gates, counts = _push_facts(have, say)
    say("  #42 FAIL FAST: likeliest to fail first - %d anchor(s) off, %d entr(ies) new or changed since %s, %d whose "
        "tampered file changed; the run stops at the first BLIND / INVALID / clean-run red."
        % (counts["anchor"], counts["entry"], base or "an UNKNOWN base (neither @{push} nor origin/main resolves - "
           "nothing ranks as changed)", counts["target"]))
    # the import CLOSURE, not the gate's own imports: a gate that starts Chrome through a helper holds the lock too
    _unk = []
    browser = browser_gates([(n, f) for n, f, _p in have], unclassified=_unk) | set(
        n for n, _f, p in have if _declares_widths(p))
    if browser:
        say("  #42 ONE BROWSER AT A TIME: %d gate(s) reach a browser through their imports (any depth) and are proved "
            "one after another: %s" % (len(browser), ", ".join(sorted(browser)[:6]) + (" …" if len(browser) > 6 else "")))
    if _unk:
        say("  #42 ⚠ %d gate(s) import a file nobody could read or parse, so whether they start a browser is UNKNOWN - "
            "they hold the lock too: %s" % (len(_unk), ", ".join(sorted(_unk)[:6])))
    by = dict((n, (n, f, p)) for n, f, p in have)
    run = _PushRun(order, browser, cache)
    _prev, _PUSH = _PUSH, run
    try:
        results, per_proof = _prove_gates([by[n] for n in gates], say, blank=blank)
    finally:
        _PUSH = _prev
    if cache is not None:
        cache.flush()
        say("  " + cache.summary(_np))
    if results is None:
        return None, None
    not_run = sorted(n for n, v in results.items() if v == NOT_RUN)
    results = dict((n, v) for n, v in results.items() if v != NOT_RUN)
    if cache is not None:
        # ⚠ A REUSED PROOF KEEPS THE TIME IT WAS MEASURED. A PROVEN gate standing on any cached proof is only as fresh
        # as the OLDEST of them (a proof that ran now is newer than any entry), so the census stamps that gate with
        # that time and not this run's clock. Only PROVEN: a BLIND / INVALID / UNPROVABLE came from a proof that RAN.
        # prove() reads cache.measured and hands it to _write_state. [[stale-reading]] [[inherited-claim-is-not-evidence]]
        _ages = {}
        for (_gn, _i), _ms in list(cache.reused.items()):
            if results.get(_gn) == PROVEN:
                _ages[_gn] = min(_ages[_gn], _ms) if _gn in _ages else _ms
        cache.measured = _ages
        if _ages:
            say("  #42 P3 CACHE: %d gate(s) stand on reused proofs, so the census keeps the age each was MEASURED at "
                "(oldest %s ago), never this run's clock" % (len(_ages), _age_say(min(_ages.values()))))
    if run.first:
        _n, _i, _v, _why = run.first
        _unrun = sum(1 for _p in per_proof.values() for x in _p if x is None)
        say("")
        say("  ⛔ #42 STOPPED at the first failure: %s[%d] %s — %s." % (_n, _i, _v, _why))
        say("     %d of %d proof(s) NOT RUN%s. Nothing unrun is banked or passed: the push is refused on the failure "
            "above. Reproduce: python3 tv/heart2.py --prove %s --push" % (
                _unrun, _np, (" (%d gate(s) never started: %s)" % (len(not_run), ", ".join(not_run[:6])))
                if not_run else "", _n))
        if stopped is not None:
            stopped.append(run.first)
    return results, per_proof


def _prove_gate(sandbox, name, filename, proofs, say):
    """Every proof of ONE gate, serially, inside ONE sandbox. -> (verdict, [verdict per proof])

    ⚠ LIFTED OUT OF prove()'s INNER LOOP WHEN THE OUTER LOOP WAS SPLIT INTO LANES — it is not a
    second copy of that policy, it is the only one, and both the one-lane and the many-lane paths
    call this same function. A rule that exists twice is how this repo's defects start.
    [[copy-drift]]
    #42 — at push time (and only then) the gate goes to _prove_gate_push: the same per-proof rule, plus the order, the
    declared widths and the stop.
    """
    if _PUSH is not None:
        return _prove_gate_push(sandbox, name, filename, proofs, say, _PUSH)
    verdicts = []
    _CLEAN.runs = {}                                     # REG-1669 — this gate's proofs share one clean run
    try:
        verdicts = _prove_gate_proofs(sandbox, name, filename, proofs, say)
        verdicts = _closing_clean(name, verdicts, say)
    finally:
        _CLEAN.runs = None
    # REG-1686 — every proof judged only elsewhere: nothing was proven HERE, so the gate is not PROVEN here
    if verdicts and all(v == ELSEWHERE for v in verdicts):
        return UNPROVABLE, verdicts
    return (BLIND if BLIND in verdicts
            else INVALID if INVALID in verdicts
            else UNPROVABLE if UNPROVABLE in verdicts
            else PROVEN), verdicts


def _closing_clean(name, verdicts, say):
    """REG-1669 — the gate's proofs shared one clean run; it must still be green after the last of them. -> verdicts

    A law whose state drifted across its proofs could otherwise go red for the drift and be credited with catching
    the tamper. Only when a clean run WAS shared; a red or unknown closing run keeps no PROVEN of this gate
    (UNPROVABLE, said).

    REG-1677 (the v3543 cross-family eye) — AND A REUSED CLEAN RUN MAY NOT BANK A BLIND OR AN INVALID EITHER. A proof
    judged on the cached green could miss its anchor (INVALID) or stay green tampered (BLIND) because an earlier proof's
    run left the sandbox changed - where its own fresh clean run would have gone red first (UNPROVABLE). BLIND and
    INVALID go on the census's blind list, and one BLIND shuts every lock on that PC. So the closing run is asked
    whenever a reused verdict could be banked (PROVEN, BLIND or INVALID), and a red, unknown or RAISING closing run
    makes PROVEN and every reused BLIND/INVALID UNPROVABLE; a first proof's BLIND, judged on its own fresh clean run,
    stands."""
    runs = getattr(_CLEAN, "runs", None) or {}
    shared = [r for r in runs.values() if r.get("reused")]
    if not shared or not any(v in (PROVEN, BLIND, INVALID) for v in verdicts):
        return verdicts
    _reused = set()
    for r in shared:
        _reused.update(r.get("by") or ())
    for r in shared:
        try:
            ok, tail = r["again"]()
        except Exception as _ce:                         # REG-1677 — the closing run raising is UNKNOWN, never a BLIND gate
            ok, tail = None, "the closing clean run raised %s" % type(_ce).__name__
        if not ok:
            say("     %-52s %s - the CLOSING clean run is %s (%s): its proofs shared one clean run and the sandbox did "
                "not stay clean across them, so no PROVEN of this gate is kept, and no BLIND judged on the shared run"
                % (name, UNPROVABLE, "UNKNOWN" if ok is None else "RED", str(tail)[:60]))
            return [UNPROVABLE if (v == PROVEN or (j in _reused and v in (BLIND, INVALID))) else v
                    for j, v in enumerate(verdicts)]
    return verdicts


def _prove_gate_proofs(sandbox, name, filename, proofs, say):
    """Every proof of ONE gate, serially. -> [verdict per proof] (the loop _prove_gate has always run)"""
    verdicts = []
    for i, pr in enumerate(proofs):
        # ⚠⚠ ONE BAD PROOF MAY NOT TAKE THE WHOLE RUN WITH IT. This loop sits inside a
        # `try: ... finally:` with NO `except`, so an exception from _prove_one escaped
        # `prove()` entirely — and `_write_state(results)` is BELOW that try, so nothing
        # was ever banked. The census in control_app.py then read a file nothing had
        # refreshed and reported from it, indefinitely.
        # MEASURED 2026-09-17: a 4-tuple proof raised AttributeError on `pr.get("file")`,
        # 12 gates declared them, and the organ that exists to ask "can my own gates still
        # go red" died on the first one while still reporting a verdict.
        # The shape is fixed at the reader (_normalise_proofs); this is the SECOND lock,
        # because the next unreadable proof will be a shape nobody has thought of yet.
        # [[the-unjoined-end]] [[unknown-stays-unknown]]
        try:
            v = _prove_one(sandbox, name, filename, pr, i, say)
        except Exception as _pe:
            say("    proof %d raised %s — recorded BLIND, run continues: %s"
                % (i, type(_pe).__name__, str(_pe)[:120]))
            v = BLIND
        verdicts.append(v)
    return verdicts


def _prove_lane(lane, work, out, lock, sink, built, buffered=True, blank=None):
    """ONE lane: build a sandbox nobody else touches, then drain the shared queue into `out`.

    ⚠⚠ EVERY GATE THIS LANE TAKES COMES BACK WITH A ROW, INCLUDING WHEN THE LANE DIES HOLDING IT.
    A dropped row does not read as a failure, it reads as a shorter census — and v2882 already
    cost this file a "0 blind of 278" that was really 279 gates with one never asked about. A
    lane that RAISES marks the gate it was holding BLIND — the same policy _prove_gate applies to
    a single proof that raises, and BLIND exits non-zero. A lane that cannot build a sandbox takes
    no gate at all, so the healthy lanes still prove them.
    [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
    """
    say = _LaneSay(sink, lock, buffered=buffered)
    holding = []
    root = None
    _LANE_LOCAL.n = lane          # #144 — _run_gate stamps this lane's ports into each gate
    try:
        sandbox, root = make_sandbox(say)
        built.append(bool(sandbox))
        if not sandbox:
            # ⚠ IT TAKES NOTHING. The first cut drained the whole queue into UNPROVABLE here, so
            # ONE lane that lost a race for disk would have STOLEN every gate from the healthy
            # lanes and reported the lot as "already red untampered" — a confident wrong sentence
            # about 500 laws, produced by the failure of one copy. A lane with no sandbox proves
            # nothing and says so; the others keep the work. If NO lane can build one, the queue
            # goes undrained and _prove_gates answers "nothing was proven", which is the same
            # answer the old single-sandbox loop gave. [[unknown-stays-unknown]]
            say("  ⚠ lane %d could not build a sandbox and therefore takes NO gate — the other "
                "lanes keep the work. UNKNOWN is not a verdict this lane may hand out." % lane)
            return
        say("  lane %d sandbox: %s" % (lane, sandbox))
        say.flush()
        while True:
            # #42 — a STOPPED push-time run takes no further gate; _prove_gates names what is left NOT RUN
            if _PUSH is not None and _PUSH.stop.is_set():
                break
            try:
                name, filename, proofs = work.get_nowait()
            except Exception:
                break
            holding = [(name, proofs)]
            try:
                with _browser_slot(name):          # #42 — a browser gate waits for the one browser at push time
                    v, per = _prove_gate(sandbox, name, filename, proofs, say)
            except Exception as _ge:
                say("    %s raised %s outside its own proofs — recorded BLIND, the run continues: "
                    "%s" % (name, type(_ge).__name__, str(_ge)[:120]))
                v, per = BLIND, [BLIND] * len(proofs)
                if blank is not None:
                    with lock:
                        blank.add(name)        # raised before any proof judged it: BLIND, and still owed
            with lock:
                out[name] = (v, per)
            holding = []
            # REG-1676 — a slice banks what it has proved AS IT GOES (see _slice_banker, set on _GATE_HOOK by prove()).
            # Never fatal: a bank that fails is said and the lane keeps proving - the slice's own write still runs.
            _hook = _GATE_HOOK.get("fn")
            if _hook is not None:
                try:
                    _hook(out, lock)
                except Exception as _be:
                    say("    ⚠ banking the slice so far raised %s - it is retried after the next gate"
                        % type(_be).__name__)
            say.flush()
    except Exception as _le:
        say("  ⚠ lane %d died: %s: %s" % (lane, type(_le).__name__, str(_le)[:140]))
        for _n, _p in holding:
            with lock:
                if _n not in out:
                    out[_n] = (BLIND, [BLIND] * len(_p))
                    if blank is not None:
                        blank.add(_n)          # the lane died holding it: BLIND, and still owed
    finally:
        _LANE_LOCAL.n = None
        say.flush()
        if root:
            _drop_sandbox(root)


#: REG-1676 — the per-gate hook the lanes call after recording a gate (prove() sets it for a SLICE, clears it after). A
#: module slot rather than a parameter so the lane and _prove_gates keep their shapes - one prover runs per process.
_GATE_HOOK = {"fn": None}
#: REG-1676 — how often (seconds) a slice may write its verdicts so far into the census; the gate scan costs ~1 s on his
#: Mac and a few on the ALT, so a bank per gate is throttled, and the slice's final write is never skipped
SLICE_BANK_EVERY_S = 60


def _slice_banker(blank, say=print, every_s=None):
    """REG-1676 — A SLICE BANKS WHAT IT HAS PROVED AS IT GOES. -> callable(out, lock)

    MEASURED on his ALT 2026-10-01: a 27-gate slice proved four once-BLIND gates PROVEN, then stood aside at "only 972 MB
    of memory left" before its end - and a slice wrote the census only at its end, so 70+ minutes of verdicts were
    thrown away, the BLIND records stood, and every lock on that PC (the river) stayed shut. Now each finished gate is
    banked through the same _write_state a slice ends with (a partial result merged over the census, atomically), at
    most once per `every_s`; a stand-aside then loses at most the gates since the last bank, and the lane reads the
    banked ones as progress, never a failure."""
    st = {"last": 0.0, "lk": threading.Lock()}
    every = SLICE_BANK_EVERY_S if every_s is None else every_s

    def bank(out, lock):
        if not st["lk"].acquire(False):
            return                                  # a bank is already writing: the next gate banks
        try:
            now = __import__("time").time()
            if now - st["last"] < every:
                return
            with lock:
                snap = {k: v for k, (v, _p) in out.items()}
                unm = set(blank or ())
            if snap:
                _write_state(snap, stamp=False, unmeasured=unm)
                st["last"] = now
        finally:
            st["lk"].release()
    return bank


def _prove_gates(have, say=print, workers=None, blank=None):
    """Prove every gate in `have` across isolated lanes. -> ({name: verdict}, {name: [verdicts]})

    (None, None) means NOT ONE lane could build a sandbox — the same "nothing was proven" answer
    the old single-sandbox loop gave, so the caller still banks no state. A run where SOME lanes
    built a sandbox is not that: those gates were really judged, and the rest say UNPROVABLE.
    """
    # imported HERE and not at module scope on purpose: control_app.py imports heart2 on every
    # census read, and it never proves anything. [[copy-drift]]
    import queue as _queue
    from concurrent.futures import ThreadPoolExecutor
    if not have:
        return {}, {}
    n = prove_workers(len(have), say) if workers is None else max(1, int(workers))
    n = max(1, min(n, len(have)))
    work = _queue.Queue()
    for item in have:
        work.put(item)
    out, lock, built = {}, threading.Lock(), []
    blank = blank if blank is not None else set()      # filled under `lock` by the lanes, and by the sweep below
    say("  proving %d gate(s) in %d lane(s), one throwaway sandbox each" % (len(have), n))
    # ⚠ RESTORED IN A `finally`, because a module global left widened would silently extend every
    # later single-lane deadline in the same process — control_app.py imports this module and
    # keeps it. A dial that does not spring back is a dial nobody set. [[label-outlived-referent]]
    global DEADLINE_SCALE
    _prev_scale = DEADLINE_SCALE
    DEADLINE_SCALE = _deadline_scale(n, say=say)
    try:
        if n == 1:
            _prove_lane(1, work, out, lock, say, built, buffered=False, blank=blank)
        else:
            say("  every gate's deadline is x%d while %d lanes are running, because the lanes "
                "make the load themselves" % (DEADLINE_SCALE, n))
            with ThreadPoolExecutor(max_workers=n) as ex:
                futs = [ex.submit(_prove_lane, i + 1, work, out, lock, say, built, True, blank)
                        for i in range(n)]
                for f in futs:
                    _e = f.exception()
                    if _e is not None:
                        # _prove_lane already catches Exception; reaching here means something got
                        # past its own handler, and the gates it was holding are covered by the
                        # missing-row sweep below. Never swallowed.
                        # [[feedback-silence-is-not-evidence]]
                        say("  ⚠ a lane raised past its own handler: %s" % type(_e).__name__)
    finally:
        DEADLINE_SCALE = _prev_scale
    if built and not any(built):
        say("  no lane could build a sandbox — nothing was proven, and that is UNKNOWN, not clean.")
        return None, None
    # ⚠ NOBODY MAY VANISH. Every gate handed in comes back with a row even if the lane holding it
    # died before writing one — an absent row reads as "nothing to see". [[zero-needs-a-denominator]]
    missing = [(nm, prs) for nm, _fn, prs in have if nm not in out]
    if missing and _PUSH is not None and _PUSH.stop.is_set():
        # #42 — a STOPPED push-time run never reached these: NOT RUN, not BLIND - nothing was found wrong with them, and
        # the run is refused on the failure that stopped it, so nothing unrun is ever passed either
        say("  #42 the run stopped before %d gate(s) were reached — NOT RUN: %s"
            % (len(missing), ", ".join(nm for nm, _p in missing[:6])))
        for nm, prs in missing:
            out[nm] = (NOT_RUN, [None] * len(prs))
        missing = []
    if missing:
        say("  ⚠ %d gate(s) were never reached by any lane — recorded BLIND, never dropped: %s"
            % (len(missing), ", ".join(nm for nm, _p in missing[:6])))
        for nm, prs in missing:
            out[nm] = (BLIND, [BLIND] * len(prs))
            blank.add(nm)                      # never reached: nothing measured it, so the census still owes it
    return ({k: v for k, (v, _p) in out.items()},
            {k: p for k, (_v, p) in out.items()})


def prove(only=None, say=print, detail=None, push=False, stopped=None, stamp=True):
    gates = gate_files()
    todo = [(n, f) for n, f in gates if (not only or n in only or f in only)]
    with_proofs = [(n, f, red_proofs_in(f)) for n, f in todo]
    have = [(n, f, p) for n, f, p in with_proofs if p]
    # ⚠ v3476 — THE DENOMINATOR NAMES EVERY STATE. v3473 printed the warning but the count line
    # still filed an unreadable declaration under "do not", and read None (the file will not even
    # parse) as False — so an unparseable gate took the "declares nothing" path. Found by the eye on
    # v3473. None is UNKNOWN, and UNKNOWN gets its own column. [[unknown-stays-unknown]]
    _state = dict((n, red_proof_unreadable(f)) for n, f in todo)
    _unread = [n for n, _f in todo if _state.get(n) is True]
    _unparsed = [n for n, _f in todo if _state.get(n) is None]
    say("  %d gate(s) in scope · %d declare a red-proof · %d do not%s%s"
        % (len(todo), len(have), len(todo) - len(have) - len(_unread) - len(_unparsed),
           (" · %d UNREADABLE" % len(_unread)) if _unread else "",
           (" · %d will not PARSE" % len(_unparsed)) if _unparsed else ""))
    if _unread:
        say("  ⚠ %d DECLARE a RED_PROOF this prover CANNOT READ (ast.literal_eval refused it) — "
            "UNREADABLE, not absent, and none of it has run: %s" % (len(_unread), ", ".join(_unread[:6])))
    if _unparsed:
        say("  ⚠ %d gate file(s) will not PARSE, so whether they declare a proof is UNKNOWN: %s"
            % (len(_unparsed), ", ".join(_unparsed[:6])))
    if not have:
        say("  nothing to prove. That is the BACKLOG, not a clean bill of health.")
        return {}
    _ages = {}
    _blank = set()      # gates written BLIND that no proof measured - never banked as proved against their file
    if push:
        # #42 — hooks/pre-push's run: declared widths, likeliest failure first, stop at the first, one browser at a time,
        # and (P3) a PROVEN reused only over byte-identical inputs - the cache is opened HERE and nowhere else
        _GATE_HOOK["fn"] = None         # #145 (the v3545 eye) - a push banks once at the end, never through a slice's banker
        _cache = open_cache(say)
        results, per_proof = _prove_push(have, say, stopped, cache=_cache, blank=_blank)
        _ages = dict(getattr(_cache, "measured", None) or {})     # gate -> oldest provedAt among its reused proofs
        if results is not None and not results:
            # ⚠ A STOP BEFORE ANY GATE WAS JUDGED TO THE END IS NOT AN EMPTY RUN. _write_state reads an empty result as a
            # FULL run that proved nothing and would wipe every standing proof (provedGates, blind) - so nothing is
            # written, and the stop itself refuses the push. [[unknown-stays-unknown]]
            say("  #42 no gate was judged to the end, so the census is left exactly as it was")
            return {}
    else:
        # REG-1676 — a SLICE (stamp=False) banks as it goes; a full run keeps its one write at the end
        _GATE_HOOK["fn"] = None if stamp else _slice_banker(_blank, say)
        try:
            results, per_proof = _prove_gates(have, say, blank=_blank)
        finally:
            _GATE_HOOK["fn"] = None     # #145 (the v3545 eye) - a raise must not leave this slice's banker installed
    if results is None:
        return {}
    # `detail` is the per-PROOF verdict list, and it exists so an A/B can compare the lanes
    # against the serial loop proof by proof. "Both green" is not the same answer as "the same
    # answers": a faster prove that flips ONE verdict is a broken gate, not a speedup.
    if detail is not None:
        detail.update(per_proof)
    if stamp:
        _write_state(results, measured=_ages, unmeasured=_blank)
    else:
        _write_state(results, measured=_ages, stamp=False, unmeasured=_blank)  # #99 — the slice flag only with --slice
    return results


def _write_state(results, measured=None, stamp=True, unmeasured=None):
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
    _unm = set(unmeasured or ())
    for _n in (results or {}):
        # REG-1623 (the #231 eye on b135b25a) - a gate NOBODY MEASURED was not tested now: it keeps its old stamp (or
        # none). A fresh stamp here is the "this run tested it" the comment above promises, and it was not.
        if _n in _unm:
            continue
        _seen[_n] = _now_ms
    # ⚠ #42 P3 — A GATE THAT STANDS ON REUSED PROOFS WAS NOT MEASURED NOW. `measured` (gate -> epoch ms) is the oldest
    # provedAt among the cached proofs a push-time run reused for that gate; stamping it `_now_ms` would make 40 gates
    # read "just now" on a retried push when their proofs ran an hour or a day earlier - the defect the comment beside
    # oldestProofMs in control_app.py records, re-introduced one level down (second eye on the first cut). The stamp
    # can never be later than now, and a gate this run did not judge takes no stamp from the map.
    # [[stale-reading]] [[inherited-claim-is-not-evidence]]
    for _n, _ms in (measured or {}).items():
        if _n in (results or {}) and isinstance(_ms, (int, float)) and not isinstance(_ms, bool):
            _seen[_n] = min(_now_ms, int(_ms))
    _seen = {k: v for k, v in _seen.items() if k in _known}   # a gate that is gone keeps no stamp
    # ⚠⚠ #99 — A SLICE MAY NOT SPEAK FOR THE GATES IT DID NOT RUN. Every run stamped the whole-tree fingerprint, which is
    # right at push time (the hook proves exactly the gates that changed) and for a full run, and would be a lie from a
    # slice: one slice of a PC's first census would open every lock with 400 gates never run there. So each gate keeps
    # the digest of the file it was proved against (`gateShas`), and a slice (stamp=False) stamps the fingerprint only
    # when no declaring gate is owed any more. Until then the census stays unstamped, may() stays closed, and
    # self_prove proves the rest a slice at a time - which is how a PC he plays on ever finishes. [[unknown-stays-unknown]]
    _shas = gate_shas(gates)
    _gs = dict(prior.get("gateShas") or {}) if isinstance(prior.get("gateShas"), dict) else {}
    for _n in (results or {}):
        # second eye on v3528 (reproduced by reading): BLIND is also what a gate NOBODY MEASURED is written as - the
        # missing-row sweep in _prove_gates, a lane that died holding it, a gate that raised outside its own proofs.
        # Banking its digest said "proved against this file" about a gate that never ran, so it stopped being owed, no
        # slice ever ran it again, and the census read current with it blind - every lock on that PC shut for good over
        # a sandbox that failed once. An unmeasured row stays OWED; a MEASURED blind (the tamper ran and the law stayed
        # green) is banked, or one gate blind on Windows would keep the census from ever finishing. [[unknown-stays-unknown]]
        if _n in _unm:
            _gs.pop(_n, None)
            continue
        _gs[_n] = _shas.get(_n)
    _gs = {k: v for k, v in _gs.items() if k in _known}
    _owed = [n for n in have if not _shas.get(n) or _gs.get(n) != _shas.get(n)]
    # ⚠⚠ REG-1623 (the #231 eye on b135b25a) - A RUN THAT KNOWS IT LEFT A GATE UNMEASURED MAY NOT STAMP. `stamp` let a
    # full or push-time run stamp the tree fingerprint whatever was owed - right for gates it simply did not run (the
    # hook proves only what changed), wrong for a gate it TRIED and could not measure: census_state called that census
    # current, may() stayed shut on the blind name, and the prover - which starts only on a census that is not
    # current - never ran it again. Nor may the PRIOR stamp stand: it can equal the tree's and read current all the
    # same. So no stamp at all: the census reads stale, the owed gate is named, and a slice measures it.
    _unm_owed = [n for n in _owed if n in _unm]
    if _unm_owed:
        _fp_out = None
    else:
        _fp_out = gates_fingerprint(gates) if (stamp or not _owed) else prior.get("gatesFingerprint")
    out.update({
        "gateShas": _gs,
        "sliceOwed": len(_owed),
        "sliceOwedSample": _owed[:12],
        "unstampedWhy": ("%d gate(s) this run could not measure are owed: %s"
                         % (len(_unm_owed), ", ".join(_unm_owed[:6])) if _unm_owed else None),
        "stampedBy": (None if _unm_owed else ("run" if stamp else ("slice-complete" if not _owed else None))),
        "proved": len(_proved),
        "provedGates": sorted(_proved),
        # v2858 — THE SPLIT, because one number hid a 93/7 one. See pixel_gates().
        "pixelTotal": len(_pixel),
        "pixelProved": len(_proved & _pixel),
        "pixelUnclassified": sorted(_pixel_unk),   # v2860 — NOT silently counted as backend
        "gatesFingerprint": _fp_out,   # v2862 — content, not mtime; #99 — a slice stamps only a COMPLETE census
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
    # #99 — tmp + os.replace. A stand-aside can end the prover at any moment and slices write often; a kill inside a
    # plain open(..., "w") left the census truncated, and a census that will not parse is one this file then refuses
    # to write over - every lock shut for good on that PC. [[open-for-write-truncates-first]]
    _tmp = "%s.%d.tmp" % (STATE, os.getpid())
    try:
        with io.open(_tmp, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
        os.replace(_tmp, STATE)
    except BaseException:
        try:
            os.unlink(_tmp)
        except OSError:
            pass
        raise


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


def _at_widths(widths):
    """#42 — ' at 1280x800' on a push-time proof's lines, '' on every other (so those lines read as they always did)"""
    if not widths:
        return ""
    import law_widths as _LW
    return " at %s" % _LW.label(widths)


def _prove_one(sandbox, name, filename, pr, idx, say, widths=None, why=None):
    # REG-1686 — a proof that declared what this PC must have is judged only where it is (see ELSEWHERE above)
    _need = pr.get("needs") if isinstance(pr, dict) else None
    if _need:
        _lacks, _words = host_lacks(_need)
        if _lacks is None and _words.startswith("an undeclared capability"):
            say("     %-52s %s — it declares %s, which no probe knows" % ("%s[%d]" % (name, idx), INVALID, _words))
            return INVALID
        if _lacks:
            say("     %-52s %s — it needs %s, which this PC does not have; it is proven on a PC that does"
                % ("%s[%d]" % (name, idx), ELSEWHERE, _words))
            return ELSEWHERE
    # #42 — `widths` (a push-time proof's own declaration, from _prove_push_one) reaches BOTH runs below, so the clean
    # run and the tampered run measure the same viewports; None = every width, all this function ever did. `why`, when
    # a caller hands one in, learns whether an UNPROVABLE was a law ALREADY RED untampered (the push-time run stops on
    # that) or a run that could not judge at all (a deadline, a missing file - named, never failed).
    _w = {"widths": widths} if widths else {}
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
    # ⚠⚠ v3241 — AN ABSENT COUNT IS NOT A DECLARED 1. `int(pr.get("matches") or 1)` reads a
    # missing key, a real 0 and a real 1 as the same number. That became live the moment
    # _normalise_proofs started handing through 4-tuple proofs, which carry NO count: 32 of them
    # would be silently measured against 1, and the first whose anchor appears twice would be
    # filed INVALID for a declaration nobody ever made.
    # The well-formedness law in test_the_heart_can_see_its_own_instruments already treats None
    # as "nobody declared one" and checks only `got >= 1`. Two readers, one field, two policies
    # is how this repo's defects start. Same rule both sides. Found by a cross-family review of
    # v3240, the version that introduced the None. [[unknown-stays-unknown]] [[copy-drift]]
    _declared = pr.get("matches")
    want = None if _declared is None else int(_declared)
    label = "%s[%d]" % (name, idx)

    if not tgt_rel or not os.path.exists(tgt):
        say("     %-52s %s — %s is not in the sandbox" % (label, UNPROVABLE, tgt_rel or "(no file)"))
        return UNPROVABLE

    # ⚠⚠ REG-1626 — A GATE WHOSE SUBJECT IS NOT ON THIS PC IS UNPROVABLE HERE, NEVER BLIND. The comment beside
    # proof_inputs() always said so ("absent: the sandbox never brought it, so the gate reads UNPROVABLE there") and
    # nothing did it: MEASURED on the ALT 2026-09-30, test_chronicle_template's PROOF_NEEDS (his hand-read footage,
    # which never leaves his Mac) was absent, all 12 laws skipped, the run exited 0, and the gate was filed BLIND -
    # which shuts every lock on that PC for good, over a law about data it will never hold. A PC can only prove what
    # it has; this one says it did not, and why, and asks no run to say otherwise. [[unknown-stays-unknown]]
    _needs = proof_needs_in(filename)
    # REG-1644 (the v3535 cross-family eye) - None is "its PROOF_NEEDS could not be read", never "it needs nothing":
    # make_sandbox and law_inputs both branch on it and this door did not, so a gate with an unreadable declaration went
    # to its clean run, and with its subject absent every law skipped, the run exited 0 and it was filed BLIND - the
    # lock-shut outcome REG-1626 ended for the readable shape. MEASURED 2026-10-01: 0 of 753 gate files hit it today.
    if _needs is None:
        say("     %-52s %s — its PROOF_NEEDS cannot be read, so whether its subject is on this PC is UNKNOWN: "
            "nothing is graded on a guess" % (label, UNPROVABLE))
        if why is not None:
            why["needsUnreadable"] = True
        return UNPROVABLE
    if _needs:
        _gone = [n for n in _needs if not os.path.exists(os.path.normpath(os.path.join(sandbox, n)))]
        if _gone:
            _here = os.path.exists(os.path.normpath(os.path.join(REPO, "tv", _gone[0])))
            say("     %-52s %s — its subject %s is %s (PROOF_NEEDS): nothing to grade here"
                % (label, UNPROVABLE, _gone[0], "not in the sandbox (it IS on this PC - the copy did not bring it)"
                   if _here else "not on this PC - it lives only where it was recorded"))
            if why is not None:
                why["absentSubject"] = _gone[0]
            return UNPROVABLE

    # 1. CLEAN RUN. A gate that is already red in the sandbox can prove nothing.
    _extra, _to, _script = gate_spec(name)
    # ⚠ THE DEADLINE IS THIS PROVER'S PATIENCE, NOT THE LAW. DEADLINE_SCALE is 1 on the
    # single-lane path, so that path is unchanged; with lanes running it widens by a measured
    # factor so a verdict can never be decided by how many copies of the prover are busy.
    _to = int(_to * DEADLINE_SCALE) if _to else _to
    # #42 lever 1 (REG-1710) — at push time, a plain unittest law whose sabotage was caught before is asked only of the
    # cases that caught it. PROVEN there is a proof; anything else falls through to the full proof below, unchanged.
    _rk = _red_key(name, idx, pr) if (_PUSH is not None and not _script and not _extra) else None
    _rids = _red_recall(_rk) if _rk else None
    if _rids and _prove_narrow(sandbox, label, tgt, tgt_rel, find, repl, want, filename, _to, _w, _rids, widths,
                               say) == PROVEN:
        return PROVEN
    _runs = getattr(_CLEAN, "runs", None)
    _ck = (filename, repr(_extra), repr(_script), _at_widths(widths), _to)
    _hit = _runs.get(_ck) if isinstance(_runs, dict) else None
    if _hit is not None:
        ok_clean, tail = _hit["ok"], _hit["tail"]           # REG-1669 — this gate's one clean run
        _hit["reused"] += 1
        _hit.setdefault("by", []).append(idx)                # REG-1677 — which proofs were judged on a reused clean run
    else:
        ok_clean, tail = _run_gate(sandbox, filename, timeout=_to, extra=_extra, script=_script, **_w)
        if isinstance(_runs, dict) and ok_clean is not None:
            _runs[_ck] = {"ok": ok_clean, "tail": tail, "reused": 0,
                          "again": (lambda: _run_gate(sandbox, filename, timeout=_to, extra=_extra,
                                                      script=_script, **_w))}
    if ok_clean is None:
        say("     %-52s %s — clean run%s: %s" % (label, UNPROVABLE, _at_widths(widths), tail))
        return UNPROVABLE
    if not ok_clean:
        say("     %-52s %s — it is ALREADY RED untampered in the sandbox%s (%s)"
            % (label, UNPROVABLE, _at_widths(widths), tail[:60]))
        if why is not None:
            why["red"] = True
        return UNPROVABLE

    with io.open(tgt, encoding="utf-8") as fh:
        original = fh.read()
    got = original.count(find) if find else 0
    # THE CARVED SCAR: a green sabotage is usually the sabotage's fault. Print the count.
    if got < 1:
        say("     %-52s %s — the tamper matched 0 time(s): its anchor is not in the file, so it "
            "changes nothing. The SABOTAGE is wrong, not the law." % (label, INVALID))
        return INVALID
    if want is not None and got != want:
        say("     %-52s %s — the tamper matched %d time(s), expected %d. The SABOTAGE is wrong, "
            "not the law." % (label, INVALID, got, want))
        return INVALID

    # 2. TAMPER
    # ⚠⚠ v3243 — AND THE THIRD READER OF THE SAME FIELD. v3241 made `want` None when nobody
    # declared a count, which is correct for the COMPARISON above — and this line passes it
    # straight to str.replace as the count, where `None` is a TypeError:
    #     "aa".replace("a", "b", None) -> 'NoneType' object cannot be interpreted as an integer
    # So every 4-tuple proof (32 of them, all count-less) would have raised here, at the exact
    # step that does the tampering — the fix for "the prover could not READ them" would have
    # become "the prover crashes while TAMPERING them". Caught by a cross-family review of v3241,
    # the version that introduced the None.
    #
    # One field, three readers: legal-with-no-count (_normalise_proofs), compare-only-if-declared
    # (here and the well-formedness law), and a literal argument to str.replace. Same rule
    # everywhere: nobody declared a number, so replace EVERY occurrence — which is exactly what
    # `got` counted and what the `got >= 1` check just accepted.
    # [[unknown-stays-unknown]] [[copy-drift]] [[the-unjoined-end]]
    _tampered = (original.replace(find, repl) if want is None
                 else original.replace(find, repl, want))
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
    _LAST_RED.pop(threading.get_ident(), None)
    try:
        ok_tampered, tail2 = _run_gate(sandbox, filename, timeout=_to, extra=_extra, script=_script, **_w)
    finally:
        with io.open(tgt, "w", encoding="utf-8") as fh:
            fh.write(original)
    if ok_tampered is False and _rk:
        _red_remember(_rk, name, idx, _LAST_RED.pop(threading.get_ident(), None))   # #42 lever 1 — learn what caught it

    if ok_tampered is None:
        say("     %-52s %s — tampered run%s: %s" % (label, UNPROVABLE, _at_widths(widths), tail2))
        return UNPROVABLE
    if ok_tampered:
        say("     %-52s %s ← %s" % (label, BLIND, blind_reason(pr.get("why"), got, tail2, widths=widths)))
        if widths:
            say("     %-52s   ↳ #42: GREEN at its DECLARED widths %s - the declaration is wrong (or the law is blind "
                "there); either way it proves nothing and the push refuses. Re-measure where the defect shows."
                % ("", _at_widths(widths).strip()))
        return BLIND
    say("     %-52s %s (%d match(es) tampered → red)%s" % (label, PROVEN, got, _at_widths(widths)))
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


def prove_exit_code(results):
    """(exit_code, broken, idle) for a set of prove() verdicts. Decides; prints nothing.

    ══ v3292 — THE VERDICT MUST BE RETURNED, NOT ONLY PRINTED ═══════════════════════════════
    BLIND already exited 1 and that was right. INVALID did not — and INVALID is the verdict that
    says the sabotage MATCHED NOTHING, so the proof changed no byte and demonstrated nothing. The
    gate it belongs to has no working red-proof at all, while reporting that it has one.

    MEASURED 2026-09-18 with a throwaway gate whose `find` was deliberately absent:
        "INVALID — the tamper matched 0 time(s)"  ->  exit 0
    Twice in one session a REAL proof went INVALID because its anchor had rotted — once on a line
    my own refactor had deleted. Both printed the word and exited 0, so any hook or CI step
    calling this recorded success. That is how inert proofs accumulate precisely where the static
    law cannot see them. [[matches-once-can-still-prove-nothing]] [[exit-status-of-the-block]]

    ⚠ UNPROVABLE is NAMED AND NOT FAILED, deliberately. It means the law was already red before
    the tamper — a fact about the working tree, which the suite is the organ to report. Failing it
    here would make this tool red for something it did not find, and a tool that is red for
    somebody else's reason is one you learn to ignore.

    ⚠ #42 — THE ONE EXCEPTION IS --push, AND IT IS NOT DECIDED HERE. In `--prove --push` (hooks/pre-push's run) an
    UNPROVABLE whose law was ALREADY RED untampered STOPS the run, like a BLIND or an INVALID, and main() then exits 1 on
    the stop even though this function returns 0 for that UNPROVABLE: every proof after the stop was never run, and
    exit 0 would pass them unseen. So at push time a clean-run red REFUSES the push. An UNPROVABLE that could not judge
    at all (a deadline, a missing file) does not stop the run and is still named and not failed, push or not.

    Extracted from main() so it can be exercised with fixtures: a decision that can only be
    reached by building a sandbox is a decision nothing will ever test.
    """
    broken = sorted(n for n, v in (results or {}).items() if v in (BLIND, INVALID))
    idle = sorted(n for n, v in (results or {}).items() if v == UNPROVABLE)
    return (1 if broken else 0), broken, idle


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--prove", nargs="*", default=None)
    ap.add_argument("--push", action="store_true",
                    help="#42 push-time proving, what hooks/pre-push runs: declared 'widths' restrict a proof's runs, the "
                         "likeliest failures run first and the run stops at the first; one browser gate at a time")
    ap.add_argument("--slice", action="store_true",
                    help="#99 prove these gates as ONE SLICE of a census: the verdicts merge, and the gate fingerprint "
                         "is stamped only once no declaring gate is owed (self_prove's runs on a PC he plays on)")
    ap.add_argument("--detect", action="store_true")
    ap.add_argument("--ratchet", action="store_true")
    ap.add_argument("--triage", action="store_true",
                    help="split the no-red-proof gates into WRITABLE vs NOT PROVABLE HERE")
    a = ap.parse_args(argv)
    if a.prove is not None:
        # a killed prover removes its sandboxes; and the ones an EARLIER killed run left are swept first
        install_sandbox_cleanup()
        for _p, _why in sweep_stale_sandboxes():
            print("  swept a sandbox an interrupted run left behind (%s): %s" % (_why, os.path.basename(_p)))
    if a.triage:
        triage()
        return 0
    if not any([a.report, a.prove is not None, a.detect, a.ratchet]):
        a.report = True

    census, results, hits = {}, {}, []
    _stopped = []
    if a.report or a.ratchet:
        census = report()
    if a.prove is not None:
        print("")
        if a.push:
            results = prove(only=set(a.prove) or None, push=True, stopped=_stopped)
        else:
            results = (prove(only=set(a.prove) or None, stamp=False) if a.slice
                       else prove(only=set(a.prove) or None))
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
    # ══ v3292 — AN INERT PROOF MUST NOT EXIT 0 ═══════════════════════════════════════════════
    # BLIND already returned 1 and that was right. INVALID did not, and INVALID is the verdict
    # that says the sabotage MATCHED NOTHING — the proof changed no byte, so it demonstrated
    # nothing and the gate it belongs to has no working red-proof at all.
    #
    # MEASURED 2026-09-18 with a throwaway gate whose `find` was deliberately absent:
    #     "INVALID — the tamper matched 0 time(s)"  ->  exit 0
    # Twice in one session a real proof went INVALID because its anchor had ROTTED — once on a
    # line my own refactor had deleted. Both printed the word and exited 0, so any harness, hook
    # or CI step calling this would have recorded success. That is how inert proofs pile up
    # exactly where the static law cannot see them. [[matches-once-can-still-prove-nothing]]
    # [[exit-status-of-the-block]]
    #
    # ⚠ UNPROVABLE is deliberately NOT failed here. It means the law was ALREADY RED before the
    # tamper, which is a fact about the working tree, and the test suite is the organ that reports
    # that. Failing it twice would make this tool red for a reason it did not find.
    if results:
        _code, _broken, _idle = prove_exit_code(results)
        if _idle:
            print("\n  ⚪ %d gate(s) UNPROVABLE — already red before the tamper, so nothing was "
                  "demonstrated. Not failed here: that is the suite's finding, not this one.\n     %s"
                  % (len(_idle), ", ".join(_idle[:6]) + (" …" if len(_idle) > 6 else "")))
        if _broken:
            print("\n  ✗ %d gate(s) have a red-proof that PROVES NOTHING (blind or inert):\n     %s"
                  % (len(_broken), ", ".join(_broken[:8]) + (" …" if len(_broken) > 8 else "")))
        if _code:
            return _code
    # #42 — A STOPPED PUSH-TIME RUN IS A REFUSAL even when what stopped it is not failed above (a law ALREADY RED
    # untampered is UNPROVABLE): the proofs after it were never run, and exit 0 would pass them unseen.
    if _stopped:
        _n, _i, _v, _why = _stopped[0]
        print("\n  ✗ #42 the push-time run STOPPED at %s[%d] (%s: %s) — the proofs after it were NOT RUN, so this "
              "cannot pass." % (_n, _i, _v, _why))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
