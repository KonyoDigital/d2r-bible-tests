#!/usr/bin/env python3
"""The accumulating record of what the Wilson shadow rule saw, and the ONLY thing that writes it.

WHY THIS FILE EXISTS AT ALL, rather than living beside the scoring. Konyo: "make it self improving
and really accurate so its locked and locks in the console." The lane has to accumulate — agreement
on 23 names is a statement about how little evidence his tree holds, not about the two rules.

But chronicle_retro.py carries LAW 1: "READ-ONLY UNTIL APPLY... NO exception: this module cannot
write AT ALL, and test_chronicle_retro proves it from the source text." My first cut opened a file
right inside it and the suite caught me. The v1608 index recovery lives in reel_index.py for exactly
this reason; this is the same split. chronicle_retro SCORES, this PERSISTS, the console REPORTS.

WHAT IT REFUSES TO DO, which is the part that matters:

  · IT NEVER PROMOTES THE SHADOW RULE. Reaching the threshold means the record is worth reading, not
    that the gate should switch. A gate that promoted itself on its own agreement statistics is
    marking its own homework, and the failure lands as a wrong verdict written into his grail — the
    one place a wrong answer is invisible. The record is the argument; the decision is his.
  · IT NEVER COUNTS DISAGREEMENTS WITHOUT NAMING THEM. "3 disagreements" is not actionable;
    "Shako: the gate grounds it, Wilson holds it at 0.31 on one witness" is. A count is where a real
    divergence hides.
  · IT NEVER STARTS A FRESH COUNT OVER A FILE IT COULD NOT PARSE. That would erase the history the
    record exists to build, and the reset would look like a young ledger rather than a lost one.
    [[unknown-stays-unknown]] [[feedback-silence-is-not-evidence]]
"""

import io
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "shadow_ledger.json")

# How much is enough to be worth HIS decision. Deliberately conservative: the cost of promoting too
# early is a wrong verdict on his grail; the cost of waiting is nothing at all.
ENOUGH_NAMES = 500
ENOUGH_SWEEPS = 20


def _blank():
    return {"v": 1, "sweeps": 0, "names": 0, "agree": 0, "disagree": 0,
            "byDirection": {"shadowWouldGround": 0, "shadowWouldHold": 0},
            "recent": [], "firstAt": None, "lastAt": None}


def observe(scores, at=None, path=None):
    """Fold one sweep's `chronicle_retro.shadow_scores(...)` into the durable record. -> dict"""
    if not isinstance(scores, dict) or not isinstance(scores.get("scored"), int):
        return {"ok": False, "why": "that is not a shadow_scores result"}
    scored = scores["scored"]
    dis = [d for d in (scores.get("disagreements") or []) if isinstance(d, dict)]
    if not scored:
        return {"ok": False, "why": "nothing in that proposal carried scoreable evidence — "
                                    "recorded nothing rather than a sweep of zero"}
    p = path or LEDGER
    doc = _blank()
    try:
        with io.open(p, encoding="utf-8") as fh:
            prior = json.load(fh)
        if isinstance(prior, dict) and isinstance(prior.get("names"), int):
            doc.update(prior)
            doc.setdefault("byDirection", {"shadowWouldGround": 0, "shadowWouldHold": 0})
            doc.setdefault("recent", [])
    except FileNotFoundError:
        pass
    except Exception:
        return {"ok": False, "why": "the shadow ledger will not parse — refusing to start a new "
                                    "count over it, because that would erase the history it is for"}

    at = at if isinstance(at, int) else int(time.time() * 1000)
    for d in dis:
        d = dict(d, at=at)
        key = "shadowWouldGround" if d.get("shadowPass") else "shadowWouldHold"
        doc["byDirection"][key] = int(doc["byDirection"].get(key) or 0) + 1
        doc["recent"].append(d)
    doc["recent"] = doc["recent"][-200:]      # bounded: a record, not a growing file
    doc["sweeps"] = int(doc.get("sweeps") or 0) + 1
    # ⚠⚠ v2225 — DISTINCT NAMES, NOT NAME-SCORINGS. This was `+= scored`, and the chronicle sweep
    # re-scores the same small proposal roughly every 11 seconds, so the field called `names` was
    # counting repetitions. MEASURED on his live ledger before the fix: names=1141 across 647
    # sweeps in 2.00 hours - while chron_evidence.json holds 417 distinct names and bible.html pins
    # the uniques universe at 403. 1141 distinct was arithmetically impossible, and THE COUNT WAS
    # THE TELL had anyone read it against the ceiling.
    #
    # It was not cosmetic. ENOUGH_SWEEPS=20 was crossed in about 222 seconds and ENOUGH_NAMES=500
    # shortly after, so `state()` returned "agrees" - the branch whose sentence is "The record is
    # worth a decision" - and console_doctor rendered it OK. The lane existed to argue about
    # changing the gate that writes his grail, and it was arguing from one small slice counted 647
    # times. Worse: scoring his ACTUAL evidence store yields 39 disagreements, while the ledger
    # reported zero.
    _seen = set(doc.get("nameSet") or [])
    _new = [n for n in (scores.get("names") or []) if isinstance(n, str)]
    _seen.update(_new)
    doc["nameSet"] = sorted(_seen)[:2000]     # bounded; the universe is ~523
    doc["names"] = len(doc["nameSet"])
    doc["scorings"] = int(doc.get("scorings") or 0) + scored   # the old number, honestly labelled
    doc["agree"] = int(doc.get("agree") or 0) + (scored - len(dis))
    doc["disagree"] = int(doc.get("disagree") or 0) + len(dis)
    doc["firstAt"] = doc.get("firstAt") or at
    doc["lastAt"] = at

    try:
        tmp = p + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True))
        os.replace(tmp, p)
    except Exception as e:
        return {"ok": False, "why": "could not write the shadow ledger: %s" % str(e)[:80]}
    return {"ok": True, "scored": scored, "disagreements": len(dis),
            "totalNames": doc["names"], "totalSweeps": doc["sweeps"]}


