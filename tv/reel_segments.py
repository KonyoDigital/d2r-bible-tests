#!/usr/bin/env python3
"""A REEL IS A TIMELINE OF ACTIVITIES, NOT A BAG OF FRAMES.

★ Konyo, and this module exists because of it: "shadow is on.. is reading every single frame.. and
retro reader also see every single frame ... how do they know to logically understand if im farming?
or teleporting? or just doing bosses or just trading? ... when it sees me in stash and inventory
open it knows that im stashing and it can flag the reel from that point and timestamp exactly to
logically start a different coding process."

Every reader today answers one frame at a time. That is why a judged item can arrive at the vault
with no idea where it was: the frame it was read from carries a name and a verdict, and the fact
that a Chronicle page was open at that moment lives in a DIFFERENT frame's read. Segmenting the
reel puts those two back together.

★ WHY THIS IS NOT A NEW READER. It adds no model call and no capture. It groups reads that already
exist into runs, and answers one question: WHAT WAS ON SCREEN AT THIS MOMENT. Everything downstream
— the vault's provenance gate, the chronicle-frame refusal, the locked-lane learner — is asking a
version of that question and each was answering it separately.

★ MEASURED ON HIS REELS BEFORE IT WAS WRITTEN, which is the only reason it is here:

    711 deep scene reads  ->  272 segments
        gameplay 212 · transition 27 · stash 13 · town 13 · inventory 4 · chronicle 3
        median span 4s, longest 516s

    the 84 names the kai JUDGE lane puts into the register, matched at ±0ms:
        frame-to-frame join      2 of 84      (the lanes use different frameId formats)
        SEGMENT membership      26 of 84      stash 11 · chronicle 10 · gameplay 3 · inventory 2

    TEN of those judged names were read while a CHRONICLE PAGE WAS OPEN. That is exactly the defect
    he reported — "most are chronicles read wrong as vault items" — identified by timestamp out of
    his own footage rather than argued about.

⚠ NO PADDING BY DEFAULT, and that is a decision. Widening the window to ±30s lifts coverage to 56
of 84, and 20 of the extra land in `gameplay` — which the route guard already teaches is "an
absence of a claim, not a rebuttal". Buying coverage with guesses is how a gate starts admitting
things nobody witnessed. [[unknown-stays-unknown]]
"""

# Two reads of the same activity further apart than this are two separate visits, not one.
# 120s because his stash sessions run minutes and his median segment is 4s — the gap has to be
# generous enough to survive a scroll and mean enough to end a visit.
SEG_GAP_MS = 120000

# What each activity says about WHERE an item read during it was. A container he owns -> a lane
# name the vault gate accepts. Everything else -> None, meaning "this moment does not establish
# possession", which is NOT the same as "it establishes absence".
#
# ⚠ chronicle is None ON PURPOSE and it is the whole point: a Chronicle page is a MENU listing
# items, most of which he does NOT have. Names read there are a checklist, never a holding.
_ACTIVITY_LANE = {
    "stash": "stash",
    "inventory": None,      # ⚠ see below — holding is not owning
    "chronicle": None,
    "loot": None,
    "town": None,
    "gameplay": None,
    "transition": None,
}

