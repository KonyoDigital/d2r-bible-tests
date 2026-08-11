/* ONE-SHOT BOOT APPLIES — DERIVED FROM bible.html, NEVER HAND-LISTED.
 *
 * v1692 and v1693 each ship a "fires exactly once" boot apply, guarded by a localStorage flag:
 * d2r_v1692FleshrenderApplied, d2r_v1693DigglerApplied, d2r_v1693RulingApplied. A spec that seeds
 * a non-empty d2r_foundLog and does NOT pre-set those flags gets twelve extra names applied to its
 * fixture during boot, and then measures them.
 *
 * WHY THIS FILE EXISTS RATHER THAN A CONSTANT IN EACH SPEC. v1692's spec hand-listed the one flag
 * that existed when it was written. v1693 added two more and did not update it, so an assertion
 * whose whole premise was "the page as he will see it on EVERY LOAD AFTER THE FIRST" quietly ran
 * as a first load, watched his ledger grow 346 -> 356, and reported it as "the app MUTATED his
 * ledger". The number was right, the app was right, and the fixture was the liar — the usual
 * culprit. 20 specs seed d2r_foundLog today and exactly 2 pre-set any flag, so the same trap is
 * armed under eighteen more.
 *
 * A hand-maintained list moves the trap rather than removing it: it only holds while every future
 * one-shot remembers to edit it. So the flags are READ OUT OF THE SHIPPED SOURCE. A one-shot that
 * exists is a one-shot this returns, on the commit that introduces it, with nobody remembering
 * anything.
 *
 * ⚠ THIS SUPPRESSES, IT DOES NOT DELETE. The applies are real, correct, and Konyo ruled on them.
 * Use this when a spec needs "his board on a later load"; use the FIRST-load path (no suppression)
 * when the apply itself is what is under test — v1692's own (3) and (5) still do exactly that.
 */
import * as fs from 'fs';
import * as path from 'path';

const BIBLE = path.resolve(__dirname, '..', 'bible.html');

/** Every one-shot guard key the shipped page reads, newest ships included, sorted for stability. */
export function oneShotFlagNames(src?: string): string[] {
  const text = src != null ? src : fs.readFileSync(BIBLE, 'utf8');
  // the guard is always a localStorage key of the form d2r_v<version><Thing>Applied
  const found = new Set(text.match(/d2r_v\d{3,4}[A-Za-z]*Applied/g) || []);
  return Array.from(found).sort();
}

/** {flag: '1'} — spread into a spec's seed overrides to boot as a LATER load. */
export function suppressOneShots(src?: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const k of oneShotFlagNames(src)) out[k] = '1';
  return out;
}
