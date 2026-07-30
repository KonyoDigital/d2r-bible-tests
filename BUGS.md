# v21_kai → v21_kai_fixed bug tracker

## Strategy
- Side branch: `/Users/konyo/Downloads/konyo_d2r_bible_v21_kai.html`
- Test bench: `/Users/konyo/d2r_bible_tests/bible.html` (copy)
- TDD: write Playwright test → confirm fail → patch → confirm pass
- Vanilla HTML/CSS/JS preserved (no React migration)

## P0 — render crashes
- [x] BUG-001 `renderBossCards()` line 1623: `r50.toLocaleString()` crashes when `runsFor()` returns null. Kills 11 boss cards + cascades to TZ/Runes/RotW.

## P1 — missing universal boss detail page (user explicit ask)
- [x] BUG-010 Universal boss detail panel — overlay, 6-diff grid, top-12 drops, esc/× close ✓ 9/9 tests
- [x] BUG-011 Boss-nav chip click → smooth-scroll + flash header + flash chip ✓
- [x] BUG-012 Boss-card header clickable → opens universal detail ✓
- [x] BUG-013 TZ-zone card click → boss detail (11 zone→boss mappings) ✓
- [x] BUG-014 Cmd/Ctrl+click on calc source-chip → boss detail (plain click preserved) ✓

## P1 — subtab rendering (CASCADE CLEARED by BUG-001 fix)
- [x] BUG-020 TZ tab: zones rendered count (8+ zones ✓)
- [x] BUG-021 Runes tab: rune table rendered (10+ rows ✓)
- [x] BUG-022 RotW tab: shards/statues/essences/sunders/sets all render (7 sets, 5 statues ✓)
- [x] BUG-023 Ancients tab: full mechanics card (Talic/Korlic/Madawc + 4 stats) ✓
- [x] BUG-024 Reference tab: TC + qlvl explainer + MF math ✓

## P2 — UX/aesthetics
- [ ] BUG-030 Boss-card visual consistency across all 11 cards
- [ ] BUG-031 Section header typography (uppercase mono, gold divider)
- [ ] BUG-032 Color contrast on blocked cells (orange qlvl, pink TC)
- [ ] BUG-033 Hover/focus states on every interactive element
- [ ] BUG-034 Mobile responsive layout
- [ ] BUG-035 Compare-difficulty table styling

## P2 — interaction tests (each click verified)
- [ ] BUG-040 Click any item tile → calc detail renders
- [ ] BUG-041 Click any source chip → bosses tab + correct boss + correct diff
- [ ] BUG-042 Star/unstar item persists to localStorage
- [ ] BUG-043 Mark owned/unowned persists to localStorage
- [ ] BUG-044 MF slider live-updates all cells
- [ ] BUG-045 Player slider live-updates
- [ ] BUG-046 Search counter updates on filter
- [ ] BUG-047 Filter pills (all/grail/uber/tc87/etc) work
- [ ] BUG-048 Sort by column (boss card tables)
- [ ] BUG-049 Keyboard shortcuts (/, ?, 1-7, Esc, B)
- [ ] BUG-050 Statue tracker click toggles

## P2 — data integrity
- [ ] BUG-060 All 312 items present in calc
- [ ] BUG-061 Verified anchors (🔒) intact
- [ ] BUG-062 Nagelring searchable
- [ ] BUG-063 Mephisto TC78 cap blocks Tyrael's etc.
- [ ] BUG-064 Pindle mlvl 86 blocks qlvl 87 items

