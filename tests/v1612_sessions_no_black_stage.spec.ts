import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1612 — SESSIONS MUST NEVER SHOW AN EMPTY FILM STAGE.
//
// Konyo, after a night of "still a black screen when trying to record": "i think i know what that
// blackscreen is.. its in sessions.. while the TV-D is actually working ... the Sessions tab is like
// falsely showing the AI screenrecording? or it needs to be surgically removed in that specific tab?"
//
// He was right. Sessions hides the stage via
//     body[data-view="sessions"]:not(.theatre-open) .stage { display: none !important; }
// so the moment ANYTHING sets theatre-open, that exception fires and a 1090x694 stage appears
// wrapping #th-film — whose src is (none) and naturalWidth 0. A large empty element on a dark page
// IS a black screen, and it sits exactly where he expects the live feed, so it reads as "recording
// is broken" while the cockpit is working perfectly.
//
// The fix is the v1380.5 separation one level up: Sessions is the hunt hub and owns no film
// surface, so opening the theatre leaves Sessions first.

const ORIGIN = 'http://tvd.console.test';
const UI = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

async function open(page: any) {
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname === '/api/sessions', (r: any) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ sessions: [] }) }));
  await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/sessions',
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1600);
}

const stageOf = (page: any) => page.evaluate(() => {
  const st = document.querySelector('.stage') as HTMLElement | null;
  const film = document.getElementById('th-film') as HTMLImageElement | null;
  const r = st ? st.getBoundingClientRect() : null;
  return {
    view: document.body.getAttribute('data-view'),
    display: st ? getComputedStyle(st).display : 'absent',
    area: r ? Math.round(r.width * r.height) : 0,
    filmSrc: film ? (film.getAttribute('src') || '') : '',
    filmNatural: film ? film.naturalWidth : -1,
  };
});

test.describe('v1612 — the hunt hub never shows a bare film stage', () => {
  test('the stage is hidden on Sessions at rest', async ({ page }) => {
    await open(page);
    const s = await stageOf(page);
    expect(s.view).toBe('sessions');
    expect(s.display).toBe('none');
  });

  test('★ ON AIR alone does not open a stage on Sessions', async ({ page }) => {
    await open(page);
    await page.evaluate(() => document.body.setAttribute('data-state', 'on'));
    await page.waitForTimeout(300);
    const s = await stageOf(page);
    expect(s.display, 'going live must not unhide a film surface the hunt hub does not own')
      .toBe('none');
  });

  test('★★ thOpen() routes off Sessions before it unhides anything', async ({ page }) => {
    // thOpen is a module-local function, not on window, so this asserts the ROUTING EXISTS in the
    // code path rather than pretending to invoke it from outside. The behavioural guarantee — that
    // no black stage can appear whatever opens the theatre — is the regression test below, which
    // forces the worst case directly and does not care how it was reached.
    await open(page);
    const src = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');
    const fn = src.slice(src.indexOf('async function thOpen()'), src.indexOf('async function thOpen()') + 1600);
    expect(fn, 'thOpen must leave Sessions before opening, or the reel opens on a view that has no stage')
      .toMatch(/data-view'\)\s*===\s*'sessions'/);
    expect(fn).toContain('_shellHome');
  });

  test('★ THE REGRESSION: no large stage may be visible while the film has no source', async ({ page }) => {
    // This is the property that actually matters, independent of HOW the stage got opened: a big
    // visible stage wrapped around an empty <img> is, to the eye, a black screen.
    await open(page);
    await page.evaluate(() => {
      document.body.setAttribute('data-state', 'on');
      document.body.classList.add('theatre-open');   // force the worst case directly
    });
    await page.waitForTimeout(400);
    const s = await stageOf(page);
    const blackBox = s.view === 'sessions' && s.display !== 'none'
                     && s.area > 200000 && !s.filmSrc;
    expect(blackBox,
      `a ${s.area}px stage is visible on Sessions with film src="${s.filmSrc}" — that is the black ` +
      'screen he reported for hours while the cockpit was recording perfectly').toBe(false);
  });
});
