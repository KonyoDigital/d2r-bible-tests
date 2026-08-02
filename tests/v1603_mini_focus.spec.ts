import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1603 — ⏱ MINI KNOWS WHAT IT IS LOOKING AT.
//
// Konyo: "so for MINI AIR ON is this finally focused and understanding of the fact that it is
// reading stash/runes/gems/materials and to look out specifically for this" — and then, for the
// grail: "for chronicles too.. should have a chronicle focused based click on.. and button for it
// so its focused specifically for each grail chronicle individually and relevant".
//
// The honest answer before this was NO. `focus` was stamped onto the reel and used for exactly one
// thing — sweeping mini reels first. is_mini_reel's own docstring said it: "being wrong here costs
// ordering, never correctness". Nothing told the READER what it was looking at.
//
// It is not a label any more. The retro sweep TRUSTS the stamp in place of a classify call, which
// makes pressing the right button both cheaper and more accurate — on a two-reel fixture a
// deliberately-wrong classifier files "Ral Rune" as lane=inventory/kind=item, while the declared
// focus files it as lane=stash/kind=rune and spends 0 model calls instead of 2.
//
// So these tests care about one thing above all: THE CHOICE MUST REACH THE ENGINE. A focus row that
// looks right and posts `{}` would be the same defect this whole feature exists to remove.

const ORIGIN = 'http://tvd.console.test';
const UI_HTML = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

const FOCUSES = ['stash', 'runes', 'gems', 'materials', 'chronicle-uniques', 'chronicle-sets'];

async function open(page: any) {
  const posts: any[] = [];
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI_HTML }));
  await page.route((u: URL) => u.pathname === '/api/mini', (r: any) => {
    const req = r.request();
    if (req.method() === 'POST') {
      let body: any = {};
      try { body = JSON.parse(req.postData() || '{}'); } catch (e) { body = {}; }
      posts.push(body);
      // the engine ECHOES what it accepted — the console must render the echo, not its own wish
      return r.fulfill({ status: 200, contentType: 'application/json',
                         body: JSON.stringify({ ok: true, seconds: 25, focus: body.focus || 'stash' }) });
    }
    return r.fulfill({ status: 200, contentType: 'application/json',
                       body: JSON.stringify({ running: false, focuses: FOCUSES }) });
  });
  await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/mini',
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1800);
  return posts;
}

test.describe('v1603 — the mini capture has a subject', () => {
  test('★ every focus the ENGINE offers gets a button — including both chronicles', async ({ page }) => {
    await open(page);
    const labels = await page.evaluate(() =>
      Array.from(document.querySelectorAll('#mini-foc .mf')).map((b: any) => b.dataset.f));
    expect(labels, 'the console must render the engine\'s list, not a second copy that can drift')
      .toEqual(FOCUSES);
    const text = (await page.textContent('#mini-foc')) || '';
    expect(text).toContain('uniques');
    expect(text).toContain('sets');
    expect(text).toContain('runes');
  });

  test('★★ THE CHOICE REACHES THE ENGINE — pressing 🧩 sets posts chronicle-sets', async ({ page }) => {
    const posts = await open(page);
    await page.click('#mini-foc .mf[data-f="chronicle-sets"]');
    await page.click('#btn-mini');
    await page.waitForTimeout(300);
    expect(posts.length, 'the start must have been sent').toBe(1);
    expect(posts[0].focus,
      'a focus row that looks right and posts {} is the same dead-plumbing defect this feature ' +
      'exists to remove — the stamp is what the sweep later TRUSTS').toBe('chronicle-sets');
  });

  test('★ a different pick sends a different focus — the selection is real, not decorative', async ({ page }) => {
    const posts = await open(page);
    await page.click('#mini-foc .mf[data-f="runes"]');
    await page.click('#btn-mini');
    await page.waitForTimeout(250);
    expect(posts[0].focus).toBe('runes');
  });

  test('the default is stash — pressing MINI without choosing still works', async ({ page }) => {
    const posts = await open(page);
    await page.click('#btn-mini');
    await page.waitForTimeout(250);
    expect(posts[0].focus, 'the common case must need no clicks').toBe('stash');
  });

  test('★ exactly one focus is selected at a time', async ({ page }) => {
    await open(page);
    await page.click('#mini-foc .mf[data-f="gems"]');
    await page.waitForTimeout(150);
    const on = await page.evaluate(() =>
      Array.from(document.querySelectorAll('#mini-foc .mf.on')).map((b: any) => b.dataset.f));
    expect(on).toEqual(['gems']);
  });

  test('★ the toast echoes the focus the ENGINE accepted, not the one we asked for', async ({ page }) => {
    // If the engine falls back (an unknown name, an older build), he has to SEE that rather than
    // be told his pick landed. The console renders j.focus, never _miniFocus.
    await page.route(ORIGIN + '/ui', (r: any) =>
      r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI_HTML }));
    await page.route((u: URL) => u.pathname === '/api/mini', (r: any) =>
      r.request().method() === 'POST'
        ? r.fulfill({ status: 200, contentType: 'application/json',
                      body: JSON.stringify({ ok: true, seconds: 25, focus: 'stash' }) })   // fell back
        : r.fulfill({ status: 200, contentType: 'application/json',
                      body: JSON.stringify({ running: false, focuses: FOCUSES }) }));
    await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/mini',
      (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
    await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1800);
    await page.click('#mini-foc .mf[data-f="chronicle-uniques"]');
    await page.click('#btn-mini');
    await page.waitForTimeout(400);
    const body = (await page.textContent('body')) || '';
    expect(body, 'the engine said stash; saying "uniques" would be a comfortable lie')
      .toMatch(/stash/i);
  });

  test('★ the panel does not throw — no dead seam in the new block', async ({ page }) => {
    const errs: string[] = [];
    page.on('pageerror', (e: any) => errs.push(String(e.message || e)));
    await open(page);
    await page.click('#mini-foc .mf[data-f="materials"]');
    await page.waitForTimeout(250);
    expect(errs).toEqual([]);
  });
});

