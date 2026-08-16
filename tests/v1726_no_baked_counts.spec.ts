import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1726 — A COUNT BAKED INTO A STRING CANNOT SELF-UPDATE, AND THIS ONE DRIFTED THREE TIMES.
//
// The grail total has been 312, then 322, then 320. Each time, prose carried the old value:
// 103 off-grail item cards in EXTRA_ITEMS read "Not in the tracked 312/322 grail", ~10 zone notes
// said "322-item grail count", GAME_RULES.md said it twice, and a routine description called
// itself a "312-item click sweep" while its own script reads ITEMS.length.
//
// The fix was to delete the numbers, not to refresh them — the sentences never needed them. This
// gate stops the next person putting one back. tests/_data_locks.ts is the ONE definition; a
// figure the user reads must be computed from the data, never typed into prose beside it.

const BIBLE = fs.readFileSync(path.resolve(__dirname, '..', 'bible.html'), 'utf8');
const RULES = fs.readFileSync(path.resolve(__dirname, '..', 'GAME_RULES.md'), 'utf8');

test.describe('v1726 — no hard-coded grail totals in prose', () => {
  test('★★★ no "N-item grail" / "N/N grail" string is baked into bible.html', async () => {
    const patterns = [
      /\b\d{3}\/\d{3}\s+grail/g,        // "312/322 grail"
      /\b\d{3}-item\s+(?:boss-drop\s+)?grail/g,
      /\b\d{3}-item\s+grail\s+count/g,
      /\b\d{3}-item\s+click\s+sweep/g,
    ];
    const hits: string[] = [];
    for (const re of patterns) {
      for (const m of BIBLE.matchAll(re)) {
        const line = BIBLE.slice(0, m.index || 0).split('\n').length;
        hits.push(`bible.html:${line} "${m[0]}"`);
      }
    }
    expect(hits, 'a grail total is typed into prose — compute it or drop it: ' + hits.join(' | '))
      .toEqual([]);
  });

  test('★★ GAME_RULES.md does not restate the item count either', async () => {
    const hits = [...RULES.matchAll(/\b\d{3}\s+items\b|\b\d{3}-item\b/g)].map((m) => m[0]);
    // the ⚠ note itself cites the drift history (312 → 322 → 320); that is the one allowed use,
    // and it lives on a line that says "drifted", so exclude only that line.
    const real = hits.filter((h) => {
      const idx = RULES.indexOf(h);
      const line = RULES.slice(RULES.lastIndexOf('\n', idx) + 1, RULES.indexOf('\n', idx));
      return !/drifted/.test(line);
    });
    expect(real, 'GAME_RULES.md restates a count that lives in tests/_data_locks.ts: ' + real.join(', '))
      .toEqual([]);
  });
});
