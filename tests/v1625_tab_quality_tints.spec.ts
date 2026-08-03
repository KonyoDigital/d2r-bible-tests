import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1625 ITEM 1 — THE MAIN TABS WEAR THE GAME'S OWN QUALITY COLOURS.
//
// Konyo: "for the main tabs i want it colored accordingly to each relevant.. example. Runewords can
// match the ingame runeword color for the tab. and for F-SETS it can be matched and synced to green
// sets like it is ingame. F-UNIQUES it can be matched and synced to the uniques color" and "FORGE
// tab can match the runewords color ingame. that way we have each tab almost matching their ingame".
//
// Three rules govern this and each one is a version this project already paid for:
//
//   v1615 — ONE CONCEPT, ONE PICTURE. Colour only where the GAME has the concept. Sessions, Tools
//           and TV·D are not item qualities; they stay chrome gold. Tinting them would say "quality"
//           about a thing that has none.
//   v1622 — THE BOARD IS THE REFERENCE, NEVER A HEX IN A TEST. --rar-unique shipped as #f0c060,
//           which is this console's own --gold, and three specs walked past it because they only
//           checked that a CLASS existed. So nothing here restates a colour: bible.html is opened
//           in a second page and its live --q-*/--rune are the expected values.
//   v1614 — THE LIT TAB MUST STAY LEGIBLE. Gold text on a gold gradient measured ~1.2:1 on the one
//           marker that answers "which tab am I on". Tinting six tabs is six new chances to do that
//           again, so every tab is measured in BOTH states against the pixels actually under it.
//
// Everything below reads COMPUTED COLOUR. A class name is not a colour.

const ORIGIN = 'http://tvd.console.test';
const REPO = path.resolve(__dirname, '..');
const UI = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');
const BOARD = 'file://' + path.join(REPO, 'bible.html');

const TABS = ['session', 'forge', 'funi', 'fsets', 'tools', 'tvd'];
// the three tabs the GAME has a quality for -> the board token that owns that quality
// v1628 CORRECTS THIS MAP, NOT THE APP. It said forge: '--rune' because until v1627 the console's
// --rar-runeword WAS #ff7d3c. v1627 pulled the palette from Konyo's own _profilehd.json and a
// completed runeword's NAME is FontColorGoldYellow #c7b377 — the same gold as a unique. --rune
// #ff7d3c is the colour of a RUNE ITEM (El, Eld), a different concept that still owns that hex.
// So this expectation was restating a hex the game disagrees with: exactly the v1621 failure
// (a spec pinned to rgb(0,255,0) that went red when the palette became CORRECT). Fixed here.
/* v1631 — the Forge tab maps to --rune, not --q-unique. A TAB labels a room; the Forge's room is
   where runes become words. Runeword NAMES stay gold (the game has no runeword colour, so quality
   decides it) — that rule lives in its own specs and is untouched here. */
const TINTED: Record<string, string> = { funi: '--q-unique', fsets: '--q-set', forge: '--rune' };
const PLAIN = ['session', 'tools', 'tvd'];
// every quality colour the board declares — a plain tab must match NONE of them
const QUALITIES = ['--q-unique', '--q-set', '--q-rare', '--q-magic', '--q-orange', '--rune'];
// v1622's trap: the console's own chrome. A tint that lands here is invisible as a tint.
const CHROME = ['--gold', '--gold-hi', '--gold-antique', '--gold-dim'];

/* ─────────── harness (copied from tests/v1621_rarity_and_craft_gems.spec.ts) ───────────
   page.screenshot() HANGS on control_ui.html, so nothing here captures; every route FULFILLS
   (an abort surfaces as a console error the console's own specs would then red on). */
