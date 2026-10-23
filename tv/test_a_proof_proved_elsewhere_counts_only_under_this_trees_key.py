# -*- coding: utf-8 -*-
"""REG-2630 — A PROOF PROVED ELSEWHERE COUNTS HERE ONLY UNDER THE KEY THIS CHECKOUT'S BYTES GIVE IT.

⚠ WHAT IT IS FOR. A push that touches bible.html or control_app.py re-proves thousands of red-proofs in the Mac's
pre-push hook. The box (or the 16-shard census) can prove the SAME commit first; `heart2 --export-proved DIR` writes
those PROVENs with an `export` manifest, the file is copied to the Mac, and `heart2 --import-proved FILE...` banks them
in the Mac's verdict cache - the cache the hook reads - so the push serves them instead of proving them again.

⚠ THE DEFECTS THIS GUARDS, each one a verdict served that nobody earned on these bytes:
  · an imported entry is banked under the key the FILE claims instead of the key THIS checkout computes - a box that
    proved other bytes (or a tampered file) would then be served for the Mac's bytes. The tamper case drives the REAL
    keyer over a real gate of this repo: the entry filed under the true key is served by peek(), the one filed under a
    key one byte off is dropped, named, and never served;
  · a file of another HEAD (proved before the version bump), from a dirty tree, an unfinished shard, a file with no
    manifest or with both, or an import into a checkout whose tracked files differ from HEAD;
  · an ELSEWHERE / BLIND / undated / fact-bound entry is banked - peek() would refuse to serve it;
  · the import rewrites `tree` - then REG-2599's clean run here, owed to every gate whose law the push changes, is
    skipped for a law whose clean run only ever happened on another machine;
  · the export ships entries its own bytes no longer key (stale proofs of older bytes) or entries nobody may serve,
    exports from a dirty tree, or merges into an older export.
Every store here is a temp file; HEAD is a stand-in except where the real keyer is named. RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402  (it prints non-ASCII)
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2        # noqa: E402
import proof_shard   # noqa: E402

RED_PROOF = [
    {
        "why": "REG-2630 - the import banks each entry under the key the FILE claims, never asking this checkout's bytes",
        "file": "heart2.py",
        "find": "_PS.select(sets, keyer=_shard_keyer(target), dropped=_gone,",
        "replace": "_PS.select(sets, keyer=None, dropped=_gone,",
        "matches": 1,
    },
    {
        "why": "REG-2630 - a file keyed at another HEAD (proved before the bump) is imported",
        "file": "proof_shard.py",
        "find": "        if not head or head != m.get(\"head\"):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-2630 - a file proved on a tree whose tracked files differed from its HEAD is imported",
        "file": "proof_shard.py",
        "find": "        if not (m.get(\"dirty\") is False):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-2630 - an unfinished census shard is imported as proved",
        "file": "proof_shard.py",
        "find": "            done = sh.get(\"finished\") is True\n",
        "replace": "            done = True\n",
        "matches": 1,
    },
    {
        "why": "REG-2630 - an import into a checkout whose tracked files differ from HEAD keys proofs by bytes no commit has",
        "file": "heart2.py",
        "find": "        if not ok_d or dirty.strip():       # REG-2630 - the importing checkout",
        "replace": "        if False:       # REG-2630 - the importing checkout",
        "matches": 1,
    },
    {
        "why": "REG-2630 - the import drops entries silently: nobody learns which laws' keys differ",
        "file": "heart2.py",
        "find": "    if _gone:\n        _dg = {}\n",
        "replace": "    if False:\n        _dg = {}\n",
        "matches": 1,
    },
    {
        "why": "REG-2630 - the export ships proofs its own bytes no longer key (stale proofs of older bytes)",
        "file": "heart2.py",
        "find": "        if keyer(str(e.get(\"gate\")), e.get(\"proof\")) != key:\n            stale += 1\n",
        "replace": "        if False:\n            stale += 1\n",
        "matches": 1,
    },
    {
        "why": "REG-2630 - the export ships entries peek() would never serve (ELSEWHERE, BLIND, undated)",
        "file": "heart2.py",
        "find": "        if not _PS.servable(e):\n            other += 1\n",
        "replace": "        if False:\n            other += 1\n",
        "matches": 1,
    },
    {
        "why": "REG-2630 - the export is written from a tree whose tracked files differ from HEAD",
        "file": "heart2.py",
        "find": "    elif not ok_d or dirty.strip():\n        why = ",
        "replace": "    elif False:\n        why = ",
        "matches": 1,
    },
    {
        "why": "REG-2630 - an export merges into an older one instead of refusing",
        "file": "heart2.py",
        "find": "    elif os.path.exists(out):\n",
        "replace": "    elif False:\n",
        "matches": 1,
    },
    {
        "why": "REG-2630 r1 - a file that claims an entry was proved in THIS tree is believed, so REG-2599 owes no clean run",
        "file": "proof_shard.py",
        "find": "                e[\"tree\"] = FOREIGN_TREE",
        "replace": "                pass",
        "matches": 1,
    },
    {
        "why": "REG-2630 r2 - a shard plan row whose index is a list reaches a set and the import tracebacks",
        "file": "proof_shard.py",
        "find": "            if type(row[1]) is not int:\n                return None\n",
        "replace": "            if False:\n                return None\n",
        "matches": 1,
    },
    {
        "why": "REG-2630 r1 - a proof index that is a list reaches a set lookup and the import tracebacks",
        "file": "proof_shard.py",
        "find": "            if type(e.get(\"proof\")) is not int:\n",
        "replace": "            if False:\n",
        "matches": 1,
    },
]

HEAD = "1234567890abcdef1234567890abcdef12345678"
BOX_TREE = "/box/repo"
REAL_GATE = "test_a_version_bump_keeps_the_proofs_of_laws_that_never_read_the_version"


def _e(gate, proof, verdict="PROVEN", at=1761200000000, **extra):
    e = {"verdict": verdict, "gate": gate, "proof": proof, "why": "w", "tree": BOX_TREE}
    if at is not None:
        e["provedAt"] = at
    e.update(extra)
    return e


class _Fixture(unittest.TestCase):
    REAL_KEYER = False

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="provedimport-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.target = os.path.join(self.tmp, "home", os.path.basename(heart2.CACHE))
        os.makedirs(os.path.dirname(self.target))
        self.said = []
        self.dirty = ""
        self.head = HEAD
        p = mock.patch.object(heart2, "_git", side_effect=lambda *a: (True, self.head + "\n") if a[0] == "rev-parse"
                              else (True, self.dirty))
        p.start()
        self.addCleanup(p.stop)
        self.keys = {}
        if not self.REAL_KEYER:
            p = mock.patch.object(heart2, "_shard_keyer", return_value=lambda g, i: self.keys.get((g, i)))
            p.start()
            self.addCleanup(p.stop)

    def export_file(self, entries, name="box", **m):
        d = os.path.join(self.tmp, name)
        os.makedirs(d)
        path = os.path.join(d, os.path.basename(heart2.CACHE))
        for key, e in entries.items():
            if type(e["proof"]) is int:
                self.keys.setdefault((e["gate"], e["proof"]), key)
        man = proof_shard.export_manifest(HEAD, False, len(entries), 1761200000000)
        man.update(m)
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"format": 2, "entries": entries, "export": man}))
        return path

    def shard_file(self, k, n, entries, assigned=None, **m):
        d = os.path.join(self.tmp, "shard-%d" % k)
        os.makedirs(d)
        path = os.path.join(d, os.path.basename(heart2.CACHE))
        for key, e in entries.items():
            self.keys.setdefault((e["gate"], e["proof"]), key)
        own = {}
        for g, i in (assigned if assigned is not None else [(e["gate"], e["proof"]) for e in entries.values()]):
            own.setdefault(g, set()).add(i)
        man = proof_shard.manifest(k, n, HEAD, False, "plan-1", own, None, [], 1761200000000)
        man.update(m)
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"format": 2, "entries": entries, "shard": man}))
        return path

    def run_import(self, paths):
        return heart2.import_proved(paths, say=self.said.append, target=self.target)

    def home(self):
        if not os.path.exists(self.target):
            return None
        with io.open(self.target, encoding="utf-8") as fh:
            return json.load(fh)

    def assertRefused(self, paths, word):
        before = self.home()
        self.assertEqual(self.run_import(paths), 2, self.said)
        self.assertEqual(self.home(), before, "a refused import wrote")
        self.assertIn(word, " ".join(str(x) for x in self.said))


class ABoxExportComesHome(_Fixture):
    def test_every_proven_is_banked_with_the_tree_it_was_proved_in(self):
        p = self.export_file({"k1": _e("g1", 0), "k2": _e("g1", 1), "k3": _e("g2", 0)})
        self.assertEqual(self.run_import([p]), 0, self.said)
        ent = self.home()["entries"]
        self.assertEqual(sorted(ent), ["k1", "k2", "k3"])
        for k, e in ent.items():
            self.assertEqual(e["tree"], BOX_TREE, "%s: the import rewrote the tree it was proved in" % k)
        self.assertIn("3 PROVEN entr(ies) banked", " ".join(self.said))

    def test_an_entry_filed_under_a_key_these_bytes_do_not_give_it_is_dropped_and_named(self):
        """THE TAMPER: the box proved g1[1] over other bytes (or the file was edited) - its key is not this tree's"""
        p = self.export_file({"k1": _e("g1", 0), "k2": _e("g1", 1), "k3": _e("g2", 0)})
        self.keys[("g1", 1)] = "the-key-this-tree-gives"
        self.assertEqual(self.run_import([p]), 0, self.said)
        ent = self.home()["entries"]
        self.assertEqual(sorted(ent), ["k1", "k3"], "a mismatched entry was banked")
        self.assertNotIn("the-key-this-tree-gives", ent, "the import re-filed a foreign proof under this tree's key")
        text = " ".join(self.said)
        self.assertIn("1 DROPPED", text)
        self.assertIn("g1 [1]", text)

    def test_an_entry_this_tree_cannot_key_is_dropped(self):
        p = self.export_file({"k1": _e("g1", 0), "k3": _e("g2", 0)})
        self.keys[("g2", 0)] = None
        self.assertEqual(self.run_import([p]), 0, self.said)
        self.assertEqual(sorted(self.home()["entries"]), ["k1"])

    def test_what_peek_would_refuse_is_never_banked(self):
        p = self.export_file({"ok": _e("g", 0), "else": _e("g", 1, verdict="ELSEWHERE"),
                              "blind": _e("g", 2, verdict="BLIND"), "undated": _e("g", 4, at=None),
                              "traced": _e("g", 5, kind="traced"), "facts": _e("g", 6, factsRef="x")})
        self.assertEqual(self.run_import([p]), 0, self.said)
        self.assertEqual(sorted(self.home()["entries"]), ["ok"])

    def test_what_this_machine_already_serves_is_kept(self):
        with io.open(self.target, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"format": 2, "entries": {"k1": dict(_e("g1", 0, at=1700000000000), tree="/here")}}))
        p = self.export_file({"k1": _e("g1", 0), "k2": _e("g1", 1)})
        self.assertEqual(self.run_import([p]), 0, self.said)
        ent = self.home()["entries"]
        self.assertEqual(ent["k1"]["tree"], "/here")
        self.assertIn("k2", ent)

    def test_a_partial_census_set_is_taken_entry_by_entry(self):
        """unlike --import-shards, one shard of 16 is enough: every entry is still keyed here"""
        a = self.shard_file(3, 16, {"k1": _e("g1", 0)})
        self.assertEqual(self.run_import([a]), 0, self.said)
        self.assertEqual(sorted(self.home()["entries"]), ["k1"])

    def test_a_box_export_and_a_census_shard_together(self):
        a = self.shard_file(1, 16, {"k1": _e("g1", 0)})
        b = self.export_file({"k2": _e("g2", 0)})
        self.assertEqual(self.run_import([a, b]), 0, self.said)
        self.assertEqual(sorted(self.home()["entries"]), ["k1", "k2"])


    def test_a_file_that_claims_this_trees_own_id_is_banked_as_foreign(self):
        """r1: `tree` is the file's word. Only this tree may say a proof ran here, or REG-2599 skips its clean run"""
        p = self.export_file({"k1": dict(_e("g1", 0), tree=heart2.TREE_ID), "k2": _e("g1", 1)})
        self.assertEqual(self.run_import([p]), 0, self.said)
        ent = self.home()["entries"]
        self.assertEqual(ent["k1"]["tree"], proof_shard.FOREIGN_TREE)
        self.assertNotEqual(ent["k1"]["tree"], heart2.TREE_ID)
        self.assertEqual(ent["k2"]["tree"], BOX_TREE, "an honest foreign tree was rewritten")


