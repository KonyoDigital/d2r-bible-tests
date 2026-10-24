# -*- coding: utf-8 -*-
"""REG-2632 - A PROOF COUNTS ONLY ON THE PLATFORM CLASS IT WAS PROVED ON, AND A PC SERVES ONLY WHAT ITS BANK KEYS EXACTLY.

⚠ WHAT IT IS FOR. REG-2630 let a machine bank proofs proved elsewhere under the key ITS bytes give them. The key had no
platform in it, so a PROVEN from the Linux box or census was served on the Mac, and would have been on a Windows PC. The
laws read sys.platform, os.name, subprocess, signal: asked over all 5680 proofs (2026-10-24), not one law's python
closure is free of a platform read, so "platform-neutral by law" is an empty set and a cross-class serve is a guess.
The class ("linux", "darwin", "windows", "other:<platform>") is now folded into every key: another class's proof cannot
meet this machine's key, whatever its file says.

⚠ THE FLEET. A PC (Dean's, the ALT) fetches `proof-bank:<HEAD>.<class>.json` with its update credentials and runs its
slice with `--bank FILE`: every gate the bank serves WHOLE under the PC's own keys is served, the rest is proved. The ALT
never proves beside his game (REG-1502); there the lane starts a BANK-ONLY run, which serves and never proves, and what
the bank does not serve stays owed - so the reel deleter stays shut for it.

⚠ BYTES, NOT LINES. A CRLF checkout is keyed raw: its CRLF twin of an LF file is a different key (a law reading bytes
can behave differently on it). Separators are not bytes: a Windows path and a POSIX path of the same input key alike.

THE DEFECTS THIS GUARDS (RED_PROOF below): the platform left out of the key; Windows read as Linux; the key's input
names spelled with the native separator; a gate served from a bank with one proof missing; bank-only proving the rest;
a bank-only run started with no bank, or ended by his game; an exported bank carrying the proving machine's path.
"""
import io
import ntpath
import os
import posixpath
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402
import self_prove as SP  # noqa: E402

RED_PROOF = [
    {"why": "REG-2632 - the platform class leaves the key, so a Linux PROVEN is served on a Mac or a PC",
     "file": "heart2.py",
     "find": '        h.update(b"REG-2632 platform\\0" + str(PLATFORM_CLASS).encode("utf-8", "replace") + b"\\0")   # PLATFORM-IN-KEY\n',
     "replace": "", "matches": 1},
    {"why": "REG-2632 - Windows is read as another class (its os.name ignored)",
     "file": "heart2.py",
     "find": '    if osname == "nt" or plat.startswith(("win", "cygwin", "msys")):\n',
     "replace": '    if plat.startswith(("cygwin", "msys")):\n', "matches": 1},
    {"why": "REG-2632 - a key's input names keep the native separator, so a Windows tree never meets a POSIX one",
     "file": "heart2.py",
     "find": '    return pm.relpath(path, repo).replace(pm.sep, "/")\n',
     "replace": "    return pm.relpath(path, repo)\n", "matches": 1},
    {"why": "REG-2632 - a gate is served from the bank with a proof that missed",
     "file": "heart2.py",
     "find": "        if prs and len(hits) == len(prs):\n",
     "replace": "        if prs and hits:\n", "matches": 1},
    {"why": "REG-2632 - bank-only proves what the bank did not serve (beside his game)",
     "file": "heart2.py",
     "find": "    return served, ([] if only else rest), ages\n",
     "replace": "    return served, rest, ages\n", "matches": 1},
    {"why": "REG-2632 - beside his game a bank-only run starts with no bank to serve from",
     "file": "self_prove.py",
     "find": "        if bank and _bf is not None and _bf == _bf and _bf >= BANK_ONLY_MIN_FREE_MB:\n",
     "replace": "        if _bf is not None and _bf == _bf and _bf >= BANK_ONLY_MIN_FREE_MB:\n", "matches": 1},
    {"why": "REG-2632 - his game ends a bank-only run that proves nothing (the guard's fast stand-aside)",
     "file": "self_prove.py",
     "find": '        aside, _why = stand_aside(False if mem.get("bankOnly") else play_now, free_now)\n',
     "replace": "        aside, _why = stand_aside(play_now, free_now)\n", "matches": 1},
    {"why": "REG-2632 - an exported bank carries the proving machine's own path",
     "file": "heart2.py",
     "find": '        e["tree"] = export_tree(e.get("tree"))    # REG-2632 - a bank is published: no machine path leaves this machine\n',
     "replace": "", "matches": 1},
]

