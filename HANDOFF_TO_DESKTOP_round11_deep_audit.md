# Handoff to Claude Desktop — Round 11 deep audit (beyond audit floor)

Konyo asked CC to do a deep audit ("really do a deep audit super deep. every cell check") after Desktop's Round 10 wrap claimed audit floor. 4 new bugs found that Round 10 missed and that Playwright cannot see. One is a single-character fix that restores about a third of the UX.

All findings are in `/Users/konyo/d2r_bible_tests/bible_routes.html`. Pre-flight: BOSSES=11, ITEMS=312, dropTable entries=3243, 0 TC/qlvl/tier inconsistencies (verified via audit2.js). Bugs A/B/C/D from Round 10 are present in working tree as patched (uncommitted) — these 4 are additive.

---

## BUG G · CATASTROPHIC · Missing `}` swallows ~85 lines of top-level init code

**Location:** `bible_routes.html:4909–4998`

**Severity: P0.** Roughly a third of the keyboard/search/jump UX does not work on page load. It only starts working after the user happens to click a Statue, and then degrades on every subsequent statue click.

**Diagnosis:** `function toggleStatue(name)` opens its body at line 4909. The intended closing `}` after `renderStatueTracker();` at line 4913 is missing. The actual closing `}` doesn't appear until line 4998. Verified with a string/template/comment-aware brace tokenizer (not naive line-grep):

```
L4909  depth 0 -> 1  | function toggleStatue(name) {
L4913  depth 1 -> 1  |   renderStatueTracker();
L4914  depth 1 -> 1  | renderTzZones();           ← still inside toggleStatue
L4915  depth 1 -> 1  | renderSetTracker();        ← still inside
L4918  depth 1 -> 2  | document.addEventListener("keydown", (e) => {
...
L4973  depth 2 -> 1  | });                        ← keydown listener closes
L4982  depth 2 -> 1  | }                          ← first-visit if-block closes
L4988  depth 1 -> 2  | window.jumpToBossItem = (itemName) => {
L4997  depth 2 -> 1  | };                         ← jumpToBossItem arrow closes
L4998  depth 1 -> 0  | }                          ← toggleStatue FINALLY closes
L4999  depth 0 -> 0  | window.toggleStatue = toggleStatue;
```

Everything between lines 4914 and 4997 is in toggleStatue's body, not at top-level scope.

**Per-line consequences:**

| line | intended role | actual behavior |
|---|---|---|
| 4914 | top-level boot call | runs only when a statue is toggled |
| 4915 | top-level boot call | runs only when a statue is toggled |
| 4918 | register one keydown listener (Esc / arrows / `b` / `/` / `?` / `1`–`7`) | listener not registered until first statue toggle, then **re-registered on every subsequent toggle** — N toggles = N firings per keypress |
| 4976 | one-shot first-visit shortcut hint | only fires on first statue toggle |
| 4985 | `let lastSearch = "";` module-scoped | function-scoped local; no persistence between calls |
| 4986 | wire `$("item-search")` input handler | not attached until first statue toggle |
| 4988 | export `window.jumpToBossItem` | undefined on window until first statue toggle |

**Smoking gun — comment at line 5107:**

```js
// v42 dedup: removed duplicate `let lastSearch` + `addEventListener('input', ...)` + window.jumpToBossItem
// (identical block also lives at ~line 4981). Duplicate was attaching the input listener twice,
// firing lastSearch updater on every keystroke twice. Single instance lives above.
```

A previous v42 patch saw the same block twice, decided one was a duplicate, and removed the top-level copy. But the "still living" copy is the one inside toggleStatue's runaway body. The "dedup" stripped the only working copy.

**User-visible effects (before any statue toggle):**

1. Esc does not close help modal / clear active boss / clear active item *(NOTE: a separate Esc handler at line 3635 survives — it ONLY closes the boss-detail overlay if visible, not the help modal or active item)*
2. Arrow nav / Enter / `b`-key in item-grid: dead
3. `/` does not focus calculator search
4. `?` does not open help modal
5. Number keys `1`–`7` do not switch tabs
6. First-visit shortcut hint banner never appears
7. **`window.jumpToBossItem` is `undefined`** — every onclick attribute that calls it throws `ReferenceError` and the surrounding setTimeout chain silently dies. Call sites that break:
   - line 4331 — best-source-box "click to jump"
   - line 4665 — aid-card "jump to fastest →" link
   - line 4706 — aid-card "↗ jump to boss" button (calc context)
   - line 4716 — calc-context source chip
   - line 4809 — item-detail-card source chip

