#!/usr/bin/env python3
"""A machine's progress as BITS over a shared roster, so the fleet can subtract two ledgers.

WHY THIS EXISTS. Konyo: "for me and my cuzin alone it should cross reference eachother based on what
set items he has that i dont... show me what he has that i dont... so its not messy."

THE FLEET CARRIES COUNTS, AND 116 CANNOT BE SUBTRACTED FROM 120 TO PRODUCE NAMES. Something has to
travel per ITEM. But `functions/api/console.js` states a boundary in as many words —

    "No item names ever cross this boundary — a roster says how many, never which."

— and that boundary is worth keeping. So what travels is a BITMASK over a roster both machines
already have: bit i is set when this machine holds `roster[i]`. 135 set pieces become 18 bytes, and
the server stores an opaque string it never decodes. The subtraction happens on HIS machine, against
HIS copy of the roster, where the names already live.

⚠ THE ONE THING THAT MAKES THIS SAFE OR DANGEROUS IS THE ROSTER FINGERPRINT. A mask is meaningless
without the exact ordered list it was built against: if the roster gains a piece, every bit after
that index shifts, and a mask decoded against the wrong roster produces a confident, wrong list of
items his cousin is "missing". That failure is silent and it looks exactly like a working feature.
So every mask carries `v` — the roster's sourceHash prefix — and a decode against a different `v`
returns UNKNOWN rather than a guess. [[unknown-stays-unknown]] [[stale-reading]]

⚠ AND AN ABSENT MASK IS NOT AN EMPTY ONE. A machine that has never reported has no mask; that is
"we have not heard from him", not "he owns nothing". decode() answers None for absent and a list for
present, and the caller must render those differently — or the box will tell him his cousin is
missing all 135 pieces the first time it opens.
"""

import base64
import hashlib
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# how many characters of the roster's sourceHash ride along. Long enough that two real rosters
# cannot collide, short enough to keep the beacon small.
FINGERPRINT_LEN = 12

# a hard ceiling on what the wire will accept, so a malformed or hostile blob cannot be large.
# 4096 bits is ~30x the set roster and still only 700 bytes of base64.
MAX_BITS = 4096


def roster_fingerprint(source_hash):
    """The identity of the ordered list a mask was built against."""
    return str(source_hash or "")[:FINGERPRINT_LEN]


def load_roster(path=None, key="pieces"):
    """-> (ordered names, fingerprint) or (None, None) when the roster cannot be read.

    UNREADABLE IS NOT EMPTY: returning [] here would make every mask encode as all-zeros and the
    cross-reference would confidently report that nobody owns anything.
    """
    p = path or os.path.join(HERE, "set_roster.json")
    try:
        with io.open(p, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return None, None
    names = d.get(key)
    if not isinstance(names, list) or not names:
        return None, None
    return [str(n) for n in names], roster_fingerprint(d.get("sourceHash"))


def encode(owned, roster, fingerprint):
    """Which of `roster` this machine holds, as base64url bits. -> dict, or None if it cannot say.

    Bit i (LSB-first inside each byte) is roster[i]. Comparison is by EXACT name, deliberately: the
    roster is generated from bible.html by roster_sync.py and the board stores the same strings, so
    a fuzzy match here would paper over a roster drift that the fingerprint is supposed to catch.
    """
    if not roster or owned is None:
        return None
    have = {str(n) for n in owned}
    n = len(roster)
    if n > MAX_BITS:
        return None
    buf = bytearray((n + 7) // 8)
    hits = 0
    for i, name in enumerate(roster):
        if name in have:
            buf[i // 8] |= (1 << (i % 8))
            hits += 1
    return {"v": fingerprint, "n": n, "have": hits,
            "b": base64.urlsafe_b64encode(bytes(buf)).decode("ascii").rstrip("=")}


def decode(mask, roster, fingerprint):
    """-> (names, why). `names` is None whenever the answer would be a guess.

    Every refusal says WHY, because "he owns none of these" and "I could not read this" reach the
    same box and must never render the same.
    """
    if not isinstance(mask, dict):
        return None, "no mask reported by that machine yet"
    if not roster:
        return None, "this machine cannot read its own roster, so it cannot decode anyone's mask"
    got = str(mask.get("v") or "")
    if not got:
        return None, "the mask does not say which roster it was built against"
    if got != fingerprint:
        return None, ("that machine is on a different item roster (%s vs %s) — the bits would "
                      "line up with the wrong items, so the comparison is refused rather than "
                      "guessed" % (got, fingerprint))
    n = mask.get("n")
    if not isinstance(n, int) or n != len(roster):
        return None, ("the mask covers %r items and this roster has %d — refusing rather than "
                      "truncating" % (n, len(roster)))
    b = str(mask.get("b") or "")
    try:
        raw = base64.urlsafe_b64decode(b + "=" * (-len(b) % 4))
    except Exception:
        return None, "the mask is not readable base64"
    if len(raw) != (n + 7) // 8:
        return None, ("the mask is %d bytes and %d items need %d — refusing a partial read"
                      % (len(raw), n, (n + 7) // 8))
    out = []
    for i, name in enumerate(roster):
        if raw[i // 8] & (1 << (i % 8)):
            out.append(name)
    return out, None


def compare(mine, theirs, roster, fingerprint):
    """The whole point: what THEY have that I do not, and what I have that THEY do not.

    -> {"ok", "why", "theyHaveIDont": [...], "iHaveTheyDont": [...], "both": n, "mineN", "theirsN"}

    ⚠ EITHER SIDE UNKNOWN MAKES THE ANSWER UNKNOWN. Subtracting a list I could not read from one I
    could produces a complete, confident, wrong answer — every one of my items would look like
    something he is missing.
    """
    a, why_a = decode(mine, roster, fingerprint)
    b, why_b = decode(theirs, roster, fingerprint)
    if a is None:
        return {"ok": False, "why": "your side: %s" % why_a}
    if b is None:
        return {"ok": False, "why": "their side: %s" % why_b}
    sa, sb = set(a), set(b)
    return {"ok": True, "why": None,
            "theyHaveIDont": [n for n in roster if n in sb and n not in sa],
            "iHaveTheyDont": [n for n in roster if n in sa and n not in sb],
            "both": len(sa & sb), "mineN": len(sa), "theirsN": len(sb)}


def sanitize_for_wire(mask):
    """What a SERVER may store: shape only, never meaning. -> dict or None.

    The worker mirrors this in JS. It exists so a hostile or broken client cannot put anything
    large or strange into the fleet record, and so the server still never learns an item name.
    """
    if not isinstance(mask, dict):
        return None
    v = str(mask.get("v") or "")[:32]
    n = mask.get("n")
    b = str(mask.get("b") or "")
    have = mask.get("have")
    if not v or not isinstance(n, int) or n <= 0 or n > MAX_BITS:
        return None
    # base64url of ceil(n/8) bytes, unpadded
    want = ((n + 7) // 8 + 2) // 3 * 4
    if not b or len(b) > want or len(b) > 4096:
        return None
    if any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in b):
        return None
    out = {"v": v, "n": n, "b": b}
    if isinstance(have, int) and 0 <= have <= n:
        out["have"] = have
    return out
