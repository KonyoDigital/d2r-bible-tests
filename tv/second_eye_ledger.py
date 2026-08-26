#!/usr/bin/env python3
"""Which shipped versions were actually LOOKED AT by a different model family, and which were not.

WHY THIS EXISTS, and it is not a nice-to-have. Konyo's standing order since 2026-07-15 is one
Grok pass after every ship — "its like ping pong. you fix and ship and then ask it what can be
perfected". On 2026-08-26 I shipped v2137, v2138, v2139, v2140, v2141 and v2142 and ran ZERO. He
asked whether the second eye was running; the honest answer was no, and nothing anywhere had
noticed, because nothing anywhere was keeping score. A standing order that lives only in memory is
a standing order that lapses silently.

So it is written down. This module is the score, and hooks/pre-push reads it.

WHAT MAKES THIS DIFFERENT FROM A CHECKBOX — every one of these is a scar this repo already paid for:

  · AN UNREACHABLE EYE IS AN EMPTY SEAT, NEVER AGREEMENT. `reached=False` is recorded, kept, and
    does NOT satisfy the gate. A dead CLI must never read as "it looked and was happy" — that is
    the exact defect that let a Grok-hardwired third eye sit permanently empty on every machine but
    his while every lamp stayed green.
  · A SKIP IS NOT A PASS. No entry at all for a version is a REFUSAL, not a shrug.
  · A COURIER IS NOT A REVIEW. The entry carries the model id, the images actually handed over, and
    the head of the raw answer. A same-family agent writing plausible strings must never be
    mistakable for a cross-family look, so `family` is derived from the model id, not asserted.
  · IT MUST BE ABLE TO GO RED. tests/../test_control.py drives both directions; a gate never seen
    red is measuring nothing.

The record itself is a runtime record of DECISIONS, like .console_scars.json and
reel_tombstones.json, so it lives untracked beside them rather than in git.
"""

import io
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# untracked, like the other runtime decision records (see .gitignore)
LEDGER_PATH = os.environ.get("TV_SECOND_EYE_LEDGER") or os.path.join(HERE, ".second_eye.jsonl")

# The families that count as a SECOND eye for work authored by Claude. Derived from the model id
# rather than trusted from a caller, because "which family looked at this" is the whole question.
# ⚠ v2145 — TOO NARROW AS WELL AS TOO WIDE. The second eye measured family_of("o3") and
# family_of("mixtral") as None, so two real other-family looks would have been discarded. Matched
# as whole TOKENS of the model id, and the id must LEAD with one (see family_of).
_FAMILY = (
    ("grok", "xai"),
    ("gpt", "openai"), ("o3", "openai"), ("o4", "openai"),
    ("gemini", "google"),
    ("llama", "meta"),
    ("mistral", "mistral"), ("mixtral", "mistral"),
    ("deepseek", "deepseek"),
    ("qwen", "qwen"),
    ("command", "cohere"),
    ("claude", "anthropic"),
)

# Who AUTHORED the ships this ledger guards. A pass from this family is not a second eye.
AUTHOR_FAMILY = "anthropic"


