import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1537 — 🔍 THE READ CHAIN panel.
//
// Konyo's cousin did an ON AIR and his rune stash never got read. "The readers aren't working"
// turned out to be five different possible failures needing five different fixes (REG-086), and the
// audit that tells them apart shipped as a CLI — the wrong shape for the person who needs it most,
// who is on a Windows box he may never open a terminal on.
//
// The rules this spec holds are the ones that decide whether he TRUSTS the panel: a broken link
// always says what to do about it, "nothing to judge" is never dressed as "everything works", and
// the panel says nothing at all rather than guessing when it cannot reach the console.

const ORIGIN = 'http://tvd.console.test';
const UI_HTML = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

const HEALTH = {
  ok: true, sessions: 16, broken: 2, verdict: '2 broken link(s)', spent: 0,
  findings: [
    { session: 's_1', tab: 'runes', verdict: 'C · named it, never fired an intake',
      detail: 'the runes tab was identified on 9 frame(s) and no intake was ever attempted',
      fix: 'THE BOARD. A tally is fired THROUGH the board window — if the board is closed, nothing fires.' },
    { session: 's_1', tab: 'gems', verdict: 'D · fired, came back empty',
      detail: '6 intake(s) fired for gems; best total was 0',
      fix: 'the READ itself (prompt or crop), not the plumbing.' },
    { session: 's_1', tab: 'materials', verdict: 'E · worked',
      detail: 'materials tallied — total 224', fix: '' },
  ],
};

async function open(page: any, payload: any) {
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI_HTML }));
  await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/reader_health',
    (r: any) => r.abort());
  await page.route((u: URL) => u.pathname === '/api/reader_health', (r: any) =>
    payload === null ? r.abort()
      : r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(payload) }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(600);
}

test.describe('v1537 — which link broke, without a terminal', () => {
  // ── v1538 — HOW THIS MACHINE CROPS ──────────────────────────────────────────────────────────
  // Konyo asked whether running it on his Windows PC would be enough of a test. It is — but only
  // if the answer is VISIBLE, and REG-086 stayed invisible for as long as it did precisely because
  // nothing ever said which branch a frame took.
  test('★ the crop branch is stated, so one Windows run PROVES the fix', async ({ page }) => {
    await open(page, { ...HEALTH, crop: { aspect: 1.7778, branch: 'derived', size: [530, 289],
      says: 'a band DERIVED for this aspect (v1536).' } });
    const row = (await page.textContent('.readh-row')) || '';
    expect(row).toContain('derived');
    expect(row).toContain('1.7778');
    expect(row, 'the pixel size is the number the whole diagnosis turned on').toContain('530×289px');
  });

  test('★ the 46% slab reads as BROKEN — that is REG-086 still happening', async ({ page }) => {
    await open(page, { ...HEALTH, crop: { aspect: 1.7778, branch: 'slab-46pct', size: [883, 1080],
      says: '⚠ the coarse 46%-of-screen fallback — 5x more diluted than the calibrated band.' } });
    const first = page.locator('.readh-row').first();
    expect(await first.getAttribute('class')).toContain('bad');
    expect(await first.textContent()).toContain('5x more diluted');
  });

  test('the calibrated Mac path reads as fine, not as a warning', async ({ page }) => {
    await open(page, { ...HEALTH, crop: { aspect: 1.5377, branch: 'locked-mac', size: [612, 289],
      says: "the LOCKED band measured on Konyo's own film — the calibrated path" } });
    expect(await page.locator('.readh-row').first().getAttribute('class')).toContain('good');
  });

  test('no crop decision yet means no crop row — never a guessed one', async ({ page }) => {
    await open(page, { ...HEALTH, crop: null });
    const rows = await page.$$eval('.readh-row', (n: any[]) => n.map((x) => x.textContent));
    expect(rows.join(' ')).not.toContain('crop ');
  });

  test('each broken link is named with the evidence behind it', async ({ page }) => {
    await open(page, HEALTH);
    expect(await page.isHidden('#hd-readh')).toBe(false);
    const rows = await page.$$eval('.readh-row', (n: any[]) => n.map((x) => x.textContent));
    expect(rows).toHaveLength(3);
    expect(rows[0]).toContain('named it, never fired');
    expect(rows[0], 'a verdict without its evidence is unarguable').toContain('9 frame(s)');
  });

  test('a working link reads as working, not as a warning', async ({ page }) => {
    await open(page, HEALTH);
    expect(await page.locator('.readh-row.good').count()).toBe(1);
    expect(await page.locator('.readh-row.bad').count()).toBe(2);
  });

  test('★ every broken link says what to DO about it', async ({ page }) => {
    // naming a problem without a next step is just an alarm — and he is looking at this precisely
    // because he does not know what to do
    await open(page, HEALTH);
    const fixes = await page.$$eval('.readh-fix', (n: any[]) => n.map((x) => x.textContent));
    expect(fixes).toHaveLength(2);
    expect(fixes.join(' ')).toContain('THE BOARD');
    expect(fixes.join(' ')).toContain('the READ itself');
  });

  test('★ the same broken link is explained ONCE, not per row', async ({ page }) => {
    // five copies of one piece of advice is noise, and noise is what he skips
    await open(page, {
      ...HEALTH,
      findings: [HEALTH.findings[1], { ...HEALTH.findings[1], tab: 'runes' },
                 { ...HEALTH.findings[1], tab: 'materials' }],
    });
    expect(await page.locator('.readh-row').count()).toBe(3);
    expect(await page.locator('.readh-fix').count()).toBe(1);
  });

  test('★ "nothing to judge" is never dressed as "everything works"', async ({ page }) => {
    await open(page, { ok: true, sessions: 3, broken: 0, findings: [],
                       verdict: 'nothing to judge — no stash activity in this journal', spent: 0 });
    const txt = (await page.textContent('#readh-body')) || '';
    expect(txt).toMatch(/nothing to judge/);
    expect(txt, 'it must tell him how to make there be something to judge').toMatch(/open a stash tab/);
    expect(txt).not.toMatch(/everything works|all good|healthy/i);
  });

  test('a clean journal DOES say so, when there is something to judge', async ({ page }) => {
    await open(page, { ok: true, sessions: 4, broken: 0, findings: [HEALTH.findings[2]],
                       verdict: 'every tally tab that was opened got a real total', spent: 0 });
    expect(await page.textContent('#readh-sub')).toContain('every tally tab');
    expect(await page.locator('.readh-row.bad').count()).toBe(0);
  });

  test('an unreadable journal says why instead of implying the readers are fine', async ({ page }) => {
    await open(page, { ok: false, why: 'could not read this machine’s journal' });
    expect(await page.textContent('#readh-body')).toContain('could not check');
  });

  test('★ with no console at all the panel stays HIDDEN — it never guesses', async ({ page }) => {
    // a diagnostic that renders a verdict it could not obtain is worse than no diagnostic
    await open(page, null);
    expect(await page.isHidden('#hd-readh')).toBe(true);
  });
});
