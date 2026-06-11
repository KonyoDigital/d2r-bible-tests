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
  audit targets the gaps: untested data-integrity / editorial / dead-code / routing
  issues. See the deep-audit section below.

---

# DEEP AUDIT — 5-agent fan-out (appended 2026-06-12)

Five parallel READ-ONLY audit agents (data-integrity / content-editorial / dead-code /
routing / coverage) swept v189. The suite is green, so NONE of these are regressions —
they are pre-existing issues the suite never asserted. `[VERIFIED]` = the orchestrator
re-checked the exact source line directly. Data game-VALUE fixes are `[NEEDS KONYO]`
because the correct Reign-of-the-Warlock number needs a silospen repull / domain call —
the *inconsistency* is verified real, the *right value* is Konyo's.

## A. Real user-facing fixes (recommend fixing)

### Content / wording  — all [VERIFIED] vs the app's own ITEM_TIP / GAME_RULES
- **P1  `bible.html:6727`** Stormshield one-liner says `+35 cold res`, but the item's own
  ITEM_TIP (`:11953`) says **Cold Resist +60%**. Self-contradiction -> set 6727 to +60.
  Also re-check its `CBF` claim (ITEM_TIP shows no Cannot-Be-Frozen line).
- **P1  `bible.html:6808`** Coif of Glory says `+8% chance to cast Light Strike` —
  **"Light Strike" is not a D2 skill** (fabricated). Real stats: Hit Blinds Target +
  Attacker-Takes-Lightning-Dmg. Replace.
- **P2  `bible.html:3798`** Aura table uses **Hephasto** as the FIXED-aura example, but the
  app states his aura is RANDOM/always-Aura-Enchanted in >=5 places (3771/3972/3976/4116/
  4279). Swap example to Smith/Lister (Lister=Meditation is genuinely fixed).
- **P2  `bible.html:4280`** Worked example "Hephasto 88/8=11" contradicts the **mlvl 83**
  used in every table (83/8=10). Fix the example (or the table mlvl).
- **P2  `bible.html:3965`/`6299` vs `4279`** The Smith mlvl: tables say **78**, corrections
  note says **79**. Reconcile.
- **P3  `bible.html:7443`** [VERIFIED present] Heart of the Oak RUNEWORD_TIP has two stats
  mashed into one run-on (`...Against DemonsAdds 3-14 Cold Damage...`). Split into two.
- **P3  `bible.html:6711`** Griffon's Eye `+1 sorc skills` -> `+1 to All Skills`.
- **P3  `bible.html:6691`** `Bul-Kathos Wedding Band` ITEM_INFO label missing apostrophe
  (spelled correctly at 4440).

### Routing  — [VERIFIED]
- **P1  `bible.html:13845-14187` (`v42BuildCommands`)** Runes (33) and gems (35) have
  first-class clickable ID cards but are **NOT in the global-search index** — no RUNES/gem
  loop in the builder, and runes aren't in `ITEMS` either. Typing "Vex"/"Ber"/"Perfect
  Topaz" returns "No match" while every sibling entity is searchable. [VERIFIED: all
  `RUNES.map/forEach` hits are grid code (11xxx); none in the 13xxx search builder.]
  Fix: add two `cmds.push` loops over RUNES + the gem index, mirroring the colossal-jewel
  block.

### Data integrity  — inconsistency [VERIFIED real]; correct value [NEEDS KONYO / repull]
- **P1  BOSSES `baal` (`:6628`)** Baal is the only farmable boss whose norm==normTz and
  nm==nmTz gates (same mlvl+tcMax) yet **63 items differ in availability** between them
  (e.g. Vampire Gaze norm=null but normTz=1:18029). A TZ column at an identical gate must
  be a superset. Repull Baal's TZ columns.
- **P1  Key-rate triple-disagreement** Countess Key of Terror=**42%** (6628) vs Summoner/
  Nihl keys=**36%**; SPECIAL_DROPS.key (4769-71)=`~1:278/p3`; GAME_RULES=`Key of Hate 36%`.
  Pick one; also keys are Hell-/p3+-only but listed at full rate in norm/nm too.
