#!/usr/bin/env python3
"""SABOTAGE THE ROUTES THEMSELVES, and bank what actually happened.

His ruling: *"each of the locked routes needs that same unified logic for wilson score and that
same lock/unlock prove themselves style"*, and *"all connected to the heart of the console
obviously.. so its all communicating and intertwined and integrated together properly within"*.

⚠⚠ WHAT A ROUTE'S GUARD ACTUALLY IS. Every route row prints a set of LANES, each of the shape
`{"ok": true, "by": [what it found]}` — source, generator, artifact, freshness, resolver for the
chronicles; getter, probe, total, unit for the fleet. The lane IS the guard: its whole job is to
notice when the thing it names has gone. So the sabotage writes itself — REMOVE WHAT THE LANE
CLAIMS TO HAVE FOUND AND SEE WHETHER IT STILL SAYS ok.

A lane that reports ok with its evidence deleted has been decorative all along, and the number of
those is the measurement this file exists to take. It is not a verdict about the console; it is a
count.

⚠⚠ NOTHING HERE MAY BE FABRICATED, AND THE DESIGN IS BUILT AROUND THAT:
  · every attempt physically edits a REAL COPY of the tree, made with tv/safe_copy.py
  · the route module is then RUN, in a subprocess, out of that copy — so HERE and BIBLE resolve to
    the sabotaged files and the lane is genuinely re-evaluated, not predicted
  · the recorded outcome is whatever the lane ACTUALLY returned
  · every sabotage prints its MATCH COUNT first. A sabotage that matched nothing proves nothing,
    and this repo has burned a day on exactly that. A zero-match attempt is dropped from the
    denominator rather than counted as a refusal.
  · a lane whose evidence cannot be removed is UNKNOWN and is NOT counted in either direction.
    [[unknown-stays-unknown]] [[feedback-blind-fixture-green-gate]] [[sabotage-is-usually-the-wrong-one]]

⚠ IT BANKS INTO THE SAME LEDGER AS THE VALVES. One vocabulary, one proof queue, one arithmetic:
tv/self_arming.py's bank()/score(), folded on lock+kind+src so a re-run cannot inflate a score, and
declared in its PROVES table so no other source can bank for a route. The heart reads that single
report, which is what makes the routes siblings of the valves on the same diagram rather than a
second system that will drift.

A VALVE earns permission to ACT. A ROUTE earns trust in the NUMBER IT PRINTS. Same flip, same
self-proving arithmetic, different verb — PROVEN / ASSERTED rather than OPEN / LOCKED.
"""
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
sys.path.insert(0, HERE)

#: module -> the state function to call, and the route keys it serves.
SETS = (
    ("chronicle_routes", "chronicle"),
    ("fleet_routes", "fleet"),
    ("roster_routes", "roster"),
)