class AForeignOrUntrustedFileIsRefused(_Fixture):
    def test_an_export_of_another_head(self):
        self.assertRefused([self.export_file({"k1": _e("g1", 0)}, head="f" * 40)], "keyed at")

    def test_an_export_from_a_dirty_tree(self):
        self.assertRefused([self.export_file({"k1": _e("g1", 0)}, dirty=True)], "differed")

    def test_an_export_of_another_manifest_version(self):
        self.assertRefused([self.export_file({"k1": _e("g1", 0)}, v=99)], "another version")

    def test_a_shard_that_never_finished(self):
        self.assertRefused([self.shard_file(1, 2, {"k1": _e("g1", 0)}, finished=False)], "never finished")

    def test_a_shard_entry_outside_its_plan(self):
        a = self.shard_file(1, 2, {"k1": _e("g1", 0), "k9": _e("g9", 4)}, assigned=[("g1", 0)])
        self.assertRefused([a], "never gave")

    def test_a_file_with_no_manifest(self):
        p = os.path.join(self.tmp, os.path.basename(heart2.CACHE))
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"format": 2, "entries": {"k": _e("g", 0)}}))
        self.assertRefused([p], "no export or shard manifest")

    def test_a_file_with_both_manifests(self):
        p = self.export_file({"k1": _e("g1", 0)})
        with io.open(p, encoding="utf-8") as fh:
            body = json.load(fh)
        body["shard"] = proof_shard.manifest(1, 1, HEAD, False, "p", {"g1": {0}}, None, [], 1)
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(body))
        self.assertRefused([p], "no export or shard manifest")

    def test_into_a_checkout_whose_files_differ_from_head(self):
        p = self.export_file({"k1": _e("g1", 0)})
        self.dirty = " M tv/heart2.py\n"
        self.assertRefused([p], "differ from its HEAD")

    def test_a_head_nobody_can_read(self):
        p = self.export_file({"k1": _e("g1", 0)})
        with mock.patch.object(heart2, "_git", return_value=(False, "")):
            self.assertRefused([p], "UNKNOWN")

    def test_no_file(self):
        self.assertRefused([], "no file")

    def test_a_plan_row_whose_index_is_not_a_whole_number(self):
        """r2: a list index in a shard's `assigned` rows used to raise TypeError while the plan was read - on both paths"""
        a = self.shard_file(1, 1, {"k1": _e("g1", 0)})
        with io.open(a, encoding="utf-8") as fh:
            body = json.load(fh)
        for bad in ([0], {"i": 0}, "0", True):
            body["shard"]["assigned"] = [["g1", 0], ["g1", bad]]
            with io.open(a, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(body))
            self.said[:] = []
            self.assertRefused([a], "not a whole number")
            self.said[:] = []
            self.assertEqual(heart2.import_shards([a], say=self.said.append, target=self.target), 2, self.said)
            self.assertIn("not a whole number", " ".join(self.said))
            self.assertIsNone(self.home(), "a refused import wrote")

    def test_a_claimed_here_entry_still_counts_as_banked_for_a_stopped_shard(self):
        """r2: the tree rewrite must not hide a banked proof from unbanked() (it asks `take.get(key) is e`)"""
        a = self.shard_file(1, 1, {"k1": dict(_e("g1", 0), tree=heart2.TREE_ID)}, assigned=[("g1", 0), ("g1", 1)])
        with io.open(a, encoding="utf-8") as fh:
            body = json.load(fh)
        ok, why, sets = proof_shard.check_proved([("s1", body, None)], HEAD)
        self.assertTrue(ok, why)
        ok, why, take, _sk = proof_shard.select(sets, keyer=lambda g, i: self.keys.get((g, i)), here=heart2.TREE_ID)
        self.assertTrue(ok, why)
        self.assertEqual(take["k1"]["tree"], proof_shard.FOREIGN_TREE)
        self.assertEqual(proof_shard.unbanked(sets, take), {1: (1, 2)})

    def test_a_proof_index_that_is_not_a_whole_number(self):
        """r1: a list or dict index used to raise TypeError mid-import; a bool or text one names no proof either"""
        for i, bad in enumerate(([0], {"i": 0}, True, "0")):
            p = self.export_file({"k1": _e("g1", 0), "k2": _e("g1", bad)}, name="bad%d" % i)
            self.assertRefused([p], "not a whole number")


