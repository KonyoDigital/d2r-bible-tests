import { test, expect } from './_net_stub';
import * as path from 'path';

// v1789 — MOST OF THE QUEUE WAS NEVER HIS DECISION.
//
// Konyo, looking at 49 pending rows: "these 49 items.. what exactly do they do they are like pending
// items that were chornicle read? and they want my approval? why? cant like an extra AI take care of
// it and cross reference it with specific and focused hunts for it to cross reference it here and
// automatically grail it.. and if it still cant then leave it for me to tick off."
//
// He was right. The server-side ledger was read by hand the day this shipped: of 36 held names, SIX
// were unresolved uniques. Six were OCR slips of items ALREADY in his grail ("Battlecage" for
// Rattlecage, "Naglring" for Nagelring). Twenty-four were reader debris — and the debris has a
// boring, specific cause that makes the rule obvious: THE CHRONICLE PRINTS THE BASE ITEM NAME FOR A
// ROW HE HAS NOT FOUND. "Templar Coat", "Bone Visage", "Wrist Sword" are not near-misses; they are
// the game stating the OPPOSITE of a find, written down faithfully by the reader.
//
// WHAT THIS SPEC PINS is the boundary, not the cleanup: a row that MIGHT be a real find is never
// dismissed. A wrong dismissal deletes a find silently, which is strictly worse than a queue that is
// too long — so "Toothrow", a roster unique he does not have, must survive every pass.
//
// The found-state here is written with the app's OWN writer (kaiChronicleAccept). An earlier version
// of this check seeded `d2r_foundLog` directly and read false back from `_gFound`: the real key is
// install-scoped ("I·<installId>·d2r_foundLog"), so the fixture was writing to a key nothing reads.
// Hardcoding that prefix in a test would put a second copy of the fork rule in the tree; asking the
// app to record the find keeps one.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

async function seedInbox(page: any, names: string[]) {
  await page.addInitScript((ns: string[]) => {
    localStorage.setItem('d2r_chronicleInbox', JSON.stringify(ns.map((n) => ({ name: n }))));
  }, names);
}

test('a base item name is retired — the Chronicle prints it for a row he has NOT found', async ({ page }) => {
  await seedInbox(page, ['Templar Coat', 'Bone Visage', 'Toothrow']);
  await page.goto(URL);
  const res = await page.evaluate(() => (window as any).kaiChronicleResolvePending({ dryRun: true }));
  const dismissed = res.dismissed.map((d: any) => d.name).sort();
  expect(dismissed).toEqual(['Bone Visage', 'Templar Coat']);
  expect(res.kept).toContain('Toothrow');
});

test('a truncated read is retired — the reader was quoting its own damage', async ({ page }) => {
  await seedInbox(page, ['Firel...', 'Heavas (partially obscured)', 'Toothrow']);
  await page.goto(URL);
  const res = await page.evaluate(() => (window as any).kaiChronicleResolvePending({ dryRun: true }));
  expect(res.dismissed.map((d: any) => d.name).sort()).toEqual(['Firel...', 'Heavas (partially obscured)']);
  expect(res.kept).toEqual(['Toothrow']);
});

test('a name he already has is retired — there is nothing to rule on', async ({ page }) => {
  await seedInbox(page, ['Rattlecage', 'Toothrow']);
  await page.goto(URL);
  // record the find through the app's own writer, then re-queue the same name
  await page.evaluate(() => {
    (window as any).kaiChronicleAccept('Rattlecage');
    localStorage.setItem('d2r_chronicleInbox', JSON.stringify([{ name: 'Rattlecage' }, { name: 'Toothrow' }]));
  });
  expect(await page.evaluate(() => !!(window as any)._gFound('Rattlecage'))).toBe(true);
  const res = await page.evaluate(() => (window as any).kaiChronicleResolvePending({ dryRun: true }));
  expect(res.dismissed.map((d: any) => d.name)).toEqual(['Rattlecage']);
  expect(res.dismissed[0].why).toContain('already in your grail');
  expect(res.kept).toEqual(['Toothrow']);
});

test('a roster unique he does NOT have is never dismissed', async ({ page }) => {
  // the whole safety boundary in one assertion: these are exactly the six his gate was holding
  const real = ['Latent Cold Rupture', 'Latent Crack of the Heavens', 'Latent Rotting Fissure',
                "Thundergod's Vigor", 'Toothrow', 'Witherstring'];
  await seedInbox(page, real);
  await page.goto(URL);
  const res = await page.evaluate(() => (window as any).kaiChronicleResolvePending({ dryRun: true }));
  expect(res.dismissed).toEqual([]);
  expect(res.kept.sort()).toEqual(real.slice().sort());
});

test('the panel shows a receipt for the rows it cleared on its own', async ({ page }) => {
  await seedInbox(page, ['Templar Coat', 'Toothrow']);
  await page.goto(URL);
  await page.evaluate(() => (window as any).renderInboxFab());
  await page.evaluate(() => (window as any).inboxPopTog());
  const pop = page.locator('#inbox-pop');
  await expect(pop).toHaveClass(/open/);
  // a queue that silently got smaller is indistinguishable from a lost one
  await expect(pop.locator('.ibp-auto')).toContainText('cleared automatically');
  await expect(pop.locator('.ibp-auto')).toContainText('base item name');
});

test('every pending row actually SHOWS its name and both buttons', async ({ page }) => {
  // v1789 — a GEOMETRY assertion, because no text assertion could have caught this. `.ibp-why` is
  // flex:0 0 100%, and in a row without flex-wrap it took the whole line and squeezed the item name
  // and both buttons to ZERO width. textContent was perfect the entire time: the name was in the
  // DOM, correctly escaped, with working handlers — and the panel rendered three rows reading
  // "unclear read" with nothing on them to act on. The one thing he needs from this panel is the
  // name. Only a screenshot showed it.
  await seedInbox(page, ['Toothrow', 'Witherstring', "Thundergod's Vigor"]);
  await page.goto(URL);
  await page.evaluate(() => (window as any).inboxPopTog());
  const rows = page.locator('#inbox-pop .ibp-row');
  await expect(rows).toHaveCount(3);
  for (let i = 0; i < 3; i++) {
    const nm = rows.nth(i).locator('.ibp-nm');
    await expect(nm).toBeVisible();
    const box = await nm.boundingBox();
    expect(box!.width).toBeGreaterThan(40);
    for (const label of ['tick it', 'ignore']) {
      const b = rows.nth(i).getByRole('button', { name: label });
      const bb = await b.boundingBox();
      expect(bb!.width).toBeGreaterThan(20);
    }
  }
});
