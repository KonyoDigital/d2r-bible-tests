import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v3526 — ONE HUNT CLOCK.
//
// Konyo, 2026-09-30, on Cow King's Hooves — the one set piece he has left: "the time to hunt is not synced
// across here and the sessions tab... here it says 84hrs. and in sets its like a million hours.. something is
// bugged i mentioned this to you alraedy before... make sure its calliberated too."
//
// MEASURED on this page before the fix (MF 699, every piece ticked but the Hooves), for ONE piece at ONE run:
//   Sets run row    "expected ~1 every 20030h of running"   kph / per-KILL odds, no kills-per-run
//   Sets quick win  "1:140.2k ~40h to find"                 right
//   Sets hero       "best run: Normal TZ Hell Bovines 1:157.5k"   the RAW odds, and no time
//   console         78.7h in Hell · "faster outside Hell ≈39.7h" over the d2r_setFarm bridge — right
// This spec drives the real forge and the real bridge the console ranks, and pins the OUTCOME: one piece,
// one run, one hour, one set of odds, one name — everywhere. The engine itself is pinned by
// tv/test_one_hunt_clock.py (node over the cut code + control_app._ev_rank).

/* 2026-09-30 — BOOT IS A STATE, NOT A DELAY. Red on v3526's CI: 76 grail rows where a booted page writes 383 (372 matched,
   0 mismatches, measured on a fresh headless page). _writeGrailFarm falls back to the old tier scan while the forge half
   (window.funiScan) has not booted, and 2.2 s was not enough on a slower runner. It waits for the seam it reads. */
const boot = async (page: any) => {
  await page.goto(URL);
  await page.waitForFunction(() => typeof (window as any).funiScan === 'function'
    && typeof (window as any).fsetsScan === 'function', undefined, { timeout: 30000 });
  await page.waitForTimeout(400);
};

