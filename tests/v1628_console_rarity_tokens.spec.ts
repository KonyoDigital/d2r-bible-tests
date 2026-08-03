import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1628 — THE CONSOLE'S RARITY VOCABULARY IS COMPLETE, AND NOTHING FALLS THROUGH TO GOLD.
//
// Konyo: "fix the console color wise any where for the relevant keywords related to the color it
// sohuld be related too tooltips images too.. full audit it."
//
// v1621 gave the hero title and the hover card a rarity class each; v1622 corrected the gold;
// v1627 pulled the whole palette out of Konyo's own install
// (data/global/ui/layouts/_profilehd.json) so both documents finally agree. What none of those
// versions noticed is that the vocabulary has SIX qualities and the console only ever taught it
// FOUR. _itemTip.build() whitelisted set|rare|magic|unique and appended no class for anything
// else, and `#itip .itip-n` / `.hh-name` both default to var(--rar-unique) — so a CRAFTED item and
// a RUNEWORD each rendered in unique gold. Not a missing colour: a WRONG one, silently, with no
// broken markup to notice. The exact shape of v1622, one rung down.
//
// Measured before this version, on the tree at 6a7ef2b:
//   tv/control_ui.html:4816   rcls whitelist = set|rare|magic|unique          (crafted → '', runeword → '')
//   tv/control_ui.html:1001-1005  #itip .itip-n{--rar-unique} + .r-set/.r-rare/.r-magic  (no crafted, no runeword)
//   tv/control_ui.html:3225-3230  .hh-name{--rar-unique} + .r-set/.r-unique/.r-rare/.r-magic  (same two missing)
//   tv/control_ui.html:2963       .ch-card-item .ch-nm { color:#f5edd8 }      — one flat cream for every quality
//   tv/control_ui.html:9959,9966  the 📦 `ch-art-ph` placeholder box, twice   — an arbitrary picture (RULE 3)
//
// THE LAW THESE TESTS OBEY: read the token, never restate the hex. v1621 pinned rgb(0,255,0) and
// went RED the moment the palette became CORRECT. v1622 shipped a wrong gold that three tests
// passed straight over, because they only checked that a CLASS was present. Every expectation
// below resolves --rar-* out of the live document through a throwaway element and compares
// rendered rgb to rendered rgb. No hex is typed into a POSITIVE expectation anywhere in this file.
// Three literal colours appear, all of them as `.not.toBe` — the values the sweep must NOT
// produce: the chronicle's flat cream #f5edd8, the chip's default cream rgb(217,201,160), and the
// four craft-gem hexes, which are declared expectations of an UNCHANGED mapping (v1621's), not of
// anything this version paints.
//
// COMPLEMENTS v1615 (one concept, one picture) rather than repeating it: v1615 proves a
// console-only panel borrows no SPRITE. The last test here proves it borrows no COLOUR either —
// the other half of the same boundary, which this sweep is the first version able to cross.

const ORIGIN = 'http://tvd.console.test';
const REPO = path.resolve(__dirname, '..');
const UI = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');

// the same four craft gems v1621 shipped — carried here only so the DO-NOT-TOUCH guard has a
// declared expectation to compare the live --gemc against
const CRAFTS = [
  { craft: 'Caster', gem: 'Perfect Amethyst', color: '#b48ce0' },
  { craft: 'Blood', gem: 'Perfect Ruby', color: '#e0556a' },
  { craft: 'Safety', gem: 'Perfect Emerald', color: '#5fd07a' },
  { craft: 'Hit Power', gem: 'Perfect Sapphire', color: '#5b8ff0' },
];

// 'Durance of Hate' is in the console's own TZ_BOSS map (control_ui.html:12211) → 'mephisto', so
// the rotation card under test is a boss card with a real route rather than the generic tracker.
const TZ = { current: 'Durance of Hate', next: 'Travincal', ts: Date.now() };

/** v1621's harness, mirrored. Route stubs FULFILL — never abort (an aborted /api/ leaves the
 *  panel in its error branch and the surfaces under test never paint). */
