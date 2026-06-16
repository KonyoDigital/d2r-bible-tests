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

test('the #ask-bible-card injects at the TOP of the Tools tab (above the Vault) with input + chips', async ({ page }) => {
  const r = await page.evaluate(() => {
    const card = document.getElementById('ask-bible-card');
    const tools = document.getElementById('tab-tools');
    return {
      present: !!card,
      firstInTools: tools?.firstElementChild?.id === 'ask-bible-card',
      hasInput: !!document.getElementById('ask-input'),
      hasScan: !!document.querySelector('#ask-bible-card .ask-chip-scan'),
      chips: document.querySelectorAll('#ask-bible-card .ask-chip').length,
    };
  });
  expect(r.present).toBe(true);
  expect(r.firstInTools).toBe(true);   // v335: rides above the Vault
  expect(r.hasInput).toBe(true);
  expect(r.hasScan).toBe(true);        // 🎯 scan button
  expect(r.chips).toBeGreaterThanOrEqual(5);
});

test('buildTopPicks ranks top-tier makeable opportunities + scanTopPicks renders a panel', async ({ page }) => {
  const r = await page.evaluate(() => {
    const tp = (window as any).buildTopPicks();
    (window as any).scanTopPicks({ localOnly: true });   // local render, no AI call
    return {
      shape: ['makeNow', 'afterCubing', 'close'].every((k) => Array.isArray(tp[k])),
      panel: !!document.querySelector('#ask-thread .ask-toppicks'),
      inSnapshot: !!(window as any).buildAskSnapshot().topPicks,
    };
  });
  expect(r.shape).toBe(true);
  expect(r.panel).toBe(true);
  expect(r.inSnapshot).toBe(true);
});

test('the visual Create-Now dashboard auto-renders makeable top-tier items (runewords detected)', async ({ page }) => {
  const r = await page.evaluate(() => {
    ['Tal', 'Thul', 'Ort', 'Amn'].forEach((n) => (window as any).adjustRuneStash(n, 2)); // Spirit runes
    (window as any).renderCreateNow();
    const host = document.getElementById('create-now')!;
    return {
      atTop: document.querySelector('#ask-bible-card .boss-body')?.firstElementChild?.id === 'create-now',
      hasTitle: !!host.querySelector('.cn-title'),
      tiles: host.querySelectorAll('.cn-tile').length,
      names: [...host.querySelectorAll('.cn-name')].map((e) => e.textContent || ''),
    };
  });
  expect(r.atTop).toBe(true);          // dashboard sits at the top of the card body
  expect(r.hasTitle).toBe(true);
  expect(r.tiles).toBeGreaterThan(0);
  expect(r.names.some((n) => /Spirit/.test(n))).toBe(true);  // runewords resolve via .n (bug fix)
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
    answer: document.querySelector('#ask-thread .ask-a:not(.ask-toppicks)')?.innerHTML || '',
    q: document.querySelector('#ask-thread .ask-q')?.textContent || '',
  }));
  expect(posted).not.toBeNull();
  expect(posted.question).toBe('what can I make?');
  expect(posted).toHaveProperty('snapshot');
  expect(posted.snapshot).toHaveProperty('runewords');
  expect(r.q).toBe('what can I make?');
  expect(r.answer).toContain('<b>Spirit</b>');   // **bold** → <b> via _askMd
});
