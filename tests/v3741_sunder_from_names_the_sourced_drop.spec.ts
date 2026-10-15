import { test, expect } from '@playwright/test';
import path from 'path';

/* REG-2239 (#93, #320 carried) - THE SUNDER "drops from" ROW MUST NAME THE SOURCED DROP.
 *
 * The section head, the blurb, the card chip, the drop stat and all six `rate` fields already say
 * a Latent drops from "any Terror-Zone monster, Heralds most often" (Maxroll, the source the cards
 * cite - #320, REG-2126/2142/2131/2146). The six charm `from` arrays still said
 * ["Hell TZ Heralds of Terror"], so the SAME card named two different drop sources: the rate said
 * any Terror-Zone monster, the "drops from" row said Hell-TZ Heralds.
 *
 * Why every earlier sweep passed: test_no_sunder_text_says_what_its_own_source_refutes matched only
 * the HYPHEN spelling "Hell-TZ Herald" (that law, line 576), never the SPACE spelling that lives in
 * these arrays - the house scar, "one spelling wide", again.
 *
 * This sweeps the CLASS, not one spelling. Every Sunder is read through the REAL resolver
 * (findMaterial) and the REAL card renderer (materialDetailHtml) - the single `item.from` both the
 * ID card and renderSpecialDrops consume - and neither the data nor the rendered "drops from" row
 * may name Hell-TZ / Hell TZ Heralds as the source; all must name the sourced breadth instead.
 */
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const CHARMS = ['Bone Break', 'Black Cleft', 'Crack of the Heavens',
                'Cold Rupture', 'Flame Rift', 'Rotting Fissure'];
const NARROW = 'Hell[- ]?TZ Herald|Heralds of Terror';   // the refuted narrow source, either spelling
const SOURCED = 'any Terror-Zone monster';               // the breadth the cited source establishes

async function boot(page: any) {
  await page.goto(URL);
  await page.waitForTimeout(2500);
}

test('every Sunder drops-from names the sourced drop, never Hell-TZ Heralds (#93, #320)', async ({ page }) => {
  await boot(page);
  const r = await page.evaluate((a: { charms: string[]; narrow: string; sourced: string }) => {
    const w: any = window;
    const fm = w.findMaterial, mdh = w.materialDetailHtml;
    const narrow = new RegExp(a.narrow, 'i');
    const out: any = {
      isFn: typeof fm === 'function' && typeof mdh === 'function',
      resolved: 0, notSunder: [] as string[], fromNarrow: [] as string[],
      fromMissingBreadth: [] as string[], rateMissingBreadth: [] as string[],
      renderNarrow: [] as string[], renderMissingBreadth: [] as string[],
    };
    a.charms.forEach(function (n) {
      const m = fm ? fm(n) : null;
      if (!m) return;
      out.resolved++;
      if (m.catKey !== 'sunder') { out.notSunder.push(n + ':' + m.catKey); return; }
      const fromStr = (m.item.from || []).join(' OR ');
      const rateStr = String(m.item.rate || '');
      const html = mdh ? String(mdh(n)) : '';
      if (narrow.test(fromStr)) out.fromNarrow.push(n + ': ' + fromStr);
      if (fromStr.indexOf(a.sourced) < 0) out.fromMissingBreadth.push(n + ': ' + fromStr);
      if (rateStr.indexOf(a.sourced) < 0) out.rateMissingBreadth.push(n + ': ' + rateStr);
      if (narrow.test(html)) out.renderNarrow.push(n);
      if (html.indexOf(a.sourced) < 0) out.renderMissingBreadth.push(n);
    });
    return out;
  }, { charms: CHARMS, narrow: NARROW, sourced: SOURCED });

  /* A SAMPLE OF ZERO PASSES EVERYTHING BELOW - refuse rather than report clean. */
  expect(r.isFn, 'findMaterial / materialDetailHtml are absent - this test measured NOTHING').toBe(true);
  expect(r.resolved, `PRINT THE DENOMINATOR: only ${r.resolved}/6 Sunder charms resolved through findMaterial`).toBe(6);
  expect(r.notSunder, `a charm did not resolve to the sunder category: ${JSON.stringify(r.notSunder)}`).toEqual([]);

  /* THE DEFECT: the drops-from row named the narrow Hell-TZ Heralds source its own rate refutes. */
  expect(r.fromNarrow,
    'a Sunder from-array still names Hell-TZ / Hell TZ Heralds as the drop source - the exact claim '
    + 'its own rate and blurb refute: ' + JSON.stringify(r.fromNarrow)).toEqual([]);
  expect(r.renderNarrow,
    'a rendered Sunder card still shows Hell-TZ Heralds in its drops-from row: ' + JSON.stringify(r.renderNarrow)).toEqual([]);

  /* AND THE CONSISTENCY: from, rate and the rendered card all name the sourced breadth. */
  expect(r.fromMissingBreadth,
    'a Sunder from-array does not name the sourced drop (any Terror-Zone monster): ' + JSON.stringify(r.fromMissingBreadth)).toEqual([]);
  expect(r.rateMissingBreadth,
    'a Sunder rate no longer names the sourced drop: ' + JSON.stringify(r.rateMissingBreadth)).toEqual([]);
  expect(r.renderMissingBreadth,
    'a rendered Sunder card does not name the sourced drop: ' + JSON.stringify(r.renderMissingBreadth)).toEqual([]);
});
