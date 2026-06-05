import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v81 — the Colossal pinnacle ID-card pass. Each of the 6 named Ancient Jewels
// and 5 named Statues is now its own calculator-style ID card routed through
// openDrop (rendered into #item-detail, same panel as materials/runes), globally
// searchable, and reachable from every place its name renders:
//   • the 3 Colossal Ancient uber-boss drop-rows (Talic/Korlic/Madawc → 2 jewels)
//   • the aggregate Colossal Statue card's DROPS-FROM rows
//   • the statue tracker rows
//   • the event-colossal-ancients jewel table
//   • a dedicated glowing Colossal Endgame showcase section under Events.
// The aggregate "Colossal Ancient Jewels" / "Colossal Ancient Statue" material
// cards stay intact (the named cards are additive, not a replacement).
test.describe('v81 Colossal jewels + statues are searchable + clickable ID cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  const JEWELS = ["Defender's Bile", "Guardian's Thunder", "Protector's Frost", "Defender's Fire", "Protector's Stone", "Guardian's Light"];
  const STATUES = ["Talic's Anguish", "Korlic's Pain", "Madawc's Ire", "Bul-Kathos' Nightmare", "Worusk's End"];

  // Apostrophe-aware: onclick attrs escape ' as \' (e.g. openDrop('Defender\'s Bile')).
  // Capture everything between openDrop(' and ') allowing escaped quotes, then unescape.
  const dropName = (oc: string): string | undefined => {
    const m = oc.match(/openDrop\('((?:\\.|[^'])*)'\)/);
    return m ? m[1].replace(/\\'/g, "'") : undefined;
  };

  test('the COLOSSAL data modules are exposed and complete', async ({ page }) => {
    const r = await page.evaluate(() => {
      const J = (window as any).COLOSSAL_JEWELS;
      const S = (window as any).COLOSSAL_STATUES;
      return {
        jLen: J?.length, sLen: S?.length,
        jNames: J?.map((x: any) => x.n),
        sNames: S?.map((x: any) => x.n),
        fns: ['findColossalJewel', 'findColossalStatue', 'colossalJewelDetailHtml', 'colossalStatueDetailHtml', 'renderColossalShowcase'].map((f) => typeof (window as any)[f]),
      };
    });
    expect(r.jLen).toBe(6);
    expect(r.sLen).toBe(5);
    expect(r.jNames).toEqual(JEWELS);
    expect(r.sNames).toEqual(STATUES);
    expect(r.fns.every((t) => t === 'function')).toBe(true);
  });

  test('openDrop on each jewel renders its dedicated jewel ID card (not a material card)', async ({ page }) => {
    for (const nm of JEWELS) {
      const r = await page.evaluate((n) => {
        (window as any).openDrop(n);
        const panel = document.getElementById('item-detail');
        const card = panel?.querySelector('.colossal-jewel-card');
        return {
          shown: panel?.classList.contains('show'),
          isJewelCard: !!card,
          name: (card?.querySelector('.gic-name')?.textContent || '').trim(),
          hasSister: !!card && /the other jewel/i.test(card.textContent || ''),
          calcActive: document.getElementById('tab-calc')?.classList.contains('active'),
        };
      }, nm);
      expect(r.shown).toBe(true);
      expect(r.isJewelCard).toBe(true);
      expect(r.name).toContain(nm);
      expect(r.hasSister).toBe(true);
      expect(r.calcActive).toBe(true);
    }
  });

  test('openDrop on each statue renders its dedicated statue ID card', async ({ page }) => {
    for (const nm of STATUES) {
      const r = await page.evaluate((n) => {
        (window as any).openDrop(n);
        const card = document.getElementById('item-detail')?.querySelector('.colossal-statue-card');
        return {
          isStatueCard: !!card,
          name: (card?.querySelector('.gic-name')?.textContent || '').trim(),
          hasBossLink: !!card?.querySelector('[onclick*="openBossDetail"]'),
        };
      }, nm);
      expect(r.isStatueCard).toBe(true);
      expect(r.name).toContain(nm);
      expect(r.hasBossLink).toBe(true);
    }
  });

  test('aggregate material cards still resolve (named cards are additive)', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openDrop('Colossal Ancient Jewels');
      const jewelAgg = document.getElementById('item-detail')?.querySelector('.material-card:not(.colossal-jewel-card):not(.colossal-statue-card)');
      const jewelAggName = (jewelAgg?.querySelector('.gic-name')?.textContent || '').trim();
      (window as any).openDrop('Colossal Ancient Statue');
      const statueAgg = document.getElementById('item-detail')?.querySelector('.material-card:not(.colossal-jewel-card):not(.colossal-statue-card)');
      const statueAggName = (statueAgg?.querySelector('.gic-name')?.textContent || '').trim();
      return { jewelAggName, statueAggName };
    });
    expect(r.jewelAggName).toContain('Colossal Ancient Jewels');
    expect(r.statueAggName).toContain('Colossal Ancient Statue');
  });

  test('every jewel + statue is globally searchable and routes to its own card', async ({ page }) => {
    for (const nm of [...JEWELS, ...STATUES]) {
      await page.fill('#gsearch-input', nm);
      await page.waitForTimeout(200);
      const hits = await page.evaluate(() => [...document.querySelectorAll('#gsearch-results .gsearch-item')]
        .map((el) => ({
          lab: (el.querySelector('.gsearch-lab') as HTMLElement)?.textContent?.trim() || '',
          cat: (el.querySelector('.gsearch-cat') as HTMLElement)?.textContent?.trim() || '',
        })));
      expect(hits.some((h) => h.lab.startsWith(nm) && /colossal/i.test(h.cat))).toBe(true);
    }
  });

  test('the 3 Colossal Ancients each drop-row links to their 2 specific jewels', async ({ page }) => {
    const raw = await page.evaluate(() => {
      (window as any).renderUberBossCards();
      const pairs: Record<string, string[]> = {};
      ['talic', 'korlic', 'madawc'].forEach((id) => {
        const card = document.getElementById('uberboss-' + id);
        pairs[id] = [...(card?.querySelectorAll('.ubc-drop [onclick*="openDrop"]') || [])]
          .map((e) => e.getAttribute('onclick') || '');
      });
      return pairs;
    });
    const jewelsOf = (arr: string[]) => arr.map(dropName)
      .filter((n): n is string => !!n && /^(Defender|Guardian|Protector)/.test(n));
    expect(jewelsOf(raw.talic).sort()).toEqual(["Defender's Bile", "Defender's Fire"].sort());
    expect(jewelsOf(raw.korlic).sort()).toEqual(["Protector's Frost", "Protector's Stone"].sort());
    expect(jewelsOf(raw.madawc).sort()).toEqual(["Guardian's Light", "Guardian's Thunder"].sort());
  });

  test('the aggregate statue card DROPS-FROM rows link to the 5 named statue cards', async ({ page }) => {
    const raw = await page.evaluate(() => {
      (window as any).openDrop('Colossal Ancient Statue');
      const card = document.getElementById('item-detail')?.querySelector('.material-card');
      return [...(card?.querySelectorAll('[onclick*="openDrop"]') || [])]
        .map((e) => e.getAttribute('onclick') || '');
    });
    const links = raw.map(dropName).filter(Boolean) as string[];
    for (const s of STATUES) expect(links).toContain(s);
  });

  test('the statue tracker rows route to each named statue card without toggling collect', async ({ page }) => {
    await page.click('.tab[data-tab="rotw"]');
    await page.waitForTimeout(150);
    const r = await page.evaluate(() => {
      const names = [...document.querySelectorAll('#statue-tracker .statue-card-name')];
      return {
        count: names.length,
        allWired: names.every((n) => /openDrop\(/.test(n.getAttribute('onclick') || '')),
        allStop: names.every((n) => /stopPropagation/.test(n.getAttribute('onclick') || '')),
      };
    });
    expect(r.count).toBe(5);
    expect(r.allWired).toBe(true);
    expect(r.allStop).toBe(true);
  });

  test('the glowing Colossal showcase section renders 11 clickable .endgame-relic tiles', async ({ page }) => {
    await page.click('.tab[data-tab="ancients"]');
    await page.waitForTimeout(150);
    const r = await page.evaluate(() => {
      const tiles = [...document.querySelectorAll('#colossal-showcase .colossal-tile')];
      return {
        count: tiles.length,
        allGlow: tiles.every((t) => t.classList.contains('endgame-relic')),
        allRouted: tiles.every((t) => /openDrop\(/.test(t.getAttribute('onclick') || '')),
        hasArt: tiles.every((t) => !!t.querySelector('.ct-art')),
      };
    });
    expect(r.count).toBe(11);
    expect(r.allGlow).toBe(true);
    expect(r.allRouted).toBe(true);
    expect(r.hasArt).toBe(true);
  });

  test('the event-colossal-ancients jewel table names are clickable to their cards', async ({ page }) => {
    const raw = await page.evaluate(() =>
      [...document.querySelectorAll('#event-colossal-ancients [onclick*="openDrop"]')]
        .map((e) => e.getAttribute('onclick') || ''));
    const links = raw.map(dropName).filter(Boolean) as string[];
    for (const j of JEWELS) expect(links).toContain(j);
  });

  test('no console errors opening every colossal card + showcase + tabs', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="ancients"]');
    await page.waitForTimeout(120);
    for (const nm of [...JEWELS, ...STATUES]) {
      await page.evaluate((n) => (window as any).openDrop(n), nm);
      await page.waitForTimeout(60);
    }
    expect(errors).toEqual([]);
  });
});
