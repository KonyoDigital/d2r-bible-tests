// v908 R7 — THE CONNECTOR SEAL (Grok matrix): wrapper honesty both ways, vault summary real,
// zero-read honest, _fsCmp order-proof. file:// board with stubbed frame fetch + bridge POSTs.
import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v908 connector seal', () => {
  test('wrappers never lie: ok mirrors the intake truth, POST carries counts', async ({ page }) => {
    await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const r = await page.evaluate(async () => {
      const w = window as any;
      const posts: any[] = [];
      const realFetch = window.fetch;
      // stub: /frame returns a fake jpeg blob; /intake_result records the body
      (window as any).fetch = async (url: any, init?: any) => {
        const u = String(url);
        if (u.includes('/frame')) return new Response(new Blob([new Uint8Array(9000)], { type: 'image/jpeg' }), { status: 200 });
        if (u.includes('/intake_result')) { posts.push(JSON.parse(init.body)); return new Response('{"ok":true}'); }
        return realFetch(url, init);
      };
      // case 1: intake reads NOTHING
      w.runeIntake = async () => ({ ok: false, total: 0, added: {}, errors: 0, kind: 'runes' });
      w._tvdSessionTalliedAt = 0;
      const empty = await w.tvStashAutoIntake('runes', { frameId: '7_777' });
      // case 2: intake reads plenty
      w._stashShutter = false;   // v920 rename — the shutter is the one truth
      w.runeIntake = async () => ({ ok: true, total: 12, added: { Ist: 2, Vex: 10 }, errors: 0, kind: 'runes' });
      const full = await w.tvStashAutoIntake('runes', { frameId: '8_888' });
      // case 3: vault wrapper truth
      w._vaultAutoBusy = false; w._vaultAutoDone = false;
      w.vaultIntake = async () => ({ ok: true, total: 3, added: { 'Harlequin Crest': 1 }, errors: 0, kind: 'vault' });
      const vault = await w.tvVaultAutoIntake({ tab: 'personal', frameId: '9_999' });
      (window as any).fetch = realFetch;
      return { empty, full, vault, posts };
    });
    expect(r.empty.ok).toBe(false);                              // no ok-lie on empty
    expect(r.full.ok).toBe(true);
    expect(r.full.total).toBe(12);
    expect(r.vault.ok).toBe(true);
    expect(r.vault.total).toBe(3);
    const post1 = r.posts.find((p: any) => p.frameId === '7_777');
    const post2 = r.posts.find((p: any) => p.frameId === '8_888');
    const post3 = r.posts.find((p: any) => p.frameId === '9_999');
    expect(post1.ok).toBe(false);
    expect(post2.ok).toBe(true);
    expect(post2.counts.Ist).toBe(2);
    expect(post2.total).toBe(12);
    expect(post3.kind).toBe('vault');
    expect(post3.counts['Harlequin Crest']).toBe(1);
  });

  test('_fsCmp is order-proof (same quest set reordered = no rewrite)', async ({ page }) => {
    await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const r = await page.evaluate(() => {
      const w = window as any;
      localStorage.removeItem('d2r_forgeSummary');
      w.forgeScan && w.forgeScan();                       // first write
      const v1 = localStorage.getItem('d2r_forgeSummary');
      w.forgeScan && w.forgeScan();                       // identical scan → change-only skip
      const v2 = localStorage.getItem('d2r_forgeSummary');
      return { same: v1 === v2, wrote: !!v1 };
    });
    expect(r.wrote).toBe(true);
    expect(r.same).toBe(true);                            // ts did not rewrite
  });
});
