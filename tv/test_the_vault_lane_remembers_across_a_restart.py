"""WHAT THE VAULT LANE LEARNS MUST SURVIVE THE PROCESS — ESPECIALLY WHAT IT STOPPED PAYING FOR.

⚠⚠ MEASURED 2026-09-10 (#60, REG-900). `control_app._VAULT_AUTOREAD` had **14 write sites and ZERO
persistence sites** — no save, no load, no json anywhere. It held everything the lane had learned:

    reads    how many sweeps completed        tries    how many attempts each reel has cost
    lastTs   when the last one finished       retired  reels the lane STOPPED PAYING FOR

⚠ `retired` is the expensive one. A retirement is the lane's decision not to buy a reel again.
Losing it does not merely forget — it makes the lane pay a second time. That is the "and re-spends
for it" in #60's title, and it was a property of the code, not a suspicion.

⚠⚠ AND IT HAD BEEN LYING TO THE CORROBORATOR. `corroborate.py`'s `vault-lane-has-worked` reads
`lastTs or reads > 0` under the comment *"lastTs is the durable tell — `reads` is a process-local
counter and resets on every restart."* BOTH were process-local; there was no durable tell. That
false distinction is why a RESTART read as "this lane has never swept" — a very different
accusation from the truth, which was "this process is new". Measured on his tree the same day:
`on=True reads=0 lastTs=None owed=8`, while his console had been REPLACED TWICE in one hour (#67).
[[label-outlived-referent]] [[unknown-stays-unknown]]

⚠ NO FOOTAGE AND NO LIVE STORE. Every test here points TV_HIST at a temp directory, so it measures
the same thing on his Mac and on a CI runner — and it cannot touch the store his console is using.
[[feedback-fixtures-never-touch-live-data]]
"""
import io
import json
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

import control_app as CA   # noqa: E402


