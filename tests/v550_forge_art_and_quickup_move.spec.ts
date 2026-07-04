import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v550 — (A) every runeword & base name in the Forge cards gets an inline HD-art logo + a floating HD-art hover
// tooltip (data-arttip), so Konyo sees exactly what to hunt for in-game ("helps accuracy"). (B) the Quick-upload
// bar moves ABOVE the AI helper so it's the first thing on the Tools tab, right under the nav.

test('A — Forge pipeline base names carry an HD-art logo + hover tooltip (data-arttip)', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Flail (Heart of the Oak base)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ko: 17, Vex: 10, Pul: 18, Thul: 36 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v580.2 — pin fresh (Insight/Wind joined the seed)
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Flail (Heart of the Oak base)');
    w.switchTab('forge'); w.forgeSetFilter('pipeline'); w.renderForge();
    const box = document.getElementById('tab-forge')!;
    const artNames = [...box.querySelectorAll('.f-artname[data-arttip]')];
    // at least one names the Flail base, and carries an <img> logo
    const flail = artNames.find((e) => /Flail/.test(e.getAttribute('data-arttip') || ''));
    return {
      anyArtName: artNames.length > 0,
      flailHasTip: !!flail,
      flailHasImg: !!(flail && flail.querySelector('img')),
      titleHasImg: !!box.querySelector('.f-cardtitle img'),
    };
  });
  expect(r.anyArtName).toBe(true);
  expect(r.flailHasTip).toBe(true);
  expect(r.flailHasImg).toBe(true);
  expect(r.titleHasImg).toBe(true);
});

test('A — Make-now cards art-ify the owned base + the 🏆 best-base names', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 2, Tir: 2, Tal: 2, Sol: 2 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v580.2 — pin fresh (Insight/Wind joined the seed)
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Colossus Voulge (4os)');
    w.switchTab('forge'); w.forgeSetFilter('now'); w.renderForge();
    const box = document.getElementById('tab-forge')!;
    const tips = [...box.querySelectorAll('.f-artname[data-arttip]')].map((e) => e.getAttribute('data-arttip'));
    return { hasColossus: tips.some((t) => /Colossus Voulge/.test(t || '')), count: tips.length };
  });
  expect(r.hasColossus).toBe(true);
  expect(r.count).toBeGreaterThan(0);
});

test('B — the Quick-upload bar sits ABOVE the AI helper card in the Tools DOM', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w.switchTab('tools');
    const qu = document.getElementById('tools-quickup');
    const ai = document.getElementById('ask-bible-card');
    if (!qu || !ai) return { both: false, quBeforeAi: false };
    // DOCUMENT_POSITION_FOLLOWING (4) set on ai relative to qu means qu comes first
    const quBeforeAi = !!(qu.compareDocumentPosition(ai) & Node.DOCUMENT_POSITION_FOLLOWING);
    return { both: true, quBeforeAi };
  });
  expect(r.both).toBe(true);
  expect(r.quBeforeAi).toBe(true);
});
