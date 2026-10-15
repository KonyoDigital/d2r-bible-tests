import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/*
 * REG-2232 (#16) — THE 400-ROW LEDGER CAP EVICTED THE FRESHEST ROW, NOT THE STALEST.
 *
 * d2r_chronicleInboxLog is trimmed to the last 400 rows by _chLogSave (`.slice(-400)`), which keeps
 * them BY ARRAY POSITION. _chLogUpsert stamped a fresh `lastTs` on every touched row but updated it
 * IN PLACE (`log[ix] = next`), so a re-read row kept its first-insertion index. The one surface he
 * reads, renderRoutingLedger, orders rows newest-first BY `lastTs`. The two orderings agreed until a
 * row was re-read, then disagreed for exactly the rows worth keeping: a name he keeps seeing (a
 * re-read Spirit) carried a fresh lastTs at a low index and was sliced off the front by a single new
 * registration, while staler rows inserted after it survived. REG-312 made the subtitle admit "the
 * oldest decisions drop"; the writer was dropping a recently-seen one instead.
 *
 * The fix moves a touched row to the TAIL so array position tracks last-touch, and `.slice(-400)`
 * then keeps the 400 the panel would show as newest. The cap itself (400, his number) is unchanged.
 *
 * RED on the in-place writer: Spirit (touched last) is evicted and the stalest filler survives.
 * GREEN after move-to-tail: Spirit survives and the genuinely stalest filler is the one dropped.
 */
test.describe('REG-2232 — the ledger cap keeps the most recently seen row', () => {
  test.beforeEach(async ({ page }) => {
    // owner world → bare keys and his board, the same environment the writer runs in live
    await page.addInitScript(() => { try { localStorage.setItem('d2r_ownerClaim', '*'); } catch (e) {} });
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('★★★ a re-read row survives the cap while the genuinely stalest row is dropped', async ({ page }) => {
    const out = await page.evaluate(() => {
      const w: any = window;
      const OLD = 1000;

      // Seed the store to exactly the 400-row cap, through the SAME door the writer uses (LSR), so
      // the key routing is identical. Spirit is the OLDEST-inserted row (index 0); every row shares
      // one long-ago lastTs, so the only thing that makes one "fresh" is the re-read below.
      const seed: any[] = [{ name: 'Spirit', status: 'pending', store: 'foundLog', firstTs: OLD, lastTs: OLD }];
      for (let i = 1; i <= 399; i++) {
        seed.push({ name: 'filler_' + i, status: 'pending', store: 'foundLog', firstTs: OLD, lastTs: OLD });
      }
      w.LSR.setItem('d2r_chronicleInboxLog', JSON.stringify(seed));

      // He sees Spirit again — a genuine re-read through the published writer. It stamps a fresh
      // lastTs and bumps seenCount, which is why the panel would now show it at the very top.
      w.kaiChronicleRecord({ name: 'Spirit', status: 'pending', store: 'foundLog', _bump: true });

      // One NEW registration arrives, taking the store to 401 and forcing exactly one eviction.
      w.kaiChronicleRecord({ name: 'Brand New Drop', status: 'pending', store: 'foundLog' });

      const log = JSON.parse(w.LSR.getItem('d2r_chronicleInboxLog') || '[]');
      const names = log.map((r: any) => String(r.name));
      const spirit = log.find((r: any) => r.name === 'Spirit') || null;
      return {
        len: log.length,
        hasSpirit: names.indexOf('Spirit') >= 0,
        hasStalest: names.indexOf('filler_1') >= 0,   // the row untouched longest = the correct victim
        hasNew: names.indexOf('Brand New Drop') >= 0,
        spiritFresh: !!(spirit && Number(spirit.lastTs) > OLD),
        spiritSeen: spirit ? Number(spirit.seenCount || 0) : -1,
      };
    });

    expect(out.len, 'the cap no longer holds at 400').toBe(400);
    expect(out.hasNew, 'the newest registration was not kept').toBe(true);

    // the heart of it: the row he just re-read is the LAST thing the cap should throw away
    expect(out.hasSpirit, 'the re-read Spirit row was evicted — the cap trims by array position, not by recency').toBe(true);
    expect(out.hasStalest, 'the genuinely stalest row survived while the freshest was dropped — eviction is not by recency').toBe(false);

    // corroboration that the re-read actually registered as fresh on the surviving row
    expect(out.spiritFresh, 'the surviving Spirit row did not carry the fresh re-read lastTs').toBe(true);
    expect(out.spiritSeen, 'the re-read did not bump seenCount on the kept row').toBeGreaterThanOrEqual(1);
  });
});
