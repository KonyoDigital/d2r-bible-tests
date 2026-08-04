import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';
import { boardTokens, consoleTokens, assertTokens } from './_palette';

/* ═══════════════════════════════════════════════════════════════════════════════════════════════
   v1634 ITEM 3 — THE SESSIONS COLOUR SWEEP, PINNED.

   Konyo's standing instruction: "same for sessions page. a full on sync to colors.. sets for green.
   uniques for uniques color.. runewords for runewords color.. each their own relevant color and
   synced to the rest of the platform".

   An earlier pass was called complete after reviewing five spec files. It was not complete, and the
   reason it looked complete is the exact hole this file exists to close: every previous audit
   asserted that a rarity CLASS was present, and never once asked what that class COMPUTED TO. That
   is the v1622 shape recorded at the top of tests/_palette.ts — three specs walked straight over
   --rar-unique being set to the console's own chrome gold, because a class was there and a class is
   not a colour.

   SO EVERY VALUE IN THIS FILE IS READ BACK THROUGH getComputedStyle, and every expectation is a
   RELATIONSHIP against a token the app itself declares:
     · EQUAL TO      the token the surface claims to wear,
     · NOT EQUAL TO  the chrome gold it must never be confused with (the negative space, below),
     · NOT EQUAL TO  the quality it would be mistaken for (set green is not unique gold),
     · UNCHANGED     across bible.html and tv/control_ui.html (one platform, one palette).

   NO QUALITY HEX LITERAL APPEARS HERE, in code or in prose, by design — P6's hex guard covers
   tests/, and more importantly v1621 proved that a spec holding a copied hex goes RED ON THE FIX
   when the palette is corrected. The app owns the values. This file owns the rules.

   THE NEGATIVE SPACE IS THE POINT. Before this version, `.ch-pill.grail.on` and
   `.ch-card-item .ch-tier.t-grail` were painted with the console's own chrome gold — the frame
   colour, not the game's unique-item gold. Nothing was red, because nothing had ever asked. Those
   two surfaces name a GRAIL, which is a unique item, so they must wear the unique token; and the
   assertion that actually catches the regression is not "equals unique" (a lucky palette could
   satisfy that) but "is NOT the chrome gold" (which the old code failed outright).
   ═══════════════════════════════════════════════════════════════════════════════════════════════ */

const ORIGIN = 'http://tvd.console.test';
const REPO = path.resolve(__dirname, '..');
const UI = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');
const BOARD = 'file://' + path.join(REPO, 'bible.html');

/* ─────────── harness (shape copied from tests/v1625_tab_quality_tints.spec.ts) ───────────
   page.screenshot() HANGS on control_ui.html, so nothing here captures a pixel; colours are read
   from the CSSOM. Every route FULFILLS rather than aborts — an abort surfaces as a console error
   that the console's own "no console errors" specs would then red on. */
