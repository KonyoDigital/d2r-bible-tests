import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1617 — THE CARD READS LIKE THE GAME, AND EVERY ITEM NAME OPENS ONE.
//
// Konyo sent two screenshots of the BOARD's own hover card (Baranar's Star, Ormus' Robes) with
// "for the frostburn this is the example it sohuld render and replicate and for griswald too", then
// "and griswald shield right under it ... also needs to be image upgraded with a description tool
// tip and routabel and clicable", then "even here the item names keywords need upgrading to full hd
// art0r image and title and cursor image floating ... for ttancred battlegear and baranas star so
// it matches".
//
// One complaint three times: the console names real items and shows him nothing about them, while
// the board three inches away shows the full in-game block. The data was never missing — ITEM_TIP
// has the transcribed stat lines for every grail item — it just never crossed the iframe.
//
// v1616 left the sets hero deliberately inert, reasoning that "the set farm ranks an AGGREGATE, so
// there is no single item card to land on". That was wrong on its own terms: the hero prints
// top.name, which is the specific missing PIECE. The destination it said the data could not name
// was in the heading all along.

const ORIGIN = 'http://tvd.console.test';
const REPO = path.resolve(__dirname, '..');
const UI = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');
const BOARD = 'file://' + path.join(REPO, 'bible.html');

const GRAIL = [{
  name: 'Frostburn', art: 'art/hd_gaunlets_h.png', rarity: 'unique',
  tip: { t: 'Unique', b: 'Gauntlets', r: 29, q: 32,
         l: ['+[10-20]% Enhanced Defense', '+30 Defense', 'Increase Maximum Mana 40%'] },
}];
const SETS = [{
  name: "Griswold's Honor (Shield)", set: "Griswold's Legacy", left: 2,
  art: 'art/hd_crown_shield.png', rarity: 'set',
  tip: { t: 'Set', b: 'Crown Shield', r: 69, q: 74,
         l: ['+[150-200]% Enhanced Defense', '+40 to Life'] },
}];

async function console_(page: any, opts: any = {}) {
  await page.addInitScript(([g, s, ai]: any) => {
    localStorage.setItem('d2r_grailFarm', JSON.stringify(g));
    localStorage.setItem('d2r_setFarm', JSON.stringify(s));
    if (ai) {
      localStorage.setItem('d2r_createNowAi', 'finish Tancred’s Battlegear (1 piece left)');
      localStorage.setItem('d2r_createNowAiArt', JSON.stringify(ai));
    }
  }, [opts.grail || GRAIL, opts.sets || SETS, opts.ai || null]);
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname.startsWith('/art/'), (r: any) => {
    const p = path.join(REPO, new URL(r.request().url()).pathname.replace(/^\//, ''));
    return fs.existsSync(p)
      ? r.fulfill({ status: 200, contentType: 'image/png', body: fs.readFileSync(p) })
      : r.fulfill({ status: 404, body: '' });
  });
  // rank exactly what each hero POSTs, so the two heroes cannot be handed each other's items
  await page.route((u: URL) => u.pathname === '/api/evrank', async (r: any) => {
    let items: any[] = [];
    try { items = JSON.parse(r.request().postData() || '{}').items || []; } catch (e) {}
    await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      ok: true,
      ranked: items.map((it: any, i: number) => ({
        name: it.name, source: 'Hell Mephisto', expectedHours: 1.3 + i, ev: 0.5 })) }) });
  });
  await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/evrank',
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2200);
  // both heroes are refresh-driven; invoke directly so the assertion is about the CARD, not timing
  await page.evaluate(async () => {
    const w: any = window;
    try { await w._hubNextGrail?.(); } catch (e) {}
    try { await w._hubNextSet?.(); } catch (e) {}
  });
  await page.waitForTimeout(300);
}

/** hover an anchor and read back the rendered card */
const card = (page: any, sel: string) => page.evaluate(async (s: string) => {
  const n: any = document.querySelector(s);
  if (!n) return { missing: true };
  const w: any = window;
  w._itemTip.show(n);
  const t: any = document.getElementById('itip');
  return {
    missing: false,
    on: !!t && t.classList.contains('on'),
    art: !!t?.querySelector('.itip-art'),
    name: (t?.querySelector('.itip-n')?.textContent || '').trim(),
    nameCls: t?.querySelector('.itip-n')?.className || '',
    type: (t?.querySelector('.att-type')?.textContent || '').trim(),
    meta: (t?.querySelector('.att-meta')?.textContent || '').trim(),
    lines: Array.from(t?.querySelectorAll('.att-aff') || []).map((e: any) => e.textContent.trim()),
    pills: Array.from(t?.querySelectorAll('.att-var') || []).map((e: any) => e.textContent.trim()),
    html: t?.innerHTML || '',
  };
}, sel);

