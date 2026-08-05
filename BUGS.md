# v21_kai → v21_kai_fixed bug tracker

> ⚠ **DUPLICATE REG NUMBERS — read the DATE, not just the number.** REG-002 and REG-083…REG-087
> were each allocated twice: once on **2026-07-31** and again on **2026-08-01**, for different
> bugs. Ten entries, five numbers. They are NOT renumbered because commit messages already cite
> them (v1516, v1518, v1529, v1536, v1539 among others) and rewriting a number would break the
> only link between a bug and the ship that fixed it. Every duplicated heading now carries its
> date, so the pair can be told apart at a glance. New entries continue from REG-088.

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

## REG-133 — longest-match picked the one name with no art, and the whole daily-pick bridge died on it

**Symptom.** Konyo, repeatedly ("ive said this before"): the DAILY TASK FORCE pick renders its item
names as flat text — no set green, no HD art, no floating card, nothing clickable.

**Why it kept surviving "fixes".** The CONSUMER was never broken. tv/control_ui.html has built the
full treatment since v1636/v1644 — `_aiMarks` + `_aiChip` give every name it can stand behind an
`_itemArtImg`, an `_itipAttr` card, `_rarCls` colour and keyboard routing, for the piece AND its set.
It was working perfectly on an empty payload, so every inspection of the console found correct code.

**Root cause (board side).** `_syncCreateNowAiArt` collects every known item name appearing in the
pick sentence and keeps the LONGEST. Measured on his exact sentence:
`"Sets · 108/135 pieces — finish Tancred's Battlegear (1 piece left: Tancred's Hobnails)"`
- `Tancred's Battlegear` (20 chars) — the SET AGGREGATE. `artUrl()` -> **null**
- `Tancred's Hobnails` (18 chars) — the PIECE. `artUrl()` -> `art/hd_leather_boots.png`

Longest won, so `hit` was the aggregate, `art` came back null, and the `!art` guard threw the ENTIRE
payload away (`removeItem`). **Measured before the fix: the published payload was `null`.** The block
immediately above had added set PIECES to the pool for this very sentence, noting "the aggregate has
no art and the piece was not in the pool" — and then longest-match handed the win back to it.

**Fix.** Length is a TIE-BREAKER, not the criterion: a candidate that resolves art always beats one
that does not; among those, longest still wins. A wholly artless match is kept only as a last resort
and still bails — the bail was right, the CHOICE feeding it was wrong.
Measured after: `{"name":"Tancred's Hobnails (light plated boots)","art":"art/hd_leather_boots.png","rarity":"set"}`.

**Second link in the same chain (console side).** The board publishes the CANONICAL name so `artUrl`
and the routers resolve the entry the app knows — and a set piece's canonical name is SLOT-SUFFIXED.
The console matched that literal against prose that says only `Tancred's Hobnails`, so `indexOf`
failed and no mark was built. A mark now carries both: `nm` is what to FIND in the sentence, while
art/tip/routing stay keyed to the canonical entry. **Fixing only the board would have looked like it
changed nothing** — which is likely why this survived several passes.

**Prevention.** When a display is inert, ask whether the CONSUMER is broken or whether it is being
handed nothing. Both look identical on screen, and only one is visible in the code.

**Not proven.** The board half is red-then-green (payload `null` -> populated). The console half is
NOT visually confirmed: a seeded harness renders the DAILY PICK row but never produced a `.tf-nm`
node, so the dressed name has not been SEEN painted. Confirm on the live console with one hard reload.

## REG-132 — the Forge chronicle painted a runeword name in CRAFTED orange, and a stale spec demanded it

**Symptom.** Konyo, on the Forge tab: "forge color needs fixing". Every row of the Sealed Chronicle
(Wrath, Peace, Bramble, Unbending Will...) rendered ORANGE.

**Caught by.** His eye. No spec asserted `.rwc-name`'s colour at all — the two specs that touch that
class (v369, v434) only read its `textContent`.

**Root cause.** `bible.html` `.rwc-name` used `color:var(--q-orange)` — #ffa800, which is CRAFTED
quality. The board's settled truth keeps three concepts apart that keep collapsing into one another
(tv/control_ui.html:28-46, verified by Konyo in his OWN install at
`data/global/ui/layouts/_profilehd.json`, not from a forum):
- a completed **RUNEWORD'S NAME** is FontColorGoldYellow **#c7b377** — the same gold as a unique
- **#ffa800** is **CRAFTED**, "never a runeword"
- **#ff7d3c** is the **RUNE ITEM** hue (El, Eld — the things you collect), living as `--rune`

A chronicle row names a *finished runeword*, so it is the first of those and was wearing the second.

**And the same mistake was ALSO frozen into a test, where it had been failing CI.**
`tests/v311_unified_rarity.spec.ts` asserted `.arw-name` must compute `rgb(255,168,0)` — crafted
orange — under the title "runeword names render in orange (their in-game colour)". v1627 moved the
runeword hue to gold and the app followed; that spec did not. It has been red ever since, and it
asserted the **opposite** of `tests/v1628_board_quality_tokens.spec.ts:205`, which requires
`.arw-name` to use `--q-unique`. **Two specs demanding different colours for one surface means one is
wrong, and the wrong one is whichever contradicts the game.**

**Fix.** `.rwc-name` → `var(--q-runeword)` (which resolves to `--q-unique` on purpose). v311's
assertion re-pointed at `rgb(199,179,119)` with the reasoning recorded inline. NOT a test relaxed to
make a build pass — it still fails if the colour drifts anywhere else.

**Prevention.** The durable lesson is that **a colour is a fact about the game, not a taste**, so the
disagreement was always resolvable by looking rather than debating — and it stayed unresolved for
19 versions because the two sources of truth were a CSS token and a test literal, neither of which
reads the other. Note the remaining smell, deliberately NOT swept here: `.arw-rune-txt`,
`.mw-rune-chip` and `.rn-name` name RUNE ITEMS but paint `--q-orange` instead of `--rune` #ff7d3c.
That is the third concept above and it is a separate change with its own spec exposure.

**Verified.** 18/19 passed across v311, v369, v1628 and v434. The single remaining failure
(`v1628:368`, the F·Uniques thumbnail-name test) was proven pre-existing by stashing this change and
re-running it: it fails identically without it. It is the Pindleskin `bossId:'nihl'` vs
"Hell TZ Pindleskin" title mismatch already known from v1643.

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

## ARCH-002 — three defects, one root: a per-world key reached without the router (2026-07-31)

- **The family:** REG-069 (`d2r_rwMade` read raw — the cousin saw the owner's forged runewords),
  REG-075 (a differently-named gate — the Forge counts contradicted their own note), REG-076 (the
  console's private `lsFork` — a fresh PC showed the owner's `243/403` chronicle). Different files,
  different authors, different symptoms, one root: a key that belongs to a per-machine or
  per-account world was touched without going through the router.
- **Why individual fixes were not enough:** each was fixed on its own and the family kept
  producing new members. All three passed a careful code reading; the third needed a user report.
  The class is invisible to review because the wrong code looks exactly like the right code — the
  only difference is which accessor it went through.
- **Fix (v1479):** `TestForkedKeysAreRouted` fails any `localStorage.getItem/setItem/removeItem`
  on a key in `_LP_FORKED`/`_WP_FORKED`, in either surface, that is not `LSR.*` (board) or
  `lsFork()` (console). The fork sets are parsed out of `bible.html` at test time, so adding a key
  to a set automatically extends the gate — there is no second list to maintain.
- **The escape hatch, bounded:** the one-time migrations legitimately name `L·`/`W·` explicitly and
  must run regardless of the active world. They stay legal via an inline `/* raw-ok: why */`
  marker, which turns the exemption into a deliberate, reviewable act. A second test caps the
  exemption count (currently 8, max 12) so the marker cannot become a habit that silences the gate,
  and also asserts the count is non-zero — otherwise a rewrite that dropped the markers would leave
  the gate passing without ever having been tested against real raw code.
- **Mutation-verified:** an injected `localStorage.getItem('d2r_forgeSummary')` is reported with
  file, line and the offending call, plus the two routed alternatives.
- **Prevention:** when the same defect arrives a third time, stop fixing instances and make the
  invariant mechanical. The question to ask is not "is this line correct" but "what would have to
  be true for this line to be impossible".

## REG-078 — a version assertion that had been wrong for ~600 versions, hidden by a crash (2026-07-31)

- **Symptom:** `tv/test_button_matrix.py` reported `FAILED 1: version stamp: v1478` against a
  correct build. The assertion was `re.match(r"^v8\d\d", ver)` — written at v849, correct for
  fifty versions, and wrong for every build from v900 onward.
- **Why it survived ~600 versions:** the script crashed with `UnicodeEncodeError` on this Hebrew
  console before its verdict could be read (REG-077's family). A tool nobody can read is a tool
  nobody runs, and a stale assertion inside it is invisible. The two defects protected each other:
  the crash hid the bad check, and the bad check meant fixing the crash looked like it would only
  reveal a failure.
- **How it was caught:** fixing the encoding first. Within one run the matrix printed a real,
  specific failure it had been sitting on.
- **Fix (v1480):** the check now compares the live app's `/api/status` version against
  `tv/WINDOWS_SHIP.json`. That is what the check was FOR — stamp drift — and it stays true at any
  version number instead of encoding one moment in the version march. It also now catches something
  genuinely useful: a running app that is an older build than the tree under test, reported as
  "restart it before trusting this matrix".
- **Prevention:** (1) never assert a version by a numeric-range pattern; compare against the file
  that declares the version, so the check ages with the product. (2) Fix reporting bugs FIRST — a
  tool that cannot speak is hiding whatever it was going to say, and the hidden thing is usually
  real. (3) Two bugs that mask each other are not twice the work of one; they are much harder to
  see, because each makes the other look like expected behaviour.

## REG-079 — a suite outside the gate set rotted for ~100 versions (2026-07-31)

- **Symptom:** `tv/test_routes.py` exited 1 with two failures in `TestSuperAnalyzeKai`. It had been
  failing continuously since v1381.1.
- **Root cause:** v1381.1 deliberately reversed which stash panels feed the item judge. Its
  forensic note is explicit — perfect gem grids were being super-judged as tooltips, which returned
  `429` / "no rare" while the tally counts never ran at all — so `stash-runes|gems|materials` became
  TALLY RECOVERY (gap-funnel + rune/gem/material intake) and plain `stash` stayed item-judge input.
  The code was changed; these two tests, which encoded the opposite rule, were not.
- **Why it survived:** `test_routes.py` is not in the gate set that gets run before a ship. A suite
  nobody runs cannot fail loudly, so its verdict decays into decoration. The suite still *passed*
  181 of 183 assertions, which is the trap — a mostly-green orphan looks maintained.
- **Fix (v1482):** both tests realigned to the shipped doctrine, plus a third that pins the
  exclusion against a HIGH router confidence — the incident frame was exactly the one that scores
  well and belongs to another organ, so "excluded" must not be something a strong score can
  outvote. 183 OK, exit 0.
- **Prevention:** a test suite that is not in the gate set is not a test suite. See v1483, which
  makes an unreferenced `tv/test_*.py` a failure in its own right — the fix for this defect is not
  the two assertions, it is that nothing was watching them.

## REG-087 — applying a read DELETED a set piece you already owned (2026-08-01, v1539)
- **Symptom:** none. That is the whole problem: your F-Sets count went DOWN, silently, and for a
  SEEDED piece it could never come back.
- **Caught by:** the deliberate hunt for REG-083's class (a name called in one script/IIFE scope and
  declared in another) — the first thing that hunt found, and the worst.
- **Root cause:** `_setHave` is declared inside the IIFE at `bible.html:33155`; both call sites
  (36765, 36848) are in the IIFE at 35817, and nothing ever published it. The guard reads
  `hv = (typeof _setHave === 'function') && _setHave().has(key)` — and **`typeof` on an UNDECLARED
  name does not throw**, it returns `'undefined'`. So `hv` was permanently FALSE, the catch never
  ran, the owned-piece early-return never fired, and `toggleSetPiece(key)` ran against a piece
  already owned.
- **Why that is destruction, not a no-op** (bible.html:18607-18625): the toggle (1) `delete fl[piece]`
  from `d2r_foundLog` — the found date is gone; (2) writes `d2r_grailUnfound[piece]=1`, so the boot
  seed floor can **never re-assert it**; (3) `setPieces.delete` + persist.
- **Proof it was a mistake, not a design:** one line above at 36847 the `uni` branch guards with
  `_gFound`, which IS published (`window._gFound`, 15093) and returns early correctly. Same guard,
  same intent — alive for uniques, dead for sets.
- **Fix:** publish `window._setHave` beside the declaration (a shim, not a ported copy — the same
  function feeds fsetsScan, toggleSetPiece and _chronAlreadySet), point both call sites at it, and
  KEEP the typeof guards so they become real load-order guards instead of dead ones.
- **Prevention:** `tests/v1539_setpiece_deletion.spec.ts` — owns a real piece, applies a read naming
  it, and asserts the piece survives, the found date survives, and `d2r_grailUnfound` is NOT written.
- **Lesson, and it is the sharpest one this class has produced:** `typeof x === 'function'` on a
  name from another scope is not a guard, it is an OFF SWITCH — and unlike a bare call it does not
  even throw, so no catch fires, no console error appears, and the code takes the other branch
  forever. Every `typeof someBareName ===` in a multi-IIFE file deserves the question: can this
  scope actually SEE that name?

## REG-086 — TV_SESSIONS isolated 1 of 11 journal sites (2026-07-31)
- **Symptom:** an isolated harness (private ports, fixture journal via `TV_SESSIONS`) returned **25
  receipts of Konyo's REAL session data** from a fixture seeded with four rows. Found while verifying
  the v1457 honesty surfaces — the fixture's gate-refused row never appeared because the fixture was
  never being read.
- **Root cause:** `TV_SESSIONS` has existed since v877 and exactly ONE of eleven `sessions.jsonl`
  sites honoured it; the other ten hardcoded `HERE/sessions.jsonl`. **Five of those ten APPEND**, so a
  test that believed it was isolated could have written into the record of his real farming nights.
- **Fix (v1493):** one `_journal_path()` resolver; every reader and writer goes through it.
  (Self-inflicted detour worth recording: the blanket replace rewrote the resolver's OWN body into
  `return … or _journal_path()` — infinite recursion, caught immediately by the suite.)
- **Prove:** `TestV1493JournalIsolation` — exactly ONE site may construct the path, reads redirect to
  the fixture, `_kai_journal_rows()` returns the fixture's single row, and the real journal's size and
  mtime are unchanged after the test.
- **Prevention:** an env override that only some call sites honour is worse than none — it buys false
  confidence. One resolver, asserted by a test that counts the construction sites.

## REG-088 — the dead-click sweep called an idempotent click dead (2026-07-31)
- **Symptom:** the LAST Routine-I red after REG-084/087 — `platform_routing_audit` →
  `[calc] .item-tile #0 ("Key of Hate") → no state change`, failing on both the original and the retry.
- **Root cause:** the sweep visits **bosses before calc**, and Key of Hate is The Summoner's signature
  drop — so that item was ALREADY the live selection by the time the sweep clicked its calc tile.
  Re-clicking the item you are already looking at cannot change state, and that is correct behaviour:
  the bug class this sweep guards is a click that goes NOWHERE, not one that goes where you already are.
  Invisible before REG-084 because the cousin world's grid put a different item at index 0.
- **Fix (v1494):** exempt a click whose target is the live selection AND whose detail is on screen —
  narrow on purpose, so a genuinely dead tile cannot hide behind a name collision.
- **THE PROCESS LESSON (the reason this entry exists):** the failure text said only "no state change",
  so the first fix was a GUESS — a re-selection dance that cost a 6-minute run and did not work. Adding
  the state signature to the message answered it on the next run in one line
  (`before: sel="Key of Hate" act="Key of Hate" detailShown:true`). The signature now ships in every
  dead-click report. Same law as REG-047 and REG-083: **instrument, then fix — never fix, then hope.**
- **Prove:** `platform_routing_audit` 8/8 locally, deterministic (it was intermittent before REG-084
  because the world differed between local and CI).

## REG-087 — four specs pinned to superseded truths (2026-07-31)
- **Symptom:** the last four Routine-I reds after REG-084 — `v632_ladder_visibility`,
  `v634_ladder_preview`, `v552_forge_flagship_visual`, and a flaky `platform_routing_audit`. They fail
  locally with AND without the v1491 UA pin (proved by reverting the config), so the pin exposed them
  rather than causing them: the cousin world has no owner seed, so nothing was unmade to place and the
  assertions never bit on CI.
- **Root cause:** **the product moved and the specs did not.** v1475 answered Konyo — *"we need it for
  forge. i dont play ladder but we need it only for the forge specifically those 8-9 runewords"* — by
  PLANNING the 8 ladder-only words in the Forge lane instead of parking them in a read-only strip. So
  `forgeScan().ladder` is empty and `#forge-ladder-strip` absent BY DESIGN whenever
  `_forgeIncludeLadder()` is on (its default). v632/v634 asserted the pre-v1475 home. Separately,
  v1474 rewrote the Chronicle meter caption to "0 / 99 runewords forged · all 99 planned here
  (8 ladder-only included)" and v552 was matching the exact old phrasing `/\/\s*99 forged/`.
- **Fix (v1493):** v632 asserts the invariant FIRST (no unmade word is silent, ever) and then the home
  for the setting that is actually set; v634 turns the setting off through the product's own switch
  (`_forgeSetIncludeLadder(false)`) so the preview it covers has content; v552 asserts the contract
  (a made/total label naming the 99-word universe + the word "forged") instead of one phrasing.
- **Prove:** all four spec files green locally, and `platform_routing_audit` passes on retry.
- **Prevention:** assert the CONTRACT, not the copy; and when a feature has a setting, drive the
  setting instead of inheriting whichever side its default is on.

## REG-086 — the stash crops were calibrated on Konyo's MacBook, and only his MacBook got them (2026-08-01, v1536)
- **Symptom:** Konyo: *"THE AI READERS arent working properly my cuzin just did a ON AIR and it
  didnt read his runestash."* Reading worked on the Mac and not on the cousin's Windows box.
- **The lead was his:** *"there might be something to do with resolution for MACBOOK/WINDOWS? we had
  that situation for the AI INTAKE and we properly recalibrated it."* He was right.
- **Root cause:** `tv/stash_eye.py` line 5 states it outright — the crop fractions are
  *"LOCKED fractions (aspect 1.45–1.62, W≥1200 fullscreen D2R)"*, measured on 2940×1912 (1.538).
  That band is MacBook: 16:10 = 1.60, 3:2 = 1.50. A normal Windows monitor is **16:9 = 1.778, outside
  the gate**, so every one of the cousin's frames took the else-branch — the "foreign/windowed"
  fallback of `im.crop((0, 0, w*0.46, h))`.
- **Measured:** on 1920×1080 that hands the reader a **954k-pixel slab** where the Mac gets a
  **177k-pixel band** — the grid arrives **5.4× more diluted**, for both the tab-strip OCR and the
  grid fingerprint. Not a subtle degradation; a different picture.
- **Fix:** `crops_for_aspect(layout, aspect)`. D2R scales its UI with HEIGHT and anchors the stash
  panel to the left of the viewport, so a panel spanning fraction x of the width at aspect a0 spans
  `x * (a0/a1)` at a1; the vertical fractions do not move. Konyo's Mac returns the LOCKED band
  byte-identical (first test in the suite). 16:9 now gets a 153k-pixel band — within 14% of the
  Mac's, which is what it should be, since the panel is the same physical size.
- **Still honest:** DERIVED, not yet measured on a real 16:9 stash frame. Said so in the source and
  asserted by a test, because a fix nobody has checked against the real thing is a claim.
- **Prevention:** `tv/test_stash_eye_aspect.py` (9 tests) — the Mac band frozen, the derivation's own
  claim checked (panel width per unit height equal across aspects), windowed frames still refused a
  band, and absurd aspects kept inside the frame. Plus `tv/live_miss_audit.py`, which names WHICH of
  the five links broke on any machine's journal, so the next report is evidence instead of a guess.
- **Lesson:** a constant measured on one machine becomes a machine-specific feature the moment a
  gate is wrapped around it. The gate here was honest about its range and nobody noticed that the
  range WAS the Mac — the comment said "1.45–1.62" where it meant "Konyo's laptop".

## REG-085 — the cousin-world spec never visited the cousin world (2026-07-31)
- **Symptom:** both `v663_machine_shell` tests red on CI *and* locally, on every version — and red
  identically with and without the v1491 UA pin, so not caused by it.
- **Root cause:** the spec ascends with `localStorage.setItem('d2r_activeMachine','windows')` alone.
  The board only honours a stored machine when `d2r_machineSource === 'user'`; otherwise it
  AUTO-DERIVES from the platform and **overwrites the key it was just handed**. Measured: after the
  spec's ascend, `D2R_MACHINE` = `mac`, `d2r_activeMachine` = `mac`, `source` = `auto`. Both tests
  then asserted W·-world facts from inside the MAC world.
- **Fix (v1492):** a `setMachine(page, m)` helper writes BOTH keys — what the console's own master
  switch writes — so the spec drives the product the way the product is driven. (First attempt put the
  helper in module scope and called it inside `page.evaluate`, where it does not exist; it runs in the
  page now.) Clean-up sites drop `d2r_machineSource` too, so no test inherits a pinned world.
- **Prove:** `v663_machine_shell` 2/2 green locally, first time.
- **Why it mattered beyond one spec:** this is the dedicated cousin-world coverage cited as the reason
  the v1491 Mac-UA pin is safe. That justification was hollow while the spec sat in the mac world.
- **Prevention:** when a product setting has a guard key, a test that sets the value without the guard
  is testing the default — silently. Drive the switch the way the UI drives it.

## REG-085 — the pill asked for a name and no gesture could give one (2026-08-01, v1529)
- **Symptom:** Konyo: *"the sigil. NAME ME it says but i cant really name it.. lol when i click it it
  just says copied."*
- **Root cause — THREE faults stacked, each hiding the next:**
  1. **The invitation and the action were different gestures.** The pill said "name me"; a click
     copied the install id. Naming was on DOUBLE-click, hinted only inside a tooltip he would have
     had to hover to find.
  2. **The naming path probably never worked at all.** It called `window.prompt()`, which
     pywebview's WebKit backend does not reliably implement — so in the app window, the only place
     this console runs, a double-click could silently do nothing. Shipped v1496, never verified in
     the real window.
  3. **Its failure could not be reported.** All three `toast()` calls in that flow live in the
     SECOND `<script>` block, and `toast()` is declared in the first — REG-083's exact shape,
     second instance. Every one threw a ReferenceError inside its own try/catch and vanished.
- **And a fourth, found while fixing:** `.sigil { display: inline-flex }` outranks the UA rule the
  `hidden` attribute depends on, so `el.hidden = true` on that pill had never hidden anything —
  including at boot, where the placeholder crest showed before identity loaded.
- **Fix:** clicking an unnamed pill opens an INLINE field (real DOM, no dialog); Enter saves, Escape
  and click-away cancel without committing a half-typed word; double-click still renames a named
  machine; `toastC()` declared in the block that uses it; `.sigil[hidden] { display: none }`.
- **Prevention:** 9 specs drive the real console UI, including one that asserts NO dialog is
  involved in naming and one that asserts a failed save is reported.
- **Lesson:** when a control asks for something, the obvious thing done to it must be the way to
  give it. And a `try/catch` around a call is not proof the call exists — it is the most common way
  to make a missing function look like a working one.

## REG-084 — the suite spent 30 versions testing a world it was never written for (2026-07-31)
- **Symptom:** Routine I went from FULL GREEN at v1459 (235 passed, 0 failed) to **100 distinct spec
  files red** by v1489 — every one of them green on the Mac. v1490's sigil fix took that to 60, with
  zero new failures, and the remainder clustered in vault / mule / intake / locker / craft persistence.
- **Root cause:** `devices['Desktop Chrome']` ships a **"Windows NT 10.0" user agent**. The board derives
  its storage world by joining EVERY platform signal (`userAgentData.platform` + `navigator.platform` +
  `userAgent`) and asking `/mac|iphone|ipad|ipod/`. On Konyo's Mac the platform probes still say
  "MacIntel", so the world stays `mac` and keys are bare. On the Linux CI runner nothing says mac, so
  the world becomes the isolated **`W·` COUSIN world** — `W·d2r_wishlist`, `W·d2r_muleAssign`, … —
  while **105 spec files** address the BARE keys. The v1477-v1488 world-routing work did not break the
  app; it made the suite's hidden assumption load-bearing, and only the Mac could hide it.
- **Fix (v1491):** the chromium project declares a Mac user agent. The subject of this suite is Konyo's
  Mac world; saying so beats inheriting it from whichever host runs the job. No spec depends on the old
  UA (checked), and the cousin world keeps its dedicated coverage in `v663_machine_shell.spec.ts`, which
  sets the machine by hand.
- **Prove:** the world resolution was measured in both directions locally by forcing `d2r_activeMachine`
  (`d2r_muleAssign` → bare on mac, `W·d2r_muleAssign` on windows). CI is the verdict on the rest.
- **NOT fixed by this:** `v663_machine_shell` fails identically WITH and WITHOUT the change — it was
  already red locally and on CI before it, and wants its own session.
- **Prevention:** a test harness must state which world/profile it is exercising. Inheriting that from
  the host means the same suite asserts different things on different machines — and the machine the
  author uses is always the one where it looks fine.

## REG-084 — spoofing one browser tell cost the specs their whole world (2026-07-31, v1518)
- **Symptom:** `v606_finish_ascend_fx` × 2 red on CI shard 5/6. The milestone epic never fired; the
  overlay that DID appear said "⚒ YOUR FIRST RUNEWORD ⚒" — the app believed forge #1 on a chronicle
  the spec had just seeded to 59.
- **Caught by:** Routine I on v1515. bible.html was byte-identical to v1508 except its build stamp,
  so the red could not be from that arc — which is what made it worth instrumenting instead of
  recalibrating.
- **Root cause:** v1499 (identity worlds) makes a browser a GUEST until claimed, and identifies the
  SUITE by `navigator.webdriver === true && location.protocol === 'file:'`. This spec's first line
  spoofs `navigator.webdriver` to **false** — legitimately, to unmask the motion effects the app
  silences under automation — and in doing so unmasked itself as a guest. Instrumented proof:
  `LSR.key('d2r_rwMade')` → **`I·5ed9ad2c·d2r_rwMade`**, count 1, while the spec's seed of 59 sat in
  the bare key nobody read.
- **Fix:** the three spoof sites (v606 ×2, v618 ×1) now also
  `localStorage.setItem('d2r_ownerClaim','*')` — which is simply true: the suite IS the owner world.
- **Prevention:** `v1518_webdriver_spoof_guard.spec.ts` makes the pairing structural — spoof the
  tell, claim the world, or fail with the reason. It also asserts the `'*'` claim still exists in
  bible.html, so the fix cannot quietly become a no-op, and asserts it found at least one spoofer, so
  a drifted regex cannot leave the guard protecting nothing.
- **Lesson:** when a feature derives identity from a browser property, every place that MOCKS that
  property becomes a caller of the feature. The spoof and the breakage lived in different files
  written months apart, and the symptom pointed at neither.

## REG-083 — the pre-push gate: 10 minutes, red, and about the machine not the code (2026-07-31)
- **Symptom:** on Konyo's Mac `tv/test_control.py` took **608s** and came back **FAILED (1 failure,
  3 errors)**. Every one of the four was `subprocess._check_timeout` — the whole browser-driven family
  (lsFork routing, profile sigil, four-worlds key routing, the JS syntax gate) plus v1484's fresh-PC test.
