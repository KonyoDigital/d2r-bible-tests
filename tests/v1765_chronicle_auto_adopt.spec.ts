import { test, expect } from './_net_stub';
import * as path from 'path';

// v1765 — THE CHAIN'S LAST LINK, AND THE THREE THINGS IT MUST REFUSE.
//
// Konyo: "i want it all automated only complicated things should get stuck in pending" and "in
// general the future of the rest of the sessions that will be."
//
// `chronicleFetchProposal` had existed for versions with **zero callers** — grep returned only its
// own definition line. The board could ask the console for a finished sweep and never did, so
// "automatic" ended at the console's memory: the watchdog swept, v1763 persisted the result, and
// the surface it was written for never asked. That is plumbing-with-no-tap, and it is silent by
// construction — every half measured healthy on its own.
//
// WHAT MADE THE FIX DANGEROUS. The console serves the board over http, and an unclaimed load on
// that origin resolves GUEST with the seeds suppressed. Measured on a clean profile against the
// running console: grail read 0, and all 17 rows of HIS sweep were proposed as pending finds — a
// stranger's inbox filled with his footage. The owner gate below is that measurement, frozen.
//
// WHY A PURE FUNCTION. Proving any of this by hand needs a live console on his Mac; CI has none and
// must never need one. A rule only checkable on one machine rots the day that machine changes, so
// the decision is a pure function and this gate exercises every branch of it — including the ADOPT
// branch, without which the four refusals are trivially satisfied by a function that never says yes.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v1765 — the board adopts a finished sweep, and only ever its own', () => {
  test('★★★ something finally calls it — the tap exists and is wired to load', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2400);
    const r = await page.evaluate(() => {
      const w: any = window;
      return { fetchFn: typeof w.chronicleFetchProposal, adoptFn: typeof w._chronAutoAdopt, gate: typeof w._chronAdoptGate };
    });
    expect(r.fetchFn, 'chronicleFetchProposal vanished').toBe('function');
    expect(r.adoptFn, 'nothing calls the fetch again — the chain is open at the last link').toBe('function');
    expect(r.gate, 'the adopt decision is not a testable function').toBe('function');
  });

  test('★★★ it ADOPTS a new sweep on the owner console — the branch that must say yes', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2400);
    const r = await page.evaluate(() => (window as any)._chronAdoptGate(
      { host: '127.0.0.1:17772', cousin: false, stamp: 'B', seen: 'A' }));
    // without this the four refusals below pass for a function that returns {ok:false} always
    expect(r.ok, 'a fresh sweep on the owner console was refused: ' + JSON.stringify(r)).toBe(true);
  });

  test('★★★ the public site never pokes a service on his laptop', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2400);
    const r = await page.evaluate(() => {
      const G = (window as any)._chronAdoptGate;
      return { site: G({ host: 'bull-4-u.com', cousin: false }), file: G({ host: '', cousin: false }) };
    });
    expect(r.site.ok, 'the deployed site tried to adopt from a console').toBe(false);
    expect(r.site.why).toMatch(/not served by the console/i);
    expect(r.file.ok, 'a downloaded file:// copy tried to adopt').toBe(false);
  });

  test('★★★ a cousin never adopts HIS footage (measured: 17 rows, all 17 pending)', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2400);
    const r = await page.evaluate(() => (window as any)._chronAdoptGate(
      { host: '127.0.0.1:17772', cousin: true }));
    expect(r.ok, 'an unclaimed load adopted a sweep of his recordings').toBe(false);
    expect(r.why, 'the refusal does not name the reason: ' + r.why).toMatch(/owner world/i);
  });

  test('★★★ it never asks twice about the same sweep', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2400);
    const r = await page.evaluate(() => (window as any)._chronAdoptGate(
      { host: '127.0.0.1:17772', cousin: false, stamp: 'A', seen: 'A' }));
    // a refresh re-proposing what he already ruled on is how a queue becomes wallpaper
    expect(r.ok, 'a page refresh re-adopted the same sweep').toBe(false);
    expect(r.why).toMatch(/already adopted/i);
  });

  /* v1765 — AND THE LEDGER IT FILLS HAS TO HOLD STILL.
     Measured on the real console across two loads of the SAME 17 rows: the sequence differed both
     times and neither was alphabetical. Two causes, both fixed here — the panel never sorted at
     all, and the writer stamped every row with its own Date.now(), so one 17-row apply that
     straddled a millisecond split into two timestamp groups that then ordered arbitrarily.
     He asked this panel for "history wise what happened... so we can see it properly routed and if
     needed we can then surgically fix whats not". A list that reshuffles between visits cannot be
     read that way: you lose your place, and a moved row is indistinguishable from a new one. */
  test('★★★ same rows, same order — every time', async ({ page }) => {
    const ts = 1786000000000;
    await page.addInitScript((t: number) => {
      localStorage.setItem('d2r_chronicleInboxLog', JSON.stringify([
        { name: 'Gorefoot',   status: 'in-chronicle', store: 'foundLog', lastTs: t },
        { name: 'Andariel\'s Visage', status: 'in-chronicle', store: 'foundLog', lastTs: t },
        { name: 'Bonesnap',   status: 'in-chronicle', store: 'foundLog', lastTs: t },
      ]));
    }, ts);
    await page.goto(URL);
    await page.waitForTimeout(2400);
    const names = await page.evaluate(() => {
      const w: any = window;
      w.switchTab && w.switchTab('tools');
      const c = document.getElementById('inbox-card');
      if (c && c.classList.contains('collapsed')) w.toggleCardCollapse('inbox-card');
      w.renderInbox && w.renderInbox();
      return [...document.querySelectorAll('#inbox-panel .ibx-row .ibx-nm')].map(e => (e.textContent || '').trim());
    });
    // one sweep = one moment, so the tie-break decides — and it must be the name, never chance
    expect(names, 'the ledger does not order rows of one sweep by name: ' + JSON.stringify(names))
      .toEqual(["Andariel's Visage", 'Bonesnap', 'Gorefoot']);
  });

  test('★★★ newer sweeps sit above older ones — it is a log, after all', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('d2r_chronicleInboxLog', JSON.stringify([
        { name: 'Older Find', status: 'in-chronicle', store: 'foundLog', lastTs: 1786000000000 },
        { name: 'Newer Find', status: 'in-chronicle', store: 'foundLog', lastTs: 1786000900000 },
      ]));
    });
    await page.goto(URL);
    await page.waitForTimeout(2400);
    const names = await page.evaluate(() => {
      const w: any = window;
      w.switchTab && w.switchTab('tools');
      const c = document.getElementById('inbox-card');
      if (c && c.classList.contains('collapsed')) w.toggleCardCollapse('inbox-card');
      w.renderInbox && w.renderInbox();
      return [...document.querySelectorAll('#inbox-panel .ibx-row .ibx-nm')].map(e => (e.textContent || '').trim());
    });
    // alphabetically 'Newer' > 'Older', so a name-only sort would invert this — that is the point
    expect(names[0], 'the newest row is not at the top: ' + JSON.stringify(names)).toBe('Newer Find');
  });

  test('★★★ off-console, the fetch itself explains rather than going quiet', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2400);
    const r = await page.evaluate(async () => await (window as any)._chronAutoAdopt());
    expect(r.ok).toBe(false);
    // silence is not evidence: an automatic step that declines must say which decline it was
    expect(String(r.why || ''), 'the refusal is empty — indistinguishable from a crash').not.toBe('');
  });
});
