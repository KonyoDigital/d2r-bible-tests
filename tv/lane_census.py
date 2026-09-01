#!/usr/bin/env python3
"""THE LANE CENSUS — which background threads exist, which are supervised, and which are neither.

⚠ WHY THIS IS A FILE AND NOT A SCRIPT I RAN ONCE. On 2026-09-01 I answered A11 (gh #198) with an
ad-hoc classifier and it was WRONG TWICE, in the same way both times: it reported
`_kai_closer_loop`, `_engine_driver`, `_console_rescue_loop`, `_bridge_prober` and
`_console_beacon_loop` as one-shot workers. Every one of them carries `while True` — I read
control_app.py:8789 to settle it. Its body-boundary detection was cutting bodies short.

The tell was never in the output, it was in the COUNT: five functions named `_loop` classified as
one-shot is not a finding, it is a broken measurement. [[feedback-suspect-the-instrument]]

So this carries its own sabotage. `--prove` plants a known loop and a known one-shot in a fixture
and REQUIRES the classifier to sort both. A classifier that has never been seen get it wrong is a
classifier nobody should quote, and the previous one was quoted into a GitHub issue.

    python3 tv/lane_census.py            # the census
    python3 tv/lane_census.py --prove    # make it go RED for its own reason

WHY THE CENSUS MATTERS. THE HEART can only supervise what it knows exists. Measured today:
21 `threading.Thread(` call sites, 11 in the roster, 11 declaring a scope. The gap between STARTED
and REGISTERED is where a lane runs unwatched while every lamp stays green — and absence and health
look identical from outside. [[heart-first]] [[unknown-stays-unknown]]

⚠ AND NOT EVERY THREAD IS A LANE. A one-shot worker is a TASK; registering it would be a promise
about something that does not persist, which test_auto_scope's
`test_no_scope_describes_a_loop_that_does_not_run` already refuses for good reason. The census
therefore reports three buckets, and UNKNOWN is a legal answer in every one.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "control_app.py")
REPO = os.path.dirname(HERE)

#: a body is persistent if it can run again without being called again
_PERSISTENT = (
    re.compile(r"^\s*while\s+True\s*:", re.M),
    re.compile(r"^\s*while\s+not\s+[\w.]+\.is_set\(\)\s*:", re.M),
    re.compile(r"^\s*while\s+[\w.]+\s*:\s*$", re.M),
)


def _body(src, name):
    """The lines belonging to `def <name>` — from the def to the next line at or left of its own
    indent that actually STARTS something.

    ⚠ THIS IS THE PART THAT WAS WRONG. The first cut broke on the first line whose indent was <=
    the def's, which fires on a blank line, a dedented continuation, or a closing bracket, and cut
    the body off long before its `while True`. A body ends at the next STATEMENT at or left of the
    def's own indent — and blank lines and comments end nothing. [[source-reading-guard]]
    """
    m = re.search(r"^([ \t]*)def[ \t]+%s[ \t]*\(" % re.escape(name), src, re.M)
    if not m:
        return None
    lines = src.splitlines()
    start = src[:m.start()].count("\n")
    indent = len(m.group(1))
    end = len(lines)
    for i in range(start + 1, len(lines)):
        raw = lines[i]
        if not raw.strip():
            continue                       # blank lines end nothing
        if raw.lstrip().startswith("#"):
            continue                       # nor do comments
        if (len(raw) - len(raw.lstrip())) > indent:
            continue                       # still inside
        if re.match(r"[ \t]*[)\]}]", raw):
            continue                       # a dangling closer is not a new statement
        end = i
        break
    return "\n".join(lines[start:end])


def _code_only(s):
    # Strip docstrings and comments before asking what the code DOES.
    #
    # WITHOUT THIS, PROSE IS CODE. A cross-family review of this very function said so, and a
    # fixture reproduced it: a docstring carrying a `while True:` line as an EXAMPLE made the
    # function classify as a LOOP. The whole job of this module is telling a supervised lane from
    # a one-shot task, so a doc example would promote a task into a lane a watchdog then waits on
    # forever.
    #
    # This repo paid for the same class twice in one day: test_reachability went red because a
    # comment I wrote quoted the dead expression it was about. A guard that greps SOURCE has to be
    # told which bytes are source. [[source-reading-guard]] [[feedback-comments-vs-code]]
    s = re.sub(r'"' + r'""(.*?)"' + r'""', "", s, flags=re.S)
    s = re.sub(r"'''(.*?)'''", "", s, flags=re.S)
    s = re.sub(r"^[ \t]*#.*$", "", s, flags=re.M)
    return s


def classify(src, name):
    """-> 'LOOP' | 'TASK' | 'UNKNOWN'. UNKNOWN when the definition cannot be found, because
    'I could not look' and 'it runs once' are opposite facts."""
    b = _body(src, name)
    if b is None:
        return "UNKNOWN"
    b = _code_only(b)          # prose is not code — see _code_only
    return "LOOP" if any(p.search(b) for p in _PERSISTENT) else "TASK"


def census(src=None):
    src = src if src is not None else io.open(APP, encoding="utf-8").read()
    starts, seen = [], set()
    for m in re.finditer(r"threading\.Thread\((.{0,200}?)\)", src, re.S):
        blob = m.group(1).replace("\n", " ")
        t = re.search(r"target\s*=\s*([A-Za-z_][\w.]*)", blob)
        if not t:
            continue
        name = t.group(1).split(".")[-1]
        if name in seen:
            continue
        seen.add(name)
        starts.append(name)
    rost = re.search(r"roster\s*=\s*\[(.*?)\n    \]", src, re.S)
    registered = dict((fn, lane) for lane, fn in
                      re.findall(r'\("([a-z0-9-]+)",\s*([A-Za-z_]\w*)\)',
                                 rost.group(1) if rost else ""))
    out, expanded = [], False
    for n in sorted(starts):
        # ⚠ THE ROSTER IS STARTED THROUGH A GENERIC TARGET, AND A FIRST CUT COUNTED IT AS ONE
        # UNKNOWN THREAD. start_background_watchers loops the roster and calls
        # threading.Thread(target=fn), so the 11 supervised lanes hide behind a single local name
        # and the census reported "supervised 0" over a console that supervises eleven. A name is
        # not a thread; expand it to what it actually starts. [[the-unjoined-end]]
        if n not in registered and registered and classify(src, n) == "UNKNOWN":
            # ⚠ EXPAND ONCE. A first cut expanded for EVERY unresolvable target name and there are
            # two (`fn` and `serve_forever`), so the roster was listed twice and the console read
            # as supervising 22 lanes when it supervises 11. A count that double-counts is the same
            # class of lie as one that omits. [[feedback-suspect-the-instrument]]
            if not expanded:
                expanded = True
                for fn_, lane in sorted(registered.items(), key=lambda kv: kv[1]):
                    out.append({"fn": fn_, "kind": classify(src, fn_), "lane": lane,
                                "supervised": True, "via": n})
            else:
                out.append({"fn": n, "kind": "UNKNOWN", "lane": None,
                            "supervised": False, "via": None})
            continue
        out.append({"fn": n, "kind": classify(src, n),
                    "lane": registered.get(n), "supervised": n in registered, "via": None})
    return out


def prove():
    """Plant one of each in a fixture and require the classifier to sort them. Founding rule 2."""
    FIX = (
        "def planted_loop():\n"
        "    x = 1\n"
        "\n"
        "    # a comment, and a blank line above it, neither of which ends a body\n"
        "    while True:\n"
        "        x += 1\n"
        "\n"
        "def planted_task():\n"
        "    return 42\n"
        "\n"
        "def planted_gated(stop):\n"
        "    while not stop.is_set():\n"
        "        pass\n"
        "\n"
        # PROSE IS NOT CODE. A cross-family reviewer found this and a fixture reproduced it: a
        # docstring carrying a `while True:` EXAMPLE classified the function as a lane. Pinned
        # here so the strip can never quietly come out. [[source-reading-guard]]
        "def planted_doc_example():\n"
        '    \"\"\"Usage:\n'
        "\n"
        "        while True:\n"
        "            go()\n"
        '    \"\"\"\n'
        "    return 1\n"
        "\n"
        "def planted_commented_out():\n"
        "    # while True:\n"
        "    return 2\n"
    )
    want = {"planted_loop": "LOOP", "planted_task": "TASK",
            "planted_gated": "LOOP", "planted_absent": "UNKNOWN",
            "planted_doc_example": "TASK", "planted_commented_out": "TASK"}
    bad = 0
    print("PROVING THE CLASSIFIER — it must sort a known loop, a known task and an absent name.\n")
    for name, expect in sorted(want.items()):
        got = classify(FIX, name)
        ok = got == expect
        bad += 0 if ok else 1
        print("   %s %-16s want %-8s got %s" % ("🟢" if ok else "🔴", name, expect, got))
    # and the exact shape that fooled the last one: a real loop whose body has blank lines,
    # a docstring and dedented continuation lines before the while.
    real = io.open(APP, encoding="utf-8").read()
    for name in ("_kai_closer_loop", "_engine_driver", "_console_rescue_loop"):
        got = classify(real, name)
        ok = got == "LOOP"
        bad += 0 if ok else 1
        print("   %s %-16s want LOOP     got %s   (control_app.py — read by hand 2026-09-01)"
              % ("🟢" if ok else "🔴", name, got))
    print()
    if bad:
        print("🔴 %d case(s) wrong — this classifier may not be quoted." % bad)
        return 1
    print("🟢 every case sorted correctly, including the three it got wrong before.")
    return 0


def blueprint_disagreement():
    """Compare the CENSUS against BLUEPRINT.md — two maps of one fact, built by different methods.

    ⚠ THIS IS THE WHOLE OF A12 (gh #199) IN ONE FUNCTION, and the first time the two were put side
    by side they disagreed: the blueprint listed 14 lanes, the census found 18 loops, and
    _bridge_prober, _engine_driver, _mini_watchdog and _orphan_watch were in neither the roster nor
    the map. Nothing noticed, because nothing had ever compared them.

    Konyo: "blueprints.. reverse blueprints.. everything" — and the point is not two documents, it
    is that where they disagree, THAT is the finding. So this reports the difference in both
    directions rather than picking a winner. [[feedback-contradiction-is-the-finding]]

    -> (only_in_census, only_in_blueprint, agreed, why_unknown)
    `why_unknown` is not None when the comparison COULD NOT BE MADE, which must never render as
    agreement. [[unknown-stays-unknown]]
    """
    bp = os.path.join(REPO, "BLUEPRINT.md")
    if not os.path.isfile(bp):
        return set(), set(), set(), "BLUEPRINT.md is not on disk — regenerate it with blueprint.py"
    txt = io.open(bp, encoding="utf-8").read()
    if "## LANES" not in txt:
        return set(), set(), set(), "BLUEPRINT.md has no LANES section — its shape changed"
    sec = txt.split("## LANES")[1].split("\n##")[0]
    blue = set(re.findall(r"^\s{4}(_\w+)", sec, re.M))
    if not blue:
        return set(), set(), set(), "the LANES section parsed to nothing — the reader, not the map"
    loops = {r["fn"] for r in census() if r["kind"] == "LOOP"}
    return loops - blue, blue - loops, blue & loops, None


def main(argv):
    # ⚠ THIS PRINTS 🟢/🔴/⚠ AND WOULD CRASH WHILE REPORTING ON A NON-UTF-8 CONSOLE — which means a
    # CLEAN tree would exit non-zero and the gate would blame the code instead of the terminal.
    # test_every_cli_that_prints_non_ascii_is_encoding_safe caught this on the v2402 push, before it
    # ever ran on a machine that could hit it. A tool that dies while saying "everything is fine" is
    # worse than one that says nothing.
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    if "--prove" in argv:
        return prove()
    if "--vs-blueprint" in argv:
        only_c, only_b, agreed, why = blueprint_disagreement()
        if why:
            print("⚪ UNKNOWN — the two maps could not be compared: %s" % why)
            print("   That is not agreement. A comparison that did not happen must never read as one.")
            return 2
        print("census loops %d · blueprint lanes %d · agreed %d"
              % (len(agreed) + len(only_c), len(agreed) + len(only_b), len(agreed)))
        for n in sorted(only_c):
            print("   🔴 %-22s runs, and the BLUEPRINT does not list it" % n)
        for n in sorted(only_b):
            print("   🔴 %-22s is on the BLUEPRINT, and does not run" % n)
        if only_c or only_b:
            print("\nTwo maps of one fact disagree. That IS the finding — neither is assumed right.")
            return 1
        print("🟢 both maps name the same lanes.")
        return 0
    rows = census()
    loops = [r for r in rows if r["kind"] == "LOOP"]
    print("thread targets %d · supervised %d · unwatched loops %d"
          % (len(rows), sum(1 for r in rows if r["supervised"]),
             sum(1 for r in loops if not r["supervised"])))
    print()
    for r in rows:
        if r["lane"]:
            note = r["lane"] + (" (via %s)" % r["via"] if r.get("via") else "")
        elif r["kind"] == "LOOP":
            note = "*** UNWATCHED ***"
        elif r["kind"] == "UNKNOWN":
            # "I could not classify this" must never render as "it is only a task".
            note = "UNKNOWN — could not be classified, which is not the same as harmless"
        else:
            note = "(task — a roster entry would be a lie)"
        print("  %-24s %-8s %s" % (r["fn"], r["kind"], note))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
