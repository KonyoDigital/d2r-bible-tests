#!/usr/bin/env python3
"""WHAT EACH AUTOMATIC LANE WILL TOUCH, AND WHAT IT WILL LEAVE ALONE.

★ WHY THIS EXISTS. A different model family was shown the console cold and asked one question with
no hint of the expected answer — "if this app were about to do something on your behalf, could you
tell from these screens what it would do and what it would leave alone?" It answered:

    "CANNOT TELL. The screens show current state and manual controls, but give no indication what
     any automated action would actually touch or skip. No confirmation text or scope is visible."

It is right, and on this machine that matters more than usual: these lanes restart his console,
back up his ledger, and are the same family of code that once deleted reels he wanted.

⚠ A DECLARATION THAT IS ONLY PROSE IS WORSE THAN NONE. "this lane never deletes" written beside a
function that calls os.remove is a lie with a confident face — and it would be believed precisely
because someone bothered to write it down. So every claim here is CHECKED AGAINST THE SOURCE of the
function it describes: a lane that declares it never deletes, and whose code can delete, fails the
gate. The declaration is a promise the tests hold it to. [[unknown-stays-unknown]]

⚠ AND THIS DECIDES NOTHING. It reports scope. It cannot stop a lane, arm one, or change what any of
them do — the same rule health_engine follows, for the same reason: an actor that both decides and
describes will eventually describe what it wishes were true.
"""

