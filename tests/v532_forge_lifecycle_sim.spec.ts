import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v532 — SIMULATION (locked into Routine I): the full Forge task lifecycle, not just a static render check.
// Drives the engine end-to-end the way Konyo does: a ready task → ✓ created → it evaporates + lands in the
// ✅ Completed tab → restore it → it's active again. Plus skip → restore, and the Completed clear/restore tools.
// This guards the "when finished, does it actually move forward?" behaviour that a plain E2E render wouldn't.

test.describe('Forge task lifecycle simulation', () => {
  test('create → completes & evaporates → Completed tab → restore → active again', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));
      localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 1, Tir: 1, Tal: 1, Sol: 1 })); // Insight
      localStorage.setItem('d2r_rwMade', JSON.stringify({}));
      localStorage.setItem('d2r_ladderMode', 'nonladder');
    });
    await page.goto(URL); await page.waitForTimeout(1600);
    const r = await page.evaluate(() => {
      const w: any = window;
      w._ensureSocketBaseEntry('Colossus Voulge (4os)');
      const readyBefore = w.forgeScan().now.some((t: any) => t.rw === 'Insight' && !t.deferred);
      // ✓ created (the Make-now button action)
      w.rwToggleMade('Insight');
      const activeAfter = w.forgeScan().now.some((t: any) => t.rw === 'Insight');
      const madeAfter = !!JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')['Insight'];
      // it should now appear in the Completed tab
      w.switchTab && w.switchTab('forge'); w.forgeSetFilter('completed');
      const inCompleted = Array.from(document.querySelectorAll('#tab-forge .f-donename')).some((e: any) => e.textContent === 'Insight');
      // restore it → back to active, gone from Completed
      w.rwToggleMade('Insight');
      const madeRestored = !!JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')['Insight'];
      const activeRestored = w.forgeScan().now.some((t: any) => t.rw === 'Insight');
      return { readyBefore, activeAfter, madeAfter, inCompleted, madeRestored, activeRestored };
    });
    expect(r.readyBefore).toBe(true);       // Insight was forge-ready
    expect(r.madeAfter).toBe(true);         // ✓ created marked it
    expect(r.activeAfter).toBe(false);      // and it evaporated from the active plan
    expect(r.inCompleted).toBe(true);       // it's in the ✅ Completed tab
    expect(r.madeRestored).toBe(false);     // restore un-marked it
    expect(r.activeRestored).toBe(true);    // and it's an active task again
  });

  test('skip → hidden from Make now → restore skipped → back', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));
      localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 1, Tir: 1, Tal: 1, Sol: 1 }));
      localStorage.setItem('d2r_rwMade', JSON.stringify({}));
      localStorage.setItem('d2r_forgeSkip', JSON.stringify([]));
      localStorage.setItem('d2r_ladderMode', 'nonladder');
    });
    await page.goto(URL); await page.waitForTimeout(1600);
    const r = await page.evaluate(() => {
      const w: any = window;
      w._ensureSocketBaseEntry('Colossus Voulge (4os)');
      w.switchTab && w.switchTab('forge'); w.forgeSetFilter('now'); w.renderForge();
      const shownBefore = Array.from(document.querySelectorAll('#tab-forge .f-cardtitle')).some((e: any) => /Insight/.test(e.textContent));
      w.forgeSkip('rw|Insight'); w.forgeSetFilter('now'); w.renderForge();
      const shownAfterSkip = Array.from(document.querySelectorAll('#tab-forge .f-cardtitle')).some((e: any) => /Insight/.test(e.textContent));
      const skipCount = JSON.parse(localStorage.getItem('d2r_forgeSkip') || '[]').length;
      w.forgeUnskipAll(); w.forgeSetFilter('now'); w.renderForge();
      const shownAfterRestore = Array.from(document.querySelectorAll('#tab-forge .f-cardtitle')).some((e: any) => /Insight/.test(e.textContent));
      return { shownBefore, shownAfterSkip, skipCount, shownAfterRestore };
    });
    expect(r.shownBefore).toBe(true);
    expect(r.shownAfterSkip).toBe(false);   // ✕ hid it
    expect(r.skipCount).toBe(1);
    expect(r.shownAfterRestore).toBe(true); // ↺ restore skipped brought it back
  });

  test('Completed tab: Clear hides the list (non-destructive), Restore brings it back', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('d2r_rwMade', JSON.stringify({ Spirit: 'Jun 28, 2026 · 12:00', Grief: 'Jun 29, 2026 · 10:00' }));
      localStorage.setItem('d2r_forgeDone', JSON.stringify([]));
    });
    await page.goto(URL); await page.waitForTimeout(1400);
    const r = await page.evaluate(() => {
      const w: any = window;
      w.switchTab && w.switchTab('forge'); w.forgeSetFilter('completed');
      const rows = () => document.querySelectorAll('#tab-forge .f-donerow').length;
      const before = rows();
      w.forgeClearCompleted(); w.forgeSetFilter('completed');
      const cleared = rows();
      const stillMade = Object.keys(JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')).length; // NOT un-created
      w.forgeRestoreCompleted(); w.forgeSetFilter('completed');
      const restored = rows();
      return { before, cleared, stillMade, restored };
    });
    expect(r.before).toBeGreaterThan(0);
    expect(r.cleared).toBe(0);           // Clear hides the rows
    expect(r.stillMade).toBeGreaterThan(0); // but they stay CREATED in the Chronicle (non-destructive)
    expect(r.restored).toBe(r.before);   // Restore brings the list back
  });
});
