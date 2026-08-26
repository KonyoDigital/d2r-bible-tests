import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v2149 — #163. THE v2135 VERDICT-STACK FOLD SHIPPED WITH NOTHING RED BEHIND IT.
//
// v2135 (`the verdict stack, measured then rebuilt`) is a behaviour ship: findings that do not
// want him render `.settled`, CSS folds their body and next-action, and clicking the headline
// opens one. Five files, ZERO tests. `rg 'chron-warn|cw-open|needsHim' tests tv/test_*.py` was
// empty, and test_control's 1166 cases never mention `.chron-warn` — they cannot see a fold that
// never ships.
//
// ⚠ AND THE PREDICTED DEFECT WAS ALREADY LIVE. push()'s sixth argument is `needsHim`, passed
// EXPLICITLY so the renderer never has to grep its own prose for "nothing to do". The cost of
// that choice is that omitting it renders the card LOUD by default. Rank 4.5 (contestedExpired)
// omitted it — while its own next-action sentence reads "not contradictions — the not-found
// reading is older and has expired, so they are not listed above", which is the same
// nothing-to-do shape as rank 3.5, which passes false. So a card that says nothing needs him sat
// permanently expanded in the stack. Fixed here; this spec is what stops the next omission.
//
// ⚠ WHY THIS EXECUTES INSTEAD OF READING THE SOURCE.
// I asked the source twice which ranks fold, with two different parsers, and got two wrong
// answers — the second because the explanatory comment I had just written contains commas, and
// the parser was splitting the call on commas. A guard that greps source fails on its own reach,
// not on the code. [[source-reading-guard]] So this mounts the SHIPPED renderer and the SHIPPED
// stylesheet and asks the rendered DOM, which is the only witness that cannot be misparsed.
// [[feedback-verify-not-proxy]]

const CONSOLE = path.resolve(__dirname, '..', 'tv', 'control_ui.html');

/** Brace-match a top-level `function NAME(` out of the console — never a copy. */
function shipped(src: string, needle: string): string {
  const i = src.indexOf(needle);
  expect(i, `${needle} vanished from control_ui.html`).toBeGreaterThan(-1);
  let depth = 0, end = src.indexOf('{', i);
  for (let k = end; k < src.length; k++) {
    if (src[k] === '{') depth++;
    else if (src[k] === '}' && --depth === 0) { end = k; break; }
  }
  return src.slice(i, end + 1);
}

/** The console's own <style> blocks, so the fold under test is the fold he sees. */
function shippedStyles(src: string): string {
  const out: string[] = [];
  const re = /<style[^>]*>([\s\S]*?)<\/style>/g;
  let m;
  while ((m = re.exec(src))) out.push(m[1]);
  expect(out.length, 'control_ui.html has no <style> blocks — the fixture would prove nothing')
    .toBeGreaterThan(0);
  return out.join('\n');
}

async function mount(page: any) {
  const src = fs.readFileSync(CONSOLE, 'utf8');
  const css = shippedStyles(src);
  const escC = shipped(src, 'function escC(');
  const strip = shipped(src, 'function _chronWarnStrip(res) {');

  // the click/keydown delegates are document-level in the console. Mount exactly ONE copy:
  // two would toggle .cw-open twice per click and cancel each other out.
  const iC = src.indexOf('var _cwOpen = {};');
  expect(iC, '_cwOpen vanished from control_ui.html').toBeGreaterThan(-1);
  const delegates = src.slice(iC, src.indexOf('function _chronWarnStrip(res) {'));

  await page.setContent(
    `<style>${css}</style><div id="mount"></div>`, { waitUntil: 'domcontentloaded' });
  await page.evaluate(([e, dg, st]: string[]) => {
    // eslint-disable-next-line no-new-func
    (0, eval)(`${e}\n${dg}\n${st}\nwindow.__strip=_chronWarnStrip;`);
  }, [escC, delegates, strip]);

  // the fold must actually exist in the mounted CSS, or every assertion below is vacuous
  const rules = await page.evaluate(() => {
    let n = 0;
    for (const sh of Array.from(document.styleSheets)) {
      try {
        for (const r of Array.from((sh as CSSStyleSheet).cssRules || []))
          if ((r as CSSRule).cssText.includes('.chron-warn.settled')) n++;
      } catch { /* cross-origin sheets cannot happen here */ }
    }
    return n;
  });
  expect(rules, 'no .chron-warn.settled rule reached the mounted CSS — the fold is untested')
    .toBeGreaterThan(0);
}

async function render(page: any, res: any) {
  return page.evaluate((r: any) => {
    const el = document.getElementById('mount') as HTMLElement;
    el.innerHTML = (window as any).__strip(r);
    return Array.from(document.querySelectorAll('.chron-warn')).map((c) => {
      const todo = c.querySelector('em.chron-todo') as HTMLElement | null;
      const body = c.querySelector('span') as HTMLElement | null;
      return {
        rank: c.getAttribute('data-rank'),
        cw: c.getAttribute('data-cw'),
        settled: c.classList.contains('settled'),
        open: c.classList.contains('cw-open'),
        todoDisplay: todo ? getComputedStyle(todo).display : null,
        bodyDisplay: body ? getComputedStyle(body).display : null,
      };
    });
  }, res);
}

