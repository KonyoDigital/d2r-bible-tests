# -*- coding: utf-8 -*-
"""#80 - A PULSE THAT NEVER FIRED ALSO LEAVES ZERO, SO "ZERO AFTER THE WINDOW" PROVED NOTHING (REG-1518).

The second eye on 6521bda8: tests/v39_polish_invariants.spec.ts '.syncing class is removed after pulse window
(~700ms)' called _v39_pulseAllSyncedCells, slept 1100 ms and expected 0 `.syncing`. The pulse early-returns on
its own 600 ms throttle, and returns before touching anything when no summary cell exists - and BOTH leave 0,
so the one assertion could never fail. Worse, the spec's "bypass" wrote `window._v39_pulseTimer = null`, a
property nobody reads: the binding the pulse checks is the script's top-level `let`, reachable from a test only
by indirect eval.

DRIVEN two ways, because Playwright cannot run here (browser suites run on CI - [[test-venue]]):
  1. the shipped `let _v39_pulseTimer` .. `_v39_pulseAllSyncedCells` cut from bible.html and run in node over a
     stub document holding the cells this law seeds. The cell the spec seeds - a class the pulse itself targets -
     carries `.syncing` right after the pulse and not after the window; a THROTTLED pulse, and a pulse over no
     synced cell, leave 0 at both readings: the vacuity, measured on the real function.
  2. the spec text: the v39 block seeds a cell the pulse actually targets and asserts the class ON before it may
     find it OFF; the sibling blocks the sweep fixed (v1599's overlay, v1520's row, v549's record) show the thing
     before they find it gone; and a ratchet over every tests/*.spec.ts block counts the blocks that reach
     `.toBe(0)` with no positive assertion before it - measured at LIMIT, and it may only go DOWN.
RED_PROOF below.
"""
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable   # its messages carry non-ASCII; a cp1255 console crashes REPORTING them
    _enable()
except Exception:
    pass

ROOT = os.path.dirname(HERE)
BIBLE = os.path.join(ROOT, "bible.html")
TESTS = os.path.join(ROOT, "tests")
NODE = shutil.which("node")

#: The pulse is cut from bible.html by its own two neighbours - never a byte-counted window, which would
#: measure this law's guess about the file instead of the file. [[source-reading-guard]]
PULSE_START = "let _v39_pulseTimer = null;\nfunction _v39_pulseAllSyncedCells() {"
PULSE_END = "\n// Helper: run fn now if DOM is ready"

SPEC = "v39_polish_invariants.spec.ts"
TITLE = ".syncing class is removed after pulse window"
#: ms after the pulse for the second reading - past the 700 ms strip and the 600 ms throttle, well short of a
#: gate timeout. The spec waits 1100.
LATER_MS = 900


def _pulse_source():
    with io.open(BIBLE, encoding="utf-8") as fh:
        src = fh.read()
    i = src.find(PULSE_START)
    j = src.find(PULSE_END, i)
    if i < 0 or j < 0:
        raise AssertionError("_v39_pulseAllSyncedCells is no longer findable in bible.html - this law measures nothing")
    return src[i:j]


def _pulse_classes(block):
    """The class selectors the pulse itself targets - what the PAGE means by 'a synced cell'. -> set"""
    m = re.search(r"querySelectorAll\(\[(.*?)\]\.join\(','\)\)", block, re.S)
    if not m:
        raise AssertionError("the pulse no longer builds its selector list the way this law reads it")
    return set(re.findall(r"'\.([A-Za-z0-9_-]+)'", m.group(1)))


_TEST_HEAD = re.compile(r"^\s*test(?:\.only|\.skip)?\(", re.M)


def _spec_block(fname, title_start):
    """One test block: from `test('<title_start>` to the next test( - bounded by structure, not by bytes."""
    with io.open(os.path.join(TESTS, fname), encoding="utf-8") as fh:
        src = fh.read()
    i = src.find("test('" + title_start)
    if i < 0:
        raise AssertionError("%s no longer has a test titled %r... - this law measures nothing" % (fname, title_start))
    m = _TEST_HEAD.search(src, i + 6)
    return src[i:m.start() if m else len(src)]


