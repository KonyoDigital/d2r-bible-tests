import { test, expect } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import * as path from 'path';

// REG-2249 (#74b) — residual on the REG-2247 (#74) fix. stash_rows_of first builds rows from the
// per-build STRUCTURED stash (positional cells, with mule/x/y/w/h), then appends every name in the
// book's flat `owned` list. It did NOT dedupe the two passes, so an item the book carries in BOTH
// places (the common case — `owned` IS his stash contents, per his 10-15 ruling) published TWO
// roster rows for ONE physical item. The grid room drew the item twice.
//
// FIX: the structured pass records the names it published (`seen`); the owned pass skips a name a
// structured row already drew. The file folds neither apostrophe nor case anywhere it matches
// names, and both passes read names raw from the same board pipeline, so the match is exact-string.
// Two copies in `owned` alone stay two rows (two physical items); two mules holding the same item
// stay two rows (the structured pass never dedupes against itself) — only the structured-vs-owned
// overlap is one item seen twice.
//
// This spec exercises the REAL Python seam (tv/roster_publish.stash_rows_of) on a fixture, like
// v3744_roster_publishes_stash. RED before the fix (the overlap name appears twice), GREEN after.
// Runs on GitHub CI only — it shells to python3 and never boots his console or reads his data
// (fixture book only). Repo is PUBLIC: no absolute user paths, cwd is the repo root.

const REPO_ROOT = path.resolve(__dirname, '..');

function runPy(script: string): any {
  const out = execFileSync('python3', ['-I', '-c', script], {
    cwd: REPO_ROOT,
    encoding: 'utf8',
  });
  const line = out.trim().split('\n').pop() as string;
  return JSON.parse(line);
}

// A book that carries "Shako" in BOTH the structured per-build stash (with its grid cell + mule)
// AND the flat `owned` list, plus an owned-only item ("Ber Rune"). Before the fix stash_rows_of
// yields "Shako" twice.
const PY_OVERLAP = `
import sys, json
sys.path.insert(0, "tv")
import roster_publish as RP
book = {
    "builds": [{"name": "Konyolock",
                "stash": [{"name": "Shako", "x": 0, "y": 0, "w": 2, "h": 2}],
                "sets": []}],
    "owned": ["Shako", "Ber Rune"],
}
rows = RP.stash_rows_of(book)
names = [r.get("name") for r in rows]
shako = [r for r in rows if r.get("name") == "Shako"]
print(json.dumps({
    "names": names,
    "shakoCount": names.count("Shako"),
    "berCount": names.count("Ber Rune"),
    # the surviving Shako must be the STRUCTURED row (carries mule/grid), not the bare owned name
    "shakoHasMule": bool(shako and shako[0].get("mule") == "Konyolock"),
    "shakoHasCell": bool(shako and shako[0].get("w") == 2),
}))
`;

// The dedupe must not over-reach: an owned-only item (no structured row of the same name) still
// yields its row. A buildless book publishes its whole `owned` list.
const PY_OWNED_ONLY = `
import sys, json
sys.path.insert(0, "tv")
import roster_publish as RP
rows = RP.stash_rows_of({"builds": [], "owned": ["Shako", "Ber Rune"]})
print(json.dumps({"names": [r.get("name") for r in rows]}))
`;

test.describe('v3745 — the roster stash dedupes owned against the structured stash (REG-2249, #74b)', () => {
  test('an item in both the structured stash and owned yields ONE row, not two', () => {
    const r = runPy(PY_OVERLAP);
    expect(
      r.shakoCount,
      'stash_rows_of published "Shako" twice — once from the per-build structured stash and again ' +
        'from the flat `owned` list. `owned` IS his stash contents, so an owned name a structured ' +
        'row already drew is the SAME physical item; dedupe it (REG-2249)'
    ).toBe(1);
    // the kept row is the structured one — the grid painter needs its mule/x/y/w/h, a bare owned
    // name has none of that, so dropping the structured copy would blank the grid cell
    expect(
      r.shakoHasMule && r.shakoHasCell,
      'the surviving "Shako" row must be the STRUCTURED one (keeps mule + grid cell), not the bare ' +
        'owned name — the roster grid painter draws from x/y/w/h (REG-2249)'
    ).toBe(true);
    // the owned-only item is untouched by the dedupe
    expect(r.berCount, 'an owned-only item still yields exactly one row').toBe(1);
    expect(r.names).toEqual(['Shako', 'Ber Rune']);
  });

  test('the dedupe does not drop an owned-only item (buildless book)', () => {
    const r = runPy(PY_OWNED_ONLY);
    expect(
      r.names,
      'with no structured stash to dedupe against, every `owned` name still yields its row — the ' +
        'dedupe skips only names a structured row already published (REG-2249)'
    ).toEqual(['Shako', 'Ber Rune']);
  });
});
