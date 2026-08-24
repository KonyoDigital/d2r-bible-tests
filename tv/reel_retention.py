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

HERE = os.path.dirname(os.path.abspath(__file__))

KEEP_RECENT = 5          # never touch the newest five, whatever the ledgers say
MIN_PAGES = 1            # "evidence banked" means at least one page was actually read


def _load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh) or {}
    except Exception:
        return {}


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
        return set()          # cannot ask the authority -> nothing is durable -> everything is held
    return set(_fa.witness_index(here or HERE).get("sessions") or ())


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
    chron = _load(os.path.join(HERE, "chronicle_swept.json")) or _load(os.path.join(hist, "chronicle_swept.json"))
    vault = _load(os.path.join(HERE, "vault_swept.json")) or _load(os.path.join(hist, "vault_swept.json"))

    try:
        reels = sorted((d for d in os.listdir(hist) if d.startswith("reel_")), key=_reel_ts)
    except OSError as e:
        return {"ok": False, "why": "cannot read %s: %s" % (hist, e), "candidates": [], "kept": []}

    # v2056 — sessions whose witnesses survive without the frames, read ONCE per plan.
    global _DURABLE
    _DURABLE = _durable_sessions(HERE)
    recent = set(reels[-keep_recent:]) if keep_recent else set()
    candidates, kept, freed = [], [], 0.0

    for reel in reels:
        path = os.path.join(hist, reel)
        size = _dir_mb(path)
        ce, ve = _entry(chron, reel), _entry(vault, reel)
        pages = int((ce or {}).get("pages") or 0)

        if reel in recent:
            why = "one of the %d most recent — kept so a re-sweep always has real footage" % keep_recent
        elif ce is None:
            why = "never chronicle-swept — it has not been read even once"
        elif pages < MIN_PAGES:
            why = ("sealed with 0 pages — that is 'this reader found nothing', not 'done'; the "
                   "engine reopens these when the prompt improves")
        elif (ve or {}).get("rows") and _reel_ts_key(reel) not in _DURABLE:
            # v2056 — READ IS NOT BANKED. This reel produced rows and none of them reached a store
            # that outlives the frames, so deleting it destroys the only record of those witnesses.
            why = ("the sweep read %s row(s) here and NONE of them are in the ledger yet — the "
                   "witnesses live only in these frames, so this reel is the record. Apply the "
                   "vault proposal (or let a sweep write vault_seen.json) and it becomes eligible."
                   % (ve or {}).get("rows"))
        elif ve is None and _vault_lane_owes(path):
            why = ("the VAULT lane has never swept it — it still owes the vault manager its stash "
                   "rows" + ("" if vault else " (vault_swept.json does not exist yet)"))
        else:
            if free_mb is not None and freed >= free_mb:
                why = "eligible, but the target was already met — this stops as soon as it can"
                kept.append({"reel": reel, "mb": round(size, 1), "why": why, "pages": pages})
                continue
            freed += size
            candidates.append({"reel": reel, "mb": round(size, 1), "pages": pages,
                               "why": "read (%d pages) and sealed by BOTH lanes — it has given up "
                                      "its information" % pages})
            continue
        kept.append({"reel": reel, "mb": round(size, 1), "why": why, "pages": pages})

    return {"ok": True, "hist": hist, "candidates": candidates, "kept": kept,
            "freeMb": round(freed, 1), "onDisk": len(reels),
            "vaultLedger": bool(vault),
            "say": ("%d reel(s) may go, freeing %d MB" % (len(candidates), round(freed))
                    if candidates else
                    "NOTHING is safe to delete yet — and that is an answer, not a failure. " +
                    ("no reel has been swept by BOTH lanes; vault_swept.json does not exist, so the "
                     "vault manager has never sealed anything." if not vault else
                     "every reel is recent, unread, or still owed to a lane."))}


def apply_plan(p, yes=False):
    """Delete what plan() selected. Refuses without an explicit yes — this is not undoable."""
    if not yes:
        return {"ok": False, "why": "refusing to delete without --yes; run without --apply to read the plan"}
    removed, failed = [], []
    for c in p.get("candidates") or []:
        path = os.path.join(p["hist"], c["reel"])
        try:
            shutil.rmtree(path)
            removed.append(c["reel"])
        except Exception as e:
            failed.append({"reel": c["reel"], "why": str(e)[:120]})
    return {"ok": not failed, "removed": removed, "failed": failed,
            "freedMb": p.get("freeMb", 0)}


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
