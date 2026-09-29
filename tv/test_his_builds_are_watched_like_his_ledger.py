# -*- coding: utf-8 -*-
"""#41 rank 5 (2026-09-29, REG-1481) — HIS BUILDS AND HIS HAND PLACEMENTS ARE WATCHED LIKE HIS LEDGER.

THE GAP, as the heart audit measured it: his builds (d2r_charBuilds) and his hand placements (d2r_muleEquip,
d2r_muleAssign) have travelled in the automatic backup since v2737 — `allStores` is the board's complete export —
and NO drop watcher judged them. `ledger_restore.drops_between` and `step_episodes` looped over BACKED_UP only;
the put-back invariant read `blob['ledger']` and never `allStores`; control_app and console_doctor had 0 matches
for charBuilds / muleEquip. Wiping his builds opened no episode, raised nothing, and the prune could take the last
file that held them. MEASURED read-only on his real backups that day: the newest snapshot HOLDS d2r_charBuilds
(1 build) and d2r_muleEquip — the data was there, and nothing was looking.

⚠ AND A SECOND, QUIETER HOLE: `_ledger_snapshot_once` wrote NO snapshot when the board's ledger COUNTS were
unchanged — and the watcher only judges snapshots. A build wiped between two snapshots with nothing found in
between would never have produced the file the watch reads. The hand-made counts now ride beside the ledger's
in that comparison. [[the-unjoined-end]]

WHAT THIS PINS, driven against FIXTURE blobs in a temp dir (his backup dir, his drop record and his board are
never opened):
  1. a hand-made store is COUNTED off `allStores` (the board's own JSON text); absent / unparseable / a bare
     ledger stays UNKNOWN, never 0 — "the export did not carry it" and "he had none" must not read the same;
  2. the SAME drop line as the ledger: 3 builds -> 0 is a drop; his own Delete of one (3 -> 2) is not;
  3. `step_episodes` opens ONE episode naming the file BEFORE the wipe, and recovery closes it;
  4. the console's own watcher (`_ledger_drop_watch`) opens it over real files, and the prune KEEPS that
     `beforeFile` while the episode is open;
  5. the doctor's row names the store, the fall and the FILE as the door — never the chronicle plan, which
     puts back none of what fell;
  6. the snapshot writer compares the hand-made counts, so a builds-only change is a new snapshot;
  7. cbMain is a declared POINTER, not a counted store, and every counted store has a declared way back.
Fixtures only. [[feedback-fixtures-never-touch-live-data]]
"""
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402  — this law's scratch dirs leave with it
_fx_tmp.contain()

import ledger_restore as LR   # noqa: E402
import control_app as CA      # noqa: E402
import console_doctor as CD   # noqa: E402

ROUTE = {"id": "f1xture000000000000000000000000a", "p": "main", "pfx": ""}
RK = LR._route_key(ROUTE)


def _builds(n):
    """n builds, as the Character Builder stores them (a dict keyed by build id)."""
    return json.dumps(dict(("b%d" % i, {"name": "Build %d" % i, "cls": "Sorceress", "level": 80, "at": i})
                           for i in range(1, n + 1)))


def _blob(builds=3, mule_equip=None, mule_assign=None, all_stores=True, found=280):
    """A backup blob the SHAPE the writer produces: ledger + counts + allStores (values are JSON TEXT)."""
    al = None
    if all_stores:
        al = {"d2r_someOtherKey": "1"}
        if builds is not None:
            al["d2r_charBuilds"] = builds if isinstance(builds, str) else _builds(builds)
        if mule_equip is not None:
            al["d2r_muleEquip"] = mule_equip
        if mule_assign is not None:
            al["d2r_muleAssign"] = mule_assign
    led = {"foundLog": dict(("Item %d" % i, 1700000000000 + i) for i in range(found)),
           "setPieces": ["Piece %d" % i for i in range(134)],
           "owned": ["Own %d" % i for i in range(223)]}
    return {"takenAt": "fixture", "source": "fixture", "route": ROUTE,
            "counts": {"foundLog": found, "setPieces": 134, "owned": 223, "runewordsMade": 0},
            "ledger": led, "allStores": al}


