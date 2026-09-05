# -*- coding: utf-8 -*-
"""v2687 — THE ENTRY STAMP: the door that opened a reel must reach the reel.

WHY THIS GUARD EXISTS. Three layers each knew which door opened a reel and not one of them wrote
it where the reel could carry it:

    capture_preflight(door)   knew it, spent it on a per-door counter
    start_agent(origin=...)   knew it, kept it in a PARENT global, served it to the UI
    the journal               0 of 10,121 rows carried door/origin/entry

Measured 2026-09-05 on his ring. The consequence was not cosmetic: no reel could answer "which
door did I come through", so nothing downstream could route by entry, and the door ledger proved
it — `shadow` held opened=609/filmed=181 while `onair` and `mini` had NO opened and NO filmed at
all, because `shadow` is the only call site that passes opened=True. Two of three doors had an
empty Wilson denominator and read as fine. [[the-unjoined-end]] [[zero-needs-a-denominator]]

⚠ THIS GUARD MUST FAIL IF THE STAMP IS REMOVED AT EITHER END. A stamp written by the parent that
the child ignores, or read by the child that the parent never sends, is the same defect wearing
the other shoe — so both halves are asserted, plus the JOIN between their two vocabularies.
"""
import ast
import io
import os
import sys
import unittest

# ⚠ THIS FILE PRINTS NON-ASCII (⚠, ✕, ×) IN ITS ASSERTION MESSAGES, so stdout has to be made
# encoding-safe or it crashes while REPORTING on a non-UTF-8 console — his Windows box is cp1255,
# where a clean tree would exit non-zero for the sake of one glyph. Caught by test_control's own
# guard on the first push that carried this file. [[windows-powershell-gotchas]]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from console_safe import enable
    enable()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))


def _src(name):
    with io.open(os.path.join(HERE, name), "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


class ParentSendsTheDoor(unittest.TestCase):
    def test_env_clean_accepts_a_door(self):
        """The env builder must take a door — parsed, not grepped, so a comment cannot satisfy it."""
        tree = ast.parse(_src("control_app.py"))
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "_env_clean"), None)
        self.assertIsNotNone(fn, "_env_clean is gone — the one env builder for every spawn")
        args = [a.arg for a in fn.args.args]
        self.assertIn("door", args,
                      "_env_clean lost its `door` parameter, so the child can never be told which "
                      "door opened it")

    def test_tv_door_is_actually_written_into_the_env(self):
        s = _src("control_app.py")
        self.assertIn('env["TV_DOOR"]', s,
                      "TV_DOOR is never set: the door parameter would be accepted and dropped")

    def test_absent_door_removes_the_var_rather_than_defaulting(self):
        """An unknown door must stay unknown. Defaulting to 'onair' would forge provenance."""
        s = _src("control_app.py")
        self.assertIn('env.pop("TV_DOOR", None)', s,
                      "a spawn that cannot name its door must clear TV_DOOR, never inherit a "
                      "stale one from this process's environment")

    def test_start_agent_maps_every_origin_to_a_door(self):
        """origin ('hand'|'shadow'|'mini') and the ledger's doors ('onair'|'mini'|'shadow') are the
        same three things under two names. The map must be explicit and total."""
        s = _src("control_app.py")
        for origin, door in (("hand", "onair"), ("mini", "mini"), ("shadow", "shadow")):
            self.assertIn('"%s": "%s"' % (origin, door), s,
                          "origin %r no longer maps to door %r" % (origin, door))


class ChildStampsTheDoor(unittest.TestCase):
    def test_agent_reads_tv_door(self):
        s = _src("tv_diablo.py")
        self.assertIn('os.environ.get("TV_DOOR")', s,
                      "the agent never reads TV_DOOR, so the parent's stamp lands nowhere")

    def test_journal_stamps_the_door_on_rows(self):
        """The stamp goes on EVERY row, beside `sim`, for the same reason `sim` is there: a row
        read on its own must be placeable."""
        s = _src("tv_diablo.py")
        self.assertIn('rec["door"] = _DOOR', s,
                      "_journal no longer stamps the door onto rows")

    def test_the_field_is_door_not_origin(self):
        """tv_diablo already has an `origin` (settle|heartbeat|text-eye|farewell) answering a
        DIFFERENT question. Two quantities under one label on the same row is how a number ends up
        under a word that stopped being true. [[label-outlived-referent]]"""
        s = _src("tv_diablo.py")
        self.assertNotIn('rec["origin"] = _DOOR', s,
                         "the door must never be written as `origin` — that word is taken on these "
                         "same rows by the dispatch context")

    def test_an_absent_door_writes_no_key(self):
        """`if _DOOR and ...` — a reel filmed before this shipped reads as UNKNOWN, not 'onair'."""
        s = _src("tv_diablo.py")
        self.assertIn("if _DOOR and isinstance(rec, dict)", s,
                      "the stamp must be guarded on a non-empty door, or every pre-v2687 reel "
                      "silently acquires a door it never came through")


