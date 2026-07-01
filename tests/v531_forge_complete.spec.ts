import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v531 — completing a Forge task actually moves you forward:
//  (1) a ready Make-now "✓ created" tick marks the runeword made AND re-renders the Forge → it leaves the list.
//  (2) a chain's FINAL "Forge <word>" step is a "✓ forged — done" that CREATES the word (marks it, resets the
//      chain), instead of the old "restart" that just looped back to step 1.

test('ready Make-now: ✓ created marks the word AND removes it from the Forge immediately', async ({ page }) => {
  await page.addInitScript(() => {
    // an owned exact-socket base + runes → Insight is a ready Make-now (not seeded/made)
    localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 1, Tir: 1, Tal: 1, Sol: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Colossus Voulge (4os)');
    const before = w.forgeScan().now.some((t: any) => t.rw === 'Insight' && !t.deferred);
    const madeBefore = !!JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')['Insight'];
    w.rwToggleMade('Insight');                       // the "✓ created" action
    const madeAfter = !!JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')['Insight'];
    const after = w.forgeScan().now.some((t: any) => t.rw === 'Insight');
    return { before, madeBefore, madeAfter, after, rendersForge: typeof w.renderForge };
  });
  expect(r.before).toBe(true);       // Insight was a ready Make-now
  expect(r.madeBefore).toBe(false);
  expect(r.madeAfter).toBe(true);    // ✓ created marked it
  expect(r.after).toBe(false);       // and it's gone from the Forge
});

test('forgeForged creates the runeword + resets the chain step (final "Forge" tick completes it)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    return {
      hasFn: typeof w.forgeForged,
      // exercise it: mark a non-seeded word made via the chain-complete path
      run: (() => {
        localStorage.setItem('d2r_forgeStep', JSON.stringify({ 'chain|TestBase': 2 }));
        w.forgeForged('chain|TestBase', 'Insight');
        const made = !!JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')['Insight'];
        const step = JSON.parse(localStorage.getItem('d2r_forgeStep') || '{}')['chain|TestBase'] || 0;
        return { made, step };
      })(),
    };
  });
  expect(r.hasFn).toBe('function');
  expect(r.run.made).toBe(true);   // the word is created
  expect(r.run.step).toBe(0);      // the chain step reset (no lingering "restart")
});