**Why Playwright didn't catch:** test fixtures probably click a statue early or test keyboard shortcuts via direct `document.dispatchEvent` after enough setup that incidentally toggles a statue. A fresh manual user landing on calc and pressing `/` sees nothing.

**Fix (single character):** add a `}` after line 4913 `  renderStatueTracker();` so toggleStatue closes correctly and lines 4914–4997 return to top-level scope where they belong.

```diff
 function toggleStatue(name) {
   if (statues.has(name)) statues.delete(name);
   else statues.add(name);
   persist();
   renderStatueTracker();
+}
 renderTzZones();
 renderSetTracker();
```

**Verification after patch:**
```js
// pre-patch (loaded fresh, no statue clicked)
typeof window.jumpToBossItem  // "undefined"  ← BUG
// post-patch (loaded fresh, no statue clicked)
typeof window.jumpToBossItem  // "function"
```

---

## BUG E · HIGH · Stale closure reads `aidCardOrigin.bossId` after wipe

**Location:** `bible_routes.html:4000–4009`

```js
window.goBackFromAid = function() {
  if (!aidCardOrigin) return;
  if (aidCardOrigin.tab === 'bosses' && aidCardOrigin.bossId) {
    switchTab('bosses');
    setTimeout(() => setActiveBoss(aidCardOrigin.bossId), 60);  // ← reads at +60ms
  } else if (aidCardOrigin.tab) {
    switchTab(aidCardOrigin.tab);
  }
  aidCardOrigin = null;  // ← runs synchronously BEFORE the timeout fires
};
```

The setTimeout closure captures the module-scoped `aidCardOrigin` reference (not its `.bossId` value). The next statement, `aidCardOrigin = null`, runs synchronously. 60 ms later the timer fires and evaluates `null.bossId` → `TypeError: Cannot read properties of null (reading 'bossId')`. Exception is swallowed by the macrotask queue; `setActiveBoss` never runs.

**User-visible effect:** the "← back to boss" button on the calc-context aid card lands on the bosses tab with no boss expanded (the chip bar is rendered but no .gbc panel below). Looks like a partial navigation.

**Fix:** capture into a local before nulling, or null inside the timer.

```diff
 window.goBackFromAid = function() {
   if (!aidCardOrigin) return;
+  const origin = aidCardOrigin;
+  aidCardOrigin = null;
-  if (aidCardOrigin.tab === 'bosses' && aidCardOrigin.bossId) {
+  if (origin.tab === 'bosses' && origin.bossId) {
     switchTab('bosses');
-    setTimeout(() => setActiveBoss(aidCardOrigin.bossId), 60);
+    setTimeout(() => setActiveBoss(origin.bossId), 60);
-  } else if (aidCardOrigin.tab) {
-    switchTab(aidCardOrigin.tab);
+  } else if (origin.tab) {
+    switchTab(origin.tab);
   }
-  aidCardOrigin = null;
 };
```

**Why Playwright didn't catch:** harness likely asserts the bosses tab becomes active after click, not that the specific boss card auto-expands. A `await page.locator('#boss-detail-panel .gbc-grail-item').first()` probe would have flagged it.

---

## BUG F · MEDIUM · "Tonight's Mission" feature is dead (3 stacked issues)

**Location:**
- `bible_routes.html:1557` — `<div class="tonight-mission" id="tonight-mission" style="display:none">`
- `bible_routes.html:2801` — `const el = $("tonights-mission");`

**Stacked issues:**

1. **ID mismatch.** HTML id is `tonight-mission` (singular). JS asks for `tonights-mission` (plural, with `s`). `$()` returns `null` and the function bails on line 2802.
2. **`style="display:none"`** on the outer div, never un-hidden by any code path.
3. **Internal target mismatch.** The function writes to `el.innerHTML` (the outer wrapper), but the markup expects the inner `<div id="mission-grid">` to receive the per-pick HTML.

`renderTonightsMission()` is called 4 times — line 4198 (toggleStar), 4216 (toggleOwned), 5012 (mf oninput), 5028 (boot) — all silent no-ops.

**Decision needed:** revive or remove. CC's lean: **remove**. `renderHero()` and `renderWishlistHuntPath()` already cover the "fastest path to your wishlist" use case that this section was meant to be. Deleting 50 lines of function + 4 call sites + the dead `<div>` is cleaner than fixing three stacked bugs to revive a redundant feature.

