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

#: state -> (section title, sectionOrder BASE, board state letter). THE ORDER IS THE STORY.
#:
#: ⚠⚠ NEGATIVE, AND THAT IS LOad-BEARING. The board carries older sections at 0..11 from before the
#: storyline existed, so a stage numbered positively sorts BELOW the very rows it is meant to
#: organise — shipped once as v2490, where the whole pending → progress → completed structure was
#: published and unreachable underneath them. Anything new here stays negative.
#:
#: ⚠ HIBERNATING and RETIRED are not stages of work, they are HIS RULINGS about the work, and they
#: sit after COMPLETED because the story runs pending → progress → done and a decision is off that
#: river. They exist because on 2026-09-03 he retired A6 and hibernated A18/A20, and re-running the
#: deriver the same afternoon put all three back into PENDING: a board that is a build output
#: cannot hold a decision the build does not understand. [[the-unjoined-end]]
#: ⚠ SPACED 20 APART, AND THE FIRST SPACING WAS TOO TIGHT — the guard below refused the build twice
#: before this table was right. -45/-44 gave HIBERNATING a single slot while it already holds two
#: topics (A20 is VISUAL, A18 is CAPTURE). Twenty is not decoration: it is the number of distinct
#: TASKS.md headings one stage can hold before a topic would renumber into the next stage.
SECTIONS = [
    ("pending",     "1 · PENDING",     -200, "p"),
    ("progress",    "2 · IN PROGRESS", -180, "f"),
    ("hiscall",     "3 · YOUR CALL",   -160, "h"),
    ("blocked",     "4 · BLOCKED",     -140, "b"),
    ("done",        "5 · COMPLETED",   -120, "s"),
    ("hibernating", "6 · HIBERNATING", -100, "h"),
    ("retired",     "7 · RETIRED",      -80, "x"),
]
_SEC = {k: (t, o, st) for k, t, o, st in SECTIONS}

#: How many topic slots each stage owns before it would collide with the next stage's base. A
#: collision does not error — it silently files one stage's topic INTO the next stage, which is a
#: task appearing under the wrong heading with nothing to notice it. Computed, never typed.
_ROOM = {SECTIONS[i][0]: (SECTIONS[i + 1][2] - SECTIONS[i][2]) if i + 1 < len(SECTIONS) else 40
         for i in range(len(SECTIONS))}


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


def _classify(status_text, progress=None):
    """Where a task sits in the story. -> str

    ⚠⚠ THE PROGRESS OUTRANKS THE HEADER WORD, AND THE FIRST CUT IGNORED IT. A task's `##` header
    carries a status like READY, which describes whether it MAY be started — not whether it HAS
    been. So A1 (1/4 done), A2 (3/4 done), A9, A11, A13 and A17 all filed as PENDING while their
    own Progress line said otherwise, and the board showed an empty IN PROGRESS column beside six
    items that were visibly moving. A row that says "3/4" and sits under "nothing started" is
    telling the reader two different things, and the wrong one is louder.

    So: read the PROGRESS first, and only fall back to the header word when the progress line says
    nothing. A fraction like 0/1 is explicitly NOT progress — it is the honest form of not-started.
    """
    prog = (progress or "").strip()
    if prog:
        up = prog.upper()
        # ⚠⚠ HIS DECISIONS OUTRANK EVERYTHING, INCLUDING A PROGRESS FRACTION. RETIRED and
        # HIBERNATING are not stages of work — they are rulings ABOUT the work, and they are
        # checked first because an item he cut still carries whatever progress text it had when he
        # cut it. A6 reads "0/1 not started" and is RETIRED; without this the fraction wins and the
        # board files a decision as a to-do.
        #
        # These two states exist because he made those calls on 2026-09-03 and the deriver put all
        # three items back into PENDING the same afternoon. A build output cannot hold a decision
        # the build does not understand. [[the-unjoined-end]]
        # ⚠⚠ THE MARKER MUST OPEN THE LINE, and my first cut matched it ANYWHERE — which retired a
        # task that was merely describing a cut. A1 reads "1/3 · v2485 ... ⛔ SCOPE CUT ... one
        # sub-goal is OUT", an item very much in progress that happens to mention a ruling about
        # part of itself, and it was filed under RETIRED whole. THE COUNT WAS THE TELL: two rows in
        # a stage where exactly one thing had been retired.
        #
        # A ruling is a statement about THIS task and it is written at the front of the progress
        # line; a ruling mentioned mid-sentence is a task TALKING about a decision, not carrying
        # one. [[feedback-suspect-the-instrument]]
        if re.match(r"^[⛔\s]*RETIRED\b", prog, re.I) or prog.startswith("⛔"):
            return "retired"
        if re.match(r"^[⏸\s]*HIBERNAT", prog, re.I) or prog.startswith("⏸"):
            return "hibernating"
        m = re.match(r"^\s*(\d+)\s*/\s*(\d+)", prog)
        if m:
            done, total = int(m.group(1)), int(m.group(2))
            if done >= total > 0:
                return "done"
            if done > 0:
                return "progress"
            # 0/N is not-started, said honestly — fall through to the header word
        elif "IN PROGRESS" in up or up.startswith("MEASURED") or up.startswith("PROVEN"):
            return "progress"
        elif "SHIPPED" in up or up.startswith("✅"):
            return "done"
        elif "BLOCKED" in up:
            return "blocked"
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


