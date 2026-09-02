#!/usr/bin/env python3
"""THE SECOND READER THAT SITS BETWEEN THE RETRO READERS AND GRADES THEM.

★ Konyo: "the retro analyzers need to be accurate and thorough with an extra AI reader if needed
inbetween them as a gated and accuracy checker", and before it: "make this a unified logic again
for everything related to the ai readers in retrospect.. everything in this lane needs their gaps
ungapped", "as additives to anything with a gap in the same lane".

WHAT THE GAP ACTUALLY WAS — measured across the retro lane before any of this was written:

    technique          vault_retro  chronicle_retro  live_miss_audit  slot_identity  prune_shadow
    tooltip crop           yes            -                -                -             -
    stash_eye grid          -             -                -                -             -
    enlarge (crop+3x)       -             -                -                -             -
    surfaces registry       -             -                -                -             -
    wilson/confluence      yes           yes               -                -            yes
    OCR worker              -             -               yes               -             -

Not ONE retro reader applied the enlarge toolkit. stash_eye owns prep_tab_chrome, the per-layout
prep_stash_grid and the 3x scale, and only the LIVE agent ever called them. So the retro pass —
which has all the time in the world and no frame to keep up with — read RAW pixels while the live
pass got prepared ones. That is backwards, and it is the whole gap.

HOW THIS CLOSES IT WITHOUT REWRITING ANYONE. Every retro sweep takes its reader as an ARGUMENT
(vault_retro.sweep(hist_dirs, sig=, reader=, classify=)). So the gate is a WRAPPER: hand it the
reader a lane already uses and it returns a reader that

    1. reads the frame the way that lane always did                     (nothing removed)
    2. ALSO reads the PREPARED frame — surfaces.prepare(), the declared crop+enlarge for that
       surface, the technique the retro lane never had                  (the gap, closed)
    3. compares the two and says whether they AGREE                     (the accuracy check)
    4. banks the outcome so the pair earns a Wilson score over time     (self-proving)

⚠ IT IS A GRADER, NOT A CENSOR. The wrapped reader returns the ORIGINAL reader's answer, always.
A disagreement is recorded, never silently substituted — because a second opinion that quietly
overwrote the first would make every downstream number unattributable, and nobody could tell which
reader produced the name they are looking at.

⚠ AND IT MUST NEVER RAISE INTO A SWEEP. A retro sweep walks hundreds of frames; an exception here
would cost a whole reel. Every failure path returns the original answer with a reason attached.

⚠ "COULD NOT ASK" IS NOT "THEY DISAGREED". If the prepared frame cannot be produced, or the second
read comes back empty, the verdict is UNKNOWN and it does not count in the Wilson denominator. An
unasked question is not a failed one. [[unknown-stays-unknown]]
"""
import io
import json
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
def _ledger_path():
    """v2423 — the same defect as shadow_ledger, capture_doors, disk_history and shadow_watch.

    CI's per-gate attribution named `retro_gate.json` as a file test_retro_gate writes; it resolved
    from HERE at import and so ignored the fixture root entirely. Resolved at CALL time now — an
    env honoured only at import is a redirect that silently does not take. In production TV_HIST is
    unset and this is exactly HERE, so nothing about his tree changes.

    ⚠ ImportError ONLY on the fallback: a blanket except would swallow a FAILING root rule and
    answer HERE, so a suite that set TV_HIST would write live believing it was isolated — which is
    the failure this exists to close.
    """
    try:
        import tv_diablo as _tvd
    except ImportError:
        return os.path.join(HERE, "retro_gate.json")
    return os.path.join(_tvd._fixture_root(HERE), "retro_gate.json")


#: kept so existing readers of the module attribute resolve; the CALLABLE is the source of truth.
LEDGER = os.path.join(HERE, "retro_gate.json")

#: verdicts. AGREE/DISAGREE are the only two that count as evidence.
AGREE = "agree"
DISAGREE = "disagree"
UNKNOWN = "unknown"


