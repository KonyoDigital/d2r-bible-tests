import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v131 — the aggregate "Colossal Ancient Jewels" material card (the card a drop-row
// or material grid opens) now surfaces the 6 individual jewels as clickable tiles,
// each routing via openDrop() to its own ID card. Previously the 6 variants were
// only named in prose, so the per-jewel cards (which already existed + were
// searchable) were unreachable from the aggregate card the user actually lands on.
const JEWELS = ["Defender's Bile", "Guardian's Thunder", "Protector's Frost", "Defender's Fire", "Protector's Stone", "Guardian's Light"];

const dropName = (oc: string): string | undefined => {
  const m = oc.match(/openDrop\('((?:\\.|[^'])*)'\)/);
  return m ? m[1].replace(/\\'/g, "'") : undefined;
};

test.describe('v131 aggregate Colossal Ancient Jewels card links to the 6 individual jewels', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);
  });

  test('the aggregate jewel material card renders 6 clickable jewel tiles routing to each card', async ({ page }) => {
    const links = await page.evaluate(() => {
      (window as any).openDrop('Colossal Ancient Jewels');
      const card = document.getElementById('item-detail')?.querySelector('.material-card:not(.colossal-jewel-card)');
      const tiles = [...(card?.querySelectorAll('.colossal-tile.endgame-relic') || [])];
      return tiles.map((t) => t.getAttribute('onclick') || '');
    });
    const names = links.map(dropName).filter(Boolean) as string[];
    expect(names.length).toBe(6);
    for (const j of JEWELS) expect(names).toContain(j);
  });

  test('clicking an aggregate-card jewel tile opens that jewel\'s own ID card', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openDrop('Colossal Ancient Jewels');
      const card = document.getElementById('item-detail')?.querySelector('.material-card:not(.colossal-jewel-card)');
      const firstTile = card?.querySelector('.colossal-tile.endgame-relic') as HTMLElement | null;
      const oc = firstTile?.getAttribute('onclick') || '';
      const m = oc.match(/openDrop\('((?:\\.|[^'])*)'\)/);
      const nm = m ? m[1].replace(/\\'/g, "'") : '';
      (window as any).openDrop(nm);
      const jewelCard = document.getElementById('item-detail')?.querySelector('.colossal-jewel-card');
      return {
        clicked: nm,
        isJewelCard: !!jewelCard,
        name: (jewelCard?.querySelector('.gic-name')?.textContent || '').trim(),
      };
    });
    expect(JEWELS).toContain(r.clicked);
    expect(r.isJewelCard).toBe(true);
    expect(r.name).toContain(r.clicked);
  });

  test('each of the 6 jewels is still globally searchable to its own card', async ({ page }) => {
    for (const nm of JEWELS) {
      await page.fill('#gsearch-input', nm);
      await page.waitForTimeout(150);
      const hit = await page.evaluate(() => {
        const el = document.querySelector('#gsearch-results .gsearch-item');
        return el ? (el.querySelector('.gsearch-lab') as HTMLElement)?.textContent?.trim() : '';
      });
      expect(hit?.startsWith(nm)).toBe(true);
    }
  });
});