# ⚠⚠ v2346 — INVENTORY ALONE IS NOT POSSESSION, AND MAPPING IT AS SUCH WAS MY MISTAKE.
# v2343 shipped `"inventory": "inventory"`, which granted a container lane to anything read while
# only the inventory was open. Konyo corrected it, and he is right:
#
#   "when the inventory alone is open its just INVENTORY its not necessarily stashing it just yet..
#    it could have picked it up identified it for the CHRONICLE item and then thrown back out to
#    the ground if its worthless.. so these are happening in real time"
#   "only when its in STASH while both templates windows are open STASH on the left and INVENTORY
#    on the right side thats when we start usually stashing stuff"
#   "not until physically it is registered in the vault and has its slot identity pinpointed"
#
# So an item seen in the inventory is being HELD this second and may be on the ground a moment
# later. That is the exact failure he opened with — things he discarded sitting in his vault for
# ever — and it was mine.
#
# MEASURED, and his rule is visible in his own footage:
#     inventory segments   4 visits,  12 SECONDS total   <- a glance
#     stash     segments  13 visits, 235 seconds total   <- actual stashing
#     names this wrongly granted 'inventory': 8 — Storm Emblem, Cloudy Sphere, Small Charm of Good
#     Luck and five set pieces, which is precisely the pick-up-look-drop kind.
#
# ⚠ AND THE INVENTORY IS NOT WORTHLESS TO US — IT IS A DIFFERENT QUESTION. It holds his permanent
# furniture (the tomes, the Horadric Cube, his small charms), which is LOCKED: registered and
# synced, never moved. That is main_character.saw() / inventory_law.is_locked() territory, and it
# must not be confused with the vault's "does he own this" question. Two lanes, two purposes.
# ★ AND THE INVENTORY IS THE FRONT DOOR, WHICH IS WHY ITS SIGHTINGS MATTER. Konyo: "the first
# logical place any item can start is from INVENTORY first even before its a chronicle identified
# item. so it starts in INVENTORY." Every item is picked up there and IDENTIFIED there, then takes
# one of three exits:
#     ground -> INVENTORY -> STASH    kept; possession is claimed there, with a slot identity
#                         -> ground   discarded: gone from the inventory, and no stash was opened
#                         -> stays    furniture: tomes, Horadric Cube, small charms (locked BY NAME)
# So an inventory sighting is the START OF THE TRAIL, not a weak possession claim. Without it a
# discard cannot be observed at all — which is why lane_at() refuses it for the vault while
# feeds_the_lock_learner() still welcomes it. Two questions, one lane.
LOCK_LANES = ("inventory", "equipped")


def feeds_the_lock_learner(activity_or_lane):
    """Should sightings from here teach what is permanently HIS? -> (bool, why)

    Deliberately separate from lane_at(): the vault asks "does he own this", the lock learner asks
    "is this his furniture". v2343 answered both with one map and got the first one wrong.

    ⚠ IT TAKES EITHER VOCABULARY, AND SAYING SO IS THE FIX. A cross-family review noticed that
    "equipped" sits in LOCK_LANES and is not a SCENE — the scene vocabulary is
    town|stash|inventory|loot|gameplay|transition|chronicle — so if this only ever received a
    segment's activity, that branch could never fire. It is not dead: "equipped" is a names_loc
    value (equipped|inventory|stash|floor), which is the OTHER vocabulary in this pipeline, and a
    caller holding a per-name location is exactly who should be asking this question.
    Two vocabularies meeting in one function is fine; two vocabularies meeting SILENTLY is how a
    branch stops being reachable without anyone noticing.
    [[feedback-threshold-above-the-ceiling]] [[the-unjoined-end]]
    """
    activity = activity_or_lane
    act = str(activity or "").strip().lower()
    if act in LOCK_LANES:
        return True, "read while the %s was open — repeated sightings here earn a lock" % act
    return False, "%s is not a lane that teaches what is permanently his" % (act or "nothing")


def _ts(row):
    try:
        return int(row.get("captureTs") or row.get("ts") or 0)
    except (TypeError, ValueError, AttributeError):
        return 0


def segments(rows, gap_ms=SEG_GAP_MS):
    """Journal rows -> the reel's timeline. -> [{sid, start, end, activity, reads}]

    Only DEEP reads carry a scene, so only they can define a segment. The OCR lane stamps a
    provisional "loot" on every row it writes ("never farmed from OCR alone" — tv_diablo.py) and
    would flood this with an activity nobody observed, so it is excluded by lane, not by value.
    """
    seen = []
    for r in rows or []:
        if not isinstance(r, dict) or r.get("lane") != "deep":
            continue
        sc = str(r.get("scene") or "").strip().lower()
        t = _ts(r)
        sid = str(r.get("sessionId") or "").strip()
        # ⚠ NO SESSION, NO TIMELINE. A cross-family review pointed out that `or ""` puts every
        # session-less row in one bucket, so reads from unrelated sittings would merge into a
        # single fake visit and lend each other provenance they never had. MEASURED: all 711 of
        # his deep scene reads carry a sessionId today, so this drops nothing — it closes a door
        # that is currently unlocked rather than one currently being walked through.
        # A row that cannot say which sitting it belongs to cannot say what was on screen either.
        # [[unknown-stays-unknown]]
        if not sc or not t or not sid:
            continue
        seen.append((sid, t, sc))
    seen.sort(key=lambda x: (x[0], x[1]))

    out = []
    for sid, t, sc in seen:
        if out and out[-1]["sid"] == sid and out[-1]["activity"] == sc \
                and (t - out[-1]["end"]) <= gap_ms:
            out[-1]["end"] = t
            out[-1]["reads"] += 1
        else:
            out.append({"sid": sid, "start": t, "end": t, "activity": sc, "reads": 1})
    return out