## P3 — polish
> ⚠️ 2026-07-15: this May-era checklist is SUPERSEDED by the verified list further down — kept for history; the bottom section is the truth.
- [x] BUG-100 (see verified list below) Hero card 5 picks update on MF change
- [x] BUG-101 Tonight's Mission appears when wishlist > 0 — **FINISHED by v688 ⚔️ Task Force**: the Mission Brief auto-resolves (pin > make-now > one-step > pipeline > wishlist > darkest wall corner); verified live 2026-07-15
- [x] BUG-102 (see below) Grail progress dial animates correctly
- [~] BUG-103 Drop simulator runs N trials — **RETIRED 2026-07-15**: superseded by the real-odds EV engine (funiScan best-runs: expected-yield per run at live MF/P#); a Monte-Carlo toy adds noise, not information
- [x] BUG-104 (see below) Set tracker pieces check off
- [x] BUG-105 (see below) Cube recipes render
- [x] BUG-106 Help modal (?) opens/closes — **FINISHED** (the ? FAB opens #help-modal, click-away closes; verified headless 2026-07-15)
- [x] BUG-107 (see below) Reset data button confirms + clears localStorage

## P2 — UX/aesthetics ✅ ALL SHIPPED
- [x] BUG-030 Boss-card visual consistency (11 cards: header, emoji, name, tier-tag, body) ✓
- [x] BUG-031 Section header typography (uppercase + gold rgb dominant) ✓
- [x] BUG-032 Color contrast on blocked cells ✓
- [x] BUG-033 Hover/focus states present (boss-header.clickable:hover CSS rule) ✓
- [x] BUG-034 Mobile responsive layout (375px, no h-overflow) ✓
- [x] BUG-035 Compare-difficulty grid renders per boss ✓ (+035b detail card mobile width)

## P2 — interactions ✅ ALL SHIPPED
- [x] BUG-040 item tile → calc detail
- [x] BUG-041 source-chip → bosses tab
- [x] BUG-042 star persists `d2r_wishlist`
- [x] BUG-043 owned persists `d2r_owned`
- [x] BUG-044 MF slider live update
- [x] BUG-045 Players slider live update
- [x] BUG-046 search counter filters
- [x] BUG-047 filter pill "grail" filters
- [x] BUG-048 sort column toggle direction class
- [x] BUG-049 kbd "/" focuses search
- [x] BUG-049b Esc clears active item
- [x] BUG-050 statue tracker toggles

## P2 — data integrity ✅ ALL SHIPPED
- [x] BUG-060 312 items in calc grid ✓
- [x] BUG-061 verified anchors in Ref tab ✓
- [x] BUG-062 Nagelring searchable ✓
- [x] BUG-063 Mephisto Hell TC≤78 ✓
- [x] BUG-064 Pindle Hell mlvl 86 ✓

## P3 — polish (5 of 8)
- [x] BUG-100 hero card renders
- [x] BUG-101 Tonight's Mission — Task Force Mission Brief (v688), see above
- [x] BUG-102 grail progress dial exists
- [~] BUG-103 drop simulator — retired, superseded by best-runs EV
- [x] BUG-104 set tracker ≥7 sets
- [x] BUG-105 cube recipes in rotw/ref/runes
- [x] BUG-106 help (?) modal — present + working (was marked absent in the old sweep)
- [x] BUG-107 reset button attached

## Discovery sweep 1 ✅ ALL SHIPPED (BUG-110..124)
- [x] BUG-110 rune table ≥10 rows
- [x] BUG-111 every boss has 6 diff columns
- [x] BUG-112 every boss has ≥1 drop row
- [x] BUG-113 search clear restores grid
- [x] BUG-114 set-piece toggle adds class
- [x] BUG-115 MF math 54.5% @ MF300
- [x] BUG-116 reset confirms (no auto-clear)
- [x] BUG-117 hero updates with MF
- [x] BUG-118 filter "all" reset
- [x] BUG-119 sort persists across re-renders
- [x] BUG-120 all 11 detail open w/o error
- [x] BUG-121 11 boss-nav chips
- [x] BUG-122 TZ ≥10 zones
- [x] BUG-123 RotW ≥5 statues
- [x] BUG-124 detail re-opens for different boss

## Status — 2026-05-26
**56/150 bugs shipped. 73 tests passing, 1 skipped, 0 failing.**
Snapshot: `/Users/konyo/Downloads/konyo_d2r_bible_v21_kai_fixed.html` (614 KB)
Next session: BUG-125+ visual regression, feature audits for 101/103/106.

## Status — 2026-05-26 17:10 — ROUTE-AUDIT lane (second version)
Konyo split work: Claude Desktop = visuals/features (v23/v24), Claude Code = routes/backend/symmetry (no visuals).
- Branch: `/Users/konyo/d2r_bible_tests/bible_routes.html` (fork of v21_kai_fixed)
- Ship: `/Users/konyo/Downloads/konyo_d2r_bible_v23_routes.html` (614 KB)
- New suite: `tests/route_audit_v23r.spec.ts` — **24/24 GREEN**
  - 7/7 sub-tabs render content (bosses, calc, tz, runes, rotw, ancients, ref)
  - 11 boss-nav chips + 11 detail openings + Esc close
  - 11 boss-cards × 6 diffs × ≥1 drop row symmetry
  - TZ→boss routing, calc tile→detail, source-chip plain & Cmd+click routing
  - MF/Players sliders no errors; overlay switch ≠ stack
- Total project tests: **97 passing** (73 original + 24 route-audit), 1 skipped, 0 failing

---

# Regression log (post-ship breakages caught by CI)

> **Companion docs (cross-referenced):** `GAME_RULES.md` (durable RoW game-truth +
> drop-odds provenance) · `BUILD_LOG.md` (dated ship/decision log + key invariants).
> Append every post-ship breakage here as `REG-NNN`.

Format: what broke · how it was caught · root cause · fix · prevention.

## REG-015 — 2026-07-09 · LOCKDOWN sweep: 20+ audited desyncs across Forge/Tools (multi-agent army, v613-v621)

- **Symptom (user-caught trio)**: sparkles fired on dead UI; creating Pattern left the Katar in the
  vault; Double Bow/Elegant Blade wore false FORGED seals (REG-014's class, wider).
- **Caught by**: two multi-agent audit workflows (39 + 22 agents) + adversarial verifiers, plus
  Konyo's live reports. CONFIRMED highs: seed-floor purged explicit un-marks on reload (the ↺ lie);
  runeCraftStatus alias lookup leaked made words into 'ready now' forever; the SI hero CTA dead-ended
  on a collapsed card; THREE formulas shipped under one '⚒ Make now' label; consume-sync searched only
  planner tasks with live bases (farm-bucket words consumed nothing — the Katar); _isIdealBase
  substring match let a plain Pike impersonate 'War Pike'; v603.1/v387/v385 exclusions trusted
  understated BASE_DB weapon maxes; Exile→Monarch art home (class-illegal); superior rule skipped
  review surfaces; eth-strip drift; '(Nos low base)' labels planner-invisible as phantom Larzuk
  candidates.
- **Fix**: v613 (factual clickability predicate) · v614 (trusted-max doctrine + game-rule batch) ·
  v615 (consume fallback chain + Chronicle fan-out consolidation + 66-word live seed) · v616
  (class-restriction full-catalog invariant — in the smoke gate) · v617 (SI flagship + honest counts)
  · v618 (hero one-click + first-forge epic) · v619 (grail-forge found-sync + seals) · v620 (tally
  flagship) · v621 (end-to-end journey sim).
- **Prevention**: trusted-vs-advice data doctrine everywhere; ONE fan-out (_rwChronicleChanged);
  consume narrates every outcome; invariant specs in the pre-push gate (v604 coverage, v616 class
  rules); the v621 journey sim locks the whole arc as a rendered-UI demo.

## REG-014 — 2026-07-07 · v562 empty exact-fit list read as "✓ forged" → 1os Suwayyah hid the unmade Pattern (live, user-caught)

- **Symptom**: Throw-Out Review said a 1os Suwayyah's "runewords are ✓ forged or belong
  in endgame bases → safe to throw out" while Pattern (the 3os claw word, Suwayyah = its
  endgame base) was NEVER created. Same card also offered "Larzuk → 3 sockets" — impossible
  on an already-socketed item. And the ⚒ FORGED stamp fired on "all N that fit THIS count"
  (Grim Scythe 4os, Small Crescent 3os) even when the base type had other-count words open.
- **Caught by**: Konyo, live screenshot 2026-07-07 ("big bug… it's supposed to recommend
  Pattern, I still didn't create it").
- **Root cause**: `_baseUnmadeRunewords(base, ks)` with a known socket count keeps ONLY
  exact-fit words (v376/v389 rule — correct), but every consumer treated the resulting
  EMPTY list as "everything is forged". Unmade words filtered out by the socket mismatch
  (Pattern s=3 vs ks=1) were indistinguishable from actually-created ones. The FORGED
  stamp had the same blind spot (gated per-count, not per-base-type), and the Larzuk/cube
  socket guide rendered unconditionally on socketed copies.
- **Fix (v602, `fca6914`)**: new `_baseUnmadeWrongSock(base, ks)` = the unmade words at
  OTHER counts. All 3 empty-list verdicts (throw-out card + 2 suggestMule paths) now say
  "Pattern (3os) is STILL UNMADE — this 1os copy can never host it (sockets are fixed) →
  throw THIS copy, hunt a 3os/unsocketed one". Stamp only renders when EVERY word the base
  can ever hold is created; partial state = plain ✓ + amber "base type NOT fully forged"
  note naming the open words. Socket guide gated to unsocketed items at all 5 render sites.
  Spec `v602_wrong_socket_honesty.spec.ts` (3 tests) + smoke/targeted 49 green.
- **Prevention**: when a filtered list drives a "nothing left / all done" verdict, the
  verdict must distinguish WHY it's empty — filtered-out ≠ completed. Any "done forever"
  stamp must be gated on the FULL entity (base type), not the current view's slice
  (socket count). Advice lines (Larzuk/cube) must check the item state they're impossible on.

## REG-013 — 2026-07-06 · v563 spare-base verdict ignored CAPACITY → 1 Bone Visage "covered" every helm word, vendoring keepers (live, user-caught)

- **Symptom**: Throw-Out Review told Konyo to vendor his Demonhead AND Spired Helm as
  "spare — runewords (Coven, Delirium, Flickering Flame…) already covered by Bone
  Visage, a base you hold" — while he owns exactly ONE Bone Visage and had 7 helm
  words still unmade. The same card even listed those words under "Keep for
  runewords" (contradictory messaging).
- **Caught by**: Konyo, live (2026-07-06 screenshots). No spec covered >1 unmade
  word sharing one owned base — v563's spec used exactly one unmade word (Insight).
- **Root cause**: `_spareBaseInfo` marked EVERY unmade word "covered" if ANY forgeScan
  task planned it on another owned base — but forgeScan emits one task per WORD, and
  when several words fit the same single copy they all name it (the v536 spread pass
  lets a word with no free base "keep" its base; rune-blocked one-steps never
  allocate at all). One physical base hosts ONE runeword, so N words "covered" by 1
  copy over-counted coverage N-fold. Same over-count silently hit the v536.2 loot
  filter (stopped farming bases for words that had NO real copy) and
  `_smartUnmadeNeedingBase`.
- **Fix** (v587): forgeScan runs a post-allocation CAPACITY LEDGER — every based task
  in plan-priority order (make-now → deferred → pipeline → rune/cube one-steps)
  claims one copy of its base (`t.base.count`); overflow tasks get `t.baseOver=true`.
  `_spareBaseInfo`, `_endgameFilterBases`, and `_smartUnmadeNeedingBase` all skip
  over-subscribed tasks. Repro (1 BV + 7 unmade helm words): OLD = both helms
  "__throwout/spare"; NEW = both "still needed for …". New spec
  `v587_spare_base_capacity`; v527's v536.2 test re-pinned to a 1-word Chronicle
  (with 6 words on 1 Voulge the base now correctly STAYS in the filter).
- **Prevention**: (1) any "already covered / already owned" verdict derived from
  forgeScan tasks must respect `t.baseOver` — a task is a PLAN, not proof of a spare
  copy; (2) when a resource (base copy, rune) is shared across recommendations,
  spec the N-demands-vs-1-supply case, not just 1-vs-1.

## REG-012 — 2026-07-06 · v584 commit swept 672 untracked art deletions → 652 dangling refs failed CI (invisible locally)

- **Symptom**: Routine I red on BOTH 59ae0af (v584-585) and 81002e4 (v586) — 7 art
  "no console errors" specs (v75/v76/v81/v123/v127/v145/v427) with
  `ERR_FILE_NOT_FOUND` ×2-4, plus 00_convergence_lock.
- **Caught by**: CI only. Every local run was green because the deleted files still
  sat on the Mac's disk — only a tracked-files checkout (CI / fresh clone) missed them.
- **Root cause**: two independent riders on the v584-585 commit.
  1. `git add -A` swept 503 corrupt blue-gem `base_*.png` + 169 `d2io_*` deletions
     (a leftover corrupt-art purge in the working tree) along with the 11 intended
     aura-gif deletions. Right files to delete — but D2IO_ART still referenced 652
     of them, so every card whose art map hit a dead path threw a console error.
  2. The recurring **stray dead-fork edit trap**: H/J/K/L sweep scripts were again
     rewritten to `bible_routes.html` + hardcoded `/Users/...` path and rode into
     the same commit; 00_convergence_lock (v533) caught it exactly as designed.
- **Fix** (5e56196, v586.1): 146 refs re-pointed to existing hd_/mr_/graphic art
  (Zakarum Shield → tier-shared hd_aerin_shield); 522 dead map entries dropped so
  the v384/v570 tier-aware resolver + glyph fallback serve those names (strictly
  better than the corrupt placeholder they used to show); sweep scripts restored
  from 1b15f21. All 8 specs re-run green in a clean `git worktree`.
- **Prevention**: (1) before `git add -A`, `git status --short | head` and READ the
  D-list — deletions you didn't make this session are a red flag; (2) after any
  art-file change, run the dangling-ref check (grep art/ refs in bible.html vs
  `git ls-files art/`) — it's 3 lines of python; (3) reproduce CI-only failures in
  a `git worktree` (tracked-files-only) FIRST — local disk state lies.

## REG-011 — 2026-06-13 · AI intake: art hallucination + silent vocab-filter drop (live, user-caught)
- **Symptom**: Konyo's 3-shot test: a no-tooltip stash screenshot registered phantom items
  (runes, "Tal Rasha set (any piece)"; replay also produced "Tyrael's Might"), while a
  crystal-clear Frostburn tooltip registered NOTHING.
- **Caught by**: the USER, live. Audited by replaying his exact screenshots against the
  live endpoint — the decisive method (headless UI tests can't catch model behavior).
- **Root cause**: (a) vision model reads item ART without a tooltip and fuzzy-matches it;
  (b) server filter `vocab.has(n)` silently discarded near-matches ("Frostburn Gauntlets"
  = tooltip name+base merged) without even surfacing them in `unrecognized`;
  (c) 4K fullscreen shots downscaled to 1344px → ~6px tooltip text → guessing regime.
- **Fix (v225 `8f29d72` + v226 `797f79c` + v227 `55e1300`)**: tooltip-or-nothing prompt
  rule + no-guess rule; exact→normalized→prefix vocab matching with NO silent drops;
  downscale 1568; dock-chip ✕ eraser; set AGGREGATES banned from vault/vocab, 67 exact
  pieces first-class. Post-fix replay of all 3 shots = exact ground truth.
- **Prevention**: (1) NEVER `filter()` model output silently — unmatched reads must
  surface somewhere visible. (2) Audit AI features by replaying REAL user inputs against
  the LIVE endpoint, not just mocked routes. (3) A vision prompt needs an explicit
  "absence" rule (no tooltip → empty), not just positive instructions.

## REG-010 — 2026-06-12 · vault hover magnifier rendered UNDERNEATH the fullscreen overlay (looked "not working")
- **Symptom**: Konyo, live on v217-v219: "the image floating cursor wasn't working" — hovering a
  vault item in the fullscreen mule card showed no enlarged image at all.
- **Caught by**: the USER on the live site. My v217/v219 headless checks verified the popup turned
  `on` and measured its size — but never that it was visibly on TOP.
- **Root cause**: `#arttip` lives at z-index 9999; the fullscreen replica `.vd-fs` overlay is
  99997. The magnifier fired correctly and rendered the whole time — underneath the overlay.
- **Fix (v220, `cf19720`)**: `html.vd-lock #arttip{z-index:2147483000 !important}`. Verified with
  a REAL `page.mouse.move` hover + screenshot (575px Spellsteel floating above the card).
- **Prevention**: (1) Any new full-viewport overlay must audit the z-index of every shared
  floating element (`#arttip`, lightbox, palette) it can co-exist with. (2) "Popup is on + has
  size" is NOT visibility — screenshot it. (3) `elementFromPoint` cannot prove popup visibility:
  it skips `pointer-events:none` elements by design.

## REG-009 — 2026-06-12 · vault stash items overflowed their grid boxes (cell ≠ track)
- **Symptom**: Konyo screenshot: items misaligned vs the 10×10 stash boxes — "you need to
  recalibrate it… match the box its sitting in."
- **Caught by**: the USER on the live site (v214-v217).
- **Root cause**: `.vd-cell` was hard-coded 40px while the CSS grid TRACKS were responsive
  (~60px) — background boxes and item blocks were sized on two different rulers.
- **Fix (v218, `8ce082f`)**: cells `width/height:auto` fill their tracks + `gridHtml` emits
  explicit `grid-auto-rows:<cell>px`; geometric audit (100 cells, cell==track ≤3px, item spans
  exactly w×h tracks).
- **Prevention**: in any CSS-grid replica, the cell ELEMENT must inherit its size from the
  track — never restate the dimension in a second place. Verify geometrically, not visually.

## REG-008 — 2026-06-12 · Python-style `\U0001F9E9` escapes rendered as literal text in vault UI
- **Symptom**: Konyo screenshot: literal `U0001F9E9` strings visible in the set sister-pieces
  header + art fallbacks (3 occurrences).
- **Caught by**: the USER on the live site.
- **Root cause**: `\U0001F9E9` is a PYTHON escape; JS treats it as `U0001F9E9` with a dead `\`.
- **Fix (v217)**: replaced with literal 🧩; repo-wide scan confirmed zero remaining `\U` escapes.
- **Prevention**: in JS strings use literal emoji or `\u{1F9E9}` (ES6 braces) — never `\UXXXXXXXX`;
  after any emoji-in-JS work, grep `\\U000`.

## REG-007 — 2026-06-12 · vault cards used `card-body` + v200 Smith top-3 flip broke two suite locks
- **Symptom**: Routine I shards 1+3 red on the v204-v207 pushes — `v83_sync_audit` (tools-card
  structure) + `v122` ("Smith gets NO top-3 strip").
- **Caught by**: scheduled CI full suite (per-push backstop) — NOT the pre-push smoke gate.
- **Root cause**: (a) the new vault tool cards used `class="card-body"`; the v83 audit requires
  every tools card to clone the idiom exactly (`.boss-card.collapsible` + `.boss-header` +
  `.boss-body`). (b) v200 deliberately GAVE the Smith a top-3 strip, but v122 had locked the
  opposite claim and was never updated.
- **Fix (v208)**: vault cards converted to `.boss-body`; v122 lock flipped to assert the new truth.
- **Prevention**: (1) new tool cards: copy an existing card's exact class skeleton. (2) Flipping
  any content claim requires grepping ALL specs for the OLD claim — a lock is a spec-encoded
  sentence, not just a selector (same family as REG-005/006).

## REG-006 — 2026-06-11 · v176 gambling section used `.drops` tables in the reference tab → broke v50 tier-count
- **Symptom**: Routine I (Playwright) shard 3/3 red on the v176 push (`670e33a`) and still
  red through v177 — 1 real test, all 3 retries deterministic:
  `v50_p_slider_explainer:41` (`expect(rows.length).toBe(4)` for the P# slider tier table).
- **Caught by**: scheduled CI full suite — NOT the 39-test pre-push smoke gate (v50 not in
  it). Reproduced locally (v50 + v176 together) = real, not tail-fatigue (failed on all retries).
- **Root cause**: the v176 Gambling section (Bridge B2) added THREE `<table class="drops">`
  (NPC / odds / what-to-gamble) inside `#tab-ref`. v50 counts `#tab-ref table.drops tbody tr`
  and assumes the P# slider tier table is the ONLY `.drops` table in the reference tab (it
  expects exactly 4 tier rows). Every OTHER ref-tab table uses `class="ref-tbl"` (Mercenary,
  Craft matrix, Breakpoints) — the gambling section broke that convention, inflating the count.
  The v176 spec only checks `#gambling-ref` text content (odds/NPCs), so it stayed green while
  the older v50 lock broke.
- **Fix (v180, commit pending)**: convert the 3 gambling tables `class="drops"` → `class="ref-tbl"`
  (the correct ref-tab convention; ids/content/`item-name` colours unchanged). v50 4/4 + v176 5/5
  green together; L_integrity 0. +6 bytes.
- **Prevention**: (1) The reference tab's table convention is `.ref-tbl`, NOT `.drops` — a
  `.drops` table there silently hijacks `v50`'s loosely-scoped `#tab-ref table.drops` selector.
  Use `ref-tbl` for any new reference-tab table. (2) A new section's spec asserting only its OWN
  `#id` text WILL pass while breaking an older spec that counts a shared selector across the tab —
  same lesson as REG-002/004/005: run the FULL `npx playwright test`, the 39-test smoke gate does
  not include v50. (3) When adding tables to an existing tab, grep `tests/` for selectors scoped
  to that tab's container (`#tab-ref table...`) before picking a table class.

## REG-005 — 2026-06-09 · v154 ref-header restructure truncated two test-locked section titles
- **Symptom**: Routine I (Playwright) shards 1 + 2 red on the v154 push (`f5dcb4a`) —
  2 real tests: `v50_p_slider_explainer:25` (expected substring "What the P# slider
  actually does") and `v112_binds_tierlist_droppool:77` (`refHasSources` regex
  `/Warlock bind .* Aura Enchanted .* sources/i` no longer matched). A 3rd red
  (`v41_deep_audit:324` calc "shako" search) was the KNOWN badge-interception flake —
  passed in isolation, NOT a regression.
- **Caught by**: scheduled CI full suite — NOT the 39-test pre-push smoke gate (neither
  v50/v112/v41 is in it). v50 + v112 reproduced locally = real.
- **Root cause**: the v154 first-glance restructure (single-line `emoji Title ▾` → rich
  `.sec-h-block` with title + subtitle) rewrote all 12 ref-tab `<h2>` titles. Two were
  SHORTENED for the bar: "What the P# slider actually does" → "…slider does", and
  "Warlock bind & Aura Enchanted — sources" → "Bind & Aura Enchanted sources". Both
  exact strings are LOCKED by older specs (v50 asserts the verbatim methodology title;
  v112 regexes the ref text for "Warlock bind"). The v154 spec only checks the NEW short
  titles ("Cube Recipes" etc.), so it stayed green while the older locks broke.
- **Fix**: commit restores both titles verbatim ("What the P# slider actually does",
  "Warlock bind & Aura Enchanted — sources"); the rich `.sec-h-block`/subtitle structure
  is untouched. v50 3/3, v112 7/7, v154 4/4, v146 (20 total) green; L_integrity 0; v41
  calc-shako passes in isolation.
- **Prevention**: (1) Restyling a section HEADER must preserve the exact title TEXT —
  older specs lock title strings as content anchors, not just structure. Before
  retitling, `grep` the verbatim phrase across `tests/`. (2) A new spec that asserts the
  POST-change wording will pass even as it breaks an OLD spec asserting the PRE-change
  wording — run the FULL suite, not just the new spec + smoke gate (same lesson as
  REG-002/004: smoke ≠ substitute for `npx playwright test`). (3) Shortening copy is a
  content change even when the intent is "just visual."

## REG-004 — 2026-06-09 · calc item-tile data-art-logo → decorateItemLogos dup + DOM-order hijack
- **Symptom**: Routine I (Playwright) shard 1/3 red — `v123_inline_item_logos`
  "Key of Terror has emoji fallback" failed (`r.fallback.length` was 0, expected >0).
- **Caught by**: scheduled CI full suite — NOT the 38-test pre-push smoke gate
  (which does not include v123). Reproduced locally in isolation = real.
- **Root cause**: v143 (`21a033b`) added a context-aware NAME hover to the calc grid
  by tagging every `.item-tile-name` (312 tiles) with `data-art-logo`. But
  `data-art-logo` has a SIDE EFFECT beyond the hover delegation: `decorateItemLogos()`
  consumes every `[data-art-logo]` lacking a `.d2art-wrap` child and PREPENDS
  `artOr(name, glyph, 'sm')` — with no `data-art-glyph` attr the injected wrap had an
  EMPTY fallback. Two failures cascaded: (a) every calc name got a duplicate glyph-less
  thumbnail; (b) calc tiles sit EARLIER in the DOM than the event-card cells, so
  v123's `querySelector('[data-art-logo="Key of Terror"]')` matched the empty-fallback
  calc tile first → `fallback.textContent.length === 0`.
- **Fix**: commit `dca9247` — calc tile uses `data-arttip` instead of `data-art-logo`.
  The #arttip delegation still reads `data-arttip` for the rich name-hover, but
  `decorateItemLogos` ignores it → no duplicate injection, no querySelector hijack.
  v123 5/5 in isolation; full suite 634 passed / 1 skipped / 0 failed.
- **Prevention**: (1) `data-art-logo` is NOT a neutral hover hook — it is CONSUMED by
  `decorateItemLogos` (auto-injects a logo). For hover-only intent use `data-arttip`
  (read by the same #arttip delegation, ignored by the decorator). (2) A `querySelector`
  that selects by a shared attribute picks FIRST-IN-DOM — adding that attribute to a
  high-frequency render path (312 calc tiles) silently hijacks any earlier-test
  selector. (3) A change to a high-frequency render path needs the FULL suite, not the
  smoke gate — same lesson as REG-002 (smoke ≠ substitute for `npx playwright test`).

## REG-003 — 2026-06-08 · per-charm Sunder recipe search misrouted to Bone Break
- **Symptom**: searching "renew black cleft" (and every other charm) landed on the
  Sunder recipe grid headed by Bone Break instead of the Black Cleft row. User: "when
  i search for black cleft it routes me to bone break."
- **Caught by**: user report (not a test — there was no per-charm routing assertion).
- **Root cause**: `openSunderRecipes()` was charm-agnostic — it only switched to the
  tools tab + uncollapsed the card, leaving all 6 rows collapsed (Bone Break first in
  the grid). The 6 per-charm recipe search commands (v133) all called it with NO
  argument, so any charm's "renew" intent landed on the same Bone-Break-led view. The
  charm's own MATERIAL card (openDrop) was always correct — only the recipe-tool route
  was generic.
- **Fix**: `openSunderRecipes(charm)` now expands + scrolls EXACTLY that charm's
  `details[data-charm]` row (closing siblings); per-charm commands pass `s.n`. No-arg
  call unchanged (opens card, no row forced). bible.html `9603dd3`.
- **Prevention**: v136_routing_audit_lockdown — AUDIT spec asserting every one of the
  6 charms routes to its OWN recipe row AND its OWN material card via both the direct
  fn and the global-search path (no sibling). Lesson: a per-entity action that takes
  NO entity argument is a latent misroute — when N search commands fan into one
  handler, the handler MUST receive + honor the entity key, and a lockdown test must
  assert each entity lands on itself, not just that "something opens".

## REG-002 — 2026-06-08 · reference tables reused class="drops" → tripped droptable integrity guards
- **Symptom**: Routine I (Playwright) shards 1 + 2 red — 3 tests:
  v109_binds_collapsible `all 12 binds sections` (count 12, got 14),
  v40_lockdown `zero empty chance cells in any droptable` (empty cells:
  tab-ref/9, /15, /20 = the FCR Note column), v50_p_slider_explainer
  `all 4 tiers present` (`#tab-ref table.drops tbody tr` ≠ 4).
- **Caught by**: scheduled CI run (push `aa6c300`) — NOT a local run.
- **Root cause**: the additive #tab-ref tables added across v112 / v115 /
  B3+B4 (bind sources, mercenary, crafted recipes, FCR/FHR breakpoints) all
  reused `class="drops"`, which v40 + v50 treat as a SEMANTIC boss droptable.
  v40 scans every `table.drops` for empty col≥2 cells (the FCR "Note" column
  is legitimately empty); v50 expects `#tab-ref table.drops` to be exactly
  the 4-row P# tier table. Separately v109 hard-codes 12 binds sections but
  v112 added the Tier-List + Aura-Enchanted sections (→14). All accumulated
  because v112–v118 ships validated SUBSETS, not the full suite, and the
  38-test smoke gate doesn't include v40/v50/v109.
- **Fix**: commit `e71e862` — new `class="ref-tbl"` (identical CSS, aliased)
  for the 7 non-droptable reference tables so the integrity drills only scan
  real drop tables; P# tier table stays `class="drops"` (v50's target).
  v109 count 12→14. 17/17 targeted + 56 adjacent + 38 smoke gate green; live.
- **Prevention**: (1) `class="drops"` is SEMANTIC (= boss droptable: item|tc|
  6-diff cells), NOT a generic table skin — use `class="ref-tbl"` for any
  reference/explainer table. (2) Adding a collapsible section to a tab that a
  count-spec guards (v109 binds, others) means bumping that count in lockstep.
  (3) Run the FULL `npx playwright test` before push when touching shared
  markup/CSS — the smoke gate is a fast-path, not a substitute.

## REG-001 — 2026-06-05 · artOr() lazy-load strip → calc-grid load storm
- **Symptom**: Routine I (Playwright) shard 3/3 failed — 3 tests red:
  v71_d2art `calc grid tiles` + `boss-nav chips` (assert `loading="lazy"`),
  v74_material_search `Colossal Ancient Statues header` (assert `loading="lazy"`).
- **Caught by**: scheduled CI run (push commit `4b80ba5`, headSha) — NOT a local run.
- **Root cause**: commit `4b80ba5` ("eager-load the 8 boss-card portraits" for a
  Safari rendering fix) dropped `loading="lazy"` from the **central `artOr()` helper**
  and the statue `<h2>` header — far wider scope than "8 portraits". That eager-loaded
  the hundreds of calc-grid item images (a load-time storm) and broke the tested
  lazy invariant in 3 places. **The commit was pushed to `main` without running the
  full Playwright suite** (the BULLETPROOF mandate) — that is the real gap.
- **Fix**: commit `74ae7f3` — restored `loading="lazy"` in `artOr()` + the statue
  head. Kept the 7 *targeted* static eager-loads Desktop added (Countess card header
  + 5 event-card logos): no test asserts `loading` on them, and those are the actual
  in-hidden-tab portraits Safari failed to render. 391 passed / 1 skipped local, green.
- **Prevention**: (1) ALWAYS run `npx playwright test` to green BEFORE pushing — esp.
  any edit to a *central* helper (`artOr`, `openDrop`, `switchTab`), whose blast radius
  is site-wide. (2) Editing a shared template means re-running the whole suite, not just
  the spec you think you touched. (3) CI (Routine I) is the backstop, not the gate —
  treat a red scheduled run as a real regression first, re-run the failing spec in
  isolation to rule out suite-tail fatigue (this one reproduced in isolation = real).

## REG-002 — 2026-06-08 · facet showcase + hidden-tier source-chip rank-first
- **Symptom**: Routine I red (push `a92b308` "Add Rainbow Facet …", inherited by
  `beda227`). 3 tests: `v81_colossal_jewels` showcase `.endgame-relic` count (was 11),
  `04_item_routing:44` (click source chip → boss) + `:79` (Esc clears active item).
- **Caught by**: scheduled CI (shards 1/3 + 3/3). Reproduced locally in isolation
  (`04:44/79` fail; PASS on parent `c6922e8`) = real, not suite-tail fatigue. NOTE: a
  concurrent CPU spike made local runs take ~19min — that was load noise, NOT the bug
  (clean runs are ~10-30s); always sanity-check `uptime` before trusting slow runs.
- **Root cause (two independent)**:
  1. v81 — `a92b308` added 8 Rainbow-Facet tiles to `#colossal-showcase` with class
     `colossal-tile endgame-relic`, so the showcase count went 11→19; the spec hard-
     asserted `toBe(11)`. (Intended feature, stale test.)
  2. 04 — LATENT since v87 (`a4d90d8`, "Hell-only view": CSS line ~107 hides
     `schip-norm/normtz/nm/nmtz` source chips with `display:none !important`). The
     aid-card chip bar still RENDERED those hidden tiers and ranked them fastest-first
     (`valid.sort` by hours-to-50%). When a NM-tier source ranked #1 for SoJ/Shako the
     first `.source-chip` was invisible → Playwright `.first().click()` timed out (a
     real user couldn't click it either). Surfaced on the `a92b308` CI run.
- **Fix** (render-only, math untouched): aid-card now builds `chipSrc =` the
  hell/hellTz subset of `valid` (falls back to all tiers if an item has no Hell
  source) and renders chips + count + "+N more" from `chipSrc` — so the first chip is
  always a visible Hell chip. v81 count assertion bumped 11→19 with a comment. New
  specs `v131_aggregate_jewel_links` (the user-requested 6-jewel links on the aggregate
  card). 04 7/7, v81 11/11, v128 4/4, v131 3/3, +84 smoke/adjacent green; L_integrity 0.
- **Prevention**: (1) when a CSS layer HIDES a class of interactive elements, stop
  RENDERING them too — a hidden-but-present clickable is a latent trap (focus/first-
  child/keyboard land on it). (2) A spec that hard-asserts a tile/row COUNT must be
  bumped in lockstep with any feature that adds to that container (v81 ↔ facets, same
  lesson as v109 ↔ binds in the BUG-above). (3) Sanity-check host load before trusting
  a slow/failing local run.

## REG-016 — socketed grimoires/voodoo heads were planner-invisible (Vigilance '✓ got the base' didn't ascend)
- **Symptom:** clicking '✓ got the base' on Vigilance registered "Blasphemous Grimoire (2os)" into owned but the word stayed a 🟡 one-step (base: null) instead of ascending to ⚒ Make now. Same for every AI-intake read of a socketed grimoire/head since the classes were added.
- **Caught by:** Konyo live (2026-07-13), reproduced headlessly same night.
- **Root cause:** `_ensureSocketBaseEntry`'s slot resolver only mapped body armor/shield/helm/weapon cats; RotW's 'grimoire' and 'voodoo head' cats fell through to `slot=null` → silent return → no EXTRA_ITEMS entry → `_ownedBases()` (cat==='Socketed bases') never saw them.
- **Fix:** v668 — grimoire + voodoo head map to the Shield slot.
- **Prevention:** REG-016 spec in tests/v660_got_base_ascend.spec.ts (registers both classes + full ascension e2e); doctrine: any NEW base cat added to _baseCats must be wired into the slot resolver or it is planner-invisible.

## REG-017 — v682 set-seed floor desynced from the live tracker (first persist() wiped all 108 seeds)
- **Symptom:** F·Sets meter could drop from 108/135 back to the pre-seed count mid-session; un-marking a seeded piece RE-ticked it and wiped the other 107 seeds; Tools Set Tracker and F·Sets forge disagreed in the same session.
- **Caught by:** 52-agent dual-mode audit (2026-07-14), adversarially verified ×2; never seen live (Konyo's profile converged via the import+reload path).
- **Root cause:** the v682 boot floor wrote the 108 `_SET_SEED` pieces to localStorage only, never syncing the in-memory `setPieces` Set — `persist()` (42 call sites) then rewrote `d2r_setPieces` from the stale Set, and `toggleSetPiece` branched on the same stale truth (inverting seeded un-ticks). The adjacent unique floor did it right (`owned.delete` mutates the live Set).
- **Fix:** v684 — the floor mirrors every seed into the live `setPieces` (`_spSet.forEach(setPieces.add)`); mac-ladder toggles no longer write MAIN's shared `d2r_grailUnfound`.
- **Prevention:** headless sim asserts in-memory === LS post-boot AND post-persist(); doctrine: a boot floor must mutate the LIVE structure, never only the store.

## TV-NOTE-003 — 2026-07-17 · run #4 stash panel false-vaulted (no object permanence)
- **Symptom:** looted Colossus Crossbow (+ Jewel) in Black Marsh; shared stash auto-vaulted
  Blood Shield / Compendium / Unidentified; Crossbow never farmed; Jewel vaulted without floor SEEN.
- **Caught by:** Konyo run #4 live + Grok bridge monitor, 2026-07-17.
- **Root cause:** `_on_stash` committed every non-junk name on the panel (panel-greedy).
- **Fix:** v738 — stash-commit requires SEEN/HOLDING/candidate; Unidentified hard-ban;
  `stash-no-chain` / `skip-weak` tags.
- **Prevention:** never vault from stash text alone; chain to floor or inv first.

## TV-NOTE-002 — 2026-07-16 · inv glimpse vaulted after ID→throw (commitment missing)
- **Symptom:** open inventory briefly → 🏦 vault chip / farmed wire; drop junk after ID still
  counted as vaulted; Vault UI sometimes empty of that name; HIT badge read as “vaulted.”
- **Caught by:** Konyo live run #4 + screenshot, 2026-07-16.
- **Root cause:** soft first-inv / farmed_names committed on first inv panel presence, with no
  hold timer or throw-out reverse. Board treated farmed as vault immediately.
- **Fix:** v731 — pending HOLDING (≥HOLD_MS ~30s still in bag) or town stash commit;
  floor-again throw-out cancels pending + `tvVaultUnregister`; hist ⏳ hold vs 🏦 vault;
  only `vault_names` auto-apply.
- **Prevention:** never auto-vault from a single inv frame; require hold duration or stash.

## TV-NOTE-001 — 2026-07-16 · session history was RAM-only (last TV run vanished on agent restart)
- **Symptom:** after a live TV DIABLO session + agent restart, the TV tab feed was empty —
  no clock-time trail of what AI read, no DB match trail, no vault filing trail for debug.
- **Caught by:** Konyo live (run #2/#3 prep), 2026-07-16.
- **Root cause:** receiver kept `FEED` in memory only; agent `state.json` resets on boot
  (`startedAt` fresh). Nothing persisted across restarts.
- **Fix:** v724 — `d2r_tvdHist` localStorage (account-forked) + SESSION HISTORY panel
  (LIVE / LAST SESSION) + HD art + HIT/DB/NO DB badges + `GET /frame` last JPEG.
  Specs: `tests/v712_tv_board.spec.ts` history test.
- **Prevention:** any new live agent feed must persist to account-forked LS (or agent
  disk history) before the next boot, or debug trail is lost by design.

## REG-018 — Routine I silently dead for 40 runs (50m cap SIGKILL = no blob report = invisible failures)
- **Symptom:** zero Routine I verdicts since v681.1 — 9 failures then 6 "cancelled"; merge-report merged the surviving shards and went green on itself, so shard 3's ~15 real failing specs were never named anywhere.
- **Caught by:** dual-mode audit CI lens (2026-07-14) reading the cancelled runs' dot output.
- **Root cause:** the suite grew to ~1400 tests (3-way sharding sized for ~946): shard 3 needed ~60m vs `timeout-minutes: 50`, and the runner's SIGKILL killed playwright before the blob report was written; `retries:2 × 180s` amplified each failing test to up to 9 minutes, which is what pushed red shards past the cap.
- **Fix:** v684 — 6-way sharding (~15m/shard), CI `globalTimeout` 45m (graceful exit always writes the blob), CI `retries:1` + 120s per-test, and merge-report FAILS unless all 6 blobs are present.
- **Prevention:** the blob-count guard makes a reportless shard a loud red forever; shard budget documented in the workflow header (re-shard when a clean shard passes ~20m).

## REG-019 — v747-v758 toggle-OFF undone by a late in-flight poll response (stage stuck visible)
- **Symptom:** flipping the TV switch OFF sometimes left the NOW ON AIR stage (and live state) up
  forever; surfaced as the Routine I shard-6 flake (the OFF assert timing out), and is the same
  race class as Konyo's oldest live complaint ("the flip switch was already on").
- **Caught by:** board754 (Fable code-review agent) stress-running the v747 spec 6×@workers=2
  after the first waitForFunction fix did NOT kill the flake — the wait was honest, the product
  was not.
- **Root cause:** poll()'s fetch .then() ran `setState('live')` unguarded; toggle-OFF cleared the
  interval but an already-in-flight response resolved afterwards and re-lit the board with no
  future poll to correct it. The .catch() path had the same late-fire hole.
- **Fix (v758.1):** `if(!T) return;` at the top of both .then() and .catch() — a response that
  lands after the switch is OFF is discarded. All four poll() call sites set T synchronously
  before any response can resolve, so no legit response is ever dropped.
- **Prevention:** stress repro is the lesson — a "flaky test" that survives an honest
  condition-wait is a PRODUCT race until proven otherwise; run repeat-each before recalibrating
  the spec.

## REG-020 — v761-v773 board-window spawn had no singleton (26-window WebKit swarm froze the Mac)
- **Symptom:** Konyo's Mac became barely usable ("something is lagging the hell out of my pc") —
  dozens of minimized python windows in the Dock, WindowServer at 57% CPU.
- **Caught by:** Konyo live; ps sweep found 27 control_app instances + 26 --board-window
  processes, each with WebKit children.
- **Root cause:** _open_board_native spawned a NEW pywebview sibling process on every call and
  never reaped the previous; rapid ON/OFF button testing (Grok's v773 verification) multiplied
  them. The _BOARD_OPENED once-guard resets per control restart, so restart loops amplified it.
- **Fix (v773.1):** pid-tracked SINGLETON — board_window.pid written on spawn, previous pid
  SIGKILLed before a new spawn.
- **Prevention:** any spawn-per-click surface needs a reap-or-reuse story from day one; process
  accumulation is invisible until the OS chokes — check `pgrep -c` in verification passes.

## REG-021 · the stale-frame capture lie (v779, 2026-07-18)
- **Symptom**: film showed the DESKTOP while the agent claimed "🎯 eye pinned to D2R.exe".
- **Caught by**: Konyo live ("its not targetting the D2R.exe"); Grok root-caused after GitHub handoff.
- **Root cause**: `screencapture -l` can exit 1 writing NOTHING; the old success gate trusted
  `os.path.exists(path)` — a previous desktop BMP at the target path masqueraded as a fresh window capture.
- **Fix**: v779 temp-path capture + `_cap_promote` (os.replace only on real bytes) + TCC preflight.
- **Prevention**: promote-gate unit locks; doctrine "trust the OUTPUT of THIS call, never the path".

## REG-022 · launcher outranked the game (v779.1/v780, 2026-07-18)
- **Symptom**: window pin grabbed the CrossOver launcher (and later a Chrome bible tab) over D2R.exe.
- **Caught by**: live window-list dump during Konyo's session.
- **Root cause**: additive scoring let launcher/browser bonuses beat game identity.
- **Fix**: game identity absolute (+1000 title / +500 owner.exe), browser/editor/launcher blocklists.
- **Prevention**: picker scoring comments carry the incident; blocklists in `_PICK_OWNER_BLOCK`.

## REG-023 · journal rotation erased the previous night (v805→v811, 2026-07-18)
- **Symptom**: second 4MB rotation overwrote `sessions.1.jsonl` — months of theatre feedstock could vanish silently.
- **Caught by**: Grok R8 sleeper hunt (claim-at-consumer class), before any real loss.
- **Root cause**: single rotation slot (`os.replace` onto .1 unconditionally).
- **Fix**: v811 generation ring .1→.5 with shift, cap event on rotate, reader concats all gens.
- **Prevention**: `TestJournalGenerations` lock (GEN1 survives a second rotation); doctor `journal_gens`.

## REG-024 · the black-screen curtain (v820, 2026-07-18)
- **Symptom**: clicking SIMULATION showed a black stage — no film, no caption.
- **Caught by**: Konyo live; reproduced headless (screenshot showed DOM-present-but-invisible).
- **Root cause**: v804 #th-credits and v814 #th-slate declare `display:flex` — any author
  `display` OVERRIDES the `hidden` attribute, so both full-stage near-black overlays rendered
  permanently above the film (slate escaped hit-testing via pointer-events:none, hiding it from
  elementsFromPoint until credits was found first).
- **Fix**: `#…[hidden] { display: none !important; }` for every theatre overlay; rule presence
  is asserted in the ship gate. Bonus finds in the same debug: /hist ?w= query was stripped by
  the router before _serve_hist (derivative never served — now parsed from self.path), and the
  T+ clock was empty until first play (now lights at open).
- **Prevention**: overlay doctrine — any `display:` on a hideable element ships WITH its
  `[hidden]{display:none!important}` twin; visual verify (screenshot) joins the theatre gate.

## REG-025 · footage evicted the archive (v839, 2026-07-18)
- **Symptom**: session history all black — old sessions' read frames deleted.
- **Caught by**: Konyo ("i cant see any videos/screenshots its all black").
- **Root cause**: v826 footage (1fps, ~480MB/day) shared the 500MB hist ceiling; MB eviction ran
  oldest-first across ALL files — old sessions' read frames were the oldest → wiped (2599 footage
  vs 11 surviving reads). v813's count-caps protected counts, not the MB path.
- **Fix**: v839 — footage has its OWN sub-ceiling (FOOT_MB=900 default) and dies FIRST; read
  frames are pruned ONLY by their own count/MB, never by footage pressure; HIST_MB default 1500.
- **Data**: pre-v839 pruned photos are unrecoverable; those beats play caption-only with an
  honest '⚠ photo pruned from disk' marker. Journals intact.
- **Prevention**: any new archive class MUST declare its own budget + eviction priority before
  sharing a directory with the read archive.

## REG-026 · background ship-chain killed a live session (2026-07-18)
- **Symptom**: Konyo ON AIR got 1 read then silence; agent bridge dead.
- **Root cause**: an operator (me) background chain contained kill+relaunch of control; it
  completed mid-run and took the agent with it.
- **Fix**: session restored via /api/on immediately; operational doctrine added — app cycles
  NEVER ride background chains; cycle only when /api/status mode=off.

## REG-027 — console "already opened" with no window (2026-07-18)
- **Symptom**: Konyo double-clicks the console; it refuses — "already opened" — but no window exists.
- **Caught by**: Konyo, live, right before a farm session.
- **Root cause**: ship-chain app cycles relaunched `control_app.py` WITHOUT `--open` (headless server holds :17772; launcher's single-instance check sees the port and bails).
- **Fix**: killed + relaunched with `--open`.
- **Prevention**: every scripted cycle MUST pass `--open` unless the chain explicitly needs headless; cycle snippets updated.

## REG-028 — site `#tvd` deep link silently landed on Tools (v914→v917)
- **Symptom:** `bull-4-u.com/d2r/#tvd` opened the Tools tab, not TV·D — even after v917 "truly live" killed the switchTab coerce.
- **Caught by:** check-and-debug sweep — Routine I `v766_tvd_console.spec.ts` "#tvd deep link" (CI red), reproduced with a fresh-context file:// probe.
- **Root cause:** the v680-era BOOT hash normalizer (`bible.html` ~3367) allow-lists `#tvd-on/#tvd-off/#session` but not plain `#tvd` — on the site (no `app=1`) it rewrote `#tvd`→`#tools` via replaceState BEFORE the router ran. The v917 probe called `switchTab('tvd')` directly and bypassed boot, so the fix looked done.
- **Fix:** `_h680 !== '#tvd'` exempted from the site→`#tools` branch (v918). App-ctx branch untouched.
- **Prevention:** deep-link truth must be probed via a real `goto(url + '#hash')` boot, never via `switchTab()` — the normalizer runs before everything.

## REG-029 — vaulted runes/gems tallied TWICE (v889→v917)
- **Symptom:** every agent-committed vault of a rune/gem added 2 to the Tools stash (Ist → +2), corrupting counts + the Vault Mirror spec downstream.
- **Caught by:** check-and-debug sweep — Routine I `v712_tv_board.spec.ts` "farmed inv/stash auto-applies" (Ist expected 1, got 2).
- **Root cause:** v889 added the tvToolsDelta FUNNEL (ledger-deduped, adjusts the stash + records photo-debt) but left the legacy routes-loop `apply(kind,key)` running for the same vault_names — two independent +1 lanes. The v889 funnel spec seeds tvToolsDelta directly, so it never saw the board path double.
- **Fix:** the routes loop skips `apply()` for kinds `_toolsClassify` can own (rune/gem) when the funnel exists (v918). apply() stays for uni/set toggles + manual chips.
- **Prevention:** any new tally lane must retire or gate the lane it replaces IN THE SAME VERSION; the exactly-once spec must drive the FULL board path (mock bridge read → auto-apply), not the function in isolation.

## REG-030 — tooltip mid-hover side-flip + a spec that measured the runner, not the card (v918.x saga)
- **Symptom:** Routine I "Archon Plate stability" red across 3 straight CI rounds while green on the Mac every time.
- **Caught by:** check-and-debug sweep; killed only when the spec started printing its numbers.
- **Root cause (two-headed):** (1) PRODUCT — move() re-chose the card's side from its CURRENT width on every mousemove, so mid-hover width drift flipped the card across the item (the original v643 "randomly moving windows" class, still reachable on slow machines). (2) SPEC — stability was measured in ABSOLUTE coords; on slow runners content-visibility materialization shifts the page mid-hover, the anchor moves, the glued card follows — correct behavior read as a jump.
- **Fix:** sticky-side placement (`cur._tipSide`, kept while it fits) + the spec asserts card-delta ≈ anchor-delta and embeds dxCard/dyCard/dxAnch/dyAnch in the assertion message.
- **Prevention:** anchored-UI invariants must be asserted RELATIVE to the anchor; any spec that fails CI-only gets its numbers into the assertion message BEFORE the next blind recalibration round.

## REG-031 — stale preview frame reads as "capture still broken" (2026-07-20)
- **Symptom:** board preview shows a previous session's photo (the TCC-denied wallpaper era) while the eye is dormant (no D2R window) — Konyo reported "it's still showing my desktop" twice on a healthy agent.
- **Caught by:** Konyo report, session 2026-07-20 (WindowServer-crash recovery arc).
- **Root cause:** frames/live.bmp + eye.jpg persist across sessions; the film lane only overwrites them while actively capturing, so a dormant boot serves the previous session's last frame forever.
- **Fix:** v927.3 (bd7f777) — agent boot deletes live.bmp/eye.jpg older than 30s; missing frames render the honest STANDBY/IDLE splash.
- **Prevention:** never trust the preview as capture ground truth — the boot event line (`Screen Recording OK` / `DENIED`) and a fresh live.bmp mtime are the real signals.

## REG-032 — "TALLIES · 0 synced" forever: bridge had no CORS preflight handler (2026-07-20)
- **Symptom:** every board's intake_result POST to the bridge (:17771) died silently in the browser's OPTIONS preflight; tallies actually landed in stores but never journaled — the synced counter read 0 on every surface, always.
- **Root cause:** BaseHTTPRequestHandler with no do_OPTIONS → preflight 501 → fetch .catch swallowed it.
- **Fix:** v927.5 do_OPTIONS (204 + allow-headers content-type).
- **Prevention:** any cross-origin POST with a JSON content-type needs the preflight handled; test with curl -X OPTIONS, not just POST.

## REG-033 — off-screen engine window: WKWebView suspends timers AND evaluate_js (2026-07-20)
- **Symptom:** v928's off-screen (-3980,-3980) board window showed "linked" (stale LS stamp) while zero auto-intakes fired; a driver thread then hung forever on its first pywebview evaluate_js call.
- **Root cause:** macOS occlusion fully suspends off-screen WKWebViews — JS timers stop and evaluate_js never returns (pywebview has no timeout).
- **Fix:** v930/v930.2 — ON-SCREEN mini engine tile + control-side driver with _ejs() hard-timeout, backlog-skipping cursor, fire-and-forget JS, probe leak guard, single intake owner (?engine=1 mutes the page's own trigger).
- **Prevention:** never park a WebView off-screen and expect it to compute; wrap every evaluate_js in a timeout; lamps must probe, not read stamps.

## REG-034 — vanishing tally receipts at session end (2026-07-20)
- **Symptom:** tallies fired and counted, but "TALLIES · synced" stayed 0 for shots finishing after END SESSION; driver telemetry proved fired=1, journaled=0.
- **Root cause:** receipts POSTed only to the agent bridge (:17771), which dies at seal — a 60-90s intake finishing post-seal hit a dead port; board .catch swallowed it.
- **Fix:** v935.2/.4 — control-side /intake_result (always alive, dedupe) + board dual-post fallback + driver confirms from the journal, not just the bridge.
- **Prevention:** any receipt/callback lane must have a listener that OUTLIVES the sender; confirm from durable storage, not live sockets.

## REG-035 — REAL replay "way too fast" (2026-07-20)
- **Symptom:** ⏱ REAL at 1× compressed a 2.5-min Baal run into ~38s.
- **Root cause:** CUT/FULL skim-speed multiplier latched via __speedTouched persisted into REAL; the axis was always wall-true; the @speed readout was hidden in real mode so the stale 4× went unseen.
- **Fix:** v935.3 — entering REAL (toggle or session load) pins 1×.
- **Prevention:** mode switches must re-pin every pacing input they redefine; never hide an active multiplier's readout.

## REG-036 — receipt dedupe was dead code (2026-07-20, caught by test-routes' DB suite)
- **Symptom:** exact-duplicate tally receipts journaled twice — the double-count class the dedupe existed to stop.
- **Root cause:** v938.3 folded ok/total/errors into the INCOMING signature but left the stored-side compare as bare counts-json — two shapes that can never be equal → the dup branch never fired.
- **Fix:** v938.7 — both sides build the identical 4-element sig; pinned-bug test flipped to assert collapse.
- **Prevention:** when changing one side of an equality contract, grep for every other builder of that value; a pinned-behavior test that "shouts when fixed" turned this from silent to caught-same-day.

## REG-037 — KAI retro funnel wasted its materials shot on the D2R title screen (2026-07-21)
- **Symptom:** v948.7 materials retro audit on reel `s_1784636825977_40909` — 11 consecutive film
  frames grid-fingerprinted as `stash-materials` (confidence 2, grid+ocr sources) and the KAI
  closer funnel fired `materialIntake` on one of them; the real production reader correctly
  returned `ok:false, total:0` because there was nothing there — but Theatre showed the frame was
  actually the D2R boot/reconnect splash ("Press Any Key to Begin" / "Connecting to Battle.net"),
  not a stash panel at all. No other materials-labeled frames exist anywhere else in the 136-frame
  reel, so materials was very likely genuinely never opened this session — the false trigger just
  meant the "one shot per tab" funnel got spent on garbage instead of a clean honest-zero.
- **Caught by:** materials retro audit (Round 1 of the v948.8 arc), viewing the actual funnel-fired
  frame in Theatre film — the pixels were the title logo, not a materials grid.
- **Root cause:** `classify_stash_grid`'s materials branch (`frac_dark>=0.42` + a little chroma +
  low gear/tan) is intentionally loose (materials is the tab most prone to under-detection). The
  D2R title/reconnect splash is ~92% pure black with a burning-logo sliver of orange/red chroma —
  same signature as a near-empty materials grid (frac_dark=0.9154, frac_chroma=0.0536 measured on
  the actual frame). The `stash_open` corroboration gate in `fuse_tab_signals` didn't block it.
- **Fix:** v948.8 — `stash_eye.is_boot_screen()`: full-frame OCR word-match ("press"+"any"+"begin",
  "connecting"+"battle", "diablo"+"resurrected", "blizzard"+"entertainment") short-circuits
  `analyze_frame` to `cls:"gameplay"` before grid/OCR fusion runs. Additive-only — never tightens
  the fragile materials grid heuristic itself, so it can't reintroduce under-detection.
- **Prevention:** when a heuristic is intentionally loose to fix under-detection, its false-positive
  twin needs its own guard — don't tighten the loose heuristic (that just un-fixes the original
  complaint), add a targeted veto for the specific known-bad case instead. Always eyeball the actual
  frame a funnel fired on, not just the routing label, before trusting a "materials found" verdict.

## REG-043 — Incomplete KAI seal left Theatre film unlabeled (2026-07-26)
- **Symptom:** Session `s_1785078127173_28278` — 114 stills playable in Theatre, `classes` had stash-materials/gems, but `routing`/`engineFrames`/`completeness` missing. Scrub = unlabeled noise; gap-funnel started then window-kill aborted mid-pass. Zero intakes journaled.
- **Root:** Closer wrote scan-only `kai_report` then process died before Stage-3 routing write; kaiVer stamped/or absent so re-close did not force re-seal.
- **Fix (v1381.0):** Force re-close when `scanned>0` and `routing` missing (even at target kaiVer). Bump `_KAIVER_TARGET` + seal stamp to **6** (lockstep). Theatre **🧠 reclose** button → `POST /api/kai_reclose` priority queue.
- **Status:** SHIPPED v1381.0 / v1381.1

## REG-042 — Gap-funnel preferred wrong-cell gems; watchdog false-resolved (2026-07-26)
- **Symptom:** Tally Engine showed GEMS/MATERIALS 0 counted / 1 error; RUNES no frame. Theatre play: 31 stash-gems + 2 materials labeled, but gemIntake got Personal+Wraithstep stills; real gems grid `f_…272837` never tallied. Watchdog said "resolved by KAI funnel" on ok:false receipts. Super-analyze item-judged gem grids → 429.
- **Root:** (1) `_kai_stage3_gap_funnels` ranked max conf — conf=3 wrong-cell beat conf=0 real grid. (2) Funnel one-shot then any receipt cleared watchdog. (3) Super path included stash-gems|materials as aicJudge not intake. (4) Vault Stage-3 default OFF left fireable vault candidates unfired.
- **Fix (v1381.0/1):** Gate-aware `_kai_gap_funnel_score` (hard-penalize wrong-cell, prefer gatePass+grid eye); multi-retry up to 4 stills/`alts`; watchdog only on `_intake_is_real`; super excludes tally panels; vault default ON; tally thumbs `encodeURI`; GRAMD CHAR OCR phrase fix.
- **Prove:** unit suite `TestV1381*` + live routing sim: gems primary = `f_1784984272837.jpg` (not `f_…201778`).
- **Status:** SHIPPED v1381.0 / v1381.1

## REG-041 — Theatre + ON AIR stage overlap (2026-07-26)
- **Symptom:** Opening Theatre while ON AIR (or the reverse) stacked live feed, HOLD card,
  status chip, and the past reel — “overlapping / bugged / closed wrong.”
- **Root cause:** Theatre lived inside `.stage` while ON AIR still painted `stage-film` /
  `film-on` / HOLD into the same CRT; both buttons could read “lit”; going live under an open
  Theatre left two products fighting one surface.
- **Fix:** v1380.5 — mutual exclusion on the stage:
  1. Pressing **ON AIR** closes Theatre first.
  2. Opening Theatre clears live film paint (scanner may keep recording; CRT is PAST-only).
  3. CSS hides `stage-film` / status-chip / HOLD under `body.theatre-open`.
  4. Button glow: Theatre owns lit when open; ON AIR lit only when live *and* Theatre closed.
- **Prevention:** never co-paint live + history on the same CRT; background recording is a lamp/ribbon note, not a second film layer.

## REG-050 — the last 3 Routine-I reds: a filmless fixture + a size-blind settle (2026-07-30)
- **Symptom:** after REG-047 dropped Routine I from ~76 reds to 3, what remained was
  `v877_rinse` ×2 (Space never toggled the play button; the caption never said "read #N") and
  `v643_anchored_tooltip` ×1 (`Archon Plate stability {dxCard:-9,dyCard:-13,dxAnch:0,dyAnch:0}`,
  CI-only). The rinse pair also failed on the Mac — pre-existing, not caused by the fix arc.
- **Root cause (rinse):** the fixture wrote a journal with `frameId`s but never the frames. `/api/session`
  only returns a beat with `frame` when `hist/<frameId>.jpg` exists, so the theatre painted
  "this session has no screenshots", `TH.beats` stayed 0, and both specs asserted film behaviour
  against a session with no film.
- **Root cause (tooltip):** the settle loop waited for POSITION only. The card is centred on its anchor
  (`y = r.top + r.height/2 - h/2`; a left-side card is `x = r.left - w - 12`), so it re-centres whenever
  its own box grows. On the Linux runner the popup `<img>` decoded between the two samples — h grew ~26px,
  w ~9px — and a correct recentre read as the detach bug-class.
- **Fix (v1459):** the fixture writes a real 32×32 JPEG per frameId and isolates them with `TV_HIST`
  (never Konyo's real reels); both rinse specs now assert their PREMISE first with a number
  (`beats > 0`, caption names a read). The tooltip settle is size-aware AND image-aware on both samples,
  bounded (≤600ms on the second), with `dW`/`dH` in the failure text.
- **Prove:** Mac — `v877_rinse` 6/6 (was 4/2), `v643_anchored_tooltip` 2/2.
- **Prevention:** a UX spec must build the whole world it asserts on (journal AND film); assert the
  premise with a number before the behaviour; settle on the full box, never just position.

## REG-049 — honesty gaps in the top-level status defaults + 7 tests that never ran (2026-07-30)
- **Symptom:** (audit, not a user report) the console could paint confident state it did not have:
  a `{}` bridge body cached as a GOOD snapshot; the 15s last-good grace showing stale scene/area/health
  as live with no marker; `gameOk` defaulting True when there was no bridge data at all; the 🛡 watchdog
  lamp hardcoded `wired:True/state:"armed"` (a lamp that can never say down); the receipt feed listing
  gate-REFUSED reads as authoritative. Separately: `unittest.main()` sat MID-FILE in tv/test_control.py,
  so every class below it (TestFleetUnity, v1418) was never even defined — 7 tests silently unrun.
- **Root cause:** top-of-payload optimism. The gate / engine-bay / reference-ID machinery was already
  honest; these were defaults chosen for a quiet UI rather than for truth.
- **Fix (v1457):** `_bridge_state()` rejects any body without `online`/`now` (a miss keeps last-good
  instead of stamping _BRIDGE_LAST_OK); `stateAgeMs`/`stateFresh` ride the payload and the capture lamp
  reads "last known 6s ago"; `gameOkKnown` separates "fine" from "unknown" ("game state unknown");
  the watchdog lamp uses the shared down/live/idle vocabulary (down when engine dead-hard) and exposes
  verdict + rules; every receipt carries `gate:{pass,reason}` + `held`, and a held read keeps its row and
  its route but wears a ⚠ HELD chip (doctrine: SURFACE, never hide). Runner moved to EOF.
- **Prove:** `TestV1456HonestyDefaults` (5 tests) in tv/test_control.py; suite 257 → 264 tests, all green.
- **Prevention:** an unknown is a third state, never folded into the good one; a lamp that cannot report
  down is decoration; `unittest.main()` stays at EOF (a suite that grows upward silently loses coverage).

## REG-048 — 3 agent tests red on the Linux CI runner only (2026-07-30)
- **Symptom:** `📺 TV DIABLO — agent tests` failed every push on ubuntu-latest (201 tests, 3 failures:
  `test_to_jpeg_does_not_upscale_small_bmp`, `test_archive_bmp_is_real_jpeg_not_bmp_bytes`,
  `test_prune_kills_derivative_twins_and_orphans`) while all 201 passed on the Mac.
- **Root cause:** `_to_jpeg` has exactly two encoders — Mac `sips` and Windows System.Drawing. The Linux
  runner has neither, so it returns False. Two of the tests assert ENCODER behaviour; the third only
  needed a frame to archive (a BMP seed) before exercising prune + the orphan sweep.
- **Fix (v1456):** `has_jpeg_encoder()` probes the platform ONCE by really converting a 4×4 BMP (no OS
  sniffing) and `@needs_jpeg_encoder` skips the two encoder tests with a stated reason; the prune test now
  seeds a real JPEG (`make_jpeg`) so prune/orphan logic runs on EVERY platform. `sips -g` dimension read
  is separately gated (Windows encodes but ships no sips). Shared `make_real_bmp` helper.
- **Prove:** Mac `python3 tv/test_agent.py` = 201 OK. Encoder-less simulation (`_to_jpeg` forced False) =
  201 run, 0 failures, 2 honest skips — i.e. exactly what the runner now does.
- **Prevention:** a test that needs a platform binary states that in a skip reason; logic tests get
  platform-neutral fixtures instead of borrowing an encoder.

## REG-047 — 2 file:// ERR_FILE_NOT_FOUND on every load = the long-running CI red (2026-07-30)
- **Symptom:** Routine G stuck at 7/8 categories and ~76 "no console errors" specs red on EVERY push
  (since ~v651), while the Mac was clean: `Page errors: 2 · CON: Failed to load resource: net::ERR_FILE_NOT_FOUND`.
- **Root cause:** the v41 routine-status loader injected two ABSOLUTE Mac paths on every file:// load —
  `/Users/konyo/d2r_bible_routines/obsidian_data/routine_status.js` and `/Users/konyo/Downloads/routine_status.js`.
  On Konyo's Mac both resolve (first one returns live data, chain stops → 0 errors). On the Linux CI
  runner both are guaranteed 404s before the repo stub answers → exactly 2 errors, every load.
  v1454 mis-blamed the d2art empty-src retry + `tv/frames/hist` fallbacks (harmless; those guards stay).
- **Fix (v1455):** `_v41_ON_MAC_DISK = /^\/Users\/[^/]+\//.test(location.pathname)` gates the two absolute
  paths; off-Mac hosts (CI, Windows cousin) go straight to the sibling stub. `end_to_end_audit.js` now
  prints the URL of every failed request — the bare console line named no file, which cost 3 blind rounds.
- **Prove:** `tests/v1455_no_mac_absolute_paths.spec.ts` — copies bible.html to a NON-`/Users/` temp dir
  (a CI-shaped host) and asserts 0 `file:///Users/…` requests + exactly 1 sibling `routine_status.js`.
  Machine-independent by construction, so the Mac can no longer hide this class.
- **Prevention:** a page must never fetch a machine-absolute path unless the page itself lives there;
  any Mac-only resource gets a host gate + a non-`/Users/` spec.

## REG-046 — Windows install/launcher UTF-8 PS1 parse fail under Hebrew locale (2026-07-26)
- **Symptom:** install-tvd.ps1 / start_tvd_win.ps1 ParserError; Desktop flash-close or IRM breaks.
- **Root:** UTF-8 emoji/emdash; Windows PowerShell 5.1 + cp1255 mis-parses.
- **Fix:** v1404+ ASCII-only PS1 + UTF-8 BOM (`_ascii_clean_ps1.py` helper). Gate: Parser::ParseFile OK.
- **Prevention:** Windows .ps1 ship files stay ASCII; never paste Mac/emoji into installers.

## REG-045 — Windows ON AIR infinite spin / /api/on never returns (2026-07-26)
- **Symptom:** Cousin clicks ON AIR; button spins forever; doctor ok; agent never live.
- **Root:** start_agent held threading.Lock then _start_capture -> _pid_alive re-entered same Lock -> deadlock.
- **Fix:** v1403 `_lock = threading.RLock()`. Verified POST /api/on ~0.65s mode=live.
- **Prevention:** RLock or never call _pid_alive while holding _lock.

## REG-044 — Windows agent UnicodeEncodeError + capture_win parser death (2026-07-26)
- **Symptom:** ON AIR timeout; control_agent.log charmap/cp1255 crash on emoji boot; capture_win ParserError.
- **Root:** tv_diablo print(emoji) on Hebrew code page; capture_win UTF-8 specials without BOM.
- **Fix:** v1402 PYTHONUTF8 + stdio reconfigure; ASCII capture_win + BOM.
- **Prevention:** no required emoji on Windows boot path.

## REG-040 — Windows cousin ON AIR fails / spins (2026-07-26)
- **Symptom:** Cousin clicks ON AIR on Windows TV DIABLO — nothing / spinner / silent fail.
- **Root cause class (compound):**
  1. Desktop shortcut launches with a thin PATH → `claude` not found → agent dies or never boots.
  2. Hung agent (process alive, bridge never opens) used to return `ok: true` → UI lit ON with a dead eye.
  3. Windows Store Python stub / `pythonw` spawn quirks.
  4. UI only toasted `j.error`, not `msg`/`logTail` — cousin saw no fix line.
- **Fix:** v1380.4 — `_find_claude_bin` deep hunt + `TV_CLAUDE_BIN`; kill hung boots; prefer
  real `python.exe`; louder ON failures + doctor; `start_tvd_win.ps1` PATH seed + clearer MessageBox.
- **Cousin action:** re-run installer or `git pull`, ensure `claude` login once, relaunch TV DIABLO.

## REG-039 — Theatre film "swallowed" / small at top of shell (2026-07-26)
- **Symptom:** Opening Theatre showed a small, top-stuck video instead of the big structured
  cinema stage users remembered.
- **Caught by:** Konyo (visual); Playwright geometry: stage **305×1044** inside 960px viewport
  while theatre-open.
- **Root cause:** Sessions/off-air layout (v903/v1252) set
  `grid-template-rows: auto auto minmax(0,1fr)…` so the **DASH** owns the flex row and
  `.stage` is capped at `min-height: clamp(256px, 26vh, 330px)`. Theatre is
  `position:absolute; inset:0` **inside** `.stage` → film only fills that compact box.
  Plus `body[data-view=sessions] .stage { display:none }` could zero the stage on Sessions tab.
- **Fix:** v1380.3 — `body.theatre-open` gives STAGE the `1fr` row, collapses dash to 0,
  forces `.stage { display:flex !important }`, hides home-dash, film centers in full CRT.
- **Prevention:** any home-density change that shrinks `.stage` must pair a `theatre-open`
  override so history replay never inherits the compact standby stage.

## REG-038 — Theatre/library sessions looked empty or black (2026-07-26)
- **Symptom:** Theatre and the session library/shelf "weren't showing sessions properly" — prev/next
  sess landed on black film; HISTORY looked empty; shelf cover art/stats wrong.
- **Caught by:** Konyo live report; Grok debug of `/api/sessions` + Playwright against control :17772.
- **Root cause (compound):**
  1. Session pager (⏮ sess / sess ⏭) stepped by ±1 through **ghost stubs** (ON/OFF with 0 frames) →
     `/api/session?n=2` returned `beats:[]` → black stage.
  2. HISTORY strip used `display:none` when collapsed — library looked empty even with 2 real runs.
  3. Shelf card reused `_cov` for both coverage **%** and cover **URL** → cover stat showed a path string.
  4. `_bestFindFrame` used `encodeURIComponent` on reel paths → `%2F` broke `/hist/reel_…/f_….jpg`.
  5. Shelf painted "No runs" before async `/api/sessions` returned when `TH.sessions` was empty.
- **Fix:** v1380.2 — `thSessionPlayable` / `thNearestPlayable` skip stubs; empty-reel load redirects;
  HISTORY collapsed keeps a mini-strip; `_covPct` vs `_coverArt`; `encodeURI` for hist paths; shelf
  waits/refetches before empty state.
- **Prevention:** session navigation must filter playable reels, not raw journal sessionIds; never
  reuse one variable for both a ratio and a URL; path-encode hist keys with `encodeURI` (slash-safe).

## PIN — engine-driver never-zero re-fire: no LIVE runes 0→recovery observed this session (2026-07-21)
- **Status:** not a bug, a coverage gap. `_drv_empty_refire_plan` is tab-agnostic (no runes/gems/
  materials/vault branching for the tally path — see `tv/control_app.py` ~L298); unit test
  `test_empty_refire_plan_tally` in `tv/test_routes.py` explicitly exercises key="runes" through
  refire→done and refire→giveup, and `tv/control_app.log` shows the mechanism actively engaging
  live this session (vault_personal/vault_shared `🚫0️⃣ empty/error → re-fire → re-fire → giveup`,
  3 tries each). But every live runes fire this session landed clean on try 1 (`total=404/405/211`),
  so no live runes 0-error ever occurred to observe an actual recovery in the wild — only the
  generic mechanism (proven via code path + unit test) backs the claim it would recover.
- **Next step if this matters:** next session where a runes fire lands `ok:false`/`total:0` live,
  grep `tv/control_app.log` for `🚫0️⃣ engine-driver: runes` and confirm the retry lands a real count.

## COHESION CERT — v1291→v1310 full-system verification (2026-07-23) · NO REGRESSIONS
- **Scope:** the whole night's G3 (auto-route sweep + apply) · G4 (removable Grok layer) · E1
  (vault stats: 2× reconcile + thrown-with-stats) · Vault Integrity deepening (G3/E1/checker
  cross-reference + provenance). Verified the 20 rounds hold together, no seam.
- **Result — ALL GREEN:** node suites **75/75** (G3 merge-max+3bucket 23 · hand-off+queue 12 ·
  E1b reconcile 7 · E1c compare 8 · vault-integrity 9 · G4 toggle-paint 5 · flags 6 · toggle-states 5),
  Python G4 **14/14** (OFF byte-identical · switch-vs-key · seams · hourly+daily caps · band ·
  promotion · flag-collect). py_compile control_app.py + g4_grok.py OK; **16/16** bible inline
  scripts `new Function`-compile; G4 removal test STILL clean (0 traces, stripped py_compile OK).
- **Data contracts cross-checked (no mismatch):** `d2r_g3Filled` writer `{tracker,count,ts,by}` ↔
  vault reader `.tracker` · `_mfChecker` fields ↔ vault-card + compare consumers · g4 flag
  `{agree,verdict,note,ts,source,kind}` ↔ `_g4_collect_flags` · `/api/autoroute-sweep` keys ↔
  `_arComputeDiff` · `/api/g4_flags` shape ↔ `_g4RenderFlags`. Real-data endpoints honest
  (sweep sunders 4/6 · g4_flags empty, no key ran).
- **Verdict:** the "one intelligent system, verified" cohesion holds. Zero regressions across
  v1291→v1310; certification-only (no code change this round).

## VISUAL-LOCK — weight type system frozen + invariant test (2026-07-23)
- **What:** the `--fw-*` weight token system (console + bible) is now enforced by
  `visual_lock_invariant.py` (repo root) — asserts **0 raw `font-weight:NNN`** literals + the
  `--fw-*` `:root` set, in BOTH `bible.html` and `tv/control_ui.html`. Pure stdlib, CI-runnable
  (`python3 visual_lock_invariant.py`). Contract doc: `LOCKED_TYPE_SYSTEM.md`. Proven: fails
  loudly with file:line on an injected raw weight (tested + reverted).
- **State:** bible.html = **0 raw** (locked). control_ui.html = **3 stragglers** the console
  tokenization missed → the test correctly RED until sessions-visual folds them:
  `tv/control_ui.html:2145` (`font-weight: 400`, spaced — needs `--fw-regular:400` added to its
  :root), `:5187` + `:6104` (`font-weight:700` in JS-string inline styles → `var(--fw-semibold)`).
- **Lesson (same as the bible finish-pass):** the SPACED syntax `font-weight: NNN` slips past a
  `font-weight:NNN`(no-space) grep — always match `font-weight: *[0-9]+`. The invariant test uses
  the spaced-tolerant pattern so this class can't recur silently.

## CAPSTONE CERT — full engine arc v1291→v1329 (2026-07-23) · NO REGRESSIONS
- **Scope:** the whole night's engine lane — G3 auto-route/tally · G4 removable Grok · E1 vault stats ·
  vault-integrity deepening · Diablo-language (B4 labels + B8 fingerprint + B4-live /api/status).
  Final re-run against HEAD (all extracts + sweep data refreshed from the current tree).
- **Result — ALL GREEN:** node **75/75** (G3 23 · hand-off 12 · E1b 7 · E1c 8 · vault 9 · G4 paint 5 ·
  flags 6 · toggle 5) · python **41/41** (G4 13 · B4 15 · B8 8 · B4-live 5) = **116 assertions, 0 failed**.
  py_compile (control_app + g4_grok) OK · 16 bible scripts compile · `visual_lock_invariant.py` GREEN
  BOTH surfaces · G4 removal test still clean (0 traces) · every SESSION_FIELD_CONTRACT field present
  in real /api/sessions + /api/status.
- **Docs:** `HANDOFF_MORNING_2026-07-23.md` (night state + waiting-for-Konyo + cert) · SESSION_FIELD_CONTRACT.md ·
  LOCKED_TYPE_SYSTEM.md · G4_GROK_REMOVAL.md. Zero regressions across the arc.

## REG-051 — Windows Desktop icon opened a window that was never shown (v1444→v1460, 2026-07-30)
- **Symptom:** Konyo double-clicks Desktop **TV DIABLO**; two black consoles blink and close; no
  app window, every time, for days. Doctor/status looked healthy the whole time.
- **Caught by:** Konyo, live ("opens a black screen window terminal like two of them and then just
  closes, i dont see the app"). Found by window enumeration, not by any test or log.
- **Root cause:** `tv/start_tvd_win.ps1` spawned the app with `-WindowStyle Hidden` (added v1444,
  `c43bb1e`). That sets `STARTUPINFO.wShowWindow = SW_HIDE`; .NET WinForms applies the startup
  show-command to the process's FIRST top-level window, which is pywebview's WebView2 host window.
  The window was created correctly (`TV DIABLO`, 1120x737, at 101,101) and never shown. `pythonw.exe`
  is GUI-subsystem and has no console, so the flag bought nothing.
  Proven A/B: identical script, `-WindowStyle Hidden` → `IsWindowVisible False`; default → `True`.
- **Why it hid for days (the real lesson):** the same v1444 commit swapped the launcher's ready
  probe from `doctor.ok` to `/api/status`. A window-less process still answers :17772, so the
  launcher logged `ready status OK` and `launch complete`, and `Focus-TvdWindow` — which skipped
  every non-visible window — silently found nothing and returned. With `mode=off` the app writes
  nothing to `control_agent.log`, so boot had zero diagnostics. **A liveness probe that cannot
  fail the way the user fails is not a probe.**
- **Contributing:** `Stop-Job -Force` (no `-Force` param on PS 5.1) threw past `-ErrorAction` into
  the outer catch, so the timed-out pull job was never stopped and rewrote `control_app.py` +
  `control_ui.html` 0.59s after python started — a second, independent stale-code bug that made
  `/api/status` report v1448 off a v1453 tree.
- **Fix (v1460):** flag removed; both focus helpers accept hidden windows, `SW_SHOW` them, and
  return true ONLY when `IsWindowVisible` confirms it; `Stop-Job` + `Wait-Job` + new
  `Wait-TvdGitQuiet` gate before spawn; `_request_console_exit` destroys only (never `hide()`);
  launcher log distinguishes `launch complete (window up)` from `WARN ... NO TV DIABLO window`.
- **Verify:** cold launch via the real `.lnk` chain → 1 window, `VISIBLE=True`,
  `MainWindowTitle='TV DIABLO'`; second click focuses without a twin; PS parse + C# compile +
  py_compile green; `WINDOWS_SHIP.json`/`WINDOWS_KONYO_BOARD.md` re-stamped from v1448 to v1460.
- **Prevention:** (1) never pass `-WindowStyle Hidden` to a GUI child — hide the console by using
  `pythonw`, never by hiding the process's windows; (2) a launch is only "complete" when a
  **visible** top-level window exists — port liveness is not window liveness; (3) any focus/raise
  helper must verify `IsWindowVisible` after `ShowWindow` instead of trusting the call;
  (4) never `hide()` on an exit path — destroy or die.
- **Sibling:** REG-027 (2026-07-18) was the same SYMPTOM — "already opened, no window" — from a
  different cause (headless relaunch without `--open`). Its prevention rule covered only the
  scripted-cycle path, so this class recurred through a new door. The invariant to police is
  "control up ⇒ visible window", not any one way of breaking it.

## REG-052 — Windows test_agent: fake workers were never spawnable (2026-07-30)
- **Symptom:** `tv/test_agent.py` 7 failures + 2 errors on Windows, green on the Mac. All in
  fake-worker fixtures; assertions read `None` for `w.p`, `rd`, and worker replies.
- **Caught by:** the v1460 ship gate — I ran the suite before claiming green, then diffed it
  against a pristine v1459 worktree to prove the failures were pre-existing, not mine.
- **Root cause:** the fakes are scripts, but `CLAUDE_BIN` (argv[0] of `_claude_lean_args`) and
  `TV_OCR_BIN` (argv[0] of `_ocr_worker_cmd`) hold a single executable PATH. `fake_claude.py`
  and the two `#!/usr/bin/env bash` OCR fakes are directly executable on the Mac via shebang;
  on Windows neither is a valid CreateProcess image → `[WinError 193] %1 is not a valid Win32
  application` → the worker never started.
- **Second cause:** `_ocr_worker_cmd()` returns the real `ocr_win.ps1` on Windows *before*
  reaching the `OCR_BIN` branch, so fixtures patching only `tv.OCR_BIN` drove the genuine
  Windows OCR script instead of their fake.
- **Rejected fix — do NOT retry:** a `.cmd` shim around the fake. It spawns, but adds a
  process between worker and fake, so `p.kill()` reaps the shim and orphans the real child on
  the stdout pipe — the exact leak REG/v1204+v1206 police — and hangs `TV_FAKE_MODE=slow`
  forever. Observed live: `python.exe` pid 25100 outliving its dead cmd.exe parent.
- **Fix (v1461):** `_argv_seam()` — optional JSON-list argv-prefix override (`TV_CLAUDE_ARGV`,
  `TV_OCR_ARGV`). Suites pass `[sys.executable, "-u", fake]`, spawning the interpreter
  directly: tree one deep, identical kill semantics everywhere. Unset in production →
  byte-identical (asserted). Same shape `_ocr_worker_cmd` already used for powershell+.ps1.
- **Also fixed a FALSE PASS:** `test_timeout_kills_worker_returns_none` was green on Windows
  for the wrong reason — it asserts `r is None` and `w.p is None`, both of which a failed
  spawn satisfies. It never exercised the timeout path. Now genuinely exercised.
- **Verify:** test_agent 201 OK · test_control 267 OK · no orphan processes after the run.
- **Prevention:** (1) a test seam that carries an executable must be able to express an
  INTERPRETER PREFIX, not just a path — scripts are not executables on Windows; (2) never fix
  a spawn problem by inserting a wrapper process when the tests assert process teardown;
  (3) an assertion that something is absent/None can pass because the setup failed — pair it
  with a positive assertion that the thing existed first.

## REG-053 — pywebview 6 moved icon=, and the obvious fix silently killed the window (2026-07-30)
- **Symptom (latent):** on pywebview >= 6 the console window had no icon, and had quietly lost
  `text_select` / `confirm_close` / `easy_drag` too. Invisible here because neither `.png` icon
  candidate exists on this box.
- **Root cause:** v6 dropped `icon=` from `create_window()` (it moved to `start(icon=)`).
  `open_control_window()` passed `icon=` to `create_window` and caught the `TypeError` into a
  hardcoded reduced call — so ONE unsupported kwarg silently discarded three supported ones.
  Guessing the API instead of asking it.
- **THE TRAP — read before touching this again:** routing the icon to `start()` with the existing
  `.png` candidate makes the WebView2 host window **never show** on Windows. Silently: no
  exception, no log line, `IsWindowVisible` just stays False. That is REG-051 (the dead Desktop
  icon) all over again, and the naive fix would have re-shipped it to every machine that HAS an
  icon file. Controlled A/B, same command, only the icon differing:
  `tv_diablo_icon.png` -> visible False - none -> True - `appicon.ico` -> True.
- **Fix (v1462):** ask `inspect.signature` instead of guessing — keep every option the installed
  version accepts, route the icon to whichever call owns it, and log anything genuinely dropped.
  Windows accepts **`.ico` only** (`appicon.ico`, which already ships and is what the Desktop
  `.lnk` uses); a non-`.ico` is refused outright. `.png` candidates stay Mac/Linux.
- **Verify:** cold launch via the real `.lnk` chain with the `.ico` active -> `launch complete
  (window up)`, 1 window VISIBLE=True; test_agent 201 OK; test_control 267 OK.
- **Prevention:** (1) probe an optional dependency's signature, never infer it from an exception —
  a `TypeError` catch-all cannot tell WHICH kwarg was rejected, so it throws away the good ones
  with the bad; (2) any change touching window creation must be A/B'd against
  `IsWindowVisible`, because this codebase has now shipped the same "window exists but is never
  shown" failure twice from two unrelated causes (REG-051, this); (3) cosmetics must never be
  able to cost the window — refuse the decoration, keep the app.

## REG-054 — the suites were only green with an undisclosed env var, and one CORRUPTED a tracked file (2026-07-30)
- **Symptom:** v1460/v1461/v1462 each shipped `Verify:` lines saying `test_agent 201 OK` /
  `test_control 267 OK`. Run plainly (`python tv/test_agent.py`, no env vars) both were RED,
  and the agent suite left `tv/stub_manifest.json` modified and un-decodable.
- **Caught by:** the v1463 third-eye pass — two of five independent reviewers found it, and it
  reproduced immediately by hand. It was invisible to me because every run I made exported
  `PYTHONIOENCODING=utf-8 PYTHONUTF8=1` first, which masks the entire class.
- **Root cause (the corruption):** `TestFarewellRead.setUp` reads `tv/stub_manifest.json` with
  `encoding="utf-8"` but wrote it back with a bare `open(path,"w")`. On a Hebrew console
  (cp1255) U+2014 is re-encoded as the single byte `0x97`, so the TRACKED fixture stops being
  valid UTF-8. Sticky: every later run then dies in the utf-8 read, and `claude_read`'s
  `except Exception: man = {}` silently degrades the stub lane instead of shouting.
- **Root cause (the reds):** `control_app.py` never got the win32 stdio reconfigure that
  `tv_diablo.py` has carried since REG-044, so its emoji `print()` calls raise
  `UnicodeEncodeError` under cp1255. Plus unencoded `open(tv.__file__)` and `cap_target.json`
  writes in the tests.
- **Fix (v1463):** every test read/write of a repo file pins `encoding="utf-8"`; control_app
  gets the same stdio reconfigure block; doctor's flat 3s urlopen timeout raised to 45s.
- **Verify:** `python tv/test_agent.py` + `python tv/test_control.py`, NO env vars, three
  consecutive rounds: 201 OK / 267 OK every round, exit 0, `git status` clean after.
- **Prevention:** (1) a "green" claim must name the exact command AND the environment it was
  run in — if it needed an env var, the env var is part of the claim; (2) tests must never
  write a TRACKED file, and if they must, `encoding=` is mandatory and the run must leave
  `git status` clean — that is now the check; (3) any Windows entry point that prints emoji
  needs the REG-044 stdio block, not just the one that happened to hit it first.

## REG-055 — a "proof the window is up" that another process could satisfy (2026-07-30)
- **Symptom (latent):** none observed live — found by review before it bit.
- **Root cause:** the v1460 window-presence check matched `title == "TV DIABLO" ||
  title.startswith("TV DIABLO ")`. The popout board window is titled `"TV DIABLO — Board"` and
  runs in its OWN process (`--board-window`), so it matches the prefix. With a board open and
  the console hidden, `Focus()` would find the board, return true, and the launcher would log
  `launch complete (window up)` — reporting success for exactly the dead-icon state the check
  was added to catch. The Python twin `_win_focus_existing_console` had the same rule.
- **Fix (v1463):** exact title only, plus an owning-PID filter (the launcher knows the pid it
  just spawned). Verified live: real pid → found, bogus pid → not found.
- **Prevention:** a liveness check must identify the thing by IDENTITY (exact title + owning
  process), never by a prefix that a sibling window can satisfy. A check that can be satisfied
  by something other than the thing it is checking is not a check.

## REG-056 — corrections to REG-053's evidence (2026-07-30)
- REG-053 said routing the icon to `start()` "with the existing `.png` candidate" would kill the
  window on any machine that has an icon file. The measurement is real, but **`tv_diablo_icon.png`
  does not exist in this repo** — I created it to run the A/B. No clean clone has an icon file,
  so the trap could not have fired from repo state, and the `.ico`-only guard added in v1462 is
  therefore unreachable today. The rule is still correct and worth keeping; the claim of imminent
  danger was overstated. Windows also now has no `.png` fallback at all — deliberate, but it was
  undisclosed.
- **Prevention:** when an experiment needs a file the repo does not ship, say so in the finding.
  Evidence produced by mutating the tree must be labelled as such or the next reader will
  reasonably believe it reproduces from a checkout.

## REG-057 — a new PC booted into the OWNER's world instead of its own (2026-07-30)
- **Symptom:** Konyo's cousin opens the console on a different PC and sees Konyo's forge defaults
  and seed floors — "it mimics my defaults".
- **Root cause:** the per-machine profile system already existed (the WINDOWS/MAC switch: MAC =
  owner, bare keys; WINDOWS = an isolated `W·` world with every owner seed floor suppressed), but
  `d2r_activeMachine` defaulted to `'mac'` whenever unset. A brand-new machine therefore landed in
  the owner's namespace until somebody manually flipped the switch.
- **Rejected fix — do NOT retry:** deriving the identity from the PLATFORM. The switch is NAMED
  WINDOWS/MAC but encodes WHOSE WORLD, not which OS — Konyo runs this console on Windows under the
  MAC identity, so platform-derivation flips the owner's own machine into the cousin shell and
  hides every tally/vault/chronicle row behind `W·`. Invisible data reads as lost data.
- **Fix (v1464):** decide on EVIDENCE, and only where it is unambiguous — a localStorage with no
  `d2r_*` key at all has never run this app, so it gets its own `W·` world; ANY `d2r_*` key means
  established, which keeps the historic `mac` default byte-for-byte. An explicit choice beats both.
- **Verify:** headless Chromium over HTTP (file:// cannot use localStorage), two-step so the
  assertion reads what the page really persisted: virgin profile → `d2r_activeMachine=windows`;
  profile seeded with `d2r_owned` and no machine key → `mac`.
- **Prevention:** (1) when a stored default is ambiguous between "never chosen" and "chose the
  default", do not guess from the environment — look for evidence that the app has run before;
  (2) a switch whose NAME (windows/mac) disagrees with its MEANING (whose world) will eventually
  be "cleaned up" by someone; the name is now documented in-code as identity, not platform;
  (3) namespace changes are data-loss-shaped even when nothing is deleted — the safe default is
  always the one that keeps an existing user seeing their own data.

## REG-058 — I reported a clipped console that was never clipped (2026-07-30)
- **Symptom (claimed):** the console clips its right edge at the default window size — the SCENE
  meter, the zone subtitle and the 6th KPI cut off. Reported twice, with screenshots.
- **It was false.** The capture harness called `GetClientRect`/`ClientToScreen` from DPI-UNAWARE
  PowerShell 5.1 against a DPI-AWARE window. It received `1105x700` — the virtualized size of a
  client that is really ~1657x1050 CSS px — and then cropped that many PHYSICAL pixels. The crop
  landed at CSS x≈1085, precisely where those three elements sit. The desktop strip visible on the
  left of the PNGs was the same offset error.
- **Ground truth:** rendering the real file in headless Chromium and reading
  `getBoundingClientRect` on every node under `.shell` gives ZERO elements past the viewport at
  1657, 1281, 1105, 1002 and 940 CSS px.
- **Consequence:** a typography rescale (4 tokens) built on the false premise was reverted before
  shipping. It would have SHRUNK a console that WebView2 already renders at 1 CSS px = 1 device px
  on a 150% display, i.e. made a physically-small UI smaller.
- **Prevention:** (1) a screenshot is not a measurement — if a claim is about geometry, read the
  geometry from the layout engine, not from a bitmap; (2) any Win32 measurement of another
  process's window must match DPI awareness with that process or it is silently virtualized;
  (3) when a UI bug is only visible through one tool, suspect the tool first.

## REG-059 — the identity model could not tell two Windows PCs apart (2026-07-30)
- **Symptom:** Konyo asked for a per-profile login symbol so his cousin could tell whose console
  he was in. Scoping it surfaced a deeper hole: Konyo runs FOUR machines (this Windows PC, a
  second Windows PC, a MacBook, the cousin's PC), but the v663 identity model is a 2x2 —
  `mac|windows` x `main|ladder`.
- **Root cause:** the model answers "whose world" (which storage namespace) and nothing answers
  "which box". Two Windows PCs both resolve to `W·` and would silently share one save with no
  indication anywhere in the UI that they were the same profile.
- **Fix (v1465):** a per-install identity in `tv/.tvd_identity.json` — an opaque uuid4 minted once
  and gitignored so it cannot travel between machines. Hostname/user ride along as LABELS only:
  two people can both be `Administrator` on `DESKTOP-PC`, so deriving the id from them would
  collide exactly where a collision is most damaging. Served on `/api/status`, rendered as a
  generated sigil (colour + rune + name + 4-char code) in the console header.
- **Design fix inside the fix:** the adjective and the colour were first hashed independently,
  which produced "AMBER ANVIL" rendered in blue. They are now index-locked so the spoken name and
  the seen colour always agree — the chip exists to be compared at a distance, and two channels
  disagreeing is worse than one channel.
- **Verify:** identity stable across calls; `git check-ignore` confirms the file is ignored;
  sigil read back from a live screenshot before and after the colour lock.
- **Prevention:** (1) an identity scheme must be sized to the real number of installs, not the
  number of platforms — "mac vs windows" was never an identity, it was an OS label doing identity
  work; (2) never derive a unique id from hostname/username, which collide on defaults; (3) if a
  visual identity has several channels, drive them from ONE index — independent hashes make the
  channels contradict each other and destroy the compare-at-a-glance property.

## REG-060 — a shell heredoc ate my JS escapes and broke the whole board (2026-07-30)
- **Symptom:** immediately after inserting the v1466 board sigil, `bible.html` threw
  `Uncaught SyntaxError: Invalid or unexpected token` at line 37727 — the entire board dead.
- **Root cause:** the block was inserted through a `bash << 'PY'` heredoc into a Python writer.
  The `\n` escapes inside the JS tooltip string did not survive as the two characters
  backslash+n; the file ended up with REAL newlines inside single-quoted JS string literals,
  which is a hard parse error. Unterminated-string, not a subtle bug — everything after it died.
- **Caught by:** the standing gate of loading the file in headless Chromium and grepping the
  console for `SyntaxError`/`Uncaught`. Without it this ships and the board is blank.
- **Fix:** re-inserted via the editor (no shell layer), and the tooltip no longer contains any
  escaped newline at all — it is built from an array and joined with `String.fromCharCode(10)`
  at runtime, so there is nothing left for a shell to eat.
- **Prevention:** (1) never author JS/CSS string escapes through a shell heredoc — use the file
  editor, or keep the payload escape-free by construction; (2) any edit to a 37k-line single-file
  app must be followed by an actual PARSE check, because a syntax error there is total, not
  local; (3) prefer runtime construction (`String.fromCharCode`, arrays + join) over escape
  sequences when the text has to survive several tools.

## REG-061 — a generated identity drawn twice can disagree with itself (2026-07-30)
- **Symptom (prevented, not observed):** the profile sigil is generated independently in the
  console (`tv/control_ui.html`) and on the board (`bible.html`). Both hash the same install id,
  but they are separate documents with separate copies of the glyph/adjective/hue/noun tables.
- **Why it matters:** if those tables drift by even one entry, the SAME machine renders two
  different crests — strictly worse than having no sigil, because the entire purpose is letting
  two people compare and conclude "same install" or "different install". A feature whose failure
  mode is a confident wrong answer needs a gate, not care.
- **Fix (v1466):** the ship gate asserts all four tables are byte-identical between the two files
  (24 glyphs, 16 adjectives, 16 hues, 16 nouns), and the adjective↔hue index-lock from v1465 is
  preserved in both copies.
- **Prevention:** duplicated derivation logic across surfaces must be equality-asserted in the
  gate, not maintained by discipline. If it cannot be shared, it must be checked.

## REG-062 — a zone numeral announced a movement that had no body (2026-07-30)
- **Symptom:** the Sessions surface showed "Ⅰ THE HUNT" and "Ⅱ THE MISSIONS" as headings over
  blank space, which is most of why the surface read as accumulated rather than designed.
- **Root cause:** `.zone-banner` and its body are SIBLINGS in the dash grid — neither owns the
  other. `#hd-taskforce` / `#hd-lastsession` ship `hidden` and are revealed only inside
  `if (rows.length)`, behind an early-return signature guard and a `try/catch` that swallows
  failures, so any throw or a pre-first-poll paint left the banner with nothing under it.
- **Fix (v1467):** `.home-dash > .zone-banner:has(+ .hd-col[hidden]) { display: none }` — CSS, so
  it cannot drift out of sync with the render path, and it degrades to the old behaviour on an
  engine without `:has()` (verified supported here, Chromium 150).
- **Prevention:** when a heading and its content are siblings rather than parent/child, the
  heading needs a content binding or it will eventually render over emptiness. The structural
  answer is a `<section>` that owns both — logged as the next round, not done here.

## REG-063 — the honest-idle rule missed the state right next to zero (2026-07-30)
- **Symptom:** at ONE recorded session the productivity row rendered six bright tiles reading
  `1 / — / 0 / 0 / n / n` — a wall of zeros, which is exactly what the "honest idle" work was
  written to prevent.
- **Root cause:** the resting teaching line is gated on `if (!n)`, i.e. it only fires at zero
  sessions. At n>=1 every tile renders at full brightness regardless of its value, and `.kpi-dim`
  was applied only to an ABSENT value (`'—'`), never to a real `0`.
- **Fix (v1467):** a real `0` is dimmed like an absent value. The data stays on screen — it is
  truthful and hiding it would be worse — it simply stops competing with the numbers that moved.
- **Prevention:** an "empty state" that only triggers at exactly zero will always have a near-
  empty neighbour that looks broken. Style by VALUE (is this number meaningful yet?), not only by
  COUNT (does any row exist?).

## REG-064 — a structural refactor broke the guard that watched it (2026-07-30)
- **Symptom:** wrapping each Sessions movement in `<section class="zone">` turned
  `test_control.py::test_zone_content_interleaved` red instantly.
- **Root cause:** the test extracted the dash with a NON-GREEDY
  `<section class="home-dash">([\s\S]*?)</section>`, which stopped at the first ZONE's closing
  tag once zones became sections — so it only ever inspected zone Ⅰ. The test's intent and its
  `expected` list were still correct; only the extraction was structure-dependent.
- **Second trap inside the fix:** the balanced tag scan counted the words `<section>` appearing in
  the new HTML COMMENTS as real tags, so depth never returned to 0 and it failed with
  "home-dash section never closes". Comments are stripped before scanning now.
- **The real risk here is not the red test, it is the temptation.** Editing a failing test until
  it passes silently destroys the guard, and this one protects a storyline order that has already
  regressed twice (v1424, v1449). So it was MUTATION-TESTED after the fix: swapping THE MISSIONS
  ahead of THE HUNT makes it fail; restoring makes it pass. Verified alive, not assumed.
- **Prevention:** (1) a test that parses structure with a regex is coupled to that structure —
  when a refactor reddens it, fix the EXTRACTION and leave the ASSERTION untouched, then prove it
  still fails on a real violation; (2) never balance-scan markup without stripping comments first;
  (3) any "fix" to a guard must be followed by a mutation check, or you have shipped a test that
  can only pass.

## REG-065 — an auto-written default is indistinguishable from a real choice (2026-07-30)
- **Symptom:** v1464 persisted `d2r_activeMachine='mac'` on every established install so the
  answer would be stable. When the product rule later changed to "only the MacBook keeps the owner
  world, every other PC starts fresh", that stored value blocked the new derivation — the Windows
  boxes looked like they had CHOSEN mac when nothing had ever chosen anything.
- **Root cause:** writing a derived default into the same slot the user writes their decision
  into. Once both live in one key, provenance is gone and the next rule change cannot tell whose
  intent it is about to override.
- **Fix (v1469):** record the author — `d2r_machineSource` is `'user'` (a click on the pill) or
  `'auto'` (derived). Auto values are re-derived on every load, user values are honoured forever,
  and an ABSENT marker (every pre-v1469 install) is treated as auto, which is what let the rule
  change take effect without touching anyone who had actually decided. `machineSwitch()` marks
  `'user'` — without that, the next reload silently undoes a real choice and the switch reads as
  broken.
- **Prevention:** never store a derived default in the same key as a user decision. If a value can
  be written by both the system and the human, it needs a provenance field, or the first rule
  change will either ignore real choices or trample defaults — and both look like data loss.

## REG-066 — one platform signal is not enough to decide whose data you see (2026-07-30)
- **Symptom:** the v1469 first cut derived identity from `navigator.userAgentData.platform` alone
  and resolved a MacBook to the WINDOWS world in test — i.e. the one machine that must keep its
  chronicle would have been sent to an empty one.
- **Root cause:** `userAgentData.platform` reports the host OS independently of the UA string, so
  a single source can disagree with the others. Any one signal being wrong decides whose data a
  machine sees.
- **Fix:** join `userAgentData.platform` + `navigator.platform` + `userAgent` and treat the
  machine as a Mac if ANY signal says Mac; everything else gets the isolated world. That is the
  safe asymmetry — a machine wrongly given its OWN world shows an empty console (recoverable, one
  click), while a machine wrongly given the OWNER's world shows someone else's chronicle.
- **Prevention:** when a detection decides data visibility, enumerate every available signal and
  choose the failure direction deliberately. Ask which way of being wrong is cheap.

## REG-067 — I wrote the window fix and never wired it up (2026-07-30)
- **Symptom:** the console kept spilling under the taskbar long after v1464 claimed to fix it.
- **Root cause:** v1464 defined `_win_nudge_onscreen()` and **never attached it to the `shown`
  event**. The sequence that produced it: I added the function, then removed its riskier sibling
  `_win_fit_to_workarea` (which had collapsed the window to 158x26), and the surviving function
  lost its wiring in the same edit. Dead code that reads like a shipped feature — the ledger even
  described the behaviour as delivered.
- **Caught by:** a SCREENSHOT taken for an unrelated UI round, which happened to include the
  taskbar sitting on top of the console. No test covered it, and the geometry check I had run
  earlier measured a window I had repositioned by hand, so it agreed with me.
- **Fix (v1470):** wired to `shown`; verified window bottom `y=1008` against work-area bottom
  `y=1008` — exact fit, measured DPI-aware from a fresh launcher-spawned window.
- **Prevention:** (1) defining a handler and registering it are two changes, and removing a
  sibling handler is exactly when the second one gets lost — grep for the registration, not the
  definition; (2) a fix whose only proof is a measurement taken after I moved the thing myself is
  not proof; re-launch clean and measure what the product does on its own.

## REG-068 — four spellings of one card surface (2026-07-30)
- **Symptom:** the console read as "accumulated" rather than designed, without any single element
  looking wrong.
- **Root cause:** `.hd-col`, `.kpi`, `.hh-card`, `.eh-organ` (plus `.hub-hero.idle`) each declared
  their own gradient and border for the SAME concept, differing only in the third decimal —
  `rgba(255,255,255,.022)` vs `.025`, `rgba(0,0,0,.32)` vs `.34` — and three different border
  colours. Individually invisible; collectively the reason nothing quite lined up.
- **Fix (v1470):** one `--card-bd` / `--card-bg` pair in `:root`, referenced by all of them.
- **Prevention:** a visual concept that appears in more than two rules needs a token the moment
  the second copy is written. Near-duplicate alpha values are the signature of a system being
  re-derived from memory instead of referenced.

## REG-069 — a forked key read RAW leaked the owner's data into another world (2026-07-30)
- **Symptom (latent, found by audit):** `d2r_rwMade` is ACCOUNT state — it forks per world via
  `_LP_FORKED`/`_WP_FORKED` — but one site read it with a raw `localStorage.getItem`. On a
  non-owner machine the "runewords sealed" mission status was therefore computed from the OWNER's
  runeword data, not that machine's.
- **How it was found:** not by reading the abstraction and trusting it, but by enumerating EVERY
  raw `localStorage.*Item` call in `bible.html` and intersecting the key names with the forked
  sets. 11 keys are touched raw; 10 are pointers/prefs that are correctly un-namespaced, and
  exactly one was account state.
- **Fix (v1471):** routed through `window.LSR`. Post-fix audit re-run: zero forked keys are read
  raw anywhere. The `L·`→bare merge near line 3509 still uses raw keys BY DESIGN — a one-time
  legacy migration has to address both namespaces literally, and that is correct.
- **Prevention:** a namespacing abstraction is only as good as its worst bypass. When one exists,
  the check is mechanical and cheap: intersect every raw access with the set of keys that are
  supposed to be namespaced, and require the result to be empty. That intersection is now a
  documented one-liner in the ledger.

## ARCH-001 — the storage re-key migration was scouted and deliberately NOT done (2026-07-30)
- **Proposal:** re-key account storage from the OS-label prefixes (`bare` / `L·` / `W·` / `WL·`)
  onto the v1465 per-install identity, so namespaces derive from the machine's identity rather
  than from an OS name.
- **Measured surface:** 49 forked account keys · 141 calls routed through `LSR` · 11 keys touched
  raw (10 legitimately, 1 a bug now fixed).
- **Decision: NOT SHIPPED, on the evidence.** `localStorage` is already per-machine, so `W·` is
  ALREADY unique to each PC — re-keying to `<installId>·` adds no isolation any real user would
  experience, while touching 49 keys holding chronicle, vault and forge state. The defect people
  actually felt was the NAMING ("Windows/Mac" describing whose-world), and that was fixable
  without moving a byte.
- **If it is ever revisited,** the blockers to solve first are: a reversible two-way mapping (users
  switch worlds and must not strand data), the one-time legacy `L·`→bare merge that assumes literal
  prefixes, and a rollback path that works when the app is offline. Do not start it without those.

## REG-070 — file handles leaked on the hottest paths in the app (2026-07-30)
- **Symptom:** the suites had been printing `ResourceWarning: unclosed file` all session, including
  one for `tvd_window_test.pid`. Nobody read them, because warnings scroll past a green OK.
- **Root cause:** five bare `open(...).read()` / `open(...,"w").write()` calls relying on refcount
  GC to close. The two that matter most are on hot paths: `_window_present()` (every launch and
  every takeover check) and the subscription-budget read (**every vision read** — thousands of
  handles across a farm session).
- **Why it is not merely untidy:** two of them are the PID FILES the launcher manages, and on
  Windows an open handle **blocks deleting or replacing the file underneath it**.
  `.tvd_window.pid` is precisely the file the cleanup path tries to remove, and "cannot delete,
  file in use" is the same failure shape that made a scratch worktree undeletable earlier in this
  same session.
- **Fix (v1472):** context managers everywhere; the two budget reads collapsed into one
  `_sub_budget_load()` that also returns `{}` on failure instead of each caller re-implementing it.
- **Verify:** `python -W error::ResourceWarning tv/test_control.py` → 0 unclosed-file warnings
  (was 2). Suites still 267 OK / 201 OK.
- **Prevention:** (1) a warning that only appears alongside a passing suite is invisible — run the
  suite under `-W error::ResourceWarning` when you want to know; (2) `open().read()` is never
  correct in long-lived code, and is actively harmful on Windows for any file you also intend to
  delete; (3) when the same leak appears twice, fix it in one helper rather than two `with` blocks.

## REG-071 — three correct numbers that read as a contradiction (2026-07-30)
- **Symptom (Konyo, live):** *"how come for forges ONE STEP is 91 if there are 99 forges to create?
  doesn't that counter it? I need this synced and accurate."*
- **Investigated, and the counts are NOT wrong.** Reconciled exactly:
  `99` runewords in `RUNEWORD_TIP` − `8` in `_RW_LADDER_ONLY` (Bulwark, Cure, Ground, Hearth,
  Hysteria, Mania, Metamorphosis, Temper) = **91 workable**, which is the ONE STEP pill; plus the
  `4` entries of the `CRAFTS` array = **95**, which is the ALL pill.
- **The real defect is legibility, not arithmetic.** Three numbers measuring three different
  universes sit inches apart on one screen: the bar counts RUNEWORDS (99), ONE STEP counts
  WORKABLE-ON-THIS-ACCOUNT (91), and ALL mixes runewords WITH craft types (95). The 8-word
  explanation existed only in a sentence further down the page, so the reader is left to derive
  the relationship — and the natural conclusion is "the app is miscounting".
- **Fix (v1474):** the progress bar states its own scope ("N / 99 runewords forged") and carries an
  inline note plus a full reconciliation tooltip, computed from the live data rather than
  hardcoded, so it cannot drift from the sets it describes.
- **Prevention:** when two counters on one screen have different denominators, the screen must say
  so. A number that is correct but unexplainable next to its neighbour will be reported as a bug —
  and the reporter is right, because trust is the feature.

## REG-072 — the Forge excluded 8 runewords the owner wanted planned (2026-07-30)
- **Ask (Konyo):** *"we need it for forge. i dont play ladder but we need it only for the forge
  specifically those 8-9 runewords."*
- **Before:** `_rwLadderBlocked()` removed the 8 `_RW_LADDER_ONLY` words (Bulwark, Cure, Ground,
  Hearth, Hysteria, Mania, Metamorphosis, Temper) from the Forge everywhere — task list, rune
  demand, base farming — because Konyo plays non-ladder (v553/v577).
- **Fix (v1475) — scoped by CALL SITE, not by a mode flip.** A second predicate,
  `_rwLadderBlockedForge()`, is asked by the four FORGE-lane sites (task universe, rune gating,
  base farming, host lookup). The other five sites keep the original: the runeword TABLE still
  hides them (the v577 display rule "Konyo plays NON-ladder, it should not be giving me these"),
  and the chronicle, stamps and elite-base filter are untouched. Flipping `d2r_ladderMode` would
  have changed all of them at once, which is not what was asked.
- **Honesty follow-through:** two pieces of on-screen text asserted the OLD rule and would have
  become lies — the progress note ("8 ladder-only" excluded) and the Forge banner ("8 ladder-only
  words remain"). Both now read the live setting instead of restating an assumption, and the
  banner says the words need a ladder character to actually form, so including them in the plan
  never reads as a promise that they will cube on this character.
- **Self-inflicted trap on the way (worth its own note):** the swap inserted a `//` comment
  MID-LINE into a single-line `forEach`, which commented out the rest of the statement and threw
  `Uncaught SyntaxError` at load — the whole board dead. Caught by the standing Chromium parse
  gate within a minute. Same class as REG-060: **never append a `//` comment to a line that
  continues after the insertion point** — use a `/* */` block above it.
- **Prevention:** when a rule should change for ONE surface, scope it by call site with a second
  predicate. A global mode flag is the tempting shortcut and it always takes surfaces with it that
  nobody asked to change.

## REG-073 — the syntax gate existed only in my hands (2026-07-30)
- **Symptom:** twice in one session an edit produced `Uncaught SyntaxError` that blanked a
  37k-line page (REG-060, REG-072). Both were caught ONLY because a human happened to run headless
  Chromium by hand. Nothing in the suite would have stopped either from shipping.
- **Fix (v1476):** `tv/js_syntax_gate.py` loads each surface in a real browser and fails on any
  console `SyntaxError`; `TestJsSyntaxGate` runs it as part of `test_control.py`. When no browser
  is present it SKIPS loudly rather than passing — a gate that cannot run must say so.
- **A hand-rolled tokenizer was tried FIRST and rejected.** It reported 14–16 problems on files
  that parse perfectly, because these pages use `${…}` templates with nested backticks, embedded
  HTML with quotes, and regex literals no heuristic separates from division. Two iterations of
  fixing it still left false alarms. **A gate that cries wolf is worse than no gate** — it trains
  people to ignore it, and then it misses the real one. Recorded so nobody re-attempts the
  tokenizer thinking it is nearly working.
- **Verified by mutation, not assumed:** injecting a raw newline into a quoted literal makes it
  fail on `bible.html` (reported `:37800`) and on `control_ui.html` (`:9881`); restoring passes.

## REG-074 — I walked into the documented trap and the suite still said OK (2026-07-30)
- **Symptom:** I appended `TestJsSyntaxGate` to the end of `test_control.py`. The suite reported
  `Ran 267 tests ... OK` — with my new test **never defined and never run**.
- **Root cause:** `unittest.main()` exits the interpreter, so any class below it is dead code.
  This is not a new discovery — **v1456 fixed exactly this and left a comment saying "Keep this
  block last"**. I appended after it anyway.
- **The lesson is about the fix, not the mistake:** a comment is not a guard. v1456 documented the
  trap and the trap still caught the next person (me), because documentation only works on people
  who read that part of the file before editing it.
- **Fix (v1476):** `TestRunnerIsLast` fails if any `class …(` appears after the top-level
  `if __name__ == "__main__":`, naming the stranded classes. Mutation-tested: stranding a class
  makes it fire, restoring makes it pass.
- **Second-order bug inside that guard:** the first version searched for the marker string
  unanchored, found the copy inside its OWN source, and failed on a correct file. Anchored to
  column 0. Guards need the same scepticism as the code they guard.
- **Prevention:** when a comment warns about a foot-gun, that is evidence the foot-gun is
  reachable — convert it to an assertion. Silent zero coverage that still prints OK is the worst
  failure mode a test suite has.

## REG-075 — v1475 changed the wrong gate; the UI then contradicted itself (2026-07-30)
- **Symptom:** after v1475 the Forge note read *"all 99 planned here (8 ladder-only included)"*
  while the pills still read **ALL 95 / ONE STEP 91**. The screen argued with itself — strictly
  worse than the original state, because now one of the two was provably lying.
- **Root cause:** v1475 swapped four `_rwLadderBlocked()` call sites to a Forge-scoped predicate.
  But the task BUCKETS are gated by a **different function** — `_rwBlocked()` (line ~31620) — which
  returns `'ladder'` and diverts the word into the read-only `out.ladder` strip, out of
  `now`/`pipeline`/`onestep` entirely (v632). The four swapped sites governed rune demand and base
  farming; none of them governed the counts.
- **How it was caught:** by launching the app, clicking to the Forge and READING THE PILLS. The
  code change was self-consistent and reviewed; only the running product showed the contradiction.
  A grep for the predicate name could never have found a differently-named gate.
- **Fix (v1477):** `_rwBlocked()` consults `_forgeIncludeLadder()` before returning `'ladder'`.
  Verified live: **ALL 103 · ONE STEP 99 · CRAFTS 4**, matching the note (99 runewords + 4 craft
  types = 103).
- **Prevention:** (1) when a behaviour is spread across several predicates, changing one and
  shipping is a guess — enumerate every gate that can exclude the thing BEFORE editing, and note
  that they may not share a naming convention; (2) any change that alters a COUNT must be verified
  against the rendered count, not against the diff; (3) the failure mode to fear is not "no
  effect", it is "half an effect" — a UI that half-changed now states two different truths.

## REG-076 — the console kept its own copy of the fork rule, and the copy was stale (2026-07-30)

- **Symptom:** Sessions showed `HOLY GRAIL 243 / 403 · 60% claimed` on a Windows machine that
  v1469 had already placed in its own fresh `W·` world. Konyo: *"the sessions feels still like its
  attached to my macbook profile. but i want this fresh and new.. same for my cuzin."*
- **Not the board.** A virgin Chrome profile proved the board seeds nothing on a new machine:
  `D2R_MACHINE=windows`, `machineSource=auto`, `bare d2r_foundLog len = 0`, `W· d2r_foundLog
  len = 0`. The grail-seed suppression added in v1469 works. So the number was not being written —
  it was being READ from somewhere it should not have been.
- **Root cause:** `tv/control_ui.html` shares an origin with the board and reads the chronicle
  directly out of `localStorage` via its own `lsFork()`. That was a hand-copied SECOND
  implementation of the board's fork rule (`bible.html` `LSR.key`), and it still asserted:
  `// machine fork (W·/WL·) never applies on this Mac console.` True when written, false the
  moment a Windows PC got its own world. The board wrote `W·`; the console read **bare**. It also
  ended in `getItem(bare) || getItem('L·'+bare)` — so even a corrected prefix would have fallen
  back to the owner's data whenever this PC's key was absent, which is precisely the state of a
  fresh machine. The fallback WAS the leak.
- **Blast radius:** every console read — `d2r_forgeSummary` (the grail crest), `d2r_craftReady`,
  `d2r_grailFarm` (the next-grail hero), `d2r_createNowAi`, `d2r_tvdTallyLog`. All five are in the
  fork sets, so all five showed the owner's world on every non-owner machine.
- **How it was caught:** by trusting the user's report over the code. The board had been proven
  clean twice, so the remaining possibility was an un-forked READER — the same hunt that found
  REG-069. Enumerating every `localStorage.getItem('d2r_…')` in the console found three raw reads;
  two were pointers (correctly bare) and the third was inside `lsFork` itself.
- **Fix (v1478):** the rule is published as DATA, not copied. `bible.html` writes `d2r_lsrRoute`
  (`{v, m, p, lp[], wp[]}`) right after it builds `LSR`; the console routes from that payload. On
  THIS PC there is **no bare fallback** — an absent key is a true empty and zero is the correct
  answer. With no route at all the console forks EVERY key rather than none: the worst case is an
  honestly-empty crest, where the opposite guess shows one person another person's progress.
- **Prevention:** (1) this is the THIRD of its family — REG-069 read a key raw, REG-075 gated on a
  differently-named function, REG-076 kept a private copy of the rule. The pattern is *a second
  place that decides the same thing*; the durable fix is to delete the second place, not to
  re-sync it. (2) All three survived a careful code reading, so the guard is behavioural:
  `TestConsoleReadsTheActiveWorld` extracts the SHIPPED `lsFork` and executes it in a real JS
  engine across six world/seed combinations, including "this PC empty, owner populated".
  Mutation-verified: restoring the bare fallback turns it red with `read 'owner'`. (3) A comment
  stating a scope limit ("never applies on this…") is a claim with an expiry date — when the scope
  changes, that comment is the bug.

## REG-077 — two gates passed their check and then failed reporting it (2026-07-30)

- **Symptom:** `visual_lock_invariant.py` and `tv/js_syntax_gate.py` both exited **1 on a clean
  tree**. Both had actually PASSED: they reached the success branch and died inside
  `print("✅ …")` with `UnicodeEncodeError: 'charmap' codec can't encode character '✅'`.
- **Root cause:** this machine's console codepage is Hebrew (cp1255) and cannot encode the check
  mark. The gates had only ever appeared green because `PYTHONIOENCODING=utf-8` was being set by
  hand off-screen — so their verdict depended on the operator's shell rather than on the code.
  Identical in kind to REG-054, which was the same discovery about the test suites.
- **Fix (v1478):** both gates reconfigure `stdout`/`stderr` to UTF-8 with `errors="replace"` before
  printing anything. Verified by plain runs with no environment variables: both exit 0.
- **Prevention:** a gate that cannot REPORT is a broken gate, and its failure mode is the dangerous
  direction — a false RED trains people to ignore it, and the next real failure is ignored too.
  Any script whose verdict is its exit code must make its own output encoding-safe rather than
  inherit it. Never run a gate with an env var that its normal invocation would not have; if it
  only passes with help, it does not pass.
