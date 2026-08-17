// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v126 — (a) the two aggregate pinnacle-chain tokens "Colossal Summit" and
// "Colossal Ancients" now route to their own golden enriched ID cards via openDrop
// (colossalSummitDetailHtml / colossalAncientsDetailHtml), zero fabrication, verified
// off the RotW chain. (b) The #binds-bestroll best-roll section keeps its 3-row top-3
// podium (unchanged) and gains an expandable <details class="baf-all"> listing the FULL
// Arreat Summit super-unique boss-modifier pool ranked S→D for an Echoing Strike bind.
test.describe('v126 colossal chain cards + full bind-affix pool', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('Colossal Summit routes to its own golden summit card', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openDrop('Colossal Summit');
      const card = document.querySelector('#item-detail .colossal-summit-card');
      const name = (card?.querySelector('.gic-name')?.textContent || '').trim();
      const txt = card?.textContent || '';
      return {
        present: !!card,
        name,
        mentionsStatues: txt.includes('5 Colossal Statues') || txt.includes('5 statues'),
        routesAncients: !!card?.querySelector("[onclick*=\"openDrop('Colossal Ancients')\"]"),
        routesJewel: !!card?.querySelector("[onclick*=\"openDrop('Colossal Ancient Jewels')\"]"),
      };
    });
    expect(r.present).toBe(true);
    expect(r.name).toContain('Colossal Summit');
    expect(r.mentionsStatues).toBe(true);
    expect(r.routesAncients).toBe(true);
    expect(r.routesJewel).toBe(true);
  });

  test('Colossal Ancients routes to its own golden pinnacle card', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openDrop('Colossal Ancients');
      const card = document.querySelector('#item-detail .colossal-ancients-card');
      const txt = card?.textContent || '';
      return {
        present: !!card,
        name: (card?.querySelector('.gic-name')?.textContent || '').trim(),
        talic: !!card?.querySelector("[onclick*=\"jumpToUberBoss('talic')\"]"),
        korlic: !!card?.querySelector("[onclick*=\"jumpToUberBoss('korlic')\"]"),
        madawc: !!card?.querySelector("[onclick*=\"jumpToUberBoss('madawc')\"]"),
        randomImm: txt.includes('random immunity'),
        lastKill: /matching the Ancient you kill/i.test(txt),
        routesSummit: !!card?.querySelector("[onclick*=\"openDrop('Colossal Summit')\"]"),
      };
    });
    expect(r.present).toBe(true);
    expect(r.name).toContain('Colossal Ancients');
    expect(r.talic).toBe(true);
    expect(r.korlic).toBe(true);
    expect(r.madawc).toBe(true);
    expect(r.randomImm).toBe(true);
    expect(r.lastKill).toBe(true);
    expect(r.routesSummit).toBe(true);
  });

  test('the prose Colossal Summit / Colossal Ancients mentions are clickable', async ({ page }) => {
    const r = await page.evaluate(() => {
      const summit = Array.from(document.querySelectorAll("[onclick*=\"openDrop('Colossal Summit')\"]")).length;
      const ancients = Array.from(document.querySelectorAll("[onclick*=\"openDrop('Colossal Ancients')\"]")).length;
      return { summit, ancients };
    });
    // at least the statue-section prose + the showcase lead
    expect(r.summit).toBeGreaterThan(1);
    expect(r.ancients).toBeGreaterThan(1);
  });

  test('top-3 podium is unchanged (still exactly 3 rows, Extra Strong #1/S)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const pod = document.querySelector('#binds-bestroll .aura-top3');
      const rows = pod ? Array.from(pod.querySelectorAll('.at3-row')) : [];
      return {
        count: rows.length,
        names: rows.map((x) => (x.querySelector('.at3-name')?.textContent || '').trim()),
        firstTier: (rows[0]?.querySelector('.at3-tier')?.textContent || '').trim(),
      };
    });
    expect(r.count).toBe(3);
    expect(r.names).toEqual(['Extra Strong', 'Cursed', 'Extra Fast']);
    expect(r.firstTier).toBe('S');
  });

  test('the expandable full affix pool lists all 12 ranked modifiers', async ({ page }) => {
    const r = await page.evaluate(() => {
      const det = document.querySelector('#binds-bestroll details.baf-all');
      const pod = det?.querySelector('.aura-top3');
      const rows = pod ? Array.from(pod.querySelectorAll('.at3-row')) : [];
      const names = rows.map((x) => (x.querySelector('.at3-name')?.textContent || '').trim());
      const tiers = rows.map((x) => (x.querySelector('.at3-tier')?.textContent || '').trim());
      return {
        present: !!det,
        summary: (det?.querySelector('summary')?.textContent || '').toLowerCase(),
        count: rows.length,
        names,
        tiers,
        hasExtraStrong: names.includes('Extra Strong'),
        hasAura: names.some((n) => n.includes('Aura Enchanted')),
        hasReroll: names.some((n) => n.includes('Mana Burn')),
        firstTier: tiers[0],
        lastTier: tiers[tiers.length - 1],
      };
    });
    expect(r.present).toBe(true);
    expect(r.summary).toContain('full bind-affix pool');
    expect(r.count).toBe(12);
    expect(r.hasExtraStrong).toBe(true);
    expect(r.hasAura).toBe(true);
    expect(r.hasReroll).toBe(true);
    expect(r.firstTier).toBe('S');
    expect(r.lastTier).toBe('D');
  });

  test('no console errors opening both colossal chain cards', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate(() => (window as any).openDrop('Colossal Summit'));
    await page.waitForTimeout(60);
    await page.evaluate(() => (window as any).openDrop('Colossal Ancients'));
    await page.waitForTimeout(60);
    expect(errs).toEqual([]);
  });
});
