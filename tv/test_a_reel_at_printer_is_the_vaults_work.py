# -*- coding: utf-8 -*-
"""#50 — A REEL THE RIVER HOLDS AT PRINTER IS THE VAULT LANE'S WORK, WHATEVER RETENTION CALLS IT (REG-1446).

PRINTER means "names were read off the frames and the session carries no seal". The only writer of that
seal is the vault sweep. But the vault lane chose its work from retention's tag alone, and retention
answers a different question - why is this reel still ON DISK - first-match-wins. So a PRINTER reel filed
as `recent` or `zero-pages` never carried a vault tag, the lane published owed:0 (a healthy idle lamp),
and the reel waited for a seal nothing would write. river_walk's own PRINTER probe had been printing that
sentence ("retention's rules are first-match-wins ... waits for a seal nothing will write").

MEASURED 2026-09-29: the ALT held 25 reels at PRINTER since 09-27, every one `zero-pages`, vault lane
`reads: 0`, no vault store ever written. His Mac held 4, every one `recent` (265, 23, 26, 14 names).
Replayed on his Mac's real shelf, the new rule adds exactly those 4 and no fixture.

ONE DEFINITION, `shelf_driver.vault_owes_read(tag, station)`, asked by all three readers: the sweeper's
list (`_vault_owed_reels`), the SHELF's "awaiting a sweep" count, and river_walk's PRINTER probe.

DRIVEN: the rule's table stated independently here; `_vault_owed_reels` run through its real body with
retention's plan and the river's positions stubbed at the module edge; `river_stamp.positions` on a temp
store; `river_walk.walk` on a stubbed shelf. RED_PROOF below.
"""
import io
import json
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import shelf_driver as SD  # noqa: E402
import river_stamp as RS  # noqa: E402


class TheRuleSaysPrinterIsTheVaultsWork(unittest.TestCase):
    """The table, written out here on purpose - a law that asked the function what it returns would
    agree with any answer."""

    def test_a_printer_reel_is_owed_whatever_retention_calls_it(self):
        for tag in ("recent", "zero-pages", "never-chronicle-swept", "holds-proof", "target-met",
                    "eligible"):
            self.assertTrue(SD.vault_owes_read(tag, "PRINTER"),
                            "a reel at PRINTER filed as %r is not the vault's work - it waits for a "
                            "seal nothing will write" % tag)

    def test_the_vetoes_hold_even_at_printer(self):
        from unittest import mock
        import frame_authority as FA
        # no-witness-index is held here while the store state is UNKNOWN or unreadable (REG-1743 below)
        with mock.patch.object(FA, "witness_index", lambda root=None: {"ok": False, "haveIndex": False}):
            for tag in ("test-fixture", "no-witness-index", "ledger-unreadable", "rows-not-banked"):
                self.assertFalse(SD.vault_owes_read(tag, "PRINTER"),
                                 "%r at PRINTER would be BOUGHT: a fixture, an UNKNOWN, or a reel owed a "
                                 "bank rather than a read" % tag)

    def test_a_pc_that_never_wrote_a_witness_store_owes_its_printer_reels_a_read(self):
        """REG-1743 - the ALT: 62 reels at PRINTER, all `no-witness-index`, both stores ABSENT, read 0 ever. Only a
        vault read writes those stores, so vetoing the tag there was a deadlock, not caution."""
        from unittest import mock
        import frame_authority as FA
        with mock.patch.object(FA, "witness_index", lambda root=None: {"ok": True, "haveIndex": False}):
            self.assertTrue(SD.vault_owes_read("no-witness-index", "PRINTER"),
                            "a fresh PC's PRINTER reel waits for a store that only this read can write")
            for st in (None, "EMPTY", "ROUTED", "CAPTURE"):
                self.assertFalse(SD.vault_owes_read("no-witness-index", st), "bought away from PRINTER at %r" % st)

    def test_an_unknown_witness_state_still_never_spends(self):
        from unittest import mock
        import frame_authority as FA

        def boom(root=None):
            raise OSError("store unreadable")
        with mock.patch.object(FA, "witness_index", boom):
            self.assertFalse(SD.vault_owes_read("no-witness-index", "PRINTER"))
        with mock.patch.object(FA, "witness_index", lambda root=None: {"ok": False, "haveIndex": False}):
            self.assertFalse(SD.vault_owes_read("no-witness-index", "PRINTER"),
                             "a store that will not read was treated as one never written")

    def test_the_old_tags_still_owe_anywhere(self):
        for st in (None, "CAPTURE", "EMPTY", "PRINTER"):
            self.assertTrue(SD.vault_owes_read("vault-owes", st))
            self.assertTrue(SD.vault_owes_read("panels-never-banked", st))

    def test_an_unknown_position_is_never_guessed_to_be_printer(self):
        self.assertFalse(SD.vault_owes_read("zero-pages", None))
        for tag in (None, "", "mystery-tag"):
            self.assertFalse(SD.vault_owes_read(tag, "PRINTER"),
                             "a tag retention never emits (%r) was bought at PRINTER - a deny-list lets "
                             "anything unforeseen spend" % (tag,))
        self.assertFalse(SD.vault_owes_read("recent", "EMPTY"))
        self.assertFalse(SD.vault_owes_read("recent", "UNKNOWN"))


