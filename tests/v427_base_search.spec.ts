import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v427 — all 498 game-data BASE ITEMS are searchable + clickable + routable to a base card
// (class · max sockets · runewords it enables). Closes the "search all 1200+ items" gap.

test('every base item produces a valid base card via openDrop + baseDetailHtml', async ({ page }) => {
  const errs: string[] = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    const bases = Object.keys(w.BASE_CLASS || {});
    let cardOk = 0; const fail: string[] = [];
    bases.forEach((b) => { const h = w.baseDetailHtml ? w.baseDetailHtml(b) : ''; if (h && /base-item-card/.test(h)) cardOk++; else fail.push(b); });
    // openDrop routes a spread of bases to the base card
    const route = (n: string) => { try { w.openDrop(n); } catch (e) { return false; } const p = document.getElementById('item-detail'); return !!(p && p.classList.contains('show') && /base-item-card/.test(p.innerHTML)); };
    return {
      baseCount: bases.length, cardOk, failSample: fail.slice(0, 10),
      cryptic: route('Cryptic Axe'), monarch: route('Monarch'), quilted: route('Quilted Armor'), cap: route('Cap'),
    };
  });
  expect(r.baseCount).toBeGreaterThanOrEqual(490);
  expect(r.cardOk).toBe(r.baseCount);    // every base cards cleanly
  expect(r.cryptic).toBe(true);
  expect(r.monarch).toBe(true);
  expect(r.quilted).toBe(true);
  expect(r.cap).toBe(true);
  expect(errs).toEqual([]);
});

test('every base reads white/grey (basic) rarity — synced across search/vault/hover; no item downgraded', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    const bases = Object.keys(w.BASE_CLASS || {});
    const notBasic: string[] = [];
    bases.forEach((b) => { if (w._artRarity(b) !== 'basic') notBasic.push(b + '=' + w._artRarity(b)); });
    return {
      total: bases.length, notBasic: notBasic.slice(0, 15), notBasicCount: notBasic.length,
      basicHex: w._qHex('Cryptic Axe'),                 // → var(--q-normal) = #f4f4f4 white
      suffixedBasic: w._artRarity('Cryptic Axe (5os)') === 'basic' && w._artRarity('Monarch (Larzuk base)') === 'basic',
      // real items must NOT be downgraded to basic
      windforce: w._artRarity('Windforce'), spirit: w._artRarity('Spirit'),
      talRasha: w._artRarity("Tal Rasha's Adjudication"), istRune: w._artRarity('Ist rune'),
    };
  });
  expect(r.notBasicCount).toBe(0);              // all 498 bases read basic (white/grey)
  expect(r.basicHex).toContain('q-normal');     // basic → white var
  expect(r.suffixedBasic).toBe(true);
  expect(r.windforce).toBe('unique');           // not downgraded
  expect(r.spirit).toBe('rw');
  expect(r.talRasha).toBe('set');
  expect(r.istRune).toBe('rune');
});

test('the global search bar surfaces base items by name', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1800);
  await page.fill('#gsearch-input', 'cryptic axe');
  await page.waitForTimeout(400);
  const r1 = await page.evaluate(() => {
    const box = document.getElementById('gsearch-results');
    return Array.from(box?.querySelectorAll('.gsearch-item') || []).map(el => ({
      label: (el.querySelector('.gsearch-lab')?.textContent || '').trim(),
      cat: (el.querySelector('.gsearch-cat')?.textContent || '').trim(),
    }));
  });
  // a base row exists with cat 'base'
  expect(r1.some(x => /Cryptic Axe/i.test(x.label) && x.cat === 'base')).toBe(true);

  await page.fill('#gsearch-input', 'monarch');
  await page.waitForTimeout(400);
  const r2 = await page.evaluate(() => {
    const box = document.getElementById('gsearch-results');
    return Array.from(box?.querySelectorAll('.gsearch-item') || []).map(el => (el.querySelector('.gsearch-lab')?.textContent || '').trim());
  });
  expect(r2.some(x => /Monarch/i.test(x))).toBe(true);
});

test('clicking a base search result opens its base card (no console errors)', async ({ page }) => {
  const errs: string[] = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(URL); await page.waitForTimeout(1800);
  await page.fill('#gsearch-input', 'thunder maul');
  await page.waitForTimeout(400);
  await page.evaluate(() => {
    const box = document.getElementById('gsearch-results');
    const row = Array.from(box?.querySelectorAll('.gsearch-item') || []).find(el => /Thunder Maul/i.test(el.querySelector('.gsearch-lab')?.textContent || ''));
    (row as HTMLElement)?.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
  });
  await page.waitForTimeout(400);
  const opened = await page.evaluate(() => {
    const p = document.getElementById('item-detail');
    return !!(p && p.classList.contains('show') && /base-item-card/.test(p.innerHTML) && /Thunder Maul/.test(p.innerHTML));
  });
  expect(opened).toBe(true);
  expect(errs).toEqual([]);
});
