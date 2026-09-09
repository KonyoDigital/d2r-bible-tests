# -*- coding: utf-8 -*-
"""v2847 — I NEARLY KILLED HIS CONSOLE, AND THE GUARD WRITTEN TO STOP ME WOULD HAVE AGREED.

2026-09-09. He said his Mac was hot and asked me to find what was doing it and kill it if it was
background. One `ps -r` sample returned:

    69557   1  108.4%  17:15:30  python3 .../tv/control_app.py --open

Orphaned to ppid 1, over a full core, seventeen hours. Textbook runaway, and I said so — *"Found it
— and it's mine"* — one command from killing it. **It is his console**, holding `localhost:17772`,
and the whole session's work is executed out of it.

TWO independent defects had to line up, and both are fixed here:

=== 1. THE OWNERSHIP GUARD NEVER ASKED ABOUT HIS PORTS ===
`my_orphans.py` declares, at the top:

    #: Ports that are HIS by definition. A process holding one of these is never "mine",
    #: whatever else matches — his console, his Chrome, TradingView, his desktop app.
    HIS_PORTS = (17772, 17781, 17955, 9222, 9223, 8848)

MEASURED: `grep -c HIS_PORTS` -> **1**. Its own definition. Nothing read it. `_attribute()`
promised three positive witnesses in its docstring, implemented two, and ended its refusal with the
words *"holds none of our ports"* — an assertion about a check that was never run. Asked about his
live console it answered `ours=None`, "busy and old, and nothing can say whose it is": the exact
shape this tool reports as a suspect. [[plumbing-with-no-tap]] [[the-unjoined-end]]

=== 2. ONE `ps` SAMPLE IS A DECAYING AVERAGE, NOT A LOAD ===
The same process, three reads seconds apart: **108.4%**, then 9.0%, then 5.6%. Nothing changed but
the sampling. A runaway is busy in BOTH samples; a burst is busy in one.
[[feedback-suspect-the-instrument]]

⚠ AND THE FIRST FIX WAS WRONG IN A WAY THAT WOULD HAVE BEEN WORSE. `lsof` ORs its selectors: with
`-p PID -iTCP` and no `-a` it returns EVERY process's listening sockets, so the check answered "does
anything on this machine listen on one of his ports" — always true while his console runs. Every
process would have been declared NEVER MINE, and the guard could never catch the runaway it exists
for. Measured by the label being wrong: the task viewer, really on :17955, came back :17772.
"""
import ast
import io
import os
import sys
import unittest

# ⚠⚠ THIS FILE PRINTS NON-ASCII (⚠ ★ ✕ →) AND MUST MAKE ITS OWN STDOUT SAFE. Caught by
# test_every_cli_that_prints_non_ascii_is_encoding_safe on the v2848 push, which REFUSED the ship:
# a CLI that inherits its safety from the operator's shell dies on a non-UTF-8 console — Windows
# python stdout is cp1255 here — and then a CORRECT tree reports FAILURE. `tv/test_button_matrix.py`
# is the precedent: it died on encoding, and hidden underneath was a version assertion that had
# been wrong since v900. A tool that crashes while REPORTING teaches people to ignore it.
for _stream in (sys.stdout, sys.stderr):
    try:
        if _stream is not None and hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import my_orphans as M   # noqa: E402


