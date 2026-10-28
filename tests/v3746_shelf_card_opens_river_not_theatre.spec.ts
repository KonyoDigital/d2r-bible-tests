import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v3746 / REG-2253 (#58) — THE SHELF CARD OPENS THE RIVER DIRECTLY, NEVER AN EMPTY THEATRE.
//
// GrokBot #6201414317 (console v3742): 8 Shelf -> Theatre tries, quick reopens 1.5-6s apart, and
// on the fast reopens the Shelf card painted an EMPTY "SESSION 1 · PAST REPLAY" Theatre (black
// film) before the River gallery replaced it. His ask: the Shelf card opens the River directly,
// no Theatre in between.
//
// THE MECHANISM: #btn-shelf's handler does `TH.shelfAsDoor = true; await thOpen(); thShelf(true)`.
// thOpen (v859) opens the black stage shell SYNCHRONOUSLY, then AWAITS /api/sessions (up to an 8s
// cap). #th-shelfov — the opaque overlay that IS the River surface — was unhidden only by the
// handler's thShelf(true), which runs AFTER that await resolves. So for the whole fetch the bare
// black stage was visible; on a fast reopen that is the empty Theatre he saw.
//
// THE FIX pins here: thOpen, in the same synchronous tick it opens the shell and BEFORE it awaits
// the network, covers the stage with #th-shelfov (a lightweight loading cover, not a second
// thShelf builder) when it is opening as a door. The browser then never paints an empty-Theatre
// frame. These tests hold /api/sessions open to make that window observable and deterministic.

const ORIGIN = 'http://tvd.console.test';
const UI = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

// Real-shaped sessions so a river can build. The assertions never read card internals — only that
// the shelf OVERLAY covers the stage, so an empty sessions array would prove the same point.
const SESSIONS = {
  sessions: [
    { n: 1, sessionId: 's1', t0: 1700000000000, t1: 1700000600000, reads: 12, footageN: 8, footageState: 'present' },
    { n: 2, sessionId: 's2', t0: 1700001000000, t1: 1700001600000, reads: 9, footageN: 5, footageState: 'present' },
  ],
};

// Hold /api/sessions open by `delayRef.ms` so the shell-open-vs-shelf-paint window is observable.
async function boot(page: any, delayRef: { ms: number }) {
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname === '/api/sessions', async (r: any) => {
    if (delayRef.ms > 0) await new Promise((res) => setTimeout(res, delayRef.ms));
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(SESSIONS) });
  });
  await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/sessions',
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1600);
}

// Click the real door and, the INSTANT the theatre shell opens, read whether the River overlay is
// up over it. The RED/GREEN difference is purely "is #th-shelfov hidden at the moment the theatre
// first opens as a door": thOpen sets theatre-open SYNCHRONOUSLY, so the fix's cover (also
// synchronous) is already applied by the next frame, while the delayed fetch keeps any later paint
// out of the window. The click is RETRIED only while it is SAFE — a click while the door is opening
// or open would hit its toggle and close it (render_check v2795/v3124) — so a first click that
// lands before the handler binds does not fail the whole read.
async function openAndReadAtShellOpen(page: any) {
  return await page.evaluate(() => new Promise<any>((resolve) => {
    const t0 = Date.now();
    (function poll() {
      const th = document.getElementById('theatre') as HTMLElement | null;
      const open = !!(document.body.classList.contains('theatre-open') && th && !th.hidden);
      if (open) {
        const ov = document.getElementById('th-shelfov') as HTMLElement | null;
        const r = ov ? ov.getBoundingClientRect() : null;
        resolve({
          theatreOpen: true,
          shelfHidden: ov ? !!ov.hidden : null,
          overlayArea: r ? Math.round(r.width * r.height) : 0,
        });
        return;
      }
      const TH: any = (window as any).TH || {};
      if (!TH.shelfOpening && !TH.open) {
        const b = document.getElementById('btn-shelf') as HTMLElement | null;
        if (b && b.click) b.click();
      }
      if (Date.now() - t0 > 4000) {
        resolve({ theatreOpen: false, shelfHidden: null, overlayArea: 0 });
        return;
      }
      requestAnimationFrame(poll);
    })();
  }));
}

