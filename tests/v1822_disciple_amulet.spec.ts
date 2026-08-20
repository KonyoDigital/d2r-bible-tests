import { test, expect } from './_net_stub';
import * as path from 'path';

// v1822 — TELLING OF BEADS IS AN AMULET, and the board contradicted itself about it.
//
// Konyo hit this seam twice. First as a mismatch he could see but not name — "telling of beads and
// the disciple there is a mismatch or unsynced" — and then plainly: "its not a spired helm its an
// amulet". Both times he was right, and the evidence was already inside the file: the HD art map
// has served "Telling of Beads":"art/hd_amulet.png" all along, while the piece label said
// "(spired helm)" under a comment claiming the pieces had been VERIFIED against setitems.json. One
// surface drew an amulet, another named a helm, and the claim of verification made the wrong one
// look settled.
//
// The slot is not decoration: it picks the vault locker and the art the card draws.
//
// THE PART THAT NEEDED CARE. d2r_setPieces stores the FULL "Name (slot)" string and _setHave is
// consulted with an exact have.has(name), so correcting a slot silently UN-FINDS the piece he
// ticked under the old label — he would watch a set he completed lose a piece with nothing to point
// at. Handled on READ: a stored entry also admits the roster's current label for the same base
// name. His storage is never rewritten, and the next slot correction is covered without a migration.

const FILE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test('v1822 — the Disciple lists Telling of Beads as an amulet', async ({ page }) => {
  await page.goto(FILE);
  await page.waitForFunction(() => typeof (window as any).__allSets === 'function', null, { timeout: 20000 });
  const pieces = await page.evaluate(() => {
    const s = (window as any).__allSets().find((x: any) => /Disciple/.test(x.name));
    return s ? s.pieces : [];
  });
  expect(pieces).toContain('Telling of Beads (amulet)');
  expect(pieces.join(' | ')).not.toContain('spired helm');
});

test('v1822 — the art map and the roster finally agree on the slot', async ({ page }) => {
  // the contradiction IS the finding: these two disagreed for as long as the label was wrong, and
  // nothing compared them. If a future edit moves one, this fails rather than letting them drift.
  await page.goto(FILE);
  await page.waitForFunction(() => typeof (window as any).__allSets === 'function', null, { timeout: 20000 });
  const art = await page.evaluate(() => {
    const w = window as any;
    for (const k of Object.keys(w)) {
      const v = w[k];
      if (v && typeof v === 'object' && typeof v['Telling of Beads'] === 'string'
          && v['Telling of Beads'].indexOf('art/') === 0) return v['Telling of Beads'];
    }
    return '';
  });
  if (art) expect(art, 'the art served for this piece').toContain('amulet');
});

test('v1822 — a tick made under the OLD label is not un-found', async ({ page, context }) => {
  await context.addInitScript(() => {
    try { localStorage.setItem('d2r_ownerClaim', '*'); } catch (e) {}
    try { Object.defineProperty(navigator, 'webdriver', { get: () => true }); } catch (e) {}
    try { localStorage.setItem('d2r_setPieces', JSON.stringify(['Telling of Beads (spired helm)'])); } catch (e) {}
  });
  await page.goto(FILE);
  await page.waitForFunction(() => typeof (window as any)._setHave === 'function', null, { timeout: 20000 });

  const seen = await page.evaluate(() => {
    const have = (window as any)._setHave();
    return { neu: have.has('Telling of Beads (amulet)'), old: have.has('Telling of Beads (spired helm)') };
  });
  expect(seen.neu, 'his old tick must still satisfy the corrected label').toBe(true);
  expect(seen.old, 'and the string he actually stored must keep working too').toBe(true);

  // and his storage is left exactly as he wrote it — the remap is read-side only
  const stored = await page.evaluate(() => localStorage.getItem('d2r_setPieces'));
  expect(stored).toBe(JSON.stringify(['Telling of Beads (spired helm)']));
});