def _seeded_class():
    """The class the v39 spec gives its seeded cell. -> str"""
    m = re.search(r"seed\.className = '([A-Za-z0-9_ -]+)'", _spec_block(SPEC, TITLE))
    if not m:
        raise AssertionError("the v39 block seeds no synced cell - with no summary cell rendered its ON premise rests on luck")
    return m.group(1)


_DRIVER = r'''
'use strict';
const SEED = %(seed)s;        // class names, one stub cell each
const ARM = %(arm)s;          // arm the 600 ms throttle first, as a pulse 0-600 ms earlier would have
const AT = %(at)d;            // ms after the pulse for the second reading
const cells = SEED.map(function (cls) {
  const set = new Set([cls]);
  return { id: '', _set: set, classList: {
    add: function (c) { set.add(c); }, remove: function (c) { set.delete(c); }, contains: function (c) { return set.has(c); } } };
});
const document = {
  querySelectorAll: function (sel) {
    const parts = String(sel).split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    return cells.filter(function (el) {
      return parts.some(function (p) { return p[0] === '.' ? el._set.has(p.slice(1)) : (p[0] === '#' && el.id === p.slice(1)); });
    });
  },
};
%(pulse)s
if (ARM) { _v39_pulseTimer = setTimeout(function () { _v39_pulseTimer = null; }, 600); }
_v39_pulseAllSyncedCells();
const count = function () { return cells.filter(function (el) { return el._set.has('syncing'); }).length; };
const t0 = count();
setTimeout(function () { process.stdout.write(JSON.stringify({ t0: t0, later: count(), cells: cells.length })); }, AT);
'''


def _drive(seed, arm=False):
    """Run the SHIPPED pulse in node over stub cells carrying `seed`'s classes. -> {t0, later, cells}"""
    js = _DRIVER % {"seed": json.dumps(seed), "arm": "true" if arm else "false", "at": LATER_MS, "pulse": _pulse_source()}
    fd, path = tempfile.mkstemp(suffix=".js", prefix="v39-pulse-")     # a FILE, never a program on argv
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(js)
        r = subprocess.run([NODE, path], capture_output=True, text=True, timeout=60)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    if r.returncode != 0:
        raise AssertionError("the SHIPPED pulse would not run in node: %s" % (r.stderr or "")[-400:])
    return json.loads(r.stdout)


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class ThePulseDrivenInNode(unittest.TestCase):

    def test_the_seeded_cell_reads_on_right_after_the_pulse_and_off_after_the_window(self):
        cls = _seeded_class()
        r = _drive([cls])
        self.assertEqual(r["cells"], 1, "PREMISE: the stub document holds the one seeded cell")
        self.assertEqual(r["t0"], 1, "the seeded .%s cell did not carry .syncing right after the pulse - it never fired" % cls)
        self.assertEqual(r["later"], 0, "the seeded .%s cell still carries .syncing %d ms after the pulse" % (cls, LATER_MS))

    def test_a_throttled_pulse_attaches_nothing_so_zero_after_the_window_proves_nothing(self):
        r = _drive([_seeded_class()], arm=True)
        self.assertEqual(r["t0"], 0, "a pulse inside the 600 ms throttle attached the class - the throttle is gone")
        self.assertEqual(r["later"], 0, "6521bda8's only assertion - 0 after the window - holds here, on a pulse that never fired")

    def test_a_pulse_over_no_synced_cell_leaves_zero_both_times(self):
        r = _drive(["not-a-synced-cell"])
        self.assertEqual(r["cells"], 1, "PREMISE: the stub document holds the one stranger cell")
        self.assertEqual((r["t0"], r["later"]), (0, 0), "a cell the page does not call synced was pulsed: %r" % r)


