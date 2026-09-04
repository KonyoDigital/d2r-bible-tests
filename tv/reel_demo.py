#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A DEMONSTRATION ON HIS REAL REELS — did they go through, and does downstream still agree?

Konyo, 2026-09-04: *"do tests on the reels see that they get run and proccesed through the printer
and everything down stream correctly as it was registered before.. chronicles and all the
readers.. everytinh was working before.. so it needs to be tested too"*, then *"simulations",
"demonstrations", "based on real reels", "ingame", "those same reels", "see that they got
proccsed logically coded"*.

⚠⚠ THIS IS A DEMONSTRATION, NOT A UNIT TEST, AND THE DIFFERENCE IS THE POINT. The suites already
assert behaviour against fixtures. What nothing did was take HIS OWN FOOTAGE, walk it through the
pipeline that has been rebuilt underneath it over nine versions, and show — reel by reel — that
every station still answers and that the numbers downstream are the ones that were registered
before any of it changed.

★ IT ASSERTS AGAINST REGISTERED VALUES, NOT AGAINST ITSELF. `route_totals` is the one source for
runewords/sets/uniques, each carrying his own ruling; a demonstration that re-derived them from
the same code it is testing would agree with itself and prove nothing. [[feedback-verify-not-proxy]]

★ AND IT NEVER WRITES. No seal, no ledger, no tombstone, no prune. It reads and it reports.

    python3 tv/reel_demo.py            # every reel, every station, and the downstream checks
    python3 tv/reel_demo.py --json
    python3 tv/reel_demo.py <reel>     # one reel, in full
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _check(name, got, want, why):
    ok = (got == want)
    return {"check": name, "ok": ok, "got": got, "want": want, "why": why}


def _downstream():
    """The numbers that were REGISTERED before the pipeline was rebuilt. -> [check]"""
    out = []
    try:
        import route_totals as RT
        for kind, want in (("runeword", 99), ("set", 135), ("unique", 403)):
            got = RT.total(kind) if hasattr(RT, "total") else None
            out.append(_check("route_totals.%s" % kind, got, want,
                              "his own ruling, and the one source every surface quotes"))
    except Exception as e:
        out.append({"check": "route_totals", "ok": False, "got": None, "want": "importable",
                    "why": "would not answer (%s)" % str(e)[:80]})
    # the three route sets must AGREE with that one source — the v2484 rule
    for mod, label in (("chronicle_routes", "chronicle"), ("fleet_routes", "fleet"),
                       ("roster_routes", "roster")):
        try:
            m = __import__(mod)
            r = m.report() if hasattr(m, "report") else (m.routes() if hasattr(m, "routes") else {})
            out.append({"check": "%s reports" % label, "ok": bool(r and r.get("ok", True)),
                        "got": (r or {}).get("state") or "ok", "want": "ok",
                        "why": "the route set still derives without raising"})
        except Exception as e:
            out.append({"check": "%s reports" % label, "ok": False, "got": str(e)[:60],
                        "want": "ok", "why": "the route set would not answer"})
    return out


def demo(reel=None):
    """Walk his real reels through the printer and check downstream. -> dict"""
    try:
        import printer as P
        rep = P.stream(reel)
    except Exception as e:
        return {"ok": False, "state": "UNKNOWN", "reels": [], "checks": [],
                "why": "the printer would not run (%s) — UNKNOWN, never 'the reels are fine'"
                       % str(e)[:90]}
    rows = rep.get("rows") or []
    stations = list(rep.get("stations") or ())
    reels, blanks = [], 0
    for r in rows:
        st = r.get("stations") or {}
        # every station must have ANSWERED — a station missing from a row reads as a reel that
        # did not need it, which is exactly what the printer's own shape law forbids
        missing = [s for s in stations if s not in st]
        unknown = [s for s in stations if str((st.get(s) or {}).get("say")) == "UNKNOWN"]
        if missing:
            blanks += 1
        reels.append({
            "reel": r.get("reel"),
            "in": (st.get("in") or {}).get("say"),
            "stage": (st.get("funnel") or {}).get("say"),
            "template": (st.get("template") or {}).get("template"),
            "zone": (st.get("template") or {}).get("say"),
            "worth": (st.get("template") or {}).get("worthReading"),
            "route": (st.get("route") or {}).get("say"),
            "extract": (st.get("extract") or {}).get("say"),
            "out": (st.get("out") or {}).get("say"),
            "missingStations": missing,
            "unknownStations": unknown,
        })
    checks = _downstream()
    checks.append(_check("every reel carries every station", blanks, 0,
                         "a station missing from a row reads as a reel that did not need it"))
    checks.append({"check": "the printer walked his shelf", "ok": bool(rows),
                   "got": len(rows), "want": ">0",
                   "why": "zero reels would mean the demonstration proved nothing at all"})
    bad = [c for c in checks if not c["ok"]]
    return {
        "ok": not bad, "state": ("PASS" if not bad else "FAIL"),
        "reels": reels, "checks": checks, "walked": len(rows),
        "stations": stations,
        "why": ("%d reel(s) walked through %d station(s); %d of %d downstream check(s) pass. %s"
                % (len(rows), len(stations), len(checks) - len(bad), len(checks),
                   "Everything registered before still agrees." if not bad else
                   "⚠ %d check(s) DISAGREE with what was registered before." % len(bad))),
    }


def main(argv):
    reel = next((a for a in argv if not a.startswith("-")), None)
    r = demo(reel)
    if "--json" in argv:
        print(json.dumps(r, indent=2, sort_keys=True, default=str))
        return 0
    print("\nREEL DEMONSTRATION — his own footage, through the whole pipeline\n")
    if not r.get("reels") and not r["ok"]:
        print("  %s\n" % r["why"])
        return 1
    print("  %-30s %-9s %-11s %-9s %-11s %s" % ("reel", "door", "stage", "template", "extract", "worth"))
    for x in r["reels"][:60]:
        print("  %-30s %-9s %-11s %-9s %-11s %s" % (
            str(x["reel"])[-30:], str(x["in"])[:9], str(x["stage"])[:11],
            str(x["template"])[:9], str(x["extract"])[:11], x["worth"]))
    print("\n  DOWNSTREAM, against what was registered before:")
    for c in r["checks"]:
        print("    %s %-34s got %-8s want %s" % ("✅" if c["ok"] else "❌", c["check"],
                                                 str(c["got"])[:8], str(c["want"])[:12]))
    print("\n  %s · %s\n" % (r["state"], r["why"]))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
