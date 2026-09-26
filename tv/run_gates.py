#!/usr/bin/env python3
"""v1483 — THE GATE SET, in one place, with one verdict.

Why this exists
---------------
`tv/test_routes.py` exited 1 for about a hundred versions and nobody knew (REG-079). It was not
broken in an interesting way — v1381.1 changed a rule, two tests kept asserting the old one — but
it was not in anybody's habit, so its verdict decayed into decoration. It still passed 181 of 183
assertions, which is the trap: a mostly-green orphan looks maintained.

The lesson generalises past that one file. "The gate set" was a thing people carried in their
heads and typed by hand, which means it was different for every person and every session, and a
suite could fall out of it silently. It is now a list in a file, and `TestNoOrphanSuite` fails if a
`tv/test_*.py` exists that this list does not name.

Reporting rules (learned the hard way)
--------------------------------------
* Encoding-safe before anything prints — a gate that dies REPORTING turns a clean tree red
  (REG-044/054/077/078).
* A suite that cannot RUN is reported as SKIPPED, loudly, and never counted as a pass. Silence
  about a check that did not happen is the same lie as a false green.
* A SKIP must be DECLARED IN ADVANCE or it is a failure (v1925). Loud was not enough: every gate
  here is required, so a gate that skips on every venue has never run at all, and the run still
  exited 0 with a tidy "✅ N gate(s) passed, 1 skipped". Each Gate now names the skip reasons its
  lane is allowed to produce (`skip_ok=`); a SKIP whose reason matches nothing there is counted
  with the failures and named in the verdict.
* The exit code is the verdict: non-zero if any REQUIRED entry failed OR skipped undeclared.
"""
from __future__ import annotations

import argparse
import shutil
import atexit
import fcntl
import glob
import os
import re
import tempfile
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

sys.path.insert(0, HERE)
try:
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass


# v1868 — one scratch dir per gate RUN, for anything a gate must not write into his tree.
# ⚠ 2026-09-26 — IT WAS MADE AT IMPORT, BY EVERY IMPORTER, AND NOTHING USES IT. Every process that imported this module
# (heart2, the laws that read GATES, the doctor) minted an empty tvd-gates-* dir, removed at exit only when the exit
# was clean: MEASURED 373 of them in his temp dir, 48 in a day, every one empty. Made on first use now.
_GATE_SCRATCH = None


def gate_scratch():
    global _GATE_SCRATCH
    if _GATE_SCRATCH is None:
        _GATE_SCRATCH = tempfile.mkdtemp(prefix="tvd-gates-")
        atexit.register(shutil.rmtree, _GATE_SCRATCH, True)
    return _GATE_SCRATCH


class Gate:
    # v1925 — skip_ok: the reasons THIS gate's lane is allowed to skip for, as regexes matched
    # (case-insensitively) against the reason string the run reports. Empty — the default — means
    # this gate may never skip: every entry in GATES is REQUIRED, so an undeclared skip is a gate
    # that did not run, and that is now counted with the failures instead of printing a warning
    # beside a green verdict. Declare a reason only when the lane genuinely cannot exist on some
    # venue (a browser lane on his Mac runs on CI instead — [[test-venue]]); "it broke today" is
    # never a reason to add one.
    def __init__(self, name, argv, timeout=900, needs_app=False, cwd=REPO, why="", skip_ok=()):
        self.name, self.argv, self.timeout = name, argv, timeout
        self.needs_app, self.cwd, self.why = needs_app, cwd, why
        self.skip_ok = tuple(skip_ok)


# v2400 — HOVER WILSON JOINS THE GATE SET, AND IT MAY ONLY GO RED ON A LEAK.
#
# tv/hover_wilson.py is a REPORT, not a gate: it scores the autopilot's four claims (coordinate,
# anchor, read, slot) on SABOTAGE ATTEMPTS and always exits 0. That is deliberate — its own header
# says "UNPROVEN MUST NOT READ AS FAILING ... a gate that turned amber on its own newest checks
# would be switched off inside a week, which is the same defect as a gate that is green forever."
# Today `anchor` is UNPROVEN (0 attempts: no tooltip->cell offset has been calibrated yet). That is
# a MISSING MEASUREMENT, not a defect, and a gate that reddened on it would be furniture within the
# week. [[unknown-stays-unknown]]
#
# So the gate is one predicate over the report's rows: LEAKS — "a deliberately WRONG input was NOT
# caught" — is the only state that fails. UNPROVEN and UNKNOWN print loudly, with their notes, and
# PASS. The three states stay three; they are not collapsed into pass/fail.
#
# ⚠ WHY -c AND NOT A FLAG: hover_wilson.py has no failing mode, and the report must keep exiting 0
# when a human runs it by hand. The script path is passed as the LAST NON-OPTION ARGUMENT on
# purpose: test_gate_set_names_only_things_that_exist reads exactly that argument, so this gate
# still names a file that must exist and cannot rot into a permanent no-op if hover_wilson.py is
# ever deleted or renamed.
_HOVER_WILSON_VERDICT = r"""
import os, sys
_p = sys.argv[1]
sys.path.insert(0, os.path.dirname(_p))
import hover_wilson as HW

rows = HW.score()

# ⚠⚠ v2464 — A2 · THIS GATE SCORED THE SABOTAGES AND BANKED NOTHING, AND THAT IS WHY THE LOCKS
# WERE ALL UNPROVEN. v2444 deliberately put banking in main() only, so that importing the module
# or calling score() from a test could not write his ledger. This gate calls score() — so every
# push measured 55 sabotages and fed the proof queue with none of them, and the only way evidence
# ever reached the queue was a human typing `python3 tv/hover_wilson.py`.
# MEASURED: tv/.self_arming.jsonl did not exist, and all five locks read UNPROVEN n=0 on the live
# console, while the board recorded miniauto.run as OPEN at 55/55 since v2444. The proof had
# decayed to nothing and nothing said so.
# Banking here is safe and idempotent: bank() folds on (lock, kind, src, ref), so three runs in a
# row still read 55/55 rather than 165/165 — measured before this line was written.
# ⚠ A GATE IS NOT A FIXTURE. v2444's rule was about tests importing the module for other reasons;
# this is the harness deliberately run against real code, which is exactly what should feed the
# queue. [[the-unjoined-end]] [[feedback-fixtures-never-touch-live-data]]
try:
    _b = HW.bank_into_proof_queue(rows)
    if _b.get("banked"):
        print("  banked into the proof queue -> miniauto.run: " + ", ".join(_b["banked"]))
    for _sk in (_b.get("skipped") or []):
        print("  NOT banked: " + _sk)
except Exception as _e:
    # a banking failure must be SAID, never swallowed, or a lock silently stops being fed
    print("  ⚠ banking RAISED and the proof queue was not fed: %s" % str(_e)[:140])

leaks = [r for r in rows if r["state"] == "LEAKS"]
unproven = [r for r in rows if r["state"] in ("UNPROVEN", "UNKNOWN")]
for r in rows:
    print("  %-12s %-9s sabotages=%s caught=%s wilson=%s"
          % (r["claim"], r["state"], r["attempts"], r["caught"],
             "-" if r["wilson"] is None else ("%.3f" % r["wilson"])))
if unproven:
    # LOUD, and PASSING. Nobody has tried to break these yet; that is work to do, not an alarm.
    print("  %d claim(s) UNPROVEN/UNKNOWN — a measurement nobody has taken, NOT a defect: %s"
          % (len(unproven), ", ".join(r["claim"] for r in unproven)))
    for r in unproven:
        for n in (r["notes"] or []):
            print("    %s: %s" % (r["claim"], n))
if leaks:
    print("LEAK — a deliberately WRONG input was NOT caught:")
    for r in leaks:
        print("  %s (%s): caught %s of %s sabotages, wilson %s"
              % (r["claim"], r["what"], r["caught"], r["attempts"],
                 "-" if r["wilson"] is None else ("%.3f" % r["wilson"])))
        for n in (r["notes"] or []):
            print("    %s" % n)
    sys.exit(1)
print("hover-wilson: %d claim(s) proven, 0 leaking, %d unproven"
      % (len(rows) - len(leaks) - len(unproven), len(unproven)))
"""


# THE GATE SET. Adding a tv/test_*.py without adding it here fails TestNoOrphanSuite.
GATES = [
    Gate("test_the_doctor_times_each_check", [sys.executable,
                                    os.path.join(HERE, "test_the_doctor_times_each_check.py")], 60,
         why="v3404c — cd.run() took >8 min while 93 checks timed standalone ~24s, and nothing "
             "on the row said which check sat, so the 1500s bound took the blame. Pins that an "
             "executed check carries ms, a skipped PERIODIC check carries ms=None not 0, and "
             "that dropping the stamp makes the law red. Does not hit his live console."),
    Gate("test_missing_companion", [sys.executable,
                                    os.path.join(HERE, "test_a_missing_companion_is_not_a_regression.py")], 60,
         why="REG-1035 — bible.html probes the local console, which cannot exist on a cloud "
             "runner, so Routine G scored 7/8 and stayed red on the absence of a desktop app "
             "beside 320/320 items and 0 page errors. Pins the bucket is narrow (other loopback "
             "ports still gate) and still PRINTED, using the audit's OWN regexes"),
    Gate("test_quit_attribution", [sys.executable,
                                   os.path.join(HERE, "test_a_quit_names_who_asked.py")], 60,
         why="REG-1071 - Grok Bot drove the native seat and his console DIED from a vault mule "
             "arrow click: 'window gone (api-quit)' with no Esc sent. Ranked worst of four traps. "
             "Not reproducible here - /api/quit has exactly ONE caller in the page - so it is "
             "made DIAGNOSABLE instead: every quit names who asked, an unnamed one records as "
             "UNATTRIBUTED, and since the Escape handler is the only legitimate caller an "
             "UNATTRIBUTED line IS the finding. 4 red-proofs"),
    Gate("test_freshness_probe_window", [sys.executable,
                                        os.path.join(HERE, "test_a_freshness_probe_has_no_window.py")], 60,
         why="v3294 - crest_loudness refuses to score until it can prove the document is NEW, which is right. Its proof was a CLOCK: sample performance.now() before the reload and wait for a reading below it. That is only observable for _before milliseconds after the navigation, so the probe reliability depended on how long the page happened to be open. MEASURED back to back with nothing else changing: run 1 exit 0 in 6s, run 2 exit 2 in 21s. It blocked two pushes on a tree that was fine, and a gate that intermittently cannot measure spends its credibility on noise - after which a real UNKNOWN is waved through as that flake again. A marker has no window: a new document does not carry it, for as long as it takes to look. Five consecutive runs green after. Pins the marker, that the OLD document is marked before the reload, and that a page which did NOT navigate is STILL refused - this fixed when it can see, not whether it insists. 3 red-proofs"),
    Gate("test_ruling_index_honest", [sys.executable,
                                     os.path.join(HERE, "test_a_ruling_index_admits_what_it_cannot_see.py")], 60,
         why="v3294 - three times in one session a recorded ruling stopped me shipping the obvious fix and each time I found it by luck of grep. EXTRACTION WAS TRIED AND MEASURED DEAD: the warning marker plus prohibition language gives 223 entries and finds 0 of the 3; prohibition language alone gives 13,974; topic plus prohibition finds v2397 and misses v1631, whose constraint is a plain fact in his own words with no prohibition word in it. A 223-row index that omits every ruling that matters is WORSE than none because it reads as complete. So it reads an explicit marker instead. The first marker RULING: collided with prose NINE times; @@RULING collides zero times and is ASCII so it cannot trip the encoding rule shipped one version earlier. Pins that the sigil cannot be weakened, that the four seeded rulings are FOUND, and that every answer says an UNMARKED ruling is invisible and absence is not permission. 3 red-proofs"),
    Gate("test_encoding_rule_one_def", [sys.executable,
                                       os.path.join(HERE, "test_the_encoding_rule_has_one_definition.py")], 60,
         why="v3293 - a test of mine printed non-ASCII without console_safe.enable(); on his cp1255 console that crashes WHILE REPORTING, so a clean tree exits non-zero for a reason unrelated to the check. The RULE was never the problem - it refused mine, and three files in tv/ carry comments saying it refused them too. The defect was WHEN you learn: it lived inside test_control, ~500s in, at push time. Moved to console_safe.audit() beside the enable() it tells you to call, with a CLI that answers in under a second and a pre-push step that runs it FIRST. Pins one definition three callers, and is BEHAVIOURAL on fixtures - it catches an unsafe entry point and spares a safe one, an ASCII one and a non-entry-point module, because a rule that returns nothing passes every source law. 3 red-proofs"),
    Gate("test_eagle_counts_drawn", [sys.executable,
                                    os.path.join(HERE, "test_the_eagle_counts_what_the_panel_draws.py")], 60,
         why="v3293 - Grok Bots native eyes on v3291: CHILIAD not measured 23, panel 23-vs-25 disagree. That sentence is v3284s clause WORKING, and it caught a real defect. TWO divergences, both making the panel draw more than the figures admitted: the server counted state == unknown while the panel buckets unknown OR unmeasured, and console_doctor emits UNMEASURED for a SLOW check that never had a full pass; and slowRows was published and bucketed by the panel but counted by NONE of the three figures, so needsYou could drift too. Measured live: rows 61 + slow 1 = 62 drawn, unknown 6 under the old rule and 7 under the new. Fixed at the NOUN - the figures widen to the drawn population and the panel is untouched, because agreement bought by drawing less is the same silence in a new place. 3 red-proofs"),
    Gate("test_inert_proof_exit", [sys.executable,
                                  os.path.join(HERE, "test_an_inert_proof_does_not_exit_zero.py")], 60,
         why="v3292 - a red-proof came back BLIND this session: it matched its anchor exactly once, deleted the clause it targeted, and the law stayed GREEN, because it asserted phrases that occur three times elsewhere in the file. BLIND already exited 1. INVALID did NOT, and INVALID means the sabotage matched NOTHING - the proof changed no byte, so the gate has no working red-proof while reporting one. MEASURED with a throwaway gate whose find was absent: INVALID exited 0. Twice in one session a real proof went INVALID on a ROTTED anchor, once a line my own refactor deleted, and both recorded success. Pins that BLIND and INVALID fail and are NAMED, that UNPROVABLE is named but NOT failed because that is the suites finding rather than this tools, and that an empty run invents no verdict. Behavioural: calls prove_exit_code with fixtures, which is why that decision was lifted out of main - a decision reachable only by building a sandbox is one nothing will ever test. 3 red-proofs"),
    Gate("test_pipeline_reading_age", [sys.executable,
                                      os.path.join(HERE, "test_the_pipeline_reading_carries_its_age.py")], 60,
         why="v3291 - Konyo at the pipeline board: pipeline though might need some updated 8 releasable 3 not, make sure its not stale and its all moving along. MEASURED: stages reads banked 3 releasable 8 across onDisk 11 with reelsUnmeasured 0, and the numbers were never stale - story() re-reads reel_retention.plan() every request, nothing cached. But the board makes the STRONGEST claim on the screen, that the counts stand still by design and not by neglect, and carried NO timestamp of any kind to check it by. Stillness-by-design and stillness-by-neglect look identical. Pins that the server stamps when it looked and at how many reels, that the panel prints it, and that an ABSENT stamp reads as UNKNOWN rather than fresh - which is a real case, since an un-restarted console still serves the old payload. 3 red-proofs"),
    Gate("test_shelf_accounts_for_every_run", [sys.executable,
                                               os.path.join(HERE, "test_the_shelf_accounts_for_every_run.py")], 60,
         why="v3290 - Konyo: the shelf is showing 12 runs why not 8, what happened there. MEASURED: five surfaces, five numbers, each correct for a DIFFERENT question - 419 sessions, 63 reels with 11 on the shelf, 11 surveyed, 15 over a 14-DAY WINDOW, FIFO 8, 12 cards. They must NOT be forced equal: the 2026-09-13 ruling is that the number was never wrong, only the NOUN was, and the strip is not the defect. What WAS broken is a silent subtraction - a STUB was the one dropped bucket with no counter anywhere, 154 of his 419 runs. With it counted the population closes exactly: 12 shown + 8 fixtures + 232 retired + 154 stubs + 13 unknown = 419. Pins that stubs are counted, that the head names how many of how many, that the shown count is measured BEFORE join() while the population is still knowable, and that an unexplained remainder is PRINTED rather than absorbed. 3 red-proofs"),
    Gate("test_shelf_opens_on_a_reel", [sys.executable,
                                        os.path.join(HERE, "test_the_shelf_opens_on_a_reel.py")], 60,
         why="v3289 - Konyo asked twice for the BEST RUN / STREAK strip at the tippy top of the SHELF with ACTIVITY under it. That reopens the v2965 scar where 1433px of furniture put all 530 cards off-screen and v3121 refused the same request. Granted WITH the guard that keeps the half he did not say out loud - the reels must be SEEN. MEASURED at his real 1120x660: order alone gave scrollTop 0 / firstCardTop 815 / visible FALSE; order plus guard gives scrollTop 476 / firstCardTop 235 / visible TRUE in a 390px viewport. The guard is a TIMING fix for a bug v3029 already had: it chose the opening scroll before _shTimeline ran, and sh-timeline ships hidden, so it measured 0px for a block that becomes 156px. Pins the ORDER, that the scroll is re-decided AFTER the chart is real, and that a healthy shelf is still left alone. 3 red-proofs"),
    Gate("test_stale_server_says_so", [sys.executable,
                                       os.path.join(HERE, "test_a_stale_server_says_so.py")], 60,
         why="v3288 - Grok Bot LOOKED 5721820085: CHILIAD panel 283 / footer 284, two numbers on one screen each claiming to be the version. TWO EXISTING MECHANISMS CONTRADICTED EACH OTHER on one process in one second: pre-push compared listener PID start vs file mtime and said stale, while _drift_once compared a baked literal vs disk and said in sync on v3287. Neither is first-hand. module_freshness captures this file mtime AT IMPORT and compares it to the mtime now - no PID, no literal, no guess about ancestry. Pins BEHAVIOUR not names: it fires on a rewrite, says the gap in words, names the PAGE-live/SERVER-stale boundary, returns UNKNOWN rather than in-sync when the file cannot be read, and is actually published. Monkeypatches the clock rather than touching the file, so it cannot leave his live console believing it is stale. 4 red-proofs"),
    Gate("test_kpi_chip_names", [sys.executable,
                                 os.path.join(HERE, "test_a_kpi_chip_names_what_it_counts.py")], 60,
         why="v3287 - Konyo: 'even top corner chronicles set uniques and runewords should color match the tabs in main console'. The Sessions header drew 99/99 CHRONICLE (runewords) and 309/403 CHRONICLE (uniques) - two different quantities under one word, four inches apart, both numbers right and the noun wrong. Pins that the chips name what they count, declare their room class, and take the SHARED tokens (--rune / --q-unique / --q-set) rather than a forked hex; and that the FULL BIBLE door spans the row and glows instead of hugging the end in --gold-dim. Runewords wears --rune not gold by v1631s ruling that a TAB labels a ROOM. 4 red-proofs"),
    Gate("test_vault_population", [sys.executable,
                                   os.path.join(HERE, "test_the_vault_says_its_own_population.py")], 60,
         why="v3286 - Konyo at a Vault screenshot: 'this is still here 200+ items that should not be'. The vault drew lockers and a dock and never said how many things it holds, so the 200+ had no referent and the number that settled it had to come off /api/vault_population rather than off the surface he was reading. Measured: 222 owned = 173 filed + 49 loose, the 49 splitting 31 set pieces / 18 other. Pins that the line exists, that renderVault actually fills it, and - the one that matters - that every figure is DERIVED BY SUBTRACTION from the two pools renderVault already built, so filed+loose==pool and pool+shared==owned by construction rather than by luck. 3 red-proofs"),
    Gate("test_guest_intake_door", [sys.executable,
                                    os.path.join(HERE, "test_a_guest_may_not_walk_through_his_door.py")], 60,
         why="v3296 - Konyo authorised this while scoping the parallel-test console: 'yea do it obivously'. The intake endpoint expression was written out BY HAND AT TEN SITES in bible.html (24312, 26090, 26722, 26960, 27672, 37972, 39894, 46859, 47559, 52952), each carrying the production URL as its file:// fallback, and the copies had ALREADY DRIFTED - nine read localStorage, one read window.LSR. Over file:// that default was the production endpoint FOR EVERY BOARD, so a GUEST board (no ownerClaim - exactly what the Linux test console is) posted its intake into HIS REAL INTAKE, silently; running the two consoles in parallel is the precise activity that fires it. Pins both halves: the public door is named EXACTLY ONCE in executable source inside _d2rIntakeEndpoint, and the guest branch cannot reach it because the production return sits behind a _D2R_OWNER test with a relative fallback after it. Also pins that HIS OWN board still reaches his own live door, because breaking that is worse than the defect. 2 red-proofs. NOTE its call-site count is taken on RAW source on purpose - _executable_only drops bible.html L38004 (raw 10, stripped 9), tracked separately. CORRECTED v3299: the cause is NOT the regex literals above that line as first recorded, it is accept=image/* at bible.html:37910 whose /* opens a comment for the context-free scanner 94 lines upstream. 2 red-proofs"),
    Gate("test_eye_declares_reach", [sys.executable,
                                     os.path.join(HERE, "test_the_eye_declares_what_it_did_not_see.py")], 60,
         why="v3299 - the second eye reviews the VERSION COMMIT, not what ships. payload_for runs `git show <sha>` on the one commit carrying the stamp, so every fix: commit landing after the bump and before the push is NEVER SEEN BY ANY EYE while the ledger row reads as though the push was reviewed. MEASURED 2026-09-18 on v3298: FOUR commits shipped in one push and the eye saw ONE; the unseen three included the membership discriminator, which took three cuts (two wrong) and was the most consequential change in the push - and the verdict then attacked `_fnew > _dm + 0.5`, code SUPERSEDED two commits later. That is not the eye being wrong, it is the gate handing it bytes that no longer ship. This law does NOT close the gap (closing it means a wider payload and the payload already truncates at ~35%, so the cost is HIS call) - it pins that the runner STATES ITS OWN REACH. Three states and collapsing any two is the defect: a LIST means these commits ship unreviewed, [] means MEASURED-AND-NONE, None means the range could not be listed and is UNKNOWN never nothing-was-missed. Pins the rule not today's shas (HEAD~1 and HEAD, so it survives the next ship) and pins that the CALLER branches on None rather than collapsing it. 2 red-proofs"),
    Gate("test_empty_world_unknown", [sys.executable,
                                      os.path.join(HERE, "test_an_empty_world_says_unknown.py")], 60,
         why="v3297 - FOUR readers, ONE defect shape, all measured 2026-09-18 against a guest board that is structurally JOURNAL-RICH AND LEDGER-EMPTY: every durable what-was-DONE store is gitignored (capture_doors, vault_swept, retro_triage, chronicle_swept, vault_accum, river_stamp...) while the journal SEED is tracked, so a fresh clone inherits his testimony about what HAPPENED and has no record of what was DONE. Each reader coerced that absence into 0 and reported a defect that did not exist. (1) the absent capture ledger: _capture_door_load swallows a missing file into {} and the report coerces int 0, and the invariant's UNKNOWN arm fires only on a NON-INT - a condition a missing FILE can never reach - which manufactured 'journal says 56, ledger says 0' where the 56 was HIS imported journal. (2) the printer-reach doctor discarded upstream's own state=UNKNOWN and re-manufactured the populated-case confession over an empty world. (3) the sweep verdict was never joined to gate_failures(), so a DEAD OCR TOOLCHAIN and a shelf with no stash panels printed the identical sentence. (4) route-lane runs==0 conflated stood-down-by-design, process-younger-than-the-90s-tick, and a tick that raises upstream of the counter for ever. Three of the four halves are BEHAVIOURAL - they call the reader against a genuinely empty world rather than asserting a name appears, because a presence-law would go green over any of these fixes being deleted. 4 red-proofs"),
    Gate("test_reel_door", [sys.executable,
                           os.path.join(HERE, "test_a_reel_says_which_door_opened_it.py")], 60,
         why="v3312 (#65/#66) - Konyo: 'the shadow reels that get shadow recorder they too need to be within the river and seen visually just like the others'. THE FIRST HALF WAS ALREADY TRUE and it took three wrong instruments to establish that: shadow reaches its reel THROUGH start_agent, so a shadow reel is an ordinary reel with the same hist dir, index and seal, and nothing in shelf_driver/river/river_walk/reel_retention filters by door. What was missing is that NO SURFACE COULD SAY WHICH ONES THEY WERE - river.py mentioned door ZERO times, so shadow flowed every joint INVISIBLY and 'shadow contributed N' had no answer, which is exactly how an evening of play producing ZERO shadow reels stayed hidden until he noticed the absence himself. MEASURED on tv/sessions.jsonl, 5169 rows: shadow 761, onair 759, mini 2, with 1522 rows carrying BOTH sessionId and door; of the reels on disk onair 7, shadow 1, and 16 with no door row at all because they predate the v2687 stamp. THOSE STAY UNKNOWN AND MUST NEVER BECOME onair - absence of a record is not evidence of the common case and a manufactured provenance cannot be told from a real one afterwards. reel_door is ONE definition for the river and the shelf, per the v3308 lesson where the partition was written twice and the screen said 9 while the engine said 7. ALSO #66: pressing ON AIR while SHADOW rolls used to answer 'already on air' - true about a reel, misleading about WHOSE, with the reply carrying mode and omitting the door. There is NO race (shadow refuses to start on top of anything, and that branch spawns nothing); the defect was the SENTENCE, and the law pins that it still kills nothing, because the fold runs at seal so pre-empting a rolling reel orphans its frames. Pins four things: a doorless reel is UNKNOWN, an unreadable journal is UNKNOWN with a REASON rather than an empty map, the say line names the unknowns out loud, and the split is DECORATION that never changes the capture joint's grade. 4 red-proofs.",
         ),
    Gate("test_clean_look_verdict", [sys.executable,
                          os.path.join(HERE, "test_a_clean_look_is_never_filed_as_findings.py")], 60,
         why="v3315 (#67) - A LOOK THAT FOUND NOTHING WAS FILED AS ONE THAT FOUND SOMETHING, and this is the FIFTH phrasing to defeat the same check. _NO_DEFECT_RX is a NOUN-PHRASE pattern needing 'no <...> defects|issues|bugs|problems'; four versions widened its vocabulary (v3216 evident, v3216 present, v3267 meeting, v3268 the bare full stop) and the lesson drawn was that the declaration IS the noun phrase. This shape has no such noun at all. MEASURED on the real v3301 look: Grok answered '**Findings**' then 'none found' and the row was filed verdict=findings, findings=2 - the ledger asserting the eye found two things when it said the opposite. Of the three conditions in _verdict_for exactly ONE failed, the declaration never matching; _claims_a_defect was False for both blocks. The repo's own COLD_FRAMING asks reviewers to say 'none found', so the instrument was refusing the wording it requested. _NO_FINDING_RX is kept as a SEPARATE named pattern because the noun-phrase one has been corrected four times and restructuring it to carry a different part of speech is how a fifth correction becomes a sixth. Safe by construction and the asymmetry is pinned as a BASELINE: a declaration followed by a real P1 still files as findings. ALSO: every row now records WHICH parser generation judged it (824 predate it), and verdict_provenance() re-judges what it can while keeping FOUR reasons for 'cannot' apart - prefix-only, no answer, a HAND-WRITTEN verdict no parser produced, and unstamped. My first cut of that measurement compared a TUPLE to a string and reported 709 disagreements; my second re-judged hand-written annotations as though a parser wrote them, which is v3313's category error one file away. Honest figures: 540 agree, 133 disagree, 91+17+47 UNKNOWN. 3 red-proofs.",
         ),
    Gate("test_look_records_commit", [sys.executable,
                          os.path.join(HERE, "test_a_look_records_the_commit_it_read.py")], 60,
         why="v3316 (#69) - A LOOK IS RECORDED AGAINST THE COMMIT IT ACTUALLY READ. payload_for(sha) resolves a commit, builds the diff from it, and the sha was THROWN AWAY: measured across all 824 prior rows there is no sha key at all, so the ledger could answer 'was this VERSION looked at' and NOT 'was this COMMIT looked at' - and the second is the one that matters because this repo batches 3-4 versions per commit to pay the gate once. 0bf8cb6d is titled v3304-v3307 and ships FOUR versions; asking once per version sends the SAME 10,016-byte payload four times, four paid looks at one set of bytes filed as four independent reviews, which is n inflated by REPETITION and is fake confluence. ALSO the hyphen range was invisible: _VER_LEADING_RUN accepts + , and & but not -, so v3304-v3307 registered as v3304 alone and v3305/v3306 shipped with NO second-eye look at all. That is the v2862 scar - which added the + form for exactly this reason - repeating with a new separator. versions_in_run() is now the ONE parser for what a subject ships and the history walk calls it, so the backlog and any future range-aware gate cannot disagree. The em-dash title case and v2854's leading-run protection are both pinned. looked_at_commit returns None and NEVER False when no row carries a sha, because answering False would declare 824 real looks to have never happened. 2 red-proofs.",
         ),
    Gate("test_heart_denominator", [sys.executable,
                          os.path.join(HERE, "test_the_heart_divides_by_the_population_it_counted.py")], 60,
         why="v3318 (#73) - THE HEART DIVIDED BY THE POPULATION ITS NUMERATOR DID NOT COME FROM. self_arming._heart_says_watched printed 'instruments watched: 394 of 457 gates proved'. proved counts gates that DECLARE a red-proof and were proven; total counts EVERY registered gate including those declaring none. COUNTED INDEPENDENTLY from run_gates.GATES and the test files: 457 registered, 417 declaring a RED_PROOF, 394 proven - so 394/457 = 86.2% was printed where 394/417 = 94.5% is true of the population 394 came from. It UNDER-stated, which is the safe direction and exactly why it would have survived: a number that looks worse than reality never gets challenged. THE REAL LOSS WAS THE 40: forty registered gates declare NO red-proof, gates never SEEN to refuse, and folding them into a denominator turns 'we have not proven these' into 'we proved a smaller fraction'. They now get their own clause naming what it means. ONE FACT, TWO READERS, ONE WRONG - control_app.py:19460 has printed it correctly all along and the store already persisted declared/total/unproven, so nothing new had to be computed; only the consumer was wrong. The no-proof count is OMITTED, never zeroed, when a figure is missing, because '0 declare no proof' is the most reassuring possible lie. The BASELINE case pins that with declared == total the sentence says 457 of 457 and a MEASURED 0, without which a hardcoded '394 of 417' would pass. The fixture carries the LIVE gates fingerprint on purpose: a stale one is refused before the sentence is composed, so the case would prove nothing. 3 red-proofs.",
         ),
    Gate("test_roster_not_debt", [sys.executable,
                          os.path.join(HERE, "test_a_roster_arriving_is_not_new_debt.py")], 60,
         why="v3328 (#71) - A ROSTER ARRIVING IS NOT NEW DEBT, AND THE FILE ALREADY KNEW IT. _verdict defines REFERENCE as a row with NO producer key AND NO clock, and line 20 says what that means: a roster or lookup table, no clock, so the question does not apply. A store the provenance question does not apply to cannot owe an answer to it. _compare's new-arrival branch reddened everything ranking below ANSWERS, so a roster arriving was filed as new debt. MEASURED 2026-09-18 on the live tree: engine_index.json SILENT (real debt, correctly red), heart_floor.json REFERENCE and test_reel_refs.json REFERENCE (both FALSE) - two of three reds were rosters being asked when they were last written and by whom, on a gate otherwise reporting 12 genuine improvements. ⚠⚠ THE SAME FALSE RED ALREADY BIT ONCE AND WAS PATCHED BY NAME: the ratchet's OWN baseline arrived REFERENCE and was reported as new debt on the very first clean run, and the fix excluded that one filename inside _split. That closed the instance and left the CLASS open, and the class re-fired the moment two more rosters landed - a rule learned once and generalised to nothing. ⚠ MY EARLIER DIAGNOSIS OF THIS TASK WAS WRONG AND IS CORRECTED IN THE SHIP: I claimed taking REFERENCE off the RANK axis would clear two false reds. There were THREE reds, none was a rank comparison, and RANK is only consulted when a store MOVES. The SILENT/REFERENCE tie is deliberate - the module says ranking one over the other would invent a distinction the census does not draw - and it is pinned here untouched. ⚠ SILENT AND PARTIAL STILL COUNT AS DEBT and the baseline half pins it: SILENT means the row HAS a clock and still names no writer, the question applies and went unanswered, which is engine_index.json today and must stay red. The exemption is for INAPPLICABILITY, never for inconvenience - exempting more would turn a ratchet into an off switch. Also pinned: a genuine ANSWERS->SILENT regression still reddens, and the empty-store sentence is unchanged because UNKNOWN had the honest shape first. 2 red-proofs, the second of which widens the exemption to every non-ANSWERS arrival and must go RED.",
         ),
    Gate("test_seed_vs_remaining", [sys.executable,
                          os.path.join(HERE, "test_a_seeded_name_is_never_one_the_game_says_he_lacks.py")], 60,
         why="v3327 (#79) - A SEEDED NAME IS NEVER ONE THE GAME SAYS HE LACKS. MEASURED on bible.html: the game's own Remaining list holds 19 names and _SET_SEED carried 17 of them WITH FIRST-FOUND DATES - set pieces he does not have, on a page he acts on, published live because a push to main deploys. _GRAIL_SEED carried 0, so the unique half was always clean. ATTRIBUTED BY BISECT across seven ships: v3308/09/10/11/12 all read 108 seeded and 0 contradictions; 12bcb40c (v3313+v3314) reads 133 and 17, and neither bake_seed.py nor test_bake_seed.py changed in that range, so the gate went red on DATA. ROOT CAUSE PROVEN BY ELIMINATION: bake() rule 3 skips any name in the Remaining list, _SET_MISSING is untouched by that commit, and the list measures 19 at every ref - therefore no run of bake() produced these and the literal was HAND-WRITTEN past the baker's rules. ⚠ AND IT IS ONE-WAY: bake() asserts old_set <= new_set, so re-baking can never remove a contaminated name; only a deliberate edit can. THE 25 v3313 ADDED SPLIT THREE WAYS and the fix follows the split rather than the count: 15 share ONE stamp, Sep 16 2026 15:28, and ALL FIFTEEN are on the Remaining list - fifteen set pieces are not found in one minute, so that date orders against nothing and the name is UNDATABLE; those are REMOVED. 2 are on the Remaining list but carry their OWN distinct dates (Laying of Hands Aug 24 01:10, Taebaek's Glory Aug 23 17:46) and are NOT automatically wrong - first-found is a historical positive while Remaining is present ownership, and found-then-sold satisfies both, so they are DECLARED in bake_seed.SEED_EXEMPT with a reason and SURFACED for his ruling rather than deleted, because deleting a real find is the worse error. 8 are dated and uncontradicted and are KEPT. 133 -> 118. ⚠ THE DECLARATION IS NOT A LOOPHOLE: a declared name whose stamp is shared by 5 or more pieces is refused, which is exactly what would be needed to re-admit the 15. Every declaration must carry a reason, and a declaration naming a name no longer seeded is refused as a stale permission. 2 red-proofs.",
         ),
    Gate("test_word_says_whose", [sys.executable,
                          os.path.join(HERE, "test_the_word_says_whose_row_it_is.py")], 60,
         why="v3326 (#84) - THE STATUS WORD SAYS WHOSE ROW IT IS, INSTEAD OF SAYING MISSING FOUR TIMES. His #35 ruling gives WAITING ON YOU a precise meaning and v3321 built the sections for it; what v3321 did not touch was the WORD inside them. MEASURED on his console at v3323 from his own screenshots: END ROUTES REACHABLE and THE RIVER both read MISSING under a heading reading RED ON PURPOSE - RULED NOT A DEFECT, NOTHING FOR YOU TO DO; CONSOLE UI FAULTS read MISSING while its own sentence says the console healed itself from 3 faults in 24h and It recovered; LEDGER PROVENANCE read MISSING under WAITING ON CODE - NOT YOURS TO FIX. Absent, ruled-fine, already-recovered and owed-by-Claude are four different facts, and one word for all of them is the same collapse as a 0 standing in for UNKNOWN, one layer up in the vocabulary. ⚠ IT IS A JOIN, NOT A NEW JUDGEMENT: _sortRow already computed the bucket from mineWhat and byDesignWhat - the server has named the owner of every row since v3307 - but it did so on the line AFTER the word was chosen, so the word could not see it. The fix moves the bucket one line earlier and passes it in; nothing here decides ownership. ⚠ THE unmeasured and unknown WORDS ARE DELIBERATELY UNTOUCHED - CAN'T ASK, NEVER and NOT THIS TICK already say the right thing with a reason and an age, and v3309 earned that distinction after his screen said NEVER about a row asked two minutes earlier. ⚠⚠ THE BASELINE IS THE HALF THAT MATTERS: the cheap way to calm this panel is to stop saying MISSING at all, so a row that is genuinely his and genuinely absent is pinned to still read MISSING in the warn tone - a panel that has stopped reporting is worse than one that reports bluntly. The warn tone is now conditioned on the bucket so a closed ruling and my own backlog stop shouting in the fault colour. IT STRIPS COMMENTS BEFORE READING, load-bearing: the block explaining this change contains the literal words BY DESIGN, CLAUDE OWES and MISSING, so a law reading raw source would be satisfied by its own commentary. 3 red-proofs.",
         ),
    Gate("test_store_guard", [sys.executable,
                          os.path.join(HERE, "test_a_store_is_never_written_over_an_unread_one.py")], 60,
         why="v3325 (#83) - A STORE IS NEVER WRITTEN OVER ONE THIS PROCESS COULD NOT READ. Three stores in this tree are READ-MODIFY-WRITTEN and the rule that protects them existed in exactly ONE. .vault_autoread.json is GUARDED and has been since v2904, its own comment carrying the lesson: never write memory over a store this process has not read, because an empty in-memory value written straight over a good store is strictly worse than not writing - the file then looks authoritative. It was learned once and generalised to nothing. MEASURED 2026-09-18 by the swallow ratchet, red 12 consecutive runs since 2026-09-17T09:51: .handoff_seen.json via _marks + --mark, and shadow_watch.json via _shadow_watch_stored + _shadow_watch_note, both collapsed a malformed file to {} and then wrote that back WHOLESALE. The handoff one is the QUEUE DRAIN: --mark reads the watermarks, adds one issue and writes them all back, so a corrupt file would have destroyed 179 and 180 while printing a normal success line. BOTH WERE LATENT NOT FIRED - the file measured readable, 332 bytes, keys 179/180/230 intact. ATTRIBUTED, not assumed: the control_app site is _shadow_watch_stored at 24081, introduced v2982, found by matching each candidate to its ENCLOSING FUNCTION across the baseline tree and today because line numbers drift 26,662 to 35,443 lines while function names do not; handoff.py:77 is v3301, mine. ⚠ MY FIRST BISECT USED THE WRONG REFERENCE and over-reported 10+ candidates against a +1 delta - the ratchet compares to the BASELINE FILE (1240f2a8, 2026-09-04), not the last green CI run, and against the right tree it reconciles exactly at 34 then 35. THREE STATES: {} is ABSENT and is a MEASUREMENT, a dict is read, None is UNREADABLE and no write may proceed on it. ⚠ THE LAW WAS PROVEN RED BEFORE THE FIX EXISTED - 2 failures showing the readers collapse malformed to {}, 2 errors showing the writers CRASH on None rather than refuse, and 1 PASS on the vault baseline, which is what proves it tells the guarded store apart from the unguarded ones rather than failing on everything. 3 red-proofs.",
         ),
    Gate("test_row_remembers_its_cap", [sys.executable,
                          os.path.join(HERE, "test_a_row_remembers_what_it_was_cut_to.py")], 60,
         why="v3339 (#77) - A ROW REMEMBERS WHAT IT WAS CUT TO. The answer-head cap was written in FOUR places: three slices in second_eye_run (200 unreached, 400 reached, 200 unreached) and the writer's own ANSWER_HEAD_CAP of 600. The RUNNER cut first, so a row capped at 400 never reached 600 and the re-judger treated it as a whole answer. MEASURED on 843 rows: 381 sat at exactly 400 while prefixOnly reported 98, and the census - counting only the writer's 600 - reported 91. Two readings disagreeing because one number lived in four places. The runner now passes the FULL answer and DECLARES head_cap; the writer cuts ONCE and records headCap on the row; the re-judger asks the row. Re-measured on 847 rows: prefixOnly 478 and agree fell 554 to 192 - THREE HUNDRED AND SIXTY-TWO rows left agreement for UNKNOWN, which is the only honest direction. ⚠ A legacy row carries no headCap and nothing on disk says which cap applied, so 200, 400 and 600 are all treated as prefix-only: that can only REMOVE claimed agreement, never manufacture it. ⚠ The default resolves at CALL time because ANSWER_HEAD_CAP is defined BELOW record() - a signature default would not even import. 3 red-proofs.",
         ),
    Gate("test_unparsed_answer_is_not_a_defect", [sys.executable,
                          os.path.join(HERE, "test_an_unparsed_answer_is_not_a_defect.py")], 90,
         why="v3346 (#101) - AN UNPARSED ANSWER IS cannot-tell, NEVER A DEFECT. v3343's look said 'The diff is correct. No defects, races, contract mismatches, leaks, or unreachable states are present' and was filed verdict=findings with ONE finding whose text was THE WHOLE ANSWER, REACH line and clean verdict included. The cause is the PARSER not the declaration: _findings_from starts a block only on a numbered or bulleted line and joins everything else onto the block above, so an answer with no such line comes back as one block containing everything - a parse that found no structure, relabelled as the worse of two. _declares_none is NOT widened and must not be: the phrasing that slipped past it is a comma-tail between No defects and are present, exactly what #76 measured and REFUSED because _claims_a_defect covers only 103 of 628 findings-rows. THE BLAST RADIUS WAS MEASURED AND MY FIRST DESIGN WAS REFUTED BY IT: firing on structure-absence alone would have reclassified 172 of 637 findings-rows including v2180 FINDING 1 Saved OFF is overruled by an env ON, a real defect with no bullet at line start - the same wrong-in-both-directions trap _verdict_for already fell into at v2808 and v3198. With the phrase test the radius is 8 of 637 and reading them they are the SAME defect being corrected (v2805, v2850, v2851, v3147, v3207, v3266 all say the diff is correct or no defects found); ONE is a genuine wrong flip, v2837, and it lands on cannot-tell not clean so nothing is cleared and a re-read is prompted. The phrase test is DOWNGRADE-ONLY and a law pins structurally that it can never reach a clean return. cannot-tell is not a new word - it is already in PARSER_VERDICTS and 13 rows use it. 6 cases, 3 red-proofs"
         ),
    Gate("test_a_bare_name_cannot_price_an_item", [sys.executable,
                          os.path.join(HERE, "test_a_bare_name_cannot_price_an_item.py")], 120,
         why="v3368 (#60) - A BARE NAME CANNOT PRICE AN ITEM. His ask was route to garbage vs HIGH QUALITY and he named the case outright, even base item with buffs socketed items, then gave the vocabulary: all these drop socketed item and ethereal items and base items with or without sockets white/blue/gold/unique/green for set. So a BASE ITEM VALUE IS DECIDED BY SOCKETS, ETHEREAL AND QUALITY, not by its name - and the pipeline kept NONE of the three. MEASURED on his real stores: a sighting row complete field list is name, lane, kind, witnesses, conf, lastSeenTs; socket/ethereal/quality occur ZERO times across all three vault stores over 44 rows; and the reader declared return contract is name, kind, count, conf, lane, throwOut, throwWhy. AND THE READER WAS ALREADY LOOKING - sockets appear in VAULT_READ_PROMPT but ONLY as throw-out criteria (sockets and no magical text, white base no sockets), so it used them to form a junk opinion and DISCARDED THE FACT. A plain Gorgon Crossbow and an ethereal 4-socket one arrived as the SAME ROW and no price list can separate them because the distinguishing information was never stored. That is heart-first rule 6 verbatim, the third instance of that exact shape already carved there after which SURFACE a frame showed stored as panel 1019, and which FRAMES carried a panel stored as panels 18 frames 2385. THE KEYS GO IN THE TEMPLATE OR THEY NEVER COME BACK: v2011 measured this on throwWhy - read by the parser, absent from the template, therefore never emitted, because a model told to reply with STRICT JSON matching a template emits the template keys. NULL IS NOT ZERO AT ALL THREE FIELDS: sockets 0 is a MEASUREMENT that it has none, null is could-not-tell; eth False is visibly-not-ethereal, null is unknown; collapsing either invents a fact about his loot and these feed a decision about what to throw away. Sockets are bounded 0..6 BY THE GAME, so 7 is a misread rather than a rare item. An unrecognised colour is UNKNOWN, never a nearest match. His own words map in: green to set, normal to white, magic to blue, rare to gold. Existing rows are NOT back-filled - they were read by a prompt that never asked, so they stay null, and VAULT_PROMPT_VER moves vp2017 to vp3368 so a row records which prompt produced it. PRICES ARE DOWNSTREAM OF THIS: an averaged price cannot be applied to a row that does not say whether the item is socketed. 4 red-proofs.",
         ),
    Gate("test_a_tally_cannot_be_asked_which", [sys.executable,
                          os.path.join(HERE, "test_a_tally_cannot_be_asked_which.py")], 120,
         why="v3374 (#28/#121) - A TALLY CANNOT BE ASKED WHICH. His #28 ruling is WIDEN THE LAW so panel-sourced names auto-bank (the 96), and the heart row reported the 96 faithfully for versions while nothing could act on it: _named_sessions classified EVERY NAME as panel/floor/chronicle and then kept only the COUNTS. The verdict was computed per name and dropped at the aggregation, so 96 could be reported and never addressed - a widening has nothing to widen ONTO while the population is a number. That is heart-first rule 6, persist what you KNEW rather than a summary of it, and it is the fourth instance of that shape hit in this session alone. THIS LANE WAS ALREADY BITTEN BY THE COARSER VERSION: v3043 own comment records that cur[panel] += len(names) WAS THE WHOLE DEFECT because one frame carries stash and inventory together, so 11 names that can NEVER be a holding were counted as panel; it was fixed from per-FRAME to per-NAME and STILL only the tally survived. WHAT THE LIST SHOWED THE MOMENT IT EXISTED, AND IT RESIZED THE RULING: 96 sightings are only 26 DISTINCT names, and against his own rosters - uniques 398, runewords 105, set pieces 135, set names 34 - exactly 10 resolve. Five are Disciple SET pieces (Laying of Hands, Credendum, Dark Adherent, Rite of Passage, Telling of Beads), one is the SET NAME The Disciple which is a set name and not an item so the bankable figure is arguably 9, and four are UNIQUE (War Traveler, Dwarf Star, Magefist, Hellfire Torch). The other 86 sightings are Horadric Cube x31, Tome of Town Portal x18, Tome of Identify x18, potions, charms and bare bases. Taken literally, auto-bank the 96 writes 31 Horadric Cubes into his ownership records - so the measurement had to come before the build, and now it has. A LIST OF PAIRS AND NOT A DICT: the Horadric Cube is seen 31 times and a dict keyed by name folds repeat sightings into one, then quietly disagrees with the count sitting beside it. VERIFIED on his journal: 42 sessions, 0 mismatches against every counter. THE LOAD-BEARING CASE IS STRUCTURAL AND VENUE-INDEPENDENT because _named_sessions reads his journal ring which CI does not have: it PARSES the function and requires one placed-record for every counter increment, so a comment mentioning the key cannot satisfy it and a future branch that counts without recording goes red. The behavioural reconciliation case SKIPS HONESTLY off his machine and says so rather than passing vacuously. NOTHING HERE WRITES TO HIS OWNERSHIP RECORDS - it persists a verdict the function already reached; banking stays gated on witnesses, the door still re-gates every row, and his fences hold: 39 rares manual, floor sightings never become cells. 4 cases, 2 red-proofs.",
         ),
    Gate("test_the_budget_is_shared_not_spent_alphabetically", [sys.executable,
                          os.path.join(HERE, "test_the_budget_is_shared_not_spent_alphabetically.py")], 120,
         why="v3370 (#116) - THE EYE BUDGET IS SHARED, NOT SPENT ALPHABETICALLY. MEASURED on v3368 and verified as an exact prefix match: the admitted set was sorted(changed files minus the always-changing six)[:5]. Nothing weighed relevance, size or risk - git default sort decided who got reviewed. Diff 63,329 chars, cap admitted 8,934 (14%); reached console_doctor, control_app, corroborate, run_gates and the new test file; DROPPED tv/tv_diablo.py and tv/vault_retro.py, which were v3368 ENTIRE subject. The eye said so itself unprompted: the only consumer of the three new fields is the new doctor check, its producer lives in the missing files - it had been shown the READER and never the WRITER. TWENTY-THREE engine files sort behind all 460 tv/test_ files and are therefore structurally last in every payload: the whole vault lane plus tree_busy, tv_diablo, unknown_age, verdict_provenance, window_visibility, write_census, write_witness. THE FEEDBACK LOOP: the standing order is JOIN GATE HEART BANK so nearly every version adds a large new test file, which alphabetically lands AHEAD of the engine it protects - the law crowded out its own subject. CORROBORATED BY A RECORD WRITTEN BEFORE THE DIAGNOSIS EXISTED: 16 of 19 ledger rows carrying an absent list (84%) lost a .py file, tv_diablo.py alone 9 times, and #97 logged that v3330 lost tree_busy.py, its own subject - tree_busy.py is one of the 23. DESIGN CHOSEN BY MEASUREMENT over 30 real versions and 182 changed code files: alphabetical 68/182 37.4%; engine-first ordering 74/182 40.7% which was my first instinct and is REFUTED; fair share with no floor 182/182 but 26 slivers under 15%; fair share with floor 1500 gives 151/182 83.0% at 100% median coverage and 1 sliver. THE NO-FLOOR VARIANT IS A TRAP AND THIS FILE ALREADY RECORDS WHY TWICE: v2803 the payload ended at a bare return and the eye returned TWO high-severity defects about a function whose last two characters the cap had removed; v2850 reported drift as never declared when its declaration sat above the first changed line. A sliver MANUFACTURES findings and a false one costs more than a missed one. THREE DEFECTS THIS FIX HAD BEFORE IT SHIPPED, ALL FOUND BY RUNNING IT ON A REAL DIFF: a slice cut BEFORE its trailing newline merged two files so the second became invisible to the eye and to every parser including the absent accounting, and the note claimed vault_retro.py 45% while re-parsing the output could not find it at all; a line-boundary cut can COLLAPSE because WINDOWS_SHIP.json is one long line so the cut landed at 6%, meaning the floor must be judged on the slice AFTER the cut; and the engine-first ordering was measured and dropped. The law own sliver case also failed on its first run against a COMPLETE 20-line file at 691 chars - short is not truncated, so it now judges only the files the note names as cut. 9 cases, 4 red-proofs.",
         ),
    Gate("test_a_corrupt_source_is_not_an_empty_one", [sys.executable,
                          os.path.join(HERE, "test_a_corrupt_source_is_not_an_empty_one.py")], 120,
         why="v3371 (#118) - A SOURCE THAT ARRIVED AND WOULD NOT PARSE IS NOT AN EMPTY ONE. CI swallow ratchet caught this ON THE DAY v3364 SHIPPED THE FILE and it was then ignored for five consecutive versions because nobody read CI: Routine M was success on v3363 (3b1d513d) and FAILURE on v3364 (5aaffe75), which is the version that added affix_lexicon.py, then failure on v3365, v3366, v3367 and v3368. The ratchet named it exactly - RANK 1, a failed read handed back as DATA, baseline 70 now 71, WHERE IT ROSE tv/affix_lexicon.py 0 to 1. THE SITE: _strings did except Exception return empty-dict. WHY THAT IS A LIE HERE: build() ALREADY distinguishes an ABSENT source and says so precisely, but a source that ARRIVES AND WILL NOT PARSE became an empty dict and sailed through - resolve finds no hits, the lexicon reports 0 affixes, and classify answers UNKNOWN for every name in the game. DEMONSTRATED END TO END rather than inferred: stubbing _pull to return garbage for every source returned a COMPLETE-LOOKING lexicon with no reason string, while stubbing it to return None correctly refused with no source could be pulled. On a screen that reads as the game has no such affixes rather than I could not read the file - a confident zero with no author, on the exact 269 magicPrefix / 298 magicSuffix / 690 baseType vocabulary the item work depends on. THE RATCHET OFFERED TWO WAYS OUT AND ONLY ONE IS HONEST: either make the failure report UNKNOWN, or if the caller genuinely treats the default as failure say so at the site and lower the baseline deliberately. The caller does NOT treat it as failure - it builds a lexicon from it - so lowering the baseline to 71 would have recorded a defect as a decision. ABSENT AND CORRUPT MUST NOT COLLAPSE INTO EACH OTHER EITHER: an absent blob is already counted in absent, and naming it unparseable would report the wrong cause and send the next reader hunting a corrupt file that does not exist, so the blob-is-not-None test keeps them apart and a case pins it. 7 cases, 3 red-proofs.",
         ),
    Gate("test_a_fact_the_reader_saw_must_reach_the_row", [sys.executable,
                          os.path.join(HERE, "test_a_fact_the_reader_saw_must_reach_the_row.py")], 120,
         why="v3369 (#60) - A FACT THE READER SAW MUST REACH THE ROW. v3368 taught the prompt to ask for sockets/ethereal/quality and normalize_item to parse them, it shipped, and the facts STILL never reached his store, because the chain is SIX links and only the first two were built: the prompt asks and the parser parses, then the sight dict drops all four, then _witness_rows drops all four, then the owned and unsure rows drop all four, and vault_seen.json never receives them. MEASURED the day after v3368 shipped: 44 banked rows, 0 carrying sockets/eth/quality. The cross-family eye said the same from the other side unprompted - the only consumer of the three new fields is the new doctor check, its producer lives in the missing files - because it had been shown the READER and never the WRITER. THIS PROJECTION HAS EATEN A FIELD FOUR TIMES NOW and its own comments record the history: conf at v1786, the witness id at v2209, the crop at v2239, each found late and repaired by hand, each invisible until something downstream read a confident blank; v3368 four make it the fourth. THE CURE ALREADY EXISTED ONE BOUNDARY LOWER - v2074 hit the identical shape at apply_payload after FOUR silent drops (v1986, v1996, v2004, v2006) and closed it with APPLY_NOT_SHIPPED, a declared list so an omission is deliberate or it is a test failure, and nobody carried that discipline up to the projection above it. WITNESS_NOT_CARRIED does that here and the declared-field case is what makes a FIFTH drop loud instead of silent. THE ROW CARRIES A SET, NOT A VALUE: a stash holds TWO Gorgon Crossbow, one ethereal 4-socket and one plain, different items worth different money folding to the SAME (name, lane) key - measured on his live store, 4 of 44 rows already carry more than one witness (Horadric Cube 20, War Traveler 4, Magefist 2, Gheed Fortune 2). A row-level sockets would be a one-to-many fact in a one-to-one store where setdefault keeps the first and d[k]=v keeps the last and neither warns, so the SIGHTING carries what one look saw and the ROW carries the distinct variants. ZERO AND FALSE ARE ANSWERS: the carry loop tests is-not-None and never truthiness, because if e.get(eth) would throw away every definitely-not-ethereal reading as though nobody had looked, on a field that decides what gets thrown out. THE LAW FOUND ITS OWN FALSE POSITIVE ON ITS FIRST RUN: the declared-field case set every sight key at once, which forced the mutually exclusive crop and cropWhy arms into one state and accused cropWhy of being silently dropped when the elif is deliberate - the code was right and the fixture was not, so it now probes ONE FIELD AT A TIME. 11 cases, 5 red-proofs.",
         ),
    Gate("test_a_dead_folder_is_not_a_frozen_screen", [sys.executable,
                          os.path.join(HERE, "test_a_dead_folder_is_not_a_frozen_screen.py")], 120,
         why="v3366 (#115) - A DEAD CAPTURE FOLDER IS NOT A FROZEN SCREEN. MEASURED 2026-09-19, same code, two roots, minutes apart: root=~/gb-shelf said FROZEN, 1 of 17 comparable window series stopped painting, 425 PNGs, newest capture 178.9 HOURS old; root=<where the seat writes> said MOVING, all painting, 2,692 PNGs, newest 0.4 h old. The seat moved where it writes, this tool kept reading the folder it left behind, and a folder nobody writes to has a newest-two that are BYTE-IDENTICAL BY CONSTRUCTION - so it reported a dead compositor for 7.5 days about a screen it was not looking at. NOTHING ERRORED: no exception, no empty result, no missing file; it ran every time it was asked and answered fluently about the wrong folder. THE FIX IS NOT THE PATH - repointing the constant fixes today and rots the next time the seat moves. newestAgeS now rides on EVERY verdict so a reader can judge a MOVING or FROZEN answer without rerunning anything, and a root staler than the bound answers UNKNOWN naming the age, because that is a statement about the RECORDER and it must never share a word with a statement about his screen. THE ARM SITS ABOVE THE FROZEN ARM ON PURPOSE - below it counts[frozen] wins first and the age is computed, stored and never consulted, which is computed-and-dropped, this repo most repeated defect. THE RESOLVER PICKS THE FRESHEST KNOWN ROOT, NOT THE FIRST, and the chosen root travels on every verdict beside its age, so the day the seat moves again this follows it and says so; it is memoised per process because report() resolves the root more than once and the live folder is ~6,000 files a walk. THE BOUND IS MEASURED WITH ITS DENOMINATOR: across 2,804 live captures the gap between consecutive frames is median 8.0s, p90 58.0s, p99 1,070s, worst-in-history 0.8 h; the dead folder sat at 178.9 h, 220x that worst live gap, so 2 h is ~2.5x the worst live case and ~1/90th of the dead one and separates them by a wide margin rather than splitting them finely. ALSO ONE RESOLVER FOR BOTH MODULES: frozen_frames hardcoded the same path with no env override while frozen_frame_watch honoured TV_GB_SHELF, so pointing one pointed only one. Fixtures fabricate PNG headers in a temp dir and never read his capture folders. 4 red-proofs.",
         ),
    Gate("test_the_recorder_keeps_its_own_evidence", [sys.executable,
                          os.path.join(HERE, "test_the_recorder_keeps_its_own_evidence.py")], 120,
         why="v3365 (#24) - THE RECORDER KEEPS ITS OWN EVIDENCE, AND KEEPS IT BEFORE IT DESTROYS IT. #24 sat unactionable across 27 events because every row says the same unusable sentence - the stage was open for 12s and had nothing on it - which records THAT nothing was there and never WHAT was there, the one fact separating a stage that never painted from one that painted where nobody looked. MEASURED on his real tv/ui_faults.jsonl: 200 rows, 8 carrying a `before` snapshot (4 percent), 11 ui_fault_record call sites, 1 passing before. A THREE-LINK CHAIN WITH THE MIDDLE AND FAR END BOTH CUT: ui_fault_record has STORED `before` since CF-4 whose own comment reads the reload destroys the only evidence; the /api/ui_fault route called it with (kind, why, where) and DROPPED before; the JS self-heal closed the stage FIRST and reported after. So the storage end was built and waiting while neither end that could fill it did - the third instance of that shape in one day. THE ORDER IS THE WHOLE FIX: classList.remove and th.hidden=true destroy the measurement, and a snapshot taken AFTER them is not a smaller snapshot, it is a snapshot OF THE DESTRUCTION - same fields, same shape, all zeroes forever, and it would look entirely correct in review. So the order is pinned by position within the bounded self-heal block, not by mere presence. The snapshot records cards, scrollH, clientH, innerH, sessions, thW/thH, scrollY, painted, loaded - cards>0 with scrollH>>clientH is painted-off-screen, cards==0 is never-painted, and without both the row still cannot tell them apart. It is wrapped and records measureFailed rather than throwing, because a stage that cannot close itself is worse than the fault being fixed. 4 red-proofs, and one of them was rewritten at authoring time because the first cut only appended a comment - an INERT sabotage that would have read BLIND against a perfectly sound case.",
         ),
    Gate("test_a_composed_name_is_not_an_unknown_one", [sys.executable,
                          os.path.join(HERE, "test_a_composed_name_is_not_an_unknown_one.py")], 120,
         why="v3364 (#60) - THE VAULT CAN NOW NAME A MAGIC OR RARE ITEM. His ask: the vault and the AI item checker must know every item and must know what to route to garbage. The roster names uniques, sets and runewords - 1,059 names - and could name nothing magic or rare, because those names are COMPOSED at drop time from four affix tables plus a base type rather than drawn from a list. I told him magic and rare cannot have a roster and he corrected me: no finite NAME list, but a finite VOCABULARY, and his 28 GB install ships it. MEASURED off his own install: magicPrefix 269, magicSuffix 298, rarePrefix 42, rareSuffix 152, baseType 690. MEASURED over his 43 real unsure rows: GRAIL 14, BASE 12, MAGIC 8, RARE 4, UNKNOWN 5 - Chaotic Grand Charm of Greed parses as chaotic + grand charm + of greed, and Blood Gyre / Death Loop / Dread Grasp / Bone Visor as rare prefix + rare suffix. THE ASYMMETRY IS THE SAFETY MODEL: a consumable or bare base reading as PROTECTED means his stash never empties, so that direction is checked BY NAME and Sacred Rondache, Bone Knife, Horadric Cube, Super Mana Potion, Ring and Jewel all land BASE. classify() never returns a best PARTIAL - an unmatched token or two parses of differing kind is UNKNOWN. TWO TRAPS PINNED, both found by reading the real data: item-names.json is NOT a base-type list (1,593 names, uniques included - Spirit Ward and Death Cleaver are in it; the base TYPES are 690 from armor/weapons/misc), and the field is `vocab` not `kind` because the unsure row has carried a hardcoded kind:item since v2051. THE TAIL-STRIP WIDENING STAYS REFUSED on a measurement taken with BOTH SIDES CASE-FOLDED - the first cut compared lowercase roster names against TitleCase item names and agreed no matter what was in it, reporting a reassuring 0; folded properly it is death cleaver -> death, spirit ward -> spirit, venom ward -> venom, three uniques collapsing onto three runewords in vault_key AND chronicle_key, permanently. 5 red-proofs.",
         ),
    Gate("test_a_file_can_arrive_and_still_be_unread", [sys.executable,
                          os.path.join(HERE, "test_a_file_can_arrive_and_still_be_unread.py")], 120,
         why="v3363 (#114) - A FILE CAN ARRIVE AND STILL BE UNREAD. absent_from asks whether a changed file reached the payload AT ALL and answers by looking for its `diff --git` header; truncation cuts MID-FILE, so a file whose header arrived and whose body was chopped is absent-clean, blind_to-clean and unread. MEASURED 2026-09-19 with the shipped function over 16 versions: 67 files ARRIVED and 8 came in under half their bytes - bible.html 259/8629 (3.0%), test_a_partial_look_is_not_agreement.py 428/11337 (3.8%), test_the_shelf_tabs_are_the_real_sessions.py 196/3406 (5.8%), test_the_shelf_shows_reels_before_analysis.py 1224/12586 (9.7%), visual_lock_invariant.py 64/516 (12.4%), prune_wilson.py 8318/27748 (30.0%), second_eye_ledger.py 3499/7200 (48.6%). AND THE FIRST CUT WAS 71% NOISE, caught only by pointing it at his real history: it flagged 41 of 100 with 33 at exactly 0.0%, files that did not arrive SHORT but did not arrive at all and were already in `absent` - the v3354 furniture defect re-created two versions after I fixed it, invisible to a fixture that by construction contains no wholly-cut file. v3354 settles it and is self-incriminating: second_eye_ledger.py is the file that version exists to change, its header arrived, and the row was filed blind_to [] verdict clean while the eye held under half its own subject. v3361 repeated it at maximum volume - the answer OPENED with \"REACH: 19/92 hunks\" naming the pre-push hook and the scoped walk, the entire version, as unjudgeable, and the row still read clean. THE FRACTION IS STORED, NEVER A FLAG: got/total per file keeps the bar in the READER (REACH_CUT_BAR, measured at 0.50 naming 4 of 47) where it can move without rewriting history - a bar baked into the store is the shape of the $5 he corrected me on and of the 0.22 threshold sitting above a signal maxing at 0.133, a branch that never ran. Measured against the PRE-TRUNCATION body so it charges the transport and not the comment/ship-note strips, which exist to BUY reach. absent and reach are kept as different questions with different remedies. The header walk is now ONE shared _file_sections used by both the strip and the measurement. 4 red-proofs.",
         ),
    Gate("test_the_machine_banner_is_one_sentence", [sys.executable,
                          os.path.join(HERE, "test_the_machine_banner_is_one_sentence.py")], 120,
         why='v3362 (#37) - ONE BANNER, ONE SENTENCE, ONE WRITER, AND IT NEVER CLAIMS A SEPARATE ECONOMY. His ruling: the machine-identity banner may claim its own world and must NOT claim separate economy. #37 was blocked all day on one value only the GrokBot seat could read; it arrived ~17:25 IDT - window.D2R_BUILD.id = v3360, banner rendering as LINUX - its own world - Mac untouched - and the value revealed there was NOTHING TO FIX. MEASURED in bible.html: its-own-world appears at L3840 COMMENT, L4274 COMMENT and L48984 CODE, so exactly ONE code writer; Mac-untouched at that same L48984; and all four separate-economy hits (L42631 comment, L42653, L42749, L48928) belong to the LADDER, a different feature. The ruling was already kept and this law exists so it cannot quietly stop being kept. ⚠⚠ THE LADDER RIBBON IS NOT THIS BANNER AND A FILE-WIDE BAN WOULD DELETE A CORRECT SENTENCE: the ladder ribbon says LADDER ACCOUNT - separate economy - your main account is untouched, and that claim is TRUE there because items forged on a ladder character do not sync to main. One phrase serving two features is the trap; this law pins the MACHINE banner by its own writer and a dedicated case PROVES it leaves the ladder alone, plus a case that refuses to judge at all if the two elements ever move within 200 chars of each other. ⚠ COMMENTS ARE NOT CLAIMS - two of the three its-own-world hits are prose explaining the feature, and grading them would make the law red on documentation, the defect that has cost this repo five versions. ⚠ THE BASELINE IS PINNED TOO: an empty banner is not compliance, so the law also requires the PERMITTED claim to still be there. 5 cases, 3 red-proofs'
         ),
    Gate("test_the_hook_asks_the_console_not_its_pid", [sys.executable,
                          os.path.join(HERE, "test_the_hook_asks_the_console_not_its_pid.py")], 120,
         why='v3361 (#98) - THE HOOK ASKS THE CONSOLE WHETHER IT IS STALE, IT DOES NOT TIME ITS PID. hooks/pre-push compared the LISTENER PROCESS START to tv/control_app.py mtime and warned on every push where the file was newer. MEASURED 2026-09-19 on his live console in one minute: the process started Fri Sep 18 23:37:38, control_app.py was written 2026-09-19 16:48:34 - 17 hours later, so the heuristic warned - and /api/status answered moduleFreshness {known true, stale FALSE, loadedAtMs > srcWrittenMs, say: this server is the file on disk}. A process can re-exec, a supervisor can reload it, and a module can be imported long after boot, so process age is not module age. v3288 built module_freshness() for exactly this reason and its own docstring says the PID heuristic can be fooled by a supervisor or a re-exec; the first-hand answer has been on /api/status ever since and this hook went on using the heuristic anyway - an answer built, published and never asked for. THREE STATES NOW, NOT TWO: stale warns and names tvd-scan.sh, fresh is silent, and an unreachable console or known=false prints UNKNOWN and explicitly NOT a warning, because a warning fired on a state nobody measured is the noise this block has been making for weeks. ⚠ THE HEURISTIC WAS WRONG IN BOTH DIRECTIONS, not merely noisy: a console restarted a second before a push would PASS it while serving a module imported hours earlier from a since-rewritten file. Process age can be wrong either way; import age cannot. ⚠ AND THIS LAW CAUGHT ITS OWN BAD WINDOW ON THE FIRST RUN: the unknown-branch case anchored on the bare token, which lands inside the EMBEDDED PYTHON that prints it, ~40 lines above the shell branch that reacts to it - so the window graded the stale branch and reported the unknown one missing. Both branches are now anchored on their shell case labels and bounded at the closing ;;. 5 cases, 3 red-proofs'
         ),
    Gate("test_a_ship_note_is_not_code_the_eye_must_read", [sys.executable,
                          os.path.join(HERE, "test_a_ship_note_is_not_code_the_eye_must_read.py")], 120,
         why='v3360 (#109) - A SHIP NOTE IS PROSE AND THE EYE BUDGET IS NOT FOR PROSE. run_gates.py carries one why= per gate, a paragraph explaining what a law is for, and _strip_comments cannot touch it because it is a string LITERAL - so the second eye pays full price for it out of a budget that truncates at 9,000 chars. MEASURED on v3354 by share of the 6,844 chars that reached the eye: corroborate.py 59.3%, run_gates.py 31.5% (almost entirely ONE why=), control_app.py 9.2%, and tv/second_eye_ledger.py - the file that version exists to change - 0%. #97 found the same shape on v3333 at 44.9% and nothing acted on it. Over the last 24 versions the strip recovers 7 changed files that never reached the eye: 65 missed -> 58, 6 versions better, ZERO worse. ⚠⚠ MY FIRST MEASUREMENT SAID IT MADE THREE VERSIONS BLINDER AND THAT WAS MY OWN TOOL: collapsing a multi-line why= onto one line pulls the next `diff --git` off the start of its own line, so a line-anchored file counter stops seeing a file that is present - for v3346 the header sat at offset 1,362 of a 9,000 cap, EARLIER than before. The newline count is now preserved and that is the whole trick. ⚠⚠⚠ AND THIS LAW CAUGHT A REAL DEFECT IN THE HELPER ON ITS FIRST RUN: the pattern allowed an optional paren after the string chunks and on `why="a one line note"),` it ATE THE CLOSING PAREN, handing the eye a diff whose Gate(...) call no longer closes - the gate-insert-missing-comma family, and invisible to the file-header count I was measuring with because a broken diff still has its diff --git lines. The pattern now touches why= and its string chunks and nothing else; a parenthesised note is left alone, which costs reach and cannot cost correctness, and the 65 -> 58 was RE-TAKEN on the narrowed pattern rather than carried over. ⚠ STATED LIMIT: in a diff every continuation line begins with + - or a space, which the pattern cannot cross, so a five-line note loses its first chunk and keeps the rest; widening to cross that marker would start eating ordinary string literals and has no measurement behind it. ⚠ It does NOT widen the cap - v3299 ruled that cost is HIS. 5 cases, 3 red-proofs'
         ),
    Gate("test_an_unreadable_store_is_not_an_absent_one", [sys.executable,
                          os.path.join(HERE, "test_an_unreadable_store_is_not_an_absent_one.py")], 120,
         why='v3355 (#108) - AN UNREADABLE STORE IS NOT AN ABSENT ONE, AND THE ERRNO IS THE WHOLE DIFFERENCE. v3325 was titled \'a store is never written over an unread one\' and put that rule in THREE loaders, all written as `except IOError: return {}` with `except Exception: return None` beneath, commented malformed/unreadable. In Python 3 `IOError is OSError` - measured True - and PermissionError, IsADirectoryError and the EMFILE family are subclasses, so an EXISTING GOOD store that merely could not be READ took the ABSENT arm. The second arm only ever saw MALFORMED: a JSON error is a ValueError, an unreadable FILE is an OSError. MEASURED on a real file holding watermarks 179, 180 and 230 at mode 000: `_marks()` returned {} and `--mark` would write {"999": 1} over it, destroying all three. The three sites are handoff._marks, control_app._shadow_watch_stored and control_app._rnf_load, and every one feeds a caller that writes the whole dict back. THE PROSE ABOVE EACH SITE ALREADY DESCRIBED THE DEFECT - _shadow_watch_stored\'s own comment says \'ABSENT vs UNREADABLE, and here it is destructive\' and the code beneath it did exactly that. THE CLASS WAS SWEPT AND THE UNSCOPED NUMBER IS ON THE RECORD: 127 handlers in tv/ catch IOError/OSError broadly, THREE are this defect, and the right idiom was already in the same file three times. AND THE RATCHET COULD NOT SEE ITS OWN FIX: swallow_census ranked on what a handler RETURNS and never on what it CATCHES, so the three repairs moved the count by ZERO - a ratchet whose number survives the repair of the thing it flagged teaches its reader to re-baseline. It now refuses the pass to a bare except, to `except Exception`, and to any tuple carrying a wider name; MEASURED 6 of 76 rank-1 sites catch absence only, rank1 76 -> 70, and the baseline moves down with it in this same commit (test_agent.py leaves rank1, control_app 34 -> 31). ⚠ CI HAD BEEN SHOUTING FOR TEN RUNS - Routine M reported 76 against 74 on every push since at least v3344 and nothing surfaced it, because the pre-push derives its gates from CHANGED TEST FILES and never runs the full set. A red nobody reads is the same as a green, so a console_doctor row now carries the count WITH its baseline. 11 cases, 5 red-proofs'
         ),
    Gate("test_a_stamp_is_not_a_blind_spot", [sys.executable,
                          os.path.join(HERE, "test_a_stamp_is_not_a_blind_spot.py")], 120,
         why='v3354 (#106) - A VERSION STAMP IS NOT A BLIND SPOT. v3349 gave the ledger a `partial` counter - how many looks never saw part of the change - which was the right question pointed at everything. MEASURED 2026-09-19 over the 7 rows carrying `absent`: it flagged 7 of 7, and 12 of their 16 absent-file entries were bible.html or tv/tv_diablo.py changed by exactly two lines, both carrying a version token. Only TWO rows missed anything a reviewer could have held an opinion about - v3349, filed clean over a payload that never contained its own 218-line subject, and v3351. A warning that fires on every row carries no information, which is the same defect as a gate that is always green. THE FIX CLASSIFIES THE CHANGE, NEVER THE FILENAME, and an allow-list was measured and refused before building: across the last 120 version commits SIX files change in >=99% of them - WINDOWS_SHIP.json, TASKS.md, tv_diablo.py, bible.html, control_app.py, BLUEPRINT.md - and two of those are the files most often the real subject. One filename, opposite verdicts: bible.html at e850b847 is SUBSTANTIVE (37 lines, the apostrophe fold) and at c08875ad is STAMP (2 lines, both version tokens); control_app.py at d2b3f3cf is SUBSTANTIVE (8 lines, the rider route) and at c08875ad is STAMP. An allow-list would excuse the two substantive rows - a genuinely blind look waved through on the day one of those files IS the subject. THREE STATES, matching `absent` exactly: a dict is measured, {} is measured and nothing missing, null means reach was never established which is all 867 prior rows - and those are classified ON READ from their own sha, the same measurement from the same source taken later, never assumed to be stamps. UNKNOWN IS NEVER AN EXCUSE: the classifier only ever REMOVES a warning and may do so only where a stamp was MEASURED, so an unreadable diff stays outside it. THE FALSE-NEGATIVE DIRECTION WAS HUNTED, NOT ASSUMED AWAY: swept over 80 version commits, every stamp-classified change to a file this classifier can be handed is exactly 2 lines (bible.html 2/2/2 n=71, tv_diablo.py 2/2/2 n=80, control_app.py 2/2/2 n=52); the only large all-version-token diffs are TASKS.md at up to 9 lines and WINDOWS_SHIP.json at 4, and neither can ever reach here because absent_from asks git for *.py *.mjs *.sh *.html only - a bound this law pins rather than trusts. Classified AT THE DOOR inside record() so no caller can forget. LIVE EFFECT on his ledger: partial 7 of 7 down to 2 of 7, and both survivors now NAME the file nobody saw instead of counting. 10 cases, 4 red-proofs'
         ),
    Gate("test_simulator_says_what_it_could_not_load", [sys.executable,
                          os.path.join(HERE, "test_a_simulator_says_what_it_could_not_load.py")], 120,
         why="v3353 (#107) - A NAME THE SIMULATOR COULD NOT FIND IS UNKNOWN, NEVER A HOST DEPENDENCY. ci_sim exists to answer one question - does this test lean on something only his Mac has - and it was answering that question about names it had never loaded. MEASURED: asked for a class living in test_an_examined_panel_is_not_an_unread_one.py it raised AttributeError module test_control has no attribute, unittest wrapped that loader error as a _FailedTest, the runner counted it among errors, and the tail printed 🔴 1 test(s) depend on something only HIS machine has. THE TEST NEVER RAN. A name the tool cannot find is UNKNOWN; turning it into a confident claim about his machine is the exact collapse the file was written to prevent, committed by the file itself. SECOND HALF: main() did import test_control and loaded names from that module ALONE, under a banner reading CI SIMULATION - the suite as a runner sees it, so every other test file was outside its reach and always had been. Both are fixed: loader failures are detected BEFORE anything counts them and exit 2 saying could not LOAD ... that is UNKNOWN not a host dependency; the search falls through from test_control to whichever tv/test_*.py DEFINES the name; and every run now prints its REACH so no-known-host-dependency can be read against a population. Import failures during the search are swallowed on purpose - a module that cannot import here is not the subject of the question, and letting one bad file abort the scan would turn a findable class into an unfindable one. ⚠ IT ALSO CORRECTED A STANDING CLAIM OF MINE: I had recorded that #99's four seal ERRORs are CI-ONLY, a VENUE fact, because they pass on his Mac. With the loader fixed the class runs 6 tests and reports NO known host dependency - so passing locally plus tripping no known stub does not make it venue, it makes the cause UNMEASURED, which is a different word and the honest one. 5 cases, 3 red-proofs",
         ),
    Gate("test_partial_look_is_not_agreement", [sys.executable,
                          os.path.join(HERE, "test_a_partial_look_is_not_agreement.py")], 90,
         why="v3349 (#104) - A LOOK THAT NEVER REACHED THE CHANGE IS NOT AN OPINION ABOUT IT. MEASURED ON v3347 THE DAY IT SHIPPED: the payload carried 8,967 of 92,115 diff chars and omitted 10 changed files INCLUDING tv/self_arming.py, the file the version exists to change; the eye answered REACH 2/2 hunks, all other listed files UNKNOWN, no concrete defect in the bytes shown; and the row stored verdict=clean. Clean means the eye looked and found nothing, and that eye said in its own first line that it could not look. THE INTENT WAS ALREADY RIGHT AND THE STORE WAS WRONG: payload_for has computed the omitted list since v3341 and used it to warn the EYE inside the prompt, and its own comment says the ROW must carry it too - which it did, as a 400-char-capped PROSE SUFFIX on `asked`. A one-to-many fact flattened into another field and truncated at the one moment keeping it was free; the fourth instance of that shape in this repo. So this version computes nothing new: it carries the LIST to the row and gives it a reader. THREE STATES ARE KEPT APART and the middle one is the point - a list means measured and these are missing, [] means measured and nothing is missing, and null or a missing key means nobody could ask, which is every one of the 860 rows written before now. Collapsing null into [] would turn we-never-checked into we-checked-and-it-was-fine. ⚠ I GOT `reached` WRONG FIRST and the correction is in the law: reached means THE SEAT ANSWERED, not that the payload reached the change - a reachable eye handed two hunks of a twelve-file change is reached=True and blind, which is exactly the v3347 row. Two questions, two fields; the second simply did not exist. ⚠ THE VERDICT RULE IS DELIBERATELY NOT IN THIS VERSION: #97 measured that 22 of 36 versions (61%) had a code file never reach the eye, so downgrading clean to cannot-tell would move a large population, and the radius CANNOT be sized from the ledger because the data was never stored - which is the defect itself. #101 already proved this session that a verdict rule designed without measurement gets refuted by the ledger, 172 of 637. Persist first, judge once there are rows to judge against. ⚠ PARTIAL LOOKS ARE NAMED, NEVER DISCARDED - what the eye said about the bytes it did see is real evidence; what must never happen is two partial looks reading as AGREEMENT about a change neither saw. 9 cases, 4 red-proofs",
         ),
    Gate("test_retired_lock_keeps_its_testimony", [sys.executable,
                          os.path.join(HERE, "test_a_retired_lock_keeps_its_testimony.py")], 90,
         why="v3347 (#31) - A RETIRED LOCK KEEPS ITS TESTIMONY: READABLE, NEVER BANKABLE. His ruling was 'leave it off and surgically remove it we need pruning' - remove the prune.arm ceremony, do not silence it, do NOT touch _PRUNE_SAFE_TO_RUN, and KEEP self_arming for the other surfaces. The removal (lock out of LOCKS, prune_wilson.py deleted, its gate de-registered) obeyed the first half. Removing PROVES['prune_wilson'] alongside them looked like the same tidy-up and did the OPPOSITE of the last half: his ledger holds 19 rows banked by prune_wilson against prune.arm (newest n=18 k=18), one unreadable row fails the WHOLE read, so _rows() returned None and ALL NINE surviving locks answered 'UNKNOWN: an unreadable proof queue fails CLOSED' - vault.apply, miniauto.run, prune.reports and reel.route all sampled and all shut. One dictionary entry, every surface at once, silently, with the module behaving exactly as designed. RETIRED now means three things and each has a case: READABLE (the pair stays declared so _row_fault accepts his rows - testimony is not mine to drop), NEVER BANKABLE (needs no new code, bank() already refuses any lock absent from LOCKS - verified it raises 'no such lock or route is declared'), and REACHES NOTHING (the clause worth proving rather than believing: dropping all 19 rows moves 0 of 9 live scores, measured). STATED CONSEQUENCE, HIS TO OWN: test_printer_wilson asserted prune.arm.after contained printer.stream - his order 'printer + reels -> theatre + shelf -> routing -> the deleter' - and that rule lived ONLY there and in the lock's prerequisite list, so retiring the lock removes the only place code enforced that the deleter waits for the river. That is the intended effect; _PRUNE_SAFE_TO_RUN survives untouched at 53 refs across 20 files and is the actual safety, pinned here. The ordering MECHANISM survives too - vault.apply and vault.forget still wait on vault.sweep_start and TestHisOrderIsEnforced drives that live chain - but no chain is longer than one step now, so the advance-to-the-next arm is asserted UNMEASURED rather than left silently passing. 10 cases, 3 red-proofs"
         ),
    Gate("test_board_folds_the_apostrophe", [sys.executable,
                          os.path.join(HERE, "test_the_board_folds_the_apostrophe_too.py")], 90,
         why="v3345 (#68) - THE BOARD FOLDS THE APOSTROPHE TOO, NOT JUST THE PYTHON STORE. His ruling was 'make it one word and unified'. v2760 fixed the PYTHON half (chron_evidence.json keyed the confluence store by RAW name so one item lived in two buckets and cross-reel corroboration could never fire) and its docstring already named the cause: bible.html spells these four items CURLY in the item rows and STRAIGHT in ITEM_VALUE, in the same file. THE BOARD HALF WAS NEVER FIXED: _chMapHas and _chSetHas decide whether a roster row reads as FOUND and they folded CASE and not the apostrophe, so _chNameKeys built [Atma's Scarab, atma's scarab] and looked them up in a map keyed with the typographic byte. MEASURED on his live board via POST /api/board_ownership: of 445 dated names exactly TWO carry that byte - Atma and Saracen - and BOTH his dates and gameFound stores key them that way consistently, so his board is not self-contradictory and the lookup simply could never reach his rows. An item he genuinely owns read as NOT FOUND. THE FOLD RUNS ON BOTH SIDES because folding only the query cannot match a map keyed with HIS byte, and the map scan runs only after a direct miss so the common path is untouched. HIS STORED BYTES ARE NOT TOUCHED - they are testimony, the reader is made tolerant. THE SAFETY HALF: item_identity already rules that the apostrophe is RENDERING and Latent/Renewed are IDENTITY, so a qualifier must never fold; verified in node that Latent Rotting Fissure does NOT match Rotting Fissure. The law strips BOTH comment kinds because its first run failed on the fix's own /* */ comment explaining the Latent rule, and the block strip is bounded at 4000 because an unbounded DOTALL removed 16.9% of this file once. 5 cases, 4 red-proofs"
         ),
    Gate("test_shelf_says_what_is_owed", [sys.executable,
                          os.path.join(HERE, "test_the_shelf_says_what_is_owed_not_who_owns_it.py")], 120,
         why="v3344 (#81) - THE SHELF SAYS WHAT IS OWED, NOT WHO OWNS IT. His console read '3 waiting on a lane (vault: 3)': it grouped owed reels by the LANE THAT OWNS them and then printed the word WAITING, which is the READ_CLEARS question asked of the OWED_BY map. shelf_driver states the split in its own comment - OWED_BY is which lane OWNS this reel, READ_CLEARS is whether a READ can clear it. rows-not-banked proves they differ: v2878 kept it OUT of READ_CLEARS because it is owed a BANK not a read, queuing it spends his money and clears nothing, so NO sweep will ever clear it - and the screen filed it under 'waiting on a lane' with the other four anyway. THREE INDEPENDENT PROSE SITES ALREADY SAID BANK and only the rendered sentence disagreed: reel_census's own docstring (panels-never-banked 3, the VAULT still owes a bank), the law that pinned the sentence (3 the vault still owes a BANK, three lines above its own assertion), and the v2878 note. Every author who described this population got it right in prose and shipped a different word to the screen. THE ROOT is that the tag was READ, used to look up the lane, and DISCARDED - the richer fact in hand at the write, where keeping it is free, the same shape as v3339's cap and v3342's second stamp. The census now keeps owedTags beside owedBy (ownership is still a real question and existing laws pin it) and the wording comes from ONE map, shelf_driver.OWED_SAYS, beside the map it describes. MEASURED on his tree: the sentence went from '3 waiting on a lane (vault: 3)' to '3 still owed (3 panels on film, nothing banked)'. owed still counts all five tags so the reconciliation still sums, and a law pins that owedTags adds up to it - a per-tag breakdown that does not sum is the authoritative-and-wrong number the header refuses to print. The rows-not-banked case is LATENT on his tree (0 today), so the law drives it from the wording map rather than from today's population. 6 cases, 4 red-proofs"
         ),
    Gate("test_rider_is_watched_not_a_vessel", [sys.executable,
                          os.path.join(HERE, "test_a_rider_is_watched_without_claiming_a_thread.py")], 120,
         why="v3342 (#93) - A RIDER IS WATCHED WITHOUT CLAIMING A THREAD, and this closes a law I broke myself. tvd-read-names-feeder shipped in v3323 with its own lane name and its own lifetime counters and NOTHING surfaced it, against his #28 ruling that the feeder be built AND watched in the same version. MEASURED: _lane_stamps saw the beat every time (strings 21, feeder PRESENT) and discarded it every time (tick_by_encloser 21, no encloser maps to it), because that map is {def: ONE stamp} and setdefault keeps the FIRST - while ast over the live source shows exactly one def stamping two lanes, _vault_autoread_loop at 24289 tvd-vault-autoread and 24311 tvd-read-names-feeder. A one-to-many fact in a one-to-one store, the same shape as v3339's cap and the owedBy tag. AND A LAW WAS SHOUTING THE WHOLE TIME: test_every_lane_stamps_its_own_beat asserted `exactly one` beat per def and has been RED in CI on every run since v3323 - eighteen versions of ['tvd-vault-autoread (_vault_autoread_loop) stamps 2'] - which is what a permanently red gate costs. The law is repaired to its OWN stated intent (its docstring says zero is the dangerous number) and NOT weakened: zero beats still fails, and a new case refuses any beat that is not a tvd- lane or the loop's own name, so an invented stamp is still filed where nobody watches and still caught. The census now keeps every stamp and emits a RIDER row for the extras, in ONE post-loop pass because a roster lane gets its row from the expansion branch which continues - the first cut emitted 0 riders for exactly the lane that needed one. A rider is NOT a vessel: the census enumerates threads and it has none, so heart.NOT_A_VESSEL's reasoning stands and vessels stays 20/0/0/0, corroborated by his live screen; it gets its own shelf naming the vessel it rides. The first cut DID count it and vessels went 20 to 21 with the rider UNKNOWN, which is a thread claimed that does not exist - that is red-proof 3. 6 cases, 4 red-proofs"
         ),
    Gate("test_payload_names_what_it_left_out", [sys.executable,
                          os.path.join(HERE, "test_a_payload_names_what_it_left_out.py")], 60,
         why="v3341 (#97) - A PAYLOAD NAMES THE FILES IT LEFT OUT, NOT JUST HOW MANY CHARS IT CUT. payload_for declared its truncation as a CHARACTER COUNT - 'truncated to 8142 of 16736 diff chars' - which is true and unusable: a count cannot say WHICH FILES are missing, so the eye answers 'the diff is correct as shown' in good faith about a payload containing none of the change under review. MEASURED by rebuilding payload_for for every version v3300-v3340 and diffing what it would send against what each commit changed (version stamps excluded): 36 versions had code changes and 22 of them - 61% - had at least one changed code file never reach the eye. In several the dropped file is the version's whole subject: v3330 lost tree_busy.py, v3315 lost second_eye_run.py, v3333 lost control_ui.html AND its own 151-line law, v3339 lost its law. The mechanism, measured on v3333: run_gates.py took 44.9% of the payload and 84% of that hunk is one why= ship-note string, so ~38% of a code review was spent on prose the comment stripper cannot touch because it is a string LITERAL, not a comment - the exact failure payload_for's own docstring warns about for control_ui.html, arriving through a .py file instead. THE ROSTER COMES FROM GIT, NEVER FROM THE FETCHED TEXT: when the python diff alone exceeds the cap the *.html show is never run, so a dropped .html is missing from the QUESTION rather than from any buffer, and deriving the set from the payload would report a confident 0 for exactly the v3333 case. THREE STATES and collapsing any two is the defect: a LIST names what never arrived, [] means MEASURED-AND-NONE, None means the roster was unreadable and is UNKNOWN never nothing-was-missed. Pins the helper, the BASELINE that a complete payload stays silent (a warning that fires when nothing is wrong is an off switch), and the JOIN - a correct helper whose names never reach the prompt or the row fixes nothing. Does NOT widen the payload: v3299 ruled that cost HIS call and pinned that the runner STATES ITS OWN REACH; this is the same move one level down. 4 red-proofs"
         ),
    Gate("test_the_world_band_leaves_room_for_the_ladder_ribbon", [sys.executable,
                          os.path.join(HERE, "test_the_world_band_leaves_room_for_the_ladder_ribbon.py")], 60,
         why="#218 - THE WORLD BAND LEAVES ROOM FOR THE LADDER RIBBON. Found by LOOKING at Grok Bot's native Linux pack: the LINUX band covered the top half of LADDER ACCOUNT on every tick while every gate was green. MEASURED headless on the same seat: the band was declared `font:var(--fw-semibold) 11px/1 inherit`; `inherit` is not a family, the shorthand is invalid at computed-value time, the band fell back to 16px and stood 35px tall against a 24px stack offset -> 11px overlap at 1280/1120/901. Longhands: 22px, overlap 0 at all five widths. A PARSE, deterministic on every machine: the band's font is valid, its line box + padding fits inside the stack offset read from the same file, and the 9 other sites with the same shorthand (deliberately not resized) may only fall. 2 red-proofs"
         ),
    Gate("test_a_reused_name_is_not_one_picture", [sys.executable,
                          os.path.join(HERE, "test_a_reused_name_is_not_one_picture.py")], 60,
         why="#197 - A REUSED FILE NAME IS NOT ONE PICTURE. The shadow log stored only the basename and the reducer grouped its per-FRAME figures by it; read.jpg is one scratch path the capture loop rewrites every read, so 131 of 1,596 both-answered rows were published as ONE mixed frame disagreeing with itself. The writer now stores picture (hashed by the caller right after Claude's read, BEFORE the shadow thread) and picture_after (after Grok's read); frames key on that identity, fall back to the name only for f_<epoch-ms>.jpg, and place everything else in NO frame, counted. A row whose picture changed between the two reads is not a comparison of one frame. The doctor row names the unattributed reads. Measured on his store: 165 frames 84/66/15 -> 161 frames 81/66/14 with 135 reads unattributed. 6 red-proofs"
         ),
    Gate("test_session_card_has_a_clock", [sys.executable,
                          os.path.join(HERE, "test_a_session_card_always_has_a_clock.py")], 60,
         why="v3333 (#80) - A SESSION CARD ALWAYS HAS A CLOCK. MEASURED on his live console: 2 of 422 sessions carry NO t0 - n=30 (s_1789330829280_66296, 753 frames, reel dated 13 Sep 23:20) and n=50 (s_1788879402448_41906, 10 frames, 08 Sep 17:56). Both hold real footage and both sit in the river, but every card site computed d0 = sm.t0 ? new Date(sm.t0) : null, so those two got a null clock: the date rendered as an em-dash and the title fell back to Session N. He reported it as cards that never paint. THE FALLBACK IS EVIDENCE, NOT A GUESS: a session id is s_<epoch-ms>_<n>, and on all 12 sessions checked where BOTH exist the embedded ms and t0 agree to the minute. ⚠ mtime CANNOT serve - all 19 reels on disk carry an mtime from one bulk pass on 16 Sep, skews 1.8 to 53.1 days, so it reports two months of footage as simultaneous; the law pins that mtime never appears in the helper. FOUR hand-rolled copies of the clock became ONE definition, and the law is a REACHABILITY check rather than a presence one: it fails if any site re-inlines the old expression. The baseline case pins that t0 STILL WINS when present, because a fallback that overrides a real reading is worse than none. ⚠ Three other t0-to-Date sites are deliberately EXCLUDED and named in the helper comment: a day-set builder and a today-filter feed COUNTS, and widening a clock that feeds a count changes the count. 2 red-proofs.",
         ),
    Gate("test_version_not_banked_into_graded_tree", [sys.executable,
                          os.path.join(HERE, "test_a_version_is_never_banked_into_a_graded_tree.py")], 60,
         why="v3330 (#72) - A VERSION IS NEVER BANKED INTO A TREE THAT IS BEING GRADED. The pre-push gate grades the WORKING TREE, not the commit, so a bump landing while a gate runs makes that green verdict describe bytes which are not the ones shipping. The tree lock was believed to be the signal and it is NOT SUFFICIENT: MEASURED 2026-09-18 during a live v3328 push, the gate flock read FREE while a pre-push had been grading for 15 minutes with Playwright smoke in flight, pid 59755. The lock is taken by run_gates, and the pre-push hook runs its browser smoke OUTSIDE that claim, so exactly the window that matters most reads as unlocked. tree_busy.why() therefore asks TWO independent questions - the flock AND a running pre-push - and returns a REASON, never a bare bool. THREE STATES: free is a measurement, busy names which signal fired, and UNKNOWN is NOT FREE, because a check that cannot tell refuses rather than waving the bank through. It RELEASES the flock immediately after testing it, since holding it would make the guard the collision it exists to prevent. The baseline case pins that a free tree still banks - a refusal that never passes is an off switch, not a guard - and the join case pins that bump_version actually consults it, because a module nobody calls is the defect this whole task is about. 3 red-proofs.",
         ),
    Gate("test_feeder_to_the_door", [sys.executable,
                          os.path.join(HERE, "test_the_feeder_hands_owed_names_to_the_door.py")], 60,
         why="v3323 (#28) - THE FEEDER THE AUTO LANE NEVER HAD, AND ITS ONE CALLER, IN THE SAME VERSION. read_names_lane.split() has always judged every journal-ring PANEL name through the REAL gate (vault_retro.gate, 0.55 conf / 2 witnesses) and separated HELD from OWED, and NOTHING called it to write - its own header said 'the accumulator has no other feeder ... they were never judged'. The module was written 2026-09-18 and lived ONLY in a scratch directory that deletes with the job: grep -rn read_names_feeder tv/*.py returned ZERO. Complete, correct, and run by nobody, which is this repo's single most repeated defect applied to his own authorised ruling. RE-MEASURED BEFORE SHIPPING, because his ruling named ~3 autoOwed and that has drained: split() state=MEASURED, names 60, auto 6, manual 54, autoOwed 0, autoHeld 1 (Crescent Moon, referents UNIQUE *and* RUNEWORD so it can never name one cell), and plan() answered ok=True bankable 0 declined 0. It banks NOTHING today - five of the six are already banked and the sixth is correctly held - and that is the honest state of the lane, not a broken feeder. ⚠⚠ WHICH IS EXACTLY WHY THE COUNTERS AND THE CALLER SHIP WITH IT: a lane that is ON with lifetime work 0 is the vault_autoreel_tick scar, so _RNF_STATE is LIFETIME (runs/banked/lastTs/owed) and owed starts None - UNKNOWN, never a confident 0. It ticks under its OWN lane name tvd-read-names-feeder and NOT vault-autoread's, because the tick it rides SPENDS money on paid sweeps while this one banks names already read and costs nothing; one supervisor row must never answer for two lanes. The door re-gates every row at the write and the board's vaultAccumApply does the landing - dated, merge-max, undoable, the same tick his hand uses - so the feeder invents no judgement of its own, and a refusal from the door is a RESULT branched on, never swallowed. THE JOIN CLASS IS NEW AND IS THE HALF THAT WAS MISSING: the recovered law's 6 cases pin what the feeder DOES when called and not one asks whether anything CALLS it. 3 red-proofs, one of which removes the caller and puts the module back exactly where it was found.",
         ),
    Gate("test_lock_state_asked", [sys.executable,
                          os.path.join(HERE, "test_a_lock_state_is_asked_not_asserted.py")], 60,
         why="v3322 (#78) - A LOCK STATE IS ASKED, NEVER ASSERTED IN PROSE. self_arming exists so a lock OPENS ITSELF once its witness survives enough distinct attacks, 'and never by anyone editing a file' - which guarantees every comment stating a lock state eventually goes false. MEASURED 2026-09-18: three production sites read 'IT SHIPS LOCKED ... may() returns False today' while may('console.pixel_rescue') answered True on 32 of 32 DISTINCT ATTACKS refused, wilson 0.893 >= 0.839, kinds 2.50 >= 1.80. It matters more than an ordinary stale comment because of WHICH lock: that block's own docstring says a wrong verdict here 'does not lose footage, it REPLACES THE WINDOW HE IS LOOKING AT'. A reader asking whether the console may replace his window reads 'ships locked' and stops - which is exactly what happened to me, caught only by calling may() instead of believing the sentence above it. IT IS A CORROBORATOR, NOT A WORD BAN: prose may say a lock is shut while it IS shut, and the law fails only when prose and may() DISAGREE, so it reds the day the lock moves and is quiet otherwise. ⚠ SENTENCE SCOPE, AND THE FIRST RUN PROVED WHY - judged per comment BLOCK it accused correct code, because a 40-line block in control_app names console.pixel_rescue in one paragraph and says 'ui_rescue_due returns False' in another about a DIFFERENT function. A claim binds to a lock only inside the same SENTENCE. REACH STATED: comments and docstrings only, run_gates why= strings NOT scanned because they are dated SHIP NOTES and 'it shipped locked' stays true of the ship forever - a law that reds on an accurate historical record is one someone deletes. 2 red-proofs.",
         ),
    Gate("test_waiting_on_you", [sys.executable,
                          os.path.join(HERE, "test_waiting_on_you_means_waiting_on_him.py")], 60,
         why="v3321 (#82) - WAITING ON YOU CARRIES ONLY WHAT IS ACTUALLY HIS. His #35 ruling defines that column as action needed FROM HIM RIGHT NOW. MEASURED on his live console 2026-09-18 it carried EIGHT rows and owner_of() answered you for all eight, while exactly ONE was his - he read it and asked 'this is the missing on me?'. Six were mine by their own sentences: engines corroborate ('the one that is wrong is not knowable from the pair alone' - he cannot arbitrate a pair neither side settles), console UI faults ('the console healed itself ... It recovered' - a report, not an errand), ledger provenance (carries its own named fix), footage has a reel (orphan_fold.py shows the plan), names banked ('no paid read is owed here' so there is nothing to authorise), stage shows the dom ('a stale composite, which every rect/content guard reports as success' - and he must not be the detector). A column that cries for him on seven rows he cannot act on is the same defect as a gate that is always red: he stops reading it and the one row that IS his goes with it. ⚠ THE BASELINE IS THE HALF THAT MATTERS MOST: the cheap way to quiet this panel is to call everything mine, which would empty the one column he relies on while looking like a fix - so 'shadow gate' is pinned as still reaching him, because its own words are 'that list is the argument for or against switching, and it is yours to read'. CLASSIFYING IS NOT MUTING: MINE and BY_DESIGN rows still render at their real state and colour, only the name on the row changes, and every key must match a REGISTERED check or the entry is dead config that silently classifies nothing while looking like it handles the row. river joints is deliberately NOT moved: it is by-design TODAY and genuinely his the day something IS safe to delete, which needs the check to answer conditionally - named as open, not silenced. 2 red-proofs.",
         ),
    Gate("test_remeasure_population", [sys.executable,
                          os.path.join(HERE, "test_a_remeasurement_covers_the_same_population.py")], 60,
         why="v3320 (#75) - A RE-MEASUREMENT COVERS THE POPULATION OF THE FIRST MEASUREMENT. test_the_cheap_subset_is_actually_CHEAP prices the every-tick doctor roster and, when the total goes over budget, re-measures and keeps min(first, second) - correct reasoning, because a wall-clock figure moves 2.7x between runs of identical code and for a floor-bounded quantity the minimum is the honest estimator. The two passes measured DIFFERENT POPULATIONS: the first skips _skip = SLOW | PERIODIC (63 checks), the re-measure skipped SLOW only (65). MEASURED on his Mac 2026-09-18, one tick, unchanged code: first-pass population 4,134 ms, retry population 8,859 ms, the surcharge being engines corroborate 3,057 + sweep would find 1,667 = 4,725 ms that the every-tick path never pays. So min() ran over two different things and could only ever absolve a burst LARGER than 8,859 ms - while the block's own comment calls the retry 'what actually decides'. It decided nothing, and on 2026-09-18 it REFUSED A LEGITIMATE PUSH at 10,146 ms for a subset costing 4,134. The same defect sat in the 'measured almost nothing' denominator, counting 65 where 63 were timed. THIRD INSTANCE OF ONE SHAPE: v3313 a seed compared only to its own population, v3317 the heart dividing by the population it counted, now this - each time the numerator was right, the denominator was a different set, and the arithmetic ran anyway. IT ASKS THE COMPILER, NOT THE TEXT: every earlier cut of a law like this was a grep, and the docstring here names cd.SLOW four times, so a grep would read the explanation of the defect as the defect. ast cannot see a comment. AND IT PINS WHICH SET - a law asserting only that the two loops agree goes green when BOTH are narrowed back to cd.SLOW, which is the bug applied consistently, so _skip must still be built from SLOW and PERIODIC. The behavioural half refuses to pass if PERIODIC ever empties, because then the populations coincide and the law measures nothing - UNMEASURED, not clean. The four other cd.SLOW sites were swept and are NOT siblings: they count the EAGLE's rows, where include_slow=False genuinely means all-but-SLOW. 3 red-proofs.",
         ),
    Gate("test_seed_population", [sys.executable,
                          os.path.join(HERE, "test_a_seed_is_compared_only_to_its_own_population.py")], 60,
         why="v3313 (#26) - A SEED IS COMPARED ONLY TO A FIGURE THAT COUNTS THE SAME POPULATION. 'uniques seed' carried a permanent '+N behind the live figure' that no action could close, because the subtraction was chronFound - len(_GRAIL_SEED) and those count different things: the seed is a list of NAMES the boot floor would write, while chronFound is funiScan().found, a walk of the ROSTER asking _ownedHas of each row, which resolves a store name to its canonical form before matching. So the seed legitimately carries alias spellings with no row of their own (the six Latent-sunder forms are dropped by _uniItems; 'Harlequin Crest (Shako)' resolves onto the row spelled 'Harlequin Crest') and his store legitimately holds rows the seed never listed. A PERMANENTLY RED ROW IS NOT MERELY IGNORED, IT IS OBEYED: it read +63 behind, so 67 names were written into _GRAIL_SEED, and it then read -3 behind. MEASURED afterwards on his live board: seed 312 names, chronFound 309, and 0 of those 312 names absent from his store - there was never any missing work. THE FACT WAS ALREADY RECORDED AND TWO SITES NEVER ASKED: every ledger declares usesStoreLength and canonical_figure already refuses this exact comparison on that field ('NOT A COMPARISON, AND SAYING SO MATTERS'), while _stale() and the FROZEN row builder both subtracted anyway - one fact, three readers, two of them wrong. seed_drift() is now the single definition and both call it. THE REAL FINDING SURVIVES AND IS PINNED AS A BASELINE: sets and runewords ARE store lengths, so Dean's runewords still read drift -5 against a seed of 99, five seeded rows genuinely missing from his store. Also: the doctor stops counting an exempt figure among the current ones in all four of its return branches, and NAMES the exemption out loud so it can be audited instead of growing silently. 3 red-proofs.",
         ),
    Gate("test_shadow_fed_like_live", [sys.executable,
                                      os.path.join(HERE, "test_the_shadow_is_fed_what_live_is_fed.py")], 60,
         why="v3311 (#31) - TWO CORRECTIONS to the shadow gate, neither arming anything. SAFETY CHECKED FIRST: confluence() has exactly ONE caller (wilson_shadow) and the tier's own note says the weighting only reports, so nothing live grounds on these numbers. (1) WITNESS_TIER was written before three tags existed - hand v2462, cross-surface v2380, same-slot v2393 were all added to witnesses() afterwards and confluence() scores an unknown tag 0.0, so the LIVE gate counted his manual tick as a full witness while the SHADOW paid it NOTHING, against his own 2026-09-02 ruling 'manual anything is enough witness obivously'. A stale LAW, not a stale reading. Weights derived not picked: hand 1.00 because CONFLUENCE_FLOOR is 1.00 so 'enough witness on its own' has a number, and it keeps its OWN TAG because this file insists hand must never masquerade as cross-reel or printed - a reader asking WHY a name grounded must see 'he says so', which is about identity not magnitude; cross-surface 0.70 priced with cross-lane because his own description of the case is 'thats two witnesses'; same-slot 0.30 priced with cross-frame because slot_identity calls it A WITNESS NOT A NAME and it must never ground alone. (2) THE SHADOW WAS FED LESS THAN LIVE INSIDE ONE CALL: _gate_verdict_live got surface_of and wilson_shadow did not and had no such parameter, so a name grounded via cross-surface was invisible to the shadow and every resulting difference was filed as a POLICY disagreement when it was a difference in what each could SEE. MEASURED with the resolver as the only variable: without it tags ['cross-frame'] confluence 0.30 wouldPass False, with it ['cross-frame','cross-surface'] confluence 1.00 wouldPass True - the same evidence flips the verdict. A comparison whose sides are fed differently measures the feeding. Also pins the OTHER direction, that fixing a zero must not turn a witness into a name, and that the caller actually hands the resolver over rather than the parameter being decorative. ⚠ HIS RULING ON THE THIRD PIECE IS RECORDED IN THE LAW: the Wilson lock must NOT be wired to the prune - 'leave it off and surgically remove it we need pruning'. 4 red-proofs.",
         ),
    Gate("test_two_looks_two_rows", [sys.executable,
                                    os.path.join(HERE, "test_two_looks_are_two_rows.py")], 60,
         why="v3310 (#56) - his ruling is ask the second eye TWICE and keep both, and wire the disagreement to the heart. THIS LAW EXISTS BECAUSE I CLAIMED TO BE OBEYING IT AND WAS NOT: through the whole v3301-v3309 arc I reported 'asked twice, both looks agree' while pasting the second look INTO the first answer's text, so record_answer wrote ONE row carrying both. The ledger has no pairs from that arc, nothing can compute agreement from it, and no disagreement could ever reach the heart. MEASURED on 817 rows: 767 versions have a look, 21 have two or more REACHED looks carrying a verdict (2.7%), and v3303/v3307/v3308 - the ones I reported as agreeing pairs - read SINGLE. It also refuted a second claim of mine: I repeatedly cited v3297 as opposite verdicts 18s apart, and the store shows THREE looks at v3297 all findings, AGREE. I stopped quoting it; a claim the store cannot show is UNKNOWN, not evidence. FOUR PROPERTIES: three states never two (AGREE/DISAGREE/SINGLE plus NONE, because collapsing SINGLE into AGREE lets one look pass as a corroborated pair, which is exactly what I did in prose); an EMPTY SEAT is not an opinion (reached=False is excluded from both sides or two failed calls read as unanimous); the census CARRIES ITS OWN REACH and states its rate is an UPPER BOUND, since a second ROW is not always a second OPINION - re-files and corrections against one version read as DISAGREE - so an unqualified percentage from a 2.7% sample containing artifacts would be the confident number this repo keeps learning to distrust; and the check is named in MINE so a look I failed to take never inflates the count HE acts on, per his #35 rule. Every case drives a THROWAWAY ledger, never the real store. 3 red-proofs.",
         ),
    Gate("test_screen_parity", [sys.executable,
                               os.path.join(HERE, "test_the_screen_bills_the_same_rows_the_engine_does.py")], 60,
         why="v3309 - BOTH HALVES WERE VISIBLE IN HIS OWN SCREENSHOT. HALF 1: the PANEL was the FIFTH copy of the partition. His console at v3307 read '9 thing(s) are waiting on YOU ... the counter and this panel disagree (you 9 vs 11 shown) - a row was counted that this panel did not draw', and the arithmetic names it: 11 minus 9 is 2, the two BY_DESIGN rows. v3307 taught the ENGINE that a row ruled NOT-A-DEFECT stops billing him, v3308 taught the ROUTE, and the panel still bucketed by its own rule knowing only mineWhat. The v3284 disagreement warning is the SYSTEM WORKING - it caught this within minutes of the ship, and silencing it instead of closing the gap would have been the real failure. The rows MOVE to their own heading rather than vanishing, because a row that leaves his count with nothing showing where it went is silencing by another name, and the new bucket gets a gap check like the other three since a bucket nobody counts is the next place a row goes missing. HALF 2 (#35): NEVER was printed about a row asked TWO MINUTES EARLIER, directly above a sentence saying so - the panel mapped unmeasured to NEVER unconditionally because the payload gave it no way to tell genuinely-never from not-asked-this-tick. The engine now PERSISTS everAsked and lastState rather than leaving the screen to recover a fact the writer already had (heart-first rule 6), and the fallback stays NEVER when the field is absent because an older payload that cannot tell us must not be rounded down to the reassuring word. Order is pinned too: the by-design test must run BEFORE the youRows fallback or the rows reach his count regardless. 4 red-proofs.",
         ),
    Gate("test_one_partition", [sys.executable,
                               os.path.join(HERE, "test_one_partition_of_what_needs_him.py")], 60,
         why="v3308 - I DRIFTED THIS RULE MYSELF WITHIN AN HOUR OF SHIPPING IT. v3307 taught the watchdog's _EAGLE partition about BY_DESIGN so rows already ruled NOT-DEFECTS (#29 end routes reachable, #30 the river) stop billing him, per his #35 standing rule that WAITING ON YOU means action is needed FROM HIM RIGHT NOW. The /api/eagle ROUTE - the one his console actually reads - kept its OWN copy and knew only about MINE. MEASURED on his live console minutes after the ship: the engine partitioned to 7 and the route still answered needsYou=9 with byDesign absent entirely. Two surfaces, one question, a number he acts on. And the route's comment CLAIMED it was fine - 'the SAME rule as the _EAGLE partition, and the only one any surface may quote from here on' - true when written, false after my change, because nobody edits the comment when they change the other copy. Third instance of this shape in one arc: v3295 lane_read_tags (three copies of a lane's work list), v3301/REG-1115 (/api/relaunch's third busy list, drifted into deadlocking the button after a crash), now this. eagle_partition() is the one definition and both callers use it. TWO HALVES: structural - no module partitions doctor rows by hand, with the OWNER exempt because a law that bans its own subject everywhere flags the fix as the defect (the first cut reported 3 hits, all three inside the definition); and behavioural - a BY_DESIGN row is kept out of bad AND still shown, because vanishing is silencing by another name. Plus the direction of failure: an UNREADABLE roster BILLS rather than silences, since a roster nobody can load must never quietly shrink the number he acts on. 3 red-proofs.",
         ),
    Gate("test_failure_attribution", [sys.executable,
                                     os.path.join(HERE, "test_a_failure_is_charged_to_the_thread_that_caused_it.py")], 60,
         why="v3304 (#55) - _check_the_sweep_would_find_something measures its own density pass by snapshotting the stash gate's failure count before and after, and v3297 (mine) took that snapshot from gate_failures() - a PROCESS-WIDE counter - while the console gates frames on several threads at once. REPRODUCED, not argued: the doctor's window was opened, a separate thread broke exactly one gate inside it, and the delta came back 1 while the density pass had broken nothing. The check then answers UNKNOWN 'the stash gate FAILED 1 time(s) during the density pass', which is false - AND THE HARM IS NOT THE WRONG SENTENCE: returning UNKNOWN means the genuine MISSING ('N reels on disk and NONE shows a stash panel; a vault sweep would read nothing') is NEVER RAISED. A check suppresses the exact finding it exists to produce, and does so more often the busier the console is. The lesson was already carved THIRTY LINES AWAY in the same file - v2191 on the BLIND channel, 'THE BLIND STATE IS NOW A PER-CALL RECEIPT, NOT A PROCESS COUNTER', which Konyo called critical and asked for first - and the FAILURE channel was left as a process counter. Fix: _gate_broke also bumps a THREAD-LOCAL tally on _GATE_LAST (already a threading.local, right beside it) and gate_failures_here() is the attributable counterpart; gate_failures() keeps its process-wide meaning because a total is a legitimate thing to report. The defect was never the counter, it was using a total to ATTRIBUTE. Two of three cases are BEHAVIOURAL (drive a real thread). 2 red-proofs. NOTE its source check uses _executable_only(src, '.py') not '.js' - the .js branch strips // and /* */ and NOT Python #, so the first cut counted its own comment and read 3 instead of 2.",
         ),
    Gate("test_overtaken_open", [sys.executable,
                                 os.path.join(HERE, "test_an_overtaken_open_leaves_the_stage_alone.py")], 60,
         why="v3305 (#59) - his report, five times: the theatre fails to open, and it is ALWAYS THE REOPEN AFTER A CLOSE, never the first open. That pattern is the whole diagnosis. thOpen() sets TH.open=true BEFORE awaiting /api/sessions (v859 'pixels BEFORE network', bounded to 8s by v2228), so for those 8 seconds the toggle 'if (TH.open) { thClose(); return; }' means A SECOND CLICK CLOSES the half-opened stage - correct and desirable. What is not correct is that the still-pending thOpen() then resolves and UNCONDITIONALLY re-runs TH.open=true, theatre.hidden=false, classList.add('theatre-open') - re-showing a stage whose state thClose() already tore down. Open, closed, then re-opened empty. AND THE MIRROR, found reading thClose: the CATCH branch is equally unguarded, so an open that times out at 8s tears down a stage that belongs to a LATER open. MEASURED: grep for thOpening/TH.opening/_thBusy/inFlight/TH.loading returns ZERO matches - no re-entry guard existed anywhere in the file. The fix is a GENERATION counter, deliberately not a busy flag: a bare 'if (TH.opening) return' makes the second click do nothing at all, silently dropping the close the user asked for, which is a different wrong behaviour. thOpen claims a generation on entry, both post-wait exits stand down if it moved, and thClose bumps it BEFORE tearing down so a resolve racing between the two cannot win. 3 red-proofs.",
         ),
    Gate("test_new_film_buys_a_read", [sys.executable,
                                      os.path.join(HERE, "test_new_film_buys_a_read_not_a_smaller_reel.py")], 60,
         why="v3303 (#57) - _chron_reel_owes_a_read states its contract in its own docstring: re-owe the moment the reel GROWS, because new frames are new evidence and THAT IS THE ONLY THING that makes a re-read worth paying for. The code disagreed in two places at once: `if len(_ff) != _at: return True` where != includes SHRINKAGE, and `return _old < _at` which fires on a look-era frame being GONE, i.e. deletion. So a PURE PRUNE - frames deleted, nothing captured - bought a paid read of a reel now holding LESS film than when it was last read, which can only find less than the answer already recorded. That is his money re-confirming a smaller version of what the ledger already says. v3298 did not introduce this and did not fix it; it made the second branch explicitly deletion-triggered while correcting a different defect. THE FIX IS ONE RULE that subsumes both branches without weakening either: new film = (frames now) - (look-era frames still present), re-owe iff > 0. Truth table measured against every case the gates already pin - nothing-moved 0 new no (REG-1111 keeps its verdict), pure growth yes, PURE DELETION 0 new NO (the only row that changes), prune-3-capture-3 under a stable count 3 new yes (TestV2202 keeps its verdict), prune-3-capture-1 1 new yes. v3298's 5ms pad and both measured bounds are untouched. BEHAVIOURAL and builds its own temp reel, so it runs on a runner rather than needing his tv/frames/hist - the exact defect v3300 had to repair. 2 red-proofs"),
    Gate("test_relaunch_interlock", [sys.executable,
                                     os.path.join(HERE, "test_a_held_relaunch_gets_a_green_light.py")], 60,
         why="v3301 - Konyo's #38 ruling: 'make sure to safegaurd the sweep so it cant relaunch until it does happen then a green light switch turns it on to relaunch when needed'. The HOLD already existed on both doors; THE GREEN LIGHT DID NOT. _exec_relaunch_soon read 'ABANDON, do not queue', so a relaunch refused mid-sweep was DROPPED and nothing ever re-fired it - the console kept its old build until some independent decision came round, at least one escalation period later and possibly never. MEASURED 2026-09-18 from the GrokBot seat's own GB-L-LOOKED rows: 8 mandatory relaunches in a day, gaps 84/42/30/21/28/14/40 min against a 60-110 min chronicle sweep, so the conflict is the NORMAL path not a corner. Four properties, each failing differently: it FIRES by itself when the work ends; it is BOUNDED FROM THE FIRST ASK and a re-ask must NOT refresh the deadline (otherwise pressing the button on any timer shorter than the TTL makes a bounded hold unbounded - the no-expiry scar wearing a new coat); UNKNOWN NEVER FIRES (ok=None means nobody could read the world, and firing then relaunches into a sweep it merely failed to see); and ONE DEFINITION of in-flight. That last one found a live defect: /api/relaunch kept a THIRD copy of the busy list which had drifted into appending 'ON AIR' from _agent_mode ALONE with no _agent_alive() test, while nothing_in_flight fixed exactly that in v2161 ('a STALE MODE DEADLOCKS IT FOREVER') on the automatic door only - so after an agent CRASH the relaunch BUTTON refused forever, and it is the button you press to recover from a crash. Seven of the eleven cases are BEHAVIOURAL, calling the pure module rather than reading source, so the law runs on a GitHub runner instead of needing his Mac. Carries a corroborator (the REGISTER against THE WORLD) that catches a green light which has stopped being ticked. 5 red-proofs"),
    Gate("test_one_work_list", [sys.executable,
                                os.path.join(HERE, "test_a_lane_has_one_work_list.py")], 60,
         why="v3295 - the vault lane's work list (OWED_BY intersect READ_CLEARS) was written out by hand in THREE places and the copies drifted: control_app's autoread candidates and its awaiting-a-sweep count were both correct since v2878, while river_walk's PRINTER probe still counted the single tag vault-owes. So the river printed 'the lane's queue is EMPTY ... this reel waits for a seal nothing will write' while the lane held 3 panels-never-banked reels - an instrument and the thing it measures disagreeing about what the lane is FOR, with the instrument believed because it is the one that renders. The THIRD copy was found by the grep that wrote the law, not by the investigation, which is why the structural half bans walking OWED_BY at all rather than checking the two known callers. Pins both halves: no production module iterates the map (all call shelf_driver.lane_read_tags), and the set still holds panels-never-banked while still refusing rows-not-banked per v2878 (owed a BANK, not a READ - queuing it spends his money and clears nothing). 2 red-proofs"),
    Gate("test_auto_lanes_no_switch", [sys.executable,
                                       os.path.join(HERE, "test_the_auto_lanes_have_no_switch.py")], 60,
         why="v3285 - Konyo, 2026-09-18, on the Sessions strip: 'these should be toggled on by default no option to it'. v1975 built four REAL switches and its doctrine (OFF IS A REAL REFUSAL) was right WHILE OFF WAS REACHABLE. Pins the inverted law: the reader never consults d2r_autoLanes, so a stale {runes:false} from an old click cannot darken a lane silently; and the pill carries no onclick, role=switch, tabindex or knob, because a control that cannot move invites a click that does nothing. 3 red-proofs"),
    Gate("test_world_ribbon", [sys.executable,
                               os.path.join(HERE, "test_the_world_ribbon_can_be_put_away.py")], 60,
         why="REG-1082 - Grok Bot filed 'Trap: persistent LINUX toast' from his native seat: "
             "#cousin-ribbon is fixed at top:0 z-index:2000, appended once on every non-Mac "
             "machine and removed by NOTHING. It is the twin of the banner Konyo reported the "
             "same day on the Mac. It now COLLAPSES rather than hides, because five CSS rules "
             "reserve room for it and removing the element would leave all five holding empty "
             "space. These laws pin: the badge is wired and toggles, the choice survives a "
             "reload, the BAND keeps pointer-events:none so it can never eat the console click "
             "v2061 measured it overlapping, collapsing sheds WIDTH ONLY so every clamp stays "
             "valid, the world sentence is unchanged, and the glyph plus title keep the fact "
             "reachable. 6 red-proofs, placement measured at 1440/901/375"),
    Gate("test_his_window", [sys.executable,
                             os.path.join(HERE, "test_his_window_is_his_on_every_platform.py")], 60,
         why="REG-1081 - he reported across three machines that the console cannot be minimised "
             "or windowed on Windows or on GrokBot's Linux: it opens fullscreen, which he likes, "
             "and fullscreen takes the titlebar with it everywhere except macOS, which keeps its "
             "own controls. The escape hatch was TV_WINDOWED, readable only BEFORE launch, which "
             "is no use from inside a running window - and this was the SECOND report, v3179 "
             "having recorded the first. These laws pin the behaviour end to end: every action "
             "reaches the pywebview method that performs it, no window / no method / a raising "
             "call each answer with their own reason, a bad action name is named as such even "
             "where there is no window, the route reaches the helper, both controls exist and "
             "POST to it, they stay HIDDEN until the console confirms it has a window, and "
             "FULLSCREEN REMAINS THE DEFAULT he asked for. 7 red-proofs"),
    Gate("test_no_footage_tracked", [sys.executable,
                                     os.path.join(HERE, "test_no_reel_footage_is_ever_tracked.py")], 60,
         why="REG-1066 - v3258 committed a 97.84MB tarball holding HIS JOURNAL and two of HIS "
             "REELS to this PUBLIC repo, through a git add -A, ~2MB from GitHub's hard limit. "
             "Writing the gate then measured 552 files / 101.7MB of his footage ALREADY tracked, "
             "which predates the session and is his call to undo. So: no archives, no tracked "
             "file over 25MB, the ignore rules proven live, and a RATCHET on the existing "
             "footage so the exposure cannot grow. 4 red-proofs"),
    Gate("test_name_rarity_colour", [sys.executable,
                                     os.path.join(HERE, "test_a_name_takes_its_colour_from_its_rarity.py")], 60,
         why="REG-1060 - four console surfaces painted an item name from the find TIER, and tier "
             "'grail' is assigned from _kai_fullnames() - 3,212 names scraped out of bible.html "
             "with SET PIECES INCLUDED. So a set piece read UNIQUE GOLD, identical to a unique. "
             "The palettes were innocent (every --rar-* equals its --q-* to the byte) and so was "
             "the classifier (135/135 sets, 397/398 uniques, measured through CDP). Pins the "
             "JOINT: a line that paints a quality class onto an interpolated .name must ask "
             "_nameRarCls. Static, comment-free, 4 red-proofs"),
    Gate("test_dock_says_why", [sys.executable,
                                os.path.join(HERE, "test_the_dock_says_why_it_is_still_full.py")], 60,
         why="REG-1055 — the dock showed a count and an Auto-Sort button; he pressed it, nothing "
             "moved, and nothing said why. All 46 unsorted carry ONE suggestion, __throwout, and "
             "Auto-Sort will not discard for him. Both halves right, the screen said neither. "
             "Runs the SHIPPED block in node against a stubbed sorter"),
    Gate("test_population_why", [sys.executable,
                                 os.path.join(HERE, "test_a_count_cannot_answer_why.py")], 60,
         why="REG-1054 — he asked three times why the vault holds 200+ and got a COUNT each time. "
             "vault_population decomposes it: 222 owned = 172 non-set-pieces + 50 that ALSO sit "
             "in d2r_setPieces, and 49 filed nowhere is what fills the dock. 172 is exactly his "
             "pre-wipe owned. Read-only, pinned by a law"),
    Gate("test_proof_chip", [sys.executable,
                             os.path.join(HERE, "test_the_proof_chip_says_nothing_when_nobody_answered.py")], 60,
         why="REG-1052 — the vault now MARKS how many of a locker's items the ledger can prove, "
             "and bible.html is also the PUBLIC site where no console exists. A chip reading 0 "
             "there would be a claim about his vault manufactured from a failed fetch. Pins "
             "absent-not-zero, a bounded ask, the matching denominator, and that it never filters"),
    Gate("test_admission_bar", [sys.executable,
                                os.path.join(HERE, "test_the_admission_bar_knows_what_it_would_admit.py")], 60,
         why="REG-1051 — #105's bar was measured as '14 earn it' and never told to the lockers, "
             "which render d2r_owned (222). And the 14 turn out to be potions, charms and the "
             "Horadric Cube — so enforcing the bar literally would empty his vault of every real "
             "keeper. The count sounded like progress; the NAMES were the finding"),
    Gate("test_live_store_skip", [sys.executable,
                                  os.path.join(HERE, "test_a_live_store_skip_is_counted.py")], 60,
         why="REG-1050 — eleven gates read stores that exist only on his Mac (chron_evidence.json "
             "2.2MB untracked, the vault accumulator, 73 ledger backups outside the repo), so they "
             "were RED on origin and GREEN here and neither was about the code. The helper skips "
             "with a MARK and this counts the population, because a silent skip is the same "
             "defect as a green that lies"),
    Gate("test_countless_proof", [sys.executable,
                                  os.path.join(HERE, "test_a_countless_proof_can_still_tamper.py")], 60,
         why="REG-1048 — a proof with no declared match count reached str.replace as its count, "
             "and None is a TypeError, so all 32 count-less proofs would have raised AT the "
             "tampering step. One field, three readers, each needing to be told separately"),
    Gate("test_blind_organ", [sys.executable,
                              os.path.join(HERE, "test_a_blind_organ_says_so.py")], 60,
         why="REG-1034 — heart_map._read returned '' so an unreadable control_ui.html would have "
             "BANKED a HEART.md claiming the console paints 0 surfaces; shelf_corroborate "
             "returned [] for both 'no sessions' and 'could not ask'. The swallow ratchet had "
             "been red on these for 10+ CI runs and nobody read it"),
    Gate("test_both_terms", [sys.executable,
                             os.path.join(HERE, "test_a_difference_needs_both_its_terms.py")], 60,
         why="REG-1032 — vault_autosort guarded the BEFORE read against an unreadable store and "
             "left the AFTER read on the old path, so a failed read reported assignedAfter 0 and "
             "newlyAssigned -173. Parses the JS with ast + node --check rather than grepping it"),
    Gate("test_eye_attribution", [sys.executable,
                                  os.path.join(HERE, "test_a_look_names_the_family_that_looked.py")], 60,
         why="REG-1029 — two genuine Grok reviews (6 and 12 findings) landed as family=None "
             "because this CLI prints no model header, so the push gate kept saying the versions "
             "OWED A LOOK that had just been looked at. Attribution now comes from WHICH BINARY "
             "RAN, which is evidence; the gate pins that it may never read EYE_MODEL, which is "
             "the v3214 defect of deriving a field correctly from a guess"),
    Gate("test_no_pinned_footage", [sys.executable,
                                    os.path.join(HERE, "test_a_gate_may_not_pin_his_footage.py")], 90,
         why="REG-1027 — a reel id in EXECUTABLE test code makes retention hold that footage "
             "forever as a fixture. My own two gates froze 43 MB that way; v2071 froze 3.15 GB "
             "and v2393 found 4.8 GB held on the strength of reel ids in PROSE. A ratchet over "
             "the 39 already-named ids, so a new one is deliberate and never an accident"),
    Gate("test_seal_named", [sys.executable,
                             os.path.join(HERE, "test_a_named_reel_does_not_defeat_its_seal.py")], 60,
         why="REG-1023 — naming a reel put it back past its own valid seal, so the autoread "
             "watchdog re-read a finished reel every tick: 3,052 re-sweeps of one reel and 104% "
             "CPU for 2h46m, almost all of it 0 paid reads so nothing alarmed. Pins the DECISION "
             "(a pure function), not the spelling of the line that held it"),
    Gate("test_read_not_waiting", [sys.executable,
                                   os.path.join(HERE, "test_a_read_reel_is_not_waiting_on_a_read.py")], 60,
         why="REG-1026 — a read that finds nothing never clears the tag, so reels already sealed "
             "by the CURRENT reader were reported forever as waiting on a sweep. He asked about "
             "this twice. Pins the split (waiting / barren / banked) and that BOTH sentences "
             "carry the already-read clause"),
    Gate("js-syntax",   [sys.executable, os.path.join(HERE, "js_syntax_gate.py")], 300,
         why="every surface must PARSE — a bad edit blanks a 37k-line page"),
    Gate("comment-count", [sys.executable, os.path.join(HERE, "comment_count_gate.py")], 60,
         why="a count in a comment is a number nobody re-measures — five drifted in one day"),
    Gate("visual-lock", [sys.executable, os.path.join(REPO, "visual_lock_invariant.py")], 120,
         why="the locked type system may not drift"),
    Gate("test_control", [sys.executable, os.path.join(HERE, "test_control.py")], 900,
         why="the console + storage routing + gate invariants"),
    Gate("test_agent",   [sys.executable, os.path.join(HERE, "test_agent.py")], 900,
         why="the agent, its argv seam and its budget circuit-breaker"),
    Gate("test_routes",  [sys.executable, os.path.join(HERE, "test_routes.py")], 300,
         why="KAI routing, labels and the super-analyze selector"),
    Gate("test_tz_art", [sys.executable, os.path.join(HERE, "test_tz_art.py")], 120,
         why="the Terror Zone panel's facts: 67 zones -> game-extracted art + the game's own "
             "density/level, and the tiering that decides which zones get greyed out"),
    Gate("test_tz_relay", [sys.executable, os.path.join(HERE, "test_tz_relay.py")], 60,
         why="the console TZ relay must treat a history-only payload as live, not as "
             "unreachable, and /d2r/api/tz must stay as open as /api/tz"),
    Gate("test_bake_seed", [sys.executable, os.path.join(HERE, "test_bake_seed.py")], 90,
         why="v1947 — the seed baker rebuilds his shipped grail/set seed from his real board. The "
             "seed is his HISTORY, so the guards are the four REFUSALS: report-only unless "
             "--write, never shrink, never seed a piece the game lists as missing, never seed a "
             "name a boot one-shot owns"),
    # v2228 — the corroborator proves its own relations can both hold and refuse. An
    # invariant nobody has seen disagree is the green that lies, so this runs every push.
    # v2228 — ⚠ `why` IS A KEYWORD (name, argv, timeout, needs_app, cwd, why, skip_ok). My first
    # cut passed it as the 4th POSITIONAL, so it landed in `needs_app` and the gate registered with
    # an empty why — which test_every_gate_says_what_it_protects caught immediately, exactly as it
    # exists to. A gate nobody can triage is the one people start ignoring.
    # v2231 (#58) — the synthetic reels must keep fingerprinting distinctly, or the vault
    # scenarios silently prove a weaker rule: vault_retro dedupes by signature, so two identical
    # frames are ONE witness. This is the property the whole fixture rests on.
    Gate("vault-fixture-reels", [sys.executable, os.path.join(HERE, "vault_fixture_reels.py")], 60,
         why="v2231 — the vault suite runs on ~140 KB of synthetic footage instead of 123 MB of his "
             "reels, after the prune deleted two of them and sent nine cases to a permanent skip. "
             "If the generated frames stop being distinct, the scenarios keep passing while "
             "proving less than they claim."),
    Gate("corroborate-selftest", [sys.executable, os.path.join(HERE, "corroborate.py"),
                                  "--selftest"], 60,
         why="v2228 — the cross-engine invariants must be able to REFUSE. Every serious defect on "
             "2026-08-28 was a pair of numbers each correct alone and wrong together (19 vs 2, "
             "1263 vs 403, 157 vs 7, 36 vs 30), invisible to all 21 single-engine checks. If this "
             "self-test stops going red on demand, the corroborator would report agreement whatever "
             "the engines actually said."),
    Gate("test_every_lock_declares_its_attacks",
         [sys.executable, os.path.join(HERE, "test_every_lock_declares_its_attacks.py")], 120,
         why="TWELVE OF SIXTEEN LOCKS COULD NOT SAY HOW MANY DISTINCT ATTACKS BACKED THEM — "
             "including prune.arm, the one door with no undo, and vault.sweep_start, which spends "
             "his money. REG-598: Wilson cannot tell 83 independent looks from ONE attack applied "
             "83 times, and `attacks` is the field that stops it. It was NOT a wiring gap — every "
             "harness already passes attacks=; the stored rows predated the re-run. Re-running "
             "them made the real picture visible: prune.arm 0.9259 raw but 0.5655 by attack "
             "against a 0.839 bar; vault.apply 0.9259 vs 0.4385; vault.sweep_start 0.8064 vs "
             "0.3424. ⚠ Which figure the bars read is HIS open ruling and this guard must never "
             "settle it — it only makes both numbers available on every lock."),
    Gate("test_dead_field_reads_jsonl",
         [sys.executable, os.path.join(HERE, "test_dead_field_reads_jsonl.py")], 120,
         why="THE DETECTOR BUILT FOR THIS CLASS NEVER LOOKED HERE, AND COULD NOT HAVE READ IT IF "
             "IT HAD. `histBytes` was null in 8,588 of 8,588 rows of his disk series while every "
             "sibling was populated — the exact shape dead_field.py exists for — and it reported "
             "ZERO rows, because WATCHED held one store. Adding the store alone would NOT have "
             "worked: `_rows_of` parsed every store with json.loads over the whole file, so a "
             "JSONL store comes back UNKNOWN — it could have sat in the registry, appeared "
             "covered, and said nothing. Reader taught the format and store added together. "
             "Driven on his real series it answers DEAD_FIELDS before the v2654 fix and OK after "
             "one filled row, so it self-clears rather than nagging about history."),
    Gate("test_hist_bytes_is_not_dead",
         [sys.executable, os.path.join(HERE, "test_hist_bytes_is_not_dead.py")], 120,
         why="A FIELD THAT NEVER ONCE CARRIED A VALUE, AND IT WAS THE DENOMINATOR OF HIS OWN "
             "QUESTION. Measured on his live series: histBytes null in 8,588 of 8,588 rows while "
             "reels, eligibleMb and freeGb beside it are populated on all 8,588 — REG-598's "
             "startedTs shape. It is the CORPUS, and `credible_pruned_mb` refuses a freed figure "
             "larger than it, so with hist_bytes null that bound had never once been applicable: "
             "the whole cold-read hardening of v2648 sat behind a None the only caller passed as "
             "a literal. The value was in the same dict all along — the call site already derives "
             "`reels` and `eligibleMb` from the retention plan, whose per-reel mb sum to 5,463 MB "
             "on his shelf, and the field is filled from the first row after the fix. "
             "\u26a0\u26a0 BUT THE BOUND IS STILL UNREACHABLE IN PRODUCTION, and an earlier "
             "version of this sentence overstated that: `credible_pruned_mb` RETURNS AT ITS "
             "FIRST BRANCH for every production call, because `pruned_mb is None` is checked "
             "before `hist_bytes` is ever read, and the only call site passes a literal None. "
             "So this fixed a dead FIELD; it did not make the corpus bound run. It becomes "
             "reachable the day a real freed figure exists, and not before. "
             "⚠ `pruned_mb` stays a deliberate None: the prune is OFF, nobody measured a freed "
             "figure, and 0 would claim a measurement nobody took."),
    Gate("test_disk_attribution_twins",
         [sys.executable, os.path.join(HERE, "test_disk_attribution_twins.py")], 120,
         why="ONE RULE IMPLEMENTED TWICE, AND THE LAW LANDED IN ONE COPY. The footer he reads "
             "attributed the 24h disk change with `_dt.prunedMbInWindow ? ...MB ours : none of "
             "it us` — and `0` is FALSY in JavaScript, so null (nobody measured) and 0 (measured, "
             "freed nothing) rendered the same affirmative sentence. LIVE: every row of his disk "
             "history since 2026-09-02 carries prunedMb null, so the footer has been asserting "
             "'none of it us' about an unmeasured quantity for three days. `disk_delta_say` on "
             "the server has had all three branches all along. The two are joined here: both are "
             "driven across null / 0 / negative / positive and must agree in KIND, and the js is "
             "LIFTED from control_ui.html rather than re-typed, because a copy would pass while "
             "the shipped renderer drifted."),
    Gate("test_render_gate_sees_the_page",
         [sys.executable, os.path.join(HERE, "test_render_gate_sees_the_page.py")], 120,
         why="GATE-EYE — THE RENDER GATE REPORTED CLEAN ON A PAGE WITH VISIBLE CLIPPING. All "
             "eleven render targets were NAMED SUBTREES: `console` is `#btn-mini, #btn-miniauto`, "
             "so its `painted 1/1 - clipped 0` measured ONE BUTTON and was never a claim about "
             "the page. A cold second-eye read of the 375px shot found panels stacked with text "
             "cut off, a bar rendering 'appea / here' and 'Failed to fetch' sliced mid-word — all "
             "confirmed by eye, all outside every selector, all invisible by construction. A "
             "`page` target now measures the document, REUSING _PROBE so the scroller exclusion, "
             "title recovery, inert check and fixed-position escape all still apply. This guard "
             "holds the capability and the two settle faults found building it: copying "
             "`settles:False` from `console` measured a half-built page, and the settle then "
             "could never succeed because it demanded a `.tab[data-tab]` row that "
             "control_ui.html does not have."),
    Gate("test_scope_reach_signal",
         [sys.executable, os.path.join(HERE, "test_scope_reach_signal.py")], 180,
         why="CF-13's READING AID IS DYING AND `actionable: 0` WOULD NEVER HAVE SAID SO. A row is "
             "`narrow` when its reach is <= 10, and the narrow-and-unpermitted rows are called "
             "the readable signal. But reach is a three-deep walk over control_app's OWN call "
             "graph, so it tracks this module's growth, not the lanes: the same four lanes "
             "measured 6/23/34/71 on 2026-09-01, 6/24/34/72 on 2026-09-02 and 7/25/35/74 today. "
             "`tvd-ledger-backup` is the only row that has ever been narrow and it went 6 to 7 in "
             "four days, three short of the threshold. When it crosses, `actionable` stays 0 "
             "while its meaning silently changes from 'nothing needs you' to 'this instrument can "
             "no longer tell the rows apart'. The threshold is NOT tuned — that is the parameter "
             "tweak auto_scope's author refused; the DEATH is published instead as "
             "signal LIVE/DEAD/UNKNOWN with the headroom to the nearest row."),
    Gate("test_reg600_axes_can_refuse",
         [sys.executable, os.path.join(HERE, "test_reg600_axes_can_refuse.py")], 180,
         why="REG-600 — TWO SABOTAGES THAT AIMED AT SOMETHING THAT COULD NOT REFUSE. "
             "`prune.reports` banked 24/24 by handing `disk_history_append(pruned_mb=None)` and "
             "asserting the row came back None, against a writer that was a PURE PASSTHROUGH with "
             "no validation anywhere in it — correct behaviour on a legal input, recorded as a "
             "guard refusing. `reel.route` had two such axes of seven: one compared two module "
             "constants eight times, one graded an observation and never called the caller its "
             "own comment said must refuse. This drives the real refusal path at the WRITE end "
             "(`credible_pruned_mb`), and runs the REG-593 control in BOTH directions — a "
             "validator hardwired open must collapse the axes to 0, one hardwired shut must fail "
             "the baseline and bank nothing. It also holds the route fix the replacement axis "
             "found on its first run: `_station_of(None)` returns UNKNOWN by design and its only "
             "caller crashed before it could."),
    Gate("test_mask_encoders_agree",
         [sys.executable, os.path.join(HERE, "test_mask_encoders_agree.py")], 120,
         why="B-84's surviving half — THE TESTED ENCODER IS NOT THE USED ENCODER. Two "
             "implementations turn 'which of this roster do I own' into a base64url bit mask: "
             "`fleet_mask.encode` (round-trip tested against `fleet_mask.decode`, and AST-measured "
             "with ZERO production callers) and an INLINE JS SNIPPET built as a string inside "
             "`control_app.board_mask` and run via `_ejs` — the one that produces every mask that "
             "has ever gone on the wire. The suite proved a pair that never runs together in "
             "production while the code that does run had no test at all. This runs the SHIPPED "
             "snippet (lifted by AST from board_mask, never re-typed) against a synthetic store "
             "and compares byte-for-byte. RED-proven: flipping the js to MSB-first bit packing "
             "reports 'THE TWO ENCODERS DISAGREE'. ⚠ Three instrument faults were caught building "
             "it, each of which would have made it lie: a regex over source returned raw escapes "
             "('g is not defined'); `about:blank` is an opaque origin with no localStorage; and a "
             "shared storage key let one case read the PREVIOUS case's write and report it as a "
             "real disagreement — decoding both masks is what exposed that, the bare inequality "
             "looked like a defect. ⚠ It touches nothing of his: a throwaway server on a scratch "
             "port, never :17772, never his board's storage."),
    Gate("test_printer_reach_facts",
         [sys.executable, os.path.join(HERE, "test_printer_reach_facts.py")], 60,
         why="A 70-CHARACTER WINDOW MANUFACTURED A FINDING AND THE MODULE PUBLISHED IT. "
             "`printer_reach` keyed its refusal tally on `str(cwhy)[:70]`. The refusal names EVERY "
             "missing contract fact in one sentence, and 70 chars lands part-way through the FIRST "
             "fact's explanation — so every distinct refusal collapsed into one bucket whose text "
             "ended inside the word `name`, and the module's own docstring then stated as a "
             "measurement: 'ALL 22 fail on the SAME single fact: name'. MEASURED UNTRUNCATED "
             "2026-09-05: name, location AND provenance are missing on ALL 30 seals. ⚠ The "
             "correction is not pedantry — one missing fact is a reader change, while `location` "
             "missing is a CAPTURE question (0 of 1,065 deep rows carry a cell) and therefore HIS "
             "ruling, so a finding naming the wrong blocker sends the next person to the wrong "
             "file. Same shape as [[source-window-shortcut]]: a fixed slice of something whose "
             "length you did not check does not shorten the answer, it produces a different one. "
             "⚠⚠ THESE GUARDS GRADE BEHAVIOUR, NOT TEXT — my first cut asserted `'[:70]' not in "
             "source` and FAILED on the comment DESCRIBING the defect; the second asserted the "
             "false claim was ABSENT and failed because the correction QUOTES it in order to "
             "retract it. Third prose-grading guard in two versions. RED-proven: restoring the "
             "truncation drops the longest blocked key to 70 and the behavioural check fails."),
    Gate("test_board_tally_alarm",
         [sys.executable, os.path.join(HERE, "test_board_tally_alarm.py")], 90,
         why="CF-5 — A FALSE ALARM THAT BLINDED A REAL WATCHDOG FOR 7.8 DAYS. MEASURED on his live "
             "board_tally.json: ownerId 77f641… , and `contested` carried 77f641…|main 293/121 "
             "FRESH against c5c2c9…|main 280/120 SEVEN POINT EIGHT DAYS stale. 293>280 AND 121>120 "
             "— strictly greater in BOTH lanes, which is what ONE monotonic adds-only counter "
             "sampled twice must look like: the same board across an install-id re-mint, not two "
             "worlds. The predicate never consulted `doc['ownerId']` (resolved 34 lines upstream) "
             "and had no staleness term. ⚠⚠ THE COST WAS NOT THE WRONG SENTENCE — console_doctor "
             "did `if doc.get('contested'): return MISSING` BEFORE its high-water/drop check, so "
             "the detector for 'his published progress is BELOW its own high-water mark' was "
             "UNREACHABLE. A warning that returns before a detector switches that detector off. "
             "⚠⚠⚠ UN-BLINDING IT MADE A LATENT DEFECT REACHABLE THE SAME DAY: `recent = drops[-1]` "
             "took the last row in the file, which is a TEST FIXTURE in his live store "
             "(route real-1|main, runewords 42->0, at:null) — 1 of his 4 drop rows is actually "
             "his. Fixing a blindness obliges you to check what the newly-sighted code says. "
             "⚠ NOTHING IS PRUNED: the fixture row stays, it is simply no longer read as his. "
             "RED-proven: restoring the two doctor defects fails 3 of 11."),
    Gate("test_paint_ink",
         [sys.executable, os.path.join(HERE, "test_paint_ink.py")], 60,
         why="THE BLANK TEST THAT COULD NEVER FIRE ON HIS CONSOLE. `verdict()` declared BLANK only "
             "when one colour covered >= 98%% of the window. MEASURED through that same instrument "
             "on his window in BOTH states plus a known-painted reference: blank modalShare 0.124 / "
             "p99 33 / bright 0.41%%; healthy 0.069 / 177 / 3.94%%; Terminal 0.628 / 254 / 5.81%%. "
             "⚠ READ THE MODAL COLUMN — the PAINTED window scores 0.628 and his blank one 0.124, so "
             "his blank window is FURTHER from the bar than a healthy one. A text window has a "
             "dominant background; this console's is a dark GRADIENT that never collapses to one "
             "colour. The 0.98 rule was not a high bar here, it was STRUCTURALLY UNREACHABLE. "
             "p99 and brightShare separate the states with no overlap and BOTH must agree before "
             "BLANK fires, with the bars in the empty middle of a 5x gap. ⚠ Rejected alternatives, "
             "each refuted by measurement: `distinct <= 4` (a healthy console swings 156->34) and "
             "mean luminance (healthy 11.3/23.9/20.8 vs a black window at 12.2 — overlapping)."),
    Gate("test_freed_is_measured",
         [sys.executable, os.path.join(HERE, "test_freed_is_measured.py")], 60,
         why="154's REAL SUBJECT, and it was worse than the row said. (1) "
             "`reel_retention.apply_plan` returned `freedMb: p.get('freeMb', 0)` — the PLAN'S HOPE "
             "— in the same dict literal as its own `removed` and `failed` lists, never consulting "
             "either. REPRODUCED against a plan whose candidate did not exist so every rmtree "
             "raised: ok=False removed=[] failed=1 freedMb=512.0, and control_app.py:16348 (which "
             "copies it with NO read of r['ok']) would have printed 'freed 512 MB by removing 0 "
             "reel(s)' — megabytes from the plan, count from the measurement. (2) A BOOLEAN "
             "counted as MEGABYTES: bool subclasses int, so isinstance(True,(int,float)) passes "
             "and sum([True,True]) is 2 — two flags produced '2 MB of that was our pruning'. "
             "⚠ math.isfinite does NOT cover it (isfinite(True) is True). RED-proven: restoring "
             "both originals fails 8 of 11. ⚠ Fixtures assert the tombstone path resolves INSIDE "
             "the fixture before calling, because _tombstone_path falls back to his live store and "
             "the tombstone is written BEFORE the first removal."),
    Gate("vault_apply_crossfamily",
         [sys.executable, os.path.join(HERE, "vault_apply_crossfamily.py")], 90,
         why="A2·HARD — THE FIRST HARDENED LOCK, and the third kind is genuinely independent. "
             "`vault.apply` guards the door that WRITES HIS LEDGER and carried only sabotage+live "
             "(confluence 1.70 against a 2.50 bar). `vault_apply` was handed COLD to a different "
             "model family, which returned three attacks; TWO LANDED on a real hole — the re-gate "
             "loop iterated `owned` ONLY, so an uncorroborated row under `unsure` reached the write "
             "path without the gate ever being asked (`owned: None` was the same hole in another "
             "shape). MEASURED: the gate refused an uncorroborated `owned` row and did NOT refuse "
             "the identical row under `unsure`. ⚠ NOTHING WAS EXPOSED — the board registers only "
             "`owned`, so it was stopped one station later; fixed anyway because this function's "
             "own v1595 note says 'a rule enforced in one place is a rule with a door beside it'. "
             "⚠⚠ TWO ANTI-REG-600 SAFEGUARDS: `_refused()` counts ONLY the gate's own sentence, "
             "never 'the board window is not open' (banking that would record the absence of a "
             "window as evidence about the gate); and it REFUSES TO BANK unless the baseline holds "
             "— 4/4 corroborated rows must still be ACCEPTED, or the refusals prove a jammed door "
             "rather than a working one. Safe by construction: every attempt carries evidence that "
             "cannot clear the gate, so the only outcome the door can produce is a refusal."),
    Gate("test_corroborate_operands",
         [sys.executable, os.path.join(HERE, "test_corroborate_operands.py")], 60,
         why="TWO CROSS-ENGINE INVARIANTS WERE READING A KEY NOBODY RETURNS. Both took their left "
             "operand as `len(plan.get('free') or plan.get('freeable') or [])`, and "
             "`frame_authority.plan_frames()` returns NEITHER — its keys are bytes/haveIndex/"
             "heldBy/kept/prunable/say/scanned/sealOk/sealedSessions/witnessFrames/witnessOk. So "
             "the left side answered 0 forever, on every tree, whatever the deleter did. An "
             "invariant whose operand is a constant cannot be violated, and BOTH of these guard "
             "the direction with no undo: 'the one thing that can delete never frees more than "
             "the planner offers'. ⚠ corroborate.py's own v2393 note already listed both by name "
             "under 'agreeing at ZERO vs ZERO (cannot tell healthy from inert)' — the suspicion "
             "was right and the cause was a key name. ⚠⚠ THIS DOES NOT MAKE THEM INFORMATIVE: "
             "`prunable` is genuinely empty on his shelf, so they still read 0 vs 0. It makes "
             "them CAPABLE — structurally-inert became quiet-but-live. RED-proven: restoring the "
             "old expression fails 4 of 9, including 'deleter frees 9 while the planner offers 2 "
             "still reads as agreement'."),
    Gate("test_store_isolation", [sys.executable, os.path.join(HERE, "test_store_isolation.py")], 60,
         why="v1965 — a non-owner browser gets its own world (I·<id8>· keys) so a guest's grail "
             "never lands in his. That set was right for every store that existed when it was "
             "written and was never extended: SEVEN grail-ish stores write BARE on a guest world, "
             "including d2r_chronicleInboxLog, the Routing Ledger. Changing the namespacing "
             "orphans guest data and is his call; this gate only refuses an EIGHTH"),
    Gate("test_gate_cache", [sys.executable, os.path.join(HERE, "test_gate_cache.py")], 60,
         why="v1941 — the Vault Accumulator quote memoises a crop+OCR verdict per frame (7.4 "
             "minutes of his evening before it did). The speed is not the risk: a stale 'stash' "
             "on a rewritten frame would send the sweep to read a gameplay screen as a stash "
             "page, and vault_retro calls that misroute permanent. Keyed on size+mtime so it "
             "MISSES rather than lying"),
    Gate("test_shard_balance", [sys.executable, os.path.join(HERE, "test_shard_balance.py")], 30,
         why="Routine I must peel the every-item simulations into the slow project so "
             "--shard cannot dump them all into one 45-minute file-count bucket"),
    Gate("test_chronicle_traffic", [sys.executable, os.path.join(HERE, "test_chronicle_traffic.py")], 180,
         why="v1888 — the whole grail (398 uniques + 135 set pieces) through proposal -> gate -> "
             "merge, order-independence across twelve reels, and the ambiguous fold his own roster "
             "contains: 'stormspie' sits between Stormspire and Stormspike at 0.947 each and must "
             "come back None"),
    Gate("test_vault_traffic", [sys.executable, os.path.join(HERE, "test_vault_traffic.py")], 180,
         why="v1884 — EVERY item through sweep() end to end, and 500 at once. The 21 tests in "
             "test_vault_retro drive gate() and merge_vault() directly and not one of them calls "
             "sweep(), so the routing INSIDE it — surface to lane per item, throw flags per key, "
             "the two bars on real piles — had never been executed at any size"),
    Gate("test_inventory_lattice", [sys.executable, os.path.join(HERE, "test_inventory_lattice.py")], 180,
         why="v1925 — the inventory lattice AND its refusals. A column of checkboxes in the game-creation lobby is periodic, so a lattice fitter finds a lattice in it and answers \"18 occupied, 9 free\" about a menu; every case here is a real frame from his own reel, so a loosened refusal fails here instead of on his screen"),
    Gate("test_fleet_mask", [sys.executable, os.path.join(HERE, "test_fleet_mask.py")], 120,
         why="v2213 — THE FLEET cross-reference turns two ledgers into 'what should I chase', and "
             "it does that by shipping BITS over a shared roster. The dangerous failure is not a "
             "crash: decode a mask against a roster it was not built for and every bit lands on a "
             "neighbouring item, so the box confidently names real pieces that are simply the wrong "
             "ones and he goes farming things his cousin already has. These pin the fingerprint "
             "refusals, and the three-language chain — the encoder runs in the BOARD (JS), the "
             "validator in the WORKER (JS) and the decoder here (Python), each of which can be "
             "individually correct while the chain is wrong"),
    # v2455/v2456 — A21c. The chronicle routes and the fleet lanes, judged by ONE corroborator.
    # ⚠ `why` IS A KEYWORD HERE. Passing it 4th positional lands it in `needs_app` and registers a
    # gate that requires a running console; that mistake produced two defects from one line on
    # 2026-09-02 and the table was swept by AST afterwards. [[the-unjoined-end]]
    # v2457 — the paint witness. `why` IS A KEYWORD (name, argv, timeout, needs_app, cwd, why).
    # v2457 — GROK'S. He wrote roster_routes.py and its guard, reverted his own Gate() row
    # because run_gates.py was mine and dirty while he worked, and asked me to register it when I
    # landed the batch. That is the protocol working: whoever holds the file adds the line.
    Gate("test_mask_why", [sys.executable, os.path.join(HERE, "test_mask_why.py")], 120,
         why="no machine on the fleet has ever published a uniques mask, and every None from "
             "board_mask looked the same on the wire. This holds that a missing mask names "
             "WHICH link gave up, and that a failure dict is never what `if m:` would keep."),
    # v2460 — the two ends of the mask wire. `why` IS A KEYWORD.
    # v2461 — the type floor, at the TOKEN level. `why` IS A KEYWORD.
    # v2462 — A21b, his hand as a witness. `why` IS A KEYWORD.
    # A21d — his rule over the item classifier. Needs headless Chrome; skips (never passes)
    # without it. `why` IS A KEYWORD.
    # v2464 — A2 · the gate must bank what it scores. `why` IS A KEYWORD.
    # A2 step 1 — "the printer and the reels". Runs the harness as a SCRIPT so it banks, the way
    # the hover-wilson gate now does. `why` IS A KEYWORD.
    # A2 — the WRITE door. `why` IS A KEYWORD.
    Gate("vault-wilson", [sys.executable, os.path.join(HERE, "vault_wilson.py")], 180,
         why="vault.apply mules items between characters — it writes his ledger — and no sabotage "
             "had ever been attempted against it. This hands it proposals it MUST reject, each row "
             "carrying an EMPTY evidence list so it fails the witness gate by construction, and "
             "counts whether v1595's re-gate refused. ⚠ It never applies anything: every rejection "
             "happens before the board is asked. Proven RED: removing the re-gate takes that claim "
             "to 8/0 LEAKS while the empty-proposal claim stays PROVEN. It also REPORTS, rather "
             "than papers over, that vault.forget has no refusal path at all and therefore cannot "
             "be proven by sabotage."),
    Gate("test_a_sweep_with_no_readable_lane_does_not_start",
         [sys.executable, os.path.join(HERE, "test_a_sweep_with_no_readable_lane_does_not_start.py")], 90,
         why="v3406 (#152) - AN ATTACK THE LOCK ANSWERED IS NOT AN ATTACK ON THE DOOR. "
             "chronicle_sweep_start asks self_arming.may('vault.sweep_start') BEFORE it reads the "
             "lane list, and that lock FAILS CLOSED on a stale heart census - its state for the "
             "whole of any session that has touched a gate file. So every sweep_wilson attack "
             "aimed at a guard BELOW the lock got a perfectly good ok:False and _refused_unstarted "
             "called it caught. MEASURED 2026-09-22 in a sandbox: reverting the door's own lane "
             "guard left sweep_wilson GREEN at exit 0 with lanesnone, lanesraise, lanesstr and "
             "lanesdict all still PROVEN - the revert was real, its anchor matched exactly once, "
             "the attack never arrived. Four claims scored a guard they could not see and banked "
             "attacks=1 each into the very lock that was answering them. Two halves: the harness "
             "now returns UNREACHED as a third state that lands in NEITHER number (0 of 0 is "
             "UNPROVEN, never 0 of 2 which reads LEAKS and accuses working code) and banks "
             "nothing; and this gate does what the harness cannot safely do - stubs the lock OPEN "
             "and threading.Thread shut, so the lane states are driven at the REAL door for the "
             "first time. It found two more: the WORD claude inside a STRING passed `in`, and so "
             "did a DICT with that key. The BASELINE case asserts the door WOULD have started on "
             "a real lane - without it a door jammed permanently shut passes every refusal. "
             "4 red-proofs."),
    Gate("sweep-wilson", [sys.executable, os.path.join(HERE, "sweep_wilson.py")], 180,
         why="vault.sweep_start guards an action that SPENDS MONEY and no sabotage had ever been "
             "attempted against it, so it sat UNPROVEN at n=0 with nothing to move it. This "
             "attempts the two states the door must refuse — a sweep already running, which would "
             "double-spend, and no lane to read with, which would spend and learn nothing — and "
             "counts whether it refused. ⚠ It never STARTS a sweep: there is no attempt in it "
             "whose success path runs. Proven RED: removing the busy guard takes that claim to "
             "8/0 LEAKS while the lane claim stays PROVEN."),
    Gate("test_tasks_ships_are_recorded",
         [sys.executable, os.path.join(HERE, "test_tasks_ships_are_recorded.py")], 120,
         why="a version that moved the four stamps but appears nowhere in TASKS.md — the list "
             "silently ceasing to describe what the repo did"),
    Gate("test_cold_caches_invalidate",
         [sys.executable, os.path.join(HERE, "test_cold_caches_invalidate.py")], 300,
         why="two disk caches now answer for a FRESH process (/api/heart cold 19.5s -> 5.5s), and a "
             "cache that answers from a key it did not verify is stale-reading with a speedup "
             "attached. Both decide deletion-adjacent facts: which reels the TEST SUITE names (a "
             "fixture reel is HELD from pruning) and which chronicle routes exist. Asserts a wrong "
             "key is refused, a corrupt cache fails OPEN, and nothing is written without a key"),
    Gate("test_unseed_is_reversible",
         [sys.executable, os.path.join(HERE, "test_unseed_is_reversible.py")], 120,
         why="window._d2rUnseed DELETES entries out of a person's chronicle and had NO test at "
             "all, while the previous version of the same control shipped completely inert (an "
             "apostrophe in \"Gloom's Trap\" terminated its onclick attribute). A code review "
             "then found four ways it did not do what its dialog said: the promised backup was "
             "written once and READ NOWHERE, so the undo did not exist; the ledger name was "
             "written LAST, so any throw left a stripped-and-unnamed store that re-seeds; and "
             "d2r_rwVerify and d2r_owned were backed up and never stripped. Worst on HIS OWN "
             "board, where naming the ledger switches the floors off permanently. Proven RED "
             "against the bytes that actually shipped as v2697 -- 7 of 8 laws, each failing on "
             "its own assertion rather than on one shared setUp error"),
    Gate("test_deep_owed_is_stamped",
         [sys.executable, os.path.join(HERE, "test_deep_owed_is_stamped.py")], 120,
         why="14 of his 40 reels have DEEP 0, and an absent deep row meant TWO things nothing could "
             "tell apart: never dispatched, or dispatched and thrown away by the _POOL_STOPPING "
             "guard. The owing is now stamped BEFORE the network call, so a lost read still leaves "
             "a trace. ⚠ It pins that every name the stamp uses is IN SCOPE — the first cut used "
             "`fid_this`, which has zero bindings in _vision_job, and inside its own try/except "
             "that NameError would have been swallowed and recorded nothing forever."),

    Gate("test_board_short_read_is_seen",
         [sys.executable, os.path.join(HERE, "test_board_short_read_is_seen.py")], 120,
         why="REG-681 fixed the torn WRITE; this closes the SERVE side. An empty read does not "
             "raise, so bible.html was served as a normal 200 with Content-Length 0 — and the only "
             "instruments that could report a blank page (ui_faults, uiBeat.panels) need the "
             "page's own JS, which a zero-byte document does not have. Detected server-side now, "
             "reported to the channel the Doctor already reads, and it still SERVES rather than "
             "refusing — a transient torn read must not become an outage."),

    Gate("test_chronicle_rebuild",
         [sys.executable, os.path.join(HERE, "test_chronicle_rebuild.py")], 120,
         why="v2732 — his 'snap shot is not enough'. A rebuild derives a chronicle from the OTHER "
             "ledgers, so drift and corruption are repaired rather than replayed. This pins the "
             "three things that almost went wrong: it must NOT reproduce the tally (the first cut "
             "aimed at d2r_owned 169 while his screen read 292/403, and reproducing 292 landed on "
             "298 — a second implementation of the number he reads most, six wrong before "
             "shipping); it must NAME what it cannot reach rather than count it; and it must "
             "REPORT a date conflict rather than resolve it away. Its purity is asserted by an "
             "IMPORT ALLOWLIST plus attribute- and bare-name call checks, after a substring "
             "version was defeated by `import json as _j` and then by `open()`."),

    Gate("test_frames_respect_evidence_holds",
         [sys.executable, os.path.join(HERE, "test_frames_respect_evidence_holds.py")], 120,
         why="v2740 — the frame deleter offered 7 frames out of a reel held so it could be RE-READ. "
             "All 805 offered frames sat inside reels reel_retention holds; 798 were test fixtures "
             "(POLICY) and 7 were a zero-pages reel (EVIDENCE), held because 'the engine reopens "
             "these when the prompt improves'. frame_authority held witness FRAMES, reel_retention "
             "held whole REELS, and neither consulted the other. Pins that the refusal lives in "
             "plan_frames (not frame_verdict, whose callers cannot supply the hold list), that an "
             "unreadable hold list makes NOTHING prunable — the same answer the seal refusal gives "
             "to the same ignorance, and the direction that cost two fixture reels at v2229 — and "
             "that POLICY holds stay uncovered, because he asked for the evidence frames."),

    Gate("test_orphans_say_whose_they_are",
         [sys.executable, os.path.join(HERE, "test_orphans_say_whose_they_are.py")], 120,
         why="v2744 — the stray-process row claimed 'nothing of OURS is busy and old' while "
             "my_orphans had NO ownership test at all: ppid was parsed and never read, and the "
             "only filter was 30 hardcoded substrings that flagged coreaudiod, ControlCenter and "
             "PID 1 (eight earlier false positives of the same kind are recorded in "
             ".console_scars.json.corrupt). Wrong in BOTH directions — it also silently exempted "
             "anything whose argv merely contained 'bird' or 'Terminal'. ⚠ NOT fixed by swapping "
             "to a positive rule: the real 52-minute runaway on 2026-09-06 was in no spawn ledger, "
             "named no tree path and held no port, so all three positive witnesses failed and only "
             "the exclusion rule caught it. Pins the THIRD state — OURS -> WARN, UNATTRIBUTED -> "
             "UNKNOWN (not the rail's failure state), still REPORTED, never dismissed."),

    Gate("test_a_leak_is_this_runs_not_his_consoles",
         [sys.executable, os.path.join(HERE, "test_a_leak_is_this_runs_not_his_consoles.py")], 60,
         why="#31 (2026-09-26) - the end-of-run orphan check printed THIS RUN LEFT 1 PROCESS RUNNING about his "
             ":17772 console's OCR worker: new since the run began and naming this tree, but spawned by a console "
             "that was running before the run. A leak of a run can only descend from the run (a gate is waited for, "
             "so its leftovers re-parent to launchd). Pins leaked_by_this_run(): the parent chain reaching a "
             "PRE-EXISTING process makes it THEIRS (named with its owner, never counted); reaching run_gates or "
             "ppid 1 makes it a leak - a real one stays counted."),

    Gate("test_a_prune_records_what_it_freed",
         [sys.executable, os.path.join(HERE, "test_a_prune_records_what_it_freed.py")], 120,
         why="v2743 — 8,790 disk-history rows and NOT ONE has ever carried a freed figure (8,270 "
             "zeros, 520 nulls, 0 nonzero). The row blamed 'nothing passes until a prune runs'; "
             "false — the only write fires ~85 lines ABOVE apply_plan with pruned_mb hardcoded to "
             "None, so a prune running changed nothing. Nor was it blocked on prune.arm: that lock "
             "governs whether a prune may ACT, not what the writer may carry. Pins that the freed "
             "figure reaches the history, that the pre-prune row still honestly says None, and — "
             "the non-obvious trap — that the second write REUSES the pre-prune corpus, because "
             "credible_pruned_mb refuses a figure larger than the corpus and re-measuring after "
             "deletion makes every legitimate prune look impossible. ⚠ Includes an AST "
             "REACHABILITY law added after sabotage proved the text-matching ones vacuous: "
             "`if False:` left every matched string in place and passed 7/7 over a write that "
             "could never run."),

    Gate("test_a_seal_is_per_session",
         [sys.executable, os.path.join(HERE, "test_a_seal_is_per_session.py")], 120,
         why="v2743 — a sweep stamped ONE pass-wide row count onto every session it read, and it "
             "ALREADY FIRED: six seals written in the same second on 2026-08-24 each carry rows=7 "
             "while two of those sessions witnessed NOTHING. The claimed 42 is 7 counted six "
             "times — and that phantom figure propagated into frame_authority.py:252, "
             "run_gates.py:789 and test_seal_verdict.py:22 as the repo's own diagnosis. Attribution "
             "existed all along (every witness dict carries `session`) and was thrown away. Pins "
             "that attribution comes from the WITNESSES and not an even split, that the pass total "
             "survives under its own name, and — run against the real deciders — that a session "
             "witnessing nothing now scores EMPTY and is HELD while a genuine contributor still "
             "releases. Proven RED on 3 sabotages."),

    Gate("test_the_art_resolver_folds_the_apostrophe",
         [sys.executable, os.path.join(HERE, "test_the_art_resolver_folds_the_apostrophe.py")], 180,
         why="FOUR GRAIL ITEMS HAD NO PICTURE BECAUSE ONE FILE SPELLS THEM TWO WAYS. "
             "unique_roster.json holds Atma's Scarab, Saracen's Chance, Seraph's Hymn and The "
             "Cat's Eye with a CURLY apostrophe (U+2019) while bible.html spells the same four "
             "STRAIGHT in ITEM_VALUE and D2IO_ART — same item, two spellings, one file — and "
             "artUrl matched exactly, so all four missed art that EXISTS under the other "
             "spelling. The page's own prose already named them. Folded in the RESOLVER, not the "
             "roster: unique_roster.json and set_roster.json SHARE one sourceHash, and changing "
             "those bytes invalidates every machine's fleet mask until it republishes — a picture "
             "is not worth making the fleet undecodable. It is a lookup FALLBACK, never a "
             "rewrite, so no caller starts seeing a spelling it did not ask for. ⚠⚠ THE ALIAS I "
             "ALMOST SHIPPED: the task note said The Scourge's art was 'keyed as the bare "
             "Scourge (hd_flail.png)' and I wrote a one-off for it. MEASURED against the real "
             "table first — NEITHER 'Scourge' NOR 'The Scourge' is an art key at all; the strings "
             "that look like keys are a BASE CODE ('Scourge':'7fl') and a DESCRIPTION. The alias "
             "pointed at nothing. Flail -> base_flail.png does exist, so a base-type fallback was "
             "available and is REFUSED: _itemArtPath's own rule is 'no art -> NO PICTURE, not a "
             "placeholder, not a fallback glyph, not a guess'. ⚠ AND THE GUARD ITSELF SKIPPED "
             "3 OF 7 ON ITS FIRST RUN — the extracted region ends with `window.D2IO_ART = "
             "D2IO_ART;` and node has no `window`, so the probe exited 1 and three laws reported "
             "nothing while looking like they ran. A skip is not a pass. 7 laws, 2 sabotages RED."),

    Gate("test_the_stash_watcher_only_seals_a_lane",
         [sys.executable, os.path.join(HERE, "test_the_stash_watcher_only_seals_a_lane.py")], 120,
         why="A GUARD THAT COULD NEVER BE FALSE WAS ENDING HIS RECORDINGS AFTER 25 SECONDS. His "
             "report: \"i click ON AIR and it just closes me out every time... same for DEAN, "
             "something unified is wrong.\" mini_state() returns `focus: m.get(focus) or "
             "MINI_FOCUS` and _MINI is INITIALISED with that default at import, so `focus` is "
             "never empty; `_current_declared_focus()` re-reads the same field, making "
             "`focus or _current_declared_focus()` ONE VALUE READ TWICE. _stash_watch_loop — whose "
             "docstring says it seals a LANE-DECLARED reel — was armed for EVERY capture. He plays "
             "rather than standing in his stash, so stash_screen_open() returns None on every poll "
             "and 25s later stop_agent() sealed his session. The ~40s was never a timer: one 5s "
             "poll + the 25s grace + startup. Measured before: alive=False at t+42s. After: alive "
             "at t+80s, watcher silent, no shutdown requested. ⚠ Safe to narrow ONLY because every "
             "mini also starts _mini_watchdog, which seals on its deadline independently — a law "
             "here pins that.",
         ),
    Gate("test_no_control_is_buried_in_another_control",
         [sys.executable, os.path.join(HERE, "test_no_control_is_buried_in_another_control.py")], 180,
         why="A CONTROL INSIDE ANOTHER CONTROL ANNOUNCES ITSELF AS NEITHER. Two role=button spans "
             "lived inside <button id=btn-chronicle-inbox>, and the measured price was the parent's "
             "ACCESSIBLE NAME swallowing both chip labels: name=\"📜 Inbox 0 open Chronicle Sweep "
             "🗑 clear all\" before, \"📜 Inbox 0\" after. A screen-reader user heard ONE control "
             "offering three actions with no way to tell which one Enter would run. ⚠⚠ AND THIS "
             "FILE REFUTES THE TASK THAT PRODUCED IT: the brief said both chips were "
             "keyboard-unreachable and their onkeydown handlers were dead code. That measurement "
             "was taken while `body[data-state=off]` had the whole live bay collapsed to "
             "display:none — and THE INBOX BUTTON ITSELF measured focusable:false in the same run, "
             "which was the tell. On air, on the shipped markup, all three were focusable and Tab "
             "and Enter both worked. A `false` needs a denominator exactly as a zero does. The "
             "nesting still had to go — his console runs WKWebView, not Chrome, and nothing here "
             "was measured against it.",
         ),
    Gate("test_a_banked_proposal_says_it_is_banked",
         [sys.executable, os.path.join(HERE, "test_a_banked_proposal_says_it_is_banked.py")], 120,
         why="#226 section 1a. The vault register button offered `register N` from a proposal that "
             "may have been graded in a process that no longer exists. The AGE was painted - into "
             "a caption a few lines above, correctly saying 'restored from disk' - while the COUNT "
             "sat on the button, so the console told the truth in one element and offered the "
             "action in another. Re-grading in JS would be a second copy of the witness rules, so "
             "the fix reports staleness rather than recomputing a verdict; the law also refuses "
             "any witness constant appearing in the panel. resultFromDisk counts as stale ON ITS "
             "OWN: a disk proposal can read four minutes old and describe a dead process."),
    Gate("test_a_broken_gate_is_reported_every_run",
         [sys.executable, os.path.join(HERE, "test_a_broken_gate_is_reported_every_run.py")], 120,
         why="#100 wire 1 of 6. gate_failures() promised in its own docstring that the count is "
             "kept so a status surface can report it, and no surface ever did: the only human "
             "channel was a ONE-SHOT print at the first break, so every breakage after the first "
             "was invisible for the lifetime of the process. ⚠ THE OBVIOUS JOIN IS THE WRONG JOIN, "
             "which is why this pins a DELTA: _GATE_BROKE is a module global and the console runs "
             "sweeps on other threads that move it, so it may only ever be a RUN-level fact, "
             "never a per-frame one - its own comment records readers getting that wrong. And it "
             "may not be the lifetime value either: the sibling report beside it carries the scar "
             "in its own words, a run-level claim built on a lifetime counter is the same defect "
             "this whole arc keeps finding. It also pins that a THROW is not a VERDICT - those "
             "frames were not judged, and a gate that threw is not a gate that said no."),
    Gate("test_the_fleet_names_what_each_side_lacks",
         [sys.executable, os.path.join(HERE, "test_the_fleet_names_what_each_side_lacks.py")], 120,
         why="He reported the Dean drill as bugged - it showed neither what Dean lacks that he "
             "has, nor what they both need. Two different things were tangled: the COMPARE ENGINE "
             "and the PUBLISH path. The engine was never the defect; the panel was on its "
             "one-sided branch because Dean's console published a COUNT and no mask (no board "
             "window), the same headless state his own machine was in that afternoon. A refusal "
             "drawn correctly looks exactly like a broken column, so this pins the engine on HIS "
             "REAL ROSTER rather than trusting a screenshot to tell them apart - and the roster "
             "form is load-bearing, because names carry suffixes and a compare fed bare names "
             "matches nothing while every count still looks plausible. neitherHas may be None and "
             "that is not a failure: the content is asserted only when a list was returned, never "
             "turning a refusal into a confident zero."),
    Gate("test_a_written_answer_has_a_reader",
         [sys.executable, os.path.join(HERE, "test_a_written_answer_has_a_reader.py")], 120,
         why="The last two of #100's six JOIN wires, both of which had exactly ONE reference in "
             "the tree - their own test. _chron_lane_detail exists so a refusal can say whether a "
             "lane is OFF or ABSENT (its docstring: you switched it off and there is no Grok CLI "
             "here are different facts and only one of them is a problem) while BOTH sweep doors "
             "refused with a flat the primary Claude lane is unavailable - the sentence that sends "
             "him reinstalling something he had deliberately switched off. Measured the moment it "
             "was joined on this machine: grok present=false why=you switched it off. story_of "
             "exists so an unknown state returns its own name rather than quietly joining PENDING, "
             "which is exactly how a retired item comes back to life - while the ONLY place states "
             "are resolved indexed _SEC directly and raised KeyError. Callers are counted by "
             "PARSING, not grepping, because several of these functions are NAMED in comments "
             "explaining why they exist and a comment is not a caller."),
    Gate("test_the_session_gets_a_vote_on_where",
         [sys.executable, os.path.join(HERE, "test_the_session_gets_a_vote_on_where.py")], 120,
         why="retro_gate.corroborate_location has answered what location the SESSION agrees on "
             "since it was written and nothing ever called it - one of the verdict-shaped "
             "functions with no caller. _kai_compile_register is where the defect it exists for "
             "is MINTED: loc is stamped earliest-sighting-wins with no cross-check, and it reaches "
             "rendered rows downstream. v3212 wired it and the wire was INERT: it passed "
             "sess_rows, and corroborate_location reads a location off each entry via _loc_of "
             "(loc/where/container/location) while session rows carry those only one level down in "
             "names_loc - so every call answered 'no read in this session said where it was'. "
             "Connected, shipped, dead. This pins the MECHANISM: the call exists, it is NOT handed "
             "sess_rows, and the per-read list is built from names_loc. It also pins the "
             "function's own ruling that a split session is worth a second look and never an "
             "automatic correction, so locAgrees FLAGS and never overwrites loc, and a row that "
             "claimed no location gets None rather than False - nobody said and they disagreed are "
             "different facts. Its fixture names real items (shako, vampire gaze, stone of jordan) "
             "and asserts they exist, because sorting _kai_fullnames picks parse artefacts that "
             "_register_is_junk does not catch and the law would pass over garbage."),
    Gate("test_a_restore_is_shaped_like_a_sweep",
         [sys.executable, os.path.join(HERE, "test_a_restore_is_shaped_like_a_sweep.py")], 120,
         why="ledger_restore.proposal_from built wouldAdd as a DICT keyed by name while "
             "bible.html's chronicleApply calls .forEach on it, so every restore that ever "
             "reached the board died with 'is not a function' and wrote NOTHING. Measured on his "
             "live board 2026-09-16 restoring 85 uniques + 50 sets after an install-id change: "
             "the call REACHED bible.html - the TypeError quotes bible.html's own comment back - "
             "and every count was unchanged. With the shape corrected the same proposal moved "
             "foundLog 363 to 445, setPieces 83 to 133, chronFound 280 to 309. Nothing caught it "
             "for hundreds of versions because plan() is read-only and its counts were always "
             "right; the only wrong half was the one crossing into the board, which nothing on "
             "the Python side could see. Pins the PROMISE proposal_from's own docstring makes - "
             "the same vocabulary a sweep uses - not a number."),
    Gate("test_a_hop_shadows_the_window",
         [sys.executable, os.path.join(HERE, "test_a_hop_shadows_the_window.py")], 120,
         why="v3209 joined the write door to the board with `window = _cw`, and window is not an "
             "assignable binding - in sloppy mode that write is DISCARDED with no error. The hop "
             "reported success, changed nothing, and every line after it went on asking the "
             "console shell. Measured: his console ran v3211, which CONTAINS v3209, and "
             "chronicle_apply still answered 'this page has no LSR' - the exact refusal v3209 "
             "existed to end - while his ledger sat visibly wrong on screen. The READ door never "
             "made this mistake: it keeps a LOCAL _ctx and passes it as a PARAMETER NAMED window, "
             "shadowing the global. A gate that grepped for tvd-eng or _cw was green across the "
             "whole defect because both strings were present and the mechanism was dead, so this "
             "pins the MECHANISM on the four named context-hopping doors and reads the JS by "
             "PARSING the string literals rather than slicing source around a guess."),
    Gate("test_a_dead_journal_reader_says_so",
         [sys.executable, os.path.join(HERE, "test_a_dead_journal_reader_says_so.py")], 120,
         why="_kai_journal_rows wrapped its whole read in except Exception pass and returned an "
             "empty list, so an unreadable or permission-denied journal was indistinguishable "
             "from a quiet night. Six call sites read it and status_payload turns an empty tail "
             "into sessionHealth verdict idle: a dead reader wearing a healthy verdict. ⚠ THE "
             "GUARD FOR EXACTLY THIS WAS ALREADY WRITTEN, CORRECT AND UNREACHABLE - the except "
             "block whose own comment says a thrown journal walk is NOT an idle night - and its "
             "test mocked the function with side_effect RuntimeError, proving a path production "
             "can never take. Green forever over a live defect. This guards the path real disks "
             "take, and keeps the opposite error out: a journal that was never written is empty "
             "and honest, because reporting UNKNOWN there would make every fresh install look "
             "broken."),
    Gate("test_the_eye_is_shown_valid_code",
         [sys.executable, os.path.join(HERE, "test_the_eye_is_shown_valid_code.py")], 120,
         why="the ship gate will not push until a DIFFERENT model family has looked, so the "
             "PAYLOAD BUILDER is part of the gate - and it was corrupting its own input. "
             "MEASURED: Grok returned a FATAL finding on v3201, that a block of prose sat in the "
             "JavaScript with no opening slash-star and the source could not parse. It was "
             "reading its input correctly; the FILE parses in a real JS engine. _strip_comments "
             "tested each added line independently, and this repo writes block comments as a "
             "title line followed by indented prose with NO leading asterisk - so the opener "
             "matched and was dropped and every continuation line was kept. The eye was handed "
             "orphaned prose inside executable code, a syntax error the transport invented. That "
             "is every multi-line block comment in this repo on every look it has ever done, "
             "INCLUDING the ones it called clean. Proven both ways on one commit and one "
             "reviewer: corrupted payload gave a fatal finding, clean payload gave no defects "
             "found."),
    Gate("test_a_clean_look_is_filed_as_clean",
         [sys.executable, os.path.join(HERE, "test_a_clean_look_is_filed_as_clean.py")], 120,
         why="the ship gate refuses to push until a DIFFERENT model family has looked at the "
             "version, and it reads that fact out of .second_eye.jsonl. So the classifier turning "
             "a reviewer's prose into clean|findings is the instrument the gate trusts, and it "
             "had never been tested. MEASURED 2026-09-16 on a real look at v3189: Grok opened "
             "with 'No concrete defects found' and the row was filed findings=4, the first "
             "finding being the sentence saying there are none. Probing found it wrong BOTH ways "
             "- and the dangerous one was that a declaration plus exactly ONE listed P1 was "
             "filed CLEAN, because the v2808 guard was len(findings) > 1 and one is not greater "
             "than one. Its docstring asserted the three-defect case and nobody ever measured "
             "the one-defect case. Also: an adjective (no CONCRETE defects) defeated the "
             "pattern, and a sentence listing what the reviewer did NOT find was read as four "
             "findings."),
    Gate("test_a_look_keeps_its_evidence",
         [sys.executable, os.path.join(HERE, "test_a_look_keeps_its_evidence.py")], 120,
         why="v3386 (#129) - THE ROW KEPT THE VERDICT AND THREW AWAY THE EVIDENCE. MEASURED on "
             "the live ledger: 898 rows, 876 with an answer, median head 400 chars and max 600 - "
             "the cap - with the text past it stored NOWHERE, so a re-judge was impossible BY "
             "CONSTRUCTION and five proposed parser changes could only ever be argued about. The "
             "caller already hands the whole answer over (v3339 moved the cut here), so nothing "
             "new is fetched; what was missing was keeping it. This pins that a long answer is "
             "stored whole, that answerChars is the TRUE length so no stored field can claim to "
             "be complete when it is not, that the head is unchanged, and that all 898 older "
             "rows read UNKNOWN rather than handing a prefix to a re-judge."),
    Gate("test_a_failed_read_never_reaches_a_zero_claim",
         [sys.executable, os.path.join(HERE, "test_a_failed_read_never_reaches_a_zero_claim.py")], 120,
         why="v3395 (#139) - A FAILED READ MUST NEVER REACH A SENTENCE CLAIMING A MEASURED ZERO. "
             "The WIN-1 seat ran the queue drain on his Windows box; the reader thread died with "
             "UnicodeDecodeError (cp1255, byte 0x9f) and the tool printed 0 new ... nothing new, "
             "That is a measured zero, not a failure to look. It was exactly a failure to look, "
             "and a reassurance on the failure path is worse than silence. TWO defects: the gh "
             "call decoded with the LOCALE CODE PAGE while the same file passes utf-8 at three "
             "other sites, and - the class - a dead reader hands back EMPTY stdout with returncode "
             "0, which the code turned into a confident []. gh prints [] for an empty result, so "
             "silence from a SUCCESSFUL call means the read FAILED and now raises. ⚠ A write may "
             "still print nothing, so that lane stays open. ⚠ This law grades CODE not PROSE: the "
             "comment explaining the fix contains the banned string and a raw count returns 1 "
             "where the code-only count returns 0."),
    Gate("test_the_eye_is_asked_for_the_verdict_it_is_read_for",
         [sys.executable, os.path.join(HERE, "test_the_eye_is_asked_for_the_verdict_it_is_read_for.py")], 120,
         why="v3394 (#129) - THE EYE IS ASKED FOR THE VERDICT FIELD THE PARSER READS. v3376 built "
             "_stated_verdict so a DECLARED verdict line would be read first and prose would never "
             "be matched, and its comment claims the review prompt contains that line - it did "
             "not. COLD_FRAMING never asked for it, so the reader had no writer. MEASURED on 906 "
             "ledger rows: 35 from v2805 to v3391 DECLARE the change clean in prose and are filed "
             "as findings, so agreement, the eagle rows and the heart are wrong on all 35. The "
             "prose fix was REFUSED by this file own ruling - #76 measured that widening the prose "
             "matcher cannot be made safe - so the fix is to ask for the field. ⚠ The options and "
             "the field must not share a line: _stated_verdict ignores any line naming two or more "
             "verdict words as a MENU, and this law caught that trap on its first run, in the very "
             "instruction written to avoid it."),
    Gate("test_a_never_recorded_machine_is_not_a_broken_one",
         [sys.executable, os.path.join(HERE, "test_a_never_recorded_machine_is_not_a_broken_one.py")], 120,
         why="v3393 (#138) - A MACHINE THAT HAS NEVER RECORDED IS NOT A BROKEN MACHINE. His Windows "
             "ALT box had never filmed (capture doors 0, No runs recorded yet) and its console "
             "answered cannot read ...frames hist WinError 3, drew a 0x0 shelf and could not draw "
             "the river - so an ORDINARY EMPTY STATE WAS DRESSED AS A FAILURE and he went hunting a "
             "sync defect that does not exist. tv_diablo creates the tree inside _film_loop, so the "
             "path is absent BY DESIGN until something films. Fixed at the SOURCE in "
             "reel_retention.plan, which end_routes._safety forwards, so every consumer inherits "
             "it. The distinction is the ERRNO, never the text of someone elses error, a genuine "
             "failure still says cannot read, and NO PATH enters the new message because a Windows "
             "profile can carry a non-ASCII character that crashes a cp1255 console mid-report."),
    Gate("test_a_machine_establishes_its_own_tree",
         [sys.executable, os.path.join(HERE, "test_a_machine_establishes_its_own_tree.py")], 120,
         why="v3393 (#138) - A MACHINE ESTABLISHES ITS OWN TREE, AND NEVER GUESSES WHERE. His "
             "Windows ALT box showed tv\\frames and tv\\frames\\hist MISSING while "
             "d2r_ledger_backups existed and was WRITTEN that day: the machine provisions fine, "
             "but the FRAME writers establish nothing (control_app 15 scattered makedirs, "
             "frame_authority 0, reel_retention 0). His ruling was to fix any machine establishing "
             "its own tree so Dean's PC is fixed BY PULLING. A third eye ranked the worst outcome "
             "first: a tree built in the WRONG place turns the heart green and makes the fault "
             "invisible. So every root declares its own anchor, a refused anchor yields NO path, "
             "found requires a PROVEN WRITE, a frozen build refuses the repo anchor, and no path "
             "reaches a message unsanitised. This gate checks the CONTRACT, never this machine - "
             "a fresh machine is a legitimate state and the heart asks that question."),
    Gate("test_the_compare_columns_ask_one_question",
         [sys.executable, os.path.join(HERE, "test_the_compare_columns_ask_one_question.py")], 120,
         why="v3392 (#137) - THE CROSS-REFERENCE PANEL ASKS THE SAME THREE QUESTIONS FOR EVERY "
             "USER. He photographed his Windows ALT console reading YOU STILL NEED 86 and said it "
             "cant be logical. v3176 replaced column 1 with his OWN missing list whenever the peer "
             "cannot publish names, so ONE COLUMN HEADER ANSWERED TWO DIFFERENT QUESTIONS "
             "depending on a condition invisible from the screen. His ruling: same unified logic "
             "for every user - they have you do not, you have they do not, you both need. A column "
             "whose names are unknown is REFUSED with its reason, never swapped for an easier "
             "question. This law pins all three labels as invariant across BOTH arms of the "
             "ternary, and pins v3022's rule that neitherHas must not be coalesced."),
    Gate("test_the_census_population_is_safe_to_name_by_file",
         [sys.executable, os.path.join(HERE, "test_the_census_population_is_safe_to_name_by_file.py")], 60,
         why="v3433 (#177) - THE FILENAME RULE IS SAFE ONLY WHILE NO PRODUCTION MODULE IS NAMED LIKE A TEST. v3427 made lane_census skip test_*.py because a test FIXTURE defining def wait had flipped the live thread target target=wp.wait from FOREIGN to UNKNOWN. The second eye said, correctly, that classifying by FILENAME is the wrong axis. I was about to replace it with an import-graph rule and MEASURED FIRST: 705 local modules, 110 reachable from the production roots, 199 kept by the filename rule, NONE reachable-but-excluded, and ZERO of 33 census targets would change their answer. The graph rule changes nothing today and adds a failure mode the filename rule does not have - sensitivity to which roots you pick, with conftest landing inside the graph purely because run_gates imports it. So the rule stays and the UNEXAMINED ASSUMPTION becomes a pinned invariant: this fails the moment a production-reachable module is named like a test, which is the only moment the rule would start lying. Also pins that the roots exist (a reachability law over a missing root walks nothing and passes forever), that the v3427 fixture is still excluded, and that wait is still FOREIGN on this tree. 2 red-proofs."),
    Gate("test_the_code_running_is_the_code_on_disk",
         [sys.executable, os.path.join(HERE, "test_the_code_running_is_the_code_on_disk.py")], 60,
         why="v3432 (#179) - A PROCESS MUST NOT GRADE A FILE IT IS NOT RUNNING. MEASURED: three pushes of the IDENTICAL tree minutes apart read tv suites green, then test_control FAILED, then tv suites green - and the failing traceback named test_control.py line 11902 with a variable fn, where the file on disk has that assertion at line 11938 using helper. That older shape is exactly the PRE-v3427 code, and the same run also reported an older second-eye version: three anomalies in ONE run, none explicable by the tree, and the full suite then ran 2238 tests OK on it. A suite executing code that is not on disk is WORSE than a red one because its verdict is about a file nobody has, and it cost a real push while pointing at a line that does not exist. It CANNOT be caught by comparing mtime and size - that is what CPython already uses to call a pyc fresh, so a check from the same two inputs agrees with it by construction including when they collide. co_firstlineno comes from the BYTECODE while the source is read fresh, and a disagreement is decisive. The central case CREATES the drift rather than describing it: import a module, rewrite its file 40 lines lower, and require the check to notice. Also pins the false positive this shipped with - functools.wraps copies __module__ onto a wrapper whose code lives in contextlib, which reported two unrelated modules as drifted at the SAME line 242. 3 red-proofs."),
    Gate("test_the_doctor_never_forks_a_quartz_process",
         [sys.executable, os.path.join(HERE, "test_the_doctor_never_forks_a_quartz_process.py")], 90,
         why="v3429 (#150) - THE DOCTOR MUST NOT fork() A PROCESS THAT HAS LOADED THE OBJECTIVE-C RUNTIME. test_control HUNG killed after 1500s on an IDLE machine has refused FOUR pushes since 2026-09-20 and the standing diagnosis was wrong. MEASURED back to back on the same idle machine: cd.run(include_slow=False) hung 28 MINUTES at 0.0 percent CPU, then the SAME call finished in 15.4 SECONDS. So it is a DEADLOCK, not a cost, and RESUME_HERE 8-min-alone measured the HUNG case - its puzzle that the whole is minutes while every part is seconds dissolves. The stuck parent had ONE child at 0 percent CPU wearing the PARENTS OWN ARGV, the signature of a Popen caught between fork and exec, holding Quartz CoreGraphics PyObjC. The escape is PROVEN BY RECORDING WHICH SYSCALL CPYTHON TAKES rather than reading its conditions: close_fds default True gives fork_exec x1, absolute exe plus close_fds=False gives posix_spawn x1, and a BARE NAME plus close_fds=False forks again because the dirname condition bites. Both halves are load-bearing and close_fds DEFAULTS TO TRUE, which is why every ordinary call forks. Pins the driven syscall, the baseline premise, the bare-name trap, and a CLASS law over every subprocess call in console_doctor - which found five more forking shell-outs the single fix had missed. 2 red-proofs."),
    Gate("test_a_live_build_read_is_never_the_banner",
         [sys.executable, os.path.join(HERE, "test_a_live_build_read_is_never_the_banner.py")], 60,
         why="v3428 (#37) - THE BOARDS BUILD ID COMES FROM THE LIVE WINDOW OR IT COMES BACK UNKNOWN. #37 sat blocked for weeks on one value and the GrokBot seat finally said why, three ticks running: live typeof window.D2R_BUILD NOT EVALABLE, no evaluate_js HTTP door on the pywebview seat, /api/eval* -> 404. It could only read the SERVED HTML, which is the file and not the window - and I once reported that blocker LIFTED on exactly that source-only read, which was wrong. board_build() is a NARROW door: one FIXED expression, no parameters, nothing to inject, never a general eval endpoint on the console he is looking at. This pins that it NEVER substitutes the banner or /api/status (that substitution IS the defect 37 bans, and the seat spent weeks correctly refusing it), and that FOUR refusals - window shut, timeout, raise, non-JSON - stay distinguishable from ONE measured absence, because I could not look and it is not there are opposite facts. 2 red-proofs."),
    Gate("test_the_hunt_says_when_somewhere_else_is_quicker",
         [sys.executable, os.path.join(HERE, "test_the_hunt_says_when_somewhere_else_is_quicker.py")], 90,
         why="v3426 (#175) - HIS REPORT 2026-09-23: MY HUNT says COW KINGS HOOVES must be hunted in HELL and calls it the fastest path, while the Sets chronicle sub-tabs rank the same piece in NORMAL with a different silospen find percent. The Hell-first headline is HIS OWN RULING (v1555: prioritized by HELL then Nightmare then Normal... i rather finish off Hell and then the others) and is untouched. What was missing is the other half that same comment promised - when something materially quicker exists at a lower difficulty the source line says so, so he is not choosing blind. v2281 built exactly that on the GRAIL hero and named this defect in its own words: the hint fires only when the fastest is a DIFFERENT ITEM, so for a piece whose Hell lead and global lead are the SAME ITEM at another difficulty nothing is said - item-vs-item where it had to be SOURCE-vs-SOURCE. Cow Kings Hooves reads of 1, one piece left, so the two leads are necessarily the same item. hubNextSet never got it. This gate EVALUATES THE SHIPPED PREDICATE in node, extracted from control_ui.html so it cannot drift from a retyped copy, and pins the mirror (silence when Hell is already quickest), the material threshold, UNKNOWN hours, one shared cutoff across both heroes, and that BOTH heroes carry the disclosure. 3 red-proofs."),
    Gate("test_the_default_eye_seat_is_the_subscription",
         [sys.executable, os.path.join(HERE, "test_the_default_eye_seat_is_the_subscription.py")], 60,
         why="v3425 - HIS RULING 2026-09-23: the xAI CLI SUBSCRIPTION is the DEFAULT second-eye transport, said the hour the paid API lane went dark (mcp upload_file -> PERMISSION_DENIED, all credits used) while the CLI answered v3421 at 95 percent reach with a schema-constrained verdict. It restates 2026-08-05 - the CLI needs no MCP connection, so a seat still fills headless and in cron, and a subscription look cannot stop being affordable mid-arc. This pins that EYE_CLI resolves to an ABSOLUTE path (the G5 scar: shutil.which searched the caller PATH while the console runs under launchd with a bare /usr/bin:/bin, and G5 sat PRIMARY and dark for WEEKS reporting calls=0 errors=0 last_error=None - every lamp clean BECAUSE nobody was asking), that ask() execs it and reaches for no metered API, that the live row separates ABSENT from NOT-EXECUTABLE from UNKNOWN, and that no doc in this repo still carries the inverted claim that the CLI is out of balance and the MCP works. 3 red-proofs."),
    Gate("test_a_scratch_dir_is_not_made_by_reading_the_module",
         [sys.executable, os.path.join(HERE, "test_a_scratch_dir_is_not_made_by_reading_the_module.py")], 90,
         why="v3422 (#170) - A DIRECTORY CREATED AT IMPORT IS CREATED BY EVERY READER. `EYE_CWD = tempfile.mkdtemp(...)` sat at module level, so it ran on IMPORT rather than on use - and 31 modules import second_eye_run, each gate in its own subprocess, so one full gate run left ~30 behind. MEASURED: three BARE imports, no look asked and no eye run, minted three directories; 115 were on his Mac from two days, 33 of them that day. #170 filed it as a dir per LOOK and the measurement refutes its own premise - a handful of looks a day cannot make 33, and fixing the runner would have left the import minting them. The law is driven in a real subprocess, because a second import in this process is a no-op that passes whatever the code says. Also pins the two halves that are easy to get wrong: a directory HE supplied via THIRD_EYE_CWD is never removed, and v3408s rule that the eye stands OUTSIDE the repo still holds. 3 red-proofs."),
    Gate("test_a_broken_pipe_must_not_skip_the_reap",
         [sys.executable, os.path.join(HERE, "test_a_broken_pipe_must_not_skip_the_reap.py")], 60,
         why="v3421 (#166) - KILLING A CHILD IS NOT REAPING IT, AND A SILENT except HIDES "
             "WHICH HALF FAILED. Caught with the zombie ALIVE: `ocr_mac --worker` pid 88160, parent gone, after four rounds of source reasoning could not choose between three Popen "
             "sites. `wp.stdin.close()` shared one try with the reap under `except Exception: pass`, so a broken pipe - the NORMAL end of a worker whose stdin is closed - skipped the "
             "wait() entirely and left one <defunct> per close. The second eye then named "
             "the same shape in the eye's own timeout handlers, so this gate sweeps the "
             "CLASS: every TimeoutExpired handler that kills must also reap."),
    Gate("test_a_constrained_verdict_is_not_a_parsed_one",
         [sys.executable, os.path.join(HERE, "test_a_constrained_verdict_is_not_a_parsed_one.py")], 60,
         why="v3420 (#169) - THE VERDICT IS A FIELD THE MODEL IS CONSTRAINED TO EMIT, NOT A WORD "
             "PARSED OUT OF ITS PROSE. `_verdict_for` and everything under it is a long line of "
             "patches on reading sentences, and its own docstrings are the receipts: a CLEAN look "
             "filed as findings (v2808); a fix that was wrong in BOTH directions, where a "
             "declaration plus exactly ONE listed P1 cleared it (v3198); a review saying NO "
             "DEFECTS filed findings because the word after defects was meeting; an answer ending "
             "VERDICT: clean filed findings. Each patch was right about the case in front of it "
             "and wrong about the next. MEASURED 2026-09-23: grok --json-schema returns an "
             "envelope with structuredOutput and the model cannot emit a verdict outside the "
             "enum. The prose path STAYS for transports that cannot constrain; what this pins is "
             "that the row SAYS WHICH ROUTE produced it, because a forced enum and a guessed "
             "sentence are different evidential objects. Never touches the live ledger - it "
             "repoints SEL.LEDGER_PATH at a temp file per case."),
    Gate("test_a_cap_must_be_a_size_the_eye_has_finished",
         [sys.executable, os.path.join(HERE, "test_a_cap_must_be_a_size_the_eye_has_finished.py")], 60,
         why="v3418 - HIS RULING, 2026-09-22: raise the second-eye cap 9,000 -> 26,000, the call "
             "#143 had been waiting on since v3299 left the cost with him. ⚠ THE OLD NUMBER'S "
             "EVIDENCE HAD EXPIRED WITHOUT THE NUMBER MOVING: 9,000 was justified by 24,000 "
             "chars timing out at 240s, measured against an EYE_TIMEOUT_S later raised to 1200, "
             "so the ceiling it protected against no longer existed. MEASURED COST of the old "
             "cap on three versions in one day - v3413 cannot-tell at 8,622 then 5 findings at "
             "25,074; v3414 never sent control_ui.html, the file the version is ABOUT; v3417 "
             "sent 4 of 5 files not at all. THE LAW THIS PINS, and it cuts both ways: a cap may "
             "only be a size the eye has actually been SEEN to finish at, so it can neither be "
             "raised blindly nor lowered quietly. An EMPTY SEAT is not a witness - it proves the "
             "payload was sent, never that the eye could chew it. Builds its OWN temp ledger, so "
             "it never reads the untracked .second_eye.jsonl and never becomes a runner skip."),
    Gate("test_a_behind_tree_is_not_a_false_all_clear",
         [sys.executable, os.path.join(HERE, "test_a_behind_tree_is_not_a_false_all_clear.py")], 60,
         why="v3416 (#163) - FOUND BY THE SECOND EYE AT FULL REACH, AND ONLY THERE. At the "
             "shipped 9,000-char cap the same eye on the same commit answered cannot-tell with "
             "0 findings; at 25,074 chars it returned 5, and three were real. Two are v3413s "
             "own doctor row: (1) it judged the all-clear by hash inequality, but derived() "
             "writes that sentence whenever origin/main..HEAD is empty - ALSO true when HEAD is "
             "strictly BEHIND origin - so a correct file was called a false all-clear on every "
             "behind tree; (2) an UNKNOWN fingerprint returned OK BEFORE the sentence was "
             "examined, so a file git could not fingerprint read fine whatever else it claimed. "
             "This gate BINDS console_doctor.ROOT to a temp tree and injects a fake git_quiet, "
             "so it drives the shipped row through states this repo cannot be put into on "
             "demand, and never reads his working tree."),
    Gate("test_the_audit_and_the_gate_read_one_row_one_way",
         [sys.executable, os.path.join(HERE, "test_the_audit_and_the_gate_read_one_row_one_way.py")], 60,
         why="v3415 (#162) - THE CONTRADICTION WAS THE FINDING. v3403 taught looked_at (and so "
             "the push gate) that a cannot-tell verdict is NOT a look; audit() never learned it, "
             "so ONE row was read two ways. MEASURED on v3413: looked_at() 0, owes_a_look() True, "
             "audit() looks=1 - the gate refused the push while its own refusal message said to "
             "run --audit, the one screen calling that row fine. And `looks` feeds THREE "
             "surfaces (the --audit mark, the --audit headline, and --backlog), so all three "
             "were blind together. This gate builds its OWN temp ledger holding all five row "
             "kinds and asks BOTH predicates about each, so it never reads his untracked "
             "ledger and never becomes a permanent skip on a runner."),
    Gate("test_a_census_nobody_took_is_not_a_clean_one",
         [sys.executable, os.path.join(HERE, "test_a_census_nobody_took_is_not_a_clean_one.py")], 90,
         why="v3414 (#161) - FOUND BY MEASURING A DASH IN GROKBOT'S FOURTH VISUAL PASS. Every "
             "pass signed `heart=-/20/0/0`, and chasing that leading dash into _heartChipPaint "
             "found two branches painting IDENTICAL pixels: the not-derived branch set "
             "textContent to 'heart' and removed data-dark, and a TAKEN, clean census set the "
             "SAME text and removed the SAME attribute. Only el.title differed, and a title "
             "needs a hover - so on his status bar a census nobody has ever taken read exactly "
             "like a clean one. RESUME_HERE records the live symptom: his Mac console's eagle "
             "answered rows:0 'not measured yet' and the chip could not tell him. This gate "
             "DRIVES the shipped painter in node against a stub element and reads the verdict "
             "off the ELEMENT, never off the source text or the title."),
    Gate("test_a_failed_git_cannot_say_the_tree_is_clean",
         [sys.executable, os.path.join(HERE, "test_a_failed_git_cannot_say_the_tree_is_clean.py")], 60,
         why="v3413 (#160) - FOUND BY READING CI AFTER THE PUSH. Routine M, the "
             "swallowed-exception ratchet, reported RANK 1 baseline 69 now 70 and NAMED the site: "
             "resume_state.py:51, shape return-falsy, a failed run becomes EMPTY-STR. ⚠ AND IT IS "
             "WORSE THAN RANK 1 SOUNDS because of what reads the result: _git returned '' and "
             "derived() feeds that to three renderers that each treat empty as GOOD NEWS - "
             "len(ahead) crashes, 'CLEAN' if not dirty says CLEAN, and the else arm prints "
             "'Nothing is waiting to be pushed'. So a git that could not answer made "
             "RESUME_HERE.md, the file a resuming session reads FIRST and the one carrying "
             "'Nothing has shipped until origin/main equals HEAD', assert the opposite of the "
             "truth. Two holes: the except swallowed into '', and returncode was NEVER read so a "
             "git exiting 128 with empty stdout came back down the SUCCESS path - the same shape "
             "as v3409's _pull_once finding, in a different file. None now travels all the way to "
             "the page as UNKNOWN and the narrative arm says plainly that an absent list is not "
             "an all-clear. ⚠ ATTRIBUTION CORRECTED BY MEASUREMENT: Routine M's first run EVER "
             "was on this sha (502aa2b2 runs=0, bad246d5 runs=0), so the gate ARRIVED, it did not "
             "go green-to-red, and the line dates to v3401. A gate's first run is not a "
             "regression. TWO BASELINE cases stop the opposite failure: a working git must still "
             "render the real counts and a genuinely clean tree must still read CLEAN, so a "
             "generator hardwired to UNKNOWN cannot pass. 7 cases, 3 red-proofs."),
    Gate("test_two_seats_cannot_render_the_same_label",
         [sys.executable, os.path.join(HERE, "test_two_seats_cannot_render_the_same_label.py")], 90,
         why="v3411 (#132) - HIS FINDING, CARRIED SINCE v3385: ambiguity must be measured on the "
             "RENDERED LABEL, not the nickname. REPRODUCED ON THE SHIPPED HELPER over a 5-row "
             "roster: two seats render the identical 'GrokBot - vm-1' and two more render '?', "
             "while the OLD row counted shared non-empty NICKNAMES, found GrokBot, confirmed "
             "control_ui carries the disambiguator and answered OK - a FALSE OK on his screen. "
             "The '?' pair it never looked at at all, because empty nicknames were skipped by "
             "construction. NOT HYPOTHETICAL: his two GrokBot seats already share a nickname AND "
             "an install id; only `machine` differs (grok-bot-vm-346371813 vs cursor), so one "
             "rename makes them indistinguishable. THE ROW NOW COUNTS DUPLICATES AMONG RENDERED "
             "LABELS and answers MISSING naming the pair - 'two seats are indistinguishable on "
             "your screen' is the honest sentence, not 'a disambiguator exists'. ⚠ AND THE FIX "
             "SHIPS A SECOND COPY OF A RULE THAT LIVES IN JAVASCRIPT, which is copy-drift by "
             "construction, so the copies are PINNED: the gate extracts _fleetName from "
             "control_ui.html, runs it in NODE over a 9-roster table and asserts the python twin "
             "agrees on every row of every one - MEASURED rosters 9, AGREE 9, DIFFER 0, including "
             "a whitespace-padded nickname, a shared nickname where one machine is empty, two "
             "blank rows, a solo row with no machine and an EMPTY roster. Without that join this "
             "is two rules wearing one name. THREE BASELINE CASES stop the opposite failure: his "
             "REAL pair, distinct names and a solo row must all stay clean, so a fix that called "
             "everything ambiguous cannot pass. 10 cases, 3 red-proofs."),
    Gate("test_a_broken_tree_is_not_an_established_one",
         [sys.executable, os.path.join(HERE, "test_a_broken_tree_is_not_an_established_one.py")], 60,
         why="v3410 - BOTH LAWS NAMED BY THE CROSS-FAMILY REVIEW OF v3405, then verified and "
             "adversarially refuted against the real source. (1) A FAILED CREATE WAS CACHED AS "
             "DONE: machine_tree.establish() reports a create/prove-write failure as a ROW and "
             "never raises, so _establish_footage stamping on the strength of it-returned "
             "recorded a broken tree as established. MEASURED with TV_HIST=/dev/null/nope/hist - "
             "establish() returned normally with a FAILED row, the stamp landed, call #2 was a "
             "CACHE HIT, and nothing clears that global; _archive_footage_copy then hits "
             "disk_usage on a missing dir, raises FileNotFoundError, and it is swallowed as "
             "return False - every film frame dropped silently for the life of the process, "
             "where v3404's per-frame makedirs used to heal on the next remount. (2) HALF A "
             "HARNESS IS NOT HALF A TREE: with TV_FRAMES_DIR set and TV_HIST unset - exactly "
             "replay.py:217 - the `if not p: continue` skipped the hist root and reported total "
             "success while tv_diablo still computes HIST_DIR = join(FRAMES, hist). MEASURED: "
             "makedirs [frames] only, HIST_DIR created False, and _FOOTAGE_WHY still read 'grab' "
             "so the console showed no reason. THE ASYMMETRY IS THE CARE: frames-set/hist-empty "
             "is DERIVED (it stays in the harness's own scratch tree); hist-set/frames-empty "
             "CANNOT be, because frames would be the LIVE tree, so it is REFUSED and NAMED. "
             "⚠ AND THE OBVIOUS FIX WAS THE DANGEROUS HALF, killed by the blast-radius skeptic "
             "before it shipped: refusing to stamp on ANY bad row retries at FILM CADENCE and on "
             "the live lane establish() walks all six roots - a prove-write storm per frame - "
             "and a REFUSED anchor is not transient, so it would be retried forever. Hence THREE "
             "states: FAILED/UNUSABLE do not stamp but are rate-limited, REFUSED stamps, "
             "created/found stamp. ⚠ The review's THIRD finding was REFUTED by measurement: "
             "resolve()'s frames path and tv_diablo.FRAMES are the same path byte for byte, and "
             "routing HIST_DIR through footage_hist() would have redirected a replay child's "
             "archive writes into his live footage. 10 cases incl. a BASELINE, 4 red-proofs."),
    Gate("test_a_failed_pull_is_not_a_pull_that_found_nothing",
         [sys.executable, os.path.join(HERE, "test_a_failed_pull_is_not_a_pull_that_found_nothing.py")], 60,
         why="v3409 - EVERY LAW HERE WAS NAMED BY THE CROSS-FAMILY REVIEW OF v3404, reading the "
             "shipped diff cold, and all four were real. (1) _pull_once ran git fetch and git "
             "merge --ff-only and read NEITHER return code; only a timeout reached its except, so "
             "an offline fetch, a credential refusal, a FETCH_HEAD.lock held by "
             "fleet_origin_status on the SAME 300s cadence, a diverged history or a refused "
             "fast-forward all left HEAD unmoved - and moved = before != after is False for "
             "nothing-to-do and for it-did-not-work ALIKE, so the lane published 'already level "
             "with origin/main', the one sentence it must never say falsely. Its own None "
             "(cannot ask) was unreachable code, and it is STICKY: a SIGKILLed fetch can leave a "
             "lock behind so every later attempt takes the same false-clean path. (2) git status "
             "exit 128 with EMPTY stdout is how git reports dubious ownership, a broken index or "
             "a held lock, and reading only stdout turned each into 'nothing is modified, go "
             "ahead and pull' - on a console that EXECS THE WORKING TREE. (3) the heart row dated "
             "`behind` from FETCH_HEAD, which any fetch of any OTHER ref rewrites, so a machine "
             "whose main was a day stale could read 'level, fetched 0.0h ago'. ⚠ AND THE OBVIOUS "
             "FIX WAS WORSE, MEASURED BEFORE IT SHIPPED: swapping in the ref's mtime made the row "
             "read MISSING 32.1h on a machine that had fetched minutes earlier, because a fetch "
             "bringing nothing NEW does not rewrite the ref - a row crying wolf is a row someone "
             "silences. Both ages are now reported and NEITHER answers the other's question. "
             "(4) three checks added in ONE session shipped without a WATCHES declaration, which "
             "reads ABSENT in the organ table - indistinguishable from a check nobody wrote. That "
             "law is now executable rather than remembered. 7 cases incl. a BASELINE, 3 "
             "red-proofs."),
    Gate("test_the_eye_is_a_cli_seat_outside_the_repo",
         [sys.executable, os.path.join(HERE, "test_the_eye_is_a_cli_seat_outside_the_repo.py")], 60,
         why="v3408 (#154) - EVERY EYE IS A CLI SEAT ON HIS OWN SUBSCRIPTION, AND IT STANDS "
             "OUTSIDE THE REPO. His ruling 2026-09-22: Grok CLI secondary, Claude CLI primary, "
             "and no API - there is bouncing regardless. THE TRIGGER, measured the same hour: an "
             "API-key seat answered PERMISSION_DENIED, used all available credits, mid-ship while "
             "the pre-push gate was demanding a second-eye look. An API seat that bounces is an "
             "EMPTY SEAT, and an empty seat blocks a push while proving nothing. THE TREE WAS "
             "ALREADY RIGHT AND THAT IS WHY THIS EXISTS: the sweep found ZERO shipped modules "
             "calling a model API across 198 scanned - _claude_env strips ANTHROPIC_API_KEY, "
             "g5_grok_eyes strips six API vars and publishes lane=subscription-cli, "
             "second_eye_run spawns ~/.grok/bin/grok. Nothing needed repairing; what was missing "
             "is the LAW, because a correct state nothing pins is a state that drifts. AND THE "
             "SECOND HALF IS SAFETY, NOT BILLING: a CLI eye is an AGENT with tools, and pointed "
             "at this checkout it can EDIT IT - witnessed 2026-09-22, a Grok CLI session writing "
             "to tv/ while a ship was mid-flight, caught by Konyo rather than by any guard. The "
             "eye now runs with cwd on a scratch dir, and its bound went 300s -> 1200s because "
             "300 was MEASURED too short for a real answer (a 22,519-char payload ran past it and "
             "was filed an empty seat, blocking a ship for a look nobody waited for). 6 laws, "
             "3 red-proofs."),
    Gate("test_windows_git_spawns_hide_the_console",
         [sys.executable, os.path.join(HERE, "test_windows_git_spawns_hide_the_console.py")], 60,
         why="v3407 (#155) - GIT.EXE WINDOWS WERE ALT-TABBING HIM OFF THE GAME. MEASURED on the "
             "Windows box 2026-09-21: 2-3 console windows in a row stealing focus every couple of "
             "minutes while TV DIABLO sat idle, parent pythonw control_app.py --open. Git for "
             "Windows' PATH git (Git\\cmd\\git.exe) is a 46 KB CUI WRAPPER and pythonw owns no "
             "console, so a CUI child ALLOCATES one - a real terminal on top of D2R. "
             "CREATE_NO_WINDOW on the wrapper is not enough: it spawns the real git WITHOUT the "
             "flag, so the flag protects the 46 KB stub and nothing else. headless-git.exe is no "
             "better - a GUI trampoline that still starts a CUI git.exe child (caught live: "
             "git.exe -> headless-git.exe -> pythonw) with Windows Terminal taking the focus. "
             "_git_run calls mingw64\\bin\\git.exe DIRECTLY so CREATE_NO_WINDOW + SW_HIDE apply "
             "to the binary that actually runs, and sets GIT_TERMINAL_PROMPT=0 so it cannot "
             "prompt. ONE OF THE TWO BURSTS WAS MINE: v3404 put _pull_once in the drift beat at "
             "300s beside the 120s fleet cache, which is exactly the cadence he reported - a fix "
             "that keeps a machine current must not cost him the window he is playing in. The "
             "guard reads control_app.py as an AST, not a character window, so it names the "
             "OFFENDING LINE rather than passing because most sites are correct; it found 13 and "
             "all 13 now route through _git_run. 3 red-proofs. Diagnosed and written on the "
             "Windows box, brought over and re-proven here."),
    Gate("test_a_machine_pulls_itself_current",
         [sys.executable, os.path.join(HERE, "test_a_machine_pulls_itself_current.py")], 60,
         why="v3404 (#149) - THE UPDATE MECHANISM LIVED IN THE LAUNCHERS AND A MACHINE CAN BE "
             "STARTED ANOTHER WAY. start_tvd_mac.sh:126 pulls and start_tvd_win.ps1:254 pulls, "
             "so Windows was never missing a launcher - but his KONYO ALT TEST box runs "
             "pythonw console.py and pythonw control_app.py --open directly, bypassing every "
             "automatic pull in the codebase. MEASURED over SSH minutes after origin moved: "
             "BEHIND 5, zero scheduled tasks matching d2r/claude/konyo/pull/bible/tv, zero "
             "startup entries. It was current only because a human kept pulling by hand, and "
             "his report was exactly that - still not being updated automatically. The other "
             "half was already built: _drift_once compares running against disk and "
             "drift_may_relaunch owns the execv with sweep interlocks, so this is a JOIN, not a "
             "feature, and it deliberately adds NO second re-exec path. 7 laws, 3 red-proofs. "
             "The two that matter most: it REFUSES on tracked edits (his console execs the "
             "working tree, so an unguarded pull lands on top of work in progress) and it "
             "honours TV_NO_AUTO_PULL, the switch both launchers already obey."),
    Gate("test_a_probe_licenses_only_what_it_tested",
         [sys.executable, os.path.join(HERE, "test_a_probe_licenses_only_what_it_tested.py")], 180,
         why="v3401 (#147) - A PROBE MAY ONLY LICENSE THE MECHANISM IT TESTED, and this wedged "
             "THREE CONSECUTIVE PUSHES while the bound took the blame. "
             "browser_can_load_localhost falls back to a CDP probe when --dump-dom times out, "
             "records WHICH path worked in LOOPBACK_PATH - and nothing ever read it. check() "
             "asked only the boolean, so CDP works flattened into loopback works and licensed "
             "the --dump-dom loads, a DIFFERENT MECHANISM. The module docstring says it: "
             "Playwright drives the same binaries over the same loopback fine, so it is THIS "
             "LAUNCH PATH on this machine. MEASURED on his Mac: the probe returned True in 13.9s "
             "with path=cdp (12s of dump-dom timing out, then 2s of CDP succeeding), and each of "
             "two targets then burned its full 90s before falling through to node anyway - about "
             "180s a run against a 1500s pre-push ceiling. After the join check() returns in 0.6s "
             "with the same verdict. Two more defects went with it: the probe exercised DIFFERENT "
             "FLAGS than it licensed (--headless=new on a 40-byte page vs --headless=old on 5.6 "
             "MB), now one shared argv builder; and a cached True was never retired by a real "
             "timeout, so target two paid again. The mirror is pinned: a machine where dump-dom "
             "DOES work still gets the stronger browser check."),
    Gate("test_the_resume_cannot_go_stale",
         [sys.executable, os.path.join(HERE, "test_the_resume_cannot_go_stale.py")], 120,
         why="v3401 - THE RESUME SAID WHERE WE LEFT OFF AND HAD BEEN WRONG FOR FOUR DAYS. "
             "MEASURED 2026-09-20: RESUME_HERE.md was last written 2026-09-16 and opened with "
             "6 commits are built, gated locally, and UNPUSHED - naming five commits that had "
             "shipped long before. CLAUDE.md points every new session at that file FIRST, so the "
             "first thing a fresh session read about this repo was four days wrong, and nothing "
             "noticed because nothing could: it was prose. BLUEPRINT.md and HEART.md never drift "
             "for one reason - nobody writes them. They are derived, regenerated on every bump, "
             "and refused at pre-push when stale. His ruling when the heart map had this same "
             "problem: we need it all updated and blueprints updated and heart updated all "
             "derived from the console, then fix this so it is like blueprints too and has "
             "enforcemnt. The resume now travels the same road. Staleness is judged on a "
             "FINGERPRINT OF THE FACTS (head, origin, version) and NOT on the whole block, "
             "because the block also prints a derive timestamp and a fetch age that move every "
             "minute - and a gate that is always red is switched off as fast as one that is "
             "always green. dirty is deliberately excluded: uncommitted files are ordinary "
             "mid-work. The narrative outside the markers is the half a machine cannot measure "
             "and a case asserts it SURVIVES regeneration, because a resume that is only derived "
             "state cannot say WHY anything is blocked."),
    Gate("test_a_failure_reason_reaches_the_shelf",
         [sys.executable, os.path.join(HERE, "test_a_failure_reason_reaches_the_shelf.py")], 120,
         why="v3400 (#141) - THE REASON RETENTION FAILED MUST REACH THE SHELF, AND A NEW MACHINE "
             "IS NOT A BROKEN ONE. reel_retention.plan() publishes its failure reason as `why`; "
             "shelf_driver.work() read `p.get(say)` - a key that exists only on the SUCCESS "
             "payload - so on EVERY failure it fell through to the generic string retention "
             "could not read this shelf. v3393 had already taught plan() to answer no footage "
             "tree on this machine yet, and v3393s own comment names the shelf as a consumer "
             "that drew a 0x0 box: the sentence was written and the shelf never received a word "
             "of it. Two halves, each correct, never joined. MEASURED on his ALT console "
             "2026-09-20 - its eagle read the shelf drivers last beat 2.5h ago reported NOT ok: "
             "retention could not read this shelf, on a machine whose only fault is that nothing "
             "has ever been recorded on it - and reproduced here against an absent tree. The fix "
             "carries a FLAG, not a sentence, so the heart never has to grep English that will "
             "change. ⚠ The mirror case is pinned too: a console that HAS filmed and then failed "
             "must still read MISSING, or the new branch swallows the case the row exists for."),
    Gate("test_a_hidden_element_is_actually_hidden",
         [sys.executable, os.path.join(HERE, "test_a_hidden_element_is_actually_hidden.py")], 120,
         why="v3397 (#142) - `hidden` MUST ACTUALLY HIDE, AND THIS HAS COST HIM TWICE. "
             "[hidden]{display:none} is a USER-AGENT rule, so ANY author display: on the same "
             "element defeats it: the attribute is set, the element stays laid out, and the "
             "source and the screen disagree with nothing to say so. v2443 found it on "
             "button.act - and its own comment records that HE is the one who noticed - then "
             "fixed that one element, wrote the law into a comment naming four earlier "
             "instances, and shipped NO GATE. v3271 then added .win-ctl{display:inline-flex} "
             "beside a hidden attribute, so his window controls have rendered ever since "
             "whether or not they can act, which the JS beside them calls worse than no "
             "button. He asked for that control a THIRD time on 2026-09-20. Measured: 7 "
             "elements defeated, 40 tokens already guarded. The scanner lives in "
             "console_doctor so the gate grades the bytes on DISK and the heart row grades the "
             "bytes the console SERVES - one implementation, two subjects. A law written only "
             "in a comment is a law with nothing enforcing it."),
    Gate("test_a_beacon_records_the_check_in",
         [sys.executable, os.path.join(HERE, "test_a_beacon_records_the_check_in.py")], 120,
         why="v3390 (#135) - A BEACON RECORDS THE CHECK-IN, NOT ONLY THE CHANGE. Konyo answered "
             "the one question I left him: Dean was ON THE CONSOLE, not the website - which "
             "retired my own retraction, because his row still said 26h. Cause: "
             "functions/api/console.js wrote lastseen: only `if (material)` (ver/mode/event/"
             "diskVer/tally/masks/pull/eye.live), so a console OPEN and beaconing every ~4 "
             "minutes with nothing moving left no trace, and its last-seen froze at the last "
             "CHANGE. Dean idles without ticking, so his row froze hardest precisely because he "
             "is the least busy user. REPRODUCED before any fix: an idle repeat beacon stored "
             "[]. Sharper than a frozen number - console: refreshes on a timer, lastseen: had "
             "none, so a machine reads ONLINE with a stale stamp and the offline list then "
             "prints that stamp. THREE ARTEFACTS DISAGREED and the code was the odd one out: the "
             "file header already promised \"written on EVERY beacon INCLUDING heartbeats\" (I "
             "read it, believed it, and told him the beacon was healthy) and the budget sizing "
             "REFRESH_S already paid for it - 4 x (3600/900) x 24 x 2 = 768 writes/day, where "
             "the x 2 is BOTH keys. Fix is one condition, identical to the line above it. This "
             "law drives the REAL handler across TWO beacons against ONE persistent store, "
             "ageing the STORED record between them rather than hand-building it."),
    Gate("test_a_tally_says_whether_it_is_a_measurement",
         [sys.executable, os.path.join(HERE, "test_a_tally_says_whether_it_is_a_measurement.py")], 120,
         why="v3389 (#133) - A COUNT THAT WAS NEVER SYNCED IS NOT A MEASUREMENT. Konyo: \"ok: "
             "True with have: 0 - a confident zero - while the mask says the board has handed "
             "over nothing\". MEASURED on his live roster, row Konyo ALT TEST: tally.ok True, "
             "sets/uniques/runewords all have:0, and the SAME object's tally.ledgerVerdict.ok "
             "False with all three provenance=UNSYNCED. Cause, to the line and in TWO copies 129 "
             "lines apart (control_app.py:2241 and :2370): out[ok] = any(out[k] for k in ...) is "
             "a truthiness test on a container, and {have:0,total:135} is a non-empty dict - so "
             "ok meant \"the row carries ledger keys\", never \"these numbers are a "
             "measurement\". The second copy was found only by printing the match count. The "
             "honest answer was already computed one field away and the outer claim never read "
             "it. ok KEEPS its meaning so older readers survive; the second question gets its "
             "own field. Pins his real row, THE BASELINE that a synced and genuinely empty board "
             "keeps an honest 0, UNKNOWN when no verdict accompanies the counts, one writer for "
             "both sites, and that the card suppresses a number only on an explicit false."),
    Gate("test_the_eye_sees_every_code_extension",
         [sys.executable, os.path.join(HERE, "test_the_eye_sees_every_code_extension.py")], 120,
         why="v3388 (#134) - THE EYE WAS BLIND TO EVERY .js FILE AND FOUND IT ITSELF. Both git "
             "pathspecs in second_eye_run.py listed *.py, *.mjs, *.sh (and *.html for the "
             "roster); *.js was never there - the module extension had been added and the plain "
             "one never was. MEASURED on v3387's payload, a version whose entire subject is two "
             "Cloudflare function files: webSeenSlug 0, recordWebSeen 0, webOnly 0, and "
             "functions/_middleware.js appeared 0 times AND was not in the omitted list, because "
             "a file the pathspec excludes is never a candidate to be reported missing - a false "
             "negative in the instrument v3341 and v3354 built to catch this. Blast radius "
             "measured and small: 1 of the last 60 versions, this one. This law CAPTURES the "
             "argv the shipped code hands to git and REPLAYS it against a purpose-built temp "
             "repo, so it exercises the pathspec that ships and asks git what it means rather "
             "than reading the source. Pins that the roster and the code fetch both reach .js, "
             "that python still reaches the eye (the baseline), that an archived build chunk "
             "does NOT, that the exclusion eats no live file, and that the html top-up stays a "
             "single NAMED exemption."),
    Gate("test_a_presence_reading_names_its_door",
         [sys.executable, os.path.join(HERE, "test_a_presence_reading_names_its_door.py")], 180,
         why="v3387 - THE SITE RECORDS PRESENCE AT TWO DOORS AND THE FLEET COULD SEE ONE. "
             "lastseen: is the console APP beaconing; a browser page-view of /d2r/ lands in "
             "visit: and was readable only at /visits. MEASURED 2026-09-19: I read Dean's row "
             "as 26h and told Konyo he had been gone a day; Konyo had watched him on the bible "
             "six hours earlier. BOTH numbers were right - the rail printed one of them under "
             "the words \"last seen\" with no statement of what the age was OF. The visit VALUE "
             "holds the login name, so grouping page-views by person means reading every one, "
             "and this file's own header already records that doing so blew the subrequest cap "
             "and 500'd the page - hence webseen:<slug>, one durable key per web identity. This "
             "pins that a page-view writes that key and an anonymous visitor is KEPT, that the "
             "write is throttled but never frozen, that a row carries BOTH ages and names the "
             "newer door, that a match is exact or absent, that an unmatched visitor is listed "
             "rather than dropped, that a row with no web half is UNCHANGED (the baseline), and "
             "that one normaliser serves both ends."),
    Gate("test_a_fleet_row_identifies_its_machine",
         [sys.executable, os.path.join(HERE, "test_a_fleet_row_identifies_its_machine.py")], 180,
         why="v3385 - A NICKNAME IS NOT AN IDENTITY. MEASURED on his live console: TWO rows both "
             "read \"GrokBot\" - grok-bot-vm-346371813 on v3383 and cursor on v3377 - two real "
             "seats that both belong there, sharing ONE install id, so machine is the only field "
             "that differs and disambiguating by install would still draw two identical lines. "
             "Since v3384 the peer VERSION decides whether names can be published, so two "
             "identical labels hide which seat is stale. This RUNS the shipped helper in node "
             "rather than re-implementing it, and pins that a shared nickname disambiguates, a "
             "unique one is untouched, an unnamed row still falls back to its machine, and all "
             "four label sites go through the one helper."),
    Gate("test_a_peer_refusal_names_an_action",
         [sys.executable, os.path.join(HERE, "test_a_peer_refusal_names_an_action.py")], 120,
         why="v3384 - THE FLEET REFUSAL NAMED NO ACTION. `maskWhy` is written by the OTHER "
             "machine and arrives verbatim, so a peer that never updates keeps sending \"no "
             "board window\" for ever and v3359's wording fix could never reach it. MEASURED on "
             "his live console: the peer is offline since 2026-09-19T03:38Z on v3342, and the "
             "capability to publish names with no board window arrived in v3379 - a fact the "
             "reader already held in the same roster row and was not reading. This pins that a "
             "peer below the bar is told what would fix it, that a peer at or above it is not "
             "accused, that an absent or unparseable version stays UNKNOWN rather than \"too "
             "old\", and that the verdict actually reaches the panel."),
    Gate("test_a_worker_read_has_a_deadline",
         [sys.executable, os.path.join(HERE, "test_a_worker_read_has_a_deadline.py")], 180,
         why="v3381 - THE SECOND WEDGE IN ONE SESSION, SAME CLASS AS THE FIRST. v3380 fixed a "
             "browser launch that hung because subprocess.run could not reach the grandchildren "
             "holding its pipe. The NEXT gate run hung again, elsewhere: tv/control_app.py 7668, "
             "10572 and 10603 each did a bare wp.stdout.readline() on the OCR worker pipe, which "
             "has no deadline - if ocr_mac --worker never emits a line the reader waits for ever. "
             "MEASURED during the gate: worker pid 23192 held cumulative CPU FLAT at 3:19.05 to "
             "3:19.25 over minutes while its child ocr_mac --worker (pid 24974) was alive 3:46 on "
             "0:00.99 CPU - both idle - and the hook reported test_control HUNG killed after 1500s "
             "on an IDLE machine (load 2.34). The bound was innocent for the second time: six "
             "completed runs on this tree measure 507-564s against it, a 2.66x margin. THE CURE "
             "EXISTED ONE FILE AWAY - tv_diablo.py OcrWorker.read() speaks the SAME protocol to the "
             "SAME binary and is bounded (pump thread, monotonic deadline, q.get(timeout)); "
             "control_app carried its own copy with none of it. One twin safe, the other not. Fix "
             "is _ocr_ask(): one bounded reader, EOF turned into a value so a dead worker returns "
             "promptly instead of costing its whole deadline. ⚠ MY OWN SWEEP WAS TOO NARROW - after "
             "v3380 I swept browsers and lsof and found none of these three; the real class is A "
             "READ FROM A SUBPROCESS WITH NO DEADLINE, and both wedges are instances. Pins behaviour "
             "first: a deaf worker cannot hold the reader, a dying worker returns promptly, a "
             "healthy worker still delivers its payload (the baseline that lets the timeout case "
             "discriminate), and no bare readline returns to the file. 9 cases, 4 red-proofs."),
    Gate("test_a_browser_is_killed_by_its_group",
         [sys.executable, os.path.join(HERE, "test_a_browser_is_killed_by_its_group.py")], 180,
         why="v3380 - FIVE CONSECUTIVE PUSHES WERE REFUSED BY A HANG THAT EVERY BOUND THEORY "
             "MISREAD. The gate died as 'test_control DID NOT FINISH in 1500s' at load averages "
             "9.44, 16.50 and 9.43 - two of the three a QUIET machine, which killed the 'he is "
             "gaming' explanation and every ceiling argument built on it. Two faulthandler dumps "
             "120s apart named the identical frame: js_syntax_gate.check -> subprocess.run -> "
             "communicate -> select, under test_surfaces_parse_in_a_real_js_engine. "
             "subprocess.run(browser, timeout=T) DOES NOT BOUND A BROWSER: its timeout path kills "
             "the LAUNCHER and then calls communicate() a second time to drain the pipes, but "
             "Chrome forks renderer/GPU/zygote helpers that INHERIT the stdout pipe and at least "
             "one reparents to launchd - measured here as a live pid with PPID 1 while its "
             "launcher was already gone. The write end never closes, so that second communicate() "
             "blocks forever. Bounded on paper, unbounded in fact. Signature was identical four "
             "times: the gate halted at 244,189-244,190 bytes and a standalone run at 244,935 - "
             "the same place within 750 bytes, at 0.0% CPU. THE BOUND WAS INNOCENT: six completed "
             "runs on this exact tree measure 507-564s against 1500s, a 2.66x margin, so raising "
             "it would have hidden a real hang behind a bigger number. THE CURE ALREADY EXISTED "
             "AND WAS NEVER JOINED - test_control.py:129 _reap() was written at v1925 for this "
             "exact failure ('ONE killpg reaches the renderer grandchildren that hold the stdout "
             "pipe open') and js_syntax_gate referenced it ZERO times. Fix is "
             "_run_browser_bounded(): Popen(start_new_session=True), communicate(timeout), then "
             "killpg the GROUP, close our pipe ends, wait, and RE-RAISE TimeoutExpired so v1808's "
             "node fallback still runs and 'nobody could check' never reads as 'it is broken'. "
             "Proven live: the same call went from never returning (10+ min at 0.0% CPU, an "
             "orphaned helper at PPID 1) to ELAPSED=194s RC=0 with ZERO surviving children. Pins "
             "behaviour first - a fake launcher that forks a pipe-holding child is killed by "
             "group within the timeout - plus a baseline that a normal launcher still returns its "
             "output, so the timeout case can discriminate. 8 cases, 4 red-proofs."),
    Gate("test_the_board_hands_its_stores_over",
         [sys.executable, os.path.join(HERE, "test_the_board_hands_its_stores_over.py")], 180,
         why="v3379 (#128) - A CONSOLE WITH NO NATIVE WINDOW COULD COUNT ITS ITEMS AND COULD "
             "NEVER NAME ONE. Konyo 2026-09-20 with a screenshot of his own fleet panel: 'fleet "
             "is still not working from dean or from my side.. we cant see or cross reference "
             "the items we each have or both need.. so fix it becuase its still not fixed'. The "
             "panel read: Dean set pieces, you have 133 of 135; YOU STILL NEED (2) filled; THEY "
             "HAVE - YOU DO NOT and YOU BOTH NEED both 'not published - no board window'; footer "
             "131 / 135 theirs (COUNT ONLY). THE CONTRADICTION IS ARITHMETIC: a count of 131 "
             "cannot be produced without knowing WHICH 131. THE TWO FACTS TRAVEL DIFFERENT ROADS "
             "- the COUNT goes board -> window.__tallyPersist -> POST /api/board_tally -> "
             "board_tally.json, and grail_tally has fallen back to that file since v2188, so it "
             "survives a missing window; the LIST is minted by EVALUATING JS inside a native "
             "pywebview window and board_mask had NO fallback at all. A console opened as a PAGE "
             "IN A BROWSER against a headless server can be HANDED facts over HTTP and can never "
             "be ASKED for them, so it published a number for ever and a list never. The sibling "
             "function had had the cure for a thousand versions and nobody carried it across. "
             "THE FIX IS THE MISSING HALF OF A JOIN: __tallyPersist hands the raw ledger STORES "
             "over on the same loopback POST it already uses for the counts, the route banks them "
             "independently of the counts, and _mask_from_board_store composes the union per "
             "fleet_mask.LEDGERS and mints the mask with fleet_mask.encode - which until now had "
             "ZERO production callers, a guard built for exactly this and never reached. MEASURED "
             "with no window anywhere in the process, on his real 135-name sets roster: a board "
             "holding 131 encodes to n=135 have=131 and decodes back to the same 131 real "
             "set-piece names. NO ITEM NAME LEAVES THE MACHINE - same-origin loopback in, base64 "
             "bits out, and the fleet wire is byte-for-byte the shape it already was. FOUR "
             "SAFETIES ARE PINNED BECAUSE EACH IS A WAY THIS COULD BE WORSE THAN A BLANK COLUMN: "
             "a ledger the board sent no store for returns None and never a mask of zeros (which "
             "would render as a confident 'they have none of these'); an unattributed hand-over "
             "is refused, because a mask of the WRONG WORLD reported ok is the v3213/v3215 scar; "
             "a store that is not a list is refused rather than coerced; and a MEASURED EMPTY "
             "list IS kept, because 'he owns none of these' is a real answer and refusing it "
             "would recreate the v3175 collapse on the same panel. THE REFUSAL NAMES BOTH "
             "FAILURES, never just the hand-over, or the panel blames the wrong half. TWO LAWS "
             "ARE REACHABILITY: one makes the hand-over return a sentinel and requires board_mask "
             "- which refuses in six places - to hand it back, so a fallback wired at five of six "
             "fails here; the other pins that every store any ledger is composed of appears in "
             "the page's hand-over list, because the console asking for a store the board never "
             "offers is the silent direction of that drift. 17 cases, 8 red-proofs"),
    Gate("test_a_reel_owes_what_its_engine_says",
         [sys.executable, os.path.join(HERE, "test_a_reel_owes_what_its_engine_says.py")], 180,
         why="v3378 (#28) - THE RIVER CONTRADICTED ITS OWN ENGINE ABOUT WHAT A REEL OWES. "
             "reel_router.STATIONS carries the promise in its own comment - a reel's station is "
             "its POSITION, what it OWES is the named gate in front of it, and two reels can sit "
             "at the same position and owe different work - and four hundred lines below it the "
             "code wrote owes = OWES.get(station), one string per station handed unchanged to "
             "every reel standing there. A rule stated in a comment the adjacent code does not "
             "implement. MEASURED LIVE 2026-09-20 on his 19 reels: two sit at JOIN and "
             "extract_gap, the engine printer.py:508 names as this station's authority, gives "
             "them OPPOSITE verdicts on the very rows the router was reading. "
             "reel_s_1784984019250_95276 (2 names, 1 with a container OPEN) is RECOVERABLE; "
             "reel_s_1786385768689_67392 (45 names, every one on a Chronicle page) is "
             "NOT_A_HOLDING, whose own why reads 'Nothing is owed here: it is neither a join nor "
             "a capture gap.' The router read sealed and names off that same station dict, THREW "
             "THE VERDICT AWAY, re-derived sealed AND names -> JOIN, and told the second reel the "
             "seal owes it code - 45 names filed as owed engineering against v2772's "
             "holding_possible, which had already measured that a Chronicle page is a checklist "
             "with no container open, so the contract's `location` has nothing to take and no "
             "join exists to write. THE FIX IS A FORWARD, NOT A NEW CLAIM: extractSay joins "
             "EVIDENCE_FIELDS, _evidence passes ex.get('say') through untouched, and a pure "
             "_owes_of(station, ev) decides the owed work per reel with the reason beside it. "
             "NOTHING MOVES - the station is unchanged, counts is unchanged (JOIN still 2), "
             "seal_releases_frames is never consulted, and no frame can be released by any of "
             "this; only the sentence changed, which is what was wrong. THE ASYMMETRY IS THE "
             "SAFETY and most of these laws pin it: ONLY an explicit NOT_A_HOLDING may downgrade "
             "the owed work, so an unreadable verdict, an unrecognised word and a reel the engine "
             "never answered for all keep the standing gate - announcing nothing is owed when "
             "nobody could tell is the direction that costs something. TWO LAWS ARE REACHABILITY "
             "RATHER THAN PRESENCE: one replaces _owes_of and requires the printed ROW to change, "
             "so re-inlining OWES.get(station) at the append site fails even though the function "
             "still exists and is still correct; the other puts a keep-reason INSIDE _owes_of and "
             "requires assert_independent_of_retention to go red, proving the new roster entry is "
             "live - _string_keys_read_by does not recurse into callees, so route()'s entry cannot "
             "cover it, which is exactly the hole v2770 found for _routed_by_a_lane. Also pinned: "
             "the override never escapes JOIN, and NOTHING_OWED stays OUT of the OWES map because "
             "_label_of derives his shelf lane names from it and a per-reel sentence living there "
             "would invent a tenth lane he never asked for. 13 cases, 7 red-proofs"),
    Gate("test_the_river_has_one_word_per_fact",
         [sys.executable, os.path.join(HERE, "test_the_river_has_one_word_per_fact.py")], 120,
         why="#227 section 2 - TOMBSTONE cannot mean two facts at once. MEASURED live from "
             "/api/river: lane TOMBSTONE carries byStation ROUTED 3 and TOMBSTONE 0 with "
             "closedCount 453, and his labels map ROUTED to TOMBSTONE and TOMBSTONE to DELETED. "
             "Two defects stacked: the strip printed RAW KEYS while the card badge printed his "
             "words, so one reel was ROUTED on the strip and TOMBSTONE on its own card (v3176 "
             "carved that rule and the strip never got it); and simply applying the labels makes "
             "it WORSE, rendering TOMBSTONE 3 beside DELETED 0 beside 453 closed out, where the "
             "0 and the 453 are THE SAME STATION with two different numbers. That 0 is "
             "structural - a closed reel leaves the shelf - and printed bare it reads nothing has "
             "been deleted while 453 reels have. ⚠ The suppression is conditional ON PURPOSE: "
             "only when the closure ledger could be READ. When it cannot, the count is genuinely "
             "UNKNOWN, the word must stay sayable, and the labelled zero chip stays - suppressing "
             "it in both cases would trade one lie for a quieter one."),
    Gate("test_the_shelf_tabs_are_the_real_sessions",
         [sys.executable, os.path.join(HERE, "test_the_shelf_tabs_are_the_real_sessions.py")], 120,
         why="he asked three times, escalating, because it kept not being done - the tabs ontop "
             "need updating related to the reels sessions, not random or outdated like it is. And "
             "the first time it was DONE it was HALF-DONE by me: v3195 shipped the filter state, "
             "the toggle branch, the predicate clause and the active flag, and never added the "
             "BUTTONS. A complete working filter with nothing on screen able to reach it. This "
             "pins both halves and what not-random means: every chip is earned by a card on the "
             "shelf, the order comes from the river rather than a list written here, an unmapped "
             "station is MARKED not dropped, an empty row hides itself, and every class the "
             "builder emits is actually styled - asked as a JOIN, because two earlier cuts of "
             "that assertion were satisfied by a rename."),
    Gate("test_an_entity_inside_an_escaper_is_printed",
         [sys.executable, os.path.join(HERE, "test_an_entity_inside_an_escaper_is_printed.py")], 120,
         why="read off his screen: the SWEEP box under THE FLEET printed the six literal "
             "characters &mdash; where the elapsed figure belongs. escC replaces & with &amp; - "
             "that is its entire job - so every HTML entity handed to it comes back out as its "
             "own source text. Two sites, both in the sweep meter. ⚠ THE OBVIOUS GUARD IS THE "
             "WRONG GUARD: five of that entity are in the file and only two are defects, the "
             "other three are concatenated straight into markup and render correctly. So this "
             "PARSES rather than greps - it finds each escaper call, walks to its MATCHING close "
             "paren with a depth counter (a nested call would otherwise hide the entity), and "
             "asks whether an entity is inside that span."),
    Gate("test_a_coverage_drop_can_be_named",
         [sys.executable, os.path.join(HERE, "test_a_coverage_drop_can_be_named.py")], 120,
         why="the render gate refused a push with three heart targets down 1-3 nodes, every one "
             "GREEN on pixels - 0 render failures, nothing clipped, every node painting at all "
             "five widths. Only the COUNT moved, and render_coverage.json stored counts and "
             "nothing else, so there was no way from the file to learn WHICH node had gone. That "
             "is the defect, not the drop: a refusal nobody can answer gets re-blessed blind, and "
             "a ratchet re-blessed blind is what excuses the next real collapse. v3201 records a "
             "weak signature per node beside the count and prints the multiset difference. It "
             "stays DIAGNOSTIC - nothing fails because a signature changed, the ratchet is still "
             "the count - and it says UNKNOWN rather than guessing when no baseline exists, "
             "because a diagnostic that fabricates on a cold start is worse than none."),
    Gate("test_the_mac_titlebar_is_the_consoles_own",
         [sys.executable, os.path.join(HERE, "test_the_mac_titlebar_is_the_consoles_own.py")], 120,
         why="he reported the grey TV DIABLO strip TWICE, and the first fix cost him his window "
             "buttons: v3175 paired frameless with fullscreen, he answered now i cant minimize or "
             "window mode the console, AND THE STRIP WAS STILL THERE. v3179 reverted it and left "
             "the instruction - the strip is NOT the pywebview frame, it will be found by LOOKING "
             "rather than by guessing at window flags again. Looked: cocoa.py paints the titlebar "
             "container with the SYSTEM window background in the non-frameless branch, which is "
             "also why framelessness appeared not to fix it. So this pins that the fix reverses "
             "THAT line down THAT path, never goes frameless, never hides a window button, wraps "
             "every native call because cosmetics have cost this app its window three times, "
             "refuses to toggle fullscreen when it cannot read the style mask, and keeps "
             "TV_WINDOWED winning. The constants are checked against AppKit rather than trusted."),
    Gate("test_the_shipped_packs_are_staged_not_his_live_footage",
         [sys.executable, os.path.join(HERE, "test_the_shipped_packs_are_staged_not_his_live_footage.py")], 120,
         why="the packs now SHIP in a public repo, by his explicit call - make it public no "
             "problem - which is what finally lets Grok Bot render a real SHELF on a box that has "
             "no footage. That moves where the risk lives. A local pack that went wrong cost a "
             "rebuild; a published one cannot be unpublished, and the mistake that matters is a "
             "staged session that STOPS SAYING IT IS STAGED, because the whole point of the guest "
             "seat is telling the truth about his console and a fixture indistinguishable from "
             "his footage defeats it. So: every session says fixture:true and names its pack, no "
             "pack leaks a home path or an id, no pack grows back toward the 196 MB reel it was "
             "cut from, the fixture id is namespaced away from his real session id, and the "
             "loader still refuses to write into the live frames tree. The leak audit that "
             "cleared the first five re-runs on whatever is in the tree now."),
    Gate("test_a_fixture_pack_is_not_his_footage",
         [sys.executable, os.path.join(HERE, "test_a_fixture_pack_is_not_his_footage.py")], 120,
         why="his recorded runs, staged so Grok Bot can click them on the guest seat. MEASURED: "
             "one reel is 196 MB / 153 frames, a pack of it is 2.7 MB / 16. Pins that the frames "
             "SPAN the reel rather than slicing its head (a head slice leaves the reel controls "
             "untestable past the opening), that a fixture DECLARES itself and does not wear the "
             "source session's id (it did for one run: the loader deduped it against his 419 real "
             "sessions and the real 153-frame row won, so an eyes-loop would have reported "
             "findings about the wrong footage), that the missing frames read as never-copied "
             "rather than pruned, that a refresh does not duplicate a staged session, and that "
             "the loader REFUSES to write into tv/frames - a pack may be BUILT from his footage "
             "and never LOADED into it, because footage has no un-delete."),
    Gate("test_the_guest_seat_is_grok_not_konyo",
         [sys.executable, os.path.join(HERE, "test_the_guest_seat_is_grok_not_konyo.py")], 120,
         why="the Grok guest seat on the box renders a MIRROR of his live console, and this repo "
             "is public. His /api/status carries an install id, a .local hostname, a unix user "
             "and absolute home paths; the board HTML carries them too - MEASURED on the first "
             "sync run, the raw board came back with FOUR of his identifiers and the leak gate "
             "refused the copy. Pins that the actor is Grok/grok-bot with a STABLE id, that the "
             "scrub reaches dict KEYS (per-session dumps are keyed by path), that the identity is "
             "REPLACED rather than merged, that an unreadable store leaves an explicit record "
             "instead of an empty one, and that no mutating endpoint is in the mirror allowlist."),
    Gate("test_the_chronicle_counts_a_sunder_once",
         [sys.executable, os.path.join(HERE, "test_the_chronicle_counts_a_sunder_once.py")], 120,
         why="his ruling twice over (v2680 and again 2026-09-15): the chronicle counts each of "
             "the six sunders ONCE, while the vault keeps Latent / Renewed / bare as separate "
             "things. It has already been implemented, broken and rebuilt - v2680 honoured it by "
             "filtering the roster, which removed the charms' cards, art and farm routes and "
             "contradicted his v1720 ruling (8 CI failures); v2685 reverted with the correct "
             "diagnosis that the fix belongs on the TALLY; v2691 put it there. Nothing gated any "
             "of it. Pins BOTH halves, because either alone is the bug: FOLDED in _uniItems (or "
             "he is asked to find a charm twice) and PRESENT in the roster (or it loses its "
             "card). Drives the shipped predicate and fold in node, both the array and the OBJECT "
             "branch - the object branch is the one production uses and is where v2680 silently "
             "matched nothing while looking correct."),
    Gate("test_two_vocabularies_for_one_item",
         [sys.executable, os.path.join(HERE, "test_two_vocabularies_for_one_item.py")], 120,
         why="his 2026-09-15 ruling: 'each its own.. for chronicle there is only one name for "
             "it.. and for items found or stashed or items renewed from the hordaic cube these "
             "are their own entity in vault terms'. Both errors were live at once - Latent and "
             "Renewed Sunder Charms risked folding into one row (a false witness), while three "
             "rows he genuinely owns read as unwitnessed because their 159 banked sightings sat "
             "under a typographic apostrophe or the board's own (set piece) suffix. Pins the "
             "axis: a qualifier is IDENTITY, an apostrophe byte / base-type tail / unambiguous "
             "disambiguator is RENDERING. Crescent Moon keeps its (amulet) because the bare name "
             "is ALSO a runeword - same punctuation, opposite meaning, decided by measurement. "
             "Also pins that the console route and the health organ answer alike."),
    Gate("test_trace_spine",
         [sys.executable, os.path.join(HERE, "test_trace_spine.py")], 180,
         why="#99 - follows ONE named item across reel -> ledger -> routing -> endpoint and, the "
             "half that actually proves a filter exists, asserts the NEGATIVE: a chronicle or "
             "farming scenario must produce zero vault rows. That filter has failed once by a "
             "side door already (the v2200 backfill vaulted found-ever names; v2203 reversed it) "
             "and the front door had no red-proof. trace_spine.py itself only reports - footage "
             "has no un-delete and the witnessed machinery stays the only thing that writes."),
    Gate("test_the_removal_journal_forks_like_the_store",
         [sys.executable, os.path.join(HERE,
          "test_the_removal_journal_forks_like_the_store.py")], 120,
         why="the removal door cited this gate BY NAME in its own prose and the file did not "
             "exist - a guard described for anyone who read the comment and never built. Building "
             "it found the comment's premise FALSE: _LP_FORKED has 51 members and d2r_owned is "
             "one, while d2r_vaultRemoved was in neither set, so the journal was BARE while its "
             "store was ladder-forked. The ledger check does not cover it either - _D2R_LEDGER "
             "reads the INSTALL's name from raw storage on purpose, so main and ladder share it. "
             "Remove on main, switch to ladder, restore, and main's removed names land in "
             "ladder's owned list as finds he never made. Pins the SAME-FORK-CLASS invariant "
             "(never 'unforked'), that the key guarded is the one the door writes, and carries a "
             "ceiling on its own parse because an overshooting reader made this look clean twice."),
    Gate("test_a_receipt_can_actually_be_opened",
         [sys.executable, os.path.join(HERE, "test_a_receipt_can_actually_be_opened.py")], 120,
         why="the vault receipt eye shipped DEAD and every instrument said it was fine: it "
             "resolved 4 of 450 banked best-frames (those four by coincidence) because the "
             "handler dropped the reel and addressed a flat hist/<ms>.jpg while evidence frames "
             "live at hist/reel_<sid>/f_<ms>.jpg - every click opened 'frame missing'. After the "
             "fix, 126 of 450, the rest honestly pruned. check_vault_receipts was GREEN "
             "throughout because it asked whether the row CONTAINS a receipt hook; presence and "
             "resolution are different questions and only one is the feature. Pins both halves "
             "of the join and that the organ downgrades when nothing opens."),
    Gate("test_a_sweep_holds_the_relaunch_lock",
         [sys.executable, os.path.join(HERE, "test_a_sweep_holds_the_relaunch_lock.py")], 120,
         why="his order: a sweep cannot be relaunched out from under itself until it has been "
             "read and swept. MEASURED: .sweep.lock was touched in exactly ONE place - the "
             "chronicle sweep - and the vault sweep touched it zero times, so a vault read was "
             "invisible to every out-of-process guard. One sweep already died at 17:09:58 when a "
             "version bump relaunched the console under it, losing 24 classified frames. Pins "
             "that the vault lane takes the lock, heartbeats it while reading, and that "
             "drift_may_relaunch refuses while it is held."),
    Gate("test_the_sweep_says_how_long_it_has_been_reading",
         [sys.executable, os.path.join(HERE,
          "test_the_sweep_says_how_long_it_has_been_reading.py")], 120,
         why="he asked for a time meter on the sweep and the lane that spends the money had no "
             "clock at all: sweep_eta was joined to the chronicle only, so a live vault read sat "
             "43.9 minutes in with 74 paid runs spent and the panel printing 'reels 0 of 14'. "
             "Pins the join, the REEL unit (vault_retro pays per still-run, not per frame - a "
             "frames denominator is the v2168 wrong-population scar in a second lane), the "
             "refusal to report a figure before there is one, and that the meter is STARTED "
             "rather than merely defined."),
    Gate("test_the_engine_room_lives_on_tvd",
         [sys.executable, os.path.join(HERE, "test_the_engine_room_lives_on_tvd.py")], 120,
         why="THE GAMEPLAY HOME IS FOR PLAYING — the seven engine lamps and the whole \u2699 ADVANCED "
             "drawer (engines \u00b7 eyes \u00b7 fleet) now live on TV\u00b7D beside the AI readers, "
             "his same ask that moved the AI READS ticker at v2763. The laws pin BOTH negatives, "
             "because either alone is wrong: only Sessions carries data-view=\"sessions\" while "
             "_toTVD() and every board tab REMOVE it, so \"not sessions\" alone would still leave "
             "these under Runewords, Crafts, Uniques, Sets, Tools and Vault. They also pin that the "
             "hide targets #sig-adv and NOT .rail-secondary — that container also holds #ver-xref "
             "and #heart-ov, two position:fixed overlays, and hiding an ancestor hides a fixed "
             "descendant, which would have left the footer's heart chip opening nothing at all.",
         ),
    Gate("test_the_river_strip_reads_as_a_river",
         [sys.executable, os.path.join(HERE, "test_the_river_strip_reads_as_a_river.py")], 120,
         why="THE RIVER HEADING WAS A FLEX ROW OF BARE TEXT NODES. A run of text directly inside a "
             "flex container becomes its own anonymous flex item, so \"the river \u00b7\", \"49\" and "
             "\"reel(s) on the shelf\" were THREE items, each wrapping its own words in its own "
             "column. Measured at 375px: three ragged columns with the FIFO qualifier crushed into a "
             "61px column three lines tall. Heights 16px at >=561, 31px at 480-560, 47px at <=414 — "
             "all invisible to a check that only reads the wide viewport. The strip also carries the "
             "printer spine's ordinal at EVERY width, because below 700px the connectors are hidden "
             "and four tiles with no direction read as a scoreboard rather than a river.",
         ),
    Gate("test_extract_gap_holding",
         [sys.executable, os.path.join(HERE, "test_extract_gap_holding.py")], 180,
         why="THE SEAL WRITER DROPPED NAMES IT ALREADY HAD. Four sealed reels carry a recoverable "
             "extraction gap, and the row that reported them could not tell 'we looked and there "
             "was nothing' from 'nobody could look' — an unreadable journal answered False where "
             "only None is honest. The laws pin: a sealed reel with unmeasurable names is UNKNOWN "
             "and not REG-340; a chronicle or floor name is not a container; the recoverable "
             "headline counts PANEL names only; and every row publishes `holdingPossible` with its "
             "reason. Proven by tv/sabotage_extract_gap_holding.py — 8 of 8 sabotages RED, each "
             "anchor counted twice (once with comments blanked, so no law can be satisfied by "
             "prose) and the file restored by SHA-256 rather than by re-editing.",
         ),
    Gate("test_the_four_routes_go_red_alone",
         [sys.executable, os.path.join(HERE, "test_the_four_routes_go_red_alone.py")], 120,
         why="EVERY ROUTE NOW HAS ITS OWN DOCTOR ROW, AND EACH CAN GO RED ALONE — one aggregate row "
             "let three healthy routes hide a fourth. Measured on his shelf: inventory 2 of 46 and "
             "stash 11 of 46 read OK with their denominators, and BOTH chronicle routes read "
             "UNKNOWN — 'no reel on this shelf carries a sets ledger, so this route is UNPROVEN "
             "here'. That is the point: an unexercised route must never read OK, which is this "
             "repo's most repeated way of shipping a blind gate.",
         ),
    Gate("test_the_harness_isolates_the_world",
         [sys.executable, os.path.join(HERE, "test_the_harness_isolates_the_world.py")], 120,
         why="ISOLATING THE PORT IS NOT ISOLATING THE WORLD. test_button_matrix has carried that "
             "scar since v1867 — \"a port is one door; the frames, the journal, the sweep memory "
             "and the sweep lock are four more\" — and render_check did all three careful things "
             "(private port, --no-open, reaps its own pid) and then handed the child HIS REAL "
             "ENVIRONMENT. With no TV_HIST, _fixture_root_for_state() and _log_root() fall back to "
             "HERE, so every isolated path resolved to his live tv/. Measured: a render run changed "
             ".board_identity.json, .chronicle_routes_cache.json, .fixture_reels_cache.json and "
             ".tvd_beacon.json. The real defect is older than render_check — `_fixture_root` says "
             "\"v1869: one rule, four files\" and THREE files added after that ship never got it. "
             "⚠ The proof is STRUCTURAL, not a before/after diff: his live console writes those same "
             "files, and attributing them to the harness is the exact mistake made earlier that "
             "night. ⛔ The snapshot is NAMED and capped and never copies frames — tv/frames/hist is "
             "5.6 GB and copying tv/ is the ENOSPC incident this repo has already paid for.",
         ),
    Gate("test_a_populated_world_survives_a_lost_claim",
         [sys.executable, os.path.join(HERE, "test_a_populated_world_survives_a_lost_claim.py")], 120,
         why="HE THOUGHT HIS CHRONICLE HAD BEEN DELETED. On 2026-09-08 his own console window read "
             "0/403 found and offered only \"Claim it to make this browser your board — it imports "
             "nothing\". Nothing was deleted: 169 owned / 429 foundLog / 125 setPieces / 99 rwMade "
             "were in the bare keys the whole time. Ownership is `claim === _D2R_INSTALL`, and "
             "`_D2R_INSTALL` MINTS A NEW ID when both id keys are missing — one eviction and a "
             "populated board renders as an empty stranger's world. His store held THREE ids and "
             "three empty guest worlds. A mismatched claim is now a QUESTION (does this browser "
             "already hold a world?) rather than a verdict, and the recovery re-pins to '*' so an id "
             "re-mint cannot hide it again. ⛔ THE LAW THAT MATTERS MOST is that an EMPTY world with "
             "a stale claim stays a GUEST — a guest writes only under `I·<id8>·`, so bare keys prove "
             "prior ownership and the fix can never hand one ledger to another. The decision is "
             "SLICED FROM bible.html AND RUN IN NODE, never grepped.",
         ),
    Gate("test_the_blueprint_cannot_go_stale",
         [sys.executable, os.path.join(HERE, "test_the_blueprint_cannot_go_stale.py")], 180,
         why="THE MAP SAID IT COULD NOT GO STALE AND HAD BEEN STALE FOR SIX DAYS. blueprint.py's "
             "own header reads \"GENERATED FROM THE CODE SO IT CANNOT GO STALE\" — the right idea, "
             "inherited from ~/achilles-revival with the reverse-blueprint rule — and NOTHING "
             "regenerated it. Measured 2026-09-08: last written Sep 2, and `station` 0 mentions, "
             "`INTAKE` 0, `TOMBSTONE` 0, `printer` 0, `panelFrames` 0. The river and the printer "
             "were both built after that date, so the one surface meant to show the wiring from "
             "above did not know they existed. His question: \"shouldnt this be a connected and "
             "communicating system thats easily seen wired from a macro view\" — it was the MAP "
             "that was missing, not the wiring. ⛔ THE GATE REFUSES, IT DOES NOT REGENERATE: the "
             "pre-push hook grades the WORKING TREE, so a hook that rewrote BLUEPRINT.md would "
             "dirty the tree it is grading and leave the stale file in the commit being pushed. "
             "⚠ THE TIMESTAMP LINE IS EXCLUDED or the gate is red forever and becomes furniture in "
             "a day. ⚠⚠ AND ITS OWN UNKNOWN LAW READ TEXT AND A SABOTAGE WALKED PAST IT — deleting "
             "`\"why\": None` from the river's initializer left the key in its error paths and the "
             "law stayed green. It now BLINDS each dependency and demands the answer.",
         ),
    Gate("test_the_proof_photo_is_found_under_either_spelling",
         [sys.executable, os.path.join(HERE, "test_the_proof_photo_is_found_under_either_spelling.py")], 90,
         why="HALF HIS PROOF PHOTOS WERE REPORTED MISSING BECAUSE THE ID WAS SPELLED THE OTHER WAY. "
             "chron_evidence carries 4,106 `reel_`-prefixed witness rows and 4,411 BARE ones, while "
             "of 663 directories under frames/hist **623 are BARE and 40 prefixed** — two "
             "conventions in one field, and on disk the convention is the opposite of what most ids "
             "suggest. _hist_frame_paths only tried the id as given, so every mismatched lookup "
             "reported the photo ABSENT: 29% reachable, 56% once both spellings are tried, 82 of "
             "300 recovered. ⚠ NOT COSMETIC — those photos are the `provenance` leg of the "
             "extraction contract, the picture behind a banked name, and he is deciding what "
             "footage to delete. A photo looked up wrongly is indistinguishable from one that is "
             "gone, and after a prune the difference stops being recoverable. ⚠ Both directions are "
             "proven red, including the tempting wrong fix: a resolver widened until EVERYTHING is "
             "found would make the already-lost figure vanish without a single file coming back.",
         skip_ok=()),
    Gate("test_a_refused_frame_leaves_no_snapshot_behind",
         [sys.executable, os.path.join(HERE, "test_a_refused_frame_leaves_no_snapshot_behind.py")], 90,
         why="THE REFUSAL PATH WROTE AN 8.6 MB FILE AND THEN LEFT IT THERE. v2799 snapshots the live "
             "frame so the capture cannot replace it mid-read - but the copy happened BEFORE the two "
             "cheapest refusals in the function, and both of those `return`s sat outside the "
             "try/finally that unlinks it, while the comment on that finally asserted 'EVERY return "
             "above passes through here'. ⚠ THE STALE PATH IS THE COMMON PATH: Grok's drive hit "
             "'the newest frame is 3124s old' repeatedly, so every press with the capture off would "
             "have cost one frame-sized file, in a repo that has already paid for an ENOSPC. "
             "★ MEASURED 0 leaked files on his Mac - latent, not manifest, because his console still "
             "runs v2796 and this rewrite had never executed there. The law is BEHAVIOURAL: it calls "
             "the real reader against a real tree and counts what is left in the temp dir, because a "
             "law asserting 'the age check comes first' would pass the moment a third early return "
             "was added below it - which is exactly how this arrived.",
         skip_ok=()),
    Gate("test_the_screen_read_never_blocks_the_button",
         [sys.executable, os.path.join(HERE, "test_the_screen_read_never_blocks_the_button.py")], 90,
         why="THE START POST DID NOT RETURN, SO THE BUTTON LOOKED DEAD. Grok drove /api/mini_auto on "
             "his live console with the game up and fresh frames and measured the POST hanging with "
             "ZERO bytes for 8s and then 25s - no JSON, no `why` - which is precisely 'nothing "
             "happens when i click mini automatic'. ★ A HANG IS NOT A REFUSAL: v2798 gave this button "
             "a refusal toast, and a POST that never returns cannot be toasted, so every fix aimed at "
             "the REASON was aimed at the wrong half. The handler ran the lattice+occupancy scan "
             "INLINE on the request thread, work with no ceiling that measured 0.26s here and 25s "
             "there. ⚠ NOT a timeout and NOT a faster scan - both still block. The law PARSES: the "
             "screen reader may never appear directly in a do_GET/do_POST body, only inside a nested "
             "function a thread runs, because a grep for 'threading.Thread' nearby would pass on a "
             "handler that spawns a thread and then blocks anyway.",
         skip_ok=()),
    Gate("test_a_periodic_check_is_still_watched_unattended",
         [sys.executable, os.path.join(HERE, "test_a_periodic_check_is_still_watched_unattended.py")], 90,
         why="'RUNS SOMEWHERE' AND 'RUNS UNWATCHED' ARE DIFFERENT PROPERTIES AND ONLY ONE WAS "
             "GUARDED. v2801 measured `engines corroborate` at 6,638-13,038 ms in the every-tick "
             "subset and moved it to SLOW. The cost was real; the move deleted a supervision loop, "
             "because _eagle_once passes include_slow=False - so SLOW does not mean 'less often' "
             "there, it means NEVER. That check is the sole caller of corroborate.verdict(), which "
             "holds every cross-engine invariant the console has, so a 19-vs-2 or 1263-vs-403 "
             "disagreement would only have been found by him pressing the eagle button. "
             "⚠ The existing mirror gate was green throughout: 'the full run still performs it' is "
             "TRUE and is not the question. v2802 adds a PERIODIC tier - too costly for a "
             "ten-minute tick, too important to go unwatched - and this law guards the PROPERTY, "
             "not the membership: whatever is periodic must be reached unattended within a bounded "
             "number of ticks, on the first tick after a restart, with run() driven rather than "
             "read. Proven red both ways: include_periodic=False, and the v2801 SLOW membership.",
         skip_ok=()),
    Gate("test_the_era_flips_at_chiliad",
         [sys.executable, os.path.join(HERE, "test_the_era_flips_at_chiliad.py")], 90,
         why="v2888 — Konyo asked for the version bar to rename itself at the 3000 mark: "
             "\"when we hit version 3000 i want it to be called Chiliad 001 ... from version 3001 "
             "its chiliad ... automatically ... like a lock/unlock style\". It ships 113 versions "
             "early and fires unattended, so the boundary is proven NOW, in a real JS engine, "
             "against the shipped window._eraName rather than the source text. Off by one and the "
             "first Chiliad ship reads 'Millenium v001' with nobody watching.",
         skip_ok=()),
    Gate("test_the_census_counts_every_gate",
         [sys.executable, os.path.join(HERE, "test_the_census_counts_every_gate.py")], 60,
         why="v2882 — run_gates registered 279 gates and the heart's census reported 278. The "
             "missing one was `visual-lock`, whose file is visual_lock_invariant.py in the REPO "
             "ROOT; gate_files() looked only in tv/, failed, and dropped it with no line saying "
             "so, so \"0 blind of 278\" read as complete while one gate had never been asked. "
             "Two counts of the same thing disagreed and the quiet one was wrong.",
         skip_ok=()),
    Gate("test_a_total_is_only_as_known_as_its_parts",
         [sys.executable, os.path.join(HERE, "test_a_total_is_only_as_known_as_its_parts.py")], 90,
         # ⚠ `why=` BY KEYWORD. Gate.__init__ is (name, argv, timeout, needs_app, cwd, why, ...),
         # so a 4th POSITIONAL string lands in needs_app — truthy — and leaves why empty. Measured
         # at the gate: 1 of 279 gates had an empty why, and it was this one.
         why="v2881 — the second eye, reviewing v2880: 'unknown vault count is still published as a "
         "complete number on the fields the screen actually reads'. v2880 made lockedVault None "
         "when the tag->lane map cannot be read and left the SUM beside it publishing a confident "
         "count that omitted those reels, and the sentence reading '0 reel(s) (0 MB) are waiting "
         "on a sweep'. Reproduced with a shelf_driver that has no OWED_BY; fixed on all three "
         "surfaces plus the UI. Proven red by restoring the raw sum.",
         skip_ok=()),
    Gate("test_the_backlog_sees_a_version_with_no_row",
         [sys.executable, os.path.join(HERE, "test_the_backlog_sees_a_version_with_no_row.py")], 60,
         why="v2854 — --backlog built its answer from the ledger, and audit() covers only versions "
         "the ledger already mentions. v2852 had no row, so the command whose job is the queue "
         "could not see it; I trusted it and the push was refused. After the fix: 249 shipped "
         "versions examined, 111 never looked at, against the 3 it used to report.",
         skip_ok=()),
    Gate("test_the_lock_derives_from_the_heart",
         [sys.executable, os.path.join(HERE, "test_the_lock_derives_from_the_heart.py")], 90,
         why="v2861 — THE LOCK AND THE HEART WERE TWO SYSTEMS THAT NEVER SPOKE. Konyo: 'the lock and "
             "everything still derives from the heart and visually seen'. Measured when he asked: "
             "self_arming.py and hover_wilson.py held ZERO references to heart2, so a surface could "
             "reach its Wilson bar and ARM ITSELF while the gates that would catch its failure were "
             "blind. A Wilson score says this refused every attack we made; it cannot say and we "
             "would have noticed if it had not. may() now asks the heart in the same precondition "
             "chain as the upstream check, and fails CLOSED on a blind, unreadable or absent census. "
             "It gates on BLIND and deliberately not on partial, which has never been False and would "
             "lock every surface for ever — a gate that can only say no is furniture.",
         skip_ok=()),
    Gate("test_the_heart_can_see_the_surfaces",
         [sys.executable, os.path.join(HERE, "test_the_heart_can_see_the_surfaces.py")], 90,
         why="v2859 — THE RENDER VERDICT WAS NOT DURABLE ANYWHERE. render_check wrote PNGs and, only "
             "on --bless, a coverage floor; WHICH targets reported on a run lived in the push log and "
             "the terminal alone. .render_shots cannot stand in — gitignored, 425 files mixing the 16 "
             "live targets with ad-hoc shots back to v2262. So the heart could not say anything about "
             "pixels because nothing recorded it. render_check now writes .render_verdict.json and "
             "heart2.surface_verdict() reads it with three honest states: OK, PARTIAL (a subset run "
             "cannot speak for the rest) and UNMEASURED. An absent or unparseable verdict is "
             "UNMEASURED, NEVER OK — a surface nobody photographed must not report as one that passed.",
         skip_ok=()),
    Gate("test_the_census_says_how_much_of_it_is_pixels",
         [sys.executable, os.path.join(HERE, "test_the_census_says_how_much_of_it_is_pixels.py")], 90,
         why="v2858 — ONE NUMBER HID A 93/7 SPLIT. Konyo: 'when we hit 100% on heart 2.0 its also "
             "a VISUAL PASS right? like its not just backend'. It is not: 269 gates, only TEN import "
             "render_check or playwright, so 100% on the old single number would be ~96% backend by "
             "gate count — true as a count and a lie as a label. The census now carries "
             "pixelTotal/pixelProved/backendTotal/backendProved. The classifier PARSES: the first cut "
             "text-scanned and answered 18, because prose naming the harness counted as looking at "
             "pixels. Both laws parse rather than grep.",
         skip_ok=()),
    Gate("test_the_shelf_subtracts_the_fixtures",
         [sys.executable, os.path.join(HERE, "test_the_shelf_subtracts_the_fixtures.py")], 60,
         why="v2877 — his ruling: hide the 8 test-fixture reels from THE SHELF, 'just do -8', no "
             "mention of them anywhere on the console. Hiding rows is the easy half; a total that "
             "still counts them is 27 rows under the word 35. One filter, and onDisk, the stage "
             "tallies and the yield percentages all move with it. Proven red three ways: the count "
             "left unsubtracted, the stages left unsubtracted, and the hide list emptied.",
         skip_ok=()),
    Gate("test_a_seal_is_not_an_extraction",
         [sys.executable, os.path.join(HERE, "test_a_seal_is_not_an_extraction.py")], 120,
         why="v2875 — `zero-pages` held 25 stash reels waiting for a chronicle page that was never "
             "filmed (2,437 panel frames, chronicle kind ZERO across all 454 surveyed reels), so "
             "vault-owes was never reached. Lifting it exposed 11 reels the chain called finished "
             "on the strength of a vault seal with zero rows behind it — `panels-never-banked` is "
             "that missing case. Proven red both ways: the hold restored, and the safety removed.",
         skip_ok=()),
    Gate("test_every_walk_is_stamped",
         [sys.executable, os.path.join(HERE, "test_every_walk_is_stamped.py")], 120,
         why="v2875 — the sweep writer has three exits and only two stamped the look. The branch "
             "that fires when the reader DID work wrote no `looked` key, so every genuinely-read "
             "reel that banked no page re-owed a read for ever and could never be tombstoned: the "
             "v2202 deadlock, one branch over. Measured on his 41 reels: 36 records carry no "
             "stamp, agentVers v1868..v2350. Proven red both ways, each branch un-stamped alone.",
         skip_ok=()),
    Gate("test_the_two_keep_floors_agree",
         [sys.executable, os.path.join(HERE, "test_the_two_keep_floors_agree.py")], 60,
         why="v2875 — KEEP_RECENT is one promise written in two files: reel_retention guards the "
             "newest N REELS from deletion, frame_authority guards the FRAMES inside them. A frame "
             "floor below the reel floor empties a reel the retention rule swore never to touch. "
             "Raised 5 -> 8 on his instruction; proven red both ways, each floor moved alone.",
         skip_ok=()),
    Gate("test_a_blind_verdict_names_the_skip",
         [sys.executable, os.path.join(HERE, "test_a_blind_verdict_names_the_skip.py")], 60,
         why="v2866 — the prover printed \"stayed GREEN through its own defeat\" about a law that "
             "SKIPPED in the sandbox and never reached its defeat. v2865 shipped blind:1 for that "
             "reason and the tail saying so (OK (skipped=5)) was in the function's hands and "
             "discarded. Proven red both ways: the skip branch off, and the helper un-joined from "
             "its only call site.",
         skip_ok=()),
    Gate("test_css_generated_text_is_not_a_js_escape",
         [sys.executable, os.path.join(HERE, "test_css_generated_text_is_not_a_js_escape.py")], 60,
         why="v2894 (#58) — a separator written as `content: \" \\u00b7\"` (the JS escape) painted the "
         "literal text U00B7 on his river strip, and render_check called the target GREEN at five "
         "widths twice: generated content is not in textContent, so every automatic check agreed "
         "with the code and disagreed with the screen. Decidable in the source, invisible to the "
         "harness. Proven red by restoring the escape.",
         skip_ok=()),
    Gate("test_the_polled_endpoint_never_waits_on_a_survey",
         [sys.executable, os.path.join(HERE, "test_the_polled_endpoint_never_waits_on_a_survey.py")], 90,
         why="v2897 (#28, REG-895) — tv/.status_worst.json kept the request that named it: totalMs "
         "612,893 with vaultAutoread 603,443 (98.5%), capture=False mode=off agent=False "
         "lockWaitDelta 0. /api/status is polled ~1/s and every 3s TTL miss ran reel_retention."
         "plan() over his footage synchronously in the handler. The refresh is now off-thread, one "
         "at a time, UNKNOWN until it lands, and carries its age. Measured after: worst handler "
         "cost 0.1ms against a 6,000ms survey, 1 invocation across 9 polls. Proven red 3 ways.",
         skip_ok=()),
    Gate("test_the_vault_lane_remembers_across_a_restart",
         [sys.executable, os.path.join(HERE, "test_the_vault_lane_remembers_across_a_restart.py")], 90,
         why="v2901 (#60, REG-900) — _VAULT_AUTOREAD had 14 write sites and ZERO persistence "
         "sites, so every restart wiped what the lane had RETIRED and it paid for those reels "
         "again. His console was replaced twice in one hour. It also made corroborate.py's "
         "vault-lane-has-worked fire on a new process while its own comment called lastTs 'the "
         "durable tell' — both fields were process-local. Now persisted atomically under the "
         "fixture root, with unreadable reported as UNKNOWN rather than as a fresh start. Proven "
         "red 3 ways.",
         skip_ok=()),
    Gate("test_two_surfaces_one_shelf",
         [sys.executable, os.path.join(HERE, "test_two_surfaces_one_shelf.py")], 60,
         why="v2893 (#58) — the shelf subtracted the 8 fixture reels from /api/reel_story at v2877 and "
         "the RIVER STRIP two panels up the same page still counted all 24: 'the river · 24 reel(s) "
         "on the shelf' over a shelf drawing 16, with INTAKE·PRINTER·CAPTURE·TOMBSTONE 6·2·12·4 of "
         "which 2·1·4·1 were fixtures. One shelf, two answers. Proven red three ways: the filter "
         "removed, the closure roster handed the FILTERED report (which reads all 8 as closed out), "
         "and the endpoint unjoined from the set it computes.",
         skip_ok=()),
    Gate("test_a_busy_control_comes_back",
         [sys.executable, os.path.join(HERE, "test_a_busy_control_comes_back.py")], 60,
         why="v2951 — his report: a CANT-CLICK cursor at controls that should be clickable. "
             "Measured: the blanket *{cursor:var(--kcur)!important} beats 82 of 83 cursor:pointer "
             "rules, so `button:disabled` is one of only THREE survivors and a stuck button is the "
             "one thing that can produce that sign. Of 7 self-disabling onclick handlers exactly "
             "ONE never re-enabled on any path. Proven red twice at 1 match each: removing the "
             "re-evaluation, and removing the plan-consume that stops a re-armed WRITE.",
         skip_ok=()),
    Gate("test_the_console_says_which_image_is_answering",
         [sys.executable, os.path.join(HERE, "test_the_console_says_which_image_is_answering.py")], 60,
         why="v2948 — task #67: his console EXECS the working tree, so every save is a deploy, but "
             "a process already running keeps its OLD image and /api/status reported nothing that "
             "changes when the image is replaced. os.execv preserves BOTH the pid and the kernel "
             "start time, so an import-time stamp is the cheapest value that necessarily differs. "
             "Proven red three ways: moving the stamp into the producer, renaming the served key, "
             "and hardcoding the version instead of calling _app_ver().",
         skip_ok=()),
    Gate("test_the_river_has_one_vocabulary",
         [sys.executable, os.path.join(HERE, "test_the_river_has_one_vocabulary.py")], 60,
         why="v2946 — FOUR modules declared an ordered list for one river and three of them each said, "
         "in their own comment, that they were the order a reel moves through; two separately "
         "declared a `tombstone`, and the journal stamped a 9th name (UNKNOWN) no module declared. "
         "river_vocab now says which question each list answers and IMPORTS the canonical river "
         "rather than restating it. Proven red three ways: a second module claiming `position`, a "
         "literal copy of the station tuple, and dropping the UNKNOWN sentinel.",
         skip_ok=()),
    Gate("test_the_lane_asks_the_item_not_the_frame",
         [sys.executable, os.path.join(HERE, "test_the_lane_asks_the_item_not_the_frame.py")], 60,
         why="his 2026-09-12 ruling — a container belongs to the ITEM, not the frame. One deep row "
         "carries one `scene` and many names, and the stash panel shows the inventory beside it, "
         "so 67 of 110 placed sightings carried a container contradicting the item's own "
         "`names_loc`. His three carried fixtures are the known-answer probe: names_loc said "
         "inventory on all 58, scene said stash on 34. The slot half stays UNBUILT — 0 of 151 "
         "deep rows carry any coordinate — and test 5 pins that zero.",
         skip_ok=()),
    Gate("test_one_story_per_snapshot",
         [sys.executable, os.path.join(HERE, "test_one_story_per_snapshot.py")], 120,
         why="printer._sources() promises 'every owner's reading, taken ONCE' and was breaking it "
             "for the story: reel_story.story() ran TWICE per snapshot — via reel_river.river() "
             "and via per_reel_routes.routes() — each doing its own reel_retention.plan(). Stack "
             "traces named both. Now one snapshot, threaded; story() 1, plan() 1. The claim is the "
             "CALL COUNT, not wall-clock: plan() walks the disk so timing swings with the page "
             "cache, and a first reading looked like a 12x regression that was only a cold run.",
         skip_ok=()),
    Gate("test_the_journal_is_read_once_per_change",
         [sys.executable, os.path.join(HERE, "test_the_journal_is_read_once_per_change.py")], 120,
         why="the read-only fleet's item 1, and the largest measured win in the repo — three "
             "dimensions found it independently. The status cache was keyed on `_live_mode`, so "
             "OFF AIR it never applied: ~3.9 of 7.8 points of one core (HALF the idle CPU), ~20 ms "
             "of a 22.4 ms request, 9.38 GB/hr re-read, 200 of 4,033 rows used, against a journal "
             "whose mtime was 49.6h old. Now keyed on (mtime_ns, size), which is STRICTLY fresher "
             "than the 3s window the live path already ships. Pins that a failed stat is never a "
             "cache hit, and that the walk stays TIMED — untimed is how 20 ms hid in "
             "unattributedMs while timing.slowest blamed a 1.9 ms section.",
         skip_ok=()),
    Gate("test_a_lost_store_is_never_seeded_over",
         [sys.executable, os.path.join(HERE, "test_a_lost_store_is_never_seeded_over.py")], 60,
         why="his 2026-09-12 ruling — 'for vault the items should not be seeded like the chronicles "
             "are'. bible.html DETECTED a store that had lost its contents, RECORDED it, NAMED the "
             "restore command, and seeded over it anyway: once the seeds land the store looks FULL, "
             "so the hole is invisible. That is how 17 uniques and 3 set pieces went missing, "
             "unnoticed from 2026-09-08 06:28 UTC. Pins BOTH directions — a lost store is left "
             "alone AND a genuine fresh install still gets its seeds, which is his 'it doesnt start "
             "fresh with 0 items everytime'.",
         skip_ok=()),
    Gate("test_the_river_reads_as_four_lanes",
         [sys.executable, os.path.join(HERE, "test_the_river_reads_as_four_lanes.py")], 60,
         why="his 2026-09-12 rulings on a screenshot of his own shelf — 'i want it down a river "
             "lane ... tombstone at the bottom of it all', 'but i think we had 4', and the names "
             "themselves (INTAKE reads FRESH, STATION reads ANALYZE, TOMBSTONE reads DELETED). "
             "/api/river published four lanes all along and the shelf rendered nine stations FLAT, "
             "in an order where a lane's own sections were not even adjacent. Six of nine keys "
             "disagree with the name in their own OWES text, worst of all ROUTED — which IS the "
             "tombstone and holds 20 reels while the section reading 'TOMBSTONE 0 NEVER REACHED' "
             "is the after-state. Nothing was removed: STATION holds 6 reels.",
         skip_ok=()),
    Gate("test_the_settled_row_names_the_store_it_is_in",
         [sys.executable, os.path.join(HERE, "test_the_settled_row_names_the_store_it_is_in.py")], 90,
         why="his 2026-09-12 ruling — 'leave the keys alone, just fix the store label'. "
             "kaiChronicleSettledWhy stamped store:'foundLog' on every _gFound hit, but _gFound is "
             "a UNION whose first line is `if (owned.has(n)) return true`. Measured on his ledger: "
             "of 360 rows carrying a store, 11 name one whose contents lack that name — 1 an "
             "apostrophe artefact of the audit, 10 real, 8 from this branch, and ALL 10 registered "
             "somewhere (the label was wrong, nothing was lost). The fold is copied from _gFound "
             "because _chMapHas does not fold the apostrophe and would mislabel the four curly "
             "names. Executes the shipped branch in node rather than reading prose about it.",
         skip_ok=()),
    Gate("test_the_armed_prune_cannot_reach_a_reel",
         [sys.executable, os.path.join(HERE, "test_the_armed_prune_cannot_reach_a_reel.py")], 90,
         why="v2984 — he said 'arm it' and _PRUNE_SAFE_TO_RUN is now True. #78's claim that arming "
             "deletes 798 frames from held reels is FALSE: _prune_once globs HIST_DIR/f_*.jpg and "
             "plan_frames reports on HIST_DIR/reel_*/ — measured overlap 0. Test 1 runs the real "
             "deleter above the floor (119 loose frames actually deleted) and asserts every frame "
             "inside a reel survives, so containment is proven by execution, not by reading the "
             "glob. Also pins the floor at 200 and the disjointness note.",
         skip_ok=()),
    Gate("test_a_read_verdict_is_never_stored",
         [sys.executable, os.path.join(HERE, "test_a_read_verdict_is_never_stored.py")], 60,
         why="#79 — `_shadow_watch_note` seeded itself from `shadow_watch_state()`, whose failure "
         "paths return diagnostic dicts wearing `ok`. One unreadable moment laundered a READ "
         "verdict into stored state, and the lockless read-modify-write carried it forward every "
         "20s forever. Measured on his live store: health_engine's shadowWatch row held at "
         "unknown->ok, and corroborate's shadow-armed-is-watching left ungraded. The write is now "
         "atomic too — the torn file was what minted the sentinel, so the defect was circular.",
         skip_ok=()),
    Gate("test_the_ratchet_cannot_erase_the_census",
         [sys.executable, os.path.join(HERE, "test_the_ratchet_cannot_erase_the_census.py")], 60,
         why="v2853 — `--ratchet` wrote {unproven, proved} straight over .heart2.json. Measured in a "
         "sandbox: keys 10->2, provedGates 97->0, verdictAt 45->0, and `proved` 97->98 as the "
         "DECLARATION count replaced the verified one. One ratchet erased every banked proof. "
         "Both laws parse rather than grep.",
         skip_ok=()),
    Gate("test_the_heart_can_see_its_own_instruments",
         [sys.executable, os.path.join(HERE, "test_the_heart_can_see_its_own_instruments.py")], 120,
         why="\u2665 HEART 2.0 — v1 asks whether the SYSTEM is healthy; this asks whether the "
             "INSTRUMENTS that answer that question can still go red. MEASURED 2026-09-08: the "
             "heart was GREEN while 12 of 238 gates were red, 8 of those blind, and CI had been "
             "failing since 06:12 the previous morning — 28 of the last 40 runs. Every check the "
             "heart made was working; nothing was checking the checkers. Three of the eight were "
             "laws that had silently STOPPED MEASURING what they claimed while staying green. "
             "\u2605 246 gates and, before this arc, ZERO executable red-proofs: each was proven "
             "red once by hand and that proof survives only as prose, so the number that can still "
             "go red was UNKNOWN. This law guards the LAYER, not the count: the census must count "
             "something (a 0 here is a broken parser wearing a measurement's clothes — which "
             "happened: the field is `argv`, the first cut read `cmd`, and it printed 0.0%); every "
             "declared RED_PROOF must be well formed with its `find` matching the exact number of "
             "times it claims; the heart must CARRY the result or the proving loop is plumbing "
             "with no tap; an absent state file must read UNKNOWN and never healthy; and heart2 "
             "must write only its state, its proposals and its sandbox — it proposes, it never "
             "edits a guard.",
         skip_ok=()),
    Gate("test_a_lane_that_declines_says_why",
         [sys.executable, os.path.join(HERE, "test_a_lane_that_declines_says_why.py")], 90,
         why="THREE KNOWABLE FACTS WERE REPORTED AS ONE UNKNOWN. Of the eight DARK supervisors on "
             "his console, three read `live: UNKNOWN, tickAgeS: None` — 'nobody can tell whether "
             "this is alive' — and every reason was knowable and DIFFERENT: _mini_watchdog is "
             "EPISODIC (spawned per MINI session, alive only for that session), _orphan_watch runs "
             "in ANOTHER PROCESS (the board window, so its stamps can never reach this reader), "
             "and _orphan_exit_loop DECLINES BY DESIGN (`if not ppid: return`, because a console "
             "nobody claimed must never self-exit). ★ The cost is not only a vague report: "
             "collapsed into UNKNOWN they hide the one case that IS a fault — a scratch console "
             "started WITH TV_PARENT_PID that still declines renders identically to the healthy "
             "primary console. lane_liveness gains DORMANT, a dormancy with no reason is REFUSED "
             "(that would be UNKNOWN in a calmer word), a declared lane must produce a ROW or the "
             "declaration is plumbing with no tap, and a lane that ticks is never reported dormant "
             "— a declaration must never outrank a measurement. ⚠ The three UNTIMED lanes were "
             "left alone HERE, and that reasoning still holds: _engine_driver has four different "
             "sleeps, lane_liveness calls UNTIMED 'a third answer, not a soft version of either "
             "other one', and declaring a period they do not have would manufacture false LATEs. "
             "SUPERSEDED IN PART by v2994 — the right move was never a period but a BOUND: see "
             "test_a_lane_with_no_period_can_still_go_red, which keeps every_s=None on all three "
             "and gives them a declared maximum silence instead, so they can finally go red "
             "without printing a period they do not have.",
         skip_ok=()),
    Gate("test_the_doctor_reads_the_console_not_a_twin",
         [sys.executable, os.path.join(HERE, "test_the_doctor_reads_the_console_not_a_twin.py")], 60,
         why="A DOCTOR ROW MEASURED A DEAD TWIN FOR ITS ENTIRE LIFE (#80). The river-walk row did "
             "`import control_app` and read a MODULE GLOBAL — but the console runs control_app "
             "as its own process entry, so the import builds a SECOND instance whose _RIVER_WALK "
             "is the empty literal: at=None, every process, since birth. Proven by ONE payload "
             "read two ways at the same instant: /api/status.riverWalk said walks=13 / at 15s "
             "old while the eagle's copy of the row said 'has not completed a tick in this "
             "process — unaskable for 4d (1468 attempts)'. Four days of UNKNOWN about a walk "
             "running every 90s. The row now reads THE WIRE, honest from standalone processes "
             "too; an ast law forbids the import returning. Found by the read-only army's "
             "hygiene agent flagging the row, then diagnosed live. Proven red both ways: the "
             "twin's exact face substituted for the wire, and the staleness branch disabled.",
         skip_ok=()),
    Gate("test_the_outlet_pair_rederives_his_rule",
         [sys.executable, os.path.join(HERE, "test_the_outlet_pair_rederives_his_rule.py")], 60,
         why="THE OUTLET'S CORROBORATOR (#80): his rule re-derived from the reels' own evidence, "
             "so a tombstone ahead of extraction goes red INDEPENDENTLY of the acting lane — a "
             "check inside the actor is the actor grading itself. ⚠ THE FIRST PREDICATE WENT RED "
             "ON HIS LIVE DATA WITHIN A MINUTE AND THE RED WAS WRONG: `sealed is False` alone "
             "counted 4 violations, all four worthReading=False/surveyed/names=0 — reels judged "
             "EMPTY OF VALUE where nothing was ever sealed because there was nothing to seal, "
             "and routing them is exactly right. The violation is the CONJUNCTION (worth reading "
             "AND unsealed AND routed); an unmeasured half counts neither way; a routed reel "
             "absent from the evidence walk is the deleter's documented wake. ⚠ v3015 — that "
             "wake is a BLIND SPOT, not a footnote: measured 20 routed and only 4 gradable, so "
             "the old note's '0 of 20' overstated coverage 5x. left() now returns UNMEASURED "
             "when nothing is gradable and the label names the population it counts. Proven "
             "red both ways: the "
             "conjunction dropped to a constant, and the sealed-only narrowing that produced "
             "the measured false red.",
         skip_ok=()),
    Gate("test_the_both_need_column_knows_its_universe",
         [sys.executable, os.path.join(HERE, "test_the_both_need_column_knows_its_universe.py")], 60,
         why="his third fleet column — the items BOTH machines lack — is a COMPLEMENT, and a "
             "complement is a claim about the whole universe where the two columns beside it are "
             "DIFFERENCES that hold over any roster. MEASURED on his tree: sets roster 135 against "
             "a posted total of 135 (safe), uniques roster 398 against 403 (NOT safe) — five of his "
             "own pinned names could never appear in a list claiming to be exhaustive. The guard "
             "refuses the column unless the roster and the posted total agree, reports UNKNOWN "
             "rather than assuming agreement when either is missing, and must never blank the two "
             "difference columns while doing it. No live probe: the total comes from board_tally, "
             "per REG-952. Proven red both ways — a guard that always says yes, and a compare() "
             "that stops returning the complement.",
         skip_ok=()),
    Gate("test_every_doctor_check_is_explained",
         [sys.executable, os.path.join(HERE, "test_every_doctor_check_is_explained.py")], 60,
         why="36 of 59 doctor checks were in NEITHER corroborate registry, so for more than half "
             "the roster 'a joint corroborates this' and 'nobody ever looked' were the same silent "
             "state. Two keys pointed the other way — 'reel rungs' and 'cold read exemption' named "
             "checks that have NEVER existed (git log -S returns one commit, and console_doctor.py "
             "is not in it), claiming coverage for rows nobody runs. Three laws, read off real "
             "imported objects rather than source text: every live check explained EXACTLY once, no "
             "key naming a check that does not exist, and every COVERED_BY claim citing a joint a "
             "REGISTERED builder actually returns. Live after the backfill: 59 of 59 explained, 0 "
             "in both, 0 phantoms. Proven red both ways — unexplain a check, and rename a roster "
             "entry so its key becomes a phantom.",
         skip_ok=()),
    Gate("test_the_backup_prune_never_orphans_a_loss",
         [sys.executable, os.path.join(HERE, "test_the_backup_prune_never_orphans_a_loss.py")], 60,
         why="RETENTION SIZED FROM HIS OWN LOSS (#81). The 2026-09-08 emptying was noticed ~3 "
             "days late and the oldest backup was 69 HOURS too young to say which backup predates "
             "the loss. His ruling: 'auto saved daily in a ledger just incase'. Policy: 48h "
             "rolling + first-of-day keepers for 90 days + THE EPISODE GUARD — while a "
             "d2r_storeEmptied episode is OPEN, the newest backup older than its `at` is "
             "protected whatever its age, because pruning it would be the backup system deleting "
             "its own reason to exist. Retention runs only after a successful new snapshot, so "
             "the corpus never shrinks except in the breath it grew. Every law drives the "
             "SHIPPED function on a fixture dir and counts what survived; deletion is the "
             "irreversible act so unreadables count as kept. Proven red three ways: dropping the "
             "keeper branch, dropping the episode guard, a zero rolling window.",
         skip_ok=()),
    Gate("test_the_auto_door_says_why_it_holds_a_name",
         [sys.executable, os.path.join(HERE, "test_the_auto_door_says_why_it_holds_a_name.py")], 90,
         why="A CORRECT HOLD WAS WEARING A FAULT'S CLOTHES (#77). One name clears two witnesses "
             "and sits unbanked: Crescent Moon — and the refusal is CORRECT, because the name has "
             "multiple referents (two uniques share it, plus the Shael+Um+Tir runeword) and two "
             "witnesses corroborate a NAME, not an ITEM. But ledger_of returns the FIRST roster "
             "hit, so nothing downstream could know about the second referent, and the doctor "
             "reported the hold as owed work ('the auto door can take those for free'). v3008: "
             "referents_of reports EVERY hit, split() separates autoHeld from autoOwed, and the "
             "doctor names the hold and its reasons — measured live: 'HOLDING 1 name(s): Crescent "
             "Moon (2 referents: UNIQUE/RUNEWORD)'. Owed (single-referent, cleared, unbanked) "
             "stays MISSING; an older lane without the split SAYS it cannot tell. Proven red "
             "three ways: early-returning the first hit, a threshold no name reaches, dropping "
             "the held branch.",
         skip_ok=()),
    Gate("test_the_waiting_on_you_reaches_the_inbox",
         [sys.executable, os.path.join(HERE, "test_the_waiting_on_you_reaches_the_inbox.py")], 90,
         why="THE 15 WAITING ON YOU NEVER REACHED HIS INBOX (#77). The console's watchdog has "
             "carried them for months (/api/status -> eagle.rows; needsYou=12 measured live), the "
             "console UI shows the chip — and bible.html, where the INBOX lives (242 inbox refs), "
             "had never heard of the field. Two halves each built right, never joined. v3006 "
             "joins them: a sibling #ibx-needsyou section (a CHILD of #inbox-panel would be "
             "clobbered by renderInbox's innerHTML writes — v2219's class of bug), its own "
             "painter, a 120s fetch (the eagle re-looks every 600s). ⚠ An unreachable console "
             "reads UNKNOWN never 'nothing waiting'; a null needsYou is the eagle never having "
             "looked, unmeasured not clear; only state==='missing' rows are WAITING — an 'ok' row "
             "in the pile teaches him the pile lies. Every law EXECUTES the shipped painter and "
             "classifier in node. Proven red three ways: dropping the off-console branch, "
             "counting every row as waiting, and folding never-looked into all-clear.",
         skip_ok=()),
    Gate("test_the_census_sees_a_stamped_lane",
         [sys.executable, os.path.join(HERE, "test_the_census_sees_a_stamped_lane.py")], 60,
         why="'SUPERVISED' MEANT 'IN THE roster LITERAL', and that stopped being the only way to "
             "be watched at v2994 (#80). A lane that stamps _lane_tick is watched by "
             "lane_liveness with no roster row, and the census kept calling it unsupervised. "
             "MEASURED 2026-09-12: 20 rows reported unsupervised, 8 of them stamping a lane tick, "
             "and the number of GENUINELY unwatched loops was ZERO — the instrument #80 uses to "
             "report supervision gaps was inventing eight of them, and my own task text repeated "
             "the invented number twice before the running system corrected it. The stamps are "
             "PARSED (ast), not grepped — this repo's own docstrings write _lane_tick('...') in "
             "prose, and one law plants exactly that ghost in a comment and requires it NOT be "
             "credited. Proven red three ways: narrowing supervised back to the roster, forcing "
             "the regex fallback on parseable source (the ghost gets credited), and dropping the "
             "via field that says WHICH authority watches a lane.",
         skip_ok=()),
    Gate("test_the_ledger_says_where_the_item_actually_landed",
         [sys.executable, os.path.join(HERE, "test_the_ledger_says_where_the_item_actually_landed.py")], 90,
         why="`store` WAS A CLAIM ABOUT WHERE AN ITEM IS, WRITTEN BEFORE ANYONE LOOKED (#74). In "
             "the tvVaultRegister wrapper `status` is DERIVED and can say 'route-failed', while "
             "three lines below it in the SAME object literal `store: 'owned'` was asserted on "
             "every row — so one row could read status:'route-failed' and store:'owned' in the "
             "same breath. The vault is the store whose mistakes are permanent and the one he has "
             "been bitten by, and this is the field a reader consults for 'where did it go'. "
             "Measured previously (labelled, not re-derived): 11 of 360 rows named a store whose "
             "contents lack the name. ⚠⚠ THE FIX HAD TO AVOID THE TRAP THIS FILE HAS SPRUNG FOUR "
             "TIMES: _chSetHas/_chLsGet do exactly what the reader needs and live in script block "
             "#24, while the write site is block #17 with neither exported to window — calling "
             "them is a ReferenceError that reads as correct in review. It goes through "
             "window.LSR instead, assigned in block #1, which is what _chLsGet itself reads "
             "through. Three answers, never two: a store that could not be READ is null, not a "
             "denial. Proven red three ways: restoring the flat literal, returning false instead "
             "of null on an unreadable store, and bypassing LSR for raw localStorage.",
         skip_ok=()),
    Gate("test_the_shelf_publishes_where_it_is_not_just_that_it_is_full",
         [sys.executable, os.path.join(HERE, "test_the_shelf_publishes_where_it_is_not_just_that_it_is_full.py")], 90,
         why="A DOM CAN BE FULLY BUILT INSIDE A CONTAINER THAT OCCUPIES NO PIXELS (#58/#34). "
             "Grokbot 2026-09-12, ver and liveVer BOTH v2988: the shelf stage is an EMPTY DARK "
             "PANEL — no cards, no headings, and two stage crops 5s apart BYTE-IDENTICAL so it is "
             "not a slow paint. At that same moment the console's own beat said filled=true, "
             "cards~535, ink=true, and my headless probe built 530 cards with no JS error. Both "
             "readings are honest: the beat published a FILL and never a RECT, so nothing in it "
             "could contradict his eyes — the one question never asked was WHERE the container "
             "is. The pair is the point: cards>0 with a state that is not `shown` is a built DOM "
             "nobody can see. ⚠ The shelf is deliberately NOT a row in the panels roster — those "
             "are panels that belong on their view, so `hidden` earns the name DARK, 'the fault "
             "and only this'. The shelf is an on-demand overlay, closed almost always, and a "
             "roster entry would publish a fault forever until he stopped reading it. The gate "
             "EXECUTES the shipped block in node rather than asserting text is present, because "
             "a presence check is how a law stays green through its own defeat. Proven red three "
             "ways: removing the zero-box test, dropping the card count, and calling a closed "
             "overlay DARK.",
         skip_ok=()),
    Gate("test_a_frozen_screen_is_never_reported_healthy",
         [sys.executable, os.path.join(HERE, "test_a_frozen_screen_is_never_reported_healthy.py")], 60,
         why="A PAGE THAT ANSWERS 200 CAN PAINT NOTHING (#34). Measured on his machine "
             "2026-09-10 from Grok Bot's captures: the TV DIABLO window was a DARK BLANK at 19:08 "
             "and a WHITE BLANK at 16:16 — titlebar and nothing else — while every text check "
             "said healthy (GET / 200 in 16ms, GET /api/status 200, 'quiet hold, HEART census "
             "held, did not kill'). Every other doctor check is blind to a dead compositor by "
             "construction. frozen_frame_watch hashes screencaptures of the REAL window instead. "
             "⚠ THIS GATE EXISTS BECAUSE THE DETECTOR'S FIRST REAL RUN PRODUCED THREE FALSE "
             "POSITIVES that all looked like a dead console: a FILE COPY (gap 0.0s), two crops "
             "0.1s apart, and a 280x280 cursor REFERENCE copy. Identical is not the evidence — "
             "identical ACROSS A GAP IN WHICH A LIVE SCREEN WOULD HAVE CHANGED is, and a crop is "
             "not a window. It also pins that a missing capture folder (CI, any machine but his) "
             "is UNKNOWN and never a clean bill, and that FROZEN never claims BLANK — that is a "
             "claim about content only an eye can make. Proven red three ways: removing the "
             "independence walk, letting an absent folder report MOVING, and dropping the window "
             "floor.",
         skip_ok=()),
    Gate("test_a_lane_with_no_period_can_still_go_red",
         [sys.executable, os.path.join(HERE, "test_a_lane_with_no_period_can_still_go_red.py")], 60,
         why="A COMPUTED SLEEP IS NOT A LICENCE TO BE UNFALSIFIABLE. lane_liveness had ONE field "
             "carrying TWO questions: every_s answers 'how often does this run' (it prints "
             "'against its own 30s period'), while LATE actually needs 'how long may this be "
             "silent before the THREAD is dead'. They coincide for a fixed-sleep lane and come "
             "apart for a loop that sleeps on a branch — so those three passed every_s=None, "
             "became permanently UNTIMED, and no silence of any length could turn them red. "
             "MEASURED on his console 2026-09-12 over 90s: _bridge_prober ticked every 1.2s, "
             "_engine_driver every 2.0s, _kai_closer_loop every 30.0s — all three UNTIMED. Three "
             "of twenty lanes, each alive and each unfalsifiable. ⚠ The tempting wrong fix is to "
             "pad every_s, which buys the red path by printing a period the loop does not have; "
             "one test refuses that, and another refuses a bound BELOW the loop's own worst "
             "sleep, which would report a healthy turn as a dead thread. Proven red three ways: "
             "disabling the bounded path, stripping a real call site's bound, and setting a bound "
             "under the loop's own 30.0s sleep.",
         skip_ok=()),
    Gate("test_a_witness_written_for_the_rescue_is_called_by_it",
         [sys.executable, os.path.join(HERE, "test_a_witness_written_for_the_rescue_is_called_by_it.py")], 90,
         why="A WITNESS WRITTEN FOR THE RESCUE THAT THE RESCUE NEVER ASKED. paint_witness exposes "
             "three rescue-facing functions; measured across the tree, blank_strikes had 1 "
             "production caller, rescue_worked had 1, and contradicts_a_blank_beat had ZERO — the "
             "one its own docstring calls 'THE VALUABLE DIRECTION, and the one his rescue needs "
             "most ... True here should HOLD a rescue'. ★ That direction costs more than the "
             "other, because it is the one that ACTS: everything the rescue reasons from is "
             "published BY the page, and a beat claiming blank while the compositor is painting "
             "means reloading a WORKING window under his hands. The reload is the harm. ⚠ And "
             "UNKNOWN must never hold a rescue — an unreadable capture returns False, so a broken "
             "camera cannot become a permanently disabled self-heal; the law pins that direction "
             "too, and that the hold CONTINUEs rather than falling through into the reload. The "
             "law is the general shape, not one name: every public entry point whose docstring "
             "names the rescue must have a caller outside the tests, because this is the THIRD "
             "time a witness in this tree was built, proven and joined to nothing.",
         skip_ok=()),
    Gate("test_the_ledger_cannot_lie_about_what_it_saw",
         [sys.executable,
          os.path.join(HERE, "test_the_ledger_cannot_lie_about_what_it_saw.py")], 90,
         why="The second-eye ledger exists so a thin look can never be filed as a thorough one, "
             "and it was failing at that THREE ways at once, each hiding the next. (1) The caller "
             "passes sent=code_was_transmitted(prompt) — already a measurement — and record() "
             "re-measured that DICT, giving chars 0, BYTE-IDENTICAL to sent=None, which the "
             "docstring defines as NOBODY CHECKED. Census: 417 rows, 20 with a sentCode, 9 zero — "
             "every look through the real path — and all 11 healthy ones written by the test, "
             "which passes raw text. (2) The unsent seam patterns let backslash-s cross a "
             "newline, and in a unified diff every added line starts with '+', so an added "
             "docstring reads as a concatenation seam: 24 false hits on the v2807 payload, zero "
             "genuine. A non-empty unsent RETRACTS the row and a version cannot ship while the "
             "previous is retracted, so this would have deadlocked the repo shut the moment (1) "
             "was fixed. (3) _findings_from folds an unenumerated answer into one block, so 'No "
             "defects found.' was recorded as verdict=findings — the ledger reporting the "
             "opposite of what the other family concluded.",
         skip_ok=()),
    Gate("test_a_banked_name_opens_its_proof",
         [sys.executable,
          os.path.join(HERE, "test_a_banked_name_opens_its_proof.py")], 90,
         why="The ticket verbatim: click a banked name, see the actual frame full-screen. The NAME "
             "was inert text; the only route to the proof was a 15px icon opening a raw JPEG in a "
             "new tab, and only when served from the console — off-console it rendered dimmed and "
             "did nothing. Meanwhile a real full-screen lightbox has existed in the same file "
             "since v741 (#tvd-frame-lb / _tvdOpenFrame) and the routing ledger never called it: "
             "both halves shipped, never met. It is clickable off-console too, deliberately, "
             "because _tvdOpenFrame carries its own bridge/archive/missing chain and 739 of "
             "10,318 cited frames no longer resolve — a reader is better served by a lightbox "
             "that SAYS the proof is gone than a dimmed icon that silently does nothing. ⚠ The "
             "first cut called jsq(), the forge IIFE's escaper, which is not in this scope: a "
             "ReferenceError thrown while BUILDING the row would have taken the whole ledger "
             "down, so one law pins that the escaper it uses is actually in scope.",
         skip_ok=()),
    # ⚠⚠ v3110 — `test_each_flow_strip_names_its_own_engine` IS RETIRED, NOT DELETED, AND THIS
    # NOTE IS THE RECORD. That law's subject was the shelf stacking TWO flow strips: its own
    # docstring said "THE SHELF stacks two 'flow' strips in one overlay ... Both use the word
    # PRINTER and mean different things". v2819's answer to that duplication was to make each
    # strip NAME ITS SOURCE. Konyo's ruling on 2026-09-14 was that labelling them never stopped
    # them reading as separate engines - "two diffrent sections rendering the same", "i would want
    # it unified only visually obivously" - so the printer spine is gone from the shelf and a law
    # requiring a SECOND strip to name a SECOND engine is a law about a world that no longer
    # exists. Its surviving clauses (the strip names its engine; the tag has a CSS rule; a tag
    # built and never rendered is no tag) moved into the replacement below, which ALSO pins the
    # removal so the duplication cannot come back. A red law deleted to make a change land is the
    # green that lies; a red law replaced by the true one is the change being finished.
    Gate("test_the_shelf_shows_one_flow_strip",
         [sys.executable, os.path.join(HERE, "test_the_shelf_shows_one_flow_strip.py")], 120,
         why="THE SHELF SHOWS ONE FLOW STRIP, AND IT NAMES THE ENGINE BEHIND IT. Replaces "
             "test_each_flow_strip_names_its_own_engine, whose subject was the shelf stacking TWO "
             "flow strips drawn from different modules in different vocabularies - river_lanes' 4 "
             "lanes over 9 router stations against printer.stream()'s 7 stations, both using the "
             "word PRINTER for different things. v2819 answered that by labelling each source; his "
             "2026-09-14 ruling is that labels never stopped three axes reading as three engines, "
             "so the printer spine no longer draws on the shelf. SURVIVING clauses are kept: the "
             "strip must name its engine, the tag must carry a CSS rule or nobody sees it, and a "
             "source tag BUILT into a variable and never concatenated into markup is the same as "
             "no tag (v2819's own near-miss, now generalised to any spelling rather than the one "
             "name it used). NEW clause: the spine may not come back - a removed section without a "
             "guard is a ruling that has to be made twice. ⚠ THE BACKEND IS UNTOUCHED and that is "
             "the scope he set: /api/reel_story still returns printerStations and printerCounts "
             "and printer.py still walks every station; only the drawing changed. ⚠ AND IT READS "
             "EXECUTABLE TEXT ONLY - the first run went red on a v2587 COMMENT mentioning "
             "`.shp-st b u` while the markup was already gone, which is the mirror of v3102's "
             "BLIND proof where a comment quoting an expression satisfied the check about it."),
    Gate("test_a_declared_station_can_be_reached",
         [sys.executable,
          os.path.join(HERE, "test_a_declared_station_can_be_reached.py")], 120,
         why="reel_router.STATIONS declares TOMBSTONE and nothing in _station_of()/route() ever "
             "assigns it, so counts[TOMBSTONE] was structurally 0 and route()[unreached] named it "
             "on EVERY run — the module reporting its own gap to nobody for months. Meanwhile "
             "reel_tombstones.json held 428 closed-out reels with ZERO overlap against the 41 on "
             "disk, so river_lanes TOMBSTONE lane — labelled closed out, the extraction contract "
             "is satisfied — could only ever display ROUTED-but-still-present reels and could "
             "never show a reel that had actually closed. ★ The per-reel walk is deliberately NOT "
             "widened: every source feeding it walks what is on disk, and folding 428 ledger "
             "entries into the rows would silently move shelf from 41 to 469 — a number he reads, "
             "changed by a refactor. The ledger is published BESIDE the walk with its own "
             "denominator and source. An unreadable ledger is UNKNOWN, never a confident 0.",
         skip_ok=()),
    Gate("test_a_gate_names_its_subject_by_importing_it",
         [sys.executable,
          os.path.join(HERE, "test_a_gate_names_its_subject_by_importing_it.py")], 120,
         why="#52. heart2_candidates resolved a gate's subject only from filename string literals, "
             "which left 94 of the 238 unproven gates with NO resolvable subject at all — the "
             "single largest refusal bucket — and every one of those 94 imports a local module. A "
             "gate that says `import reel_router as RR` and asserts on RR has named its subject; it "
             "just does not spell it with a .py. After resolving from imports: no-target-file 94 -> "
             "5, derivable 78 -> 104. ★ AND THE TRAP: 95% of gates import console_safe, the stdout "
             "encoding helper. Resolving a subject to it would derive a tamper that DOES redden the "
             "gate while proving nothing — every gate importing it goes red together, the most "
             "convincing kind of green that means nothing. So infrastructure is excluded and the "
             "threshold is COMPUTED, not hardcoded: measured over 264 gates the distribution is "
             "console_safe 95%, then a cliff to control_app 21%, so INFRA_SHARE 0.25 sits in the "
             "gap and a module that becomes ubiquitous later is excluded without anyone noticing. "
             "Also held: filename resolution still works, stdlib resolves to nothing, a corpus "
             "under 20 files excludes NOTHING (a share over 3 files is noise), real subjects are "
             "not swept up, and a gate is still never its own subject. Three tampers proven red.",
         skip_ok=()),
    Gate("test_a_covered_label_is_still_in_the_picture",
         [sys.executable,
          os.path.join(HERE, "test_a_covered_label_is_still_in_the_picture.py")], 90,
         why="#54, and it is the root cause of the whole heartov2 family. leaves() ends with a hit "
             "test — elementFromPoint at each element's centre, dropped if something else answers "
             "— which is right for 'what is visible' and which pxCount (the overlap ratchet) "
             "depends on. It is exactly wrong as the input to a solver whose job is to separate "
             "OVERLAPPING labels: for a covered label something else always answers, so the one "
             "label the fit pass most needs is the one it never receives. MEASURED on a live "
             "render: of 20 authored fan labels, vault.sweep_start was dropped because the point "
             "at its centre returned an hrt-fan-arith label lying on top of it. It entered no "
             "items, so the solver read 1 collision where there were 2; it entered no stack, so "
             "when that stack moved dx=-16 the NAME stayed behind; and pxCount calls the same "
             "leaves(), so the ratchet could not see it either — four instruments, invisible to "
             "all at once, which is why the panel read clean while his screenshot showed labels "
             "running through each other. After taking the fan from the authored NodeList: "
             "painted 19->20, collisions seen 1->2, moves 3->4, final 0. ⚠ leaves() is UNCHANGED "
             "and still the obstacle set — the fix is not 'delete the hit test', and this gate "
             "holds that too. Three tampers proven red.",
         skip_ok=()),
    Gate("test_the_fan_keeps_its_own_verdict",
         [sys.executable,
          os.path.join(HERE, "test_the_fan_keeps_its_own_verdict.py")], 90,
         why="#53. _hrtFanFit returns the whole record of what it tried — reverted, solve.from -> "
             "solve.to, passes, moves, before/after/wouldHaveBeen — and its ONLY caller was "
             "`try { _hrtFanFit(ov); } catch (e) {}`, which discarded all of it INCLUDING the "
             "exception. That one line is why #53's central question was UNKNOWN: a probe measured "
             "withTransform 0, which is consistent with the solver finding no move AND with it "
             "finding one and the all-or-nothing revert putting it back — opposite causes with "
             "different fixes, and three distinct root causes are already on record for this "
             "symptom. MEASURED once the report was kept, over a live headless render at scale "
             "1.074: reverted FALSE, solve from {collisions 1, adjacent 2} to {0, 0}, ratchet "
             "before 1 after 0, 3 stacks kept, 5 of 20 labels transformed — so in the render world "
             "the solver WORKS and keeps its solution. ⚠ NOT a verdict on his console: that is the "
             "fixture world and his lock set differs; what changed is the question is now one "
             "attribute read away. Two surfaces because they have two readers — window._hrtFanLast "
             "for a CDP probe, data-fanfit for the render harness which cannot reach a JS global. "
             "Neither is visible to him. Three tampers proven red.",
         skip_ok=()),
    Gate("test_the_fan_names_the_stacks_it_kept",
         [sys.executable,
          os.path.join(HERE, "test_the_fan_names_the_stacks_it_kept.py")], 120,
         why="#53. v2848 made the revert INCREMENTAL — withdraw the most-displaced stack, "
             "re-measure, stop when the arrangement is no longer worse — and it landed with a "
             "defect one field over. `applied` is dense over the stacks that MOVED; `kept` and "
             "`dropped` hold indices into `stacks`. The partial path filtered one index space "
             "by the other's values. MEASURED 2026-09-11 by running the real _hrtFanFit over a "
             "stub DOM: moves reported [{x:100,dy:15}] — WITHDRAWN, carrying no transform — "
             "while the only transform on the page was x=500, named nowhere. Exactly inverted, "
             "and keptStacks:1 was right the whole time, which is what hid it: a correct count "
             "beside a wrong name. Four source-reading laws already guard this function and "
             "none could see it, because the code LOOKS right — the mistake is only in what it "
             "returns, so this law EXECUTES it. Also pins `moves` to one meaning on all three "
             "returns (what carries a transform NOW) after the reverted path published "
             "moves:N beside keptStacks:0, with `attempted` keeping the record of what was "
             "tried. Both branches have a fixture-still-reaches-it guard. Three tampers proven "
             "red. node absent => SKIP, which is UNMEASURED and not a pass.",
         skip_ok=()),
    Gate("test_the_shelf_joins_on_the_key_the_river_uses",
         [sys.executable,
          os.path.join(HERE, "test_the_shelf_joins_on_the_key_the_river_uses.py")], 60,
         why="#58. SHELF_RIVER is keyed by the reel id minus its reel_ prefix — a SESSION ID "
             "like s_1784984019250_95276 — and three sites looked it up with data-n, the "
             "card ORDINAL ('1','3','6'). The two key spaces never intersect, so every "
             "lookup returned undefined and EVERY reel rendered 'not stamped'. MEASURED on "
             "his live console 2026-09-11 in one page load: /api/river said 60 reels stamped, "
             "122 stamps, unparsed 0, while the grid drew ten station groups reading 0 reels "
             "and dumped all 530 cards into not-stamped. Joining on the session id: TRIAGE 2, "
             "STATION 21, PRINTER 5, JOIN 21, CAPTURE 34, ROUTED 24 — 107 stamped, and the "
             "timestamps he asked for appear. A comment above the map build SAID data-n and "
             "was wrong for the feature's whole life, which is why nobody looked again. Also "
             "note SHELF_RIVER={} is TRUTHY, so the could-not-be-read path never fired: a "
             "join matching nothing rendered exactly like a river with nothing stamped. The "
             "law does NOT hardcode the attribute — it reads whichever one the lookups use "
             "and demands the builder emit THAT, so a rename moves both halves or it goes "
             "red. Two tampers proven red.",
         skip_ok=()),
    Gate("test_the_shelf_shows_reels_before_analysis",
         [sys.executable,
          os.path.join(HERE, "test_the_shelf_shows_reels_before_analysis.py")], 60,
         why="#58. MEASURED on his live console at his real 1120x660: the shelf overlay is "
             "811x390 and the first card sat at y=2491 — 2101px BELOW the panel's own bottom "
             "edge — behind 1433px of header, pipeline board, highlights, controls and a "
             "14-day timeline, inside a 60561px scroll. 530 cards rendered and NOT ONE was on "
             "screen: the panel named 'your reels' showed no reels. Reordered so the list "
             "comes straight after the controls that filter it and every analytic block sits "
             "below — first card y=2491 -> 738, nothing removed, no id moved. Also trims the "
             "river badge: .shc-river never rendered until v2963 joined the card to the river, "
             "so its height had never been paid — the card jumped 332->376px inside a 390px "
             "panel, mostly an 80-char `why` wrapping to three lines. The reason moved to the "
             "badge title and the card came back to 318px. ⚠ STILL TRUE: panel 390px vs card "
             "318px with a 325px river strip above means NO card is fully visible at his "
             "window size — a structural choice, stated not closed. Two tampers proven red.",
         skip_ok=()),
    Gate("test_the_triage_says_what_produced_it",
         [sys.executable,
          os.path.join(HERE, "test_the_triage_says_what_produced_it.py")], 60,
         why="#69. MEASURED 2026-09-11 by verdict_provenance on the live tree: 44 stores, "
             "ANSWERS 6, PARTIAL 4, SILENT 16, REFERENCE 17, UNKNOWN 1. retro_triage.json was "
             "SILENT across 437 rows while being the store that decides EMPTY on the river. It "
             "carried gateVer — WHICH classifier — which is a different question from WHAT "
             "WROTE THIS. A verdict with no producer cannot be INVALIDATED: improve the "
             "classifier and nothing names the rows that predate the improvement, so a stale "
             "NO outlives every later pass looking exactly like a fresh one, and on this river "
             "a stale NO means footage is never read again. The stamp is ADDITIVE and the law "
             "pins BOTH halves: a new row names its producer with an epoch-ms clock, and an "
             "existing unstamped row is NOT back-filled — verdict_provenance's standing "
             "ruling, since stamping the past invents provenance nobody can attribute. Also "
             "pins that the stamp is swallowed, so a failure in the LABEL never costs the "
             "VERDICT. ⚠ the task's own headline '37 of 43' was STALE: it predates the "
             "census gaining a REFERENCE class, and the actionable set is the 16 SILENT. One "
             "tamper proven red.",
         skip_ok=()),
    Gate("test_the_console_series_say_what_wrote_them",
         [sys.executable,
          os.path.join(HERE, "test_the_console_series_say_what_wrote_them.py")], 60,
         why="#69. ui_faults.jsonl and disk_history.jsonl were both SILENT in the 2026-09-11 "
             "census (44 stores, SILENT 16). A row with no producer cannot be INVALIDATED when "
             "the writer improves: a fault logged by an old detector, or a disk reading taken "
             "under an older credibility rule, outlives every later pass looking exactly like "
             "a fresh one. A JSONL ROW IS ITS OWN LINE, so stamp_row here carries none of the "
             "fake-row hazard that forced the reel-keyed store to take it inside its rows "
             "(REG-972) — same helper, different shape, and the shape decides. Pins that the "
             "row keeps its OWN `at` (when the thing happened) distinct from the producer's "
             "clock, that the fault/reading itself is unharmed, and that one row is still one "
             "LINE — a stamped row split across lines would parse as two faults. ⚠ the first "
             "cut of this law asked for a writer named disk_history_record, which does not "
             "exist, and SKIPPED: two laws reporting OK while measuring nothing. The writer is "
             "disk_history_append, named rather than guessed. Two tampers proven red.",
         skip_ok=()),
    Gate("test_the_last_result_twins_name_their_writer",
         [sys.executable,
          os.path.join(HERE, "test_the_last_result_twins_name_their_writer.py")], 60,
         why="#69. chron_last_result.json and vault_last_result.json were both SILENT in the "
             "2026-09-11 census. They are DELIBERATE TWINS — _vault_result_save says it "
             "'mirrors _chron_result_save deliberately' — so they are stamped together; "
             "fixing one and leaving its declared mirror is this repo's most repeated shape. "
             "Both payloads are FLAT ({result, [proposal,] savedTs}) and every reader takes a "
             "NAMED field, so the stamp goes on the BLOB; a reel-keyed store needs it inside "
             "each row or it gains a phantom row (REG-972) — same helper, opposite right "
             "answer, decided by the shape, and this law pins the shape as well as the "
             "presence. Also pins that each twin tags its OWN store name (a shared tag would "
             "make both claim one origin AND collapse the two red-proof anchors into one), and "
             "that the stamp sits inside the try — both saves are best-effort because losing "
             "the cache must never take down the sweep that produced it, so a LABEL must never "
             "become the thing that loses it. Two tampers proven red.",
         skip_ok=()),
    Gate("test_the_page_is_not_its_own_console",
         [sys.executable,
          os.path.join(HERE, "test_the_page_is_not_its_own_console.py")], 300,
         why="THE JS SYNTAX GATE READ ITS OWN DOCUMENT'S PROSE AS A BROWSER ERROR, AND IT COST SIX "
             "PUBLICATIONS. Its browser path runs Chrome with --dump-dom AND --enable-logging="
             "stderr: stdout is the WHOLE rendered document, stderr is the console. It concatenated "
             "them and grepped for SyntaxError:, so any page that merely QUOTES an error message "
             "reports itself as broken. MEASURED 2026-09-09: bible.html contains exactly ONE match "
             "and it is a code COMMENT from v2824 explaining a bug — 'a NEWLINE throws SyntaxError: "
             "Invalid or unexpected token, taking the whole routing ledger down'. The file parses "
             "perfectly under node --check and under the browser once it stops reading the body. "
             "★ IT WAS INVISIBLE ON THE MACHINE THAT WRITES THE CODE: --dump-dom never answers over "
             "loopback on his Mac (v1490), so the NODE parser runs locally and a parser does not "
             "grep prose. Green where it is written, red where it ships — Publish failed on v2825, "
             "v2828, v2830, v2832, v2833 and v2835-v2837 while the page was fine. This file already "
             "carries the same shape one layer up (v1808: a timeout is not a syntax verdict). Now "
             "stdout and stderr are kept apart, the error scan and its context window both read the "
             "CONSOLE, and the crashed-renderer check asks the console rather than the page. Three "
             "tampers proven red.",
         skip_ok=()),
    Gate("test_the_slow_request_is_kept_whole",
         [sys.executable,
          os.path.join(HERE, "test_the_slow_request_is_kept_whole.py")], 90,
         why="#28. /api/status once took 52 SECONDS while ON AIR was recording, against ~24ms idle, "
             "and two things stopped that ever being answerable. (1) worstSinceBoot is a request "
             "that NEVER HAPPENED — per-section maxima from DIFFERENT calls, summing to 3,031ms on "
             "his console while the last request took 244ms, so a reader chasing the event against "
             "it is chasing a composite. (2) Every slow request was overwritten by the next "
             "ordinary one: `last` holds only the most recent, and his console had ALREADY logged "
             "6 requests over the 750ms bar with not one breakdown surviving. The event had "
             "happened repeatedly and left no record. Now the slowest request is kept ENTIRE — "
             "sections, unattributed remainder, slowest component — persisted across a restart and "
             "stamped with capture/mode/agent read from the SAME payload the sections were measured "
             "in, because a breakdown that cannot say whether the capture was running answers half "
             "the question. FIRST CATCH on wiring: 4,449.3ms with vaultAutoread at 3,426.8ms (77%) "
             "and capture=False — so a multi-second status request happens with NO session at all, "
             "which narrows #28 before he ever presses record. Also held: only a STRICTLY slower "
             "request replaces the record (the defect that lost the first six), only above the bar "
             "(or a 1Hz poll writes a file per second), an unreadable record is None and not a fast "
             "console, and saving never raises into the request path. Four tampers proven red.",
         skip_ok=()),
    Gate("test_the_status_breakdown_covers_what_it_bills",
         [sys.executable,
          os.path.join(HERE, "test_the_status_breakdown_covers_what_it_bills.py")], 120,
         why="#28. MEASURED on his live console 2026-09-09 (947 requests, 6 slow): totalMs 36.4, "
             "sections sum 2.7, unattributedMs 33.7 — the breakdown billed 7% of the request it "
             "was measuring, because 13 producers were wrapped in _t() and 31 were not. #28's own "
             "next step was 'reproduce with a live recording session and read the breakdown', and "
             "that reproduction would have returned 96% UNKNOWN: every instrumented section at its "
             "worst-since-boot sums to 2,192 ms against a 52,360 ms event. After wrapping 16 more: "
             "attributed 1104.0 of 1141.5 ms (97%), and the top cost was one of the invisible ones "
             "— fleetOrigin at 619.3 ms, 54% of the request, with screenRecOk at 79.8 ms behind "
             "it. ★ The law is AST, not text: every producer call inside status_payload is either "
             "inside a _t(...) node or named in EXEMPT with a reason, so a producer added later is "
             "RED until somebody decides which it is. Also held: no duplicate section name (_t "
             "ACCUMULATES, so two producers would merge into one unfindable line), no ghost "
             "exemptions, the gap published UNCLAMPED, and UNKNOWN-not-zero before the first "
             "completed request. Three tampers proven red.",
         skip_ok=()),
    Gate("test_no_technique_is_lost_when_mini_goes",
         [sys.executable,
          os.path.join(HERE, "test_no_technique_is_lost_when_mini_goes.py")], 120,
         why="#44 — his 2026-09-08 order: harness every technique BEFORE ON AIR and MINI unify, "
             "because removing MINI first would drop read-paths and the loss would surface as "
             "reels that stop yielding names with nothing saying why. unify_census.py DERIVES the "
             "roster every run — templates from reel_templates.ROUTES, scenarios from "
             "extract_gap's own constants, read-paths from an AST call-graph over control_app — "
             "so a technique added without teaching ON AIR about it turns up without anyone "
             "remembering to look. MEASURED 2026-09-09: 19 techniques, 4 reproduced, 8 MINI-only "
             "gaps, 7 unasked; the stream stamp `door` covers 25 of 3,926 journal rows (0.6%) and "
             "19 of the 23 ON AIR rows are session_end carrying 2 names, so a per-scenario tally "
             "cannot tell 'never reaches it' from 'has barely run'. ★ UNKNOWN BLOCKS AS HARD AS A "
             "KNOWN GAP, and a census that could not run REFUSES rather than permits — an "
             "instrument failure must never become permission. Four tampers proven red. MINI AUTO "
             "(hover) is deliberately out of scope: his ruling, #17/#41.",
         skip_ok=()),
    Gate("test_a_reels_whole_life_is_one_work_list",
         [sys.executable,
          os.path.join(HERE, "test_a_reels_whole_life_is_one_work_list.py")], 120,
         why="#36's second half. v2817 published the closure ledger BESIDE the walk; the station "
             "was still unassignable and the TOMBSTONE lane still could not draw a single reel "
             "that had actually closed out. reel_router.roster() now assigns TOMBSTONE and spans "
             "a reel's whole life — MEASURED on his stores 2026-09-09: 41 on disk + 428 closed = "
             "469 lifetimes, so the per-reel surfaces covered 8.7% and 91.3% were visible only as "
             "one aggregate sentence attached to rows about OTHER reels. ★ route()['shelf'] is "
             "held UNMOVED by AST — if the closure rows ever reach `reels`, 41 becomes 469 on a "
             "figure he acts on with nothing on screen saying why. Also held: exactly ONE reader "
             "of the ledger (two readers is how three walks came to agree at 41 by luck); a reel "
             "in BOTH records counted ONCE and named as a contradiction under either of the "
             "ledger's two key conventions; an unreadable ledger UNKNOWN and never 0 at the "
             "roster, the lane, the endpoint and the renderer; the drawn sample never passing "
             "for the total. Three tampers proven red.",
         skip_ok=()),
    Gate("test_the_deleter_will_not_destroy_a_receipt",
         [sys.executable,
          os.path.join(HERE, "test_the_deleter_will_not_destroy_a_receipt.py")], 90,
         why="frame_ref has stated the receipt rule since v2364 — a frame cited by a row that "
             "NAMED an item is PROOF and may not be deleted while the claim stands — and "
             "AST-confirmed, nothing in production ever called it: the only callers of "
             "cited_frames/prunable/Index were frame_ref itself and one test, and reel_retention "
             "did not even import it. Meanwhile apply_plan() rmtree'd the WHOLE reel directory on "
             "a coarse reel-level vault signal. MEASURED on his tree 2026-09-09: of 10,318 "
             "citations across uniques+sets, 739 cited frames already resolve to nothing on disk. "
             "★ AND THE ADAPTER IS THE WHOLE FIX: cited_frames() decides a row is proof via "
             "items/names, while chron_evidence stores the item name as the KEY — wire the guard "
             "straight onto that and named comes back EMPTY, so the deleter keeps deleting proof "
             "while carrying a protection that reads correct. Both halves are proven red.",
         skip_ok=()),
    Gate("test_a_cached_absence_is_not_an_absence",
         [sys.executable,
          # ⚠⚠ v3447 — RAISED 120 -> 300 BECAUSE 120 WAS A COIN FLIP. Measured by the #189
          # parallelisation work: this gate's CLEAN run is ~110-130s against a 120s registered
          # timeout, so its proofs were UNPROVABLE-by-timeout at random — in the SERIAL control
          # too, not only under parallel proving. It was the ONE proof that flipped
          # (PROVEN -> UNPROVABLE) in the A/B, and the flip was the margin, not the concurrency:
          # 2 lanes flipped it identically, and only 1 lane avoided it, which buys no speedup.
          # A gate whose verdict depends on 10 seconds of headroom is measuring the machine.
          # [[feedback-threshold-above-the-ceiling]] inverted — a ceiling BELOW the real load.
          os.path.join(HERE, "test_a_cached_absence_is_not_an_absence.py")], 300,
         why="Two sentences from the fleet panel minutes apart — 'the fleet is unreachable' and "
             "'Dean has not reported which set pieces it holds yet' — with the live beacon in the "
             "same minute showing Dean ONLINE carrying masks sets=76ch uniques=118ch. Three "
             "defects. (1) fleet_presence caches 60s and on a timeout wrote the ERROR over the "
             "cached roster, so one 6s timeout destroyed data the card had already rendered; "
             "strictly worse than no cache, because without it the modal would have re-tried. "
             "(2) the cross-reference refused on any fetch failure, treating a STALE roster as an "
             "unreachable fleet while the card beside it showed that machine's real numbers. "
             "(3) 'he has not reported' was concluded from that cache — a claim about ANOTHER "
             "machine, the one kind this console cannot check by looking inward — so an absence "
             "in a cached record was reported as an absence in the world. Serve the last good "
             "roster WITH ITS AGE, and make a miss earn one authoritative re-read before the "
             "sentence may be said.",
         skip_ok=()),
    Gate("test_the_sweep_knows_whose_world_it_is",
         [sys.executable,
          os.path.join(HERE, "test_the_sweep_knows_whose_world_it_is.py")], 90,
         why="The routine said: after any render/CDP session, rm -f tv/.board_identity.json before "
             "pushing, because a CDP load can leave a GUEST record and five TestV2072 assertions "
             "then fail with a drift reason naming none of it. Real scar, right removal FOR THAT "
             "RECORD. MEASURED 2026-09-09 on the record actually present: firstSeen 01:04:20, his "
             "console started 01:04:29 — NINE SECONDS LATER — lastSeen 01:25:14 with seenCount 28 "
             "and still being written, owner=True pfx='' previous=None, i.e. "
             "board_identity_drift() == ok. That was his console's LIVE world record. Removing it "
             "degrades a healthy ok into unknown, which that function's own docstring calls "
             "deliberate and NOT ok, and the next write starts a fresh install id with "
             "previous=None — the exact shape that makes a real board render as a stranger's "
             "world at 0/403. So the rule is the record's STATE, not the ritual: guest and "
             "drifted are swept (backed up first), a healthy owner claim is KEPT, an absent one "
             "is UNKNOWN rather than a clean sweep, an unparseable one is never deleted, and the "
             "whole thing REFUSES while his console is running, because a live writer owns that "
             "file and sweeping under it leaves a record that reads as neither state.",
         skip_ok=()),
    Gate("test_the_status_breakdown_names_its_own_blind_spot",
         [sys.executable,
          os.path.join(HERE, "test_the_status_breakdown_names_its_own_blind_spot.py")], 90,
         why="/api/status answers in 0.024s idle and took ~52s under a recording session. v2320 "
             "already fought this and left the ruling in the source: a PAYLOAD-level cache was "
             "tried at v2319 and torn out, because seven guards set state and read status back "
             "expecting it to be true NOW. Its other half was never acted on — 'cache the "
             "expensive COMPONENTS' — and nothing here could name WHICH component, because "
             "nothing had ever timed them. The trap is in how: status_payload is a 243-line dict "
             "and only thirteen producers are wrapped, so a breakdown built from those alone "
             "always accounts for 100% of itself and therefore always blames an instrumented "
             "name, including when the cost sits somewhere nobody wrapped. So the total is "
             "measured separately and the gap ships as unattributedMs, UNCLAMPED — a negative gap "
             "means the components double-counted, and an instrument that hides its own breakage "
             "is the thing this repo keeps rediscovering.",
         skip_ok=()),
    Gate("test_the_hover_reads_the_panel_the_pixels_show",
         [sys.executable, os.path.join(HERE, "test_the_hover_reads_the_panel_the_pixels_show.py")], 90,
         why="THE CONTAINER WAS ACCEPTED AND DROPPED, AND THAT IS A WRONG-PANEL BUG. "
             "_mini_cells_from_live_frame(container) used its argument exactly ONCE — in its own "
             "signature. vault_corpus's lattice/occupancy readers take NO container and find a "
             "grid wherever one is, while hover_mode.start maps those cells through "
             "slot_identity.panel_box_for(container). The panels are 1,510px apart: stash at "
             "x=281 y=381, inventory at x=1791 y=984. So an INVENTORY frame with the button "
             "hardcoded to 'stash' produced REAL cells read off the inventory and hovered them at "
             "STASH coordinates — the pointer sweeping empty screen while `moved` counted up and "
             "every number said it worked. ★ The lattice itself answers it: GRIDS holds stash "
             "10x10, inventory 10x4, cube 3x4, three distinct shapes, so the reader infers which "
             "panel it read and RETURNS it, the caller hovers THAT one, and a shape matching none "
             "is REFUSED rather than assigned to whatever the button said. The law also pins that "
             "the grids stay distinguishable (if two ever share a shape, inference becomes "
             "guessing) and that every return path carries the container, including the refusals.",
         skip_ok=()),
    Gate("test_a_lattice_refusal_is_a_reason_not_a_crash",
         [sys.executable, os.path.join(HERE, "test_a_lattice_refusal_is_a_reason_not_a_crash.py")], 150,
         why="THE GRID READER RAISED WHERE EVERY OTHER PATH RETURNS A REASON. He was in-game saying "
             "MINI AUTO \"does nothing\"; handed a real live frame, inventory_lattice threw in 0.4s "
             "— `sr, rp, _rph, rows = _fit(...)` with _fit returning None, unpacked blind at BOTH "
             "call sites. Every other refusal there returns {ok: False, why}, which is the "
             "function's stated contract; this one path threw, so the caller could only say "
             "\"reading the frame raised TypeError\" and the real finding — the ridge fit saw no "
             "grid at all — never reached him. AN EXCEPTION IS NOT A REASON, and he had already "
             "been told \"nothing happens\" by three surfaces. ⚠ The law EXERCISES the path with a "
             "flat frame rather than grepping for the guard, and asserts the fixture is big enough "
             "to reach the fit (a small one would trip the SIZE refusal and go green having tested "
             "nothing).",
         skip_ok=()),
    Gate("test_the_banner_may_not_claim_what_it_did_not_measure",
         [sys.executable, os.path.join(HERE, "test_the_banner_may_not_claim_what_it_did_not_measure.py")], 90,
         why="THE STARTUP BANNER SAID \"OCR OFF\" AND \"ocr lane: ON\" FIVE LINES APART. The first "
             "was a hardcoded string inside `if LIGHT_MODE:`; the second is measured from "
             "_OCR.available(). OCR_ENABLED reads TV_OCR and has NOTHING to do with LIGHT mode, so "
             "the literal was simply false — and while he was reporting \"its not reading "
             "anything\" I believed it and chased the wrong thing. `_film_on` was computed on the "
             "line directly above and thrown away. ⚠⚠ THIS LAW TOOK TWO INSTRUMENT FIXES TO BITE: "
             "the first cut pooled prints from EVERY `if LIGHT_MODE:` in the file, and the second "
             "still walked the whole ast.If — which INCLUDES the orelse — so it counted the ELSE "
             "branch's four interpolations and a banner replaced by a bare string stayed GREEN "
             "twice. It now walks n.body only. All three arms proven red.",
         skip_ok=()),
    Gate("test_the_live_frame_cannot_be_pulled_mid_read",
         [sys.executable, os.path.join(HERE, "test_the_live_frame_cannot_be_pulled_mid_read.py")], 90,
         why="MINI AUTO STAT-ED THE LIVE FRAME IN ONE PLACE AND OPENED IT IN ANOTHER, AND THE "
             "CAPTURE MOVES IT BETWEEN THE TWO. `_mini_cells_from_live_frame` picked the newest "
             "EXISTING label with os.path.isfile and handed the PATH to vault_corpus, which opens "
             "it later; the capture promotes eye.jpg by REPLACING it, so the open raced the "
             "promote and returned [Errno 2]. That is why MINI AUTO alternated between \"the "
             "newest frame is Ns old\" and \"the grid could not be located\" — two faces of ONE "
             "missing file, decided by whether a promote was in flight. ⛔ READING THE BYTES WAS "
             "NOT ENOUGH AND I NEARLY SHIPPED THAT: both readers OPEN what they are given and "
             "neither takes bytes (checked), so passing the path anyway would have been plumbing "
             "with no tap. The bytes go to a private snapshot and the SNAPSHOT travels. ⚠ NOT a "
             "wider age bound — the file's ABSENCE was the event, never its age. ⚠ The fix also "
             "hid a NameError (tempfile is NOT module-level in control_app; my ast.walk check saw "
             "it nested inside another function and wrongly said it was) which only surfaced "
             "because this law EXERCISES the path rather than reading it.",
         skip_ok=()),
    Gate("test_a_button_speaks_where_it_stands",
         [sys.executable, os.path.join(HERE, "test_a_button_speaks_where_it_stands.py")], 90,
         why="HE PRESSED MINI AUTO AND SAID \"nothing happens\", AND THE CONSOLE HAD ANSWERED HIM "
             "PERFECTLY — into a room he was not in. Driving the endpoint got the reason in one "
             "call: \"the newest frame is 3124s old - MINI will not hover off a stale screen\". "
             "The handler writes to #eagle-out, and v2381 moved the CARD out of TOOLS to sit beside "
             "MINI while the BOX stayed behind — its own comment says \"same id, same handler, same "
             "state readout; only the seat moved\". The id was the same; the readout was left in "
             "the other room. MEASURED: every other button in this console sits 2-46 lines from "
             "the box it writes into; btn-miniauto sat **275**. Same fix as v2446's shelf door and "
             "for its reason — \"a message only visible when the thing works is not an error "
             "message\" — a toast outside the panels, with the box KEEPING its durable copy. ⚠ The "
             "law is general: any handler answering into a box further than 80 lines away must also "
             "speak, or the next card that moves seat repeats this exactly. ⚠⚠ AND ITS FIRST CUT "
             "WAS WRONG — it matched the sentence anywhere in the handler, so the #eagle-out write "
             "satisfied it and a toast stripped of `why` stayed GREEN. It now parses the toast CALL. "
             "Both arms proven red.",
         skip_ok=()),
    Gate("test_a_source_window_must_reach_its_subject",
         [sys.executable, os.path.join(HERE, "test_a_source_window_must_reach_its_subject.py")], 120,
         why="A FIXED-SIZE SOURCE WINDOW MEASURES MY GUESS, NOT THE FILE. test_the_river_has_a_mouth "
             "cut SRC[i:i+9000] from the /api/river route and the success payload had grown to "
             "**+9145** — 145 characters past the window — so the helper returned None, one law "
             "reported the route was GONE and two more ERRORED, about a route that was perfectly "
             "fine. Nothing had broken except the guard's REACH, which shrank a little more every "
             "time somebody documented that handler. ⚠⚠ AND THAT WAS THE LUCKY DIRECTION: a window "
             "that runs short under assertNotIn/assertFalse simply PASSES, reporting an absence it "
             "never looked for — a zero with no denominator and no author. MEASURED BY AST, never "
             "by grep: 68 windows across 23 files, and **25 of them sit under a negative "
             "assertion**. The first count of this was a grep and said 80, because it matched the "
             "pattern inside the comments explaining the defect — over-counted by 12, a law about "
             "misreading source measured by misreading source. Two ratchets, because 68 sites "
             "cannot be rewritten in one pass and a law that fails on all of them is one nobody "
             "can ship: the total and the silent subset may FALL, never RISE.",
         skip_ok=()),
    Gate("test_atomic_write_keeps_the_mode",
         [sys.executable, os.path.join(HERE, "test_atomic_write_keeps_the_mode.py")], 90,
         why="⚠⚠ THE COMMIT THAT ADDED A GATE TURNED EVERY GATE OFF. `atomic_write` writes a temp "
             "file and `os.replace`s it into place — and the temp file is born 0644, so every "
             "executable it edited came out NON-EXECUTABLE. Measured: hooks/pre-push was 100755 at "
             "v2793 and 100644 at v2794, git printed one line — \"the hook was ignored because "
             "it is not set as executable\" — and v2794 went to origin with NO gates at all: no "
             "test_control, no render, no smoke, no second eye, not even the blueprint check that "
             "commit existed to add. It would have stayed disabled for every future push, silently, "
             "because a hook that is not executable does not fail — it is simply never run, and a "
             "SKIP IS NOT A PASS. This gate holds both halves: atomic_write preserves the mode (and "
             "still gives a brand-new file the default), and hooks/pre-push is executable BOTH on "
             "disk and in the git index — the index mode is what a fresh clone inherits, the disk "
             "mode is what arms the machine actually pushing."),
    Gate("test_the_shelf_lands_on_the_river",
         [sys.executable, os.path.join(HERE, "test_the_shelf_lands_on_the_river.py")], 120,
         why="THE RIVER SECTIONS WERE BUILT AND HE COULD ONLY REACH THEM THROUGH A DROPDOWN. His "
             "words: \"all the reels on the bottom rendering need to be inside those same "
             "sections.. not outside of them\". v2746 had ALREADY built exactly that — cards "
             "grouped under river sections, in the backend's order, empty stations printed dimmed "
             "— from the FIRST time he asked. It was gated behind SHELF_S === 'river', a sort "
             "mode, and the default was 'newest', so every open gave him a flat list while the "
             "river strip above it described a flow the cards did not show. A feature behind a "
             "control he has to find is a feature he does not have. ⚠⚠ AND FLIPPING THE DEFAULT "
             "ALONE WOULD HAVE BROKEN IT: the river-unknown branch printed \"not read yet\" and "
             "RETURNED, and the only caller of _shRiverLoad was the sort menu's own change "
             "handler — so with river as the default and nobody picking it, SHELF_RIVER stays null "
             "forever and he lands on that sentence on every open. The branch now asks, ONCE "
             "(_shSort runs on every render, filter and pin). ⛔ Newest is still one click away, "
             "the section order still comes from the backend's stations rather than a second list, "
             "and an empty station is still printed rather than vanishing.",
         ),
    Gate("test_the_theatre_open_chain_cannot_hang",
         [sys.executable, os.path.join(HERE, "test_the_theatre_open_chain_cannot_hang.py")], 120,
         why="v2228 BOUNDED ONE FETCH AND ITS SIBLING ELEVEN LINES AWAY WAS NEVER SWEPT. thOpen "
             "awaits thLoadSession, whose `/api/session?n=` had NO AbortController, NO timeout and "
             "NO catch — while `/api/sessions` right above it has carried all three since v2228, "
             "whose own comment names the failure: \"when the auto-relaunch replaces the server "
             "process mid-fetch, the promise never settles ... and the black stays up\". And this "
             "is the MORE expensive route: /api/session defaults to pack=debug, and this repo "
             "measured the archive siblings at ~4s alone and 41.6s under contention — so it gets "
             "12s, not the lighter sibling's 8s, or a merely slow read would be aborted. ⚠⚠ THIS "
             "IS NOT WHAT HE WAS SEEING: a different model family put live eyes on his console and "
             "THE SHELF opened, painted and stayed open past 15s — REG-708 as written is REFUTED "
             "and this is a latent hazard fixed on its merits. ⚠ THE LAW IS DELIBERATELY NARROW: "
             "measured 71 awaited fetches in this file, 4 bounded. Bounding all 67 others would be "
             "a sweeping change to a hot path with no measurement behind it, and a law failing on "
             "67 sites is furniture on day one. What makes THIS chain different is that a hang "
             "leaves a BLACK STAGE with no account of it; every other call is a click-driven panel "
             "whose failure is local and visible.",
         ),
    Gate("test_no_resolver_falls_back_to_his_live_world",
         [sys.executable, os.path.join(HERE, "test_no_resolver_falls_back_to_his_live_world.py")],
         180,
         why="v2783 FIXED ONE RESOLVER THAT FELL BACK TO HIS LIVE DIRECTORY AND FOUR MORE COPIES "
             "WERE STILL RUNNING. A parallel read-only sweep found them. The worst was "
             "control_app._log_root, a VERBATIM unfixed copy of the corrected function seventy "
             "lines above it, binding LOG_PATH — which is APPENDED to on every line of console "
             "output and TRUNCATED at 2 MB. Its own docstring already records that harm happening "
             "once from a milder cause. chronicle_routes and frame_authority both WRITE into the "
             "resolved root, and frame_authority's v2778 comment had already MEASURED those files "
             "left dirty in his live tv/ — the comment was written, the arm was not fixed. ⛔ THE "
             "LAW IS A CENSUS, NOT A LIST OF FOUR: naming them would be green the day a fifth "
             "appears, and a fifth is exactly how four appeared, one copy at a time. ⚠⚠ THE CODE "
             "TAUGHT THE DISCRIMINATOR: the first cut flagged shadow_ledger and retro_gate, and "
             "BOTH ARE CORRECT — they catch ImportError ONLY, and say why: \"if the root rule is "
             "broken that must surface, not resolve to his tree\". A blanket except Exception is "
             "the defect because it also swallows a runtime failure OF THE RULE. So the three were "
             "NARROWED to the blessed template rather than having the TV_HIST arm copied a fourth "
             "time. One site is exempt WITH A REASON: _chron_hunt_mem_path already tried walking "
             "TV_HIST and it was wrong. AST-parsed, never grepped — every fix quotes the defective "
             "arm to explain it.",
         ),
    Gate("test_the_set_pieces_carry_a_real_qlvl",
         [sys.executable, os.path.join(HERE, "test_the_set_pieces_carry_a_real_qlvl.py")], 120,
         why="1,444 OF 1,598 SET-TIER DROP RECORDS CARRIED qlvl 0, AND A ZERO ON A MISSING ROW IS A "
             "NUMBER HE FARMS BY — it reads as \"any monster level can drop this\". The qlvl check "
             "is one of the two filters that decide whether an item can drop at all (monster mlvl "
             ">= item qlvl), so a wrong zero sends him to the wrong zone. Filled from the game's "
             "OWN table, extracted from his local D2R CASC store: data/global/excel/setitems.txt, "
             "column `lvl`, joined on column `index` (the piece name) rather than *ItemName (the "
             "base type). CROSS-CHECKED against excel/base/setitems.txt — 132 pieces in both, ZERO "
             "disagreements, which is the second witness his no-fabrication rule requires. ⛔ THE "
             "GAME DATA IS BLIZZARD'S AND THIS REPO IS PUBLIC, so it is deliberately absent and "
             "these laws pin the SHAPE instead: measured across all 35 sets, every piece of a set "
             "carries the same qlvl with zero exceptions, and one piece appears in many drop "
             "records so every record naming it must agree. A partial fill or a bad join breaks "
             "that instantly with no Blizzard bytes present. ⚠ ELEVEN pieces stay 0 because they "
             "have NO row under any spelling, and several are probably naming errors in the bible "
             "(the table says Tal Rasha's Fire-Spun Cloth where the bible says Fine-Spun) — a "
             "near-spelling is not a trace and guessing one is the fabrication the rule forbids.",
         ),
    Gate("test_the_pixels_earn_the_right_to_act",
         [sys.executable, os.path.join(HERE, "test_the_pixels_earn_the_right_to_act.py")], 180,
         why="HIS RULING: \"if they are hardened and tested and prove themselves to work is this a "
             "good place for a hardening and wilson to connect to the heart of the console "
             "specifically #34\". The pixel witness REPORTS and POST-GRADES but may not TRIGGER — "
             "the rescue fires on a beat read from the PAGE, and a blank page can still beat, which "
             "is exactly the state he was looking at with a black window and the hover art still "
             "painting. `console.pixel_rescue` is now declared in self_arming at the DELETER'S BAR "
             "(0.839 / kinds 1.8), because a wrong BLANK does not lose footage — it replaces the "
             "window he is looking at. ⛔ IT SHIPS LOCKED: may() is False, the loop falls through to "
             "the same continue, behaviour byte-for-byte unchanged, and it opens ITSELF only after "
             "three independent families have attacked it. 16/16 sabotages refused is wilson 0.806 "
             "against 0.839 — a PERFECT score from one family still refuses. ⚠ ONE LAW IS ABOUT MY "
             "OWN ATTACKER: its boundary attacks first read `_m(0.50, PW.INK_P99_MAX, 0.001)`, "
             "derived from the bar they exist to pin, so widening that bar moved the input with it "
             "and all 16 attacks passed while his HEALTHY console (p99 177) read BLANK. ⚠ And the "
             "first run of that sabotage lied: cp restored the source while python read CACHED "
             "BYTECODE from ~/Library/Caches/com.apple.python — the tree said 80 and the "
             "interpreter loaded 200.",
         ),
    Gate("test_the_pixel_witness_looks_at_his_console",
         [sys.executable, os.path.join(HERE, "test_the_pixel_witness_looks_at_his_console.py")], 120,
         why="THE PIXEL WITNESS LOOKED AT ITSELF AND SAID UNKNOWN FOREVER. He sent a screenshot of "
             "a BLACK TV DIABLO window; running the one hand-run instrument for exactly that "
             "question answered `UNKNOWN - pid 60574 owns no on-screen window`, and pid 60574 did "
             "not exist. The line was `pid = int(next((a for a in argv if a.isdigit()), "
             "os.getpid()))` - with no argument it looked at the interpreter running the witness, "
             "which owns no window, so the answer was UNKNOWN every time by construction. Its own "
             "usage line says `look at his console once` and it had never once done so. ⚠ THE PORT "
             "HAS MORE THAN ONE OWNER: :17772 was held by the console AND by a WebKit XPC renderer "
             "service with no window, so taking the first pid lsof prints reproduces the bug with a "
             "different wrong number - console_pid() takes the owner that HAS a window. ⚠ THE LAWS "
             "PARSE, THEY DO NOT GREP: the fix's comment names os.getpid() to explain it, and a "
             "substring law would go red on the explanation.",
         ),
    Gate("test_the_panel_prints_what_the_row_measured",
         [sys.executable, os.path.join(HERE, "test_the_panel_prints_what_the_row_measured.py")], 120,
         why="THE PANEL PRINTED \"read once\" OVER A ROW THAT SAYS \"only 0 independent "
             "witnesses\". The inbox row already carries the count AND the witness kind, measured "
             "by the sweep — his eight pending rows say `only 1 independent witness (cross-frame) "
             "- needs 2`, and Gheed's Wager says ZERO. The panel discarded all of it for a fixed "
             "sentence that is FALSE on that row and that throws away cross-reel vs cross-frame, "
             "which is the whole question of whether a second sighting is independent. ⚠ THE "
             "ENGINE'S OWN COMMENT PREDICTED IT: `code stays null by default ON PURPOSE. Callers "
             "read code || why, so a default code would override the specific why of every branch "
             "that does not set one.` roster-unconfirmed is not a default — it is a real code — "
             "and it outranked triageWhy anyway, in a caller three thousand lines from where that "
             "rule was written. ⛔ SCOPED: only roster-unconfirmed defers; misread-of and "
             "reads-as-two are statements about the NAME and must keep winning. The decision is "
             "SLICED FROM bible.html AND RUN IN NODE, never grepped.",
         ),
    Gate("test_a_cold_review_must_carry_the_code",
         [sys.executable, os.path.join(HERE, "test_a_cold_review_must_carry_the_code.py")], 120,
         why="THREE \"COLD CODE REVIEWS\" WERE RECORDED AS SECOND-EYE LOOKS AND THE CODE WAS NEVER "
             "SENT. The prompts were assembled as plain strings, so the code fence went out holding "
             "the un-evaluated expression that was supposed to read the file. The other family got a "
             "fence full of source-expression plus accurate prose context, and answered confidently "
             "and specifically about code it had never seen; a sentinel probe made it say \"NO CODE "
             "RECEIVED\". ⛔ NOTHING IN THE LANE COULD CATCH IT: every field the ledger stored "
             "described the ANSWER — model, family, verdict, findings, answer head, even a hash of "
             "the bytes I SAID were photographed — and not one described the QUESTION. `record()` "
             "now takes the prompt, and a fence carrying an un-evaluated file read forces the row to "
             "an EMPTY SEAT instead of a look. ⚠ It reads the FENCES ONLY, never the whole prompt, "
             "or the explanation of the defect would trip the guard against it. ⚠ AND IT WAS NOT "
             "ALL OF THEM — v2775's prompt carried its diff intact and its finding was real; the "
             "first blanket claim that every review had gone out empty was itself unmeasured.",
         ),
    Gate("test_the_console_notices_its_own_runaway",
         [sys.executable, os.path.join(HERE, "test_the_console_notices_its_own_runaway.py")], 120,
         why="REG-699 — HIS CONSOLE BURNED A CORE FOR TWO HOURS AND NOTHING NOTICED BUT HIM. The "
             "cause is STILL unknown; what this fixes is that he was the detector. A watchdog now "
             "times ITSELF (never polls its own API — that is the poll-slower-than-its-interval "
             "trap) and dumps every thread's Python stack on detection, which is the one fact "
             "nobody had. ⚠ THE FIRST DESIGN WAS REFUTED BY ITS OWN PROOF RUN: `late AND busy` "
             "detected NOTHING under 12 burner threads (cpu 1.01, tick 1.1s) because pure-Python "
             "loops release the GIL every ~5ms. That failure reconciled his measurements — `/` fast, "
             "`/api/status` dead, 108% CPU — which only fit ONE shape: a thread SPINNING WHILE "
             "HOLDING the lock the status path needs. So the real signal is lock-refusal growth. "
             "Proven end to end: idle 0 detections, a sweep at a full core 0 detections, his shape "
             "7 detections, and the dump named `spin_holding_lock`.",
         ),
    Gate("test_the_status_poll_never_waits_on_a_spawn",
         [sys.executable, os.path.join(HERE, "test_the_status_poll_never_waits_on_a_spawn.py")], 120,
         why="ON AIR SPUN \"loading\" WHILE THE RECORDING WAS ALREADY RUNNING. `start_agent` holds "
             "`_lock` across a 166-line block containing subprocess.Popen(), time.sleep(0.2) and "
             "three open() calls — and four functions on the /api/status path needed that SAME lock "
             "for one `.poll()` each. Every status poll therefore queued behind the spawn, so the "
             "button stayed \"loading\" and OFF AIR stayed greyed while the capture ran perfectly. "
             "The readers are now bounded (0.25s, then answer from the lock-free pid cache), proven "
             "by holding `_lock` for 3s and measuring — the sabotage that reverts them blocks for "
             "3.005s. ⚠ THIS DOES NOT EXPLAIN the 30-52s sweep-time wedge with no agent running; a "
             "cross-family review answered UNKNOWN on that and the published `lockWait.blocked` "
             "counter (with its `reads` denominator) is the instrument that will settle it from his "
             "own machine.",
         ),
    Gate("test_the_rescue_has_a_top_rung",
         [sys.executable, os.path.join(HERE, "test_the_rescue_has_a_top_rung.py")], 120,
         why="WHEN THE SELF-RESCUE FAILED, KONYO WAS THE FALLBACK. Over 196 hours his fault journal "
             "shows 73 blank-pixel sightings, 111 rescues, and 4 x "
             "`console-rescue-did-not-restore-painting` — after which NOTHING stronger happened and "
             "he had to notice the dead window himself, twice on 2026-09-08. The loop's refusal to "
             "retry the RELOAD is correct and stands; a relaunch is a DIFFERENT act, and it restored "
             "his window twice in ~3s where reloads had failed. This gate protects the REFUSALS far "
             "more than the act: never while a reel is recording (that costs him footage he cannot "
             "get back), never on one failure, and at most once per 15 minutes so a persistent fault "
             "can never become a restart loop. It drives `_rescue_escalation_decision` directly and "
             "checks the loop's call to it by PARSING — a substring law would be satisfied by the "
             "comment explaining the rule, which is how a defined-and-uncalled function passed green "
             "six times in one session.",
         ),
    Gate("test_the_throw_bar_stays_stricter",
         [sys.executable, os.path.join(HERE, "test_the_throw_bar_stays_stricter.py")], 120,
         why="THE `locked lanes` DOCTOR ROW WAS CRYING WOLF ABOUT HIS OWN RULING. It required the "
             "throw bar to be strictly above the keep bar ON WITNESSES and reported MISSING when he "
             "levelled them on 2026-09-07 (\"make it two also.. its fine.. i will review what i "
             "throw regardless\"). The danger is real and unchanged — there is no un-throw in "
             "Diablo — but the protection is not carried by the witness count: throwing still "
             "demands STRICTLY more confidence (0.85 vs 0.55), and the throw bar counts independent "
             "RECORDINGS where the keep bar counts LOOKS. The invariant is now 'strictly above on "
             "AT LEAST ONE axis, never below on either', so a real inversion and the degenerate "
             "identical-on-both case both still go red. ⛔ The fix was to the ROW, never to the "
             "BARS — moving a bar to make a check green is repairing the measurement to fit the "
             "data, on the one gate in this tree that owns an irreversible act. A row that reports "
             "his deliberate choice as a fault is one he learns to scroll past, and then it is not "
             "believed on the day something IS wrong.",
         ),
    Gate("test_the_river_has_a_driver",
         [sys.executable, os.path.join(HERE, "test_the_river_has_a_driver.py")], 180,
         why="THE RIVER HAD AN OUTLET AND NOTHING DRIVING IT. Found by the post-ship review of "
             "v2764: reel_route_lane.apply() was referenced by NOTHING but its own CLI and its own "
             "test, so the six reels closed out that day were moved BY HAND and the `river outlet` "
             "row would have sat on MISSING for ever the moment a new reel reached EMPTY. The "
             "diagnosis flowed; the river did not. The triage tick now drives the lane. ⚠⚠ ORDER "
             "IS CORRECTNESS: the lane ACTS first and the walk OBSERVES after, because reversed "
             "the walk would stamp the station the lane is about to change and every tick would "
             "cost a transition row in an append-only journal. ⛔ It rides the TRIAGE tick, never "
             "the retention pass, and writes ROUTED only — TOMBSTONE stays with the deleter behind "
             "the arming lock.",
         ),
    Gate("test_a_manual_declaration_can_be_found",
         [sys.executable, os.path.join(HERE, "test_a_manual_declaration_can_be_found.py")], 120,
         why="his #166 ruling - manual anything is enough witness obivously - only means anything "
             "if a manual declaration can actually be FOUND by the code that grades ownership. "
             "d2r_foundLog is where he writes one. This pins that classify_row is called with the "
             "world it is grading rather than a default, because a declaration made on one "
             "profile is invisible from the other and the row then reads as unwitnessed."),
    Gate("test_the_river_folds_without_losing_a_figure",
         [sys.executable, os.path.join(HERE, "test_the_river_folds_without_losing_a_figure.py")], 120,
         why="HE ASKED WHETHER THE RIVER STRIP ABOVE THE PIPELINE WAS NEEDED AT ALL: 'is it "
             "needed visually? do i need this information? it can be hidden by me.' v3198 folded "
             "it -- the closed line keeps the one figure he acts on (where the reels stand), the "
             "open body keeps every defence the strip has accumulated across v2819/v2822/v2903, "
             "each of which was added after a real misread. This gate stops the two ways that "
             "rots: someone 'simplifying' the fold by dropping the body (taking three fixed "
             "defects with it), and the closed summary drifting onto its own source so it can "
             "contradict the cards it summarises. And it pins the default CLOSED, because that "
             "is the whole of what he asked for."),
    Gate("test_the_shelf_shows_the_four_lanes",
         [sys.executable, os.path.join(HERE, "test_the_shelf_shows_the_four_lanes.py")], 180,
         why="THE RIVER MADE VISIBLE AS THE FOUR LANES HE NAMED — INTAKE, PRINTER, CAPTURE, "
             "TOMBSTONE — over the nine stations that actually exist. river_lanes DECIDES NOTHING: "
             "reel_router.route() decides and this groups its answer, because his instruction was "
             "'the backend should be pinpoint perfect and nothing fabricated what so ever.. just "
             "the visual rendering'. The lane map is a PARTITION of reel_router.STATIONS, proven "
             "against the router's own tuple, and the view REFUSES TO DRAW if that stops holding "
             "— four tidy lanes over a broken map is worse than none, because it looks complete "
             "while reels quietly leave the frame. ⚠⚠ THE DEFECT THAT COST MOST WAS A NAME: the "
             "strip was first called _shRiverLoad, which ALREADY EXISTED (the SHELF_RIVER "
             "card-grouping feature). Two function declarations, one scope, later wins SILENTLY — "
             "the whole feature was unreachable while the container rendered, the export was on "
             "window, the fetch returned 200 with a good payload, and NOTHING THREW. A second bug "
             "hid it for four rounds: the could-not-ask branch rendered the SAME words as the "
             "loading placeholder. test_no_new_duplicate_function_name is the general guard that "
             "would have caught it in one second.",
         ),
    Gate("test_the_vault_proposal_is_watched",
         [sys.executable, os.path.join(HERE, "test_the_vault_proposal_is_watched.py")], 180,
         why="THE VAULT ACCUMULATOR'S PROPOSAL WAS SUPERVISED BY NOTHING. console_doctor carried "
             "exactly ONE vault row (`vault stores`) and it asks only whether the FILES ARE "
             "READABLE; whether what they OFFER is still acceptable was asked by nothing. A "
             "proposal is a PHOTOGRAPH of a decision made under the bars that existed when it was "
             "taken, and the bars move. ⚠ THE DRIFT HAS ALREADY HAPPENED IN BOTH DIRECTIONS: when "
             "this task was written KEEP_MIN_WITNESSES was 3 and 6 of his 7 stored rows failed it; "
             "re-measured when it came to be built the bar is 2 again and all 7 pass. The task's "
             "own premise expired between writing and building, which is the argument FOR a row "
             "that re-asks. ⚠ NOT DANGEROUS: vault_apply re-gates at the WRITE and is "
             "ALL-OR-NOTHING, so a stale proposal is REFUSED IN FULL rather than landing badly — "
             "the defect was only that nobody was told. ⛔ The row never re-grades his stored rows "
             "and never moves the bar, which guards a deleter.",
         ),
    Gate("test_the_eye_says_which_family_looked",
         [sys.executable, os.path.join(HERE, "test_the_eye_says_which_family_looked.py")], 180,
         why="A DARK EYE AND AN ABSENT ONE LOOKED IDENTICAL ON THE FLEET. The wire carried "
             "eye={live, ageMs} and the card drew the glyph ONLY when live, so three machines drew "
             "the same nothing: no second model family INSTALLED (Dean, correct and expected); one "
             "installed and IDLE (Konyo, toggled off); one installed, on and FAILING. Absence, rest "
             "and failure are not the same fact. ⚠ THE TASK WAS FIRST WRITTEN AS 'make the eye "
             "provider-neutral' AND THAT WAS WRONG — chronicle_hunt already defaults to Claude "
             "(`lane or \"claude\"`) with zero grok references, and G5 is a removable sidecar OFF "
             "by default. Nothing was rebuilt; the gap was that none of it reached the WIRE. "
             "⚠⚠ AVAILABILITY IS NOT A SECOND EYE: a lane that COULD look has not looked, only "
             "second_eye_ledger records one, and it refuses same-family looks so a model cannot "
             "certify its own work. A law forbids this chip ever wording itself as a completed "
             "review. Proven RED by four sabotages.",
         ),
    Gate("test_the_missing_wall_shows_the_qlvl",
         [sys.executable, os.path.join(HERE, "test_the_missing_wall_shows_the_qlvl.py")], 180,
         why="THE MISSING WALL PRINTS THE QLVL, AND REFUSES TO PRINT ONE IT DOES NOT HAVE. ⚠⚠ "
             "`qlvl: 0` IN THIS DATA IS A SENTINEL, NOT A LEVEL — measured distinct by name across "
             "5,925 item rows: high 126/127, grail 78/91, common 93/175, set 14/148, special 0/4. "
             "Printing the 0 would put a confident q0 under 134 set pieces and 96 uniques, in the "
             "longest list on the page, which is exactly where a fabricated figure would never be "
             "caught. ⚠⚠ AND THE 14 SET ROWS THAT DO CARRY ONE ARE AGGREGATES, NOT PIECES "
             "(Trang-Oul set (any piece), Immortal King set (any), Sigon's Complete Steel). "
             "`_etaHours` legitimately borrows a set aggregate as a fallback SOURCE; borrowing one "
             "for a LEVEL would print the set's gate under every piece of it, which is the "
             "substitution v2299 refused in the same file. The qlvl reader takes no fallback at "
             "all. Proven RED by three sabotages; the leak law took three attempts because the "
             "first two sabotages did not actually leak.",
         ),
    Gate("test_the_river_has_an_outlet",
         [sys.executable, os.path.join(HERE, "test_the_river_has_an_outlet.py")], 180,
         why="THE RIVER HAD NO OUTLET. `_station_of` could return 7 of the 9 declared stations; "
             "ROUTED and TOMBSTONE were UNREACHABLE, and `river_walk.py` had already written down "
             "why in its own note: the ONLY writer of a tombstone row lives inside the deleter "
             "(`reel_retention.apply_plan` -> `_tombstone`), so a reel could not be recorded as "
             "CLOSED OUT without being REMOVED — and removal is behind the arming lock, which is "
             "False and stays False. Being finished and being deleted were one event, so no reel "
             "could ever complete the waterfall. Measured on his shelf before: 40 reels, ROUTED 0, "
             "TOMBSTONE 0. ⚠⚠ THE FLAP THIS HAD TO AVOID: routing changes no evidence, so the "
             "router goes on deriving EMPTY for a routed reel; if the outlet overlay read OBSERVER "
             "rows, the observer walk's own output would feed back in and the station would "
             "oscillate for ever, appending a transition row to an append-only store on every "
             "walk. It reads ACTOR rows only. Proven live: walk 1 moved 6, walk 2 moved 0.",
         ),
    Gate("test_his_console_is_never_mine_to_kill",
         [sys.executable, os.path.join(HERE, "test_his_console_is_never_mine_to_kill.py")], 120,
         why="I NEARLY KILLED HIS CONSOLE AND THE GUARD WRITTEN TO STOP ME WOULD HAVE AGREED. He "
             "said his Mac was hot; one `ps -r` sample showed pid 69557 at 108.4%% CPU, 17h "
             "uptime, orphaned to ppid 1 — and I said 'found it, it is mine'. It is his console on "
             ":17772, which executes this whole tree. TWO defects had to line up. (1) "
             "`my_orphans.HIS_PORTS` — the constant whose own comment says a process holding one "
             "of these is NEVER mine — had exactly ONE reference: its definition. `_attribute` "
             "promised three witnesses, implemented two, and ended its refusal with 'holds none of "
             "our ports', an assertion about a check nobody ran; asked about his console it "
             "answered 'nothing can say whose it is'. (2) One `ps` %%CPU is a DECAYING AVERAGE: "
             "the same pid read 108.4%%, then 9.0%%, then 5.6%% seconds apart. ⚠ AND THE FIRST FIX "
             "WAS WORSE — lsof ORs its selectors, so without `-a` the check asked 'does ANYTHING "
             "listen on his ports', always true, declaring every process NEVER MINE and making the "
             "guard incapable of catching the runaway it exists for.",
         ),
    Gate("test_the_fleet_lane_reaches_the_heart",
         [sys.executable, os.path.join(HERE, "test_the_fleet_lane_reaches_the_heart.py")], 120,
         why="THE FLEET FAILED ON HIS SCREEN AND THE HEART HAD NEVER HEARD THE WORD. 2026-09-09 "
             "11:07, photographed: the card read `fleet unreachable — <urlopen error _ssl.c:1112: "
             "The handshake operation timed out>` while the heart's own footer two inches below "
             "said 8 dark, and not one of those 8 was the fleet. MEASURED: `grep -c fleet` was 0 "
             "in BOTH heart.py and lane_census.py, and CHECKS carried no fleet row — the lane was "
             "not failing its supervision, it HAD none. ⚠ AND THE PANEL ALREADY HELD THE ANSWER: "
             "fleet_presence_last_good() was built in v2815 to keep 'who did we last see' separate "
             "from 'did the fetch work', and `grep -c lastGood control_ui.html` was 0 — one "
             "producer, no consumer, so a console holding a three-machine roster rendered a C "
             "source location instead. ⚠⚠ THE SCRIPT-BLOCK HALF IS PART OF THE LAW: control_ui "
             "has two blocks and a call across them throws at call time and paints nothing, which "
             "has shipped four times — a fix declaring the helper in the wrong block would restore "
             "the exact blank card and pass every hand-check, so colocation is asserted.",
         ),
    Gate("test_the_river_reaches_the_heart",
         [sys.executable, os.path.join(HERE, "test_the_river_reaches_the_heart.py")], 180,
         why="THE RIVER MEASURED ITSELF FOR NOBODY. `tv/river.py` walks ELEVEN joints, grades each "
             "CARRIES/DRY/UNKNOWN and names the first blockage in a sentence a person can act on — "
             "and `grep -rl 'import river' tv/*.py` returned ONE file: its own test. Neither "
             "corroborate.py nor console_doctor.py had ever asked it anything. ⚠ A ROW CALLED 'the "
             "river' ALREADY EXISTED, which is why the gap survived: it reads reel_router and "
             "answers WHERE REELS ARE STATIONED, a different question from WHETHER THE JOINTS "
             "CARRY. The console watched position and was blind to flow. ⚠⚠ AND THE GATE JOINT WAS "
             "A ZERO WITH NO DENOMINATOR INSIDE THE DIAGNOSTIC ITSELF — TWO defects pointing the "
             "same way: it counted keys 'grounded'/'applied'/'accepted' that chron_last_result.json "
             "has NEVER written, AND it asked the top level when every figure lives under "
             "`result`. It reported '0 names grounded of 14,034' for a joint that was never "
             "measured. ⚠ THE TRUE STATE WAS NOT BLOCKED: his last sweep proposed 354 and the "
             "crossref answers '354 of the 354 are already in your chronicle; 0 are new' — NOTHING "
             "NEW TO GROUND, a legitimate state the old joint could not tell from a blockage "
             "because both rendered as 0. Now three states, the real keys, and 0 of 354 proposed "
             "with 41 held and the caveat in its own why. ⚠ IT ALSO CORRECTED ME: my "
             "'303 of 306 clear the bar' was a (reel,lane) proxy labelled an upper bound; the REAL "
             "witnesses() says uniques 272/306 (89%%), sets 86/126 (68%%), with 36 set names one "
             "witness short. 10 laws, 4 sabotages RED."),

    Gate("test_his_own_fleet_row_is_not_a_round_trip",
         [sys.executable, os.path.join(HERE, "test_his_own_fleet_row_is_not_a_round_trip.py")], 180,
         why="HIS OWN FLEET ROW CAME BACK FROM CLOUDFLARE TO TELL HIM WHAT WAS ON HIS OWN DISK. "
             "Konyo, seconds after ticking a set piece: 'i just changed my sets from a 123/135 to "
             "124/135 but how come THE FLEET is delayed? ... should it not be SHARING A CSS so its "
             "rendered is always the same?' MEASURED at that moment: board_tally.json already said "
             "sets 124/135, SIX SECONDS old, while the card read 123 'as of 1m ago'. The data was "
             "never late — the RENDER was: his own row arrived the way a cousin's does, published "
             "by the beacon and read back through fleet_presence, which is 60s cached. ⚠ AND THE "
             "ANSWER TO HIS QUESTION IS NO: sharing a stylesheet would make the two surfaces LOOK "
             "identical while still printing 123 and 124 — the disagreement would survive in "
             "matching fonts, which is worse, because two surfaces that look like one source and "
             "disagree are harder to disbelieve. What they must share is the SOURCE. ⚠ ONLY HIS "
             "ROW: a peer's numbers are knowable only through the beacon, so overlaying local "
             "figures onto Dean's row would publish Konyo's board as Dean's. ⚠ THROUGH "
             "board_tally_load(), the path authority — _fleet_show_total hardcoded its own "
             "os.path.join and thereby bypassed the TV_HIST isolation override, and this law "
             "proves the read by SUBSTITUTION rather than by grepping for a string. Verified live "
             "after relaunch: localRead=True, sets 124/135, both peers still on the beacon. "
             "9 laws, 3 sabotages RED."),

    Gate("test_the_shelf_builds_what_it_shows",
         [sys.executable, os.path.join(HERE, "test_the_shelf_builds_what_it_shows.py")], 180,
         why="THE SHELF BUILT 3,086 CARDS TO SHOW 529 AND THAT STOPPED THE WHOLE WINDOW PAINTING. "
             "Five reports in one afternoon — black shelf, empty ADVANCED, a theatre with nothing "
             "to close, a screen-height gap on Sessions — were FOUR SYMPTOMS OF ONE CAUSE. "
             "MEASURED: opening the shelf took the page 11,744 -> 84,414 elements in ONE build; "
             "3,086 cards at ~23 elements each = 72,337, which is 86% of the page. 2,557 of those "
             "cards were built and then display:none'd — 58,811 elements, 70% OF THE PAGE, built "
             "only to be invisible, while the panel's own chip already said '529 of 3086'. Past "
             "~84k elements WebKit stops producing frames, so once the shelf had been opened ONCE "
             "panels he never touched went dark too. His console diagnosed itself and nothing "
             "surfaced it: uiBeat painting=false, frozenBeats=12, 'DOM is intact (84470 "
             "elements)', and ui_faults.jsonl carries days of 'BEATING AND DRAWING NOTHING'. "
             "Proven by relaunch: 84,470 -> 11,796, painting=true. AFTER: 84,414 -> 27,415, 529 "
             "cards, chip still reads 2,557. ⚠ TWO OF MY OWN READS WERE WRONG FIRST: 'it appends "
             "without clearing' (refuted — innerHTML replaces, re-opens add 0) and _shellPaintAgain "
             "(a symptom fix: a page that CANNOT paint asked to try again). ⚠ THE TRAPS THIS PINS: "
             "return '' rather than .filter() or data-n renumbers and silently breaks the "
             "card->session join; count the ghosts from TH.sessions or the chip reads '0 empty "
             "runs' while withholding 2,557; and the chip must REBUILD, not unhide, or it goes "
             "inert while looking exactly like a chip that works. 7 laws, 3 sabotages RED."),

    Gate("test_one_item_has_one_key",
         [sys.executable, os.path.join(HERE, "test_one_item_has_one_key.py")], 180,
         why="THE SAME ITEM WAS STORED TWICE AND ITS SIGHTINGS NEVER MET. chron_evidence.json keys "
             "the confluence store by RAW name, and his live store held Atma's Scarab as curly 20 "
             "PLUS straight 38, Saracen's Chance as curly 50 plus straight 6, Endlesshail 22 plus "
             "'Endless Hail' 2, Stealskull 23 plus 'Steal Skull' 2. The apostrophe split is not "
             "drift from outside: bible.html spells those four CURLY in the item rows and STRAIGHT "
             "in ITEM_VALUE, in the same file. ⚠ THE COST IS CORROBORATION, NOT PICTURES — "
             "merge_proposals de-dupes by (reel, frame, lane) WITHIN a bucket, so two spellings "
             "meant two buckets and a name seen in reel A under one and reel B under the other "
             "read as two lonely singles, so cross-reel could never fire. Same defect v1776/v1798 "
             "killed, arriving through the KEY instead of the value. ⚠⚠ EXACT FOLD ONLY: "
             "canonical() also does a difflib near-match, which is right for asking what an OCR "
             "read meant and WRONG as a store key — the roster holds near-twin pairs ('Bone Break' "
             "/ 'Latent Bone Break') on purpose, so a fuzzy key is a coin flip between two grail "
             "items. MEASURED over all 310 names: 281 fold exactly, 10 would need fuzzy (left "
             "RAW), 19 match no roster (rares/bases, left RAW), and exactly 4 collisions — the "
             "four pairs and nothing else. ⚠ THE FOLD PROVES THE SPLIT WAS REAL: 20+38 becomes 54 "
             "not 58, because 5 rows were the SAME PHOTOGRAPH banked under both spellings. "
             "11 laws; sabotage-proven 3 ways (inert fold 5 red, unjoined merge 1 red, fuzzy fold "
             "2 red)."),

    Gate("test_a_reused_shell_must_not_inherit_a_grid_it_has_no_tenant_for",
         [sys.executable, os.path.join(HERE,
          "test_a_reused_shell_must_not_inherit_a_grid_it_has_no_tenant_for.py")], 120,
         why="HE REPORTED IT THREE TIMES — 'symetric', '+ typography', 'its like not aligned' — "
             "and the cause was a grid column reserved for a panel that is not there. `.fx-body` "
             "is a two-column grid whose right rail belongs to the `.fx-drill` read-trail aside; "
             "three dialogs reuse the `.fleet-xref` shell for its DESIGN and own no drill, so that "
             "rail has no tenant and whatever child comes second falls into it. Measured at 1080 "
             "on #fleet-xref: the body is `.fx-cols` + `.fx-foot`, exactly two children, so the "
             "STATS LINE rendered beside the 'you both need' heading and squeezed the third column "
             "to a sliver. THIRD OCCURRENCE — v2384 hit #ver-xref, v2443 hit #heart-ov and its own "
             "comment reads 'the warning was already written directly above and I walked into it "
             "anyway'. Both fixes were written as an ID LIST, so each new panel had to be "
             "remembered into it and #fleet-xref, the original owner of the class, never was. This "
             "gate therefore refuses the id-list SHAPE, not a missing id: the override must be "
             "selected by the class so membership is automatic. It parses the stylesheet by "
             "brace-matching rather than grepping, so a rule buried in an unrelated @media block "
             "cannot satisfy it."),
    Gate("test_foreign_is_narrow_and_unknown_stays_unknown",
         [sys.executable, os.path.join(HERE,
          "test_foreign_is_narrow_and_unknown_stays_unknown.py")], 180,
         why="TWO THREADS WERE UNKNOWN FOREVER AND THE FIX IS THE DANGEROUS KIND. Measured on his "
             "live console 2026-09-12: vessels 22, WATCHED 20, DARK 0, UNKNOWN 2 — and both "
             "UNKNOWNs were `serve_forever` and `wait`, because census() reduces "
             "`Thread(target=srv.serve_forever)` to a bare name and classify() then finds no `def` "
             "of it in control_app.py. It was RIGHT to answer UNKNOWN; but nobody could ever look, "
             "because those are methods on stdlib objects with no definition in this repo at all. "
             "v3034 added the kind FOREIGN for exactly that. ⚠ A classification that converts "
             "UNKNOWN into not-a-vessel is a machine for making a census look finished: loosened by "
             "one condition it stops describing stdlib methods and starts absolving real lanes, and "
             "the result reads UNKNOWN 0 — the number a completed job produces. So this gate does "
             "not check that the two known names are FOREIGN; it checks that FOREIGN CANNOT WIDEN. "
             "A target with no receiver stays UNKNOWN however unresolvable, and a target whose "
             "method IS defined anywhere in this package stays UNKNOWN even through a receiver. "
             "Both red-proofs delete one of those conditions rather than the feature."),
    Gate("test_the_eagle_is_asked_where_it_lives",
         [sys.executable, os.path.join(HERE, "test_the_eagle_is_asked_where_it_lives.py")], 120,
         why="THE EAGLE'S COLUMN COULD NEVER HAVE BEEN ANYTHING BUT EMPTY, AND THE TABLE BLAMED "
             "THE EAGLE FOR IT. organ_matrix asked the eagle by doing __import__('control_app') "
             "and calling eagle_state() on a FRESHLY IMPORTED module, where _EAGLE is still the "
             "literal it is defined as — rows: [], say: 'not measured yet'. That dict is only "
             "filled by the RUNNING console's loop, in another process, so the answer was [] for "
             "every tree regardless of how well the eagle worked. Measured 2026-09-12: the live "
             "console published 58 eagle rows on /api/status in the same minute the table printed "
             "'eagle answered, and named nothing at all — which cannot tell watches-nothing apart "
             "from had-nothing-to-say'. It was neither; nobody had asked the process that knows. "
             "Pointed at the console, the same organ names 59. ⚠ The failure was invisible because "
             "it looked like a FINDING: an empty answer reads as a verdict about the organ and was "
             "a verdict about the reader, which is why this gate checks the READER. Its second "
             "half is equally load-bearing — with the console down the reader must answer UNKNOWN "
             "with a reason and never an empty set, because 'the console was off' and 'the eagle "
             "watches nothing' are opposite facts and only one is a defect. Parsed with ast, so a "
             "mention in a comment can neither satisfy nor defeat it."),
    Gate("test_the_doctor_says_what_it_watches",
         [sys.executable, os.path.join(HERE, "test_the_doctor_says_what_it_watches.py")], 180,
         why="THE DOCTOR WORKED PERFECTLY AND ITS WHOLE COLUMN READ UNKNOWN, because nobody had "
             "said what it watches in the words the table uses. organ_matrix measured it: 'doctor "
             "names 59 thing(s), and NONE of them resolves to any of the 58 surfaces — it is "
             "naming a different KIND of thing (concerns, not code objects)'. A check is called "
             "'shelf lanes reading'; a surface is called 'shelf-cards'. ⚠ IT CANNOT BE DERIVED, "
             "and that was MEASURED before it was authored: a parser over each check's body for "
             "unambiguous surface-shaped tokens found, on a 12-check sample, 4 reaching anything "
             "at all and not one registry surface — it returned control_app.py, status, per-lane, "
             "REG-415. The relationship is not in the code, so the deriver was thrown away rather "
             "than shipped as noise, and WATCHES states it instead. This gate is what keeps a "
             "STATED thing honest: every check must appear (silence is not 'covers nothing' — a "
             "check added next week with no entry would inherit an empty list and read ABSENT, a "
             "claim nobody made); a check that truly watches no surface declares an EMPTY tuple "
             "deliberately, because under-claiming is the intended bias; and a declared name that "
             "is not in the registry FAILS, since a typo would sit there forever matching nothing "
             "and looking like considered coverage. Measured after: surfaces named by NO "
             "comparable organ went 49 -> 29, and comparable organs 1 -> 2."),
    Gate("test_a_reader_does_not_go_dark_when_an_unrelated_gate_goes_blind",
         [sys.executable, os.path.join(HERE, "test_a_reader_does_not_go_dark_when_an_unrelated_gate_goes_blind.py")], 120,
         why="NINE BLIND GATES TOOK THE RIVER OFF HIS SCREEN, and none of them watched the river. "
             "v3049 put a may() seat in printer.stream(), the chokepoint every river caller goes "
             "through. BLIND never softens — correctly — so when routine U recorded 9 blind "
             "instruments, /api/river answered lanes.ok:false, 'printer.stream() could not "
             "answer', and his live console rendered 'the river could not be drawn'. Measured on "
             ":17772, not a fixture. A surface that ACTS keeps the full guarantee; a surface that "
             "only SHOWS him what is there must not go blank because an unrelated gate lost its "
             "red-proof. may_on_merit refuses every destructive lock outright so it can never "
             "become a soft door."),
    Gate("test_a_test_seam_never_softens_the_real_lock",
         [sys.executable, os.path.join(HERE, "test_a_test_seam_never_softens_the_real_lock.py")], 120,
         why="A SEAM THAT LETS TESTS ASSUME SUPERVISION MUST NEVER LET THE LOCK'S OWN LAW ASSUME "
             "IT. self_arming reads TV_HEART_CENSUS so tests about SWEEP LOGIC stop depending on "
             "whether his census happens to be fresh — measured: 16 gate-file edits staled it, "
             "closed vault.sweep_start and failed 20 tests that were not about supervision. But a "
             "seam into a safety path is the thing that quietly stops guarding, so this refuses "
             "two rots: the lock's own law using the seam (it would prove nothing), and the seam "
             "returning anything but CLOSED on an absent census."),
    Gate("test_an_organ_never_covers_a_lane_it_cannot_name",
         [sys.executable, os.path.join(HERE, "test_an_organ_never_covers_a_lane_it_cannot_name.py")], 120,
         why="AN ORGAN'S COVERAGE NEVER CROSSES A LANE. Measured 2026-09-13: the matrix called "
             "fleet.sets, fleet.uniques, roster.set and roster.unique MISNAMED on both the eagle "
             "and the doctor — 8 cells, 100% of the MISNAMED in the table — meaning 'the organ IS "
             "watching that thing under another name'. It was not: both organs name exactly "
             "chronicle.set and chronicle.unique and NOTHING in the fleet or roster lane. "
             "one_name.same_thing compares the tail and is lane-blind, so four surfaces borrowed "
             "chronicle's organs. This does not demand those lanes be covered — they are honestly "
             "ABSENT — it refuses a table that reports a watcher it does not have."),
    Gate("test_the_window_says_which_document_it_renders",
         [sys.executable, os.path.join(HERE, "test_the_window_says_which_document_it_renders.py")], 120,
         why="IS THE PAGE IN FRONT OF HIM THE PAGE ON DISK? His console execs the working tree, so "
             "every save is a deploy - and until v3057 nothing could answer that. The console "
             "published FOUR versions (ver, liveVer, bibleVer, agentVer) and every one described a "
             "FILE, never the rendered document. The absence was not silent: on 2026-09-12 and "
             "again 2026-09-13 a liveVer trailing the tree was read as 'the reload did not take', "
             "which is wrong - liveVer lagging disk is correct for unpushed work. The page now "
             "sends its own D2R_BUILD id on the beat, the server publishes it RAW as "
             "uiBeat.docVer, and a doctor row compares it to disk. This refuses all three rots: "
             "the page going quiet, the server not publishing, and the doctor calling an older "
             "document - or an ABSENT stamp - agreement."),
    Gate("test_the_shelf_is_watched_by_all_four_organs",
         [sys.executable, os.path.join(HERE, "test_the_shelf_is_watched_by_all_four_organs.py")], 180,
         why="THE SHELF MUST BE WATCHED BY ALL FOUR ORGANS. Measured 2026-09-13: it had 8 of 16 "
             "organ cells and NO CORROBORATOR ON ANY SURFACE - which is exactly how a card could "
             "print '19 frames - full video' while the dossier printed '0 FRAMES' for the same "
             "reel and nothing noticed. An eagle watches cheaply, a watchdog asks if a thing is "
             "alive, a doctor asks if a check passes; only a corroborator compares witnesses. On "
             "its first run the new one reported 52 of 53 reels disagreeing and named the odd "
             "witness: `frames` counts JOURNAL ROWS IN A GROUP, not frames of film. This refuses "
             "four rots - the corroborator or the watchdog dropping the shelf, the corroborator "
             "losing the ability to say NO, and an unwitnessable shelf reading as agreement."),
    Gate("test_one_reel_is_one_session_row",
         [sys.executable, os.path.join(HERE, "test_one_reel_is_one_session_row.py")], 180,
         why="ONE REEL IS ONE SESSION ROW, however its journal rows interleave. split_sessions cut "
             "a new session whenever sessionId differed from the PRECEDING row, so two reels "
             "recording concurrently emitted A,B,A as THREE groups. Measured on his journal: "
             "11,162 rows -> 3,129 contiguous runs -> 3,128 session rows, 176 sessionIds in more "
             "than one run, worst reel 16. Each fragment carried its own SHARE of the frames, so "
             "one reel read frames=10 in one row and frames=0 in another while 19 stills sat on "
             "disk - he opened the row saying 0 and the player had nothing to play. Fixed: a reel "
             "is all its rows; unstamped pre-v780 history keeps the silence split. After: 2,893 "
             "groups, 0 duplicates, every row preserved."),
    Gate("test_the_transport_offers_no_playback_without_a_reel",
         [sys.executable, os.path.join(HERE, "test_the_transport_offers_no_playback_without_a_reel.py")], 120,
         why="THE TRANSPORT MAY NOT OFFER PLAYBACK FOR A REEL HE HAS NOT OPENED. He reported it "
             "scrolling the shelf with no session open: play/pause, step, timeline, mode, speed "
             "and fullscreen all showing, and hovering one fired 'Next screenshot' over a reel "
             "that was never opened. The band itself is deliberate - #th-shelfov stops 54-72px "
             "short so the strip stays reachable - so this hides only the controls that need a "
             "LOADED REEL and keeps the shelf toggle and session steppers. Keyed off "
             ":has(#th-shelfov:not([hidden])) rather than a hand-set class, because the shelf is "
             "opened from several call sites and a class would drift invisibly on the one "
             "somebody forgot."),
    Gate("test_a_lane_count_names_the_population_it_counted",
         [sys.executable, os.path.join(HERE, "test_a_lane_count_names_the_population_it_counted.py")], 120,
         why="A LANE COUNT MUST NAME WHAT IT COUNTED. Measured on his console, same lane, same "
             "second: the shelf lane header printed 'INTAKE 8 REELS' from a count of visible "
             "CARDS while the river strip four inches above printed 'INTAKE 4' from /api/river's "
             "REELS - 425 cards against 16 reels, two populations 26x apart under one word. The "
             "NUMBER was never wrong, only the noun, the same shape as 'stash x19' counting "
             "frames and 'frames' counting journal rows. RUN is already this shelf's word for a "
             "card ('2,468 empty runs', 'Search runs'), so the rename removes a vocabulary rather "
             "than adding one. Also pins that the river strip's own reel phrase SURVIVES - that "
             "surface is correct and v2822 already fixed its denominators."),
    Gate("test_the_epoch_never_deletes_and_never_fakes_a_terminus",
         [sys.executable, os.path.join(HERE, "test_the_epoch_never_deletes_and_never_fakes_a_terminus.py")], 120,
         why="THE EPOCH MAY NEVER DELETE AND MAY NEVER REPORT A TERMINUS IT DID NOT REACH. Its "
             "first run on his footage converged to a FIXED POINT: 24 reels on disk, 0 candidates "
             "to release, nothing moved across two cycles, and 7 gap rules STILL never fired - "
             "eligible among them. Not once has a reel been ruled safe to release, which is the "
             "measurement behind 'the vault hasnt worked yet'. So nothing may delete on this lane "
             "until it has been seen to reach its own terminus. Refuses four rots: the harness "
             "gaining a destructive call (parsed as CALLS, since its prose says delete and retire "
             "repeatedly), `apply` ceasing to default dry, a fixed point reported as success, and "
             "the two excluded rules dropped silently instead of named with their reason."),
    Gate("test_the_vault_writes_only_what_the_gate_judged",
         [sys.executable, os.path.join(HERE, "test_the_vault_writes_only_what_the_gate_judged.py")], 120,
         why="THE VAULT WRITES ONLY THE ROWS THE GATE ACTUALLY JUDGED. Found by handing "
             "vault_apply COLD to a different model family - the method that found the `unsure` "
             "hole in v2641. The re-gate collected _kept and _dropped, refused on _dropped, then "
             "THREW _kept AWAY and built the payload from a SECOND read of the proposal (and a "
             "THIRD via apply_payload). A list subclass with a lying __iter__, or a dict subclass "
             "whose get() is not a snapshot, answered the gate with a corroborated decoy and the "
             "write with an evidence-less row. In-process only - json.loads cannot build a lying "
             "container - but this re-gate exists because 'the gate has to hold where the WRITE "
             "happens', and a verdict discarded one line later holds nowhere."),
    Gate("test_the_orphan_guard_is_never_inside_a_handler",
         [sys.executable, os.path.join(HERE, "test_the_orphan_guard_is_never_inside_a_handler.py")], 120,
         why="THE THREAD THAT CAN END THE CONSOLE MUST NOT HAVE ITS TRIGGER INSIDE AN EXCEPTION "
             "HANDLER. board_window._orphan_watch calls os._exit(0) once the control server has "
             "been unreachable ~100s - the guard that stops a board window outliving its console, "
             "the orphaned-process case that made his Mac hot (three consoles at PPID 1, load 5.42 "
             "-> 3.08 when killed). v3076 inserted a try/except around a lane_trace.note call above "
             "it and the old `if misses >= 5: os._exit(0)` KEPT ITS INDENT, becoming the second "
             "statement of that except after `pass`. Reproduced by AST: FunctionDef > While > Try "
             "> ExceptHandler > If. lane_trace.note swallows everything and returns False, so it "
             "never raises - the self-close could effectively NEVER run, and the inversion is that "
             "a WORKING corroborator was what disabled the killer. It SHIPPED, and the existing "
             "coverage gate stayed green because it only asserts `_lane_tick` appears in the AST "
             "dump and os._exit was still in the tree. Found by the cross-family second eye "
             "reading the pushed diff."),
    Gate("test_a_failed_call_is_not_a_verdict_on_the_film",
         [sys.executable, os.path.join(HERE, "test_a_failed_call_is_not_a_verdict_on_the_film.py")], 120,
         why="A CLASSIFY CALL THAT FAILED IS NOT A FRAME THAT COULD NOT BE CLASSIFIED. `_classify` "
             "wrapped claude_read in a bare `except Exception: return None`, and _surface_of(None) "
             "is the SAME None a frame gets when it genuinely is not an ownership surface - so two "
             "opposite facts produced one verdict and sweep() wrote 'could not be classified - "
             "held rather than guessed onto a shelf', a sentence about the FILM describing "
             "something that happened to the RUN. Nothing prompted a retry because nobody was told "
             "there was anything to retry. MEASURED on the reel s_1788099999528_42457: two sweeps "
             "reported classified=2 and held the run, while calling tv_diablo.claude_read() on the "
             "SAME frame directly returned scene='stash' with names - the frame is a Shared stash "
             "page 5/5 with ~25 items and the inventory open beside it. After the lane recovered "
             "the same sweep read it: pagesRead=1, 33 occupied / 7 free, sealed examinedEmpty, and "
             "the reel RELEASED (panels_never_banked True -> False). The footage was held by a "
             "transient call for as long as nobody could see the difference. Recorded ONCE like "
             "_pix_err, never per frame."),
    Gate("test_a_read_reel_says_why_it_cannot_seal",
         [sys.executable, os.path.join(HERE, "test_a_read_reel_says_why_it_cannot_seal.py")], 120,
         why="A REEL THAT WAS READ AND STILL CANNOT SEAL MUST SAY WHICH CONDITION REFUSED. "
             "vault_seal_is_definitive takes four inputs and returns ONE bool, so a reel read "
             "cleanly that will not release looks identical to one nobody looked at. MEASURED on "
             "the 63-frame held reel (s_1788195270707_36946): the sweep printed '1 panel(s) READ CLEANLY and held no "
             "readable name', classifyError was None and the pixel lane printed nothing - and the "
             "seal still came back examinedEmpty=None. The cause was invisible from outside: "
             "read_ok=1 with an EMPTY reconciled, so len(rec) != read_ok refused. A frame READ but "
             "never CROSS-CHECKED is a real state that had no voice; pixelLaneError (v1998) covers "
             "the lane FAILING, not the lane running and skipping a frame. why_not_definitive is "
             "PURE for the same reason its sibling is, and the law asserts the two AGREE on every "
             "combination - a silent explanation exactly when the verdict is definitive - because "
             "two functions deriving one rule is how a console says 'fine' beside a reel it "
             "refuses to release."),
    Gate("test_the_console_opens_fullscreen",
         [sys.executable, os.path.join(HERE, "test_the_console_opens_fullscreen.py")], 120,
         why="THE CONSOLE OPENS FULLSCREEN, AND A WINDOWED ONE STOPS PAINTING WITHIN TWENTY "
             "SECONDS. His ask: 'this console keeps opening up windows mode. and it should open up "
             "FULLSCREEN by default with an option to go windows mode if wanted.' It is not only a "
             "preference - it is the cause of every black stage the eyes lane has reported. "
             "MEASURED on his live console, three samples 20s apart with nothing touching it: "
             "hidden=true painting=false, then painting=true after a raise, then dark again within "
             "TWENTY SECONDS. A page that is not frontmost is document.hidden, so it stops "
             "painting, so there is nothing to photograph - while /api/status answered in 31ms the "
             "whole time. Grok Bot reported 'Quartz ON-SCREEN none' and 'off-space white is not "
             "blank' tick after tick and I read it as the bot being unable to look, when it was "
             "reporting that there was nothing on screen to look AT. ⚠ The opt-out stays REAL "
             "(TV_WINDOWED=1 starts windowed at the old 1120x660, which v1464 sized to a "
             "672-logical work area) because a default nobody can leave is a trap. ⚠ And the key "
             "is added BEFORE the _cw_ok signature filter, so a pywebview build that does not "
             "accept `fullscreen` drops it and still gets a window - a console that refuses to "
             "start is worse than one that starts windowed."),
    Gate("test_a_chip_counts_only_what_it_can_explain",
         [sys.executable, os.path.join(HERE, "test_a_chip_counts_only_what_it_can_explain.py")], 120,
         why="A CHIP MAY ONLY COUNT ROWS WHOSE ABSENCE OF FILM IT CAN EXPLAIN, and the defect this "
             "pins SHIPPED IN THE COMMIT THAT ARGUED AGAINST IT. v3092 dropped no-film rows into "
             "two chips - 'retired to history' and 'no film and no record' - and put that split "
             "ABOVE the stub check. A STUB is a run with under three real rows and no reel: it "
             "never HAD film, but it also has footageN 0, so every stub fell into the no-film "
             "branch first and was labelled as though its film had been retired after giving up "
             "its information. MEASURED on his live console over 2,894 rows: the chips would have "
             "read 450 and 2,424, of which 184 and 2,286 were STUBS - the second chip claiming "
             "2,424 against a true 138, a 17x overstatement. And that same commit carries a "
             "comment insisting the two states be kept apart because collapsing them throws away "
             "the only fact that says whether the river finished or stalled: the reasoning was "
             "right, the branch order was wrong, and prose in a commit is not evidence about "
             "behaviour. ⚠ The numbers reported to him (266/138) were measured BEFORE the code and "
             "never re-measured against it - a figure derived from intent rather than the "
             "artifact. THE RULE: every drop branch must come AFTER the branches whose rows it "
             "would otherwise absorb."),
    Gate("test_the_vault_save_can_only_copy",
         [sys.executable, os.path.join(HERE, "test_the_vault_save_can_only_copy.py")], 120,
         why="THE VAULT'S SAVE MAY ONLY COPY, AND A PARTIAL SAVE IS NOT A SAVE. His ask: the vault "
             "'can be restored or wiped clean with a safeguarded button that asks twice', brought "
             "back 'based on like last recent save ledger wise.. by day and timestamp'. The wipe is "
             "the most destructive act in this console - six stores gone on a click - and the only "
             "thing that makes it safe to build is a save already proven to work. So the module may "
             "not contain a delete BY CONSTRUCTION, the way hover_drive never BUILDS a mouse-down: "
             "no remove, unlink, rmtree, truncate, and no store opened for writing, asserted by "
             "PARSE rather than grep because a grep is satisfied by the word appearing in a comment "
             "saying it must not. A PARTIAL save is the dangerous shape, not a failed one - five of "
             "six stores copied silently restores as a complete-looking vault that is short, at the "
             "one moment nobody can check, so every file is read back at its source size and any "
             "mismatch fails the WHOLE save. Stores are NAMED not globbed (a vault*.json glob would "
             "sweep whatever a future feature calls vault-something). And the retention is REUSED, "
             "not re-derived: 48h rolling + one keeper per UTC day for 90 days is "
             "_ledger_backup_prune's policy, sized in v3009 from his real 2026-09-08 loss where the "
             "oldest backup on disk was 69 HOURS too young to answer which save predates it."),
    Gate("test_a_proof_history_survives_its_verdict",
         [sys.executable, os.path.join(HERE, "test_a_proof_history_survives_its_verdict.py")], 180,
         why="A CHECK'S PROOF HISTORY MUST REACH EVERY BRANCH, AND A VESSEL MUST INHERIT ITS "
             "WATCHER'S SCORE. Two breaks found together, both the shape this tree keeps making: "
             "built at both ends, joined on one path only. (1) _row computes the Wilson number "
             "from k/n in ONE place, correctly - and check_self_arming passed them on its OK "
             "return and NEITHER other. So the moment a lock went inert, which is the finding that "
             "check exists to make, the row lost proofK, proofN and score entirely. MEASURED on "
             "his live console: the selfArming row was state=warn and carried no k, no n and no "
             "score KEY AT ALL, hiding 564 sabotages of evidence exactly when something was wrong; "
             "after the fix proofK=556 proofN=564 score=0.9723. A proof history does not depend on "
             "today's verdict. (2) heart.vessels() asked `scored.get(watcher)` where watcher is a "
             "LANE name from the census, while `scored` was keyed ONLY on organ ids - lanes, "
             "readers, selfArming, board_join, laneLiveness. The intersection of those two "
             "vocabularies is EMPTY, so FLOWING was unreachable by any path for any vessel, ever. "
             "Keying by each organ's own `surfaces` bridges it: 20 surfaces now resolve to a proven "
             "score where none did. ⚠ FLOWING is STILL None and that is now the TRUE answer - the "
             "20 vessels are watched by laneLiveness, which nobody has ever sabotaged, so it is "
             "UNPROVEN (work owed) and must never be drawn as 0.0, which would mean tested and "
             "never refused."),
    Gate("test_the_blueprint_names_the_engine",
         [sys.executable, os.path.join(HERE, "test_the_blueprint_names_the_engine.py")], 180,
         why="BLUEPRINT.md MUST NAME EVERY MODULE, AND A CONCEPT MUST FIND ITS OWNER IN ONE GREP. "
             "His ask: 'make sure the blueprint is updated accordignly so you dont need to ask "
             "these questions in the future and the blueprints speaks for itself'. This is "
             "test_the_blueprint_cannot_go_stale's sibling one rung down: that one keeps the GATES "
             "section honest, this one keeps the CODE section honest - and the code section did "
             "not exist until v3091 while the tree held 178 modules and 1,045 public functions "
             "that this document said nothing about. MEASURED the day it was built: `footprint`, a "
             "function shipped hours earlier in slot_identity.py that REFUSES an item overhanging "
             "the grid, scored ZERO hits anywhere in BLUEPRINT.md - and so did occupancy, "
             "names_loc, terror zone, lattice and slot identity, every one a shipped tested "
             "behaviour the map could not find. The section splits DERIVED (which modules exist, "
             "which are imported - parsed every render, so it cannot go stale) from CURATED "
             "(purpose, territory, gotcha in tv/engine_index.json, because a sentence about what a "
             "module MEANS cannot come from an AST), and this law guards the DRIFT between them: a "
             "module on disk with no entry, or an entry whose file is gone, must be REPORTED. A "
             "map that silently omits a module is worse than no map. It also pins determinism, "
             "because a clock leaking into render() makes every tree look stale."),
    Gate("test_a_card_tile_reads_the_chronicles",
         [sys.executable, os.path.join(HERE, "test_a_card_tile_reads_the_chronicles.py")], 120,
         why="THE REEL CARD'S LAST TWO TILES MUST READ THE CHRONICLES, AND AN ABSENT ROSTER IS NOT "
             "A ZERO. His ask: 'where its says grail.. i want it reading the chronicles.. what does "
             "cover even mean?'. MEASURED over the 425 cards the shelf actually renders - not all "
             "2,893 journal rows, because the shelf hides empty runs and the wrong denominator "
             "would have overstated every figure: COVER had a value on 16 of 425 and TWELVE of "
             "those read 0%, so a real figure appeared on FOUR cards in 425; GRAILS counted "
             "tier=='grail' and found 16 because tier is UNSET on 194 of the 218 finds (89%), so "
             "it measured whether an optional field happened to be filled in, not rarity. Every "
             "find carries a NAME and the rosters know what a name IS (398 uniques, 135 set "
             "pieces): folding the same 218 names gives 57 uniques + 26 sets = 83 against the old "
             "tile's 16, and a figure on 25 cards where the old one managed 10. The 135 that match "
             "nothing are base items and runewords and are correctly not chronicle rows. It folds "
             "through chronicle_resolve.canonical rather than a second comparison at the call site "
             "- measured first, exact and canonical() agree 57/26/135 with zero drift - so it "
             "inherits the near-name calibration that refuses 'Bone Break'/'Latent Bone Break'. "
             "And '-' and '?' stay DIFFERENT ANSWERS: load_roster RAISES rather than returning {} "
             "because an empty roster would classify every name as debris, which here would print "
             "a confident 0 uniques on every card in the shelf."),
    Gate("test_a_blob_of_cells_is_not_an_item",
         [sys.executable, os.path.join(HERE, "test_a_blob_of_cells_is_not_an_item.py")], 120,
         why="THE OCCUPIED CELLS ARE EVIDENCE; THE CLUSTERS THEY FORM ARE NOT ITEMS. He asked for "
             "the ledger to carry slot identity, footprint, witness count and container 'item wise'. "
             "Every piece already existed and ONE LINE threw the useful half away: "
             "vault_corpus.inventory_occupancy returns {ok, occupied, free, cells, grid} - grid "
             "being a row-major array of taken/None read from PIXELS on a bimodal signal - and the "
             "sweep kept only the two COUNTS, so slot_identity.item_groups was never handed anything "
             "and a vault row could say 'Bone Break, stash' while knowing nothing about WHERE in the "
             "panel it sat. This law pins the join: cells are carried, derived from the grid, never "
             "synthesised from a range. AND IT PINS THE CAVEAT, because item_groups joins ADJACENT "
             "cells so touching items merge. MEASURED on his own f_1788100004704.jpg: 33 occupied "
             "cells -> 2 clusters, one of them 25 of 33 cells with a 7x4 footprint, which is plainly "
             "many items. Storing that under the word ITEMS would be a right number beneath a word "
             "that stopped being true, so they are blobs, carrying blobsAreItems=False. The third "
             "test re-measures the merge on a synthetic 2x2 pair - touching gives 1 cluster, a "
             "one-cell gap gives 2 - so the caveat is proven on CI with no footage, and if the "
             "grouping ever stops merging, the law that exists to describe it fails instead of "
             "quietly describing something untrue."),
    Gate("test_the_shelf_shows_reels_before_it_shows_charts",
         [sys.executable, os.path.join(HERE, "test_the_shelf_shows_reels_before_it_shows_charts.py")], 120,
         why="THE CARDS COME FIRST AND ACTIVITY LEADS THE ANALYTIC BAND BEHIND THEM - two of his "
             "asks pulling opposite ways, one of them a measured scar. He asked for the ACTIVITY "
             "chart 'uptop organized with the other data/anlytics TOP of the SHELF section'. Read "
             "literally that is above the list, and v2985 MEASURED what that costs at his real "
             "1120x660: the overlay is trapped in a grid row worth ~449px of a 660px window and "
             "549px of furniture above the first card put every reel off-screen - the panel named "
             "'your reels' showed none of them, photographed as blank three times. So the list "
             "precedes every analytic block and ACTIVITY leads the band rather than trailing it. "
             "Reads the assembly order, and counts each marker first because two matches would "
             "make the index comparison meaningless."),
    Gate("test_a_held_stage_does_not_read_as_a_queue",
         [sys.executable, os.path.join(HERE, "test_a_held_stage_does_not_read_as_a_queue.py")], 120,
         why="A STAGE WHOSE EVERY REEL IS HELD MUST NOT RENDER AS A PLAIN COUNT. His own words at "
             "his console: 'this 8 releasable has been stale for like a week im pretty sure'. He "
             "was right, and it was not stale data - it was a figure that CANNOT MOVE. Measured "
             "on GET /api/reel_story: onDisk 12, releasable 8, banked 4, and all twelve held - the "
             "8 by the newest-8 floor (holdKind policy), the 4 for missing evidence. reel_story "
             "maps the 'recent' tag onto the 'releasable' stage, so that 8 IS the floor, counted, "
             "pinned at 8 forever, drawn in plain gold under a heading about what gets 'no "
             "further'. The number was right and the word above it had stopped being true. This "
             "law extracts the real rail builder and runs it under node against his own reel "
             "shapes - it does not grep for the word 'held', which a comment would satisfy."),
    Gate("test_the_drain_covers_the_whole_journal_ring",
         [sys.executable, os.path.join(HERE, "test_the_drain_covers_the_whole_journal_ring.py")], 180,
         why="THE DRAIN MUST COVER EVERY FILE THE JOURNAL IS READ FROM, OR REFUSE TO RUN - and this "
             "is why the river could not drain, invisible for six versions. replay.load_journal has "
             "read a GENERATION RING since v779 (.5 through .1 then the live file) while "
             "journal_retention asked tv_diablo.JOURNAL and got the live file ALONE, so the planner "
             "judged the whole journal and the applier rewrote one file of it. MEASURED on his "
             "tree: sessions.1.jsonl holds 7,103 rows and 2,483 sessions the applier never touched, "
             "against sessions.jsonl's 5,093 rows and 357 sessions. Every release against a session "
             "in the rotated half was a SILENT NO-OP that reported success - removedSessions 324 "
             "looked like progress while 2,483 sessions were unreachable. replay.journal_paths() is "
             "now the one place the ring is spelled and both ends ask it. AND A PLAN IS A JUDGEMENT "
             "ABOUT A SET OF FILES: applying it to a different set is how a correct decision lands "
             "on the wrong rows, which is not hypothetical - on 2026-09-14 a plan computed over the "
             "ring was applied to the live file alone, and nothing was lost only because the backup "
             "was written and verified first. The plan now names the corpus it judged and the apply "
             "refuses when that corpus moved. Also pinned: a backup name must carry its SOURCE, "
             "because 'sessions.<stamp>.jsonl' is fine for one file and silently collides the "
             "moment two ring generations are backed up in the same second, leaving the earlier one "
             "with no backup while the log says it has one."),
    Gate("test_the_amnesty_covers_only_the_past",
         [sys.executable, os.path.join(HERE, "test_the_amnesty_covers_only_the_past.py")], 180,
         why="KONYO'S AMNESTY COVERS WHAT PREDATES THE INSTRUMENT, AND NOTHING AFTER IT. His ruling "
             "2026-09-14, after being shown that 'drain to 8' and his own earlier condition "
             "contradict each other: 'it can go.. whatever was in the past for here specifically "
             "its fine.. just make sure forward it is all working'. MEASURED before asking him: "
             "reel_tombstones.json's earliest deletion is 2026-08-24 23:49 and 2,385 of the 2,424 "
             "unknown rows - 98.4% - are runs that STARTED BEFORE THAT, so their film was gone "
             "before any instrument existed to record it going. No record was ever written and none "
             "can be manufactured, which is why his condition could never be satisfied for them and "
             "why they would be held forever. THE CUTOFF IS DERIVED FROM THE LEDGER'S OWN FIRST "
             "ENTRY, never a constant: a hardcoded date is a number nobody can re-derive and one "
             "that keeps being true as the tree moves, while reading the ledger means the amnesty "
             "covers precisely 'older than the instrument' and a run that started after it existed "
             "is NEVER covered however old it later becomes - the forward half enforced by "
             "arithmetic rather than intention. Measured after: releasable 215 -> 2,292, and 30 "
             "unknown rows that post-date the ledger are STILL HELD. An unreadable ledger grants NO "
             "amnesty, because a boundary nobody can compute may not be assumed on a path that "
             "deletes. And the amnesty does NOT waive the only-trace hold: a row that is the only "
             "copy of a find is a different concern from a row with no retention record, and he "
             "ruled on the second."),
    Gate("test_a_row_that_is_the_only_trace_is_never_released",
         [sys.executable, os.path.join(HERE, "test_a_row_that_is_the_only_trace_is_never_released.py")], 180,
         why="A JOURNAL ROW THAT IS THE ONLY TRACE OF WHAT A REEL FOUND MAY NEVER BE RELEASED. He "
             "approved the river's deletion on 2026-09-14 with one string attached - 'i agree "
             "delete.. just make sure before it was tallied and extracted properly' - and this is "
             "that sentence as a RULE rather than a check somebody ran once. MEASURED on his live "
             "journal before the rule existed: of 447 rows the planner would have released, 245 "
             "still carried payload (finds, tallies, intakes, named, chron, registered, topFind), "
             "207 of those had their reel recorded in the sweep memory so the READ survives the "
             "row, and 38 appeared in NO bank at all - several carrying finds and topFind. The film "
             "is already gone for every one of them, so the row is what is left and nothing else "
             "names the reel; deleting it is not tidying, it is forgetting. The film gate already "
             "enforces the same sentence one step upstream: reel_retention refuses to tombstone on "
             "zero-pages ('that is this reader found nothing, not done') and on panels-never-banked, "
             "whose comment quotes him directly. UNKNOWN HOLDS - a bank that could not be read is "
             "not an empty bank, and on a path that deletes those must never share a branch. And "
             "the bank reader DELEGATES to control_app._chron_swept_mem rather than joining the "
             "path itself, because control_app's own v2139.1 scar names this exact file: a third "
             "reader joined it from HERE and bypassed TV_CHRON_SWEPT, _CHRON_SWEPT_PATH and "
             "TV_HIST, so two fixtures that patched the path still read LIVE data."),
    Gate("test_the_bump_refuses_a_tree_that_does_not_parse",
         [sys.executable, os.path.join(HERE, "test_the_bump_refuses_a_tree_that_does_not_parse.py")], 300,
         why="THE VERSION STAMP IS THE MOMENT THE TREE BECOMES SOMETHING HE EXECUTES, SO IT MUST "
             "PARSE FIRST. This exists because I put a SyntaxError on his LIVE screen through this "
             "exact door: a splice in bible.html used `}} catch(e){{}}` as its END anchor and left it "
             "behind, then bump_version happily stamped v3100 onto a file the browser refuses to "
             "parse - and HIS CONSOLE EXECS THE WORKING TREE, so window.renderSubMeter was never "
             "assigned on his screen until the second eye found it on the shipped diff. The gate "
             "that catches this ALREADY EXISTED: js-syntax is registered here and parses every "
             "surface in a real engine. I ran visual_lock_invariant after the edit, because that is "
             "what had refused the push, and not the one that asks whether the file still parses. "
             "Adding laws does not fix a law nobody runs, so the check moved to the CHOKE POINT: "
             "every change passes through the version bump, four stamps move together or none do, "
             "and that block already promised 'nothing touches disk until all four are known good' "
             "while 'known good' meant only that a regex matched. It now ast.parses the two python "
             "surfaces, json.loads WINDOWS_SHIP, and hands bible.html to js_syntax_gate itself "
             "rather than growing a second copy of the script extractor. It also parses the ONE "
             "line the tool generates, because `note` is free text landing inside a single-quoted "
             "JS string and the two guards above it (apostrophe, callable CSS token) are a list of "
             "past accidents rather than a parser. ORDER IS PINNED TOO - a check after the writes "
             "is a report about damage, not a guard - and the first red-proof puts the literal "
             "v3100 defect back into bible.html and demands the bump refuse it."),
    Gate("test_the_grok_chip_paints_on_every_path",
         [sys.executable, os.path.join(HERE, "test_the_grok_chip_paints_on_every_path.py")], 120,
         why="THE GROK CHIP MUST PAINT WHEN CLAUDE IS UNMEASURED, AND A CEILING OF 0 MUST NOT LOOK "
             "UNMEASURED. The second eye's two HIGHs on the shipped v3099 diff, both verified in "
             "the file before a line changed. v3099 fixed the PRODUCER - _meter_lanes now runs on "
             "every return of _meter_state, so /api/meter carries lanes.grok even where claude has "
             "never written its ledger - and the CONSUMER was still shut: bible.html's "
             "renderSubMeter did `if (!known){ ... return j; }` at 52817-52822 and the grok paint "
             "sat at 52848, below it. So on exactly the machine v3099 exists for (grok primary, "
             "grok shadow, a fresh checkout, CI) the payload arrived and the chip was never drawn - "
             "the same unjoined end, one layer down. Second: `_ghm or None` turned a ceiling of 0 "
             "into None while paint() writes the same '-' for any falsey max, so the circuit that "
             "refuses EVERY read was drawn identically to a lane nobody measured - off, unknown and "
             "switched-off-at-the-budget are three facts and two shared pixels. THIRD, WHICH NOBODY "
             "REPORTED AND IS MINE: the early call is legal only because paintGrok is a hoisted "
             "function DECLARATION; rewriting it as `const paintGrok = () =>` - the modern habit, "
             "and a change any reviewer waves through - throws a TDZ ReferenceError inside a try, "
             "killing the chip silently on the one path this exists to fix. All three pinned, the "
             "block located by BRACE MATCHING rather than a fixed window."),
    Gate("test_the_cap_names_the_window_that_tripped",
         [sys.executable, os.path.join(HERE, "test_the_cap_names_the_window_that_tripped.py")], 120,
         why="A CAPPED READ LANE MUST NAME THE WINDOW THAT IS FULL, AND `atCap` MUST MIRROR THE "
             "LANE'S OWN REFUSAL. Found by the second eye on the SHIPPED v3092 diff and both halves "
             "reproduced before a line was changed. The meter grew a second lane precisely so that "
             "'switched off' and 'at its ceiling' could never be drawn alike - after the Grok lane "
             "sat at 201 of a 200 daily cap refusing every read while the console showed nothing - "
             "and the lane it added carried the same class of defect twice. MEASURED against the "
             "real predicates: tv_diablo._sub_budget_check and g5_grok_eyes._budget_ok both refuse "
             "on ANY max <= 0, on hour >= hourly, and on day >= daily; the meter asked only "
             "'armed and day >= dailyMax' for claude and required the tripped max to be > 0 for "
             "grok. So an HOURLY exhaustion read as healthy on the Claude lane, and a ceiling of 0 "
             "- the state where every read is rejected outright - read as healthy on BOTH. And "
             "when it did fire the sentence named the wrong window, printing 'grok (4000 of 20000 "
             "today) is AT ITS CEILING' for an exhausted HOUR: a correct number under a word that "
             "had stopped being true, on the one line whose whole job is to say there is no "
             "headroom. This law tests the JOIN rather than a copy of the rule, and BOTH halves are "
             "now actually driven - the eye caught the first cut claiming both and driving only "
             "grok: _budget_ok across a ten-cell grid (10 of 10 agree) and _sub_budget_check "
             "end-to-end on a temp ledger through _meter_state (6 of 6 agree), including the "
             "boundary cell where a call at EXACTLY 3600.0s old is outside `< 3600` and inside "
             "`<= 3600` - the old meter said AT ITS CEILING there while every read was allowed. "
             "v3099 also closes the High the eye found on v3098: the lanes were built BEHIND "
             "claude's ledger check, so on a machine where claude has never read - grok as "
             "primary, grok as shadow, a fresh checkout, CI - the GROK lane was not published at "
             "all, the watchdog said UNKNOWN instead of WARN, and the Tools chip was never drawn. "
             "Grok records into a DIFFERENT file and its loader already fails open; the dual meter "
             "was simply one door behind the other lane's ledger. Reproduced before the fix (lanes "
             "NONE PUBLISHED) and pinned here. It also pins the mirror-image lie - an unarmed lane "
             "refuses nothing and must never read as capped - and that UNKNOWN is a VALUE rather "
             "than a missing field, since the honest-absent grok shape used to omit capWindow and "
             "capText entirely."),
    Gate("test_the_render_fixture_can_reach_the_card_branch",
         [sys.executable, os.path.join(HERE, "test_the_render_fixture_can_reach_the_card_branch.py")], 120,
         why="A FIXTURE THAT CANNOT EXERCISE THE BRANCH DOES NOT GO QUIETLY GREEN - IT GOES LOUDLY "
             "RED AT THE PRODUCT, AND SOMEONE EVENTUALLY BLESSES OVER IT. The `shelf-cards` render "
             "target refused for six versions with 'never matched a painted element in 20s', and "
             "the product was fine the whole time: a cross-family LOOK at his live console the same "
             "night counted 17 cards / 12 visible. Booting the render sandbox and asking it settled "
             "it in one call - /api/sessions returns 357 rows and ALL 357 carry "
             "footageState:'unknown' with footageN:0, so 0 of 357 would render a card. Two correct "
             "decisions had met: since v3092 the shelf routes a film-less run OUT of the grid into "
             "the history chips, which is what he asked for ('make sure those no footage end up "
             "tombstoned and then deleted also visually and ends up HISTORY'), and _serve_console "
             "points TV_HIST at an EMPTY frames dir because tv/frames/hist is 5.6 GB and copying it "
             "is an ENOSPC incident this repo has already paid for. The card branch was therefore "
             "unreachable BY CONSTRUCTION. render_check now seeds synthetic film - 285 bytes x 3 on "
             "the newest 24 runs, into the sandbox only, never his tree - and this law pins all "
             "five halves of it: the stills are written in the shape control_app COUNTS, on the "
             "NEWEST runs because the grid is newest-first and a card at the bottom of a 4,120px "
             "scroller cannot measure the fold defect, as real JPEG bytes rather than empty files, "
             "with the join pinned from control_app's own side by PARSE so renaming `reel_` or "
             "`f_` fails HERE instead of silently emptying the grid again, and with the blessed "
             "floor held between the structural minimum (2 unconditional nodes per card) and what "
             "the world can paint with every optional line present. MEASURED after the seed: "
             "\U0001f7e2 49/49 painted, 0 clipped, 0 off, 0 covered, at all five widths."),
    Gate("test_a_journal_row_leaves_only_on_proof",
         [sys.executable, os.path.join(HERE, "test_a_journal_row_leaves_only_on_proof.py")], 120,
         why="A JOURNAL ROW MAY LEAVE ONLY ON A PROOF OF EXTRACTION, AND THE PLANNER MAY NEVER "
             "WRITE. He asked for the river to end in tombstone then deletion 'after being "
             "extracted' - that last clause is the whole law, and there is no un-delete. MEASURED: "
             "the REEL river is already finished (20 on disk, ROUTED 20 which the router calls the "
             "REAL tombstone, TOMBSTONE 0 meaning none have left the disk - correct, since the 20 "
             "are 8 he keeps + 9 the suite pins + 3 held). His shelf still shows 419 rows because "
             "it lists JOURNAL sessions and a row outlives its film. plan() reports 446 releasable "
             "on a `retired` state - the retention lane's own proof that the film gave up its "
             "information first - and holds 2,325 that say `unknown`, which is no film AND no "
             "retention record: an absence of evidence in BOTH directions, never permission. Also "
             "held: the newest 8 whatever their state, rows a test pins by name, rows whose reel "
             "still has film, and rows that cannot be dated. The planner is PARSED to prove it "
             "cannot write - no open-for-write, no remove, rename or rmtree anywhere in it."),
    Gate("test_a_card_with_no_film_says_so",
         [sys.executable, os.path.join(HERE, "test_a_card_with_no_film_says_so.py")], 120,
         why="A CARD WITH NO FILM MUST SAY SO, IN WORDS. MEASURED by GROKBOT on his live console "
             "at 1470x923: the top INTAKE/TRIAGE cards paint chrome, titles, dates and "
             "READS/FOUND rows while the thumbnail slot is CONTINUOUS BLACK; deeper cards show "
             "real thumbs, so those runs simply have no film. Every instrument called the shelf "
             "green - GET reported shelf.open true, 430 cards, 425 visible, filled true, "
             "emptyHero false, theatre painted+ink true - because a card that is present, "
             "measurable and EMPTY is the one shape a GET check cannot fail on. Only eyes saw it. "
             "The answer was already on the wire: /api/sessions carries footageState "
             "(retired|unknown) and a footageWhy sentence, and `footageState` appeared in ZERO "
             "html files. The `noimg` branch's 'placeholder gradient' is #1a160d -> #0c0a06 with "
             "no text, so 'no film' and 'the image failed' render identically and neither speaks. "
             "RETIRED and UNKNOWN must never share a label: retired means the film gave up its "
             "information and was then released - the lifecycle that WORKED, 449 of his runs - "
             "while unknown means no film and no retention record at all, 2,423 runs. Collapsing "
             "them lets a run that was never filmed wear the badge of one that finished."),
    Gate("test_a_declared_trace_must_be_one_the_loop_writes",
         [sys.executable, os.path.join(HERE, "test_a_declared_trace_must_be_one_the_loop_writes.py")], 120,
         why="A LOOP DECLARED TO LEAVE A TRACE MUST ACTUALLY WRITE THE FILE DECLARED. v3076 gave "
             "four loops a second witness via lane_trace, taking ALL FOUR organs from 9 surfaces "
             "to 12 - and every one of those cells is a DECLARATION. A declaration with nothing "
             "behind it is the coverage v3055 deleted. Worse, the failure is SILENT: if a declared "
             "path and the path lane_trace writes differ by one character, _trace_age finds no "
             "artefact and the row reads UNKNOWN for ever, which is not red anywhere - the organ "
             "would look reasonable while corroborating nothing. This pins the join from both "
             "ends by PARSING control_app.py (the call, not a string in a comment) and by "
             "computing the path from lane_trace.path_of rather than re-typing it, and refuses a "
             "declared period shorter than the writer's own throttle. It also pins the case that "
             "made his healthiest console read as broken: _orphan_exit_loop is ALWAYS dormant on "
             "a console nobody started, so DORMANT plus an absent tick is two witnesses AGREEING, "
             "while dormant-and-ticking is the real defect."),
    Gate("test_the_tooltip_split_may_only_add_pages",
         [sys.executable, os.path.join(HERE, "test_the_tooltip_split_may_only_add_pages.py")], 120,
         why="SPLITTING A RUN ON THE TOOLTIP MAY ONLY EVER ADD PAGES. v2396 splits a still run on "
             "the tooltip so a hover-by-hover pass stops collapsing into one page, and claims it "
             "'splits on evidence and leaves the rest alone'. It did not: MIN_RUN_FRAMES is a "
             "STILLNESS floor calibrated on UNSPLIT runs, and applied to the fragments it can "
             "discard every candidate a reel had. MEASURED on the reel s_1788099999528_42457 - 4 "
             "frames, 1 run and 1 candidate before the split; 2 runs and ZERO after, both under "
             "the 3-frame floor. A forced re-sweep read 0 pages, called classify 0 times and the "
             "reader 0 times, while the free structural gate opened all 4 frames as `shared` and "
             "the survey counted 4 panels. The reel could never bank a row, so the river held it "
             "forever. The fallback restores the pre-split grouping WITH the same floor - it does "
             "not remove the floor, and a reel with no candidates either way still reads nothing."),
    Gate("test_an_examined_panel_is_not_an_unread_one",
         [sys.executable, os.path.join(HERE, "test_an_examined_panel_is_not_an_unread_one.py")], 120,
         why="A PANEL THAT WAS READ AND HELD NO NAMES IS NOT A PANEL NOBODY READ. The river could "
             "not drain and `eligible` had NEVER fired once: 8 reels sat on panels-never-banked, "
             "and the rule holding them asked only whether the survey saw panels and whether the "
             "reel was in the durable stores - never consulting the seal, though its own comment "
             "says it exists for 'the state a seal-with-no-rows leaves behind'. A reel whose "
             "panels carry no readable NAME can never enter those stores, so the answer was True "
             "forever. Those panels are unreadable CORRECTLY: a stash GRID prints no names at "
             "all, only the hover tooltip does, and one of the eight is a Shared stash page 5/5 "
             "with ~25 items on screen. The asymmetry was the defect - the examined_empty flag "
             "was reachable only from the branch taken when a pass grounded NOTHING, so the same "
             "reel released when swept alone and was held forever when swept beside one "
             "productive neighbour. Only frame_authority.seal_releases_frames may lift the hold; "
             "a default 'nothing was taken' seal and an unreadable store both still KEEP the "
             "footage, because there is no un-delete."),
    Gate("test_a_loop_that_ticks_must_leave_a_trace",
         [sys.executable, os.path.join(HERE, "test_a_loop_that_ticks_must_leave_a_trace.py")], 120,
         why="A LOOP THAT CLAIMS TO RUN MUST HAVE LEFT SOMETHING BEHIND. Ten surfaces sat at 3 of "
             "4 organs, ALL missing the corroborator, because that organ needs TWO independent "
             "witnesses and six of the eight loops leave nothing an outside reader can date. Two "
             "do - the ledger backup loop and the vault autoread loop - and this covers exactly "
             "those two, leaving the other six honestly ABSENT rather than filled with an "
             "invented trace. It refuses two rots: a fresh tick with an ancient trace ceasing to "
             "be a contradiction (a loop running and producing nothing), and an UNREADABLE tick "
             "read as a dead loop - lane_liveness._TICKS is in-process on a monotonic clock, so "
             "any other process sees it empty and would otherwise report healthy loops broken."),
    Gate("test_a_lock_may_not_bank_more_attacks_than_it_declares",
         [sys.executable, os.path.join(HERE, "test_a_lock_may_not_bank_more_attacks_than_it_declares.py")], 120,
         why="A SOURCE MAY NOT BANK MORE ATTACKS THAN IT DECLARES - the arithmetic his vault rests "
             "on. score() clears a bar on wilson_lower(min(k, attacks), attacks), computed on "
             "DISTINCT attacks because Wilson cannot tell 83 independent looks from one attack run "
             "83 times; an overstated `attacks` buys a lock open on refusals nobody earned, and "
             "that same arithmetic took vault.apply from locked to OPEN. Compared PER SOURCE, "
             "never per lock: reel.route's 34 is 7 from reel_router_wilson plus 27 from "
             "rung_accounting_wilson, and a per-lock total would flag a HARDENED lock as 5x "
             "inflated. An unreadable declaration is UNKNOWN, never a violation."),
    Gate("test_a_stale_prover_is_not_a_safety_verdict",
         [sys.executable, os.path.join(HERE, "test_a_stale_prover_is_not_a_safety_verdict.py")], 120,
         why="WRITING ONE GATE SHUT NINETEEN LOCKS, and that is why most of them were never wired "
             "to anything. may() asks _heart_says_watched() before it asks about the surface, and "
             "that fails closed when the census is STALE — which it becomes the moment any GATE "
             "FILE changes. Measured 2026-09-12 in one session of writing gates: the census staled "
             "FOUR times and every lock answered may=False with the census sentence rather than "
             "anything about itself. Wiring may() into action sites on top of that would mean "
             "editing a test takes features off his console until a ~38-minute re-prove. His "
             "ruling splits by REVERSIBILITY: an act that cannot be undone keeps the whole "
             "guarantee (five locks carry destructive:True, each justified by its own `acts` "
             "string — 'deletes footage — there is no undo', 'drops the ledger', 'the last check "
             "before deletion', 'mules items between characters', 'starts a paid sweep'), while an "
             "act that reports, walks or decides refuses on MERIT alone, because an out-of-date "
             "instrument says nothing about whether THAT surface earned the right to act. ⚠ BLIND "
             "IS NOT STALE and never softens — a gate that cannot fail is a fact about supervision "
             "and refuses everything. ⚠ heart_block_kind() matches TEXT, so this gate PARSES "
             "self_arming and proves both phrases still live inside _heart_says_watched's own "
             "body: a silent reword would classify every stale census as 'other' and refuse "
             "everything again, quietly."),
    Gate("test_a_frame_label_is_not_an_item_location",
         [sys.executable, os.path.join(HERE, "test_a_frame_label_is_not_an_item_location.py")], 120,
         why="ONE FRAME LABEL WAS STAMPED ONTO A WHOLE LIST OF ITEMS, and that is why the wrong "
             "things registered. Konyo: 'it was working exactly like that just not registering the "
             "right items based on the routing.' The defect was one line: `cur[\"panel\"] += "
             "len(names)` — a deep row carries ONE scene and a LIST of names, and in D2R the stash "
             "panel and the inventory are open TOGETHER, so a single frame legitimately holds "
             "items from BOTH containers. read_names_lane was fixed for this in v2983 and RECORDS "
             "the per-item container; extract_gap never read it (measured: `loc` 0 references, "
             "`scene` 1). MEASURED on his journal: stash/inventory 56, stash/stash 12, "
             "inventory/inventory 31, inventory/floor 7, stash/floor 1, stash/equipped 2, "
             "inventory/equipped 1 — so ELEVEN names that can never be a holding counted as panel "
             "and FIFTY-SIX inventory items were filed under stash. ⚠ AND `stash` IS NOT A "
             "CONTAINER AN ITEM IS READ IN: his ruling, 'stash/stash there is no such thing.. when "
             "stash is open the INVENTORY IS OPEN at the same time' — items already in the stash "
             "are not what gets read, so such a placement is counted CONTRADICTED and named, never "
             "folded into panel. ⚠ And the fallback is not uniform: a CHRONICLE frame IS its names "
             "so falling back is safe (it keeps his 154), while a PANEL frame would pick a "
             "container by coin-flip, so an unplaced name there stays UNPLACED. Before -> after on "
             "his real journal: panel 110 -> 87, floor 208 -> 216, equipped 3, contradicted 12, "
             "unplaced 0, names 472 unchanged — every name in exactly one bucket."),
    Gate("test_the_card_says_why_the_list_is_missing",
         [sys.executable, os.path.join(HERE, "test_the_card_says_why_the_list_is_missing.py")], 120,
         why="v3169 fixed the cross-reference SENTENCE so it stopped saying Dean had not reported "
             "when he had. The CARD - the thing he actually hovers - stayed silent: counts, a "
             "one-word verdict, and no word about the per-item mask being absent or why. So the "
             "card and the panel disagreed about how much this console knows. MEASURED before "
             "this shipped: maskWhy appeared 5 times in control_app.py and ZERO times in "
             "control_ui.html - published by the server on every fleet row, read by nothing. "
             "This law drives the SHIPPED block in node and pins: the reason is rendered; ONE "
             "machine state is named ONCE with its ledgers grouped (Dean carries {sets: no board "
             "window, uniques: no board window} and printing it per ledger reads as two separate "
             "faults); two DIFFERENT reasons are both kept; a row with nothing to explain does "
             "not grow an empty line; a falsy reason is not a reason; and the text is ESCAPED, "
             "because a fleet row is remote input from another machine."),
    Gate("test_reported_counts_is_not_no_report",
         [sys.executable, os.path.join(HERE, "test_reported_counts_is_not_no_report.py")], 120,
         why="HIS CORRECTION, 2026-09-15. The cross-reference panel said \"Dean has not reported "
             "which set pieces it holds yet... It publishes on its next heartbeat\" while his own "
             "fleet card, in the same screenshot, read DEAN SETS 131/135. He said: \"dean already "
             "synced his sets something is regressed here\" and then \"i m saying that he has it "
             "even says it here\". MEASURED on the live /api/fleet: Dean carried tally.sets "
             "{have 131, total 135} and maskWhy {sets: no board window}, masks None. The sentence "
             "was wrong twice - he DID report (the COUNTS were on the wire; only the per-item "
             "MASK was missing, so the panel can count but not name), and the promised heartbeat "
             "CANNOT deliver, because a machine with no board window fails identically on every "
             "beat until one is open. A false 'just wait' turns a fixable condition into an "
             "invisible one. maskWhy was published by the server and rendered ZERO times. This "
             "law pins both halves and the original case too: a genuinely silent machine is still "
             "named UNHEARD rather than zero, and a reported ZERO (Dean's real uniques 0/403) "
             "counts as a measurement, not a silence - `if _have:` instead of "
             "`isinstance(_have, int)` is the realistic regression and it is one of the six "
             "sabotages this file was seen RED under."),
    Gate("test_a_missing_row_never_claims_it_does_not_know",
         [sys.executable, os.path.join(HERE, "test_a_missing_row_never_claims_it_does_not_know.py")], 60,
         why="HIS ORDER reading the state panel, 2026-09-15: \"everythin should be reading healthy "
             "if its not missing and those that are are being fixed ... so its honest\". MEASURED: "
             "`tooltip finder` returned MISSING while its own sentence read \"the finder has never "
             "been asked - no frame has been put through it, so nothing is known about it either "
             "way\". An unexercised lane is not a broken lane, and MISSING feeds WHAT NEEDS YOU, "
             "so it was inflating the one number he acts on. This walks the doctors' ASTs for "
             "`return MISSING, <str>` and fails when the string admits it never looked - the "
             "console's oldest doctrine (0 is measured, None is nobody looked) enforced by the "
             "file instead of by memory. It carries its own blind-fixture proof: a planted "
             "offender in a throwaway module must be caught, because a guard that cannot see a "
             "violation is measuring nothing."),
    Gate("test_a_decoded_empty_is_not_unknown",
         [sys.executable, os.path.join(HERE, "test_a_decoded_empty_is_not_unknown.py")], 60,
         why="FOUND BY THE CODEX EYE reviewing v3175 (cross-family, openai/gpt-5.6-terra): \"a "
             "valid empty local item list is rendered as unknown/unpublished. In fleet_compare, "
             "`if _mine_names` treats an empty successfully decoded list ...\" It is right, and "
             "it is the scar the surrounding comment already cites. fleet_mask.decode() returns "
             "None when the answer would be a GUESS and [] when the mask decoded cleanly and he "
             "owns none of that ledger; an empty list is FALSY, so a real measured zero was "
             "folded into \"this console published no mask\". This panel exists to keep exactly "
             "one distinction — I have none of these vs I could not find out — and the console "
             "has had to correct that confusion repeatedly (UNIQUES SYNCED over 0/403 in v2875, "
             "the both-need column refusing rather than claiming 0 in v3022). Getting it wrong in "
             "the code that DRAWS the distinction is the worst place for it. ⚠ He owns 132 of 135 "
             "today, so his own data never exercises this branch — a gate blind to what his data "
             "never exercises is the exact failure this pins. The laws drive the SHIPPED "
             "fleet_compare with a SIDE-AWARE decode stub: the first cut stubbed both sides, so "
             "theirs decoded cleanly too, compare() returned ok:True and the branch under test "
             "never ran — the law failed against correct code and the FIXTURE was at fault."),
    Gate("test_the_river_is_one_flow_of_eight",
         [sys.executable, os.path.join(HERE, "test_the_river_is_one_flow_of_eight.py")], 120,
         why="HIS ORDER, 2026-09-15, with four screenshots of the shelf: \"all these anyways need "
             "to end up unified in one section after being extracted one step behind deleted "
             "after flowing from top to bottom.. its still in sections each reel in a diffrent "
             "place\", and when asked whether older runs stay scrollable below: \"no only the "
             "last 8 sessions stay and the one coming in pushes the last one out of those 8 "
             "sections\". ⚠ THIS SUPERSEDES v2746, WHICH WAS ALSO HIS — that ruling asked for "
             "sections down the page, intake to tombstone, and was built faithfully; he watched "
             "it run and ruled the other way. The station is NOT lost, it moved onto the card "
             "where .shc-river has stamped it since v2746; what goes is the GROUPING. The laws "
             "DRIVE the shipped block in node against stub cards and pin: newest flows first so "
             "top-to-bottom is downstream; exactly 8 flow and the 9th is marked data-river-out "
             "and hidden; a PIN does not eat a flow slot (he pins deliberately, and silently "
             "shortening the river to honour a count he set for the flow would be the console "
             "overruling him); ONE header, not one per station; the header says how many were "
             "pushed, because runs vanishing with no denominator read as data loss; and the "
             "TOMBSTONE mouth figure survives the section that carried it — a closed-out reel "
             "leaves the disk and becomes a retention-ledger row, which is why its section could "
             "only ever read 0 cards, and dropping it would re-tell the lie v2963 fixed (410 "
             "finished journeys reading as nothing ever finished). ⚠ The pin law was GREEN under "
             "its own sabotage on the first cut — pins sort to the top so a single pin is inside "
             "the first eight either way; it now tests the slot, which is what the guard does."),
    Gate("test_the_node_venue_is_not_silently_absent",
         [sys.executable, os.path.join(HERE, "test_the_node_venue_is_not_silently_absent.py")], 60,
         why="FOUND BY THE CODEX EYE reviewing v3170 (cross-family, openai/gpt-5.6-terra), and it "
             "was right: a law that drives shipped JavaScript converts a missing node into "
             "skipTest, and unittest counts a skip as not-a-failure. The pattern is the HOUSE "
             "STYLE, not a new mistake - `skipTest(\"node unavailable - a skip is NOT a pass\")` "
             "sits at 26 sites across 9 law files and the message already knows the hazard. But 26 "
             "quiet skips is not a report: if node ever leaves a venue, every law that executes "
             "the page in a real engine stops asserting AT ONCE and the suite still prints OK - "
             "regression-guard's green-that-lies, with the HOST MACHINE as the fixture at fault. "
             "So rather than rewriting 26 call sites into failures, ONE law asserts the venue, by "
             "name, and reports how many files would have gone silent. It also checks that a node "
             "on PATH actually RUNS, because present is not working. PROVEN RED by stripping node "
             "from PATH (it lives in two places on his Mac - /usr/local/bin and "
             "/opt/homebrew/bin, so the first proof attempt stayed green and the sabotage, not "
             "the law, was wrong)."),
    Gate("test_the_sweep_reads_the_reels_that_have_something",
         [sys.executable, os.path.join(HERE, "test_the_sweep_reads_the_reels_that_have_something.py")], 180,
         why="THE REASON HIS VAULT HAS NO RECEIPTS. MEASURED 2026-09-15: 45 sessions swept, 36 of "
             "them (80%) took NOTHING, 39 rows banked in total - while the three best stash-panel "
             "reels, one at 100% density, had NEVER BEEN SWEPT. The stash bank held 12 keys "
             "against the chronicle bank's 8517 sightings over 324 names. The sweeper took reels "
             "in DIRECTORY ORDER filtered only by 'not already sealed'. Both signals it needed "
             "already existed and neither was joined to it: vault_retro.panel_density (free - a "
             "crop and an OCR, whose own docstring says it exists so 'the sweep can afford to ask "
             "it about every reel before paying to read any of them') was computed ONLY inside a "
             "doctor row that PRINTS it; and _vault_owed_reels() - the ROUTING system's answer, "
             "tag intersect READ_CLEARS - was never consulted by the sweep either. ⚠ THE TWO "
             "SIGNALS DISAGREE: the router named 5 owed reels and NOT ONE was the 100%-density "
             "reel, because an untriaged reel carries no tag and is invisible to the owed list. "
             "Either alone misses half the work, so the sweep now orders owed-first then by what "
             "the frames actually show. This law pins the ordering, that an unmeasurable reel "
             "sorts LAST (never promoted over one we could measure), that ties keep their order, "
             "that a ranker failure falls back instead of killing the lane, that the doctor and "
             "the sweeper share ONE ranker, that an unreadable bank is UNKNOWN not zero, and that "
             "all four organs (doctor/heart/watchdog/eagle) watch it. ⚠ One of these laws was "
             "BLIND on its first cut - it asserted 'rank_by_panel' appears in the function source "
             "and the explanatory COMMENT above the call satisfied it, so deleting the real call "
             "left it green. Now it parses for an actual Call node. Parse, never grep."),
    Gate("test_the_removal_door_is_undoable",
         [sys.executable, os.path.join(HERE, "test_the_removal_door_is_undoable.py")], 180,
         why="HIS ORDER, 2026-09-15: a board-side removal door with the same care as "
             "chronicleApply \u2014 dated, listed, undoable, stamped once. #96 has to take ~150 "
             "backfilled names out of d2r_owned and the only remover that existed was "
             "vaultUnown(name): one name, one render, one save, NO RECORD, and an undo that "
             "lived only in his memory. v3168 adds vaultRemove(names[]) + vaultRestoreLast() "
             "and ROUTES the one-click path through the same door, so every removal on the "
             "board is journaled to d2r_vaultRemoved (ring of 20, the same depth "
             "d2r_chronApplied uses). The laws DRIVE the shipped function bodies in node \u2014 "
             "not a paraphrase \u2014 and pin: a name the board does not hold is `skipped` not "
             "`removed`; the locker assignment is recorded and given back, because an undo that "
             "returns the item UNFILED has lost where it lived while looking like it worked; a "
             "name he re-ticked himself is LEFT ALONE, chronicleUndoLast's own rule mirrored; a "
             "batch cut on another ledger is REFUSED and stays undoable on its own board, "
             "because v2692 is that hazard in the other direction and it reached his cousin's "
             "board; and the journal forks exactly like d2r_owned, which is in neither fork set. "
             "10 laws, every one seen RED by a sabotage that deletes the real thing. The heart "
             "organ check_vault_removals watches the JOIN, not just the door: if the one-click "
             "path ever stops routing through it, single removals go back to leaving no record "
             "while the batch count still looks healthy. #246 review: an undo and the socket-count "
             "rename put a filing back as a RESTORE - the witness row it had, verbatim, or none; one "
             "undo had minted 'placed by hand' for 172 found-ever filings. 3 red-proofs"),
    Gate("test_the_vault_receipt_is_watched",
         [sys.executable, os.path.join(HERE, "test_the_vault_receipt_is_watched.py")], 120,
         why="HE ASKED FOR A RECEIPT ON A VAULT ITEM AND PUSHED BACK WHEN I SAID NOTHING WAS "
             "BUILT — he was right. The console already carries the whole apparatus: a "
             "cursor-following frame float on `.rc-art`, a full-HD viewer on the `.rcpt-ic` eye "
             "reading the real on-disk /hist/<frameId>.jpg, and a route-to-source click; the "
             "evidence store already records {reel, frame, lane} per sighting. What never existed "
             "is the INTRODUCTION — the vault emits NONE of those hooks, so a row in a locker "
             "cannot show the frame that witnessed it. Built, correct, joined to nothing, and "
             "nothing watched the join, which is why it stayed invisible until he remembered it. "
             "MEASURED: 172 owned, 153 filed, ZERO carrying a sighting — a row with no receipt "
             "looks identical to one with a reel behind it, which is how 150 rows from a retired "
             "found-ever backfill sat in his lockers looking like real finds."),
    Gate("test_the_fleet_card_is_asked_again_when_he_looks",
         [sys.executable, os.path.join(HERE, "test_the_fleet_card_is_asked_again_when_he_looks.py")], 120,
         why="#82 — HIS CARD READ SETS 131/135 WHILE HIS BOARD HELD 132. Every trigger it had "
             "painted it ONCE: _fleetKick at load, the v2851 ladder only AFTER a failed fetch so "
             "never from a good-but-old reading, and the button only when pressed. A number true "
             "at load, shown in the present tense — REG-815 again, and this card has already lost "
             "a trigger once before (it refreshed when the ADVANCED drawer filled, the card was "
             "moved OUT of that drawer, and its refresh stayed behind). ⚠ THE FIX IS AN EVENT, "
             "NEVER A SHORTER POLL — his ruling. visibilitychange + focus cost nothing while he "
             "is elsewhere and fire exactly when the card is about to be read; the same pair the "
             "v2348 heartbeat uses, because WebKit suspends timers in a hidden window. This law "
             "holds all four halves: both triggers, the throttle that stops one alt-tab firing "
             "twice, and a standing refusal to put the card on a timer."),
    Gate("test_the_restore_proposal_reaches_the_board",
         [sys.executable, os.path.join(HERE, "test_the_restore_proposal_reaches_the_board.py")], 120,
         why="#81 — THE RESTORE'S TWO HALVES WERE JOINED BY A COMMENT. ledger_restore builds the "
             "proposal and the board's `window.chronicleApply` is the only door it may travel "
             "through, and between them sat one sentence in a test — 'the board reads "
             "proposal.wouldAdd and nothing else' — asserted nowhere. Rename that key on EITHER "
             "side and the old shape law stays green while the apply posts a payload the board "
             "reads as EMPTY and reports the board's own ok. This law measures the join: the key "
             "the restore writes against the key the board's own source reads, brace-matched so a "
             "fixed window cannot report a key as absent that is merely past its end. ⚠ It does "
             "NOT prove an end-to-end apply: chronicle_apply calls the live board WINDOW and "
             "cannot be sandboxed, and the board is whole (missingTotal 0 against 446/446), so a "
             "real apply would mean deleting one of his finds to manufacture a gap. That half "
             "stays honestly UNPROVEN rather than faked."),
    Gate("test_a_skipped_file_is_never_an_absent_name",
         [sys.executable, os.path.join(HERE, "test_a_skipped_file_is_never_an_absent_name.py")], 120,
         why="FOUND BY THE SECOND EYE ON THE SHIPPED v3151 DIFF, and it was damage from that "
             "ship's own fix. v3151 memoised `_defined_anywhere` because it re-parsed every "
             "tv/*.py per NAME — 11.0s of a 12.7s heart.vessels(), which is what had been "
             "dropping the heart targets out of the render gate. But the cache key is built from "
             "os.stat BEFORE the parse loop, so a file that stats and then fails to OPEN was "
             "dropped from the set and that short set was stored as a finished answer. `kind_of` "
             "returns FOREIGN — not ours, stop watching — only when `_defined_anywhere` is False, "
             "so an fd-exhausted console would cache an EMPTY set and classify every dotted "
             "in-package target FOREIGN for the rest of the process, with the census reading "
             "complete the whole time and no stat able to move to let it recover. The pre-v3151 "
             "code swallowed the same exception PER CALL and a later census still saw the file — "
             "caching is what turned transient into permanent."),
    Gate("test_every_lane_stamps_its_own_beat",
         [sys.executable, os.path.join(HERE, "test_every_lane_stamps_its_own_beat.py")], 120,
         why="#80 — EVERY WATCHER LANE IS A `while True` LOOP WHOSE WORK SITS INSIDE "
             "`except Exception: pass`, so the beat it stamps is the ONLY thing that makes it "
             "visible to lane_liveness and through it to the heart. Delete the beat and the lane "
             "keeps running, keeps failing silently, and reports UNKNOWN forever — nobody looked, "
             "which reads as fine and is worse. Twelve lanes had no sabotage evidence of their own "
             "because evidence is credited per DEF SPAN and only six of the 163 proofs naming "
             "control_app.py landed inside a watcher loop. The twelve proofs here each delete ONE "
             "lane's beat, so each counts for that lane and no other. ⚠ The second assertion was "
             "MEASURED before it was written: tvd-runaway-watch really does stamp its function "
             "name and tvd-ledger-backup really does sleep on a computed wait — both legal, and a "
             "law demanding the registry name would have flagged correct design as a defect."),
    Gate("test_lane_attacks_are_per_lane",
         [sys.executable, os.path.join(HERE, "test_lane_attacks_are_per_lane.py")], 120,
         why="#80 — TWELVE WATCHER LANES COULD NOT BE SCORED AT ALL, because no organ row named a "
             "single `tvd-*` lane and a vessel inherits the score of the organ that names it. The "
             "fix is a routing organ, and the trap it must never fall into is the cheap version of "
             "itself: 163 RED_PROOFs name control_app.py and exactly SIX land inside one of the "
             "twelve watcher-loop def spans. Handing every lane the file's tally would have "
             "published FLOWING 20/20 out of evidence that never touched nine of them. This law "
             "holds the three properties that keep it honest — a sabotage credits ONLY the lane "
             "whose def span it lands in, the published score is the WEAKEST named lane's rather "
             "than the sum, and a lane attacked-and-never-refused is never named as a surface so "
             "it cannot inherit a proven lane's score."),
    Gate("test_flowing_is_unmeasured_not_zero",
         [sys.executable, os.path.join(HERE, "test_flowing_is_unmeasured_not_zero.py")], 120,
         why="THE HEART PRINTED `flowing 0` WHILE EVERY VESSEL ROW SAID NOBODY COULD TELL. FLOWING "
             "means 'it runs, something watches it, AND a sabotage has proven the watcher can "
             "refuse'. No vessel has ever earned it, and each row said why — 'watched, and NOTHING "
             "CAN SCORE THIS WATCHER' — while the legend rendered that as a confident zero, which "
             "reads as 'none are flowing' rather than 'nobody can tell'. ⚠ AND IT CANNOT BE EARNED "
             "TODAY BY ANY VESSEL: measured 2026-09-12, the organ rows this census scores from "
             "carry NO score field at all (keys: evidence, id, line, measuredAt, state, surfaces), "
             "so `scored` is {id: None} for all seven and even a perfect key match returns None. "
             "The old comment blamed disjoint vocabularies; that is true and not the whole truth. "
             "It is a MISSING MEASUREMENT, not a missing quality. ⚠ The perfusion wash cannot "
             "carry the difference — with FLOWING null it draws no flowing stop, which looks "
             "IDENTICAL to zero — so the words in the legend are the only place it can live, and "
             "`(c.FLOWING || 0)` flattened them because null || 0 is 0 in JS. ⚠ AND THE LEGEND WAS "
             "PHOTOGRAPHED BY NOTHING until the heart target's selector was widened past "
             "`.hrt-h, .hrt-row`: the contradiction between the rows and the count sat on his "
             "screen and no instrument here could have seen it."),
    Gate("test_a_tick_filed_under_a_lane_name_still_counts",
         [sys.executable, os.path.join(HERE,
          "test_a_tick_filed_under_a_lane_name_still_counts.py")], 120,
         why="THREE VESSELS REPORTED 'no tick has been stamped under this name' WHILE STAMPING "
             "PERFECTLY WELL. Measured on his live console 2026-09-12, stable across two "
             "consecutive samples with zero drift: FLOWING 13, DORMANT 3, UNKNOWN 3, UNTIMED 1 — "
             "and the three unknowns were _console_beacon_loop, _retro_triage_loop and "
             "_warden_loop. All three call _lane_tick; two file it under the LANE's name rather "
             "than the FUNCTION's (_retro_triage_loop -> 'tvd-retro-triage', _warden_loop -> "
             "'tvd-space-warden'). _live_of looked up the watcher then the vessel name, neither "
             "of which is 'tvd-retro-triage', so a MISS was rendered as 'never started' about a "
             "lane that was beating. The lanes are now DERIVED from each function's own body with "
             "ast — 21 functions stamp today and a table beside the code would have to be "
             "remembered into every time one is renamed. ⚠ The first cut of that reader returned "
             "[] for everything SILENTLY: heart.py imports only os and sys, the reader called "
             "io.open, the NameError was swallowed by a broad except, and every function read as "
             "stamping no lanes — indistinguishable from a measured absence. The cache keeps the "
             "failure REASON now. ⚠ And the half that must not soften: a vessel whose lanes are "
             "genuinely silent still reads UNKNOWN, or this would turn every unwatched thread "
             "green."),
    Gate("test_a_lock_that_gates_nothing_is_not_a_lock",
         [sys.executable, os.path.join(HERE, "test_a_lock_that_gates_nothing_is_not_a_lock.py")], 120,
         why="NINETEEN LOCKS SCORED, DISPLAYED, AND GATED NOTHING. self_arming.may() was consulted "
             "at exactly THREE call sites in the whole tree — all three about console.pixel_rescue "
             "— while nineteen locks computed Wilson scores, drew padlocks on the heart, and "
             "stopped nothing. The arithmetic was real; the authority was imaginary. ⚠ And it "
             "could not simply be wired, which is why it sat: may() asks the heart first and that "
             "fails closed on a STALE census, which happens whenever a GATE FILE changes — "
             "measured FOUR times in one session of writing gates, every lock answering may=False "
             "about the census rather than itself. v3042's reversibility split is what made wiring "
             "safe. This gate pins the SEATS, one per lock, at the place state actually changes: "
             "printer.stream in printer.stream(), reel.route in reel_route_lane.apply() (NOT "
             "reel_router.route(), which derives a station and writes nothing — a guard on a "
             "thought is not a guard), vault.sweep_start in chronicle_sweep_start(), and "
             "prune.reports inside the CLAIM test in disk_history_append(), because that lock "
             "guards the REPORT while prune.arm guards the deletion and a guard on the whole "
             "function would stop him seeing his own free space. ⚠ It also refuses a "
             "vault.sweep_start refusal that wears the `busy` shape: callers treat busy as "
             "contention and RETRY, so a locked door in that shape is retried forever. Parsed with "
             "ast — a lock named in a comment must not satisfy a law about whether the code ASKS."),
    Gate("test_the_cross_reference_asks_one_question",
         [sys.executable, os.path.join(HERE, "test_the_cross_reference_asks_one_question.py")], 180,
         why="HIS CROSS-REFERENCE READ 160/398 BESIDE A BOARD THAT SAYS 292/403 — TWO WRONG "
             "HALVES. NUMERATOR: fleet_mask's uniques spec still pointed at `d2r_owned` (the VAULT "
             "store) while control_app:1997 repointed the TALLY to the chronicle pair at v2717 and "
             "renamed the old measure `vaultUniques`; sets was immune because both its sides read "
             "d2r_setPieces, which is why one tab was right and the other wrong. And it is a "
             "UNION: bible.html's _ownedNames() IS the definition of found — d2r_owned plus "
             "keys(d2r_foundLog), 'ledger + LEGACY owned' — so a single store would be correct "
             "only by coincidence. DENOMINATOR: the panel printed rosterN=398, of which "
             "bible.html:3757 says 'produced by neither, and NO array on the page is this size'. "
             "⚠ rosterN CANNOT become 403 — decode() refuses a mask whose n != len(roster), the "
             "equality that proves both machines packed the same bit positions — so 403 got its "
             "own field and does NOT fall back. ⚠⚠ AND THE FIX HAD A LANDMINE AIMED AT ITSELF: "
             "corroborate held a SECOND hardcoded ledger->store map with 'uniques' absent, so its "
             "dynamic left side would count uniques the day this shipped while its frozen right "
             "side would not — the invariant reddening because the code got MORE correct. It now "
             "asks surface_pairs(). PROOF THE FIX IS RIGHT: with uniques no longer excluded the "
             "invariant names the defect itself — Konyo uniques tally 292 vs popcount 160. "
             "12 laws, 10 sabotages RED."),

    Gate("test_a_sighting_says_which_surface",
         [sys.executable, os.path.join(HERE, "test_a_sighting_says_which_surface.py")], 180,
         why="TWO LOOKS AT DIFFERENT SURFACES ARE NOT A CONTRADICTION, AND TWELVE OF HIS WERE "
             "ABOUT TO BE. His ruling: 'chron_evidence - widen it, one confluence store'. Every "
             "row in that store is chronicle-scene BY CONSTRUCTION (chronicle_kind refuses "
             "non-chronicle pages; the live-lane converter skips them), while the deep reader "
             "produces names across SIX scenes that no corroboration store receives. MEASURED: 12 "
             "names sit in notFound AND were seen by the deep reader on a PANEL surface - "
             "Goldwrap, Magefist, Wraithstep, Radament's Sphere, Credendum, Dark Adherent, Rite of "
             "Passage, Bramble Mitts, Death Mask + 3 bases. resolve_contested joins the two sides "
             "BY NAME ONLY on pure timestamp arithmetic, and its `not-found` verdict says 'the "
             "found reading is the suspect one' - so a real stash sighting would have been blamed "
             "by a menu page that had not registered the item yet. Step 1 stamps `scene` at all "
             "THREE mint sites; step 2 adds a `cross-scene` verdict at the ONE choke point. ⚠ NO-OP "
             "ON SHIP DAY: it fires only when BOTH sides know their scene and disagree; absence is "
             "UNKNOWN, never a default, so none of his 8,300 existing rows is re-graded. Named "
             "`scene` not `surface` because `loc` and witnesses()'s surface_of already answer to "
             "that with a narrower vocabulary. 8 laws, 6 sabotages RED."),

    Gate("test_the_vault_witness_holds_two_readings",
         [sys.executable, os.path.join(HERE, "test_the_vault_witness_holds_two_readings.py")], 180,
         why="I TOLD HIM THE VAULT'S WRITE PATH RE-GATES. ON THE BUTTON HE PRESSES, IT DOES NOT. "
             "vault_apply's re-gate lives inside `if caller_supplied`, and the console posts "
             "body:'{}' deliberately ('the engine already holds the gated result'). That rests on "
             "one buried assumption - that the stored result was gated under the law in force NOW "
             "- and merge_vault/_absorb merge-max forever without ever calling gate() again. "
             "MEASURED: 6 of 7 stored OWNED rows could not clear the bar they were displayed "
             "under; pressing 'register 7' would have applied all seven. His ruling unified the "
             "bar to 2 the same day so those are legitimate now, but the STRUCTURAL hole is "
             "untouched - the next bar change recreates it silently. The pair: the stored claim "
             "beside a re-gate of the SAME evidence at today's constants, AGREE/CONTRADICTION/"
             "UNKNOWN, never averaged. ⛔ Age is context, never a verdict - his proposal lives on "
             "disk across restarts by design. PROVEN AGAINST REALITY: AGREE at today's bar of 2, "
             "CONTRADICTION naming exactly the six rows when set back to 3. 9 laws."),

    Gate("test_the_shelf_shows_the_mouth",
         [sys.executable, os.path.join(HERE, "test_the_shelf_shows_the_mouth.py")], 120,
         why="THE SHELF'S TOMBSTONE SECTION SAID 'never reached' OVER 410 COMPLETED JOURNEYS. The "
             "river view prints every station including the empty ones, deliberately — but it "
             "counts CARDS, and at TOMBSTONE that can only ever be 0 because a closed-out reel "
             "LEAVES THE DISK and becomes a row in the retention ledger. MEASURED: 410 tombstoned, "
             "5,768.1 MB reclaimed, overlap with the 40 living reels EXACTLY ZERO. ⚠⚠ AND THE CSS "
             "WOULD HAVE PRINTED THE CONTRADICTION IN ONE LINE: .sh-riverempty appends "
             "' · never reached' to any station with no cards, so the header read 'TOMBSTONE · "
             "never reached · 410 closed out' — the false claim beside its own refutation. The "
             "mouth now suppresses that ::after and is not dimmed, ONLY when the ledger actually "
             "holds rows (the other direction of the same lie). null is not zero: 'ledger not read "
             "yet' and an unreadable ledger each say so rather than rendering as none finished. "
             "8 laws, 7 sabotages RED — two of which were VACUOUS on the first run: one asserted "
             "against the raw file and matched its own explanatory comment (5th prose-trap today), "
             "the other checked one of two TOMBSTONE scopes and survived on its twin."),

    Gate("test_the_river_has_a_mouth",
         [sys.executable, os.path.join(HERE, "test_the_river_has_a_mouth.py")], 180,
         why="I REPORTED THAT THE RIVER NEVER REACHED ITS END. IT HAS REACHED IT 410 TIMES. "
             "reel_router._station_of returns TOMBSTONE zero times in code and the census reads "
             "counts.TOMBSTONE 0 with unreached [INTAKE,TRIAGE,ROUTED,TOMBSTONE] — and I reported "
             "that as 'the river has no mouth'. MEASURED, the opposite: the tombstone ledger holds "
             "410 closed-out reels reclaiming 5,768.1 MB, and the overlap between them and the 40 "
             "living reels is EXACTLY ZERO, because a tombstoned reel LEAVES THE DISK and stops "
             "being something the router can station. The router was answering a different "
             "question and I read its answer as the answer to mine. ⇒ The mouth is read from the "
             "LEDGER and never manufactured in the router, which keeps "
             "assert_independent_of_retention() intact — a living reel's position still comes only "
             "from its own reading evidence. Pins: mouth on the payload and in the SUCCESS branch; "
             "no router import in river_mouth's CODE (the law was fooled by its own docstring "
             "first — 4th time this session, now an ast-based _code_of helper); a missing ledger "
             "is UNKNOWN with n=None, never 0 journeys; FIFO by deletedTs with UNDATED rows "
             "sorting LAST and counted separately. 8 laws, 6 sabotages RED."),

    Gate("test_the_river_walk_says_it_walked",
         [sys.executable, os.path.join(HERE, "test_the_river_walk_says_it_walked.py")], 180,
         why="A SUCCESSFUL WALK THAT FOUND NOTHING SAID NOTHING, so a STILL RIVER and a DEAD LOOP "
             "looked identical. Konyo asked for the shelf drawn as the river, 'honest and accurate "
             "and pinpointed .. visually synced to the backend' — and the thing it would draw was "
             "not measurable. _retro_triage_loop already walked every tick and reported TWO of "
             "three outcomes: transitions when something moved, 'NOT WALKED' when it failed; a "
             "successful walk finding nothing printed nothing and stored nothing. MEASURED: 40 "
             "stamps, ALL by claude:first-wiring, newest 12.8h old, 0 of 40 carrying a `from` — "
             "not one row ever written by the loop, which is equally consistent with 'the river is "
             "still' and 'the loop never runs'. The walk now records that it RAN — when, reels "
             "compared, moved INCLUDING ZERO — and publishes it on /api/status, because recording "
             "it in a global and shipping nothing to a surface is the defect control_app's own "
             "v2457 note describes. ⛔ The doctor row does NOT redden on a calm river (most ticks "
             "find nothing, by design); it reddens when the WATCHING stops. 10 laws, 6 sabotages "
             "RED including the original bug (state written inside the moved-branch)."),

    Gate("test_an_empty_ledger_is_not_synced",
         [sys.executable, os.path.join(HERE, "test_an_empty_ledger_is_not_synced.py")], 120,
         why="HIS CATCH: 'SYNCED' SAT DIRECTLY ABOVE '0 / 403 found' ON DEAN'S FLEET CARD. "
             "SYNCED is defined as 'this ledger's rows were earned on this board' and there were "
             "no rows — the label outlived its referent. His sets (130) and runewords (96) were "
             "non-zero, which is why four provenance answers looked sufficient for so long. Added "
             "a FIFTH, UNSYNCED, at BOTH sites that stamp SYNCED (fixing one and leaving the "
             "other is this repo's most repeated defect). ⚠ IT IS NOT UNKNOWN: this module's own "
             "doctrine is '0 IS MEASURED-AND-ZERO, None IS NOBODY LOOKED', and somebody DID look "
             "at Dean's store and found nothing — collapsing that into UNKNOWN throws a real "
             "measurement away. The law pins both directions (a populated declared ledger still "
             "reads SYNCED), pins that an UNREAD store stays UNKNOWN, pins that the card has a CSS "
             "rule so the new value does not render unstyled, and pins that the constants block "
             "stopped claiming 'there is no fifth'. 5 sabotages RED."),

    Gate("test_the_stage_agrees_with_the_dom",
         [sys.executable, os.path.join(HERE, "test_the_stage_agrees_with_the_dom.py")], 180,
         why="3,090 CARDS BUILT, THE CONSOLE CALLING ITSELF PAINTED, AND HE WAS LOOKING AT BLACK. "
             "His order: 'connect it to the heart of the console too'. MEASURED live: shelf {open, "
             "filled, cards 3090} and theatre {open, loaded, painted, ink} while the room was dead. "
             "The shelf door had ALREADY been hardened three times for this same complaint (v2446 "
             "swallowed, v2451 toggles, v2666 prove-from-the-RECT) and every one of those guards "
             "proves the DOCUMENT - `painted` and `ink` are DOM measurements wearing pixel names, "
             "blind to a stale composite. The pixel witnesses missed it too: paint_witness reads "
             "the WHOLE window and said PAINTED (header/rail/footer were lit), and region_witness "
             "at its shipped 3x2 had every cell catching a lit edge. Measured on that dead window: "
             "3x2->0 blank, 4x3->0, 6x4->0, 8x5->2, 10x6->7, which is why GRID is 8x5. So neither "
             "side is evidence alone and THE DISAGREEMENT IS THE FINDING. Reads only - no "
             "relaunch, repair or click, proven from the AST. 10 laws incl. both directions, the "
             "cry-wolf case (nothing open = OK) and the unlookable-window UNKNOWN."),

    Gate("test_the_paint_pass_survives_a_dead_raf",
         [sys.executable, os.path.join(HERE, "test_the_paint_pass_survives_a_dead_raf.py")], 120,
         why="THE CURE FOR A STALE COMPOSITE WAS SWITCHED OFF IN THE ONE STATE THAT CAUSES IT. He "
             "sent a screenshot of a black room: 'shelf isnt rendering when clicked either'. Both "
             "shell entry points repeat the demote/restore pair inside requestAnimationFrame, "
             "commented 'one more paint tick: WebKit sometimes keeps the last full-viewport "
             "composite' - and rAF DOES NOT FIRE in a window WebKit thinks is hidden. MEASURED on "
             "his live console via /api/status while he looked at the black room: hidden true, "
             "painting false, frozenBeats 29, blankStrikes 0, els 84,514. The DOM was intact and "
             "correct; the pixels never followed. blankStrikes 0 is why the existing rescue never "
             "armed - the window is not BLANK, it is STALE. AND 'hidden' did not mean he was not "
             "looking: an OCCLUDED pywebview window (his Terminal overlapped it) reports hidden "
             "while plainly on screen. Two wrong fixes are recorded in the file: a global "
             "body-opacity nudge (27 position:fixed elements would reparent) and firing the pair "
             "from visibilitychange (_shellRestoreConsole drops shell-open and would kick him out "
             "of the board tab he was reading). 6 laws, 5 sabotages RED."),

    Gate("test_a_sidecar_does_not_reowe_a_read",
         [sys.executable, os.path.join(HERE, "test_a_sidecar_does_not_reowe_a_read.py")], 120,
         why="#25 (v3298) — A MOVED DIRECTORY IS NOT MOVED FILM. kai_report.json bumps the reel "
             "dir mtime with zero frame change and used to re-buy a read of unchanged film — the "
             "retirement deadlock's minting mechanism. BOTH halves pinned and SEEN RED on HEAD: "
             "a sidecar-only touch reads owes=False (was True), and a prune-then-capture at EQUAL "
             "count still reads owes=True (the case the strict dir stamp exists for, kept)."),
    Gate("test_a_skipped_periodic_check_still_emits_a_row",
         [sys.executable, os.path.join(HERE, "test_a_skipped_periodic_check_still_emits_a_row.py")],
         120,
         why="#35 (v3298) — a PERIODIC check skipped this tick EMITS an UNMEASURED not-asked row "
             "instead of vanishing 5 of 6 ticks — 'engines corroborate' is the sole caller of "
             "corroborate.verdict(), so its silent absence was supervision downtime. SEEN RED on "
             "HEAD (KeyError: the row simply did not exist). Also pins the sidecar MERGE keeping "
             "SLOW readings, and that a placeholder never persists as a measurement."),
    Gate("test_read_names_lane",
         [sys.executable, os.path.join(HERE, "test_read_names_lane.py")], 180,
         why="TWO READERS, ONE BANKING STORE, AND ONLY ONE WAS WIRED TO IT. His question: 'if it "
             "witnessesed three times it automatically tallys itself right?' The auto lane DOES "
             "exist (vault sweep -> vault_accum -> vault_retro.gate -> vault_apply -> the board's "
             "own tick), but vault_accum is written only by a PAID SWEEP, while the 119 unbanked "
             "names came from the DEEP reader's journal. They were never refused - they were never "
             "JUDGED. MEASURED on his journal: 42 PANEL names, 3 clear the bar, 15 could ever tick "
             "(UNIQUE 9 / SET 5 / RUNEWORD 1), 24 never. THE THREE THAT CLEAR THE BAR ARE THE "
             "THREE THAT CAN NEVER TICK - his ruling names why: 'locked inventory only.. the tombs "
             "and the hordaic cub', carried permanently so present in every session by "
             "construction. They are 58 of 110 sightings (52.7%) while the 15 real names are 20. "
             "So manual is the path for ALL FIFTEEN. This module REPORTS AND NEVER WRITES: banking "
             "releases footage for pruning (rows-not-banked), and the write ban is proven from the "
             "AST, not grepped. 11 laws incl. both red directions and the unreadable-roster zero "
             "that this very build produced."),

    Gate("test_the_two_deleters_share_one_window",
         [sys.executable, os.path.join(HERE, "test_the_two_deleters_share_one_window.py")], 120,
         why="SWEPT AFTER v2752 — TWO DELETERS, TWO INDEPENDENT `KEEP_RECENT = 5`, AND NOTHING LINKED THEM. "
             "Found by sweeping for the shape of v2752 (a constant that outlived its instrument); "
             "this is its cross-module twin, one rule written down twice: frame_authority.py:52 "
             "and reel_retention.py:47, near-identical prose, no link. ASYMMETRIC AND THAT IS THE "
             "POINT: retention deletes whole REELS, frame_authority strips FRAMES. Raise "
             "retention to 10 for safety and leave frame_authority at 5, and reels 6..10 survive "
             "as directories WHILE BEING GUTTED of their frames — the reel list still shows them, "
             "the disk figure still drops, and protection reads as INCREASED while being partial. "
             "Demands EQUALITY, not >=, because the dangerous direction is retention > authority. "
             "Behavioural half runs the real recent_reels over real directories (host-independent: "
             "it only globs and sorts, unlike reel_retention.plan which reads a witness index from "
             "HERE — the v2750 host-dependency). Proven RED on 5 sabotages including BOTH drift "
             "directions and an equality satisfied by setting both to 0."),

    Gate("test_chrome_alone_is_not_paint",
         [sys.executable, os.path.join(HERE, "test_chrome_alone_is_not_paint.py")], 120,
         why="v2752 — HIS BLACK CONSOLE READ AS *PAINTED* BECAUSE OF TWO ROWS OF WINDOW CHROME. He "
             "sent a screenshot of a black window: 'black screen again.. something should be "
             "catching this'. Nothing was. MEASURED on that window (pid 4333, 1120x660) while "
             "blank: crop 30 -> bright 0.0159, p99 255, PAINTED; crop 32 -> bright 0.0000, p99 27, "
             "BLANK. EVERY one of the 63 bright samples sat at y=30 EXACTLY — the title bar's "
             "bottom border at luminance 255 — which is 1.59% of the frame, a hair over the 1.5% "
             "ink bar, and it also dragged p99 to 255. ⚠ CHROME_TOP_PX=30 was correctly derived "
             "against the MODAL test, where leftover chrome only DILUTES; the INK test added later "
             "asks whether ANY pixel is bright, and two rows of 255 answer yes forever. The "
             "threshold outlived the instrument. ⚠ And the second witness did not cover for the "
             "first: region_witness saw all six cells blank but returns half=False for a FULLY "
             "blank window, deferring to the whole-window witness — the blind one. Both are fixed. "
             "6 laws, 6 sabotages RED, including reverting the crop to 30 AND to 31."),

    Gate("test_the_witness_can_see_half_a_window",
         [sys.executable, os.path.join(HERE, "test_the_witness_can_see_half_a_window.py")], 180,
         why="v2747 — his Sessions tab lost ~1080x560 of its MAIN COLUMN while the rail painted "
             "fine, and the only instrument watching for a blank console could not see it: "
             "paint_witness asks about the WHOLE WINDOW, so content anywhere means 'not blank'. "
             "PROVEN by his own fault log — 21 faults that day, 16 of them blank-pixel, and ZERO "
             "within 45 minutes of the 20:14 sighting. region_witness measures a GRID (named "
             "regions derived from it, never measured separately, so they cannot drift) and can "
             "say 'this half is drawn and that half is not'. ⚠ Three things testing on his real "
             "machine changed: samples 24->40 (a cell flipped BLANK->PAINTED with sample count), "
             "strikes over consecutive looks (moving blank cells = repainting, refused), and an "
             "OCCLUSION guard — Safari covered 100% of his console while this was built, and a "
             "one-sided cover would have fired about a healthy window. ⚠⚠ That guard was PRESENT "
             "AND INERT at first: occluded_by returns a TUPLE, not a dict with a 'state' key. "
             "8 sabotages, all proven RED."),

    Gate("test_a_dead_fill_keeps_its_content",
         [sys.executable, os.path.join(HERE, "test_a_dead_fill_keeps_its_content.py")], 120,
         why="v2746 — his Sessions tab lost ~1080x560 of content and then self-resolved on a "
             "restart, which means NOBODY MEASURED THE CAUSE. The obvious suspicion (a fill that "
             "blanks on a failed fetch) was REFUTED: _tzPaint already repaints the last recorded "
             "zone with stale:true and _chronXref already repaints _chronLastSt. This pins that "
             "correct behaviour so it cannot regress, pins the OTHER direction too (a genuine "
             "empty must still say 'no rotation available', or the fix becomes stale-forever), and "
             "closes the unguarded `console_ui_two_script_blocks` scar in control_ui.html — a call "
             "across the block boundary is a DEAD RENDER and it has happened four times. ⚠ The "
             "probe for that scar was itself wrong twice: a bare name( regex counted "
             "classList.add() as a call, and `<script` matched an occurrence INSIDE A JS STRING at "
             "~14102, which would have published '0 violations' over an incomplete corpus. All six "
             "laws proven RED by in-memory sabotage; the file on disk is never mutated because his "
             "live console execs this working tree."),

    Gate("test_a_found_row_carries_its_evidence",
         [sys.executable, os.path.join(HERE, "test_a_found_row_carries_its_evidence.py")], 180,
         why="v2746 — t133/t166. d2r_foundLog is 419 rows of DISPLAY STRINGS, so a found row could "
             "not be re-verified. ⚠ The evidence was never missing and the loop was never "
             "indifferent: _chRecordApplied DOES read row.witnesses and row.seen[0] — but it writes "
             "d2r_chronicleInboxLog, a ring TRIMMED TO 400 ROWS while his foundLog holds 419, so the "
             "oldest proof is already being evicted and an inbox row was never joined to a ledger "
             "row. A sibling store d2r_foundEvidence now carries the proof beside the date. ⚠⚠ The "
             "law it exists for: null = NOBODY LOOKED, [] = looked and corroborated nothing. "
             "Array.isArray is the whole distinction; one `||` collapses them forever. A hand tick "
             "writes NO ROW and reads back null. Retraction at all four doors, because v1891/v1963 "
             "already paid for that rule four times. 13 sabotages, every one MATCHES=1, 12 of 12 "
             "laws seen RED."),

    Gate("test_ledger_authority",
         [sys.executable, os.path.join(HERE, "test_ledger_authority.py")], 180,
         why="v2746 — ONE authority over all four seeds (_GRAIL_SEED 245 · _SET_SEED 108 · "
             "_RWC_SEED 99 · _RULING_SEED 10), parsed from bible.html at runtime so a seed that "
             "grows cannot make it lie. It caught an arithmetic trap: _GRAIL_SEED and _RULING_SEED "
             "SHARE NINE NAMES, so the uniques seed is a UNION of 246, not the sum 255. Feeds the "
             "doctor rows `ledger provenance` and `ledger staleness`, both RED on real data."),

    Gate("test_the_river_carries_a_stamp",
         [sys.executable, os.path.join(HERE, "test_the_river_carries_a_stamp.py")], 180,
         why="v2746 — reel_router answers WHERE A REEL IS and remembers nothing, so a reel had a "
             "POSITION and never a JOURNEY. river_stamp is the only member of the family that "
             "writes: append-only, one row per station actually reached, deduped so a walk over a "
             "still river writes zero bytes."),

    Gate("test_the_never_fired_rules_can_fire",
         [sys.executable, os.path.join(HERE, "test_the_never_fired_rules_can_fire.py")], 180,
         why="v2750 — reel_retention.plan() reports its own blind spot: 5 rules NEVER REACHED on "
             "his 40 reels (no-witness-index, never-chronicle-swept, rows-not-banked, vault-owes, "
             "eligible) because `zero-pages` catches 27 of 40 and a PAID READ is what clears it. "
             "That made a circle: his money ruling says a paid pass runs AFTER the consuming path "
             "is proven, but the path could not be proven without pages, and pages cost money. A "
             "fixture of five synthetic reels — one per rule — walks the REAL chooser and settles "
             "it for nothing: 5 of 5 fire correctly, so the rules were never broken, only never "
             "reached. ⚠ REG-570 is what makes it honest — before it, plan(hist_dir=) read his LIVE "
             "401-entry ledger and ignored the caller's, so every sabotage aimed at this chooser "
             "was graded against data it could not control. ⚠ keep_recent=0 is deliberate AND a "
             "limit: `recent`/`test-fixture` sit above the subject, so this proves FIVE rules, not "
             "eight, and a law asserts those two still report as never-fired rather than implying "
             "the chain is wholly exercised. 5 sabotages, all RED."),

    Gate("test_read_names_are_banked",
         [sys.executable, os.path.join(HERE, "test_read_names_are_banked.py")], 180,
         why="v2751 — 119 ITEM NAMES WERE READ FROM HIS FOOTAGE AND NONE ARE BANKED. MEASURED: "
             "PRINTER 11 reels / 64 names with NO SEAL AT ALL, JOIN 4 reels / 55 names under a seal "
             "that does not carry them. The printer says it per reel: 'N item name(s) were read, but "
             "this session has no seal at all, so the extraction contract was never even asked about "
             "it.' ⚠⚠ THE READING ALREADY HAPPENED — the names are in the JOURNAL RING right now "
             "(Andariel's Visage, Atma's Wail, Bartuc's Cut-Throat, Sandstorm Trek) — so NO PAID "
             "READ IS OWED, and the row says so, because without that sentence a reader reaches for "
             "the paid lane. ⚠ It reports PANEL separately per his filter (472 corpus names split "
             "PANEL 110 / FLOOR 208 / CHRONICLE 154, 77% filtered): a floor name has no cell to "
             "name, so it is a sighting not a holding, and one number over both overstates the work. "
             "⚠ Two fault kinds stay separate — 'no seal at all' is a lane that never ran, 'sealed "
             "but blind' is a code problem. ⛔ The row REPORTS and never writes: banking lands in "
             "vault_accum/vault_seen, witness-gated on purpose, feeding a deleter with no un-delete. "
             "9 laws, 9 sabotages ALL RED, and green under a fresh-checkout simulation."),

    Gate("test_the_printer_reach_is_watched",
         [sys.executable, os.path.join(HERE, "test_the_printer_reach_is_watched.py")], 120,
         why="v2749 — `grep -c printer_reach` was 0 across control_app.py, console_doctor.py, "
             "corroborate.py and control_ui.html: the THIRD module in three versions found built, "
             "correct, and read by nothing. It answers the question his 3/4D-printer ask opens "
             "with — how much of the corpus the pipeline can act on. MEASURED: reels 437, seals 31, "
             "joined 21, sealsSatisfyingContract **0**, with name/location/provenance missing on "
             "all 31. ⚠⚠ The row exists because a reader seeing ZERO CONTRADICTIONS concludes the "
             "pipeline is healthy: it is not, the contract refuses every seal so the contradiction "
             "CANNOT ARISE. It names the missing FACTS because they imply different work — a "
             "missing `name` is a reader change, a missing `location` is a CAPTURE question (0 of "
             "1,065 deep rows carry a cell) and HIS ruling. ⚠ Its own gate caught a crash in the "
             "UNKNOWN path: `(r or {}).get` raises on a truthy non-dict, so an UNKNOWN written to "
             "survive a bad report crashed on one — and the same shape was then swept out of the "
             "end-route and river rows in the same pass. 8 sabotages, all RED."),

    Gate("test_the_end_route_is_watched",
         [sys.executable, os.path.join(HERE, "test_the_end_route_is_watched.py")], 120,
         why="v2748 — `grep -c end_routes` was 0 in control_app.py, console_doctor.py, "
             "corroborate.py AND control_ui.html: the derived end-route predicate was built, "
             "correct, covered by 27 of its own tests, and read by nothing but its own gate line. "
             "That is the SAME defect this heart caught in reel_router ONE VERSION EARLIER — the "
             "river's unjoined end was fixed and its sibling left running. The doctor row `end "
             "routes reachable` is RED today at 32 of 40 and NAMES WHAT THEY LACK (panels read 32, "
             "chronicle pages 32, a vault seal 18), because a count alone is not actionable. ⚠ It "
             "keeps DEAD-ENDED separate from FINISHED-WAITING: counting both would read 40 of 40 — "
             "true, useless, and ignored within a week. ⛔ No wilson lock: whether a reel can reach "
             "an end route is a reading, not a claim attacks can refute. 7 sabotages, all RED."),

    Gate("test_end_routes",
         [sys.executable, os.path.join(HERE, "test_end_routes.py")], 180,
         why="v2746 — gh210. His ruling settled the DESTINATION (reels should reach their end "
             "routes) and not the PREDICATE (what makes a reel qualify), so the predicate is "
             "derived from the reels that already completed rather than invented. ⚠ ROUTED has a "
             "measured population of ZERO today, which is why the derivation cannot simply read "
             "reels sitting at that station."),

    Gate("test_the_verdict_reaches_the_card",
         [sys.executable, os.path.join(HERE, "test_the_verdict_reaches_the_card.py")], 120,
         why="v2746 — MEASURED on his live /api/fleet: Dean onOwnerSeed=True AND **Konyo "
             "onOwnerSeed=True**, and the card warns on a bare `=== true`. So HIS OWN CARD told him "
             "his 292 uniques were 'inherited, not synced'. The flag is right; the sentence over it "
             "means something else. The card now reports the authority's PER-LEDGER verdict, which "
             "is true on either board and can DISPROVE inheritance (Dean's runewords: the seed can "
             "supply 99, the store holds 94 - 5 missing, so it was never seeded). This walks all "
             "THREE hops because v2739 shipped this exact defect: it computed onOwnerSeed on the "
             "board and read it on the card while functions/api/console.js silently dropped it."),

    Gate("test_the_river_is_wired_to_the_console",
         [sys.executable, os.path.join(HERE, "test_the_river_is_wired_to_the_console.py")], 120,
         why="v2746 — `grep -c reel_router tv/control_app.py` was 0. The station assigner was built, "
             "correct, covered by its own suite and read by NO console code. This pins the joint: "
             "/api/river serves the journey, and the FREE triage tick walks it every 90s (never the "
             "retention pass, which deletes). ⚠ The route I first wrote read `_cen.get(\"reelIds\")` "
             "— a census key that does not exist — and would have served an EMPTY detail list over "
             "a store holding 40 reels, passing any test that only checked for a 200. ⚠⚠ And the "
             "law catching that first failed on its OWN COMMENT describing the bug, the same trap "
             "TASKS.md records for task 159; it now judges CODE with comments stripped. Eight "
             "sabotages, all proven RED, in memory only — his console execs this working tree."),

    Gate("test_the_river_is_watched",
         [sys.executable, os.path.join(HERE, "test_the_river_is_watched.py")], 120,
         why="v2742 — MEASURED heart coverage before adding any: reel_router (the station assigner, "
             "the whole per-reel stamp) had 0 corroborator invariants, 0 doctor checks, and 0 "
             "references from the console. printer the same. Built, correct, covered by its own "
             "suite, invisible to every supervision layer. This pins the two new watchers: the "
             "doctor row 'the river' (RED today at 24 of 40 — PRINTER 11, STATION 7, EMPTY 6 — and "
             "asserted to be ABLE to fail, since a row that can only be green measures nothing), "
             "and the invariant 'router-and-shelf-agree' at `==` because a router stationing FEWER "
             "reels than the shelf holds is dropping some and MORE means it invented one. Also "
             "pins that the by-design exclusions (JOIN, CAPTURE/REG-340) each carry a REASON, and "
             "that NO wilson lock was invented for a STATE — a score belongs on a claim attacks can "
             "refute, and manufacturing attacks for a reading is the inflation _hardening_gap "
             "refuses."),

    Gate("test_seed_never_reaches_another_world",
         [sys.executable, os.path.join(HERE, "test_seed_never_reaches_another_world.py")], 180,
         why="v2740 — whose finds a console may inherit, pinned in all THREE states. The seed lands "
             "only when `_seedsBelongHere = (!_isCousinShell && _D2R_LEDGER === _SEED_LEDGER)`, and "
             "until this file nothing tested it: the property rested on two `window.X =` lines and "
             "a comment. A guest is refused; a NAMED board is refused; a CLAIMED and UNNAMED board "
             "is the only way in, and bible.html:10245 already calls it 'a claimed stranger holding "
             "Konyo's 245 finds'. Measured: the RESET did not close it either — the surviving "
             "set-piece row kept the heuristic answering KonyoEndgame, and the un-tick registry "
             "cannot cover a seed name added later. Runs the REAL resolver in node; proven RED on "
             "5 sabotages, two of which first passed because the fixtures were vacuous."),

    Gate("test_every_store_read_is_routed",
         [sys.executable, os.path.join(HERE, "test_every_store_read_is_routed.py")], 180,
         why="v2740 — Konyo: 'to each profile its individual ledgers ... just needs a unified logic "
             "it already is im pretty sure'. He is right: 249 accesses route through window.LSR. "
             "What did not exist is anything keeping it that way — a new bare "
             "localStorage.getItem('d2r_foundLog') compiles, passes every other gate, and inside a "
             "guest world reads the OWNER's key. A RATCHET (83 unwaived bare lines today, may "
             "shrink, never grow) plus a hard law that no LEDGER store is read bare without a "
             "written raw-ok reason. Pointers stay bare by design — they decide the namespace."),

    Gate("test_uniques_reset_is_uniques_only",
         [sys.executable, os.path.join(HERE, "test_uniques_reset_is_uniques_only.py")], 180,
         why="v2739 — the reset button he asked for, and the two ways it could have been a lie. "
             "(1) d2r_foundLog carries SET-PIECE rows alongside uniques, so a wholesale clear "
             "would take his set-piece dates while leaving d2r_setPieces intact — invisible in the "
             "store anyone would check. (2) It is TWO ACTS: the boot path re-seeds every missing "
             "_GRAIL_SEED name on EVERY load unless the name sits in d2r_grailUnfound, so clearing "
             "rows alone reverts on the next reload while reporting success. Runs the REAL "
             "javascript in node. Proven RED on 5 sabotages. ⚠ The first fixture was VACUOUS — "
             "every seed name was also a cleared name, so each sweep covered for the other's "
             "removal and two sabotages passed 9/9; the fixture now gives each sweep a victim only "
             "it can save."),

    Gate("test_export_scopes_to_one_world",
         [sys.executable, os.path.join(HERE, "test_export_scopes_to_one_world.py")], 180,
         why="v2738 — his Backup & Share export carried OTHER WORLDS. _collectProgress strips the "
             "MACHINE fork prefixes (L· W· WL·, v684) and was never swept when v1499 added the "
             "INSTALL fork (I·<id8>· / IL·<id8>·, variable-length so no fixed slice removes it), "
             "even though bible.html:4263 already handled all five. Measured on his real backup: "
             "his owner snapshot held two guests' chronicles, and a GUEST's own rows exported under "
             "namespaced names that _applyProgress can never route home — so Dean restoring into a "
             "reinstalled browser would get nothing back. The write side had the same gap. "
             "⚠ RUNS THE REAL JAVASCRIPT in node against a synthetic store rather than grepping "
             "for a spelling; proven RED on the pre-fix code (3 of 6 laws failed). No node is a "
             "declared SKIP, never a pass."),

    Gate("test_ledger_restore",
         [sys.executable, os.path.join(HERE, "test_ledger_restore.py")], 120,
         why="v2736 — ledger_restore joins the automatic backup to the board's apply door, and it "
             "shipped in v2735 with NO suite: the orphan-suite gate catches a test file no gate "
             "runs, not a MODULE no test covers. Pins that an UNROUTED backup is never attributed "
             "to anyone (59 of his 60 files predate the route stamp), that `owned` stays out of "
             "RESTORABLE because /api/vault_apply re-gates on 3 witnesses a restore cannot have, "
             "that a restore invents no DATE, and — the finding a different model family made — "
             "that a TRUNCATED board read is UNKNOWN rather than a reported loss. Reproduced: a "
             "board holding 6000 against a 5000 sample cap reported 1000 names missing."),

    Gate("test_board_read_js_has_no_free_variables",
         [sys.executable, os.path.join(HERE, "test_board_read_js_has_no_free_variables.py")], 120,
         why="v2735 — v2731 shipped `rwMadeFull:(dump?rwFull:null)` into the board read. There is "
             "no JS variable named `dump`: dump_stores is interpolated as a bare true/false "
             "LITERAL twelve lines above. The name resolved to nothing, the WHOLE read threw "
             "'Can't find variable: dump', and his automatic ledger backup wrote ZERO files for a "
             "day while every gate stayed green — because they grade the SOURCE, and source is not "
             "a running board. This extracts the JS board_ownership actually emits, statically, "
             "and reports every identifier used but never declared. Proven RED on the real defect "
             "and four sabotages. A free variable here does not degrade one field; it kills the "
             "entire board read."),

    Gate("test_backup_loop_is_watched",
         [sys.executable, os.path.join(HERE, "test_backup_loop_is_watched.py")], 120,
         why="v2735 — grades the WATCHER, not the loop. console_doctor's `backup loop` row reads "
             "the RUNNING loop's last act from /api/status.ledgerBackup, which is where the "
             "day-long outage above was visible and where nothing was looking. The load-bearing "
             "law is that `_BACKUP_BENIGN` is an allowlist of what the loop is ALLOWED to have "
             "done rather than a list of known errors — had it been the latter, an unpredicted "
             "message like \"Can't find variable: dump\" would have fallen through as healthy. "
             "Also pins that an unanswered console and a not-yet-run loop are UNKNOWN, never OK, "
             "and that the timeout survives a COLD /api/status (measured 11.6s)."),

    Gate("test_ledger_backup_covers_every_store",
         [sys.executable, os.path.join(HERE, "test_ledger_backup_covers_every_store.py")], 120,
         why="v2731 — his automatic ledger backup ran every 10 minutes for 60 consecutive files "
             "and never copied rwMade (99 runewords) or gameFound (29), and recorded no profile. "
             "It also blinded ledger_highwater, which ratchets rwMade against snapshots that never "
             "contained it — a column that can only read UNKNOWN looks exactly like one with "
             "nothing wrong. The load-bearing law here is that gameFound is NOT graded for "
             "truncation: the board publishes no independent count for it, so the only available "
             "comparison is the copy against its own length, and a check that cannot fail reads as "
             "coverage while providing none."),

    Gate("test_heart_fan_labels_are_width_bounded",
         [sys.executable, os.path.join(HERE, "test_heart_fan_labels_are_width_bounded.py")], 120,
         why="v2729 — the heart fan places labels by INDEX and sizes them by CONTENT, and nothing "
             "compares the two. PROVEN by causing it: banking evidence into two locks changed only "
             "the NUMBERS in two labels and overlap_ratchet went 2->4 at three widths, with no code "
             "touched. This pins the WIDTH BOUNDS, which is the part checkable from source and "
             "runnable anywhere — overlap_ratchet owns the count and can only run where the live "
             "console is. It also pins that the reverted vertical-dodge pass stays reverted: it "
             "was measured at 4->5, because the fan opens downward and pushing a group down drives "
             "it into the next one."),

    Gate("test_eyebrow_never_strands_a_separator",
         [sys.executable, os.path.join(HERE, "test_eyebrow_never_strands_a_separator.py")], 120,
         why="v2728 — TWO independent cold reads on two different versions reported '· OF 383' "
             "alone on a line, neither knowing the other had. The row had been filed-not-fixed "
             "because all four options cost something; a FIFTH was never listed. The separators "
             "are plain ' · ' in a text node, so the browser can break on either side of the dot "
             "and takes the left one — binding the dot to the word before it with U+00A0 deletes "
             "that break opportunity. Proven red then green in the same page by cloning the live "
             "element and putting the plain space back: 901px went 't·' STRANDS -> 'th' clean. "
             "This also pins that nobody reaches for white-space:nowrap, which hides the "
             "separator by clipping the end of the sentence instead."),

    Gate("test_coldread_empty_is_not_broken",
         [sys.executable, os.path.join(HERE, "test_coldread_empty_is_not_broken.py")], 120,
         why="v2726 — coldread aborted its whole run because `.vrg-cols` was absent, and it was "
             "absent because renderVaultRegistered() correctly HIDES the panel in a world that "
             "owns nothing — which is every run, since render_check launches a FRESH Chrome "
             "profile on purpose. The renderer built to satisfy the second-eye gate could not "
             "satisfy it. The exemption that fixes this is the dangerous kind, so this pins that "
             "only the host's own declaration excuses a region, that a VISIBLE host missing its "
             "region still refuses, and above all that the empty branch being blamed still exists "
             "in bible.html — an exemption whose premise nobody re-checks is a permanent blind "
             "spot wearing a fix's clothes."),

    Gate("test_derived_rungs_are_not_traceless",
         [sys.executable, os.path.join(HERE, "test_derived_rungs_are_not_traceless.py")], 120,
         why="v2725 — one_funnel told four of its six rungs they left NO TRACE, while "
             "reel_retention.plan() decided every one of them for all 40 reels. Uncached was "
             "being reported as unknown, in a module whose own comments cite "
             "[[unknown-stays-unknown]] five times. The load-bearing law here is the one that "
             "keeps the discovery OUT of `passage`: four rungs turning out to be observable must "
             "not raise the number that measures whether their HISTORY is dated, or a strict "
             "verdict quietly becomes a lenient one with nobody told."),

    Gate("test_rung_accounting_wilson",
         [sys.executable, os.path.join(HERE, "test_rung_accounting_wilson.py")], 120,
         why="the harness banking evidence for `reel.route` must attack THAT lock and no other, "
             "and must refuse to bank a run it failed. It also pins that the attacks are ten "
             "distinct ideas rather than one cover map ten ways — repetition counted as breadth "
             "is exactly what wilsonByAttack exists to refuse."),

    Gate("test_frame_release_wilson",
         [sys.executable, os.path.join(HERE, "test_frame_release_wilson.py")], 120,
         why="the harness that proves the DELETION GATE must itself be unable to delete — asserted "
             "from its own source, not promised in a comment. It also pins that the lock cannot "
             "pass by refusing everything: two of the eight attacks MUST RELEASE, so a wall (which "
             "would score a perfect Wilson) fails. And that no two attacks are the same input — "
             "repetition counted as breadth is the illusion wilsonByAttack exists to refuse."),

    Gate("test_examined_empty_releases",
         [sys.executable, os.path.join(HERE, "test_examined_empty_releases.py")], 120,
         why="HIS ruling: an examined-empty reel may continue down the river 'as long as its "
             "ledgered and extracted properly'. seal_verdict had answered COVERED/EMPTY/UNEVIDENCED "
             "since v2702 and was called by ONE reporter while BOTH deciders asked the old binary "
             "question. Joined — but the obvious join was too generous: 23 of his 31 seals score "
             "EMPTY and only 17 declared examinedEmpty, the rest on the substring 'nothing'. The "
             "deciders now ask seal_releases_frames; reporters keep the looser verdict."),

    Gate("test_eyes_banner_ages_out",
         [sys.executable, os.path.join(HERE, "test_eyes_banner_ages_out.py")], 120,
         why="his EYES panel printed 'the Grok balance is exhausted' in the PRESENT TENSE beside "
             "its own admission that the error was 7d old — while 14 Grok reads succeeded that "
             "same day and the CLI answered ALIVE. `_age` was computed, rendered, and never asked. "
             "Age now decides staleness (1h bar, crossed in both directions) and raw JSON never "
             "reaches the visible line. Found by the cross-family read he required BEFORE ruling "
             "any design item out."),

    Gate("test_one_terror_level",
         [sys.executable, os.path.join(HERE, "test_one_terror_level.py")], 120,
         why="'96 terrorized' was an UNNAMED literal printed immediately right of the zone's real "
             "per-zone alvl, so it read as derived from it. Two cold cross-family reads, on two "
             "versions with two different zone pairs, both flagged it unprompted. It is NOT a "
             "formula: bible.html states 'mlvl 96 terror' for TEN researched zones spanning alvl "
             "67-85, so it is a game constant and inventing arithmetic would be a fabricated fix. "
             "Now one named constant, and this pins the name, the value, the render site and the "
             "bible's agreement."),

    Gate("test_one_chronicle_denominator",
         [sys.executable, os.path.join(HERE, "test_one_chronicle_denominator.py")], 120,
         why="the chronicle denominator was re-derived at ELEVEN sites and they disagreed on his "
             "own screen: /api/fleet returned uniques 169/398 and 292/403 six minutes apart on the "
             "same board, while the board's own meter read 258/403. Nine sites now call ONE "
             "function; two keep chronTotal and the carded total apart on purpose (_darkN, "
             "_uniLeft) and this pins their ARITHMETIC, not their names — a sabotage that zeroed "
             "_darkN left the first cut green."),

    Gate("test_version_stamps_are_written_atomically",
         [sys.executable, os.path.join(HERE, "test_version_stamps_are_written_atomically.py")], 120,
         why="the write that runs on EVERY ship left his 6 MB bible.html at ZERO BYTES. "
             "bump_version wrote all four stamps with io.open(path,'w'), which truncates on open, "
             "and his console EXECS the working tree — it re-reads bible.html per request. "
             "MEASURED with a concurrent reader: 4.8% of reads got an EMPTY file, every torn size "
             "0 bytes. That is his 'panel that renders NOTHING and says nothing', and it never "
             "reproduced because a settled tree is fine. Now tmp+os.replace; this pins that the "
             "SHIP PATH calls it, not merely that the helper exists."),

    Gate("test_live_version_is_not_the_working_tree",
         [sys.executable, os.path.join(HERE, "test_live_version_is_not_the_working_tree.py")], 120,
         why="his console EXECS the working tree, so the page in front of him can be bytes that "
             "were never pushed — and /api/status reported THREE versions (ver, bibleVer, "
             "agentVer) that ALL read that same tree, while shipVer is None on mac. Three "
             "readings of one source is n=1, not n=3: they agree with each other and can be "
             "wrong together. MEASURED this session: the console said v2706 while origin/main "
             "shipped v2705, for over an hour, silently. Pins that liveVer comes from the REMOTE "
             "ref and never the tree, that it carries the age of that ref (a local origin/main "
             "goes stale, and a confidently wrong live version is worse than none), that an "
             "unaskable question answers None rather than guessing, and that it is CACHED — an "
             "uncached subprocess per poll is how a machine gets saturated. Proven RED four ways"),
    Gate("test_chronicle_ledger_refines_the_template",
         [sys.executable, os.path.join(HERE, "test_chronicle_ledger_refines_the_template.py")], 120,
         why="his check: the printer's template station could name WHICH stash panel a reel showed "
             "(stash - gems/personal) but only ever said the bare word `chronicle` — four of the "
             "six MINI_FOCUSES resolved and two reached the doorstep. The ledger was recorded all "
             "along: tv_diablo asks for chronicleTab on every frame and v1689 writes a visit row "
             "carrying it (13 rows across 12 sessions: uniques 9, sets 3). ⚠ THE JOIN IS "
             "UNEXERCISED BY HIS OWN DATA -- zero overlap between those 12 sessions and the 40 "
             "reels on his shelf -- so on his machine it runs, answers UNKNOWN, and is RIGHT to, "
             "which is indistinguishable from a join that does not work. This supplies the input "
             "his shelf never does. Proven RED four ways, including the zone guard, whose first "
             "law was vacuous because every stash case lacked ledger data"),
    Gate("test_mini_foc_pills_are_symmetric",
         [sys.executable, os.path.join(HERE, "test_mini_foc_pills_are_symmetric.py")], 120,
         why="his A17 #7 ruling — \"this is a visual thing? make it symmetric then?\" — shipped at "
             "v2686 as a 2-column grid on .mini-foc, and NOTHING pinned it: the three .mini-foc "
             "mentions in test_control are all about the --mini-focus CLI flag. That is the "
             "heartov2 shape, where a defect was fixed three times and returned each time because "
             "after every fix nobody was looking. Pins the LAW not the string — equal-fraction "
             "columns, refusing auto/min-content/max-content/fit-content — because the longest "
             "label MOVED this session: v2709 made a chronicle reel resolve to `chronicle - "
             "uniques`, longer than any stash label, and a content-sized column would have "
             "desynchronised the pills the moment it did"),
    Gate("test_seal_verdict",
         [sys.executable, os.path.join(HERE, "test_seal_verdict.py")], 120,
         why="seal_covers_extraction answers yes or no, and its `no` covered two OPPOSITE facts: "
             "a seal that examined a session and recorded there was nothing to take, and a seal "
             "that never says what it took. Measured-zero collapsed into nobody-looked, inside "
             "the function whose job is policing evidence. It made `seals_certify_nothing` read "
             "as 30 records with no evidence when 22 of them cover ZERO ROWS and say so; the "
             "real defect is SIX seals over 42 rows. seal_verdict() adds COVERED/EMPTY/"
             "UNEVIDENCED and this pins the load-bearing half: rows==0 is required, so a seal "
             "claiming nothing-to-take while covering 7 rows stays UNEVIDENCED and the word "
             "EMPTY cannot become self-certifying. Also pins that the strict bool did NOT soften "
             "-- two other gates depend on it"),
    Gate("test_owner_resolution",
         [sys.executable, os.path.join(HERE, "test_owner_resolution.py")], 120,
         why="`window._D2R_OWNER` is the most consequential boolean in bible.html -- "
             "_isCousinShell is its negation, which gates _seedsBelongHere, which decides "
             "whether 245 of HIS uniques appear in somebody else's chronicle. It has now broken "
             "in BOTH directions: too generous gave Dean 243/403 of another man's finds; too "
             "strict made an automated world unable to stop being the owner, so the claim bar "
             "never rendered and the one spec about the stranger path died on `b.onclick is not "
             "a function`. Runs the REAL fragment lifted out of bible.html in a vm sandbox "
             "across 9 cases -- never a Python paraphrase of the rule. Proven RED three ways, "
             "including a sabotage that reproduces the Dean defect exactly",
         ),
    Gate("test_search_placeholder_fits",
         [sys.executable, os.path.join(HERE, "test_search_placeholder_fits.py")], 120,
         why="the global search field carried a 70-character sentence written for a 1440px input; "
             "at 375 the browser cut it mid-word and it read as broken text. NO GEOMETRY GATE "
             "COULD SEE IT -- an input truncating its own placeholder is normal rendering, not "
             "overflow, so every clipping check was green and correct. The second eye found it "
             "cold on the pixels. Pins the LAW rather than the string: the narrow text must fit "
             "the 375px box (a budget derived from the box, not from today's wording), the swap "
             "must listen for `change` so a rotate does not strand the desktop sentence, and it "
             "must sit BELOW the input -- getElementById during parse returns null and the "
             "handler dies silently, which this repo has shipped four times"),
    Gate("test_tombstone_station",
         [sys.executable, os.path.join(HERE, "test_tombstone_station.py")], 180,
         skip_ok=(r"no reels on this host",),
         why="the printer's last station and the sealed/certified split are REPORTS, and a report "
             "is the easiest thing here to break silently — it keeps returning a shape while the "
             "word stops being true. Two named rots: a tombstone verdict of ON DISK because the "
             "LEDGER failed to load rather than because nothing was pruned (opposite facts), and "
             "`certified` decaying into an alias for `sealed` when 30 seals exist and ZERO satisfy "
             "the extraction contract"),
    Gate("test_entry_door_stamp",
         [sys.executable, os.path.join(HERE, "test_entry_door_stamp.py")], 120,
         why="the door that opened a reel never reached the reel: 0 of 10,121 journal rows carried "
             "it, so nothing downstream could route by entry. And the half nobody saw — v2316 gave "
             "each door a Wilson score, only `shadow` ever passed opened=True, so onair and mini "
             "carried NO denominator while their refused counters ticked and made the ledger look "
             "alive (shadow 609/181, the other two absent). A score nobody increments cannot fail"),
    # ⚠ 600, NOT 120 — THE CEILING WAS BELOW THE FLOOR. MEASURED on an IDLE Mac this suite
    # takes 126.8s, so a 120s timeout could never pass and the gate reported "timed out after
    # 120s" with an EMPTY "what actually broke" section — a failure with no defect named,
    # which reads as noise and gets scrolled past. It is slow for a real reason: it spawns
    # NESTED run_gates subprocesses to prove the census and the banking end to end, and
    # `rg.GATES = [g]` means that cost is per-CASE and does not scale with the gate count.
    # ⚠ The headroom is deliberate: a suite measured at 126.8s idle runs far slower inside a
    # full set, and a threshold sitting a few seconds above a measurement is a flake waiting
    # to be blamed on whatever shipped that day. [[feedback-threshold-above-the-ceiling]]
    Gate("test_gate_banks", [sys.executable, os.path.join(HERE, "test_gate_banks.py")], 600,
         why="the board said since v2444 that the sabotages BANK and the first lock opened itself; "
             "the live console said open 0 of 5, every lock n=0, and the ledger file did not "
             "exist. v2444 put banking in main() only so a test importing the module could not "
             "write his ledger — but the GATE imports and calls score(), so every push measured 55 "
             "sabotages and fed the queue with none of them. Pins that the verdict script banks, "
             "that a banking failure is SAID rather than swallowed, and that banking the same "
             "evidence three times is still one measurement — the gate now runs on every push, so "
             "a non-folding bank would let Wilson climb on repetition alone."),
    # v2466 — the build stamp renders whole. Needs headless Chrome; skips, never passes, without
    # it. `why` IS A KEYWORD.
    # v2469 — the probe primitives. `why` IS A KEYWORD.
    Gate("test_tab_vocabulary", [sys.executable, os.path.join(HERE, "test_tab_vocabulary.py")], 120,
         why="the console had FOUR copies of the Chronicle-tab vocabulary and two of them\n"
             "disagreed. ct.detect() reports 'unique' (its marker box is keyed on it) while\n"
             "READ_PROMPT asks the model for 'uniques', and each resolver understood only its\n"
             "own: 'unique' resolved through ledger_kind_for_tab and returned None from\n"
             "chronicle_kind, 'uniques' the reverse, 'sets' agreed by luck of spelling.\n"
             "chronicle_kind also built its ledger name by concatenation, right only because\n"
             "those two words pluralise correctly. Pins the LAWS: every alias resolves the\n"
             "same in both resolvers, and every word either PRODUCER can emit is in the\n"
             "shared map — so a new tab word understood by half the console goes red."),
    Gate("test_safe_copy", [sys.executable, os.path.join(HERE, "test_safe_copy.py")], 120,
         why="nothing in this repo may be copied in a way that can fill his disk. Three review\n"
             "agents ran `cp -R tv /tmp/...` and wrote 20.5 GB in four minutes onto a volume\n"
             "with 9 GB free; at ENOSPC every Bash call in the session failed BEFORE IT RAN,\n"
             "so nobody could even run df or rm. Guards tv/safe_copy.py (excludes frames and\n"
             ".render_shots, refuses above a ceiling and below a free-space floor) and the\n"
             "render gate's Chrome profile being temporary — it had reached 1.4 GB."),
    Gate("test_render_coverage", [sys.executable, os.path.join(HERE, "test_render_coverage.py")], 120,
         why="the render gate could not notice its own COVERAGE SHRINKING. It refuses a\n"
             "zero-size element, a black capture, an unsettled page and a dropped socket —\n"
             "every way ONE reading can lie — and had no way to see it was taking FEWER\n"
             "readings than before. `console` went 3/3 to 2/2 when the DOM changed and\n"
             "re-baselined silently, because two clean measurements are two clean\n"
             "measurements. tv/render_coverage.json is a ratchet: coverage may RISE freely,\n"
             "a DROP fails, and blessing refuses on a partial run so one busy afternoon\n"
             "cannot become the new normal."),
    # #72 — the ratchet was correct and NOT CONSULTED on a subset run, and its floor was stale.
    Gate("test_every_version_binds_to_a_commit",
         [sys.executable, os.path.join(HERE, "test_every_version_binds_to_a_commit.py")], 120,
         why="v2927 — MEASURED: 249 of 278 rows in the TASKS.md version table carried the literal "
             "`(this commit)`, so 89% of the ship history could not bind a version to a commit. "
             "Grok Bot raised it three ticks running (GB-B-403/404/405) and was right. The "
             "backfill binds on the commit whose diff ADDED the VERSION stamp — never on a subject "
             "line, which can mention a version it does not ship. Three honest states: bound (230), "
             "carried (19, a batched intermediate that shipped inside the next stamped commit), "
             "and UNKNOWN. Proven red five ways, including the narrow-regex defect the tool "
             "shipped and caught on itself.",
         skip_ok=()),
    Gate("test_a_target_can_hand_back_its_own_verdict",
         [sys.executable, os.path.join(HERE, "test_a_target_can_hand_back_its_own_verdict.py")], 120,
         needs_app=False,
         why="a surface built for this harness that this harness never read. control_ui.html writes "
             "the fan solver's whole record onto the overlay as `data-fanfit` and says it is \u2018for "
             "the render harness, which photographs the DOM and cannot reach a JS global\u2019 \u2014 "
             "and render_check.py contained ZERO occurrences of `fanfit`. #53's central question "
             "(did the solver find nothing, or find something and revert it?) sat in the DOM being "
             "photographed, one manual probe away, on every render this gate ever did. `report` is "
             "the general tap; it is PRINTED, not merely collected, and it may never decide ok \u2014 "
             "a diagnostic that can fail a run is a second gate in disguise.",
         skip_ok=()),
    Gate("test_the_ratchet_is_not_skipped_by_a_subset",
         [sys.executable, os.path.join(HERE, "test_the_ratchet_is_not_skipped_by_a_subset.py")],
         120,
         why="the coverage ratchet above was SKIPPED WHOLESALE on a subset run, so\n"
             "`render_check.py heart-stored` could lose a node and exit 0 with an\n"
             "informational line about it. A subset cannot speak for the targets it did not\n"
             "render; it has exactly as much evidence as a full run about the ones it did.\n"
             "And the floor is a CEILING on what the ratchet can see: heart-stored's floor\n"
             "said 9 at every width while the v2910 selector photographs 15, so six watched\n"
             "nodes could vanish and the run would still be green. This pins the scope, the\n"
             "loud per-width STALE report, and the rule that a subset may still never bless."),
    # v2589 — A7's remaining half: the per-store writer was a measurement NOBODY HAD TAKEN, and
    # three earlier attempts each returned a zero that measured the instrument.
    Gate("write_census", [sys.executable, os.path.join(HERE, "write_census.py")], 120,
         why="arms write_witness over a REAL write to a scratch root and reads back who did it, "
             "so the declared owner of each reel store is confirmed by observation rather than "
             "by coupling. A store nobody could exercise says NOT EXERCISED with the reason — "
             "never a zero that reads like an answer — and a measured store with no declaration "
             "is UNCHECKED, never agreement."),
    # v2580 — HIS ASK: "do tests on the reels see that they get run and proccesed through the
    # printer and everything down stream correctly as it was registered before... everytinh was
    # working before.. so it needs to be tested too". The suites assert behaviour against
    # fixtures; nothing took HIS OWN FOOTAGE through the pipeline that has been rebuilt under it
    # over nine versions and showed the downstream numbers are still the registered ones.
    Gate("reel_demo", [sys.executable, os.path.join(HERE, "reel_demo.py")], 180,
         why="walks his real reels through all six printer stations and checks the numbers that "
             "were REGISTERED BEFORE any of this changed — runewords 99, sets 135 pieces, "
             "uniques 403, each his own ruling — plus that all three route sets still derive and "
             "that no reel is missing a station. It asserts against registered values, never "
             "against the code it is testing, and it writes nothing.",
         # v2658 — DECLARED, because the alternative was a FALSE GREEN. `tv/frames/` is gitignored
         # and zero-tracked, so a fresh checkout has no shelf and this gate can walk nothing. Its
         # first repair separated UNKNOWN from FAILED (right, and it stopped four false REDS) but
         # left `ok = not bad`, so a venue with nothing to walk returned 0 and run_gates recorded
         # a ✅ over the gate's own words `0 reel(s) walked … 3 UNKNOWN`. A false red traded for a
         # false green is the worse half of the trade: a red gets investigated, a green ships.
         # It exits 77 in that state now, and this is what makes that skip DECLARED rather than a
         # failure. ⚠ NARROW ON PURPOSE — only the absent-shelf sentence. A shelf that EXISTS and
         # walks nothing is the real defect this gate is for, and still fails.
         # #123 — and EMPTY, which is not that defect: a directory machine_tree.establish() built,
         # holding nothing, on a host whose ledger never closed a reel (reel_demo._shelf decides).
         skip_ok=(r"reel shelf is (?:absent|empty) on this venue",)),
    Gate("test_a_relaunch_leaves_a_receipt",
         [sys.executable, os.path.join(HERE, "test_a_relaunch_leaves_a_receipt.py")], 60,
         why="#225 - the Windows ALT console died relaunching into v3419 with NO trace (pythonw drops "
             "stdout; on Windows os.execv starts a NEW pid that can contest the mutex and :17772 while "
             "its parent still holds them). Now a boot log is written before the mutex/bind checks, both "
             "quiet exits and any uncaught exception land in it, every exec leaves a receipt naming its "
             "pid, and a Windows child waits for that pid to exit (measured on the ALT: 3.03 s for a 3 s "
             "parent). A TV_STUB or scratch-port console writes a temp log, never this machine's record "
             "(8 of 9 lines were render_check's on day one). 12 cases, 5 red-proofs"),
    Gate("test_the_chronicle_inbox_asks_on_the_page",
         [sys.executable, os.path.join(HERE, "test_the_chronicle_inbox_asks_on_the_page.py")], 60,
         why="#230 - his ask: harness Grok's mailbox study (~/tv-diablo-mailbox) into the console's own "
             "Chronicle inbox. Ported: the tome on the pill and header, the item art 112px on a plate (an "
             "empty plate says 'no picture'), the three destructive questions drawn ON THE PAGE (a native "
             "confirm() blocks the window; some webviews answer NO unseen), the chips' dim/danger variants "
             "styled outside the footer and the session dismiss labelled 'Dismiss' (a grok-4.7 look found "
             "them reading as disabled). Pixels: render target ch-inbox. The second eye on v3497: an answer "
             "acts only on the queue it was asked about (a poll between question and click re-asks). "
             "6 cases, 3 red-proofs"),
    Gate("test_the_render_budget_is_not_spent_on_a_cold_cache",
         [sys.executable, os.path.join(HERE, "test_the_render_budget_is_not_spent_on_a_cold_cache.py")], 60,
         why="#236 - inside a push /api/heart cost 30.4s cold on the render gate's fresh console, a tenth "
             "of the 300s ceiling paid serially at load 6, and the render was killed four targets short. "
             "_prewarm warms every declared endpoint once, in the background, the moment the console "
             "answers; each target still warms its own before it is judged. 2 cases, 1 red-proof"),
    Gate("test_the_pop_carries_his_questions",
         [sys.executable, os.path.join(HERE, "test_the_pop_carries_his_questions.py")], 60,
         why="#223 - the 📥 pop is titled 'Waiting on you' and carried only the names the readers could not "
             "settle; his questions (the console's ASKS) were drawn in the inbox alone, and with no names it "
             "said 'Nothing is waiting' over an open question. One builder (_askCardsHtml) now reaches the "
             "inbox, the pop and the Sessions sticky through window._inboxAskCards; the badge counts asks. "
             "Pixels: render target pop-asks. 6 cases, 4 red-proofs"),
    Gate("test_the_banner_reads_the_heap",
         [sys.executable, os.path.join(HERE, "test_the_banner_reads_the_heap.py")], 60,
         why="#178 (his ruling 2026-09-25: the banner reads the heap) - the host OS had two writers, the cousin "
             "ribbon's own UA test and the board_build door's raw navigator.platform, which is how GrokBot's "
             "Linux seat filed 'machine windows' beside a LINUX ribbon as a contradiction. Now window.D2R_HOST_OS "
             "is computed once on the heap; the ribbon renders it (pixels: 'LINUX - its own world') and the door "
             "reports it. The real block driven in node for 4 hosts. 3 cases, 2 red-proofs"),
    Gate("test_a_fresh_install_is_not_a_lost_store",
         [sys.executable, os.path.join(HERE, "test_a_fresh_install_is_not_a_lost_store.py")], 60,
         why="REG-1275 (#165) - the v2988 loss detector read 'has run before' from keys THIS boot had just "
             "written, so every fresh install was filed as a lost store and the seed floor refused it for ever "
             "(measured: first load found 0 + d2r_storeEmptied). The reading is now a snapshot taken before any "
             "write; a store that ran and then emptied is still caught (spec v3503). 2 cases, 1 red-proof"),
    Gate("test_each_console_says_its_own_system",
         [sys.executable, os.path.join(HERE, "test_each_console_says_its_own_system.py")], 90,
         why="#229 - the roadmap's last build item: from the fleet, see each console stand on its own. The "
             "beacon sends {tree, reels} (the doctor's own tree verdict, the reel folders on its shelf; None "
             "is unread, never 0), the relay shapes it (a string '25' is not a count - the law caught my first "
             "cut coercing it), the row's hover says it. All three ends driven for real. 8 cases, 3 red-proofs"),
    Gate("test_a_headless_console_says_it_has_no_window",
         [sys.executable, os.path.join(HERE, "test_a_headless_console_says_it_has_no_window.py")], 90,
         why="#145 - the supervisor revives with --no-open, headless by construction; witnessed on a scratch port: "
             "0 windows for the process, while its banner read 'native window'. The banner now says HEADLESS and "
             "drops the close-the-window line. Driven on a real isolated boot, killed by PID. 1 case, 1 red-proof"),
    Gate("test_switching_views_closes_the_theatre",
         [sys.executable, os.path.join(HERE, "test_switching_views_closes_the_theatre.py")], 60,
         why="#172 - his ruling 2026-09-25: switching views closes the theatre. It deliberately covers every "
             "non-Sessions view while open, and the seat's 'dark glass' over the Vault was its film stage. The "
             "shipped header-tab guard runs in node: a different tab closes it, the same tab or a closed theatre "
             "calls nothing; thClose is exported. The browser half is in v877. 4 cases, 2 red-proofs"),
    Gate("test_the_theatre_never_waits_on_the_fixture_scan",
         [sys.executable, os.path.join(HERE, "test_the_theatre_never_waits_on_the_fixture_scan.py")], 120,
         why="REG-1284 (#165) - the theatre ran frame_authority's test-file scan inside /api/sessions; cold (a fresh "
             "world, or his console after every ship) it took 9.03 s and the page aborts at 8 s - the first open "
             "after a restart failed, and v877 was red in every Routine I run. A non-blocking accessor (None = "
             "mark nothing) + a boot warm-up: 0.08 s cold. Driven on the real handler with a 5 s scan. 3 cases, 2 red-proofs"),
    Gate("test_a_scratch_console_leaves_no_trace_in_his_world",
         [sys.executable, os.path.join(HERE, "test_a_scratch_console_leaves_no_trace_in_his_world.py")], 120,
         why="REG-1283 - lane_trace.DIR was always his live tv/.lane_trace, so every scratch console (the render gate's "
             "each push) stamped the corroborator's second witness that HIS loops ran (measured: a scratch console "
             "booted 06:07:12 wrote _orphan_exit_loop.json at 06:07:18), and loop_corroborate read the same hard-coded "
             "path. Both now follow tv_diablo._fixture_root. Driven in fresh interpreters. 2 cases, 2 red-proofs"),
    Gate("test_importing_a_suite_isolates_his_stores",
         [sys.executable, os.path.join(HERE, "test_importing_a_suite_isolates_his_stores.py")], 120,
         why="REG-1281 - test_control isolated control_app's chronicle/vault paths only in setUpModule, and a harness "
             "that ran its cases one by one (mine, 2026-09-25) wrote fixture evidence over his live chron_evidence.json "
             "(324 uniques / 2,714 pages; restored byte-exact). Importing a suite now isolates every _CHRON_*/_VAULT_* "
             "path (8, discovered not listed) and the G5 stats path. Driven in fresh interpreters. 2 cases, 2 red-proofs"),
    Gate("test_a_shared_stash_item_survives_the_vault_cleanse",
         [sys.executable, os.path.join(HERE, "test_a_shared_stash_item_survives_the_vault_cleanse.py")], 60,
         why="REG-1280 (#165) - the seed floor's vault cleanse deletes every unfiled _GRAIL_SEED name from owned on each "
             "owner load, and a shared-stash item is never filed (tvVaultRegister('Bone Break') -> mule:null). Measured: "
             "a registered Bone Break vanished on reload, Black Cleft (no seed name) stayed. The shipped cleanse statement "
             "runs in node with the shipped _SHARED_KEEP: shared kept, floor residue still stripped. 3 cases, 1 red-proof"),
    Gate("test_a_live_witness_is_not_an_extraction",
         [sys.executable, os.path.join(HERE, "test_a_live_witness_is_not_an_extraction.py")], 90,
         why="REG-1277 (#221) - his ruling was DIG. The 18 unexplained tombstones were his console's own "
             "retention lane (stdout: v2875 booted 01:36:21, 'freed 3565 MB by removing 7 reel(s)' one "
             "second later; 11 more that day). 13 had panels and a seal that took 0 rows, and went because "
             "one LIVE-lane row put the session in the durable stores - a 2,385-frame reel left on one row. "
             "A seal with 0 rows now holds; the deleter and the end-route doors are compared and the doctor "
             "leads with any disagreement. 7 cases, 4 red-proofs"),
    Gate("test_the_seed_holds_no_one_shot_name",
         [sys.executable, os.path.join(HERE, "test_the_seed_holds_no_one_shot_name.py")], 60,
         why="REG-1271 (#165) - the v3313 bake seeded Fleshrender, Gloom's Trap and The Diggler, the names "
             "rule 4 refuses (each arrives by its own one-shot), because one_shot_owned scraped a line "
             "window that later swallowed 25,522 strings. It now reads each one-shot's own chronicleApply; "
             "the seed may hold only the ruling nine. 3 cases, 2 red-proofs"),
    Gate("test_a_drained_verdict_is_a_declared_one",
         [sys.executable, os.path.join(HERE, "test_a_drained_verdict_is_a_declared_one.py")], 60,
         why="REG-1267 (#222) - the row 'a verdict comes from a declared field' said 6 of 6 recent looks "
             "carried no declared verdict; all six were drained from #231, whose required `verdict:` field "
             "the drain reads as a FIELD. The check re-parsed the findings paragraph for a VERDICT line that "
             "could never be there, and had no law at all. schema and #231 fields are declared; prose is not. "
             "6 cases, 1 red-proof"),
    Gate("test_the_closer_reads_frames_on_every_os",
         [sys.executable, os.path.join(HERE, "test_the_closer_reads_frames_on_every_os.py")], 60,
         why="REG-1266 (#229) - the Kai closer hard-coded bin/ocr_mac and ended at boot on Windows, while "
             "tv_diablo._ocr_worker_cmd() has returned ocr_win.ps1 (same protocol) since v818. MEASURED on "
             "the ALT: OS OCR present, ocr_win.ps1 read 'Harlequin Crest'/'Shako' in 208 ms. The closer asks "
             "the one seam and spawns windowless. 4 cases, 2 red-proofs"),
    Gate("test_a_windows_boot_is_checked_before_it_reaches_him",
         [sys.executable, os.path.join(HERE, "test_a_windows_boot_is_checked_before_it_reaches_him.py")], 90,
         why="#229 - the only Windows console anything ever booted was his ALT, so a Windows-only boot "
             "death (#225) reached his box first. tv/windows_boot_check.py boots a SCRATCH console and "
             "asks which build it runs; tv-windows-boot.yml runs it on windows-latest. Proven on the ALT "
             "over SSH before shipping (3.7s, shipped build, platform=windows). Driven here against fake "
             "trees: shipped build 0, other build 1, boot death 1 with its last words, no manifest 77. "
             "5 cases, 2 red-proofs"),
    Gate("test_a_windows_console_asks_before_it_starts_at_sign_in",
         [sys.executable, os.path.join(HERE, "test_a_windows_console_asks_before_it_starts_at_sign_in.py")], 60,
         why="#229 - MEASURED on the ALT: zero scheduled tasks and zero startup entries, so the console "
             "survives its own relaunch but not a reboot. Starting it at sign-in is a standing change on "
             "his PC, so it is HIS call: a Windows row asks in his mailbox (yes = handoff to Claude, no = "
             "his ruling). A failed schtasks query is UNKNOWN, never 'not set up'. 6 cases, 2 red-proofs"),
    Gate("test_a_machine_that_died_restarting_is_asked_about",
         [sys.executable, os.path.join(HERE, "test_a_machine_that_died_restarting_is_asked_about.py")], 60,
         why="#223 / #227 item 2 - the fleet's only 'is it on?' question. MEASURED on his roster: "
             "relaunch.armed is True on EVERY console, so it cannot be the signal; a last beacon with a "
             "newer build on disk than running (diskVer != ver) and the restart allowed, then silence, is "
             "a machine that died restarting (the ALT, #225). Dean (off, v3404 on v3404) and Wife PC ask "
             "nothing. The ask's identity carries the build. 7 cases, 2 red-proofs"),
    Gate("test_a_test_run_leaves_no_scratch_dirs",
         [sys.executable, os.path.join(HERE, "test_a_test_run_leaves_no_scratch_dirs.py")], 60,
         why="#171 - 138 mkdtemp sites across 46 test files had no teardown in their own function or "
             "class; one test_agent run left 70 entries in a $TMPDIR already holding 43,744. "
             "fixture_tmp.contain() holds a test process's scratch dirs in one parent removed at exit "
             "(and sweeps dead runs' day-old parents, never a live one's); every file with an unpaired "
             "site must call it at import. Measured after: the same run leaves 0. 6 cases, 3 red-proofs"),
    Gate("test_a_self_updated_console_can_read_its_frames",
         [sys.executable, os.path.join(HERE, "test_a_self_updated_console_can_read_its_frames.py")], 60,
         why="REG-1260 (#227) - MEASURED on the ALT: tree at 6dab59f1 held the launcher's Pillow step, "
             "consoles started 20:26 and 21:06, no Pillow - the launcher's last run was 19:04; every later "
             "start was the console's own os.execv, which never runs start_tvd_win.ps1. The console now "
             "installs Pillow at boot (python.exe, hidden, user site added) and the doctor row quotes the "
             "attempt instead of promising a launcher run. 6 cases, 2 red-proofs"),
    # ══ #246 VAULT 2.0 — ONE DOOR INTO THE MULE MAP, AND EVERY LAW IT ANSWERS TO ══════════════════════
    # His words: "all those item inside the vault are falsely there ... make sure they dont get routed here
    # again" and "all the items getting vaulted and vaulted by AI READERS or manually should be to the
    # dedicated mules alone". 173 filings, 160 from found-ever data with no witness, one writer.
    Gate("test_found_ever_never_files_to_a_mule",
         [sys.executable, os.path.join(HERE, "test_found_ever_never_files_to_a_mule.py")], 300,
         needs_app=False,
         why="#246 L1/L3/L5 - vaultAutoAssign walked ownedPool() (d2r_owned = ticked or found-ever) and filed "
             "every name with no home: 173 filings on his board, 160 with no witness, made in two runs on "
             "2026-09-16 by a restore and the sorter. The SHIPPED board in its own headless Chrome is given a "
             "found-ever world (owned + foundLog + setPieces, no witness) and every trigger is pressed - the "
             "sorter, a ledger restore through chronicleApply, _chronAutoAdopt, a one-look vaultAccumApply row, "
             "the owned_restore / rw_restore / vault_autosort scripts the console really sends, the registrar "
             "with no witness, the inbox auto-accept, the KAI judge keep tier, Chronicle Accept and Accept-All "
             "- and the map and the witness store stay empty. A set piece restored as a 'unique' goes to the "
             "set door (L3), Chronicle Accept ticks the Chronicle only (L5), and his hand still files with a "
             "provenance row (the positive control). #246 review: the console's 'register as owned' press "
             "files nothing (it minted a hand witness from a route with no confirm), and the inbox's 'Both' "
             "button, clicked for real, files as his hand while 'Chronicle' does not. 6 cases, 6 red-proofs",
         skip_ok=()),
    Gate("test_every_mule_filing_carries_its_witness",
         [sys.executable, os.path.join(HERE, "test_every_mule_filing_carries_its_witness.py")], 120,
         why="#246 L6/W5 - the mule map stored a bare string and had ~40 writers, none asking for a witness; "
             "the only author record was a 400-row ledger whose source is overwritten in place. window.vaultFile "
             "is the ONE door, cut from bible.html and driven in node: no witness files nothing; his hand, a "
             "verified .d2s, or two stash looks each with its own frame and conf file with a d2r_vaultProv row; "
             "one look, a frameless or unsure look, one session twice, a folded re-look and a held gate are "
             "refused; what the MAIN carries is refused as the MAIN's; a home he chose is never overridden and a "
             "reader never replaces his hand's row. Every key in the map has its row after every call; the tag "
             "reads the row (W5); the board's bars equal vault_retro's (his 2-look ruling). Source half: no "
             "assign[...] = outside the door, every wholesale re-bind named. #246 review: a hand must say WHEN "
             "(a time that is no date, or none, is refused) and the row carries the spec's `main`. 11 cases, 6 red-proofs"),
    Gate("test_the_witnessed_lane_files_its_own_rows",
         [sys.executable, os.path.join(HERE, "test_the_witnessed_lane_files_its_own_rows.py")], 240,
         needs_app=False,
         why="#246 L7/W2 - the system was INVERTED: vault_accum held 14 gate-passing stash rows and the "
             "witnessed lane could land none (rows carried `lane`, the container gate reads `loc`; 'already "
             "vaulted' was read from found-ever d2r_owned). The REAL vault_retro.apply_payload builds the "
             "payload and the REAL vaultAccumApply applies it in its own headless Chrome: a two-look stash row "
             "files with its witness row (looks, gate verdict, stamped bound) even when the grail knew the name "
             "first; Magefist's frameless conf-0.0 shape and a found-ever name do not file; a set piece seen in "
             "the stash files through the set door; with no gate verdict travelling the board judges each look itself. "
             "#246 review: a witnessed shared-stash name is refused 'no-home' and its ledger row says so, never "
             "'no witness ... a second look', and the sorter logs such a row 'no-home' too. 7 cases, 6 red-proofs",
         skip_ok=()),
    Gate("test_a_look_without_a_frame_is_not_a_witness",
         [sys.executable, os.path.join(HERE, "test_a_look_without_a_frame_is_not_a_witness.py")], 60,
         why="#246 L8/W3 - vault_retro.gate counted a session from every row and tested the floor on the "
             "pile's BEST row, so Magefist passed on one real look plus a frameless conf-0.0 look (Wilson "
             "0.095). Each look now qualifies on its own frame and conf; looksSeen rides beside; two real looks "
             "still pass; the payload carries the verdict and a stamped, never-decisive bound (moving the bar "
             "to Wilson is HIS call). 5 cases, 2 red-proofs"),
    Gate("test_main_gear_never_files_to_a_mule",
         [sys.executable, os.path.join(HERE, "test_main_gear_never_files_to_a_mule.py")], 120,
         why="#246 L10/W4 - three sources each knew part of the MAIN lock (d2r_laneLock, the furniture law, "
             "main_character.py - read 0 times by the board) and none reached the writer; the furniture law "
             "locked Blackhand Key as a 'key'. The SHIPPED lock and door, cut and run in node: one predicate "
             "joins all three (his 3-session bar kept), the door refuses every locked name even by hand and "
             "files Blackhand Key, MAIN_LOCKS stays null until the console answers, the MAIN's name comes only "
             "from his declaration or a .d2s he says is his (tag 'MAIN (name UNKNOWN)' until then), the panel "
             "calls out a MAIN item in a mule, a reader never files a consumable, and the furniture and consumable lists equal inventory_law's. "
             "#246 review: the panel carries the MAIN-name input, joined to the declare door that had no caller. 9 cases, 5 "
             "red-proofs"),
    Gate("test_every_locked_main_row_reaches_the_board",
         [sys.executable, os.path.join(HERE, "test_every_locked_main_row_reaches_the_board.py")], 120,
         why="#246 L11/W4 - main_character.is_locked had no reader on the board. GET /api/main_locks is served "
             "by the REAL Handler over a FIXTURE ledger and publishes exactly what the ledger locks; the SHIPPED "
             "lock block, fed that answer in node, locks every one and the door refuses it; the board fetches "
             "the path the console serves; an unreadable ledger is ok:false/locked:null and the board keeps "
             "MAIN_LOCKS null. 4 cases, 3 red-proofs"),
    Gate("test_a_filing_is_kept_by_its_witness_not_by_owned",
         [sys.executable, os.path.join(HERE, "test_a_filing_is_kept_by_its_witness_not_by_owned.py")], 60,
         why="#246 L12/W6 - the render prune kept a filing exactly as long as its name sat in `owned` "
             "(ticked or found-ever). The SHIPPED prune, run in node: a witnessed filing stands when its name "
             "leaves the pool; an unwitnessed one outside the pool goes; an unwitnessed one in the pool is "
             "left for the NO WITNESS tag and the doctor (the fresh vault is his ruling). 1 case, 1 red-proof"),
    Gate("test_a_restored_set_piece_travels_as_a_set",
         [sys.executable, os.path.join(HERE, "test_a_restored_set_piece_travels_as_a_set.py")], 60,
         why="#246 L3/W0c - a ledger restore sent every foundLog key as a unique, set pieces included; on the "
             "board toggleOwned dropped each piece into d2r_owned and the sorter filed 19 of them (2026-09-16 "
             "15:28:34). plan() now carries the backup's set-piece list and proposal_from sends those names "
             "through `sets` only, once. 3 cases, 1 red-proof"),
    Gate("test_the_vault_provenance_row_can_go_red",
         [sys.executable, os.path.join(HERE, "test_the_vault_provenance_row_can_go_red.py")], 60,
         why="#246 W7 - the one door, watched: the doctor row 'vault provenance' reads the board through the "
             "shared tick read and reports filings with no witness, MAIN-locked names in a mule, gate-passing "
             "stash rows never filed, and the feeder's banked-of-runs; UNKNOWN without a board read. Each arm "
             "driven with a fixture and seen RED; furniture and consumables are never reported as unfiled; "
             "registered, declared and explained. #246 review: arm 3 never counts a shared-stash row or a set "
             "piece filed under its slot name, and arm 2's OK is UNKNOWN when nothing locks. 10 cases, 7 red-proofs"),
    Gate("test_every_operator_door_keeps_its_contract",
         [sys.executable, os.path.join(HERE, "test_every_operator_door_keeps_its_contract.py")], 60,
         why="REG-1259 - Routine I's v1550 audit was red on four doors no page calls by design "
             "(owned_restore, rw_restore, vault_autosort, vault_route_probe): walked by hand after "
             "something went wrong. This law is their NAMED OWNER and drives them through the real "
             "Handler with a recording board: no write door writes without confirm, each writes with "
             "it, the probe only reads. #246 L4: a confirmed possession door never presses the sorter, a "
             "chronicle restore never reaches the owned door, and the register button re-gates the stored "
             "sweep row by row, naming what it holds back. 6 cases, 5 red-proofs"),
    Gate("test_the_gate_never_adopts_a_browser_it_did_not_start",
         [sys.executable, os.path.join(HERE, "test_the_gate_never_adopts_a_browser_it_did_not_start.py")], 60,
         why="REG-1258 - hooks/pre-push, render_check and crest_loudness all USED whatever answered on :9224; "
             "measured before a push, another session's research Chrome held it, and the gate would have "
             "graded the page in that browser. The hook now chooses the first port nothing listens on "
             "(bash /dev/tcp, any OS) and exports TV_RENDER_PORT to every child. The real snippet runs "
             "in bash against a held socket. 5 cases, 2 red-proofs"),
    Gate("test_the_measured_bit_crosses_the_relay",
         [sys.executable, os.path.join(HERE, "test_the_measured_bit_crosses_the_relay.py")], 60,
         why="the doctor row 'a tally agrees with its own ledger verdict' read MISSING for every fleet row, v3499 "
             "consoles included: the tally seals measured/measuredWhy (v3389) and functions/api/console.js "
             "copied the tally through a fixed key list that dropped both - the sixth joint of the fleet tally. "
             "The real shaper runs in node; a non-boolean arrives as null. 4 cases, 1 red-proof"),
    Gate("test_the_ask_route_waits_for_its_question",
         [sys.executable, os.path.join(HERE, "test_the_ask_route_waits_for_its_question.py")], 60,
         why="#25 - his CHOOSE IN INBOX landed on a black Tools page. Not reproduced in Chrome; hardened against the "
             "one mechanism that yields that picture: a zero-size (not laid out) question is no longer 'landed', "
             "and the route retries inside its 40 x 80 ms budget. 4 cases, 2 red-proofs"),
    Gate("test_the_eye_workers_bound_their_writes",
         [sys.executable, os.path.join(HERE, "test_the_eye_workers_bound_their_writes.py")], 60,
         why="REG-1300 - v3391 bounded control_app's pipe WRITE and left its two twins in tv_diablo "
             "(VisionWorker.ask, OcrWorker.read): a worker that stops draining stdin held the vision/OCR lane "
             "for ever. The doctor row named both lines on the Mac and the ALT. The shipped classes are driven "
             "against a stdin-deaf worker with a payload past the pipe buffer. 5 cases, 4 red-proofs"),
    Gate("test_a_last_seen_is_aged_at_its_own_snapshot",
         [sys.executable, os.path.join(HERE, "test_a_last_seen_is_aged_at_its_own_snapshot.py")], 60,
         why="REG-1302 - the 'a present machine has a fresh last-seen' doctor row aged ONE cached roster against "
             "the check's own clock, so it measured the cache: 'GrokBot (57m); Konyo ALT TEST (58m); Konyo (59m)' "
             "while the same rows were 133-226 s old. Now aged at the roster's own clock. 5 cases, 2 red-proofs"),
    Gate("test_a_windows_console_is_seen_by_its_own_os",
         [sys.executable, os.path.join(HERE, "test_a_windows_console_is_seen_by_its_own_os.py")], 60,
         why="REG-1303 - window_visibility asked only Quartz, so on the ALT (Windows) the console's covered/on-screen "
             "witness was always UNKNOWN and the silence rescue reloaded a console Citrix was covering: 13 rescues "
             "since 09-20, 7 in one night. A Win32 window list now feeds the same layer/union/95% arithmetic; the "
             "shipped silence branch is driven through it. 10 cases, 4 red-proofs"),
    Gate("test_esc_on_a_console_panel_never_quits",
         [sys.executable, os.path.join(HERE, "test_esc_on_a_console_panel_never_quits.py")], 60,
         why="REG-1304 - Esc on THE STATE OF THIS CONSOLE (its own X says 'close (Esc)'), the fleet window, the heart "
             "or a receipt's full frame closed the panel AND quit his console: each listener closed its panel without "
             "marking the key, so the v1420 empty-page handler saw an empty page. What is open is now read at PRESS "
             "time in a window-capture listener. The shipped listeners run in node in the page's own order. "
             "7 cases, 3 red-proofs"),
    Gate("test_the_console_serves_his_install_font",
         [sys.executable, os.path.join(HERE, "test_the_console_serves_his_install_font.py")], 60,
         why="#174 v-B2 - the d2planner sets item text in Blizzard's Exocet, which may never be committed to this public "
             "repo; his install carries it (68,596 bytes, OTTO), so the console streams it from there, in memory only, "
             "404 + the reason without an install, never a non-font, never a name outside its table. 5 cases, 3 red-proofs"),
    Gate("test_a_page_error_names_where_it_died",
         [sys.executable, os.path.join(HERE, "test_a_page_error_names_where_it_died.py")], 60,
         why="REG-1306 - the render gate refused a push on 'Cannot read properties of null (reading innerHTML)' "
             "and kept only that first line, so an intermittent red (clean alone and in a full rerun) named what "
             "died and never where. It now keeps the first stack frame. The shipped collector is driven on a fake "
             "CDP socket. 3 cases, 2 red-proofs"),
    Gate("test_no_child_opens_a_window_on_windows",
         [sys.executable, os.path.join(HERE, "test_no_child_opens_a_window_on_windows.py")], 60,
         why="REG-1307 - on Windows a terminal window kept jumping up and alt-tabbing him (and Dean) out of the game: "
             "pythonw has no console, so each console-subsystem child gets a visible one unless it passes "
             "CREATE_NO_WINDOW, and 82 spawn sites did not. win_quiet replaces subprocess.Popen once per process "
             "(console + agent) so every spawn is windowless. Driven on a fake Windows subprocess module. "
             "4 cases, 4 red-proofs"),
    Gate("test_no_new_home_path_is_published",
         [sys.executable, os.path.join(HERE, "test_no_new_home_path_is_published.py")], 60,
         why="#27 - the repo is PUBLIC and 113 /Users/<name>/ literals sat in 65 tracked files, two of them live code in "
             "the published bible.html (the routine loader) and one in the generated BLUEPRINT.md. Those are gone; the rest "
             "are history. A ratchet over `git ls-files`: every tracked file is pinned at its count and may only keep or "
             "lower it, so a new home path is refused before it is published. The counter is driven on a fixture "
             "(a real path counts; an escaped regex, a placeholder and a bare prefix do not)."),
    Gate("test_no_law_hands_node_its_program_on_argv",
         [sys.executable, os.path.join(HERE, "test_no_law_hands_node_its_program_on_argv.py")], 60,
         why="#242 - REG-1308's mule laws were green on his Mac and errored on every CI run: `node -e <program>` "
             "handed a 134 KB / 422 KB program as ONE argument and Linux caps one at 131,072 bytes. 27 more sites in "
             "25 law files carried the same trap and moved to stdin; this reads every tv/test_*.py (ast) and refuses "
             "a node call that passes a non-literal program after -e. 2 cases, 2 red-proofs"),
    Gate("test_a_killed_prover_leaves_no_sandbox",
         [sys.executable, os.path.join(HERE, "test_a_killed_prover_leaves_no_sandbox.py")], 60,
         why="MEASURED 2026-09-26: 11 heart2.* repo copies in the temp dir, one per interrupted --prove (the gate's "
             "bound, a perl alarm) - a finally never runs under a signal. heart2 now registers each sandbox with its "
             "owner's pid, removes them on SIGTERM/SIGALRM/SIGHUP, and sweeps a dead owner's (or an ownerless day-old "
             "one) before every --prove. Driven with real signals on a real child. 5 cases, 4 red-proofs"),
    Gate("test_no_harness_leaves_its_scratch",
         [sys.executable, os.path.join(HERE, "test_no_harness_leaves_its_scratch.py")], 300,
         why="#171's class in PRODUCTION code: MEASURED 2026-09-26, per day, 1,890 diskrep_* (the disk proof, every "
             "doctor pass), 196 heartlane_*, 77 sweep*_, 48 empty tvd-gates-* (minted at import), 26 killed-run Chrome "
             "profiles, 15 vault-sim-*, 5 rrw_*. The harnesses run end to end in a child with its own TMPDIR and must "
             "leave it empty; the static list is #171's ratchet (lowered 24 -> 2 by this fix). 3 cases, 5 red-proofs"),
    Gate("test_the_affix_tables_are_the_installs",
         [sys.executable, os.path.join(HERE, "test_the_affix_tables_are_the_installs.py")], 90,
         why="#174 v-B3 - the Edit tab's ADD MOD and the sheet read the CB_DB block's af / rn / qm rows, generated from "
             "his install's magicprefix / magicsuffix / automagic / rareprefix / raresuffix / qualityitems / "
             "lowqualityitems. Counted and shaped; a named sample hand-read from the tables (Chaotic, of Vita, Ruby, "
             "Crimson's maxlevel, the frequency-0 classic Sturdy kept and marked); the rare words equal "
             "tv/affix_lexicon.json's (a different generator); quality flags per type, never inherited (a Grand Charm is "
             "magic only); where the install is, every spawnable row re-read from the raw table and --check 0. FIX "
             "ROUND: a base's magic lvl (b[23]) beside its qlvl; an affix's class level requirement (of Magic Arrow: 11, "
             "an Amazon 1); every one of the 112 charged skills the table gives as negative is ONE UNKNOWN line, never "
             "\"Level -10\"; the six rare words the item strings miss are named by monsters.json / ui.json (Ghoul, "
             "Wraith, Fiend, Crusher, Scarab, Strap). 7 cases, 10 red-proofs"),
    Gate("test_the_item_edit_tab_builds_magic_and_rare_items",
         [sys.executable, os.path.join(HERE, "test_the_item_edit_tab_builds_magic_and_rare_items.py")], 90,
         why="#174 v-B3 - their Select -> Quality -> Edit over the game's affix tables, driven on the SHIPPED modal in "
             "node: a Diadem waits on Rare / Magic / Superior / Normal / Low, a ring on Rare / Magic, a Grand Charm goes "
             "straight to Edit as magic; ADD MOD filters by type, level, maxlevel, group, class, the rare flag, the "
             "automod group and the quality's limits (magic 1+1, rare 3+3, a rare jewel 4); a roll outside its range is "
             "refused; a picked mod reaches the stored entry, the tooltip, the composed name and STATS; an old build "
             "loads unchanged; Esc closes ADD MOD first. FIX ROUND: an affix is held against the AFFIX level (alvl from "
             "the item level, qlvl and magic lvl - of Vita on a Small Charm needs item level 61; a Diadem at 85 keeps its "
             "level-90 prefixes); an item born with Enhanced Defense sits at its base's max + 1 (a Godly Diadem +200% is "
             "183, its Defense box 61, fixed); a class's own level requirement; a negative charged skill is UNKNOWN; two "
             "affixes of one stat print one line (135 mana, not 67 twice); ADD MOD is a combobox (the active option "
             "painted, ArrowDown moves it, Enter adds it) with no AUTOMOD header over nothing; the six rare words offered. "
             "11 cases, 19 red-proofs"),
    Gate("test_the_character_sheet_sums_picked_affixes",
         [sys.executable, os.path.join(HERE, "test_the_character_sheet_sums_picked_affixes.py")], 90,
         why="#174 v-B3 - D2R_CHAR_ENGINE sums the affixes he picked exactly like a unique's props (typed EXACT, "
             "untouched RANGE, never averaged): a magic Grand Charm (Chaotic + of Vita) moves exactly the Chaos Skills "
             "and Life rows; a rare Diadem's three mods sum; a typed base defense is EXACT, a superior row raises its own "
             "item, a low-quality base's defense is UNKNOWN, an unknown affix id is an UNKNOWN row naming it, none "
             "picked stays UNKNOWN and says so. Hand-worked from the tables; the two generators name the same affix "
             "rows. FIX ROUND: a magic / rare / superior item born with Enhanced Defense sits at its base's max + 1 "
             "(Godly Diadem +200% = 183 EXACT; superior +15% = 70, the typed base set aside); a negative charged level "
             "is UNKNOWN, never -10 EXACT; two affixes of one per-level stat are one stat, scaled once (135, not 134); "
             "the sheet names the affix the item shows (Mojo, never the table key Vodoun). 16 cases, 12 red-proofs"),
    Gate("test_the_tooltip_is_the_games_tooltip",
         [sys.executable, os.path.join(HERE, "test_the_tooltip_is_the_games_tooltip.py")], 90,
         why="#174 v-B4 - the SHIPPED tooltip (_cbTipEntry + d2Tip, in node) equals THEIR tooltip text, line for line, "
             "on 203 measured rows (Breath of the Dying on 40 bases incl. the 7 of the brief, Grief, Spirit, Insight, "
             "Call to Arms, Heart of the Oak; tv/the_tooltip_oracle.json, text only): damage with ED lo..hi floored, "
             "Durability, requirements base + trunc(base x pct / 100) (Hel: 94 -> 76), the rune string, '<Class> Class - "
             "<Speed> Attack Speed' from animdata frames + the game's formula + the measured bands (10-13 Very Fast, "
             "14-15 Fast, 16-19 Normal, 20-22 Slow, UNKNOWN outside), the runeword's and its runes' lines merged (+200% "
             "Damage to Undead, +30 to all Attributes) and ordered by descpriority / descfunc / stat id, their range "
             "form. Three differences declared and asserted where they apply: a sword's class line (theirs none), a "
             "blunt base's +50% undead (the game's code - ours UNKNOWN), an untyped IAS roll across two bands (ours "
             "both words; typed at its top, theirs). Annihilus: Keep in Inventory + ONE all-Attributes roll; a unique "
             "and a set item keep their own lines. 8 cases, 10 red-proofs"),
    Gate("test_the_save_reader_watches_its_tables",
         [sys.executable, os.path.join(HERE, "test_the_save_reader_watches_its_tables.py")], 60,
         why="#174 - the .d2s reader decodes against tables generated once from his install; a patch that moves a "
             "stat's bit width makes every import decode wrong while it still looks like items. Its doctor row "
             "re-derives sourceHash: fresh OK, stale MISSING, no install UNKNOWN. 4 cases, 1 red-proof"),
    Gate("test_the_skill_trees_come_from_the_install",
         [sys.executable, os.path.join(HERE, "test_the_skill_trees_come_from_the_install.py")], 120,
         why="#174 - the planner's three skill trees per class come from his install's CASC (skills.txt, skilldesc, "
             "charstats, playerclass, the HD tree layout, the string tables), never from memory: 8 classes (the "
             "Warlock included), exactly 3 tabs each, every skill inside the layout's own 6 x 3 grid, every "
             "prerequisite in the same class and tab, SkillRow agreeing with reqlevel. A key is not a name "
             "(Wearwolf), a page is not a tab position (the Druid's page 3 is Elemental, leftmost; the Warlock's "
             "leftmost key is Wa3), and a tab order the tables do not settle is UNKNOWN. A fake install runs "
             "everywhere; the json's sourceHash and content match a fresh build when the install is present, "
             "UNMEASURED otherwise. 23 cases, 5 red-proofs"),
    Gate("test_the_eye_reads_the_commit_read_only",
         [sys.executable, os.path.join(HERE, "test_the_eye_reads_the_commit_read_only.py")], 60,
         why="#169 Win 2 (his ruling: the Grok CLI) - the eye ran in an EMPTY folder on pasted text. It now gets the "
             "reviewed commit's changed files AS AT THAT COMMIT (git archive, never the live tree), read-only, oversized "
             "files named not dropped, and a prompt that names them and bounds it. 5 cases, 4 red-proofs"),
    Gate("test_every_decision_file_is_ignored",
         [sys.executable, os.path.join(HERE, "test_every_decision_file_is_ignored.py")], 60,
         why="#223's answers store (tv/his_answers.json) shipped with no ignore line and his first answer sat untracked "
             "in a PUBLIC repo. Fourth time for this class; every _decision_path name is now read out of the code and "
             "asked of git check-ignore, primary and scratch form. 2 cases, 1 red-proof"),
    Gate("test_the_console_window_claims_its_own_board",
         [sys.executable, os.path.join(HERE, "test_the_console_window_claims_its_own_board.py")], 60,
         why="#239 - his go: wire the one synced identity from what exists. The console's claim door wrote '*' with no "
             "ledger name and nothing called it. Now one routine claims + names the ledger; it runs by itself only in "
             "a pywebview window on a store with no claim, and only when this machine never held a populated board "
             "(no ledger snapshot, no banked count) - restore, never reseed. 12 cases, 5 red-proofs"),
    Gate("test_each_console_shows_its_own_counts",
         [sys.executable, os.path.join(HERE, "test_each_console_shows_its_own_counts.py")], 60,
         why="#240 - from his ALT, Konyo's and GrokBot's fleet rows showed no numbers while Dean's did ('as if im "
             "the same person on all three'). The rows were individual; every v3504 tally sealed measured=False "
             "over SYNCED ledgers (the authority was asked before ok was sealed, and the seal keyed on 'EARNED', "
             "a word the authority never says), and the card blanks a False. Now per ledger (measuredBy) through "
             "seal, relay, card and doctor. 11 cases, 5 red-proofs"),
    Gate("test_a_character_save_reads_byte_exact",
         [sys.executable, os.path.join(HERE, "test_a_character_save_reads_byte_exact.py")], 60,
         why="tv/d2s_read.py reads a D2R .d2s (format 105): an item bitstream has no per-item length, so one "
             "misread bit leaves item-shaped garbage; the only witness is ending exactly on the corpse 'JM'. "
             "A synthetic save (the repo is public - his saves never enter it) round-trips every field; a short "
             "count, a missing format-105 bit, truncation and a bad checksum all come back ok=False with the byte; "
             "a runeword past runes.txt row 79 is UNKNOWN, never guessed. His TESTCLAUDE.d2s (49 items, "
             "Jalal's Mane) and BLANK.d2s (28 items, none equipped, the study's sniffed pad read as a trailing bit) "
             "are MEASURED when present, UNMEASURED otherwise. 21 cases, 7 red-proofs"),
    Gate("test_a_receipt_row_is_not_a_beat",
         [sys.executable, os.path.join(HERE, "test_a_receipt_row_is_not_a_beat.py")], 60,
         why="#238 - a `deep-owed` receipt row (a deep read committed to a frame) was journaled with no ts and "
             "emitted by the theatre session builder as a playable beat that sorted as 1970; test_roundtrip_sim "
             "errored wherever tv/frames exists (never on CI). The builder skips receipts (legacy rows have no ts) "
             "and the writer stamps its time; each proven on its own. 4 cases, 2 red-proofs"),
    Gate("test_escape_answers_the_question_no",
         [sys.executable, os.path.join(HERE, "test_escape_answers_the_question_no.py")], 60,
         why="the second eye on v3497: Escape with an in-page inbox question up closed the INBOX (a capture-phase "
             "listener ran first and stopped the event), left 'Promote all N' armed, and the next Escape reached "
             "the empty-page handler and POSTed /api/quit. The real handlers run in node through a capture/bubble "
             "dispatcher; on the shipped code the law reproduces the quit. 5 cases, 3 red-proofs"),
    Gate("test_a_child_s_words_are_read_as_utf8_on_every_os",
         [sys.executable, os.path.join(HERE, "test_a_child_s_words_are_read_as_utf8_on_every_os.py")], 60,
         why="#229 - measured on his Windows ALT: the visual-lock row ran its child with text=True and no encoding, "
             "Python decoded the child's emoji with cp1255, and the reader thread died. 42 production calls had "
             "the shape (invisible on the Mac's UTF-8 locale); all pass encoding='utf-8' now. AST sweep with a "
             "premise. 2 cases, 1 red-proof"),
    Gate("test_a_pass_says_which_check_it_is_in",
         [sys.executable, os.path.join(HERE, "test_a_pass_says_which_check_it_is_in.py")], 60,
         why="#229 - his Windows ALT read 'not measured yet' for 14+ minutes after boot while the same checks "
             "finished standalone in ~6 minutes, and nothing could name the check the pass sat in. The doctor "
             "records the running check (CURRENT) and eagle_state() publishes it as `measuring`. 2 cases, "
             "3 red-proofs"),
    Gate("test_free_space_is_measured_on_every_os",
         [sys.executable, os.path.join(HERE, "test_free_space_is_measured_on_every_os.py")], 60,
         why="#229 - river.py, safe_copy and space_warden measured free disk with os.statvfs, which does not "
             "exist on Windows: the river's disk joint read UNKNOWN on every Windows console and safe_copy "
             "could never prove its 4 GB floor there. shutil.disk_usage everywhere; driven with statvfs "
             "removed, plus an AST sweep. 4 cases, 2 red-proofs"),
    Gate("test_the_frozen_screen_watch_reads_only_recent_looks",
         [sys.executable, os.path.join(HERE, "test_the_frozen_screen_watch_reads_only_recent_looks.py")], 60,
         why="measured 2026-09-24: the evidence shelf grew to 9,325 PNGs / 3.2 GB and frozen_frame_watch walked "
             "all of it on every doctor pass - 'screen still painting' took 337.5 s and a push was refused as "
             "test_control HUNG at its 1500 s bound on an idle machine. It reads the newest 12 top-level "
             "entries now (0.1 s, same verdict). 3 cases, 1 red-proof"),
    Gate("test_this_machine_can_decode_a_frame",
         [sys.executable, os.path.join(HERE, "test_this_machine_can_decode_a_frame.py")], 60,
         why="#227 - measured over SSH: his Windows ALT ran Python 3.12.10 with pywebview and NO Pillow, so "
             "every frame it filmed was unreadable and nothing said so. The launcher and installer now "
             "install Pillow; the doctor row 'this machine can decode a frame' round-trips a BMP (the "
             "Windows capture's format) pixel for pixel. 6 cases, 3 red-proofs"),
    Gate("test_a_fresh_machine_establishes_its_tree_at_boot",
         [sys.executable, os.path.join(HERE, "test_a_fresh_machine_establishes_its_tree_at_boot.py")], 60,
         why="#227 - the one boot-shaped machine_tree.establish() sat inside _prewarm_seal_cache, which returns "
             "at once on Windows and otherwise runs only after a capture session STOPS - never at boot. A "
             "fresh machine established nothing until it filmed, and 'this console tree is established' "
             "read MISSING for as long as that took. main() now establishes at boot on every platform; a "
             "scratch console provisions nothing. 4 cases, 3 red-proofs"),
    Gate("test_the_windows_eye_is_found_by_its_exe",
         [sys.executable, os.path.join(HERE, "test_the_windows_eye_is_found_by_its_exe.py")], 60,
         why="#227 - on his Windows ALT box grok.exe existed and was on PATH, the resolver listed no .exe and "
             "second_eye_run hardcoded ~/.grok/bin/grok, so the doctor said 'no binary there'. Driven on a "
             "Windows-shaped home: the resolver, the second eye and the doctor row all find the .exe. "
             "4 cases, 2 red-proofs"),
    Gate("test_the_sets_count_asks_for_a_fresh_page",
         [sys.executable, os.path.join(HERE, "test_the_sets_count_asks_for_a_fresh_page.py")], 60,
         why="#228 - his screenshot 2026-09-24 11:13: the chronicle-sweep panel drew 'the board and the game "
             "do not add up' RED, reading as if he had done something wrong. Measured: it rested on a "
             "Remaining page filmed 2026-08-21 (the card said 24.5 days; it was 34) while the game's own bar "
             "agreed with his board, and its next-action said 'the two wrong rows' for 16. The card is calm "
             "and folded, ages the page from readAt, and the one line that was his - film a new Remaining "
             "page - is a WAITING ON YOU question (doctor 'a fresh remaining page', every tick). A grok-4.7 "
             "look at the OPENED card found the raw alarm inside it; it shows the measurement; the eye on v3498 aligned card and doctor. 17 cases, "
             "8 red-proofs"),
    Gate("test_a_slow_census_is_still_remembered",
         [sys.executable, os.path.join(HERE, "test_a_slow_census_is_still_remembered.py")], 60,
         why="#237 - the heart memo aged from when the census STARTED, so a census slower than its 45s "
             "TTL was born expired: inside a push at load ~7 /api/heart took 48.3s, the panel's own fetch "
             "one click later walked the source again, and the render gate refused the heart panel. "
             "Reuse now counts from when it LANDED; the shown age is still the reading's. 6 cases, "
             "3 red-proofs"),
    Gate("test_a_scratch_console_never_films_his_screen",
         [sys.executable, os.path.join(HERE, "test_a_scratch_console_never_films_his_screen.py")], 60,
         why="#236 - mid-push the render gate's private (stub) console went live, pinned HIS GeForce NOW "
             "stream and captured it frame after frame into its sandbox: console 84% CPU, render starved "
             "at load 12.6, push refused (earlier the same console filmed a Finder window). TV_CAPTURE=off "
             "now refuses every capture and calls nothing that reads a window; the harness spawns its "
             "console with it (AST-checked). 3 cases, 2 red-proofs"),
    Gate("test_the_eye_finds_d2r_however_he_runs_it",
         [sys.executable, os.path.join(HERE, "test_the_eye_finds_d2r_however_he_runs_it.py")], 60,
         why="#232 - his order: the eye targets D2R however he runs it - Mac CrossOver, GeForce NOW or "
             "Boosteroid (their app or a browser tab), Windows local D2R.exe plus the same cloud routes, "
             "and Linux pins nothing (they lock there). Before: every browser was blocked on the Mac and "
             "Windows only enumerated D2R-process windows, so a streamed session fell through to FULL "
             "SCREEN. A browser needs the service AND the game in its title; '\u00ae/\u2122' are "
             "normalized; a service window without the game is reported, never pinned. Real cloud "
             "titles UNMEASURED. The second eye on v3496: a game word is a WORD, a browser is its whole "
             "name, a title naming two services never pins, the scorer normalizes first, a refused cloud "
             "window is named. 19 cases, 9 red-proofs; the C# twin compiles and agrees on the Windows box"),
    Gate("test_a_title_is_not_an_owner",
         [sys.executable, os.path.join(HERE, "test_a_title_is_not_an_owner.py")], 60,
         why="#223 - with no game open, the eye pinned a FINDER window titled 'tv-diablo-mailbox' as the "
             "game (score 1602: 'diablo' in the title was the whole qualification) and a stub console "
             "filmed his desktop; the render gate then flaked on whichever window was in front. A title "
             "that mentions the game qualifies only with a game/wine/CrossOver/d2r-named owner or one he "
             "named in TV_WINDOW_MATCH. 3 cases, 1 red-proof"),
    Gate("test_a_resize_callback_defers_its_layout",
         [sys.executable, os.path.join(HERE, "test_a_resize_callback_defers_its_layout.py")], 60,
         why="#223 - the render gate's inbox target went red three runs straight on one uncaught "
             "'ResizeObserver loop completed with undelivered notifications' (and on v3493's page too: "
             "the loop was old, the load was new). _inboxSync re-sized the element it observes inside "
             "the delivery loop. Every observer in bible.html defers its layout one frame, coalesced. "
             "Structural count + _roDefer driven in node. 2 cases, 2 red-proofs"),
    Gate("test_his_answer_closes_only_its_question",
         [sys.executable, os.path.join(HERE, "test_his_answer_closes_only_its_question.py")], 90,
         why="#223 - his answer from the mailbox: one per question with its fingerprint (a changed "
             "question reopens, a lapsed answer reopens, an unreadable store is never written over), "
             "applied at read time so the count moves in the same request, in its own bucket (never "
             "CLAUDE OWES). POST /api/board_answer refuses a foreign/missing Origin (_cors answers *), "
             "an automated browser, no explicit yes, a guest board, nothing measured, an undeclared "
             "question or answer, a stale fingerprint - each named, none writing. 15 cases, 5 red-proofs"),
    Gate("test_a_row_is_his_only_when_it_asks",
         [sys.executable, os.path.join(HERE, "test_a_row_is_his_only_when_it_asks.py")], 90,
         why="#226 - his ruling: 'it should only really be waiting on me if its something i need to do'. "
             "Measured: WAITING ON YOU read 5 and ONE was his. v2284 made every unlisted check his by "
             "default; a red row now bills him only while its check DECLARES a question (console_doctor.ASKS: "
             "what is needed, why, the answers), and every other red row lands under Claude's work, still "
             "drawn. Fails loud: a pre-registry row or an unreadable registry bills him as before. The "
             "server publishes needsYouWhat and the mailbox reads it instead of re-deciding (it billed 7 "
             "where the console billed 5). 8 cases, 4 red-proofs"),
    Gate("test_an_entrance_survives_endurance",
         [sys.executable, os.path.join(HERE, "test_an_entrance_survives_endurance.py")], 60,
         why="#228 - his ⚙ ADVANCED drawer read open with black under it and its tooltips answering from "
             "the black: after 10 minutes every console enters endurance and pauses `*`, so a one-shot "
             "fade-in that starts later starts PAUSED AT OPACITY 0 (the EYES switch, the shadow reader, "
             "and 27 other entrances). Every invisible-start entrance must be exempted from the pause; "
             "derived from the keyframes, so a new fade-in without it goes red. 4 cases, 2 red-proofs. "
             "The on-pixels half is render_check's ADVANCED targets, now judged UNDER endurance"),
    Gate("test_an_exec_leaves_no_corpse",
         [sys.executable, os.path.join(HERE, "test_an_exec_leaves_no_corpse.py")], 90,
         why="#224 - 35 <defunct> ocr_mac children under his console, one per in-place os.execv relaunch "
             "(measured by ucomm + start times, 36/36): every exec site now quiesces the warm workers "
             "first, and main() reaps inherited children BY PID before it spawns anything. Driven on "
             "real processes with a baseline that reproduces the leak. 5 cases, 3 red-proofs"),
    Gate("test_a_mark_covers_only_what_was_shown",
         [sys.executable, os.path.join(HERE, "test_a_mark_covers_only_what_was_shown.py")], 60,
         why="the handoff watermark covers only what a drain SHOWED (2026-09-24 07:09Z: --mark filed "
             "an unseen GrokBot tick as read by taking the newest comment at mark time); --through "
             "names the last comment read; newer comments are named, never swallowed; and --summary, "
             "the line the prompt hook prints every turn, counts new and ACT/ASK-owed and says "
             "UNKNOWN when the queue cannot be read. 5 cases, 2 red-proofs"),
    Gate("test_production_scratch_dirs_only_get_fewer",
         [sys.executable, os.path.join(HERE, "test_production_scratch_dirs_only_get_fewer.py")], 60,
         why="#171 - a production mkdtemp with no cleanup in its own function may only get FEWER: "
             "24 frozen by (file, function), the list must shrink the moment one is fixed, and the "
             "one cross-function teardown (render_check's Chrome profile) is declared with a reason "
             "re-proven by AST. Read by the parser, never by text. 5 cases, 2 red-proofs"),
    Gate("test_a_conditional_reap_is_not_a_reaper",
         [sys.executable, os.path.join(HERE, "test_a_conditional_reap_is_not_a_reaper.py")], 60,
         why="#177 - a helper counts as a reaper only if it reaps its first parameter on EVERY path "
             "(its own level, first in a try, a finally, a with; never behind an exit, a branch or "
             "an earlier raising statement in the same try - the v3421 shape). The call site is read "
             "by the parser, so keyword hand-offs count. 5 cases, 4 red-proofs"),
    Gate("test_an_established_empty_shelf_is_not_footage",
         [sys.executable, os.path.join(HERE, "test_an_established_empty_shelf_is_not_footage.py")], 60,
         why="#123 - a directory machine_tree.establish() built is not his shelf: EMPTY skips like "
             "ABSENT only when this host's ledger never closed a reel; an emptied shelf or an "
             "unreadable ledger stays 'present' so the walked-nothing FAIL still fires. Both main() "
             "exits ask the one SKIPPED decision. 9 cases, 4 red-proofs"),
    # v2570 — the printer had NO lock; fourteen were declared and not one named the river.
    Gate("test_printer_wilson", [sys.executable, os.path.join(HERE, "test_printer_wilson.py")], 90,
         why="the printer walks every reel he owns and nothing had ever attempted to break it. "
             "These pin that its harness cannot ACT (AST, not prose — the first cut matched the "
             "docstring promising safety), and that prune.arm waits on printer.stream so the "
             "deleter cannot open before the river feeding it."),
    Gate("printer_wilson", [sys.executable, os.path.join(HERE, "printer_wilson.py")], 240,
         why="runs the five printer sabotages themselves: an owner that raises, every owner "
             "empty, rows naming no reel, a reel only one owner knows, and printer_reach "
             "raising. The printer must say UNKNOWN with a reason rather than invent one."),
    Gate("test_app_ctx_nav", [sys.executable, os.path.join(HERE, "test_app_ctx_nav.py")], 120,
         why="the board hid its own tab row on a URL flag and never checked the flag was "
             "true (REG-443). `?engine=1` is written only by the #tvd-eng iframe, and the "
             "CSS it arms hides the whole rail because inside the shell the console header "
             "IS the rail; top-level there is no rail and he was left with 0 of 19 tabs. "
             "Pins two LAWS: every site adding `engine-driven` tests for a real frame, and "
             "every tab re-shown in app context lives in .tabs-workshop — which is the "
             "premise under hiding the otherwise-empty .tabs-data cluster frames"),
    Gate("test_dom_probe", [sys.executable, os.path.join(HERE, "test_dom_probe.py")], 120,
         why="five DOM probes in one night measured something ADJACENT to the question and each "
             "produced a confident sentence: `body *` returned <script> source as screen text "
             "(twice), a clip test on an inline box can never be true because clientWidth is 0, an "
             "occlusion test sampled the coverer's own centre instead of the target, a text search "
             "grabbed a 183x33 inner div instead of the 925x118 panel under discussion, and a "
             "colour check looked for a class instead of asking what the element PAINTS. This pins "
             "each correction in the JS the probes actually inject."),
    Gate("test_build_stamp", [sys.executable, os.path.join(HERE, "test_build_stamp.py")], 240,
         why="v1691.1 capped this badge deliberately and ruled 'id + date must survive; the name is "
             "the decoration that clips'. Underneath that rule the version NAMES grew to 45 "
             "characters in a box fitting 24, so the decoration was ALWAYS cut mid-word — 259px of "
             "437 hidden. Two independent cold cross-family reads called that fragment an "
             "unintended cut-off, and the second one had just correctly identified a genuinely "
             "deliberate overlay elsewhere as intentional, so it distinguishes deliberate from "
             "broken. Pins the law that whatever the stamp renders it renders WHOLE — dropping the "
             "decoration is allowed, ending mid-word is not — while protecting v1691.1's actual "
             "rule that id and date survive and the full note stays one hover away."),
    Gate("test_classify_corroborator",
         [sys.executable, os.path.join(HERE, "test_classify_corroborator.py")], 240,
         why="every member of a roster should classify the same way, and nothing had ever compared "
             "them. On its first run 9 of 398 uniques did NOT resolve to unique: four carried a "
             "curly apostrophe where every lookup table holds a straight one, four (Harlequin "
             "Crest, Hellfire Torch, Gull, The Cranium Basher) were in no table at all and rendered "
             "with no rarity, and one is a genuine dual-name. The two dual-names are DECLARED with "
             "their reasons, and the gate also fails if a declaration stops being true — a stale "
             "exception is how a corroborator quietly stops finding anything."),
    Gate("test_manual_witness", [sys.executable, os.path.join(HERE, "test_manual_witness.py")], 120,
         why="every tag witnesses() produced came from reels and frames, so a manual tick — which "
             "has neither — earned NO witness at all, while an OCR read of a blurry row counted "
             "twice. His ruling is that a manual tally is witness enough. Holds four laws: his hand "
             "earns its OWN tag and never a synonym for another; a tick banks a row the witness "
             "counter can actually read; saying it twice is not two witnesses; and ownership alone "
             "never mints one, because no rule manufactures testimony never given."),
    Gate("test_type_floor", [sys.executable, os.path.join(HERE, "test_type_floor.py")], 120,
         why="16 nodes rendered below the 13px floor at his real 1120x628 and NOTHING in the "
             "stylesheet was typed below it. Two font tokens were referenced and never defined, so "
             "every use silently rendered at its fallback — 12px and 10px — and an audit for small "
             "numbers would have found nothing. A fallback is a font size nobody reviewed. Pins two "
             "rules: no fallback below the floor, and no BARE reference to an undefined token "
             "(which makes the declaration invalid, so the element inherits and the size an author "
             "wrote has no effect)."),
    Gate("test_ledger_parity", [sys.executable, os.path.join(HERE, "test_ledger_parity.py")], 120,
         why="the console has published 'every ledger this machine can build' since v2329 and the "
             "worker receiving those masks stored exactly one of them, so a uniques mask would be "
             "discarded on arrival and the uniques cross-reference could never work end to end. "
             "Grok measured the board side, I confirmed it from the live record, and BOTH of us "
             "were looking at the wrong end. This pins the rule that the two ends carry the same "
             "set — never the roster, so adding a third ledger stays legal."),
    Gate("test_roster_routes", [sys.executable, os.path.join(HERE, "test_roster_routes.py")], 180,
         why="a roster reaches a screen through declared -> getter -> probe -> wire -> unit, and "
             "nothing compared those chains to each other. On its first run against this tree it "
             "flagged that runewords carried no UNIT on the fleet card while sets and uniques "
             "did — my defect, found by his corroborator. Proven both ways: 2-vs-1 flags and "
             "names the siblings, 1-vs-1 stays silent because a coincidence is not a divergence."),
    Gate("test_paint_witness", [sys.executable, os.path.join(HERE, "test_paint_witness.py")], 180,
         why="he reported a black console twice while its beat was perfectly healthy — n advancing, "
             "els 11,707, blankStrikes 0, rescues 0 — because the blank detector counts DOM "
             "elements and his blank has a full DOM. setInterval and requestAnimationFrame are "
             "throttled by different machinery, so a page that stops PAINTING keeps every "
             "timer-driven signal green. This holds the three-valued paint witness and, as much as "
             "the code itself, the rule that it must NOT claim which of two causes it is seeing."),
    Gate("test_chronicle_routes", [sys.executable, os.path.join(HERE, "test_chronicle_routes.py")], 180,
         why="the uniques / sets / runewords rosters are siblings and should carry the same lanes. "
             "The runeword roster was stamped at write time and NOTHING ever re-checked that "
             "stamp, so it was correct on the day and nothing would say a word when it stopped. "
             "This holds the corroborator that names the odd one out, and the rule that a "
             "describer never counts as a watcher."),
    Gate("test_fleet_routes", [sys.executable, os.path.join(HERE, "test_fleet_routes.py")], 180,
         why="window._gSetRoster was never defined in bible.html while the console asked for it "
             "on every read, so the fleet card's set denominator was null forever and printed a "
             "bare number with an indeterminate bar. This holds the rule that a MENTION is not a "
             "definition, and that an unknown total never reads as a missing one."),
    Gate("test_vault_doctor", [sys.executable, os.path.join(HERE, "test_vault_doctor.py")], 120,
         why="v2013 — the doctor answers 'why is the vault empty', and its three causes need three "
             "different actions from him. On his real tree it reports ONE of them, so without these "
             "a doctor that had lost the ability to say the other two would look identical: every "
             "case runs on a TEMP fixture through TV_HIST, including the tooltip answer that is "
             "true today (220 occupied cells, zero names) and the measured-EMPTY mirror that must "
             "read OK rather than as a fault"),
    Gate("test_reel_retention", [sys.executable, os.path.join(HERE, "test_reel_retention.py")], 120,
         why="v2001 — the only script in this tree that DELETES his footage. On his real reels it "
             "correctly reports zero candidates today, so without these the safe answer and a broken "
             "one are the same output: they prove it can select, that a 0-page seal never qualifies "
             "(1166 MB of his film is in that state and the engine reopens it), that --apply refuses "
             "without --yes, and that it takes the right directory and leaves the rest"),
    Gate("test_vault_retro", [sys.executable, os.path.join(HERE, "test_vault_retro.py")], 120,
         why="the vault accumulator's laws: merge-max never subtracts, throw-out needs more "
             "evidence than keep, order cannot change the ledger, missing is never zero"),
    Gate("ui_icons", [sys.executable, os.path.join(HERE, "extract_ui_icons.py"), "--check"], 60,
         why="v1614 — every console tab and MINI focus icon is present in art/. The icons are "
             "committed PNGs; this proves none was deleted or renamed out from under the HTML, "
             "which fails SILENTLY: each <img> carries onerror=this.remove(), so a missing file "
             "leaves a tidy label with no picture rather than anything that looks broken"),
    Gate("test_reachability", [sys.executable, os.path.join(HERE, "test_reachability.py")], 120,
         why="LAW19 as a gate, not an intention — BOTH halves. Every DOM id READ must be WRITTEN "
             "in the same document, and every `typeof X === function` guard must name a symbol "
             "that exists. Six bugs were this one shape: REG-083/087, the v1576 dead-safe "
             "classifier, the v1593 TZ crash, ~680 versions of unreachable shelf code (REG-095), "
             "and five ownership changes that never repainted (REG-096)"),
    Gate("test_free_pass_quote", [sys.executable, os.path.join(HERE, "test_free_pass_quote.py")], 180,
         why="the free pass may never quote BELOW what a real sweep spends — it priced only the "
             "classify lane and structurally could not count a page read (v1596)"),
    Gate("test_chronicle_retro", [sys.executable, os.path.join(HERE, "test_chronicle_retro.py")], 300,
         why="the retro sweep's three laws: read-only until Apply, merge-max, pay-for-runs"),
    # v2387 — the swallowed-exception RATCHET, in the same gate set as everything else so it has
    # one verdict rather than being a thing someone remembers to run. It grades RANK 1 only —
    # a failed read handed back as DATA — and only fails when that count GROWS.
    Gate("swallow_ratchet", [sys.executable, os.path.join(HERE, "swallow_census.py"), "--check"],
         120,
         why="a failed read must not be handed to a caller as 0 / {} / [] / '' — 'nobody could "
             "ask' and 'measured zero' are opposite facts, and every wrong-number-on-screen scar "
             "in this project has that shape. Ratchets down, never up"),
    Gate("test_reel_story", [sys.executable, os.path.join(HERE, "test_reel_story.py")], 120,
         why="the shelf's pipeline board reads the deciders and never becomes a second one: an "
             "unsurveyed reel stays UNKNOWN rather than scoring 0%, an unmapped retention verdict "
             "refuses instead of defaulting to 'releasable', and every rule reel_retention can "
             "emit has a stage"),
    Gate("test_chronicle_template", [sys.executable, os.path.join(HERE, "test_chronicle_template.py")], 300,
         why="the Chronicle panel's own template is measured, not guessed — the page frame, its "
             "NO TOOLTIP ITEM state, and the MINI-parameter geometry a live read leans on, so the "
             "consumers due in v1691 have a locked shape to read instead of re-deriving it each time"),
    Gate("test_reel_index_durability", [sys.executable, os.path.join(HERE, "test_reel_index_durability.py")], 300,
         why="a sealed reel must always carry a parseable index.json — even when the seal is "
             "interrupted mid-way — because theatre, read_reel and the retro sweep all enter "
             "through the index, and a reel of real frames without one plays BLACK"),
    Gate("test_g5_budget_units", [sys.executable, os.path.join(HERE, "test_g5_budget_units.py")], 120,
         why="g5_subscription_budget.json had TWO writers on TWO clocks — Python seconds, Node "
             "milliseconds — so Python could never prune a Node row (it reads as 1.78 million "
             "million seconds in the FUTURE) and Node deleted every Python row. The count only "
             "climbed, and at 30 the second eye pins itself OFF behind a legitimate-looking "
             "'hourly cap (30/30)' while the real call rate is zero. It stood at 9. This is the "
             "FIRST test that has ever existed on the G5 lane"),
    Gate("test_chronicle_known_wire", [sys.executable, os.path.join(HERE, "test_chronicle_known_wire.py")], 300,
         why="sweep_hist(known_chronicle=) shipped in v1689 and NOTHING EVER PASSED IT, so every "
             "retro sweep re-derived what the live agent had already identified and paid a "
             "classifier to disagree with it. Measured on his own reel: a classifier that "
             "recognises nothing reads 0 pages without the marks and 8 with them. This is the "
             "v1576 defect class again — plumbing built on both ends and never joined"),
    Gate("test_chronicle_chain", [sys.executable, os.path.join(HERE, "test_chronicle_chain.py")], 300,
         why="the WHOLE chronicle chain in one pass — every other suite mocks its neighbours"),
    Gate("test_chronicle_calibrate", [sys.executable, os.path.join(HERE, "test_chronicle_calibrate.py")], 120,
         why="the completion-bar reader shipped as a SAFEGUARD and returned a single constant — "
             "0.8395 on every frame it answered across three reels, and 83.9% on a page printing "
             "63%. A reader that returns the same number for different inputs is dead and nothing "
             "could tell. This pins the property it lacked: two reels at different completions must "
             "read differently, it must answer on most frames of a reel that has a bar, and it must "
             "land within about two points of the printed figure. It also records that his ACTUAL "
             "2.4-point defect sits INSIDE the 3-point tolerance, so nobody mistakes this watchdog "
             "for the instrument that catches two wrong rows (that is counter_ledger)"),
    Gate("test_counter_ledger", [sys.executable, os.path.join(HERE, "test_counter_ledger.py")], 120,
         why="the game's own Remaining page is the ONLY reading in this project that can say "
             "\"you do not have that\" — every other reader reads a found page and proposes an "
             "addition, so the count can only go up and a wrong row is invisible to all of it. "
             "It is TIME-ORDERED, and that is the half worth a gate: a denial must bite only when "
             "the page was shot AFTER the sighting, or the safeguard starts eating the finds it "
             "exists to protect. Its first cut compared bare pipeline names against suffixed "
             "roster names and passed cleanly on 86 of them, none of which could ever have "
             "matched — so the folding is pinned too"),
    Gate("test_chronicle_visit_flush", [sys.executable, os.path.join(HERE, "test_chronicle_visit_flush.py")], 120,
         why="a Chronicle visit still OPEN when the session ends must still be journalled — "
             "looking at the Chronicle LAST is the normal way to register finds, and before "
             "v1689 that case wrote no visit row at all, so /api/chronicle_visits stayed []"),
    Gate("test_chronicle_route_guard", [sys.executable, os.path.join(HERE, "test_chronicle_route_guard.py")], 120,
         why="a frame the vision lane read as scene='chronicle' must never be routed into a "
             "stash/vault/tally intake — a kai-vault intake fired on a Chronicle page and came "
             "back ok:false total:0, and the refusal must be NAMED and COUNTED, not silent"),
    Gate("test_inbox_engine", [sys.executable, os.path.join(HERE, "test_inbox_engine.py")], 300,
         why="v1794 — bible.html's inbox fold and chronicle_resolve.py's fold must answer "
             "identically. The board cannot call the Python (it is a file:// page and a phone he "
             "opens mid-game), so the second implementation is forced; a second BEHAVIOUR is not. "
             "This extracts the SHIPPED block out of bible.html, runs it in node, and fails on the "
             "first name where the two disagree — a drifted cutoff folds 'Gul' onto 'Gull' and "
             "writes a find he never made"),
    Gate("test_heart", [sys.executable, os.path.join(HERE, "test_heart.py")], 60,
         why="v2442 — A16, THE HEART. It can only supervise what it KNOWS EXISTS, and it did "
             "not: measured 30 thread targets, 11 supervised, 8 UNWATCHED loops, 2 that could "
             "not be classified — and two of those eight unwatched loops had a real defect the "
             "same day. These cases defend the distinctions that would let the heart report "
             "green over them: DARK (runs, nothing watches) is not UNKNOWN (could not be "
             "classified) and neither is harmless; WATCHED is work owed and NOT a fault, so it "
             "carries no score rather than a zero; and FLOWING must be EARNED — a watcher that "
             "was sabotaged and never refused scores 0.0 and must never be mistaken for a "
             "proven one, which a plain `if score:` would do. Also pins that it DERIVES and "
             "never writes, because a stored picture is a map that drifts from the territory — "
             "BLUEPRINT.md went stale exactly that way and a gate graded the last build."),
    Gate("test_resolver_ratchet",
         [sys.executable, os.path.join(HERE, "test_resolver_ratchet.py")], 60,
         why="A NINTH RESOLVER MAY NOT APPEAR UNNOTICED. A cold cross-family review, with no "
             "knowledge of this tree's history, predicted exactly how one_name decays: someone "
             "adds a consumer and hard-codes another variant while the original resolvers keep "
             "being patched directly. That is not hypothetical — it has happened five times here "
             "(A1's unreachable FLOWING, A3's nine mis-reported cells, a tab resolving on one "
             "side only, a board printing one topic twice) and TWO of those alias maps were "
             "written in a single day by the same hand that was fixing the others. Nothing "
             "detected any of them; each was found by tripping over the defect it caused. So the "
             "census of resolver-shaped declarations is a RATCHET: 8 today, it may only FALL as "
             "they retire into one_name, and a new one fails. Not because a local map is always "
             "wrong, but because it must be a decision in a diff rather than the sixth accident. "
             "It also fails if the baseline goes STALE, so the remaining debt cannot read larger "
             "than it is, and if one_name.py disappears. All four sabotages seen RED, the first "
             "naming the offender by file and symbol."),
    Gate("test_one_name", [sys.executable, os.path.join(HERE, "test_one_name.py")], 60,
         why="THE JOIN THE CONSOLE WAS MISSING FIVE TIMES OVER. Measured: three resolvers disagree "
             "on 6 of 9 inputs — chronicle_template says `sets` where route_totals says `set`, "
             "lane_lock says `uniques` where both others say `unique`. Each is right for ITS OWN "
             "consumers, so flattening them to one string breaks all three, quietly: the call "
             "sites keep compiling and start missing. The same missing piece caused A1's "
             "unreachable FLOWING, A3's 9 MISNAMED cells, v2480's tab vocabulary and v2490's "
             "duplicate board topics — and I wrote two of those local alias maps myself, the same "
             "day, while fixing instances of the problem. So one_name holds ONE concept identity "
             "and every surface asks for the form IT needs. These assert AGREEMENT, not "
             "replacement: each rendering must equal what the live resolver returns today, so "
             "adoption cannot change behaviour and a later divergence goes red instead of "
             "silent. Plus the traps: two unknowns must not compare equal, an unknown word must "
             "be None and never echoed back as if resolved. All four sabotages seen RED."),
    Gate("test_write_witness", [sys.executable, os.path.join(HERE, "test_write_witness.py")], 120,
         why="A7-s remaining half — who ACTUALLY writes a reel store, witnessed at runtime, "
             "because two static walks both measured themselves (a filename-adjacency grep and an "
             "AST walk resolving path constants each returned 0 writers for all four stores, "
             "v2507). ⚠⚠ AND IT NEARLY BECAME THE THIRD ZERO: patching only builtins.open missed "
             "io.open, which this codebase uses everywhere, so a module whose entire job is "
             "counting writers reported ZERO for a store it had just watched being written — "
             "caught by its own demo before shipping. ⚠ It also NAMED A MODULE THAT DOES NOT "
             "EXIST: abspath('<stdin>') lands inside the tree, so an interactive frame passed the "
             "is-it-ours test and a blind [:-3] reported the writer as `<std`. A witness naming a "
             "module that does not exist is worse than one naming nobody — the first is believed. "
             "These pin: an io.open write is seen; the ATOMIC write is seen (these stores are "
             "written to <name>.tmp and MOVED, so watching only `open` would see the tmp file and "
             "never the store — the same shape as the two static failures); a READ is not a write; "
             "every name printed is a module on disk; an UNWATCHED store is None and not zero; the "
             "patches are restored; and it never redirects or blocks a write, because it watches "
             "the one door with no undo. ⚠ It is an INSTRUMENT, not a measurement — the per-store "
             "answer needs a sweep to run while it is on, and that is a measurement nobody has "
             "taken. 5 sabotages, 5 RED."),
    Gate("test_declared_vs_content",
         [sys.executable, os.path.join(HERE, "test_declared_vs_content.py")], 120,
         why="A15 — the route must be DERIVED FROM THE CONTENT, never guessed from a declared "
             "stamp (v1783: a default is not a declaration, and an untouched `stash` stamp "
             "labelled a town, a fight and a Chronicle page as stash panels). ⚠⚠ THE ANSWER ON "
             "HIS TREE IS UNTESTABLE AND THAT IS THE POINT: 40 reel dirs, 40 with an index.json, "
             "and exactly ONE declaring a chronicle focus — carrying ZERO surveyed panels. Zero "
             "disagreements over a sample that cannot disagree measures the SAMPLE, and reported "
             "as AGREES it would say the routing law holds when nobody has shown it. These pin: "
             "one declaring reel with no content is UNTESTABLE; a declaration its own content "
             "contradicts is REPORTED; AGREES needs enough exercised reels, because two agreeing "
             "reels is an anecdote; a real disagreement OUTRANKS the sample floor rather than "
             "hiding behind it; AGREES stays REACHABLE, since a check that can never agree is as "
             "useless as one that always does; THREE empty reels are still UNTESTABLE (the "
             "sample floor masked that guard, so its first sabotage passed — it takes three to "
             "tell the two paths apart); and both unreadable branches SAY unknown rather than "
             "printing an errno. 6 sabotages, 6 RED. ⚠ Recorded in the module: one suspicion was "
             "REFUTED BY THE SOURCE before publication — _vault_lane_owes returning True with no "
             "declared focus looks exactly like v1783 and is the deliberate safe direction, per "
             "its own docstring: I could not tell must never resolve to delete it."),
    Gate("test_template_is_the_mechanism",
         [sys.executable, os.path.join(HERE, "test_template_is_the_mechanism.py")], 120,
         why="A8 — his ask was that the templates be what the routing filters WITH, not a pass "
             "beside it, and TASKS.md gives the testable form: if a template can be removed "
             "without the routing changing, it is not wired in. ⚠⚠ MEASURED, AND IT WAS THE "
             "INVERSE: resolve_tab named ANY tab present in the marker dict, including one with "
             "NO template band at all — handed {'tab_marker': {'hardcore': 0.05}} it answered "
             "`hardcore`, a tab TAB_BANDS has never heard of. geometry_signals only produces "
             "TAB_BANDS keys today, so nothing was wrong on this tree; the router's correctness "
             "rested on an upstream convention it did not check, which breaks the day a band is "
             "renamed or a dict merged. A tab that can be ROUTED WITHOUT A TEMPLATE is the "
             "opposite of A8. These pin: an undeclared tab is never named and the refusal SAYS "
             "it had no template; every banded tab can still be named (a filter that refuses "
             "everything would pass the first test and be useless); removing a template makes "
             "its tab unnameable, which is A8's own test run literally; two REAL tabs lit stay "
             "AMBIGUOUS, because a Sets page tallied as Uniques writes a wrong count into his "
             "grail truth; a contaminated window is still excluded; and every ledger tab has a "
             "template, since one without would route to a kind nothing can produce. ⚠ One "
             "deliberate behaviour change is pinned so it is not mistaken for a defect: a stray "
             "key used to make a real read AMBIGUOUS and refuse; it is now dropped WITH ITS "
             "REASON and the real marker wins. 5 sabotages, 5 RED."),
    Gate("test_sighting_loc_persist",
         [sys.executable, os.path.join(HERE, "test_sighting_loc_persist.py")], 120,
         why="A5 — his words: the fact was in hand at intake, discarded, and the re-derivation "
             "needs footage that no longer exists. _sighting_loc (v2353) ALREADY ANSWERS where a "
             "name was seen and NOTHING KEPT THE ANSWER: measured on the live store, 0 of 14,034 "
             "evidence rows carry a persisted loc, while 39 reels are named and 3 still exist "
             "(92% gone) so only 25% of rows could ever have it re-derived. Computed, rendered, "
             "and thrown away. The stamp runs at merge time, the last moment the reel is reliably "
             "present. These pin: a KNOWN surface is written down; an UNKNOWN one is NEVER stamped "
             "(a stored unknown is indistinguishable from a stored fact once the reel is pruned, "
             "which is the exact confusion this task exists to end); an existing loc is never "
             "overwritten, because the earlier answer was taken closer to the capture; a resolver "
             "failure does not cost the sweep; ONE bad sighting does not skip every sighting "
             "after it (the outer except already saves the sweep — the inner one is about REACH, "
             "and removing it left the first test green); and the MERGE actually calls the "
             "stamper BEFORE the save, since computed-and-not-kept is the defect being fixed. "
             "⚠ It cannot recover the past and does not pretend to: a row whose reel is gone "
             "stays without a loc for ever. 6 sabotages, 6 RED."),
    Gate("test_eye_vs_beat", [sys.executable, os.path.join(HERE, "test_eye_vs_beat.py")], 120,
         why="A13 — the half TASKS.md said was unbuilt: an observation with verdict LOOKED that "
             "CONTRADICTS the console-s own beat. On 2026-09-01 the eye reported his webview BLANK "
             "WHITE while the beat published taskforce shown H=502 top=1050, and that finding "
             "reached no gate — it COULD NOT HAVE, because the console publishes a beat and stores "
             "no history, so an observation and the beat to check it against can never be "
             "reconciled afterwards. observed() captures the beat AT THE MOMENT OF LOOKING now. "
             "⚠⚠ THE CHECK ITSELF WAS WRONG ON THE EXACT CASE IT EXISTS FOR: _shown_panels was "
             "written against the FLAT beats in live_panel_gate.prove() because those were the "
             "examples in front of me, while the LIVE panels_of() returns them NESTED — against "
             "his running console it returned [] and reported AGREES while the beat claimed a "
             "panel shown at h=1309. Both shapes are asserted. These also pin: a row with NO "
             "captured beat is UNKNOWN, never agreement (the 13 existing rows can never be "
             "judged); prose that does not claim blankness is NEEDS-A-READER rather than guessed "
             "at; a silent console captures NOTHING, since an empty beat would make every future "
             "observation look agreed-with; and a panel shown at height 0 is not shown. "
             "6 sabotages, 6 RED."),
    Gate("test_ledger_highwater",
         [sys.executable, os.path.join(HERE, "test_ledger_highwater.py")], 120,
         why="A14 — his ask was \"a counter for chronicles only going up never down\", and a "
             "counter implies a STORED PEAK, not a diff. console_doctor already names what "
             "vanished between the two NEWEST snapshots — which is the half that matters, and it "
             "came out of 2026-08-28 when foundLog went 391->383 overnight with nothing saying a "
             "word — but that finding survives only as long as nobody takes two more snapshots. "
             "⚠ THE MODULE-S OWN FIRST ACT WAS THE BUG: seed() recorded the LATEST snapshot as the "
             "peak, so a ledger that had already dropped would lock the loss in as its own high "
             "water mark. It seeds from the highest value across every readable snapshot now. "
             "These pin: seeding after a drop records the HIGH not today; re-seeding cannot lower "
             "the bar even once the snapshot proving it is ROTATED AWAY (the sabotage for this "
             "passed at first, because the proof was still on disk — the guard only matters when "
             "it is not); a standing loss is reported until reconciled; accept() needs a REASON "
             "and records what it replaced, because a ratchet with no reconcile path goes "
             "permanently red the first time he removes something on purpose; no peak recorded is "
             "UNKNOWN not OK; an ABSENT key is not a key worth zero, which would read as losing "
             "every set piece he owns; and it never restores and never fails a build. Measured on "
             "60 real snapshots: zero drops in the window, so it ships GREEN — insurance, not a "
             "fix for a live bug. 6 sabotages, 6 RED."),
    Gate("test_store_owners", [sys.executable, os.path.join(HERE, "test_store_owners.py")], 120,
         why="A7 — one declared OWNER per reel store, everyone else a declared reader WITH A "
             "REASON, so a second implementation has to be argued in rather than appearing. "
             "⚠ IT DOES NOT PROVE SINGLE-WRITER, and that limit is the point: two static attempts "
             "to measure writers returned ZERO for all four stores — a filename-adjacency grep, "
             "then an AST walk resolving path constants — because paths are bound in helpers and "
             "threaded through arguments. Both zeros measured the instrument, so this checks "
             "COUPLING, which is checkable. ⚠ The registry CAUGHT ITSELF on its first run: it "
             "names every store, so it read as an undeclared toucher of all four. Excluding it is "
             "honest only while it never OPENS one, and that is asserted here rather than promised "
             "— this console has produced the counts-itself defect before. These pin: undeclared "
             "and STALE couplings both fail, the owner must actually mention its store, a reader "
             "needs a real reason, the exclusion stays narrow (widening it would make a hiding "
             "place), and nothing here fails a build. 5 sabotages, 5 RED."),
    Gate("test_printer", [sys.executable, os.path.join(HERE, "test_printer.py")], 120,
         why="THE 3D/4D PRINTER — every reel in at ONE door, down ONE stream, out the other end. "
             "His instruction: \"3d 4d printer connected to the heart of the console and the reels "
             "like we said going in unified and getting processed and routed out clean on the "
             "other end of the stream\". ⚠⚠ THE PRINTER OWNS NO MEASUREMENT and that is the law "
             "these hold: seven modules already answer one question each, every one measured on "
             "his own forty reels, and if this file re-derived any of them a badge and a diagram "
             "would eventually disagree on screen about the same reel. So each station QUOTES its "
             "owner, and the guards MOVE an owner's answer and require the printer's row to move "
             "with it — a token check would have passed on a printer keeping its own copy. ⚠⚠ AND "
             "THE FAR END IS UNDECIDED FOR EVERY REEL, DELIBERATELY: A15 never says which door "
             "decides `clean`, the two candidates disagree on this shelf (12 of 40 by the REEL "
             "door, 0 of 15 asked by the FRAME contract), and conjoining them is the collapse "
             "v2312 attempted and WITHDREW. A printer that picked one would answer his question "
             "with my preference and call it a measurement. Also pinned: a reel missing from an "
             "owner is UNKNOWN not dropped, the shelf-wide EXTRACT state says out loud that it is "
             "shelf-wide rather than inventing forty per-reel measurements, and the printer "
             "contains no delete or write at all — the prune stays OFF and this routes on paper. "
             "4 sabotages, 4 RED."),
    Gate("test_probe_unknown_law",
         [sys.executable, os.path.join(HERE, "test_probe_unknown_law.py")], 90,
         why="EVERY PROBE MUST BE ABLE TO SAY UNKNOWN, AND MUST SAY IT WHEN HANDED NOTHING. ⚠⚠ "
             "This is a PATTERN, not an incident: FOUR times on 2026-09-04 a fix shipped the very "
             "class it was fixing, one edit away — REG-534 (filenames retyped), REG-537 (a "
             "snapshot frozen at import, written ONE LINE BELOW the fix for REG-534), REG-540 (a "
             "store path resolved two ways, inside the module built to catch dead fields), REG-541 "
             "(a wholly unreadable store reporting OK, shipped INSIDE the fix for REG-540's crash, "
             "by the one module whose entire job is refusing to call the unmeasured clean). The "
             "rule was quoted correctly in every one of those commits; what failed was that the "
             "NEW code was never re-asked the question the rule exists to ask. A note cannot fix "
             "that — this law can, because it runs against ALL four probes at once, so the next "
             "one added inherits the question. It asserts BEHAVIOUR (nothing in -> UNKNOWN out) "
             "rather than pinning a roster, carries a REASON check because UNKNOWN with no reason "
             "cannot tell 'the shelf is empty' from 'the shelf could not be read', and holds a "
             "count because a probe silently dropped from the list looks identical to a passing "
             "run. ⚠ BASELINE: each probe must also reach a REAL verdict, or the law would pass on "
             "four functions that answer UNKNOWN to everything. 3 sabotages, 3 RED."),
    Gate("test_dead_field", [sys.executable, os.path.join(HERE, "test_dead_field.py")], 90,
         why="A FIELD RECORDED ON EVERY ROW AND FILLED ON NONE. His instruction, 2026-09-04: "
             "\"connect it to the heart of the console that way we would have caught it\". "
             "`reel_retention._tombstone` recorded every deleted reel's `startedTs` from two keys "
             "NO REEL INDEX HAS EVER CARRIED (0 of 40, measured) and wrote None 410 times out of "
             "410 — on the ONE door with no undo — while nothing anywhere said so. It was found by "
             "READING A LINE, a detector that fires once against a field dead for 410 deletions. "
             "These pin the two ways this detector would lie: reporting a YOUNG store as clean (a "
             "zero over rows that cannot disagree measures the SAMPLE — the mistake A15 clause 1 "
             "exists to avoid, so under the 30-row floor the answer is UNKNOWN), and reporting a "
             "SOMETIMES-null field as dead (`focus` is legitimately null on a reel with no "
             "declared focus, and a row that cries wolf is a row he learns to skip). A field must "
             "be on EVERY row to be judged, and ONE filled row clears the store. It reports and "
             "refuses nothing. 4 sabotages, 4 RED, with a floor-crossing baseline."),
    Gate("test_per_reel_routes", [sys.executable, os.path.join(HERE, "test_per_reel_routes.py")], 90,
         why="A15 clause 3 — *the routes separate PER REEL, BY SCENARIO; each reel takes the path "
             "its own content earns*. ⚠ THE QUESTION IS NOT WHETHER REELS DIFFER — they obviously "
             "do. It is whether the difference is EARNED BY THE CONTENT: a shelf where every route "
             "is decided by age, or by whether the test suite opens the reel, has divergence in it "
             "and none of it is the divergence A15 asks for. Measured on his 40 reels the two "
             "columns are the same 28 and the same 12 — every reel that reached the far end got "
             "there BY POLICY (5 recent, 7 test-fixture), and all 28 content-routed reels sit "
             "under ONE tag at ONE rung. ⚠⚠ AND THAT IS NOT A DEFECT: `zero-pages` means *swept, "
             "and the sweep found nothing to read*, a deliberate hold because the engine reopens "
             "those when the prompt improves — a probe calling it a routing failure would cry wolf "
             "on a shelf behaving exactly as designed. So UNEXERCISED is a THIRD state, distinct "
             "from broken and from working, and these pin it stays distinct: a policy hold is "
             "never counted as content, one content route is a queue not a divergence, an untaught "
             "tag is not rounded into the content bucket, and the policy/content split is QUOTED "
             "from reel_story.POLICY_HOLDS rather than copied. 4 sabotages, 4 RED, with an EARNED "
             "baseline so UNEXERCISED is a measurement and not the only reachable answer."),
    Gate("test_one_funnel", [sys.executable, os.path.join(HERE, "test_one_funnel.py")], 90,
         why="A15 clause 2 — ONE FUNNEL: *they all flow down the same river together*. The clause "
             "holds TWO questions and only one has an answer today: THE LADDER (is there one "
             "stage vocabulary?) is answerable and the answer is yes — 6 rungs, no rung naming "
             "two stages, 0 reels at a stage the ladder does not know; THE PASSAGE (did each reel "
             "actually flow down it, in order?) is PARTIAL — exactly 2 of the 6 rungs leave a "
             "dated waypoint (retro_triage 40/40, vault_swept 15/40) and the other four leave "
             "nothing at all. Answering the easy half and marking the clause done is how a task "
             "gets called shipped while the thing he asked for is unbuilt, so these pin that a "
             "ONE_LADDER verdict may never imply the passage is known. ⚠ AND OCCUPANCY IS NOT A "
             "ROUTE: `reel_story._stage_of` maps a reel's current HOLD TAG to the rung it is stuck "
             "BEFORE, so an empty rung means nobody is STUCK there, never that nobody passed — "
             "the same misreading that opened A10. An unreadable store stays UNKNOWN rather than "
             "counting as zero coverage. 3 sabotages, 3 RED, plus a SPLIT_LADDER baseline."),
    Gate("test_one_start_point", [sys.executable, os.path.join(HERE, "test_one_start_point.py")], 90,
         why="A15 clause 1 — ONE START POINT: *every reel enters at the same place; no lane has "
             "its own front door*. It is asked of the ARTIFACT, not of a source grep, because A7 "
             "tried counting writers twice — a filename-adjacency grep, then an AST walk — and "
             "BOTH returned zero for all four stores while measuring only my own instrument's "
             "reach. His forty reels cannot do that. THE TWO WAYS THIS PROBE LIES, both pinned: "
             "(1) crying wolf — three modules can write a reel's index.json and only ONE is a "
             "front door, so counting the repair door (reel_index, which restores an index a reel "
             "already had and refuses to rewrite one that parses) as a violation reports a defect "
             "on a healthy shelf, where 2 of 40 are repairs; (2) rounding UNKNOWN up to the common "
             "case, which is the default-as-measurement defect. A FIXTURE reel on his LIVE shelf "
             "IS a second door and must reach MULTIPLE_DOORS, or the first law is describing a "
             "function that can never object — and the fixture is caught by its SHAPE (keys on "
             "`reel`, not `sessionId`) as well as by its `synthetic` mark, so one word a future "
             "edit could drop is not the only tell. 4 sabotages, 4 RED."),
    Gate("test_reel_river", [sys.executable, os.path.join(HERE, "test_reel_river.py")], 120,
         why="A10 — the fish down the stream, and the law that keeps it readable: a GAP is two "
             "deciders answering the SAME question differently. Walking the river found 12 reels "
             "reporting RELEASABLE while frame_authority refused every seal on the tree, which "
             "reads exactly like a defect and is not one — reel_retention settled it in v2314: "
             "\"frame_authority is stricter because it answers a DIFFERENT question — may this "
             "FRAME go, protecting the witness frames behind his vault rows — not may this REEL "
             "go.\" The v2312 attempt to collapse them was WITHDRAWN because it would have stopped "
             "the prune firing on every existing reel. A probe that counts that split reports 12 "
             "gaps on a healthy shelf, and a row that cries wolf is a row he learns to skip. These "
             "pin: the split is never a gap; both questions are named ON the row with different "
             "deciders, since a reader cannot tell two questions apart when only one is named; a "
             "reel with no seal is UNASKED and not refused (8 of his 12 are); gaps stay REACHABLE "
             "via an undeclared stage, or the emptiness above proves nothing; an unreadable shelf "
             "is UNKNOWN and not an empty river. 5 sabotages, 5 RED."),
    Gate("test_printer_reach", [sys.executable, os.path.join(HERE, "test_printer_reach.py")], 120,
         why="The printer zone's acceptance test (A4·A7·A8·A9·A15), and the one law it exists to "
             "hold: a zero taken through a filter that rejects every input measures the filter. "
             "The contradiction A4 was born from — a seal certifying full extraction on a reel the "
             "survey says held panels — returns ZERO on this tree, and the cause is that NOT ONE of "
             "the 30 seals satisfies the extraction contract. ⚠ THE OLD NOTE HERE SAID '22 fail on "
             "the same fact, `name`, which only ever appears in a hover tooltip; 8 predate the "
             "contract' AND THAT NUMBER WAS RETRACTED — printer_reach.py:21 carries the "
             "correction, measured untruncated: name, location AND provenance are missing on ALL "
             "30. The original came from a reason string cut at [:70], mid-sentence inside the "
             "first missing fact. This gate note was the LAST COPY of the false figure, still "
             "readable months later next to the module that retracts it — a retraction that lands "
             "in one copy is not a retraction. [[copy-drift]] [[source-window-shortcut]]. So no "
             "reel can "
             "be judged disposable and the contradiction cannot arise at all. Reported as CLEAN "
             "that zero would say the routing is sound; it says nothing of the kind. These pin "
             "UNREACHABLE apart from CLEAN in both directions, keep CLEAN and CONTRADICTION both "
             "REACHABLE so the report can still distinguish anything, and refuse a hardcoded copy "
             "of the contract. Subjects are CONSTRUCTED, because a guard that only fires while his "
             "stores contain an example goes blind exactly when the bug is absent. 5 sabotages, "
             "5 RED."),
    Gate("test_board_story", [sys.executable, os.path.join(HERE, "test_board_story.py")], 120,
         why="The board is a BUILD OUTPUT of TASKS.md, so a decision the build cannot read does "
             "not survive a refresh. On 2026-09-03 he retired A6 and hibernated A18/A20; those "
             "rulings were written into TASKS.md and the live board by hand, and re-running the "
             "deriver the same hour filed all three back into PENDING because _classify knew five "
             "states and none of them was 'he decided not to'. Correct now, silently wrong later. "
             "These pin: his two rulings HAVE a state; a ruling that OPENS the progress line is "
             "read while one MENTIONED mid-line is not (that mis-file retired A1, a live 1/3 item "
             "whose note describes a scope cut — the COUNT was the tell, two rows in a stage where "
             "one thing was retired); no topic can renumber into the next stage (the index was "
             "GLOBAL, so VISUAL under IN PROGRESS landed on YOUR CALL's base); every stage sorts "
             "ABOVE the board's pre-storyline sections (v2490 published the whole storyline "
             "unreachable underneath them); an unknown state does not quietly become pending; and "
             "there is exactly ONE state table (my first cut of story_of carried a second copy, "
             "written the same hour as a fix for two sources disagreeing). 5 sabotages, 5 RED."),
    Gate("test_organ_comparability",
         [sys.executable, os.path.join(HERE, "test_organ_comparability.py")], 180,
         why="A3, the half that would have made the table LIE. console_doctor had no report(), so "
             "a quarter of the organ matrix was UNKNOWN — and simply adding one nearly replaced "
             "that honest unknown with 44 confident ABSENT cells, because the doctor names "
             "CONCERNS ('armed migration', 'art corpus') while the surfaces are CODE OBJECTS "
             "('_bridge_prober'), and ZERO of its 34 names resolve to any of the 44. One word was "
             "about to be printed for three different situations and only one of them was a "
             "measurement. These assert the law that stops it: a cell may say ABSENT only when "
             "that organ's vocabulary actually reaches this list, report() must answer without "
             "touching the window he is looking at (run() posts to /api/board_ownership, which "
             "evaluates JS in his live board), and the summary must state how many organs its "
             "verdict rests on. ⚠ The FIRST version of this suite passed the sabotage — it "
             "iterated the organs the module had already labelled incomparable, so disabling the "
             "label removed them from its own scope. It counts the overlap itself now; 5 "
             "sabotages, 5 RED, each caught by its own test."),
    Gate("test_organ_matrix", [sys.executable, os.path.join(HERE, "test_organ_matrix.py")], 120,
         why="A3 — he was shown a surface x capability table that was mostly holes and said "
             "\"fix those gaps and anywhere else.. make it unified\", every surface getting the "
             "same four organs OR being honestly marked as not having them. The danger is not an "
             "incomplete matrix, it is one that FILLS ITSELF IN: a cell claiming coverage nobody "
             "demonstrated is worse than the blank he was already looking at. These assert that "
             "every COVERED cell is re-derivable from the organ's own output, that an organ which "
             "cannot be asked at all reads UNKNOWN and never ABSENT (console_doctor has no "
             "report(), so accusing it of gaps would be inventing a measurement), and that "
             "MISNAMED stays apart from ABSENT — 9 cells are an organ watching a thing under "
             "another name, which is a join nobody made rather than a hole, and is HOW that table "
             "came to look empty. ⚠ The MISNAMED guard was VACUOUS on its first cut and passed "
             "while every such cell collapsed to ABSENT; it now re-derives the pairs and demands "
             "the label. All four sabotages seen RED."),
    Gate("test_route_totals", [sys.executable, os.path.join(HERE, "test_route_totals.py")], 120,
         why="v2484 — ONE TAB, ONE NUMBER. The heart drew three route sets and each read a "
             "different producer: runeword 105/99/99 and unique 398/403/403. Every number was "
             "right and the panel read as a defect, which is what he said out loud: \"sync and "
             "match them obivously.. no reason to have this gap\". All three now quote "
             "tv/route_totals.py. NO TEST HERE NAMES 99, 135 OR 403 — a gate pinned to a number "
             "is the next label that outlives its referent. They assert the LAWS: the three print "
             "the producer's figure, they all MOVE when it moves (equality today could be a "
             "coincidence — sets looked exactly like this before), the unit word is identical "
             "across surfaces, a divergence names BOTH numbers instead of dropping the loser, an "
             "unreadable producer is UNKNOWN and never zero, every set declaration contributes to "
             "the walk (a bare `pieces:` pattern once returned a confident 81 instead of 135 "
             "because the third declaration quotes its key), and touching bible.html moves every "
             "row cache key — measured, it did not in any of the three."),
    Gate("test_ruling_note_numbers", [sys.executable,
                                      os.path.join(HERE, "test_ruling_note_numbers.py")], 60,
         why="v2484 — A NOTE THAT QUOTES A MEASURED NUMBER MUST STILL BE TELLING THE TRUTH. The "
             "v2192 ruling comment carried the row \"RUNEWORD_TIP 97 what the chronicle KPI "
             "divides by today\". It was never true: that KPI returns Object.keys(_tip).length "
             "UNFILTERED and has always divided by 99, and the 97 is the NUMERATOR — the filtered "
             "`made` count, which is the next line of the same table. The note then used its own "
             "wrong figure to accuse the neighbouring (99/99) comment of being a label that "
             "outlived its referent. The map never drifted; the accusing note carried the stale "
             "number. Nothing on any screen was wrong and his ruling is untouched — the defect "
             "lived in the reasoning record, where nothing reads prose. This reads it, and fails "
             "if anyone but him moves RUNEWORD_CHRONICLE_TOTAL."),
    Gate("test_overlap_ratchet", [sys.executable, os.path.join(HERE, "test_overlap_ratchet.py")],
         60,
         why="v2606 — the overlap ratchet's own arithmetic, and a debt paid one version after it "
             "was named. overlap_ratchet shipped at v2605 with no unit suite and its gate `why` "
             "said so; one version before that I had been bitten by exactly the same shape "
             "(reel_templates, REG-586, classifying all forty reels since v2571 with nothing "
             "testing it). This grades the RATCHET without a browser: a rise fails and NAMES the "
             "width, a FALL fails too so a win is recorded rather than absorbed as slack, an "
             "unmeasurable run is UNKNOWN and never a pass, an absent baseline is UNCONFIGURED "
             "rather than clean, and a malformed count is not read as zero. It also pins that the "
             "3px threshold is not zero — a 1px box kiss is antialiasing, and a gate that cries "
             "wolf is one he learns to skip."),
    Gate("overlap_ratchet", [sys.executable, os.path.join(HERE, "overlap_ratchet.py"), "--check"],
         300,
         why="v2605 — THE CLASS THE RENDER GATE CANNOT SEE. render_check measures CLIPPED, "
             "OFF-SCREEN and COVERED; none of those catches two labels drawn on top of each "
             "other, where both are fully on screen, neither is clipped, and the pixels are a "
             "mess. Measured at a width render_check already renders and calls clean: 375x800 has "
             "24 overlapping text pairs, and even 1440x1000 has 3 — one of them 246x29 px, the "
             "EYES panel's UNKNOWN sentence sitting on the AI READS bar. A cold cross-family look "
             "found it unprompted on the same PNG the gate had just passed. It is a RATCHET "
             "because 24 today would make a pass/fail gate red from birth, and a gate that is red "
             "on arrival gets re-baselined instead of read. A rise fails; a FALL fails too, so a "
             "win is recorded rather than absorbed as slack. ⚠ Its own unit suite is OWED — the "
             "gate exercises the real measurement against real pixels every run, which is stronger "
             "than a fixture, but that is not the same as having one.",
         # v2658 — DECLARED, and narrowly. The module printed "⚪ UNKNOWN — headless chrome would
         # not start" and exited 1, so on a runner with no browser installed this counted as a
         # RED GATE while nine siblings printing ⚪ SKIPPED did not, purely because they exit 77.
         # It now exits 77 for THAT reason only; every other unmeasurable run still fails.
         # ⚠ This declares a venue fact, it does not fix one: `tv-tests.yml` installs no browser,
         # so the gate SKIPS on CI and measures only on his Mac. That is a named coverage gap —
         # publish.yml:97-117 already has the chromium install and cache this workflow needs.
         # ⚠ TWO declared reasons, and they are different facts. The first is a venue with no
         # browser. The second is a venue whose FONT METRICS are not the ones the baseline was
         # measured on — overlap counts follow text advance widths, so comparing macOS numbers to
         # a Linux runner's is not a strict verdict or a lenient one, it is not a verdict at all.
         # Both are declared SKIPS, printed loudly and counted in "did not run"; neither is a tick.
         skip_ok=(r"headless chrome would not start", r"baseline venue mismatch")),
    Gate("test_pixel_witness", [sys.executable, os.path.join(HERE, "test_pixel_witness.py")], 60,
         why="v2601 — the beat is published BY the document, so a window that beats happily while "
             "the compositor presents nothing looks perfect from the inside. Measured on his "
             "machine: blankStrikes 0 and 11,841 DOM elements while the window was blank white. "
             "tv/paint_witness.py reads the window server's own bitmap instead. This suite guards "
             "the calibration, and it exists because the FIRST cut of that bar failed on the only "
             "case it was built for — window CHROME draws 8-9 distinct luminances, so a "
             "`distinct <= 4` conjunct called his blank console PAINTED. It also pins that an "
             "unreadable capture is UNKNOWN and never a clean bill, and that the module can never "
             "reload, delete or kill anything: it is a witness, not a trigger. ⚠ NAMED "
             "test_pixel_witness because test_paint_witness.py was already taken by v2457's "
             "beat-side suite, which I overwrote once and had to restore from git."),
    Gate("test_reel_reaper",
         [sys.executable, os.path.join(HERE, "test_reel_reaper.py")], 60,
         why="THE RECORDER MAY NOT EAT EVIDENCE. `tv_diablo`'s disk-floor branch deleted a WHOLE "
             "REEL with no seal check, no witness check, no tombstone and no log line. Its own "
             "comment promised \"the OLDEST *sealed* reels\" and the word `sealed` appeared ONLY "
             "in that comment; `TV_AUTO_PRUNE` occurs ZERO times in that file, so 'the prune "
             "stays OFF' never reached it — armed, needing no switch. MEASURED: its first victim "
             "would have been reel_s_1784984019250_95276, the oldest reel on the shelf and the "
             "one the vault still cites as witness for \"Chaotic Grand Charm\". ⚠ THE EMERGENCY "
             "IS KEPT — a full disk stops recording entirely, which is worse than losing a reel — "
             "so these grade that it still reaps while refusing to reap EVIDENCE, refuses "
             "outright when the ledger cannot be read (None is never an empty set), sorts by the "
             "reel's own capture clock with un-datable reels LAST, and leaves a record. ⚠ It is "
             "NOT a second writer of reel_tombstones.json; reel_retention stays the one writer."),
    Gate("test_code_staleness",
         [sys.executable, os.path.join(HERE, "test_code_staleness.py")], 60,
         why="THE STALE-IMAGE WATCHDOG. His console booted 2026-09-04 08:43 and served that image "
             "for SIXTEEN HOURS across v2621->v2633. `reel_router_wilson` was declared in PROVES "
             "on disk and its rows appended to the ledger; the running console judged them "
             "against the registry it loaded at boot and published \".self_arming.jsonl has a row "
             "that could not have been banked\" — a definite accusation of forgery against a row "
             "that was banked correctly (read on disk: reel.route OPEN, 56/56). ⚠ The defect is "
             "NOT the staleness — processes go stale. It is that an UNRECOGNISED source and a "
             "FORBIDDEN source produced the same sentence. His ask, three times: *\"a "
             "stale-in-memory registry safeguard watchdog for it too?\"* ⚠⚠ THE SOFTENING IS "
             "NARROW AND THE BASELINE PROVES IT: a FRESH process still refuses an undeclared "
             "source, and a declared source proving a lock outside its declaration is still "
             "refused whatever the reader's age. It reports and never reloads, restarts or execs."),
    Gate("test_reel_router",
         [sys.executable, os.path.join(HERE, "test_reel_router.py")], 90,
         why="A7·ROUTE — one station per reel, decided by the reel's OWN evidence and never by "
             "the keep-reason. MEASURED on his shelf 2026-09-05: 40 reels, 29 never read, the "
             "oldest ten (back to 07-25) all unread, and `vault-owes` matching 0 of 40 because it "
             "is the LAST first-match-wins rule — so the reel reader picked nothing, forever, "
             "while publishing `owed: 0` like a healthy idle lane. Root cause: "
             "`reel_story._stage_of(tag)` derives a reel's STAGE from the RETENTION TAG, so all "
             "40 sat at two of six stages with four permanently empty. ⚠ It arms NOTHING — it "
             "publishes a queue nobody consumes; wiring a paid reader to it is a separate "
             "decision and his. The prune stays OFF."),
    Gate("reel_router_wilson",
         [sys.executable, os.path.join(HERE, "reel_router_wilson.py")], 90,
         why="A7·ROUTE's seven refusals — the ways the keep-reason could creep back into the "
             "read-fate, or an unmeasured reel be dressed as a measured one. RED-proven on the "
             "real module: restoring the coupling (`_station_of` reading `tag`) takes the guard "
             "from independent=YES to NO naming the field. ⚠ Both halves are walked by AST — the "
             "decider AND the evidence builder — because a guard aimed only at the decider leaves "
             "the smuggling path open one function upstream."),
    Gate("verdict_provenance",
         [sys.executable, os.path.join(HERE, "verdict_provenance.py")], 90,
         why="Can each stored verdict say WHAT produced it? His catch, 2026-09-05, after the "
             "router's EMPTY turned out to rest on `retro_triage.json` rows carrying no "
             "classifier version: *\"make sure to look out for other coding things like this "
             "that might be gapped just like this was.\"* Swept 2026-09-11: 44 stores, ANSWERS 6, PARTIAL 4, SILENT 16, REFERENCE 17, UNKNOWN 1. "
             "A SILENT verdict cannot be invalidated when its "
             "producer improves, so a stale NO outlives every later pass looking exactly like a "
             "fresh one — and here a stale NO means footage is never read again. ⚠ It REPORTS and "
             "never repairs: back-filling a producer onto 437 existing rows would invent "
             "provenance for verdicts nobody can now attribute."),
    Gate("disk_report_wilson",
         [sys.executable, os.path.join(HERE, "disk_report_wilson.py")], 120,
         why="154 — can the disk row REFUSE to claim space it did not free? `prunedMb` was "
             "HARDCODED to 0 at the only call site, so 'the prune has never freed a byte' was a "
             "fact about the CALLER and that framing was retracted. The call site passes None now "
             "— his live store shows the cut-over exactly, 8,270 rows carrying 0 against 280 "
             "carrying None — and the remainder was that nothing had ever passed a REAL figure. "
             "His ruling: 'fix it to the hardening and wilsons and to the heart so it proves "
             "itself before its unlocked.' ⚠⚠ IT NEVER PRUNES AND CANNOT: every attempt is a "
             "state in which the row must decline to name a freed figure, prune_once is never "
             "called, TV_AUTO_PRUNE is never touched, and it writes only to a throwaway temp path "
             "so it cannot inject fixtures into the series he makes storage decisions from. "
             "RED-proven against the ORIGINAL defect — restoring 'unmeasured becomes 0' takes it "
             "from 24/24 refused to 0/24 with all three claims LEAKING. ⚠ It guards the REPORT, "
             "not the deleter: prune.arm already guards whether the prune may ACT, this guards "
             "whether the row may CLAIM, and they fail differently."),
    Gate("test_hover_calibration",
         [sys.executable, os.path.join(HERE, "test_hover_calibration.py")], 60,
         why="v2621 — the root of a chain six stations long. His question was why no reel can reach "
             "the pruning zone; traced: `out` decides nothing for 40 reels <- the FRAME door has "
             "never once said YES <- no seal carries `extracted` (22 of 30 are `[]`, 8 predate the "
             "field, ZERO satisfy the contract) <- the contract needs `name` <- `name` only ever "
             "appears in a hover tooltip <- MINI AUTO is the only thing that films tooltips <- and "
             "its tooltip->cell offset was never calibrated. The calibration data was not missing, "
             "it was DISCARDED: hover_mode's step callback receives the planned target, which IS "
             "the true cell because mini auto chose it, and dropped it. This suite guards the "
             "recorder and the arithmetic. Its most important case is that the calibrator can "
             "SUCCEED — every other case proves a refusal, and a calibrator that can only refuse "
             "is indistinguishable from a broken one. It also caught a real flaw in its own "
             "module: the outlier rule refused only when MORE THAN HALF the readings disagreed, "
             "so three readings 800px from the other five still yielded an offset."),
    Gate("test_reel_templates", [sys.executable, os.path.join(HERE, "test_reel_templates.py")], 60,
         why="v2604 — reel_templates classifies all forty reels on his shelf and shipped at v2571 "
             "with NO SUITE AT ALL: the inverse of REG-079, which catches a suite no gate runs. "
             "It guards the reason a reel cannot be classified, because that reason named the "
             "wrong component: every unknown reel said 'the segmenter returned no activity', and "
             "measured on his shelf all 14 unknowns have ZERO deep journal rows while carrying "
             "22-2,385 frames on disk and 7-40 SHALLOW rows. They were read, never read DEEPLY, "
             "and the segmenter was working perfectly with nothing handed to it."),
    Gate("test_self_arming", [sys.executable, os.path.join(HERE, "test_self_arming.py")], 60,
         why="v2438 — KONYO RULED THE PRUNE MUST NOT BE ARMED BY HAND. \"a lock until it "
             "automatically unlocks with a que for wilson score. arithmetic as you see.\" This "
             "suite guards the one thing that would make that a lie: the denominator counts "
             "SABOTAGES ATTEMPTED, never agreements. An invariant that always agrees may be "
             "perfect or INERT and those are indistinguishable, so a lock fed by an agreement "
             "rate opens BECAUSE nobody tested it. It also pins that UNPROVEN (n=0) never "
             "renders as a score, that Wilson and confluence must BOTH clear, that his order "
             "is enforced so the deleter cannot arm before the lanes feeding it, that an "
             "unreadable proof queue fails CLOSED, and that may() never grows an override "
             "parameter — which would quietly restore the hand-arming this replaces."),
    Gate("test_heart_surface", [sys.executable, os.path.join(HERE, "test_heart_surface.py")], 60,
         why="♥ THE HEART AS A SURFACE — the route and the shell it borrows. test_heart covers the "
         "derivation; this covers what actually broke on the way in. A panel reusing .fleet-xref "
         "inherits a TWO-COLUMN GRID along with the design: #ver-xref hit that and wrote a warning, "
         "and v2443 added #heart-ov three lines under the warning and hit it again — the diagram "
         "squeezed to its 640px min-width, the valves stranded in a right column, a scrollbar under "
         "everything. Pins the LAW (any borrower must override) rather than the two panels that "
         "exist today. Also holds the render seam, without which the blood animation can never be "
         "seen run on a console with 0 flowing vessels, and the route's failure direction."),
    Gate("test_shell_tracks", [sys.executable, os.path.join(HERE, "test_shell_tracks.py")], 60,
         why="v2453 — THE TRACK COUNT MUST MATCH THE AREA ROW COUNT. Konyo photographed a black "
             "panel twice and found the cause himself: \"maybe it because i wasnt full screen\". "
             "`body.theatre-open .shell` carried FIVE track sizes with !important, written for the "
             "desktop layout; at <=900px the rail stops being a column and stacks in, so the "
             "template has SIX rows. Every size landed one row short of its area and the computed "
             "track list came out `72px 0px 0px 498px 38px 16px` — matching NO authored rule, "
             "which is what made it look impossible and produced TWO wrong diagnoses before the "
             "cascade was measured properly. The !important is also why a higher-specificity "
             "counter-rule did nothing. Pins the LAW (tracks must equal area rows, in every media "
             "block) rather than the numbers, and pins that the narrow rule keeps both its "
             "!important and a pixel floor — without either, the stage can collapse again."),
    Gate("test_item_classifier", [sys.executable, os.path.join(HERE, "test_item_classifier.py")], 90,
         why="A21a — ONE CLASSIFIER, AND NOTHING MAY CLAIM A NAME IT DOES NOT RECOGNISE. Konyo "
             "found Rotting Fissure — a sunder charm, a UNIQUE — sitting on the SETS chronicle. "
             "FOURTH shipment of one class: v664 walked 62 mod-chronicle uniques into "
             "d2r_setPieces, v1692 routed a find into the physical vault, v1913 put Blood Crescent "
             "on the Sets bar. v1913 diagnosed it correctly and its own comment PROMISED the cure "
             "— \"`else -> set` IS GONE, a name neither side recognises is claimed by NEITHER "
             "bar\" — and the code kept the catch-all for two hundred versions while the comment "
             "said otherwise. This pins BOTH halves: the sets bucket may not claim a name the "
             "classifier has no opinion about, and a comment claiming the catch-all is gone must "
             "be true. It also pins that the sunder charms resolve through the roster the feature "
             "already maintains rather than a fifth hand-kept exceptions list, that the roster "
             "still holds six, and that Latent/Renewed prefixes are stripped — the codex carries "
             "only the 'Latent …' form, so without stripping it recognises one form in three."),
    Gate("test_lane_health", [sys.executable, os.path.join(HERE, "test_lane_health.py")], 60,
         why="v2272 — HE HAD TO ASK WHY NOTHING HAD BEEN EXTRACTED FOR DAYS. Measured that day: the "
             "chronicle lane had swept 36 sessions and the vault lane had sealed 8, its newest seal "
             "136.7h old, and frame_authority reads ONLY the vault seal — so 36 already-read reels "
             "were held as 'not sealed' and nothing was prunable. Nothing surfaced it: the "
             "auto-sweep watchdog speaks only when its message CHANGES, which is exactly wrong for "
             "a lane that has said the same thing for five days. This pins the three questions a "
             "lane must answer about itself — freshness, reach, and DIVERGENCE from the lane it "
             "should agree with, which neither lane can see alone — and pins that an unreadable or "
             "timestamp-less store is UNKNOWN rather than healthy. All five laws sabotage-proven "
             "RED."),
    Gate("test_handoff_queue", [sys.executable, os.path.join(HERE, "test_handoff_queue.py")], 90,
         why="v2289 — THE CONSOLE-TO-BOARD HANDOFF, DRIVEN END TO END RATHER THAN GREPPED. v2274 "
             "\"fixed\" register by preferring a _BOARD_WIN handle and pinned it with a SOURCE "
             "guard; that guard stayed green for four versions while the join did not exist, "
             "because board_window() is spawned as a separate OS process and the handle lives in "
             "the child. A pattern was present and a path was not. So this extracts the REAL "
             "shipped drain block out of bible.html, runs it in node against a fake store, and "
             "asserts what ENDED UP in the inbox. It pins the lines that may not move: nothing "
             "reaches his ledger (v1523 — the console never writes the grail), a name he DISMISSED "
             "never comes back, and the drain stamp is the record's SHAPE with counts rather than "
             "a flag whose presence can be forged — which is precisely the v2205 loaded gun that "
             "would have dropped 273 of his 280 names. Six laws sabotage-proven RED, and one of "
             "them caught a test of mine that looked like it checked drain-once and actually only "
             "checked de-duplication."),
    Gate("test_chronicle_crossref", [sys.executable, os.path.join(HERE, "test_chronicle_crossref.py")], 60,
         why="v2278 — THE COUNT HE ACTS ON MUST BE THE COUNT OF WHAT WOULD CHANGE. His console read "
             "\"347 find(s) read from your reels\" under a claim that they were absent from his "
             "chronicle. He asked: \"did it cross reference what i currently already own? im pretty "
             "sure i alread have those items\". MEASURED on his live console 2026-08-29: 347 "
             "proposed, 347 already in his foundLog, every one already dated, newlyDated 0 — "
             "pressing the green button would have changed nothing, and it had been saying 347 "
             "every minute for days. This pins the three states apart — some new, none new, and "
             "NOT MEASURED (which may never render as a number, because 347 after no ledger read is "
             "the same lie as 0) — and pins that two byte forms of one apostrophe are one item, "
             "since bible.html carries Atma\u2019s Scarab, Cat\u2019s Eye and Death\u2019s Web "
             "both ways. It also pins the opposite failure: a canon that over-normalises would hide "
             "real finds, so Bloodrise and Bloodfist must stay two. All five laws sabotage-proven "
             "RED, including the negative control that the cross-reference can still say NEW."),
    Gate("crest_loudness", [sys.executable, os.path.join(HERE, "crest_loudness.py")], 120,
         why="v2294 — THE INSTALL CREST IS NEVER THE LOUDEST THING ON THE BOARD. Measured: every "
             "element above the fold ranked by the share of its own pixels that are saturated, and "
             "`.bs-glyph` came FIRST at 92.5%, ahead of the help button at 75.7%. A solid 20x20 "
             "block of the install hue was the loudest thing on the page — and which hue is picked "
             "by a hash of the install id, so nobody chose it: six of the sixteen crests land in "
             "the palette's red/orange ALERT band, meaning 38% of installs wear an identity chip "
             "the eye reads as an alarm. His hashed to Crimson, hue 0. A cross-family read named "
             "it unprompted as 'also the loudest element' and noted it is the character name, not "
             "the hunt. The obvious fix was REFUTED before it was written: damping the hue to a "
             "22% tint puts the closest pair of crests (Hollow vs Iron) at dE 2.4 — the "
             "just-noticeable threshold, i.e. two machines that look the same colour, which v1466 "
             "calls worse than showing no crest at all. So the hue is untouched at full strength "
             "and only its FOOTPRINT shrank. ⚠ v2430 — THIS GATE NEEDS CHROME, AND FOR ITS "
             "WHOLE LIFE IT REPORTED THAT ABSENCE AS A BUILD FAILURE. The line here used to read "
             "'exits 2 (UNKNOWN) without it, which run_gates reports as a loud SKIP'. It does not: "
             "SKIP_EXIT is 77 and every other non-zero code is a FAIL, so CI run 33594870851 went "
             "red on this one gate with the other twenty-nine green — camouflage for any real "
             "failure landing beside it. The checker now exits 77 and the reason is DECLARED below, "
             "which is the v1925 mechanism finally being used by something: an undeclared skip is "
             "still counted as a failure, so this stays visible and stays honest. A skip is not a "
             "pass. [[unknown-stays-unknown]] [[label-outlived-referent]]",
         skip_ok=(r"no Chrome",)),
    Gate("test_auto_scope", [sys.executable, os.path.join(HERE, "test_auto_scope.py")], 60,
         why="v2293 — EVERY AUTOMATIC LANE DECLARES WHAT IT WOULD DO WITHOUT HIM. The cold-read "
             "question \"if this app were about to do something on your behalf, could you tell what "
             "it would do and what it would leave alone?\" came back CANNOT TELL. Nine loops run "
             "with no prompt, one of them a DELETION lane, and nothing on the console named their "
             "scope. Each now declares does/touches/forbids/never/when/brakes, and the guard checks "
             "the promise against the lane's OWN BODY rather than trusting the prose. Four laws "
             "sabotage-proven RED: a body that contradicts its forbids, a started loop with no "
             "declaration, a declaration for a loop nothing starts, and a roster reader that cannot "
             "reach the roster. That last one is not hypothetical — this guard's first reader "
             "sliced a fixed 1,600 chars and the roster's own comments had outgrown it, so the "
             "FIRST lane fell off the top and was reported as a ghost. What the check does NOT "
             "cover is stated in its own output: the wider call graph is measured and labelled "
             "unverified, never folded into the verdict, because a promise nobody measured is not "
             "a promise. [[source-reading-guard]] [[unknown-stays-unknown]]"),
    Gate("test_cf_handoff", [sys.executable, os.path.join(HERE, "test_cf_handoff.py")], 60,
         why="v2454 — five inverted-role tasks. CF-8 UNKNOWN carries first-seen/last-attempt; "
             "CF-10 four states are four words; CF-12 SLOW checks reach slowRows not the cheap "
             "pass; B-83 equipment is names_loc not a frame class; #135 stays unfingerprinted. "
             "Each guard has a named sabotage."),
    Gate("test_health_engine", [sys.executable, os.path.join(HERE, "test_health_engine.py")], 60,
         why="v2277 — ONE HEALTH ENGINE, RED/GREEN, REPORTING ONLY. Konyo: \"not sure we need a "
             "live watchdog that fixes things might be wrong for the console and make a bug worse.. "
             "but maybe a system that does red/green flag us... should be a system working one unit "
             "system engine locked in\". Four things had to be asked BY HAND this session before "
             "anyone knew they were wrong: a lane that had said nothing for 137h, a retired "
             "migration whose flag left a destructive undo armed on every board since v2203, a "
             "console asking ITSELF for the board's store, and my own unbounded glob holding a core "
             "at 99.7% for 28 hours. Each was silent BY CONSTRUCTION. This pins that the engine "
             "REPORTS and never repairs (it may not import subprocess or open a file for writing), "
             "that a check which raises still appears in the report, and above all that UNKNOWN "
             "never renders as ok — \"the board is not open so its store cannot be asked\" is not "
             "\"fine\". The armed-migration law is proven RED against a reconstruction of the "
             "actual pre-v2275 bytes, so it is not a check that has only ever seen green. AND IT "
             "IS NOT A FIFTH SURFACE: the checks live here, the SURFACE is the existing eagle eye "
             "(console_doctor), because this machine already had four things implementing "
             "report-never-repair and a fifth would be copy-drift with three of them unread."),
    Gate("test_main_character", [sys.executable, os.path.join(HERE, "test_main_character.py")], 60,
         why="v2320 — WHAT IS ON HIS CHARACTER. LOCKED_LANES protects the equipment panel only while that panel is on screen; a helm he is WEARING could still be proposed for a mule from a reel that only saw the stash. This ledger learns his gear from repeated sightings and Wilson-scores it, so a lock is EARNED — a wrong lock silently removes an item from everything the vault is for. Furniture stays locked by law at zero sightings."),
    Gate("test_tooltip_find", [sys.executable, os.path.join(HERE, "test_tooltip_find.py")], 90,
         why="v2321 — FINDING THE TOOLTIP IN ONE FRAME, which is the blocker the cursor offset, "
             "slot identity and MINI(AUTOMATIC) all sat behind. Every obvious method was tried "
             "and MEASURED dead first: differencing returned the whole screen on 38 of 39 "
             "consecutive pairs because the D2R world never stops animating; darkness fails "
             "because 48.7% of his frame is near-black; there is no border to find because the "
             "tooltip is semi-transparent and the stash grid shows through it. Text DENSITY is "
             "what is actually true of it — and density ALONE finds the HUD, so the area floor "
             "is the load-bearing half: his real tooltip is 33.4% of the frame, the impostor "
             "2.8%. These cases pin the growth, the refusals, and that a located-but-unjudged "
             "tooltip counts in NEITHER side of the Wilson ledger."),
    Gate("test_retro_gate", [sys.executable, os.path.join(HERE, "test_retro_gate.py")], 60,
         why="v2320 — THE RETRO ACCURACY GATE. A focused MINI bypasses the witness rule because he AIMED it, which removes the lane's only accuracy mechanism; this replaces it on the FIRST look by grading every read on WHAT it named, WHERE it placed it and HOW it read it. It also resolves a garble that shares a frame with a clean name to that name, and separates stat lines from item names — both proven on his own 2026-08-30 frames."),
    Gate("test_slot_identity", [sys.executable, os.path.join(HERE, "test_slot_identity.py")], 60,
         why="v2271 — SLOT IDENTITY. Konyo: \"it needs to be read within the tooltip and where and "
             "what cell box its located so it can have a slot identity for each item\". This pins "
             "the arithmetic (a cell is derivable from pixels, so the LOCKED intake is never "
             "touched), the refusals (a point outside the panel, a zero-size panel, an unknown "
             "container — each refuses rather than guessing, because a WRONG slot files an item "
             "somewhere he will not look), and the two lanes he separated by hand: shadow keeps "
             "witnesses + watchdog + eagle eye and this module defers to that gate, while HIS own "
             "route is barred by a RECHECK instead — two reads of the SAME frame that must agree "
             "on the name AND the cell, and hold when they do not. All six of those laws were "
             "sabotage-proven RED before this gate was written."),
    Gate("lane-census", [sys.executable, os.path.join(HERE, "lane_census.py"), "--prove"], 60,
         why="v2402 — THE HEART CAN ONLY SUPERVISE WHAT IT KNOWS EXISTS, and the instrument that "
             "answers that question was wrong twice on the day it was written. It reported five "
             "functions named `_loop` as one-shot workers; every one carries `while True`. So this "
             "gate does not run the census — it runs the census's OWN SABOTAGE, which plants a "
             "known loop, a known task, a gated loop and an absent name and requires all four "
             "sorted, plus the three real functions it previously got wrong. A census nobody has "
             "seen get it wrong is a census nobody should quote, and the broken one was already "
             "quoted into gh #198. What the census currently reports: 28 thread targets, 11 "
             "supervised, and SEVEN persistent loops running unwatched.",
         skip_ok=()),
    Gate("task-freshness", [sys.executable, os.path.join(HERE, "tasks_freshness.py")], 60,
         skip_ok=(),
         why="v2435 — A LIST THAT NAMES FINISHED WORK AS READY COSTS SOMEONE THE WORK TWICE. Grok "
             "Bot filed this as GB-B-3/GB-B-4 on 2026-09-01 and repeated it on NINETEEN consecutive "
             "watch ticks; it was right every time. Four of the five rows under READY TO APPLY had "
             "shipped in v2400 and sat there for thirty-four versions: 143 (`fv.onclick` occurs 0 "
             "times), 159 (the doc now says KEEP 3 / THROW 4 and v2400's message says 'Closes "
             "GB-B-1'), 153 (hover_wilson has 5 refs in this very file) and 164. Keeping the list "
             "current by remembering is exactly what failed, so each row now carries a FINGERPRINT "
             "— the string whose PRESENCE means the work is undone — and this refuses when one "
             "disappears. Seen RED on his real file before the rows were closed. A row with no "
             "fingerprint reports UNKNOWN on every run and is never rounded up to clean.",
         ),
    Gate("human-eyes", [sys.executable, os.path.join(HERE, "human_eyes_gate.py"), "--gate"], 120,
         skip_ok=(r"no human-eyes ledger",),
         why="v2404 — THE VISUAL HARNESS NOW REACHES SOMETHING. Konyo: 'i want this part of the "
             "workflow.. what about the visual harness with grok bot where is that?' It was built "
             "— ask_view.py, human_eyes_ledger.py, the skill, briefs HE-1..HE-5 as issues — and it "
             "reached NOTHING. Its ledger held the first sighting of gh #200 ('the whole webview is "
             "white... the beat still reports taskforce shown top=1050 in a 660px window'), correct "
             "and acted on by nobody, in an untracked .jsonl. An observation that reaches nothing "
             "is a diagnosis nobody made. This gate runs the checker's own SABOTAGE — empty ledger "
             "and a brief owed past 24h must go RED, an answered round trip must go GREEN, and an "
             "unreadable ledger must be UNKNOWN rather than a pass. ⚠ It asserts only what the "
             "RECORD proves; the full ask — a LOOKED observation contradicting the live console "
             "raising a blocker — needs a running console and belongs beside the render gate. "
             "Filed, not faked. ⚠ v2428 — AND FOR ITS WHOLE LIFE IT RAN ONLY THAT SABOTAGE. Registered as --prove, it proved the CHECKER on temp fixtures and never once opened the real ledger, so the record this harness exists to make reachable stayed unread by the thing built to read it. --gate runs both: sabotage first (an untrustworthy checker must not be believed), then HIS ledger, with an absent ledger reported as UNKNOWN rather than folded into a verdict — it is gitignored, so absent is the normal state of every venue but his Mac, and the old code called that RED.",
         ),
    Gate("live-panel", [sys.executable, os.path.join(HERE, "live_panel_gate.py"), "--gate"], 120,
         skip_ok=(r"no console is listening", r"console never answered"),
         why="v2406 — THE LIVE BEAT FINALLY REFUSES SOMETHING, AND THIS GATE IS THE JOIN THAT WAS "
             "MISSING FOR A WHOLE SHIP. uiBeat.panels has reported ON-SCREEN / BELOW-FOLD / "
             "OFF-SIDE / OFF-VIEW since v2404 — because `shown` was TRUE for a card sitting at "
             "y=1050 in a 628px window — and NOTHING READ IT. tv/live_panel_gate.py was written to "
             "read it and then was not registered here, which is the same unjoined end it exists "
             "to catch, committed while fixing that class of defect. "
             "⚠ render_check.py CANNOT do this job and must not be assumed to: at his real "
             "1120x628 it reported taskforce y=224 h=30 ON-SCREEN while the live beat reported "
             "y=1050 h=502 BELOW-FOLD. Both correct — the gate renders a seeded fixture and the "
             "console renders his real state, and at h=30 vs h=502 they are not even measuring the "
             "same element. A fixture that lays out differently from the app cannot gate the "
             "app's layout. "
             "This runs the checker's own SABOTAGE: a collapsed panel and one clipped sideways "
             "must go RED, a page that merely scrolls must stay GREEN (his window is 660px by "
             "design), a panel that is simply not on the visible tab must stay GREEN — that last "
             "case is pinned because the first cut REFUSED HIS LIVE CONSOLE over #hd-tallybar "
             "being display:none off its own view, and a gate that refuses a working console is "
             "how a gate gets switched off.",
         ),
    Gate("blueprint-agrees", [sys.executable, os.path.join(HERE, "lane_census.py"),
                              "--vs-blueprint"], 60,
         why="v2403 — TWO MAPS OF ONE FACT, AND WHERE THEY DISAGREE IS THE FINDING. BLUEPRINT.md "
             "is generated from the code and tv/lane_census.py counts the same thing by a "
             "different route; until today nothing had ever put them side by side. The first "
             "comparison found the blueprint listing 14 lanes against the census's 18 — it matched "
             "on the NAME (`def *loop*`) rather than on the behaviour, so _bridge_prober, "
             "_engine_driver, _mini_watchdog and _orphan_watch were on no map and in no roster. "
             "A map built from a naming convention describes the names, not the building. "
             "⚠ THIS IS A CONSISTENCY CHECK, NOT CORROBORATION — both sides read control_app.py, "
             "so they share a source and can be wrong together. Real corroboration needs the "
             "RUNTIME roster from a live console as the second witness; that is not built yet and "
             "this gate must not be mistaken for it.",
         skip_ok=()),
    Gate("hover-wilson", [sys.executable, "-c", _HOVER_WILSON_VERDICT,
                          os.path.join(HERE, "hover_wilson.py")], 120,
         why="v2400 — MINI(AUTOMATIC) SCORES ITS OWN FOUR CLAIMS, and this gate is the LEAKS half "
             "of that report. The lane the vault cost us ran every 45 seconds at a 100% agreement "
             "rate and had swept nothing, so the denominator here is SABOTAGE ATTEMPTS, not runs: "
             "a claim only counts as caught when a deliberately wrong input was rejected. LEAKS — "
             "a wrong point that still resolved to the cell we aimed at, a recheck that agreed "
             "with a read it should have refused — is the only state that goes red. UNPROVEN and "
             "UNKNOWN print with their notes and PASS, because zero attempts is a measurement "
             "nobody has taken (today: `anchor`, waiting on a calibrated tooltip->cell offset) and "
             "a gate that reddens on its own newest checks is switched off inside a week. Proven "
             "RED against a slot_identity whose cell_of collapses adjacent columns: 12 of the 24 "
             "coordinate sabotages went uncaught and the gate exited 1, while `anchor` stayed "
             "UNPROVEN and green throughout. [[unknown-stays-unknown]] [[heart-first]]"),
    Gate("test_vault_lane", [sys.executable, os.path.join(HERE, "test_vault_lane.py")], 420,
         why="v1795 — the vault lane decides what he KEEPS and what it dares suggest he "
             "bins, and it has never run on real footage (0 of 17 reels declare an "
             "ownership surface, REG-185). These scenarios drive the REAL sweep over his "
             "REAL reels with only the reader injected, and pin the asymmetry he asked "
             "about: repetition makes an item more OWNED and must never make it closer to "
             "being thrown away. Also pins the ONE KEY — at most one lane is ever "
             "unlocked, and a frame claiming both a stash panel and a chronicle tab "
             "unlocks nothing."),
    Gate("chronicle-doctor", [sys.executable, os.path.join(HERE, "chronicle_doctor.py")], 120,
         why="the arc is wired on THIS machine — lanes, footage, board build"),
    Gate("test_stash_eye_aspect", [sys.executable, os.path.join(HERE, "test_stash_eye_aspect.py")], 120,
         why="the stash crops must stay locked on Konyo's Mac AND reach 16:9 for the cousin"),
    Gate("test_console_fleet", [sys.executable, os.path.join(HERE, "test_console_fleet.py")], 180,
         why="the fleet tracker must SHOW the machines that were here — the 'console:' prefix also "
             "matched every 'consolelog:' key, and the offline window listed the OLDEST 400 events, "
             "so the cousin who ran it yesterday was invisible"),
    Gate("test_g5_grok_eyes", [sys.executable, os.path.join(HERE, "test_g5_grok_eyes.py")], 300,
         why="the vision-eye contract"),
    Gate("test_roundtrip_sim", [sys.executable, os.path.join(HERE, "test_roundtrip_sim.py")], 900,
         why="a full simulated session round trip"),
    Gate("robot_smoke", [sys.executable, os.path.join(HERE, "robot_smoke.py")], 120,
         why="the TV_ROBOT=1 frozen-boot lane must not rot — a 20s stub boot, no model call. "
             "⚠ It lived as a hand-listed CI step while the gate set knew nothing about it, so "
             "consolidating CI onto run_gates.py would have DROPPED it silently. It is not a "
             "tv/test_*.py, so TestNoOrphanSuite could never have caught the omission: that guard "
             "watches for suites missing from this list, and cannot see a runnable check that was "
             "never named as one"),
    Gate("test_kai_missed_recoverable",
         [sys.executable, os.path.join(HERE, "test_kai_missed_recoverable.py")], 120,
         why="a session close that reports 'N frames held text no eye read' must NAME those "
             "frames, not just count them. It journalled 20 verbose rows and nothing else, so on "
             "his 108-frame session the headline was honest while 88 frames existed only inside a "
             "number and no sweep could ever find them"),
    Gate("test_chronicle_still_threshold",
         [sys.executable, os.path.join(HERE, "test_chronicle_still_threshold.py")], 120,
         why="the chronicle sweep's still threshold must stay BELOW what jpeg_sig can produce. At "
             "the shared 0.22 it was above the ceiling of the measurement (largest real diff: "
             "0.133), so no frame pair ever broke a run, a whole 217-frame session became ONE run, "
             "and 9 of his 10 reels read zero pages. Synthetic on purpose so it runs on CI, where "
             "his footage cannot exist"),
    Gate("test_chronicle_seal", [sys.executable, os.path.join(HERE, "test_chronicle_seal.py")], 120,
         why="the retro sweep must never seal a reel it did not read. chronicle_swept.json hides "
             "every reel it names from all future sweeps, and the loop used to record even a "
             "no-index reel that read NOTHING — footage lost until a full `force` re-run. The "
             "tests EXECUTE the shipped loop out of control_app.py rather than copying it, so a "
             "widened predicate turns them red instead of quietly passing"),
    Gate("test_import_bound_paths",
         [sys.executable, os.path.join(HERE, "test_import_bound_paths.py")], 120,
         why="v1925 — the registry of which env redirects a fixture can still make AFTER import. "
             "_CHRON_EVIDENCE_PATH binds from TV_CHRON_EVIDENCE at import, so a test that set it "
             "inside a function body called the real save and truncated tv/chron_evidence.json "
             "from 525,187 bytes to 748 — 767 paid page reads gone. conftest.py reports that "
             "damage after the fact; this names the trap before a fixture falls into it"),
    Gate("test_sets_base_index",
         [sys.executable, os.path.join(HERE, "test_sets_base_index.py")], 60,
         why="base -> set piece exists TWICE — the source JSON and the copy embedded in "
             "bible.html — and a copy nothing compares is a copy that drifts [[copy-drift]]. "
             "ITEM_CODEX carries a base for only 14 of the 135 set pieces, so the mapping could "
             "not be derived and had to be recorded; this is the comparison"),
    Gate("test_button_matrix", [sys.executable, os.path.join(HERE, "test_button_matrix.py")], 300,
         # v1711 — needs_app was TRUE, so this gate was skipped before it could even try, on
         # every run where Konyo did not happen to have his console open. It now BOOTS ITS OWN
         # control_app on a free ephemeral port (never :17772, his live one) and stops it after,
         # so it runs unattended and in CI. It still reports SKIP — never a pass — if that private
         # instance cannot come up.
         needs_app=False,
         why="every app button, against the LIVE control API"),

    # ── v2907 — the fleet's three lanes, registered by me, not by the agents that wrote them ──
    Gate("test_frozen_frames",
         [sys.executable, os.path.join(HERE, "test_frozen_frames.py")], 120,
         needs_app=False,
         why="a FROZEN feed and a BLANK screen are two findings and neither may be reported as the "
             "other. Measured on his real capture shelf 2026-09-10: 68 of 178 captures were "
             "byte-identical repeats, three long runs, two confirmed blank by opening the image "
             "\u2014 while every HTTP check in the same minute read `GET / 200, 1,744,954 bytes`. "
             "A repeated hash is the POINTER; the verdict needs a look. #34.",
         skip_ok=()),
    Gate("test_provenance",
         [sys.executable, os.path.join(HERE, "test_provenance.py")], 120,
         needs_app=False,
         why="a store must be able to name what produced it, and must never invent a name it does "
             "not have. Census measured on this tree 2026-09-10: 44 stores \u2014 6 ANSWER, 4 "
             "PARTIAL, 16 SILENT, 17 REFERENCE, 1 UNKNOWN. `37 of 43` was arithmetically true and "
             "three classes wide, which is why the fix had to separate them. #69.",
         skip_ok=()),
    Gate("test_the_pixel_verdict_reaches_the_wire",
         [sys.executable, os.path.join(HERE, "test_the_pixel_verdict_reaches_the_wire.py")], 120,
         needs_app=False,
         why="the one instrument that can tell a DEAD window from a COVERED one must answer where "
             "someone can read it. Measured on his console 2026-09-10: up 1h27m, rescue loop "
             "FLOWING at its 10s period, so the witness had run ~87 times \u2014 and "
             "`/api/status` published SIXTEEN uiBeat keys with the pixel verdict not among them. "
             "The same day Grok Bot read those sixteen fields and filed FROZEN about a window the "
             "witness called OCCLUDED (Terminal 100% on top). A covered window and a dead one "
             "produce byte-identical captures. Three answers, never two: None is NOT ASKED, "
             "OCCLUDED is clean, BLANK is the fault.",
         skip_ok=()),
    Gate("test_a_negative_gap_is_not_covers_all",
         [sys.executable, os.path.join(HERE, "test_a_negative_gap_is_not_covers_all.py")], 120,
         needs_app=False,
         why="more stamps than the census counted means the census is STALE, never that it covers "
             "everything. Measured on his live console 2026-09-10 via /api/heart: proved 285, "
             "provenAtCount 289, so _iGap is -4, `_iGap > 0` is false, and the panel asserted "
             "\u2018covers all 289 gate(s)\u2019 three lines under a header saying 285 proven. The "
             "two figures age independently \u2014 `proved` moves on a FULL census, "
             "`provenAtCount` on every TARGETED --prove \u2014 so any session proving a handful of "
             "gates reproduces it. Behavioural: the real expression is run under node against all "
             "four states.",
         skip_ok=()),
    Gate("test_a_weld_never_repeats_a_word",
         [sys.executable, os.path.join(HERE, "test_a_weld_never_repeats_a_word.py")], 120,
         needs_app=False,
         why="a weld joins a figure to its noun and must never show a word twice. `_weld` wraps the "
             "first two and last two words of a clause; for a THREE-word clause those windows "
             "overlap at index 1 and the middle word was emitted twice. Latent \u2014 the live "
             "clauses are 2, 6 and 8 words, so every render was green. The law is arithmetic "
             "(guard >= head + tail - 1) read as NUMBERS out of the source, plus the real helper "
             "run under node over lengths 1..14.",
         skip_ok=()),
    Gate("test_shelf_driver_supervision",
         [sys.executable, os.path.join(HERE, "test_shelf_driver_supervision.py")], 120,
         needs_app=False,
         why="a lane that sits DARK must say so, and nothing in this console could say it. "
             "`vaultAutoread` sat at `reads: 0, lastTs: null` for weeks with work owed and no "
             "heartbeat, and neither heart2 (can the GATES go red) nor lane_liveness (is the "
             "thread ticking) joins `there is work owed` to `this lane did a unit of work`. "
             "One predicate, not a second opinion. #59.",
         skip_ok=()),
    # ⚠ MIND THE SEPARATING COMMA ON EVERY Gate(...) INSERT — dropping it has produced a
    # SyntaxError twice in this file. [[gate-insert-missing-comma]]
    Gate("test_a_tab_opener_is_bounded",
         [sys.executable, os.path.join(HERE, "test_a_tab_opener_is_bounded.py")], 120,
         needs_app=False,
         why="#185 - the PUT /json/new that opens a CDP tab had NO timeout in roster_sync.py "
             "while the create_connection on the very NEXT line was bounded. urllib blocks "
             "FOREVER by default and nothing calls socket.setdefaulttimeout, so a Chrome that "
             "accepts the TCP connection and never answers wedges the caller with no bound and "
             "no message. Third file in the same class in one day (render_check v3436, then "
             "this), and it was found by a SWEEP rather than by a failure - which is the whole "
             "argument for closing a class instead of a site.",
         skip_ok=()),
    Gate("test_an_echo_is_not_a_corroboration",
         [sys.executable, os.path.join(HERE, "test_an_echo_is_not_a_corroboration.py")], 120,
         needs_app=False,
         why="#182 - agreement() decided AGREE/DISAGREE/SINGLE and NEVER READ WHO LOOKED. "
             "Measured on 940 rows: of 55 versions asked twice, 41 (75%) were SAME-FAMILY pairs, "
             "all xai - and console_doctor mapped AGREE to OK, so one witness asked twice read "
             "as corroboration. Two derivations of one source agreeing is one number wearing two "
             "names. ECHO is its own state on purpose: making a same-family pair report DISAGREE "
             "would turn 8 historical versions red at once and the row would be silenced within "
             "a week, which costs more than the defect.",
         skip_ok=()),
    # ⚠ MIND THE SEPARATING COMMA — a dropped one has produced a SyntaxError here twice.
    Gate("test_an_echo_reaches_his_screen_as_a_measurement",
         [sys.executable, os.path.join(HERE, "test_an_echo_reaches_his_screen_as_a_measurement.py")], 120,
         needs_app=False,
         why="#182 second half - agreement() gained an ECHO state (a SAME-FAMILY pair, one witness "
             "asked twice) and console_doctor let it fall through to UNKNOWN, which is wrong in "
             "kind: ECHO is MEASURED and UNKNOWN means nobody could ask. DRIVEN, not read: the "
             "eagle buckets on four literal strings, so a FIFTH state is counted by nothing and "
             "folds into ALL CLEAR while control_ui still draws the row under WAITING ON YOU - "
             "uncounted and shown as his at once, the same shape as the UNMEASURED row that cost "
             "a day of deploys. So ECHO maps to MISSING, and the 8 affected versions are +0.9pp "
             "on a row already MISSING on 856 of 877.",
         skip_ok=()),
    Gate("test_a_shadow_log_nobody_read_is_not_agreement",
         [sys.executable, os.path.join(HERE, "test_a_shadow_log_nobody_read_is_not_agreement.py")], 120,
         needs_app=False,
         why="#188 - g5_grok_eyes wrote 6,082 Claude-vs-Grok rows and NOTHING ever read them: the "
             "four keys occur at exactly four lines tree-wide and all four are writes. Of 1,596 "
             "rows where both lanes answered, 67.6% disagreed on names - while that lane is "
             "mode=primary. The reducer publishes BOTH lanes with their reach and never prefers "
             "one; one-sided rows are counted separately, and a rate over nothing is UNKNOWN, "
             "never 0.0.",
         skip_ok=()),
    Gate("test_an_unread_test_is_not_a_clean_verdict",
         [sys.executable, os.path.join(HERE, "test_an_unread_test_is_not_a_clean_verdict.py")], 90,
         needs_app=False,
         why="#196 - ci_sim printed 'N test(s) could not be read for platform facts - UNCHECKED, "
             "not clear' and then EVERY return ignored it: exit 1 on failures, exit 3 on platform "
             "facts, else exit 0 'no KNOWN host dependency'. So a suite whose unreadable tests all "
             "passed produced a clean verdict about work the tool never examined - a skip counted "
             "as a pass, in the one tool whose header forbids over-claiming. Reachable by "
             "construction: a method added on the class at RUNTIME is unreadable, because "
             "_source_index only holds FunctionDef nodes appearing in the class body. Now folded "
             "into the tool's existing UNKNOWN answer (exit 3) with the two reasons NAMED apart. "
             "The law is DRIVEN, not read: the first cut walked the AST for an if-unread "
             "containing a Return, and reverting the guard left that Return present but "
             "UNREACHABLE, so it stayed green through the exact defect. A presence-law is not a "
             "reachability-law.",
         skip_ok=()),
    Gate("test_a_reach_difference_is_not_an_unsteady_eye",
         [sys.executable, os.path.join(HERE, "test_a_reach_difference_is_not_an_unsteady_eye.py")],
         90,
         needs_app=False,
         why="#168 - agreement() said '2 looks at ONE payload DISAGREE ... a finding about the "
             "INSTRUMENT' about pairs whose payloads differed 2.9x (v3413: 8,622 vs 25,074) and "
             "9.9x (v3451: 7,744 vs 76,810). An eye shown a TENTH of the change answering "
             "differently from one shown all of it is not an unsteady eye - it is the cap doing "
             "what the cap does, and blaming the instrument is the conclusion that stops anyone "
             "looking at the cap. The data was in the rows the whole time: `sentCode` and `chars` "
             "appeared NOWHERE in agreement()'s body, checked by AST over every string constant. "
             "MEASURED when this shipped: SEVEN versions moved out of DISAGREE (19 -> 12). This "
             "law pins BOTH halves - a 2x+ split reads INCOMPARABLE and NAMES both sizes, while a "
             "1.1x pair still reads DISAGREE, because an exemption that swallowed every "
             "disagreement would delete the unsteady-eye finding it exists to sharpen.",
         skip_ok=()),
    Gate("test_a_handoff_lane_must_not_pile_up",
         [sys.executable, os.path.join(HERE, "test_a_handoff_lane_must_not_pile_up.py")], 90,
         needs_app=False,
         why="#199 - HIS ORDER 2026-09-23 after #230 reached FORTY-ONE unread: 'make sure they both "
             "get done inbetween and DONT stack up like it just did 41 times'. The drainers existed "
             "and only ran when someone remembered, which is not a mechanism - NOTHING WATCHED them, "
             "so nothing noticed. MEASURED: #230's watermark sat 16.1h stale while its 41 unread "
             "ticks carried live answers to open items - freeze=AFTER_REOPEN_PAINT-58756 (#172, "
             "still firing at v3456), the Fleet PARTIAL state #157 needs, and ASK digests for "
             "#37/#45/#113. This law pins the watcher: a stale lane is NAMED and goes MISSING, an "
             "unreadable watermark is UNKNOWN and never an empty queue, each lane is judged by ITS "
             "OWN mechanism (#231 through the ledger, #230 through handoff) so a healthy lane is "
             "never accused, and the watcher NEVER drains or marks anything read.",
         skip_ok=()),
    Gate("test_a_look_on_github_is_not_a_look_in_the_ledger",
         [sys.executable, os.path.join(HERE, "test_a_look_on_github_is_not_a_look_in_the_ledger.py")],
         120,
         needs_app=False,
         why="#180 - the #231 seat posts a cross-family look to GitHub and NOTHING carried it to "
             "the ledger, so the gate that asks `was this version looked at` could not see looks "
             "that had already happened. MEASURED 2026-09-23 and it cost a whole review: the seat "
             "reviewed v3449 at 181,141 chars and named BOTH defects later rediscovered by a fresh "
             "Grok call and shipped as v3452 - the verdict arm that still says GATES RED when red "
             "is false, and the no-spec patience callers with their 18-of-20 denominator. It sat "
             "unread. This law pins the drain: a look becomes ONE row, a look naming no version is "
             "refused AND counted, and an unreachable GitHub is UNKNOWN rather than an empty lane.",
         skip_ok=()),
    Gate("test_a_cut_off_gate_set_is_not_a_verdict",
         [sys.executable, os.path.join(HERE, "test_a_cut_off_gate_set_is_not_a_verdict.py")], 120,
         needs_app=False,
         why="#184 - GitHub reports a TIMED-OUT job as `cancelled`, not `failure`, so when the "
             "gate set crosses its 25-minute ceiling it does not go red, IT GOES SILENT, and a "
             "missing verdict reads like a scheduling hiccup. #123 quoted a stale gate count for "
             "weeks for exactly this reason. Measured: the gate set is 95% of the job wall clock "
             "and has already crossed once (25.3m, cancelled).",
         skip_ok=()),
    # ⚠ MIND THE SEPARATING COMMA — a dropped one has produced a SyntaxError here twice, and it
    # takes the WHOLE gate set down because every gate subprocess imports this file.
    Gate("test_a_parallel_proof_is_the_same_proof",
         [sys.executable, os.path.join(HERE, "test_a_parallel_proof_is_the_same_proof.py")], 180,
         needs_app=False,
         why="#189 - heart2 proved every red-proof SERIALLY (a doubly nested for-loop, zero "
             "concurrency primitives in the file), which measured 24 of a 38m42s push and 26 of a "
             "41m25s one - 60%+ of EVERY push, growing with every law added. Parallelising it is "
             "only safe if the verdicts are IDENTICAL: a faster prove that flips one verdict is "
             "not a speedup, it is a broken gate. This law pins that, because the danger is "
             "measured - test_control is 19.5s idle and 565.9s under concurrent load, and parallel "
             "proving deliberately manufactures that load.",
         skip_ok=()),
    Gate("test_a_host_dependency_is_not_always_an_attribute",
         [sys.executable, os.path.join(HERE, "test_a_host_dependency_is_not_always_an_attribute.py")], 120,
         needs_app=False,
         why="#123/#185 - ci_sim answers 'would this pass on a runner?' and its HOST_STUBS held "
             "exactly THREE entries, all the SAME KIND: patch a module attribute. Neither "
             "CI-vs-Mac disagreement found this week is one - tv/bin/ocr_mac is a MACOS BINARY ON "
             "DISK (green on his Mac in 5.3s, red on CI at 25.4s), and 'this interpreter takes "
             "fork_exec where Linux takes posix_spawn' is a PLATFORM fact that cannot be patched "
             "at all. The simulator reported 'no KNOWN host dependency' for both. That gap once "
             "cost a full day of deploys.",
         skip_ok=()),
    Gate("test_every_push_line_carries_its_elapsed_time",
         [sys.executable, os.path.join(HERE, "test_every_push_line_carries_its_elapsed_time.py")], 60,
         needs_app=False,
         why="#193 - every pre-push status line was untimed, so a gate's duration could only be "
             "BOUNDED from outside by polling ps; the v3447-v3451 prover, the one run that most "
             "needed a number, could only be reported as '<=20 min'. Two starvation refusals on "
             "2026-09-24 left logs that could not say how long the stages before them took. The "
             "same law pins the stopwatch glyph: `\\u23f1` in a bash double-quoted string printed "
             "six literal characters in the one message he reads when a push fails.",
         skip_ok=()),
    Gate("test_the_seed_check_leaves_a_receipt",
         [sys.executable, os.path.join(HERE, "test_the_seed_check_leaves_a_receipt.py")], 60,
         needs_app=False,
         why="#159 - bake_seed.py printed 'no drift' to stdout and left nothing behind, so nothing on "
             "his console could say WHEN the seed was last checked against his board. It now "
             "writes a dated receipt on every run; the doctor row reads its age (never re-runs "
             "the baker, which opens his WebKit store). Driven on temp receipts only.",
         skip_ok=()),
    Gate("test_the_gate_set_shards_cleanly",
         [sys.executable, os.path.join(HERE, "test_the_gate_set_shards_cleanly.py")], 60,
         needs_app=False,
         why="#184 - the gate set ran 25m18s against its 25-minute CI ceiling and was CANCELLED, so "
             "a shipped version got no verdict. CI now runs run_gates.py --shard K/N as a matrix; "
             "this pins that the slices are disjoint, complete, order-independent, cost-balanced, "
             "never empty (run() reads [] as EVERY gate), and that a bad slice is refused.",
         skip_ok=()),
    Gate("test_no_test_writes_his_eagle_ledgers",
         [sys.executable, os.path.join(HERE, "test_no_test_writes_his_eagle_ledgers.py")], 60,
         needs_app=False,
         why="v3470 - seven doctor suites drove console_doctor / unknown_age with fake checks and "
             "never redirected TV_UNKNOWN_AGE / TV_EAGLE_SLOW, so every run appended 'exploder' "
             "(813) and 'exploding check' (803) to his LIVE ledgers, and _LIVE_STATE never named "
             "either file, so CI filed it as 'also touched'. One helper (fixture_ledgers) called "
             "at import by all seven; both ledgers joined the watcher; driven, AST-read law.",
         skip_ok=()),
    Gate("test_every_push_checks_every_proof_anchor",
         [sys.executable, os.path.join(HERE, "test_every_push_checks_every_proof_anchor.py")], 60,
         needs_app=False,
         why="REG-1163 - four red-proofs went INVALID in one day because an ordinary edit changed "
             "a line another gate's proof pins, and the hook re-proves only laws whose TEST file "
             "changed. The census case knew all four and never ran at push time. This pins that "
             "the hook runs it on EVERY push, at top level, not inside the changed-tests block.",
         skip_ok=()),
    Gate("test_two_eyes_are_compared",
         [sys.executable, os.path.join(HERE, "test_two_eyes_are_compared.py")], 60,
         needs_app=False,
         why="#188 - v3450 built the shadow reducer and its divergence_row() and NOTHING called "
             "it: the G5 lane ran PRIMARY on a 6,082-row two-family comparison no surface read. "
             "MEASURED 2026-09-24: the newest both-answered row is ten days old, and 1,078/1,596 "
             "READS disagree (67.5%) while 66/165 distinct FRAMES do (40.0%). The row reads it, "
             "states both denominators, and is red only on staleness or a majority by BOTH.",
         skip_ok=()),
    Gate("test_the_characters_tab_is_manual_and_separate",
         [sys.executable, os.path.join(HERE, "test_the_characters_tab_is_manual_and_separate.py")], 90,
         needs_app=False,
         why="#245 - 👤 Characters is its own top tab, the MANUAL side (his: 'a separate section for the character MAIN "
             "character and builds ... just like the mules have their designated areas', 'Its own top tab'): drives the "
             "SHIPPED room with the Character Builder, CB_DB, switchTab, LSR, the fork sets and the Backup exporter in node "
             "on a fake clock. The tab sits right before the Vault and app context re-shows it; the cards are exactly the "
             "builds in d2r_charBuilds, MAIN first then newest; Set as MAIN writes only d2r_cbMain; Delete is two steps (5 s "
             "confirm) and Undo restores the store byte-identical for 20 s, deleting MAIN clears d2r_cbMain; every OTHER "
             "localStorage key (mules, vault, owned, chronicle, ladder copies) is byte-identical across every action and no "
             "vault / mule function is called; Open calls openCharBuilder(id) and the builder's dropdown leads with "
             "'★ MAIN'; an unreadable store is UNKNOWN and refuses writes; d2r_cbMain forks per account and rides Backup. "
             "#245 review: the Undo bar's countdown never replaces the Undo button (focus + slow clicks survive), a "
             "keyboard delete keeps focus (armed -> Undo -> the restored card), one double-click is not a delete, Undo "
             "is byte-identical in ANY order, nothing is deleted under the open planner and the planner says when its "
             "build is gone (UNKNOWN when unreadable), and app context's row starts where a scroll reaches. "
             "15 cases, 25 red-proofs",
         skip_ok=()),
    Gate("test_the_character_builder_is_their_builder",
         [sys.executable, os.path.join(HERE, "test_the_character_builder_is_their_builder.py")], 90,
         needs_app=False,
         why="#174 v-B2 - the Character Builder (a tool of its own; the mules stay mules) is the d2planner's builder "
             "over the game's own tables: drives the SHIPPED builder block, the generated CB_DB block (from his "
             "install, tv/char_builder_db.py), CHARS, LSR, the fork sets and the Backup exporter in node. The helm's "
             "rail is their Helmets / Circlets / Pelts (Druid) / Primal Helms (Barbarian) and the list is the ENTIRE "
             "database for the slot; gloves have no Runewords tab; a runeword is offered only on bases that hold its "
             "runes (Enigma on Mage Plate, never Quilted Armor); a roll box is clamped to its range - typed = EXACT "
             "under the game's own key, out of range = refused and unsaved, blank = the range (Crown of Ages "
             "Defense 349-399 untouched, 399 typed, hand-checked); d2r_charBuilds is the brief's shape, forked per "
             "account and carried by Backup & Share; Esc closes the picker, then the builder; a whole session reads "
             "no vault store and calls no mule; the tooltip's colours are spec 8 and a requirement is red only when "
             "KNOWN failed; Crafted is the game's cube, witnessed by the board's CRAFTS; the block's names are "
             "tv/item_tables.json's; STATS is the stats engine's rows with their source (a capped one with its raw) "
             "and, with no engine, every row UNKNOWN and no number drawn. FIX ROUND: a Sorceress's parent list holds no "
             "other class's items; sockets are what the item may hold (Crown of Ages' own Socketed 1-2 IS the stepper, "
             "another unique 0..1 by Larzuk); the inventory's All Items is charms; the stash tree's Jewels > Colossal "
             "Jewels and Melee / Ranged Weapons fold; the shipped block's per-level [L, lo, key, hi, shift] and random "
             "class [C, ...]; the generator's --check where the install is; the doctor row 'builder item data'. "
             "16 cases, 22 red-proofs",
         skip_ok=()),
    Gate("test_the_character_builder_fits_at_every_width",
         [sys.executable, os.path.join(HERE, "test_the_character_builder_fits_at_every_width.py")], 150,
         needs_app=False,
         why="#174 v-B2 - the Character Builder measured in a REAL browser (its own headless Chrome on a free port) at "
             "7 widths in 5 states - as it opens, with Crown of Ages worn and Annihilus in the inventory, the helm's "
             "picker open, the helm in Edit, the stash open: no word or control cut or outside its panel, nothing "
             "sideways, no header title under its control, the modal on screen and NEVER over the glowing slot it "
             "serves (it covered the helm at 1024 and 901 until the placement took the roomier side), 2000 = their "
             "literal 322 | 716 | 300 columns with the doll filling the centre, and under 900 the character first. "
             "The entry and the equip are REAL input (Tools tab, the card, the slot, the search box, typed keys, a "
             "roll, a charm dropped and dragged). No browser binary = declared skip (77). FIX ROUND: at 375 and 2000 the "
             "picker's list reaches its last row under a real wheel (the stacked pane was unbounded at 375), and an active "
             "gold button under the pointer keeps its dark label. v-B3: the Edit tab of a base with its picked mods (a rare "
             "Diadem with four, a magic Grand Charm with two) and its ADD MOD list open fit at 2000 / 1280 / 375. "
             "v-B3 FIX ROUND: the open list lies inside the Edit tab's visible box and takes its room (it ran 137px "
             "below the modal at 1280x800 and stopped at 158px on a phone); ADD MOD by REAL keys - focus stays in the "
             "search box, ArrowDown makes the second option the painted, aria-activedescendant one, Enter adds exactly "
             "it. v-B4: the doll and its 10x4 inventory are ONE carved-stone panel, the game's grid flush under the doll "
             "(<= 12px, no word between; the caption and status line under the panel), 10 x 4 equal square cells edge to "
             "edge, radius 0, never wider than the doll, >= 26px from 1280 up, every item inside its cells - in every "
             "plain / worn state and with three charms (Annihilus, a Grand Charm, Gheed's Fortune) placed through the "
             "cell's own picker at 2000 / 1280 / 1120 / 900 / 375, which move STATS. 18 cases, 23 red-proofs",
         skip_ok=(r"no Chrome/Chromium on this machine",)),
    Gate("test_the_mule_window_is_the_planner_shell",
         [sys.executable, os.path.join(HERE, "test_the_mule_window_is_the_planner_shell.py")], 60,
         needs_app=False,
         why="#174 v-A - the mule window is rebuilt as the d2planner builder's shell: three columns "
             "322|716|300, their ten measured doll slots, the 10x4 inventory under the doll, the "
             "10x10 stash as a locker's centre view, every stat UNKNOWN with a reason. And Esc: "
             "#vault-detail matched none of the console's overlay selectors, so Esc closed the SHELL "
             "and left the window up; it is now a role=dialog. Drives the SHIPPED openMuleCard in node. "
             "Also pins the #174 fit fixes structurally: the four prose panels are min-height floors, every size "
             "in the window is a --fs-mp-* token = root token x --kf floored at --fs-micro, a header title and "
             "its control own grid columns, and a resize re-lays the window only when its layout signature "
             "moves (a phone keyboard is a height-only resize). #174 v-B2: the columns are their LITERAL 322 | 716 | "
             "300 again (v-B's 1.25x doll unit is gone - his 'literally the same'), the five stash tabs are buttons "
             "that switch the grid, and the unit also answers the height (a height-only resize at 1280 re-lays the "
             "window exactly when it moves the unit). 25 cases, 17 red-proofs",
         skip_ok=()),
    Gate("test_the_mule_window_fits_at_every_width",
         [sys.executable, os.path.join(HERE, "test_the_mule_window_fits_at_every_width.py")], 120,
         needs_app=False,
         why="#174 - the mule window's words were cut ON SCREEN while the node law, reading innerHTML, stayed "
             "green: every length was N*--u and the type was fixed px, so between 900 and 1250 wide the "
             "MERCENARY note lost its (v-C) line (his 1120), STRENGTHS AND WEAKNESSES read TRENGTHS AND "
             "WEAKNESSE and the Stash button covered EQUIPMENT; at 375 the gold box and the mule tabs scrolled "
             "sideways; a phone keyboard (a height-only resize) rebuilt the window under the Stats search box. "
             "Renders bible.html in its OWN headless Chrome on a free port at 7 widths: no word cut or outside "
             "its panel, nothing sideways, no header title under its control, type = token x min(1,k) floored "
             "at --fs-micro, 2000 = their measured rects, the caret survives a keyboard and a background "
             "re-render. Seen RED on the pre-fix page (7 of 9 cases). No browser binary = declared skip (77), "
             "never a pass. #174 v-B: every width measured AGAIN with three items worn through the picker and the "
             "picker open (new words in new boxes). #174 v-B2: 2000 = their rects literally (DOLL_K = 1); 1280x695 (his "
             "console's board) joins the widths and the part he packs from (header, mule bar, doll + inventory, "
             "stash panel) plus STATS end inside the window (the Grok seat's 'bottoms sliced'); a worn item's hover "
             "card never covers the mule bar ('ES IN THIS LOCKER'); and a REAL-INPUT drag pass: a ring dropped on a "
             "cell locks there with a green footprint in the air and survives a reload (2000 stash, 1280x695 "
             "inventory), a 2x4 past the edge is red and refused with nothing written, the keyboard carries an item, "
             "a right-click unlocks it, a drop on the Gems tab moves it there. #174 v-B2 integration: the hover card "
             "is the builder's in-game box (#cb-tip) - the worn weapon, the worn ring and a stash tile, hovered by a real "
             "mouse at 2000 and 1280x695, each open #cb-tip naming the item, leave #arttip shut, keep off the mule bar "
             "and under their panel's header. FIX ROUND at 375, real input: a drag held at the top edge scrolls the window to "
             "another mule's tab and the drop moves the item there; ] carries a keyboard item to the next mule; a real tap "
             "beside a placed ring's 10px lock (coarse pointer) unlocks it. 19 cases, 21 red-proofs",
         skip_ok=(r"no Chrome/Chromium on this machine",)),
    Gate("test_the_mule_window_equips_and_says_its_source",
         [sys.executable, os.path.join(HERE, "test_the_mule_window_equips_and_says_its_source.py")], 90,
         needs_app=False,
         why="#174 v-B - the mule window equips from its own locker and every stat says its source. Drives the "
             "SHIPPED vault span, ITEM_CODEX / ITEM_TIP / tipOf, the routed store and the Backup exporter in node: "
             "d2r_muleEquip's shape and a manual placement always winning over an analyzer route; a ring never "
             "offered for the helm and every item left out counted with its reason (no slot on record = never "
             "offered); the text parser (exact / a range never averaged / UNKNOWN for what needs a character / "
             "mixed as >= exact + range); the store forked per world and riding Backup & Share; Esc closes the "
             "picker first; a worn copy leaves the stash on both surfaces; one hover card on an equipped slot; "
             "NOTES saved on Enter/blur with its draft surviving a re-render. The slot table is the game's: "
             "checked against tv/item_tables.json kinds in CI, the subtypes against the install where it is "
             "(UNMEASURED, never passed, elsewhere). 16 cases, 18 red-proofs",
         skip_ok=()),
    Gate("test_the_character_sheet_sums_the_game_data",
         [sys.executable, os.path.join(HERE, "test_the_character_sheet_sums_the_game_data.py")], 90,
         needs_app=False,
         why="#174 v-B2 - his order: 'add all the information and data based on the items buffs ... calculate the total "
             "sum of it all correctly. based on HELL and its data like the resistances starting with -100%'. The stats "
             "engine (window.D2R_CHAR_ENGINE.sheet) sums from the GAME'S property data, generated from his install into "
             "bible.html's CHAR_PROPS block by tv/char_props.py (uniqueitems / setitems / sets / runes / gems, properties "
             "code -> stat, itemstatcost per-level shifts, difficultylevels ResistPenalty 0/-40/-100). Drives the SHIPPED "
             "engine in node with answers worked by hand from the tables: Hell + quests Crown 30 typed + Vipermagi + "
             "Mara's + Oculus = 20..45 (cap 75), untouched 10..45, a typed roll narrows, penalties 0/-40/-100, quests off "
             "30 lower, PDR 45..50 capped at 50 with the raw beside it, the 75 cap and a max-res cap of 90, defense "
             "349..399 / 470..485 from the base table, a per-level shift, class skills to one class, an unmapped prop and "
             "an unnamed item UNKNOWN naming the item. And the block's watchman: char_props --check on a fake install "
             "(fresh 0 / moved 1 / hand-edited 1 / no install 77 / corrupt 77), the doctor row 'character sheet data' "
             "OK / MISSING / UNKNOWN and registered, and the block's uniques and set items against tv/item_tables.json "
             "(a second generator). The real install's --check runs where the install is, UNMEASURED elsewhere. FIX "
             "ROUND: Enhanced MAXIMUM Damage is its own row (Hellslayer ED 100, EMD 240 at 80); a class-locked base on "
             "another class counts nothing (Herald of Zakarum on a Sorceress); a set bonus with no switch blanks only what "
             "it feeds; elemental absorb caps at 40; a magic charm blanks only its affix pool's stats (FCR stays 60). "
             "35 cases, 20 red-proofs",
         skip_ok=()),
    Gate("test_the_mule_picker_offers_the_whole_database",
         [sys.executable, os.path.join(HERE, "test_the_mule_picker_offers_the_whole_database.py")], 90,
         needs_app=False,
         why="#174 v-B4 - ONE PICKER, TWO HOSTS. His ALT PC (v3514): every body-gear slot of every mule said 'Nothing in "
             "<mule> fits' - that PC's store routes nothing (no muleAssign, no muleEquip, owned []), and the mule window's "
             "picker listed only the locker's own rows. A slot now opens the Character Builder's picker in a MULE host. "
             "Drives the SHIPPED vault span + builder block + CB_DB block + mule tooltip script together in node: on the "
             "ALT's empty store the Body Armor slot opens on Select with every spawnable body armor base in CB_DB and "
             "every unique / set on one (no ring), never 'Nothing in X fits'; with locker items the In this locker tab is "
             "in front and is word for word the old list and footer (the same as the picker drawn without the builder's "
             "block); Enigma -> Base -> Mage Plate writes the mule {source manual, id, base xtp, q, sockets 3, its runes}, "
             "Edit edits it in place, the doll wears it LIVE and it frees no cell, the mule's hover is the builder's "
             "tooltip over that entry; d2r_charBuilds and d2r_cbSel byte-identical; Esc closes Filters, then the picker, "
             "then the window; a builder pick never writes d2r_muleEquip. v-B4 REVIEW: I / II swapped with a hand's picker "
             "open re-aims it (Edit showed set II and wrote set I - Windforce silently replaced, a pick onto set II landed "
             "in set I); a pick hides the hovered row's tooltip in the mule host as in the builder; a locker (no class) "
             "lists second weapons for the left hand. 8 cases, 13 red-proofs",
         skip_ok=()),
    Gate("test_the_runeword_base_tab_is_theirs",
         [sys.executable, os.path.join(HERE, "test_the_runeword_base_tab_is_theirs.py")], 90,
         needs_app=False,
         why="#174 v-B4 - their Select | Base | Edit, measured on their planner with a real mouse. Picking a runeword opens "
             "the Base tab (it no longer goes on its first base): every base its itypes allow that holds its runes at the "
             "item level, another class's bases left out, grouped Elite / Exceptional / Normal <Category>, categories A-Z, "
             "rows by qlvl high to low - Breath of the Dying's 48 rows, Grief 30, Spirit 24 (swords only on the weapon "
             "slot), Heart of the Oak 12 exactly theirs, Insight and Call to Arms as far as their list drew; an Amazon sees "
             "her spears and a Sorceress does not; item level 20 holds no six-socket base and says so; hover = the "
             "runeword on that base through d2Tip; click = worn there, Edit opens, Edit's Base goes back; the search match "
             "underlined; the weapon rail is itemtypes.txt's Equiv tree from CB_DB ty[code][4] (their parents, children "
             "and folds). v-B4 REVIEW: a non-Barbarian's left-hand tree keeps the flat rail's 'Second Weapons (Barbarian)' "
             "row, listing exactly the block's one-handed classless weapon bases, never drawn on her Base tab; a "
             "Barbarian's carries the weapon types. 8 cases, 13 red-proofs",
         skip_ok=()),
    Gate("test_the_rails_fold_is_a_chevron_not_a_dot",
         [sys.executable, os.path.join(HERE, "test_the_rails_fold_is_a_chevron_not_a_dot.py")], 120,
         needs_app=False,
         why="#174 v-B4 review - the type tree's folds were the SMALL-triangle glyphs: 4x4 px of ink at 2000 and 3x4 at 375 by this law's own instrument on the pre-fix page (the review's PIL read 4x3; theirs 14x8), "
             "dots on screen while every node law was green. Its own headless Chrome on a free port, REAL input (Tools tab, "
             "builder card, right-hand slot; Vault tab, a mule, its right-hand slot): every fold on the rail, at 2000x1300 "
             "and 375x812 and in the mule host, draws at least two thirds of their chevron in PIXELS (its clip shown vs "
             "hidden, decoded by frozen_frames.png_rows), open points up and folded down, and a pressed folded chevron "
             "opens and turns up. No browser binary = declared skip (77). 4 cases, 2 red-proofs",
         skip_ok=()),
    Gate("test_the_mule_window_places_by_hand",
         [sys.executable, os.path.join(HERE, "test_the_mule_window_places_by_hand.py")], 90,
         needs_app=False,
         why="#174 v-B2 - his order: move an item to any cell and it LOCKS there (his_mule_locked_21: a ring he dragged "
             "would not move - nothing in the window could hold a chosen cell). Drives the SHIPPED vault span in node: "
             "packGrid takes occupied rectangles; _muleLoad lays d2r_mulePos spots FIRST and first-fit flows around "
             "them (every item once, no overlap, grid-fault clean, on a spilled Mule 2 and in the inventory); a "
             "footprint past the edge or over another hand-placed item is refused with its reason and nothing is "
             "written; a spot that no longer fits is REPORTED (loader, window NOTES, calc row, shelf card) and never "
             "rewritten; unlock returns it to first-fit; a drop on a Mule tab or a stash tab lands in the first free "
             "cell there; copies place one by one; the store forks per world and rides Backup & Share; the shelf "
             "card's shipped line and the window read the same packer AND the same names (the MAGIC & RARE locker's "
             "magicFinds keepers, fix round); SUMMARY, CALCULATIONS and the gold box count "
             "one mule the same with gear worn (the Grok seat's v-B finding). And every mule-window harness hands "
             "node its program on STDIN: as one argv string (node -e) the cut passed Linux's 131,072-byte "
             "argument cap, so the shell and equip laws were RED on CI (main 1e1f946e: errors=19 / errors=26) "
             "while green on the Mac. 15 cases, 13 red-proofs",
         skip_ok=()),
    Gate("test_the_character_builder_is_joined_to_the_engine_and_the_mule_window",
         [sys.executable, os.path.join(HERE, "test_the_character_builder_is_joined_to_the_engine_and_the_mule_window.py")], 90,
         needs_app=False,
         why="#174 v-B2 integration - the merge order: the builder's STATS column renders D2R_CHAR_ENGINE.sheet(build, "
             "{difficulty, quests}) with their Normal / Nightmare / Hell tabs and the Quests toggle driving it, every row "
             "value / range + cap + source; and the mule window's hover is the builder's one in-game tooltip, window.d2Tip. "
             "Written against two halves that each passed their own law and never met: handed its build raw, the engine "
             "read the builder's q 'u' as 'a u item' (every row UNKNOWN), its column-keyed typed rolls (p2) as no line "
             "(silently a range) and its `active` set as Set 1. Drives the SHIPPED builder + engine + mule-tip scripts "
             "together in node: Sorceress, Hell, quests on, Crown of Ages + Vipermagi + Mara's + Oculus = fire 10..45 "
             "untouched and 20..45 with the Crown typed 30 through its own roll box (worked by hand), cap 75, RANGE, "
             "drawn '10–45%' RANGE 'cap 75%'; Normal 75 (raw 90..125), Nightmare 60..75 (raw 60..95), quests off "
             "-20..15; a roll the engine shares no range with (Bone Break) is never guessed and STATS names it; the 8 "
             "Rainbow Facets reach the engine by *ID; Set 2 sums Set 2; a vault name opens the builder's entry "
             "(nicknames, runes by socket class, bases, UNKNOWN for none or many); the box honours its floor; the "
             "board's two hover lanes ask window.D2TIP_OWNS. FIX ROUND, the tooltip and the sheet agree about one item: a "
             "runeword keeps its base (Chains of Honor 697-890, never 892), a blank-par per-level line is its roll "
             "(Fortitude 80-120), the shift is the table's (Eaglehorn 480), Hellslayer's maximum is 602, Guardian Angel "
             "names four maximum resistances, Hellfire Torch rolls a CLASS, a class-locked item on another class is red "
             "and counts nothing, a magic charm leaves FCR EXACT. 16 cases, 22 red-proofs",
         skip_ok=()),
]

SKIP_EXIT = 77          # a gate that could not run (must match tv/js_syntax_gate.py)

_OK = re.compile(r"^(OK|✅|Ran \d+ tests)", re.M)


def _skip_allowed(g, reason):
    """v1925 — which declared reason (if any) covers this SKIP. None means it is a FAILURE.

    The reason string is the gate's own last output line, so the patterns below are matched against
    what the gate SAYS, not against why we think it stopped. A gate that skips silently produces an
    empty reason and matches nothing — which is the correct verdict: an unexplained skip is the
    least trustworthy state a required gate can be in.
    """
    for pat in g.skip_ok:
        if re.search(pat, reason or "", re.I):
            return pat
    return None


def _app_up(port=17772, timeout=1.5):
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/api/status" % port, timeout=timeout):
            return True
    except Exception:
        return False


_skip_reasons = []          # (gate, reason) for every case unittest reported as skipped


def leaked_by_this_run(before, after, me, here):
    """-> (leaked, theirs). `before` / `after` are {pid: (ppid, command)} tables taken at the start and the end of
    the run; `me` the pids of this run (run_gates and the `ps` it spawned); `here` the tree path a leak names.

    NEW since the run started AND naming this tree - both halves load-bearing (see the check in run()). #31, measured
    2026-09-26: that alone BLAMED HIS CONSOLE. His :17772 console forks an OCR worker whenever it reads a frame; the
    worker runs `tv/...` from this tree, and it is new if it started mid-run - so the gate printed "THIS RUN LEFT 1
    PROCESS RUNNING" about a child of a process that was running before the run began, and the only advice it gives
    ("kill by PID") would have killed his console's work. A leak of THIS run can only descend from this run: a gate is
    waited for, so whatever it left is re-parented to launchd (ppid 1) or still hangs under run_gates itself. So the
    parent chain decides: it reaches `me` or ppid 1 first -> ours (leaked); it reaches a process that was ALREADY
    running before the run (and is not us) -> THEIRS, reported by name with its owner and never counted."""
    before = before or {}
    after = after or {}
    me = set(me or ())
    leaked, theirs = [], []
    for pid in sorted(after):
        ppid, cmd = after[pid]
        if pid in before or pid in me or here not in str(cmd or ""):
            continue
        owner, cur, seen = None, pid, set()
        while cur in after and cur not in seen:
            seen.add(cur)
            pp = after[cur][0]
            if pp in me or pp <= 1:
                break                                   # ours: under this run, or orphaned to launchd
            if pp in before:
                owner = pp                              # a process that predates the run spawned it
                break
            cur = pp                                    # a NEW parent: keep climbing - it may be a leak's child
        if owner is None:
            leaked.append(pid)
        else:
            theirs.append((pid, owner))
    return leaked, theirs


def run(only=None, live_watch=True, live_writer=None):
    del _skip_reasons[:]
    """`live_watch` fingerprints the live-state files BETWEEN gates, so a leak is attributed.

    ⚠ v2419 — THE WATCHLIST COULD SAY WHAT MOVED AND NEVER WHICH GATE MOVED IT. main() fingerprints
    once before the whole run and once after, so CI reported `shadow_ledger.json (absent -> ...)`
    with no way to tell which of thirty gates wrote it — and each gate is a SEPARATE SUBPROCESS, so
    an in-process probe cannot see it either. I tried one: it ran 279 tests across the two suites
    that touch that ledger and found ZERO live writes, because the writer is in a subprocess.

    A delta is not actionable; a name is. That is the same lesson as the eagle row that said
    "32 against 34" until it was diffed BY NAME. [[feedback-suspect-the-instrument]]

    ⚠ AND IT WATCHES MORE THAN _LIVE_STATE, BECAUSE THE FILE THAT PROMPTED THIS IS NOT IN IT. My
    first cut used _live_fingerprint() and would have been INERT on the very case it was written
    for: `shadow_ledger.json` is not one of the sixteen named live-state files — it was caught by
    the whole-TREE diff, which main() only takes once. A guard that cannot fire on its own
    motivating example is measuring nothing, and that is the second time tonight I built one.

    MEASURED before choosing the net: a full tree fingerprint is 1.00s over 4,349 files, so 30s on
    a ~400s run; `tv/*.json` + `tv/*.jsonl` is 0.017s over 39 files, so 0.5s. The state files all
    live there, so the cheap net covers the case and the expensive one buys almost nothing.
    """
    results = []
    app_up = _app_up()
    _lw_prev = _state_fingerprint() if live_watch else None
    _lw_blame = []
    # ⚠⚠ v2659 — THE ORPHAN GUARD EXISTED AND HAD NEVER RUN ONCE ON THE GATED PATH.
    # `conftest.no_orphaned_children` is a `@pytest.fixture(scope="session", autouse=True)`, and
    # MEASURED 2026-09-05: there is NO pytest config anywhere in this repo (no pytest.ini,
    # setup.cfg, pyproject.toml or tox.ini), CI runs `python3 tv/run_gates.py`, and run_gates'
    # only mention of pytest is `.pytest_cache` in a directory skip-list. So the fixture is
    # structurally inert on every path that gates anything — `_descendants`, `leaked` and `reaped`
    # each occur ZERO times in this file. [[the-unjoined-end]]
    #
    # It is written for exactly the failure it never guarded: a suite spawned `tv/tv_diablo.py`
    # and never reaped it; it ran 22 MINUTES after the tests finished, writing stub reads into the
    # live `tv/state.json` and spending 39 of a 240-a-day read cap. And on 2026-09-05 Konyo said
    # *"my pc is super hot you left background processes running"* — the FOURTH such correction.
    # A guard that only runs under a runner nobody uses is the same defect as one that never runs.
    #
    # ⚠ THIS ONLY REPORTS. It names what leaked and never signals anything: `pkill -f` is banned
    # here, and killing by descendant-walk from inside the harness that spawned them is one bad
    # ppid away from taking his console. Naming is what was missing; killing is `claude-owns` and
    # `reap`, which is where the port and registration refusals already live.
    # ⚠⚠⚠ AND MY FIRST CUT OF THIS WAS ITSELF INERT — WRITTEN, PROVEN BLIND, REWRITTEN, SAME HOUR.
    # It used `conftest._descendants(table, os.getpid())`, i.e. it walked the process TREE down
    # from run_gates. That cannot work here and the reason is structural: `subprocess.run` WAITS
    # for each gate, so a child the gate leaked is re-parented to launchd the INSTANT the gate
    # exits — before this code ever looks. MEASURED: leaked pid found, ppid now 1, and
    # `_descendants(me)` returned []. The fixture it was lifted from is right to walk the tree —
    # pytest holds its children open — but run_gates does not, and copying the mechanism instead
    # of the QUESTION is [[copy-drift]] on a safety routine.
    #
    # So orphans are caught by IDENTITY, not parentage: any process that did not exist before the
    # run, exists after it, and names THIS TREE on its command line. That survives re-parenting,
    # which is the whole realistic case.
    # ⚠ The tree-path discriminator is what keeps it honest — without it every unrelated process
    # the machine happened to start during a 400-second run reads as a leak, and a guard that cries
    # wolf is one he learns to skip.
    _orphan_before, _orphan_ok = None, False
    try:
        import conftest as _cf                       # IMPORT the reader, never re-implement it
        _tbl, _ = _cf._live_processes()
        if _tbl:
            _orphan_before, _orphan_ok = dict(_tbl), True    # the TABLE, not a set: #31 walks the parents
    except Exception:
        pass                                        # no ps, no claim — UNKNOWN, never "clean"
    for g in GATES:
        if only and g.name not in only:
            continue
        if g.needs_app and not app_up:
            # v1925 — NO GATE SETS needs_app=True ANY MORE (test_button_matrix, the last one, boots
            # its own control_app on an ephemeral port since v1711), so this branch is currently
            # unreachable and the :17772 probe above only costs the run 1.5s. It is kept because the
            # NEXT gate that needs the live app will reach for it — and it is deliberately left
            # UNDECLARED in skip_ok, so the day someone sets needs_app=True the run goes red on his
            # Mac with the console down instead of quietly not running that gate. That is the whole
            # v1711 lesson: "needs_app was TRUE, so this gate was skipped before it could even try".
            results.append((g, "SKIP", 0.0, "control app is not running on :17772", ""))
            continue
        t0 = time.time()
        _lw_before = _lw_prev
        try:
            # v1868 — NO BLANKET TV_SESSIONS HERE, and that is a deliberate retreat.
            # Forcing a scratch journal on every gate DID stop the leaks — and broke eleven tests
            # that already isolate correctly by repointing control_app.HERE at a tempdir, because
            # an env var outranks their patch. A lock that overrides working isolation is not a
            # stronger guard, it is a different bug. The leaks are fixed where they were written
            # (the durability harness, the button matrix, the capped-vault-read test) and the
            # live-state watchlist below is what catches the next one — it caught all three within
            # an hour of learning to watch the journal. [[feedback-blind-fixture-green-gate]]
            # v2669 — ASK THE SUITE TO SAY WHY IT SKIPPED. v2668 gave the census a
            # denominator (12 of 12, not a bare 12) but still could not say WHAT stopped
            # running, which is CF-3's own complaint one level down: "a delta of 2 is not
            # actionable, two names are". unittest prints a skip REASON only at verbosity=2,
            # and every suite here hardcodes `unittest.main(verbosity=1)` — but argv wins, so
            # `-v` is enough and no suite has to change.
            #
            # ⚠ THIS DOES NOT BLOAT THE CI LOG. capture_output means nothing streams; the blob
            # is parsed and then DROPPED for a pass (a passing gate keeps only a 150-char
            # tail). The reasons are aggregated and printed as a short histogram, so the log
            # grows by a few lines, not by test_control's 2,233.
            #
            # Only unittest suites get -v. A non-suite gate (js_syntax_gate, render_check)
            # would either ignore it or, worse, read it as its own flag.
            _argv = list(g.argv)
            if len(_argv) > 1 and os.path.basename(str(_argv[-1])).startswith("test_") \
               and str(_argv[-1]).endswith(".py"):
                _argv.append("-v")
            p = subprocess.run(_argv, cwd=g.cwd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=g.timeout)
            dt = time.time() - t0
            # A GATE DECLARES ITS SKIP REASON ON STDOUT. Reading `stdout + stderr` let ANYTHING on
            # stderr — a SyntaxWarning, an atexit flush, a traceback tail — become the gate's
            # "reason" and displace the declared line, converting a DECLARED skip into an
            # UNDECLARED one, which :2025 counts as a build failure. That is exactly the camouflage
            # v2430 shipped to remove, arriving through the back door.
            # Measured on CI at af8beac: `render_check.py:332` emitted an invalid-escape warning
            # whose source echo `  "activate": """(function(){` became crest_loudness's reason
            # instead of its own `⚪ SKIPPED — no Chrome on :9224`. Invisible on Konyo's python3.9
            # (hidden DeprecationWarning), fatal on CI's 3.12 (visible SyntaxWarning).
            # stderr is still the fallback, because a gate that dies without printing anything to
            # stdout has its only explanation there — silence must not become an empty reason.
            _out = [ln for ln in (p.stdout or "").strip().split("\n") if ln.strip()]
            _err = [ln for ln in (p.stderr or "").strip().split("\n") if ln.strip()]
            blob = (p.stdout or "") + (p.stderr or "")
            # v1601 — exit 77 means "I could not run", not "I passed". Without this a gate that
            # self-skipped printed its own ⚠ SKIPPED line and still got counted green, which is the
            # lie this file's docstring opens by forbidding. js-syntax skips on every local run on
            # Konyo's Mac, so the surface least protected was the one showing a tick.
            if p.returncode == SKIP_EXIT:
                status = "SKIP"
            else:
                status = "PASS" if p.returncode == 0 else "FAIL"
            # ⚠⚠ THE STDOUT PREFERENCE IS FOR THE **SKIP** CASE ONLY — and the first cut applied it
            # to every status, which traded one hidden reason for another. TWO INDEPENDENT
            # REVIEWERS REACHED THIS FROM DIFFERENT DIRECTIONS, which is why it is taken rather
            # than argued: a cross-family read called it "displacement of stderr from tail", and a
            # same-family review named the consequence exactly — **unittest writes
            # `FAILED (failures=N)` to STDERR**, so any suite that also prints to stdout would show
            # an incidental print as its failure reason in the summary table. Measured stdout
            # printers among the gates: test_button_matrix (27 prints), test_routes (5),
            # test_control (2), and test_scope_reach_signal's own new informational line.
            #
            # So the rule splits by what the line is FOR:
            #   · SKIP — the gate DECLARED a reason on stdout, and stderr noise must not displace
            #     it. That is the crest_loudness defect this whole ship exists to fix.
            #   · FAIL/PASS — the diagnosis is whatever the run said LAST, on either stream,
            #     because unittest's verdict lives on stderr.
            # [[feedback-contradiction-is-the-finding]] — two checks disagreeing WAS the finding.
            if status == "SKIP":
                tail = (_out or _err)[-1:] or [""]
            else:
                _both = [ln for ln in blob.strip().split("\n") if ln.strip()]
                tail = _both[-1:] or [""]
            # v1925 — the blob is kept for a SKIP too. An undeclared skip is now a failure, and a
            # failure has to be diagnosable from the log alone: the reason column is only the LAST
            # line the gate printed, which for a suite that skipped in setUp is rarely the sentence
            # that says why.
            # v2668 — CARRY THE DENOMINATOR WHILE THE BLOB IS STILL IN HAND. The blob is
            # dropped for a PASS (right above), so by the time the case-census runs, the only
            # surviving text is this 150-char tail. unittest's own summary says "OK (skipped=26)"
            # and never how many ran, so the census could report a suite and a count and NOTHING
            # to divide it by — "test_chronicle_template=12" reads like a detail when it is in
            # fact 12 of 12, a gate that passed while covering NOTHING on this venue.
            # [[zero-needs-a-denominator]] [[regression-guard]]
            for _sk in re.findall(r"\bskipped ['\"](.{3,120}?)['\"]", blob or ""):
                _skip_reasons.append((g.name, _sk.strip()))
            _detail = tail[0][:150]
            if "skipped=" in _detail and " of " not in _detail:
                _ran = re.search(r"Ran (\d+) test", blob or "")
                if _ran:
                    _detail = re.sub(r"skipped=(\d+)",
                                     lambda m: "skipped=%s of %s" % (m.group(1), _ran.group(1)),
                                     _detail)[:170]
            results.append((g, status, dt, _detail, blob if status in ("FAIL", "SKIP") else ""))
        except subprocess.TimeoutExpired:
            results.append((g, "FAIL", time.time() - t0,
                            "timed out after %ds — a hung gate is a failed gate" % g.timeout, ""))
        except OSError as e:
            results.append((g, "SKIP", time.time() - t0, "could not launch (%s)" % e, ""))
        if live_watch:
            _lw_now = _state_fingerprint()
            _moved = _live_state_diff(_lw_before, _lw_now,
                                      names=sorted(set(_lw_before) | set(_lw_now)))
            if _moved:
                _lw_blame.append((g.name, _moved))
                # ⚠ ATTRIBUTION IS NOT BLAME WHEN SOMETHING ELSE IS ALSO WRITING. On his Mac the
                # console and a sweep write these files continuously, so a gate that merely ran
                # while they did would be named as the culprit. Say which it is instead of
                # implying. [[feedback-contradiction-is-the-finding]]
                _who = ("⚠ but %s is running, so this may be its write and not the gate's"
                        % ", ".join(live_writer)) if live_writer else \
                       "nothing else was writing, so this gate did it"
                print("   \u26a0 state moved during `%s`: %s — %s"
                      % (g.name, "; ".join(_moved), _who), flush=True)
            _lw_prev = _lw_now
    if live_watch and _lw_blame:
        print()
        print("\u26a0 WHICH GATE %s:" % ("MAY HAVE TOUCHED HIS LIVE STATE — suspects, because "
                                          "something else was writing too" if live_writer
                                          else "TOUCHED HIS LIVE STATE — attributed, not just "
                                               "detected"))
        for name, moved in _lw_blame:
            print("     %-22s %s" % (name, "; ".join(moved)))
        print("   Each gate runs as its own SUBPROCESS, so this is the only place the writer can be")
        print("   named. Find it there rather than adding the file to an ignore list — the point of")
        print("   the watchlist is WHO WROTE IT.")
        if live_writer:
            print("   ⚠ %s was running throughout, so these are SUSPECTS, not verdicts. The clean"
                  % ", ".join(live_writer))
            print("     read is a CI run, where nothing else touches the tree.")

    # ── v2659 — WHAT THE RUN SPAWNED AND NEVER REAPED ───────────────────────────────────────
    # The other half of the guard above. Every gate is its own subprocess, so anything a gate
    # leaves behind is a descendant of THIS process — which makes here the only place it can be
    # seen at all, and the reason the pytest fixture could never have covered a run_gates run.
    if _orphan_ok:
        try:
            import conftest as _cf
            _tbl2, _ps_pid = _cf._live_processes()
            if _tbl2 is None:
                # ⚠ ps ANSWERED ONCE AND NOT TWICE. That is UNKNOWN, and it must not read as a
                # clean sweep — the whole point of this block is that silence is not evidence.
                print("\n⚠ ORPHAN CHECK UNKNOWN — the process table could not be read a second "
                      "time, so nothing was established about what this run left behind.")
            else:
                # NEW since the run started, AND naming this tree. Both halves are load-bearing:
                # "new" alone catches every unrelated thing the machine started in 400 seconds;
                # "names this tree" alone catches his own console, which was running before us.
                _me = {os.getpid(), _ps_pid}
                # #31: attributed by the parent chain - a new tree process whose chain reaches a process
                # that was running BEFORE the run (his console's OCR worker) is THEIRS, named, never counted
                _leaked, _theirs = leaked_by_this_run(_orphan_before or {}, _tbl2, _me, HERE)
                if _theirs:
                    print("\n· %d new tree process(es) belong to processes that were running before this run "
                          "(not counted as leaks):" % len(_theirs))
                    for _p, _o in _theirs:
                        print("     pid %-7s spawned by pid %-7s %s" % (_p, _o, str((_tbl2.get(_p) or (None, ""))[1])[:80]))
                if _leaked:
                    print("\n❌ THIS RUN LEFT %d PROCESS(ES) RUNNING:" % len(_leaked))
                    for _p in _leaked:
                        _cmd = (_tbl2.get(_p) or (None, ""))[1]
                        print("     pid %-7s %s" % (_p, str(_cmd)[:100]))
                    print("   A gate that spawns and does not reap keeps writing after the verdict")
                    print("   is printed — one such leak ran 22 minutes past the suite and spent 39")
                    print("   of a 240-a-day read cap into his live state.")
                    print("   ⚠ NOT KILLED FROM HERE. `pkill -f` is banned and a descendant-walk is")
                    print("   one bad ppid from his console. Kill by PID, or use `claude-owns")
                    print("   sweep -f` / `reap -f`, which refuse his ports by name.")
        except Exception as _oe:
            print("\n⚠ ORPHAN CHECK UNKNOWN — %s" % str(_oe)[:80])
    else:
        print("\n⚠ ORPHAN CHECK NOT TAKEN — the process table was unreadable at the start of the "
              "run, so there is no baseline to compare against. UNKNOWN, not clean.")
    return results


# v1751 — ONE GATE RUN PER TREE. This is REG-162's reproduced cause, not a theory: two runs were
# started at once and each failed a DIFFERENT gate (robot_smoke in one, test_roundtrip_sim in the
# other) while a clean single run passed 30/30. Every one of those gates passes alone. They share
# ports, reel directories and the journal, so whichever gate happens to need an exclusive one loses
# — and the verdict names the loser, never the collision. A gate that is wrong about the tree
# because of what else is running is the worst kind of red: it sends you to debug working code.
#
# flock, deliberately: the kernel drops it when the process dies, so a crashed or kill -9'd run
# cannot leave a stale lock that refuses every future run. A pid file would need reaping logic, and
# reaping logic is how a lock starts lying.
#
# KEYED ON THE RESOLVED TREE, not on a fixed path, so his two worktrees can gate in parallel — they
# have separate reel dirs and separate journals, and the collision this prevents is within ONE tree.
# [[process-port-discipline]]
_LOCK_FH = None


def _claim_the_tree():
    """Take the per-tree gate lock, or explain who has it. Returns None on success, else a message."""
    global _LOCK_FH
    # D2R_GATE_LOCK_KEY exists for ONE reason: test_control.py is itself a gate, so when CI runs
    # `python3 tv/run_gates.py` the outer run holds this lock while TestOneGateRunPerTree spawns
    # child gate runs to prove the lock works. Without an override those children are refused BY
    # THE RUN TESTING THEM, and the test fails on CI while passing on every laptop — a gate blind
    # to its own venue. The children get their own key; the mechanism under test is unchanged.
    key = os.environ.get("D2R_GATE_LOCK_KEY") or os.path.realpath(REPO)
    safe = re.sub(r"[^A-Za-z0-9]+", "_", key).strip("_")[-80:]
    path = os.path.join(tempfile.gettempdir(), "d2r_gates_%s.lock" % safe)
    fh = open(path, "a+")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.seek(0)
        who = (fh.read() or "").strip() or "an unnamed run"
        fh.close()
        return ("another gate run already holds this tree (%s).\n"
                "   Two runs share ports, reel dirs and the journal, so a gate that needs an "
                "exclusive one fails and the verdict blames the gate.\n"
                "   That is REG-162's signature. Wait for it, or run in a separate worktree."
                % who)
    fh.seek(0)
    fh.truncate()
    fh.write("pid %d, started %s, tree %s\n"
             % (os.getpid(), time.strftime("%Y-%m-%d %H:%M:%S"), key))
    fh.flush()
    _LOCK_FH = fh   # held for the life of the process; the kernel releases it on exit
    return None


# ── FIXTURES NEVER TOUCH LIVE DATA — enforced, not intended ────────────────────────────────────
# The console keeps its state in files beside this script: the persisted sweep, the swept-reel
# marks, the visit marks. Those belong to the RUNNING console on his Mac, and a test must never
# write them.
#
# It did. test_chronicle_chain drove _chron_visit_run directly with the live paths still in place,
# so every gate run on this machine overwrote tv/chron_last_result.json with the fixture "Harlequin
# Crest"/"Windforce" from reels s_100/200/300. Found by opening that file expecting his footage.
#
# It turned dangerous the same day v1765 taught his board to ADOPT a persisted sweep automatically:
# the fixture carries four witnesses, so it would have been applied rather than queued, and neither
# name is in his grail. Two finds he never made, written into the dataset that is meant to be his
# own truth, by his own test suite.
#
# Redirecting the paths in that one setUp fixes today. This makes it STRUCTURAL: the runner
# fingerprints the live files before the set and again after, and fails the whole run if anything
# moved. A future test that forgets cannot pass quietly - which is the only kind of guard worth
# having, because the failure mode here is silent by construction.
# v1778 — THESE NAMES ARE READ FROM control_app.py, NOT GUESSED. The first version of this tuple
# listed "autoread.json" and "chronicle_autoread.json"; the real file is chron_autoread.json, so the
# guard built to catch REG-179 was blind to the visit-mark file for its whole life. Caught by
# review_lite.py, which compares this tuple against the _*_PATH constants themselves.
# v1867 — THE FILE THE LEAK ACTUALLY USED WAS NOT ON THIS LIST.
# This guard exists to catch a test writing his live state, and it watched five files while
# test_reel_index_durability appended 1,729 rows to a SIXTH — sessions.jsonl, his session journal,
# 75% of every session_end row in it, for months, through every green run of this gate. A watchlist
# that omits the busiest live file is a gate blind to the thing it was built for.
# [[feedback-blind-fixture-green-gate]] [[feedback-fixtures-never-touch-live-data]]
# chron_reads.json joins it for the same reason: it is live state added this week and the list did
# not follow.
_LIVE_STATE = ("tooltip_find.json",      # v2321 — did a located tooltip really turn out to be one
                "main_character.json",    # v2320 — what his gear is, learned from sightings
                "retro_gate.json",        # v2320 — the accuracy gate banks every graded read
                "capture_doors.json",      # v2316 — per-door Wilson ledger, written on every open/seal
                "shadow_watch.json",       # v2304 — the watcher writes every 20s
               ".board_identity.json",   # v2147 — a test that forgets to patch
               #   _BOARD_ID_PATH would otherwise mutate his real world record unseen
               "chron_last_result.json", "chronicle_swept.json", "chron_autoread.json",
               "chron_evidence.json", "vault_swept.json", "sessions.jsonl",
               "chron_reads.json", "vault_last_result.json",
               # v2177 — the hunt memory, the SIXTH live-state file, joins on day one. It records
               # which paid hunts came back empty; a throwaway test name marked "already empty" in
               # his real memory stops a REAL hunt from ever running until new footage arrives.
               # Its own suite wrote his live copy once before isolation landed, which is why
               # review_lite blocked the push that added it. [[feedback-fixtures-never-touch-live-data]]
               "chron_hunt_memory.json",
               # v2189 — the board's tally, POSTed by bible.html. Live state naming his counts.
               "board_tally.json",   # v1895 — new live state joins on day one
               # v3470 — the two eagle ledgers never joined. Seven
               # suites wrote fixture checks into them on every run and this list never
               # named them, so CI filed it under "also touched", never as a failure.
               ".unknown_age.json", ".eagle_slow.json",
               ".bake_seed_receipt.json")   # v3475 — the baker's receipt


def _console_is_running(port=17772):
    """v1774 — the guard below cannot tell a TEST writing his console state from the CONSOLE writing
    it, and the console writes those files as its normal job. Accusing the suite because his app is
    open would be a false red, and a gate that cries wolf gets ignored — so the check is SKIPPED and
    said out loud, never quietly passed. [[feedback_silence_is_not_evidence]]"""
    import socket
    s = socket.socket()
    s.settimeout(0.4)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


_SWEEP_LOCK = os.path.join(HERE, ".sweep.lock")


def _sweep_in_progress(max_age_s=900):
    """v1780 — A SWEEP DECLARES ITSELF, because lsof cannot see one.

    The first attempt asked the kernel who held the state files open; a sweep writes them with
    tmp+rename, so it holds nothing and the guard still blamed the suite. A lock file with a
    heartbeat is the honest signal: a sweep touches it while it runs, and a stale one (older than
    max_age_s) is ignored so a crashed sweep cannot disable the guard forever.
    """
    try:
        age = time.time() - os.path.getmtime(_SWEEP_LOCK)
        return age < max_age_s
    except Exception:
        return False


def _external_writer(names=_LIVE_STATE):
    """v1780 — IS SOMETHING OTHER THAN THE SUITE WRITING THESE RIGHT NOW?

    The guard exists to catch a TEST writing his console state. A background sweep writing the
    accumulated ledger is legitimate and the fingerprint cannot tell them apart, so it accused the
    suite of a change a chronicle sweep had just made. A gate that cries wolf gets disabled, so ask
    the kernel instead: if a process outside this run holds one of these files open, the check is
    SKIPPED and said out loud rather than failed. [[feedback_suspect_the_instrument]]
    """
    import subprocess
    held = []
    for n in names:
        p = os.path.join(HERE, n)
        if not os.path.exists(p):
            continue
        try:
            r = subprocess.run(["lsof", "-t", p], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5)
            pids = [x for x in (r.stdout or "").split() if x.strip() and int(x) != os.getpid()]
            if pids:
                held.append("%s (pid %s)" % (n, ",".join(pids[:3])))
        except Exception:
            pass
    return held


# v1874 — THE WATCHLIST BECOMES THE WHOLE TREE.
#
# A named list is a list of the leaks somebody already found. It named five files while a harness
# wrote a sixth (1,729 rows), and adding that sixth immediately caught two more writers, and then a
# whole-tree hash caught five files nobody had thought to name — including .subscription_budget.json,
# which meant every push spent a real vision call on his account.
#
# So: hash EVERYTHING here, not a list. Measured with his console down, after the last writer was
# fixed, a full 32-gate run leaves tv/ byte-identical — so this can be armed without inventing false
# reds. The exclusions are the three that legitimately churn: git internals, bytecode caches, and
# his footage (the frames dir is enormous and a sweep writing an index there is not this gate's
# business). [[feedback-blind-fixture-green-gate]]
_TREE_SKIP_DIRS = {".git", "__pycache__", "frames", "node_modules", ".pytest_cache"}


def _tree_fingerprint():
    import hashlib
    out = {}
    for root, dirs, files in os.walk(HERE):
        dirs[:] = [d for d in dirs if d not in _TREE_SKIP_DIRS]
        for f in files:
            p = os.path.join(root, f)
            try:
                with open(p, "rb") as fh:
                    out[os.path.relpath(p, HERE)] = hashlib.md5(fh.read()).hexdigest()[:16]
            except Exception:
                continue
    return out


def _live_fingerprint():
    import hashlib
    out = {}
    for n in _LIVE_STATE:
        p = os.path.join(HERE, n)
        try:
            with open(p, "rb") as fh:
                out[n] = hashlib.sha256(fh.read()).hexdigest()[:16]
        except FileNotFoundError:
            out[n] = None          # absent is a state too, and creating one IS a mutation
        except Exception as e:
            out[n] = "unreadable:%s" % e
    return out


#: state files a gate has been SEEN to write, named so coverage does not depend on their existing.
#: Distinct from _LIVE_STATE, which is the list whose movement is a FAILURE — this one only decides
#: what gets watched for ATTRIBUTION. Every entry here was named by a real CI run.
_NAMED_STATE_FILES = (
    "shadow_ledger.json",      # test_control, 14 tests, via a real sweep -> _shadow_bank
    "capture_doors.json",      # test_control / test_roundtrip_sim / test_button_matrix
    "disk_history.jsonl",      # test_control / test_button_matrix
    "known_frames.json",       # test_agent
    "retro_gate.json",         # test_retro_gate
)


def _state_fingerprint():
    """Every state file a gate could plausibly write, keyed by name. -> {name: hash or None}

    ⚠ WIDER THAN _LIVE_STATE ON PURPOSE. That list names sixteen files whose movement is a FAILURE;
    this one exists to ATTRIBUTE a movement to a gate, so it must cover anything a subprocess might
    create — including `shadow_ledger.json`, which is not on the failure list and is exactly the
    file that prompted this. Absent is recorded as None, because creating a file IS a mutation.
    """
    import glob as _g
    import hashlib
    out = {}
    # ⚠⚠ v2659 — THE GLOB MISSED FOUR FILES THE OTHER GUARD NAMES AS PROTECTED, and they are the
    # four whose NAMES are unusual rather than whose importance is. `*.json` does not match a
    # DOTFILE (the console-scars store) and does not match a different extension at all (the three
    # `.healer_bak` files — the healer's ONLY copies of the vault stores). MEASURED 2026-09-05: of
    # conftest.LIVE_FILES' 15, this net covered 10; the 5 it missed were those four plus the vault
    # ledger, which is merely absent today.
    # ⚠ THE STORES ARE NAMED BY ROLE, NOT BY FILENAME, ON PURPOSE. `store_owners.audit()` asks
    # `store in src`, so writing a store's literal filename in a comment here reads as this module
    # COUPLING to it — and the first version of this note did exactly that, turning the whole gate
    # set red with `1 store(s) are touched by a module nothing declares: run_gates`. The only
    # occurrence in this file was the comment. [[source-reading-guard]]
    # A backup that a suite silently overwrites is worse than a live file it overwrites, because
    # the backup is what the repair reads. [[unknown-stays-unknown]]
    for pat in ("*.json", "*.jsonl", ".*.json", "*.healer_bak"):
        for p in _g.glob(os.path.join(HERE, pat)):
            n = os.path.basename(p)
            try:
                with open(p, "rb") as fh:
                    out[n] = hashlib.md5(fh.read()).hexdigest()[:16]
            except Exception as _e:
                # ⚠ UNREADABLE IS NOT ABSENT, and recording it as None made them the same fact.
                # A torn read would look like absence and the next successful read like CREATION,
                # attributed to whatever gate happened to be running. `_live_fingerprint` already
                # records "unreadable:..." for this reason; matching it keeps one vocabulary.
                # [[unknown-stays-unknown]]
                out[n] = "unreadable:%s" % str(_e)[:24]
    for n in _LIVE_STATE:                      # keep the named ones even if they are absent
        out.setdefault(n, None)
    # ⚠ AND THE ONES CI HAS ACTUALLY NAMED, WHETHER OR NOT THEY EXIST YET. The glob can only see
    # files that are already there — and on a fresh CI checkout these are ABSENT, which is exactly
    # the "absent -> created" case that started this. The union of before/after in run() does catch
    # a creation, so the attribution was not broken; but a file that is absent at the first
    # fingerprint is invisible to any check that asks "is it covered", and that ambiguity is not
    # worth keeping. Naming them makes coverage independent of whether the file happens to exist.
    for n in _NAMED_STATE_FILES:
        out.setdefault(n, None)
    return out


def _live_state_diff(before, after, names=None):
    moved = []
    for n in (names if names is not None else _LIVE_STATE):
        b, a = before.get(n), after.get(n)
        if b != a:
            was = "absent" if b is None else b
            now = "absent" if a is None else a
            moved.append("%s (%s -> %s)" % (n, was, now))
    return moved


def _tree_diff(before, after):
    """Every file under tv/ that the run created, changed or removed. v1874 — the named list is a
    list of the leaks somebody already found; this is the one that finds the next one."""
    return sorted(_live_state_diff(before, after, names=sorted(set(before) | set(after))))


def _cost_table():
    """-> (table | {} | None, the sentence naming what the shards are balanced on).

    ⚠ ONE DECISION, TWO READERS. The second eye on ea3f05da: after v3477 the shard banner still
    printed "balanced by declared timeout" on every --shard run while cost_weights() balanced on the
    measured table — the label outlived its referent at a second site after the docstring was fixed.
    cost_weights() and the banner now read this, so the words cannot drift from the weights again.
    [[label-outlived-referent]] [[unknown-stays-unknown]]
    """
    try:
        import gate_costs as _gc
        table = _gc.load()
    except Exception as e:
        return {}, "declared timeout — gate_costs would not import (%s)" % type(e).__name__
    if table is None:
        return None, "declared timeout — tv/gate_costs.json exists and is UNREADABLE"
    if not table:
        return {}, "declared timeout — there is no measured cost table"
    return table, ("measured CI seconds from tv/gate_costs.json (%d gates measured; the median for "
                   "any it has not seen)" % len(table))


def cost_weights(gates=None):
    """{gate name: weight} — measured CI seconds from tv/gate_costs.json, the MEDIAN measured cost for
    a gate the table has not seen, or the declared timeout when there is no table at all."""
    gates = list(GATES if gates is None else gates)
    table, _basis = _cost_table()
    if not table:
        return dict((g.name, float(g.timeout or 0)) for g in gates)
    vals = sorted(table.values())
    med = vals[len(vals) // 2]
    return dict((g.name, float(table.get(g.name, med))) for g in gates)


def shard_names(k, n, gates=None):
    """The K-th (1-based) of N deterministic, cost-balanced slices of the gate set. -> sorted names

    v3472 (#184) — THE GATE SET OUTGREW ITS CI CEILING. The agent-suite job ran 25m18s against
    timeout-minutes 25 on d9bdb682 and GitHub CANCELLED it: no verdict for the shipped version. The
    workflow's own words are the ruling — "The fix is to shard the gate set, never to raise the
    ceiling" — and test_a_cut_off_gate_set_is_not_a_verdict caps the ceiling at 25 to hold it.

    Longest-processing-time greedy on each gate's cost_weights() — MEASURED CI seconds from
    tv/gate_costs.json since v3477 (the median for a gate the table has not seen, declared timeout
    only when there is no readable table): heaviest first into the lightest slice, ties by name, so
    every run on every machine cuts the SAME slices. The union of all N slices is the whole set and
    they are disjoint — both pinned by test_the_gate_set_shards_cleanly.
    ⚠ #219 — this said "DECLARED timeout … a proxy" for a release after v3477 replaced it: a label
    that outlived its referent. Witnessed on CI run 35943284218: 13m33s / 13m58s.
    """
    gates = list(GATES if gates is None else gates)
    if not (1 <= int(k) <= int(n)) or int(n) > len(gates):
        raise ValueError("shard %s/%s is not a slice of %d gates" % (k, n, len(gates)))
    # ⚠⚠ v3477 — BALANCE ON WHAT A GATE COSTS, NOT ON WHAT IT DECLARES. The first sharded run split
    # by declared timeout and came back 8m41s / 17m25s; measured from its logs, test_control alone is
    # 430 of 1,457 gate-seconds. tv/gate_costs.json is that measurement; a gate it has never seen
    # weighs the MEDIAN measured cost. With no table at all, declared timeout is the fallback.
    weigh = cost_weights(gates)
    bins = [[0.0, i, []] for i in range(int(n))]
    for g in sorted(gates, key=lambda g: (-weigh[g.name], g.name)):
        b = min(bins, key=lambda b: (b[0], b[1]))
        b[0] += weigh[g.name]
        b[2].append(g.name)
    return sorted(bins[int(k) - 1][2])


def main(argv):
    ap = argparse.ArgumentParser(description="run the gate set and return one verdict")
    ap.add_argument("--only", nargs="*", help="run only these gate names")
    ap.add_argument("--shard", help="K/N — run the K-th of N deterministic cost-balanced slices (#184)")
    a = ap.parse_args(argv[1:])
    only = a.only
    if a.shard:
        # ⚠ exit 2 is "NO GATE RAN" everywhere this file's verdict is read, and each refusal below is
        # exactly that. An EMPTY list would be worse than a refusal: `run()` reads `if only and ...`,
        # so [] means EVERY gate, and a mis-cut slice would silently run the whole set twice.
        if a.only:
            print("⛔ REFUSED — --shard and --only together name two different selections; NO gate ran")
            return 2
        try:
            _k, _n = [int(x) for x in str(a.shard).split("/")]
            only = shard_names(_k, _n)
        except Exception as e:
            print("⛔ REFUSED — --shard %r is not a slice of the gate set (%s); NO gate ran" % (a.shard, e))
            return 2
        if not only:
            print("⛔ REFUSED — shard %s is EMPTY; NO gate ran" % a.shard)
            return 2
        print("── SHARD %d/%d: %d of %d gates (balanced on %s) ──"
              % (_k, _n, len(only), len(GATES), _cost_table()[1]))

    busy = _claim_the_tree()
    if busy:
        print("⛔ REFUSED — %s" % busy)
        return 2

    print("══ GATE SET ══")
    _console_live = _console_is_running()
    _sweep_live = _external_writer()
    if _sweep_in_progress():
        _sweep_live = _sweep_live or ["a chronicle sweep (tv/.sweep.lock)"]
    _live_before = _live_fingerprint()
    _tree_before = _tree_fingerprint()
    # hand the run what else is writing, so a gate is not blamed for his console's work
    results = run(only, live_writer=([("the console" if _console_live else None)] +
                                       list(_sweep_live or []) if (_console_live or _sweep_live)
                                       else None) and
                  [x for x in ([("the console" if _console_live else None)] +
                               list(_sweep_live or [])) if x] or None)
    _live_moved = _live_state_diff(_live_before, _live_fingerprint())
    # the named files are the FAILURE; everything else in the tree is reported by name so the next
    # leak is found the way tonight's five were, instead of waiting to be guessed at
    _tree_moved = [m for m in _tree_diff(_tree_before, _tree_fingerprint())
                   if m.split(" (")[0] not in _LIVE_STATE]
    # v1925 — an undeclared SKIP is decided BEFORE the table prints, so the line itself carries ⛔
    # rather than the same ⚠ a legitimate CI-only lane wears. Two states that read identically in
    # the log is how "js-syntax skipped for ~220 versions" stayed invisible in plain sight.
    _undeclared = {g.name for g, s, _, d, _ in results
                   if s == "SKIP" and not _skip_allowed(g, d)}
    for g, status, dt, detail, _blob in results:
        mark = {"PASS": "✅", "FAIL": "❌", "SKIP": "⚠"}[status]
        if status == "SKIP" and g.name in _undeclared:
            mark = "⛔"
        print("%s %-20s %6.1fs  %s" % (mark, g.name, dt, detail))

    failed = [g.name for g, s, _, _, _ in results if s == "FAIL"]
    if _live_moved and not _console_live and not _sweep_live:
        # not a warning: a suite that writes his console's state has already done the damage
        failed.append("live-state-untouched")
    skipped = [(g.name, d) for g, s, _, d, _ in results if s == "SKIP"]
    # v1925 — the verdict, not a warning: a required gate that did not run is not a clean run.
    failed += ["%s (undeclared SKIP)" % n for n in sorted(_undeclared)]
    print("\n── VERDICT ──")
    if _live_moved and (_console_live or _sweep_live):
        why = "the console is running on :17772" if _console_live else ("held by %s" % ", ".join(_sweep_live))
        print("⚠ SKIPPED live-state check — %s, so a change here is not the suite" % why)
        for m in _live_moved:
            print("     %s" % m)
    if _live_moved and not _console_live and not _sweep_live:
        print("❌ THE SUITE WROTE THE LIVE CONSOLE STATE — a fixture reached his data:")
        for m in _live_moved:
            print("     %s" % m)
        print("   Redirect the path in that test's setUp; never write files beside control_app.py.")
    if _tree_moved:
        _why = ("the console is running on :17772" if _console_live
                else ("held by %s" % ", ".join(_sweep_live)) if _sweep_live else "")
        print("⚠ THE RUN ALSO TOUCHED %d OTHER FILE(S) UNDER tv/%s:"
              % (len(_tree_moved), (" — %s, so this may not be the suite" % _why) if _why else ""))
        for m in _tree_moved[:12]:
            print("     %s" % m)
        if not _why:
            print("   Nothing here should move: with his console down, a full gate run leaves this "
                  "tree byte-identical (measured v1874). Find the writer before it becomes a "
                  "watchlist entry.")
    if skipped:
        # never silent: a check that did not happen is not a check that passed
        for n, d in skipped:
            print("%s SKIPPED %s — %s" % ("⛔" if n in _undeclared else "⚠", n, d))
    if _undeclared:
        # v1925 — LOUD IS NOT ACCOUNTABLE. Every entry in GATES is required, so a skip is a gate
        # that did not run; printing that beside exit 0 is the same lie as a false green, one
        # sentence further along. The allowed reasons are declared per gate (skip_ok=), so an
        # environment that quietly stops producing a lane turns the run red instead of shrinking it.
        print("\n⛔ %d REQUIRED gate(s) SKIPPED for a reason no lane declared:" % len(_undeclared))
        for g, s, _dt, d, blob in results:
            if s != "SKIP" or g.name not in _undeclared:
                continue
            print("   · %s — %s" % (g.name, d or "(the gate printed no reason at all)"))
            print("     declared skip reasons: %s"
                  % (", ".join(g.skip_ok) if g.skip_ok else "NONE — this gate may never skip"))
            for ln in [ln for ln in (blob or "").strip().split("\n") if ln.strip()][-6:]:
                print("       " + ln[:200])
        print("   Either fix the lane so the gate RUNS here, or add the reason to that Gate's "
              "skip_ok= and say which venue does run it. A gate that skips on every venue has "
              "never run at all.")
    if failed:
        # v1711 — SAY WHICH TEST, NOT JUST WHICH GATE.
        # The summary line was the gate's LAST output line, which for a unittest run is
        # "FAILED (failures=1)" — a fact with no address. A CI log carrying that and nothing else
        # cannot be diagnosed remotely, and these gates include browser lanes that SKIP on Konyo's
        # Mac (Chrome never answers --dump-dom over loopback there) and therefore run ONLY on CI.
        # So the one machine that can produce those failures was also the one that could not
        # report them, and the answer was to guess. Now the log carries the addresses.
        for g, st, _dt, _d, blob in results:
            if st != "FAIL":
                continue
            names = [ln.strip() for ln in blob.split("\n")
                     if ln.startswith(("FAIL:", "ERROR:")) or "AssertionError" in ln]
            print("\n── %s — what actually broke ──" % g.name)
            for ln in (names[:12] or [ln for ln in blob.strip().split("\n") if ln.strip()][-12:]):
                print("   " + ln[:200])
            if len(names) > 12:
                print("   … and %d more" % (len(names) - 12))
        print("\n❌ %d gate(s) FAILED: %s" % (len(failed), ", ".join(failed)))
        return 1
    # ── v2049 — COUNT THE CASES THAT DID NOT RUN INSIDE THE GATES THAT PASSED ────────────────
    # This file's own docstring already says it: "Silence about a check that did not happen is the
    # same lie as a false green." That rule was enforced for a whole GATE that skips. It was not
    # enforced one level down, and that is where it hid.
    #
    # MEASURED 2026-08-24 in atrue CI environment (a fresh clone, so tv/frames/ is absent because it
    # is gitignored): 45 gates passed while 24 individual CASES skipped inside them — 8 of them the
    # entire scoring half of test_stash_eye_aspect. The hand-labelled corpus had meanwhile rotted
    # from 14 frames to 7, losing EVERY negative, and CI stayed green the whole time because the
    # cases that would have failed never executed. The per-gate line said "OK (skipped=8)"; the
    # verdict said "45 gate(s) passed". Only the verdict gets read.
    #
    # Not promoted to a failure: most of these skips are legitimate on a runner that has no frames
    # and no second-eye binary. Making them fatal would just teach everyone to ignore a red gate,
    # which is the same decay in the other direction. Naming the number is what was missing.
    _cases = 0
    _where = []
    _dark = []
    for _g, _st, _dt, _d, _ in results:
        _m = re.search(r"skipped=(\d+)(?: of (\d+))?", str(_d or ""))
        if _m and _st != "SKIP":
            _n = int(_m.group(1))
            _ran = int(_m.group(2)) if _m.group(2) else None
            if _n:
                _cases += _n
                _where.append("%s=%d%s" % (_g.name, _n, ("/%d" % _ran) if _ran else ""))
                if _ran and _n >= _ran:
                    _dark.append((_g.name, _n, _ran))
    print("\u2705 %d gate(s) passed%s."
          % (len(results) - len(skipped),
             (", %d skipped for a DECLARED reason" % len(skipped)) if skipped else ""))
    if _cases:
        print("\u26a0 %d CASE(S) DID NOT RUN inside those gates: %s"
              % (_cases, ", ".join(sorted(_where))))
        print("   A gate that passes while its cases skip is not covering them. If a skip here is "
              "because a fixture is absent on this venue, that check has never run at all.")
    if _dark:
        # A suite whose skips equal its whole roster is not "mostly covered" — it is a PASS with
        # nothing behind it. Named separately because a bare count hides it: 12 looks small next
        # to 2,783 right up until you learn the suite only ever had 12.
        print("\u26d4 %d GATE(S) PASSED WHILE COVERING NOTHING ON THIS VENUE: %s"
              % (len(_dark), ", ".join("%s (%d of %d cases skipped)" % r for r in sorted(_dark))))
        print("   This is a PASS with an empty denominator. Treat it as UNKNOWN for this venue, "
              "never as evidence the suite's subject is healthy.")
    if _skip_reasons:
        _hist = {}
        for _gn, _r in _skip_reasons:
            _hist.setdefault(_r, []).append(_gn)
        print("   WHY THEY SKIPPED — the reason each case gave, most common first:")
        for _r, _gs in sorted(_hist.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:12]:
            _u = sorted(set(_gs))
            print("     %3d x  %s   [%s]"
                  % (len(_gs), _r[:96], ", ".join(_u[:3]) + (", +%d" % (len(_u) - 3) if len(_u) > 3 else "")))
        if len(_hist) > 12:
            print("     (+%d more distinct reason(s) not listed)" % (len(_hist) - 12))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
