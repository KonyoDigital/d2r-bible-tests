import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v660 — "✓ got the base" ascension (Konyo: 'lets say i did get a runeword base… clicking i have the
// base with a checkmark style and then it automatically ascends to MAKE NOW'). A one-step get-a-base
// card carries a ✓ button that registers the recommended base at the word's exact socket count
// (owned + EXTRA_ITEMS socketed entry — the same registry the AI intake writes) and the word jumps
// straight to ⚒ Make now in the same forge view.

test('one-step base card shows ✓ got the base; clicking registers the base and the word ascends to Make now', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_rwProfile', 'fresh');           // clean chronicle — the word must be unmade
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_owned', JSON.stringify([]));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ort: 1, Sol: 1 }));   // Lore = Ort+Sol, 2os helm
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const s0 = w.forgeScan();
    const t = (s0.onestep || []).find((x: any) => x.rw === 'Lore' && x.sub === 'base');
    if (!t) return { taskFound: false };
    // the card renders the button
    w.switchTab('forge'); try { w.renderForge && w.renderForge(); } catch (e) {}
    const btn = Array.from(document.querySelectorAll('#tab-forge .f-btn'))
      .find((b) => (b.textContent || '').includes('got the base'));
    const base = String(t.bestStr || '').split(/\s*\/\s*/)[0].trim();
    const need = ((w.RUNEWORD_TIP || {})['Lore'] || {}).rec.length;
    w.forgeGotBase(null, 'Lore', base, need);
    const s1 = w.forgeScan();
    const now = (s1.now || []).find((x: any) => x.rw === 'Lore' && !x.deferred);
    return {
      taskFound: true, btnRendered: !!btn, base, need,
      ascended: !!now, nowBase: now && now.base && now.base.name,
      ownedHasLabel: JSON.parse(w.LSR.getItem('d2r_owned') || '[]').includes(base + ' (' + need + 'os)'),
    };
  });
  expect(r.taskFound).toBe(true);
  expect(r.btnRendered).toBe(true);
  expect(r.ascended).toBe(true);                       // 🟡 one step → ⚒ Make now, one click
  expect(r.ownedHasLabel).toBe(true);                  // registered exactly like an intake read
  expect(r.nowBase).toBe(r.base + ' (' + r.need + 'os)');
});
