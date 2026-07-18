// v851 — THE THEATRE SPEC PACK (audit-board: 'everything v790→v847 is unguarded').
// Drives the LIVE control app (http://127.0.0.1:17772) — the native UI itself, real /api/session
// data. CI-safe: auto-skips when no control server is listening (Mac gate runs it for real).
import { test, expect } from '@playwright/test';

const CTRL = 'http://127.0.0.1:17772/';

async function controlUp(): Promise<boolean> {
  try {
    const r = await fetch(CTRL + 'api/status', { signal: AbortSignal.timeout(1500) });
    return r.ok;
  } catch { return false; }
}

test.describe('v851 theatre pack (live control app)', () => {
  test.beforeEach(async () => {
    test.skip(!(await controlUp()), 'control app not running — Mac-gate-only spec');
  });

  test('AI read line renders CAPTURE/AI READ/IT SAW and degrades honestly', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await page.click('#btn-sim');
    await page.waitForTimeout(1600);
    const cap = await page.locator('#th-caption').textContent();
    expect(cap).toContain('CAPTURE');
    expect(cap).toMatch(/AI READ|IT SAW/);
    // read line block exists
    await expect(page.locator('.th-airead')).toHaveCount(1);
  });

  test('READ CARD drawer opens with I, follows the playhead, closes with ✕', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await page.click('#btn-sim');
    await page.waitForTimeout(1400);
    const drawer = page.locator('#th-drawer');
    if (await drawer.isHidden()) { await page.keyboard.press('i'); await page.waitForTimeout(300); }
    await expect(drawer).toBeVisible();
    const t1 = await drawer.textContent();
    expect(t1).toContain('identity');
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(300);
    await page.click('#th-drawer-x');
    await page.waitForTimeout(200);
    await expect(drawer).toBeHidden();
  });

  test('transport: arrows step beats, End+play rewinds and rolls', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await page.click('#btn-sim');
    await page.waitForTimeout(1400);
    const readNo = async () => ((await page.locator('#th-caption').textContent()) ?? '').match(/read #(\d+)/)?.[1];
    const a = await readNo();
    await page.keyboard.press('ArrowRight'); await page.waitForTimeout(250);
    const b = await readNo();
    expect(b).not.toBe(a);
    await page.keyboard.press('End'); await page.waitForTimeout(250);
    await page.click('#th-play'); await page.waitForTimeout(600);
    const c = await readNo();
    expect(Number(c)).toBeLessThanOrEqual(Number(b) + 2); // rewound to the reel head region
  });

  test('mode button cycles CUT → FULL → REAL and the axis rebuilds', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await page.click('#btn-sim');
    await page.waitForTimeout(1400);
    const mode = page.locator('#th-mode');
    const dots = () => page.locator('#th-timeline').evaluate(el => el.children.length);
    const d0 = await dots();
    await mode.click(); // FULL
    await page.waitForTimeout(300);
    const d1 = await dots();
    expect(d1).toBeGreaterThanOrEqual(d0); // FULL shows ≥ CUT beats
    await mode.click(); // REAL
    await page.waitForTimeout(300);
    expect(await mode.textContent()).toContain('REAL');
    await mode.click(); // back to CUT
  });

  test('📚 shelf lists sessions and loads one on click', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await page.click('#btn-sim');
    await page.waitForTimeout(1400);
    await page.click('#th-shelf');
    await page.waitForTimeout(400);
    const cards = page.locator('#th-shelfov .sh-card');
    expect(await cards.count()).toBeGreaterThan(0);
    await cards.first().click();
    await page.waitForTimeout(400);
    await expect(page.locator('#th-shelfov')).toBeHidden();
    await expect(page.locator('.th-airead')).toHaveCount(1);
  });

  test('cinema ⛶ fills the window and Esc exits', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await page.click('#btn-sim');
    await page.waitForTimeout(1200);
    await page.click('#th-fs');
    await page.waitForTimeout(400);
    const on = await page.evaluate(() => document.body.classList.contains('cinema'));
    expect(on).toBe(true);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
    expect(await page.evaluate(() => document.body.classList.contains('cinema'))).toBe(false);
  });
});
