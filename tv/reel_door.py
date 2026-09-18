# -*- coding: utf-8 -*-
"""v3312 (#65) — WHICH DOOR OPENED THIS REEL, as ONE definition every surface reads.

Konyo, 2026-09-18: *"the shadow reels that get shadow recorder they too need to be within the
river and seen visually just like the others"*.

⚠⚠ THE FIRST HALF OF THAT WAS ALREADY TRUE AND THE SECOND HALF WAS NOT, and it took three wrong
instruments to find out which. Shadow reaches its reel THROUGH `start_agent`
(control_app.py:24134), so a shadow reel is an ordinary reel — same hist dir, same index, same
seal — and nothing in shelf_driver / river / river_walk / reel_retention filters by door. They
have always flowed. What no surface could do is SAY which ones they are.

✅ THE RECORD EXISTS AND IS PROPERLY JOINED. v2687 built it: control_app exports `TV_DOOR` at
spawn (:1388) and pops it when the door cannot be named (:1390, never inherit a stale one),
tv_diablo reads it into `_DOOR`, and `test_entry_door_stamp.py` pins all three halves.
MEASURED on tv/sessions.jsonl (5,169 rows): door values shadow 761 · onair 759 · mini 2, with
1,522 rows carrying BOTH `sessionId` and `door`.

⚠ THE FIELD IS `door`, NOT `origin` — tv_diablo.py:553 is explicit, because `origin` already
names something else on the dispatch context ("settle" | "heartbeat" | "text-eye" | "farewell").
Reusing the word would put two quantities under one label. [[label-outlived-referent]]

⚠⚠ AND A DOORLESS REEL IS *UNKNOWN*, NEVER THE DEFAULT DOOR. 11 of his 19 reels predate the stamp
and carry no door row at all. Nothing here may infer "onair" from silence: absence of a record is
not evidence of the common case, and a manufactured provenance is worse than a missing one because
it cannot be told apart from a real one. [[unknown-stays-unknown]] [[manual-tally-is-witness]]

ONE DEFINITION, ON PURPOSE. The river and the shelf both need this, and v3308 is the standing
lesson: the eagle partition was written twice, drifted within an hour, and the screen said 9 while
the engine said 7. [[copy-drift]]
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

#: His play journal. Named once; callers may override for fixtures.
JOURNAL = os.path.join(HERE, "sessions.jsonl")

#: Every door the spawn may name. A value outside this set is reported AS ITSELF rather than
#: folded into "other" — an unexpected door is a finding, not a rounding error.
KNOWN_DOORS = ("onair", "shadow", "mini")


def door_map(journal=None):
    """sessionId -> door, read from the journal. -> (dict, why).

    ⚠ A journal that cannot be read returns ({}, why) and the caller must treat that as UNKNOWN
    for every reel — never as "they are all onair". An empty map and an unreadable one are
    different facts and the `why` is what tells them apart. [[zero-needs-a-denominator]]
    """
    path = journal or JOURNAL
    if not os.path.exists(path):
        return {}, "the journal is not on this machine (%s), so no reel can name its door" % (
            os.path.basename(path),)
    out, rows, bad = {}, 0, 0
    try:
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln.startswith("{"):
                    continue
                rows += 1
                try:
                    r = json.loads(ln)
                except Exception:
                    bad += 1
                    continue
                sid, door = r.get("sessionId"), r.get("door")
                if sid and door:
                    # ⚠ FIRST WRITER WINS, and it is the one that opened the session. A later row
                    # in the same session carries the same door today, but if one ever differed
                    # the OPENING row is the answer to "which door opened this reel".
                    out.setdefault(str(sid), str(door))
    except Exception as e:
        return {}, "the journal could not be read (%s)" % type(e).__name__
    why = "%d session(s) named a door across %d journal row(s)" % (len(out), rows)
    if bad:
        why += " · %d row(s) were unparseable and were skipped, never guessed" % bad
    return out, why


def door_of(reel, dmap):
    """The door that opened `reel`. -> str | None. None means UNKNOWN, never a default."""
    if not reel:
        return None
    name = os.path.basename(str(reel).rstrip("/"))
    sid = name[5:] if name.startswith("reel_") else name
    return (dmap or {}).get(sid)


def split(reels, dmap):
    """Count reels by door, keeping UNKNOWN as its own bucket. -> dict.

    ⚠ `unknown` is reported and never folded into a door. It is the honest home for the 11 reels
    that predate the stamp, and collapsing it would invent provenance for them.
    """
    out = {"unknown": 0}
    for r in (reels or []):
        d = door_of(r, dmap)
        if d is None:
            out["unknown"] += 1
        else:
            out[d] = out.get(d, 0) + 1
    return out


def say(counts):
    """One sentence a surface can print. -> str."""
    if not counts:
        return "no reels to attribute"
    known = [(d, n) for d, n in sorted(counts.items()) if d != "unknown" and n]
    unk = int(counts.get("unknown") or 0)
    head = ", ".join("%s %d" % (d, n) for d, n in known) or "no reel names a door"
    if unk:
        head += " · %d UNKNOWN (recorded before the door stamp; not assumed onair)" % unk
    return head
