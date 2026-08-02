import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1547 — 🌀 THE TERROR ZONE, IN THE CONSOLE.
//
// Konyo: "i DONT see the TZ tracker anywhere within the console."
//
// He was right, and precisely so: control_ui.html had ZERO TZ references. The relay has existed
// since v944 — /api/tz proxies the live Pages function through the site's gate, caches 90s, and
// serves the last good rotation flagged `stale` when upstream dies — but it existed so the BOARD
// served at /board could reach it. Nothing in the console itself ever rendered it.
//
// What these tests hold is the honesty, not the layout: stale is never dressed as live, an
// unreachable relay says so instead of showing an empty pair of slots, and the hunt-or-skip verdict
// is NOT duplicated here — it lives in bible.html's tzHuntMatch, and one copy is the whole point.

const ORIGIN = 'http://tvd.console.test';
const UI_HTML = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

async function open(page: any, payload: any, status = 200) {
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI_HTML }));
  await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/tz',
    (r: any) => r.abort());
  await page.route((u: URL) => u.pathname === '/api/tz', (r: any) =>
    payload === null ? r.abort()
      : r.fulfill({ status, contentType: 'application/json', body: JSON.stringify(payload) }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  // v1589 — THE PANEL LIVES IN SESSIONS ONLY. Konyo: "remove it completely from TV-D tab.. i want
  // it only in sessions". It was rendering 419px tall in the cockpit as well, so it is now
  // display:none outside the Sessions view. This helper loads the console standalone (every /api/
  // but /api/tz is aborted), which lands on the cockpit — so the view has to be set, or every
  // assertion below is measuring a hidden element. Setting the attribute rather than calling
  // _showSessions() is deliberate: showSessions() reaches for endpoints this harness aborts, and
  // what these tests need is exactly the CSS contract the attribute drives.
  await page.evaluate(() => document.body.setAttribute('data-view', 'sessions'));
  await page.waitForTimeout(700);
}

const LIVE = { current: 'The Secret Cow Level', next: 'Travincal', ts: Date.now() };

test.describe('v1547 — the rotation, in the console', () => {
  test('★ the panel EXISTS at all — the thing he could not find', async ({ page }) => {
    await open(page, LIVE);
    expect(await page.locator('#hd-tz').count(), 'there must be a Terror Zone panel').toBe(1);
    expect(await page.isHidden('#hd-tz')).toBe(false);
  });

  test('★ and it is hidden OUTSIDE Sessions — the cockpit is not its home', async ({ page }) => {
    // the other half of v1589. Without this, "Sessions only" is enforced by nothing and the panel
    // could drift back into the cockpit the next time someone touches the grid.
    await open(page, LIVE);
    expect(await page.isHidden('#hd-tz'), 'it must be visible in Sessions').toBe(false);
    await page.evaluate(() => document.body.removeAttribute('data-view'));
    await page.waitForTimeout(120);
    expect(await page.isHidden('#hd-tz'),
      'the rotation must NOT render in the cockpit — that view is the live feed').toBe(true);
  });

  test('★ live now and next are both named', async ({ page }) => {
    await open(page, LIVE);
    const txt = (await page.textContent('#tz-body')) || '';
    expect(txt).toContain('The Secret Cow Level');
    expect(txt).toContain('Travincal');
    expect(txt).toContain('LIVE NOW');
    expect(txt).toContain('NEXT');
  });

  test('★ STALE IS NEVER DRESSED AS LIVE', async ({ page }) => {
    // v944's relay already flags it; blurring that into "live" is how a tracker starts lying, and a
    // wrong zone sends him to farm somewhere the terror is not.
    await open(page, { ...LIVE, stale: true });
    const txt = (await page.textContent('#tz-body')) || '';
    expect(txt).toContain('LAST GOOD rotation');
    expect(txt).toContain('not the current one');
    expect(await page.textContent('#tz-updated')).toContain('stale');
    expect(await page.locator('.tz-stale').count()).toBe(1);
  });

  test('a fresh rotation carries no stale warning and no amber', async ({ page }) => {
    await open(page, LIVE);
    expect(await page.locator('.tz-stale').count()).toBe(0);
    expect(await page.locator('.tz-down').count()).toBe(0);
    expect(await page.textContent('#tz-updated')).not.toContain('stale');
  });

  test('★ an unreachable relay SAYS SO rather than showing empty slots', async ({ page }) => {
    await open(page, { error: 'tz upstream unreachable: timed out' }, 502);
    const txt = (await page.textContent('#tz-body')) || '';
    expect(txt).toContain('no rotation available');
    expect(txt).toContain('unreachable');
    expect(await page.locator('.tz-slot').count(), 'no invented LIVE NOW row').toBe(0);
  });

  test('a dead fetch is handled without blanking the panel', async ({ page }) => {
    await open(page, null);
    expect(await page.locator('#hd-tz').count()).toBe(1);
    expect((await page.textContent('#tz-body')) || '').toContain('no rotation available');
  });

  test('★ the hunt-or-skip verdict is NOT duplicated into the console', async ({ page }) => {
    // tzHuntMatch lives in bible.html. A second copy here is a second thing to drift the next time
    // a zone is reclassified — so the console reports the rotation and hands off for the verdict.
    const src = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');
    // Target a DEFINITION, not a mention — the first version of this grepped for the bare name and
    // caught the comment that explains why the name is not implemented here.
    expect(src, 'the console must not define its own hunt matcher')
      .not.toMatch(/function\s+tzHuntMatch|tzHuntMatch\s*=\s*function|const\s+tzHuntMatch/);
    expect(src, 'nor carry its own list of hunt zones')
      .not.toMatch(/TZ_HUNT|HUNT_ZONES|huntZones\s*=/);
    await open(page, LIVE);
    expect(await page.locator('#tz-open').count(), 'it hands off to the board instead').toBe(1);
  });

  test('the panel is wired to the relay the console already had', async ({ page }) => {
    const hits: string[] = [];
    await page.route(ORIGIN + '/ui', (r: any) =>
      r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI_HTML }));
    await page.route((u: URL) => u.pathname.startsWith('/api/'), (r: any) => {
      const p = new URL(r.request().url()).pathname;
      if (p === '/api/tz') {
        hits.push(p);
        return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(LIVE) });
      }
      return r.abort();
    });
    await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(700);
    expect(hits, 'it must use /api/tz — the v944 relay, not a new endpoint').toContain('/api/tz');
  });

  test('↻ refresh re-asks', async ({ page }) => {
    let n = 0;
    await page.route(ORIGIN + '/ui', (r: any) =>
      r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI_HTML }));
    await page.route((u: URL) => u.pathname.startsWith('/api/'), (r: any) => {
      const p = new URL(r.request().url()).pathname;
      if (p !== '/api/tz') return r.abort();
      n += 1;
      return r.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ ...LIVE, current: 'zone ' + n }),
      });
    });
    await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
    // v1589 — this test builds its OWN routes instead of using open(), so it never got the
    // Sessions view the helper now sets — and the panel (with its ↻ button) is display:none in the
    // cockpit. The click timed out on an invisible button for 3 minutes before failing.
    await page.evaluate(() => document.body.setAttribute('data-view', 'sessions'));
    await page.waitForTimeout(700);
    const before = n;
    await page.click('#tz-refresh');
    await page.waitForTimeout(500);
    expect(n).toBeGreaterThan(before);
    expect((await page.textContent('#tz-body')) || '').toContain('zone ' + n);
  });

  test('a rotation missing its NEXT still shows what it does know', async ({ page }) => {
    await open(page, { current: 'Travincal', ts: Date.now() });
    const txt = (await page.textContent('#tz-body')) || '';
    expect(txt).toContain('Travincal');
    // v1585 — the wording changed on purpose and the INTENT is unchanged: an absent NEXT must be
    // NAMED, never left blank. It used to say "(unknown)", which was true and read like a broken
    // panel — the upstream really does return next:"" for part of every slot, so this is a normal
    // state, not a fault. It now says which of the two it is.
    expect(txt, 'an absent next must be named, not left blank').toContain('not published yet');
  });
});
