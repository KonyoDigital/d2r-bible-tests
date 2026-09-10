"""THE ONE INSTRUMENT THAT CAN SEE A DEAD WINDOW MUST SAY SO WHERE SOMEONE CAN READ IT.

⚠⚠ MEASURED ON HIS LIVE CONSOLE 2026-09-10, and the numbers are the whole case:

    console uptime            1h27m
    _console_rescue_loop      FLOWING — "it ran 8s ago, within its own 10s period"
    _pixel_blank_report       fires every 6th tick  ->  ~87 firings in that window
    paint_witness answer      state=OCCLUDED, "Terminal (100.0%) is on top of it"
    /api/status uiBeat keys   ageS · blankStrikes · elsHigh · elsNow · elsWindowN · frozenBeats ·
                              hidden · lastRescueWhy · n · paintWhy · painting · panels · raf ·
                              rescues · silenceBoundS · view
    'pixelBlank' in uiBeat    False

Sixteen keys, none of them the pixel verdict. The witness ran, answered correctly every time, wrote
its answer into `_UI_BEAT`, and **nothing put it on the wire**. `_pixel_blank_report`'s own comment
says the gap out loud — *"PUBLISHED IS NOT SHOWN. What belongs here is louder reporting"* — and it
has recorded `console-pixels-blank-nothing-else-saw-it` 73 times across 8 days while he still found
the fault by looking at a black screen.

⚠ THE COST WAS PAID THE SAME DAY, BY THE ONE READER WHO MOST NEEDED IT. Grok Bot, reading exactly
those sixteen fields, reported the window **FROZEN — pixels dead** (`hidden=false`, `painting=true`,
capture hash static across a whole look). Asked directly, the witness said **OCCLUDED**. A covered
window returns a uniform frame forever, so its captures are byte-identical — the same signature as a
freeze. The field that separates them existed, was correct, was current, and was not published.

⚠ THREE ANSWERS, NEVER TWO — this is the law, not the plumbing. `state=None` means NOT ASKED.
OCCLUDED is a clean result. BLANK is the fault. Any pair collapsed and the field is worse than
absent, because it would then be trusted. [[the-unjoined-end]] [[plumbing-with-no-tap]]
[[unknown-stays-unknown]] [[zero-needs-a-denominator]]
"""
import ast
import io
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "control_app.py")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ verbosity=2 prints every docstring and they all open with a warning sign; on a cp1255 console
# that is a crash WHILE REPORTING. This exact refusal blocked a push on 2026-09-10.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()


def _src():
    return io.open(APP, encoding="utf-8").read()


def _fn(name):
    """The AST node for a top-level function. -> FunctionDef

    ⚠ PARSED, NOT GREPPED. A law about where a key is published must read the STRUCTURE; a text
    search cannot tell a real dict entry from the same words inside a comment, and this file is
    mostly comments by volume. [[source-reading-guard]]
    """
    for n in ast.walk(ast.parse(_src())):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    raise AssertionError("%s() is gone from control_app.py — this gate did not reach its subject, "
                         "so its silence is not evidence" % name)


def _publishes(fn_name, key):
    """Does this function build a dict literal carrying `key`? -> bool"""
    for n in ast.walk(_fn(fn_name)):
        if isinstance(n, ast.Dict):
            for k in n.keys:
                if isinstance(k, ast.Constant) and k.value == key:
                    return True
    return False