class HandMadeStoresAreCounted(unittest.TestCase):

    def test_a_hand_made_store_is_counted_off_allStores(self):
        b = _blob(builds=3, mule_equip=json.dumps({"m1": {"setI": {"head": {"name": "Shako"}}}}),
                  mule_assign=json.dumps({"Shako": "m1", "Enigma": "m1"}))
        self.assertEqual(LR.store_count(b, "charBuilds"), 3)
        self.assertEqual(LR.store_count(b, "muleEquip"), 1)
        self.assertEqual(LR.store_count(b, "muleAssign"), 2)
        self.assertEqual(LR.store_count(b, "foundLog"), 280, "the ledger path was disturbed")

    def test_absent_unparseable_or_a_bare_ledger_is_UNKNOWN_never_zero(self):
        self.assertIsNone(LR.store_count(_blob(builds=None), "charBuilds"), "absent read as a number")
        self.assertIsNone(LR.store_count(_blob(all_stores=False), "charBuilds"), "no allStores read as a number")
        self.assertIsNone(LR.store_count(_blob(builds="not json {"), "charBuilds"), "unparseable read as a number")
        self.assertIsNone(LR.store_count(_blob(builds='"a string"'), "charBuilds"), "a JSON string read as a count")
        self.assertIsNone(LR.store_count({"foundLog": {}}, "charBuilds"), "a bare ledger read as a number")
        self.assertEqual(LR.store_count(_blob(builds="{}"), "charBuilds"), 0, "a measured empty store is 0")

    def test_cbMain_is_a_declared_pointer_not_a_counted_store(self):
        """The Characters tab clears it with removeItem when the MAIN is deleted — a choice with an Undo. Counting
        it would page on his own action; not naming it would read as an oversight."""
        self.assertNotIn("cbMain", LR.HAND_MADE)
        self.assertIn("cbMain", LR.HAND_MADE_POINTERS)
        self.assertIsNone(LR.store_count(_blob(), "cbMain"))

    def test_every_counted_store_has_a_declared_way_back(self):
        for s in LR.HAND_MADE:
            self.assertTrue(str(LR.HAND_MADE_DOOR.get(s) or "").strip(),
                            "%s is watched and has no door — judged, paged, and nowhere to send him" % s)
        self.assertEqual(sorted(LR.HAND_MADE_DOOR), sorted(LR.HAND_MADE),
                         "HAND_MADE and HAND_MADE_DOOR name different stores")
        for s in LR.HAND_MADE:
            self.assertIn("allStores", LR.HAND_MADE_DOOR[s], "%s's door does not say where the file keeps it" % s)


class TheDropLineIsTheLedgers(unittest.TestCase):

    def test_a_wipe_is_a_drop_and_his_own_delete_of_one_build_is_not(self):
        wiped = LR.drops_between(_blob(builds=3), _blob(builds="{}"))
        self.assertEqual([(d["store"], d["from"], d["to"]) for d in wiped], [("charBuilds", 3, 0)],
                         "3 builds -> 0 did not open as a charBuilds drop: %r" % wiped)
        self.assertEqual(LR.drops_between(_blob(builds=3), _blob(builds=2)), [],
                         "his own Delete of one build (3 -> 2) paged — that is crying wolf on his hand")
        self.assertEqual(LR.drops_between(_blob(builds=3), _blob(builds=None)), [],
                         "a store the next export did not carry was read as a loss")
        self.assertEqual(LR.drops_between(_blob(builds=3), _blob(builds=3)), [], "sitting still filed a drop")

    def test_the_ledgers_own_line_is_untouched(self):
        """[[copy-drift]] — one definition; the hand-made stores join it, they do not change it."""
        self.assertEqual(LR.drops_between(_blob(found=280), _blob(found=270)), [])
        self.assertEqual([d["store"] for d in LR.drops_between(_blob(found=280), _blob(found=0))], ["foundLog"])
        # a counts-only blob (board_tally's shape) carries no allStores: the hand-made stores are UNKNOWN there
        self.assertEqual(LR.drops_between({"ledger": {}, "counts": {"setPieces": 134}},
                                          {"ledger": {}, "counts": {"setPieces": 134}}), [])