def activity_at(segs, sid, ts, pad_ms=0):
    """What was on screen at this moment. -> (activity, segment) or (None, None).

    pad_ms defaults to 0 deliberately — see the module docstring. A caller that wants to trade
    honesty for coverage has to say so in its own code, where a reader can see it.
    """
    try:
        ts = int(ts or 0)
    except (TypeError, ValueError):
        return None, None
    if not ts:
        return None, None
    sid = str(sid or "")
    for s in segs or []:
        if s.get("sid") != sid:
            continue
        if (s.get("start", 0) - pad_ms) <= ts <= (s.get("end", 0) + pad_ms):
            return s.get("activity"), s
    return None, None


def lane_at(segs, sid, ts, pad_ms=0):
    """The container lane in force at this moment, or None. -> (lane, why)

    None is the answer for a Chronicle page, for gameplay, for town, and for a moment no segment
    covers — four different reasons, one honest answer, and the reason is returned beside it so a
    refusal can say WHICH of the four it was rather than going quiet.
    """
    act, seg = activity_at(segs, sid, ts, pad_ms=pad_ms)
    if act is None:
        return None, "no read covers this moment, so where it was seen is unknown"
    lane = _ACTIVITY_LANE.get(act, None)
    if lane:
        return lane, "read while the %s was open" % act
    if act == "chronicle":
        return None, ("read while the CHRONICLE was open — that page is a list of item names, "
                      "most of which he does not own, so it is a checklist and never a holding")
    if act == "inventory":
        return None, ("read while ONLY the inventory was open — that is holding, not owning. He "
                      "may have picked it up, identified it, and dropped it again. Possession is "
                      "claimed in the stash, once it is physically registered with a slot "
                      "identity")
    return None, "read during %s, which does not establish possession" % act


# ── THE SECOND WITNESS ────────────────────────────────────────────────────────────────────────
# Konyo: "chronicle menu page has a template it needs to be locating and cross referencing... that
# way it can never miscalculate a chronicle read item for a stash one... and watchdog and eagle eye
# and corroborator all working as one!"
#
# The scene above is ONE MODEL'S OPINION. stash_eye.classify_stash_grid() is a pixel fingerprint
# that runs with NO model at all, so it is a genuinely independent witness rather than a second
# look by the same eye.
#
# THE STRUCTURAL FACT IT LEANS ON IS HIS: "for the STASH theres a template automatically opens with
# the INVENTORY it cant even be open without the inventory they come together." A container panel
# shows a GRID. A Chronicle page is rows of names with no grid at all. So the question the pixels
# can answer without reading a word is: is there a container grid here?
#
# MEASURED ON HIS REELS, 58 frames, before this was written:
#     model said chronicle (2)  -> pixels said gameplay 2      no grid   ✓ agree
#     model said stash     (8)  -> pixels said stash* 8        grid      ✓ agree
#     model said gameplay (40)  -> pixels said gameplay 40     no grid   ✓ agree
#     model said inventory (3)  -> pixels said stash* 3        grid      ✓ agree (his rule: the
#                                                              inventory grid is a grid too)
# Wilson lower bound on those arms: gameplay 0.912, stash 0.676, chronicle 0.342 — all three are
# 100% raw, and Wilson is what stops 2-for-2 being reported as certainty. The chronicle arm is
# UNDER-EVIDENCED because only 2 chronicle frames survive on disk, which is a statement about the
# corpus and not about the method.

_GRID_ACTIVITIES = ("stash", "inventory")

