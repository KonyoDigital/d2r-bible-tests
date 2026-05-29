# HANDOFF → Desktop Claude — Top Drops feature shipped, visual polish pending

**From:** CC (terminal) · **Date:** 2026-05-30
**File md5 (all 3 copies in sync):** `c933c3ad3bf888c2404414fec3a538eb`

## What CC shipped (functional — done, tested, committed)
New per-boss **"🏆 Holy Grail — Top Drops"** section in the boss detail card
(`renderBossCards`, bible.html ~line 4567+):
- Curated list of the boss's **grail/uber** items, ranked **rarest-first** by
  best-achievable MF-adjusted odds (top 20). Per Konyo's explicit choice.
- The full ~300-item table is now wrapped in a collapsed
  `<details class="all-drops-details">` dropdown ("Show all N droppable items").
- Rows are clickable → `navigateToItem()` into the calculator.
- Data (`BOSSES`) untouched → 312 items / 11 chips / all L-integrity drop probes
  unchanged. 0 JS errors. New spec `tests/top_drops_per_boss.spec.ts` (4/4 green).

## IMPORTANT — I already incorporated your boss-card typography
Your **uncommitted** Desktop-copy edit (`.boss-name → Cinzel`,
`.boss-subtitle → Playfair italic`, color/size/margin tweaks) was the +71-byte
delta on the Desktop copy only. I adopted the Desktop copy as the canonical base
before building, so **that typography is now baked into all 3 copies + my commit.**
➜ **Do NOT re-commit it** — it's already shipped. Verify-render is still owed (below).

## Visual polish still owed (your lane)
1. **Verify boss-card typography renders** — you never screenshotted the
   Cinzel-name / Playfair-italic-subtitle change. Confirm on the bosses landing
   tab (The Countess / Andariel), 0 JS errors, BUG-031 + BUG-033 still green.
2. **Style the new `.top-drops` section** to the editorial system. I gave it
   functional CSS using existing tokens (near the `.owned-btn` block):
   `.top-drops-title`, `.top-drops-sub`, `.top-drops-list`, `.top-drop-row`
   (CSS grid: rank | name | odds | hours), `.top-drop-uber`, `.top-drop-verified`,
   `.all-drops-summary`. It's clean but plain — give the title the Cinzel
   treatment, refine the row chrome / hover, and harmonize the `<summary>` with
   the rest of the editorial language.
3. The `<summary>` uses a `▸` marker; `list-style:none` is set. Confirm it reads
   well across tabs and on mobile (narrow grid columns may want a breakpoint).

## Coordination
- CC owns test files; you stay on visuals — unchanged.
- Two prior polish commits (h2→Cinzel `83d3d07`, Inter `e52a5f4`) + this feature
  commit are going to origin in CC's push (CI shard-3 timeout fix already landed).
