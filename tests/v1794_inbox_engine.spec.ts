import { test, expect } from './_net_stub';
import * as path from 'path';

// v1794 — THE INBOX STOPS ASKING HIM ABOUT THINGS THAT ARE NOT IN THE GAME.
//
// Konyo: "make sure the inbox is now calliverated to the new coding and architecure. so it doesnt
// tell me to do something inaccurate and unrelated to the game. it should have its own engine
// coding even or an AI reader task for it to automate it too."
//
// He is describing a measured class of row. On 2026-08-18 the console side learned to repair OCR
// slips — tv/chronicle_resolve.py folds a reader's raw name onto this file's own unique roster, so
// "Battlecage" becomes Rattlecage — and of the 36 names read off his ledger by hand that day, SIX
// were exactly that: the same row read twice, once right and once wrong.
//
// THE BOARD NEVER LEARNED IT. d2rResolveItem is exact-match only, so on this side "Battlecage"
// resolved 'unknown', fell through every rule and landed on hold: human-review — a row on his screen
// asking him to tick an item that does not exist in this game. Two halves built, the joint never
// made. And the queue in his browser is a legacy store: rows queued before the fold shipped sit
// there raw, so no amount of correctness on the console reaches them.
//
// WHAT THESE SPECS PIN is the boundary, not the tidying. The dangerous direction is a wrong fold: a
// name repaired onto the wrong roster item writes a find he never made, silently, into a ledger that
// has no unfind. So the ambiguous case must stay ambiguous, real uniques must survive every pass,
// and debris must fold onto nothing.
//
// The agreement between this fold and the Python one is NOT tested here — tv/test_inbox_engine.py
// extracts the shipped block out of bible.html, runs it in node, and fails on the first name where
// the two disagree. These specs test what the BOARD does with the answer.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* Seed the queue AND clear everything the resolver reads. These specs share a `file://` origin with
   every other spec in the shard — including their own earlier tests — and v1789 learned that the
   hard way twice: other specs write the grail, and v1790's keep-list survives between tests, after
   which a row stops being retired and five assertions go red at once. A fixture that seeds only what
   it wants and inherits the rest is not testing the code, it is testing the run order. */
async function seedInbox(page: any, names: string[]) {
  await page.addInitScript((ns: string[]) => {
    localStorage.removeItem('d2r_chronicleAutoRetired');
    localStorage.removeItem('d2r_chronicleKeepPending');
    localStorage.removeItem('d2r_inboxReader');
    localStorage.setItem('d2r_chronicleInbox', JSON.stringify(ns.map((n) => ({ name: n }))));
  }, names);
}

/* Make these names NOT-FOUND on this page, whatever the shard left behind. toggleOwned is the
   board's own writer, so this goes through the same door a click does and needs no knowledge of the
   install-scoped key ("I·<installId>·d2r_foundLog") that defeated the first version of v1789's. */
async function ensureUnfound(page: any, names: string[]) {
  await page.evaluate((ns: string[]) => {
    ns.forEach((n) => {
      for (let i = 0; i < 3 && (window as any)._gFound(n); i++) (window as any).toggleOwned(n);
    });
  }, names);
}

test('the engine exists as a real global, and the fold with it', async ({ page }) => {
  // v1793's scar, one floor up: a shared thing defined inside a function nobody called is not
  // shared. Both of these are assigned at parse time for exactly that reason.
  await page.goto(URL);
  expect(await page.evaluate(() => typeof (window as any).d2rInboxEngine)).toBe('function');
  expect(await page.evaluate(() => typeof ((window as any).D2R_INBOX_FOLD || {}).fold)).toBe('function');
  // the fold is worthless against an empty roster — chronicle_resolve.load_roster RAISES rather than
  // return {} for the same reason: folding against nothing classifies every name as debris
  expect(await page.evaluate(() => (window as any)._gUniqueRoster().length)).toBeGreaterThan(300);
});

test('a misread of an item he does NOT have is shown as the REAL item', async ({ page }) => {
  // "Battlecage" is not an item in this game. Rattlecage is. Before this he was asked to rule on the
  // first one; now he rules on the second, with the reader's actual string kept beneath it as the
  // receipt — a repaired name with no receipt is a name he cannot check.
  await page.goto(URL);
  await ensureUnfound(page, ['Rattlecage']);
  const v = await page.evaluate(() => (window as any).d2rInboxEngine('Battlecage'));
  expect(v.verdict).toBe('misread-open');
  expect(v.action).toBe('hold');          // a fold repairs a spelling; it is never a second witness
  expect(v.canonical).toBe('Rattlecage');
  expect(v.show).toBe('Rattlecage');
});