async function console_(page: any, injectCss?: string) {
  const body = injectCss ? UI.replace('</head>', `<style id="v1625-mutation">${injectCss}</style></head>`) : UI;
  await page.addInitScript(() => {
    localStorage.setItem('d2r_grailFarm', JSON.stringify([{ name: 'Frostburn', source: 'Hell Mephisto',
      dropChance: 0.0002, killsPerHr: 100, art: 'art/hd_gaunlets_h.png', rarity: 'unique' }]));
    localStorage.setItem('d2r_setFarm', JSON.stringify([{ name: "Griswold's Honor (Shield)",
      set: "Griswold's Legacy", left: 2, source: 'Hell TZ Pindleskin', dropChance: 0.0003,
      killsPerHr: 90, art: 'art/hd_crown_shield.png', rarity: 'set' }]));
  });
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body }));
  await page.route((u: URL) => u.pathname.startsWith('/art/'), (r: any) => {
    const p = path.join(REPO, new URL(r.request().url()).pathname.replace(/^\//, ''));
    return fs.existsSync(p)
      ? r.fulfill({ status: 200, contentType: 'image/png', body: fs.readFileSync(p) })
      : r.fulfill({ status: 404, body: '' });
  });
  await page.route((u: URL) => u.pathname === '/api/evrank', async (r: any) => {
    let items: any[] = [];
    try { items = JSON.parse(r.request().postData() || '{}').items || []; } catch (e) {}
    await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true,
      ranked: items.map((it: any, i: number) => ({ name: it.name, source: it.source, expectedHours: 1.3 + i })) }) });
  });
  await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/evrank',
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2400);
}

/* Resolve a list of custom properties to rgb() THROUGH THE BROWSER, so `#00ff00`, `#0f0` and
   `rgb(0,255,0)` all normalise to one string and the two documents are comparable. A sentinel is
   written first: if a token is missing, style.color simply keeps its previous value, and without
   the sentinel that silently reads as "some colour" instead of "not declared". */
async function tokens(page: any, names: string[]) {
  return page.evaluate((ns: string[]) => {
    const cs = getComputedStyle(document.documentElement);
    const probe = document.createElement('span');
    probe.style.cssText = 'position:absolute;left:-9999px';
    document.body.appendChild(probe);
    const out: Record<string, string | null> = {};
    for (const n of ns) {
      probe.style.color = 'rgb(1, 2, 3)';
      probe.style.color = cs.getPropertyValue(n).trim();
      const got = getComputedStyle(probe).color;
      out[n] = got === 'rgb(1, 2, 3)' ? null : got;   // null === token not declared here
    }
    probe.remove();
    return out;
  }, names);
}

/* Measure every tab in one state. The background is the pixels ACTUALLY under the label:
   the element's own background-color composited down the ancestor chain, and if the tab paints a
   gradient, every stop of it — the reported ratio is the WORST of them (v1614's lit-pill case). */
