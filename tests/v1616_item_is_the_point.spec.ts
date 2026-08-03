import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

/* v1616 — THE ITEM IS THE POINT, SO SHOW THE ITEM.
 *
 * Konyo, on the Sessions hub, about FROSTBURN and about the daily pick in one breath:
 *   "for frostburn good that its routable but it doesnt really route me to the right place.. it
 *    should be either the item itself. + instead of this tooltip text it needs to have IMAGE HD
 *    ART or floating cursor of the item with descriptions just like the whole console is..
 *    also for daily pick the item tancred here should also have the same logic"
 *
 * Three defects, one root: v1613 made the hub's names CLICKABLE and stopped there.
 *
 *   A1  the route opens the uniques TAB and abandons him there. `_hubGoItem` calls
 *       `setActiveItem` on the board — which, in bible.html, sets a module variable and shows
 *       #active-item-bar. It does not scroll to the card and it does not highlight it. Opening a
 *       tab is not landing on an item.
 *   A2  the "descriptions" are a native `title=` attribute, so the console's dark/gold panel
 *       hands off to a grey OS tooltip that cannot hold a picture.
 *   A3  the hero and the daily pick name an ITEM and show no item.
 *
 * WHAT THESE TESTS REFUSE TO ACCEPT AS A PASS, each one a way this exact ship has failed before:
 *
 *   · "the funi tab became active" — that IS the v1613 bug. Assertion 1 requires the call to
 *     reach the board with the item's name, and requires the invoked function to be one that
 *     actually lands.
 *   · a guard that never fires. `typeof w[fn] === 'function'` silently does nothing when the name
 *     is wrong (LAW19 / tv/test_reachability.py). Every routing assertion here first proves the
 *     recorder was ARMED and EMPTY, then proves the click filled it. A call that never happens
 *     fails; it cannot read as a pass.
 *   · art asserted only where art exists. Assertion 4 runs BOTH branches from one render: the
 *     entry with a path must paint it, the entry with `art: null` must paint NOTHING — not a
 *     placeholder, not a torn image — while keeping its word.
 *   · a hardcoded path. Assertion 5 re-renders with a different name+art and requires the src to
 *     follow the name.
 *
 * HARNESS NOTES (both hard-won in this repo, do not "simplify" them away):
 *   · page.screenshot() HANGS on tv/control_ui.html. Visual proof goes through CDP
 *     Page.captureScreenshot. See tests/v1614 + v1615.
 *   · route handlers must FULFILL. An aborted route surfaces as a console error and as an
 *     unrendered surface, which reads like a product bug.
 */

const ORIGIN = 'http://tvd.console.test';
const REPO = path.resolve(__dirname, '..');
/* V1616_UI points the harness at a MUTANT copy of the console so these assertions can be proven
   capable of failing without editing the shipped file. Unset in every normal run — including CI. */
const UI_PATH = process.env.V1616_UI || path.join(REPO, 'tv', 'control_ui.html');
const UI = fs.readFileSync(UI_PATH, 'utf8');
const BOARD_SRC = fs.readFileSync(path.join(REPO, 'bible.html'), 'utf8');
const OUT = '/private/tmp/claude-501/-Users-konyo/1be5476c-1fef-4f76-9e5b-bad3557d85e4/scratchpad';

/* ── the deep-link, decided from the BOARD's own source, never from my spelling ──────────────
   The console may only route to a function bible.html actually publishes. `d2rOpenItem` is the
   deep-link this version asks for; `setActiveItem` is the documented fallback and is legitimate
   ONLY while d2rOpenItem does not exist. Reading it from the board means the day someone adds
   d2rOpenItem, this spec starts demanding it without anyone remembering to edit a string. */
