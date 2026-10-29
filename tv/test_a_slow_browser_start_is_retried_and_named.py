# -*- coding: utf-8 -*-
"""#161 (REG-3060) - A BROWSER THAT IS SLOW TO START IS GIVEN ITS GRACE, ONE THAT WILL NOT START IS TRIED ONCE MORE ON A
FRESH PORT AND PROFILE, AND EITHER WAY THE LAUNCHER SAYS WHY.

MEASURED on CI 2026-10-29: test_found_ever_never_files_to_a_mule went red twice, "Chrome is INSTALLED at
/usr/bin/google-chrome and would not start on :51565" (v3837's first grade) and ":59361" (v3838), each FAILED
(failures=1): only the FIRST case failed, and the five after it found that same browser answering and passed. So the
browser was alive and slow under the shard's load; render_check._chrome_up() gave up after 20 s, left it running, and
threw its output to DEVNULL, so no log said why. test_the_rails_fold_is_a_chevron_not_a_dot did the same on :37209.

Now _chrome_up() gives a start that is ALIVE and silent a grace; a start that exited, or is still silent after its
grace, is killed through its handle and tried ONCE more on a fresh port and a fresh profile (a Popen that raises is
not retried - a new port cannot fix a missing binary); Chrome's stderr is kept in the profile; every start is recorded
and chrome_start_why() says it. The nine browser laws that raised a plain AssertionError now call require_chrome(),
which raises a VenueFault naming that cause - read by run_gates as VENUE (UNKNOWN), never as a red
(tv/test_a_law_that_cannot_measure_is_unknown_never_red.py). The worst-case start fits every such law's gate timeout.

Driven: _chrome_up() through its seams (a fake Popen whose process lives, exits or never answers; a fake DevTools
probe; no sleep; a fixed fresh port) - no browser is started. RED_PROOF below.
"""
import io
import os
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

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
import render_check as RC  # noqa: E402
import run_gates as RG  # noqa: E402

BROWSER_LAWS = ("test_a_roster_name_opens_its_row_with_the_eyes", "test_a_sweep_never_reticks_what_he_unticked",
                "test_found_ever_never_files_to_a_mule", "test_the_character_builder_fits_at_every_width",
                "test_the_fleet_card_says_how_each_pc_films_and_drains", "test_the_fleet_row_keeps_its_name_whole",
                "test_the_mule_window_fits_at_every_width", "test_the_rails_fold_is_a_chevron_not_a_dot",
                "test_the_vault_tab_lock_never_sits_on_its_label")


class _Proc(object):
    def __init__(self, exit_code=None, said=b"", stderr=None):
        self.exit_code, self.killed, self.args = exit_code, False, None
        if said and stderr is not None and hasattr(stderr, "write"):
            stderr.write(said)
            stderr.flush()

    def poll(self):
        return self.exit_code

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        return 0


