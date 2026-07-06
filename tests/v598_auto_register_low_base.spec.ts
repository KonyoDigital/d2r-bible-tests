import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v598 — FULLY-AUTOMATED low-base registration (Konyo: "this needs to be automated completely.. no
// clicks"). An intake read the AI grades "<Base> (Nos low base)" used to park in the Throw-Out Review
// waiting for a human; now a runeword-capable one registers with FULL criteria — exact sockets, quality
// prefix in the label, tier/art/RW description, mule assignment — exactly like a normal read. Only
// genuine junk (can't host a word / verdict says vendor) still goes to review.

test('low-base read auto-registers with full criteria; junk still routes to review; 2nd read = ×2', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify([]));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ko: 2, Mal: 1 }));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1500);
  await page.evaluate(() => {
    const w: any = window;
    // Sanctuary (Ko+Ko+Mal, 3os shields) is the ONLY unmade word → a 3os shield is a keeper, a 3os axe is not
    const made: any = {}; Object.keys(w.RUNEWORD_TIP || {}).forEach((n) => { if (n !== 'Sanctuary') made[n] = 'x'; });
    localStorage.setItem('d2r_rwMade', JSON.stringify(made));
    localStorage.setItem('d2r_rwProfile', 'fresh');
  });
  await page.reload(); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const first = w._autoRegisterLowBase('Gothic Shield (3os low base)');
    const entry = (w.EXTRA_ITEMS || {})['Gothic Shield (3os)'] || null;
    const second = w._autoRegisterLowBase('Gothic Shield (3os low base)');
    const copies = JSON.parse(localStorage.getItem('d2r_copies') || '{}');
    const sup = w._autoRegisterLowBase('Superior Gothic Shield (3os low base)');
    const junkAxe = w._autoRegisterLowBase('Small Crescent (3os low base)');       // no unmade 3os axe word → review
    const notRw = w._autoRegisterLowBase('Circlet (3os low base)');                // circlets can't host words → review
    const ownedNow = JSON.parse(localStorage.getItem('d2r_owned') || '[]');
    const task = [...(w.forgeScan().now || [])].find((t: any) => t.rw === 'Sanctuary');
    return { first, second, sup, junkAxe, notRw, ownedNow,
             entrySockets: entry && entry.sockets, entryCat: entry && entry.cat,
             copiesGothic: copies['Gothic Shield (3os)'] || 0,
             sanctuaryBase: task && task.base && task.base.name };
  });
  expect(r.first).toEqual({ label: 'Gothic Shield (3os)', mode: 'new' });
  expect(r.entrySockets).toBe(3);                       // full registration: exact socket count…
  expect(r.entryCat).toBe('Socketed bases');            // …in the real Socketed-bases category
  expect(r.ownedNow).toContain('Gothic Shield (3os)');
  expect(r.second).toEqual({ label: 'Gothic Shield (3os)', mode: 'copy' });
  expect(r.copiesGothic).toBe(2);                       // a 2nd distinct read = a 2nd physical copy
  expect(r.sup && r.sup.label).toBe('Superior Gothic Shield (3os)');   // quality prefix rides into the label
  expect(r.junkAxe).toBeNull();                         // nothing left for a 3os axe → stays a human call
  expect(r.notRw).toBeNull();                           // can't host a runeword → stays a human call
  expect(r.sanctuaryBase).toBe('Gothic Shield (3os)');  // the Forge picks the auto-registered shield up as make-now
});