---

## BUG H · LOW-MED · `setActiveBoss` toggle conflicts with non-toggle entry points

**Location:** `bible_routes.html:2848–2850`

```js
window.setActiveBoss = function(bossId, focusDiff) {
  if (activeBossId === bossId) { clearActiveBoss(); return; }  // toggle
  ...
};
```

Toggle is correct for the boss-chip use case (Konyo's explicit request earlier in this session). But the same function is reached by 5 entry points where the user intent is "open this boss" not "toggle":

- TZ zone card click — `bible_routes.html:1685+, 4829` → `openBossDetail(bossId)`
- gic-source-cell click — `bible_routes.html:3282, 3307`
- Cmd/Ctrl+click on `.source-chip` — `bible_routes.html:3665`
- `#tab/bossId` URL hash routing — `bible_routes.html:5274`
- hero-pick onclick — `bible_routes.html:2836` (already-open boss → click another hero-pick that maps to the same boss = collapses)

In all of these, if the boss is already active, the call **closes** it. Looks like a misclick from the user's perspective.

**Fix sketch:**

```diff
-window.setActiveBoss = function(bossId, focusDiff) {
-  if (activeBossId === bossId) { clearActiveBoss(); return; }
+window.setActiveBoss = function(bossId, focusDiff, opts) {
+  const intent = opts?.intent || 'toggle';
+  if (activeBossId === bossId) {
+    if (intent === 'toggle') { clearActiveBoss(); return; }
+    // intent === 'open' — just re-scroll, no-op state-wise
+    setTimeout(() => $("boss-detail-panel")?.scrollIntoView({behavior:'smooth',block:'start'}), 50);
+    return;
+  }
   activeBossId = bossId;
   ...
```

Then update the 5 "open" entry points to pass `{intent:'open'}`. Boss-chip click stays as `setActiveBoss(id)` with default toggle.

**Why Playwright didn't catch:** test flow doesn't typically re-enter the same boss via two different entry points in sequence.

---

## Verification surfaces audited clean (no findings, for the record)

So Desktop knows where I did look:

- **Data integrity** — 11 bosses, 312 unique items, 3243 dropTable entries, 0 cross-boss TC/qlvl/tier inconsistencies (via audit2.js, replicating the in-page ITEMS population logic).
- **Set/Map mutations** — all 8 mutation sites correctly invoke `persist()`: toggleStar:4196, toggleOwned:4207, toggleSetPiece:4866, toggleStatue:4912, fallback at :3391.
- **NaN safety** — `$("mf").oninput` / `$("players").oninput` at lines 5012-5013 use unguarded `parseInt()` BUT both inputs are `type="range"` (lines 1485, 1490) so values are always numeric strings — no NaN path. The `mfNumberInput` text input at 2920/2927 correctly uses `|| 0` fallback.
- **Decorator chains** — v39 (hash) at 5281 + v40 (field manual) at 5577 on `openBossDetail`, v37 wishlist export at 5210 on `renderWishlistHuntPath` — all use `apply(this, arguments)` and wrap in `try/catch` correctly.
- **XSS escaping** — every `${escName}` interpolation in onclick attributes feeds a `.replace(/'/g, "\\'")` first.
- **switchTab no-op behavior** — the v42 "re-tap active tab = scroll to top" guard at 5246 is safe: only goBackFromAid relies on switchTab firing renders, and renderDetail/renderBossDetailCard run independently after.
- **Routine letter chip handler** — `:5188` correctly uses `e.target.dataset.r` → `ROUTINE_INFO[r]` with defensive `if (info)`.
- **Round 10 bugs A/B/C/D** — all four are present in working tree as patched (uncommitted). No reversion seen.

---

## Suggested ship order

1. **BUG G first** — single-character fix, restores keyboard shortcuts + search input + jumpToBossItem + first-visit hint in one keystroke. Highest blast radius, lowest patch risk.
2. **BUG E** — 4-line cleanup, fixes silent back-button failure.
3. **BUG F** — decide remove vs revive, then 1 commit.
4. **BUG H** — opts.intent disambiguation, slightly more touch (5 call sites).

After Desktop ships these, CC will kick a fresh Playwright sweep + re-audit for any new regressions introduced.

— CC, Round 11 deep audit