_LAW = "import unittest\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        pass\n"


class _Tree(object):
    def __init__(self, subject=b"all fine here\n"):
        self.root = tempfile.mkdtemp(prefix="plat.")
        self.tv = os.path.join(self.root, "repo", "tv")
        os.makedirs(self.tv)
        for rel, data in (("control_app.py", b"# marker\n"), ("t_plat.py", _LAW.encode()), ("subject.txt", subject)):
            with open(os.path.join(self.tv, rel), "wb") as fh:
                fh.write(data)

    def key(self, cls, subject=None):
        if subject is not None:
            with open(os.path.join(self.tv, "subject.txt"), "wb") as fh:
                fh.write(subject)
        c = H._VerdictCache(path=os.path.join(self.root, ".heart2_cache.json"), say=lambda *a, **k: None)
        with mock.patch.object(H, "PLATFORM_CLASS", cls):
            return c.key_for(self.tv, "t_plat", "t_plat.py", {"file": "subject.txt", "find": "fine", "replace": "x"})[0]

    def gone(self):
        shutil.rmtree(self.root, ignore_errors=True)


class TheClass(unittest.TestCase):

    def test_each_platform_names_its_class(self):
        self.assertEqual(H.platform_class("win32", "nt"), "windows")
        self.assertEqual(H.platform_class("linux", "nt"), "windows", "os.name nt is Windows whatever sys.platform says")
        self.assertEqual(H.platform_class("darwin", "posix"), "darwin")
        self.assertEqual(H.platform_class("linux", "posix"), "linux")
        self.assertEqual(H.platform_class("freebsd13", "posix"), "other:freebsd13")

    def test_the_same_bytes_key_apart_on_each_class_and_alike_on_one(self):
        t = _Tree()
        try:
            ks = dict((c, t.key(c)) for c in ("linux", "darwin", "windows"))
            self.assertTrue(all(ks.values()), ks)
            self.assertEqual(len(set(ks.values())), 3, "two classes gave one key: %s" % ks)
            self.assertEqual(t.key("darwin"), ks["darwin"], "one class, one tree, two keys")
        finally:
            t.gone()

    def test_a_linux_proven_is_never_served_on_another_class(self):
        t = _Tree()
        try:
            c = H._VerdictCache(path=os.path.join(t.root, ".heart2_cache.json"), say=lambda *a, **k: None)
            lk = t.key("linux")
            c.entries[lk] = {"verdict": H.PROVEN, "provedAt": 1, "gate": "t_plat", "proof": 0, "tree": "/elsewhere"}
            self.assertIsNotNone(c.peek(lk), "BASELINE: the Linux key serves on Linux")
            for cls in ("darwin", "windows"):
                self.assertIsNone(c.peek(t.key(cls)), "a Linux PROVEN was served on %s" % cls)
        finally:
            t.gone()


class TheBytes(unittest.TestCase):

    def test_a_crlf_twin_keys_apart_and_one_byte_moves_the_key(self):
        t = _Tree()
        try:
            lf = t.key("windows", b"all fine here\nline two\n")
            crlf = t.key("windows", b"all fine here\r\nline two\r\n")
            self.assertNotEqual(lf, crlf, "a CRLF twin served the LF tree's proof: the key must be over raw bytes")
            self.assertEqual(t.key("windows", b"all fine here\r\nline two\r\n"), crlf)
            self.assertNotEqual(t.key("windows", b"all fine here\r\nline twO\r\n"), crlf, "one byte changed, one key")
        finally:
            t.gone()

    def test_a_windows_path_and_a_posix_path_name_an_input_alike(self):
        w = H.key_rel("C:\\pc\\d2r\\tv\\gate_ledger.py", "C:\\pc\\d2r", pathmod=ntpath)
        p = H.key_rel("/home/x/d2r/tv/gate_ledger.py", "/home/x/d2r", pathmod=posixpath)
        self.assertEqual(w, "tv/gate_ledger.py")
        self.assertEqual(w, p)