class TheVaultLaneRemembersAcrossARestart(unittest.TestCase):

    def setUp(self):
        self._hist = os.environ.get("TV_HIST")
        self.tmp = tempfile.mkdtemp(prefix="vault-remember-")
        os.environ["TV_HIST"] = self.tmp
        self._snap = dict(CA._VAULT_AUTOREAD)
        self._store = dict(CA._VAULT_AUTOREAD_STORE)

    def tearDown(self):
        # ⚠ put BOTH globals back, or this suite's fixture leaks into the next law — REG-865.
        CA._VAULT_AUTOREAD.clear(); CA._VAULT_AUTOREAD.update(self._snap)
        CA._VAULT_AUTOREAD_STORE.clear(); CA._VAULT_AUTOREAD_STORE.update(self._store)
        if self._hist is None:
            os.environ.pop("TV_HIST", None)
        else:
            os.environ["TV_HIST"] = self._hist
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _restart(self):
        """Everything a new process would start with, and nothing more."""
        CA._VAULT_AUTOREAD.update({"reads": 0, "lastTs": 0, "retired": {}, "tries": {},
                                   "lastWhy": {}, "skipped": {}})
        CA._VAULT_AUTOREAD_STORE.update({"tried": False, "readable": None})

    # ── the store must not be able to reach his live console ─────────────────────────────────
    def test_the_store_lives_under_the_fixture_root(self):
        p = CA._vault_autoread_path()
        self.assertIn(self.tmp, p,
                      "the vault store resolved to %r while TV_HIST pointed at a fixture — a suite "
                      "or a render gate would write into his live tv/ and overwrite what his lane "
                      "had retired" % p)

    # ── the whole point ──────────────────────────────────────────────────────────────────────
    def test_a_retirement_survives_a_restart(self):
        CA._VAULT_AUTOREAD["retired"] = {"reel_x": {"why": "3 attempts, still owed", "at": 1}}
        CA._VAULT_AUTOREAD["reads"], CA._VAULT_AUTOREAD["lastTs"] = 3, 1788999999000
        self.assertTrue(CA._vault_autoread_save(), "the store could not be written at all")
        self._restart()
        self.assertEqual(sorted(CA._VAULT_AUTOREAD["retired"]), [],
                         "the fixture did not actually clear memory, so this proves nothing")
        self.assertIs(CA._vault_autoread_load(), True, "the store did not read back")
        self.assertEqual(sorted(CA._VAULT_AUTOREAD["retired"]), ["reel_x"],
                         "a RETIREMENT was lost across a restart — the lane will pay for that reel "
                         "again, which is exactly what #60 is about")
        self.assertEqual(CA._VAULT_AUTOREAD["reads"], 3, "the completed-read count was lost")
        self.assertEqual(CA._VAULT_AUTOREAD["lastTs"], 1788999999000,
                         "lastTs was lost — 'has this lane ever swept' goes back to reading 0")

    def test_has_ever_swept_is_true_again_after_a_restart(self):
        """The corroborator's own predicate, run over a restart."""
        CA._VAULT_AUTOREAD["lastTs"] = 1788999999000
        CA._vault_autoread_save()
        self._restart()
        st = CA._vault_autoread_state() or {}
        left = 1 if (st.get("lastTs") or (st.get("reads") or 0) > 0) else 0
        self.assertEqual(left, 1,
                         "after a restart the lane still reports it has NEVER swept, so "
                         "`vault-lane-has-worked` fires on a new process instead of a broken lane")

    # ── the third outcome, and it is the one that costs money ────────────────────────────────
    def test_an_unreadable_store_is_UNKNOWN_and_not_a_fresh_start(self):
        with io.open(CA._vault_autoread_path(), "w", encoding="utf-8") as fh:
            fh.write("{ this is not json")
        self._restart()
        self.assertIsNone(CA._vault_autoread_load(),
                          "an UNREADABLE store read as a fresh start. An empty `retired` is then a "
                          "CLAIM that nothing was retired, and acting on it re-buys every reel the "
                          "lane had already ruled out")
        st = CA._vault_autoread_state() or {}
        self.assertIsNone(st.get("storeReadable"),
                          "the state does not carry the store's UNKNOWN, so nothing downstream can "
                          "tell an unmeasured retired list from an empty one")
        self.assertIn("UNKNOWN", str(st.get("storeWhy") or ""),
                      "UNKNOWN with no reason attached is not an answer")

    def test_no_store_yet_is_FALSE_not_unknown(self):
        """A first run is a real fact and must not be dressed as UNKNOWN either."""
        self._restart()
        self.assertIs(CA._vault_autoread_load(), False,
                      "a missing store must read as 'no store yet', which is a genuine fresh start")

    # ── the write must not be able to leave a torn file ──────────────────────────────────────
    def test_the_writer_is_atomic(self):
        """⚠ PARSED, NOT GREPPED. This repo has already emptied a 6 MB file with a plain
        open(w). [[source-reading-guard]] [[open-for-write-truncates-first]]"""
        import ast
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "_vault_autoread_save"), None)
        self.assertIsNotNone(fn, "_vault_autoread_save is gone — nothing persists the lane")
        calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == "replace"]
        self.assertTrue(calls,
                        "_vault_autoread_save does not os.replace — it writes the destination "
                        "directly, so a reader can see a half-written store and a crash mid-write "
                        "loses every retirement")


    # ── THE ACTOR, NOT JUST THE REPORTER ─────────────────────────────────────────────────────
    def test_a_tick_after_a_restart_still_knows_what_was_retired(self):
        """⚠⚠ THE MONEY BUG, AND v2901 SHIPPED IT INSIDE THE FIX FOR IT. Raised by the
        cross-family eye: v2901 loaded the store from `_vault_autoread_state()` — the REPORTER —
        and `vault_autoreel_tick()`, the function that SPENDS, read `retired` straight out of
        process memory. Two of its callers never go through state(): the 45s loop's first pass
        after a restart, and the stop-agent nudge that fires as soon as a reel stops. So a tick
        could run with `retired == {}` and pay for every reel the previous process had ruled out.

        Chronicle's sibling had this right already — `chronicle_autoreel_tick` lazy-loads via
        `_chron_reels_retired()`. The persistence was copied; the lesson was not. [[copy-drift]]"""
        CA._VAULT_AUTOREAD["retired"] = {"reel_paid_for_once": {"why": "2 attempts", "at": 1}}
        self.assertTrue(CA._vault_autoread_save())
        self._restart()
        self.assertEqual(sorted(CA._VAULT_AUTOREAD["retired"]), [],
                         "the fixture did not clear memory, so this proves nothing")
        CA.vault_autoreel_tick()          # ⚠ the ACTOR, called directly — no state() first
        self.assertIn("reel_paid_for_once", CA._VAULT_AUTOREAD["retired"],
                      "a tick ran after a restart without restoring the retirements, so the lane "
                      "will pay again for a reel it had already ruled out")

    def test_a_save_before_any_load_cannot_erase_the_store(self):
        """An empty in-memory `retired` written over a good store is strictly worse than not
        persisting at all — the file would then look authoritative while holding nothing."""
        CA._VAULT_AUTOREAD["retired"] = {"reel_paid_for_once": {"why": "2 attempts", "at": 1}}
        self.assertTrue(CA._vault_autoread_save())
        self._restart()
        CA._VAULT_AUTOREAD["reads"] = 1   # something trivial changes, and a save fires
        CA._vault_autoread_save()
        with io.open(CA._vault_autoread_path(), encoding="utf-8") as fh:
            on_disk = json.load(fh)
        self.assertIn("reel_paid_for_once", on_disk.get("retired") or {},
                      "a save that ran before any load wrote empty memory over the store and "
                      "destroyed every retirement on disk")


RED_PROOF = [
    {
        "why": "dropping the restore: every restart goes back to reporting a lane that has never "
               "swept, and every retirement is bought again",
        "file": "control_app.py",
        "find": "        _st_readable = _vault_autoread_load()",
        "replace": "        _st_readable = False",
        "matches": 1,
    },
    {
        "why": "an unreadable store reported as a fresh start — an empty `retired` becomes a claim "
               "nobody measured, and the lane re-buys what it had ruled out",
        "file": "control_app.py",
        "find": '        st["readable"] = None            # ⚠ NOT False — "unreadable" is not "fresh"',
        "replace": '        st["readable"] = False',
        "matches": 1,
    },
    {
        "why": "writing the store in place instead of tmp + os.replace — a crash mid-write loses "
               "every retirement, and a reader can see a torn file",
        "file": "control_app.py",
        "find": "        os.replace(tmp, dest)\n        return True",
        "replace": "        shutil.copyfile(tmp, dest)\n        return True",
        "matches": 1,
    },
    {
        "why": "unloading the ACTOR: a tick after a restart then sees no retirements and pays "
               "again for every reel the previous process had ruled out — the money bug v2901 "
               "shipped inside its own fix",
        "file": "control_app.py",
        "find": "    _vault_autoread_load()\n    if not _VAULT_AUTOREEL_ON:",
        "replace": "    if not _VAULT_AUTOREEL_ON:",
        "matches": 1,
    },
    {
        "why": "letting a save run before any load: empty memory is written over a good store and "
               "every retirement on disk is destroyed",
        "file": "control_app.py",
        "find": '    if not _VAULT_AUTOREAD_STORE.get("tried"):\n        _vault_autoread_load()',
        "replace": '    if False:\n        _vault_autoread_load()',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