class HisConsoleIsNeverMine(unittest.TestCase):

    # ── LAW 1 — the constant is CONSULTED, not merely declared ──────────────────────────────
    def test_his_ports_is_read_by_the_code_and_not_only_defined(self):
        """The defect verbatim: a protective constant with one reference — its own definition.

        ⚠ PARSED, NOT COUNTED IN TEXT. `HIS_PORTS` appears in this file's own prose and in
        my_orphans' comments; a substring count would be satisfied by the very commentary that
        described the bug. This asks the AST for real LOADS of the name. [[source-reading-guard]]
        """
        src = io.open(os.path.join(HERE, "my_orphans.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        stores = [n for n in ast.walk(tree)
                  if isinstance(n, ast.Name) and n.id == "HIS_PORTS"
                  and isinstance(n.ctx, ast.Store)]
        loads = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Name) and n.id == "HIS_PORTS"
                 and isinstance(n.ctx, ast.Load)]
        self.assertEqual(len(stores), 1,
                         "HIS_PORTS must be defined exactly once; found %d" % len(stores))
        self.assertGreaterEqual(
            len(loads), 1,
            "HIS_PORTS is DEFINED and never READ — %d load(s). That is the defect this gate "
            "exists for: the constant that would have saved his console was dead, and the "
            "refusal sentence claimed a check nobody ran." % len(loads))

    # ── LAW 2 — lsof must AND its selectors ─────────────────────────────────────────────────
    def test_the_port_lookup_ands_its_selectors(self):
        """Without `-a`, lsof ORs `-p` and `-i` and hands back the whole machine — so every
        process looks like it holds his port and NOTHING can ever be identified as mine. A guard
        that cannot say 'mine' cannot catch a runaway."""
        src = io.open(os.path.join(HERE, "my_orphans.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        calls = []
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            name = getattr(f, "attr", None) or getattr(f, "id", None)
            if name != "run" or not n.args:
                continue
            arg = n.args[0]
            if not isinstance(arg, (ast.List, ast.Tuple)):
                continue
            parts = [e.value for e in arg.elts if isinstance(e, ast.Constant)]
            if parts and parts[0] == "lsof":
                calls.append(parts)
        self.assertGreaterEqual(len(calls), 1, "no lsof invocation found to check")
        for parts in calls:
            self.assertIn(
                "-a", parts,
                "an lsof call omits `-a`, so its -p and -i selectors are ORed and it reports "
                "sockets belonging to OTHER processes: %r" % (parts,))

    # ── LAW 3 — a port-holder, and its children, are positively NOT mine ────────────────────
    def test_a_process_on_one_of_his_ports_is_refused(self):
        """⚠ STUBBED ON PURPOSE, so this law does not depend on his console being up. A gate whose
        fixture is 'the machine happens to be running his console' passes for the wrong reason on
        his Mac and is vacuous on CI. [[gate-blind-to-unexercised-input]]"""
        real = M._listening_ports
        try:
            M._listening_ports = lambda pid: (({17772} if str(pid) == "4242" else set()), "stub")
            port, why = M.holds_his_port("4242")
            self.assertEqual(port, 17772,
                             "a process listening on :17772 must be identified as his, got %r" % port)
            own, ownWhy = M._attribute("4242", "python3 %s/control_app.py --open" % HERE)
            self.assertIs(own, False,
                          "a process on HIS port must be positively NOT-MINE. Got %r (%s). Note "
                          "the command line NAMES THIS TREE, which is the other witness — his "
                          "port has to win, or 'names this tree' hands me his console."
                          % (own, ownWhy))
            self.assertIn("NEVER MINE", ownWhy,
                          "the refusal must say so unmistakably; got: %s" % ownWhy)
        finally:
            M._listening_ports = real

    def test_a_child_of_a_port_holder_is_refused_too(self):
        """His console holds the port on ONE pid and runs helpers beside it that hold none.
        Killing a child breaks the console just as surely as killing the listener."""
        real_lp, real_par = M._listening_ports, M._parent_of
        try:
            M._listening_ports = lambda pid: (({17772} if str(pid) == "999" else set()), "stub")
            M._parent_of = lambda pid: {"111": "999"}.get(str(pid))
            port, why = M.holds_his_port("111")
            self.assertEqual(port, 17772,
                             "a CHILD of the port holder must be protected; got %r (%s)" % (port, why))
            self.assertIn("ancestor", why, "the reason must name the ancestry; got: %s" % why)
        finally:
            M._listening_ports, M._parent_of = real_lp, real_par

    # ── LAW 4 — a burst is not a runaway ────────────────────────────────────────────────────
    def test_a_single_cpu_spike_cannot_become_a_verdict(self):
        """108.4%, then 9.0%, then 5.6% — one process, three reads, nothing changed but the
        sampling. `suspects` must take TWO samples and judge on the lower."""
        src = io.open(os.path.join(HERE, "my_orphans.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        fn = [n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "suspects"]
        self.assertEqual(len(fn), 1, "expected exactly one suspects(); found %d" % len(fn))
        called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                  for n in ast.walk(fn[0]) if isinstance(n, ast.Call)}
        self.assertIn(
            "_cpu_sample", called,
            "suspects() does not take a second CPU sample — it judges on one decaying average, "
            "which is what turned a 5.6%% process into '108.4%%, pinning a core for 17 hours'. "
            "It calls: %s" % ", ".join(sorted(x for x in called if x)))
        self.assertIn("min", called,
                      "suspects() must judge on the MINIMUM of the two samples, so a burst in "
                      "either one cannot promote itself into a verdict")


    # ── LAW 5 — the OS is excused, and I am NOT ─────────────────────────────────────────────
    def test_the_system_is_excused_but_the_sweep_can_still_see_its_own_author(self):
        """★ THE DANGEROUS DIRECTION IS THE SECOND HALF.

        Excusing macOS is necessary: the first live run flagged `coreaudiod` — 22.8%% and 23.5%%
        across both samples, seven days old — because he was on a call. A watcher that cries about
        the operating system teaches him to ignore it.

        But an over-broad prefix would excuse the sweep's OWN author. My processes run under
        `/Library/Developer/CommandLineTools/...`, his node tools under `/usr/local/bin` — adding
        either would make this tool structurally unable to report a runaway of mine, which is the
        failure it exists to prevent, wearing the costume of a fix. [[gate-blind-to-unexercised-input]]
        """
        excused = [
            "/usr/sbin/coreaudiod",
            "/System/Library/PrivateFrameworks/SkyLight.framework/Resources/WindowServer",
            "/usr/libexec/runningboardd",
        ]
        for path in excused:
            self.assertTrue(path.startswith(M.SYSTEM_PATHS),
                            "%r is macOS and must be excused, or this sweep cries wolf at the "
                            "operating system every time he takes a call" % path)
        mine = [
            "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/"
            "Versions/3.9/Resources/Python.app/Contents/MacOS/Python",
            "/usr/local/bin/node",
            "/usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe",
            "python3",
        ]
        for path in mine:
            self.assertFalse(
                path.startswith(M.SYSTEM_PATHS),
                "%r would be excused as an OS binary — but that is the interpreter THIS SWEEP "
                "RUNS UNDER. A guard that cannot see its own author can never report the runaway "
                "it was written for." % path)
        self.assertNotIn("/usr/local", M.SYSTEM_PATHS,
                         "/usr/local holds node and his own tools; excusing it blinds the sweep")


# ══ THE EXECUTABLE RED-PROOFS ════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "dropping the port check from _attribute is the original defect — his console comes "
               "back as an unattributed suspect and I kill it",
        "file": "my_orphans.py",
        "find": "    _hp, _hpWhy = holds_his_port(pid)\n    if _hp is None or _hp:\n        return False, (\"NEVER MINE — %s\" % _hpWhy)\n",
        "replace": "    _hp, _hpWhy = (0, \"tampered\")\n",
        "matches": 1,
    },
    {
        "why": "removing -a returns lsof to ORing its selectors, so every process on the machine "
               "reads as holding his port and nothing can ever be caught",
        "file": "my_orphans.py",
        "find": '        r = subprocess.run(["lsof", "-nP", "-a", "-p", str(pid), "-iTCP", "-sTCP:LISTEN"],\n                           capture_output=True, text=True, timeout=10)\n    except Exception as e:\n        return set(), "lsof could not be asked (%s)" % type(e).__name__',
        "replace": '        r = subprocess.run(["lsof", "-nP", "-p", str(pid), "-iTCP", "-sTCP:LISTEN"],\n                           capture_output=True, text=True, timeout=10)\n    except Exception as e:\n        return set(), "lsof could not be asked (%s)" % type(e).__name__',
        "matches": 1,
    },
    {
        "why": "removing the ancestry walk leaves his console's helpers killable",
        "file": "my_orphans.py",
        "find": "            if port in _up:\n                return port, (\"its ancestor pid %s listens on :%d — killing a child of his \"\n                              \"console breaks his console\" % (_pp, port))",
        "replace": "            if False:\n                return port, (\"tampered %s %d\" % (_pp, port))",
        "matches": 1,
    },
    {
        # ⚠⚠ RE-ANCHORED, AND THE REASON IS THE SCAR ITSELF. The v2851 swallow fix renamed
        # `_first = _cpu_sample()` to `_cur = _cpu_sample()` — and that line WAS this sabotage's
        # anchor, so my own fix silently disarmed my own proof. The gate said so exactly:
        # "the tamper matches 0 time(s), it declares 1 — a sabotage that changes nothing proves
        # nothing". Third time in one session that a refactor of mine moved a sabotage.
        #
        # ⚠ AND THE OBVIOUS RE-ANCHOR WOULD ALSO HAVE PROVEN NOTHING. Pointing it at the new
        # `_cur = _cpu_sample()` looks right and is useless: the law asserts that `suspects()`
        # CALLS `_cpu_sample` and `min`, and there are now TWO `_cpu_sample()` calls, so deleting
        # one leaves the set intact and the gate green. The tamper has to defeat the LAW's subject,
        # not merely edit a line the law once happened to sit near.
        # This one removes the MINIMUM — the single thing that makes two samples a judgement rather
        # than a pair of readings — which is precisely "going back to one sample".
        # [[sabotage-is-usually-the-wrong-one]]
        "why": "dropping the minimum-of-two-samples restores the single decaying average that "
               "reported 108% for a process sitting at 5.6%",
        "file": "my_orphans.py",
        "find": "        cpu = min(cpu, cpu0) if cpu0 is not None else 0.0",
        "replace": "        cpu = cpu if cpu0 is not None else 0.0",
        "matches": 1,
    },
    {
        "why": "widening SYSTEM_PATHS to /usr excuses /usr/local and, with it, node and his own "
               "tools — the sweep goes blind to whole classes of process it is meant to watch",
        "file": "my_orphans.py",
        "find": 'SYSTEM_PATHS = ("/System/", "/usr/sbin/", "/usr/libexec/", "/sbin/", "/Library/Apple/")',
        "replace": 'SYSTEM_PATHS = ("/System/", "/usr/", "/sbin/", "/Library/Apple/")',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
