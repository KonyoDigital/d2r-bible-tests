# -*- coding: utf-8 -*-
"""v3414 — A CENSUS NOBODY TOOK IS NOT A CLEAN ONE.

`_heartChipPaint` had two branches and they painted IDENTICAL pixels:

    if (!d || !d.ok || !d.counts) {
      nm.textContent = 'heart';                    <-- the not-derived branch
      el.removeAttribute('data-dark');
    ...
    nm.textContent = dark ? (dark + ' dark') : 'heart';   <-- a taken, clean census
    if (dark) el.setAttribute('data-dark','1'); else el.removeAttribute('data-dark');

Same text, same attribute, same everything. The ONLY difference was `el.title`, and a title
needs a hover — so on his status bar "the census has never been taken" and "the census is
taken and nothing is dark" were the same word. RESUME_HERE.md records the live symptom: his
Mac console's eagle reported `rows: 0, "not measured yet"` and the chip could not tell him.

⚠ THIS GATE DRIVES THE SHIPPED FUNCTION, IT DOES NOT READ IT. A source check would pass on a
file that merely CONTAINS 'not taken' somewhere; the question is what the element ends up
showing, so the real `_heartChipPaint` is extracted from control_ui.html and executed in node
against a stub element, and every verdict is read off that element afterwards.

[[unknown-stays-unknown]] — 0-measured and nobody-looked collapsed into one face.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

UI = os.path.join(HERE, "control_ui.html")


def _node():
    return shutil.which("node") or shutil.which("nodejs")


def _fn_source():
    """The SHIPPED _heartChipPaint, bounded by its own closing brace — never a byte window."""
    src = io.open(UI, encoding="utf-8", errors="replace").read()
    i = src.find("function _heartChipPaint(d){")
    assert i >= 0, "_heartChipPaint is gone from control_ui.html"
    end = src.find("\n  }", i)
    assert end > i, "_heartChipPaint has no closing brace where one is expected"
    return src[i:end + 4]


def _paint(censuses):
    """Paint each census onto ONE stub element, in order. -> the element's final face."""
    prog = (
        "var window = {};\n"
        "var EL = { attrs: {}, title: '',"
        "  setAttribute: function(k, v){ this.attrs[k] = v; },"
        "  removeAttribute: function(k){ delete this.attrs[k]; } };\n"
        "var NM = { textContent: '' };\n"
        "var document = { getElementById: function(id){\n"
        "  if (id === 'heart-chip') return EL;\n"
        "  if (id === 'heart-chip-n') return NM;\n"
        "  return null; } };\n"
        + _fn_source() + "\n"
        "var INPUT = " + json.dumps(censuses) + ";\n"
        "INPUT.forEach(function(d){ _heartChipPaint(d); });\n"
        "console.log(JSON.stringify({ text: NM.textContent, attrs: EL.attrs, title: EL.title }));\n"
    )
    p = subprocess.run([_node(), "-e", prog], capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise AssertionError("node could not run the shipped painter: %s" % (p.stderr or "")[:300])
    return json.loads(p.stdout.strip().split("\n")[-1])


def _face(f):
    """What his EYE can tell apart: the text and the attributes. Never the title."""
    return (f["text"], tuple(sorted(f["attrs"].items())))


NEVER_TAKEN = [None, {"ok": False}, {"ok": True}, {"ok": True, "counts": None}]
CLEAN = {"ok": True, "counts": {"FLOWING": 20, "WATCHED": 0, "DARK": 0, "UNKNOWN": 0}}
DARKISH = {"ok": True, "counts": {"FLOWING": 17, "WATCHED": 0, "DARK": 3, "UNKNOWN": 0}}


class TestACensusNobodyTookIsNotACleanOne(unittest.TestCase):

    def setUp(self):
        if not _node():
            self.skipTest("no node on this machine — the painter cannot be EXECUTED, and reading "
                          "the source instead would answer a different question")

    # ---- the baseline: without the fix these two are the same pixels ----------------------

    def test_BASELINE_the_clean_census_paints_a_face_at_all(self):
        """If the clean census painted nothing, every comparison below would be vacuous."""
        f = _paint([CLEAN])
        self.assertTrue(f["text"], "a taken, clean census painted no text at all — the cases "
                                   "below would then be comparing two empty faces")

    def test_never_taken_and_clean_are_DIFFERENT_faces(self):
        """The whole defect, in one assertion, read off the element and not off the title."""
        for d in NEVER_TAKEN:
            self.assertNotEqual(
                _face(_paint([d])), _face(_paint([CLEAN])),
                "a census nobody took paints the SAME face as a clean one for %r — this is the "
                "v3414 defect: only the title differed, and a title needs a hover" % (d,))

    def test_the_title_alone_is_not_allowed_to_carry_it(self):
        """Proves the distinction survives when the title is discarded — which is what he sees."""
        a, b = _paint([NEVER_TAKEN[0]]), _paint([CLEAN])
        self.assertNotEqual(a["text"] + str(sorted(a["attrs"])), b["text"] + str(sorted(b["attrs"])),
                            "the two states differ only in the title")

    # ---- each state says its own thing ----------------------------------------------------

    def test_an_untaken_census_says_so_in_words(self):
        for d in NEVER_TAKEN:
            self.assertEqual(_paint([d])["text"], "not taken",
                             "census %r did not say it was never taken" % (d,))

    def test_an_untaken_census_is_flagged_for_css(self):
        for d in NEVER_TAKEN:
            self.assertEqual(_paint([d])["attrs"].get("data-untaken"), "1",
                             "census %r left no attribute for the stylesheet to colour" % (d,))

    def test_a_clean_census_is_not_flagged_untaken(self):
        f = _paint([CLEAN])
        self.assertNotIn("data-untaken", f["attrs"],
                         "a census that WAS taken is wearing the never-taken face")
        self.assertEqual(f["text"], "heart")

    def test_a_dark_census_still_reports_its_count(self):
        f = _paint([DARKISH])
        self.assertEqual(f["text"], "3 dark")
        self.assertEqual(f["attrs"].get("data-dark"), "1")
        self.assertNotIn("data-untaken", f["attrs"])

    # ---- the state must not carry over, in either direction -------------------------------

    def test_taking_the_census_CLEARS_the_never_taken_face(self):
        """The real sequence on his console: the chip boots untaken, then /api/heart answers."""
        f = _paint([None, CLEAN])
        self.assertNotIn("data-untaken", f["attrs"],
                         "the chip kept the never-taken flag after the census came back")
        self.assertEqual(f["text"], "heart",
                         "the chip kept the never-taken WORD after the census came back")

    def test_a_failure_AFTER_a_census_does_not_un_take_it(self):
        """⚠ v3417 REVERSED v3414 HERE, DELIBERATELY. This used to assert the chip fell back to
        'not taken' when a later read failed. The second eye showed why that is wrong: TWO
        painters reach the chip with no ordering — the overlay's fetch and the deferred 4 s read
        — so an overlay census followed by a failing deferred read flipped the chip to
        'not taken' while the overlay still displayed the census it had just drawn. 'Not taken'
        is a claim about whether a census has EVER arrived; once one has, it has. The overlay
        reports the current failure. [[stale-reading]]"""
        f = _paint([CLEAN, None])
        self.assertNotIn("data-untaken", f["attrs"],
                         "a failed read un-took a census that had already arrived")
        self.assertEqual(f["text"], "heart")

    def test_a_dark_census_then_silence_KEEPS_the_count_he_was_shown(self):
        f = _paint([DARKISH, None])
        self.assertEqual(f["text"], "3 dark",
                         "a later failure erased a DARK count he had already been shown")
        self.assertEqual(f["attrs"].get("data-dark"), "1")

    # ---- the two failure arms must REACH the chip ------------------------------------------

    def test_the_deferred_read_does_not_swallow_its_own_failure(self):
        """This is the chip's ONLY scheduled read. Swallowing it left the face resting on boot
        markup nothing in the script is joined to. [[the-unjoined-end]]"""
        src = io.open(UI, encoding="utf-8", errors="replace").read()
        self.assertIn("['catch'](function(){ _heartChipPaint(null); });", src,
                      "the chip's only census read swallows its failure, so a console that never "
                      "answered leaves the chip wearing whatever the HTML happened to say")

    def test_the_overlay_failure_arm_repaints_the_chip_too(self):
        """The overlay prints THE CONSOLE DID NOT ANSWER; the chip beside it must not keep the
        last clean census. Two surfaces of one fact must not disagree. [[stale-reading]]"""
        src = io.open(UI, encoding="utf-8", errors="replace").read()
        i = src.find("a failed fetch is not an empty heart")
        self.assertGreater(i, 0, "the overlay's failure arm is gone")
        arm = src[i:src.find("['finally']", i)]
        self.assertIn("_heartChipPaint(null);", arm,
                      "the overlay says the console did not answer while the chip beside it still "
                      "wears the last clean face")

    # ---- the two languages must split the SAME payload the same way -----------------------

    def test_an_empty_counts_object_is_not_a_taken_census(self):
        """`{}` is TRUTHY in JS and FALSY in Python. Before v3417 the chip painted the CLEAN face
        for {"ok":true,"counts":{}} while the doctor row called the same payload MISSING and told
        him the chip was reading 'not taken'. Both halves wrong."""
        f = _paint([{"ok": True, "counts": {}}])
        self.assertEqual(f["text"], "not taken",
                         "an empty counts object painted a CLEAN heart — the chip is claiming a "
                         "census that carried nothing")
        self.assertEqual(f["attrs"].get("data-untaken"), "1")

    def test_a_counts_that_is_a_list_is_not_a_census_either(self):
        f = _paint([{"ok": True, "counts": []}])
        self.assertEqual(f["text"], "not taken")

    def test_THE_JOIN_the_chip_and_the_doctor_row_agree_on_every_payload(self):
        """A CORROBORATOR ACROSS TWO LANGUAGES. The row says what his SCREEN shows, so a payload
        the row calls un-feedable must be one the chip actually paints as un-taken, and one it
        calls fine must be one the chip paints as a census. [[heart-first]] §1"""
        import types
        import console_doctor as _cd
        row = dict(_cd.CHECKS)["the chip can say nobody looked"]
        PAYLOADS = [
            {"ok": True, "counts": {"FLOWING": 20, "WATCHED": 0, "DARK": 0, "UNKNOWN": 0}},
            {"ok": True, "counts": {"DARK": 3}},
            {"ok": True, "counts": {}},
            {"ok": True, "counts": []},
            {"ok": True},
            {"ok": False, "why": "the census could not read the tree"},
        ]
        bad = []
        for d in PAYLOADS:
            m = types.ModuleType("control_app")
            m.heart_state = (lambda _d=d: _d)
            old = sys.modules.get("control_app")
            sys.modules["control_app"] = m
            try:
                st, _why = row()
            finally:
                if old is not None:
                    sys.modules["control_app"] = old
                else:
                    sys.modules.pop("control_app", None)
            chip_untaken = _paint([d])["attrs"].get("data-untaken") == "1"
            row_unfeedable = (st != _cd.OK)
            if chip_untaken != row_unfeedable:
                bad.append((d, "chip untaken=%s" % chip_untaken, "row=%s" % st))
        self.assertEqual(bad, [], "the chip and the doctor row disagree about %d payload(s): %r "
                                  "— the row is describing a screen that shows something else"
                                  % (len(bad), bad))

    # ---- v3419: silence and an empty ANSWER are different events ---------------------------

    def test_an_EMPTY_census_AFTER_a_real_one_still_paints_not_taken(self):
        """⚠ THE DEFECT v3417's LATCH CREATED. `_hrtSawCensus` suppressed every later non-census
        paint, so an empty census arriving after a real one left the clean face up while the
        doctor row called that same payload MISSING. A failed FETCH is silence; a payload that
        CAME BACK carrying nothing is an ANSWER, and the answer is that there is no census."""
        f = _paint([CLEAN, {"ok": True, "counts": {}}])
        self.assertEqual(f["text"], "not taken",
                         "an empty census after a real one left the clean face up — the "
                         "cross-language split, reopened by the guard that was meant to close it")
        self.assertEqual(f["attrs"].get("data-untaken"), "1")

    def test_a_refused_census_after_a_real_one_also_paints(self):
        f = _paint([CLEAN, {"ok": False, "why": "the census could not read the tree"}])
        self.assertEqual(f["text"], "not taken")

    def test_a_PARTIAL_census_says_question_mark_not_a_zero(self):
        """{FLOWING:8} has keys, so it IS a census — but DARK is absent, and `c.DARK || 0` used to
        coerce that to a measured zero and paint the clean 'heart' while the doctor printed `?`
        for the same key. [[unknown-stays-unknown]]"""
        f = _paint([{"ok": True, "counts": {"FLOWING": 8}}])
        self.assertEqual(f["text"], "? dark",
                         "an absent DARK key was painted as a measured zero and read 'heart'")
        self.assertNotIn("data-dark", f["attrs"])
        self.assertIn("?", f["title"])

    def test_a_census_with_a_real_zero_still_reads_heart(self):
        """A measured zero must NOT become a question mark — that would be the same lie inverted."""
        f = _paint([{"ok": True, "counts": {"FLOWING": 8, "WATCHED": 0, "DARK": 0, "UNKNOWN": 0}}])
        self.assertEqual(f["text"], "heart")

    def test_THE_JOIN_holds_over_SEQUENCES_not_just_single_payloads(self):
        """⚠ WHY THIS EXISTS: the single-payload join could never have caught v3417's latch,
        because every _paint() runs in a FRESH node process and the latched state is never
        reached. A join that cannot see the stateful path is a join that grades the easy half."""
        import types
        import console_doctor as _cd
        row = dict(_cd.CHECKS)["the chip can say nobody looked"]
        ANSWERS = [
            {"ok": True, "counts": {"FLOWING": 20, "WATCHED": 0, "DARK": 0, "UNKNOWN": 0}},
            {"ok": True, "counts": {"DARK": 3}},
            {"ok": True, "counts": {}},
            {"ok": True, "counts": []},
            {"ok": True},
            {"ok": False, "why": "refused"},
        ]
        bad = []
        for d in ANSWERS:
            old = sys.modules.get("control_app")
            m = types.ModuleType("control_app")
            m.heart_state = (lambda _d=d: _d)
            sys.modules["control_app"] = m
            try:
                st, _why = row()
            finally:
                if old is not None:
                    sys.modules["control_app"] = old
                else:
                    sys.modules.pop("control_app", None)
            # the REAL sequence on his console: a census lands, then this payload arrives
            chip_untaken = _paint([CLEAN, d])["attrs"].get("data-untaken") == "1"
            row_unfeedable = (st != _cd.OK)
            if chip_untaken != row_unfeedable:
                bad.append((d, "chip untaken=%s" % chip_untaken, "row=%s" % st))
        self.assertEqual(bad, [], "AFTER A CENSUS, the chip and the doctor row disagree about %d "
                                  "payload(s): %r — the row describes a screen showing something "
                                  "else" % (len(bad), bad))

    # ---- the two ends the painter cannot reach --------------------------------------------

    def test_the_stylesheet_can_actually_colour_it(self):
        """An attribute no rule selects is a flag nobody can see. [[the-unjoined-end]]"""
        # ⚠ v3417 — GRADE THE CODE, NOT THE PROSE. This was a whole-file substring search, so a
        # COMMENT mentioning the selector would satisfy it while the rule itself was gone — the
        # [[source-reading-guard]] §4b shape, in my own gate. Block comments are stripped with a
        # BOUNDED pattern; an unbounded /\*.*?\*/ over this 5-6 MB mixed file deletes a sixth of
        # it. The eye reported the rule missing outright; that half was REFUTED — it is at line
        # 6208 and the payload had simply stripped the comment block it sits in.
        import re as _re
        raw = io.open(UI, encoding="utf-8", errors="replace").read()
        # ⚠ v3419 — 4,000 WAS ITSELF A GUESS, AND A LONGER COMMENT SLIPPED UNDER IT. A block
        # comment of 4,001+ chars was left whole, so the selector could hide inside one with the
        # live rule deleted and this would still pass. HTML comments and // lines were not
        # stripped at all. The bound stays FINITE on purpose — an unbounded /\*.*?\*/ over this
        # 5-6 MB mixed file deletes a sixth of it and 170 of its 444 id= declarations — but it is
        # now far above any real comment here, and the other two comment forms are stripped too.
        code = _re.sub(r"/\*.{0,60000}?\*/", lambda m: "\n" * m.group(0).count("\n"), raw,
                       flags=_re.S)
        code = _re.sub(r"<!--.{0,60000}?-->", lambda m: "\n" * m.group(0).count("\n"), code,
                       flags=_re.S)
        code = "\n".join(_re.sub(r"(^|\s)//.*$", "", ln) for ln in code.split("\n"))
        self.assertIn('#heart-chip[data-untaken="1"]', code,
                      "nothing in the stylesheet selects the never-taken chip OUTSIDE A COMMENT, "
                      "so the flag is set and painted identically anyway")

    def test_the_chip_boots_untaken(self):
        """Before the first paint nobody has taken the census either."""
        src = io.open(UI, encoding="utf-8", errors="replace").read()
        i = src.find('id="heart-chip"')
        self.assertGreater(i, 0, "the chip is gone from the markup")
        btn = src[i:src.find("</button>", i)]
        self.assertIn('data-untaken="1"', btn,
                      "the chip boots without the never-taken flag, so it renders as clean until "
                      "the first census answers")
        self.assertIn(">not taken<", btn,
                      "the chip boots reading 'heart', which is the clean face")


RED_PROOF = [
    {
        "why": "v3414 — THE COLLAPSE, RESTORED. Painting 'heart' for a census nobody took is the "
               "exact pre-fix behaviour: it makes a never-measured heart read as a clean one on "
               "his status bar, with only a title to tell them apart.",
        "file": "control_ui.html",
        "find": "      nm.textContent = 'not taken';",
        "replace": "      nm.textContent = 'heart';",
        "matches": 1,
    },
    {
        "why": "v3414 — THE FLAG WITHHELD. Without data-untaken the stylesheet has nothing to "
               "colour, so the never-taken chip is drawn in the same ink as a clean one.",
        "file": "control_ui.html",
        "find": "      el.setAttribute('data-untaken', '1');",
        "replace": "      el.removeAttribute('data-untaken');",
        "matches": 1,
    },
    {
        "why": "v3414 — THE FLAG NEVER CLEARED. A census that DID answer must drop the "
               "never-taken face; leaving it set means the chip goes on claiming nobody looked "
               "long after somebody did, which is the same lie pointing the other way.",
        "file": "control_ui.html",
        "find": "    el.removeAttribute('data-untaken');",
        "replace": "    el.setAttribute('data-untaken', '1');",
        "matches": 1,
    },
    {
        "why": "v3414 - THE SWALLOW, RESTORED. An empty catch on the chip's ONLY scheduled census "
               "read means a console that never answered leaves the chip showing whatever the "
               "markup said, so the face is honest only by accident.",
        "file": "control_ui.html",
        "find": "['catch'](function(){ _heartChipPaint(null); });",
        "replace": "['catch'](function(){});",
        "matches": 1,
    },
    {
        "why": "v3414 - THE OVERLAY TELLS THE TRUTH ALONE. Without this the overlay prints THE "
               "CONSOLE DID NOT ANSWER while the chip two centimetres away still wears the last "
               "clean census - two surfaces of one fact, disagreeing.",
        "file": "control_ui.html",
        "find": "      _heartChipPaint(null);\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "v3417 - THE TRUTHINESS SPLIT, RESTORED. `{}` is TRUTHY in JS and FALSY in Python, "
               "so a bare truthiness test lets an EMPTY census paint the clean face here while "
               "the doctor row calls the same payload MISSING and says the chip reads 'not "
               "taken'. One payload, two surfaces, both wrong.",
        "file": "control_ui.html",
        "find": "    var _hasCensus = !!(_cts && typeof _cts === 'object' && !(_cts instanceof Array)\n                        && Object.keys(_cts).length);",
        "replace": "    var _hasCensus = !!_cts;",
        "matches": 1,
    },
    {
        "why": "v3417 - THE RACE GUARD REMOVED. Two painters reach this function with no "
               "ordering: the overlay fetch and the deferred 4 s read. Without the guard an "
               "overlay census followed by a failing deferred read flips the chip to 'not taken' "
               "while the overlay still shows the census it just drew.",
        "file": "control_ui.html",
        # ⚠ v3419 — RE-ANCHORED, AND heart2 IS WHAT CAUGHT IT. v3419 rewrote this very line to
        # separate silence from an empty answer, so the old anchor matched ZERO times and the
        # proof reported INVALID rather than red. A red-proof whose anchor has drifted proves
        # nothing — and it drifts exactly when the code it guards gets better.
        # [[source-reading-guard]] §2 — print the match count, always.
        "find": "      if (!(d && typeof d === 'object') && window._hrtSawCensus) return;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "v3419 - THE STICKY LATCH, RESTORED. Suppressing every later non-census paint means "
               "an EMPTY census arriving after a real one leaves the clean face up while the "
               "doctor calls that same payload MISSING - the split v3417 closed, reopened by "
               "v3417's own guard. Silence is not an empty answer.",
        "file": "control_ui.html",
        "find": "      if (!(d && typeof d === 'object') && window._hrtSawCensus) return;",
        "replace": "      if (window._hrtSawCensus) return;",
        "matches": 1,
    },
    {
        "why": "v3419 - THE ABSENT KEY COERCED BACK TO ZERO. With `dark` falling back to 0 a "
               "census carrying only {FLOWING:8} paints the clean 'heart' while the doctor prints "
               "`?` for the very same missing key.",
        "file": "control_ui.html",
        "find": "    nm.textContent = (dark === null) ? '? dark' : (dark ? (dark + ' dark') : 'heart');",
        "replace": "    nm.textContent = dark ? (dark + ' dark') : 'heart';",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
