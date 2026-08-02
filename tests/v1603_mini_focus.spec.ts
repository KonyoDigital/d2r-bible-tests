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
