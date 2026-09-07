# -*- coding: utf-8 -*-
"""WHAT THE LEDGER SAYS HE OWNS, BESIDE WHAT TODAY'S LAW WOULD GRANT ON THE SAME EVIDENCE.

Konyo, 2026-09-07: *"the vault accumalator that should be connected to the heart of the console
with the vault and joined obivously too"*, and *"just make sure its all wired and not stale and
connected to the heart"*.

=== THE HOLE, AND I HAD IT WRONG FIRST ===
I told him the vault's write path re-gates, so a stale proposal could not land. **That is false on
the path he actually uses.** `control_app.vault_apply` reads:

    caller_supplied = proposal is not None
    prop = proposal or (st.get("result") if isinstance(st.get("result"), dict) else None)
    if caller_supplied and isinstance(prop, dict):   <- the re-gate lives INSIDE this

and the console's own button posts `body: '{}'` — deliberately, and its comment says why: *"NO
BODY. Posting the proposal back would hand the server a client-editable payload; the engine already
holds the gated result, and v1595 re-gates anything supplied from outside precisely because that
door existed."* So the design is coherent — trust your own engine, guard the untrusted door — with
ONE assumption buried in it: **that the engine's stored result was gated under the same law that is
in force now.**

It was not. `vault_retro.merge_vault`/`_absorb` merge-max accumulated rows forever and never call
`gate()` again, so a row keeps whatever verdict it was granted under whatever bar was live the day
it entered. MEASURED on his own store on 2026-09-07: **6 of 7 stored OWNED rows could not clear the
bar they were being displayed under** (banked at 2 witnesses, bar had risen to 3). Pressing
"register 7" would have applied all seven.

⚠ His ruling that day unified the bar back to 2, so those seven are legitimate today and the
immediate risk is gone. THE STRUCTURAL HOLE IS NOT: the next bar change recreates it exactly, and
nothing would say so. That is what this module is for.

=== THE PAIR ===
Neither side is evidence alone, and this never averages them. [[feedback-contradiction-is-the-finding]]
    A  THE STORED CLAIM   vault_accum.json's owned rows as they sit on disk — what the ledger says
    B  THE RE-GATE        those same rows' OWN witnesses through `vault_retro.gate()` at TODAY's
                          live constants — what current law would grant on the same evidence
    AGREE / CONTRADICTION / UNKNOWN

⛔ AGE IS CONTEXT, NEVER A VERDICT. A proposal being 23 hours old is not a fault; his lives on disk
across restarts by design. Reddening on age is the cry-wolf that gets a row ignored within a week.
The verdict comes from the RE-GATE disagreeing, and the age travels beside it as context.
[[stale-reading]]

⛔ AND IT READS ONLY. No sweep, no apply, no prune, no paid read. It re-runs a pure gate over
witnesses already on disk.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

LEDGER = "vault_accum.json"


def stored(path=None):
    """Side A — the owned rows as the ledger holds them. -> (rows, why)

    ⚠ None, never []. "no ledger on this venue" and "a ledger with no owned rows" are opposite
    facts and only the second is a measurement. [[unknown-stays-unknown]]
    """
    p = path or os.path.join(HERE, LEDGER)
    if not os.path.isfile(p):
        return None, ("there is no vault accumulator on this venue - no sweep has banked anything "
                      "here, which is NOT the same as a sweep that found nothing")
    try:
        doc = json.load(io.open(p, encoding="utf-8"))
    except Exception as e:
        return None, "the vault accumulator could not be read (%s)" % str(e)[:70]
    if not isinstance(doc, dict):
        return None, "the vault accumulator is not a readable object (%s)" % type(doc).__name__
    rows = [r for r in (doc.get("owned") or []) if isinstance(r, dict)]
    return rows, ""


def regate(rows):
    """Side B — what today's law grants on the SAME evidence. -> (dict, why)

    ⚠ It re-runs the REAL gate with the REAL live constants. A private reimplementation of the
    witness rule would drift from the rule the write path enforces, and then this module would be
    comparing the ledger against a copy of the law rather than the law.
    """
    try:
        import vault_retro as VR
    except Exception as e:
        return None, "vault_retro could not be imported (%s)" % str(e)[:70]
    keeps, fails = [], []
    for r in rows:
        ev = r.get("witnesses") or []
        try:
            v = VR.gate(ev, VR.KEEP_CONF_FLOOR, VR.KEEP_MIN_WITNESSES)
        except Exception as e:
            # ⚠ a row whose gate RAISED is UNKNOWN, never a failure — a crashing check is not a
            # verdict about his data.
            return None, "the gate raised on %r (%s)" % (str(r.get("name"))[:40], str(e)[:60])
        (keeps if v.get("pass") else fails).append(
            {"name": r.get("name"), "witnesses": v.get("witnesses"),
             "sightings": v.get("sightings"), "why": str(v.get("why") or "")[:150]})
    return {"pass": keeps, "fail": fails,
            "bars": {"conf": VR.KEEP_CONF_FLOOR, "witnesses": VR.KEEP_MIN_WITNESSES}}, ""


def verdict(path=None):
    """Do the ledger and today's law agree about what he owns? -> dict

    ⛔ READS ONLY — no sweep, no apply, no prune, no paid read.
    """
    out = {"ok": False, "state": "UNKNOWN", "why": "", "n": None,
           "agree": None, "disagree": None, "bars": None, "ageS": None}
    rows, why = stored(path)
    if rows is None:
        out["why"] = why
        return out
    # age is CONTEXT and is gathered even when it plays no part in the verdict
    try:
        p = path or os.path.join(HERE, LEDGER)
        out["ageS"] = round(max(0.0, __import__("time").time() - os.path.getmtime(p)), 1)
    except Exception:
        out["ageS"] = None
    if not rows:
        out["ok"], out["state"], out["n"] = True, "AGREE", 0
        out["why"] = ("the accumulator holds no owned rows, so there is nothing claimed and nothing "
                      "to disagree with - measured, not unknown")
        return out
    got, why2 = regate(rows)
    if got is None:
        out["why"] = why2
        return out
    out["ok"] = True
    out["n"] = len(rows)
    out["agree"] = len(got["pass"])
    out["disagree"] = len(got["fail"])
    out["bars"] = got["bars"]
    out["failing"] = got["fail"][:8]
    if got["fail"]:
        out["state"] = "CONTRADICTION"
        out["why"] = ("%d of %d row(s) the ledger calls OWNED would NOT be granted by today's law "
                      "on their own evidence (needs %d witness(es) at conf %.2f). The console's "
                      "apply button posts no body, so the stored result is applied AS-IS - these "
                      "would land."
                      % (len(got["fail"]), len(rows), got["bars"]["witnesses"],
                         got["bars"]["conf"]))
    else:
        out["state"] = "AGREE"
        out["why"] = ("all %d owned row(s) still clear today's bar (%d witness(es), conf %.2f)"
                      % (len(rows), got["bars"]["witnesses"], got["bars"]["conf"]))
    return out


def report():
    v = verdict()
    print(u"VAULT WITNESS - %s" % v.get("state"))
    print(u"  %s" % v.get("why"))
    if v.get("ageS") is not None:
        print(u"  ledger age: %.1f h (context, not a verdict)" % (v["ageS"] / 3600.0))
    for r in (v.get("failing") or []):
        print(u"    %-34s %s witness(es) - %s" % (str(r.get("name"))[:34], r.get("witnesses"),
                                                  str(r.get("why"))[:70]))
    return 0 if v.get("state") == "AGREE" else (1 if v.get("state") == "CONTRADICTION" else 2)


if __name__ == "__main__":
    sys.exit(report())