def family_of(model):
    """anthropic / xai / openai / ... or None when the id does not say ONE recognisable family.

    None is deliberately NOT "some other family" — an unrecognised model cannot be SHOWN to be a
    different one, and [[unknown-stays-unknown]] applies to provenance too.

    ⚠ v2143.1 — AN ADVERSARIAL PASS LAUNDERED CLAUDE AS XAI THROUGH THIS FUNCTION. The first cut
    walked an ordered list of substrings and returned the first hit, with "claude" scanned LAST.
    So `grok-mcp/claude-opus-5` matched "grok" and came back "xai" — the author's own model
    satisfying a gate whose entire purpose is that the author's family does not count. Order can
    never be load-bearing here. Every family is now matched, and:
      · if MORE THAN ONE matches, the id is AMBIGUOUS and returns None. An id naming two families
        cannot be shown to be either one, so it must not buy a pass.
      · a single match returns that family, whichever it is.
    """
    import re as _re
    m = str(model or "").lower()
    toks = [t for t in _re.split(r"[^a-z0-9]+", m) if t]
    if not toks:
        return None
    hits = sorted({fam for needle, fam in _FAMILY if needle in toks})
    if len(hits) != 1:
        return None                       # zero = unrecognised, two+ = ambiguous. Both are UNKNOWN.
    # ⚠ v2145 — AND THE FIRST TOKEN MUST BE THE FAMILY. A substring needle said
    # family_of("not-grok") == "xai": the id says it is NOT grok and the gate read it as grok. The
    # id must LEAD with the family, so "grok-4" qualifies and "not-grok", "fake-grok" and
    # "grok-emulator-by-someone-else" do not. Combined with the ambiguity rule above,
    # "grok-mcp/claude-opus-5" still returns None because two families appear.
    lead = {needle: fam for needle, fam in _FAMILY}.get(toks[0])
    if lead != hits[0]:
        return None
    return hits[0]


def norm_version(v):
    """v2143 — ONE canonical spelling. The writer stored whatever it was handed and the reader
    normalised, so a real cross-family look recorded as "2142" was invisible to `--check v2142`
    while `--audit` cheerfully listed it as OK — two commands, opposite verdicts, and the refusal
    message stating a falsehood. Both ends call this now.
    """
    t = str(v or "").strip().lower()
    if not t:
        return ""
    if t.startswith("v"):
        t = t[1:]
    return ("v" + t) if t.isdigit() else ""


def current_version(here=None):
    """The version the four stamps agree on, read from the JSON one (the only machine-readable one)."""
    p = os.path.join(here or HERE, "WINDOWS_SHIP.json")
    try:
        with io.open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        # "ver" is the real key in WINDOWS_SHIP.json — measured, not guessed. The others are kept
        # as fallbacks, but an unrecognised shape returns None and the CLI treats that as UNKNOWN
        # rather than as a pass.
        for k in ("ver", "version", "ship", "build", "v"):
            v = d.get(k)
            if isinstance(v, str) and re.match(r"^v?\d+$", v.strip()):
                return v.strip() if v.strip().startswith("v") else "v" + v.strip()
    except Exception:
        pass
    return None


