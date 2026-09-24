# -*- coding: utf-8 -*-
"""#229 — BOOT A SCRATCH CONSOLE ON THIS MACHINE AND ASK IT WHO IT IS. -> exit 0 / 1 / 77 (could not run)

Written for the Windows CI job (tv-windows-boot.yml): until it existed, the only Windows console anything
booted was the ALT itself, so a Windows-only boot death (the ALT died relaunching into v3419, #225) could
reach his box before anything else saw it. Runs on any OS; CI runs it on windows-latest.

It starts `control_app.py --no-open` as a SCRATCH console - TV_STUB=1, TV_CAPTURE=off, its own port, an
empty TV_HIST and sandboxed stores (the same isolation render_check gives its served console) - so it can
never film, never touch a real shelf and never contest the primary mutex (scoped by port, v1484). Then:
  1. /api/status answers inside the bound, and
  2. the build it RUNS is the build tv/WINDOWS_SHIP.json SHIPS (a half-bumped tree reads as a lie here),
  3. it reports the platform it is actually on.
The console is stopped by its own PID, and its sandbox removed, whatever happened.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def _tree():
    """The tree to boot, read at CALL time (test_import_bound_paths: an env path bound at import is fixed
    for the whole process). TVD_BOOT_CHECK_TREE is how this was proven on the ALT without touching his checkout."""
    return os.environ.get("TVD_BOOT_CHECK_TREE") or HERE
PORT = int(os.environ.get("TVD_BOOT_CHECK_PORT") or 17990)
BOUND_S = float(os.environ.get("TVD_BOOT_CHECK_BOUND_S") or 120)


def _shipped():
    try:
        with open(os.path.join(_tree(), "WINDOWS_SHIP.json"), encoding="utf-8") as f:
            return (json.load(f) or {}).get("ver")
    except Exception:
        return None


def _env(sand):
    hist = os.path.join(sand, "hist")
    os.makedirs(hist, exist_ok=True)
    return dict(os.environ, TV_CONTROL_PORT=str(PORT), TV_PORT=str(PORT + 1), TV_STUB="1",
                TV_CAPTURE="off", TV_NO_AUTO_PULL="1", TV_PARENT_PID=str(os.getpid()),
                TV_HIST=hist, TV_FRAMES_DIR=os.path.join(sand, "frames"),
                TV_SESSIONS=os.path.join(sand, "sessions.jsonl"),
                TV_CHRON_EVIDENCE=os.path.join(sand, "chron_evidence.json"),
                TV_CHRON_RESULT=os.path.join(sand, "chron_last_result.json"),
                TV_CHRON_SWEPT=os.path.join(sand, "chronicle_swept.json"),
                TV_CHRON_READS=os.path.join(sand, "chron_reads.json"),
                TV_SWEEP_LOCK=os.path.join(sand, ".sweep.lock"),
                TV_CONSOLE_BOOT_LOG=os.path.join(sand, "console_boot.log"),
                PYTHONIOENCODING="utf-8")


def main():
    want = _shipped()
    if not want:
        print("⚪ UNKNOWN — tv/WINDOWS_SHIP.json names no version, so there is nothing to compare the boot against")
        return 77
    sand = tempfile.mkdtemp(prefix="tvd-boot-check-")
    log = open(os.path.join(sand, "console.out"), "w", encoding="utf-8")
    proc = subprocess.Popen([sys.executable, os.path.join(_tree(), "control_app.py"), "--no-open"],
                            cwd=_tree(), env=_env(sand), stdout=log, stderr=subprocess.STDOUT)
    st, t0, err = None, time.time(), None
    try:
        while time.time() - t0 < BOUND_S:
            if proc.poll() is not None:
                err = "the console EXITED during boot (code %s)" % proc.returncode
                break
            try:
                with urllib.request.urlopen("http://127.0.0.1:%d/api/status" % PORT, timeout=3) as r:
                    st = json.loads(r.read().decode("utf-8"))
                break
            except Exception:
                time.sleep(1.0)
        took = time.time() - t0
        if st is None:
            log.flush()
            tail = open(os.path.join(sand, "console.out"), encoding="utf-8", errors="replace").read()[-1500:]
            print("🔴 the scratch console never answered /api/status within %ds on %s - %s\n--- its last words ---\n%s"
                  % (BOUND_S, sys.platform, err or "no answer", tail))
            return 1
        ver = st.get("ver")
        plat = ((st.get("identity") or {}).get("platform")) or "?"
        bad = []
        if ver != want:
            bad.append("it runs %s but WINDOWS_SHIP.json ships %s" % (ver, want))
        if sys.platform.startswith("win") and plat != "windows":
            bad.append("it says it is on %r while running on Windows" % plat)
        if bad:
            print("🔴 the console booted in %.1fs and " % took + "; ".join(bad))
            return 1
        print("🟢 a scratch console booted on %s in %.1fs, runs %s (the shipped build) and says platform=%s"
              % (sys.platform, took, ver, plat))
        return 0
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=15)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        log.close()
        shutil.rmtree(sand, ignore_errors=True)


if __name__ == "__main__":
    sys.path.insert(0, _tree())
    try:
        from console_safe import enable as _enable
        _enable()
    except Exception:
        pass
    sys.exit(main())