test('a misread of an item he ALREADY has is retired — there was never a decision', async ({ page }) => {
  // Six of the 36 names on his ledger were this: the same row read twice, once right and once wrong,
  // carrying zero new information.
  await page.goto(URL);
  await page.evaluate(() => (window as any).kaiChronicleAccept('Nagelring'));
  expect(await page.evaluate(() => !!(window as any)._gFound('Nagelring'))).toBe(true);
  const v = await page.evaluate(() => (window as any).d2rInboxEngine('Naglring'));
  expect(v.verdict).toBe('misread-settled');
  expect(v.action).toBe('retire');
  expect(v.why).toContain('Nagelring');
});

test('ticking a repaired row writes the ROSTER name, not the reader\'s misspelling', async ({ page }) => {
  // THE DEFECT THIS CLOSES, in chronicle_resolve.py's own words: "A GROUNDED NAME THAT IS NOT A
  // ROSTER NAME CAN NEVER TICK." The board had the same hole from the other side — pressing "tick
  // it" wrote d2r_foundLog['Battlecage'], a key nothing counts, nothing renders and nothing can ever
  // un-tick. The row left the queue, looked accepted, and added zero to his total.
  await seedInbox(page, ['Battlecage']);
  await page.goto(URL);
  await ensureUnfound(page, ['Rattlecage']);
  await page.evaluate(() => (window as any).kaiChronicleAccept('Battlecage'));
  expect(await page.evaluate(() => !!(window as any)._gFound('Rattlecage'))).toBe(true);
  expect(await page.evaluate(() => !!(window as any)._gFound('Battlecage'))).toBe(false);
  // and the raw string it was stored under is gone from the queue, not left behind as a twin
  const left = await page.evaluate(() =>
    ((window as any).kaiChronicleInbox({ sync: false }) || []).map((x: any) => x.name));
  expect(left).not.toContain('Battlecage');
});

test('a name that is not an item in this game leaves his queue for the reader lane', async ({ page }) => {
  // THE ROW HE COMPLAINED ABOUT. "Chronicle of Items" is the panel's own heading; the reader typed it
  // down and the board asked him whether he had found it.
  const junk = ['Chronicle of Items', 'Sort by'];
  await seedInbox(page, [...junk, 'Toothrow']);
  await page.goto(URL);
  /* POLL, do not race. renderInboxFab's auto-run is on a 900ms timer after `load`, so reading the
     receipt straight off `goto` is a coin flip that happens to land right when the assertions before
     it are slow enough. Measured here: 8 of 9 tests passed and this one failed on all three retries
     with an EMPTY receipt — not a wrong verdict, an unwritten one. Waiting for the automatic path is
     also the more honest test, because the automatic path is the feature. */
  await expect.poll(() => page.evaluate(() => !!(window as any)._inboxLastResolve),
                    { timeout: 15000 }).toBe(true);
  const receipt = await page.evaluate(() => (window as any)._inboxLastResolve || { dismissed: [], reader: [] });
  const ctx = JSON.stringify(receipt);
  const readerNames = (receipt.reader || []).map((r: any) => r.name);
  for (const n of junk) expect(readerNames, ctx).toContain(n);
  // handed over WITH its frame and session, never deleted: "we looked and it is not an item" and
  // "nobody looked" must never produce the same tidy empty queue
  const q = await page.evaluate(() => (window as any).inboxReaderQueue());
  expect(q.map((x: any) => x.name)).toEqual(expect.arrayContaining(junk));
  expect(q[0].ts).toBeGreaterThan(0);
  // and it is off the decision queue
  const pend = await page.evaluate(() =>
    ((window as any).kaiChronicleInbox({ sync: false }) || []).map((x: any) => x.name));
  for (const n of junk) expect(pend, ctx).not.toContain(n);
});

test('the reader hand-off is never silent — the panel says how many and where they went', async ({ page }) => {
  // a queue that got smaller with no explanation is indistinguishable from one that lost something
  await seedInbox(page, ['Chronicle of Items', 'Toothrow']);
  await page.goto(URL);
  await page.evaluate(() => {
    (window as any).renderInboxFab();
    const pop = document.getElementById('inbox-pop');
    if (pop && !pop.classList.contains('open')) (window as any).inboxPopTog();
  });
  const pop = page.locator('#inbox-pop');
  await expect(pop).toHaveClass(/open/);
  await expect(pop.locator('.ibp-auto').filter({ hasText: 'matched nothing in this game' }))
    .toContainText('Chronicle of Items');
});

test('an ambiguous fold names BOTH candidates and never guesses', async ({ page }) => {
  // "Bloodrist" sits within AMBIGUITY_GAP of Bloodrise AND Bloodfist — two real grail items one
  // character apart from each other. Picking a winner here writes a find he never made into a ledger
  // that has no unfind, so it reaches him as an open question with both names on it. That is still
  // more use to him than the raw string ever was.
  await page.goto(URL);
  const v = await page.evaluate(() => (window as any).d2rInboxEngine('Bloodrist'));
  expect(v.verdict).toBe('ambiguous');
  expect(v.action).toBe('hold');
  expect(v.canonical).toBeNull();
  expect(v.rivals).toEqual(expect.arrayContaining(['Bloodrise', 'Bloodfist']));
  const said = await page.evaluate((w: string) => (window as any)._chSayWhy(w), v.why);
  expect(said).toContain('Bloodrise');
  expect(said).toContain('guessing');
});

