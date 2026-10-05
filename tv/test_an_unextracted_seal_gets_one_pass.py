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
import time
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
                                   "retired": {}, "lastWhy": {}, "reextract": {},
                                   "joinQueued": {}, "joinTried": {}})
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

    def _rows(self):
        # Injected. vault_join_once must not call extract_gap.gap() from a law.
        return [
            {"state": "RECOVERABLE", "reel": "reel_s_join_1"},
            {"state": "NOT_A_HOLDING", "reel": "reel_s_checklist"},
            {"state": "UNKNOWN", "reel": "reel_s_unknown"},
            {"reel": "reel_s_missing"},
            {"state": "RECOVERABLE", "reel": "not-a-reel"},
        ]

    def test_a_dry_queue_names_the_join_and_writes_nothing(self):
        store = os.path.join(self.tmp, ".vault_autoread.json")
        got = CA.vault_join_once(dry=True, rows=self._rows())
        self.assertEqual(got["queued"], ["reel_s_join_1"], got)
        self.assertTrue(got["dry"])
        self.assertFalse(got["retry"])
        self.assertEqual(CA._VAULT_AUTOREAD.get("joinQueued"), {})
        self.assertEqual(CA._VAULT_AUTOREAD.get("joinTried"), {})
        self.assertFalse(os.path.exists(store), "a dry run wrote the lane store")

    def test_one_queue_is_remembered_and_a_second_call_adds_nothing(self):
        first = CA.vault_join_once(dry=False, rows=self._rows())
        self.assertEqual(first["queued"], ["reel_s_join_1"], first)
        self.assertIn("reel_s_join_1", CA._VAULT_AUTOREAD["joinQueued"])
        self.assertIn("reel_s_join_1", CA._VAULT_AUTOREAD["joinTried"])
        self.assertNotIn("reel_s_checklist", CA._VAULT_AUTOREAD["joinQueued"])
        saved_q = dict(CA._VAULT_AUTOREAD["joinQueued"])
        saved_t = dict(CA._VAULT_AUTOREAD["joinTried"])
        CA._VAULT_AUTOREAD.clear()
        CA._VAULT_AUTOREAD.update({"tries": {}, "skipped": {}, "reads": 0, "lastTs": 0,
                                   "retired": {}, "lastWhy": {}, "reextract": {}})
        CA._VAULT_AUTOREAD_STORE.update({"tried": False, "readable": None})
        self.assertIs(CA._vault_autoread_load(), True)
        self.assertEqual(CA._VAULT_AUTOREAD.get("joinQueued"), saved_q)
        self.assertEqual(CA._VAULT_AUTOREAD.get("joinTried"), saved_t)
        second = CA.vault_join_once(dry=False, rows=self._rows())
        self.assertEqual(second["queued"], [], second)

    def test_an_unreadable_store_queues_nothing_and_stays_retryable(self):
        import unittest.mock as mock
        with mock.patch.object(CA, "_vault_autoread_load", lambda: None):
            got = CA.vault_join_once(dry=False, rows=self._rows())
        self.assertFalse(got["ok"])
        self.assertTrue(got["retry"], got)
        self.assertEqual(got["queued"], [])
        self.assertIn("UNKNOWN", got["why"])
        self.assertEqual(CA._VAULT_AUTOREAD.get("joinQueued"), {})

    def test_extract_gap_failing_queues_nothing_and_is_not_retried(self):
        import types
        import unittest.mock as mock
        fake = types.ModuleType("extract_gap")

        def gap():
            raise RuntimeError("shelf")

        fake.gap = gap
        with mock.patch.dict(sys.modules, {"extract_gap": fake}):
            got = CA.vault_join_once(dry=False, rows=None)
        self.assertFalse(got["ok"], got)
        self.assertFalse(got["retry"], got)
        self.assertEqual(got["queued"], [])
        self.assertEqual(CA._VAULT_AUTOREAD.get("joinQueued"), {})
        fake.gap = lambda: {"ok": False, "why": "no"}
        with mock.patch.dict(sys.modules, {"extract_gap": fake}):
            got2 = CA.vault_join_once(dry=False, rows=None)
        self.assertFalse(got2["ok"], got2)
        self.assertFalse(got2["retry"], got2)
        self.assertIn("UNKNOWN", got2["why"])

    def test_a_recoverable_join_is_read_once_even_when_the_seal_says_empty(self):
        rid = "reel_s_1_12001"
        CA._VAULT_AUTOREAD["joinQueued"] = {rid: 1}
        CA._VAULT_AUTOREAD["joinTried"] = {rid: 1}
        empty = _barren()
        empty["examinedEmpty"] = True
        first = self._run([empty, {"ok": True, "started": True}])
        self.assertTrue(first.get("join"), first)
        self.assertEqual(self.calls[-1].get("force"), True)
        self.assertNotIn(rid, CA._VAULT_AUTOREAD.get("joinQueued") or {})
        self.assertEqual(CA._VAULT_AUTOREAD["reextract"].get(rid), "vp3368")
        self.assertEqual(CA._VAULT_AUTOREAD.get("tries"), {},
                         "the one re-read was charged as a failed attempt")
        self.calls = []
        second = self._run([empty])
        self.assertFalse(second.get("join"))
        self.assertFalse(any(c.get("force") for c in self.calls), self.calls)

    def test_the_same_reader_spends_the_queue_and_buys_nothing(self):
        rid = "reel_s_1_12001"
        CA._VAULT_AUTOREAD["joinQueued"] = {rid: 1}
        CA._VAULT_AUTOREAD["reextract"] = {rid: "vp3368"}
        empty = _barren()
        empty["examinedEmpty"] = True
        got = self._run([empty])
        self.assertFalse(got.get("join"), got)
        self.assertEqual(len(self.calls), 1, self.calls)
        self.assertFalse(self.calls[0].get("force"))
        self.assertNotIn(rid, CA._VAULT_AUTOREAD.get("joinQueued") or {})

    def test_a_busy_sweep_puts_the_join_back(self):
        rid = "reel_s_1_12001"
        CA._VAULT_AUTOREAD["joinQueued"] = {rid: 1}
        empty = _barren()
        empty["examinedEmpty"] = True
        got = self._run([empty, {"ok": False, "state": "running",
                                 "why": "a vault sweep is already running"}])
        self.assertEqual(got.get("deferred"), rid, got)
        self.assertIn(rid, CA._VAULT_AUTOREAD.get("joinQueued") or {})
        self.assertTrue(self.calls[-1].get("force"))

    def test_a_failed_re_read_is_spent(self):
        rid = "reel_s_1_12001"
        CA._VAULT_AUTOREAD["joinQueued"] = {rid: 1}
        CA._VAULT_AUTOREAD["joinTried"] = {rid: 1}
        empty = _barren()
        empty["examinedEmpty"] = True
        got = self._run([empty, {"ok": False, "why": "vault_retro exploded"}])
        self.assertFalse(got.get("ok"), got)
        self.assertNotIn(rid, CA._VAULT_AUTOREAD.get("joinQueued") or {})
        self.assertIn("exploded", CA._VAULT_AUTOREAD["lastWhy"].get(rid, ""))
        self.assertIn(rid, CA._VAULT_AUTOREAD["joinTried"])

    def test_a_queued_join_the_seal_skipped_stays_owed(self):
        import reel_retention as rr
        import unittest.mock as mock
        rid = "reel_s_joinlaw_9001"
        os.makedirs(os.path.join(self.tmp, rid))
        CA._VAULT_AUTOREAD["joinQueued"] = {rid: 1}
        kept = [{"reel": rid, "tag": "recent"}]
        with mock.patch.object(rr, "plan", lambda h, **k: {"ok": True, "kept": list(kept)}), \
                mock.patch.object(CA, "_vault_positions_and_seals",
                                  lambda: ({rid: "PRINTER"}, {rid: {"by": "vault"}})):
            got = CA._vault_owed_reels(hist=self.tmp)
        names = [os.path.basename(g) for g in (got or [])]
        self.assertEqual(names, [rid], names)

    def test_a_queued_join_already_on_the_list_is_not_added_twice(self):
        import reel_retention as rr
        import unittest.mock as mock
        rid = "reel_s_joinlaw_9002"
        CA._VAULT_AUTOREAD["joinQueued"] = {rid: 1}
        kept = [{"reel": rid, "tag": "vault-owes"}]
        with mock.patch.object(rr, "plan", lambda h, **k: {"ok": True, "kept": list(kept)}), \
                mock.patch.object(CA, "_vault_positions_and_seals", lambda: ({}, {})):
            got = CA._vault_owed_reels(hist=self.tmp)
        names = [os.path.basename(g) for g in (got or [])]
        self.assertEqual(names, [rid], names)

    def test_a_missing_reel_and_a_proven_empty_join_are_not_owed(self):
        import reel_retention as rr
        import shelf_driver as sd
        import unittest.mock as mock
        missing = "reel_s_joinlaw_gone"
        empty = "reel_s_joinlaw_empty"
        os.makedirs(os.path.join(self.tmp, empty))
        CA._VAULT_AUTOREAD["joinQueued"] = {missing: 1, empty: 2}
        with mock.patch.object(rr, "plan", lambda h, **k: {"ok": True, "kept": []}), \
                mock.patch.object(CA, "_vault_positions_and_seals", lambda: ({}, {})), \
                mock.patch.object(sd, "_proven_empty", lambda reel: os.path.basename(str(reel)) == empty):
            got = CA._vault_owed_reels(hist=self.tmp)
        self.assertEqual(got, [], got)


