# -*- coding: utf-8 -*-
"""#151 - HIS GROK CHATS ARE PRUNED ON THEIR OWN, AND ONLY WHEN THEY HAVE TO BE.

His ruling, 2026-10-28: "pruning your own Grok chats ... architecure and build and design something so fix it and prune
automatically if needed." The Grok CLI keeps every conversation as a folder under ~/.grok/sessions/<its cwd>/<session id>/
and never removes one. On 2026-09-01 that folder reached 11.25 GB and took his Mac to 1.1 GB free / ENOSPC (memory:
grok-sessions-eat-the-disk). The console's own reads already drop their sessions (REG-1687, REG-2718, REG-2731); what is
left is his own chats, and nothing ever pruned those.

WHEN: only when it is needed - the sessions folder is over BUDGET_BYTES (the 11 GB repeat), or the disk is under the ON AIR
floor. Neither -> nothing is touched, however old a chat is.
WHAT: whole conversation folders (<cwd folder>/<session id>/), oldest first by their newest file. Never:
  * a session Grok lists as open in active_sessions.json (his live TUI) - unreadable registry -> nothing is pruned at all;
  * a folder written in the last LIVE_S (a run still writing has not registered yet);
  * a folder younger than KEEP_DAYS - or KEEP_DAYS_CRITICAL when the disk is under the critical floor (red);
  * anything that is not a directory two levels under the sessions root (prompt_history.jsonl, session_search.sqlite,
    a symlink, a file) - the walk never leaves the root.
HOW MUCH: until the folder is back under TARGET_BYTES (when over budget) and the disk is back over the floor plus
MARGIN_BYTES (when short) - or nothing more may go, which is said, never forced.
WHAT IT SAYS: a receipt per pass (what went, how big, how old, why) appended to the console's log root, and the lane
status in the shared words - on / worked / lastTs / owed / say. owed counts the bytes still over the line after a pass
(UNKNOWN when the folder could not be read; never 0 on a guess). [[heart-first]] [[unknown-stays-unknown]]

Every filesystem touch is a parameter, so a law drives this on a fixture tree and never his folder.
"""
import json
import os
import shutil
import time

BUDGET_BYTES = 2 * 1000 ** 3          # over this the folder is pruned back
TARGET_BYTES = 1500 * 1000 ** 2       # ... to under this
MARGIN_BYTES = 1 * 1000 ** 3          # a short disk is pruned until it is this far over the floor
KEEP_DAYS = 7                         # a chat this young stays
KEEP_DAYS_CRITICAL = 1                # ... unless the disk is under the critical floor
LIVE_S = 3600                         # a folder written this recently may belong to a run still going


def sessions_root(home=None):
    """~/.grok/sessions (GROK_HOME honoured, as every lane that drops a session reads it). -> path"""
    base = os.environ.get("GROK_HOME") or os.path.join(home or os.path.expanduser("~"), ".grok")
    return os.path.join(base, "sessions")


def live_ids(registry_path):
    """The session ids Grok lists as open. -> set, or None when the registry cannot be read (then NOTHING is pruned)"""
    if not os.path.exists(registry_path):
        return set()
    try:
        with open(registry_path, encoding="utf-8") as fh:
            rows = json.load(fh)
    except Exception:
        return None
    if not isinstance(rows, list):
        return None
    return {str(r.get("session_id")) for r in rows if isinstance(r, dict) and r.get("session_id")}


def _size_and_newest(path):
    """Bytes and newest mtime under one conversation folder, never following a link. -> (bytes, newest_s)"""
    total, newest, stack = 0, os.lstat(path).st_mtime, [path]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for e in it:
                    try:
                        st = e.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    newest = max(newest, st.st_mtime)
                    if e.is_dir(follow_symlinks=False):
                        stack.append(e.path)
                    elif not e.is_symlink():
                        total += st.st_size
        except OSError:
            continue
    return total, newest


def inventory(root):
    """Every conversation folder two levels under the root. -> [{path, cwd, id, bytes, newest}] ; [] when absent"""
    out = []
    if not os.path.isdir(root):
        return out
    with os.scandir(root) as top:
        for c in top:
            if not c.is_dir(follow_symlinks=False):
                continue
            try:
                with os.scandir(c.path) as kids:
                    for k in kids:
                        if not k.is_dir(follow_symlinks=False):
                            continue
                        b, n = _size_and_newest(k.path)
                        out.append({"path": k.path, "cwd": c.name, "id": k.name, "bytes": b, "newest": n})
            except OSError:
                continue
    return out


