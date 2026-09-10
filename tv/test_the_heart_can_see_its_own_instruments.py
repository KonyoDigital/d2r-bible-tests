#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""♥♥ HEART 2.0 — the law that the heart can see whether its own instruments still work.

**MEASURED 2026-09-08, and it is the entire argument for this layer.** The heart was GREEN while
12 of 238 gates were red, 8 of those were blind instruments, and the full set had been failing in
CI since 2026-09-07 06:12 — 28 of the last 40 runs. Every check the heart made was working.
Nothing was checking the checkers, so nobody knew. Three of the eight were laws that had silently
STOPPED MEASURING what they claimed while staying green.

    heart v1   is the SYSTEM healthy?   — lanes, routes, stores, the console
    heart v2   are my own INSTRUMENTS   — the gates and locks themselves
               still able to go red?

★ THE NUMBER THAT SETTLES "isn't it basically built?": 246 gates, and before this arc **0** had an
executable red-proof. Each was proven red exactly once, by hand, in a shell, and that proof
survives only as prose in a docstring. It cannot be re-run — so the number of gates that can still
go red was UNKNOWN. Not zero, not fine. Unknown. [[unknown-stays-unknown]]

THIS LAW GUARDS THE LAYER, NOT THE NUMBER. It does not assert how many proofs exist — that is a
ratchet's job and it would fail every honest commit. It asserts that the machinery is joined and
cannot quietly stop working:

  · the census counts something (a 0 here means the parser broke, not that there are no gates —
    which is exactly what happened: the first cut read `g.cmd`, the field is `g.argv`, and it
    printed "0 gates / 0.0%" as though it were a measurement) [[zero-needs-a-denominator]]
  · every declared RED_PROOF is well formed, names a file that exists, and its `find` occurs the
    exact number of times it claims — a tamper that matches nothing proves nothing, and a green
    sabotage is usually the sabotage's fault [[sabotage-is-usually-the-wrong-one]]
  · the heart actually CARRIES the result, so the proving loop is not plumbing with no tap
  · and it proposes rather than repairs — a tool that edits its own guards can talk itself into
    anything [[achilles-self-carving-system]]
