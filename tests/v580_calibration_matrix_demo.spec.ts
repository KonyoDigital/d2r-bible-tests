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
      return !ideal && (t.mercOwn || !elite);   // v583 — a BiS/ideal home passes even held as a 2H/merc stick
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

// v582 — LIVE INCIDENT (Konyo's fresh re-scan): the Zweihander (5os) registered first, so when the 1H
// Flail (5os) arrived the spare logic vendored IT ("Honor covered by your Zweihander") — backwards. A
// hand-correct base is the player home; the 2H merc-rescue is the compromise. Now: the Forge's tie-break
// prefers hand-correct bases, and a merc-rescued coverage can never spare a hand-correct candidate.
test('v582 — 1H Flail beats the earlier-registered 2H Zweihander for Honor; the Zweihander keeps for its own words (v628)', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Zweihander (5os)', 'Flail (5os)']));   // Zwei FIRST
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Amn: 1, El: 1, Ith: 1, Tir: 1, Sol: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(async () => {
    const w: any = window;
    ['Zweihander (5os)', 'Flail (5os)'].forEach((n) => w._ensureSocketBaseEntry(n));
    await new Promise((res) => setTimeout(res, 500));        // let the spare-scan memo expire
    const s = w.forgeScan();
    const honor = [...(s.now || []), ...(s.pipeline || [])].find((t: any) => t.rw === 'Honor');
    const flail = w.suggestMule('Flail (5os)');
    const zwei = w.suggestMule('Zweihander (5os)');
    return {
      honorBase: honor ? String(honor.base && honor.base.name) : 'none',
      honorMercOwn: !!(honor && honor.mercOwn),
      flailRoute: flail && flail.id, flailWhy: String((flail && flail.why) || ''),
      zweiRoute: zwei && zwei.id, zweiWhy: String((zwei && zwei.why) || ''),
    };
  });
  expect(r.honorBase).toMatch(/^Flail/);      // the Forge tasks Honor on the 1H player base
  expect(r.honorMercOwn).toBe(false);         // …not as a merc compromise
  expect(r.flailRoute).toBe('bases');         // the vault MULES the Flail (Konyo: "it should have muled it")
  expect(r.flailWhy).toContain('Honor');
  // v628 DOCTRINE FLIP: the Zweihander is no longer a vendorable spare — its 5 sockets exact-fit other
  // unmade 5os words (CtA/Eternity…), and capability in hand is a keeper. Honor itself still belongs
  // to the hand-correct Flail (asserted above) — the Zwei keeps for its OWN jobs, not as Honor's spare.
  expect(r.zweiRoute).toBe('bases');
  expect(r.zweiWhy).toContain('spare');
});

// v582.1 — re-registering an already-labelled read must not double the suffix ("Flail (5os) (5os)" —
// live incident during the Flail rescue): all register/fix paths strip repeated socket/Larzuk suffixes.
test('v582.1 — vaultSetSockets/vaultKeepAsBase strip existing suffixes (no "Flail (5os) (5os)")', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(async () => {
    const w: any = window;
    w.switchTab('tools'); w.renderVault && w.renderVault();
    await new Promise((res) => setTimeout(res, 300));
    w.vaultSetSockets('Flail (5os)', 5);                 // read already labelled → same clean label
    w.vaultKeepAsBase('Scourge (Larzuk base)');          // same for the Larzuk path
    await new Promise((res) => setTimeout(res, 300));
    const own = JSON.parse(localStorage.getItem('d2r_owned') || '[]');
    return { own, doubled: own.filter((n: string) => /\(\d+os\)\s*\(\d+os\)|\(Larzuk base\)\s*\(Larzuk base\)/i.test(n)) };
  });
  expect(r.doubled).toEqual([]);
  expect(r.own).toContain('Flail (5os)');
  expect(r.own).toContain('Scourge (Larzuk base)');
});

// v583 — THE BiS-HOME LAYER: the platform knows WHERE each word belongs, not just where it fits.
test('v583 — Flail headlines CtA/HotO (its classic jobs); Grief is ideal in a PB; BotD passes in an eth CB', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    const flailWhy = String((w.suggestMule('Flail (5os)') || {}).why || '');
    return {
      flailWhy,
      ctaIdealFlail: w._isIdealBase ? undefined : undefined,
      metaCta: (w._forgeMetaBase('Call to Arms') || {}).names,
      metaHoto: (w._forgeMetaBase('Heart of the Oak') || {}).names,
      metaGrief: (w._forgeMetaBase('Grief') || {}).names,
      metaBotd: (w._forgeMetaBase('Breath of the Dying') || {}).names,
      metaUw: (w._forgeMetaBase('Unbending Will') || {}).names,
      bisExecUw: w._isBisBaseFor('Executioner Sword', 'Unbending Will'),
      bisFlailCta: w._isBisBaseFor('Flail', 'Call to Arms'),
      bisFlailHonor: w._isBisBaseFor('Flail', 'Honor'),
      rwLine: String(w._baseRWLine('Flail', 5)),
    };
  });
  expect(r.metaCta).toContain('Flail');                      // the BiS overlay feeds the meta engine…
  expect(r.metaCta).toContain('Crystal Sword');
  expect(r.metaHoto[0]).toBe('Flail');
  expect(r.metaGrief[0]).toBe('Phase Blade');
  expect(r.metaBotd).toContain('Colossus Blade');
  expect(r.metaBotd).toContain('Berserker Axe');             // v583.1 — BiS is ADDITIVE, options stay open
  expect(r.metaUw[0]).toBe('Phase Blade');                   // UW's true 1H home (Konyo's question)
  expect(r.bisExecUw).toBe(false);                           // an exceptional Exec Sword is usable, NOT the home
  expect(r.bisFlailCta).toBe(true);
  expect(r.bisFlailHonor).toBe(false);
  expect(r.flailWhy).toMatch(/still needed for Call to Arms/); // CtA headlines, not Honor
  expect(r.flailWhy).toContain('classic');                     // …and says WHY
  expect(r.rwLine).toContain('THE classic base');              // the review card teaches the meta home
});
