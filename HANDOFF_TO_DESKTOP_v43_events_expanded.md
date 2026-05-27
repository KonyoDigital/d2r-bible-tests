# Handoff to Claude Desktop — v43 events-expanded · verified ship-clean

Verified your expanded Events tab additions (Uber Tristram + Diablo Clone + Cow Level + Colossal Ancients) against the locked regression suite. **19/19 pass in 1.9m.** Logic intact, all 11 audit-floor bug fixes (A-I + Finding N) still hold.

---

## Verified file

```
/Users/konyo/Downloads/konyo_d2r_bible_v43.html  md5 9eef86b3a9afbf775c0b1a0c532ed409  876,105 bytes
/Users/konyo/d2r_bible_tests/bible.html          md5 9eef86b3a9afbf775c0b1a0c532ed409  (mirror in sync)
```

Up from the v43-editorial lock md5 `31c27f2d...` (855,885 bytes) by ~20 KB — events tab content.

---

## Test results

**workers=1, 19-test focused sweep:**

| spec | passed | duration |
|---|---|---|
| `01_smoke.spec.ts` (8 tests) | 8/8 ✓ | — |
| `v43_editorial_audit.spec.ts` (11 tests) | 11/11 ✓ | — |
| **total** | **19/19** | **1.9m** |

All 11 editorial regression probes green:
- boot integrity (312 items + 11 boss chips) ✓
- editorial masthead ✓
- navigateToItem syncs active-item-bar ✓
- Bug D (palette action → navigateToItem) ✓
- Bug H (setActiveBoss intent disambiguation) ✓
- Bug E (goBackFromAid no null.bossId) ✓
- localStorage corruption recovery ✓
- Finding N (stale wishlist sanitization) ✓
- keyboard shortcuts 1-7 ✓
- memory: 30× boss detail no DOM growth ✓
- Bug I (_v41_refreshStatus script tag cleanup) ✓

---

## Earlier workers=2 noise (the 4 fails you saw) — all harness, not regressions

Re-checked each failing test in isolation:

| failing test | workers=2 result | isolation result | verdict |
|---|---|---|---|
| `01_smoke:35` 11 boss cards consistent structure | ❌ 3/3 with `--repeat-each=3` | ✅ 7.3s workers=1 | worker-contention race |
| `v43_editorial:39` navigateToItem syncs active-item-bar | ❌ | ✅ 9.5s | tail-flake |
| `v43_editorial:55` palette navigateToItem (Bug D) | ❌ | ✅ 10.6s | tail-flake |
| `v43_editorial:153` 30× boss-detail memory probe | ❌ | ✅ 21.6s | tail-flake |

Headless DOM probe via Playwright confirmed all 11 boss IDs render with `.boss-name` populated at the 600ms wait point in `bible_routes.html` (unchanged since `ae5f206`). The cows-card failure was Playwright worker-isolation friction, not a DOM regression.

This joins the known set from the LOCK doc:
- workers=2 recovers ~5 tail-fatigue fails vs workers=1
- workers=2 trades them for ~3-4 worker-isolation races on selector-timing-sensitive tests
- Net: workers=2 is still the better default for full sweeps (-2 fails, -6 min), but the workers=1 focused-19 sweep is the **definitive ship signal**

---

## Recommended commit strategy

The events-tab changes in `bible.html` (test mirror) are uncommitted. v43-editorial tag points at the lock md5 `31c27f2d...`. Two clean paths:

**Path A — new commit on main, no retag** (lighter weight):
```
git add bible.html
git commit -m "feat: expand Events tab — Uber Tristram + Diablo Clone + Cow Level + Colossal Ancients"
git push
```
v43-editorial tag stays at the original lock; events expansion lives on main as the working head.

**Path B — new commit + new tag `v43-events`** (matches semantic):
```
git add bible.html
git commit -m "feat: expand Events tab with 4 endgame events"
git tag v43-events
git push && git push --tags
```
Recovery point per event-addition cycle. Slightly heavier but matches your tag-per-ship rhythm.

I'd lean **Path B** — you set the v43-editorial tag precedent that ship-cleans get tagged; events expansion is its own ship.

---

## Production file ahead of tag

Note: the production `~/Downloads/konyo_d2r_bible_v43.html` (md5 `9eef86b3...`) is already ahead of the committed `v43-editorial` tag (md5 `31c27f2d...`). Whatever path you pick, the commit should land the events-expanded file into the repo so source-of-truth matches what Konyo's actually using.

---

— CC, events-expanded verification post (workers=1 isolation = ship signal)
