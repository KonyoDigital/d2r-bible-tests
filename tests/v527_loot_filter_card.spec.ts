import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v527 / v535 — the Tools "Loot Filters" card now serves ONE filter that is REBUILT LIVE from the Chronicle:
// unmade runeword -> its socket-correct meta base(s) (window._forgeMetaBase) -> base item code. No "cube up a
// white base" premise (v534: white bases can't be tier-upgraded). Guards: card exists, the dynamic builder
// works, the output parses, is circlet-clean, and shrinks as words are marked made. The old static all-tier
// "KonyoChron" embed is GONE.

test('Tools loot-filter card: dynamic endgame filter builds valid, circlet-clean, importable JSON', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const tplEl = document.getElementById('lf-data-endgame');
    const tpl = tplEl ? JSON.parse(tplEl.textContent!.trim()) : null;
    const built = w.buildEndgameFilter ? w.buildEndgameFilter() : null;
    let out: any = null;
    try { out = built ? JSON.parse(built.text) : null; } catch (e) {}
    const circletLeak = (f: any) => !f ? true : f.rules
      .filter((r: any) => ['3. Show ETH and Socket bases', 'Show Base Items'].includes(r.name))
      .some((r: any) => (r.equipmentCategory || []).includes('circl') || (r.equipmentItemCode || []).some((x: string) => ['ci0', 'ci1', 'ci2', 'ci3'].includes(x)));
    return {
      card: !!document.getElementById('loot-filters-card'),
      copyFn: typeof w.copyLootFilter,
      buildFn: typeof w.buildEndgameFilter,
      chronGone: !document.getElementById('lf-data-chron'),
      tplName: tpl && tpl.name, tplRules: tpl && tpl.rules.length,
      outName: out && out.name, outRules: out && out.rules.length,
      baseCount: built && built.baseCount,
      outLeak: circletLeak(out),
    };
  });
  expect(r.card).toBe(true);
  expect(r.copyFn).toBe('function');
  expect(r.buildFn).toBe('function');
  expect(r.chronGone).toBe(true);              // old all-tier "cube these up" filter removed
  expect(r.tplName).toBe('KonyoEndgame');      expect(r.tplRules).toBe(13);
  expect(r.outName).toBe('KonyoEndgame');      expect([17, 18]).toContain(r.outRules);   // v562 +4 tail hides; v575.2 +1 superior-gamble hide when gamble-only codes exist
  expect(r.baseCount).toBeGreaterThan(20);     // a real set of socket-correct bases
  expect(r.outLeak).toBe(false);               // no white circlets leak in
});

test('the filter shrinks when runewords are marked made (live-synced to the Chronicle)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const nAll = w._endgameFilterBases().codes.length;   // nothing made yet
    // Mark EVERY runeword made -> nothing left to farm for WORDS -> the filter shrinks to exactly the
    // v588 premium trade floor (bases worth keeping for TRADE regardless of the Chronicle).
    const made: Record<string, boolean> = {};
    Object.keys(w.RUNEWORD_TIP || {}).forEach((rw) => { made[rw] = true; });
    localStorage.setItem('d2r_rwMade', JSON.stringify(made));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    const nNone = w._endgameFilterBases().codes.length;
    return { nAll, nNone, nPremium: (w._premiumTradeBases || []).length };
  });
  expect(r.nAll).toBeGreaterThan(r.nPremium);   // word-driven bases on top of the floor
  expect(r.nNone).toBe(r.nPremium);             // all words made -> shrinks to exactly the premium trade floor (v588)
});

// v536.2 — the loot filter must stay SYNCED with the Forge: don't tell you to FARM the ideal base for a word
// you already own a socket-correct base for. Insight (Ral+Tir+Tal+Sol) → its meta base is Colossus Voulge, which
// no other unmade word uses. (Konyo's live case: Eternity/Honor on his Thresher+Cryptic Axe → Scourge/Ettin Axe
// correctly dropped.) Two scenarios, each seeded before load so the app reads the owned bases.
test('v536.2 — with NO base owned, the word\'s meta base IS in the loot filter', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify([]));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 1, Tir: 1, Tal: 1, Sol: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => ({ names: (window as any)._endgameFilterBases().names }));
  expect(r.names).toContain('Colossus Voulge');   // you need to farm the base for Insight
});

test('v536.2 — owning a socket-correct base for the word DROPS its base from the filter (synced with the Forge)', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 1, Tir: 1, Tal: 1, Sol: 1 }));
    // NOTE: rwMade deliberately NOT set here — addInitScript re-runs on reload and would stomp the
    // pinned Chronicle written below (the v578.1 lesson).
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  // v587 — CAPACITY: pin the Chronicle so Insight is the ONLY unmade word. With everything unmade, six
  // 4os polearm words pile onto the ONE Voulge copy; Insight is out-valued, flags baseOver, and its base
  // correctly STAYS farmable. The drop-from-filter promise only holds when the owned copy is genuinely
  // planned for THIS word — so this spec pins exactly that scenario.
  await page.evaluate(() => {
    const w: any = window;
    const made: any = {}; Object.keys(w.RUNEWORD_TIP || {}).forEach((n) => { if (n !== 'Insight') made[n] = 'x'; });
    localStorage.setItem('d2r_rwMade', JSON.stringify(made));
    localStorage.setItem('d2r_rwProfile', 'fresh');
  });
  await page.reload(); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Colossus Voulge (4os)');
    const s = w.forgeScan();
    const insight = [...s.now, ...s.pipeline].find((t: any) => t.rw === 'Insight');
    return { insightHasBase: !!(insight && insight.base), names: w._endgameFilterBases().names };
  });
  expect(r.insightHasBase).toBe(true);              // Insight is a Forge make-now/pipeline task (base owned)
  expect(r.names).not.toContain('Colossus Voulge'); // …so you don't farm its base → dropped from the filter
});

test('every base code emitted maps to a real base name in the embedded code map', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const CODE = JSON.parse(document.getElementById('lf-base-codes')!.textContent!.trim());
    const valid = new Set(Object.values(CODE));
    const eb = w._endgameFilterBases();
    const orphan = eb.codes.filter((c: string) => !valid.has(c));
    return { total: eb.codes.length, orphan, names: eb.names.length };
  });
  expect(r.orphan).toEqual([]);                // no code without a source base name
  expect(r.names).toBeGreaterThan(0);
});
