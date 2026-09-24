# -*- coding: utf-8 -*-
"""#226 — A ROW IS HIS ONLY WHEN IT ASKS HIM SOMETHING.

⚠⚠ HIS RULING, 2026-09-24: "it should only really be waiting on me if its something i need to do".
MEASURED on his live console the same morning: WAITING ON YOU read 5 and exactly ONE was his — the
shadow gate. The other four were my work (a lane not yet drained, a parser owed a declared field, a
seed bake owed, a river the planner calls "an answer, not a failure"). v2284 made every unlisted
check his BY DEFAULT; this inverts it. A red row bills him only while its check DECLARES a question
(console_doctor.ASKS), and every other red row is Claude's — still drawn, at its real state, under
WAITING ON CODE with the reason. It FAILS LOUD: a row with no `asks` key (banked before the
registry) or a registry nobody can read bills him as before.

DRIVEN on synthetic rows (never his console): the registry, the per-row attach, the ask shape, and
the one partition both surfaces read. RED_PROOF below.
"""
import inspect
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

import console_doctor as cd  # noqa: E402


class TheRegistryIsHonest(unittest.TestCase):

    def test_every_asking_check_exists_and_is_nobody_elses(self):
        names = {n for n, _ in cd.CHECKS}
        self.assertTrue(cd.ASKS, "premise: no check asks him anything — the shadow gate is his")
        for k in cd.ASKS:
            self.assertIn(k, names, "%r asks him something but no such check exists" % k)
            self.assertNotIn(k, cd.MINE, "%r is both his question and Claude's defect" % k)
            self.assertNotIn(k, cd.BY_DESIGN, "%r is both his question and red on purpose" % k)

    def test_a_check_that_asks_nothing_is_not_his(self):
        self.assertEqual(cd.owner_of("shadow gate"), "you")
        self.assertIn("ledger staleness", {n for n, _ in cd.CHECKS}, "premise: re-anchor on a real check")
        self.assertEqual(cd.owner_of("ledger staleness"), "me",
                         "a check that declares no question is billed to him by default again (v2284)")


class EachRowCarriesItsQuestions(unittest.TestCase):

    def test_the_shadow_gate_asks_while_it_disagrees(self):
        rows = cd.attach_asks([{"check": "shadow gate", "state": "missing", "why": "57 names differ"}])
        asks = rows[0]["asks"]
        self.assertEqual(len(asks), 1, "the shadow gate is red and asks him nothing: %r" % rows[0])
        self.assertEqual(cd.ask_problems(asks[0]), [], "its declared question is malformed")
        self.assertEqual([a["key"] for a in asks[0]["answers"]], ["keep", "stricter", "week"])
        self.assertTrue(asks[0]["fp"].startswith("shadow-gate:"))

    def test_a_green_row_asks_nothing(self):
        rows = cd.attach_asks([{"check": "shadow gate", "state": "ok", "why": ""},
                               {"check": "ledger staleness", "state": "missing", "why": "bake owed"}])
        self.assertEqual([r["asks"] for r in rows], [[], []])

    def test_a_question_that_throws_is_said_never_swallowed(self):
        real = dict(cd.ASKS)
        try:
            cd.ASKS["shadow gate"] = lambda r: 1 / 0
            row = cd.attach_asks([{"check": "shadow gate", "state": "missing"}])[0]
            self.assertEqual(row["asks"], [])
            self.assertIn("could not be computed", row.get("askWhy") or "")
            cd.ASKS["shadow gate"] = lambda r: [{"id": "x", "kind": "decide", "q": "?", "fp": "f",
                                                 "answers": [{"key": "a", "label": "L" * 40,
                                                              "effect": "ruled"}]}]
            row = cd.attach_asks([{"check": "shadow gate", "state": "missing"}])[0]
            self.assertEqual(row["asks"], [])
            self.assertIn("malformed", row.get("askWhy") or "")
        finally:
            cd.ASKS.clear()
            cd.ASKS.update(real)

    def test_run_attaches_before_it_banks(self):
        src = inspect.getsource(cd.run)
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        a, b = code.find("attach_asks(rows)"), code.find("_persist_slow(rows)")
        self.assertTrue(a >= 0 and b >= 0, "premise: run() no longer attaches or no longer banks")
        self.assertLess(a, b, "rows are banked before they carry their questions")


class TheOnePartitionReadsTheQuestions(unittest.TestCase):

    def test_only_a_row_that_asks_bills_him(self):
        import control_app as ca
        rows = [
            {"check": "shadow gate", "state": "missing", "asks": [{"id": "shadow-gate"}]},
            {"check": "ledger staleness", "state": "missing", "asks": []},     # asks nothing
            {"check": "the river", "state": "missing", "asks": []},            # BY_DESIGN
            {"check": "board join", "state": "missing", "asks": []},           # MINE
            {"check": "handoff lanes drained", "state": "missing"},           # banked before ASKS
        ]
        p = ca.eagle_partition(rows)
        self.assertEqual({r["check"] for r in p["bad"]}, {"shadow gate", "handoff lanes drained"},
                         "a row that asks him nothing was billed, or a pre-registry row went quiet")
        self.assertEqual({r["check"] for r in p["noQuestion"]}, {"ledger staleness"})
        self.assertEqual({r["check"] for r in p["mine"]}, {"board join", "ledger staleness"},
                         "a no-question row VANISHED instead of landing under Claude's work")
        self.assertEqual({r["check"] for r in p["byDesign"]}, {"the river"})

    def test_an_unreadable_registry_bills_everything(self):
        import control_app as ca
        real = cd.ASKS
        try:
            cd.ASKS = None
            p = ca.eagle_partition([{"check": "ledger staleness", "state": "missing", "asks": []}])
            self.assertEqual([r["check"] for r in p["bad"]], ["ledger staleness"],
                             "a registry nobody can read silenced a row from his count")
        finally:
            cd.ASKS = real


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#226 - every check that asks nothing is his by default again (v2284): my bugs re-bill him",
        "file": "console_doctor.py",
        "find": "    return \"you\" if name in ASKS else \"me\"\n",
        "replace": "    return \"you\"\n",
        "matches": 1,
    },
    {
        "why": "#226 - the partition bills every red row whether or not it asks him anything (5 billed, 1 his)",
        "file": "control_app.py",
        "find": "        return bool(r.get(\"asks\"))\n",
        "replace": "        return True\n",
        "matches": 1,
    },
    {
        "why": "#226 - rows never carry their questions: the shadow gate stops asking and his count reads 0 over a real decision",
        "file": "console_doctor.py",
        "find": "        r[\"asks\"] = got\n",
        "replace": "        r[\"asks\"] = []\n",
        "matches": 1,
    },
    {
        "why": "#226 - an unreadable registry silences instead of billing",
        "file": "control_app.py",
        "find": "        if not asks_known or \"asks\" not in r:\n            return True\n",
        "replace": "        if \"asks\" not in r:\n            return True\n",
        "matches": 1,
    },
]
