# -*- coding: utf-8 -*-
"""#218 (his ruling 2026-10-28, phase 1) - THE OWNER'S SESSIONS, SUMMARIZED SO A SHADOW CAN SHOW THEM.

His words: a shadow must render the owner's exact data one to one - and his ruling on the size: summarized frames, "a
few small key frames per session", because a full reel is 8-12 GB and never leaves its PC (his 10-07 ruling stands).
In a shadow today THE SHELF answers with a refusal toast and TV·D shows the viewer's own pane: the owner's sessions are
not in the upload (console_snapshot DENY keeps tvdHist and the session log home, on purpose - they are large).

This builds the digest a shadow can carry: the owner's newest sessions (replay.split_sessions, newest first), each
dated by what it captured (replay.session_moments, REG-2736), its read count by the Shelf's own rule (control_app's
_is_a_live_read, passed in - one predicate, never a copy), the names its reads saw, and up to 3 key frames as the
theatre's own 160 px thumbnails (tv/frames/hist/cache160/<frameId>.jpg, ~11 KB) - frames whose read named something
first, else first / middle / last. A frame with no thumbnail is made by `sips` on a Mac (the theatre's own resizer, into
the theatre's own cache); a PC with no resizer carries the session without pictures and says why, never a full frame.

Caps (the record is KV-bound): a thumbnail over 20 KB is left out and named, and the total stays under 600 KB by
dropping the OLDEST sessions' pictures first, each drop counted. Phase 2 signs and publishes it as the owner's own
roster record; phase 3 draws it in the shadow's Shelf and TV·D. Never raises; writes only the theatre's cache.
"""
import base64
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

MAX_SESSIONS = 16
MAX_FRAMES = 3
MAX_THUMB = 20 * 1024
MAX_TOTAL = 600 * 1024
MAX_NAMES = 8


def _sips_thumb(src, dst):
    """The theatre's own 160 px derivative (control_app._prewarm_session_frames' sips call). -> bool"""
    if sys.platform != "darwin":
        return False
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "68", "--resampleHeightWidthMax", "160",
                        src, "--out", dst], capture_output=True, timeout=8)
    except (OSError, subprocess.SubprocessError):
        return False
    return os.path.isfile(dst)


def thumb_bytes(hist_dir, frame_id, make=_sips_thumb):
    """The 160 px thumbnail of one read frame. -> (bytes | None, why | None)"""
    base = "%s.jpg" % frame_id
    cached = os.path.join(hist_dir, "cache160", base)
    if not os.path.isfile(cached):
        src = os.path.join(hist_dir, base)
        if not os.path.isfile(src):
            return None, "its picture is not on disk"
        if not (make and make(src, cached)):
            return None, "this PC has no thumbnail resizer, so no picture rides (a full frame never does)"
    try:
        with open(cached, "rb") as fh:
            data = fh.read()
    except OSError as e:
        return None, "its thumbnail would not read (%s)" % type(e).__name__
    if len(data) > MAX_THUMB:
        return None, "its thumbnail is %d KB, over the %d KB a summarized frame may be" % (len(data) // 1024, MAX_THUMB // 1024)
    return data, None


def _names(r):
    v = r.get("names")
    if isinstance(v, str):
        v = [v] if v and not v.startswith("[") else []
    return [str(x) for x in (v or []) if isinstance(x, str) and x.strip()]


def _key_frames(reads):
    """Up to MAX_FRAMES frame ids: those whose read named something first (newest name first), else first/middle/last."""
    ids = [r.get("frameId") for r in reads if isinstance(r.get("frameId"), str) and r.get("frameId")]
    named = [r.get("frameId") for r in reads if _names(r) and isinstance(r.get("frameId"), str)]
    out = []
    for f in list(reversed(named)) + ([ids[0], ids[len(ids) // 2], ids[-1]] if ids else []):
        if f and f not in out:
            out.append(f)
        if len(out) >= MAX_FRAMES:
            break
    return out


def digest(rows, hist_dir, is_read, now_ms, make=_sips_thumb):
    """rows: the journal's rows. is_read: the Shelf's read rule. -> {v, at, sessions: [...], bytes, dropped, left}"""
    import replay as _rp
    out = {"v": 1, "at": int(now_ms), "sessions": [], "bytes": 0, "dropped": 0, "left": []}
    try:
        groups = _rp.split_sessions(list(rows or []))
    except Exception as e:
        out["why"] = "the journal would not split into sessions (%s)" % type(e).__name__
        return out
    for g in groups[:MAX_SESSIONS]:
        reads = [r for r in g if is_read(r)]
        moments = _rp.session_moments(g) or []
        names = []
        for r in reads:
            for n in _names(r):
                if n not in names:
                    names.append(n)
        sid = next((r.get("sessionId") for r in g if r.get("sessionId")), None)
        s = {"sessionId": sid, "t0": min(moments) if moments else None, "t1": max(moments) if moments else None,
             "reads": len(reads), "names": names[:MAX_NAMES], "namesMore": max(0, len(names) - MAX_NAMES),
             "frames": [], "why": None}
        whys = []
        for fid in _key_frames(reads):
            data, why = thumb_bytes(hist_dir, fid, make)
            if data is None:
                whys.append("%s: %s" % (fid, why))
                if "KB, over" in (why or ""):
                    out["left"].append(fid)
                continue
            s["frames"].append({"id": fid, "jpg": base64.b64encode(data).decode("ascii")})
        if not s["frames"] and whys:
            s["why"] = whys[0]
        out["sessions"].append(s)
    total = sum(len(f["jpg"]) for s in out["sessions"] for f in s["frames"])
    for s in reversed(out["sessions"]):                       # the oldest sessions give their pictures up first
        if total <= MAX_TOTAL:
            break
        for f in list(s["frames"]):
            if total <= MAX_TOTAL:
                break
            s["frames"].remove(f)
            total -= len(f["jpg"])
            out["dropped"] += 1
        if not s["frames"] and not s["why"]:
            s["why"] = "its pictures were left out to keep the record under %d KB (newer sessions keep theirs)" % (MAX_TOTAL // 1024)
    out["bytes"] = total
    return out
