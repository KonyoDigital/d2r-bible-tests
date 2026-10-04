# -*- coding: utf-8 -*-
"""#144 — A PROVE LANE HAS ITS OWN PORTS, AND A SHARED PORT IS HOW A TRACKED FILE VANISHES.

test_control, test_agent and test_chronicle_route_guard pinned TV_PORT 17971 and
TV_CONTROL_PORT 17972. heart2 runs each lane in its own sandbox, but those numbers do not
change with the lane, so two lanes share one listener.

The bind is not the deleter. This law watches the file:

  · two processes bind the SAME port and neither is asked to wipe — the tracked file stays,
    and the watcher records no delete;
  · the second process, having lost the bind, sends a wipe to that port — the wipe runs in
    the FIRST sandbox, the watcher records the delete, and the deleter's pid is the listener;
  · the same wipe with each process on its own port — the neighbour's tracked file stays.

heart2 stamps TV_LANE_PORT_BASE per lane. A suite derives from it and, with no base, keeps
the port it has always used. His console port is never derived.
RED_PROOF below.
"""
import os
import socket
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lane_ports as LP  # noqa: E402
import heart2 as H  # noqa: E402


def _free_pair():
    """Two different loopback ports, held until both numbers exist so the kernel cannot reuse one."""
    a, b = socket.socket(), socket.socket()
    try:
        a.bind(("127.0.0.1", 0))
        b.bind(("127.0.0.1", 0))
        return a.getsockname()[1], b.getsockname()[1]
    finally:
        a.close()
        b.close()


_SERVER = textwrap.dedent(r"""
    import os, socket, sys, time
    root = os.environ["BOX"]
    port = int(os.environ["PORT"])
    role = os.environ["ROLE"]
    tracked = os.path.join(root, "tracked.py")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
    except OSError:
        s.close()
        if role == "wipe":
            c = socket.create_connection(("127.0.0.1", port), 2)
            c.sendall(b"WIPE\n")
            c.recv(8)
            c.close()
        sys.exit(0)
    s.listen(1)
    s.settimeout(2.0)
    try:
        conn, _addr = s.accept()
    except socket.timeout:
        s.close()
        sys.exit(0)
    data = b""
    try:
        data = conn.recv(16)
    except OSError:
        data = b""
    if data.startswith(b"WIPE") and os.path.isfile(tracked):
        with open(os.path.join(root, "deleter.pid"), "w") as fh:
            fh.write(str(os.getpid()))
        time.sleep(0.15)
        os.remove(tracked)
    try:
        conn.sendall(b"OK\n")
        conn.close()
    except OSError:
        pass
    s.close()
""")


def _watch(path, events, stop):
    was = os.path.exists(path)
    while not stop.is_set():
        now = os.path.exists(path)
        if was and not now:
            events.append("delete")
        was = now
        stop.wait(0.01)
    now = os.path.exists(path)
    if was and not now and "delete" not in events:
        events.append("delete")