def _mk_copy(say=print):
    """A real, isolated copy of the tree. -> path | None

    Uses tv/safe_copy.py, which is the only sanctioned copier here: `cp -R` of this repo once
    wrote 20.5 GB in four minutes and ENOSPC'd his Mac.
    """
    dest = tempfile.mkdtemp(prefix="route-wilson-")
    target = os.path.join(dest, "tree")
    rc = subprocess.call([sys.executable, os.path.join(HERE, "safe_copy.py"), target],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if rc != 0 or not os.path.isdir(os.path.join(target, "tv")):
        say("   could not make a working copy (rc=%s) — UNKNOWN, nothing attempted" % rc)
        shutil.rmtree(dest, ignore_errors=True)
        return None
    return target


_READER = r"""
import io, json, os, sys
sys.path.insert(0, os.path.join(%r, "tv"))
os.chdir(os.path.join(%r, "tv"))
import %s as M
try:
    rep = M.routes()
except TypeError:
    rep = M.routes(None)
out = {}
for r in (rep.get("routes") or []):
    out[str(r.get("key"))] = {k: (v.get("ok") if isinstance(v, dict) else None)
                              for k, v in (r.get("lanes") or {}).items()}
print(json.dumps(out))
"""


def _read_lanes(tree, module):
    """Run the route module OUT OF the copy and report each lane's real ok. -> dict | None"""
    code = _READER % (tree, tree, module)
    try:
        out = subprocess.check_output([sys.executable, "-c", code], stderr=subprocess.DEVNULL,
                                      timeout=180, cwd=os.path.join(tree, "tv"))
        return json.loads(out.decode("utf-8", "replace").strip().split("\n")[-1])
    except Exception:
        return None


# ── the sabotages, one per lane KIND ─────────────────────────────────────────────────────────
# Each returns (did_it_bite, note). `did_it_bite` False means the evidence could not be removed,
# which is UNKNOWN — the attempt is dropped, never counted as a refusal.

def _sab_delete_file(tree, path_rel):
    p = os.path.join(tree, path_rel)
    if not os.path.isfile(p):
        return False, "nothing at %s to remove" % path_rel
    os.rename(p, p + ".moved")
    return True, "removed %s" % path_rel


def _undo_delete_file(tree, path_rel):
    p = os.path.join(tree, path_rel)
    if os.path.isfile(p + ".moved"):
        os.rename(p + ".moved", p)


def _sab_blank_mentions(tree, stem):
    """Remove every mention of the roster stem from the scanned .py files. -> (bit, note)

    This is what `generator` and `resolver` search for. Comments are blanked too — the lane reads
    decommented source, so leaving a mention in a comment would not be a real removal.
    """
    tvd = os.path.join(tree, "tv")
    n = 0
    touched = []
    for fn in sorted(os.listdir(tvd)):
        if not fn.endswith(".py"):
            continue
        p = os.path.join(tvd, fn)
        try:
            s = io.open(p, encoding="utf-8").read()
        except Exception:
            continue
        if stem not in s:
            continue
        c = s.count(stem)
        io.open(p + ".orig", "w", encoding="utf-8").write(s)
        io.open(p, "w", encoding="utf-8").write(s.replace(stem, "zzz_removed_zzz"))
        n += c
        touched.append(fn)
    return (n > 0), "blanked %d mention(s) of %r across %d file(s)" % (n, stem, len(touched))


def _undo_blank_mentions(tree):
    tvd = os.path.join(tree, "tv")
    for fn in sorted(os.listdir(tvd)):
        if fn.endswith(".py.orig"):
            src = os.path.join(tvd, fn)
            shutil.move(src, src[:-5])


#: Which FILE each lane kind reads its evidence out of. A lane names a SYMBOL in `by`; removing
#: that symbol from the file it lives in is the honest removal, and it is what these map.
#:
#: ⚠ THE FIRST VERSION OF THIS FILE KNEW ONLY source/artifact/resolver, so it attempted the three
#: CHRONICLE routes and silently skipped the fleet and roster ones entirely — their lanes are
#: getter/probe/total/unit/declared and every one fell through `if lane not in lanes: continue`.
#: It then printed "9 of 9 attempts refused" which was true and covered a THIRD of the routes.
#: A harness that reports a perfect score over the subset it happens to understand is the
#: sample-is-not-a-verdict scar. Every lane kind now has a removal, and a lane kind with no entry
#: here is reported as UNKNOWN rather than skipped in silence.
LANE_FILES = {
    "declared": "bible.html",
    "getter": "bible.html",
    "probe": os.path.join("tv", "control_app.py"),
    "total": os.path.join("tv", "control_app.py"),
    "unit": os.path.join("tv", "control_ui.html"),
}


def _sab_rename_symbol(tree, rel, symbol):
    """Remove a lane's evidence from the file it lives in. -> (bit, note)

    ⚠⚠ THE EVIDENCE IS NOT ALWAYS A SYMBOL, AND TREATING IT AS ONE MANUFACTURED 12 FALSE LEAKS.
    A lane's `by` is sometimes a FILENAME — the fleet's `probe` says ["control_app.py"] and its
    `unit` says ["control_ui.html"] — and the first cut pulled an identifier out of that string
    ("control_app") and renamed it INSIDE the file. That removes nothing: the probe code is still
    there and the file still exists, so the lane correctly stayed ok, and the harness recorded a
    LEAK. Twelve of them, across six routes, every one an artefact of the instrument.
    Reporting those would have been a fabricated defect count. When the evidence names a FILE,
    remove the FILE. [[feedback-suspect-the-instrument]] [[sabotage-is-usually-the-wrong-one]]
    """
    if symbol and re.match(r"^[\w./-]+\.(py|html|json|mjs|ts)$", str(symbol).strip()):
        base = str(symbol).strip()
        for cand in (base, os.path.join("tv", base)):
            if os.path.isfile(os.path.join(tree, cand)):
                return _sab_delete_file(tree, cand)
        return False, "%r names a file that is not in the copy" % base
    p = os.path.join(tree, rel)
    if not os.path.isfile(p):
        return False, "no %s to edit" % rel
    try:
        s = io.open(p, encoding="utf-8", errors="replace").read()
    except Exception as e:
        return False, "could not read %s — %s" % (rel, str(e)[:40])
    # a lane's `by` may be a regex fragment (roster's "declared" is `const\s+RUNEWORDS\s*=`);
    # pull the identifier out of it so there is something concrete to remove
    ident = None
    for cand in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", symbol or ""):
        if cand not in ("const", "var", "let", "function", "window"):
            ident = cand
            break
    if not ident or ident not in s:
        return False, "%r is not in %s to remove" % (ident or symbol, rel)
    c = s.count(ident)
    io.open(p + ".orig", "w", encoding="utf-8").write(s)
    io.open(p, "w", encoding="utf-8").write(s.replace(ident, "zzz_removed_zzz"))
    return True, "renamed %d occurrence(s) of %r in %s" % (c, ident, os.path.basename(rel))


def _sab_rename_many(tree, rel, symbols):
    """Remove EVERY identifier a lane cites, from one file, in a single pass. -> (bit, note)"""
    p = os.path.join(tree, rel)
    if not os.path.isfile(p):
        return False, "no %s to edit" % rel
    s = io.open(p, encoding="utf-8", errors="replace").read()
    idents = []
    for sym in symbols or []:
        for cand in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", str(sym)):
            if cand not in ("const", "var", "let", "function", "window") and cand in s:
                idents.append(cand)
                break
    idents = sorted(set(idents))
    if not idents:
        return False, "none of %r is in %s" % (symbols, rel)
    io.open(p + ".orig", "w", encoding="utf-8").write(s)
    total = 0
    for i in idents:
        total += s.count(i)
        s = s.replace(i, "zzz_removed_" + i + "_zzz")
    io.open(p, "w", encoding="utf-8").write(s)
    return True, "removed %d occurrence(s) of %s from %s" % (total, idents, os.path.basename(rel))


def _undo_rename_symbol(tree, rel, symbol=None):
    p = os.path.join(tree, rel)
    if os.path.isfile(p + ".orig"):
        shutil.move(p + ".orig", p)
    # a filename-shaped evidence was removed by moving the file aside; put it back
    if symbol:
        base = str(symbol).strip()
        for cand in (base, os.path.join("tv", base)):
            _undo_delete_file(tree, cand)


# ══ HARD MODE ══════════════════════════════════════════════════════════════════════════════════
# His ruling: "is there a way to make it HARD MODE".
#
# ⚠ THE EASY ATTEMPTS ABOVE ARE GROSS REMOVALS — delete the file, rename the symbol. Any lane
# notices those, which is why they scored 33/33, and 33/33 is a weak fact: it says the lanes catch
# the obvious. Repeating them would only inflate n without asking a new question.
#
# HARD MODE LEAVES THE EVIDENCE IN PLACE AND BREAKS ITS MEANING. A lane that greps for
# `const RUNEWORDS =` still matches when the array behind it is EMPTY. A lane that checks
# os.path.isfile still says yes to a zero-byte file. A mention that survives only inside a COMMENT
# is not a mention of working code. These are the states where a decorative lane and a real one
# finally look different — and they are the states that actually happen, because files get emptied
# and code gets commented out far more often than files get deleted.
#
# ⚠ THESE ARE EXPECTED TO FIND LEAKS, and a leak found here is worth more than a refusal: it is
# the difference between a lane that watches and a lane that decorates. Nothing is graded softer
# because it is hard. [[feedback-blind-fixture-green-gate]]

def _sab_empty_file(tree, rel):
    """Leave the file, remove everything in it. -> (bit, note)"""
    p = os.path.join(tree, rel)
    if not os.path.isfile(p):
        return False, "no %s to empty" % rel
    io.open(p + ".orig", "w", encoding="utf-8").write(
        io.open(p, encoding="utf-8", errors="replace").read())
    io.open(p, "w", encoding="utf-8").write("")
    return True, "emptied %s to 0 bytes, the file still EXISTS" % os.path.basename(rel)


def _sab_empty_declaration(tree, rel, symbols):
    """Keep every declaration line; empty what it declares. -> (bit, note)

    The array/object header survives, so a lane that greps for the declaration still matches.
    """
    p = os.path.join(tree, rel)
    if not os.path.isfile(p):
        return False, "no %s to edit" % rel
    s = io.open(p, encoding="utf-8", errors="replace").read()
    idents = []
    for sym in symbols or []:
        for cand in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", str(sym)):
            if cand not in ("const", "var", "let", "function", "window") and cand in s:
                idents.append(cand)
                break
    idents = sorted(set(idents))
    if not idents:
        return False, "none of %r is in %s" % (symbols, rel)
    io.open(p + ".orig", "w", encoding="utf-8").write(s)
    done = 0
    for ident in idents:
        # `const X = [ ... ]`  ->  `const X = []`   (header intact, contents gone)
        m = re.search(r"((?:const|var|let|window\.)\s*%s\s*=\s*)(\[|\{)" % re.escape(ident), s)
        if not m:
            continue
        opench = m.group(2)
        closech = "]" if opench == "[" else "}"
        blk = _balanced_span(s, m.end() - 1, opench, closech)
        if blk is None:
            continue
        s = s[:m.end() - 1] + opench + closech + s[m.end() - 1 + len(blk):]
        done += 1
    if not done:
        return False, "no %r declaration had a body to empty" % idents
    io.open(p, "w", encoding="utf-8").write(s)
    return True, "EMPTIED %d declaration(s) %s — the declaration line still reads exactly the same" % (done, idents)


def _balanced_span(s, start, opench, closech):
    depth = 0
    instr = None
    j = start
    while j < len(s):
        c = s[j]
        if instr:
            if c == "\\":
                j += 2
                continue
            if c == instr:
                instr = None
        elif c in "\"'":
            instr = c
        elif c == opench:
            depth += 1
        elif c == closech:
            depth -= 1
            if depth == 0:
                return s[start:j + 1]
        j += 1
    return None


def _sab_comment_out(tree, rel, symbol):
    """Leave the symbol present, but only inside a COMMENT. -> (bit, note)"""
    p = os.path.join(tree, rel)
    if not os.path.isfile(p):
        return False, "no %s to edit" % rel
    s = io.open(p, encoding="utf-8", errors="replace").read()
    ident = None
    for cand in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", str(symbol or "")):
        if cand not in ("const", "var", "let", "function", "window") and cand in s:
            ident = cand
            break
    if not ident:
        return False, "%r not present in %s" % (symbol, rel)
    io.open(p + ".orig", "w", encoding="utf-8").write(s)
    c = s.count(ident)
    marker = "//" if rel.endswith((".html", ".js", ".mjs")) else "#"
    body = s.replace(ident, "zzz_gone_zzz")
    io.open(p, "w", encoding="utf-8").write(
        body + "\n%s the name still appears in this file, in a comment only: %s\n" % (marker, ident))
    return True, "moved %r out of the code and left it in a COMMENT only (%d were live)" % (ident, c)


def _sab_comment_out_many(tree, rel, symbols):
    """Move EVERY name a lane cites out of the code, leaving them only in a comment."""
    p = os.path.join(tree, rel)
    if not os.path.isfile(p):
        return False, "no %s to edit" % rel
    s = io.open(p, encoding="utf-8", errors="replace").read()
    idents = []
    for sym in symbols or []:
        for cand in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", str(sym)):
            if cand not in ("const", "var", "let", "function", "window") and cand in s:
                idents.append(cand)
                break
    idents = sorted(set(idents))
    if not idents:
        return False, "none of %r is in %s" % (symbols, rel)
    io.open(p + ".orig", "w", encoding="utf-8").write(s)
    live = 0
    for i in idents:
        live += s.count(i)
        s = s.replace(i, "zzz_gone_" + i + "_zzz")
    marker = "//" if rel.endswith((".html", ".js", ".mjs")) else "#"
    io.open(p, "w", encoding="utf-8").write(
        s + "\n%s these names appear here in a comment only: %s\n" % (marker, ", ".join(idents)))
    return True, "moved ALL of %s out of the code into a COMMENT (%d were live)" % (idents, live)


def hard_attempts_for(route_key, artifact, lanes=None):
    """Attempts a lazy lane passes and a real one fails. -> [(lane, apply, undo, label)]"""
    out = []
    if "source" in (lanes or {}):
        out.append(("source", lambda t: _sab_empty_file(t, "bible.html"),
                    lambda t: _undo_rename_symbol(t, "bible.html"),
                    "EMPTY bible.html but leave the file"))
    for lane in ("declared", "getter"):
        by = ((lanes or {}).get(lane) or {}).get("by") or []
        if not by:
            continue
        rel = LANE_FILES.get(lane, "bible.html")
        out.append((lane,
                    (lambda r, bs: (lambda t: _sab_empty_declaration(t, r, list(bs))))(rel, by),
                    (lambda r: (lambda t: _undo_rename_symbol(t, r)))(rel),
                    "EMPTY what it declares, keep the declaration line"))
        # ⚠ ALL of them, not by[0]. `unique` declares through BOTH ITEM_VALUE and _UNI_EXTRA, and
        # commenting out only the first left the second live — _declared returns True on ANY
        # pattern, so the lane correctly stayed ok and this harness called it a LEAK. Twice. That
        # is the FOURTH instrument error in this file and the same shape every time: a partial
        # removal reported as a defect. [[sabotage-is-usually-the-wrong-one]]
        out.append((lane,
                    (lambda r, bs: (lambda t: _sab_comment_out_many(t, r, list(bs))))(rel, by),
                    (lambda r: (lambda t: _undo_rename_symbol(t, r)))(rel),
                    "leave ALL %d name(s) in a COMMENT only" % len(by)))
    return out


def attempts_for(route_key, artifact, lanes=None):
    """The sabotages that apply to one route. -> [(lane, apply, undo, label)]

    Built from the route's OWN lanes and their `by` evidence, so a lane kind added later is
    attempted rather than quietly skipped.
    """
    stem = (artifact or "").replace(".json", "")
    out = [
        ("source", lambda t: _sab_delete_file(t, "bible.html"),
         lambda t: _undo_delete_file(t, "bible.html"), "delete bible.html"),
    ]
    if artifact:
        out.append(("artifact", lambda t: _sab_delete_file(t, os.path.join("tv", artifact)),
                    lambda t: _undo_delete_file(t, os.path.join("tv", artifact)),
                    "delete %s" % artifact))
    if stem:
        out.append(("resolver", lambda t: _sab_blank_mentions(t, stem),
                    _undo_blank_mentions, "blank every mention of %r" % stem))
        out.append(("generator", lambda t: _sab_blank_mentions(t, stem),
                    _undo_blank_mentions, "blank every mention of %r" % stem))
    for lane, rel in sorted(LANE_FILES.items()):
        by = ((lanes or {}).get(lane) or {}).get("by") or []
        sym = by[0] if by else None
        if not sym:
            continue
        # ⚠⚠ A LANE MAY REST ON SEVERAL DECLARATIONS, AND REMOVING ONE IS NOT A REMOVAL.
        # roster `declared` asks _decl_patterns(key), which for `set` returns every pattern
        # naming ITEM_SETS **or** SET_PIECES, and for `unique` both ITEM_VALUE and _UNI_EXTRA.
        # Renaming the first one left the others matching, the lane correctly stayed ok, and the
        # harness called it a LEAK — twice. That is the sabotage's fault, not the console's, and
        # it is the third instrument error this file has had to correct. When a lane cites more
        # than one piece of evidence, ALL of it goes. [[sabotage-is-usually-the-wrong-one]]
        if len(by) > 1:
            out.append((lane,
                        (lambda r, bs: (lambda t: _sab_rename_many(t, r, bs)))(rel, list(by)),
                        (lambda r: (lambda t: _undo_rename_symbol(t, r)))(rel),
                        "remove ALL %d declaration(s) in %s" % (len(by), os.path.basename(rel))))
            continue
        out.append((lane,
                    (lambda r, sy: (lambda t: _sab_rename_symbol(t, r, sy)))(rel, sym),
                    (lambda r, sy: (lambda t: _undo_rename_symbol(t, r, sy)))(rel, sym),
                    "rename %r in %s" % (sym[:28], os.path.basename(rel))))
    return out


HARD = os.environ.get("ROUTE_WILSON_HARD", "1") not in ("0", "off", "no")


def run(say=print):
    """-> [row] per route, in the shape self_arming.bank() takes."""
    tree = _mk_copy(say=say)
    if tree is None:
        return []
    rows = []
    try:
        base = {}
        for module, _label in SETS:
            got = _read_lanes(tree, module)
            if got:
                base[module] = got
        if not base:
            say("   no route module answered from the copy — UNKNOWN, nothing attempted")
            return []

        for module, label in SETS:
            clean = base.get(module) or {}
            for key, lanes in sorted(clean.items()):
                art = None
                # the artifact name the route names for itself, read from the live report
                try:
                    import importlib
                    m = importlib.import_module(module)
                    rep = m.routes() if module == "chronicle_routes" else m.routes(None)
                    for r in (rep.get("routes") or []):
                        if str(r.get("key")) == key:
                            art = r.get("artifact")
                except Exception:
                    art = None

                live_lanes = {}
                try:
                    import importlib
                    m2 = importlib.import_module(module)
                    rep2 = m2.routes() if module == "chronicle_routes" else m2.routes(None)
                    for r in (rep2.get("routes") or []):
                        if str(r.get("key")) == key:
                            live_lanes = r.get("lanes") or {}
                except Exception:
                    live_lanes = {}
                # ⚠ ANY LANE THIS HARNESS HAS NO REMOVAL FOR IS NAMED, NOT SKIPPED IN SILENCE.
                # The first cut understood three lane kinds and quietly attempted nothing on the
                # fleet and roster routes, then printed a perfect score for the third it covered.
                _plan = attempts_for(key, art, live_lanes)
                if HARD:
                    _plan = _plan + hard_attempts_for(key, art, live_lanes)
                planned = {lane for lane, _a, _u, _w in _plan}
                unattempted = sorted(set(lanes) - planned)

                n = k = 0
                notes = []
                for lane in unattempted:
                    notes.append("%s: no removal exists for this lane kind — UNKNOWN" % lane)
                for lane, apply_, undo_, what in _plan:
                    if lane not in lanes:
                        continue
                    if lanes.get(lane) is not True:
                        notes.append("%s: lane was not ok before the attempt — skipped" % lane)
                        continue
                    bit, note = apply_(tree)
                    say("      %-9s %-34s %s" % (lane, what, note))
                    if not bit:
                        notes.append("%s: %s — UNKNOWN, not counted" % (lane, note))
                        continue
                    try:
                        after = _read_lanes(tree, module) or {}
                        got = (after.get(key) or {}).get(lane)
                        n += 1
                        if got is not True:
                            k += 1
                        else:
                            notes.append("%s LEAKED: still ok with its evidence removed" % lane)
                    finally:
                        undo_(tree)
                rows.append({"route": "%s.%s" % (label, key), "n": n, "k": k,
                             "notes": notes, "unattempted": len(unattempted)})
                if True:
                    say("   %-22s %d/%d refused%s" % ("%s.%s" % (label, key), k, n,
                                                      "  ⚠ " + "; ".join(notes) if notes else ""))
    finally:
        shutil.rmtree(os.path.dirname(tree), ignore_errors=True)
    return rows


def main(argv=None):
    argv = list(argv or [])
    say = print
    say("route sabotage — remove what each lane claims to have found, and see if it still says ok")
    rows = run(say=say)
    if not rows:
        say("\nnothing was attempted — that is UNKNOWN, not a pass")
        return 2
    tot_n = sum(r["n"] for r in rows)
    tot_k = sum(r["k"] for r in rows)
    leaks = [r for r in rows if r["k"] < r["n"]]
    say("\n%d of %d attempts refused across %d route(s)" % (tot_k, tot_n, len(rows)))
    if leaks:
        say("🔴 %d route(s) have a lane that stayed ok with its evidence removed:" % len(leaks))
        for r in leaks:
            say("   %-22s %d/%d — %s" % (r["route"], r["k"], r["n"], "; ".join(r["notes"])[:110]))
    else:
        say("✅ every lane attempted noticed its evidence was gone")
    if "--bank" in argv:
        try:
            import self_arming as SA
        except Exception as e:
            say("could not bank — %s" % str(e)[:80])
            return 1
        banked = 0
        for r in rows:
            try:
                SA.bank(r["route"], "sabotage", "route_wilson", r["n"], r["k"],
                        note="removed what each lane claims to have found")
                banked += 1
            except Exception as e:
                say("   refused for %s — %s" % (r["route"], str(e)[:90]))
        say("banked %d row(s)" % banked)
    return 0 if not leaks else 1


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