- **P1  Essence-rate self-contradiction** SPECIAL_DROPS.essence (4746/48)=`~4% / 1:25` vs
  Essences hub (5109/17/23)=`~10-15% (~12%)`. Different order of magnitude — reconcile.
- **P2  SoJ ring mislabeled "TC block"** Jewelry is qlvl-gated, but SoJ carries tc=60 so its
  null cells (travincal/pindle/cows/pit Norm-TZ + pit NM) render a pink "TC block" label.
  countess NM (mlvl49/tc57) SoJ=1:15581 present, but pit NM at the *identical* gate=null.
  Set jewelry tc=0 (or skip TC-block label for rings) + repull missing ring cells.
- **P2  Tyrael's Might** (tc87/qlvl87, body armor = equipment = TC-gated): the qlvl=87 gate
  blocks pindle Hell(mlvl86)/cows/pit while nihl Hell(85) drops it. Drop the qlvl gate for
  TC87 equipment.
- **P2 (low)  Worldstone Shard** BOSSES=1:300 vs SPECIAL_DROPS=~1:500-1500. Align.
- **P3  COLOSSAL_STATUES `.ancient`** (5019-20) for the 2 boss-only statues is arbitrary
  filler (search keyword only).

## B. Test-hygiene (optional — prevents future false reds; this is what bit us tonight)
- `picks_count_diag.spec.ts` + `diag2.spec.ts`: zero `expect()` — diagnostics that can only
  "fail" by timeout (the "1 failed" tonight). Skip/delete or add real assertions.
- **15 "no console errors" specs load external diablo2.io art with NO network mocking** ->
  intermittently red offline (this caused tonight's 2 flakes, v114 + v136): v71_d2art,
  v73_tz_art, v76, v78, v111, v113, v116, v123, v124, v127, v135, v137, v139, v140, v170.
  Add a shared `page.route('**/diablo2.io/**', r => r.fulfill(1x1 png))` fixture.
- Brittle hard-coded counts that drift on the next data add: the **"13" boss-chips constant
  is duplicated across 8 specs**; 16 binds (v109); 312 items (v42); 36 recipes; 15
  hero-picks; 11 tabs. Derive from data or assert ranges.
- Coverage gaps (grep-confirmed 0 spec refs, all LIVE code): `runGicSim`, `runPuvSim`/
  `setPuvTrials` (the simulators — highest-value untested logic), `setHeroCount`/
  `setHeroDiversity`, `exportWishlistAsMarkdown`, `importGemTally`, `toggleStarred`,
  `setBossSort`.

## C. Cleanup (cosmetic, zero functional risk)
- **7 dead JS symbols** (0 callers, 0 test refs): `renderItemDesc` (10307), `renderClassRec`
  (10313), `renderActionPlan` (10329), `renderDiffCompareTable` (10646), `renderSourceStrip`
  (10882), `tzZoneArtBanner` (7097), `_origRenderHero` const (8965).
- **~50 lines dead CSS**, whole removed-feature blocks: "Tonight's Mission" (323-327, 438),
  sim-* (415-424), shard-* (234-243), q-unique/set/rune classes (133-135), tc-badge/tc-60..87
  (213-218).
- Inert `if(false)` keydown listener (12812-16).
- `v173_bind_banners_gallery.spec.ts:10-11, 67-70`: stale "binds-top-gallery was removed"
  comments contradict the still-live, still-tested feature (#binds-top-gallery:4161,
  renderBindTopGallery:6373, driven by the passing v186 tests). Fix the comments OR finish
  the removal.

## Recommended order for the Mac
1. Quick wins (1-line text fixes, [VERIFIED]): Stormshield, Coif of Glory, Hephasto x2,
   Smith mlvl, Heart of Oak split, Griffon's, Bul-Kathos.
2. Routing P1: add runes+gems to gsearch (small, high user value).
3. Data P1/P2: Baal TZ + Key/Essence rates + SoJ/Tyrael gating — needs a silospen repull /
   your RoW call before changing numbers.
4. Test-hygiene: mock diablo2.io art in the "no console errors" specs (kills the flakes),
   skip/assert the diagnostics.
5. Cleanup C: whenever; purely cosmetic.

Nothing above is auto-fixed — Windows clone is read-only here; the Mac commits + ships.

