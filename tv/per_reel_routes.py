#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A15 clause 3 — *"then the routes separate, PER REEL, BY SCENARIO. Each reel takes the path its
own content earns, and gets extracted from according to what it actually holds."*

⚠⚠ THE QUESTION IS NOT "DO REELS DIFFER" — THEY OBVIOUSLY DO. It is whether the difference is
EARNED BY THE CONTENT. A shelf where every route is decided by age, or by whether the test suite
opens the reel, has divergence in it and none of it is the divergence A15 asks for. So each route
is attributed to what decided it, using the split `reel_story` already draws in its own source:

    POLICY_HOLDS  recent · test-fixture · target-met      <- decided by AGE or by the SUITE
    GLOBAL_HOLDS  no-witness-index · ledger-unreadable    <- decided by a fact about the WHOLE tree
    everything else                                       <- decided by what this reel HOLDS

MEASURED 2026-09-04, his 40 reels:

    tag        zero-pages 28 · test-fixture 7 · recent 5
    holdKind   evidence 28   · policy 12
    stage      swept      28 · releasable 12

⚠⚠ THE TWO COLUMNS ARE THE SAME 28 AND THE SAME 12, AND THAT IS THE FINDING. Every reel that has
reached the far end got there BY POLICY — five for being recent, seven for being a fixture the
suite opens. Every content-routed reel is parked at one rung, under ONE tag. So the content-earned
divergence A15 describes exists in the code and **NOTHING ON HIS SHELF EXERCISES IT**: there are not
two reels today taking different paths because of what they hold.

