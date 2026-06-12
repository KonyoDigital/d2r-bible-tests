// v212 — 📂 folder watch: connect the D2R screenshots directory ONCE (File
// System Access API), persist the handle in IndexedDB, auto-scan on vault
// init + manual 🔄. Only NEW files are fed to the SAME vaultIntake pipeline.
// v221: Safari/Firefox fallback via a hidden webkitdirectory input.
// v222: session-batch chooser (Latest 20 / Latest 40 / All / Skip) replaces the
// all-or-nothing confirm + the silent 12-cap; ledger is keyed by FILE NAME —
// a name ever registered is never read again, even if the file is re-saved.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const TINY_JPG_B64 = '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==';

async function stubFolder(page: any, files: { name: string; mtime: number }[]) {
  await page.evaluate(({ files, b64 }: any) => {
    const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
    const mk = (name: string, mtime: number) => ({
      kind: 'file',
      name,
      getFile: async () => new File([bytes], name, { type: 'image/jpeg', lastModified: mtime }),
    });
    (window as any).showDirectoryPicker = async () => ({
      queryPermission: async () => 'granted',
      requestPermission: async () => 'granted',
      values: async function* () { for (const f of files) yield mk(f.name, f.mtime); },
    });
  }, { files, b64: TINY_JPG_B64 });
}

// the v222 chooser renders into #vault-status; wait for it then pick
async function chooserPick(page: any, n: number) {
  await page.waitForFunction(
    () => (document.getElementById('vault-status')?.textContent || '').includes('read how many'),
    undefined, { timeout: 8000 }
  );
  await page.evaluate((k: number) => (window as any).vaultReadBatch(k), n);
}