def normalise(name):
    """The comparison form of an item name. -> str

    ⚠ CURLY AND STRAIGHT APOSTROPHES ARE THE SAME LETTER TO A PERSON AND DIFFERENT BYTES TO A
    DICT. His own roster carries 202 straight and 4 curly, and that split has already cost this
    project a wrong mule for `Gheed's Fortune`. Two readers disagreeing about which quote mark the
    font used is not a disagreement about the ITEM, and grading it as one would poison the score
    with noise the reader cannot control.
    """
    s = str(name or "")
    for ch in ("\u2019", "\u02bc", "\u00b4", "`", "\u2018"):
        s = s.replace(ch, "'")
    s = re.sub(r"[^A-Za-z0-9' ]+", " ", s)
    return " ".join(s.lower().split())


def _load():
    try:
        with io.open(_ledger_path(), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save(d):
    try:
        tmp = _ledger_path() + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=1, sort_keys=True)
        os.replace(tmp, _ledger_path())
    except Exception:
        pass


def bank(lane, verdict, detail=None):
    """Record one graded read. Only AGREE/DISAGREE move the score."""
    if verdict not in (AGREE, DISAGREE, UNKNOWN):
        return
    d = _load()
    row = d.get(lane) or {}
    row[verdict] = int(row.get(verdict) or 0) + 1
    row["lastAt"] = int(time.time() * 1000)
    if detail:
        row["lastDetail"] = str(detail)[:160]
    d[lane] = row
    _save(d)


def report():
    """Per-lane agreement, Wilson-scored. -> dict

    k = the raw read and the prepared read named the same item.
    n = the times BOTH produced a name, so the question could actually be asked.
    UNKNOWN is reported beside them and excluded from n — nobody looked is not a failure.
    """
    try:
        from confidence import wilson_lower
    except Exception:
        try:
            from tv.confidence import wilson_lower
        except Exception:
            wilson_lower = None
    out = {}
    for lane, row in sorted((_load() or {}).items()):
        if not isinstance(row, dict):
            continue
        k = int(row.get(AGREE) or 0)
        bad = int(row.get(DISAGREE) or 0)
        n = k + bad
        w = None
        if wilson_lower is not None and n > 0:
            try:
                w = round(float(wilson_lower(k, n)), 3)
            except Exception:
                w = None
        out[lane] = {
            "agree": k, "disagree": bad, "judged": n,
            "unknown": int(row.get(UNKNOWN) or 0),
            "wilson": w,
            "say": ("no read has been graded in this lane yet — nothing is proved either way"
                    if n == 0 else
                    "%d of %d graded reads agreed · Wilson floor %.3f" % (k, n, w or 0.0)),
            "lastDetail": row.get("lastDetail") or "",
        }
    return out


def grade(raw_name, prepared_name):
    """Do the two reads name the same item? -> (verdict, why)"""
    a, b = normalise(raw_name), normalise(prepared_name)
    if not a or not b:
        return UNKNOWN, ("one side produced no name (raw=%r prepared=%r) — an unasked question is "
                         "not a failed one" % (raw_name, prepared_name))
    if a == b:
        return AGREE, None
    return DISAGREE, "raw read %r, prepared read %r" % (raw_name, prepared_name)


def gated(reader, surface, lane=None, second=None, work_dir=None):
    """Wrap a lane's reader so every read is ALSO taken from the prepared frame and graded.

    `reader`  the reader that lane already uses — unchanged, still authoritative.
    `surface` a key of surfaces.SURFACES; decides which enlarge is applied.
    `second`  the reader for the prepared frame. Defaults to `reader` itself, which is the
              cheap and honest default: the SAME eye on a BETTER image. Pass a different one to
              make it a genuinely independent second opinion.

    Returns a callable with the same shape as `reader`. It returns the ORIGINAL answer, always.
    """
    lane = lane or ("%s" % surface)
    second = second or reader

    def _read(frame_path, *a, **kw):
        try:
            out = reader(frame_path, *a, **kw)
        except Exception:
            raise                      # the lane's own reader failing is the lane's business
        try:
            import surfaces as _S
            prepared, why = _S.prepare(frame_path, surface, work_dir=work_dir)
            if not prepared or prepared == frame_path:
                bank(lane, UNKNOWN, why or "no prepared frame to compare against")
                return out
            alt = second(prepared, *a, **kw)
            verdict, detail = grade(_name_of(out), _name_of(alt))
            bank(lane, verdict, detail)
        except Exception as e:
            bank(lane, UNKNOWN, "the gate could not run: %s" % str(e)[:90])
        return out

    _read.__name__ = "gated_%s" % (getattr(reader, "__name__", "reader"),)
    return _read


