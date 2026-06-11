# HANDOFF_TO_DESKTOP — Audit 2026-06-12

> Generated on the **Windows clone** (consumer). The **Mac is the committer/deployer**.
> This is a checkpoint: the regression-suite audit. A deeper 5-agent audit
> (data / content / dead-code / routing / coverage) was IN PROGRESS when this was
> written — its findings will be appended as a follow-up section.

## TL;DR
Full Playwright suite (772 tests) on **v189 = GREEN. Zero real code bugs.**
Nothing code-wise to ship — v189 is already committed **and** live
(`bull-4-u.com/d2r/` byte-matches HEAD, the "Fanaticism floor roll" v189 marker is
present on live). This file is the audit record + test-hygiene notes.

## Suite result — full run (`--workers=3`, ~1.5h, Windows box, v189 / `5baf441`)
- **768 passed**, 1 skipped
- **1 "failed" — NOT a bug:** `tests/picks_count_diag.spec.ts` is a diagnostic with
  **zero `expect()` assertions**; it can only "fail" by hitting its 90s timeout under
  full-suite load. Its own logs show it working (`[countess] n=20 … [baal] n=20`).
  **Passes in 47.6s when run isolated.** Pure load/timeout flake.
- **2 flaky** (passed on retry), both environment, not code:
  - `tests/v114_mercenary_reference.spec.ts:88` — "no console errors …"
  - `tests/v136_routing_audit_lockdown.spec.ts:96` — "no console errors …"
  Both reds were transient network `net::ERR_INTERNET_DISCONNECTED` while loading
  external diablo2.io images (9× across the run). Not regressions.

## Test-hygiene candidates (optional cleanup — Mac's call, low priority)
1. **`picks_count_diag.spec.ts`** — no assertions + 90s timeout = a recurring CI
   false-positive. Recommend: `test.skip` it, delete it (it's a dev diagnostic), or
   convert its `console.log`s into real `expect()`s and bump the timeout.
2. **Network-flaky "no console errors" specs** — any spec that loads external
   diablo2.io art / aura GIFs and asserts zero console errors will intermittently red
   on a slow/offline link (v114 + v136 hit it this run; others share the pattern).
   Recommend route-blocking/stubbing external image requests in the test fixture.
3. **`v173_bind_banners_gallery.spec.ts` internal contradiction** — its header comment
   says the Desktop golden-merge **removed** `#binds-top-gallery` / `.btg-card` /
   `renderBindTopGallery`, but `bible.html` still contains them (×2 / ×9 / ×4) **and**
   the spec's own v186 tests (L128+) still drive those elements (they pass — the gallery
   still exists). Reconcile: either finish removing the old gallery or fix the stale
   comment so code/test/comment agree.

## Deploy state — no gap
- git HEAD = **v189 (`5baf441`)**; `origin/main` = same; **live = v189**. In sync.

## Verification notes
- The "regression suite is green" only certifies *tested* behavior. The 5-agent deep
  audit (in progress) targets the gaps: untested data-integrity / editorial / dead-code
  / routing issues. Follow-up section to come.
