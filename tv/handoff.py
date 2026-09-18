# -*- coding: utf-8 -*-
"""Drain a handoff queue in O(new), not O(all) — and never lose a brief to a watermark.

Measured 2026-09-18, the reason this exists: issue #180 held 1,177 comments / 2.55 MB, and 140
comments (536 KB) arrived in one day against 10 replies. `gh issue view --comments` fetches the
WHOLE history to show the newest, so every drain paid 2.55 MB to read 6 new briefs. A queue that
expensive to read stops being read, which is exactly what happened.

This reads only what arrived since the last watermark, using the REST `since` parameter, and it
sorts the ASK / ACT lines to the top because the old format buried them under the evidence.

⚠ THE WATERMARK MOVES ONLY WHEN YOU SAY SO (`--mark`). Draining does NOT advance it. A drain that
silently marked-as-read would lose every brief that arrived while the reader was mid-answer, and an
unanswered brief that no longer appears is worse than a noisy queue — it is a queue that lies.
[[the-unjoined-end]] [[unknown-stays-unknown]]
"""
import argparse
import io
import json
import os
import subprocess
import sys

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from console_safe import enable as _cs
    _cs()
except Exception:
    pass

REPO = "KonyoDigital/d2r-bible-tests"
HERE = os.path.dirname(os.path.abspath(__file__))
MARKS = os.path.join(HERE, ".handoff_seen.json")

#: The lead-line verbs of protocol v2. ACT and ASK are owed an answer; FYI is not.
OWED = ("ACT", "ASK")


def _gh(path, method=None, fields=None):
    cmd = ["gh", "api", path, "--paginate"]
    if method:
        cmd = ["gh", "api", "-X", method, path]
    for k, v in (fields or {}).items():
        cmd += ["-f", "%s=%s" % (k, v)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or "").strip()[:300])
    body = (p.stdout or "").strip()
    if not body:
        return []
    # ⚠ --paginate CONCATENATES JSON DOCUMENTS with no separator, and they may be pretty-printed,
    # so neither splitlines() nor a "][" replace is safe: a fragment can parse as a bare int and
    # sail through as a "row". That is exactly how the first cut produced
    # `'int' object has no attribute 'get'` on #179 — a parse error wearing the costume of data.
    # raw_decode walks the stream one complete document at a time. [[unknown-stays-unknown]]
    dec = json.JSONDecoder()
    out, i, n = [], 0, len(body)
    while i < n:
        while i < n and body[i] in " \t\r\n":
            i += 1
        if i >= n:
            break
        try:
            got, i = dec.raw_decode(body, i)
        except ValueError:
            break
        for row in (got if isinstance(got, list) else [got]):
            if isinstance(row, dict):
                out.append(row)
    return out


