import { test, expect } from '@playwright/test';

/* v3743 / REG-2242 (#76, 2026-10-15) — MERCENARY GEAR ROUTES TO THE SHARED STASH.
 *
 * His ruling: "mercenary gear like gullaume and andriels and maras are types of items that i want
 * in the sahred". A mercenary's gear is worn by a hireling every character can summon, so it lives
 * in the one stash every character reaches — not stranded on a single mule.
 *
 * suggestMule gets a MERC_GEAR rule that returns {id:'shared'} for a hireling-gear name. It sits on
 * the same footing as the war-gear rule: AFTER the keeper + share-override checks, and BEFORE the
 * set / runeword / unique drawers — so it catches Guillaume's Face (an Orphan's Call set piece) and
 * the merc-worn uniques alike. A forced 'mule' override still wins, so he can untick any of them,
 * and the rule never calls _shareDefault, so it cannot recurse.
 *
 * RED before the fix: Guillaume's Face routes to sets-rest, Andariel's Visage and Vampire Gaze to
 * uni-armor, and _shareDefault("Guillaume's Face") answers 'mule'. GREEN after: all answer 'shared'.
 * Mara's Kaleidoscope was already shared (high trade value), so it is a consistency check. Harlequin
 * Crest (Shako) and Shaftstop are the controls that prove the rule did not widen onto non-merc gear.
 *
 * Runs on GitHub CI, never on his Mac (test-venue).
 */

const URL = 'file://' + process.cwd() + '/bible.html';

test.describe('v3743 — mercenary gear → shared stash', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForFunction(
      () => typeof (window as any).suggestMule === 'function'
         && typeof (window as any)._shareDefault === 'function',
      null, { timeout: 20000 });
  });

  test('the three he named, plus an extended merc unique, route to the shared stash', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sm = (n: string, o?: any) => {
        try { return (window as any).suggestMule(n, o) || { id: '(null)', why: '' }; }
        catch (e) { return { id: 'THREW', why: '' }; }
      };
      const one = (n: string) => { const x = sm(n); return { id: x.id, why: String(x.why || '') }; };
      return {
        guillaume: one("Guillaume's Face"),    // an Orphan's Call set piece — the rule must beat the set branch
        andariel: one("Andariel's Visage"),
        mara: one("Mara's Kaleidoscope"),      // already shared on trade value; a consistency check
        vampire: one('Vampire Gaze'),          // an extended (not-named) merc unique
        andarielCurly: one('Andariel’s Visage'),   // an OCR curly apostrophe must fold to the same verdict
        guillaumeCurly: one('Guillaume’s Face'),
      };
    });
    expect(r.guillaume.id, "Guillaume's Face must reach the shared stash ahead of the set branch").toBe('shared');
    expect(r.guillaume.why, 'and by the mercenary rule').toMatch(/mercenary/i);
    expect(r.andariel.id, "Andariel's Visage is merc gear").toBe('shared');
    expect(r.andariel.why).toMatch(/mercenary/i);
    expect(r.mara.id, "Mara's Kaleidoscope is in the shared stash").toBe('shared');
    expect(r.vampire.id, 'Vampire Gaze is a canonical merc helm').toBe('shared');
    expect(r.vampire.why).toMatch(/mercenary/i);
    expect(r.andarielCurly.id, 'a curly apostrophe folds to the same route').toBe('shared');
    expect(r.guillaumeCurly.id, 'a curly apostrophe folds to the same route').toBe('shared');
  });

  test('a forced mule override wins, and the rule feeds the share-panel default without recursing', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sm = (n: string, o?: any) => {
        try { return (window as any).suggestMule(n, o) || { id: '(null)' }; }
        catch (e) { return { id: 'THREW' }; }
      };
      return {
        forcedOut: sm("Andariel's Visage", { _shareForceOut: true }).id,     // he unticked it → a forced 'mule'
        ruleOnly: sm("Andariel's Visage", { ignoreShareOverride: true }).id, // how _shareDefault asks (override-free)
        defMerc: (window as any)._shareDefault("Guillaume's Face"),          // the share panel's default tick
        defControl: (window as any)._shareDefault('Shaftstop'),              // a plain non-merc armour unique
      };
    });
    // a forced 'mule' override beats the merc rule and sends it to its slot mule
    expect(r.forcedOut, 'a forced mule override must win over the merc rule').not.toBe('shared');
    expect(r.forcedOut).toBe('uni-armor');
    // asked override-free (the shape _shareDefault uses) the rule keeps merc gear in the shared stash
    expect(r.ruleOnly, 'the rule itself routes merc gear to the shared stash').toBe('shared');
    // ...which is exactly what the share panel reads as the DEFAULT tick for a merc item
    expect(r.defMerc, 'merc gear is ticked into the shared stash by default').toBe('shared');
    // and a non-merc armour unique is still default-mule, so the rule did not widen the panel
    expect(r.defControl, 'a non-merc unique must not default into the shared stash').toBe('mule');
  });

  test('the rule does not widen onto non-merc uniques', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sm = (n: string) => {
        try { return (window as any).suggestMule(n) || { id: '(null)', why: '' }; }
        catch (e) { return { id: 'THREW', why: '' }; }
      };
      const one = (n: string) => { const x = sm(n); return { id: x.id, why: String(x.why || '') }; };
      return { shako: one('Harlequin Crest'), shaft: one('Shaftstop') };
    });
    // Harlequin Crest (Shako) is UNCHANGED: it reaches the shared stash on trade value, not merc gear
    expect(r.shako.id, 'Shako is unchanged — high trade value already shares it').toBe('shared');
    expect(r.shako.why, 'Shako must NOT be claimed by the merc rule').not.toMatch(/mercenary/i);
    // a plain non-merc armour unique stays in its slot mule — the rule did not swallow the roster
    expect(r.shaft.id, 'a non-merc armour unique is untouched by the merc rule').toBe('uni-armor');
  });
});