- **Root cause:** Chrome's `--dump-dom` NEVER returns for an `http://127.0.0.1` page on this machine.
  Measured, not assumed: a 40-byte hello-world page returns instantly over `file://` and hangs over
  loopback; it hangs identically for Google Chrome AND Chrome for Testing; `--no-proxy-server` and
  `--proxy-bypass-list=<-loopback>` change nothing (there is no proxy configured); and Playwright drives
  the same binaries over the same loopback fine. So it is this launch path on this machine — not the
  network, not the page, not the code being pushed. v1484's budget made it worse: 300s × 2 attempts ×
  2 loads = up to **20 minutes**, and a killed run orphaned Chrome processes (two found burning CPU),
  because `subprocess` timeouts kill the launcher and not the renderers Chrome forks.
- **Fix (v1490):** `js_syntax_gate.browser_can_load_localhost()` — probe the capability ONCE on a
  40-byte page (12s), cache it, and have every browser-driven test skip with `NO_LOOPBACK` (a reason
  that says the result proves nothing) instead of burning its timeout and erroring. `check()`
  short-circuits the same way. The fresh-PC test now asks for `--headless=new` first with `old` as
  fallback, bounds each load to 45s, kills the whole process GROUP on timeout, and skips the second
  load when the first never answered.
- **Prove:** same suite, same machine: **608s / FAILED(1,3) → 17.9s / OK (skipped=8)**.
- **Prevention:** a capability the harness cannot assume gets PROBED, cheaply, once — and a test that
  could not run says so. An environment fact must never render as a verdict about the code.

## REG-083 — a panel reported an outage it invented (2026-07-31, v1516)
- **Symptom:** the FLEET panel in the console rendered "fleet unreachable" even when `/api/fleet`
  answered perfectly. Shipped in v1496 and wrong ever since — twenty versions of a panel that
  reported a network failure that never happened.
- **Caught by:** writing the v1516 Chronicle-panel spec. A probe showed the fetch returning **200
  with real JSON** while the DOM said "unreachable" — the fetch succeeded and the RENDER died.
- **Root cause:** `tv/control_ui.html` has TWO `<script>` blocks. `esc()` is declared at the top
  level of the first, so nothing in the second can see it. Every `esc(` call from the second block
  threw a ReferenceError *inside the try*, and the catch — written for network failure — blamed the
  network. The new Chronicle panel was about to ship with the identical bug.
- **Fix:** `escC()` declared in the block that uses it; 19 call sites moved; the first block
  untouched (asserted: 0 `escC` in block 1, 0 stray `esc` in block 2).
- **Prevention:** a catch that names a CAUSE must only be reachable from that cause. `catch (e)`
  around a fetch *and* a render will attribute render bugs to the network forever — and the message
  is the only thing anyone sees. Where a handler spans both, split the try or report `e` itself.
  Second lesson, same bug: an "unreachable/empty" state is exactly the state that looks plausible
  when it is wrong, so it needs a spec that asserts it appears only when the route actually failed.

## REG-082 — two specs read a key the app does not write (2026-07-31)
- **Symptom:** `bug040_050 BUG-042 star toggle persists localStorage` red on CI, green on the Mac.
- **Root cause:** the Linux runner is not a Mac, so `D2R_MACHINE` resolves to `windows` (by design —
  any non-Mac gets its own isolated world) and the star writes `W·d2r_wishlist`. The spec read the bare
  `d2r_wishlist` and got `[]`. The toggle had worked perfectly; the test was reading the wrong drawer.
- **Fix (v1490):** both specs read/seed through `LSR` — the app's own published router — so they are
  correct in every world. Proved in BOTH worlds by forcing `d2r_activeMachine` locally.
- **Prevention:** never hand-write a routed key in a test; ask the router. The Mac is the one machine
  where bare == routed, which is exactly why it hides this class.

## REG-081 — the profile sigil asked a question file:// cannot answer (2026-07-31)
- **Symptom:** Routine G back to 7/8 and the ~76 "no console errors" specs red, from v1486 onward:
  `CON: Fetch API cannot load file:///api/status. URL scheme "file" is not supported.`
- **Root cause:** the v1486 sigil called `fetch('/api/status')` with no protocol guard. On `file://`
  that resolves to `file:///api/status`, and Chromium logs a CONSOLE error that `.catch()` cannot
  suppress. Every other same-origin call in bible.html already carries the guard — this one skipped it.
  Identical class to REG-047.
- **Fix (v1490):** gate the call to non-`file:` origins; off the console the crest paints the local
  identity IMMEDIATELY rather than waiting 1.2s for an answer that was never coming.
- **Prove:** `node end_to_end_audit.js bible.html` → Page errors: 0 · 8/8 categories.
- **Prevention:** the board may only call `/api/*` when it is actually being served by the console.

## REG-080 — the single-primary mutex made a whole suite unrunnable (2026-07-31)

- **Symptom:** `tv/test_roundtrip_sim.py` reported `Ran 0 tests · FAILED (errors=1)` with
  `RuntimeError: roundtrip control server never came up`, after burning ~100s in `setUpClass`.
- **Root cause:** the harness boots its own `control_app.py` on `:17956`, but the v1406 Windows
  single-primary mutex used ONE machine-wide name, `TV_DIABLO_CONTROL_PRIMARY_v1`. Whenever the
  real app was running, the harness child hit `ERROR_ALREADY_EXISTS`, printed "already running
  (primary mutex)" and exited 0 — so the parent waited 40 × 0.5s for a server that had quietly
  declined to exist. Since a developer's app is usually open while they work, the suite was
  effectively unrunnable on the machine that needed it most.
- **Why the diagnosis was slow:** the harness sends the child's stdout/stderr to `DEVNULL`, so the
  one line that explained everything was thrown away, and the visible symptom pointed at the
  server's startup rather than at a mutex.
- **Fix (v1484 / shipped in v1483):** the mutex name is scoped by `CONTROL_PORT`. This is not a
  weakening — what v1406 prevents is two primaries fighting over the same port and window, and a
  process on a different port is a different instance by definition. `:17772` remains strictly
  single-primary (the desktop icon still cannot spawn two) while an isolated harness runs alongside
  a live console. The refusal message now also names the port and says the mutex is per-port, so
  the next person who hits it is told what to do instead of being left with a mystery.
- **Also fixed:** the same suite leaked its child — `proc.kill()` with no `wait()`, which left a
  `ResourceWarning` and, worse, a surviving `control_app` still holding its port and its own agent
  child, so the NEXT run failed to bind. It now terminates, escalates to kill, and always reaps.
  Runtime dropped from 27s to 11s once the orphans stopped competing.
- **Prevention:** (1) a lock should be scoped to the resource it protects — a machine-wide name is
  a much broader claim than "one app per port", and the extra breadth is invisible until something
  legitimate needs a second instance. (2) Never send a spawned child's output to DEVNULL in a
  harness whose failure mode is "the child did not start"; capture it and print it on timeout.

## REG-089 — plumbing with no tap: guards that can never be true (2026-08-02)

- **Symptom:** features that look shipped in the source, are described as working in their own
  commit message, and do nothing at all. Four live instances, found by the v1576 sweep:
  - `typeof toast === 'function'` guarded the v631 forge-base promotion. `toast` is declared
    NOWHERE in the 38,888-line file, so the guard was permanently false. The promotion was really
    running (it returned `["Heater (2 os)"]`) — it had simply never once announced itself.
  - The Vault **🪄 Fix all safe** button reported through `window._toast && window._toast(...)`.
    No writer for `_toast` exists anywhere in the repo; the `&&` swallowed it in silence. The
    button repaired N issues and gave Konyo zero receipt that it had done anything.
  - `_g3ForwardRender` fell back to a "safe" escaper when `typeof escHtml !== 'function'` — and
    that fallback did not escape. It wrote into `data-n`, which `kaiForwardUndo` reads back, so a
    grail name containing a quote would have made ↩ undo un-tick **the wrong grail**.
  - `window._FORGE_REDO` (v1570, MINE): the slot was declared, read and cleared, and no code ever
    wrote it while no button ever called `_forgeRedo`. Shipped three hours after I wrote a spec
    whose whole purpose was to make orphaned routes fail the suite.
