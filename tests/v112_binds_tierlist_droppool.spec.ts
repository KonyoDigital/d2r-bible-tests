import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v112 — three additive ships in the binds tab + super-unique cards:
//   1. "🏆 Best Warlock Binds — Tier List" card (#binds-tierlist): ranked best→budget,
//      with the three fully-sourced targets (Hephasto / Lister / The Smith) clickable
//      and routing to their super-unique ID cards, exactly like the rest of the site.
//   2. "⚜️ Aura Enchanted — exact aura levels & the Hell elite-affix pool" (#binds-elite):
//      sourced from maxroll's Elite Monster guide — per-aura level divisors (Fanaticism
//      ÷8 → cap 12) + the 13-affix Hell roll pool (random per spawn, 3 affixes in Hell).
//   3. Baal-card-parity DROP POOL grid wired onto Lister (Throne Wave 5 · TC87) and
//      Hephasto (terrored River of Flame · mlvl 96 / TC87) cards — every item routes to
//      its golden card via navigateToItem, reusing zoneHellGridHtml (zero fabricated odds).
test.describe('v112 binds tier-list + elite-affix + drop pools', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('tier-list card exists with 7 ranked rows and routable sourced targets', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sec = document.getElementById('binds-tierlist');
      const rows = sec ? sec.querySelectorAll('tbody tr') : [];
      const html = sec ? sec.innerHTML : '';
      return {
        has: !!sec,
        rowCount: rows.length,
        hephRoute: html.includes("jumpToSuperUniqueByName('Hephasto the Armorer')"),
        listRoute: html.includes("jumpToSuperUniqueByName('Lister the Tormentor')"),
        smithRoute: html.includes("jumpToSuperUniqueByName('The Smith')"),
        urdarRoute: html.includes("openBindSection('binds-unique')"),
      };
    });
    expect(r.has).toBe(true);
    expect(r.rowCount).toBe(7);
    expect(r.hephRoute).toBe(true);
    expect(r.listRoute).toBe(true);
    expect(r.smithRoute).toBe(true);
    expect(r.urdarRoute).toBe(true);
  });

  test('elite-affix section carries the per-aura level table + Mana Burn affix', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sec = document.getElementById('binds-elite');
      const txt = sec ? (sec.textContent || '') : '';
      return {
        has: !!sec,
        fana: txt.includes('Fanaticism') && txt.includes('mlvl ÷ 8'),
        freeze: txt.includes('mlvl ÷ 7'),
        manaBurn: txt.includes('Mana Burn'),
        random: /random per spawn/i.test(txt),
      };
    });
    expect(r.has).toBe(true);
    expect(r.fana).toBe(true);
    expect(r.freeze).toBe(true);
    expect(r.manaBurn).toBe(true);
    expect(r.random).toBe(true);
  });

  test('bind sources are consolidated in the reference tab, not on the bind cards', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ref = document.getElementById('tab-ref');
      const refTxt = ref ? (ref.textContent || '') : '';
      const tier = document.getElementById('binds-tierlist');
      const elite = document.getElementById('binds-elite');
      const tierTxt = tier ? (tier.textContent || '') : '';
      const eliteTxt = elite ? (elite.textContent || '') : '';
      return {
        refHasSources: /Warlock bind .* Aura Enchanted .* sources/i.test(refTxt) && refTxt.includes('Elite Monster') && refTxt.includes('Summoner Warlock'),
        cardsPointToRef: tierTxt.includes('reference tab') && eliteTxt.includes('reference tab'),
        cardsHaveNoSourceCitation: !/maxroll's Summoner-Warlock aura formula/i.test(tierTxt) && !/maxroll\.gg Elite Monster resource/i.test(eliteTxt),
      };
    });
    expect(r.refHasSources).toBe(true);
    expect(r.cardsPointToRef).toBe(true);
    expect(r.cardsHaveNoSourceCitation).toBe(true);
  });

  test('openBindSection helper exists and expands a collapsed tier section', async ({ page }) => {
    const ok = await page.evaluate(() => typeof (window as any).openBindSection === 'function');
    expect(ok).toBe(true);
    await page.evaluate(() => (window as any).openBindSection('binds-unique'));
    await page.waitForTimeout(150);
    const visible = await page.evaluate(() => {
      const s = document.getElementById('binds-unique');
      const b = s ? s.querySelector('.sec-body') : null;
      return b ? !b.hasAttribute('hidden') : false;
    });
    expect(visible).toBe(true);
  });

  test('the three fully-sourced bind targets carry a su.pool drop-pool descriptor', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sus = (SUPER_UNIQUES as any[]);
      return sus.filter((s) => s.pool).map((s) => s.name).sort();
    });
    expect(r).toEqual(['Hephasto the Armorer', 'Lister the Tormentor', 'The Smith']);
  });

  test('Lister card renders a clickable Baal-parity drop-pool grid (TC87)', async ({ page }) => {
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('Lister the Tormentor'));
    await page.waitForTimeout(350);
    const r = await page.evaluate(() => {
      const card = document.querySelector('.su-card-rich');
      const intro = card ? card.querySelector('.su-pool-intro') : null;
      const grid = card ? card.querySelector('.zd-hell-grid') : null;
      const rows = grid ? grid.querySelectorAll('.zd-hg-row') : [];
      const firstRowOnclick = rows.length ? (rows[0].getAttribute('onclick') || '') : '';
      return {
        hasIntro: !!intro,
        introTxt: intro ? (intro.textContent || '') : '',
        hasGrid: !!grid,
        rowCount: rows.length,
        routes: firstRowOnclick.includes('navigateToItem'),
      };
    });
    expect(r.hasIntro).toBe(true);
    expect(r.introTxt).toContain('Throne of Destruction');
    expect(r.introTxt).toContain('TC87');
    expect(r.hasGrid).toBe(true);
    expect(r.rowCount).toBeGreaterThan(5);
    expect(r.routes).toBe(true);
  });

  test('Hephasto card renders a drop-pool grid sourced to the River of Flame', async ({ page }) => {
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('Hephasto the Armorer'));
    await page.waitForTimeout(350);
    const r = await page.evaluate(() => {
      const card = document.querySelector('.su-card-rich');
      const intro = card ? card.querySelector('.su-pool-intro') : null;
      const grid = card ? card.querySelector('.zd-hell-grid') : null;
      return { hasIntro: !!intro, introTxt: intro ? (intro.textContent || '') : '', hasGrid: !!grid };
    });
    expect(r.hasIntro).toBe(true);
    expect(r.introTxt).toContain('River of Flame');
    expect(r.hasGrid).toBe(true);
  });

  test('a non-pool super-unique (Shenk) shows no drop-pool intro', async ({ page }) => {
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('Shenk the Overseer'));
    await page.waitForTimeout(300);
    const has = await page.evaluate(() => !!document.querySelector('.su-card-rich .su-pool-intro'));
    expect(has).toBe(false);
  });

  test('no console errors opening the new binds card + pool cards', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('Lister the Tormentor'));
    await page.waitForTimeout(250);
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('Hephasto the Armorer'));
    await page.waitForTimeout(250);
    expect(errs).toEqual([]);
  });
});