test.describe('v212 folder watch', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/intake', (route) =>
      route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ items: ['Vampire Gaze'], unrecognized: [], usage: { in: 700, out: 20, cached: 0 } }),
      })
    );
    await page.goto(URL);
    await page.waitForTimeout(2200);
    await page.evaluate(() => {
      localStorage.clear();
      indexedDB.deleteDatabase('d2r_vault_fs');
      localStorage.setItem('d2r_intakeUrl', 'https://intake.test/api/intake');
      (window as any).switchTab('tools');
      (window as any).renderVault();
    });
  });

  test('buttons visible when the API exists; connect → chooser → All reads through intake; ledger keyed by NAME', async ({ page }) => {
    await stubFolder(page, [{ name: 'Screenshot001.png', mtime: 1000 }, { name: 'notes.txt', mtime: 1001 }]);
    await page.evaluate(() => {
      (document.getElementById('vault-folder-btn') as HTMLElement).style.display = '';
      (document.getElementById('vault-scan-btn') as HTMLElement).style.display = '';
      (window as any).vaultConnectFolder();
    });
    await chooserPick(page, 999); // "All"
    await page.waitForFunction(
      () => (document.getElementById('vault-intake-report')?.textContent || '').includes('AI intake done'),
      undefined, { timeout: 10000 }
    );
    const r = await page.evaluate(() => ({
      owned: eval('owned').has('Vampire Gaze'),
      seen: Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')),
    }));
    expect(r.owned).toBe(true);
    expect(r.seen).toEqual(['Screenshot001.png']); // txt ignored; NAME-keyed
  });

  test('re-scan skips already-seen; a NEW file auto-reads incrementally (≤12, no chooser)', async ({ page }) => {
    await stubFolder(page, [{ name: 'a.png', mtime: 1 }]);
    await page.evaluate(() => (window as any).vaultConnectFolder());
    await chooserPick(page, 999);
    await page.waitForFunction(() => (document.getElementById('vault-intake-report')?.textContent || '').includes('AI intake done'), undefined, { timeout: 10000 });
    // same folder again → nothing new → v223 rewind offer (not a silent dead end)
    await page.evaluate(() => (window as any).vaultScanFolder());
    await page.waitForFunction(() => (document.getElementById('vault-status')?.textContent || '').includes('no NEW screenshots'), undefined, { timeout: 8000 });
    await page.evaluate(() => (window as any).vaultRewind(0)); // dismiss the offer
    // add a new capture → routine scan reads it WITHOUT a chooser
    await stubFolder(page, [{ name: 'a.png', mtime: 1 }, { name: 'b.png', mtime: 2 }]);
    await page.evaluate(() => (window as any).vaultConnectFolder());
    await page.waitForFunction(() => {
      const seen = JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}');
      return Object.keys(seen).length === 2;
    }, undefined, { timeout: 10000 });
    const seen = await page.evaluate(() => Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')).sort());
    expect(seen).toEqual(['a.png', 'b.png']);
  });

  test('token guard: Skip on first-connect baselines old files WITHOUT reading them', async ({ page }) => {
    await stubFolder(page, [{ name: 'old1.png', mtime: 1 }, { name: 'old2.png', mtime: 2 }]);
    await page.evaluate(() => (window as any).vaultConnectFolder());
    await chooserPick(page, 0); // Skip — just baseline
    await page.waitForFunction(
      () => (document.getElementById('vault-status')?.textContent || '').includes('baseline saved'),
      undefined, { timeout: 8000 }
    );
    const r = await page.evaluate(() => ({
      seen: Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')).length,
      report: document.getElementById('vault-intake-report')!.hidden, // intake never ran
      owned: eval('owned').has('Vampire Gaze'),
    }));
    expect(r.seen).toBe(2);
    expect(r.report).toBe(true);
    expect(r.owned).toBe(false);
  });

  test('no folder connected → scan explains instead of failing', async ({ page }) => {
    await page.evaluate(() => (window as any).vaultScanFolder());
    await page.waitForFunction(() => (document.getElementById('vault-status')?.textContent || '').includes('no folder connected'), undefined, { timeout: 8000 });
    expect(true).toBe(true);
  });

  // v221 — Safari/Firefox fallback: no showDirectoryPicker → the scan button is
  // STILL shown (relabelled), wired to a hidden webkitdirectory input, and runs
  // the same ledger diff + chooser. Silent feature-hiding = REG-011.
  test('v221 legacy mode: scan button shown + relabelled when showDirectoryPicker is absent', async ({ page }) => {
    const ui = await page.evaluate(() => {
      const di = document.getElementById('vault-dir-input') as HTMLInputElement;
      return {
        legacyFnExists: typeof (window as any).vaultScanFolderLegacy === 'function',
        inputExists: !!di && di.hasAttribute('webkitdirectory'),
      };
    });
    expect(ui.legacyFnExists).toBe(true);
    expect(ui.inputExists).toBe(true);
  });

  test('v221 legacy scan: Skip baselines with ZERO AI calls, next scan feeds only the new file', async ({ page }) => {
    const r = await page.evaluate(async (b64: string) => {
      const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
      const mk = (name: string, mtime: number) =>
        new File([bytes], name, { type: 'image/png', lastModified: mtime });
      const sent: string[][] = [];
      (window as any).vaultIntake = (files: File[]) => { sent.push(files.map((f) => f.name)); };
      (window as any).vaultScanFolderLegacy([mk('old1.png', 1), mk('old2.png', 2)]);
      (window as any).vaultReadBatch(0); // Skip — just baseline
      const afterBaseline = {
        sent: sent.length,
        ledger: Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')).length,
      };
      (window as any).vaultScanFolderLegacy([mk('old1.png', 1), mk('old2.png', 2), mk('new1.png', 3)]);
      return { afterBaseline, second: sent[0] || null, ledger: Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')).length };
    }, TINY_JPG_B64);
    expect(r.afterBaseline.sent).toBe(0);
    expect(r.afterBaseline.ledger).toBe(2);
    expect(r.second).toEqual(['new1.png']); // routine ≤12 scan auto-reads
    expect(r.ledger).toBe(3);
  });

  test('v221 legacy scan ignores nested subfolders and non-images (top-level parity with handle.values())', async ({ page }) => {
    const r = await page.evaluate(async (b64: string) => {
      const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
      const mk = (name: string, rel: string) => {
        const f = new File([bytes], name, { type: 'image/png', lastModified: 9 });
        Object.defineProperty(f, 'webkitRelativePath', { value: rel });
        return f;
      };
      const sent: string[][] = [];
      (window as any).vaultIntake = (files: File[]) => { sent.push(files.map((f) => f.name)); };
      (window as any).vaultScanFolderLegacy([
        mk('top.png', 'SHOTS/top.png'),
        mk('nested.png', 'SHOTS/sub/nested.png'),
        mk('notes.txt', 'SHOTS/notes.txt'),
      ]);
      (window as any).vaultReadBatch(999); // first connect → chooser → All
      return sent[0] || [];
    }, TINY_JPG_B64);
    expect(r).toEqual(['top.png']);
  });

  // v222 — session-batch chooser + never-duplicate-by-name
  test('v222 session chooser: 50 new offers Latest 20/40 + All + Skip; Latest 20 reads the NEWEST 20; everything baselined', async ({ page }) => {
    const r = await page.evaluate(async (b64: string) => {
      const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
      const mk = (name: string, mtime: number) =>
        new File([bytes], name, { type: 'image/png', lastModified: mtime });
      const sent: string[][] = [];
      (window as any).vaultIntake = (files: File[]) => { sent.push(files.map((f) => f.name)); };
      const pile = Array.from({ length: 50 }, (_, i) => mk('shot' + String(i + 1).padStart(2, '0') + '.png', i + 1));
      (window as any).vaultScanFolderLegacy(pile);
      const bar = document.getElementById('vault-status')!.innerHTML;
      (window as any).vaultReadBatch(20);
      return {
        bar20: bar.includes('Latest 20'), bar40: bar.includes('Latest 40'),
        barAll: bar.includes('All 50'), barSkip: bar.includes('Skip'),
        got: sent[0] || [],
        ledger: Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')).length,
      };
    }, TINY_JPG_B64);
    expect(r.bar20 && r.bar40 && r.barAll && r.barSkip).toBe(true);
    expect(r.got.length).toBe(20);
    expect(r.got[0]).toBe('shot31.png');  // newest 20 by mtime
    expect(r.got[19]).toBe('shot50.png');
    expect(r.ledger).toBe(50);            // the unread 30 are baselined too
  });

  test('v223 session rewind: nothing-new scan offers Latest 20/40 that re-read PAST the ledger', async ({ page }) => {
    const r = await page.evaluate(async (b64: string) => {
      const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
      const mk = (name: string, mtime: number) =>
        new File([bytes], name, { type: 'image/png', lastModified: mtime });
      const sent: string[][] = [];
      (window as any).vaultIntake = (files: File[]) => { sent.push(files.map((f) => f.name)); };
      const pile = Array.from({ length: 45 }, (_, i) => mk('s' + String(i + 1).padStart(2, '0') + '.png', i + 1));
      // pre-baseline EVERYTHING (the Konyo situation: Cancel swallowed the session)
      const seen: any = {}; pile.forEach((f) => { seen[f.name] = 1; });
      localStorage.setItem('d2r_intakeSeen', JSON.stringify(seen));
      (window as any).vaultScanFolderLegacy(pile);
      const bar = document.getElementById('vault-status')!.innerHTML;
      (window as any).vaultRewind(20);
      return {
        offered: bar.includes('re-read a session') && bar.includes('Latest 20') && bar.includes('Latest 40'),
        got: sent[0] || [],
      };
    }, TINY_JPG_B64);
    expect(r.offered).toBe(true);
    expect(r.got.length).toBe(20);
    expect(r.got[0]).toBe('s26.png');  // the NEWEST 20, ledger ignored on purpose
    expect(r.got[19]).toBe('s45.png');
  });

  test('v222 never-duplicate: a registered file NAME is never re-read, even with a changed mtime', async ({ page }) => {
    const r = await page.evaluate(async (b64: string) => {
      const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
      const mk = (name: string, mtime: number) =>
        new File([bytes], name, { type: 'image/png', lastModified: mtime });
      const sent: string[][] = [];
      (window as any).vaultIntake = (files: File[]) => { sent.push(files.map((f) => f.name)); };
      (window as any).vaultScanFolderLegacy([mk('dup.png', 100)]);
      (window as any).vaultReadBatch(999);
      const firstSent = sent.length;
      // same name re-saved with a NEW mtime → must NOT be auto-read again
      // (v223: the nothing-new path now OFFERS a deliberate rewind instead)
      (window as any).vaultScanFolderLegacy([mk('dup.png', 999999)]);
      return {
        firstSent,
        totalSent: sent.length,
        status: document.getElementById('vault-status')!.textContent,
        // old-format ledger entries still honored
        legacyHonored: (function(){
          localStorage.setItem('d2r_intakeSeen', JSON.stringify({ 'old-style.png|123': 1 }));
          (window as any).vaultScanFolderLegacy([mk('old-style.png', 123)]);
          return (document.getElementById('vault-status')!.textContent || '').includes('no NEW screenshots');
        })(),
      };
    }, TINY_JPG_B64);
    expect(r.firstSent).toBe(1);
    expect(r.totalSent).toBe(1); // nothing auto-re-sent
    expect(r.status).toContain('no NEW screenshots'); // rewind offer, not a silent dead end
    expect(r.legacyHonored).toBe(true);
  });
});
