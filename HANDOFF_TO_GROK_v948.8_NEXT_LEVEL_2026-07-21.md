# 🚀 NEXT-LEVEL ARC → SuperGrok (from Fable, near context limit)

Konyo: "take it to the next level, Konyo-Workflow rounds with SuperGrok, ship 10+ versions."
Fable landed v948.7 (verified green, pushed, /api/kai_reclose confirmed working, reel re-close
queued). Fable is context-capped (resets 19:00) — Grok runs the engine rounds, Fable gates on
return. Below is the prioritized next-level work + what Fable already checked so you don't redo it.

## VERIFIED THIS SESSION (don't re-investigate)
- ✅ Socket capture LIVE: Spirit Monarch ⏣4, Obsession ⏣6 (v946.5/.6 solid)
- ✅ Vault grid-count LIVE: shared COUNT=25 (v947.2 — the vault-0 saga is fixed)
- ✅ End-session unstick, Screen-Recording popup killed, vault never-zero re-fire — all live
- ✅ v948.7 retro reel recheck + /api/kai_reclose shipped green
- ℹ️ Grail gate promoting runewords ("Spirit → grail") is INTENTIONAL (never-toss a runeword);
  the LABEL is imprecise but behavior is correct. If Konyo wants a distinct "runeword" tier
  (vs "grail"), that's a cosmetic tier-label split — confirm with him first.

## PRIORITY ROUNDS (ship version-per-round, Fable gates each)
1. **Materials retro audit** (the v948.7 reclose is running on reel s_1784636825977_40909):
   inspect kai_report kaiVer>=3 + routing. If materials pixels exist on film but still 0 →
   fix classify_stash_grid materials branch (dark+chroma band) in tv/stash_eye.py. If film never
   showed materials → honest-zero, document it. THIS is the open thread from the handoff.
2. **Runes 0-error recovery** (seen live this session): confirm the never-zero re-fire actually
   RECOVERS a runes 0 to a real count on a fresh frame (it engaged on vault; verify on runes).
3. **Film/registration completeness**: Konyo's standing ask — every hovered item Konyo sees should
   produce a read + reel frame. Cross-ref a session's reel count vs read count; find dropped hovers.
4. **Next-level polish** (UI = polish-ui-2's lane, control_ui.html): socket pill everywhere,
   grid-count surfaced in the vault/tally overlay, theatre stamp-ledger polish, closeability held.

## GUARDRAILS (Konyo's locks — do not cross)
- Do NOT change gem/rune/material CROP FRACTIONS in functions/api/intake.js without Konyo.
- Do NOT touch the LOCKED vaultIntake IDENTITY reader (grid-count is the additive path).
- Subscription intake only (TV_INTAKE_LOCAL=1). NEVER run the full Playwright suite on the Mac.
- Every ship: stamps ×3 parity, floor green (test_control/test_routes/test_agent/demo 7/7),
  bible change → smoke gate. Fable gates + pushes on return.

## Resume line
> Read this. Run the materials retro audit first (reclose result on s_1784636825977_40909), then
> rounds 2-4. Ship version-per-round; hand each back for Fable's gate. Konyo Workflow, 10+ versions.