class ThePixelVerdictReachesTheWire(unittest.TestCase):

    def test_the_status_payload_carries_the_pixel_verdict(self):
        """THE ONE THAT MATTERS. Sixteen uiBeat keys shipped without it for eight days."""
        self.assertTrue(_publishes("status_payload", "pixelBlank"),
                        "status_payload() does not publish `pixelBlank`, so the only instrument "
                        "that can tell a dead window from a covered one answers to nobody — which "
                        "is how a FROZEN report was filed about an OCCLUDED window")

    def test_the_pre_rescue_snapshot_carries_it_too(self):
        """The snapshot is what a supervisor reads when deciding whether to act. It carries
        `painting`, `frozenBeats` and `blankStrikes` — every counter that is STRUCTURALLY blind to
        this fault — so omitting the one that is not blind makes it a curated view of the wrong
        evidence."""
        self.assertTrue(_publishes("ui_pre_rescue_snapshot", "pixelBlank"),
                        "ui_pre_rescue_snapshot() publishes the page's own counters but not the "
                        "pixel verdict, so a supervisor sees only the signals that cannot see "
                        "this fault")

    def test_not_asked_is_not_the_same_as_nothing_wrong(self):
        """⚠ THE FIELD IS WORSE THAN ABSENT IF IT LIES ABOUT SILENCE. Before the first firing —
        and every exec restarts that clock — the honest answer is UNKNOWN."""
        import control_app as CA
        got = CA.pixel_witness_public({})
        self.assertIsNone(got.get("state"),
                          "with no reading yet the state must be None (NOT ASKED), not a verdict: "
                          "%r" % got)
        self.assertIsNone(got.get("ageS"), "an unasked reading has no age: %r" % got)
        why = (got.get("why") or "").lower()
        self.assertTrue("not been asked" in why or "unknown" in why,
                        "the why must say it was never asked rather than describing the pixels: "
                        "%r" % got)

    def test_occluded_and_blank_do_not_collapse_into_each_other(self):
        """His measured OCCLUDED reading and a genuine BLANK must be different answers on the wire.
        They produce IDENTICAL captures, which is the entire reason this field exists."""
        import control_app as CA
        now = int(time.time() * 1000)
        occ = CA.pixel_witness_public({"pixelBlank": {
            "state": "OCCLUDED", "strikes": 0, "ts": now,
            "why": "NOT blank - Terminal (100.0%) is on top of it, so he cannot see it"}})
        blank = CA.pixel_witness_public({"pixelBlank": {
            "state": "BLANK", "strikes": 3, "ts": now,
            "why": "brightest 1% at luminance 27; a painted console reads ~177"}})
        self.assertEqual(occ.get("state"), "OCCLUDED")
        self.assertEqual(blank.get("state"), "BLANK")
        self.assertNotEqual(occ.get("state"), blank.get("state"),
                            "a covered window and a dead one must not report the same state")
        self.assertEqual(occ.get("strikes"), 0)
        self.assertEqual(blank.get("strikes"), 3)

    def test_the_reading_carries_its_own_age(self):
        """⚠ A verdict from before the last exec is a STALE verdict, and the console re-execs on
        every version bump. Without an age the reader cannot tell. [[stale-reading]]"""
        import control_app as CA
        got = CA.pixel_witness_public({"pixelBlank": {
            "state": "PAINTED", "strikes": 0, "why": "x",
            "ts": int((time.time() - 42.0) * 1000)}})
        self.assertIsInstance(got.get("ageS"), float,
                              "the reading must carry its own age in seconds: %r" % got)
        self.assertGreater(got.get("ageS"), 40.0, "age should be ~42s: %r" % got)
        self.assertLess(got.get("ageS"), 60.0, "age should be ~42s: %r" % got)

    def test_a_malformed_reading_is_UNKNOWN_and_never_a_verdict(self):
        """A writer that half-failed must not be laundered into a clean answer."""
        import control_app as CA
        for junk in ("BLANK", 3, [], None):
            got = CA.pixel_witness_public({"pixelBlank": junk})
            self.assertIsNone(got.get("state"),
                              "a non-dict reading (%r) must read as NOT ASKED, never as a "
                              "verdict: %r" % (junk, got))


RED_PROOF = [
    {
        "why": "removing the key from status_payload restores the exact state measured on his "
               "console: sixteen uiBeat fields, none of them the pixel verdict, and an outside "
               "reader left to infer paint from a capture hash that is identical for a covered "
               "window and a dead one.",
        "file": "control_app.py",
        "find": '                   "pixelBlank": pixel_witness_public(),',
        "replace": '                   "_pixelBlankRemovedByHeart2": None,',
        "matches": 1,
    },
    {
        "why": "removing it from the pre-rescue snapshot leaves a supervisor reading only the "
               "counters that are structurally blind to this fault.",
        "file": "control_app.py",
        "find": '        "pixelBlank": pixel_witness_public(b),',
        "replace": '        "_pixelBlankRemovedByHeart2": None,',
        "matches": 1,
    },
    {
        "why": "making 'never asked' report a clean PAINTED verdict is the lie this field exists "
               "to prevent - silence becoming evidence of health.",
        "file": "control_app.py",
        "find": '        return {"state": None, "why": "the pixels have not been asked yet on this process — "',
        "replace": '        return {"state": "PAINTED", "why": "the pixels have not been asked yet on this process — "',
        "matches": 1,
    },
    {
        "why": "dropping the age turns a verdict from before the last exec into one that looks "
               "current, and the console re-execs on every version bump.",
        "file": "control_app.py",
        "find": '        "ageS": (round(max(0.0, time.time() - (_ts / 1000.0)), 1)',
        "replace": '        "ageS": (None if True else round(max(0.0, time.time() - (_ts / 1000.0)), 1)',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
