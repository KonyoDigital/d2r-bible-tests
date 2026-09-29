# -*- coding: utf-8 -*-
"""#83 (REG-1515) — THE CHILD SUPERVISOR: ONE TREE PER ROLE, VERIFIED, AND A REUSED PID IS NEVER OURS.

His words, 2026-09-29, after five capture_win.ps1 leaked at once and crashed his Boosteroid: *"have a logic coded
for this so it bypasses it - architecture something smart to make the ascending of the reel sessions smooth"*.

tv/child_guard.py is that architecture; every joint below is DRIVEN through the real code:
  · the door, on REAL processes (POSIX, this machine's own temp processes): a fake role that spawns a grandchild is
    started twice through spawn(); after the second start exactly one tree is alive - the first parent AND its
    grandchild are gone - and end() ends the survivor's tree too;
  · a pid the OS reused is never ours: a record whose creation time no longer matches is dropped, not killed, and an
    UNKNOWN birth ends nothing;
  · Windows: the Job Object is created with KILL_ON_JOB_CLOSE, the child is assigned to it, and end() terminates the
    job and closes the handle - driven with a fake kernel32 on this Mac; a failed assignment is said and falls back;
  · the watchdog ends the recorded children of dead parents (verified by birth) and the UNRECORDED processes of
    known roles whose parent is gone or ours; a stranger's child is counted, never ended; an unreadable table is
    UNKNOWN, ends nothing, and owes None - never 0;
  · the census by family and the doctor's one_of_each row (through the real control_app function);
  · the memory policy: under the floor no secondary worker, UNKNOWN free RAM never refuses;
  · the console: _start_capture through the door ends a capture the lamp lost track of (the five-captures shape,
    replayed through the real _start_capture/_stop_capture with the Windows edges stubbed - never a real process);
  · the agent: VisionWorker and OcrWorker spawn/stop through the door, the stall reader releases its claude after
    each sweep, and neither the stall drain nor OCR starts a worker under the RAM floor.
Fake pids are >= 9990001: past macOS's pid ceiling (99998) and Linux's default pid_max (4194304), and every OS
door (kill / alive / birth / kernel32) is stubbed, so no law here ever touches a real pid it did not start.
RED_PROOF below. [[feedback-fixtures-never-touch-live-data]] [[unknown-stays-unknown]] [[heart-first]]
"""
import ctypes
import inspect
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
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
import child_guard as cg  # noqa: E402
import control_app as ca  # noqa: E402

os.environ["TV_PORT"] = "17973"          # never a live agent's port (test_agent holds 17971)
import tv_diablo as tv  # noqa: E402
tv.JOURNAL = os.path.join(tempfile.gettempdir(), "tvd_child_guard_law_journal.jsonl")   # never the real journal

IS_POSIX = sys.platform != "win32"


class _FakeProc(object):
    """A child that is alive while its pid is in `live`. Never a real process."""

    def __init__(self, pid, live, handle=None):
        self.pid, self._live, self._handle = pid, live, handle
        self.stdin = self.stdout = self.stderr = None
        self.killed = 0

    def poll(self):
        return None if self.pid in self._live else 1

    def kill(self):
        self.killed += 1
        self._live.discard(self.pid)

    def wait(self, timeout=None):
        return self.poll()


