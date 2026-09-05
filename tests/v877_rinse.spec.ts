// v877 — THE RINSE, PERMANENT (Konyo Workflow step 12: 'RINSE as permanent spec').
// The 13-point user-experience matrix that used to live as a scratchpad driver: every console
// button both directions, keyboard matrix, rapid-fire stress — now SELF-HOSTED so CI runs it
// unconditionally: the spec boots its OWN control server (private port, fixture journal via
// TV_SESSIONS) and never touches a live console on :17772.
// v1754 — through the shared net stub, so this spec's measurements do not depend on the
// runner reaching fonts.googleapis.com. bible.html makes exactly FIVE external requests and
// all five are fonts; stubbing them removes the whole external surface.
//
// ⚠ NOT because a failed font collapses this layout — I checked, and it does not. Measured
// three ways, .set-card-header is 78px ONLINE, 78px OFFLINE and 78px STUBBED. The v1749
// note on _net_stub says a font failure makes that bar 0px; offline does not reproduce it,
// and the flake it was written about turned out to be a blind toggleCardCollapse leaving
// the card COLLAPSED (fixed in v1751, proven by forcing .collapsed). The honest reason to
// stub here is determinism, not a defect anyone has shown. [[inherited_claim_is_not_evidence]]
import { test, expect } from './_net_stub';
import { spawn, ChildProcess } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const PORT = 17962;
const CTRL = `http://127.0.0.1:${PORT}/`;
let server: ChildProcess | null = null;

// v1459 — a real 32×32 JPEG (SOI ff d8 ff). The fixture must put ACTUAL film on disk: /api/session
// only returns a beat with `frame` when hist/<frameId>.jpg exists, and the theatre refuses to paint a
// filmless session ("this session has no screenshots"). Without these bytes TH.beats stayed 0, so
// Space had nothing to play and the caption never said "read #N" — the two rinse specs were asserting
// film behaviour against a session with no film.
const TINY_JPEG_B64 =
  '/9j/4AAQSkZJRgABAQAASABIAAD/wAARCAAgACADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAA' +
  'AAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0Kx' +
  'wRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4' +
  'eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl' +
  '5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQD' +
  'BAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygp' +
  'KjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOk' +
  'paanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9sAQwAEBAQE' +
  'BAQGBAQGCQYGBgkMCQkJCQwPDAwMDAwPEg8PDw8PDxISEhISEhISFRUVFRUVGRkZGRkcHBwcHBwcHBwc' +
  '/9sAQwEEBQUHBwcMBwcMHRQQFB0dHR0dHR0dHR0dHR0dHR0dHR0dHR0dHR0dHR0dHR0dHR0dHR0dHR0d' +
  'HR0dHR0dHR0d/90ABAAC/9oADAMBAAIRAxEAPwDhaKKK/PT9WCiiigD/0OFooor89P1YKKKKAP/Z';

