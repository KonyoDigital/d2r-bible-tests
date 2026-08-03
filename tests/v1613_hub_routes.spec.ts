import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1613 — THE HUNT HUB IS ROUTABLE.
//
// Konyo, in four messages about four surfaces:
//   "frostburn item should be clickable and routable to like the info of the item itself"
//   "durance of hate should be clicked and routed to mephisto.. for the run itself and farming"
//   "for daily task force when clicked on a grail it should route me to the accordingly relevant tab"
//   "same for open forge should be clickable under the missions"
//
// One complaint four times: Sessions TELLS him things and then makes him go find them. Every name
// already knew where it belonged — the hero knows its item, the TZ card knows its boss, a
// task-force row knows its ledger, a forge chip literally SAYS "open Forge" — and none was a link.
//
// These tests care that the ROUTE IS CORRECT, not merely that something is clickable. A control
// that fires the wrong destination is worse than one that fires nothing, because it looks like it
// worked.

const ORIGIN = 'http://tvd.console.test';
const UI = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

test.describe('v1613 — every name on the hunt hub goes where it says', () => {
  test('★ the shared router exists and is published', async ({ page }) => {
    await page.route(ORIGIN + '/ui', (r: any) =>
      r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
    await page.route((u: URL) => u.pathname.startsWith('/api/'),
      (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
    await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);
    const api = await page.evaluate(() => ({
      go: typeof (window as any)._hubGo,
      item: typeof (window as any)._hubGoItem,
      boss: typeof (window as any)._hubGoBoss,
    }));
    expect(api).toMatchObject({ go: 'function', item: 'function', boss: 'function' });
  });

  test('★★ the routes point at tabs the BOARD actually has', async () => {
    // The killer failure here is a plausible-looking tab name that does not exist: shellOpen would
    // succeed, the pane would open, and nothing would switch — a dead link that looks alive.
    const board = fs.readFileSync(path.resolve(__dirname, '..', 'bible.html'), 'utf8');
    const boardTabs = new Set(
      [...board.matchAll(/data-tab="([a-z0-9-]+)"/g)].map((m) => m[1]));
    for (const tab of ['funi', 'fsets', 'runes', 'forge', 'bosses']) {
      expect(boardTabs.has(tab), `the console routes to "${tab}" but the board has no such tab`).toBe(true);
    }
  });

  test('★★ every TZ boss id is a real boss in the board\'s BOSSES[]', async () => {
    // Same class, one level deeper: openBossDetail('mephsito') would open the tab and then quietly
    // do nothing. The ids must come from the board's own data, not from my spelling.
    const ui = UI;
    const board = fs.readFileSync(path.resolve(__dirname, '..', 'bible.html'), 'utf8');
    const map = ui.slice(ui.indexOf('var TZ_BOSS = {'), ui.indexOf('var TZ_HINT = {'));
    const ids = [...map.matchAll(/:\s*'([a-z0-9]+)'/g)].map((m) => m[1]);
    expect(ids.length, 'TZ_BOSS should not be empty').toBeGreaterThan(8);
    const bossIds = new Set([...board.matchAll(/"id"\s*:\s*"([a-z0-9]+)"/g)].map((m) => m[1]));
    for (const id of ids) {
      expect(bossIds.has(id), `TZ_BOSS maps to "${id}" but no boss with that id exists`).toBe(true);
    }
  });

  test('★ Durance of Hate routes to Mephisto specifically', async () => {
    const map = UI.slice(UI.indexOf('var TZ_BOSS = {'), UI.indexOf('var TZ_HINT = {'));
    expect(map).toMatch(/'Durance of Hate':\s*'mephisto'/);
  });

  test('★ the grail hero name is a real control, with a tooltip', async () => {
    const fn = UI.slice(UI.indexOf('function hubNextGrail'), UI.indexOf('window._hubNextGrail'));
    expect(fn, 'the item name must route').toContain('_hubGoItem');
    expect(fn, 'and be reachable by keyboard, not mouse-only').toContain('onkeydown');
    expect(fn, 'and explain itself on hover — he asked for a tooltip').toContain('title=');
  });

  test('★ each task-force chronicle row routes to ITS OWN ledger', async () => {
    /* Asserts the DESTINATION, not the icon. The first version of this test pinned the emoji too
       (`_tfChron('🔨', 'Runewords', …)`) and duly went red when v1615 replaced that argument with
       an art key — a passing test failing on a correct change, which is how tests get loosened
       instead of fixed. The tab is what this test is about; the picture has its own spec. */
    expect(UI).toMatch(/_tfChron\('[^']+', 'Runewords'[^)]*'runes'\)/);
    expect(UI).toMatch(/_tfChron\('[^']+', 'Grail Uniques'[^)]*'funi'\)/);
    expect(UI).toMatch(/_tfChron\('[^']+', 'Sets'[^)]*'fsets'\)/);
  });

  test('★ a chip that says "open Forge" opens the Forge — from BOTH quest sources', async () => {
    const chip = UI.slice(UI.indexOf('function _forgeChip'), UI.indexOf('function _forgeChip') + 500);
    expect(chip).toContain('_hubGo(&quot;forge&quot;)');
    // Both call sites must use the shared builder, or one of them drifts back to a dead label.
    // Count RETURNS, not every mention — `function _forgeChip(ck){` matches a naive pattern too,
    // which is how this assertion first failed at 3 on correct code.
    expect((UI.match(/return _forgeChip\(ck\);/g) || []).length,
      'both quest sources must build the chip the same way').toBe(2);
    expect(UI, 'and no raw dead label may survive').not.toContain("'<span class=\"hd-chip\">⚗️ ' + ck + ' · open Forge</span>'");
  });

  test('★★★ LIVE — clicking each of the six controls lands on the RIGHT board tab', async ({ page }) => {
    /* Every other test in this file reads the source. Source-reading proves the plumbing exists; it
       cannot prove water comes out. This one seeds the panels with real-shaped data, CLICKS each
       control, and reads back where the shell actually went.
       It is also the test that forced `body[data-shell-tab]` to exist: the console header carries
       six buttons for fifteen board tabs, so routing to `bosses` or `runes` lit nothing and left
       the destination unobservable — four of six routes confirmable and two taken on faith. */
    await page.addInitScript(() => {
      localStorage.setItem('d2r_forgeSummary', JSON.stringify({
        craftTypes: ['Blood', 'Caster'], ts: Date.now(),
        chron: { made: 60, total: 99 }, grail: { found: 243, total: 403 },
        sets: { found: 108, total: 135 },
      }));
      localStorage.setItem('d2r_grailFarm', JSON.stringify([{ name: 'Frostburn', boss: 'mephisto' }]));
    });
    await page.route(ORIGIN + '/ui', (r: any) =>
      r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
    await page.route((u: URL) => u.pathname.startsWith('/api/'),
      (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
    await page.route((u: URL) => u.pathname === '/api/tz', (r: any) => r.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ ok: true, current: 'Durance of Hate', next: 'Catacombs', ts: Date.now() }) }));
    await page.route((u: URL) => u.pathname === '/api/evrank', (r: any) => r.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ ok: true, ranked: [{ name: 'Frostburn', ev: 3.2, boss: 'Mephisto',
        source: 'Mephisto (Hell)', etaH: 4.1, diff: 'Hell', kind: 'unique' }] }) }));
    await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);

    const hit = async (sel: string, match?: string) => {
      await page.evaluate(() => { document.body.dataset.shellTab = ''; });
      const found = await page.evaluate(([s, m]: any) => {
        const els = Array.from(document.querySelectorAll(s));
        const el: any = m ? els.find((e: any) => (e.textContent || '').includes(m)) : els[0];
        if (!el) return false;
        el.click();
        return true;
      }, [sel, match || '']);
      if (!found) return 'NOT-RENDERED';
      await page.waitForTimeout(350);
      return await page.evaluate(() => document.body.dataset.shellTab || null);
    };

    expect(await hit('.hh-name'), 'the grail hero must open the uniques chronicle').toBe('funi');
    expect(await hit('#hd-tz .tzz', 'Durance of Hate'),
      'Durance of Hate must open the BOSS page — "routed to mephisto.. for the run itself"').toBe('bosses');
    expect(await hit('.tf-chron', 'Runewords')).toBe('runes');
    expect(await hit('.tf-chron', 'Grail Uniques')).toBe('funi');
    expect(await hit('.tf-chron', 'Sets')).toBe('fsets');
    expect(await hit('#hd-forge-chips .hd-chip', 'open Forge')).toBe('forge');

    // and the hero's tooltip answers the question the click is about to answer.
    // v1616 — this assertion moved from `title=` to `data-itip`, and NOT to make it pass: the
    // native title= was the grey OS box in Konyo's screenshot and was deliberately deleted in
    // favour of the console-skinned floating card. The v1613 INTENT is unchanged and still
    // enforced here — the hero must name the item and say where to hunt it BEFORE the click —
    // it is only read off the surface that now carries it. Accessible-name parity is asserted
    // too, so the payload cannot quietly vanish from assistive tech.
    const tip = await page.evaluate(() =>
      (document.querySelector('.hh-name') as any)?.getAttribute('data-itip') || '');
    expect(tip, 'the hero must carry a hover payload, not a native title=').not.toBe('');
    expect(tip).toContain('Frostburn');
    expect(tip, 'the tooltip should say where to hunt it, not just repeat the name').toMatch(/Mephisto/i);
    expect(await page.evaluate(() =>
      (document.querySelector('.hh-name') as any)?.getAttribute('title')),
      'the native OS tooltip must be gone — it is the one surface that did not look like the console').toBeFalsy();
    const aria = await page.evaluate(() =>
      (document.querySelector('.hh-name') as any)?.getAttribute('aria-label') || '');
    expect(aria).toContain('Frostburn');
    expect(aria, 'the accessible name must keep the where-to-hunt fact the title used to carry').toMatch(/Mephisto/i);
  });
});
