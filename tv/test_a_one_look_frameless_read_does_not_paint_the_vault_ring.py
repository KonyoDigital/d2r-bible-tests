# -*- coding: utf-8 -*-
"""CI Routine I — A ONE-LOOK FRAMELESS STASH READ DOES NOT PAINT THE VAULT RING.

Routine I on 1d5b706f failed tests/v712_tv_board.spec.ts at the v747 stage: the vault ring
was expected on, and it was off. The read the spec feeds is one stash look with no frame and
no confidence. Vault 2.0 refuses that witness. The stage paints tvn-lc-vault only from the
registrar's filed flag, so the ring stays off. The cast still has the name.

This law drives the shipped door (cut from bible.html, the same cut as the witness law) and
the shipped ring line. It does not add a second door. A throw-out stays unringed even when
filed. Two framed looks still file, and that is the ring. The spec now expects the ring off.

RED_PROOF below.
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import test_every_mule_filing_carries_its_witness as WIT  # noqa: E402

PROOF_NEEDS = ["../tests/v712_tv_board.spec.ts"]

SPEC = os.path.join(ROOT, "tests", "v712_tv_board.spec.ts")
RING_EXPECT = "expect(vault.ring).toBe(false);"


def _ring_line(src):
    lines = [ln.strip() for ln in src.splitlines() if ln.strip().startswith("x.vault =")]
    if len(lines) != 1:
        raise AssertionError("the stage's vault-ring line is not the one assignment: %r" % lines)
    return lines[0]


def _live_stmt(src):
    start = "var _liveW = { lane: 'stash', by: 'tv-live',"
    n = src.count(start)
    if n != 1:
        raise AssertionError("the live witness builder is not the one statement (%d)" % n)
    i = src.index(start)
    j = src.index("};", i)
    return src[i:j + 2]


def _drive():
    src = WIT._src()
    ring = _ring_line(src)
    live = _live_stmt(src)
    body = (
        "var OUT = {};\n"
        "function liveWitness(rd){\n" + live + "\n  return _liveW;\n}\n"
        "function paint(vr){\n  var x = {};\n  " + ring + "\n  return x.vault === true;\n}\n"
        "var oneW = liveWitness({});\n"
        "var one = window.vaultFile('Harlequin Crest', oneW, { mule: 'uni-armor' });\n"
        "OUT.one = { ok: !!(one && one.ok), why: one && one.why,\n"
        "            ring: paint({ ok: true, mode: 'new', filed: !!(one && one.ok) }) };\n"
        "var twoW = { lane: 'stash', by: 'tv-live', sessions: [\n"
        "  { session: 's_a', frame: 'f_a.jpg', conf: 0.9 },\n"
        "  { session: 's_b', frame: 'f_b.jpg', conf: 0.85 }] };\n"
        "var two = window.vaultFile('Harlequin Crest', twoW, { mule: 'uni-armor' });\n"
        "OUT.two = { ok: !!(two && two.ok), why: two && two.why,\n"
        "            ring: paint({ ok: true, mode: 'new', filed: !!(two && two.ok) }) };\n"
        "OUT.throwRing = paint({ ok: true, mode: 'throwout', filed: true });\n"
        "process.stdout.write(JSON.stringify(OUT));\n"
    )
    prog = WIT.HARNESS + WIT._door(src) + body
    r = subprocess.run([WIT.NODE, "-"], input=prog, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("the shipped door would not execute — UNKNOWN, not passing: %s"
                             % (r.stderr or r.stdout)[-800:])
    return json.loads(r.stdout)


@unittest.skipIf(WIT.NODE is None, "node is absent — this law runs the shipped door; UNMEASURED, not passing")
class AOneLookFramelessReadDoesNotPaintTheVaultRing(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.out = _drive()

    def test_one_look_with_no_frame_does_not_file_and_does_not_ring(self):
        one = self.out["one"]
        self.assertFalse(one["ok"], "a one-look frameless stash read was filed: %r" % one)
        self.assertFalse(one["ring"], "the vault ring painted on a read the door refused: %r" % one)
        self.assertIn("needs", one["why"] or "", one)

    def test_two_framed_looks_file_and_the_ring_follows(self):
        two = self.out["two"]
        self.assertTrue(two["ok"], "two framed looks did not file: %r" % two)
        self.assertTrue(two["ring"], "a filed stash name left the vault ring off: %r" % two)

    def test_a_throwout_does_not_wear_the_vault_ring(self):
        self.assertIs(False, self.out["throwRing"], "a throw-out painted the vault ring")

    def test_the_board_spec_expects_the_ring_off(self):
        with open(SPEC, encoding="utf-8") as fh:
            spec = fh.read()
        self.assertEqual(1, spec.count(RING_EXPECT),
                         "the v712 stage no longer expects the vault ring to stay off")
        self.assertNotIn("expect(vault.ring).toBe(true);", spec)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the stage paints the vault ring on every name, including a one-look the door refused",
        "file": "bible.html",
        "find": "x.vault = !!(vr && vr.ok && vr.mode !== 'throwout' && vr.filed !== false);",
        "replace": "x.vault = true;",
        "matches": 1,
    },
    {
        "why": "the stage never paints the vault ring, so a filed two-look read looks unvaulted",
        "file": "bible.html",
        "find": "x.vault = !!(vr && vr.ok && vr.mode !== 'throwout' && vr.filed !== false);",
        "replace": "x.vault = false;",
        "matches": 1,
    },
    {
        "why": "the short-look refusal now accepts, so a frameless read files and the ring lights",
        "file": "bible.html",
        "find": (
            "      return { ok: false, lane: lane, looks: distinct.length, dropped: dropped,\n"
            "               why: 'only ' + distinct.length + ' qualifying look' + (distinct.length === 1 ? '' : 's') + ' in your ' + lane\n"
            "                    + ' — needs ' + VAULT_WITNESS_MIN + '; a look counts only with its own frame and its own conf >= '\n"
            "                    + VAULT_WITNESS_FLOOR + (dropped ? (' (' + dropped + ' did not)') : '') };\n"
        ),
        "replace": (
            "      return { ok: true, kind: 'lane', lane: lane, looks: [{id:'s', frame:'f.jpg', conf:0.9}],"
            " sessions: ['s'], conf: 0.9, reel: 's', frame: 'f.jpg' };\n"
        ),
        "matches": 1,
    },
    {
        "why": "the v712 spec asks for the vault ring on the one-look frameless read again",
        "file": "tests/v712_tv_board.spec.ts",
        "find": "expect(vault.ring).toBe(false);",
        "replace": "expect(vault.ring).toBe(true);",
        "matches": 1,
    },
]
