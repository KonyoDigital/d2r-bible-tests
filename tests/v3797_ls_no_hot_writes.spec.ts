import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const BRIDGE = 'http://127.0.0.1:17771/state';

// v3797 — LAW: A LOOP OR POLL NEVER REWRITES localStorage WITH WHAT IS ALREADY THERE, AND NEVER
// FASTER THAN ONE WRITE PER KEY PER MIN_GAP_MS.
//
// Measured on Elad's Mac (2026-10-25, read-only): WebKit's LocalStorage localstorage.sqlite3-wal
// beside a 2.9 MB database had grown to ~19 GB at ~18 MB/min under the 3-day-old console. Cause,
// found on the box: the TV·D live poll (250 ms) lands each OCR read through pushHistRead(), which
// called ensureLiveSession() — a full saveHist() of d2r_tvdHist with NOTHING changed — and then a
// second full saveHist(). d2r_tvdHist carries the live session plus 12 archived sessions of up to
// 200 reads each, so every read rewrote the whole blob twice. Every rewrite of an unchanged or
// near-identical value is a fresh page set in the WAL.
//
// The law drives that exact path with a realistic history and a bridge that yields a new read on
// every poll, hooks Storage.prototype.setItem, and fails on (a) any write whose value equals the
// stored one, or (b) any key written more often than once per MIN_GAP_MS in steady state.
const MIN_GAP_MS = 2000;
const STEADY_MS = 12000;

function seedHist() {
  const read = (s: number, i: number) => ({ ts: s + i * 1000, n: i, area: 'Chaos Sanctuary', scene: 'loot',
    intent: 'seen', names: ['Shako', 'Ber Rune'], items: [{ kind: 'item', key: 'Shako', label: 'Shako' }],
    frameId: 'f' + s + '_' + i, note: 'x'.repeat(120) });
  const sess = (s: number) => ({ agentStart: s, startedAt: s, endedAt: s + 200000, reads: Array.from({ length: 200 }, (_, i) => read(s, i)) });
  return JSON.stringify({ live: null, sessions: Array.from({ length: 12 }, (_, k) => sess(1700000000000 + k * 1e7)) });
}

test('🧱 no loop or poll rewrites localStorage unchanged or faster than once per key per 2 s', async ({ page }) => {
  test.setTimeout(60000);
  const hist = seedHist();
  await page.addInitScript((h: string) => {
    try { if (!sessionStorage.getItem('__seeded')) { localStorage.setItem('d2r_tvdHist', h); sessionStorage.setItem('__seeded', '1'); } } catch (e) {}
    const orig = Storage.prototype.setItem;
    (window as any).__lsw = [];
    Storage.prototype.setItem = function (k: string, v: string) {
      let same = false; try { same = this.getItem(k) === String(v); } catch (e) {}
      (window as any).__lsw.push({ t: Date.now(), k: String(k), n: String(v).length, same });
      return orig.call(this, k, v);
    };
  }, hist);
  // Playwright matches the LAST-registered route first: the catch-all goes in before /state.
  await page.route('http://127.0.0.1:17771/**', (route) => route.abort());
  const start = Date.now(); let seq = 0;
  await page.route(BRIDGE + '**', (route) => {
    seq++;
    const ts = start + seq * 250;   // a brand-new read on EVERY poll — the worst honest case
    route.fulfill({ contentType: 'application/json', body: JSON.stringify({
      startedAt: start, reads: [{ ts, n: seq, area: 'Chaos Sanctuary', scene: 'loot', intent: 'seen',
        names: ['Shako'], frameId: 'live_' + seq }] }) });
  });
  await page.goto(URL); await page.waitForTimeout(400);
  await page.evaluate(() => (window as any).switchTab('tvd')); await page.waitForTimeout(200);
  await page.evaluate(() => (window as any)._tvdToggle());
  await page.waitForTimeout(3000);                      // boot + first-connect settle
  const t0 = await page.evaluate(() => Date.now());
  await page.waitForTimeout(STEADY_MS);
  const rows: { t: number; k: string; n: number; same: boolean }[] =
    await page.evaluate((t0: number) => (window as any).__lsw.filter((r: any) => r.t >= t0), t0);

  // PREMISE: the poll really ran, so "no hot writes" is not vacuous.
  expect(seq, 'bridge polls served').toBeGreaterThan(20);

  const unchanged = rows.filter(r => r.same).map(r => r.k);
  expect(unchanged, 'setItem with the value already stored').toEqual([]);
  // RATE: the minimum gap between two writes of one key, not a window count, so a burst can never hide.
  const per: Record<string, number[]> = {};
  for (const r of rows) (per[r.k] ||= []).push(r.t);
  const hot: string[] = [];
  for (const [k, ts] of Object.entries(per))
    for (let i = 1; i < ts.length; i++)
      if (ts[i] - ts[i - 1] < MIN_GAP_MS - 100) { hot.push(`${k} gap ${ts[i] - ts[i - 1]}ms`); break; }
  expect(hot, `keys written faster than once per ${MIN_GAP_MS} ms`).toEqual([]);
  // KEPT, NOT DROPPED: after the page flushes, every read the bridge served is in the live session.
  await page.evaluate(() => window.dispatchEvent(new Event('pagehide')));
  const got = await page.evaluate(() => { try { const L: any = (window as any).LSR && (window as any).LSR.getItem ? (window as any).LSR : localStorage;
    const h = JSON.parse(L.getItem('d2r_tvdHist') || '{}'); return (h.live && h.live.reads || []).map((r: any) => r.n); } catch (e) { return null; } });
  expect(got, 'live session readable').not.toBeNull();
  const served = seq;
  const missing = Array.from({ length: Math.min(served, 200) - 4 }, (_, i) => served - 4 - i).filter(n => n > 0 && !got!.includes(n));
  expect(missing, 'reads served by the bridge but not persisted (last 4 may still be in flight)').toEqual([]);
});
