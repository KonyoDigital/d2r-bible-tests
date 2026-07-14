import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v60 — "Most Wanted" community/forum trade-demand board. A SEPARATE layer from the
// Holy Grail rarity tables: the grail ranks by GAME rarity (how hard to find), this
// ranks by COMMUNITY DEMAND / trade value (what's worth chasing & holding) — they
// diverge. Demand tiers are an editorial community-consensus call (diablo.io-style,
// ROTW-aware), explicitly NOT a drop rate. Global Top 10 + #1 most-wanted per
// act/section. Every entry routes to a real card via the unified openDrop()
// (rune/material/item); runewords expand to clickable rune chips. No grail data touched.
test.describe('v60 Most Wanted community-demand board', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    // v693.2 recalibration — v687 made ⚡session the HOME tab; the MW board lives on MAIN,
    // so navigate there first (the old boot tab WAS main).
    await page.evaluate(() => (window as any).switchTab('main'));
    await page.waitForTimeout(400);
    // v63: dropdown sections now default to COLLAPSED site-wide. The Most Wanted
    // board lives inside one, so expand it before any real-UI click/focus test.
    await page.evaluate(() => {
      const h = document.querySelector('#most-wanted .sec-h') as HTMLElement | null;
      const b = h && (h.nextElementSibling as HTMLElement | null);
      if (h && b && b.hasAttribute('hidden')) h.click();
    });
  });

  test('board mounts on the home tab: Top 10 + 7 per-act/section cards, no undefined', async ({ page }) => {
    const r = await page.evaluate(() => {
      const host = document.getElementById('most-wanted');
      return {
        hasHost: !!host,
        // v61: the non-boss home sections were split out of the bosses tab into a new
        // default-active Main tab; Most Wanted now lives under #tab-main.
        onMainTab: !!document.querySelector('#tab-main #most-wanted'),
        rows: document.querySelectorAll('#most-wanted .mw-row').length,
        sections: document.querySelectorAll('#most-wanted .mw-sec').length,
        wants: document.querySelectorAll('#most-wanted .mw-want-chip').length,
        hasTitle: /Most Wanted/.test(host?.innerHTML || ''),
        // honesty: must declare itself NOT a drop rate + separate from the grail
        disclaimsRate: /NOT a drop rate/i.test(host?.innerHTML || ''),
        separateFromGrail: /separate layer/i.test(host?.innerHTML || ''),
        noUndef: !/undefined/.test(host?.innerHTML || 'undefined'),
        // it must NOT have clobbered the grail Top-Drops layer (those live in boss cards)
        topDropsStillExists: typeof (window as any).navigateToItem === 'function',
      };
    });
    expect(r.hasHost).toBe(true);
    expect(r.onMainTab).toBe(true);
    expect(r.rows).toBe(10);
    expect(r.sections).toBe(7);
    expect(r.wants).toBeGreaterThanOrEqual(14);
    expect(r.hasTitle).toBe(true);
    expect(r.disclaimsRate).toBe(true);
    expect(r.separateFromGrail).toBe(true);
    expect(r.noUndef).toBe(true);
    expect(r.topDropsStillExists).toBe(true);
  });

  test('every Top-10 + section target resolves to a real card (no dead clicks)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const fr = (window as any).findRune, fm = (window as any).findMaterial;
      // ITEMS / SPECIAL_DROPS are top-level consts (page scope) — reference bare.
      // v228: openDrop ALSO resolves SPECIAL_DROPS group LABELS (e.g. 'Sunder
      // Charms' → the golden 6-charm card), so the resolver must know them too.
      const groupLabel = (n: string) => {
        try { return Object.values(SPECIAL_DROPS as any).some((g: any) => g && g.label === n); }
        catch (e) { return false; }
      };
      const resolves = (n: string) => !!(fm && fm(n)) || !!(fr && fr(n)) ||
        (ITEMS as any).some((i: any) => i.n === n) || groupLabel(n);
      const dead: string[] = [];
      // MW_TOP10 / MW_SECTIONS are top-level consts (page scope), referenced bare
      (MW_TOP10 as any).forEach((e: any) => {
        if (e.drop && !resolves(e.drop)) dead.push('top-drop:' + e.drop);
        if (e.rw) e.rw.forEach((rune: string) => { if (!resolves(rune)) dead.push('rune:' + rune); });
      });
      (MW_SECTIONS as any).forEach((s: any) => {
        s.wants.forEach((w: any) => { if (w.drop && !resolves(w.drop)) dead.push('want:' + w.drop); });
      });
      return { dead, tabs: (MW_TOP10 as any).filter((e: any) => e.tab).length };
    });
    expect(r.dead).toEqual([]);
  });

  test('clicking a rune row (#2 Ber) opens the rune card', async ({ page }) => {
    await page.locator('#most-wanted .mw-row[data-mw="1"]').click();
    await page.waitForTimeout(300);
    const card = page.locator('#item-detail .rune-card');
    await expect(card).toBeVisible();
    await expect(card.locator('.gic-name')).toContainText('Ber Rune');
    expect(await page.evaluate(() => (window as any).__activeRune)).toBe('Ber');
  });

  test('clicking a material row (Hellfire Torch) opens the material card', async ({ page }) => {
    // #7 (index 6) = Hellfire Torch
    await page.locator('#most-wanted .mw-row[data-mw="6"]').click();
    await page.waitForTimeout(300);
    const card = page.locator('#item-detail .material-card');
    await expect(card).toBeVisible();
    await expect(card).toContainText('Hellfire Torch');
    await expect(card).not.toContainText('undefined');
  });

  test('a runeword row (#1 Enigma) expands to clickable rune chips; chip opens that rune', async ({ page }) => {
    const row = page.locator('#most-wanted .mw-row[data-mw="0"]');
    await expect(row).not.toHaveClass(/open/);
    await row.click();
    await page.waitForTimeout(150);
    await expect(row).toHaveClass(/open/);
    // Enigma = Jah · Ith · Ber → 3 clickable chips
    const chips = row.locator('.mw-rune-chip');
    await expect(chips).toHaveCount(3);
    await chips.filter({ hasText: 'Jah' }).first().click();
    await page.waitForTimeout(300);
    await expect(page.locator('#item-detail .rune-card .gic-name')).toContainText('Jah Rune');
  });

  test('section header routes to its boss (Act 3 → Mephisto detail)', async ({ page }) => {
    const meph = page.locator('#most-wanted .mw-sec', { hasText: 'Mephisto' });
    await meph.locator('.mw-sec-head').click();
    await page.waitForTimeout(450);
    const r = await page.evaluate(() => ({
      bossesActive: !!document.querySelector('.tab[data-tab="bosses"].active'),
      detailOpen: !document.getElementById('boss-detail-overlay')?.classList.contains('hidden'),
      detailText: document.getElementById('boss-detail-panel')?.textContent || '',
    }));
    expect(r.bossesActive).toBe(true);
    expect(r.detailOpen).toBe(true);
    expect(/Mephisto/i.test(r.detailText)).toBe(true);
  });

  test('section want-chip opens its item card (Act 5 → Griffon\'s Eye)', async ({ page }) => {
    const act5 = page.locator('#most-wanted .mw-sec', { hasText: 'Pindleskin' });
    await act5.locator('.mw-want-chip', { hasText: "Griffon's Eye" }).click();
    await page.waitForTimeout(400);
    const aid = page.locator('#item-detail .aid-card');
    await expect(aid).toBeVisible();
    await expect(aid).toContainText("Griffon's Eye");
  });

  test('#9 Sunder Charms opens the golden 6-charm card (v228 routing)', async ({ page }) => {
    await page.locator('#most-wanted .mw-row[data-mw="8"]').click();
    await page.waitForTimeout(300);
    const six = ['Bone Break', 'Black Cleft', 'Crack of the Heavens', 'Cold Rupture', 'Flame Rift', 'Rotting Fissure'];
    const txt = await page.evaluate(() => document.getElementById('item-detail')?.textContent || '');
    for (const c of six) expect(txt, `missing charm: ${c}`).toContain(c);
  });

  test('keyboard: Enter on a focused row activates it (a11y role=button)', async ({ page }) => {
    await page.locator('#most-wanted .mw-row[data-mw="2"]').focus();
    await page.keyboard.press('Enter');
    await page.waitForTimeout(300);
    await expect(page.locator('#item-detail .rune-card .gic-name')).toContainText('Jah Rune');
  });

  test('ROTW entries are badged; demand tiers render (S/A), not drop odds', async ({ page }) => {
    const r = await page.evaluate(() => {
      const host = document.getElementById('most-wanted')!;
      return {
        rotwBadges: host.querySelectorAll('.mw-rotw-badge').length,
        sTiers: host.querySelectorAll('.mw-tier-S').length,
        aTiers: host.querySelectorAll('.mw-tier-A').length,
        // the board must NOT print "1:" drop-odds (that's the grail's job)
        noOdds: !/1:\d/.test(host.innerHTML),
      };
    });
    expect(r.rotwBadges).toBeGreaterThanOrEqual(2);
    expect(r.sTiers).toBeGreaterThan(0);
    expect(r.aTiers).toBeGreaterThan(0);
    expect(r.noOdds).toBe(true);
  });

  test('no console errors across the Most-Wanted flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push('PAGEERR: ' + e.message));
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => {
      (window as any).renderMostWanted();
      (window as any).mwToggleRw(0);
      (window as any).mwOpen('Ber');
      (window as any).mwOpen('Colossal Ancient Jewels');
      (window as any).mwOpen(null, 'rotw');
      (window as any).mwSection('mephisto');
    });
    await page.waitForTimeout(250);
    expect(errors).toEqual([]);
  });
});
