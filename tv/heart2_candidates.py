#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Derive a PRE-MEASURED red-proof candidate from a gate's own assertions.

⚠⚠ WHY THIS EXISTS. Heart 2.0's `propose()` wrote a LIST OF NAMES — "these 242 gates declare no
executable red-proof" — and called it a proposal. It is not. A name is a backlog item; a proposal
is something a person can act on. Measured 2026-09-09: 12 of 254 gates carried a proof (4.7%) and
the backlog had not moved, because every one of the 242 required a human to re-derive by hand the
sabotage that the gate's own assertions already state.

★ THE GATE ALREADY KNOWS ITS OWN PROOF. A source-reading law says `assertIn("X", src_of_file_Y)`.
That IS the sabotage: remove X from Y and the law must go red. The derivation is mechanical, and
leaving it to a person is why the backlog stayed at 242.

WHAT THIS REFUSES TO PROPOSE, and it refuses often on purpose:

  · a literal that occurs 0 times in the target — the gate is not asserting what it appears to,
    and a tamper with no match proves nothing [[sabotage-is-usually-the-wrong-one]]
  · a literal that occurs MORE THAN ONCE — an ambiguous anchor tampers the wrong occurrence, which
    is the single most common way a sabotage in this repo has been wrong
  · a literal shorter than 8 characters — too generic to anchor
  · a gate whose target file cannot be resolved — UNKNOWN, and it says so rather than guessing