class TheSpecRequiresTheClassOnBeforeItMayFindItOff(unittest.TestCase):

    def test_it_asserts_a_positive_syncing_count_before_the_zero(self):
        block = _spec_block(SPEC, TITLE)
        zero = block.find(".toBe(0)")
        self.assertGreater(zero, 0, "the removal claim itself is gone from the block")
        self.assertIsNotNone(re.search(r"toBeGreaterThan\(0\)", block[:zero]),
                             "the block reaches '.toBe(0)' without first requiring .syncing > 0 - a pulse that early-returns "
                             "(throttle) or finds no cell also leaves 0, so it can never fail (6521bda8)")

    def test_it_seeds_a_cell_the_pulse_actually_targets(self):
        seeded = set(_seeded_class().split())
        targets = _pulse_classes(_pulse_source())
        self.assertTrue(seeded & targets,
                        "the spec seeds %s but the pulse targets %s - a cell the page does not call synced never gets the class"
                        % (sorted(seeded), sorted(targets)))

    def test_its_bypass_reaches_the_real_throttle_binding(self):
        block = _spec_block(SPEC, TITLE)
        self.assertIn("eval)('_v39_pulseTimer = null", block,
                      "the throttle is a top-level `let`; only an indirect eval can clear it from a test")
        self.assertNotIn("w._v39_pulseTimer = null", block, "a window property is not the `let` the pulse reads")


class TheFixedSiblingsShowTheThingBeforeTheyFindItGone(unittest.TestCase):

    def test_v1599_sees_the_prompt_overlay_before_it_finds_none_left(self):
        block = _spec_block("v1599_kept_promises.spec.ts", "the prompt cleans itself up")
        zero = block.find(".toBe(0)")
        self.assertGreater(zero, 0, "the 'none left' claim itself is gone from the block")
        self.assertRegex(block[:zero], r"expect\(r\.open\b[^\n]*\.toBe\(1\)",
                         "the overlay is found gone without ever being found present - a uiPrompt that rendered nothing passes")

    def test_v1520_sees_the_row_before_it_finds_no_drawer(self):
        block = _spec_block("v1520_sweep_review.spec.ts", "a name with no evidence shows no drawer")
        zero = block.find(".chron-ev').count()).toBe(0)")
        self.assertGreater(zero, 0, "the 'no drawer' claim itself is gone from the block")
        self.assertRegex(block[:zero], r"expect\(await row\.count\(\)[^\n]*\.toBe\(1\)",
                         "a row that never rendered also has 0 drawers - the row is the denominator")

    def test_v549_has_something_on_record_before_the_reset_empties_it(self):
        block = _spec_block("v549_chronicle_profile_reset.spec.ts", "chronicleReset() flips to fresh + empties")
        self.assertRegex(block, r"expect\(r\.before\b[^\n]*toBeGreaterThanOrEqual\(1\)",
                         "a reset from 0 to 0 proves nothing - the block must show something on record first")
        toggle, reset = block.find("rwToggleMade("), block.find("await w.chronicleReset()")
        self.assertTrue(0 < toggle < reset, "the entry must be put on record BEFORE the reset (toggle at %d, reset at %d)"
                        % (toggle, reset))


#: What counts as the block having SHOWN something before it may find nothing. A `.toBe(0)` that no
#: line before it in the same test( block qualifies is a zero without a premise.
_POS = re.compile(r"toBeGreaterThan(?:OrEqual)?\(|toHaveCount\(\s*[1-9]|\.toBe\(\s*[1-9]|\.toBe\(true\)|toBeTruthy\(|"
                  r"toBeVisible\(|toHaveClass\(|toContain(?:Text)?\(|toMatch\(|toEqual\(|toHaveText\(|toBeDefined\(|"
                  r"not\.toBeNull\(|toBeInstanceOf\(|toHaveAttribute\(|toHaveValue\(|toBeFocused\(|toHaveURL\(|"
                  r"toHaveTitle\(|toHaveLength\(\s*[1-9]|toBeCloseTo\(")
_ZERO = re.compile(r"\.toBe\(\s*0\s*\)")


