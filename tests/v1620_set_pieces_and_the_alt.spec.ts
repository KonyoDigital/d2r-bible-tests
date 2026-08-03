import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1620 — SET PIECES GET THEIR IN-GAME BLOCK, AND THE ALTERNATIVE IS AN ITEM TOO.
//
// Konyo: "also the girswald sheild in the sessions. doesnt show the item description ingame.. it
// needs that extra detail integrated too into it".
//
// v1617 published a stat block onto all three bridges through one _bridgeTip(), which reads
// ITEM_TIP — 301 entries, every one a UNIQUE and not one set piece. So all nine entries on his set
// bridge shipped tip:null and the card had nothing to show. The data was never missing, only
// shaped differently: ITEM_CODEX keys the SET ("Griswold's Legacy (any)") and carries
// setMembers[] = {name, slot, reqLvl, affixes[]}.
//
// The second half is the same class one line up in the same panel: "quicker below Hell: Umbral
// Disk" names a second real unique, two pixels under a title that shows art and opens a card, and
// offered neither.

const ORIGIN = 'http://tvd.console.test';
const REPO = path.resolve(__dirname, '..');
const UI = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');
const BOARD = 'file://' + path.join(REPO, 'bible.html');

test.describe('v1620 — the set piece and the runner-up', () => {
  test('★★★ a set piece resolves its REAL in-game block from setMembers', async ({ page }) => {
    await page.goto(BOARD); await page.waitForTimeout(2600);
    const t = await page.evaluate(() =>
      (window as any)._bridgeSetTip("Griswold's Honor (Shield)", "Griswold's Legacy"));
    expect(t, '_bridgeSetTip must exist and resolve').toBeTruthy();
    expect(t.b, 'the slot is the base line — "Set · Vortex Shield"').toBe('Vortex Shield');
    expect(t.r).toBe(68);
    expect(t.l).toContain('65% Faster Block Rate');
    expect(t.l).toContain('All Resistances +45');
  });

  test('★★★ the match is EXACT or paren-stripped — never fuzzy', async ({ page }) => {
    /* Fuzzy matching here would hand him another piece's affixes under this piece's name, which is
       worse than the blank card he reported: a blank card says "I don't know", a wrong one lies. */
    await page.goto(BOARD); await page.waitForTimeout(2600);
    const r = await page.evaluate(() => {
      const w: any = window;
      return {
        suffixed: !!w._bridgeSetTip("Griswold's Honor (Shield)", "Griswold's Legacy"),
        bare: !!w._bridgeSetTip("Griswold's Honor", "Griswold's Legacy"),
        wrongPiece: w._bridgeSetTip("Griswold's Redemption", "Griswold's Legacy"),
        notAPiece: w._bridgeSetTip('Totally Invented Piece', "Griswold's Legacy"),
        wrongSet: w._bridgeSetTip("Griswold's Honor", 'No Such Set At All'),
      };
    });
    expect(r.suffixed, 'the bridge names it with the slot in parens').toBe(true);
    expect(r.bare, 'the codex names it without').toBe(true);
    expect(r.notAPiece, 'an invented name must resolve to nothing, not to a neighbour').toBeNull();
    expect(r.wrongSet, 'and a set that does not exist resolves to nothing').toBeNull();
    // a REAL sibling may legitimately resolve — but it must be ITS OWN block, never this one's
    if (r.wrongPiece) {
      expect(r.wrongPiece.b, 'a sibling must not inherit the shield\'s slot').not.toBe('Vortex Shield');
    }
  });

  test('★★★ the set bridge actually ships the blocks — it was 0 of 9', async ({ page }) => {
    await page.goto(BOARD); await page.waitForTimeout(3000);
    const r = await page.evaluate(() => {
      const w: any = window;
      try { w._writeSetFarm && w._writeSetFarm(); } catch (e) {}
      let farm: any = null;
      try { farm = JSON.parse(localStorage.getItem('d2r_setFarm') || 'null'); } catch (e) {}
      return { total: (farm || []).length, withTip: (farm || []).filter((f: any) => f.tip).length };
    });
    expect(r.total, 'his set bridge must have entries at all').toBeGreaterThan(0);
    // not 100%: a set genuinely absent from the codex degrades to a card with no stat block, which
    // is the honest outcome — but "most" is the difference between working and not
    expect(r.withTip / r.total, 'was 0/9 before this version').toBeGreaterThan(0.6);
  });

  test('★★ the ALTERNATIVE item is a real anchor with its own card', async ({ page }) => {
    await page.addInitScript(() => {
      // two uniques where the runner-up is materially quicker, so the alt line renders
      localStorage.setItem('d2r_grailFarm', JSON.stringify([
        { name: 'Frostburn', source: 'Hell Mephisto', dropChance: 0.0002, killsPerHr: 100,
          art: 'art/hd_gaunlets_h.png', rarity: 'unique' },
        { name: 'Umbral Disk', source: 'Normal Andariel', dropChance: 0.002, killsPerHr: 120,
          art: 'art/hd_crown_shield.png', rarity: 'unique',
          tip: { t: 'Unique', b: 'Heater', r: 12, q: 20, l: ['+30% Faster Block Rate'] } },
      ]));
      localStorage.setItem('d2r_setFarm', JSON.stringify([]));
    });
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
      /* Frostburn leads on DIFFICULTY (Hell), Umbral Disk is far quicker (Normal) => the alt
         line appears. The real ranker returns ranked ASCENDING by hours and the hero reads
         _ranked[0] as "the quickest anywhere", so the stub must sort or the alt can never fire —
         an unsorted stub silently tests a state the server never produces. */
      const ranked = items.map((it: any) => ({ name: it.name, source: it.source,
        expectedHours: it.name === 'Frostburn' ? 3.0 : 0.9 }))
        .sort((a: any, b: any) => a.expectedHours - b.expectedHours);
      await r.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ ok: true, ranked }) });
    });
    await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/evrank',
      (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
    await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2400);

    const alt = await page.evaluate(() => {
      const a: any = document.querySelector('.hh-altgo');
      if (!a) return { missing: true, srcText: (document.querySelector('.hh-src') as any)?.textContent || '' };
      return { missing: false, text: (a.textContent || '').trim(), role: a.getAttribute('role'),
               tab: a.getAttribute('tabindex'), onclick: a.getAttribute('onclick') || '',
               itip: a.getAttribute('data-itip') || '', art: !!a.querySelector('img') };
    });
    expect(alt.missing, `the alt line should name the quicker item; got: ${alt.srcText}`).toBe(false);
    expect(alt.text).toContain('Umbral Disk');
    expect(alt.role, 'it names an item, so it opens that item').toBe('button');
    expect(alt.tab).toBe('0');
    expect(alt.onclick).toContain('_hubGoItem');
    expect(alt.art, 'and wears its own face like every other item name').toBe(true);
    const d = JSON.parse(alt.itip);
    expect(d.name).toBe('Umbral Disk');
    expect(d.tip, 'carrying its OWN stat block, not the lead item\'s').toBeTruthy();
    expect(d.tip.b).toBe('Heater');
  });
});