class AProveLaneKeepsItsOwnPort(unittest.TestCase):

    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in
                       (LP.ENV, "TV_PORT", "TV_CONTROL_PORT", "TV_LAW_PORT")}

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        H._LANE_LOCAL.n = None

    def test_lanes_do_not_share_a_port_base(self):
        bases = [LP.base_for_lane(i) for i in range(1, 9)]
        self.assertEqual(len(set(bases)), len(bases), "two lanes were handed the same base: %r" % bases)
        self.assertEqual(bases[1] - bases[0], LP.STRIDE)
        used = []
        for b in bases:
            ports = (b, b + 1, b + 2)
            for p in ports:
                self.assertNotIn(p, LP.FORBIDDEN, "lane port %s is a reserved port" % p)
                self.assertNotIn(p, used, "port %s belongs to two lanes" % p)
                used.append(p)

    def test_a_suite_keeps_its_historical_port_until_a_lane_hands_it_a_base(self):
        os.environ.pop(LP.ENV, None)
        LP.adopt(17971, 17972)
        self.assertEqual(os.environ["TV_PORT"], "17971")
        self.assertEqual(os.environ["TV_CONTROL_PORT"], "17972")
        os.environ[LP.ENV] = str(LP.base_for_lane(3))
        LP.adopt(17971, 17972)
        b = LP.base_for_lane(3)
        self.assertEqual(os.environ["TV_PORT"], str(b))
        self.assertEqual(os.environ["TV_CONTROL_PORT"], str(b + 1))
        self.assertNotEqual(os.environ["TV_PORT"], "17971")

    def test_a_forbidden_base_is_refused(self):
        os.environ[LP.ENV] = "17772"
        self.assertIsNone(LP.current_base(), "his console port was accepted as a lane base")
        LP.adopt(17971, 17972)
        self.assertEqual(os.environ["TV_CONTROL_PORT"], "17972")
        self.assertNotEqual(os.environ["TV_CONTROL_PORT"], "17772")

    def test_the_gate_process_is_stamped_with_its_lanes_ports(self):
        """The stamp is what _run_gate puts in the child. A suite that then derives reads this."""
        os.environ.pop(LP.ENV, None)
        root = tempfile.mkdtemp(prefix="laneport.")
        self.addCleanup(__import__("shutil").rmtree, root, True)
        tv = os.path.join(root, "tv")
        os.makedirs(tv)
        open(os.path.join(tv, "lane_port_probe.py"), "w").close()
        script = (
            "import os\n"
            "print('%s %s %s %s' % (os.environ.get('TV_LANE_PORT_BASE',''),"
            "os.environ.get('TV_PORT',''), os.environ.get('TV_CONTROL_PORT',''),"
            "os.environ.get('TV_LAW_PORT','')))\n"
        )
        H._LANE_LOCAL.n = 2
        ok, tail = H._run_gate(tv, "lane_port_probe.py", timeout=30, script=script)
        self.assertTrue(ok, "the probe did not run: %r" % tail)
        b = str(LP.base_for_lane(2))
        self.assertEqual(tail.strip().split("|")[-1].strip(),
                         "%s %s %s %s" % (b, b, str(int(b) + 1), str(int(b) + 2)),
                         "lane 2's gate was not stamped with its own ports: %r" % tail)

    def test_a_shared_port_is_how_a_tracked_file_vanishes(self):
        """The watcher is the witness. The bind deletes nothing. The request through it does."""
        shared, other = _free_pair()
        for p in (shared, other):
            self.assertNotIn(p, LP.FORBIDDEN)

        stayed, _ev, deleter = self._collide(shared, shared, "hold")
        self.assertTrue(stayed, "binding the same port deleted the tracked file, and a bind cannot")
        self.assertEqual(_ev, [], "the watcher saw a delete when nobody asked for one: %r" % _ev)
        self.assertIsNone(deleter)

        stayed, ev, deleter = self._collide(shared, shared, "wipe")
        self.assertFalse(stayed, "a wipe through the shared port left the tracked file in place")
        self.assertEqual(ev, ["delete"], "the watcher did not record the unlink: %r" % ev)
        self.assertEqual(deleter, "listener",
                         "the deleter was not the listener that holds the shared port: %r" % deleter)

        stayed, ev, deleter = self._collide(shared, other, "wipe")
        self.assertTrue(stayed, "a wipe on the other port deleted this sandbox's tracked file")
        self.assertEqual(ev, [], "the watcher saw a delete across separate ports: %r" % ev)

    def _collide(self, port_a, port_b, role_b):
        """Sandbox A listens on port_a. B uses port_b with `role_b`. Watch A's tracked.py.

        -> (file_still_there, watcher events, 'listener' | 'other' | None)
        """
        root = tempfile.mkdtemp(prefix="lanevanish.")
        self.addCleanup(__import__("shutil").rmtree, root, True)
        box_a = os.path.join(root, "a")
        box_b = os.path.join(root, "b")
        os.makedirs(box_a)
        os.makedirs(box_b)
        tracked = os.path.join(box_a, "tracked.py")
        with open(tracked, "w") as fh:
            fh.write("KEEP\n")
        with open(os.path.join(box_b, "tracked.py"), "w") as fh:
            fh.write("KEEP\n")
        script = os.path.join(root, "server.py")
        with open(script, "w") as fh:
            fh.write(_SERVER)
        events, stop = [], threading.Event()
        watcher = threading.Thread(target=_watch, args=(tracked, events, stop))
        watcher.start()
        env_a = dict(os.environ, BOX=box_a, PORT=str(port_a), ROLE="hold")
        proc_a = subprocess.Popen([sys.executable, script], env=env_a)
        self.addCleanup(self._reap, proc_a)
        time.sleep(0.1)
        env_b = dict(os.environ, BOX=box_b, PORT=str(port_b), ROLE=role_b)
        proc_b = subprocess.Popen([sys.executable, script], env=env_b)
        self.addCleanup(self._reap, proc_b)
        try:
            proc_b.wait(timeout=5)
            proc_a.wait(timeout=5)
        finally:
            stop.set()
            watcher.join(timeout=2)
        who = None
        pid_path = os.path.join(box_a, "deleter.pid")
        if os.path.isfile(pid_path):
            with open(pid_path) as fh:
                got = fh.read().strip()
            who = "listener" if got == str(proc_a.pid) else "other"
        return os.path.isfile(tracked), list(events), who

    @staticmethod
    def _reap(proc):
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()


RED_PROOF = [
    {
        "why": "#144 - a lane no longer stamps its ports, so every sandbox binds 17971 again "
               "and a wipe through that port deletes the neighbour's tracked file",
        "file": "heart2.py",
        "find": "    if _ln and not _rg_env.needs_app_of(filename):\n"
                "        env = _stamp_lane_ports(env, _ln)\n",
        "replace": "    if False:\n"
                   "        env = _stamp_lane_ports(env, _ln)\n",
        "matches": 1,
    },
    {
        "why": "#144 - the suite stops reading the lane base and pins 17971 in every sandbox",
        "file": "lane_ports.py",
        "find": "    return _parse(os.environ.get(ENV, \"\"))\n",
        "replace": "    return None\n",
        "matches": 1,
    },
    {
        "why": "#144 - every lane is handed the same base, which is the shared port again",
        "file": "lane_ports.py",
        "find": "    b = BASE0 + (n - 1) * STRIDE\n",
        "replace": "    b = BASE0\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
