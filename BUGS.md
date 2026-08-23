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

**2026-08-20 (b) — THE STATED FIX WILL NOT WORK, and here is what will.** Toolchain rebuilt and
PROVEN against this install (CascLib -> /tmp/casc_extract, verified by pulling a known-good sprite
while the game was running; nothing installed system-wide, nothing in the bottle touched). Then the
game's own tables were asked instead of guessing paths:

    levels.txt    Halls of Anguish = "Act 5 - Temple 1", Id 122, LevelType 32
    lvltypes.txt  LevelType 32 = "Act 5 - Temple", tileset Expansion/wildtemple/interior.dt1

That is the answer and it is a negative one. The game ships a TILESET for this zone; the
`*_graphic.png` family is 800x800 SCENE pictures. There is no drop-in asset in CASC to re-extract,
so "re-extract the way v1578 did the TZ art" cannot be followed — v1578's tz_*.jpg set is
per-environment-type and has no act5 member at all (`ls art/tz_act5*` returns nothing).

His own footage was searched too: the live journal holds exactly one Temple frame
(`6_1786554035205`, "Nihlathak's Temple"), and opening it shows the OUTSIDE at the moment of
entering — Harrogath snow and the red portal, not the interior.

**So the fix is a FRAME, not an extraction.** One capture of any wildtemple interior (Halls of
Anguish / Pain / Vaught — all LevelType 32) taken while the console is recording can be processed to
the family's style, which keeps the art self-hosted from his own game exactly as the doctrine
requires. Until then this stays OPEN for a reason now recorded, rather than for a fix nobody could
execute.

**2026-08-20 — re-verified by OPENING it, still OPEN.** Exposure remains in family (mean 42.9 against
siblings 41.3 / 44.2 / 46.1, max 249), so the gamma correction still holds and the luminance confound
is still removed. The picture itself is unchanged: jagged brown-black abstract shapes with one small
purple blob, no floor, no torch, no figure, no architecture — nothing a person would call Halls of
Anguish. That is a second independent read, months after Grok's, agreeing with the diagnosis. It
also re-proves the entry's own warning against a SECOND statistic, not just luminance. The tz_*
family gained a pixel-VARIANCE gate in v1610 after a flat grey tile passed a byte-size floor (real
tiles stdev 14.0-42.7, the blank one 2.8). Measured here: this file's stdev is 24.9, and the
`*_graphic.png` family runs 21.5-61.0 — comfortably healthy and well clear of any floor. Both
statistics say fine while the picture stays wrong, so no threshold will ever close this one.

**2026-08-20 (c) — THE PROCESSOR EXISTS NOW, so the only thing left is the walk.** `art/make_zone_graphic.py`
turns one captured frame into a family-matched `*_graphic.png`:

```
python3 art/make_zone_graphic.py <frame.jpg> act5-hallsofanguish
```

Every number in it is **measured off the four existing family members**, not chosen: 800×800 (centre
-cropped square first, so nothing is squashed), gamma-matched to the family mean band 40.0–46.4, and
saved as mode `P` with 256 adaptive colours — three of the four members are already `P` with 138–206
distinct colours, and a straight RGB save of a game frame lands at ~750KB, seven times the family.

It **refuses** a picture with stdev < 15 rather than shipping it: that is the v1610 failure on the
`tz_*` family, where a blank grey tile passed a byte-size floor. And it prints its two statistics
while saying plainly that **both were already healthy on the broken file** — this entry exists
because luminance 42.9 and variance 24.9 both looked fine while the picture stayed wrong. Open the
result and look at it; no threshold closes this one.

WARNING FOR WHOEVER LOOKS NEXT: `act5-crystallinepassage_graphic.png` is murky enough that judging
the family from it alone suggests they are ALL abstract and nothing is broken. That reading is
wrong. `act5-worldstonekeep_graphic.png` is a stone floor with a lit wall lantern and a figure —
the readable sibling this entry originally cited — and `act5-bloodyfoothills_graphic.png` is a
campfire with flames and a figure. Against those two, hallsofanguish is plainly the outlier. The fix is still a re-extraction,
and it needs the game — not this repo.

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

## v1654 — Tools index chip colour-sync (TINY build)
Konyo: "also color sync all the keywords relevant here too on the tools page" — the Tools tab
index chip rows (`.ti-chip` inside `.ti-g` groups). Synced ONLY the chips naming an item QUALITY,
using the same tokens the board already uses elsewhere (`--rune`, `--q-runeword`, `--q-set`,
`--q-orange`), added via new modifier classes `.ti-q-rune`/`.ti-q-runeword`/`.ti-q-set`/
`.ti-q-crafted` at `.tools-index .ti-chip.ti-q-*` (3319-ish, specificity 0,3,0 — beats both the
`:hover` and `.ti-hot` rules at 0,2,0 so the quality colour holds even on the hot "do now" runes
chip and on hover).
Touched (measured live via Playwright `getComputedStyle`, file:// load, no server):
  - "runes" (rune-stash-card, do-now group, also `.ti-hot`) -> rgb(255,125,60) = `--rune` #ff7d3c
  - "crafts" (craft-workshop-card) -> rgb(255,168,0) = `--q-orange` #ffa800
  - "recipes" (horadric-recipe-card) -> rgb(255,168,0) = `--q-orange` #ffa800
  - "runewords" (all-runewords-card) -> rgb(199,179,119) = `--q-runeword` (resolves to
    `--q-unique` #c7b377, per REG-132 — runewords are gold, not crafted-orange)
  - "sets" (set-tracker-card) -> rgb(0,252,0) = `--q-set` #00fc00
Deliberately LEFT neutral (measured unchanged at rgb(181,164,138) = `--text-muted`): sweep, vault,
chronicle, insights, gems, materials, sunders, AI checker, bases, loot filter, worth, rarity, HVF,
field guide — every one of these names a TOOL or a PLACE, not an item quality; there is no token
for gems/materials/stash (storage/crafting inputs, not qualities) and colouring a tool would make
the vocabulary meaningless. No chip on this page names "uniques" or "grail" currently, so
`--q-unique` direct (not via runeword) was not applied anywhere.
Grepped `tests/v1628_board_quality_tokens.spec.ts`, `v311_unified_rarity.spec.ts`,
`v518_forge_craft_art_colors.spec.ts`, `v1625_board_quality_surfaces.spec.ts` for `.ti-chip` —
zero hits, none assert Tools-index chip colours, so none needed re-running.
Companion piece (console MINI focus chips, item 1 of the same request) is a separate
tv/control_ui.html owner/task, not touched by this bible.html-only edit.

## REG-136 — v1654 MINI focus chips colour-sync (TINY build, item 1: tv/control_ui.html)
Konyo, on the console: "under MINI where on air is. the stash materials runes sets uniques can
also be color synced accordingly to their relevant coding color also." Sole owner of
tv/control_ui.html for this task; the Tools-page half (item 2) above was a companion agent on
bible.html and is untouched by this edit.
Added `.mini-foc .mf[data-f="..."]` rules (~2789-2791, specificity 0,3,0 — ties `.mini-foc .mf.on`
also 0,3,0, resolved by SOURCE ORDER placed after `.on` so category colour wins in both states) for
the three focuses that name an item QUALITY: `runes` -> `var(--rar-rune)`, `chronicle-uniques` ->
`var(--rar-unique)`, `chronicle-sets` -> `var(--rar-set)`. Deliberately left `stash`, `gems`,
`materials` on the existing neutral cream/gold — they are storage/crafting inputs, not item
qualities, and there is no `--rar-*` token for them on purpose (per this file's own console
vocabulary at the top of `control_ui.html`).
Design decision: the category owns the TEXT COLOUR in BOTH the unselected and selected state;
selection is still carried by `.on`'s existing border/background/font-weight, so a synced chip
still reads as visibly "on" without losing its category colour when picked.
Measured live (Playwright, `getComputedStyle`, exact `<style>` block extracted from the file into
a throwaway harness with the real `.mf`/`.mf.on` markup — the live app's `#mini-foc` needs a
running `control_app.py` backend to populate and could not be reached inside budget, so this is
the CSS-cascade truth, not the full app pipeline):
  - `stash` off -> rgb(236,224,200) (`--text-dim`), on -> rgb(240,192,96) (gold) — UNCHANGED
    (deliberately left, confirms no accidental match)
  - `gems` off -> rgb(236,224,200), on -> rgb(240,192,96) — UNCHANGED (deliberately left)
  - `materials` off -> rgb(236,224,200), on -> rgb(240,192,96) — UNCHANGED (deliberately left)
  - `runes` off -> rgb(255,125,60), on -> rgb(255,125,60) = `--rar-rune` #ff7d3c, BOTH states
  - `chronicle-uniques` off -> rgb(199,179,119), on -> rgb(199,179,119) = `--rar-unique` #c7b377,
    BOTH states
  - `chronicle-sets` off -> rgb(0,252,0), on -> rgb(0,252,0) = `--rar-set` #00fc00, BOTH states
  - Selection is still legible: measured `runes` on vs off also differs in border-color
    (rgba(198,166,100,.24) -> rgba(240,192,96,.7)) and background (rgba(0,0,0,.3) ->
    rgba(240,192,96,.14)) — untouched by this change.
Ran `tests/v1603_mini_focus.spec.ts`, `tests/v1614_game_art_icons.spec.ts`,
`tests/v1615_one_concept_one_picture.spec.ts` (the three specs touching `#mini-foc`/`.mf`) —
29/29 passed, none assert `.mf` text colour so none were changed, none needed updating.
NOT proven: computed colour inside the actual running console UI (needs `control_app.py` + a
websocket session, out of budget) — the CSS-cascade proof above is real (same `<style>` block,
same selectors, same markup shape the builder emits) but is not a substitute for opening the live
page. Anyone doubting it should load the console and pick each focus once.

## REG-137 — `_qHex` was the last map still calling a RUNEWORD "crafted", and a stale spec held it there (v1663)
**Symptom (caught by CI, not by eye):** `v518_forge_craft_art_colors` failed
`expect(r.tipRW).toBe('#ffa800')` with `#c7b377`. Investigating that showed the two colour
resolvers openly disagreeing about the same item:
```
_qHex('Breath of the Dying')    -> var(--q-orange)  #ffa800   CRAFTED
_tipTint('Breath of the Dying') -> #c7b377                    unique gold  (correct)
```
**Root cause:** `bible.html:14744`, the `_qHex` rarity map, still read
`rw:'var(--q-orange)', rune:'var(--q-orange)'`. THREE maps in this file assign a colour to `rw`
and the other two were already correct — `_Q_HEX` at 16533 (`rw:_qTok('--q-runeword')`) and the
map at 31963 (`rw:'var(--q-runeword)'`). The v1646 work fixed the CSS and those two maps and
missed this one, so every surface routing through `_qStyle`/`_qHex` — wishlist item names, zone
drop tables, the Forge pipeline card title — painted runeword names **crafted orange**.
`--q-runeword` already existed and already equalled `--q-unique`; it simply was not being used.
**The stale spec was PROTECTING the bug, which is the part worth remembering.** Line 43 asserted
`expect(r.rwHex).toBe('var(--q-orange)')` and therefore **PASSED** for as long as the app was
wrong. A stale assertion does not only fail noisily — it can agree with a defect and hold it in
place. Only the *second* assertion in the same test (`tipRW`, added later against the corrected
`_tipTint`) disagreed, and that internal contradiction is what exposed it.
**Fix:** one line — `rw:'var(--q-runeword)', rune:'var(--rune)'`, leaving `crafted:'var(--q-orange)'`
alone because crafted really is orange. `rune` was changed on the same evidence: both correct maps
already say `rune -> --rune` (#ff7d3c), so this matches existing truth rather than asserting a new one.
**Verification:** `_qHex` and `_tipTint` now agree on `Breath of the Dying`, `Insight` and
`Windforce` (all resolve `#c7b377`), and the v522 pipeline-card test measures the rendered title at
`rgb(199,179,119)` — a real surface, not a function return. 0 page errors.
**Prevention:** the four stale assertions in `v518` were migrated with the reason written beside
them, and the whole rarity-colour spec family (v311, v341, v309, v323, v294, v1621, v301, v130 —
53 tests) was run to prove no other spec carried the same belief. All 53 pass.
**Class:** a fact settled in one place and left wrong in another. Same shape as the CSS
"LAST RULE WINS" trap — when a value lives in more than one map, fixing one is a half fix, and
`grep` for *every* assignment before declaring it done.

## REG-138 — three quality-colour defects the red CI had been hiding (v1664)
Found by working down the standing Routine I failures rather than by eye.
**1. Console TZ "→ 96 terrorized" rendered a colour that exists nowhere else.**
`tv/control_ui.html:2693` had `.tzz-terr{color:var(--q-orange,#d08a3c)}`. The console does not
define `--q-orange` AT ALL — it uses the `--rar-*` family (`--rar-orange:#ffa800`). So the var
never resolved and the fallback `#d08a3c` was what actually painted: a duller orange belonging to
no palette. A board-family token had been written into the console where it can never resolve.
Fixed to `var(--rar-orange)` with NO literal fallback — the token is defined in that same file, so
the fallback was dead code, and a fallback that can never fire is precisely what drifts unnoticed.
*(First attempt used `var(--rar-orange,#ffa800)` and the gate immediately failed it: spelling a
settled hex outside its token definition is itself the violation. The gate caught my fix.)*
**2. The Chronicle Sealed card's 🏆 F·Uniques and 🧩 F·Sets buttons wore CHROME gold.**
`.fs-btn-uni` and `.fs-btn-set` set `--fsq`, `border-color` and `background` — but never `color`,
so the text fell through to `.fs-btn{color:var(--gold-bright,#f0c060)}`. `.fs-btn-craft` DID set
its colour, so the pattern existed and two of three were missed. Added `color:var(--fsq)` to both.
Measured: 🏆 rgb(199,179,119) at 9.66:1, 🧩 rgb(0,252,0) at 14.22:1.
**3. The plain Forge title wore the RUNE-ITEM colour.** `#tab-forge .forge-title{color:var(--rune)}`
(#ff7d3c). `.forge-title` has FIVE colour rules; v1625 ITEM6 designed exactly TWO per-tab overrides
(funi→unique, fsets→set) because a page with no in-game quality keeps chrome gold. v1633 added the
rune override — its commit message is about the Completed subtab and says nothing about it — and in
the same commit duplicated the `#tab-fsets` rule verbatim. Both hallmarks of copy-paste, not a
decision. Removed both; plain Forge measured back at rgb(240,192,96).
**Prevention / lesson:** `grep` for the removed rule still matched — because the comment recording
its removal QUOTES it. A comment describing a bug is textually identical to the bug. Verified by
rendering instead. Same trap as `feedback_comments_vs_code`.

## REG-139 — the Sessions hub emitted item names it never decorated, so they shipped with no art (v1665)
`decorateItemLogos()` runs once via `_v39_whenReady` and again after `openBossDetail`. The Sessions
hub's TWO row renders (`bible.html` ~38191 ops rows, ~38290 TZ rows) emit item names carrying
`data-art-logo` and called neither — so anything painted there stayed undecorated permanently.
**Measured, not guessed:** a probe over `[data-art-logo]` after load found 59 tagged elements and
**2 with no `.d2art-wrap`** — `Tancred's Battlegear` and `Baranar's Star`, both `.zd-item-click`
inside `.sc-row-txt`. Those are the exact two names Konyo had been asking to see wearing HD art.
Fixed by calling `decorateItemLogos()` after each render. It is idempotent (skips any tag that
already has a wrap), so the call costs nothing on a second pass — which is also what the failing
test asserted: `first` and `second` must both decorate ZERO.
**Two renders, not one.** Fixing only the TZ render left the test still red; the ops render at
38191 was the actual source. The class was swept only after the first fix failed to move the number.

## REG-140 — the no-source run bucket rendered a blank 44px square (v1665)
`_runArtThumb` returned `''` when `_runBossArt` resolved nothing, but `.f-cardart` is
`flex:0 0 44px` — so the box still rendered, empty. The file's own rule is "art if we have it, else
a glyph" (`.f-artglyph`, used one line below), and the no-boss case simply fell out of it. Now
renders a neutral ❓ glyph titled "no verified farm source yet". This is NOT the misleading-picture
problem the surrounding comment warns about — a neutral glyph says "we do not know where this
drops", which is exactly true.

## REG-142 — the TZ relay blamed the network for an empty current (v1710)
The console fallback is `the tracker relay could not reach the live site`. That
string fired when `https://bull-4-u.com/api/tz` was 200 and returned
`{current:'', next:'', history:[...]}` — d2runewizard briefly empty, KV still
full. `_tzPaint` treated empty current as DOWN.

Sibling: `/d2r/api/tz` 401. Middleware only ungated `pathname === '/api/tz'`.
The app lives at `/d2r/`, so a relative fetch or a "fixed" upstream 401'd
while the public function was fine.

**Fix:** history-only is a live (stale) payload; both paths open; proxy tries
public `/api/tz` first, gated cousin second; SSL last-resort so a missing CA
bundle on Windows cannot invent an outage.

## REG-141 — a failure answered as health (v1709)
Found by the `tvd-leftover-bugs` hunt (18 raw → 17 verified). Shipped the honesty class, not the
whole list.

1. **`fleet_origin_status`** left `ok=True, behind=0` when `git rev-list` failed, then said
   "unified with origin/main". Doctor used `bn == 0` so a failed count was a green lamp.
2. **`/api/status`** on a thrown journal walk painted `sessionHealth.verdict=idle` and zeroed
   the driver — the same bytes as a real quiet night.
3. **Export + delete + doctor gens** built `HERE/sessions.jsonl` and ignored `TV_SESSIONS` /
   `_journal_path()`. The UI listed the harness file; those routes mutated the production journal.
4. **OCR `mode=err`** with `lines=[]` was accepted as a loot read (`scene=loot`, `conf=0.45`,
   `mode=ocr`).
5. **`_readable_frame`** on JPEG convert-fail returned `frames/eye.jpg` — a different photo
   than the settle frame.
6. **Footer** `st.ver || 'v927'` invented a stamp 776 versions behind when `/api/status` omitted
   `ver`. Now `—`.
7. **`POST /api/g5_toggle`** swallowed `set_mode` and returned 200 last-known status.

**Left for the next ship (confirmed, not this class):** force-kill always `sessionSaved:true`;
TALLIES launcher hidden on Sessions homepage; RECORD/TZ writers painting `display:none` nodes;
chronicle `|| 0` inventing zeros; window pin scoring any titled window; WATCH leftover
`snap_*`/`read_*` frames; WATCH_MODE skipping the D2R pin.
**Verification:** 11 cheap python tests (fleet fail-closed, journal unknown, ring follows
TV_SESSIONS, footer not v927, OCR err is None, convert-fail ≠ eye.jpg). No Playwright on this Mac.

## REG-143 — the farm board routed off data that did not cover the game (v1716)
Konyo, reading his own board: *"for SETS i also see pindleskin as the runs... so thats definitely
bugged.. + i see alot of UNVERIFIED boss hunts for farming which dont render anything at all."*
Both true. Three defects, measured before anything was changed:

1. **SETS had no per-piece drop data.** 14 `(any piece)` aggregate rows stood in for 34 sets.
   `_pickSrc` maximises `kph/chance` and Pindleskin's kph (300-360) is 3-10x every other boss's,
   so the aggregate handed him **two run cards, both Pindleskin** — and the recommended one was
   *NM* Pindleskin, because the sets side never got v1542's hardest-first rule even though
   `_setAggSrc`'s comment claimed it ranked "by the SAME rule as the uniques side". **21 of 34
   sets resolved to no route at all.**
2. **The roster and the drop tables spell items differently.** `reg[n]` was an exact lookup, so
   `Harlequin Crest` could not see the row `Harlequin Crest (Shako)`. Same for `Gull` vs
   `Gull (dagger)` and for four names the roster writes with a curly apostrophe. **33 uniques sat
   in the "no verified source yet" bucket**, the most farmed unique in the game among them.
3. **The tables were genuinely short.** silospen RoW 3.0 lists **348** uniques for Hell Mephisto;
   the tree carried **277**. The v697 pull calibrated cells that already existed and never added
   rows, so ~105 real uniques per boss had no cell to calibrate.

**Fix.** A full silospen pull (D2R_ROW_3_0, MF=300, players=1, desecratedLevel 50/76/99 — the
convention the stored cells were pulled under, re-verified first: **230 of 243** overlapping
Hell-Mephisto rows matched exactly). 2,366 rows added (134 set PIECES with their own per-boss
odds, 93 uniques), 9,820 cells re-synced. One name fold (`_regKey`) reconciles roster to table on
the JS side, binding only when exactly one row answers. Sets route by PIECE, hardest-first.

**Two traps the dry run caught before it wrote:**
- **Never null on a name miss.** The first merge cleared any cell silospen did not list, which
  would have deleted the routes of 18 rows it never mentions at all — the set aggregates, the two
  rune rows, Polaris Spear, The Scourge, Bloodmoon's Light. "Absent from silospen" and "does not
  drop" are different claims. Clearing is now gated on the name being in silospen's pool.
- **Binding must not rename.** Returning the drop row itself renamed the item to the table's
  spelling, and `x.n` is the ledger key: **3 found uniques flipped to missing** on the first pass.
  The roster name stays; only the route is borrowed.

**Result:** no-source uniques 33 → 8 (six Sunder charms, the Hellfire Torch, Crescent Moon — all
genuinely not boss drops); sets with no route 21 → 0; the sets board went from 2 Pindleskin cards
to 8 runs across 5 bosses, Hell first.
**Verification:** `tests/v1716_silospen_sync_routes.spec.ts`, 30/30 gates, rendered and read at
1440 and 375.

## REG-144 — the integrity gate had two probes that could never find their item (v1716)
`L_integrity.js` probes four drop values and diffs them against `baseline/integrity_baseline.json`.
Two of the four — `probe_anda_soj` and `probe_anda_bk` — matched on `i.n === name` with the names
**"Stone of Jordan"** and **"Bul-Kathos' Wedding Band"**, while the rows are called *"The* Stone of
Jordan" and "Bul-Kathos Wedding Band" (no apostrophe). Both returned `{}` on every run since the
day they were written, and `{}` was then committed into the baseline as the expected value. **Half
this gate has been guarding nothing, permanently, while reporting agreement.**
Fixed: the names are corrected, a probe that cannot find its item now returns
`{__NOT_FOUND: name}` so a miss can never read as a clean empty result again, and the baseline
carries the real measurements (SoJ and BKWB at Andariel, six cells each).
Same class as [[feedback-blind-fixture-green-gate]]: a gate that always skips is a gate that never
runs, and baselining its silence makes the silence permanent.

## REG-145 — `tcMax` disagrees with the rows underneath it, table-wide (OPEN, not v1716's doing)
Measured while checking a contradiction the v1716 pull surfaced on the Mephisto card. Each boss
difficulty declares a `tcMax`, and the drop rows in that same cell routinely exceed it: **39 of 66
cells at v1715, before the pull touched anything** (e.g. Normal Mephisto declares TC40 and carries
Bverrit Keep, TC60, at 1:289). The pull took it to 48/66 by adding rows silospen serves.
So `tcMax` is a stale annotation rather than a rule the data obeys — and it is the field the
"blocked" reason strings are built from, which means those strings can name a ceiling the table
itself ignores. NOT rewritten here: 66 values, and correcting them changes what the calculator
tells him is impossible. **His call.**
One consequence WAS fixed, because it was a false sentence on a card whose own table refutes it:
Mephisto's `why` said "BUT TC78 ceiling — can NEVER drop Tyrael's/CoA/Fathom/Griffon's even
terrorized". silospen RoW 3.0 lists all four for terrorized Hell Mephisto in Durance of Hate Level
3 (Tyrael's 1:20,975 · CoA 1:2,331 · Griffon's 1:2,331 · Fathom 1:3,543), and the June v185-B recon
recorded the same Tyrael's figure. The prose now says what the data says.

## REG-147 — the pull redecided the CALCULATOR, which nobody asked it to (v1717)
Bigger than REG-146 and found the same way — by CI, not by me noticing. `ITEMS` is the
calculator's database and `ITEM_REGISTRY` is built from the same loop, so writing 216 new names
into the drop tables put all of them into the Calculator grid too: **322 tiles → 538**, and 66 of
the 69 `_UNI_EXTRA` uniques landed in the one surface bible.html says in words they must never
enter ("appended to the F·Uniques universe ONLY, never the calculator" — v659/v1692). He asked for
the HUNT to route correctly. A data pull must not redecide a curated surface.
Fixed by splitting the two: a row whose name did not exist before the pull carries `nc:1` and
joins ITEM_REGISTRY only; every routing consumer (`_pieceSrc`, `_setAggSrc`, the console bridge,
`funiScan`) reads `window._allDropItems()`, and the four boss-card/calculator render surfaces read
`_calcDrops(boss)`. Calculator back to exactly 322 tiles, `_UNI_EXTRA` leakage back to its
pre-existing 2, and the hunt keeps every route. Gates that moved with it:
`DROP_INDEX_TOTAL = 538` is a NEW lock for the master drop index (the structure test was counting
distinct dropTable names and borrowing the calculator's constant, so one of the two lists had to
be wrong); `CALC_ITEMS_TOTAL` stays 322.
Three more gates were red on their own instrument once the data finally exercised them —
[[gate-blind-to-unexercised-input]] in three flavours: v41's duplicate-droptable signature compared
item NAMES only, and complete tables legitimately converge on the same pool (now name+odds, which a
real copy-paste still trips); v1625's thumbnail check read `naturalWidth` on LAZY images that were
below the fold once the board grew from 2 run cards to 8; and it required the boss ID to appear in
the run title, which `cows` → "Hell Bovines" never satisfies. v619 rebuilt the run grouping out of
`ITEMS` and now asks the engine. 04_item_routing asserted Mephisto "can never" drop Tyrael's — the
same vanilla-think REG-145 found on the card.

## REG-146 — the pull added 11 rows the app cannot open (v1717)
`v645_every_item_sim` failed with 11 `UNREACHABLE:` names and it was RIGHT. silospen RoW 3.0 serves
Entropy Locket, Hellwarden's Will, Latent Bone Break, Latent Flame Rift, Measured Wrath, Opalvein,
Sling, Ars Al'Diabolos, Ars Dul'Mephistos, Ars Tor'Baalos and Gheed's Wager — RotW items this app
carries no card for. v1716 wrote them into the boss tables, where each became a chip that opens
nothing. **110 rows removed.** ITEMS 549 → 538, unrouted names back to 30, exactly the v1715 level.
Giving them a card means adding them to the GRAIL ROSTER, which moves his chronicle denominator —
his call, queued, not a side effect of a data pull.
Also fixed here: my merge matched names PER BOSS, so where one boss lacked a row it added
silospen's spelling — the tree briefly carried both `Cranium Basher` and `The Cranium Basher`.
Renamed to the spelling the tree already used, and ONLY where the pre-merge tree was unambiguous:
`Crescent Moon (amulet)`/`(sword)`, `Hellmouth`/`(gloves)` and `The Hand of Broc`/`(gloves)` are
each two pre-existing spellings that may be two different items, so they were left alone. (My first
pass collapsed the sword into the amulet — caught by reading its own output before committing.)

## REG-148 — four surfaces still read the unfiltered table after the split (v1718, found by the third eye)
Grok, handed the v1717 two-list split and asked to REFUTE "every consumer reads the right list",
did not argue with the call sites — it went at the seam and found four reads of raw
`boss.dropTable` that `_calcDrops` had not been applied to:
- **the boss chip GLOW** (`const has = boss.dropTable.some(...)`) lit a boss for an item whose row
  the table below it hides, and the scroll-to-row that follows then hunts a `tr[data-item]` that
  was never built;
- **two COUNT surfaces** — `show all ${boss.dropTable.length}` and the `all (N)` filter pill —
  disagreed with the filtered rows under them by every `nc` row;
- **the machine-shell boss summary** (`_bRow.dropTable.length`).
All four now read `_calcDrops`.

It also found the sharper thing, which was NOT reachable and is now guarded: **`nc` is a per-ROW
flag while ITEMS membership is decided ONCE, by the first row for that name.** A name that were
`nc:1` on its first boss and plain on a later one would never join ITEMS while `_calcDrops` still
rendered the later row — a click that opens "item not found". Measured: **zero split names**,
because the merge flags by NAME. `window._ncAudit()` is published from inside the BOSSES scope so
the gate can prove it every run instead of skipping, and the gate was **seen RED** for its own
reason first: doctoring one `Axe of Fechmar` row reported `split: ["Axe of Fechmar"]`.

## REG-149 — the Forge could not name a base he owns, and the tab scrolled sideways on his phone (v1719)
Konyo: *"fix the forge so it names bases i own.. only in one step it can show the ones i dont own"*

**The base bug was an ORDERING bug, which is why it looked like a missing feature.**
`_rwLegalBases(rw, limit)` ran `.slice(0, limit || 4)` on the curated meta list and applied the
class/socket filter AFTER, so the answer was always "of these four picks, the legal ones" — never
"the legal ones". A base outside the four could not appear no matter what was in his stash. And
the function never consulted his stash at all: `_forgeMetaBase` is a curated endgame shortlist
with no idea what he owns, so the Forge could only ever recommend shopping.
Measured before: `_rwLegalBases('Rhyme',4)` → Luna / Monarch / Troll Nest / Aegis with a
**Bloodlord Skull (2os) in the stash**, while `_baseRunewords('Bloodlord Skull')` lists Rhyme and
its socket max is 2 — legal, owned, and unreachable.
Fixed: filter first and cut LAST; owned bases enter the same filter and come FIRST, because a base
in hand outranks a better one he would have to find. `opts.ownedOnly` / `opts.notOwned` let one
definition answer two questions — the ONE STEP card keeps showing the ones he does NOT own (his
explicit instruction), and the v1715 shopping list now asks `notOwned` so "bases to buy" can never
list something already in his stash. Seen red first: with the pre-v1719 order restored in a
doctored copy, the owned base is absent and the guard fails.
The footnote stopped calling his own stash a curated pick — "4 endgame homes shown" became
"1 in your stash + 3 endgame homes" ([[label-outlived-referent]]).

**And the phone defect this surfaced.** `.fp-lbl` is `flex:0 0 auto` + `white-space:nowrap`, so the
Forge progress label can neither shrink nor wrap. On his REAL profile it reads "📜 99 / 99
runewords forged · all 99 planned here (8 ladder-only included)" plus a 100% coin and forces the
document to **537px at 375, 390 AND 414** — every phone width, on the tab he reads mid-game. Older
than this change and unrelated to it (identical with and without an owned base). Now wraps below
520px; desktop `white-space`/`flex` verified unchanged by `getComputedStyle`.

**Closed with it: `tests/v1712_onestep_host_bases.spec.ts` (h), red since `fe185ea`.** Two FIXTURE
facts, both measured: a default profile has all 99 runewords MADE so `forgeScan()` returns zero
tiles in every bucket (and a seeded word is un-mark-proof by design — the durable floor purges the
un-mark), and the rune stash is read AT BOOT so writing it and scanning in the same page measures
the old stash. With an empty chronicle and a reload, the whole lane is now provable end to end:
no runes → `ONE STEP: Bloodlord Skull [runes]`; runes in hand → `MAKE NOW: Bloodlord Skull`, and it
leaves ONE STEP. It only passes because v1719 made the owned base reachable at all.

## REG-150 — the eleven, ruled into the roster (v1720)
Konyo: *"add the 11 rotw items to the roster"* — closing the decision v1717 left open.

v1716's silospen pull found 11 uniques RoW 3.0 serves for bosses he farms that this app had no
card for; v1717 removed their drop rows rather than ship chips that open nothing, and said the fix
was his because it moves his chronicle denominator. It is now taken.

**Two of the eleven were never new territory.** `_UNI_EXTRA` already carried Latent Black Cleft,
Latent Cold Rupture, Latent Crack of the Heavens and Latent Rotting Fissure — **four of the six**
Latent sunders. Latent Bone Break and Latent Flame Rift were the missing siblings of a family
already in the roster.

**Measured, before and after:** roster 387 → 398 · `_UNI_EXTRA` 69 → 80 · missing 141 → 152 ·
chronicle rows still dark 16 → **5** · found **246, unchanged** · `d2r_foundLog` **354, unchanged**
· calculator grid **322, unchanged** (he ruled on the roster, so the v1717 separation stands and
the restored rows carry `nc:1`). All 11 resolve as `kind:'unique'`, all 11 carry a farm route, all
11 have art. 246 found + 157 not found = the game's own 403.

**Two hazards checked rather than assumed, both raised by the third eye:**
- **`Sling` is also a vanilla base-item name**, and `d2rResolveItem` tries set-piece → unique →
  base, so a new unique could have hijacked a base name — routing a found base into the grail
  LEDGER instead of the physical vault. Refuted by measurement: `Sling` is not in this app's
  `BASE_DB`, and its resolution went **unknown → unique**, never base → unique. `Bone Break` and
  `Flame Rift` resolved as uniques before and after, unchanged by their new `Latent` siblings.
- **`bible.html:16180` DELETES from `d2r_setPieces` any name found in `_UNI_EXTRA`, and writes.**
  A set-piece collision would have silently edited his set ledger. Checked against all 270 piece
  names in both bare and suffixed form: zero collisions, and none of the eleven is in his ledger.

Also corrected here: the roster block's own comment still said "_UNI_EXTRA (69 keys) … 514 − 127 =
387", 15 versions stale — under a line that warns *a count in a comment is a number nobody
re-measures*. Now 80 / 525 − 127 = 398, re-measured in a browser.

## REG-151 — his top uniques run rested on two columns nothing could reproduce (v1721)
Konyo, on v1720's open item: *"why is this not reproduced though?"* — the right question, and the
answer was not "silospen has no data".

**The pull asked the wrong id.** silospen mints a separate terrorized `d`-suffix id ONLY where the
terrorized variant differs. Its own desecrated SUPERUNIQUE list, read per difficulty, says so:
`NORMAL → Pindleskin` · `NIGHTMARE → Pindleskin` · `HELL → Pindleskin (d)`. v1716 sent
`Pindleskind` at all three, got an empty body at two (silospen's signature for a bad enum, HTTP
always 200), and recorded "no data". The plain id with `desecrated=true` serves it fine: Normal
156 → **184** rows terrorized, Nightmare 261 → **291**.

**And the stored cells were not a pull at all.** Measured three ways before touching them:
- vs silospen at EVERY character level (45/55/60/65/70/71/76): at most **1 exact match of 186**;
- vs every other column of the same boss and the same column of every other boss: **no copy**;
- vs their own base column: Pindle's `hell→hellTz` tracks tightly like every other boss
  (376/536 within ±0.5% of the median ratio), while **`nm→nmTz` is 0 of 190** and
  `norm→normTz` is 3 of 78, with a median ratio of 0.35 — i.e. the TZ column claimed odds ~3×
  better than its own base, which no other TZ column in the file does.
Those two are the only columns in the table that behave like nothing else in it.

**Consequence, which is why this mattered.** `NM TZ Pindleskin` was his number-one uniques run at
**43 items, ~7.9 per hour**. On the real data it is **10 items, ~1.3 per hour** — the yield was
overstated roughly six-fold, and 33 uniques have moved to runs where they are genuinely better
found. `Normal TZ Pindleskin` left the board entirely.

402 `nmTz` and 281 `normTz` cells corrected under the same convention as every other cell
(RoW 3.0, MF=300, players=1, saturation). Nothing added, nothing cleared, and the 36 app-authored
rows silospen's pool never mentions were left exactly as they were — the v1716 out-of-pool rule.

## REG-152 — a ceiling lower than what it lets through (v1722)
Konyo: *"derive it from the rows and gate it"* — the last of the four open decisions.

Each boss difficulty declares `tcMax` (top item tier that kill can produce) and `mlvl`. Both are
hand-authored vanilla-era annotations; the odds beside them have been re-pulled five times (v129,
v187, v697, v1716, v1721) and the annotations never moved. Measured before the fix:

- **50 of 66 cells declared a tcMax BELOW what their own rows prove droppable.** Pindle NORM
  declared TC30 while dropping Ginther's Rift (TC85) at 1:45,761 — silospen's own figure, and
  real: Pindle is an **Act 5** monster, so Normal there is nothing like Act 3 Normal.
- **735 of 737 TC reasons** named a ceiling the same cell contradicts.
- **51 of 66 cells** have rows that drop despite `qlvl > mlvl` — 715 rows — and the engine checks
  THAT branch first, so a wrong mlvl produced a wrong reason before tcMax was ever consulted.

**Fix.** `tcMax` is raised to what its rows prove and **never lowered** — lowering would invent a
ceiling nothing disproves, which is how these went stale in the first place. **`mlvl` is
deliberately NOT derived**: monster level is a game fact, not a ceiling, and rewriting it to "the
highest qlvl seen dropping" would be a right number under a word that stopped being true
([[label-outlived-referent]]). Instead the qlvl reason is SUPPRESSED in any cell whose own data
breaks that rule — no reason beats a false reason. Result: 1,732 blocked reasons, all TC-based,
**zero** citing a rule their own cell disproves.

**The gate.** `tests/v1722_ceiling_invariant.spec.ts` asserts (a) no cell declares a tcMax below
the TC of an item it drops, and (b) no blocked reason cites a rule its own cell disproves. It reads
`window._ceilingAudit()`, published from inside the BOSSES scope — its first draft read
`window.BOSSES`, got `undefined`, and its own non-vacuity assertion caught that rather than passing
on an empty list. **Seen RED**: restoring Mephisto HELL TZ to its stale TC78 reports
`mephisto HELL TZ: declares 78 drops 87`.

Mephisto's card now reads NORM 60 · NORM TZ 85 · NM 85 · NM TZ 85 · HELL 85 · HELL TZ 87, and its
terror line "mlvl jumps to 99 (max TC 87)" is finally consistent with the Tyrael's / Griffon's /
CoA rows v1716 added and the prose v1717 corrected.

## REG-153 — suppressing a false reason deleted the fact it explained (v1723)
v1722 stopped citing `qlvl > mlvl` in cells whose own data breaks that rule. But a row with no
reason gets **no source entry at all** (the builder only pushes a null-chance row when it has a
`blocked` string), so the "cannot drop here" marker vanished along with the bad explanation.
**Routine L caught it within one push**: `probe_meph_shako` lost its `norm` / `normTz` / `nm` keys
outright, where they had been present-and-null — the integrity gate doing precisely the job it
exists for, one commit after two of its four probes were repaired (REG-144).
The item still does not drop there; we simply cannot say WHY from those two annotations. So the row
keeps its entry with a reason true by construction — `not in Normal Mephisto's drop pool`.
[[unknown-stays-unknown]]: "not in the pool" is an answer, an invented rule is not, and **silence
is not either**. Verified by the baseline matching again with NO baseline edit — the fix restored
the invariant rather than moving the goalposts. Guarded: all six Mephisto cells for Shako are
represented, three with odds and three with an honest reason.

## REG-154 — the five he queued (v1724)
Konyo: *"fix those first"* — the five items I had listed as worth queueing.

**1 · A gate that reported it established nothing, and passed.** `v1628`'s boss-anchor check queried
`.f-runart[data-art-logo]`, but **v1636 replaced that attribute with `data-boss-tip`** (its sibling
spec v1625 documents the swap). It found nothing, printed `NOT ESTABLISHED` and RETURNED, so five
assertions were unreached for ~90 versions. Two neighbours did the same: `#tab-forge` art (his
chronicle is complete, so a bare `switchTab` draws nothing — now driven with an empty chronicle:
**0 → 106 images checked**) and boss-card art (**0 → 13**, now opens Mephisto first). All three fail
if they cannot establish their subject.

**4 · `Bloodmoon's Light` is not an item.** Its `ITEM_CODEX` entry gave its base as
**`"Reign of the Warlock"` — the MOD'S NAME** — with empty props, a note describing a sin claw, and
drop numbers cloning Jade Talon (tc85/qlvl71). Absent from ITEM_VALUE, the roster, his ledger and
silospen's pool: six independent signals. Removed from the drop tables, the codex, the tip map and
a placeholder art mapping that pointed at **Skewer of Krintiz's picture**.

**3 · One mis-tagged row was setting ceilings.** `Ginther's Rift` carries tc 85 / qlvl 80 with
reqLvl 37 — internally contradictory, and silospen lists it dropping from NORMAL monsters, which
qlvl 80 forbids. **It alone set the ceiling in 24 of the 29 single-witness cells v1722 raised.**
Ceilings now require **two witnesses** ([[d2r-multiwitness-corroboration]]): 25 cells corrected,
every one still above its pre-v1722 value. Single-witness rows above a ceiling are counted and
pinned, not silently laundered.

**5 · The Pit was the last boss on vanilla-era data.** Modelled per the app's own zone precedent —
one representative dweller. Evidence for the pick: scanning all 341 regular monsters found 28 in a
"Pit" area, of which four are the real Tamoe Highland Pit; **all four share the same 381-item pool
and three of the four give IDENTICAL odds** (`cr_archer3`, an archer, is the outlier), and **Pit
Level 1 ≡ Level 2 across all 381 items**, so it is one run. 1,639 cells updated, 225 rows added,
**384 Hell cells match the pull exactly**.

**2 · `mlvl` — deliberately still open.** v1723 stopped it lying; deriving it would conflate monster
level with item level. It remains flagged, not invented.

**Three of my own defects, each caught by a guard built earlier the same night:**
- the `nc` audit (v1720) caught the Pit merge flagging 200+ names inconsistently — the flag is a
  property of the NAME, so it must be copied from the tree, not inferred per boss;
- restoring `pit` from HEAD silently reintroduced the `Bloodmoon's Light` row I had just deleted,
  and two auxiliary maps still referenced it;
- `tc`/`qlvl`/`tier` are properties of the ITEM, and new Pit rows carrying `0/0` produced **82
  cross-boss contradictions**. All 82 reconciled; the assertion now names its offenders instead of
  reporting a bare count.

## REG-155 — a RUNEWORD was listed as a farmable unique in eleven boss drop tables (v1725)
Found by the 13-agent read-only sweep Konyo authorised, and it is the sharpest thing the sweep
returned. The file classified one key three incompatible ways:

- **`ITEM_TIP['Crescent Moon (sword)']`** (`bible.html:24164`) carries `"t":"Runeword"` and the
  exact affixes of Shael+Um+Tir — *10% CtC Chain Lightning, Ignore Target's Defense, -35% enemy
  lightning resist, Summon Spirit Wolf charges*.
- **`ITEM_CODEX['Crescent Moon (sword)']`** calls it `rarity:'unique'` with `base:'Amulet'`, and its
  props are **byte-identical, same order**, to `Crescent Moon (amulet)`. Its key says sword, its
  base says amulet, its props are the amulet's.
- **Eleven of thirteen bosses carried a drop row for it** — every farmable boss in the app.

**A runeword cannot drop.** He could farm every boss in the game forever for an item that is
forged, not found. 11 rows removed; ITEMS 321 → 320, drop index 548 → 547.

**And it was the cause of an "honest unknown" I had shipped.** v1716 left `Crescent Moon` unrouted
on the reasoning that two different uniques share the name, and v1720's spec pinned that as correct
behaviour. There was only ever ONE Crescent Moon unique. With the runeword row gone the amulet
resolves to a single row and **routes for the first time** — no-source uniques 8 → 7, and the seven
that remain are the six Sunder charms and the Hellfire Torch, all genuinely not boss drops.
The spec now pins the truth and keeps the principle, witnessed by the real duplicate pairs that do
remain (`Hellmouth` / `Hellmouth (gloves)`, `The Hand of Broc` / `(gloves)`).

⚠ **The refutation pass corrected the finder's own argument**: identical odds across rows with
different tc/qlvl is NORMAL here (nine unique amulets share countess-hell 1:13,532 across tc
15/42/60/78), so "identical odds" proves nothing. The tip-table contradiction is the evidence.

## REG-156 — a total typed into 116 strings, stale three times over (v1726)
Konyo: *"do the 312/322 sweep"*. The grail total has been **312, then 322, then 320**, and each time
prose carried the old value:
- **103 off-grail item cards** in `EXTRA_ITEMS[*].desc` read *"Not in the tracked 312/322 grail"* —
  user-visible on every off-grail card. (The sweep attributed these to `ITEM_CODEX`; they are in
  `EXTRA_ITEMS`. Verified before acting: `ITEM_CODEX` contains zero.)
- ~10 zone notes said *"322-item grail count"*, plus *"312-item boss-drop grail"* ×3 and a routine
  description calling itself a *"312-item click sweep"* while its own script reads `ITEMS.length`.
- `GAME_RULES.md` twice, and a *"~300 items"* per-boss figure for tables that now reach 540.

**Fixed by DELETING the numbers, not refreshing them.** None of those sentences needed a total —
"Not in the tracked grail" says everything the reader needs. A count baked into a static string
cannot self-update, which is precisely how it drifted three times.
Guard: `tests/v1726_no_baked_counts.spec.ts` fails on any `NNN-item grail` / `NNN/NNN grail` string
in bible.html or a restated count in GAME_RULES.md. **Seen RED** — reinserting one occurrence names
`bible.html:16961`. It immediately caught a fourth I had not spotted (the `~300 items` line).

## REG-157 — item cards naming the wrong tier of their own base (v1726)
Konyo: *"and the elite/exceptional base audit"*. Audited all 321 codex entries against `BASE_DB`
(the sweep could resolve 189; normalising case first raised it to 259). **Three classes, kept apart:**

**1 · TIER SUBSTITUTION — the card sends him after the wrong item.** Proven without outside
authority, since a unique cannot require a LOWER level than the base it sits on:
- `Jalal's Mane` named **Dream Spirit** (elite, reqLvl 66) while storing reqLvl 42 / reqStr 65. Its
  own note says *"druid grail pelt"*, and of the seven bases at reqStr 65 only **Totemic Mask**
  (exceptional, reqLvl 41) is a pelt — and 41 feeds a unique reqLvl of 42 exactly.
- `Bartuc's Cut-Throat` named **Runic Talons** (elite, reqLvl 60) while storing reqLvl 42 / 79 / 79.
  Exactly one candidate: **Greater Talons** (exceptional, reqLvl 37).

**2 · A BASE THAT IS NOT AN ITEM.** `Andariel's Visage` gave `'demonhead'` — lowercase, matching no
key — while its reqStr 102 matches `Demonhead` (elite) alone. And `Polaris Spear` + `The Scourge`
gave **"Reign of the Warlock"**, the MOD'S NAME, as their base item: the same signature that
identified `Bloodmoon's Light` as a garbled row in v1725. These two are REAL RotW customs, so the
FIELD was nulled rather than the item deleted — unknown beats wrong.

**3 · CASE-ONLY MISMATCHES — 67 of them.** `'bone visage'`, `'armet'`, `'corona'`, `'diadem'`,
`'spired helm'`… none resolved in `BASE_DB`, so 67 item cards could show no base requirements at
all. Normalised to the database's own spelling.

**Counted, not guessed:** three entries name the right base but disagree with its reqLvl by 1–6
(`Darkforce Spawn`/Bloodlord Skull, `Astreon's Iron Ward`/Caduceus, `Ghostflame`/Legend Spike).
Nothing in this repo says which side is wrong, so they are pinned at 3 rather than invented.
**And one candidate was DISMISSED**: `Skystrike` (reqStr 25 on an 18-str Edge Bow) is legal — a
unique may require more than its base. Recorded because a sweep that only reports hits says nothing
about its own precision.

## REG-158 — the TZ zone odds audited end to end, and found CLEAN (v1727)
Konyo: *"do the tz zones diff too"* — the surface the fleet sweep named as its own biggest blind
spot, *"exactly the shape that could be hiding another Crescent Moon"*. It is not. Four axes, all
verified against the live silospen API rather than by reading:

- **Zone → dweller → location wiring: 11 of 11 correct.** Every zone's declared `dweller`
  (`fetish3`, `cr_lancer8`, `bloodlord2` …) really does spawn in its declared `loc`.
- **The duplication is REAL, not a copy-paste.** Seven zones share one identical `hellTz` block,
  which is exactly the signature that unmasked Crescent Moon. Queried independently, **all seven
  dwellers return the identical stored figures** (Tyrael's 1:19,827,272 · Knell Striker
  1:13,616,751 · Entropy Locket 1:8,512,237) — terror saturation puts every one of those areas at
  the same level, so one pool is the truth.
- **528 of 528 stored cells match a live pull exactly.**
- **97 distinct item names, none unknown** to the item universe.

⚠ **My first pass reported 24 mismatches and every one was my instrument.** I queried
`itemQuality=UNIQUE` only, so 24 SET items (Griswold's Honor, Sander's Paragon, Tal Rasha's
Adjudication …) came back absent and read as drift. Merging both qualities: zero.

The single runeword-shaped name in the TZ data, **"Crescent Moon"**, is the real unique AMULET —
and it resolves to exactly one row ONLY because v1725 removed the sword. Before that it was
ambiguous, which is why this looked dangerous and was not.

**The durable artifact is the generalisation.** v1725 removed the runeword from BOSSES only;
`tests/v1727_no_runeword_in_drop_lists.spec.ts` now forbids a runeword-only name in ANY drop list,
requires every TZ odds name to exist in the item universe, and pins the zone wiring. Seen RED:
adding `Enigma` to Mephisto reports `mephisto: Enigma`.

## REG-159 — a feature that disabled itself without saying why (v1728)
The photo intake detects the Anthropic key's monthly usage limit in **seven** places. Exactly ONE
(`bible.html:33172`, the first read) set both `_aiLimitHit` and the banner text `_aiErr`. The six
retry/fallback paths set only the flag, so hitting the cap on a fallback suppressed the read with
**nothing on screen**.

That matters more than a usual missing error: the message exists to say *"⚠ AI usage limit reached
— the Anthropic API key hit its monthly cap … **This is NOT your screenshots — they are fine.**"*
Without it, a capped key is indistinguishable from the AI failing to read his photos, and the
natural response is to go re-shoot screenshots that were never the problem.

**Why they diverged:** `_aiReadJson` was the named wrapper that did both — and it had **zero
callers** anywhere in the repo. Every site hand-rolled the guard, so they drifted apart one by one.
Replaced by `_aiLimitSeen(d)`, called by all seven. Guard: `tests/v1728_ai_limit_says_why.spec.ts`
allows exactly ONE assignment to `_aiLimitHit` (inside the helper) and requires every
`_aiIsLimit(x)` to lead to `_aiLimitSeen(x)`. **Seen RED** — reverting one site reports
`bible.html:33205 — detects the limit but does not explain it`.

⚠ Konyo's correction is recorded, because I had repeated the fleet's framing without checking it:
this is not about him being billed. The cost is a **wrong diagnosis**, not money.

## REG-160 — the last zero-assertion spec in the live suite (v1728)
`tests/_rarity_audit.spec.ts` imports `test` but **not `expect`**, writes `/tmp/rarity_audit.json`
and asserts nothing — yet ran in the live 6-way shard, because the leading underscore filters
nothing (`testDir` is `./tests`, no config excludes it). It could only ever fail by timing out
under full-suite load, or on the Windows half of the dual-machine setup where `/tmp` does not
exist: false reds about nothing.
It is the **last survivor of a class the 2026-06-12 audit swept**, which applied `test.skip(` to
`diag2.spec.ts` and `picks_count_diag.spec.ts` with that exact reasoning and missed this one.
Skipped, not deleted — the diagnostic is useful run deliberately. Verified after: **no live spec
file in the repo now has zero assertions.**

## REG-161 — the F·Uniques title was matt because its glow was its own colour (v1729)
Konyo, from three screenshots: *"even the F-Uniques tab looks dull and matt colored compared to
other sections"* and *"make it the unique that resembles the ingame diablo ii .. matching and
symmetric throughout the console"*.

**Measured, not judged.** The three sibling titles paint:
`Forge #ff7d3c` (vivid orange) · `F·Sets #00fc00` (vivid green) · `F·Uniques #c7b377` (the game's
own unique tan). Two are inherently saturated and carry no glow; F·Uniques is the only muted one —
**and it was the only one WITH a glow, painted `rgba(199,179,119,…)`: the exact same tan as its
base.** A glow the colour of its base lights nothing, so the title was flat by construction.

**The base colour did not move, and that was the important part.** `#c7b377` is his own v1625
ruling (*"F-UNIQUES it can be matched and synced to the uniques color"*), it is D2's
FontColorGoldYellow, three specs pin it, and `v1625_tab_quality_tints.spec.ts:214` explicitly
forbids it collapsing into the console chrome gold `#f0c060` — which is precisely what "just make
it brighter" would have done. Only the glow moved, to the bright end of the same unique-gold family.

**On "symmetric throughout the console": the unique colour already is.** Both surfaces define it
once and identically (`--q-unique` / `--rar-unique` = `#c7b377`), and the rendered audit finds it
painted correctly on both. What is NOT symmetric is the surrounding gold family — **145 distinct
gold/amber hexes in bible.html and 81 in tv/control_ui.html**, several doing the same job (labels,
chips, chrome). That is the real cause of "slightly different between pictures", and it is a
census-scale job, not a hand edit.

## REG-162 — a gate whose verdict depends on what ran before it (CLOSED v1751 — BOTH halves, and the second was never order-dependence at all)

**CLOSED HERE: `test_chronicle_known_wire::AgainstHisRealFootage::test_real_journal_and_reel`.**
Chasing REG-162 turned up a different failure in the same family, and this one was live and red:

```
AssertionError: 8 != 12 : every frame the live agent marked should be read back
```

The test builds `known` from **every** chronicle visit in his journal — all sessions — and then reads
**one** reel, asserting `len(pages) == len(known)`. That held only while his journal happened to
contain visits from that single session. **His Chronicle session tonight added a third visit row (4
frames), `known` became 12, and the test went red on footage that had not changed.** A test standing
on live, growing data has to say which slice of it it is judging.

⚠ **And the obvious fix was wrong.** Scoping by timestamp — match the visit's `"<idx>_<ts>"` against
the reel's `"f_<ts>.jpg"` — found **ZERO overlap**, while `read_reel` was happily binding eight. The
reason is in `_resolve_known`'s own docstring: a mark is a deep-lane frameId, *"a different capture
of the same moment"*, bound to the nearest frame within `JOURNAL_MATCH_MS`. The two captures are
milliseconds apart and never identical. The test now calls **`cr._resolve_known`** — the module's own
join — rather than carrying a second copy of a rule that would drift. **[[copy-drift]]**

### The original REG-162 — a likely cause, with evidence (2026-08-17)

Trying to reproduce it produced the same SHAPE twice, from a cause worth naming: **two gate runs at
once**. I left `run_gates.py` running in the background and started a second one in the foreground.

| run | verdict |
|---|---|
| background (concurrent) | ❌ `robot_smoke` — *"TV_ROBOT lane didn't engage · only 0 journal rows in 20s"* |
| foreground (concurrent) | ❌ `test_roundtrip_sim` |
| **clean single run** | ✅ **30 gates passed** |

Each failing gate passes alone — `test_roundtrip_sim` on its own is 1 passed in 64s. Two runs share
the same ports, the same reel directories and the same journal, so whichever gate happens to need an
exclusive one loses. **That is exactly the signature REG-162 describes**: a gate that is wrong about
the tree depending on what else is happening, and a different gate each time.

This does not *prove* the original sighting was concurrent — I cannot know what else was running that
night — but it is a reproducible cause of that exact symptom, and it matches the standing scar about
running batches locally (his own: local runs made `test_control` take 565s instead of 19.5s and
refused a legitimate push). **The concurrency half is now CLOSED (v1751): a gate run takes an exclusive per-tree lock.**

`tv/run_gates.py` refuses to start while another run holds the same tree, and says who has it:

```
⛔ REFUSED — another gate run already holds this tree (pid 81468, started 2026-08-17 07:17:24, ...).
   Two runs share ports, reel dirs and the journal, so a gate that needs an exclusive one fails
   and the verdict blames the gate. That is REG-162's signature.
```

`flock`, deliberately — the kernel drops it when the holder dies, so a crashed or `kill -9`'d run
cannot leave a stale lock that refuses every run after it. A pid file would need reaping logic, and
reaping logic is how a lock starts lying. Keyed on the RESOLVED tree, so his two worktrees still gate
in parallel; the collision being prevented is within one tree.

All three properties are asserted in `TestOneGateRunPerTree`, and proven red: delete the lock and it
fails on *"a concurrent gate run was ALLOWED — REG-162 can happen again."*

⚠ **A venue trap was caught before it shipped, and it is worth recording because it is the shape that
keeps recurring.** `test_control.py` IS a gate, so under CI's `python3 tv/run_gates.py` the OUTER run
holds the tree lock while this test spawns child gate runs to prove the lock works — the children
would have been refused by the very run testing them, and the class would have been **red on CI and
green on every laptop**. The lock key now honours `D2R_GATE_LOCK_KEY`, the test gives its children a
key of their own, and the fix is verified by holding the real tree lock and running the class anyway.
[[feedback_blind_fixture_green_gate]]

### The "ORDER half" was a 1.2% coin flip on a random directory name (CLOSED v1751)

`test_chronicle_retro` was logged here as order-dependent — *"something earlier in the run leaves
frames or journal rows that make its dedup count read 2"*. **That diagnosis was wrong, and the way it
was wrong is worth more than the fix.**

`read_reel` is pure: it takes no clock, imports no console, and reads nothing it was not handed —
its own docstring says so. Its fixture is a fresh `tempfile.mkdtemp()`. Nothing earlier in a run can
reach it. So the reproduction went at it head-on:

| how it was run | result |
|---|---|
| 30 sequential runs | **0 failures** |
| 6 concurrent runs | **1 failure** |
| 400 iterations in ONE process | **5 divergences (1.25%)** |

One process, no concurrency, still diverging — so it was never about neighbours. The classifier was:

```python
return "chronicle-uniques" if "f0" in p or "f1.jpg" in p or "f2" in p or "f3" in p else None
```

`p` is the FULL PATH, and the fixture directory comes from `mkdtemp()`, which produces names like
**`tmpf2i981c7`**. Measured: **7 of 600 mkdtemp names contain `f0`, `f2` or `f3` — 1.2%**, against an
observed divergence of 1.25%. When one does, *every* frame classifies as a chronicle, the second run
is read too, and the assertion fails `2 != 1`.

Forced deterministically, both directions:

```
OK   dir=tmp_clean_dir  classifier=old -> 1 read
RED  dir=tmpf2i981c7    classifier=old -> 2 reads ['f0.jpg', 'f6.jpg']
OK   dir=tmpf2i981c7    classifier=new -> 1 read
```

**The lesson is the shape, not the line.** A ~1% failure that only ever appears inside a 30-gate run
looks exactly like contamination from a neighbour, because a long run rolls the dice more times. The
tell was that the module under test is pure and clockless — *there was no mechanism by which a
neighbour could have reached it*, and that should have outranked the pattern in the timing.

The classifier now matches `os.path.basename(p)` against an explicit set, which also closes the
second trap in the original line: `"f1" in p` matched `f10.jpg` and `f11.jpg` too. **And the fixture
is now named `f2trap_…` on purpose** — revert to substring-matching the path and the class fails
every time, on the first run, on any machine, instead of 1.2% of the time. A trap the fixture springs
beats a comment asking people not to. [[feedback_suspect_the_instrument]]


`test_chronicle_retro` failed **twice** inside the full 30-gate run tonight with
`AssertionError: 2 != 1 : six identical frames of one page = ONE read`, and passes **3 of 3 alone
in 0.3s**. It is order-dependent: something earlier in the run leaves frames or journal rows that
make its dedup count read 2. Not caused by tonight's changes — it first appeared before most of
them. Recorded rather than dismissed as a flake, because a gate that can be wrong about the tree
depending on its neighbours is the same class as a gate that cannot fail.

## REG-163 — two copies of "why is this cell empty", and only one got fixed (v1730)
**CI caught four regressions the 30 local gates cannot see**, all from one root cause. `deriveBlocked()`
(the CELL renderer's rule, `bible.html:~17500`) is a SECOND implementation of the logic in the
ITEM_REGISTRY builder (`~15850`). v1722 (suppress a qlvl reason the cell's own data disproves) and
v1723 (the honest "not in the drop pool" fallback) corrected the builder — and this copy got
neither. One concept, two hand-copies: the same shape as the runeword, the `nc` flag, and
`_aiReadJson`.

**What he would have seen:** a cell that used to read `TC 60 > NORM TZ Mephisto TC 57` now rendered
an em-dash with an **empty tooltip** — "no data" where it used to say "cannot drop here".

Both callers now share one rule, the boss table is passed in so the qlvl branch is suppressed on
the same evidence, and **the final state carries a tooltip too** (`not in the NORM TZ drop pool`).

**Three specs pinned an explanation that was never true.** `Vampire Gaze` at Meph Norm-TZ was
asserted TC-BLOCKED because the declared ceiling was TC57 — but v1722 measured equipment of tc 78
AND tc 85 dropping in that very cell (`Stormchaser`, `The Grim Reaper`, `Ginther's Rift`), so 57
was never the cap. The item is tc60 / qlvl41 in a cell of mlvl 45: **neither stored number blocks
it, and it still cannot drop.** The FACT was right and the REASON was wrong; the specs now pin the
fact, and a new assertion requires every non-dropping cell to explain itself somehow.

⚠ My jewelry hypothesis was **wrong** and is recorded as such: I expected the inflated ceiling to
come from qlvl-gated jewelry (v187's rule), and measured it to be equipment throughout.

`v311_unified_rarity` probed `_artRarity("Bloodmoon's Light")` — deleted in v1725 as a garbled row,
so `''` is now the correct answer. Replaced with `Polaris Spear`, which exercises the same path: a
real RotW unique carried by `_UNI_EXTRA` with no `ITEM_VALUE` entry.

## REG-164 — two tables stored one required level, and drifted (v1731)
Found by the round-two fleet. I had filed this as unresolvable — *"three items name the right base
but disagree with its level by 1-6, and nothing in the repo says which side is wrong."* **The repo
did say. I had not read `ITEM_TIP`.**

| item | ITEM_CODEX | ITEM_TIP | its base's own reqLvl |
|---|---|---|---|
| Darkforce Spawn | 64 | **65** | Bloodlord Skull **65** |
| Astreon's Iron Ward | 60 | **66** | Caduceus **66** |
| Ghostflame | 62 | **66** | Legend Spike **66** |

Two independent in-file witnesses agree on the higher number; the codex stands alone on the lower
one. And the effective requirement is `max(base, unique)` regardless — no character equips a
Bloodlord Skull below 65. **Both numbers reached a screen**: `renderCodexCard` printed one and the
hover card printed the other, inches apart.

Fixed three ways: the values raised; **the card now DERIVES `max(base, codex)`** so the two
surfaces cannot disagree again (ONE CONCEPT, ONE IMPLEMENTATION); and a gate keeps the
codex-vs-ITEM_TIP disagreement set EMPTY.

That set had a fourth member — `Crescent Moon (sword)`, the runeword. v1725 pulled its drop rows
but left its ITEM_CODEX entry (still claiming `rarity:unique`, `base:'Amulet'`, the amulet's exact
props). **Same removal, two standards** — `Bloodmoon's Light` was taken out of every surface the
same night. The codex entry is now gone; the item is unreachable (`inItems:false`,
`d2rResolveItem → unknown`) and `_artRarity` classifies it `rw`. Its three remaining references are
genuine RUNEWORD data (affix list, art, note) under a legacy key and are deliberately kept.

---

## REG-165 — a terror zone frozen at pre-terror levels, and prose that outlived it (v1732)

`Catacombs L4` stored `mlvl:75, tcMax:75`. Every other Hell terror zone in the file read `mlvl:96`.
Terror saturation lifts all Hell TZ areas to 96, so the stored figures were the PRE-terror numbers
for Andariel, sitting in a field describing the terrorized zone. **[[label-outlived-referent]]**

The cost was not cosmetic. `zoneGrailDrops()` filters by `tcMax`, so the card offered **7** grail
items where the zone really drops **79** — 72 items hidden from a farm-planning surface, including
the entire TC85 elite set. Measured, not argued: forcing the ceiling to TC60 in a fixture shrank
the pool to 4, confirming the pool is a pure function of the ceiling.

Six further zones read `tcMax:85` against a live silospen pull in which all seven dwellers sharing
that `hellTz` block independently returned **Tyrael's Might at 1:19,827,272** — a TC87 item. Those
six were raised to 87. **Arcane Sanctuary was deliberately left at 85**, because its dweller tops
out at TC78; it is the control proving the raise was measured per zone rather than applied blanket,
and a gate now pins it as the single zone below the top ceiling.

### The second defect, which the first one hid

Raising the numbers left the hand-written prose on the same card saying the opposite, two lines
apart:

> 🎯 Andariel (same monster, **no mlvl boost**) … terror doesn't help Andy much, she's **already
> mlvl 75 Hell**. **Same NM SoJ rate. Skip vs Pindle/Pit.**

directly above the card's own generated line, *"Terror lifts this zone to mlvl 96 / TC87 — the
highest ceiling in the game."* All three claims were refuted **by the bible's own data**:

| claim | what the file says |
|---|---|
| "no mlvl boost" / "already mlvl 75" | `BOSSES` has Andariel **HELL TZ = mlvl 87 / TC87** |
| "Same NM SoJ rate" | The Stone of Jordan: **1:2,286 in NM** vs **1:4,014 in Hell TZ** |
| "Skip vs Pindle/Pit" | rested entirely on the TC75 cap just disproved |

The SoJ correction is the interesting one: the truth is STRONGER than the note. NM Andariel really
is the better SoJ kill — by 1.8× — but because the Hell pool is wider, not because terror does
nothing. The card now says that.

### Two copies, as always

Every string existed twice: the `TZ_ZONES` literal and a static pre-rendered card that is what a
no-JS reader is served. The first repair pass fixed the literal and left **five static twins** still
reading `TC 85 max`. **[[copy-drift]]** A `assert count == 1` fired on the sixth string and stopped
a half-applied edit before it was written.

### Gates, and one gate deleted for being unable to fail

* `v1732` — no zone's prose may claim an `mlvl` the zone contradicts, or a `TC` above its ceiling.
  RED on a fixture holding the raised numbers with the stale prose.
* `v1732` — the static pre-rendered card must carry the same figures as the live data. Its FIRST
  version read `document.documentElement.outerHTML` and found **seen=0 on every fixture**, because
  `renderTzZones()` replaces the static cards before a test can look. It was a green gate measuring
  nothing, caught only by its own non-vacuity assertion; it now reads the file. **[[feedback-blind-fixture-green-gate]]**
* `v49` — the old `Catacombs L4 (tc75) reaches NO TC85 elite pool` located its subject as
  `ZS.find(z => z.tcMax < 85)`. Catacombs was the only zone under 85, so that was a de-facto name
  lookup, and the fix made it return `undefined` — the test silently lost its subject. Replaced by
  the saturation invariant (every Hell TZ at mlvl 96, ceilings only 85 or 87, exactly one zone
  below 87), which goes RED on the pre-fix file.
* **DELETED, and recorded rather than quietly dropped:** "no zone pool contains an item above that
  zone's tcMax." It cannot fail — the pool is BUILT by filtering on `tcMax`, so a violating item is
  unconstructible. It would have shipped as a green ★★★ gate protecting nothing.

### Verification

Rendered at 1440 and 375 via CDP. The first three capture attempts were all HARNESS FAULTS and none
of them looked like one: a clip that photographed **Burial Grounds + Crypt + Mausoleum** while the
logged `textContent` said Catacombs (the page re-renders between the scroll and the rect read);
byte-identical 375 captures whose crop missed the changed line; and an `elementFromPoint` calibration
returning NONE at 375 because a fixed bottom bar overlays the card. The harness now proves its own
aim before any capture is trusted, and **refuses a verdict** when it misses. Grok, given the two
renders cold with no hint of the expected values, transcribed `mlvl 96 terror · TC 87 max`,
confirmed the two widths agree, and found no clipping or overlap.

⚠ The before/after fixture lives in `/tmp`, away from the art directory, so **its images cannot
load and it falls back to emoji**. Any art difference between those two shots is the fixture, not
the change.

---

## REG-166 — 192 references to a colour that was never defined (v1733)

`--gold-dim` was referenced **192 times** in `bible.html` and defined **zero** times. It resolved to
the empty string, and CSS handles that silently and destructively:

* `border:1px solid var(--gold-dim)` — the shorthand is invalid at computed-value time, so the
  border becomes `none`. **160 elements carried a border that never drew.**
* `color:var(--gold-dim)` — the declaration is dropped and the element inherits instead. **243
  elements silently took their parent's colour.**

Defining it changed **403 rendered elements across 11 tabs**. Nothing errored, nothing logged, every
gate stayed green — the page simply rendered a design nobody had authored. **[[plumbing-with-no-tap]]**

The worst instance: `.glossary-card`, a modal, measured `background: rgba(0,0,0,0)` and
`border: 0px none` — a floating panel with no surface and no edge, over live page content. It is now
`rgb(36,28,18)` with a `1px solid` gold border.

The value was not invented. `tv/control_ui.html` — the other surface of the same product — has
defined `--gold-dim: #a07830` all along. **[[copy-drift]]**

### The audit that followed, and the four it found

| file | token | uses | resolved to | why that value |
|---|---|---|---|---|
| bible | `--bg-elev1` | 17 | `var(--surface-2)` | the file's own elevation ladder |
| bible | `--bg-elev0` | 12 | `var(--surface)` | ditto; ordering **verified** (luminance 21.0 < 29.3) |
| bible | `--best-dim` | 4 | `color-mix` from `--best` | the idiom this file already uses 72× |
| console | `--text-dim` | 17 | `#756657` | the value bible.html defines for that exact name |

Aliases rather than new hexes, so each colour keeps one source.

`--body` in the console was different in kind: a **font family inside a `font:` shorthand**, which
invalidated the whole declaration and took `--fw-semibold`, `--fs-xs` and the 1.35 line-height down
with it — one missing token killing four properties. The console defines only `--mono` and `--serif`,
so rather than invent a third family the shorthand became longhands: the three intended properties
now apply and the family stays inherited, which is what the element was getting anyway.
**[[unknown-stays-unknown]]**

### Two instrument errors, both caught

1. A **runtime** probe over `getComputedStyle` reported nine bible tokens as undefined that are
   nothing of the kind — they are assigned inline on elements built later. It also reported `--q-`
   with 2,489 uses, which is not a token at all but the literal prefix of `var(--q-${quality})` in a
   template string. The gate is **static** for exactly this reason. **[[feedback-suspect-the-instrument]]**
2. `--rar-rune` looked like a fifth case and is not one. Its only occurrence sits **inside a
   comment** documenting a past state ("the Forge room now wears `--rune`"). I had already defined
   it before stripping comments revealed the reference was prose; the definition was removed. A
   guard that reads comments invents defects, the mirror of a guard blinded BY one.
   **[[feedback-comments-vs-code]]** The same strip cleared a phantom `--a` in the console.

### On the second eye

Given the two full-page renders, Grok reported **"no meaningful difference; no element gained a
border"** — wrong. Given the same change as a crop, it reported "a clear improvement" but described
overlay heights and obscured buttons, which is not what changed. Two mutually inconsistent readings
of one diff. The full-page ask was my error as operator — the skill says the crop is what catches
collisions, and a 1px border is exactly that class — but on this change it added no signal either
way. **The evidence here is the DOM measurement** (`0px none` → `1px solid rgb(160,120,48)`,
`rgba(0,0,0,0)` → `rgb(36,28,18)`), not a vision verdict.

Gate `v1733`: no bare `var()` may name a token nothing ever defines, in either file; plus the
elevation ladder must stay ordered. RED on both pre-fix files, naming exactly the right tokens.

---

## REG-167 — one token, several colours at once (v1734)

The v1733 audit left a second half. A token that is UNDEFINED still renders, via its fallbacks —
and if those fallbacks disagree, the same design token draws different colours in different places.

`tv/control_ui.html` referenced `--gold-bright` twice and defined it nowhere, so both fallbacks were
live and they disagreed: `#itip`'s border drew **#d4a849** while `.hh-go:hover` drew **#f0c060**.
The comment directly above `#itip` states its intent — *"is the board's, so it is the same card at a
legible size rather than a different one"* — and it was not the board's colour. Measured before and
after: `rgb(212,168,73)` → `rgb(240,192,96)`. The console now defines the token at the value
bible.html uses for that name.

**This also corrects the v1733 record.** `--gold-dim` was not merely absent. Across its fallback
sites it was rendering as **six colours at once** — #6a5a38, #8a6f2e, #9a7426, #a07830, #c8a24a,
#caa24a — on top of the 192 bare uses that rendered as nothing. One of those six was already
**#a07830**, the console's value, which is a second independent witness that v1733 chose right.
**[[d2r-multiwitness-corroboration]]**

### A gate written, measured, and thrown away

The first version demanded every fallback EQUAL the definition it backs up. **The count was the
tell**: it flagged 28 sites, including `--text-dim` with twelve different fallbacks and `--text`
with eight. Approximate fallbacks are this file's house style, and while a token IS defined the
token wins — those fallbacks are dead code that never renders. A gate ordering ~28 edits with no
visual effect is a style opinion wearing a gate's clothes.

Worse, I nearly acted on a TRUNCATED view of it: an earlier run printed only the first five and I
was about to "fix three and pin two" on that basis. The five were not the set.
**[[feedback-suspect-the-instrument]]**

For the same reason the 11 `--gold-bright` fallback edits I had already made to `bible.html` were
**reverted**. They were dead code, they changed nothing on screen, and keeping them would have
contradicted the rationale of the gate shipped beside them.

Two sites are recorded and NOT touched: `.aura-tag-target` (`var(--best,#c9a14a)`) and
`.forge-donow-h` (`var(--best,#e8c878)`) put a GOLD fallback on a GREEN token. They render green
today and always have. Either the variable is wrong at those sites or the fallback is a leftover,
and nothing in this repo says which. **[[unknown-stays-unknown]]**

Gate `v1734`: an undefined token may not render as two different values. RED on both pre-fix files,
naming `--gold-bright` in the console and the six-colour `--gold-dim` in the board.

---

## REG-168 — 19 item cards missing their requirements, over a spelling (v1735)

19 of the 62 "unresolved" codex bases were not unresolvable. Every one had a second witness in the
same file — `ITEM_TIP[item].b` — naming a base `BASE_DB` knows perfectly well. Two independent
sources agreed and the codex disagreed with both. **[[d2r-multiwitness-corroboration]]**

**Twelve were misspellings** of real D2 items: `AncientArmor`, `succubae skull`,
`Light Plate Boots`, `Battle Guantlets`, `Espadon`, `CedarBow`, `Long Siege Bow`, `Balista`,
`Heirophant Trophy`, `Stilleto`, `Jo Stalf` — and one **mangled escape**: the file held the literal
characters `Hunter\92s Bow`, a Windows-1252 right single quote that had been escaped into the source
as text.

**Seven named something the game has no base for.** `Girdle`, `Leather Boots` and `Plate Boots` are
not Diablo II items; `Gloves` and `Bracers` are slots, not bases:

| item | codex said | truth |
|---|---|---|
| Corpsemourn | Ornate Armor | Ornate Plate |
| Bladebuckle | Girdle | Plated Belt |
| Hotspur | Leather Boots | Boots |
| Tearhaunch | Plate Boots | Greaves |
| Chance Guards | Bracers | Chain Gloves |
| The Hand of Broc (×2) | Gloves | Leather Gloves |

### What it cost

`renderCodexCard` derives `max(BASE_DB[base].reqLvl, codex.reqLvl)` (v1731), so a base that does not
resolve means **no base data at all**. Measured on Chance Guards, the card gained three things:
the correct base name, a **NORMAL** tier label, and its **item icon** — the art lookup keys off the
base too. Nineteen cards had been quietly missing the requirements they exist to show.

### Every occurrence had to move together

The misspellings were not confined to `ITEM_CODEX` — `Stilleto` appeared **7** times,
`Long Siege Bow` 4, `Heirophant Trophy` 3 — and **`_TIER_CHAIN` carried two of them**. Fixing the
codex alone would have broken the chain against the codex instead of against `BASE_DB`: moving the
defect, not removing it. **[[copy-drift]]** `_TIER_CHAIN` carries a v526 note that it deliberately
uses DISPLAY names so it matches `_baseCats`/`_baseRunewords`; the rename moves it **toward** that
intent, and all twelve corrected names were verified present in the built chain afterwards.

### The gate needed no fuzzy matching

An edit-distance first draft was written and thrown away: it called `Ring` a misspelling of `Kris`
(3 edits apart, and a generic slot rather than a typo), and a length-relative variant then hid
`Balista` because the name was too short. The second witness settles it with no threshold at all —
*if `ITEM_TIP` names a base the DB knows and the codex names one it doesn't, the codex is wrong.*
**[[feedback-suspect-the-instrument]]**

v1726's residue pin tightened **62 → 43**. A pin left 19 above the true count stops catching
anything. `levelGap` is unchanged at 1 (`Ironward/Caduceus`) and case-only mismatches remain 0.

---

## REG-169 — the board changed the protocol; the console was never told (v1736)

`bible.html` publishes `d2r_lsrRoute` so the console never re-derives the fork rule. v1478 built
that. **v1499 then changed the route's vocabulary**: `m` stopped being `'mac'`/`'windows'` and became
`'owner'`/`'guest'`, and the route began carrying the LITERAL prefixes (`pfx`, `lpfx`) so that no
other surface would ever construct one. The board shipped `v:2`.

`tv/control_ui.html`'s `lsFork()` was never told. It still read `r.m` expecting a machine name and
still branched on `machine === 'windows'` — a value the board had stopped writing three versions
earlier. **[[the-unjoined-end]]** — both ends built correctly, the joint never made, silent by
construction.

### Measured, by executing the shipped function against a real v:2 route

With `m: 'guest'`, the `machine === 'windows'` branch cannot fire, so control falls through to
`return localStorage.getItem(bare)`. Two failures in one:

| case | pre-fix result |
|---|---|
| guest world empty, owner's key present | **returned the OWNER's data** |
| guest ladder, owner's `L·` key present | **returned the owner's ladder data** |
| guest main, its own `I·<id8>·` key present | `null` — could not see its own world |
| guest ladder, its own `IL·<id8>·` key present | `null` — same |
| no route at all | returned the owner's data |
| a `v:1` route | returned the owner's data |

The first is the **"HOLY GRAIL 243 / 403 · 60% claimed"** bleed that REG-076 was written to close,
reopened by a vocabulary change rather than by any change to the logic. The third and fourth are
plain blindness: the board writes a guest world at `I·<id8>·` and the console looked at bare.

`lsFork` now mirrors the board's `key()` (bible.html:3655) rather than re-deriving it, takes every
prefix from the payload — **there is no prefix literal left in the file** — and reads NOTHING when
the route is absent or not `v:2`, which is bible.html's own instruction in its own words:
*"A reader that finds no route, a v:1 route, or an id it does not recognise must resolve UNKNOWN and
read nothing. Guessing bare is how the harm happened."*

⚠ If the console ever renders empty where it used to render data, the board has not loaded in that
origin yet — open it once. The answer is never to restore the guess.

### The test that should have caught it had never run

`TestConsoleReadsTheActiveWorld` does the right thing: it EXECUTES the shipped `lsFork` rather than
grepping it, and it was written for exactly this defect class. Two things had gone wrong with it:

1. **It seeded `{v:1, m:'windows'}`** and asserted `W·`/`WL·`/bare/`L·` — the pre-v1499 protocol.
   Every case fed the console an input the board had stopped writing. A real gate, on real data,
   that never once fed the input that breaks it. **[[gate-blind-to-unexercised-input]]**
2. **On this machine it SKIPS.** It drives Chrome with `--dump-dom` over `http://127.0.0.1`, which
   Chrome here never answers — and the skip message says so honestly, even noting *"Playwright
   drives the same binary fine"*. A gate that always skips is the same defect as one that cannot
   fail. **[[feedback-blind-fixture-green-gate]]**

Both fixed: the python cases rewritten to the v:2 vocabulary (8 cases, was 6), and a Playwright
gate added that runs the same cases through a driver that works on this machine. Verified RED
against the pre-fix console — six failures, naming the leak — and green after.

---

## REG-170 — a toggle that only turned things OFF, and a base that ate his runes (v1737)

### The ladder toggle was inverted

Konyo: *"its showing ladder runewords when it shouldnt be when im in non ladder. only when i toggle
it on it should show those 9 runewords."*

`_forgeIncludeLadder()` defaulted to **TRUE**. An unset preference meant INCLUDE, so anyone who had
never touched the control got the ladder-only words in the Forge lanes on a non-ladder character.
The toggle only did anything once switched OFF — the opposite of a control that turns a thing on.
Every other surface had always hidden them off-ladder (the v577 rule), so the Forge was the outlier.

Measured through `forgeScan()` with an empty chronicle and a stocked stash: **before**, all eight
ladder-only words sat in MAKE NOW with the toggle unset; **after**, they sit in the read-only
`ladder` strip and enter MAKE NOW only when the toggle is explicitly on. His other ask — that
ONE-STEP and MAKE NOW follow the same rule — needed no separate fix: both lanes were already gated
by `_rwBlocked`, which consults this predicate. One default, three lanes.

⚠ The set holds **EIGHT** words while three comments and Konyo both say "9". Seven other 2.4-era
words (Pattern, Plague, Obsession, Mist, Flickering Flame, Unbending Will, Wisdom) exist in the file
unmarked. Nothing here says which — if any — is the ninth, so the set is pinned at 8 rather than
guessed at. **[[unknown-stays-unknown]]**

### A base the Forge named, that cost him runes

Konyo: *"voice of reason runeword i created a runword for it in it and it didnt work... i wasted
runewords"* — a 4os Broad Sword, socketed in order, no transform.

**Reproduced exactly.** With a 4os Broad Sword owned and Lem/Ko/El/Eld in the stash, `forgeScan()`
returned `MAKE NOW · Voice of Reason · Broad Sword (4os)`.

By every source this file HAS, that pairing is legal: Broad Sword is a sword, `maxSockets` 4, and
the word reads `"4 socket Swords Maces"`. **That clause is diablo2.io v3.2 data — vanilla.** He
plays Reign of the Warlock, where the AB wiki is the authority and a correct vanilla fact can be
wrong. The repo cannot rule on this pairing; his game can, and did. Recorded per RUNEWORD+BASE in
`_RW_BASE_FAILED`, because Voice of Reason is not broken — that home for it is — and honoured by
both `forgeScan` and `_rwLegalBases`, which had been disagreeing with each other about it.

### Found, measured, and deliberately NOT "fixed"

**2,763 of 7,692** base×runeword pairs (36%, across 281 of 508 bases) need MORE sockets than the
base can ever hold: `_baseRunewords('Broad Sword')` offers Breath of the Dying (6) and Call to Arms
(5) against a cap of 4. **None reached a Forge lane in testing** — forgeScan's per-branch guards
catch them, and its v553 note explains why the cap is deliberately not applied at the cross: an
owned base that ALREADY has N sockets proves it can hold them even where the estimate is low (a 2os
Wand is real though Wand reports max 1). Pinned at 2,763 so it cannot grow unnoticed, rather than
filtered by a rule that would suppress real bases. **[[unknown-stays-unknown]]**

### Fixture note, paid for by v1712 and re-paid here

A default profile has **all 99 runewords marked MADE** (`_RWC_SEED`), so `forgeScan()` returns zero
tiles in every bucket and any assertion about the lanes passes vacuously. Testing PLANNING needs
`d2r_rwProfile='fresh'` with an empty `d2r_rwMade` — and the rune stash is read AT BOOT, so it needs
a reload before the scan. Three of my own probe runs reported "no ladder words in the lanes" while
measuring nothing at all before I found this.

---

## AUDIT (not a defect) — the base↔runeword relation, checked end to end (2026-08-17)

Konyo, after losing runes to a Voice of Reason / Broad Sword pairing: *"make sure you fully audit
the runewords base items we recently added to the database... i dont want random sockets numbers
matching, i need the base item related to the specific and relevant runeword also matched."*

**7,692 base×runeword pairs were checked on two axes.** One finding is real and pinned (REG-170);
the other two were MY instrument, and both are recorded because a sweep that only reports hits
teaches nothing about its own precision.

### 1. Socket reachability — REAL, pinned at 2,763 (see REG-170)

### 2. Type compatibility — 255 flagged, 0 defects. Two separate instrument errors

**First pass** flagged 255 pairs, including `Vigilance` on `Preserved Head`. That was my parser:
it split the multiword category "Shrunken Heads" into "shrunken" + "heads" and matched neither.
Vigilance's clause names shrunken heads *explicitly*. Fixed the parser; the count stayed 255 with a
different composition, which is the tell that a second error was underneath.

**Second pass** flagged 240 pairs — eight shield runewords offered on sorceress orbs (`grimoire`)
and necro shrunken heads (`voodoo head`), whose clauses say only "Shields". I reasoned that since
Vigilance's clause enumerates "Grimoires Shields Shrunken Heads Targes", the enumeration would be
redundant if "Shields" already covered them — so the plain-"Shields" words must be wrong. **That
argument was clean, and the conclusion was false.** I put it to Konyo, he ruled "shields only,
stop offering them", and I measured before implementing:

* `bible.html:10141` records a deliberate v386 decision with better evidence than my inference —
  in D2's ItemTypes.txt, `head` (shrunken heads) and `grim` (grimoires) have **`shld` as their
  equivalent parent**, which is exactly why Rhyme and Splendor really can be made in them.
* And the arithmetic kills it anyway: **all 15 heads and all 15 grimoires cap at exactly 2
  sockets.** Of the eight words, only Rhyme (2) and Splendor (2) can physically fit — 60 pairs.
  The other 180 (Spirit 4, Phoenix 4, Sanctuary 3, Dragon 3, Dream 3, Ancients' Pledge 3) were
  **already counted in the 2,763 impossible set**. I double-counted them and re-presented them as
  a different kind of defect.

Implementing the ruling would have deleted 60 legitimate budget options — Rhyme in a shrunken head
is real and cheap — to fix nothing that was not already blocked. **Not implemented, and the ruling
was returned with the correction rather than executed.** A user answering a question I framed wrong
has not approved the thing I would have built. [[feedback-suspect-the-instrument]]

### What the audit did NOT establish

Nothing here can rule on RotW legality. `RUNEWORD_TIP.b` is diablo2.io v3.2 (vanilla) and `RW_BIS`
is a curated meta list; neither is the AB wiki. The Voice of Reason case proves the two can diverge
and that his game is the only authority available. Per-pair failures he measures in-game go in
`_RW_BASE_FAILED`. **[[unknown-stays-unknown]]**

---

## RESOLVED — "I'm pretty sure there are 9": there are 8, and the data was right (v1738)

Konyo, on the ladder-only runeword set: *"im pretty sure there are 9... look it up and research it."*

He was right to ask and the file was right all along. **The set is EIGHT**, and every surface had
been saying so: `_RW_LADDER_ONLY` holds 8, the Chronicle group header renders `8`, the Forge strip
lists 8, and 91 non-ladder + 8 = the 99 in `RUNEWORD_TIP`.

### What was checked, and what each candidate turned out to be

| candidate | verdict |
|---|---|
| The eight marked | Confirmed by the Season 15 ladder-only list, name for name: Bulwark, Cure, Ground, Hearth, Temper, Metamorphosis (helms), Mania (weapons), Hysteria (body armor) |
| **Mosaic** | WAS ladder-only; moved to non-ladder in **patch 3.1**. Leaving it unmarked is correct, not an omission |
| Void, Ritual, Coven, Authority, Vigilance | RotW's five NEW runewords. All present in `RUNEWORD_TIP`; none ladder-restricted |
| Pattern, Plague, Obsession, Mist, Flickering Flame, Unbending Will, Wisdom | 2.4-era, since released to non-ladder. Correctly unmarked |
| **Hustle** | The best candidate — a real runeword, absent from all 99. **Absent CORRECTLY:** RotW *renamed* it, to **Mania** on weapons and **Hysteria** on body armor. That is why those two share one rune set (`Shael+Ko+Eld`), and why his own `rwVerify` seed recorded both as failing off-ladder |

### Where the 9 came from

**Three claims of "9" lived in this file's prose and none in its data** — `bible.html:16351`
("the 9 ladder words"), `:16416` ("all 9 words unlocked"), and the v1475 note quoting him as
"those 8-9 runewords". That is very likely the origin of the belief: a number under a word,
repeated until it read as a fact. **[[label-outlived-referent]]**

The two that were ASSERTIONS are corrected to 8. His own quoted words stay verbatim — a record of
what he said is not a claim by the file about how many there are — with the research recorded
beside them.

A gate now pins the set to the exact eight names, asserts `Shael+Ko+Eld` resolves to exactly
Mania + Hysteria (if that ever stops being true, the rename has been undone and the count is
genuinely back in question), asserts `Hustle` does NOT reappear, and fails on any file prose
claiming a ladder count that is not 8 — so the number and the data can never drift apart again.

⚠ A stale claim of the same shape was found and fixed next door: the `rwVerify` seed comment says
"the **three** Shael+Ko+Eld combos Konyo proved don't work", and there are two.

---

## v1739 — HD art on the shopping list, and the anchor is the keyword

Konyo: *"for shopping list i want it more upgraded with HD art / image cursor floating for the items
its rendering and the keyword items also."*

**Nothing new was built.** The board has carried a cursor-following art card since v283 — `arttip`,
with the v441 nav-orb that mirrors the hovered sprite — and it fires on any `[data-arttip]`. The
shopping list was simply not wired to it: runes carried an 18px icon and no hover, **bases carried
no art at all**, and the runeword each base is FOR was inert text. All are now anchors — 363 of
them: 33 rune keywords, 91 base keywords, 91 runeword links, 148 alternate bases, plus the
thumbnails. A second floating-preview component would have been `copy-drift` with extra steps.

### The anchor is the keyword, never the cell — and that is v654

The obvious wiring is `data-arttip` on the `.shop-name` grid cell. It was done that way first and
fired **nothing**, because v654 refuses any anchor wider than 430px:

```js
if (_rr.width > 430 || _rr.height > 120) return;
```

Konyo asked for that rule in those words — *"i dont want it opening when i hit the SECTION itself,
only over the specific item keyword; it feels random"* — and measured here, the cells are **480px**
on a rune row and **600px** on a base row. **The rule was working.** His request this time says the
same thing again ("the keyword items also"), so the attribute moved onto the `<b>` name and the
thumbnail: 25px and 18px, comfortably inside the rule that rejected the first attempt.

### Three harness faults on the way, none of which looked like one

1. **Every anchor measured 0x0.** The card lives on `tab-tools` and ships `collapsed` — nothing has
   a box until the tab is switched AND the card opened. Two probes reported "passes" against zeros.
2. **`imgsLoaded: 0`.** `loading="lazy"` with the card off-screen. Forced eager: **124/124 load, 0
   broken.**
3. **Hand-computed hover coordinates landed under the fixed dock** — `elementFromPoint` returned
   `DIV.dock-inner`, so the cursor never reached the anchor and the card "didn't fire". Playwright's
   `hover()` resolves actionability properly, and all six anchor types then opened the card with
   the right art: Zod → `hd_zod_rune.png`, Troll Nest → `hd_bone_shield.png`, Ancients' Pledge →
   `hd_kite_shield.png`, Dusk Shroud → `hd_quilted_armor.png`. **[[feedback-suspect-the-instrument]]**

Verified at 1440 and 375 — no overflow at either. Grok, given the 1440 render cold, described the
floating card's picture as a shield matching Troll Nest, found no clipping or contrast problems,
read the row icons as distinct rather than placeholders, and called the interactive styling
consistent.

---

## REG-171 — two numbers for one farm, and the better one was never shown (v1740)

Konyo: *"the next grail time find is different saying from the sessions like the f-uniques and
f-sets are showing diffrent number for time farming those specific items... cant have two diffrent
numbers for farming.. and its obivously not the quickets either cuz i see in the tabs f-unqies and
f-sets faster ones."*

He was reading **two answers to two different questions** as one contradiction, and the app gave him
no way to tell them apart:

* **F·Uniques ranks ITEMS.** Its card prints `~1.2h to find` — the fastest single item.
* **The Sessions ops queue ranks RUNS.** It takes `funiScan().runs[0]` — the route that yields a
  missing unique fastest — then named ONE item from that run and printed **that item's** odds:
  `Hell TZ Mephisto 1:449`, which is 3.9h.

So the row advertised **3.9h for a decision made on a different number entirely**, and 3.9h loses to
F·Uniques' 1.2h — which is exactly why it read as "not the quickest".

**The rate that justified the pick was computed into `c.op.route` and thrown away before
rendering.** Measured: that run yields a missing unique **every 33 minutes**, which beats every
single-item time on the board. The best number in the app was the one number it never showed.
**[[the-unjoined-end]]**

The row now reads:

> 🏆 Shadow Killer — Hell TZ Mephisto 1:449 **~3.9h to find** · *this run yields ~1 missing unique
> every 33m* · 157 uniques left

The item's time-to-find goes through **`_ttf`**, the exact helper the F·Uniques card prints with, so
the same item now shows the same number on both surfaces — verified equal, boss included.

### Three suspects checked and found innocent, so the fix stayed narrow

| suspect | measured |
|---|---|
| console `_ev_hours` vs board `hoursFor` | **144/144 identical**, 0 mismatches. No formula drift |
| bridge item set vs `funiScan().missing` | identical top 10, nothing dropped, 144 vs 144 |
| two source-pickers | **real, and nearly harmless**: `_pickSrc` maximises `kph/chance` (kph fallback **30**, skips `blocked`) while the bridge minimises `hoursFor` (fallback **100**, skips `chance <= 50`). Across 144 items they disagree on the boss for **zero** and on hours for **one** — Gheed's Fortune, 12% |

That last one is a genuine two-implementations-of-one-rule and it is **recorded, not fixed on the
way past**: it is not what he was seeing, and changing a picker while chasing a different defect is
how two fixes break each other. **[[two-fixes-broke-each-other]]**

### Instrument errors on the way

* `document.getElementById('tab-sessions')` does not exist — the tab is **`tab-session`**, singular.
  My first scrape fell back to `document.body`, so "Sessions shows 3.9h" was measured **on the whole
  page**, not on that tab. The conclusion happened to survive; the method did not.
* `window.effChance` / `window.hoursFor` are `undefined` — both are MODULE-scoped and reachable only
  as bare identifiers inside `evaluate()`. Reading them off `window` leaves every comparison null,
  and the first version of the v1740 gate passed over an **empty set** until its own non-vacuity
  assertion failed it. **[[feedback-blind-fixture-green-gate]]**

⚠ Noted, not chased: `bloodcrescent` is `tier:'common'` and lower-cased, sits in the bridge at
1.04h, and is invisible on F·Uniques (whose display excludes that tier). One of the two surfaces is
wrong about whether it belongs; nothing here says which.

---

## REG-172 — the sets half: one piece, two sets of odds (v1741)

Konyo named both tabs — *"f-uniques and f-sets are showing diffrent number"* — and v1740 fixed only
the uniques half. The sets row was wrong in a plainer way: it printed the **raw** `src.chance` while
the F·Sets card printed `_adjC(...)`, his MF/players-adjusted figure.

Measured on the rendered surfaces, same piece, same boss:

| surface | Tancred's Hobnails @ Normal TZ Mephisto |
|---|---|
| Sessions ops row | **1:2.1k**, and no time at all |
| F·Sets card | **1:1.9k · ~14h to find** |

Two numbers for one farm, exactly as he described. The row now runs the piece through the same seam
the card does — `_adjC` for the odds, `_ttf` for the time — and both surfaces read
**`1:1.9k ~14h to find`**.

### Three instrument errors, and the last one changed the test

1. `w._adjC` is **not on window** — module/closure-scoped. An early probe called it through `window`
   and reported *"adjResolved: 0 of 22 pieces"*, which read like a data fact and was nothing but an
   undefined function. The real fix was confirmed on rendered output instead.
2. `eval('_adjC')` inside `page.evaluate` also fails — unlike `effChance`/`hoursFor`, which are
   module-level, `_adjC` sits inside a closure and is unreachable from a test at all.
3. So the gate stopped reaching for internals and **compares the two rendered surfaces directly** —
   scrape the ops row, scrape the F·Sets card, assert the odds and the time match. That is the
   comparison he actually made, between two things on screen. **[[feedback-verify-not-proxy]]**

Verified RED against the pre-fix file (*"the sets ops row still has no time-to-find"*) and green
after.

---

## REG-173 — his #1 farming target was published under a name that is not an item (v1743)

The unique roster carried **`bloodcrescent`** — no space, no capitals — where every drop table in the
file says **`Blood Crescent`**. It looked cosmetic and was not:

* `funiScan` folds names with `_regKey` to borrow a ROUTE, so the item found its **65 sources** and
  computed **1.04h — the fastest time on the board**;
* but v1716's rule *"THE NAME HE TICKS MUST NOT CHANGE"* deliberately keeps the ROSTER spelling for
  display and for every ledger read;
* so the grail bridge published his **#1 farming target under a name that is not an item**, and
  F·Uniques — which resolves by the real name — **never showed it at all**.

That is the missing half of REG-171: the Sessions bridge and F·Uniques disagreed about the fastest
grail because one of them was ranking something the other could not see.
**[[label-outlived-referent]]**

Fixed at the source — the two map keys — plus a **one-time ledger migration**, because the same
v1716 comment records the scar for renaming without one: *"3 found uniques flipped to missing the
moment the object came back under the other name."* If he ever ticked it under the old spelling, the
tick moves with the name rather than vanishing.

After: the bridge's top three read **Blood Crescent 1.04h · Umbral Disk 1.2h · Frostburn 1.5h**,
F·Uniques renders Blood Crescent, and the item keeps all 65 sources. Zero page errors.

### The gate is narrow on purpose

The roster has **twelve** names that differ from their registry match, and every one is legitimate —
curly apostrophes (Atma’s, Seraph’s, The Cat’s Eye, Saracen’s), disambiguating qualifiers
(`Harlequin Crest (Shako)`, `Gull (dagger)`, `Crescent Moon (amulet)`, `Athena's Wrath (set piece)`)
and a leading article (The Cranium Basher, The Iron Jang Bong, The Mahim-Oak Curio). `_regKey` was
written for exactly those and they must not be flagged.

`bloodcrescent` was different in kind: not a rendering of the name, but a name that had lost its
capitals and its spaces. **A name that reaches a screen starts with a capital** — that line separates
the one defect from the twelve non-defects cleanly, and the twelve are pinned so a thirteenth is
noticed.

⚠ Flagged next door, then CHECKED AND CLEARED: `"Djinn Slayer": "art/bloodcrescent_graphic.png"`
looked like the v1629 wrong-picture-under-a-right-name shape. It is not. `D2IO_ART` names its files
after whichever unique first needed a given BASE sprite and shares them across that family — its
neighbours say so plainly (`"Demonhorn's Edge": "art/hornedhelm_graphic.png"`, the base's own
graphic). Blood Crescent is a Scimitar and Djinn Slayer is an Ataghan, the ELITE Scimitar, so they
share a sprite by design — and `artUrl('Djinn Slayer')` independently resolves to `hd_scimitar.png`,
the same family. **Both images were opened**, because that is the only check v1629 accepts: each is a
curved crescent-bladed sword, correct for either item. `art/mr_djinnslayer.png` exists but is the
small `mr_` sprite for a different map; substituting it would trade a full graphic for a thumbnail.
**No change made.** Recorded because a flag raised and then silently dropped is indistinguishable
from one nobody looked at.

---

## Two assertions that were judging an empty set (2026-08-17, test-only)

`tests/v562_chronicle_sync_filter_throwout.spec.ts` carried two assertions that could not fail:

```js
expect(r.wantedInTrash).toEqual([]);        // filtering an EMPTY list
expect(r.commonPlainHidden).toBe(true);     // .every() over an EMPTY array is true by definition
```

`_endgameFilterBases()` shrinks to match the Chronicle, and its own comment says so — *"Empty = show
no bases, consistent with the count + the shrinks-to-match-your-Chronicle promise."* A **default
profile has all 99 runewords marked MADE** (`_RWC_SEED`), so nothing needs farming and the function
returns **zero codes**. Correct behaviour, and fatal to a test built on it. Measured on the default
profile: `eb.codes 0`, `plainCodes 0`.

With an empty Chronicle the same numbers read **77 codes / 47 plain**, and the `.every()` judges
**30** real ones — and **both still pass**. That distinction is the point: this found a blind gate,
not a broken filter. **[[gate-blind-to-unexercised-input]]**

### Why it became a second test rather than a fixture change

The obvious fix — seed a fresh Chronicle in the existing test — was tried and **reverted**. Two of
that test's other assertions are written FOR the sealed state and say so: `uitMagicHidden` is
documented *"at the sealed stage (sock universe empty)"*. Emptying the Chronicle flips `gts` and
`uit` to magic-hidden and fails them — the state moving under the assertion, not a defect found.
One fixture cannot serve both states, and forcing it would have traded a vacuous pass for a false
failure. The exercised assertions now live in their own test; the sealed-state ones stay put.

Four non-vacuity guards sit directly above the assertions they protect. Verified by removing the
seeding: the guard fails with *"the wanted-base set is empty, so nothing below judges anything —
Expected: > 10, Received: 0."*

---

## A test that wrote into his live capture directory (2026-08-17, test-only)

`tv.FRAMES` resolves to his **real** capture directory unless `TV_FRAMES_DIR` is set, and `tv.STATE`
to the live `state.json`. Of 42 references in `tv/test_agent.py`, nearly every one already does the
right thing — save the global, point it at a temp dir, restore in `tearDown`. **One did not.**

`test_convert_fail_does_not_swap_in_live_eye` planted a fake `eye.jpg` **among his real frames** and
put it back by hand: read the old bytes first, and afterwards delete its own file *only if it was
still under 400 bytes*. Careful, and the wrong shape twice over — while it ran, a live reader could
have picked up the decoy, and recovery depended on the test's own cleanup being reached.

It now rebinds `tv.FRAMES` to a temp dir like its neighbours, which **deletes the save/restore dance
entirely**: there is nothing of his to preserve if his directory is never touched. Guard the FIXTURE,
not the call site. **[[feedback-fixtures-never-touch-live-data]]**

A non-vacuity guard went in with it — the decoy `eye.jpg` must actually exist before the assertion
runs, or *"did not return eye.jpg"* is true merely because there was no `eye.jpg` to return.

### And the static form of the rule

`TestNoTestWritesIntoHisLiveCaptureDir` scans this file's own test bodies: a body that WRITES to
`tv.FRAMES` / `tv.STATE` / `tv.HIST_DIR` (creating the directory, or opening for write/append) must
REBIND it first. Reading is fine. It carries two non-vacuity checks of its own — the file must split
into test bodies, and at least one body must legitimately rebind, or a regex matching nothing would
pass in silence.

Verified by injecting the exact shape the old test had; the guard names the offender:
*"test_writes_into_live_frames_without_rebinding writes to the live capture path without rebinding
it first."* Full agent suite: **225 passed**.

⚠ **And the repo caught ME making the same class of error.** I appended the new guard class to the
END of the file — below `if __name__ == "__main__": unittest.main()`. `TestNoOrphanSuite` failed the
push and said exactly why: *"these suites define a test class AFTER unittest.main(), which exits the
interpreter — every class below it is NEVER DEFINED and the suite still reports OK."* A gate written
to prevent a silently-absent gate, catching a silently-absent gate, in the same commit that adds one.
Moved above the guard; both suites green.

---

## REG-174 — a shortlist of ONE reads as a rule, and MINI was too short for a Chronicle (v1744)

### Crescent Moon offered one base out of seventy-five

Konyo: *"crescent moon shows a 1 item picture runeword, it only shows mythical sword as a base item
for creating a runeword.. but there are other base items."*

He is right and the gap is not small. Crescent Moon is **`3 socket Polearms Axes Swords`** and
**75 bases can host it**; the card showed **one**. The cause is a name that outlived its meaning:
`_rwLegalBases` returns `_forgeMetaBase(rw).names` — the CURATED pick list — despite being called
*legal bases*, and Crescent Moon's curated list has a single entry.
**[[label-outlived-referent]]**

A curated shortlist is the right default — listing 195 bases for `Strength` would be noise, and the
median word shows 3. **A shortlist of ONE is different in kind**: it stops reading as a
recommendation and starts reading as a rule. Measured across all 99 words, four show ≤1 while more
than three bases fit.

`_rwLegalBases` now tops up from the remaining bases that pass its OWN `isLegal` test — class via
`_baseRunewords`, socket ceiling via `_socketMaxFor`, and his disproved pairings from v1737 — **elite
tier first**, and only when owned+curated falls short of the caller's limit. Owned bases still lead,
the curated picks keep their position, nothing is demoted. Crescent Moon's card now renders **4
tiles with 4 HD sprites loaded**, up from one.

**The v1712 guard was restated, not relaxed.** It asserted the tiles EQUAL the meta list ("not a
second list of my own"). That equality is the wrong shape now, so it asserts the stronger thing:
every tile must be a base the ENGINE sanctions (never an invented name), the curated picks must
still LEAD in order, and a word must render at least one tile. That forbids exactly what the
original title forbids.

### MINI could not last long enough to read a Chronicle

Konyo: *"a click option under MINI that knows maybe to read chronicles... and maybe longer then 25
seconds for it."*

The **buttons already existed** — `MINI_FOCUSES` has carried `chronicle-uniques` and
`chronicle-sets` since v1603, with their own board-medallion art. What did not exist was enough
TIME: one bound, `[10, 40]`, default 25, for every focus.

A stash tab is ONE screen — 25s photographs it several times. **A Chronicle is a list he scrolls**,
and the vision lane samples it sparsely on top of that (the v1689 guard measured his chronicle reads
**4.6–9.7s apart**). Measured on session `s_1786922954749_12579`: one pass over his uniques
Chronicle produced five reads and got from "Amulet" to "Jewel" — **A→J of ~400 names**. The cap was
the binding constraint, not his scrolling.

The bound is now per-focus via `_mini_bounds()`: stash/runes/gems/materials unchanged at
**25s default / 40s max**; the two chronicle focuses get **75s / 120s**. The console's sub-line reads
the same table, so a button can never advertise a duration it will not get.

---

## REG-175 — no watchdog read the Chronicle, and the button that does was named wrong (v1745)

### "where is the coded AI reader that retro analyzes this... like a watchdog"

There was none, and that was deliberate. `chron_visit_flush`'s own docstring sets the doctrine:
*"recording is FREE, reading is OFFERED. This journals the visit and says so; it never calls
`claude_chronicle_read` / `g5_chronicle_read` and never spends a classify."* And
`chronicle_sweep_start` was reachable **only** from the HTTP endpoint — nothing called it when a
session ended. So a session could close with a perfectly good Chronicle recording on disk and
nothing would ever look at it.

Measured on session `s_1786922954749_12579`: the visit was journalled with **`ledger:'uniques'`, 4
frames**, its five deep reads named **13 discovered uniques**, and his count sat at **249/403** with
the evidence sitting right there.

**The hole in that reasoning.** "Offered, not automatic" is a COST argument, and it stops applying
when the read is free — which v1528 names exactly: a visit whose LEDGER is already known is *"the
cheapest read in the system: he already told us these frames are the Chronicle and which ledger was
open, so there is no classify stage to pay for."*

So `chronicle_autoread_tick()` fires **only** on visits that carry a ledger. A visit without one is
refused with a NAMED reason and left offered — sweeping it would have to GUESS which ledger, and a
wrong guess writes set pieces into his grail. It also refuses while a session is live (a visit is
only final once the reel stops growing) or while a sweep is running. **It never applies**: the sweep
produces a proposal and the review gate stays where v947 put it. Automatic reading, human-gated
writing.

⚠ **A mistake worth recording.** The first live test ran `chronicle_autoread_tick()` from a throwaway
python process. It really did start a sweep on his visit — then the process exited, the sweep died
with it, and because the code marked the visit read BEFORE checking the sweep took the job, the
visit was left flagged as read with nothing to show for it. The stale marker was deleted, the order
was fixed (mark only on a successful start), a test now pins it, and every later test used
`TV_CHRON_AUTOREAD` to point the state file at a temp dir. **Fixtures never touch live data** — I
broke that rule and then applied it. **[[feedback-fixtures-never-touch-live-data]]**

### The chronicle MINI buttons existed; their labels did not say so

Konyo, looking straight at the row: *"where is the button for it? there are other buttons there
representing other focused hunts for stash/gems/runes.. so for chronicle should also be a focused
run for it."*

Both were there — `MINI_FOCUSES` has carried `chronicle-uniques` / `chronicle-sets` since v1603 —
labelled **"uniques"** and **"sets"**. In a row beside stash / runes / gems / materials, those read
as ITEM CATEGORIES, not as read-my-Chronicle modes, and their art is the board's own uniques/sets
medallion, which says the same wrong thing a second time. The button existed; its name did not say
what it does. Now **"📜 chronicle · uniques"** / **"📜 chronicle · sets"**, each with a title that
says to scroll the Chronicle while it runs. **[[label-outlived-referent]]**

---

## v1746 — the watchdog could retry a refused visit forever

Konyo, on the 20-second tick: *"i dont want it looping though the same video over and over.. needs
logic coding and like a stamped verification after its first and second swap or more.. it might loop
and waste?"*

He was right, and about the one path that was open. A **successful** read was already read-once —
the visit timestamp is persisted and never revisited, so the tick only ever notices a NEW sealed
visit. But a **refused** sweep marked nothing, so that same visit would be re-attempted every 20
seconds for as long as the console ran.

Two tries, then the visit is **retired with its reason kept** — a third identical refusal teaches
nothing and costs what the first did. Retired is deliberately distinguishable from never-tried:
`skipped[ts] = "gave up after 2 tries — <why>"`, so a visit that stopped being attempted can never
be mistaken for one nobody looked at.

⚠ The test for it failed first, and for a reason worth keeping: `_CHRON_AUTOREAD["tries"]` is module
state and `setUp` reset `done` and `skipped` but not `tries`, so one test's refusal count carried
into the next and retired it a tick early. Shared mutable state between tests is its own defect
class — the fixture now resets all three.

---

## v1747 — the tally search bar, in both grail forges

Konyo: *"for a tally version SEARCHBAR within each F-Uniques and F-Sets separately their own
individual search bar to tally off... a search bar that i can sometimes casually while i farm one by
one search for it and tally without needing to visually look for it. just a easy type it in style...
with the colors sync and keyword items image floating HD cursor art same as the platform."*

**ONE implementation, two callers** — `window._tallySearch('uni'|'sets')`, rendered at the same seam
in both tabs (directly under the four filter tiles, above the wall it tallies into). A second copy is
exactly how two lists start disagreeing about one collection, which is the defect this pair of tabs
has been fixing all week. **[[copy-drift]]**

**It writes through the same functions his manual ✓ uses** — `grailFoundUni` for uniques,
`grailTogglePiece` for pieces — so there is no second write path to drift, and an un-tick behaves
like a tick. Measured end to end: **found 246 → 247**, `_gFound('Harlequin Crest')` false → true, and
the typed query survives the re-render so he can tick three things in a row without retyping.

**The name is the hover anchor, never the row.** v654 refuses any arttip anchor wider than 430px —
he asked for that rule in those words — and a result row is far wider. Measured: the name anchor is
**63×16**, and the floating card opens on it with the item's own HD art (Ravenlore →
`hd_falcon_mask.png`, "Elite Unique · Sky Spirit"). Same rule that shaped the shopping list in v1739.

**Colours are the platform's own tokens**, verified by computed style rather than by eye:
F·Uniques renders `rgb(199,179,119)` = `--q-unique`, F·Sets `rgb(0,252,0)` = `--q-set`. Ordering is
starts-with before contains, so "vex" lands on Vex before Vexed Ring. An unknown name says so in
words rather than leaving an empty bordered box.

⚠ The second eye read the uniques name as GREEN and called the rarity cue deliberate. Half right:
the cue is deliberate, the hue was not green — the computed value is the unique tan-gold. Recorded
because a vision verdict that is right about the intent and wrong about the fact is the kind that
gets quoted later as if it were a measurement.

---

## v1748 — the build stamp said the version twice

Found by the second eye, on the pixels: it reported the stamp rendering as
`v1747 · 2026-08-17 · v174…` and flagged the ellipsis.

The truncation is **v1691.1's deliberate design** — the badge is capped at 180px so that "is this
tab stale?" (id + date) always survives and the ship NAME is the decoration that clips. That part was
working exactly as written.

The waste was underneath it. `D2R_BUILD.name` already **begins** with the id
(`"v1747 - the tally search bar"`), and the badge composed `id · date · name` — so it printed the
version twice: **319px of content in a 180px box**, where every character surviving the ellipsis
after the date was an echo of the id. The tab title did the same
(`Konyo's D2R Farming Bible v1747 · v1747 - the tally search bar`).

Now **269px**, and the visible remainder carries the ship name instead of a repeat.

Stripped at **display time only**, in both places. `D2R_BUILD.name` is left exactly as it is because
other readers key on it — the meta tags, the console footer stamp, the version gates. Fixing the
field would have been a far wider blast radius for the same pixels.

The gate carries a non-vacuity check that is worth naming: it asserts `D2R_BUILD.name` **still**
starts with a version, because if the underlying field is ever cleaned up, this gate would start
passing for the wrong reason — testing against a problem that no longer exists.

---

## CLOSED (not a defect) — the 713 qlvl-over-mlvl rows (2026-08-17)

Carried since v1722 as an open worry: **713 rows across 51 of 66 boss cells** drop an item whose
`qlvl` exceeds that cell's declared `mlvl` — e.g. `countess/NORM TZ: Stormchaser qlvl 53 > mlvl 45`.

**Measured, and it is not a defect.** Those rows carry real odds from the silospen pulls, so the
drops are real. In D2 the treasure class is picked by monster level but a TC spans a range, so an
item qlvl above the monster's mlvl is legal — **`mlvl` is a game fact, not a drop ceiling**, which is
exactly what v1722 concluded when it declined to derive it.

The part that WAS a defect — a cell claiming `qlvl N > mlvl M` as the *reason* an item cannot drop,
in a cell whose own data disproves it — was fixed in v1722 and is still gated: *"no blocked reason
cites a rule its own cell disproves"* passes.

**And the sibling check that caught Catacombs finds nothing here.** TZ_ZONES were all supposed to
share one saturation value (96), so a single 75 stood out. Boss cells are the opposite: Andariel is
75 in Hell, Baal 99, Diablo 94, and Hell-TZ values legitimately spread 86–99 because terror lifts
each area from its own base. Every "loner" value belongs to exactly one boss **by design**, so the
outlier test that worked on zones has no purchase on bosses — worth writing down, because running it
and reading the spread as 11 anomalies would have been an easy wrong turn.

Remaining open on this board: **REG-162** (with a first suspect — concurrent gate runs), and the two
gold-on-green `--best` fallbacks (`.aura-tag-target`, `.forge-donow-h`) that need Konyo's call on
whether the variable or the fallback is the mistake.

---

## Another gate comparing two zeros (2026-08-17, test-only)

A sweep for the class found **79 specs** that assert emptiness with no numeric guard — too many to be
all defects, and most are fine. Narrowing to the collections that are **empty on a default profile**
(anything gated by the Chronicle, which ships with all 99 runewords MADE) left **six**, and reading
them settled it:

* `v559_grail_forges` asserts `Array.isArray(s[k])` — a SHAPE check, true on empty **legitimately**.
  Not a defect, and worth saying so: the heuristic flagged it and the code was right.
* `v617_smart_insights_flagship` was the real one. It asserts `_smartProgress()` agrees with
  `forgeScan()` — a genuine invariant it **never exercised**. Measured on a default profile:
  `makeNow 0 / scNow 0`, `deferred 0 / scDef 0`. `0 === 0` passes however wrong both derivations are,
  and keeps passing if they drift **together**.

**An empty Chronicle alone was not enough** — measured, still all zeros, because the Forge also needs
something to plan ON. With a fresh chronicle, a stocked rune stash AND owned socketed bases the same
assertions read **`makeNow 28 === scNow 28`** and **`deferred 29 === scDef 29`**, and they hold. The
invariant was right; the gate was blind. **[[gate-blind-to-unexercised-input]]**

Verified by removing the fixture again: *"the Forge planned nothing, so 'counts agree' compares two
zeros."*

~~⚠ **One half of it is still unexercised and is left honest rather than dressed up:** `farmMatches`
compares `p.farm` against `sc.farm.length`, and both are **0 even with the full fixture**. I did not
find an input that populates `farm`, so that sub-assertion remains `0 === 0`. It is named here rather
than guarded, because a guard I cannot satisfy would just turn a blind assertion into a red build.~~

✅ **CLOSED (v1751).** The input existed; the fixture was hiding it. Handing every rune out at 20
means the board can make everything, so nothing is ever left to farm — the fixture that made the
other two thirds honest is precisely what kept this one blind. Withholding the top six runes
(**Zod, Cham, Jah, Ber, Sur, Lo**) pushes the high runewords into the farm bucket: measured
`farm 0 -> 10` on **both** sides, with makeNow and deferred still clearing their own guards. The
non-vacuity guard its two siblings already had is now in place, and it has been seen red for its own
reason — restore the six runes and it fails on *"nothing needs farming, so farm agrees compares two
empty lists."*

The lesson generalises past this line: **"I could not find an input that exercises it" was a
statement about the fixture, not about the feature.** A fixture rich enough to make every other
assertion non-vacuous can be exactly the thing that starves one of them, and it will never announce
that — it just keeps passing. When one branch of a gate refuses to light up under a generous
fixture, suspect the generosity. [[gate-blind-to-unexercised-input]]



---

## REG-180 — a throttled reader answered EMPTY and every layer believed it (v1774)

Konyo, after re-sweeping and seeing 249/403 unchanged: *"something isnt calculated correctly.. either
the perecentages caliiberation on your end.. or the items arent being read."* The second one, and not
for the reason either of us was chasing.

**The flag nobody downstream read.** `_note_slot_death()` (v891) flips a throttle when 2+ readers die
inside 60s, and its docstring promises to *"SAY SO instead of silent empties"*. `_is_throttled()` had
exactly two consumers: the live heartbeat cap and a status chip. The retro sweep had none.

**Measured, by calling the reader directly on his 08-17 frames:**

| frame | first read | minutes later, throttled |
|---|---|---|
| clean list page | `chronicle` / `uniques` / 6 names / conf 0.9 | `gameplay` / 0 names / conf `None` |
| page with his item tooltip open | `transition` / 0 names / conf 0.85 | `gameplay` / 0 names / conf `None` |

Three sweeps in a row returned **39, then 22, then 0** names as it deepened. I spent that stretch
blaming my own threshold work and **reverted v1771 on evidence that was this**.

**Why it cost footage rather than just time.** The seal rule reasons that *"classified > 0 with pages
== 0 IS a legitimate seal: the cheap classifier looked at every frame and correctly found no
Chronicle page"*. A throttle counterfeits that shape exactly — the classifier was never asked. So a
throttled sweep finishes clean, finds nothing, and seals the reels; since v1766 a sealed reel is never
read again. The v1773 run is the specimen: **105 classifies, 4 pages, 0 names**, and it would have
burned his 08-17 reel. His recordings cannot be re-made.

**Two guards, because either alone leaves the hole open.** The retro readers refuse out loud while
throttled — `claude_chronicle_read` returns a `note` (which `chronicle_retro` already counts as NOT
read, not as an empty page) and `claude_read` returns `None` ("no answer", not the verdict "not a
Chronicle page"). And a run that touched the throttle **seals nothing**, saying how many reads were
refused rather than skipping quietly.

**Related, same session:** the reader called a tooltip-covered Chronicle a `transition` at conf 0.85,
while the tell it already documents for `transition` (no bottom HUD) was plainly present. Prompt fixed
(v1774) and the run-level workaround kept (v1773), because classify runs once per run and one bad
probe discarded up to 44 pages behind it.

**A false red of my own:** the REG-179 live-state guard cannot tell a TEST writing his console state
from the CONSOLE writing it. It now skips while `:17772` is listening, and says so. [[feedback_silence_is_not_evidence]]

## REG-198 — v1798's own fix made the evidence ledger un-writable, and CI was 7/7 GREEN on it (v1799)

**The worst defect of the arc, shipped live, found by the review hook one hour after it was built.**

v1798 taught `merge_proposals` to accumulate `setGroups`/`completeSets`/`notFound` — the right fix, and
it used Python `set`s to do it. Sets are the correct type to fold WITH and the wrong type to hand back:
the merged dict is `json.dump`-ed straight to `chron_evidence.json`, and **`json.dumps` refuses a set.**
It failed on an EMPTY merge.

Proven end to end before anything was changed:

    merge_proposals({}, {})      -> TypeError: Object of type set is not JSON serializable
    _chron_evidence_save(merged) -> False
    file written                 -> NO

`_chron_evidence_save` wraps its dump in a bare `except Exception: return False`, and **no caller reads
that return.** So every sweep would have reported success, the console would have shown its findings,
and the accumulated ledger would have silently frozen at its last pre-v1798 content — losing every
sighting from then on. That is precisely the *"the progress is going up and then reversing"* defect
v1776 was written to kill, reintroduced **globally** by the fix for it, and silent this time.

**CI WAS 7/7 GREEN ON THIS.** So were 32 local gates and 425 tests. Nothing in the suite JSON-round-trips
a proposal, and `TestV1798TheSetsLaneHasATapEndToEnd` — written an hour earlier, citing the blind-fixture
rule in its own docstring — asserted only on the in-memory dict with `sorted()` and `in`, both of which
behave identically on a set. **A ledger is what reaches DISK; asserting its shape in memory tests the
wrong noun.**

**Fixed three ways:** the merge now ends in the producer's shape (`proposal_from_pages` already sorts to
lists — the two halves of one contract must agree); `_chron_evidence_save` now PRINTS when it fails,
because a write whose return value is dropped must be audible; and two tests pin it — the one-line
`json.dumps` that would have caught it, and one that verifies the artifact on disk. Proven red without
the fix.

**The process finding matters as much as the defect.** `/code-review` had been run exactly once across
nine shipped versions, on a whim. It found this on the first ship after it was made mandatory. The
`review_after_ship.py` hook exists so that is never a whim again.

---

## REG-200 — prep_tab_chrome returned None on EVERY call for 310 versions (v1849)

**Symptom.** The vault kept items he does not have. He said so plainly: "im pretty sure some items
here were incorrectly VAULTED and MULED some are okay and i have them for real in my stash but some
i do not."

**Found by** building the structural stash gate he asked for on 2026-08-20 — it could not pass a
single genuine stash frame, including frames his own journal marks `scene=stash`.

**Measured.** Four lines in `prep_tab_chrome` were pasted from `prep_stash_grid` and reference
`derived`, `aspect` and `layout` — all local to THAT function, none defined in this one:

```
if not derived and aspect >= 1.3:
    _LAST_CROP.update({... "layout": layout ...})
```

Running the body without the swallow raises `NameError: name 'derived' is not defined`, while the
crop before it succeeds at 820x142. The function's own `except Exception: return None` turned that
into a plausible answer. Introduced v1538 (cc9c6f71), found at v1848 — **310 versions**.

**Why it mattered.** The stash TAB CHROME is the one NON-MODEL signal for which tab is open, and
stash_eye's own note says the chrome "only becomes readable via a deliberate crop + 3x upscale" —
which is exactly what this function does. With it dead there was no readable chrome, nothing could
confirm a stash panel structurally, and every ownership frame fell back to a model's guess.
vault_retro states the consequence itself: "a rune tab misread as 'inventory' files his runes in the
wrong lane, which merge-max then makes permanent."

**Fixed** in v1849; the telemetry those lines meant to write is kept, corrected to describe what this
function actually does. Verified on his own footage, green and red each for its own reason:
`5_1784984201581.jpg` (journal: scene=stash) -> tab `gems`; `6_1786554035205.jpg` (gameplay) ->
refused.

**Prevention — the transferable law: A BARE `except` THAT RETURNS A PLAUSIBLE VALUE IS HOW A
FUNCTION DIES SILENTLY AND STAYS DEAD.** Guard: `tv/test_control.py
TestPrepTabChromeIsNotDead` — and it asks the COMPILER (`co_names`) rather than grepping the source,
because the first cut tripped on the dict KEY `"layout"`, a string that was never the bug.

⚠ The same shape was then found in `stash_screen_open`, written the next day, and fixed in v1854: a
gate that cannot RUN must not answer "no". It still refuses (the safe direction) but is no longer
silent, and `gate_failures()` counts it.

## REG-201 — ten versions reached origin/main and NONE of them deployed (2026-08-20)

**Symptom.** v1829..v1838 were each reported as shipped. The site stayed on v1828.

**Cause.** `bump_version.py` writes four version stamps; they were staged by hand and
`tv/tv_diablo.py` stopped being included from v1832. The committed tree read:

```
bible.html v1838 · control_app v1837 · tv_diablo v1831 · WINDOWS_SHIP v1838
```

and the Publish job's own guard, `test_all_four_stamps_are_the_same_version`, refused it exactly as
designed — ten times.

**Why nothing local saw it.** That guard reads the four files FROM THE WORKING TREE, where every
stamp was correct the whole time, and `hooks/pre-push` runs the same suite against the same working
tree. CI reads the COMMITTED tree. A gate blind to the only state that matters: the bytes that were
actually pushed.

**Fixed** by committing the missing stamps, and by a guard that reads `git show HEAD:` for all four —
so a half-bumped commit fails LOCALLY, before the push. A second cause surfaced behind the first:
`publish.yml` had never installed Pillow, while `tv-tests.yml` has since it was written, so the
workflow that BLOCKS THE DEPLOY ran the same suite with fewer capabilities than the one that only
reports.

**Prevention — the transferable law: A PUSH THAT LANDS IS NOT A SHIP.** `origin/main` moving proves
the push; only the deploy proves the ship. Read CI, and read the SITE.

⚠ Two more gates were red and unheard on the same day: `test_chronicle_seal` for nine versions
(run_gates runs it, the pre-push hook did not — now it does), and `v1733_css_tokens_resolve` for ten
(Routine I was never read). Both were caught by their own guards instantly and by nobody else.

## REG-199 — the height caps ignored the dock, and the earlier "zero collisions" only held for short queues (v1799)

Two findings from the same review, both real, both mine.

`.inbox-sticky.has{max-height:calc(100vh - 24px)}` with `top:8px` put the panel's bottom edge at
`100vh - 16px` — **underneath the fixed dock**. `--dock-h` is 84px at `:root` and 118px at ≤700px, but
renders at **132px (1440), 178px (640), 219px (375x700)**. On a queue long enough to hit the cap the last
rows and their buttons sat under the dock, and scrolling the panel could not help because the occlusion
is at the panel's own bottom edge. The correct precedent was two rules away:
`.nav-widget.open .nav-panel` already uses `calc(100vh - var(--dock-h,84px) - 130px)`.

`.inbox-pop` was rebased 66px higher onto the tray anchor and kept `max-height:70vh` with no `top`, so it
grows UPWARD and overflows the top edge whenever `bottom + 0.7h > h` — below about 1006px at the measured
dock height. At 1440x900 its header sat ~32px ABOVE the viewport, unreachable, because `overflow:auto`
scrolls content inside a box whose top is already off screen. **Raising an anchor without re-budgeting
the height moves the clipping rather than removing it.**

**Why the earlier measurement missed both:** "zero collisions at 375/640/901/1440" was taken with a SHORT
queue that never reached the cap — the condition the cap exists for. Re-measured with a 20-name queue:
all 17 buttons reachable at some scroll position, at every size, and the panel clears the dock.

**Seven instrument corrections were needed to get that measurement right**, and every wrong reading
looked like a product defect: measuring an unpinned panel, scrolling the wrong element, scrolling and
measuring inside one expression before layout settled, counting in-panel scrolled-out buttons as
unreachable, and a fixed-overlay scan whose `width<120px` filter excluded the very compass causing the
collision. Suspect the instrument first — it was the instrument six of seven times.

---

## REG-195 — a complete-set claim could never earn cross-reel, because merge_proposals REPLACED its evidence (v1798)

**The most valuable finding of the arc, and it came from `/code-review`, not from me.** Reproduced
before it was believed and before it was fixed.

v1776 made the chronicle evidence ACCUMULATE — the fix that let a name seen in reel A on Monday
corroborate one seen in reel B on Tuesday. It de-dupes sightings by `(reel, frame, lane)` and appends.
Two keys were left on `dict.update`:

```python
for k in ("setGroups", "completeSets"):
    out[k].update(src.get(k) or {})      # REPLACES the value
```

Measured on exactly the scenario the accumulator exists for — the same set read in two reels:

| key | before the fix |
|---|---|
| `uniques` | 2 sightings → `witnesses ['cross-reel']` ✓ |
| `completeSets` | reel A's sighting **gone**, `witnesses []` |
| `setGroups` | `Adjudication` **lost**, only `Guardianship` survives |
| `notFound` | key **dropped entirely** |

`apply_proposal` gates a complete-set claim by the same `MIN_WITNESSES = 2` rule, and `witnesses()`
returned `[]` — so **a set worth five pieces could never ground on cross-reel evidence, forever**. The
uniques lane was fixed and its set-shaped twin was left running with the identical defect.

Fixed by giving both keys the rule the loop above already had: `completeSets` de-dupes sightings by
`(reel, frame, lane)` and appends; `setGroups` UNIONS its piece names, because a half-scrolled page
showing three of five pieces must never delete the other two; and `notFound` is carried, because "the
game says he has NOT found this" surviving one sweep and then vanishing is an absence nobody can act
on. Verified after: 2 sightings, `['cross-reel']`, both pieces present — **and the same page twice is
still ONE sighting**, so the de-dupe that stops a photograph corroborating itself survived the change.

**And the test I had just written did not catch it.** `TestV1798TheSetsLaneHasATapEndToEnd` cited
REG-181 in its own docstring while stopping at `proposal_from_pages` — `merge_proposals` sits between
that and the fold on every production path, and it was the one step where the lane actually broke. A
fixture built on the near side of the joint it claims to test is the blind-fixture shape. The class now
runs the full chain and pins the joint directly. Its fixture also named "Tal Rasha's Howling Wind",
which is not a D2R item; it passed only because `notFound` was never folded.

---

## REG-196 — the FAB joined the system tray and left its own popover behind (v1798)

`.inbox-fab` was rebased onto the dock-relative tray at `calc(var(--dock-h,84px) + 170px)`.
`.inbox-pop` kept `bottom:236px` — a static number tuned to the FAB's OLD position. The two lines
directly above the new rule rebase `.forge-legend-pop` and `.tools-legend-pop` for exactly this reason;
the inbox was left out.

Not theoretical: `--dock-h` is measured live by a ResizeObserver, and it renders at **132px at 1440 and
178px at 640**, not the 84px default. So the orb sat at 302px while its panel sat at 236px — **66px
adrift at the widest viewport and worse at the narrow one**. A control and its panel that do not share
an anchor drift apart on exactly the screens nobody tests on.

**Also retired here:** the v1793 base `.inbox-fab` rule is now entirely dead — every declaration is
overridden with `!important` 32k lines later — and its comment still described the old stack
("help 146-190 / legend 250-294 / inbox 312-364") as live geometry. Someone tuning `bottom:312px` would
have watched nothing move. Marked SUPERSEDED with a pointer rather than left to mislead.

---

## REG-197 — the review's better fix was necessary and not sufficient, and the measurement said so (v1798)

Worth keeping because taking a good review finding wholesale would have swapped one visible defect for
another.

The 72px reserve I had added was, correctly, called out as treating a symptom: a `position:sticky` box
TALLER than its scrollport stops pinning altogether, so over-tallness caused both the occlusion and a
header that scrolls away, and `max-height` fixes both without spending row width where width is
scarcest. `.inbox-pop` has carried `max-height:70vh;overflow:auto` since it was written; the sticky twin
never got it.

So the cap went in and the reserve came out — and the measurement refused it: with the reserve removed,
`help-btn` still covered "put back" at 640 (20x19) and "ignore" at 1440 (25x22), because the panel runs
to the right edge whatever its height. **Both are needed.** The reserve is now 64px rather than 72,
which is what the orbs actually occupy (44px wide at `right:12px` → 12..56px from the edge). Final
state, measured at 375 / 640 / 901 / 1440: pinned at every width, zero collisions.

---

## REG-194 — the FALLBACK lane calls a Chronicle page a "transition", and the primary lane never does (v1797)

**A correction to my own earlier finding, which is why it is written down.** I reported that "the
classifier misreads a textbook example" of a Chronicle panel. Re-measured, that is wrong in an
important way: it is the FALLBACK lane that misreads it, and the primary lane is right every time.

The frame — `cache1280/f_1786922977454.jpg`, the CHRONICLE panel with its title bar, the
Unique/Sets/Runewords tabs, the 64% meter and the life and mana orbs plainly on screen:

| when | lane | answer |
|---|---|---|
| Grok 402-exhausted | `model: sonnet` (Claude fallback) | `scene: transition`, `chronicleTab: ""` |
| Grok restored, 3 consecutive reads | `model: grok-subscription-cli` | `scene: chronicle`, `chronicleTab: "uniques"`, conf 0.95 / 0.95 / 0.96 |

The read prompt already states the rule the fallback broke, in its own words: *"It is NEVER a
transition: a transition has no bottom HUD, and this panel is drawn over a live game with the life and
mana orbs still on screen."* Both orbs are visible in the frame.

**Why this is worse than a wrong label.** `classify()` runs ONCE PER RUN, and a run classified
`transition` discards every Chronicle page behind it — the file already carries a note that one such
answer "discarded up to 44 Chronicle pages". So the cost of the fallback being wrong here is not one
bad row, it is a whole session silently dropped. And it happens precisely when the primary eye is
DOWN, which is the moment nobody is watching.

**No test added, deliberately.** A regression test for this needs a real vision call, and v1796 has
just removed one such test for costing 100.8s and real subscription budget on every suite run
(REG-192). Adding one back to catch this would trade a known cost for an occasional catch. The
mitigation that already exists is v1773's second-opinion probe on a refused run; what is recorded here
is the evidence, the frame path, and the fact that the two lanes disagree on it — so the next person to
touch classify() knows which lane to trust on this frame class and has a fixture with a known-correct
answer to hand.

---

## REG-192 — a cap test passed only while Grok was DOWN, and cost 100s of real vision on every run (v1796)

`test_a_capped_classify_says_NOTHING_not_gameplay` caps the CLAUDE subscription budget and asserts
`claude_read` returns None. It went red the hour his Grok balance came back, returning a real chronicle
read stamped `model='grok-subscription-cli'`, `mode='g5-primary'`, `conf 0.91`, with real item names.

**The product code is right, and deliberately so.** v1778 moved the Claude cap BELOW the G5 block on
purpose: *"a per-lane circuit breaker that takes down the other lane is worse than no breaker: it
removes the independent witness precisely when the main lane is struggling."* So with G5 primary, the
read comes from GROK on GROK's quota, and the Claude budget has nothing to say about it.

**The test was asserting something it never tested.** Its own fixture guard checked the CLAUDE circuit
while the answer arrived from another lane, so it only ever passed when Grok happened to be
unreachable — which, that afternoon, it was: the peer session had just recorded `HTTP 402 usage balance
exhausted` from the Grok CLI. The suite was green for the same reason the second eye was empty.

That is blind-fixture, and it is the class the test's OWN docstring was written about — it already
carried a note about a gitignored budget file making the cap vacuous on CI. The same defect had simply
moved lanes.

**Two costs, and the second was invisible.** Beyond asserting nothing, the fall-through made a REAL
vision call on every suite run: `test_control` took **141s**, of which this one test was **100.8s**,
spending real subscription budget to fail an assertion about not spending it. With the Grok lane stood
down in the fixture the same test runs in **0.022s** and the suite in **24.9s**.

**Fixed in the fixture, never the product:** `_open_the_circuit` now also patches
`g5_grok_eyes.is_primary` to False (with cleanup, and tolerating the module's absence), so the test
isolates the lane it claims to be testing.

---

## REG-193 — sets had no fold, so a misread piece stayed one witness forever (v1796)

Uniques got the roster fold in v1789; sets got nothing. A misread piece — the set-ledger twin of
"Battlecage" — stayed its own name with one witness and could never corroborate the real one.

`chronicle_resolve.load_set_roster()` reads a GENERATED `set_roster.json` (34 sets, 135 pieces, from
bible.html's own `__allSets()`, sharing the unique roster's sourceHash), and `fold_proposal` now takes
a `set_roster` so **each ledger is asked of its own catalogue**. Pieces are stored SUFFIXED
("Tal Rasha's Adjudication (amulet)") because that is the `d2r_setPieces` form, while the Chronicle row
prints the BARE name; `_norm` strips the parenthetical so both collapse to one key and the canonical
stays suffixed.

    "Tal Rasha's Adjudication"      -> "Tal Rasha's Adjudication (amulet)"    bare row -> ledger form
    "Tal Rashas Adjudicaton"        -> "Tal Rasha's Adjudication (amulet)"    misread repaired
    "Windforce"                     -> None                                   a unique, refused

**Measured before relying on any of it:** 135 pieces produce 135 DISTINCT keys, and ZERO of them also
match a unique roster name — so a name cannot be both, and the two ledgers fold independently without
leaking. Both facts are pinned, because either becoming false would let a set piece land in his grail
tally.

**The wrong-catalogue case is a test, not a comment:** hand the sets ledger the UNIQUE roster and every
piece resolves to nothing and is retired as debris — the whole ledger silently emptied, with a tidy
receipt saying so.

**Still unexercised on real data.** His sets ledger is empty and no reel is `chronicle-sets`, so this is
proven on fixtures only (REG-185's shape). One ~4-minute sets scroll makes it real.

---

## REG-189 — a pixel gate calls his CHRONICLE page a stash panel, and agrees it is open (v1795)

**Found by opening a frame the detector had classified, rather than trusting the label.**

Sampling every reel through `stash_eye.classify_stash_grid` returned 87 recognised panels. Two were
opened and looked at:

| frame | classify | frac_dark | dark cols | `_panel_open_from_features` |
|---|---|---|---|---|
| gameplay, entering Nihlathak's Temple | `stash` | 0.7778 | 53 | False — caught |
| **the in-game CHRONICLE panel** | `stash` | 0.5364 | 11 | **True — accepted** |

The Chronicle page sits inside every stash threshold: dark cells in range, a visible column lattice,
not-a-photograph. It is a grid of dark rows behind item icons, which is exactly what the fingerprint
was built to recognise. **A cheap pixel gate cannot tell these apart, and nothing about the numbers
hints that it failed** — the reading is confident and wrong.

**Not exploitable today, and that is luck rather than design.** The live vault sweep classifies with
`tv_diablo.claude_read`, and asked about those same two frames it answered `scene: transition` and
`scene: gameplay`, both with `stashTab: ""` — so `_surface_of` returns None and neither page is read.
The pixel path is used for cheaper purposes. But two lanes were each guarding themselves with
different instruments and no shared answer, which is how one of them eventually reads a Chronicle row
into the OWNERSHIP ledger.

**Fixed by making it one decision.** `tv/lane_lock.py` is now the only function allowed to answer what
a frame may write to: at most ONE lane is ever unlocked, and a frame that claims both a stash panel and
a chronicle tab unlocks NOTHING. The asymmetry is why locking is right — a Chronicle row filed as
ownership claims he owns an item he merely saw listed; a stash item filed as a chronicle find ticks a
grail row he never earned. Locking costs one unread page.

**Guards:** `TestLaneLock` — stash unlocks the vault and locks the chronicle; the tab he clicked is the
only ledger unlocked; gameplay unlocks nothing; a frame claiming both unlocks nothing; and `may_write`
refuses a SETS write on the uniques tab.

---

## REG-190 — the runewords tab cannot be seen by anything, at any layer (v1795)

Konyo, describing the focus logic: *"so either UNIQUES or SETS or RUNEWORDS ... something should switch
on and off some sort of engine or key like that unlocks or locks."*

Measured across the whole path: the classifier prompt enumerates only `"uniques"` and `"sets"`;
`_norm_chron_tab("runewords")` returns `""`; `chronicle_kind({"chronicleTab": "runewords"})` returns
`None`. **Three layers, none of which can express the third tab**, while the tab is plainly visible in
his own footage next to Unique and Sets.

Deliberately NOT half-wired. Teaching the parser to accept the word without a reader lane, an intake
kind and a fold would produce a tab that unlocks and then reads nothing — a dark lane that looks
supported. `lane_lock` CAN return a runewords ledger the moment something upstream produces one, and a
test pins all three refusals so the gap is a KNOWN dark path rather than a surprise.

---

## REG-191 — the vault lane had never been run, so "what it would do" was theory (v1795)

His question, and it is the right one to ask of a lane nobody has exercised: *"lets say im playing
ingame ... and it reads my inventory and sees the item two or three times lets say.. what exactly does
it do? because based on the item it reads it doesnt necesarily have to discard all... it should tell me
to mule it."*

**Answered by running it, not by reading it.** `tv/vault_simulate.py` drives the REAL sweep over his
REAL reels — real frame names, real timestamps, real still-run grouping — injecting only the reader's
answer, since that is the one thing the archive lacks:

    one look at a Shako            -> UNSURE, never owned
    the Shako in TWO recordings    -> OWN, to the Vault manager for a mule and a cell
    junk flagged, ONE recording    -> HELD, suggests nothing ("needs 3")
    junk flagged, THREE recordings -> DISCARD, suggestion only
    a Shako in THREE recordings    -> OWN, and NOTHING in discard
    a later read of 2 after a 5    -> count stays 5

The fifth line is the rule he was checking for, and it holds because `throwOut` reads the READER's junk
flag (`raw.get("throwOut") is True`) and never the witness count. Repetition decides whether he OWNS a
thing; only the reader's own flag can propose a discard, and then only across three recordings.

**Still open and stated rather than implied:** `vault_retro.py` contains zero occurrences of
mule/destination/route. It says WHAT he owns and never WHERE it goes — the mule and cell are computed
board-side by the Vault manager's packer at render time. The chain looks complete (accept →
`tvVaultRegister` → packer) but cannot be proven end to end until one stash session exists to run it on.

---

## REG-187 — a grey Chronicle row is the game saying NOT FOUND, and it was reaching him as a decision (v1793)

Konyo, looking at Ancient Sword / Basinet / Battle Hammer sitting in his inbox: *"this is not properly
coded.. its looking at the wrong thing.. it needs to tell me the UNIQUE name of the item itself not the
BASE ITEM"*, and then: *"the PUTBACK shouldnt even tell me anything in this case ... its accidentally
tallying or MAYBE tallying and is unsure of if it a chorincle.. but it cant be because it greyed out."*

**Both halves right, and the second one names the defect exactly.**

Half of it is the game, not the reader: an UNFOUND row in the in-game Chronicle prints the BASE name,
grey, with no date and no dropper. Verified on his own frames — "Thunder Maul" appears TWICE in grey
between "The Ward" and "Thundergod's Vigor", and "Troll Belt"/"Troll Nest" sit between "Treads of
Cthon" and "Twitchthroe". The unique's name is not on screen to read, so the reader was not looking in
the wrong place; the information genuinely is not there.

**Why it reached the queue anyway.** The live register hands `kaiChronicleTriage` a bare NAME with no
found-state attached — the one fact that settles the row is discarded before triage ever sees it. So a
grey row fell through to `human-review` and arrived asking him to decide something the game had already
decided. Fixed at the top of the pipe: a name that resolves to a BASE item is dismissed outright,
because it cannot be a find. A certain retire also needs no undo, so those rows lost their "put back"
button — an undo on a decision that does not exist is an invitation to make a mistake.

**And the base is the wrong noun to show him, which is fixable from the other side.** ITEM_CODEX
carries the specific base per unique, so the row resolves BACK: Ancient Sword is **The Atlantean**,
Basinet is **Darksight Helm**, Battle Hammer is **Earthshaker**. The two grey Thunder Maul rows are
**Cranium Basher** AND **Earth Shifter** — which is also why one base can legitimately appear twice and
look like a duplicate until you know what it means. He saw the value immediately: *"the HAVENT FOUND is
actually pretty cool for like a reverse enginnering of WHATS STILL LEFT TO FIND."*

**THE CASE THAT MUST NOT BE SWALLOWED.** If he already owns every unique built on that base, the game
called it unfound and the board says found. Both cannot be true, and dismissing it destroys the only
evidence the disagreement exists — so it HOLDS, with the conflict spelled out. Contradiction is the
finding.

**Also fixed here:** the widget was printing RAW codes on his screen ("human-review") while a
plain-words table sat three thousand lines away doing the job properly. The first attempt to share it
assigned `window._chSayWhy` INSIDE `renderInbox`, which had not run — a shared thing defined inside a
function nobody called is not shared. Now hoisted, one definition, two callers.

**Guards:** `tests/v1789_inbox_resolves_non_decisions.spec.ts` — a base name is dismissed at triage and
NAMES the unique still to hunt (including both uniques when a base has two); a real unique is untouched
by the rule; the game-vs-ledger disagreement HOLDS rather than dismisses; and the humaniser is a real
global rather than one trapped inside a render function.

---

## REG-188 — the inbox FAB and the legend compass overlapped by 38px (v1793)

His screenshot, then measured: the inbox sat at `bottom:236px` (52px tall → 236-288) and the
Forge/Tools legend compass at `bottom:250px` (44px tall → 250-294). `getBoundingClientRect` confirmed
inbox x1353-1405 against compass x1373-1417 — a **32×38px** overlap on both of those tabs. Neither
element was wrong on its own; they were placed by two different versions, neither of which measured the
other.

The stack from the bottom is now help 146-190 / legend 250-294 / inbox 312-364. The inbox also moved to
`right:12px`, **not** the 24 its rule declared: measured, the help button and the compass both COMPUTE
to 12px (their own rules say 24 and something later overrides it), so 24 left the inbox alone in a
column of three, inset 12px from the two beneath it. Matching what they render, not what they say.

**And the sticky created a second collision the moment it existed.** Konyo: *"att hthe inbox to the
sessions tab as asticky too."* The FAB is `position:fixed` and the sticky is in flow, so the badge
landed on top of a row's "ignore" button — two copies of the same control, one covering the other. On
Sessions the sticky IS the inbox, so the FAB now stands down there. Verified per tab: Sessions
FAB-hidden/sticky-shown, Tools and Forge FAB-shown/sticky-hidden, no overlaps anywhere.

Two instrument errors on the way, both worth keeping: `getComputedStyle(e).display` says nothing about
whether an ANCESTOR is hidden, and `offsetParent` is always `null` for `position:fixed` — so the first
two visibility measurements were both wrong in opposite directions. `element.checkVisibility()` is the
one that answers the question actually being asked.

---

## REG-186 — a re-look inside one recording now counts for KEEP, and can never count for THROW (v1792)

Not a defect — his idea, evaluated and built with a boundary.

Konyo: *"maybe though like it can be smarter then this if in the same session but theres a 3-4 min gap
between timestamped reels then it can be considered another witness?"*

**The reasoning holds, and better than it first looks.** Two candidate runs inside one reel are ALREADY
separated by a signature change — `still_runs` only starts a new run when the screen moves past
`STILL_MAX_DIFF` — so a second run is not the same frozen screen, it is the panel left and returned
to. Add a multi-minute gap and it is him walking away and coming back: different scroll, different
overlay, different mouse.

**What it does not buy, which is where the boundary is.** The failure this rule guards against is a
SYSTEMATIC misread — same model, same prompt, same font, same row. Coming back four minutes later and
reading "Ral" as "Ort" a second time is exactly as likely as the first. **Elapsed time buys
independence of STATE, never independence of JUDGEMENT.**

So the keep bar counts LOOKS (separate recordings, or one recording re-opened after `REOPEN_GAP_MS`)
and the throw bar counts RECORDINGS. Measured at maximum confidence with three re-looks in a single
recording:

    KEEP : True  — corroborated across 3 looks (s1#0, s1#1, s1#2) at conf 0.99
    THROW: False — only 1 independent recording (s1) — needs 3

The same evidence grounds what he owns and still refuses to suggest binning anything. Law 3 intact:
there is no un-throw in Diablo.

Buckets compare against the PREVIOUS RUN'S END rather than the reel's start, so three looks spread
across an hour are three witnesses while three quick glances in one minute remain one.

**Still unmeasured, and labelled so.** There is no ownership footage in the archive to calibrate
`REOPEN_GAP_MS` against (REG-185); 3 minutes is his number, taken as given rather than tuned.

**Guards:** `TestV1792ARelookCountsForKeepAndNeverForThrow` — two re-looks ground owned; two glances in
one bucket do not (the rule can say no); a single recording at 0.99 with three re-looks can never
reach the throw bar, and refuses for the RIGHT reason; three real recordings do; the sweep actually
applies the gap and stamps the key; and pre-v1792 evidence with no `witness` field falls back to the
session id rather than un-grounding what he already owns.

---

## REG-184 — the re-gate changed the answer and kept the stamp, so the board would have refused all six (v1791)

**Caught before it reached him, and only because the adoption path was read rather than assumed.**

`_chronAutoAdopt` dedupes on the sweep stamp: it reads `proposal.startedTs`, falls back to the
console's `startedTs`/`restoredFrom`, compares against `d2r_chronAdopted`, and returns
**"this sweep was already adopted"** when they match. `_chron_result_save()` stamps `savedTs` with
the current time on every write, so a sweep that runs normally always presents a new stamp.

**A re-gate done by hand does not go through that function.** After the second lane grounded six held
names, `chron_last_result.json` was rewritten in place — 255 grounded became 261 — and the file kept
its ORIGINAL `savedTs`. Every number in it was correct.

What would have happened: the console reports 261, the board shows 255, and the two disagree forever
with **no error anywhere**. The refusal message even reads like success. Both halves right, the joint
silent — the-unjoined-end in its purest form, and the second time this arc produced one.

**Fixed** by making the re-gate a supported operation instead of hand surgery: `tv/chronicle_regate.py`
re-judges the stored evidence, stamps `savedTs` exactly as the console does, prints what changed, and
**refuses to write at all** if any grounded name is not a roster name — because a grounded name the
board cannot match is a number that can never tick.

**Guards:** `TestV1791ARegateThatKeepsItsStampIsInvisible` — the stamp advances; a second lane grounds
a name one lane could not (one reel, two frames, plus a different model family); reader debris never
reaches the board; and the CLI refuses rather than warns on an off-roster name.

---

## REG-185 — the vault lane has never run on real footage, and says so (v1791, no fix required)

Recorded because "unmeasured" was being carried forward as an inherited claim rather than a measured
one, and because the honest answer here is *don't change the code*.

**Measured, not assumed:** every reel in `frames/hist` was checked against `vault_retro._declared_surface`.
**Zero of 17 are ownership reels.** So the vault thresholds are not merely unmeasured — the whole lane
is unexercised, which is `gate-blind-to-unexercised-input` at the level of an entire subsystem.

**It behaves correctly in that state, which is the part worth keeping.** Run fully wired against his
real history it returns `ok: true`, **0 owned, 0 throwOut, 11 held, 0 reader calls**, and says:
*"11 reel(s) held no screen still long enough to be worth reading — that is footage of moving, not of
looking at a stash."* An empty shelf and a sweep that never looked do not read alike, and it spends
nothing to say so. The two bars already declare themselves REASONED rather than measured.

**What would close it** — and this is the deliverable, since no code change can be:

| requirement | value |
|---|---|
| declared surface | one of `stash` `inventory` `equipment` `runes` `gems` `materials`, chosen deliberately (a default is not a declaration, v1783) |
| panel held still | ≥ 3 frames (`MIN_RUN_FRAMES`) |
| to KEEP an item | conf ≥ 0.55 across **2 different sessions** |
| to THROW OUT an item | conf ≥ 0.85 across **3 different sessions** |

So: two separate recordings per surface to ground anything, three before it will ever suggest
discarding. Until that footage exists the thresholds stay reasoned, and any number derived from them
is `None`, not `0`.

---

## REG-182 — the inbox retired rows instantly and one-way, and he had to ask how long he had (v1790)

Konyo, immediately on being shown the auto-retire: *"how long after it retires when i dont click it?
maybe like it should have a certain timelimit for this."*

**The honest answer was: no time at all.** The resolver runs at page load, so a row was gone before he
had opened the panel, and nothing in the UI could put it back. The dismissal WAS written to the inbox
ledger, so nothing was destroyed — but a record he has to go find is not the same as a control he can
press, and that gap is precisely where a wrong retirement would have lived unnoticed. The receipt said
"3 rows cleared automatically" and gave him no way to disagree with it.

**A timer would have been the wrong shape.** A delay before acting runs out while he sleeps and
changes nothing he can act on. What he needs is not a pause, it is a way back AFTER it acted. So
retirement stays immediate — being asked is the thing he explicitly does not want — and every retired
row is now kept with its reason and a timestamp, listed under the receipt with a "put back" button,
for 7 days. Past the window the row stops being OFFERED; it is never deleted.

**The detail that would have made the button a lie:** a restored row goes onto a keep-list the
resolver never touches again. Without it the very next render retires it a second time, and the
control looks broken while behaving exactly as designed.

**Guards:** `tests/v1789_inbox_resolves_non_decisions.spec.ts` — a retired row records its reason and
timestamp, the put-back is visible with non-zero width, the row comes back, **and it survives two
further renders**; a row retired 9 days ago is no longer offered while remaining in the store.

---

## REG-183 — six real finds sat un-counted because one reel can only ever be one witness (v1790)

Not a bug in the gate — the gate was right — but the arc is worth keeping, because the fix is the
whole argument for the second eye.

After the v1789 fold, six names remained held: Thundergod's Vigor, Toothrow, Witherstring, Latent Cold
Rupture, Latent Rotting Fissure, Latent Crack of the Heavens. **Every one is a real find.** Their
frames were opened and read by hand: all gold, each with a First Found date and a source monster.

They could not ground because each appears in **exactly one reel**, and one reel yields only
`cross-frame` — a single tag. **216 focused reads across two different targeting strategies found no
second sighting**, which is not a failure of the hunt: the footage does not contain one. No amount of
re-reading his own reels could ever have closed this.

**What closed it was a DIFFERENT MODEL FAMILY on the same pixels.** Each frame was handed to Grok
cold — no hint of which name was being tested, phrased so the answer could come back negative ("list
only the rows that are gold and have a First Found line"). It returned all six by name with dates
matching exactly, and that read is `cross-lane`: a genuinely independent witness, recorded with its
lane, model and the string it actually produced (`tv/g5_second_lane_v1789.json`).

Ledger: **255 grounded / 6 held → 261 grounded / 0 held.** Nothing was hand-entered; the six passed
the same gate as everything else, on evidence a machine produced. This is what "Grok is additive, not
required" means in practice — its absence had cost coverage, exactly as designed, and never
correctness.

---

## REG-180 — the gate counted witnesses on RAW reader strings, so two spellings of one item never corroborated each other (v1789)

**His inbox held 36 names waiting for a hand-tick, and six of them were decisions.**

The queue was read by hand, name by name, against the board's own 398-name roster:

| what it was | how many | examples |
|---|---|---|
| an unresolved unique — a real decision | 6 | Toothrow · Witherstring · Thundergod's Vigor |
| an OCR slip of an item ALREADY grounded | 6 | "Battlecage"→Rattlecage · "Naglring"→Nagelring · "Heart Garver"→Heart Carver · "Twitchthrow"→Twitchthroe · "Gravepalms"→Gravepalm |
| reader debris | 24 | base names (Bone Visage · Templar Coat · Wrist Sword) and truncations (Firel... · Natalya's... · "Heavas (partially obscured)") |

**The debris has a specific cause worth naming, because it makes the rule obvious: THE CHRONICLE
PRINTS THE BASE ITEM NAME FOR A ROW HE HAS NOT FOUND.** "Templar Coat" is not a near-miss on a
unique; it is the game stating the OPPOSITE of a find, written down faithfully by the reader and
then handed to him as though it were a question.

**The defect underneath.** `witnesses()` keys on the string the reader produced. Two readings of one
row that differ by an apostrophe or a letter are two names, each with one witness, each held forever
— the gate is asked to corroborate and is handed the evidence pre-split. Folding onto the roster
BEFORE gating merged them: `Atma's Scarab` and `Atma’s Scarab` became one name with cross-frame AND
cross-reel, and grounded. Grounded count went 255 → 255 — **nothing was invented; two names were
corrected to the roster's own spelling** — and held went 36 → 6.

**The near-miss that shaped the fix, and the false diagnosis it produced on the way past.**
"Latent Cold Rupture" reads exactly like a quality prefix on "Cold Rupture", and the first cut of
the resolver stripped it. Then the roster was asked instead of assumed: it carries BOTH forms as
separate grail entries, and there are six such pairs — Black Cleft, Bone Break, Cold Rupture, Crack
of the Heavens, Flame Rift, Rotting Fissure. **Twelve slots, not six.** Stripping would have credited
him with items he had not found and deleted the twins from his hunt list. It also produced a wrong
finding I had already written down: that a grounded "Latent Black Cleft" could never tick. It ticks
fine; it is a roster name in good standing. `load_roster()` now RAISES when a fold rule collapses two
distinct roster items, so the next plausible-looking rule fails loudly instead of picking a winner.

**Fixed in** `tv/chronicle_resolve.py` (new) · `tv/roster_sync.py` (new — regenerates
`tv/unique_roster.json` from bible.html's own `_gUniqueRoster()`, so the roster rule is not written a
second time in Python) · `tv/control_app.py` `_chron_fold` wired at all three gate sites, including
the tuner, so its preview judges the same input the live gate does · board-side
`kaiChronicleResolvePending()` retires the same three classes from his localStorage queue and prints
a receipt, because a queue that silently got smaller is indistinguishable from a lost one.

**Guards:** `TestV1789TheRosterIsTheAuthorityOnWhatIsOneItem` (the six twin pairs stay two items; a
collapsing rule crashes; an empty roster is refused rather than retiring his whole queue; a stale
artifact fails in milliseconds with no browser) · `TestV1789TheGateReadsTheBoardsNames` (two
spellings corroborate; the fold is actually CALLED at ≥3 sites — proven red by unwiring it) ·
`tests/v1789_inbox_resolves_non_decisions.spec.ts`.

---

## REG-181 — the focused hunt was aimed at pixels that could not change the answer (v1789, caught before it shipped)

**It ran 325 seconds against three names and returned nothing, and nothing was the only thing it
could return.**

Built to earn a second witness for held names, its first design re-read the frames NEIGHBOURING a
known sighting. Then the arithmetic was checked against the six names actually being held:

    Latent Cold Rupture 2 sightings / 1 reel / ['cross-frame']    Toothrow           4 / 1 / ['cross-frame']
    Latent Crack of the Heavens 3 / 1 / ['cross-frame']           Witherstring       3 / 1 / ['cross-frame']
    Latent Rotting Fissure 3 / 1 / ['cross-frame']                Thundergod's Vigor 2 / 1 / ['cross-frame']

**Every one already had `cross-frame`** — one on four sightings. `witnesses()` returns a SET, so
another frame in the same reel re-adds a tag that is already there. The hunt was not under-powered;
its best possible outcome was the current outcome.

Worse, the first run *looked* like a clean negative. It reported "36 frames read, 0 new sightings"
for `Battlecage`, `Bloodfist Shard` and `Bloodthirst` — which was true, and was ALSO true of a
misread that names no real item. **A negative result from an instrument that cannot return a positive
is not evidence** (founding rule 5), and it read like one.

**Fixed** by aiming at OTHER reels, where a hit earns `cross-reel` — the tag these names need. The
Chronicle is sorted alphabetically, so a held name's row lies BETWEEN its alphabetical neighbours,
and those neighbours are already in the ledger with their frames. That turns "somewhere in another
400-frame reel" into a bracket of a few frames. A name with no anchors in another reel gets no
targets at all, because a blind sweep of a whole reel is the ordinary sweep with a smaller budget and
a better name.

**And then the corrected hunt was aimed wrong too, and only a picture showed it.** With the bracket
logic in place it ran 72 reads across four names and returned zero — a tidy, plausible negative. One
target frame was opened and looked at: the hunt for **Thundergod's Vigor** was reading the **W**
section — Winged Harpoon, Winged Helm, Wire Fleece, Witchwild String. One of his reels indexes **63
names against 39 frames**, so position stopped tracking the alphabet there and the nearest anchors
came back as "War Traveler" at position 2 and "Pelta Lunata" at position 8. Bracketing between them
is arithmetic on two numbers that were never comparable.

Every read in that reel was a guaranteed miss, and it arrived labelled as evidence of absence. The
code reads correctly in either state — **the only thing that separated them was rendering one target
frame and looking at the list on it.** A reel that fails the ordering check is now SKIPPED rather
than reordered, because swapping lo/hi would fabricate a range instead of admitting the index is
unusable. The well-formed reels bracket exactly as intended: `The Ward` (420) → `Tiamat's Rebuke`
(425), which is precisely where Thundergod's Vigor sorts.

**Guards:** `TestV1789TheHuntAimsWhereATagCanChange` — it never targets the reel the name was already
seen in, the bracket sits between the anchors, a reel whose frame order does not track the alphabet is
skipped, a hit is recorded with its reel so it earns cross-reel, and it stops reading a name the
moment it has its hit.

---

## REG-179 — the sweep threw away 56% of a slow scroll, and the tally sat ~9 short of the game (v1770)

Konyo, twice, after re-sweeping and seeing 249/403 unchanged: *"how come the percentage isnt 64% and
matching like it is INGAME? like something is off"* and *"i literally did it slow and went through
the uniques and scrolled slowly."* He was right on both counts.

**The number.** His in-game panel reads **64%** (visible bottom-left of his own frame). 64% of 403 is
~258. The board holds 249. So ~9 finds exist in-game that the board has never been told about — and
the board's arithmetic is fine: 249/403 = 61.8%, which is the 62% on screen. The *input* was short,
not the formula.

**The cause.** `MIN_RUN_FRAMES = 3` — "below this a run is somebody walking through town, not a screen
being read". Correct for gameplay, wrong for a Chronicle read. Measured on `reel_s_1786922954749_12579`:

| | |
|---|---|
| frames in the reel | 339 |
| distinct screens (`still_runs` @ `CHRON_STILL_MAX_DIFF`) | **55** |
| screens kept by `min_frames=3` | **24** |
| screens discarded before anything looked at them | **31 (56%)** |
| of the discarded, runs only 1 frame long | 25 |

At ~6 found rows per screen that is roughly **180 item rows the sweep never read**. A Chronicle page
carries three lines per found item (name / First Found / Dropped By), so only ~7 rows fit a screen and
403 uniques needs ~58 screens to scroll — the reel was never going to survive a 3-frame floor.

**Why the existing fix did not cover it.** v1689 found this same defect from the other side and its
docstring names it exactly — *"reading a Chronicle means scrolling it, and a scroll is never still"*.
`_journal_runs()` rescues short runs the vision lane had already marked, at zero classify cost. Real
fix, starved input: the journal had marked 13 frames. Half a joint. [[the-unjoined-end]]

**The fix.** The discriminator is the reel itself. Once any run comes back `chronicle-*`, the
walking-through-town rationale cannot apply to that reel — it IS a recording of the Chronicle — so the
floor drops to 1 for the rest of that reel and nowhere else. Runs whose frames were already read in
the first pass are excluded, so v1689's zero-classify guarantee is untouched.

Measured after: his reel goes **24 → 55 screens read**, 31 rescued, 44% → 100% coverage of what he
filmed. Red-proofed both ways — disarm the rescue and the new test fails `0 != 8`; a reel that is not
a Chronicle still pays for exactly one classify.

**Still open, and not this bug:** the second eye (Grok) answers 402 on every call, so a name read on
one screen gets one witness and the gate needs two. Until that is topped up, recovered names land in
the inbox as pending rather than ticking. See v1768.

## REG-178 — the two "gold-on-green" --best fallbacks: CLOSED on measurement, not on opinion (v1753)

Two `var(--best, …)` fallbacks were parked as needing Konyo's ruling on contrast: `.aura-tag-target`
(#c9a14a) and `.forge-donow-h` (#e8c878). Measured instead of asked, and **neither is a contrast
problem**:

| element | foreground | background | contrast |
|---|---|---|---|
| `.aura-tag-target` | `rgb(26,18,7)` near-black | gold end `#ffd480` | **13.22** |
| `.aura-tag-target` | same | green end `#66ff88` | **14.31** |
| `.forge-donow-h` | `rgb(102,255,136)` | painted `rgb(10,8,5)` | **15.45** |

WCAG AAA is 7.0. All three are roughly double it. **No ruling needed.**

⚠ **The first measurement was WRONG and is worth recording, because the mistake is reusable.** I
appended the probe elements to `document.body` and read `.forge-donow-h` as cream `rgb(244,232,208)`,
which looked exactly like the "last declaration wins" scar — a second rule quietly beating the token.
There is no second rule. The single rule is SCOPED, `:is(#tab-forge,#tab-funi,#tab-fsets)
.forge-donow-h`, so outside those tabs it never applied and the element simply inherited body text.
**A probe that renders an element outside the scope its CSS is written for measures the absence of
the rule, and reports it as the presence of a different one.** [[feedback_suspect_the_instrument]]

### What WAS wrong, one layer down

Of the 33 `var(--best, …)` fallbacks, **ten named the wrong colour**: six gold (`#e8c878` ×5,
`#c9a14a`) and four near-greens that are not the token (`#7ddc7d` ×2, `#7bc77b` ×2). The other 23
already used `#66ff88`, so the convention was right and these were drift. Normalised to 33/33.

**Nothing rendered differently, and that is the point.** `--best` is defined at `:root` and 415
elements resolve it, so the fallback branch never runs — verified, not assumed. What was wrong is
what the code SAYS: a fallback documents the token it stands in for, and in ten places it stated a
colour the token has never had. Same shape as the extractor claiming *The Seven Tombs* for a picture
of a ring. [[label-outlived-referent]]
---

## REG-177 — his "I'm pretty sure I'm 64% uniques" was right, and nothing was miscalibrated (v1751)

He asked twice: *"make sure the % ingame for the chronicle matches and syncs too it needs to be
caliverated maybbe. im prety sure im 64% uniques so eaither didnt count correctly.. or its not
calliberated correctly."*

**Measured live in a browser:** `funiScan()` returns `total: 398`, `found: 246`, `chronTotal: 403`.
The meter at `:37035` already divides by `chronTotal` — the GAME's denominator — not by the roster,
so **the formula was never wrong**. The three numbers on his screen are three different true facts:
403 is what the in-game Chronicle counts, 398 is what the site can put a NAME on, and the 5 dark
rows he asked about are exactly `403 - 398` (`:37075`), silhouettes the game refuses to name until
they drop.

**The gap is arithmetic, not calibration.** 246/403 = 61.0%. Add the **13** finds sitting in the
chronicle visit that was never read (`ts 1786923296176` = 2026-08-17 02:34:56 IDT, `ledger:
uniques`, 4 frames) and it is **259/403 = 64.3%** — his number. Three independent signals agree: his
memory of the in-game panel, last session's cross-reference of his own screenshots, and the board's
own tally.

**Stated as a falsifiable prediction:** once that visit is read the board should land on ~64%. If it
lands anywhere else, the unread visit was not the whole story and this entry is what to re-open.

### The loose end that came with it — 403 vs 404, left OPEN

`chronTotal:403` is a hardcoded literal whose tooltip states its provenance as *"game-file truth:
uniqueitems.txt"*, while `:17315` records an actual reading of the in-game panel as **404, printing
63%**. Two numbers in one file, one entry apart, and neither is re-derivable on this machine: the
CASC extractor lives at `/tmp/casc_extract` and `/tmp` does not survive a reboot. **Recorded at the
definition site rather than averaged** — a denominator quietly nudged to make a percentage look
right is precisely the defect this board keeps finding. It does not move his answer: 259 is 64%
against either total.

**2026-08-20 — revisited, still OPEN, and the evidence trail was repaired.** The CASC route is
confirmed closed on this machine rather than assumed: `tv/casc_extract.c` (the extractor SOURCE)
survives in the repo, but there is no reachable game storage — no CrossOver bottle, no `.build.info`
anywhere under Application Support — so `uniqueitems.txt` cannot be counted here and 403-vs-404
cannot be settled by measurement. What COULD be fixed was the pointer: this note's evidence was
cited as `:17315`, and the file has grown enough since v1751 that the line now holds crafted-amulet
definitions. Anyone chasing the 404 landed on unrelated code. Both citations are by searchable text
now, not line number — a line number is a reference with a short half-life, the same defect class as
a stale count.

Two counts in that same block had rotted the identical way and were re-measured: it read "385 named
+ the 18 still-dark rows" where the roster is now **398 named + 5 still-dark** (still 403), and it
pointed at `~line 13641` for `__allSets()`, which now lives at 14122. The paragraph immediately
above those figures warns that a count in a comment is a number nobody re-measures — it had become
its own example. The split is no longer restated as literals; `python3 tv/roster_sync.py` prints the
live count.
---

## REG-176 — v1736 broke twelve console specs, and CI said so while local smoke did not (v1749)

**Routine I — the full Playwright suite — went red**, and it was mine. The last green Routine I was
**v1735**; everything between was CANCELLED by the next push, so the first run that got to finish
already carried the break. That is worth naming on its own: pushing fast enough to cancel your own
CI hides which commit did it.

**The cause is v1736 working exactly as designed.** It made the console's `lsFork` honour
bible.html's v1499 instruction — *"a reader that finds no route, a v:1 route, or an id it does not
recognise must resolve UNKNOWN and read nothing. Guessing bare is how the harm happened."* Before
that it fell back to the bare key.

**Twelve console specs seed `d2r_forgeSummary` / `d2r_grailFarm` / `d2r_setFarm` and NO
`d2r_lsrRoute`** — so they were leaning on the guess that was removed. `v1615` failed on exactly the
surfaces that render from that data:

```
a surface is missing its sets icon: ["/art/ui_tab_fsets.png","/art/ui_tab_fsets.png",null]
missing: ["/art/ui_tab_funi.png","/art/ui_tab_funi.png",null,null]
```

The tab strip and MINI focus row (which read their art directly) were fine; every **Task Force**
surface, which reads through `lsFork`, was empty.

**The fixture was modelling a state production cannot reach.** Console data exists only because the
board ran, and the board writes the route as it does — so a console holding data with no route is
impossible in the field. Seeding it makes these specs *more* faithful, not less.

`seedOwnerRoute()` and `OWNER_ROUTE` now live in `tests/_net_stub.ts` — **one definition**, imported
by the specs that need it, rather than twelve pasted copies of a payload shape that would drift from
bible.html's. **[[copy-drift]]** OWNER / main profile, `pfx ''` and `lpfx 'L·'`, which is what makes
`lsFork` land on the bare keys these specs seed.

Fixed and verified locally: **v1615 8/8**, the nine bulk-wired specs **71/71**, **v1554 8/8**.

⚠ Two of the twelve needed no change (`v766_tvd_console`, and v1554's other tests) — they never read
through `lsFork`. The sweep listed them because they seed localStorage; only the ones whose surfaces
read the board's world were affected.

### v1749 continued — the rest of Routine I, and what was NOT mine

The first fix cleared `v1615` but Routine I stayed red, on three more specs. Splitting them honestly:

**MINE, same v1736 cause:** `v1556_meter_coverage` seeded `d2r_lsrRoute` as **`{ prefix: '' }`** — a
shape from before the route carried a version. The old `lsFork` ignored it and fell through to the
`d2r_activeMachine` fallback, landing on the bare key by accident; v1736 refuses a route it does not
recognise, so this seeded nothing readable and *"the Daily Task Force must render chronicle rows at
all"* went red. Now the real payload, from `OWNER_ROUTE`.

**NOT MINE — pre-existing fragility to the outside world:** `v146_ref_header_unify` and
`v157_set_tracker_rich_cards` assert *"no console errors"* and *"the gradient bar must actually
occupy space"*. bible.html pulls its typeface from **fonts.googleapis.com / fonts.gstatic.com**, and
on a runner whose outbound network is slow or blocked those requests fail.

Reproduced locally by blocking external hosts: the reference tab logs `Failed to load resource` and
`.set-card-header` measures **0px tall**, because the bar's height comes from text with no font to
lay out. **The same collapse reproduces on v1735 — the last green Routine I** — so it predates this
work. The specs were always one bad minute of weather away from red; my runs simply hit it, on the
same night Routine G aborted on a `fonts.gstatic.com` woff2.

Fixed where the other external stub already lived: `_net_stub` now fulfils both font hosts —
**empty CSS, empty woff2**, never `abort()`, because an abort is itself a failed request and
`page.screenshot` waits on fonts (`chrome-cdp-mac`). One place, every spec.

⚠ Worth stating plainly: **two of the four failures were mine and two were not**, and it would have
been easy to "fix" all four as one regression or dismiss all four as flake. They needed separating
before either verdict was safe.

---

## REG-202 — the vault gate refused his clearest stash frames (FIXED v1860)

**Found:** 2026-08-20, by measuring the gate against every frame in `tv/frames/hist/` rather than
against a fixture.

`stash_screen_open()` decided ADMISSION by asking `tab_from_ocr_lines()` **which tab is selected**.
That function abstains — returns `""` — whenever 2+ canon labels are legible, and it is right to:
the stash strip prints all five tab names whichever one is active. The gate read that abstention as
"not a stash frame".

So the **strongest possible evidence that his stash is open** produced the same verdict as an empty
frame. Measured on his own reels: of the 68 frames the grid fingerprint called a stash panel, four
carried unmistakable chrome — `['$•NAL','SHAkED','% Gems','I mATeRIALS']` and
`['S*NAL','SHARED','g Gems','mATeRIALS']` among them — and **all four were turned away**. This is
`the-unjoined-end`: a gate built correctly and joined to the wrong question.

**Fix.** `stash_eye.stash_chrome_canons()` is now the admission signal — how many canon labels are
legible. One is proof the panel is open, four is overwhelming. `tab_from_ocr_lines()` keeps its
abstention for the tab question, where abstaining is correct. Ambiguous chrome now answers `"stash"`
(true, and not a tab) instead of `None`.

Admitted, over the same 68 frames: **3 → 5**. Refused: 63, and those were verified by eye to be
gameplay — one is a Durance-of-Hate fight. **Guards:** `test_control.TestTheVaultTemplateGate` —
`test_FULL_chrome_admits_it_is_the_strongest_proof_the_stash_is_open`,
`test_ambiguous_chrome_names_no_tab_it_did_not_read`, `test_junk_chrome_still_refuses` (the mirror,
or the fix is just a gate that always says yes).

## REG-203 — `classify_stash_grid` calls a fire-lit gameplay frame `stash-gems` (OPEN)

**Found:** 2026-08-20, while checking whether the gate was over-refusing. It was not — the GRID was
over-claiming, and I nearly filed the instrument's error as the gate's.

`tv/frames/hist/f_1786554127532.jpg` is a Durance-style fight lit by a wall of fire. `classify_stash_grid`
returns **`stash-gems`**. The v1258 not-D2R guard does not catch it: fire supplies the chroma and the
dark scene supplies enough dark columns for `panel_open` to read true. It is the same shape as the
scar already recorded in that function — *"69 wallpaper frames sealed as stash-gems"* — in a new
flavour.

**Exposure, measured:** across all 847 hist frames the grid names a tally tab on **9**; **8 of those
9 have no legible tab chrome at all**, i.e. they are not stash panels. In `fuse_tab_signals` rule 2,
`allow_grid_solo=True` (the KAI retro path) lets grid promote a tally tab with **no** corroboration,
so those 8 can be filed as gems/materials panels in retro.

**Not fixed here** — retuning a pixel fingerprint needs its own before/after sweep over the whole
corpus, and the vault lane is already protected by REG-202's chrome gate, which refuses all 8.

## REG-204 — a solo OCR tab GUESS outranks two disagreeing witnesses (OPEN)

**Found:** 2026-08-20, sweeping the class of the v1857/v1859 defect.

`stash_eye.fuse_tab_signals` rule 1 — *"OCR tally wins over vague vault labels"* — returns the OCR
tab **before grid or model are consulted at all**. The intent is sound (a specific tally word should
beat a vague `shared`/`vault` label); the implementation also beats a **specific and different**
tally tab. Measured:

```
fuse_tab_signals(ocr_tab="gems", grid_label="stash-runes")            -> ('gems', ['ocr'])
fuse_tab_signals(ocr_tab="gems", grid_label="stash", model_tab="runes") -> ('gems', ['ocr'])
```

One witness — one that names itself a *guess* in its own docstring — overrules two that disagree,
and reports `sources: ['ocr']` while doing it. That contradicts the multi-witness doctrine directly.
v1194 fixed the neighbouring half (an OCR-only fusion masquerading as a grid vote in
`_kai_grid_vote_label`); it did not touch which tab is chosen.

**Not fixed here, deliberately.** The correct behaviour on a contradiction is to name no tally tab
rather than to pick a side — but the disagreement is **not exercised by any frame in his corpus**
(zero occurrences across the 68 stash-panel frames), so a change here would ship untested against
his data. Filed with the measurement so the next pass starts from evidence rather than from this
paragraph.

## REG-205 — the selected stash tab IS visible in the pixels; reading it is not solved (OPEN)

**Found:** 2026-08-20, looking at the frames REG-202 newly admits.

The tab question is answered by a documented **guess** today (REG-204, v1859). But the answer is
right there in the picture: D2R draws the ACTIVE tab boxed and brighter — `MATERIALS` in
`8_1785078207015.jpg`, `PERSONAL` in `6_1784984233446.jpg`. A pixel read of which label is
highlighted would replace the guess with a structural fact, exactly as the chrome gate replaced a
model's opinion.

**Tried and measured, so the next pass does not re-derive it.** Crop `_TAB_CHROME`, find the
brightest row band, split into five equal cells, take the argmax mean luminance:

| frame | truth | cell means | argmax | margin |
|---|---|---|---|---|
| `6_1784984233446` | personal | 57.7 52.7 51.7 50.6 45.5 | **personal** ✓ | 5.0 |
| `8_1785078207015` | materials | 63.2 77.3 80.1 74.0 66.3 | gems ✗ | 2.8 |
| `5_1784984201581` | runes | 47.4 54.5 60.9 59.6 49.7 | gems ✗ | 1.2 |

**1 of 3, on margins of 1–5 grey levels.** The five-equal-cells assumption is the flaw: the labels
are not equal width (`Gems` is short, `Materials` long), so a cell straddles two labels and the
bright pixels land in the wrong bucket. Segmenting by the separators, or matching the box border
rather than the fill, are the next things to try.

**NOT shipped.** Three hand-labelled frames is not a corpus, and a plausible-but-wrong tab detector
is the precise defect v1857 and v1859 already cost. Ground truth in this table was established by
opening the images. When he records a stash reel, label its frames and calibrate against those.

## REG-206 — the vault lane cannot ledger a stash by looking at it (MEASURED, by design not defect)

**Found:** 2026-08-20, by running the whole vault chain end-to-end on the exact template Konyo
described — `6_1784984233446.jpg`: Stash open on the left with **Personal** selected, Inventory open
on the right, both full of items.

Every link works:

| step | answer |
|---|---|
| `stash_screen_open` | `"stash"` — admitted (v1860) |
| `claude_read` (classify) | `scene: "stash"`, `stashTab: "personal"`, conf 0.95, 31s, G5/grok |
| `claude_vault_read(…, "stash")` | `{"items": [], "conf": 0.0}` |

The reader was genuinely asked — the raw `_oneshot` reply was captured: `sonnet, 8s ->
{'surface':'materials','items':[],'conf':0.0}`. Same answer on the Runes tab
(`5_1784984201581`) and the Materials tab (`8_1785078207015`).

**It is right.** `VAULT_READ_PROMPT` says *"Return a row ONLY when you can actually READ its name on
this image"* — and **D2R prints no item names in a stash grid.** A name exists only in the HOVER
tooltip. The one name that DID come through on that frame arrived exactly that way: the classify
returned `names_loc: {"Tome of Town Portal": "inventory"}`, read off the tooltip he happened to be
hovering.

**What this means for the footage he records.** Parking on an open stash grounds nothing, however
long the recording. To ledger items by name he must **hover them**. The alternative — ledger by icon
and stack count rather than by name — is a different design and his call.

**Shipped alongside:** the sweep now counts and names this third outcome, so its report says
*"read cleanly and held no readable name"* instead of offering "unreadable page or empty shelf",
neither of which was true.

## REG-207 — the inventory read was cropped to the stash panel (FIXED v1861)

`claude_vault_read` cropped every non-tally surface to the `runes` band — the **left** stash panel.
For `surface="stash"` that is roughly right. For `surface="inventory"` it handed the reader HIS
STASH and asked it to read his inventory, so the honest reply was always "not an inventory panel,
items empty": a lane that could never ground a row, reported as an empty shelf.

No inventory band is calibrated anywhere in `stash_eye` — the tally crops were measured for the left
panel only. Rather than invent one, `inventory` now reads the **full frame**: more tokens, and the
only rectangle known to contain the panel. [[unknown-stays-unknown]]

## REG-208 — a throttled page burned one of its three looks (FIXED v1861)

The re-read cap (his ask: *"after third read it should be blocked..? safegaurd?"*) counted reads
that never happened. `_read_one` bumped the counter unconditionally, under a comment that said the
opposite — *"bump only when a read was really attempted — a throttled or capped page must not burn
one of its three looks."* The CAPPED case returned early so it was safe; **THROTTLED and
BUDGET-BLOCKED fell straight through to the bump.**

`claude_chronicle_read` answers those two with `{"note": "reader throttled — not read"}` and
`{"note": "not read — <why>"}` and reads nothing. So three throttled sweeps would retire a page that
had never been read once — and the cap message would then tell him to re-read it *"by changing the
reader"*, about a page the reader never saw.

Measured, old vs new, five refusals on one frame: **count 5 → 0**, **capped True → False**.

The decision moved out of the closure into `_chron_read_bump_if_read()` so a test can drive it; the
version that could not be driven was wrong for two ships. **Guards:** `test_control` —
`test_a_THROTTLED_page_does_not_burn_a_look`, `test_a_DEAD_lane_does_not_burn_a_look_either`,
`test_a_REAL_read_still_spends_one` (the mirror), `test_the_sweep_spends_looks_through_THIS_function_only`.

## REG-209 — three different set counts on one screen (FIXED v1862)

**Reported by Konyo, 2026-08-20:** *"this dailt tasks is not sycned to the counter as the sets and
uniques tabs"* — with two screenshots three minutes apart:

| surface | says |
|---|---|
| F·Sets tab | **116**/135 · 86% · 19 pieces still missing |
| console DAILY TASK FORCE, progress row | **113**/135 · 84% · 22 pieces left |
| console DAILY TASK FORCE, daily pick sentence | **112**/135 pieces |

Each surface is internally consistent (135−116=19, 135−113=22). They disagree with each other, and
**two separate staleness bugs** produced the two wrong numbers.

**113 — the bridge cache key omitted the value it was caching.** `d2r_forgeSummary` is written only
on real change, and `_fsCmp` computes the signature that decides. `sets` joined the payload in v922;
`_fsCmp` dates from v913 and was never updated. A change in the set count alone produced an
identical signature, so the bridge was never rewritten and the console served whatever snapshot was
stored the last time the GRAIL or a RUNEWORD moved. Measured: of the six `fs.<chronicle>.<field>`
values the console PRINTS, **four were absent from the comparator** — `sets.found`, `sets.total`,
`grail.total`, `chron.total`.

**112 — a cached sentence quoting a count that had moved.** `dailyCreateAi` generates one sentence
per day and caches it, count frozen inside. A staleness check already existed and covered only
RUNEWORDS (*"if the cached pick NAMES a runeword the player has since made"*); nobody extended the
reasoning to the other chronicles. Now the `N/M` pairs in the cached sentence are compared against
the live rotation — same denominator, different numerator means the sentence describes a state he
has left — and it is regenerated. No model call: the grail/sets pick is computed locally.

**Guards:** `test_control.TestTheBridgeCacheKeyNamesWhatItCaches` — a cross-file invariant, since
neither file alone shows the defect: every `fs.<chronicle>.<field>` the console prints must appear
in the comparator that decides whether it is refreshed.

## REG-210 — "I don't have 116 items" — the Chronicle counts FOUND-EVER, not HELD-NOW (ANSWERED)

**Konyo, 2026-08-20:** *"this is incorrect i didnt and dont have 116 items... the last item i
defintely dont have where did it read this exactly? where is the tooltip image for it"*

Provenance, from `chron_evidence.json`, for **Immortal King's Will**:

```
reel s_1787177267889_92273  frame f_1787177298256.jpg  lane claude  conf 0.55
reel s_1787177267889_92273  frame f_1787177298256.jpg  lane grok    conf 0.55
reel s_1787177267889_92273  frame f_1787177300387.jpg  lane claude  conf 0.55
```

That reel is his own **🧩 Set pieces** recording. Opening the frame: it is his in-game **Chronicle →
Sets** panel, sorted Newest to Oldest, and the row reads —

> **IMMORTAL KING'S WILL** · Dropped By: **Andariel** · First Found: **07/18/2026, 02:47**

— in the gold found styling, with the drop provenance the game prints only for pieces you have
found. Two frames, two independent lanes, and the game's own words.

**It is not a tooltip read.** A tooltip IS on screen in that frame (he was hovering the item, green
"Immortal King's Will / Avenger Guard"), but the ledger entry came from the ROW, which is the
Chronicle's own record.

**The gap is FOUND-EVER vs HELD-NOW.** The in-game Chronicle is a holy-grail ledger: it records
what has ever dropped for him, permanently, whether or not he still holds it. The board mirrors that
ledger, so 116 is "pieces the game says you have found", not "pieces in your stash". His own in-game
Sets bar on that very frame reads **85%** against the board's 86% — the same truth, one piece apart.

Nothing to fix in the reader. If he wants a HELD-NOW count that is a different ledger and a
different feature — and per REG-206 it cannot come from looking at a stash, because D2R prints no
names there.

## REG-211 — MINI has been dead since v1853 (FIXED v1863)

**Reported by Konyo:** *"for sets when i click MINI and the sets for a reel record it does an
error"*, then *"the MINI doesnt work for them all"*.

v1853 removed `_focus_was_chosen` as dead code — correctly, nothing called it — and took the six
constants beside it: `MINI_MIN_SECONDS`, `MINI_MAX_SECONDS`, `MINI_DEFAULT_SECONDS`,
`MINI_CHRONICLE_FOCUSES`, `MINI_CHRONICLE_MAX_SECONDS`, `MINI_CHRONICLE_DEFAULT_SECONDS`.
`_mini_bounds` still names all six.

Every `/api/mini` POST raised `NameError` → 500 → a non-JSON body → the console's `fetch().json()`
threw → its catch printed **"mini could not start — the console is not reachable"**. Ten versions,
every focus, and the only thing on screen blamed the network.

```
_mini_bounds('stash')            NameError  ->  (25, 40)
_mini_bounds('chronicle-sets')   NameError  ->  (75, 120)
```

**Guard: `test_control.TestNoFunctionLoadsAnUndefinedName`** — a static AST scope walk over nine tv
modules. Python resolves a name used only inside a function body when that LINE RUNS, so this class
cannot be caught at import and no test that never called `/api/mini` could see it. Seen red against
the exact shape v1853 left behind.

## REG-212 — the in-game First Found date reached nothing (FIXED v1864)

**Konyo:** *"i want the console also updateing me on when it was found timestamped in the game..
(not when the AI READ IT) ... it should be storyline synced with the ingame diablo ii"*

Every end of this path already existed; the middle did not.

| step | state before |
|---|---|
| the reader returns `foundAt` / `droppedBy` | ✅ since p1839 — measured live: `{"Immortal King's Will": "07/18/2026, 02:47"}`, `{"...": "Andariel"}`, matching his pixels |
| `proposal_from_pages` hangs them on each sighting | ✅ since v1819 |
| the sweep payload carries them | ❌ `name` / `why` / `witnesses` / `seen` only |
| `bible.html` consumes a per-row date | ✅ since v1693 — **and had never once been fed** |
| the SETS branch consumes one | ❌ never existed |

Result: **0 of 339 names** in his stored proposal carried a date, and every find was filed with the
moment the sweep ran. [[plumbing-with-no-tap]]

Now: `chronicle_retro.in_game_stamp()` resolves the date and the dropper **by agreement** across
sightings (a First Found date is a fixed fact, so two lanes printing the same string is
corroboration; a tie between two different values returns nothing rather than a coin flip). The
payload carries `gameFound`. Both board branches consume it, and `d2r_gameFound` keeps the game's
answer **beside** `d2r_foundLog` rather than overwriting it — "when the game says he found it" and
"when this board learned of it" are different questions and both keep an answer.

⚠ **The date order is measured, not assumed.** `07/18/2026` can only be July 18, so his D2R prints
US `M/D/YYYY` — which is what settles the ambiguous rows (`06/02/2026` is 2 June). Anything not of
that shape is refused rather than approximated; a wrong find-date reorders his history.

**Guards:** `test_chronicle_retro.TestTheGamesOwnFindDate` (agreement, tie→nothing, date and dropper
decided separately) · `test_control.TestTheGameFindDateReachesTheBoard` (the seam, both branches,
the sets branch by name) · `test_control.TestTheGameDateConversionRunsInARealEngine` (the JS
converter run in **node**, including the refusals).

## REG-213 — a silent OCR lane and a dark strip gave the gate the same answer (FIXED v1864)

Found because `TestPrepTabChromeIsNotDead` went RED once mid-run and passed alone seconds later:
Konyo's live session held the OCR worker, `ocr_fast` returned no lines, and `stash_screen_open`
answered `None` for a genuine stash frame.

Zero lines means either a genuinely blank strip (gameplay — 61 of his 68 grid-called stash frames,
correctly refused) **or** an OCR lane that could not run. The frame-level answer cannot tell them
apart and stays `None`, which is the safe direction. The **run** can: every probe silent means the
lane is down, not that his footage holds no stash. Counted as `gate_hearing() -> (silent, heard)`
and read out at the end of a sweep. [[feedback-silence-is-not-evidence]]

## REG-214 — a simulation looked exactly like a live session (FIXED v1866)

**Found:** 2026-08-20, investigating Konyo's *"i did a regular LIVE SESSION it worked... make sure
to see the coding logic for ai readers are correct"* — his Sets chronicle was open and nothing read
it as a chronicle.

**The readers are correct.** `control_agent.log` records five agent starts in 64 seconds while MINI
was dead (REG-211): **sim · live · live · sim**. Under `TV_STUB` the deep reader returns canned rows
from `stub_manifest.json` whose `scene` defaults to `"gameplay"` — so a Chronicle page open on
screen is journaled as gameplay, and nothing in the pipeline is broken.

⚠ **CORRECTION, and then a correction to the correction — the record keeps both, in order.**

**v1869 said the attribution above was wrong.** It was half wrong. `test_button_matrix` and `test_roundtrip_sim` spawn their own control app and write
`—— control start … mode=sim ——` banners into the same `control_agent.log` — 14 and 4 lines per run
— so the "five starts in 64 seconds" I read as Konyo at his keyboard were **my own gate runs**.
Founding rule 4: suspect the instrument.

**v1870 settled it from his own data instead, and the original story holds.** Reel
`s_1787244002054_15361` is unmistakably his — shared stash open at page 1/5, a **Raven Frost**
tooltip under the cursor — and its journal rows read `lane=deep mode=stub`, so those reads were
canned. His running console's environment carries `TV_FILM=1` and `TV_OCR=1` and **no `TV_STUB`**,
so a non-sim start could not have produced canned rows: that session was started with **SIM**.

What remains true from the correction: the log banners are polluted by tests and were never
admissible evidence. What changes back: the conclusion was right, reached the wrong way.
[[feedback-suspect-the-instrument]] [[feedback-contradiction-is-the-finding]]

**His journal holds 414 rows written under TV_STUB across ten days** (08-02 → 08-20), beside real
ones, with nothing to tell them apart except `mode: "stub"` on the deep-read rows. Session summary
rows carry no mode at all, so a whole SIM session was indistinguishable from a live one that saw
nothing.

Worse, the console *believed* it excluded them: `HD_ALL` filters `x.stub`, and `stub` in that
payload means **a 1-read ghost with no footage**, not a simulation. His six- and seven-frame sim
sessions passed straight through and were counted as *"runs recorded today"*.
[[label-outlived-referent]]

**Fixed:** every journal row written under `TV_STUB` now carries `sim: true`; the sessions payload
exposes a real `sim` field derived from the rows; the TODAY row counts runs and simulations
separately and **says so** (`24 runs recorded today (+3 sim)`) rather than hiding them — he presses
SIM on purpose.

⚠ **The contamination exposure is real and has not fired — both halves belong in the record.**
`stub_manifest.json` carries real item names (`Ars Dul'Mephistos` is in bible.html's own
`_UNI_EXTRA`, `Skin of the Vipermagi`, `Ist Rune`) and nothing excluded a sim reel from a sweep. It
never landed because the manifest is keyed by basenames his reels never use (`pit_loot.jpg`,
`town_stash.jpg`) and the `"*"` fallback returns `names: []`. **Measured: 0 of 414 stub rows carry a
canned name.** A guard that depends on a filename not colliding is not a guard, so the flag is now
the guard, and a test asserts the fallback still returns no names.
[[feedback-fixtures-never-touch-live-data]]

## REG-215 — a test harness wrote 1,729 rows into his live journal (FIXED v1867)

**Found:** 2026-08-20, tracing his session history. `tv/sessions.jsonl` holds **1,729 rows** whose
session id ends `_dur` and whose note is `"durability-harness"` — **75% of every `session_end` row
in his journal** — and they were still arriving *during tonight's gate runs* (7 more at 18:35,
18:44, 19:11, 19:21, 19:36 and 20:04).

`test_reel_index_durability.py` isolates its frames correctly: its child gets `TV_FRAMES_DIR` and
`TV_HIST` pointing at a temp tree. It never knew there was a **third** path —
`tv_diablo.JOURNAL = os.environ.get("TV_SESSIONS") or HERE/sessions.jsonl` — so
`close_session()` appended into his live journal regardless.

**Fixed at the module, not just the call site**, which is what his scar demands: an overridden
`TV_HIST` that does not live under `tv/` now implies an overridden journal, so a caller that
isolates the frames gets an isolated journal whether or not it thought to ask. An explicit
`TV_SESSIONS` still wins (the CI harness has always used it and knows what it is asking for), a
`TV_HIST` *inside* `tv/` is his real world and keeps his real journal, and the harness also names
its own journal now — belt to that braces. [[feedback-fixtures-never-touch-live-data]]

**Proven by running the suite twice**, which is the other half of that scar: `_dur` rows in his
journal **1729 → 1729** across a full `test_reel_index_durability` run that previously added seven.

**No purge, and no surface was lying.** Each `_dur` session is a single `session_end` row with zero
frames, so `_theatre_sessions` already marks it `stub` (a 1-read ghost with no footage) and the
console's shelf filters it out. The rows are journal bloat, not a wrong number on a screen — and
they are his data, so they stay unless he says otherwise.

## REG-216 — the live-state gate learned to watch the journal and found three leaks in an hour (FIXED v1868)

`run_gates`' live-state watchlist named five chronicle/vault files and **not** `sessions.jsonl`,
which is why REG-215 survived for months of green runs. Adding it (plus `chron_reads.json`, live
state added this week that the list never followed) turned the gate **red within one run**, and it
kept finding writers:

1. **`test_reel_index_durability`** — 1,729 rows (REG-215, fixed at the module).
2. **`test_button_matrix`** — boots a private control app on a private free port with `--no-open`,
   terminating only its own pid: every process-discipline lesson applied, and then it handed that
   app **his real environment**. Six rows per run into his journal, plus his hist root and his
   chronicle state. **Isolating the port is not isolating the world.** Now sandboxed on all six
   paths; measured 4173 → 4173 across a full run that previously appended six, and every check
   still passes.
3. **The subscription-cap tests** — this class exists to *cause* refusals, and a refusal is
   journaled. Every run appended `{"lane":"skip","note":"subscription daily cap 50/1 (oneshot)"}`
   to his live file — the source of those rows. Worse, `test_a_capped_vault_read_names_the_refusal`
   restored `_sub_budget_load` in its `finally` and **not `_SUB_DAILY_MAX`**, leaking a daily cap of
   **1** into every later test in the same process.

**A blanket `TV_SESSIONS` for every gate subprocess was tried and reverted.** It stopped the leaks
and broke eleven tests that already isolate correctly by repointing `control_app.HERE` at a tempdir
— an env var outranks their patch. A lock that overrides working isolation is not a stronger guard,
it is a different bug. The reason is recorded in `run_gates.py` so it is not re-attempted.

**Now: a full 32-gate run leaves his journal byte-identical.**

## REG-217 — a millisecond timestamp in a seconds meter never expires (FIXED v1868)

His live `.subscription_budget.json` held `1787177667153.0` among 404 seconds-scale entries. Both
windows read `now - t < WINDOW`; for a value ~55,000 years in the future that difference is hugely
**negative**, so it passed every window forever — one permanent slot off the hourly cap *and* the
daily cap, invisible, unable to age out.

Harmless at 4000/hour and 20000/day; not harmless as a mechanism, and **not new** — the same unit
collision is already on the record against the G5 lane. A meter the passage of time cannot correct
only ever moves one way.

`_sub_budget_calls()` now rescales a millisecond value rather than discarding it (the real moment is
recoverable: 1787177667153 → today 18:14), drops anything beyond a minute of clock skew into the
future, and uses a **two-sided** window — *"not older than a day"* and *"not in the future"* are two
conditions and the one-sided test only ever checked one. Normalised on write as well as read, or the
next recorded call copies the poison straight back in.


## REG-218 — one gate run rewrote five of his live files, and spent a real vision call (FIXED v1869)

With the journal leak closed, the same question was asked of the WHOLE tree rather than a watchlist:
hash every file in `tv/`, run all 32 gates, hash again. **Five files changed** —
`.subscription_budget.json`, `.tvd_beacon.json`, `control_agent.log`, `g5_stats.json`, `state.json`
— and the first of those means a gate run **spent one real vision call against his subscription**.
Every push runs those gates, so every push quietly bought a read he did not ask for.

**One rule, four files.** `tv_diablo._fixture_root()`: when `TV_HIST` points outside the module's own
tree, the caller has said *"this is not his world"*, so his engine state, his console log, his G5
stats and his subscription meter follow the fixture instead. Same shape as v1867's journal rule.
`test_g5_grok_eyes` was the fifth: it patched `_STATE_FILE` and `_BUDGET_PATH` to a tempdir and
**not `_STATS_PATH`** — a partial sandbox reads as a sandbox.

Measured: `test_roundtrip_sim` spent **1 → 0** real vision calls.

⚠ **The log pollution had already cost a wrong diagnosis** — see the correction on REG-214. That is
why this is filed as a defect and not as tidiness: a diagnostic file a test can write is a
diagnostic that will eventually be believed about the wrong actor.


## REG-219 — "is this console reading for real?" had no answer (FIXED v1870)

`status_payload` carried `stub` as a literal `None` — which reads like *"no"* and means *"nobody
asked"*, the worst of the three answers. Deciding whether his canned session was a SIM press or a
console that had inherited `TV_STUB` cost an hour, a log that tests also write to (REG-218), and a
by-hand inspection of the live process's environment.

The payload now answers `stub` and `readsAreReal` truthfully, guarded in both directions.
[[unknown-stays-unknown]]

## REG-220 — the sets MINI and the uniques MINI got equal time for unequal work (FIXED v1870)

**Konyo:** *"i just did a MINI sets and its too short.. it needs to be longer like the UNIQUES mini"*

They were **already identical** — 75s in `_mini_bounds` and 75s in the console's own
`MINI_FOCUS_SECS` — so the premise as stated could not be the defect. The reason underneath it is
real: a **SETS** row is three lines (name · *Dropped By* · *First Found*) where a **UNIQUES** row is
one, so the same 75 seconds of scrolling covers roughly a third as much ledger. Equal numbers,
unequal work.

And the ceiling was binding either way: the console POSTs only `{focus}` and no duration, so he had
**no way to ask for more**.

- `chronicle-sets` → **150s** default (uniques stays 75).
- The chronicle ceiling → **240s**, so there is headroom above both.
- ⚠ **The durations are now published by the engine** (`/api/mini` → `focusSecs`, `focusMax`).
  `MINI_FOCUS_SECS` in `control_ui.html` was a second copy of the server's table: raising the bound
  on the server alone would have left the button printing *75s* and asking for 75s — a bound lying
  about itself, which is the exact thing `_mini_bounds`' own docstring says it exists to prevent.
  [[copy-drift]]

**Guards:** sets > uniques · headroom above both · the stash focuses untouched (a stash tab is one
screen and 25s photographs it several times over) · the engine publishes what it enforces · the
console prefers the published numbers **before** it renders the buttons.

## REG-221 — the in-game date reached one item, not the wall (FIXED v1871)

v1864 landed the game's own First Found date and dropper, and v1864 showed it in exactly one place:
the *"last found"* bar. Konyo's ask was broader — *"when it was added to the chronicle it should be
storyline synced with the ingame diablo ii"*.

Every found chip now carries it, in the chip's `title`: nothing on the page moves, because the wall
is dense and a second line would cost the density that makes it readable.

**Proven in node, not by reading** — which is how the half-claim was caught: `{at:'', by:'Mephisto'}`
rendered *"found in game · dropped by Mephisto"*, a sentence that stops mid-claim. Each half now
stands alone or not at all, and an unparseable date claims nothing.

**And the whole chain is locked**, with a guard built from his own measured reader output rather
than an invented fixture: two frames × two lanes → `proposal_from_pages` → `gate_verdict`
(corroborated *cross-frame, cross-lane*) → the exact `wouldAdd` row the board receives, carrying
`gameFound {at: "07/18/2026, 02:47", by: "Andariel"}`. A page that printed no date ships **no key
at all** rather than an empty one, so the board can still tell *found on this date* from *found,
date unknown*. v1864's defect was that every link was sound and the chain carried nothing.

## REG-222 — two silent-nothing classes, swept statically across the board (FIXED v1872)

Both fail the same way: the JS is valid, the branch simply never runs, and nothing anywhere says so.

**A. `typeof X !== 'undefined'` on a name that is never declared.** Permanently false. Not
hypothetical here — it is **v1562**, recorded in bible.html's own comment: a Session cockpit KPI tile
*"HAS NEVER RENDERED, NOT ONCE"* because its guard needed `SETS` while the array is `ITEM_SETS`. His
cockpit reported Chronicle 99/99 and Grail 243/403 and said nothing at all about sets, while F·Sets
one click away said 108/135. **Swept: 94 such guards in the board, 0 dead.** The class is closed and
now stays closed.

**B. `window.X && window.X()` on a name assigned nowhere.** Calls nothing, forever. **Swept: 227 call
sites, 85 distinct names, exactly ONE dead** —
`window.renderGrailMeters && window.renderGrailMeters()` in `_inboxAct`, the line that reads as the
backstop refreshing his grail meters after an inbox decision. The real name is `renderGrailProgress`,
published on window at ~18547 and called that way in five other places. Repointed.

It was harmless in practice, because `kaiChronicleAccept` already calls `renderGrailProgress` itself
— **and that is exactly why it survived**. A backstop that is never needed is a backstop nobody
notices is missing, until the path it guards changes. [[the-unjoined-end]]

⚠ **The sweep's first run after the fix reported a dead call to `window.X`** — the placeholder inside
the comment explaining the fix. Comments are stripped first now. His scar file already names this
shape: an explanatory comment blinding a guard that greps for a name.
[[feedback-comments-vs-code]]

These are the JS twins of the AST walk that found MINI dead (v1863): a name inside a branch is only
resolved when that branch runs, so neither class can be caught by parsing or by running the suite.

## REG-223 — my own sweep's comment stripper ate a third of the board (FIXED v1873)

**Found within the hour of shipping v1872**, by pointing a third sweep at the same helper.

`re.sub(r"/\*.*?\*/", " ", src, flags=re.S)` on a 5.6MB mixed HTML/CSS/JS file removed **16.9% of
it and 170 of its 444 `id=` declarations** — because a `/*` inside a JS string or a regex literal
matches forward to the next `*/` anywhere in the file. `js_syntax_gate` says exactly this in its own
docstring — *"a heuristic cannot separate a comment from a string containing nested backticks,
embedded HTML with quotes, and regex literals"* — and I built a guard on one anyway.

It **passed**, on a mangled view. A stripper that deletes a third of the file can only produce false
**negatives**, which is the quiet direction and the reason it went unnoticed.

Bounding the block form (`/\*.{0,4000}?\*/`) loses **0 of 444**: a real comment in this file is long
but not unbounded; a match spanning thousands of characters is a string that happens to contain the
tokens. The stripper now has **its own test**, run before any verdict built on it is believed.
[[feedback-suspect-the-instrument]]

## REG-224 — no element is looked up that nothing creates (SWEPT CLEAN, guarded v1873)

`document.getElementById('x')` with no `id="x"` anywhere returns null, and the customary `if (el)`
turns that into silence. The console records this failure in its own comment: everything after one
line *"wrote into `#hd-shelf-grid`, an element nothing creates"* — a whole block rendering into
nowhere.

**Swept: bible.html looks up 276 distinct ids against 444 declared, 0 missing. control_ui.html: 236
looked up, 0 missing.** Both clean, and now they stay clean.

⚠ **The count was the tell.** The first run reported **135 missing ids in the board** — not a
codebase 135 ways broken, a broken instrument (REG-223). Founding rule 4, which is why the
stripper's own test now sits beside this one.

## REG-225 — the last two writers, and the watchlist becomes the whole tree (FIXED v1874)

With Konyo's console **down** — so nothing else could be blamed — a full 32-gate run still rewrote
two of his files, both of which v1869 was supposed to have covered:

1. **`g5_stats.json`.** v1869 patched `_STATS_PATH` in `TestG5OffByDefault`'s `setUp` and stopped
   there. Every other class in that file — the CLI call, the dual intake receivers, the
   cross-process counter — writes through `_stats_path()`, which reads
   **`os.environ.get("G5_STATS_PATH")` FIRST**. One env var in `setUpModule` covers all of them,
   where a `mock.patch` covers exactly the class that remembered to write it. Third time this
   lesson has arrived tonight: guard the FIXTURE, not the call site.
2. **`.tvd_beacon.json`.** The beacon test stubs `urlopen`, which stops the network half — and the
   beacon *also* persists to `_BEACON_STATE_PATH`, his real fleet-history file. A test telling his
   dashboard that a console checked in.

**Then the gate itself was upgraded.** A named watchlist is a list of the leaks somebody already
found: it named five files while a harness wrote a sixth, and adding that sixth caught two more
writers inside an hour, and a whole-tree hash then caught five nobody had thought to name —
including the subscription meter.

`run_gates` now fingerprints **everything under `tv/`** (skipping `.git`, `__pycache__`, `frames`,
`node_modules`, `.pytest_cache`). The named files remain the hard failure; every other moved file is
**reported by name**, so the next leak is found rather than waited for.

**PROVEN:** with his console down, a full 32-gate run now leaves his whole `tv/` tree
**byte-identical**. That is the first time this has been true.

## REG-226 — `var(--x)` with no fallback on a token nothing defines (SWEPT CLEAN, guarded v1876)

The whole declaration collapses, silently. That is **v1841**, on his own board: `--fs-tiny` was used
and never defined, so the rule carrying it rendered with no font-size at all. `bump_version` already
refuses `var(--x)` in a build note (so the note cannot re-create it); nothing guarded the CSS.

**The distinction that matters.** `var(--x, 10px)` still renders — the fallback is doing the work,
which makes the token decorative rather than broken, and that is a tidiness question and his call.
`var(--x)` with **no** fallback and no definition renders **nothing**. Only the second fails.

**Swept: bible.html 118 tokens used / 114 defined, control_ui.html 92 / 87 — zero hard failures on
either.** The with-fallback ones are recorded rather than fixed: `--gold-antique`, `--q-base` on the
board; `--dim`, `--amber`, `--sg-hue`, `--fg-accent`, `--st-warn` on the console, each falling back
to a literal hex. `--fs-micro` falls back to `var(--fs-2xs)`, which is defined.

⚠ **The instrument needed two corrections before its verdict was worth anything**, both found by
looking at what it accused rather than believing it:
- a token set from JS — `style.setProperty('--claim-h', …)` — **is** defined, just not in CSS. Four
  of five accusations were these.
- `'var(--q-' + rarity + ')'` is a dynamic **construction**, not a reference to a token named
  `--q-`. The fifth was that.

Founding rule 4, twice in one sweep. [[feedback-suspect-the-instrument]]

## REG-227 — 153 selectors set the same property twice, and that is not 153 defects (TOOL, v1877)

`d2r_css_last_rule_wins` is a carved scar: `.hero-title` had four rules and a twin `filterSilver`
cost a whole pane. At equal specificity the **last** declaration wins, so editing the first
occurrence changes nothing and reads as *"the edit did not take"*.

**Measured on bible.html:** 4,682 top-level rules · **201 selectors declared more than once** · **153
that set the same property in more than one block**. `.h-title` has 4 blocks, `.tabs` has 8,
`.hero-pick` has 6.

**That is deliberately NOT a gate.** A file grown over 1,800 versions overrides on purpose, so a
gate would cry wolf 153 times and be turned off. The hazard is a *person editing the wrong copy*,
and the answer to that is a question you can ask in one second:

```
python3 tv/css_who_wins.py .hero-title color
   [0] line 83     .hero-title            color: var(--best)
   [1] line 29448  .hero-title            (does not set color)
   [2] line 29613  h1, h2, h3, .h-title…  (does not set color)
   [3] line 29856  .hero-title            color: var(--ink-kicker) !important
>> color comes from block [3]
```

**It must be right about WHICH LINE or it is worse than nothing.** The first cut concatenated the
style blocks and hunted for a needle, and reported two different rules at the same line. Offsets are
carried through the comment-blanking now (comments are blanked *in place*, same length, so every
offset still lands), and a test asserts every reported line really declares that selector — all four
above verified by reading the file. Only `<style>` bodies are scanned, so a selector-shaped string in
JS cannot become a rule, and only depth-1 rules: one inside `@media` is a different cascade question
and answering it here would be worse than silence.

## REG-228 — `newlyDated` was computed twice and read nowhere (WRONG — CORRECTED v1880)

⚠ **THIS ENTRY WAS MINE AND IT WAS WRONG.** `newlyDated` was already consumed: `control_app` prints
it at **both** sweep sites, **live**, while the reel is still being read. His own sweep printed it
forty minutes after I shipped the "fix":

```
🆕 1 find(s) newer than anything read before: Bul-Kathos' Tribal Guardian (08/20/2026, 02:59)
```

— from the engine, not from the line v1878 added. **The duplicate print is removed (v1880)**, and
the guards now assert the joint that was always real.

**Why the grep missed it:** I searched for the field name `newlyDated`; the consumer works from the
local `_fresh`, assigned before the field is built. Searching a name and concluding absence is the
exact failure `source-reading-guard` exists for, applied to my own field.
[[source-reading-guard]] [[feedback-silence-is-not-evidence]]

What survives, and it is worth keeping: the field really is the **only** thing that separates *"he
found this since the last sweep"* from *"nobody had read this page before"*, and the guards now cover
both ends — the engine prints it while the sweep runs **and** carries it into the stored result, so a
later reader cannot silently get nothing.

**The original (incorrect) claim, kept so the record shows what happened:** Produced in `control_app`
at two sites since **v1846**; consumed at **zero** places in the console,
the board or the sweep script. Plumbing built at both ends and never joined — mine, and found by
grepping my own field name. [[plumbing-with-no-tap]]

It is the only thing that can separate **"he found this since the last sweep"** from **"nobody had
read this page before"**, which are identical in every other number a sweep prints: both arrive as a
name that was not in the ledger. And the dates come from the **game's own First Found rows** (v1864),
so it is his history talking, not the reader's clock.

The hand sweep now prints it — `🆕 N find(s) NEWER than anything read before this sweep: …` — and
only when there are any: a line that always prints is one he stops reading. Guarded on **both** ends
of the joint, because if the field stops being emitted the reader goes quiet and looks exactly like
*"nothing new"* forever.

## REG-229 — the game's find DATE and the find it dates could have drifted apart (guarded v1879)

`d2r_gameFound` (v1864) holds the game's First Found date and dropper per item; `d2r_foundLog` holds
when the **board** learned of the same find. They describe **one event from two sides**, so they must
live in the same scope — and `_LP_FORKED` decides that: a forked key is per-account, an unforked one
is shared.

**Measured, not assumed:** neither is forked, which matches the ladder doctrine — *"everything
NON-LADDER syncs to main; a profile toggle must never change a count"*. A grail is what he has **ever
found**, so it is account-wide. `d2r_owned` **is** forked, because what he **holds** is per-profile.
That split is right.

The guard asserts the **pair**, not either value: if the log is ever forked, the dates follow it
instead of quietly splitting from the finds they date. Two companions check the other half — the
physical vault must stay per-profile, and the store must go through `LSR` at all, since the fork only
applies to keys that use the wrapper. [[d2r-ladder-doctrine]]

## REG-230 — the vault-gate test failed on a busy OCR lane, twice (FIXED v1880)

`TestPrepTabChromeIsNotDead.test_a_real_stash_frame_is_recognised_and_gameplay_is_not` went red
inside two long combined runs tonight and passed alone seconds later, both times.

**REG-213 had already diagnosed why** — the tab-chrome OCR came back with no lines, so
`stash_screen_open` refused a genuine stash frame — and v1864 gave the engine a way to tell the two
apart (`gate_hearing() -> (silent, heard)`). **The test went on asserting the verdict anyway.**

It now reads the counters around its own probe: if that probe was **silent**, the reader could not
run, so the outcome is a **skip with the reason** rather than a failure blamed on the gate. Run three
times in a row and inside the full combined suite: green.

A flaky test is a test he learns to ignore, which is the same defect as a gate that never goes red.
[[feedback-silence-is-not-evidence]] [[feedback-blind-fixture-green-gate]]

## Sweep result — his Set-pieces reel, read 2026-08-20 23:5x

22 frames quoted, **40 minutes**, and the numbers are the interesting part:

```
⏸ 5 page(s) refused by the throttle or the budget — NOT read, and none of their 3 looks spent
🆕 1 find(s) newer than anything read before: Bul-Kathos' Tribal Guardian (08/20/2026, 02:59)
   read 17 page(s) · 0 unique name(s) · 25 set name(s) · refused 5 · 5 read as not-found
   fold: 53 name(s) corrected (Atma's Scarab → Atma’s Scarab, Battlecage → Rattlecage) · 26 retired
```

Three of tonight's ships proved themselves on his own footage in that one run:

- **v1861** — five pages were refused by the throttle and **kept all three of their looks**. Before
  that fix they would have burned one each, and three such sweeps would have retired pages the
  reader never opened.
- **v1864** — `Bul-Kathos' Tribal Guardian (08/20/2026, 02:59)` is the **game's own First Found**
  stamp, not the reader's clock. He found it today at 02:59.
- **v1878/v1880** — the new-finds line is the engine's, printed live while the reel was still being
  read (which is how the v1878 claim was caught and corrected).

⚠ **THE NUMBERS BELOW WERE READ MID-SWEEP AND ARE WRONG. See REG-244 for the real ones** — 11 of
the 13 cleared, not 6, and `wouldAdd` sets reached **36**, not 28. Kept here as written, because a
record that quietly resolves to whatever turned out right teaches nothing.

**Nothing was applied.** The proposal is what changed, and by exactly how much:

| | |
|---|---|
| **6 of the 13 held pieces cleared** | Arcanna's Flesh · Arcanna's Sign · Hsarus' Iron Heel · Immortal King's Forge · Natalya's Shadow · Natalya's Soul |
| **7 still held** | Arcanna's Deathwand · Arcanna's Head · Dangoon's Teaching · Iratha's Collar · Iratha's Cord · Iratha's Cuff · Milabrega's Diadem |
| **3 newly surfaced, held on one witness** | Bul-Kathos' Sacred Charge · Bul-Kathos' Tribal Guardian · **Natalya's Totem** |
| **`wouldAdd` sets** | **21 → 28** |

⚠ **`Natalya's Totem` is the DAILY PICK on his own F·Sets screen** — *"the LAST piece of Natalya's
Odium"*. It now has one witness (cross-frame). One more legible pass over that row grounds it and
completes the set.

The seven that stayed held need the same thing they needed before: one more corroborating sighting.
Two of them (Arcanna's Deathwand, Arcanna's Head) are held because **the reader itself was unsure**
(0.50 against a 0.55 floor) — those rows are hard to read, not merely unseen, so a slower pass over
that part of the ledger is what they want.

## REG-231 — the TZ tracker looked stuck because nothing moved (FIXED v1881)

**Konyo:** *"the TZ TRACKER when im on it i want it to be refreshed its stuck and not updating"*

It was not frozen. It was **silent**, and **late at the only moment that matters**:

- the panel refetched on a **flat 120s interval**, so between polls nothing on screen changed — a
  working tracker and a dead one look identical to a person watching one;
- that poll is **unaligned to the rotation**, which turns on the hour and the half hour, so he could
  sit up to two minutes reading the zone that had just ended;
- ⚠ a comment fifty lines above claimed *"the board already refetches 6s after the turn"*. **It did
  not, and never did** — `_tzTimer` was the only timer in the file. A stale claim about a safeguard
  is worse than no claim: it is why nobody went looking. [[label-outlived-referent]]

Three things now, one per symptom, all hanging off a **single one-second interval** so there is one
timer to reason about and one place it can be cleared:

1. **A live countdown** to the next `:00` / `:30`, turning green inside the last two minutes. The
   page is visibly alive and he can see the turn coming.
2. **A turn-aligned chase** — refetch at the boundary, then again at **+8s, +25s and +60s**, because
   the upstream feed lags its own rotation (the *"turning over"* state this file already renders is
   exactly that lag).
3. **The 120s poll stays** as the floor for everything else.

The boundary maths is run in **node** against fixed clocks — both one-second edges and the midnight
rollover — because an off-by-one there fires the chase on the wrong side of the turn and he reads the
old zone for another half hour: `00:05→1500s · 00:29:59→1s · 00:30→1800s · 23:59:59→1s`.

⚠ **The stale-claim guard failed on its own documentation.** It asserted the phrase was absent, and
v1881's note about removing it quotes the phrase — so the guard found the record of the fix and
called it the defect. **Third time tonight** an explanatory comment blinded a guard that greps for a
name, and this one was written sixty seconds after the last. A string cannot tell a claim from its
retraction, so the check is now about what surrounds it: every occurrence must sit beside a
retraction. Proven to still flag the claim standing alone. [[feedback-comments-vs-code]]

## REG-232 — the dock's TZ countdown was up to 30 minutes wrong, on every tab (FIXED v1882)

Found while **visually verifying** the tracker fix (REG-231) — the render showed *two* countdowns,
and only their agreement in that moment hid the defect.

The bottom-dock badge computed `remMin = 59 - m`: it counts to the next **`:00` only**. So for the
whole first half of every hour it read **up to thirty minutes too long**, and it **never once fired
at the `:30` turn**. It sits in the dock on every tab — the most-seen clock on the site — and it had
said *"TZ rotates each hour at :00 IDT"* for ~1,840 versions while the tracker page said *"on the
hour and the half hour"*.

**Settled from the feed's own history**, not from either surface's opinion — `bull-4-u.com/api/tz`,
ten consecutive slots:

```
00:30 · 21:30 · 21:00 · 20:30 · 20:00 · 19:30 · 19:00 · 18:30 · 18:00 · 17:30
gaps (min): [30, 30, 30, 30, 30, 30, 30, 30, 30, 30]
```

The tracker was right; the badge was wrong. ⚠ **They agreed only when sampled in the second half of
an hour**, where `:30` and `:00` coincide — and the render that found it happened at 00:34, showing
25:28 and 25:29. That is why it survived. [[feedback-contradiction-is-the-finding]]

Both go through **one** definition now (`window._tzTurnBoundary`), so a cadence change cannot move
one surface and leave the other. Measured after: `00:05→1500s · 00:29:59→1s · 00:31→1740s ·
00:59:59→1s` — the old rule gave **3300s** at 00:05.

**Verified on the pixels**, per the standing order: both clocks rendered at 1440×1000 in headless
Chrome read **21:32**, identical.

## REG-233 — an `except:` that fell back to his own directory (FIXED v1883)

`_g5_stats_root()` asked `tv_diablo` for the fixture root and, on **any** failure, returned its own
directory — his live `tv/`. The import genuinely can fail there: a control app spawned by a harness
imports the two modules in an order this one does not control.

Measured with his console down, after v1874: **six** harnesses still rewrote his live `g5_stats.json`
— `test_console_fleet`, `robot_smoke`, `test_roundtrip_sim`, `test_button_matrix`, `test_vault_lane`,
`test_inbox_engine` — every one of them with `TV_HIST` correctly sandboxed.

**An `except: return his_directory` is a fallback that fails toward the thing being protected.** The
rule is six lines; it is inlined now rather than surrendered. Five of the six went clean immediately.

The sixth, `test_console_fleet`, imports `control_app` **in-process** — and it already isolates the
beacon with real care, which is exactly the point: *a harness can be scrupulous about the leak it
knows about and still have another*. It gets `G5_STATS_PATH`, the override g5 reads first.

**A full 32-gate run leaves his whole `tv/` tree byte-identical again.**

## REG-234 — the vault routing had never been driven end to end, at any size (CLOSED v1884)

**Konyo:** *"vault manager? and items being routed correctly? you simulated every single item that
would be found and made sure it gets muled or thrown out properly? and you fed it 300-500 items at
once to see how it reacted to the traffic?"*

**The honest answer was no**, and the gap was precise. `test_vault_retro.py` has 21 good tests —
merge-max never subtracts, order cannot change the answer, lanes do not bleed, the throw bar is
strictly higher. **Every one of them calls `gate()` or `merge_vault()` directly**, with three or four
hand-made rows. **Not one calls `sweep()`.** So the routing *inside* the sweep — surface → lane per
item, throw flags collected per key, the two bars applied to real piles — had never been executed at
all.

`tv/test_vault_traffic.py` (16 tests, now gate #33) drives the real `sweep()` over real reel
directories in a tempdir. Measured:

| | |
|---|---|
| his whole set roster, 2 sessions | **169 in → 169 owned, 0 dropped**, 0.06s |
| the same, 1 session | **0 owned**, 169 unsure — law 2 holds at scale |
| every surface × every item | `stash`/`runes`/`gems`/`materials` → **stash** · `inventory` → **inventory** · `equipment` → **equipment** |
| throw-out, 2 recordings | **0 suggested, 1 held** |
| throw-out, 3 recordings | **1 suggested**, `suggestion:true`, never automatic |
| **500 items at once** | **500 owned, 0 dropped, 0.00s** |
| 500 throw flags × 3 recordings | **500 verdicts** |
| 1,000 rows of one item | **1 row**, count not inflated |
| one item alone vs in a crowd of 500 | identical lane and count |

**Seen red, three ways**, because a battery that passes first time proves nothing on its own: route
`inventory` into the stash lane → the routing test fails; drop the keep bar to one witness → the
one-session test fails; drop the throw bar to two recordings → the throw test fails. Restored: clean.

⚠ **The first run of the harness proved the harness wrong, not the code.** It gave every frame a
different signature and got 0 of 135 items out — and the sweep said exactly why: *"2 reel(s) held no
screen still long enough to be worth reading — that is footage of moving, not of looking at a
stash."* A still run is frames that look the **same**. [[feedback-suspect-the-instrument]]

**No defect was found in the routing.** That is the result, and it is worth stating plainly rather
than dressing up: the laws hold at 1 item and at 500, and now there is something that would notice
if they stopped.

## REG-235 — a misread name became a permanent ghost in his vault (FIXED v1885)

Found by taking REG-234's battery one step further, on his own data: the **53 name corrections his
chronicle sweep made on 2026-08-20**, pushed at the **vault** lane instead.

```
pushed   Atma's Scarab · Battlecage · Saracen's Chance
owned    Atma's Scarab · Battlecage · Saracen's Chance      (verbatim)
both spellings together -> SIX owned rows for THREE real items
```

**The vault sweep had no name fold at all** — 0 occurrences of `fold`, `roster` or `resolve` in its
198 lines — while the chronicle sweep has had one for versions. And **merge-max never subtracts**, so
every one of those rows is permanent. The two-witness keep bar does not save it either: a
*systematic* misread is exactly the kind that repeats, as this repo's own law-3 note says —
*"reading 'Ral' as 'Ort' a second time is exactly as likely as the first time."*

**Fixed: an EXACT fold, and only exact.** `Atma's Scarab` and `Saracen's Chance` normalise onto their
curly-quoted roster names exactly, so the apostrophe class — the common one, and the one his own
sweep hit — is corrected. Six rows became three.

⚠ **NEAR MATCHES ARE REFUSED, and that is a defect my own fold shipped for one minute before this
battery caught it.** `canonical()` near-matched `"Isenhart's Armory (set)"` — a **set aggregate** —
onto `"Isenhart's Parry (shield)"`, a specific piece. Not a correction: **a find he never made**,
which is exactly what the resolver's own comment warns about.

The chronicle lane can afford near matches because a Chronicle page is a **closed list** of grail
names — every row *is* a roster item. **A stash is an open universe**: runes, gems, materials, bases,
charms, jewels, set aggregates, quest items. "Nearest roster entry" there is a guess about which of
two different things he owns.

**So `Battlecage → Rattlecage` is deliberately NOT fixed in this lane.** An uncorrected row he can
see beats a confident wrong attribution he cannot. Stated here rather than left as a surprise.

⚠ And a missing resolver now **says so** — *"gating on RAW reader names, so a misread can become a
permanent row"* — instead of silently reverting to the old behaviour.

**22 tests**, including the safety half: nine ordinary stash things (`Ral Rune`, `Perfect Ruby`,
`Cracked Sash`, `Chipped Skull`, `Tome of Town Portal`, `Small Charm`, `Jewel`, `Key of Terror`,
`Wirt's Leg`) must come out **exactly as read**.


## REG-236 — my own test was a time bomb, and his pre-push gate caught it going off (FIXED v1886)

`test_a_millisecond_entry_is_rescaled_not_trusted` (v1868) pinned the real value from his budget
file — `1787177667153.0` — and asserted it survived the 24-hour window. That value rescales to
**08-20 01:14**, so the test passed for a day and then failed **mid-push at 01:16 the next night,
exactly 24.0 hours after the moment it described**. Measured at the moment of failure: age 24.0 h
against a 24 h window, crossed **two minutes** earlier.

**A fixture whose verdict depends on how long ago it was written is not a fixture.** The behaviour
under test has nothing to do with the wall clock, so neither does the test now: the millisecond value
is built **relative to `now`**. A mirror was added at the same time — a millisecond stamp three days
old must still age out, or "rescale" would quietly mean "resurrect".

⚠ **The refusal is the story.** `git push` exited 1 and the ref never moved; the version was
committed locally and reported nowhere until this was fixed. That is the gate working exactly as
designed, on a test I wrote about timestamp units being confused — undone by the passage of time.

**Swept the class:** every other absolute epoch literal in tonight's tests is a reel id or a frame
name — opaque strings with no window semantics. The one reel fixture that *does* care about age
(`_make_reel`) ages its files with `os.utime` relative to now, which is the right shape.
[[feedback-blind-fixture-green-gate]] [[stale-reading]]

## REG-237 — mixed panels in one reel, and the board's vault apply, both driven for the first time (v1887)

Closing the two gaps I named after REG-234.

**Mixed panels in one reel.** Every earlier test used one surface per sweep; he does not park on one
panel. Three still-runs in one reel — Personal stash → Runes tab → Inventory — now drive the sweep:
6 classifies, 6 page reads, and each item lands in the lane of the panel it was seen on
(`Shako`→stash, `Ral Rune`→stash/rune/count 3, `Tome of Town Portal`→inventory). The same item on two
panels stays **two rows**, and a gameplay panel between them **costs nothing** — 4 pages read, not 6.
26 tests in the battery now.

**The board's `vaultAccumApply`, in a real page.** It lives inside an IIFE no unit test can reach, so
it was driven under headless Chrome on `:9224`. All four rules it states about itself hold:

1. **merge-max** — a read of 3 left a stored 9 alone; a read of 14 raised it
2. **route by kind** — gem→gems, material→materials, `item`→grail, unknown kind→**skipped by name**
3. **throw-outs are never written** — 2 suggestions acknowledged, all three stores byte-identical
4. **an empty payload refuses** — `ok:false, "the payload carried no items"`

Traffic: **500 tally items in 242 ms**, every one written. A throw-out naming something he owns left
it owned. Garbage counts (`-3`, `'lots'`) never lowered anything.

**One real finding: `count: 0` was reported as "no readable count".** Zero is a measurement — *"I
looked at that shelf and there are none"* — and null is an absence. Both correctly write nothing, so
the store was always safe, but the receipt attached a wrong reason to a right action. His own
doctrine: *"`0` means 'we measured, it was zero'; `None` means 'nobody looked'. Collapsing them is a
lie with no author."* Now: `read as none — nothing to raise` vs `no readable count`.

⚠ **Three instrument errors in this pass, none of them in his code**, each caught by looking rather
than believing: a 501st rune that was residue from my own earlier probe (merge-max taking the max of
memory and localStorage — the designed behaviour); an edit that "did not take" because my harness
matched the *first* `bible.html` tab and picked a stale one; and before that, the still-run signature
inverted. **The count is the tell.** [[feedback-suspect-the-instrument]]

## REG-238 — the chronicle lane got the battery the vault got (v1888)

The symmetric half of REG-234. `test_chronicle_retro.py` has **162 tests** and they are thorough
about the laws — a verdict explains itself either way, every reel folds into one proposal, a
scroll's later pages are read and not just the first. **Every one of them uses a handful of
hand-made names, and nothing tested volume.**

`tv/test_chronicle_traffic.py` (11 tests, gate #34) drives the **whole universe**: 398 uniques + 135
set pieces = **533 names**.

| | |
|---|---|
| every unique, 2 frames × 2 lanes | **398 → 398 in the proposal → 398 ground** |
| every set piece | **135 → 135 ground** |
| one lane, one frame | **0 ground** — the corroboration law at 398 names, not three |
| every held verdict | still carries a `why` |
| the whole universe in one proposal | lossless, well under the time bound |
| a page read **200 times** | still one row per name |
| **12 reels, shuffled** | `merge_proposals` gives the same answer in any order, and loses nothing |

**And the ambiguous fold his own roster contains** — found by trying *every single-letter deletion of
every roster key*, not by imagining one:

```
probe 'stormspie'  ->  Stormspire (0.947)  vs  Stormspike (0.947)
```

Two **real** grail items, tied to three decimals. A reader dropping one letter of `Stormspike` would
otherwise be recorded as finding `Stormspire` — a find he never made, kept forever by merge-max.
`canonical()` returns **None**, and a standing check now sweeps all 398 keys × every deletion to
prove no ambiguous probe ever folds onto a name.

**Seen red**: drop the witness bar to zero and the one-lane test fails; set the ambiguity gap to zero
and both fold tests fail. ⚠ My first sabotage attempt did **not** bite — `gate_verdict`'s
`min_witnesses` default is bound at def time, so patching the module global does nothing. That was
the instrument again, and the fix was to patch the function.

## REG-239 — the apply receipt said five, the grail meter moved four (FIXED v1889)

Driving `window.chronicleApply` in a real page — headless Chrome, because it lives in a closure no
unit test can reach — applying **Shako · Stormspire · Stormspike · Titan’s Revenge · Herald of
Zakarum** reported `uniques: 5` and moved the counter by **4**.

One at a time named the odd one out:

```
Shako   reported 1 · delta 0 · not in d2r_foundLog at all · found in d2r_owned
```

**"Shako" is the community nickname for Harlequin Crest**, so the board has no such unique.
`toggleOwned` routes by what the board *knows*: a grail unique lands in the **found ledger**, a name
it does not recognise lands in the **physical vault**. That split is deliberate — `_UNI_EXTRA` exists
precisely so real uniques with no card stop falling into the vault — but **the receipt did not know
about it** and counted both as applied uniques. A number under a word naming a different quantity.

The reader-side fold does not save it either: `canonical("Shako")` is `None`.

**The ledger is the arbiter, not the intent**, so the receipt asks it. After: `uniques: 4`,
`vaulted: ["Shako"]`, delta **4** — receipt and meter agree.

⚠ **An unreadable ledger does not invent a demotion.** If the store cannot be read, *"he did not find
it"* is a claim we have not earned, so the fallback is the old behaviour — counted as a unique — not
a fabricated vault row. Guarded explicitly, because the tempting `catch` is the wrong way round.

## REG-240 — a name that is not a set piece was written into his found ledger (FIXED v1890)

v1889's defect, in a worse shape, found by sweeping the class it belongs to: *a receipt computed from
intent rather than from the store.*

**Measured in a real page, on a cleared store.** Applying three real pieces plus `IK Helm` and
`Totally Not A Set Piece`:

```
receipt   sets: 5          meter  +3          d2r_foundLog: all FIVE
```

In the uniques case an unrecognised name at least landed in the vault. **Here it lands in the found
ledger and stays**, because nothing ever un-finds.

**After:** `sets: 3` · `unknown: ["IK Helm", "Totally Not A Set Piece"]` · meter **+3** · the ledger
holds only the three real pieces.

The membership question is asked **before** the write, against the board's own piece universe
(`__allSets` — `ITEM_SETS` plus the two EXTRA tables), memoised because a 500-name payload would
otherwise walk that universe 500 times, and published on `window` so a guard can reach it (the
REG-083/REG-087 shape: a helper that only *looks* available from outside its IIFE).

⚠ **An unreadable — or empty — roster does not invent a refusal.** *"This is not a set piece"* is a
claim that needs the roster to make; without it the old behaviour stands. The tempting `catch` is the
wrong way round here, exactly as it was in REG-239, and both directions are guarded.

**The sweep that found it:** a regex for *a write call followed immediately by a `.push` into a
result array* over the whole board — one live hit, this one.

## REG-241 — the undo left the game's find date behind (FIXED v1891)

The undo bar promises *"the ledger entry is erased and it returns to the hunt"*, and v1864's
`d2r_gameFound` survived it. Measured in a real page, the full round trip:

```
tick   have +1 · ledger row + stamp "Jul 18, 2026 · 02:47" · date present
undo   have  0 · ledger row gone                          · DATE STILL THERE   ← the defect
now    have  0 · ledger row gone                          · date gone
redo   have +1 · date restored exactly: 07/18/2026, 02:47 · Andariel
```

**Why it matters rather than being tidy.** The reason he un-ticks is usually that the **read was
wrong**, so the date belongs to a different item. Left behind, it re-attaches the moment he ticks
that name by hand later — and v1871 prints it on the chip: *"⚔ found in game Jul 18, 2026 ·
Andariel"*, a claim sourced from a read he threw away. If he genuinely found it, the next read
re-establishes it.

A joint I opened in v1864 and did not finish. The undo stashes the date on `_FORGE_REDO` first, so
the round trip loses nothing, and it touches **only** the name being undone.

⚠ **And it broke two of my own v1871 guards, for the fourth-in-a-night reason.** They anchored on the
bare name `window._gameFoundSet`; v1891 added a **call** to it inside `_forgeRedo`, which sits
earlier in the file, so the anchor hit the call and truncated the extracted slice to nothing. Both
now anchor on the **definition** (`window._gameFoundSet = function`). An anchor that matches the
wrong occurrence is the exact failure `source-reading-guard` is carved about.

## REG-242 — four guards died on one shape in one night, so the shape is now pinned (v1892)

Not a defect in his code: a defect in **mine**, four times over, all the same family — a source guard
that fails on its own reach rather than on the thing it checks.

```
v1866  body = ui[i:i + 900]        a later comment pushed the checked line past the window
v1872  window.X in a comment       my own explanatory placeholder became the defect it hunted
v1873  /\*.*?\*/ unbounded         ate 16.9% of a 5.6MB file and 170 of its 444 id= declarations
v1891  find("window._gameFoundSet")  matched a new CALL earlier in the file, not the definition
```

**Every one produced an empty or truncated slice**, and an empty slice does not announce itself:
`assertIn` fails somewhere confusing and **`assertNotIn` passes**.

Two things, and deliberately not a third:

1. **`_between(case, src, start, end, min_len)`** — the safe way to take a slice. It refuses if the
   start anchor is missing, if the end anchor is not *after* it, or if what comes back is too small
   to be the thing you meant. Seen red in all three directions.
2. **A ratchet.** `test_control.py` currently has **26** byte-counted slices (`src[i:i + N]`). A test
   pins that number so the class **cannot grow** and names `_between()` as the way to write the next
   guard. ⚠ The number is a **debt, not a target** — lower it as sites are converted, never raise it.

**Deliberately NOT done: rewriting all 26 now.** They are the things that catch regressions, at
3am, in one sweep, with no way to tell a converted-and-still-correct guard from a
converted-and-quietly-broken one. The ratchet stops the bleeding; the conversion is ordinary work
for a normal hour.

⚠ And installing it broke the file once: my first attempt's `%%`-escaped template got written with a
live `""" % (25,)` on the end of a docstring, and the module stopped importing. Caught by the very
next run, removed whole rather than patched.

## REG-243 — the safe helper had no users, so it got three (v1893)

`_between()` shipped in v1892 with nothing calling it but its own self-test — plumbing with no tap,
by the definition I have been using all night. Three of the longest byte-windows are converted, and
the ratchet drops **26 → 24**.

**The conversion immediately caught one.** `def _classify_one(` → `def _reader(` looked like the
obvious pair, and **`def _reader(` does not appear after `_classify_one` at all**. `_between`
refused; the old `src[i:i + 3600]` would have measured 3,600 bytes of whatever followed and reported
a pass. The real end of that function is the line that wraps it —
`_classify = _cr.classifier(...)`.

That is the helper doing precisely the job it was written for, on its first real use.

**Seen red in place**, not merely assumed: sabotaging `chronicle_template` *inside* the slice fails
the guard; restoring it passes. ⚠ My first sabotage attempt replaced the first occurrence in the
whole file — a comment near the top — and nothing happened. The instrument again, and the fix was to
sabotage inside the slice the guard actually reads.

| | |
|---|---|
| `board_ownership` | 2600 bytes → bounded by the next `def ` |
| the vault `_reader` | 900 bytes → bounded by `prop = _vr.sweep(` |
| the chronicle `_classify_one` | 3600 bytes → bounded by `_classify = _cr.classifier(` |


## REG-244 — I read the result while the sweep that owns it was still running (CORRECTED v1894)

I reported *"6 of the 13 held pieces cleared, `wouldAdd` sets 21 → 28"*. **Both numbers were from
the PREVIOUS proposal.** `chron_last_result.json` was written at **00:47:02**; my read was minutes
earlier, while the sweep was still in its fold-and-gate phase.

**The real result:**

| | |
|---|---|
| of the 13 held before that reel | **11 CLEARED**, 2 still held |
| cleared | Arcanna's Deathwand · Arcanna's Flesh · Arcanna's Head · Arcanna's Sign · Hsarus' Iron Heel · Immortal King's Forge · Iratha's Collar · Iratha's Cord · Iratha's Cuff · Natalya's Shadow · Natalya's Soul |
| still held | **Dangoon's Teaching** · **Milabrega's Diadem** |
| `wouldAdd` | **266 uniques · 36 sets** |
| **every one of the 36 set rows carries the game's own date** | e.g. `Arcanna's Head — 05/14/2026, 20:17 · The Cow King` |

Including the two — Arcanna's Deathwand and Arcanna's Head — that had been held because *"the reader
itself was unsure"*. The second pass corroborated them.

**The durable fix, because the surface had the same blindness I did.** The engine has stamped every
result `savedTs` for versions and **nothing rendered it**: the console showed a proposal with no age
at all, so one made an hour ago and one made last week looked identical and he would act on both the
same way. The state now publishes `resultTs` and `resultFromDisk`, and the panel says *"this proposal
was made 12 min ago · restored from disk, not from this session"*, turning amber past a day.
[[stale-reading]]

⚠ **And the type floor caught the new line the moment it existed.** `font-size: 11px` is under his
declared ~13px floor; `TestV1504TypeFloor` failed, and it now uses `--fs-2xs`. Three surfaces had
slipped under that floor before — the gate exists so a fourth does not.

## REG-245 — the vault proposal did not survive a restart (FIXED v1895)

`_VAULT_JOB` was **in-memory only**. He sweeps his vault, closes the console, and the proposal is
gone — **while the reads that paid for it are spent.** The chronicle solved this in v1763 for exactly
that reason: *"a fresh process reports the LAST sweep, not 'idle, nothing here'."*

Now it persists, mirroring `_chron_result_save/load` deliberately — atomic `tmp` + `os.replace`, and
**no `default=str`** (v1800: it turns an unserializable value into its REPR and reloads it as a
**name**, silently corrupting the ledger instead of raising).

**Proven end to end in an isolated tree, with his own confirmed untouched by the same run:**

```
save    -> the fixture's own vault_last_result.json, not his
reload  -> owned rows restored into a fresh, empty job
state   -> resultFromDisk true, resultTs set
his tv/ -> no vault_last_result.json; chronicle result byte-identical
```

**The age matters more here than anywhere**, and that is the reason to ship it in the same breath: a
proposal that now *outlives the session* must say how old it is, or one made last week reads as one
made just now. Same line as the chronicle got in v1894 — *"this vault proposal was made 3d ago ·
restored from disk, not from this session"*, amber past a day. [[stale-reading]]

⚠ **The new live file joined the gate's watchlist and `.gitignore` on day one** — new live state that
nothing watches is precisely how REG-215, REG-216 and REG-218 each survived.

## REG-246 — the held pile reaches his inbox and stays held (VERIFIED, no defect, v1896)

v1759 built this path after five names the readers genuinely saw were *"silently discarded on the
server: they never reached the board, never reached the inbox, and he never saw them."* It had never
been driven with a real held pile.

**Measured in a real page against the 41 names his own sweep is currently holding:**

```
held in                 41
queued                  41   (skipped 0 · conflicts 0 · autoAccepted 0 · autoDismissed 0)
rows in the inbox       41, each carrying its reason as `triageWhy`
                        e.g. "only 1 independent witness (cross-frame) — needs 2"
auto-ticked             0
after THREE sync passes  still 41 rows, still 0 ticked
```

**The three passes are the point.** A defect that needs a second triage to bite would hide from one,
and v1759's own note says what is at stake: *"the board's triage sees a well-formed grail name and
AUTO-TICKS it, which quietly undoes the gate that just refused to ground it."*

**No defect found**, and that is the result rather than a disappointment — this is where his last two
set pieces (**Dangoon's Teaching**, **Milabrega's Diadem**) are waiting, with the reason each is
waiting attached. The contract the run exercised is now pinned: held names go through the one door,
carrying `gateHeld` and carrying **why**.

## REG-247 — the isolation rule was a coin flip on his Windows machine (FIXED v1897)

Tonight's isolation work compared paths with `h.startswith(root + os.sep)`, written **four times**.
That is a coin flip on two of his three surfaces:

- **Windows** — the same directory arrives as `C:\Users\…` from one call and `c:\users\…` from
  another. `startswith` says no, and the rule silently decides a **fixture is his real tree** — the
  exact class this whole arc closed, arriving on the machine the suite cannot run on.
- **His Mac, the mirror** — APFS is case-insensitive by default, so the **uppercased** spelling of
  `tv/frames/hist` *is* the same directory. `normcase` alone calls it different, so "isolated"
  writes would land in his real folder under another spelling. **Measured before the fix: exactly
  that.**

**So the filesystem decides when it can.** `os.path.samefile` compares inodes and is right on both;
it also walks up the ancestors, so a nested path is answered with the same authority. `normcase` is
the fallback only for a directory that does not exist yet — a fixture about to be created, where
there is nothing to stat.

**One definition** (`tv_diablo._under`), used by all four sites. Five cases guarded: no override ·
his real hist · **an uppercased spelling of it** · a real fixture · a directory that does not exist
yet.

⚠ **And the guard failed on its own documentation — the fifth time tonight.** `_under`'s docstring
quotes the shape it replaced, so `assertNotIn("h.startswith(root + os.sep)")` found the record of the
fix. It asserts the **executable** form now (`…)):`), which the prose does not contain.

## REG-248 — the art route's 403 guard, on his Windows machine (FIXED v1898)

`_serve_art` refuses anything outside `ART_DIR` with a `startswith` prefix test. On Windows a case
difference between the resolved target and `ART_DIR` makes that say **no**, and the traversal guard
**fails closed on his own art** — a 403 on every picture, on the machine the suite cannot run on.

It uses `tv_diablo._under` now: resolve both sides, ask the filesystem (inode identity), fall back
to a case-normalised prefix. **Exactly as strict as before** — normalising both sides identically
cannot admit a path outside `ART_DIR`. Verified:

```
boss_andariel.png · hd/x.png · ./boss_andariel.png     ALLOWED
../control_app.py · ../../etc/passwd
..%2f..%2fetc%2fpasswd · ../../../../../../etc/hosts   REFUSED
```

⚠ **What this does NOT fix, recorded because I nearly claimed the opposite.** I wrote a comment
saying `ART_DIR` was un-resolved, so any symlink in the repo path would make the two incomparable
and 403 everything. **`ART_DIR` is already `os.path.realpath`'d at its definition** (line 98). That
half of the hazard does not exist in this repo and never did — I checked the line only after writing
the claim, and corrected it before shipping.

A comment that invents the defect it fixes is the same lie as a receipt that reports the wrong
number; it just takes longer to catch.

## REG-249 — a result save that could not write, and a vault save that never said so (FIXED v1899)

Found **in the suite's own output**, which had been carrying it for a while:

```
⚠ chronicle result NOT persisted ([Errno 2] No such file or directory:
  '/var/folders/.../nodeadlock.json.tmp') — this sweep will not survive a restart
```

repeated on every run. A result path whose **directory does not exist** means the sweep is not
persisted at all. Both saves had that shape; both create their parent now, and the noise is gone
(**grep count 0** after the fix).

⚠ **And my own vault save (v1895) swallowed the failure entirely** — `except Exception: pass`. The
chronicle's has said *"this sweep will not survive a restart"* for versions. Mine was written **one
ship after** I fixed the same class in his code.

That silence undoes v1895 exactly: the reads that paid for the proposal are spent, he closes the
console, and there is **nothing and no reason**. It speaks now, and a guard asserts neither save
swallows its error. [[feedback-silence-is-not-evidence]]

**Also checked and clean, so it is not re-checked later:** the suites are **order-independent**
(reversed order: 1,326 green) and **every suite passes alone** — nine for nine. The 7 skips are all
documented and legitimate: four need a browser that answers `--dump-dom` over http on his Mac (they
run on CI), one is PowerShell-only, two are permanently skipped fixtures whose decisions are covered
by other tests.

## REG-250 — two writers for one file, and the third occurrence of one class (FIXED v1900)

`chron_autoread.json` had **two writers** — the visit mark and the reel mark — and that fact has
un-marked the file **twice**:

- **v1762**: the visit writer knew only `done` and rewrote the file **without `reels`**, so the
  watchdog re-walked the whole backlog and **paid for it again**.
- **v1784**: the same shape with `skipped`, so a reel retired for a named reason read as never-swept.

Both were fixed by teaching one writer about one more key, which leaves the **next** key exactly as
fragile. Three occurrences of one class is where you stop fixing instances: there is **one writer**
now (`_chron_autoread_save`), it writes every key from the live sources, it makes its parent, and
it says so when it cannot — losing these marks is not cosmetic, it is **re-reading reels that have
already been paid for**.

The guard was **seen RED for its own reason** before it was believed: re-introducing v1762's exact
defect (`"reels": []`) fails it with *"a visit mark wiped the swept reels again — v1762, a third
time"*, and a second assertion pins the writer count at 1.

Also swept the class from REG-249 across all 34 atomic-write sites in `tv/`. The ones that matter
are the four whose path is **env-isolated** (`TV_CHRON_AUTOREAD`, `TV_CHRON_EVIDENCE`,
`TV_CHRON_RESULT`, `TV_VAULT_RESULT`) — all four make their parent now. The evidence save holds the
**banked pages**, the most expensive bytes the console keeps, because every one was paid for by a
real read. The remaining sites write into directories that exist by construction (the reel dir,
`tv/` itself) and were left alone rather than papered with a line each.

## REG-251 — the second witness was being shown a different picture (FIXED v1901)

The Chronicle is read by **two lanes** so that agreement between them is evidence. For eleven
versions the two lanes were not looking at the same pixels:

- The **Claude** lane has cropped to the Chronicle list band since v1780 — its own measurement was
  **0/6 pages read full-frame against 5/6 cropped**, six frames of his reel, same reader, same day.
- The **Grok** lane was handed the whole **2940×1912 desktop grab every time**, because the crop
  lived *inside* the Claude reader where no other lane could call it. `grep LIST_BAND` found it in
  `chronicle_template` (which owns the numbers) and `tv_diablo` — and nowhere else.

Agreement between witnesses shown different pictures is worth less than it reads, and a
**disagreement was not even attributable**, because the framing was never written down anywhere.

⚠ **This does NOT claim the crop is simply better, and the file says so.** v1829 measured a frame
the sweep had refused twice and found the **full frame read it fine — and so did the Grok lane,
full-frame, conf 0.88, six names.** Both measurements are real and they are in tension; the cause
of the transience is still open. What is not in tension is that the two lanes should be asked the
same question about the same rectangle, and that the record should say which.

**Fixed:** one `chronicle_crop.list_crop()` called by both lanes (the band stays in
`chronicle_template`, which measured it); the Grok lane gets the same dual route — a refused crop
retries the full frame, so this can only add a read, never lose one; and `normalize_page` now
stamps **`framing`** (`crop` / `full` / `stub` / `None` = the lane did not say) onto every page, so
the next cross-lane disagreement is attributable instead of mysterious.

Guards in `test_g5_grok_eyes.TestBothLanesSeeTheSamePixels`, **seen RED for their own reason**:
restoring the pre-v1901 lane fails with *"the grok lane read the WHOLE DESKTOP GRAB — the framing
v1780 measured at 0/6 pages"*. A third asserts neither lane names `LIST_BAND` itself, comments
excluded — the copy that drifts is always the second one.

## REG-252 — the file that says what he owns did not follow the isolation rule (FIXED v1902)

Every neighbouring piece of live state takes an isolated `TV_HIST` along with it — sessions,
frames, the chronicle's swept memo, its reads memo, and (v1895) the vault's own **result**. Two did
not:

```
VAULT_LEDGER_PATH = os.path.join(HERE, "vault_accum.json")   # the record of WHAT HE OWNS
_VAULT_SWEPT_PATH = os.path.join(HERE, "vault_swept.json")
```

A sweep driven against a fixture hist wrote its swept memo and its **owned-item ledger** into his
real `tv/` tree. `tv_diablo._KNOWN_DEAD_FILE` — the learned dead-frame signatures, whose whole point
is that the learning **survives restarts** — had it too.

**Nothing has hit it, and that is exactly why it was worth fixing rather than shrugging at.** What
stopped it was the discipline of every fixture written so far, not the path. The gate that proves
his tree is byte-identical after a run can only catch this *after* a test reaches it, and by then
the ledger it corrupted is merge-max: nothing it gained would ever be subtracted.

Three chronicle files (`chron_evidence`, `chron_autoread`, `chron_last_result`) had the softer
version — they isolated only when a test **remembered their own env var**, while the swept and reads
memos have derived from `TV_HIST` for versions. A rule half the files follow is a rule nobody can
rely on. All six derive from the hist now; each env override still wins where a test wants one
specific file.

`_fixture_root_for_state()` also **moved to the top of the file**. It sat 11,000 lines down, after
every vault path had already been built from a bare `HERE` — a helper that arrives after its callers
is a rule that applies to whoever remembered.

The guard is **the class, not the two instances**: `TestEveryWrittenStateFileFollowsAnIsolatedHist`
asks all eleven written state paths where they live with and without `TV_HIST`, with every other
`TV_*` variable stripped, and fails any that stays in his tree. Seen RED for its own reason.

## REG-253 — `throwOut` was in the schema and nowhere in the prompt (FIXED v1903)

He asked, in his own words: *"items being routed correctly? you simulated every single item that
would be found and made sure it gets muled or thrown out properly?"* The throw half had a hole.

`throwOut` appeared **exactly once** in `VAULT_READ_PROMPT` — inside the JSON template, printed as
`false`. Nothing told the reader what it meant, when to set it, or that `throwWhy` existed at all.
Meanwhile `vault_retro` consumes **both**, gates them behind a strictly higher confidence floor
(0.85) and three separate recordings, refuses to let one reel ever suggest a bin, and rides them out
to him as `suggestions`. **An elaborate safety mechanism fed by a field nobody was ever asked to
fill** — so an empty throw lane read as "nothing is junk" when it meant "nobody was asked".

Two fixes, and the second does not depend on the first:

1. **The prompt now defines it** — narrowly: a white/grey base with no sockets and no magical text,
   never a named unique or set item, never a rune/gem/jewel/charm/material, never "I don't recognise
   it", and `throwWhy` in the reader's own words. Konyo decides how wide *junk* should be; this is
   the floor, not his policy.
2. **A grail name is refused in code, whatever the reader says.** Every existing guard on this lane
   was about *how much evidence* a throw needs; none was about *what may be thrown*, and "is this
   junk" was a vision model's opinion. `vault_retro._grail_guard()` checks his roster: a named
   unique or set piece is never a throw-out suggestion at any confidence, from any number of
   recordings. An unloadable roster **says so once** rather than quietly answering "not grail".

⚠ **My own first guard was vacuous and I caught it by turning the backstop off.** It asserted
`"Isenhart's Parry" not in throwOut` — but the fold rewrites the straight apostrophe to his roster's
curly one, so the name it looked for was never in that list either way. With the backstop disabled
only 1 of 4 tests went red. It asserts on the lane being empty now, and 2 of 4 go red.
A fourth test is the CLASS: every field `normalize_item()` consumes must appear in the prompt.

## REG-254 — the simulator he asked for printed nothing (FIXED v1904)

`python3 tv/vault_simulate.py` **printed nothing and exited 0.** The file has no `__main__`; the
scenarios were reachable only by importing the module from `test_vault_lane.py`.

Its own docstring promises the opposite: *"this prints the whole decision for a scenario in the
words the Vault manager would use, so a wrong rule is visible rather than merely unasserted"* — and
it exists because he asked for exactly that: *"simulate it based on the reels you already have …
make sure its not discading anything it shouldnt. and make sure its muling anything it is."* The
demonstration existed as code and could not be watched. **A quiet exit 0 is the worst possible
answer, because it is indistinguishable from a clean run.**

It runs now — six scenarios over his real reels, no vision calls, no writes — and a scenario whose
reels are missing from the checkout prints `⚠ NO FRAMES … this is not a pass` and exits 1 rather
than scrolling past. The assertions stay in `test_vault_lane.py`; this prints, that gate judges.

⚠ **And the transcript did not show the number its own scenario is about.** `merge-max` claims
*"count stays 5"* while the OWN line printed conf and witnesses only. It prints `x5` now — a
demonstration that omits the quantity under discussion proves nothing to the person reading it.

⚠ **The encoding guard caught the new CLI within the same run**, and that is the guard working:
`test_every_cli_that_prints_non_ascii_is_encoding_safe` skips importable modules, so it had never
looked at this file. Adding an entry point made it a CLI, and a CLI that prints `⚠`/`✅` on a
non-UTF-8 console **crashes while REPORTING** — a clean tree exiting non-zero from the wrong place.
`console_safe.enable()` added. [[dual-machine-setup]]

## REG-255 — the second eye had a lamp and no receipt (FIXED v1905) + a falsifiable prediction for v1901

The doctor's `grok lane` check reports the lane is **available**. That is a status lamp, and a lamp
has been wrong on this exact lane before: G5 sat pinned PRIMARY and **silently dark for weeks** while
every honesty surface read clean, because a lane that never attempts never records a failure.

The new `second eye receipt` check reads the **banked evidence** — written by the readers themselves
— and answers the only question that matters: *of the names Claude has seen, how many did the second
eye actually corroborate?* A lane that is ready and has corroborated nothing reports **MISSING**, not
OK. No evidence at all is **UNKNOWN**, never a failure.

**Measured on his own evidence, 2026-08-21, 767 banked pages:**

| ledger | corroborated by both lanes | seen only by grok |
|---|---|---|
| uniques | **35 / 298 — 11.7 %** | **0** |
| sets | **34 / 86 — 39.5 %** | 6 |

⚠ **THIS IS THE BASELINE FOR v1901, AND IT IS FALSIFIABLE.** The uniques rate is a third of the sets
rate and grok has *never once* seen a unique Claude missed — which is exactly what you would expect
if the second eye was being handed the full 2940×1912 desktop grab on the densest pages, the framing
v1780 measured at 0/6. If the framing was the variable, the uniques rate on pages swept **after**
v1901 should rise materially above 11.7 % and grok-only sightings should stop being exactly 0.

**If it does not move, the framing was not the cause** — v1829 already measured the full frame reading
one refused page fine, grok included — and the next place to look is the worker pool under
concurrency, which is where that note left the question open. Either answer is worth having; the
point is that the number now exists and can be read off `chronicle_doctor.py` at any time.

Also fixed in the same run: the doctor's report column was a hardcoded `%-16s`, which the 18-char
name `second eye receipt` un-aligned on sight. The width comes from the longest name now.

## REG-256 — two CSS defects sat on main for eleven versions because their only gate kept getting cancelled (FIXED v1906)

`Routine I — Playwright suite` is the only thing that judges two CSS invariants, and it takes long
enough that the next push cancels it. **Twelve consecutive Routine I runs — v1894 through v1902 —
are all `cancelled`.** v1903 was the first to reach a verdict since v1893, and it went **RED** on two
defects I had shipped myself and never seen:

```
bible.html:3288        var(--q-set,#5fc97a)  — the settled set green is #00fc00   (mine, v1881)
tv/control_ui.html     --dim renders as #5f6a5a AND #7d7360, undefined, both live (mine, v1894)
```

**A gate that never reaches a verdict reads exactly like one that passed.** That is the same class as
everything else in this arc, and the cause was my own push cadence — one ship per push, all night,
against his standing rule to batch 3–4. [[feedback-batch-pushes-gate-cost]]

**Fixed, both:** the "soon" countdown now uses `--best` (#66ff88), which is the green its own live dot
already uses and semantically right — an item-quality token had no business colouring a clock. The
console's `.chron-age` uses the `#5f6a5a` every other `--dim` site in that file uses.

**And both invariants now run where they cannot be cancelled.** They are pure file reads — no
browser, no page — so there was never a reason for them to live only in a shard-6 Playwright suite.
They run in the python suites, which his pre-push hook executes on every single push. The Playwright
copies stay; this is an earlier second reader of the same rule, not a replacement. ⚠ **The palette is
parsed out of the spec, never copied** — a second hardcoded `SETTLED` would drift from the first the
moment either moved, which is the defect the guard exists to catch.

Verified on pixels (headless Chrome, CDP, :9231): forcing `.soon` was useless because `_tzPaintClock`
rewrites `el.className` every second and the forced class was gone before the shutter — the first
capture showed the GOLD normal state while `getComputedStyle` had just reported green. Stubbing
`Date.now()` to 45s before a boundary made the state genuinely soon, and it renders `0:45` in green.
[[chrome-cdp-mac]] — markers do not survive a re-render.

## REG-257 — the sort control was asked for, stored, and read under another name (FIXED v1907)

The live prompt has asked for `chronicleSort` since v1818 — *"the sort control at the TOP RIGHT of
the panel, read literally"* — and `tv_diablo` writes the answer into every chronicle journal row.
`normalize_page` reads **`sort`**, and `proposal_from_pages` copies it onto every sighting.

`live_pages` built its page dict **without it.** So the field was empty on every page ever produced:
a question asked, an answer stored, and a reader looking at a different key. Fifth hit of this shape.
[[plumbing-with-no-tap]]

Joined, both spellings (`chronicleSort` / `chronicle_sort`), and the blank is now explained rather
than accidental: **neither retro prompt asks for `sort` at all**, deliberately, because v1828 settled
that the printed `First Found:` stamps decide order and never a label. So a retro page's blank `sort`
is the absence of a *question* and a live page's blank one is the absence of an *answer* — pinned by
a test so the distinction cannot quietly collapse. [[unknown-stays-unknown]]

## REG-204 — a solo OCR tab guess outranked two disagreeing witnesses (CLOSED v1907, filed OPEN 2026-08-20)

`fuse_tab_signals` rule 1 — *"OCR tally wins over vague vault labels"* — returned the OCR tab before
grid or model were consulted at all. The intent is right; the implementation also beat a **specific
and different** tally:

```
fuse_tab_signals(ocr_tab="gems", grid_label="stash-runes")              -> ('gems', ['ocr'])
fuse_tab_signals(ocr_tab="gems", grid_label="stash", model_tab="runes") -> ('gems', ['ocr'])
```

One witness — one that calls itself a **guess** in its own docstring — overruled two that disagreed,
and reported `sources: ['ocr']` while doing it.

Now: a tally from grid, model or journal that **disagrees** with the OCR tally returns
`("stash", ["tab-conflict"])` — a named refusal, no tally claimed.

⚠ **It returns `"stash"`, not `""`.** Both witnesses agree the panel IS a stash and disagree only
about which tally; `""` sends `class_from_tab` down the else branch and the frame is dropped as
`gameplay`. Losing a real stash panel is a worse answer than declining to name its tab.

⚠ **The reason it sat OPEN is the reason it needed synthetic tests.** The disagreement occurs in
**zero of the 68 stash-panel frames** in his corpus, so his data cannot exercise the branch either
way — a fix validated on his frames alone would be untested. Five tests drive it directly, including
the half that was always right (a vague `shared`/`personal` label is still beaten by the tally).
[[gate-blind-to-unexercised-input]]

**CI note:** `Routine I — Playwright suite` reached a verdict on v1906 — **all 8 shards green**, the
first completed Playwright run since v1893, confirming both REG-256 fixes. And the live site serves
`v1906`, checked on the actual bytes at `https://bull-4-u.com/d2r/`, not on a workflow's green tick.

## REG-258 — a lagging witness is not a disagreeing one (FIXED v1908, regression from v1907)

**v1907 shipped REG-204's fix with `journal_tab` in the conflict set, and that was wrong.** Caught in
the review pass 20 minutes later, before any sweep ran against it.

`_kai_sticky_tab` says what it is in its own docstring: *"journal tab for a film timestamp: last deep
tab with st<=ts+1.5s, **held** until the next deep tab (or 25s)"*. It is a **lagging** signal by
construction. So for up to 25 seconds after he clicks from Runes to Gems, the sticky still says runes
while the OCR correctly reads gems — and v1907 treated that as a contradiction, demoting an **ordinary
tab switch** to a generic `stash` with no tally.

That trades a regression on something he does constantly against a contradiction measured at **zero of
68 frames**. REG-204's measurement named `grid` and `model`, and it named them for a reason — I widened
the set past the evidence that justified it. The conflict set is grid and model again, with the ordinary
tab-switch case pinned by its own test. [[feedback-suspect-the-instrument]]

Two more guards while the file was open, both **seen RED for their own reason**:

- **The conflict marker is not mistaken for an OCR witness.** `control_app` has two sites that do
  `owner = "ocr" if row.get("sources") else None`, so a non-witness token in `sources` could claim OCR
  ownership of a frame no reader vouched for. It cannot — the conflict returns tab `"stash"`, whose
  label is `stash` and never `stash-*`, and that branch is guarded by `label.startswith("stash-")`.
  Pinned rather than left to be re-reasoned. (Precedent for a named non-witness token already exists in
  that file: the boot-screen guard returns `["boot-screen-guard"]`.)
- **The CLAUDE lane's crop path is driven.** v1901 moved the crop into a shared module and the new tests
  covered only the lane that had been broken. **Every existing chronicle test runs under `TV_STUB`,
  which returns before the crop is ever reached** — so the side that was already right was unexercised,
  and a refactor whose old side is unexercised is a refactor half-verified.

## REG-203 — a fire-lit fight called `stash-gems` (CLOSED v1909, filed OPEN 2026-08-20)

Filed OPEN with a named reason: *"retuning a pixel fingerprint needs its own before/after sweep over
the whole corpus"*, and REG-205 added *"three hand-labelled frames is not a corpus."* Both are
answered here.

**The corpus:** `tv/stash_grid_truth.json` — **twelve frames labelled by opening the images**: five
real stash panels (materials, personal, runes, and two on shared), a Chronicle panel, two portal
scenes, three frames of a fire-lit Nihlathak temple, and the River of Flame. `tv/stash_grid_score.py`
prints the before/after; the ratchet lives in `test_stash_eye_aspect.py`.

**The fix:** `_panel_open_from_features` had a floor on `dark_cols` and **no ceiling**. A stash grid
is a *lattice* — a bounded number of dark gridline columns out of 84. A dark *picture* is not a
lattice: most of its columns are dark. So a fire-lit temple (31–40) satisfied "grid lattice present"
as easily as a real panel (7–14). `_PANEL_MAX_DARKCOLS = 24` sits in the middle of that 17-column
gap, and `dark_cols` spans 0–71 across his hist, so it is a threshold the signal actually crosses.

**Measured on his whole 883-frame hist, before → after:**

| | before | after |
|---|---|---|
| tally claims | **9** | **1** |
| …of which correct | 1 | **1** (`8_1785078207015`, the real MATERIALS panel) |
| `stash` bucket | 69 | 77 — the eight false tallies are **demoted, not discarded** |
| real panels claimed | 5/5 | 5/5 |

⚠ **I CONCLUDED THE OPPOSITE FIRST, FROM THE FEATURE TABLE, AND THE MEASUREMENT OVERTURNED IT.** A
real stash panel on the SHARED tab reads `dark_cols=40` — the same as the fire — which looks fatal to
any ceiling. It is not: **the plain-stash path never required `panel_open`**, so those frames still
come back `stash`. The ceiling gates only the TALLY branches, where the real panels read 7 and 14 and
the false ones 31–39. I wrote the refutation into the corpus file before running it, and running it
said otherwise. That paragraph is now the correction it deserves. [[feedback-suspect-the-instrument]]

⚠ **AND MY FIRST SCORER WAS BLIND.** It graded `label != "gameplay"` — an axis that is nearly
constant, because the grid answers `stash` for almost any dark frame. **Two opposite sabotages — a
`dark_cols` cap and refusing every panel outright — scored identically to the real code.** A metric
two opposite sabotages cannot move is measuring nothing. It grades the TALLY axis now, and three
sabotages (remove the ceiling · refuse every panel · a ceiling above the signal's range) each fail a
different test. [[feedback-blind-fixture-green-gate]]

**Still open, and now measurable:** `5_1784984201581` is a real RUNES tab the grid calls plain
`stash` — one missed tally, pinned by the ratchet so a future retune has to keep it at one or say
what earned better. That is REG-205's remaining half.

## REG-259 — three CI gates that could not fail, and one that failed for no reason (FIXED v1910)

A sweep of every routine asking one question: **can this gate go red for the thing it exists to
watch?** Four could not, in four different ways.

**1. Routine J was a lamp.** `J_screens.js` captured four PNGs, printed *"captured 4 screenshots"*
and exited 0 — always. The workflow's own header says they are uploaded *"for manual visual review"*,
and nobody downloads a 30-day artifact daily. So it reported SUCCESS for a page that could be four
black rectangles, four copies of one unchanged view, or a calc panel with nothing selected.

It asserts three renderer-independent things now, rather than the pixel baseline the header proposed
(a committed baseline goes flaky the moment CI's fonts or GPU flags move, and a gate that cries wolf
gets disabled): every shot **painted** something, the four states are actually **different from each
other**, and the state each shot **claims** to show is the state the page was in. Every threshold was
measured first through CDP — 547–751 KB per shot, four distinct md5s, `data-active-tab` stepping
`bosses → calc → tz` — and `MIN_BYTES` is 60 000: an order of magnitude under the smallest real shot
and an order of magnitude over a blank 1600×1200 PNG.

⚠ **And shot 01 was never the bosses.** The page opens on `session`, so `01_bosses.png` has been a
picture of the session cockpit for as long as that file existed. It clicks the bosses tab now —
restoring the intent rather than renaming the evidence. [[label-outlived-referent]]

**2. Routine H could pass vacuously.** It gated on `fail_count !== 0` and nothing else. `items` comes
from the page's own `ITEMS` array; if that stops loading the sweep reports
`{tested: 0, opened: 0, fail_count: 0}` and the gate said **PASS**. It also collected `pageerror`
since the day it was written and **never looked at it** — evidence gathered and not consumed, the
same defect as a field nobody reads. Measured on the run before the change: tested 320, opened 320,
errors []. The floor is 250. Driven against four fixtures: normal passes; zero-tested, page-threw and
a real failure each fail with their own message.

**3. Routine K signed off on measurements it never took.** Warn-only about speed by choice — but
`undefined > 2500` is false, so a metric `K_perf.js` stopped emitting printed `k=undefined (budget
2500ms) OK` and the step concluded **"All perf thresholds green"**. *"We measured and it was fine"*
and *"nobody measured"* are different facts. A missing metric is an error now; exceeding a budget
still only warns.

**4. Five routines could not see the input they police.** Routine I already says this in its own path
list; G, H, J, K and L watched only `bible.html`. Editing `J_screens.js` — or the workflow file that
runs it — changed what the gate DOES while triggering nothing, so the change landed and the routine
that judges it stayed asleep until the next cron. Each watches its own script and itself now, pinned
by a test. ⚠ That test had its own trap worth recording: **PyYAML parses the bare key `on:` as the
boolean `True`**, so a naive `doc.get("on")` reads as *"this workflow has no triggers"*.

## REG-260 — a flaky spec is a lamp with extra steps (FIXED v1910)

`tests/v587_spare_base_capacity.spec.ts` failed **twice** on one CI runner (`retries: 1` = two
attempts) on **v1909 — a commit that changed no page logic at all** — and passed on a fresh runner
minutes later, same bytes. Attribution by delta: Routine I was green on v1906, v1907 and v1908, and
v1909 touched only `tv/` python and the version stamps.

The spec waited on three fixed `waitForTimeout`s and a 400 ms `_spareBaseInfo` memo; on a loaded
runner `forgeScan` had simply not planned both words yet. Both phases poll now, up to 20 s, with a
message that says what never happened. **Polling is strictly more patient than a fixed sleep, so it
can only remove timing failures, never add one.**

A flaky gate is the same defect as a lamp: it stops carrying information, and it trains everyone to
re-run instead of read. Compile-checked with `playwright test --list`, which runs no test and opens
no browser — the suite itself still runs on GitHub, never on his Mac.

## REG-261 — `import yaml` in a test took the deploy down, and every local signal was green (FIXED v1911)

**v1910 never reached the live site.** The Publish workflow went red on
`ModuleNotFoundError: No module named 'yaml'` — two errors in
`TestEveryRoutineCanSeeTheInputItPolices`, Deploy skipped, `bull-4-u.com/d2r/` left serving v1909 —
while locally **1,413 tests and all 34 gates were green.** PyYAML is installed on his Mac and is not
on the runner.

The host is part of the fixture, and this is the **third host-difference of this arc**: his Windows
console encoding (v1904), a local Python **3.9** against CI's **3.11** (`sys.stdlib_module_names`
does not exist here), and now a module that only one of the two machines has.

**Fixed** by parsing the `on: push: paths:` block directly — the shape is fixed, three keys deep, one
quoted string per line — and verified under a **simulated no-yaml host** (`__import__` patched to
raise for `yaml`), not merely by deleting the import and hoping.

⚠ **Skipping would have been worse than failing.** `try: import yaml / except: skipTest` turns green
on the only machine that publishes, and a test that skips where it matters is a test that does not
exist.

**The class is guarded now:** `TestNoSuiteImportsSomethingCIDoesNotHave` walks every `tv/test_*.py`
AST and fails on any third-party import outside the allowlist — which is exactly what CI installs
(`pillow`, one line in `publish.yml` and `tv-tests.yml`), plus `playwright` where its single importer
wraps it in a `try`. It asks the **filesystem** where each module lives rather than consulting
`sys.stdlib_module_names`, which his 3.9 does not have — the guard must not repeat the defect it
guards. Seen RED by restoring the exact import: *"test_control.py:9744 imports 'yaml'"*.

## REG-205 — the selected stash tab is in the pixels, and the marker is the GEM (CLOSED v1912, filed OPEN 2026-08-20)

REG-205's own words: *"the selected stash tab IS visible in the pixels; reading it is not solved."*
It tried the obvious thing — crop the chrome, split into five equal cells, argmax mean luminance —
and got **1 of 3 on margins of 1–5 grey levels**, because the labels are not equal width and a cell
straddles two of them.

**The obvious thing was the wrong FEATURE.** D2R does not merely brighten the active tab: it draws a
gold box around it *and* sets a small **blue gem** on the underline directly beneath it — tiny,
saturated, at a position no other chrome occupies. A structural marker, not a brightness contest.

**Measured on the twelve hand-labelled frames: 12 correct, 0 wrong, and zero false tabs on the seven
non-panels.** Across his whole 883-frame hist it names a tab on **8** frames.

**The geometry is regular, and that is a measurement, not an assumption.** The gem centres came out
at personal **0.141**, shared **0.324**, materials **0.691** of the strip — differences of 0.183 and
0.367, exactly one and two pitches. So the five centres are `0.141 + 0.1835·i`, which **predicts**
gems at 0.508 and runes at 0.875. ⚠ **No frame in his corpus has either tab open, so those two
predictions are UNVERIFIED** and the constants say so rather than letting them read as covered.

⚠ **IT CAUGHT A WRONG LABEL, AND THE DISAGREEMENT WAS THE FINDING.** On `5_1784984201581` the reader
said PERSONAL where REG-205's hand label said RUNES. Zoomed to 2.6×: the gold box and the gem are
both on PERSONAL, a WRAITHSTEP tooltip covers its text, RUNES is grey with no border, and the grid
below holds gear. **The detector was right and the label was wrong** — corrected in the corpus, and
REG-203's "one missed tally" was that same mislabel, so the tally axis is now **0 false, 0 missed**.

⚠ **THE FALSE POSITIVE THAT ALMOST SHIPPED.** Without guards it named a tab on **131 of 883** frames,
125 of them "personal" — and five of the six I opened were **solid blue capture failures**, where
every pixel qualifies as blue. Same shape as this file's oldest scar, *"69 wallpaper frames sealed as
stash-gems"*. Both guards sit in enormous measured gaps — qualifying blue px **2–18 vs 1025**, strip
luminance sd **32.7–35.2 vs 0.00** — and both are driven red by their own fixture.

**Wired as a witness, not a king.** It sits *after* the OCR, which reads the actual word, and
*before* the grid, which measured 1-of-9. It joins the conflict set, and it is credited when it
agrees. Twelve frames is a small corpus and two tabs have no example: a reader of words outranks a
geometric prediction until the corpus says otherwise.

⚠ **Instrument note, ~15 minutes lost:** a stale `__pycache__` served bytecode from a sabotage run
and reported a result the source could not produce. **After a sabotage/restore cycle, clear
`__pycache__` before believing anything.** Founding rule 4, in its cheapest form.

## REG-262 — a unique filed under sets, an undo that could not undo, and a date wired to one surface of three (FIXED v1913)

Three reports in one sitting, and the first two are **one cause**.

**1. "this is a UNIQUE item and it wrongly put this color and item in the wrong area routed
incorrectly to F-Sets instead of F-Uniques"** — *Blood Crescent*, a unique Scimitar, sitting as
F·Sets' last find. **2. "when i hit UNDO it doesnt really undo it its stil counted"** — because every
sets-side operation on a name that is not a set piece is a no-op, so the ledger row survived.

The undo bar bucketed names as `isU = in ITEMS || in _UNI_EXTRA`, with **`else → SET` as a
catch-all**. Blood Crescent is an off-grail unique in neither list, so the sets bucket took it.
`_UNI_EXTRA` is a hand-maintained exceptions list, and this is the **third** time it has been patched
for exactly this shape (v664: 62 mod-chronicle uniques walked into `d2r_setPieces`; v1692: a find
routed into the physical vault). **A list of exceptions is not a classifier.**

⚠ **AND THE ANSWER WAS ALREADY INSIDE THE SAME FUNCTION.** Two lines below the bucket, the colour is
resolved with `window._artRarity` — the app's one classifier — which is why the chip **rendered in
unique gold while the bucket called it a set**. Measured in a real page:

```
Aldur's Deception -> "set"    Immortal King's Will -> "set"
Blood Crescent    -> "unique" Shako -> "basic"
```

It routes on the classifier now, keeps the two lists as a fallback for names it has no opinion about,
and **`else → set` is gone**: a name neither side recognises is claimed by neither bar. Verified in a
real page — F·Uniques claims Blood Crescent in `#c7b377`, F·Sets claims Aldur's Deception in
`#00fc00`, and undo removes the row. [[feedback-contradiction-is-the-finding]]

**3. "the items need to be timestamped to the ingame finding (NOT WHEN THE AI REGISTERED IT) … same
for F-Sets same logic."** v1864 built exactly that and joined it to **one** surface — the undo bar's
single last-find line — while both FOUND lists, which are where he actually reads his collection,
kept printing the ledger stamp alone. One `window._chipFoundDate(name, ledgerStamp, long)` now serves
all three: the game's date on the chip in gold, *"this board ticked it …"* in the title, and nothing
invented when the Chronicle page never printed one. [[the-unjoined-end]] [[copy-drift]]

## REG-263 — one legible label is not a selected tab (FIXED v1913)

`stash_screen_open` returned `canons[0]` when exactly **one** chrome label was legible — the same
wrong question v1860 fixed on the line below it. The strip prints **all five** labels whichever tab is
active, so how many the OCR transcribed is a fact about the OCR.

**Measured on all 883 of his hist frames:** the gate admits 10 and took that branch on **three**, and
was **wrong on all three** — `5_1784984201581` (canons `['gems']`, a tooltip over the rest),
`7_1784984245418` and `8_1784984208085` (canons `['shared']`) are all unmistakably on **PERSONAL**.

It asks the **gem** first now (v1912, structural, abstains rather than guess) and otherwise answers
`"stash"`. Before: 7 honest + 3 wrong. After: **8 correct specific tabs + 2 honest abstentions, zero
wrong.** ⚠ It was inert — all three callers test `is None` and discard the value, because v1857 used
it as a lane and v1859 had to revert that. A function that returns a wrong-by-construction tab is a
loaded gun waiting for the next caller who does not read the comment.

## REG-264 — 302 finds were waiting and the tab he lives on said nothing (FIXED v1914)

Konyo: *"where is my inbox widget with the ACCEPTing the 267/214 the thing you mentioned earlier."*

**It was never missing — it was on the other tab.** Measured live against his running console:

```
/api/chronicle_sweep  ->  wouldAdd {uniques: 266, sets: 36}   saved 2026-08-21 00:47
#chron-apply          ->  text "register 302 ✓", hidden=false, boundingBox 0 × 0
#hd-chron             ->  display: none
```

The button exists, is not hidden, says the right number, and **has no pixels** — because v1674 hid
that whole column on Sessions **at his own request** (*"everything here and to the bottom is
duplicated on the TV-D tab.. i dont need it on SESSIONS TAB"*).

So the panel stays where he put it and **Sessions gets a pointer**: `📜 302 find(s) read and waiting
to register — TV·D ▸ Chronicle Sweep →`, rendered only when there is something to register, carrying
the COUNT (a nag without a number is furniture), and clicking it routes to TV·D and scrolls the panel
into view. Verified on his live console at 1001×38 px on the Sessions tab.

**A night of reads nobody can see is a night of reads that did not happen.** [[the-unjoined-end]]

Also confirmed by the same measurement, and worth recording because both were shipped blind last
night: the panel's header reads *"this proposal was made 10h ago · restored from disk, not from this
session"* — v1894's age line and v1895/v1899's persistence, both working on his machine, through a
restart, on real data.

## REG-265 — a thin TZ zone looks unfarmable and clicks like a farmable one (FIXED v1915)

Konyo: *"the mouse cursor for TZ ZONES that arent worth farming at all i want a CANCELLED sign on it
so i know i cant click them. only the TZ ZONES worth farming should be clickable and routable."*

A thin zone (density < 600) was greyed and grayscaled and still routed on click, with the title
saying *"not worth the window. Open it anyway"*.

⚠ **THIS IS THE THIRD REVERSAL OF THE SAME DECISION AND THE THREAD IS RECORDED RATHER THAN SWAPPED
IN SILENCE:**

- **v1588** — a thin zone is inert: aria-disabled, no handler, a padlock. His call.
- **v1801** — unlocked. Dropping the meaningless level term took thin from **15 of 66 to 40 of 66**,
  and *"a lock over most of the map stops informing him of a ranking and starts punishing him for
  one."* Asked directly, he chose greyed-and-cancelled-but-clickable.
- **v1915** — locked again, in his own words above.

**The v1801 consequence has not changed and is not hidden by this ship: under 600 density is thin, so
a large share of the map is unclickable again.** He decided it twice in opposite directions; the
later decision wins, and what a codebase must not do is let a reversal happen quietly.

What v1588 never had — and what he actually asked for — is the **cursor**: `.tzz-thin` and everything
inside it is `cursor: not-allowed`, and the hover lift is off. The title now ends *"Not farmable, so
not clickable"* instead of *"Open it anyway"*.

`tests/v1596_tz_emphasis.spec.ts` pinned v1801's choice in four assertions, which is exactly why the
reversal could not be accidental. It pins the new one — no handler, `aria-disabled="true"`,
`tabindex="-1"`, `cursor: not-allowed` — and the verdict half (grey, grayscale, THIN tag, "not worth
the window") is untouched. **The test's name was renamed too**: *"but it is no longer a dead card"*
would have been a label that outlived its assertion. [[label-outlived-referent]]

## REG-266 — the board wore the gauntlet and the console wore the macOS arrow (FIXED v1916)

Konyo: *"the MOUSE CURSOR with its effects when clicking and the hand closes the cursor mouse isnt
syncing and symetric across the platform there are areas that its a regular mouse cursor."*

**Measured on both surfaces before writing a line — the asymmetry is not scattered, it is the whole
console:**

| | custom cursor | measured |
|---|---|---|
| `bible.html` | `*{cursor:url(<gauntlet>) 2 1, auto !important}` since v605 | **2,778 interactive elements across 12 tabs, zero on the OS arrow** |
| `tv/control_ui.html` | **none** | 69 plain `cursor: pointer` rules |

**One asset, not a second copy.** `art/hd_cursor_hand32.png` is the exact bytes decoded out of the
board's inline data URI (1674 bytes, md5 `e7af77aa`), served to the console as `/art/`. A test pins
the two **byte-identical**, so the hand cannot drift between surfaces — which is what he actually
asked for. The board keeps its inline copy: it is proven, it deploys to Cloudflare where a relative
art path is a different question, and changing a working cursor to prove a point is not a fix.

Verified in a real page: `body` and every button return the gauntlet URL with hotspot `2 1`, text
inputs keep the I-beam, and the OS-arrow audit on the console is now **21 interactive elements, 0 on
the arrow**. Three sabotages each fail their own guard: remove the rule, drift the hotspot, drop the
`not-allowed` override.

⚠ **THE CLOSED HAND IS NOT DONE, AND THAT IS SAID RATHER THAN FAKED.** He also asked for the hand to
close on click. `art/hd_cursor_ohand_atlas.png` is **16 frames of the OPEN hand idling** — opened and
looked at, frame by frame, with the ink bounding box measured per frame — and **there is no closed
fist in it**. A slightly-more-curled idle frame would read as a fix and look like nothing. The press
state needs the real CASC press asset or new art, and his CrossOver bottle is not on this machine's
usual path to re-extract from. [[unknown-stays-unknown]]

## REG-267 — the biggest button on the panel never said what it does (FIXED v1916)

The Chronicle Sweep panel was shown **cold to a different model family**, with no hint, and asked
what was worst about it for someone deciding whether to press the green button:

> *"The actual cost or consequence of pressing `register 302` is never stated. The user only sees
> what WOULD be added, not what 302 means, or whether registration is permanent."*

It is right. The note beside the button says what has **not** happened yet (*"read-only — nothing has
been written"*); nothing said what happens when he presses it. And `302` is `266 + 36` — the panel
shows both numbers and never joins them to the button.

The control now carries the arithmetic and the consequence, and the consequence is **true rather
than reassuring**: *"writes 266 unique(s) + 36 set piece(s) = 302 into your grail ledger. Reversible:
undo any one on the board, or press 'forget what is swept' here to drop the whole proposal."*
Both escape routes exist — `_forgeUndo` per item, `/api/chronicle_forget` wholesale.
[[grok-second-eye]]

## REG-268 — the focused hunt was dead twice over, and both halves were invisible (FIXED v1917)

Konyo: *"for F-SETS it should cross reference the items i still dont have so it knows whats left to
find and it can keyword search for it when anaylzing and reading. (JUST LIKE UNIQUES i remember we
integrated this in some way for it already)."*

The integration is real — v1789's **focused hunt**, which goes back and re-reads the names the gate
HELD (seen once, needing a second witness). It had two defects, and each hid the other.

**1. IT READ A KEY THE READER HAS NEVER EMITTED.** `chronicle_hunt` scored every page on
`page["items"]`. `normalize_page` returns eighteen keys — `kind, ledger, lane, found, notFound, sets,
stateVisible, wrongTab, wholePage, witness, conf, printed, sort, foundAt, droppedBy, read, framing,
note` — and **`items` is not one of them**; `two_lane_read` passes that dict straight through. So
every hunted frame was read, **paid for with a real vision call**, and matched against an empty list.
It could not register a hit in production and never has: `grep -c "hunting\|hunt done"` across every
log on his machine is **0**, while `live lane` from the same function prints fine.

⚠ **The test that covered it handed it the wrong shape too** — `{"items": [{"name": "Mid Name"}]}` —
a fixture nobody had cross-checked against the real reader. The blind-fixture scar, in the one place
it costs money. [[feedback-blind-fixture-green-gate]]

**2. IT WAS UNIQUES-ONLY WHILE EVERY HELD NAME WAS A SET PIECE.** Hardcoded in three places. Measured
on his own last sweep (2026-08-21 00:47): **41 held, 41 of them sets, 0 uniques** — and the report
said *"nothing was held"* and spent **0 reads**, with `Tancred's Skull (bone helm)` sitting on six
sightings, one witness short of grounding.

**Fixed:** `page_names()` reads what the reader emits — `found` for a uniques page, `sets[].pieces`
for a sets page, and the old `items` shape still accepted because a caller using it is old, not
wrong. The hunt runs **per ledger**, each in its own evidence (`targets_for` defaulted to uniques, so
a sets hunt looked for its frames in the wrong index) and with its own page kind, and the read cap is
**per ledger** so a long uniques list cannot starve the sets hunt.

Guards: five, including the two measurements above. Sabotage A (back to `items`) fails 2; sabotage B
(uniques-only filter) fails 1. The old blind fixture now speaks the reader's real shape.

**Also filed, not fixed:** nothing anywhere hands a reader a list of what he is still MISSING. Both
chronicle prompts take only `{path}` and `{ledger}`, and both explicitly forbid naming an item the
reader expects to see (*"a name you expect to be there — leave it out"*). The hunt targets what was
**seen once**, never what was **never seen**. That is a different feature and it is written down in
`PROJECT_VAULT_MANAGER.md` rather than half-built.

## REG-269 — the per-item ledger existed and the accept path could not reach it (FIXED v1918)

Konyo: *"make sure it does register the items properly timestamped based on when it did analyze it
and add it to the vault/chronicle or whatever else happened in ledger while its routing and
funneling and tallying dii language so its related to the game and understood whats happening so
that way we can surgically fix something going in the future when it wrongly routes or funnels or
analyzes."*

He is describing **`d2r_chronicleInboxLog`**, which this file's own comment already calls the
*"VISUAL BACKEND — every KAI read forever for debug"*: one upserted row per name, never deleted.
The recorder was **IIFE-private**, so `chronicleApply` could not call it even though they live in the
same file.

**MEASURED on the proposal sitting on his disk right now** (`tv/chron_last_result.json`): **302 rows
ready to apply, all 302 carrying `why` + `witnesses[]` + `seen[{reel,frame,lane}]`** — and
`chronicleApply` read exactly three fields per row (`name`, `date`, `gameFound`). Six provenance
facts arrived; **one survived**, and only on the 66 rows where a page printed a legible date.

Every applied item now leaves a row, verified end to end in a real page:

```
Harlequin Crest              accepted  store foundLog   uniques
  why   "two different eyes read the same row · seen in two separate Chronicle visits"
  reel  reel_s_1786998496819_31092 · frame f_1786998503940.jpg · lane claude
  game  08/16/2026, 02:18 · Andariel        (kept apart from the board's own stamp)
Tancred's Skull (bone helm)  accepted  store setPieces  sets
  why   "seen on more than one photograph of the same page" · lane grok
Totally Not A Set Piece      REFUSED   store refused    sets
  why   "the board roster has no such set piece"
```

**`store` is the routing answer he wants to debug** — `foundLog` (grail ledger) · `owned` (physical
vault) · `setPieces` · `refused` — and it is written at the one point in the code that knows it,
three lines under where it was already computed and reported to nobody.

⚠ **The refusal row is the one most worth having and the one that used to vanish**: a name the board
roster rejects left no trace at all, so a refusal and a name that was never proposed looked identical.

Also fixed: `vaultAccumApply` reduced every item to a bare name string before handing it on, so a
grail item found by the **vault** lane arrived with no reel, no eye and no reason, and its ledger row
would have claimed it came from the Chronicle. It carries `lane/conf/witnesses/source` across now.

⚠ **A GUARD BROKE ON ITS OWN REACH, NOT ON THE CODE.** `test_an_unknown_name_is_reported_not_written`
pinned the literal spelling `res.unknown.push(n); return;` inside a 120-character window; the
provenance write between the push and the return moved them apart and it went red while the branch
still refused, still returned, and still wrote nothing. It asserts the **property** now — pushed,
returned, and no writer in the branch — and it was driven RED by letting the refusal write.
[[source-reading-guard]]

## REG-270 — the ownership footage was never missing; the archive is two archives (MEASURED v1919)

The Vault Manager brief needs one number before any of it is buildable: **how many frames of each
surface does he have, and which tab is each one on.** `tv/vault_corpus.py` answers it from pixels
alone — the INVENTORY title (gold-on-stone in a fixed band, scored as a fraction) and the v1912
active-tab gem. No model call.

**MEASURED over the 27 reels the sweeps already walk:**

| | |
|---|---|
| frames carrying ownership evidence | **263** |
| the stash+inventory template — his exact "both panels open" | **112** |
| a structurally readable stash tab | **151** |
| by tab | personal **102** · shared **23** · materials **14** · runes **8** · gems **4** |

⚠ **THE ARCHIVE IS TWO ARCHIVES, AND EVERY STASH MEASUREMENT SO FAR WAS TAKEN ON THE WRONG HALF.**
`frames/hist` holds **883 loose frames**; the 27 reels hold **1,970**; they share **zero filenames**.
The 68-frame corpus, the gem calibration and `stash_grid_truth.json` all came from the **loose** half
— **which no sweep has ever walked**. REG-185's *"0 of 17 reels declare an ownership surface"* was
read for months as "there is no stash footage"; it only ever said no reel **declared** one.

✅ **THE FALSIFIABLE PREDICTION FROM v1912 CAME TRUE.** The tab pitch `0.141 + 0.1835·i` was derived
from three tabs and predicted **gems 0.508** and **runes 0.875** with no frames to check them
against. The reels have both. Opened and looked at — gold box and gem on the named tab:

```
f_1784984269782   RUNES   detector x = 0.874   predicted 0.875   (off by 0.001)
f_1784984271825   GEMS    detector x = 0.506   predicted 0.508   (off by 0.002)
```

**The gem reader is 5 of 5 tabs**, and the corpus behind that claim is 151 frames, not 12.

⚠ **Widening the corpus surfaced a real miss, and the ratchet went UP.** The runes frame is a genuine
RUNES panel the grid fingerprint calls plain `stash` — `MISSED_TALLIES` goes 0 → **1**. It is
contained: the gem names that frame correctly, so `fuse_tab_signals` still answers
`('runes', ['gem'])`. **A number that only ever goes down is a number nobody is testing.**

## REG-271 — the game prints its own number and nothing ever read it (FIXED v1920)

Konyo: *"and sets.. are you sure its 118/135 how is it 87%? ingame im 85% somewthing isnt
calliberated properly to the ingame with the console"*, and then the harder question —
*"the AI READERS needs to be doing this automatically... where is the AI intelligence and AI coder
that routes and funnels and watchdog even for a safegaurd of this?"*

**He was right that it did not exist.** Every Chronicle page carries a completion bar and a printed
percentage. The readers have been photographing that panel for months and **nothing has ever compared
it to the board's own tally.** Two numbers about one collection, computed by different routes, never
put side by side — the single arrangement that turns a silent drift into a finding.

**HIS TWO SENTENCES SETTLED THE ARITHMETIC, and no gate did:**

> *"this is exactly 19 i still have missing"* … *"meaning i have 116/135"*

**116 + 19 = 135** ✓ and 116/135 = **85.9%**, which the game truncates to the **85%** on his page.
So the denominator is right and **the board's 118 was two too many** — a drift he caught by eye.

`tv/chronicle_calibrate.py` reads the bar's gold fill as a fraction of its track: structural, no OCR,
no model call, on frames the sweep already has. `_chron_calibration()` runs it on **every sweep** and
puts the verdict in the result.

⚠ **IT IS A WATCHDOG, NOT A COUNTER, and it says so in its own docstring.** On his 2026-08-21 sets
reel the fill reads **0.8395 on four separate frames** (stable, so the reading is repeatable) while
the page's printed digits say 85% — the soft right edge of the fill and the track end-cap are worth
about a point. Tolerance is 3 points: wider than the instrument's own error, tighter than the gap
that matters. A tolerance tighter than the instrument is an alarm that fires on itself.

⚠ **SILENCE IS NOT AGREEMENT.** No bar on any sampled frame reports `ok: None` — *"the game was not
asked, which is not the same as the game agreeing"* — and a board window that does not answer is
reported the same way. [[unknown-stays-unknown]]

⚠ **A CORRECTION I OWE, recorded because I told him the wrong thing first.** I reported that 12 of
the 36 proposed set pieces are ones the game shows as NOT found. That was built on stale data: his
newest reel shows `Natalya's Totem`, `Hsarus' Iron Fist` and `Hsarus' Iron Heel` **with First Found
dates**. The underlying defect is real but different — `notFound` is stored as a bare list of names
with **no page and no timestamp** (`chronicle_retro.py`: `prop['notFound'][ledger]` is a set of
strings), so a May reading can never be aged out by an August one and the gate cannot tell stale from
current. Filed, not half-fixed.

⚠ **AND THE v1853 SCOPE GUARD CAUGHT A NameError IN THIS VERY SHIP.** The first cut called
`_chron_calibration(dirs)` and `dirs` does not exist in that function — the reel list is `reels`. A
name inside a function body resolves only when that line RUNS, so it would have surfaced as "the
sweep crashed at the end", long after the reads were paid for. That is precisely the class that left
MINI dead for ten versions, caught this time before it shipped. [[source-reading-guard]]

## REG-272 — a not-found reading had no page, so the contradiction was invisible (FIXED v1921)

`notFound` has been a bare set of NAMES since it was written — no reel, no frame, no lane, no moment
(`chronicle_retro.py`: `prop["notFound"][ledger]` is a `set` of strings). So when the same piece is
read **FOUND** on one page and **NOT FOUND** on another — which happens constantly, because he keeps
finding things — nothing could say which photographs disagreed, and **nothing computed that they
disagreed at all**.

⚠ **IT COST A WRONG ANSWER TO HIM DIRECTLY.** Told that 12 of his 36 proposed set pieces were ones
*"the game says you do not have"*, the truth was that three of them — `Natalya's Totem`,
`Hsarus' Iron Fist`, `Hsarus' Iron Heel` — carry **First Found dates on his newest reel**. The
not-found readings were simply OLD. A claim built on evidence that cannot be dated cannot be checked,
and I made it anyway.

**Measured over his banked evidence: 26 contested names** — 13 uniques and 13 sets — including
`Immortal King's Will`, the very item he told me hours earlier he does not have. Every one of them
was invisible before this.

Each not-found reading now carries `{reel, frame, lane}` **beside** the existing set (the old field is
untouched, because every reader and gate consumes it and changing it would be a second defect), the
contradiction is computed as `contested`, `merge_proposals` carries the receipts and recomputes it
over the merged evidence, and the sweep prints it:

> ⚔ 26 name(s) were read BOTH found and not-found — the reader disagreed with itself about these,
> and that is worth your eyes before you register

⚠ **THIS MAKES THE CONTRADICTION VISIBLE, NOT RESOLVABLE — and that distinction is the point.**
Deciding which reading is newer needs a timestamp on the sighting, which these do not carry. An older
not-found reading is perfectly ordinary once he has since found the item, so picking a side would be
an invention. It is reported and left to him. [[unknown-stays-unknown]]
[[feedback-contradiction-is-the-finding]]

## REG-273 — cross-referencing his own Remaining page: the proposal is 35 of 36 right, and one row is wrong (MEASURED v1922)

Konyo: *"just did a F-sets MINI SESSION FOR SETS check the last reel session and cross reference is
and see exactly the correct sets i have and make sure the AI READERS are reading them and correctly
tallying and fix what is wrongly counted"*, then *"this is exactly 19 i still have missing"*.

His 25-frame session was the sets Chronicle with the **Remaining** filter on — the game's own list of
what he does not have. **Read by eye, not by a model**, off `reel_s_1787307553811_9452`, and it comes
to **exactly 19**, matching his count.

⚠ **THE GAME LISTS REMAINING PIECES BY THEIR BASE NAME**, not the set-piece name: `Ward`,
`Occult Codex`, `Sacred Armor`, `Bramble Mitts`. The roster records that base in each piece's slot
suffix (`Taebaek's Glory (ward)`, `Laying of Hands (bramble mitts)`), so all **19 of 19** matched
exactly. This is also the reason a reader must never treat a Remaining page as a list of finds — the
board already knows the shape as `base-name-still-to-find`.

Saved as `tv/sets_remaining_2026-08-21.json`.

**CROSS-REFERENCED AGAINST THE PENDING PROPOSAL:**

| | |
|---|---|
| the game says he is missing | **19** |
| the sweep proposes to add | **36** |
| proposed AND consistent with the game | **35** |
| ⚠ proposed but the game says he does NOT have it | **1 — `Natalya's Soul (claws)`** |
| held names that are genuinely missing | 0 (nothing was wrongly withheld) |

So the readers are doing well — **35 of 36** — and the single bad row is now named rather than
suspected. The proposal is safe to register **minus that one**, and v1916's own tooltip already tells
him the write is reversible per item.

⚠ **AND A CORRECTION TO MY OWN EARLIER CLAIM, twice over.** I said 12 of the 36 were pieces the game
shows as unfound; the real number measured against today's Remaining page is **1**. I also told him
he was right that `Immortal King's Will` is not his — **today's game data shows it as FOUND**. Both of
my claims came from `notFound` readings with no date on them (REG-272), which is exactly the defect
that made them unusable as evidence. The lesson is the one already carved: an inherited claim is not
evidence, and a claim built on undated evidence cannot be checked.

**Still open and separate:** the board counts **118** where the game's own arithmetic gives **116**
(116 + 19 = 135). Those two phantoms are in what the board ALREADY holds, not in this proposal — the
two pieces on the 19 that his board does not list among its 17 missing.

## REG-274 — a commit claimed a version it had not stamped (FIXED immediately, v1922)

`bump_version.py` refuses a note containing an apostrophe, because the ship note is written into a
**single-quoted JS literal** in `D2R_BUILD` and an apostrophe would break the page. It said so
clearly — *"apostrophe in note/name would break the single-quoted D2R_BUILD literal"* — and exited
without bumping.

⚠ **AND I PUSHED ANYWAY.** The refusal was one line above a `git commit` in the same command, its
output scrolled past, and a commit titled **v1922** landed on `origin/main` with all four stamps
still reading **v1921** — the half-bumped state the four-stamp rule exists to prevent, arriving by
the one route the rule does not cover: not a partial bump, but a *commit message* asserting a version
that nothing stamped.

Two things, and the second is the general one:

1. Fixed by bumping properly and pushing the stamps, so the ref that says v1922 is v1922.
2. **A refusal printed into a compound command is a refusal nobody reads.** This is the same shape as
   `git push | tail` reporting tail's exit status — the check ran, it was right, and the pipeline
   swallowed it. It had already happened once tonight on this exact tool and I re-ran it by hand;
   the second time I did not look. **Bump, then VERIFY the stamps, then commit — never in one
   breath.** [[feedback-version-numbers-mean-ships]]

## REG-275 — nothing in the pipeline could ever say "you do not have that" (FIXED v1923)

Every reader on this project reads a **found** page and proposes an **addition**. That is the whole
chain: classify, read, normalize, gate, apply. So the count can only ever go UP, and a row that is
on the board and should not be is invisible to all of it — there is no reading in the system capable
of subtracting.

His board said 118/135 = 87%; the game said 85%. Both computed correctly. The board was carrying two
pieces he does not own, and had been long enough that **he caught it by eye before any gate did**.

The game keeps the negative itself: the Chronicle's **Remaining** filter. One recording of it is
worth more than a found page, because it FALSIFIES, it COMPLETES BY SUBTRACTION (135 roster − 19
remaining = the 116 he owns, exactly, by name, with no model call), and it TARGETS the hunt.

`tv/counter_ledger.py`, wired at three points: the sweep flags a denied row, the panel shows it, and
`chronicle_apply` **withholds it on the write path** — because a flag the register button ignores is
decoration. On today's pending proposal it catches exactly one row of 36, `Natalya's Soul (claws)`,
which is the row he was about to register.

**⚠ TIME-ORDERED, and that is the rule rather than a refinement.** A Remaining page is a photograph
of one moment and he keeps playing, so a denial only bites when the page was shot AFTER the
sighting. Three-way split — `denied` / `superseded` (found since) / `undated` (order UNKNOWN, flagged
never denied). Without it the safeguard would start eating the finds it exists to protect.
Guards: `tv/test_counter_ledger.py` (17), `TestV1923TheGameGetsAVetoOnTheWritePath` (5).

## REG-276 — my own guard could not reach the names it was guarding (FIXED before ship, v1923)

The first cut of `denied()` compared proposal names against the Remaining page directly and reported
**"no proposed name appears on the game's missing list (86 checked)"**. A clean pass.

**Zero of those 86 names were roster strings.** The pipeline carries set pieces bare —
`M'avina's Caster` — while the roster and the Remaining page carry them suffixed —
`M'avina's Caster (helm)`. A comparison between two naming conventions agrees no matter what is in
it. Folding both sides turns the same input into the one true hit.

The tell was the count, again: 86 checked, 0 hits, on data I already knew by hand contained one.
[[source-reading-guard]] [[feedback-suspect-the-instrument]]

## REG-277 — three safeguards computed, carried, and never rendered (FIXED v1923)

`calibration` (v1920), `contested` (v1921) and `denial` (v1923) were each built, each attached to the
sweep payload, and **none was ever drawn**. Grepping both UI files for all three returned zero hits.

Two of the three were mine, from the same night. That is the defining property of the class: it reads
as protection from the code side and carries nothing at the only moment that matters — when he is
looking at a green `register 302` button. [[plumbing-with-no-tap]] [[the-unjoined-end]]

## REG-278 — an undefined CSS variable renders as a plausible page (FIXED v1923)

The new strip was styled `var(--st-ok)`. This file's token is `--st-good`. No parse error, no console
warning, no failing assertion — the property simply **inherited**, so the one REASSURING block on the
panel rendered in white and louder than the two real warnings above it. The hierarchy was inverted.

Found only by looking at the pixels. Swept the whole class across both files: of four undefined
tokens, **three were prose** — `--a` and `--rar-rune` appear only inside comments (one quoting the
other file) and `--q-` is a name JS concatenates at runtime. Exactly one was real and it was mine.
A guard that reads its own documentation reports its explanations as defects.
Guard: `TestV1923EveryCssVariableUsedIsActuallyDefined`, comments stripped first.

## REG-279 — a not-found reading was quoted as if it described today (FIXED v1923)

**This one cost a wrong answer to his face.** I told Konyo that **12 of his 36 proposed set pieces
were ones the game shows as not-found**. Three of them carry First Found dates on his newest reel:
those not-found readings were simply OLD, describing a moment before he owned the item. The real
number was **one**.

A not-found reading is not a fact about an item. It is a fact about an item **at one moment**, and it
expires the instant a later look disagrees.

**The code already knew this and did nothing with it.** v1921's own comment, sitting directly above
the offending line, reads: *"an older not-found reading is a perfectly ordinary thing when he has
since found the item."* The line under it compared found-names against not-found-names as flat set
membership. Knowledge in the prose and not in the engine is the same as not having it — the same
shape as REG-277, one layer up.

Fixed in three places:

1. `counter_ledger.resolve_contested` decides each contradiction **by time** — `found` (the
   not-found is older and expired), `not-found` (a real contradiction), `same-moment` (the reader
   disagreed about one picture), `undatable` (**order unknown, never resolved by guess**).
2. `contested` no longer lists a name whose newest look says found. That padding is the defect: a
   contested list swollen with expired readings is exactly how a wrong number gets stated.
3. A proposal now declares its own evidential reach in `notFoundDatable`, and the panel says so.

**⚠ AND THE MEASUREMENT THAT MATTERS:** on his currently banked evidence, **46 of 46** not-found
readings carry no reel and no frame — receipts only arrived in v1921. So every one is `undatable`
and the engine refuses to quote any of them. That is the correct answer and it is also the proof
that my "12" was never supportable by that file. `python3 tv/counter_ledger.py --audit` reports it
and exits non-zero. Guards: `TestANotFoundReadingExpires` (6). [[stale-reading]] [[unknown-stays-unknown]]

## REG-280 — a test spawned his engine and never reaped it (FIXED v1924)

`tv/state.json` grew from **3,867 to 136,116 bytes** during a local gate run, carrying **80 stub
reads** and leaving `readCount: 39` against a `cap: 240` — a test run had spent a sixth of his daily
read budget.

The cause was not the tests writing directly. A suite spawned `tv/tv_diablo.py` as a real
subprocess and never reaped it; it ran for **22 minutes**, writing a stub read into his live state
every ~17 seconds. The proof was in the file itself: `sessionId: s_1787314996559_31332` embeds the
orphan's PID, 31332. Reaped by PID (never `pkill -f`). [[process-port-discipline]]

## REG-281 — the v1869 live-state rule was bound at the wrong time (FIXED v1924)

v1869 established the right rule — when `TV_HIST` points outside his tree, live state follows the
fixture — and computed `tv_diablo.STATE` **once, at import**. Inside a suite the import happens
during collection, so a test that repoints `TV_HIST` in its own body got his real tree anyway. The
redirect looked applied and was not: the same trap, on the same night, that truncated his banked
evidence.

Worse, most suites never set `TV_HIST` at all, so the "default" was his live file. Measured:
`test_agent`, `test_routes` and `test_control` each grew it ~1.7 KB per run, and had been doing so
for as long as they existed. **A default that is safe only when the caller remembers to redirect is
not a default, it is a trap.** `_state_path()` now resolves at call time, an explicit
`tv_diablo.STATE = …` still wins, and under pytest with nothing redirected it lands in a temp dir.

## REG-282 — nothing compared the live files before and after a test run (FIXED v1924)

Both of the above had been happening on **every local run**, silently, because no check ever asked
the only question that matters: *did the bytes change?*

`tv/conftest.py` is a session-scoped autouse canary over the eight irreplaceable files — banked page
reads, the last proposal, the play journal, the visit ledgers. **Every one is gitignored: there is
no git recovery for any of them.**

⚠ The obvious static guard was written first and **returned 26 hits, nearly all correct code** —
`TV_HIST` and `TV_SESSIONS` are read at call time as well as at import, so redirecting them mid-test
genuinely works. A guard with 26 false positives is a guard nobody reads. The canary has none,
because it reasons about no mechanism at all. Seen RED on a planted write.

## REG-283 — the repair fixed one of two surfaces, and MOVED the disagreement (FIXED v1926)

Immediately after the F·Sets count was corrected: *"the daily tasks not synced to the tab F-Sets 116
to 118"*. Reproduced in a browser on his own ledger — **bridge 118, tab 116, same page**.

The repair repainted `renderSetTracker` and `renderForgeSets`, the two SET surfaces. The console's
DAILY TASK FORCE reads `d2r_forgeSummary`, which is written **only inside `forgeScan()`**, reached
through `renderForge()`. Never called, so the tab read live and the bridge served a fossil.

⚠ **v1862 already fixed this complaint once**, from the other end: its comparator decided whether
the bridge is rewritten *at all* and did not include the set count, so a change in sets alone
produced an identical signature. That fix taught the comparator about the number; this one makes
sure the comparator is actually **consulted** after the number moves. Same defect, new door.

**A repair that fixes one of two disagreeing surfaces has not fixed the disagreement — it has moved
it.** [[the-unjoined-end]] [[feedback-generalize-fixes]]

## REG-284 — one chronicle opted itself out of the rule that unified them (FIXED v1926)

*"make sure its a unified CSS between the individual chronicles related."*

The stylesheet already unifies them: `:is(#tab-forge,#tab-funi,#tab-fsets) .fp-fill` gives all three
siblings one gradient, and F·Uniques uses it by passing no colour. **F·Sets passed
`'#4ade80,#86efac'` as an inline style, and inline beats the stylesheet.** Measured side by side:

```
uniques  rgb(95,201,122) -> rgb(143,230,160)     <- the shared rule
sets     rgb(74,222,128) -> rgb(134,239,172)     <- an inline override
```

⚠ **v775 had already found this drift**, unified the sibling TITLE colour, and wrote *"was #4ade80
on Sets"* in its own comment — then left the FILL behind. **Half a class is how it comes back.**

Both now inherit one rule; computed styles are byte-identical. Guard:
`TestTheChroniclesShareOneStyle` — no `_meter` call may pass an inline colour, and it also asserts
the shared rule still exists, because removing the overrides is only safe while there is something
to inherit. Seen RED by restoring the inline gradient.

## REG-285 — the Chronicle bar reader returned a CONSTANT (FIXED v1926)

`chronicle_calibrate.bar_fill` shipped in v1920 as a safeguard with a docstring claiming ±1.5
points. Measured across 36 frames from **three different reels**: it answered **0.8395 on all 14**
and `None` on the rest — one distinct value, which is not a measurement. On a Chronicle page
printing **63%** it said **83.9%**.

Two bugs, and the first is the instructive one:

1. **It picked the row with the MOST GOLD.** In an 882×210 band that row is not the bar — it is the
   "View Rewards" button chrome (316 gold pixels, fragmented) outvoting the bar (208, solid).
   **The discriminator is CONTIGUITY, not quantity:** a progress bar is one run, chrome is pieces.
2. **It walked the unfilled track as "dark"** (`r,g,b < 90`). The track is mid-grey, ~55–110 — and
   so is the panel background beyond it, so the walk ran to the band edge and the denominator became
   the whole band.

Fixed it reads 61.4% where the game prints 63% — 1.6 points, reported as the watchdog it is and
never as the figure. [[feedback-suspect-the-instrument]] [[unknown-stays-unknown]]

## REG-286 — the bar reader was cut by ONE channel unit, and its tolerance is above its own case

Two follow-ons to REG-285, both found by measuring coverage instead of stopping at "it works now".

**(a) `is_gold` required `b < 130`, and the bar's own pixels reach b=131.** The contiguous run was
cut a pixel short on his sets panel, the track walk then ended *behind* the gold, `frac` came out
1.004, and the reader refused — **0 of 25 frames**. The warm/grey split is already done by
`(r - b) > 35`: bar pixels measure r-b **42..61**, the dark track beyond measures **-4..0**. The blue
cap was redundant and load-bearing in the wrong direction. Also clamped `x1 >= xg`: a bar with no
measurable remainder is FULL, not broken.

Coverage after, against the game's printed figure:

```
reel_s_1787307553811_9452    22/25  frames -> 84.4%   [85%]   0.6 points
reel_s_1787307317840_8033   144/148 frames -> 84.4%   [85%]   0.6 points
reel_s_1786385768689_67392  198/217 frames -> 61.4%   [63%]   1.6 points
```

Two reels now return two different numbers — the property the old reader did not have.

**(b) ⚠ `TOLERANCE = 0.03` IS ABOVE THE DEFECT IT EXISTS TO CATCH.** His board read 118/135 = 87.4%
against a printed 85%: a **2.4-point** gap, *inside* a 3-point tolerance, verdict "agree". The
comment it replaced claimed the tolerance sat "below the gap that matters" — the gap that mattered
was smaller than the tolerance. [[feedback-threshold-above-the-ceiling]]

**It is deliberately NOT tightened.** The reader is only good to ~2 points itself, so a 2-point
tolerance fires on its own noise, and a gate that cries wolf is a gate nobody reads. The right
instrument for a small gap is `counter_ledger` — exact, and it NAMES the rows. Keep both: the bar
needs no session and catches gross drift; the Remaining page needs a recording and catches two rows.
Recorded as a test so the limit is a fact, not a surprise.
Guard: `tv/test_chronicle_calibrate.py` (10), registered in `run_gates.py`.

## REG-287 — v1925 wrote two ledger statuses and never told the thing that renders them (FIXED v1927)

The ledger repair records `removed` and the write guard records `refused`. Neither was in the panel's
`PILL` map, so both fell through to the bare-status fallback and rendered as **plain dim text
beside a green "✓ ticked"** — a row that CHANGED his grail reading quieter than one that merely
confirmed it, which inverts the whole point of the changed/confirmed split shipped in the same
version. Seen on the rendered panel, not in the source.

Both now have pills (`⛔ taken out`, `⛔ kept out`). Guard: `TestEveryLedgerStatusHasAPill` — every
status written through `kaiChronicleRecord` must have one. Seen RED by deleting the `removed` pill.

⚠ **The guard's first draft grepped a bare `status: '...'` and reported six defects that were not
there** — `farm`, `hunt`, `idle`, `now`, `pipe`, `queued`, belonging to entirely different
subsystems this panel never renders. Scoped to `kaiChronicleRecord` call sites, plus an assertion
that it found any at all, so it cannot pass by matching nothing. [[source-reading-guard]]

## REG-288 — a runnable module had its own code below the `__main__` guard (FIXED v1929)

`vault_corpus.py` grew an inventory block appended **below** `if __name__ == "__main__": sys.exit(main())`.
The guard runs first, so `main()` executed while `INV_SAMPLE` did not yet exist and a **145-second**
corpus scan died with `NameError` on its final line, after every frame had been read.

⚠ **The same shape had already bitten this session**, in `tv/test_control.py`, where appended classes
sat below the runner and were never collected. `TestRunnerIsLast` caught that one — it covers test
files. Nothing covered the RUNNABLE MODULES.

⚠ **And the scope guard passed.** `TestNoFunctionLoadsAnUndefinedName` asks whether a name EXISTS,
not whether it exists **yet**: `INV_SAMPLE` is a perfectly good module global, defined twenty lines
too late. A guard can be right about its own question and blind to the failure standing next to it.
[[feedback-generalize-fixes]] [[feedback-blind-fixture-green-gate]]

Guard: `TestV1928NothingRunnableLivesBelowTheRunner` over nine runnable modules, plus a
planted-offender calibration so a check that can no longer see one fails rather than passing quietly.
Seen RED on the real defect (`vault_corpus.py:224 Assign is defined BELOW the __main__ guard at :221`).

## REG-289 — the inventory detector was built, guarded, and called by nothing (JOINED v1929)

`inventory_lattice` / `inventory_occupancy` / `inventory_reading` shipped with 13 tests and **zero
callers** — the exact defect class this whole arc has been about: a mechanism that reads as
protection and carries nothing.

Joined to `vault_corpus.main()`, which already scans the archive. It now reports free inventory space
per reel, sampling 8 panel frames each (corroboration, not volume) and printing **how many agreed**,
because 93 of 94 is evidence and 1 of 1 is a fixture. Measured across his archive:

```
reel_s_1784984019250_95276    18 free of 40   (8 of 8 agreed)
reel_s_1785078127173_28278    18 free of 40   (8 of 8 agreed)
reel_s_1785708285647_38665    11 free of 40   (2 of 2 agreed)
reel_s_1787244002054_15361     8 free of 40   (6 of 6 agreed)
reel_s_1787243026006_12211     1 free of 40   (2 of 3 agreed; 1 disagreed)
```

Six of sixteen reels hold a readable inventory; the other ten say **"no frame held a readable
inventory panel — which is not the same as an empty inventory"** rather than printing 0 free.

## REG-290 — seven payload keys no UI ever read, and two of them were mine (FIXED v1930)

Sweeping the chronicle sweep RESULT payload against both UI files, comments stripped, found **seven
keys nothing has ever read**. Two mattered:

- **`newlyDated`** (v1846) — the finds whose **in-game** date is newer than anything read before this
  sweep. That is precisely what he asked for: *"the items need to eventually be timestamped to the
  ingame finding … (NOT WHEN THE AI REGISTERED IT)"*. Computed for eighty versions, shown nowhere.
- **`contestedExpired`** (v1923, mine) — names dropped from the contested count because the newest
  look says found. Without it a row he saw flagged silently stops being flagged and nothing says why.

⚠ **`contestedExpired` shipped in the SAME COMMIT that fixed `calibration`, `contested` and `denial`
for this exact defect.** Fixing three instances of a class and shipping a fourth is how a class
survives being fixed. [[feedback-generalize-fixes]] [[plumbing-with-no-tap]]

`contestedResolved` (also mine) drove no decision and is **removed from the payload** rather than
rendered — it is derivable, and an unread key is the thing being swept for.

⚠ **The first sweep was unscoped and returned 153 keys** — subprocess kwargs, HTTP headers, platform
strings. A finding too large to act on is noise; scoped to the result payload it returned 7.
[[sweep-dont-ask]]

## REG-291 — `\U` is not a JavaScript escape (FIXED v1930)

The new block's icon was written `'\U0001f5d3'`. JavaScript understands `\uXXXX` and `\u{...}`, not
uppercase `\U` — so the panel rendered the literal text **`U0001f5d3 2 find(s) carry…`**. The JS
syntax gate passed (it is valid JS, just not the escape intended) and no text assertion would have
caught it. Found by looking at the rendered strip. Swept both UI files for siblings: none.

## REG-292 — a gate that only runs when one file changes hid a failure for seven versions (FIXED v1930)

`hooks/pre-push` runs the console demos **only when `tv/control_ui.html` is in the diff AND the
console app is up**. v1930 touched that file with his console running, so the gate fired for the
first time in a while and blocked the push on **J9 TERROR ZONE FLAGSHIP**.

Bisected: **J9 fails on v1924, v1925, v1926, v1927, v1928 and v1929 — every one of which pushed
clean**, because none of them touched `control_ui.html`. *A gate that always SKIPS is the same
defect as one that always passes.* [[feedback-blind-fixture-green-gate]]

**Both failures were mine, and both were HIS later instructions the demo had not caught up with:**

- **`firstCard`** asserted `zone.children[1] === el` — silently assuming nothing would ever sit
  between the zone banner and the flagship. v1914 put `#chron-waiting` there, the "N finds waiting
  to register" line he asked for on the tab he lives on. Measured children:
  `[zone-banner, chron-waiting, hd-tz, hd-taskforce]`. The flagship is still the first **card**; it
  is no longer the second **child**. Now compared against the cards, so a notice line cannot fail a
  layout gate.
- **`thinRoutes`** asserted a thin zone stays clickable — **a decision he has now reversed three
  times.** v1588 inert → v1801 clickable ("a lock over most of the map stops informing him of a
  ranking and starts overruling him with one") → v1915 inert again, in his own words: *"only the TZ
  ZONES worth farming should be clickable and routable."* The assertion is not a bug that appeared;
  it is a recorded expectation his instruction superseded. Updated to assert the current rule —
  `role=button`, `aria-disabled="true"`, no `onclick`, `cursor:not-allowed` — which is a **stronger**
  check than the one it replaces.

9/9 demos green.

⚠ **The remaining hole is the trigger, not the assertions.** The demos still only run on a
`control_ui.html` diff with the app up. That is deliberate (never block on an environment the push
did not break) and it is why this sat unseen for seven versions. Worth revisiting: run them on any
`tv/` UI change, or report loudly when they SKIP so a skip is visible rather than silent.

## REG-293 — the skip is now loud (FIXED v1931)

Follow-on to REG-292. The trigger stays narrow deliberately — never block a push on an environment
the push did not break — but the **silent** skip is gone. Both branches now announce themselves, the
file-unchanged branch counts how many commits have passed since `tv/control_ui.html` last moved, and
both say how to run the demos by hand.

*"We chose not to run this"* and *"this passed"* must never look the same.
Guard: `TestNoGateSkipsSilently` (3), seen RED.

## REG-294 — a set PIECE was being read as a SET, five times in his banked evidence (FIXED v1932)

Class-4 sweep (a guard that cannot reach its subject), run by measuring the **overlap** between
every name-set the pipeline holds and the roster it is judged against. The table is the finding:

```
source                        n   vs SET roster   vs UNIQUE roster
board.setPieces             119        118              1     <- Blood Crescent (already fixed)
evidence.sets                86          0              0     <- bare vs suffixed (folds: 85/86)
evidence.setGroups           38          0              0     <- a set is not a piece; 0 is correct
evidence.notFound.uniques    32          0             11     <- the rest are BASE names (correct)
game.remaining               19         19              0
```

Reading `setGroups` properly turned up the real defect: **5 of its 38 keys are PIECE names, not set
names** — `M'avina's True Sight` (a helm) keyed as a set carrying `M'avina's Icy Clutch` and
`M'avina's Tenet`; `Cleglaw's Claw` (a shield) carrying `Cleglaw's Pincers` and `Cleglaw's Tooth`.
The reader grouped rows under a **row** instead of under the heading.

`setGroups` alone is harmless — no UI reads it. **`completeSets` is the one that bites:** a set the
panel calls complete is ONE ROW WORTH FIVE PIECES, expanded by the board. A piece accepted there
would tick pieces he does not own from a single misread heading. It has not happened yet
(`completeSets` is empty on his evidence), which is exactly when a guard is cheap.

Refused OUT LOUD and with its receipt (reel + frame), and printed by the sweep — a silently dropped
group is indistinguishable from a page that held none.

⚠ **The guard's first cut had the defect it was written about.** It stripped the slot suffix from
the ROSTER and compared the raw input, so it caught `M'avina's Tenet` and missed
`M'avina's Tenet (belt)` — the same two-conventions gap, inside the guard. Caught by its own test.
[[source-reading-guard]] Guards: `TestV1932APieceIsNotASet` (5), seen RED.

## REG-295 — the uniques ledger, audited: 5 stray rows, and NONE of them cost him a find (v1933)

Symmetric audit of `d2r_foundLog` against both rosters. 389 rows: 265 uniques, 119 set pieces
(they live in both stores by design, v644), **5 matching neither**. Measured, not guessed:

| row | verdict |
|---|---|
| `Atma's Scarab` | roster spells it `Atma’s Scarab` — a **curly** apostrophe. Both `_norm`s fold `‘’ʼ` → `'`, so it **resolves**. Not debris. |
| `Saracen's Chance` | same |
| `Naglring` | a misread of `Nagelring` — and **`Nagelring` is also in his foundLog**, so it is a duplicate, not a lost find |
| `Athena's Wrath (set piece)` | same: the real name is also present |
| `Cow King's Leathers (set)` | a SET NAME sitting in the uniques ledger |

**His 267/403 is right and nothing here changes it.** `funiScan` counts against the roster, so a
row that resolves to nothing cannot inflate it, and the two names that *could* have been lost are
present under their real spelling. The uniques write path is already guarded — it writes only when
the name resolves — so these are historical rows, not an open leak.

⚠ **The unique roster uses BOTH apostrophe forms**: 83 straight, 4 curly (`Atma’s Scarab`,
`Saracen’s Chance`, `Seraph’s Hymn`, `The Cat’s Eye`). The set roster uses only straight. Every
comparison in this pipeline goes through a `_norm` that folds them — but an exact-match comparison
written in future would silently miss those four. Recorded rather than "fixed": normalising the
roster risks breaking matches against what the readers actually print.

**REPORTED, NOT REMOVED.** Deleting grail rows that cost him nothing, to tidy a number that is
already correct, is an unasked-for edit to his history. `_chRepairLedgers` now returns `debris` and
touches none of it. Guards: `TestTheUniquesLedgerIsAuditedNotEdited` (3).

## CLASS-3 SWEEP CLOSED — every API payload, and what was deliberately left alone (2026-08-21)

Completing the sweep begun in REG-290, which covered only the chronicle sweep result. Extended to
**every `self._json(...)` response payload** in `tv/control_app.py`, comments and docstrings
stripped, matched against both UI files.

**54 payload keys across all routes; 7 read by no UI.** Each was inspected rather than counted:

| key | route | verdict |
|---|---|---|
| `nav`, `spawned` | `/api/board` | **by design.** v781 stopped the UI calling this route ("that spawned a second native window") and does the nav in-document. Kept as the explicit `?popout=1` escape hatch, and it has tests. Not a defect. |
| `dup`, `retry_s` | intake | intake internals: a duplicate-record flag and a 429 rate-limit hint on a receiver the UI does not call. |
| `hist`, `kaiVerTarget`, `vision` | diagnostics | path echo, an internal version target, per-row vision data. |

**Nothing further to fix, and that is the finding.** The two keys that mattered (`newlyDated`,
`contestedExpired`) were wired in v1930 and one was dropped; the rest are either deliberate or
diagnostic.

⚠ **One instrument note, because it produced a wrong attribution mid-sweep.** Locating a key's route
by "the last `path == "/api/…"` before this line" is unreliable with nested handlers — it filed
`dup` and `retry_s` under `/api/identity_name` when both are intake keys. The claim was checked
against the surrounding code and corrected before it went anywhere.
[[feedback-suspect-the-instrument]]

## REG-296 — a keeper could not name the photograph it came from (FIXED v1934)

Konyo, on a small charm in his MAGIC locker: *"it wrongly muled a random charm.. i dont think i even
own this.. from what picture is this here?"*

He could not check, and neither could the board. A `d2r_magicFinds` row carried
`{q, base, mods, verdict, score, checkedAt}` — **no frame, no reel, no session** — while the keeper
card said *"Stats read from your screenshot."* A claim its own data could not support.

⚠ **THE RECEIPT WAS ALREADY IN SCOPE.** Thirty-seven lines above the writer, the same function
(`aicJudgeApply`) builds `prop` for `kaiChroniclePropose` carrying `frameId`, `sessionId` and
`firstSeenTs` from `meta` — **uses them for the chronicle, drops them for the vault.** Two halves of
one read, one of which remembers where it came from.

The asymmetry is the tell: the tally lane (runes/gems/materials) has keyed its durable ledger on
`sid|frameId|name` since **v889**. Keepers went through a different door and lost it.
[[the-unjoined-end]]

Fixed: the writer records `frameId` / `sessionId` / `at`, and the card **names the frame**. Rows that
predate this carry nothing, and the card now says so rather than repeating the claim — *"no source
frame for this one, so it cannot be traced back. Untick it if you do not own it."* An item whose
source cannot be produced is exactly the one he is right to distrust. [[unknown-stays-unknown]]

⚠ **The provenance branch first used `esc`, which is not in that scope.** Only the WITH-frame case
reaches that line, so it threw `ReferenceError` on exactly the case the feature adds — and passed on
the case that already existed. **Testing both branches is the only reason it was caught.**
Guard: `TestAKeeperCanNameItsPhotograph` (3).

⚠ **The second writer still has no provenance.** A different vault path takes its rows from a finds
list with no frame in scope. Named here rather than half-fixed: it is a separate seam and it is not
the one he was looking at.

## REG-297 — the "second writer with no provenance" had BETTER provenance all along (FIXED v1935)

v1934 fixed the aic-judge writer and **named this one as unfixable — "no frame in scope"**. That was
wrong, and it was wrong because I stopped at the first look instead of walking out to the enclosing
function.

`processFile(i, _retry)` holds **`fname`** — the uploaded screenshot's filename — and
`_vPutShot(fname, …)` has been stashing the **full-res image in IndexedDB under that same key since
v365**, for click-to-enlarge. So this lane can not only name its source, it can **show** it. The
receipt existed, was already keyed, and the row dropped it.

The keeper card now distinguishes **three** states, and collapsing any two is how a claim outlives
its evidence:

```
· frame f_1787307574509                                    read from a reel
· Screenshot 2026-08-21 at 18.44.12.png (full-res stored)  read from an upload — openable
  no source frame for this one … untick it if you do not own it   predates provenance
```

⚠ **The lesson is about the earlier finding, not this fix.** "No frame in scope" came from a regex
that walked *up* a few lines and hit `_sleep` — a red herring. Walking out by brace depth found the
real enclosing function immediately. **A negative claim deserves the same measurement as a positive
one**; I published "unfixable" on a worse instrument than the one that found the answer.
[[feedback-suspect-the-instrument]] Guard: 2 more in `TestAKeeperCanNameItsPhotograph`.

## CLASS-6 SWEEP — one real instance, and 449 candidates that were noise (v1936)

The last unswept class from the hardening brief: *a comment that asserts a rule the adjacent code
does not enforce.*

⚠ **The broad sweep is useless and saying so is the finding.** Matching strong assertions
("must never", "always", "can never") above code returned **449 candidates** across `tv/*.py`, and
inspection of the first twenty found every one to be ordinary prose using "never" descriptively.
A finding too large to act on is noise. [[sweep-dont-ask]]

**The one real instance came from following a known scar instead**, `STILL_MAX_DIFF` in memory:

`CHRON_STILL_MAX_DIFF` is **0.002**. The v1712 calibration table three lines above it still read
`0.005 ← chosen`. v1758 had moved the constant — correctly, with its evidence immediately *below* —
and nobody updated the table above. **Two statements about one number, three lines apart,
disagreeing.**

Nothing was broken: the code is right. What was broken is the instruction to the next reader, who
sees `0.005 ← chosen` beside `= 0.002` and helpfully "fixes" a deliberate decision back to the
comment. **I nearly did exactly that**, which is the only reason it is written down.
[[label-outlived-referent]] [[feedback-comments-vs-code]]

Guard: `TestV1936ACalibrationTableCannotOutliveItsConstant` — a `← chosen` marker must name the live
constant or say it is history. Seen RED by restoring the stale marker.

⚠ The guard's own first draft used `io.open` in a suite that does not import `io`. The guard about
stale comments failed on its own missing import. Caught by running it.

## REG-298 — my repair mutated another spec's fixture, and only CI caught it (FIXED v1937)

v1925's ledger repair runs on load and removes rows the game's Remaining page lists as missing.
`tests/v1692_tally_counts_the_chronicle.spec.ts` seeds **110** set pieces — including
`Natalya's Soul (claws)` and `Sazabi's Ghost Liberator (balrog skin)`, the exact two — and then read
**108 of its own fixture**.

⚠ **The pre-push smoke does not run that spec. Routine I did.** Six versions of Routine I show
`cancelled` (superseded by the next push) with one `failure` in the middle — a red full-suite run
that no local signal reproduced, because the local subset never touches it.

⚠ **AND THE MECHANISM TO PREVENT THIS ALREADY EXISTED.** `tests/_oneshots.ts` derives every
boot-apply guard **out of bible.html** by the pattern `d2r_v<version><Thing>Applied`, so a spec can
boot as a *later* load. It was written because a hand-listed version went stale and reported *"the
app MUTATED his ledger"* about a correct apply — the same failure, one ship earlier.

`d2r_setRepairAt` does not match that pattern, so the suppressor could not see it. Fixed by naming a
second guard correctly — and the spec then passed with **zero spec changes**, because the suppressor
derives it from source.

Two keys, two questions, and conflating them is what cost the CI round-trip:

```
d2r_setRepairAt                    WHICH READING did this act on   (staleness)
d2r_v1925RemainingRepairApplied    is a SPEC booting a later load  (suppression)
```

⚠ **Suppression covers the game-Remaining apply only.** The unique-in-the-set-store branch is NOT
suppressed: "this is a unique" is a structural invariant, not a one-shot decision, and it does not
go stale. Measured — his board removes 3, a suppressed spec removes 1.
[[the-unjoined-end]] [[feedback-blind-fixture-green-gate]]

## MEASURED, NOT FIXED — Routine I produces a verdict about once in sixty runs (2026-08-21)

Reading **every** CI workflow's history, not just the convenient ones:

```
Routine G  clean 9/9      Routine J  clean 9/9      Publish   clean 9/9
Routine H  clean 9/9      Routine K  clean 9/9      Routine L clean 9/9
📺 agent tests   6 failures — v1928..v1933, ALL FIXED by v1934's pathguard (green since)
Routine I        1 completion in 12; 10 cancelled
```

`concurrency: cancel-in-progress: true` on `routine-i-${{ github.ref }}` means each push kills the
running suite. Measured across 39 push-triggered runs: **36 of 38 gaps are under an hour, median 18
minutes** — shorter than the suite takes. The nightly scheduled run shares the group deliberately
("never doubles up with a late-evening push") and so is cancelled too.

⚠ **THE HONEST READING IS THAT THIS IS MOSTLY MY FAILURE, NOT THE CI'S.** The config says plainly
*"only the newest commit's verdict survives"*, and that design works — the last push does complete.
**v1933's Routine I DID complete, with a failure, and I pushed four more times without reading it.**
The gate produced its verdict and nobody looked.

The secondary property is still real and worth him knowing: at an 18-minute push cadence the full
suite rarely reaches a verdict, so a cross-spec regression can survive several ships. The
pre-push smoke is 13 specs; Routine I is the whole suite.

**NOT CHANGED.** The obvious fix — splitting the concurrency group by event so the nightly survives
— was written, then reverted: it lets a push and the schedule run two full suites at once, which
costs CI minutes and contradicts a documented decision. That is his money and his call. Options if
he wants one: split the group by event (one guaranteed verdict a day, more minutes), or leave it and
**read Routine I before the next push** — which is what the design already assumes.

## REG-299 — the load-time repair raced a simulation mid-loop (FIXED, test-side)

Caught by reading Routine I **while it was still running**, one job at a time, instead of pushing
past it: `slow 2/2` failed with

```
NOT TALLIED:        Natalya's Soul (claws)
NOT DATED:          Natalya's Soul (claws)
NOT RESTORED:       Natalya's Soul (claws)
LEDGER NOT ERASED:  Natalya's Soul (claws)
```

`tests/v645_every_item_sim.spec.ts` ticks every missing set piece and checks the store immediately.
v1925's repair fires **400 ms after `load`**, so on a loaded CI runner it lands **mid-loop**: the
tick writes, the repair strips (that piece is one of the 19 the game says he does not have), and the
check reports four failures for one row.

**An async mutation on a timer races anything that touches the same store.** On his board that is
invisible — he clicks slowly. In a simulation it is a coin flip, which is why it passed locally and
failed on CI.

Fixed test-side: the spec boots as a **later load** via `suppressOneShots()` — the mechanism
`_oneshots.ts` exists for — because it is measuring the tick lifecycle, not boot applies. The
structural rule (a unique may never sit in the set store) is **not** suppressed and still runs.

Verified: the whole `slow` project, **58 passed**, locally, BEFORE pushing — rather than discovering
it on the next CI round-trip, which is what the previous four ships did.

## REG-300 — the count he asked for landed, then his first click undid it (v1925→v1938, FIXED v1939)

`_chRepairLedgers` wrote `d2r_setPieces` to storage and never touched the live in-memory
`setPieces` Set. `persist()` serialises `[...setPieces]` over the top of that key, and `persist()`
runs on virtually any board interaction — a set tick, a rune, a boss filter, a stash edit.

**MEASURED, end to end** (`tests/v1938_remaining_repair_outcome.spec.ts`):

```
roster 135 -> repair -> 116   correct, and this is where every guard stopped looking
   -> un-tick ONE unrelated piece -> 134   all 19 back
```

So F·Sets showed the 116/135 he asked for — *"fix the 118/135 to 116/135 i want to see it fixed!"* —
and reverted to 134 the moment he touched anything. **Fourteen ships carried it, v1925 through
v1938**, and every guard written in that window stayed green, because each read the store
immediately after boot and nothing ever clicked. A gate that never interacts cannot see a defect
that only appears on interaction.

⚠ **THE RULE ALREADY EXISTED, ELEVEN LINES FROM CODE THAT OBEYS IT.** v684 wrote it into the seed
floor: *"sync the LIVE in-memory Set too ... otherwise the first persist() rewrites d2r_setPieces
from the stale pre-seed Set and clobbers every floored piece."* The floor obeys it. The repair was a
second writer to the same store that never read the first writer's warning.

**THE CLASS, SWEPT — AND THE FIRST SWEEP WAS TOO NARROW.** I first checked the 15 writers of
`d2r_setPieces` / `d2r_owned` / `d2r_foundLog` and called it closed. But the exposure is not those
three keys: it is **every key `persist()` writes**, because `persist()` is what does the clobbering.
`persist()` writes **21**. Checking 3 of 21 and reporting a closed class is the same mistake in
miniature — the count is the tell.

All 21 swept. Nine have a writer outside `persist()`, and every one of those nine is safe by one of
three mechanisms:
  * it serialises FROM the live structure (`owned` x3, `copies`, `multiKeep`, `magicFinds` x5,
    `ethereal`, `superiorBases`, `unknownReads`, `rwMade` x4);
  * it mutates the live structure and THEN writes (`chronicleReset` sets `rwMade = {}` on the line
    above its storage write; the `_UNI_EXTRA` strip deletes from the Set first; the v684 floor);
  * it writes and then RELOADS the page (the grail-import path, which says so in its own comment).

The repair was the only writer in the file that did none of the three. `d2r_foundLog` carries no
live mirror — every reader re-parses it — so it is not exposed to this at all.

**Second symptom, same cause:** ticking a repaired-away piece back "did nothing". The stale Set
still contained it, so `toggleSetPiece` took the *delete* branch instead of *add*.

Guard: `tests/v1938_remaining_repair_outcome.spec.ts` — un-ticks one unrelated piece after the
repair and requires 115, seen RED at 134 before being trusted.

## REG-301 — the price tag that took seven minutes (FIXED v1941)

Konyo: *"vault accumaltor i click this it says grouping frames.. what does it do and mean?"*

It is the dry-run price tag — what a vault sweep WOULD cost, no model call, nothing written. It was
not looping. `vault_scan_cost()` probes every frame through `stash_screen_open()`, a crop plus an
OCR. **MEASURED on his own film: 0.118s x 2699 frames across 1065 sealed reels = ~7.4 MINUTES**, no
progress, no timeout. `curl` against his live console returned `http=000` after 90s. "costs nothing"
on that button was only ever about MONEY.

Three fixes: the per-frame gate verdict memoised on `(size, mtime)` so a rewritten frame MISSES
rather than lying (1367x, survives a restart); the quote itself memoised on the sealed-reel set
(first call 414s, second **0.087s**, identical answer); and the button now ticks the seconds with a
3-minute bound, because one static label looked the same at 5 seconds and at 7 minutes.

Guard: `tv/test_gate_cache.py` — the test that matters plants a deliberately WRONG verdict, rewrites
the file underneath it, and requires the memo to miss.

## REG-302 — a stamp outlived its effect and froze F·Sets at 117 (FIXED v1942)

Konyo, after v1939 was supposed to have fixed this: *"still it read 117! insted of 116/135"*.

`doneThisReading` INFERRED his intent from a timestamp: "the repair already ran against this
reading, so anything still ticked must be his doing." False on his board, because of REG-300 —
v1925..v1938 removed the piece from storage and `persist()` wrote it straight back. **The effect was
undone; the stamp survived.** So the repair believed it was done, refused to act, and the wrong
count froze in permanently. v1939 stopped the undoing but could not un-stamp history.

Fixed by recording instead of inferring: `d2r_setRepairKept` holds the pieces he has explicitly
ticked back, written by `toggleSetPiece` — the only place his intent exists. In it = his ruling,
outranks the game page for good. Not in it and reappeared = not his doing, corrected every load.
Un-ticking withdraws the ruling. Strictly stronger than the stamp, and **self-healing**: any future
defect that puts a piece back is corrected next load instead of frozen in by a receipt for work that
no longer exists.

Guard: a fourth test in `tests/v1938_remaining_repair_outcome.spec.ts` reproducing his exact frozen
state — all ticked, stamp set, nothing recorded — requiring 116; and its inverse, that a deliberate
re-tick survives a reload.

---

## REG-303 — a curly apostrophe split three major sets across four mules

Found while measuring, not reported: `tvVaultRegister('Battlecage')` filed to UNI-WEAPONS, and
Rattlecage is a Cuirass. Pulling that thread found the larger one underneath it.

**The board treated `’` and `'` as different items.** `findSetPiece` and `tipOf` resolve through the
global `_norm`, which lowercased, stripped parens and collapsed whitespace — and never folded the
curly apostrophe. So a set piece read with one matched nothing at all and fell past every set rule
in `suggestMule` to its last line, `default: weapons`:

| read as | went to | belongs in |
|---|---|---|
| Griswold’s Redemption | UNI-WEAPONS | SETS-TAL-IK |
| Immortal King’s Soul Cage | UNI-WEAPONS | SETS-TAL-IK |
| M’avina’s True Sight | UNI-WEAPONS | SETS-REST |
| Tal Rasha’s Adjudication | SHARED STASH | SETS-TAL-IK |
| Horazon’s Splendor | UNI-WEAPONS | SETS-REST |

**AND THE TABLE ABOVE WAS THE SMALL HALF.** Swept across every apostrophe-bearing name the board
knows — **206** of them, and **119 of his 135 set pieces carry one** — **158 routed to a different
mule depending on which apostrophe byte was read.** After v1958: zero.

(The first sweep said 39 of 87. It read `window.SETS`, which does not exist on the page, so it
silently measured uniques only and undercounted by four times while looking healthy. The figure
above comes from `__setPieceNames()`, the accessor findSetPiece itself resolves through.) The 39 include Andariel's Visage, Arkaine's Valor,
Arreat's Face, Nightwing's Veil, Ormus' Robes, Skullder's Ire and Thundergod's Vigor — all body
armour or helms, all landing in UNI-WEAPONS when read with a curly apostrophe.

One of the 39 is worse than a misfiling. **`Gheed's Fortune` went from `__keep` to `uni-weap`** — the
KEEP_IN_INVENTORY rule, whose whole purpose is that the charm only works on the character actively
playing, was bypassed by the apostrophe. Muling it is not a tidy-up error; it is moving the item
somewhere it does nothing.

Three major sets split across four mules, under a roster note in this file that reads *never split a
set*. Every straight-apostrophe form routed correctly the whole time — the difference is one byte,
and OCR emits both.

**THIS WAS HALF-SEEN FOUR DAYS AGO, IN REG-295.** That audit found the same fact — *"the unique
roster uses BOTH apostrophe forms: 83 straight, 4 curly"* — and concluded: *"Every comparison in
this pipeline goes through a `_norm` that folds them, but an exact-match comparison written in
future would silently miss those four. Recorded rather than fixed."*

Both halves of that sentence were right about the LEDGER pipeline and neither was checked against
the ROUTING one. There are two `_norm`s in this file. The v1794 resolver folds; the global one — the
one `findSetPiece` and `tipOf` use, and therefore the one `suggestMule` decides mules by — did not.
So the danger REG-295 correctly identified was not hypothetical and not in the future: it was
already live, in a pipeline the audit never named, and it was the larger of the two by far. The
lesson is about scope, not vigilance — *"this pipeline"* was doing load-bearing work in that
sentence and nobody asked which pipelines there were.

**Only the board had failed to learn it.** `tv/chronicle_resolve.py:80` has folded `’` to `'` since
2026-08-18, and this file's OTHER `_norm` (the v1794 resolver) folds `‘’ʼ` too. One name was one
item to the console and two to the board — the two-halves shape, silent by construction.

Not hypothetical damage: the v440 comment beside `_KEEP_SET` records that his four Horazon's pieces
were once wrongly discarded as junk, and Horazon’s Splendor is in this table.

**Fixed in two places because there are two mechanisms, not because the rule is written twice.**
The global `_norm` now folds the character, which repairs everything that resolves through a
normalizer — four of the five above. It could not repair Horazon’s Splendor, whose slot is decided
by `tipOf`'s EXACT-KEY lookup; an exact-key map cannot be taught to fold a character, it can only be
handed a name that already has. So `suggestMule` also repairs the name once at its top, ahead of
every branch. Measured after both: 5/5 route identically to their straight forms.

**And the misread half.** `suggestMule` now folds an unresolved name onto the roster the way the
inbox has since v1794 (`Battlecage` → routed as `Rattlecage` → UNI-ARMOR), naming the repair in the
`why` rather than relabelling the tile. Measured conservative across 14 names: only genuine slips
move; Blood Shield, Horazon's Splendor, Grand Charm, Larzuk Helm Base and every other RotW custom
fold to null and route exactly as before. A real find of his that is not on the roster must never be
dragged onto a roster name that resembles it.

**Left for him, deliberately.** A name nothing recognises still parks in UNI-WEAPONS, because there
is no unsorted mule and inventing one would ask him to make a character in game. Only the wording
changed, from `default: weapons` to a reason that says it is a park rather than a classification.
An unsorted drawer is his call.

**IT WAS LIVE ON HIS BOARD, not a constructed example.** Five of his real stores hold curly
apostrophes right now — `d2r_chronApplied` (14), `L·d2r_grailFarm` (3), `d2r_gameFound` (2),
`d2r_chronicleInboxLog` (2), `d2r_grailFarm` (2) — and the names are four amulets: **Atma’s Scarab ·
Saracen’s Chance · Seraph’s Hymn · The Cat’s Eye**. Measured against the pre-v1958 file, all four
routed to **UNI-WEAPONS**; after, all four reach **UNI-SMALL**, where his rings and amulets live.

These are the same four names an earlier check in this session reported as missing from the roster,
twice, because it searched with a straight apostrophe. The board had folded them all along and the
tooling had not — which is the defect and its own misdiagnosis wearing the same byte.

Guard: `tests/v1958_apostrophe_and_misread_routing.spec.ts` — three tests. The first derives every
apostrophe-bearing name from the board's own tables at runtime and asserts the RULE (curly routes
where straight routes) rather than a five-name snapshot, so names added later are covered; it fails
on 40+ names with v1958 reverted.

---

## REG-304 — the en-dash: the same gap one character over (v1959)

REG-303 fixed the apostrophe. The v1794 resolver also folds `–—` to `-` and the global `_norm` did
not, so an en-dash read broke identically. Measured on the 13 hyphenated names the board knows:
**10 routed differently** — the whole **Trang-Oul** set (a class endgame set `_KEEP_SET` exists to
protect) plus Tal Rasha's Fine-Spun Cloth, every one to UNI-WEAPONS.

Fixing only the apostrophe would have closed the class on paper and left an identical defect behind
a different byte. Swept afterwards for further classes: across all 533 board names the ONLY
non-ASCII character is U+2019 (4 occurrences). Nothing else to fold.

## REG-305 — a byte-repair's `null` is a verdict, not a miss (v1959)

Found by reviewing my own v1958 after it shipped, which is the whole point of the post-ship pass.

`suggestMule` returns `null` in exactly one place — `if (isSharedStash(name)) return null` on its
first line — so `null` means **shared stash, never mule**. v1958's repair hop accepted the result
only `if (_as && _as.id)`, which threw that verdict away and fell through to route the *unrepaired*
name to a mule.

`SHARED_STASH_RE` anchors five names each carrying a straight apostrophe — the Sunder charms
`talic's anguish`, `korlic's pain`, `madawc's ire`, `bul-kathos' nightmare` (also a hyphen),
`worusk's end`. Read with the other byte, **all five routed to UNI-WEAPONS instead of the shared
stash.** It measured identically before v1958, so it was not introduced there — but the hop had the
answer in its hand and discarded it because the answer was falsy, which is worse than not looking.

The fuzzy roster fold below it deliberately keeps the `&& _fs.id` form: a *guessed* name may not
speak for an item confidently enough to suppress its filing. The byte repair is exact; the fold is
not. Guard: a fifth test in `tests/v1958_apostrophe_and_misread_routing.spec.ts`.

## REG-306 — three rows that said the wrong thing about what happened (v1959)

He asked for a ledger he could read surgically. These are the rows that lied to it.

**A throw-out read as a vault registration.** `tvVaultRegister` has THREE outcomes — file to a mule,
route to the 🗑 throw-out review with the planner's advice (`mode:'throwout'`, the v739 branch), or
refuse. v1954 collapsed the first two, so an item the board judged junk produced *"the TV saw you
pick this up, so it went into your vault"*. Measured: `Sigon's Gage` routes `__throwout`, stays
owned (the v739 no-undo invariant holds — verified), and logged as `vault-registered`. It now logs
`throw-suggested`, a status already taught to the pill map, with a reason that says it is still his.

**A guard reading a field its producer never sets.** The same wrapper skipped logging on `!r.dup`.
`tvVaultRegister` returns `mode:'new'|'already'` and never a `dup` field — the only `dup:` in this
file is set by a different function (the inbox queue, ~18208). The duplicate-suppression it looks
like it performs **has never once run**. Harmless only by luck, because `_chLogUpsert` merges a
repeat and bumps `seenCount`, which is the better behaviour anyway. Guard removed rather than
repaired, and the row now distinguishes a first sighting from a re-read.

**Two sibling wrappers, one question, opposite answers.** `tvChronicleRoute`'s wrapper dropped
`already` on the floor while the vault wrapper twenty lines up logged it. A TV re-read of something
he owns is a decision, and its `seenCount` is the signal that the reader keeps finding the same row.
Logging cannot flood the view — the upsert merges. Both now agree. Measured: a re-read logged 0 rows
before, 1 row with `seenCount: 2` after.

---

## REG-307 — the ledger could not name the one decision with no undo (v1960)

He asked to "visually render the backend through the ledger... so we can visually surgically fix
anything needed". Two lanes could not be read there at all.

**Throw-out suggestions were a NUMBER.** `vaultAccumApply` set `out.suggestions = <count>` and left
no row, so he saw "3 suggestions" and never which three, from which reel, on whose word — for the
one lane that has no undo. They now log a `throw-suggested` row carrying the witness's reel and
frame, so the ledger's click-the-eye opens the actual photograph the suggestion came from.

**It still does not act, deliberately.** `control_app.py` states the contract twice — the throw list
ships flagged `automatic:false`, "the BOARD ignores it by contract … never registered", and a
proposal that is ONLY throw-outs is refused outright because "pressing apply could only ever
destroy". `vault_retro.py:30` says the same. Logging a row registers nothing and touches neither
`owned` nor `assign` — measured: after applying a payload with one throw-out, `owned` and
`muleAssign` are unchanged and the row is present. How wide "junk" is remains his call.

**And three silent failures.** `_vlog` fires for `raised` and `stash-held` and nothing else, so all
seven `out.skipped` paths left no ledger row. Three of them are not outcomes but FAILURES — the
stash write threw, the grail apply threw, or the build has no `chronicleApply` — each leaving only a
string inside a return value, read once by the console and then gone. Silence is not evidence, and a
write that failed is the last thing that should be quiet. The other four are ordinary outcomes
("read as none") and stay unlogged; two also sit inside the span `test_neither_branch_writes_anything`
measures, where a refusal that starts writing is exactly what that guard exists to stop.

## REG-308 — a guard on the intake door and not the merge door (v1960)

v1932 taught the reader that a PIECE is not a SET and refused piece-keyed groups out loud into
`refusedGroups`. **The guard works** — measured: `_is_piece_not_set` returns True for
`M'avina's True Sight`, `Tenet`, `Caster`, `Embrace` and `Cleglaw's Claw`, and False for every real
set name tested (`Tal Rasha's Wrappings (Sorc)`, `Trang-Oul's Avatar`, `Sigon's Complete Steel`,
`Hsarus' Defense (set)`, `Bul-Kathos' Children (Barb)`).

**It has never once fired on his data.** `merge_proposals` is a SECOND door and copied every key
across unexamined. His live `chron_last_result.json` carries **5 of 43** group keys the guard would
refuse, and no `refusedGroups` key at all — which is what "never fired" looks like from outside. An
accumulator carries history forward by design, so a group admitted before the guard existed is
re-admitted on every merge, forever. v1932's own comment measured "5 of 38"; the same five are still
there at 43. A guard on one of two doors is a guard-shaped delay.

Refused out loud at the merge too, and any refusal the source already recorded is carried across —
a receipt that does not survive a merge is a receipt that expires.

⚠ **Scope held deliberately.** Five keys are bare possessives (`M'avina's`, `Cathan's`,
`Trang-Oul's`, `Immortal King's`, `Natalya's`) — neither pieces nor valid set names. The guard lets
them through and this change does NOT extend it to them. On his data refusing them would be
lossless (measured: not one carries a piece absent from a properly-named group), but "lossless on
his data" is not "lossless in general" — a future read could put the only sighting of a piece under
one. Widening what counts as invalid is a policy change, not a bug fix.

## REG-309 — the eye pointed at a file that was never there (v1960)

The Routing Ledger's frame link is the "surgically" half of what he asked it for — click the eye,
see the photograph the decision came from. **It was dead on seven of every eight rows.**

Measured on his live ledger: 324 rows carry a `frameId` and **only 42 resolved**. The link was built
as `'/hist/' + frameId + '.jpg'`, and THREE shapes reach that renderer:

| frameId | where it lives | before |
|---|---|---|
| `reel_s_1785708285647_38665/f_1785708358178` | reel dir, no extension | ✅ |
| `f_1787000217218.jpg` | reel dir, name carries `.jpg` | ❌ 282 rows |
| `7_1786385852302` | `hist/` depth 1 (a verify beat) | ✅ |

The 282 are wrong twice: `.jpg` appended to a name that already ends in it, AND the reel directory
dropped. The file is not missing — `f_1787000217218.jpg` sits at
`hist/reel_s_1786999742937_35523/` — and **the row knew all along**: it carries `sessionId` beside
`frameId`, and the renderer never read it. All 282 rebuild exactly.

**The near-regression, which is the part worth keeping.** The first fix prefixed every bare name
with its session. That repaired 282 rows and turned the 23 verify beats into 404s — a fix that
repairs 282 and breaks 23 is not a fix, and nothing but measuring against his real ledger would have
caught it. `control_app.py`'s own `_hist_frame_paths` docstring draws the line: *"Verify beats use
frameId 'N_ts#v' … Reel footage uses 'reel_<sid>/f_<ts>' relative form."* So the rule prefixes `f_`
names and leaves the rest. **AFTER: 324 of 324 resolve, 0 regressions.**

The server always knew better — `_hist_frame_paths` tests `stem.endswith('.jpg')` before appending —
but the board never learned the same rule and `_serve_hist` does a literal path join, so nothing
downstream rescued it.

⚠ **Deliberately NOT swept across the console UI.** Its six `/hist/` builders look identical and are
CORRECT for their own data: **zero of 1,157** console-side frameIds carry an extension (680 bare,
477 path form). Same shape, different data — measured before deciding not to touch them. The root is
upstream (the python proposal's `frame` field carries the filename with its extension while sessions
write it bare), and the fix is at the DISPLAY layer on purpose: 282 historical rows already hold the
bad shape, so repairing only the writer would leave every one of them dead forever.

Guard: a sixth test in `tests/v1958_apostrophe_and_misread_routing.spec.ts`. It calls the BUILDER,
not the DOM, because the eye renders only on the console host — a spec on `file://` builds no links
at all and every assertion about them would pass while measuring nothing. `_chFrameHref` is hoisted
onto `window` for exactly that reason, and the test asserts the exposure exists so the guard fails
loudly rather than going quiet if it ever disappears.

---

## REG-310 — v1960 put a receipt on a branch that cannot fire (v1961)

Found by the post-ship review of v1960, in v1960's own work.

REG-307 added a ledger row for "the stash write failed". **That branch is unreachable.**
`_writeStash` wraps every step in its own `try { } catch(e){}` — the memory mirror, the LSR write,
the LS mirror, the re-renders — so it CANNOT THROW, and its caller is written as
`try { _writeStash(...) } catch(e){ out.skipped.push(kind + ' (write failed)') }`. That catch has
never been reachable, and v1960 made it worse by putting a receipt inside it: a row on dead code
reads as protection that does not exist, which is the exact defect class this ledger arc exists to
end.

Proven by executing all three failure paths, not by reading: "grail apply threw" and "no
chronicleApply on this build" both fired and wrote their rows; the write branch produced nothing.

Swallowing remains correct for the memory mirror, the LS mirror and the re-renders — none is the
durable store and none should abort a write. **The LSR write IS the durable store**, so its failure
is now returned instead of eaten and the caller asks rather than catching something that never
arrives. The other two `_writeStash` call sites ignore the return and are unchanged. Verified by
forcing it: a stubbed `LSR.setItem` that throws on stash keys now yields
`skipped: ["runes (write failed)"]` and a `route-failed` row naming the cause.

## REG-311 — REG-308 was half a fix, and it repaired the harmless half (v1961)

v1960 put `_is_piece_not_set` on the `setGroups` merge and stopped. v1932's own comment says which
of the two matters, in as many words:

> "setGroups alone is harmless — no UI reads it. `completeSets` is the one that bites: a set the
> panel calls complete is ONE ROW WORTH FIVE PIECES, expanded by the board. A piece accepted as a
> set there would tick pieces he does not own, from a single misread heading."

Both are guarded at INTAKE by the same `continue` — `completeSets` is populated inside that block,
after the refusal — and both were copied across `merge_proposals` unexamined. Guarding one door on
the harmless twin left the path that can tick items he does not own.

⚠ **Not measured biting**: his live proposal carries `completeSets: {}`. That is "nothing has come
through yet", not "safe", and it is exactly when a guard is cheap.

Verified: two piece-keyed complete-set claims refused into `refusedGroups`, while a real set's
sightings survive from BOTH sources (2 of 2) — the cross-reel corroboration the old `dict.update`
defect destroyed is intact.

## REG-312 — the ledger is a WINDOW and called itself a history (v1961)

Both writers cap `d2r_chronicleInboxLog` at `.slice(-400)`, consistently and deliberately — and
nowhere visibly. This file's own comment called it "every KAI read forever for debug". **He is at
326 of 400 (82%)**, so the oldest decisions will begin dropping silently out of the one surface he
asked for so he could "surgically fix anything needed". A row discarded without a word is the defect
this ledger exists to end; it just happened to point at the ledger itself.

The cap is NOT changed — 400 is a deliberate number and storage policy is his. What changed is that
the subtitle stops claiming "every decision the board made" once the window is full, and the comment
now says what the store is.

Also: the `#v` verify-suffix strip, mirrored from `control_app.py`'s `_hist_frame_paths`
(`base = fid.split("#", 1)[0]`), because without it such a row builds `/hist/N_ts%23v.jpg` and 404s
silently. ⚠ **UNEXERCISED and labelled so**: 0 of his 326 ledger rows and 0 of the frameIds in
`tv/sessions.jsonl` carry a `#`. It is there because the server documents the shape and the failure
without it is silent — not because it was measured biting.

**Headroom, measured rather than assumed**: his whole board store is 879 KB across 93 keys against a
~5 MB quota (~17%); the ledger is the largest key at 265 KB and tops out near 325 KB. A quota
failure is not a live risk, so `_chLsSet`'s silent swallow was left alone rather than gold-plated.

---

## REG-313 — a test seam born inside a branch (v1962)

**Routine I went red on v1960 and v1961, and on nothing before them.** v1958 and v1959 were green;
so were v1956 and earlier. The delta names the cause exactly — the two ships carrying the frame-eye
guard — and it was found only by READING CI, four ships after the last time I did.

`window._chFrameHref` was assigned inside `renderRoutingLedger`, BELOW its early return:

```js
if (!Array.isArray(rows) || !rows.length){ el.style.display = 'none'; return; }
```

Every probe I ran seeded his 326 ledger rows, so the renderer always ran past that line and the
export always existed. **CI boots an EMPTY ledger**, returns early, and the export is never created.
The guard then failed with its own message — *"_chFrameHref is not exposed — this guard would
measure nothing"* — which is precisely what it was written to say.

**The link-building was never broken.** It happens inside the same loop where the local is in scope,
so the 324/324 frame links worked the whole time. What was conditional on his data was the SEAM A
TEST CAN REACH. A pure function whose entire purpose is to be testable must not be born inside a
branch — and "my probe always seeded data" is exactly how that goes unnoticed.

Fixed by defining the helper above `renderRoutingLedger` at module scope. Verified in both
conditions: with an EMPTY ledger the export exists and resolves
(`/hist/reel_s_1786999742937_35523/f_1787000217218.jpg`), and with rows the panel still renders and
all three frameId shapes resolve unchanged.

**SEEN RED, AND THE FIRST ATTEMPT TO SEE IT RED WAS ITSELF WRONG.** Probing the shipped file
reported `exposed: true` — appearing to refute the diagnosis. The cause was the probe: `file://`
origins share localStorage between runs, so a PREVIOUS probe's 326 rows were still in the store at
boot, the renderer ran past its early return, and the export already existed. Clearing the store and
RELOADING before measuring reproduces CI exactly:

| bytes | empty boot | `window._chFrameHref` |
|---|---|---|
| pre-v1962 (shipped, CI-red) | 0 rows | **false** |
| post-v1962 | 0 rows | **true** |

That is the same defect class as the bug itself, one level up: a measurement whose result depended
on data left behind by an earlier measurement.

⚠ **The wider lesson, and it is about me, not the code.** I shipped four versions tonight and read
CI on none of them. The pre-push gate runs a SUBSET; Routine I runs the whole suite. Two red ships
sat unnoticed for over an hour while I audited seven other territories and reported them clean.
[[sweep-dont-ask]] says it in one line: *"Read CI. It is not optional and it is not later."*

---

## REG-314 — the repair rejected a read and kept its date (v1963)

v1891 closed this joint on ONE door. `_forgeUndo` — his manual un-tick — deletes `d2r_gameFound`,
and its own comment says why, in words that describe the OTHER door exactly:

> "The reason he un-ticks is usually that the READ WAS WRONG, so the date belongs to a different item
> entirely. Left behind, it re-attaches itself the moment he ticks that name by hand later, and v1871
> prints it on the chip: '⚔ found in game Jul 18, 2026 · Andariel' — **a claim sourced from a read he
> threw away**."

`_chRepairLedgers` is that same retraction reached automatically instead of by hand — the game's
Remaining filter saying he does not have the piece. It deletes from `setPieces`, records
`d2r_setRepairRemoved`, and **never touches `d2r_gameFound`**.

**FOUND LIVE ON HIS BOARD.** `Natalya's Soul (claws)` sits in `d2r_setRepairRemoved` AND still
carries `05/27/2026, 01:02 · The Cow King · n=6`. Tick it by hand and the chip prints that dropper
as corroboration — when it is the very reading the repair rejected.

⚠ **AND IT NEARLY COST HIM A WRONG DECISION.** I first read those two records as INDEPENDENT and
disagreeing — a bare "appeared on the Remaining list" against a specific date + named dropper + kill
count — and told him the specific one looked stronger, which would have made `Natalya's Odium` a
second complete set at 22. They are not independent. They are **one read counted twice**: the repair
rejected the reading and left its date standing, so the "corroboration" was the rejected claim
wearing a second hat. [[feedback-contradiction-is-the-finding]] — a contradiction is only a finding
when the two sides are genuinely independent sources.

Fixed by retracting the date for every piece the repair removes, mirroring `_forgeUndo` exactly.
Never inverted: if he genuinely found it, the next read re-establishes the date — the same promise
`_forgeUndo`'s comment makes.

Verified red-then-green on the same planted state: pre-v1963 the repair removes the piece and the
date SURVIVES; post-v1963 it removes the piece and the date is gone, with `removed: 1` both times so
the repair's own behaviour is unchanged. Guard: an eighth test in
`tests/v1958_apostrophe_and_misread_routing.spec.ts`.

---

## REG-315 — the same retraction, at the two doors he actually clicks (v1964)

REG-314 fixed the automatic repair. This is the census that should have come with it.

Retracting a rejected read's First Found date has **four doors**, and v1891 taught exactly one:

| door | reached by | retracts `d2r_gameFound`? |
|---|---|---|
| `_forgeUndo` | the Forge's undo bar | ✅ v1891 |
| `_chRepairLedgers` | the automatic repair | ✅ v1963 |
| `toggleSetPiece` | **clicking a set piece** (`grailTogglePiece` delegates here) | ❌ → fixed here |
| `toggleOwned` | **clicking a unique** (`grailFoundUni` delegates here) | ❌ → fixed here |

Measured before fixing: un-ticking through either toggle deletes the ledger row and leaves the date
standing. Those are the doors he uses; `_forgeUndo` is only the Forge's undo bar. **A rule
implemented at half its entrances is a rule that holds until he uses the other half.**

⚠ `vaultUnown` is deliberately NOT in this list. It removes an item from the physical vault, which
under the v677 split is not a retraction of a FIND — he still found it, he simply no longer has it
stashed. Clearing the date there would be wrong, and the census exists partly to say so.

⚠ **NO REDO AT THESE DOORS, and that is a real difference rather than an oversight.** `_forgeUndo`
stashes the date in `_FORGE_REDO` so a redo restores it unchanged; a plain toggle has no redo, so an
accidental un-tick loses a legitimate date with no recovery. v1891 already accepted that cost in
principle — *"if he genuinely found it, the next read re-establishes it"* — and consistency across
the doors is the point of this change. Recorded so the asymmetry is a known trade-off.

Verified in BOTH directions at both doors: un-tick retracts the date; **tick still writes the ledger
row with a proper stamp** (the `if/else` in `toggleSetPiece` was restructured, so that regression was
the one worth checking), and the uniques toggle round-trips `false → true → false` cleanly.

---

## REG-316 — the isolation set was right when it was written, and never extended (v1965)

bible.html gives a non-owner browser its own world: keys in `_WP_FORKED` take an `I·<id8>·` prefix
(`IL·` on ladder), so a guest's grail never lands in the owner's keys. Keys in neither fork set stay
BARE in every world, deliberately — *"so every world LOOKS identical and bare-key presence can never
be read as ownership."*

**That set was correct for every store that existed when it was written.** Measured 2026-08-22: 29 of
the 41 stores written through `LSR` are in a fork set, and **seven grail-ish stores are not**:

`d2r_chronAdopted` · `d2r_chronicleInbox` · **`d2r_chronicleInboxLog`** · `d2r_gameFound` ·
`d2r_setRepairAt` · `d2r_setRepairKept` · `d2r_setRepairRemoved`

Every one postdates the fork sets. The third is the **Routing Ledger** — the surface he asked to be
able to read surgically — and on a guest world it writes into the key the owner reads. The fourth is
`d2r_gameFound`, which v1963/v1964 just made load-bearing at four doors.

**THE NAMESPACING IS NOT CHANGED HERE, and that is deliberate.** Adding keys to `_WP_FORKED` orphans
whatever a guest world already wrote under the bare name; this repo carries migration machinery
because that cost is real. Which stores to migrate is his call. What is NOT his call is whether the
NEXT store repeats the pattern silently — so the seven are named in `KNOWN_UNISOLATED` and an EIGHTH
fails the gate.

Practical exposure today is narrow: he is the owner on his console, so bare IS his. The leak needs
one browser used both with and without the owner claim.

⚠ **THE SUITE REFUSED IT ON THE FIRST RUN, CORRECTLY.** The new gate passed its own three tests and
broke a different one: `test_every_cli_that_prints_non_ascii_is_encoding_safe` named it, because the
file prints `I·<id8>·` and em-dashes in its failure messages without calling
`console_safe.enable()`. On a non-UTF-8 console — his Windows cousin — that crashes WHILE REPORTING,
so a clean tree exits non-zero for a reason unrelated to the code. A guard that cannot print its own
verdict is worse than no guard. Fixed by the idiom the message itself prescribes.

Guard: `tv/test_store_isolation.py`, registered in `run_gates.py` (42 gates). **Calibrated in three
directions, each seen RED**: a new unisolated grail store fails; one of the seven becoming isolated
fails (a stale allowlist hides the next one); and the fork sets ceasing to parse fails, because a
guard whose input stopped parsing measures air. ⚠ Its reach is stated in the file: it reads
`LSR.setItem('d2r_…')` literals, so a store written through a variable is invisible — the count is a
floor, not a census, which is why the assertion is "no NEW escape" rather than "all isolated".
[[source-reading-guard]]

---

## REG-317 — v1964's code shipped under the v1963 stamp, because I did not read a refusal

`bump_version.py v1964` **REFUSED**, correctly and out loud:

> `apostrophe in note/name would break the single-quoted D2R_BUILD literal`

The note contained `read's`. The guard is right — an apostrophe would break the single-quoted
`D2R_BUILD` literal in bible.html. **I piped its output to `tail -3` inside a backgrounded command
and never read the result**, so the refusal went unseen, the four stamps stayed at v1963, and the
commit went out titled "v1963 + v1964" claiming a ship that was never stamped.

His own rule names it exactly: *"A vNNNN IS A SHIP, NOT A COMMIT — number ONLY commits that bump the
four stamps."*

**What is and is not affected.** v1964's CODE is live and correct: 41 gates and all 8 CI lanes green
on it. The four stamps are internally CONSISTENT (all four read v1963), so nothing on the board
contradicts anything else — the board simply reports one version behind what it carries. v1965
supersedes it with a correctly bumped stamp.

⚠ **This is the SECOND unread verdict tonight**, and the same shape as REG-313: a tool printed a
refusal, the output was swallowed by a pipe in a background command, and I proceeded on the
assumption it had worked. The lesson is not "read CI" or "read bump output" separately — it is that
**a command whose verdict I do not read is a command I did not run.**

Two concrete rules: never put an apostrophe in a bump note or name; and never pipe a bump through
`tail` — its refusals are one line and land at the TOP of the output, which is precisely what `tail`
discards.

---

## REG-318 — the rule that says what a version means, finally enforced (v1966)

REG-317 recorded that v1964 shipped under the v1963 stamp because a refusal went unread. This is the
guard, because the rule it breaks was already written down and nothing checked it: *"A vNNNN IS A
SHIP, NOT A COMMIT — number ONLY commits that bump the four stamps."*

`tv/version_stamp_gate.py`, wired into `hooks/pre-push`. If the commit subject names a version, the
stamps must carry it.

**It checks the HIGHEST version named, not the first — and that is the whole design.** The subject
that caused REG-317 was "v1963 + v1964". A first-match gate would have found v1963, matched the
stamps, and agreed with the mistake. Verified: on that exact subject with those exact stamps it
REFUSES and names both the fix and the apostrophe trap that caused it.

Calibrated in five directions: a correct claim passes; the REG-317 subject refuses; an unnumbered
commit (`test:`, `ci:`) passes in silence, because those are exactly the commits the rule says must
NOT be numbered; a stamp it cannot read REFUSES rather than passing, since a gate that cannot read
its input measures nothing; and it was proven in situ by temporarily claiming v1999 against v1965
stamps.

⚠ **AND A MISTAKE OF MINE IN TESTING IT, recorded because it is the more useful half.** That in-situ
proof was done with `git commit --amend` on a commit ALREADY PUSHED, which diverged local from
origin (1 ahead, 1 behind) for a test I had already run another way minutes earlier by stubbing
`subject()`. The content was byte-identical so nothing was lost, and `git reset --mixed origin/main`
realigned it with the working tree intact. **Never amend a published commit — and never reach for a
riskier proof when a safe one has already answered the question.**

## REG-319 — the version-stamp gate graded three of the four surfaces (v1966)

REG-318 shipped the gate that enforces *"a vNNNN is a ship, not a commit"*. It was caught, before its
own push, printing `✅ v1966 claimed and all 3 stamps agree` — while `tv/bump_version.py:6-7` names
**four** places a version lives: `bible.html`'s `D2R_BUILD`, `tv/control_app.py`'s `/api/status`,
`tv/tv_diablo.py`'s `VERSION`, and `tv/WINDOWS_SHIP.json`. `STAMPS` listed three. `tv/control_app.py`
was missing.

**Why it mattered:** a tree whose `control_app.py` stamp had been left behind — exactly the
half-bumped state `bump_version.py:71-72` records having happened before — would have passed the gate
whose entire purpose is that the four agree. A guard shorter than its own subject reports clean for
the one case it exists to catch.

**Why the pattern is unambiguous despite 12 `"ver"` keys in that file:** only one is a `vNNNN`
literal; the rest are `_app_ver()` calls and `st.get("ver")` reads. `bump_version.py:97` already
depends on that, raising unless `s.count('"ver": "<cur>"') == 1`.

**Calibrated red, in a temp copy, with the live tree never written to:** the four stamp files were
copied to a scratch dir, the module's `REPO` repointed at it, and *only* `control_app.py` knocked
back to `v1901`. The gate reads v1966 / v1966 / v1966 / v1901 and refuses. It now prints
`all 4 stamps agree`.

The tell was the gate's own success line. A count in a green message is worth reading — it is the
cheapest place a guard admits how far it actually reaches.

## REG-320 — the inbox said "unclear read" about a name it could have identified (v1967)

v1789 read his real ledger by hand and split 36 held rows three ways: six unresolved uniques,
twenty-four reader debris, and **six OCR slips of items already in his grail** ("Battlecage" for
Rattlecage, "Naglring" for Nagelring). It then built machinery for exactly one of the three —
dismissing debris, because the Chronicle prints the BASE item name for a row he has NOT found, so
"Templar Coat" is the game stating the *opposite* of a find. The slips were named in that spec's own
header and given no resolver. Measured 2026-08-22: `bible.html` contained **zero** string-distance
functions of any kind, so a slip reached him as `unclear read`.

His ask, quoted in v1789's own header: *"cant like an extra AI take care of it and cross reference it
... and if it still cant then leave it for me to tick off."*

**Measured on his current reader output** (`tv/chron_last_result.json`): 369 names, 343 recognised
(93%). Of the 26 that were not, four are slips of real roster entries and every one was mute.

`window._nearestGrailName()` — bounded Levenshtein over `_gUniqueRoster() ∪ __setPieceNames()`,
rendered into the pending row as `probably <Name>`. **It suggests and nothing else**: it never
accepts, never writes, never moves a count, and a spec asserts every grail-ish store is
byte-identical after it runs. A fuzzy match that grails an item invents a find, and an invented find
is unrecoverable — he could not tell it from a real one later.

### The bound is 3, and the first draft's 2 was INERT
Written first as `2`, which felt conservative and produced **zero** suggestions on his real data —
the slips are three edits out (`hawkfane` → `hawkmail` differs at f/m, n/i, e/l). That is a threshold
above the ceiling of the signal: a branch that never runs, wearing a constant that looks tuned. The
same shape as `STILL_MAX_DIFF=0.22` against a signal whose maximum was 0.133.

At 3, the same 23 candidates yield four confident hits and nineteen silences:

| read | probably | edits |
|---|---|---|
| Hawkfane | Hawkmail | 3 |
| Stouthale | Stoutnail | 3 |
| Endlessmane | Endlesshail | 3 |
| Bloodfist Shard | Bloodpact Shard | 3 |

`Templar Coat`, `Bone Visage`, `Tomahawk`, `Corona`, `Death Mask`, `Shadow Blade` and `Spired Helm`
stay mute — held by the **tie rule** and the 6-character floor, not by the bound. A tie is an
admission that the evidence does not name one item; printing either candidate would be a coin-flip
wearing a verdict.

**Two instrument errors on the way, both caught by re-measuring rather than by reasoning:** the
candidate set was first drawn from `"n":` records (the 322-entry boss-drop-table `ITEMS` array, which
v1692 already warns is not the roster), and then the roster was checked against `_UNI_EXTRA` alone —
concluding wrongly that Hawkmail was untracked. The real roster is `ITEM_VALUE ∪ _UNI_EXTRA` = 525
keys and contains every one of them.

Guard: `tests/v1967_nearest_grail_name.spec.ts` — the hits, the eight refusals, purity, and an
explicit **not-inert** assertion so a future narrowing fails loudly instead of going quiet.

## REG-321 — v1967 shipped a comment claiming NINE, and the code makes FOUR (v1968)

Caught by reviewing the **pushed bytes**, not the working tree. The header block of
`_nearestGrailName` shipped saying *"Of the 26 that were not, NINE are slips of real roster
entries"* and listed mappings the function does not produce:

| the comment claimed | what the code actually does |
|---|---|
| `Kinemit` → `Kinemil's Awl` | no candidate within the bound |
| `Nord's Tooth` → `Nord's Tenderizer` | no candidate within the bound |
| `The Dragon` → `The Dragon Chang` | no candidate within the bound |
| `Bloodfist Shard` → `Bloodfist` | → **`Bloodpact Shard`** — not even the right candidate |

**Where the nine came from:** an earlier count, taken before the bound was calibrated, against the
322-entry boss-drop-table `ITEMS` array — which `v1692`'s own block explicitly warns is *not* the
roster. The calibration that followed measured four and was written into the `_NGN_MAX` block one
screen below. Nobody re-read the paragraph above it, so the file shipped carrying two contradictory
statements with the stale one on top.

This is the failure `bible.html` already documents in the v1692 block — *"a count in a comment is a
number nobody re-measures"* — recurring **one screen away from where it is written down**. The v1692
block had itself gone stale exactly that way in v1720 and says so. Third occurrence in this file.

The corrected paragraph now carries the contradiction rather than quietly replacing it, because the
interesting fact is not "four" — it is that a measured number and a remembered number sat adjacent
and only one of them was true.

## REG-322 — the new CSS rule was inert, and looked applied (v1968)

`.ibx-why-near` was written **above** `.ibx-why` in the stylesheet. The span carries *both* classes,
both set `color`, and both are single-class selectors — equal specificity, so **source order
decides** and `.ibx-why`'s `--text-dim` won. The suggestion would have rendered in exactly the dim
style it exists to escape, while the rule sat in the file looking correct.

Caught before push by checking byte offsets rather than by reading the diff, which is the only way
this class is catchable: a CSS rule that loses on order is indistinguishable, on inspection, from one
that wins. Standing scar `d2r_css_last_rule_wins` — `.hero-title` once had FOUR competing rules and a
twin `filterSilver` cost a whole pane. The rule now sits after `.ibx-why` and carries a comment
saying it must stay there.

## REG-323 — CI failed on a number that survived its own recalibration, for the third time in a day (v1968)

`Routine I` went **red on v1967** — one test in the whole suite, and it was mine:

```
✓ line 47   got.name === 'Hawkmail'                       ← the resolver answered correctly
✗ line 48   expect(dist).toBeLessThanOrEqual(2)           ← the assertion still said 2
    Error: "Hawkfane" should be within 2 edits
```

**The feature worked and the test was wrong.** The bound had moved from 2 to 3 during calibration;
the `SLIPS` table was updated, the assertion beside it was not.

### The class, not the instance
This is the **third** occurrence in one day of a number outliving the measurement that set it:

| where | stale value | found by |
|---|---|---|
| the resolver's header comment | "NINE slips", with mappings the code never makes | reviewing the pushed bytes (REG-321) |
| the spec's distance assertion | `toBeLessThanOrEqual(2)` | CI going red |
| the length pre-filter | `Math.abs(len diff) > 3` as a literal | sweeping for the class after the other two |

The third was found only because the first two forced a sweep, and it is the most dangerous of the
three because it fails **silently**: raise `_NGN_MAX` to 4 and the pre-filter still discards every
candidate 4 apart in length, so the extra edit is unreachable while the constant above it looks
tuned. That is the `feedback_threshold_above_the_ceiling` shape — a bound that cannot be reached —
hiding one line below the bound it contradicts.

**Fixed by naming the number once on each side of the boundary**: `_NGN_MAX` in `bible.html` (used by
both the pre-filter and the distance call) and `NGN_MAX` in the spec (used by the assertion and the
message). Two names rather than one is deliberate — the spec must be able to disagree with the page,
or it is asserting the page against itself.

**What went right:** the failure was a single test, on the version that introduced it, because v1968
was deliberately held back until Routine I returned. Stacking it would have buried a red spec under a
green one.

## REG-324 — v1967's resolver is WITHDRAWN: it duplicated a better engine, and was dead code (v1969)

v1967 added `_nearestGrailName` to name the probable item behind an OCR slip. It was measured,
calibrated, guarded by six specs, verified in a real browser — and it should never have been written.
Removed in full (9,009 bytes, spec deleted).

### 1. The machinery already existed, under different words
`D2R_INBOX_FOLD` (v1794, `bible.html:17856`) already resolves misreads, with four outcomes stated in
its own header:

```
misread-settled  a slip of an item he ALREADY has        -> retired; there was never a decision
misread-open     a slip of a real item he does NOT have  -> shown as the REAL item, raw read kept
ambiguous        two roster items within AMBIGUITY_GAP   -> held, BOTH named, never guessed
not-in-game      folds onto nothing in the roster        -> quarantined to the reader lane
```

**Recon missed it because I grepped for the wrong vocabulary** — `levenshtein|editDistance|_fuzzy|
_closest|misread|alias` — and this engine says *fold*, *NEAR_CUTOFF* and *AMBIGUITY_GAP*. The count
should have been the tell: `grep -c "suggest|nearest|closest|guess"` returned **165 hits** and I read
none of them, concluding "no near-name resolver exists" from a search for names rather than for
behaviour. `workflow-topology §0` says to grep the CONCEPT, not the filename you had in mind; the
same applies to functions.

### 2. Its threshold contradicts a calibrated one, and the calibration is better
`NEAR_CUTOFF = 0.86`, calibrated in `tv/chronicle_resolve.py` against HIS OWN ledger, with a gate
asserting both literals agree. Its comment rejects exactly what I built:

> *"0.86 folds all five real OCR slips (battlecage->rattlecage .90, naglring->nagelring .94) and
> pulls no debris onto a roster item; 0.80 pulls 'the dragon' onto 'the dragon chang', which is a
> GUESS about which item he saw. A wrong fold writes a find he never made."*

`hawkfane`->`hawkmail` scores ≈**0.625**. My bound of 3 edits admits it; the calibrated engine refuses
it on purpose, and is right to: at that distance the name could be Hawkmail, Hawkfist, or nothing in
this game. **My "measured" bound of 3 was measured against my own candidate list, not against the
question "would this fold be correct".** A threshold calibrated on the wrong quantity is not calibrated.

### 3. It was unreachable
It rendered in the `pend` branch. Every row reaching that branch is already a roster name — the
`hold` verdicts are `tier-grail-ungrounded`, `g4-disagreed` and gate-uncorroborated, all grail-tier —
and the function returns null for names already in the roster. **Proven in a browser, not argued:**
seeding a queue with `Hawkfane`, `Stouthale`, `Templar Coat`, `Toothrow` rendered four rows and
`document.querySelectorAll('.ibx-why-near').length === 0`. `kaiChronicleTriage('Hawkfane')` returns
`{action:'dismiss', why:'not-in-game'}` — it never arrives.

### 4. And nothing was being swallowed, which was my whole premise
The reader lane renders **"🔎 N reads matched nothing in this game — handed to the reader, not to
you"**, names them, and deliberately offers no put-back, *"because putting a string that is not an
item in this game back in front of him is the exact thing he asked to stop; the ledger still holds
every one of them."* `Hawkfane` was already visible to him, correctly labelled, the whole time.

### What survives
REG-321/322/323 stand — the stale-count, the inert CSS rule and the recalibration stragglers were
real, and the lesson about naming a bound once on each side of a boundary is worth keeping even
though the bound itself is gone. **The visual check is what killed this feature**: every parser-level
gate was green, six specs passed, and one look at the rendered panel showed `near-marked: 0`.

## REG-325 — a discard he chose and a discard nobody chose read the same sentence (v1970)

The vault keeps eight sets (`_KEEP_SET`) and throws out everything else, so **the default is
discard**. The v394 comment names **18** sets he actually ruled junk — Sigon's, Cleglaw's, Angelic,
Arctic, Cathan's, Bul-Kathos and the rest. The board knows **34**. The remaining **8 are discarded by
silence** and every one of them printed the same row as a set he had judged:

> `low set piece — track for grail, discard: <set>`

| never ruled either way | holds |
|---|---|
| **The Disciple** | **Laying of Hands** (+350% damage to demons) |
| Sazabi's Grand Tribute | Cobalt Redeemer |
| Naj's Ancient Vestige | Naj's Puzzler |
| Hwanin's Majesty | Hwanin's Justice |
| Arcanna's Tricks · Bane's Garments · Heaven's Brethren · Orphan's Call | — |

**This is the position Horazon's Splendor occupied until v440**, and the code comment records the
cost in his own words: *"Konyo's 4 Horazon's pieces wrongly discarded"*. The defect was never the
routing — it is that the row gave him no way to separate a verdict from a default, so the one case
worth a second look was indistinguishable from eighteen settled ones.

**Nothing was re-routed.** Which sets are worth muling is his call and not a defect to fix behind his
back; a wrongly-kept item costs a stash tab, a wrongly-discarded one is gone, and only he knows which
error he prefers. So the fix is to the SENTENCE:

```
Sigon's Guard    -> low set piece — track for grail, discard: Sigon's Complete Steel
Laying of Hands  -> discard by DEFAULT — you have never ruled The Disciple (set) keep or junk
```

Verified on the rendered page, with `Tal Rasha's Lidless Eye -> sets-major` as the control proving the
harness discriminates. Guard: `tests/v1970_discard_by_default.spec.ts` — and **its routing assertions
are the important ones**: every name above must still return `__throwout`, so that if a future edit
turns this honest label into a behaviour change, the build goes red.

## REG-326 — the comment deferred to a spec, and the spec disagreed with it (v1971)

`bible.html:18639` described the roster and named its own authority:

> *"…_gUniqueRoster() is the resolver's ITEM_VALUE ∪ _UNI_EXTRA union (**514** names) … the FILTERED
> roster (**514 − 127** set pieces = **387**) … v659_grail_seed.spec.ts pins **387** — that spec, not
> this comment, is the authority."*

`v659_grail_seed.spec.ts:70` reads `expect(r.total).toBe(398)`, with its own note *"v1720: 387 + the
eleven he ruled in"*. **The comment pointed at an authority that contradicted it.**

v1720 added the eleven RotW uniques he ruled in (`_UNI_EXTRA` 69 → 80, roster 387 → 398). A paragraph
elsewhere in the same file was corrected then — it already says *"525 − 127 set pieces = 398 unique
names, measured in a browser, not assumed"* — and this one was not. So the file asserted **both**
numbers, and the copy sitting next to the code was the wrong one.

**Re-measured, not adjusted on paper:**

| | claimed | measured 2026-08-22 |
|---|---|---|
| ITEM_VALUE ∪ _UNI_EXTRA | 514 | **525** (505 ∪ 80) |
| `_gUniqueRoster().length` | 387 | **398** (in a browser) |
| what v659 pins | 387 | **398** |

Found by sweeping every count claimed in a comment against its live value — a sweep run *because* the
same class had already bitten twice tonight. The other claims all held: `ITEM_VALUE` 505 ✓,
`_UNI_EXTRA` 80 ✓, `BASE_DB` 508 ✓ (top-level keys — a first pass counted 4140 by walking nested
keys, which the 8× gap gave away), roster 398 ✓, and the set-piece figures 108/110/127/135 are four
*different* quantities, all correct: 108 = set pieces in his found ledger, 110 = the same in the
346-key `d2r_foundLog`, 127 = union members that are set-piece names, 135 = the roster total.

**Fourth instance in one day** of a number outliving its measurement — REG-321 (a header claiming
nine slips), REG-323 (a spec assertion and a length pre-filter that kept the old bound), and this,
which had been stale since v1720. This file warns twice that *"a count in a comment is a number
nobody re-measures"*. The warning is correct; it is just not a guard.

## REG-327 — The Disciple is a keeper, on his ruling (v1972)

v1970 did not change routing; it made the difference between *a discard he chose* and *a discard
nobody chose* visible, and named the eight sets in the second category. He read it and ruled:
**add The Disciple to `_KEEP_SET`.**

All five pieces now mule instead of being discarded — `Laying of Hands`, `Rite of Passage`,
`Telling of Beads`, `Dark Adherent`, `Credendum` — to **`sets-rest`**, because `MAJOR_SETS` is
`Tal Rasha | Immortal King | Griswold` only. That is a placement, not a downgrade.

Verified on the rendered page, with all three controls holding: `Naj's Puzzler` still throws out and
still says *"by DEFAULT only — you have never ruled…"*, `Sigon's Guard` still carries his own junk
ruling, and `Tal Rasha's Lidless Eye` still routes to `sets-major`.

**Seven sets remain discarded by default and unruled** — Sazabi's Grand Tribute, Naj's Ancient
Vestige, Hwanin's Majesty, Arcanna's Tricks, Bane's Garments, Heaven's Brethren, Orphan's Call —
each still labelled a default rather than a judgement, and each still one word away from a ruling.

**The spec was updated with the code, not after it.** `tests/v1970_discard_by_default.spec.ts` pinned
`Laying of Hands` as `__throwout`; left alone it would have failed CI and, worse, would have been
pinning the defect rather than the behaviour. It now asserts the ruling directly — *a piece of a set
he has RULED must never reach the throw-out pile* — which is the assertion that would have caught the
original problem had it existed. The calibration case moved to `Naj's Puzzler`, which is still
genuinely unruled, so the two-branch test still discriminates.

## REG-328 — the stale-count class, finally given a gate (v1973)

`bible.html` warns twice that *"a count in a comment is a number nobody re-measures"*. On
**2026-08-22 it drifted that way five times**:

| | what drifted |
|---|---|
| REG-321 | a header claimed NINE misread slips; the code made four, and named a candidate it never picks |
| REG-323 | a spec assertion still read `toBeLessThanOrEqual(2)` after the bound became 3 — **CI caught it** |
| REG-323 | a length pre-filter still hardcoded `3`, which would have capped reach **silently** if the bound rose |
| REG-326 | the roster block claimed `514 − 127 = 387` while naming a spec that pins **398** — stale since v1720 |
| **this** | the shopping-list comment said *"between the chronicle and 99/99"* with **100** runewords live |

Every one was written by someone who had just measured. The warning was already there and already
believed; what was missing is the thing that **fails**. So: `tv/comment_count_gate.py`, registered in
`run_gates.py`, 60s cap.

### What it deliberately does NOT check — most of the design
Numbers near the same words are usually **different quantities, all correct at once**. Measured on
this file: `108` = set pieces in his found ledger · `110` = the same in the 346-key `d2r_foundLog` ·
`127` = union members that are set-piece names · `135` = the roster total. Likewise *"~300 rows × 14
bosses ≈ 50k DOM nodes"* is an explicitly approximate perf note, and *"the Shako drops from 11
bosses"* counts drop sources. **A gate that flagged those would be wrong four times and get switched
off** — which is exactly how a red signal becomes furniture.

So it checks only claims that name their subject unambiguously, against a value parsed from the same
file, where the author plainly intended the pair to be equal. Three today: the runeword denominator,
`ITEM_VALUE` keys, `_UNI_EXTRA` keys. It also fails loudly if it cannot MEASURE a value — a parser
that missed its literal is a broken gate, not a passing one.

### Calibrated on real data, in both directions
Run before the fix it went **red on the live defect without being told where to look**; run after,
green with 3 claims matching. The runeword denominator is DISTINCT words, not entries — `Spirit
(sword)` and `Spirit (shield)` are one runeword in two bases, so 101 entries are 100 words, and 100
is what the user-facing `N/N` means.

**Also fixed here:** the `99/99` claim itself → `100/100`.

## REG-329 — Orphan's Call is a keeper, on his ruling (v1974)

Second ruling off v1970's honest label, and the same shape as the first: **Guillaume's Face**
(15% crushing blow / 35% deadly strike) was discarded by a default nobody had decided.

All four pieces now mule to `sets-rest`: `Guillaume's Face`, `Whitstan's Guard`, `Magnus' Skin`,
`Wilhelm's Pride`.

Verified on the rendered page, with every control holding: `Laying of Hands` still `sets-rest`
(v1972), `Naj's Puzzler` still `__throwout` and still saying *"by DEFAULT only — you have never
ruled…"*, `Sigon's Guard` still carrying his own junk ruling, `Tal Rasha's Lidless Eye` still
`sets-major`. **And no count moved** — 34 sets · 135 pieces · 398 roster · 403 chronTotal, identical
before and after. A routing decision must never move a tally, and it didn't.

**SIX sets remain discarded by default and unruled**: Sazabi's Grand Tribute, Naj's Ancient Vestige,
Hwanin's Majesty, Arcanna's Tricks, Bane's Garments, Heaven's Brethren.

The spec now pins both rulings by **destination**, not by wording — `NOW_KEPT` covers all nine pieces
of the two ruled sets, and the assertion is *a piece of a set he has RULED must never reach the
throw-out pile*. The label was only ever how he found out; the destination is the thing that matters.
`NEVER_RULED` still guards the six, so the two-branch test continues to discriminate.

## REG-330 — the manual AI-intake doors for runes/gems/materials are gone; each lane has an ON/OFF mini (v1975)

Konyo: *"all the AI INTAKE the manual ones… surgically remove them all and have like a on/off for that
specific MINI ON AIR that we already have coded for automated and AI reads… that way it forces me and
my cuzin also to just hit reel session instead of anything manual."*

**Restore point before any of this: `restore/v1974-before-intake-consolidation` (on origin).**

### What was removed, and what deliberately was NOT
Removed: the 📸 button and its hidden `<input type="file">` for **runes, gems, materials**.

**Every intake FUNCTION survives.** `tvStashAutoIntake` dispatches to
`window[runeIntake|gemIntake|materialIntake]` **by name**, and its own comment says it *"only supplies
a File"*. Deleting those would have broken the automation this change exists to promote — and broken
it **silently**, since every call site is guarded with `window.x &&`. So each section keeps its own
reading logic: runes still go through `_runeSheetPrep`, gems/materials through `_tallyPrepImage`, and
each still posts its own `kind` template. That is asserted first in the new spec.

### The mini
One component (`_miniOnAirHtml` / `_miniOnAirToggle` / `_miniOnAirPaint` / `_miniOnAirMount`), one
store (`d2r_autoLanes`), rendered from one `_MINI_SLOTS` table so a lane cannot appear in the strip
and be missing from its section. CSS is a smaller sibling of `.tvd-switch`, placed **after** it so it
cannot be outranked at equal specificity.

- **Default is ON.** An unset lane is armed, because the point is that doing nothing yields automatic
  intake. This is the inverse of the v1737 bug, where a toggle defaulted to INCLUDE and only did
  anything once switched OFF.
- **OFF is a real refusal.** `tvStashAutoIntake` consults it and returns `{ok:false, why:'lane-off'}` —
  a NAMED reason, so a lane he switched off is distinguishable from one that failed.

### Two hazards found on the way, both silent
1. **A second map keyed by those input ids.** `quickIntake` drove the same file pickers from a Tools
   bar; removing the inputs would have made four buttons do nothing, with no error. `quickIntake`
   therefore **keeps its name and signature** and now expands the card and arms the lane instead.
2. **Two `window.quickIntake` definitions briefly existed** — last-one-wins, exactly the CSS-order
   trap. The dead file-picker version was removed rather than left to confuse.

### Verified on a real page, not asserted
7 minis render · defaults all ON · manual inputs for the three lanes = 0 · all six intake fns still
`function` · toggling runes OFF makes the reel return `lane-off` · gems still reaches its fetch ·
`quickIntake('rune')` arms the lane · **0 console errors** · and `v544_quick_upload`'s targets are
intact (bar present, 4 cards, labels unchanged).

**Still manual by design:** `craft` (his instruction — set aside), and `vault`/`set`/`grail`, which
are next.

## REG-331 — vault, sets and grail lose their manual doors; only one of them gets a switch (v1976)

Removed: the 📸 manual door for **vault**, **sets** and **grail** — four buttons (grail had two) and
three hidden `<input type="file">`. `craft-intake-file` is now the **only** manual intake left, set
aside on his instruction.

### The three were not treated the same, and the difference is the whole point

**VAULT gets a pill.** It has a real auto lane: `_startAutoWatch` polls the linked folder every
**12000ms** into the same `window.vaultIntake`, which keeps all 38 of its crop steps and its
`locate`/`rawname`/`socketcheck`/`vault` templates. Its `webkitdirectory` picker **stays** — that is
the automation's *setup*, not a manual read, and removing it would disarm the very lane being
promoted.

**SETS and GRAIL get NO pill, deliberately.** Their ticks are *"review-first, never silent"* — the TV
DIABLO panel says exactly that — and `kaiChronicleAcceptAll` / `kaiChronicleAcceptSession` are called
**zero** times inside `bible.html`; he accepts from the console. There is no auto-apply to arm, so a
switch would control **nothing**. A control that controls nothing is decoration, which is precisely
what v1975's `lane-off` guard exists to prevent — it would have been a lie of exactly the kind this
board keeps auditing out. They get an honest line instead: *"Set pieces tick from a reel session —
the reader proposes, you approve in the Chronicle queue."*

The spec now asserts the negative too: **no pill may exist for `grail` or `sets`.** A future well-meant
"consistency" pass that adds them would fail the build.

### Verified on a real page
8 minis render · the only remaining manual door is `craft-intake-file` · `vault-dir-input` intact ·
`_startFolderAutoWatch` still a function · `vaultIntake` / `setIntake` / `grailIntake` / `craftIntake`
all still functions · 2 review notes shown · **0 console errors**.

## REG-332 — the lane pills said ON AIR, and so did the card above them (v1977)

Found by **looking**, not by testing. Every behaviour assertion in v1975/v1976 passed; the defect was
only visible on the rendered page, and it was confirmed by a second model family shown the screenshot
**cold, with no hint of what to look for**:

> *"The card title claims the feature is ON AIR while its own toggle says OFF AIR. Below it, the four
> pills also say 'ON AIR'… A user could reasonably think the master switch is fighting the individual
> toggles, or that **'ON AIR' means two opposite things at once**."*

It did mean two things. The card is the **broadcast** state — is the reel running. A lane is whether
**this category** gets read. Two different questions wearing one phrase, stacked vertically.

**Fixed three ways, smallest first:** the lanes now read `AUTO` / `OFF`, so `ON AIR` keeps exactly one
meaning on the screen; the pills gained padding and the row a gap; and the row is now labelled
**"Auto lanes"** so it stops reading as the card's detail. His card was not touched — the tension
between its title and its status pill is pre-existing and is the honest broadcast state.

### Two findings from the same review were REJECTED against the pixels
The follow-up read claimed the pills were *"still cramped… rounded ends touching"* and that *"the left
pill sits slightly higher than the right three."* Neither survives inspection: the row measured
**459px → 534px** after the padding change, the gaps are plainly visible, and the baseline is even.
**A review is evidence, not a verdict** — the same review was right about the thing that mattered and
wrong about two details, which is exactly why findings get reproduced before they are believed.

Its other observations (`MF QUICK SET` showing a value off the preset ticks, the header contrast, the
clipped scrollbar) are pre-existing and outside this change; recorded here, not chased.

## REG-333 — a set piece read off film was filed as a unique (v1978)

Raised by a read-only Grok audit of the Vault Manager, then reproduced here before acting.

`vaultAccumApply` called `chronicleApply({ wouldAdd: { uniques: grailNames, sets: [] } })` with
**`sets` hardcoded empty**. A Tal Rasha or Disciple piece that a sweep grounded went down the uniques
pipe, never reached `toggleSetPiece`, and the set grail never ticked. Measured: `vaultAccumApply` is
11,573 chars and calls `toggleSetPiece` **0** times.

The machinery already existed and was simply never fed — `_chronicleApplyInner` reads `wouldAdd.sets`
in seven places and calls `toggleSetPiece` twice. **A join, not new logic.**

### The trap that made my first fix WORSE than the bug
The sets branch validates every name against `_chronSetPieceSet()` — **135 entries, all
slot-suffixed** — and pushes anything absent to `unknown` rather than ticking it:

```
_chronSetPieceSet().has('Laying of Hands')                 -> false
_chronSetPieceSet().has('Laying of Hands (bramble mitts)') -> true
```

So passing the bare read name routed **every** set piece to `unknown`. `findSetPiece` already returns
the canonical string as `.piece`, so it costs nothing and introduces no second naming rule. **Caught
by feeding the pipe and reading `unknown:["Laying of Hands"]` back — not by inspection.** The spec now
pins the bare name as refused, so a later "simplification" fails loudly.

### What I did NOT accept from that audit
Its headline — *"film cannot see the names it would mule"* — is **not a defect**. `control_app.py`
already documents it at v1861 and quotes the very same three frames the report offered as evidence:

> *"READ FINE, AND THERE IS NOTHING NAMEABLE ON IT" IS A THIRD ANSWER. D2R prints no item names in a
> stash grid; a name appears only in the HOVER tooltip. So a perfectly good read of a full shelf
> honestly returns items:[] — measured on his own frames.*

They are counted separately in `_read_no_names` precisely so the sweep can say which of three things
happened. `owned: []` therefore follows from **physics**, not a broken join, and the `BLOCKED` verdict
rests partly on re-presenting the code's own documented evidence as a discovery.

**Still open and real from that audit:** `vaultAccumApply` calls neither `vaultAutoAssign` nor
`suggestMule` (0 and 0 — it does not mule); `gate()` returns `"witnesses": n` as a COUNT while the
board reads `.seen[0]` as an array; and `KEEP_MIN_WITNESSES` is applied with no per-kind exception, so
one clean rune-tab photo stays unsure. Not fixed here — each needs its own verified pass.

## REG-334 — every held row reached the inbox with no frame (v1979)

The board read `h.seen[0]` for a held row's provenance. **Nothing emits `seen`.** Measured:

| sweep | what it actually hangs on the row | keys |
|---|---|---|
| chronicle (`chronicle_retro.py`) | `sightings` | `reel`, `frame`, `witness`, `conf`, `lane` |
| vault (`vault_retro.py`) | `witnesses` | `session`, `frame`, `lane`, `conf` |

Neither is called `seen`, so `seen[0]` was `undefined`, `frameId` came out `''`, and `_chFrameHref`
(v1960) had nothing to build a link from. **The held rows — precisely the ones he must rule on — could
not show him the frame that produced them.** The two sweeps also disagree about the session key
(`reel` vs `session`), so even a rename would have fixed only one of them.

Fixed board-side, reading all three names and accepting `session` as an alias for `reel`. That repairs
both pipes at once, works on rows already stored, and touches no Python payload contract that its own
tests pin. Verified by feeding a chronicle-shaped and a vault-shaped held row and reading the queued
proposal back: `frameId:"f_9.jpg"/sessionId:"s_123"` and `frameId:"f_4.jpg"/sessionId:"s_777"`.

**Credit where due, and a correction.** The Grok audit called this "witnesses are flattened to a
number… provenance dies at the join," pointing at `apply_payload`'s `"witnesses": len(...)`. That
flattening is real but it is **not** this bug: it applies to `items` (owned rows), while `held` passes
through untouched. The actual defect is a field-name mismatch on the held path, in **both** sweeps —
broader than reported, and in a different place. The finding was worth chasing; the diagnosis needed
re-deriving.

## REG-335 — the function that quotes "muling the items" did not mule (v1980)

`vaultAccumApply`'s own header says the sweep exists to *"feed the vault manager for throwing out or
muling."* Measured: that body called `vaultAutoAssign` **0** times and `suggestMule` **0** times. It
registered rows and stopped.

Muling lived behind a separate button — ⚖️ Auto-assign unsorted — which had **zero programmatic
callers**. So "register a sweep" and "mule what it registered" were two halves nobody joined, and the
second only happened if he pressed it himself. The on-disk ledger (`owned: []`) made it look like
nothing had ever been found; in truth nothing had ever been *placed*.

### Why calling it here is a join, not new policy
- `vaultAutoAssign()` takes no arguments and walks `ownedPool()`, so it acts on what the apply just
  registered without being handed anything.
- It **skips anything already assigned** (`if (assign[name]) return`), so running it after every apply
  is idempotent — it can only place items that have no mule yet.
- A `__throwout` verdict is **logged as a suggestion and never assigned**. Nothing is auto-binned. That
  contract is untouched and is the one that must never bend: there is no un-throw in Diablo.
- It is the same function his button calls, so no second opinion about where an item belongs enters
  the tree.

Guarded so a failure cannot lose a registration that already succeeded: the apply's result returns
regardless, and the newly-placed count reports separately as `out.muled`. `assign` is in scope there —
the original body already referenced it four times — so that count is real rather than always zero.

**Verified:** `vaultAccumApply` now references `vaultAutoAssign`; `suggestMule('Shako')` → `bases`
while `suggestMule("Sigon's Guard")` → `__throwout`, so the keeper places and the throw-out does not.

## REG-336 — v1978's fix never fired: grailNames holds OBJECTS, not strings (v1981)

v1978 split `grailNames` with `findSetPiece(n)` to send set pieces down the sets pipe. **It never
fired once.** v1918 had already made that array carry the row's evidence across —
`grailNames.push({ name, lane, conf, witnesses, … })` — so `findSetPiece` was handed an **object**,
returned null every time, and every set piece went on down the uniques pipe exactly as before.

**How it passed verification and still was wrong.** I checked it by calling
`findSetPiece('Laying of Hands')` with a string literal. That tests `findSetPiece`; it does not test
the join. It is the exact proxy the standing rule forbids — *verify the thing, not a proxy* — and the
fix shipped green.

**What actually caught it:** running a real payload through `vaultAccumApply` and reading `grail:[]`
back. After extracting `n.name` first:

```
grail: ["Laying of Hands (bramble mitts)", "Sigon's Guard (shield)"]
d2r_setPieces: both stored · foundLog: 2 keys
```

Uniques still push the whole row so their ledger entry keeps reel/frame/conf; only the sets branch
takes the canonical name, because that is what `_chronSetPieceSet()` holds.

### Two things this run surfaced, NOT fixed here
- **`muled: 0`.** `vaultAutoAssign` walks `ownedPool()`, but this path registers grail finds
  (`foundLog` / `setPieces`) and never adds to `owned`. So v1980's join is correct and simply has
  nothing to place from THIS path — a grail tick is "I found this", not "it is in my stash". Whether
  a vault sweep should also register physical ownership is a design question, not a bug to patch.
- **`Shako` never reached `grail`.** A plain unique passed through `_uni` and came back in neither
  `res.uniques` nor `res.sets`. Unexplained; needs its own pass rather than a guess.

## REG-337 — a vaulted row landed and the result said nothing happened (v1982)

Chasing REG-336's unexplained `Shako` turned up no bug in the routing — it turned up a **fifth
outcome** and a reporting gap.

`chronicleApply` returns `uniques / sets / skipped / unknown` **and `vaulted`**, the last for a name
that is a BASE rather than a grail unique. `Shako` is the base; `Harlequin Crest` is the unique
(`_gUniqueRoster().includes('Shako')` → **false**). The board routed it to physical vault stock,
exactly right — my test item was the wrong one.

But `out.grail` counted only `uniques + sets`, so **a sweep carrying nothing but bases reported an
empty success**. That is the shape this board keeps auditing out: a real outcome the caller cannot
see, indistinguishable from "nothing was found."

Reported on its own key rather than folded into `grail`, because a base in the vault and a grail tick
are not the same claim and must not add up to one number.

**Verified with all three kinds in one payload:**
```
grail:   ["Harlequin Crest", "Laying of Hands (bramble mitts)"]
vaulted: ["Shako"]
muled:   0
```

`muled: 0` remains correct and explained: `vaultAutoAssign` walks `ownedPool()`, and a grail tick is
not stash stock. Whether a vault sweep should also register physical ownership is his design call.

## REG-338 — the lane lock: never tell him to move what is on his character (v1983)

`PROJECT_VAULT_MANAGER.md`, his words in capitals:

> *"inventory and main character equiment (**SHOULD NEVER BE TOLD TO BE MOVED its locked there**)"*

Nothing enforced it, and nothing **could**. Measured before this change:

```
vault_retro LANES = ("stash","inventory","equipment")   ← the sweep carries a lane on every row
board 'equipment' = 0 occurrences                        ← the lane died before the board
per-item lane key = 0
ownedPool()       → Array.from(owned) = bare NAMES
suggestMule(name) → takes no lane argument at all
```

So an item on his character was indistinguishable from stash junk and got a mule verdict like
anything else. **v1980 made this worse by making `vaultAutoAssign` run after every sweep** — a button
he pressed became something that happens on its own.

**The lane was never missing — it was discarded.** `vaultAccumApply` already sees `it.lane` on every
row and mentioned `equipment` zero times. `_laneLockNote(name, lane)` now records it, before any
branch returns, for every kind — a rune on his belt is still on his belt.

**Locked on FIRST SIGHT, not after the spec's "3+ verified reads".** The two errors are not
symmetric: a wrong lock means an item is not auto-muled and he releases it in one call; no lock means
the board tells him to move gear off his character, which is the thing he said in capitals must never
happen. Sightings are counted so the 3+ state can be shown, but they do not gate the protection.

`stash` is deliberately NOT a locked lane — a stash item is exactly what the vault manager exists to
file. The lock is releasable (`_laneLockRelease`), because a protection with no release is a trap. And
the skip is **logged** (`lane-locked`), because a lock nobody can see is indistinguishable from a rule
that stopped working.

**Verified end to end:** `Harlequin Crest`(equipment)→locked, `Annihilus`(inventory)→locked,
`Bonesnap`(stash)→**not** locked, release returns it to unlocked, and all three still register to
grail — the lock records where a thing lives and never touches whether he found it.

## REG-339 — the lane lock renders where it lives, and needs THREE separate sessions (v1984)

Two changes on top of v1983, one of them a correction he made to my design.

### He overruled my bar, and his reason was better than mine
v1983 locked on **first sight**. My argument: a wrong lock is cheaper than telling him to move gear.
His answer: *"still needs the three witnesses i want accuracy here i dont want it wrongly doing it"*.

He is right, and the reason is stronger than my asymmetry argument: **a lock that fires on one glimpse
is not protection, it is noise — and an untrusted panel gets ignored exactly when it matters.**
`PROJECT_VAULT_MANAGER.md` already specified *3+ verified reads across separate sessions*; I had
substituted my own bar for his written one.

**Witnesses are DISTINCT SESSION IDS**, the same law `vault_retro` states for grounding — "two
still-runs inside one reel are ONE witness". The row's `witnesses[].session` feed it, so three
sightings in one reel do **not** lock anything. Verified:

```
read 1 (s_A) → 1 session   not locked
read 2 (s_A) → 1 session   not locked      ← same reel counted once
read 3 (s_B) → 2 sessions  not locked
read 4 (s_C) → 3 sessions  LOCKED equipment
```

Below the bar the row is still recorded and shown as **👁 watching · n/3**, because an unmet threshold
must never look like an absence.

### It renders where the thing lives
Konyo: *"should render it based on the character/mule that its currently on… it just needs to
understand it that its our decision and if its there there a reason for it."*

`renderLaneLocks()` lists each held name with its lane ("on your character" / "in your inventory"),
the mule it is filed to when he has filed one, its session count, and a **release** button — a
protection with no release is a trap.

⚠ **What it cannot say, and does not pretend to.** The in-game CHARACTER name is captured nowhere in
this pipeline — `charName`/`char_name` appears **zero** times in `vault_retro.py`, `control_app.py`
and `tv_diablo.py`, and no frame carries a character identity. So a row states the LANE and the MULE
and never guesses a character. That gap is named as unbuilt in `PROJECT_VAULT_MANAGER.md`; printing a
name the film never read would be the fabrication this board exists to prevent.

## REG-340 — he names the character, because the film cannot (v1985)

He asked for the lock to render "based on the character/mule that its currently on". I checked
whether that is readable before building it, and it is **not**:

- a reel's `index.json` carries `sessionId` and `focus` — **nothing else**
- `sessions.jsonl` has **zero** `character` / `charName` / `profile` / `hero` rows
- `charName` appears **zero** times in `vault_retro.py`, `control_app.py`, `tv_diablo.py`
- **and it is not on screen.** A real Chronicle frame from his own footage shows the character
  SPRITE, the orbs, the belt and the skill bar. D2R prints the name only on the character panel,
  which he does not film.

Inferring "Sorc" from a sprite or a skill icon would be a guess wearing a fact — the same class as
reading a boss thumbnail's filename instead of opening it. So the field is **his**: one label per
locked item, typed once, remembered (`_laneLockSetWhere`), empty until he fills it.

That is also what he actually asked for — *"it just needs to understand it that its our decision and
if its there there a reason for it."* The board records the reason; it does not invent it. An empty
field shows a prompt rather than a placeholder name, so **"not told yet" and "told" never look alike**.

**Verified:** locks at 3 distinct sessions, `where` is `undefined` until set, `'Sorc — Blizz'`
round-trips into the store and back into the field.

⚠ **The honest limit stands:** if he wants this filled automatically, the reel must film the character
panel at least once per session. That is a capture change, not a code change, and it is the real
prerequisite — `PROJECT_VAULT_MANAGER.md` lists "no character/mule identity on a frame" as unbuilt for
exactly this reason.

### v1985.1 — the gate caught a guard that could never pass
`renderLaneLocks` looked up the mule with `window.muleById && window.muleById(a)`. **`muleById` is
never assigned to `window`** — it is a closure function the vault code calls bare (`vaultAutoAssign`
does exactly that). So the guard was permanently falsy and the mule label would have rendered empty
forever while looking correctly wired.

`test_the_board_calls_nothing_that...` refused the push and named it precisely: *"optional calls to
functions assigned nowhere — they have never run and never will: muleById"*. That is a gate earning
its keep on the exact failure class this session kept hitting — a join that reads as wired from both
ends and carries nothing.

## REG-341 — the production payload flattened witnesses, so v1984's lock could never fire (v1986)

**The v1981 scar, repeated by me one version later.** REG-339 shipped a 3-distinct-session equipment
lock and I proved it with hand-made arrays. Production sends something else.

`tv/vault_retro.py :: apply_payload` emitted `"witnesses": len(...)`, turning the list `_witness_rows`
builds into an **int**. Measured on a proposal built the way `sweep()` builds one:

```
owned row      witnesses : list, len 3
apply_payload  witnesses : int,  3
```

The board's lock does `for (i = 0; i < _ws.length; i++)`. **A number has no `.length`, so the loop
never ran, `_sids` was always `[]`, and `_laneLocked` could never reach three sessions.** Equipment
could not be locked on the only path that actually runs — while the tests stayed green because they
hand in `witnesses: [{session:'s_A'}, …]`. And `shaped` carries no `owned` key, so the board had no
raw rows to fall back to.

Every reader wants the array anyway — `witnesses[0].session`, `witnesses.length`. Nothing wanted the
int. Rows now ship; the count survives as `witnessCount`.

### Proven with the production shape, and sabotaged to prove the guard is load-bearing
```
apply_payload output → vaultAccumApply:
  Harlequin Crest (equipment, s_A+s_B+s_C) → locked 'equipment', 3 sessions
  Annihilus       (inventory, s_A)         → '' watching 1/3
  Bonesnap        (stash)                  → '' never locks
sabotage (restore len(...)) → witnesses int 3 → board collects [] → LOCK CANNOT REACH 3
```
⚠ The first sabotage attempt did **not** reproduce the failure: that list-comprehension string exists
in **two** functions and `replace(...,1)` hit the wrong one. Re-anchored on the `witnessCount` pair.
A sabotage that fails to go red proves nothing about the fix — only about the sabotage.

**Also fixed here:** `_vlog` read `it.seen[0]`, which vault items never have, so every raised/held
ledger row lost its reel and frame — the same field-name mismatch as REG-334, on the vault side. It
now reads the witness rows and accepts `session` as an alias for `reel`.

`tv/test_vault_retro.py` + `tv/test_vault_traffic.py`: **51 tests OK** after the change.

## REG-342 — one reader per Forge tab (v1987)

Konyo, with a screenshot of F·Sets showing both: *"the Chronicle AI READER for uniques should be
located only in uniques and for the tab F-SETS it should only render the Chronicle AI READER for
SETS."*

The cross-button was deliberate once — v1711 made the two Forge headers symmetric so he could
"register a uniques batch while standing on #tab-fsets". **Safe to remove now**: the defect that era
actually fixed was the REPORT NODE — a read started on one tab rendering into the other tab's hidden
div — and that fix is `_chronShotReport` fanning out to *every* `.chron-shot-report` container, which
stays untouched. Only the extra door goes. Result: `uniques` on `tab-funi` only, `sets` on
`tab-fsets` only.

### The lane question, answered from the code
He asked whether the Runes/Gems/Materials lanes are time-based and can get "stuck on looped". They
cannot:
- `_stashVisitDone` — *"once per visit per tally tab"*; each fires **once** while the stash is open
- it **resets on close**: `else if (_stashVisitOpen) { _stashVisitOpen = false; _stashVisitDone = {}; }`
- `_intakeLeaseClaim` carries `ttlMs: 120000`, so a stuck cross-document claim expires
- `_stashShutter` is "ONE truth for both lanes", preventing concurrent fires
- and TV·D does show it: the ON-AIR stage reads that shutter for its READING… state

## REG-343 — a P1 fix that was a no-op, reverted rather than shipped (v1987)

The handoff's P1: a grail tick is not stash stock, so `vaultAutoAssign` (which walks `ownedPool()`)
has nothing to file. I added `owned.add(_nm)` inside the apply, plus `_vaultEnsureDrawable` for the
`ownedPool()` membership filter.

**Measured after a real `apply_payload` run: `I·<id8>·d2r_owned` stayed `[]` and `muled` stayed `0`.**
The `typeof owned !== 'undefined'` guard silently skipped — `owned` is a `let` in a different scope
than `vaultAccumApply`. That is the **muleById defect again**: a guard that can never pass, shipping
as a fix while doing nothing. Reverted rather than shipped.

`_vaultEnsureDrawable` is KEPT — it demonstrably works (`EXTRA_ITEMS['Blood Shield']` created on a
real payload) and is the documented "universe guarantee" `tvVaultRegister` already relies on.

**Still open, stated plainly:** `chronicleApply` reports `vaulted` for a base, yet `d2r_owned` does not
gain it — so nothing reaches `ownedPool()` and nothing can be filed. That join needs its own pass with
the scope established first, not a guess at the end of an arc.

## REG-344 — the vault lease is not a tally lease (v1988)

Konyo: *"the button VAULT MANAGER this one automatically timebased should be alot longer… or some
sort of mechanism that maybe closes it automatically based on exiting the stash/inventory? is there a
way to mechanism this???"*

**Both halves — and the second already existed.** Closing on stash-exit is shipped: when the stash
closes, the poll clears `_stashVisitDone = {}` **and** sets `window._vaultAutoDone = false`, so the
vault read ends with the stash rather than with a clock. The lease is only the crash-guard
underneath — what frees the claim if the page dies mid-read and nothing cleans up.

`_intakeLeaseClaim` hard-coded `ttlMs: 120000` for three very different jobs:

| lane | job | TTL now |
|---|---|---|
| `vault_*`, `vaultcount_*` | walking a stash he is actively scrolling | **600000** |
| `runes` / `gems` / `materials` | a single photograph | 120000 |

Sizing them apart means a long vault read is no longer cut off by a guard meant for a snapshot, while
a stuck tally still frees in two minutes instead of ten.

**Still a TTL, deliberately.** A lease that never expires is a lock nobody can release — worse than
one that ends early. His "own kill switch" idea is the right next step and is explicitly NOT this: it
is the read deciding it is finished, which needs the reader to know when the stash is done. Recorded
as future work rather than faked.

### Measured, not assumed — `toggleOwned` does not register stock
Chasing REG-343 further: `toggleOwned('Bonesnap')` runs cleanly and creates **no `d2r_owned` key at
all**. And `chronicleApply`'s `vaulted` is not "put in the vault" — it is
`_landed = hasOwnProperty(foundLog, n); if (_landed) uniques.push(n); else vaulted.push(n)`, i.e.
**"toggleOwned ran and this did not land in the grail."** So nothing on the film path puts a base
into `owned`, which is why `ownedPool()` stays empty and `muled` stays 0. That is the precise
statement of the open join, replacing the vaguer one in REG-343.

## REG-345 — THE GLIMPSE: proving something is there without claiming to know what (v1989)

Konyo: *"it can also like reverse engineer my inventory type of style for like items that it doesnt
know what they are because we only have a GLIMPSE of it and view it but with NO TOOLTIP so there is
no TEXT to read… so those items can be like shown to be missing or not found or told to need to
verify."*

A nameless read is **not an empty shelf**. D2R draws no names in a grid, so the reader is right to
return `items: []` — but the CELLS are still measurable. `inventory_occupancy` separates them on
brightness alone: an empty cell is uniformly near-black (mean 4.3, std 0.6–1.0); an occupied one is
31–169 with std 20–78.

**Measured on his own reels, not fixtures:**
```
reel_s_1784984019250_95276  f_1784984209709  grid 10×4  occupied=22 free=18
                            f_1784984218860             occupied=22 free=18   ← three frames agree
                            f_1784984236715             occupied=22 free=18
reel_s_1787242455315_9654   f_1787242458369             occupied=33 free=7
2 frames REFUSED honestly ("columns pitch pinned to the search bound")
```

So the sweep can now make the third statement the board had no word for: **not "found", not
"nothing" — SEEN, UNNAMED, verify with a tooltip pass.** It never invents an item and never ticks a
grail row.

**It is free.** Pure local pixel work, no model turn, and it runs only on a frame that already passed
the stash template gate and already cost a read — so it adds nothing to a frame that was never going
to be read. This is the join Grok flagged: `inventory_lattice`/`inventory_occupancy` worked on his
film and `vault_retro.sweep` called them **zero** times.

### Two silent failures caught before shipping
1. I called `_vault_corpus()` — **which did not exist** — inside a bare `except: pass`. It would have
   thrown and done nothing, forever, looking wired. Added as a real accessor beside its twin
   `_vault_retro()`, and proven: `_vault_corpus().inventory_occupancy(his frame)` → `22/18`.
2. `_glimpsed` was never declared. Same outcome. Declared beside `_read_no_names`, the counter it
   belongs with.

Both are the muleById shape — a call into nothing, swallowed by a guard.

## REG-346 — the gate test could not tell a dead OCR lane from a broken gate (v1990)

`test_his_three_real_frames_are_no_longer_given_a_wrong_tab` went RED mid-suite on 2026-08-23
("5_1784984201581.jpg stopped being admitted at all") and PASSED on the **identical commit** minutes
earlier. Measured alone at load 30 it returns `'personal'` in 0.34s. Nothing about the gate had
changed — v1989's hunks are all in `_vault_sweep_run` (10261-10721); `stash_screen_open` is at 11302.

**The code already knew the difference and the test threw it away.** `control_app.py:11344` says it
in as many words: zero OCR lines means EITHER a genuinely blank strip (gameplay — 61 of his 68
grid-called frames, correctly refused) OR a lane that could not run, and it counts the second in
`_GATE_SILENT` instead of pretending it learned something. The same comment records this exact flake
happening before: *"this gate's own test went RED once during a run while his live session held the
OCR worker, and passed alone seconds later."* The test read every `None` as a regression.

So it now asks the counter it already had (`ca.gate_hearing()`), around each call:
- lane went **silent** on this call → `skipTest` — the run measured nothing about the gate
- lane was **heard** and the gate still refused → still fails, and now says which

**PROVEN RED FOR ITS OWN REASON** — the skip is narrow, not a way of never failing:
```
1. untouched (lane works)                  -> PASS
2. OCR lane SILENT (sabotage)              -> SKIP
3. lane HEARD but gate refuses (sabotage)  -> FAIL     ← the real defect still fails
```

### The hypothesis I measured and DISCARDED
First read of the timeouts said `OcrWorker.read` defaults to **1.2s** and the gate passes no
override, so "the cold read blows the budget" looked obvious. Measured instead of assumed, n=6 at
load 26-30: **0.21 / 0.29 / 0.29 / 0.21 / 0.29 / 0.50s, zero over budget.** Only the
process-cold first read is slow (0.90s / 0.96s across two runs) — thin headroom, but not a
demonstrated failure, so no timeout was changed on a story. Recorded because the next reader will
find the same 1.2s and reach for the same wrong fix.

## REG-347 — the sweep registered items and nothing ever reached a mule (v1991)

Konyo's ask: *"auto-arrange in mules based on the items the readers read and analyze within the
reels."* `vaultAccumApply` did not do it, and v1987's attempt was reverted for the right reason:
`typeof owned !== 'undefined'` inside that IIFE is a guard that **can never pass** — `owned` is a
`let` in `tvVaultRegister`'s closure. Its note said the real join "needs its own pass with the scope
established first, not a guess at the end of an arc".

**The scope is now measured, not assumed.** Headless Chrome, clean store, called from `window`
exactly as the apply calls it:
```
window.tvVaultRegister('Shako')
  -> {ok:true, mode:'new', mule:'uni-armor', muleName:'UNI-ARMOR'}
  d2r_owned      ["Shako"]
  d2r_muleAssign {"Shako":"uni-armor"}
```
So the apply goes through the **live door** rather than growing a second writer. Full table, driven
by real `vault_retro.apply_payload` output (not handmade rows):

| row | expected | measured |
|---|---|---|
| Harlequin Crest, equipment, 3 sessions | grail tick, never muled | ✅ ticked · `laneLocked` · absent from `d2r_muleAssign` |
| Laying of Hands | set tick via `.piece` | ✅ `"Laying of Hands (bramble mitts)"` |
| Shako, stash | owned + a mule locker | ✅ `d2r_owned` + `{"Shako":"uni-armor"}` |

**`out.muled` was structurally always 0** and looked like a measurement. It read
`Object.keys(assign).length` on both sides — and `assign` is in the same out-of-scope closure, so
both reads threw, both were caught, and the answer was 0 every time since v1980. It now counts from
`d2r_muleAssign`, the store `saveA()` actually writes, and the throw-out review bucket is reported
separately as `out.throwout` because parking something for review is not muling it.

`_vaultEnsureDrawable` (v1987) is **deleted**: it had exactly one occurrence — its own definition —
and duplicated a rule `tvVaultRegister` already enforces. Going through the real door retires it.

## REG-348 — everything the sweep filed was thrown away by the next page load (v1991)

**This is why the vault looked empty even when the chain worked.** One apply, then one reload:
```
before reload   d2r_owned      ["Shako","Cracked Sash","Laying of Hands (bramble mitts)"]
                d2r_muleAssign {"Laying of Hands (bramble mitts)":"sets-rest","Shako":"uni-armor", ...}
AFTER  reload   d2r_owned      []                    <-- all of it gone
                d2r_muleAssign unchanged             <-- orphan rows pointing at nothing
                EXTRA_ITEMS['Shako'] -> false
```

Two correct halves, never joined across a reload. `tvVaultRegister`'s UNIVERSE GUARANTEE (v739)
writes `EXTRA_ITEMS[name]` so the manager can always DRAW the item — but `EXTRA_ITEMS` is a `const`
object literal seeded at parse time and **never persisted** (89 mentions in `bible.html`, zero
writes to any store). The load-time prune at `bible.html:18511` then filters `owned` against
`_EXTRA_ITEM_SET`, built from that static constant. A runtime registration survived exactly as long
as the tab did.

**v342.16 and v465 each patched this same shape with a regex whitelist** (`_SHARED_KEEP`,
`_SOCKET_KEEP`) and v465's comment states the symptom in his words: *"every reload silently DROPPED
them, so a later intake batch looked like it did not build on top of the earlier one (Konyo's
accumulation bug)."* A regex cannot cover an arbitrary item name, so this persists the entries
instead: `d2r_tvExtraItems`, added to `_LP_FORKED` so it forks per install exactly like `d2r_owned`,
re-seeded into both `EXTRA_ITEMS` and `_EXTRA_ITEM_SET` immediately after the set is built and long
before the prune. One writer door, `window._tvExtraRemember`, so object and store cannot drift.

Measured after: `d2r_owned` and `EXTRA_ITEMS` both survive the reload. Guarded by
`tests/v1991_vault_mules_stick.spec.ts`, which asserts **after** a reload — every earlier version of
this would have passed without one.

## REG-349 — OPEN, NOT FIXED: the universe guarantee inverts the throw-out verdict

Measured on the real board, and it needs Konyo's ruling rather than my guess.

`tvVaultRegister` writes `EXTRA_ITEMS[name] = {rarity:'basic', ...}` **before** it asks
`suggestMule`. The planner then sees a known basic with a slot and files it by slot, so the
white-base throw-out verdict never survives to be seen. 5 of 5 flipped:

```
                suggestMule BEFORE the stub  ->  AFTER the stub
Cracked Sash    __throwout                   ->  uni-armor
Quilted Armor   __throwout                   ->  uni-armor
Grim Wand       __throwout                   ->  uni-weap
Stag Bow        __throwout                   ->  uni-weap
Cap             __throwout                   ->  uni-armor
```
Not destructive — nothing is ever binned — but every white base TV registers goes onto a mule
instead of into the throw-out review bucket, which is the opposite of what the planner decided.

**I built the one-line fix (ask the planner first) and REVERTED it**, because measuring it showed
the cure moves a real keeper the wrong way: with the correct order, `suggestMule('Shako')` returns
`__throwout` — "white Shako, its runewords are forged or belong in endgame". That is defensible for
a white Shako he just picked up and wrong for the `Shako` a reader read off **Harlequin Crest's base
line**, which is how the name arrives from film. The board cannot currently tell those two apart,
and picking one silently is exactly the fabrication this repo audits out. His call.

## REG-350 — `vaultAutoAssign` appeared to overwrite `__throwout`, and the instrument was wrong

Recorded so the next reader does not chase it. A probe showed `{"Cracked Sash":"__throwout"}` become
`{"Cracked Sash":"uni-armor"}` after `vaultAutoAssign()`, which reads as the review bucket being
overwritten. The source refutes it — `if (assign[name]) return;` and an explicit `__throwout` early
return.

My instrument was at fault twice over: I monkey-patched `window.suggestMule`, but `vaultAutoAssign`
calls the **bare closure-scoped** `suggestMule`, so the call counter read 0 and measured nothing
about the function under test. The store change was REG-348's prune, not an overwrite.
[[feedback-suspect-the-instrument]]

## REG-351 — the four "Auto lanes" cards promised a reel and only flipped a flag (v1992)

Konyo went looking in Tools → Vault Manager for a Shadow-AI button that **does not exist** — measured,
zero occurrences of any shadow-AI surface in `bible.html`, `control_app.py` or `tv_diablo.py`. I had
described that design to him and never built it, which is how he ended up clicking around for it.

What he was actually clicking is `quickIntake('vault')` at `bible.html:5015`. It expands the card and
arms a lane in `d2r_autoLanes`. **That is all it did.** The lane flag is only read LATER, by
`tvStashAutoIntake`, while a session is *already* recording — so on a board with no reel running, all
four cards were switches wired to nothing he could see. The card's own subtitle says "the reel reads
these", true only once a reel exists.

**Both halves existed and were never joined.** The console has had `POST /api/on` since v778
(`control_app.py:15598`); measured, `/api/on` appeared **zero times** in `bible.html`. So the board
has never once asked the console to start a reel.

Now `quickIntake` → `_laneStartReel(lane)`:
- **same-origin only** (`:17771|:17772`) — the public site must never poke a service on his laptop,
  and off-console it says so instead of failing silently
- surfaces the console's REASON, which was previously discarded. `/api/on` answers with `why` when a
  mini is counting down or the disk is under 8 GB; nothing had ever read it.

Proven against a stub on **:17771** (never :17772 — his live console was up on pid 27335 throughout):
```
ok       -> 🔴 ON AIR — the reel is recording; the vault lane reads and files what it sees.
refusal  -> ⚠ could not start the reel: already recording — seal the current session first (42s left)
file://  -> ⚡ vault lane is ARMED. Open this board from the TV DIABLO console to start the reel.
```
Verified on pixels at 1440: the say-line takes its own full-width row under the four cards, squeezes
nothing, clips nothing. `.tqu-say` is declared AFTER `.tqu-cards` on purpose — in this file the last
declaration wins and an earlier `.tqu-*` rule has silently outranked a later intent before.

**Not a bug, recorded because it looks like one:** `d2r_autoLanes` reads `{}` after a click.
`_miniOnAirOn` returns true for an unset key by design — "doing nothing yields automatic intake" — so
`{}` means all four lanes are ARMED, and an already-on lane is not rewritten.

## REG-352 — 17 tests pinned the manual door I removed, and CI has been RED on every ship since (v1993)

Konyo asked for the manual AI-intake doors to go — *"surgically remove them all… that way it forces
me and my cuzin to just hit reel session instead of anything manual"* — and v1975/v1976 did it:
`vault-intake-file`, `rune-intake-file`, `gem-intake-file`, `material-intake-file` are gone (5 file
inputs remain in `bible.html`, none of them these).

**Seventeen tests across seven specs kept seeding themselves through those inputs.** Playwright waits
for a selector that will never exist, so each burned its full 120s timeout:

```
Routine I — Playwright suite, shard 4/6:  11 failed · 330 passed (33.3m)
Error: page.setInputFiles: Test timeout of 120000ms exceeded.   ×10
```

RED on every ship since v1975 and I never went back for it. **A test that pins a retired contract is
worse than no test** — it is a red gate everyone learns to scroll past, which is how the next real
failure goes unread. That is the exact trap `sweep-dont-ask` exists to break, and I walked into it
while carrying the rule.

**The tests were not wrong about the LOGIC** they assert — dedup, shared-stash routing, cost
reporting, the throw-out triage, the cropped-flag contract. They were wrong about the DOOR. The
intake functions never moved: `window.vaultIntake / runeIntake / gemIntake / materialIntake` are all
still exported, and they are the very seam the automated lane feeds — `tvStashAutoIntake` "only
supplies a File" to these same functions.

So seeding now goes through `tests/_intake.ts` → `seedIntake(page, lane, files)`, which builds real
`File` objects and calls that function. **The specs now exercise the AUTOMATED path** instead of a
door the product no longer has — which is what integrating them should have meant in the first
place, rather than leaving them to rot.

16 call sites converted mechanically across 5 specs. Three tests asserted the doors' *existence* and
were rewritten to pin the current contract instead:
- `v205` → the manual door is gone AND `vaultIntake` (the name `tvStashAutoIntake` dispatches to)
  survives — a rename would break the automated lane silently
- `v544` ×2 → the four doors are gone, the four functions live, and tapping a lane expands the card,
  keeps the lane armed, and **reaches for a reel** (v1992)

`tests/v1975_mini_on_air_lanes.spec.ts` already asserted `doors === 0` and needed no change — it was
written after the removal and is the one that got it right.

## REG-353 — the layer above the read: names cross-checked against cells (v1994)

Konyo: *"we need an AI manager that reads and analyzes above them to cross reference and check and
verify.. so like another layer of accuracy.. maybe even two."*

**Both layers already existed and had never been introduced to each other.**

| layer | what it produces | cost |
|---|---|---|
| 0 `stash_screen_open` | is this a stash panel at all | free (OCR of tab chrome) |
| 1 `inventory_occupancy` | **how many cells are FILLED** | free (pixels) |
| 2 `claude_vault_read` | **which items are NAMED** | paid |
| 3 `vault_retro.gate()` | 2+ witnesses, conf floor | free |
| 4 lane lock | 3 distinct sessions | free |

Layer 1 produces a COUNT and layer 2 produces NAMES, about the same panel, and nothing ever compared
the two numbers. Comparing them is free and catches the one failure a reader cannot self-report:

```
named > occupied   OVER-READ — more names than filled cells. At least one name came from
                   somewhere other than the picture.
named == 0 < occ   UNDER-READ — the glimpse (v1989): something is there, no tooltip.
otherwise          the two independent layers corroborate, at zero cost.
```

**The over-read is the only fabrication signal this lane has ever had**, and it is exactly the class
behind his own complaint — *"it wrongly muled a random charm.. i dont think i even own this.. from
what picture is this here?"*

**It flags and reports; it does not bin.** A disagreement is a FINDING, not a ruling about which
layer is right — the lattice refuses honestly on some frames, and a tooltip legitimately covers
cells. The read still travels, marked with `reconcile`, and the counts reach `prop["reconciled"]` /
`prop["overRead"]` so the board can render the disagreement instead of averaging it away.

**Measured on his own frames** (occupied / synthetic named / verdict):
```
5_1784984201581   22   0 -> under-read   22 -> agree   27 -> over-read
7_1784984245418   23   0 -> under-read   23 -> agree   28 -> over-read
8_1784984208085   22   0 -> under-read   22 -> agree   27 -> over-read
```

The verdict is a real function, `reconcile_verdict()`, not an inline ternary — inline logic can only
ever be guarded by a source scan, and a source scan fails on its own reach rather than on the code.
Guarded by `TestV1994TheTwoLayersAreCompared`, including the boundary that matters
(`occupied=0, named=0` is **agree**, not a permanent glimpse on an empty stash) and the join itself.
**Sabotage-proven**: changing `n > occ` to `n >= occ` turns it red (2 failures); restoring makes it
green.

## REG-354 — the map before the names: the room, and what moved in it (v1995)

Konyo: *"like a IROBOT cleaning my house it maps out my house and it doesnt necesarily know whats
there yet.. so same here i want it to like sort of understand the reverse of it and see where we have
room."* And the layer on top: *"if two reels or a couple show this logic it should be able to also as
an extra layer of measurement and accuracy to cross reference between those reels and understand
alone that it moved from my inventory to my stash."*

Everything before this asks *what is in the panel*. This asks *what SHAPE is the panel*, which is a
cheaper question and survives having no names at all. Three kinds of square, and the distinction is
his:

- **FIXED** — occupied in ≥90% of frames. *"the space that isnt locked for the items like hordaic
  cube and my other tombs and charms.. which again should render this and lock it accordingly like
  the equipment."* Furniture, not loot. Nothing should ever suggest moving it.
- **OPEN** — free in ≥90%. *"the grey area that left is space to loot and play with for farming."*
- **CHURN** — changes between frames. Where loot actually flows.

**PROVEN ON HIS OWN FILM.** `reel_s_1784984019250_95276`, **94 of 153 frames** held a readable panel,
every one reading 22/18, and the map came out as his actual inventory:
```
FFFFF.....     F = fixed (the cube / tome / charm cluster he named)
FFFFF.....     . = open floor
FFFFFF....     ~ = churn
FFFFFF....
```
22 fixed in the top-left block, 18 open, 0 churn. **No model, no names, zero cost.**

`motion_between` is **cell-level, not total-level**, which catches the case a count comparison cannot
see at all: one item leaves and another arrives, and the total is identical. `infer_transfer` then
cross-references two panels and uses **conservation** as the check — inventory loses k squares and
the stash gains k → a stash-in, corroborated by two independent measurements and no name required.
When they do NOT balance it says `partial` and reports both numbers, because items also arrive from
the floor and leave to a vendor.

### ⚠ THE HALF THAT IS NOT PROVEN, AND WHY IT MUST NOT BE REPORTED AS WORKING
`motion_between` / `infer_transfer` are **UNPROVEN ON HIS FILM**. Every one of his 31 reels was
scanned; **not one shows the panel changing**, because none captured him actually stashing. That is
missing FOOTAGE, not a broken detector — and the two are indistinguishable unless someone says which
it is. The tests therefore drive it on constructed grids, which proves the ARITHMETIC and nothing
more. **To activate it: one reel that films the inventory, then the stash, with items moved between
them.** [[unknown-stays-unknown]]

Guards refuse the two ways this could quietly lie: a **single frame maps nothing** (one frame is a
fixture — this project has already paid for believing one), and **two different lattice geometries
are never compared square to square**, because cell (2,3) of a 4×10 grid is not cell (2,3) of a 4×9.

### The guard that caught me mid-ship
The v1994 push was **BLOCKED** by `TestRunnerIsLast`: I appended the new class *after*
`unittest.main()`, where it can never run — the exact silent-zero-coverage defect that guard was
written for in v1476, whose docstring says *"this session I appended a new test class after the
runner anyway and the suite happily reported 267 OK with my test uncollected."* I did it again, in
**both** files: `test_inventory_lattice.py` has its runner at line 173 and my six tests landed below
it. Both hoisted; both now run (19 and 4).

**And then a THIRD time in the same ship**, on `vault_corpus.py` — caught by
`TestV1928NothingRunnableLivesBelowTheRunner`, which reported six definitions below the `__main__`
guard at :370. That one is subtler than the test-class case: module-level defs below a runner guard
*do* get defined on import, so every check I ran by hand passed. They are only dead when the module
is run **as a script**, where `sys.exit(main())` fires first — so `python3 vault_corpus.py` would
have had `main()` running without them.

**THE COMMON CAUSE IS MINE, NOT THE CODE'S: I keep reaching for `cat >> file.py`.** Appending is
correct for `BUGS.md` and wrong for any Python file that ends in a runner block, which is most of
them here. Three guards caught three instances in one night and none of them was caught by reading —
each looked right, imported fine, and passed the tests I chose to run. Append to prose; **insert**
into code.

## REG-355 — the backend finally renders, and the default bucket was swallowing a fabrication warning (v1996)

Konyo's standing ask, from the top of this arc: *"i want it to visually render the backend through
the ledger visually so we can visually surgically fix anything needed future wise."*

I had built three pixel signals — `glimpsed` (v1989), `reconciled` and `overRead` (v1994) — and
rendered **none** of them. Measured before this fix: `glimpsed` had **0 readers** in `bible.html`,
`overRead` **0**, and `witnessCount` **0 readers anywhere in the repo**. I kept fixing unjoined ends
while committing three more.

**They failed to arrive twice over, and each half was silent on its own.**

1. **`apply_payload` dropped them.** It returns a hand-built dict and never copied the three keys
   through, so the board could not have rendered them however much it wanted to.
2. **`renderInbox` filed them under "nothing to do".** The v1925 split is
   `CHANGED[status]` versus **everything else** — so any status the map has not heard of falls into
   the no-op bucket by default. Measured on the real board: an **over-read** — 27 names on a panel
   holding 22, the only fabrication signal this lane has — was shown as *"2 already had — nothing to
   do"*, under the sentence *"The readers changed nothing this time. That is a clean run."*

**A default bucket that absorbs unknown statuses turns every future signal silent on arrival.** So
there are three kinds now, not two: changed · confirmed · **needs your eye**, in its own group that
does not collapse, each row naming the FRAME he can go and open.

### Caught on the pixels, not by reading
The first render put the pill straight through the why-text — *"seen but not named"* superimposed on
*"22 square(s) are visibly full"*. The DOM was correct and **every text assertion passed**; only the
picture showed it. Cause: the base `.ibx-row` is a **five**-column grid (when · name · pill · why ·
dest) and these rows carry three children, so they landed in the wrong columns. They now have their
own template, declared after both other `.ibx-row` rules because the last declaration wins here.

Guarded by `tests/v1996_pixels_reach_the_ledger.spec.ts`, which pins **the bucket** and not merely
the row — including `expect(sum).not.toMatch(/5\s*already had/)`, the exact wrong reading — plus a
geometric overlap check that would have failed on the first render.

### Harness note, so the next reader does not lose an hour
`Page.captureScreenshot`'s `clip` is in **page** coordinates while `getBoundingClientRect()` is
**viewport**-relative. On a scrolled page the difference is exactly `scrollY`, and the result is a
plausible **black rectangle** rather than an error. `chrome-cdp-mac §3` warns about this for
`captureBeyondViewport:true`; it applies with `false` too. Add `window.scrollX/scrollY` to the clip.

## REG-356 — the one payload the glimpse was built for bailed out three lines in (v1997)

`vaultAccumApply` opened with:
```js
if (!items.length && !(p.throwOut||p.suggestions||[]).length)
  return { ok:false, why:'the payload carried no items' };
```
The pixel evidence is carried by **exactly the payload that has no items**. The glimpse (v1989)
exists for a read that named nothing while the cells are visibly full; an over-read (v1994) can land
on a frame whose names were all rejected. So the single case the whole feature was built for returned
early, before anything could reach the ledger.

**CI caught it; I did not.** My own probe fed a payload containing a real named row (`Shako`), so the
early return never fired and the render looked perfect — three rows, correct bucket, clean pixels.
The spec passed `items: []` and CI came back `1 already had — nothing to do` with **no eye bucket at
all**. That is the blind-fixture shape exactly: a fixture friendlier than production, and a green
read taken from it. The lesson is not "write better fixtures" — it is that the fixture and the
production payload differed in the ONE field the feature keys on, and I chose the fixture.

"Nothing to apply" now means nothing to apply **and nothing seen** — never merely nothing named.
Re-measured against CI's exact payload: `0 changed your grail · 1 already had · **3 need your eye**`.

## REG-357 — the function that shapes every production payload had never been executed (v1998)

Measured: **`apply_payload` appears in ZERO test files.** It owns the contract between `vault_retro`
and the board, and it is where REG-341 lived — it emitted `"witnesses": len(...)`, turning the list
`_witness_rows` builds into an int. Every reader on the board treats it as an ARRAY
(`witnesses[0].session`, `witnesses.length`), so a JS loop over a number simply never ran and the
3-session equipment lock **could not fire on a real apply**. It locked fine in the tests that
existed, because none of them went through this function.

Grok's read of the same gap: *"No committed test asserts apply_payload items have list witnesses…
Without this, REG-341 is a comment."* It was a comment. Six tests now pin the shape:

- witnesses is a **list of rows**, `witnessCount` rides beside it as the int
- the board can count **distinct sessions** the way the lane lock does, and every row still carries
  `frame` / `lane` / `conf` — provenance lives on those dicts and nowhere else
- a junk witness is dropped while `witnessCount` still counts what the sweep **saw**, because
  collapsing those two hides that something was dropped
- the v1996 pixel evidence survives the shaping
- a refused proposal returns `[]`, never `None` — the board branches on both
- it **mutates nothing**, which is the law the whole module rests on

**Sabotage-proven, and carefully**: the anchor is the `witnesses`/`witnessCount` PAIR, because the
list-comprehension alone appears in two functions and a previous attempt at this patched the wrong
one and went green. Restoring `"witnesses": len(...)` → 3 failures; reverting → 27 pass.

## REG-358 — the free pixel lane could fail silently, which reads as an empty stash (v1998)

Both pixel call sites sat in `except Exception: pass`. A missing `vault_corpus`, a broken lattice or
a renamed function would produce **zero glimpses and zero complaint** — identical to "his panels were
empty". Not hypothetical: v1989 shipped a call to `_vault_corpus()`, a function that **did not
exist**, inside exactly such a block; it would have done nothing forever while looking wired.

The lane now records the first failure once — it runs per frame, so a per-frame print would bury the
run — reads it out at the end (*"so 'no glimpse' and 'no cross-check' this run mean NOTHING WAS
MEASURED, not that the panels were empty"*), and sets `prop["pixelLaneError"]` so the board can tell
the two apart.

Guarded with **AST, not a grep**: the question is whether the handler for the try block containing
the pixel calls is a bare `pass`, and a text search cannot see block structure. Sabotage-proven —
restoring one bare handler fails with `still swallows into a bare pass at line 10789`.

## REG-359 — the module that declares the law had zero callers, and its vocabulary was blind (v1999)

`tv/lane_lock.py` states it in its own words — *"THE LAW: AT MOST ONE LANE IS EVER UNLOCKED"* — and
**only tests imported it**. Zero production callers. A module that documents a law and enforces
nothing is the `muleById` defect at module scale.

**Why it could not join the VAULT sweep, written down so nobody tries.** `VAULT_READ_PROMPT` never
asks for `chronicleTab`, so `lane_for()` on that path can only ever answer `"vault"` — a gate that
can never refuse. The signal lives on the **chronicle** path, where `READ_PROMPT` asks for `stashTab`
AND `chronicleTab` on every frame (`tv_diablo.py:264`). So the join is at `chronicle_kind()`.

**The case it catches**: the reader fills BOTH — `scene=chronicle`, `chronicleTab=uniques`,
`stashTab=personal`. The vault sweep and the chronicle sweep are separate runs over the SAME reels,
so such a frame can be filed as OWNERSHIP by one and as a grail FIND by the other. `lane_lock` states
why that matters: *"a Chronicle row filed as OWNERSHIP claims he owns an item he has merely seen
listed, and a stash item filed as a Chronicle FIND ticks a grail row he never earned."*

### And the vocabulary did not match its own input
`VAULT_SURFACES` listed `stash/inventory/equipment/runes/gems/materials`, while `stashTab` carries the
RotW **left tabs** — `tv_diablo.py:259` says so verbatim: *"Personal·Shared·Gems·Materials·Runes"*.
Three overlapped by luck. **`personal` and `shared` — the two he is in most often — did not.**
Measured before the fix:
```
chronicle_kind({scene:'chronicle', chronicleTab:'uniques', stashTab:'personal'})
  -> 'chronicle-uniques'      # should be None; the frame claims both
```
So the ambiguity guard was blind on precisely the case it exists for.

They are **folded to `"stash"`**, not added as surfaces of their own: `surface` is compared against
`vault_retro.LANES` (`stash/inventory/equipment`) and a lane named `personal` is a value no consumer
knows. Recognise the input, keep the output vocabulary — the first attempt renamed the surface and
correctly broke `test_stash_open_unlocks_the_vault_and_locks_the_chronicle` (`'personal' != 'stash'`).

**An unavailable law is not a violated one**: if `lane_lock` cannot be imported, the sweep reads
exactly as before rather than refusing every page. Guarded, and sabotage-proven — removing the fold
turns the ambiguity test red while the other four stay green.

## REG-360 — the shadow reader existed for 1068 versions and had no switch (v2000)

Konyo: *"is there a way to like have an AI lurking in the shadows reading the game ingame and
sometimes firing whats needed? … for this it should have an ON/OFF for shadow AI a button to click a
cool widget."* Then, hunting Tools for it: *"where exactly is ther button for SHADOW AI"*.

**There was none.** Measured: zero shadow-AI occurrences across `bible.html`, `control_app.py` and
`tv_diablo.py`. I had described the design to him and never built it, so he spent time clicking
around for a button that did not exist. I also told him it was *blocked* because "control_app exposes
zero HTTP routes" — **that was wrong**: it exposes 38, one of which (`/api/on`) I used the same night.

**The reader has existed since v932.** `_text_eye_loop` OCRs the live frame and turns new item-ish
text into a PRIORITY read. What it never had was a switch he could reach: `TV_TEXT_EYE` is checked
**once, before the loop starts** — a boot flag — and an env var of a running process cannot be
changed from outside anyway.

**One writer, one reader, its own file.** `shadow_ai.json` is written only by the console and read
only by the agent, so there is no lock and no lost write. It is deliberately **not** `state.json`:
the agent owns that file, and a console also writing it is the `pt_signals.json` shape exactly —
four programs whole-file-writing one path and erasing each other seconds later. It rides
`_fixture_root` for the same reason `STATE` does, so a test that repoints `TV_HIST` can never switch
off the eye in his real world.

**Absent means ON, and unreadable means ON.** The eye has run by default since v932; a fresh
checkout, a wiped frames dir or a truncated write mid-save must never silently blind it. Off is only
ever something he chose.

**Three facts, three surfaces, never merged into one lamp.** `on` is his choice · `available` is
whether local OCR exists at all · `recording` is whether a reel is rolling. That separation is the G5
scar paid forward: G5 sat dark for weeks reporting `mode=primary, calls=0` because one object
answered "is it ready" and "was it asked" with the same word. A lane that **cannot** run shows amber
and disabled — never the same grey as one he switched off.

Verified against a stub on **:17771** (never :17772 — his live console), all four states rendered and
read on the pixels; and the console→agent round trip measured directly: `_shadow_set(False)` →
`tv_diablo.shadow_ai_on()` returns `False` on the next check, both halves resolving the same path.

## REG-361 — retention: the obvious rule would have deleted 1.1 GB of unread footage (v2001)

Konyo: *"for storage optimization … it should delete the oldest and older reel session after it
analyzes them and ledgers them and registers and they all get funneled properly as they should and
are."* On keying it to swept + evidence banked: *"its fine"*.

**Measured on his 31 reels before writing a line of it**, because the obvious rule is the wrong one:

| bucket | reels | MB |
|---|---|---|
| read — evidence banked (`pages>0`) | 6 | 254 |
| **sealed with 0 pages** | **12** | **1166** |
| never chronicle-swept | 13 | 1058 |

"Delete what has been swept" takes 18 reels and 1420 MB — and **1166 MB of that was never actually
read**. A 0-page seal does not mean *done*; it means *this reader found nothing*, and the engine
already knows it, because it reopens exactly those on its own:
```
🔓 8 reel(s) reopened - sealed with 0 pages by an older reader (now p1839)
```
So the safe rule is the inverse of the obvious one: **footage that has yielded nothing is the
footage most worth keeping.** Free disk is 13 GB against an 8 GB ON AIR floor, so there is room to
be careful.

**Five bars, each because deleting his film cannot be undone**: evidence banked (`pages ≥ 1`) ·
sealed by **both** lanes · the newest 5 always kept · oldest first · stops the moment the target is
met. `--apply` refuses without `--yes`.

**On his real tree it selects NOTHING today, and that is the correct answer**: `vault_swept.json`
does not exist, so the vault manager has never sealed anything, and no reel has been through both
lanes. The report says exactly that rather than printing an empty list.

Which is precisely why the fixture tests matter — **on his data the safe answer and a broken one are
the same output.** Nine tests on temp dirs (never his frames) prove it can select, that a 0-page seal
never qualifies however old, that `keep_recent` protects the newest, that it stops at the target,
that `--apply` without `--yes` deletes nothing, and that it removes the right directory and leaves
the rest. Verified after the run: his 31 reels and 2.8 GB are intact.

## REG-362 — a vault seal was a life sentence, and the vault reader had no version at all (v2002)

Found while building retention (REG-361), which needs `vault_swept.json` to mean something.

The **chronicle** lane learned this in v1830: a seal records `{ts, classified, pages, promptVer,
agentVer}`, and a reel an older reader sealed with *nothing* is **reopened** when the prompt improves. Its own words: *"only the 'I looked and there was nothing' claim expires."*

The **vault** lane never learned it:
- the seal recorded `{"ts": ...}` — no rows, no reader
- **`VAULT_READ_PROMPT` had no version constant at all** — zero occurrences of any `VAULT_PROMPT_VER`
- the skip list was `not in swept`, so **any** sealed reel was skipped forever

So a vault verdict was permanent however much the reader improved — the same "stale verdict made
permanent" defect v1830 fixed on the other lane, still live on the lane whose mistakes reach his
stash. And it is not academic: the reader was rebuilt in v1785 (`claude_vault_read`, the seam that
had never existed), so any reel sealed before that was sealed by a reader that could not produce
rows at all.

Fixed as the exact mirror of the chronicle rule:
```
unreadable record  -> stay sealed   a broken row is not a licence to re-spend his subscription
rows > 0           -> stay sealed   the findings outlive the reader that found them
rows == 0          -> reopen ONLY if a different vault prompt is current now
```
`VAULT_PROMPT_VER = "vp2002"` now exists beside the prompt, with a note to bump it whenever the
prompt changes; the seal records `{ts, rows, promptVer, agentVer}`; and the sweep prints which reels
it reopened, in the same words the chronicle sweep uses.

**Every row he already has is `{"ts": ...}`** — no rows, no promptVer — so all of them reopen. That
is deliberate: without it the ledger he has today would stay frozen under whatever reader wrote it.

Sabotage-proven: putting the seal back to `{"ts": ...}` turns the guard red.

### Still open, and it costs money every sweep
A stash **grid** has no names by design — proven on his own film, where the reader correctly returns
`items: []`. Those frames pass the template gate, take a **paid** read, produce no rows, seal
nothing, and are paid for again next sweep. The v1994 reconciler now gives the signal that would let
a *confirmed* nameless read seal safely (cells occupied + zero names = a complete answer, not a
failure), and v2002's reopen net makes such a seal recoverable. Not wired yet — the safety net had to
exist first.

## REG-363 — the sweep paid to re-read the same nameless grids forever (v2003)

"No rows" is **two different facts** and was treated as one.

A sweep that **failed** must never seal — that safeguard is from v1785 and it stands. But a sweep
that **read every frame and found nothing nameable** has given a *complete* answer, and D2R
guarantees it will give the same one forever: a stash **grid prints no names at all**, only the hover
tooltip does. Proven on his own film, where the reader returns `items: []` and is right to.

Until now those frames passed the template gate, took a **paid** read, produced no rows, sealed
nothing, and were paid for again on the very next sweep. Forever. That is the leak, and it is the
whole reason `vault_swept.json` has never existed on his machine.

**Five bars, and any one refuses** — each is a way the answer could be incomplete:

| bar | why |
|---|---|
| something was read | a sweep that read nothing knows nothing |
| the pixel lane worked | v1998's `_pix_err` — no cross-check means no verdict |
| no over-read | a frame naming MORE than its panel holds is not settled |
| **every** read frame reconciled | `len(reconciled) == reads`, or some frame went unchecked |
| every verdict settled | only `under-read` (cells full, no names) and `agree` (0 vs 0) |

**It is a pause, never a life sentence.** v2002 records the reader on the seal, so the moment
`VAULT_PROMPT_VER` changes every one of these reopens by itself — which is exactly why the two are
separate versions: the net had to exist and be proven before this could ship.

Extracted to `vault_seal_is_definitive()` rather than left inline, for the same reason
`reconcile_verdict()` was: inline logic can only be guarded by a source scan, and a source scan fails
on its own reach. Guarded, including junk in the reconcile list — a non-dict entry must not satisfy
the length check and then be waved through. **Sabotage-proven** on the subtlest bar: removing the
"every read frame was cross-checked" check turns it red with 2 failures.

## REG-364 — I swept my own night's work and found the defect I keep fixing in his (v2004)

After shipping v1989–v2003 I ran the audit I keep running on his code, against mine. Three of my own
additions had **zero production callers or readers**:

| mine | state |
|---|---|
| `space_map` | **0 call sites.** Built it, proved it on his film — 94 of 153 frames of one reel, and the map came out as his actual inventory — and never joined it. |
| `infer_transfer` | 0 call sites. Honestly blocked: no reel of his shows the panel changing. Named, not faked. |
| `pixelLaneError` | written by v1998, **read by no surface**. The signal that tells "nothing was measured" from "the panels were empty" was itself invisible. |

`space_map` is the iRobot map he asked for — *"see where we have room"* — and I left it exactly as
unjoined as `lane_lock`, which I had fixed **hours earlier**. It now runs at the end of a sweep on the
panels that already measured (free, 3+ frames required), rides the proposal as `room`, and renders as
a ledger row: *"22 square(s) never move (cube / tomes / charms — treat them like equipment), 18 are
open floor."* Which is his ruling made visible: furniture is shown, never suggested for a move.

### And the same line broke twice
The apply's early return counted `glimpsed + overRead` only, so a payload whose **sole** evidence was
the room bailed out with *"the payload carried no items"* — **the same defect v1997 fixed for the
other two, in the same line, eight versions later, in my own fix.** The instance had been fixed; the
shape had not.

The evidence keys are now enumerated **once**: `['glimpsed','overRead','reconciled','room',
'pixelLaneError']`. A new signal is added there and nothing else has to remember it. Guarded by two
new specs — one that applies a room-only payload and asserts it renders, one that asserts a silent
lane says `NOTHING WAS MEASURED` rather than looking like an empty stash.

## REG-365 — LAW19 was enforced for DOM ids only, and the same shape cost six versions in one arc (v2005)

`test_reachability.py` states LAW19 — *"every symbol a change adds must have a caller AND a writer"* —
and enforced it for **DOM ids** and **`typeof` guards**. The identical shape in Python and in the
payload contract was unguarded, and it cost six versions in one night, **four of them mine**:

| | |
|---|---|
| `lane_lock.py` | declared "AT MOST ONE LANE IS EVER UNLOCKED", zero production callers (REG-359) |
| `vault_corpus.space_map` | worked on his film and nothing called it (REG-364) |
| `prop["glimpsed"]` / `["overRead"]` | written, read by no surface until v1996 (REG-355) |
| `prop["room"]` / `["pixelLaneError"]` | the same, eight versions later (REG-364) |

Every one looked wired from its own end — that is the defining property. It is mechanically
checkable, so it must not depend on anyone remembering to look.

**Two guards, both with an allowlist that demands a REASON** (the existing file's own principle: *"an
allowlist you have to justify is the point; one that grows silently is not"*), and both with a second
test that fails when an entry stops being an orphan — an excuse that outlives its subject is how a
list stops being read.

Four public functions had no caller: `infer_transfer` (blocked on FOOTAGE — no reel of his shows the
panel changing), `may_write` (a wrapper whose only honest caller would compare a value to itself),
and two pre-existing helpers now visible instead of silently tolerated. **"We might need it later" is
explicitly rejected** — that was the reason all four defects already had.

### The guard read its own documentation and passed
Sabotage caught it: unjoining `witnessCount` left the payload guard **green**, because the comment
explaining why `witnessCount` matters contains the word `witnessCount`. The exact scar already on
record. Comments are now stripped before searching — **non-greedy**, because an unbounded `/*…*/`
regex once ate 16.9% of `bible.html`, and the result is size-floored so a runaway strip fails loudly
instead of passing everything. (Measured: 5,828,213 → 4,791,192 bytes, 17.8% — this file really is
that commented.)

With honest eyes it immediately found one more: **`lastSeenTs`**, whose single "reader" was prose.
`vault_retro` computes it as the max ts across every sighting and the board dropped it, so a row read
six weeks ago and one read this morning arrived identical. Both it and `witnessCount` are now
carried — sightings and sessions are different numbers, and twelve sightings across two sessions is a
different claim from two across two.

## REG-366 — the retention tool had no caller, and its threshold disagreed with itself (v2006)

`reel_retention.py` shipped in v2001 correct and complete, and **nothing imported it** — the
module-level version of plumbing with no tap. Konyo asked for the oldest reels to go *"after it
analyzes them and ledgers them and registers"*, which means the tool has to RUN; as shipped it ran
only if he opened a terminal.

A vault sweep now reports it: how much footage has given up its information, and how close the disk
is to the **8 GB floor below which `/api/on` refuses to record at all**. It **reports and never
deletes** — `--apply --yes` stays something he types, because deleting his film cannot be undone.

Measured on his tree as this shipped: 31 reels, 0 reclaimable (no reel swept by both lanes yet),
**12.0 GB free — 4.0 GB of headroom above the recording floor.**

### And the threshold disagreed with itself
The first cut compared the **unrounded** float in python (`_free_gb < 12.0`) and the **rounded** one
on the board (`rt.freeGb < 12`). His disk measured **12.0077 GB**, which displays as `12.0` — so
python would have warned and the board would have stayed silent, about the same disk, in the same
run. Two halves, two thresholds, one fact.

The side holding the real number now decides and ships `low` (and `floorGb`); the board renders the
verdict it was given and re-derives nothing. Guarded both ways at the same `freeGb`: the board must
not invent a warning the sweep did not raise, and must not swallow one it did.

## REG-367 — two guards on the template gate were permanently dead, and his current film can hold them (v2007)

`TestStashPanelOpenGuard` has two real-frame tests that had not run since the corpus was pruned —
v1712 called it honestly: *"PERMANENTLY skipped in both venues… A skip that reads like a passing
environment check is the friendlier face of a gate that never runs."* It kept the pure-predicate
tests covering the DECISION and wrote down exactly what was gone:

> *"What is genuinely lost here is only the END-TO-END path (crop → features → label) on real
> pixels, which is why these are kept rather than deleted."*

**The fixtures were pinned to REEL NAMES, and reel names get pruned.** Pin to a PROPERTY instead and
the coverage survives any pruning. Measured across 199 sampled frames of his 31 current reels, every
case the pruned pair covered is present:
```
gameplay / gameplay        122
stash    / stash            43
stash    / stash-default    31
gameplay / not-d2r           3     <- the wallpaper bug's exact verdict
```
Three tests now run on whatever footage exists — **0 skips on his machine, every push** — including a
cross-check that the two INDEPENDENT detectors (`stash_screen_open`'s tab-chrome OCR and
`classify_stash_grid`'s pixel geometry) never flatly contradict each other, since the vault sweep
leans on both.

### The first cut skipped instead of failing, and sabotage caught it
Anchoring the search on the **verdict** (`pick == "not-d2r"`) meant that breaking the predicate
produced no not-d2r frames at all — so the search found nothing and the test **skipped**. `OK
(skipped=1)` against a deliberately broken gate. That is the *"a gate that always skips is the same
defect"* scar, in my own new test, the first time I ran it against a broken predicate.

Re-anchored on `frac_dark` / `dark_cols` — measurements of the picture, which survive any change to
the rule that reads them. Now the frame is still found and the ASSERTION fails:
```
AssertionError: f_1784984130673.jpg: a LIT PHOTOGRAPH (frac_dark=0.0, dark_cols=0 — no game
content) classified as 'stash-runes'. This is the wallpaper bug.
```
The original defect, reproduced end to end on his real pixels, for the first time since it was fixed.

## REG-368 — three guards had been dead for ~430 versions because one launch path was mistaken for the machine (v2008)

`browser_can_load_localhost()` measured `--dump-dom` over `http://127.0.0.1` and concluded this Mac
cannot load a loopback page. The measurement was right; **the conclusion was drawn one step too
wide** — and v1490's own note says so in the same breath:

> *"Playwright drives the same binaries over the same loopback fine, so it is this launch path on
> this machine, not the network and not the page."*

CDP is a third path and it works here. **Measured on the identical loopback URL, same browser, same
server: `--dump-dom` → False, CDP → `"LOOPBACK_OK"`.**

What was skipping is the install-scoped key family — three real bugs, one of which greeted a fresh
machine with **someone else's chronicle** (`HOLY GRAIL 243 / 403 · 60% claimed`):

| | |
|---|---|
| REG-069 | a key read RAW |
| REG-075 | a gate on a differently-named function |
| REG-076 | the console read BARE while the board wrote `W·` |

The test that executes the shipped `lsFork` against seeded storage — written *because* "a grep-level
assertion is not enough, all three passed a reading" — has not run since. **All four now run and
pass, on the machine that has the data, every push.**

### 297s → 26.7s, and the reason was another call into nothing
The first cut worked and cost **297 seconds** — `_dump_dom` tried both headless modes (45s each) per
call before reaching CDP, on a machine where the probe already knew they were doomed. So the probe
now records **which** path answers and `_dump_dom` asks it first — the v2006 rule again: the side
that measured it decides, nobody re-derives.

That fix appeared to do nothing (93.6s per call, unchanged) because it called
`js_syntax_gate.loopback_path()` **without importing it** — the module is imported locally inside
the test methods, not at module scope, so it raised `NameError` into my own `except Exception: pass`.
**Eighth instance of that shape in one night, third of them mine**, and caught only by timing a
single call instead of trusting the change. A second one in the same session: `_cdp_can_load_localhost`
used `time.time()` in a file that never imports `time` — same swallow, same silence, found the same
way.

`websocket` is allowlisted as a **GUARDED** import only. It is optional by construction: absent, the
helper returns None and every caller skips exactly as before. CI is deliberately not given the
dependency — its `--dump-dom` may well answer, and adding a package to two workflows to enable a
fallback nothing there needs is cost for nothing. Sabotage-proven: a **bare** `import websocket`
still fails the guard.

## REG-369 — the fresh-machine test loaded nothing, and the suite got FASTER by testing more (v2009)

`TestAFreshMachineStartsEmpty` has its own local `load()` — it does not go through `_dump_dom`, so
v2008's fallback never reached it. It was skipping with *"the browser did not finish loading
bible.html within 45s in ANY headless mode"*, which is true and was being read as a machine fault.

**CDP loads the same 5.8 MB page in 7.7 s and hands back 9.26 MB of DOM.**

The test now runs and skips for an **honest** reason instead: *"this browser derived machine='mac',
so there is no W· world to check"* — a real environment fact, not a broken harness.

**The profile had to travel with it.** The test loads `bible.html` so the board initialises ITSELF,
then loads a probe page that reads what that boot wrote — both loads must share one
`user-data-dir`. A helper minting its own profile would quietly test a different question: an empty
browser reading an empty store, which passes for the wrong reason. `_dump_dom_cdp` now accepts a
caller's profile and does not delete what it did not create.

### The suite got faster by running more
Both loaders now ask `loopback_path()` before trying anything, instead of burning two 45-second
attempts per call that the probe already knows are doomed:

| | before | after |
|---|---|---|
| the three install-key guards | skipped → 297 s | **26.7 s** |
| the fresh-machine test | skipped → 204 s | **24.4 s** |
| **whole `test_control` suite** | 349 s, 7 skipped | **268.9 s, 4 skipped** |

699 tests, OK. All four remaining skips are honest facts — PowerShell is Windows-only, `machine='mac'`
has no `W·` world, and two pruned-fixture tests are superseded by v2007's discovered-frame versions.
None of them is a harness that cannot run.

## REG-370 — a caller with no symbol: the shape that hit eight times now has a gate (v2010)

A reference to a name nothing binds. Outside a `try` it crashes loudly and is fixed in a minute;
**inside one it is swallowed and the code looks perfectly wired forever.** Both halves read fine from
their own end — that is the defining property, and it is why reading never catches it.

Three that shipped in this arc, all mine:

| version | the call | what it did |
|---|---|---|
| v1989 | `_vault_corpus()` — a function that did not exist | inside a bare `except: pass`; would have done nothing, silently, forever |
| v2008 | `js_syntax_gate.loopback_path()` without the import | the module is imported LOCALLY inside the test methods, so the name was undefined at module scope. Timing did not move — 93.6 s per call, twice — and the shortcut **looked** wired |
| v2008 | `time.time()` in a file that never imports `time` | same swallow, same silence |

LAW19 already covers *a symbol with no caller* (v2005) and *a payload key with no reader*. **This is
the third face: a caller with no symbol.**

### It uses CPython's own symbol table, and the hand-rolled version is why
A hand-rolled AST walk was tried first and produced **59 findings, nearly all false** — closure
variables, parameters, module dunders — because getting nested scopes right *is* writing pyflakes,
which is not installed and would be a dependency CI lacks. `symtable` is the compiler's own answer to
"what scope does this name resolve to", it is stdlib, and it is correct by construction.

**Currently zero findings across the tree** — which is exactly when a guard must be asked whether it
can go red. Sabotage-proven twice: on a synthetic file carrying all three real shapes (both bugs
caught, and closures / parameters / imported names correctly ignored), and by reintroducing the exact
v2008 bug into `control_app.py`, which fails with
`control_app.py: 'js_syntax_gate' in _v2010_sabotage()`.

## REG-371 — throwWhy was in the prose and nowhere in the shape (v2011)

The exact mirror of v1903, in the same prompt. That version found `throwOut` **in the JSON schema and
nowhere in the prose** — *"an elaborate safety mechanism fed by a field nobody was ever asked to
fill."* This is the other direction:

```
prose:     "When you set it true, also give throwWhy = a short reason in your own words"
template:  {"name":…,"kind":…,"count":…,"throwOut":false}          ← no throwWhy
```

A model told to reply with **STRICT JSON matching a template** emits the template's keys. So the
reason was requested in prose, never in the shape, and never arrived.

**And the loss was invisible**, which is the part that matters. `vault_retro` read it as
`or "the reader flagged it as junk"` — so **every** throw-out suggestion in his review bucket carried
the same sentence, and it read like the reader's own words rather than a default standing in for one.
That default now says it is one: *"no reason given by the reader — flagged as junk on the throwOut
flag alone."*

`VAULT_PROMPT_VER` moved `vp2002 → vp2011`, which is v2002's machinery doing its job: a better reader
now exists, so rows==0 seals reopen and those frames get looked at again.

### Why it matters for REG-349
The prompt already asks the reader to tell *"a WHITE or GREY base with no sockets and no magical
text"* from *"a named unique or set item"* — which is exactly the distinction `suggestMule('Shako')`
cannot make from a string. **The eye that saw the item has the information the name matcher lacks**,
and it can now say WHY in its own words. That does not decide REG-349 — still his ruling — but the
evidence for it will no longer be a generic sentence.

### The guard, and its own near-miss
The two halves are now pinned: every field `normalize_item` reads off a raw item must be one the
reader was actually asked for. Sabotage-proven — removing `throwWhy` fails twice, once generally and
once by name.

⚠ The first cut looked for **`_row_of`**, the name Grok's handoff used. There is no such function; it
is `normalize_item`. The guard **refused rather than passing on an empty set**, which is the only
reason the mistake surfaced in one run — a guard that cannot find its subject must fail, never report
"nothing wrong here."

## REG-372 — the launcher raced itself and killed a live session (v2012)

`start_tvd_mac.sh` frees `:17772` before binding, which is right — v1379.1: a double-click must boot
THIS checkout, never window-only onto a stale headless. It was **unconditional**, so two launches
close together race. Measured in his own `control_app.log`, 2026-08-23, after he closed the window
with ✕:

```
01:30:01  auto-pull: fast-forward ok   → native window up
01:30:21  auto-pull: fast-forward ok   → window gone (signal-SIGTERM)
01:30:51  auto-pull: fast-forward ok   → window gone (signal-SIGTERM)
```

Three launches in fifty seconds, each SIGTERMing the one before it, each running the exit safeguard
and stopping ON AIR. **Had he been recording, that is a session destroyed by a race with itself.**

**Now:** if something is already listening and it is younger than 25 s (the supervisor cycles at 20 s;
a console binds in a few), another launch is still coming up — stand down rather than take the port.
An incumbent that is genuinely old is stale and still gets replaced. `TV_FORCE_PORT=1` restores the
old behaviour for the case this gets wrong: a crash-looping console would hold the port with a
forever-young pid.

Proven on a **throwaway** port, never `:17772`: young → STAND-DOWN · old → PROCEED · override →
PROCEED · free port → PROCEED. The test drives the function **extracted from the shipped script**,
not a copy — a copy passes while the real file rots. Sabotage-proven: deleting the loop fails both
tests by name.

### Two mistakes of mine on the way here, both worth the record
**I blamed the wrong thing first.** Those three `auto-pull` lines look like a poller reacting to a git
push; auto-pull runs **once per launch**, twenty lines above the kill. Reading them as a timeline of
cause pinned it on a push nine minutes earlier, and I told him so. The lines are a symptom of
relaunching, not a cause. [[feedback-suspect-the-instrument]]

**I called `_reap` on a process I had not put in its own session.** Its docstring states the
precondition outright — *"the launcher is started in its own session, so ONE killpg reaches the
renderer grandchildren"* — so `os.getpgid()` returned the **test runner's** group and `killpg`
SIGKILLed the suite mid-run: one dot, exit 1, no summary, no traceback. Using a helper without
honouring its documented contract.

## REG-373 — why the vault is empty, answerable for free (v2012)

`tv/vault_accum.json` has been 72 bytes of empty since 2026-08-20, and finding out WHY required
paying for a sweep. Empty has three causes needing three different actions — no footage · footage but
no stash panels · panels but no readable names — and **an empty file looks identical whichever one it
is**.

`tv/vault_doctor.py` answers it from his own film: local pixels only, no model turn, no console, no
network. It runs while the console is down, which is exactly when someone wants to know. Doctrine
borrowed wholesale from `chronicle_doctor`: reports, never fixes, never guesses; OK / MISSING /
UNKNOWN, and an UNKNOWN is never dressed as a failure.

Measured on his tree the moment it was written:
```
🟢 footage        31 reel(s) on disk
🟢 stash panels   10 of 155 sampled frame(s) are a stash panel
🟢 panels measure 10 of 10 panel(s) measured
🟢 anything there 220 occupied cell(s) across 10 panel(s) — there IS loot in this footage
🟠 readable names ZERO named items, and 220 cell(s) are visibly full. D2R prints NO names in a
                  stash grid — a name exists only in the HOVER TOOLTIP.
🟠 sealed reels   vault_swept.json does not exist — retention has nothing it may delete
```

**220 items are visibly in his stash and not one is nameable.** That is the whole answer, and it was
previously invisible. It samples MID-REEL on purpose: sampling the first frames found zero stash
panels on footage that had ten — a biased sample that nearly produced "your film has no stash in it".
