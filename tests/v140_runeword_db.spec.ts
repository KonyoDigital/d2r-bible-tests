import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v140 — the runeword database is expanded from ~15 to the full Reign-of-the-Warlock
// set (100 verified entries transcribed from diablo2.io ajax tooltips). New surface:
//   - RUNEWORD_TIP: per-runeword verified stat registry {l,t:'Runeword',b,r,rec}.
//   - _arttipResolve resolves any runeword name → a rich hover card (image-less).
//   - findRuneword + runewordDetailHtml + an openDrop branch (EXACT match, before
//     findMaterial) give every runeword a clickable ID card in the .runeword-card slot.
//   - an "All Runewords" collapsible browser (#all-runewords-card) lists all of them,
//     each row clickable → openDrop, with a filter box.
//   - the global-search runeword results now route to openDrop (the ID card) instead
//     of the old toast.
// Additive + ZERO fabrication: RUNEWORDS keeps the curated 15 + Death's Web pseudo so
// the v68 planner/v42 search constraints still hold.

const FLAGSHIP = ['Enigma', 'Spirit', 'Grief', 'Infinity', 'Call to Arms', 'Heart of the Oak',
  'Last Wish', 'Phoenix', 'Faith', 'Mosaic', 'Metamorphosis', 'Mist', 'Doom'];

