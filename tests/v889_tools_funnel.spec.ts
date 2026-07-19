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

  test('v909-R6: multi-vault debt nets −n · unvault nets to zero · debt survives reload', async ({ page }) => {
    await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const r1 = await page.evaluate(() => {
      const w = window as any;
      localStorage.removeItem('d2r_tvdTallyLog'); localStorage.removeItem('d2r_tvdKeyDebt');
      w.runeStash = {};
      // TWO Ist vaulted before any photo → debt n=2
      w.tvToolsDelta('Ist Rune', 1, { sid: 's_m1', frameId: '1_1' });
      w.tvToolsDelta('Ist Rune', 1, { sid: 's_m1', frameId: '2_2' });
      // one Vex vaulted then UNVAULTED → debt nets 0
      w.tvToolsDelta('Vex Rune', 1, { sid: 's_m1', frameId: '3_3' });
      w.tvToolsDelta('Vex Rune', -1, { sid: 's_m1', frameId: '3_3' });
      return JSON.parse(localStorage.getItem('d2r_tvdKeyDebt') || '{}');
    });
    expect((r1['rune:Ist'] || {}).n).toBe(2);
    expect(r1['rune:Vex']).toBeUndefined();               // unvault netted the debt away
    // RELOAD — the debt must survive (Grok b: the reload hole)
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const r2 = await page.evaluate(async () => {
      const w = window as any;
      const realFetch = window.fetch;
      (window as any).fetch = async (url: any, init?: any) => {
        const u = String(url);
        if (u.includes('/frame')) return new Response(new Blob([new Uint8Array(9000)], { type: 'image/jpeg' }), { status: 200 });
        if (u.includes('/intake_result')) return new Response('{"ok":true}');
        return realFetch(url, init);
      };
      w.runeIntake = async () => { w.adjustRuneStash('Ist', 3); return { ok: true, total: 3, added: { Ist: 3 }, errors: 0, kind: 'runes' }; };
      w._stashIntakeBusy = false;
      await w.tvStashAutoIntake('runes', { frameId: '4_4' });
      (window as any).fetch = realFetch;
      return { ist: (JSON.parse(localStorage.getItem('d2r_runeStash') || '{}')['Ist']) || 0,
               debt: JSON.parse(localStorage.getItem('d2r_tvdKeyDebt') || '{}') };
    });
    expect(r2.ist).toBe(3);           // v912 — SET truth: the photo saw 3, the stash IS 3
    expect(r2.debt['rune:Ist']).toBeUndefined();          // debt superseded by photo truth
  });

  test('v912: auto lane is SET — re-photo idempotent, unreported keys untouched, empty never zeroes', async ({ page }) => {
    await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const r = await page.evaluate(async () => {
      const w = window as any;
      localStorage.removeItem('d2r_tvdKeyDebt');
      const realFetch = window.fetch;
      (window as any).fetch = async (url: any, init?: any) => {
        const u = String(url);
        if (u.includes('/frame')) return new Response(new Blob([new Uint8Array(9000)], { type: 'image/jpeg' }), { status: 200 });
        if (u.includes('/intake_result')) return new Response('{"ok":true}');
        return realFetch(url, init);
      };
      // stash starts: 5 Ist (old manual tally) + 4 Vex (not in the next photo) — seeded
      // through the REAL adjust lane (module truth, not a window shadow)
      const cur = JSON.parse(localStorage.getItem('d2r_runeStash') || '{}');
      if (cur.Ist) w.adjustRuneStash('Ist', -cur.Ist);
      if (cur.Vex) w.adjustRuneStash('Vex', -cur.Vex);
      w.adjustRuneStash('Ist', 5); w.adjustRuneStash('Vex', 4);
      const shoot = async () => {
        w.runeIntake = async () => { w.adjustRuneStash('Ist', 3); return { ok: true, total: 3, added: { Ist: 3 }, errors: 0, kind: 'runes' }; };
        w._stashIntakeBusy = false;
        return w.tvStashAutoIntake('runes', { frameId: 'p_' + Math.floor(performance.now()) });
      };
      await shoot();
      const after1 = JSON.parse(localStorage.getItem('d2r_runeStash') || '{}');
      await shoot();   // RE-PHOTO of the same stack — the class debt could never fix
      const after2 = JSON.parse(localStorage.getItem('d2r_runeStash') || '{}');
      // empty shot must never zero anything
      w.runeIntake = async () => ({ ok: false, total: 0, added: {}, errors: 0, kind: 'runes' });
      w._stashIntakeBusy = false;
      await w.tvStashAutoIntake('runes', { frameId: 'p_empty' });
      const after3 = JSON.parse(localStorage.getItem('d2r_runeStash') || '{}');
      (window as any).fetch = realFetch;
      return { after1, after2, after3 };
    });
    expect(r.after1.Ist).toBe(3);      // SET: the photo is the truth (5 stale → 3 real)
    expect(r.after1.Vex).toBe(4);      // unreported key untouched
    expect(r.after2.Ist).toBe(3);      // RE-PHOTO idempotent — the re-ADD class is dead
    expect(r.after3.Ist).toBe(3);      // an empty shot zeroes NOTHING
    expect(r.after3.Vex).toBe(4);
  });
});
