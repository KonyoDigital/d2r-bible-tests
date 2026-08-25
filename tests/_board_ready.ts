/* v2108 — WAIT FOR THE BOARD, DO NOT SLEEP AND HOPE.
 *
 * bible.html is ~5.9MB and builds its rosters (RUNEWORD_TIP, CRAFTS, the *Scan functions)
 * after load. Fifty-one specs paired `await page.waitForTimeout(1500)` with an evaluate that
 * reads one of those globals — and every one of them has the same failure mode when a CI
 * runner is loaded: the global is not there yet, `|| {}` swallows it, the fixture seeds
 * NOTHING, and the assertion then reports a PRODUCT defect that is really the harness
 * arriving early.
 *
 * Two of them actually fired on 2026-08-25 — v592 (seeded an empty d2r_rwMade, then accused
 * the loot filter) and v559 (read a toast that had not been created yet). Both were green in
 * four consecutive runs and red in one, with the only ship in between touching a different
 * surface entirely. That is the signature of a flake, and a gate that is sometimes red has
 * stopped carrying information — the same defect as one that is always green.
 *
 * Use this instead of a sleep. It waits for the thing you are about to read.
 */
import type { Page } from '@playwright/test';

/** Wait until every named global is present on the board (default: the runeword roster). */
export async function boardReady(
  page: Page,
  names: string[] = ['RUNEWORD_TIP'],
  timeout = 30000,
): Promise<void> {
  await page.waitForFunction(
    (ns: string[]) => ns.every((n) => {
      const v = (window as any)[n];
      if (typeof v === 'function') return true;
      return !!v && Object.keys(v).length > 0;   // an EMPTY roster is not a ready one
    }),
    names,
    { timeout },
  );
}
