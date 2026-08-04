import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1615 — ONE CONCEPT, ONE PICTURE.
//
// v1614 gave the tab strip and the MINI focus row real game art. That was the ask, and on its own
// it made the console LESS consistent than the emoji it replaced: the sets chronicle showed a
// Golden Bird medallion in the tab strip, a Golden Bird in the MINI row, and a 🧩 jigsaw piece in
// the Daily Task Force — three surfaces naming one thing, two of them agreeing by accident. The
// grail was worse: a 🏆 trophy on the Task Force HERO row sat directly above a Grail Uniques row
// wearing the medallion, on the same panel, two lines apart.
//
// The cause was structural, not cosmetic: every surface chose its own glyph inline, so agreement
// was never enforced anywhere. There is now one map, CONSOLE_ART, and every dynamic surface reads
// its picture from it.
//
// These tests enforce the invariant rather than the icons. They do not care WHICH picture the sets
// chronicle uses — they care that the tab, the focus button, the task-force row and the engine
// chip all use the SAME one, so the next person to add a surface cannot quietly introduce a
// seventh jigsaw piece.

const ORIGIN = 'http://tvd.console.test';
const REPO = path.resolve(__dirname, '..');
const UI = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');

const FOCUSES = ['stash', 'runes', 'gems', 'materials', 'chronicle-uniques', 'chronicle-sets'];

// enough state that every surface under test actually renders
const FORGE_SUMMARY = {
  craftTypes: ['Blood', 'Caster'],
  chron: { made: 60, total: 99 },
  grail: { found: 243, total: 403 },
  sets: { found: 108, total: 135, done: 12 },
  now: [], onestep: [], ts: 1,
};

async function console_(page: any, seed: any = FORGE_SUMMARY) {
  await page.addInitScript((fsum: any) => {
    localStorage.setItem('d2r_forgeSummary', JSON.stringify(fsum));
  }, seed);
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname.startsWith('/art/'), (r: any) => {
    const p = path.join(REPO, new URL(r.request().url()).pathname.replace(/^\//, ''));
    return fs.existsSync(p)
      ? r.fulfill({ status: 200, contentType: 'image/png', body: fs.readFileSync(p) })
      : r.fulfill({ status: 404, contentType: 'text/plain', body: 'no such art' });
  });
  await page.route((u: URL) => u.pathname === '/api/mini', (r: any) => r.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ ok: true, running: false, focuses: FOCUSES }) }));
  await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/mini',
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2400);
}

/** every icon on the page, keyed by the surface it lives on */
const survey = (page: any) => page.evaluate(() => {
  const src = (el: any) => {
    const i = el ? el.querySelector('img') : null;
    return i ? new URL(i.src).pathname : null;
  };
  const byText = (sel: string, needle: string) => {
    const el = Array.from(document.querySelectorAll(sel))
      .find((e) => (e.textContent || '').toLowerCase().includes(needle.toLowerCase()));
    return el ? src(el) : null;
  };
  return {
    tab: {
      forge: src(document.querySelector('#head-tabs .ht[data-tab="forge"]')),
      uniques: src(document.querySelector('#head-tabs .ht[data-tab="funi"]')),
      sets: src(document.querySelector('#head-tabs .ht[data-tab="fsets"]')),
    },
    focus: {
      stash: src(document.querySelector('#mini-foc .mf[data-f="stash"]')),
      runes: src(document.querySelector('#mini-foc .mf[data-f="runes"]')),
      uniques: src(document.querySelector('#mini-foc .mf[data-f="chronicle-uniques"]')),
      sets: src(document.querySelector('#mini-foc .mf[data-f="chronicle-sets"]')),
    },
    taskforce: {
      runes: byText('.tf-row.tf-chron', 'Runewords'),
      uniques: byText('.tf-row.tf-chron', 'Grail Uniques'),
      sets: byText('.tf-row.tf-chron', 'Sets'),
      hero: src(document.querySelector('.tf-row.tf-hero')),
    },
    panel: {
      forge: src(document.querySelector('#hd-forge .hd-h')),
      stash: src(document.querySelector('#hd-vault .hd-h')),
    },
    chip: {
      forge: byText('#hd-forge-chips .hd-chip', 'open Forge'),
    },
  };
});