def _name_of(v):
    """The item name out of whatever shape a reader returns. -> str

    Readers in this tree return a string, a dict with `name`, or a list of either. Guessing wrong
    here would grade two identical reads as a disagreement, so unknown shapes return "" and the
    verdict becomes UNKNOWN rather than DISAGREE.
    """
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        for k in ("name", "item", "text"):
            if v.get(k):
                return str(v[k])
        return ""
    if isinstance(v, (list, tuple)):
        for x in v:
            n = _name_of(x)
            if n:
                return n
    return ""



# ── THE THREE THINGS A READ CAN BE WRONG ABOUT ────────────────────────────────────────────────
#
# ★ Konyo: "what maybe does need an extra layer of accuracy might be a double checker for these
# same reels for when it does BYPASS THE WITNESSES based on my focusing this stash inventory run
# (not being shadow and letting AI analyze and work for understanding..) for like if its right on
# the FIRST analysis of what it read and WHERE it read and HOW it read it".
#
# THE BYPASS IS THE WHOLE REASON THIS EXISTS. The witness rule — three separate looks before a
# KEEP is believed — buys accuracy with REPETITION. A focused MINI does not have repetition to
# spend: he opened the stash himself, hovered each item once, and sealed. The run is trustworthy
# BECAUSE he aimed it, which is exactly why it is allowed to skip the witnesses; but skipping them
# removes the only accuracy mechanism the lane had. Something has to take their place on the FIRST
# analysis, and this is it.
#
# HIS OWN SESSION SHOWS ALL THREE FAILING, and they fail independently:
#   WHAT   "Rune Grip Ring" was read SIX times and registered as "Rune Grip" — the name truncated.
#   WHERE  that same register carries loc "floor" for an item that was in his stash.
#   HOW    "Crescent Moon" was read twice plus two garbles ('SHAELVmTIR', 'CkESCENT rn••N') and
#          registered nothing, because the reel had never been closed at all.
# One number ("registers: 4") hid three different defects. Grading them separately is what makes
# them separately fixable. [[feedback-contradiction-is-the-finding]]

WHAT = "what"
WHERE = "where"
HOW = "how"
DIMENSIONS = (WHAT, WHERE, HOW)


def _loc_of(v):
    """The location out of whatever shape a reader returns. -> str"""
    if isinstance(v, dict):
        for k in ("loc", "where", "container", "location"):
            if v.get(k):
                return str(v[k]).strip().lower()
    return ""


