import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v111 — Lister the Tormentor & Hephasto the Armorer each carry an emphasized
// "⚜️ Warlock Bind" callout on their super-unique ID card. Content is sourced from
// the bible's own verified-3.2 binds tab cross-checked against diablo2.io/aoeah/icy-veins:
//   · Lister = fixed Lvl 15 Meditation + 150% ED + 25% phys DR; the PROJECTED aura
//     rolls per spawn → reroll for Fanaticism, bind in a TZ (mlvl 96) for aura 12.
//   · Hephasto = always Aura-Enchanted, solo at the Hellforge → reroll for Fanaticism.
// The callout is data-driven (su.bind) so only the two fully-sourced bind targets show it.
test.describe('v111 Warlock bind callout on super-unique cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('exactly the three fully-sourced bind targets carry a su.bind block', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sus = (SUPER_UNIQUES as any[]);
      const withBind = sus.filter((s) => s.bind).map((s) => s.name);
      return { withBind };
    });
    expect(r.withBind.sort()).toEqual(['Hephasto the Armorer', 'Lister the Tormentor', 'The Smith']);
  });

  test('Lister card renders the OP bind callout with its verified roll detail', async ({ page }) => {
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('Lister the Tormentor'));
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const co = document.querySelector('.su-card-rich .su-bind-callout') as HTMLElement | null;
      return { has: !!co, txt: co?.textContent || '' };
    });
    expect(r.has).toBe(true);
    expect(r.txt).toContain('Warlock Bind');
    expect(r.txt).toContain('150% Enhanced Damage');
    expect(r.txt).toContain('25% Physical Damage Reduction');
    expect(r.txt).toContain('Meditation');
    expect(r.txt).toContain('Fanaticism');
    expect(r.txt).toContain('Terror Zone');
    expect(r.txt).toContain('20 hard points');
  });

  test('Hephasto card renders the Fanaticism-reroll bind callout', async ({ page }) => {
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('Hephasto the Armorer'));
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const co = document.querySelector('.su-card-rich .su-bind-callout') as HTMLElement | null;
      return { has: !!co, txt: co?.textContent || '' };
    });
    expect(r.has).toBe(true);
    expect(r.txt).toContain('Warlock Bind');
    expect(r.txt).toContain('Always Aura Enchanted');
    expect(r.txt).toContain('Fanaticism');
    expect(r.txt).toContain('solo');
    expect(r.txt).toContain('Fire Immune');
  });

  test('a non-bind super-unique (Shenk) shows no bind callout', async ({ page }) => {
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('Shenk the Overseer'));
    await page.waitForTimeout(300);
    const has = await page.evaluate(() => !!document.querySelector('.su-card-rich .su-bind-callout'));
    expect(has).toBe(false);
  });

  test('no console errors opening the bind cards', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('Lister the Tormentor'));
    await page.waitForTimeout(250);
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('Hephasto the Armorer'));
    await page.waitForTimeout(250);
    expect(errs).toEqual([]);
  });
});
