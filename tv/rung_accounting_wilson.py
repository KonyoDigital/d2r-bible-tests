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
would be ONE idea. These are TWENTY-SEVEN different ways to be wrong about the same question.

⚠⚠ SEVENTEEN OF THEM WERE ADDED TO CLEAR THE HARDENED TIER, AND NINE WENT RED ON ARRIVAL.
`wilson_lower(N, N)` is exactly N / (N + 3.8416), so HARD_BAR 0.900 needs 35 distinct attacks and
`reel.route` held 19. That is a REASON TO LOOK HARDER, never a reason to count louder: an attack
that cannot fail inflates n and proves nothing, which is the objection `wilsonByAttack` exists to
make. Nine of the seventeen found a real defect — a fraction over zero reels, a string iterated
into a decided-count, a bool read as a coverage of one, RECORDED asserted over rungs the ladder
does not name — and the guards for all nine shipped in the same change.
"""
import io
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




# ── SEVENTEEN MORE DISTINCT ATTACKS ─────────────────────────────────────────────
# ⚠⚠ EACH RETURNS "ok" OR WHAT IT ACTUALLY GOT, and each is a DIFFERENT IDEA about how
# "we cannot establish this" gets laundered into a number — never one idea over more inputs.
# NINE of them went red against the code as it stood when they were written; the guards they
# demanded shipped in the same change. `wilsonByAttack` counts these one each.
#
# ⚠ PURE. Every one builds a dict, swaps a module attribute back in a `finally`, or writes
# inside a temp directory it removes. Nothing here reads his shelf, arms a sweep or deletes a byte.

class _Reader(object):
    """Hands the REAL store reader a store's TEXT, with no file anywhere. -> file-like

    ⚠⚠ THE HARNESS MAY NOT WRITE AND MAY NOT DELETE, and `test_it_cannot_write_delete_or_arm_
    anything` refuses any such name in this source. It is right to: a harness able to create and
    remove paths is a harness that one wrong path points at his footage. The first cut of these
    attacks used a temp directory and that gate caught it — working, on the first run of new code.

    So the store attacks swap `one_funnel`'s own `io` for this, which answers from memory, and
    put it back in a `finally`. No path is created, none is removed, and the code under attack
    is the real `_waypoint_cover` rather than a re-implementation of it.
    """

    def __init__(self, text):
        self.text = text

    def open(self, path, *a, **k):
        import io as _io
        if self.text is None:
            raise IOError("this store does not exist: %s" % path)
        return _io.StringIO(self.text)


def _cover_reading(text, sids):
    """Run the REAL `_waypoint_cover` over a store whose CONTENT is `text`. -> dict

    ⚠ `_waypoint_cover` does `os.path.join(HERE, store)`, and join with an ABSOLUTE second
    component discards the first — so the name below never resolves inside tv/ even if the
    reader shim were removed.
    """
    _store, _iomod = OF._store_of, OF.io
    try:
        OF._store_of = lambda r: (("/rung_accounting_synthetic_store.json", "")
                                  if r == "triaged" else (None, "no store"))
        OF.io = _Reader(text)
        return OF._waypoint_cover(sids)
    finally:
        OF._store_of, OF.io = _store, _iomod


def _a_owner_will_not_import():
    _orig = dict(OF.WAYPOINT_SOURCES)
    try:
        OF.WAYPOINT_SOURCES["triaged"] = ("no_such_module_zzz", "STORE")
        nm, why = OF._store_of("triaged")
    finally:
        OF.WAYPOINT_SOURCES.clear()
        OF.WAYPOINT_SOURCES.update(_orig)
    return "ok" if (nm is None and why) else "named %r (%s)" % (nm, why)


def _a_owner_stopped_declaring_its_constant():
    import retro_triage as RT
    had, sv = hasattr(RT, "STORE"), getattr(RT, "STORE", None)
    try:
        if had:
            delattr(RT, "STORE")
        nm, why = OF._store_of("triaged")
    finally:
        if had:
            setattr(RT, "STORE", sv)
    return "ok" if (nm is None and why) else "named %r (%s)" % (nm, why)


def _a_waypoints_follows_a_rename():
    import retro_triage as RT
    sv = getattr(RT, "STORE", None)
    try:
        RT.STORE = "retro_triage_RENAMED.json"
        got = OF.waypoints().get("triaged")
    finally:
        RT.STORE = sv
    return "ok" if got == "retro_triage_RENAMED.json" else "answered %r" % (got,)


def _a_store_is_not_an_object():
    c = _cover_reading('["a", "b"]', {"s1", "s2"})["triaged"].get("covered")
    return "ok" if c is None else "covered=%r from a store that is a list" % (c,)


def _a_store_will_not_open():
    c = _cover_reading(None, {"s1"})["triaged"].get("covered")
    return "ok" if c is None else "covered=%r from a store that would not open" % (c,)


def _a_one_reel_counted_twice():
    c = _cover_reading('{"s1": 1, "reel_s1": 1}', {"s1"})["triaged"].get("covered")
    return "ok" if c == 1 else "covered=%r for ONE reel under two spellings" % (c,)


def _a_coverage_over_zero_reels():
    cov = _cover_reading('{"s1": 1}', set())
    if cov["triaged"].get("covered") is not None:
        return "covered=%r with no reel named" % cov["triaged"].get("covered")
    got = OF._observability(cov).get("state")
    return "ok" if got == "UNKNOWN" else "verdict %s over zero reels" % got


def _a_reels_is_a_truthy_non_sequence():
    import reel_story as RS
    orig, out = RS.story, []
    try:
        for shape in ("abcdefg", {"x": 1, "y": 2}):
            RS.story = lambda *a, **k: {"reels": shape}
            out.append(OF._decided_count()[:2])
    finally:
        RS.story = orig
    return "ok" if all(x == (None, None) for x in out) else "counted %r" % (out,)


def _a_stage_the_ladder_does_not_declare():
    import reel_story as RS
    orig = RS.story
    try:
        RS.story = lambda *a, **k: {"reels": [
            {"reel": "r1", "stageKnown": True, "stage": "TELEPORTED"}]}
        dec, tot, _w = OF._decided_count()
    finally:
        RS.story = orig
    return "ok" if dec == 0 else "decided %r of %r at a stage STAGES does not name" % (dec, tot)


def _a_cover_is_not_a_mapping():
    try:
        got = OF._observability(["filmed", "triaged"]).get("state")
    except Exception as e:
        return "raised %s" % type(e).__name__
    return "ok" if got == "UNKNOWN" else got


def _a_rung_reading_is_not_a_mapping():
    try:
        got = OF._observability({"a": {"store": "x", "covered": 3}, "b": None}).get("state")
    except Exception as e:
        return "raised %s" % type(e).__name__
    return "ok" if got == "UNKNOWN" else got


def _an_impossible_count():
    neg = OF._observability({"a": {"store": "x", "covered": 3},
                             "b": {"store": "y", "covered": -1}}).get("state")
    over = OF._observability({"a": {"store": "x", "covered": 3},
                              "b": {"store": None, "derivedBy": "m.f()",
                                    "decided": 41, "decidedOf": 40}}).get("state")
    return "ok" if (neg == "UNKNOWN" and over == "UNKNOWN") else "covered=-1 %s, 41 of 40 %s" % (neg, over)


def _a_bool_wearing_a_counts_clothes():
    got = OF._observability({"a": {"store": "x", "covered": 3},
                             "b": {"store": "y", "covered": True}}).get("state")
    return "ok" if got == "UNKNOWN" else "%s (True read as one reel covered)" % got


def _unknown_outranks_dark():
    got = OF._observability({"a": {"store": "x", "covered": None},
                             "b": {"store": "y", "covered": 0},
                             "c": {"store": "z", "covered": 5}}).get("state")
    return "ok" if got == "UNKNOWN" else got


def _with_funnel(ladder, rows, cover):
    """Drive the REAL `funnel()` over a synthetic shelf. -> dict"""
    _l, _r, _c = OF._ladder, OF._rows, OF._waypoint_cover
    try:
        OF._ladder = lambda: (ladder, "")
        OF._rows = lambda: (rows, "")
        OF._waypoint_cover = lambda sids: cover
        return OF.funnel()
    finally:
        OF._ladder, OF._rows, OF._waypoint_cover = _l, _r, _c


def _an_unreadable_store_outranks_recorded():
    f = _with_funnel(("a", "b"),
                     [{"reel": "reel_s1", "stage": "a", "stageIdx": 0, "stageKnown": True},
                      {"reel": "reel_s2", "stage": "b", "stageIdx": 1, "stageKnown": True}],
                     {"a": {"store": "x", "covered": 2}, "b": {"store": "y", "covered": None}})
    return "ok" if f.get("passage") == "UNKNOWN" else "passage %s" % f.get("passage")


def _the_waypoint_vocabulary_drifts_from_the_ladder():
    f = _with_funnel(("a", "b", "c", "d", "e", "f"),
                     [{"reel": "reel_s1", "stage": "a", "stageIdx": 0, "stageKnown": True}],
                     dict((k, {"store": "s", "covered": 2}) for k in "abghij"))
    return ("ok" if f.get("passage") != "RECORDED"
            else "RECORDED over %s, none of which the ladder names" % sorted(f.get("datedRungs")))


def _a_reel_row_that_is_not_a_mapping():
    try:
        f = _with_funnel(("a", "b"),
                         [{"reel": "reel_s1", "stage": "a", "stageIdx": 0, "stageKnown": True},
                          "a row that is not a mapping", None],
                         {"a": {"store": "x", "covered": 1}, "b": {"store": "y", "covered": 1}})
    except Exception as e:
        return "raised %s" % type(e).__name__
    return "ok" if f.get("ok") else "funnel refused: %s" % str(f.get("why"))[:40]


def _extra_attacks():
    """Seventeen more. -> list of (name, fn, why). Each fn answers "ok" or what it got."""
    return [
        ("the store's owner will not import", _a_owner_will_not_import,
         "A GUESSED FILENAME WOULD READ SOMEBODY ELSE'S FILE and report its coverage as this "
         "rung's. The resolver must name the store or refuse, never derive one from the rung"),
        ("the owner stopped declaring its store constant",
         _a_owner_stopped_declaring_its_constant,
         "A DIFFERENT CAUSE FROM AN IMPORT FAILURE and a different branch: the module is fine "
         "and the constant was renamed. A stale name here reads a file that is no longer the "
         "store, which is worse than not reading one"),
        ("waypoints() must follow a rename", _a_waypoints_follows_a_rename,
         "REG-537 REGRESSED ONCE ALREADY — this was a dict comprehension evaluated at import, "
         "three lines under the fix for the same defect. A frozen snapshot cannot be caught by "
         "asking the resolver, because the resolver is the half that is right"),
        ("a store that parses but is not an object", _a_store_is_not_an_object,
         "`s in blob` is legal on a list and answers a confident 0. The refusal must come from "
         "the type check, not from the lookup happening to find nothing"),
        ("a store that will not open", _a_store_will_not_open,
         "UNREADABLE IS NOT ZERO COVERAGE — REG-555's whole subject, asked at the site that "
         "PRODUCES the None rather than at the verdict that consumes it"),
        ("one reel present under both spellings", _a_one_reel_counted_twice,
         "a store holding `s1` AND `reel_s1` must count that reel ONCE. Counting keys instead "
         "of reels would put coverage above the number of reels asked about, and a fraction "
         "over 100% reads as healthier than complete"),
        ("a coverage fraction over ZERO reels", _a_coverage_over_zero_reels,
         "0 of 0 IS NOT COVERAGE OF ZERO. Reachable whenever every row on the shelf is nameless: "
         "the empty-shelf guard does not fire, every store answers 0, and the passage claims his "
         "pipeline records nothing. [[zero-needs-a-denominator]]"),
        ("`reels` is truthy and not a sequence", _a_reels_is_a_truthy_non_sequence,
         "ONE LEVEL BELOW the not-a-mapping attack, which the `isinstance(st, dict)` check "
         "already catches. A string passes that check and is then iterated character by "
         "character into a confident 'nothing was decided'"),
        ("a stage the ladder does not declare", _a_stage_the_ladder_does_not_declare,
         "TWO READERS OF ONE SHELF. `funnel()`'s ladder loop calls this reel unknownStage and "
         "`_decided_count` called it decided, so the observability verdict rested on the more "
         "generous of two disagreeing counts. [[feedback-contradiction-is-the-finding]]"),
        ("the cover is not a mapping", _a_cover_is_not_a_mapping,
         "A VERDICT FUNCTION THAT RAISES HAS NO STATE AT ALL. Distinct from the empty-map "
         "attack: that one returns a wrong verdict, this one returns none"),
        ("one rung's reading is not a mapping", _a_rung_reading_is_not_a_mapping,
         "the container is sound and one entry is not — a different fix from validating the "
         "container, and the shape a half-written cover actually has"),
        ("an impossible coverage count", _an_impossible_count,
         "covered=-1 read as 'answers for nobody' and decided 41-of-40 read as OBSERVED. More "
         "coverage than reels is the instrument fault `bank()` refuses as k > n, and a negative "
         "count is a finding manufactured from one"),
        ("a bool wearing a count's clothes", _a_bool_wearing_a_counts_clothes,
         "`bool` subclasses `int`, so `covered=True > 0` held and a store that answered YES was "
         "read as ONE REEL COVERED. Distinct from an impossible count: this one is a plausible "
         "number. The same shape `self_arming._row_fault` already refuses on its own rows"),
        ("UNKNOWN must outrank DARK", _unknown_outranks_dark,
         "a genuine gap and an unmeasurable rung in the same cover: the verdict must be about "
         "what could not be established, or a real reading failure hides behind a real finding"),
        ("an unreadable store outranks RECORDED", _an_unreadable_store_outranks_recorded,
         "the same precedence one layer up and in another vocabulary — `passage`, not "
         "`observability`. REG-555 proved the UNRECORDED direction; this proves the RECORDED one"),
        ("the waypoint vocabulary drifts from the ladder",
         _the_waypoint_vocabulary_drifts_from_the_ladder,
         "`len(dated) >= len(rungs)` weighs a count from WAYPOINT_SOURCES against a count from "
         "reel_story.STAGES. Six dated rungs the ladder never names read as RECORDED — the "
         "strongest verdict available, over rungs nobody measured. [[copy-drift]]"),
        ("a reel row that is not a mapping", _a_reel_row_that_is_not_a_mapping,
         "the ladder loop defends against exactly this shape and continues past it; the sid "
         "loop twenty lines down did not, because `(r or {})` leaves a truthy non-mapping "
         "alone. One module expecting and forbidding the same row. [[the-unjoined-end]]"),
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

    for name, fn, why in _extra_attacks():
        try:
            got = fn()
        except Exception as e:
            got = "CRASHED(%s)" % str(e)[:40]
        correct = (got == "ok")
        ok += 1 if correct else 0
        rows.append({"attack": name, "expected": "ok", "got": got, "correct": correct, "why": why})

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
    # ⚠⚠ v2734 — THIS BLOCK WAS UNREACHABLE ON ITS FIRST WRITING. It was anchored on the
    # sabotage bank line, which lives INSIDE `if "--bank" in argv:` — so `--xfam` alone
    # never reached it and the mode printed a normal run instead of refusing. Built and
    # not joined, caught only by invoking it. [[the-unjoined-end]]
    import self_arming as SA
    # ⚠⚠ v2734 — THE CROSS-FAMILY SOURCE NEEDS AN OWNER, AND CI WAS RIGHT TO SAY SO.
    # `rung_accounting_xfam` was banked from a one-off shell call, so PROVES named a source no
    # module owned and `test_every_lock_declares_its_attacks` failed with the exact sentence
    # that matters: "evidence nobody can re-derive". A witness with no author is a number.
    #
    # This is the `vault_live` shape — a legitimate LABEL, provided a real harness banks under
    # it. The cross-family pass itself is a paid call to another model family and cannot be
    # re-run for free, so this RECORDS a verdict that was obtained, the same way
    # `ship_audit.py --third-eye` records a review rather than performing one.
    # ⚠ AND IT REFUSES WITHOUT ONE. `--xfam` with no verdict file banks NOTHING: a mode that
    # banked on being invoked would manufacture a witness on demand, which is the precise cheat
    # `_hardening_gap` names. [[unknown-stays-unknown]] [[join-gate-heart]]
    if "--xfam" in argv:
        _vf = None
        for _i, _a in enumerate(argv):
            if _a == "--xfam" and _i + 1 < len(argv):
                _vf = argv[_i + 1]
        if not _vf:
            print("  --xfam needs the path of a recorded cross-family verdict; banking NOTHING")
            return 1
        try:
            _txt = io.open(_vf, encoding="utf-8").read().strip()
        except Exception as _e:
            print("  --xfam could not read %r (%s); banking NOTHING" % (_vf, str(_e)[:60]))
            return 1
        if not _txt:
            print("  --xfam verdict file is empty; banking NOTHING")
            return 1
        SA.bank("reel.route", "cross-family", "rung_accounting_xfam", n=1, k=1, attacks=1,
                note=("a different model family was handed the rung-accounting decision code "
                      "and told to REFUTE six named claims; recorded verdict: %s"
                      % _txt.replace("\n", " ")[:160]),
                ref=_vf)
        print("  banked the recorded cross-family verdict under rung_accounting_xfam")
        return 0

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
                      note="v2725+a2hard — twenty-seven distinct attacks on whether the rung "
                           "accounting can refuse when it cannot establish where a reel is",
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
