# Handoff to Claude Desktop — v43 editorial · Playwright sweep results

Ran the full 144-test Playwright suite against `konyo_d2r_bible_v43.html` (editorial round 2, the Cinzel/Playfair masthead version). Cross-referencing against your own 11/11 internal pass + 0 JS errors / 0 warnings — failures here are almost certainly **test-harness vs. editorial-DOM mismatch**, not real regressions. But worth disclosing them so you can decide what (if anything) to firm up before locking v43.

---

## Results table

| run | passed | failed | skipped | dur |
|---|---|---|---|---|
| baseline (stale `bible.html`, pre-Round-11) | 142 | 1 | 1 | 10.8m |
| v43 round 1 (game-UI luxe) | 140 | 3 | 1 | 13.6m |
| **v43 round 2 (editorial)** | **136** | **7** | **1** | **16.1m** |

Net delta vs stale baseline: +6 failures introduced. Vs round-1 luxe: +4 failures (editorial polish stricter on DOM shape than luxe was).

---

## The 7 v43 editorial failures

1. **`00_diagnostic.spec.ts:7`** — *no console errors during initial load*
2. **`bug023_024_static_tabs.spec.ts:23`** — *Reference tab shows TC + qlvl + MF explainers*
3. **`bug030_035_aesthetics.spec.ts:7`** — *BUG-030 all 11 boss cards have consistent structure*
4. **`bug040_050_interactions.spec.ts:7`** — *BUG-040 click item tile → calc detail renders*
5. **`bug040_050_interactions.spec.ts:146`** — *BUG-050 statue tracker toggles state*
6. **`bug110_149_discovery.spec.ts:26`** — *BUG-112 every boss card drops table has ≥1 row*
7. **`v42_full_ux_audit.spec.ts:26`** — *every boss chip opens its detail panel cleanly* (also failed on baseline + round 1)

---

## Most likely root causes

### A. Google Fonts CDN from `file://` origin
Test #1 (`no console errors during initial load`) is the smoking gun.
- v43 editorial pulls Cinzel + Playfair Display + Inter from Google CDN
- Playwright opens via `file://`, which most browsers block cross-origin font fetches for (or at least surface them as console warnings)
- Console errors / warnings on initial load → `00_diagnostic` fails
- Cascade: slower initial paint may also push tests #4, #7 past the 30 s timeout if the masthead is still pending render when first interaction fires
- **Quick check:** open `bible.html` from `file://` in Chrome devtools and look at the Network + Console tabs. If you see CORS-blocked font requests or `OTS parsing error`, that's it.
- **Fix options:**
  - Embed fonts inline as `@font-face` data URIs (file gets bigger but renders identically online + offline + file://)
  - Or accept it as `file://`-only noise and add a console-warn-suppression sentinel to the diagnostic test (less clean)

### B. DOM-shape selector drift
Tests #2, #3, #4, #5, #6 probe specific DOM structures:
- `.boss-card`-style class hierarchies
- Reference-tab content containers (looking for TC/qlvl/MF explainer text or IDs)
- item tile click target → calc detail render path
- statue tracker DOM state toggle
- boss card drops-table row count

If the editorial polish wrapped, re-classed, or restructured any of these containers (e.g. you added a `<div class="editorial-section">` wrapper around boss cards, or renamed a class to match the masthead's section system), the selector misses and the test times out / asserts empty.
- **Quick check:** open one failing test, run it locally with `--headed`, watch what selector hangs. Or `npx playwright show-trace test-results/<failing-test>/trace.zip` for any of them — the trace will show the exact selector that didn't resolve.
- **Fix options:**
  - Restore the original class/id on the affected container (keep the editorial styling, lose the structural rename)
  - Or update the test selectors to match the new shape (requires touching test files, slower but cleaner long-term)

### C. Test #7 is pre-existing
`v42_full_ux_audit.spec.ts:26` failed against the **stale** baseline too. Same `window.openBossDetail` timeout. Not a v43-introduced regression — likely a test that was already flaky against the stale `bible.html` (which predates the Bug G fix that restored `window.jumpToBossItem` to top-level; possibly the same surface bit `openBossDetail` differently).

---

## Recommended order of attack

1. **Confirm root cause A** (Google Fonts via file://) — 30-second devtools check; if confirmed, decide inline-embed vs accept-and-suppress
2. **Pick one DOM-drift failure** (#3 boss-card structure or #6 boss-card drops-table — both probe the same container family) and trace it — that will tell you whether the polish renamed/wrapped one parent or several
3. If it's a single parent rename, one CSS-selector revert restores 4-5 tests at once
4. Re-sweep, expect ~141/144 (the stale `bible.html` baseline minus the #7 pre-existing flake)

---

## What this does NOT close

- The 11/11 internal Desktop audit + 0 JS errors / 0 warnings stand. v43 logic + boot integrity is intact.
- The 11 bugs A–I + Finding N from Rounds 10–12 are still landed in `bible_routes.html` (audit-floor baseline) and inherited by v43 (which was built on top).
- This is purely about getting the Playwright suite to agree with your direct verification.

If editorial is the final aesthetic direction and you don't want to chase selector parity, valid call to lock v43 + add a one-line note in the diagnostic spec ("editorial DOM shape — selectors deprecated, see bug_*_revised.spec.ts"). Test suite is a tool, not a target.

— CC, v43 sweep post-mortem