class TheExportShipsOnlyWhatItsBytesKey(_Fixture):
    def source(self, entries):
        p = os.path.join(self.tmp, "src", os.path.basename(heart2.CACHE))
        os.makedirs(os.path.dirname(p))
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"format": 2, "entries": entries}))
        return p

    def export(self, src, out=None):
        return heart2.export_proved(out or os.path.join(self.tmp, "out"), say=self.said.append, source=src)

    def written(self, out=None):
        with io.open(os.path.join(out or os.path.join(self.tmp, "out"), os.path.basename(heart2.CACHE)),
                     encoding="utf-8") as fh:
            return json.load(fh)

    def test_only_servable_entries_these_bytes_key_leave(self):
        self.keys.update({("g1", 0): "k1", ("g1", 1): "now", ("g2", 0): "k3"})
        src = self.source({"k1": _e("g1", 0), "old": _e("g1", 1), "k3": _e("g2", 0),
                           "blind": _e("g2", 1, verdict="BLIND")})
        self.assertEqual(self.export(src), 0, self.said)
        body = self.written()
        self.assertEqual(sorted(body["entries"]), ["k1", "k3"])
        self.assertEqual(body["export"]["head"], HEAD)
        self.assertIs(body["export"]["dirty"], False)
        self.assertEqual(body["export"]["entries"], 2)
        self.assertIn("1 banked over other bytes and 1 not servable", " ".join(self.said))

    def test_the_export_round_trips_into_an_import(self):
        self.keys.update({("g1", 0): "k1"})
        src = self.source({"k1": _e("g1", 0)})
        self.assertEqual(self.export(src), 0, self.said)
        out = os.path.join(self.tmp, "out", os.path.basename(heart2.CACHE))
        self.assertEqual(self.run_import([out]), 0, self.said)
        self.assertEqual(sorted(self.home()["entries"]), ["k1"])

    def test_a_dirty_tree_exports_nothing(self):
        src = self.source({"k1": _e("g1", 0)})
        self.dirty = " M bible.html\n"
        self.assertEqual(self.export(src), 2)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "out")))

    def test_an_older_export_is_never_merged_into(self):
        self.keys.update({("g1", 0): "k1", ("g2", 0): "k2"})
        self.assertEqual(self.export(self.source({"k1": _e("g1", 0)})), 0, self.said)
        os.rename(os.path.join(self.tmp, "src"), os.path.join(self.tmp, "src1"))
        self.assertEqual(self.export(self.source({"k2": _e("g2", 0)})), 2, self.said)
        self.assertEqual(sorted(self.written()["entries"]), ["k1"])


