import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v75 — every Herald ladder tier (Fright → Dread → Fear → Horror → Terror) is now
// a clickable ID card routed through openDrop (same #item-detail panel as materials),
// searchable from the global box, and reachable from the RotW Herald ladder table.
// The main Herald card emblem renders the verified Bone Break charm art (👹 fallback).
test.describe('v75 Herald tiers are searchable + clickable ID cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  const TIERS = ['Herald of Fright', 'Herald of Dread', 'Herald of Fear', 'Herald of Horror', 'Herald of Terror'];

  async function search(page: any, q: string) {
    await page.fill('#gsearch-input', q);
    await page.waitForTimeout(220);
    return page.evaluate(() => [...document.querySelectorAll('#gsearch-results .gsearch-item')]
      .map((el) => ({
        lab: (el.querySelector('.gsearch-lab') as HTMLElement)?.textContent?.trim() || '',
        cat: (el.querySelector('.gsearch-cat') as HTMLElement)?.textContent?.trim() || '',
      })));
  }

  test('HERALD_TIERS is a global ladder of 5 tiers', async ({ page }) => {
    const r = await page.evaluate(() => {
      const m = (window as any).HERALD_TIERS;
      return { isArr: Array.isArray(m), len: m?.length, apex: m?.[4]?.n, apexFlag: m?.[4]?.apex };
    });
    expect(r.isArr).toBe(true);
    expect(r.len).toBe(5);
    expect(r.apex).toBe('Herald of Terror');
    expect(r.apexFlag).toBe(true);
  });

  test('each Herald tier is searchable', async ({ page }) => {
    for (const nm of TIERS) {
      const hits = await search(page, nm);
      // The apex (Herald of Terror) is searched via its dedicated RotW card command
      // (cat 'rotw'); the 4 lower rungs via the tier loop (cat 'herald').
      expect(hits.some((h) => h.lab.includes(nm) && /herald|rotw/i.test(h.cat))).toBe(true);
    }
  });

  test('only ONE Herald of Terror search result (no leaner duplicate)', async ({ page }) => {
    const hits = await search(page, 'Herald of Terror');
    // lab text = label + ' ' + sub; the apex label is the only one starting with
    // "Herald of Terror" (other rungs are Fright/Dread/Fear/Horror).
    const apex = hits.filter((h) => h.lab.startsWith('Herald of Terror'));
    expect(apex.length).toBe(1);
  });

  test('searching a tier and picking it opens its tier card', async ({ page }) => {
    await page.fill('#gsearch-input', 'Herald of Fear');
    await page.waitForTimeout(220);
    await page.locator('#gsearch-results .gsearch-item').first().click();
    await page.waitForTimeout(250);
    const r = await page.evaluate(() => {
      const panel = document.getElementById('item-detail');
      const card = panel?.querySelector('.herald-tier-card');
      return {
        shown: panel?.classList.contains('show'),
        name: card?.querySelector('.gic-name')?.textContent?.trim() || '',
        sunderChips: card?.querySelectorAll('.zd-item-click').length || 0,
      };
    });
    expect(r.shown).toBe(true);
    expect(r.name).toMatch(/Herald of Fear/);
    expect(r.name).toMatch(/tier 3/);
    expect(r.sunderChips).toBeGreaterThanOrEqual(6); // the 6 Latent Sunder Charm chips
  });

  test('openDrop(apex) routes to the RICH dedicated RotW card (not the lean tier card)', async ({ page }) => {
    await page.evaluate(() => (window as any).openDrop('Herald of Terror'));
    await page.waitForTimeout(400);
    const r = await page.evaluate(() => {
      const rotw = document.getElementById('tab-rotw');
      const card = document.getElementById('herald-card');
      const sec = card?.closest('.sec-body') as HTMLElement | null;
      // the lean tier card must NOT be what rendered for the apex anymore
      const leanShown = !!document.getElementById('item-detail')?.querySelector('.herald-tier-card');
      return {
        rotwActive: !!rotw?.classList.contains('active'),
        sectionOpen: !!sec && !sec.hasAttribute('hidden'),
        richName: card?.querySelector('.gbc-name')?.textContent?.trim() || '',
        leanShown,
      };
    });
    expect(r.rotwActive).toBe(true);
    expect(r.sectionOpen).toBe(true);
    expect(r.richName).toMatch(/Herald of Terror/);
    expect(r.leanShown).toBe(false);
  });

  test('a non-apex card names the next rung up', async ({ page }) => {
    await page.evaluate(() => (window as any).openDrop('Herald of Dread'));
    await page.waitForTimeout(250);
    const txt = await page.evaluate(() =>
      document.getElementById('item-detail')?.querySelector('.herald-tier-card')?.textContent || '');
    expect(txt).toMatch(/Herald of Fear/); // Dread → Fear is the next spawn
  });

  test('the RotW Herald ladder table rows are clickable → open tier cards', async ({ page }) => {
    await page.click('.tab[data-tab="rotw"]');
    await page.waitForTimeout(200);
    // expand the Herald section
    await page.evaluate(() => {
      const h = [...document.querySelectorAll('#tab-rotw .sec-h')]
        .find((e) => /Herald of Terror/.test(e.textContent || '')) as HTMLElement | undefined;
      if (h && h.classList.contains('collapsed')) h.click();
    });
    await page.waitForTimeout(200);
    const wired = await page.evaluate(() => {
      const rows = [...document.querySelectorAll('#herald-card .sunder-tbl .zd-item-click')]
        .filter((e) => /Herald of/.test(e.textContent || ''));
      return { count: rows.length, allWired: rows.every((r) => (r.getAttribute('onclick') || '').includes('openDrop(')) };
    });
    expect(wired.count).toBe(5);
    expect(wired.allWired).toBe(true);
  });

  test('Herald tier cards keep the 👹 monster glyph (not the charm graphic)', async ({ page }) => {
    await page.evaluate(() => (window as any).openDrop('Herald of Horror'));
    await page.waitForTimeout(250);
    const r = await page.evaluate(() => {
      const card = document.getElementById('item-detail')?.querySelector('.herald-tier-card');
      return {
        emoji: (card?.querySelector('.gic-header .gic-emoji')?.textContent || '').trim(),
        charmInHeader: !!card?.querySelector('.gic-header .d2art-img'),
      };
    });
    expect(r.emoji).toContain('👹');
    expect(r.charmInHeader).toBe(false);
  });

  test('no console errors opening Herald tier cards', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    for (const nm of TIERS) {
      await page.evaluate((n) => (window as any).openDrop(n), nm);
      await page.waitForTimeout(120);
    }
    expect(errors).toEqual([]);
  });
});