test('a roster unique he does NOT have is still never dismissed', async ({ page }) => {
  // THE SAFETY BOUNDARY, unchanged from v1789 and re-asserted because this version added three new
  // ways for a row to leave the queue. Every one of these six was later confirmed by eye to be a real
  // find with a date and a source monster: a wrong dismissal deletes a find silently, which is
  // strictly worse than a queue that is too long.
  const real = ['Latent Cold Rupture', 'Latent Crack of the Heavens', 'Latent Rotting Fissure',
                "Thundergod's Vigor", 'Toothrow', 'Witherstring'];
  await seedInbox(page, real);
  await page.goto(URL);
  await ensureUnfound(page, real);
  await page.evaluate((ns: string[]) => {
    localStorage.setItem('d2r_chronicleInbox', JSON.stringify(ns.map((n) => ({ name: n }))));
    (window as any)._inboxLastResolve = null;
    (window as any).renderInboxFab();
  }, real);
  const state = await page.evaluate((ns: string[]) => ns.map((n) => ({
    name: n,
    found: !!(window as any)._gFound(n),
    verdict: ((window as any).d2rInboxEngine(n) || {}).verdict,
  })), real);
  const receipt = await page.evaluate(() => (window as any)._inboxLastResolve || { dismissed: [], reader: [] });
  const gone = new Set([...(receipt.dismissed || []).map((d: any) => d.name),
                        ...(receipt.reader || []).map((d: any) => d.name)]);
  const ctx = JSON.stringify({ state, receipt });
  const unfound = state.filter((s: any) => !s.found);
  expect(unfound.length, ctx).toBeGreaterThan(0);
  for (const s of unfound) {
    expect(s.verdict, ctx).toBe('find');
    expect(gone.has(s.name), ctx).toBe(false);
  }
});

test('the pending row is judged NOW, not when it was queued', async ({ page }) => {
  // triageWhy is a stamp from the moment the name arrived, and the queue is full of rows that predate
  // every rule since — they rendered as "the readers could not call this one", which is the panel
  // admitting it has nothing to say about a row it is nonetheless asking him to rule on.
  await page.addInitScript(() => {
    localStorage.removeItem('d2r_chronicleAutoRetired');
    localStorage.removeItem('d2r_chronicleKeepPending');
    localStorage.removeItem('d2r_inboxReader');
    // a LEGACY row: no triageWhy at all, exactly as the queue stored them before v1789
    localStorage.setItem('d2r_chronicleInbox', JSON.stringify([{ name: 'Battlecage' }]));
  });
  await page.goto(URL);
  await ensureUnfound(page, ['Rattlecage']);
  await page.evaluate(() => {
    localStorage.setItem('d2r_chronicleInbox', JSON.stringify([{ name: 'Battlecage' }]));
    (window as any).renderInboxFab();
    const pop = document.getElementById('inbox-pop');
    if (pop && !pop.classList.contains('open')) (window as any).inboxPopTog();
  });
  const row = page.locator('#inbox-pop .ibp-row').first();
  await expect(row.locator('.ibp-nm')).toContainText('Rattlecage');
  await expect(row.locator('.ibp-nm')).toContainText('Battlecage');   // the receipt for the repair
  await expect(row.locator('.ibp-why')).toContainText('misspelling');
  // v1789's geometry scar: .ibp-why is flex:0 0 100% and in a non-wrapping row it squeezes the name
  // and both buttons to zero width. textContent was perfect the whole time; only pixels showed it.
  const box = await row.locator('.ibp-nm').boundingBox();
  expect(box!.width).toBeGreaterThan(40);
  /* v2682 — THE THIRD SPEC OF THE SAME BUTTON RENAME, and the most expensive of them.
     `getByRole('button', { name: 'tick it' })` has no match: the popover renders
     `📖 Chronicle` (.ibp-ok), `🏦 Vault` (.ibp-vault), `📖🏦 Both` (.ibp-both) and `ignore`.
     Measured on CI — `locator.boundingBox: Test timeout of 120000ms exceeded`, so this one line
     burned two minutes of every Routine I run before failing. `ignore` still exists and is
     untouched; only the accept door was renamed.
     THE LAW IS GEOMETRY, and it is unchanged: this file's own scar is that `.ibp-why` is
     `flex:0 0 100%` and squeezes the name and both buttons to ZERO width while textContent stays
     perfect — only pixels showed it. So it still measures an accept door and a dismiss door, by
     the names they actually carry. [[label-outlived-referent]] */
  for (const label of ['Chronicle', 'ignore']) {
    const bb = await row.getByRole('button', { name: label }).boundingBox();
    expect(bb!.width).toBeGreaterThan(20);
  }
});
