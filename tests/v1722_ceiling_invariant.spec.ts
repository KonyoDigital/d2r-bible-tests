import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1722 — A CEILING MAY NOT BE LOWER THAN WHAT IT LETS THROUGH.
//
// Konyo, on the last open item: "derive it from the rows and gate it".
//
// Each boss difficulty declares `tcMax` (the top item tier that kill can produce) and `mlvl`.
// Both are hand-authored vanilla-era annotations. The ODDS beside them have been re-pulled five
// times — v129, v187, v697, v1716, v1721 — and the annotations never moved with them. Measured on
// the tree before this fix:
//
//     50 of 66 cells declared a tcMax BELOW what their own rows prove droppable
//        (Pindle NORM declared TC30 and drops Ginther's Rift at TC85, 1:45,761 — silospen's own
//         number, and real: Pindle is an ACT 5 monster, so Normal there is nothing like Act 3)
//     51 of 66 cells have rows that drop despite qlvl > that cell's own mlvl (715 rows)
//     735 of 737 TC reasons named a ceiling the same cell contradicts
//
// The fix raises tcMax to what its rows prove and NEVER lowers it — lowering would invent a
// ceiling nothing disproves, which is how these numbers went stale in the first place. `mlvl` is
// deliberately NOT derived: monster level is a game fact, not a ceiling, so instead the qlvl
// reason is suppressed in any cell whose own data breaks that rule.
//
// This spec is the part that keeps it true. It reads the DATA, not the prose.

const boot = async (page: any) => { await page.goto(URL); await page.waitForTimeout(2000); };

const COLS: [string, string][] = [
  ['norm', 'NORM'], ['normTz', 'NORM TZ'], ['nm', 'NM'],
  ['nmTz', 'NM TZ'], ['hell', 'HELL'], ['hellTz', 'HELL TZ'],
];

test.describe('v1722 — the ceiling agrees with what drops under it', () => {
  test('★★★ no cell declares a tcMax below the TC of an item it actually drops', async ({ page }) => {
    await boot(page);
    // BOSSES is a module const — the audit is published from inside its scope so this can never
    // silently skip. The non-vacuity checks below caught exactly that when it read window.BOSSES.
    const r = await page.evaluate(() => {
      const w: any = window;
      const rows = w._ceilingAudit ? w._ceilingAudit() : [];
      const bad = rows
        .filter((x: any) => x.proven !== null && x.proven > x.declared)
        .map((x: any) => `${x.boss} ${x.cell}: declares TC${x.declared} but drops TC${x.proven}`);
      return { bad, cells: rows.length, proven: rows.filter((x: any) => x.proven !== null).length };
    });
    // non-vacuity: this must actually have had cells to judge
    expect(r.cells, 'no boss difficulty cells were read').toBeGreaterThan(60);
    expect(r.proven, 'no cell had a single row with a known TC — nothing was measured').toBeGreaterThan(60);
    expect(r.bad, 'ceilings contradicted by their own rows: ' + r.bad.join(' | ')).toEqual([]);
  });

  test('★★ no blocked reason cites a rule its own cell disproves', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const bad: string[] = [];
      let reasons = 0;
      // rebuild the per-cell truth, then read the reasons the engine actually produced
      const violates: Record<string, boolean> = {};
      const ceiling: Record<string, number> = {};
      (w._ceilingAudit ? w._ceilingAudit() : []).forEach((x: any) => {
        violates[x.boss + '|' + x.col] = x.qlvlBroken;
        ceiling[x.boss + '|' + x.col] = x.declared;
      });
      for (const it of (w._allDropItems ? w._allDropItems() : [])) {
        for (const s of (it.sources || [])) {
          if (!s || !s.blocked) continue;
          reasons++;
          const key = s.bossId + '|' + s.diffKey;
          if (/^qlvl /.test(s.blocked) && violates[key]) {
            bad.push(`${it.n} @ ${s.boss}: "${s.blocked}" — but items of that qlvl DO drop in this cell`);
          }
          const m = /^TC (\d+) > .* TC (\d+)$/.exec(s.blocked);
          if (m && Number(m[2]) !== ceiling[key]) {
            bad.push(`${it.n} @ ${s.boss}: reason cites TC${m[2]} but the cell declares TC${ceiling[key]}`);
          }
        }
      }
      return { bad: bad.slice(0, 10), badN: bad.length, reasons };
    });
    expect(r.reasons, 'no blocked reasons were produced — nothing was measured').toBeGreaterThan(100);
    expect(r.bad, `${r.badN} self-contradicting reasons: ` + r.bad.join(' | ')).toEqual([]);
  });

  /* v1723 — AND THE FACT MUST SURVIVE THE REASON.
     v1722's suppression deleted the source entry entirely when neither annotation could explain
     an empty cell, so the "cannot drop here" marker vanished with the bad explanation. Routine L
     caught it — probe_meph_shako lost its norm/normTz/nm keys, which had been present-and-null.
     Every row that does not drop must still SAY so; only the false reason goes. */
  test('★★ a cell that cannot drop an item still says so, even when no rule explains why',
    async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const reg = (w.ITEM_REGISTRY || {});
      const shako = reg['Harlequin Crest (Shako)'];
      const cells = (shako ? shako.sources : [])
        .filter((s: any) => s.bossId === 'mephisto')
        .map((s: any) => s.diffKey);
      const reasons = (shako ? shako.sources : [])
        .filter((s: any) => s.bossId === 'mephisto' && s.chance == null)
        .map((s: any) => s.blocked);
      return { cells, reasons, all: cells.length };
    });
    // Shako is TC60/qlvl69: it drops at Hell/HellTZ/NM-TZ and cannot at Normal/NormalTZ/NM.
    // All six cells must be REPRESENTED — three with odds, three with an honest reason.
    expect(r.all, 'Mephisto cells represented for Shako: ' + r.cells.join(',')).toBe(6);
    expect(r.reasons.every((x: any) => !!x), 'a non-dropping cell carried no reason at all').toBe(true);
  });
});