class TheEpisodeNamesTheFileBeforeTheWipe(unittest.TestCase):

    def test_step_episodes_opens_one_and_recovery_closes_it(self):
        eps = []
        opened, closed = LR.step_episodes(eps, _blob(builds=3), _blob(builds="{}"),
                                          "ledger_2026-09-29_010000.json", "ledger_2026-09-29_020000.json",
                                          route_key=RK, at_ms=1000)
        self.assertEqual(len(opened), 1, "the wipe opened %d episode(s)" % len(opened))
        e = opened[0]
        self.assertEqual((e["store"], e["from"], e["to"], e["beforeFile"], e["open"]),
                         ("charBuilds", 3, 0, "ledger_2026-09-29_010000.json", True))
        self.assertEqual(closed, [])
        # sitting wiped opens nothing more; the builds coming back closes it
        o2, c2 = LR.step_episodes(eps, _blob(builds="{}"), _blob(builds="{}"), "b", "c", route_key=RK, at_ms=2000)
        self.assertEqual((o2, c2), ([], []), "sitting at zero re-filed the same fall")
        o3, c3 = LR.step_episodes(eps, _blob(builds="{}"), _blob(builds=3), "c", "d", route_key=RK, at_ms=3000)
        self.assertEqual(len(c3), 1, "the builds came back and the episode stayed open")
        self.assertFalse(eps[0]["open"])