test.describe('v140 full runeword database + ID cards + browser', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);
  });

  test('RUNEWORD_TIP holds 100 verified, well-formed entries', async ({ page }) => {
    const r = await page.evaluate(() => {
      const T = (window as any).RUNEWORD_TIP || {};
      const keys = Object.keys(T);
      let emptyLines = 0, badTier = 0, noRec = 0, noReq = 0;
      for (const k of keys) {
        const o = T[k];
        if (!Array.isArray(o.l) || o.l.length === 0) emptyLines++;
        if (o.t !== 'Runeword') badTier++;
        if (!Array.isArray(o.rec) || o.rec.length === 0) noRec++;
        if (o.r == null) noReq++;
      }
      return { count: keys.length, emptyLines, badTier, noRec, noReq };
    });
    expect(r.count).toBe(100);
    expect(r.emptyLines).toBe(0);
    expect(r.badTier).toBe(0);
    expect(r.noRec).toBe(0);
    expect(r.noReq).toBe(0);
  });

  test('findRuneword normalizes display names (incl. parenthetical abbrevs)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const f = (window as any).findRuneword;
      return {
        spiritSword: f('Spirit (sword)'),
        spiritShield: f('Spirit (shield)'),
        cta: f('Call to Arms (CTA)'),
        hoto: f('Heart of the Oak (HotO)'),
        botd: f('Breath of the Dying (BotD)'),
        enigma: f('Enigma'),
        crescent: f('Crescent Moon'),
        bogus: f('Not A Runeword'),
        deathsWeb: f("Death's Web"),
      };
    });
    expect(r.spiritSword).toBe('Spirit');
    expect(r.spiritShield).toBe('Spirit');
    expect(r.cta).toBe('Call to Arms');
    expect(r.hoto).toBe('Heart of the Oak');
    expect(r.botd).toBe('Breath of the Dying');
    expect(r.enigma).toBe('Enigma');
    expect(r.crescent).toBe('Crescent Moon');
    expect(r.bogus).toBeNull();
    expect(r.deathsWeb).toBeNull();   // the unique pseudo-entry is NOT a runeword
  });

  test('_arttipResolve gives every runeword a rich (image-less) stat card', async ({ page }) => {
    const r = await page.evaluate((flagship) => {
      const f = (window as any)._arttipResolve;
      const out: Record<string, { rich: boolean; type: boolean; rec: boolean; req: boolean }> = {};
      for (const n of flagship) {
        const x = f(n);
        out[n] = {
          rich: x.rich,
          type: /att-type/.test(x.desc) && /Runeword/.test(x.desc),
          rec: /att-rwrec/.test(x.desc),
          req: /Req level/.test(x.desc),
        };
      }
      return out;
    }, FLAGSHIP);
    for (const n of FLAGSHIP) {
      expect(r[n].rich, n).toBe(true);
      expect(r[n].type, n).toBe(true);
      expect(r[n].rec, n).toBe(true);
      expect(r[n].req, n).toBe(true);
    }
  });

  test('runeword stat ranges render as green chips; no raw [X-Y] markers leak', async ({ page }) => {
    const r = await page.evaluate(() => {
      const f = (window as any)._arttipResolve;
      const enigma = f('Enigma');            // has +[750-775] Defense + level-scaled chips
      return {
        chip: /att-var/.test(enigma.desc),
        rawBrackets: /\[[0-9]/.test(enigma.desc),
      };
    });
    expect(r.chip).toBe(true);
    expect(r.rawBrackets).toBe(false);
  });

  test('openDrop routes a runeword to its .runeword-card ID card (clickable recipe runes)', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openDrop('Enigma');
      const panel = document.getElementById('item-detail')!;
      const card = panel.querySelector('.runeword-card');
      return {
        shown: panel.classList.contains('show'),
        hasCard: !!card,
        name: card?.querySelector('.gic-name')?.textContent?.includes('Enigma'),
        chips: panel.querySelectorAll('.rwd-recipe .mw-rune-chip').length,
        firstChipArttip: (panel.querySelector('.rwd-recipe .mw-rune-chip') as HTMLElement)?.getAttribute('data-arttip'),
        stats: panel.querySelectorAll('.rwd-stat').length,
      };
    });
    expect(r.shown).toBe(true);
    expect(r.hasCard).toBe(true);
    expect(r.name).toBe(true);
    expect(r.chips).toBe(3);                 // Jah + Ith + Ber
    expect(r.firstChipArttip).toBe('Jah');
    expect(r.stats).toBeGreaterThan(5);
  });

  test('a short-named runeword routes to ITS card, not a material substring collision', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openDrop('Bone');       // must NOT mis-route to the "Bone Break" sunder charm
      const panel = document.getElementById('item-detail')!;
      return {
        rwCard: !!panel.querySelector('.runeword-card'),
        materialCard: !!panel.querySelector('.material-card'),
        name: panel.querySelector('.gic-name')?.textContent?.includes('Bone'),
      };
    });
    expect(r.rwCard).toBe(true);
    expect(r.materialCard).toBe(false);
    expect(r.name).toBe(true);
  });

  test('the All Runewords browser lists every entry; rows are clickable + filterable', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).renderAllRunewords();
      const list = document.getElementById('all-rw-list')!;
      const allRows = list.querySelectorAll('.arw-row').length;
      const firstClickable = (list.querySelector('.arw-row') as HTMLElement)?.getAttribute('onclick') || '';
      const firstArttip = !!(list.querySelector('.arw-row') as HTMLElement)?.hasAttribute('data-arttip');
      // filter
      const f = document.getElementById('all-rw-filter') as HTMLInputElement;
      f.value = 'jah';
      (window as any).renderAllRunewords();
      const filtered = list.querySelectorAll('.arw-row').length;
      const names = [...list.querySelectorAll('.arw-name')].map((e) => e.textContent);
      return { allRows, firstClickable, firstArttip, filtered, hasEnigma: names.includes('Enigma') };
    });
    expect(r.allRows).toBeGreaterThanOrEqual(100);   // 100 tip RWs + curated dupes/pseudo
    expect(r.firstClickable).toContain('openDrop');
    expect(r.firstArttip).toBe(true);
    expect(r.filtered).toBeGreaterThan(0);
    expect(r.filtered).toBeLessThan(r.allRows);       // 'jah' narrows the list
    expect(r.hasEnigma).toBe(true);                   // Enigma uses a Jah
  });

  test('global search routes a runeword result to the openDrop ID card', async ({ page }) => {
    await page.fill('#gsearch-input', 'enigma');
    await page.waitForTimeout(220);
    await page.evaluate(() => {
      const items = [...document.querySelectorAll('#gsearch-results .gsearch-item')] as HTMLElement[];
      const hit = items.find((el) => /Enigma/.test(el.textContent || '')) || items[0];
      // gsearch executes the result action on mousedown (not click)
      hit?.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    });
    await page.waitForTimeout(150);
    const r = await page.evaluate(() => {
      const panel = document.getElementById('item-detail')!;
      return {
        rwCard: !!panel.querySelector('.runeword-card'),
        name: panel.querySelector('.gic-name')?.textContent?.includes('Enigma'),
      };
    });
    expect(r.rwCard).toBe(true);
    expect(r.name).toBe(true);
  });

  test('hovering a planner row / runeword cell floats the rich runeword card', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openDrop('Spirit (sword)');
      const chip = document.querySelector('.runeword-card .mw-rune-chip[data-arttip="Tal"]') as HTMLElement | null;
      const tip = document.getElementById('arttip')!;
      // hover the whole-card route instead: tag a synthetic element
      const probe = document.createElement('span');
      probe.setAttribute('data-arttip', 'Grief');
      document.body.appendChild(probe);
      probe.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 200, clientY: 200 }));
      const onAfterRW = tip.classList.contains('on');
      const rich = tip.classList.contains('tip-rich');
      const txt = tip.querySelector('.att-type')?.textContent || '';
      probe.remove();
      return { chipFound: !!chip, onAfterRW, rich, isRW: /Runeword/.test(txt) };
    });
    expect(r.chipFound).toBe(true);
    expect(r.onAfterRW).toBe(true);
    expect(r.rich).toBe(true);
    expect(r.isRW).toBe(true);
  });

  test('the full runeword rollout produces no console errors', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate(() => {
      const T = (window as any).RUNEWORD_TIP || {};
      const f = (window as any)._arttipResolve;
      for (const k in T) { f(k); (window as any).runewordDetailHtml(k); }
      (window as any).renderAllRunewords();
      (window as any).openDrop('Mosaic');
      (window as any).openDrop('Phoenix');
    });
    await page.waitForTimeout(120);
    expect(errs).toEqual([]);
  });
});
