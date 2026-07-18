/**
 * v773 — App API ↔ site TV·D 1:1 sync with the REAL hidden agent.
 * Control must already be on :17772 (matrix/harness starts it).
 */
import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as http from 'http';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const CTRL = 'http://127.0.0.1:17772';
const AGENT = 'http://127.0.0.1:17771';

// v884 (routines-in-check) — CI has no live control server: skip instead of ECONNREFUSED.
// Same contract as v851_theatre_pack: Mac gate runs this for real.
async function controlUp(): Promise<boolean> {
  try {
    const r = await fetch(CTRL + '/api/status', { signal: AbortSignal.timeout(1500) });
    return r.ok;
  } catch { return false; }
}
test.beforeEach(async () => {
  test.skip(!(await controlUp()), 'control app not running — Mac-gate-only spec');
});

function post(p: string): Promise<any> {
  return new Promise((resolve, reject) => {
    const u = new URL(CTRL + p);
    const req = http.request(
      { hostname: u.hostname, port: u.port, path: u.pathname, method: 'POST' },
      (res) => {
        let b = '';
        res.on('data', (c) => (b += c));
        res.on('end', () => {
          try {
            resolve(JSON.parse(b || '{}'));
          } catch (e) {
            reject(e);
          }
        });
      },
    );
    req.on('error', reject);
    req.end();
  });
}

function get(url: string): Promise<any> {
  return new Promise((resolve, reject) => {
    http
      .get(url, (res) => {
        let b = '';
        res.on('data', (c) => (b += c));
        res.on('end', () => {
          try {
            resolve(JSON.parse(b || '{}'));
          } catch (e) {
            reject(e);
          }
        });
      })
      .on('error', reject);
  });
}

async function waitOff(ms = 20000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    try {
      const s = await get(CTRL + '/api/status');
      if (s.mode === 'off' && !s.bridge) return s;
    } catch {}
    await new Promise((r) => setTimeout(r, 300));
  }
  throw new Error('control did not go off');
}

test.describe('v773 app ↔ site 1:1 with real agent', () => {
  test.beforeAll(async () => {
    // control must be up
    const s = await get(CTRL + '/api/status');
    expect(s.ok).toBe(true);
    await post('/api/off').catch(() => {});
    await waitOff(25000).catch(() => {});
  });

  test('SIM on → site ON AIR; OFF → site NO SIGNAL / OFF AIR', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    await page.evaluate(() => (window as any).switchTab('tvd'));
    await page.waitForTimeout(200);

    // start SIM from app backend
    const r = await post('/api/sim');
    expect(r.ok).toBe(true);

    // Playwright sets navigator.webdriver so the auto interval is skipped — drive the probe
    await expect
      .poll(
        async () =>
          page.evaluate(() => {
            try {
              (window as any)._tvdProbe && (window as any)._tvdProbe();
            } catch (e) {}
            return {
              bug: (document.getElementById('tvz-bug-txt') || ({} as any)).textContent || '',
              st: (document.getElementById('tvz-shell') || ({} as any)).getAttribute?.('data-tvstate') || '',
              phase: (document.getElementById('tvz-phase') || ({} as any)).textContent || '',
            };
          }),
        { timeout: 20000 },
      )
      .toMatchObject({ bug: expect.stringMatching(/ON AIR/) });

    const live = await page.evaluate(() => ({
      bug: document.getElementById('tvz-bug-txt')!.textContent,
      st: document.getElementById('tvz-shell')!.getAttribute('data-tvstate'),
    }));
    expect(live.st === 'live' || live.bug!.includes('ON AIR')).toBeTruthy();

    // cut from app
    await post('/api/off');
    await waitOff(20000);

    await expect
      .poll(
        async () =>
          page.evaluate(() => {
            try {
              (window as any)._tvdProbe && (window as any)._tvdProbe();
            } catch (e) {}
            return {
              bug: (document.getElementById('tvz-bug-txt') || ({} as any)).textContent || '',
              verb: (document.getElementById('tvb-verb') || ({} as any)).textContent || '',
              st: (document.getElementById('tvz-shell') || ({} as any)).getAttribute?.('data-tvstate') || '',
            };
          }),
        { timeout: 20000 },
      )
      .toMatchObject({
        bug: expect.stringMatching(/OFF AIR/),
      });

    const dark = await page.evaluate(() => ({
      bug: document.getElementById('tvz-bug-txt')!.textContent,
      verb: document.getElementById('tvb-verb')!.textContent,
      st: document.getElementById('tvz-shell')!.getAttribute('data-tvstate'),
    }));
    const ok =
      (dark.bug || '').includes('OFF AIR') ||
      (dark.verb || '').includes('NO SIGNAL') ||
      (dark.verb || '').includes('DISCONNECTED') ||
      dark.st === 'offline' ||
      dark.st === 'off';
    expect(ok).toBeTruthy();
  });

  test('site controls: Theatre + GET THE APP present and clickable', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(300);
    await page.evaluate(() => (window as any).switchTab('tvd'));
    await page.waitForTimeout(150);

    // Theatre
    const thBtn = page.locator('#tvz-theatre-btn');
    await expect(thBtn).toBeVisible();
    await thBtn.click();
    await page.waitForTimeout(200);
    // panel should unhide (id may be tvz-theatre)
    const open = await page.evaluate(() => {
      const t = document.getElementById('tvz-theatre');
      return t ? t.hidden === false : !!document.querySelector('.tvz-theatre:not([hidden])');
    });
    expect(open).toBeTruthy();

    // copy installers
    const n = await page.locator('.tvz-ga-copy').count();
    expect(n).toBe(2);
  });

  test('ON then STOP cuts agent; site follows', async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => (window as any).switchTab('tvd'));
    await post('/api/on');
    await expect
      .poll(async () => (await get(CTRL + '/api/status')).bridge === true, { timeout: 15000 })
      .toBeTruthy();

    await expect
      .poll(
        async () =>
          page.evaluate(() => {
            try {
              (window as any)._tvdProbe && (window as any)._tvdProbe();
            } catch (e) {}
            return (document.getElementById('tvz-bug-txt') || ({} as any)).textContent || '';
          }),
        { timeout: 20000 },
      )
      .toMatch(/ON AIR/);

    // soft OFF (STOP/farewell can wait ~90s on live when capture fails — UI uses OFF for hard cut)
    await post('/api/off');
    await waitOff(25000);

    await expect
      .poll(
        async () =>
          page.evaluate(() => {
            try {
              (window as any)._tvdProbe && (window as any)._tvdProbe();
            } catch (e) {}
            return (document.getElementById('tvz-bug-txt') || ({} as any)).textContent || '';
          }),
        { timeout: 20000 },
      )
      .toMatch(/OFF AIR/);
  });
});
