# -*- coding: utf-8 -*-
"""#171 (REG-2480) - AN EYE ROW ASKS ONLY A PC THAT SHIPS.

MEASURED on Dean's PC 2026-10-22 02:44 - a PC that has never shipped a version, whose EYES is Claude-only: the eagle
billed it two MISSING rows ('this machine can get a second opinion', 'the eye seat can be filled' - grok.exe absent)
and eleven UNKNOWN 'unaskable for 31d' rows over a second-eye ledger that does not exist there. Thirteen rows about the
SHIP-TIME instrument, on a PC that does not ship.

console_doctor.this_pc_ships() is ONE measured predicate - its second-eye ledger exists, OR its eye binary exists, OR
its tree is a development tree - and run() asks every row in SHIP_EYE_ROWS through it:
  * measured NOT shipping (all three read, none holds) -> OK, with the one sentence and what was measured;
  * shipping -> the row's own question, unchanged (an absent binary is still today's MISSING);
  * an input that could not be read -> the row's own question, unchanged: nothing is relabelled on a guess.
And no fifth state word: the eagle counts ok / missing / unknown / unmeasured, and only those.
[[unknown-stays-unknown]] [[per-pc-personal-data]]
"""
import contextlib
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import fixture_ledgers as _fx_ledgers  # noqa: E402  never HIS eagle ledgers - this law drives run()
_fx_ledgers.redirect()
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

import console_doctor as CD  # noqa: E402
import second_eye_ledger as SEL  # noqa: E402
import second_eye_run as SER  # noqa: E402
import self_prove as SP  # noqa: E402

STATES = (CD.OK, CD.MISSING, CD.UNKNOWN, CD.UNMEASURED)
REAL_CHECKS = list(CD.CHECKS)


@contextlib.contextmanager
def _quiet_tick():
    """Production tick_caches POSTs /api/board_ownership into HIS window. Not here."""
    yield


def _installed():
    return "installed", "an installed console, level with origin (fixture)"


