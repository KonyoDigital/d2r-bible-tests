import json, time, urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:17772"
frames = Path.home() / "d2r_bible_tests" / "tv" / "frames"


def jload(p):
    p = Path(p)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8-sig"))


def get(path, method="GET", body=None, timeout=12):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def main():
    # ensure ON
    st = get("/api/status")
    if st.get("mode") != "live":
        on = get("/api/on", "POST", {})
        print("ON", on)
        time.sleep(1)
        st = get("/api/status")
    print(
        "NOW",
        st.get("ver"),
        st.get("mode"),
        "agent",
        st.get("agent"),
        "bridge",
        st.get("bridge"),
        "cap",
        st.get("captureProc"),
    )
    print("status_target", st.get("captureTarget"))
    print("cap_file", jload(frames / "cap_target.json"))
    print("=== RECORD 18s ===")
    pins = []
    for i in range(1, 19):
        time.sleep(1)
        st = get("/api/status")
        cap = jload(frames / "cap_target.json")
        dbg = jload(frames / "win_pin_debug.json")
        eye = frames / "eye.jpg"
        ea = (time.time() - eye.stat().st_mtime) if eye.exists() else -1
        lab = str(cap.get("label") or "")
        mode = str(cap.get("mode") or "")
        ok = mode == "window" and (
            "D2R" in lab or "diablo" in lab.lower() or "primary" in lab.lower()
        )
        pins.append(ok)
        print(
            f"t+{i:02d}s live={st.get('mode')} phase={st.get('phase')} "
            f"agent={st.get('agent')} bridge={st.get('bridge')} cap={st.get('captureProc')} "
            f"reads={st.get('readCount')} eye={ea:.1f}s pin_ok={ok} mode={mode} "
            f"label={lab[:70]!r} d2rProc={cap.get('d2rProcess')} best={dbg.get('best')!r}"
        )
    print("PIN_OK_RATE", sum(pins), "/", len(pins))
    off = get("/api/off", "POST", {})
    print("OFF", off)
    sess = get("/api/sessions")
    items = sess.get("sessions") or []
    print("sessions", len(items))
    if items:
        last = items[0]
        keys = [
            "sessionId",
            "n",
            "frames",
            "reads",
            "mode",
            "ver",
            "durationS",
            "label",
        ]
        print("latest", {k: last.get(k) for k in keys if last.get(k) is not None})
    print("FINAL", jload(frames / "cap_target.json"))
    dbg = jload(frames / "win_pin_debug.json")
    if dbg:
        print("PIN_DEBUG_best", dbg.get("best"), "d2rAlive", dbg.get("d2rProcessAlive"), "n", dbg.get("candidateCount"))


if __name__ == "__main__":
    main()
