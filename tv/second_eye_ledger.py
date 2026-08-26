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
_FAMILY = (
    ("grok", "xai"),
    ("gpt", "openai"),
    ("gemini", "google"),
    ("llama", "meta"),
    ("mistral", "mistral"),
    ("claude", "anthropic"),
)

# Who AUTHORED the ships this ledger guards. A pass from this family is not a second eye.
AUTHOR_FAMILY = "anthropic"


def family_of(model):
    """anthropic / xai / openai / ... or None when the id says nothing recognisable.

    None is deliberately NOT treated as "some other family" — an unrecognised model cannot be
    shown to be a different one, and [[unknown-stays-unknown]] applies to provenance too.
    """
    m = str(model or "").lower()
    for needle, fam in _FAMILY:
        if needle in m:
            return fam
    return None


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
                    out.append(json.loads(ln))
                except Exception:
                    continue          # one bad line must not blind the whole ledger
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
        "version": str(version or "").strip(),
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


def looked_at(version, path=None):
    """The rows that COUNT as a second-eye look at `version`, newest first.

    A row counts only when all three hold: the seat was reached, the family is a recognised one,
    and that family is not the one that wrote the code. Anything else is kept in the ledger and
    excluded here — recorded, but never mistaken for agreement.
    """
    v = str(version or "").strip()
    hits = [r for r in _rows(path)
            if r.get("version") == v
            and r.get("reached")
            and r.get("family")
            and r.get("family") != AUTHOR_FAMILY]
    return sorted(hits, key=lambda r: -(r.get("ts") or 0))


def owes_a_look(version, path=None):
    """True when `version` shipped and no different family has looked at it."""
    return not looked_at(version, path)


def audit(path=None):
    """Every version mentioned in the ledger, and whether it was really seen. For the report."""
    seen = {}
    for r in _rows(path):
        v = r.get("version") or "?"
        s = seen.setdefault(v, {"version": v, "attempts": 0, "empty": 0, "author": 0, "looks": 0})
        s["attempts"] += 1
        if not r.get("reached"):
            s["empty"] += 1
        elif r.get("family") == AUTHOR_FAMILY:
            s["author"] += 1
        elif r.get("family"):
            s["looks"] += 1
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

    if "--check" in argv:
        i = argv.index("--check")
        want = argv[i + 1] if len(argv) > i + 1 else current_version()
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
        print("second eye: %s was looked at by %s (%s) — %s"
              % (want, r.get("model"), r.get("family"), r.get("verdict")))
        return 0

    print(__doc__.strip().split("\n")[0])
    print("usage: second_eye_ledger.py --audit | --check [vNNNN]")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