test.describe('v1615 — one concept, one picture', () => {
  test('★★★ the SETS chronicle wears the same picture on every surface', async ({ page }) => {
    await console_(page);
    const s = await survey(page);
    const seen = [s.tab.sets, s.focus.sets, s.taskforce.sets];
    expect(seen.every(Boolean), `a surface is missing its sets icon: ${JSON.stringify(seen)}`).toBe(true);
    expect(new Set(seen).size,
      'the tab strip, the MINI focus row and the Daily Task Force must agree on what "sets" ' +
      `looks like — got ${JSON.stringify(seen)}`).toBe(1);
  });

  test('★★★ the GRAIL UNIQUES chronicle agrees across all four of its surfaces', async ({ page }) => {
    await console_(page);
    const s = await survey(page);
    // the hero row leads with the grail when nothing is ready to forge, so it is the same concept
    const seen = [s.tab.uniques, s.focus.uniques, s.taskforce.uniques, s.taskforce.hero];
    expect(seen.every(Boolean), `missing: ${JSON.stringify(seen)}`).toBe(true);
    expect(new Set(seen).size,
      'the Task Force HERO said "Chase the Grail" with a 🏆 while the row two lines below it ' +
      `showed the medallion — got ${JSON.stringify(seen)}`).toBe(1);
  });

  test('★★★ the FORGE agrees across tab and panel header — and a CRAFT chip shows its GEM', async ({ page }) => {
    await console_(page);
    const s = await survey(page);

    // The Forge CONCEPT still has exactly one picture wherever the Forge itself is named.
    const seen = [s.tab.forge, s.panel.forge];
    expect(seen.every(Boolean), `missing: ${JSON.stringify(seen)}`).toBe(true);
    expect(new Set(seen).size, `got ${JSON.stringify(seen)}`).toBe(1);

    // The chip is deliberately NOT in that set any more. v1621 gave each craft its real gem
    // (Konyo: "they should be gems extracted from the game… they are gems relevant and colored")
    // and v1633 made that survive a stale bridge, so a Caster chip shows a Perfect Amethyst, not
    // the Forge medallion. That does not break "one concept, one picture" — it applies it: the
    // chip's concept is the CRAFT, and a craft's picture is its gem. What must never happen is a
    // chip falling back to the generic medallion, which is exactly what the stale bridge caused.
    expect(s.chip.forge, 'a craft chip must carry a picture').toBeTruthy();
    expect(s.chip.forge, 'a craft chip must show its GEM, not the generic Forge medallion')
      .not.toBe(s.tab.forge);
    expect(s.chip.forge, 'and that picture must be one of the four craft gems')
      .toMatch(/hd_perfect_(amethyst|ruby|emerald|sapphire)\.png$/);
  });

  test('★★ RUNES and STASH agree across their surfaces too', async ({ page }) => {
    await console_(page);
    const s = await survey(page);
    expect(new Set([s.focus.runes, s.taskforce.runes]).size,
      'the MINI runes focus and the Runewords chronicle row').toBe(1);
    expect(new Set([s.focus.stash, s.panel.stash]).size,
      'the MINI stash focus and the VAULT ACCUMULATOR header — the vault IS the stash').toBe(1);
  });

  test('★★ CONSOLE_ART is the only place a picture is chosen', async () => {
    /* The static tab strip keeps its src in the markup (threading a map through six literal
       buttons buys nothing), so the two vocabularies must be checked against each other rather
       than trusted to stay aligned. Every /art/ path the console references must be a value in
       CONSOLE_ART — a src that is in the markup but NOT in the map is exactly how a second
       picture for one concept gets in. */
    const block = UI.slice(UI.indexOf('var CONSOLE_ART = {'), UI.indexOf('function artImg'));
    const declared = new Set([...block.matchAll(/'(\/art\/[^']+)'/g)].map((m) => m[1]));
    expect(declared.size, 'the vocabulary should not be empty').toBeGreaterThanOrEqual(8);

    // every icon the console renders, from either source
    const referenced = new Set([
      ...[...UI.matchAll(/class="(?:ht-i|hd-h-i|mf-i|tf-i)"\s+src="(\/art\/[^"]+)"/g)].map((m) => m[1]),
      ...[...UI.matchAll(/src="(\/art\/ui_[^"]+)"/g)].map((m) => m[1]),
    ]);
    const orphans = [...referenced].filter((r) => !declared.has(r));
    expect(orphans,
      'these icons are referenced without going through CONSOLE_ART, so nothing keeps them in ' +
      'step with the surfaces that name the same thing').toEqual([]);
  });

  test('★★ every declared icon EXISTS and every one is actually used', async ({ page }) => {
    const block = UI.slice(UI.indexOf('var CONSOLE_ART = {'), UI.indexOf('function artImg'));
    const declared = [...block.matchAll(/'(\/art\/[^']+)'/g)].map((m) => m[1]);
    for (const d of declared) {
      expect(fs.existsSync(path.join(REPO, d.replace(/^\//, ''))), `${d} is declared but not on disk`).toBe(true);
    }
    // and none of them is a leftover: a declared-but-unrendered entry is dead vocabulary
    await console_(page);
    const painted = await page.evaluate(() =>
      Array.from(document.querySelectorAll('img'))
        .filter((i: any) => i.naturalWidth > 0)
        .map((i: any) => new URL(i.src).pathname));
    const keys = ['forge', 'uniques', 'sets', 'runes', 'stash', 'tz', 'chronicle'];
    const unpainted = keys.filter((k) => {
      const m = block.match(new RegExp(k + ":\\s*'(/art/[^']+)'"));
      return m && !painted.includes(m[1]);
    });
    expect(unpainted, 'declared in the vocabulary but never rendered on the Sessions homepage').toEqual([]);
  });

  test('★ surfaces the game has NO concept for keep their emoji, honestly', async ({ page }) => {
    /* The line this version draws: art where the game has the thing, emoji where it does not.
       D2R has no picture of a read-chain, a productivity meter or an engine-health pulse, and
       dressing those in a borrowed medallion would be decoration pretending to be provenance. */
    await console_(page);
    const plain = await page.evaluate(() => {
      const want = ['PRODUCTIVITY', 'READ CHAIN', 'ENGINE HEALTH', 'LIVE INTAKE', 'LAST SESSION'];
      const out: any = {};
      document.querySelectorAll('.hd-h').forEach((h: any) => {
        const t = (h.textContent || '').toUpperCase();
        const hit = want.find((w) => t.includes(w));
        if (hit) out[hit] = !!h.querySelector('img');
      });
      return out;
    });
    for (const [name, hasArt] of Object.entries(plain)) {
      expect(hasArt, `${name} is a console concept, not a game one — it should not borrow a sprite`).toBe(false);
    }
    expect(Object.keys(plain).length, 'the panels under test must actually be present').toBeGreaterThanOrEqual(3);
  });

  test('★ a missing art file degrades to the WORD, never to a torn placeholder', async ({ page }) => {
    // every surface shares one builder precisely so this contract is uniform
    await page.addInitScript((fsum: any) =>
      localStorage.setItem('d2r_forgeSummary', JSON.stringify(fsum)), FORGE_SUMMARY);
    await page.route(ORIGIN + '/ui', (r: any) =>
      r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
    await page.route((u: URL) => u.pathname.startsWith('/art/'),
      (r: any) => r.fulfill({ status: 404, contentType: 'text/plain', body: '' }));
    await page.route((u: URL) => u.pathname === '/api/mini', (r: any) => r.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ ok: true, running: false, focuses: FOCUSES }) }));
    await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/mini',
      (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
    await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2200);
    const state = await page.evaluate(() => ({
      // scoped to THIS version's icon classes. The console's older art (the stage runes, the hero)
      // hides itself with `style.display='none'` instead of removing the node, which is equally
      // fine and would otherwise fail this assertion for a contract it never signed.
      brokenImgs: Array.from(document.querySelectorAll('.ht-i, .hd-h-i, .mf-i, .tf-i, .hd-chip-art'))
        .filter((i: any) => i.complete && i.naturalWidth === 0).length,
      tabsStillReadable: Array.from(document.querySelectorAll('#head-tabs .ht'))
        .every((b: any) => (b.textContent || '').trim().length > 2),
      chronRowsStillReadable: Array.from(document.querySelectorAll('.tf-row.tf-chron'))
        .every((r: any) => (r.textContent || '').trim().length > 4),
    }));
    expect(state.brokenImgs, 'a broken icon must remove itself, not sit there torn').toBe(0);
    expect(state.tabsStillReadable, 'the WORD is the tab; the picture is the ornament').toBe(true);
    expect(state.chronRowsStillReadable).toBe(true);
  });
});
