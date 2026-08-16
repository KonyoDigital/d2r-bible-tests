import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1726 — AN ITEM'S CARD MUST NAME THE BASE IT ACTUALLY DROPS ON.
//
// Found by the fleet sweep, then audited across all 321 codex entries (the sweep could only
// resolve 189; normalising case first raised that to 259).
//
// THREE DISTINCT CLASSES, and they must not be conflated:
//
//   1. TIER SUBSTITUTION — the entry names the ELITE base while storing the EXCEPTIONAL tier's
//      requirements. Proof needs no outside authority: a unique cannot require a LOWER level than
//      the base it sits on, and the stored requirements match a different tier exactly.
//        Jalal's Mane        named Dream Spirit (elite, reqLvl 66) with reqLvl 42, reqStr 65 —
//                            and its own note says "druid grail pelt"; of the seven bases at
//                            reqStr 65, only Totemic Mask (exceptional, reqLvl 41) is a pelt.
//        Bartuc's Cut-Throat named Runic Talons (elite, reqLvl 60) with reqLvl 42, 79/79 —
//                            exactly one candidate: Greater Talons (exceptional, reqLvl 37).
//      Both corrected. This class is ZERO TOLERANCE.
//
//   2. A BASE THAT IS NOT AN ITEM — `Polaris Spear` and `The Scourge` gave their base as
//      "Reign of the Warlock", the MOD'S NAME. (The same signature identified `Bloodmoon's Light`
//      as a garbled row in v1725, but these two are real RotW customs, so the FIELD was nulled
//      rather than the item deleted: unknown beats wrong.) Also zero tolerance.
//
//   3. A LEVEL THAT DISAGREES BY A LITTLE — three entries name the right base but its reqLvl
//      exceeds the item's by 1-6. One of the two numbers is off and nothing in this repo says
//      which, so they are COUNTED, not guessed at. A pinned count means a fourth cannot appear
//      unnoticed while the three stay honest.
//
// Skystrike was investigated and DISMISSED: a unique may carry higher requirements than its base
// (reqStr 25 on an 18-str Edge Bow is legal), so it is not a defect. Recorded because a sweep that
// only reports hits teaches nothing about its own precision.

const BIBLE = fs.readFileSync(path.resolve(__dirname, '..', 'bible.html'), 'utf8');

function literal(name: string): any {
  const i = BIBLE.indexOf(`const ${name} = `);
  const j = BIBLE.indexOf('\n', i);
  return JSON.parse(BIBLE.slice(i + `const ${name} = `.length, j).trim().replace(/;$/, ''));
}

const CODEX = literal('ITEM_CODEX');
const BASES = literal('BASE_DB');

test.describe('v1726 — the base an item names is the base it drops on', () => {
  test('★★★ no entry names a base that requires a higher level than the item (tier substitution)', async () => {
    const bad: string[] = [];
    for (const [name, e] of Object.entries<any>(CODEX)) {
      const b = e.base && BASES[e.base];
      if (!b || e.reqLvl == null || b.reqLvl == null) continue;
      const gap = b.reqLvl - e.reqLvl;
      if (gap <= 0) continue;
      // a large gap PLUS requirements that match another tier exactly is the substitution signature
      const twin = Object.entries<any>(BASES).find(([, v]) =>
        v.tier !== b.tier && v.reqStr === e.reqStr &&
        (e.reqDex == null || v.reqDex === e.reqDex) && v.reqLvl != null && v.reqLvl <= e.reqLvl);
      if (gap >= 10 && twin) {
        bad.push(`${name}: names ${e.base} (${b.tier}, reqLvl ${b.reqLvl}) but its reqs match ${twin[0]} (${twin[1].tier})`);
      }
    }
    expect(bad, 'tier-substituted bases: ' + bad.join(' | ')).toEqual([]);
  });

  test('★★★ no entry gives the MOD as its base item', async () => {
    const bad = Object.entries<any>(CODEX)
      .filter(([, e]) => e.base && /reign of the warlock/i.test(String(e.base)))
      .map(([n]) => n);
    expect(bad, 'entries whose base is the mod name — a garbled ingest row: ' + bad.join(', ')).toEqual([]);
  });

  test('★★ base names resolve in BASE_DB, case included', async () => {
    const lower: Record<string, string> = {};
    for (const k of Object.keys(BASES)) lower[k.toLowerCase()] = k;
    // a base that differs from BASE_DB ONLY by case is a lookup that silently returns nothing —
    // 67 entries were in this state, so their cards could show no base requirements at all.
    const caseOnly = Object.entries<any>(CODEX)
      .filter(([, e]) => e.base && !BASES[e.base] && lower[String(e.base).toLowerCase()])
      .map(([n, e]) => `${n} (${e.base})`);
    expect(caseOnly, 'bases that differ from BASE_DB only by case: ' + caseOnly.join(', ')).toEqual([]);
  });

  test('★ the honest residue is counted, not guessed at', async () => {
    const unresolved = Object.entries<any>(CODEX).filter(([, e]) => e.base && !BASES[e.base]);
    const levelGap = Object.entries<any>(CODEX).filter(([, e]) => {
      const b = e.base && BASES[e.base];
      return b && e.reqLvl != null && b.reqLvl != null && b.reqLvl > e.reqLvl;
    }).map(([n, e]) => `${n}/${e.base}`);
    // unresolved bases are generic slots the BASE_DB does not model (Amulet, Ring, Gloves,
    // Pandemonium Event Key). Pinned so a NEW unresolvable name is noticed.
    expect(unresolved.length, 'codex bases not in BASE_DB').toBeLessThanOrEqual(62);
    // three entries name the right base but disagree with it by 1-6 levels. Nothing in this repo
    // says which side is wrong, so they stay reported rather than invented.
    expect(levelGap.length, 'base-vs-item level disagreements: ' + levelGap.join(', ')).toBeLessThanOrEqual(3);
  });
});
