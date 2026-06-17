import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// D2R in-game item-quality name colors
const GOLD = 'rgb(199, 179, 119)';   // --q-unique #c7b377
const GREEN = 'rgb(0, 255, 0)';      // --q-set    #00ff00
const ORANGE = 'rgb(255, 168, 0)';   // --q-orange #ffa800

async function openAll(page) {
  await page.evaluate(() => {
    document.querySelectorAll('details.all-drops-details').forEach((d) => d.setAttribute('open', ''));
  });
}
const nameCell = (page, boss: string, item: string) =>
  page.locator(`#${boss} tr[data-item="${item}"] td.item-name`);

test.describe('v130 in-game item-quality name colors + Cinzel font', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(false); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(300);
    await openAll(page);
  });

  test('unique items render gold (incl. tricky names that are NOT materials)', async ({ page }) => {
    for (const [boss, item] of [
      ['mephisto', 'Harlequin Crest (Shako)'],
      ['mephisto', 'The Stone of Jordan'],
      ['countess', 'Nokozan Relic'],
    ] as const) {
      const c = nameCell(page, boss, item);
      await expect(c).toHaveClass(/q-unique/);
      await expect(c).toHaveCSS('color', GOLD);
    }
  });

  test('set items render green', async ({ page }) => {
    const c = nameCell(page, 'mephisto', 'Tal Rasha set (any piece)');
    await expect(c).toHaveClass(/q-set/);
    await expect(c).toHaveCSS('color', GREEN);
  });

  test('runes render orange', async ({ page }) => {
    const c = nameCell(page, 'countess', 'Ist rune');
    await expect(c).toHaveClass(/q-rune/);
    await expect(c).toHaveCSS('color', ORANGE);
  });

  test('event tokens / shards render orange', async ({ page }) => {
    const c = nameCell(page, 'summoner', 'Key of Hate');
    await expect(c).toHaveClass(/q-material/);
    await expect(c).toHaveCSS('color', ORANGE);
  });

  test('item names use the in-game-style Cinzel display serif', async ({ page }) => {
    const c = nameCell(page, 'mephisto', 'Harlequin Crest (Shako)');
    await expect(c).toHaveCSS('font-family', /Cinzel/i);
  });

  test('grail rarity is still signalled — the tier pill survives next to the name', async ({ page }) => {
    const row = page.locator('#mephisto tr[data-item="The Stone of Jordan"]');
    // SoJ is a grail-tier item — tierPill still renders <span class="pill pill-grail"> in the name cell
    await expect(row.locator('td.item-name span.pill-grail')).toHaveCount(1);
  });
});
