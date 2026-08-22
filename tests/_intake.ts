import type { Page } from '@playwright/test';

/* v1993 — SEED INTAKE THROUGH THE DOOR THAT STILL EXISTS.
 *
 * Konyo asked for the manual AI-intake doors to be removed — "surgically remove them all… that way
 * it forces me and my cuzin to just hit reel session instead of anything manual" — and v1975/v1976
 * did exactly that: `vault-intake-file`, `rune-intake-file`, `gem-intake-file` and
 * `material-intake-file` are GONE from bible.html (5 file inputs remain, none of them these).
 *
 * Seventeen tests across seven specs still seeded themselves with
 * `page.setInputFiles('#vault-intake-file', …)`. Playwright waits for a selector that will never
 * exist, so each one burned its full 120s timeout and CI shard 4/6 sat RED — 11 failed / 330 passed
 * — for every ship since. The tests were not wrong about the LOGIC they assert (dedup, shared-stash
 * routing, cost reporting, the throw-out triage); they were wrong about the DOOR.
 *
 * The intake functions themselves never went anywhere: window.vaultIntake / runeIntake / gemIntake /
 * materialIntake are all still exported, and they are the very seam the automated lane feeds —
 * tvStashAutoIntake "only supplies a File" to these same functions. So seeding through them makes
 * these specs exercise the AUTOMATED path rather than a door the product no longer has.
 *
 * [[the-unjoined-end]] [[label-outlived-referent]] [[feedback-blind-fixture-green-gate]]
 */

export type SeedFile = { name: string; mimeType?: string; buffer: Buffer | Uint8Array };

const FN: Record<string, string> = {
  vault: 'vaultIntake',
  rune: 'runeIntake',
  runes: 'runeIntake',
  gem: 'gemIntake',
  gems: 'gemIntake',
  material: 'materialIntake',
  materials: 'materialIntake',
};

/** Hand the lane's intake function real File objects, exactly as the reel lane does. */
export async function seedIntake(page: Page, lane: keyof typeof FN | string, files: SeedFile[]) {
  const fn = FN[String(lane)];
  if (!fn) throw new Error('seedIntake: unknown lane ' + lane);
  const payload = files.map((f) => ({
    name: f.name,
    type: f.mimeType || 'image/jpeg',
    bytes: Array.from(f.buffer as Uint8Array),
  }));
  return page.evaluate(
    async ({ fn, payload }) => {
      const w: any = window;
      if (typeof w[fn] !== 'function') {
        throw new Error('seedIntake: window.' + fn + ' is not a function — the intake seam moved');
      }
      const fs = payload.map(
        (p: any) => new File([new Uint8Array(p.bytes)], p.name, { type: p.type })
      );
      return await w[fn](fs);
    },
    { fn, payload }
  );
}
