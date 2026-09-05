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

// v2671 — #btn-sim IS HIDDEN BY DESIGN, so page.click() can never reach it.
//
// v2438 made THE SHELF the single door and hid Theatre's button with the `hidden`
// attribute, keeping "its id, its class, its title and its handler ... so every existing
// binding and spec still finds it". That promise holds for querySelector and NOT for a
// click: Playwright waits for the element to be visible, and the console's own CSS says
// `button.act[hidden] { display: none !important; }`. Measured on CI run 33968788226 —
//
//     Error: page.click: Test timeout of 120000ms exceeded.
//       - locator resolved to <button hidden="" id="btn-sim" ...>
//       - element is not visible
//
// — so each of these burned the full 120 s before failing. That is the whole cost of this
// suite's red.
//
// These tests are about SIM/Theatre BEHAVIOUR (toggling, keyboard, scrubbing), not about
// how the door is painted, so they invoke the button's OWN handler — the one v2438 says it
// kept. `window._dossierToTheatre()` is the Shelf's route and only OPENS; these assertions
// need click-to-open AND click-to-close, so the element's click() is the faithful call.
//
// ⚠ WHAT THIS DELIBERATELY DOES NOT COVER: the real user path (Shelf -> "▶ Open in
// Theatre"). Nothing here would notice if that door broke. It wants its own spec.
async function simToggle(page: any) {
  await page.$eval('#btn-sim', (el: any) => el.click());
}

test.describe('v851 theatre pack (live control app)', () => {
  test.beforeEach(async () => {
    test.skip(!(await controlUp()), 'control app not running — Mac-gate-only spec');
  });

  // v918.4 — the reel now interleaves FOOTAGE + 📸 INTAKE beats with reads, and the theatre
  // parks on the LAST beat (often an intake). The read-line assertions are about READ beats:
  // navigate to one first instead of asserting wherever the playhead happens to sit.
  const gotoReadBeat = async (page: any) => {
    await page.keyboard.press('Home');
    await page.waitForTimeout(250);
    for (let i = 0; i < 40; i++) {
      const cap = (await page.locator('#th-caption').textContent()) || '';
      if (cap.includes('CAPTURE')) return cap;
      await page.keyboard.press('ArrowRight');
      await page.waitForTimeout(150);
    }
    return (await page.locator('#th-caption').textContent()) || '';
  };

  test('AI read line renders CAPTURE/AI READ/IT SAW and degrades honestly', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await simToggle(page);
    await page.waitForTimeout(1600);
    const cap = await gotoReadBeat(page);
    expect(cap).toContain('CAPTURE');
    expect(cap).toMatch(/AI READ|IT SAW/);
    // read line block exists
    await expect(page.locator('.th-airead')).toHaveCount(1);
  });

  test('READ CARD drawer opens with I, follows the playhead, closes with ✕', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await simToggle(page);
    await page.waitForTimeout(1400);
    await gotoReadBeat(page);   // v918.4 — 'identity' lives on READ cards; intake beats show the tally table
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
    await simToggle(page);
    await page.waitForTimeout(1400);
    // v859.1 — footage-heavy reels have beats with no 'read #'; track the beat index instead
    const beatNo = async () => Number((((await page.locator('#th-sess').textContent()) ?? '').match(/beat (\d+)\//) || [])[1] || 0);
    const a = await beatNo();
    await page.keyboard.press('ArrowRight'); await page.waitForTimeout(250);
    const b = await beatNo();
    expect(b).toBe(a + 1);
    await page.keyboard.press('End'); await page.waitForTimeout(250);
    await page.click('#th-play'); await page.waitForTimeout(600);
    const c = await beatNo();
    expect(c).toBeLessThanOrEqual(b + 2); // End+play rewound to the reel head region
  });

  test('mode button cycles CUT → FULL → REAL and the axis rebuilds', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await simToggle(page);
    await page.waitForTimeout(1400);
    // v918.4 — default-agnostic: v896 made ⏱ REAL the debugger default, so blind clicks land
    // wherever the cycle starts. Assert the CYCLE (3 distinct labels, wraps to start) and the
    // axis truth (CUT is the smallest reel — FULL/REAL play ≥ the highlight cut).
    const mode = page.locator('#th-mode');
    const dots = () => page.locator('#th-timeline').evaluate(el => el.children.length);
    const seen: Record<string, number> = {};
    const l0 = ((await mode.textContent()) || '').trim();
    seen[l0] = await dots();
    for (let i = 0; i < 2; i++) {
      await mode.click();
      await page.waitForTimeout(300);
      seen[((await mode.textContent()) || '').trim()] = await dots();
    }
    expect(Object.keys(seen).length).toBe(3);   // CUT · FULL · REAL all reachable
    const labels = Object.keys(seen);
    const cut = labels.find(l => l.includes('CUT')), full = labels.find(l => l.includes('FULL')), real = labels.find(l => l.includes('REAL'));
    expect(cut && full && real).toBeTruthy();
    expect(seen[full!]).toBeGreaterThanOrEqual(seen[cut!]);
    expect(seen[real!]).toBeGreaterThanOrEqual(seen[cut!]);
    await mode.click(); // wrap back to where the viewer started
    await page.waitForTimeout(200);
    expect(((await mode.textContent()) || '').trim()).toBe(l0);
  });

  test('📚 shelf lists sessions and loads one on click', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await simToggle(page);
    await page.waitForTimeout(1400);
    await page.click('#th-shelf');
    await page.waitForTimeout(400);
    // v2199 — :visible, and the count is of VISIBLE cards. The shelf now hides empty ghost runs
    // by default (2,261 of his 2,461), and the first card in DOM order is session n=1, which on
    // his machine IS a ghost. locator.count() ignores visibility so the assertion passed, and then
    // .first().click() waited for actionability on a display:none node and timed out — RED on the
    // Mac gate, and SKIPPED in CI because nothing listens on 17772 there. A skip is not a pass.
    const cards = page.locator('#th-shelfov .sh-card:visible');
    expect(await cards.count(),
      'no VISIBLE shelf cards — the ghost filter is hiding everything, or the shelf did not open')
      .toBeGreaterThan(0);
    await cards.first().click();
    await page.waitForTimeout(400);
    await expect(page.locator('#th-shelfov')).toBeHidden();
    await gotoReadBeat(page);   // v918.4 — the loaded reel may park on footage/intake; the read line lives on READ beats
    await expect(page.locator('.th-airead')).toHaveCount(1);
  });

  test('cinema ⛶ fills the window and Esc exits', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await simToggle(page);
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