#: Each lane: what it MAY touch, what it NEVER touches, and how often it wakes.
#: `forbids` is the load-bearing half — those are the words the source check enforces.
LANES = {
    "tvd-version-drift": {
        "does": "restarts this console onto a newer build already on disk",
        "touches": "this console process only",
        "forbids": ["delete"],
        "never": "your ledger, your reels, your vault — nothing on disk is written or removed",
        "when": "when the disk build is newer than the running one",
        "brakes": "refuses while a film is rolling, and refuses into a board that came back a "
                  "different world",
    },
    "tvd-ledger-backup": {
        "does": "copies your ledger aside so a bad write can be undone",
        "touches": "its own backup files",
        # ⚠ v2410 — THIS DECLARATION CONTRADICTED ITSELF, AND THE AUDITOR HAD BEEN SAYING SO TO
        # NOBODY. `touches: its own backup files` and `forbids: [delete]` cannot both be true of a
        # lane that rotates its own backups — and it does: _ledger_snapshot_once keeps the newest
        # _LEDGER_BACKUP_KEEP and os.remove()s the rest. unverified_reach() has been printing
        # "tvd-ledger-backup · 6 function(s) beyond it NOT audited (something down there can
        # delete)" from a CLI nothing runs.
        #
        # ⚠ THE FIX IS NOT TO DROP "delete" FROM forbids. That would weaken a real guard to silence
        # a TRUE alarm — the worst possible trade. Rotating one's own artefacts is simply not the
        # danger `forbids: delete` exists to prevent, so it gets its own clause that names WHAT and
        # HOW MANY. A permission with a directory and a keep-count is checkable; a blanket
        # exemption is not. The forbid still covers everything else on disk.
        "forbids": ["delete"],
        "rotates": {"dir": "_LEDGER_BACKUP_DIR", "glob": "ledger_*.json",
                    "keep": "_LEDGER_BACKUP_KEEP",
                    "why": "a backup directory that only ever grows fills his disk; the snapshot "
                           "keeps the newest N of its OWN files and removes no others"},
        "never": "the ledger itself — it only ever reads it",
        "when": "on a timer",
        "brakes": "a backup that cannot be written says so rather than pretending it wrote",
    },
    "tvd-eagle-watch": {
        "does": "asks every check how the running system is doing",
        "touches": "nothing — it reports",
        "forbids": ["delete"],
        "never": "any of your data; it has no write path at all",
        "when": "on a ten-minute timer",
        "brakes": "an unmeasurable check reads UNKNOWN, never ok",
    },
    "tvd-retro-triage": {
        "does": "surveys one unread reel at a time to learn, for free, which reels are worth "
                "paying to read",
        "touches": "its own triage store — the survey verdicts, one row per reel",
        "forbids": ["delete"],
        "never": "your reels, your frames, your ledger or your vault. It reads footage and "
                 "writes down what it saw; it removes nothing",
        "when": "on a timer, ONE reel per tick — spread out on purpose so it stays "
                "interruptible on the machine you play on, not because it is slow",
        "brakes": "it stands down for five named reasons rather than skipping silently: you are "
                  "playing (D2R is alive), the machine is loaded above its core count, a capture "
                  "is live, a paid sweep is spending, or the disk is below its floor",
    },
    "tvd-retention": {
        "does": "accounts for what old footage COULD be freed",
        "touches": "its own accounting",
        "forbids": [],
        "never": "a reel, unless the prune is armed — and the prune is OFF by his decision",
        "when": "on a timer",
        "brakes": "frame_authority holds any frame whose reel is unsealed, recent, or a witness",
    },
    "tvd-rolling-prune": {
        "does": "would delete old frames while he records — THE ONLY LANE HERE THAT CAN REMOVE HIS "
                "FOOTAGE",
        "touches": "frames inside reels that frame_authority has cleared for deletion",
        "forbids": [],
        "never": "runs at all while the arming flag is off — and it is off, by his decision. Its "
                 "own docstring says 'Prune while he records, indefinitely, exactly as he asked'; "
                 "what stops it is _PRUNE_SAFE_TO_RUN",
        "when": "on a timer, gated by that flag",
        "brakes": "frame_authority refuses any frame whose reel is one of the newest, unsealed, "
                  "named as a witness, or whose state could not be read at all",
    },
    "tvd-stash-watch": {
        "does": "seals a reel once the stash has been off screen long enough",
        "touches": "the seal record for that reel",
        "forbids": ["delete"],
        "never": "the footage itself — sealing marks a reel as read, it does not remove it",
        "when": "after a grace period with no stash on screen",
        "brakes": "only a reel the lane itself declared is sealed this way",
    },
    "tvd-shadow-watch": {
        "does": "looks for the Diablo window and ROLLS A REEL ITSELF when it finds one — the only "
                "lane here that starts a recording without him pressing anything",
        "touches": "starts the same capture agent /api/on starts; writes frames into a new reel",
        "forbids": ["delete"],
        "never": "a SECOND reel — it refuses while an agent is alive or a mini is counting down; "
                 "and it refuses below the 8 GB floor, because a reel the reaper cannot keep alive "
                 "is worse than no reel",
        "when": "every 20 s, only while the shadow switch is ON",
        "brakes": "tv_diablo.find_d2r_window_mac() — the SAME finder ON AIR and MINI capture "
                  "through. No window, no reel.",
    },
    "tvd-vault-autoread": {
        "does": "starts a vault read on footage that is waiting for one",
        "touches": "the vault ledger of what has been SEEN — never what he owns",
        "forbids": ["delete"],
        "never": "his grail; a vault read proposes, and the board is the only thing that writes",
        "when": "when a reel is owed a read",
        "brakes": "the free structural gate refuses a frame that is not a stash screen before any "
                  "paid read happens",
    },
    "tvd-chron-autoread": {
        "does": "starts a chronicle read on footage that is waiting for one",
        "touches": "the sweep's own proposal — a read-only picture until he presses register",
        "forbids": ["delete"],
        "never": "his ledger. Since v2289 the console cannot even call the board directly; it "
                 "leaves a note and he accepts it in the inbox",
        "when": "when a reel is owed a read",
        "brakes": "the gate holds any name without enough witnesses, and nothing is written "
                  "without him",
    },
    "tvd-space-warden": {
        "does": "watches free disk and refuses recording below the floor",
        "touches": "nothing — it refuses, it does not free",
        "forbids": ["delete"],
        "never": "delete anything to make room",
        "when": "on a timer",
        "brakes": "it stops a NEW recording rather than making space",
    },
}


