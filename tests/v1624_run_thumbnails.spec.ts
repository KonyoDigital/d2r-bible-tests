import { test, expect } from './_net_stub';
import * as path from 'path';

// v1624 — THE RUN'S PICTURE IS THE RUN.
//
// Konyo: "the item logos on the left for each Hell mephisto and the pindleskin.. like what are they
// representing? ... something might be not coded properly and its confusing fix it please too".
//
// The thumbnail was art(r.items[0].n) — whichever unique happened to sort FIRST in that run's drop
// list, with a target glyph when that item had no art. Not the boss, not the fastest drop, not the
// level: an arbitrary picture that changed as his grail changed. Pindleskin rendered a bare emoji
// for no reason a reader could infer.
//
// His call: "for best runs it shows us the boss as a main.. and for quick wins we dont touch and
// leave it as is which is the item as the main" — both clickable, both with the hover card.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

async function funi(page: any) {
  await page.goto(URL);
  await page.waitForTimeout(2800);
  await page.evaluate(() => { try { (window as any).switchTab('funi'); } catch (e) {} });
  await page.waitForTimeout(1800);
}

test.describe('v1624 — the run wears its boss, the quick win wears its item', () => {
  test('★★★ every BEST RUN thumbnail is its BOSS, and it loads', async ({ page }) => {
    await funi(page);
    const rows = await page.evaluate(() =>
      Array.from(document.querySelectorAll('#tab-funi .f-card.f-pipe')).slice(0, 5).map((c: any) => {
        const a: any = c.querySelector('.f-runart');
        const img: any = a?.querySelector('img');
        return { title: (c.querySelector('.f-rwbig') as any)?.textContent?.trim() || '',
                 logo: a?.getAttribute('data-art-logo') || null,
                 loaded: img ? img.naturalWidth > 0 : false,
                 click: (a?.getAttribute('onclick') || '') };
      }));
    expect(rows.length).toBeGreaterThan(2);
    for (const r of rows) {
      expect(r.logo, `${r.title} has no boss anchor`).toBeTruthy();
      // the picture is OF the boss the row is about — the title contains the boss name
      expect(r.title.toLowerCase()).toContain(String(r.logo).toLowerCase());
      expect(r.loaded, `${r.title}: the boss art must actually decode`).toBe(true);
      expect(r.click, 'and open that boss').toContain('openBossDetail');
    }
  });

  test('★★ QUICK WINS still shows the ITEM — his explicit call', async ({ page }) => {
    await funi(page);
    const q = await page.evaluate(() =>
      Array.from(document.querySelectorAll('#tab-funi .f-card.f-step')).slice(0, 3).map((c: any) => {
        const a: any = c.querySelector('.f-runart');
        return { logo: a?.getAttribute('data-art-logo') || null,
                 click: a?.getAttribute('onclick') || '',
                 name: (c.querySelector('.f-rwbig') as any)?.textContent?.trim() || '' };
      }));
    if (!q.length) return;   // no one-step wins right now is a legitimate state
    for (const r of q) {
      expect(r.logo, 'the quick win names an ITEM, not a boss').toBeTruthy();
      expect(r.click, 'and opens that item, not a boss card').toContain('navigateToItem');
    }
  });

  test('★★ the boss art resolver covers EVERY boss — measured, not hoped', async ({ page }) => {
    /* Written before the change and kept: 13 of 13 resolve — 8 through the zone art the TZ panel
       already paints with, 5 through their own portrait. A resolver that silently returns null for
       a third of the roster would put the arbitrary-picture problem back under a new name. */
    await page.goto(URL); await page.waitForTimeout(2600);
    const cover = await page.evaluate(() => {
      const w: any = window;
      let B: any = [];
      try { B = (0, eval)('BOSSES'); } catch (e) { B = w.BOSSES || []; }
      let ok = 0;
      for (const b of B) {
        const r = w._runBossArt ? w._runBossArt(b.id, b.name) : null;
        if (r && (r.url || r.emoji)) ok++;
      }
      return { total: B.length, ok };
    });
    expect(cover.total).toBeGreaterThan(10);
    expect(cover.ok, 'every boss must resolve to something real').toBe(cover.total);
  });
});