It NEVER writes to a guard, and it never writes to a target file. It returns text.
[[achilles-self-carving-system]] [[unknown-stays-unknown]]
"""
import ast
import io
import os

#: An anchor shorter than this is too generic to tamper safely.
MIN_ANCHOR = 8

#: What a proposal must be able to name.
NO_TARGET, NO_ANCHOR, AMBIGUOUS, ABSENT, OK = (
    "no-target-file", "no-usable-anchor", "ambiguous-anchor", "anchor-absent", "ok")


def _read(p):
    try:
        with io.open(p, encoding="utf-8") as fh:
            return fh.read()
    except Exception:
        return None


#: Modules imported by more than this fraction of the gate corpus are INFRASTRUCTURE, not any one
#: gate's subject. Measured 2026-09-09 over 264 gates: `console_safe` 95%, then a cliff to
#: `control_app` 21% and down. The threshold sits in the gap, and it is computed rather than
#: hardcoded so a module that becomes ubiquitous later is excluded without anyone noticing it did.
INFRA_SHARE = 0.25

_INFRA_CACHE = {}


def _module_imports(tree):
    """Top-level module names this file imports. -> [str]"""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                out.append(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            out.append(n.module.split(".")[0])
    return out


def infrastructure(here):
    """Local modules too widely imported to be any single gate's subject. -> set

    ⚠⚠ WITHOUT THIS, IMPORT RESOLUTION IS WORSE THAN NO RESOLUTION. 95% of gates import
    `console_safe` — the stdout encoding helper. Resolving a gate's subject to it would derive a
    tamper against `console_safe.py`, that tamper WOULD turn the gate red, and the proof would be
    recorded as coverage while demonstrating nothing whatsoever about the law: every gate that
    imports it goes red together. A proof that reddens for a reason unrelated to its own subject is
    the most convincing kind of green that means nothing.
    [[feedback-blind-fixture-green-gate]] [[zero-needs-a-denominator]]
    """
    if here in _INFRA_CACHE:
        return _INFRA_CACHE[here]
    import glob as _glob
    files = _glob.glob(os.path.join(here, "test_*.py"))
    counts, total = {}, 0
    for f in files:
        src = _read(f)
        if src is None:
            continue
        try:
            t = ast.parse(src)
        except SyntaxError:
            continue
        total += 1
        for m in set(_module_imports(t)):
            if os.path.isfile(os.path.join(here, m + ".py")):
                counts[m] = counts.get(m, 0) + 1
    # ⚠ A CORPUS TOO SMALL TO RANK IS NOT A CORPUS WITH NO INFRASTRUCTURE. Below 20 gates the
    # share is noise, so nothing is excluded and every candidate has to survive --prove anyway.
    infra = set() if total < 20 else {m for m, k in counts.items() if k > total * INFRA_SHARE}
    _INFRA_CACHE[here] = infra
    return infra


def target_files(tree, here):
    """Which source files does this gate READ? -> [abs path]

    Resolved first from the filenames the gate itself names, then — v2836 — from the LOCAL MODULES
    IT IMPORTS. The filename-only rule left 94 of the 238 unproven gates with no resolvable subject
    at all, the single largest refusal bucket, and every one of those 94 imports a local module.
    A gate that says `import reel_router as RR` and then asserts on RR's behaviour names its subject
    perfectly well; it just does not spell it with a `.py`.

    ⚠ Widely-imported infrastructure is excluded — see `infrastructure()`. Resolving a subject to
    `console_safe` would produce a tamper that reddens the gate for a reason that has nothing to do
    with its law.
    """
    names = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            v = n.value
            if v.endswith((".py", ".html", ".mjs", ".sh")) and "/" not in v and len(v) > 4:
                names.append(v)
    # v2836 — the modules it IMPORTS are subjects too, minus the infrastructure everything imports
    _infra = infrastructure(here)
    for m in _module_imports(tree):
        if m in _infra:
            continue
        if os.path.isfile(os.path.join(here, m + ".py")):
            names.append(m + ".py")
    out, seen = [], set()
    for v in names:
        if v in seen:
            continue
        seen.add(v)
        for root in (here, os.path.dirname(here)):
            p = os.path.join(root, v)
            if os.path.isfile(p):
                out.append(p)
                break
    return out


def _anchors(tree):
    """Every string literal the gate REQUIRES to be present. -> [str]

    Only `assertIn` / `assertTrue(... in ...)` shapes: a POSITIVE requirement is the only kind
    whose removal is a valid sabotage. A negative assertion (`assertNotIn`) is satisfied by
    absence, so deleting something cannot make it fail.
    """
    out = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        if n.func.attr != "assertIn" or not n.args:
            continue
        a = n.args[0]
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            if len(a.value) >= MIN_ANCHOR:
                out.append(a.value)
    seen, uniq = set(), []
    for v in out:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq


def _mutate(anchor):
    """A textual tamper that DELETES the anchor rather than obscuring it.

    Removing the thing is the honest sabotage: the point is to prove the law notices its subject
    is GONE, not that it notices a spelling change. `_HEART2_` makes the tamper unmistakable in a
    diff if one ever escapes the sandbox.
    """
    return "_HEART2_TAMPERED_"


def candidates_for(gate_path, here=None):
    """-> (list_of_proofs, status, note). Never edits anything."""
    here = here or os.path.dirname(os.path.abspath(gate_path))
    src = _read(gate_path)
    if src is None:
        return [], NO_TARGET, "the gate file could not be read"
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [], NO_TARGET, "the gate does not parse (%s)" % type(e).__name__
    targets = target_files(tree, here)
    # ⚠ A GATE MAY NOT BE ITS OWN SUBJECT. After the cross-file fix, test_agent began proposing
    # tampers against test_agent.py itself — anchors like 'leaving Durance of Hate Level 2', which
    # are its own FIXTURE DATA. Deleting those does turn the gate red, so it would pass --prove and
    # count as coverage, while proving nothing whatsoever about the code the law is meant to guard.
    # A proof that only demonstrates a test can break its own fixture is the most convincing kind
    # of green that means nothing. [[feedback-blind-fixture-green-gate]]
    _self = os.path.basename(os.path.abspath(gate_path))
    targets = [t for t in targets if os.path.basename(t) != _self]
    if not targets:
        return [], NO_TARGET, ("the gate names no source file it reads — its subject cannot be "
                               "resolved from the text, so no tamper can be derived")
    anchors = _anchors(tree)
    if not anchors:
        return [], NO_ANCHOR, ("no positive assertIn on a string literal of >= %d chars. A law "
                               "that only asserts ABSENCE cannot be sabotaged by deletion."
                               % MIN_ANCHOR)
    proofs, rejected = [], []
    for a in anchors:
        # ⚠⚠ v2820 — THE ANCHOR MUST BE UNAMBIGUOUS ACROSS *EVERY* NAMED FILE, NOT THE FIRST FILE
        # THAT HAPPENS TO HOLD IT ONCE. A cross-family review of v2818 found this and my own batch
        # data had already proved it without my noticing:
        #
        #   'stop_agent' -> control_app.py:31  tv_diablo.py:1  run_gates.py:1  test_control.py:13
        #
        # The old loop took the FIRST target with exactly one occurrence — tv_diablo.py — while the
        # gate's real subject held 31. Tampering an unrelated file leaves the gate green, which is
        # exactly the BLIND verdict `test_agent[0]` returned when I applied it. MEASURED on
        # test_control.py: 40 of 40 anchors resolve in MORE THAN ONE named file.
        #
        # And the old loop could not even refuse properly: `n > 1` recorded a rejection but did NOT
        # break, so an anchor appearing twice in the right file and once in an incidental one still
        # produced a proof — for the wrong file.
        #
        # `target_files` collects every source filename the gate MENTIONS; it does not know which
        # one any given assertion actually reads. Until an anchor can be tied to its container by
        # dataflow, the only honest rule is: exactly one named file may contain it, exactly once.
        # This refuses far more than it accepts, and every refusal is a candidate that would have
        # been wrong. [[sabotage-is-usually-the-wrong-one]] [[unknown-stays-unknown]]
        hits = []
        for t in targets:
            n = (_read(t) or "").count(a)
            if n:
                hits.append((t, n))
        if len(hits) == 1 and hits[0][1] == 1:
            t = hits[0][0]
            proofs.append({
                "why": "the law requires this text in %s, where it occurs exactly once and in no "
                       "other file the gate names; deleting it must turn the gate red"
                       % os.path.basename(t),
                "file": os.path.basename(t),
                "find": a,
                "replace": _mutate(a),
                "matches": 1,
            })
        elif hits:
            rejected.append("%r in %s (ambiguous — a tamper could not name one subject)"
                            % (a[:40], ", ".join("%s x%d" % (os.path.basename(t), n)
                                                 for t, n in hits[:4])))
    if not proofs:
        return [], (AMBIGUOUS if rejected else ABSENT), (
            "; ".join(rejected[:3]) or
            "every anchor the gate asserts is ABSENT from the files it names — worth a look on its "
            "own, because a law asserting text that is not there is not measuring what it claims")
    return proofs[:3], OK, "%d candidate(s) from %d anchor(s)" % (len(proofs), len(anchors))


def render_block(name, proofs):
    """The exact text a person pastes into the gate file. -> str"""
    out = ["", "# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════",
           "# PROPOSED by tv/heart2_candidates.py — derived from this gate's OWN assertions and",
           "# measured against the target file (each anchor occurs exactly once). Review it: the",
           "# question is whether deleting this text is the defect the law exists to catch.",
           "RED_PROOF = ["]
    for p in proofs:
        out += ["    {",
                "        \"why\": %r," % p["why"],
                "        \"file\": %r," % p["file"],
                "        \"find\": %r," % p["find"],
                "        \"replace\": %r," % p["replace"],
                "        \"matches\": %d," % p["matches"],
                "    },"]
    out += ["]", ""]
    return "\n".join(out)
