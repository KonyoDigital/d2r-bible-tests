#!/usr/bin/env python3
"""THE CONSOLE→BOARD HANDOFF, DRIVEN END TO END.

★ WHY THIS FILE IS NOT A SOURCE GREP. v2274 "fixed" register by preferring a _BOARD_WIN handle and
pinned it with a guard that read the source text. The guard was green for four versions while the
join it stood for did not exist: board_window() is spawned as a SEPARATE OS PROCESS, so the handle
lives in the child's interpreter and the HTTP server reads None every time. A pattern was present;
a path was not. [[the-unjoined-end]]

So this drives the REAL shipped block, extracted from bible.html, in node, against a fake store —
console writes the note, board drains it, and the assertions are about what ENDED UP in the inbox.
"""
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")
START = "var _hoRaw = window.LSR.getItem('d2r_chronicleHandoff');"
END = "  /* ══════════════════════════════════════════════════════════════════════════════════════════════\n     v1540 — CHRONICLE PHOTO INTAKE"


def _extract_drain():
    """The SHIPPED drain block, not a copy. A copy is a second thing that can drift."""
    with io.open(BIBLE, encoding="utf-8") as fh:
        s = fh.read()
    i = s.index(START)
    # walk back to the enclosing `try {` and forward to ITS OWN `} catch(e){}` — slicing to the
    # next section header instead left the try unclosed and node refused the whole harness with
    # "Unexpected end of input", which reads like a defect in the block rather than in the cut.
    k = s.rindex("try {", 0, i)
    e = s.index("} catch(e){}", i) + len("} catch(e){}")
    return s[k:e]


