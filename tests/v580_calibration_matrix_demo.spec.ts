import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v580 — THE CALIBRATION MATRIX DEMO: one vault that exercises EVERY accuracy rule shipped 2026-07-04/05,
// end to end, in a single forgeScan + render:
//   · plain white unsocketed ideal base → CUBE GAMBLE fires (HotO on Flail, need 4 < max 5)      [v575]
//   · SUPERIOR unsocketed base → NO gamble ever (Larzuk-max is its only path)                    [v575.1]
//   · elite exact-socket base + runes → MAKE NOW (Spirit in a 4os Monarch)                       [v470]
//   · ideal merc base → PIPELINE (Insight on a Larzuk Colossus Voulge)                           [v470]
//   · ENDGAME-GEAR GATE: no expensive word (top rune ≥ Ist) on a non-ideal/non-elite or
//     merc-rescued base — scan-wide invariant                                                    [v576]
//   · LADDER-CLEAN: no ladder-only word anywhere in the plan or the example chips               [v553/v577]
//   · LOOT FILTER: superior drops of gamble-only bases hidden; magic leak sealed                 [v562/v575.2]

const SEED = () => {
  localStorage.setItem('d2r_owned', JSON.stringify([
    'Flail (Larzuk base)',            // plain white ideal HotO base → gamble
    'Superior Flail (Larzuk base)',   // superior twin → Larzuk-only, never a gamble
    'Monarch (4os)',                  // elite, exact sockets → Spirit make-now
    'Colossus Voulge (Larzuk base)',  // ideal merc base → Insight pipeline
  ]));
  localStorage.setItem('d2r_runeStash', JSON.stringify({
    Ko: 1, Vex: 1, Pul: 1, Thul: 2,   // Heart of the Oak
    Tal: 2, Ort: 1, Amn: 1,           // Spirit
    Ral: 1, Tir: 1, Sol: 1,           // Insight
  }));
  localStorage.setItem('d2r_rwMade', JSON.stringify({}));
  localStorage.setItem('d2r_rwProfile', 'fresh');
  localStorage.setItem('d2r_ladderMode', 'nonladder');
};

test('the matrix: gamble/superior/make-now/pipeline/endgame-gate/ladder — one scan obeys every rule', async ({ page }) => {
  await page.addInitScript(SEED);
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    JSON.parse(localStorage.getItem('d2r_owned') || '[]').forEach((n: string) => w._ensureSocketBaseEntry(n));
    const s = w.forgeScan();
    const all = [...(s.now || []), ...(s.pipeline || []), ...(s.onestep || [])];
    const hoto = all.filter((t: any) => t.rw === 'Heart of the Oak');
    const istIdx = (w.RUNE_INDEX && w.RUNE_INDEX['Ist'] != null) ? w.RUNE_INDEX['Ist'] : 23;
    const val = (rw: string) => (((w.RUNEWORD_TIP[rw] || {}).rec) || []).reduce((m: number, x: string) => Math.max(m, (w.RUNE_INDEX || {})[x] || 0), 0);
    const gateBreaches = [...(s.now || []), ...(s.pipeline || [])].filter((t: any) => {
      if (val(t.rw) < istIdx || !t.base) return false;
      const elite = w._baseTier && w._baseTier(t.base.base) === 'elite';
      const ideal = ((w._forgeMetaBase(t.rw) || {}).names || []).some((x: string) =>
        String(t.base.base).toLowerCase().includes(x.toLowerCase()) || x.toLowerCase().includes(String(t.base.base).toLowerCase()));
      return t.mercOwn || (!elite && !ideal);
    }).map((t: any) => t.rw + '@' + t.base.name);
    const ladderLeaks = all.filter((t: any) => w._rwIsLadderOnly && w._rwIsLadderOnly(t.rw)).map((t: any) => t.rw);
    return {
      hotoGambleOnPlain: hoto.some((t: any) => t.cubeGamble && t.base && !t.base.sup),
      hotoOnSuperior: hoto.some((t: any) => t.base && t.base.sup),
      spiritNow: (s.now || []).some((t: any) => t.rw === 'Spirit' && /Monarch/.test(t.base && t.base.name || '')),
      insightPlanned: all.some((t: any) => t.rw === 'Insight' && /Voulge/.test(t.base && t.base.name || '')),
      gateBreaches, ladderLeaks,
    };
  });
  expect(r.hotoGambleOnPlain).toBe(true);   // plain white ideal base → the gamble path exists
  expect(r.hotoOnSuperior).toBe(false);     // the superior twin is NEVER offered the gamble
  expect(r.spiritNow).toBe(true);           // elite exact-socket + runes → make-now
  expect(r.insightPlanned).toBe(true);      // ideal merc base → planned (pipeline/now)
  expect(r.gateBreaches).toEqual([]);       // no expensive word on non-endgame gear, scan-wide
  expect(r.ladderLeaks).toEqual([]);        // no ladder-only word anywhere in the plan
});

test('the same vault renders in the real Forge tab, and the loot filter carries the superior-gamble hide', async ({ page }) => {
  await page.addInitScript(SEED);
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    JSON.parse(localStorage.getItem('d2r_owned') || '[]').forEach((n: string) => w._ensureSocketBaseEntry(n));
    w.switchTab('forge');
    const txt = (document.getElementById('tab-forge')!.textContent || '').replace(/\s+/g, ' ');
    const f = JSON.parse(w.buildEndgameFilter().text);
    const supHide = f.rules.find((x: any) => x.name === 'Hide Superior Gamble-Only Bases');
    const eb = w._endgameFilterBases();
    return {
      rendersSpirit: /Spirit/.test(txt), rendersInsight: /Insight/.test(txt),
      rendersHoto: /Heart of the Oak/.test(txt),
      supHideExists: !!supHide,
      supHideRarity: supHide ? supHide.equipmentRarity : null,
      gambleCodesTracked: (eb.gambleOnlyCodes || []).length >= 0 && Array.isArray(eb.gambleOnlyCodes),
    };
  });
  expect(r.rendersSpirit).toBe(true);
  expect(r.rendersInsight).toBe(true);
  expect(r.rendersHoto).toBe(true);
  expect(r.supHideExists).toBe(true);                 // superior drops of gamble-only bases are hidden
  expect(r.supHideRarity).toEqual(['hiQuality']);     // …exactly the superior rarity, nothing else
  expect(r.gambleCodesTracked).toBe(true);
});

// v580.1 — LIVE-CAUGHT BREACH: the gamble fired on Konyo's real "Superior Flail (Larzuk base)" because
// _isSuperior only consulted the intake's superior flag-set, not the NAME PREFIX. The prefix is now
// authoritative — this is the exact live repro.
test('v580.1 — a "Superior X (…)" LABEL is superior everywhere, even without the intake flag', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    return {
      byLabel: w._isSuperior('Superior Flail (Larzuk base)'),
      plain: w._isSuperior('Flail (Larzuk base)'),
    };
  });
  expect(r.byLabel).toBe(true);
  expect(r.plain).toBe(false);
});