class TheRealKeyerDecides(_Fixture):
    """No stand-in keyer: the key of a real gate of this checkout, computed by heart2's own keyer (the one the hook's
    cache uses). The import must serve the entry filed under that key and never the one filed one byte off."""
    REAL_KEYER = True

    def real_key(self, idx):
        k = heart2._shard_keyer(self.target)(REAL_GATE, idx)
        self.assertTrue(k, "the real keyer gave %s[%d] no key - this case would measure nothing" % (REAL_GATE, idx))
        return k

    def test_the_true_key_is_served_and_a_tampered_one_never_is(self):
        k0, k1 = self.real_key(0), self.real_key(1)
        off = ("0" if k1[0] != "0" else "1") + k1[1:]          # the box's key for other bytes: one character off
        p = self.export_file({k0: _e(REAL_GATE, 0), off: _e(REAL_GATE, 1)})
        self.assertEqual(self.run_import([p]), 0, self.said)
        cache = heart2._VerdictCache(path=self.target, say=lambda *a, **k: None)
        self.assertIsNotNone(cache.peek(k0), "the entry filed under this tree's own key is not served")
        self.assertIsNone(cache.peek(k1), "a proof keyed over other bytes is served for this tree's bytes")
        self.assertIsNone(cache.peek(off), "a key this tree never computes was banked")
        self.assertIn("%s [1]" % REAL_GATE, " ".join(self.said))

    def test_a_proof_filed_under_another_proofs_key_is_dropped(self):
        """an entry for proof 1 filed under proof 0's real key: the key is real, but not THIS proof's"""
        k0 = self.real_key(0)
        p = self.export_file({k0: _e(REAL_GATE, 1)})
        self.assertEqual(self.run_import([p]), 0, self.said)
        self.assertEqual((self.home() or {}).get("entries", {}), {})


if __name__ == "__main__":
    unittest.main()
