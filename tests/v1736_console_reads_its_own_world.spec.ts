import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1736 — THE CONSOLE MUST SPEAK THE ROUTE THE BOARD ACTUALLY PUBLISHES.
//
// bible.html publishes `d2r_lsrRoute` so the console never re-derives the fork rule. v1478 built
// that. v1499 then changed the route's VOCABULARY — `m` stopped being 'mac'/'windows' and became
// 'owner'/'guest', and the route began carrying the LITERAL prefixes (`pfx`, `lpfx`) so that no
// other surface would ever construct one. The board shipped v:2.
//
// tv/control_ui.html's `lsFork()` was never told. It still read `r.m` expecting a machine name and
// still branched on `machine === 'windows'` — a value the board had stopped writing. Executed
// against a real v:2 guest route, `machine` was 'guest', that branch could not fire, and control
// fell through to `return localStorage.getItem(bare)`: the OWNER's key. Two failures in one —
//
//   * the LEAK — the "HOLY GRAIL 243 / 403 · 60% claimed" bleed that REG-076 was written to close,
//     reopened three versions later by a vocabulary change rather than by any change to the logic;
//   * and plain BLINDNESS — the board writes a guest world at `I·<id8>·`, the console looked at
//     bare, so a guest console could not read its own data at all.
//
// [[the-unjoined-end]] — both ends built correctly, the joint never made, and silent by construction.
//
// WHY THIS FILE EXISTS ALONGSIDE tv/test_control.py's TestConsoleReadsTheActiveWorld:
// that test does the right thing — it EXECUTES the shipped function rather than grepping it — but
// it drives Chrome with `--dump-dom` over http://127.0.0.1, and on this machine Chrome never
// answers that way. It SKIPS, with a message that says so honestly and even notes "Playwright
// drives the same binary fine". So the one check that could have caught this had never run here.
// A gate that always skips is the same defect as a gate that cannot fail.
// [[feedback-blind-fixture-green-gate]]
//
// This runs the same cases through Playwright, which works, so the check actually executes.

const CONSOLE = path.resolve(__dirname, '..', 'tv', 'control_ui.html');
const BOARD = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/** Pull the SHIPPED lsFork out of control_ui.html — never a copy, so the test cannot drift. */
function shippedLsFork(): string {
  const src = fs.readFileSync(CONSOLE, 'utf8');
  const i = src.indexOf('function lsFork(bare){');
  expect(i, 'lsFork() vanished from control_ui.html').toBeGreaterThan(-1);
  let depth = 0, end = src.indexOf('{', i);
  for (let k = end; k < src.length; k++) {
    if (src[k] === '{') depth++;
    else if (src[k] === '}' && --depth === 0) { end = k; break; }
  }
  return src.slice(i, end + 1);
}

const ID = 'abcd1234efgh';
const route = (owner: boolean, p: string) => ({
  v: 2, owner, id: ID, m: owner ? 'owner' : 'guest', p,
  pfx: owner ? '' : 'I·' + ID.slice(0, 8) + '·',
  lpfx: owner ? 'L·' : 'IL·' + ID.slice(0, 8) + '·',
  lp: ['K'], wp: ['K'],
});

const CASES: [string, any, Record<string, string>, string | null][] = [
  ['owner main reads bare',      route(true, 'main'),    { 'K': 'owner' },                              'owner'],
  ['owner ladder reads L',       route(true, 'ladder'),  { 'L·K': 'owner-l' },                     'owner-l'],
  ['guest main reads I<id8>',    route(false, 'main'),   { 'I·abcd1234·K': 'mine' },          'mine'],
  ['guest ladder reads IL<id8>', route(false, 'ladder'), { 'IL·abcd1234·K': 'mine-l' },       'mine-l'],
  // the case that actually bit: this world has farmed nothing, the owner has
  ['guest empty stays empty',    route(false, 'main'),   { 'K': 'owner' },                              null],
  ['guest ladder no fallback',   route(false, 'ladder'), { 'K': 'owner', 'L·K': 'x' },             null],
  // "Guessing bare is how the harm happened" — bible.html's own v1499 instruction
  ['no route reads nothing',     null,                   { 'K': 'owner' },                              null],
  ['v:1 route reads nothing',    { v: 1, m: 'mac', p: 'main', lp: ['K'], wp: ['K'] }, { 'K': 'owner' }, null],
];

test.describe('v1736 — the console reads its own world, not the owner\'s', () => {
  test('★★★ the shipped lsFork lands on the key the board would have written', async ({ page }) => {
    // a real origin with a real localStorage; the board is only the host page here
    await page.goto(BOARD);
    const results = await page.evaluate(([fnSrc, cases]: [string, any[]]) => {
      // eslint-disable-next-line no-eval
      const lsFork = eval('(' + fnSrc + ')');
      return cases.map((c: any) => {
        localStorage.clear();
        if (c[1]) localStorage.setItem('d2r_lsrRoute', JSON.stringify(c[1]));
        for (const k of Object.keys(c[2])) localStorage.setItem(k, c[2][k]);
        let got: any;
        try { got = lsFork('K'); } catch (e: any) { got = 'THREW ' + e.message; }
        return { label: c[0], want: c[3], got: got === undefined ? null : got };
      });
    }, [shippedLsFork(), CASES] as any);

    // non-vacuity: every case must have actually run
    expect(results.length, 'no routing cases were executed').toBe(CASES.length);
    const failures = results
      .filter((r: any) => r.got !== r.want)
      .map((r: any) => `${r.label}: wanted ${JSON.stringify(r.want)}, got ${JSON.stringify(r.got)}`);
    expect(failures, 'console routing: ' + failures.join(' | ')).toEqual([]);
  });

  test('★★★ the console builds no prefix of its own — the route carries them', async () => {
    const src = fs.readFileSync(CONSOLE, 'utf8');
    const i = src.indexOf('function lsFork(bare){');
    let depth = 0, end = src.indexOf('{', i);
    for (let k = end; k < src.length; k++) {
      if (src[k] === '{') depth++;
      else if (src[k] === '}' && --depth === 0) { end = k; break; }
    }
    const body = src.slice(i, end + 1).replace(/\/\/[^\n]*/g, '');   // strip comments: they name the prefixes
    /* Every prefix literal must come from the payload. A hand-built 'W·'+bare is exactly the
       residue REG-076 was made of, and it is how this function fell out of step twice. */
    const literals = [...body.matchAll(/['"](?:W|WL|L|I|IL)\\u00b7['"]|['"](?:W|WL|L|I|IL)·['"]/g)]
      .map((m) => m[0]);
    expect(literals, 'lsFork constructs prefixes instead of reading them: ' + literals.join(', '))
      .toEqual([]);
    // and it must not branch on the retired machine vocabulary
    expect(/machine\s*===\s*['"]windows['"]/.test(body),
      'lsFork still branches on the pre-v1499 machine vocabulary').toBe(false);
  });
});
