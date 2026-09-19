#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the second eye over a shipped version, end to end, in one command.

    python3 tv/second_eye_run.py v2802
    python3 tv/second_eye_run.py --backlog        # every version that still OWES a look
    python3 tv/second_eye_run.py v2802 --dry      # build and MEASURE the payload, send nothing

WHY THIS EXISTS. Every look used to be assembled by hand: find the commit, pull the diff, strip the
comments, paste it into a chat, read the answer back, and type the ledger row. Six manual steps per
version, and versions ship in batches of three or four.

⚠⚠ THE HAND-ASSEMBLY DID NOT MERELY COST TIME — IT PUT A FABRICATED NUMBER IN AN EVIDENCE LEDGER.
Recording v2801 by hand, the `sentCode` field was filled with `{"chars": 7250, "fences": 3}` typed
from an estimate, because `code_was_transmitted()` takes the PROMPT TEXT and returns that dict, and
it was handed a dict instead. It returned `{"chars": 0, "fences": 0}` — the honest answer to the
wrong question — and the invented value went into the row. The real figure, measured afterwards
from the actual payload, was 7,366. The ledger exists precisely so a claim of "a different family
looked at this" is checkable, and the one field that proves code was really transmitted had been
typed rather than measured. A number nobody measured is not evidence, however plausible it looks.
[[unknown-stays-unknown]] [[paid-work-with-no-memory]]

So: the payload is built by this script, MEASURED by this script from the bytes it is about to
send, and recorded by this script from what actually came back. There is no step where a human
number enters the row.

⚠ COLD MEANS COLD. The framing below is fixed and says nothing about what the code should do, what
changed, or what anyone suspects. The diff's own comments are stripped, because this repo's comments
routinely NAME the defect and its fix — handing them over would be asking the eye to agree with the
author rather than to look. [[feedback-comments-vs-code]]

⚠ AN UNREACHABLE EYE IS AN EMPTY SEAT. A CLI that fails, times out, or answers nothing is recorded
with reached=False and NO verdict. It is never silence-as-agreement.
[[feedback-silence-is-not-evidence]]
"""
import argparse
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_ledger as SEL  # noqa: E402

# The eye. Overridable so this is not welded to one vendor — a previous version of this lane was
# hardwired to one CLI and was therefore PERMANENTLY EMPTY on every machine but his.
EYE_CLI = os.environ.get("THIRD_EYE_CLI") or os.path.expanduser("~/.grok/bin/grok")
EYE_MODEL = os.environ.get("THIRD_EYE_MODEL") or "grok-4-1-fast-reasoning"
EYE_TIMEOUT_S = float(os.environ.get("THIRD_EYE_TIMEOUT_S") or 300)

# A prompt has to fit. Truncation is allowed; SILENT truncation is not — what was dropped is
# reported in the row, so a thin look can never read as a thorough one.
# MEASURED, not guessed: a 7,366-char payload came back in seconds; 24,000 chars timed out at
# 240s and was correctly recorded as an EMPTY SEAT. A cap above what the eye can actually chew
# turns every look into a non-look, which is the same "threshold above the ceiling" that made the
# runaway guard unreachable. [[feedback-threshold-above-the-ceiling]]
MAX_FENCE_CHARS = 9000

# ⚠ THAT CEILING BELONGS TO ONE TRANSPORT, NOT TO THE TRUTH. 9,000 is what the CLI can chew in an
# INLINE fence. A file-upload transport is a different pipe with a different ceiling, and holding
# every transport to the narrowest one is why v2806 and v2807 were both looked at through ~32% of
# their diffs — which is how two FALSE high-severity findings got manufactured this session, each
# reasoning correctly about a function my own cap had cut in half.
#
# So the cap is now an ARGUMENT with the CLI's value as its default. It is not raised blindly:
# whatever is actually sent is measured from the bytes and recorded, so a look through a third of
# a diff can never be filed as a look at all of it. [[unknown-stays-unknown]]
def _cap():
    return int(os.environ.get("SECOND_EYE_MAX_CHARS") or MAX_FENCE_CHARS)


COLD_FRAMING = (
    "Code review. The following is a diff of source that has already shipped.\n\n"
    "List concrete defects, ranked by severity, each with the specific scenario in which it "
    "fails. Include races, unreachable states, resource leaks, and any place a caller and a "
    "callee disagree about a contract. If you believe it is correct, say so plainly rather than "
    "inventing a finding.\n"
)


def _sh(args, timeout=60):
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=REPO)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        return None, "timed out after %ss" % timeout
    if p.returncode != 0:
        return None, (err or b"").decode("utf-8", "replace")[:300]
    return out.decode("utf-8", "replace"), ""


# ⚠ ANCHORED AT THE START, because the repo stamps a ship as "v2853 — ..." while a follow-up
# says "fix: the v2804 row narrated the catcher". MEASURED over 400 subjects: 252 start with
# a version, 19 merely mention one. The loose form counted v1554 as a ship because a later
# commit talked about it. [[label-outlived-referent]]
# ⚠⚠ v2862 — AND A COMMIT MAY SHIP MORE THAN ONE VERSION. The v2854 anchor was right to
# reject "fix: the v2804 row narrated the catcher" — but it took only the FIRST token, so a
# subject reading "v2859+v2860 — ..." registered v2859 and made v2860 INVISIBLE to the queue.
# MEASURED 2026-09-09: the pre-push gate refused with "v2860 OWES A LOOK" while --backlog
# listed v2861 and v2859 and could not see v2860 at all. Two checks disagreed and the quiet
# one was wrong again, for a NEW reason. [[feedback-contradiction-is-the-finding]]
#
# The LEADING RUN only: v2859+v2860 both count, and a version mentioned later in the same
# subject still does not — which is the protection the anchor was added for.
_VER_LEADING_RUN = re.compile(r"^(v\d{4}(?:\s*[+,&]\s*v\d{4})*)\b")
_VER_TOKEN = re.compile(r"v\d{4}")


#: ⚠⚠ v3316 — A HYPHEN IS A RANGE, AND THIS REPO WRITES ONE. `_VER_LEADING_RUN` accepts `+`, `,`
#: and `&` between versions because v2862 was bitten by "v2859+v2860 — ..." registering only
#: v2859. The SAME defect returned with a hyphen: `0bf8cb6d` is titled "v3304-v3307" and ships
#: FOUR versions, of which the parser saw one — so v3305 and v3306 were invisible to the backlog
#: and shipped with no second-eye look at all. Measured over 200 subjects on origin/main: 1
#: hyphen range, hiding 3 versions.
#:
#: ⚠ THE SEPARATOR MUST NOT EAT THE TITLE. Subjects read "v3312 — the river ..." with a spaced
#: EM-DASH; a range is a bare hyphen-minus with no spaces between two version tokens. Requiring
#: `v\d{4}-v\d{4}` adjacency is what keeps the two apart, and the title case is pinned in the law.
_VER_RANGE = re.compile(r"^v(\d{4})-v(\d{4})\b")


def versions_in_run(subject):
    """Every version a commit subject SHIPS, expanding a range. -> [vNNNN]

    Only the LEADING run counts, which is v2854's protection and it survives unchanged: a subject
    reading "fix: the v2804 row narrated the catcher" ships nothing.
    """
    s = str(subject or "").strip()
    m = _VER_RANGE.match(s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        # A backwards or absurd range is not a range. Refusing beats inventing 900 versions.
        if b < a or (b - a) > 24:
            return ["v%04d" % a]
        return ["v%04d" % n for n in range(a, b + 1)]
    m = _VER_LEADING_RUN.match(s)
    if not m:
        return []
    out, seen = [], set()
    for tok in _VER_TOKEN.findall(m.group(1)):
        if tok not in seen:
            seen.add(tok)
            out.append(tok)
    return out


def versions_in_history(n=400):
    """Every version stamped by a commit subject, newest first. -> ([version], why)

    ⚠⚠ v2854 — `--backlog` READ THE LEDGER, AND A VERSION WITH NO ROW HAS NOTHING TO READ.
    audit()'s own docstring says its scope out loud: "Every version mentioned in the ledger". A
    version that shipped and was never looked at produces NO row, so the one command whose job is
    "what is stacking up" could not see the single case that matters most — the newest unlooked
    version, which is exactly the one that blocks the next push.

    MEASURED 2026-09-09: `--backlog` reported "3 version(s) owe a look: v2772, v2774, v2776" and did
    not name v2852. I trusted it, pushed v2853, and the gate refused with "v2852 OWES A LOOK —
    nothing was ever recorded for it". Two checks disagreed and the quiet one was wrong.
    [[silence-is-not-evidence]] [[zero-needs-a-denominator]]
    """
    out, why = _sh(["git", "log", "--format=%s", "-%d" % int(n)])
    if out is None:
        return [], why
    seen, vs = set(), []
    for line in out.splitlines():
        # v3316 — ONE parser for "what does this subject ship", so the backlog and any future
        # range-aware gate cannot disagree about it. [[copy-drift]]
        for tok in versions_in_run(line):
            if tok not in seen:
                seen.add(tok)
                vs.append(tok)
    return vs, ""


def _bound_commit(version):
    """The commit TASKS.md says this version shipped as. -> sha | None

    ⚠⚠ v3266 — `bump_version.py` ALREADY WRITES THIS AND NOBODY ASKED IT. Every bump prints
    "bound N version row(s) to a commit" and leaves a row in TASKS.md:

        | **v3265** | `25a6ad2b` | v3265 — HEART: lane_health gains a third state ...

    `commit_for` re-derived the same fact by string-matching COMMIT SUBJECTS, so a version whose
    subject did not happen to contain its own stamp was invisible to its own runner. MEASURED
    2026-09-17: v3265 shipped as *"fix: BLOCKED is not STOPPED — the chronicle lane was never
    stopped"*, which names the defect and not the version, and `second_eye_run v3265` answered
    "no commit subject names v3265 in the last 400". The look could not be taken, so the NEXT
    push would have been refused at the gate for a version that was sitting right there, bound,
    in a file written by the tool that stamped it. Two halves of one fact, never joined.
    [[the-unjoined-end]] [[copy-drift]]
    """
    path = os.path.join(REPO, "TASKS.md")
    try:
        with io.open(path, encoding="utf-8") as fh:
            body = fh.read()
    except Exception:
        return None
    m = re.search(r"\|\s*\*\*%s\*\*\s*\|\s*`([0-9a-f]{7,40})`" % re.escape(version), body)
    return m.group(1) if m else None


def commit_for(version):
    """The commit that shipped this version. -> (sha | None, why)

    Asks the BINDING first (see _bound_commit), then falls back to scanning subjects — a repo
    without a TASKS.md row still works exactly as it did.
    """
    bound = _bound_commit(version)
    if bound:
        # ⚠ trust it only if the object actually exists; a stale or hand-edited row must not
        # send the runner at a sha that is not there. [[unknown-stays-unknown]]
        _ok, _ = _sh(["git", "cat-file", "-e", "%s^{commit}" % bound])
        if _ok is not None:
            return bound, ""
    out, why = _sh(["git", "log", "--format=%H %s", "-400"])
    if out is None:
        return None, why
    rx = re.compile(r"\b%s\b" % re.escape(version))
    for line in out.splitlines():
        sha, _, subject = line.partition(" ")
        if rx.search(subject):
            return sha, ""
    return None, ("no TASKS.md row binds %s to a commit, and no commit subject names it in the "
                  "last 400" % version)


_PY_COMMENT = re.compile(r"^\s*#")
_JS_COMMENT = re.compile(r"^\s*(/\*|\*|//)")


def _strip_comments(diff):
    """Drop comment-only ADDED lines. The code still reads; the author's account of it does not.

    ⚠⚠ v3203 — IT DROPPED THE OPENER AND KEPT THE BODY, AND THAT MANUFACTURED A P1.
    MEASURED 2026-09-16 on the v3201 look. Grok returned a fatal finding: *"the edit inserts a
    block of explanatory prose directly into the JavaScript source without an opening `/*` ...
    the resulting string is not syntactically valid JS."* It was reading the payload correctly.
    The FILE is fine — `js_syntax_gate.py` parses it in a real JS engine — and the real diff
    carried 4 added lines with the warning glyph while the payload carried 1.

    THE MECHANISM: the old loop matched each added line against `_JS_COMMENT` INDEPENDENTLY. This
    codebase writes block comments as

        /* ⚠⚠ TITLE — first line
           continuation prose with NO leading asterisk
           ... */

    so the opener matched and was dropped, and every continuation line did not match and was
    KEPT. The eye was then handed orphaned prose sitting in the middle of executable code — a
    syntax error the transport invented. That is not a one-off: it is EVERY multi-line block
    comment in this repo, on EVERY look this instrument has ever done, including the ones it
    called clean. An instrument that corrupts its own input has no verdict worth the name.
    [[feedback-suspect-the-instrument]] [[unknown-stays-unknown]]

    ⚠ THE STATE RESETS AT EVERY HUNK AND FILE BOUNDARY. A diff shows hunks, so a block comment
    can be opened inside one and closed in a part that is not shown; without a reset an unclosed
    opener would swallow the whole remainder of the payload — trading manufactured findings for
    silently missing code, which is the worse direction.
    """
    keep = []
    in_block = False
    for ln in diff.splitlines():
        # continuity is only claimable inside one hunk of one file
        if ln.startswith("diff --git") or ln.startswith("@@") or ln.startswith("+++") \
                or ln.startswith("---"):
            in_block = False
            keep.append(ln)
            continue
        if ln.startswith("+"):
            body = ln[1:]
            if in_block:
                if "*/" in body:
                    in_block = False
                    tail = body.split("*/", 1)[1]
                    if tail.strip():          # real code sharing the closing line survives
                        keep.append("+" + tail)
                continue
            if _PY_COMMENT.match(body) or _JS_COMMENT.match(body) or not body.strip():
                if _opens_block(body):
                    in_block = True
                continue
            if _opens_block(body):            # code, then a block comment that runs on
                head = body.split("/*", 1)[0]
                in_block = True
                if head.strip():
                    keep.append("+" + head)
                continue
        keep.append(ln)
    return "\n".join(keep)


def _opens_block(body):
    """Does this line open a /* block that does NOT close on the same line?"""
    i = body.find("/*")
    return i >= 0 and "*/" not in body[i + 2:]