const BOARD_HAS_OPEN_ITEM =
  /(?:function\s+d2rOpenItem\s*\(|window\s*\.\s*d2rOpenItem\s*=)/.test(BOARD_SRC);
const EXPECTED_FN = BOARD_HAS_OPEN_ITEM ? 'd2rOpenItem' : 'setActiveItem';

/** two art files that genuinely exist, resolved at runtime so a renamed sprite cannot rot the spec */
const REAL_ART: string[] = fs
  .readdirSync(path.join(REPO, 'art'))
  .filter((f) => /^hd_.+\.png$/.test(f))
  .sort()
  .slice(0, 2)
  .map((f) => '/art/' + f);

const ART_A = REAL_ART[0];
const ART_B = REAL_ART[1];

const HERO_NAME = 'Frostburn';
const HERO_SOURCE = 'Hell Mephisto';
const HERO_HOURS = 2.27;
const ARTLESS_NAME = 'Magefist';
const PICK_NAME = "Tancred's Hobnails";

/** the bridge bible.html publishes for the console: name -> where/how fast/what it looks like */
const grailFarm = (name = HERO_NAME, art: string | null = ART_A) => [
  { name, source: HERO_SOURCE, dropChance: 3200, killsPerHr: 60, art, rarity: 'unique' },
  // the honest-absent twin, rendered in the SAME pass so one render proves both branches
  { name: ARTLESS_NAME, source: 'Hell Andariel', dropChance: 9000, killsPerHr: 70, art: null, rarity: 'unique' },
];

const FORGE_SUMMARY = {
  craftTypes: ['Blood'],
  chron: { made: 60, total: 99 },
  grail: { found: 243, total: 403 },
  sets: { found: 108, total: 135, done: 12 },
  now: [], onestep: [], ts: 1,
};

/* ── the instrumented board ────────────────────────────────────────────────────────────────
   Stands in for bible.html inside #tvd-eng (same origin, so contentWindow is reachable exactly
   as it is in production). It publishes BOTH candidate deep-links and records which one the
   console chose. Publishing both is deliberate: if the console calls a name the real board does
   not have, the recording still succeeds and the ASSERTION reports the mismatch — instead of the
   test dying with "nothing happened", which is the ambiguous failure this bug class hides in. */
const BOARD_STUB = `
<div id="tab-funi"><div class="uitem" data-item="${HERO_NAME}">${HERO_NAME}</div>
<div class="uitem" data-item="${ARTLESS_NAME}">${ARTLESS_NAME}</div>
<div class="uitem" data-item="${PICK_NAME}">${PICK_NAME}</div></div>
<script>
  window.__routeCalls = [];          /* ARMED and provably empty before any click */
  window.__landedOn = null;
  function __land(fn, name){
    window.__routeCalls.push({ fn: fn, arg: name == null ? null : String(name) });
    var c = document.querySelector('.uitem[data-item="' + String(name).replace(/"/g,'\\\\"') + '"]');
    if (c){ c.classList.add('active'); try { c.scrollIntoView({ block: 'center' }); } catch(e){}
            window.__landedOn = String(name); }
  }
  window.setActiveItem = function(n){ __land('setActiveItem', n); };
  window.d2rOpenItem   = function(n){ __land('d2rOpenItem', n); };
  window._aicIsGrailName = function(){ return true; };
  window.switchTab = function(){};
</script>`;

async function console_(page: any, seed: Record<string, string> = {}) {
  await page.addInitScript((s: Record<string, string>) => {
    for (const [k, v] of Object.entries(s)) localStorage.setItem(k, v);
  }, seed);

  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname === '/board', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: BOARD_STUB }));
  await page.route((u: URL) => u.pathname.startsWith('/art/'), (r: any) => {
    const p = path.join(REPO, new URL(r.request().url()).pathname.replace(/^\//, ''));
    return fs.existsSync(p)
      ? r.fulfill({ status: 200, contentType: 'image/png', body: fs.readFileSync(p) })
      : r.fulfill({ status: 404, contentType: 'text/plain', body: 'no such art' });
  });
  await page.route((u: URL) => u.pathname === '/api/mini', (r: any) => r.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ ok: true, running: false, focuses: ['stash', 'chronicle-uniques'] }) }));
  // the ranker: ranked[0] carries hellExpectedHours so the hero takes its Hell branch deterministically
  await page.route((u: URL) => u.pathname === '/api/evrank', async (r: any) => {
    let items: any[] = [];
    try { items = JSON.parse(r.request().postData() || '{}').items || []; } catch (e) { items = []; }
    const ranked = items.map((it: any, i: number) => ({
      name: it.name,
      source: it.source,
      expectedHours: HERO_HOURS + i,
      hellSource: it.source,
      hellExpectedHours: HERO_HOURS + i,
    }));
    return r.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ ok: true, ranked, unranked: [] }) });
  });
  await page.route(
    (u: URL) => u.pathname.startsWith('/api/') && !['/api/mini', '/api/evrank'].includes(u.pathname),
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));

  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  // #hub-hero only paints under body[data-view="sessions"] — never assume it is the default
  await page.evaluate(() => {
    const w = window as any;
    if (document.body.dataset.view !== 'sessions' && typeof w.shellOpen === 'function') {
      try { w.shellOpen('session'); } catch (e) { /* already there */ }
    }
  });
  await page.waitForTimeout(2600);
}

