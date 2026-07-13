import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v447 — the Chronicle's Ladder/Non-Ladder toggle SEPARATES the list into two labelled groups
// (Ladder-only vs Non-Ladder), and the active character mode reorders which group leads.
test('Chronicle splits runewords into Ladder-only vs Non-Ladder groups, reordered by mode', async ({ page }) => {
  // v681 — CHRONICLE SEALED 99/99: the owner floor (_RWC_SEED) marks every word made, so the
  // Chronicle's default 'todo' filter renders an empty list → 0 group headers. A fresh profile
  // suppresses the seed so both the Ladder-only and Non-Ladder groups populate.
  await page.addInitScript(() => { try { localStorage.setItem('d2r_rwProfile', 'fresh'); } catch(e){} });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window;
    const headers = () => Array.from(document.querySelectorAll('#rwc-list .rwc-grp-hdr')).map(h => ({
      text: (h.textContent || '').trim(), ladder: h.classList.contains('rwc-grp-ladder'),
    }));
    w.rwSetLadderMode('ladder'); w.renderRunewordChronicle();
    const ladderMode = headers();
    w.rwSetLadderMode('nonladder'); w.renderRunewordChronicle();
    const nonLadderMode = headers();
    return { ladderMode, nonLadderMode };
  });
  // both modes render two groups: one ladder-only, one non-ladder
  expect(r.ladderMode.length).toBe(2);
  expect(r.ladderMode.some(h => h.ladder)).toBe(true);
  expect(r.ladderMode.some(h => !h.ladder)).toBe(true);
  // Ladder mode → the ladder-only group leads; Non-Ladder mode → the non-ladder group leads
  expect(r.ladderMode[0].ladder).toBe(true);
  expect(r.nonLadderMode[0].ladder).toBe(false);
});
