# RESUME HANDOFF — Unify-every-ID-card master goal (paused for PC restart)

> **Written 2026-06-06 by CC** so nothing is lost while Konyo restarts the Mac to
> update macOS (D2R-on-CrossOver Rosetta fix). Pick up here next session.

## Master goal (dominant, ongoing)
Unify **every** loot-dropping entity's ID card to the rich **Baal boss-card
format** — detailed, enriched, unified. Hard constraints:
- **ZERO FABRICATION** — no invented odds/data; flag gaps with `.zd-note`.
- **ADDITIVE ONLY** — "nothing gets cut out." Enrich/wrap, never delete content.
- Visually clean "eye candy."

## Shipped this session (DONE — do NOT redo)
- **v88** — Herald ladder research (#49) + 5 tier-card enrichment (#50). commit `7fa0929`, deployed, md5 parity confirmed, suite green.
- **v89** — tab-ref section-header unification (#47): 8 bare `<h2>` → collapsible
  `.sec-h`/`.sec-body`. v50 test innerText→textContent. New v83 "section-header
  parity" guard. **Shipping status: see bottom of this file** (commit/deploy/push
  state recorded once complete).

## REMAINING LIST (in priority order — resume here)

### #53 — Batch 3: hover-glow unify  ✅ SHIPPED (v90)
Fresh cross-section sweep. Goal: every clickable item/row/chip uses the SAME
hover-glow treatment (the golden Baal-card hover). Currently inconsistent across
tabs. **Not started** — deliberately deferred from the pre-restart rush because
it's a multi-file CSS/markup sweep with site-wide reach; better done with a clean
session than crammed before a restart. Steps:
1. Grep the existing hover/glow CSS classes (`.item-tile:hover`, `.source-chip:hover`,
   `.zd-item-click:hover`, boss-row hovers, etc.) — inventory the variants.
2. Pick the canonical golden hover (the Baal-card one) as the target.
3. Unify the others to it (additive — don't strip existing transitions that tests assert).
4. Add a v83 invariant locking hover-glow parity.
5. Ship (commit → Cloudflare deploy → md5 parity → push). Run FULL suite first
   (hover CSS can touch shared selectors → blast radius).

**Inventory done (2026-06-06):** the CANONICAL golden item-click hover already
exists as `.fi-clickable:hover` (bible.html L455) and `.zd-item-click:hover`
(L514) — both `transform:translateY(-1px)` + gold border + `box-shadow:0 2px
8-9px rgba(0,0,0,.3-.35)` + `↗` after-content. **Laggards to unify to it
(additive — keep existing transitions tests assert):**
- `.item-tile:hover` (L180) — only `background`+`border-color:--gold`, no glow/transform (L800 adds transform on focus/hover only).
- `.gbc-grail-item:hover` (L999) — gold-bright border + transform, **missing box-shadow glow**.
- `.source-chip:hover` (L791) — uses `--star` accent + transform, no glow (intentional? it's a nav chip not an item — VERIFY before changing; bug041 test clicks source-chip).
- `.boss-chip:hover` (L265) — `--gold` border, **no transform**.
- `.gic-source-cell:hover` (L1200) — already has glow; fine.
- `.top-drop-row:hover` (L322, later def wins) — already golden gradient+transform; fine.
- `.guaranteed-card`/`.su-card`/`.colossal-tile`/`.statue-card` — card-level hovers, separate treatment; decide if in scope.
**Caution:** `.source-chip` is asserted by `bug040_050_interactions` (bug041 click); `.item-tile` + `.zd-item-click` asserted across many specs — change CSS only, not the click contract.

### ✅ #51 (audit) + #52 (guards) + #58 (super-uniques) — SHIPPED as v91
- `AUDIT_id_card_parity.md` = the gap matrix. Key finding: items/runes/materials are
  LOOT (correctly `.gic-card`); the drop-SOURCE entities are the gbc-parity targets.
- v91 brought **super-uniques** into the golden `.gbc-card` shell (were lean `.zd-*`),
  the last entity gap besides events. v83 "gbc-format parity" guard locks it.
- **Remaining drop-source gap = event monsters** (DClone / Uber Tristram triune /
  Pandemonium) + cows/travincal/pit — audit them next (do they have detail cards or
  only rows?). That's the next batch (v92) toward the master goal.

### (original) #51 — Audit every ID card for Baal-format parity (~30-50 entities)
Catalog every drop-source ID card (bosses, super-uniques, TZ zones, Heralds,
events, ancients, cows/pit/travincal, etc.) and score each against the Baal-card
template (golden `.gbc-card` shell, portrait/emblem via `artOr`, enriched
sections, drop grid, `.zd-note` gap-flags). Produce a gap matrix → enrich the
laggards. This is the big remaining chunk of the master goal.

### #52 — Extend v83 sync audit: artOr-title + card-format-parity invariants
Lock the #51 parity in tests: every ID card resolves an `artOr` title/emblem and
matches the structural Baal-format contract. Pairs with #51.

### #48 — Extend v83 sync audit to cover the new symmetry invariants + ship
Partially done (section-header parity landed in v89). Sweep for any remaining
symmetry gaps (collapse idioms, title formats) and add guards. Roll into #52.

## Standing loops (re-arm after restart if desired)
- **Routine I scheduled-CI check** — `/loop 30m` (baseline scheduled run was
  databaseId 26679413862 / headSha df9d216; the v88 push hadn't triggered a new
  cron tick at pause time — re-baseline to the newest scheduled run on resume).
- **Obsidian BUILD_LOG maintenance** + **D2R self-heal health ratchet**.

## Ship mechanics cheat-sheet (so resume is friction-free)
- Deploy: `cp bible.html /tmp/d2r_dist/d2r/index.html && cd /tmp/d2r_dist && set -a && . ~/.config/cf-d2r/env && set +a && npx wrangler@latest pages deploy . --project-name=d2r-bible --branch=main`
- md5 parity: `cd /Users/konyo/d2r_bible_tests; md5 -q bible.html` vs `curl -s -A 'Mozilla/5.0' https://bull-4-u.com/d2r/ | md5 -q`
- Before any commit: `git status` for dead-fork strays (`H_sweep.js`/`K_perf.js`/`J_screens.js`/`L_integrity.js`/`bible_routes.html`) → `git checkout --` them, never commit.
- Full suite ~16-18min, 423 tests. Background-run: redirect to file, poll for `EXIT=`.

---

## v89 ship record
- commit `c33d4f9`, deployed to Cloudflare, md5 parity `f4723323` (local==live),
  pushed (pre-push smoke 36/36 green). Full suite 423 passed / 1 skipped. #47 + #48 done.
