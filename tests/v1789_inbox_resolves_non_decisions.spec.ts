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

// NOTE ON HOW THESE ASSERT, and the two corrections that got them here.
//
// (1) The first cut called kaiChronicleResolvePending({dryRun:true}) after page load and checked its
// return. It came back EMPTY on CI, and correctly: renderInboxFab runs the resolver AT LOAD — that is
// the whole point, "i dont want it pending my decisions at all if its not needed" — so by the time
// the test asked, the non-decisions were already retired.
//
// (2) The second cut asserted the dismissed list EXACTLY, and CI reported "Toothrow" dismissed as
// well, on all three tests, while a pristine local profile kept it every time. `Toothrow` resolves
// 'unique' and `_gFound('Toothrow')` is false locally, so the only branch that can retire it is
// "already in your grail" — which means something in the shard had already marked it found. These
// specs share a `file://` origin with every other spec in the shard, and several of them seed
// `d2r_foundLog` directly.
//
// Rather than guess at that, these now assert THE CLAIM instead of the whole world: the named
// non-decisions ARE retired for the stated reason, and a name is only required to survive when this
// page agrees it is not already found. A test that depends on global cleanliness it does not own is
// measuring the shard, not the code.

async function receiptOf(page: any) {
  return await page.evaluate(() => (window as any)._inboxLastResolve || { dismissed: [], kept: [] });
}

test('a base item name is retired — the Chronicle prints it for a row he has NOT found', async ({ page }) => {
  await seedInbox(page, ['Templar Coat', 'Bone Visage', 'Toothrow']);
  await page.goto(URL);
  const receipt = await receiptOf(page);
  const why = new Map<string, string>(receipt.dismissed.map((d: any) => [d.name, d.why]));
  const ctx = JSON.stringify(receipt);
  for (const n of ['Templar Coat', 'Bone Visage']) {
    expect(why.get(n), ctx).toContain('base item name');
  }
});

test('a truncated read is retired — the reader was quoting its own damage', async ({ page }) => {
  await seedInbox(page, ['Firel...', 'Heavas (partially obscured)', 'Toothrow']);
  await page.goto(URL);
  const receipt = await receiptOf(page);
  const why = new Map<string, string>(receipt.dismissed.map((d: any) => [d.name, d.why]));
  const ctx = JSON.stringify(receipt);
  for (const n of ['Firel...', 'Heavas (partially obscured)']) {
    expect(why.get(n), ctx).toContain('truncated');
  }
});

test('a name he already has is retired — there is nothing to rule on', async ({ page }) => {
  await seedInbox(page, ['Toothrow']);
  await page.goto(URL);
  // record the find with the app's OWN writer. Seeding d2r_foundLog directly does not work: the real
  // key is install-scoped ("I·<installId>·d2r_foundLog"), so _gFound reads false and the branch never
  // fires. Hardcoding that prefix here would put a second copy of the fork rule in the tree.
  await page.evaluate(() => {
    (window as any).kaiChronicleAccept('Rattlecage');
    localStorage.setItem('d2r_chronicleInbox', JSON.stringify([{ name: 'Rattlecage' }]));
    (window as any).renderInboxFab();
  });
  expect(await page.evaluate(() => !!(window as any)._gFound('Rattlecage'))).toBe(true);
  const receipt = await receiptOf(page);
  const why = new Map<string, string>(receipt.dismissed.map((d: any) => [d.name, d.why]));
  expect(why.get('Rattlecage'), JSON.stringify(receipt)).toContain('already in your grail');
});

test('a roster unique he does NOT have is never dismissed', async ({ page }) => {
  // THE SAFETY BOUNDARY. Every one of these six was later confirmed by eye to be a real find with a
  // date and a source monster, so a wrong dismissal here deletes a find silently — strictly worse
  // than a queue that is too long. Only names this page agrees are NOT already found are required to
  // survive; one that is already found is legitimately retired and proves nothing either way.
  const real = ['Latent Cold Rupture', 'Latent Crack of the Heavens', 'Latent Rotting Fissure',
                "Thundergod's Vigor", 'Toothrow', 'Witherstring'];
  await seedInbox(page, real);
  await page.goto(URL);
  const state = await page.evaluate((ns: string[]) => ns.map((n) => ({
    name: n,
    found: !!(window as any)._gFound(n),
    kind: ((window as any).d2rResolveItem(n) || {}).kind,
  })), real);
  const receipt = await receiptOf(page);
  const dismissed = new Set(receipt.dismissed.map((d: any) => d.name));
  const ctx = JSON.stringify({ state, receipt });
  const unfound = state.filter((s: any) => !s.found);
  expect(unfound.length, ctx).toBeGreaterThan(0);
  for (const s of unfound) {
    expect(s.kind, ctx).toBe('unique');
    expect(dismissed.has(s.name), ctx).toBe(false);
  }
});

test('the panel shows a receipt for the rows it cleared on its own', async ({ page }) => {
  await seedInbox(page, ['Templar Coat', 'Toothrow']);
  await page.goto(URL);
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
