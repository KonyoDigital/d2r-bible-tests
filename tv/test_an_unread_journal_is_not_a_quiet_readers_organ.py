# -*- coding: utf-8 -*-
"""REG-1807 — AN UNREAD JOURNAL IS NOT A QUIET READERS ORGAN.

The readers organ treats a missing queue count as zero. While live that
pulse stays ok and the subtitle says queue 0. Off air it rests, idle, on
that same zero. An unread journal walk is that same missing count: the
poll already publishes null, because the walk did not copy the counters.

A measured zero still says queue 0. A deep queue still warns. A dead
engine is still down. A paused reader still says paused. A KAI catch is
still that catch. A complete film is still that film. Grok stepping in is
still said. A judge count is still added when the queue was read. An
unread walk says the journal was not read, and the pulse is not ok. A
judge count is not added onto a zero that was not measured.

Nothing here reads his journal. The wire stays null. RED_PROOF below.
[[unknown-stays-unknown]]
"""
import json
import os
import subprocess
import unittest


HERE = os.path.dirname(os.path.abspath(__file__))
_NOT_READ = "the journal was not read"


def _paint(mode="off", driver=None, judge_q=0, read_count=0, eyes=None,
           completeness=None, engine_alive=True, ai_paused=False, readers=None):
    with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        ui = fh.read()
    start = ui.find("var _EH_STATE = { ok: 'HEALTHY'")
    end = ui.find("function _rnFeedRow", start)
    if start < 0 or end < 0:
        raise AssertionError("the readers organ is not in control_ui.html")
    fn = ui[start:end]
    if "\x00" in fn:
        raise AssertionError("the organ slice crossed the null byte")
    dr = {} if driver is None else dict(driver)
    dr.setdefault("judgeQ", judge_q)
    sh = {"verdict": "idle", "tabs": {}}
    if completeness is not None:
        sh["completeness"] = completeness
    st = {
        "mode": mode,
        "sessionHealth": sh,
        "driver": dr,
        "eyes": {} if eyes is None else eyes,
        "watchdog": {},
        "journalMB": 0,
        "readCount": read_count,
        "engineAlive": engine_alive,
        "aiPaused": ai_paused,
    }
    if readers is not None:
        st["readers"] = readers
    js = (
        "function esc(s){return String(s==null?'':s);}\n"
        + fn
        + "var o=_engineOrganData(" + json.dumps(st) + ");\n"
        + "var rd=o.filter(function(x){return x.key==='readers';})[0];\n"
        + "process.stdout.write(JSON.stringify({pulse:rd.pulse,stat:rd.stat,"
        + "sub:rd.sub,state:rd.state}));\n"
    )
    got = subprocess.run(
        ["node", "-"], input=js.encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if got.returncode != 0:
        raise AssertionError(got.stderr.decode("utf-8", "replace")[:800])
    return json.loads(got.stdout.decode("utf-8"))


class AnUnreadJournalIsNotAQuietReadersOrgan(unittest.TestCase):

    def test_a_measured_zero_off_air_is_still_a_quiet_queue(self):
        row = _paint(mode="off", driver={"seen": 0, "queued": 0, "fired": 0}, read_count=0)
        self.assertEqual(row["pulse"], "idle")
        self.assertEqual(row["state"], "IDLE")
        self.assertEqual(row["sub"], "queue 0")
        self.assertNotIn("was not read", row["sub"])
        self.assertIn("0", row["stat"])

    def test_a_live_measured_zero_is_still_that_zero(self):
        row = _paint(mode="live", driver={"seen": 0, "queued": 0, "fired": 0}, read_count=7)
        self.assertEqual(row["pulse"], "ok")
        self.assertEqual(row["state"], "HEALTHY")
        self.assertEqual(row["sub"], "queue 0")
        self.assertNotIn("was not read", row["sub"])
        self.assertIn("7", row["stat"])
        self.assertIn("✓", row["stat"])

    def test_an_unread_journal_is_not_a_quiet_readers_organ(self):
        row = _paint(
            mode="live",
            driver={"seen": None, "queued": None, "fired": None, "refire": None},
            read_count=7, ai_paused=True)
        self.assertEqual(row["pulse"], "warn")
        self.assertEqual(row["state"], "STRAINED")
        self.assertEqual(row["sub"], _NOT_READ)
        self.assertNotEqual(row["pulse"], "ok")
        self.assertNotIn("queue", row["sub"])
        self.assertNotIn("paused", row["sub"])
        self.assertIn("7", row["stat"])

    def test_an_off_air_unread_journal_is_not_a_resting_queue(self):
        row = _paint(
            mode="off",
            driver={"seen": None, "queued": None, "fired": None, "refire": None})
        self.assertEqual(row["pulse"], "warn")
        self.assertNotEqual(row["pulse"], "idle")
        self.assertEqual(row["state"], "STRAINED")
        self.assertEqual(row["sub"], _NOT_READ)
        self.assertNotIn("queue 0", row["sub"])

    def test_a_deep_queue_still_warns(self):
        row = _paint(mode="live", driver={"seen": 9, "queued": 9, "fired": 1})
        self.assertEqual(row["pulse"], "warn")
        self.assertEqual(row["state"], "STRAINED")
        self.assertEqual(row["sub"], "queue 9")
        self.assertNotIn("was not read", row["sub"])

    def test_a_dead_engine_is_still_down(self):
        row = _paint(
            mode="live", driver={"seen": 1, "queued": 0, "fired": 0},
            engine_alive=False, read_count=3)
        self.assertEqual(row["pulse"], "bad")
        self.assertEqual(row["state"], "DOWN")
        self.assertEqual(row["sub"], "queue 0")
        self.assertNotIn("was not read", row["sub"])
        self.assertIn("3", row["stat"])

    def test_a_dead_engine_with_an_unread_queue_is_still_down(self):
        row = _paint(
            mode="live",
            driver={"seen": None, "queued": None, "fired": None},
            engine_alive=False)
        self.assertEqual(row["pulse"], "bad")
        self.assertEqual(row["state"], "DOWN")
        self.assertEqual(row["sub"], _NOT_READ)
        self.assertNotIn("queue", row["sub"])

    def test_a_paused_reader_is_still_paused(self):
        row = _paint(
            mode="live", driver={"seen": 1, "queued": 1, "fired": 0}, ai_paused=True)
        self.assertEqual(row["pulse"], "ok")
        self.assertEqual(row["sub"], "queue 1 · paused")
        self.assertNotIn("was not read", row["sub"])

    def test_a_kai_catch_is_still_that_catch(self):
        row = _paint(
            mode="live", driver={"seen": 2, "queued": 0, "fired": 1},
            eyes={"kaiMissed": 4, "verifyTs": 5})
        self.assertEqual(row["pulse"], "ok")
        self.assertEqual(row["sub"], "queue 0 · KAI caught 4")
        self.assertIn("4", row["stat"])
        self.assertIn("✓", row["stat"])
        self.assertNotIn("was not read", row["sub"])

    def test_a_complete_film_is_still_that_film(self):
        row = _paint(
            mode="live", driver={"seen": 2, "queued": 0, "fired": 2},
            completeness={"reads": 2, "unread": 1, "film": 3, "dropped": 0})
        self.assertEqual(row["pulse"], "ok")
        self.assertIn("2 live", row["sub"])
        self.assertIn("1 retro-caught", row["sub"])
        self.assertNotIn("was not read", row["sub"])
        self.assertNotIn("queue", row["sub"])

    def test_a_deep_queue_still_warns_when_the_film_is_complete(self):
        row = _paint(
            mode="live", driver={"seen": 2, "queued": 12, "fired": 1},
            completeness={"reads": 2, "unread": 0, "film": 3, "dropped": 0})
        self.assertEqual(row["pulse"], "warn")
        self.assertIn("2 live", row["sub"])
        self.assertNotIn("was not read", row["sub"])

    def test_an_unread_queue_does_not_borrow_a_film_line(self):
        row = _paint(
            mode="live",
            driver={"seen": None, "queued": None, "fired": None},
            completeness={"reads": 2, "unread": 0, "film": 3, "dropped": 0})
        self.assertEqual(row["pulse"], "warn")
        self.assertEqual(row["sub"], _NOT_READ)
        self.assertNotIn("live", row["sub"])

    def test_grok_stepping_in_is_still_said(self):
        row = _paint(
            mode="live", driver={"seen": 1, "queued": 0, "fired": 1},
            readers={"backupReads": 2, "backupWhy": "claude"})
        self.assertEqual(row["pulse"], "ok")
        self.assertIn("queue 0", row["sub"])
        self.assertIn("Grok stepped in 2", row["sub"])
        self.assertIn("claude", row["sub"])
        self.assertNotIn("was not read", row["sub"])

    def test_an_unread_walk_does_not_append_grok_onto_the_sentence(self):
        row = _paint(
            mode="live",
            driver={"seen": None, "queued": None, "fired": None},
            readers={"backupReads": 2, "backupWhy": "claude"})
        self.assertEqual(row["pulse"], "warn")
        self.assertEqual(row["sub"], _NOT_READ)
        self.assertNotIn("Grok", row["sub"])

    def test_a_judge_count_is_still_added_when_the_queue_was_read(self):
        row = _paint(
            mode="live", driver={"seen": 0, "queued": 0, "fired": 0}, judge_q=2)
        self.assertEqual(row["pulse"], "ok")
        self.assertEqual(row["sub"], "queue 2")
        self.assertNotIn("was not read", row["sub"])

    def test_an_unread_walk_does_not_add_the_judge_onto_a_zero(self):
        row = _paint(
            mode="live",
            driver={"seen": None, "queued": None, "fired": None, "refire": None},
            judge_q=2)
        self.assertEqual(row["pulse"], "warn")
        self.assertEqual(row["sub"], _NOT_READ)
        self.assertNotIn("queue", row["sub"])
        self.assertNotEqual(row["sub"], "queue 2")

    def test_a_missing_count_is_still_a_measured_zero(self):
        """A driver block that never sent the key is not the null the walk publishes."""
        row = _paint(mode="live", driver={})
        self.assertEqual(row["pulse"], "ok")
        self.assertEqual(row["sub"], "queue 0")
        self.assertNotIn("was not read", row["sub"])

    def test_the_organ_asks_this_look(self):
        with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
            ui = fh.read()
        self.assertEqual(ui.count("\x00"), 1)
        self.assertIn("    var queueUnread = (dr.queued === null);\n", ui)
        self.assertIn(
            "var rdPulse = dead ? 'bad' : (queueUnread ? 'warn' : "
            "(!on ? 'idle' : (qDepth > 8 ? 'warn' : 'ok')));",
            ui)
        self.assertIn("    var rdSub = queueUnread\n", ui)
        self.assertIn(
            "    if (!queueUnread && typeof _bkN === 'number' && _bkN > 0)\n",
            ui)
        self.assertNotIn(
            "var rdPulse = dead ? 'bad' : (!on ? 'idle' : (qDepth > 8 ? 'warn' : 'ok'));",
            ui)
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn('"queued": None', src)


RED_PROOF = [
    {
        "why": "REG-1807 - an unread journal is painted as a quiet readers organ",
        "file": "control_ui.html",
        "find": "    var queueUnread = (dr.queued === null);\n",
        "replace": "    var queueUnread = false;\n",
        "matches": 1,
    },
    {
        "why": "REG-1807 - a measured zero is painted as a journal that was not read",
        "file": "control_ui.html",
        "find": "    var queueUnread = (dr.queued === null);\n",
        "replace": "    var queueUnread = (dr.queued === 0);\n",
        "matches": 1,
    },
    {
        "why": "REG-1807 - the subtitle calls an unread queue zero",
        "file": "control_ui.html",
        "find": "    var rdSub = queueUnread\n"
                "      ? 'the journal was not read'\n"
                "      : (hasCp\n",
        "replace": "    var rdSub = (hasCp\n",
        "matches": 1,
    },
    {
        "why": "REG-1807 - an unread journal stays an ok readers organ",
        "file": "control_ui.html",
        "find": "    var rdPulse = dead ? 'bad' : (queueUnread ? 'warn' : "
                "(!on ? 'idle' : (qDepth > 8 ? 'warn' : 'ok')));\n",
        "replace": "    var rdPulse = dead ? 'bad' : (!on ? 'idle' : (qDepth > 8 ? 'warn' : 'ok'));\n",
        "matches": 1,
    },
    {
        "why": "REG-1807 - grok stepping in is glued onto an unread queue",
        "file": "control_ui.html",
        "find": "    if (!queueUnread && typeof _bkN === 'number' && _bkN > 0)\n",
        "replace": "    if (typeof _bkN === 'number' && _bkN > 0)\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
