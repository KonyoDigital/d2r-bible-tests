// v204 — mule ID card: the in-game replica. Click a locker (no chip selected)
// → #vault-detail renders a 10×10 personal-stash grid + 10×4 inventory with
// the mule's items FIRST-FIT-PACKED at their approximate in-game sizes
// (vaultSize: base-type keyword taxonomy), a col/row packing list, and an
// overflow warning ("roll NAME-2") when the mule physically can't hold it.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v204 mule ID card', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2200);
    await page.evaluate(() => {
      localStorage.removeItem('d2r_muleRoster');
      localStorage.removeItem('d2r_muleAssign');
      ['Harlequin Crest (Shako)', 'Stormshield', 'Vampire Gaze', 'War Traveler',
       'The Stone of Jordan', 'Annihilus', 'Hellfire Torch', "Gheed's Fortune",
       'Windforce'].forEach(n => eval('owned').add(n));
      (window as any).switchTab('tools');
      (window as any).renderVault();
      (window as any).vaultAutoAssign();
    });
  });

  test('size taxonomy: caps 2×2, shields 2×3, bows 2×4, rings/anni 1×1, torch 1×2, gheed 1×3', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sz = (n: string) => (window as any).vaultSize(n).join('x');
      return {
        shako: sz('Harlequin Crest (Shako)'), storm: sz('Stormshield'),
        wf: sz('Windforce'), soj: sz('The Stone of Jordan'),
        anni: sz('Annihilus'), torch: sz('Hellfire Torch'), gheed: sz("Gheed's Fortune"),
      };
    });
    expect(r.shako).toBe('2x2');
    expect(r.storm).toBe('2x3');
    expect(r.wf).toBe('2x4');
    expect(r.soj).toBe('1x1');
    expect(r.anni).toBe('1x1');
    expect(r.torch).toBe('1x2');
    expect(r.gheed).toBe('1x3');
  });

  test('clicking a locker plate (no chip selected) opens the replica with a 10×10 grid + packed items + list', async ({ page }) => {
    await page.evaluate(() => {
      (document.querySelector('[data-vault-mule="uni-armor"] .vm-plate') as HTMLElement).click();
    });
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const det = document.getElementById('vault-detail')!;
      const blocks = [...det.querySelectorAll('.vd-item')];
      // no two placed blocks overlap (packer integrity)
      const rects = blocks.map(b => b.getBoundingClientRect());
      let overlap = false;
      for (let i = 0; i < rects.length; i++) for (let j = i + 1; j < rects.length; j++) {
        const a = rects[i], c = rects[j];
        if (a.left < c.right - 1 && c.left < a.right - 1 && a.top < c.bottom - 1 && c.top < a.bottom - 1) overlap = true;
      }
      return {
        visible: !det.hidden,
        name: det.querySelector('.vd-name')!.textContent,
        // v206: stash 100 + always-visible inventory 40 (side-by-side zones)
        cells: det.querySelectorAll('.vd-cell').length,
        items: blocks.length,
        listRows: det.querySelectorAll('.vd-list div').length,
        overlap,
      };
    });
    expect(r.visible).toBe(true);
    expect(r.name).toBe('UNI-ARMOR');
    expect(r.cells).toBe(140);
    expect(r.items).toBeGreaterThanOrEqual(3);
    expect(r.listRows).toBe(r.items);
    expect(r.overlap).toBe(false);
  });

  test('overflow: a mule with more bulk than 10×10 + 10×4 warns to roll NAME-2', async ({ page }) => {
    const r = await page.evaluate(() => {
      // stuff one locker past 140 cells: pick 40 real items whose computed
      // size is >=4 cells (40 x >=4 = >=160 > 100+40 capacity)
      const big = eval('ITEMS')
        .map((i: any) => i.n)
        .filter((n: string) => { const sz = (window as any).vaultSize(n); return sz[0] * sz[1] >= 4; })
        .slice(0, 40);
      big.forEach((n: string) => { eval('owned').add(n); (window as any).vaultAssign(n, 'wip'); });
      (window as any).openMuleCard('wip');
      const det = document.getElementById('vault-detail')!;
      return { assigned: big.length, overflow: !!det.querySelector('.vd-overflow'), invGrid: det.querySelectorAll('.vd-grid').length };
    });
    expect(r.assigned).toBeGreaterThanOrEqual(20);
    expect(r.overflow).toBe(true);
    expect(r.invGrid).toBe(2); // stash + inventory both render when overflowing
  });

  test('close button hides the card; empty locker shows the empty state', async ({ page }) => {
    await page.evaluate(() => (window as any).openMuleCard('dupes'));
    const r1 = await page.evaluate(() => ({
      visible: !document.getElementById('vault-detail')!.hidden,
      empty: document.getElementById('vault-detail')!.textContent!.includes('empty locker'),
    }));
    expect(r1.visible).toBe(true);
    expect(r1.empty).toBe(true);
    await page.evaluate(() => (document.querySelector('#vault-detail .vd-close') as HTMLElement).click());
    expect(await page.evaluate(() => document.getElementById('vault-detail')!.hidden)).toBe(true);
  });
});
