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
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    // MF=300 matches the stored-base reference, so cells render the raw repulled numbers
    await page.locator('#mf').fill('300');
    await page.locator('#mf').dispatchEvent('input');
    await page.waitForTimeout(200);
  });

  test('Mephisto Hell-TZ Shako carries the RotW desecrated value (1:899, not vanilla 1:1,287)', async ({ page }) => {
    const c = await cell(page, 'mephisto', 'Harlequin Crest (Shako)', HELL_TZ);
    await expect(c).toContainText('1:899');
  });

  test('v187 gating, corrected: jewelry is qlvl-gated (Meph Norm-TZ SoJ has REAL odds), equipment stays TC-blocked (Vampire Gaze)', async ({ page }) => {
    // The original v129 pin assumed SoJ is TC60-gated — vanilla-think. Verified
    // empirically against silospen RoW desecrated (2026-06-11): SoJ (qlvl 39)
    // appears at EXACTLY desecratedLevel=39 and not at 30 (proper qlvl gating,
    // 1:4,472 at saturation), while Vampire Gaze (true TC60 equipment) NEVER
    // appears in Norm-TZ. The bible mirrors both: real odds for the ring, the
    // TC-block for the helm.
    const soj = await cell(page, 'mephisto', 'The Stone of Jordan', NORM_TZ);
    await expect(soj).toContainText('1:4,472');
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
    const gaze = await cell(page, 'mephisto', 'Vampire Gaze', NORM_TZ);
    await expect(gaze).toHaveClass(/blocked-tc|cannot/);
    await expect(gaze).not.toContainText('1:');
    await expect(gaze).toHaveAttribute('title', /TC \d+|not in .*drop pool/);
  });

  test('TZ odds are now per-boss real, not flat Meph-scaled — Countess Hell-TZ SoJ is far rarer than Mephisto', async ({ page }) => {
    // v187: values re-aligned to silospen-exact display (the v129 pull stored
    // +1 on a subset of cells — rounding epoch, not a data change).
    const mephSoj = await cell(page, 'mephisto', 'The Stone of Jordan', HELL_TZ);
    const countessSoj = await cell(page, 'countess', 'The Stone of Jordan', HELL_TZ);
    await expect(mephSoj).toContainText('1:7,808');
    await expect(countessSoj).toContainText('1:26,400');
  });

  test('runes are untouched by the unique/set repull — Countess Ist keeps 1:850 across TZ tiers', async ({ page }) => {
    const nm = await cell(page, 'countess', 'Ist rune', NM_TZ);
    const hell = await cell(page, 'countess', 'Ist rune', HELL_TZ);
    await expect(nm).toContainText('1:850');
    await expect(hell).toContainText('1:850');
  });
});