def uncovered_commits(sha):
    """-> list of "sha subject" lines that ship WITH `sha` but are NOT in its payload, or None.

    ⚠⚠ v3299 — THE LOOK COVERS ONE COMMIT AND THE PUSH CARRIES MANY. `payload_for` runs
    `git show <sha>` on the single commit that carries the version stamp, so every `fix:` commit
    landing after the bump and before the push is NEVER SEEN BY ANY EYE — while the row that lands
    reads as though the push was reviewed.

    MEASURED 2026-09-18 on v3298: FOUR commits shipped in one push and the eye saw ONE. The unseen
    three included the membership discriminator, which took THREE cuts (two of them wrong) and was
    the most consequential change in the push. The verdict then attacked `_fnew > _dm + 0.5` — code
    SUPERSEDED two commits later. That is not the eye being wrong; it is the gate handing it bytes
    that no longer ship.

    ⚠ None means "the range could not be listed", which is UNKNOWN and must never be rendered as
    "nothing was missed". An empty list means MEASURED-AND-NONE. Those are different facts and the
    caller must not collapse them. [[zero-needs-a-denominator]] [[source-reading-guard]]
    """
    out, _why = _sh(["git", "log", "--oneline", "%s..HEAD" % sha], timeout=30)
    if out is None:
        return None
    return [l.strip() for l in out.splitlines() if l.strip()]


def absent_from(sha, body):
    """-> (absent, why). Which of `sha`'s changed code files are NOT present in `body`.

    THREE STATES, and collapsing any two is the defect this exists to prevent:
        a LIST  -> these changed files never reached the eye at all
        []      -> MEASURED AND NONE: every changed code file is in the payload
        None    -> the roster could not be read; UNKNOWN, never "nothing was missed"

    ⚠ THE ROSTER COMES FROM GIT, NEVER FROM WHAT WAS FETCHED. When the python diff alone already
    exceeds the cap, payload_for never runs the *.html show — so a dropped .html is not missing
    from any buffer to compare against, it is missing from the QUESTION. Deriving this from the
    fetched text would report 0 for exactly the v3333 case that prompted it.
    [[unknown-stays-unknown]] [[the-unjoined-end]]
    """
    names, why = _sh(["git", "show", "--format=", "--name-only", sha,
                      "--", "*.py", "*.mjs", "*.sh", "*.html"], timeout=90)
    if names is None:
        return None, (why or "the changed-file roster could not be read")
    sent = set(re.findall(r"(?m)^diff --git a/(\S+)", body or ""))
    return [f for f in (l.strip() for l in names.splitlines()) if f and f not in sent], ""


#: a `why=` in run_gates.py is a SHIP NOTE — prose wearing code's clothes. `_strip_comments`
#: cannot touch it because it is a string LITERAL, so the eye pays full price for it out of a
#: budget that truncates. MEASURED over the last 24 versions: run_gates.py took 31.5% of v3354's
#: whole payload and the file that version exists to change reached 0% of it.
#: ⚠⚠ NO PARENTHESES IN THIS PATTERN, AND THE LAW CAUGHT WHY ON ITS FIRST RUN. The first cut
#: allowed an optional `(` before the chunks and an optional `)` after them, and on
#: `why="a one line note"),` it ATE THE CLOSING PAREN — handing the eye a diff whose `Gate(...)`
#: call no longer closes. Mangling registration structure is the `gate_insert_missing_comma`
#: family, and the file-header count I measured with could not see it: a broken diff still has
#: its `diff --git` lines. The pattern now touches the `why=` and its string chunks and nothing
#: else; a parenthesised note is simply left alone, which costs reach and cannot cost correctness.
_WHY_NOTE_RX = re.compile(
    r'why=\s*(?:"(?:[^"\\]|\\.)*"\s*|\'(?:[^\'\\]|\\.)*\'\s*)+', re.S)


