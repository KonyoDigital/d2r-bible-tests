# -*- coding: utf-8 -*-
"""REG-2614 - ON A REAL WINDOWS, THE KEEPALIVE TASK IS ACCEPTED AS WRITTEN AND A PASS DECIDES RIGHT. -> exit 0 / 1 / 77

Run on windows-latest by windows_boot_check.py (tv-windows-boot.yml), after the scratch boot passes. The box laws prove the logic with a fake schtasks; only a real Task
Scheduler can say whether the XML it is given is one it takes. Under a SCRATCH task name, so a dev PC running this is
never touched: register through ensure_keepalive_task's own path, read it back (battery, hidden, interval, user),
delete it. Then one keepalive pass against a port nothing listens on, with a recording launcher, must launch once and
hold the next pass. Nothing is ever launched for real.
"""
import os
import shutil
import socket
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main():
    if not sys.platform.startswith("win"):
        print("SKIP: Windows only")
        return 77
    import console_doctor as cd
    import console_keepalive as ka
    sand = tempfile.mkdtemp(prefix="ka-check-")
    cd.KEEPALIVE_TASK = "TV DIABLO keepalive CI check %d" % os.getpid()
    bad = []
    try:
        r = cd.ensure_keepalive_task(os.path.join(sand, ".keepalive_task.json"), "created", run=subprocess.run,
                                     is_win=True, tv_dir=HERE, python=sys.executable)
        print("ensure_keepalive_task:", r)
        if r.get("did") != "created":
            bad.append("the task was not made: %s" % r)
        q = subprocess.run(["schtasks", "/Query", "/TN", cd.KEEPALIVE_TASK, "/XML"], capture_output=True, text=True)
        x = q.stdout or ""
        for want in ("<DisallowStartIfOnBatteries>false", "<StopIfGoingOnBatteries>false", "<Hidden>true",
                     "<Interval>PT5M", "<LogonType>InteractiveToken", "IgnoreNew", "console_keepalive.py"):
            if want not in x:
                bad.append("the registered task lacks %s" % want)
        again = cd.ensure_keepalive_task(os.path.join(sand, ".keepalive_task.json"), "created", run=subprocess.run,
                                         is_win=True, tv_dir=HERE, python=sys.executable)
        if again.get("did") != "already":
            bad.append("a second pass did not leave it: %s" % again)
    finally:
        subprocess.run(["schtasks", "/Delete", "/TN", cd.KEEPALIVE_TASK, "/F"], capture_output=True)
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    st = ka.probe(port, 5.0)
    if st != "gone":
        bad.append("a closed port on Windows read %r, not gone" % st)
    launched = []
    kw = dict(here=HERE, state_path=os.path.join(sand, "st.json"), log_path=os.path.join(sand, "k.log"),
              on_purpose_path=os.path.join(sand, "p"), pause_path=os.path.join(sand, "q"),
              popen=lambda argv, **k: launched.append((argv, k)) or type("P", (), {"pid": 1})())
    a = ka.run_once(now_s=1000, probe_fn=lambda: ka.probe(port, 5.0), **kw)
    b = ka.run_once(now_s=1060, probe_fn=lambda: ka.probe(port, 5.0), **kw)
    if (a["action"], b["action"], len(launched)) != ("launch", "held", 1):
        bad.append("passes went %s, %s with %d launches" % (a["action"], b["action"], len(launched)))
    elif not launched[0][1].get("creationflags", 0) & 0x08000000:
        bad.append("the launch was not windowless")
    shutil.rmtree(sand, True)
    for b_ in bad:
        print("FAIL:", b_)
    print("OK" if not bad else "FAILED")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