def zero_without_a_premise():
    """Every tests/*.spec.ts block that reaches `.toBe(0)` with nothing positive asserted before it.
    -> ([(file, line)], blocks_scanned)"""
    found, scanned = [], 0
    for f in sorted(glob.glob(os.path.join(TESTS, "*.spec.ts"))):
        with io.open(f, encoding="utf-8") as fh:
            src = fh.read()
        starts = [m.start() for m in _TEST_HEAD.finditer(src)]
        for k, s in enumerate(starts):
            scanned += 1
            block = src[s:starts[k + 1] if k + 1 < len(starts) else len(src)]
            z = _ZERO.search(block)
            if z and not _POS.search(block[:z.start()]):
                found.append((os.path.basename(f), src.count("\n", 0, s + z.start()) + 1))
    return found, scanned


class TheZeroWithoutAPremiseCountOnlyGoesDown(unittest.TestCase):
    """A ratchet, the way TestTheCountDoesNotGrow ratchets sleep-then-read specs: the blocks left are
    zero-BY-DESIGN cases (an undo with nothing to undo, an empty locker, a removed door) that the sweep read and
    left, and the number may only go DOWN. A new block that finds 0 without first finding anything joins the
    list and is named here."""

    LIMIT = 40   # measured 2026-09-29 (40 of 2217 blocks) after #80's fixes: v39, v1599, v1520, v549 left the list. DOWN only.

    def test_no_new_block_finds_zero_without_first_finding_anything(self):
        found, scanned = zero_without_a_premise()
        self.assertGreater(scanned, 1000, "only %d test( blocks scanned - the parser is broken, not the suite small" % scanned)
        self.assertLessEqual(
            len(found), self.LIMIT,
            "%d spec blocks reach '.toBe(0)' with no positive assertion before it, up from %d. A pulse that early-returns, "
            "a row that never rendered and an overlay that never opened ALL leave 0 - show the thing before you find it "
            "gone (#80). Newest: %s" % (len(found), self.LIMIT, ["%s:%d" % fl for fl in found[-6:]]))

    def test_the_census_sees_a_zero_without_a_premise_when_one_is_planted(self):
        # driven on a planted block, so a regex that drifted off the spec grammar is caught here, not on CI
        block_ok = "test('a', async () => {\n  expect(n).toBe(1);\n  expect(m).toBe(0);\n});\n"
        block_bad = "test('b', async () => {\n  await go();\n  expect(m).toBe(0);\n});\n"
        for text, want in ((block_ok, False), (block_bad, True)):
            z = _ZERO.search(text)
            self.assertIsNotNone(z)
            self.assertEqual(not _POS.search(text[:z.start()]), want, text)


RED_PROOF = [
    {
        "why": "2026-09-29 - the pulse adds the class to nothing again: the seeded synced cell never reads ON (the first "
               "way 6521bda8's assertion was satisfied by nothing)",
        "file": "bible.html",
        "find": "  targets.forEach(el => el.classList.add('syncing'));\n",
        "replace": "  targets.forEach(el => el.classList.add('syncing-never'));\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the class is never stripped after the window: the half the spec is titled for",
        "file": "bible.html",
        "find": "  setTimeout(() => {\n    targets.forEach(el => el.classList.remove('syncing'));\n  }, 700);\n",
        "replace": "  if (false) setTimeout(() => {\n    targets.forEach(el => el.classList.remove('syncing'));\n  }, 700);\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the v39 spec drops its premise again: 0 after the window with nothing shown ON first",
        "file": "tests/v39_polish_invariants.spec.ts",
        "find": "    expect(during.total, 'no cell carries .syncing right after the pulse — it never fired, so a later 0 "
                "proves nothing').toBeGreaterThan(0);\n",
        "replace": "    // (the premise 6521bda8 shipped without)\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - v1599's overlay is found gone without ever being found present (and the ratchet counts it)",
        "file": "tests/v1599_kept_promises.spec.ts",
        "find": "    expect(r.open, 'the prompt overlay never appeared, so \"none left\" measures nothing').toBe(1);\n",
        "replace": "    // (the premise the sweep added)\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - v1520's drawer is found absent on a row never shown to render",
        "file": "tests/v1520_sweep_review.spec.ts",
        "find": "    expect(await row.count(), 'the Windforce row must render before its drawer can be judged').toBe(1);\n",
        "replace": "    // (the premise the sweep added)\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
