import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1703 — KONYO'S RULING ON FOUR UNIQUES, AND THE GHOST IT ALMOST CREATED.
 *
 * v645 reported four uniques as unreachable — Mahim-Oak Curio, Polaris Spear, Iron Jang Bong,
 * The Scourge — and they were held behind an ABSENT_PENDING_HIS_RULING allowlist because whether
 * they exist in Reign of the Warlock is a question about the MOD, not the code, and the answer
 * moves his grail denominator. He ruled: they exist.
 *
 * ⚠ TWO OF THEM ALREADY DID, AND ADDING THEM WOULD HAVE BEEN A REGRESSION. "The Mahim-Oak Curio"
 * and "The Iron Jang Bong" are in ITEM_VALUE, in _UNI_EXTRA, and SEEDED FOUND in _GRAIL_SEED
 * (May 18 / May 19, 2026). Only their BARE spellings were missing — and _norm() (bible.html:16609)
 * folds case and punctuation but NOT a leading "The ", so "Mahim-Oak Curio" and "The Mahim-Oak
 * Curio" are different roster keys. Minting the bare form would have produced a SECOND,
 * permanently-unfound card for an item he already owns: his missing list would grow by items he
 * has, and the denominator would inflate by two.
 *
 * So only Polaris Spear and The Scourge joined the roster; the bare spellings became name variants.
 * This file pins BOTH halves, because the dangerous half is the one that looks like a fix.
 *
 * ⚠ FIXTURES NEVER TOUCH LIVE DATA — everything here seeds through page.addInitScript, and the
 * lifecycle test restores what it toggles. Roster TOTALS are owned by v659_grail_seed.spec.ts and
 * deliberately not duplicated here.
 */

const NEWLY_ADDED = ['Polaris Spear', 'The Scourge'];
const ALREADY_HIS = ['The Mahim-Oak Curio', 'The Iron Jang Bong'];
const BARE_VARIANTS: Record<string, string> = {
  'Mahim-Oak Curio': 'The Mahim-Oak Curio',
  'Iron Jang Bong': 'The Iron Jang Bong',
};

test('the two genuinely-absent uniques are on the roster, resolve as uniques, and are tickable', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(2200);
  const r = await page.evaluate(async (names: string[]) => {
    const w: any = window;
    w.switchTab('funi');
    await new Promise((res) => setTimeout(res, 900));
    const box = document.getElementById('tab-funi')!;
    const ticks = new Set([...box.querySelectorAll('.gf-allgrid [data-gf-tick]')]
      .map((t: any) => t.getAttribute('data-gf-tick')));
    const roster = new Set(typeof w._gUniqueRoster === 'function' ? w._gUniqueRoster() : []);
    return names.map((n) => ({
      n,
      inRoster: roster.has(n),
      kind: (w.d2rResolveItem ? (w.d2rResolveItem(n) || {}).kind : null) || null,
      // THE THING HE ACTUALLY NEEDS: somewhere to record the find
      hasTick: ticks.has(n),
    }));
  }, NEWLY_ADDED);

  for (const row of r) {
    expect(row.inRoster, `${row.n} is not on _gUniqueRoster()`).toBe(true);
    expect(row.kind, `${row.n} does not resolve as a unique`).toBe('unique');
    expect(row.hasTick, `${row.n} has no tick in the F·Uniques grid — he cannot record finding it`).toBe(true);
  }
});

test('a find of a newly-added unique lands in the shared LEDGER, never the profile-scoped vault', async ({ page }) => {
  /* v1696's defect, and these two are exactly its shape: toggleOwned() routed items that were in
     the widened roster but not in (ITEMS ∪ _UNI_EXTRA) into d2r_owned — which forks per profile —
     instead of d2r_foundLog, which MAIN and LADDER share. A tick that does not cross to LADDER is
     a silent ladder-doctrine breach, so it is pinned here rather than assumed. */
  await page.goto(URL);
  await page.waitForTimeout(2200);
  const r = await page.evaluate(async (names: string[]) => {
    const w: any = window;
    const out: any[] = [];
    for (const n of names) {
      w.toggleOwned(n);
      const log = JSON.parse(localStorage.getItem('d2r_foundLog') || '{}');
      const vault = JSON.parse(localStorage.getItem('d2r_owned') || '[]');
      const after = { n, inLedger: Object.prototype.hasOwnProperty.call(log, n), inVault: vault.indexOf(n) >= 0 };
      w.toggleOwned(n);   // restore — this test must leave the board as it found it
      const log2 = JSON.parse(localStorage.getItem('d2r_foundLog') || '{}');
      out.push({ ...after, restored: !Object.prototype.hasOwnProperty.call(log2, n) });
    }
    return out;
  }, NEWLY_ADDED);

  for (const row of r) {
    expect(row.inLedger, `${row.n} did not reach d2r_foundLog (the SHARED chronicle)`).toBe(true);
    expect(row.inVault, `${row.n} landed in d2r_owned — the vault forks per profile, so this would not cross to LADDER`).toBe(false);
    expect(row.restored, `${row.n} survived its own un-tick`).toBe(true);
  }
});

test('NO GHOST ROWS — the bare spellings must NOT become second roster entries', async ({ page }) => {
  /* The half that looks like a fix and is not. If a future change "helpfully" adds the bare names,
     his missing list grows by two items he already owns and the denominator inflates. */
  await page.goto(URL);
  await page.waitForTimeout(2200);
  const r = await page.evaluate(async (payload: { bare: string[]; canonical: string[] }) => {
    const w: any = window;
    w.switchTab('funi');
    await new Promise((res) => setTimeout(res, 900));
    const box = document.getElementById('tab-funi')!;
    const ticks = new Set([...box.querySelectorAll('.gf-allgrid [data-gf-tick]')]
      .map((t: any) => t.getAttribute('data-gf-tick')));
    const roster = new Set(typeof w._gUniqueRoster === 'function' ? w._gUniqueRoster() : []);
    const log = JSON.parse(localStorage.getItem('d2r_foundLog') || '{}');
    return {
      bareInRoster: payload.bare.filter((n) => roster.has(n)),
      bareHasTick: payload.bare.filter((n) => ticks.has(n)),
      canonicalInRoster: payload.canonical.filter((n) => roster.has(n)),
      canonicalFound: payload.canonical.filter((n) => Object.prototype.hasOwnProperty.call(log, n)),
      canonicalHasTick: payload.canonical.filter((n) => ticks.has(n)),
    };
  }, { bare: Object.keys(BARE_VARIANTS), canonical: ALREADY_HIS });

  expect(r.bareInRoster, 'a bare spelling became a SECOND roster row for an item he already owns').toEqual([]);
  expect(r.bareHasTick, 'a bare spelling rendered its own tick — that is a ghost of an owned item').toEqual([]);
  // and the real ones are present AND already his
  expect(r.canonicalInRoster.sort(), 'the canonical "The …" names must stay on the roster').toEqual([...ALREADY_HIS].sort());
  expect(r.canonicalFound.sort(), 'both are seeded FOUND — he already owns them').toEqual([...ALREADY_HIS].sort());
  // already found ⇒ they are NOT in the missing grid, which is why a naive probe reports them absent
  expect(r.canonicalHasTick, 'an already-found unique must not sit in the MISSING grid').toEqual([]);
});