def _marks():
    """-> dict of watermarks, or None when the store cannot be READ.

    ⚠⚠ v3325 — ABSENT AND UNREADABLE ARE DIFFERENT FACTS, and collapsing them here is destructive
    rather than merely vague. `--mark` does `marks = _marks()`, adds one key, and writes the WHOLE
    DICT BACK. Returning {} for a corrupt or unreadable file therefore writes {} + one key OVER A
    GOOD STORE, destroying every other watermark — in the tool that drains his queue.
    MEASURED 2026-09-18: tv/.handoff_seen.json holds keys 179, 180, 230; the path was LATENT, not
    fired. The rule is the one `_vault_autoread_save` already earned: never write memory over a
    store this process has not read. [[unknown-stays-unknown]]
    """
    try:
        with io.open(MARKS, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else None
    except IOError:
        return {}            # absent: nothing marked yet, and that IS a measurement
    except Exception:
        return None          # malformed/unreadable: UNKNOWN


def _classify(body):
    """-> ('ACT'|'ASK'|'FYI'|'?', first_meaningful_line). Protocol v2 leads with the verb."""
    for raw in (body or "").splitlines():
        line = raw.strip().lstrip("#* ").strip()
        if not line or line.startswith("```"):
            continue
        for verb in ("ACT", "ASK", "FYI"):
            if line.upper().startswith(verb):
                return verb, line[:200]
        # pre-v2 briefs: no lead verb. Say so rather than guessing a priority.
        return "?", line[:200]
    return "?", "(empty body)"


def drain(issue, since=None, limit=40):
    marks = _marks()
    key = str(issue)
    if marks is None:
        # UNKNOWN watermark: drain from the beginning, and SAY so. Silently starting at zero
        # reads as "the queue is enormous" rather than "the store could not be read".
        print("⚠ the watermark store could not be READ — draining #%s from the beginning. "
              "That is UNKNOWN, not an empty queue." % issue)
        marks = {}
    since = since or marks.get(key, {}).get("ts")
    path = "repos/%s/issues/%s/comments?per_page=100" % (REPO, issue)
    if since:
        path += "&since=%s" % since
    rows = _gh(path)
    # ⚠ GITHUB'S `since` IS INCLUSIVE, so the very comment the watermark points AT comes back as
    # "new" on every drain. Left alone this queue reads "1 new" forever — and a queue that is never
    # empty is one a reader learns to skip, which is the exact habit this tool exists to break.
    # Drop the watermarked id explicitly rather than nudging the timestamp, because a nudge would
    # silently swallow anything posted inside the same second. [[zero-needs-a-denominator]]
    _mark = marks.get(key) or {}
    _seen_id, _seen_upd = _mark.get("id"), _mark.get("updated")
    if _seen_id is not None:
        # ⚠ EXCLUDE IT ONLY IF IT HAS NOT CHANGED SINCE. Protocol v2 has each seat EDIT one rolling
        # `📍 STATE` comment, and GitHub's `since` filters on UPDATED — so a watermarked comment
        # that is later edited is NEW INFORMATION. A blanket exclude-by-id would hide every future
        # edit of whichever comment the watermark happened to land on: a filter that silently drops
        # real content, which is the same class of defect this tool exists to surface.
        rows = [c for c in rows
                if c.get("id") != _seen_id
                or (_seen_upd is not None and c.get("updated_at") != _seen_upd)]
    rows.sort(key=lambda c: c.get("created_at") or "")

    print("queue #%s — %d new since %s" % (issue, len(rows), since or "THE BEGINNING (no watermark)"))
    if not since:
        print("  no watermark set. This is every comment on the issue, not a delta.")
    if not rows:
        print("  nothing new. That is a measured zero, not a failure to look.")
        return rows

    buckets = {"ACT": [], "ASK": [], "FYI": [], "?": []}
    for c in rows:
        verb, lead = _classify(c.get("body"))
        buckets[verb].append((c, lead))

    print("  %d ACT · %d ASK · %d FYI · %d pre-v2 (no lead verb)"
          % (len(buckets["ACT"]), len(buckets["ASK"]), len(buckets["FYI"]), len(buckets["?"])))
    for verb in ("ACT", "ASK", "?", "FYI"):
        got = buckets[verb]
        if not got:
            continue
        print("\n── %s ──" % verb)
        for c, lead in got[:limit]:
            print("  #%s  %s  %s" % (c.get("id"), (c.get("created_at") or "")[:16], lead))
        if len(got) > limit:
            print("  … +%d more not listed (raise --limit)" % (len(got) - limit))

    newest = rows[-1]
    print("\n  newest: #%s at %s" % (newest.get("id"), newest.get("created_at")))
    print("  answer the ACT/ASK rows, then: handoff.py --issue %s --mark" % issue)
    print("  ⚠ the watermark has NOT moved — draining never marks anything read.")
    return rows


def mark(issue):
    rows = _gh("repos/%s/issues/%s/comments?per_page=100" % (REPO, issue))
    if not rows:
        print("no comments; watermark unchanged.")
        return
    rows.sort(key=lambda c: c.get("created_at") or "")
    newest = rows[-1]
    marks = _marks()
    if marks is None:
        # ⚠⚠ REFUSE, DO NOT OVERWRITE. Writing here would replace a store this process could not
        # read with {} plus one key, and the file would then look authoritative — strictly worse
        # than not marking at all. [[unknown-stays-unknown]]
        print("⚠ REFUSED to advance the watermark: %s could not be READ, and writing now would "
              "destroy every other issue's mark. Fix or remove the file, then re-run." % MARKS)
        return
    marks[str(issue)] = {"id": newest.get("id"), "ts": newest.get("created_at"),
                         "updated": newest.get("updated_at")}
    with io.open(MARKS, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(marks, indent=2, sort_keys=True))
    print("watermark for #%s -> %s (#%s)" % (issue, newest.get("created_at"), newest.get("id")))


def archive(issue, path):
    rows = _gh("repos/%s/issues/%s/comments?per_page=100" % (REPO, issue))
    rows.sort(key=lambda c: c.get("created_at") or "")
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rows, indent=1, sort_keys=True, ensure_ascii=False))
    total = sum(len(c.get("body") or "") for c in rows)
    print("archived %d comment(s), %s body bytes -> %s" % (len(rows), format(total, ","), path))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # ⚠⚠ THE LEGACY QUEUES ARE STILL DRAINED, AND THAT IS NOT BELT-AND-BRACES. #179/#180 were
    # rotated CLOSED on 2026-09-18 — but GitHub ACCEPTS COMMENTS ON CLOSED ISSUES, and the seats
    # post from their own schedulers which may still name the old number. Draining only #230 would
    # report a confident "0 new" while briefs piled into a thread nobody reads: a rotation that
    # orphans the far end is the-unjoined-end wearing a tidy-up costume, and the zero would look
    # exactly like peace. Drop a legacy id only once that seat has been SEEN posting to #230.
    ap.add_argument("--issue", default="230,180,179",
                    help="comma-separated; 230 is the live queue, 180/179 are closed but still "
                         "writable and are drained until each seat is seen to have moved")
    ap.add_argument("--since", default=None, help="ISO8601; overrides the stored watermark")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--mark", action="store_true", help="advance the watermark to the newest comment")
    ap.add_argument("--archive", metavar="PATH", help="write every comment to PATH as JSON")
    a = ap.parse_args(argv)

    issues = [i.strip() for i in str(a.issue).split(",") if i.strip()]
    if a.archive:
        for i in issues:
            archive(i, a.archive if len(issues) == 1 else "%s.%s" % (a.archive, i))
        return 0
    if a.mark:
        for i in issues:
            mark(i)
        return 0
    live = 0
    for i in issues:
        rows = drain(i, since=a.since, limit=a.limit)
        live += len(rows or [])
        print("")
    if live == 0:
        print("all %d queue(s) quiet — a measured zero across every one, legacy included."
              % len(issues))
    return 0


if __name__ == "__main__":
    sys.exit(main())
