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

// v605.1/.2 — the grab animation: pointerdown on something GRABBABLE steps --kcur to the grab frame
// and HOLDS; release restores. Pressing empty background does NOTHING (Konyo: "if i click on just a
// blank space it works too — it should be smarter than that").
test('gauntlet grabs on interactive elements, ignores blank space', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const cur = () => page.evaluate(() => getComputedStyle(document.body).cursor.slice(0, 120));
  const idle = await cur();
  expect(idle).toContain('data:image/png');
  // 1) press a nav tab (interactive) → the hand closes, and reopens on release
  const tab = page.locator('.tab').first();
  const bb = (await tab.boundingBox())!;
  await page.mouse.move(bb.x + bb.width / 2, bb.y + bb.height / 2);
  await page.mouse.down();
  await page.waitForTimeout(220);                 // 3 steps × 38ms + slack → holding the grab frame
  const held = await cur();
  expect(held).toContain('data:image/png');
  expect(held).not.toBe(idle);                    // a DIFFERENT gauntlet pose while the button is down
  await page.mouse.up();
  await page.waitForTimeout(220);
  expect(await cur()).toBe(idle);                 // …and back to the open hand
  // 2) press verified BLANK space → the hand must NOT close (v613: judged by the live predicate)
  const blank = await page.evaluate(() => {
    const w: any = window;
    // v708 recal — five FIXED points all landed on interactive chrome after the v703 nav
    // clusters shifted layout ~12px (coordinate probes rot with every layout change).
    // Scan a grid instead: any genuinely inert point qualifies.
    for (let y = 140; y < Math.min(innerHeight - 40, 860); y += 34) {
      for (const x of [200, 400, 720, 1000, 1240]) {
        if (x > innerWidth - 20) continue;
        const el = document.elementFromPoint(x, y);
        if (el && !w._kcurHit(el)) return { x, y };
      }
    }
    return null;
  });
  expect(blank).not.toBeNull();
  await page.mouse.move(blank!.x, blank!.y);
  await page.mouse.down();
  await page.waitForTimeout(220);
  expect(await cur()).toBe(idle);                 // blank press → hand stays OPEN
  await page.mouse.up();
  await page.waitForTimeout(220);
  expect(await cur()).toBe(idle);
});

// v613 — FACTUAL CLICKABILITY: the grab/sparkle predicate must agree with reality (the wf_28c4af50
// audit). Inert-but-decorated surfaces never grab; delegated/decorator surfaces (no onclick attr) DO.
test('predicate truth: inert surfaces refuse, delegated surfaces grab', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    const hit = (sel: string) => { const el = document.querySelector(sel); return el ? w._kcurHit(el) : null; };
    const mk = (html: string) => { const d = document.createElement('div'); d.innerHTML = html; document.body.appendChild(d); const el = d.firstElementChild!; const out = w._kcurHit(el); d.remove(); return out; };
    return {
      // INERT — must refuse: tooltip-only chip, decorative art wrap, count pill, card container
      arttipOnly: mk('<span data-arttip="Oath">Oath</span>'),
      artWrap: mk('<span class="d2art-wrap sm"><img alt=""></span>'),
      countPill: mk('<span class="to-ct">5</span>'),
      cardShell: mk('<div class="f-card"><div class="f-cardbody">text</div></div>'),
      sockBadge: mk('<span class="to-sock">3os</span>'),
      // CLICKABLE — must grab: nav tab (button+onclick prop), delegated data-route, vault chip
      navTab: hit('.tab'),
      dataRoute: mk('<span data-art-route="Shako">Shako</span>'),
      vaultChip: mk('<span class="vault-chip" draggable="true" data-vault-item="X">X</span>'),
      inlineOnclick: mk('<span onclick="void 0">go</span>'),
      nestedInOnclick: (() => { const d = document.createElement('div'); d.innerHTML = '<div onclick="void 0"><span class="deep"><b>leaf</b></span></div>'; document.body.appendChild(d); const out = w._kcurHit(d.querySelector('b')); d.remove(); return out; })(),
    };
  });
  expect(r.arttipOnly).toBe(false);
  expect(r.artWrap).toBe(false);
  expect(r.countPill).toBe(false);
  expect(r.cardShell).toBe(false);
  expect(r.sockBadge).toBe(false);
  expect(r.navTab).toBe(true);
  expect(r.dataRoute).toBe(true);
  expect(r.vaultChip).toBe(true);
  expect(r.inlineOnclick).toBe(true);
  expect(r.nestedInOnclick).toBe(true);   // the 8-hop ancestor walk
});