def _strip_ship_notes(diff):
    """Replace every `why=` ship note in a diff with a stub, KEEPING THE LINE COUNT.

    ⚠⚠ THE NEWLINES ARE THE WHOLE TRICK, AND MY FIRST CUT LOST THEM. Collapsing a multi-line
    `why=` onto one line pulls the NEXT `diff --git` off the start of its own line, and every
    line-anchored reader — including the one measuring whether this change helps — stops seeing
    that file. That instrument reported the strip making THREE versions blinder; with the line
    count preserved the same measurement says 65 missed files -> 58 over 24 versions, 6 better
    and ZERO worse. The regression was mine, in the measuring tool, not in the idea.
    [[feedback-suspect-the-instrument]] [[source-reading-guard]]

    ⚠ ONLY THE NOTE. The `Gate(...)` registrations around it are real code — a missing separating
    comma there is a live defect class in this repo — so nothing else in run_gates.py is touched.

    ⚠⚠ AND IT REMOVES LESS THAN IT LOOKS LIKE, STATED SO THE NUMBER IS NOT OVER-READ. In a DIFF
    every continuation line begins with `+`, `-` or a space, and the pattern's `\s*` cannot cross
    that marker — so a note spanning five lines loses its FIRST quoted chunk and keeps the rest.
    That is deliberate: widening the pattern to eat `^[+- ]\s*"..."` would start eating ordinary
    string literals in ordinary code, and the 65 -> 58 measurement above is of THIS narrow form,
    not of a fuller one. A wider strip needs its own measurement before it is worth anything.

    ⚠⚠⚠ SCOPED TO run_gates.py, AND THE CROSS-FAMILY EYE FOUND WHY ON v3360 — a real defect I
    shipped. `why=` is a ship note ONLY in run_gates.py. MEASURED across tv/*.py: 188 occurrences
    sit outside any `Gate(` call, and many are live message strings — `why="boot"`,
    `why="a session ended"`, `why="disk too full"`, `why="the second-family CLI is not installed
    here"`. Stripping those replaces the very bytes a version about wording exists to change, and
    hands the eye a stub in place of the subject. That is the defect this whole area exists to
    prevent, re-created by the fix for it. So the strip walks the diff FILE BY FILE and only
    touches the run_gates.py hunks. [[the-unjoined-end]] [[sweep-dont-ask]]

    ⚠ The eye's other two findings on the same diff were REFUTED by measurement and are recorded
    so nobody re-derives them: it said the replacement drops newlines (the shipped `_repl` appends
    `"\n" * m.group(0).count("\n")`, verified 4 -> 4) and that the strip is a no-op after
    `_strip_comments` (measured on v3360's own payload: 18,647 -> 11,433 chars, 7,214 removed).
    It was judging a TRUNCATED payload that cut the replacement line.
    """
    def _repl(m):
        return 'why="<ship note stripped for the eye>"' + "\n" * m.group(0).count("\n")
    d = diff or ""
    out, i = [], 0
    for path, a, b in _file_sections(d):
        out.append(d[i:a])
        hunk = d[a:b]
        out.append(_WHY_NOTE_RX.sub(_repl, hunk) if path.endswith("run_gates.py") else hunk)
        i = b
    out.append(d[i:])
    return "".join(out)


def _file_sections(diff):
    """-> [(path, start, end)] over a diff's OWN `diff --git a/<path>` headers.

    v3363 - ONE WALK, TWO READERS. `_strip_ship_notes` already walked the diff file by file, and
    `reach_of` below needs the identical boundaries. Two copies of a boundary rule disagree the
    day one is edited, and this particular rule is subtle enough to have been got wrong once
    already: the end of a file's section is the NEXT header's line start, not the match start,
    and a section that runs to EOF has no next header at all. [[copy-drift]]
    """
    d = diff or ""
    outs = []
    for m in re.finditer(r"(?m)^diff --git a/(\S+)", d):
        j = d.find("\ndiff --git a/", m.start())
        outs.append((m.group(1), m.start(), len(d) if j < 0 else j + 1))
    return outs


def reach_of(full_body, final_body):
    """-> {path: {"got": int, "total": int}} | None. How much of each ARRIVED file the eye got.

    ⚠⚠ THIS IS A DIFFERENT QUESTION FROM `absent_from`, AND THAT GAP IS THE WHOLE DEFECT.
    `absent` answers "did this file reach the payload at all", measured by the presence of its
    `diff --git` header. Truncation cuts MID-FILE, so a file whose header arrived and whose body
    was chopped is `absent`-clean and unread. Every reach check built before this says it was
    seen.

    MEASURED 2026-09-19 WITH THIS FUNCTION over 16 versions. 67 files ARRIVED; 8 of them arrived
    under half their bytes:
        v3356  bible.html                                        259 /  8,629    3.0%
        v3349  test_a_partial_look_is_not_agreement.py           428 / 11,337    3.8%
        v3350  test_the_shelf_tabs_are_the_real_sessions.py      196 /  3,406    5.8%
        v3358  test_the_shelf_shows_reels_before_analysis.py   1,224 / 12,586    9.7%
        v3348  visual_lock_invariant.py                           64 /    516   12.4%
        v3352  test_the_shelf_tabs_are_the_real_sessions.py    1,464 /  5,915   24.8%
        v3347  prune_wilson.py                                 8,318 / 27,748   30.0%
        v3354  second_eye_ledger.py                            3,499 /  7,200   48.6%

    ⚠⚠ v3354 IS THE ROW THAT SETTLES IT. `second_eye_ledger.py` is the file that version exists
    to change; its header arrived, so the row was filed `blind_to: []` and `verdict: clean` while
    the eye held under half of its subject. v3361 did the same: the answer's OWN first line read
    "REACH: 19/92 hunks" and the row said clean.

    ⚠ THE FRACTION IS STORED, NEVER A BOOLEAN AGAINST A BAKED CONSTANT. A hardcoded 0.5 here
    would be a bar nobody measured and nobody can move - the shape of the $5 he corrected me on
    and of the 0.22 threshold that sat above a signal maxing at 0.133. Store got/total; let the
    reader decide and let the bar be tuned once there are rows to tune it against.
    [[feedback-threshold-above-the-ceiling]]

    THREE STATES, and collapsing any two is the defect this exists to prevent:
        a DICT  -> measured; compare got against total per file
        None    -> the full body could not be established; UNKNOWN, never "all complete"
    A file present in `final` but not in `full` cannot happen (final is a prefix of full) and is
    recorded at its own length rather than silently dropped, so an instrument fault shows up as
    got > total instead of disappearing.
    """
    if full_body is None or final_body is None:
        return None
    full = {}
    for path, a, b in _file_sections(full_body):
        full[path] = full.get(path, 0) + (b - a)
    if not full:
        return None
    got = {}
    for path, a, b in _file_sections(final_body):
        got[path] = got.get(path, 0) + (b - a)
    # ⚠⚠ A FILE WITH ZERO BYTES HERE DID NOT *ARRIVE SHORT* — IT DID NOT ARRIVE, and
    # `absent_from` already names it. Including those made this counter 71% NOISE the first time
    # it was pointed at real data: 41 of 100 files flagged over 16 versions, 33 of them at exactly
    # 0.0%, every one already in the row's `absent` list. That is v3354's defect - a warning that
    # fires on most rows is furniture - re-created two versions after I fixed it, and only a
    # measurement against his real history caught it. The fixture could not: a fixture built to
    # show a half-cut file has no wholly-cut file in it. [[regression-guard]] §5
    # So `reach` answers exactly one question: OF THE FILES THAT ARRIVED, how much arrived.
    # {} is therefore MEASURED-AND-NONE-ARRIVED (and `absent` carries them), which is still a
    # different state from None = nobody could measure.
    return dict((p, {"got": int(got[p]), "total": int(n)})
                for p, n in full.items() if int(got.get(p, 0)) > 0)



# ── v3370 (#116) — THE BUDGET IS SHARED, NOT SPENT ALPHABETICALLY ───────────────────────────
# MEASURED on v3368: the admitted set was EXACTLY sorted(changed files)[:5]. Nothing weighed
# relevance, size or risk — git's default sort decided who got reviewed, so the files late in the
# alphabet were never reviewed at all. TWENTY-THREE engine files sort behind all 460 tv/test_*.py,
# and they are the whole vault lane plus tree_busy, tv_diablo, unknown_age, verdict_provenance,
# window_visibility, write_census, write_witness.
#
# The feedback loop made it worse: the standing order is JOIN -> GATE -> HEART -> BANK, so nearly
# every version adds a large new tv/test_*.py, which alphabetically lands AHEAD of the engine it
# protects and pushes it past the cap. The law crowded out its own subject. v3368 lost
# vault_retro.py and tv_diablo.py — its entire fix — and the eye said so itself: "the only consumer
# of the three new fields is the new doctor check; its producer lives in the missing files."
#
# MEASURED over 30 real versions / 182 changed code files:
#     alphabetical prefix (before)    68/182  37.4%   median cov   -    slivers <15%:  0
#     engine-first ordering           74/182  40.7%                     <- refuted, barely moves
#     fair share, no floor           182/182 100.0%   median cov  66%   slivers <15%: 26
#     fair share, floor 1500         151/182  83.0%   median cov 100%   slivers <15%:  1
#
# ⚠⚠ THE NO-FLOOR VARIANT IS A TRAP, AND THIS FILE ALREADY RECORDS WHY. v2803: the payload ended
# at `+    return ` and the eye returned TWO high-severity defects about a function whose last two
# characters the cap had removed. v2850: `drift` reported as never declared, when the declaration
# sat above the first changed line. A SLIVER OF A FILE DOES NOT MERELY FAIL TO HELP — IT
# MANUFACTURES FINDINGS, and each false one has to be chased and refuted by hand. So a file gets a
# USEFUL slice or none at all, and the ones that get none are named by the v3341 mechanism.
MIN_USEFUL_SLICE = 1500


