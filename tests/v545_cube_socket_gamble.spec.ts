import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v545 — CUBE-SOCKET GAMBLE. You own a base TAGGED for a specific word (e.g. "Flail (Heart of the Oak base)"),
// it's unsocketed, and its MAX sockets OVERSHOOT the word's count (Flail max 5, HotO needs 4) — so Larzuk can't
// hit it cleanly. Instead of dropping the owned base to a "go get a base" one-step, the Forge offers the cube
// socket recipe (Ral+Amn+P.gem = a RANDOM 1→max) as a gamble task. Scoped to TAGGED bases only so it never
// floods untagged white bases. Konyo: "its unsocketed.. but in this case why not task/pipeline to cube it
// randomly to gamble for the 4?"

test('_ownedBases recognises a "<Base> (<Runeword> base)" tagged, unsocketed base', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Flail (Heart of the Oak base)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ko: 17, Vex: 10, Pul: 18, Thul: 36 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Flail (Heart of the Oak base)');
    const b = (w._ownedBases() || []).find((x: any) => x.base === 'Flail');
    return b ? { base: b.base, sockets: b.sockets, max: b.max, taggedRw: b.taggedRw } : null;
  });
  expect(r).not.toBeNull();
  expect(r!.base).toBe('Flail');
  expect(r!.sockets).toBe(0);
  expect(r!.max).toBe(5);                       // Flail max sockets = 5
  expect(r!.taggedRw).toBe('Heart of the Oak'); // resolved to the canonical runeword
});

test('an owned tagged base whose max overshoots → a cube-socket GAMBLE pipeline task (not "go get a base")', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Flail (Heart of the Oak base)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ko: 17, Vex: 10, Pul: 18, Thul: 36 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Flail (Heart of the Oak base)');
    const s = w.forgeScan();
    const pipe = s.pipeline.find((t: any) => t.rw === 'Heart of the Oak');
    const one = s.onestep.find((t: any) => t.rw === 'Heart of the Oak');
    return {
      pipe: pipe ? { gamble: !!pipe.cubeGamble, base: pipe.base.base, need: pipe.need, max: pipe.base.max } : null,
      oneSub: one ? one.sub : null,
    };
  });
  expect(r.pipe).not.toBeNull();
  expect(r.pipe!.gamble).toBe(true);   // it's a gamble, not a clean Larzuk
  expect(r.pipe!.base).toBe('Flail');
  expect(r.pipe!.need).toBe(4);        // HotO = 4 sockets
  expect(r.pipe!.max).toBe(5);         // Flail max 5 → Larzuk overshoots → gamble
  expect(r.oneSub).not.toBe('base');   // must NOT also show as a "go get a Flail" one-step
});

test('the gamble step renders in the Pipeline card (recipe + re-roll wording, not "guaranteed max")', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Flail (Heart of the Oak base)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ko: 17, Vex: 10, Pul: 18, Thul: 36 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Flail (Heart of the Oak base)');
    w.switchTab('forge'); w.forgeSetFilter('pipeline'); w.renderForge();
    const txt = document.getElementById('tab-forge')!.textContent || '';
    return {
      gamble: /Cube-socket/.test(txt),
      reroll: /re-roll the cube until it lands/i.test(txt),
      recipe: /Ral \+ Amn \+ Perfect Amethyst/.test(txt),  // Flail = weapon slot
    };
  });
  expect(r.gamble).toBe(true);
  expect(r.reroll).toBe(true);
  expect(r.recipe).toBe(true);
});

test('untagged white bases do NOT get a gamble task (scoped to tagged bases only)', async ({ page }) => {
  // A plain "Crystal Sword (Larzuk base)" (6os max) is NOT tagged for any word → for a 4os word it stays a
  // "go get the right base" one-step, never a gamble. Only tagged owned bases gamble.
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Crystal Sword (Larzuk base)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ko: 17, Vex: 10, Pul: 18, Thul: 36 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Crystal Sword (Larzuk base)');
    const s = w.forgeScan();
    return { anyGamble: s.pipeline.some((t: any) => t.cubeGamble) };
  });
  expect(r.anyGamble).toBe(false);
});
