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
    """Drop comment-only ADDED lines. The code still reads; the author's account of it does not."""
    keep = []
    for ln in diff.splitlines():
        if ln.startswith("+") and not ln.startswith("+++"):
            body = ln[1:]
            if _PY_COMMENT.match(body) or _JS_COMMENT.match(body) or not body.strip():
                continue
        keep.append(ln)
    return "\n".join(keep)


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


_NO_DEFECT_RX = re.compile(
    r"\bno\s+(?:defects?|issues?|bugs?|problems?)\s+(?:were\s+)?(?:found|identified|detected)\b",
    re.I)


def _verdict_for(answer, findings):
    """"clean" or "findings" — and a declaration alone can never clear an enumerated list.

    ⚠ v2808 — A CLEAN LOOK WAS BEING FILED AS ONE THAT FOUND DEFECTS. `_findings_from` folds an
    unenumerated answer into a single block, so "No defects found." came back as findings=[<the
    whole answer>] and the row read verdict="findings". The v2807 row said the eye had found
    something when it had said the opposite, in the ledger whose entire job is to record what
    another family concluded. [[label-outlived-referent]]

    The rule is deliberately conservative in the direction that matters: a model that declares
    "no defects found" and then lists three stays "findings". Only an answer with NO enumerated
    item and an explicit declaration is clean, so this can never be used to bury a real finding.
    """
    enumerated = len(findings) > 1
    if not enumerated and _NO_DEFECT_RX.search(answer or ""):
        return "clean", []
    return ("findings" if findings else "clean"), findings


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


def record_answer(version, answer, sent, dropped=""):
    """Record an answer obtained by ANY transport, with the payload's measured `sent`."""
    version = SEL.norm_version(version)
    answer = (answer or "").strip()
    if len(answer) < 40:
        SEL.record(version=version, model=EYE_MODEL, verdict="", findings=[], images=[],
                   asked=COLD_FRAMING.strip()[:200], answer_head=answer[:200], reached=False,
                   path=None, seen_path=None, sent=sent)
        print("  %s: the answer was %d chars — EMPTY SEAT, not agreement" % (version, len(answer)))
        return False
    findings = _findings_from(answer)
    _verdict, findings = _verdict_for(answer, findings)
    SEL.record(version=version, model=EYE_MODEL,
               verdict=_verdict,
               findings=findings, images=[],
               asked=(COLD_FRAMING.strip() + (" [%s]" % dropped if dropped else ""))[:400],
               answer_head=answer[:400], reached=True, path=None, seen_path=None, sent=sent)
    print("  %s: LOOKED — %d finding(s) recorded" % (version, len(findings)))
    return True


def run_one(version, dry=False, prompt_out=None, answer_in=None):
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
            return record_answer(version, fh.read(), sent, dropped)
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
        owed = [r.get("version") for r in _rows
                if isinstance(r, dict) and not int(r.get("looks") or 0)]
        if not owed:
            print("  nothing owes a look.")
            return 0
        print("  %d version(s) owe a look: %s" % (len(owed), ", ".join(owed)))
        ok = all(run_one(v) for v in owed)
        return 0 if ok else 1
    if not a.version:
        ap.print_help()
        return 2
    return 0 if run_one(a.version, dry=a.dry, prompt_out=a.prompt_out,
                        answer_in=a.answer_in) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