def state(path=None):
    """What the record says, in one dict a surface can render. -> dict

    Four states kept apart, because collapsing them is how a shadow lane becomes a rubber stamp:
    empty · unreadable · thin (agreeing, too small to mean anything) · agrees · disagrees.
    """
    scg = 0          # v2225 — defined BEFORE the early returns below reference it
    try:
        with io.open(path or LEDGER, encoding="utf-8") as fh:
            d = json.load(fh)
    except FileNotFoundError:
        return {"ok": True, "scorings": scg, "state": "empty",
                "say": "the shadow rule has never been run over a sweep — nothing is known yet"}
    except Exception as e:
        return {"ok": False, "state": "unreadable",
                "say": "the shadow ledger will not parse (%s) — which is not the same as "
                       "'they agree'" % str(e)[:60]}
    n, sw = int(d.get("names") or 0), int(d.get("sweeps") or 0)
    dis = int(d.get("disagree") or 0)
    # v2225 — the honest pair, both reported. `names` is DISTINCT names ever scored; `scorings` is
    # how many times a name was scored at all, which is the number this field used to hold while
    # calling itself names. Publishing both makes the inflation visible instead of silent: a
    # scorings/names ratio of 647 says the lane is re-reading one slice, not accumulating evidence.
    scg = int(d.get("scorings") or 0)
    recent = list(d.get("recent") or [])
    if dis:
        names = ", ".join(str(r.get("name", "?")) for r in recent[-5:])
        return {"ok": True, "scorings": scg, "state": "disagrees", "names": n, "sweeps": sw, "disagree": dis,
                "byDirection": d.get("byDirection"), "recent": recent[-20:],
                "say": "the Wilson rule and the live gate have disagreed on %d of %d names across "
                       "%d sweeps (%s). Each is a name the two rules judge differently — that list "
                       "is the argument for or against switching, and it is yours to read."
                       % (dis, n, sw, names)}
    if n < ENOUGH_NAMES or sw < ENOUGH_SWEEPS:
        return {"ok": True, "scorings": scg, "state": "thin", "names": n, "sweeps": sw, "disagree": 0,
                "say": "the Wilson rule has agreed with the live gate on all %d names it has scored "
                       "across %d sweeps. That is agreement on a SMALL SAMPLE, not evidence the two "
                       "rules are equivalent — %d more names and %d more sweeps before the record "
                       "is worth a decision."
                       % (n, sw, max(0, ENOUGH_NAMES - n), max(0, ENOUGH_SWEEPS - sw))}
    return {"ok": True, "scorings": scg, "state": "agrees", "names": n, "sweeps": sw, "disagree": 0,
            "say": "the Wilson rule has now agreed with the live gate on %d names across %d sweeps "
                   "with zero disagreements. The record is worth a decision — and it is YOURS: this "
                   "lane does not promote itself, because a gate that switches on its own agreement "
                   "statistics is marking its own homework." % (n, sw)}
