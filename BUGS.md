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