class TheJoinHolds(unittest.TestCase):
    """The two halves above can each be right while the pair is broken — this is the join."""

    def test_the_var_name_matches_on_both_sides(self):
        parent, child = _src("control_app.py"), _src("tv_diablo.py")
        self.assertIn("TV_DOOR", parent)
        self.assertIn("TV_DOOR", child)

    def test_the_stamp_survives_a_real_journal_call(self):
        """Behaviour, not source: set TV_DOOR, call the real _journal writer, read the row back."""
        import json
        import subprocess
        import sys
        import tempfile
        d = tempfile.mkdtemp(prefix="doorstamp_")
        code = (
            "import os,sys,json\n"
            "sys.path.insert(0, %r)\n"
            "os.environ['TV_DOOR']='mini'\n"
            "os.environ['TV_HIST']=%r\n"
            "import tv_diablo as T\n"
            "T._JQ=None\n"
            "T._journal({'lane':'deep','scene':'stash','sessionId':'s_test_1'})\n"
            "print('JPATH=' + T._journal_path())\n"
        ) % (HERE, d)
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            self.skipTest("agent import unavailable in this venue: %s" % (r.stderr or "")[-200:])
        path = ""
        for ln in (r.stdout or "").splitlines():
            if ln.startswith("JPATH="):
                path = ln[6:].strip()
        self.assertTrue(path and os.path.isfile(path),
                        "the journal path was not produced — nothing to verify against")
        rows = []
        with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    pass
        mine = [x for x in rows if x.get("sessionId") == "s_test_1"]
        self.assertTrue(mine, "the row this test wrote is not in the journal (measured %d rows) — "
                              "the probe, not the stamp, is what failed" % len(rows))
        self.assertEqual(mine[-1].get("door"), "mini",
                         "TV_DOOR=mini was set and the row came back carrying door=%r"
                         % mine[-1].get("door"))


class EveryDoorEarnsItsDenominator(unittest.TestCase):
    """v2687 — the half of this that was silently broken for a week.

    v2316 gave each door a Wilson score. Only `shadow` ever passed opened=True, so `onair` and
    `mini` had NO denominator at all — and their `refused` counters kept ticking, which made the
    ledger look alive. A score nobody increments cannot fail, so nothing ever reported it."""

    def _opened_calls(self):
        """Parse the calls; a grep would count the word inside the comment that explains it."""
        tree = ast.parse(_src("control_app.py"))
        out = []
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            if not (isinstance(f, ast.Name) and f.id == "_capture_door_note"):
                continue
            opened = any(k.arg == "opened" for k in n.keywords)
            out.append((n.lineno, opened, len(n.args)))
        return out

    def test_the_credit_is_claimed_in_exactly_one_place(self):
        calls = self._opened_calls()
        self.assertTrue(calls, "no _capture_door_note calls found — the probe failed, not the code")
        credited = [c for c in calls if c[1]]
        self.assertEqual(len(credited), 1,
                         "expected exactly ONE site to credit an open (start_agent, which every "
                         "door reaches); found %d of %d calls passing opened=. Two sites means a "
                         "reel counted twice for one door." % (len(credited), len(calls)))

    def test_that_place_is_start_agent(self):
        tree = ast.parse(_src("control_app.py"))
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "start_agent"), None)
        self.assertIsNotNone(fn, "start_agent is gone")
        lines = {n.lineno for n in ast.walk(fn)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == "_capture_door_note" and any(k.arg == "opened" for k in n.keywords)}
        self.assertEqual(len(lines), 1,
                         "the open must be credited inside start_agent — the ONE place a reel is "
                         "confirmed rolling. Crediting at a door instead is what left onair and "
                         "mini with an empty denominator since c1b2865a.")

    def test_the_credit_covers_every_door_not_a_literal(self):
        """It must credit the door it was CALLED with. A literal here would re-create the bug for
        the two doors that are not named."""
        s = _src("control_app.py")
        self.assertIn("_capture_door_note(_door_of_origin(origin), None, opened=True)", s,
                      "the open is credited for a hardcoded door rather than the calling one")

    def test_all_three_origins_map_to_a_door(self):
        import importlib
        import sys as _s
        _s.path.insert(0, HERE)
        CA = importlib.import_module("control_app")
        for origin, door in (("hand", "onair"), ("mini", "mini"), ("shadow", "shadow")):
            self.assertEqual(CA._door_of_origin(origin), door)
        self.assertEqual(CA._door_of_origin(None), "onair",
                         "an unlabelled caller is a hand click — the v2362 default")


