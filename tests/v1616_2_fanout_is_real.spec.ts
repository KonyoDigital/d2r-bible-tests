import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1616.2 — THE FANOUT IS NOT ALLOWED TO BE DECORATION.
//
// _sliderFanout() is what finally connects the MF and /players sliders to the chronicles, and it
// calls all four of its targets through `typeof window.X === 'function'` guards. That pattern is
// the single most repeated bug in this repo (REG-083/087, the v1576 dead-safe classifier, the
// v1593 TZ crash, ~680 versions of unreachable shelf code, five ownership changes that never
// repainted): a guard naming a symbol that does not exist is permanently false, silently, and the
// code around it still "works" because it just does nothing.
//
// If that happened here the sliders would go back to moving nothing, and the only visible symptom
// would be Konyo saying it stopped working again — six months from now, with no error anywhere.
//
// So this asserts BOTH halves: every name is a real function, AND moving the slider actually
// reaches all four. Checking existence alone would pass on a repaint that is never invoked.

test('\u2605\u2605\u2605 every fanout target exists AND the slider reaches it', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2600);
  const exists = await page.evaluate(() => ({
    renderForgeUni: typeof (window as any).renderForgeUni,
    renderForgeSets: typeof (window as any).renderForgeSets,
    renderForge: typeof (window as any).renderForge,
    _writeSetFarm: typeof (window as any)._writeSetFarm,
  }));
  console.log('EXISTS ' + JSON.stringify(exists));

  // and prove the slider actually REACHES them
  const hit = await page.evaluate(async () => {
    const w: any = window; const seen: string[] = [];
    const names = ['renderForgeUni', 'renderForgeSets', 'renderForge', '_writeSetFarm'];
    const orig: any = {};
    names.forEach((n) => { orig[n] = w[n]; if (typeof w[n] === 'function') w[n] = () => { seen.push(n); }; });
    const m: any = document.getElementById('mf');
    m.value = '250'; m.dispatchEvent(new Event('input', { bubbles: true }));
    await new Promise((r) => setTimeout(r, 700));
    names.forEach((n) => { w[n] = orig[n]; });
    return seen;
  });
  console.log('REACHED ' + JSON.stringify(hit));
  for (const [k, v] of Object.entries(exists)) {
    expect(v, `${k} is named by a typeof guard but does not exist — the repaint is decoration`).toBe('function');
  }
  expect(hit.sort()).toEqual(['_writeSetFarm', 'renderForge', 'renderForgeSets', 'renderForgeUni']);
});
