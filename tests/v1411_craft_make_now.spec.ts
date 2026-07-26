import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1411 — ready crafts must land as Make-now tasks (cards), even when the runeword
// chronicle is sealed (the "stuck on Completed" regression).

test('sealed chronicle + gems/runes → crafts on Make now as atomic tasks', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_gemStash', JSON.stringify({
      'Perfect Amethyst': 3,
      'Perfect Ruby': 2,
    }));
    localStorage.setItem('d2r_runeStash', JSON.stringify({
      Ral: 2, Amn: 2, Sol: 1, Nef: 1, Ort: 1, Ith: 1, Tal: 1, Eth: 1, Tir: 1, Thul: 1,
    }));
    localStorage.setItem('d2r_rwProfile', 'fresh');
  });
  await page.goto(URL);
  await page.waitForTimeout(1800);

  const r = await page.evaluate(() => {
    const w: any = window;
    try {
      const tip = w.RUNEWORD_TIP || {};
      const made: any = {};
      Object.keys(tip).forEach((n) => { made[n] = '2026-07-26'; });
      (w.LSR || localStorage).setItem('d2r_rwMade', JSON.stringify(made));
      if (w.rwMade) Object.keys(tip).forEach((n) => { w.rwMade[n] = '2026-07-26'; });
    } catch (e) {}
    // simulate the stuck filter the regression left users on
    try { (w as any)._forgeFilter = 'completed'; } catch (e) {}
    try { w.switchTab && w.switchTab('forge'); } catch (e) {}
    try { w.renderForge && w.renderForge(); } catch (e) {}
    const s = w.forgeScan();
    const body = document.getElementById('forge-body');
    const html = body ? body.innerHTML : '';
    const nowSec = document.querySelector('#forge-body .forge-sec-now');
    const craftCards = document.querySelectorAll('#forge-body .forge-sec-now .f-card.f-craft');
    const craftBtns = document.querySelectorAll('#forge-body .forge-sec-now .f-btn-go');
    const nowPill = document.querySelector('#forge-body .forge-tab.ft-now');
    let fs: any = null;
    try { fs = JSON.parse(localStorage.getItem('d2r_forgeSummary') || 'null'); } catch (e) {}
    let cr: any = null;
    try { cr = JSON.parse(localStorage.getItem('d2r_craftReady') || 'null'); } catch (e) {}
    return {
      craftN: (s.crafts || []).length,
      hasNowSec: !!nowSec,
      craftCards: craftCards.length,
      craftBtns: craftBtns.length,
      nowPillOn: nowPill ? nowPill.classList.contains('on') : false,
      htmlHasCraftAct: /Craft <b|f-craft|⚗️/.test(html),
      summaryNow: (fs && fs.now) || [],
      summaryCrafts: (fs && fs.crafts) || [],
      craftReadyNow: (cr && cr.now) || [],
      gem: typeof w._gemCount === 'function' ? w._gemCount('Perfect Amethyst') : 0,
      ral: typeof w._runeCount === 'function' ? w._runeCount('Ral') : 0,
    };
  });

  expect(r.gem).toBeGreaterThanOrEqual(1);
  expect(r.ral).toBeGreaterThanOrEqual(1);
  expect(r.craftN).toBeGreaterThan(0);
  expect(r.hasNowSec).toBe(true);
  expect(r.craftCards).toBeGreaterThan(0);
  expect(r.nowPillOn).toBe(true); // auto-routed off Completed onto Make now
  expect(r.htmlHasCraftAct).toBe(true);
  // Sessions bridge: crafts appear in forgeSummary.now and/or crafts
  const nowHasCraft = (r.summaryNow || []).some((x: any) => String(x).indexOf('⚗️') >= 0 || /Caster|Blood|Safety|Hit Power/i.test(String(x)));
  const hasCraftList = (r.summaryCrafts || []).length > 0 || (r.craftReadyNow || []).length > 0;
  expect(nowHasCraft || hasCraftList).toBe(true);
});

test('Perfect Amethyst + Ral still scan as Caster Amulet ready', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_gemStash', JSON.stringify({ 'Perfect Amethyst': 1 }));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 1 }));
  });
  await page.goto(URL);
  await page.waitForTimeout(1600);
  const c = await page.evaluate(() => {
    const s = (window as any).forgeScan();
    return (s.crafts || []).find((x: any) => x.craft === 'Caster' && x.slot === 'Amulet');
  });
  expect(c).toBeTruthy();
  expect(c.gem).toBe('Perfect Amethyst');
  expect(c.rune).toBe('Ral');
});
