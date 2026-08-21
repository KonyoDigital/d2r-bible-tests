#!/usr/bin/env python3
"""THE COUNTER-LEDGER — the game's own list of what he does NOT have.

WHY THIS EXISTS. Every reader in this project reads a FOUND page and proposes ADDITIONS. That
pipeline can only ever push the board's count up, so a row that is on the board and should not be
is invisible to all of it — there is no reading that can subtract. On 2026-08-21 that showed:
the board said 118/135 = 87% while the game's own Sets screen said 85%. Both numbers were
computed correctly. The board was carrying two pieces he does not own, and nothing in the
pipeline could have found them, because nothing in the pipeline ever reads a negative.

The game keeps that negative itself: the Chronicle's **Remaining** filter is the list of pieces he
does not have. Read once, it is worth more than a found page, because:

  * It FALSIFIES. A name on the board that appears here is wrong, and can be named.
  * It COMPLETES BY SUBTRACTION. The roster is 135 and the Remaining page was 19, so the 116 he
    owns are known EXACTLY, by name, with no model call — `owned_by_subtraction`.
  * It TARGETS. Those 19 are the whole of what is left to hunt, so a reader can keyword-search for
    them instead of re-reading pages of things already had.

THE HONESTY THIS MODULE IS MOSTLY MADE OF. A negative ledger accuses. That is its value and its
danger, and every guard below exists because an accusation is much more expensive to get wrong
than an omission:

  * **A reading has an age, and the age is the reading's, not the file's.** He plays between
    readings. A piece he found yesterday is on a two-day-old Remaining page and is not a defect.
    Every result carries `readAt`, `reel` and `ageDays`, and `contradicted()` splits a later find
    out of the accusation rather than counting it.
  * **`d2r_setPieces` IS AN UNDATED ARRAY OF STRINGS.** For most pieces there is no board-side date
    to order against the reading at all. That is UNKNOWN, and it is reported as `undated: True` on
    the row rather than resolved in either direction. An unmeasured order is not evidence for the
    accusation and it is not evidence against it.
  * **No reading is not agreement.** `load()` returns None, never an empty list. A consumer that
    treats "the game was never asked" as "the game agrees" is the exact failure this file was
    written to end.

Related: [[stale-reading]] · [[unknown-stays-unknown]] · tv/chronicle_calibrate.py (the same
watchdog from the other side — it reads the game's completion BAR, which needs no session but can
only ever produce a percentage; this file needs a session and produces NAMES).
"""
import glob
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()


def _dir():
    return os.environ.get("TV_REMAINING_DIR") or os.path.join(HERE, "remaining")


def _norm_piece(s):
    return " ".join(str(s or "").split())


def _set_roster():
    try:
        sys.path.insert(0, HERE)
        import chronicle_resolve as _res
        return _res.load_set_roster() or {}
    except Exception:
        return {}


def _folder(roster=None):
    """Return a fn mapping any spelling of a piece to its CANONICAL roster name.

    ⚠ THE DEFECT THIS EXISTS TO PREVENT, CAUGHT ON ITS FIRST RUN. The first cut of `denied()`
    compared proposal names directly against the reading's names and reported **"no proposed name
    appears on the game's missing list (86 checked)"** — a clean pass, from a check that could not
    possibly have failed. The pipeline carries set pieces under their BARE name (`M'avina's
    Caster`) while the roster and the Remaining page use the SUFFIXED one (`M'avina's Caster
    (helm)`). **Zero of those 86 names were roster strings.** Folding them first turns the same
    input into the one true hit, `Natalya's Soul (claws)` — the exact row found by hand.

    So the folding is not a convenience for callers, it is the guard's reach: a comparison between
    two naming conventions is a comparison that always agrees. Both sides go through here, and the
    roster is loaded by default so a caller cannot forget to pass it. [[source-reading-guard]]
    """
    ro = roster if roster is not None else _set_roster()

    def fold(n):
        nm = _norm_piece(n)
        if not nm:
            return None
        if ro:
            try:
                import chronicle_resolve as _res
                c = _res.canonical(nm, ro)
                if c:
                    return c
            except Exception:
                pass
        return nm

    return fold


