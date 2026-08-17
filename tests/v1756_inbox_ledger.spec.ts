import { test, expect } from './_net_stub';
import * as path from 'path';

// v1756 — THE INBOX HAS A SCREEN NOW.
//
// Konyo, on the fifth ask: "and the inbox visually where is it?? for like the fifth time asking
// about it lol.. we said we had a ledger/log of the items getting added too so i know whats exactly
// is happening within the system."
//
// Every previous answer of mine pointed at `kaiChronicleLedger()` — a FUNCTION. Measured before this
// spec was written: **zero** DOM elements matched /inbox/i and there was no render function at all.
// The data layer had existed for versions; the surface never had. That is the plumbing-with-no-tap
// class, and describing a data structure as though it were a screen is how it survived five asks.
//
// AUTOMATIC IS THE POINT, and the panel has to SHOW that rather than assert it. Konyo: "i dont want
// it pending my decisions at all if its not needed only something its really not sure about."
// kaiChronicleTriage already worked that way — a grounded grail name is accepted outright, OCR junk
// and checker-tosses are dismissed outright, and only two cases hold: the second eye disagreed, or
// the tier claims grail while the name will not ground.
//
// WHAT IT MUST NEVER DO IS ASK TWICE. The second eye read the first build cold and found exactly one
// fault: "Spirit appears in both sections, which is momentarily confusing... an internal
// inconsistency the tool has not resolved." The pending queue is written at read time, but
// kaiChronicleLedger RE-ANNOTATES against live state afterwards, so an item can be settled and still
// queued. Settled wins, and this asserts it.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

async function withLedger(page: any, log: any[], inbox: any[]) {
  await page.addInitScript(([l, i]: [any[], any[]]) => {
    localStorage.setItem('d2r_chronicleInboxLog', JSON.stringify(l));
    localStorage.setItem('d2r_chronicleInbox', JSON.stringify(i));
  }, [log, inbox]);
  await page.goto(URL);
  await page.waitForTimeout(2400);
  await page.evaluate(() => {
    const w: any = window;
    w.switchTab && w.switchTab('tools');
    const c = document.getElementById('inbox-card');
    if (c && c.classList.contains('collapsed')) w.toggleCardCollapse('inbox-card');
    w.renderInbox && w.renderInbox();
  });
  await page.waitForTimeout(400);
}

test.describe('v1756 — the inbox is a place, not a function', () => {
  test('★★★ the card and its render function exist at all', async ({ page }) => {
    await withLedger(page, [], []);
    const r = await page.evaluate(() => {
      const w: any = window;
      const host = document.getElementById('inbox-panel');
      return {
        card: !!document.getElementById('inbox-card'),
        render: typeof w.renderInbox,
        rendered: host ? (host.textContent || '').trim().length : -1,
      };
    });
    expect(r.card, 'there is no #inbox-card on the board').toBe(true);
    expect(r.render, 'renderInbox() does not exist — the ledger has no surface again').toBe('function');
    expect(r.rendered, 'the panel rendered nothing at all').toBeGreaterThan(20);
  });

  test('★★★ an empty ledger explains WHICH silence it is, never a blank box', async ({ page }) => {
    await withLedger(page, [], []);
    const txt = await page.evaluate(() =>
      (document.getElementById('inbox-panel') || { textContent: '' }).textContent || '');
    // an empty bordered box is the first thing the second eye is told to flag
    expect(txt, 'the empty state says nothing about why it is empty')
      .toMatch(/nothing has been swept yet|holds no rows yet/i);
  });

  test('★★★ it says what happened AND where it went', async ({ page }) => {
    const now = Date.now();
    await withLedger(page, [
      { name: "Baranar's Star", status: 'accepted', store: 'foundLog', why: 'safe-auto-grail:name', lastTs: now - 60000 },
      { name: 'Chanpion Swrd', status: 'dismissed', why: 'safe-auto-junk:ocr', lastTs: now - 120000 },
    ], []);
    const r = await page.evaluate(() => {
      const host = document.getElementById('inbox-panel') as HTMLElement;
      const rows = [...host.querySelectorAll('.ibx-row')];
      return rows.map((x) => ({
        name: (x.querySelector('.ibx-nm') || { textContent: '' }).textContent,
        dest: (x.querySelector('.ibx-dest') || { textContent: '' }).textContent,
        why: (x.querySelector('.ibx-why') || { textContent: '' }).textContent,
        rawKept: (x.querySelector('.ibx-why') as HTMLElement | null)?.getAttribute('title') || '',
      }));
    });
    expect(r.length, 'no ledger rows rendered').toBe(2);
    const star = r.find((x) => /Baranar/.test(String(x.name)))!;
    expect(star.dest, 'the row does not say WHERE it landed').toContain('grail');
    // plain words on screen...
    expect(star.why, 'the reason is still internal shorthand: ' + star.why).toMatch(/matched a real unique/i);
    // ...and the exact code still reachable, because that is what you fix things with
    expect(star.rawKept, 'the raw reason code was thrown away').toContain('safe-auto-grail');
    const junk = r.find((x) => /Chanpion/.test(String(x.name)))!;
    expect(junk.dest, 'a dismissed row must say it went nowhere').toContain('nowhere');
  });

  test('★★★ a settled item is never ALSO asked about (the second eye caught this)', async ({ page }) => {
    const now = Date.now();
    await withLedger(page, [
      { name: 'Spirit', status: 'pending', triageWhy: 'tier-grail-ungrounded', proposedAt: now - 300000 },
    ], [
      { name: 'Spirit', triageWhy: 'tier-grail-ungrounded', proposedAt: now - 300000 },
    ]);
    const r = await page.evaluate(() => {
      const host = document.getElementById('inbox-panel') as HTMLElement;
      const names = [...host.querySelectorAll('.ibx-nm')].map((e) => (e.textContent || '').trim());
      return { names, spirit: names.filter((n) => n === 'Spirit').length };
    });
    // non-vacuity: it must be on screen at all, or "not twice" is trivially true
    expect(r.names, 'Spirit is not rendered anywhere, so this proves nothing').toContain('Spirit');
    expect(r.spirit, 'the same item is listed in BOTH sections: ' + JSON.stringify(r.names)).toBe(1);
  });
});
