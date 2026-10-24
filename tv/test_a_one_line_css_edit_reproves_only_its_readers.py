# -*- coding: utf-8 -*-
"""REG-2642 (#42 P3-fine) — A ONE-LINE CSS EDIT TO control_ui.html RE-PROVES ONLY THE LAWS THAT READ IT.

"make sure it really do reuse... i dont want this happening again and again" (Elad, 2026-10-25). v3796 r6 changed 8
lines of CSS and the Mac pre-prove re-proved 5,012 of 6,327 proofs from nothing, because every law whose import
closure SPELLS control_ui.html keyed its bytes. This law runs the REAL push path (_prove_push with a real cache file)
over a fixture repo of ten laws: eight never open control_ui.html although a helper names it (as run_gates names
every file), two read it. A cold push banks all ten; a one-line CSS edit, then a warm push, must reuse the eight and
re-prove only the two - and the re-proved share must stay under MAX_REPROVED_SHARE.

MAX_REPROVED_SHARE = 0.30. Measured on the box (2026-10-25, 40 real gates / 204 proofs, real cache): back-to-back
on an unchanged tree 203/204 reused (the 1 is a macOS-only proof); a one-line CSS edit on top of r6 130/204 reused
(74 re-proved = laws that read the page, plus node/git/browser laws the trace cannot yet see - #42 phase 2). The
fixture has only traced laws, so its honest share is 2/10 = 20%; 30% leaves room for one more reader and fails long
before the regression this guards (100% here, 79% on the real r6 replay). [[regression-guard]]
RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import heart2 as H  # noqa: E402
import test_a_proven_verdict_is_reused_only_on_identical_bytes as P3  # noqa: E402
from test_a_push_proof_runs_only_where_its_defect_shows import _Env, _Patch, _no_facts  # noqa: E402

MAX_REPROVED_SHARE = 0.30
_READERS, _OTHERS = 2, 8
_CSS = "<style>\n  html { scrollbar-color: rgba(240,192,96,.28) transparent; }\n  .a { color: red; }\n</style>\n"

_LAW = r'''
import io, os, sys
import helper_ui
here = os.path.dirname(os.path.abspath(__file__))
SUBJECT = os.path.join(here, "sub" + "ject_%(i)d.txt")
%(read)s
with io.open(SUBJECT, encoding="utf-8") as fh:
    subject = fh.read()
with io.open(os.environ["P3_LOG"], "a", encoding="utf-8") as fh:
    fh.write("%(i)d|%%s\n" %% ("tampered" if "BROKEN" in subject else "clean"))
red = "BROKEN" in subject
print("Ran 1 tests in 0.001s")
print("")
print("FAILED (failures=1)" if red else "OK")
sys.exit(1 if red else 0)
'''
_READ = "with io.open(os.path.join(here, helper_ui.PAGE), encoding='utf-8') as _fh: _fh.read()"


def _gates():
    out = []
    for i in range(_READERS + _OTHERS):
        pr = {"why": "the fixture's defect", "file": "subject_%d.txt" % i, "find": "fine", "replace": "BROKEN",
              "matches": 1}
        out.append(("css-law-%d" % i, "t_css_%d.py" % i, [pr]))
    return out


class _Tree(P3._Tree):
    def __init__(self):
        super(_Tree, self).__init__()
        self.files = {"tv/control_app.py": "# sandbox marker\n", "tv/control_ui.html": _CSS,
                      "tv/helper_ui.py": "PAGE = 'control_ui.html'   # named, as run_gates names every file\n"}
        for i in range(_READERS + _OTHERS):
            self.files["tv/t_css_%d.py" % i] = _LAW % {"i": i, "read": _READ if i < _READERS else ""}
            self.files["tv/subject_%d.txt" % i] = "all fine here\n"


class AOneLineCssEditReprovesOnlyItsReaders(unittest.TestCase):

    def setUp(self):
        self.tree = _Tree()
        self.dir = tempfile.mkdtemp(prefix="csscache.")
        self.cache_path = os.path.join(self.dir, ".heart2_cache.json")
        self._tracked = H._tracked_files
        H._tracked_files = lambda repo=None: None

    def tearDown(self):
        H._tracked_files = self._tracked
        H._TRACES.clear()
        shutil.rmtree(self.dir, ignore_errors=True)
        for r in self.tree.made:
            shutil.rmtree(r, ignore_errors=True)

    def push(self):
        H._TRACES.clear()                                   # each push is another process
        fd, log = tempfile.mkstemp(prefix="csslog.")
        os.close(fd)
        said = []
        try:
            cache = H._VerdictCache(path=self.cache_path, say=said.append)
            with _Env(P3_LOG=log, HEART2_PROVE_WORKERS="1", TV_LAW_WIDTHS=None), \
                    _Patch(make_sandbox=self.tree.make, _push_facts=_no_facts):
                results, per = H._prove_push(_gates(), said.append, [], cache=cache)
            with io.open(log, encoding="utf-8") as fh:
                ran = sorted({int(l.split("|")[0]) for l in fh if l.strip()})
        finally:
            os.remove(log)
        return results, ran, said

    def test_a_one_line_css_edit_reproves_only_the_laws_that_read_it(self):
        """★ THE REGRESSION GUARD: cold banks 10; a 1-line CSS edit re-proves the 2 readers and reuses the 8"""
        results, ran, said = self.push()
        self.assertEqual(set(results.values()), {H.PROVEN}, "\n".join(said))
        self.assertEqual(len(ran), _READERS + _OTHERS, "the cold push did not run every law: %s" % ran)
        self.tree.files["tv/control_ui.html"] = _CSS.replace(".28)", ".29)")
        results, ran, said = self.push()
        self.assertEqual(set(results.values()), {H.PROVEN}, "\n".join(said))
        share = float(len(ran)) / (_READERS + _OTHERS)
        self.assertLessEqual(share, MAX_REPROVED_SHARE, "a one-line CSS edit re-proved %d of %d laws (%.0f%% > %.0f%%): "
                             "%s\n%s" % (len(ran), _READERS + _OTHERS, 100 * share, 100 * MAX_REPROVED_SHARE, ran,
                                         "\n".join(said)))
        self.assertEqual(ran, list(range(_READERS)), "SOUNDNESS: the laws that READ control_ui.html must re-prove")

    def test_an_unchanged_tree_reuses_everything(self):
        """★ the bank writes and reads: a second push over identical bytes runs nothing"""
        self.push()
        results, ran, said = self.push()
        self.assertEqual(ran, [], "an unchanged tree re-proved %s\n%s" % (ran, "\n".join(said)))
        self.assertEqual(set(results.values()), {H.PROVEN}, "\n".join(said))


RED_PROOF = [
    {"why": "keying every named file by bytes again (the v3796 r6 regression) re-proves all ten",
     "file": "tv/heart2.py", "find": "    return sorted(r for r in rels if r not in keep\n",
     "replace": "    return []\n    return sorted(r for r in rels if r not in keep\n", "matches": 1},
]

if __name__ == "__main__":
    unittest.main()