class TestAChecklistIsNotAHolding(unittest.TestCase):

    def test_only_the_word_recoverable_is_queued_and_only_three(self):
        rows = [{"state": "RECOVERABLE", "reel": "reel_s_%d" % i} for i in range(5)]
        rows.append({"state": "NOT_A_HOLDING", "reel": "reel_s_checklist"})
        rows.append({"state": "UNKNOWN", "reel": "reel_s_unknown"})
        rows.append({"state": "RECOVERABLE", "reel": "checklist.txt"})
        got = CA._join_once_pick(rows, {"reel_s_1": 1}, {"reel_s_2": 9}, CA._VAULT_REJUDGE_PER_BOOT)
        self.assertEqual(got, ["reel_s_0", "reel_s_3", "reel_s_4"], got)
        self.assertNotIn("reel_s_checklist", got)

    def test_a_checklist_alone_queues_nothing(self):
        rows = [
            {"state": "NOT_A_HOLDING", "reel": "reel_s_checklist"},
            {"state": "UNKNOWN", "reel": "reel_s_unknown"},
            {"state": "RECOVERABLE", "reel": "notes.txt"},
            "not-a-row",
        ]
        self.assertEqual(CA._join_once_pick(rows, {}, {}, CA._VAULT_REJUDGE_PER_BOOT), [])

    def test_a_bool_cap_queues_nothing(self):
        rows = [{"state": "RECOVERABLE", "reel": "reel_s_1"}]
        self.assertEqual(CA._join_once_pick(rows, {}, {}, True), [])

    def test_the_recoverable_door_is_one_line(self):
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        needle = '        if not isinstance(row, dict) or row.get("state") != "RECOVERABLE":\n'
        self.assertEqual(src.count(needle), 1)