class _StubCache(object):
    def __init__(self, keys, entries):
        self.keys, self.entries = keys, entries

    def key_for(self, sandbox, name, filename, pr):
        k = self.keys.get((name, pr["i"]))
        if k == "raise":
            raise RuntimeError("boom")
        return k, [], None

    def peek(self, key):
        return self.entries.get(key)


def _have():
    return [("g_all", "g_all.py", [{"i": 0}, {"i": 1}]), ("g_one_miss", "g_one_miss.py", [{"i": 0}, {"i": 1}]),
            ("g_raise", "g_raise.py", [{"i": 0}])]


def _cache():
    ok = {"verdict": H.PROVEN, "provedAt": 5}
    keys = {("g_all", 0): "a0", ("g_all", 1): "a1", ("g_one_miss", 0): "m0", ("g_one_miss", 1): "m1-tampered",
            ("g_raise", 0): "raise"}
    return _StubCache(keys, {"a0": ok, "a1": dict(ok, provedAt=3), "m0": ok, "m1": ok})


class TheBank(unittest.TestCase):

    def test_a_gate_is_served_only_whole(self):
        served, rest, ages = H.serve_from_bank(_have(), lambda *a: None, _cache())
        self.assertEqual(sorted(served), ["g_all"])
        self.assertEqual(served["g_all"][0], H.PROVEN)
        self.assertEqual(ages["g_all"], 3, "the census keeps the OLDEST measured age")
        self.assertEqual(sorted(n for n, _f, _p in rest), ["g_one_miss", "g_raise"])

    def test_bank_only_leaves_the_rest_owed_and_never_proves_it(self):
        served, rest, _ages = H.serve_from_bank(_have(), lambda *a: None, _cache(), only=True)
        self.assertEqual(sorted(served), ["g_all"])
        self.assertEqual(rest, [], "bank-only handed gates on to be proved")

    def test_a_bank_only_slice_never_runs_a_proof(self):
        boom = mock.Mock(side_effect=AssertionError("a bank-only slice ran a proof"))
        gate = next(iter(H.gate_files(say=lambda *a, **k: None)))
        with mock.patch.object(H, "_prove_gates", boom), \
                mock.patch.object(H, "serve_from_bank", lambda have, say, c, only=False: ({}, [] if only else have, {})), \
                mock.patch.object(H, "_write_state", mock.Mock()) as ws, \
                mock.patch.dict(H._BANK, {"on": True, "only": True}):
            out = H.prove(only={gate[0]}, say=lambda *a, **k: None, stamp=False)
        self.assertEqual(out, {})
        boom.assert_not_called()
        ws.assert_not_called()

    def test_the_bank_flags_refuse_any_other_run(self):
        with mock.patch("builtins.print"):
            self.assertEqual(H.main(["--prove", "x", "--slice", "--bank-only"]), 2)
            self.assertEqual(H.main(["--prove", "x", "--bank", "f.json"]), 2)
            self.assertEqual(H.main(["--prove", "x", "--slice", "--push", "--bank", "f.json"]), 2)

    def test_an_export_names_no_machine_path(self):
        self.assertTrue(H.export_tree("/srv/someone/d2r").startswith("exported:"))
        self.assertNotIn("someone", H.export_tree("/srv/someone/d2r"))
        self.assertNotEqual(H.export_tree(H.TREE_ID), H.TREE_ID)
        ent = {"k1": {"verdict": H.PROVEN, "provedAt": 7, "gate": "g", "proof": 0, "tree": "/srv/someone/d2r"}}
        take, stale, other = H.export_take(ent, lambda g, i: "k1")
        self.assertEqual((sorted(take), stale, other), (["k1"], 0, 0))
        self.assertNotIn("someone", repr(take), "an export carried the proving machine's path")
        self.assertEqual(ent["k1"]["tree"], "/srv/someone/d2r", "the export rewrote this machine's own store")


