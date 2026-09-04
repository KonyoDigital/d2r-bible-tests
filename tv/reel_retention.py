"""v2001 — WHICH FOOTAGE HAS GIVEN UP ITS INFORMATION, AND MAY THEREFORE GO.

Konyo: "for storage optimization ... it should delete the oldest and older reel session after it
analyzes them and ledgers them and registers and they all get funneled properly as they should and
are." And, on keying it to swept + evidence banked: "its fine".

MEASURED FIRST, ON HIS 31 REELS (2026-08-23), because the obvious rule is the wrong one:

    read — evidence banked (pages>0)      6 reels    254 MB
    SEALED WITH 0 PAGES                  12 reels   1166 MB
    never swept                          13 reels   1058 MB

"Delete what has been swept" would take 18 reels and 1420 MB — and 1166 MB of that was **never
actually read**. A 0-page seal does not mean "done"; it means THIS READER FOUND NOTHING, and the
engine already knows it, because it reopens exactly those on its own:

    "🔓 8 reel(s) reopened - sealed with 0 pages by an older reader (now p1839)"

So the safe rule is the inverse of the obvious one: a reel is a candidate only once it has GIVEN
something up. Footage that has yielded nothing yet is the footage most worth keeping.

THE FIVE BARS, and every one of them exists because deleting his film cannot be undone:

  1. EVIDENCE BANKED     chronicle_swept says pages > 0. A 0-page seal is a re-read candidate.
  2. BOTH LANES SEALED   chronicle AND vault. A reel the vault has never swept still owes the vault
                         manager its stash rows, and vault_swept.json does not exist at all today —
                         which is why this reports ZERO candidates on his machine right now, and
                         that is the correct answer rather than a broken one.
  3. KEEP THE RECENT     the newest KEEP_RECENT reels stay whatever their state, so a bad sweep can
                         always be re-run against real footage.
  4. OLDEST FIRST        his words. It frees space in the order he asked for.
  5. FLOOR               it stops as soon as the target is met; it never empties the shelf.

IT DOES NOT DELETE UNLESS ASKED. `plan()` is pure and `main()` prints. Deletion needs --apply, and
--apply refuses without --yes, because the one thing worse than a full disk is a confident script
that removed the only copy of a Ber drop. [[unknown-stays-unknown]]
"""
import argparse
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

KEEP_RECENT = 5          # never touch the newest five, whatever the ledgers say
MIN_PAGES = 1            # "evidence banked" means at least one page was actually read


def _load(path):
    """{} for callers that do not need to tell the two empties apart. Use _load_state when it
    matters, and for a DELETER it always matters."""
    return _load_state(path)[0]


def _load_state(path):
    """(blob, state) where state is 'absent' | 'ok' | 'unreadable'.

    v2079 — THE HOLE THIS CLOSES, and it has been on origin since v2065. `_load` answered `{}` for
    both "this store has never been written" and "this store exists and will not parse", and those
    are opposite facts. ABSENT is a measurement: `vault_swept.json` genuinely does not exist on a
    tree that has never run a vault sweep, and this module's own prose says so. UNREADABLE is an
    UNKNOWN — the ledger might name every witness in the reel about to be deleted, and nobody can
    say, because nobody could open it.

    Collapsed, the consequence is concrete and it is not the safe direction: with an unreadable
    `vault_swept.json`, `_entry(vault, reel)` is None for EVERY reel, so every reel that a chronicle
    sweep has read falls past `ve is None and _vault_lane_owes(...)` — false for any reel that
    declared a chronicle focus — straight into `else:` and out as ELIGIBLE. Footage deleted on the
    strength of a file that could not be opened, with the report cheerfully saying "sealed by BOTH
    lanes". There is no un-delete.
    [[unknown-stays-unknown]] [[feedback-silence-is-not-evidence]]
    """
    if not os.path.exists(path):
        return {}, "absent"
    try:
        with open(path, encoding="utf-8") as fh:
            return (json.load(fh) or {}), "ok"
    except Exception:
        return {}, "unreadable"


def _entry(ledger, reel):
    """Reels are keyed BOTH ways in these files — `reel_<sid>` and bare `<sid>`. Checking one form
    only means a naming mismatch reads as 'never swept', which for a DELETER is the safe direction
    but for the report is a lie.

    ⚠⚠ REG-561 — AND `a or b` DEFEATED THAT FIX FOR A FALSY ENTRY. `ledger.get(x) or ledger.get(y)`
    treats a present-but-empty record as absent, and it does so ASYMMETRICALLY: measured, `{}`
    stored under `reel_s_1` returned None ("never swept") while the SAME `{}` stored under `s_1`
    returned it. **The same data under two spellings gave two different answers**, which is exactly
    the naming mismatch this function exists to remove. Membership, not truthiness.

    ⚠⚠ REG-563 — AND TWO PLACES IMPLEMENTED THIS ONE LOOKUP WITH OPPOSITE PRECEDENCE. This tried
    `reel` then the bare form; `reel_river`'s seal lookup tried the bare form then `reel`. Measured
    with BOTH keys present, the two returned DIFFERENT RECORDS for the same reel — the same
    copy-drift-of-a-meaning defect as REG-556's `ok`, where nothing was duplicated in text and two
    modules simply decided one question had two answers. One helper, one precedence, quoted by
    both. [[copy-drift]] §1

    ⚠ `str.replace("reel_", "", 1)` was also the wrong tool: it strips the substring ANYWHERE, so
    `"xreel_foo"` became `"xfoo"`. A prefix strip, not a replace.
    """
    return lookup_either_way(ledger, reel)