// journal + the matching hist frames, in one temp dir the server owns via TV_SESSIONS + TV_HIST
function fixtureRun(): { journal: string; hist: string } {
  const dir = mkdtempSync(join(tmpdir(), 'tvd-rinse-'));
  const p = join(dir, 'sessions.jsonl');
  const hist = join(dir, 'hist');
  mkdirSync(hist, { recursive: true });
  const jpg = Buffer.from(TINY_JPEG_B64, 'base64');
  const t0 = 1784400000000;
  const sid = 's_rinse_1';
  const rows = [] as string[];
  for (let i = 1; i <= 6; i++) {
    const fid = `${i}_${t0 + i * 9000}`;
    writeFileSync(join(hist, `${fid}.jpg`), jpg);   // the film this read was made from
    rows.push(JSON.stringify({
      ts: t0 + i * 9000, captureTs: t0 + i * 9000, completedTs: t0 + i * 9000 + 6000,
      names: i % 2 ? ['Perfect Ruby', `${100 + i} Gold`] : [],
      n: i, area: 'Rinse Plains', scene: 'gameplay', tz: [], ms: 6000,
      mode: 'warm', lane: 'deep', model: 'sonnet', conf: 0.9, intent: 'context',
      stashTab: '', frameId: fid, sessionId: sid,
      escalated: false, interest: 0.7, priority: false, provisional: false,
    }));
  }
  rows.push(JSON.stringify({ ts: t0 + 70000, sessionId: sid, sessionEnd: true, n: 7 }));
  writeFileSync(p, rows.join('\n') + '\n');
  return { journal: p, hist };
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

test.describe('v877 RINSE (self-hosted console)', () => {
  test.beforeAll(async () => {
    // v1379 — MUST pass --no-open. Without it control_app opens a pywebview window
    // (blocks / steals focus / flakes in CI) and the rinse suite was timing out on
    // every keyboard/arrow assertion waiting for a stable #btn-sim.
    const fx = fixtureRun();
    server = spawn('python3', ['tv/control_app.py', '--no-open'], {
      env: {
        ...process.env,
        TV_CONTROL_PORT: String(PORT),
        TV_PORT: '17961',
        TV_SESSIONS: fx.journal,
        TV_HIST: fx.hist,   // v1459 — isolate hist to the fixture's own film (never Konyo's real reels)
      },
      stdio: 'ignore',
    });
    // wait for the server
    for (let i = 0; i < 40; i++) {
      try {
        const r = await fetch(CTRL + 'api/status', { signal: AbortSignal.timeout(900) });
        if (r.ok) return;
      } catch {}
      await new Promise((r) => setTimeout(r, 500));
    }
    throw new Error('rinse control server never came up');
  });

  test.afterAll(async () => {
    try { server?.kill('SIGKILL'); } catch {}
  });

  const state = (page: any) => page.evaluate(() => ({
    body: document.body.getAttribute('data-state'),
    theatre: !(document.getElementById('theatre') as any).hidden,
    drawer: !(document.getElementById('th-drawer') as any).hidden,
    cinema: document.body.classList.contains('cinema'),
    playing: document.getElementById('th-play')?.textContent || '',
  }));

  test('SIM toggles idempotently ×3 rapid', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    for (let i = 0; i < 3; i++) {
      await simToggle(page);
      await page.waitForTimeout(700);
      expect((await state(page)).theatre, `open round ${i}`).toBe(true);
      await simToggle(page);
      await page.waitForTimeout(500);
      expect((await state(page)).theatre, `close round ${i}`).toBe(false);
    }
  });

  test('Space plays/pauses the reel and NEVER touches the agent', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await simToggle(page);
    await page.waitForTimeout(1000);
    // v1459 — assert the PREMISE first with a number. When the fixture shipped no film, TH.beats was
    // 0 and this spec failed on the play-button label, which reads like a keyboard bug and is not one.
    const beats = await page.evaluate(() => ((window as any).TH?.beats || []).length);
    expect(beats, 'fixture must load real film before Space can play it').toBeGreaterThan(0);
    const before = await state(page);
    await page.keyboard.press('Space');
    await page.waitForTimeout(350);
    const after = await state(page);
    expect(after.playing).not.toBe(before.playing);
    expect(after.body).toBe(before.body);   // v859 doctrine: theatre owns Space
  });

  test('arrows single-step, Home/End clamp, ✕ closes the drawer', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await simToggle(page);
    await page.waitForTimeout(1000);
    const readNo = async () =>
      ((await page.locator('#th-caption').textContent().catch(() => '')) || '').match(/read #(\d+)/)?.[1] || null;
    await page.keyboard.press('Home');
    await page.waitForTimeout(300);
    const r0 = await readNo();
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(300);
    const r1 = await readNo();
    // v1459 — r0 null used to mean "no film in the fixture", not "arrows are broken". Say which.
    expect(r0, 'caption must name a read (film loaded?) before arrows can step it').not.toBe(null);
    expect(r1).not.toBe(r0);   // stepped exactly one beat forward
    await page.keyboard.press('End');
    await page.waitForTimeout(300);
    await page.keyboard.press('ArrowRight');   // clamped — must not crash or wrap
    await page.waitForTimeout(200);
    if (!(await state(page)).drawer) { await page.keyboard.press('i'); await page.waitForTimeout(300); }
    expect((await state(page)).drawer).toBe(true);
    await page.click('#th-drawer-x');
    await page.waitForTimeout(250);
    expect((await state(page)).drawer).toBe(false);
  });

  test('cinema ⛶ in, Esc out — never a black screen', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await simToggle(page);
    await page.waitForTimeout(1000);
    await page.click('#th-fs');   // v913 chrome: the ⛶ cinema button is #th-fs now
    await page.waitForTimeout(400);
    expect((await state(page)).cinema).toBe(true);
    // the stage must be visibly painting (not the v-cinema black-screen regression, REG-024)
    const stageVisible = await page.evaluate(() => {
      // v913 chrome: #th-stage is gone — the theatre body is #theatre with #th-film/#th-card
      // inside. REG-024's class is the cinema visibility cascade hiding EVERYTHING: assert the
      // theatre has real height AND its content is computed-visible.
      const th = document.getElementById('theatre');
      const inner = document.getElementById('th-film') || document.getElementById('th-card');
      return !!th && th.getBoundingClientRect().height > 100
        && !!inner && getComputedStyle(inner).visibility === 'visible';
    });
    expect(stageVisible).toBe(true);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
    expect((await state(page)).cinema).toBe(false);
    expect((await state(page)).theatre).toBe(true);   // Esc leaves cinema, not the theatre
  });

  test('visual snapshot sanity: stage paints, header tabs present, nothing black', async ({ page }) => {
    // v883 (#49) — deterministic visual floor (no pixel-diff flake): the console must LOOK alive
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    /* v1681 — MEASURE THE SURFACE THE HOMEPAGE ACTUALLY PAINTS, NOT #stage.
       This asserted `#stage` is wider than 400px and had been red on CI shard 6 since v901 made
       SESSIONS the console home: measured on a live console, body[data-view="sessions"] and
       #stage computes `display:none`, so its rect is 0×0. The stage being hidden here is not a
       regression — it is the design, and demo_console.mjs J8 gates it in the opposite direction
       ("session→data-view=sessions, hunt shown, stage hidden"). Two gates asserting contradictory
       things about the same element is how one of them stays red forever.
       The INTENT of this test is the sentence above it — the console must LOOK alive, nothing
       black — so it now measures whatever surface the current view owns: #home-dash on the
       sessions home (measured 1046×677), #stage once a view that uses the stage is up. That keeps
       the black-screen floor and stops pinning it to one element's 2019 role. */
    const vis = await page.evaluate(() => {
      const tabs = document.querySelectorAll('#head-tabs .ht').length;
      const view = document.body.getAttribute('data-view') || '';
      const surface = document.getElementById('home-dash') || document.getElementById('stage');
      const r = surface ? surface.getBoundingClientRect() : { width: 0, height: 0 };
      const phase = (document.getElementById('phase') || {}).textContent || '';
      return { tabs, view, surface: surface ? surface.id : null,
               stageW: r.width, stageH: r.height, phase };
    });
    expect(vis.tabs).toBe(8);   // v888 — TV·D joined the header nav · v2092 +🎒 Vault · v2094 +⚗️ Crafts
    expect(vis.surface, 'the console home paints no surface at all').not.toBeNull();
    expect(vis.stageW, `${vis.surface} is 0-wide on view "${vis.view}" — the console is black`)
      .toBeGreaterThan(400);
    expect(vis.stageH).toBeGreaterThan(200);   // v905 OFF-state law: stage capped at 250px — the dash owns the homepage
    expect(vis.phase.length).toBeGreaterThan(2);   // STANDBY/WATCHING — never empty
    await page.screenshot({ path: 'test-results/rinse-visual.png' });   // artifact for the humans
  });

  test('status latency budget: cached /api/status answers <500ms', async () => {
    const t0 = Date.now();
    const r = await fetch(CTRL + 'api/status', { signal: AbortSignal.timeout(3000) });
    expect(r.ok).toBe(true);
    expect(Date.now() - t0).toBeLessThan(500);   // v872 pure-memory status — the STANDBY fix stays fixed
  });
});
