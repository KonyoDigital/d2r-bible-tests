import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v527 — the Tools "Loot Filters" card embeds both Chronicle filters as importable JSON with a one-tap
// copy-to-clipboard. Guards: card exists, copy fn exists, both filters parse, and no WHITE circlets leak
// into the embedded base-show rules (rare-only circlets, mirroring the app's runeword-worthiness rule).

test('Tools loot-filter card: both filters embedded as valid, circlet-clean, importable JSON', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const parse = (id: string) => { const el = document.getElementById(id); try { return el ? JSON.parse(el.textContent!.trim()) : null; } catch (e) { return null; } };
    const c = parse('lf-data-chron'), e = parse('lf-data-endgame');
    const whiteCircletLeak = (f: any) => !f ? true : f.rules
      .filter((r: any) => ['3. Show ETH and Socket bases', 'Show Base Items'].includes(r.name))
      .some((r: any) => (r.equipmentCategory || []).includes('circl') || (r.equipmentItemCode || []).some((x: string) => ['ci0', 'ci1', 'ci2', 'ci3'].includes(x)));
    return {
      card: !!document.getElementById('loot-filters-card'),
      copyFn: typeof w.copyLootFilter,
      chronName: c && c.name, chronRules: c && c.rules.length,
      endgameName: e && e.name, endgameRules: e && e.rules.length,
      chronLeak: whiteCircletLeak(c), endgameLeak: whiteCircletLeak(e),
    };
  });
  expect(r.card).toBe(true);
  expect(r.copyFn).toBe('function');
  expect(r.chronName).toBe('KonyoChron');   expect(r.chronRules).toBe(13);
  expect(r.endgameName).toBe('KonyoEndgame'); expect(r.endgameRules).toBe(13);
  expect(r.chronLeak).toBe(false);          // no white circlets in the embedded filter
  expect(r.endgameLeak).toBe(false);
});
