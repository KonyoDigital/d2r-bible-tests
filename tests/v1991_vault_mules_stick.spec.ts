import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1991 — THE SWEEP FILED ITEMS INTO MULES AND THE NEXT PAGE LOAD THREW THEM AWAY.
 *
 * Konyo asked the vault manager to "auto-arrange in mules based on the items the readers read".
 * Two separate joins were missing and each looked fine from its own end.
 *
 * JOIN 1 — vaultAccumApply never wrote physical stock. v1987 tried `owned.add(nm)` behind a
 * `typeof owned !== 'undefined'` guard that can NEVER pass (owned is a `let` in tvVaultRegister's
 * closure), measured d2r_owned still [] and correctly reverted rather than shipped. The apply now
 * goes through window.tvVaultRegister — the same door his live TV pickup uses — which writes
 * `owned`, asks suggestMule, assigns the mule and persists, all inside the scope where those names
 * actually live.
 *
 * JOIN 2 — and this is the one that made the whole thing invisible. tvVaultRegister's UNIVERSE
 * GUARANTEE writes EXTRA_ITEMS[name] so the Vault Manager can draw the item, but EXTRA_ITEMS is a
 * `const` seeded at parse time and NEVER persisted. The load-time prune then filters `owned`
 * against _EXTRA_ITEM_SET, built from that static constant. MEASURED before the fix, one apply
 * then one reload:
 *     before   d2r_owned ["Shako","Cracked Sash","Laying of Hands (bramble mitts)"]
 *     AFTER    d2r_owned []                     <-- all gone, orphan d2r_muleAssign rows left
 * So a runtime registration survived exactly as long as the tab did.
 *
 * v342.16 and v465 each patched this same shape with a REGEX whitelist and their comments say why
 * in his words: "every reload silently DROPPED them, so a later intake batch looked like it did not
 * build on top of the earlier one". A regex cannot cover an arbitrary item name, so the entries are
 * persisted (d2r_tvExtraItems, forked per install like d2r_owned) and re-seeded before the prune.
 *
 * This test asserts the RELOAD, because every earlier version of this passed before one.
 */

const ROWS = [
  // name, lane, distinct sessions
  ['Harlequin Crest', 'equipment', 3],   // locked: 3 sessions on his character -> never muled
  ['Laying of Hands', 'stash', 1],       // a set piece, ticks via findSetPiece().piece
  ['Shako', 'stash', 2],                 // a BASE -> physical stock + a mule
] as const;

function payload() {
  return {
    ok: true, source: 'vault-retro', mode: 'merge-max', readOnlyUntilApply: true,
    generatedTs: 1787242458369, sessionsRead: ['s_A', 's_B', 's_C'],
    items: ROWS.map(([name, lane, n]) => ({
      name, lane, kind: 'item', count: null, conf: 0.95,
      witnesses: Array.from({ length: n as number }, (_, i) => ({
        session: 's_' + 'ABC'[i], frame: 'f' + i, lane, conf: 0.95,
      })),
      witnessCount: n, lastSeenTs: 1787242458369,
    })),
    suggestions: [],
  };
}

test('a swept item reaches a mule AND is still there after a reload', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1200);
  // v2144 (#151) — d2r_rwProfile='fresh' suppresses the automated world's 99-runeword seed, which
  // otherwise makes every white base correctly __throwout so suggestMule files nothing. Measured in
  // CI's world: rwMade 99 without it, 0 with it. Read bare by bible.html:17357, so it must be set
  // before the reload below.
  await page.evaluate(() => {
    localStorage.clear();
    localStorage.setItem('d2r_ownerClaim', '*');
    localStorage.setItem('d2r_rwProfile', 'fresh');
  });
  await page.goto(URL);
  await page.waitForTimeout(1600);

  const applied = await page.evaluate((p) => {
    const w: any = window;
    return w.vaultAccumApply(p);
  }, payload());

  // the grail ticked, and the SET piece went through as its canonical suffixed name
  expect(applied.grail).toContain('Harlequin Crest');
  expect(applied.grail.join('|')).toContain('Laying of Hands (');

  // his character is HIS decision — "if its there there a reason for it"
  expect(JSON.stringify(applied.laneLocked || [])).toContain('Harlequin Crest');

  const read = () => page.evaluate(() => ({
    owned: JSON.parse(localStorage.getItem('d2r_owned') || '[]'),
    assign: JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}'),
  }));

  const before = await read();
  expect(before.owned).toContain('Shako');
  expect(before.assign['Shako']).toBeTruthy();
  // never told to move off his character
  expect(Object.keys(before.assign)).not.toContain('Harlequin Crest');

  // ── THE ASSERTION EVERY EARLIER VERSION WOULD HAVE PASSED WITHOUT ──────────────────────
  await page.goto(URL);
  await page.waitForTimeout(1800);
  const after = await read();

  expect(after.owned, 'the reload wiped d2r_owned — the reference entry was not persisted')
    .toContain('Shako');
  expect(after.assign['Shako'], 'the mule row survived but the item did not — an orphan assignment')
    .toBe(before.assign['Shako']);

  // and the board can still DRAW it, which is what the prune was really testing
  const drawable = await page.evaluate(() => {
    const w: any = window;
    return !!(w.EXTRA_ITEMS && w.EXTRA_ITEMS['Shako']);
  });
  expect(drawable, 'EXTRA_ITEMS lost the runtime entry across the reload').toBe(true);
});