class ThePositionsComeFromTheRiversOwnRecord(unittest.TestCase):

    def test_the_last_stamp_wins_and_a_missing_store_is_empty_not_unknown(self):
        d = tempfile.mkdtemp(prefix="printer_law_")
        p = os.path.join(d, "river_stamp.jsonl")
        self.assertEqual(RS.positions(p)[0], {}, "a store that does not exist yet read as UNKNOWN")
        with io.open(p, "w", encoding="utf-8") as fh:
            for i, (reel, st) in enumerate((("reel_s_1_a", "TRIAGE"), ("reel_s_1_a", "PRINTER"),
                                            ("reel_s_2_b", "EMPTY"))):
                fh.write(json.dumps({"at": 1000 + i, "seq": i, "reel": reel, "station": st,
                                     "by": "law", "byKind": "observer"}) + "\n")
        pos, _w = RS.positions(p)
        self.assertEqual(pos, {"reel_s_1_a": "PRINTER", "reel_s_2_b": "EMPTY"})


class TheSweeperSelectsOnTheRule(unittest.TestCase):

    KEPT = [
        {"reel": "reel_s_10_a", "tag": "zero-pages"},      # PRINTER  -> owed (the ALT's 25)
        {"reel": "reel_s_11_b", "tag": "recent"},          # PRINTER  -> owed (his Mac's 4)
        {"reel": "reel_s_12_c", "tag": "test-fixture"},    # PRINTER  -> vetoed
        {"reel": "reel_s_13_d", "tag": "recent"},          # EMPTY    -> not owed
        {"reel": "reel_s_14_e", "tag": "zero-pages"},      # PRINTER, but ALREADY SEALED (stale stamp)
        {"reel": "reel_s_15_f", "tag": "vault-owes"},      # the old path, unchanged
    ]
    POS = {"reel_s_10_a": "PRINTER", "reel_s_11_b": "PRINTER", "reel_s_12_c": "PRINTER",
           "reel_s_13_d": "EMPTY", "reel_s_14_e": "PRINTER", "reel_s_15_f": "CAPTURE"}

    def _owed(self, pos, seals):
        import control_app as ca
        import reel_retention as rr
        with mock.patch.object(rr, "plan", lambda h, **k: {"ok": True, "kept": list(self.KEPT)}), \
                mock.patch.object(ca, "_vault_positions_and_seals", lambda: (pos, seals)):
            got = ca._vault_owed_reels(hist=tempfile.gettempdir())
        return sorted(os.path.basename(g) for g in (got or []))

    def test_the_printer_reels_are_on_the_list(self):
        got = self._owed(self.POS, {"s_14_e": {"by": "vault"}})
        self.assertEqual(got, ["reel_s_10_a", "reel_s_11_b", "reel_s_15_f"],
                         "the vault's work list is wrong: %r" % got)

    def test_an_unreadable_river_is_unknown_not_a_shorter_list(self):
        import control_app as ca
        import reel_retention as rr
        with mock.patch.object(rr, "plan", lambda h, **k: {"ok": True, "kept": list(self.KEPT)}), \
                mock.patch.object(ca, "_vault_positions_and_seals", lambda: (None, {})):
            got = ca._vault_owed_reels(hist=tempfile.gettempdir())
        self.assertIsNone(got, "an unreadable stamp log produced a confident list (%r) - the PRINTER half "
                               "was silently dropped and the lamp would read it as measured" % (got,))

    def test_an_unreadable_seal_store_adds_nothing_through_printer(self):
        self.assertEqual(self._owed(self.POS, None), ["reel_s_15_f"],
                         "with the seals UNKNOWN a stale PRINTER stamp could re-buy a sealed reel")

    def test_a_seal_under_either_spelling_is_honoured(self):
        got = self._owed(self.POS, {"reel_s_14_e": {"by": "vault"}})
        self.assertNotIn("reel_s_14_e", got, "a seal stored under the prefixed key was not recognised")