⚠ THAT IS NOT A DEFECT AND MUST NOT BE REPORTED AS ONE. `zero-pages` means *swept, and the sweep
found nothing to read* — those reels are held as EVIDENCE on purpose, because the engine reopens
them when the prompt improves (`reel_story`'s own words). A probe that called this a routing failure
would cry wolf on a shelf behaving exactly as designed. It is UNEXERCISED, which is a different
fact from broken, and a third fact from working. [[unknown-stays-unknown]]

    python3 tv/per_reel_routes.py
    python3 tv/per_reel_routes.py --json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: How many DISTINCT content-earned routes must be observed before the clause can be called
#: exercised. Two is the floor because one route is not a divergence — it is a queue.
MIN_DISTINCT = 2


def _story():
    try:
        import reel_story as RS
        st = RS.story()
        return ((st.get("reels") or []) if isinstance(st, dict) else []), RS, ""
    except Exception as e:
        return [], None, "reel_story would not answer (%s)" % str(e)[:80]


def _decided_by(tag, RS):
    """What decided this reel's route? -> ("policy" | "global" | "content" | "unknown", why)

    ⚠ THE SPLIT IS QUOTED FROM `reel_story`, NEVER RESTATED HERE. It draws exactly this line in its
    own source — *"held for a reason that is ABOUT THIS REEL'S EVIDENCE versus held by policy"* —
    and a second copy of that list is a rename away from attributing a policy hold to content.
    [[copy-drift]] §1
    """
    t = str(tag or "")
    if not t:
        return "unknown", "the reel carries no tag, so nothing here knows what routed it"
    if t in getattr(RS, "POLICY_HOLDS", ()):
        return "policy", "%r is a POLICY hold — age, or the suite opening it, not what it holds" % t
    if t in getattr(RS, "GLOBAL_HOLDS", ()):
        return "global", "%r is a hold about the WHOLE tree, identical for every reel" % t
    if t not in getattr(RS, "TAG_STAGE", {}):
        # ⚠ AN UNTAUGHT TAG IS NOT CONTENT. Rounding it into the content bucket would inflate the
        # very count this module exists to report honestly.
        return "unknown", "%r is a tag reel_story's own map has never been taught" % t
    return "content", "%r is decided by what this reel holds" % t


def routes(rows=None):
    """-> {"ok", "state", "byDecider", "contentRoutes", "policyRoutes", "rows", "why"}

    States: EARNED (>= MIN_DISTINCT distinct content-earned routes) · UNEXERCISED (content routing
    exists but every content-routed reel took the same one) · POLICY_ONLY (no reel was routed by
    its content at all) · UNKNOWN (nothing to read).
    """
    # ⚠⚠ REG-546 — EVERY RETURN CARRIES THE SAME KEYS. These dropped five, so a caller reading
    # them broke on exactly the paths that mean NOTHING WAS ESTABLISHED. Caught by the cross-probe
    # SHAPE law, which found the same defect in three sibling probes on its first run.
    def _unknown(w):
        return {"ok": False, "state": "UNKNOWN", "rows": [], "byDecider": {},
                "contentRoutes": {}, "policyRoutes": {}, "distinctContentRoutes": 0,
                "minDistinct": MIN_DISTINCT, "walked": 0, "why": w}

    RS = None
    why = ""
    if rows is None:
        rows, RS, why = _story()
    else:
        try:
            import reel_story as RS
        except Exception as e:
            return _unknown("reel_story would not import (%s)" % str(e)[:80])
    if not rows:
        return _unknown("UNKNOWN, not an empty shelf — %s"
                        % (why or "no reel reached this probe and nothing said why"))

    out, by_decider = [], {}
    content_routes, policy_routes = {}, {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        tag = r.get("tag")
        decider, dwhy = _decided_by(tag, RS)
        # A ROUTE is the pair a reader would call "the path this reel took": what routed it, and
        # where that put it. Two reels on the same tag at the same rung took the same path.
        route = "%s@%s" % (tag, r.get("stage"))
        out.append({"reel": r.get("reel"), "tag": tag, "stage": r.get("stage"),
                    "decidedBy": decider, "why": dwhy, "route": route})
        by_decider[decider] = by_decider.get(decider, 0) + 1
        if decider == "content":
            content_routes[route] = content_routes.get(route, 0) + 1
        elif decider == "policy":
            policy_routes[route] = policy_routes.get(route, 0) + 1

    n_content = len(content_routes)
    if not content_routes:
        state = "POLICY_ONLY"
    elif n_content >= MIN_DISTINCT:
        state = "EARNED"
    else:
        state = "UNEXERCISED"

    if state == "EARNED":
        tail = ("EARNED — %d distinct content-decided route(s) across %d reel(s), so two reels do "
                "take different paths because of what they hold."
                % (n_content, by_decider.get("content", 0)))
    elif state == "UNEXERCISED":
        tail = ("UNEXERCISED — content routing EXISTS (%d reel(s) routed by what they hold) and "
                "every one of them took the SAME route (%s). One route is a queue, not a "
                "divergence. ⚠ This is not a defect: a content tag can mean 'swept and found "
                "nothing', which is a deliberate hold, so a probe calling this a routing failure "
                "would cry wolf on a shelf behaving as designed."
                % (by_decider.get("content", 0), ", ".join(sorted(content_routes))))
    elif state == "POLICY_ONLY":
        tail = ("POLICY_ONLY — not one reel was routed by its content. Every route on this shelf "
                "was decided by age, by the suite opening the reel, or by a fact about the whole "
                "tree. A15 asks for the path a reel's own content earns.")
    else:
        tail = "UNKNOWN"

    return {
        "ok": True, "state": state, "rows": out, "byDecider": by_decider,
        "contentRoutes": content_routes, "policyRoutes": policy_routes,
        "distinctContentRoutes": n_content, "minDistinct": MIN_DISTINCT, "walked": len(out),
        "why": ("%d reel(s): %s. %s"
                % (len(out),
                   " · ".join("%s %d" % (k, by_decider[k]) for k in sorted(by_decider)),
                   tail)),
    }


def main(argv):
    r = routes()
    if "--json" in argv:
        print(json.dumps(r, indent=2, sort_keys=True))
        return 0
    print("\nA15 clause 3 — do the routes separate PER REEL, BY WHAT THE REEL HOLDS?\n")
    if not r["ok"]:
        print("  %s\n" % r["why"])
        return 0
    print("  %s" % r["state"])
    for k in sorted(r["byDecider"]):
        print("     decided by %-8s %3d reel(s)" % (k, r["byDecider"][k]))
    print()
    print("  CONTENT-EARNED ROUTES (the ones A15 is about):")
    for k in sorted(r["contentRoutes"]) or ["(none)"]:
        print("     %-28s %s" % (k, r["contentRoutes"].get(k, "")))
    print("  ROUTES DECIDED BY POLICY (age, or the suite opening the reel):")
    for k in sorted(r["policyRoutes"]) or ["(none)"]:
        print("     %-28s %s" % (k, r["policyRoutes"].get(k, "")))
    print("\n  %s\n" % r["why"])
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