class TheLane(unittest.TestCase):
    CENSUS = {"state": "stale", "why": "s", "fingerprint": "f", "owedGates": [["g", 1]]}

    def ask(self, playing, free, bank):
        return SP.decide(self.CENSUS, ("installed", ""), None, 1.0, {}, 1000.0, playing=playing, free=free, bank=bank)

    def test_beside_his_game_only_a_bank_starts_and_only_bank_only(self):
        d = self.ask(True, 2000, "/b.json")
        self.assertTrue(d["start"] and d.get("bankOnly"), d)
        for free in (None, 100, "junk", float("nan")):
            self.assertFalse(self.ask(True, free, "/b.json")["start"], "bank-only started on free=%r" % (free,))
        d = self.ask(True, 4000, None)
        self.assertFalse(d["start"], "beside his game with no bank something started: %s" % d)
        self.assertEqual(d["key"], "playing")

    def test_off_his_game_a_bank_never_makes_the_run_bank_only(self):
        d = self.ask(False, 4000, "/b.json")
        self.assertTrue(d["start"])
        self.assertFalse(d.get("bankOnly"), "Dean's idle PC would never prove the rest")

    def test_the_spawned_command_carries_the_bank_only_on_a_slice(self):
        seen = []

        class P(object):
            pid = 4242

        def pop(cmd, **kw):
            seen.append(cmd)
            return P()
        d = tempfile.mkdtemp(prefix="plat.")
        try:
            log = os.path.join(d, "l.log")
            SP.spawn(log, workers=1, popen=pop, names=["g"], bank="/b.json", bank_only=True)
            SP.spawn(log, workers=1, popen=pop, names=None, bank="/b.json", bank_only=True)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        self.assertEqual(seen[0][-3:], ["--bank", "/b.json", "--bank-only"])
        self.assertNotIn("--bank", seen[1], "a whole-census run took a bank (heart2 refuses it)")

    def test_his_game_never_ends_a_bank_only_run_but_memory_does(self):
        d = tempfile.mkdtemp(prefix="plat.")
        try:
            path = os.path.join(d, "sp.json")
            SP.save({"pid": 4242, "pidBirth": 1, "bankOnly": True}, path)
            ticks = []
            with mock.patch.object(SP, "identity", lambda pid, birth: True):
                got = SP.guard(path=path, playing=True, free=4000, _tick=lambda **k: ticks.append(k) or {"key": "t"})
                self.assertIsNone(got, "his game ended a bank-only run")
                got = SP.guard(path=path, playing=True, free=10, _tick=lambda **k: ticks.append(k) or {"key": "t"})
                self.assertEqual(got, {"key": "t"}, "a bank-only run kept memory he needs")
                SP.save({"pid": 4242, "pidBirth": 1}, path)
                got = SP.guard(path=path, playing=True, free=4000, _tick=lambda **k: ticks.append(k) or {"key": "t"})
                self.assertEqual(got, {"key": "t"}, "BASELINE: his game ends a real prover")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_a_bank_is_fetched_for_this_head_and_this_class_only(self):
        head = "a" * 40
        asked = []

        def git(*a, **k):
            asked.append(a)
            if a[0] == "rev-parse":
                return 0, head
            if a[0] == "fetch":
                return 1, ""
            if a[0] == "show":
                return (0, '{"entries": {}}') if a[1] == "origin/proof-bank:%s.windows.json" % head else (128, "")
            return 1, ""
        d = tempfile.mkdtemp(prefix="plat.")
        try:
            p, why = SP.fetch_bank(d, git=git, cls="windows")
            self.assertTrue(p and os.path.isfile(p), why)
            p2, why2 = SP.fetch_bank(d, git=git, cls="linux")
            self.assertIsNone(p2, "another class's bank was taken")
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