def _age_days(read_at, now=None):
    """Days between the reading and now — None when the stamp cannot be parsed.

    An age that cannot be established is UNKNOWN, and says so by being None. It never silently
    becomes 0, which would read as "fresh" for a stamp nobody could parse.
    """
    if not read_at:
        return None
    try:
        s = str(read_at).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return round((now - dt).total_seconds() / 86400.0, 2)


def readings(ledger="sets"):
    """Every recorded reading for a ledger, newest first. [] when none were ever taken."""
    out = []
    for p in sorted(glob.glob(os.path.join(_dir(), "*.json"))):
        try:
            with open(p, encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        if str(d.get("ledger") or "sets") != ledger:
            continue
        rows = d.get("rows")
        if not isinstance(rows, list):
            continue
        names = []
        for r in rows:
            nm = r.get("piece") if isinstance(r, dict) else r
            nm = _norm_piece(nm)
            if nm:
                names.append(nm)
        if not names:
            # A file with a rows key and nothing in it is not "he is missing nothing" — it is a
            # recording that failed. Refusing it is the difference between an unread page and a
            # completed grail, which are opposite facts that look identical here.
            continue
        out.append({
            "ledger": ledger,
            "names": names,
            "count": len(names),
            "readAt": d.get("readAt"),
            "reel": d.get("reel"),
            "readBy": d.get("readBy"),
            "source": os.path.basename(p),
            "ageDays": _age_days(d.get("readAt")),
        })
    out.sort(key=lambda r: (str(r.get("readAt") or ""), r["source"]), reverse=True)
    return out


def load(ledger="sets"):
    """The newest reading, or **None** when the game has never been asked.

    None is the whole point of the return type. There is no empty-list answer here, because an
    empty list would mean "the game says he is missing nothing" — a strong claim — and that is not
    what "nobody has taken a reading" means.
    """
    rs = readings(ledger)
    return rs[0] if rs else None


def missing_names(ledger="sets", reading=None, roster=None):
    r = reading or load(ledger)
    if not r:
        return None
    fold = _folder(roster)
    return {c for c in (fold(n) for n in r["names"]) if c}


def owned_by_subtraction(roster, ledger="sets", reading=None):
    """The names he DOES have — roster minus the game's own missing list.

    Exact, and it costs nothing: no model call, no page read. It works only because the Remaining
    filter is a WHOLE-CATALOGUE negative — every piece is either on it or owned — so the complement
    is complete by construction rather than by sampling.

    Returns (owned:set, meta:dict). `meta['unresolved']` names any missing-row that is not a roster
    string; the subtraction is only exact when it is empty, and `meta['exact']` says which case
    this is instead of leaving the caller to guess.
    """
    r = reading or load(ledger)
    if not r:
        return None, {"why": "the game has never been asked — no Remaining reading on file"}
    names = set((roster or {}).values()) if isinstance(roster, dict) else set(roster or ())
    fold = _folder(roster if isinstance(roster, dict) else None)
    miss = {c for c in (fold(n) for n in r["names"]) if c}
    unresolved = sorted(miss - names)
    owned = names - miss
    return owned, {
        "rosterTotal": len(names),
        "missing": len(miss),
        "owned": len(owned),
        "unresolved": unresolved,
        "exact": not unresolved,
        "readAt": r.get("readAt"), "reel": r.get("reel"), "ageDays": r.get("ageDays"),
        "source": r.get("source"),
    }


def contradicted(board_names, ledger="sets", dates=None, reading=None, roster=None):
    """Which of the board's claimed-found names the game says he does NOT have.

    `dates` maps a piece name to when the BOARD believes it was found (any ISO string). It is
    optional and usually absent, because `d2r_setPieces` is a bare array of strings — which is
    exactly why the result distinguishes three states rather than two:

        contradicted  the board claims it, the game denies it, and nothing dates the claim after
                      the reading. These are the rows worth looking at.
        laterFinds    the board dates the find AFTER the reading was taken. Not a defect — he
                      found it since, and the reading is simply older than the fact.
        undated       carried on each contradicted row: no board-side date exists, so the ORDER of
                      the two is unestablished. The row still deserves a look; it does not deserve
                      to be called wrong on evidence nobody has.
    """
    r = reading or load(ledger)
    if not r:
        return {"ok": None, "reading": None,
                "say": "the game has never been asked for a Remaining page, so nothing is "
                       "compared — which is not the same as the board being right"}
    fold = _folder(roster)
    miss = {c for c in (fold(n) for n in r["names"]) if c}
    read_at = r.get("readAt")
    hits, later = [], []
    for nm in sorted({c for c in (fold(n) for n in (board_names or ())) if c}):
        if nm not in miss:
            continue
        d = (dates or {}).get(nm)
        if d and read_at and str(d) > str(read_at):
            later.append({"name": nm, "boardDate": d})
            continue
        hits.append({"name": nm, "boardDate": d, "undated": not d})
    out = {"ok": not hits, "contradicted": hits, "laterFinds": later,
           "checked": len(board_names or ()), "reading": {
               "readAt": read_at, "reel": r.get("reel"), "ageDays": r.get("ageDays"),
               "count": r.get("count"), "source": r.get("source")}}
    age = r.get("ageDays")
    aged = ("%.1f days old" % age) if age is not None else "of UNKNOWN age"
    if hits:
        undated = sum(1 for h in hits if h["undated"])
        out["say"] = (
            "⚠ THE GAME'S OWN REMAINING PAGE CONTRADICTS %d ROW(S) ON THE BOARD: %s. That page is "
            "%s, so a piece found since would show here wrongly%s."
            % (len(hits), ", ".join(h["name"] for h in hits), aged,
               " — and %d of them carry NO board-side date at all, so nothing establishes which "
               "came first" % undated if undated else ""))
    else:
        out["say"] = ("every name the board claims is consistent with the game's Remaining page "
                      "(%d checked against %d missing, page %s)"
                      % (len(board_names or ()), len(miss), aged))
    return out


def sighting_time(s):
    """The millisecond epoch a sighting was captured, or None.

    Reel ids are `s_<ms>_<n>` and frame files are `f_<ms>.jpg`, so a sighting timestamps itself and
    needs no side table. The FRAME is preferred: a reel is a whole session and its id is the moment
    it STARTED, which can be an hour before the frame that actually shows the item.
    """
    if not isinstance(s, dict):
        return None
    for key, pos in (("frame", 1), ("reel", 1)):
        v = str(s.get(key) or "")
        if not v:
            continue
        parts = v.replace(".jpg", "").replace(".png", "").split("_")
        for tok in parts[pos:]:
            if tok.isdigit() and len(tok) == 13:
                return int(tok)
    return None


def _reading_ms(reading):
    if not reading:
        return None
    v = str(reading.get("reel") or "")
    for tok in v.split("_"):
        if tok.isdigit() and len(tok) == 13:
            return int(tok)
    ra = reading.get("readAt")
    if ra:
        try:
            s = str(ra).replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        except Exception:
            return None
    return None


def denied(sightings_by_name, ledger="sets", reading=None, roster=None):
    """Proposed names the game itself says he does not have — TIME-ORDERED, which is the whole rule.

    A Remaining page is a photograph of one moment. He keeps playing. So "the game says he does not
    have it" is only an objection to a sighting the game LOOKED AT AFTER — otherwise a piece he
    found this evening gets denied by a page shot this morning, and the safeguard starts destroying
    exactly the finds it was built to protect.

    Three outcomes, and the third is the one that keeps this honest:

        denied      every sighting predates the reading. The game looked later and said no. This is
                    a real objection and the row should not be registered on this evidence.
        superseded  at least one sighting is NEWER than the reading. He found it since; the page is
                    stale for this row and the proposal stands.
        undated     no sighting carries a readable timestamp, so the ORDER IS UNKNOWN. Flagged for
                    his eyes, never auto-denied — an unmeasured order is not evidence, and treating
                    it as one would be the same mistake in the opposite direction.
                    [[unknown-stays-unknown]] [[stale-reading]]
    """
    r = reading or load(ledger)
    if not r:
        return {"ok": None, "denied": [], "superseded": [], "undated": [], "reading": None,
                "say": "no Remaining page on file, so no proposed name can be contradicted — which "
                       "is not the same as every proposed name being right"}
    fold = _folder(roster)
    miss = {c for c in (fold(n) for n in r["names"]) if c}
    ref = _reading_ms(r)
    den, sup, und = [], [], []
    # Fold FIRST, then merge: two spellings of one piece are one row with both their sightings, and
    # keeping them apart would let a name be denied on half its own evidence.
    merged = {}
    for nm, sights in (sightings_by_name or {}).items():
        c = fold(nm)
        if c:
            merged.setdefault(c, []).extend(sights or [])
    for name, sights in merged.items():
        if name not in miss:
            continue
        times = [t for t in (sighting_time(x) for x in (sights or [])) if t]
        if not times:
            und.append({"name": name, "why": "no sighting carries a readable timestamp"})
        elif ref is None:
            und.append({"name": name, "why": "the Remaining reading itself carries no usable time"})
        elif max(times) > ref:
            sup.append({"name": name, "seenMs": max(times), "readingMs": ref})
        else:
            den.append({"name": name, "seenMs": max(times), "readingMs": ref})
    out = {"ok": not den, "denied": den, "superseded": sup, "undated": und,
           "reading": {"readAt": r.get("readAt"), "reel": r.get("reel"),
                       "ageDays": r.get("ageDays"), "count": r.get("count"),
                       "source": r.get("source")}}
    bits = []
    if den:
        bits.append("⚠ THE GAME DENIES %d PROPOSED ROW(S): %s. Its own Remaining page was shot "
                    "AFTER these were seen and does not list them as found, so registering them "
                    "would put on your board something you do not have."
                    % (len(den), ", ".join(d["name"] for d in den)))
    if sup:
        bits.append("%d proposed row(s) are on that page but were seen AFTER it — you found them "
                    "since, so the page is simply older than the fact: %s."
                    % (len(sup), ", ".join(d["name"] for d in sup)))
    if und:
        bits.append("%d row(s) could not be ordered against the page at all (%s) — flagged for his "
                    "eyes rather than denied, because an order nobody established is not evidence."
                    % (len(und), ", ".join(d["name"] for d in und)))
    out["say"] = "  ".join(bits) or (
        "no proposed name appears on the game's own missing list (%d checked, %d of which fold "
        "onto a roster piece)" % (len(sightings_by_name or {}), len(merged)))
    return out


def resolve_contested(found_sightings, notfound_sightings):
    """A name read BOTH found and not-found: decide it by WHEN each look happened.

    THIS IS THE ONE THAT COST A WRONG ANSWER TO HIS FACE. On 2026-08-21 I told Konyo that **12 of
    his 36 proposed set pieces were ones the game shows as not-found**. Three of those carried First
    Found dates on his newest reel. The not-found readings were simply OLD — a negative observation
    from a page shot before he owned the item — and I quoted them as if they described today. The
    real number was one.

    A not-found reading is not a fact about the item. It is a fact about **the item at one moment**,
    and it expires the instant a later look disagrees. v1921 added the receipts (`notFoundSeen`
    carries reel, frame and lane per sighting) and even wrote the rule down in a comment — *"an
    older not-found reading is a perfectly ordinary thing when he has since found the item"* — and
    then compared the two sets as flat membership anyway. The knowledge was in the prose and not in
    the engine, which is the same as not having it.

    Four verdicts, and the last two are the honest ones:

        found        the newest look says FOUND. The not-found is older and expired. NOT a
                     contradiction, and it must never be quoted as one.
        not-found    the newest look says NOT FOUND. This is a real contradiction: the reader saw
                     it on a found page and the game said otherwise later.
        same-moment  both looks land on the same frame. The reader genuinely disagreed with itself
                     about one picture — the most informative row there is.
        undatable    at least one side carries no readable timestamp, so the order cannot be
                     established. It stays a flagged contradiction and is never resolved by guess.
                     [[unknown-stays-unknown]] [[stale-reading]]
    """
    fs = [t for t in (sighting_time(x) for x in (found_sightings or [])) if t]
    ns = [t for t in (sighting_time(x) for x in (notfound_sightings or [])) if t]
    out = {"foundMs": max(fs) if fs else None, "notFoundMs": max(ns) if ns else None,
           "foundLooks": len(found_sightings or []), "notFoundLooks": len(notfound_sightings or [])}
    if not fs or not ns:
        out["verdict"] = "undatable"
        out["say"] = ("read both ways and the two looks cannot be ordered (%s carries no readable "
                      "timestamp), so which came first is UNKNOWN"
                      % ("the found reading" if not fs else "the not-found reading"))
        return out
    if out["foundMs"] > out["notFoundMs"]:
        out["verdict"] = "found"
        out["say"] = ("the NEWEST look says found; the not-found reading is older and describes a "
                      "moment before that, so it is expired rather than contradictory")
    elif out["foundMs"] < out["notFoundMs"]:
        out["verdict"] = "not-found"
        out["say"] = ("the NEWEST look says NOT found, and it came after the found reading — this "
                      "is a real contradiction and the found reading is the suspect one")
    else:
        out["verdict"] = "same-moment"
        out["say"] = ("both readings land on the same frame — the reader disagreed with itself "
                      "about one picture, which no ordering can settle")
    return out


def resolve_all(proposal, ledgers=("uniques", "sets")):
    """Apply resolve_contested across a whole proposal.

    Returns {ledger: {name: verdict}}. Only `not-found`, `same-moment` and `undatable` are real
    contradictions; `found` names are resolved and must be dropped from any contested count, which
    is the entire point — a contested list padded with expired readings is how a wrong claim gets
    made with a straight face.
    """
    out = {}
    for led in ledgers:
        found = (proposal or {}).get(led) or {}
        nf_seen = ((proposal or {}).get("notFoundSeen") or {}).get(led) or {}
        nf_flat = set((proposal or {}).get("notFound", {}).get(led) or ())
        for nm in found:
            if nm not in nf_flat and nm not in nf_seen:
                continue
            r = resolve_contested(found.get(nm) or [], nf_seen.get(nm) or [])
            out.setdefault(led, {})[nm] = r
    return out


def arithmetic(board_found, roster_total, ledger="sets", reading=None):
    """board_found + game_missing vs the roster — the one line that started this.

    116 + 19 = 135 is a complete account and 118 + 19 = 137 is not, so the surplus IS the number of
    wrong rows, without needing to know which they are.
    """
    r = reading or load(ledger)
    if not r:
        return {"ok": None, "say": "no Remaining reading on file — the arithmetic cannot be done, "
                                   "and an arithmetic nobody did is not an arithmetic that agreed"}
    miss = int(r.get("count") or 0)
    total = int(roster_total or 0)
    surplus = int(board_found or 0) + miss - total
    out = {"boardFound": int(board_found or 0), "gameMissing": miss, "rosterTotal": total,
           "surplus": surplus, "impliedFound": total - miss,
           "reading": {"readAt": r.get("readAt"), "reel": r.get("reel"),
                       "ageDays": r.get("ageDays"), "source": r.get("source")}}
    if surplus == 0:
        out["ok"] = True
        out["say"] = ("the account closes: %d found + %d the game says are missing = %d, the whole "
                      "roster" % (out["boardFound"], miss, total))
    elif surplus > 0:
        out["ok"] = False
        out["say"] = ("⚠ %d found + %d missing = %d, which is %d MORE than the %d-piece roster. The "
                      "board is carrying %d row(s) the game says you do not have."
                      % (out["boardFound"], miss, out["boardFound"] + miss, surplus, total,
                         surplus))
    else:
        out["ok"] = False
        out["say"] = ("%d found + %d missing = %d, which is %d SHORT of the %d-piece roster — %d "
                      "piece(s) are on neither list, so something is unaccounted rather than "
                      "double-counted."
                      % (out["boardFound"], miss, out["boardFound"] + miss, -surplus, total,
                         -surplus))
    return out


def audit(evidence=None):
    """THE VALIDATOR — one call that says what this evidence is ALLOWED to conclude.

    Konyo, 2026-08-21, after I told him twelve of his rows were contradicted and the true number was
    one: *"needs to update and be refreshed maybe a mechanism that cheks AI that really syncs and
    works this has task or an engine that validates"*.

    The failure was not a bad reading. Every individual reading was fine. The failure was quoting
    readings whose AGE nobody had established, in a sentence that implied they described today. So
    what this reports is not "are the readings right" — it is **which questions this evidence can
    answer at all**, which is the thing nobody was asking.
    """
    if evidence is None:
        path = os.path.join(HERE, "chron_evidence.json")
        if not os.path.isfile(path):
            return {"ok": None, "say": "no banked evidence on this machine — nothing to audit, "
                                       "which is not the same as nothing being wrong"}
        with open(path, encoding="utf-8") as fh:
            evidence = json.load(fh)
    out = {"ledgers": {}}
    nf_total = nf_receipts = 0
    for led in ("uniques", "sets"):
        nf = list((evidence.get("notFound") or {}).get(led) or ())
        seen = (evidence.get("notFoundSeen") or {}).get(led) or {}
        nf_total += len(nf)
        nf_receipts += len(seen)
        res = resolve_all(evidence, ledgers=(led,)).get(led) or {}
        counts = {}
        for v in res.values():
            counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1
        out["ledgers"][led] = {
            "proposed": len(evidence.get(led) or {}), "notFound": len(nf),
            "notFoundWithReceipts": len(seen), "overlap": len(res), "verdicts": counts,
            "realContradictions": sorted(n for n, v in res.items() if v["verdict"] == "not-found"),
        }
    r = load("sets")
    out["remainingPage"] = ({"readAt": r.get("readAt"), "reel": r.get("reel"),
                             "ageDays": r.get("ageDays"), "count": r.get("count")} if r else None)
    out["notFoundDatable"] = (nf_total == 0 or nf_receipts >= nf_total)
    out["ok"] = out["notFoundDatable"] and out["remainingPage"] is not None
    bits = []
    if not out["notFoundDatable"]:
        bits.append("⚠ %d of %d not-found reading(s) carry NO reel or frame. NOTHING in this batch "
                    "may be quoted as contradicting a find — this is the exact evidence a wrong "
                    "claim of 12 was once made from, where the true number was 1."
                    % (nf_total - nf_receipts, nf_total))
    else:
        bits.append("every not-found reading carries a receipt and can be ordered (%d)" % nf_total)
    if out["remainingPage"] is None:
        bits.append("no Remaining page has ever been recorded, so the game cannot deny anything")
    else:
        age = out["remainingPage"].get("ageDays")
        bits.append("the game's Remaining page lists %d missing and is %s"
                    % (out["remainingPage"]["count"],
                       ("%.1f days old" % age) if age is not None else "of UNKNOWN age"))
    out["say"] = "  ".join(bits)
    return out


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    ledger = "sets"
    if "--ledger" in argv:
        ledger = argv[argv.index("--ledger") + 1]
    sys.path.insert(0, HERE)
    import chronicle_resolve as _res
    roster = _res.load_set_roster() if ledger == "sets" else _res.load_roster()
    if "--phantoms" in argv:
        # NAME THE WRONG ROWS. The arithmetic can say "the board carries 2 it should not" from the
        # counts alone; naming them needs the board's actual list, which lives in localStorage and
        # therefore needs his console open. That is a real dependency, not a missing feature — and
        # the honest thing is to say so in one line rather than to guess or to fail obscurely.
        try:
            sys.path.insert(0, HERE)
            import control_app as _ca
            own = _ca.board_ownership(400) or {}
        except Exception as e:
            print("could not reach the board: %s" % str(e)[:160])
            print("⚠ that is 'nobody asked the board', not 'the board is fine'.")
            return 2
        if not own.get("ok"):
            print("the board did not answer: %s" % str(own.get("why"))[:180])
            print("→ open TV DIABLO so the board window exists, then run this again.")
            return 2
        names = (own.get("sample") or {}).get("setPieces") or []
        found = int((own.get("counts") or {}).get("setPieces") or 0)
        if len(names) < found:
            print("⚠ the board reported %d set pieces but only listed %d — the sample was capped, "
                  "so a phantom could be hiding in the part nobody read." % (found, len(names)))
        c = contradicted(names, ledger)
        a = arithmetic(found, len(roster or {}), ledger)
        print(a["say"])
        print()
        print(c["say"])
        if c.get("contradicted"):
            print()
            print("  the rows to untick:")
            for h in c["contradicted"]:
                print("    %-42s %s" % (h["name"],
                      "no date on the board, so only the page's date orders them"
                      if h["undated"] else "board dates it %s" % h["boardDate"]))
        if c.get("laterFinds"):
            print()
            print("  found since the page was shot (these are fine): %s"
                  % ", ".join(x["name"] for x in c["laterFinds"]))
        return 0 if (c.get("ok") and a.get("ok")) else 1
    if "--audit" in argv:
        a = audit()
        print("WHAT THIS EVIDENCE CAN ANSWER")
        print()
        for led, v in (a.get("ledgers") or {}).items():
            print("  %-8s proposed %-4d  not-found %-4d (%d with receipts)  overlap %d  %s"
                  % (led, v["proposed"], v["notFound"], v["notFoundWithReceipts"], v["overlap"],
                     v["verdicts"] or ""))
            if v["realContradictions"]:
                print("           real contradiction(s): %s" % ", ".join(v["realContradictions"]))
        print()
        print("  %s" % a["say"])
        return 0 if a.get("ok") else 1
    r = load(ledger)
    if not r:
        print("no Remaining reading on file for %r." % ledger)
        print("⚠ That is 'the game was never asked', NOT 'the board is fine'.")
        return 0
    age = r.get("ageDays")
    print("newest reading: %s" % r.get("source"))
    print("  read at %s  from %s  (%s)"
          % (r.get("readAt"), r.get("reel"),
             ("%.1f days ago" % age) if age is not None else "AGE UNKNOWN"))
    print("  the game says you are missing %d piece(s)" % r["count"])
    owned, meta = owned_by_subtraction(roster, ledger, reading=r)
    print()
    print("  roster %d - missing %d = %d owned, by name%s"
          % (meta["rosterTotal"], meta["missing"], meta["owned"],
             "" if meta["exact"] else "  ⚠ NOT EXACT: %s unresolved" % meta["unresolved"]))
    if "--board" in argv:
        i = argv.index("--board")
        try:
            found = int(argv[i + 1])
        except Exception:
            print("  --board needs the board's found count")
            return 2
        a = arithmetic(found, meta["rosterTotal"], ledger, reading=r)
        print()
        print("  %s" % a["say"])
    if "--names" in argv:
        print()
        print("  still to find:")
        for nm in sorted(r["names"]):
            print("    %s" % nm)
    return 0


if __name__ == "__main__":
    sys.exit(main())