class _FakeStory(types.ModuleType):
    STAGES = ("SHELF", "READ", "SEALED")

    def __init__(self, tag):
        types.ModuleType.__init__(self, "reel_story")
        self.tag = tag

    def story(self, hist_dir=None):
        return {"ok": True, "reels": [{"reel": "reel_s_20_z", "tag": self.tag, "stage": "READ",
                                       "stageIdx": 1, "stageKnown": True, "held": True,
                                       "holdKind": "policy", "why": "law"}]}


class _FakeRouter(types.ModuleType):
    def __init__(self):
        types.ModuleType.__init__(self, "reel_router")

    def route(self, hist=None):
        return {"ok": True, "reels": [{"reel": "reel_s_20_z", "station": "PRINTER", "owes": "SEAL",
                                       "why": "7 name(s) read and the session carries no seal",
                                       "sealed": False, "names": 7}]}


class _FakePrinter(types.ModuleType):
    STATIONS = ()

    def __init__(self):
        types.ModuleType.__init__(self, "printer")

    def stream(self, name):
        return {"ok": False, "why": "law"}


class TheRiverProbeAgreesWithTheSweeper(unittest.TestCase):

    def _walk(self, tag):
        import river_walk as RW
        mods = {"reel_story": _FakeStory(tag), "reel_router": _FakeRouter(), "printer": _FakePrinter()}
        with mock.patch.dict(sys.modules, mods):
            return RW.walk("reel_s_20_z")

    def test_a_zero_pages_reel_at_printer_is_on_the_lanes_queue(self):
        out = self._walk("zero-pages")
        q = ((out.get("next") or {}).get("queue") or {})
        self.assertNotIn("nothing will write", str(q.get("why")),
                         "the river still says the seal will never be written, while the sweeper "
                         "selects this reel: %r" % q.get("why"))
        self.assertGreaterEqual(q.get("carryingIt") or 0, 1)

    def test_a_fixture_at_printer_still_reads_as_nobodys(self):
        q = ((self._walk("test-fixture").get("next") or {}).get("queue") or {})
        self.assertIn("nothing will write", str(q.get("why")),
                      "PREMISE: a vetoed reel should still read as waiting on nobody: %r" % q.get("why"))


