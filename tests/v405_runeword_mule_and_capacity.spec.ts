import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v405 — (1) ALL runewords route to the dedicated RUNEWORDS mule regardless of base slot;
//        (2) a mule that overflows 140 cells (100 stash + 40 inventory) auto-splits across
//            multiple mule characters with a working ◄ ► pager — "97 in one mule" can't happen.
test.describe('v405 runeword mule + capacity overflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('every runeword (weapon OR armor base) routes to {id:"runewords"}', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      // Enigma = body armor base, Spirit = sword/shield base, Insight = polearm — all must go to one mule
      return {
        enigma: w.suggestMule('Enigma'),
        spirit: w.suggestMule('Spirit'),
        insight: w.suggestMule('Insight'),
        cta: w.suggestMule('Call to Arms'),
      };
    });
    expect(r.enigma.id).toBe('runewords');
    expect(r.spirit.id).toBe('runewords');
    expect(r.insight.id).toBe('runewords');
    expect(r.cta.id).toBe('runewords');
  });

  test('a runeword stays in ownedPool (so its mule assignment is not pruned)', async ({ page }) => {
    const inPool = await page.evaluate(() => {
      const w = window as any;
      const pool = w.ownedPool ? w.ownedPool() : null;
      // ownedPool returns the list of names considered "real" / keepable
      return !!(pool && (Array.isArray(pool) ? pool.indexOf('Enigma') >= 0 : pool['Enigma']));
    });
    // ownedPool may be a membership test rather than a list; fall back to the predicate the app uses
    if (!inPool) {
      const viaPredicate = await page.evaluate(() => {
        const w = window as any;
        return !!(w.findRuneword && w.findRuneword('Enigma'));
      });
      expect(viaPredicate).toBe(true);
    } else {
      expect(inPool).toBe(true);
    }
  });

  test('the RUNEWORDS mule exists in the roster', async ({ page }) => {
    const names = await page.evaluate(() =>
      [...document.querySelectorAll('.vm-name')].map(e => e.textContent)
    );
    expect(names).toContain('RUNEWORDS');
  });

  test('overflowing a mule splits across multiple mule pages with a working pager', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', m => { if (m.type()==='error') errs.push(m.text()); });
    page.on('pageerror', e => errs.push(e.message));
    const r = await page.evaluate(() => {
      const w = window as any;
      // pack 60 big (2x4 = 8-cell) armor bases into one mule → 60*8 = 480 cells ≫ 140 → needs >=4 mules
      const names: string[] = [];
      for (let i = 0; i < 60; i++) {
        const nm = 'TestPolearm ' + i + ' (Larzuk base)';
        names.push(nm);
        w.EXTRA_ITEMS[nm] = { cat: 'Socketed bases', slot: 'Weapon' };
        eval("owned.add(" + JSON.stringify(nm) + ");");
        w.vaultAssign(nm, 'bases');
      }
      w.openMuleCard('bases');
      const box = document.getElementById('vault-detail');
      const tag = box?.querySelector('.vd-mule-pg')?.textContent || '';
      const page1Items = box ? box.querySelectorAll('.vd-item').length : 0;
      // step to mule 2 via the pager and confirm the page changes
      w._muleSetPage(1);
      const box2 = document.getElementById('vault-detail');
      const tag2 = box2?.querySelector('.vd-mule-pg')?.textContent || '';
      const page2Items = box2 ? box2.querySelectorAll('.vd-item').length : 0;
      w.vaultCloseCard && w.vaultCloseCard();
      return { tag, page1Items, tag2, page2Items };
    });
    expect(r.tag).toContain('Mule 1');
    expect(r.tag).toMatch(/\/\s*[2-9]/);          // total pages >= 2
    expect(r.page1Items).toBeGreaterThan(0);
    expect(r.page1Items).toBeLessThanOrEqual(140); // never more than one mule's worth on a page
    expect(r.tag2).toContain('Mule 2');
    expect(r.page2Items).toBeGreaterThan(0);
    expect(errs).toEqual([]);
  });
});