def _share_the_budget(body, cap):
    """-> (body, cut_note, absent_extra). Every file gets a useful slice of the cap, or none.

    Max-min fair: the smallest diffs complete cheaply and donate what they do not need. When the
    remaining pool cannot give everyone a USEFUL slice, the largest file is dropped rather than
    everyone being shaved into slivers — a partial file the eye can reason about beats several it
    cannot.
    """
    secs = _file_sections(body)
    if len(secs) < 2:
        cut = body.rfind("\n", 0, cap)
        return body[:cut if cut > 0 else cap], None, []
    sized = [(p, a, b, b - a) for p, a, b in secs]
    # ⚠ THE PREAMBLE COMES OUT OF THE POOL. Anything before the first `diff --git` is emitted
    # below, so leaving it out of the accounting lets the ONE promise this function makes — the
    # cap — be exceeded by however many leading bytes happen to be there. Measured by a
    # cross-family review of v3370: cap 5000, a 361-char preamble, 5319 chars returned.
    lead = sized[0][1]
    take, pool, cand = {}, max(0, cap - lead), sorted(sized, key=lambda x: x[3])
    while cand:
        share = pool // len(cand)
        if share < MIN_USEFUL_SLICE:
            cand.pop()                      # cannot serve everyone usefully; drop the largest
            continue
        p, a, b, n = cand[0]
        if n <= share:
            take[p] = n; pool -= n; cand.pop(0); continue
        for p, a, b, n in cand:
            take[p] = share
        break
    out, cuts, absent = [], [], []
    if sized[0][1] > 0:
        out.append(body[:sized[0][1]])      # anything before the first header is kept
    for p, a, b, n in sized:                # ORIGINAL order on the wire, not the allocation order
        want = int(take.get(p, 0))
        if want <= 0:
            absent.append(p); continue
        seg = body[a:b]
        if want < n:
            # ⚠ LINE BOUNDARY, same as the single cut it replaces — a mid-statement cut is what
            # manufactured the v2803 findings.
            #
            # ⚠⚠ AND THE SLICE MUST KEEP ITS TRAILING NEWLINE. Cutting BEFORE it leaves the next
            # file header appended to a half-line, so `diff --git` is no longer at line start: the
            # two files merge on the wire and the second becomes INVISIBLE to the eye and to every
            # parser downstream, including the absent-file accounting. Caught by re-parsing this
            # function own output and finding vault_retro.py missing while the note claimed 45%.
            # ⚠ `>= 0`, NOT `> 0`, AND NO UNTERMINATED FALLBACK. When there is no newline in the
            # first `want` bytes, seg[:want] does not end on a line boundary, so the NEXT file's
            # `diff --git` header lands mid-line and stops being a header: the two files merge and
            # the second disappears from the payload AND from `absent`, which is the exact defect
            # this function exists to remove. Reproduced on a section whose header is followed by
            # one unbroken 40,000-char line — tv/two.py vanished entirely and was never named.
            # An empty slice falls through to the floor below, which drops and NAMES it.
            c = seg.rfind("\n", 0, want)
            seg = seg[:c + 1] if c >= 0 else ""
            # ⚠ A LINE-BOUNDARY CUT CAN COLLAPSE. WINDOWS_SHIP.json is one long line, so the cut
            # landed at 6% of it — a sliver, which is what the floor exists to prevent. Judge the
            # slice AFTER the cut, not by the share that was allocated, and drop it if it is not
            # useful. An absent file is named; a sliver manufactures findings.
            if len(seg) < MIN_USEFUL_SLICE:
                absent.append(p); continue
            cuts.append("%s %d%%" % (p, int(round(100.0 * len(seg) / float(n)))))
        out.append(seg)
    note = None
    if cuts:
        note = "shown in part: %s" % ", ".join(cuts)
    return "".join(out), note, absent


def payload_for(sha):
    """-> (prompt, dropped_note). Code only, comments stripped, truncation declared."""
    # ⚠ PYTHON FIRST, and the reason is measurable: control_ui.html diffs in this repo run to tens
    # of thousands of characters that are largely prose, so a single combined diff spends the whole
    # budget on comments the stripper cannot remove (they sit inside string literals and JS block
    # comments spanning lines) and the eye never reaches the logic. Ask for the code first.
    out, why = _sh(["git", "show", "--format=", "--unified=3", sha,
                    "--", "*.py", "*.mjs", "*.sh"], timeout=90)
    if out is None:
        return None, why
    # ⚠⚠ v3360 — THE SHIP NOTES GO BEFORE THE CAP DOES. run_gates.py carries one `why=` per gate
    # and each is a paragraph of prose the eye never needs to review; `_strip_comments` cannot
    # reach them because they are string LITERALS. MEASURED on v3354: corroborate.py 59.3%,
    # run_gates.py 31.5%, control_app.py 9.2% — and tv/second_eye_ledger.py, the file that version
    # exists to change, got 0%. Over the last 24 versions this recovers 7 changed files that never
    # reached the eye (65 missed -> 58), 6 versions better and none worse.
    # ⚠ It does NOT widen the cap. v3299 ruled that cost is HIS; this only stops spending the
    # budget on prose. [[the-unjoined-end]]
    body = _strip_ship_notes(_strip_comments(out))
    _full_len_holder = [body]
    if len(body) < _cap():
        _more, _ = _sh(["git", "show", "--format=", "--unified=3", sha, "--", "*.html"],
                       timeout=90)
        if _more:
            body = body + "\n" + _strip_ship_notes(_strip_comments(_more))
    _full_len_holder = [body]
    dropped = ""
    if len(body) > _cap():
        # ⚠⚠ CUT ON A LINE BOUNDARY, AND SAY SO IN THE PROMPT — because a mid-statement cut
        # MANUFACTURES FINDINGS. Measured on v2803: the payload ended at exactly `+    return `
        # and the eye returned TWO high-severity defects — "gate_files() returns None on every
        # execution", "the documented contract is violated" — reasoning correctly about a
        # function whose last two characters my own cap had removed. The real line is
        # `return out` and it returns 247 gates.
        #
        # The record already declared the truncation, which is the only reason it was caught. But
        # a declaration in the LEDGER does not help the EYE: it was never told, so it treated an
        # artefact of the transport as a defect in the code. An instrument that fabricates
        # findings costs more than one that finds nothing, because each false one has to be
        # chased down and refuted by hand. [[feedback-suspect-the-instrument]]
        body, _cut_note, _cut_absent = _share_the_budget(body, _cap())
        dropped = ("shared %d of %d diff chars across the changed files, each cut at a line "
                   "boundary" % (len(body), len(_full_len_holder[0])))
        if _cut_note:
            dropped += " — " + _cut_note
    # ⚠⚠ v2851 — THE SCOPE WARNING BELONGS ON EVERY DIFF, NOT ONLY A TRUNCATED ONE.
    # It used to live entirely inside `if dropped:`. But a diff is ALWAYS partial — it shows
    # HUNKS, never whole functions — so a complete, untruncated diff invites the same false
    # finding, and got one. MEASURED on the v2850 look: the reviewer reported at HIGH severity
    # that `drift` was "referenced but never declared" in a function it had seen three hunks of.
    # `var drift = ...` is declared once and referenced four times, above the first changed line
    # — unchanged context, therefore absent from the diff BY CONSTRUCTION. The reviewer
    # reasoned correctly from what it was shown; the PAYLOAD misled it. A false finding at high
    # severity costs more than a missed one, because it has to be chased and refuted by hand.
    # [[feedback-suspect-the-instrument]] [[unknown-stays-unknown]]
    # v3341 - A CHAR COUNT CANNOT NAME WHAT IS MISSING, AND 22 OF 36 VERSIONS LOST A CODE FILE.
    # The declaration above says "truncated to 8142 of N diff chars", which is true and unusable:
    # the eye cannot tell from it that control_ui.html is wholly absent, so it answers "the diff is
    # correct as shown" in perfect good faith about a payload containing none of the fix. MEASURED
    # across v3300-v3340 by rebuilding this function per commit: 22 of 36 versions with code changes
    # had at least one changed code file never reach the eye. v3330 lost tree_busy.py and v3315 lost
    # second_eye_run.py - in both cases the file the version exists to change.
    #
    # THE WANTED SET COMES FROM GIT, NEVER FROM WHAT WAS FETCHED. When the python diff alone already
    # exceeds the cap, the *.html show above is never run at all - so a dropped .html is not missing
    # from any buffer here, it is missing from the QUESTION. Only git can see it. Deriving the list
    # from `body` would silently report 0 for exactly the v3333 case that prompted this.
    # [[unknown-stays-unknown]] [[the-unjoined-end]]
    absent, _nwhy = absent_from(sha, body)
    # v3363 - AND HOW MUCH OF EACH FILE THAT DID ARRIVE. Measured against the pre-truncation body,
    # so it isolates what the TRANSPORT lost; the comment strip and the ship-note strip are
    # deliberate and already declared, and charging them here would read as loss.
    reach = reach_of(_full_len_holder[0], body)

    note = ("\nNOTE: this is a DIFF, not whole files. A name used in one hunk may be DECLARED "
            "or ASSIGNED in a part of the same function the diff does not show, because "
            "unchanged context is omitted by construction. Do not report a variable as "
            "unbound, undefined, undeclared or unpacked-from-nowhere unless you can see its "
            "whole scope here. Judge only what is fully shown, and say so when a judgement "
            "would need code that is not in front of you.\n")
    if dropped:
        note += ("\nAND IT IS ALSO TRUNCATED — it stops part-way through, mid-file at a line "
                 "boundary. Do not report a function, statement or block as incomplete, "
                 "unterminated or missing a return merely because the excerpt stops before it "
                 "does.\n")
    if absent is None:
        note += ("\nThe roster of changed files could not be read (%s), so WHICH of this commit's "
                 "files reached you is UNKNOWN. Do not treat this payload as complete.\n"
                 % (_nwhy or "no reason given"))
    elif absent:
        note += ("\nAND THESE CHANGED FILES ARE NOT IN THIS PAYLOAD AT ALL - not truncated, absent. "
                 "Treat them as UNKNOWN rather than as unchanged, say so if a judgement would need "
                 "them, and do not call the change correct on their behalf: %s\n"
                 % ", ".join(absent))
    # The ROW must carry it too, or a later reader sees a clean verdict with no way to know its
    # reach without rebuilding the payload by hand - which is how this went unnoticed for 22 ships.
    if absent:
        dropped = ((dropped + " - ") if dropped else "") + (
            "%d changed file(s) never reached the eye: %s" % (len(absent), ", ".join(absent)))
    elif absent is None:
        dropped = ((dropped + " - ") if dropped else "") + (
            "which changed files reached the eye is UNKNOWN (%s)" % (_nwhy or "unreadable"))
    # ⚠⚠ v3349 — THE LIST TRAVELS, NOT ONLY THE SENTENCE. `dropped` is PROSE, and the row was
    # carrying it as a 400-char-capped suffix on `asked`, so the one-to-many fact "these files
    # never reached the eye" arrived at the ledger flattened into another field and truncated.
    # The comment above this line already says "the ROW must carry it too"; the intent was right
    # and the STORE was wrong. [[one-to-one-store-for-a-one-to-many-fact]]
    # `absent` keeps its THREE states all the way to the row: a LIST (measured, these are missing),
    # [] (measured, nothing missing) and None (nobody could ask). [[unknown-stays-unknown]]
    return COLD_FRAMING + note + "\n```diff\n" + body + "\n```\n", dropped, absent, reach


