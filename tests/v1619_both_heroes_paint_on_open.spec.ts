import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1619 — BOTH HEROES PAINT WHEN SESSIONS OPENS, WITHOUT A STORAGE EVENT.
//
// Konyo: "now i dont see the griswald shield.. under the grail in sessions.. we had them both
// sections there.. for sets and uniques where did it go?"
//
// It had not gone anywhere; it had never loaded. hubNextSet has existed since v1570, but the line
// that paints the hub on open (v1378) only ever called hubNextGrail. The sets hero's only callers
// were _hubResync — which fires on a storage EVENT — and the chronicle-apply path. So THE NEXT
// PIECE appeared exactly when the board happened to rewrite d2r_setFarm while the console was
// already open, and never on simply opening Sessions.
//
// That is why it read as intermittent rather than broken, and why rebooting his PC made it vanish:
// a cold start has no storage event to ride. The uniques hero was on the open line from v1378, so
// it always appeared — which is what made the missing twin look like a disappearance.
//
// THE TEST MUST NOT TOUCH THE RENDERER. An earlier probe called _hubNextSet() directly, saw the
// card, and concluded the panel was fine — the bug lives in who CALLS it, so any test that invokes
// it by hand is blind to exactly this class.

const ORIGIN = 'http://tvd.console.test';
const REPO = path.resolve(__dirname, '..');
const UI = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');

const GRAIL = [{ name: 'Frostburn', source: 'Hell Mephisto', dropChance: 0.0002, killsPerHr: 100,
                 art: 'art/hd_gaunlets_h.png', rarity: 'unique' }];
const SETS = [{ name: "Griswold's Honor (Shield)", set: "Griswold's Legacy", left: 2,
                source: 'Hell TZ Pindleskin', dropChance: 0.0003, killsPerHr: 90,
                art: 'art/hd_crown_shield.png', rarity: 'set' }];

async function coldOpen(page: any, seed: { grail?: any[]; sets?: any[] } = {}) {
  await page.addInitScript(([g, s]: any) => {
    localStorage.setItem('d2r_grailFarm', JSON.stringify(g));
    localStorage.setItem('d2r_setFarm', JSON.stringify(s));
  }, [seed.grail ?? GRAIL, seed.sets ?? SETS]);
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname.startsWith('/art/'), (r: any) => {
    const p = path.join(REPO, new URL(r.request().url()).pathname.replace(/^\//, ''));
    return fs.existsSync(p)
      ? r.fulfill({ status: 200, contentType: 'image/png', body: fs.readFileSync(p) })
      : r.fulfill({ status: 404, body: '' });
  });
  await page.route((u: URL) => u.pathname === '/api/evrank', async (r: any) => {
    let items: any[] = [];
    try { items = JSON.parse(r.request().postData() || '{}').items || []; } catch (e) {}
    await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      ok: true,
      ranked: items.map((it: any, i: number) => ({ name: it.name, source: it.source, expectedHours: 1.4 + i })) }) });
  });
  await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/evrank',
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2400);   // no manual render call — the console's own open path only
}

const hero = (page: any, id: string) => page.evaluate((i: string) => {
  const el: any = document.getElementById(i);
  if (!el) return { missing: true };
  return {
    missing: false,
    idle: el.className.includes('idle'),
    len: (el.innerHTML || '').length,
    visible: getComputedStyle(el).display !== 'none' && el.getBoundingClientRect().height > 10,
    name: (el.querySelector('.hh-name')?.textContent || '').trim(),
  };
}, id);

test.describe('v1619 — the hub loads both chronicles', () => {
  test('★★★ THE NEXT PIECE paints on a cold open, with no storage event', async ({ page }) => {
    await coldOpen(page);
    const sets = await hero(page, 'hub-hero-sets');
    expect(sets.missing).toBe(false);
    expect(sets.idle, 'idle means hubNextSet never ran — it was only wired to a storage event').toBe(false);
    expect(sets.visible, 'the panel he says vanished must be on screen').toBe(true);
    expect(sets.name).toContain("Griswold's Honor");
  });

  test('★★ its twin still paints — the fix must not trade one hero for the other', async ({ page }) => {
    await coldOpen(page);
    const uni = await hero(page, 'hub-hero');
    expect(uni.idle).toBe(false);
    expect(uni.visible).toBe(true);
    expect(uni.name).toContain('Frostburn');
  });

  test('★★ the open path calls BOTH, and they sit together', async () => {
    // structural, so the two cannot drift apart again the way they did for 49 versions
    const open = UI.slice(UI.indexOf("_shellLight('session');"), UI.indexOf("_shellLight('session');") + 1400);
    expect(open, 'the uniques hero has been on this line since v1378').toContain('hubNextGrail()');
    expect(open, 'and its twin was missing from it since v1570').toContain('hubNextSet()');
  });

  test('★ an EMPTY sets bridge still degrades honestly — idle, not a broken card', async ({ page }) => {
    // the panel is allowed to be absent when there is genuinely nothing to hunt; that is different
    // from being absent because nobody called it
    await coldOpen(page, { sets: [] });
    const sets = await hero(page, 'hub-hero-sets');
    expect(sets.missing).toBe(false);
    expect(sets.idle, 'no set data = idle, and that is correct').toBe(true);
    expect(sets.len, 'and it renders nothing rather than an empty frame').toBe(0);
  });
});