async function console_(page: any) {
  await page.addInitScript((crafts: any) => {
    localStorage.setItem('d2r_grailFarm', JSON.stringify([{ name: 'Frostburn', source: 'Hell Mephisto',
      dropChance: 0.0002, killsPerHr: 100, art: 'art/hd_gaunlets_h.png', rarity: 'unique' }]));
    localStorage.setItem('d2r_setFarm', JSON.stringify([{ name: "Griswold's Honor (Shield)",
      set: "Griswold's Legacy", left: 2, source: 'Hell TZ Pindleskin', dropChance: 0.0003,
      killsPerHr: 90, art: 'art/hd_crown_shield.png', rarity: 'set' }]));
    localStorage.setItem('d2r_forgeSummary', JSON.stringify({ ts: 1, craftTypes: crafts }));
  }, CRAFTS);
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname.startsWith('/art/'), (r: any) => {
    const p = path.join(REPO, new URL(r.request().url()).pathname.replace(/^\//, ''));
    return fs.existsSync(p)
      ? r.fulfill({ status: 200, contentType: 'image/png', body: fs.readFileSync(p) })
      : r.fulfill({ status: 404, contentType: 'text/plain', body: 'no such art' });
  });
  await page.route((u: URL) => u.pathname === '/api/tz', (r: any) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(TZ) }));
  await page.route((u: URL) => u.pathname === '/api/evrank', async (r: any) => {
    let items: any[] = [];
    try { items = JSON.parse(r.request().postData() || '{}').items || []; } catch (e) {}
    await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true,
      ranked: items.map((it: any, i: number) => ({ name: it.name, source: it.source, expectedHours: 1.3 + i })) }) });
  });
  await page.route((u: URL) => u.pathname.startsWith('/api/')
      && u.pathname !== '/api/evrank' && u.pathname !== '/api/tz',
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  /* v1589 put the rotation panel in Sessions only (display:none elsewhere). The boss card must be
     LAID OUT for its route and its art to be measurable, so the view is set the way
     v1547's harness does it — by attribute, not by _showSessions(), which reaches for endpoints
     this harness deliberately answers with ok:false. */
  await page.evaluate(() => document.body.setAttribute('data-view', 'sessions'));
  await page.waitForTimeout(2400);
}

/* ── THE ONE MEASUREMENT PRIMITIVE ────────────────────────────────────────────────────────────
   Resolve a custom property to the SAME rgb() string getComputedStyle returns for a painted
   element, by feeding it to a throwaway element and reading it back. This is why no hex is ever
   typed into an expectation: the document is its own reference, so a typo in the palette cannot be
   typed identically into the test that guards it. */
const tokens = (page: any, names: string[]) => page.evaluate((ns: string[]) => {
  const cs = getComputedStyle(document.documentElement);
  const probe = document.createElement('span');
  document.body.appendChild(probe);
  const out: any = {};
  for (const n of ns) {
    const raw = cs.getPropertyValue(n).trim();
    probe.style.color = '';
    probe.style.color = raw;
    out[n] = { raw, rgb: raw ? getComputedStyle(probe).color : '' };
  }
  probe.remove();
  return out;
}, names);