class _Scratch(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="eye_rows_law_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.ledger = os.path.join(self.d, ".second_eye.jsonl")
        with open(self.ledger, "w") as fh:
            fh.write("")
        self.no_ledger = os.path.join(self.d, "no", ".second_eye.jsonl")
        self.eye = sys.executable                                   # a real, present binary
        self.no_eye = os.path.join(self.d, "no", "grok.exe")


class TheOnePredicate(_Scratch):

    def _never(self):
        raise AssertionError("the tree was asked although an earlier input already answered")

    def test_each_input_alone_makes_a_pc_that_ships(self):
        self.assertIs(CD.this_pc_ships(self.ledger, self.no_eye, self._never)[0], True, "a ledger did not count")
        self.assertIs(CD.this_pc_ships(self.no_ledger, self.eye, self._never)[0], True, "an eye did not count")
        self.assertIs(CD.this_pc_ships(self.no_ledger, "https://api.x.ai/v1", self._never)[0], True,
                      "an eye configured as an API did not count as an eye")
        s, why = CD.this_pc_ships(self.no_ledger, self.no_eye, lambda: ("dev", "2 local commit(s)"))
        self.assertIs(s, True, "a development tree did not count: %s" % why)

    def test_all_three_read_and_false_is_a_pc_that_does_not_ship(self):
        s, why = CD.this_pc_ships(self.no_ledger, self.no_eye, _installed)
        print("   not shipping: %s" % why)
        self.assertIs(s, False, why)
        for part in ("no second-eye ledger", "no eye binary", "installed console"):
            self.assertIn(part, why, "the predicate does not say what it measured")
        self.assertIs(CD.this_pc_ships(self.no_ledger, "", _installed)[0], False, "no eye configured is no eye")

    def test_an_input_that_cannot_be_read_is_none_never_a_guess(self):
        self.assertIsNone(CD.this_pc_ships("bad\0path", self.no_eye, _installed)[0], "an unreadable ledger was read")
        self.assertIsNone(CD.this_pc_ships(self.no_ledger, "bad\0path", _installed)[0], "an unreadable eye was read")
        self.assertIsNone(CD.this_pc_ships(self.no_ledger, self.no_eye, lambda: ("unknown", "git refused"))[0],
                          "a tree nobody could read was taken for an installed one")

        def _boom():
            raise OSError("git is missing")
        self.assertIsNone(CD.this_pc_ships(self.no_ledger, self.no_eye, _boom)[0])


class EveryEyeRowAsksThePredicate(_Scratch):

    def setUp(self):
        super(EveryEyeRowAsksThePredicate, self).setUp()
        saved = (CD.CHECKS, CD.SLOW, CD.PERIODIC, CD.tick_caches)
        self.addCleanup(lambda: setattr(CD, "CHECKS", saved[0]) or setattr(CD, "SLOW", saved[1])
                        or setattr(CD, "PERIODIC", saved[2]) or setattr(CD, "tick_caches", saved[3]))
        CD.tick_caches = _quiet_tick
        CD.SLOW, CD.PERIODIC = (), ()

    def test_every_eye_row_is_a_real_row(self):
        names = [n for n, _fn in REAL_CHECKS]
        missing = [n for n in CD.SHIP_EYE_ROWS if n not in names]
        self.assertEqual(missing, [], "SHIP_EYE_ROWS names rows the eagle does not have: %r" % missing)
        self.assertEqual(len(CD.SHIP_EYE_ROWS), 13)

    def test_a_pc_that_does_not_ship_hears_ok_on_every_eye_row_and_nothing_else_moves(self):
        asked, ships = [], []

        def _row(n):
            def fn():
                asked.append(n)
                return CD.MISSING, "the row's own question"
            return fn
        CD.CHECKS = [(n, _row(n)) for n in CD.SHIP_EYE_ROWS] + [("not an eye row", _row("not an eye row"))]
        with mock.patch.object(CD, "this_pc_ships", lambda: ships.append(1) or (False, "fixture: nothing ships")):
            rows = CD.run(include_slow=False, include_periodic=True, tick=6)
        by = dict((r["check"], r) for r in rows)
        for n in CD.SHIP_EYE_ROWS:
            self.assertEqual(by[n]["state"], CD.OK, "%s was not asked through the predicate: %r" % (n, by[n]))
            self.assertIn(CD.NOT_SHIPPING_SAY, by[n]["why"])
        print("   e.g. %s" % by[CD.SHIP_EYE_ROWS[0]]["why"])
        self.assertEqual(asked, ["not an eye row"], "an eye row was asked its own question on a PC that does not "
                         "ship, or a non-eye row was relabelled: %r" % asked)
        self.assertEqual(by["not an eye row"]["state"], CD.MISSING, "a row that is not an eye row was relabelled")
        self.assertEqual(len(ships), 1, "the predicate was asked %d times in one pass" % len(ships))
        for r in rows:
            self.assertIn(r["state"], STATES, "a fifth state word reached the eagle: %r" % r)

    def test_a_pc_that_ships_keeps_todays_missing_about_an_absent_binary(self):
        name = "this machine can get a second opinion"
        CD.CHECKS = [(name, dict(REAL_CHECKS)[name])]
        with mock.patch.object(SEL, "LEDGER_PATH", self.ledger), mock.patch.object(SER, "EYE_CLI", self.no_eye), \
                mock.patch.object(SP, "tree_state", lambda git=None: _installed()):
            rows = CD.run(include_slow=False, include_periodic=True, tick=6)
        r = dict((x["check"], x) for x in rows)[name]
        print("   shipping PC, absent binary: %s - %s" % (r["state"], r["why"][:110]))
        self.assertEqual(r["state"], CD.MISSING, "a shipping PC's real MISSING vanished: %r" % r)
        self.assertIn("there is no binary there", r["why"], "today's words about an absent binary changed")

    def test_an_unreadable_input_runs_todays_logic(self):
        name = "this machine can get a second opinion"
        CD.CHECKS = [(name, dict(REAL_CHECKS)[name])]
        with mock.patch.object(SEL, "LEDGER_PATH", self.no_ledger), mock.patch.object(SER, "EYE_CLI", self.no_eye), \
                mock.patch.object(SP, "tree_state", lambda git=None: ("unknown", "git status failed (fixture)")):
            rows = CD.run(include_slow=False, include_periodic=True, tick=6)
        r = dict((x["check"], x) for x in rows)[name]
        self.assertEqual(r["state"], CD.MISSING, "an input nobody could read relabelled the row: %r" % r)
        self.assertNotIn(CD.NOT_SHIPPING_SAY, r["why"])

    def test_the_door_answers_ok_only_on_a_measured_false(self):
        def today():
            return CD.UNKNOWN, "today's question"
        self.assertEqual(CD.ask_an_eye_row(today, (False, "fixture"))[0], CD.OK)
        self.assertEqual(CD.ask_an_eye_row(today, (True, "fixture")), (CD.UNKNOWN, "today's question"))
        self.assertEqual(CD.ask_an_eye_row(today, (None, "fixture")), (CD.UNKNOWN, "today's question"))


RED_PROOF = [
    {
        "why": "REG-2480 - the predicate is forced to 'does not ship': a shipping PC's real MISSING (no eye binary) "
               "vanishes behind an OK",
        "file": "console_doctor.py",
        "find": "    if s is False:\n        return OK, \"%s (measured: %s)\" % (NOT_SHIPPING_SAY, swhy)\n",
        "replace": "    if True:\n        return OK, \"%s (measured: %s)\" % (NOT_SHIPPING_SAY, swhy)\n",
        "matches": 1,
    },
    {
        "why": "REG-2480 - the predicate ignores the ledger: the shipping Mac, whose ledger is its proof, would read "
               "as a PC that never shipped",
        "file": "console_doctor.py",
        "find": "        os.stat(ledger_path)\n",
        "replace": "        raise FileNotFoundError(ledger_path)\n",
        "matches": 1,
    },
    {
        "why": "REG-2480 - a tree nobody could read is taken for an installed one: a guess relabels thirteen rows",
        "file": "console_doctor.py",
        "find": "    if kind != \"installed\":\n        return None, \"whether this tree ships could not be read (%s)\" % twhy\n",
        "replace": "    if False:\n        return None, \"whether this tree ships could not be read (%s)\" % twhy\n",
        "matches": 1,
    },
    {
        "why": "REG-2480 - run() stops routing the eye rows through the predicate: Dean's healthy PC reads two "
               "MISSING and eleven UNKNOWN again",
        "file": "console_doctor.py",
        "find": "                if name in SHIP_EYE_ROWS:\n",
        "replace": "                if False:\n",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