test.describe('v3746 — THE SHELF card opens the River directly, never an empty Theatre', () => {
  test('★★ one Shelf-card click shows the River over the stage, not a bare Theatre', async ({ page }) => {
    const delayRef = { ms: 0 };
    await boot(page, delayRef);
    delayRef.ms = 2500; // hold /api/sessions open — this is the wait he stared at a black stage through
    const s: any = await openAndReadAtShellOpen(page);
    expect(s.theatreOpen, 'clicking THE SHELF must open the theatre shell').toBe(true);
    expect(s.shelfHidden,
      'the theatre opened as a door but #th-shelfov (the River) was still hidden — that bare black ' +
      '"SESSION 1 · PAST REPLAY" stage is the empty Theatre #58 is about').toBe(false);
    expect(s.overlayArea,
      'the River overlay is unhidden but occupies no pixels — a flag flip is not a surface he can ' +
      'see (this file\'s v2666 scar: prove it from the RECT)').toBeGreaterThan(0);
  });

  test('★★ a fast reopen (close, then reopen in the race window) still shows the River', async ({ page }) => {
    const delayRef = { ms: 0 };
    await boot(page, delayRef);

    // open #1 — a quick /api/sessions, and let it fully settle so the door toggle is released,
    // exactly as a real reopen does (he reopens AFTER the shelf has shown).
    delayRef.ms = 200;
    await openAndReadAtShellOpen(page);
    await page.waitForFunction(() => {
      const ov = document.getElementById('th-shelfov') as HTMLElement | null;
      const TH: any = (window as any).TH || {};
      return !!(ov && !ov.hidden) && !TH.shelfOpening;
    });

    // close it, and reopen INSIDE the race window (a now-slow /api/sessions)
    await page.evaluate(() => { const w: any = window; if (w.thClose) w.thClose(); });
    await page.waitForFunction(() => {
      const ov = document.getElementById('th-shelfov') as HTMLElement | null;
      return !ov || ov.hidden;
    });

    delayRef.ms = 2500;
    const s: any = await openAndReadAtShellOpen(page);
    expect(s.theatreOpen, 'the reopen must open the theatre shell again').toBe(true);
    expect(s.shelfHidden,
      'on the fast reopen the theatre opened as a door but the River overlay was hidden — the empty ' +
      'Theatre flashes exactly on these quick reopens (GrokBot #6201414317: 8 tries, 1.5-6s apart)')
      .toBe(false);
  });

  test('★ the cover is in thOpen BEFORE the network wait, not only in the handler after it', async () => {
    // Source pin for the behavioural tests above: the empty-Theatre window existed only because the
    // River overlay was unhidden AFTER `await thOpen()` resolved. thOpen's own shell-open section —
    // everything before it awaits /api/sessions — must now touch #th-shelfov so the door covers the
    // stage immediately. A revert to a handler-only paint would make the timing tests flaky; this
    // stays deterministic and names the exact seam.
    const src = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');
    const i = src.indexOf('async function thOpen()');
    expect(i, 'thOpen is gone — re-point this law').toBeGreaterThan(-1);
    // REG-2698 - thOpen's /api/sessions wait is thSessionsWait (bounded at 45 s, says it is waiting); thOpen awaits it here
    const wait = src.indexOf("j = await thSessionsWait(", i);
    expect(wait, 'thOpen no longer awaits /api/sessions — re-point this law').toBeGreaterThan(i);
    const preWait = src.slice(i, wait);
    expect(preWait,
      'thOpen does not touch #th-shelfov before it awaits the network, so the shelf door still paints ' +
      'the River only after the fetch — the empty-Theatre window is unfixed')
      .toContain('th-shelfov');
    expect(preWait,
      'the early cover is not gated on the shelf-door case (_shelfDoor), so it would fire for a reel too')
      .toContain('_shelfDoor');
  });
});