def _model_from_transport():
    """Which family answered, read from WHICH BINARY WAS EXECUTED. -> model id or ""

    ⚠⚠ v3229 — WITHOUT THIS THE LANE WAS REACHABLE AND STILL USELESS TO THE GATE. Measured
    2026-09-16: v3224 and v3225 both got genuine cross-family reviews through the CLI door — 6 and
    12 real findings — and BOTH landed as `model='' family=None`, because this Grok CLI prints no
    model header and `_model_from_answer` had nothing to read. `family_of(None)` is None by
    design, an unattributable look cannot discharge a cross-family debt, and so the push gate went
    on reporting **"v3224 OWES A LOOK — nothing was ever recorded for it"** about a look that had
    just happened. Two eyes ran for 15 minutes each and bought nothing.

    ⚠ AND IT MUST NOT BECOME THE BUG IT IS FIXING. v3214-v3216 recorded `model=EYE_MODEL` — the
    CONFIGURED default — no matter who answered, so three OpenAI looks were filed `family=xai`.
    The lesson there was *read it from the evidence, not the config*. **This is evidence**: it is
    not what we hoped to run, it is which executable the subprocess actually launched, and a
    same-family agent cannot produce a row through a path it never took. That is why it derives
    from `EYE_CLI` alone and never from `EYE_MODEL`.

    It stays a FALLBACK: `record_answer` prefers the model the answer names, always. And every row
    it attributes carries `modelSource="transport"`, so the ledger says which kind of evidence it
    had. [[derived-correctly-from-a-guess]] [[unknown-stays-unknown]]
    """
    low = (EYE_CLI or "").lower()
    if "grok" in low:
        return "grok-cli"          # family_of() -> xai
    if "codex" in low or "chatgpt" in low:
        return "codex-cli"         # family_of() -> openai
    return ""                      # UNKNOWN transport -> stays unattributable, fails closed