def grade_three(raw, prepared, expect_loc=None):
    """Grade one read on all three dimensions. -> {dim: (verdict, why)}

    `expect_loc` is what the RUN says it was looking at — a focused MINI declares `stash`, so a
    read that lands on `floor` inside a stash-focused reel is contradicting the run's own subject.
    That is a WHERE failure the name-level check cannot see, and it is exactly the "Rune Grip at
    loc floor" defect. When no focus was declared, WHERE is UNKNOWN rather than assumed correct —
    an undeclared run has nothing to contradict. [[unknown-stays-unknown]]
    """
    out = {}

    out[WHAT] = grade(_name_of(raw), _name_of(prepared))

    lr, lp = _loc_of(raw), _loc_of(prepared)
    if expect_loc:
        want = str(expect_loc).strip().lower()
        seen = lr or lp
        if not seen:
            out[WHERE] = (UNKNOWN, "neither read said where it was, so nothing contradicts the run")
        elif seen == want:
            out[WHERE] = (AGREE, None)
        else:
            out[WHERE] = (DISAGREE,
                          "the run was focused on %r and the read placed it at %r" % (want, seen))
    elif lr and lp:
        out[WHERE] = (AGREE, None) if lr == lp else (DISAGREE, "raw %r vs prepared %r" % (lr, lp))
    else:
        out[WHERE] = (UNKNOWN, "no declared focus and no location on both sides")

    # HOW: did the prepared image change the answer at all? Agreement here means the technique was
    # not load-bearing for this frame; disagreement means the enlarge MATTERED, which is the single
    # most useful thing this gate can tell anyone about whether the toolkit is worth its cost.
    a, b = normalise(_name_of(raw)), normalise(_name_of(prepared))
    if not a and not b:
        out[HOW] = (UNKNOWN, "neither the raw nor the prepared frame produced a name")
    elif a and b:
        out[HOW] = ((AGREE, None) if a == b
                    else (DISAGREE, "the prepared frame read %r where the raw frame read %r"
                                    % (_name_of(prepared), _name_of(raw))))
    elif b and not a:
        out[HOW] = (DISAGREE, "ONLY the prepared frame produced a name (%r) — the enlarge is "
                              "earning its cost on this frame" % _name_of(prepared))
    else:
        out[HOW] = (DISAGREE, "only the RAW frame produced a name (%r) — the enlarge LOST it, "
                              "which is a defect in the technique, not the reader" % _name_of(raw))
    return out


def bypassed_witnesses(focus=None, lane=None):
    """Is this run one that skips the witness rule and therefore NEEDS the double check? -> bool

    A run he AIMED — a MINI with a declared focus — is trusted on one look. Shadow and plain ON AIR
    are not aimed at anything, so they keep the witness rule and do not need this.
    """
    return bool(focus)


def bank_three(lane, graded):
    """Bank a three-dimension grade. Each dimension scores separately, because they fail
    separately — see the header. Lane keys are suffixed so one bad dimension cannot hide inside
    another's average."""
    for dim in DIMENSIONS:
        v = (graded or {}).get(dim)
        if not v:
            continue
        verdict, why = v
        bank("%s:%s" % (lane, dim), verdict, why)



# ── WHAT THE CLOCK KNOWS THAT NO SINGLE FRAME DOES ────────────────────────────────────────────
#
# ★ Konyo: "also a logic between timestamped reels and when they were extracted after being pruned
# maybe? like also this data can cross reference and be used as data and information to base an
# idea or an educated guess/analyzation for these items".
#
# MEASURED ON HIS OWN SESSION BEFORE BUILDING ANY OF IT, which is what makes it more than a nice
# idea. One read at 18:44:15 contained, together:
#
#     "Crescent Moon"          the clean name
#     "CkESCENT rn••N"         the SAME name, garbled
#     "'SHAELVmTIR'"           ShaelUmTir — that runeword's runes
#
# and across the session, "'SHAELVmTIR'" and "EASED ArtACX SpEE" (Increased Attack Speed) appeared
# together four times. So the noise is not scattered: it CLUSTERS around the item it came from,
# because a tooltip paints the name and its stats in one frame.
#
# THREE THINGS THAT FOLLOW, and each removes work rather than inventing it:
#   1. A garble sharing a read with a clean name is THE SAME ITEM. It must not become a second
#      register, and it must not be counted as an unread miss.
#   2. A stat line sharing a read with an item name BELONGS TO that item. "Increased Attack Speed"
#      is not a find; today it counted as text seen and never read.
#   3. Reads inside one session are one view of one stash, so a location established for any of
#      them is evidence about the others. That is what makes "Rune Grip at loc floor" visibly wrong
#      when everything around it says stash.
#
# ⚠ IT IS A GUESS AND IT SAYS SO. Co-occurrence is CORROBORATION, never identification: two things
# in one frame are related, and which one is the item is decided by the roster, not by this.
# Nothing here promotes a name on its own. [[unknown-stays-unknown]]