test.describe('v3526 — one hunt clock', () => {
  test('★ the Hooves read ONE hour and ONE set of odds on the run row, the quick win, the hero and the bridge', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const E: any = (0, eval);   // top-level consts (hoursFor, killsPerRun) are not window properties
      const s0 = w.fsetsScan(); const all: string[] = [];
      s0.sets.forEach((st: any) => st.pieces.forEach((p: any) => all.push(p.name)));
      w.LSR.setItem('d2r_setPieces', JSON.stringify(all.filter((n: string) => !/^Cow King's Hooves/.test(n))));
      w._fsLanded = true; w.fsetsSetFilter('all');
      const box = document.getElementById('fsets-body') as HTMLElement;
      const txt = (e: Element | null) => (e ? (e.textContent || '').replace(/\s+/g, ' ').trim() : '');
      const grab = (s: string, re: RegExp) => { const m = s.match(re); return m ? m[1] : null; };
      const run = txt(box.querySelector('.f-pipe .f-atomsubrow'));
      const quick = txt(box.querySelector('.f-step .gf-src'));
      const hero = txt(box.querySelector('.forge-hero .fh-body'));
      const src = w._pieceSrc("Cow King's Hooves (heavy boots)");
      const adj = w._fAdjC(src, "Cow King's Hooves");
      const card = w._ttf(adj, src.kph, E('killsPerRun')(src.bossId));
      const odds = '1:' + (adj >= 1000 ? (Math.round(adj / 100) / 10) + 'k' : adj);
      try { E('_writeSetFarm')(); } catch (e) {}
      let row: any = null;
      try {
        const sf = JSON.parse(localStorage.getItem('d2r_setFarm') || w.LSR.getItem('d2r_setFarm') || 'null');
        const rows = (sf && (sf.items || sf)) || [];
        row = (rows.filter ? rows : []).filter((x: any) => /Cow King/.test(String(x.set || x.name || '')))[0] || null;
      } catch (e) {}
      const evh = (p: number, k: number) => (p > 0 && p < 1 && k > 0) ? Math.ceil(Math.log(0.5) / Math.log(1 - p)) / k : null; // control_app._ev_hours
      return {
        run, quick, hero, card, odds, srcBoss: src.boss,
        runHr: grab(run, /~(\S+) to find it/), quickHr: grab(quick, /~(\S+) to find/), heroHr: grab(hero, /~(\S+) to find/),
        quickOdds: grab(quick, /(1:[\d.]+k?)/), heroOdds: grab(hero, /(1:[\d.]+k?)/),
        quickHell: grab(quick, /Hell: (.+?) ~/), quickHellHr: grab(quick, /Hell: .+? ~(\S+)/), heroHellHr: grab(hero, /Hell: .+? ~(\S+)/),
        bridge: row ? { source: row.source, hellSource: row.hellSource,
                        hr: w._fmtHunt(evh(row.dropChance, row.killsPerHr)), hellHr: w._fmtHunt(evh(row.hellDropChance, row.hellKillsPerHr)) } : null,
        text: txt(box),
      };
    });
    expect(r.card, 'the quick-win card must time the piece at all').toBeTruthy();
    expect(r.runHr, 'Sets run row: ' + r.run).toBe(r.card);
    expect(r.quickHr, 'quick win: ' + r.quick).toBe(r.card);
    expect(r.heroHr, 'hero: ' + r.hero).toBe(r.card);
    expect(r.quickOdds).toBe(r.odds);
    expect(r.heroOdds, 'the hero printed the RAW row once').toBe(r.odds);
    expect(r.bridge, 'the d2r_setFarm bridge the console ranks must carry the piece').toBeTruthy();
    expect(r.bridge.source).toBe(r.srcBoss);
    expect(r.bridge.hr, 'console /api/evrank hour').toBe(r.card);
    expect(r.quickHellHr, 'the Sets card names the Hell hour the Sessions tab leads with').toBe(r.bridge.hellHr);
    expect(r.heroHellHr).toBe(r.bridge.hellHr);
    expect('Hell ' + r.quickHell).toBe(r.bridge.hellSource);
    expect(r.text).not.toContain('~1 every');
    expect(r.text).not.toContain('Hell Hell');
  });

  test('★ every grail item: the forge names the SAME best run and Hell run the console hero ranks', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const E: any = (0, eval);
      try { E('_writeGrailFarm')(); } catch (e) {}
      let rows: any[] = [];
      try {
        const gf = JSON.parse(localStorage.getItem('d2r_grailFarm') || w.LSR.getItem('d2r_grailFarm') || 'null');
        rows = (gf && (gf.items || gf)) || [];
      } catch (e) {}
      const byName: any = {};
      w._allDropItems().forEach((x: any) => { byName[x.n] = x; });
      const bad: string[] = []; let checked = 0;
      (rows.filter ? rows : []).forEach((row: any) => {
        const it = byName[row.name]; if (!it) return;
        checked++;
        const p = w._pickSrc(it.sources, it.n);
        if (!p || p.s.boss !== row.source) bad.push(row.name + ': forge ' + (p && p.s.boss) + ' vs console ' + row.source);
        const hp = w._pickSrc((it.sources || []).filter((s: any) => s && String(s.diffKey || '').indexOf('hell') === 0), it.n);
        const want = (hp && hp.hours != null) ? hp.s.boss : null;
        if ((row.hellSource || null) !== want) bad.push(row.name + ': forge Hell ' + want + ' vs console Hell ' + row.hellSource);
      });
      const board = document.getElementById('funi-body');
      return { checked, bad: bad.slice(0, 12), nBad: bad.length, text: board ? (board.textContent || '') : '' };
    });
    expect(r.checked, 'grail rows the console ranks').toBeGreaterThan(100);
    expect(r.bad, r.nBad + ' item(s) named differently on the forge and the console').toEqual([]);
    expect(r.text).not.toContain('~1 every');
  });
});
