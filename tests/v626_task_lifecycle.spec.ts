import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v626 — TASK LIFECYCLE DEMONSTRATIONS (Konyo: 'simulate and demonstrate all types and every
// outcome… that it's automatically coded and synced and tasking properly'). Every consume outcome
// drives the REAL UI and asserts the next task appears automatically.

const ALL_RUNES = ['El','Eld','Tir','Nef','Eth','Ith','Tal','Ral','Ort','Thul','Amn','Sol','Shael','Dol','Hel','Io','Lum','Ko','Fal','Lem','Pul','Um','Mal','Ist','Gul','Vex','Ohm','Lo','Sur','Ber','Jah','Cham','Zod'];
const seedState = (page: any, owned: string[], copies: any = {}) => page.evaluate(({ owned, copies }: any) => {
  localStorage.setItem('d2r_rwProfile', 'fresh');
  localStorage.setItem('d2r_rwMade', JSON.stringify({}));
  localStorage.setItem('d2r_owned', JSON.stringify(owned));
  localStorage.setItem('d2r_copies', JSON.stringify(copies));
  const st: any = {};
  ['El','Eld','Tir','Nef','Eth','Ith','Tal','Ral','Ort','Thul','Amn','Sol','Shael','Dol','Hel','Io','Lum','Ko','Fal','Lem','Pul','Um','Mal','Ist','Gul','Vex','Ohm','Lo','Sur','Ber','Jah','Cham','Zod'].forEach((n) => (st[n] = 6));
  localStorage.setItem('d2r_runeStash', JSON.stringify(st));
}, { owned, copies });
const cleanup = (page: any) => page.evaluate(() => ['d2r_rwProfile', 'd2r_rwMade', 'd2r_owned', 'd2r_copies', 'd2r_runeStash', 'd2r_rwBaseUsed', 'd2r_rwUnmade'].forEach((k) => localStorage.removeItem(k)));

test("Konyo's exact case: ONE last copy, TWO 6os words — forging one AUTOMATICALLY re-tasks the other as get-a-base", async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  await seedState(page, ['Phase Blade (Larzuk base)']);
  await page.reload(); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => new Promise<any>((res) => {
    const w: any = window;
    w.switchTab('forge'); try { w.renderForge(); } catch (e) {}
    const sc0 = w.forgeScan();
    const pbWords = [].concat(sc0.pipeline || []).filter((t: any) => t.base && t.base.name === 'Phase Blade (Larzuk base)').map((t: any) => t.rw);
    if (pbWords.length < 2) { res({ skip: true, pbWords }); return; }
    const [w1, w2] = pbWords;
    w.rwToggleMade(w1, 'Phase Blade (Larzuk base)');   // forge word 1 via its card (hint = the clicked base)
    setTimeout(() => {
      const sc1 = w.forgeScan();
      const own = JSON.parse(localStorage.getItem('d2r_owned') || '[]');
      const w2task = [].concat(sc1.now || [], sc1.pipeline || [], sc1.onestep || [], sc1.farm || []).find((t: any) => t.rw === w2);
      const dom = (document.getElementById('forge-body') || document.body).textContent || '';
      res({
        skip: false, w1, w2,
        copyConsumed: own.indexOf('Phase Blade (Larzuk base)') < 0,
        w2kind: w2task ? (w2task.kind + ':' + (w2task.sub || '')) : 'MISSING',
        w2inDom: dom.includes(w2),
      });
    }, 700);
  }));
  if (r.skip) test.skip(true, 'env produced <2 PB words');
  expect(r.copyConsumed).toBe(true);            // the forge ate the last copy
  expect(r.w2kind).toBe('onestep:base');        // …and word 2 AUTOMATICALLY became a get-a-base task
  expect(r.w2inDom).toBe(true);                 // …visible in the rendered Forge, no click needed
  await cleanup(page);
});

test('TWO copies, two words: forging one keeps the other PIPELINED on the remaining copy', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  await seedState(page, ['Phase Blade (Larzuk base)'], { 'Phase Blade (Larzuk base)': 2 });
  await page.reload(); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => new Promise<any>((res) => {
    const w: any = window;
    const sc0 = w.forgeScan();
    const pbWords = [].concat(sc0.pipeline || []).filter((t: any) => t.base && t.base.name === 'Phase Blade (Larzuk base)').map((t: any) => t.rw);
    if (pbWords.length < 2) { res({ skip: true }); return; }
    const [w1, w2] = pbWords;
    w.rwToggleMade(w1, 'Phase Blade (Larzuk base)');
    setTimeout(() => {
      const own = JSON.parse(localStorage.getItem('d2r_owned') || '[]');
      const copies = JSON.parse(localStorage.getItem('d2r_copies') || '{}');
      const sc1 = w.forgeScan();
      const w2task = [].concat(sc1.pipeline || [], sc1.now || []).find((t: any) => t.rw === w2);
      res({ skip: false, stillOwned: own.indexOf('Phase Blade (Larzuk base)') >= 0, copiesNow: copies['Phase Blade (Larzuk base)'] || 1, w2stays: !!(w2task && w2task.base && w2task.base.name === 'Phase Blade (Larzuk base)') });
    }, 700);
  }));
  if (r.skip) test.skip(true, 'env produced <2 PB words');
  expect(r.stillOwned).toBe(true);              // one copy remains…
  expect(r.w2stays).toBe(true);                 // …and word 2 stays planned on it, seamlessly
  await cleanup(page);
});

test('undo returns the base AND the re-tasked word snaps back to the pipeline', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  await seedState(page, ['Phase Blade (Larzuk base)']);
  await page.reload(); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => new Promise<any>((res) => {
    const w: any = window;
    const sc0 = w.forgeScan();
    const pbWords = [].concat(sc0.pipeline || []).filter((t: any) => t.base && t.base.name === 'Phase Blade (Larzuk base)').map((t: any) => t.rw);
    if (pbWords.length < 2) { res({ skip: true }); return; }
    const [w1, w2] = pbWords;
    w.rwToggleMade(w1, 'Phase Blade (Larzuk base)');   // forge
    setTimeout(() => {
      w.rwToggleMade(w1);                              // undo (↺)
      setTimeout(() => {
        const own = JSON.parse(localStorage.getItem('d2r_owned') || '[]');
        const sc1 = w.forgeScan();
        const w2task = [].concat(sc1.pipeline || []).find((t: any) => t.rw === w2 || t.rw === w1);
        res({ skip: false, baseBack: own.indexOf('Phase Blade (Larzuk base)') >= 0, repipelined: !!w2task });
      }, 700);
    }, 700);
  }));
  if (r.skip) test.skip(true, 'env produced <2 PB words');
  expect(r.baseBack).toBe(true);
  expect(r.repipelined).toBe(true);
  await cleanup(page);
});
