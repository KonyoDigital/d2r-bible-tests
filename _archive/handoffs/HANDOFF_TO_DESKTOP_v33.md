# Handoff to Claude Desktop — v32 → v33

Route audit on v32: **22/24 GREEN**. Two slider tests fail. Root cause is mechanical and unambiguous.

## The bug

The entire v32 Wishlist Hunt Path JavaScript was pasted into the **wrong block**. The `<style>` tag closes at line 1015, the `<script>` tag opens at line 1614. All of the new code at lines 720-857 — including:

- `function renderWishlistHuntPath()` (line 720)
- `window.renderWishlistHuntPath = renderWishlistHuntPath` (line 857)
- All inline `onclick` callbacks inside the chip templates

...sits **inside the `<style>` block**. The browser parses it as CSS text and silently throws it away. It is never executable.

## Evidence

```
pageerror: renderWishlistHuntPath is not defined
  at $.oninput (bible_routes.html:4062:353)  ← MF slider
  at $.oninput (bible_routes.html:4063:269)  ← Players slider
```

Surrounding context at line 720:
```
715:  .kbd-help-close:hover{background:var(--gold-dim);color:var(--text)}
716:
717:
718:
719:/* === v32: Wishlist Hunt Path — your starred items, ranked by best source === */
720:function renderWishlistHuntPath() {
```

Line 715 is CSS. Line 720 is meant to be JS. They're in the same block. Browsers do not eval JS inside `<style>`.

The init-time guards (`if (typeof renderWishlistHuntPath === "function")` at lines 2705 and 4089) silently no-op because `typeof undefined === "undefined"`, not `"function"`. That's why the page LOOKS like it loads — the wishlist card div renders empty and the user just sees an empty card until they touch a slider, then the audit catches it.

## Fix

Cut lines 720-857 (the entire v32 JS payload) out of the `<style>` block. Paste them **inside the `<script>` block** (anywhere between line 1614 and the existing call sites at 2705 / 4062 / 4063 / 4089). Function declarations hoist, so position within the script doesn't matter.

After paste, verify with this 1-line console probe:
```js
typeof window.renderWishlistHuntPath  // must be "function"
```

If it returns `"function"`, you're done. If it returns `"undefined"`, the function is still in the wrong block.

## What's NOT broken

- `openBossDetail` works perfectly (your earlier hang concern was unfounded — `_origRenderHero` shim is not the issue here)
- 22/24 of the route audit passes
- Boss-cards, calc tiles, TZ routing, golden item card — all clean
- This isn't a routing regression. It's a copy-paste-into-wrong-block bug.

## Verifier (after v33 ships)

```bash
cp /Users/konyo/Downloads/konyo_d2r_bible_v33.html /Users/konyo/d2r_bible_tests/bible_routes.html
cd /Users/konyo/d2r_bible_tests
npx playwright test tests/route_audit_v23r.spec.ts --reporter=line
```

Target: 24/24 GREEN.

## Side note on next planned work

You mentioned: *"unify the calc tab's renderDetail() to use renderItemDetailCard itself (single source of truth for item visualization)."* That's the right move, but be careful about a recursion risk:

- If `renderDetail` calls `renderItemDetailCard` and `renderItemDetailCard` (when mounted in calc tab) triggers `setActiveItem`, and `setActiveItem` calls `renderDetail`, you have infinite recursion
- Mitigation: pass an explicit `{source: 'calc'}` or `{noPropagate: true}` flag through the call so the unified renderer knows not to fire the calc-tab side effects
- Or hoist all shared state mutation OUT of the renderer and into a single thin wrapper above both call sites