_STAT_WORDS = (
    "damage", "attack", "speed", "defense", "mana", "life", "resist", "durability",
    "requirement", "strength", "dexterity", "level", "chance", "wounds", "kill",
    "absorb", "static", "field", "striking", "cast", "enhanced", "increased",
    # v2320 — the CATEGORY line. D2R prints "Sword Class", "Staff Class", "Dagger Class",
    # "Polearm Class" under the name, and "STAff CLAs$" scored 0.82 as an item because it is
    # letters with one stray glyph. It is furniture of the tooltip, not a find. Found by running
    # the clusterer over his own reels and reading what it promoted.
    # ⚠ "charges" IS DELIBERATELY ABSENT. These match on a FOUR-character prefix so OCR damage
    # survives ("spee" -> speed), and "charges"[:4] is "char" — which matches CHARM. Adding
    # it reclassified every Grand Charm as a stat line, including "Graverobber's Grand
    # Charm", one of the items that actually registered from his session. A prefix short
    # enough to survive garbling is short enough to collide, so each word has to be checked
    # against the item vocabulary before it goes in. [[feedback-generalize-fixes]]
    "class", "socketed", "ethereal", "indestructible", "required", "repair",
)


def looks_like_a_stat(text):
    """Is this line a tooltip STAT rather than an item name? -> bool

    Deliberately generous on OCR damage: 'EASED ArtACX SpEE' has to read as a stat, and it does,
    because 'speed' survives as 'spee'. A false positive here costs one skipped register; a false
    NEGATIVE files a stat line as an item he owns, which is worse.
    """
    low = normalise(text)
    if not low:
        return False
    # ⚠ FOUR CHARACTERS, NOT FIVE, AND THAT IS THE WHOLE POINT. The first cut used w[:5], so
    # "speed" never matched "spee" — and his real frame reads "EASED ArtACX SpEE", where OCR
    # dropped the final letter of every word. The clusterer then chose that stat line AS THE ITEM
    # NAME and demoted "Crescent Moon" to a garble, reporting stats:[] on a frame that was almost
    # entirely stats. An empty stat list on a tooltip frame is the tell. [[source-reading-guard]]
    for w in _STAT_WORDS:
        if len(w) >= 4 and w[:4] in low:
            return True
    if re.search(r"\d", str(text or "")) and len(low) < 34:
        # a short line carrying a number, on a tooltip, is a stat far more often than a name —
        # "+183% Enhanced Damage", "10% Chance", "Required Level: 47"
        if "%" in str(text or "") or re.search(r"\b\d+\b", low):
            return True
    return False


def cluster(reads):
    """Group one frame's texts into (likely item name, its garbles, its stats). -> dict

    `reads` is the list of strings a single frame produced. The CLEANEST name wins: the longest
    string that is not a stat and normalises to mostly letters. Everything else in that frame is
    attributed to it as supporting text rather than treated as separate findings.
    """
    texts = [str(t or "").strip() for t in (reads or []) if str(t or "").strip()]
    if not texts:
        return {"name": "", "garbles": [], "stats": [], "why": "the frame produced no text"}
    stats = [t for t in texts if looks_like_a_stat(t)]
    rest = [t for t in texts if t not in stats]

    rest.sort(key=cleanliness, reverse=True)
    names = [t for t in rest if cleanliness(t) >= _NAME_FLOOR]
    garbles = [t for t in rest if t not in names]
    return {
        "name": (names[0] if names else ""),
        "names": names,
        "garbles": garbles,
        "stats": stats,
        "why": ("" if names else
                "nothing in this frame reads cleanly enough to be a name — the texts are kept as "
                "garbles rather than promoted"),
    }


_NAME_FLOOR = 0.62