@unittest.skipIf(shutil.which("node") is None, "node not installed")
class TestTheHandoffActuallyLands(unittest.TestCase):
    def _run(self, store, times=1):
        """Run the real block `times` times over a fake LSR. -> the resulting store"""
        block = _extract_drain()
        harness = (
            "const store = JSON.parse(process.argv[2]);\n"
            "global.window = { LSR: {\n"
            "  getItem: k => (k in store ? store[k] : null),\n"
            "  setItem: (k, v) => { store[k] = String(v); },\n"
            "} };\n"
            "for (let i = 0; i < Number(process.argv[3]); i++) {\n"
            + block + "\n}\n"
            "process.stdout.write(JSON.stringify(store));\n"
        )
        d = tempfile.mkdtemp(prefix="handoff-")
        self.addCleanup(shutil.rmtree, d, True)
        hp = os.path.join(d, "h.js")
        with io.open(hp, "w", encoding="utf-8") as fh:
            fh.write(harness)
        out = subprocess.run([shutil.which("node"), hp, json.dumps(store), str(times)],
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, "the shipped drain block threw:\n%s" % out.stderr[:900])
        return json.loads(out.stdout)

    @staticmethod
    def _note(names, at=1788000000000):
        """Exactly what control_app's JS writes."""
        return json.dumps({"v": 1, "at": at, "from": "console", "n": len(names),
                           "proposal": {"wouldAdd": {"uniques": [{"name": n} for n in names],
                                                     "sets": []}, "held": [], "lanes": []},
                           "drained": None})

    def test_the_names_REACH_THE_INBOX(self):
        """The whole point. Not 'the code mentions the inbox' — the names are IN it."""
        st = self._run({"d2r_chronicleHandoff": self._note(["Windforce", "Stormlash"])})
        inbox = json.loads(st.get("d2r_chronicleInbox") or "[]")
        self.assertEqual(sorted(r["name"] for r in inbox), ["Stormlash", "Windforce"])
        self.assertTrue(all(r.get("src") == "console-handoff" for r in inbox),
                        "the rows do not say where they came from, so he cannot tell a console "
                        "proposal from something he added himself")

    def test_NOTHING_reaches_his_LEDGER(self):
        """⚠ THE LINE THAT MAY NEVER MOVE. v1523: the console never writes the grail. A handoff
        that wrote d2r_foundLog directly would be a SECOND write path into his ledger."""
        st = self._run({"d2r_chronicleHandoff": self._note(["Windforce"])})
        for k in ("d2r_foundLog", "d2r_owned", "d2r_setPieces"):
            self.assertNotIn(k, st, "the drain wrote %s — the board's own doors own that, and a "
                                    "second writer is a second thing that can drift" % k)

    def test_it_drains_ONCE_however_many_times_the_board_loads(self):
        st = self._run({"d2r_chronicleHandoff": self._note(["Windforce", "Stormlash"])}, times=5)
        inbox = json.loads(st.get("d2r_chronicleInbox") or "[]")
        self.assertEqual(len(inbox), 2, "five loads produced %d rows — the drain re-fires"
                                        % len(inbox))

    def test_a_name_he_DISMISSED_does_not_come_back(self):
        """★ THE LAW THE PREVIOUS TEST ONLY LOOKED LIKE IT WAS CHECKING. Draining five times in a
        row proves nothing on its own: the de-dupe against the CURRENT inbox absorbs the repeat, so
        the test stayed green with the drain-once condition sabotaged away.

        The failure that actually costs him something is a re-fire AFTER he has cleared the row —
        the name reappears in his inbox every time he opens the board, for ever, and no amount of
        dismissing it helps. That is what `drained` exists to prevent, and only this shape of test
        can see it. [[regression-guard]]"""
        first = self._run({"d2r_chronicleHandoff": self._note(["Windforce", "Stormlash"])})
        # he reads the inbox and dismisses both
        first["d2r_chronicleInbox"] = json.dumps([])
        again = self._run(first, times=3)
        self.assertEqual(json.loads(again.get("d2r_chronicleInbox") or "[]"), [],
                         "a proposal he had already cleared came back on the next board load")

    def test_the_stamp_is_the_RECORD_S_SHAPE_not_a_flag(self):
        """★ THE v2205 LESSON, APPLIED. A retired migration stamped a flag unconditionally and a
        destructive undo trusted its PRESENCE — it would have dropped 273 of his 280 owned names.
        So `drained` carries counts, which a stray write cannot forge."""
        st = self._run({"d2r_chronicleHandoff": self._note(["Windforce"])})
        d = (json.loads(st["d2r_chronicleHandoff"]) or {}).get("drained")
        self.assertIsInstance(d, dict, "drained is not a record — a bare flag is forgeable")
        self.assertEqual(d.get("n"), 1)
        self.assertEqual(d.get("offered"), 1)
        self.assertTrue(d.get("at"))

    def test_a_FORGED_flag_does_not_stop_a_real_drain(self):
        """The mirror of the above: if something writes drained:true or drained:{} with no counts,
        the proposal must still land rather than being silently swallowed."""
        note = json.loads(self._note(["Windforce"]))
        note["drained"] = {}                      # present, but proves nothing
        st = self._run({"d2r_chronicleHandoff": json.dumps(note)})
        inbox = json.loads(st.get("d2r_chronicleInbox") or "[]")
        self.assertEqual([r["name"] for r in inbox], ["Windforce"],
                         "an empty 'drained' object swallowed a real proposal")

    def test_it_does_not_duplicate_what_is_ALREADY_waiting(self):
        st = self._run({"d2r_chronicleHandoff": self._note(["Windforce", "Stormlash"]),
                        "d2r_chronicleInbox": json.dumps([{"name": "Windforce", "src": "reel"}])})
        inbox = json.loads(st["d2r_chronicleInbox"])
        self.assertEqual(len(inbox), 2)
        self.assertEqual(sum(1 for r in inbox if r["name"] == "Windforce"), 1)

    def test_an_EMPTY_proposal_changes_nothing(self):
        st = self._run({"d2r_chronicleHandoff": self._note([])})
        self.assertNotIn("d2r_chronicleInbox", st,
                         "an empty proposal created an inbox anyway")

    def test_garbage_in_the_key_does_not_throw(self):
        """A half-written record must not stop the board booting."""
        for junk in ("{not json", "null", "[]", '{"proposal":null}'):
            st = self._run({"d2r_chronicleHandoff": junk})
            self.assertIn("d2r_chronicleHandoff", st)


class TestBothEndsNameTheSameKey(unittest.TestCase):
    """⚠ THE JOINT ITSELF. Two halves that use different key names is precisely how register spent
    four versions looking wired and carrying nothing."""

    def test_the_writer_and_the_reader_agree(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            app = fh.read()
        with io.open(BIBLE, encoding="utf-8") as fh:
            b = fh.read()
        self.assertIn("'d2r_chronicleHandoff'", app,
                      "the console no longer writes the handoff key")
        self.assertIn("getItem('d2r_chronicleHandoff')", b,
                      "the board no longer reads the handoff key")
        self.assertIn("d2r_chronicleInbox", b)

    def test_the_console_still_PREFERS_calling_the_board_when_it_can(self):
        """Queueing is the fallback, not the plan. If a window ever does hold chronicleApply, it
        must be used — the queue costs him an extra step."""
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            app = fh.read()
        i = app.index("if(typeof window.chronicleApply==='function')")
        j = app.index("d2r_chronicleHandoff")
        self.assertLess(i, j, "the queue is attempted before the direct call — a console that CAN "
                              "apply directly should, and only fall back when it cannot")


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
