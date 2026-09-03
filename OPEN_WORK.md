# OPEN WORK — saved 2026-09-02, before a forced restart

> Written because he had to restart a frozen machine mid-session and asked: **"SAVE THIS LIST — i
> want all 31 pending on github + everything else left."** A list that lives in a session is not a
> list. This file is the durable copy; GitHub issues are the second.

## ⚠ FIRST THING AFTER THE RESTART — the machine froze for a reason, and it comes back

The freeze was **not** the D2R console alone. Measured at the time:

| pid | what | state |
|---|---|---|
| 17006 | his TV·D console | **104.9% CPU**, 17h, **12 defunct children never reaped** |
| 45140 + 21 more | `achilles-revival/pt_signal_server.py` | **all orphaned (PPID 1)**, spawned ~90s apart, never exiting |
| — | `tools/queue_refresh.sh` | crontab `*/5 * * * *` |

**Killing the 24 achilles processes did NOT stick — they respawn.** Two respawners, both still armed:

1. **launchd job `ai.kai.boot`** — `launchctl list | grep ai.kai.boot`
2. **crontab** — `*/5 * * * * /Users/konyo/achilles-revival/tools/queue_refresh.sh >/dev/null 2>&1`

He said *"wtf why is the pt-signal server and achilles revival even working now..... kill it"*.
Killing PIDs is not enough. **HIS CALL, because it is another project's config:**
  · `launchctl bootout gui/$(id -u)/ai.kai.boot`   (or `disable`, which survives reboot)
  · `crontab -e` and remove the `queue_refresh.sh` line

⚠ Do NOT do this unilaterally — the Achilles webhook door being open was a deliberate win
(`achilles_webhook_door_shut.md`). Ask which of the two he wants off.

**AND A SEPARATE REAL DEFECT:** his console leaks zombies — 12 defunct children, oldest 16.5h, while
every other parent on the machine had at most 1. It spawns subprocesses and never `wait()`s them.
Not the CPU cause, but a genuine leak with a named location. NOT YET FILED AS A TASK.

---

## Shipped and verified today (do not redo)

| version | what | proof |
|---|---|---|
| **v2433** | the theatre + shelf join the heart; scratch consoles die with their parent | live beat: `theatre {painted:true, ink:true}` · `shelf {filled:true, cards:3089}` · a full render run left ZERO orphans |
| **v2434** | a number a human types goes stale; an invariant graded but never run | on origin |
| `532f1125` | the shelf DATE column — the sentence took the row and the date got cut | cold cross-family read confirmed every date whole |
| **v2435** | `uiBeat.view` published + TASKS.md honesty becomes a gate | **REFUSED BY THE GATE, correctly** — see below |

### ⚠ v2435 IS COMMITTED (`b755a485`) AND NOT ON ORIGIN

The pre-push refused it for a real defect in my own new file:
`tv/tasks_freshness.py` prints 🔴🟢⚪ and never called `console_safe.enable()`, so on a non-UTF-8
console it crashes **while reporting** and a clean tree exits non-zero.