def plan(rows, live, free_bytes, floor_bytes, critical_bytes, now_s):
    """Which conversation folders go, oldest first. Pure. -> {need, go: [row], keep_why, total, after}

    need: None (nothing to do) | "over-budget" | "disk-short" | "both". free_bytes None is UNKNOWN: the disk alone never
    triggers on a guess (the budget still can)."""
    total = sum(r["bytes"] for r in rows)
    short = isinstance(free_bytes, (int, float)) and not isinstance(free_bytes, bool) and free_bytes < floor_bytes
    over = total > BUDGET_BYTES
    need = "both" if (over and short) else "over-budget" if over else "disk-short" if short else None
    if need is None or live is None:
        return {"need": need, "go": [], "total": total, "after": total,
                "keep_why": None if live is not None else "the live-session registry could not be read"}
    critical = short and isinstance(critical_bytes, (int, float)) and free_bytes < critical_bytes
    keep_s = (KEEP_DAYS_CRITICAL if critical else KEEP_DAYS) * 86400
    goable = [r for r in rows
              if r["id"] not in live and now_s - r["newest"] >= max(LIVE_S, keep_s)]
    goable.sort(key=lambda r: r["newest"])
    go, freed = [], 0
    for r in goable:
        under_target = total - freed <= TARGET_BYTES
        disk_ok = not short or (free_bytes + freed >= floor_bytes + MARGIN_BYTES)
        if (not over or under_target) and disk_ok:
            break
        go.append(r)
        freed += r["bytes"]
    left = [r for r in rows if r not in go]
    young = sum(1 for r in left if now_s - r["newest"] < keep_s)
    held = sum(1 for r in left if r["id"] in live)
    return {"need": need, "go": go, "total": total, "after": total - freed, "critical": critical,
            "keep_why": ("%d chat(s) younger than %d day(s) and %d live session(s) stay"
                         % (young, keep_s // 86400, held))}


def run(root=None, registry=None, free_bytes=None, floor_bytes=None, critical_bytes=None, receipt_path=None,
        now_s=None, remove=None):
    """One pass. Never raises. -> the pass record {need, removed, freed, total, after, say}"""
    now_s = time.time() if now_s is None else now_s
    root = root or sessions_root()
    registry = registry or os.path.join(os.path.dirname(root), "active_sessions.json")
    rm = remove or (lambda p: shutil.rmtree(p))
    try:
        rows = inventory(root)
    except Exception as e:
        return {"need": None, "removed": [], "freed": 0, "total": None, "after": None,
                "say": "the Grok sessions folder could not be read (%s) - UNKNOWN, nothing pruned" % type(e).__name__}
    live = live_ids(registry)
    p = plan(rows, live, free_bytes, floor_bytes or 0, critical_bytes, now_s)
    removed, freed, failed = [], 0, 0
    for r in p["go"]:
        try:
            rm(r["path"])
            removed.append({"cwd": r["cwd"], "id": r["id"], "bytes": r["bytes"],
                            "ageDays": round((now_s - r["newest"]) / 86400.0, 1)})
            freed += r["bytes"]
        except Exception:
            failed += 1
    rec = {"ts": int(now_s * 1000), "need": p["need"], "removed": removed, "freed": freed, "failed": failed,
           "total": p["total"], "after": p["total"] - freed}
    if p["need"] is None:
        # REG-2754 (GrokBot's v3823 pass: 0.74 GB here, "Grok sessions 0.82 GB" on the sign's list) - the budget counts the
        # conversation folders, and the sign's list measures the whole sessions folder; the words say which
        rec["say"] = "not needed - the Grok chats (their conversation folders) hold %.2f GB, under the %.0f GB budget, and the disk is over its floor" % (
            p["total"] / 1e9, BUDGET_BYTES / 1e9)
    elif live is None:
        rec["say"] = "needed (%s) but %s - nothing pruned" % (p["need"], p["keep_why"])
    else:
        rec["say"] = "needed (%s): pruned %d old chat(s), %.2f GB; %s%s" % (
            p["need"], len(removed), freed / 1e9, p["keep_why"], (" - %d could not be removed" % failed) if failed else "")
        if receipt_path and (removed or failed):
            try:
                with open(receipt_path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec) + "\n")
            except Exception:
                rec["say"] += " (the receipt could not be written)"
    return rec