def _rows(path=None):
    out = []
    try:
        with io.open(path or LEDGER_PATH, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    row = json.loads(ln)
                except Exception:
                    continue          # one bad line must not blind the whole ledger
                if isinstance(row, dict):
                    out.append(row)   # ...and a line that PARSES but is not an object is one of
                                      # those bad lines. It used to reach every consumer and
                                      # traceback --audit, which is the recovery command the
                                      # refusal message tells him to run.
    except Exception:
        return []
    return out


def record(version, model, verdict, findings=None, images=None, asked=None,
           answer_head=None, reached=True, path=None):
    """Append one look. Returns the row written.

    `verdict` is what the OTHER family concluded: "clean" | "findings" | "cannot-tell".
    `reached` False means the seat was empty — the row is still written, on purpose, so a run of
    failures is visible instead of looking like nobody tried.
    """
    row = {
        "version": norm_version(version) or str(version or "").strip(),
        "ts": int(time.time() * 1000),
        "model": str(model or ""),
        "family": family_of(model),
        "reached": bool(reached),
        "verdict": str(verdict or ""),
        "findings": list(findings or []),
        "images": [os.path.basename(str(i)) for i in (images or [])],
        "asked": (str(asked or "")[:400]) or None,
        # the head of the RAW answer, so a plausible-sounding summary cannot stand in for a look
        "answerHead": (str(answer_head or "")[:600]) or None,
    }
    p = path or LEDGER_PATH
    try:
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    except Exception:
        pass
    with io.open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _has_evidence(row):
    """Is this row bound to anything a person could go and check?

    Any ONE of: the head of the raw answer, a named image, or a finding the other family made.
    Empty strings do not count in any of them — measured: images:[""] satisfied the first cut.
    """
    if str(row.get("answerHead") or "").strip():
        return True
    if any(str(i or "").strip() for i in (row.get("images") or [])):
        return True
    if any(str(f or "").strip() for f in (row.get("findings") or [])):
        return True
    return False


def looked_at(version, path=None):
    """The rows that COUNT as a second-eye look at `version`, newest first.

    A row counts only when all three hold: the seat was reached, the family is a recognised one,
    and that family is not the one that wrote the code. Anything else is kept in the ledger and
    excluded here — recorded, but never mistaken for agreement.
    """
    v = norm_version(version)
    if not v:
        return []                          # a version we cannot name cannot be shown to be looked at
    out = []
    for r in _rows(path):
        if not isinstance(r, dict):
            continue                       # a line that parses but is not an object must not crash
        if norm_version(r.get("version")) != v:
            continue
        # ⚠ v2143.1 — RE-DERIVED, NOT TRUSTED. The first cut read the row's own `family` field, so
        # a hand-written line claiming family:"xai" satisfied the gate — the exact forgery this
        # ledger was introduced to make impossible, and I had told him it was. The stored field is
        # now evidence for a human reading the file; the DECISION is made from the model id alone.
        fam = family_of(r.get("model"))
        if not fam or fam == AUTHOR_FAMILY:
            continue
        # ⚠ strict True, not truthiness: the STRING "false" is truthy, and an adversarial pass used
        # exactly that to count an empty seat as a reached one.
        if r.get("reached") is not True:
            continue
        # ⚠ a row must be bound to something. A hollow {version, model, reached} line proved a
        # look had happened while carrying no trace of one.
        #
        # v2145 — TWO CORRECTIONS FROM THE SECOND EYE, and the first is the serious one:
        #   · FINDINGS ARE EVIDENCE. record(..., findings=[...]) — the natural way to write down
        #     what the other family said — produced a row this refused, because only answerHead and
        #     images counted. So the honest path was: do the look, call the writer, and still be
        #     blocked. A gate that fails the correct behaviour trains the bypass.
        #   · images:[""] used to pass. An empty string in a list is not an image.
        if not _has_evidence(r):
            continue
        out.append(r)
    return sorted(out, key=lambda r: -(r.get("ts") or 0))


def owes_a_look(version, path=None):
    """True when `version` shipped and no different family has looked at it."""
    return not looked_at(version, path)


def audit(path=None):
    """Every version mentioned in the ledger, and whether it was really seen.

    ⚠ v2145 — THIS USED THE RULES `looked_at` HAD ALREADY ABANDONED, and the second eye measured
    both directions of the resulting contradiction: a forged row (model:"", family:"xai") that
    --check REFUSED was listed here as "OK looks=1", and a real look recorded as version "9999"
    that --check ACCEPTED was listed here as OWED. The test named
    test_check_and_audit_cannot_disagree_about_a_bare_number never called audit(), so the
    disagreement it claimed to close was still there, both ways.

    audit() is also the recovery command the refusal message tells him to run, which makes a
    contradiction here worse than one anywhere else: it is the screen he reads when he is already
    blocked. One rule, asked from both. [[feedback-contradiction-is-the-finding]]
    """
    seen = {}
    for r in _rows(path):
        v = norm_version(r.get("version")) or (str(r.get("version") or "?").strip() or "?")
        st = seen.setdefault(v, {"version": v, "attempts": 0, "empty": 0, "author": 0, "looks": 0})
        st["attempts"] += 1
        fam = family_of(r.get("model"))          # re-derived, exactly as the verdict does it
        if r.get("reached") is not True:
            st["empty"] += 1
        elif fam == AUTHOR_FAMILY:
            st["author"] += 1
        elif fam and _has_evidence(r):
            st["looks"] += 1
        else:
            st["empty"] += 1                     # unidentifiable, or bound to nothing
    return sorted(seen.values(), key=lambda s: s["version"])


def _encoding_safe():
    """His suite caught this one on the first run: a CLI that prints non-ASCII and never makes
    stdout encoding-safe CRASHES WHILE REPORTING on a non-UTF-8 console, and a clean tree then
    exits non-zero for a reason that has nothing to do with the thing being checked. He runs a
    Windows machine, so that console is real. Same idiom as js_syntax_gate.py:439-443.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main(argv):
    _encoding_safe()
    argv = list(argv or [])

    # ⚠ v2143.1 — THE GATE MUST NOT BE REDIRECTABLE BY THE PUSHER'S ENVIRONMENT. LEDGER_PATH honours
    # TV_SECOND_EYE_LEDGER so tests can point it at a fixture, and an adversarial pass showed that a
    # one-word prefix on the push command therefore disarms the whole thing with no --no-verify and
    # no trace. `--gate` (which is what hooks/pre-push passes) pins the canonical path and ignores
    # the variable entirely. Tests keep the seam by calling the functions with an explicit `path=`.
    global LEDGER_PATH
    if "--gate" in argv:
        LEDGER_PATH = os.path.join(HERE, ".second_eye.jsonl")

    # ⚠ and --check must not be swallowed by --audit appearing anywhere in argv, which printed
    # "OWES A LOOK" and then exited 0 — a refusal that reads as a pass.
    if "--check" in argv:
        return _cmd_check(argv)
    if "--audit" in argv:
        rows = audit()
        if not rows:
            print("second eye: the ledger is empty — nothing has ever been looked at.")
            return 0
        for s in rows:
            mark = "OK " if s["looks"] else "OWED"
            print("  %-6s %-8s looks=%d  empty-seats=%d  author-only=%d"
                  % (mark, s["version"], s["looks"], s["empty"], s["author"]))
        return 0

    print(__doc__.strip().split("\n")[0])
    print("usage: second_eye_ledger.py --audit | --check [vNNNN] [--gate]")
    return 0


def _cmd_check(argv):
    if True:
        i = argv.index("--check")
        want = argv[i + 1] if len(argv) > i + 1 else current_version()
        # ⚠ the hook interpolates a value it read off disk straight into argv. An adversarial pass
        # set it to "--audit" and turned the check into a printed pass. Anything that is not a
        # version is UNKNOWN, and unknown exits non-zero.
        if want is not None and not norm_version(want):
            print("second eye: %r is not a version — refusing rather than guessing." % (want,))
            return 2
        if not want:
            print("second eye: cannot tell which version to check — no version given and "
                  "WINDOWS_SHIP.json did not yield one.")
            return 2                      # unknown is not a pass
        if owes_a_look(want):
            rows = [r for r in _rows() if r.get("version") == want]
            why = "nothing was ever recorded for it"
            if rows:
                empt = sum(1 for r in rows if not r.get("reached"))
                auth = sum(1 for r in rows if r.get("reached") and r.get("family") == AUTHOR_FAMILY)
                bits = []
                if empt:
                    bits.append("%d empty seat(s) — the eye was not reached" % empt)
                if auth:
                    bits.append("%d look(s) from the family that WROTE it, which is not a second eye"
                                % auth)
                if bits:
                    why = "; ".join(bits)
            print("second eye: %s OWES A LOOK — %s" % (want, why))
            return 1
        r = looked_at(want)[0]
        # v2145 — PRINT WHAT THE VERDICT USED. This line read the STORED `family` field, which
        # looked_at had just refused to trust: a row {model:"grok-4", family:"anthropic"} counted
        # (re-derived xai) and then announced itself as "looked at by grok-4 (anthropic)". A
        # success message that contradicts the rule that produced it is how a reader learns to
        # stop believing the messages. [[label-outlived-referent]]
        print("second eye: %s was looked at by %s (%s) — %s"
              % (want, r.get("model"), family_of(r.get("model")),
                 r.get("verdict") or "no verdict recorded"))
        return 0



if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