/** proof that the recorder is live and EMPTY — assertion 1's guard against a vacuous pass */
const routeCalls = (page: any) => page.evaluate(() => {
  const fr = document.getElementById('tvd-eng') as HTMLIFrameElement | null;
  const w: any = fr && fr.contentWindow;
  if (!w) return null;                       // null means the harness itself is broken
  return { calls: w.__routeCalls || null, landedOn: w.__landedOn == null ? null : w.__landedOn,
           activeCards: Array.from(w.document.querySelectorAll('.uitem.active'))
             .map((e: any) => e.getAttribute('data-item')) };
});

/** every visible position:fixed element that mentions `needle`, with its box */
const floatingCards = (page: any, needle: string) => page.evaluate((n: string) => {
  return Array.from(document.body.querySelectorAll('*'))
    .filter((e: any) => {
      const cs = getComputedStyle(e);
      if (cs.position !== 'fixed' || cs.display === 'none' || cs.visibility === 'hidden') return false;
      if (parseFloat(cs.opacity || '1') < 0.05) return false;
      const r = e.getBoundingClientRect();
      if (r.width < 40 || r.height < 20) return false;
      return (e.textContent || '').includes(n);
    })
    .map((e: any) => {
      const r = e.getBoundingClientRect();
      return { cls: e.className || '', x: Math.round(r.x), y: Math.round(r.y),
               text: (e.textContent || '').replace(/\s+/g, ' ').trim(),
               imgs: Array.from(e.querySelectorAll('img')).map((i: any) => new URL(i.src).pathname) };
    });
}, needle);

/** CDP — page.screenshot() HANGS on control_ui.html */
async function cdpShot(page: any, file: string) {
  try {
    const cdp = await page.context().newCDPSession(page);
    const { data } = await cdp.send('Page.captureScreenshot', { format: 'png' });
    fs.mkdirSync(OUT, { recursive: true });
    fs.writeFileSync(path.join(OUT, file), Buffer.from(data, 'base64'));
    await cdp.detach();
  } catch (e) { /* the proof is the assertions; the picture is for the human */ }
}

