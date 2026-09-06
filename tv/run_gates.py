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
_GATE_SCRATCH = tempfile.mkdtemp(prefix="tvd-gates-")
atexit.register(shutil.rmtree, _GATE_SCRATCH, True)


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
    Gate("test_gate_banks", [sys.executable, os.path.join(HERE, "test_gate_banks.py")], 120,
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
         skip_ok=(r"reel shelf is absent on this venue",)),
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
    Gate("test_prune_wilson", [sys.executable, os.path.join(HERE, "test_prune_wilson.py")], 120,
         why="the harness that sabotages the DELETER must be unable to delete, and must be\n"
             "able to go RED (A2 step 4). It calls exactly one console function, whose own\n"
             "docstring is \"Decides; never acts\", and refuses at write time to set\n"
             "TV_AUTO_PRUNE to anything that is not a spelling of OFF — v2082's scar, where\n"
             "only the byte \"0\" held and off/false/no/OFF all ARMED an unattended deleter.\n"
             "⚠ It strips comments before looking for forbidden calls, because prune_wilson's\n"
             "own docstring NAMES every one of them: a naive grep goes red on the sentence\n"
             "promising it does not delete."),
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
             "that might be gapped just like this was.\"* Swept: 41 stores, ANSWERS 4, PARTIAL 3, "
             "SILENT 21, REFERENCE 12, UNKNOWN 1. A SILENT verdict cannot be invalidated when its "
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
            _orphan_before, _orphan_ok = set(_tbl), True
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
                _leaked = sorted(
                    p for p, (_pp, _cmd) in _tbl2.items()
                    if p not in (_orphan_before or set())
                    and p not in _me
                    and HERE in str(_cmd or ""))
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
               "board_tally.json")   # v1895 — new live state joins on day one


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
            r = subprocess.run(["lsof", "-t", p], capture_output=True, text=True, timeout=5)
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


def main(argv):
    ap = argparse.ArgumentParser(description="run the gate set and return one verdict")
    ap.add_argument("--only", nargs="*", help="run only these gate names")
    a = ap.parse_args(argv[1:])

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
    results = run(a.only, live_writer=([("the console" if _console_live else None)] +
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
