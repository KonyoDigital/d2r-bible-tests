import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v50 — lock the "What the P# slider actually does" methodology block in the
// reference tab. /players scales drop QUANTITY (not quality) via
// (1 - q^k)/(1 - q), k = ceil(N/2). The block must make clear it moves 3 of 4
// boss tiers (Swarm / Hoarders / Prime Evils) and that only the q=0 Open Vault
// (Countess / Duriel / Pindleskin) is P#-proof.
test.describe('v50 P# slider explainer — reference-tab methodology block', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.click('.tab[data-tab="ref"]');
    await page.waitForTimeout(150);
  });

  test('header, formula, breakpoint caveat and quantity-not-quality framing all render', async ({ page }) => {
    const t = await page.locator('#tab-ref').innerText();
    expect(t).toContain('What the P# slider actually does');
    // formula + breakpoint key
    expect(t).toContain('multiplier = (1 − qᵏ) / (1 − q)');
    expect(t).toContain('k = ceil(N / 2)');
    // quantity, not quality
    expect(t).toMatch(/quantity/i);
    expect(t).toMatch(/never.*quality/i);
    // breakpoints (p1==p2, steps at p3/p5/p7)
    expect(t).toMatch(/\/p3, \/p5, \/p7/);
    expect(t.toLowerCase()).not.toContain('undefined');
  });

  test('all 4 tiers present with the correct multipliers; only Open Vault is P#-proof', async ({ page }) => {
    const rows = await page.evaluate(() => {
      const tbl = [...document.querySelectorAll('#tab-ref table.drops tbody tr')]
        .map((tr) => [...tr.querySelectorAll('td')].map((td) => td.textContent!.trim()));
      return tbl;
    });
    // 4 tier rows
    expect(rows.length).toBe(4);
    const byTier = Object.fromEntries(rows.map((r) => [r[0], r]));
    const swarm = Object.keys(byTier).find((k) => /Swarm/.test(k))!;
    const hoarders = Object.keys(byTier).find((k) => /Hoarders/.test(k))!;
    const prime = Object.keys(byTier).find((k) => /Prime Evils/.test(k))!;
    const vault = Object.keys(byTier).find((k) => /Open Vault/.test(k))!;
    expect(swarm && hoarders && prime && vault).toBeTruthy();
    // multipliers (last cell)
    expect(byTier[swarm].at(-1)).toContain('×2.26');
    expect(byTier[hoarders].at(-1)).toMatch(/×1\.38.1\.51/);
    expect(byTier[prime].at(-1)).toContain('×1.22');
    // only the Open Vault is P#-proof
    expect(byTier[vault].at(-1)).toContain('P#-PROOF');
    expect(byTier[swarm].at(-1)).not.toContain('P#-PROOF');
    expect(byTier[prime].at(-1)).not.toContain('P#-PROOF');
    // open-vault q=0, swarm q=0.625
    expect(byTier[vault]).toContain('0.0');
    expect(byTier[swarm]).toContain('0.625');
  });

  test('the explainer agrees with the live playerMult math it documents', async ({ page }) => {
    // sanity: the documented multipliers are what playerMult() actually returns @ /p8 hell
    const m = await page.evaluate(() => {
      const pm = (window as any).playerMult;
      const r = (id: string) => Math.round(pm(id, 'hell', 8) * 100) / 100;
      return {
        cows: r('cows'), pit: r('pit'),
        meph: r('mephisto'), diablo: r('diablo'), baal: r('baal'),
        countess: r('countess'), duriel: r('duriel'), pindle: r('pindle'),
      };
    });
    expect(m.cows).toBe(2.26);
    expect(m.pit).toBe(2.26);
    expect(m.meph).toBe(1.22);
    expect(m.diablo).toBe(1.22);
    expect(m.baal).toBe(1.22);
    // Open Vault — guaranteed droppers stay ×1.00
    expect(m.countess).toBe(1);
    expect(m.duriel).toBe(1);
    expect(m.pindle).toBe(1);
  });
});
