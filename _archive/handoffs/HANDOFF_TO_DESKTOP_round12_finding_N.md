# Handoff to Claude Desktop — Round 12 · Finding N

Single real bug surfaced from CC's parallel deep pass. Desktop spotted the symptom ("5 starred when only 1 real") and logged it as cosmetic. CC re-verified — the math actually drifts visibly. Worth a one-shot boot-time fix before declaring audit floor.

---

## Finding N · Wishlist count drift on stale entries

**Severity: LOW-MEDIUM.** Visible count inconsistency, no crash, no data loss. Pure self-inflicted by users whose wishlist/owned sets accumulated names that the bible's data layer later renamed or removed. Routine L drift detection should already be flagging these on the data-integrity side; this is the user-facing side of the same drift.

**Locations:**
- `bible_routes.html:2771` — grail-progress strip count
- `bible_routes.html:2983` — wishlist hunt-path render entry point
- `bible_routes.html:3059` — wishlist hunt-path summary line

### Reproduction (mental)

1. User stars `"Harlequin Crest"`, `"Old Item Name X"`, `"Old Item Name Y"`, `"Old Item Name Z"`, `"Old Item Name W"` across earlier sessions.
2. Bible data is updated — items X/Y/Z/W are renamed or removed from `ITEM_REGISTRY`.
3. `wishlist` Set still holds all 5 names (only persist+load, no scrub).
4. Render flow:
   - `const starred = Array.from(wishlist || []);` → 5 entries
   - `starred.forEach(name => { … push to remaining[] only if ITEMS.find(i => i.n === name) … });` → 1 entry pushed
   - `ownedFromWishlist` counts only items that exist + are in owned set → 0
5. Summary at 3059: ``${starred.length} starred · ${ownedFromWishlist} found · ${remaining.length} to chase``
   → `5 starred · 0 found · 1 to chase` — sum doesn't reconcile.
6. Grail-progress at 2771: ``⭐ ${wishlist.size} starred for priority.``
   → `⭐ 5 starred for priority.` while only 1 hunt-path row is actually visible.

### Root cause

Wishlist + owned Sets are loaded from LS verbatim, never reconciled against the live `ITEM_REGISTRY`. Every readout call site (count, render, summary) reaches into the raw Sets. Some paths are guarded (the hunt-path row loop is — that's why only valid items render), but the count readouts are not.

### Fix — one-shot boot-time sanitization (preferred)

Add this **immediately after** the existing wishlist/owned LS load (search for `let wishlist =` around line 2657-ish):

```js
// Sanitize stale entries: items renamed/removed in data updates should not
// inflate wishlist/owned counts. Routine L flags the data-side drift;
// this fixes the user-facing side. One-shot, then persist if anything was scrubbed.
(function _scrubStaleWishlistOwned() {
  const beforeW = wishlist.size, beforeO = owned.size;
  wishlist = new Set([...wishlist].filter(n => ITEM_REGISTRY[n]));
  owned    = new Set([...owned].filter(n => ITEM_REGISTRY[n]));
  if (wishlist.size !== beforeW || owned.size !== beforeO) {
    console.info(`[bible boot] scrubbed stale wishlist (${beforeW}→${wishlist.size}) + owned (${beforeO}→${owned.size})`);
    persist();
  }
})();
```

**Placement constraint:** must run AFTER `ITEM_REGISTRY` is populated (the `BOSSES.forEach → ITEMS.push → ITEM_REGISTRY[d.n] = ...` block) AND AFTER `wishlist` / `owned` are loaded from LS. If those happen in the wrong order, ITEM_REGISTRY is empty and the scrub would nuke the entire wishlist. **Verify boot order before pasting.**

### Why option 1 over filter-at-render-time

- Single boot block vs N render-site changes (count appears in at least 3 places, all need the same filter else drift returns)
- Self-heals — next persist() writes the scrubbed sets back to LS, problem stays fixed across sessions
- Console.info logs scrub events → useful telemetry for Routine L cross-correlation

### Verification

Pre-patch:
1. In devtools console pre-load: `LS.setItem('d2r_wishlist', JSON.stringify(['Harlequin Crest', 'foo', 'bar', 'baz', 'quux']))`
2. Reload bible
3. Grail strip shows `⭐ 5 starred`, hunt-path summary shows `5 starred · 0 found · 1 to chase`, only 1 row renders. **BUG.**

Post-patch:
1. Same LS prime
2. Reload bible
3. Console emits `[bible boot] scrubbed stale wishlist (5→1) + owned (0→0)`
4. Grail strip shows `⭐ 1 starred`, hunt-path summary shows `1 starred · 0 found · 1 to chase`, 1 row renders. **MATH RECONCILES.**

### What this closes

Last real bug from CC's Round 11/12 parallel pass. After this lands:
- All 8 Round 11 bugs (A-H) ✓
- All 5 Round 11/12 cleanup findings (I=dead pinnedBoss, J=Esc cascade, K=Set safety, L=interval safety, M=ring buffer) — observed clean, no patch needed
- Finding N ← this one

= genuine audit floor.

— CC, Round 12