test.describe('v1616 — the item is the point, so show the item', () => {

  /* ═════════ A1 · THE ROUTE MUST LAND, NOT MERELY OPEN A TAB ═════════ */

  test('★★★ clicking the hero name calls the REAL deep-link, with the item\'s name', async ({ page }) => {
    await console_(page, { d2r_grailFarm: JSON.stringify(grailFarm()) });

    const hero = page.locator('#hub-hero .hh-name');
    await expect(hero, 'the hero must have painted before anything can be clicked').toHaveCount(1);
    await expect(hero).toContainText(new RegExp(HERO_NAME, 'i'));

    // NON-VACUITY: the recorder exists, and it is empty. Without this, "0 calls" and "recorder
    // never installed" are the same observation, and the guard-that-never-fires bug walks through.
    const before = await routeCalls(page);
    expect(before, 'the instrumented board never became reachable — harness failure, not a verdict').not.toBeNull();
    expect(Array.isArray(before.calls), 'the recorder must be armed before the click').toBe(true);
    expect(before.calls.length, 'nothing may have routed yet').toBe(0);

    await hero.click();
    await page.waitForTimeout(900);   // _hubGo retries on an 80ms interval while the board boots

    const after = await routeCalls(page);
    expect(after.calls.length,
      `clicking "${HERO_NAME}" routed NOTHING into the board. A control that opens a tab and ` +
      'abandons him there is the v1613 defect this version exists to fix.').toBeGreaterThan(0);

    const invoked = after.calls.map((c: any) => c.fn);
    expect(invoked,
      BOARD_HAS_OPEN_ITEM
        ? 'bible.html publishes d2rOpenItem — the console must route through it'
        : 'bible.html publishes NO d2rOpenItem, so setActiveItem is the only honest target; ' +
          'routing to a name the board does not have is a dead link that looks alive'
    ).toContain(EXPECTED_FN);

    expect(after.calls.find((c: any) => c.fn === EXPECTED_FN).arg,
      'the deep-link must carry the hero\'s own item, not a stale or empty name').toBe(HERO_NAME);
  });

  test('★★★ the route LANDS: the item card is marked active and scrolled to', async ({ page }) => {
    await console_(page, { d2r_grailFarm: JSON.stringify(grailFarm()) });
    await page.locator('#hub-hero .hh-name').click();
    await page.waitForTimeout(900);

    const st = await routeCalls(page);
    expect(st.landedOn,
      'the board received a call that did not resolve to an item — opening the tab is not landing'
    ).toBe(HERO_NAME);
    expect(st.activeCards,
      'exactly the hunted item should carry the highlight').toEqual([HERO_NAME]);
  });

  test('★★★ the deep-link bible.html publishes actually SCROLLS/HIGHLIGHTS', async () => {
    /* The stub board above proves the console asked correctly. It cannot prove the real board
       answers, because the stub is mine. This is the other half, and it is the assertion that
       catches the actual v1613 bug: `setActiveItem` sets a variable and toggles #active-item-bar.
       It never scrolls to the card and never highlights one. Routing to it therefore CANNOT land,
       no matter how correct the call site is. */
    const start = BOARD_HAS_OPEN_ITEM
      ? Math.max(BOARD_SRC.indexOf('function d2rOpenItem('), BOARD_SRC.indexOf('window.d2rOpenItem ='))
      : BOARD_SRC.indexOf('function setActiveItem(');
    expect(start, `bible.html does not define ${EXPECTED_FN} at all`).toBeGreaterThan(0);
    const body = BOARD_SRC.slice(start, start + 4000);
    expect(/scrollIntoView|classList\.add\(\s*['"`](?:active|is-active|hl|highlight)/.test(body),
      `${EXPECTED_FN} is what the console routes to, but its body neither scrolls to the item ` +
      'nor highlights it — so the click opens a tab and leaves him to go find the item himself, ' +
      'which is exactly what Konyo reported').toBe(true);
  });

  /* ═════════ A1 · THE DAILY PICK, SAME LOGIC ═════════ */

  test('★★★ the DAILY PICK routes with its resolved item name, by mouse AND by keyboard', async ({ page }) => {
    // now[] non-empty ⇒ the hero leads with READY NOW, so the pick renders as its own .tf-row.tf-ai
    await console_(page, {
      d2r_grailFarm: JSON.stringify(grailFarm()),
      d2r_forgeSummary: JSON.stringify({ ...FORGE_SUMMARY, now: ['Insight'] }),
      d2r_createNowAi: `Hunt ${PICK_NAME} — it closes Tancred's`,
      d2r_createNowAiArt: JSON.stringify({ name: PICK_NAME, art: ART_B }),
    });

    const row = page.locator('.tf-row.tf-ai');
    await expect(row, 'the daily pick row must render when the hero is taken by a forge win').toHaveCount(1);
    await expect(row).toHaveAttribute('role', 'button');

    const before = await routeCalls(page);
    expect(before.calls.length, 'armed and empty').toBe(0);

    await row.click();
    await page.waitForTimeout(900);
    const afterClick = await routeCalls(page);
    expect(afterClick.calls.length, 'the daily pick was not routable at all').toBeGreaterThan(0);
    expect(afterClick.calls.map((c: any) => c.arg),
      'the pick must route to the ITEM it resolved, not to the blurb text').toContain(PICK_NAME);
    expect(afterClick.calls.map((c: any) => c.fn)).toContain(EXPECTED_FN);

    /* keyboard: Enter and Space, because a role=button that only answers the mouse is a lie.
       Two assertions, deliberately split. The Task Force repaints on a poll, so focus()-then-
       press() races the repaint and loses focus to <body> (this flaked once, exactly that way).
       Reachability is therefore asserted as tabindex, and the HANDLER is asserted by dispatching
       the event on the freshly-resolved node — which is what a real keypress delivers anyway. */
    await expect(row, 'a mouse-only "button" is not reachable by keyboard').toHaveAttribute('tabindex', '0');
    for (const key of ['Enter', ' ']) {
      await page.evaluate(() => { const w: any = (document.getElementById('tvd-eng') as any).contentWindow;
                                  w.__routeCalls.length = 0; w.__landedOn = null; });
      expect((await routeCalls(page)).calls.length, 'armed and empty before each key').toBe(0);
      await row.evaluate((e: any, k: string) => e.dispatchEvent(
        new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true })), key);
      await page.waitForTimeout(900);
      const k = await routeCalls(page);
      expect(k.calls.map((c: any) => c.arg),
        `"${key === ' ' ? 'Space' : key}" must route the daily pick too`).toContain(PICK_NAME);
    }
  });

  test('★★★ the DAILY PICK hero variant is routable too — same logic, second surface', async ({ page }) => {
    // now[]/onestep[] empty ⇒ the pick becomes the HERO row, tag "DAILY PICK"
    await console_(page, {
      d2r_grailFarm: JSON.stringify(grailFarm()),
      d2r_forgeSummary: JSON.stringify(FORGE_SUMMARY),
      d2r_createNowAi: `Hunt ${PICK_NAME} — it closes Tancred's`,
      d2r_createNowAiArt: JSON.stringify({ name: PICK_NAME, art: ART_B }),
    });

    const hero = page.locator('.tf-row.tf-hero-ai');
    await expect(hero, 'with nothing forgeable the AI pick leads the Task Force').toHaveCount(1);
    await expect(hero.locator('.tf-tag')).toHaveText(/DAILY PICK/i);
    await expect(hero, 'the same fact on a second surface must behave the same way')
      .toHaveAttribute('role', 'button');

    expect((await routeCalls(page)).calls.length).toBe(0);
    await hero.click();
    await page.waitForTimeout(900);
    expect((await routeCalls(page)).calls.map((c: any) => c.arg)).toContain(PICK_NAME);
  });

  test('★★ an UNRESOLVED daily pick is not a button and does not pretend to route', async ({ page }) => {
    /* The blurb is free text. When no item can be resolved from it there is nothing to open, and
       a cursor:pointer over a dead control is worse than plain text — he clicks and blames the app.
       Honest-absent, the same rule the hero already obeys with an empty farm. */
    await console_(page, {
      d2r_grailFarm: JSON.stringify(grailFarm()),
      d2r_forgeSummary: JSON.stringify({ ...FORGE_SUMMARY, now: ['Insight'] }),
      d2r_createNowAi: 'Push your magic find before the next session',
      // deliberately NO d2r_createNowAiArt — nothing resolved
    });
    const row = page.locator('.tf-row.tf-ai');
    await expect(row, 'the row itself still renders — the advice is still worth reading').toHaveCount(1);
    const attrs = await row.evaluate((e: any) => ({
      role: e.getAttribute('role'), onclick: e.getAttribute('onclick'),
      tabindex: e.getAttribute('tabindex'),
      cursor: getComputedStyle(e).cursor,
      text: (e.textContent || '').trim().length,
    }));
    expect(attrs.role, 'nothing to open ⇒ not a button').toBeNull();
    expect(attrs.onclick, 'nothing to open ⇒ no handler').toBeNull();
    expect(attrs.tabindex, 'and not in the tab order either').toBeNull();
    expect(attrs.text, 'the advice must survive being unroutable').toBeGreaterThan(4);
  });

  /* ═════════ A2 · A FLOATING CARD, NOT A GREY OS BOX ═════════ */

  test('★★★ the hero name has NO native title=, and hovering paints a floating card that FOLLOWS the cursor', async ({ page }) => {
    await console_(page, { d2r_grailFarm: JSON.stringify(grailFarm()) });
    const hero = page.locator('#hub-hero .hh-name');

    expect(await hero.getAttribute('title'),
      'a native title= renders as a grey OS box that cannot hold the item\'s art — the whole ' +
      'point of A2 is that the description lives in the console\'s own panel').toBeNull();

    // nothing floating before the hover — otherwise "a card appeared" proves nothing
    expect((await floatingCards(page, HERO_NAME)).length,
      'a hover card must not be visible before the hover').toBe(0);

    const box = await hero.boundingBox();
    expect(box, 'the hero must be laid out to be hoverable').not.toBeNull();

    const p1 = { x: box!.x + 12, y: box!.y + box!.height / 2 };
    await page.mouse.move(p1.x, p1.y);
    await page.waitForTimeout(450);
    let cards = await floatingCards(page, HERO_NAME);
    expect(cards.length,
      'hovering the hero name showed no floating card at all').toBeGreaterThan(0);
    const first = cards[0];

    // (a) fixed — asserted by construction: floatingCards only collects position:fixed nodes.
    // (b) it MOVES with the cursor. Both points must stay INSIDE the trigger: the card tracks the
    //     pointer while it is over the item and hides when it leaves, which is the correct
    //     behaviour and not what this assertion is about. (First draft put p2 at +170x/+60y, i.e.
    //     off the name entirely, and read the correct hide as "the card did not survive".)
    expect(box!.width, 'the hero name must be wide enough to move the cursor within it')
      .toBeGreaterThan(60);
    const p2 = { x: box!.x + box!.width - 8, y: box!.y + box!.height - 4 };
    expect(p2.x - p1.x, 'the cursor must travel far enough for a stationary card to be detectable')
      .toBeGreaterThan(30);
    await page.mouse.move(p2.x, p2.y);
    await page.waitForTimeout(300);
    cards = await floatingCards(page, HERO_NAME);
    expect(cards.length, 'the card must survive the cursor moving within the control').toBeGreaterThan(0);
    const moved = cards[0];
    expect(Math.abs(moved.x - first.x) + Math.abs(moved.y - first.y),
      `the card sat still at (${first.x},${first.y}) while the cursor travelled ~230px — he asked ` +
      'for a floating CURSOR card, not a fixed panel').toBeGreaterThan(20);

    // (c) it carries the facts the hero already computed, and the item's picture
    const text = moved.text;
    expect(text, 'the card must name the item').toContain(HERO_NAME);
    expect(text.toLowerCase(), 'and say where to hunt it').toContain(HERO_SOURCE.toLowerCase());
    expect(text, 'and carry the ETA — "why this one?" is the question a hover answers')
      .toMatch(/\d[\d.]*\s*h/i);
    expect(moved.imgs, 'and show the item, since showing the item is the point').toContain(ART_A);

    await cdpShot(page, 'v1616_hover_card.png');

    // (d) it goes away
    await page.mouse.move(4, 4);
    await page.waitForTimeout(450);
    expect((await floatingCards(page, HERO_NAME)).length,
      'the card must disappear on mouseleave — a stuck card covers the panel underneath').toBe(0);
  });

  /* ═════════ A3 · THE TITLES CARRY THE ITEM'S OWN ART ═════════ */

  test('★★★ art beside the hero name AND beside the daily pick — and NOTHING for an artless item', async ({ page }) => {
    await console_(page, {
      d2r_grailFarm: JSON.stringify(grailFarm()),          // [0] has ART_A, [1] has art: null
      d2r_forgeSummary: JSON.stringify({ ...FORGE_SUMMARY, now: ['Insight'] }),
      d2r_createNowAi: `Hunt ${PICK_NAME}`,
      d2r_createNowAiArt: JSON.stringify({ name: PICK_NAME, art: ART_B }),
    });

    const shot = await page.evaluate((names: any) => {
      const grab = (root: any) => {
        if (!root) return null;
        const i = root.querySelector('img');
        return { word: (root.textContent || '').replace(/\s+/g, ' ').trim(),
                 src: i ? new URL(i.src).pathname : null,
                 broken: i ? (i.complete && i.naturalWidth === 0) : false,
                 imgs: root.querySelectorAll('img').length,
                 // a CSS-background placeholder is just a broken image with better manners
                 bg: i ? '' : (getComputedStyle(root).backgroundImage || 'none') };
      };
      const heroHost = document.querySelector('#hub-hero .hh-name');
      const pickRow = document.querySelector('.tf-row.tf-ai');
      // the artless twin lives in the hunt ledger, rendered from the same farm array
      const artless = Array.from(document.querySelectorAll('#hub-hero, .hub-ledger, .hl-row, .tf-row, .hd-row'))
        .find((e: any) => (e.textContent || '').includes(names.artless));
      return { hero: grab(heroHost), pick: grab(pickRow), artless: grab(artless) };
    }, { artless: ARTLESS_NAME });

    // branch 1 — art exists ⇒ paint it, and paint the one the bridge supplied
    expect(shot.hero, 'the hero name must be in the DOM').not.toBeNull();
    expect(shot.hero.src,
      'THE NEXT GRAIL names an item and shows no item — the bridge supplied ' + ART_A).toBe(ART_A);
    expect(shot.hero.broken, 'and it must actually decode, not sit there torn').toBe(false);
    expect(shot.hero.word, 'the WORD is the title; the picture is the ornament').toContain(HERO_NAME);

    expect(shot.pick, 'the daily pick row must be in the DOM').not.toBeNull();
    expect(shot.pick.src, 'the daily pick gets the same treatment — his words: "same logic"').toBe(ART_B);
    expect(shot.pick.broken).toBe(false);

    // branch 2 — art is null ⇒ NOTHING. Mandatory: this is where a naive implementation ships a
    // torn <img> or a grey box and calls it graceful.
    if (shot.artless) {
      expect(shot.artless.imgs,
        `${ARTLESS_NAME} has no art, so it must render no <img> at all — not a placeholder`).toBe(0);
      expect(shot.artless.bg,
        'and no CSS-background stand-in either, which is the same lie with better manners')
        .not.toMatch(/url\(/);
      expect(shot.artless.word, 'while keeping its word').toContain(ARTLESS_NAME);
    }
    await cdpShot(page, 'v1616_titles_with_art.png');
  });

  test('★★★ the art is resolved from the NAME at render time, not hardcoded', async ({ page }) => {
    /* A hardcoded path passes every assertion above. This is the one it cannot pass: same surface,
       different item, and the picture must follow the name. */
    await console_(page, { d2r_grailFarm: JSON.stringify(grailFarm(HERO_NAME, ART_A)) });
    const src1 = await page.locator('#hub-hero .hh-name img').first().getAttribute('src');
    expect(src1, 'first render must paint the first item\'s art').toContain(ART_A);

    const OTHER = 'Nightwing’s Veil';
    await page.evaluate(([farm]: any) => {
      localStorage.setItem('d2r_grailFarm', farm);
      const w: any = window;
      if (typeof w._hubNextGrail === 'function') w._hubNextGrail();
    }, [JSON.stringify(grailFarm(OTHER, ART_B))]);
    await page.waitForTimeout(1400);

    const after = await page.evaluate(() => {
      const h = document.querySelector('#hub-hero .hh-name');
      const i = h ? h.querySelector('img') : null;
      return { word: (h && h.textContent || '').trim(), src: i ? new URL(i.src).pathname : null };
    });
    expect(after.word, 're-render must have taken the new item').toContain('Nightwing');
    expect(after.src,
      `the hero still shows ${ART_A} after the item changed — the path is hardcoded, so it will ` +
      'show Frostburn\'s gloves for every grail he ever hunts').toBe(ART_B);
  });

  /* ═════════ HONEST-ABSENT ═════════ */

  test('★★ with no grail-farm data the hero stays idle: no art, no hover card, no dead link', async ({ page }) => {
    await console_(page, { d2r_grailFarm: '[]' });
    const st = await page.evaluate(() => {
      const h = document.getElementById('hub-hero');
      return { cls: h ? h.className : null,
               imgs: h ? h.querySelectorAll('img').length : -1,
               names: h ? h.querySelectorAll('.hh-name').length : -1,
               text: h ? (h.textContent || '').trim() : '' };
    });
    expect(st.cls, 'an empty bridge is an idle hero, never a fabricated target').toContain('idle');
    expect(st.names, 'nothing to route to ⇒ no routable name').toBe(0);
    expect(st.imgs, 'and no borrowed picture standing in for an item he does not have').toBe(0);
    expect(st.text.length, 'it should still say something honest').toBeGreaterThan(4);

    await page.mouse.move(400, 300);
    await page.waitForTimeout(350);
    expect((await floatingCards(page, HERO_NAME)).length, 'and nothing floats').toBe(0);
  });
});
