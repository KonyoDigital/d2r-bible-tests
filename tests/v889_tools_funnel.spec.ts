// v889 — THE TOOLS FUNNEL (Grok pp1 A1-A3+A5): an AI-vaulted rune/gem/material tallies into
// the Tools stashes EXACTLY once (durable ledger), unvault decrements, junk never classifies.
import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v889 tools funnel', () => {
  test('vault +1 exactly once · unvault −1 · junk ignored', async ({ page }) => {
    await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const r = await page.evaluate(() => {
      const w = window as any;
      localStorage.removeItem('d2r_tvdTallyLog');
      w.clearGemStash && w.renderGemStash();
      const meta = { sid: 's_test_1', frameId: '9_123' };
      const before = (JSON.parse(localStorage.getItem('d2r_runeStash') || '{}')['Ist']) || 0;
      const a1 = w.tvToolsDelta('Ist Rune', 1, meta);          // vault
      const a2 = w.tvToolsDelta('Ist Rune', 1, meta);          // same frame re-read → dedupe
      const afterVault = (JSON.parse(localStorage.getItem('d2r_runeStash') || '{}')['Ist']) || 0;
      const a3 = w.tvToolsDelta('Ist Rune', -1, meta);         // unvault
      const afterUnvault = (JSON.parse(localStorage.getItem('d2r_runeStash') || '{}')['Ist']) || 0;
      const g1 = w.tvToolsDelta('Perfect Ruby', 1, { sid: 's_test_1', frameId: '10_456' });
      const gemN = (JSON.parse(localStorage.getItem('d2r_gemStash') || '{}')['Perfect Ruby']) || 0;
      const junk = w.tvToolsDelta('Harlequin Crest', 1, meta); // unique — NOT a tools tally
      // second frame vaults another Ist — a real second copy counts
      const b1 = w.tvToolsDelta('Ist Rune', 1, { sid: 's_test_1', frameId: '11_789' });
      const final = (JSON.parse(localStorage.getItem('d2r_runeStash') || '{}')['Ist']) || 0;
      return { before, a1, a2, afterVault, a3, afterUnvault, g1, gemN, junk, b1, final };
    });
    expect(r.a1).toBe(true);
    expect(r.a2).toBe(false);                          // deduped
    expect(r.afterVault).toBe(r.before + 1);           // exactly once
    expect(r.a3).toBe(true);
    expect(r.afterUnvault).toBe(r.before);             // unvault decrements
    expect(r.g1).toBe(true);
    expect(r.gemN).toBeGreaterThanOrEqual(1);
    expect(r.junk).toBe(false);                        // uniques belong to the grail, not tools
    expect(r.b1).toBe(true);                           // a genuinely new frame counts again
    expect(r.final).toBe(r.before + 1);
  });

  test('v909: per-key reconcile — vault +1 then photo ADD nets exactly once', async ({ page }) => {
    await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const r = await page.evaluate(async () => {
      const w = window as any;
      localStorage.removeItem('d2r_tvdTallyLog');
      w.clearRuneStash && (w.runeStash = {});
      const realFetch = window.fetch;
      (window as any).fetch = async (url: any, init?: any) => {
        const u = String(url);
        if (u.includes('/frame')) return new Response(new Blob([new Uint8Array(9000)], { type: 'image/jpeg' }), { status: 200 });
        if (u.includes('/intake_result')) return new Response('{"ok":true}');
        return realFetch(url, init);
      };
      // live funnel vaults an Ist (+1)
      w.tvToolsDelta('Ist Rune', 1, { sid: 's_g1', frameId: '1_1' });
      const mid = (JSON.parse(localStorage.getItem('d2r_runeStash') || '{}')['Ist']) || 0;
      // photo intake then reads the WHOLE stack (2 Ist total, incl. the one just vaulted)
      w.runeIntake = async () => { w.adjustRuneStash('Ist', 2); return { ok: true, total: 2, added: { Ist: 2 }, errors: 0, kind: 'runes' }; };
      w._stashIntakeBusy = false;
      const res = await w.tvStashAutoIntake('runes', { frameId: '2_2' });
      const fin = (JSON.parse(localStorage.getItem('d2r_runeStash') || '{}')['Ist']) || 0;
      (window as any).fetch = realFetch;
      return { mid, fin, ok: res && res.ok };
    });
    expect(r.mid).toBe(1);      // funnel counted it
    expect(r.ok).toBe(true);    // the shot RAN (no blunt defer)
    expect(r.fin).toBe(2);      // net truth: 2 Ist exist, not 3 — exact reconcile
  });
});
