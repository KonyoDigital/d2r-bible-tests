# HANDOFF → WINDOWS: full-suite backstop owed (v199 → v207)

Mac shipped NINE versions on fast targeted gates only (per the new protocol:
Mac ships, Windows backtests). All are pushed AND live. Run the FULL suite on
v207 (`b4996be`) and report (commit a follow-up section here, or relay).

## What shipped since the last backstop (v198 = last full-green on Mac)
- v199 per-boss AURA READ boxes (binds cards)
- v200 The Smith full bind layer (Stone Skin = 75% NOT immune)
- v201 footer signature (sources line + dev-notes blob removed; erase kept)
- v202 keyboard truth: B global, 9/0 tab keys, palette hints fixed, help rewrite
- v203 THE VAULT mule manager (Tools centerpiece)
- v204 mule ID cards (in-game stash/inventory replica + packer)
- v205 📸 AI intake (functions/api/intake.js Pages Function + page UI)  ⚠ NEW: deploys must include functions/
- v206 replica: inventory always visible, bigger cells
- v207 replica: in-game two-panel layout, responsive cells

## Run
nice playwright test --workers=3  (or whatever the box likes)
Suite size ≈ 815+ tests. Known-flaky-class already net-stubbed (18 specs use
tests/_net_stub.ts). New specs: v199(3) v200(in v199 file) v202(4) v203(7)
v204(4) v205(3, endpoint mocked via d2r_intakeUrl override).

## If red
Re-run the failing spec in isolation first (tail-fatigue rule). Real reds:
push findings here; Mac fixes + re-ships.