class TheTriageHasRuled(unittest.TestCase):
    """REG-1749 — a reel retro_triage walked in full and found no panel on owes the vault no paid read.

    MEASURED on the ALT: REG-1743 sent the vault to its reel …11808 (1,212 frames, 0 panels by a FULL triage);
    the pass found no stash, could not prove its gate live, called it UNKNOWN and requeued it. The rule now asks
    retention's own reading - the chronicle rule's call since REG-1747 - when its caller names the reel."""
    EMPTY = "reel_s_1500000000005_11808"      # synthetic (2017 epoch)
    KEPT = TheSweeperSelectsOnTheRule.KEPT
    POS = TheSweeperSelectsOnTheRule.POS

    def _proven(self, *empty):
        import reel_retention as rr
        return mock.patch.object(rr, "_proven_empty", lambda r: r in empty)

    def test_a_proven_empty_reel_owes_nothing_whatever_its_tag(self):
        import frame_authority as FA
        with self._proven(self.EMPTY), \
                mock.patch.object(FA, "witness_index", lambda root=None: {"ok": True, "haveIndex": False}):
            self.assertFalse(SD.vault_owes_read("no-witness-index", "PRINTER", self.EMPTY),
                             "a reel the triage proved empty was still sent to the vault - the ALT's 1,212-frame reel")
            self.assertFalse(SD.vault_owes_read("vault-owes", "PRINTER", self.EMPTY))
            self.assertTrue(SD.vault_owes_read("no-witness-index", "PRINTER", "reel_s_1500000000006_99999"),
                            "PREMISE: a reel the triage did NOT rule on must still owe on a fresh PC")

    def test_a_triage_that_cannot_answer_keeps_the_read_owed(self):
        """REG-1749 (the v3566 second eye) - an error while asking the triage is NOT PROVEN, never "empty": the read
        stays owed, the triage's own rule ("NOT SURVEYED IS NOT EMPTY - the unknown case must fall on the keep side").
        The eye was right that no case exercised the except path; this one does."""
        import frame_authority as FA
        import reel_retention as rr

        def boom(_r):
            raise RuntimeError("law: the triage store will not read")
        with mock.patch.object(rr, "_proven_empty", boom), \
                mock.patch.object(FA, "witness_index", lambda root=None: {"ok": True, "haveIndex": False}):
            self.assertTrue(SD.vault_owes_read("no-witness-index", "PRINTER", self.EMPTY),
                            "a triage that raised was read as 'proven empty' and the reel was dropped - UNKNOWN "
                            "must keep the read owed")

    def test_no_reel_named_decides_as_before(self):
        with self._proven(self.EMPTY):
            self.assertTrue(SD.vault_owes_read("vault-owes", "PRINTER"),
                            "with no reel named, the triage must not be consulted at all")

    def test_the_sweepers_list_drops_the_proven_empty_reel(self):
        with self._proven("reel_s_15_f"):
            got = TheSweeperSelectsOnTheRule._owed(self, self.POS, {"s_14_e": {"by": "vault"}})
        self.assertNotIn("reel_s_15_f", got, "the sweeper's own list still holds a reel the triage proved empty: %r"
                                             % (got,))
        self.assertIn("reel_s_10_a", got, "PREMISE: the other PRINTER reels stay on the list")

    def test_the_lane_counts_what_the_triage_ruled(self):
        """REG-1751 — the heart can see the join: the vault lane's state says how many reels it skipped because the
        triage proved them empty, so a join that silently stops being asked shows as a number that moved."""
        import control_app as ca
        with self._proven("reel_s_15_f", "reel_s_11_b"):
            TheSweeperSelectsOnTheRule._owed(self, self.POS, {"s_14_e": {"by": "vault"}})
        self.assertEqual(ca._TRIAGE_RULED_EMPTY.get("vault"), 2,
                         "the vault lane skipped 2 triage-proven reels and its count says %r"
                         % (ca._TRIAGE_RULED_EMPTY.get("vault"),))

    def test_an_early_unknown_does_not_keep_the_last_vault_count(self):
        """REG-1755 — six early returns left the previous pass's count in place, so the heart showed
        a number beside owed=UNKNOWN."""
        import control_app as ca
        import reel_retention as rr
        ca._TRIAGE_RULED_EMPTY["vault"] = 7
        with mock.patch.object(rr, "plan", lambda h, **k: {"ok": True, "kept": []}), \
                mock.patch.object(ca, "_vault_positions_and_seals", lambda: (None, {})):
            got = ca._vault_owed_reels(hist=tempfile.gettempdir())
        self.assertIsNone(got, "PREMISE: an unreadable river is UNKNOWN")
        self.assertIsNone(ca._TRIAGE_RULED_EMPTY.get("vault"),
                          "the vault list returned UNKNOWN and the heart still shows the last count, 7")

    def test_a_status_poll_during_a_pass_reads_the_last_count_not_unknown(self):
        """REG-1943 (the #231 eye on v3568) - REG-1755 cleared the count on ENTRY, so a status poll on another thread
        during a long pass read UNKNOWN although the last pass had counted. MEASURED before the fix: 2 -> None -> 2
        across one overlapping pass. The pass now assigns its count once, after it ends."""
        import threading
        import control_app as ca
        import reel_retention as rr
        gate, inside = threading.Event(), threading.Event()
        kept = list(TheSweeperSelectsOnTheRule.KEPT)

        def plan(h, **k):
            if threading.current_thread().name == "law-second-pass":
                inside.set()
                gate.wait(10)
            return {"ok": True, "kept": list(kept)}
        with self._proven("reel_s_15_f", "reel_s_11_b"), mock.patch.object(rr, "plan", plan), \
                mock.patch.object(ca, "_vault_positions_and_seals", lambda: (self.POS, {"s_14_e": {"by": "vault"}})):
            ca._vault_owed_reels(hist=tempfile.gettempdir())
            self.assertEqual(2, ca._TRIAGE_RULED_EMPTY.get("vault"), "PREMISE: the finished pass counted 2")
            t = threading.Thread(target=ca._vault_owed_reels, kwargs={"hist": tempfile.gettempdir()},
                                 name="law-second-pass", daemon=True)
            t.start()
            try:
                self.assertTrue(inside.wait(10), "PREMISE: the second pass never reached the plan")
                during = ca._TRIAGE_RULED_EMPTY.get("vault")
            finally:
                gate.set()
                t.join(10)
        self.assertEqual(2, during, "a status poll during a pass read %r - UNKNOWN over a count that was measured"
                                    % (during,))

    def test_a_pass_that_raises_clears_the_count(self):
        """REG-1943 - the one assignment runs on a raise too: a pass that blew up is UNKNOWN, never the last count."""
        import control_app as ca
        import reel_retention as rr
        ca._TRIAGE_RULED_EMPTY["vault"] = 7

        def boom(*a, **k):
            raise RuntimeError("law: the rule blew up mid-pass")
        with mock.patch.object(rr, "plan", lambda h, **k: {"ok": True, "kept": list(TheSweeperSelectsOnTheRule.KEPT)}), \
                mock.patch.object(ca, "_vault_positions_and_seals", lambda: (self.POS, {})), \
                mock.patch.object(SD, "vault_owes_read", boom):
            with self.assertRaises(RuntimeError):
                ca._vault_owed_reels(hist=tempfile.gettempdir())
        self.assertIsNone(ca._TRIAGE_RULED_EMPTY.get("vault"), "a pass that raised left the last count, 7")

    def test_a_chronicle_pass_that_cannot_list_reels_clears_its_count(self):
        """REG-1755 — the first except in _chron_owed_count returned None and left the chronicle count."""
        import control_app as ca
        import chronicle_retro
        ca._TRIAGE_RULED_EMPTY["chronicle"] = 4
        with mock.patch.object(chronicle_retro, "reel_dirs",
                               side_effect=OSError("law: the reel list will not read")):
            n = ca._chron_owed_count(tempfile.gettempdir())
        self.assertIsNone(n, "PREMISE: an unreadable reel list is UNKNOWN, not a guessed 0")
        self.assertIsNone(ca._TRIAGE_RULED_EMPTY.get("chronicle"),
                          "the chronicle pass could not count and the heart still shows the last count, 4")