class TestTheConsoleAsksOnce(unittest.TestCase):
    """The measurement runs on the lamp thread, and only when this process is the console.
    Both spenders are replaced, so this cannot walk his shelf or write his lane store."""

    def setUp(self):
        import frame_ref as fr
        self._hist = os.environ.get("TV_HIST")
        self.tmp = tempfile.mkdtemp(prefix="vault-join-kick-")
        os.environ["TV_HIST"] = self.tmp
        self._fr = fr
        self._console = fr.on_console_path()
        self._re = CA._VAULT_REENTRY_DONE
        self._join = CA._VAULT_JOIN_ONCE_DONE
        self._refresh = dict(CA._VAULT_AUTOREAD_REFRESH)
        fr.mark_console_path(False)
        CA._VAULT_REENTRY_DONE = False
        CA._VAULT_JOIN_ONCE_DONE = False
        CA._VAULT_AUTOREAD_REFRESH["running"] = False

    def tearDown(self):
        self._fr.mark_console_path(self._console)
        CA._VAULT_REENTRY_DONE = self._re
        CA._VAULT_JOIN_ONCE_DONE = self._join
        CA._VAULT_AUTOREAD_REFRESH.clear()
        CA._VAULT_AUTOREAD_REFRESH.update(self._refresh)
        if self._hist is None:
            os.environ.pop("TV_HIST", None)
        else:
            os.environ["TV_HIST"] = self._hist
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _wait_idle(self):
        deadline = time.time() + 3
        while CA._VAULT_AUTOREAD_REFRESH["running"] and time.time() < deadline:
            time.sleep(0.01)
        self.assertFalse(CA._VAULT_AUTOREAD_REFRESH["running"], "the lamp thread did not finish")

    def test_a_law_does_not_ask_and_the_console_asks_once(self):
        import unittest.mock as mock
        calls = {"join": 0, "sweep": 0}

        def join(dry=True, rows=None):
            calls["join"] += 1
            self.assertIs(dry, False)
            self.assertIsNone(rows)
            return {"ok": True, "queued": [], "retry": False, "why": "stub"}

        def sweep(dry=True):
            calls["sweep"] += 1
            return {"ok": True, "readmitted": [], "rejudged": [], "lattice": []}

        with mock.patch.object(CA, "vault_join_once", join), \
                mock.patch.object(CA, "vault_reentry_sweep", sweep), \
                mock.patch.object(CA, "_vault_autoread_state", lambda: {"on": True, "why": "stub"}):
            self.assertTrue(CA._vault_autoread_kick())
            self._wait_idle()
            self.assertEqual(calls, {"join": 0, "sweep": 0})
            self.assertFalse(CA._VAULT_JOIN_ONCE_DONE)
            self._fr.mark_console_path(True)
            self.assertTrue(CA._vault_autoread_kick())
            self._wait_idle()
            self.assertEqual(calls, {"join": 1, "sweep": 1})
            self.assertTrue(CA._VAULT_JOIN_ONCE_DONE)
            self.assertTrue(CA._vault_autoread_kick())
            self._wait_idle()
            self.assertEqual(calls["join"], 1, "the measurement ran again in the same process")

    def test_an_unreadable_store_is_asked_again_on_the_next_kick(self):
        import unittest.mock as mock
        calls = {"join": 0}

        def join(dry=True, rows=None):
            calls["join"] += 1
            return {"ok": False, "retry": True, "queued": [], "why": "unreadable"}

        self._fr.mark_console_path(True)
        with mock.patch.object(CA, "vault_join_once", join), \
                mock.patch.object(CA, "vault_reentry_sweep",
                                  lambda dry=True: {"ok": True, "readmitted": [], "rejudged": [],
                                                    "lattice": []}), \
                mock.patch.object(CA, "_vault_autoread_state", lambda: {"on": True, "why": "stub"}):
            self.assertTrue(CA._vault_autoread_kick())
            self._wait_idle()
            self.assertEqual(calls["join"], 1)
            self.assertFalse(CA._VAULT_JOIN_ONCE_DONE)
            self.assertTrue(CA._vault_autoread_kick())
            self._wait_idle()
            self.assertEqual(calls["join"], 2)


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
        "find": "        for k in (\"retired\", \"tries\", \"lastWhy\", \"reextract\", \"rejudged\"):\n",   # REG-1663 re-anchor
        "replace": "        for k in (\"retired\", \"tries\", \"lastWhy\", \"rejudged\"):\n",
        "matches": 1,
    },
    {
        "why": "a checklist page is queued as a holding, so a chronicle is bought a vault read",
        "file": "control_app.py",
        "find": "        if not isinstance(row, dict) or row.get(\"state\") != \"RECOVERABLE\":\n",
        "replace": "        if False and (not isinstance(row, dict) or row.get(\"state\") != \"RECOVERABLE\"):\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
