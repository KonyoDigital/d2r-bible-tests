import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v294 — every grail item's ID card renders its NAME in the EXACT in-game rarity colour
// (the ÿc quality palette, defined as --q-* CSS vars): unique #c7b377, set #00ff00,
// magic #6969ff, rare #ffff64, crafted/runeword #ffa800. _artRarity stamps aid-r-<rarity>
// on each aid-card so the name colour follows automatically; set items route to a set
// card whose title is also set-green.

async function colorOf(page: any, item: string, sel: string){
  await page.evaluate((n: string) => (window as any).openDrop(n), item);
  await page.waitForTimeout(200);
  return page.evaluate((s: string) => {
    const el = document.querySelector('#item-detail ' + s) as HTMLElement | null;
    return el ? getComputedStyle(el).color : null;
  }, sel);
}

test.describe('v294 in-game rarity colours', () => {
  test.beforeEach(async ({ page }) => { await page.goto(BIBLE); await page.waitForTimeout(500); });

  test('the exact in-game quality palette vars are defined', async ({ page }) => {
    const vars = await page.evaluate(() => {
      const s = getComputedStyle(document.documentElement);
      const g = (n: string) => s.getPropertyValue(n).trim().toLowerCase();
      return { unique: g('--q-unique'), set: g('--q-set'), magic: g('--q-magic'), rare: g('--q-rare'), orange: g('--q-orange') };
    });
    expect(vars.unique).toBe('#c7b377');
    expect(vars.set).toBe('#00ff00');
    expect(vars.magic).toBe('#6969ff');
    expect(vars.rare).toBe('#ffff64');
    expect(vars.orange).toBe('#ffa800');
  });

  test('a unique item ID-card name is rendered in unique gold (#c7b377)', async ({ page }) => {
    const c = await colorOf(page, 'The Stone of Jordan', '.aid-card.aid-r-unique .aid-item-name');
    expect(c).toBe('rgb(199, 179, 119)');
  });

  test('a set item card title is rendered in set green (#00ff00)', async ({ page }) => {
    const c = await colorOf(page, "Sigon's Complete Steel", '.set-items-card .gic-name');
    expect(c).toBe('rgb(0, 255, 0)');
  });

  test('a runeword card title is rendered in orange (#ffa800)', async ({ page }) => {
    const c = await colorOf(page, 'Spirit', '.runeword-card .gic-name');
    expect(c).toBe('rgb(255, 168, 0)');
  });

  test('every grail item carries a rarity → none would fall back to default gold', async ({ page }) => {
    // _artRarity must classify every aid-card-routed grail unique/set (no empty rarity).
    const r = await page.evaluate(() => {
      const ar = (window as any)._artRarity;
      const names = ['The Stone of Jordan', 'Nagelring', "Sigon's Complete Steel", 'Tal Rasha set (any piece)'];
      return names.map(n => ({ n, r: ar(n) }));
    });
    for (const x of r) expect(x.r).not.toBe('');
  });
});
