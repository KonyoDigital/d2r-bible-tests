// v460 — ETH-WORTHY HIGHLIGHT: when a base is ethereal, the runeword guidance calls out WHY eth is worth
// keeping (merc weapon / static armor — +50% damage/defense, can't be repaired). Rides _baseRWLine so it shows
// everywhere (Socketed Review, throw-out, detail card, cursor tooltip). Only fires for ethereal items.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v460 eth-worthy highlight', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForFunction(() => (window as any)._baseRWLine && (window as any)._isEthereal && (window as any)._ethWorthyNote);
  });

  test('_ethWorthyNote is type-aware (polearm = merc Insight/Infinity; armor = +50% def)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      return { polearm: w._ethWorthyNote('Thresher'), armor: w._ethWorthyNote('Archon Plate'),
               ring: w._ethWorthyNote('Ring') };
    });
    expect(r.polearm).toMatch(/Insight|Infinity|merc/);
    expect(r.armor).toMatch(/\+50% defense|Fortitude/);
    expect(r.ring).toBe('');   // rings can't be ethereal → no note
  });

  test('a NON-ethereal base shows NO eth note in _baseRWLine', async ({ page }) => {
    const line = await page.evaluate(() => (window as any)._baseRWLine('Thresher', 5));
    expect(line).not.toContain('Ethereal — worth keeping');
  });

  test('an ETHEREAL base shows the eth note in _baseRWLine (rides the guidance)', async ({ page }) => {
    const line = await page.evaluate(() => {
      const w = window as any;
      w.etherealItems.add('Thresher (5os)');   // mark this base ethereal
      return w._baseRWLine('Thresher', 5);
    });
    expect(line).toContain('Ethereal — worth keeping');
    expect(line).toMatch(/Insight|Infinity|merc/);
  });

  test('eth note + Socketed Review ⊘ ETH badge appear for an owned ethereal socketed base', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w._ensureSocketBaseEntry('Thresher (5os)');
      eval('owned').add('Thresher (5os)');
      w.etherealItems.add('Thresher (5os)');
      w.renderVault();
      const el = document.getElementById('vault-socketed');
      return { html: el ? el.innerHTML : '' };
    });
    expect(r.html).toContain('⊘ ETH');                    // the badge
    expect(r.html).toContain('Ethereal — worth keeping'); // the note (via _baseRWLine)
  });
});
