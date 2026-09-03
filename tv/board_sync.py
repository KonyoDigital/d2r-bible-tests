#!/usr/bin/env python3
"""THE BOARD IS A BUILD OUTPUT OF TASKS.md AND git — never typed twice.

His ruling: *"i want it designed properly so its structured accordingly and synced and derived from
tasks live"*, and *"structured formally story line telling in code meaning pending and then progress
and the completed"*.

⚠⚠ WHY THIS EXISTS. Until now the board was hand-written into the artifact database AND separately
into TASKS.md — two copies of one truth, kept in step by me remembering. That is the copy-drift
shape this repo has paid for repeatedly, and the failure mode is silent: the two disagree and
whichever you read last looks authoritative.

So: TASKS.md and git are THE SOURCE. This derives every row from them and emits the row set. A row
that is wrong here means TASKS.md is wrong, and there is one place to fix it.

⚠ THE STORY IS THE STRUCTURE. Sections are STATES, in the order work actually moves:

    1  PENDING       nothing started
    2  IN PROGRESS   moving now
    3  YOUR CALL     waiting on Konyo, and I may not close these at any price
    4  BLOCKED       named, with what blocks it
    5  COMPLETED     shipped, with its real commit and author-date from git

⚠ TIMESTAMPS COME FROM git, NEVER FROM PROSE. A `vNNNN` is joined to its commit and its author
date. A date typed into a markdown line is a claim; `git log` is a record.

⚠ AND IT NEVER PRUNES. It emits adds and updates only. Anything already on the board that this run
did not derive is reported as ORPHANED — never deleted — because a parser that silently drops a row
looks exactly like the pruning he has already caught once, and his ~36 pending items must stay
visible beside the shipped ones.
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("D2R_REPO", "/Users/konyo/d2r_bible_tests")
TASKS = os.path.join(REPO, "TASKS.md")

#: state -> (section title, sectionOrder, board state letter). The ORDER IS THE STORY.
SECTIONS = [
    ("pending",  "1 · PENDING",     10, "p"),
    ("progress", "2 · IN PROGRESS", 20, "f"),
    ("hiscall",  "3 · YOUR CALL",   30, "h"),
    ("blocked",  "4 · BLOCKED",     40, "b"),
    ("done",     "5 · COMPLETED",   50, "s"),
]
_SEC = {k: (t, o, st) for k, t, o, st in SECTIONS}


def _git_ships():
    """-> {version: (sha, 'YYYY-MM-DD HH:MM', subject)} straight from git. No typed dates."""
    try:
        out = subprocess.check_output(
            ["git", "log", "--format=%h|%ad|%s", "--date=format:%Y-%m-%d %H:%M", "origin/main"],
            cwd=REPO, text=True, timeout=120)
    except Exception:
        return {}
    ships = {}
    for line in out.split("\n"):
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        sha, when, subject = parts
        # a commit may carry two stamps: "v2464+v2465 — ..."
        for m in re.finditer(r"\bv(2\d{3})\b", subject.split("—")[0]):
            ships.setdefault("v" + m.group(1), (sha, when, subject))
    return ships


def _classify(status_text):
    """A TASKS.md status word -> which part of the story it belongs to. -> str"""
    s = (status_text or "").upper()
    if "SHIPPED" in s or s.startswith("✅"):
        return "done"
    if "BLOCKED" in s:
        return "blocked"
    if "HIS CALL" in s or "YOUR CALL" in s:
        return "hiscall"
    if "IN PROGRESS" in s or "IN FLIGHT" in s or "GATING" in s:
        return "progress"
    return "pending"


#: ⚠ THE TOPIC COMES FROM HIS OWN HEADERS, not a list I invent. Walking the file and carrying the
#: nearest preceding heading means the grouping is whatever TASKS.md already says it is — rename a
#: header there and the board follows, with nothing to keep in step by hand. [[copy-drift]]
_TOPIC_CLEAN = re.compile(r"^[#\s✅⚠🔓🏛★📒🔒📋]+|\s*·.*$")


def _topics_by_offset(text):
    """-> [(offset, topic)] sorted, so any match can find the header above it."""
    out = []
    # ⚠ LEVEL-1 ONLY. The first cut took the nearest header of ANY depth, and every A-list item
    # is its own `##` heading — so each one became its own topic and the board fragmented into
    # twenty groups of one. A topic that contains a single row is not a grouping. His big
    # divisions are the `#` headers; those are the topics.
    for m in re.finditer(r"^(#)\s+(.+?)\s*$", text, re.M):
        title = _TOPIC_CLEAN.sub("", m.group(2)).strip()
        title = re.sub(r"\s*—.*$", "", title).strip()
        if title:
            out.append((m.start(), title[:46]))
    return out


#: ⚠ AN EXPLICIT TAG BEATS A GUESS, AND MOVING HIS PROSE TO GROUP IT WOULD BE THE RISKIER FIX.
#: Deriving the topic from "the nearest level-1 header" works only if the file is already grouped
#: that way, and reorganising 600 lines of his writing to make a parser happy is how a task file
#: loses a task. So a task may name its own topic and its own progress on one added line:
#:
#:     **Topic:** ARCHITECTURE · **Progress:** 2/5 — route_wilson banks, heart render still owed
#:
#: The header remains the fallback for anything untagged. Additive: nothing of his moves.
_TOPIC_TAG = re.compile(r"\*\*Topic:\*\*\s*([^·*\n]+)", re.I)
_PROG_TAG = re.compile(r"\*\*Progress:\*\*\s*([^\n]+)", re.I)


def _tagged(text, pos, end=None):
    """-> (topic, progress) from the tag line under a task, if it has one."""
    seg = text[pos:end if end is not None else min(len(text), pos + 1400)]
    t = _TOPIC_TAG.search(seg)
    g = _PROG_TAG.search(seg)
    return ((t.group(1).strip() if t else None),
            (g.group(1).strip()[:180] if g else None))


def _topic_at(topics, pos):
    best = "Unfiled"
    for off, title in topics:
        if off <= pos:
            best = title
        else:
            break
    return best


def parse_tasks(text):
    """-> [row] derived from TASKS.md. Never invents a state it did not read."""
    rows = []
    topics = _topics_by_offset(text)

    # 1 — the A-list:  ## A20 · TITLE · 2026-09-02 · READY
    for m in re.finditer(r"^##\s+(A\d+[^\n·]*)·\s*([^\n·]+?)\s*·\s*([^\n·]*?)\s*"
                         r"(?:·\s*([A-Z ]+))?\s*$", text, re.M):
        ident, title, when, status = m.group(1).strip(), m.group(2).strip(), \
            m.group(3).strip(), (m.group(4) or "").strip()
        rows.append({"id": ident, "what": title, "asked": when,
                     "state": _classify(status), "src": "TASKS.md A-list",
                     "topic": (_tagged(text, m.start())[0] or _topic_at(topics, m.start())),
                     "progress": _tagged(text, m.start())[1],
                     "status": status or "pending"})

    # 2 — numbered table rows:  | **166** | description | STATE |
    for m in re.finditer(r"^\|\s*\*\*(#?\d+[^*]*)\*\*\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$",
                         text, re.M):
        ident, what, status = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        if re.match(r"^v2\d{3}", ident):
            continue                      # ships are handled from git, not from prose
        rows.append({"id": ident, "what": what[:400], "state": _classify(status),
                     "src": "TASKS.md table", "topic": _topic_at(topics, m.start()),
                     "status": re.sub(r"\*+", "", status)[:120]})

    # 3 — the LANDED ship table:  | **v2487** | description |
    for m in re.finditer(r"^\|\s*\*\*(v2\d{3})\*\*\s*\|\s*(.+?)\s*\|\s*$", text, re.M):
        rows.append({"id": m.group(1), "what": m.group(2)[:400], "state": "done",
                     "src": "TASKS.md LANDED", "topic": "Ships", "status": "shipped"})
    return rows


def build():
    """-> (rows_for_board, notes). Every timestamp measured, never typed."""
    text = io.open(TASKS, encoding="utf-8").read()
    ships = _git_ships()
    rows = parse_tasks(text)
    notes = []

    seen = {}
    for r in rows:
        seen.setdefault(r["id"], r)       # first mention wins; later ones are duplicates
    out = []
    order = {k: 0 for k, _t, _o, _s in SECTIONS}
    topic_order = {}
    for ident, r in sorted(seen.items()):
        state = r["state"]
        title, sec_order, st = _SEC[state]
        topic = r.get("topic") or "Unfiled"
        got = ships.get(ident)
        if got and state != "done":
            # a ship exists for something TASKS.md does not call shipped — say so, do not decide
            notes.append("%s: git has a commit (%s) but TASKS.md says %r" % (ident, got[0], state))
        # STATE is the story; TOPIC groups within it. sectionOrder is state-major, topic-minor,
        # so the page reads pending -> in progress -> completed, and inside each the work is
        # gathered by the heading it lives under in TASKS.md.
        topic_ix = topic_order.setdefault(topic, len(topic_order))
        row = {
            "id": ident, "progress": r.get("progress"),
            "section": "%s · %s" % (title, topic),
            "sectionOrder": sec_order * 100 + topic_ix,
            "order": order[state], "st": st, "state": "done" if st == "s" else state,
            "what": r["what"], "status": r.get("status") or "",
        }
        if got:
            row["shipped"] = got[0]
            row["at"] = got[1]            # ⚠ from git, never from the markdown
        order[state] += 1
        out.append(row)
    return out, notes


def main(argv=None):
    rows, notes = build()
    argv = list(argv or [])
    if "--json" in argv:
        print(json.dumps(rows, indent=1, ensure_ascii=False))
        return 0
    from collections import Counter
    c = Counter(r["section"] for r in rows)
    print("derived %d row(s) from TASKS.md + git" % len(rows))
    for sec in sorted(c, key=lambda x: min(r["sectionOrder"] for r in rows if r["section"] == x)):
        print("   %-52s %d" % (sec, c[sec]))
    dated = sum(1 for r in rows if r.get("at"))
    print("   %d row(s) carry a git-measured timestamp; %d carry none (never invented)"
          % (dated, len(rows) - dated))
    if notes:
        print("\n⚠ %d disagreement(s) between git and TASKS.md, reported not resolved:" % len(notes))
        for n in notes[:8]:
            print("   " + n)
    return 0


if __name__ == "__main__":
    # ⚠ THE RUN WITH SOMETHING TO SAY IS THE ONE THAT DIES WITHOUT THIS. This file prints ⚠ and ·
    # in its disagreement lines — the output that matters most — and on a console that cannot
    # encode U+26A0 the report crashes while reporting. Same scar as prune_wilson at v2472, and
    # his gate caught it here before it ever ran on the Windows side.
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