class _World(unittest.TestCase):
    """A private ledger dir, an empty door, every OS door stubbed to a recorder."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="child_guard_law_")
        self.live = set()
        self.births = {}
        self.killed = []
        self.saved = (cg.LEDGER_DIR, dict(cg._LIVE), dict(cg._EXPECT), dict(cg.RECEIPT), dict(cg.WATCHDOG),
                      dict(cg.RAM), cg._SELF_BIRTH)
        cg.LEDGER_DIR = os.path.join(self.d, "ledger")
        cg._LIVE.clear()
        cg._EXPECT.clear()
        cg.WATCHDOG.update(on=True, worked=None, lastTs=None, owed=None, ended=[], kept=[], failed=[], strangers=[],
                           unknown=None, say="the watchdog has not ticked yet")
        cg.RECEIPT.update(spawns=0, ends=0, survivors=0, reused=0, worked=None, lastTs=None, owed=None)
        cg._SELF_BIRTH = 100
        self.stack = [
            mock.patch.object(cg, "_alive_default", self.alive),
            mock.patch.object(cg, "_birth_default", self.birth),
            mock.patch.object(cg, "_kill_tree_default", self.kill_tree),
        ]
        for p in self.stack:
            p.start()

    def tearDown(self):
        for p in reversed(self.stack):
            p.stop()
        cg.LEDGER_DIR = self.saved[0]
        cg._LIVE.clear(); cg._LIVE.update(self.saved[1])
        cg._EXPECT.clear(); cg._EXPECT.update(self.saved[2])
        cg.RECEIPT.clear(); cg.RECEIPT.update(self.saved[3])
        cg.WATCHDOG.clear(); cg.WATCHDOG.update(self.saved[4])
        cg.RAM.clear(); cg.RAM.update(self.saved[5])
        cg._SELF_BIRTH = self.saved[6]
        shutil.rmtree(self.d, ignore_errors=True)

    def alive(self, pid):
        return pid in self.live

    def birth(self, pid):
        return self.births.get(pid)

    def kill_tree(self, rec):
        self.killed.append(rec.get("pid"))
        self.live.discard(rec.get("pid"))
        return "stub"

    def kill(self, pid):
        self.killed.append(pid)
        self.live.discard(pid)

    def popen(self, pids, handle=None):
        it = iter(pids)

        def _popen(argv, **kw):
            p = _FakeProc(next(it), self.live, handle=handle)
            self.live.add(p.pid)
            self.births[p.pid] = 1000
            self.spawned.append((p.pid, list(argv), dict(kw)))
            return p
        self.spawned = []
        return _popen


# ── 1. the door on real processes ────────────────────────────────────────────────────────────────────────────

FAKE_ROLE = r'''
import subprocess, sys, time
gc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
with open(sys.argv[1], "w") as fh:
    fh.write(str(gc.pid))
time.sleep(120)
'''


def _pid_alive_real(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _gone(pid, within_s=5.0):
    deadline = time.time() + within_s
    while time.time() < deadline:
        if not _pid_alive_real(pid):
            return True
        time.sleep(0.05)
    return not _pid_alive_real(pid)


@unittest.skipUnless(IS_POSIX, "the POSIX tree (own session + killpg) is proven where it runs; Windows has the job law")
class TheDoorLeavesOneTreePerRole(unittest.TestCase):
    """REAL processes of this law's own: a fake role that spawns a grandchild, started twice through the door."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="child_guard_tree_")
        self.saved = (cg.LEDGER_DIR, dict(cg._LIVE), dict(cg.RECEIPT), cg._SELF_BIRTH)
        cg.LEDGER_DIR = os.path.join(self.d, "ledger")
        cg._LIVE.clear()
        cg._SELF_BIRTH = None
        self.fake = os.path.join(self.d, "fake_role.py")
        with io.open(self.fake, "w", encoding="utf-8") as fh:
            fh.write(FAKE_ROLE)
        self.mine = []

    def tearDown(self):
        for pid in self.mine:                       # never leave a process of ours behind, whatever the verdict
            try:
                os.killpg(int(pid), 9)
            except Exception:
                pass
            try:
                os.kill(int(pid), 9)
            except Exception:
                pass
        cg._LIVE.clear(); cg._LIVE.update(self.saved[1])
        cg.RECEIPT.clear(); cg.RECEIPT.update(self.saved[2])
        cg.LEDGER_DIR, cg._SELF_BIRTH = self.saved[0], self.saved[3]
        shutil.rmtree(self.d, ignore_errors=True)

    def _tree(self, n):
        pf = os.path.join(self.d, "gc%d.pid" % n)
        p = cg.spawn("law-fake", [sys.executable, self.fake, pf], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.mine.append(p.pid)
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                with io.open(pf) as fh:
                    gc = int(fh.read().strip())
                break
            except Exception:
                time.sleep(0.05)
        else:
            self.fail("premise: the fake role never reported its grandchild")
        self.mine.append(gc)
        self.assertTrue(_pid_alive_real(gc), "premise: the grandchild is alive")
        return p, gc

    def test_a_restart_leaves_exactly_one_tree_and_end_ends_it(self):
        p1, g1 = self._tree(1)
        rec = cg.record_of("law-fake")
        self.assertEqual((p1.pid, os.getpid(), True), (rec["pid"], rec["parent"], rec["session"]),
                         "the record does not say whose child this is, or it does not lead its own session: %r" % rec)
        self.assertIsNotNone(rec["birth"], "the child's creation time was not read - a reused pid could never be told")
        p2, g2 = self._tree(2)
        self.assertTrue(_gone(p1.pid), "the first parent outlived the restart")
        self.assertTrue(_gone(g1), "THE GRANDCHILD SURVIVED THE RESTART - the tree was not ended, only its head; this "
                                   "is the leak that stacked five captures on the ALT")
        self.assertIsNone(p2.poll(), "the restarted role is not running")
        self.assertTrue(_pid_alive_real(g2), "the new tree's grandchild is not running")
        self.assertEqual(p2.pid, cg.record_of("law-fake")["pid"])
        self.assertEqual((2, 1), (cg.RECEIPT["spawns"], cg.RECEIPT["ends"]), "the receipt did not count the restart")
        with io.open(os.path.join(cg.LEDGER_DIR, "%d.json" % os.getpid())) as fh:
            ledger = json.load(fh)
        self.assertEqual(p2.pid, ledger["children"]["law-fake"]["pid"], "the ledger does not carry the live record")
        r = cg.end("law-fake")
        self.assertTrue(r["ended"], "end() did not see the tree go: %r" % r)
        self.assertTrue(_gone(p2.pid) and _gone(g2), "end() left part of the tree alive")
        self.assertIsNone(cg.record_of("law-fake"))
        with io.open(os.path.join(cg.LEDGER_DIR, "%d.json" % os.getpid())) as fh:
            self.assertNotIn("law-fake", json.load(fh)["children"], "the ledger still names an ended role")


# ── 2. a reused pid is never ours ────────────────────────────────────────────────────────────────────────────

class AReusedPidIsNeverOurs(_World):

    def _previous_life(self, pid=9990011, birth=1000):
        # a record with no Popen of ours (a previous console's, read back from a ledger)
        cg._LIVE["capture"] = {"role": "capture", "pid": pid, "birth": birth, "parent": 9990009, "parentBirth": 50,
                               "argv0": "powershell.exe", "ts": 1, "session": False, "job": None, "proc": None}
        self.live.add(pid)

    def test_a_pid_born_at_another_time_is_dropped_not_killed(self):
        self._previous_life()
        self.births[9990011] = 5000                  # alive, but born later: Windows handed the pid to a browser
        r = cg.end("capture", kill=self.kill)
        self.assertEqual([], self.killed, "A REUSED PID WAS KILLED - that process was never ours")
        self.assertIn("reused", r["say"])
        self.assertIsNone(cg.record_of("capture"), "the stranger's pid is still recorded as ours")
        self.assertEqual(1, cg.RECEIPT["reused"])

    def test_an_unknown_birth_ends_nothing(self):
        self._previous_life()
        self.births.pop(9990011, None)               # the reader could not answer
        r = cg.end("capture", kill=self.kill)
        self.assertEqual([], self.killed, "a pid whose birth could not be read was ended on a guess")
        self.assertIn("never ended on a guess", r["say"])

    def test_a_pid_born_when_recorded_is_ours_and_ended(self):
        self._previous_life()
        self.births[9990011] = 1001                  # one second off: `ps -o lstart` resolution
        r = cg.end("capture", kill=self.kill, wait_s=0.5)
        self.assertEqual([9990011], self.killed)
        self.assertTrue(r["ended"])

    def test_our_own_exited_child_is_forgotten_without_a_kill(self):
        cg.spawn("ocr", ["x"], popen=self.popen([9990021]), kill=self.kill)
        self.live.discard(9990021)                    # it exited by itself
        r = cg.end("ocr", kill=self.kill)
        self.assertEqual([], self.killed)
        self.assertIn("already exited", r["say"])
        self.assertIsNone(cg.record_of("ocr"))


# ── 3. the Windows job object ────────────────────────────────────────────────────────────────────────────────

class _FakeKernel32(object):
    """Records every call the door makes; the structure handed to SetInformationJobObject is read back."""

    def __init__(self, assign_ok=True):
        self.calls = []
        self.assign_ok = assign_ok
        self.flags = None
        self.info_class = None
        self.info_size = None

    def CreateJobObjectW(self, a, b):
        self.calls.append(("CreateJobObjectW", a, b))
        return 77

    def SetInformationJobObject(self, job, cls, ref, size):
        obj = getattr(ref, "_obj", None)
        self.flags = obj.BasicLimitInformation.LimitFlags if obj is not None else None
        self.info_class, self.info_size = cls, size
        self.calls.append(("SetInformationJobObject", job, cls))
        return 1

    def AssignProcessToJobObject(self, job, handle):
        self.calls.append(("AssignProcessToJobObject", job, handle))
        return 1 if self.assign_ok else 0

    def TerminateJobObject(self, job, code):
        self.calls.append(("TerminateJobObject", job, code))
        return 1

    def CloseHandle(self, h):
        self.calls.append(("CloseHandle", h))
        return 1

    def GetLastError(self):
        return 5


class TheWindowsJobObject(_World):

    def _spawn(self, k32):
        with mock.patch.object(cg, "IS_WIN", True), mock.patch.object(cg, "_kernel32", lambda: k32):
            p = cg.spawn("capture", ["powershell.exe"], popen=self.popen([9990031], handle=4242), kill=self.kill)
            rec = cg.record_of("capture")
            return p, rec

    def test_the_child_is_put_in_a_job_that_kills_on_close(self):
        k32 = _FakeKernel32()
        p, rec = self._spawn(k32)
        self.assertEqual(cg.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE, k32.flags,
                         "the job was created WITHOUT JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE (flags %r) - a grandchild "
                         "would outlive the handle, and the console's death would end nothing" % (k32.flags,))
        self.assertEqual(cg.JobObjectExtendedLimitInformation, k32.info_class)
        # sizeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION): 144 on 64-bit Windows, 112 on 32-bit - the SDK's numbers
        self.assertEqual(144 if ctypes.sizeof(ctypes.c_void_p) == 8 else 112, k32.info_size,
                         "the extended limit structure is not laid out as Windows expects (size %r)" % k32.info_size)
        self.assertIn(("AssignProcessToJobObject", 77, 4242), k32.calls, "the child was never assigned to the job")
        self.assertIn("KILL_ON_JOB_CLOSE", rec["jobSay"])
        self.assertNotIn("start_new_session", self.spawned[0][2], "a Windows spawn was handed a POSIX-only kwarg")

    def test_end_terminates_the_job_and_closes_the_handle(self):
        k32 = _FakeKernel32()
        self._spawn(k32)
        with mock.patch.object(cg, "IS_WIN", True), mock.patch.object(cg, "_kernel32", lambda: k32), \
                mock.patch.object(cg, "_kill_tree_default", self.saved_kill_tree()):
            r = cg.end("capture", wait_s=0)
        self.assertIn(("TerminateJobObject", 77, 1), k32.calls,
                      "end() did not terminate the job - the grandchildren (conhost, node helpers) live on")
        self.assertIn(("CloseHandle", 77), k32.calls, "the job handle leaked")
        self.assertEqual("job", r["how"])
        self.assertEqual([], self.killed, "the pid kill ran beside the job kill - two kills for one tree")

    def saved_kill_tree(self):
        # the REAL _kill_tree_default, but with taskkill (the no-job fallback) never reachable: this law's records
        # all hold a job, so the job branch is what runs
        real = self.stack[2].temp_original

        def _kt(rec):
            self.assertTrue(rec.get("job"), "the fallback taskkill would have run on a fake pid")
            return real(rec)
        return _kt

    def test_a_failed_assignment_is_said_and_the_pid_kill_is_the_fallback(self):
        k32 = _FakeKernel32(assign_ok=False)
        p, rec = self._spawn(k32)
        self.assertIsNone(cg._LIVE["capture"]["job"], "a job that failed to take is still held")
        self.assertIn("taskkill /T is the fallback", rec["jobSay"])
        self.assertIn(("CloseHandle", 77), k32.calls, "the unused job handle leaked")
        with mock.patch.object(cg, "IS_WIN", True), mock.patch.object(cg, "_kernel32", lambda: k32):
            r = cg.end("capture", kill=self.kill, wait_s=0)
        self.assertEqual([9990031], self.killed, "without a job, the caller's pid kill must still run")
        self.assertNotIn(("TerminateJobObject", 77, 1), k32.calls)


# ── 4. the watchdog ──────────────────────────────────────────────────────────────────────────────────────────

def _cap_cmd():
    return "powershell.exe -NoProfile -File " + os.path.join(HERE, "capture_win.ps1")


class TheWatchdogEndsOnlyWhatIsOurs(_World):

    def _ledger(self, parent, pborn, children):
        os.makedirs(cg.LEDGER_DIR, exist_ok=True)
        with io.open(os.path.join(cg.LEDGER_DIR, "%d.json" % parent), "w", encoding="utf-8") as fh:
            json.dump({"parent": parent, "parentBirth": pborn, "expect": {}, "children": children}, fh)

    def test_dead_parents_children_are_ended_by_birth_and_strangers_kept(self):
        self._ledger(9990099, 100, {"capture": {"role": "capture", "pid": 9990101, "birth": 1000, "session": True},
                                    "ocr": {"role": "ocr", "pid": 9990103, "birth": 1000, "session": True}})
        self._ledger(9990555, 100, {"capture": {"role": "capture", "pid": 9990105, "birth": 1000, "session": True}})
        # THIS process is alive (it is): with it dead, the 'unrecorded child of ours' branch went blind in the drill -
        # the orphan fallback ended 9990202 for the wrong reason. [[sabotage-is-usually-the-wrong-one]]
        self.live.update({9990101, 9990103, 9990105, 9990555, 9990777, 9990888, 9990201, 9990202, 9990203, 9990205,
                          os.getpid()})
        self.births.update({9990101: 1000, 9990103: 7777, 9990105: 1000, 9990555: 100, 9990888: 900})
        rows = [
            (9990201, 999998, 1000, _cap_cmd()),          # unrecorded, parent dead: an orphan
            (9990202, os.getpid(), 1000, _cap_cmd()),     # unrecorded child of THIS process
            (9990203, 9990777, 1000, _cap_cmd()),         # unrecorded, parent alive and not ours: a stranger's
            (9990204, 9990777, 1000, "python tv_diablo.py --watch " + HERE),   # not a known role
            (9990205, 9990888, 500, _cap_cmd()),          # parent born AFTER it: a reused parent pid, orphan
            (9990105, 9990555, 1000, _cap_cmd()),         # recorded by a live parent's ledger
        ]
        st = cg.watchdog_tick(rows_fn=lambda: rows, kill=self.kill, alive=self.alive, birth=self.birth, now_ms=1,
                              settle_s=0.3)
        self.assertEqual({9990101, 9990201, 9990202, 9990205}, set(self.killed),
                         "the watchdog ended the wrong set: %r (say %r)" % (sorted(self.killed), st["say"]))
        self.assertEqual([9990203], [s[0] for s in st["strangers"]], "another console's capture was ended or lost")
        self.assertIn(9990103, [k[0] for k in st["kept"]], "the reused pid was not said")
        self.assertIn("reused", [k[2] for k in st["kept"] if k[0] == 9990103][0])
        self.assertIn(9990105, [k[0] for k in st["kept"]], "a live parent's recorded child was not kept")
        self.assertEqual((0, True), (st["owed"], st["worked"]))
        self.assertFalse(os.path.exists(os.path.join(cg.LEDGER_DIR, "9990099.json")),
                         "the dead parent's ledger was not removed once its children were ended")
        self.assertTrue(os.path.exists(os.path.join(cg.LEDGER_DIR, "9990555.json")), "a live parent's ledger was removed")

    def test_an_unreadable_table_ends_nothing_and_owes_none(self):
        self.live.update({9990301, 9990777})
        st = cg.watchdog_tick(rows_fn=lambda: None, kill=self.kill, alive=self.alive, birth=self.birth, now_ms=1)
        self.assertEqual([], self.killed)
        self.assertIsNone(st["owed"], "an unreadable table read as 'nothing owed' (0) - UNKNOWN is not 0")
        self.assertTrue(st["unknown"])
        self.assertIn("UNKNOWN", st["say"])

    def test_a_kill_that_would_not_land_is_owed(self):
        self.live.update({9990401})
        rows = [(9990401, 999998, 1000, _cap_cmd())]
        st = cg.watchdog_tick(rows_fn=lambda: rows, kill=lambda pid: None, alive=self.alive, birth=self.birth,
                              now_ms=1, settle_s=0.2)
        self.assertEqual(1, st["owed"])
        self.assertFalse(st["worked"])
        self.assertEqual([9990401], [f[0] for f in st["failed"]])

    def test_the_role_of_a_command_line(self):
        self.assertEqual("capture", cg.role_of_command(_cap_cmd()))
        self.assertEqual("vision", cg.role_of_command("node claude -p --input-format stream-json --output-format "
                                                      "stream-json --add-dir " + HERE + "/frames"))
        self.assertEqual("ocr", cg.role_of_command(HERE + "/bin/ocr_mac --worker"))
        self.assertIsNone(cg.role_of_command("python " + HERE + "/tv_diablo.py --watch"))
        self.assertIsNone(cg.role_of_command("claude -p something " + HERE), "a plain claude session is not a role")


# ── 5. the census and the doctor row ─────────────────────────────────────────────────────────────────────────

class TheCensusAndTheDoctorRow(_World):

    def _ledger(self, parent, children, expect=None):
        os.makedirs(cg.LEDGER_DIR, exist_ok=True)
        with io.open(os.path.join(cg.LEDGER_DIR, "%d.json" % parent), "w", encoding="utf-8") as fh:
            json.dump({"parent": parent, "parentBirth": 100, "expect": expect or {}, "children": children}, fh)

    def test_two_captures_across_two_parents_is_over_the_ceiling(self):
        self._ledger(9990555, {"capture": {"role": "capture", "pid": 9990105, "birth": 1000}})
        self._ledger(9990556, {"capture": {"role": "capture", "pid": 9990106, "birth": 1000}})
        self.live.update({9990105, 9990106})
        c = cg.census(alive=self.alive)
        self.assertFalse(c["families"]["capture"]["ok"], "two live captures read OK: %r" % c["families"]["capture"])
        self.assertFalse(c["ok"])
        row = ca._one_of_each_check(alive=self.alive)
        self.assertFalse(row["ok"], "the doctor row read OK with two captures alive: %r" % row)
        self.assertIn("capture: 2 alive", row["detail"])
        self.assertIn("Task Manager", row.get("fix") or "")

    def test_the_agents_pool_ceiling_comes_from_its_ledger(self):
        self._ledger(9990557, {"vision-r0": {"role": "vision-r0", "pid": 9990110, "birth": 1000},
                               "vision-r1": {"role": "vision-r1", "pid": 9990111, "birth": 1000}},
                     expect={"vision": [0, 2]})
        self.live.update({9990110, 9990111})
        c = cg.census(alive=self.alive)
        self.assertTrue(c["families"]["vision"]["ok"], "a two-reader pool the agent declared read as over the ceiling")
        self.assertEqual([0, 2], c["families"]["vision"]["expected"])
        self.assertTrue(ca._one_of_each_check(alive=self.alive)["ok"])

    def test_a_clean_console_is_ok_and_an_unknown_watchdog_is_not(self):
        row = ca._one_of_each_check(alive=self.alive)
        self.assertTrue(row["ok"], "nothing recorded and no watchdog yet read as a fault: %r" % row)
        self.assertIn("watchdog not run yet", row["detail"])
        cg.WATCHDOG.update(lastTs=1, unknown=True, say="UNKNOWN - the process table could not be asked")
        row = ca._one_of_each_check(alive=self.alive)
        self.assertFalse(row["ok"], "an UNKNOWN table read OK - orphans could film behind a green row")
        self.assertIn("UNKNOWN", row["detail"])

    def test_a_would_not_end_warns_only_while_it_lives(self):
        cg.WATCHDOG.update(lastTs=1, unknown=False, failed=[(9990401, "capture", "would not end")], say="1 would not end")
        self.live.add(9990401)
        self.assertFalse(ca._one_of_each_check(alive=self.alive)["ok"])
        self.live.discard(9990401)
        row = ca._one_of_each_check(alive=self.alive)
        self.assertTrue(row["ok"], "the row kept warning about a pid that left: %r" % row)
        self.assertIn("has since left", row["detail"])

    def test_the_doctor_the_rescue_loop_and_status_carry_it(self):
        self.assertIn("_one_of_each_check", ca.doctor_payload.__code__.co_names, "doctor_payload no longer asks the row")
        loop = inspect.getsource(ca._console_rescue_loop)
        self.assertIn("_child_guard_tick()", loop, "nothing runs the watchdog")
        self.assertIn('"childGuard": _child_guard_status()', inspect.getsource(ca))
        self.assertEqual({"door", "watchdog", "ram"}, set(ca._child_guard_status()))

    def test_the_console_tick_uses_its_own_doors_and_never_raises(self):
        with mock.patch.object(cg, "watchdog_tick", lambda **k: (_ for _ in ()).throw(RuntimeError("x"))):
            self.assertIsNone(ca._child_guard_tick())
        self.assertIn("raised RuntimeError", cg.WATCHDOG["say"])
        seen = {}
        with mock.patch.object(cg, "watchdog_tick", lambda **k: seen.update(k) or {}):
            ca._child_guard_tick()
        self.assertIs(ca._pid_alive, seen.get("alive"), "the console's tick does not hand the watchdog its own alive")
        self.assertTrue(callable(seen.get("kill")))


# ── 6. the memory policy ─────────────────────────────────────────────────────────────────────────────────────

class TheMemoryPolicy(_World):

    def test_under_the_floor_no_secondary_worker(self):
        ok, why = cg.secondary_spawn_allowed(free_mb=300, floor_mb=1024)
        self.assertFalse(ok, "300 MB free cleared a 1024 MB floor")
        self.assertIn("under the 1024 MB floor", why)
        self.assertEqual(1, cg.RAM["refused"])

    def test_above_the_floor_is_allowed(self):
        self.assertTrue(cg.secondary_spawn_allowed(free_mb=2048, floor_mb=1024)[0])

    def test_unknown_free_ram_never_refuses_and_says_so(self):
        ok, why = cg.secondary_spawn_allowed(free_mb=None, floor_mb=1024)
        self.assertTrue(ok, "UNKNOWN free RAM refused the spawn - on a machine whose meter cannot be read the fast "
                            "lane and the stall drain would be off for ever")
        self.assertIn("UNKNOWN", why)

    def test_the_meter_is_cached_and_never_zero_for_unknown(self):
        cg.RAM.update(lastTs=None, lastFreeMb=None, unknown=0)
        reads = []
        self.assertEqual(1500, cg.free_ram_mb(now=100.0, read=lambda: reads.append(1) or 1500))
        self.assertEqual(1500, cg.free_ram_mb(now=102.0, read=lambda: reads.append(1) or 1))
        self.assertEqual(1, len(reads), "the meter was read again inside the cache window")
        self.assertIsNone(cg.free_ram_mb(now=200.0, read=lambda: None), "an unreadable meter did not read as UNKNOWN")
        self.assertEqual(1, cg.RAM["unknown"])

    def test_vm_stat_is_parsed_and_this_machines_meter_answers_or_says_unknown(self):
        sample = ("Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free:      32418.\n"
                  "Pages active:    213812.\nPages inactive:  195691.\nPages speculative:  17107.\nPages wired down: 1.\n")
        self.assertEqual(int((32418 + 195691 + 17107) * 16384 // (1024 * 1024)), cg.parse_vm_stat(sample))
        self.assertIsNone(cg.parse_vm_stat("garbage"))
        cg.RAM.update(lastTs=None, lastFreeMb=None)
        v = cg.free_ram_mb()
        self.assertTrue(v is None or (isinstance(v, int) and v > 0), "free RAM read as %r" % (v,))
        print("free RAM on this machine: %s MB" % v)


# ── 7. the console's capture through the door ───────────────────────────────────────────────────────────────

class _TrapPsutil(object):
    BELOW_NORMAL_PRIORITY_CLASS = 0x00004000

    def __init__(self):
        self.touched = []

    def Process(self, pid):
        self.touched.append(pid)
        return self

    def nice(self, *_a):
        return None


class TheConsolesCaptureGoesThroughTheDoor(_World):
    """The five-captures shape, through the REAL _start_capture / _stop_capture: the lamp cleared the lease and
    dropped _capture_proc while the capture never died. Windows edges stubbed (a capture is a pid in a set)."""

    def setUp(self):
        super().setUp()
        self.pidfile = os.path.join(self.d, "control_capture.pid")
        self.log = io.StringIO()
        self.ca_saved = (ca._capture_proc, dict(ca._CAP_STOP))
        ca._capture_proc = None
        self.reniced = []
        self.ca_stack = [
            mock.patch.object(ca, "IS_WIN", True),
            mock.patch.object(ca, "CAP_PID_PATH", self.pidfile),
            mock.patch.object(ca, "CAP_KILL_SETTLE_S", 0.3),
            mock.patch.object(ca, "_log_fp", self.log),
            mock.patch.object(ca, "_stub_never_films", lambda *a, **k: False),
            mock.patch.object(ca, "_capture_off", lambda *a, **k: False),
            mock.patch.object(ca, "_pid_alive", self.alive),
            mock.patch.object(ca, "_kill_pid", lambda pid, force=False: self.kill(pid)),
            mock.patch.object(ca, "_lower_capture_priority", lambda pid: self.reniced.append(pid)),
            mock.patch.object(ca.os.path, "isfile",
                              lambda p: True if p == ca.CAPTURE_PS1 else (str(p).startswith(self.d) and os.path.exists(p))),
            mock.patch.dict(sys.modules, {"psutil": _TrapPsutil()}),
            mock.patch.object(ca.subprocess, "Popen", self.popen(range(9990601, 9990699, 2))),
        ]
        for p in self.ca_stack:
            p.start()

    def tearDown(self):
        for p in reversed(self.ca_stack):
            p.stop()
        ca._capture_proc = self.ca_saved[0]
        ca._CAP_STOP.clear(); ca._CAP_STOP.update(self.ca_saved[1])
        super().tearDown()

    def test_a_capture_the_lamp_lost_is_ended_before_the_next_one_starts(self):
        a = ca._start_capture({"PATH": "x"}, self.log)
        self.assertIn(a, self.live)
        self.assertEqual(a, (cg.record_of("capture") or {}).get("pid"), "the console's capture was not recorded")
        self.assertIn("no job: not Windows", self.log.getvalue(), "the spawn log does not say whether the job took")
        # the lamp's path: lease cleared, _capture_proc dropped - and the process is STILL ALIVE
        os.remove(self.pidfile)
        ca._capture_proc = None
        b = ca._start_capture({"PATH": "x"}, self.log)
        self.assertNotEqual(a, b)
        self.assertNotIn(a, self.live, "THE LOST CAPTURE SURVIVED THE NEXT START - two captures film at once; this is "
                                       "how five stacked up on the ALT")
        self.assertEqual([b], sorted(p for p in (s[0] for s in self.spawned) if p in self.live))
        self.assertEqual([a], self.killed, "the old capture was not ended through this console's own kill")
        self.assertEqual(b, cg.record_of("capture")["pid"])
        self.assertIn("after ending pid %d" % a, cg.RECEIPT["say"])
        self.assertEqual([], sys.modules["psutil"].touched, "the law reached the real priority step with a fake pid")

    def test_the_stop_ends_the_recorded_tree_once_and_forgets_it(self):
        a = ca._start_capture({"PATH": "x"}, self.log)
        ca._CAP_STOP.update(survived=0, last=None)
        ca._stop_capture()
        self.assertEqual([a], self.killed, "the stop killed the capture twice, or not at all: %r" % self.killed)
        self.assertIsNone(cg.record_of("capture"), "the stopped capture is still recorded")
        self.assertEqual(0, ca._CAP_STOP["survived"])
        self.assertFalse(os.path.exists(self.pidfile))

    def test_a_lease_the_door_never_recorded_still_gets_the_plain_kill(self):
        with io.open(self.pidfile, "w") as fh:
            fh.write("9990777")
        self.live.add(9990777)
        ca._CAP_STOP.update(survived=0, last=None)
        ca._stop_capture()
        self.assertEqual([9990777], self.killed, "a previous life's lease was not killed")


# ── 8. the agent's workers through the door ──────────────────────────────────────────────────────────────────

class TheAgentsWorkersGoThroughTheDoor(_World):

    def setUp(self):
        super().setUp()
        self.tv_saved = (tv._STALL_WORKER, dict(tv._STALL_RELEASE), tv.OCR_ENABLED)
        self.popen_patch = mock.patch.object(subprocess, "Popen", self.popen(range(9990801, 9990899, 2)))
        self.popen_patch.start()

    def tearDown(self):
        self.popen_patch.stop()
        tv._STALL_WORKER = self.tv_saved[0]
        tv._STALL_RELEASE.clear(); tv._STALL_RELEASE.update(self.tv_saved[1])
        tv.OCR_ENABLED = self.tv_saved[2]
        super().tearDown()

    def test_a_vision_worker_spawns_and_stops_through_the_door(self):
        w = tv.VisionWorker(role="vision-law")
        w._spawn()
        rec = cg.record_of("vision-law")
        self.assertIsNotNone(rec, "the reader's claude was spawned outside the door - nothing ends its tree")
        self.assertEqual(w.p.pid, rec["pid"])
        if IS_POSIX:
            self.assertTrue(self.spawned[0][2].get("start_new_session"), "the reader does not lead its own session")
        self.assertIn("--input-format", self.spawned[0][1])
        w.stop()
        self.assertIsNone(cg.record_of("vision-law"), "stop() left the record - a restart would not end this tree")
        self.assertEqual([rec["pid"]], self.killed, "stop() did not end the tree through the door")

    def test_a_deaf_reader_is_buried_as_a_whole_tree(self):
        # the sweep's sibling: a write that never lands hands the worker to _bury_worker, which killed only the head
        w = tv.VisionWorker(role="vision-deaf")
        with mock.patch.object(tv, "_sub_budget_check", lambda *a, **k: None), \
                mock.patch.object(tv, "_pipe_write_by", lambda *a, **k: False):
            self.assertIsNone(w.ask("x", timeout=1))
        pid = self.spawned[0][0]
        self.assertEqual([pid], self.killed, "the deaf reader was not ended through the door - its helpers live on")
        self.assertIsNone(cg.record_of("vision-deaf"), "the buried reader is still recorded")
        self.assertIsNone(w.p)

    def test_pool_readers_and_the_stall_reader_hold_distinct_roles(self):
        roles = [w.role for w in tv._WORKERS]
        self.assertEqual(len(set(roles)), len(roles), "two pool readers share a role: %r" % roles)
        self.assertTrue(all(r.startswith("vision-r") for r in roles), roles)
        tv._STALL_WORKER = None
        self.assertEqual("vision-stall", tv._stall_worker().role)
        self.assertEqual([0, tv.POOL_N], cg._expected("vision"))

    def test_the_stall_reader_releases_its_claude_after_each_sweep(self):
        class _W(object):
            def __init__(self):
                self.p, self.stops = object(), 0

            def stop(self):
                self.stops += 1
                self.p = None
        w = _W()
        tv._STALL_RELEASE.update(n=0, lastTs=None)
        self.assertTrue(tv._stall_worker_release(w))
        self.assertEqual(1, w.stops)
        self.assertEqual(1, tv._STALL_RELEASE["n"])
        self.assertFalse(tv._stall_worker_release(w), "a reader with no process was 'released' again")
        # the join: the release runs where the sweep's busy flag clears, and nowhere else would see every sweep
        src = inspect.getsource(tv)
        anchor = 'globals()["_STALL_BUSY"] = False'
        self.assertEqual(1, src.count(anchor), "the sweep's busy-clear is no longer one site")
        after = src[src.index(anchor):src.index(anchor) + 200]
        self.assertIn("_stall_worker_release()", after,
                      "the stall reader is not released after the sweep - ~400 MB stays warm for a safety net")

    def test_the_stall_drain_does_not_fire_under_the_ram_floor(self):
        thr = tv.STALL_DRAIN_S * 1000
        self.assertTrue(tv._stall_drain_decision(1, 1, 1, thr, False))
        self.assertFalse(tv._stall_drain_decision(1, 1, 1, thr, False, ram_ok=False),
                         "the stall drain fires a second claude into memory pressure")
        asked = []
        self.assertFalse(tv._stall_drain_decision(1, 1, 1, thr, False, ram_ok=lambda: asked.append(1) and False))
        self.assertFalse(tv._stall_drain_decision(0, 1, 1, thr, False, ram_ok=lambda: asked.append(1) or True))
        self.assertEqual(1, len(asked), "the meter was asked before the cheaper gates had opened")
        with mock.patch.object(tv, "_text_eye_backlog_len", lambda: 1), \
                mock.patch.object(tv, "_vision_in_flight_n", lambda: tv.POOL_N), \
                mock.patch.object(tv, "_live_stall_ms", lambda: thr + 1), \
                mock.patch.object(tv, "_STALL_BUSY", False), \
                mock.patch.dict(os.environ, {"TV_STALL_DRAIN": "1"}):
            with mock.patch.object(cg, "secondary_spawn_allowed", lambda *a, **k: (False, "under")):
                self.assertFalse(tv._stall_drain_ready(), "the live glue does not ask the RAM policy")
            with mock.patch.object(cg, "secondary_spawn_allowed", lambda *a, **k: (True, "clear")):
                self.assertTrue(tv._stall_drain_ready())

    def test_the_ocr_worker_is_not_started_under_the_floor_and_goes_through_the_door_above_it(self):
        o = tv.OcrWorker()
        tv.OCR_ENABLED = True
        with mock.patch.object(tv, "_ocr_worker_cmd", lambda: ["ocr-fake", "--worker"]), \
                mock.patch.object(cg, "secondary_spawn_allowed", lambda *a, **k: (False, "under the floor")):
            self.assertFalse(o._spawn(), "the OCR worker started under the RAM floor")
            self.assertEqual([], self.spawned)
            self.assertFalse(o.ok)
        with mock.patch.object(tv, "_ocr_worker_cmd", lambda: ["ocr-fake", "--worker"]), \
                mock.patch.object(cg, "secondary_spawn_allowed", lambda *a, **k: (True, "clear")):
            self.assertTrue(o._spawn())
        self.assertEqual(o.p.pid, (cg.record_of("ocr") or {}).get("pid"), "the OCR worker was spawned outside the door")
        o.stop()
        self.assertIsNone(cg.record_of("ocr"))
        self.assertEqual([self.spawned[0][0]], self.killed, "stop() did not end the OCR tree through the door")


RED_PROOF = [
    {
        "why": "#83 - POSIX: the child no longer leads its own session, so a restart kills the head and the grandchild survives",
        "file": "tv/child_guard.py",
        "find": "    if not IS_WIN:\n        kw.setdefault(\"start_new_session\", True)\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#83 - a pid born at another time (reused by a newer process) is ended as if it were ours",
        "file": "tv/child_guard.py",
        "find": "    if _same_birth(rec.get(\"birth\"), now_birth):\n        return True, \"pid %s alive, born when recorded\" % pid\n",
        "replace": "    if True:\n        return True, \"pid %s alive, born when recorded\" % pid\n",
        "matches": 1,
    },
    {
        "why": "#83 - an UNKNOWN birth ends the pid on a guess",
        "file": "tv/child_guard.py",
        "find": "    if now_birth is None:\n        return False,",
        "replace": "    if False:\n        return False,",
        "matches": 1,
    },
    {
        "why": "#83 - Windows: the job is created without KILL_ON_JOB_CLOSE, so the tree outlives the handle",
        "file": "tv/child_guard.py",
        "find": "        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE\n",
        "replace": "        info.BasicLimitInformation.LimitFlags = 0\n",
        "matches": 1,
    },
    {
        "why": "#83 - Windows: end() closes the job handle without terminating the job (a closed handle kills only because of the flag; the law wants the explicit end)",
        "file": "tv/child_guard.py",
        "find": "                k.TerminateJobObject(job, 1)\n                k.CloseHandle(job)\n",
        "replace": "                k.CloseHandle(job)\n",
        "matches": 1,
    },
    {
        "why": "#83 - the watchdog no longer ends an unrecorded child of ours (a grandchild spawned outside the door)",
        "file": "tv/child_guard.py",
        "find": "        if ppid in our_pids:\n            to_end.append",
        "replace": "        if False:\n            to_end.append",
        "matches": 1,
    },
    {
        "why": "#83 - a parent born after its child (a reused parent pid) reads as the child's live console",
        "file": "tv/child_guard.py",
        "find": "            if pborn is not None and pborn > born + BIRTH_TOL_S:\n",
        "replace": "            if False:\n",
        "matches": 1,
    },
    {
        "why": "#83 - an unreadable process table owes 0 instead of UNKNOWN",
        "file": "tv/child_guard.py",
        "find": "                        owed=(len(failed) if not unknown else None), ended=ended, kept=kept, failed=failed,\n",
        "replace": "                        owed=len(failed), ended=ended, kept=kept, failed=failed,\n",
        "matches": 1,
    },
    {
        "why": "#83 - a family over its ceiling reads OK on the census",
        "file": "tv/child_guard.py",
        "find": "        elif f[\"alive\"] > hi:\n            f[\"ok\"] = False\n",
        "replace": "        elif False:\n            f[\"ok\"] = False\n",
        "matches": 1,
    },
    {
        "why": "#83 - under the floor a secondary worker is still allowed",
        "file": "tv/child_guard.py",
        "find": "    if int(free) < floor:\n        RAM[\"refused\"]",
        "replace": "    if False:\n        RAM[\"refused\"]",
        "matches": 1,
    },
    {
        "why": "#83 - UNKNOWN free RAM refuses the spawn (a meter that cannot be read silences the lanes for ever)",
        "file": "tv/child_guard.py",
        "find": "    if free is None:\n        RAM[\"say\"] = \"free RAM UNKNOWN",
        "replace": "    if free is None:\n        return False, \"guess\"\n    if False:\n        RAM[\"say\"] = \"free RAM UNKNOWN",
        "matches": 1,
    },
    {
        "why": "#83 - the doctor's one_of_each row reads an UNKNOWN watchdog table as OK",
        "file": "tv/control_app.py",
        "find": "    wd_unknown = wd.get(\"lastTs\") is not None and bool(wd.get(\"unknown\"))\n",
        "replace": "    wd_unknown = False\n",
        "matches": 1,
    },
    {
        "why": "#83 - the console's capture is spawned outside the door: a capture the lamp lost survives the next start",
        "file": "tv/control_app.py",
        "find": "        _capture_proc = _child_guard.spawn(\n            \"capture\",\n",
        "replace": "        _capture_proc = subprocess.Popen(\n",
        "matches": 1,
    },
    {
        "why": "#83 - the stop no longer forgets the role, so the next spawn 'ends' a pid that is gone and the record lies",
        "file": "tv/control_app.py",
        "find": "        _r = _child_guard.end(\"capture\", kill=lambda p: _kill_pid(p, force=True), alive=_pid_alive, wait_s=0)\n        if _r.get(\"killedPid\") != pid:\n            _kill_pid(pid, force=True)\n",
        "replace": "        _kill_pid(pid, force=True)\n",
        "matches": 1,
    },
    {
        "why": "#83 - nothing runs the watchdog off the rescue loop",
        "file": "tv/control_app.py",
        "find": "                _child_guard_tick()         # #83",
        "replace": "                pass                        # #83",
        "matches": 1,
    },
    {
        "why": "#83 - the reader's claude is spawned outside the door (its tree is never ended on a restart)",
        "file": "tv/tv_diablo.py",
        "find": "        self.p = _child_guard.spawn(self.role,\n",
        "replace": "        self.p = subprocess.Popen(\n",
        "matches": 1,
    },
    {
        "why": "#83 - the stall reader stays warm (~400 MB) after its sweep",
        "file": "tv/tv_diablo.py",
        "find": "                    _stall_worker_release()     # #83",
        "replace": "                    pass                        # #83",
        "matches": 1,
    },
    {
        "why": "#83 - the stall drain fires a second claude regardless of free RAM",
        "file": "tv/tv_diablo.py",
        "find": "    if not ram_ok:\n        return False\n    return True\n",
        "replace": "    return True\n",
        "matches": 1,
    },
    {
        "why": "#83 - the live glue never asks the RAM policy",
        "file": "tv/tv_diablo.py",
        "find": "        ram_ok=lambda: _child_guard.secondary_spawn_allowed()[0],      # #83 — asked last, cached 5 s\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#83 - the OCR worker starts under the RAM floor",
        "file": "tv/tv_diablo.py",
        "find": "            if not _ram_ok:\n                self.ok = False\n",
        "replace": "            if False:\n                self.ok = False\n",
        "matches": 1,
    },
    {
        "why": "#83 - the OCR worker is spawned outside the door",
        "file": "tv/tv_diablo.py",
        "find": "            self.p = _child_guard.spawn(\"ocr\",\n",
        "replace": "            self.p = subprocess.Popen(\n",
        "matches": 1,
    },
    {
        "why": "#83 - a deaf reader is buried by p.kill() alone: the head dies, its helpers (the pipe's read end) live on",
        "file": "tv/tv_diablo.py",
        "find": "                    _bury_worker(p, role=self.role)     # not draining its input",
        "replace": "                    _bury_worker(p)     # not draining its input",
        "matches": 1,
    },
    {
        "why": "#83 - _bury_worker ignores the role it was handed and never reaches the door",
        "file": "tv/tv_diablo.py",
        "find": "    ended = False\n    if role:\n",
        "replace": "    ended = False\n    if False:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
