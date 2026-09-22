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

    def test_losing_the_census_restores_the_never_taken_face(self):
        """And back again — a census that stops answering must stop claiming it was clean."""
        f = _paint([CLEAN, None])
        self.assertEqual(f["attrs"].get("data-untaken"), "1")
        self.assertEqual(f["text"], "not taken")

    def test_a_dark_census_then_silence_does_not_keep_the_dark_count(self):
        f = _paint([DARKISH, None])
        self.assertEqual(f["text"], "not taken")
        self.assertNotIn("data-dark", f["attrs"])

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

    # ---- the two ends the painter cannot reach --------------------------------------------

    def test_the_stylesheet_can_actually_colour_it(self):
        """An attribute no rule selects is a flag nobody can see. [[the-unjoined-end]]"""
        src = io.open(UI, encoding="utf-8", errors="replace").read()
        self.assertIn('#heart-chip[data-untaken="1"]', src,
                      "nothing in the stylesheet selects the never-taken chip, so the flag is set "
                      "and painted identically anyway")

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
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
