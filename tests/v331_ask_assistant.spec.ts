import { test, expect } from '@playwright/test';

// v331 — AI Diablo II Helper: buildAskSnapshot reads live tallies + makeable-now engines,
// the #ask-bible-card injects after the Crafting Workshop, and askBible POSTs to /api/ask.
test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any).buildAskSnapshot && (window as any).askBible);
  await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tools'));
});

test('buildAskSnapshot returns the makeable-now snapshot shape from live tallies', async ({ page }) => {
  const snap = await page.evaluate(() => {
    // seed a couple runes/gems so the snapshot has content
    try { (window as any).adjustRuneStash && (window as any).adjustRuneStash('Tal', 5); } catch (e) {}
    try { (window as any).adjustGemStash && (window as any).adjustGemStash('Perfect Amethyst', 2); } catch (e) {}
    return (window as any).buildAskSnapshot();
  });
  expect(snap).toHaveProperty('runewords');
  expect(snap.runewords).toHaveProperty('completableNow');
  expect(Array.isArray(snap.runewords.completableNow)).toBe(true);
  expect(snap).toHaveProperty('crafts');
  expect(Array.isArray(snap.crafts.cubeableNow)).toBe(true);
  expect(Array.isArray(snap.crafts.oneAway)).toBe(true);
  expect(snap).toHaveProperty('tally');
  expect(snap).toHaveProperty('owned');
});

test('the #ask-bible-card injects after the Crafting Workshop with input + quick chips', async ({ page }) => {
  const r = await page.evaluate(() => {
    const card = document.getElementById('ask-bible-card');
    return {
      present: !!card,
      afterCraft: !!(card && card.previousElementSibling && card.previousElementSibling.id === 'craft-workshop-card'),
      hasInput: !!document.getElementById('ask-input'),
      chips: document.querySelectorAll('#ask-bible-card .ask-chip').length,
    };
  });
  expect(r.present).toBe(true);
  expect(r.afterCraft).toBe(true);
  expect(r.hasInput).toBe(true);
  expect(r.chips).toBeGreaterThanOrEqual(4);
});

test('askBible POSTs the snapshot to /api/ask and renders the answer', async ({ page }) => {
  let posted: any = null;
  await page.route('**/api/ask', (route) => {
    posted = route.request().postDataJSON();
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ answer: 'You can make **Spirit** now.' }) });
  });
  await page.evaluate(() => (window as any).askBible('what can I make?'));
  await page.waitForFunction(() => /Spirit/.test(document.getElementById('ask-thread')?.textContent || ''));
  const r = await page.evaluate(() => ({
    answer: document.querySelector('#ask-thread .ask-a')?.innerHTML || '',
    q: document.querySelector('#ask-thread .ask-q')?.textContent || '',
  }));
  expect(posted).not.toBeNull();
  expect(posted.question).toBe('what can I make?');
  expect(posted).toHaveProperty('snapshot');
  expect(posted.snapshot).toHaveProperty('runewords');
  expect(r.q).toBe('what can I make?');
  expect(r.answer).toContain('<b>Spirit</b>');   // **bold** → <b> via _askMd
});
