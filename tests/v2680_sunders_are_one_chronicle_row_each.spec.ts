import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v2680 — THE SIX SUNDER CHARMS ARE ONE CHRONICLE ROW EACH, AND THE VAULT STILL KNOWS THE LATENT ONES.
//
// Konyo, 2026-09-05, reading his own panel: "yes we have latent of bone break but the chronicle
// itself is not latent thats just the upgraded version of it after we upgrade in hordaic cube.. so
// for the chronicle all sunders 6 of them need to be counted in the chronicle specifically as 1
// tally for each.. and for the vault that a different story the entire item database should be
// there regardless."
//
// SETTLED FROM THE GAME FILE, NOT FROM ARGUMENT. uniqueitems.txt was re-extracted from the live
// 28 GB RotW CASC store and tv/chronicle_total.py --count reproduced every cached number exactly
// (439 rows · 24 disableChronicle · 36 notSpawnable · 403 chronicle · 396 distinct · 7 duplicate).
// On that file the game's Chronicle carries EXACTLY SIX sunder rows —
//   PreCrafted Bone Break · Cold Rupture · Crack of the Heavens · Flame Rift · Rotting Fissure · Black Cleft
// — and ZERO rows for any "Latent …" form. Before the fix the roster carried BOTH spellings for all
// six: 12 entries where the game has 6, so each sunder asked him to find it twice.
//
// VENUE: a browser spec. Runs on GitHub CI, never on his Mac. [[test-venue]]

const SUNDERS = ['Bone Break', 'Cold Rupture', 'Crack of the Heavens',
                 'Flame Rift', 'Rotting Fissure', 'Black Cleft'];

test('the chronicle counts each sunder ONCE — six tallies, no Latent twin', async ({ page }) => {
  await page.goto(URL);
  await page.waitForFunction(() => typeof (window as any)._gUniqueRoster === 'function',
                             null, { timeout: 60000 });
  const r = await page.evaluate((sun: string[]) => {
    const w: any = window;
    const roster: string[] = (w._gUniqueRoster() || [])
      .map((x: any) => (typeof x === 'string' ? x : x && (x.name || x.n)))
      .filter(Boolean);
    return {
      rosterN: roster.length,
      bare: sun.filter((s) => roster.indexOf(s) >= 0),
      latent: sun.filter((s) => roster.indexOf('Latent ' + s) >= 0),
      anyLatent: roster.filter((n) => /^Latent /.test(n)),
    };
  }, SUNDERS);

  // DENOMINATOR FIRST — an empty roster would make every "0 latent" below true for the wrong
  // reason, and it would read exactly like success. [[zero-needs-a-denominator]]
  expect(r.rosterN, 'the roster is empty, so this test measures nothing').toBeGreaterThan(300);

  expect(r.bare.sort(), 'every sunder must have exactly one chronicle row').toEqual([...SUNDERS].sort());
  expect(r.latent, 'a "Latent <sunder>" row is the upgraded form, not a second chronicle item — '
    + 'the game file lists ZERO of them, so each of these asks him to find one charm twice')
    .toEqual([]);
  expect(r.anyLatent, 'no Latent name belongs in the chronicle roster').toEqual([]);
});

test('the VAULT knows all THREE forms of every sunder — 18 distinct, the chronicle still 6', async ({ page }) => {
  /* v2681 — his ruling, in his words: "the vault and the console as a whole engine need to know
     there is 3 of them distinct" · "thats fine that there is 3 different wording for sunders" ·
     "but the chronicle is 1 only" · "for each".

     The game backs the three forms exactly — from its own string table
     (data:data/local/lng/strings/item-names.json, extracted from his 28 GB store):
         index 'Cold Rupture'            -> 'Cold Rupture'
         index 'PreCrafted Cold Rupture' -> 'Latent Cold Rupture'
         index 'Crafted Cold Rupture'    -> 'Renewed Cold Rupture'
     6 sunders x 3 forms = 18 items; the CHRONICLE row is the PreCrafted one, so 6 tallies.

     ⚠ MEASURED BEFORE THIS SHIPPED: the vault resolved 12 of 18 — every 'Renewed …' form was
     missing from the item database, so a reel reading one would not have resolved it. A dedicated
     sunder table knew all three, but the vault's lookup did not. Two halves, never joined.
     [[the-unjoined-end]] */
  await page.goto(URL);
  await page.waitForFunction(() => !!(window as any)._UNI_EXTRA && typeof (window as any)._gUniqueRoster === 'function',
                             null, { timeout: 60000 });
  const r = await page.evaluate((sun: string[]) => {
    const w: any = window;
    const ue = w._UNI_EXTRA || {}, ex = w.EXTRA_ITEMS || {}, iv = w.ITEM_VALUE || {};
    const roster: string[] = (w._gUniqueRoster() || [])
      .map((x: any) => (typeof x === 'string' ? x : x && (x.name || x.n))).filter(Boolean);
    const names: string[] = [];
    sun.forEach((s2) => ['', 'Latent ', 'Renewed '].forEach((p) => names.push(p + s2)));
    return {
      total: names.length,
      vault: names.filter((n) => !!(ue[n] || ex[n] || iv[n])),
      missingFromVault: names.filter((n) => !(ue[n] || ex[n] || iv[n])),
      chronicle: names.filter((n) => roster.indexOf(n) >= 0),
    };
  }, SUNDERS);

  expect(r.total, 'six sunders in three forms is eighteen names').toBe(18);
  expect(r.missingFromVault,
    'the vault must resolve all three forms — a reel that reads one of these would otherwise come '
    + 'back unknown').toEqual([]);
  expect(r.vault.length, 'the vault knows every form').toBe(18);
  expect(r.chronicle.length,
    'the chronicle is ONE row per sunder — six. Any more and he is asked to find one charm twice')
    .toBe(6);
});

test('the VAULT still knows every Latent charm — that database is a different story', async ({ page }) => {
  // His words. The chronicle filter must never reach the item database: a Latent charm READ from a
  // reel still has to resolve to a real item, or the vault would call his own drop unknown.
  await page.goto(URL);
  await page.waitForFunction(() => !!(window as any)._UNI_EXTRA, null, { timeout: 60000 });
  const r = await page.evaluate((sun: string[]) => {
    const w: any = window;
    const ue = w._UNI_EXTRA || {}, ex = w.EXTRA_ITEMS || {};
    return {
      ueN: Object.keys(ue).length,
      inUniExtra: sun.filter((s) => !!ue['Latent ' + s]),
      inExtraItems: sun.filter((s) => !!ex['Latent ' + s]),
    };
  }, SUNDERS);
  expect(r.ueN, '_UNI_EXTRA is empty, so this proves nothing').toBeGreaterThan(50);
  expect(r.inUniExtra.sort(), 'the item database must keep all six Latent charms')
    .toEqual([...SUNDERS].sort());
  expect(r.inExtraItems.sort(), 'EXTRA_ITEMS must keep them too — the vault reads from here')
    .toEqual([...SUNDERS].sort());
});
