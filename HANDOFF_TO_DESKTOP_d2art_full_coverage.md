# Handoff → Desktop: full diablo2.io art coverage (calc fix + bosses + Herald + TZ + boss-nav chips)

**From:** Claude Code (Mac) · **Date:** 2026-06-04 · **Asks:** (1) crystallization pass, (2) visual QA pass.

## What shipped (code-complete, BULLETPROOF-verified)

### Ship 1 — calc regression + boss art + Herald emblem (commit `2f63979`, already live)
- **Calc tile nesting regression FIXED.** `renderCalc` tile template (≈ bible.html:6614) had 3 opening
  divs (`item-tile` / `item-tile-row` / `item-tile-text`) but only 2 closing `</div>` — every tile
  swallowed the next (card-in-card cascade). Added the missing outer `</div>`. Regression guard:
  `v71_d2art.spec.ts` → "calc grid tiles are flat siblings — no recursive nesting".
- **Baal / Pindleskin / Uber-Diablo-Clone / The Pit** added to `D2IO_ART` with HEAD-verified slugs:
  - Baal → `baal-opt_graphic.png`
  - Pindleskin → `reanimatedhorde-opt_graphic.png` (Pindle's sprite IS the Reanimated Horde)
  - Uber Diablo (Diablo Clone) → `diablo_hell_graphic.png`
  - The Pit → `act1-underground_graphic.png`
- **Herald of Terror card** now collapsed-by-default (inside a `.sec-h/.sec-body[hidden]`) and its header
  emblem renders the verified `bonebreakcharm_graphic.png` (👹 emoji preserved as onerror fallback).

### Ship 2 — terror-zone area banners + boss-nav chip portraits (THIS commit)
- **TZ_ZONE_ART** global map (11 zones → `actN-<slug>` area slugs) + `tzZoneArtBanner(name)`. Every
  terror-zone card now wears a full-width `actN-..._graphic.png` scene banner across its top; The Pit
  lvl-85 cross-link card gets `act1-underground_graphic.png`. Lazy-loaded, onerror → `.d2art-failed`
  hides the banner (never a broken-image box). Spec: `v73_tz_art.spec.ts` (5 tests).
- **Boss-nav chips** (the sticky chip grid in the Bosses tab) now lead with `artOr(b.name, …, 'sm')` —
  mapped bosses show a 22px portrait thumbnail beside the name; unmapped (Andariel) keep the emoji.
  Guard: `v71_d2art.spec.ts` → "the boss-nav chips show portrait art … emoji for unmapped (Andariel)".

## Zero-fabrication discipline (every URL HEAD-probed: 200 + image content-type)
- **All 13 bosses now carry art EXCEPT Andariel** — she genuinely has no portrait `_graphic.png` on
  diablo2.io (probed andariel-opt / maiden-of-anguish / andariel_graphic / … all 404; her DB page
  carries no graphic). Honest call: keep the emoji. **Do not "find" one — there isn't one.**
- Two verified diablo2.io roots only: avatar gallery `/images/avatars/gallery/<folder>/<file>` (gifs +
  rune icons) and DB graphics `/styles/zulu/theme/images/items/<slug>_graphic.png`. No guessed slugs.

## Visual-pass asks (Desktop, please eyeball on the live site after deploy)
1. **TZ banners** — 132px scene strip on each terror-zone card; confirm crop/opacity reads well and the
   hover scale (1.03) isn't janky. Check a few zones actually resolve vs silently `.d2art-failed`.
2. **Boss-nav chips** — confirm the 22px portrait + name align cleanly in the sticky grid (flex gap 6px);
   Andariel's chip should look intentional with just the emoji, not "missing".
3. **Herald card** — collapsed by default; expand → emblem shows the Bone Break charm, not a bare 👹.
4. **Calc grid** — tiles are flat (no nesting); art thumbnail + name + TC line render on one row.

## Test / ship status
- Affected specs (v71/v72/v73/v56): **28/28 green** in isolation.
- Full suite running at handoff; dead-fork check (`git checkout -- K_perf.js H_sweep.js J_screens.js
  L_integrity.js`) + Cloudflare deploy + md5 parity (live == local) done as part of the ship.
- Integrity baseline / BOSSES data **untouched** — UI-only art layer, L-integrity probes unaffected.
