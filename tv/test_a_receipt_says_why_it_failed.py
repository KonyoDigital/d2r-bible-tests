# -*- coding: utf-8 -*-
"""#158.3 (GrokBot, the vault on his real frames) - A RECEIPT SAYS WHY IT FAILED, AND A GUARD HOLD IS NOT AN ERROR.

v1945 kept the reason on every intake record (`err`, `why`, `guardHeld`, `refused`) after 45 of 46 receipts read ok:false
with nothing to tell a deliberate hold, a failed read and an honest empty apart. /api/intake_log then built its rows from
seven fields and dropped the reason again, so the 39 failed reads on his frames read only 'error' in the RECEIPT LEDGER.

Driven on the real control_app.intake_log_answer over a journal holding each kind of record, and the ledger's own row
renderer (_rlogRender, cut from control_ui.html) in node. RED_PROOF below.
"""
import json
import os
import subprocess
import sys
import unittest

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
import control_app as CA  # noqa: E402
from cb_node_harness import NODE  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")
T0 = 1792800000000


def _rec(ts, **ik):
    base = {"tab": "stash", "kind": "stash", "counts": {}, "total": 0, "errors": 0, "items": [], "ok": True}
    base.update(ik)
    return {"ts": ts, "lane": "intake", "frameId": "f_%d.jpg" % ts, "sessionId": "s_1", "intake": base}


JOURNAL = [
    _rec(T0 + 1, ok=True, total=3, counts={"Shako": 1}),
    _rec(T0 + 2, ok=False, err="the read came back empty: the frame was a loading screen"),
    _rec(T0 + 3, ok=False, guardHeld=True, why="held: the auto-intake guard is off on this console"),
    _rec(T0 + 4, ok=False, refused=True, err="intake refused - chronicle route guard"),
    _rec(T0 + 5, ok=False),                                  # an old receipt: no reason recorded
    {"ts": T0 + 6, "lane": "stash", "names": ["Shako"]},     # not an intake record
]


class AReceiptSaysWhyItFailed(unittest.TestCase):

    def test_each_row_carries_its_reason_and_a_hold_is_its_own_status(self):
        d = CA.intake_log_answer(JOURNAL)
        rows = {r["ts"] - T0: r for r in d["rows"]}
        self.assertEqual(sorted(rows), [1, 2, 3, 4, 5], "a non-intake record became a receipt, or one was lost")
        self.assertEqual(rows[1]["status"], "ok")
        self.assertIsNone(rows[1]["why"])
        self.assertEqual(rows[2]["status"], "error")
        self.assertIn("loading screen", rows[2]["why"] or "", "a failed read lost the reason its record carries")
        self.assertEqual(rows[3]["status"], "held", "a deliberate guard hold read as an error: %r" % rows[3])
        self.assertIn("guard is off", rows[3]["why"] or "")
        self.assertTrue(rows[4]["refused"])
        self.assertIn("route guard", rows[4]["why"] or "")
        self.assertIsNone(rows[5]["why"], "an old receipt with no reason was given one")
        self.assertEqual(d["summary"], {"total": 5, "empty": 0, "error": 3, "held": 1}, d["summary"])
        self.assertEqual([r["ts"] - T0 for r in d["rows"]], [5, 4, 3, 2, 1], "the ledger is not newest first")

    @unittest.skipUnless(NODE, "node is absent on this machine - UNMEASURED here, never a pass")
    def test_the_ledger_row_says_the_reason(self):
        with open(UI, encoding="utf-8") as fh:
            ui = fh.read()
        start = "  function _rlogRender(){\n"
        self.assertEqual(ui.count(start), 1, "PREMISE: the ledger renderer moved")
        i = ui.index(start)
        fn = ui[i:ui.index("\n  }\n", i) + 4]
        dot = ui[ui.index("  var _RDOT = {"):]
        dot = dot[:dot.index("\n") + 1]
        rows = CA.intake_log_answer(JOURNAL)
        js = ("var EL = {}; var document = { getElementById: function(id){ return EL[id] || (EL[id] = {}); } };\n"
              "function esc(t){ return String(t == null ? '' : t).replace(/[<>\"&]/g, ''); }\n"
              "function thTabIcon(){ return ''; }\n" + dot + fn +
              "\nvar RLOG = %s;\n_rlogRender();\nconsole.log(JSON.stringify({ list: EL['rlog-list'].innerHTML, "
              "sum: EL['rlog-sum'].textContent }));" % json.dumps({"rows": rows["rows"], "summary": rows["summary"]}))
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertIn("loading screen", out["list"], "the row does not say why the read failed")
        self.assertIn("rlog-held", out["list"])
        self.assertIn("1 held by a guard", out["sum"])


RED_PROOF = [
    {"why": "#158.3 - the ledger drops the reason the record carries again",
     "file": "tv/control_app.py",
     "find": "        _why = str(ik.get(\"why\") or ik.get(\"err\") or \"\")[:300] or None\n",
     "replace": "        _why = None\n",
     "matches": 1},
    {"why": "#158.3 - a deliberate guard hold reads as an error again",
     "file": "tv/control_app.py",
     "find": "            \"status\": (\"held\" if (_held and not _ok) else (\"error\" if not _ok else (\"empty\" if _tot == 0 else \"ok\"))),\n",
     "replace": "            \"status\": (\"error\" if not _ok else (\"empty\" if _tot == 0 else \"ok\")),\n",
     "matches": 1},
    {"why": "#158.3 - the ledger row does not say the reason",
     "file": "tv/control_ui.html",
     "find": "        + (r.why ? '<span class=\"rlog-why\" title=\"' + esc(r.why) + '\">' + esc(String(r.why).slice(0, 90)) + '</span>' : '')\n",
     "replace": "",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
