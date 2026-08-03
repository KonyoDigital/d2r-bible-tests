import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1627 — GOING LIVE MEANS GOING WHERE THE FILM IS.
//
// Konyo: "when i click on mini air or ON AIR it like needs to aoutmatically route me to the TV-D
// and also for THEATRE MODE like close theatre mode and theathre mode need to route me to the
// relevant cell related. because its also a black screen like before when we had the routing/bug".
//
// v1612 stopped Sessions from unhiding an EMPTY stage, with
// `body.theatre-open:not([data-view="sessions"]) .stage`. v1612 also taught thOpen to call
// _shellHome() when on Sessions — and _shellHome EXISTS, so that guard fires. What it does not do
// is clear `data-view`, and data-view is precisely what the selector tests. The attribute survived
// the navigation, the selector kept matching, the stage stayed hidden: a black screen with a
// perfectly healthy film behind it. ON AIR and MINI never navigated at all.

const ORIGIN = 'http://tvd.console.test';
const REPO = path.resolve(__dirname, '..');
const UI = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');

async function onSessions(page: any) {
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname.startsWith('/art/'), (r: any) => r.fulfill({ status: 404, body: '' }));
  await page.route((u: URL) => u.pathname.startsWith('/api/'),
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1800);
  await page.evaluate(() => { try { (window as any).showSessions(); } catch (e) {} });
  await page.waitForTimeout(400);
}

test.describe('v1627 — the live controls go where the film is', () => {
  test('★★★ _toTVD clears data-view — the attribute the stage rule keys on', async ({ page }) => {
    await onSessions(page);
    const before = await page.evaluate(() => document.body.getAttribute('data-view'));
    expect(before, 'the test must actually start on Sessions').toBe('sessions');
    const after = await page.evaluate(() => {
      (window as any)._toTVD();
      return document.body.getAttribute('data-view');
    });
    expect(after, 'shellHome() alone left this set, so the stage stayed hidden').toBeNull();
  });

  test('★★★ with data-view cleared, the theatre stage is no longer display:none', async ({ page }) => {
    /* The whole bug in one assertion: same DOM, same film, the ONLY difference is the attribute. */
    await onSessions(page);
    const r = await page.evaluate(() => {
      const st: any = document.querySelector('.stage');
      document.body.classList.add('theatre-open');
      const onSessionsDisplay = getComputedStyle(st).display;
      (window as any)._toTVD();
      document.body.classList.add('theatre-open');   // _toTVD may restore the console view
      const afterDisplay = getComputedStyle(st).display;
      return { onSessionsDisplay, afterDisplay };
    });
    expect(r.onSessionsDisplay, 'on Sessions the stage is correctly hidden').toBe('none');
    expect(r.afterDisplay, 'and once we have left Sessions it must be visible').not.toBe('none');
  });

  test('★★ every live control routes, and _backFromLive returns him', async ({ page }) => {
    await onSessions(page);
    const api = await page.evaluate(() => ({
      toTVD: typeof (window as any)._toTVD,
      back: typeof (window as any)._backFromLive,
      showSessions: typeof (window as any).showSessions,
    }));
    // the guard-with-no-symbol class: thClose/thOpen name these, so they must exist
    expect(api.toTVD).toBe('function');
    expect(api.back).toBe('function');

    const round = await page.evaluate(() => {
      (window as any)._toTVD();                       // leaves Sessions, remembering it
      const away = document.body.getAttribute('data-view');
      (window as any)._backFromLive();                // and puts him back
      return { away, home: document.body.getAttribute('data-view') };
    });
    expect(round.away).toBeNull();
    expect(round.home, 'closing the film returns him to the surface he opened it from').toBe('sessions');
  });

  test('★★ ON AIR and MINI both call it — and MINI only after the engine accepts', async () => {
    const air = UI.slice(UI.indexOf("post('/api/on', this, e);") - 400, UI.indexOf("post('/api/on', this, e);") + 40);
    expect(air, 'ON AIR must route before posting').toContain('_toTVD()');
    // MINI's call must sit AFTER the refusal branch, or a "disk too full" moves him for nothing
    const mini = UI.slice(UI.indexOf("$('btn-mini').onclick"), UI.indexOf("$('btn-mini').onclick") + 2600);
    const refusalAt = mini.indexOf('mini could not start');
    const routeAt = mini.indexOf('_toTVD()');
    expect(routeAt, 'MINI must route').toBeGreaterThan(-1);
    expect(routeAt, 'but only past the refusal, so a rejected run leaves him reading the reason')
      .toBeGreaterThan(refusalAt);
  });
});
