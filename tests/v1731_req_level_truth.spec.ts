import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1731 — TWO TABLES STORED THE SAME REQUIREMENT AND DRIFTED.
//
// A fleet lens found what I had filed as unresolvable. I had written "three items name the right
// base but disagree with its level by 1-6, and nothing in the repo says which side is wrong."
// The repo did say — in ITEM_TIP, a second table I never looked at:
//
//   Darkforce Spawn      codex 64 · ITEM_TIP 65 · base Bloodlord Skull reqLvl 65
//   Astreon's Iron Ward  codex 60 · ITEM_TIP 66 · base Caduceus        reqLvl 66
//   Ghostflame           codex 62 · ITEM_TIP 66 · base Legend Spike    reqLvl 66
//
// Two independent in-file witnesses agree on the higher number and the codex stands alone on the
// lower one — and no character equips a Bloodlord Skull below 65 whatever a row says, since the
// effective requirement is max(base, unique). Both numbers reached a screen: renderCodexCard
// printed one, the hover card printed the other, inches apart.
//
// Fixed three ways: the three values raised; the card now DERIVES max(base, codex) so the two
// surfaces cannot disagree again; and this gate keeps the disagreement set empty.

const BIBLE = fs.readFileSync(path.resolve(__dirname, '..', 'bible.html'), 'utf8');
const lit = (n: string) => {
  const i = BIBLE.indexOf(`const ${n} = `);
  const j = BIBLE.indexOf('\n', i);
  return JSON.parse(BIBLE.slice(i + `const ${n} = `.length, j).trim().replace(/;$/, ''));
};
const CODEX = lit('ITEM_CODEX');
const BASES = lit('BASE_DB');
const TIP = lit('ITEM_TIP');

test.describe('v1731 — one required level, not two', () => {
  test('★★★ no codex entry sits below the base it names', async () => {
    const bad = Object.entries<any>(CODEX).filter(([, e]) => {
      const b = e.base && BASES[e.base];
      return b && e.reqLvl != null && b.reqLvl != null && b.reqLvl > e.reqLvl;
    }).map(([n, e]) => `${n}: reqLvl ${e.reqLvl} under ${e.base} (${BASES[e.base].reqLvl})`);
    expect(bad, 'items requiring less than their own base: ' + bad.join(' | ')).toEqual([]);
  });

  test('★★★ ITEM_CODEX and ITEM_TIP agree on every required level', async () => {
    const bad = Object.keys(CODEX).filter((n) =>
      TIP[n] && TIP[n].r != null && CODEX[n].reqLvl != null && TIP[n].r !== CODEX[n].reqLvl
    ).map((n) => `${n}: codex ${CODEX[n].reqLvl} vs tip ${TIP[n].r}`);
    // the fourth disagreement was Crescent Moon (sword) — the runeword whose codex entry v1725
    // left behind; removing it in v1731 emptied this set, which is why it can now be gated at 0.
    expect(bad, 'two tables disagreeing about one number: ' + bad.join(' | ')).toEqual([]);
  });

  test('★★ the runeword is gone from the item universe, not merely from the drop tables', async () => {
    expect(Object.keys(CODEX)).not.toContain('Crescent Moon (sword)');
  });
});
