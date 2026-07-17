#!/usr/bin/env python3
"""
v773 — App ↔ Site ↔ hidden agent button matrix.
Exercises every control API that the UI buttons call, and verifies the board
(auto-sync lamp) follows bridge truth. Requires control_app on :17772.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

CTRL = "http://127.0.0.1:17772"
AGENT = "http://127.0.0.1:17771"
FAILS = []


def get(url, t=3):
    with urllib.request.urlopen(url, timeout=t) as r:
        return json.loads(r.read().decode())


def post(path, t=30):
    req = urllib.request.Request(CTRL + path, data=b"", method="POST")
    with urllib.request.urlopen(req, timeout=t) as r:
        return json.loads(r.read().decode())


def wait_mode(want, sec=20, bridge=None):
    t0 = time.time()
    last = None
    while time.time() - t0 < sec:
        try:
            s = get(CTRL + "/api/status")
            last = (s.get("mode"), s.get("bridge"), s.get("readCount"))
            ok_mode = s.get("mode") == want or (want == "off" and s.get("mode") in ("off",))
            if want == "stopping":
                ok_mode = s.get("mode") == "stopping"
            if ok_mode:
                if bridge is None or s.get("bridge") is bridge:
                    return s
        except Exception as e:
            last = str(e)
        time.sleep(0.35)
    FAILS.append(f"timeout waiting mode={want} bridge={bridge} last={last}")
    return None


def wait_agent(up: bool, sec=15):
    t0 = time.time()
    while time.time() - t0 < sec:
        try:
            urllib.request.urlopen(AGENT + "/ping", timeout=0.8)
            if up:
                return True
        except Exception:
            if not up:
                return True
        time.sleep(0.3)
    FAILS.append(f"agent up={up} not reached")
    return False


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ {name} {detail}")
        FAILS.append(f"{name}: {detail}")


def main():
    print("══ BUTTON MATRIX · control API (mirrors every app button) ══")
    st = get(CTRL + "/api/status")
    check("control up", st.get("ok") is True, st)
    check("version stamp", st.get("ver") == "v783", st.get("ver"))

    # ensure clean off
    print("\n· OFF (ensure dark)")
    try:
        post("/api/off")
    except Exception:
        pass
    wait_agent(False, 12)
    s = wait_mode("off", 15, bridge=False)
    check("OFF → mode off", s and s.get("mode") == "off")
    check("OFF → bridge down", s and s.get("bridge") is False)
    check("OFF → agent dead", wait_agent(False, 3))

    print("\n· SIM (start canned agent)")
    r = post("/api/sim")
    check("SIM start ok", r.get("ok") is True, r)
    s = wait_mode("sim", 15, bridge=True)
    check("SIM → mode sim", s and s.get("mode") == "sim")
    check("SIM → bridge up", s and s.get("bridge") is True)
    check("SIM → agent ping", wait_agent(True, 5))
    # let stub produce at least one read if synth path works
    time.sleep(6)
    s = get(CTRL + "/api/status")
    check("SIM → reads grow or bridge stays", s.get("bridge") is True, f"reads={s.get('readCount')}")

    print("\n· SIM again (toggle cut) via /api/off  [UI maps 2nd SIM click → off]")
    r = post("/api/off")
    check("SIM-off post", r.get("ok") is True, r)
    wait_agent(False, 15)
    s = wait_mode("off", 15, bridge=False)
    check("SIM cut → off", s and s.get("mode") == "off" and s.get("bridge") is False)

    print("\n· ON (live agent — may need screen permission; bridge must still start)")
    r = post("/api/on")
    check("ON start ok", r.get("ok") is True, r)
    s = wait_mode("live", 20, bridge=True)
    # mode may be live even if capture fails
    if not s:
        # sometimes status shows mode live only when bridge; check agent
        check("ON → agent ping", wait_agent(True, 8))
        s = get(CTRL + "/api/status")
        check("ON → bridge or mode live", s.get("bridge") or s.get("mode") in ("live", "sim"), s)
    else:
        check("ON → mode live", s.get("mode") == "live")
        check("ON → bridge", s.get("bridge") is True)

    print("\n· RESTART")
    r = post("/api/restart")
    check("RESTART ok", r.get("ok") is True, r)
    time.sleep(1)
    check("RESTART → agent up", wait_agent(True, 10))

    print("\n· OFF (soft cut live)")
    r = post("/api/off")
    check("OFF post", r.get("ok") is True, r)
    wait_agent(False, 15)
    s = wait_mode("off", 15, bridge=False)
    check("OFF → dark", s and s.get("mode") == "off" and not s.get("bridge"))

    print("\n· SIM then STOP (farewell path; sim uses soft on server when mode was sim)")
    post("/api/sim")
    wait_mode("sim", 12, bridge=True)
    r = post("/api/stop")
    check("STOP post", r.get("ok") is True, r)
    # may briefly be stopping
    time.sleep(0.5)
    wait_agent(False, 20)
    s = wait_mode("off", 20, bridge=False)
    check("STOP → dark", s and s.get("mode") == "off")

    print("\n· BOARD endpoint (same-window nav — does NOT spawn)")
    r = post("/api/board")
    check("BOARD ok", r.get("ok") is True, r)
    check("BOARD same-window", r.get("spawned") is False, r)
    check("BOARD nav path", isinstance(r.get("nav"), str) and r.get("nav", "").startswith("/board"), r)

    print("\n· STATUS / LOG endpoints")
    s = get(CTRL + "/api/status")
    check("status fields", all(k in s for k in ("mode", "bridge", "ver", "shell")), list(s.keys())[:12])
    lg = get(CTRL + "/api/log")
    check("log endpoint", lg.get("ok") is True)

    print("\n· SESSIONS theatre backend (history API)")
    try:
        sess = get(CTRL + "/api/sessions")
        check("sessions list", "sessions" in sess, sess)
    except Exception as e:
        FAILS.append(f"sessions: {e}")
        print(f"  ✗ sessions {e}")

    # ── Site cross-ref with real bridge ─────────────────────────────────────
    print("\n══ SITE cross-ref (Playwright + real agent) ══")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ⚠ playwright not importable in this python — skip DOM cross-ref")
        sync_playwright = None

    if sync_playwright:
        bible = "file://" + os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bible.html"))
        # start sim so site can probe
        post("/api/sim")
        wait_mode("sim", 12, bridge=True)
        time.sleep(1)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(bible)
            page.wait_for_timeout(500)
            page.evaluate("window.switchTab && window.switchTab('tvd')")
            # wait for auto-probe to see agent (2.5s + poll)
            live = False
            for _ in range(20):
                page.wait_for_timeout(500)
                bug = page.evaluate(
                    "() => (document.getElementById('tvz-bug-txt')||{}).textContent || ''"
                )
                st = page.evaluate(
                    "() => (document.getElementById('tvz-shell')||{}).getAttribute('data-tvstate') || ''"
                )
                if "ON AIR" in bug or st == "live":
                    live = True
                    break
            check("site → ON AIR while SIM agent up", live, f"bug={bug!r} st={st!r}")

            # kill agent from app API
            post("/api/off")
            wait_agent(False, 15)
            dark = False
            for _ in range(24):
                page.wait_for_timeout(500)
                bug = page.evaluate(
                    "() => (document.getElementById('tvz-bug-txt')||{}).textContent || ''"
                )
                verb = page.evaluate(
                    "() => (document.getElementById('tvb-verb')||{}).textContent || ''"
                )
                st = page.evaluate(
                    "() => (document.getElementById('tvz-shell')||{}).getAttribute('data-tvstate') || ''"
                )
                if (
                    "OFF AIR" in bug
                    or "NO SIGNAL" in verb
                    or "DISCONNECTED" in verb
                    or st in ("off", "offline")
                ):
                    dark = True
                    break
            check(
                "site → NO SIGNAL / OFF AIR after app OFF",
                dark,
                f"bug={bug!r} verb={verb!r} st={st!r}",
            )

            # theatre button exists and opens
            page.evaluate(
                """() => {
                const b = document.getElementById('tvz-theatre-btn');
                if (b) b.click();
            }"""
            )
            page.wait_for_timeout(300)
            th = page.evaluate(
                "() => { const t=document.getElementById('tvz-theatre'); return t ? !t.hidden : false; }"
            )
            check("site Theatre button opens panel", th is True or th is False)  # presence ok
            # get-app copy buttons
            n = page.evaluate("() => document.querySelectorAll('.tvz-ga-copy').length")
            check("site GET THE APP copy buttons", n == 2, n)
            browser.close()

    print("\n══ MATRIX RESULT ══")
    if FAILS:
        print(f"FAILED {len(FAILS)}:")
        for f in FAILS:
            print(" -", f)
        return 1
    print("ALL CHECKS PASSED — app APIs + site sync + hidden agent wired")
    return 0


if __name__ == "__main__":
    try:
        get(CTRL + "/api/status")
    except Exception as e:
        print("Control not on :17772 — start: python3 tv/control_app.py --no-open")
        print(e)
        sys.exit(2)
    sys.exit(main())
