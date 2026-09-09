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
import io
import json
import os
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
def gate_files():
    """Every registered gate that is a python test file here. -> [(name, filename)]"""
    out = []
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
        if fn:
            out.append((getattr(g, "name", fn), fn))
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
    for _root_file in ("bible.html",):
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


def _run_gate(sandbox_tv, filename, timeout=180):
    """-> (passed: bool, tail: str)"""
    p = os.path.join(sandbox_tv, filename)
    if not os.path.exists(p):
        return None, "the gate file is not in the sandbox"
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"      # no stale .pyc can outlive a tamper
    try:
        r = subprocess.run([sys.executable, p], cwd=sandbox_tv, env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "timed out after %ss" % timeout
    tail = (r.stdout or b"").decode("utf-8", "replace").strip().splitlines()
    return r.returncode == 0, (tail[-1] if tail else "")


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
    prior = {}
    if os.path.exists(STATE):
        try:
            with io.open(STATE, encoding="utf-8") as fh:
                prior = json.load(fh)
        except Exception:
            prior = {}
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
    out.update({
        "proved": len([n for n, v in (results or {}).items() if v == PROVEN]),
        "declared": len(have),
        "unproven": len(gates) - len(have),
        "total": len(gates),
        "blind": blind,
        "partial": _partial,
        "ranAt": int(__import__("time").time() * 1000),
    })
    with io.open(STATE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)


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
    tgt = os.path.join(sandbox, tgt_rel)
    if tgt_rel and not os.path.exists(tgt):
        _alt = os.path.join(_repo_copy, tgt_rel)
        if os.path.exists(_alt):
            tgt = _alt
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
    ok_clean, tail = _run_gate(sandbox, filename)
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
        ok_tampered, tail2 = _run_gate(sandbox, filename)
    finally:
        with io.open(tgt, "w", encoding="utf-8") as fh:
            fh.write(original)

    if ok_tampered is None:
        say("     %-52s %s — tampered run: %s" % (label, UNPROVABLE, tail2))
        return UNPROVABLE
    if ok_tampered:
        say("     %-52s %s ← stayed GREEN through its own defeat (%d match(es)): %s"
            % (label, BLIND, got, str(pr.get("why"))[:70]))
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
    return {"total": total, "proved": len(have), "unproven": len(missing),
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
        # a file that will not tokenise or parse is UNKNOWN, not clean — return nothing rather
        # than letting raw prose through and calling the hits a measurement
        return ""
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
        for label, rx, why in SIGNATURES:
            n_hits = len(rx.findall(src))
            if n_hits:
                hits.append((fn, label, n_hits, why))
    say("  scanned %d file(s) outside the gate set" % (len(os.listdir(HERE))))
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
        lines += ["- `%s` — the tamper reintroduced the defect and the gate stayed GREEN. "
                  "Either the law reads prose instead of code, or it asserts something the "
                  "tamper does not touch." % n for n in blind] + [""]
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


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--prove", nargs="*", default=None)
    ap.add_argument("--detect", action="store_true")
    ap.add_argument("--ratchet", action="store_true")
    a = ap.parse_args(argv)
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
        prev = {}
        if os.path.exists(STATE):
            try:
                with io.open(STATE, encoding="utf-8") as fh:
                    prev = json.load(fh)
            except Exception:
                prev = {}
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
        with io.open(STATE, "w", encoding="utf-8") as fh:
            json.dump({"unproven": now, "proved": census.get("proved", 0)}, fh)
        print("\n  ✓ RATCHET: unproven %d (was %s)" % (now, base if base < 10 ** 9 else "unset"))
    if results and BLIND in results.values():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
