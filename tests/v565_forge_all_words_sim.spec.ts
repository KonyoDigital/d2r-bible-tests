import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v565 — the two Forge simulation proofs that were still missing after the v564 audit:
//  A) ALL-WORDS ENGINE SWEEP: give EVERY runeword its ideal meta base (exact sockets) + plentiful runes →
//     every single word must surface a Forge task (now/pipeline/onestep). Proves no word can fall through
//     the engine — the per-kind specs (v470/v501/v536/v545) prove the SHAPES, this proves the COVERAGE.
//  B) RENDERED MATRIX DEMO: one combined vault that produces every major task kind at once, then the REAL
//     Forge tab renders and shows each kind in its section (make-now, pipeline, one-step, crafts).

test('A — every runeword, given its ideal base + runes, surfaces a Forge task (none falls through)', async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto(URL); await page.waitForTimeout(1500);
  // pass 1: compute per-word ideal base labels from the live meta engine, then seed localStorage
  const plan = await page.evaluate(() => {
    const w: any = window;
    const words = Object.keys(w.RUNEWORD_TIP || {});
    const labels: string[] = []; const skipped: string[] = []; const runes: Record<string, number> = {};
    // RUNES is a lexical global (not on window) — bare identifier resolves in the page's global scope
    const RUNES_REF: any[] = (typeof RUNES !== 'undefined') ? (RUNES as any) : [];
    RUNES_REF.forEach((r: any) => { runes[r.n] = 100; });
    if (!Object.keys(runes).length) return { total: -1, labels: 0, skipped: ['RUNES data unreachable'] };
    words.forEach((rw) => {
      const rec = (w.RUNEWORD_TIP[rw] || {}).rec || [];
      if (!rec.length) { skipped.push(rw + ' (no recipe)'); return; }
      const need = rec.length;
      let base = ((w._forgeMetaBase(rw) || {}).names || [])[0];
      if (!base) {
        // merc-only fallback (empty meta names): first real base that hosts the word at its exact count
        base = Object.keys(w.BASE_CLASS || {}).find((b: string) =>
          (w._baseRunewords(b) || []).some((x: any) => x.n === rw && x.s === need));
      }
      if (!base) { skipped.push(rw + ' (no base found)'); return; }
      labels.push(base + ' (' + need + 'os)');
    });
    localStorage.setItem('d2r_owned', JSON.stringify([...new Set(labels)]));
    localStorage.setItem('d2r_runeStash', JSON.stringify(runes));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');     // v549 — suppress the owner's durable 45-word floor
    localStorage.setItem('d2r_ladderMode', 'ladder');   // include ladder-only words → truly ALL
    return { total: words.length, labels: labels.length, skipped };
  });
  expect(plan.skipped).toEqual([]);                     // every word resolves to a seedable base
  // pass 2: reload so the boot path ingests the seeds, register the socketed entries, scan
  await page.reload(); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    JSON.parse(localStorage.getItem('d2r_owned') || '[]').forEach((n: string) => w._ensureSocketBaseEntry(n));
    const s = w.forgeScan();
    const have = new Set([...(s.now || []), ...(s.pipeline || []), ...(s.onestep || [])].map((t: any) => t.rw));
    const missing = Object.keys(w.RUNEWORD_TIP || {}).filter((rw) => !have.has(rw));
    return { tasks: have.size, missing, nowN: (s.now || []).length };
  });
  expect(r.missing).toEqual([]);                        // NO runeword falls through the engine
  expect(r.tasks).toBe(plan.total);                     // all 100 planned
  expect(r.nowN).toBeGreaterThan(80);                   // with exact sockets + full runes, ~all are make-now
});

test('B — combined vault renders every task kind in the real Forge tab at once', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify([
      'Wand (2os)',                    // MAKE NOW    — White (Dol+Io in hand)
      'Colossus Voulge (Larzuk base)', // PIPELINE    — Insight (runes in hand, needs Larzuk 4os)
      'Thresher (5os)',                // ONE STEP    — Obedience (missing runes)
    ]));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Dol: 1, Io: 1, Ral: 2, Tir: 1, Tal: 1, Sol: 1 }));
    localStorage.setItem('d2r_gemStash', JSON.stringify({ 'Perfect Amethyst': 1 }));   // CRAFT — Caster
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    JSON.parse(localStorage.getItem('d2r_owned') || '[]').forEach((n: string) => w._ensureSocketBaseEntry(n));
    const s = w.forgeScan();
    w.switchTab('forge');                               // renderForge fires on tab open (v470)
    const el = document.getElementById('tab-forge');
    const txt = el ? el.textContent! : '';
    return {
      scan: { white: !!(s.now || []).find((t: any) => t.rw === 'White'),
              insightPipe: !!(s.pipeline || []).find((t: any) => t.rw === 'Insight'),
              obedienceStep: !!(s.onestep || []).find((t: any) => t.rw === 'Obedience' && t.sub === 'runes'),
              craft: !!(s.crafts || []).find((c: any) => c.craft === 'Caster') },
      rendered: { white: txt.includes('White'), insight: txt.includes('Insight'),
                  obedience: txt.includes('Obedience'), caster: /Caster/i.test(txt) },
    };
  });
  expect(r.scan).toEqual({ white: true, insightPipe: true, obedienceStep: true, craft: true });
  expect(r.rendered).toEqual({ white: true, insight: true, obedience: true, caster: true });
});
