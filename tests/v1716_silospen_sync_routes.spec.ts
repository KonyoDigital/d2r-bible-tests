import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1716 — THE FARM BOARD WAS ROUTING OFF DATA THAT DID NOT COVER THE GAME.
//
// Konyo, on his own board: "for SETS i also see pindleskin as the runs... so thats definitely
// bugged.. + i see alot of UNVERIFIED boss hunts for farming which dont render anything at all."
//
// Both were true, and they were three separate defects:
//
//  1. SETS had no per-piece drop data at all — 14 "any piece" aggregate rows for 34 sets. The
//     picker maximises kph/chance and Pindleskin's kph (300-360) is 3-10x every other boss, so
//     the aggregate handed him TWO run cards, both Pindleskin, and 21 sets with no route.
//  2. The roster and the drop tables spell items differently. "Harlequin Crest" could not see
//     the row named "Harlequin Crest (Shako)", so the most farmed unique in the game rendered
//     as "no verified source yet" — 33 uniques sat in that bucket.
//  3. The tables were genuinely short: silospen RoW 3.0 lists 348 uniques for Hell Mephisto,
//     the tree carried 277.
//
// The 2026-08-16 silospen pull (D2R_ROW_3_0, MF=300, players=1, desecratedLevel 50/76/99 — the
// same convention the stored cells were pulled under: 230 of 243 overlapping Hell-Mephisto rows
// matched EXACTLY before anything was written) added 2,366 rows and re-synced 9,820 cells.
//
// What this spec pins is the OUTCOME on his board, not the pull.

const boot = async (page: any) => { await page.goto(URL); await page.waitForTimeout(2200); };

test.describe('v1716 — every hunt on the board resolves to a real run', () => {
  test('★ SETS route by PIECE, so the board is no longer one boss', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const sets = w.__allSets ? w.__allSets() : [];
      let pieces = 0, routed = 0;
      const bosses = new Set<string>();
      for (const st of sets) {
        for (const pn of (st.pieces || [])) {
          pieces++;
          const s = w._pieceSrc(pn);
          if (s && s.boss) { routed++; bosses.add(String(s.bossId || s.boss)); }
        }
      }
      return { sets: sets.length, pieces, routed, bosses: [...bosses] };
    });
    // the pull covers 134 of the 135 tracked pieces; a piece it does not cover falls back to the
    // set aggregate rather than to silence, so this floor is deliberately just under the total.
    expect(r.routed, 'set pieces with their own drop row').toBeGreaterThanOrEqual(r.pieces - 2);
    // THE BUG ITSELF: one boss answering for every set is what he saw. Any honest per-piece
    // routing spreads across the roster.
    expect(r.bosses.length, 'distinct bosses across piece routes').toBeGreaterThan(3);
  });

  test('★ the F-SETS board ranks hardest-first, like the uniques board', async ({ page }) => {
    await boot(page);
    const diffs = await page.evaluate(() => {
      const w: any = window;
      w.switchTab && w.switchTab('fsets');
      w.renderForgeSets && w.renderForgeSets();
      const box = document.getElementById('fsets-body')!;
      // .f-pipe is the run card; read the difficulty word out of its title line
      return [...box.querySelectorAll('.f-card.f-pipe')].map(c => {
        const t = (c.textContent || '');
        return /Hell/.test(t) ? 2 : /NM|Nightmare/.test(t) ? 1 : 0;
      });
    });
    expect(diffs.length, 'run cards on the sets board').toBeGreaterThan(2);
    for (let i = 1; i < diffs.length; i++) {
      expect(diffs[i], 'run ' + (i + 1) + ' must not be harder than the run above it').toBeLessThanOrEqual(diffs[i - 1]);
    }
  });

  test('★ Harlequin Crest has a run again — and keeps the name he ticks', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const fu = w.funiScan();
      const all = fu.missing.concat([]);
      const find = (n: string) => all.find((x: any) => x.n === n) || null;
      const shako = find('Harlequin Crest');
      const nosrc = fu.missing.filter((x: any) => !w._pickSrc(x.sources, x.n)).map((x: any) => x.n);
      return {
        shakoPresent: !!shako,
        shakoName: shako ? shako.n : null,
        shakoRouted: shako ? !!w._pickSrc(shako.sources, shako.n) : null,
        nosrc,
        found: fu.found,
      };
    });
    if (r.shakoPresent) {
      // the roster spelling is the LEDGER key — binding to the drop row must not rename it,
      // or a tick writes under a name nothing else reads (measured: 3 found uniques flipped
      // to missing the first time this returned the drop row itself).
      expect(r.shakoName, 'the roster name survives the bind').toBe('Harlequin Crest');
      expect(r.shakoRouted, 'Harlequin Crest resolves to a run').toBe(true);
    }
    // 33 before. What may honestly remain are items no boss drops: the six Sunder charms
    // (cubed), the Hellfire Torch (Uber Tristram) and Crescent Moon (two different uniques
    // share that name, so a single roster row cannot claim either one's odds).
    expect(r.nosrc.length, 'uniques with no tracked drop location: ' + r.nosrc.join(', ')).toBeLessThanOrEqual(10);
  });

  test('★ an ambiguous name stays unrouted rather than borrowing one', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const items = (w.ITEMS || []).filter((x: any) => /^Crescent Moon/.test(x.n)).map((x: any) => x.n);
      const fu = w.funiScan();
      const cm = fu.missing.find((x: any) => x.n === 'Crescent Moon');
      return { rows: items, unrouted: cm ? !w._pickSrc(cm.sources, cm.n) : null };
    });
    expect(r.rows.length, 'two different uniques are called Crescent Moon').toBeGreaterThan(1);
    if (r.unrouted !== null) {
      expect(r.unrouted, 'one roster row cannot speak for two items').toBe(true);
    }
  });
});
