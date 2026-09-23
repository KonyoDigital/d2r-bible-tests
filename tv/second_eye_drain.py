# -*- coding: utf-8 -*-
"""Drain the #231 SECOND-EYE lane into the ledger, so a look that happened becomes a look the
gate can SEE.

⚠⚠ WHY THIS EXISTS, AND IT IS NOT TIDINESS. MEASURED 2026-09-23, and it cost a whole review:
the #231 seat reviewed **v3449** at 181,141 chars and reported, in plain words, BOTH defects that
were later "found" by a fresh Grok call and shipped as v3452 —

    "(1) ... reached is true, red is false, the job is failure, the new guard does not fire, and
     the failure arm prints 'the gate set reached a verdict and it was RED.'"
    "(2) ... the abort summary and .render_verdict.json call _budget_shortened_the_read() and
     _declared_page_patience() with no spec, so both still use the registry maximum, 30s ...
     a target granted the 12s default (18 of 20)."

Same two defects. The same 18-of-20 denominator. It sat unread on GitHub while the same ground was
covered again from scratch, because THE LANE POSTS TO GITHUB AND NOTHING CARRIES IT TO THE LEDGER.
Both halves were built and never joined. [[the-unjoined-end]]

⚠ AND IT IS NOW THE ONLY REACHABLE EYE (#198). On the same day all three local transports refused
within minutes of each other: the Grok CLI hung (rc=142 after a 560s stall), the xAI API answered
PERMISSION_DENIED for exhausted credits, and Codex hit a usage limit that does not reset until
Oct 12. The pre-push gate blocks on an unlooked-at version, so this drain is the way through.

WHAT IT DOES NOT DO, on purpose:
 · IT NEVER JUDGES. It copies what the seat said — verdict, model, sha, chars, reach, findings —
   and records it. A drainer that re-scored a verdict would be a second opinion wearing the first
   one's name.
 · IT NEVER MOVES THE HANDOFF WATERMARK. tv/handoff.py owns that, and marking #231 read here
   would make a human drain of the same issue silently skip comments. One owner per watermark.
 · IT NEVER INVENTS A FAMILY. `model` goes in verbatim and second_eye_ledger.family_of() decides;
   an unrecognised id stays UNKNOWN rather than being guessed into a family. [[unknown-stays-unknown]]

IDEMPOTENT BY CONSTRUCTION: every row it writes carries `verdictFrom = "gh#231 comment <id>"`, and
a comment whose id is already in the ledger is skipped. The ledger is append-only, so a drainer
that could double-record would inflate `looks` and turn one witness into a false corroboration —
the exact failure #182 was built to end.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ THIS FILE PRINTS ⚠, ⓘ AND · AND HAS A __main__. On his Windows box python stdout is cp1255,
# where one emoji CRASHES the script — and the pre-push encoding gate refuses an unguarded entry
# point outright (it refused a whole batch earlier today). [[windows-powershell-gotchas]]
try:
    from console_safe import enable as _cs
    _cs()
except Exception:
    pass

import handoff as _handoff                      # noqa: E402  the one GitHub reader, reused
import second_eye_ledger as _led                # noqa: E402

ISSUE = 231

#: the lane's own header. A comment without it is not a look and must not become a row.
_MARKER = "SECOND-EYE"

#: `field: value` up to the next field or the end. DOTALL so a multi-line `findings:` survives —
#: the v3449 finding above is one paragraph of prose and truncating it would throw away the half
#: that names the failing scenario.
_FIELDS = ("version", "sha", "verdict", "model", "chars", "reach", "not shown", "findings")


def parse_comment(body):
    """One SECOND-EYE comment -> dict, or None when it is not one. Never raises.

    ⚠ A MISSING FIELD IS None, NEVER A DEFAULT. A comment with no `sha:` must not be recorded as
    though it named a commit — 89.5% of the ledger already cannot say which commit it read, and
    quietly adding more is how a version LABEL gets mistaken for a commit. [[unknown-stays-unknown]]
    """
    text = str(body or "")
    if _MARKER not in text:
        return None
    out = {}
    for name in _FIELDS:
        # stop at the next known field so a value cannot swallow the rest of the comment
        others = "|".join(re.escape(f) for f in _FIELDS if f != name)
        m = re.search(r"^%s:[ \t]*(.*?)(?=^(?:%s):|\Z)" % (re.escape(name), others),
                      text, re.MULTILINE | re.DOTALL)
        out[name] = (m.group(1).strip() or None) if m else None
    if not out.get("version"):
        return None                       # a look that cannot name its version cannot be filed
    return out


def _chars(raw):
    """-> int or None. Unparseable is UNKNOWN, never 0 — a 0 would read as 'nothing was sent'."""
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return None


def _findings_list(raw):
    """-> list. `none` is an EMPTY list (measured: the seat found nothing); absent is also empty,
    but the caller distinguishes them via the verdict the seat published."""
    s = (raw or "").strip()
    if not s or s.lower() in ("none", "none.", "no findings"):
        return []
    return [s]


def already_recorded():
    """The set of #231 comment ids the ledger already holds. -> set(str)

    ⚠ READ FROM THE LEDGER ITSELF, not from a side file. A watermark stored anywhere else can drift
    out of step with the thing it claims to describe, and then a re-drain silently doubles a look.
    """
    seen = set()
    for row in _led._rows():
        vf = str(row.get("verdictFrom") or "")
        m = re.search(r"gh#%d comment (\d+)" % ISSUE, vf)
        if m:
            seen.add(m.group(1))
    return seen


def drain(limit=None, dry=False, say=print):
    """Copy every not-yet-recorded SECOND-EYE comment into the ledger. -> dict"""
    try:
        rows = _handoff._gh("repos/%s/issues/%d/comments?per_page=100" % (_handoff.REPO, ISSUE))
    except Exception as exc:
        # ⚠ AN UNREACHABLE GITHUB IS UNKNOWN, NOT AN EMPTY LANE. Returning a clean zero here would
        # let a dead reader read exactly like a quiet issue. [[feedback-silence-is-not-evidence]]
        say("⚠ #%d could not be READ (%s: %s) — that is UNKNOWN, not 'no looks to drain'."
            % (ISSUE, type(exc).__name__, str(exc)[:120]))
        return {"ok": False, "why": "github unreachable", "read": None,
                "looks": None, "new": None, "recorded": 0, "skipped": None}

    seen = already_recorded()
    looks, fresh, no_version = [], [], []
    for c in rows:
        got = parse_comment(c.get("body"))
        if not got:
            continue
        got["_id"] = str(c.get("id"))
        got["_at"] = c.get("created_at")
        looks.append(got)
        # ⚠⚠ A LOOK THAT SAYS `version: unknown` IS HONEST AND MUST NOT BECOME A VERSION.
        # The seat writes that when the commit carries no version stamp (measured: one such commit
        # touched only CLAUDE.md and TASKS.md). norm_version("unknown") is "", so record() would
        # fall back to storing the literal string — minting a version called "unknown" that every
        # such look then piles into. agreement("unknown") would report three looks at one version
        # and could read as a corroborated one. It is skipped, and it is COUNTED, because a silent
        # skip reads as "there were none". [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
        if _led.norm_version(got.get("version")) == "":
            no_version.append(got)
            continue
        if got["_id"] not in seen:
            fresh.append(got)

    say("#%d — %d comment(s) read · %d are SECOND-EYE looks · %d already in the ledger · %d new"
        % (ISSUE, len(rows), len(looks), len(looks) - len(fresh) - len(no_version), len(fresh)))
    if no_version:
        say("  ⓘ %d look(s) name NO version (the seat wrote `version: unknown` because the commit "
            "carries no stamp). NOT filed — they cannot answer 'was vNNNN looked at', and a "
            "version called 'unknown' would collect them all. Their shas: %s"
            % (len(no_version), ", ".join((g.get("sha") or "?")[:8] for g in no_version[:6])))
    if not looks and rows:
        say("  ⚠ %d comment(s) and NOT ONE parsed as a look. That is a parser/format mismatch, "
            "not an empty lane — do not read it as 'nothing to drain'." % len(rows))

    if limit:
        fresh = fresh[:limit]
    written = 0
    for got in fresh:
        ver, sha = got.get("version"), got.get("sha")
        verdict = (got.get("verdict") or "").strip().lower() or "cannot-tell"
        n = _chars(got.get("chars"))
        # ⚠⚠ v3457 — REACH MUST BE A DICT OR THE LEDGER THROWS IT AWAY SILENTLY.
        # record() stores it as `dict(reach) if isinstance(reach, dict) else None`, and the first
        # cut of this drain passed the seat's reach LINE as a string. MEASURED: reach was null on
        # 39 of 39 drained rows. The whole argument of #180 is that a ledger row PRESERVES reach
        # where a GitHub comment loses it — and the drain built to close that gap was losing it.
        # Found by the cross-family eye on the SHIPPED v3454 bytes. [[the-unjoined-end]]
        _reach_line = got.get("reach")
        notshown = got.get("not shown")
        reach = {}
        if _reach_line:
            reach["line"] = _reach_line
            for _part in str(_reach_line).split(","):
                _part = _part.strip()
                if _part.lower().startswith("absent:"):
                    reach["absent"] = _part.split(":", 1)[1].strip()
                elif "/" in _part or _part.endswith(".md"):
                    reach.setdefault("files", []).append(_part)
        if notshown:
            # ⚠ ITS OWN KEY, not concatenated onto the reach line. "what was NOT shown" is the half
            # that tells a consumer the look was partial, and burying it inside a sentence makes it
            # unaskable. [[heart-first]] §6
            reach["notShown"] = notshown
        reach = reach or None
        if dry:
            say("  [dry] %s %s  %s  %s  chars=%s" % (ver, (sha or "")[:8], verdict,
                                                     got.get("model"), n))
            continue
        _led.record(
            version=ver,
            model=got.get("model") or "",
            verdict=verdict,
            findings=_findings_list(got.get("findings")),
            sha=sha,
            reached=True,
            # ⚠ the seat's OWN measured payload size. None stays None — an unparseable `chars:`
            # must not become a confident 0.
            # ⚠ `fences: 0` — THE DRAIN SENDS NO CODE FENCE. The seat measured its own payload
            # and reported a char count; claiming "1 fence" asserts a transmission shape this path
            # never uses, and that field exists precisely to stop a thin look being filed as a
            # thorough one. chars is measured; fences is not ours to claim.
            sent=({"chars": n, "fences": 0, "unsent": []} if n is not None else None),
            reach=reach,
            answer_head=got.get("findings") or "",
            asked="posted by the #%d seat; this row is a COPY of what it said, not a re-judgement"
                  % ISSUE,
            verdict_from="gh#%d comment %s" % (ISSUE, got["_id"]),
        )
        written += 1
        say("  + %s  %s  %s  (%s, chars=%s)  <- comment %s"
            % (ver, (sha or "no-sha")[:8], verdict, got.get("model"), n, got["_id"]))

    if not fresh:
        say("  nothing new to record. That is a measured zero — %d look(s) were read and all were "
            "already filed." % len(looks))
    return {"ok": True, "read": len(rows), "looks": len(looks),
            "new": len(fresh), "recorded": written,
            "noVersion": len(no_version),
            "skipped": len(looks) - len(fresh) - len(no_version), "why": ""}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    dry = "--dry" in argv
    lim = None
    if "--limit" in argv:
        try:
            lim = int(argv[argv.index("--limit") + 1])
        except (IndexError, ValueError):
            lim = None
    out = drain(limit=lim, dry=dry)
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
