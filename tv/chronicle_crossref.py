#!/usr/bin/env python3
"""IS THIS FIND ACTUALLY NEW, OR DOES HE ALREADY HAVE IT?

Konyo, 2026-08-29, looking at "📜 347 find(s) read from your reels — not in your ledger yet":
    "okay but did it cross reference what i currently already own? is it speaking and communicating
     to the console? im pretty sure i alread have those items... like didnt i already tally them
     manually or the chronicle readers the ON AIR already caught it? ... like some i did some the AI did"

He is right and it did not. Measured against his live ledger the same day: of 347 proposed names,
319 WERE ALREADY HIS and only 28 were new. The strip counted what the READERS PRODUCED and printed
it under a sentence about his LEDGER — a true number under a claim it cannot support.
[[label-outlived-referent]] [[unknown-stays-unknown]]

⚠ THIS MODULE DECIDES NOTHING AND WRITES NOTHING. It answers one question — which of these names
does he already have — and the board remains the only thing that writes the ledger (v1523).

⚠ AND "I COULD NOT ASK" IS NOT "THEY ARE ALL NEW". If the ledger cannot be read, `measured` is
False and the caller MUST render that rather than a count. A 347 that silently means "nobody
checked" is the defect this module exists to remove, and printing 347 with no ledger read is
exactly how it would come back.
"""
import re
import unicodedata

#: 202 of his item names carry a STRAIGHT apostrophe and 4 a CURLY one, and bible.html holds both
#: byte forms of the same names — measured 2026-08-29: Atma’s Scarab, Cat’s Eye, Death’s Web all
#: appear twice, once each way. Comparing raw bytes files the same item as two, which is how the
#: "28 new" inflates. [[d2r-curly-apostrophe-class]]


def canon(name):
    """The comparison key for one item name. NEVER the display name — that stays as he wrote it."""
    s = unicodedata.normalize("NFKC", str(name or ""))
    s = s.replace("’", "'").replace("ʼ", "'").replace("‘", "'")
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def _names(x):
    """A store may arrive as a list of names, a dict keyed by name, or a list of {name:…} rows."""
    out = []
    if isinstance(x, dict):
        out = list(x.keys())
    elif isinstance(x, (list, tuple)):
        for row in x:
            if isinstance(row, dict):
                n = row.get("name")
                if n:
                    out.append(n)
            elif row:
                out.append(row)
    return [str(n) for n in out]


def crossref(proposed, ledger):
    """Split a proposal against what he already has.

    `proposed` — {"uniques": [...], "sets": [...]} (names, or {name:…} rows).
    `ledger`   — {"foundLog": [...], "owned": [...], "setPieces": [...]} or None when UNREADABLE.

    Returns a dict. `measured` False means nobody could ask, and then `newCount` is None — never 0
    and never the proposed total, because both of those are answers and there is no answer.
    """
    prop_u = _names((proposed or {}).get("uniques"))
    prop_s = _names((proposed or {}).get("sets"))
    total = len(prop_u) + len(prop_s)

    if not isinstance(ledger, dict):
        return {"measured": False, "newCount": None, "alreadyCount": None,
                "proposedCount": total, "new": {"uniques": [], "sets": []},
                "already": {"uniques": [], "sets": []}, "dupesInProposal": 0,
                "why": "his ledger could not be read, so how many of these are new is UNKNOWN — "
                       "that is not the same as all of them being new"}

    have = set()
    for k in ("foundLog", "owned", "setPieces"):
        for n in _names(ledger.get(k)):
            have.add(canon(n))

    out_new = {"uniques": [], "sets": []}
    out_old = {"uniques": [], "sets": []}
    seen = set()
    dupes = 0
    for key, rows in (("uniques", prop_u), ("sets", prop_s)):
        for n in rows:
            c = canon(n)
            if c in seen:
                # the SAME item twice in one proposal — two byte forms of one apostrophe is the
                # way this happens, and counting it twice inflates the number he is shown
                dupes += 1
                continue
            seen.add(c)
            (out_old if c in have else out_new)[key].append(n)

    n_new = len(out_new["uniques"]) + len(out_new["sets"])
    n_old = len(out_old["uniques"]) + len(out_old["sets"])
    return {"measured": True, "newCount": n_new, "alreadyCount": n_old,
            "proposedCount": total, "new": out_new, "already": out_old,
            "dupesInProposal": dupes,
            "why": ("%d of the %d read are already in your chronicle; %d %s new"
                    % (n_old, total, n_new, "is" if n_new == 1 else "are"))}


def say(x):
    """The one line the strip shows. Refuses to name a number it does not have."""
    if not x.get("measured"):
        return "read from your reels — not yet checked against your chronicle"
    n = x["newCount"]
    if not n:
        return "read from your reels — you already have every one"
    return "read from your reels — %d not in your chronicle yet" % n