class _Fixture(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="slow-start-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        binary = os.path.join(self.tmp, "chrome")
        with io.open(binary, "w") as fh:
            fh.write("#")
        saved = (RC.PORT, os.environ.get("TV_RENDER_PORT"), RC._CHROME_PROC, RC._CHROME_PROFILE)

        def restore():
            RC.PORT = saved[0]
            if saved[1] is None:
                os.environ.pop("TV_RENDER_PORT", None)
            else:
                os.environ["TV_RENDER_PORT"] = saved[1]
            RC._CHROME_PROC, RC._CHROME_PROFILE = saved[2], saved[3]
        self.addCleanup(restore)
        for name, val in (("CHROME", binary), ("_sweep_dead_profiles", lambda: None)):
            p = mock.patch.object(RC, name, val)
            p.start()
            self.addCleanup(p.stop)
        RC.PORT = 41001
        self.procs, self.ports, self.profiles = [], [], []

    def popen(self, plan):
        """plan: one (exit_code, stderr bytes) per start, in order"""
        plan = list(plan)

        def popen(args, stdout=None, stderr=None):
            code, said = plan.pop(0)
            pr = _Proc(code, said, stderr)
            pr.args = list(args)
            self.procs.append(pr)
            self.ports.append(RC.PORT)
            self.profiles.append(RC._CHROME_PROFILE)
            return pr
        return popen

    def up(self, plan, answer_after=None, answer_port=None):
        """answer_after: polls of one start before its port answers (None: never); answer_port: only that port answers"""
        polls = {}

        def answers(port):
            if not self.procs:
                return False
            if answer_port is not None and port != answer_port:
                return False
            polls[port] = polls.get(port, 0) + 1
            return answer_after is not None and polls[port] > answer_after
        return RC._chrome_up(popen=self.popen(plan), answers=answers, sleep=lambda s: None,
                             free_port=lambda: 51002)


class ASlowStartIsGivenItsGrace(_Fixture):

    def test_an_alive_start_that_answers_inside_its_grace_is_kept(self):
        polls = int(RC.CHROME_START_WAIT_S / 0.5) + 5          # past the first wait, inside the grace
        self.assertTrue(self.up([(None, b"")], answer_after=polls))
        self.assertEqual(len(self.procs), 1, "a slow but living browser was killed and started again")
        self.assertFalse(self.procs[0].killed)
        self.assertIn("slow start", RC._CHROME_START["attempts"][0]["cause"])

    def test_a_start_still_silent_after_its_grace_is_tried_once_more_on_a_fresh_port_and_profile(self):
        self.assertTrue(self.up([(None, b""), (None, b"")], answer_after=0, answer_port=51002))
        self.assertEqual(len(self.procs), 2)
        self.assertTrue(self.procs[0].killed, "the first browser was left running")
        self.assertEqual(self.ports, [41001, 51002])
        self.assertEqual((RC.PORT, os.environ.get("TV_RENDER_PORT")), (51002, "51002"),
                         "the retry's port is not the one the law and its children now read")
        self.assertNotEqual(self.profiles[0], self.profiles[1], "the retry reused the first profile")
        self.assertFalse(os.path.isdir(self.profiles[0]), "the first start's profile was left behind")
        self.assertIn("was alive and never answered", RC._CHROME_START["attempts"][0]["cause"])
        RC._chrome_down()

    def test_a_start_that_exits_is_named_with_what_it_said_and_tried_once_more(self):
        said = b"[0101/000000.000:ERROR:devtools_http_handler.cc] Cannot start http server for devtools.\n" \
               b"bind() failed: Address already in use (98)\n"
        self.assertFalse(self.up([(1, said), (1, said)]))
        self.assertEqual(len(self.procs), 2, "an exited start was not tried again")
        why = RC.chrome_start_why() or ""
        self.assertIn(":41001 exited with code 1", why)
        self.assertIn(":51002 exited with code 1", why)
        self.assertIn("Address already in use", why, "the cause Chrome printed never reached the reason: %r" % why)
        self.assertIsNone(RC._CHROME_PROFILE, "a failed start kept its profile")

    def test_a_launch_that_raises_is_said_and_not_retried(self):
        def popen(args, stdout=None, stderr=None):
            self.procs.append(args)
            raise OSError("exec format error")
        self.assertFalse(RC._chrome_up(popen=popen, answers=lambda p: False, sleep=lambda s: None,
                                       free_port=lambda: 51002))
        self.assertEqual(len(self.procs), 1)
        self.assertIn("could not be launched (OSError: exec format error)", RC.chrome_start_why() or "")

    def test_a_browser_already_answering_is_used_and_nothing_is_started(self):
        started = []
        self.assertTrue(RC._chrome_up(popen=lambda *a, **k: started.append(a), answers=lambda p: True,
                                      sleep=lambda s: None))
        self.assertEqual(started, [])


class ALawThatCannotGetItsBrowserIsAVenueFault(_Fixture):

    def test_require_chrome_names_the_cause_as_a_venue_fault(self):
        # REG-3119: a VenueFault is for an INSTALLED Chrome that would not start - any existing file stands in for its
        # binary here, so the case holds on a machine with no Chrome too (an absent one is a red, its own law's case)
        with mock.patch.object(RC, "_chrome_up", lambda: False), mock.patch.object(RC, "CHROME", sys.executable):
            RC._CHROME_START.update(attempts=[], why=":41001 was alive and never answered /json/version in 40 s")
            with self.assertRaises(RC.VenueFault) as cm:
                RC.require_chrome()
        msg = str(cm.exception)
        self.assertIsInstance(cm.exception, AssertionError, "PREMISE: a VenueFault still fails a case that ignores it")
        self.assertIn(RC.VENUE_MARK, msg)
        self.assertIn("never answered /json/version in 40 s", msg)
        with mock.patch.object(RC, "_chrome_up", lambda: True):
            self.assertTrue(RC.require_chrome())

    def test_the_mark_is_the_one_the_gate_set_reads(self):
        self.assertEqual(RC.VENUE_MARK, RG.VENUE_MARK)

    def test_every_browser_law_asks_through_require_chrome(self):
        plain = re.compile(r"if not RC\._chrome_up\(\):\s*\n(?:\s*[^\n]*\n)?\s*raise AssertionError")
        for name in BROWSER_LAWS:
            with io.open(os.path.join(HERE, name + ".py"), encoding="utf-8") as fh:
                src = fh.read()
            with self.subTest(law=name):
                self.assertIn("RC.require_chrome()", src, "%s no longer asks for its browser the venue way" % name)
                self.assertIsNone(plain.search(src), "%s reads a browser that will not start as a red again" % name)

    def test_the_worst_start_fits_every_browser_laws_gate(self):
        worst = RC.CHROME_START_WAIT_S + RC.CHROME_START_GRACE_S + RC.CHROME_RETRY_WAIT_S
        gates = dict((g.name, g.timeout) for g in RG.GATES)
        for name in BROWSER_LAWS:
            with self.subTest(law=name):
                self.assertIn(name, gates, "PREMISE: %s is a registered gate" % name)
                self.assertGreaterEqual(gates[name], worst + 45,
                                        "%s's gate (%ss) would time out - a red - while its browser is still starting"
                                        % (name, gates[name]))


RED_PROOF = [
    {"why": "REG-3060 - a slow but living start is killed at 20 s instead of given its grace",
     "file": "render_check.py",
     "find": "    while waited < wait_s + grace_s:\n",
     "replace": "    while waited < wait_s:\n",
     "matches": 1},
    {"why": "REG-3060 - a start that never answered is not tried again",
     "file": "render_check.py",
     "find": "    for n, (wait_s, grace_s) in enumerate(((CHROME_START_WAIT_S, CHROME_START_GRACE_S), (CHROME_RETRY_WAIT_S, 0.0))):\n",
     "replace": "    for n, (wait_s, grace_s) in enumerate(((CHROME_START_WAIT_S, CHROME_START_GRACE_S),)):\n",
     "matches": 1},
    {"why": "REG-3060 - the retry reuses the port the first start could not answer on",
     "file": "render_check.py",
     "find": "            PORT = free_port()                       # REG-3060 - the retry's own port; a child reads the same one\n",
     "replace": "            pass\n",
     "matches": 1},
    {"why": "REG-3060 - a failed start's browser is left running beside the retry",
     "file": "render_check.py",
     "find": "        _chrome_down()                               # this start's browser (by its handle) and its profile go\n",
     "replace": "        pass\n",
     "matches": 1},
    {"why": "REG-3060 - what Chrome printed never reaches the reason (its stderr thrown away again)",
     "file": "render_check.py",
     "find": "            stdout=subprocess.DEVNULL, stderr=fh)\n",
     "replace": "            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n",
     "matches": 1},
    {"why": "REG-3060 - nothing says why the browser did not come",
     "file": "render_check.py",
     "find": "    _CHROME_START[\"why\"] = \"; \".join(\":%d %s\" % (a[\"port\"], a[\"cause\"]) for a in _CHROME_START[\"attempts\"])\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-3060 - a launch that raises is retried on a new port (which cannot fix it)",
     "file": "render_check.py",
     "find": "        if not launched:\n            break\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-3061 - require_chrome fails as a plain assertion, read as a red",
     "file": "render_check.py",
     "find": "    raise VenueFault(\"\\u26aa %s. This law could not measure on this venue: UNKNOWN, not a red.\" % words)",
     "replace": "    raise AssertionError(\"\\u26aa %s. This law could not measure on this venue: UNKNOWN, not a red.\" % words)",
     "matches": 1},
    {"why": "REG-3061 - a browser law reads a browser that will not start as a red again",
     "file": "test_found_ever_never_files_to_a_mule.py",
     "find": "        RC.require_chrome()   # REG-3061 - a browser that will not start is UNKNOWN for this law (a VenueFault), never a red\n",
     "replace": "        if not RC._chrome_up():\n            raise AssertionError(\"Chrome would not start\")\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
