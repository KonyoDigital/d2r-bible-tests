# -*- coding: utf-8 -*-
"""THE JOURNAL DRAIN — the half that WRITES, kept out of the half that JUDGES.

⚠⚠ v3113 — THIS MODULE EXISTS BECAUSE A LAW I ALREADY HAD SAID SO, AND I BROKE IT WITHOUT NOTICING.
`test_a_journal_row_leaves_only_on_proof.test_the_planner_cannot_write_anything` parses
`journal_retention.py` and refuses ANY write-capable call in it — "no open-for-write, no remove, no
rename, anywhere in the module" — because, in its own words:

    "the journal PLANNER can write. It exists to classify and explain; the apply half is a
     separate decision and it is his. There is no un-delete"

I then put `backup()` and `apply_plan()` INTO that module. The gate is registered in run_gates and
has been RED for several versions; I did not see it because I only ran the gates I was editing,
which is the same failure that put a SyntaxError on his console in v3100 — a law I did not run is a
law I did not apply. [[carved-skill-unloaded-is-unapplied]]

⚠ THE LAW IS RIGHT AND THE CODE WAS WRONG. Weakening it to "the plan() FUNCTION cannot write" would
have been me editing a safety rule to fit what I had already built — the exact shape I refused two
versions ago when a red law had to be RETIRED rather than deleted. Classify and delete are now
different modules, which is what the sentence asked for all along.

⚠ THE SAFETY PROPERTIES ARE UNCHANGED AND ALL STILL LIVE HERE: an explicit `yes=True`, a backup
written AND read back for every ring file BEFORE any rewrite, a refusal when the corpus moved since
the plan judged it, a per-file recheck immediately before each rewrite, and `os.replace` so a
truncate can never be observed. `reel_retention.apply_plan` deletes PIXELS and is gated behind a
LOCK; a journal row is different in exactly one way that matters — a timestamped copy restores it
perfectly — so the bar here is the verified backup rather than the lock.
"""
import io
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))

BACKUP_DIR = os.path.join(os.path.expanduser("~"), "d2r_journal_backups")


