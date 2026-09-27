# -*- coding: utf-8 -*-
"""A seal with no rows is not an extraction. The lane gives that reel one solo pass.

Measured: 19 reels held, 8 fixtures + 8 newest + 3 panels-never-banked. Each of the
three is sealed by the current reader with rows 0, examinedEmpty unset, and
extractedWhy "nothing was taken", while the pass they rode in banked a row for a
different session. The tick treated the seal as finished and moved on, so the solo
pass that can finish the answer never started, and the drain could free nothing.

One pass per reader. The same prompt must not buy the reel again: that loop re-swept
one reel thousands of times.
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as CA  # noqa: E402


def _barren(prompt="vp3368"):
    return {"ok": False, "alreadySealed": True, "rows": 0, "examinedEmpty": None,
            "sealedBy": prompt, "why": "sealed, nothing taken"}


class TestAnUnextractedSealGetsOnePass(unittest.TestCase):

    def test_a_barren_current_seal_needs_one_pass(self):
        self.assertTrue(CA._unextracted_seal_needs_one_pass(_barren(), None))

    def test_the_same_reader_does_not_get_a_second_pass(self):
        self.assertFalse(CA._unextracted_seal_needs_one_pass(_barren(), "vp3368"))

    def test_a_declared_empty_seal_is_already_an_answer(self):
        row = _barren()
        row["examinedEmpty"] = True
        self.assertFalse(CA._unextracted_seal_needs_one_pass(row, None))

    def test_rows_already_taken_are_not_swept_again(self):
        row = _barren()
        row["rows"] = 4
        self.assertFalse(CA._unextracted_seal_needs_one_pass(row, None))

    def test_an_unnamed_reader_does_not_spend(self):
        row = _barren("?")
        self.assertFalse(CA._unextracted_seal_needs_one_pass(row, None))


class TestTheTickRunsThatPassOnce(unittest.TestCase):
    """Drives the tick against a fixture world. vault_sweep_start is replaced, so this
    cannot open his film or start a sweep thread."""

    def setUp(self):
        self._hist = os.environ.get("TV_HIST")
        self.tmp = tempfile.mkdtemp(prefix="vault-one-pass-")
        os.environ["TV_HIST"] = self.tmp
        self._snap = dict(CA._VAULT_AUTOREAD)
        self._store = dict(CA._VAULT_AUTOREAD_STORE)
        CA._VAULT_AUTOREAD.clear()
        CA._VAULT_AUTOREAD.update({"tries": {}, "skipped": {}, "reads": 0, "lastTs": 0,
                                   "retired": {}, "lastWhy": {}, "reextract": {}})
        CA._VAULT_AUTOREAD_STORE.update({"tried": False, "readable": None})
        self.reel = os.path.join(self.tmp, "reel_s_1_12001")
        self.calls = []

    def tearDown(self):
        CA._VAULT_AUTOREAD.clear()
        CA._VAULT_AUTOREAD.update(self._snap)
        CA._VAULT_AUTOREAD_STORE.clear()
        CA._VAULT_AUTOREAD_STORE.update(self._store)
        if self._hist is None:
            os.environ.pop("TV_HIST", None)
        else:
            os.environ["TV_HIST"] = self._hist
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, answers):
        pending = list(answers)

        def start(*a, **k):
            self.calls.append(dict(k))
            return pending.pop(0)

        owed = [self.reel]
        import unittest.mock as mock
        with mock.patch.object(CA, "_vault_owed_reels", lambda hist=None: owed), \
                mock.patch.object(CA, "_reel_is_growing", lambda d: False), \
                mock.patch.object(CA, "vault_sweep_start", start):
            return CA.vault_autoreel_tick()

    def test_the_first_tick_forces_one_solo_pass_and_the_next_does_not(self):
        first = self._run([_barren(), {"ok": True, "started": True}])
        self.assertTrue(first.get("reextract"), first)
        self.assertEqual(self.calls[-1].get("force"), True)
        self.assertEqual(CA._VAULT_AUTOREAD["reextract"].get("reel_s_1_12001"), "vp3368")
        self.calls = []
        second = self._run([_barren()])
        self.assertFalse(second.get("reextract"))
        self.assertFalse(any(c.get("force") for c in self.calls),
                         "the same reader bought the reel again: %r" % self.calls)

    def test_a_seal_that_already_has_rows_is_not_forced(self):
        row = _barren()
        row["rows"] = 4
        got = self._run([row])
        self.assertFalse(any(c.get("force") for c in self.calls), got)
        self.assertEqual(CA._VAULT_AUTOREAD.get("reextract"), {})

    def test_the_one_pass_survives_a_restart(self):
        self._run([_barren(), {"ok": True, "started": True}])
        saved = dict(CA._VAULT_AUTOREAD.get("reextract") or {})
        CA._VAULT_AUTOREAD.update({"reextract": {}})
        CA._VAULT_AUTOREAD_STORE.update({"tried": False, "readable": None})
        self.assertIs(CA._vault_autoread_load(), True)
        self.assertEqual(CA._VAULT_AUTOREAD.get("reextract"), saved,
                         "a restart forgot the solo pass and will buy the reel again")


RED_PROOF = [
    {
        "why": "a barren seal is treated as finished, so the solo extraction pass never starts",
        "file": "control_app.py",
        "find": "    return str(already or \"\") != prompt\n",
        "replace": "    return False\n",
        "matches": 1,
    },
    {
        "why": "the tick ignores the one-pass decision and leaves the reel sealed",
        "file": "control_app.py",
        "find": "                if _unextracted_seal_needs_one_pass(r, _prior):\n",
        "replace": "                if False:\n",
        "matches": 1,
    },
    {
        "why": "a restart forgets the solo pass and buys the same reel again",
        "file": "control_app.py",
        "find": "        for k in (\"retired\", \"tries\", \"lastWhy\", \"reextract\"):\n",
        "replace": "        for k in (\"retired\", \"tries\", \"lastWhy\"):\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
