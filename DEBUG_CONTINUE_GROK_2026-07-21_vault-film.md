# 🛰 CONTINUE + DEBUG for SuperGrok — 2026-07-21 (Fable vision handoff)

_Fable at context limit; leaving this for Grok. Konyo's live session + a 58s screen recording
cross-referenced with my own vision. Two linked bugs, root cause PROVEN. Do NOT touch the LOCKED
vault intake reader without Konyo's explicit OK — the fix is likely upstream (what frame/flow feeds it)._

## Shipped this arc (all on main, green, smoke-gated)
- v946 lease-key fix (vault dual-fire cross-block) · v946.1/.2 Grok (end-session unstick, tab identity)
- v946.3 VAULT NEVER-ZERO — vault errors now re-fire vs silently 0 (engages live: driver refire>0)
- v946.4 Screen-Recording popup killed (only opens when grant ACTUALLY missing, not when D2R closed)
- v946.5 SOCKET CAPTURE (prompt p831 → parse → journal → pack beat; Diadem reads {Diadem:3})
- v946.6 socket render (⏣N pill in theatre caption/drawer/lightbox)

## ✅ SUPERGROK RETURN — v946.7 (vault grid gate + film truth)

### BUG A — FIXED (upstream of locked reader)
**Decision (Fable option b, with Konyo intent):** do **not** auto-fire `vaultIntake` on a raw
personal/shared **icon grid**. That reader needs tooltip text (manual photo flow).

| Change | Where |
|--------|--------|
| `_vault_names_worth_auto(names)` | real item text only; reject `'Ii'` / empty |
| Engine driver | queues `vault_*` **only** when deep has worth names; else skip (visit open for later tooltip) |
| Vault re-fire | grid jobs (`has_names=false`) **give up** immediately — no thrash |
| Board `tvVaultAutoIntake` | same name gate (EDIT_LOCK) |
| KAI Stage-3 vault | **default OFF** (`TV_KAI_VAULT=0`); opt-in only for tooltip reels |

Locked `vaultIntake` **untouched**.

### BUG B — FILM vs READS (cross-ref done)
Session `s_1784621819814` / reel `reel_s_1784621819814_13252`:

| Fact | Number |
|------|--------|
| Film frames | **82** over ~81s (~1 fps continuous) |
| Film gaps >1.5s | **1** only |
| Deep reads | 6 (3 real names: Gheed's / Ring of Maiming / War Traveler) |
| Journal "skip text-eye" | 10 — these are **trigger ticks** (text-eye enqueued), not dropped film |
| Vault personal frame | `2_1784621850691.jpg` full of icons, vault still 0 — proves grid, not missing photo |

**Conclusion:** Screenshots **are on the reel**. What was "missing" is **named AI beats** for every hover —
settle/deep only lands some tooltips; film still has the pixels. Theatre **📁 film** opens the folder;
scrub **⏱ REAL** to see every `f_*.jpg`. Registration still requires a successful deep name (and
vault identities still require manual tooltip photo or future count-reader — not this patch).

### Verify
`test_control` · `test_agent` · `test_routes` (+vault gate pins) · `demo_console` 7/7 · stamps v946.7

---

## 🔴 BUG A — VAULT (personal/shared) intake ALWAYS reads 0 (root cause PROVEN)
Live session s_1784621819814: runes tallied 405 ✓, but personal=0 ERROR and shared=0 ERROR (×2).
The v946.3 re-fire ENGAGED (driver refire counter climbed) but every attempt still read 0.
**I pulled the exact frame vaultIntake fired on (`tv/frames/hist/2_1784621850691.jpg`) and LOOKED:**
the PERSONAL tab is wide open and FULL — 9 grand/large charms, ~a dozen rings/amulets/jewels, boots,
a tome. 20+ items, crisp full-res. Receipt: `{ok:false,total:0,items:[],errors:0}` — read NOTHING.
**Root cause (video frame v_03 confirms): the personal/shared stash tabs are ICON GRIDS. The vault
AI reader returns "no readable item text (honest empty)" / "personal MISS" — it's built for Konyo's
MANUAL photo-upload flow (hover each item → tooltip text), NOT a raw icon grid.** OCR on the grid
returns garbage ("IA Lla", "Ii"). Contrast: runeIntake/gemIntake/materialIntake work because they
COUNT icons; vaultIntake tries to READ item identities from icons and can't.
**Grok's fix options (upstream of the locked reader):**
1. The driver should NOT auto-fire vaultIntake on a raw personal/shared GRID frame — it has no
   per-item text. Either (a) skip vault auto-intake entirely (keep it manual, honest), or (b) feed
   it only frames where an item TOOLTIP is up (like the tooltip→judge path), or (c) give personal/
   shared a COUNT-style reader like the tally tabs if the goal is "N items present," not identities.
2. If vault MUST read identities, that's the manual photo flow — the auto-path can't substitute.
**→ SuperGrok chose (b): only auto when deep has real names; else skip.**

## 🔴 BUG B — captures/reads missing from the FILM reel + not registered (Konyo's words)
Konyo recorded 58s from ON AIR (11:17:26). He hovered MANY items; the console LIVE EYE was visibly
"thinking/reading". But only **3 reads journaled** (Gheed's Fortune GC, Ring of Maiming, War Traveler)
+ the tally intakes. He wants those exact item captures RENDERED in the theatre film — they're missing.
**SuperGrok cross-ref:** reel has **82 frames**, continuous ~1fps — film is NOT empty. Missing piece is
**per-hover deep registration**, not missing JPEGs. Use Theatre 📁 film + REAL mode to scrub all stills.

## Method / artifacts for Grok
- Video frames extracted to scratchpad `vidframes/v_01..07.jpg` (fps 1/8) — v_03 shows the smoking gun.
- Reel: `tv/frames/hist/reel_s_1784621819814_13252/` (82 f_*.jpg).
- Journal: session s_1784621819814 → 3 deep reads + intakes [personal 0F, runes 405T, shared 0F ×2].
- The perfect-but-unread vault frame: `tv/frames/hist/2_1784621850691.jpg` (Fable viewed it).
- Verify battery unchanged: test_control 43 · test_agent · test_routes · demo 7/7 · NEVER the full Playwright suite on the Mac.
