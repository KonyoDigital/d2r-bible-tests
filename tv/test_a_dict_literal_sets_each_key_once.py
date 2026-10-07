# -*- coding: utf-8 -*-
"""REG-1948 - NO DICT LITERAL IN tv/*.py SETS THE SAME KEY TWICE. THE LATER ONE WINS, SILENTLY.

The #231 eye on 5f85fc67: heart_state built its route answer as one literal that set "locksOk" twice - first "the lock
ledger was read" (rep.get("locksOk")), then the self-arming lock report's verdict (bool(locks.get("ok"))). Python keeps
the later value, so the panel's "PART OF THE HEART WAS NOT READ" (organsOk === false || locksOk === false) never saw an
unread ledger and fired on a lock that was merely not ok, under the census's own reason. test_heart counted the first
assignment's TEXT, which stayed present, so it stayed green. A sweep the same hour found one more ("footageFps" twice in
tv_diablo._health, harmless - both called the same function).

The law reads every tv/*.py with ast and refuses any dict literal whose constant keys repeat. DRIVEN: the scanner is
fed a source holding a duplicate and a clean literal and must flag exactly the duplicate - a scanner that sees nothing
cannot pass. The heart route keeps the ledger flag under its own name.
"""
import ast
import collections
import glob
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


def duplicate_keys(src, name="<src>"):
    """-> [(line, [repeated keys])] for every dict literal whose constant keys repeat."""
    out = []
    for n in ast.walk(ast.parse(src, name)):
        if isinstance(n, ast.Dict):
            ks = [k.value for k in n.keys if isinstance(k, ast.Constant) and isinstance(k.value, (str, int, float))]
            d = sorted(str(k) for k, v in collections.Counter(ks).items() if v > 1)
            if d:
                out.append((n.lineno, d))
    return out


class ADictLiteralSetsEachKeyOnce(unittest.TestCase):

    def test_the_scanner_can_see_a_duplicate(self):
        src = 'a = {"x": 1, "y": 2, "x": 3}\nb = {"x": 1, "y": 2}\nc = {**a, "x": 4}\n'
        self.assertEqual(duplicate_keys(src), [(1, ["x"])], "the scanner no longer sees a repeated key")

    def test_no_law_or_module_in_tv_repeats_a_key(self):
        bad = []
        files = sorted(glob.glob(os.path.join(HERE, "*.py")))
        self.assertGreater(len(files), 100, "the sweep reached almost nothing - re-point it")
        for p in files:
            with io.open(p, encoding="utf-8") as fh:
                src = fh.read()
            try:
                hits = duplicate_keys(src, p)
            except SyntaxError:
                continue
            bad += ["%s:%d %s" % (os.path.basename(p), ln, ",".join(ks)) for ln, ks in hits]
        self.assertEqual(bad, [], "a dict literal sets the same key twice - the later one silently wins (REG-1948)")

    def test_the_heart_route_keeps_the_ledger_flag_under_its_own_name(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(src.count('"locksOk": rep.get("locksOk"),'), 1)
        self.assertEqual(src.count('"lockReportOk": bool(locks.get("ok")),'), 1,
                         "the self-arming lock report's verdict lost its own key")


RED_PROOF = [
    {
        "why": "REG-1948 - the self-arming verdict takes the ledger flag's key again and silently overwrites it",
        "file": "tv/control_app.py",
        "find": '        "lockReportOk": bool(locks.get("ok")),\n',
        "replace": '        "locksOk": bool(locks.get("ok")),\n',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