class AnOpenDoesNotRestampWhatItDidNotMeasure(unittest.TestCase):
    """v2689 — found by reviewing v2687's own shipped bytes, not by a gate.

    v2687 began crediting opens with `_capture_door_note(door, None, opened=True)`. This function
    then moved `lastAt` to now and blanked `lastWhy`, while every `last_*` fact kept its value from
    an OLDER preflight — because the fact-copy loop is guarded on `pre` and pre was None.

    Reproduced before the fix: a preflight recording why='disk too full', screenRecOk=False,
    freeGb=3.1, followed by an open, left the row reading "as of one second ago, Screen Recording
    was denied and the disk had 3.1GB" — a moment at which nothing was measured — with the
    sentence that explained it deleted. An open and a look are different events.
    [[stale-reading]] [[label-outlived-referent]]"""

    def _isolated(self):
        import importlib
        import json as _j
        import sys as _s
        _s.path.insert(0, HERE)
        CA = importlib.import_module("control_app")
        store = {}
        CA._capture_door_load = lambda: _j.loads(_j.dumps(store))

        def _save(x):
            store.clear()
            store.update(_j.loads(_j.dumps(x)))

        CA._capture_door_save = _save
        return CA, store

    def test_an_open_preserves_the_last_looks_facts_and_reason(self):
        import time as _t
        CA, store = self._isolated()
        CA._capture_door_note("mini", {"why": "disk too full", "screenRecOk": False,
                                       "freeGb": 3.1, "diskOk": False})
        was = dict(store["mini"])
        _t.sleep(0.02)
        CA._capture_door_note("mini", None, opened=True)
        row = store["mini"]
        self.assertEqual(row["lastAt"], was["lastAt"],
                         "an open with no preflight moved lastAt, so stale facts now sit under a "
                         "fresh timestamp")
        self.assertEqual(row["lastWhy"], "disk too full",
                         "an open erased the reason the last LOOK recorded")
        self.assertEqual(row["last_freeGb"], 3.1)
        self.assertIs(row["last_screenRecOk"], False)

    def test_the_open_is_still_recorded_with_its_own_stamp(self):
        """The fix must not achieve tidiness by dropping the credit — that would restore the empty
        denominator v2687 existed to fill."""
        CA, store = self._isolated()
        CA._capture_door_note("mini", {"why": "", "screenRecOk": True, "freeGb": 55.0})
        CA._capture_door_note("mini", None, opened=True)
        row = store["mini"]
        self.assertEqual(row.get("opened"), 1, "the open was not counted")
        self.assertTrue(row.get("openedAt"), "the open carries no timestamp of its own")

    def test_a_real_preflight_still_updates_everything(self):
        """The guard must not freeze the row: a genuine look still refreshes facts AND reason."""
        CA, store = self._isolated()
        CA._capture_door_note("mini", {"why": "disk too full", "screenRecOk": False, "freeGb": 3.1})
        CA._capture_door_note("mini", {"why": "", "screenRecOk": True, "freeGb": 55.0})
        row = store["mini"]
        self.assertIs(row["last_screenRecOk"], True)
        self.assertEqual(row["last_freeGb"], 55.0)
        self.assertEqual(row["lastWhy"], "", "a clean look must clear the previous refusal reason")


if __name__ == "__main__":
    unittest.main(verbosity=2)