async function measureTabs(page: any, lit: boolean) {
  return page.evaluate((on: boolean) => {
    type C = { r: number; g: number; b: number; a: number };
    /* Chromium serialises the tinted pill's `color-mix(in srgb, …)` stops as `color(srgb 1 0.57
       0.35)` — 0–1 floats — while the plain gold pill serialises as `rgb(255, 223, 154)`. A parser
       that only knew rgb() found ZERO stops on the tinted lit tab and silently measured its label
       against the page background four layers down: 1.10:1 for a pill that actually reads ~7:1.
       That was a false red on real code, which is the same failure mode as a false green. */
    const rgb = (s: string): C | null => {
      const m = (s.match(/[\d.]+/g) || []).map(Number);
      if (m.length < 3) return null;
      const k = /^color\(/.test(s.trim()) ? 255 : 1;   // color(srgb …) is 0–1, rgb() is 0–255
      return { r: m[0] * k, g: m[1] * k, b: m[2] * k, a: m.length > 3 ? m[3] : 1 };
    };
    const over = (fg: C, bg: C): C => ({
      r: fg.a * fg.r + (1 - fg.a) * bg.r,
      g: fg.a * fg.g + (1 - fg.a) * bg.g,
      b: fg.a * fg.b + (1 - fg.a) * bg.b, a: 1 });
    const lum = (c: C) => {
      const f = [c.r, c.g, c.b].map((x) => { const v = x / 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
      return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2];
    };
    const ratio = (a: C, b: C) => { const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x); return (hi + 0.05) / (lo + 0.05); };
    const CANVAS: C = { r: 255, g: 255, b: 255, a: 1 };   // the ultimate backdrop under everything

    const chainBg = (el: Element | null): C => {
      const stack: C[] = [];
      for (let n: Element | null = el; n; n = n.parentElement)
        stack.push(rgb(getComputedStyle(n).backgroundColor) || { r: 0, g: 0, b: 0, a: 0 });
      let acc = CANVAS;
      for (let i = stack.length - 1; i >= 0; i--) acc = over(stack[i], acc);   // back to front
      return acc;
    };

    const out: any[] = [];
    for (const b of Array.from(document.querySelectorAll('#head-tabs .ht')) as HTMLElement[]) {
      const had = b.classList.contains('shell-on');
      if (on) b.classList.add('shell-on'); else b.classList.remove('shell-on');
      const cs = getComputedStyle(b);
      // getComputedStyle returns a LIVE declaration: every read below must happen while the state
      // under test is still applied, so the string is snapshotted here, not at report time.
      const colorStr = cs.color;
      const fg = rgb(colorStr) as C;
      const base = over(rgb(cs.backgroundColor) || { r: 0, g: 0, b: 0, a: 0 }, chainBg(b.parentElement));
      const stops = (cs.backgroundImage.match(/(?:rgba?|color)\([^)]*\)/g) || []).map((s) => over(rgb(s) as C, base));
      const cands = stops.length ? stops : [base];
      // the element's own opacity chain — v905 dims Tools/TV·D to .55; recorded, not asserted on
      let alpha = 1;
      for (let n: HTMLElement | null = b; n; n = n.parentElement) alpha *= parseFloat(getComputedStyle(n).opacity || '1');
      let worst = Infinity, worstPainted = Infinity, worstBg = '';
      for (const c of cands) {
        const r1 = ratio(over(fg, c), c);
        if (r1 < worst) { worst = r1; worstBg = `rgb(${c.r.toFixed(0)}, ${c.g.toFixed(0)}, ${c.b.toFixed(0)})`; }
        worstPainted = Math.min(worstPainted, ratio(over({ ...fg, a: fg.a * alpha }, c), c));
      }
      if (!had) b.classList.remove('shell-on'); else b.classList.add('shell-on');
      out.push({ tab: b.getAttribute('data-tab'), color: colorStr, bg: worstBg,
                 ratio: worst, painted: worstPainted, opacity: alpha, stops: stops.length });
    }
    return out;
  }, lit);
}

