# 🔤✨ UX + TYPOGRAPHY POLISH ARC — app-wide (Konyo standing directive, 2026-07-21)

**Status:** QUEUED — a dedicated 5-round Konyo-workflow arc (with Grok third-eye), to run AFTER/alongside
the 40-version Ninja-engine + Engine-Room flagship. Logged now so nothing is lost.

> Konyo: "all toggle-free. smooth, visually crisp, visually clear, understandable. PERFECT TYPOGRAPHY.
> the app needs some structuring — I didn't have a chance to get to it. tiny little fonts bigger; anything
> small while I'm in fullscreen needs to be optimized bigger, clearer, visually polished, rendering
> perfectly. Focus another 5 rounds specifically around this, workflow style with Grok."

## THE MANDATE (app-wide: bible.html + control_ui.html/TV·D)
1. **TOGGLE-FREE** — no toggles anywhere; one smooth shell, instant panes (the one-shell law, extended to
   every remaining toggle in the app).
2. **PERFECT TYPOGRAPHY** — one deliberate type system: scale, weight, tracking, rhythm. No accidental sizes,
   no mono-islands, no 9-10px whispers. Everything on the shared APP TYPE SCALE (already the source of truth
   in control_ui.html — extend the same discipline to bible.html).
3. **BIGGER SMALL FONTS, FULLSCREEN-OPTIMIZED** — anything tiny while Konyo is in FULLSCREEN must scale up:
   legible at his real viewing distance/resolution. Audit every surface at fullscreen widths; nothing dips
   below the readable app floor. Fullscreen is the primary viewing mode — optimize for it, not a small window.
4. **VISUALLY CRISP / CLEAR / UNDERSTANDABLE** — sharp rendering, clear hierarchy, self-evident meaning
   (pairs with the legends already shipped). No blur, no clutter, no clipped text; wide content scrolls in
   its own container, the page never scrolls sideways.
5. **STRUCTURING** — the app grew organically; give it deliberate structure/layout hierarchy so it reads as
   one designed product (Konyo hasn't had a pass at this — this arc is it).

## THE 5-ROUND ARC (Konyo-workflow, polish-ui-2 owns UI + a bible-copy/legend lane, Fable gates, Grok third-eye)
- **R1 — TYPOGRAPHY SYSTEM**: one type scale across bible.html + control_ui.html; kill every undersized font;
  fullscreen-first floor. Verify computed sizes ≥ target at fullscreen widths.
- **R2 — TOGGLE SWEEP**: find + remove every remaining toggle; smooth one-shell transitions everywhere.
- **R3 — FULLSCREEN OPTIMIZATION**: audit every surface at fullscreen; scale small UI up, crisp rendering,
  no clipping, no sideways scroll.
- **R4 — STRUCTURE + HIERARCHY**: deliberate layout structure, section rhythm, card language unified app-wide.
- **R5 — VISUAL POLISH + CONSISTENCY SWEEP**: color/contrast/spacing/state consistency, the whole app reads
  as one designed product; Grok third-eye pass on the before/after.

## GUARDRAILS
- Copy/CSS/layout only where possible — do NOT change logic, IDs, data, or test-pinned strings/structure
  (e.g. "legend renders 8 cards" — keep counts, improve the text/size). bible.html needs EDIT_LOCK.
- Every round green: test_control 43 · demo 7/7 · smoke on bible changes · closeability + 0.00px alignment
  invariants HELD · NEVER the full Playwright suite on the Mac.
- Fullscreen is the target viewport — verify at fullscreen widths, not just a small window.

_Queued behind the flagship. When the 40 land (or in parallel where non-colliding), this is the polish pass
that makes the whole console feel perfect._ 🔤✨