def bare_reel(reel):
    """`reel_<sid>` -> `<sid>`. A PREFIX strip, never a substring replace."""
    r = str(reel or "")
    return r[len("reel_"):] if r.startswith("reel_") else r


def lookup_either_way(store, reel):
    """The one rule for finding a reel's record in a store keyed BOTH ways. -> record or None

    PRECEDENCE: **the form you ASKED WITH wins**, then its alias. Ask with `reel_s_1` and the
    prefixed record wins; ask with `s_1` and the bare one does. `reel_river` quotes this rather
    than keeping its own order.

    ⚠⚠ REG-566 — THIS DOCSTRING SAID "the PREFIXED form first, then the bare one" AND THE CODE HAS
    NEVER DONE THAT. Measured against a store holding BOTH keys: asking with `reel_s_1` returned
    the prefixed record and asking with `s_1` returned the bare one — the asked form, both times.
    The stated rule and the real rule agreed only for the caller the deleter happens to use
    (`plan()` always asks with the directory name, which is prefixed), so nothing ever contradicted
    it.

    ⚠ AND THIS IS REG-564's CLASS ONE VERSION LATER — a comment contradicting the code it sits on —
    **in the docstring of the very function that fix produced.** The rule is now written as the
    code behaves, and a guard asks it BOTH ways so the two cannot drift apart again.

    ⚠ Membership, not truthiness (REG-561): a present-but-empty record is FOUND, not absent.
    """
    # ⚠⚠ REG-567 — AN EMPTY NAME RESOLVED TO AN EMPTY-STRING KEY. `bare_reel("reel_")` is `""`,
    # and this then looked `""` up in the store: `lookup_either_way({"": 5}, "reel_")` returned 5.
    # The phantom-key class one more time (REG-550, REG-559) — a name that names nothing must not
    # find a record. An empty name and an empty bare form are both simply not keys.
    r = str(reel or "").strip()
    if not r:
        return None
    if r in store:
        return store[r]
    b = bare_reel(r)
    if b and b != r and b in store:
        return store[b]
    # ⚠⚠ REG-565 — THE THIRD STEP RE-PREFIXED AN ALREADY-PREFIXED NAME. `"reel_" + r` was built
    # from the ORIGINAL name, so asking for `reel_s_1` against a store holding only
    # `reel_reel_s_1` RETURNED THAT DOUBLE-PREFIXED RECORD — a key this lookup should never be
    # able to reach. Found by a cold review of the shipped bytes. The prefixed form of a name that
    # already has the prefix is itself; only a BARE name gets one added.
    if r.startswith("reel_"):
        return None
    pref = "reel_" + r
    return store[pref] if pref in store else None


