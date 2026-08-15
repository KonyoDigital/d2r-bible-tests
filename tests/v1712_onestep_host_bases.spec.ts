import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1712 — ONE STEP · THE BASES THAT CAN HOST THIS WORD.
// Konyo asked for the Forge → 🟡 ONE STEP runeword hover card to name the base items the word can
// actually be made in, with HD art, instead of only the socket-class phrase ("4 socket Body Armor").
//
// Three things here are held by the gate rather than by discipline:
//
//  (a) THE VIEW GATE. The row belongs to ONE STEP only. A gate never seen to REFUSE is not a gate,
//      so the negative case is asserted as hard as the positive one.
//  (b) SOCKET FEASIBILITY. The meta engine's curated path does not socket-filter, and it offered
//      "Mage Plate" (max 3) as an endgame home for Chains of Honor, which needs 4 — a base that can
//      never hold that word, in a row whose whole job is telling him what to farm. Every DOM
//      assertion was green; only looking at the render caught it. This sweep is why it cannot return.
//  (c) ONE SOURCE OF TRUTH. The tiles must come from window._forgeMetaBase — the same function that
//      prints the "base:" label on the task row beside the tooltip. A second, independently derived
//      list is REG-076's defect exactly (the console kept a hand-copied copy of a routing rule and it
//      went stale), and v524's "no mismatches" doctrine forbids it.

test('(a) the base row renders in ONE STEP — and REFUSES in every other Forge view', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const rw = 'Bramble';
    const tip = w.RUNEWORD_TIP[w.findRuneword(rw)];
    const at = (tab: string, view: string) => {
      document.documentElement.setAttribute('data-active-tab', tab);
      w._FORGE_VIEW = view;
      return String(w._rwTipHtml(tip, rw) || '').indexOf('att-bases') >= 0;
    };
    return {
      onestep: at('forge', 'onestep'),
      all: at('forge', 'all'),
      now: at('forge', 'now'),
      completed: at('forge', 'completed'),
      otherTab: at('session', 'onestep'),
      noName: (function () {
        document.documentElement.setAttribute('data-active-tab', 'forge');
        w._FORGE_VIEW = 'onestep';
        // called the old way, with no runeword name — must not throw and must not invent a row
        return String(w._rwTipHtml(tip) || '').indexOf('att-bases') >= 0;
      })(),
    };
  });
  expect(r.onestep).toBe(true);
  // the refusals — each one a separate way the row could leak somewhere it was never asked for
  expect(r.all).toBe(false);
  expect(r.now).toBe(false);
  expect(r.completed).toBe(false);
  expect(r.otherTab).toBe(false);
  expect(r.noName).toBe(false);
});

test('(b) no tile ever names a base whose TRUSTED socket max is below what the word needs', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    document.documentElement.setAttribute('data-active-tab', 'forge');
    w._FORGE_VIEW = 'onestep';
    const bad: string[] = [];
    let tiles = 0;
    let words = 0;
    Object.keys(w.RUNEWORD_TIP).forEach((rw: string) => {
      const need = w._rwSock ? w._rwSock(rw) : 0;
      if (!need) return;
      const html = String(w._rwHostBaseTiles(rw) || '');
      if (!html) return;
      words++;
      const d = document.createElement('div');
      d.innerHTML = html;
      Array.from(d.querySelectorAll('.att-base')).forEach((e: any) => {
        tiles++;
        const nm = (e.querySelector('.att-base-n') || {}).textContent || '';
        // _keepSocketCeil returns 0 for WEAPONS on purpose (their BASE_DB maxes are known
        // understated — v553's real 2os Wand), so weapons fail OPEN and are not judged here.
        let ceil = 0;
        try { ceil = w._keepSocketCeil ? w._keepSocketCeil(nm) || 0 : 0; } catch (x) { ceil = 0; }
        if (ceil && need > ceil) bad.push(`${rw} → ${nm} (needs ${need}, trusted max ${ceil})`);
      });
    });
    return { bad, tiles, words };
  });
  expect(r.words).toBeGreaterThan(20);   // the sweep must actually have swept something
  expect(r.tiles).toBeGreaterThan(50);
  expect(r.bad).toEqual([]);
});

test('(c) the tiles are the Forge meta-base engine, not a second list of my own', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    document.documentElement.setAttribute('data-active-tab', 'forge');
    w._FORGE_VIEW = 'onestep';
    const out: any[] = [];
    ['Bramble', 'Wrath', 'Chains of Honor', 'Enigma', 'Insight'].forEach((rw: string) => {
      const meta = (w._forgeMetaBase(rw) || {}).names || [];
      const need = w._rwSock ? w._rwSock(rw) : 0;
      // the row is the meta list, minus only the socket-infeasible entries, capped at 4
      const expected = meta.slice(0, 4).filter((bn: string) => {
        let ceil = 0;
        try { ceil = w._keepSocketCeil ? w._keepSocketCeil(bn) || 0 : 0; } catch (x) { ceil = 0; }
        return !need || !ceil || need <= ceil;
      });
      const d = document.createElement('div');
      d.innerHTML = String(w._rwHostBaseTiles(rw) || '');
      const shown = Array.from(d.querySelectorAll('.att-base-n')).map((e: any) => e.textContent);
      out.push({ rw, expected, shown });
    });
    return out;
  });
  for (const row of r) expect(row.shown, row.rw).toEqual(row.expected);
});

test('(d) an unknown word yields NO row — never an empty bordered box', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    document.documentElement.setAttribute('data-active-tab', 'forge');
    w._FORGE_VIEW = 'onestep';
    return {
      bogus: String(w._rwHostBaseTiles('Not A Runeword At All') || ''),
      empty: String(w._rwHostBaseTiles('') || ''),
      nul: String(w._rwHostBaseTiles(null) || ''),
    };
  });
  expect(r.bogus).toBe('');
  expect(r.empty).toBe('');
  expect(r.nul).toBe('');
});