# The pixel witness's CLOSED vocabulary, taken from stash_eye.classify_stash_grid's own docstring:
#   stash-runes | stash-gems | stash-materials | stash | gameplay
# ⚠ AN UNRECOGNISED LABEL IS "CANNOT TELL", NOT "NO GRID". The first cut tested
# pix.startswith("stash"), so any label the classifier might grow — and there are already two
# other functions in that file returning "shared" and "stash-<tab>" — would silently read as "no
# grid" and produce a confident WRONG verdict rather than an honest refusal. A witness that
# answers something you do not understand has not said no. [[unknown-stays-unknown]]
_PIX_GRID = ("stash", "stash-runes", "stash-gems", "stash-materials")
_PIX_NO_GRID = ("gameplay",)
# Activities where NO grid is the expected sight, so agreement is a positive result rather than a
# shrug. Konyo asked for the corroborator to work everywhere it can, and discarding a real
# agreement is throwing away the cheapest evidence there is.
_NO_GRID_ACTIVITIES = ("gameplay", "town", "transition")


def corroborates_chrome(activity, stash_tab, chrome_readable=True):
    """The scene read against the STASH TAB CHROME. -> (verdict, why)

    ★ THIS IS THE RIGHT SECOND WITNESS, and corroborates() below is the one that was not.

    control_app.stash_screen_open() reads the stash TAB CHROME out of a fixed band by OCR after a
    deliberate crop and 3x upscale, and resolves it to one of his real tabs. Its own docstring
    quotes him asking for exactly this: "it needs to be hardcoded and safegauded for vault manager
    to only when maybe i CLICK stash and am in my stash with my inventory open at the same time
    thats the template". The chrome only renders when the stash panel is open, and D2R draws the
    inventory beside it whenever it is — so that chrome IS his "both windows at once" template.

    ⚠ WHY IT REPLACED THE COLOUR FINGERPRINT. classify_stash_grid() fingerprints the stash CROP to
    guess WHICH TAB once you already know you are in the stash; it was never a detector for whether
    a container is open. Measured across his 1429 frames it produced 59 contradictions, and the two
    I opened — Nihlathak's Temple in town, and the Chaos Sanctuary mid-combat full of fire — have
    no stash panel at all. The chrome gate answers None on both, in 0.1s.

    Because it does not false-positive on bright scenes, the gameplay/town arm is now SAFE to rule
    on, which the colour witness could never support.

    `stash_tab` is the gate's answer: a tab name when the stash is open, None when it is not.
    `chrome_readable` is False when the gate could not be asked at all — an unreadable frame is
    CANNOT TELL, never "no stash". [[unknown-stays-unknown]]
    """
    act = str(activity or "").strip().lower()
    if not act:
        return None, "the scene witness did not answer, so they cannot be compared"
    if not chrome_readable:
        return None, "the tab chrome could not be read on this frame, so it cannot rule"
    open_now = bool(stash_tab)
    if act == "stash":
        if open_now:
            return True, "the read says stash and the stash chrome is showing (tab %r)" % (stash_tab,)
        return False, ("the read says stash but there is NO stash tab chrome — the panel that must "
                       "be open for that scene is not on this frame")
    if act == "inventory":
        # ⚠ INVENTORY IS NOT IN THE "must show stash chrome" ARM, AND THAT WAS MY BUG. The first
        # cut required chrome for both, and measured 3 contradictions that were nothing of the
        # sort. His rule says why: "THE INVENTORY itself can be opened separately with its own
        # template" — the inventory opens alone, and then there is no stash chrome to find.
        # Chrome present means he is STASHING (both panels, his "thats when we start usually
        # stashing stuff"); chrome absent means the inventory alone. Both are legitimate, so the
        # chrome witness cannot contradict an inventory read — it can only tell them apart.
        if open_now:
            return True, ("the read says inventory and the stash chrome is showing too (tab %r) — "
                          "both panels, which is stashing" % (stash_tab,))
        return True, "the read says inventory and no stash chrome — the inventory alone, which is his second template"
    if act == "chronicle":
        if open_now:
            return False, ("the read says chronicle but the stash chrome is showing (tab %r) — a "
                           "Chronicle page is not a container panel" % stash_tab)
        return True, "the read says chronicle and no stash panel is open"
    if act in _NO_GRID_ACTIVITIES:
        if open_now:
            return False, ("the read says %s but the stash chrome is showing (tab %r) — a panel "
                           "was open and the scene read missed it" % (act, stash_tab))
        return True, "the read says %s and no container panel is open" % act
    return None, "%s is not a template this comparison knows" % act


