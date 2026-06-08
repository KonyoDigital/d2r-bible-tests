import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// Diff-col order: 0 norm, 1 normTz, 2 nm, 3 nmTz, 4 hell, 5 hellTz
const NORM_TZ = 1, NM_TZ = 3, HELL_TZ = 5;

async function cell(page, bossId: string, item: string, idx: number) {
  // the drop table is collapsed behind <details>; open it so reads are robust
  await page.evaluate((b) => {
    document.getElementById(b)?.querySelector('details.all-drops-details')?.setAttribute('open', '');
  }, bossId);
  const row = page.locator(`#${bossId} tr[data-item="${item}"]`);
  return row.locator('td.diff-col').nth(idx);
}

test.describe('v129 TZ columns repulled from silospen RotW desecrated data', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    // MF=300 matches the stored-base reference, so cells render the raw repulled numbers
    await page.locator('#mf').fill('300');
    await page.locator('#mf').dispatchEvent('input');
    await page.waitForTimeout(200);
  });

  test('Mephisto Hell-TZ Shako carries the RotW desecrated value (1:899, not vanilla 1:1,287)', async ({ page }) => {
    const c = await cell(page, 'mephisto', 'Harlequin Crest (Shako)', HELL_TZ);
    await expect(c).toContainText('1:899');
  });

  test('the bible TC/mlvl gating is preserved — Meph Norm-TZ SoJ (TC60 > TZ TC57) stays blocked-tc, not overwritten', async ({ page }) => {
    const c = await cell(page, 'mephisto', 'The Stone of Jordan', NORM_TZ);
    await expect(c).toHaveClass(/blocked-tc/);
    await expect(c).toHaveAttribute('title', /TC \d+/);
  });

  test('TZ odds are now per-boss real, not flat Meph-scaled — Countess Hell-TZ SoJ is far rarer than Mephisto', async ({ page }) => {
    const mephSoj = await cell(page, 'mephisto', 'The Stone of Jordan', HELL_TZ);
    const countessSoj = await cell(page, 'countess', 'The Stone of Jordan', HELL_TZ);
    await expect(mephSoj).toContainText('1:7,809');
    await expect(countessSoj).toContainText('1:26,401');
  });

  test('runes are untouched by the unique/set repull — Countess Ist keeps 1:850 across TZ tiers', async ({ page }) => {
    const nm = await cell(page, 'countess', 'Ist rune', NM_TZ);
    const hell = await cell(page, 'countess', 'Ist rune', HELL_TZ);
    await expect(nm).toContainText('1:850');
    await expect(hell).toContainText('1:850');
  });
});