test.describe('v1625 — the six main tabs wear the game\'s quality palette', () => {
  test('★★ the strip is exactly the six known tabs', async ({ page }) => {
    await console_(page);
    const got = await page.evaluate(() =>
      Array.from(document.querySelectorAll('#head-tabs .ht')).map((b: any) => b.getAttribute('data-tab')));
    expect(got, 'the tint map below addresses these six by name — a seventh would go untinted and untested').toEqual(TABS);
  });

  test('★★★ F·Uniques, F·Sets and Forge ARE the board\'s colours — read live, not restated', async ({ page }) => {
    /* v1623: the previous sync probe was pinned to the wrong reference and agreed with itself.
       bible.html is the single source of the palette; this reads it in its own document and
       compares the console's PAINTED tab colour to it, so a drift on either side reds. */
    await page.goto(BOARD); await page.waitForTimeout(2000);
    const board = await tokens(page, QUALITIES);
    for (const n of QUALITIES) expect(board[n], `bible.html must declare ${n}`).toBeTruthy();

    await console_(page);
    const tabs = await measureTabs(page, false);
    const byTab: Record<string, any> = Object.fromEntries(tabs.map((t: any) => [t.tab, t]));
    for (const [tab, tok] of Object.entries(TINTED)) {
      expect(byTab[tab].color,
        `the ${tab} tab must BE the game's ${tok} (${board[tok]}) — it is ${byTab[tab].color}`)
        .toBe(board[tok]);
    }
    /* v1631 — THREE TABS, THREE COLOURS. Konyo: "these two colors cant be the same... RUNEWORD is
       separate from the F-UNIQUES".
       v1628's comment here argued the opposite and it was reasoning about the wrong object. It is
       true that a completed runeword's NAME is the same gold as a unique — the game has no
       FontColorRuneword, and the runeword strings carry no colour code, so quality decides it at
       render time. But a TAB is not an item name; it labels a ROOM. The Forge's room is where
       runes become words, so it wears the RUNE colour, which IS a real game colour for a real
       thing. Runeword NAMES are untouched and still gold everywhere in the app — that rule has its
       own tests and this one does not contradict it.
       Not FontColorDarkGold either: #78622f measures 3.42:1 against this background, under the
       4.5:1 floor v1614 set. */
    expect(byTab.fsets.color, 'set green must read differently from the gold').not.toBe(byTab.funi.color);
    expect(byTab.forge.color, 'the Forge tab must not be the F·Uniques gold — he needs them apart')
      .not.toBe(byTab.funi.color);
    expect(byTab.forge.color, 'nor the set green').not.toBe(byTab.fsets.color);
    expect(new Set([byTab.forge.color, byTab.funi.color, byTab.fsets.color]).size,
      'three quality tabs, three distinct colours').toBe(3);
    const chrome = await tokens(page, CHROME);
    for (const c of Object.values(chrome)) {
      if (!c) continue;
      expect(byTab.funi.color, `the gold tint must not collapse into the console chrome ${c}`).not.toBe(c);
    }
  });

  test('★★★ the console\'s --rar-runeword and --rar-orange equal the board\'s runeword gold and --q-orange', async ({ page }) => {
    /* Same invariant tests/v1621 holds for --rar-unique/set/rare/magic, extended to the two tokens
       ITEM 1 and ITEM 2 introduce. Runeword gold and craft orange are D2's colours, not ours.
       v1628 CORRECTS THE TOKEN NAME: this asked for --rar-rune, which NEITHER file has ever
       declared — the console's token is --rar-runeword and the board's is --q-runeword. The old
       assertion could only pass by accident, so it is renamed to the tokens that exist and the
       comparison is kept exact. --q-runeword is declared as var(--q-unique), so the board side is
       read as the unique gold it aliases, and that aliasing is asserted rather than assumed. */
    await page.goto(BOARD); await page.waitForTimeout(2000);
    const board = await tokens(page, ['--q-unique', '--q-runeword', '--q-orange', '--rune']);
    // tokens() RESOLVES through a probe element, so an alias arrives already computed — which is
    // what we want here: the question is what the pixel is, not how it was spelled. That it is
    // spelled as an alias and not a second literal is tests/v1628_no_literal_quality_hex.spec.ts's job.
    expect(board['--q-runeword'],
      'the board must declare a runeword token, and it must resolve to the unique gold')
      .toBe(board['--q-unique']);
    expect(board['--rune'], 'a RUNE ITEM keeps its own colour and must not have been folded into the gold')
      .not.toBe(board['--q-unique']);
    await console_(page);
    const cons = await tokens(page, ['--rar-runeword', '--rar-orange']);
    expect(cons['--rar-runeword'], 'the console must declare --rar-runeword').toBeTruthy();
    expect(cons['--rar-orange'], 'the console must declare --rar-orange').toBeTruthy();
    expect({ runeword: cons['--rar-runeword'], orange: cons['--rar-orange'] })
      .toEqual({ runeword: board['--q-unique'], orange: board['--q-orange'] });
  });

  test('★★★ PLAIN STAYS PLAIN — Sessions, Tools and TV·D carry no quality colour (v1615)', async ({ page }) => {
    await page.goto(BOARD); await page.waitForTimeout(2000);
    const board = await tokens(page, QUALITIES);
    await console_(page);
    const tabs = await measureTabs(page, false);
    for (const t of tabs.filter((x: any) => PLAIN.includes(x.tab))) {
      for (const q of QUALITIES) {
        expect(t.color,
          `${t.tab} has no in-game quality, so it must not wear ${q} — a colour that means "unique" ` +
          'on one tab cannot mean "log" on the next').not.toBe(board[q]);
      }
    }
  });

  test('★★★ ANTI-v1622 — no tint may land on the console\'s own chrome gold', async ({ page }) => {
    /* --rar-unique once shipped as #f0c060 = --gold. Konyo saw it in one glance: "it doesnt look so
       it looks like the rest of the console". A tint that equals the chrome is not a tint. */
    await console_(page);
    const chrome = await tokens(page, CHROME);
    const tabs = await measureTabs(page, false);
    const byTab: Record<string, any> = Object.fromEntries(tabs.map((t: any) => [t.tab, t]));
    for (const tab of Object.keys(TINTED)) {
      for (const c of CHROME) {
        expect(byTab[tab].color,
          `${tab} is painted ${byTab[tab].color}, which IS ${c} — the tint would be invisible ` +
          'against every gold border on the page').not.toBe(chrome[c]);
      }
    }
  });

  test('★★★ every tab stays legible UNLIT and LIT — measured, with the number in the message', async ({ page }) => {
    /* v1614 fixed exactly one of these states on exactly one tab. Six tinted tabs × two states is
       twelve chances to reprint that bug, so all twelve are measured against the pixels under them.
       Ratio uses the resolved rgb() pair (WCAG's own model); the opacity-attenuated figure is
       recorded alongside because v905 dims Tools/TV·D to .55 — that dimming predates this change
       and is reported, not asserted on. */
    await console_(page);
    const unlit = await measureTabs(page, false);
    const lit = await measureTabs(page, true);
    expect(unlit.length).toBe(6);
    for (const [state, rows] of [['unlit', unlit], ['lit', lit]] as [string, any[]][]) {
      for (const t of rows) {
        expect(t.ratio,
          `${state} "${t.tab}": ${t.color} on ${t.bg} measures ${t.ratio.toFixed(2)}:1` +
          (t.stops ? ` (worst of ${t.stops} gradient stops)` : '') +
          ` [painted with opacity ${t.opacity.toFixed(2)} → ${t.painted.toFixed(2)}:1] — the tab strip ` +
          'is how he knows where he is; it must be the most readable thing in the chrome, not the least')
          .toBeGreaterThanOrEqual(4.5);
      }
    }
    // v1614's own case, kept explicit: the LIT tab must not be gold-on-gold again
    const litSession = lit.find((t: any) => t.tab === 'session');
    expect(litSession.ratio, `the lit current-tab marker sits at ${litSession.ratio.toFixed(2)}:1`).toBeGreaterThan(4.5);
  });

  test('★★ the two guards above actually BITE — mutation-checked in-page', async ({ page }) => {
    /* The mutation is served, not written: tv/control_ui.html belongs to another owner this round.
       A <style> injected into the served copy paints the exact two defects the guards exist for —
       if either guard were vacuous, this test would be the one that never fails. */
    await console_(page, `
      #head-tabs .ht[data-tab="funi"] { color: var(--gold) !important; }
      #head-tabs .ht.shell-on { background: linear-gradient(180deg, #1c1408, #120c04) !important; }`);
    const chrome = await tokens(page, CHROME);
    const unlit = await measureTabs(page, false);
    const lit = await measureTabs(page, true);
    const funi = unlit.find((t: any) => t.tab === 'funi');
    // MUTATION A — the anti-v1622 guard
    expect(funi.color, 'the injected defect must actually paint the chrome gold').toBe(chrome['--gold']);
    // MUTATION B — the contrast guard: near-black label on a near-black lit pill
    const worstLit = Math.min(...lit.map((t: any) => t.ratio));
    expect(worstLit, `a darkened lit gradient must drop the measured ratio below 4.5 — it read ${worstLit.toFixed(2)}:1`)
      .toBeLessThan(4.5);
  });
});