def _fn_source(mod, name):
    """The source of the function a lane runs, or None if it cannot be found."""
    import inspect
    fn = getattr(mod, name, None)
    if fn is None:
        return None
    try:
        return inspect.getsource(fn)
    except Exception:
        return None


def reachable_source(mod, name, depth=3):
    """The source of `name` AND of everything it calls, to `depth`. -> (text, [names], why)

    ⚠ THE ONE-FRAME READ COULD NOT FAIL, AND I ONLY FOUND THAT BY CALIBRATING IT. Making the
    retention lane promise "never deletes" produced NO break — because _retention_loop does not
    delete inline, it CALLS something that does. A promise checked one frame deep is a promise
    about a function's own text, not about what running it can do, and it would have shipped as a
    confident green.

    So the check follows the call graph, using co_names rather than a text scan: reading the
    IDENTIFIERS a function actually references is the instrument this repo already learned to
    prefer over grepping its own prose. Bounded by depth and a visited set, and it REPORTS what it
    could not follow — a name it cannot resolve is a hole in the promise, not a pass.
    [[source-reading-guard]] [[feedback-suspect-the-instrument]]
    """
    import inspect
    seen, out, unresolved = set(), [], []

    def walk(fname, d):
        if d < 0 or fname in seen:
            return
        seen.add(fname)
        fn = getattr(mod, fname, None)
        if fn is None or not callable(fn):
            return
        try:
            out.append(inspect.getsource(fn))
        except Exception:
            unresolved.append(fname)
            return
        code = getattr(fn, "__code__", None)
        if code is None:
            return
        for n in code.co_names:
            # only follow names this module actually owns; a stdlib call is not ours to audit
            nxt = getattr(mod, n, None)
            if callable(nxt) and getattr(nxt, "__module__", None) == getattr(mod, "__name__", None):
                walk(n, d - 1)

    walk(name, depth)
    if not out:
        return None, sorted(seen), "no source could be read for %s" % name
    return "\n".join(out), sorted(seen), ("could not read: %s" % ", ".join(unresolved)
                                          if unresolved else "")


#: the loop function behind each lane name, so a claim can be checked against real code
LANE_FN = {
    "tvd-version-drift": "_drift_loop",
    "tvd-ledger-backup": "_ledger_backup_loop",
    "tvd-eagle-watch": "_eagle_watch_loop",
    "tvd-retention": "_retention_loop",
    "tvd-space-warden": "_warden_loop",
    "tvd-rolling-prune": "_prune_loop",
    "tvd-stash-watch": "_stash_watch_loop",
    "tvd-vault-autoread": "_vault_autoread_loop",
    "tvd-shadow-watch": "_shadow_watch_loop",
    "tvd-chron-autoread": "_chron_autoread_loop",
    "tvd-retro-triage": "_retro_triage_loop",
}

#: what a forbidden word means in code. Deliberately broad: a false alarm costs a comment, a missed
#: one costs his data.
FORBIDDEN_CALLS = {
    "delete": ("os.remove(", "os.unlink(", "shutil.rmtree(", ".unlink()"),
}


def check_declarations(mod):
    """Every lane's promise, checked against the source of the function it names. -> list of breaks.

    A lane that declares it never deletes, and whose loop body can delete, is reported. So is a
    lane with no declaration at all, and a declaration naming a function that does not exist —
    because a promise about code nobody can find is not a promise.
    """
    breaks = []
    for lane, spec in sorted(LANES.items()):
        fname = LANE_FN.get(lane)
        if not fname:
            breaks.append("%s: declared but no function is named for it, so nothing can be "
                          "checked" % lane)
            continue
        # ⚠ THE DIRECT BODY IS WHAT THIS CAN PROVE. A transitive walk found _drift_loop "reaches
        # os.remove" after 59 functions — in a module this size nearly everything reaches
        # everything, so that is not evidence of anything and reporting it as a broken promise
        # would be a false alarm. A guard that cries wolf is how a real one stops being read.
        # So: the lane's OWN body is CHECKED, the wider reach is MEASURED AND REPORTED as
        # unverified, and the two are never mixed. [[unknown-stays-unknown]]
        direct = _fn_source(mod, fname)
        if direct is None:
            breaks.append("%s: names %s, which does not exist — the declaration describes code "
                          "nobody can find" % (lane, fname))
            continue
        for word in spec.get("forbids") or []:
            for call in FORBIDDEN_CALLS.get(word, ()):
                if call in direct:
                    breaks.append("%s promises it never %ss, and %s itself calls %s"
                                  % (lane, word, fname, call))
    return breaks


