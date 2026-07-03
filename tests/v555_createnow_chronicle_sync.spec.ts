import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v555 — the AI-Helper "✨ what you can create now" (runeCraftStatus → dashboard, Top Picks, ask snapshot) now
// respects the Chronicle: a runeword you've ALREADY forged (rwMade) is no longer recommended, and ladder-only
// words are dropped off-ladder. So Enigma is recommended on a fresh profile (cousin) but drops once you tick it
// created (Konyo). Konyo: "it still recommends me Enigma even though I made it."

test('a fresh profile recommends Enigma; marking it created drops it', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_rwProfile', 'fresh');   // no owner seed
    localStorage.setItem('d2r_rwMade', '{}');
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Jah: 2, Ith: 2, Ber: 2 }));   // Enigma runes
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    const has = () => (w.runeCraftStatus().ready || []).map((x: any) => x.n || x.name).some((n: string) => /^Enigma/.test(n));
    const before = has();
    w.rwToggleMade('Enigma');            // forge it
    const after = has();
    return { before, after };
  });
  expect(r.before).toBe(true);           // fresh profile → Enigma is a recommendation
  expect(r.after).toBe(false);           // once created → no longer recommended
});

test('ticking the Chronicle LIVE-refreshes the create-now dashboard (no reload needed)', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_rwProfile', 'fresh');
    localStorage.setItem('d2r_rwMade', '{}');
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Jah: 2, Ith: 2, Ber: 2 }));
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const called = await page.evaluate(() => {
    const w: any = window;
    let hit = false;
    const orig = w.renderCreateNow;
    w.renderCreateNow = function () { hit = true; return orig && orig.apply(this, arguments); };
    w.rwToggleMade('Enigma');           // a Chronicle tick
    w.renderCreateNow = orig;
    return hit;
  });
  expect(called).toBe(true);   // rwToggleMade re-renders the create-now dashboard automatically
});

test('the ask snapshot completableNow also excludes an already-made runeword', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_rwProfile', 'fresh');
    localStorage.setItem('d2r_rwMade', JSON.stringify({ Enigma: 'x' }));   // already made
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Jah: 2, Ith: 2, Ber: 2 }));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const snap = (window as any).buildAskSnapshot();
    return (snap.runewords.completableNow || []).some((n: string) => /^Enigma/.test(n));
  });
  expect(r).toBe(false);   // a made runeword never appears in "what you can create now"
});

test('ticking a runeword the cached "Today\'s pick" names invalidates + re-asks it', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_rwProfile', 'fresh');
    localStorage.setItem('d2r_rwMade', '{}');
    localStorage.setItem('d2r_createNowAi', "Today's pick: Make Enigma (Jah + Ith + Ber) — best in the game.");
    localStorage.setItem('d2r_createNowAiDate', '2026-07-03');
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    let reasked = false;
    w.dailyCreateAi = function () { reasked = true; };   // stub to avoid a real API call
    w.rwToggleMade('Enigma');                            // make the very word the cached pick recommends
    return { dateCleared: localStorage.getItem('d2r_createNowAiDate') === null, reasked };
  });
  expect(r.dateCleared).toBe(true);   // stale daily cache invalidated
  expect(r.reasked).toBe(true);       // …and a fresh pick requested
});
