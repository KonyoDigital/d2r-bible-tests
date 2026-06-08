import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v109 — the Warlock "Bind Demon" tab (#tab-binds) was a stack of always-open .colossal
// blocks with plain <h3> headers — it didn't match the rest of the site, where every data
// section is a collapsible .sec-h/.sec-body that defaults COLLAPSED (the v56/v63 idiom).
// Each of the binds sections now carries a clickable .sec-h header + a .sec-body wrapper,
// driven by the same generic toggleSec() — content verbatim, nothing cut. (Count grew 12→14
// when v112 added the Tier-List + Aura-Enchanted elite-affix sections — both additive; then
// →15 when v120 added the Council roster section — also additive; then →16 when the
// "🎯 Best roll — what to look for" aura guide section was added — also additive; then
// →17 when v124c added the "Top 3 immunity profiles to bind" (#binds-immroll) section
// — also additive.)
test.describe('v109 binds tab collapsible sections', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => (window as any).switchTab('binds'));
    await page.waitForTimeout(150);
  });

  test('all 17 binds sections are collapsible and collapsed by default', async ({ page }) => {
    await expect(page.locator('#tab-binds .sec-h')).toHaveCount(17);
    await expect(page.locator('#tab-binds .sec-body')).toHaveCount(17);
    await expect(page.locator('#tab-binds .sec-body[hidden]')).toHaveCount(17);
    // every section head has a chevron affordance (matches the other tabs)
    await expect(page.locator('#tab-binds .sec-h .sec-chev')).toHaveCount(17);
    // the always-on intro banner is NOT a collapsible section
    await expect(page.locator('#tab-binds .events-intro')).toBeVisible();
  });

  test('clicking a header expands, clicking again collapses', async ({ page }) => {
    const head = page.locator('#tab-binds .sec-h', { hasText: 'The hard-point gate' });
    const body = head.locator('xpath=following-sibling::div[1]');
    await expect(body).toBeHidden();
    await head.evaluate((e: any) => e.click());
    await expect(body).toBeVisible();
    await expect(body).toContainText('Bind Demon checks your');
    await head.evaluate((e: any) => e.click());
    await expect(body).toBeHidden();
  });

  test('a tier-header section (Super-Unique Bosses) is also a working sec-h', async ({ page }) => {
    // the 3 tier sections keep their fancy tier-header banner but it now doubles as the toggle
    const head = page.locator('#tab-binds .sec-h', { hasText: 'Super-Unique Bosses' });
    await expect(head).toHaveClass(/tier-header/);
    const body = head.locator('xpath=following-sibling::div[1]');
    await expect(body).toBeHidden();
    await head.evaluate((e: any) => e.click());
    await expect(body).toBeVisible();
    // content preserved verbatim — Lister + Hephasto rows still there
    await expect(body).toContainText('Lister the Tormentor');
    await expect(body).toContainText('Hephasto the Armorer');
  });

  test('content is preserved verbatim — the Lister/Throne data the v83 sync test depends on still renders', async ({ page }) => {
    // textContent reaches into collapsed sections, so the binds-tab monster-data note survives
    const txt = await page.evaluate(() => (document.getElementById('tab-binds') as HTMLElement).textContent || '');
    expect(txt).toMatch(/Lister\s*92/);
    expect(txt).toMatch(/Throne of Destruction waves/);
    expect(txt).toMatch(/Minions of Destruction/);
  });
});