- **Caught by:** a targeted 14-agent sweep for this one class, then `tests/v1577_dead_seams.spec.ts`.
- **Root cause:** a name is checked with `typeof` before use, the checked name is wrong or was never
  written, and the guard's whole purpose is to fail quietly. Nothing throws, nothing logs, and the
  code reads as defensive rather than broken. `X && X()` and `try{}catch(e){}` are the same shape.
- **Fix (v1576):** each guard pointed at the name the board actually owns (`window._grailToast`),
  the escaping fallback removed, `/api/quit`'s hard-coded `{ok:true}` replaced with a receipt keyed
  off the ground-truth `_FORCE_EXIT_ARMED` flag.
- **The premise that was wrong, and matters more than the bugs:** a `typeof NAME` guard sitting in a
  DIFFERENT `<script>` block from its declaration is **not** dead. Top-level `let`/`const` in
  classic scripts share ONE global lexical environment across the document — 190 of 196 guarded
  names in `bible.html` are live, and a detector built on "different block = dead" would condemn
  all of them. The REG-083/087 shape only bites when the SOLE declaration is nested inside an IIFE;
  the v1576 scope map found zero live instances of that.
- **Prevention:** `tests/v1577_dead_seams.spec.ts` requires TWO independent witnesses before it
  condemns a name — the live browser says it resolves nowhere at global scope, AND the source says
  it is declared nowhere at all. Either witness alone lies, in opposite directions: the browser
  cannot see function-locals (its first run flagged 26 healthy names — `v`, `d`, `map`,
  `refreshOpenCard`…), and the source cannot see scope. Known limit, stated rather than hidden: it
  does NOT catch an IIFE-nested declaration guarded from outside; that needs a parser, not a regex.

## REG-090 — the pre-push gate destroyed the evidence it existed to produce (2026-08-02)

- **Symptom:** the v1575 push was blocked by `tv/test_control.py`. The re-run passed. Three further
  runs passed. 340 tests, one of them red, and no way left on earth to learn which one.
- **Root cause:** every gate in `hooks/pre-push` ran with `>/dev/null 2>&1`, so a blocked push said
  only THAT a suite failed. The one remedy it offered — "run it by hand" — is precisely the thing
  that cannot recover a FLAKY failure, because by the time you run it, it passes.
- **Fix:** `gate_run()` tees each gate to a kept, pid-scoped log and prints the last 40 lines on
  failure, where unittest's FAIL block lives. Applied to all four gates. Proven against a
  deliberately failing suite; a passing gate still prints nothing.
- **Also fixed in the fix:** the first version reported `exit 0` on every failure. After an `if`
  block whose branch did not run, `$?` is the *if statement's* status, not the command's;
  `&& return 0` short-circuits and preserves the real code. Verified against a command exiting 42.
- **Prevention:** this is REG-088's own prevention rule (2) — never send output to DEVNULL in a
  harness whose failure mode is "it did not work" — which had been written down for this repo and
  applied only to the Windows harness, while the gate every push goes through kept discarding it.
  A prevention rule is not applied until it is applied *everywhere the shape occurs*.
- **STILL OPEN:** which test flaked is unknown and unrecoverable. The suspicion is the sub-100ms
  wall-clock budgets near `tv/test_control.py:1179` / `:1211` under load, but that is a guess and is
  recorded as one. The next occurrence will name itself.

## REG-091 — the ten-minute push: a bounded timeout that could not bound anything (2026-08-02)

- **Symptom:** the v1578 `git push` sat inside `tv/test_control.py` for TEN MINUTES and had to be
  killed from outside. Earlier, the v1575 push was blocked by the same suite and passed on every
  re-run. Both were the same defect; only the second one was slow enough to be caught in the act.
- **Why it hid:** it needs Chrome to be launchable AND to stall, so it does not reproduce on demand.
  Three standalone runs, one straight after `test_agent.py` (in case of REG-088's leaked-port
  shape), and one under a hook-like git environment were all 340/340 green.
- **Caught by:** sampling the blocked pid while it was still stuck (`sample <pid>`): the main thread
  was parked in `poll()`, and two orphan "Google Chrome for Testing" processes were burning CPU
  beside it. The process also held ESTABLISHED sockets to the live console on :17772.
- **Root cause, two halves that only hang when combined:**
  1. Three tests launched Chrome with `--headless=old`. That mode does not answer on this Mac —
     `tv/js_syntax_gate.py` ALREADY knew, and skips with the words "this browser never answers
     --dump-dom over http://127.0.0.1 on this machine". These three asked anyway.
  2. They used a bare `subprocess.run(..., capture_output=True, timeout=90)`. **A subprocess
     timeout kills the LAUNCHER, not the renderer helpers Chrome forks.** Those grandchildren
     inherit and hold the stdout pipe, so `capture_output` keeps waiting on a pipe that will never
     close — past the timeout, forever.
  So the timeout fired, killed the wrong process, and then the call blocked anyway. A timeout that
  cannot interrupt what it is timing is decoration.
- **Fix (v1579):** one `_dump_dom()` helper — `--headless=new` first with `--headless=old` only as
  a fallback, `start_new_session=True` so the launch owns its process group, and `killpg` on
  timeout so the kill reaches the helpers. Returns None when no mode answered, and callers
  `skipTest` on None: a probe that could not run proves nothing and must never report a pass.
