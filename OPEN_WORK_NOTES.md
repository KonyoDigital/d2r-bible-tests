# ADDENDUM — measurements, optimizations, and notes worth not re-deriving

Everything below was measured or decided in this session. It is here so a fresh session does not
pay for it twice.

---

## 1. MEASUREMENTS — numbers that cost real time to establish

| what | value | how |
|---|---|---|
| Grok Bot live-console ticks parsed | **46** | split gh #180 comments on the tick header |
| …of which the visual pass was **SKIPPED** | **33 (72%)** | ten name my pre-push explicitly |
| his console CPU, at the freeze | **104.9%**, 17h uptime | `ps -r` |
| defunct children under his console | **12**, oldest **16.5h** | every other parent on the machine had ≤1 |
| orphaned `achilles-revival` processes | **24**, all PPID 1, spawned ~90s apart | and they **respawn** — see the two respawners |
| eagle rows total / not-ok | **32 / 11** | live `/api/status` |
| eagle `needsYou` (server) vs the panel's own count | **7 vs 9** | the gap is exactly `MINE` |
| the live shelf | **3,089 cards**, `filled:true` | live beat at v2434 |
| gates registered in `run_gates` | **66** | after adding `task-freshness` |
| the full local suite | **2,162 tests, 451.9s** | one pre-push run |
| beat fields the page sends | **6** (`hidden · view · els · panels · loaded · theatreOpen`) | comments stripped first |
| …published by `/api/status` | 76 keys; `els/loaded/theatreOpen` reachable under other names | `elsNow/elsHigh`, `panels.theatre` |
| reel directories on disk | **40** (not 641 — that count included `.DS_Store`, loose `.jpg`, `tooltip_crops`) | |

---

## 2. THE INSTRUMENT LIED FOUR TIMES, AND THE COUNT WAS ALWAYS THE TELL

Recorded because each one nearly became a wrong claim on the record.

1. **The beat-field scan found 4 of 6.** Every key sits behind a `/* */` note and my anchor required
   `,` or `{`, so `hidden` and `panels` vanished silently. **Strip comments before any key scan.**
   The guard now REFUSES below 6 fields — a scan that finds too little looks exactly like a clean
   codebase.
2. **Task 159 read as OPEN.** Grepping the doc for the old wording still hits — *inside the note
   recording the fix*. My own prose about a fix satisfying my own search for the bug. **Close on
   what a page ASSERTS, never on a grep count.**
3. **Five "pre-push processes" were my own waiter shells.** `until ! pgrep -f "hooks/pre-push"`
   matches its own siblings; the `[h]` trick only stops grep matching *itself*. **Wait on a PID
   (`kill -0 $PID`), never on a pattern.** Five deathless waiters were sitting on his machine.
4. **`/api/eagle` returned nothing parseable** and I did not retry — that endpoint runs a full sweep
   on his live console. Settled from source instead. **Do not poll `/api/eagle` to satisfy
   curiosity.**

---

## 3. FOUR TIMES I NEARLY FILED A DESIGNED REFUSAL AS A FAULT

The pattern: something measures TRUE and means something other than "broken".

- **`console UI faults` red** — reads *"the console healed itself from 1 fault in 24h"*. Its
  docstring argues the case: *"A fault that healed is still a fault — the point is that it stops
  being HIS job to notice"*, backed by his own *"watch dog it and eagle eye it"*. **The docstring is
  an argument. Read it as one before treating it as an obstacle.**
- **`TERROR ZONE — Failed to fetch`** — the cross-family eye named it the worst thing on screen.
  True on the pixels, and expected: the render harness has no network. **Not filed.** Whether it
  also shows on his LIVE console is a separate, real, unanswered question.
- **Three panels at `OFF-VIEW H=0`** — that is `getClientRects().length === 0`, i.e. a tab he is not
  looking at. Healthy.
- **The 355px `.lab` truncation** and the **14-card history teaser** — both argued decisions with a
  `title` as the way back.

---

## 4. OPTIMIZATIONS IDENTIFIED (not yet done)

- **Batch 3–4 versions per push.** The gate is ~452s and the cost is *per push*, not per version.
  And every extra push is a Grok Bot visual look that does not happen (72% skip rate above). This is
  the single highest-leverage process change available.
- **The watch could publish its skip reason as a counter the eagle reads**, so *"the visual lane has
  been starved N ticks running"* is visible instead of needing someone to count comments by hand.
  Today nobody could see it but me, after the fact.
- **`/api/eagle` should publish the partition, not raw rows** — done in the working tree; the panel
  now reads `needsYou/mine/mineWhat/unknown` instead of re-deriving. **Still owes a guard.**
- **The eagle needs a WHAT-KIND axis beside its WHOSE axis.** `MINE` separates my defects from his.
  Nothing separates *a system failing* from *a system working* (healed) or *a system unproven*
  (never asked). `needsYou: 7` is inflated by rows he cannot act on. ⚠ Adding a 4th `state` string
  is the WRONG fix — two UI branches render anything non-`missing` as UNKNOWN, and `console_healer`
  keys off `state == "missing"` to decide what to heal. Add a separate `kind` field, exactly how
  `MINE` already works.
- **His console leaks zombies** — 12 defunct children never reaped. Real, located, unfiled.

---

## 5. DESIGN DECISIONS MADE, WITH THEIR REASONS

- **`tasks_freshness` fingerprints rather than edits.** Editing the four stale rows fixes today and
  drifts next ship; keeping the list current by *remembering* is exactly what failed for 34
  versions. A row carries the string whose PRESENCE means the work is undone.
  ⚠ A row with **no** fingerprint reports **UNKNOWN every run** — never rounded up to clean.
- **The beat guard pins the LAW, not the word `view`.** *Every field the page beats must reach a
  supervisor or be declared with the name it comes out under.* Pinning `view` would not catch the
  next dropped field. It also has a companion test asserting `view` specifically, because the law
  alone would pass if someone deleted the field from the page instead of publishing it.
- **`uiBeat.view` is honest-absent.** `None` = nobody could ask · `''` = the page answered and body
  carries no `data-view`. `or None` would collapse two opposite facts into one.
- **The panel's fallback SAYS SO.** When `/api/eagle` ships no partition, the panel counts locally
  **and prints "(this console cannot split mine from yours)"** rather than passing a
  differently-computed number off as the server's answer.

---

## 6. PROCESS NOTES

- **v2435 is committed (`b755a485`) and NOT on origin.** The gate refused it for a real defect in my
  own new file — `tasks_freshness.py` printed 🔴🟢⚪ without `console_safe.enable()`, so a non-UTF-8
  console would crash *while reporting*. Already fixed in the tree. **Next action: bump v2436,
  commit, push once.**
- **The second-eye ledger is UNTRACKED**, so the cross-family debt is local-only and CI cannot see
  it. Existing design; worth deciding on deliberately.
- **v2434's cross-family look is PAID** — recorded LOOKED with findings, so the ledger will not
  block the next push.
- **The render harness reported `1 target UNKNOWN — the browser went away mid-render`** on the last
  gate run. A skip is not a pass; it did not block, but it means one target was not established.