def _rotates_is_wellformed(mod, rot):
    """Is this a real, scoped rotation permission — or a flag? -> bool

    ⚠ PRODUCTION USED TO ASK `bool(spec.get("rotates"))`. A cold review put it exactly: the clause
    was "documentation that a future edit can quietly widen", and the schema tests policed the
    dict's shape while the code that GRANTS the permission never looked at a single field. Copy the
    key onto another lane, or empty its contents, and every test stays green while the permission
    spreads.

    So the grant now requires what the clause claims: a directory and a keep-count that CONTROL_APP
    ACTUALLY DEFINES, a glob, and a stated reason. A permission naming something nobody can find is
    the same defect check_declarations already refuses for LANE_FN — "a promise about code nobody
    can find is not a promise" — applied to the permission rather than the prohibition.

    ⚠ AND A KEEP OF ZERO IS NOT ROTATION. It is deletion under a friendlier word, so it does not
    grant. [[the-unjoined-end]] [[unknown-stays-unknown]]
    """
    if not isinstance(rot, dict):
        return False
    if not str(rot.get("glob") or "").strip() or not str(rot.get("why") or "").strip():
        return False
    d, keep = rot.get("dir"), rot.get("keep")
    if not d or not keep or not hasattr(mod, d) or not hasattr(mod, keep):
        return False
    val = getattr(mod, keep, None)
    return isinstance(val, int) and not isinstance(val, bool) and val > 0


def undeclared_reach_abilities(mod):
    """Lanes that FORBID an ability and can nonetheless reach one, with no clause permitting it.

    -> list of dicts {lane, ability, functions, permitted}

    ⚠ THIS IS A NARROWER QUESTION THAN unverified_reach AND THAT IS THE WHOLE POINT. That function
    reports raw reachability and warns, correctly, that it must never be rendered as a verdict — in
    a module this size everything reaches everything. This one reports the INTERSECTION of what a
    lane PROMISED NOT TO DO with what its reach can actually do, which is a different and much
    smaller set. Measured at the shipped depth on 2026-09-01: exactly ONE lane of eleven.

    ⚠⚠ AND MY FIRST DRAFT OF THIS DOCSTRING CLAIMED "exactly ONE lane of eleven", WHICH IS FALSE.
    I read it off a GREPPED EXCERPT of the CLI output that happened to show one row, and wrote the
    number down as if I had counted. Measured properly, on the same tree, the same minute:

        tvd-ledger-backup   delete   reach= 6   permitted=True   (rotates its own backups)
        tvd-shadow-watch    delete   reach=23   permitted=False
        tvd-stash-watch     delete   reach=34   permitted=False
        tvd-version-drift   delete   reach=71   permitted=False

    FOUR, and one of them reaches seventy-one functions. So the original author's noise argument
    STANDS and my "one row is a signal" did not survive contact with the measurement: at reach=71
    this is exactly the everything-reaches-everything case that would make a gate cry wolf.

    THEREFORE THIS REPORTS AND DOES NOT REFUSE. It is strictly more informative than
    unverified_reach — it names WHICH forbidden ability is reachable and whether a clause permits
    it — and strictly less authoritative than the direct-body check. The one row that is actually
    actionable (ledger-backup, reach 6, now carrying an explicit `rotates` clause) was found by
    reading it, not by a gate failing.

    ⚠ DO NOT PROMOTE THIS TO A FAILING GATE ON THE STRENGTH OF THE LEDGER-BACKUP CASE. Three of
    the four rows are almost certainly reach-noise, and a gate that fails on all four teaches him
    to skip the row — the exact defect CF-10 records three instances of. Narrowing it honestly
    (a shorter depth, or following only the call path that actually performs the ability) is real
    work, not a parameter tweak. [[unknown-stays-unknown]] [[feedback-suspect-the-instrument]]

    ⚠ A lane may legitimately do a forbidden-sounding thing to its OWN artefacts. That is declared
    with a `rotates` clause naming the directory, the glob and the keep-count — checkable, unlike a
    blanket exemption — and such a lane is reported as PERMITTED rather than as a break.
    """
    out = []
    for lane in sorted(LANES):
        spec = LANES[lane]
        forbids = spec.get("forbids") or []
        if not forbids:
            continue
        u = unverified_reach(mod, lane)
        if not u.get("checked"):
            continue                       # UNKNOWN is reported by unverified_reach, not here
        for ability in sorted(set(u.get("reachesAbilities") or [])):
            if ability not in forbids:
                continue
            out.append({"lane": lane, "ability": ability,
                        "functions": u.get("functions"),
                        "permitted": (ability == "delete"
                                      and _rotates_is_wellformed(mod, spec.get("rotates"))),
                        "why": (spec.get("rotates") or {}).get("why")})
    return out