**FIXED in the working tree already.** Also already applied on top, uncommitted:
`/api/eagle` publishes the partition + the panel reads it (see #59 below).

**NEXT ACTION: bump to v2436, commit, push once.** Do not push v2435 alone — the gate run costs
~452s and batching is the rule.

---

## THE PENDING LIST — everything still open

### Architecture asks (his numbered A-list)
| # | task |
|---|---|
| A1 | self-proving gaps everywhere, wired to the heart |
| A2 | Wilson everywhere, and make the score actually mean something *(in progress)* |
| A3 | unify the surface × capability matrix: every surface gets the same four organs |
| A4 + A15 | the 3D/4D printer and THE RIVER: one start point, one funnel, per-reel routes |
| A5 | keep the surface at capture, and prove it BOTH WAYS |
| A6 | a gated AI reader BETWEEN the retro analyzers |
| A7 + A8 | every reel down one path, and the templates live INSIDE the routing |
| A9 | the 10-15% law: the engine throws the garbage out by default *(in progress)* |
| A10 | the fish down the stream: probe ONE reel through the whole river |
| A11 | census every lane: is it here, does it run, does it collaborate, is it reverse-engineered |
| A12 | blueprints AND reverse blueprints, and where they disagree is the finding |
| A14 | monotonic chronicle counter + ledger proof, so the profile can never be lost |
| A16 | THE HEART: eagle eye + watchdog + corroborator + doctor, and Wilson score it all |
| **A17** | **the console redesign — flagship, editorial titles, OCD-aligned** *(in progress)* |

**A17 remaining:** type scale · editorial titles · RARE PATHS widths. ⚠ The hero/dash split must be
decided BEFORE the type scale and the titles — both grow scrollHeight.

### Console faults (CF) — found by the corroborator sweep
| # | task |
|---|---|
| CF-1 | EXTRACTION LANES: chronicle and vault both stopped doing work hours ago *(in progress)* |
| CF-2 | BOARD JOIN: the window answering is the console, not the board (`path=/`) |
| CF-4 | CONSOLE UI FAULTS: the page beat while blank; he reported the class by hand |
| CF-5 | PROGRESS NUMBER: two worlds both claim to be him, 290 uniques vs 280 |
| CF-6 | `board_tally.json` grows a guest-world route per probe: 148 empty routes, nothing prunes |
| CF-8 | BOARD IS CLAIMED is UNKNOWN and has been 110 times |
| CF-9 | the render gate rendered four viewports his console never has; his real one is 1120x628 |
| CF-10 | the state panel cannot tell a FAULT from a DESIGNED REFUSAL *(in progress — see #59)* |
| CF-12 | two of thirty-four checks never run unattended, and nothing says so |
| ~~CF-13~~ | ✅ **DONE, and it was already done — this row was the stale thing.** Verified end to end 2026-09-03 and photographed on the live console: `scope_reach_state()` returns 4 rows, `heart_state()` carries them, `_hrtReach` renders them, and the section reads **"Promises a lane can still break · 4 · evidence, not a verdict"** with every reach count visible (ledger-backup 6 PERMITTED · shadow-watch 24 · stash-watch 34 · version-drift 72, all TOO BROAD). ⚠ My first grep said the UI rendered nothing — I searched for `scopeReach`/`scope_reach` when the function is `_hrtReach`. The zero was my search terms, not the code. |
| CF-15 | five suites write live state during a gate run; fix at the seam *(in progress)* |

### Numbered defects and blocked work
| # | task |
|---|---|
| 155 | APPROVED: run the paid reads, with the no-waste gate |
| 146 | prune 4.34 GB / 4,128 frames — APPROVED but BLOCKED until the river is built. **`_PRUNE_SAFE_TO_RUN` stays False. HIS call.** |
| 166 | lock the namespace, ledger authoritative — BLOCKED: the loggers carry no proof |
| 167 + 186 | show the eye in THE FLEET when it is live, and the eye contract |
| 133 + 136 + 148 + 154 | the four blocked defects, each waiting on something real |
| 181 + 184 | HE-1 and HE-4: UNBLOCK via `he_tap.swift` (Grok Bot corrected me) |
| 135 | daily-pick dead branch — the ONE row left in READY TO APPLY, and it has **no fingerprint**, so `tasks_freshness` reports it UNKNOWN every run |

### Grok Bot handoffs still open
| id | claim |
|---|---|
| GB-L-1 | HE-1 look — BLOCKED, no `D2R.exe`, HID dead |
| GB-L-2/4/5 | visual briefs posted, still awaiting his eyes |
| B-63 · B-65 · B-70 · B-71 · B-80 · B-81 · B-82 · B-83 · B-84 · B-86 · B-90 | the standing backend docket — **not closed, not forgotten** |

**CLOSED today:** GB-B-1, GB-B-2, GB-B-3, GB-B-4 (answered on #179) · GB-L-3, GB-L-6, GB-L-7
(answered on #180 from the live beat).

### New findings from today, not yet fixed
| # | finding |
|---|---|
| **#58** | **MY push cadence starves the one lane that can see his screen.** 33 of 46 Grok Bot visual ticks SKIPPED (72%), ten naming my pre-push. Batch 3–4 versions per push. |
| **#59** | **Two surfaces of one console count "need you" differently** — the panel says 9, the server says 7. `/api/eagle` returns raw rows so the panel re-derives without MINE. **Fix applied in the working tree, needs a guard.** |
| — | **his console leaks zombies** — 12 defunct children, oldest 16.5h. Not filed yet. |

### Final
| # | task |
|---|---|
| 30 | FINAL — full third-eye Grok audit + full debugging session over everything above |

---

## Rules that do not bend, restated so a fresh session has them

- never `--no-verify` · browser suites go to **GitHub CI**, never his Mac
- never `pkill -f` — kill by **PID or port**. `:17772` his console · `:9222` his Chrome · `:9223` TradingView · scratch on `:9224+` / `:179xx`
- **the pre-push grades the WORKING TREE, not the commit** — do not edit mid-push
- `git push | tail` reports **tail's** exit status. Confirm `origin/main` moved before claiming a ship.
- `timeout` is not installed — `perl -e 'alarm N; exec @ARGV'`
- **wait on a PID (`kill -0 $PID`), never on a pattern** — `pgrep -f X` matches its own siblings
- a gate never seen RED is measuring nothing · a SKIP is not a PASS · UNKNOWN is not clean
