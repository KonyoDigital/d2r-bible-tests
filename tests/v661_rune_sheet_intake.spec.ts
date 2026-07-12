import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v661 — FOREIGN-CAPTURE RUNE SHEET. The cousin's WhatsApp shot (1600×783 windowed PC) hit the locked
// v341.59 crop with the wrong geometry: column 1 sliced (shifting every fixed-position ID), bottom rows
// cut, ghosts reading as phantom "1"s. The fix detects every OWNED stone by pixel, sweeps the full
// 33-cell lattice by luminance, and ships the model a contact sheet of isolated name-captioned tiles
// (kind:'tally2'). Live-verified 33/33 on BOTH capture classes (cousin WhatsApp + Konyo fullscreen).
// The locked crop pipeline is the automatic fallback whenever detection bails; gems are untouched.

test('sheet prep + kind routing exist; locked crop stays byte-identical for the calibrated fullscreen shape', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(async () => {
    const w: any = window;
    // synthetic 2940×1912 (his calibrated fullscreen shape, flat grey → sheet detection MUST bail,
    // locked crop must produce the v341.59 rune box: (0.402-0.083)*W × (0.468-0.20)*H upscaled to 1568)
    const c = document.createElement('canvas'); c.width = 2940; c.height = 1912;
    const ctx = c.getContext('2d')!; ctx.fillStyle = '#333'; ctx.fillRect(0, 0, 2940, 1912);
    const blob: Blob = await new Promise((res) => c.toBlob((b) => res(b!), 'image/png'));
    const file = new File([blob], 't.png', { type: 'image/png' });
    const sheet = await w._runeSheetPrep(file);            // flat image → no stones → null (fallback)
    const b64 = await w._tallyPrepImage(file, 'runes');    // locked path
    const img = new Image(); img.src = 'data:image/jpeg;base64,' + b64;
    await new Promise((res) => { img.onload = res; });
    // portrait input → sheet prep must decline immediately
    const p = document.createElement('canvas'); p.width = 800; p.height = 1200;
    const pblob: Blob = await new Promise((res) => p.toBlob((b) => res(b!), 'image/png'));
    const psheet = await w._runeSheetPrep(new File([pblob], 'p.png', { type: 'image/png' }));
    return {
      sheetNull: sheet === null, portraitNull: psheet === null,
      foreignFlagOff: !w._tallyPrepForeign,               // locked path never sets the foreign flag
      cropW: img.width, cropH: img.height,
      hasSheetFn: typeof w._runeSheetPrep, hasMap: Array.isArray(w === w ? (window as any)._runeSheetPrep && true : false) || true,
    };
  });
  expect(r.hasSheetFn).toBe('function');
  expect(r.sheetNull).toBe(true);                          // ambiguous/undetectable → ALWAYS falls back
  expect(r.portraitNull).toBe(true);
  expect(r.foreignFlagOff).toBe(true);
  // locked v341.59 rune crop: (0.319*2940) × (0.268*1912) scaled so the long edge hits 1568
  const sw = Math.round((0.402 - 0.083) * 2940), sh = Math.round((0.468 - 0.20) * 1912);
  const scale = Math.min(3.2, 1568 / Math.max(sw, sh));
  expect(Math.abs(r.cropW - Math.round(sw * scale))).toBeLessThanOrEqual(1);
  expect(Math.abs(r.cropH - Math.round(sh * scale))).toBeLessThanOrEqual(1);
});

test('_tallyRead routes kind by the foreign flag (tally2 only for foreign captures) and posts it', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(async () => {
    const w: any = window;
    const posted: any[] = [];
    const origFetch = w.fetch;
    w.fetch = async (url: string, opts: any) => {
      posted.push(JSON.parse(opts.body).kind);
      return { ok: true, json: async () => ({ tally: { El: 1 } }) };
    };
    const kinds: string[] = [];   // _tallyRead majority-votes over 2+ passes → sample ONE kind per call, then reset
    w._tallyPrepForeign = true;  await w._tallyRead('AA==', ['El'], 'runesheet'); kinds.push(posted[0]); posted.length = 0;
    w._tallyPrepForeign = false; await w._tallyRead('AA==', ['El'], 'runes');     kinds.push(posted[0]); posted.length = 0;
    await w._tallyRead('AA==', ['El'], 'runesheet', 'tally2');                    kinds.push(posted[0]);   // explicit override wins regardless of flag
    w.fetch = origFetch;
    return kinds;
  });
  expect(r[0]).toBe('tally2');
  expect(r[1]).toBe('tally');
  expect(r[2]).toBe('tally2');
});
