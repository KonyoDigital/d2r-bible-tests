import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1996 — THE BACKEND FINALLY RENDERS. Konyo's standing ask, from the top of this arc: "i want it to
 * visually render the backend through the ledger visually so we can visually surgically fix anything
 * needed future wise."
 *
 * Three signals were computed from the PIXELS — free, on the frames the paid reader had to give up
 * on — and rendered NOWHERE:
 *   glimpsed    cells visibly full on a panel whose read named nothing (v1989)
 *   reconciled  names compared against occupied cells per frame (v1994)
 *   overRead    the read named MORE than the panel can hold — the only fabrication signal this lane
 *               has, and the class behind "i dont think i even own this"
 *
 * They failed to arrive TWICE over, each half silent on its own:
 *   1. apply_payload dropped them, so the board never received them however much it wanted to
 *   2. renderInbox split rows into CHANGED[status] vs EVERYTHING ELSE, so an unknown status landed
 *      in "already had — nothing to do". MEASURED: an over-read (27 names on a 22-cell panel) was
 *      shown to him as "nothing to do" under the sentence "The readers changed nothing this time.
 *      That is a clean run."
 *
 * A default bucket that absorbs unknown statuses turns every FUTURE signal silent on arrival, which
 * is why this test pins the bucket and not just the row.
 */

const PAYLOAD = {
  ok: true, source: 'vault-retro', mode: 'merge-max', generatedTs: 1787242458369,
  sessionsRead: ['s_A'], items: [], suggestions: [],
  glimpsed: [
    { frame: 'f_1784984209709.jpg', surface: 'personal', occupied: 22, free: 18 },
    { frame: 'f_1787242458369.jpg', surface: 'stash', occupied: 33, free: 7 },
  ],
  reconciled: [{ frame: 'f_bad.jpg', surface: 'stash', named: 27, occupied: 22, verdict: 'over-read' }],
  overRead: [{ frame: 'f_bad.jpg', surface: 'stash', named: 27, occupied: 22, names: ['Shako', 'Ist'] }],
};

async function applyAndOpen(page: any) {
  await page.goto(URL); await page.waitForTimeout(1200);
  await page.evaluate(() => { localStorage.clear(); localStorage.setItem('d2r_ownerClaim', '*'); });
  await page.goto(URL); await page.waitForTimeout(1600);
  await page.evaluate((p: any) => (window as any).vaultAccumApply(p), PAYLOAD);
  await page.waitForTimeout(400);
  await page.evaluate(() => {
    const w: any = window;
    try { w.switchTab('tools'); } catch (e) { /* tab may not exist in a stub */ }
    const c = document.getElementById('inbox-card');
    if (c && c.classList.contains('collapsed') && w.toggleCardCollapse) w.toggleCardCollapse('inbox-card');
    try { w.renderInbox(); } catch (e) { /* reported by the assertions below */ }
  });
  await page.waitForTimeout(700);
}

test('a fabrication warning is never filed under "nothing to do"', async ({ page }) => {
  await applyAndOpen(page);
  const sum = await page.evaluate(() =>
    (document.querySelector('#inbox-panel .ibx-sum') as HTMLElement)?.innerText || '');
  expect(sum, 'the summary line did not render at all').not.toBe('');
  // the whole point: three findings, in their OWN bucket
  expect(sum).toContain('need your eye');
  expect(sum).toMatch(/3\s*need your eye/);
  // and they must NOT have been counted as no-ops
  expect(sum).not.toMatch(/5\s*already had/);
});

test('each row names the frame he can go and open, and the over-read says what it read', async ({ page }) => {
  await applyAndOpen(page);
  const rows = await page.evaluate(() =>
    Array.from(document.querySelectorAll('#inbox-panel .ibx-eye-row')).map((r) => (r as HTMLElement).innerText));
  expect(rows.length).toBe(3);
  expect(rows.join(' | ')).toContain('f_1784984209709.jpg');
  expect(rows.join(' | ')).toContain('f_bad.jpg');
  const over = rows.find((r) => r.includes('named more than the panel holds'))!;
  expect(over, 'the over-read row is missing its label').toBeTruthy();
  expect(over).toContain('27');   // what it claimed
  expect(over).toContain('22');   // what the panel holds
  expect(over).toContain('Shako');
  // it must never read as a verdict that threw his data away
  expect(over).toContain('Nothing was discarded');
});

test('the pixel row does not overlap its own pill', async ({ page }) => {
  await applyAndOpen(page);
  /* CAUGHT ON THE PIXELS, NOT BY READING. The base .ibx-row is a FIVE-column grid (when · name ·
     pill · why · dest) and these rows carry three children, so the why-text ran straight through
     the pill. Every text assertion passed while the render was unreadable. */
  const bad = await page.evaluate(() => {
    const out: string[] = [];
    document.querySelectorAll('#inbox-panel .ibx-eye-row').forEach((row, i) => {
      const pill = row.querySelector('.ibx-pill') as HTMLElement;
      const why = row.querySelector('.ibx-why') as HTMLElement;
      if (!pill || !why) { out.push(`row ${i}: missing pill or why`); return; }
      const p = pill.getBoundingClientRect(), w = why.getBoundingClientRect();
      const overlap = p.right > w.left + 1 && p.left < w.right - 1 && p.bottom > w.top + 1 && p.top < w.bottom - 1;
      if (overlap) out.push(`row ${i}: pill overlaps why (pill.right=${Math.round(p.right)} why.left=${Math.round(w.left)})`);
      if (p.width < 20 || p.height < 8) out.push(`row ${i}: pill has no box`);
    });
    return out;
  });
  expect(bad, bad.join('; ')).toEqual([]);
});