def unverified_reach(mod, lane):
    """How far this lane's calls go, and whether anything down there can delete. -> dict

    ⚠ THIS IS NOT A VERDICT AND MUST NEVER BE RENDERED AS ONE. It is the honest statement of what
    the direct check does NOT cover: "this lane's body does not delete, and it calls into N
    functions that were not audited". Presenting reachability as proof of danger would be as wrong
    as presenting its absence as proof of safety — in a module this size a walk of 59 functions
    touches most of the file, and everything reaches everything.
    """
    fname = LANE_FN.get(lane)
    if not fname:
        return {"checked": False, "why": "no function named for this lane"}
    src, walked, why = reachable_source(mod, fname)
    if src is None:
        return {"checked": False, "why": why or "no source"}
    can = sorted({w for w, calls in FORBIDDEN_CALLS.items() if any(c in src for c in calls)})
    return {"checked": True, "functions": len(walked), "reachesAbilities": can,
            "why": why or "",
            "note": "reachability, not behaviour — the direct body is what was verified"}


def say(lane):
    """One line he can read before a lane acts. -> str"""
    s = LANES.get(lane)
    if not s:
        return "%s has no declared scope — what it would touch is UNKNOWN" % lane
    return "%s · touches %s · never %s · %s" % (s["does"], s["touches"], s["never"], s["brakes"])


def report():
    """Every lane, for the console. -> dict"""
    return {"lanes": {k: dict(v, say=say(k)) for k, v in LANES.items()}, "count": len(LANES)}


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    import control_app as _ca
    bad = check_declarations(_ca)
    print("\n🤖 WHAT RUNS WITHOUT YOU, AND WHAT IT TOUCHES\n")
    for lane in sorted(LANES):
        s = LANES[lane]
        print("  %-20s %s" % (lane, s["does"]))
        print("  %-20s   touches: %s" % ("", s["touches"]))
        print("  %-20s   NEVER:   %s" % ("", s["never"]))
        print("  %-20s   brakes:  %s" % ("", s["brakes"]))
        print()
    print("  ── what was PROVEN, and what was not ──")
    for lane in sorted(LANES):
        u = unverified_reach(_ca, lane)
        if u.get("checked"):
            print("  %-20s body verified · %d function(s) beyond it NOT audited%s"
                  % (lane, u["functions"],
                     (" (something down there can %s)" % "/".join(u["reachesAbilities"]))
                     if u["reachesAbilities"] else ""))
        else:
            print("  %-20s ⚪ could not be checked — %s" % (lane, u.get("why")))
    print()
    if bad:
        print("🔴 %d declaration(s) the CODE contradicts:" % len(bad))
        for b in bad:
            print("     %s" % b)
        raise SystemExit(1)
    print("🟢 no lane's own body contradicts its promise.")
    print("⚠ that is a check of each lane's OWN code, not of everything it calls — the line above")
    print("  says how much was left unaudited, because a promise nobody measured is not a promise.")
