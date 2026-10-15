import { test, expect } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import * as fs from 'fs';
import * as path from 'path';

// REG-2247 (#74) — HIS RULING 2026-10-15: publish THE STASH on the roster too.
// Before this, each PC published characters / vault / reels but no stash: the roster "Vault grid"
// room another owner redraws had nothing to draw, so it read "not published" even when he owned
// items. His owned items (the book's flat `owned` list the board already posts) ARE his stash
// contents, so roster_publish.stash_rows_of must yield them, same shape as the vault section.
//
// The publish is a Python action (tv/roster_publish.py builds the body, tv/control_app.py POSTs it
// to the live site). The POST itself is a network action with no CI seam, but the body builder is a
// pure, unit-testable seam. This spec exercises the REAL Python pipeline — clean_book ->
// stash_rows_of -> stash_read -> sections_from — on a fixture and proves the published sections now
// carry a non-empty `stash` shaped exactly like `vault`. RED before the fix (no stash section),
// GREEN after. Runs on GitHub CI only — it shells to python3 and never boots his console or reads
// his data (fixture book only). Repo is PUBLIC: no absolute user paths, cwd is the repo root.

const REPO_ROOT = path.resolve(__dirname, '..');

function runPy(script: string): any {
  const out = execFileSync('python3', ['-I', '-c', script], {
    cwd: REPO_ROOT,
    encoding: 'utf8',
  });
  const line = out.trim().split('\n').pop() as string;
  return JSON.parse(line);
}

// A book shaped like his LIVE one: builds present, but the per-build stash/inv cells are empty, and
// the flat `owned` list carries the item names. Before the fix this publishes no stash at all.
const PY_PIPELINE = `
import sys, json
sys.path.insert(0, "tv")
import roster_publish as RP
NOW = 1790000000000
book = RP.clean_book({
    "builds": [{"name": "Konyolock", "cls": "Warlock", "level": 88,
                "sets": [{"name": "Set 1", "slots": {}, "inv": []}], "stash": []}],
    "owned": ["Shako", "Ber Rune", "Griffon's Eye"],
})
rows = RP.stash_rows_of(book)
reads = {"stash": RP.stash_read(rows, NOW)} if rows else {}
# the vault section, from the same names, is the shape the stash must match
reads["vault"] = RP.vault_read("ok", [{"name": n} for n in (book.get("owned") or [])], NOW)
secs = RP.sections_from(reads, NOW)
stash = secs.get("stash")
vault = secs.get("vault")
print(json.dumps({
    "hasStash": "stash" in secs,
    "stashCounts": (stash or {}).get("counts"),
    "stashRowNames": [r.get("name") for r in ((stash or {}).get("rows") or [])],
    "stashKeys": sorted((stash or {}).keys()),
    "vaultKeys": sorted((vault or {}).keys()),
}))
`;

// A book with NO publishable builds must STILL publish its stash from `owned` — the stash is a
// first-class per-PC section, not a rider on the characters read (control_app._roster_reads edit).
const PY_BUILDLESS = `
import sys, json
sys.path.insert(0, "tv")
import roster_publish as RP
rows = RP.stash_rows_of({"builds": [], "owned": ["Shako", "Ber Rune"]})
print(json.dumps({"rowNames": [r.get("name") for r in rows]}))
`;

test.describe('v3744 — the roster publishes the stash (REG-2247, #74)', () => {
  test('the published sections include a non-empty stash, shaped like vault', () => {
    const r = runPy(PY_PIPELINE);
    expect(
      r.hasStash,
      'roster_publish published no `stash` section for a book whose items live in `owned` — ' +
        'the roster room has nothing to draw and reads "not published" (REG-2247)'
    ).toBe(true);
    expect(r.stashCounts, 'the stash section carries a count of his owned items').toBe(3);
    expect(r.stashRowNames).toEqual(['Shako', 'Ber Rune', "Griffon's Eye"]);
    // same shape as the vault section his other roster rooms already read
    expect(r.stashKeys, 'the stash section must be shaped like the vault section').toEqual(
      r.vaultKeys
    );
  });

  test('a book with no publishable builds still publishes its stash from owned', () => {
    const r = runPy(PY_BUILDLESS);
    expect(
      r.rowNames,
      'a stash is derivable from `owned` alone — it does not require a character build (REG-2247)'
    ).toEqual(['Shako', 'Ber Rune']);
  });

  test('control_app._roster_reads reads the stash for any stored book, not only one with builds', () => {
    const src = fs.readFileSync(path.join(REPO_ROOT, 'tv', 'control_app.py'), 'utf8');
    const reads = src.split('def _roster_reads(')[1].split('def _roster_post(')[0];
    expect(reads, 'the stash read is wired into _roster_reads').toContain('_rp.stash_rows_of(');
    // The stash read must sit under its OWN `if isinstance(book, dict):` guard — not nested inside
    // the `book.get("builds")` branch that also gates the characters-from-book read. Nested, a PC
    // that draws its characters from char_select (no publishable builds) never even attempts a
    // stash read, so it can never publish a stash (REG-2247). Inspect the nearest guard above the
    // stash read.
    const beforeStash = reads.slice(0, reads.indexOf('_rp.stash_rows_of('));
    const guardAt = beforeStash.lastIndexOf('if isinstance(book, dict)');
    expect(guardAt, 'the stash read is guarded by an isinstance(book, dict) check').toBeGreaterThan(-1);
    const guardLine = beforeStash.slice(guardAt).split('\n')[0];
    expect(
      guardLine.includes('book.get("builds")'),
      'the stash read still sits inside the `book.get("builds")` characters branch — lift it to ' +
        'its own `if isinstance(book, dict):` guard so every PC publishes its stash (REG-2247)'
    ).toBe(false);
    expect(
      guardLine.includes('if isinstance(book, dict):'),
      'the stash read must be guarded by a standalone `if isinstance(book, dict):` (REG-2247)'
    ).toBe(true);
  });
});
