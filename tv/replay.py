#!/usr/bin/env python3
# 📼 TV DIABLO — REPLAY (v752). Re-run a REAL past session: the frames the agent archived
# (tv/frames/hist) + the reads it recorded (tv/sessions.jsonl) drip through the REAL loop
# in watch mode with TV_STUB — real photos, recorded truth, zero vision cost.
#
#   tvd replay             replay the newest journaled session
#   tvd replay --list      list journaled sessions
#   tvd replay --n 2       replay the 2nd-newest session
#   tvd replay --pace 0.8  seconds between frames (default 1.2)
#
# Honesty: the manifest is built ONLY from reads whose archived frame still exists; the
# recorded read (area/scene/names/tz/stashTab/note) is replayed verbatim — nothing invented.
import json, os, shutil, signal, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
JOURNAL = os.path.join(HERE, "sessions.jsonl")
HIST = os.path.join(HERE, "frames", "hist")
SESSION_GAP_MS = 10 * 60 * 1000   # ≥10min silence = a new session


def load_journal(path=None):
    # v779 (Grok R5/R7) — read the ROTATED half first, then the live file, concatenated in
    # chronological order, so a rotation (sessions.jsonl → sessions.1.jsonl) never hides history.
    if path is not None:
        paths = [path]
    else:
        _root, _ext = os.path.splitext(JOURNAL)
        paths = [_root + ".1" + _ext, JOURNAL]
    reads = []
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:                       # torn/empty line — skip, never break loading
                        continue
                    try:
                        reads.append(json.loads(line))
                    except Exception:
                        pass                           # partial JSON from a mid-write crash — skip
        except FileNotFoundError:
            pass
    return reads


def split_sessions(reads):
    """Chronological journal → list of sessions (newest first).

    v780 — prefer explicit sessionId (one ON cycle = one theatre reel). Fall back to the
    classic ≥10min silence split for pre-v780 journal rows that lack sessionId.
    """
    sessions, cur, last_ts, last_sid = [], [], None, None
    for r in sorted(reads, key=lambda x: x.get("ts") or 0):
        ts = r.get("ts") or 0
        sid = r.get("sessionId") or None
        cut = False
        if cur:
            if sid and last_sid and sid != last_sid:
                cut = True
            elif sid and not last_sid:
                # first stamped row after unstamped history — new reel
                cut = True
            elif (not sid) and last_ts is not None and ts - last_ts > SESSION_GAP_MS:
                cut = True
            elif sid and last_sid is None and last_ts is not None and ts - last_ts > SESSION_GAP_MS:
                cut = True
        if cut:
            sessions.append(cur)
            cur = []
        cur.append(r)
        last_ts = ts
        if sid:
            last_sid = sid
        elif cut:
            last_sid = None
    if cur:
        sessions.append(cur)
    sessions.reverse()
    return sessions


def build_manifest(reads, frames_dir):
    """Recorded reads → (stub manifest keyed by frame basename, playback order).
    Only reads whose archived frame file still exists make the cut — never invent."""
    man, order = {}, []
    for r in reads:
        fid = r.get("frameId") or ""
        if not fid:
            continue
        base = fid + ".jpg"
        if not os.path.exists(os.path.join(frames_dir, base)):
            continue
        # LAST row wins per frame (an OCR/provisional glimpse is followed by the deep truth);
        # playback order = first appearance, so the run replays in real sequence.
        man[base] = {
            "area": r.get("area", ""), "scene": r.get("scene", "gameplay"),
            "names": r.get("names", []), "tz": r.get("tz", []),
            "conf": r.get("conf", 1.0),
            "stashTab": r.get("stashTab", ""),
            "note": r.get("note", ""), "transition_from": r.get("transition_from", ""),
        }
        if base not in order:
            order.append(base)
    return man, order


def main():
    args = sys.argv[1:]
    pace = 1.2
    pick = 1
    if "--pace" in args:
        pace = float(args[args.index("--pace") + 1])
    if "--n" in args:
        pick = int(args[args.index("--n") + 1])
    sessions = split_sessions(load_journal())
    if "--list" in args:
        if not sessions:
            print("📼 no journaled sessions yet — run `tvd` once, then replay")
            return
        for i, sess in enumerate(sessions, 1):
            t0 = time.strftime("%m/%d %H:%M", time.localtime((sess[0].get("ts") or 0) / 1000))
            areas = [r.get("area") for r in sess if r.get("area")]
            named = sum(1 for r in sess if r.get("names"))
            print(f"  --n {i} · {t0} · {len(sess)} reads · {named} named · "
                  + (" → ".join(dict.fromkeys(areas)) if areas else "(no areas)"))
        return
    if not sessions:
        print("📼 no journaled sessions yet — run `tvd` once (the journal starts at v752), then replay")
        sys.exit(1)
    if pick > len(sessions):
        print(f"⛔ only {len(sessions)} journaled session(s) — see `tvd replay --list`")
        sys.exit(1)
    sess = sessions[pick - 1]
    man, order = build_manifest(sess, HIST)
    if not order:
        print("⛔ that session's frames are gone from tv/frames/hist — nothing real to replay")
        sys.exit(1)

    tmp = tempfile.mkdtemp(prefix="tvd_replay_")
    watch = os.path.join(tmp, "watch")
    os.makedirs(watch)
    man_path = os.path.join(tmp, "manifest.json")
    with open(man_path, "w", encoding="utf-8") as f:
        json.dump(man, f)

    t0 = time.strftime("%m/%d %H:%M", time.localtime((sess[0].get("ts") or 0) / 1000))
    print(f"📼 REPLAY — session of {t0} · {len(order)} real frames · recorded reads · pace {pace}s")
    print("   real screenshots from tv/frames/hist through the REAL loop — flip the TV switch and watch")

    env = dict(os.environ, TV_STUB="1", TV_STUB_MANIFEST=man_path, TV_FRAMES_DIR=watch,
               TV_OCR="0",        # recorded truth only — the OCR lane would garble over replayed pixels
               TV_NO_JOURNAL="1")  # a replay never journals itself as a new session
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    proc = subprocess.Popen([sys.executable, os.path.join(HERE, "tv_diablo.py"), "--watch"], env=env)
    try:
        time.sleep(2.0)   # agent boot
        for i, base in enumerate(order, 1):
            if proc.poll() is not None:
                print("⛔ agent exited early"); break
            shutil.copy2(os.path.join(HIST, base), os.path.join(watch, base))
            rd = man[base]
            tag = rd.get("scene", "?") + (" · " + ", ".join(rd["names"][:3]) if rd.get("names") else "")
            print(f"  📼 {i}/{len(order)} {base} · {tag}")
            time.sleep(pace)
        if "--exit-after" in args:
            time.sleep(float(args[args.index("--exit-after") + 1]))
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=95)
        else:
            print("📼 replay finished — Ctrl-C stops the agent (farewell read included)")
            proc.wait()
    except KeyboardInterrupt:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=95)
        except Exception:
            proc.kill()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