class TheConsolesWatcherAndPruneHonourIt(unittest.TestCase):
    """The join: the SHIPPED watcher over real files in a temp dir, then the SHIPPED prune over the same dir."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="handmade-drop-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.drops = os.path.join(self.d, ".ledger_drops.json")
        self.a = self._write("ledger_2026-09-29_010000.json", _blob(builds=3), age_s=3 * 86400)
        self.b = self._write("ledger_2026-09-29_020000.json", _blob(builds="{}"), age_s=3 * 86400 - 3600)

    def _write(self, name, blob, age_s):
        p = os.path.join(self.d, name)
        with io.open(p, "w", encoding="utf-8") as fh:
            json.dump(blob, fh)
        t = time.time() - age_s
        os.utime(p, (t, t))
        return p

    def test_the_watcher_opens_the_episode_over_real_files(self):
        first = CA._ledger_drop_watch(self.a, bdir=self.d, path=self.drops, now_ms=1000)
        self.assertTrue(first.get("ok"), first)
        out = CA._ledger_drop_watch(self.b, bdir=self.d, path=self.drops, now_ms=2000)
        self.assertTrue(out.get("ok"), out)
        self.assertEqual(out["opened"], ["charBuilds 3->0 (before: ledger_2026-09-29_010000.json)"],
                         "the console's watcher did not open a charBuilds episode: %r" % out)
        self.assertEqual(out["open"], 1)
        with io.open(self.drops, encoding="utf-8") as fh:
            doc = json.load(fh)
        eps = [e for e in doc["episodes"] if e.get("store") == "charBuilds"]
        self.assertEqual(len(eps), 1)
        self.assertTrue(eps[0]["open"])
        self.assertEqual(eps[0]["beforeFile"], "ledger_2026-09-29_010000.json")
        # ── and the prune keeps that file while the episode is open, however old it is ──
        pr = CA._ledger_backup_prune(bdir=self.d, now=time.time(), drops_path=self.drops)
        self.assertIn("ledger_2026-09-29_010000.json", pr.get("dropProtected") or [],
                      "the prune does not protect the last backup before his builds were wiped: %r" % pr)
        self.assertTrue(os.path.exists(self.a), "the prune took the file the restore needs")

    def test_the_doctor_names_the_store_the_fall_and_the_file_as_the_door(self):
        CA._ledger_drop_watch(self.a, bdir=self.d, path=self.drops, now_ms=1000)
        CA._ledger_drop_watch(self.b, bdir=self.d, path=self.drops, now_ms=2000)
        state, msg = CD._check_no_ledger_store_dropped_unseen(bdir=self.d, drops_path=self.drops, now=time.time())
        self.assertEqual(state, CD.MISSING, "an open charBuilds drop graded %r: %s" % (state, msg))
        self.assertIn("charBuilds fell 3 -> 0", msg)
        self.assertIn("RESTORE charBuilds by hand", msg, "the doctor does not name the hand-made door: %s" % msg)
        self.assertIn("ledger_2026-09-29_010000.json", msg, "the doctor does not name the file to restore from")
        self.assertIn("allStores", msg, "the doctor does not say where in the file the store is")
        self.assertNotIn("ledger_restore_plan", msg,
                         "a builds-only drop sends him to the chronicle plan, which puts back none of what fell")

    def test_a_ledger_drop_beside_it_still_leads_with_its_own_door(self):
        """The hand-made door is ADDED, never a replacement: a foundLog drop keeps the chronicle plan."""
        self._write("ledger_2026-09-29_030000.json", _blob(builds="{}", found=0), age_s=60)
        CA._ledger_drop_watch(self.a, bdir=self.d, path=self.drops, now_ms=1000)
        CA._ledger_drop_watch(self.b, bdir=self.d, path=self.drops, now_ms=2000)
        CA._ledger_drop_watch(os.path.join(self.d, "ledger_2026-09-29_030000.json"), bdir=self.d, path=self.drops,
                              now_ms=3000)
        state, msg = CD._check_no_ledger_store_dropped_unseen(bdir=self.d, drops_path=self.drops, now=time.time())
        self.assertEqual(state, CD.MISSING)
        self.assertIn("ledger_restore_plan", msg, "the chronicle door is gone for a foundLog drop")
        self.assertIn("RESTORE charBuilds by hand", msg)


class TheSnapshotNoticesABuildsOnlyChange(unittest.TestCase):

    def test_hand_made_counts_change_when_only_the_builds_change(self):
        before = LR.hand_made_counts({"d2r_charBuilds": _builds(3), "d2r_foundLog": "{}"})
        after = LR.hand_made_counts({"d2r_charBuilds": "{}", "d2r_foundLog": "{}"})
        self.assertEqual(before["charBuilds"], 3)
        self.assertEqual(after["charBuilds"], 0)
        self.assertNotEqual(before, after)
        self.assertEqual(sorted(before), sorted(LR.HAND_MADE))
        self.assertEqual(LR.hand_made_counts(None), dict((s, None) for s in LR.HAND_MADE),
                         "no export read as measured zeros")

    def test_the_snapshot_writer_compares_them_beside_the_ledger_counts(self):
        """Source, bounded by the function's own end (never a byte window), against the CALL — the guard
        `_LEDGER_BACKUP_STATE.get("handMade") == _hm` cannot appear in prose by accident.
        [[source-reading-guard]]"""
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        i = src.index("def _ledger_snapshot_once(")
        body = src[i:src.index("\ndef ", i + 10)]
        code = "\n".join(l.split("#", 1)[0] for l in body.split("\n"))
        self.assertIn('_LEDGER_BACKUP_STATE.get("handMade") == _hm', code,
                      "the snapshot writer decides 'unchanged' on the ledger counts alone, so a builds-only "
                      "wipe never produces the snapshot the watcher judges")
        self.assertIn("hand_made_counts(got.get(\"fullStores\"))", code,
                      "the hand-made counts are not taken off the board's export")
        self.assertIn('_LEDGER_BACKUP_STATE["handMade"] = _hm', code,
                      "the hand-made counts are compared but never remembered, so every snapshot reads as changed")


RED_PROOF = [
    {
        "why": "REG-1481 — charBuilds leaves the watched set: wiping his builds opens no episode, raises nothing, "
               "and the prune can take the last file that held them — the exact gap #41 rank 5 measured",
        "file": "ledger_restore.py",
        "find": 'HAND_MADE = ("charBuilds", "muleEquip", "muleAssign")',
        "replace": 'HAND_MADE = ("muleEquip", "muleAssign")',
        "matches": 1,
    },
    {
        "why": "REG-1481 — the drop pass loops the ledger stores only again; the hand-made stores are declared, "
               "counted, and never judged",
        "file": "ledger_restore.py",
        "find": "    for store in BACKED_UP + HAND_MADE:\n",
        "replace": "    for store in BACKED_UP:\n",
        "matches": 1,
    },
    {
        "why": "REG-1481 — an absent hand-made store is read as a measured ZERO: every snapshot whose export "
               "skipped a key files a wipe he never had",
        "file": "ledger_restore.py",
        "find": "    raw = al.get(\"d2r_\" + store)\n    if raw is None:\n        return None\n",
        "replace": "    raw = al.get(\"d2r_\" + store)\n    if raw is None:\n        return 0\n",
        "matches": 1,
    },
    {
        "why": "REG-1481 — the snapshot writer compares the ledger counts alone again: a builds-only wipe never "
               "produces the snapshot the watcher judges",
        "file": "control_app.py",
        "find": ' and _LEDGER_BACKUP_STATE.get("handMade") == _hm:\n',
        "replace": ":\n",
        "matches": 1,
    },
    {
        "why": "REG-1481 — the doctor sends a hand-made drop to the chronicle plan and names no door for it",
        "file": "console_doctor.py",
        "find": "        _hand = [e for e in open_eps if e.get(\"store\") in _LR.HAND_MADE]\n",
        "replace": "        _hand = []\n",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
