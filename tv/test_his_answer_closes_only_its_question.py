# -*- coding: utf-8 -*-
"""#223 — HIS ANSWER CLOSES ONLY THE QUESTION IT WAS GIVEN TO, AND ONLY HE CAN GIVE IT.

His ask, 2026-09-24: the rows that need him should be "like the mailbox ... if need something done of
me what exactly and maybe the option there to tally it off ... that triggers and connects the answer
to the console". A row bills him only while it asks (test_a_row_is_his_only_when_it_asks); this is
the answer half. DRIVEN on temp stores and synthetic watchdog state, never his:
  · the store: one answer per question, a changed question reopens, a lapsed answer reopens, an
    unreadable store is never written over;
  · the partition: an answered question stops billing him and lands in its own bucket;
  · the door: every refusal, in order — a foreign Origin, an automated browser, no explicit yes, a
    guest board, nothing measured, an undeclared question or answer, a stale fingerprint.
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

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import his_answers as HA  # noqa: E402

ASK = {"id": "shadow-gate", "kind": "decide", "q": "stricter?", "fp": "shadow-gate:wouldHold",
       "answers": [{"key": "keep", "label": "Keep it as it is", "effect": "ruled"},
                   {"key": "stricter", "label": "Be stricter (Wilson)", "effect": "handoff"},
                   {"key": "week", "label": "Ask me in a week", "effect": "snooze"}]}
DAY = 24 * 3600 * 1000


class TheStore(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="his-answers-")
        self.p = os.path.join(self.d, "his_answers.json")

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_an_answer_closes_its_question_and_says_what_he_chose(self):
        ent, why = HA.record(self.p, ASK, "keep", now_ms=1000)
        self.assertTrue(ent, why)
        answers, _ = HA.load(self.p)
        self.assertEqual(HA.standing(ASK, answers, now_ms=2000)["label"], "Keep it as it is")
        rows = HA.apply([{"check": "shadow gate", "asks": [ASK]}], answers, now_ms=2000)
        self.assertEqual((rows[0]["openAsks"], rows[0]["answered"][0]["key"]), ([], "keep"))

    def test_a_changed_question_reopens_and_the_old_answer_is_kept(self):
        HA.record(self.p, ASK, "keep", now_ms=1000)
        answers, _ = HA.load(self.p)
        flipped = dict(ASK, fp="shadow-gate:wouldGround")
        rows = HA.apply([{"check": "shadow gate", "asks": [flipped]}], answers, now_ms=2000)
        self.assertEqual(len(rows[0]["openAsks"]), 1, "an answer to one question closed a different one")
        self.assertTrue(rows[0]["staleAnswers"][0]["stale"], "the old answer vanished instead of being kept")

    def test_a_lapsed_answer_asks_again(self):
        HA.record(self.p, ASK, "week", now_ms=1000)
        answers, _ = HA.load(self.p)
        self.assertIsNotNone(HA.standing(ASK, answers, now_ms=1000 + 6 * DAY))
        self.assertIsNone(HA.standing(ASK, answers, now_ms=1000 + 7 * DAY), "a week's snooze never lapsed")

    def test_a_handoff_holds_until_the_question_changes(self):
        ent, _ = HA.record(self.p, ASK, "stricter", now_ms=1000)
        self.assertIsNone(ent["until"])
        answers, _ = HA.load(self.p)
        self.assertIsNotNone(HA.standing(ASK, answers, now_ms=1000 + 400 * DAY))

    def test_an_answer_not_offered_is_refused(self):
        ent, why = HA.record(self.p, ASK, "delete-everything", now_ms=1000)
        self.assertIsNone(ent)
        self.assertFalse(os.path.exists(self.p), "a refused answer wrote the store")

    def test_an_unreadable_store_is_never_written_over(self):
        io.open(self.p, "w").write("{half a file")
        ent, why = HA.record(self.p, ASK, "keep", now_ms=1000)
        self.assertIsNone(ent)
        self.assertIn("cannot be read", why)
        self.assertEqual(io.open(self.p).read(), "{half a file", "his earlier answers were written over")
        self.assertEqual(HA.load(self.p)[0], None, "an unreadable store read as empty")


class ThePartitionAppliesThem(unittest.TestCase):

    def test_an_answered_question_stops_billing_him_and_is_not_claudes(self):
        import control_app as ca
        ent, _ = HA.entry_for(ASK, "keep")          # the real clock: a 1970 answer has lapsed
        rows = [{"check": "shadow gate", "state": "missing", "asks": [ASK]},
                {"check": "ledger staleness", "state": "missing", "asks": []}]
        open_p = ca.eagle_partition([dict(r) for r in rows], answers={})
        self.assertEqual([r["check"] for r in open_p["bad"]], ["shadow gate"], "premise: it asks while open")
        p = ca.eagle_partition([dict(r) for r in rows], answers={"shadow-gate": ent})
        self.assertEqual(p["bad"], [], "an answered question still billed him")
        self.assertEqual([r["check"] for r in p["answered"]], ["shadow gate"])
        self.assertNotIn("shadow gate", [r["check"] for r in p["mine"]],
                         "his ruling was filed as Claude's work (it would read CLAUDE OWES)")


    def test_a_handed_off_answer_becomes_claudes_work(self):
        """The second eye on 518945b3: 'Be stricter' (effect handoff) left his count and reached nobody."""
        import control_app as ca
        ent, _ = HA.entry_for(ASK, "stricter")
        rows = [{"check": "shadow gate", "state": "missing", "asks": [ASK]}]
        p = ca.eagle_partition([dict(r) for r in rows], answers={"shadow-gate": ent})
        self.assertEqual(p["bad"], [], "a handed-off question still billed him")
        self.assertIn("shadow gate", [r["check"] for r in p["mine"]],
                      "a handoff never reached Claude's work (WAITING ON CODE did not gain it)")
        self.assertEqual([r["check"] for r in p["answered"]], ["shadow gate"],
                         "the handoff is no longer shown as his answer")


class TheDoorOnlyOpensForHim(unittest.TestCase):

    def setUp(self):
        import control_app as ca
        self.ca = ca
        self.d = tempfile.mkdtemp(prefix="board-answer-")
        self._path = ca._his_answers_path
        ca._his_answers_path = lambda: os.path.join(self.d, "his_answers.json")
        self._eagle = dict(ca._EAGLE)
        ca._EAGLE.update({"needsYou": 1, "rows": [{"check": "shadow gate", "state": "missing",
                                                   "asks": [ASK]}], "slowRows": []})
        self.origin = "http://127.0.0.1:%d" % ca.CONTROL_PORT
        self.body = {"askId": "shadow-gate", "key": "keep", "fp": ASK["fp"], "confirm": True,
                     "who": {"id": "x", "p": "y", "pfx": ""}, "webdriver": False}

    def tearDown(self):
        self.ca._his_answers_path = self._path
        self.ca._EAGLE.clear()
        self.ca._EAGLE.update(self._eagle)
        shutil.rmtree(self.d, ignore_errors=True)

    def _stored(self):
        p = os.path.join(self.d, "his_answers.json")
        return json.load(io.open(p))["answers"] if os.path.exists(p) else {}

    def test_his_answer_lands_and_the_count_moves_in_the_same_request(self):
        code, out = self.ca.board_answer(dict(self.body), self.origin)
        self.assertEqual((code, out.get("ok")), (200, True), out)
        self.assertEqual(self._stored()["shadow-gate"]["key"], "keep")
        self.assertEqual(out["eagle"]["needsYou"], 0, "the count waited for the next tick")
        self.assertEqual(out["eagle"]["answeredWhat"], ["shadow gate"])

    def _refused(self, name, body=None, origin="__default__"):
        code, out = self.ca.board_answer(body if body is not None else dict(self.body),
                                         self.origin if origin == "__default__" else origin)
        self.assertEqual(out.get("refused"), name, out)
        self.assertEqual(self._stored(), {}, "a refused answer (%s) wrote the store" % name)
        return code, out

    def test_a_foreign_or_missing_origin_is_refused(self):
        self._refused("origin", origin="http://evil.example")
        self._refused("origin", origin="null")
        self._refused("origin", origin=None)

    def test_an_automated_browser_cannot_answer_for_him(self):
        self._refused("automation", body=dict(self.body, webdriver=True))

    def test_no_explicit_yes_is_no(self):
        self._refused("confirm", body=dict(self.body, confirm="false"))

    def test_a_guest_board_is_read_only(self):
        self._refused("guest", body=dict(self.body, who={"id": "x", "p": "y", "pfx": "I-abc-"}))

    def test_nothing_is_answered_before_anything_was_asked(self):
        self.ca._EAGLE["needsYou"] = None
        self._refused("unmeasured")

    def test_an_undeclared_question_or_answer_is_refused(self):
        self._refused("undeclared", body=dict(self.body, askId="delete-my-reels"))
        self._refused("undeclared", body=dict(self.body, key="prune-all"))

    def test_a_stale_fingerprint_gets_the_current_question_back(self):
        code, out = self._refused("stale", body=dict(self.body, fp="shadow-gate:wouldGround"))
        self.assertEqual((code, out["ask"]["fp"]), (409, ASK["fp"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#223 - a handed-off answer leaves his count and reaches nobody again (second eye on 518945b3)",
        "file": "control_app.py",
        "find": "        \"mine\":     [r for r in miss if r.get(\"check\") in mine_names] + no_q + handed,\n",
        "replace": "        \"mine\":     [r for r in miss if r.get(\"check\") in mine_names] + no_q,\n",
        "matches": 1,
    },
    {
        "why": "#223 - an answer given to one question closes a different one (the fingerprint is ignored)",
        "file": "his_answers.py",
        "find": "    if not isinstance(ent, dict) or ent.get(\"fp\") != ask.get(\"fp\"):\n",
        "replace": "    if not isinstance(ent, dict):\n",
        "matches": 1,
    },
    {
        "why": "#223 - an unreadable answers store is written over: his earlier answers are lost",
        "file": "his_answers.py",
        "find": "    answers, why = load(path)\n    if answers is None:\n        return None, why\n    ent, why = entry_for(ask, key, now_ms)\n",
        "replace": "    answers, why = load(path)\n    answers = answers or {}\n    ent, why = entry_for(ask, key, now_ms)\n",
        "matches": 1,
    },
    {
        "why": "#223 - any page he has open can write his decisions (the Origin check is gone; _cors answers *)",
        "file": "control_app.py",
        "find": "    if not origin or origin not in ok_origins:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "#223 - a harness or bot answers for him (navigator.webdriver is ignored)",
        "file": "control_app.py",
        "find": "    if body.get(\"webdriver\") is True or str(body.get(\"webdriver\")).lower() == \"true\":\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "#223 - an answered question keeps billing him (answers are not applied at read time)",
        "file": "control_app.py",
        "find": "        return bool(r.get(\"openAsks\", r.get(\"asks\")))\n",
        "replace": "        return bool(r.get(\"asks\"))\n",
        "matches": 1,
    },
]
