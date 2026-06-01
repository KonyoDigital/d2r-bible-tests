import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v50 — lock the "What the P# slider actually does" methodology block AND the
// underlying playerMult breakpoints. /players scales drop QUANTITY (not quality)
// via (1 - q^k)/(1 - q), with the CANONICAL D2 drop factor k = 1 + floor(N/2)
// (== 1 + (players>>1)). That pairs (2,3)(4,5)(6,7) with /p1 and /p8 distinct.
// The earlier ceil(N/2) was an off-by-one (paired (1,2)(3,4)(5,6)(7,8)) that made
// /p5 == /p6 — the bug Konyo caught in-game. This spec guards the fix from
// regressing and keeps the explainer copy in sync with the engine.
test.describe('v50 P# slider explainer + breakpoint math', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.click('.tab[data-tab="ref"]');
    await page.waitForTimeout(150);
  });

  test('explainer documents the canonical k = 1 + floor(N/2), not ceil', async ({ page }) => {
    const t = await page.locator('#tab-ref').innerText();
    expect(t).toContain('What the P# slider actually does');
    expect(t).toContain('multiplier = (1 − qᵏ) / (1 − q)');
    expect(t).toContain('k = 1 + floor(N / 2)');
    expect(t).not.toContain('ceil(N / 2)'); // the old buggy formula must be gone
    expect(t).toMatch(/quantity/i);
    expect(t).toMatch(/never.*quality/i);
    // correct breakpoints: solo baseline, steps at even levels, paired with the odd above
    expect(t).toMatch(/\/p2, \/p4, \/p6, \/p8/);
    expect(t).toMatch(/\/p2=\/p3, \/p4=\/p5, \/p6=\/p7/);
    expect(t.toLowerCase()).not.toContain('undefined');
  });

  test('all 4 tiers present; @ /p8 multipliers match k=5; only Open Vault is P#-proof', async ({ page }) => {
    const rows = await page.evaluate(() =>
      [...document.querySelectorAll('#tab-ref table.drops tbody tr')]
        .map((tr) => [...tr.querySelectorAll('td')].map((td) => td.textContent!.trim())));
    expect(rows.length).toBe(4);
    const byTier = Object.fromEntries(rows.map((r) => [r[0], r]));
    const swarm = Object.keys(byTier).find((k) => /Swarm/.test(k))!;
    const hoarders = Object.keys(byTier).find((k) => /Hoarders/.test(k))!;
    const prime = Object.keys(byTier).find((k) => /Prime Evils/.test(k))!;
    const vault = Object.keys(byTier).find((k) => /Open Vault/.test(k))!;
    expect(swarm && hoarders && prime && vault).toBeTruthy();
    // k=5 @ /p8 values
    expect(byTier[swarm].at(-1)).toContain('×2.41');
    expect(byTier[hoarders].at(-1)).toMatch(/×1\.39.1\.5[23]/); // 1.39–1.52 (tolerate 1.53 display rounding)
    expect(byTier[prime].at(-1)).toContain('×1.22');
    // only the Open Vault is P#-proof
    expect(byTier[vault].at(-1)).toContain('P#-PROOF');
    expect(byTier[swarm].at(-1)).not.toContain('P#-PROOF');
    expect(byTier[prime].at(-1)).not.toContain('P#-PROOF');
    expect(byTier[vault]).toContain('0.0');
    expect(byTier[swarm]).toContain('0.625');
  });

  test('playerMult uses k=1+floor(N/2): @/p8 math + the (2,3)(4,5)(6,7) pairing', async ({ page }) => {
    const m = await page.evaluate(() => {
      const pm = (window as any).playerMult;
      const r2 = (id: string, p: number) => Math.round(pm(id, 'hell', p) * 100) / 100;
      const raw = (id: string, p: number) => pm(id, 'hell', p);
      return {
        // documented @/p8 multipliers (k=5)
        cows: r2('cows', 8), pit: r2('pit', 8),
        meph: r2('mephisto', 8), diablo: r2('diablo', 8), baal: r2('baal', 8),
        countess: r2('countess', 8), duriel: r2('duriel', 8), pindle: r2('pindle', 8),
        // breakpoint pairing on a q>0 boss
        p: Array.from({ length: 8 }, (_, i) => raw('cows', i + 1)),
      };
    });
    // @/p8 with k=5
    expect(m.cows).toBe(2.41);
    expect(m.pit).toBe(2.41);
    expect(m.meph).toBe(1.22);
    expect(m.diablo).toBe(1.22);
    expect(m.baal).toBe(1.22);
    // Open Vault guaranteed droppers stay ×1.00
    expect(m.countess).toBe(1);
    expect(m.duriel).toBe(1);
    expect(m.pindle).toBe(1);
    // canonical pairing: (2,3) (4,5) (6,7) equal; /p1 and /p8 distinct singletons.
    const [p1, p2, p3, p4, p5, p6, p7, p8] = m.p;
    expect(p2).toBe(p3);
    expect(p4).toBe(p5); // the fix: /p4 == /p5 (was /p5 == /p6 under ceil)
    expect(p6).toBe(p7);
    expect(p5).not.toBe(p6); // /p6 starts a new tier — the exact case from the screenshots
    expect(p1).toBeLessThan(p2);
    expect(p7).toBeLessThan(p8);
  });
});
