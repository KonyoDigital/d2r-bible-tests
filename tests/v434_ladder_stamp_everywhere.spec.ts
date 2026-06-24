import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v434 — the 🪜 ladder stamp must show on EVERY runeword title (not just the ID card), and the
// Ladder/Non-Ladder toggle must actually change the Chronicle list (ladder-only RWs get BLOCKED on
// a non-ladder character). Also locks the corrected ladder-only set (Authority OUT, Bulwark IN).
test('ladder stamp renders on All-Runewords + What-I-can-make titles', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window;
    if (w.renderAllRunewords) w.renderAllRunewords();
    const allRw = document.getElementById('all-rw-list')?.innerHTML || '';
    return {
      tagHelper: typeof w._rwLadderTag === 'function',
      bulwarkLadder: !!(w._RW_LADDER_ONLY && w._RW_LADDER_ONLY['Bulwark']),
      authorityNotLadder: !(w._RW_LADDER_ONLY && w._RW_LADDER_ONLY['Authority']),
      // a ladder-only RW row carries the tag; a non-ladder one does not
      bulwarkTagged: w._rwLadderTag ? /rw-ladder-tag/.test(w._rwLadderTag('Bulwark')) : false,
      authorityUntagged: w._rwLadderTag ? w._rwLadderTag('Authority') === '' : false,
      browserHasTag: /rw-ladder-tag/.test(allRw),
    };
  });
  expect(r.tagHelper).toBe(true);
  expect(r.bulwarkLadder).toBe(true);
  expect(r.authorityNotLadder).toBe(true);
  expect(r.bulwarkTagged).toBe(true);
  expect(r.authorityUntagged).toBe(true);
  expect(r.browserHasTag).toBe(true);
});

test('Ladder/Non-Ladder toggle changes the Chronicle list', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window;
    const cls = (name:string) => {
      const rows = Array.from(document.querySelectorAll('#rwc-list .rwc-row')) as HTMLElement[];
      const row = rows.find(el => (el.querySelector('.rwc-name')?.textContent || '').trim().startsWith(name));
      return row ? row.className : null;
    };
    w.rwSetLadderMode('nonladder'); w.renderRunewordChronicle();
    const nonLadder = cls('Cure');           // ladder-only, not made → should be blocked
    w.rwSetLadderMode('ladder'); w.renderRunewordChronicle();
    const ladder = cls('Cure');
    return { nonLadder, ladder };
  });
  // Non-ladder: Cure is blocked/dimmed; Ladder: it is not blocked → the list visibly changes.
  expect(r.nonLadder).toContain('rwc-r-block');
  expect(r.ladder).not.toContain('rwc-r-block');
});
