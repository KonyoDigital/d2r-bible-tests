import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1958 (test-only) — A CURLY APOSTROPHE IS THE SAME ITEM. THE MULE ROUTER DID NOT AGREE.
 *
 * Konyo asked for the vault to "auto-arrange in mules based on the items the readers read". This
 * guards the half of that which was measurably wrong, and it was not a near-miss:
 *
 *   Griswold’s Redemption      → UNI-WEAPONS   (should be SETS-TAL-IK)
 *   Immortal King’s Soul Cage  → UNI-WEAPONS   (should be SETS-TAL-IK)
 *   M’avina’s True Sight       → UNI-WEAPONS   (should be SETS-REST)
 *   Tal Rasha’s Adjudication   → SHARED STASH  (should be SETS-TAL-IK)
 *   Horazon’s Splendor         → UNI-WEAPONS   (should be SETS-REST)
 *
 * Three major sets split across four mules, under a roster note in this very file that reads
 * "never split a set". The straight-apostrophe form of each routed correctly the whole time — the
 * difference was one byte, and OCR emits both. tv/chronicle_resolve.py:80 had folded ’ to ' since
 * 2026-08-18; the board never learned it, so the same name was one item to the console and two to
 * the board. It is also not hypothetical damage: the v440 comment beside _KEEP_SET records that his
 * four Horazon's pieces were once wrongly discarded as junk.
 *
 * WHY THIS TEST DERIVES ITS SAMPLE INSTEAD OF LISTING THOSE FIVE. A list of five names guards five
 * names. Every apostrophe-bearing set piece on the board is affected by construction, and new ones
 * arrive with every data update, so the sample is read out of the board's own tables at runtime and
 * the assertion is a RULE — curly routes where straight routes — rather than a snapshot. That is
 * the same correction made to test_counter_ledger.py earlier in this arc.
 *
 * MEASURED SCOPE: swept across all 206 apostrophe-bearing names the board knows — 119 of his 135
 * set pieces carry one — and 158 routed to a different mule depending on the byte. After v1958, zero. The 39 include Andariel's Visage,
 * Arkaine's Valor, Arreat's Face, Nightwing's Veil, Ormus' Robes, Skullder's Ire and Thundergod's
 * Vigor — every one of them body armour or a helm, every one landing in UNI-WEAPONS.
 *
 * SEEN RED: with the v1958 changes reverted, the first test fails on 158 of 206 names.
 */

test('★★★ Gheed’s Fortune stays in inventory whichever apostrophe reads it', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1600);

  /* The single highest-consequence member of the 39, and it deserves its own assertion because the
     sweep above would still pass if this one rule broke in some other way. KEEP_IN_INVENTORY exists
     because the charm only works on the character actively playing. With a curly apostrophe it
     routed `uni-weap` instead of `__keep` — muling it is not an untidy filing, it is moving the item
     somewhere it does nothing, and nothing on his screen would say so. */
  const r = await page.evaluate(() => {
    const w: any = window;
    const p = (n: string) => { try { return w.suggestMule(n); } catch (e) { return null; } };
    return { straight: p("Gheed's Fortune"), curly: p('Gheed’s Fortune') };
  });

  expect(r.straight?.id).toBe('__keep');
  expect(r.curly?.id, 'a curly apostrophe must not mule a keep-in-inventory charm').toBe('__keep');
});

