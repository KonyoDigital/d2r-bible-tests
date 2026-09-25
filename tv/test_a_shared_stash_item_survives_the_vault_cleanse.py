# -*- coding: utf-8 -*-
"""REG-1280 (#165) — A SHARED-STASH ITEM SURVIVES THE VAULT CLEANSE.

The seed floor's "one-time vault cleanse" (v677, it runs on every owner load) deletes every _GRAIL_SEED /
_UNI_EXTRA name that sits in `owned` with no mule filing - the residue the v659-v676 floors left when
they wrote ledger names into the physical vault. A shared-stash item is never filed to a mule: the
shared stash has no mule, and tvVaultRegister('Bone Break') answers mule:null ("unsorted") by design.
Bone Break is also a _GRAIL_SEED name, so the cleanse deleted it on the next load.

MEASURED on a real page (fresh floored board, automation world): registered Bone Break and Black
Cleft, reloaded - Bone Break gone, Black Cleft (no seed name) kept. After the fix both survive. Found
because v2208's reload case went red the moment REG-1275 let the floor run on a fresh board.

  · DRIVEN (node, the SHIPPED cleanse statement cut from bible.html, with the SHIPPED _SHARED_KEEP):
    an unfiled shared-stash seed name is KEPT; an unfiled plain seed name is still STRIPPED (the cleanse
    keeps its job); a filed seed name is kept; a name in no seed is untouched.
RED_PROOF below.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

NODE = shutil.which("node")
START = "        Object.keys(_GRAIL_SEED).concat(Object.keys(typeof _UNI_EXTRA!=='undefined'?_UNI_EXTRA:{})).forEach(function(n){"
END = "        });\n"


def _bible():
    with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as f:
        return f.read()


def _pieces(src):
    """The shipped cleanse statement and the shipped _SHARED_KEEP regex. -> (statement, regex literal)"""
    assert src.count(START) == 1, "the cleanse statement is not where this law looks (%d)" % src.count(START)
    i = src.index(START)
    j = src.index(END, i) + len(END)
    m = re.search(r"var _SHARED_KEEP = (/.+?/i);", src)
    assert m, "the shipped _SHARED_KEEP regex is gone"
    return src[i:j], m.group(1)


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class ASharedStashItemSurvivesTheVaultCleanse(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.stmt, cls.keep = _pieces(_bible())

    def _run(self, owned, filed):
        seed = {"Bone Break": "Jul 1", "Harlequin Crest": "Jul 2", "Crown of Ages": "Jul 3"}
        js = ("var _GRAIL_SEED = %s; var _UNI_EXTRA = {};\n"
              "var owned = new Set(%s); var _ma = %s; var _gfl = {}; var _gch = false, _gflCh = false;\n"
              "var _SHARED_KEEP = %s; var window = {};\n%s\n"
              "console.log(JSON.stringify([...owned].sort()));"
              % (json.dumps(seed), json.dumps(owned), json.dumps(filed), self.keep, self.stmt))
        d = tempfile.mkdtemp(prefix="cleanse_law_")
        f = os.path.join(d, "t.js")
        with io.open(f, "w", encoding="utf-8") as fh:
            fh.write(js)
        r = subprocess.run([NODE, f], capture_output=True, text=True, timeout=60)
        shutil.rmtree(d, ignore_errors=True)
        if r.returncode != 0:
            raise AssertionError("the shipped cleanse would not execute - UNKNOWN, not passing: %s" % r.stderr[:300])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_an_unfiled_shared_stash_seed_name_is_kept(self):
        self.assertIn("Bone Break", self._run(["Bone Break"], {}),
                      "a registered sunder charm (never filed - the shared stash has no mule) was deleted on load")

    def test_floor_residue_is_still_stripped(self):
        self.assertNotIn("Harlequin Crest", self._run(["Harlequin Crest", "Bone Break"], {}),
                         "the cleanse no longer strips an unfiled plain seed name - it stopped doing its job")

    def test_a_filed_seed_name_and_a_name_in_no_seed_are_kept(self):
        got = self._run(["Crown of Ages", "Black Cleft"], {"Crown of Ages": "uni-armor"})
        self.assertEqual(got, ["Black Cleft", "Crown of Ages"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1280 - the cleanse forgets the shared stash again: a registered Bone Break is deleted on the next load",
        "file": "bible.html",
        "find": "          if (owned.has(n) && !_ma[n] && !_SHARED_KEEP.test(n)) { owned.delete(n);",
        "replace": "          if (owned.has(n) && !_ma[n]) { owned.delete(n);",
        "matches": 1,
    },
]