- **This was already known and already fixed — once.** v1490 fixed exactly this in ONE test,
  writing the reason in its comments ("subprocess.run's timeout kills the launcher, NOT the
  renderer helpers"). Three other tests kept the broken shape for ~90 versions.
- **Prevention:** the same rule REG-090 needed — **a fix is not applied until it is applied
  everywhere the shape occurs.** When a comment explains a trap, grep for the trap before moving
  on. And the pre-push gates are now individually time-bound (`hooks/pre-push`), so the next
  unbounded wait fails loudly with its log instead of holding a push hostage in silence.

## REG-092 — the terror-zone countdown overstated the window by up to 30 minutes (2026-08-02)

- **Symptom:** the console's TZ clock read "50:46 until the zone turns · on the hour" at 15:09,
  when the zone actually turned at 15:30 — 20 minutes away. That number is what Konyo uses to
  decide whether there is time to start a run.
- **Root cause:** v1567 counted to the top of the hour and wrote the reason in its own comment —
  "This is the GAME's rule (terror zones turn hourly)". It was stated as a rule and never checked
  against the feed, which is the kind of claim that survives longest: nothing contradicts a comment.
- **The contradiction was already on screen.** The board's tracker tab labelled the next slot
  "⏭️ NEXT · ~30 MIN" and its lead text said "refreshes every 30 min". Two surfaces of the same app
  disagreed about the same fact for fourteen versions, and neither was checked against the source.
- **Evidence (measured, not assumed):** the relay's own history has slots on :00 and :30 with
  nothing in between, and across 93 adjacent half-hour pairs the zone CHANGED in 90. An hourly
  rotation would repeat roughly half of them; 3 of 93 is 3%, consistent with genuine back-to-back
  draws rather than a slower clock.
- **Fix (v1581):** `SLOT_S = 1800`, counting to the next :00 or :30, and the label now says "on the
  hour and the half hour". The progress bar fills over the half hour instead of the hour. Verified
  live: 13:49 remaining where the old code would have shown 43:49.
- **Prevention:** `tv/test_tz_art.py::TestRotationCadence` pins the slot length, the label, and —
  most importantly — that the two surfaces AGREE. The bug was not that one number was wrong; it
  was that two screens gave different answers and nothing compared them.

## REG-093 — `limit:400` on a timestamp-keyed KV list returned the OLDEST 400, so the fleet tracker hid every recent machine (2026-08-02)

- **Symptom:** Konyo — "my cousin in the states used the console as recently as yesterday and I
  DONT SEE IT, and my Windows PC I dont see logged either." Live
  `GET https://bull-4-u.com/api/console` returned `online=[konyo-3 / mac / v1595 / Jerusalem]` and
  `offline=[]` — exactly ONE machine and an EMPTY offline list, on a tracker whose whole job is to
  say which machines have been here.
- **Caught by:** the user report; confirmed by reading `functions/api/console.js:78` and
  `functions/console.js:25`.
- **Root cause (confirmed):** both files listed the event log with
  `kv.list({ prefix: 'consolelog:', limit: 400 })`. Cloudflare KV returns keys in **LEXICOGRAPHIC
  ASCENDING** order and the keys are `consolelog:<ISO-ts>:<machine>` — so `limit:400` returned the
  OLDEST 400 events in the 30-day window, not the newest. Once the log passed 400 entries, every
  RECENT machine fell outside the window and became invisible. The list was not truncated at the
  end Konyo was looking at; it was truncated at the other end.
- **Contributing cause (design, not a typo):** presence keys carry a 600s TTL, so any machine off
  for more than ten minutes vanished from `online` entirely, and "when was this machine last here"
  had to be reconstructed from an event log that was never designed to answer it. Heartbeats wrote
  no durable record at all — the most frequent signal the fleet produces was the one nothing kept.
- **Contributing cause (honesty):** `_console_beacon` in `tv/control_app.py` swallowed every failure
  with a bare `except Exception: pass`. A machine whose beacon had been failing for months looked
  IDENTICAL to a machine that was never switched on. Silence was being read as absence.
- **Contributing cause (UX):** `/visits` and `/console` are DIFFERENT trackers answering DIFFERENT
  questions — `/visits` counts browser page-views of `/d2r/`, `/console` tracks TV-D console APP
  presence, and the console app never appears in `/visits` by design. Neither page said so.
  Conflating them cost a debugging session before a line of code was read.
- **Refuted hypothesis, recorded so it is never re-opened:** a suspected prefix collision between
  `console:` and `consolelog:` is **NOT REAL**. Character 8 of `console:` is `:` and of
  `consolelog:` is `l`, so `consolelog:…` never matches `prefix: 'console:'`. Verified by
  execution, not by reading; a test now pins it in BOTH directions.
- **Fix:** full cursor pagination in both files — correct under EITHER ordering, which is the whole
  point of paginating instead of raising the limit; a durable `lastseen:<machine>` key written on
  EVERY beacon including heartbeats (~400-day TTL); scan diagnostics in the API response so the
  window is visible instead of assumed; a `lastBeacon` result reported by the app, stored
  server-side and rendered RED when failing; and scope banners on `/visits` and `/console` stating
  what each one does and does not cover.
- **Prevention:** `tv/test_console_fleet.py`, registered in `tv/run_gates.py`, containing a test
  **observed RED on the pre-fix code** — a regression test that never failed on the bug proves
  nothing. Two general rules, stated so they outlive this entry:
  1. **Never use a bare `limit:` on a KV list of timestamp-keyed records to mean "the most recent
     N".** Lexicographic ascending order makes that "the OLDEST N". Paginate the cursor, or key by
     descending timestamp.
  2. **Silent fire-and-forget telemetry is not evidence.** Any beacon must record and surface its
     own last result; otherwise "we have no data" and "everything is fine" are the same picture.

## REG-094 — the fix for REG-093 read 2,556 KV values in one request and 500'd `/console` (2026-08-02)

- **Symptom:** minutes after deploying the REG-093 fix, `https://bull-4-u.com/console?k=…` returned
  **HTTP 500** on every request (`error code: 1101`). `/api/console` kept returning 200, which made
  it look like a page-specific rendering bug rather than a shared one.
- **Caught by:** a live check immediately after deploying — not by any test. Every local test passed,
  including a stub reproduction carrying all 2,556 records.
- **Root cause:** REG-093 was fixed by listing EVERY `consolelog:` key (correct) and then doing one
  `kv.get()` per key to learn which machine each event belonged to (**not** correct). That is 2,556
  subrequests in a single Worker invocation, and Cloudflare caps subrequests per invocation. The
  real exception — `Error - Too many API requests by single Worker invocation` — was only visible
  from `npx wrangler pages deployment tail <deployment> --format=json`. **A local stub cannot
  reproduce this class at all: the limit does not exist off-platform.**
- **The nastier half:** each read was wrapped in `.catch(() => null)`. So when the cap was hit,
  every remaining read resolved to `null` and the code reported an EMPTY offline list — "we exceeded
  a limit" was silently rewritten as "no machines have ever been here". That is REG-093's own
  honesty defect, reintroduced by REG-093's fix, one layer down.
- **Fix:** read the KEY, not the value. `consolelog:<ISO-ts>:<machine>` already carries both facts,
  so `machinesFromLogKeys()` derives newest-event-per-machine from key names at **zero** subrequests;
  only the records actually rendered are fetched. Measured on the 2,556-key fixture: `/api/console`
  went 2,556 → **2** reads, `/console` → **121**. Split on the LAST ':' — an ISO timestamp contains
  colons, so `parts[1]` is the hour, not the machine.
- **Proof it was the real cause:** with the corrected read path the live offline list immediately
  returned the two machines that started this whole investigation — `LAPTOP-QNFL860M` ("Dean",
  Windows v1551, Monroe US, 2 Aug 00:02) and `AdiJusid` (Windows v1489, Jerusalem, 1 Aug 21:07).
- **Prevention:**
  1. **Never fan out one KV read per listed key.** Design keys so the listing itself answers the
     question; fetch values only for what you render.
  2. **A per-item `.catch(() => null)` over a bulk read is a lie generator.** It converts a
     platform-level refusal into ordinary-looking emptiness. If a bulk read can partially fail,
     count the failures and say so.
  3. **Platform limits are not testable locally.** After deploying anything that changes read
     volume, hit the live URL and read `wrangler pages deployment tail` — a green local suite is
     not evidence about production.

## REG-095 — ~680 versions of unreachable render code, found by making LAW19 a gate (2026-08-02)

- **Symptom:** none visible. That is the point of this entry — nothing was broken on screen, so
  nothing ever prompted a look.
- **Caught by:** a static sweep of every DOM id READ in each surface against every id WRITTEN in the
  same document. Not by a user report, and not by any existing test.
- **Root cause:** `#hd-shelf-grid` and `#hd-shelf-pager` were read in four places and created in
  **none** — not in `control_ui.html`, not anywhere in the repo. v910 moved the markup ("the grid
  lives in the shelf now") and left the renderer behind. So `if (!$('hd-shelf-grid')) return;` in
  `hdShelf()` was permanently TRUE, and `hdShelfRender()` plus everything after that guard had been
  unreachable ever since. Roughly 60 lines of render code, its paging state (`HD_PAGE` / `HD_PER`)
  and the scroll-anchor bookkeeping that existed only to serve it.
- **Same shape, three more places:** `#tvd-frame-lb` looked up TWICE in the console's own document
  when it belongs to the board (the working check is the iframe probe beside it); and the board's
  routine-widget lookup chained three ids "because the widget id varies across bible versions" when
  only ONE bible document exists at runtime and it defines `#routine-status-bar` as static markup —
  so `routine-toggle-pulse` and `routine-bar` named nothing that could ever be present.
- **Fix:** all of it deleted. The features are NOT lost — the shelf renders in `#th-shelfov .sh-grid`
  and the session strip in `#hd-hist-strip`; the board's routine toggle keeps its real id and its
  attribute-selector catch-all, which is a genuine safety net precisely because it names no phantom.
- **Prevention:** `tv/test_reachability.py`, registered in `tv/run_gates.py`. Every id read must be
  written in the same document; a genuinely cross-document read goes in `CROSS_DOCUMENT` **with a
  reason**. It carries three tests proving the detector actually fires, because a gate nobody has
  seen fail is a gate nobody knows works.
- **Why this was worth a version:** it is the FOURTH instance of one defect — REG-083/087 (a
  `typeof` guard on a name declared nowhere), v1576 (a tested-but-uncalled classifier while the live
  copy was the unsafe one), v1593 (`RUNES`/`_flat` deleted with the reference left behind, which
  crashed the whole Terror Zone panel), and now this. Three were found by accident and one by a
  crash. It is a mechanical property, so it stopped being a habit and became a gate.
- **Lesson, generalised:** *a reference to a name nothing produces is checkable without running
  anything.* Where a defect class is mechanical, automate it — an intention that depends on someone
  remembering to look has already failed once by the time you notice it.

## REG-096 — five ownership changes never repainted the surfaces that show ownership (2026-08-02)

- **Symptom:** un-own an item, clear the unsorted dock, run a full reset, or log an intake — and the
  grail meter, the hero card, the boss cards, the calculator and both forge tallies kept showing the
  PRE-change picture until something unrelated happened to repaint them. Same family as the v1594
  chronicle-apply staleness and the tooltip complaint before it.
- **Caught by:** sweeping `typeof X === 'function'` guards for names declared nowhere — the
  REG-083/087 detector pointed at symbols instead of DOM ids.
- **Root cause:** all five sites ended with `if (typeof renderAll === 'function') renderAll();`.
  **There is no `renderAll` in this app and there never was** — the name is declared nowhere, so
  every one of those guards was permanently false. They were not merely dead code: each site MUTATES
  `owned`, and the repaints they DID run (`renderVault` / `refreshOpenCard` / `renderJournal`) cover
  the vault and the journal only. The intended repaint of everything else simply never existed.
- **Why it hid for so long:** the guard reads as defensive, and the app never errored — it just
  showed a stale number. `typeof X === 'function'` on a name that exists nowhere is indistinguishable
  at a glance from the same guard on a function that is merely loaded later.
- **Fix:** `window._repaintOwned()` — the EXACT six painters `toggleOwned()` already runs for the
  same kind of change, so un-owning now costs what ticking costs and no new performance profile is
  introduced. Each painter is individually try-guarded: the state change has already happened by
  then, and a repaint that aborts halfway leaves a worse picture than none — half the surfaces
  updated, half stale, nothing saying so.
- **Second promise, same shape:** `window.cycleIntakeLogger` read
  `(typeof uiPrompt === 'function') ? await uiPrompt(...) : prompt(...)`. `uiPrompt` was declared
  nowhere, so the app's only type-in dialog always raised the OS-native white box that `uiConfirm`
  was written in v341.41 to replace. `uiPrompt` now exists, reusing the `.ui-confirm` skin (two
  dialog themes is how one of them ends up looking foreign after a palette change). Esc resolves
  **null**, not `""` — `setIntakeLogger` coerces empty to "Konyo", so an empty string on cancel would
  have silently renamed the logger instead of leaving it alone.
- **Prevention:** `tests/v1599_kept_promises.spec.ts` — 7 tests that assert the repaint actually
  reaches its painters (a stub that does nothing would pass a `typeof` check, which is the same
  defect one layer up), that a throwing painter cannot stop the rest, and that the prompt focuses,
  resolves what was typed, cancels to null and leaves no orphaned overlay.
- **Lesson:** *a `typeof` guard is only defensive if the name exists somewhere.* When it does not, it
  is a promise nobody kept — and it is invisible precisely because the surrounding code still works.

## REG-097 — the v1577 isolation tests never ran once, and the gate was red for 24 versions (2026-08-02)

- **Symptom:** `tv/test_chronicle_retro.py` exited 1 with `errors=2`. Nobody was chasing it, which is
  the same shape as REG-079 (`test_routes` red for ~100 versions).
- **Caught by:** running the FULL gate set instead of the subset touched by the change.
- **Root cause:** `TestV1577ClassifyIsolation._reels` wrote `index.json` frames as a list of bare
  STRINGS. A sealed reel holds ROWS — `{"f": "f_1784984130673.jpg", "ts": 1784984130673}` — which is
  what the agent writes and what every real reel on disk contains. `still_runs()` reads `fr.get("f")`,
  so both tests died with `AttributeError: 'str' object has no attribute 'get'` **inside the
  fixture's own sweep**, before reaching the isolation they exist to pin.
- **Second fault underneath the first:** once the shape was fixed the tests still failed —
  `classified == 0`. The fixture wrote four magic bytes and 64 zeros as a `.jpg`, which Pillow cannot
  decode, so `jpeg_sig()` returned None for every frame. An unreadable frame BREAKS a run by design
  (one unreadable frame must never weld two screens into one), so no run ever reached
  `MIN_RUN_FRAMES` and the classifier was never called — which is why "the throwing probe" never
  threw. Fixed by writing real, decodable, non-blank JPEGs.
- **What this means:** from v1577 until now, the two tests guarding *"one bad frame must not abandon
  the whole retro sweep"* have never once exercised it. **The behaviour they pin is correct** — both
  pass immediately once the fixture is right — but nothing was checking it. That is exactly LAW19's
  clause about proving added tests actually RAN: a test that errors in its setup is not a weaker
  test, it is no test at all.
- **Related honesty fix, same run:** `js_syntax_gate.py` printed "⚠ GATE SKIPPED" and returned **0**,
  so `run_gates` showed a green tick beside it — contradicting its own docstring ("a check that did
  not happen is not a check that passed"). On this Mac that gate skips on EVERY local run, so the
  surface least protected was the one wearing a tick. It now exits **77**, and `run_gates` maps 77 to
  SKIP. Verified no other caller runs it as a subprocess expecting 0 (`test_control` imports
  `check()` directly; the pre-push hook does not invoke it).
- **Prevention:** run the whole gate set, not the subset you touched. Both faults here were invisible
  to any targeted run, and the fixture had been wrong since the day it was written.

## REG-098 — MINI's focus was stamped on every reel and never once steered a read (2026-08-03)

- **Symptom:** Konyo — *"so for MINI AIR ON is this finally focused and understanding of the fact
  that it is reading stash/runes/gems/materials and to look out specifically for this"*. The honest
  answer was **no**.
- **Root cause:** `MINI_FOCUS` was carried all the way from the button to `--mini-focus` to
  `_idx["focus"]` in the sealed reel — and then used for exactly ONE thing: sweeping mini reels
  first. `is_mini_reel`'s own docstring stated the limit plainly: *"being wrong here costs ordering,
  never correctness."* Nothing told the READER what it was looking at, so a capture taken while
  parked in the rune tab still paid a model call to **discover** that, and could still get it wrong.
- **Why that is worse than a wasted call:** a rune tab misclassified as `inventory` files his runes
  in the wrong lane, and merge-max then makes it permanent. Measured on a two-reel fixture with a
  deliberately-wrong classifier: `Ral Rune → lane=inventory, kind=item`. With the focus declared:
  `lane=stash, kind=rune`, and 2 classify calls became **0**.
- **Fix:** the retro sweep now TRUSTS a declared focus in place of the classify call — the same
  trade `chronicle_retro.sweep_frames()` has made for the live lane since v1527 (*"a recorded visit
  already knows two things a blind sweep has to pay a model to discover"*). Cheaper and more
  accurate at once, which is rare enough to state: the call it removes is the one that could lie.
- **Trusted NARROWLY, on purpose:** only a focus in the engine's own vocabulary, and only where the
  sweep owns it. `chronicle-uniques` / `chronicle-sets` return None from the vault's
  `_declared_surface()` and fall through to the chronicle sweep, which has its own `_declared_kind()`
  — claiming one in the wrong sweep would file grail pages into the vault as a stash tab.
- **Second half, same shape:** the chronicle sweep now skips its classify for a chronicle-focused
  mini. That matters more there than on the vault side, because `chronicle_kind()` deliberately
  returns None for a Chronicle page whose TAB it cannot read — guessing "uniques" would write set
  pieces into his grail — so an unreadable tab used to cost the whole page. If he has already said
  which ledger he opened, that failure mode is gone.
- **Prevention:** `tests/v1603_mini_focus.spec.ts` drives the real UI and asserts THE CHOICE REACHES
  THE ENGINE (a focus row that renders correctly and posts `{}` would be the same dead-plumbing
  defect the feature exists to remove), plus that the toast echoes the focus the engine ACCEPTED
  rather than the one we asked for. Engine-side, `tv/test_vault_retro.py` pins that an unknown or
  cross-sweep focus is never trusted. Totals now report `trustedFocus` — "9 classifies" and
  "9 classifies + 4 you told us" are different facts about the same sweep.

## REG-099 — 98 real frames, no index.json: the reel's existence was written last (2026-08-03)

- **Symptom:** Konyo — *"still a black screen when trying to record."* Capture itself was fine:
  **98 real JPGs, ~85 MB**, on disk in `tv/frames/hist/reel_s_1785708285647_38665`. But that reel had
  **no `index.json`**, and theatre / `read_reel` / `sweep_hist` all key off `index.json` — so a reel
  without one is invisible and unplayable. The footage existed; nothing could find it.
- **Caught by:** Konyo, on his live recording path, **after** a separate fault had already been fixed
  in the same session — a headless console (`control_app.py --no-open`) does not hold the Screen
  Recording TCC grant, so `/api/on` refused and nothing recorded at all; fixed by relaunching via
  `tv/tvd-scan.sh` (TV DIABLO.app, `--open`). **Two distinct bugs stacked behind one sentence.** That
  is why the first fix looked like it had failed: the grant fix was real and verified (`/api/on` →
  `ok:true`, agent alive, `eye.jpg` refreshing every second), and the screen stayed black anyway
  because the reel it produced had no index. When a fix "doesn't work", check whether the SECOND
  failure downstream of it is a different bug before undoing the first.
- **Root cause:** `tv/tv_diablo.py` ~6457-6514 wrote `index.json` — the one artefact without which
  the entire reel is worthless — only **after** a per-frame blank-detection pass that decodes every
  JPEG. Measured: **0.076 s/frame → ~7.4 s** for this 98-frame reel. `control_app.stop_agent()`
  (~line 2193) asks for shutdown with `timeout=1.0` and force-kills after `wait_s = 2.5`, so the hard
  kill lands **~3.5 s** in — about **4 s before the index would have been written**. The 1-frame reel
  sealed 34 minutes earlier DID get an index (a single 76 ms decode, comfortably inside the deadline),
  which is exactly the contrast the timing predicts. The comment at the kill site asserting *"seal is
  already on disk before kill"* was simply false.
- **Compounding fault — a double-swallowing `except`:** the block was wrapped in
  `except Exception: _blank = 0` inside an outer `except Exception: pass`, so a failure to open,
  serialise, write or complete `index.json` was indistinguishable from success. Nothing logged, nothing
  retried, and the reel silently became unplayable.
- **Stated honestly — the race is NOT deterministic:** three older reels of **114 / 126 / 153** frames
  also got indexes, so different stop paths grant different grace. The exact stop path taken by the
  01:04 session is **not established**.
- **Blast radius, with numbers:** the archive survey found **6 reels** (153, 126, 114, 98, 1, 1 frames)
  plus two thumbnail caches (`cache1280`, `cache160` — jpgs, no index, correctly not reels). Exactly
  **ONE** reel was ever silently lost: the 98-frame session — **18% of the 543 archived frames**, and
  the newest session. It has since been recovered. 2 reels carry an index over a single frame. This has
  **not** been quietly eating footage for a long time; the archive does not support that claim.
- **Fix:** `index.json` is written **FIRST and atomically**, from the filenames alone (tmp + `fsync` +
  `os.replace`) — every frame is `f_<epoch-ms>.jpg`, which is exactly what an index row carries
  (`{"f": name, "ts": int(name[2:-4])}`), so nothing has to be decoded to produce it. Blank flags are
  demoted to an optional, time-bounded **second** atomic rewrite. An index-write failure is now logged
  loudly and retried once. Readers reconstruct a missing index from the filenames via
  `chronicle_retro.ensure_reel_index` / `load_index`, and `chronicle_retro.reel_dirs()` no longer drops
  index-less reels. `control_app` repairs after a kill and at boot, and reports it. The blind 2.5 s is
  replaced by a bounded seal-aware stop grace (hard cap ~8 s). `tv/reel_repair.py` gives a
  hand-runnable survey/repair, doctor gains a `reels_indexed` warn check, and `tvd-console.sh` now
  refuses **by default** to hand back a console that cannot record — the always-up headless console is
  precisely the thing that reintroduces the TCC half of this symptom.
- **Prevention — the general law, and this is the transferable part: THE CHEAP, ESSENTIAL ARTEFACT
  MUST BE DURABLE BEFORE THE EXPENSIVE, OPTIONAL ENRICHMENT RUNS.** The index costs microseconds and
  is the reel's existence; the blank flags cost seconds and only save classify calls later. Writing
  them in the wrong order turned a shutdown race into lost footage. And a swallowing `except` around
  the essential write is what converts a race into **silent** data loss — the same failure with a loud
  log would have been a one-line diagnosis instead of a night. Regression suite:
  `tv/test_reel_index_durability.py`, **observed RED on the pre-fix code first** (LAW19) and registered
  in `tv/run_gates.py` per REG-079 — an unregistered suite rots.

## REG-100 — the grail that was never split: a migration built, reverted, and finally disproved (2026-08-04)

- **Symptom (reported as a defect, and it was not one):** `d2r_owned` and `d2r_copies` sit in
  `window._LP_FORKED`, so they fork per PROFILE (`main` vs `ladder`) while `d2r_foundLog`,
  `d2r_setPieces` and `d2r_rwMade` are machine-shared. Read from the store list alone that looks like
  "his uniques count differently on MAIN than on LADDER", and Konyo asked for uniques to behave
  *"like runeword and sets.. same logic"*.
- **Caught by:** the v1633 store-fork audit — from the SHAPE of the code, not from a measurement.
- **What v1633 did, and why it had to be reverted:** it moved both keys into the machine-shared set
  plus a one-shot union migration with a backup key. Seeded names kept vanishing after a reload, so it
  was reverted before shipping. The reason is the v677 doctrine: `d2r_owned` is not the found-truth,
  it is the PHYSICAL VAULT (items on a given account's mules) plus pre-v677 residue. `toggleOwned()`
  on a grail item writes the LEDGER (`d2r_foundLog`), and `funiScan` computes
  `found = foundLog ∪ owned`. The board therefore re-derives from the shared ledger on every load and
  the union merge had nothing lasting to do.
- **Root cause of the false alarm:** a store-list audit answers *where does this key live*, never
  *what does the user see*. Two keys can be forked and still produce one number.
- **Fix — deliberately NO code change to the stores. Measured instead, on the real board:** MAIN read
  **243** found; ticking one unique took it to **244**; LADDER, switched the way the app switches
  (`d2r_activeProfile` + reload), read **244** off the same `d2r_foundLog` — its own fork
  `L·d2r_owned` had **length 0**. Marking on LADDER took it to **245**, and MAIN then read **245**.
  Both directions, across reloads. The fork is inert. Shipped: the measurement pinned as
  `tests/v1634_profile_grail_parity.spec.ts` (a name found on either account shows on the other, and
  the ladder namespace holds no chronicle of its own), plus a comment at the `_LP_FORKED` definition
  recording the numbers so the fourth person to read that list does not rebuild the migration.
- **Prevention — the transferable law: A STORE-SHAPE FINDING IS A HYPOTHESIS, NOT A BUG. DRIVE THE
  REAL SURFACE AND READ THE NUMBER BEFORE MIGRATING ANYONE'S DATA.** A migration is the most
  destructive change a single-file app can make; this one would have rewritten his grail to fix a
  divergence that does not exist. And the tell that it was wrong was available for free — the merge
  could not survive a reload, which is precisely what "the board derives this from somewhere else"
  looks like from the outside. NEVER ship a migration that cannot be shown to hold after a reload.

## META — v1634 shipped through an adversarial gate that could not refuse anything (2026-08-04)

- **Symptom:** v1634 was built, gated and pushed by a MAX run that reported every item as having
  survived its adversarial skeptic panel. None of them had been reviewed at all.
- **Caught by:** reading the workflow's own arithmetic after the fact, not by anything the run said.
- **Root cause:** the kill threshold was the hardcoded literal `refutedN >= 2`, while triage had
  sized the panel at **1** skeptic. One skeptic can produce at most one refutation, so the condition
  was unreachable by construction — **every item auto-passed, unreviewed, and the run reported that
  as a pass.** A fixed threshold that is not scaled to panel size is not a weak gate; it is no gate,
  and it is indistinguishable from a strong one in the log.
- **Fix:** the threshold now DERIVES from panel size instead of being a literal, so a panel of 1 can
  refuse and a panel of 3 still needs a majority. Fixed in the workflow, not in this repo.
- **Retroactive verdict on the code that got through — the payload of this entry:** v1634 was
  re-gated adversarially after the fact, item by item, against the live board. **It survives, with
  exactly one real defect: REG-101 below.** Everything else held (see the NOTE after REG-101).
- **Prevention:** *a gate whose pass condition is arithmetically unreachable reports the same word as
  a gate that passed on the merits.* Any quorum, threshold or majority must be computed from the
  population it judges — and when a gate is repaired, the work it already waved through is owed the
  review it never got. Re-gate retroactively; do not assume the ship was fine because it was green.

## REG-101 — the armed state of a destructive control was invisible: a borrowed class name that matched nothing (2026-08-04)

- **Symptom:** the two-tap un-chronicle control shipped in v1634 on the Craft Workshop rows
  (`✕` → arm → confirm) looked **identical armed and at rest**. The tap that arms a destructive
  control gave no colour, no border, no background — nothing but the word in the button changing.
- **Caught by:** the retroactive adversarial re-gate driving the PAINTED board (not reading the
  source), plus `tests/v1635_craft_book_painted.spec.ts`, which now asserts the armed state differs
  from the resting state by a **computed** property.
- **Root cause:** `window.forgeUncraft` applies `btn.classList.add('gp-rm-armed')` (bible.html
  :33638) — the class name borrowed from the grail chips' `_armUnmark`. But the only rule for that
  class in the entire file is **descendant-scoped**: `.gf-piece .gp-rm.gp-rm-armed` (:3836). The
  craft button is `.f-btn.f-craft-unchron` inside `.f-craftrow` (:33709) — never inside a
  `.gf-piece`, and `.f-craft-unchron` has no rule of its own anywhere in the file. The selector could
  not match, so the class was decoration on a DOM node and nothing more.
- **Measured, before and after:** at rest `borderColor` read **rgb(58,47,30)**; armed it read
  **rgb(58,47,30)** — the same value, on the same element, in the same paint. The only surviving
  signal that the control was armed was `textContent` flipping to `remove?`. After the fix the two
  states differ by a computed property, which is what the spec now reads.
- **Fix:** the craft row's armed state gets its OWN rule instead of borrowing one that cannot reach
  it, so arming is visible where the control actually lives.
- **Prevention — the transferable law: BORROWING A CLASS *NAME* FROM ANOTHER COMPONENT BORROWS
  NOTHING IF THAT CLASS IS DESCENDANT-SCOPED. COPY THE RULE OR WRITE A NEW ONE.** And prove an armed
  state differs by **measuring a computed property, never by eye** — a mirrored two-tap flow reads as
  correct in the source and in review, because the code that arms it is right; only the paint is
  missing, and only a measurement sees that. This is the same shape as every "it looked applied"
  defect in this file: the class landed, the rule never did.

## NOTE — v1634's other claims were re-gated adversarially and SURVIVED (2026-08-04)

Recorded so nobody re-litigates them. Each was attacked with intent to refute; each held, and the
evidence is here rather than in a run log that will be gone.

- **`d2r_craftMade` belongs in `_WP_FORKED` (:3564) and needs NO migration.** A craft RECORD is the
  same class of fact as `d2r_rwMade` / `d2r_setPieces` — something this bench made, once, shared
  across MAIN and LADDER and forked on the Windows cousin. `_WP_FORKED` is built as a **superset** of
  `_LP_FORKED`, so the choice is not an either/or. GUEST/cousin worlds route to `I·<id8>·` on both
  profiles — measured, not assumed. And the store is **new in v1634**: there is no prior key, on any
  prefix, for a migration to have anything to move. Verified rather than assumed, per REG-100.
- **`window.forgeCrafted` cannot double-count, cannot fire on load, cannot be faked by a re-render.**
  The celebration is gated on a genuine rise of the **distinct-recipe Set**, so a second ✓ on the
  same recipe is a no-op (Set membership), and the handler is reachable only from `onclick` — it does
  not run during render or on boot.
- **`window.forgeUncraft` cannot leak arming between rows and cannot poison the baseline.** The armed
  flag lives in the clicked element's own `dataset`, so two rows cannot share it; `__chronPrevN` is
  **assigned a Set `.size`**, which cannot go negative or go stale, and a later re-log therefore
  still reads as a rise of exactly one. It never celebrates — the v559.1 rule holds.
- **The comment at bible.html :3540-3549 is TRUE, verified independently of the comment.**
  `_ownedNames()` (:34571) computes `new Set(d2r_owned)` unioned with `Object.keys(d2r_foundLog)`,
  and all four `d2r_owned` writers (:15991, :16642, :31751, :33482) go through the fork router
  (`const LS = window.LSR`, :15249). `d2r_owned` really is the PHYSICAL vault, the grail read really
  is `owned ∪ keys(foundLog)`, and the per-profile fork really is inert. **No grail migration was
  owed. NOBODY BUILD THAT MIGRATION A FIFTH TIME** — see REG-100 for the four previous attempts.
- **Two candidate defects were checked and are NOT real, so they get no number.** `chronicleReset()`
  (:20626) does not clear `d2r_craftMade` — but it does not clear `d2r_setPieces` either; it is the
  **runeword** chronicle reset and its own copy says so ("track their own runewords from zero"), so
  that is scope, not a bug. And every `--rar-*` token used in `tv/control_ui.html` is defined there
  (7 used, 7 defined: unique/set/rare/magic/runeword/rune/orange) — no usage falls through to an
  inherited colour.

## REG-102 — a boss portrait that was a gemstone for seven weeks, and every automated check passed (2026-08-04, v1636)

- **Symptom:** the Forge run thumbnails served `art/mephisto_graphic.png` for Mephisto — **a polished
  blue teardrop soulstone**, an ITEM — and `art/diablo_graphic.png` for Diablo, **a leather-bound
  book**. Konyo, twice: *"mephisto image is not correct.. it needs a boss level image of mephisto not
  annihilus charm"* and *"diablo same thing its not a book. its a boss"*.
- **Caught by:** a human OPENING the two files and saying what they depicted — and independently by
  Grok, a different model family, shown the file with no hint of what it was supposed to be, which
  answered *"a polished, deep-blue teardrop gemstone"*. Two witnesses, per the multi-witness rule.
  Nothing automated ever caught it, and v1629 "fixed" it without looking at a single pixel.
- **Root cause — an art-pipeline write, not a rendering bug.** Commit `ff2787e` (v269, *"more D2R HD
  items … via **fuzzy base-item matching**"*) rewrote **54** `art/*_graphic.png` files from ITEM art.
  Two of its slugs collide with bosses that share a name with an item: `mephisto` → Mephisto's
  Soulstone, `diablo` → a tome. The matcher had no notion that some `*_graphic.png` files are
  MONSTERS rather than items, so it clobbered two boss portraits in passing and nothing noticed. The
  code was innocent the whole time: `BOSS_PORTRAIT` (bible.html :34973) maps correctly, and
  `_runArtThumb` measurably served the right FILENAMES. **The files themselves were mislabelled.**
- **Measured, before and after:** before — `mephisto_graphic.png` **10KB** (a gem), `diablo_graphic.png`
  **46KB** (a book). After restoring from `ab079b8`, the commit immediately before v269 — **154,022
  bytes** and **149,265 bytes**, both re-opened and confirmed to depict the boss. 10 of the 13 boss
  ids carry a portrait; the other 3 deliberately fall through to level art.
- **Fix:** both portraits restored from `ab079b8` rather than re-extracted from CASC — the other
  eight are diablo2.io-style full-body renders on white, and a raw SpA1 sprite frame would not have
  matched them. Pinned with `art/boss_portraits.manifest.json` (what a human SAW in each of the ten)
  and `art/verify_boss_portraits.py`.
- **The whole class, swept — this bug shipped THREE times before anyone named it.** The same fuzzy
  overwrite was patched one-off twice and never generalised: `a54d5e6` (v284, *"fix Deep shard art
  (**was a helmet**)"*) and `fdd9849` (v287, *"sunder charms: **RESTORE** the real per-element art"*,
  6 files). Each was treated as a one-item typo. Across the HD arc — `498241d` v268 (154 files),
  `ff2787e` v269 (54), `92df081` v270 (83) — **291 distinct `*_graphic.png` files were bulk-rewritten
  by name matching**, out of 356 in `art/`. Only the ones Konyo happened to look at were ever caught.
- **Prevention — the transferable law: AN IMAGE IS UNVERIFIED UNTIL SOMEONE OPENS IT.**
  `naturalWidth > 0`, a resolving path, a filename, an md5 and a byte count all prove a file EXISTS;
  **not one of them proves it is the RIGHT PICTURE**, and all five passed for seven weeks here. Both
  cheap proxies were tried and are recorded as PROVEN INSUFFICIENT — md5 across `art/` found zero
  duplicates (catches nothing), and file size flagged Mephisto at 10KB but **missed Diablo at 46KB,
  which is a book**. Second rule, aimed at the pipeline rather than the checker: **never bulk-write
  `art/` by fuzzy name match without excluding the boss-portrait filenames** — a name is not a type,
  and `art/` contains `durielsshell_graphic.png` (Duriel's SHELL, an item) waiting for the next
  "starts with duriel" rule to grab it.

## REG-103 — the picture was fixed and the card that opened over it was still the item (2026-08-04, v1636)

- **Symptom:** independent of REG-102 and left behind by its v1629 predecessor — hovering a boss run
  thumbnail floated an ITEM card. `#arttip` over Mephisto showed the soulstone's card, over Diablo a
  book's, **under a title promising "open the boss card"**. Fixing the art alone did not fix this:
  after v1629 the thumbnail was the right boss and the hover card was still the wrong thing.
- **Caught by:** driving the painted board and reading the card that actually opened — not by reading
  the emitter, which looks correct in isolation.
- **Root cause:** `_runArtThumb` (bible.html :35032) emitted `data-art-logo="Mephisto"`, and
  `data-art-logo` resolves through `artUrl` / `D2IO_ART` — **an ITEM art map**. A boss name was being
  used as a lookup key into a table that contains no bosses, so every boss thumb resolved by
  name-collision into whatever item shared its name, and bosses with no colliding item resolved to
  nothing at all. This is REG-102's defect one layer up: **asking an item map for a boss.**
- **Measured, before and after:** across the **13** boss ids, **0** produced a boss card before the
  fix — the ones that resolved produced an item card, the rest produced a card with an empty desc.
  After: all 13 resolve to their own `BOSSES` row and render a populated boss card. A non-vacuous
  count in both directions — the "before" number is 0 out of a population that is genuinely 13, not
  0 out of 0.
- **Fix:** boss surfaces now carry `data-boss-tip="<bossId>"` and the card is built **from the
  `BOSSES` row itself** (bible.html :23341) — an **id** lookup into boss data, never a **name** lookup
  into item art. A boss whose name collides with an item can no longer resolve to the item, which
  closes the collision class rather than the two instances of it.
- **Prevention — the transferable law: A NAME IS NOT AN IDENTIFIER, AND THE MAP YOU ASK MUST BE THE
  MAP THAT HOLDS THE THING.** Two entity types sharing a namespace of display names will collide the
  moment one is looked up in the other's table, and the failure is silent and confident — a card
  opens, it is populated, it is simply about the wrong entity. Route by id. Second law, the one that
  cost the extra version: **a bug with an image and a behaviour half has TWO halves.** v1629 fixed
  the picture, declared the bug closed, and shipped the wrong hover for another seven versions —
  when a fix makes a surface look right, check what that surface still DOES.

## REG-106 — the daily pick rendered its item art TWICE

**Symptom.** On the Sessions → DAILY TASK FORCE hero row, the AI Daily Pick showed the item icon,
a 4px gap, then the same icon again.

**Caught by.** An adversarial skeptic reading the emitting source during the v1636 run — NOT by a
screenshot, because the render gate never ran on that run (the agent ceiling was spent first). The
one item whose ship gate was "an ACTUAL LOOK AT THE PICTURE" is the one item nobody looked at.

**Root cause.** Two art nodes in one row, added a year apart and never reconciled. v1616/v1617 put
the item art in the row's GLYPH slot (`icon: _aiIcon`, control_ui.html:11224, and `(_aiIcon || '✶')`
on the fallback row :11242). v1636 then answered Konyo's ask — "the item tancred here should also
have the same logic" — by giving the NAME its own art inside `_aiSay` (:11203). Neither knew about
the other, and no CSS suppressed either copy (:3374 deliberately styles the inline one). The pattern
the change was told to copy, hub-hero-sets, has exactly ONE art node per row.

**Fix.** The art lives on the NAME, because the name is the thing being made clickable; the glyph
went back to being a glyph (`✶`). Both the hero row and the fallback row. `_aiIcon` was then a
symbol with no reader, so it was removed rather than left as a dead seam — LAW19's exact target.

**Prevention.** When a change adds a rendering of X to a row, grep the row's other slots for an
existing rendering of X BEFORE adding one. "Copy the sets hero pattern" means copy its shape — one
art node — not just its ingredients. And a render gate that does not run is not a render gate that
passed: this defect was live in the tree with a green-looking build for the length of one run.

---

## REG-104 — the TZ card's side-by-side layout had been dead since v1567 (a `@media` block written ABOVE the rule it was meant to override)

**Symptom.** The TERROR ZONE card in the Sessions column rendered LIVE NOW and UP NEXT **stacked**,
each one line of text across a 1401px card, at every viewport width. This is a large part of the
"empty space here in the middle... needs to be structured and designed better... so its stretched"
that started the v1636 work — and v1636 answered it by widening cards that were *already* full
width, because nobody ever looked at the page.

**Caught by.** A CDP render gate (`Page.captureScreenshot` — `page.screenshot()` hangs on this
file), at a 1920px viewport. Measured `getComputedStyle('.tz-body').flexDirection === "column"`
with both `.tz-slot`s at 1371px, card height 402.5px. Not caught by four earlier passes that read
selectors, and not catchable that way: the CSS says `flex-direction: row` in plain text.

**Root cause.** `.hd-tz .tz-body { flex-direction: row }` lived inside `@media (min-width: 900px)`
at line 2568, and the base rule `.hd-tz .tz-body { display: flex; flex-direction: column }` sat at
line 2583 — fifteen lines LATER, with identical specificity (two classes). A media query is not
more specific; it only wraps. So the later rule won at every width and the responsive layout never
applied once. The file already knew this trap: the comment at what is now :2769 warns about exactly
it for `.tz-slot .tzz-txt b`.

**Fix.** v1637 moved the `@media (min-width: 900px)` block BELOW the base declaration, unchanged.
Measured after: `flexDirection: "row"`, slots 682px + 682px, `.tz-body` height 267px → 194.1px,
card height 402.5px → 329.6px. A second one-line rule inside the same block lets the zone NAME wrap
to two lines in a half-row slot — at 682px the `.tz-zones` auto-fit puts two zones at ~315px each
and the old `nowrap` + ellipsis truncated "Moo Moo Farm" to "Moo Moo ...". Both states seen painted.

**Prevention.** Two rules, both now provable by script:
1. A `@media` block must come AFTER the base rule it overrides when the selectors are equal. A
   repo-wide sweep of every media-query declaration against later same-selector top-level rules
   found exactly TWO clashes in this file: this one, and `.head-tabs .ht { padding }` — which is
   harmless, because the `!important` rule that beats it is itself shadowed at every width by the
   higher-specificity `.topbar .head-tabs .ht` responsive rules. Left as-is, deliberately.
2. A layout claim is a MEASUREMENT, never a class list. "#hd-forge has no .hd-wide, so it is half a
   column" was asserted about this same panel and is FALSE for forge — measured 1401px of a 1416px
   dash — but the *reason* recorded here in v1637 was also wrong (see REG-105). Forge is full width
   because it is alone in zone Ⅱ and hits `.zone > .hd-col:nth-child(2):last-child { grid-column: 1 / -1 }`,
   not because a sibling's `.hd-wide` collapses the zone's auto-fit track list. Zones keep their
   tracks (`459px 459px 459px` at 1401px); a spanning card spans them, it does not delete them.
   The same prevention rule, applied honestly, would have forced a paint of #hd-lastsession too.

---

## REG-105 — LAST SESSION was the half-column v1637 declared gone without ever painting it (2026-08-04, v1638)

**Symptom.** `#hd-lastsession` in Sessions → Ⅲ THE RECORD rendered at **459px of a 1401px zone**
(one auto-fit track of `459px 459px 459px`), leaving ~942px of black beside a short digest card.
Same dead-column shape v1464 described for the pre-wide taskforce.

**Caught by.** An adversarial re-run of the render gate that *forced the panel visible* with
session-shaped content. v1637's own write-up admitted "NOT ESTABLISHED: the RENDERED WIDTH of
#hd-lastsession" because its stub returned zero sessions and the panel stayed `hidden` / 0×0 —
and then the prose still claimed every Sessions card was full width and that taskforce's
`hd-wide` had "also widened #hd-forge and #hd-lastsession beside it".

**Root cause.** Two independent mistakes:
1. **#hd-lastsession never carried `.hd-wide`**, and it is not alone in zone Ⅲ (kpi / tally /
   chron / vault / history are siblings), so neither the v1507 lone-card rule nor any sibling
   span applies. `grid-column` stayed `auto` → one 459px track.
2. **The v1637 mechanism story was false.** `#hd-forge` and `#hd-lastsession` are not beside
   `#hd-taskforce` at all — forge is alone in zone Ⅱ, lastsession is in zone Ⅲ. Taskforce's
   `hd-wide` cannot widen a card in a different `<section class="zone">`. A 0×0 measurement of a
   hidden panel was treated as evidence the width was fine.

**Fix.** v1638 adds `hd-wide` to `#hd-lastsession`. Re-measured at 1920px with the panel forced
visible: **1401px**, `grid-column: 1 / -1`. `#hd-ls-row` stays `display: flex` (the v1636
subgrid scoped to `#hd-tf-rows` still does not leak).

**Prevention.** A layout claim about panel N is not established by measuring panels {1..N-1}
and a class list for N. Hidden panels measure 0×0 — force the visible state before declaring
width. And a mechanism that names the wrong parent (`#hd-taskforce` "beside" cards in other
zones) is not a mechanism; check the DOM tree, not the class inventory.

## REG-107 — the TZ card spanned the column and clipped every label inside it

**Symptom.** The Sessions column's TERROR ZONE card measured full width (1401px of a 1416px dash),
yet a four-zone rotation rendered as four 157.75px tiles crammed into the 658px LIVE slot: the zone
NAMES measured 0px wide and "act 5" / "700 density · alvl 84" were clipped to 49.8px. 13 text nodes
had scrollWidth > clientWidth. This is the same "empty space / not using the space" complaint the
v1636 pass tried to answer by widening a card that was already full width.

**Caught by.** The render gate that had never run — CDP screenshot + measured geometry at 1920px,
not a selector read. Every prior pass on this card verified by reading CSS. Grok's third-eye note
("#hd-tz already has hd-wide, so if it still looks sparse the cause is INTERNAL") was correct and
had never been tested.

**Root cause.** `.tz-zones` used `repeat(var(--tz-cols, 2), minmax(0, 1fr))`, which obeys the zone
COUNT and ignores the available space. The auto-fit fallback that would have wrapped four zones 2x2
existed but sat under `@media (max-width: 900px)` — only where the grid was never the problem.
v1637's own comment already ASSUMED auto-fit was in force above 900px ("two zones side by side at
~315px each"). It was not. Same defect class as the bug v1637 itself fixed: the right rule parked
in a block that never runs.

**Fix.** One rule at all widths: `grid-template-columns: repeat(auto-fit, minmax(min(238px, 100%), 1fr))`.
`min(238px, 100%)` so a slot narrower than one track wraps instead of overflowing.
Measured after: four tiles at 324.5px in a 2x2 grid, ZERO clipped text nodes (was 13), document
scrollWidth still 1920 = innerWidth, no console errors.

**Prevention.** A media query is a place a rule might never run. When a comment claims a fallback
is active at the width you are looking at, MEASURE the computed `grid-template-columns` — it read
"157.75px 157.75px 157.75px 157.75px" while the source said auto-fit. And a card that is full width
is not a card that uses its width: measure the CHILDREN, not the panel.


---

## REG-108 — "the Forgotten Tower" lost its art because English kept the article (2026-08-04, v1639)

**Symptom.** A three-zone UP NEXT of "Catacombs, Cathedral, and the Forgotten Tower" rendered the
third tile with a rune-glyph placeholder, no act, no density, no level. The other two tiles were
fine. Measured: nameW 216.5, art = linear-gradient placeholder, while Catacombs/Cathedral resolved
to `/art/tz_act1-*.jpg`.

**Caught by.** The render gate that had never run — CDP screenshot of the Sessions TZ card with a
seeded four-zone LIVE + three-zone NEXT rotation. Selector-only passes never hit this string.

**Root cause.** The Oxford-comma splitter strips a leading `and ` after splitting, so
`"and the Forgotten Tower"` becomes `"the Forgotten Tower"`. `_tzKey` then flattens to
`theforgottentower`, which does not match TZ_INFO's `"Forgotten Tower"` (`forgottentower`).
Zones that truly begin with "The" (`The Pit`, `The Chaos Sanctuary`) are the TABLE KEYS and hit
on the first pass; the article-leftover case is the one that silently failed.

**Fix.** v1639: after the flat match fails, if the flat key starts with `the`, try again without
that prefix and return the canonical table key. Display still shows what the feed said; art,
density and tier now resolve.

**Prevention.** Any splitter that peels English conjunctions must be paired with a lookup that
tolerates a leftover article — or the display name must be re-canonicalised through the same
table the art uses. A zone tile with a name and no numbers is a failed lookup, not "thin data".

---

## REG-109 — THE READ CHAIN was a child of CHRONICLE SWEEP (2026-08-04, v1639)

**Symptom.** `#hd-readh` measured `parent = "hd-chron"`. The panel rendered inset (1371px of a
1401px peer column) and every third-eye question of the form "did the A/D/E collapse land on the
read chain or the sweep?" had to dig into a foreign tree. Grok concern (c) was right to demand a
paint check of WHICH panel collapsed — the collapse code was on `#hd-readh`, but `#hd-readh`
itself was inside `#hd-chron`.

**Caught by.** CDP `element.parentElement.id` during the render gate. Not visible to a class-list
read of either id alone.

**Root cause.** When v1537 inserted the read-chain markup, the closing `</div>` of `#hd-chron`
was left BELOW the new card. `#chron-visits` and `#chron-review` (chron children) sat after
`#hd-readh` in source order, so the browser tree nested the read chain inside the sweep.

**Fix.** v1639 moves `#hd-readh` to AFTER the chron section closes (visits + review stay inside
chron). Re-measured: parent is the zone section, width 1401px matching its peers.

**Prevention.** A new `.hd-col` sibling must be inserted at the SECTION level, not into the open
body of the previous card. A render-gate parent check (`#hd-readh` must not be inside `#hd-chron`)
is cheaper than re-litigating "which panel" from screenshots alone.

## REG-110 — a repaired asset was invisible for 24 hours (art had no cache validation)

**Symptom.** Konyo, at v1637, on thumbnails whose files had been fixed at v1636: "the mephisto and
other bosses.. pindleskin diabo. .still NOT FIXED". The picture on screen was still the soulstone.

**Caught by.** Him, looking at the running app — after three separate verifications had all said the
bug was fixed. That is the important part: the FILE was right (opened by eye, identified
independently by Grok against a known-good Andariel, and `art/verify_boss_portraits.py` green on all
10) and the CODE was right (`_runBossArt` -> `BOSS_PORTRAIT[bossId]` -> `art/<file>`). Everything
anyone measured was correct and the user still saw the wrong picture.

**Root cause.** `tv/control_app.py` served every static file, art included, as
`Cache-Control: public, max-age=86400` — which does not merely permit caching, it tells the browser
it may reuse its copy for 24 hours WITHOUT ASKING THE SERVER. v269 broke those two portraits by
overwriting them IN PLACE; v1636 repaired them the same way. Same filename, new bytes, and no
request was ever made. **A repaired asset is invisible until the browser is told to look again.**

**Fix.** Cache VALIDATION instead of cache duration: `Cache-Control: no-cache` (which means "cache,
but revalidate", not "do not cache") plus an ETag over the file bytes, and a 304 for
`If-None-Match`. Measured: first GET 200 + ETag + 154,022 bytes; second GET 304 with no body;
replacing the file changes the ETag, so the browser is forced to re-fetch.

**Why not `?v=` on the URL** (the obvious fix, deliberately rejected): `bible.html` builds art URLs
in ~60 places — static `src="art/…"` plus `artUrl()`, `tzArtFor()`, `_itemArtImg()`, `_runBossArt()`
— so a query-string bust means editing all of them AND every future one. This exact class has
already failed that way twice: a54d5e6/v284 and fdd9849/v287 both one-off patched the v269 art
overwrite and neither generalised. One line at the layer every image passes through cannot be
forgotten by whoever adds the next `<img>`.

**Prevention.** When a fix repairs a file IN PLACE rather than adding one, ask what is allowed to
serve the old bytes — browser cache, CDN, a service worker, a packaged copy. "The file on disk is
correct" is not the same claim as "the user sees the correct file", and only the second one matters.
The live Cloudflare Pages deploy needs the same audit; a cached soulstone there is this bug on a
different server.

## REG-111 — the TZ card showed the BASE area level on a zone that is by definition terrorized

**Symptom.** Konyo, reading the tracker: "lvl 70-73 is okay? i thought 80 was the rarer drop
levels.. but also being Terrorized Zones maybe makes it up more in level?" Jail printed `alvl 71`
beside Ancient's Way at `alvl 82`, so the Jail run read as the weaker choice.

**Caught by.** Him, from the live app — by disbelieving a number rather than by any gate.

**Root cause.** The card printed `t.lvl`, the BASE area level. The board has stated the real rule
since v700 (bible.html:11288): *terror raises any TZ-eligible area to mlvl 96*. While a zone is the
terror zone, its base level is irrelevant — Jail (71) and Ancient's Way (82) are BOTH mlvl 96 and
both reach TC87. Every number on the card was TRUE and the conclusion it invited was FALSE, which is
the worst shape a display bug can take: nothing to catch, because nothing is wrong.

**Fix.** The card now reads `alvl 71 → 96 terrorized`. The base stays — it is what the zone is worth
when it is NOT terrorized, and the density beside it still discriminates between runs — but the
number that decides the run sits next to it.

**Prevention.** When a panel exists only for state X, check every figure on it is the figure that
holds under X. A value copied from the general case into a specialised card is true and useless.

## REG-112 — LIVE NOW and UP NEXT did not line up, because prose changed card height

**Symptom.** "this needs to be symmetric and aligned to the other acts at LIVE. you see how its off."

**Root cause.** Some zones carry a `why` subtitle ("next door to the Ancient Tunnels") and some do
not, so cards were as tall as their prose and the two columns drifted apart row by row.

**Fix.** `.tz-zones { grid-auto-rows: 1fr }` + `.tzz { height: 100% }` — every row in a slot is
equal and the card fills it, so the columns agree whatever text each zone happens to have.

**Prevention.** A card whose height is set by its content cannot align with a sibling card that has
different content. Equal rows must be a property of the GRID, never of the prose.

## REG-114 — a gate that could not fail, and a grid rule that could not reach

**Symptom.** Konyo, on the live TZ tracker: LIVE NOW and UP NEXT still did not line up after v1640
claimed to fix exactly that. A card carrying a `why` subtitle ("next door to the Ancient Tunnels")
stood one prose line taller than one without.

**Caught by.** Konyo's own screen — NOT by the gate, which is the real finding. `grep -c why
tv/demo_console.mjs` was **0**: the demo fixture contained no zone with a `why` subtitle, so every
card in J9 was trivially equal-height and the gate passed 9/9 over a visibly uneven live view. A
gate exercising a case that CANNOT FAIL is the same defect as the `oneRow` proxy v1640 had just
replaced — the assertion changed, the fixture did not.

**Root cause (and the v1640 diagnosis was wrong).** v1640 answered with `grid-auto-rows:1fr` +
`.tzz{height:100%}`. The stated reason — "1fr only equalises rows when the container has a definite
height" — is FALSE: per CSS Grid 12.7.1, with indefinite free space every 1fr track is sized to the
largest track's max-content, so that rule does work inside one grid. That is precisely why it looked
right and was not. The actual reason it could not work: **LIVE NOW and UP NEXT are two SEPARATE
grids in two separate `.tz-slot` boxes, and no grid rule can equalise a row in one grid against a
row in another.** Measured at v1640 with a `why` live and none up next: LIVE 4 cards at 484x139,
NEXT 2 cards at 484x118 — a 21px step, exactly one prose line.

**Fix.** Card height no longer depends on what prose a zone happens to carry. Every optional line
(the act, the `why`, the density) is ALWAYS emitted and always reserves its line, empty or not
(`.tzz-txt i, .tzz-txt em { display:block; min-height:1.25em }`). The `1fr` pair stays — it is still
the right way to let a short card stretch inside its own slot — but it is no longer load-bearing.
The pending-placeholder reserves the same three lines. Measured after: all six cards 484x139,
**spread 0px**.

**Prevention.** The fixture now carries the asymmetry it is meant to police: two `why`-bearing zones
live, none up next. Proven red-then-green — with `tv/control_ui.html` reverted to v1640 and the new
fixture kept, J9 goes RED 8/9; restored, 9/9. J9 also reports its measured geometry
(`["·Stony Tomb 484x139@y456", ...]`) so a future failure names its own numbers. **The durable
lesson is not about CSS: a green gate proves nothing until you have seen it go red for the reason
you care about.** Strengthening an assertion while leaving the fixture unable to trigger it buys
confidence and no coverage.

**Still open, deliberately.** (a) The three missing boss portraits (`dclone` / `pindle` / `pit`)
were NOT shipped — the run's agent ceiling trimmed `bible.html` from the plan. Pindleskin still
falls through to the map-tile level art. (b) The candidate assets are unusable and this is measured,
not assumed: `art/hdx_uberdiablo_icon.png` reads as corrupt scanline noise, and
`art/Pitspawn_Fouldog.gif` depicts a purple horned bovine, not the dog-type unique — so item 3 needs
a real CASC extraction, not a filename. (c) PRE-EXISTING, not a regression: at 1500x1000 the `why`
line clips (`scrollWidth 308` vs `clientWidth 135`); identical on v1640 and here, and J9 does not
see it because J9 runs at a different viewport.

## REG-113 (OPEN, NOT FIXED) — act5-hallsofanguish_graphic.png is a bad extraction, not a dark scene

**Symptom.** Grok, during the v1639 render gate: "depicts a near-black void with faint gold outlines
— not a recognizable Halls of Anguish scene."

**Measured.** mean luminance 7.7 against siblings at 41.3 / 44.2 / 46.1, with the SAME max (241 vs
243) — so content existed and was crushed, not missing.

**What was done, and what it did not achieve.** Exposure corrected (gamma 0.46) to the sibling
profile, mean 7.7 → 42.9. An independent multimodal check then read the corrected file as "murky
dark organic mess — UNREADABLE" while calling its sibling "stone dungeon floor with torch and figure
— READABLE". So the exposure was A problem and not THE problem: this is a bad crop/extraction. The
correction is kept because it removes one confound and matches the sibling profile; **the defect is
NOT fixed.**

**Next.** Re-extract from the game the way v1578 did the TZ art (CASC → .texture → BC3), then verify
by OPENING it and by an independent read — not by luminance statistics, which is exactly what this
entry proves insufficient.

## REG-115 — Routine I: the 27 failures are ONE deterministic set, not flake, and not CI-only

**Symptom.** `Routine I — Playwright suite` has been red since ~v1634 and, per the project record,
has had no green since roughly v651. It had never once been isolated: no failing spec, no failing
assertion, no numbers.

**Caught by.** A deliberate isolation pass on run **30915493081** (v1641, main, 34m16s, 6 shards,
27 failed) cross-read against run **30910708368** (v1640). `📺 TV DIABLO — agent tests` passes on
both commits, so the red is specific to Routine I.

**The two facts nobody had established.**

1. **The failing set does not drift.** Extracting the failing `file:line:col › title` triples from
   both runs and diffing them: **27 vs 27, `diff` empty — byte-identical, same line numbers, same
   titles.** So none of it is shard/parallelism flake, none of it is retry noise, and the suite-tail
   fatigue caveat does not apply. It is 27 deterministic failures.
2. **It is NOT a CI-only artefact.** Four of the failing specs were re-run locally on a clean tree at
   `f8367e6` (= the exact commit CI ran), `nice -n 19 --workers=4`:
   `v518_forge_craft_art_colors`, `v123_inline_item_logos`, `v1518_webdriver_spoof_guard`,
   `v232_tz_tracker` → **6 failed / 10 passed, and the 6 are the same 6 test titles CI reports.**
   The Mac-absolute-path class that caused the last two CI-only reds (REG-…/v1455) is therefore
   ruled out by measurement, not by inspection.

**Root cause.** There is no single root cause — that assumption is why this stayed undiagnosed. The
27 failures decompose into **12 independent groups**, logged below as REG-116…REG-126, of three
different kinds: real app regressions in `bible.html`, specs asserting a design that has since
changed, and one meta-guard whose allowlist went stale. Only ONE group (REG-116's sibling REG-117
aside) has an onset that matches "~v1634": REG-116/REG-118 below.

**Prevention.** Diff the failing-set between two consecutive red runs BEFORE theorising. An identical
set means deterministic and worth grouping; a drifting set means flake and worth quarantining. That
one `diff` is the difference between a 20-minute diagnosis and eight months of an unread red badge.

## REG-116 — the ~v1634 ONSET: three new specs spoof `navigator.webdriver` and never claim the owner world

**Symptom.** `tests/v1518_webdriver_spoof_guard.spec.ts:20` — `expect(offenders).toEqual([])`,
Expected `[]`, Received a 3-name array:
`["v1633_chronicle_celebration.spec.ts", "v1634_craft_chronicle.spec.ts", "v1635_craft_book_painted.spec.ts"]`.

**Caught by.** The v1518 guard itself, working exactly as designed — and reproduced locally (not a
CI artefact). **This is the group whose onset actually explains "red since ~v1634": the offending
specs are named v1633, v1634 and v1635.**

**Root cause.** v1499 makes a browser a GUEST until a human claims it, and identifies the suite by
`navigator.webdriver` + `file://`. These three specs spoof `navigator.webdriver` to false — a
legitimate move, to unmask motion effects the app silences under automation — and in doing so unmask
themselves as guests. Every bare key they seed then lands in an `I·<id>·` world the app never reads,
so they assert against a world that does not exist. REG-084 is the same trap; v1518 was built to
close it, and three specs walked into it anyway within three versions of each other.

**Fix — NOT APPLIED HERE, and the reason is ownership, not doubt.** This diagnosis ran under a
one-file write lock (`BUGS.md`); `tests/*` was not written. The fix is the one the guard prints, one
line per file, at the top of each spec's `beforeEach`/first navigation:

    await page.addInitScript(() => localStorage.setItem('d2r_ownerClaim', '*'));

Applied to `tests/v1633_chronicle_celebration.spec.ts`, `tests/v1634_craft_chronicle.spec.ts`,
`tests/v1635_craft_book_painted.spec.ts`. Verified failing before the change (local run above); the
three specs must be re-run after, because claiming the owner world changes what they see and may
expose real assertions that the guest world was hiding.

**Prevention.** The guard already exists and already works — it named its own offenders and printed
its own fix. What failed is that nobody read a red Routine I for months. The durable lesson: a
self-diagnosing guard is worth nothing behind a badge no one opens.

## REG-117 — the shared `.forge-title` rule WAS repainted globally; v1625 ITEM 6's own assertion says it must not be

**Symptom (9 of the 27 failures — the largest group).**
- `tests/v775_tab_family.spec.ts:24` × 3 — "forge / funi / fsets GOLD title @1500": expected
  `rgb(240, 192, 96)`; received `rgb(0, 252, 0)` for fsets.
- `tests/v1625_board_quality_surfaces.spec.ts:327` — "the plain Forge title must stay chrome gold":
  expected `rgb(240, 192, 96)`, received `rgb(255, 125, 60)`.
- `tests/v1625_board_quality_surfaces.spec.ts:214` — "sealed 🏆 F·Uniques button": expected
  `rgb(199, 179, 119)`, received `rgb(240, 192, 96)` — the **inverse** swap.
- plus `v1628_board_quality_tokens.spec.ts:268` ("the F·Uniques route wears UNIQUE quality"),
  `v1630_sealed_stamp.spec.ts:242`, `v311_unified_rarity.spec.ts:64`, `v331_ask_assistant.spec.ts:192`.

**Root cause — located, with every received colour matched to its token.** `bible.html:7380` is the
v775 family rule, `:is(#tab-forge,#tab-funi,#tab-fsets) .forge-title{ … color:#f0c060 }` = the
`rgb(240,192,96)` gold three specs demand. Four later per-tab overrides beat it on specificity:

    7825: #tab-funi  .forge-title{color:var(--q-unique)}   /* v1625 ITEM6 — per-tab override */
    7830: #tab-forge .forge-title{color:var(--rune)}
    7831: #tab-fsets .forge-title{color:var(--q-set)}
    7832: #tab-fsets .forge-title{color:var(--q-set)}      /* byte-identical duplicate of 7831 */

Token values in the same file: `--q-unique:#c7b377` = `rgb(199,179,119)`, `--rune:#ff7d3c` =
`rgb(255,125,60)`, `--q-set:#00fc00` = `rgb(0,252,0)`. **Every received value above is exactly the
token the override installs** — forge→rune, fsets→set green, funi→unique. That is the whole
mechanism, and it is measured, not inferred.

The sharpest part: **v1625 ITEM 6's own test (`:313`, "the shared `.forge-title` rule was not
repainted globally") is one of the failures.** The change shipped under that item did precisely what
the item's own guard forbade. Line 7830 (`#tab-forge` → `--rune`) has no defender anywhere: v775
wants it gold and v1625 wants it gold.

**Fix — NOT APPLIED. `bible.html` is owned by another agent this run, and one half needs a ruling.**
- Unambiguous: **delete `bible.html:7830`** (plain Forge title returns to `#f0c060`), and delete the
  duplicate at `:7832`. Both v775 and v1625 agree on this.
- Ambiguous, needs Konyo or a design ruling: **v775 and the v1625/v1628 doctrine flatly contradict
  each other on funi and fsets.** v775 (older) asserts all three sibling titles are one GOLD family;
  v1625/v1628 (newer) assert each route wears its own quality. Both cannot pass. Whichever loses must
  have its assertion retired — do not "fix" this by editing whichever file is closest to hand.

**Prevention.** A per-tab override of a rule whose whole stated purpose is "one sibling title colour"
should have failed review at the CSS, not at the assertion. When two specs written 850 versions apart
assert opposite colours for the same element, the contradiction — not either colour — is the bug.

## REG-118 — a runeword's floating item-card title is painted UNIQUE instead of ORANGE

**Symptom.** `tests/v518_forge_craft_art_colors.spec.ts:45` — `expect(r.tipRW).toBe('#ffa800')`,
received `#c7b377`. Corroborated independently by
`tests/v1628_no_literal_quality_hex.spec.ts:254`: "quality colours that disagree with the settled
palette (**1 of 10 checked**)".

**Root cause.** `--q-orange:#ffa800` is the settled runeword colour and `--q-unique:#c7b377` is the
unique colour; the floating card resolves a runeword's title to the unique token. Two independently
written specs, one asserting a literal and one asserting against the live token table, agree — so
this is the app being wrong, not a stale literal. Same family as REG-117 (a quality token applied to
the wrong subject) but a different surface, so it will not be fixed by the `.forge-title` deletion.

**Fix.** NOT APPLIED — `bible.html`-side, owned elsewhere this run. Route the floating card's title
tint through the same quality resolver the board uses; `1 of 10` in v1628 pins the blast radius to a
single entry.

**Prevention.** v1628's "every quality-keyed colour equals its settled token value" is the right
shape of guard and it caught this. It needs to be read.

## REG-119 — v518 asserts a magic-blue literal the settled palette retired (STALE SPEC)

**Symptom.** `tests/v518_forge_craft_art_colors.spec.ts:27` — `expect(r.tipTint).toBe('#9fb0ff')`,
received `#6e6eff`.

**Root cause.** `--q-magic:#6e6eff` in `bible.html`; `#9fb0ff` appears nowhere in the palette. A
jewel IS magic, so the app is rendering the correct token and the spec is asserting a legacy literal
from before the palette settled. **This one is the opposite verdict to REG-118 in the same file** —
line 27 is a stale spec, line 45 is a real regression. Grouping by file would have got both wrong.

**Fix.** NOT APPLIED (`tests/*` not written this run). Assert the resolved value of `var(--q-magic)`
rather than a hardcoded hex, so the spec tracks the palette instead of racing it.

**Prevention.** No spec should hardcode a quality hex — that is exactly what v1628 was created to
forbid, and v518 predates it. Sweep the class: any `toBe('#…')` on a quality-tinted surface is the
same latent failure.

## REG-120 — v232/v234 assert TZ copy retired at v1584-85 / v1588-89 (STALE SPECS, red since ~v1585)

**Symptom.**
- `tests/v232_tz_tracker.spec.ts:46` — `expect(r.count).toContain('huntable')`; received
  `"4 slots · 1 worth running"`.
- `tests/v234_tz_history.spec.ts:62` — `expect(r.fillerName).toBe('Cold Plains and The Cave')`;
  received `"Cold Plains 🔒"`.

**Root cause.** Traced by `git log -S`: `668723b` (v1584-85, "the log ranks its windows, and three
tiers finally look like three") removed the "huntable" copy and introduced "worth running";
`acadf6f` (v1588-89, "locked or routable, and the rotation lives only in Sessions") replaced the
filler zone's spelled-out name with a 🔒 marker. Both changes were deliberate. **These two have been
red since ~v1585, not v1634** — they are part of why "no green since v651" is true while the
proximate onset is REG-116.

**Fix.** NOT APPLIED (`tests/*` not written this run). Re-point both assertions at the current copy —
`'worth running'` and the 🔒 filler marker — keeping the intent (a count line that names how many
zones are worth running; filler zones distinguishable from huntable ones).

**Prevention.** A copy change that renames a user-visible string should grep `tests/` for that string
in the same commit. `git log -S'<old string>'` answers "who changed this and did they mean to" in one
call and was never run here.

## REG-121 — v1577's PARKED allowlist is stale: `uiPrompt` now resolves

**Symptom.** `tests/v1577_dead_seams.spec.ts:140` — "a PARKED name now resolves — it was
implemented. Remove it from PARKED." Diff: Expected `-1` / Received `+0`, the missing entry being
`"uiPrompt"`.

**Root cause.** The v1577 guard deliberately fails when an allowlisted dead name comes alive, so the
allowlist cannot outlive its reason. `uiPrompt` was implemented; the entry was not removed. The guard
is behaving exactly as written — this is bookkeeping, not a defect.

**Fix.** NOT APPLIED (`tests/*` not written this run). Delete the `uiPrompt` entry from `PARKED` in
`tests/v1577_dead_seams.spec.ts`. Verified failing before any change by a local isolated run.

**Prevention.** This is the guard working. The only prevention needed is reading Routine I.

## REG-122 — board and run thumbnails have no boss anchor (same defect as the v1642 portrait item)

**Symptom.**
- `tests/v1624_run_thumbnails.spec.ts:40` — "**Hell Mephisto has no boss anchor**".
- `tests/v1625_fsets_run_thumbnails.spec.ts:102` — "**NM Pindleskin: no data-art-logo, so the
  board's hover card cannot bind**".
- `tests/v1628_board_quality_tokens.spec.ts:392` — "a card with no resolvable subject still rendered
  an `<img>` — that is the arbitrary picture v1624 removed; render nothing instead": expected
  `false`, received `true`.

**Root cause.** The same seam REG-112's "still open" note and the v1642 boss-portrait item describe:
run rows whose boss has no portrait entry cannot bind a hover card, and the v1628 case shows the
fallback still emits an `<img>` for an unresolvable subject instead of rendering nothing. Pindleskin
is literally one of the two portraits the v1642 item exists to add.

**Fix.** NOT APPLIED here — `bible.html`/`art/` are owned by the boss-portrait agent this run. These
three assertions are the correct regression test for that item and should be re-run as its proof.

**Prevention.** Wire the portrait map to a build-time completeness check over the run-row ids, so a
row without a portrait fails at the map rather than at three separate hover-card specs.

## REG-123 — the Task Force grail region renders ZERO times, and the guard that caught it is misnamed

**Symptom.** `tests/v1556_meter_coverage.spec.ts` —
- `:127` `expect(u.found).toBe(P.grail.found)`: expected `243`, received **`null`**.
- `:155` same shape on the A/B payload-swap test.
- `:194` `expect(regions, 'the hub must not print the grail pair in two places').toBe(1)`: expected
  `1`, received **`0`**.

**Root cause — NOT ESTABLISHED, deliberately.** Two readings fit and I could not separate them
inside this pass: (a) the Task Force grail region is genuinely absent from the hub, or (b) this is
another instance of the REG-116 guest-world family, where seeded keys land in an `I·<id>·` world and
the region never renders because there is no data. `received null` and `regions 0` are equally
consistent with both. **Resolve REG-116 first and re-run this spec before touching `bible.html` for
it** — if the ownerClaim fix turns it green, there was never an app defect here.

**Worth noting regardless.** The assertion message says "must not print the grail pair in two
places", but received `0`, not `2`. A guard written against duplication reports its opposite as the
same failure. Split it: assert `≥1` (it exists) and `≤1` (it is not duplicated) separately, so the
message names the actual state.

## REG-124 — `thOpen()` no longer routes off Sessions before unhiding the stage

**Symptom.** `tests/v1612_sessions_no_black_stage.spec.ts:75` — `expect(fn).toContain('_shellHome')`
with the message "thOpen must leave Sessions before opening, or the reel opens on a view that has no
stage". Received source begins `"async function thOpen(){"` and does not contain `_shellHome`.

**Root cause.** `thOpen` was rewritten and lost the `_shellHome` hop. Note the spec asserts on
**function source text**, so it will also fail if the routing is achieved by a differently-named
call — the assertion cannot tell "the behaviour is gone" from "the behaviour moved". Confirm the
behaviour before assuming the regression.

**Fix.** NOT APPLIED — `bible.html`-side. Related: `tests/v877_rinse.spec.ts:194` reports
`stageW` expected `> 400`, received **`0`**, i.e. the self-hosted console stage lays out at zero
width. Same symptom class (a stage that is not there when the reel opens); whether it is the same
cause is **not established**.

**Prevention.** Assert the observable — that the reel opens on a view that owns a stage, measured —
rather than a substring of a function body. A source-text assertion is a proxy, and this project has
already paid for proxies.

## REG-125 — the slot-suffix seam disagrees with itself: one spec demands it kept, another demands it stripped

**Symptom.**
- `tests/v1617_ingame_item_card.spec.ts:119` — expected `"Griswold's Honor (Shield)"`, received
  `"Griswold's Honor"` (suffix **stripped**, spec wants it kept).
- `tests/v134_tools_cards_arthover_routing.spec.ts:75` — "set-tracker pieces get base-name art +
  data-arttip (**slot suffix stripped**, no dead route)" — also failing.

**Root cause — NOT ESTABLISHED.** Two specs, 1483 versions apart, place opposite requirements on the
same slot-suffix handling, and both are red. That means at least one is stale and possibly the
implementation satisfies neither. This needs a single ruling on where the suffix lives (in the
display name, or only in the art-key) before either spec is touched. Fixing whichever is examined
first is exactly how one bug ships three times.

**Fix.** NOT APPLIED — needs the ruling above, then likely one `bible.html` change and one spec
retirement.

**Prevention.** The suffix rule should exist in one named helper that both surfaces call, so the two
specs are testing one implementation instead of two.

## REG-126 — `decorateItemLogos` lost idempotency, and an unmapped tag now decorates

**Symptom.** `tests/v123_inline_item_logos.spec.ts` —
- `:43` `expect(r.first).toBe(0)` ("already ran on load — nothing left to do"): received `1`.
- `:83` `expect(r.added).toBe(0)` ("**unmapped name decorated nothing**"): received `1`.
- `:91` `expect(r.labelKeepsSlot).toBe(true)`: received `false`.

**Root cause.** NOT ESTABLISHED at source level — `bible.html` was not read for this pass because it
is owned elsewhere. But `:83` is the load-bearing one and it is not cosmetic: **a `data-art-logo` tag
with no mapping now gets decorated anyway.** That is the "arbitrary picture" failure mode again
(cf. REG-122 / v1628:392) and the same shape as the corrupt-art class this project keeps re-paying
for — a decoration that fires without a resolvable subject. `:43` (a second call adds one more) says
the guard against re-decoration no longer holds, which is the likely single cause of all three.

**Fix.** NOT APPLIED — `bible.html`-side. Restore the "already decorated" marker check and the
mapped-name precondition; `:43` and `:83` are probably one fix.

**Prevention.** Sweep the class: every decorator that writes into the DOM on a name lookup needs
(a) an idempotency marker and (b) an early return when the lookup misses. `naturalWidth > 0` will
never catch either — it only proves a file loaded, never that anything should have been drawn.

## REG-127 — "no Pindleskin render exists in this repo" — the app's own map had been pointing at one for weeks

**Symptom.** v1642 refused to wire a Pindleskin thumbnail and wrote the refusal into
`art/boss_portraits.manifest.json` as fact: *"There is no Pindleskin picture anywhere in this repo."*
So every `Hell Pindleskin` / `Hell TZ Pindleskin` best-run row kept rendering
`art/tz_exp-wildtemple.jpg` — a bone-strewn top-down TERRAIN tile with no creature in it — under a
hover card promising "open the boss card". Konyo has reported that picture more than once.

**Caught by.** A human, by hand, in one command. `grep -n Pindleskin bible.html` →
`bible.html:14217  "Pindleskin": "art/reanimatedhorde-opt_graphic.png"`. The file is 32KB, dated
2026-06-14, and OPENING it shows a gaunt undead skeleton warrior — bare bone limbs, rectangular
shield on the left arm, a long thin spear angled down — i.e. a Reanimated Horde, which is
Pindleskin's own monster class. The boss picker had been rendering it, labelled 🧟Pindleskin, the
whole time.

**Root cause.** The search that produced "does not exist" was a filesystem search: `ls art/` for a
file named after the boss, plus a look at the 17 super-unique GIFs and at `D2IO_ART`. Pindleskin's
render is not filed under his name — it is filed under his MONSTER CLASS, and only the app's
`name -> art` map knows that. The same run had just solved `dclone` by consulting that exact map
(`bible.html:14336`), so the technique was already in hand and simply was not applied a second time.
An absent result was then written down as a proven negative, which is how a wrong picture acquires a
citation.

**Fix.** v1643 — `BOSS_PORTRAIT.pindle = 'reanimatedhorde-opt_graphic.png'`, pinned in
`art/boss_portraits.manifest.json` with what a human saw, covered by
`art/verify_boss_portraits.py` (which now REQUIRES pindle rather than merely tolerating it, so
re-declining the row cannot go green), and asserted end-to-end in
`tests/v1624_run_thumbnails.spec.ts` — if `BOSS_PORTRAIT` knows a boss, the rendered row must be
wearing that file. `pit` stays on level art deliberately: The Pit is an area farm, not a boss, and
there is no creature to picture. The one refusal that was RIGHT also stands — never borrow `nihl`'s
portrait for pindle, because `_runBossArt` returns `{name: b.name}` and `BOSSES` has
`{"id":"pindle","name":"Pindleskin"}`, so Nihlathak's robed elder would arrive labelled Pindleskin.

**Prevention.** **Before concluding an asset does not exist, ask the app what it already believes.**
An `ls` of `art/` is not the index — the `name -> art` map is, and it is keyed by what the picture
DEPICTS, not by what the row is CALLED. And a negative finding is a claim like any other: it does
not get written into a manifest as settled fact on the strength of one search shape.

## REG-128 — a repaired asset is invisible until its URL changes

**Symptom.** Konyo re-reports pictures that were already fixed. The live one:
`art/diablo_graphic.png` was repaired at v1636 and is CORRECT (opened: a red four-horned clawed
Diablo, 149KB) — and he screenshotted the `Hell TZ Diablo` thumbnail still showing a tan rectangle,
which is what the OLD bytes at that same filename (a leather-bound book) look like at 60px.

**Caught by.** Reading `_runBossArt` after he re-reported a fixed asset: the URL is built as
`'art/' + pic`, with no version query, at every art seam.

**Root cause.** `tv/control_app.py` serves the page as `?v={_app_ver()}`, so a version bump busts
the HTML and the JS and **never the images** — image URLs never changed. v269 rewrote ~230
`art/*_graphic.png` files IN PLACE and v1636 repaired them IN PLACE, same filenames, new bytes.
A cache keyed on URL has no way to know, and correctly keeps serving what it has. Every "I fixed
it, reload" exchange after an in-place asset repair was therefore unfalsifiable on his machine.

**Fix.** v1643 — the build id is appended at every art seam (`_runBossArt`, `_itemArtImg`,
`artUrl`/`D2IO_ART`, the TZ art seam), so a version bump changes the URL of every picture.
`tests/v1624_run_thumbnails.spec.ts` asserts it on the run board: every painted `src`, boss art and
item art alike, must carry `?v=`.

**Prevention.** Any in-place asset repair must change the URL, in the same change. And verification
compares **the bytes the app renders**, not a reload-and-eyeball: "the file changed" is not "the
running system changed" the moment anything caches.

## REG-129 — a stale spec held Routine I red since ~v1634, and the message said so

**Symptom.** `tests/v1624_run_thumbnails.spec.ts:40` —
`expect(r.logo, 'Hell Mephisto has no boss anchor').toBeTruthy()` → *Expected truthy, Received null*.
Routine I red for nine versions; never diagnosed, treated as mysterious.

**Caught by.** Reproducing it locally and measuring all 8 best-run rows: `hasAnchor=true`,
`logo=null`, and every `src` already the correct boss.

**Root cause.** v1636 (`d200b7b`) deliberately replaced `data-art-logo` with `data-boss-tip` on the
best-run `.f-runart` span, for a correct reason: `data-art-logo` resolves through the ITEM art map,
so the row showed Mephisto's correct PORTRAIT while hovering it opened his SOULSTONE. The app was
right and the spec was stale. `getAttribute('data-art-logo')` returns `null` for an attribute that
no longer exists, and **a null was read as a mystery instead of as "the attribute is gone"**.

**Fix.** v1643 — the spec reads `data-boss-tip`. Not as a rename: the old line compared the row
title against the attribute, and the attribute is now an ID, so a straight swap would have asserted
`"Hell TZ Pindleskin".contains("pindle")` — true by luck for four ids and nonsense for the rest
(`"Hell Bovines"` does not contain `cows`). The id is resolved through `BOSSES` to that boss's NAME
and the title must name that boss, which is what the assertion was always reaching for — and it is
the check that catches the defect underneath: best-run Pindleskin rows carrying bossId `nihl`, fixed
at source in the same version. The retired attribute is now itself asserted ABSENT on best-run rows,
so its return (and the soulstone with it) is a red.

**Prevention.** When you rename an attribute the app exposes for measurement, `grep tests/` for the
old name in the same commit. And treat a NULL in a failing assertion as evidence about the shape of
the DOM, not as noise — nine versions of red said "this attribute is gone" in plain text.

## REG-130 — a gate with zero callers guarded nothing for weeks

**Symptom.** `art/verify_boss_portraits.py` — the checker written specifically to stop boss art
being silently swapped — never ran. Boss/manifest drift landed anyway.

**Caught by.** A wiring audit: the script is absent from `hooks/pre-push` (which runs
`visual_lock_invariant.py`, `tv/test_agent.py`, `tv/test_control.py`, `tv/test_tz_art.py`,
`tv/demo_console.mjs` and the Playwright smoke), absent from all 8 `.github/workflows/*.yml`,
absent from `package.json`, and absent from `tests/`. Zero callers.

**Root cause.** The script WORKS — exit 0 on the real tree, exit 1 on deliberate breaks — so it
passed its own hand-run at authoring time and was recorded as done. "It works" and "it runs" are
different properties, and only the first one was ever checked.

**Fix.** v1643 — wired into `hooks/pre-push` as the `boss-portraits` gate, immediately after
`visual-lock`, through the same `gate_run` wrapper (kept log, 120s bound, non-zero exit blocks the
push). Proven from the WIRED path: the hook went red on a real half-landed change (`BOSS_PORTRAIT`
served `pindle` while the manifest still `_declined` it) and printed both mismatches, then green
once the manifest caught up. The script also grew the check that hole implies — a portrait served by
`bible.html` but in NEITHER manifest list is now a failure, not a silent pass.

**Prevention.** A new checker is not done until (a) it is wired into pre-push or CI and (b) somebody
has watched it FAIL from that wired path. A green nobody could ever have seen turn red is not a
green.

**Sweep (v1643).** The same stale read exists in two sibling specs on the same DOM and they are
still red — `tests/v1625_fsets_run_thumbnails.spec.ts:102`
(`expect(r.logo, 'no data-art-logo, so the board's hover card cannot bind').toBeTruthy()` on F·Sets
run rows, which are built by the SAME `_runArtThumb` helper) and
`tests/v1628_board_quality_tokens.spec.ts:490`
(`querySelector('#tab-funi .f-card.f-pipe .f-runart[data-art-logo]')`, a selector that now matches
nothing). Both were left untouched in v1643 only because another agent owned those files during the
run; the diagnosis and the fix are identical to the one applied here — read `data-boss-tip`, resolve
the id through `BOSSES` to a NAME, and compare the name. Until they are updated, Routine I stays red
for this reason and no other. Measured on the v1643 tree: `v1624` 4/4 green, `v1625` 1 failure
(`:90`), `v1628` 1 failure (`:368`), 16 other tests in those two files green.

**Fallout, measured on the v1643 tree, and NOT yet fixed.** Appending `?v=<build>` changes the END
of every art URL, and 14 spec files assert art `src` with an END-ANCHORED regex — 36 assertions of
the shape `expect(src).toMatch(/lister01_graphic\.png$/)`, plus 8 exact-equality `toBe('art/…')`
comparisons. Four of them sit in the PRE-PUSH SMOKE set, so the v1643 push was blocked by its own
gate: `tests/v71_d2art.spec.ts:123` (rune-stash icons), `:219` (boss-nav chips — this one already
asserted `reanimatedhorde-opt_graphic.png` for Pindleskin, which is a second independent witness
that the picture was always there, cf. REG-127), `:273` (Lister's portrait), and
`tests/v74_material_search.spec.ts:77` (Talic statue art). Distribution of the remaining anchored
assertions: v71×10, v47×5, v127×4, v73×3, v78×2, v72×2, v116×2, v113×2, v564×1, v1616×1, v1615×1,
v1614×1, v128×1, v74×1. The mechanical fix is `\.png$` → `\.png(\?|$)` (and `.split('?')[0]` before
an equality compare), which is what `tests/v1624_run_thumbnails.spec.ts` already does.

**Prevention (second lesson, and the expensive one).** A change to the SHAPE of a value — not its
meaning — is a change to every assertion that pattern-matches it. Before shipping a global URL
rewrite, grep the test suite for the OLD shape (`grep -rE '\.(png|jpg|gif)\$/' tests/`) in the same
change. This is the same failure as REG-129 one layer up: an app-side rename that nobody grepped
`tests/` for.

## REG-131 — plain `.q-unique` text surfaces had colour with no glow (v1645)

**Symptom.** Konyo: unique-gold text reads as "just a regular picked theme colour" everywhere
except item tiles, which already glow (`.item-tile.it-r-unique .item-tile-name` at bible.html:264
— `text-shadow:0 0 4px rgba(199,179,119,.55),0 0 10px rgba(199,179,119,.55),0 1px 1px
rgba(0,0,0,.55)`).

**Root cause.** Two independent glow systems coexist in bible.html: (1) a proven per-surface
hardcoded-rgba treatment (item tiles, arttip, aid cards, runeword-card, `.arw-name` names via the
universal rule) and (2) a universal `currentColor`-based glow rule at bible.html:278-279 covering
`.dtp-name,.top-drop-name[class*="q-"],table.drops td.item-name[class*="q-"],table.ref-tbl
td.item-name[class*="q-"],.hvf-name,.set-card-name,.vm-cell-name,.vj-chip,.cw-out-name,
.arw-rune-n,.arw-name,.mw-rune-chip,.rec-chip,.rs-name,.wishlist-item-name,.hero-pick-item,
.gbc-grail-name,.gsearch-lab,.set-piece-name,.zd-hg-name strong,.vault-chip-name,.aid-name-txt`
plus a dedicated `.gic-name` rule (line 279) and `#arttip .att-name` (line 1190). Four surfaces
were bare `color:var(--q-unique)`/`var(--q-runeword)` with NEITHER: `#tab-funi .gf-chip .gf-cname`,
`#tab-funi .gf-piece .gf-nm`, `#tab-funi .forge-title`, `#tab-funi .gf-lastname` (all in the F·Uniques
Forge tab).

**Fix.** Added the proven hardcoded-rgba touch (`text-shadow:0 0 4px rgba(199,179,119,.55),0 0 10px
rgba(199,179,119,.55),0 1px 1px rgba(0,0,0,.55)`) to those 4 selectors only. `--q-unique`/`--rar-unique`
hex value (#c7b377) is UNCHANGED — contrast measured 9.66:1 vs `--bg` and 8.82:1 vs `--surface`,
both unaffected by adding a shadow (WCAG contrast is fill-vs-background, not shadow-dependent).

**Deliberately left bare (already glowing via one of the two existing systems, confirmed by
grep — adding a second glow would double up or silently override the currentColor one with a
harder-coded one):** `table.drops td.item-name.q-unique`, `table.ref-tbl td.item-name.q-unique`,
`.top-drop-row .top-drop-name.q-unique` (all match `[class*="q-"]` in the universal rule),
`.arw-name` (named directly in the universal rule), `#arttip.tip-r-unique .att-name` /
`#arttip.tip-r-rw .att-name` (base `#arttip .att-name` already glows via currentColor, line 1190),
`.aid-card.aid-r-unique .aid-item-name` (its only rendered text is the child `.aid-name-txt` span,
already covered), `.runeword-card .gic-name` (`.gic-name` has its own dedicated 12px currentColor
glow at line 279), `.vault-chip.vc-r-unique > span:not(.d2art-wrap)` (selects `.vault-chip-name`,
already covered). `--rar-runeword`/`--q-runeword` deliberately equals `--q-unique` per existing
doctrine — a runeword surface that inherited the glow via `var(--q-runeword)` is correct, not a bug.

**Pre-existing, NOT caused by this change (verified unrelated: colour values these tests check
were never touched by this edit, and shadow-only diffs don't move a `getComputedStyle().color`
read):** `v1625_board_quality_surfaces.spec.ts` ITEM 3 + ITEM 6 (REG-117, already red on a clean
checkout), `v1628_board_quality_tokens.spec.ts:368` (stale F·Uniques thumbnail art-name lookup,
tracked earlier in this file under the v1643 `?v=` URL fallout), `v1628_no_literal_quality_hex.spec.ts:212`
(fails on the `console` file — tv/control_ui.html, which this change never touches),
`v518_forge_craft_art_colors.spec.ts:19` + `:42` (jewel-tint and runeword/base white-colour checks,
no `--q-unique` involved), `v775_tab_family.spec.ts` forge/funi/fsets GOLD-title checks (expects a
single blanket `rgb(240,192,96)` on `.forge-title`, but `#tab-funi`/`#tab-fsets` already carry
per-tab colour overrides — `var(--q-unique)`/`var(--q-set)` — unrelated to and unchanged by this
edit; `#tab-forge`'s own failure with an untouched `--rune` colour proves the family is broken
independent of this ship).

## REG-134 — MY HUNT bosses and set aggregates had no fact for the console to dress them with

**Symptom (Konyo, screenshots 2026-08-04).** Three labels flat (`Sets · 🧩` / `🏆 Grail` /
`📜 Runewords`) and the MY HUNT panel half-dressed: `Hell Mephisto` and `Hell TZ Pindleskin`
(boss-name SOURCE labels on the grail/set hero) carried no art and no card, and `Griswold's
Legacy` (a set aggregate) had green text but no picture.

**Root cause.** `_writeGrailFarm`/`_writeSetFarm` (bible.html) publish the `d2r_grailFarm` /
`d2r_setFarm` bridges the console reads. They already shipped `art`/`rarity` for the ITEM being
hunted (v1616), but the `source`/`hellSource` fields — the BOSS the item drops from — were bare
strings with no art fact at all, so a console trying to dress "Hell Mephisto" had nothing but a
name and would have had to guess at an item-art lookup — exactly the soulstone-as-Mephisto class
of bug `_runBossArt` (v1629) exists to refuse. Separately, `_writeSetFarm`'s `setArt` called
`artUrl(st.name)` directly with no fallback; a set's collective name carries no sprite of its own
(the daily-pick bridge learned this at v1649 and added a `_setRepArtName` fallback chain there),
so any set whose bare aggregate name doesn't happen to resolve shipped `setArt: null` — measured,
"Cow King's Leathers (set)" was one of his own 9 in-progress sets doing exactly this.

**Fix.** `_writeGrailFarm`/`_writeSetFarm` now publish `sourceArt`/`hellSourceArt` (via the
published `window._runBossArt(bossId)` seam, same one `openBossDetail` and the terror-zone cards
use — no new lookup, no re-derivation) and `sourceBossId`/`hellSourceBossId` so a console-side
click can route to `openBossDetail` instead of an item card. `_writeSetFarm`'s `setArt` now runs
the same `_setRepArtName` → first-missing-piece fallback chain the daily-pick bridge uses, instead
of a bare `artUrl(st.name)`.

**Measured, before → after, via `_writeGrailFarm()`/`_writeSetFarm()` run live in bible.html:**
- `sourceArt`/`hellSourceArt` did not exist before (field absent on every entry); after, e.g. the
  grail hero's Hell source ships `hellSourceArt: "art/reanimatedhorde-opt_graphic.png?v=v1650"`
  (Pindleskin's real portrait, via `_runBossArt`), not an item-art guess.
- `d2r_setFarm[*].setArt` for `"Cow King's Leathers (set)"`: `null` before → 
  `"art/hd_studded_leather.png"` after (the same 9-entry live working set, same run).
- `_artRarity('Frostburn')` (the fact this bridge exports as `rarity`) already read `"unique"`
  before this change — `ITEM_CODEX["Frostburn"].rarity === "unique"` — so the data layer this file
  owns was already correct; if the console renders it as `--text` instead of `--rar-unique` that
  is a control_ui.html class/CSS bug, outside this file, NOT re-derived or re-fixed here.

**Out of scope for this file (bible.html only):** the three label titles (`Sets`/`Grail`/
`Runewords` as coloured HD-art headers), the FROSTBURN computed-colour render check itself, and
routing a click on a boss/set name to the right card — all console-side (tv/control_ui.html)
rendering, owned elsewhere. This ship is the bridge only: publish the facts a console-side fix
would otherwise have had to re-derive.

**Tests.** Ran the 4 spec files that exercise `_writeGrailFarm`/`_writeSetFarm` directly
(`v1554_hero_typography`, `v1616_2_fanout_is_real`, `v1620_set_pieces_and_the_alt`,
`v1630_set_piece_slot_suffix` — 18 tests) unchanged and green; these specs seed synthetic bridge
JSON for console-side assertions and pass the real writer functions with no shape assumptions
that additive fields break.

## REG-135 — the console side of REG-134: the facts were published, nothing consumed them yet (v1651)

**Symptom.** REG-134 shipped `sourceArt`/`hellSourceArt`/`sourceBossId`/`hellSourceBossId` (grail
+ set bridges) and a real `setArt` fallback chain, but `tv/control_ui.html` still rendered
`top.source` (`"hunt at <b>Hell Mephisto</b>"`) and the set aggregate name (`"completes
<b>Griswold's Legacy</b>"`) as bare escaped text — the facts existed on the bridge and nothing on
the console read them. Same gap on the daily-pick sentence: `_chronRotation` always opens the pick
with `🧩 Sets · ` / `🏆 Grail · ` / `📜 Runewords · ` (bible.html:36000/36015/36041), and `_aiSay`
dressed every NAME to the right of that prefix but left the prefix itself flat.

**Fix (tv/control_ui.html only).** Added one shared `_bossChip(label, bossId, art)` builder — a
bossId/art pair resolves to HD art + a floating `_itipAttr` card + a click that calls
`window._hubGoBoss(id)` (→ `openBossDetail`, pre-existing since v1613); no bossId, the label stays
exactly the plain text it was, same "no dead affordance" rule every other chip on this file
follows. Wired into both `hubNextGrail`'s and `hubNextSet`'s `hh-src` line, keyed off the SAME
hell-vs-global branch that picked `top.source` (so the label and the picture can never name two
different bosses on a re-rank). Added a matching `_setChip` for the set-aggregate name using
`meta.setArt` (REG-134's fallback chain) + the same `_hubGoSetPiece` door the piece above it
already uses. Added `_aiHeadDress`/`_AI_HEAD_RE` to `_aiSay` so the sentence's own opening marker
becomes an HD-art + coloured + clickable title (`artImg('sets'|'uniques'|'runes')` + `_rarCls('set'
|'unique'|'rw')`), reusing the same CONSOLE_ART keys and `--rar-*` tokens `_tfChron` already paints
correctly two rows below (proven live, v1615). Runewords is `_rarCls('rw')` → `--rar-runeword`
(#c7b377, GOLD) on purpose, matching REG-132 — not `--rar-rune` (#ff7d3c, the FORGE ROOM accent
used two rows below for a different reason and left untouched).

**FROSTBURN, measured, not assumed.** `tests/v1621_rarity_and_craft_gems.spec.ts` (pre-existing,
unmodified) seeds `d2r_grailFarm` with `rarity:'unique'` for Frostburn and asserts `#hub-hero
.hh-name`'s computed colour — ran it: **8/8 passed**. A throwaway Playwright probe against the live
render (seeded via the same harness as the v1616/v1617/v1620 spec suite) confirms the same node:
`getComputedStyle` → `rgb(199, 179, 119)` = `--rar-unique` (#c7b377), class `hh-name hh-go
r-unique`. It was ALREADY gold. Nothing changed for Frostburn's colour — REG-134's note that
`_artRarity('Frostburn')` already read `'unique'` upstream holds, and the console class chain
(`_rarCls(_meta.rarity || 'unique')` → `.hh-name.r-unique { color: var(--rar-unique) }`) already
resolved it correctly. No fix applied because none was needed.

**Measured, every dressed name, via the same throwaway probe (real `/art/*` files served from
disk, real `getComputedStyle`, real `naturalWidth`):**
| node | text | color | img src | naturalWidth | box |
|---|---|---|---|---|---|
| `#hub-hero .hh-src b.hh-go` | "Hell Mephisto" | rgb(143,230,160) mint (no rarity — a boss, not an item) | `art/mephisto_graphic.png` | **1400** | 134×16 |
| `#hub-hero-sets .hh-name` | "Griswold's Honor" | rgb(0,252,0) green | `art/hd_crown_shield.png` | **185** | 720×33 |
| `#hub-hero-sets .hh-src b.hh-go.r-set` | "Griswold's Legacy" | rgb(0,252,0) green | `art/hd_crown_shield.png` (fallback) | **185** | 169×16 |
| `#hub-hero-sets .hh-src b.hh-go` (boss) | "Hell TZ Pindleskin" | rgb(143,230,160) mint | `art/reanimatedhorde-opt_graphic.png` | **600** | 178×16 |
| `.tf-row.tf-ai b.tf-nm` | "Sets" | rgb(0,252,0) green | `art/ui_tab_fsets.png` | **96** | 64×20 |

All five `onclick` handlers verified present and correctly targeted (`_hubGoBoss("mephisto")`,
`_hubGoBoss("pindle")`, `_hubGoSetPiece(...)` ×2, `_hubGo("fsets")`). Every `naturalWidth` above is
non-zero — a decoded picture, not markup that merely exists.

**Class swept, not just this instance.** `_bossChip` is the ONE builder both heroes call — a third
boss-bearing surface reuses it, not a fourth invention. Checked `_aiMarks`/`_aiChip` (the daily
pick's item+set names) — already dressed since v1636/v1644/v1649, untouched here. Checked the
`_tfChron` room rows (`Runewords`/`Grail Uniques`/`Sets` progress rows, two lines below the daily
pick) — already HD-arted and coloured since v1615/v1636; deliberately left alone (`--rar-rune`
orange there is the FORGE-ROOM accent, a different and intentional token, per the v1636 comment at
control_ui.html:~3876).

**Stale claims corrected.** REG-134's "out of scope for this file" note (listing the three
labels/FROSTBURN check/routing as owed to control_ui.html) is now satisfied by this entry — no
further console-side gap on this arc that I could find inside budget.

**Tests.** Ran `v1616_item_is_the_point`, `v1617_ingame_item_card`, `v1620_set_pieces_and_the_alt`,
`v1628_console_rarity_tokens`, `v1613_hub_routes`, `v1554_hero_typography` (47 tests) — 46 passed,
1 pre-existing fail (`v1617_ingame_item_card.spec.ts:115`, "the NEXT PIECE card matches it", name
assertion off by the `(Shield)` suffix) confirmed failing identically on clean HEAD via `git stash`
— NOT caused by this change, not touched. `v1621_rarity_and_craft_gems` (the FROSTBURN colour
proof, 8 tests) also green. No spec anywhere asserts the OLD flat-text shape of `.hh-src`/the daily
pick's head marker (checked via grep across `tests/*.spec.ts` for `hh-src`/`tf-nm`/`_aiSay`
usages) — the one spec that does inject `.hh-src` HTML (`v1554_hero_typography`) writes it as a
hand-authored fixture, not through `hubNextGrail`, so it is unaffected by this change.
