import type { Page } from '@playwright/test';

/* v1751 — OPEN A TOOLS CARD, DETERMINISTICALLY. ONE COPY, FOUR CALLERS.
 *
 * `window.toggleCardCollapse(id)` is a TOGGLE and it opens with `if (!card) return;` — a SILENT
 * no-op. Four specs called it blind, wrapped in a try/catch commented "already expanded", and that
 * comment is wrong twice over: the function never throws, so the catch is dead, and if the card
 * IS already expanded the toggle CLOSES it. Both failure modes end the same way — a collapsed
 * card, whose getComputedStyle still resolves every colour and gradient you ask for while
 * getBoundingClientRect() reports 0x0. A spec then measures a card it believes it opened.
 *
 * That is not theory: it is the v157 CI flake, which failed on `headerH: 0` one line AFTER its
 * `linear-gradient` assertion passed. The other three sites were the same code waiting for a
 * slow enough shard.
 *
 * bible.html already does this correctly of its own accord, twice (:5868 and :21601):
 *     if (card && card.classList.contains('collapsed')) toggleCardCollapse(id)
 * This is that idiom, plus the two waits it needs to be honest.
 *
 * WAIT FOR THE STATE, NEVER FOR MILLISECONDS. A fixed sleep is a bet on the boot time of a
 * machine you do not own; every one of these specs runs on a 6-shard CI runner under load.
 *
 * IT WAITS FOR **OPEN**, NEVER FOR **TALL**. That distinction is the whole point — a card that
 * opens flat must still fail its caller's geometry assertion rather than be waited into looking
 * fine. [[feedback_suspect_the_instrument]] [[copy-drift]]
 */
export async function ensureCardExpanded(page: Page, cardId: string, readySelector?: string) {
  await page.evaluate(() => {
    try { (window as any).switchTab && (window as any).switchTab('tools'); } catch (e) {}
  });

  // 1. the card must EXIST — this is the guard the silent `if (!card) return;` never gave us
  await page.waitForFunction((id: string) => !!document.getElementById(id), cardId, { timeout: 20000 });

  // 2. expand ONLY if collapsed
  await page.evaluate((id: string) => {
    const c = document.getElementById(id);
    if (c && c.classList.contains('collapsed')) (window as any).toggleCardCollapse(id);
  }, cardId);

  // 3. the class must have actually cleared
  await page.waitForFunction((id: string) => {
    const c = document.getElementById(id);
    return !!c && !c.classList.contains('collapsed');
  }, cardId, { timeout: 20000 });

  // 4. and the card's own contents must be rendered, when the caller can name them
  if (readySelector) {
    await page.waitForFunction((sel: string) => !!document.querySelector(sel), readySelector,
                               { timeout: 20000 });
  }

  await page.waitForTimeout(250);   // one layout settle after the class flips
}