def cleanliness(t):
    """How much does this look like a real item name? -> 0.0 .. 1.0

    ⚠ SCORED ON THE RAW STRING, NEVER THE NORMALISED ONE, AND THAT WAS MY BUG. The first cut
    measured normalise(t) — which STRIPS the punctuation that made a string dirty — so
    "DffiffJE.. tts I" scored as clean as "Death Mask" and then WON on length, because the score
    multiplied by length. His real 18:54 frame came back with the garbage as the item name.
    Normalising before judging cleanliness destroys the evidence you are judging.
    [[feedback-suspect-the-instrument]]

    Three things a D2R item name has and OCR garble does not:
      · almost no punctuation or digits
      · words that alternate case normally, not mid-word capitals like "DffiffJE" or "CkESCENT"
      · at least one word of real length
    """
    raw = str(t or "").strip()
    if len(raw) < 3:
        return 0.0
    letters = sum(1 for c in raw if c.isalpha())
    spaces = sum(1 for c in raw if c == " ")
    junk = len(raw) - letters - spaces
    if not letters:
        return 0.0
    score = letters / float(len(raw))                       # punctuation/digit density
    words = [w for w in raw.split() if w]
    odd = 0
    for w in words:
        core = w.strip("'\".,:;()[]")
        if len(core) < 2:
            continue
        # a capital appearing after a lowercase INSIDE a word is the signature of OCR damage
        for i in range(1, len(core)):
            if core[i].isupper() and core[i - 1].islower():
                odd += 1
                break
    if words:
        score *= (1.0 - 0.55 * (odd / float(len(words))))
    if junk > 2:
        score *= 0.55

    # ⚠ A SHOUTY FRAGMENT WAS SCORING A PERFECT 1.00. Measured on his own reels: "REQ", "KING",
    # "UNDEAD" and "RADIANCE" all came back 1.00 — higher than "Heart of the Oak" at 0.81 — because
    # they are pure letters with no punctuation and no mid-word capital, which is everything the
    # test above looks for. They are fragments of stat lines ("REQuired Level", "Area of KING
    # Leoric"), not items.
    #
    # A D2R item name is TITLE CASE and usually more than one word; the OCR's leftovers are
    # SHOUTED and short. Neither rule is safe alone — "RADIANCE" really is a runeword, and
    # "Shako" really is one word — so each is a penalty, not a veto, and a genuine one-word Title
    # Case name still clears the floor.
    letters_only = [c for c in raw if c.isalpha()]
    shouted = bool(letters_only) and all(c.isupper() for c in letters_only)
    if shouted:
        score *= 0.72                      # shouted: probably a stat fragment, not a name
    # ⚠ SHORT ALONE IS NOT THE SIGNAL — "Shako" IS A REAL UNIQUE. The first cut penalised any
    # single word of six characters or fewer and knocked Shako to 0.55, below the floor, which
    # would have dropped a genuine grail item. What separates "REQ" and "KING" from "Shako" is not
    # length, it is that the fragments are SHOUTED and the item name is Title Case. Both conditions
    # together, or neither.
    if len(words) == 1 and len(raw.strip()) <= 6 and shouted:
        score *= 0.55
    return max(0.0, min(1.0, score))


def corroborate_location(reads_in_session):
    """What location does the SESSION agree on? -> (loc, why)

    `reads_in_session` is a list of dicts that may carry `loc`. A single read placing an item on
    the floor while every other read in the same session says stash is contradicted by its own
    session — which is exactly the "Rune Grip at loc floor" defect, visible only from the clock.
    """
    seen = {}
    for r in (reads_in_session or []):
        l = _loc_of(r)
        if l:
            seen[l] = seen.get(l, 0) + 1
    if not seen:
        return None, "no read in this session said where it was"
    top = max(seen.items(), key=lambda kv: kv[1])
    if len(seen) == 1:
        return top[0], "every read in the session agreed on %r" % top[0]
    total = sum(seen.values())
    return top[0], ("the session is split %s — %r leads with %d of %d, so a read disagreeing with "
                    "it is worth a second look, not an automatic correction"
                    % (dict(seen), top[0], top[1], total))


def main(argv=None):
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    print("── THE RETRO ACCURACY GATE ──")
    rep = report()
    if not rep:
        print("  nothing graded yet — the gate has never been asked")
        return 0
    for lane, row in sorted(rep.items()):
        print("  %-22s %s" % (lane, row["say"]))
        if row["unknown"]:
            print("  %-22s   (%d could not be asked)" % ("", row["unknown"]))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
