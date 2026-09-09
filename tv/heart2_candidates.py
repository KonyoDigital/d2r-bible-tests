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


def target_files(tree, here):
    """Which source files does this gate READ? -> [abs path]

    Resolved from the filenames the gate itself names. A gate that reads a file it never names is
    not resolvable this way, and that is reported as UNKNOWN rather than guessed at.
    """
    names = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            v = n.value
            if v.endswith((".py", ".html", ".mjs", ".sh")) and "/" not in v and len(v) > 4:
                names.append(v)
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
        for t in targets:
            body = _read(t) or ""
            n = body.count(a)
            if n == 1:
                proofs.append({
                    "why": "the law requires this text in %s; deleting it must turn the gate red"
                           % os.path.basename(t),
                    "file": os.path.basename(t),
                    "find": a,
                    "replace": _mutate(a),
                    "matches": 1,
                })
                break
            if n > 1:
                rejected.append("%r x%d in %s (ambiguous)" % (a[:40], n, os.path.basename(t)))
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