def _dir_mb(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total / (1024.0 * 1024.0)


_DURABLE = set()


def _reel_ts_key(reel):
    """The SESSION id a reel directory name carries. vault_swept is keyed by session, the plan
    iterates directories, and the two differ by the `reel_` prefix — matching them by eye is how a
    reel gets held or released for the wrong reason."""
    b = os.path.basename(str(reel or ""))
    return b[len("reel_"):] if b.startswith("reel_") else b


def _reel_ts(reel):
    """Sort key: the epoch ms embedded in reel_s_<ms>_<n>. Falls back to mtime, and a reel whose
    name cannot be parsed sorts NEWEST so it is the last thing anyone deletes."""
    try:
        return int(reel.split("_")[2])
    except Exception:
        return float("inf")


def _durable_sessions(here=None):
    """Sessions whose witnesses survive INDEPENDENTLY of the frames.

    v2056 — Konyo: "after the sweep ... data needs to be extracted and ledgered and counted for
    items as witnesses so when they get pruned they continue to exist on record."

    MIN_PAGES called it "evidence banked" and meant "at least one page was READ". Reading produces
    a PROPOSAL; only an apply puts rows in the ledger. Measured 2026-08-24: reel
    s_1787242455315_9654 had rows=7 in vault_swept and NOTHING in any durable store, so deleting it
    would have taken those seven witnesses with it.

    v2065 — AND THE RULE NOW HAS ONE HOME. v2062 built frame_authority to be "the one deletion
    authority" and then wired only the frame prune to it, leaving this — the deleter that removes
    WHOLE REELS — reading its own private copy of the same two stores. Two copies of one rule is how
    they drift, and these two already differed: this one swallowed an unreadable store silently
    (`except: continue`), so "no witnesses" and "could not read the ledger" were the same answer.
    They agreed on his tree the day this was written (5 sessions, identical set) — which is exactly
    when a duplicate is cheapest to remove and hardest to notice. [[copy-drift]]

    Still errs toward KEEPING: a store that will not parse contributes nothing here AND makes
    witness_index report ok=False, and the caller treats a non-durable reel as HELD. So "I could not
    read the ledger" can only ever hold a reel, never release one.
    """
    try:
        import frame_authority as _fa
    except Exception:
        # cannot ask the authority -> nothing is durable AND nothing is known
        return set(), False, "frame_authority could not be imported, so nothing can say which "\
                             "recordings are banked"
    idx = _fa.witness_index(here or HERE)
    # v2079 — and carry the authority's own `ok` instead of dropping it on the floor. It is False
    # when ANY durable store would not parse, and the sessions set is then a PARTIAL index. The
    # comment above argues a partial index can only hold reels; that is true of the rows-not-banked
    # branch and NOT true of a reel with no rows, which reaches `else:` untouched.
    bad = [k for k, v in (idx.get("perStore") or {}).items() if v is None]
    return (set(idx.get("sessions") or ()), bool(idx.get("ok")),
            ("%s will not parse" % ", ".join(sorted(bad))) if bad else None)


def _vault_lane_owes(reel_path):
    """Would the VAULT lane ever read this reel at all?

    v2042 — a reel that DECLARED a chronicle focus is not the vault lane's to read:
    `vault_retro.OWNERSHIP_SURFACES` deliberately excludes 'chronicle'. Holding such a reel until
    the vault sweeps it holds it FOREVER.

    Measured 2026-08-24: five reels declaring chronicle-uniques / chronicle-sets (250 MB) were kept
    on exactly that reason, waiting for a lane that was never going to come, while the disk sat at
    96%. A hold that can never be satisfied is not a hold, it is a leak.

    Errs toward KEEPING: an unreadable index, or no declared focus at all, still owes the lane.
    Deleting footage is irreversible and 'I could not tell' must never resolve to 'delete it'.
    """
    try:
        with open(os.path.join(reel_path, "index.json"), encoding="utf-8") as fh:
            ix = json.load(fh)
    except Exception:
        return True
    focus = str((ix or {}).get("focus") or "").lower()
    if not focus:
        return True
    try:
        import vault_retro as _vr
        surfaces = tuple(_vr.OWNERSHIP_SURFACES)
    except Exception:
        surfaces = ("stash", "inventory", "equipment", "runes", "gems", "materials")
    return focus in surfaces


_TRIAGE_CACHE = {"at": None, "store": None}


def _proven_empty(reel):
    """Has the FREE pass fully surveyed this reel and found no panel at all? -> bool

    ⚠ THIS IS THE ONE RULE ALLOWED TO OVERRULE "it has never been read", so it is deliberately
    the narrowest thing that can: a FULL pass (`full`), and ZERO frames on which any panel or
    stash screen was open. `retro_triage.survey` refuses to produce a disposal list from a
    sampled pass for the same reason, and this refuses to consult one.

    ⚠ NOT SURVEYED IS NOT EMPTY. A missing store, an unparseable one, a reel absent from it, or
    any exception all return False — which KEEPS the reel. The cost of being wrong here is
    footage with no un-delete, so the unknown case must fall on the keep side every time.
    [[unknown-stays-unknown]] [[feedback-suspect-the-instrument]]

    Why it is safe against BOTH lanes: the gate is stash_screen_open_cached, which answers with a
    tab name whenever a stash grid OR a chronicle panel is on screen. Zero of those across every
    frame means there is no page for the chronicle reader to read and no grid for the vault lane
    to bank — so `vault-owes` is satisfied too, which is why that rule is guarded as well.
    """
    try:
        import os as _os
        import retro_triage as _rt
        p = _rt._store_path()
        # ⚠ KEY THE CACHE ON (PATH, MTIME), NOT MTIME ALONE. The store path follows TV_HIST, so
        # it is NOT one fixed file: a harness and the live console resolve different ones. Keyed
        # on mtime alone, two stores whose timestamps happen to match would serve each other's
        # verdicts — and the consequence here is deleting footage that has no un-delete.
        key = (p, _os.path.getmtime(p))
        if _TRIAGE_CACHE["at"] != key:                # re-read only when the store actually moved
            # ⚠ load() RETURNS (store, ok), NOT a store. Calling .get() on that tuple raises, the
            # except below swallows it, and every reel comes back "not proven empty" — which is
            # INDISTINGUISHABLE from the deadlock this change exists to break. It got as far as a
            # sandbox run before anything noticed. `ok` False means the store could not be READ,
            # which is not "nothing surveyed": treat it as UNKNOWN and keep the footage.
            # [[unknown-stays-unknown]] [[feedback-silence-is-not-evidence]]
            store, ok = _rt.load()
            if not ok:
                return False
            _TRIAGE_CACHE["store"] = store
            _TRIAGE_CACHE["at"] = key
        rec = (_TRIAGE_CACHE["store"] or {}).get(reel)
        if not isinstance(rec, dict):
            return False
        return bool(rec.get("full")) and int(rec.get("panels") or 0) == 0
    except Exception:
        return False


# Every conclusion plan() can reach about a reel. Module-level since v2383 so reel_story can
# assert it has a stage for each one — see tv/test_reel_story.py.
RULES = ("no-witness-index", "ledger-unreadable", "test-fixture", "recent",
         "never-chronicle-swept", "zero-pages",
         "rows-not-banked", "vault-owes", "target-met", "eligible")


def plan(hist_dir=None, free_mb=None, keep_recent=KEEP_RECENT):
    """What may go, oldest first, and WHY every other reel stays. Writes nothing.

    free_mb: stop once this much has been selected. None = report every eligible reel.
    """
    hist = hist_dir or os.path.join(HERE, "frames", "hist")
    unreadable = []

    def _pick(fn):
        """First readable copy wins, and every UNREADABLE copy is named. A store that exists and
        will not parse is recorded even when a sibling copy answers, because the reason a caller
        wants to know is 'is my picture of the ledgers complete', not 'did I get a dict'."""
        # ⚠⚠ v2575 REG-570 — A FIXTURE COULD NOT REDIRECT THE DELETER'S LEDGERS, AND ELEVEN TEST
        # CALL SITES BELIEVED IT COULD. This searched HERE before `hist` unconditionally, so
        # `plan(hist_dir=<scratch>)` read Konyo's LIVE chronicle_swept (401 entries) and
        # vault_swept (30) instead of the caller's. Proven: a scratch ledger declaring pages=99
        # for three fixture reels produced `never-chronicle-swept: 3` — his store answered, the
        # fixture's was ignored. Setting TV_HIST did not help either; the read was anchored to
        # HERE and nothing else.
        #
        # The consequence is not a wrong number in a report — it is that every sabotage ever
        # aimed at this chooser was graded against live data it could not control, which is
        # exactly why four claimed defects in it could not be reproduced. [[feedback-fixtures-
        # never-touch-live-data]] guards the FIXTURE, not the call site — so the redirect happens
        # HERE, once, rather than in eleven tests remembering to.
        #
        # ⚠ THE DEFAULT PATH IS UNCHANGED. With no redirect the order is still HERE then hist.
        # Only a caller that explicitly repointed gets its own directory consulted first.
        _redirected = bool(hist_dir) or bool(os.environ.get("TV_HIST"))
        _order = ((os.path.join(hist, fn), os.path.join(HERE, fn)) if _redirected
                  else (os.path.join(HERE, fn), os.path.join(hist, fn)))
        # ⚠⚠ AND "FIRST READABLE WINS" IS WHAT THIS DOCSTRING ALWAYS SAID, while the code said
        # "first NON-EMPTY wins" (`if b and not blob`). They differ on the one case that matters:
        # a readable `{}` is a MEASUREMENT — nothing has been swept — and under the old rule a
        # stale non-empty sibling overruled it, so more reels looked swept and MORE FOOTAGE
        # became eligible. The docstring's rule holds footage; the code's rule released it.
        # [[unknown-stays-unknown]] [[feedback-comments-vs-code]]
        blob, picked = {}, False
        for cand in _order:
            b, st = _load_state(cand)
            if st == "unreadable":
                unreadable.append(os.path.relpath(cand, HERE))
                continue
            if st == "ok" and not picked:
                blob, picked = b, True
        return blob

    chron = _pick("chronicle_swept.json")
    vault = _pick("vault_swept.json")

    try:
        reels = sorted((d for d in os.listdir(hist) if d.startswith("reel_")), key=_reel_ts)
    except OSError as e:
        return {"ok": False, "why": "cannot read %s: %s" % (hist, e), "candidates": [], "kept": []}

    # v2056 — sessions whose witnesses survive without the frames, read ONCE per plan.
    global _DURABLE
    _DURABLE, _durable_ok, _durable_why = _durable_sessions(HERE)
    if not _durable_ok:
        # NAME THE REAL REASON. `_durable_sessions` returns ok=False both when a store will not
        # parse AND when frame_authority itself could not be imported — and saying "vault_accum.json
        # / vault_seen.json will not parse" about two perfectly readable files sends him to fix the
        # wrong thing. Right hold, wrong reason is still a wrong report.
        unreadable.append("the durable witness index could not be read"
                          if _durable_why is None else _durable_why)
    # v2122 (#32) — AND A TREE WITH NO INDEX AT ALL HOLDS TOO. frame_authority refuses to delete a
    # SINGLE FRAME when `haveIndex` is False — nothing there can prove a frame is not the only
    # record of what it saw — and this module, which deletes the WHOLE REEL those frames live in,
    # never asked: `haveIndex` appeared zero times in this file. `ok` is True for a complete
    # picture of NOTHING, so the two deleters disagreed by construction on the same footage, and
    # footage has no undo. [[unknown-stays-unknown]] [[feedback-contradiction-is-the-finding]]
    _have_index = False
    try:
        import frame_authority as _fa_idx
        _have_index = bool(_fa_idx.witness_index(HERE).get("haveIndex", True))
    except Exception:
        _have_index = False
    recent = set(reels[-keep_recent:]) if keep_recent else set()
    try:
        import frame_authority as _fa
        _fixtures = _fa.test_referenced_reels()
    except Exception:
        _fixtures = set()          # cannot ask -> hold nothing extra, but never hold LESS safely:
                                   # the other rules still apply and eligibility is unchanged
    candidates, kept, freed = [], [], 0.0

    # ── v2068 — A RULE THAT NEVER RUNS MUST SAY SO ─────────────────────────────────────────────
    # Every reason below is a REASON NOT TO DELETE, and they are checked in order, so an earlier
    # one hides every later one. MEASURED on his 35 reels: 12 never-swept, 11 sealed-with-0-pages,
    # 5 recent, 1 vault-owes, 6 eligible — and the v2056 rule ("this reel produced rows and none of
    # them are banked, so the frames ARE the record") fired ZERO times. On his data a working v2056
    # and a deleted one are indistinguishable, which is the mirror of a blind fixture: real data,
    # right gate, still green.
    #
    # So the plan now counts its own branches and names the ones that never ran. NEVER FIRED is
    # reported as UNMEASURED, never as "fine" and never as "broken" — this run simply contains no
    # reel that reaches it, and that is a fact about the footage, not about the rule.
    # [[gate-blind-to-unexercised-input]] [[unknown-stays-unknown]]
    # v2383 — the tuple now lives at MODULE scope (see RULES above). It stayed local for as
    # long as nothing outside plan() needed to know what this module can conclude; reel_story
    # draws a stage per verdict, so "every rule has a stage" is now a contract another file must
    # be able to check. A test that had to re-list these by hand would be a copy that drifts.
    # [[copy-drift]]
    # ⚠ v2316 — "not-extracted" WAS DECLARED HERE AND IS GONE. v2312 tried to make retention hold a
    # reel whose seal names nothing it took; that fix was WITHDRAWN (every existing seal predates
    # the contract, so the prune would never have fired again). The code went and the DECLARATION
    # stayed — an orphan tag no code path can ever reach, which coverage then reported as an
    # unmeasured rule for ever. A withdrawn change must take its declarations with it, or the
    # roster slowly fills with rules that describe work nobody does.
    # [[the-unjoined-end]] [[label-outlived-referent]]
    hits = dict((r, 0) for r in RULES)

    # v2383 — THE TAG TRAVELS WITH THE REEL, not only into the counter. `hits` says how many reels
    # were held for each reason; nothing said WHICH reason held THIS reel except the prose, so a
    # caller wanting to draw the lifecycle would have had to regex an English sentence. A reader
    # that pattern-matches prose is a guard on the sentence, not on the rule. [[source-reading-guard]]
    _last = [None]

    def _rule(tag, why):
        hits[tag] += 1
        _last[0] = tag
        return why

    for reel in reels:
        path = os.path.join(hist, reel)
        size = _dir_mb(path)
        # ⚠⚠ REG-562 — TWO DIFFERENT QUESTIONS, AND v2560 QUIETLY MERGED THEM. `_entry` was fixed
        # to return a present-but-EMPTY record faithfully (membership, not truthiness) because the
        # REPORT was lying about which reels had a ledger row. But the branches below ask
        # `ce is None` / `ve is None` to mean *this lane has not finished with the reel*, and after
        # that fix an empty `{}` stopped answering None — so a reel whose ledger row exists and
        # says NOTHING would skip the HOLD branches and fall toward releasable.
        #
        # Measured on his tree: chronicle_swept 401 entries, vault_swept 30, **0 falsy in either**,
        # so nothing moved today. That is luck, not design, and it is the DELETER. The report's
        # question is "is there a row?"; the deleter's question is "does the row SAY anything?" —
        # `_told` asks the second one, so an empty row holds exactly as an absent one does.
        def _told(e):
            return e if e else None

        ce, ve = _told(_entry(chron, reel)), _told(_entry(vault, reel))
        pages = int((ce or {}).get("pages") or 0)

        if not _have_index:
            why = _rule("no-witness-index",
                        "HELD — no durable witness store exists yet, so nothing here can prove "
                        "this reel's frames are not the only record of what it saw. The FRAME "
                        "deleter holds every frame in this reel for exactly that reason; a reel "
                        "deleter that released it would destroy what the frame deleter is "
                        "protecting.")
        elif unreadable:
            # v2079 — FIRST, and it holds EVERYTHING. Not a per-reel judgement: a ledger that will
            # not parse means this module's picture of what has been banked is unknown for every
            # reel at once, so there is no reel it can honestly release. Deliberately ahead of
            # test-fixture so the REPORT names the real reason rather than a coincidental one.
            why = _rule("ledger-unreadable",
                        "HELD — %s will not parse, so nothing here knows which witnesses are "
                        "banked. 'I could not read the ledger' is not 'there are no witnesses', "
                        "and footage has no un-delete. Fix or remove the file and re-run."
                        % ", ".join(sorted(set(unreadable))))
        elif reel in _fixtures:
            # ── v2069 — A REEL A TEST OPENS IS A FIXTURE, WHATEVER THE LEDGERS SAY ─────────────
            # Learned the expensive way, on a prune that had already run: six reels went as
            # "sealed by both lanes, has given up its information" and THREE were named by
            # tv/test_control.py. The suite did not go red — those cases skipTest when the footage
            # is absent — so a real check silently became a permanent skip.
            #
            # It had happened twice before and been absorbed: two cases already read "fixture reel
            # ... was pruned — PERMANENTLY skipped in both venues". Of the 17 reels the suite names,
            # EIGHT are already gone. Nobody was wrong at any step; the deleter asks the ledgers,
            # and the ledgers have no idea a test exists.
            # [[feedback-blind-fixture-green-gate]] [[gate-blind-to-unexercised-input]]
            why = _rule("test-fixture",
                        "the TEST SUITE opens this reel by name — deleting it does not turn a test "
                        "red, it turns one into a permanent skip, which is worse")
        elif reel in recent:
            why = _rule("recent",
                        "one of the %d most recent — kept so a re-sweep always has real footage"
                        % keep_recent)
        elif ce is None and not _proven_empty(reel):
            why = _rule("never-chronicle-swept",
                        "never chronicle-swept — it has not been read even once")
        elif pages < MIN_PAGES and not _proven_empty(reel):
            why = _rule("zero-pages",
                        "sealed with 0 pages — that is 'this reader found nothing', not 'done'; "
                        "the engine reopens these when the prompt improves")
        elif (ve or {}).get("rows") and _reel_ts_key(reel) not in _DURABLE:
            # v2056 — READ IS NOT BANKED. This reel produced rows and none of them reached a store
            # that outlives the frames, so deleting it destroys the only record of those witnesses.
            why = _rule("rows-not-banked",
                        "the sweep read %s row(s) here and NONE of them are in the ledger yet — the "
                        "witnesses live only in these frames, so this reel is the record. Apply the "
                        "vault proposal (or let a sweep write vault_seen.json) and it becomes "
                        "eligible." % (ve or {}).get("rows"))
        elif ve is None and _vault_lane_owes(path) and not _proven_empty(reel):
            why = _rule("vault-owes",
                        "the VAULT lane has never swept it — it still owes the vault manager its "
                        "stash rows" + ("" if vault else
                                        (" (vault_swept.json will not parse)" if unreadable
                                         else " (vault_swept.json does not exist yet)")))
        else:
            if free_mb is not None and freed >= free_mb:
                why = _rule("target-met",
                            "eligible, but the target was already met — this stops as soon as it can")
                kept.append({"reel": reel, "mb": round(size, 1), "why": why, "pages": pages,
                             "tag": _last[0]})
                continue
            # ⚠⚠ v2314 — I TIGHTENED THIS IN v2312 AND IT WAS AN OVER-CORRECTION. WITHDRAWN.
            #
            # After deleting 388.6 MB of his footage unattended on 2026-08-30 I made eligibility
            # require the seal to satisfy frame_authority's extraction contract. Three deliberate
            # cases went red, and they were right: EVERY seal on his tree predates that contract,
            # so the change would have stopped the prune firing on any existing reel — the exact
            # opposite of "automatically prune its not a question.. needs to be defaulted in".
            #
            # And re-examined honestly, the RULE was not the defect. reel_s_1786922954749_12579 had
            # 286 pages read by the chronicle lane and a vault seal confirming no stash screen
            # existed to take anything from. Both lanes were genuinely finished with it.
            # frame_authority is stricter because it answers a DIFFERENT question — may this FRAME
            # go, protecting the witness frames behind his vault rows — not may this REEL go. Two
            # authorities at two granularities is correct; collapsing them was my error.
            #
            # What actually went wrong that day was mine and not the code's: I swept a reel to
            # clear a backlog, which made it eligible, while telling him nothing could delete
            # because I had checked _PRUNE_SAFE_TO_RUN and not retention_may_act().
            # [[feedback-suspect-the-instrument]]
            freed += size
            candidates.append({"reel": reel, "mb": round(size, 1), "pages": pages,
                               "why": _rule("eligible",
                                            "read (%d pages) and sealed by BOTH lanes — it has "
                                            "given up its information" % pages),
                               "tag": "eligible"})
            continue
        kept.append({"reel": reel, "mb": round(size, 1), "why": why, "pages": pages,
                             "tag": _last[0]})

    # NOT REACHED and NOT APPLICABLE are two different answers, and only one of them is a gap.
    # `target-met` can only fire when a free_mb target was asked for; with no target it is
    # unreachable BY CONSTRUCTION, not unexercised by the footage. Reporting them together would
    # make a structurally-inert branch look like a rule that quietly stopped working.
    # `ledger-unreadable` is structurally inert on a healthy tree, exactly like `target-met` with no
    # target — reporting it as NEVER REACHED would train him to ignore the list that names real gaps.
    _na = set() if free_mb is not None else {"target-met"}
    if not unreadable:
        _na.add("ledger-unreadable")
    never = [r for r in RULES if not hits[r] and r not in _na]
    na = sorted(r for r in _na if not hits[r])
    return {"ok": True, "hist": hist, "candidates": candidates, "kept": kept,
            "freeMb": round(freed, 1), "onDisk": len(reels),
            "vaultLedger": bool(vault),
            # Published so a caller cannot repeat the mistake this fix corrects: an empty
            # `candidates` because everything is held reads identically to an empty one because
            # nothing was eligible, unless the reason is on the payload.
            "unreadable": sorted(set(unreadable)),
            "coverage": dict(hits), "neverFired": never, "notApplicable": na,
            "coverageSay": (("every rule this run could reach was exercised by the footage"
                             if not never else
                             "%d rule(s) were NEVER REACHED on these %d reel(s) — %s. That is "
                             "UNMEASURED, not fine and not broken: nothing in this footage gets far "
                             "enough down the chain to test them."
                             % (len(never), len(reels), ", ".join(never)))
                            + ("" if not na else
                               " (%s cannot fire without a free_mb target and is not counted as a "
                               "gap.)" % ", ".join(na))),
            # v2080 — AND `say` MUST NOT CONTRADICT `unreadable`. It branched on bool(vault),
            # which is falsy for BOTH an absent store and a corrupt one, so a ledger that would not
            # parse was reported to him as "vault_swept.json does not exist, so the vault manager
            # has never sealed anything." The `unreadable` field said the opposite two keys away —
            # and the sweep consumer (control_app.py) copies ONLY `say` onto his console, so the
            # true field never reaches a screen. The most alarming state was described as the most
            # innocent one. [[unknown-stays-unknown]] [[label-outlived-referent]]
            "say": ("%d reel(s) may go, freeing %d MB" % (len(candidates), round(freed))
                    if candidates else
                    "NOTHING is safe to delete yet — and that is an answer, not a failure. " +
                    ("%s will NOT PARSE, so every reel is held: nothing here knows which "
                     "witnesses are banked, and that is not the same as knowing there are none."
                     % ", ".join(sorted(set(unreadable))) if unreadable else
                     "no reel has been swept by BOTH lanes; vault_swept.json does not exist, so the "
                     "vault manager has never sealed anything." if not vault else
                     "every reel is recent, unread, or still owed to a lane."))}


def _tombstone_path(hist=None):
    """v2080 — RESOLVE AT CALL TIME, NOT AT IMPORT.

    `TOMBSTONE_PATH = os.path.join(HERE, ...)` was bound when the module loaded, so a test that
    repoints `rr.HERE` at a fixture tree — which every retention test does — still wrote its
    tombstones into HIS tree. The full gate run proved it: 89 tombstones carrying 2017 fixture
    stamps sitting in his real reel_tombstones.json, and the byte-identical canary caught the file
    moving during a run with his console down.

    Nothing of his was deleted (all 30 reels intact, and the 6 real entries are an earlier
    deliberate prune) — but a deleter's record of what it removed is not a file tests may write to,
    and "it happened to be harmless this time" is not a property to rely on.

    A constant computed at import is a fixture guard with a race built into it: the guard is only
    as good as the moment it was evaluated. [[feedback-fixtures-never-touch-live-data]]
    """
    # v2086 — AND IT ANSWERS FROM THE TREE BEING DELETED, when the caller knows which one that is.
    # It resolved from rr.HERE and TV_HIST only, so a caller that repointed NEITHER — passing
    # hist_dir straight to plan() — deleted from one tree and recorded the tombstones into HIS.
    # `_tombstone(hist, cands)` has always RECEIVED that path and ignored it. Not exercised today
    # (the suite patches the resolver, _retention_once sets TV_HIST) but a deleter's record of what
    # it removed should not be one indirection away from the footage it removed.
    # [[feedback-fixtures-never-touch-live-data]]
    if hist:
        # ⚠ `_under` is NOT in this module — it lives in tv_diablo, and the first cut called it
        # bare. That is a NameError, and the `except Exception: pass` right here would have
        # swallowed it and fallen through to the old behaviour: a guard that can never pass, hiding
        # inside its own error handling. The muleById defect, one more time.
        #
        # And it is imported rather than re-derived because v1897 says why: this comparison "was
        # written four times tonight as h.startswith(root + os.sep), and on Windows that is a coin
        # flip". His Windows machine is the other half of this project. [[copy-drift]]
        try:
            sys.path.insert(0, HERE)
            from tv_diablo import _under as _is_under
        except Exception:
            _is_under = None
        if _is_under is not None:
            try:
                h = os.path.realpath(hist)
                base = os.path.dirname(h) if os.path.basename(h) == "hist" else h
                if not _is_under(h, HERE):
                    return os.path.join(base, "reel_tombstones.json")
            except Exception:
                pass
    try:
        sys.path.insert(0, HERE)
        import tv_diablo as _tvd
        return os.path.join(_tvd._fixture_root(HERE), "reel_tombstones.json")
    except Exception:
        return os.path.join(HERE, "reel_tombstones.json")


TOMBSTONE_PATH = _tombstone_path()   # back-compat for readers; the writers call the function


def _filmed_ts(reel_dir, ix=None):
    """When was this reel FILMED? -> int ms, or None if nothing can say.

    Two sources, both measured at 40 of 40 on his shelf, asked cheapest-first:
      1. the frame NAMES — the recorder stamps every frame `f_<epoch-ms>.jpg`, which is the same
         pair `reconstruct_index` rebuilds a lost index from, so it survives a missing index;
      2. the index's own frame rows, whose `ts` is that stamp already parsed.

    ⚠ The EARLIEST stamp, not the latest: the question is when the reel began, and a reel is
    written over minutes. And None when neither answers — a guessed age on a deletion record is
    worse than an absent one. [[unknown-stays-unknown]]
    """
    best = None
    try:
        for f in os.listdir(reel_dir):
            if not (f.startswith("f_") and f.endswith(".jpg")):
                continue
            try:
                v = int(f[2:-4])
            except Exception:
                continue
            if v > 1e12 and (best is None or v < best):
                best = v
    except Exception:
        pass
    if best is not None:
        return best
    for row in ((ix or {}).get("frames") or []):
        if isinstance(row, dict) and isinstance(row.get("ts"), (int, float)) and row["ts"] > 1e12:
            v = int(row["ts"])
            if best is None or v < best:
                best = v
    return best


def _tombstone(hist, cands):
    """Write down what a reel WAS before its frames go.

    Konyo: "after the sweep ... data needs to be extracted and ledgered and counted for items as
    witnesses so when they get pruned they continue to exist on record."

    apply_plan used to rmtree and return a count, so a deleted reel left NOTHING behind — not its
    id, not how much was read from it, not why it was judged spent. The rows it produced live in the
    ledger, but the reel itself simply stopped having existed, and "I never recorded that" and "that
    was pruned in August" became the same answer.

    Written BEFORE the delete and flushed to disk, so a crash mid-delete leaves a record of MORE
    than was removed rather than less. Returns the rows it wrote; a failure here is reported and
    does NOT block the delete he asked for — but it is never silent.
    """
    rows = []
    for c in cands or []:
        d = os.path.join(hist, c["reel"])
        rec = {"reel": c["reel"], "session": _reel_ts_key(c["reel"]),
               "mb": c.get("mb"), "pages": c.get("pages"), "why": c.get("why"),
               "deletedTs": int(time.time() * 1000)}
        try:
            rec["frames"] = len([f for f in os.listdir(d) if f.endswith(".jpg")])
        except Exception:
            rec["frames"] = None          # UNKNOWN, never 0 — nobody counted
        try:
            with open(os.path.join(d, "index.json"), encoding="utf-8") as fh:
                ix = json.load(fh) or {}
            rec["focus"] = ix.get("focus") or None
            # ⚠⚠ REG-538 — THIS READ TWO KEYS NO INDEX HAS EVER CARRIED, and wrote None 410 times
            # out of 410. Measured on his shelf: 0 of 40 indexes carry `startedTs`, 0 carry `ts`.
            # So the one door with no undo recorded WHAT it deleted and WHEN it deleted it, and
            # never HOW OLD THE FOOTAGE WAS — the question you would actually ask after a bad
            # prune. Both real sources exist and both cover 40 of 40: the frame names, which the
            # recorder stamps as f_<epoch-ms>.jpg, and the index's own frame rows. Ask them, in
            # that order, and keep None only when neither can answer. [[unknown-stays-unknown]]
            rec["startedTs"] = (ix.get("startedTs") or ix.get("ts")
                                or _filmed_ts(d, ix) or None)
        except Exception:
            rec["focus"] = None
            rec["startedTs"] = _filmed_ts(d, None) or None
        rows.append(rec)
    try:
        old = _load(_tombstone_path(hist))
        prev = old.get("reels") if isinstance(old, dict) else None
    except Exception:
        prev = None
    blob = {"reels": (prev or []) + rows, "updatedTs": int(time.time() * 1000)}
    dest = _tombstone_path(hist)
    tmp = dest + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(blob, fh, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, dest)
    return rows


def apply_plan(p, yes=False):
    """Delete what plan() selected. Refuses without an explicit yes — this is not undoable."""
    if not yes:
        return {"ok": False, "why": "refusing to delete without --yes; run without --apply to read the plan"}
    # v2069 — THE RECORD GOES DOWN FIRST. Written before a single rmtree, so a crash halfway leaves
    # a tombstone for more reels than were actually removed rather than for fewer.
    tomb, tomb_why = None, None
    try:
        tomb = _tombstone(p["hist"], p.get("candidates") or [])
    except Exception as e:
        tomb_why = str(e)[:160]
    removed, failed = [], []
    for c in p.get("candidates") or []:
        path = os.path.join(p["hist"], c["reel"])
        try:
            shutil.rmtree(path)
            removed.append(c["reel"])
        except Exception as e:
            failed.append({"reel": c["reel"], "why": str(e)[:120]})
    return {"ok": not failed, "removed": removed, "failed": failed,
            "freedMb": p.get("freeMb", 0),
            "tombstoned": (len(tomb) if tomb is not None else None),
            "tombstonePath": _tombstone_path(p.get("hist")),
            "tombstoneWhy": tomb_why}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Which reels have given up their information.")
    ap.add_argument("--hist", default=None)
    ap.add_argument("--free-mb", type=float, default=None, help="stop once this much is selected")
    ap.add_argument("--keep-recent", type=int, default=KEEP_RECENT)
    ap.add_argument("--apply", action="store_true", help="actually delete (needs --yes)")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args(argv)

    p = plan(a.hist, a.free_mb, a.keep_recent)
    if not p["ok"]:
        print("refusing: %s" % p["why"])
        return 1
    print("%d reel(s) on disk in %s" % (p["onDisk"], p["hist"]))
    print(p["say"])
    if p["candidates"]:
        print("\nMAY GO (oldest first):")
        for c in p["candidates"]:
            print("   %-40s %6.1f MB  %s" % (c["reel"], c["mb"], c["why"]))
    print("\nKEPT, and why:")
    for k in p["kept"]:
        print("   %-40s %6.1f MB  %s" % (k["reel"], k["mb"], k["why"]))
    # v2068 — print the coverage LAST, where a verdict is read. A rule that never ran is the one
    # thing this plan cannot otherwise tell him, and it is exactly the thing that looks fine.
    print("\nRULE COVERAGE:")
    for _r, _n in p["coverage"].items():
        _tag = ("" if _n else ("   <- NEVER REACHED on this footage"
                               if _r in p["neverFired"] else "   (n/a without --free-mb)"))
        print("   %-24s %3d%s" % (_r, _n, _tag))
    print("   %s" % p["coverageSay"])
    if a.apply:
        r = apply_plan(p, a.yes)
        print("\n%s" % ("removed %d reel(s), freed %d MB" % (len(r["removed"]), round(r["freedMb"]))
                        if r["ok"] else r.get("why") or "some deletions failed"))
        for f in r.get("failed") or []:
            print("   FAILED %s — %s" % (f["reel"], f["why"]))
        return 0 if r["ok"] else 1
    return 0


if __name__ == "__main__":
    import console_safe  # noqa: F401 — emoji must survive a non-UTF-8 console
    sys.exit(main())