test.describe('v1617 — the in-game card, everywhere an item is named', () => {
  test('★★★ the NEXT GRAIL card reads like the game: art, type · base, req/qlvl, stat lines', async ({ page }) => {
    await console_(page);
    const c = await card(page, '#hub-hero .hh-name');
    expect(c.missing, 'the grail hero must render').toBe(false);
    expect(c.name).toBe('Frostburn');
    expect(c.art, 'the item shows its own face').toBe(true);
    expect(c.type, 'the line the board prints as "Unique · Devil Star"').toBe('Unique · Gauntlets');
    expect(c.meta).toBe('Req level: 29 · Quality level: 32');
    expect(c.lines).toContain('+30 Defense');
    expect(c.lines).toContain('Increase Maximum Mana 40%');
    expect(c.pills, 'a [range] renders as the board\'s green pill, not as literal brackets').toContain('10-20');
    expect(c.html, 'and no raw bracket survives').not.toContain('[10-20]');
  });

  test('★★★ the NEXT PIECE card matches it — and is a real control', async ({ page }) => {
    await console_(page);
    const c = await card(page, '#hub-hero-sets .hh-name');
    expect(c.missing, 'v1616 left this inert; it must render a card now').toBe(false);
    expect(c.name).toBe("Griswold's Honor (Shield)");
    expect(c.art).toBe(true);
    expect(c.type).toBe('Set · Crown Shield');
    expect(c.meta).toBe('Req level: 69 · Quality level: 74');
    expect(c.pills).toContain('150-200');
    expect(c.nameCls, 'a set piece is GREEN, the in-game set colour').toContain('r-set');

    const ctl = await page.evaluate(() => {
      const n: any = document.querySelector('#hub-hero-sets .hh-name');
      return { role: n?.getAttribute('role'), tab: n?.getAttribute('tabindex'),
               onclick: n?.getAttribute('onclick') || '', keys: !!n?.getAttribute('onkeydown'),
               aria: n?.getAttribute('aria-label') || '' };
    });
    expect(ctl.role, 'Konyo: "routabel and clicable"').toBe('button');
    expect(ctl.tab, 'and reachable by keyboard').toBe('0');
    expect(ctl.keys).toBe(true);
    expect(ctl.onclick).toContain('_hubGoSetPiece');
    expect(ctl.aria).toContain("Griswold's Honor");
  });

  test('★★★ _hubGoSetPiece EXISTS and opens the SETS chronicle, not the calculator', async ({ page }) => {
    // the guard-with-no-symbol class: an onclick naming a function that was never defined
    await console_(page);
    const r = await page.evaluate(async () => {
      const w: any = window;
      if (typeof w._hubGoSetPiece !== 'function') return { missing: true };
      document.body.dataset.shellTab = '';
      w._hubGoSetPiece("Griswold's Honor (Shield)");
      await new Promise((res) => setTimeout(res, 300));
      return { missing: false, tab: document.body.dataset.shellTab || null };
    });
    expect(r.missing, '_hubGoSetPiece is named by the hero\'s onclick — it must exist').toBe(false);
    expect(r.tab, 'a set piece belongs in F·Sets, beside its set — not on the calculator').toBe('fsets');
  });

  test('★★ the DAILY PICK carries the same in-game block', async ({ page }) => {
    await console_(page, { ai: { name: 'Frostburn', art: 'art/hd_gaunlets_h.png', rarity: 'unique',
      tip: { t: 'Unique', b: 'Gauntlets', r: 29, q: 32, l: ['+30 Defense'] } } });
    const attr = await page.evaluate(() => {
      const n: any = document.querySelector('.tf-ai[data-itip], .tf-hero[data-itip]');
      return n ? n.getAttribute('data-itip') : null;
    });
    expect(attr, 'the daily pick must carry an item card').toBeTruthy();
    const d = JSON.parse(attr as string);
    expect(d.tip, 'including the stat block, not just the name').toBeTruthy();
    expect(d.tip.b).toBe('Gauntlets');
  });

  test('★★★ a hostile stat line cannot inject markup — the bridge is localStorage', async ({ page }) => {
    /* d2r_grailFarm is written by the board, but ANYTHING running on this origin can write it, and
       the console renders what it finds there. The lines are escaped before the [range] pills are
       applied, which is the whole reason the card is built here instead of shipping the board's
       HTML across the bridge. */
    await console_(page, { grail: [{ name: 'Frostburn', art: '', rarity: 'unique',
      tip: { t: '<img src=x onerror=window.__pwn=1>', b: 'Gauntlets', r: 1, q: 1,
             l: ['<script>window.__pwn=1</script>', '+[1-2] <b>bold</b>'] } }] });
    const c = await card(page, '#hub-hero .hh-name');
    const pwned = await page.evaluate(() => !!(window as any).__pwn);
    expect(pwned, 'a bridge value executed').toBe(false);
    expect(c.html).not.toContain('<script>');
    expect(c.html, 'markup in a stat line stays TEXT').not.toContain('<b>bold</b>');
    expect(c.pills, 'while a genuine range still becomes a pill').toContain('1-2');
  });

  test('★★ the board publishes d2rOpenSetPiece, and it is HONEST about landing', async ({ page }) => {
    await page.goto(BOARD); await page.waitForTimeout(2600);
    const r = await page.evaluate(() => {
      const w: any = window;
      if (typeof w.d2rOpenSetPiece !== 'function') return { missing: true };
      let bogus: any = 'threw';
      try { bogus = w.d2rOpenSetPiece('Nonexistent Piece Of Nothing'); } catch (e) {}
      return { missing: false, bogus, tipFn: typeof w._bridgeTip };
    });
    expect(r.missing, 'the console calls this by name across the iframe').toBe(false);
    expect(r.bogus, 'an item that is not there must report false, never a silent success').toBe(false);
    expect(r.tipFn, '_bridgeTip feeds the stat block onto all three bridges').toBe('function');
  });

  test('★★ the OPS QUEUE names items with art and a hover anchor', async () => {
    /* Konyo: "even here the item names keywords need upgrading". These rows live on the BOARD, so
       they use the board's own `data-art-logo` card rather than the console's — same card he
       screenshotted. The 430px note matters: the hover binding refuses wide anchors, so the mark
       must wrap the NAME, never the row. */
    const board = fs.readFileSync(path.join(REPO, 'bible.html'), 'utf8');
    const fn = board.slice(board.indexOf('function _opsMark'), board.indexOf('function _opsMark') + 900);
    expect(fn, 'the mark shows the item art').toContain('sc-ops-art');
    expect(fn, 'and anchors the board hover card').toContain('data-art-logo');
    expect(fn, 'falling back to the glyph when there is genuinely no art').toContain('glyph');
    // all three ops rows go through it, or one drifts back to a bare emoji
    expect((board.match(/_opsMark\(/g) || []).length).toBeGreaterThanOrEqual(4);
    expect(board, 'and the art has a size, or it renders full-bleed').toContain('.sc-ops-art{');
  });
});

// ── v1618 — SYNCED, NOT MERELY SIMILAR ────────────────────────────────────────────────────────
// Konyo, with two screenshots of the board's own card: "why not copy this exact template for each?
// i want a synced tooltip for these items ... no need to create a new one just sync the current
// one". v1617 reproduced the board's STRUCTURE but styled it in the console's idiom — a big
// uppercase serif name where the board uses a small mono one. Same facts, visibly different
// object.
//
// This test compares the two cards' COMPUTED style, so "synced" is a measurement rather than an
// opinion, and drifting one of them apart fails here instead of in a screenshot months later.
test.describe('v1618 — the console card is the board card', () => {
  test('★★★ the title, type and meta match bible.html #arttip computed-for-computed', async ({ page }) => {
    // what the BOARD renders
    await page.goto(BOARD); await page.waitForTimeout(2400);
    const board = await page.evaluate(() => {
      const mk = (cls: string, parent: any) => { const d = document.createElement('div'); d.className = cls; parent.appendChild(d); return d; };
      /* v1622 — the probe must carry the SAME rarity the console card under test is showing.
         The board tints its title through a class on the container (#arttip.tip-r-unique
         .att-name{color:#c7b377}), so a bare #arttip measures the UNTINTED base gold and compares
         the console's unique against a card the board never renders for a unique. That is how this
         assertion went red on a correct v1622 fix: it was pinned to the wrong reference. */
      const t = document.createElement('div'); t.id = 'arttip'; t.className = 'tip-rich tip-r-unique';
      document.body.appendChild(t);
      // the real card nests the body in .att-desc (bible.html:22916) — att-type/meta/aff INHERIT
      // its 10.5px from there, so measuring them as direct children of #arttip reads the page
      // default instead and compares the console against a card the board never renders
      const n = mk('att-name', t), desc = mk('att-desc', t);
      const ty = mk('att-type', desc), me = mk('att-meta', desc), af = mk('att-aff', desc);
      const g = (e: any) => { const c = getComputedStyle(e);
        return { ff: c.fontFamily, fs: c.fontSize, fw: c.fontWeight, color: c.color }; };
      const out = { name: g(n), type: g(ty), meta: g(me), aff: g(af),
                    box: (() => { const c = getComputedStyle(t);
                      return { radius: c.borderRadius, border: c.borderColor, maxW: c.maxWidth, align: c.textAlign }; })() };
      t.remove(); return out;
    });

    // what the CONSOLE renders
    await console_(page);
    await page.evaluate(() => {
      const n: any = document.querySelector('#hub-hero .hh-name');
      (window as any)._itemTip.show(n); (window as any)._itemTip.move(300, 300);
    });
    const cons = await page.evaluate(() => {
      const t: any = document.getElementById('itip');
      const g = (sel: string) => { const e = t.querySelector(sel); if (!e) return null;
        const c = getComputedStyle(e); return { ff: c.fontFamily, fs: c.fontSize, fw: c.fontWeight, color: c.color }; };
      const c = getComputedStyle(t);
      return { name: g('.itip-n'), type: g('.att-type'), meta: g('.att-meta'), aff: g('.att-aff'),
               box: { radius: c.borderRadius, border: c.borderColor, maxW: c.maxWidth, align: c.textAlign } };
    });

    /* EVERYTHING EXCEPT SIZE IS IDENTICAL — family, weight-class, colour, alignment, radius.
       Size is the one deliberate divergence: the board sets 10.5px/9.5px and the console has a
       13px floor (v1504, Konyo's own "nothing important under ~12-13px at fullscreen", enforced by
       TestV1504TypeFloor). Copying the board's px would honour his newer request by breaking his
       older one, so the rule asserted here is NEVER SMALLER THAN THE BOARD — same card, legible. */
    const px = (v: string) => parseFloat(v);

    expect(cons.name!.ff, 'the board titles in mono; v1617 used the console serif').toBe(board.name.ff);
    expect(cons.name!.color, "the board's unique tan #c7b377, same hex on both surfaces").toBe(board.name.color);
    expect(px(cons.name!.fs)).toBeGreaterThanOrEqual(px(board.name.fs));

    expect(cons.type!.ff).toBe(board.type.ff);
    expect(cons.type!.color, '#c9c9c9, the board\'s type-line grey').toBe(board.type.color);
    expect(px(cons.type!.fs)).toBeGreaterThanOrEqual(px(board.type.fs));

    expect(cons.meta!.color, '#8f8f8f').toBe(board.meta.color);
    expect(px(cons.meta!.fs)).toBeGreaterThanOrEqual(px(board.meta.fs));

    expect(cons.aff!.ff).toBe(board.aff.ff);
    expect(cons.aff!.color, '#d8d8d8, the stat-line grey').toBe(board.aff.color);
    expect(px(cons.aff!.fs)).toBeGreaterThanOrEqual(px(board.aff.fs));

    // the hierarchy the board establishes must survive the size lift
    expect(px(cons.name!.fs), 'the name still leads').toBeGreaterThan(px(cons.type!.fs));

    // and the card itself is the board's object
    expect(cons.box.radius).toBe(board.box.radius);
    expect(cons.box.align).toBe(board.box.align);
    expect(px(cons.box.maxW), 'a touch wider than 300px only because the type is larger')
      .toBeLessThanOrEqual(px(board.box.maxW) + 40);

    // nothing in the console card may fall under his floor
    const floor = await page.evaluate(() => {
      const t: any = document.getElementById('itip');
      return Array.from(t.querySelectorAll('*')).map((e: any) => parseFloat(getComputedStyle(e).fontSize))
        .filter((n: number) => n > 0);
    });
    expect(Math.min(...floor), 'v1504: nothing important under 13px').toBeGreaterThanOrEqual(13);
  });

  test('★★ the CSS block cannot silently die again', async ({ page }) => {
    /* Writing this sync, a comment inside the rule contained a literal comment-terminator in the middle of a
       CSS-variable name. It closed the comment early and killed the ENTIRE #itip block — the card
       rendered its text completely unstyled, position:static, full page width, and the only reason
       it was caught is that a screenshot came back black. A stylesheet that dies is silent. */
    await console_(page);
    const pos = await page.evaluate(() => {
      const n: any = document.querySelector('#hub-hero .hh-name');
      (window as any)._itemTip.show(n); (window as any)._itemTip.move(300, 300);
      const c = getComputedStyle(document.getElementById('itip') as any);
      return { position: c.position, maxWidth: c.maxWidth };
    });
    expect(pos.position, 'the rule block is alive').toBe('fixed');
    expect(pos.maxWidth).not.toBe('none');
    const ui = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');
    const block = ui.slice(ui.indexOf('#itip { position: fixed'), ui.indexOf('#itip .itip-go'));
    // A comment legitimately ENDS with the terminator, so its presence proves nothing — the real
    // invariant is BALANCE. The bug produced one opener and two terminators, because a variable
    // name inside the prose closed the comment a paragraph early.
    const OPEN = '/' + '*', TERM = '*' + '/';
    const opens = block.split(OPEN).length - 1, closes = block.split(TERM).length - 1;
    expect(closes, `the #itip block has ${opens} comment opener(s) and ${closes} terminator(s) — ` +
      'an extra terminator means a comment closed early and the rest of the rule is now garbage')
      .toBe(opens);
  });
});
