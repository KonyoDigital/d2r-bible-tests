import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// Nightly bridge B1 — additive Mercenary reference section in the 📐 reference tab.
// maxroll-sourced vanilla mechanics (4 hirelings, the Act 2 aura-by-difficulty table,
// the revive-cost formula, best merc gear, ethereal-on-merc), with an explicit RotW
// caveat. Additive only — nothing on the tab was removed.
test.describe('v114 mercenary reference (nightly B1)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
  });

  test('the reference tab gains a Mercenary mechanics section (additive, collapsible)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ref = document.getElementById('tab-ref');
      const headers = ref ? Array.from(ref.querySelectorAll('h2.sec-h')).map((h) => h.textContent || '') : [];
      const mercH = headers.find((t) => /Mercenary mechanics/i.test(t));
      // it must NOT have replaced the existing cube / MF sections (nothing cut)
      const hasCube = headers.some((t) => /Cube Recipes/i.test(t));
      const hasMF = headers.some((t) => /MF math/i.test(t));
      return { hasMerc: !!mercH, hasCube, hasMF, count: headers.length };
    });
    expect(r.hasMerc).toBe(true);
    expect(r.hasCube).toBe(true);
    expect(r.hasMF).toBe(true);
  });

  test('the Act 2 aura table is correct (Nightmare = Holy Freeze / Might) and flags hire-in-NM', async ({ page }) => {
    // expand every ref-tab section, then read the merc text
    await page.evaluate(() => {
      document.querySelectorAll('#tab-ref h2.sec-h').forEach((h) => {
        if (/Mercenary mechanics/i.test(h.textContent || '')) (window as any).toggleSec(h);
      });
    });
    await page.waitForTimeout(150);
    const txt = await page.evaluate(() => {
      const ref = document.getElementById('tab-ref');
      const heads = ref ? Array.from(ref.querySelectorAll('h2.sec-h')) : [];
      const mercH = heads.find((h) => /Mercenary mechanics/i.test(h.textContent || ''));
      const body = mercH ? (mercH.nextElementSibling as HTMLElement) : null;
      return body ? (body.textContent || '') : '';
    });
    // canonical aura facts
    expect(txt).toContain('Holy Freeze');
    expect(txt).toContain('Might');
    expect(txt).toContain('Defiance');
    expect(txt).toContain('Blessed Aim');
    expect(txt).toContain('Prayer');
    expect(txt).toContain('Thorns');
    expect(txt).toMatch(/hire.*Act 2.*NIGHTMARE/i);
    // revive formula + cap
    expect(txt).toContain('50,000');
    expect(txt).toMatch(/hlvl/);
    // best gear anchors
    expect(txt).toContain('Infinity');
    expect(txt).toContain('Insight');
    expect(txt).toContain('Fortitude');
    expect(txt).toContain("Andariel's Visage");
    expect(txt).toMatch(/ETHEREAL/i);
    // RotW guard-rail present
    expect(txt).toMatch(/Reign of the Warlock|RotW/i);
    // Konyo Warlock cross-reference to the Meditation bind
    expect(txt).toContain('Meditation');
  });

  test('the four hireling acts are all listed', async ({ page }) => {
    await page.evaluate(() => {
      document.querySelectorAll('#tab-ref h2.sec-h').forEach((h) => {
        if (/Mercenary mechanics/i.test(h.textContent || '')) (window as any).toggleSec(h);
      });
    });
    await page.waitForTimeout(150);
    const txt = await page.evaluate(() => {
      const heads = Array.from(document.querySelectorAll('#tab-ref h2.sec-h'));
      const mercH = heads.find((h) => /Mercenary mechanics/i.test(h.textContent || ''));
      const body = mercH ? (mercH.nextElementSibling as HTMLElement) : null;
      return body ? (body.textContent || '') : '';
    });
    expect(txt).toContain('Rogue Scout');
    expect(txt).toContain('Desert Mercenary');
    expect(txt).toContain('Ironwolf');
    expect(txt).toContain('Barbarian');
  });

  test('no console errors when activating the reference tab + expanding the merc section', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate(() => (window as any).switchTab('ref'));
    await page.waitForTimeout(150);
    await page.evaluate(() => {
      document.querySelectorAll('#tab-ref h2.sec-h').forEach((h) => {
        if (/Mercenary mechanics/i.test(h.textContent || '')) (window as any).toggleSec(h);
      });
    });
    await page.waitForTimeout(150);
    expect(errs).toEqual([]);
  });
});
