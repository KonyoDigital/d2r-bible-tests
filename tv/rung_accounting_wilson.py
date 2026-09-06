# -*- coding: utf-8 -*-
"""A2 — `reel.route`: can the rung accounting refuse when it cannot establish where a reel is?

`reel.route` is declared as the authority that "decides where each reel is, and therefore what it
is owed". Two modules answer that between them: `reel_story` names the ladder and places each reel
on it, and `one_funnel` reports how each rung's passage is observed. This harness attacks the
SECOND half — the reporting — because v2725 found it saying something false.

WHAT v2725 FOUND, AND WHY IT NEEDED A HARNESS RATHER THAN A FIX
---------------------------------------------------------------
`one_funnel` printed, for four of six rungs, "no store records this rung, so passing it leaves no
trace". Measured on his shelf: `reel_retention.plan()` answers for all 40 reels, `reel_story` gives
all 40 a known stage, and reel_story's own docstring names the decider for every one of those four.
The rungs were never traceless — they were UNCACHED, and the module reported the second as the
first. That is [[unknown-stays-unknown]] inside a module whose comments cite it five times.

A single fix would have left the class alive. These are the states in which the accounting must
still refuse rather than answer, each a DISTINCT idea about how "we cannot establish this" could be
laundered into a number.

⚠⚠ THIS HARNESS BANKS AGAINST `reel.route` AND NOTHING ELSE. Every attack below is against the
question that lock names — can we establish where a reel is on the ladder, and is that answer
honest about its own reach. Filing them under `printer.stream` (which walks reels) or `prune.arm`
(which deletes them) would move a bigger counter and prove nothing about either, the exact cheat
`_hardening_gap` names by name. [[join-gate-heart]]

⚠ IT IS PURE. Every attack builds dictionaries in memory or swaps a module attribute back on the
way out. It writes no store, deletes nothing, and arms nothing; `tv/test_derived_rungs_are_not_
traceless.py` holds the laws, and this file holds the evidence they generate.

⚠ EVERY ATTACK IS A DISTINCT IDEA, NOT A PARAMETER SWEEP. `wilsonByAttack` exists because 80 of
printer.stream's 83 were two functions applied to 40 reels each. Ten near-identical cover maps
would be ONE idea. These are ten different ways to be wrong about the same question.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import one_funnel as OF  # noqa: E402


def _cover_attacks():
    """States the OBSERVABILITY verdict must read correctly. -> list of (name, cover, want, why)"""
    return [
        ("nothing was examined at all", {}, "UNKNOWN",
         "AN EMPTY MAP IS NOT A CLEAN BILL. This shipped as OBSERVED — `seen == total` holds at "
         "0 == 0 and it printed 'every one of the 0 rung(s) can be established'. Found by writing "
         "this attack, not by re-reading the code. [[zero-needs-a-denominator]]"),

        ("one rung's store could not be read",
         {"a": {"store": "x.json", "covered": 3}, "b": {"store": "y.json", "covered": None}},
         "UNKNOWN",
         "UNKNOWN PROPAGATES. A rung nobody could read is not a rung measured as absent, and "
         "letting it drag a fraction turns a reading failure into a finding about his pipeline"),

        ("one rung has a store holding nothing",
         {"a": {"store": "x.json", "covered": 3}, "b": {"store": "y.json", "covered": 0}},
         "PARTIAL",
         "MEASURED-EMPTY IS A REAL ANSWER, and the opposite of the one above. A store that opened "
         "and held no row for any reel is a genuine gap, not an unknown — collapsing these two is "
         "the distinction REG-559 was written for"),

        ("a rung with neither store nor decider",
         {"a": {"store": "x.json", "covered": 3}, "b": {"store": None, "derivedBy": None}},
         "PARTIAL",
         "GENUINELY TRACELESS IS ALLOWED TO EXIST. If this reported OBSERVED the module would be "
         "unable to say the thing it was built to say, and the v2725 fix would have swung from "
         "under-reporting to over-reporting"),

        ("a decider that answered for nobody",
         {"a": {"store": "x.json", "covered": 3},
          "b": {"store": None, "derivedBy": "m.f()", "decided": None}},
         "UNKNOWN",
         "A DECIDER THAT COULD NOT RUN IS NOT A DECIDER THAT FOUND NOTHING. The store path learned "
         "this as REG-559; the derived path must not relearn it from scratch"),

        ("a decider that answered for everyone",
         {"a": {"store": "x.json", "covered": 3},
          "b": {"store": None, "derivedBy": "m.f()", "decided": 40}},
         "OBSERVED",
         "THE SUCCESS PATH MUST ALSO WORK. A verdict that only ever refuses proves nothing about "
         "judgement — this is the state his shelf is actually in, and it has to be reachable"),
    ]


def _decider_attacks():
    """States `_decided_count()` must call UNKNOWN. -> list of (name, patch, why)"""
    return [
        ("the shelf raises", "raise",
         "an exception is not a count. Returning 0 here would claim every reel is undecided, the "
         "strongest possible finding, manufactured from a failure to look"),
        ("the shelf answers with no reels", "empty",
         "no reels is UNKNOWN, not 'nothing was decided' — an empty shelf and an unreadable one "
         "produce the same empty list, and they are opposite facts"),
        ("the shelf answers something that is not a mapping", "garbage",
         "a list, a string or None from story() must not be indexed into a confident zero"),
    ]


def run():
    """-> (attempts, correct, rows). Pure; touches no store."""
    rows, ok = [], 0

    for name, cover, want, why in _cover_attacks():
        try:
            got = OF._observability(cover).get("state")
        except Exception as e:
            got = "CRASHED(%s)" % str(e)[:40]
        correct = (got == want)
        ok += 1 if correct else 0
        rows.append({"attack": name, "expected": want, "got": got, "correct": correct, "why": why})

    import reel_story as RS
    orig = RS.story
    for name, patch, why in _decider_attacks():
        try:
            if patch == "raise":
                RS.story = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("shelf offline"))
            elif patch == "empty":
                RS.story = lambda *a, **k: {"reels": []}
            else:
                RS.story = lambda *a, **k: ["not", "a", "mapping"]
            dec, tot, _w = OF._decided_count()
            got = "UNKNOWN" if dec is None and tot is None else "COUNT(%r/%r)" % (dec, tot)
        except Exception as e:
            got = "CRASHED(%s)" % str(e)[:40]
        finally:
            RS.story = orig
        correct = (got == "UNKNOWN")
        ok += 1 if correct else 0
        rows.append({"attack": name, "expected": "UNKNOWN", "got": got,
                     "correct": correct, "why": why})

    # ── the laundering attack, and it is the one that matters ────────────────────────────────
    # A derived rung proves the PRESENT. `passage` measures recorded HISTORY. If discovering that
    # four rungs are observable is allowed to raise `passage`, the number that says "his pipeline
    # keeps no history" quietly becomes the number that says "his pipeline is fine".
    try:
        f = OF.funnel()
        leaked = sorted(set(f.get("datedRungs") or []) & set(OF.DERIVED_SOURCES))
        borrowed = sorted(r for r in OF.DERIVED_SOURCES
                          if (f.get("waypoints") or {}).get(r, {}).get("covered") is not None)
        got = "clean" if not leaked and not borrowed else "leaked=%s borrowed=%s" % (leaked, borrowed)
    except Exception as e:
        got = "CRASHED(%s)" % str(e)[:40]
    correct = (got == "clean")
    ok += 1 if correct else 0
    rows.append({"attack": "a live decider counted as a dated waypoint", "expected": "clean",
                 "got": got, "correct": correct,
                 "why": "THE LOAD-BEARING ONE. Two readings of the pipeline exist precisely so a "
                        "true discovery cannot launder a strict verdict; merging them is how a "
                        "definition moves under a reader with nobody told"})
    return len(rows), ok, rows


def live():
    """Walk HIS REAL SHELF and check the rung accounting is coherent on it. -> (n, ok, rows, why)

    A different KIND of witness from `run()`: that one hands dictionaries to pure functions and
    would pass on a machine with no reels. This one can only answer where his data is.

    ⚠ NO REELS MEANS UNKNOWN, NOT A PASS. On CI there is no shelf, and returning "0 of 0 correct"
    would bank a clean-looking result over nothing examined — the [[zero-needs-a-denominator]]
    shape, in the one place where it would quietly move a lock toward opening.
    """
    try:
        import reel_story as RS
        st = RS.story()
    except Exception as e:
        return 0, 0, [], "reel_story would not answer (%s)" % str(e)[:70]
    reels = (st.get("reels") or []) if isinstance(st, dict) else []
    if not reels:
        return 0, 0, [], ("no reel is on this shelf, so nothing about his routing can be "
                          "established here — UNKNOWN, not a clean run")

    rows, ok = [], 0

    # 1. every reel the shelf holds gets a KNOWN rung. A reel nobody can place is a reel nothing
    #    downstream can decide about, and reel_story refuses rather than guessing on an unknown tag.
    unplaced = [r.get("reel") for r in reels
                if isinstance(r, dict) and not (r.get("stageKnown") and r.get("stage"))]
    rows.append({"check": "every reel on the shelf is placed on a rung",
                 "measured": "%d of %d placed" % (len(reels) - len(unplaced), len(reels)),
                 "correct": not unplaced,
                 "why": "an unplaced reel cannot be routed, swept or released; "
                        "%s" % ("none" if not unplaced else "unplaced: %s" % unplaced[:3])})
    ok += 1 if not unplaced else 0

    # 2. the funnel answers about that same shelf, and its two readings stay separate. `passage`
    #    counts DATED rungs; `observability` counts ESTABLISHABLE ones. Live is where they could
    #    silently merge, because here both have real values instead of hand-built ones.
    try:
        import one_funnel as OF
        f = OF.funnel()
        obs = f.get("observability") or {}
        dated = set(f.get("datedRungs") or [])
        leaked = sorted(dated & set(OF.DERIVED_SOURCES))
        rows.append({"check": "no live decider is counted as a dated waypoint",
                     "measured": "datedRungs=%s observability=%s" % (sorted(dated), obs.get("state")),
                     "correct": not leaked,
                     "why": "on real data a derived rung must still prove only the PRESENT; "
                            "%s" % ("clean" if not leaked else "leaked: %s" % leaked)})
        ok += 1 if not leaked else 0

        # 3. the funnel walked the same shelf reel_story reported. Two readers disagreeing about
        #    HOW MANY REELS EXIST would make every ratio above meaningless, and it is the kind of
        #    drift that only shows on real data. [[feedback-contradiction-is-the-finding]]
        same = (f.get("walked") == len(reels))
        rows.append({"check": "the funnel and the shelf counted the same reels",
                     "measured": "funnel walked %s, shelf holds %d" % (f.get("walked"), len(reels)),
                     "correct": same,
                     "why": "two readers of one shelf disagreeing about its size makes every "
                            "per-rung fraction untrustworthy"})
        ok += 1 if same else 0
    except Exception as e:
        rows.append({"check": "one_funnel answers on his shelf", "measured": "raised",
                     "correct": False, "why": str(e)[:90]})

    return len(rows), ok, rows, ""


def main(argv):
    n, ok, rows = run()
    show = "-v" in argv or "--verbose" in argv
    for r in rows:
        if show or not r["correct"]:
            print("  %-46s expected %-9s got %-9s %s"
                  % (r["attack"][:46], r["expected"], r["got"], "OK" if r["correct"] else "<<< WRONG"))
    print("\n  reel.route rung accounting: %d/%d distinct attack(s) answered correctly" % (ok, n))
    if "--bank" in argv:
        if ok != n:
            print("  REFUSING TO BANK: %d attack(s) were answered wrongly. Evidence is banked only "
                  "from a CLEAN run — a harness that banks its own failures is measuring nothing."
                  % (n - ok))
            return 1
        import self_arming as SA
        # ⚠ THE LIVE PASS IS BANKED SEPARATELY AND AS attacks=1. Three coherence checks over forty
        # reels is ONE IDEA about his shelf, not forty; `wilsonByAttack` exists to refuse exactly
        # that inflation. It is banked ONLY if it actually ran — an empty shelf returns n=0 and is
        # skipped with its reason printed, never banked as a clean zero.
        ln, lok, lrows, lwhy = live()
        if ln and lok == ln:
            SA.bank("reel.route", "live", "rung_accounting_live", n=ln, k=lok, attacks=1,
                    note="v2727 — three coherence checks over his real shelf: every reel placed on "
                         "a rung, no live decider counted as dated, and the funnel and the shelf "
                         "agreeing on how many reels exist",
                    ref="tv/rung_accounting_wilson.py")
            print("  live: %d/%d coherence check(s) on his real shelf — banked as live" % (lok, ln))
        else:
            print("  live: NOT BANKED — %s" % (lwhy or "%d of %d check(s) failed" % (ln - lok, ln)))
        row = SA.bank("reel.route", "sabotage", "rung_accounting_wilson", n=n, k=ok, attacks=n,
                      note="v2725 — ten distinct attacks on whether the rung accounting can refuse "
                           "when it cannot establish where a reel is",
                      ref="tv/test_derived_rungs_are_not_traceless.py")
        print("  banked: %s" % row)
    return 0 if ok == n else 1


if __name__ == "__main__":
    # ⚠ THIS FILE PRINTS NON-ASCII AND IS AN ENTRY POINT, so stdout has to be made encoding-safe
    # or it crashes WHILE REPORTING on a non-UTF-8 console and a clean tree exits non-zero.
    # test_control's `test_every_cli_that_prints_non_ascii_is_encoding_safe` refused the push over
    # exactly this — the gate working, on the first run of a new file.
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