#: Where each state sits in the storyline he asked for — pending, then progress, then completed,
#: with the two OFF-RIVER states after it. Negative because the board's older sections occupy 0..11
#: and a new stage must sort ABOVE them, not below; that ordering bug shipped once already (v2490,
#: the storyline was published and unreachable underneath the sections it was meant to replace).
def story_of(state):
    """-> (label, sectionOrder) for a state. UNKNOWN states are NOT silently filed as pending.

    ⚠ A state this table does not know returns its own name rather than a default, so a new state
    added to _classify and forgotten here shows up as an odd section a person notices — instead of
    quietly joining PENDING, which is exactly how a retired item comes back to life.
    """
    # ⚠ READS `SECTIONS`, WHICH IS THE ONLY TABLE. My first cut of this function carried its own
    # copy of the same seven states — a second source, written the same hour as a fix for two
    # sources disagreeing. [[copy-drift]] §1: name ONE source, everything else quotes it.
    if state in _SEC:
        title, order, _st = _SEC[state]
        return (title, order)
    return ("? · %s — a state the storyline does not know" % str(state).upper(), -10)


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
    # ⚠⚠ THE TITLE MAY CONTAIN THE SEPARATOR, AND A17 PROVED IT BY VANISHING. Its heading is
    # "## A17 · THE TV·D CONSOLE NEEDS AN EDITORIAL REDESIGN · 2026-09-01 20:0x" — the "·" inside
    # TV·D is the same character this splits on, so the pattern failed to match and the task was
    # not merely mis-filed, it was ABSENT from the board with nothing saying so. A parser that
    # silently loses a row is indistinguishable from the pruning he has already caught once.
    # Split from the RIGHT on the trailing date/status instead, so the title keeps whatever it
    # contains. The coverage check below is the real guard: it counts headers against rows.
    for m in re.finditer(r"^##\s+(A\d+)\s*·\s*(.+?)\s*$", text, re.M):
        ident = m.group(1).strip()
        rest = m.group(2).strip()
        # trailing "· STATUS" and "· date" are peeled from the RIGHT; the rest is the title
        status = ""
        mstat = re.search(r"·\s*([A-Z][A-Z ]{2,})\s*$", rest)
        if mstat:
            status = mstat.group(1).strip()
            rest = rest[:mstat.start()].rstrip()
        when = ""
        mwhen = re.search(r"·\s*(\d{4}-\d{2}-\d{2}[^·]*)$", rest)
        if mwhen:
            when = mwhen.group(1).strip()
            rest = rest[:mwhen.start()].rstrip()
        title = rest
        rows.append({"id": ident, "what": title, "asked": when,
                     "state": _classify(status, _tagged(text, m.start())[1]),
                     "src": "TASKS.md A-list",
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


def coverage(text, rows):
    """Every `## AN ·` header in the file must reach a row. -> (missing, total)

    ⚠ THIS IS THE ONE THAT MATTERS. The generator promises it never prunes — but a row that fails
    to PARSE was never a row, so it cannot be reported as orphaned and simply is not there. A17
    was absent for exactly that reason and nothing said so. Counting headers against derived rows
    is the only check that catches a silent loss. [[unknown-stays-unknown]]
    """
    heads = set(re.findall(r"^##\s+(A\d+)\s*·", text, re.M))
    got = {r["id"] for r in rows}
    return sorted(heads - got), len(heads)


def build():
    """-> (rows_for_board, notes). Every timestamp measured, never typed."""
    text = io.open(TASKS, encoding="utf-8").read()
    ships = _git_ships()
    rows = parse_tasks(text)
    notes = []
    missing, total_heads = coverage(text, rows)
    if missing:
        notes.append("⚠ %d of %d A-headers produced NO ROW and would be invisible: %s"
                     % (len(missing), total_heads, ", ".join(missing)))

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
        # ⚠⚠ PER STAGE, NOT GLOBAL — and the global version was a latent mis-file that only became
        # visible when the bases moved. `topic_order` was ONE dict for the whole file, so a topic's
        # index kept climbing across stages: VISUAL sat at index 5 everywhere, and under IN PROGRESS
        # (-80) that numbered it to -75, which IS the base of YOUR CALL. The old scheme multiplied
        # the base by 100 and so had room to hide it. The index means "which topic within THIS
        # stage", so it is counted within the stage.
        topic_ix = topic_order.setdefault((state, topic), len([k for k in topic_order if k[0] == state]))
        # ⚠⚠ A TOPIC THAT OVERFLOWS ITS STAGE LANDS IN THE NEXT STAGE, SILENTLY. The base numbers
        # are 20-30 apart and topic_ix is a running count, so the 21st topic under PENDING would
        # be numbered into IN PROGRESS and render as a task that had started. Nothing would error.
        # Refuse instead — a board that stops is recoverable, one that mis-files is not.
        room = _ROOM.get(state, 40)
        if topic_ix >= room:
            raise SystemExit(
                "REFUSED: stage %r has %d topic(s) but only %d slot(s) before it collides with the "
                "next stage. Widen the SECTIONS bases; do not let a topic renumber into another "
                "stage." % (state, topic_ix + 1, room))
        row = {
            "id": ident, "progress": r.get("progress"),
            "section": "%s · %s" % (title, topic),
            "sectionOrder": sec_order + topic_ix,
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