RED_PROOF = [
    {"why": "REG-1743 - a fresh PC's PRINTER reels are vetoed again: the vault never reads, so no store is ever written",
     "file": "shelf_driver.py",
     "find": "        return _no_witness_store_was_ever_written()\n",
     "replace": "        return False\n",
     "matches": 1},
    {"why": "REG-1743 - an unreadable witness store is treated as one never written, and spends",
     "file": "shelf_driver.py",
     "find": "    return wi.get(\"ok\") is True and wi.get(\"haveIndex\") is False\n",
     "replace": "    return wi.get(\"haveIndex\") is False\n",
     "matches": 1},
    {
        "why": "2026-09-29 (second eye) - an unreadable stamp log yields a confident shorter list instead of UNKNOWN",
        "file": "tv/control_app.py",
        "find": "    if _pos is None:\n        return None, None\n    out = []\n",
        "replace": "    _pos = _pos or {}\n    out = []\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (second eye) - a tag retention never emits is bought at PRINTER",
        "file": "tv/shelf_driver.py",
        "find": "        return tag in _rr.RULES\n",
        "replace": "        return True\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the router's PRINTER position is ignored again: the ALT's 25 reels wait forever",
        "file": "tv/shelf_driver.py",
        "find": "    if station != \"PRINTER\":\n        return False\n",
        "replace": "    return False\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - a fixture at PRINTER is bought by a paid vault read",
        "file": "tv/shelf_driver.py",
        "find": "VAULT_READ_VETO = (\"test-fixture\", \"no-witness-index\", \"ledger-unreadable\", \"rows-not-banked\")\n",
        "replace": "VAULT_READ_VETO = (\"no-witness-index\", \"ledger-unreadable\", \"rows-not-banked\")\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - a reel the vault already sealed is re-bought on a stale PRINTER stamp",
        "file": "tv/control_app.py",
        "find": "            if _sealed is None or _rr.lookup_either_way(_sealed, rid) is not None:\n",
        "replace": "            if False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - river_walk's probe goes back to the tag alone and says 'a seal nothing will write' over a queued reel",
        "file": "tv/river_walk.py",
        "find": "            if _this_owed and row.get(\"tag\") not in _tags:\n                owes += 1\n",
        "replace": "",
        "matches": 1,
    },
    {"why": "REG-1749 - the vault rule stops asking the triage: a reel proven empty is paid for again",
     "file": "tv/shelf_driver.py",
     "find": "    if reel and _proven_empty(reel):\n        return False\n",
     "replace": "    if False:\n        return False\n",
     "matches": 1},
    {"why": "REG-1749 - the sweeper's list stops naming the reel, so the triage is never asked for it",
     "file": "tv/control_app.py",
     "find": "        if not _sd.vault_owes_read(k.get(\"tag\"), _pos.get(rid), rid):\n",
     "replace": "        if not _sd.vault_owes_read(k.get(\"tag\"), _pos.get(rid)):\n",
     "matches": 1},
    {"why": "REG-1751 - the vault lane stops counting the reels the triage ruled empty: the heart cannot see the join",
     "file": "tv/control_app.py",
     "find": "            _ruled += 1                  # REG-1751 - counted from the same triage reading the rule asks\n",
     "replace": "            pass\n",
     "matches": 1},
    {"why": "REG-1749 - a triage that cannot answer is taken as proven empty: the read is dropped on an error",
     "file": "tv/shelf_driver.py",
     "find": "        return bool(_rr._proven_empty(_os.path.basename(str(reel))))\n    except Exception:\n        return False\n",
     "replace": "        return bool(_rr._proven_empty(_os.path.basename(str(reel))))\n    except Exception:\n        return True\n",
     "matches": 1},
    {"why": "REG-1755 - an early UNKNOWN from the vault list keeps the last triage count beside owed=UNKNOWN",
     "file": "tv/control_app.py",
     "find": "        _TRIAGE_RULED_EMPTY[\"vault\"] = ruled   # REG-1755 - UNKNOWN unless this pass counted\n",
     "replace": "        _TRIAGE_RULED_EMPTY[\"vault\"] = ruled if ruled is not None else _TRIAGE_RULED_EMPTY[\"vault\"]\n",
     "matches": 1},
    {"why": "REG-1943 - the vault count is cleared on ENTRY again: a status poll during a pass reads UNKNOWN",
     "file": "tv/control_app.py",
     "find": "    out, ruled = None, None\n    try:\n        out, ruled = _vault_owed_reels_counted(hist)\n",
     "replace": "    out, ruled = None, None\n    _TRIAGE_RULED_EMPTY[\"vault\"] = None\n    try:\n"
                "        out, ruled = _vault_owed_reels_counted(hist)\n",
     "matches": 1},
    {"why": "REG-1943 - a pass that raises keeps the last count standing",
     "file": "tv/control_app.py",
     "find": "    try:\n        out, ruled = _vault_owed_reels_counted(hist)\n    finally:\n",
     "replace": "    try:\n        out, ruled = _vault_owed_reels_counted(hist)\n    except Exception:\n"
                "        raise\n    else:\n",
     "matches": 1},
    {"why": "REG-1755 - a chronicle pass that cannot list the reels keeps the last triage count",
     "file": "tv/control_app.py",
     "find": "        _TRIAGE_RULED_EMPTY[\"chronicle\"] = None   # REG-1755 - this pass did not count\n",
     "replace": "",
     "matches": 1}
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