async function console_(page: any) {
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname.startsWith('/art/'), (r: any) => {
    const p = path.join(REPO, new URL(r.request().url()).pathname.replace(/^\//, ''));
    return fs.existsSync(p)
      ? r.fulfill({ status: 200, contentType: 'image/png', body: fs.readFileSync(p) })
      : r.fulfill({ status: 404, body: '' });
  });
  await page.route((u: URL) => u.pathname.startsWith('/api/'),
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1200);
}

/* Paint real markup with the app's real classes into the live document, so the cascade that runs is
   the SAME cascade Konyo sees — not a hand-rolled restatement of a rule. The host is visible and on
   top because one probe below needs a genuine :hover, which a display:none element can never take.
   Returns the computed value of `prop` for every id in the spec map. */
async function paint(page: any, spec: Record<string, { html: string; prop: string }>) {
  return page.evaluate((s: Record<string, { html: string; prop: string }>) => {
    let host = document.getElementById('v1634-probe-host') as HTMLElement | null;
    if (!host) {
      host = document.createElement('div');
      host.id = 'v1634-probe-host';
      host.style.cssText = 'position:fixed;left:0;top:0;z-index:2147483647;background:#000;padding:4px';
      document.body.appendChild(host);
    }
    host.innerHTML = Object.keys(s).map(k => s[k].html).join('');
    const out: Record<string, string | null> = {};
    for (const k of Object.keys(s)) {
      const el = document.getElementById(k);
      out[k] = el ? (getComputedStyle(el) as any)[s[k].prop] : null;
    }
    return out;
  }, spec);
}

async function clearProbes(page: any) {
  await page.evaluate(() => document.getElementById('v1634-probe-host')?.remove());
}

/* A probe that resolved to null means the element never rendered — the selector moved or the markup
   was renamed. Comparing null to null is green and proves nothing (the whole reason
   _palette.assertTokens exists), so probe absence fails LOUDLY and by name, exactly like a missing
   token does. */
function assertPainted(got: Record<string, string | null>, ...ids: string[]): asserts got is Record<string, string> {
  const missing = ids.filter(k => !(k in got) || got[k] == null || got[k] === '');
  if (missing.length) {
    throw new Error('V1634 PROBE DID NOT RENDER: ' + missing.map(k => '"' + k + '"').join(', ') +
      '. The element or its class moved. A probe that renders nothing measures nothing, and an ' +
      'unmeasured surface is how the last three colour audits shipped green over a real defect.');
  }
}

/* The exact markup the console emits, id-tagged so it can be measured. Class chains are copied from
   tv/control_ui.html; the nesting matters, because several rules are descendant selectors
   (`.ch-card-item .ch-tier.t-grail`) and a flat probe would silently miss them. */
const PROBES = {
  /* v1634's repaints. Every one of these NAMES a grail — which is a unique item — and every one of
     them was previously painted with the console's own chrome gold or a hand-picked cousin of it
     (#f4cd6a, #ffdf9a, --gold-hi). The whole change table is pinned here, not just the two headline
     surfaces, because "fixed the one in front of me" is how one colour bug ships three times. */
  grailPill:  { html: '<span id="grailPill" class="ch-pill grail on">GRAIL</span>', prop: 'backgroundColor' },
  grailTier:  { html: '<div class="ch-card-item"><span id="grailTier" class="ch-tier t-grail">GRAIL</span></div>', prop: 'color' },
  grailFind:  { html: '<div class="find-card fc-grail"><span id="grailFind" class="fc-name">a grail find</span></div>', prop: 'color' },
  grailBtn:   { html: '<span id="grailBtn" class="bt bt-grail">grail</span>', prop: 'color' },
  grailHero:  { html: '<div id="grailHero" class="hh-grail">next grail</div>', prop: 'color' },
  grailMind:  { html: '<div class="brain"><div id="grailMind" class="line mind-grail">a grail thought</div></div>', prop: 'color' },
  grailChip:  { html: '<span id="grailChip" class="hd-chip nm nm-grail">GRAIL</span>', prop: 'color' },
  setsChip:   { html: '<span id="setsChip" class="hd-chip nm nm-sets">SETS</span>', prop: 'color' },
  chronUni:   { html: '<div class="chron-c q-uni"><span class="chron-n"><b id="chronUni">a unique</b></span></div>', prop: 'color' },
  chronSet:   { html: '<div class="chron-c q-set"><span class="chron-n"><b id="chronSet">a set piece</b></span></div>', prop: 'color' },
  /* the surfaces the sweep must leave agreeing — one per quality the console renders */
  setName:    { html: '<div class="ch-card-item"><span id="setName" class="ch-nm r-set">a set piece</span></div>', prop: 'color' },
  setRow:     { html: '<div class="tf-row tf-q-sets"><span class="tf-t"><b id="setRow">sets</b></span></div>', prop: 'color' },
  rwRow:      { html: '<div class="tf-row tf-q-runes"><span class="tf-t"><b id="rwRow">runewords</b></span></div>', prop: 'color' },
  rwName:     { html: '<div class="hh-name r-runeword" id="rwName">a completed runeword</div>', prop: 'color' },
  uniName:    { html: '<div class="hh-name r-unique" id="uniName">a unique</div>', prop: 'color' },
  craftName:  { html: '<div class="hh-name r-crafted" id="craftName">a crafted item</div>', prop: 'color' },
};

test.describe('v1634 — sessions colour sweep: every quality surface computes to its own token', () => {

  test('1 · the repainted GRAIL surfaces, and every quality surface, equal the token they claim', async ({ page }) => {
    await console_(page);
    const t = await consoleTokens(page);
    /* gate BEFORE any comparison — a renamed token must throw by name, never compare null===null */
    assertTokens(t, 'unique', 'set', 'runeword', 'orange', 'rune');

    const got = await paint(page, PROBES);
    assertPainted(got, ...Object.keys(PROBES));

    /* v1634's fix, whole. Before this version every GRAIL surface below computed to the console's
       chrome gold or a hand-mixed cousin of it. A grail is a unique item; it wears the unique token. */
    expect(got.grailPill, 'the GRAIL filter pill fills with the unique-item token').toBe(t.unique);
    expect(got.grailTier, 'the GRAIL tier chip writes in the unique-item token').toBe(t.unique);
    expect(got.grailFind, 'a GRAIL find-card name is the unique-item token').toBe(t.unique);
    expect(got.grailBtn,  'the GRAIL button label is the unique-item token').toBe(t.unique);
    expect(got.grailHero, 'the NEXT-GRAIL hero line is the unique-item token').toBe(t.unique);
    expect(got.grailMind, 'a GRAIL brain-line is the unique-item token').toBe(t.unique);
    expect(got.grailChip, 'the GRAIL progress chip is the unique-item token').toBe(t.unique);
    expect(got.setsChip,  'the SETS progress chip is the set token').toBe(t.set);
    expect(got.chronUni,  'a unique in the celebration toast is the unique-item token').toBe(t.unique);
    expect(got.chronSet,  'a set piece in the celebration toast is the set token').toBe(t.set);

    /* the rest of the platform, pinned so the sweep cannot rot back.
       v1636/v1639 — the RUNEWORDS task-force ROW is a ROOM label, not an item name. It wears
       --rar-rune (Forge orange). A completed runeword NAME still wears --rar-runeword (unique
       gold). See test 5's deliberate-doctrine block; this half of the pin was left on the old
       claim and went red the moment the room was painted correctly. */
    expect(got.uniName,   'a unique NAME is the unique token').toBe(t.unique);
    expect(got.setName,   'a set piece NAME is the set token').toBe(t.set);
    expect(got.setRow,    'the SETS task row is the set token').toBe(t.set);
    expect(got.rwRow,     'the RUNEWORDS task row is the Forge-orange ROOM accent, not runeword gold').toBe(t.rune);
    expect(got.rwName,    'a completed runeword NAME is the runeword token').toBe(t.runeword);
    expect(got.craftName, 'a crafted item NAME is the crafted-orange token').toBe(t.orange);

    await clearProbes(page);
  });

  test('2 · the craft-gem chip is driven by --gemc, and by nothing else', async ({ page }) => {
    await console_(page);
    const t = await consoleTokens(page);
    assertTokens(t, 'gold', 'orange');

    /* --gemc is NOT a :root token: _forgeChip() writes it inline, per craft, from _CRAFT_GEM (the
       perfect gem each craft consumes). So the claim that can be made here is the one that matters —
       the chip's colour FOLLOWS --gemc and is not quietly the chrome gold with a gem-shaped name.
       Two different gem values must produce two different chips, and the :hover border, whose rule
       is a bare var(--gemc), must land exactly on the value handed in. The two probe values are
       arbitrary non-palette colours chosen so this test can never accidentally restate a quality. */
    const A = 'rgb(180, 140, 224)', B = 'rgb(95, 208, 122)';
    const mk = (id: string, c: string) =>
      '<span id="' + id + '" class="hd-chip hd-go hd-chip-gem" style="--gemc:' + c + '">gem chip</span>';
    const base = await paint(page, {
      gemA: { html: mk('gemA', A), prop: 'borderTopColor' },
      gemB: { html: mk('gemB', B), prop: 'borderTopColor' },
    });
    assertPainted(base, 'gemA', 'gemB');
    expect(base.gemA, 'two different gems must not paint the same chip').not.toBe(base.gemB);
    expect(base.gemA, 'a gem chip is never the console chrome gold').not.toBe(t.gold);
    expect(base.gemB, 'a gem chip is never the console chrome gold').not.toBe(t.gold);

    /* The cascade claim: the gem rule must actually WIN. A plain .hd-chip (no --gemc, no gem class)
       carries the chrome-ish default border; the gem chip must not land on it, or "gem-coloured"
       would be a class name with no effect — the v1622 shape in its purest form. */
    const plain = await paint(page, {
      gemA:  { html: mk('gemA', A), prop: 'borderTopColor' },
      plainC:{ html: '<span id="plainC" class="hd-chip hd-go">plain chip</span>', prop: 'borderTopColor' },
    });
    assertPainted(plain, 'gemA', 'plainC');
    expect(plain.gemA, 'the gem rule must beat the plain .hd-chip border, or the class does nothing')
      .not.toBe(plain.plainC);

    /* NOT ESTABLISHED HERE, ON PURPOSE — read this before "finishing" it.
       `.hd-chip.hd-chip-gem:hover` is a bare var(--gemc), so under hover the border should equal the
       handed-in gem exactly. That claim is NOT asserted, because in this harness the :hover state
       could not be OBSERVED, and an assertion that cannot see the state it names is worse than none:
         · page.hover() — the console's fixed chrome overlays the top-left corner, so the pointer
           either never reaches the probe or the actionability check times out (3 min, observed).
         · CDP CSS.forcePseudoState — accepted by the protocol, but getComputedStyle in the page
           still returns the UNHOVERED value (the base rule's color-mix, serialised by Chromium as
           oklab(... / 0.46)). DevTools' forced state does not feed the page's own CSSOM.
       Both attempts read the base rule and would have reported the app broken while it was correct —
       a false red, which costs exactly as much trust as a false green. The three claims above are
       measurable and do hold; the hover exactness needs a different instrument (a real pointer over
       a probe rendered outside the chrome, or a pixel read) and is left honestly unproven. */

    await clearProbes(page);
  });

  test('3 · NEGATIVE SPACE — no quality token is the console chrome gold', async ({ page }) => {
    await console_(page);
    const t = await consoleTokens(page);
    assertTokens(t, 'unique', 'set', 'rare', 'magic', 'runeword', 'orange', 'rune', 'gold');

    /* THIS is the assertion that had teeth on the old code. v1622: --rar-unique shipped AS --gold
       and a unique looked like every frame label around it. A quality that equals the chrome is
       invisible AS a quality, whatever its class is called. */
    for (const k of ['unique', 'set', 'rare', 'magic', 'runeword', 'orange', 'rune']) {
      expect(t[k], 'quality token ' + k + ' must read visibly NOT-chrome').not.toBe(t.gold);
    }

    /* and specifically every surface this version repainted, measured as pixels-worth-of-CSS rather
       than as tokens — a RULE can be pointed straight at the chrome, which is exactly what each of
       these did before v1634, and no token-level check would ever have seen it. THIS LOOP IS THE
       NON-VACUOUS ONE: run it against the pre-v1634 file and eight of these ten go red. */
    const got = await paint(page, PROBES);
    assertPainted(got, ...Object.keys(PROBES));
    for (const k of ['grailPill', 'grailTier', 'grailFind', 'grailBtn', 'grailHero', 'grailMind',
                     'grailChip', 'setsChip', 'chronUni', 'chronSet']) {
      expect(got[k], 'repainted surface ' + k + ' must not be the chrome gold').not.toBe(t.gold);
    }

    await clearProbes(page);
  });

  test('4 · MEANINGFUL DIFFERENCES — the qualities Konyo must be able to tell apart, differ', async ({ page }) => {
    await console_(page);
    const t = await consoleTokens(page);
    assertTokens(t, 'unique', 'set', 'orange', 'rune', 'rare', 'magic');

    expect(t.set,    'set green is not unique gold').not.toBe(t.unique);
    expect(t.orange, 'crafted orange is not the Forge tab rune accent').not.toBe(t.rune);
    expect(t.rare,   'rare yellow is not unique gold').not.toBe(t.unique);
    expect(t.magic,  'magic blue is not set green').not.toBe(t.set);
    expect(t.orange, 'crafted orange is not rare yellow').not.toBe(t.rare);
  });

  test('5 · DELIBERATE DOCTRINE — a NAME obeys the game, a ROOM label wears its accent', async ({ page }) => {
    await console_(page);
    const t = await consoleTokens(page);
    assertTokens(t, 'unique', 'runeword', 'rune');

    /* ┌─ DO NOT "FIX" EITHER HALF OF THIS TEST. They are two different claims about two different
       │  kinds of surface, and a future sweep that collapses them will break the app in one
       │  direction or the other. Both halves are asserted together, here, so the difference is
       │  impossible to miss:
       │
       │  (a) AN ITEM NAME OBEYS THE GAME. D2 has no runeword colour — the game paints a completed
       │      runeword's NAME the same gold it paints a unique. So --rar-runeword resolving EQUAL to
       │      --rar-unique is CORRECT and intentional (v1627/v1628 pulled this from Konyo's own
       │      _profilehd.json). An audit that sees "two tokens, one value" and de-duplicates them is
       │      deleting the distinction, not the duplication.
       │
       │  (b) A ROOM LABEL WEARS ITS ACCENT. The Forge TAB does not name an item; it names the room
       │      where runes become words. Because of (a), "runeword gold" could only ever be the same
       │      pill as F·Uniques, and Konyo needs those two tabs to differ — so v1631 gave the Forge
       │      tab --rar-rune, the colour of a RUNE ITEM. That is a label choice, not a quality claim,
       │      and it must NOT be dragged onto runeword names.
       └─ */
    expect(t.runeword, '(a) a runeword NAME is the same gold as a unique — the game has no runeword colour')
      .toBe(t.unique);

    const tab = page.locator('.head-tabs .ht[data-tab="forge"]');
    expect(await tab.count(), 'the Forge tab must exist for this claim to mean anything').toBeGreaterThan(0);
    const tabColor = await tab.first().evaluate((el: Element) => getComputedStyle(el).color);
    expect(tabColor, '(b) the Forge ROOM label wears the rune accent').toBe(t.rune);
    expect(tabColor, '(b) and is therefore NOT the runeword-name gold — that is the whole point of v1631')
      .not.toBe(t.runeword);

    /* the same doctrine, the same version, a second surface: v1634 gave the hub's FORGE progress
       chip --rar-rune for exactly the reason the tab has it. Both are room labels. If a later sweep
       "corrects" one of them to the runeword gold, it has to explain why the other one stays. */
    const chip = await paint(page, { forgeChip: { html: '<span id="forgeChip" class="hd-chip nm nm-forge">FORGE</span>', prop: 'color' } });
    assertPainted(chip, 'forgeChip');
    expect(chip.forgeChip, '(b) the FORGE hub chip is a room label too — rune accent, not runeword gold').toBe(t.rune);
    await clearProbes(page);
  });

  test('6 · CROSS-DOCUMENT PARITY — one platform, one palette', async ({ page, context }) => {
    await console_(page);
    const c = await consoleTokens(page);
    assertTokens(c, 'unique', 'set', 'rare', 'magic', 'runeword', 'orange', 'rune', 'gold');

    const boardPage = await context.newPage();
    await boardPage.goto(BOARD, { waitUntil: 'domcontentloaded' });
    const b = await boardTokens(boardPage);
    assertTokens(b, 'unique', 'set', 'rare', 'magic', 'runeword', 'orange', 'rune', 'goldBright');

    /* Both documents render these qualities. Konyo moves between the board and the Sessions console
       inside one session; a unique that is one gold on one screen and a different gold on the other
       is the failure that nothing catches unless something compares them. */
    for (const k of ['unique', 'set', 'rare', 'magic', 'runeword', 'orange', 'rune']) {
      expect(c[k], 'console and board must agree on ' + k).toBe(b[k]);
    }
    /* the chrome is shared too — which is what makes test 3's "quality != chrome" a real constraint
       on BOTH documents rather than a local console quirk */
    expect(c.gold, 'the two documents share one chrome gold').toBe(b.goldBright);

    await boardPage.close();
  });
});
