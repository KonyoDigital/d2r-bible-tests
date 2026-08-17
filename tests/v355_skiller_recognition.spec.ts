// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';

// v355 — magic-find tooltips recognise skillers + known valuable magic items (cross-ref D2_VAL_MAGIC),
// diacritic-folded so the AI's "Harpoönist's" (umlaut OCR) still matches "Harpoonist's".

const URL = 'file://' + process.cwd() + '/bible.html';

test('skiller + valuable-magic recognition (diacritic-folded)', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.goto(URL);
  await page.waitForTimeout(2200);
  const r = await page.evaluate(() => {
    const w = window as any;
    return {
      isSkillerUmlaut: w._isSkiller("Harpoönist's Grand Charm"),   // umlaut OCR
      isSkillerPlain: w._isSkiller("Harpoonist's Grand Charm"),
      notSkiller: w._isSkiller("Steelgoad Voulge"),
      vmUmlaut: w._magicValue("Harpoönist's Grand Charm"),         // folded match
      vmRare: w._magicValue("Harpoönist's Grand Charm (rare)"),    // suffix-stripped
    };
  });
  expect(errs).toEqual([]);
  expect(r.isSkillerUmlaut).toBe(true);
  expect(r.isSkillerPlain).toBe(true);
  expect(r.notSkiller).toBe(false);
  expect(r.vmUmlaut && r.vmUmlaut.v).toBe('med');     // matched across the umlaut
  expect(r.vmRare && r.vmRare.v).toBe('med');
});