def corroborates(activity, pixel_label):
    """Do the model's scene and the pixels' own fingerprint agree? -> (verdict, why)

    verdict is True (agree), False (they contradict) or None (cannot tell) — three answers, because
    "the pixels could not be read" is not "the pixels disagree". A contradiction IS the finding and
    must never be averaged away into a shrug.
    """
    act = str(activity or "").strip().lower()
    pix = str(pixel_label or "").strip().lower()
    if not act and not pix:
        return None, "neither witness answered, so they cannot be compared"
    if not act or not pix:
        return None, ("the %s witness did not answer, so they cannot be compared"
                      % ("pixel" if act else "scene"))
    if pix in _PIX_GRID:
        pix_has_grid = True
    elif pix in _PIX_NO_GRID:
        pix_has_grid = False
    else:
        return None, ("the pixel witness answered %r, which is not a label this comparison knows "
                      "— that is CANNOT TELL, never 'no grid'" % pix)
    if act in _NO_GRID_ACTIVITIES:
        # ⚠⚠ THE PIXEL WITNESS MAY NOT RULE ON A NON-CONTAINER SCENE, AND I LEARNED THAT THE HARD
        # WAY. A cross-family review suggested corroborating gameplay positively (no grid expected,
        # no grid found) and it sounded free. Measured across ALL 1429 frames both witnesses saw:
        #     AGREE 682 · cannot tell 688 · CONTRADICT 59
        # and every one of the 59 was the same shape — the scene read said gameplay/transition/town
        # while the pixels claimed a container grid. I OPENED TWO OF THEM. One is Nihlathak's
        # Temple in town, one is the Chaos Sanctuary mid-combat with the screen full of fire.
        # Neither has a stash panel anywhere. The MODEL was right both times.
        #
        # classify_stash_grid is a colour/luminance fingerprint of the stash crop region, built to
        # guess WHICH TAB you are on once you already know you are in the stash. It was never a
        # detector for "is a container open", and a fire-lit dungeon in that crop fools it. So it
        # can CONFIRM a grid the scene read already claims; it cannot DISCOVER one.
        #
        # Enabling this arm would have manufactured 59 contradictions against frames that are fine
        # — a gate that cries wolf until it is switched off. [[feedback-suspect-the-instrument]]
        return None, ("%s is not a scene the pixel witness can rule on — it fingerprints the stash "
                      "crop and false-positives on bright gameplay (measured: 59 such frames)" % act)
    if act in _GRID_ACTIVITIES:
        if pix_has_grid:
            return True, "the read says %s and the pixels show a container grid" % act
        return False, ("the read says %s but the pixels show NO container grid (%s) — a stash "
                       "cannot be open without its grid" % (act, pix))
    if act == "chronicle":
        if pix_has_grid:
            return False, ("the read says chronicle but the pixels show a container grid (%s) — a "
                           "Chronicle page is rows of names, never a grid of icons" % pix)
        return True, "the read says chronicle and the pixels show no container grid"
    # gameplay / town / transition / loot: the pixels are not asked to rule on these
    return None, "%s is not a template the pixel witness can rule on" % act


def summarise(segs):
    """One line per activity: how many visits and how long. For the eagle and for a person."""
    import collections
    n = collections.Counter()
    ms = collections.Counter()
    for s in segs or []:
        n[s["activity"]] += 1
        ms[s["activity"]] += max(0, int(s.get("end", 0)) - int(s.get("start", 0)))
    return {a: {"visits": n[a], "totalMs": ms[a]} for a in n}


if __name__ == "__main__":
    import io, json, os, sys
    # This file prints non-ASCII (the arrows and rule marks in its own output) and the repo's
    # TestToolsCanReportTheirVerdict refuses a CLI that can crash while REPORTING on a non-UTF-8
    # console — a tool that dies explaining itself turns a clean tree into a non-zero exit.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from console_safe import enable as _console_safe_enable
        _console_safe_enable()
    except Exception:
        pass
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "sessions.jsonl")
    rows = []
    with io.open(p, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if isinstance(r, dict):
                rows.append(r)
    segs = segments(rows)
    print("%d rows -> %d segments" % (len(rows), len(segs)))
    for a, d in sorted(summarise(segs).items(), key=lambda kv: -kv[1]["visits"]):
        print("  %-11s %4d visit(s)  %8.1fs total" % (a, d["visits"], d["totalMs"] / 1000.0))
