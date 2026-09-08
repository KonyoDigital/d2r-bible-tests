# ⏩ RESUME HERE — written 2026-09-08 ~04:00, mid-session, Konyo away

## The one-line state
**14 commits sit unpushed, and NOTHING can ship until `tv/control_ui.html` renders clean** — the
pre-push gate grades the WORKING TREE, not the commit, so a broken file in the tree blocks every
commit behind it.

## ⛔ THE ONE BLOCKER
`tv/control_ui.html` (uncommitted, an agent's work) breaks the ADVANCED drawer. Measured both ways,
minutes apart, same machine:

| version of that one file | render_check.py |
|---|---|
| `git show HEAD:./control_ui.html` | **15 green · 0 red** |
| the working tree | **11 green · 8 red** |

Failing: `advanced`, `advanced-fleet`, `advanced-shadow` — *"the panel could not be ACTIVATED after
12.1s of polling"* — plus 3 matching COVERAGE refusals (those surfaces went UNMEASURED, a separate
fact from a layout defect).

**Already ruled out — do not redo:** machine load (re-run at load 3.10 with a pinned core freed,
still red) · JS syntax (`node --check` passes BOTH script blocks) · missing ids (`#shadow-adv`,
`#fleet-list` each present once, same as HEAD) · new cross-script-block calls (name set identical to
HEAD). ⇒ It is a RUNTIME activation failure on the path `_adv_activate` drives: it seeds
`localStorage d2r_advOpen=1`, opens the drawer, then polls for `#fleet-list` to be FILLED.

⚠ **ONE render_check runner at a time.** Two concurrent runs killed the browser and returned 12
surfaces as ⚪ UNKNOWN (`Errno 61 Connection refused`). The tool reports that honestly — do not read
those as defects.

## What shipped into the commits (not yet pushed)
- **#27** the self-rescue has a top rung — one gated relaunch when the reload fails. Never while
  recording, never on one failure, at most once per 15 min. 4 sabotages red.
- **#28 (half)** ON AIR spun "loading" while the recording ran. `start_agent` holds `_lock` across
  166 lines containing `Popen` + `sleep`; the four `/api/status` readers needed that lock for one
  `.poll()` each. Readers now bounded (0.25s) with a lock-free fallback. Sabotage blocks 3.005s of a
  3s hold.
- **the interaction between those two** — a refused read is not proof nothing is recording, so an
  escalation cannot relaunch during a capture start (`_recording_or_unknown`).
- **the automatic relaunch** now asks `nothing_in_flight()` at the point of no return; it was
  bypassing the busy checks `/api/relaunch` enforces.
- **#26** a sealed reel with unmeasurable names is UNKNOWN, not REG-340. 8 of 8 sabotages red.
- **#16** per-route doctor rows; inventory 2/46 OK, stash 11/46 OK, both chronicle routes UNKNOWN
  ("no reel on this shelf carries a sets ledger") — unexercised must never read OK.
- **REG-682** in `BUGS.md`.

**222 gates registered.**

## ⚠ REG-682 — the real open question
His console was found at **108–109% CPU for ~2 hours**, `/api/status` returning 0 bytes at a 25s
timeout, its log silent 38 minutes, **no capture running**, both children idle, while `/` still
served in 0.69s. `sample` shows `_PyEval_EvalFrameDefault` dominant — a runaway Python loop starving
every API thread through the GIL. **This refutes both lock hypotheses**, including mine: a thread
waiting on a lock burns 0% CPU. A fresh console on the same code idles at 0.0%.

Console was restarted (SIGTERM, clean exit 6s): 25s timeout → **0.022s**, CPU → 11.3%. It now
carries `faulthandler` on SIGUSR1 and `lockWait{blocked,reads}`, both verified live on his machine.

**Next occurrence: `kill -USR1 <pid>` dumps every thread's Python stack to the log**, and
`lockWait.blocked` climbing (or not) says whether a lock is involved at all. Do NOT close it as
"fixed by a restart". A grok-bot brief asking for `lockWait` readings during a sweep is on gh #180.

## Still open
- **#6 / #25** — the UI file above. The agent also still owes a plain yes/no on whether it captured
  screenshots at 375/901/1440 and whether a different family looked. Neither is evidenced.
- **#17** HIS CALL — needs the game open, the stash panel up, MINI AUTO pressed for ≥5 hovers.
- **#20** BLOCKED ON DATA — set qlvl. The render half is done; `_qlvlOf` reads the drop-table index
  (`_etaIdx`), which structurally covers only the set pieces that appear in it. The game's own
  SetItems table is not on this Mac (the CrossOver path is a 380K launcher stub, `Bottles/` empty).
  ⇒ Needs a source from him. Do not write 134 values from memory.
- **#29** HIS INSTRUCTION, 2026-09-08 — after the list ships, a proper ping-pong of upgrades and
  ships with Grok MCP + grok bot + the visual harnesses, skills and workflows. **Gated on the list
  shipping first**, by his own words.