def backup(journal_path=None, stamp=None):
    """Copy the whole journal aside BEFORE anything leaves it. -> (path, rows) or (None, why)

    ⚠⚠ THIS IS WHAT MAKES THE RELEASE REVERSIBLE, AND REVERSIBILITY IS WHY THIS LANE MAY RUN AT
    ALL. reel_retention.apply_plan deletes PIXELS — "there is no undo" in its own words — so it is
    gated behind self_arming's `frame.release` lock and fails closed on any refusal. A journal row
    is different in exactly one way that matters: a timestamped copy of the file restores it
    perfectly. So the bar here is an explicit yes AND a verified backup, not a lock, and the
    difference is the undo rather than a judgement that rows matter less.

    Konyo asked for precisely this shape on the vault: "able to be brought back based on like last
    recent save ledger wise.. by day and timestamp". Same mechanism, one lane earlier.
    """
    # ⚠⚠ v3114 — NO DEFAULT PATH, BECAUSE THE TWO RESOLVERS ARE NOT THE SAME FILE. A
    # cross-family read of v3113 caught it: `_journal_path()` goes to tv_diablo.JOURNAL, which
    # honours TV_HIST for an isolated-hist run, while `_journal_paths()` goes to
    # replay.journal_paths(), which does NOT. So `backup()` with no argument snapshotted the LIVE
    # file while `apply_plan` went on to rewrite the whole ring — the rotated half with no backup
    # at all — and under TV_HIST they can be different files entirely. Every internal caller
    # already passes an explicit path; the ambiguous door is simply shut.
    # [[copy-drift]] [[unknown-stays-unknown]]
    if not journal_path:
        return None, ("backup() needs the file to copy — the planner and the drain resolve "
                      "'the journal' differently (tv_diablo.JOURNAL honours TV_HIST, "
                      "replay.journal_paths() does not), so a default here would snapshot one "
                      "file while the drain rewrote another")
    src = journal_path
    if not os.path.exists(src):
        return None, "there is no journal at %s to back up" % src
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
    except OSError as exc:
        return None, "could not make %s (%s)" % (BACKUP_DIR, exc)
    stamp = stamp or time.strftime("%Y-%m-%d_%H%M%S")
    # ⚠ v3106 — THE SOURCE'S OWN NAME, OR A RING BACKUP OVERWRITES ITSELF. This was
    # "sessions.%s.jsonl" % stamp, which is fine for ONE file and silently collides the moment
    # two ring generations are backed up in the same second — the second copy would land on the
    # first and the earlier file would have no backup at all while the log said it did.
    dst = os.path.join(BACKUP_DIR, "%s.%s" % (os.path.basename(src), stamp))
    try:
        with io.open(src, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        tmp = dst + ".part"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            fh.write(body)
        os.replace(tmp, dst)
    except Exception as exc:
        return None, "the backup did not write (%s: %s)" % (type(exc).__name__, exc)
    # ⚠ VERIFY IT LANDED. A backup nobody read back is a promise, not a safety net, and this is the
    # one line standing between a release and losing his history.
    try:
        n = sum(1 for _ln in io.open(dst, encoding="utf-8", errors="replace") if _ln.strip())
    except Exception as exc:
        return None, "the backup could not be read back (%s)" % exc
    # ⚠⚠ v3108 — "EMPTY COPY" AND "EMPTY SOURCE" ARE DIFFERENT FACTS, AND CONFLATING THEM BROUGHT
    # THE RIVER-CANNOT-DRAIN BUG BACK ONE LAYER DOWN. A cross-family read of v3106 found it: this
    # refused any 0-row backup, which is the right guard for "we failed to copy a file that HAD
    # rows" and the wrong one for a ring generation that was legitimately drained to nothing.
    # Once `sessions.1.jsonl` holds only doomed rows and is rewritten empty, EVERY later
    # apply_plan dies here — at the backup step, before the live file is touched — so the doomed
    # live rows stay forever and the drain reports a refusal it cannot explain.
    # The honest question is whether the COPY matches the SOURCE, not whether it is non-zero.
    # [[zero-needs-a-denominator]] [[unknown-stays-unknown]]
    try:
        src_n = sum(1 for _ln in io.open(src, encoding="utf-8", errors="replace") if _ln.strip())
    except Exception as exc:
        return None, "the source could not be counted for comparison (%s)" % exc
    if n != src_n:
        return None, ("the backup holds %d row(s) and the source holds %d — refusing to release "
                      "anything against a copy that does not match" % (n, src_n))
    return dst, n


def _late_lines(path, read_lines, doomed):
    """Rows appended to `path` after the first `read_lines` lines were read. -> [line]

    ⚠⚠ v3114 — THE CARRY-FORWARD, EXTRACTED SO A LAW CAN DRIVE IT. The second eye's High on v3113:
    `tv_diablo._journal_write` appends with NO LOCK, so a row written between the drain's read and
    its `os.replace` is published away — and the backup predates that row, so a restore does not
    bring it back. The drain would destroy a row that was never in the plan, and the realistic time
    to run a drain is while a session is recording.

    ⚠ IT DOES NOT CLOSE THE WINDOW AND MUST NOT CLAIM TO. Re-reading here narrows the gap from "the
    whole rewrite" to "between this call and the rename". A row landing inside THAT is still lost
    and cannot be saved without a lock the writer does not take. [[unknown-stays-unknown]]

    ⚠ AND A LATE ROW IS STILL JUDGED. If the recorder appends a row for a session the plan doomed,
    carrying it forward would resurrect exactly what the drain was asked to remove.
    """
    out = []
    try:
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except Exception:
        return []
    if len(lines) <= read_lines:
        return []
    for raw_line in lines[read_lines:]:
        raw = raw_line.strip()
        if not raw:
            continue
        try:
            sid = str((json.loads(raw) or {}).get("sessionId") or "")
        except Exception:
            out.append(raw_line)        # unparseable stays: it is not ours to judge
            continue
        if not (sid and sid in doomed):
            out.append(raw_line)
    return out


def apply_plan(p, yes=False, journal_path=None):
    """Remove the released sessions' rows from EVERY file the journal is read from. -> dict

    ⚠ REFUSES WITHOUT AN EXPLICIT YES, refuses if the backup did not verify, and — v3106 — refuses
    if the corpus MOVED since the plan judged it. The order is deliberate and is reel_retention's:
    every recoverable record goes down FIRST, so a crash halfway leaves backups covering MORE than
    was removed rather than fewer.

    ⚠⚠ v3106 — IT USED TO REWRITE ONE FILE OF A RING. `plan()` is fed the whole journal, which
    `replay.load_journal` has read as a generation ring since v779; this rewrote `tv_diablo.JOURNAL`
    alone. MEASURED on his tree: 2,483 of 2,840 sessions live in `sessions.1.jsonl`, so a release
    against any of them was a SILENT NO-OP that reported success. The river could not drain and
    nothing said why. [[the-unjoined-end]]
    """
    if not yes:
        return {"ok": False, "why": "refusing to rewrite the journal without yes=True; "
                                    "call plan() alone to read what WOULD go"}
    if not isinstance(p, dict) or not p.get("ok"):
        return {"ok": False, "why": "that is not a plan journal_retention produced"}
    doomed = {str(r.get("sessionId") or "") for r in (p.get("release") or []) if r.get("sessionId")}
    if not doomed:
        return {"ok": True, "removedRows": 0, "removedSessions": 0,
                "why": "the plan released nothing, so nothing was written"}

    targets = [journal_path] if journal_path else _jr()._journal_paths()
    if not targets:
        return {"ok": False, "why": "there is no journal to rewrite"}

    # ⚠⚠ THE CORPUS MUST BE THE ONE THE PLAN JUDGED. A plan is a judgement ABOUT a set of files;
    # applying it to a different set is how a correct decision lands on the wrong rows. This is
    # not hypothetical — it is exactly what happened on 2026-09-14, when a plan computed over the
    # ring was applied to the live file alone.
    if not journal_path:
        want = {(s.get("path"), s.get("rows")) for s in (p.get("sources") or [])}
        have = set()
        for t in targets:
            try:
                have.add((t, sum(1 for l in io.open(t, encoding="utf-8", errors="replace")
                                 if l.strip())))
            except Exception:
                have.add((t, None))
        if not want:
            return {"ok": False, "why": "this plan does not name the files it judged (it predates "
                                        "v3106) — re-run plan() before applying it"}
        if want != have:
            return {"ok": False,
                    "why": "the journal MOVED since this plan judged it — refusing.\n"
                           "   planned over: %s\n   on disk now  : %s"
                           % (sorted(want), sorted(have))}

    # ── every backup first, then every rewrite ──────────────────────────────────────────────
    stamp = time.strftime("%Y-%m-%d_%H%M%S")
    backups = []
    for t in targets:
        where, n_backed = backup(t, stamp=stamp)
        if where is None:
            return {"ok": False, "why": "NOT touching the journal — %s" % n_backed,
                    "backups": backups}
        backups.append({"of": t, "at": where, "rows": n_backed})

    # ⚠⚠ v3108 — THE CORPUS IS RE-CHECKED PER FILE, IMMEDIATELY BEFORE ITS REWRITE. The snapshot
    # above is taken once and `tv_diablo._journal_write` rotates the ring with `os.replace` and no
    # lock — live -> .1 -> .2 — so a rotation landing between the check and the write leaves this
    # rewriting the OLD paths while the doomed rows have moved a generation along. The eye
    # reproduced it: `ok: True` while the doomed generation is still in the ring. This cannot close
    # the window entirely without a lock the writer does not take, but it narrows it from "the
    # whole backup pass" to "between two statements", and a rotation caught here ABORTS instead of
    # reporting success. [[unknown-stays-unknown]]
    _want = {s.get("path"): s.get("rows") for s in (p.get("sources") or [])}

    dropped, sids, kept_total, wrote, carried = 0, set(), 0, [], 0
    for t in targets:
        if not journal_path and t in _want:
            try:
                _now_n = sum(1 for _l in io.open(t, encoding="utf-8", errors="replace")
                             if _l.strip())
            except Exception as exc:
                return {"ok": False, "why": "%s vanished between the backup and the rewrite (%s) — "
                                            "%d file(s) already rewritten, backups at %s"
                                            % (t, exc, len(wrote), BACKUP_DIR),
                        "backups": backups, "rewrote": wrote}
            if _now_n != _want[t]:
                return {"ok": False,
                        "why": "%s changed between the backup and the rewrite (%s rows planned, "
                               "%s now) — the ring rotated underneath this apply. %d file(s) "
                               "already rewritten, backups at %s"
                               % (t, _want[t], _now_n, len(wrote), BACKUP_DIR),
                        "backups": backups, "rewrote": wrote}
        kept = []
        _read_lines = 0
        try:
            with io.open(t, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    _read_lines += 1
                    raw = line.strip()
                    if not raw:
                        continue
                    try:
                        sid = str((json.loads(raw) or {}).get("sessionId") or "")
                    except Exception:
                        kept.append(line)      # unparseable stays: it is not ours to judge
                        continue
                    if sid and sid in doomed:
                        dropped += 1
                        sids.add(sid)
                    else:
                        kept.append(line)
        except Exception as exc:
            return {"ok": False, "why": "%s could not be read (%s) — %d file(s) already rewritten, "
                                        "backups at %s" % (t, exc, len(wrote), BACKUP_DIR),
                    "backups": backups, "rewrote": wrote}
        # ⚠ ATOMIC. A plain open(path, "w") TRUNCATES before anything is written, so a crash
        # between those two moments leaves him with an empty history and a backup he does not
        # know to look for.
        tmp = t + ".part"
        try:
            with io.open(tmp, "w", encoding="utf-8") as fh:
                fh.writelines(kept)
            # ⚠⚠ v3114 — CARRY FORWARD ANYTHING THE RECORDER APPENDED WHILE WE WERE WRITING.
            # The second eye's High on v3113, and it is the worst failure this module could have:
            # `tv_diablo._journal_write` appends with NO LOCK, so a row written between our read
            # and this `os.replace` is published away — and the backup was taken BEFORE that row
            # existed, so a restore does not bring it back either. The drain would destroy a row
            # that was never in the plan. That is the realistic case: he runs this while a session
            # is recording.
            #
            # ⚠ THIS DOES NOT CLOSE THE WINDOW AND MUST NOT CLAIM TO. It re-reads the source after
            # writing the replacement and appends any line that arrived since, which narrows the
            # gap from "the whole rewrite" to "between this re-read and the rename" — microseconds
            # instead of seconds. A row landing inside THAT is still lost, and it cannot be made
            # zero without a lock the writer does not take. Said out loud rather than implied.
            # [[unknown-stays-unknown]] [[the-unjoined-end]]
            _late = _late_lines(t, _read_lines, doomed)
            if _late:
                with io.open(tmp, "a", encoding="utf-8") as fh:
                    fh.writelines(_late)
                carried += len(_late)
            os.replace(tmp, t)
        except Exception as exc:
            try:
                os.remove(tmp)
            except OSError:
                pass
            return {"ok": False, "why": "the rewrite of %s failed (%s) — that file is untouched; "
                                        "backups at %s" % (t, exc, BACKUP_DIR),
                    "backups": backups, "rewrote": wrote}
        kept_total += len(kept)
        wrote.append({"path": t, "kept": len(kept)})

    return {"ok": True, "removedRows": dropped, "removedSessions": len(sids),
            "carriedForward": carried,
            "keptRows": kept_total, "backups": backups, "rewrote": wrote,
            "say": "released %d row(s) across %d session(s) from %d file(s); %d row(s) remain. "
                   "Restore with: %s"
                   % (dropped, len(sids), len(targets), kept_total,
                      " && ".join("cp %s %s" % (b["at"], b["of"]) for b in backups))}


def _jr():
    """The planner, imported lazily so this module never becomes its dependency."""
    import journal_retention as _m
    return _m
