import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v56 — ROTW data sections are collapsible via the generic toggleSec mechanism.
// The 4 data sections (Shards/Essences/Keys/Sunders) get a clickable .sec-h
// header + .sec-body wrapper. v63: every dropdown section site-wide now defaults
// to COLLAPSED (Konyo's request — tidy by default, click a title to open). The
// 2 interactive trackers (Statues, Set) are intentionally left untouched.
test.describe('v56 ROTW collapsible sections', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => (window as any).switchTab('rotw'));
  });

  test('5 sections collapsible, all collapsed by default', async ({ page }) => {
    // v72: the Herald of Terror showpiece card is a 5th .sec-h/.sec-body at the
    // top of the tab. Per Konyo's request every section (incl. Herald) now
    // defaults COLLAPSED — tidy by default, click a title to drop it open.
    await expect(page.locator('#tab-rotw .sec-h')).toHaveCount(5);
    await expect(page.locator('#tab-rotw .sec-body')).toHaveCount(5);
    await expect(page.locator('#tab-rotw .sec-body[hidden]')).toHaveCount(5);
    await expect(page.locator('#tab-rotw .sec-h').first()).toHaveText(/Herald of Terror/);
  });

  test('clicking a header expands, clicking again collapses', async ({ page }) => {
    const head = page.locator('#tab-rotw .sec-h', { hasText: 'Worldstone Shards' });
    const body = head.locator('xpath=following-sibling::div[1]');
    await expect(body).toBeHidden();
    await head.evaluate((e:any) => e.click());
    await expect(body).toBeVisible();
    await head.evaluate((e:any) => e.click());
    await expect(body).toBeHidden();
  });

  test('routing still works inside a wrapped section', async ({ page }) => {
    // section defaults collapsed → expand it first, then click the shard link
    await page.locator('#tab-rotw .sec-h', { hasText: 'Worldstone Shards' }).evaluate((e:any) => e.click());
    await page.locator('#tab-rotw .shard-name.zd-item-click', { hasText: 'Eastern Worldstone Shard' }).first().evaluate((e:any) => e.click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Cold Rupture');
  });

  test('statue tracker cross-links to the Colossal Ancient Jewels card', async ({ page }) => {
    await page.locator('#tab-rotw .zd-item-click', { hasText: 'Colossal Ancient Jewels' }).first().evaluate((e:any) => e.click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Colossal Ancient Jewels');
  });

});
