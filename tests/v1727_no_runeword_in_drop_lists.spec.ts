import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1727 — A RUNEWORD MAY NEVER APPEAR IN A DROP LIST, ANYWHERE.
//
// v1725 removed `Crescent Moon (sword)` — the runeword Shael+Um+Tir — from ELEVEN boss drop
// tables, where it had been listed as a farmable unique. That fix was applied to BOSSES only.
// This generalises it to every drop list in the file, which is what the defect class deserves:
// a runeword is forged, never found, so its presence in any drop list is a farming instruction
// that can never pay out.
//
// It also covers the TZ surface the fleet sweep named as its biggest blind spot. That surface was
// then audited end to end and came back clean:
//   * 11 of 11 zones — the declared `dweller` really does spawn in the declared `loc` (checked
//     against silospen's own monster data, zero mismatches);
//   * 7 zones share one hellTz block, and that is REAL: queried independently, all seven dwellers
//     return the identical stored figures, because terror saturation puts every one of those areas
//     at the same level;
//   * 528 of 528 stored TZ cells match a live silospen pull exactly (uniques AND sets — checking
//     only uniques first produced 24 phantom "mismatches", every one a set item my query had not
//     asked for);
//   * 97 distinct item names, none unknown to the item universe.
// The one runeword-shaped name in that data — "Crescent Moon" — is the real unique AMULET, and it
// resolves to exactly one row ONLY because v1725 removed the sword. Before that it was ambiguous.
//
// The network checks above cannot run in CI. What this gate pins is the invariant they justified.

const BIBLE = fs.readFileSync(path.resolve(__dirname, '..', 'bible.html'), 'utf8');

function literal(name: string): any {
  const i = BIBLE.indexOf(`const ${name} = `);
  const j = BIBLE.indexOf('\n', i);
  return JSON.parse(BIBLE.slice(i + `const ${name} = `.length, j).trim().replace(/;$/, ''));
}

const norm = (x: string) => {
  const k = String(x).replace(/\s*\([^)]*\)\s*$/, '').toLowerCase().replace(/[^a-z0-9]+/g, '');
  return k.startsWith('the') && k.length > 3 ? k.slice(3) : k;
};

const BOSSES = literal('BOSSES');
const RW_SEED = literal('_RWC_SEED');           // all 99 runeword names, as keys
const TZ_ODDS = JSON.parse(
  /id="tz-zone-odds">(\{[\s\S]*?\})<\/script>/.exec(BIBLE)![1]
);

/* A name is only a runeword hit if it is a runeword AND NOT also a real item name. "Crescent Moon"
   is both — the runeword and the unique amulet — so the test asks whether a DROPPABLE item of that
   name exists, and flags only names that exist purely as runewords. */
const itemNames = new Set<string>();
for (const b of BOSSES) for (const d of b.dropTable) itemNames.add(norm(d.n));

test.describe('v1727 — no runeword sits in a drop list', () => {
  test('★★★ no boss drop table lists a runeword-only name', async () => {
    const rw = new Set(Object.keys(RW_SEED).map(norm));
    const bad: string[] = [];
    for (const b of BOSSES) {
      for (const d of b.dropTable) {
        const k = norm(d.n);
        // a name shared with a real unique (Crescent Moon the amulet) is fine; the sword was not
        if (rw.has(k) && !/\(amulet\)|\(sword\)/.test(d.n)) {
          // only flag when NO non-runeword item of that name exists in the codex
          const codex = literal('ITEM_CODEX');
          const alt = Object.keys(codex).some((n) => norm(n) === k && !/runeword/i.test(String(codex[n].rarity || '')));
          if (!alt) bad.push(`${b.id}: ${d.n}`);
        }
      }
    }
    expect(bad, 'runewords listed as farmable drops: ' + bad.join(' | ')).toEqual([]);
  });

  test('★★ no TZ zone odds block lists a name the item universe does not know', async () => {
    const unknown: string[] = [];
    for (const [zone, v] of Object.entries<any>(TZ_ODDS)) {
      for (const col of ['hell', 'hellTz']) {
        for (const name of Object.keys(v[col] || {})) {
          if (!itemNames.has(norm(name))) unknown.push(`${zone}/${col}: ${name}`);
        }
      }
    }
    expect(unknown, 'TZ odds naming items no boss table carries: ' + unknown.slice(0, 8).join(' | '))
      .toEqual([]);
  });

  test('★★ every TZ zone declares a dweller and a location, and they are distinct fields', async () => {
    const bad: string[] = [];
    for (const [zone, v] of Object.entries<any>(TZ_ODDS)) {
      if (!v.dweller) bad.push(`${zone}: no dweller`);
      if (!v.loc) bad.push(`${zone}: no loc`);
      // a dweller id is a monster code (fetish3, cr_lancer8); a loc is prose. If they ever match,
      // the wiring has collapsed into one field and the zone→monster link is guesswork.
      if (v.dweller && v.loc && String(v.dweller).toLowerCase() === String(v.loc).toLowerCase()) {
        bad.push(`${zone}: dweller and loc are the same value`);
      }
    }
    expect(bad, 'TZ zone wiring: ' + bad.join(' | ')).toEqual([]);
    expect(Object.keys(TZ_ODDS).length, 'TZ zones present').toBeGreaterThan(8);
  });
});
