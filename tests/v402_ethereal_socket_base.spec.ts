import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v402 — an ETHEREAL socketed base (e.g. a 4os ethereal War Scepter) keeps its ⊘ ETH flag. The eth flag rides
// on the per-entry `sockets` array (not parsed.ethereal), so the server forwards it under the registered label;
// the client _isEthereal then matches across the "(4os)"/"(Larzuk base)" suffix in either direction.
test.describe('v402 ethereal socketed-base flag', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('_isEthereal matches a registered socketed base against a bare-base eth flag (both directions)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      eval("etherealItems.add('War Scepter')");           // AI flagged bare base
      const suffixSide = w._isEthereal('War Scepter (4os)');// registered WITH socket suffix
      eval("etherealItems.add('Gull (Larzuk base)')");     // AI flagged WITH suffix
      const bareSide = w._isEthereal('Gull');              // looked up bare
      const notEth = w._isEthereal('Grim Scythe (6os)');   // unrelated base
      return { suffixSide, bareSide, notEth };
    });
    expect(r.suffixSide).toBe(true);
    expect(r.bareSide).toBe(true);
    expect(r.notEth).toBe(false);
  });

  test('_etherNorm strips socket / Larzuk / low-base descriptors to the bare base', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      // _etherNorm is a top-level function; reach it via eval
      return {
        sock: eval("_etherNorm('War Scepter (4os)')"),
        larzuk: eval("_etherNorm('Cryptic Axe (Larzuk base)')"),
        low: eval("_etherNorm('Broad Sword (4os low base)')"),
        plain: eval("_etherNorm('Phase Blade')"),
      };
    });
    expect(r.sock).toBe('war scepter');
    expect(r.larzuk).toBe('cryptic axe');
    expect(r.low).toBe('broad sword');
    expect(r.plain).toBe('phase blade');
  });

  test('no console errors with the ethereal matching loaded', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    page.on('pageerror', (e) => errs.push(e.message));
    await page.evaluate(() => { (window as any)._isEthereal('War Scepter (4os)'); });
    await page.waitForTimeout(150);
    expect(errs).toEqual([]);
  });
});
