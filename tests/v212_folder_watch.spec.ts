// v212 — 📂 folder watch: connect the D2R screenshots directory ONCE (File
// System Access API), persist the handle in IndexedDB, auto-scan on vault
// init + manual 🔄. Only NEW files (name|lastModified ledger in localStorage
// d2r_intakeSeen) are fed to the SAME vaultIntake pipeline. Buttons hidden
// where the API is unsupported. showDirectoryPicker is stubbed here.
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
      // v213: first-connect guard confirms before reading existing files —
      // default these tests to the read-all path; the skip path has its own test
      (window as any).confirm = () => true;
    });
  });

  test('buttons visible when the API exists; connect → scan reads new files through intake', async ({ page }) => {
    await stubFolder(page, [{ name: 'Screenshot001.png', mtime: 1000 }, { name: 'notes.txt', mtime: 1001 }]);
    await page.evaluate(() => {
      // re-init visibility now that the stub exists
      (document.getElementById('vault-folder-btn') as HTMLElement).style.display = '';
      (document.getElementById('vault-scan-btn') as HTMLElement).style.display = '';
      (window as any).vaultConnectFolder();
    });
    await page.waitForFunction(
      () => (document.getElementById('vault-intake-report')?.textContent || '').includes('AI intake done'),
      undefined, { timeout: 10000 }
    );
    const r = await page.evaluate(() => ({
      owned: eval('owned').has('Vampire Gaze'),
      seen: Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')),
    }));
    expect(r.owned).toBe(true);
    expect(r.seen).toEqual(['Screenshot001.png|1000']); // txt ignored
  });

  test('re-scan skips already-seen files; a NEW file is picked up incrementally', async ({ page }) => {
    await stubFolder(page, [{ name: 'a.png', mtime: 1 }]);
    await page.evaluate(() => (window as any).vaultConnectFolder());
    await page.waitForFunction(() => (document.getElementById('vault-intake-report')?.textContent || '').includes('AI intake done'), undefined, { timeout: 10000 });
    // same folder again → nothing new
    await page.evaluate(() => (window as any).vaultScanFolder());
    await page.waitForFunction(() => (document.getElementById('vault-status')?.textContent || '').includes('no new screenshots'), undefined, { timeout: 8000 });
    // add a new capture → only it is read
    await stubFolder(page, [{ name: 'a.png', mtime: 1 }, { name: 'b.png', mtime: 2 }]);
    await page.evaluate(() => (window as any).vaultConnectFolder());
    await page.waitForFunction(() => {
      const seen = JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}');
      return Object.keys(seen).length === 2;
    }, undefined, { timeout: 10000 });
    const seen = await page.evaluate(() => Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')).sort());
    expect(seen).toEqual(['a.png|1', 'b.png|2']);
  });

  test('v213 token guard: declining first-connect baselines old files WITHOUT reading them', async ({ page }) => {
    await stubFolder(page, [{ name: 'old1.png', mtime: 1 }, { name: 'old2.png', mtime: 2 }]);
    await page.evaluate(() => {
      (window as any).confirm = () => false; // "start fresh"
      (window as any).vaultConnectFolder();
    });
    await page.waitForFunction(
      () => (document.getElementById('vault-status')?.textContent || '').includes('old screenshots skipped'),
      undefined, { timeout: 8000 }
    );
    const r = await page.evaluate(() => ({
      seen: Object.keys(JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}')).length,
      report: document.getElementById('vault-intake-report')!.hidden, // intake never ran
      owned: eval('owned').has('Vampire Gaze'),
    }));
    expect(r.seen).toBe(2);        // baselined as seen
    expect(r.report).toBe(true);   // no AI reading happened
    expect(r.owned).toBe(false);
  });

  test('no folder connected → scan explains instead of failing', async ({ page }) => {
    await page.evaluate(() => (window as any).vaultScanFolder());
    await page.waitForFunction(() => (document.getElementById('vault-status')?.textContent || '').includes('no folder connected'), undefined, { timeout: 8000 });
    expect(true).toBe(true);
  });
});
