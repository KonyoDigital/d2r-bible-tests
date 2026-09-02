# RESUME — read this FIRST in a new session, then act

> Written 2026-09-02 because his machine froze and he said: *"nothing erased — i want to be able to
> start this next chat with you perfectly from where we were, with the context and skills all
> loaded, workflows."* This file is the handoff. `CLAUDE.md` points at it.

---

## STEP 0 — LOAD THESE BEFORE THE FIRST TOOL CALL. Do not narrate it, do not ask.

**Always in this repo:** `d2r-bible` (project skill) · `test-venue` · `regression-guard` ·
`the-unjoined-end` · `unknown-stays-unknown`

**The work in flight touches all of these too — load them now, not at verification time:**
`visual-regression-detector` · `chrome-cdp-mac` · `grok-second-eye` · `heart-first` ·
`source-reading-guard` · `human-eyes-harness` (project skill) · `process-port-discipline` ·
`stale-reading` · `copy-drift` · `review-after-ship` · `borrowed-surface`

⚠ `d2r-bible` and `human-eyes-harness` are **directory-scoped**. The Skill tool answers "Unknown
skill" from `~`. That is not absence — read `.claude/skills/<name>/SKILL.md` directly.

**Workflow:** `/konyo-workflow` is used as a **plan-refuser before spending**, and only when he asks.
Do not launch a fleet unprompted — the cost is fixed regardless of task size.

---

## STEP 1 — THE THREE FILES THAT HOLD THE STATE

| file | what it holds |
|---|---|
| **`OPEN_WORK.md`** | every pending task, grouped; the freeze diagnosis; the rules |
| **`OPEN_WORK_NOTES.md`** | the measurements, the four times my instrument lied, the optimizations |
| **`TASKS.md`** | the long-lived task file (READY rows now carry fingerprints) |

Also on GitHub: **issue #209** carries both of the first two verbatim.
**#179** = Grok Bot backend queue · **#180** = live/eyes queue. Both are ticking every ~10 minutes.

---

## STEP 2 — THE VERY FIRST ACTION, precisely

**v2435 is committed as `b755a485` and is NOT on origin.** The pre-push refused it, correctly, for a
real defect in my own new file: `tv/tasks_freshness.py` printed 🔴🟢⚪ without calling
`console_safe.enable()`, so a non-UTF-8 console crashes *while reporting*.

**That is already fixed in the working tree.** So is a second change on top of it:
`/api/eagle` now publishes `needsYou/mine/mineWhat/unknown` and the panel reads it instead of
re-deriving the count without `MINE` (issue #59 in the list — the panel said 9, the server said 7).

```
cd ~/d2r_bible_tests
git log --oneline -3          # expect 8ebd4d2e, 5323271e, b755a485
git status --porcelain        # expect control_app.py + control_ui.html modified
python3 tv/tasks_freshness.py # expect exit 0, one UNKNOWN row (135)
```

Then: **bump to v2436, commit, push ONCE.** Do not push v2435 alone — the gate is ~452s and
batching 3–4 versions per push is the rule.

**STILL OWED on that ship:** a guard that would have caught the two-surfaces-one-number defect
(assert the panel does not re-derive a count the server publishes), **and it must be seen RED.**

---

## STEP 3 — WHAT HE ASKED FOR THAT IS NOT DONE

His standing order, verbatim in spirit: *"i want you fixing this and not stopping until every single
tasked grok bot/grok handoff is done + everything i asked of you"*, and *"im really wanting it to be
at 0 pending eventually — even if you have to add more pending to perfect the console."*

Closed today: **GB-B-1, GB-B-2, GB-B-3, GB-B-4** (#179) · **GB-L-3, GB-L-6, GB-L-7** (#180).
Still open: the eleven standing **B-nn** backend claims, **GB-L-1/2/4/5**, and the whole A-list.

---

## STEP 4 — THE MACHINE FROZE. IT WILL COME BACK.

Killing the 24 orphaned `achilles-revival` processes **did not stick**. Two respawners, both armed:

1. launchd **`ai.kai.boot`**
2. crontab **`*/5 * * * * ~/achilles-revival/tools/queue_refresh.sh`**

He said *"kill it"* — but disabling either is a durable config change to **another project**, and the
Achilles webhook door being open was a deliberate win. **ASK HIM WHICH ONE TO TURN OFF.**

And separately: **his console leaks zombies** — 12 defunct children, oldest 16.5h, while every other
parent on the machine had at most 1. Real, located, not yet filed.

---

## THE RULES THAT DO NOT BEND

- never `--no-verify` · browser suites run on **GitHub CI**, never his Mac
- never `pkill -f` — kill by **PID or port**. `:17772` his console · `:9222` his Chrome ·
  `:9223` TradingView · scratch on `:9224+` / `:179xx`. **Never relaunch `:17772`. Never kill 17006.**
- **the pre-push grades the WORKING TREE, not the commit** — do not edit mid-push
- `git push | tail` reports **tail's** exit status — confirm `origin/main` moved before saying shipped
- **wait on a PID (`kill -0 $PID`), never a pattern** — `pgrep -f X` matches its own siblings
- `timeout` is not installed — use `perl -e 'alarm N; exec @ARGV'`
- `_PRUNE_SAFE_TO_RUN` stays **False**. Do not arm the prune. **His call.**
- `d2r_owned` is **testimony** — only he may overrule his own ticks
- a gate never seen RED is measuring nothing · a SKIP is not a PASS · UNKNOWN is not clean
- **fix it, don't offer it** — in-territory, broken, and I know the fix → do it, report in past tense
