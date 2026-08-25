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
    but for the report is a lie."""
    return ledger.get(reel) or ledger.get(reel.replace("reel_", "", 1))


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
        blob = {}
        for cand in (os.path.join(HERE, fn), os.path.join(hist, fn)):
            b, st = _load_state(cand)
            if st == "unreadable":
                unreadable.append(os.path.relpath(cand, HERE))
            if b and not blob:
                blob = b
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
    RULES = ("ledger-unreadable", "test-fixture", "recent", "never-chronicle-swept", "zero-pages",
             "rows-not-banked", "vault-owes", "target-met", "eligible")
    hits = dict((r, 0) for r in RULES)

    def _rule(tag, why):
        hits[tag] += 1
        return why

    for reel in reels:
        path = os.path.join(hist, reel)
        size = _dir_mb(path)
        ce, ve = _entry(chron, reel), _entry(vault, reel)
        pages = int((ce or {}).get("pages") or 0)

        if unreadable:
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
        elif ce is None:
            why = _rule("never-chronicle-swept",
                        "never chronicle-swept — it has not been read even once")
        elif pages < MIN_PAGES:
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
        elif ve is None and _vault_lane_owes(path):
            why = _rule("vault-owes",
                        "the VAULT lane has never swept it — it still owes the vault manager its "
                        "stash rows" + ("" if vault else
                                        (" (vault_swept.json will not parse)" if unreadable
                                         else " (vault_swept.json does not exist yet)")))
        else:
            if free_mb is not None and freed >= free_mb:
                why = _rule("target-met",
                            "eligible, but the target was already met — this stops as soon as it can")
                kept.append({"reel": reel, "mb": round(size, 1), "why": why, "pages": pages})
                continue
            freed += size
            candidates.append({"reel": reel, "mb": round(size, 1), "pages": pages,
                               "why": _rule("eligible",
                                            "read (%d pages) and sealed by BOTH lanes — it has "
                                            "given up its information" % pages)})
            continue
        kept.append({"reel": reel, "mb": round(size, 1), "why": why, "pages": pages})

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
            rec["startedTs"] = ix.get("startedTs") or ix.get("ts") or None
        except Exception:
            rec["focus"] = None
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