test.describe('v1628 — every quality the console names wears its own token', () => {

  test('★★★ #itip: .r-crafted and .r-runeword EXIST and PAINT — crafted must not be unique gold', async ({ page }) => {
    /* THE DEFECT, EXACTLY. _itemTip.build() (control_ui.html:4816) appended a rarity class only for
       set|rare|magic|unique. Feed it rarity:'crafted' and it emitted a bare `.itip-n`, which
       inherits `color: var(--rar-unique)` from :1001 — so D2's orange crafted quality rendered as
       gold, on the card, with no broken markup anywhere to give it away.

       Driven through the REAL renderer, not by hand-injecting a class: a CSS rule that exists but
       that build() never reaches would be a fix nobody can see. The class is asserted AND the
       computed colour is asserted — v1622's lesson is that either one alone is a hole. */
    await console_(page);
    const tok = await tokens(page, ['--rar-orange', '--rar-runeword', '--rar-unique', '--rar-set']);
    for (const k of Object.keys(tok))
      expect(tok[k].raw, `${k} must be a real colour — an empty token would make every ` +
        'comparison below compare "" to "" and prove nothing').toMatch(/^#[0-9a-fA-F]{3,8}$/);

    const got = await page.evaluate(() => {
      const probe = document.createElement('span');
      probe.style.position = 'fixed'; probe.style.left = '-9999px';
      document.body.appendChild(probe);
      const read = (rarity: string) => {
        probe.setAttribute('data-itip', JSON.stringify({ name: 'Probe of ' + rarity, rarity }));
        (window as any)._itemTip.show(probe);
        (window as any)._itemTip.move(300, 300);
        const n: any = document.querySelector('#itip .itip-n');
        return { cls: n ? n.className : null, color: n ? getComputedStyle(n).color : null };
      };
      const out = { crafted: read('crafted'), runeword: read('runeword'),
                    unique: read('unique'), plain: read('') };
      probe.remove();
      (window as any)._itemTip.hide();
      return out;
    });

    expect(got.crafted.cls, 'the card must SAY it is crafted').toContain('r-crafted');
    expect(got.runeword.cls, 'the card must SAY it is a runeword').toContain('r-runeword');
    expect(got.crafted.color, "D2 paints crafted items orange — read from --rar-orange, not typed")
      .toBe(tok['--rar-orange'].rgb);
    expect(got.runeword.color, "a completed runeword's NAME is gold — read from --rar-runeword")
      .toBe(tok['--rar-runeword'].rgb);
    /* THE DIFFERENCE IS THE DEFECT. Before this version both of the next two lines were EQUAL,
       because crafted fell through to the `.itip-n` default. */
    expect(got.crafted.color, 'crafted must not fall through to unique gold — this equality WAS the bug')
      .not.toBe(got.unique.color);
    expect(got.crafted.color, 'nor to the un-classed default, which is the same gold by another route')
      .not.toBe(got.plain.color);
    // and the un-classed default itself must still be the unique tan v1622/v1627 settled on
    expect(got.plain.color, 'the base card colour is D2 unique').toBe(tok['--rar-unique'].rgb);
  });

  test('★★★ .hh-name: the hero title has the same two classes, and they differ from its default', async ({ page }) => {
    /* The title and the card are two surfaces naming ONE item — the whole reason --rar-* exists
       (v1621). Adding the classes to only one of them would recreate the v1621 defect on the two
       qualities v1621 did not cover. Measured on a probe carrying the class, because no seeded
       hero is crafted: the CSS rule is what is missing, and the CSS rule is what is measured. */
    await console_(page);
    const tok = await tokens(page, ['--rar-orange', '--rar-runeword', '--rar-unique']);
    const got = await page.evaluate(() => {
      const host = document.querySelector('#hub-hero') || document.body;
      const mk = (cls: string) => {
        const s = document.createElement('span');
        s.className = 'hh-name' + (cls ? ' ' + cls : '');
        s.textContent = 'probe';
        host.appendChild(s);
        const c = getComputedStyle(s).color;
        s.remove();
        return c;
      };
      return { crafted: mk('r-crafted'), runeword: mk('r-runeword'),
               unique: mk('r-unique'), plain: mk('') };
    });
    expect(got.crafted, '.hh-name.r-crafted must resolve to --rar-orange').toBe(tok['--rar-orange'].rgb);
    expect(got.runeword, '.hh-name.r-runeword must resolve to --rar-runeword').toBe(tok['--rar-runeword'].rgb);
    expect(got.plain, "the title's default is still D2 unique").toBe(tok['--rar-unique'].rgb);
    expect(got.crafted, 'a crafted hero must not read as a unique one').not.toBe(got.unique);
    expect(got.crafted, 'nor as the un-classed default').not.toBe(got.plain);
    // the card and the title must agree on crafted, exactly as v1621 made them agree on set/unique
    expect(got.crafted, 'title vs card, on the quality neither of them knew').toBe(tok['--rar-orange'].rgb);
  });

  test('★★★ a runeword is GOLD — the same gold as a unique, and NOT the console chrome gold', async ({ page }) => {
    /* v1622 in one assertion. --rar-unique once WAS #f0c060, this console's own --gold, and the
       one title meant to announce a unique looked like every border around it. Konyo: "it doesnt
       look so it looks like the rest of the console."

       Two facts, both from Konyo's install (data/global/ui/layouts/_profilehd.json): a runeword's
       NAME is FontColorGoldYellow, which is the unique colour — so those two tokens must be EQUAL;
       and neither is the console's chrome --gold, so that equality is not the OLD confusion coming
       back. Note this token is NOT the board's --rune (#ff7d3c): that is the colour of a RUNE ITEM
       (El, Eld), a different concept that was sharing the word "runeword". */
    await console_(page);
    const tok = await tokens(page, ['--rar-runeword', '--rar-unique', '--gold', '--rar-orange']);
    for (const k of Object.keys(tok))
      expect(tok[k].raw, `${k} must exist for this comparison to mean anything`).toMatch(/^#[0-9a-fA-F]{3,8}$/);
    expect(tok['--rar-runeword'].rgb, "a runeword's name is the same gold D2 gives a unique")
      .toBe(tok['--rar-unique'].rgb);
    expect(tok['--rar-runeword'].rgb, "and it is NOT this console's chrome gold — that swap is what v1622 shipped")
      .not.toBe(tok['--gold'].rgb);
    expect(tok['--rar-unique'].rgb, 'nor is the unique tan the chrome gold')
      .not.toBe(tok['--gold'].rgb);
    expect(tok['--rar-orange'].rgb, 'crafted orange is its own quality, not the runeword gold')
      .not.toBe(tok['--rar-runeword'].rgb);
  });

  test('★★★ the four CRAFT GEMS survive this sweep untouched and equal NO --rar-* token', async ({ page }) => {
    /* THE DO-NOT-TOUCH BOUNDARY, guarded. The four chips are the GEM a craft consumes (amethyst /
       ruby / emerald / sapphire, v1621) — not a quality. A rarity sweep that grep-replaced them
       would repaint four distinct crafts one colour, which is the exact defect v1621 fixed. The
       guard is stronger than v1621's: every gem is compared against EVERY rarity token, so the
       boundary is asserted as a property rather than against one colour that happened to be next
       to it this version. */
    await console_(page);
    const tok = await tokens(page,
      ['--rar-unique', '--rar-set', '--rar-rare', '--rar-magic', '--rar-orange', '--rar-runeword']);
    const got = await page.evaluate(() => {
      const probe = document.createElement('span');
      document.body.appendChild(probe);
      const asRgb = (hex: string) => { probe.style.color = ''; probe.style.color = hex;
        return getComputedStyle(probe).color; };
      const out = Array.from(document.querySelectorAll('#hd-forge-chips .hd-chip')).map((c: any) => {
        const cs = getComputedStyle(c);
        const gemc = cs.getPropertyValue('--gemc').trim().toLowerCase();
        return { text: (c.textContent || '').trim(), gemc, gemcRgb: gemc ? asRgb(gemc) : '', color: cs.color };
      });
      probe.remove();
      return out;
    });
    expect(got.length, 'the four craft chips must be present to be guarded').toBe(4);
    const rarRgb = Object.values(tok).map((t: any) => t.rgb);
    for (const c of CRAFTS) {
      const chip = got.find((g) => g.text.startsWith(c.craft));
      expect(chip, `${c.craft} chip missing`).toBeTruthy();
      expect(chip!.gemc, `${c.craft} must still wear its ${c.gem} — this sweep must not reach gems`)
        .toBe(c.color);
      expect(rarRgb, `${c.craft}'s gem has been swept onto a rarity token`).not.toContain(chip!.gemcRgb);
      expect(chip!.color, `${c.craft}: the gem tint must reach the pixels, not the chip default`)
        .not.toBe('rgb(217, 201, 160)');
    }
    expect(new Set(got.map((g) => g.color)).size, 'four crafts must still read as four things').toBe(4);
  });

  test('★★★ chronicle cards wear rarity, and the 📦 placeholder box is gone', async ({ page }) => {
    /* TWO defects on one card. (1) `.ch-card-item .ch-nm` was `color:#f5edd8` (:2963) — one flat
       cream for a unique, a set piece, a rune and a craft alike, on the panel whose entire job is
       telling him WHICH of those he just found. (2) chArtHtml (:9959, :9966) fell back to
       `<div class=ch-art-ph>📦</div>` — a cardboard box standing in for an item whose art could
       not be resolved. RULE 3: if a picture cannot be resolved honestly, render NOTHING. A box
       that means "some item" is the same failure as v1624's thumbnail rendering items[0].

       The colour is measured on real card markup inserted into the live document, because the
       chronicle's own data arrives from the BOARD through the #tvd-eng iframe (chRefreshData,
       :9880) which a standalone console harness has no honest way to populate — and a test that
       opened an EMPTY chronicle and found no placeholder would be measuring zero against zero,
       which proves nothing. What is under test is the CSS contract and the builder's source; both
       are non-vacuous and both are where the defect physically lives. */
    await console_(page);
    const tok = await tokens(page, ['--rar-unique', '--rar-set', '--rar-orange']);
    const got = await page.evaluate(() => {
      const card = document.createElement('div');
      card.className = 'ch-card-item';
      document.body.appendChild(card);
      const mk = (cls: string) => {
        const n = document.createElement('div');
        n.className = 'ch-nm' + (cls ? ' ' + cls : '');
        n.textContent = 'probe';
        card.appendChild(n);
        const c = getComputedStyle(n).color;
        n.remove();
        return c;
      };
      const out = { unique: mk('r-unique'), set: mk('r-set'), crafted: mk('r-crafted'), plain: mk('') };
      card.remove();
      return out;
    });
    expect(got.unique, 'a grail unique in the chronicle wears the unique token').toBe(tok['--rar-unique'].rgb);
    expect(got.set, 'a set piece wears the set token').toBe(tok['--rar-set'].rgb);
    expect(got.crafted, 'a craft wears the crafted token').toBe(tok['--rar-orange'].rgb);
    const CREAM = 'rgb(245, 237, 216)';   // #f5edd8 — the one flat colour being removed, named only to exclude it
    for (const [k, v] of Object.entries(got))
      if (k !== 'plain')
        expect(v, `${k} must no longer render the flat cream every quality shared`).not.toBe(CREAM);
    expect(new Set([got.unique, got.set, got.crafted]).size,
      'three qualities, three colours — one cream for all of them was the defect').toBe(3);

    /* (2) the placeholder, at its source. Before this version the token appeared 3× in
       tv/control_ui.html: the CSS rule at :2961 and the two builders at :9959/:9966.

       The first draft of this assertion was `expect(UI).not.toContain('ch-art-ph')` and it went
       red against a CORRECT tree, because the fix left two COMMENTS naming the thing it deleted
       ("v1628 removed .ch-art-ph — it styled the 📦 stand-in that chArtHtml no longer emits").
       A comment describing a defect is textually identical to the defect. The assertion is
       therefore aimed at the two things that can actually paint a box — emitted markup and a live
       CSS rule — and not at the word, so the prose that documents the removal cannot fail it. */
    expect(UI.match(/class=['"]?ch-art-ph/g), 'no builder may still EMIT the 📦 placeholder box — ' +
      'an unresolvable picture renders NOTHING (RULE 3)').toBe(null);
    expect(UI.match(/\.ch-art-ph[^{;\n]*\{/g), 'and no CSS rule may still style one').toBe(null);
    expect(await page.locator('.ch-art-ph').count(), 'and no placeholder may survive in the DOM').toBe(0);
    expect(await page.getByText('📦', { exact: true }).count(), 'nor the bare glyph').toBe(0);
  });

  test('★★ every picture on these panels DECODES — markup existing is not evidence', async ({ page }) => {
    /* Every <img> the console builds carries onerror="this.remove()", so a wrong path fails
       SILENTLY as a tidy label and a test asserting "the img is there" would pass on a page with
       no pictures at all. naturalWidth is the only honest question. Scoped to laid-out images so a
       lazily-loaded icon inside a hidden panel is not counted as a broken one. */
    await console_(page);
    const shot = await page.evaluate(() => {
      const imgs = Array.from(document.querySelectorAll('img')) as any[];
      const live = imgs.filter((i) => i.getBoundingClientRect().width > 0);
      return {
        total: imgs.length,
        live: live.length,
        broken: live.filter((i) => i.complete && i.naturalWidth === 0)
          .map((i) => new URL(i.src).pathname),
      };
    });
    expect(shot.live, 'the panels under test must actually be showing pictures, or this proves nothing')
      .toBeGreaterThanOrEqual(3);
    expect(shot.broken, 'these are rendered but do not decode').toEqual([]);
  });

  test('★★★ a named ITEM and a named BOSS each route, by keyboard as well as mouse', async ({ page }) => {
    /* v1613's contract, held on the two surfaces this sweep touches. The route is SPIED rather
       than followed: _hubGoItem/_hubGoBoss reach into the board iframe, which this harness does not
       serve, so driving the real navigation would test the harness. What must be true is that the
       element names a routable thing AND hands that thing to the right router — plus role=button,
       tabindex=0 and onkeydown, or the name is reachable by mouse only. */
    await console_(page);
    const got = await page.evaluate(() => {
      const calls: any[] = [];
      (window as any)._hubGoItem = (n: string) => calls.push(['item', n]);
      (window as any)._hubGoSetPiece = (n: string) => calls.push(['setpiece', n]);
      (window as any)._hubGoBoss = (id: string) => calls.push(['boss', id]);
      const probe = (el: any) => el && ({
        role: el.getAttribute('role'), tab: el.getAttribute('tabindex'),
        key: !!el.getAttribute('onkeydown'), text: (el.textContent || '').trim().slice(0, 40),
      });
      const item: any = document.querySelector('#hub-hero [onclick*="_hubGoItem"]');
      const boss: any = document.querySelector('.tzz[onclick*="_hubGoBoss"]');
      const out: any = { item: probe(item), boss: probe(boss),
                         hasSetRouter: typeof (window as any)._hubGoSetPiece === 'function' };
      if (item) item.click();
      if (boss) boss.click();
      out.calls = calls;
      return out;
    });
    expect(got.item, 'the hero item name must be a routable control').toBeTruthy();
    expect(got.boss, 'the rotation card for a boss zone must be a routable control').toBeTruthy();
    for (const [what, el] of [['item', got.item], ['boss', got.boss]] as any[]) {
      expect(el.role, `${what}: role=button`).toBe('button');
      expect(el.tab, `${what}: tabindex=0`).toBe('0');
      expect(el.key, `${what}: onkeydown — a name reachable by mouse only is half a control`).toBe(true);
    }
    expect(got.calls.find((c: any) => c[0] === 'item'), 'clicking the item must call _hubGoItem').toBeTruthy();
    expect(got.calls.find((c: any) => c[0] === 'item')[1], 'and hand it the item it names').toContain('Frostburn');
    expect(got.calls.find((c: any) => c[0] === 'boss'), 'clicking the boss zone must call _hubGoBoss').toBeTruthy();
    // Durance of Hate → 'mephisto', straight out of the console's own TZ_BOSS map
    expect(got.calls.find((c: any) => c[0] === 'boss')[1], 'and hand it the boss that zone holds').toBe('mephisto');
    expect(got.hasSetRouter, 'set pieces have their own router — F·Sets, not the uniques card').toBe(true);
  });

  test('★★ CONSOLE-ONLY concepts stay plain — this sweep must not bleed colour into them', async ({ page }) => {
    /* The other half of v1615's boundary. v1615 proves a console concept borrows no SPRITE; the
       risk this version introduces is that it borrows a COLOUR. D2 has no picture AND no quality
       colour for a productivity meter, a read chain or an engine-health pulse, so a --rar-* on one
       of those headers would be decoration pretending to be provenance. Asserted as "equals none
       of the six rarity tokens", so it cannot be satisfied by moving to a seventh wrong colour. */
    await console_(page);
    const tok = await tokens(page,
      ['--rar-unique', '--rar-set', '--rar-rare', '--rar-magic', '--rar-orange', '--rar-runeword']);
    const rarRgb = Object.values(tok).map((t: any) => t.rgb);
    const seen = await page.evaluate(() => {
      const want = ['PRODUCTIVITY', 'READ CHAIN', 'ENGINE HEALTH', 'LIVE INTAKE', 'LAST SESSION'];
      const out: any[] = [];
      document.querySelectorAll('.hd-h').forEach((h: any) => {
        const t = (h.textContent || '').toUpperCase();
        const hit = want.find((w) => t.includes(w));
        if (hit) out.push({ name: hit, color: getComputedStyle(h).color, art: !!h.querySelector('img') });
      });
      return out;
    });
    expect(seen.length, 'the panels under test must be present, or this measures nothing')
      .toBeGreaterThanOrEqual(3);
    for (const s of seen) {
      expect(rarRgb, `${s.name} is a console concept — it must not wear a game quality colour`)
        .not.toContain(s.color);
      expect(s.art, `${s.name} must not borrow a sprite either (v1615's half of the boundary)`).toBe(false);
    }
  });
});
