import { test, expect } from '@playwright/test';

import * as path from 'path';
const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');
test.describe('Each cell renders the correct state', () => {
  test('blocked-tc cells render with TC-overrun title', async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(400);
    // Mephisto Norm-TZ TC57 caps below Vampire Gaze TC60 — TC block with overrun title.
    // (Was SoJ, but SoJ is a RING — jewelry is qlvl-gated, not TC-gated; the v187
    // silospen RoW pull gives Norm-TZ Meph real SoJ odds (1:4472), so the old pin
    // was asserting a vanilla-think wrong state. Vampire Gaze is true TC60 equipment.)
    /* v1729 — THE FACT SURVIVES; THE REASON DID NOT.
       This asserted that Vampire Gaze at Meph Norm-TZ is TC-BLOCKED, and that label came from a
       declared ceiling of TC57. v1722 measured that same cell and found equipment of tc 78 AND
       tc 85 demonstrably dropping in it (Stormchaser, The Grim Reaper, Ginther's Rift), so 57 was
       never the real cap — the app was attaching a discredited REASON to a true FACT.
       Vampire Gaze is tc60 / qlvl41 in a cell of mlvl 45 and a corroborated ceiling of 78: NEITHER
       annotation blocks it, and it still cannot drop (silospen does not list it). The two numbers
       this app stores simply do not explain that cell, so it now says so — `cannot`, with the
       honest reason "not in this run's drop pool".
       The assertion keeps what was verified empirically in v187 — the ring HAS odds, the helm does
       NOT — and drops the claim about WHICH annotation explains the helm, because that claim is
       the part that was wrong. */
    const row = page.locator('#mephisto tr[data-item="Vampire Gaze"]');
    const normTzCell = row.locator('td.diff-col').nth(1);
    await expect(normTzCell).toHaveClass(/blocked-tc|cannot/);
    await expect(normTzCell).not.toContainText('1:');
    await expect(normTzCell).toHaveAttribute('title', /TC \d+|not in .*drop pool/);
  });

  test('qlvl blocked cells show orange (block-mlvl) class', async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    // Andariel NM can't drop Mara's (qlvl 67 > NM Andy mlvl 49)
    const row = page.locator('#andariel tr[data-item="Mara\'s Kaleidoscope"]');
    const nmCell = row.locator('td.diff-col').nth(2);
    /* v1729 — a qlvl reason is now SUPPRESSED in any cell whose own data breaks that rule: if
       items of that qlvl demonstrably drop there, "qlvl X > mlvl Y" is not why this one does not.
       Such a cell falls through to the TC reason if one is true, and otherwise to the honest
       "not in the … drop pool". All three are correct states; a cell with NO explanation is not,
       which is what this now guards. */
    const cls = await nmCell.getAttribute('class') || '';
    const title = await nmCell.getAttribute('title') || '';
    expect(cls).toMatch(/blocked-mlvl|blocked-tc|cannot/);
    expect(title, 'every non-dropping cell must explain itself').toMatch(/qlvl \d+|TC \d+|drop pool/);
  });

  test('best cells in each row are highlighted gold', async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    // Pick first boss card, verify at least one cell is best-cell
    const bestCells = page.locator('#mephisto td.best-cell');
    const count = await bestCells.count();
    expect(count).toBeGreaterThan(0);
  });

  test('each visible chance cell shows 1:N format or %', async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    const cells = page.locator('#mephisto td.diff-col:not(.blocked-tc):not(.blocked-mlvl):not(.cannot)');
    const count = await cells.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < Math.min(count, 10); i++) {
      const text = (await cells.nth(i).textContent())?.trim() || '';
      // should match "1:N" with optional comma or "N%"
      expect(text, `cell ${i}: "${text}"`).toMatch(/^(1:[\d,]+|\d+%|—)$/);
    }
  });

  test('boss tier badges are present', async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    const tiers = ['S+', 'S', 'A+', 'A', 'A-'];
    for (const tier of tiers) {
      const found = await page.locator(`.boss-tier-val:has-text("${tier}")`).count();
      expect(found, `tier ${tier} should appear`).toBeGreaterThan(0);
    }
  });

  test('every boss row has clickable item name with star + owned button', async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(400);
    // v43: the full drop table is collapsed behind <details class="all-drops-details"> (Top Drops
    // feature). Expand mephisto's so the rows are visible before asserting on their controls.
    await page.evaluate(() => {
      document.getElementById('mephisto')
        ?.querySelector('details.all-drops-details')?.setAttribute('open', '');
    });
    const firstRow = page.locator('#mephisto tr.clickable').first();
    expect(await firstRow.locator('.star-btn').count()).toBe(1);
    expect(await firstRow.locator('.owned-btn').count()).toBe(1);
  });

  test('total item-rows across all bosses ≥ 200', async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    const rows = page.locator('.boss-card tr.clickable');
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(200);
  });
});
