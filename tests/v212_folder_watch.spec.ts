// v212 — 📂 folder watch: connect the D2R screenshots directory ONCE (File
// System Access API), persist the handle in IndexedDB, auto-scan on vault
// init + manual 🔄. Only NEW files are fed to the SAME vaultIntake pipeline.
// v221: Safari/Firefox fallback via a hidden webkitdirectory input.
// v222: ledger keyed by FILE NAME — a name ever registered is never auto-read
// again, even if the file is re-saved with a new mtime.
// v224: ONE full-width scan menu in #vault-intake-report on EVERY manual scan
// (✨ New X · 🕐 Latest 20 · 🕐 Latest 40 · Skip); Latest N deliberately reads
// PAST the ledger (session recovery). Quiet auto-scans still read ≤12 new.
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

// the v224 menu renders full-width in #vault-intake-report; wait then pick
async function menuPick(page: any, k: number | string) {
  await page.waitForFunction(
    () => (document.getElementById('vault-intake-report')?.textContent || '').includes('read which'),
    undefined, { timeout: 8000 }
  );
  await page.evaluate((kk: any) => (window as any).vaultReadBatch(kk), k);
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

  test('connect → menu → ✨New reads through intake; ledger keyed by NAME; txt ignored', async ({ page }) => {
    await stubFolder(page, [{ name: 'Screenshot001.png', mtime: 1000 }, { name: 'notes.txt', mtime: 1001 }]);
    await page.evaluate(() => (window as any).vaultConnectFolder());
    await menuPick(page, 'new');
    await page.waitForFunction(
      () => (document.getElementById('vault-intake-report')?.textContent || '').includes('Last scan'),
      undefined, { timeout: 10000 }
    );
    const r = await page.evaluate(() => ({
      owned: eval('owned').has('Vampire Gaze'),
      seen: Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')).filter((k) => !k.includes('|')),
    }));
    expect(r.owned).toBe(true);
    expect(r.seen).toEqual(['Screenshot001.png']);
  });

  test('re-scan shows 0 new (registered names skipped); a NEW file appears in the next menu', async ({ page }) => {
    await stubFolder(page, [{ name: 'a.png', mtime: 1 }]);
    await page.evaluate(() => (window as any).vaultConnectFolder());
    await menuPick(page, 'new');
    await page.waitForFunction(() => (document.getElementById('vault-intake-report')?.textContent || '').includes('Last scan'), undefined, { timeout: 10000 });
    // same folder again → menu reports 0 new
    await page.evaluate(() => (window as any).vaultScanFolder());
    await page.waitForFunction(() => (document.getElementById('vault-intake-report')?.textContent || '').includes('0 new'), undefined, { timeout: 8000 });
    await page.evaluate(() => (window as any).vaultReadBatch(0)); // dismiss
    // add a new capture → menu offers exactly it
    await stubFolder(page, [{ name: 'a.png', mtime: 1 }, { name: 'b.png', mtime: 2 }]);
    await page.evaluate(() => (window as any).vaultConnectFolder());
    await menuPick(page, 'new');
    await page.waitForFunction(() => {
      const seen = JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}');
      return Object.keys(seen).filter((k) => !k.includes('|')).length === 2;
    }, undefined, { timeout: 10000 });
    const seen = await page.evaluate(() => Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')).filter((k) => !k.includes('|')).sort());
    expect(seen).toEqual(['a.png', 'b.png']);
  });

  test('token guard: Skip registers old files WITHOUT reading them and re-hides the report row', async ({ page }) => {
    await stubFolder(page, [{ name: 'old1.png', mtime: 1 }, { name: 'old2.png', mtime: 2 }]);
    await page.evaluate(() => (window as any).vaultConnectFolder());
    await menuPick(page, 0); // Skip — just register
    await page.waitForFunction(
      () => (document.getElementById('vault-status')?.textContent || '').includes('registered'),
      undefined, { timeout: 8000 }
    );
    const r = await page.evaluate(() => ({
      seen: Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')).filter((k) => !k.includes('|')).length,
      reportHidden: document.getElementById('vault-intake-report')!.hidden,
      owned: eval('owned').has('Vampire Gaze'),
    }));
    expect(r.seen).toBe(2);
    expect(r.reportHidden).toBe(true); // no intake ran, row tucked away again
    expect(r.owned).toBe(false);
  });

  test('no folder connected → scan explains instead of failing', async ({ page }) => {
    await page.evaluate(() => (window as any).vaultScanFolder());
    await page.waitForFunction(() => (document.getElementById('vault-status')?.textContent || '').includes('no folder connected'), undefined, { timeout: 8000 });
    expect(true).toBe(true);
  });

  test('v221 legacy mode: webkitdirectory input + legacy scan fn exist for Safari/Firefox', async ({ page }) => {
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

  test('v221 legacy scan: Skip registers with ZERO AI calls; the next menu offers only the new file', async ({ page }) => {
    const r = await page.evaluate(async (b64: string) => {
      const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
      const mk = (name: string, mtime: number) =>
        new File([bytes], name, { type: 'image/png', lastModified: mtime });
      const sent: string[][] = [];
      (window as any).vaultIntake = (files: File[]) => { sent.push(files.map((f) => f.name)); };
      (window as any).vaultScanFolderLegacy([mk('old1.png', 1), mk('old2.png', 2)]);
      (window as any).vaultReadBatch(0); // Skip — just register
      const afterBaseline = {
        sent: sent.length,
        ledger: Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')).filter((k) => !k.includes('|')).length,
      };
      (window as any).vaultScanFolderLegacy([mk('old1.png', 1), mk('old2.png', 2), mk('new1.png', 3)]);
      const menu = document.getElementById('vault-intake-report')!.textContent || '';
      (window as any).vaultReadBatch('new');
      return { afterBaseline, menuHasOneNew: menu.includes('1 new'), second: sent[0] || null, ledger: Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')).filter((k) => !k.includes('|')).length };
    }, TINY_JPG_B64);
    expect(r.afterBaseline.sent).toBe(0);
    expect(r.afterBaseline.ledger).toBe(2);
    expect(r.menuHasOneNew).toBe(true);
    expect(r.second).toEqual(['new1.png']);
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
      (window as any).vaultReadBatch('new');
      return sent[0] || [];
    }, TINY_JPG_B64);
    expect(r).toEqual(['top.png']);
  });

  test('v224 session menu: 50 new offers ✨New 50 + 🕐Latest 20/40 + Skip; Latest 20 reads the NEWEST 20; everything registered', async ({ page }) => {
    const r = await page.evaluate(async (b64: string) => {
      const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
      const mk = (name: string, mtime: number) =>
        new File([bytes], name, { type: 'image/png', lastModified: mtime });
      const sent: string[][] = [];
      (window as any).vaultIntake = (files: File[]) => { sent.push(files.map((f) => f.name)); };
      const pile = Array.from({ length: 50 }, (_, i) => mk('shot' + String(i + 1).padStart(2, '0') + '.png', i + 1));
      (window as any).vaultScanFolderLegacy(pile);
      const rep = document.getElementById('vault-intake-report')!;
      const bar = rep.innerHTML;
      (window as any).vaultReadBatch(20);
      return {
        visible: !rep.hidden,
        barNew: bar.includes('New 50'), bar20: bar.includes('Latest 20'),
        bar40: bar.includes('Latest 40'), barSkip: bar.includes('Skip'),
        got: sent[0] || [],
        ledger: Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')).filter((k) => !k.includes('|')).length,
      };
    }, TINY_JPG_B64);
    expect(r.visible).toBe(true); // full-width report row, not the cramped toolbar span
    expect(r.barNew && r.bar20 && r.bar40 && r.barSkip).toBe(true);
    expect(r.got.length).toBe(20);
    expect(r.got[0]).toBe('shot31.png');
    expect(r.got[19]).toBe('shot50.png');
    expect(r.ledger).toBe(50); // the unread 30 are registered too
  });

  test('v224 session recovery: all-registered folder still offers 🕐Latest 20/40 that read PAST the ledger', async ({ page }) => {
    const r = await page.evaluate(async (b64: string) => {
      const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
      const mk = (name: string, mtime: number) =>
        new File([bytes], name, { type: 'image/png', lastModified: mtime });
      const sent: string[][] = [];
      (window as any).vaultIntake = (files: File[]) => { sent.push(files.map((f) => f.name)); };
      const pile = Array.from({ length: 45 }, (_, i) => mk('s' + String(i + 1).padStart(2, '0') + '.png', i + 1));
      // the Konyo situation: an earlier baseline swallowed the whole session
      const seen: any = {}; pile.forEach((f) => { seen[f.name] = 1; });
      localStorage.setItem('d2r_intakeSeen', JSON.stringify(seen));
      (window as any).vaultScanFolderLegacy(pile);
      const bar = document.getElementById('vault-intake-report')!.innerHTML;
      (window as any).vaultReadBatch(20);
      return {
        offered: bar.includes('0 new') && bar.includes('Latest 20') && bar.includes('Latest 40'),
        noNewBtn: !bar.includes('New 0'),
        got: sent[0] || [],
      };
    }, TINY_JPG_B64);
    expect(r.offered).toBe(true);
    expect(r.noNewBtn).toBe(true);
    expect(r.got.length).toBe(20);
    expect(r.got[0]).toBe('s26.png');  // the NEWEST 20, ledger deliberately ignored
    expect(r.got[19]).toBe('s45.png');
  });

  test('v222 never-duplicate: a registered file NAME never shows as new again, even with a changed mtime', async ({ page }) => {
    const r = await page.evaluate(async (b64: string) => {
      const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
      const mk = (name: string, mtime: number) =>
        new File([bytes], name, { type: 'image/png', lastModified: mtime });
      const sent: string[][] = [];
      (window as any).vaultIntake = (files: File[]) => { sent.push(files.map((f) => f.name)); };
      (window as any).vaultScanFolderLegacy([mk('dup.png', 100)]);
      (window as any).vaultReadBatch('new');
      const firstSent = sent.length;
      // same name re-saved with a NEW mtime → must NOT count as new
      (window as any).vaultScanFolderLegacy([mk('dup.png', 999999)]);
      const menu = document.getElementById('vault-intake-report')!.textContent || '';
      (window as any).vaultReadBatch(0);
      // old-format name|mtime ledger entries still honored
      localStorage.setItem('d2r_intakeSeen', JSON.stringify({ 'old-style.png|123': 1 }));
      (window as any).vaultScanFolderLegacy([mk('old-style.png', 123)]);
      const menu2 = document.getElementById('vault-intake-report')!.textContent || '';
      (window as any).vaultReadBatch(0);
      return { firstSent, totalSent: sent.length, menuZero: menu.includes('0 new'), legacyHonored: menu2.includes('0 new') };
    }, TINY_JPG_B64);
    expect(r.firstSent).toBe(1);
    expect(r.totalSent).toBe(1); // nothing auto-re-sent, ever
    expect(r.menuZero).toBe(true);
    expect(r.legacyHonored).toBe(true);
  });
});