def ask(prompt):
    """-> (answer, reached, why). An unreachable eye returns reached=False and NO verdict."""
    if not os.path.exists(EYE_CLI):
        return "", False, "no eye at %s (set THIRD_EYE_CLI)" % EYE_CLI
    try:
        p = subprocess.Popen([EYE_CLI, "-p", prompt],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(timeout=EYE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        p.kill()
        return "", False, "the eye did not answer within %ss" % EYE_TIMEOUT_S
    except Exception as e:
        return "", False, "the eye could not be run: %s" % type(e).__name__
    ans = (out or b"").decode("utf-8", "replace").strip()
    if p.returncode != 0:
        return ans, False, ("the eye exited %d: %s"
                            % (p.returncode, (err or b"").decode("utf-8", "replace")[:200]))
    # ⚠ EXIT 0 IS NOT AN ANSWER. This CLI has been measured exiting 0 on "Not signed in"; an empty
    # or near-empty body is an empty seat however clean the status code looked.
    if len(ans) < 40:
        return ans, False, "the eye answered %d chars — too little to be a look" % len(ans)
    return ans, True, ""


# ⚠⚠ v3198 — THE ADJECTIVE WAS THE WHOLE BUG, AND IT MADE THE LEDGER LIE IN THE DIRECTION
# THE LEDGER EXISTS TO PREVENT. Measured 2026-09-16 on a real cross-family look at v3189: Grok
# opened with **"No concrete defects found in the diff."** and the row was filed
# `verdict=findings, findings=4`. The four "findings" were its own summary of what the diff
# CHANGED — the first of them literally reading "No concrete defects found."
#
# The pattern demanded `no <noun> found` with nothing between, so one adjective — concrete,
# obvious, real, apparent, actual — defeated it. This is `label-outlived-referent` inside the
# instrument itself: the ledger whose entire job is to record what another family concluded
# recorded the opposite of what it concluded, and the ship gate reads this ledger.
#
# ⚠ TWO ADJECTIVES, NOT UNBOUNDED. `\w+\s+` repeated without a ceiling would let
# "no ... found" span a whole sentence and match "there is no way to tell whether the bugs the
# reviewer found are real" — the exact inversion. Bounded at 2 it covers every real phrasing
# measured and cannot swallow a clause. [[unknown-stays-unknown]] [[source-reading-guard]]
# A provider-level refusal — rate limit, auth, a model the account may not use. These arrive as
# ordinary stdout and can be any length, so a size test will not catch them. They are NOT a review
# and must never be recorded as one: the seat was never occupied. [[unknown-stays-unknown]]
# ⚠⚠ v3223 — ANCHORED, AND THE VOCABULARY IS OPENERS NOT TOPICS. The v3220 version searched for
# "quota", "unauthor", "authentication", "rate-limit" ANYWHERE in the first 400 characters, so a
# genuine review saying "authentication is not checked" or "quota is never decremented" was filed
# as a provider refusal and DISCARDED. A cross-family look named it, and pointed out that a review
# of that very diff would trip it. Over-refusing is the worse direction of the two: a false LOOKED
# is visible in the ledger, a discarded real look is not.
# These are how a PROVIDER opens when it produced nothing else. A reviewer does not begin a review
# with "You have hit your usage limit". [[unknown-stays-unknown]] [[source-reading-guard]]
_PROVIDER_ERROR_RX = re.compile(
    r"(?is)\s*(?:"
    r"ERROR\b|error:|\{\s*\"type\"\s*:\s*\"error\"|"
    r"you(?:'ve| have) hit your usage limit|"
    r"(?:you are|you're) being rate[- ]limited|"
    r"rate[- ]limit(?:ed|-exceeded)?\b|"
    r"quota exceeded|"
    r"please (?:sign|log) in\b|"
    r"authentication (?:failed|required)\b|"
    r"unauthorized\b|"
    r"the '[^']+' model is not supported"
    r")")


_NO_DEFECT_RX = re.compile(
    # ⚠⚠ v3268 — THE TRAILING `\s+` HERE IS WHY THE BARE FORM COULD NEVER MATCH, and it is also
    # why v3268's first cut LOOKED like it worked. "No concrete defects." puts a `.` straight
    # after the noun, so a REQUIRED space fails before the tail is ever tried. The optional-tail
    # branch added below was therefore unreachable for exactly the input it was written for — and
    # the test passed anyway, because `_findings_from` returns NO blocks for a one-line answer and
    # `_verdict_for` reads "a declaration with nothing listed" as clean. A green arrived by a
    # route that had nothing to do with the fix. [[matches-once-can-still-prove-nothing]]
    # The separator moves INTO the verb branch, where it belongs: a verb needs a space before it,
    # a full stop does not.
    r"\bno\s+(?:\w+\s+){0,2}(?:defects?|issues?|bugs?|problems?)\b"
    # ⚠ v3216 — `evident` AND `present` ADDED, and `is` to the copula list. An OpenAI seat wrote
    # "No concrete functional defect is evident in this diff", every block scored
    # claims_a_defect=False, and the row STILL said verdict=findings — because the declaration
    # used a verb this list did not carry. Widening here is safe by construction: the pattern only
    # ever GRANTS clean, and only when `claims` is simultaneously empty, so a miss costs a noisy
    # row and a false match still cannot clear a real finding. [[unknown-stays-unknown]]
    # ⚠⚠ v3267 — A THIRD VERB, AND IT IS THE SAME DEFECT A THIRD TIME. Grok answered v3266 with
    # "The diff is correct as shown (no concrete defects meeting the criteria)." — a flat clean —
    # and the row was filed verdict=findings, because the word after `defects` was `meeting`,
    # which this list did not carry. v3216 added `evident`/`present` for the same reason. The
    # instrument keeps failing on the one axis nobody can enumerate in advance: how a different
    # model phrases "nothing is wrong".
    # ⚠ Widening stays safe by construction, and that is WHY it is the right fix rather than a
    # looser pattern: this regex only ever GRANTS clean, only when no block makes a defect claim
    # (`_DEFECT_MARK_RX`), so a false match cannot clear a real finding — it can only spare a
    # clean look from the stricter bucket. [[feedback-blind-fixture-green-gate]]
    # ⚠⚠⚠ v3268 — AND THE VERB CAN BE ABSENT ENTIRELY. Widening the participle list in v3267 was
    # still chasing vocabulary. Taking the very next look, Grok opened with "**No concrete
    # defects.**" — full stop, no verb at all — and the row was filed verdict=findings AGAIN. That
    # is four phrasings in three versions (v3216 `evident`, v3216 `present`, v3267 `meeting`, this).
    # The lesson is that enumerating how a model says "nothing is wrong" does not converge: the
    # declaration is the NOUN PHRASE, and everything after it is optional decoration.
    # So the tail is now `verb | end-of-clause`, which covers the bare form and every future one.
    # ⚠ Still safe by construction, and the guard is unchanged: this only ever GRANTS clean, and
    # only when NO block makes a defect claim. A red-proof asserts that a P1 following the
    # declaration is still filed as findings. [[unknown-stays-unknown]]
    r"(?:"
    r"\s+(?:were\s+|are\s+|was\s+|is\s+)?"
    r"(?:found|identified|detected|visible|apparent|evident|present|noted|observed|seen|"
    r"reported|meeting|matching|warranting|meriting)\b"
    r"|\s*(?:\*+\s*)?(?:[.;:!]|$)"      # "No concrete defects." / "**No concrete defects.**"
    r")",
    re.I)

#: ⚠⚠⚠ v3315 — THE FIFTH PHRASING, AND IT IS A DIFFERENT PART OF SPEECH. `_NO_DEFECT_RX` is a
#: NOUN-PHRASE pattern: it needs `no <...> defects|issues|bugs|problems`. Four versions widened its
#: vocabulary (v3216 `evident`, v3216 `present`, v3267 `meeting`, v3268 the bare full stop) and the
#: lesson drawn was "the declaration is the NOUN PHRASE". This shape has no such noun at all.
#:
#: MEASURED 2026-09-18 on the real v3301 look. Grok answered:
#:
#:     **Findings**
#:
#:     none found
#:
#: and the row was filed verdict="findings", findings=2 — the ledger asserting the eye found two
#: things when it had answered the opposite. The blocks were `**Findings** none found …` and
#: `**Visibility note** …`; `_claims_a_defect` was FALSE for both, so the only failing condition
#: was the declaration itself never matching. A reviewer told to say "none found" per category
#: says exactly that, and the prompt this repo sends ASKS for that wording.
#:
#: ⚠ SAFE BY CONSTRUCTION, on the same argument every prior widening used: this can only ever
#: GRANT clean, and only when `_claims_a_defect` is false for EVERY block. A review that says
#: "off-by-one: none found" and then lists a real P1 still lands in `findings`, because the claim
#: check is unchanged. A miss costs a noisy row; a false match cannot clear a real defect.
_NO_FINDING_RX = re.compile(
    r"(?:\bnone\s+found\b"
    r"|\bnothing\s+(?:found|wrong|to\s+report|of\s+note|to\s+flag)\b"
    r"|\bfindings?\b\s*[:\-\u2013\u2014]?\s*none\b"
    r"|\bnone\s*(?:\*+\s*)?(?:[.;:!]|$))", re.I)


def _declares_none(text):
    """Does this text DECLARE that nothing was found? -> bool

    Two shapes, and they are different parts of speech:
      · the NOUN PHRASE  — "no concrete defects found" (`_NO_DEFECT_RX`)
      · the PRONOUN      — "none found", "findings: none" (`_NO_FINDING_RX`)

    Kept as two named patterns rather than one, because the noun-phrase one has been corrected
    four times and restructuring it to carry a different part of speech is how the fifth
    correction becomes a sixth. [[copy-drift]]
    """
    t = text or ""
    return bool(_NO_DEFECT_RX.search(t) or _NO_FINDING_RX.search(t))


# a block that carries one of these is making a CLAIM about a defect, not describing a change.
# Used only to refuse a clean verdict, never to grant one — so a miss here costs nothing and a
# false hit only keeps a look in the stricter bucket.
_DEFECT_MARK_RX = re.compile(
    r"\b(?:P[0-9]\b|severity|critical|race\s+condition|deadlock|leak|crash|"
    r"unreachable|mismatch|disagree|fails?\b|breaks?\b|vulnerab)", re.I)

# ⚠⚠ A NEGATED MARKER IS THE OPPOSITE OF A MARKER, AND IT COST A CLEAN VERDICT. Measured on the
# real v3189 answer: its closing line is *"No caller/callee contract mismatches, races, leaks, or
# unreachable states are visible in the provided hunks."* — four marker words in one sentence,
# every one of them DENIED. Matching them read a reviewer listing what it did NOT find as a
# reviewer finding it. The clause is cut at the first `.`/`;`/`:` so a genuine claim sharing the
# block ("No defects found. P1: ...") still survives the strip. [[measured-true-read-wrong]]
# ⚠⚠ v3255 — AND "NOTHING" IS A NEGATION TOO. THIRD TIME THIS CLASS HAS BITTEN THIS FILE (v2808,
# v3198, now). Measured on the real v3252 answer, whose FIRST LINE is "**No concrete defects
# found.**": its closing sentence is *"Nothing in the shown hunks indicates a caller/callee
# contract violation, a race, a leak, an unreachable state, or any other observable defect."*
# `\bno\b` does not match "Nothing" — there is no word boundary after the "no" — so three marker
# words survived the strip and a review that said NO DEFECTS was filed as verdict="findings", in
# the ledger whose entire job is recording what another family concluded. Exactly the v2808
# defect, through a door the v3189 fix did not cover.
#
# ⚠ THIS WIDENS THE STRIP, WHICH IS THE DANGEROUS DIRECTION, AND IT IS BOUNDED ON PURPOSE. The
# strip is only consulted by `_verdict_for` AFTER the answer has already DECLARED no defects in
# its first block; an answer with no such declaration never reaches it. Measured both ways before
# shipping: "No defects found. P1: the caller crashes on empty input." still files as findings,
# and "Nothing validates the payload, so it crashes" (no declaration) still files as findings.
# [[measured-true-read-wrong]] [[strictness-that-closes-the-lane]]
_NEGATED_RX = re.compile(r"\b(?:nothing|no|not|none|never|without|free\s+of)\b[^.;:]*", re.I)


def _claims_a_defect(block):
    """does this block CLAIM a defect — as opposed to naming one it rules out?"""
    return bool(_DEFECT_MARK_RX.search(_NEGATED_RX.sub(" ", block or "")))


def _verdict_for(answer, findings):
    """"clean" or "findings" — and a declaration alone can never clear a real defect claim.

    ⚠ v2808 — A CLEAN LOOK WAS BEING FILED AS ONE THAT FOUND DEFECTS. `_findings_from` folds an
    unenumerated answer into a single block, so "No defects found." came back as findings=[<the
    whole answer>] and the row read verdict="findings". The v2807 row said the eye had found
    something when it had said the opposite, in the ledger whose entire job is to record what
    another family concluded. [[label-outlived-referent]]

    ⚠⚠ v3198 — THAT FIX WAS `len(findings) > 1`, AND IT WAS WRONG IN BOTH DIRECTIONS. Measured,
    2026-09-16, by probing it with four hand-built answers:

        "No concrete defects found."  + 3 blocks describing the diff   -> findings   WRONG
        "No defects found." + ONE listed P1                            -> clean      WRONG, and
                                                                          this is the dangerous
                                                                          direction

    The second is the one that matters. A declaration followed by exactly ONE defect produced
    `len(findings) == 1`, which is not `> 1`, so the declaration cleared it and a real P1 was
    filed as a clean look. The docstring above says "a model that declares no defects and then
    lists three stays findings" — true for three, FALSE for one, and nothing measured the claim.
    [[feedback-blind-fixture-green-gate]] — a rule nobody ever saw refuse.

    THE RULE NOW HAS THREE PARTS, and all three must hold before a look is cleared:
      1. the answer DECLARES no defects, and
      2. the declaration is in the FIRST block — a list of defects does not begin with
         "no defects found", so order is the measurable tell, and
      3. no block makes a defect CLAIM (`_DEFECT_MARK_RX`).
    Anything else stays "findings". That is deliberately asymmetric: over-reporting a finding
    costs a re-read, under-reporting one ships a defect with a clean stamp on it.
    """
    decl_anywhere = _declares_none(answer)
    if not decl_anywhere:
        # ⚠⚠ v3346 — AN UNPARSED ANSWER IS `cannot-tell`, NEVER A DEFECT. This branch fires when the
        # answer does not DECLARE cleanliness in a phrasing _declares_none recognises. v3343 landed
        # here saying "The diff is correct. No defects, races, contract mismatches, leaks, or
        # unreachable states are present" — a comma-tail #76 measured and REFUSED to widen for, and
        # rightly: _claims_a_defect covers only 103 of 628 findings-rows, so the narrow declaration
        # IS the safety.
        #
        # So the fix is not in the declaration. It is that the "finding" here was the WHOLE ANSWER:
        # no line started a finding, so _findings_from had nothing to split on and swallowed it. A
        # parse that found no structure is UNKNOWN, and the ledger already has the word for it —
        # `cannot-tell` is in PARSER_VERDICTS and 13 rows use it.
        #
        # ⚠ ALL THREE CONDITIONS, because this function has been wrong here twice (v2808, v3198 —
        # "wrong in both directions"). It fires ONLY when nothing parsed AND nothing is claimed:
        #   · a real findings answer NUMBERS its findings -> has structure -> untouched
        #   · a prose answer that CLAIMS a defect          -> stays `findings`, never downgraded
        #   · v3341/v3342/v3344 declare cleanliness        -> never reach this branch at all
        # MEASURED across the four looks taken today: exactly ONE (v3343) satisfies all three.
        # `cannot-tell` is not clean either, so nothing is cleared by it. [[unknown-stays-unknown]]
        if findings and not _has_finding_structure(answer) \
                and not any(_claims_a_defect(f) for f in findings) \
                and _SAYS_NO_DEFECT_RX.search(answer):
            return "cannot-tell", []
        return ("findings" if findings else "clean"), findings
    if not findings:
        return "clean", []
    opens_clean = _declares_none(findings[0])
    claims = [f for f in findings if _claims_a_defect(f)]
    if opens_clean and not claims:
        return "clean", []
    return "findings", findings


def _model_from_answer(answer):
    """Which model actually produced this answer? -> slug or None. Read from the BYTES.

    ⚠⚠ v3216 — IN HANDOFF MODE THE LEDGER RECORDED THE CONFIGURED GROK DEFAULT NO MATTER WHO
    ANSWERED. `--answer-in` passed `model=EYE_MODEL`, which is `grok-4-1-fast-reasoning` unless
    THIRD_EYE_MODEL is set — so three real OpenAI looks (v3214, v3215, v3216, all produced by
    `gpt-5.6-terra`) were filed as **family=xai**. The ledger's own docstring says family "is
    derived from the model id, not asserted" because "a same-family agent writing plausible
    strings must never be mistakable for a cross-family look" — and that derivation was correct
    while its INPUT was a guess. The one question this file exists to answer was being answered
    from configuration rather than from evidence.

    ⚠ AND IT FAILS CLOSED. If the answer does not say, this returns None and the caller records an
    UNKNOWN model rather than inheriting the default — an unattributable look must not be able to
    discharge a cross-family debt. [[unknown-stays-unknown]] [[the-unjoined-end]]
    """
    head = (answer or "")[:4000]
    m = re.search(r"(?mi)^\s*(?:\x1b\[[0-9;]*m)?model:(?:\x1b\[[0-9;]*m)?\s*([A-Za-z0-9._-]+)", head)
    return m.group(1) if m else None


def _strip_echo(answer, prompt):
    """Drop a prompt the tool echoed back before its reply. -> str

    ⚠⚠ v3216 — THE ECHO WAS BEING COUNTED AS FINDINGS. `codex exec` prints the whole prompt —
    including the DIFF — before its answer, and `_findings_from` split that too. Every handoff row
    came back with exactly **12** findings (the `[:12]` cap) whose text was
    `'--- a/tv/control_app.py'` and `'Reading prompt from stdin...'`, and a reply that said
    *"No concrete functional defect is evident in this diff"* was filed as `verdict=findings`.
    A constant is not a measurement. [[zero-needs-a-denominator]] [[feedback-suspect-the-instrument]]
    """
    a = answer or ""
    tail = (prompt or "").strip()[-160:]
    if tail and tail in a:
        a = a[a.rindex(tail) + len(tail):]
    # ⚠⚠ AND THE TERMINAL CONTROL BYTES, which is why the first cut of this still mis-read a
    # CLEAN answer. `codex exec` writes its reply behind an ANSI colour run and a `codex` speaker
    # label, so `findings[0]` began `\x1b[35m\x1b[3mcodex\x1b[0m ... No concrete functional
    # defect is evident` — and `_NO_DEFECT_RX`, which anchors near the start, never matched. The
    # row then said verdict=findings over a reply that found nothing. Over-reporting is the safe
    # direction, but a verdict that disagrees with its own answerHead is still a broken instrument.
    a = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", a)
    a = re.sub(r"(?m)\A\s*(codex|assistant)\s*$", "", a).lstrip()
    return a.lstrip()


#: ⚠⚠ DOWNGRADE-ONLY, AND THAT IS THE WHOLE SAFETY ARGUMENT. This may move a row from `findings`
#: to `cannot-tell`. It may NEVER produce `clean`, and `_declares_none` — the function that DOES
#: decide clean — is untouched. #76 measured that widening _declares_none cannot be made safe
#: (_claims_a_defect covers only 103 of 628 findings-rows), and that ruling stands; this is a
#: different question asked in a different direction.
#:
#: ⚠ SIZED AGAINST THE REAL LEDGER BEFORE SHIPPING, because my first cut was REFUTED by it. Without
#: this phrase test the structure-absence rule alone would have reclassified 172 of 637 findings
#: rows — including v2180 "FINDING 1: Saved OFF is overruled by an env ON", a real defect. With it,
#: 13 flip, and reading them: v2805 "No defects found", v2850/v2851/v3207/v3266 "The diff is correct
#: as shown", v3147 "No concrete defects found" — clean looks that were misfiled as findings, the
#: same defect as v3343. ONE is a wrong flip, v2837 ("real hazard, cache never cleared"), and it
#: lands on cannot-tell rather than clean, so nothing is cleared and a re-read is prompted. That is
#: the safe direction this function's own docstring names. [[regression-guard]] §5a
_SAYS_NO_DEFECT_RX = re.compile(
    r"(no\s+(concrete\s+)?(defects?|issues?|problems?|bugs?)\b"
    r"|the\s+diff\s+is\s+correct"
    r"|is\s+correct\s+(on|as)\s+(the\s+)?(bytes|shown)"
    r"|correct\s+as\s+shown)", re.I)

#: What STARTS a finding. ONE definition — _findings_from splits on it and _has_finding_structure
#: asks whether it ever matched, and a second copy is how the two disagree about the same answer.
#: [[copy-drift]]
_FINDING_START_RX = re.compile(r"^(\d+[\.\)]|[-*•]|\*\*\d+)")


def _has_finding_structure(answer):
    """Did ANY line start a finding? -> bool

    ⚠ v3346 — THIS IS THE DIFFERENCE BETWEEN A DEFECT AND AN UNPARSED ANSWER. _findings_from joins
    every non-starting line onto the block above, so an answer with NO numbered or bulleted line
    comes back as ONE finding whose text is the WHOLE ANSWER — REACH line, verdict and all. That is
    not something the eye reported; it is a parse that found no structure, and it read as the worse
    of the two. MEASURED on v3343: the eye said "The diff is correct. No defects, races, contract
    mismatches, leaks, or unreachable states are present" and the row was filed verdict=findings,
    findings=1. [[unknown-stays-unknown]]
    """
    for ln in (answer or "").splitlines():
        if _FINDING_START_RX.match(ln.strip()):
            return True
    return False


def _findings_from(answer):
    """Split the answer into findings without interpreting them. Numbered or bulleted lines start
    a finding; everything else joins the one above."""
    out, cur = [], []
    for ln in answer.splitlines():
        s = ln.strip()
        if _FINDING_START_RX.match(s) and cur:
            out.append(" ".join(cur).strip())
            cur = [s]
        elif s:
            cur.append(s)
    if cur:
        out.append(" ".join(cur).strip())
    return [f for f in out if len(f) > 30][:12]


# ⚠⚠ THE CLI ON THIS MACHINE IS AGENTIC, NOT ONE-SHOT — MEASURED, and it changes the design.
# Given a 3,052-char prompt and 120s it replied: "I'll review the snippet against the surrounding
# source... I'll read the rest of the function... I'll inspect hover_mode, the GET status path,
# occupancy parsing, and tests" — and was still exploring the repository when the budget expired.
# It is not slow at answering; it is doing a different job. A one-shot chat endpoint answered the
# same class of payload in seconds.
#
# So the eye has TWO shapes and this script supports both rather than pretending one exists:
#   · CLI mode      — unattended, long budget, deeper because it reads the tree. Background it.
#   · handoff mode  — --prompt-out / --answer-in. The payload is still assembled and MEASURED
#                     here, and the answer is still recorded from the bytes that came back; only
#                     the transport is external. Every number in the row stays measured.
# The one thing neither mode may do is let an unanswered ask read as agreement.


def record_answer(version, answer, sent, dropped="", prompt_text="", answer_model="",
                  sha="", absent=None, reach=None):
    """Record an answer obtained by ANY transport, with the payload's measured `sent`."""
    version = SEL.norm_version(version)
    answer = (answer or "").strip()
    # ⚠⚠⚠ v3220 — THE EMPTINESS TEST MUST RUN ON THE REPLY, NOT ON THE ECHO. v3216 taught this
    # function to strip the tool's echoed prompt — and left this guard ABOVE the strip, reading the
    # raw bytes. `codex exec` prints the whole payload before replying, so a run that produced NO
    # REPLY AT ALL still arrived here as ~10,000 characters and sailed past `len(answer) < 40`.
    #
    # MEASURED 2026-09-16, and it filed two lies: the Codex seat answered
    # "ERROR: You've hit your usage limit … try again at Oct 12th" for BOTH v3217 and v3218, and
    # each was recorded as **LOOKED — 1 finding**. The ledger's whole purpose is that an
    # unreachable eye is an EMPTY SEAT and never agreement, and the push gate reads `reached`.
    # A false LOOKED does not merely mis-report — it opens a gate that should have stayed shut.
    #
    # So: strip FIRST, then judge what is left, and treat a provider-level refusal as unreached
    # however long it is. [[unknown-stays-unknown]] [[grok-second-eye]]
    _reply = _strip_echo(answer, prompt_text) if prompt_text else answer
    # ⚠⚠⚠ v3223 — A REFUSAL *IS* THE WHOLE ANSWER; A REVIEW MERELY MENTIONS THESE WORDS.
    # v3220's regex matched "quota", "rate-limit", "unauthor", "authentication", "please sign in"
    # ANYWHERE in the first 400 chars. A cross-family look at v3221 named the trap: a genuine
    # review that says *"authentication is not checked"* or *"quota is never decremented"* would be
    # discarded as a provider refusal — and a review OF THIS VERY DIFF would contain those words.
    # That is the over-refusing direction `AProviderRefusalIsAnEmptySeat` names in its own
    # docstring: it would turn every real eye into an empty seat, which is worse than the false
    # LOOKED it was written to stop, because a discarded look is invisible.
    #
    # A provider refusal is SHORT and it is the ENTIRE reply — the tool printed nothing else.
    # A review is long and discusses many things. So: an explicit `ERROR:` opener always counts,
    # and the softer vocabulary only counts when the whole reply is too short to be a review.
    # [[unknown-stays-unknown]] [[feedback-blind-fixture-green-gate]]
    # ⚠ ANCHORED AT THE OPENING, NOT LENGTH. My first cut added "…or it matches anywhere and the
    # reply is under 600 chars", and a 434-char REVIEW about authentication was refused by it.
    # Length is the wrong instrument: a short review is still a review. What separates the two is
    # that a provider refusal is the FIRST thing the tool says, because it never got further.
    _refused = bool(_PROVIDER_ERROR_RX.match(_reply.lstrip()))
    if len(_reply) < 40 or _refused:
        _why = ("the provider refused: %s" % _reply.strip().splitlines()[0][:110]) if _refused \
               else ("the answer was %d chars" % len(_reply))
        SEL.record(version=version, model=(_model_from_answer(answer) or answer_model or ""),
                   verdict="", findings=[], images=[],
                   asked=COLD_FRAMING.strip()[:200], answer_head=_reply, head_cap=200, reached=False,
                   path=None, seen_path=None, sent=sent, sha=sha)
        print("  %s: %s — EMPTY SEAT, not agreement" % (version, _why))
        return False
    # ⚠⚠ v3216 — STRIP THE ECHO AND READ WHO ACTUALLY ANSWERED, because handoff mode was doing
    # neither. `codex exec` prints the whole prompt — diff included — before its reply, so the
    # splitter counted the ECHO: every handoff row came back with exactly 12 findings (the cap)
    # reading `'--- a/tv/control_app.py'`, and a reply saying "No concrete functional defect is
    # evident" was filed as verdict=findings. And `model=EYE_MODEL` recorded the configured GROK
    # default no matter who answered, so three real `gpt-5.6-terra` looks were filed family=xai —
    # the ledger asserting a Grok seat that was never occupied. [[unknown-stays-unknown]]
    # ⚠ ORDER MATTERS, AND I GOT IT WRONG FIRST: the tool prints its `model:` header BEFORE the
    # echoed prompt, so stripping the echo first throws away the one piece of evidence that says
    # who answered. Read the model from the RAW bytes, then strip.
    _model = _model_from_answer(answer) or answer_model or ""
    answer = _strip_echo(answer, prompt_text)
    findings = _findings_from(answer)
    _verdict, findings = _verdict_for(answer, findings)
    SEL.record(version=version, model=_model,
               verdict=_verdict,
               findings=findings, images=[],
               asked=(COLD_FRAMING.strip() + (" [%s]" % dropped if dropped else ""))[:400],
               answer_head=answer, head_cap=400, reached=True, path=None, seen_path=None, sent=sent,
               sha=sha, absent=absent, reach=reach)
    print("  %s: LOOKED — %d finding(s) recorded" % (version, len(findings)))
    return True


def run_one(version, dry=False, prompt_out=None, answer_in=None, answer_model=""):
    version = SEL.norm_version(version)
    sha, why = commit_for(version)
    if not sha:
        print("  %s: cannot find the commit — %s" % (version, why))
        return False
    prompt, dropped, absent, reach = payload_for(sha)
    if prompt is None:
        print("  %s: cannot build the payload — %s" % (version, dropped))
        return False
    sent = SEL.code_was_transmitted(prompt)
    print("  %s  %s  payload: %d chars in %d fence(s)%s"
          % (version, sha[:8], sent["chars"], sent["fences"],
             ("  ⚠ " + dropped) if dropped else ""))
    # ⚠⚠ v3299 — SAY WHAT THIS LOOK DOES **NOT** COVER. `payload_for` runs `git show <sha>` on the
    # ONE commit carrying the version stamp, so every `fix:` commit landing after the bump and
    # before the push is NEVER SEEN BY ANY EYE — and the row that lands reads as though the push
    # was reviewed.
    # MEASURED 2026-09-18, v3298: four commits shipped in one push and the eye saw ONE of them.
    # The unseen three included the membership discriminator, which went through THREE cuts (two
    # wrong) and is the most consequential change in the push. The verdict then attacked
    # `_fnew > _dm + 0.5` — code SUPERSEDED two commits later. That is not the eye being wrong;
    # it is the gate handing it bytes that no longer ship.
    # ⚠ This prints the gap rather than closing it. Closing it means a wider payload, and the
    # payload already truncates at ~35% — the two are one problem and the cost is HIS call.
    # A guard that cannot state its own reach is the defect this repo keeps re-learning.
    # [[source-reading-guard]] [[zero-needs-a-denominator]]
    _rows = uncovered_commits(sha)
    if _rows is None:
        print("     ⚠ could not list commits after %s — what this look MISSES is UNKNOWN, not zero"
              % sha[:8])
    elif _rows:
        print("     ⚠ THIS LOOK COVERS %s ONLY. %d later commit(s) ship with it and are NOT "
              "reviewed:" % (sha[:8], len(_rows)))
        for _r in _rows[:6]:
            print("        %s" % _r[:96])
        if len(_rows) > 6:
            print("        ... +%d more" % (len(_rows) - 6))
    if sent["chars"] == 0:
        print("     nothing to look at — the diff carried no code. NOT recorded.")
        return False
    if prompt_out:
        with io.open(prompt_out, "w", encoding="utf-8") as fh:
            fh.write(prompt)
        print("     payload written to %s — ask any eye, then --answer-in" % prompt_out)
        return True
    if answer_in:
        with io.open(answer_in, encoding="utf-8") as fh:
            # the PROMPT is passed so the echo can be stripped, and the model is read from the
            # answer's own bytes rather than inherited from whatever THIRD_EYE_MODEL happens to be
            # v3364 - AND `reach` TRAVELS TOO. v3363 added the parameter to record_answer and
            # the forwarding INTO the ledger, and wired NEITHER CALLER - so every row it wrote
            # carried reach=None, which is byte-identical to a row written before the field
            # existed. Found by using it: v3363's OWN row came back reach=NoneType while the eye
            # had said "REACH 2/7". [[the-unjoined-end]] - third time in this one area.
            return record_answer(version, fh.read(), sent, dropped,
                                 prompt_text=prompt, answer_model=answer_model, sha=sha,
                                 absent=absent, reach=reach)
    if dry:
        return True
    answer, reached, awhy = ask(prompt)
    if not reached:
        SEL.record(version=version, model=EYE_MODEL, verdict="", findings=[], images=[],
                   asked=COLD_FRAMING.strip()[:200],
                   answer_head=(answer or ""), head_cap=200, reached=False,
                   path=None, seen_path=None, sent=sent, sha=sha)
        print("     EMPTY SEAT — %s  (recorded as unreached, never as agreement)" % awhy)
        return False
    # ⚠⚠⚠ v3221 — ONE RECORDER, NOT TWO. v3220 fixed the empty-seat guard in `record_answer` and
    # this path never called it: the CLI door recorded inline, so it stripped no echo and ran no
    # `_PROVIDER_ERROR_RX`. `ask()` treats "exit 0 and >= 40 chars" as a look — and a Grok CLI that
    # exits 0 with a long usage-limit or auth body is exactly that. So the SAME false-LOOKED bug
    # REG-1017 documents was still live on the DEFAULT door (and on `--backlog`), one function
    # away from its own fix. Found by the Grok seat reviewing v3220, which is the version that
    # fixed the other half.
    #
    # Fixing one copy of a rule and leaving its twin is the defect this repo keeps finding. The
    # answer is not a second guard here — it is routing both doors through the one guard.
    # [[copy-drift]] [[sweep-dont-ask]] [[the-unjoined-end]]
    # v3229 — the transport names the family when the answer does not. FALLBACK ONLY:
    # record_answer prefers the model the answer's own bytes name.
    return record_answer(version, answer, sent, dropped, prompt_text=prompt,
                         answer_model=_model_from_transport(), absent=absent, reach=reach)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("version", nargs="?")
    ap.add_argument("--backlog", action="store_true",
                    help="every version the ledger still says OWES a look")
    ap.add_argument("--dry", action="store_true", help="build and measure, send nothing")
    ap.add_argument("--prompt-out", help="write the measured payload here instead of asking")
    ap.add_argument("--answer-in", help="record this answer against the measured payload")
    # ⚠ v3216 — for an eye whose output does not NAME its model. Without it the row records an
    # empty model, family_of() returns None, and the look does NOT discharge a cross-family debt —
    # which is the right way to fail: an unattributable answer is not evidence about who looked.
    ap.add_argument("--answer-model", default="",
                    help="the model that produced --answer-in, when the answer does not say")
    a = ap.parse_args(argv)
    if a.backlog:
        # ⚠⚠ v2848 — THE BACKLOG COMMAND HAS BEEN CRASHING, SO NOTHING REPORTED THE QUEUE.
        # `SEL.audit(None)` returns a list of DICTS — {version, attempts, empty, author, looks,
        # bound, unbound} — and this unpacked each row into `v, st`. Iterating a dict yields its
        # KEYS, and seven keys will not unpack into two, so every invocation died with
        # `ValueError: too many values to unpack (expected 2)`. The one command whose entire job is
        # "show me what is stacking up" answered nothing but a traceback, which is why the second
        # eye backlog was only ever discovered by a push being REFUSED at the gate.
        # ⚠ A version OWES a look when it has ZERO real looks. `empty` (a seat that was offered and
        # came back dark) and `author` (a look by the same family that wrote the code) are NOT
        # looks — counting them would clear the queue without anyone having looked.
        # [[the-unjoined-end]] [[unknown-stays-unknown]]
        _rows = SEL.audit(None) if callable(getattr(SEL, "audit", None)) else []
        _known = {r.get("version") for r in _rows if isinstance(r, dict)}
        owed = [r.get("version") for r in _rows
                if isinstance(r, dict) and not int(r.get("looks") or 0)]
        # ⚠⚠ AND THE VERSIONS THE LEDGER HAS NEVER HEARD OF. See versions_in_history(): a shipped
        # version with no row is the STRONGEST case of owing a look, and it was the only one this
        # command could not report. Ask the same predicate the gate asks.
        _shipped, _why = versions_in_history()
        for _v in _shipped:
            if _v not in _known and SEL.owes_a_look(_v):
                owed.append(_v)
        owed = sorted(set(owed), key=lambda x: -int(x[1:]) if x[1:].isdigit() else 0)
        if not owed:
            # ⚠ a zero carries its denominator, or it is UNKNOWN rather than clean.
            print("  nothing owes a look — %d ledger row(s), %d shipped version(s) examined.%s"
                  % (len(_rows), len(_shipped), (" (%s)" % _why) if _why else ""))
            return 0
        print("  %d version(s) owe a look: %s     [%d ledger row(s), %d shipped version(s) examined]"
              % (len(owed), ", ".join(owed), len(_rows), len(_shipped)))
        ok = all(run_one(v) for v in owed)
        return 0 if ok else 1
    if not a.version:
        ap.print_help()
        return 2
    return 0 if run_one(a.version, dry=a.dry, prompt_out=a.prompt_out,
                        answer_model=a.answer_model,
                        answer_in=a.answer_in) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
