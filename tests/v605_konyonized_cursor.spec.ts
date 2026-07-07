import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v605 — 🧤 KONYONIZED CURSOR: the real D2R gauntlet hand (CASC-extracted ohand.sprite) is the app-wide
// cursor, like the game itself. Locks: (1) the gauntlet data-URI actually applies (computed style, not
// just CSS text) on the body AND on clickable chrome (inline cursor:pointer styles must lose to it);
// (2) text entry keeps the I-beam; (3) no page errors from the giant data-URI rule.
test('gauntlet cursor applies app-wide, text inputs keep the I-beam', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const cur = (el: Element | null) => el ? getComputedStyle(el).cursor : '';
    const body = cur(document.body);
    const tab = cur(document.querySelector('.nav-tab, [onclick]'));
    const search = cur(document.querySelector('input[type=text], input[type=search], #search, input'));
    return { body: body.slice(0, 40), tab: tab.slice(0, 40), search,
      bodyIsGauntlet: body.includes('data:image/png'), tabIsGauntlet: tab.includes('data:image/png') };
  });
  expect(r.bodyIsGauntlet).toBe(true);   // the whole app wears the gauntlet
  expect(r.tabIsGauntlet).toBe(true);    // clickables too — inline cursor:pointer loses to it
  expect(r.search).toBe('text');         // typing keeps the I-beam
  expect(errors).toEqual([]);
});