// Every rank the strip can emit. cal.ok===false (rank 1) and cal.ok===null (rank 5) are mutually
// exclusive, so the map needs two fixtures — a single one would silently never reach rank 5.
const LOUD_FIXTURE = {
  denial: { denied: ['Shako'], undated: ['Hoz'], superseded: ['Occy'],
            reading: { ageDays: 2.5 } },
  calibration: { ok: false, say: 'board 240 vs game 236' },
  contested: { uniques: ['Tal Rasha’s Adjudication'] },
  notFoundDatable: { ok: false, say: 'no in-game dates on these' },
  newlyDated: [{ name: 'Griffon’s Eye', foundAt: 'day 40' }],
  contestedExpired: { uniques: ['Gheed’s Fortune'], sets: [] },
};
const UNKNOWN_FIXTURE = { calibration: { ok: null, say: 'the cross-check did not run' } };

// rank -> does this card fold? Derived by EXECUTION below, pinned here as the law.
const FOLDS: Record<string, boolean> = {
  '0': true,     // the game denies these — the register already withholds them
  '1': false,    // the board and the game do not add up — he must look
  '1.5': false,  // undatable not-found readings — unknown is not agreement
  '2': false,    // the reader contradicted itself
  '3': false,    // cannot be ordered against the game's list
  '3.5': true,   // in-game dates newer than the sweep — "nothing to do."
  '4': true,     // superseded
  '4.5': true,   // contestedExpired — THE ONE THAT WAS WRONG
  '5': false,    // the cross-check did not run
};

test('every rank folds exactly as the finding says it should', async ({ page }) => {
  await mount(page);
  const cards = [...await render(page, LOUD_FIXTURE), ...await render(page, UNKNOWN_FIXTURE)];

  const seen = cards.map((c) => c.rank).sort();
  expect(seen.length, `only ${seen.length} cards rendered (${seen}) — the fixture does not reach `
    + `every rank, so any rank it misses is untested`).toBe(Object.keys(FOLDS).length);

  for (const c of cards) {
    const want = FOLDS[c.rank as string];
    expect(want, `rank ${c.rank} rendered but is not in the fold map — a new card shipped `
      + `without a ruling on whether it wants him`).not.toBeUndefined();
    expect(c.settled, `rank ${c.rank} is ${c.settled ? 'settled' : 'LOUD'} and should be `
      + `${want ? 'settled' : 'LOUD'}. push()'s 6th argument needsHim is explicit: omit it and the `
      + `card is loud by default, which is how rank 4.5 shipped expanded while its own sentence `
      + `said there was nothing to do.`).toBe(want);
    if (want) {
      expect(c.todoDisplay, `rank ${c.rank} is settled but its next-action is still displayed `
        + `(${c.todoDisplay}) — the fold rule did not reach it`).toBe('none');
    }
  }
});

test('the denial age survives the fold, because nothing else renders it', async ({ page }) => {
  await mount(page);
  await render(page, LOUD_FIXTURE);
  const age = await page.evaluate(() => {
    const card = document.querySelector('.chron-warn[data-rank="0"]') as HTMLElement;
    const a = card && card.querySelector('.cw-age') as HTMLElement | null;
    if (!a) return null;
    const r = a.getBoundingClientRect();
    return { text: (a.textContent || '').trim(), display: getComputedStyle(a).display,
             visible: r.width > 0 && r.height > 0, insideB: !!a.closest('b') };
  });
  // den.reading.ageDays is rendered in exactly ONE place in the whole console. Folding it away
  // would hide the calibration that says whether the denial can be trusted at all.
  expect(age, '.cw-age is gone from the denial card — the reading age now renders NOWHERE')
    .not.toBeNull();
  expect(age.visible, `.cw-age is in the DOM but paints nothing (display ${age.display}) — the `
    + `fold ate the one fact that says whether the denial is fresh`).toBe(true);
  expect(age.insideB, '.cw-age left the headline, so the fold can reach it again').toBe(true);
  expect(age.text).toContain('2.5');
});

test('a card he opened stays open when the strip repaints', async ({ page }) => {
  await mount(page);
  await render(page, LOUD_FIXTURE);

  const sel = '.chron-warn[data-rank="4"]';
  await page.click(`${sel} > b`);
  const opened = await page.evaluate((s: string) => {
    const c = document.querySelector(s) as HTMLElement;
    const t = c.querySelector('em.chron-todo') as HTMLElement | null;
    return { open: c.classList.contains('cw-open'),
             todo: t ? getComputedStyle(t).display : null };
  }, sel);
  expect(opened.open, 'clicking the headline did not open the settled card').toBe(true);
  expect(opened.todo, 'the card opened but its next-action is still folded').not.toBe('none');

  // A sweep repaint rebuilds the whole strip. v2135 keeps _cwOpen OUTSIDE the renderer precisely
  // so a repaint cannot slam a card shut under him — the v2120 #23 class (scroll lost on rebuild).
  const after = await render(page, LOUD_FIXTURE);
  const card = after.find((c) => c.rank === '4');
  expect(card!.open, 'the repaint slammed the card shut — _cwOpen did not survive the rebuild')
    .toBe(true);
  expect(card!.todoDisplay, 'the card claims cw-open after the repaint but is still folded')
    .not.toBe('none');
});

test('open state is keyed per card, so two cards cannot share it', async ({ page }) => {
  await mount(page);
  await render(page, LOUD_FIXTURE);
  const keys = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.chron-warn')).map((c) => c.getAttribute('data-cw')));
  expect(new Set(keys).size, `data-cw keys collide (${keys}) — two cards would open and close `
    + `together, and a card would remember a state that was never its own`).toBe(keys.length);
  expect(keys.every((k) => !!k), 'a card shipped without data-cw, so its open state is forgotten')
    .toBe(true);
});