test('★★★ a curly apostrophe routes to the same mule as a straight one', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1600);

  const r = await page.evaluate(() => {
    const w: any = window;
    // every name the board knows that carries an apostrophe — set pieces AND uniques, so the
    // sample covers both the normalized lookups (findSetPiece) and the exact-key ones (tipOf).
    const names = new Set<string>();
    try { (w._gUniqueRoster() || []).forEach((n: string) => { if (/'/.test(n)) names.add(n); }); } catch (e) {}
    /* __setPieceNames() and NOT `window.SETS` — the first draft of this test read w.SETS, which does
       not exist on this page and silently yielded ZERO set pieces. The sample still looked healthy
       (87 names, all uniques) and the test still passed, while covering none of the Griswold /
       Tal Rasha / Immortal King cases that motivated it. It undercounted the real breakage by 4x:
       158 of 206 names, not 39 of 87. A sample drawn from a source that returns nothing is the
       blind fixture in its purest form — green, and measuring air. */
    try { (w.__setPieceNames() || []).forEach((n: string) => { if (/'/.test(n)) names.add(n); }); } catch (e) {}
    const sample = [...names];
    const bad: any[] = [];
    sample.forEach((straight) => {
      const curly = straight.replace(/'/g, '’');
      let a: any = null, b: any = null;
      try { a = w.suggestMule(straight); } catch (e) {}
      try { b = w.suggestMule(curly); } catch (e) {}
      const ai = a && a.id, bi = b && b.id;
      if (ai !== bi) bad.push({ straight, straightMule: ai, curlyMule: bi });
    });
    return { n: sample.length, bad };
  });

  /* The floor is set from the measured population (206: 119 of his 135 set pieces carry an
     apostrophe, plus the uniques) and deliberately well below it, so a data update cannot fail this
     test — but a SOURCE that silently returns nothing, which is how the first draft went wrong,
     drops the sample to ~87 or 0 and trips it. A sample that found nothing is a broken instrument,
     never a pass. */
  expect(r.n, 'apostrophe sample collapsed — a name source returned nothing').toBeGreaterThan(150);
  expect(r.bad, `${r.bad.length}/${r.n} names route differently with a curly apostrophe`).toEqual([]);
});

test('★★ an OCR slip is filed as the item it is a misread of, and says so', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1600);

  const r = await page.evaluate(() => {
    const w: any = window;
    const probe = (n: string) => { try { return w.suggestMule(n); } catch (e) { return null; } };
    return {
      // Rattlecage is a Cuirass; the slip used to land in UNI-WEAPONS
      battlecage: probe('Battlecage'), rattlecage: probe('Rattlecage'),
      // Nagelring is a ring; the slip used to land in UNI-WEAPONS
      naglring: probe('Naglring'), nagelring: probe('Nagelring'),
      // a real find of his that is simply not on the roster must NOT be dragged onto a lookalike
      bloodShield: probe('Blood Shield'),
      resolveBloodShield: (() => { try { return w.d2rResolveItem('Blood Shield'); } catch (e) { return null; } })(),
      foldBloodShield: (() => { try { return w.d2rInboxEngine({ name: 'Blood Shield' }).canonical; } catch (e) { return 'threw'; } })(),
    };
  });

  expect(r.battlecage?.id, 'Battlecage must file where Rattlecage files').toBe(r.rattlecage?.id);
  expect(r.naglring?.id, 'Naglring must file where Nagelring files').toBe(r.nagelring?.id);
  // and it must NAME the repair rather than silently relabel
  expect(r.battlecage?.why || '').toContain('Rattlecage');
  expect(r.naglring?.why || '').toContain('Nagelring');
  // the conservative half: an unrostered real find folds to nothing and is left alone
  expect(r.foldBloodShield, 'a RotW custom must not be folded onto a roster lookalike').toBeNull();
});

test('★★ a name nothing recognises is not described as a weapon', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1600);

  const r = await page.evaluate(() => {
    const w: any = window;
    let s: any = null;
    /* The fixture matters and the obvious one is wrong: "Zoidberg Helm of Nonsense" never reaches
       the default line at all — ARMOR_RE matches the word "Helm" and files it to UNI-ARMOR. A
       nonsense name has to be nonsense in EVERY keyword list to exercise the branch under test,
       which is the blind-fixture trap in miniature: the first draft of this test passed the wrong
       string and failed for a reason that had nothing to do with the change. */
    try { s = w.suggestMule('Quovadis Fnord'); } catch (e) {}
    return { id: s && s.id, why: String((s && s.why) || '') };
  });

  /* He has no unsorted mule and inventing one would ask him to make a character in game, so the
     item still parks in weapons. What must not survive is the WORDING: "default: weapons" read as
     a classification for a name nothing had classified. The drawer is a park; the reason says so. */
  expect(r.why).not.toMatch(/^default: weapons$/);
  expect(r.why.toLowerCase()).toContain('nothing on the board recognises');
});