"""
import os
import re
import ast
import io
import sys
import unittest

import heart2 as _H2   # noqa: E402  (the ONE resolver for a proof's target file)

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import heart2  # noqa: E402

APP = os.path.join(HERE, "control_app.py")


def _app():
    with io.open(APP, encoding="utf-8") as fh:
        return fh.read()


class TestHeartSeesItsInstruments(unittest.TestCase):

    def test_the_census_counts_something(self):
        """THE INSTRUMENT FIRST. A 0 here is a broken parser wearing the clothes of a measurement —
        which is precisely what shipped for one run of this file."""
        gates = heart2.gate_files()
        self.assertGreater(len(gates), 100,
                           "the census found %d gate(s). run_gates registers hundreds, so this is "
                           "the parser failing, not a clean tree" % len(gates))
        print("\n   census: %d gate(s) with a python file" % len(gates))

    def test_every_declared_red_proof_is_well_formed(self):
        bad = []
        checked = 0
        for name, fn in heart2.gate_files():
            proofs = heart2.red_proofs_in(fn)
            if not proofs:
                continue
            for i, pr in enumerate(proofs):
                checked += 1
                label = "%s[%d]" % (name, i)
                if not isinstance(pr, dict):
                    bad.append("%s is not a dict" % label)
                    continue
                for k in ("why", "file", "find", "replace", "matches"):
                    if k not in pr:
                        bad.append("%s has no %r" % (label, k))
                # ⚠ THROUGH heart2's OWN RESOLVER, NOT A SECOND os.path.join. This joined against
                # tv/ alone, so every proof naming the repo-root `bible.html` was reported malformed
                # while heart2 applied it without trouble — 8 of them, and the law was the wrong one.
                # [[copy-drift]]
                tgt = _H2.resolve_proof_target(HERE, str(pr.get("file") or ""))
                if not os.path.isfile(tgt):
                    bad.append("%s names a file that does not exist: %r" % (label, pr.get("file")))
                    continue
                with io.open(tgt, encoding="utf-8") as fh:
                    src = fh.read()
                got = src.count(str(pr.get("find") or ""))
                want = int(pr.get("matches") or 0)
                if got != want:
                    bad.append("%s: the tamper matches %d time(s), it declares %d — a sabotage "
                               "that changes nothing proves nothing" % (label, got, want))
                if str(pr.get("find")) == str(pr.get("replace")):
                    bad.append("%s: find and replace are identical — it tampers with nothing"
                               % label)
        self.assertEqual(bad, [], "malformed red-proofs:\n  " + "\n  ".join(bad))
        print("   %d red-proof(s) declared, all well formed" % checked)

    def test_the_heart_carries_the_instrument_census(self):
        """The proving loop and the heart must be JOINED. Two halves each built right and never
        joined is this repo's single most repeated defect."""
        src = _app()
        self.assertIn("def _heart2_census(", src,
                      "control_app.py has no instrument census to report")
        self.assertIn('"instruments": _heart2_census()', src,
                      "heart_state() does not carry the instruments — the proving loop would "
                      "measure and nothing would ever read it")
        import control_app as CA
        got = CA._heart2_census()
        self.assertIsInstance(got, dict)
        for k in ("state", "why"):
            self.assertIn(k, got)
        self.assertIn(got["state"], ("WATCHED", "DARK", "UNKNOWN"),
                      "the census reported an unknown state word: %r" % got.get("state"))
        print("   heart carries: %s — %s" % (got.get("state"), str(got.get("why"))[:70]))

    def test_the_console_actually_RENDERS_the_instrument_census(self):
        """⚠⚠ THE JOIN STOPPED ONE LAYER SHORT AND THE GATE DID NOT NOTICE. The census reached
        heart_state() and went no further: `grep -c instruments control_ui.html` was **0**, so
        --prove could report a gate that survived its own defeat and the console would show
        exactly what it showed before. The earlier version of this law asserted only that
        `"instruments": _heart2_census()` appears in control_app.py — the payload, never the
        surface. A finding nobody can see is a finding nobody has.

        This repo has the identical scar forty lines from the join site, about d.rosters:
        "THE THIRD COLUMN WAS COMPUTED AND RENDERED NOWHERE". A repeat, not a first.
        [[the-unjoined-end]] [[plumbing-with-no-tap]]"""
        ui = os.path.join(HERE, "control_ui.html")
        with io.open(ui, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("d.instruments", src,
                      "control_ui.html never reads d.instruments — the heart carries the census "
                      "and no human ever sees it")
        self.assertIn("function _hrtInstruments(", src,
                      "there is no renderer for the instrument census")
        # reading it is not rendering it: the renderer has to be CALLED from the panel builder
        self.assertIn("_hrtInstruments(d.instruments)", src,
                      "_hrtInstruments exists but the heart panel never calls it — a renderer "
                      "with no caller is the same silence with more code")
        # and a BLIND gate must be nameable on screen, not merely counted
        self.assertIn("BLIND", src,
                      "the panel cannot say the word BLIND, so a gate that survived its own "
                      "defeat would render as an ordinary number")

    def test_an_absent_state_file_reads_UNKNOWN_not_clean(self):
        """The commonest lie a supervision layer tells is that never-measured means fine.

        ⚠ IT POINTS heart2.STATE AT A TEMP PATH; IT DOES NOT RENAME HIS LIVE FILE. The first cut
        renamed `tv/.heart2.json` to `tv/.heart2.json.lawtest` and renamed it back in a `finally`.
        Two problems, both found by a cross-family review: `.gitignore` matches the exact path
        `tv/.heart2.json` and NOT the suffixed one, so the temporary file was untracked-and-visible
        and a later `git add -A` would commit one machine's runtime census into a public repo; and
        this gate runs in pre-push, which in this repo is routinely killed at the 10-minute
        foreground ceiling — three recorded kills — so an interrupt between the rename and the
        `finally` would leave the real census renamed and the heart reading UNKNOWN for ever.
        A law that can damage the thing it measures is not worth the reading. [[borrowed-surface]]
        """
        import control_app as CA
        import tempfile
        real = heart2.STATE
        d = tempfile.mkdtemp(prefix="heart2law.")
        try:
            heart2.STATE = os.path.join(d, "absent.json")
            got = CA._heart2_census()
            self.assertEqual(got.get("state"), "UNKNOWN",
                             "with no state file the heart reported %r — never-measured must "
                             "never read as healthy" % got.get("state"))
            self.assertIsNone(got.get("proved"),
                              "an absent measurement produced a number: %r" % got.get("proved"))
        finally:
            heart2.STATE = real
            import shutil
            shutil.rmtree(d, ignore_errors=True)

    def test_it_proposes_and_never_edits_a_guard(self):
        """Achilles' reason, verbatim: 'In one night working this tree I introduced three defects
        while fixing others, and I can read a diff.' A repairer of its own instruments is a tool
        that can talk itself into anything.

        ⚠⚠ THIS LAW WAS VACUOUSLY GREEN AND IT WAS THE ONLY ONE ENFORCING THAT PROPERTY. It hunted
        `ast.Name` calls named `open` — and heart2.py uses `io.open` for every one of its writes,
        which parses as `ast.Attribute`. MEASURED: ast.Name open() calls **0**, io.open() calls
        **10**. The assertion loop iterated zero times and the test passed having asserted nothing.
        A blind instrument inside the layer built to catch blind instruments, found by a
        cross-family review rather than by the tree. The instrument check below is the fix: a law
        that cannot find its own subject must fail loudly instead of passing quietly.
        [[zero-needs-a-denominator]] [[feedback-blind-fixture-green-gate]]
        """
        with io.open(os.path.join(HERE, "heart2.py"), encoding="utf-8") as fh:
            src = fh.read()
        tree = ast.parse(src)
        lines = src.splitlines()
        writes = []
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            is_open = ((isinstance(f, ast.Name) and f.id == "open")
                       or (isinstance(f, ast.Attribute) and f.attr == "open"))
            if not is_open:
                continue
            mode = ""
            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                mode = str(n.args[1].value)
            for kw in n.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = str(kw.value.value)
            if "w" in mode or "a" in mode or "+" in mode:
                writes.append(n.lineno)

        # THE INSTRUMENT FIRST — this is the assertion the old version was missing entirely.
        self.assertTrue(
            writes,
            "this law found ZERO write-mode opens in heart2.py. heart2 demonstrably writes its "
            "state file, its proposals file and its sandbox targets, so finding none means the "
            "FINDER is broken and every assertion below passes over an empty list — which is "
            "exactly how this law shipped green while enforcing nothing.")
        print("\n   write-mode opens found in heart2.py: %d" % len(writes))

        for ln in writes:
            ctx = "\n".join(lines[max(0, ln - 8):ln + 1])
            ok = ("STATE" in ctx) or ("PROPOSALS" in ctx) or ("tgt" in ctx)
            self.assertTrue(ok,
                            "heart2.py writes at line %d to something that is neither its state "
                            "file, its proposals file, nor a sandbox target:\n%s" % (ln, ctx))

    def test_a_proof_may_not_tamper_outside_the_sandbox(self):
        """⚠⚠ THE SANDBOX WAS A CLAIM WITH NO CODE BEHIND IT. os.path.join DISCARDS its prefix
        when the second argument is absolute, so a RED_PROOF declaring an absolute `file` — a
        natural copy-paste out of an error message — resolved to his REAL tree, where _prove_one
        truncates and rewrites. The restore is a `finally`; a SIGKILL or the push ceiling would
        leave the defect live, and his console execs the working tree."""
        for name, fn in heart2.gate_files():
            for i, pr in enumerate(heart2.red_proofs_in(fn) or []):
                rel = str(pr.get("file") or "")
                self.assertFalse(os.path.isabs(rel),
                                 "%s[%d] declares an ABSOLUTE file %r — os.path.join would drop "
                                 "the sandbox and tamper the real tree" % (name, i, rel))
                joined = os.path.normpath(os.path.join("/sandbox", rel))
                self.assertTrue(joined.startswith("/sandbox" + os.sep),
                                "%s[%d] escapes the sandbox via %r -> %r" % (name, i, rel, joined))

    def test_the_stored_half_says_how_old_it_is_and_whether_it_was_partial(self):
        """⚠⚠ THE PANEL SAID "derived just now" OVER A CENSUS 49.6 MINUTES OLD.

        _hrtBuild renders the heart panel's own age from d.ageMs, and that age is the LIVE
        derivation — seconds. _hrtInstruments is a different kind of thing: heart2 writes
        tv/.heart2.json and NOTHING refreshes it but a human typing `--ratchet`. control_app
        already SERVES ageMs and partial for that section; MEASURED 2026-09-10, the UI rendered
        NEITHER, so a fifty-minute-old count sat under a banner promising it was fresh.

        v2804's gate asserted only that `"instruments": _heart2_census()` appears in
        control_app.py — its own comment calls that "one layer short of the surface". This is the
        layer it stopped short of. [[stale-reading]] [[zero-needs-a-denominator]]"""
        ui = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
        i = ui.find("function _hrtInstruments")
        self.assertGreater(i, -1, "_hrtInstruments is gone — the heart 2.0 census has no renderer")
        d, j = 0, ui.index("{", i)
        end = j
        while end < len(ui):
            if ui[end] == "{":
                d += 1
            elif ui[end] == "}":
                d -= 1
                if d == 0:
                    break
            end += 1
        body = ui[i:end + 1]
        # ⚠⚠ STRIP THE COMMENTS FIRST. The first cut of this law asserted the substrings against the
        # RAW body — and the explanatory comment I had just written inside _hrtInstruments contains
        # the words "ageMs" and "partial", so the law was satisfied by its own prose. MEASURED:
        # replacing d.ageMs -> d.NOPE and d.partial -> false left it GREEN. A law that reads MENTION
        # instead of BEHAVIOUR is inert, and this is the fourth of that shape today.
        # [[source-reading-guard]] [[sabotage-is-usually-the-wrong-one]]
        body = re.sub(r"/\*(?:.|\n)*?\*/", " ", body)
        body = re.sub(r"(?m)//.*$", " ", body)
        self.assertIn("ageMs", body,
                      "_hrtInstruments does not read d.ageMs, so a stored census renders with no "
                      "age and cannot be told from one measured a second ago")
        self.assertIn("partial", body,
                      "_hrtInstruments does not read d.partial, so a run that proved a SUBSET "
                      "renders as the whole picture — a count with the wrong denominator")

        # ⚠⚠ v2896 — AND NOW THE THINGS THE SHIP ACTUALLY CHANGED, BECAUSE THE TWO ASSERTIONS
        # ABOVE DID NOT PIN THEM. Raised by the cross-family eye on v2892, and it is right: the
        # backend added `oldestProofMs` PRECISELY BECAUSE the file's `ageMs` is the mtime of a
        # write and not the age of the census ("mtime 98 min, median gate proof 569 min"). A law
        # that only asks for the strings `ageMs` and `partial` stays GREEN through the exact
        # regression this ship exists to prevent — delete the `oldestProofMs` branch, keep
        # `d.ageMs`, and the panel goes straight back to advertising a file's mtime as the
        # freshness of 281 gates. Naming the fields is not pinning the behaviour.
        # [[regression-guard]] [[label-outlived-referent]]
        self.assertIn("oldestProofMs", body,
                      "_hrtInstruments no longer reads d.oldestProofMs — the STORED age is back to "
                      "the FILE'S mtime, which any write refreshes, so re-proving three gates "
                      "would make the whole census read fresh")
        _i_old, _i_age = body.find("oldestProofMs"), body.find("ageMs")
        self.assertLess(_i_old, _i_age,
                        "d.ageMs is consulted BEFORE d.oldestProofMs — the fallback has become the "
                        "headline, which is the defect with the fix still present in the file")
        self.assertIn("provenAtCount", body,
                      "_hrtInstruments does not read d.provenAtCount, so the oldest-proof age is "
                      "printed with no denominator: a --prove of 3 gates against an otherwise "
                      "unstamped store renders 'oldest gate proof just now' over ~280 gates that "
                      "nobody has ever looked at")

        # ⚠ AND IT MUST REACH THE MARKUP. Every assertion above is satisfied by a value that is
        # computed and then dropped on the floor — the shape this repo logs as [[plumbing-with-no-
        # tap]]. The `hrt-w` cell is where the reader sees it, so that is what gets pinned.
        _w = re.search(r"hrt-w[^\n]*?>'\s*\+\s*_hrtEsc\(([^;]{0,400})", body)
        self.assertIsNotNone(_w, "the STORED row no longer builds an .hrt-w cell — the age, the "
                                 "PARTIAL flag and the denominator have nowhere to appear")
        _painted = _w.group(1)
        for _var in ("_iAge", "_iPart", "_iDenom"):
            self.assertIn(_var, _painted,
                          "%s is computed and never concatenated into the .hrt-w cell — the value "
                          "is 'read' and reaches no screen, which is indistinguishable from never "
                          "having been served" % _var)


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
# The law that demands re-runnable proofs carries one. Cutting the join is the defect: the proving
# loop would keep measuring perfectly and the heart would never carry a word of it.
# ⚠⚠ THE FIRST PROOF HERE WAS SELF-FULFILLING, and a cross-family review caught it. It tampered
# the string `"instruments": _heart2_census(),` — which DID break the join assertion, and ALSO
# broke test_every_declared_red_proof_is_well_formed in this same file, because that test recounts
# every proof's `find` against the tree and this proof's own `find` then matched 0 instead of 1.
# So the file exited non-zero even with the join assertion deleted outright: --prove would report
# PROVEN without that being evidence the join law works. The one gate meant to demonstrate the
# protocol had a proof that could not tell the law from its own bookkeeping.
# This tamper breaks the census's RETURN SHAPE instead: no proof's `find` is disturbed, the
# well-formed test stays green, and only the join assertion can fail.
# [[sabotage-is-usually-the-wrong-one]]
RED_PROOF = [{
    "why": "a census that returns no `state` leaves the heart unable to say anything about its instruments",
    "file": "control_app.py",
    "find": '            "state": ("DARK" if _blind else ("WATCHED" if _proved else "UNKNOWN")),',
    "replace": '            "stateMISSING": ("DARK" if _blind else ("WATCHED" if _proved else "UNKNOWN")),',
    "matches": 1,
}, {
    # ⚠⚠ THE THREE BELOW WERE ADDED AT v2896 BECAUSE THE CROSS-FAMILY EYE SHOWED THIS LAW COULD
    # NOT GO RED THROUGH THE REGRESSION IT WAS WRITTEN FOR. It asserted the strings `ageMs` and
    # `partial` and nothing else, so the panel could revert to advertising a file's mtime as the
    # freshness of 283 gates and stay green. A red-proof is the only thing that would have caught
    # that, and this law shipped without one covering its own subject.
    "why": "reverting the STORED age to the FILE'S mtime — the exact bug v2892 shipped to fix, "
           "and the one the old assertions could not see",
    "file": "control_ui.html",
    "find": "(typeof d.oldestProofMs === 'number') ? d.oldestProofMs",
    "replace": "(typeof d.ageMs === 'number') ? d.ageMs",
    "matches": 1,
}, {
    "why": "dropping the denominator: the oldest-proof age is then printed over a census whose "
           "other gates may never have been looked at, with nothing on screen saying so",
    "file": "control_ui.html",
    "find": "var _iStamped = (typeof d.provenAtCount === 'number') ? d.provenAtCount : null;",
    "replace": "var _iStamped = null;",
    "matches": 1,
}, {
    "why": "computing all three values and painting none of them — the plumbing-with-no-tap shape "
           "every string-matching assertion in this file was blind to",
    "file": "control_ui.html",
    "find": "_hrtEsc(_iAge + _iPart + _iDenom",
    "replace": "_hrtEsc(''",
    "matches": 1,
}]


if __name__ == "__main__":
    unittest.main(verbosity=2)
