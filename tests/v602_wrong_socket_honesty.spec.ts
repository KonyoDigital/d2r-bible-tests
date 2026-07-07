import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v602 — two fixes from Konyo's 2026-07-07 Throw-Out Review screenshots:
// (1) WRONG-SOCKET HONESTY (the 1os Suwayyah / Pattern bug): an empty exact-fit runeword list does NOT
//     mean "its runewords are ✓ forged" — unmade words can exist at OTHER socket counts (Pattern is 3os).
//     _baseUnmadeWrongSock surfaces them; every verdict now says "X (Nos) is still unmade — this copy
//     can't host it (sockets are fixed once socketed), hunt the right-count copy" instead of lying.
// (2) FORGED-STAMP GATE (Konyo: "stamped only when ALL runewords are completely done for that base"):
//     the ⚒ Forged ✓ stamp means "ignore this base type forever", so it only renders when EVERY word the
//     base can EVER hold is created — all-at-this-count-only now shows a plain ✓ + an amber "base type
//     NOT fully forged" note naming the other-count words. Also: the Larzuk/cube socket guide no longer
//     renders on already-socketed copies (Larzuk + the cube recipe require zero sockets).

test('1os Suwayyah: Pattern-class unmade words at other counts are named, never called "✓ forged"', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));   // fresh Chronicle — nothing forged
    const ws = (w._baseUnmadeWrongSock('Suwayyah', 1) || []) as Array<{ n: string; s: number }>;
    const sm = w.suggestMule('Suwayyah (1os)');
    const patternLive = !!(w.RUNEWORD_TIP && w.RUNEWORD_TIP['Pattern'])
      && !(typeof w._rwLadderBlocked === 'function' && w._rwLadderBlocked('Pattern'));
    localStorage.removeItem('d2r_rwMade');
    return {
      wsNames: ws.map((x) => x.n), wsSocks: ws.map((x) => x.s), patternLive,
      smId: sm && sm.id, smWhy: String((sm && sm.why) || ''),
    };
  });
  expect(r.wsNames.length).toBeGreaterThan(0);            // claw words DO exist unmade — just not at 1os
  expect(r.wsSocks).not.toContain(1);                     // wrong-sock list = other counts only
  // v603.1 — v385 max-socket cap: a claw maxes at 3os, so 4-6os words (Phoenix/BotD…) must NOT appear —
  // the verdict may never tell Konyo to hunt an impossible 4os+ Suwayyah
  expect(Math.max(...r.wsSocks)).toBeLessThanOrEqual(3);
  if (r.patternLive) expect(r.wsNames).toContain('Pattern');   // Konyo's exact case
  expect(r.smId).toBe('__throwout');                      // this copy still can't be fixed → vendor it
  expect(r.smWhy).toContain('still unmade');              // …but the verdict is HONEST about why
  expect(r.smWhy).toContain('hunt');                      // …and points at the right-count copy to find
  expect(r.smWhy).not.toContain('✓ forged');              // the old lie is gone
});

test('throw-out card + tip for a socketed copy: honest amber note, no Larzuk/cube socket guide', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    const line1os = String(w._baseRWLine('Suwayyah', 1) || '');
    const tipSock = String(w._throwTipHtml ? w._throwTipHtml('Suwayyah (1os low base)') : '');
    const tipBare = String(w._throwTipHtml ? w._throwTipHtml('Suwayyah') : '');
    localStorage.removeItem('d2r_rwMade');
    return { line1os, tipSockHasGuide: /guaranteed max/.test(tipSock), tipBareHasLarzuk: /Larzuk/.test(tipBare) };
  });
  expect(r.line1os).toContain('none takes exactly 1 socket');   // the exact-fit truth stays
  expect(r.line1os).toContain('NOT fully forged');              // …but the other-count words are now named
  expect(r.line1os).toMatch(/needs a fresh copy/);              // with the "sockets are fixed" explanation
  expect(r.tipSockHasGuide).toBe(false);   // a 1os copy can NEVER be Larzuk'd/cubed — guide suppressed
  expect(r.tipBareHasLarzuk).toBe(true);   // a name-only (unsocketed) read keeps its socketing guidance
});

test('⚒ Forged stamp only when EVERY word the base can ever hold is created', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  // pick a NON-SEEDED other-count word on Monarch to leave unmade (the seed force re-marks seeded words
  // on load, so the hold-out must be one Konyo hasn't forged) — then mark everything else created.
  const target = await page.evaluate(() => {
    const w: any = window;
    const rws = (w._baseRunewords('Monarch') || []) as Array<{ n: string; s: number }>;
    const seed = w._RWC_SEED || {};
    const t = rws.find((r) => r.s !== 4 && r.s <= 4 && !seed[r.n]
      && !(typeof w._rwLadderBlocked === 'function' && w._rwLadderBlocked(r.n)));
    const made: any = {};
    Object.keys(w.RUNEWORD_TIP || {}).forEach((n) => { if (!t || n !== t.n) made[n] = 'x'; });
    localStorage.setItem('d2r_rwMade', JSON.stringify(made));
    return t ? { n: t.n, s: t.s } : null;
  });
  expect(target).not.toBeNull();   // Monarch hosts sub-4os words (Rhyme/Ancient's Pledge class)
  await page.reload(); await page.waitForTimeout(1500);   // rwMade global re-inits from localStorage
  const partial = await page.evaluate(() => {
    const w: any = window;
    return { ks: String(w._baseRWLine('Monarch', 4) || ''), noKs: String(w._baseRWLine('Monarch', 0) || '') };
  });
  // all 4os words made but one 2/3os word open → NO stamp, plain ✓ + amber note naming the hold-out
  expect(partial.ks).not.toContain('⚒ Forged');   // NOT 'rw-stamp' — the '✓ already created' mini-tag's class contains that substring
  expect(partial.ks).toContain('NOT fully forged');
  expect(partial.ks).toContain(target!.n);
  expect(partial.noKs).not.toContain('⚒ Forged');
  expect(partial.noKs).toContain('still unmade below max');
  // v603 — the '✓ already created' SEAL styling is also gated: words still open → plain label, no seal band
  expect(partial.ks).toContain('already created');       // the created words are still LISTED…
  expect(partial.ks).not.toContain('rw-stamp-mini');     // …but never with the done-seal styling
  expect(partial.ks).not.toContain('base complete');
  // now close the hold-out too → the stamp returns, worded as the WHOLE base type being done
  await page.evaluate(() => {
    const w: any = window;
    const made: any = {}; Object.keys(w.RUNEWORD_TIP || {}).forEach((n) => (made[n] = 'x'));
    localStorage.setItem('d2r_rwMade', JSON.stringify(made));
  });
  await page.reload(); await page.waitForTimeout(1500);
  const full = await page.evaluate(() => {
    const w: any = window;
    const out = { ks: String(w._baseRWLine('Monarch', 4) || ''), noKs: String(w._baseRWLine('Monarch', 0) || '') };
    localStorage.removeItem('d2r_rwMade');
    return out;
  });
  expect(full.ks).toContain('⚒ Forged');
  expect(full.ks).toContain('can ever hold');
  expect(full.noKs).toContain('⚒ Forged');
  // v603 — base fully forged → the created list becomes the flat HORIZONTAL seal band (trade-keeper signal)
  expect(full.ks).toContain('rw-band');
  expect(full.ks).toContain('base complete');
  expect(full.ks).toContain('save spares for trading');
});
