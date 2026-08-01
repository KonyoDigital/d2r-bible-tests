import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1552 — THE SIGIL MUST MEAN THE SAME THING ON BOTH SURFACES.
//
// Found by auditing every `window.X =` export in the board for one nobody calls. 649 exports, 33
// with no in-file caller, and 32 of those turned out to be called from a spec, the console or Kai —
// legitimate. Exactly one was called by nothing anywhere: `window.D2R_SIGIL`.
//
// It is unused because the console does not load the board. It carries its OWN copy of the
// algorithm — GLYPHS, HUES, the adjective and noun tables, and FNV-1a — and exports it as
// `window.TVD_SIGIL`. Two implementations of one identity, in two files, with no link between them.
//
// That is a live hazard rather than untidiness. The sigil's whole job, in its own words, is that
// "a colour seen across a room and a name said out loud agree". If either copy's word list, hue
// list or hash drifts by one entry, the same machine wears one identity on the board and a
// different one in the console, and the thing he uses to tell his Mac from his Windows PC from his
// cousin's box starts lying.
//
// The duplication is structural — the console is a separate document and cannot import from a 38k
// line board at runtime — so the fix is not to delete a copy. It is to pin them together here.

const BOARD = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const ORIGIN = 'http://tvd.console.test';
const UI_HTML = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

/** Ids spanning what actually gets hashed: install uuids, machine names, empties, unicode. */
const IDS = [
  'a1b2c3d4e5f60718293a4b5c6d7e8f90', '0', 'konyo-mac', 'KONYO-MAC', 'windows-pc',
  'cousin-box-2', 'ᚠᚢᚦ', 'the quick brown fox', '9f'.repeat(16), 'z',
  '00000000000000000000000000000000', 'ffffffffffffffffffffffffffffffff',
];

async function boardSigils(page: any) {
  await page.goto(BOARD);
  await page.waitForTimeout(1800);
  return page.evaluate((ids: string[]) => {
    const w: any = window;
    if (!w.D2R_SIGIL || typeof w.D2R_SIGIL.of !== 'function') return null;
    return ids.map((id) => w.D2R_SIGIL.of(id));
  }, IDS);
}

async function consoleSigils(page: any) {
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI_HTML }));
  await page.route((u: URL) => u.pathname.startsWith('/api/'), (r: any) => r.abort());
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(600);
  return page.evaluate((ids: string[]) => {
    const w: any = window;
    if (!w.TVD_SIGIL || typeof w.TVD_SIGIL.of !== 'function') return null;
    return ids.map((id) => w.TVD_SIGIL.of(id));
  }, IDS);
}

test.describe('v1552 — one identity, two surfaces', () => {
  test('★ BOTH surfaces expose their sigil, so they CAN be compared', async ({ page }) => {
    // D2R_SIGIL was the one export in the whole board that nothing called. It is not dead code —
    // it is the seam that makes this test possible, and now it has a caller.
    const b = await boardSigils(page);
    expect(b, 'window.D2R_SIGIL must exist on the board').not.toBeNull();
    const c = await consoleSigils(page);
    expect(c, 'window.TVD_SIGIL must exist in the console').not.toBeNull();
  });

  test('★ THE SAME ID PRODUCES THE SAME SIGIL ON BOTH', async ({ page }) => {
    const b = await boardSigils(page);
    const c = await consoleSigils(page);
    expect(b).not.toBeNull();
    expect(c).not.toBeNull();
    for (let i = 0; i < IDS.length; i++) {
      expect(c![i], 'id ' + JSON.stringify(IDS[i]) + ' — the two surfaces disagree about who this machine is')
        .toEqual(b![i]);
    }
  });

  test('★ glyph, hue, NAME and code all agree — not just the one you happen to look at', async ({ page }) => {
    // a partial match is the worst outcome: the colour matches across the room and the name said
    // out loud does not, which is precisely the failure the index-lock comment warns about
    const b = await boardSigils(page);
    const c = await consoleSigils(page);
    const fields = ['glyph', 'hue', 'name', 'code'] as const;
    for (const f of fields) {
      expect(c!.map((x: any) => x[f]), 'field "' + f + '" differs between board and console')
        .toEqual(b!.map((x: any) => x[f]));
    }
  });

  test('an empty id is null on both, rather than a sigil for nobody', async ({ page }) => {
    await page.goto(BOARD); await page.waitForTimeout(1800);
    const b = await page.evaluate(() => (window as any).D2R_SIGIL.of(''));
    await page.route(ORIGIN + '/ui', (r: any) =>
      r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI_HTML }));
    await page.route((u: URL) => u.pathname.startsWith('/api/'), (r: any) => r.abort());
    await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(500);
    const c = await page.evaluate(() => (window as any).TVD_SIGIL.of(''));
    expect(b).toBeNull();
    expect(c).toBeNull();
  });

  test('★ the four tables are byte-identical in both files', async () => {
    // the behavioural test above is the one that matters, but this names WHICH table moved when it
    // fails, which is the difference between a two-minute fix and an afternoon
    const read = (p: string) => {
      const s = fs.readFileSync(path.resolve(__dirname, '..', p), 'utf8');
      const i = s.indexOf('GLYPHS');
      const j = s.indexOf('sigilFor', i);
      const seg = s.slice(Math.max(0, i - 400), j + 700);
      const grab = (n: string) => {
        const m = new RegExp('\\b' + n + '\\s*=\\s*(\\[[\\s\\S]*?\\])').exec(seg);
        return m ? [...m[1].matchAll(/'([^']*)'/g)].map((x) => x[1]) : null;
      };
      return { GLYPHS: grab('GLYPHS'), HUES: grab('HUES'), A: grab('A'), B: grab('B') };
    };
    const b = read('bible.html');
    const c = read('tv/control_ui.html');
    for (const k of ['GLYPHS', 'HUES', 'A', 'B'] as const) {
      expect(b[k], k + ' missing from the board').not.toBeNull();
      expect(c[k], k + ' missing from the console').not.toBeNull();
      expect(c[k], 'the ' + k + ' table drifted between the two surfaces').toEqual(b[k]);
    }
    // index-lock: one index drives both the adjective and its colour, so these must stay equal
    expect(b.HUES!.length, 'adjective and hue are index-locked — equal lengths or the colour lies')
      .toBe(b.A!.length);
  });

  test('the sigil is stable across reloads — an identity that changes is not one', async ({ page }) => {
    const once = await boardSigils(page);
    const twice = await boardSigils(page);
    expect(twice).toEqual(once);
  });
});
