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
        m = _VER_LEADING_RUN.match(line)
        if not m:
            continue
        for tok in _VER_TOKEN.findall(m.group(1)):
            if tok not in seen:
                seen.add(tok)
                vs.append(tok)
    return vs, ""


def commit_for(version):
    """The commit whose subject stamps this version. -> sha | None"""
    out, why = _sh(["git", "log", "--format=%H %s", "-400"])
    if out is None:
        return None, why
    rx = re.compile(r"\b%s\b" % re.escape(version))
    for line in out.splitlines():
        sha, _, subject = line.partition(" ")
        if rx.search(subject):
            return sha, ""
    return None, "no commit subject names %s in the last 400" % version


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
    body = _strip_comments(out)
    _full_len_holder = [body]
    if len(body) < _cap():
        _more, _ = _sh(["git", "show", "--format=", "--unified=3", sha, "--", "*.html"],
                       timeout=90)
        if _more:
            body = body + "\n" + _strip_comments(_more)
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
        cut = body.rfind("\n", 0, _cap())
        body = body[:cut if cut > 0 else _cap()]
        dropped = ("truncated to %d of %d diff chars at a line boundary — the eye saw the first "
                   "part only" % (len(body), len(_full_len_holder[0])))
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
    return COLD_FRAMING + note + "\n```diff\n" + body + "\n```\n", dropped


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
_PROVIDER_ERROR_RX = re.compile(
    r"(?im)^\s*ERROR\b|usage limit|rate[- ]limit|quota|not supported when using|"
    r"invalid_request_error|unauthor|authentication|please (?:sign|log) in")


_NO_DEFECT_RX = re.compile(
    r"\bno\s+(?:\w+\s+){0,2}(?:defects?|issues?|bugs?|problems?)\s+"
    # ⚠ v3216 — `evident` AND `present` ADDED, and `is` to the copula list. An OpenAI seat wrote
    # "No concrete functional defect is evident in this diff", every block scored
    # claims_a_defect=False, and the row STILL said verdict=findings — because the declaration
    # used a verb this list did not carry. Widening here is safe by construction: the pattern only
    # ever GRANTS clean, and only when `claims` is simultaneously empty, so a miss costs a noisy
    # row and a false match still cannot clear a real finding. [[unknown-stays-unknown]]
    r"(?:were\s+|are\s+|was\s+|is\s+)?(?:found|identified|detected|visible|apparent|evident|present)\b",
    re.I)

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
_NEGATED_RX = re.compile(r"\b(?:no|not|none|never|without|free\s+of)\b[^.;:]*", re.I)


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
    decl_anywhere = _NO_DEFECT_RX.search(answer or "")
    if not decl_anywhere:
        return ("findings" if findings else "clean"), findings
    if not findings:
        return "clean", []
    opens_clean = bool(_NO_DEFECT_RX.search(findings[0] or ""))
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


def _findings_from(answer):
    """Split the answer into findings without interpreting them. Numbered or bulleted lines start
    a finding; everything else joins the one above."""
    out, cur = [], []
    for ln in answer.splitlines():
        s = ln.strip()
        if re.match(r"^(\d+[\.\)]|[-*•]|\*\*\d+)", s) and cur:
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


def record_answer(version, answer, sent, dropped="", prompt_text="", answer_model=""):
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
    _refused = bool(_PROVIDER_ERROR_RX.search(_reply[:400]))
    if len(_reply) < 40 or _refused:
        _why = ("the provider refused: %s" % _reply.strip().splitlines()[0][:110]) if _refused \
               else ("the answer was %d chars" % len(_reply))
        SEL.record(version=version, model=(_model_from_answer(answer) or answer_model or ""),
                   verdict="", findings=[], images=[],
                   asked=COLD_FRAMING.strip()[:200], answer_head=_reply[:200], reached=False,
                   path=None, seen_path=None, sent=sent)
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
               answer_head=answer[:400], reached=True, path=None, seen_path=None, sent=sent)
    print("  %s: LOOKED — %d finding(s) recorded" % (version, len(findings)))
    return True


def run_one(version, dry=False, prompt_out=None, answer_in=None, answer_model=""):
    version = SEL.norm_version(version)
    sha, why = commit_for(version)
    if not sha:
        print("  %s: cannot find the commit — %s" % (version, why))
        return False
    prompt, dropped = payload_for(sha)
    if prompt is None:
        print("  %s: cannot build the payload — %s" % (version, dropped))
        return False
    sent = SEL.code_was_transmitted(prompt)
    print("  %s  %s  payload: %d chars in %d fence(s)%s"
          % (version, sha[:8], sent["chars"], sent["fences"],
             ("  ⚠ " + dropped) if dropped else ""))
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
            return record_answer(version, fh.read(), sent, dropped,
                                 prompt_text=prompt, answer_model=answer_model)
    if dry:
        return True
    answer, reached, awhy = ask(prompt)
    if not reached:
        SEL.record(version=version, model=EYE_MODEL, verdict="", findings=[], images=[],
                   asked=COLD_FRAMING.strip()[:200],
                   answer_head=(answer or "")[:200], reached=False,
                   path=None, seen_path=None, sent=sent)
        print("     EMPTY SEAT — %s  (recorded as unreached, never as agreement)" % awhy)
        return False
    findings = _findings_from(answer)
    _verdict, findings = _verdict_for(answer, findings)
    SEL.record(version=version, model=EYE_MODEL,
               verdict=_verdict,
               findings=findings, images=[],
               asked=(COLD_FRAMING.strip() + (" [%s]" % dropped if dropped else ""))[:400],
               answer_head=answer[:400], reached=True,
               path=None, seen_path=None, sent=sent)
    print("     LOOKED — %d finding(s) recorded" % len(findings))
    for f in findings[:3]:
        print("       · %s" % f[:150])
    return True


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
