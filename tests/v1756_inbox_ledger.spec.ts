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

import { suppressOneShots } from './_oneshots';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1938 — THIS SPEC SEEDS A LEDGER, SO IT MUST BOOT AS A LATER LOAD.
   v1925's remaining-repair runs 400ms after load and writes its own provenance rows into
   d2r_chronicleInboxLog — the very store this fixture seeds and then counts. It read 3 rows where
   it had seeded 2, and the empty-ledger test got a ledger that was no longer empty. The repair is
   correct; the fixture was measuring the repair's output as if it were its own.
   suppressOneShots() derives every boot-apply guard out of bible.html, so this needs no list and
   cannot go stale — see tests/_oneshots.ts for why a hand-listed version already failed once. */
const BOOT_AS_LATER_LOAD = suppressOneShots();

async function withLedger(page: any, log: any[], inbox: any[]) {
  await page.addInitScript(([l, i, flags]: [any[], any[], Record<string, string>]) => {
    for (const k of Object.keys(flags)) localStorage.setItem(k, flags[k]);
    localStorage.setItem('d2r_chronicleInboxLog', JSON.stringify(l));
    localStorage.setItem('d2r_chronicleInbox', JSON.stringify(i));
  }, [log, inbox, BOOT_AS_LATER_LOAD]);
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
    // v2672 — THE APP RENAMED THIS LANE AND THE ASSERTION DID NOT FOLLOW. Measured at HEAD:
    // bible.html emits "→ chronicle" (1 occurrence) and "already in your chronicle" (5); the string
    // "→ grail" appears ZERO times. This expected the pre-rename word and had been failing on CI
    // since the rename, saying "the row does not say WHERE it landed" about a row that says exactly
    // where it landed.
    // ⚠ PINNED TO THE CURRENT WORD, not widened to accept either. `toContain('grail|chronicle')`
    // would pass whichever way the app drifts, which is a test that cannot detect the next rename.
    // [[regression-guard]] — pin the LAW, not the number.
    expect(star.dest, 'the row does not say WHERE it landed').toContain('chronicle');
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

  /* v1769 — THE TWO BUTTONS ARE THE ONLY WAY OUT, and nothing guarded them. This file covered
     rendering, the three empty states and the badge — every part except whether pressing anything
     does something. That gap matters more than it looks: the gate needs two independent witnesses
     and the second eye is a Grok lane that is currently answering 402 on every call, so ANY doubtful
     name now lands here rather than being ticked. If "tick it" were decorative, the whole pending
     queue would be a place where his finds go to be forgotten — and it would look perfectly healthy,
     because a row that renders and a row that works are indistinguishable on screen.

     Measured before writing this: accept moved the row into foundLog and the grail count 248 -> 249;
     ignore wrote a dismissed row and emptied the queue. This pins that, and it pins that each button
     acts on ITS OWN row — the first draft of this check assumed seed order and read the alphabetical
     sort as a wrong-row bug. */
  /* v2263 — THE DEFECT THE TEST ABOVE CAUGHT, PINNED FROM THE OTHER SIDE.
     "tick it" worked (found 248 -> 249) and still recorded `in-chronicle`, because the vault door
     v2194 added upserts the SAME row with status 'vault-registered' after the acceptance, and
     Object.assign overwrote it; kaiChronicleLedger then relabels any non-accepted row that is now
     settled. Result: every item he ticks by hand read as one the board already had.

     The test above proves the symptom is gone. This one pins the RULE, because the obvious fix —
     freezing a ruled row outright — silently breaks undo, and nothing else in this suite would say
     so. Both directions, or neither is guarded. */
  test('a vault landing keeps his ruling; an undo still overturns it', async ({ page }) => {
    await withLedger(page, [], []);
    const r = await page.evaluate(() => {
      const w: any = window;
      const rec = (n: string, st: string, ex?: any) =>
        w.kaiChronicleRecord(Object.assign({ name: n, status: st }, ex || {}));
      const read = (n: string) => {
        const L = JSON.parse(w.LSR.getItem('d2r_chronicleInboxLog') || '[]');
        const row = L.filter((x: any) => x.name === n)[0] || {};
        return row.status + '|' + (row.vaultStatus || '-');
      };
      rec('ZZ_ruled', 'accepted', { store: 'foundLog' });
      rec('ZZ_ruled', 'vault-registered', { store: 'owned' });
      rec('ZZ_undo', 'accepted', { store: 'foundLog' });
      rec('ZZ_undo', 'removed', { store: 'foundLog' });
      rec('ZZ_dismiss', 'accepted', {});
      rec('ZZ_dismiss', 'dismissed', {});
      rec('ZZ_open', 'pending', {});
      rec('ZZ_open', 'vault-registered', { store: 'owned' });
      return {
        ruled: read('ZZ_ruled'), undo: read('ZZ_undo'),
        dismiss: read('ZZ_dismiss'), open: read('ZZ_open'),
      };
    });
    expect(r.ruled, 'a vault landing overwrote his acceptance — the ledger can no longer say who decided')
      .toBe('accepted|vault-registered');
    expect(r.undo, 'an undo can no longer overturn an acceptance — the freeze is too wide')
      .toBe('removed|-');
    expect(r.dismiss, 'a dismissal can no longer overturn an acceptance').toBe('dismissed|-');
    expect(r.open, 'an UNRULED row stopped taking the vault status it has always shown')
      .toBe('vault-registered|-');
  });

  test('★★★ tick it actually ticks THAT row, and ignore actually dismisses it', async ({ page }) => {
    const now = Date.now();
    await withLedger(page, [], [
      { name: "Griffon's Eye", triageWhy: 'only 1 independent witness (claude) — needs 2', proposedAt: now },
      { name: 'Bul-Kathos Wedding Band', triageWhy: 'the second eye disagreed with this read', proposedAt: now },
    ]);
    const r = await page.evaluate(async () => {
      const w: any = window;
      const nameOf = (row: Element) => ((row.querySelector('.ibx-nm') || {}) as any).textContent.trim();
      const rows = [...document.querySelectorAll('#inbox-panel .ibx-row')];
      const grail0 = w.funiScan().found;
      const first = nameOf(rows[0]);
      (rows[0].querySelector('.ibx-ok') as HTMLElement).click();
      await new Promise((x) => setTimeout(x, 500));
      const found = JSON.parse(w.LSR.getItem('d2r_foundLog') || '{}');

      w.renderInbox && w.renderInbox();
      const left = [...document.querySelectorAll('#inbox-panel .ibx-row')]
        .find((x) => x.querySelector('.ibx-b:not(.ibx-ok)'));
      const second = left ? nameOf(left) : null;
      if (left) (left.querySelector('.ibx-b:not(.ibx-ok)') as HTMLElement).click();
      await new Promise((x) => setTimeout(x, 500));

      return {
        first, second, grail0, grail1: w.funiScan().found,
        firstTicked: !!found[first],
        secondTicked: second ? !!found[second] : null,
        queue: (w.kaiChronicleInbox({ sync: false }) || []).map((x: any) => x.name),
        ledger: (w.kaiChronicleLedger({ sync: false }) || []).map((x: any) => x.name + ':' + x.status),
      };
    });
    expect(r.first, 'no pending row rendered, so nothing was tested').toBeTruthy();
    // ACCEPT: the row he pressed is the row that moved
    expect(r.firstTicked, `"tick it" did not put ${r.first} in the grail`).toBe(true);
    expect(r.grail1, 'the grail count did not move').toBe(r.grail0 + 1);
    expect(r.ledger, 'the ledger does not record the acceptance')
      .toContain(r.first + ':accepted');
    // IGNORE: dismissed, recorded, and NOT quietly ticked as well
    expect(r.second, 'the second name vanished from the queue without being ruled on').toBeTruthy();
    expect(r.secondTicked, `"ignore" put ${r.second} in the grail anyway`).toBe(false);
    expect(r.ledger, 'a dismissal left no trace in the ledger')
      .toContain(r.second + ':dismissed');
    // and the queue is empty, so a ruled item never comes back to be ruled again
    expect(r.queue, 'a resolved item is still waiting on him: ' + JSON.stringify(r.queue)).toEqual([]);
  });

  /* v1760 — THE NOTIFICATION HALF. Konyo asked for "an inbox that like has a NOTIFICATION of this a
     log or ledger". v1756 shipped the ledger and no notification: the card lives COLLAPSED inside
     Tools, so a name waiting on him stayed invisible until he went looking for the panel he had
     already asked about five times. A queue you must remember to check is a filing cabinet. */
  test('★★★ a waiting name shows a badge while the card is still SHUT', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('d2r_chronicleInbox', JSON.stringify([
        { name: 'Annihilus', triageWhy: 'only 0 independent witnesses (none) — needs 2' },
        { name: 'Gorefoot', triageWhy: 'the second eye disagreed with this read' },
      ]));
    });
    await page.goto(URL);
    await page.waitForTimeout(2600);
    const r = await page.evaluate(() => {
      const el = document.getElementById('inbox-badge');
      const card = document.getElementById('inbox-card');
      return {
        exists: !!el,
        hidden: el ? el.hidden : null,
        text: el ? (el.textContent || '').trim() : null,
        title: el ? (el.getAttribute('title') || '') : '',
        // the whole point: it must be right while the card is CLOSED
        collapsed: card ? card.classList.contains('collapsed') : null,
      };
    });
    expect(r.exists, 'there is no badge element at all').toBe(true);
    expect(r.collapsed, 'the card was already open, so this proves nothing about a shut card').toBe(true);
    expect(r.hidden, 'two names are waiting and the badge is hidden').toBe(false);
    expect(r.text, 'the badge does not say how many are waiting: ' + r.text).toMatch(/2\s*waiting/i);
    expect(r.title, 'the badge gives no explanation on hover').toMatch(/could not call/i);
  });

  test('★★★ nothing waiting shows NO badge — it never becomes wallpaper', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2600);
    const r = await page.evaluate(() => {
      const el = document.getElementById('inbox-badge');
      return { hidden: el ? el.hidden : null, text: el ? (el.textContent || '').trim() : null };
    });
    // a badge that is always there is a badge nobody reads
    expect(r.hidden, 'the badge is showing with an empty queue').toBe(true);
    expect(r.text, 'the badge still carries text with nothing waiting').toBe('');
  });

});