test.describe('v1604 — a refusal has to say WHY', () => {
  // Konyo, on his wife's Windows PC: "i clicked mini and it doesnt record anything". mini_start()
  // returns a precise reason for every one of its four refusals — but two put it in `error` and one
  // in `msg`, and the console only ever read `why`. So "DISK TOO FULL to record" and "still shutting
  // down — session saving" both rendered as "mini could not start". The engine was never silent;
  // the console was deaf, and he was left with a button that did nothing and no way to find out why.
  const UI = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

  async function refuse(page: any, payload: any) {
    await page.route(ORIGIN + '/ui', (r: any) =>
      r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
    await page.route((u: URL) => u.pathname === '/api/mini', (r: any) =>
      r.request().method() === 'POST'
        ? r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(payload) })
        : r.fulfill({ status: 200, contentType: 'application/json',
                      body: JSON.stringify({ running: false, focuses: FOCUSES }) }));
    await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/mini',
      (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
    await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1600);
    await page.click('#btn-mini');
    await page.waitForTimeout(350);
    return {
      toast: (await page.textContent('#toast')) || '',
      sub: (await page.textContent('#mini-sub')) || '',
    };
  }

  test('★ a DISK-FULL refusal reaches him — it arrives in `error`, not `why`', async ({ page }) => {
    const out = await refuse(page, { ok: false, mode: 'off',
      error: 'DISK TOO FULL to record — 3.1GB free, need 8GB. Free ~6GB and press MINI again.' });
    expect(out.toast, 'this is the exact reason the engine gave; dropping it leaves him guessing')
      .toContain('DISK TOO FULL');
    expect(out.sub, 'a toast can be missed — the button label must keep the reason').toContain('DISK');
  });

  test('★ a STILL-SEALING refusal reaches him — it arrives in `msg`', async ({ page }) => {
    const out = await refuse(page, { ok: false, mode: 'stopping', error: 'still stopping',
      msg: 'still shutting down — session saving; try MINI again in a moment' });
    expect(out.toast).toMatch(/still (shutting down|stopping)/i);
  });

  test('a `why` refusal still works — the old key was never wrong, only incomplete', async ({ page }) => {
    const out = await refuse(page, { ok: false, mode: 'live',
      why: 'already recording — seal the current session first' });
    expect(out.toast).toContain('already recording');
  });

  test('★ a refusal with NO reason says so, rather than pretending', async ({ page }) => {
    const out = await refuse(page, { ok: false });
    expect(out.toast, '"no reason given" is a fact he can report; silence is not')
      .toMatch(/no reason given/i);
  });
});

test.describe('v1605 — an empty mini must not look like a good one', () => {
  // Konyo: "i clicked mini and it doesnt record anything." MINI replicates ON AIR everywhere that
  // matters — same start_agent, same disk preflight, same stop path, and MINI_MODE changes no
  // capture behaviour in the agent. The one thing it ADDS is a 25s bound, and that is where the
  // gap was: if capture had not warmed up inside it, the watchdog sealed a reel with ZERO frames
  // and reported the same quiet success as a full one.
  const UI = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

  async function afterSeal(page: any, state: any) {
    await page.route(ORIGIN + '/ui', (r: any) =>
      r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
    await page.route((u: URL) => u.pathname === '/api/mini', (r: any) =>
      r.fulfill({ status: 200, contentType: 'application/json',
                  body: JSON.stringify({ running: false, focuses: FOCUSES, ...state }) }));
    await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/mini',
      (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
    await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1600);
    await page.click('#btn-mini').catch(() => {});
    await page.waitForTimeout(1200);
    return {
      sub: (await page.textContent('#mini-sub')) || '',
      toast: (await page.textContent('#toast')) || '',
      empty: await page.evaluate(() =>
        !!document.getElementById('btn-mini')?.classList.contains('mini-empty')),
    };
  }

  test('★★ ZERO frames is reported — this is the exact thing he could not see', async ({ page }) => {
    const out = await afterSeal(page, { sealedTs: 1785700000000, sealedFrames: 0 });
    expect(out.sub, 'the label must carry it — a toast can be missed').toMatch(/0 frames|nothing/i);
    expect(out.empty, 'and the button must show it, not sit there looking normal').toBe(true);
    expect(out.toast, 'and it should point at the likely cause rather than just stating failure')
      .toMatch(/D2R|Doctor/i);
  });

  test('★ UNKNOWN (null) is NOT reported as zero — never accuse the capture on missing evidence',
    async ({ page }) => {
      const out = await afterSeal(page, { sealedTs: 1785700000000, sealedFrames: null });
      expect(out.sub).not.toMatch(/0 frames/i);
      expect(out.empty).toBe(false);
    });

  test('a mini that DID record says nothing alarming', async ({ page }) => {
    const out = await afterSeal(page, { sealedTs: 1785700000000, sealedFrames: 47 });
    expect(out.sub).not.toMatch(/0 frames|nothing was captured/i);
    expect(out.empty).toBe(false);
  });
});
