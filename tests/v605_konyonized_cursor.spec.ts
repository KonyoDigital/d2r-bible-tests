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

// v605.1 — the grab animation: pointerdown steps --kcur to the grab frame and HOLDS; release restores.
test('gauntlet grabs on pointerdown and reopens on release', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const cur = () => page.evaluate(() => getComputedStyle(document.body).cursor.slice(0, 120));
  const idle = await cur();
  expect(idle).toContain('data:image/png');
  await page.mouse.move(600, 400);
  await page.mouse.down();
  await page.waitForTimeout(220);                 // 3 steps × 38ms + slack → holding the grab frame
  const held = await cur();
  expect(held).toContain('data:image/png');
  expect(held).not.toBe(idle);                    // a DIFFERENT gauntlet pose while the button is down
  await page.mouse.up();
  await page.waitForTimeout(220);
  expect(await cur()).toBe(idle);                 // …and back to the open hand
});
