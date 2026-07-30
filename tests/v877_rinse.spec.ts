// v877 — THE RINSE, PERMANENT (Konyo Workflow step 12: 'RINSE as permanent spec').
// The 13-point user-experience matrix that used to live as a scratchpad driver: every console
// button both directions, keyboard matrix, rapid-fire stress — now SELF-HOSTED so CI runs it
// unconditionally: the spec boots its OWN control server (private port, fixture journal via
// TV_SESSIONS) and never touches a live console on :17772.
import { test, expect } from '@playwright/test';
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
      await page.click('#btn-sim');
      await page.waitForTimeout(700);
      expect((await state(page)).theatre, `open round ${i}`).toBe(true);
      await page.click('#btn-sim');
      await page.waitForTimeout(500);
      expect((await state(page)).theatre, `close round ${i}`).toBe(false);
    }
  });

  test('Space plays/pauses the reel and NEVER touches the agent', async ({ page }) => {
    await page.goto(CTRL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await page.click('#btn-sim');
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
    await page.click('#btn-sim');
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
    await page.click('#btn-sim');
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
    const vis = await page.evaluate(() => {
      const tabs = document.querySelectorAll('#head-tabs .ht').length;
      const stage = document.getElementById('stage');
      const r = stage ? stage.getBoundingClientRect() : { width: 0, height: 0 };
      const phase = (document.getElementById('phase') || {}).textContent || '';
      return { tabs, stageW: r.width, stageH: r.height, phase };
    });
    expect(vis.tabs).toBe(6);   // v888 — TV·D joined the header nav
    expect(vis.stageW).toBeGreaterThan(400);
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
