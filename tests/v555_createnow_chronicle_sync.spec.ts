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
