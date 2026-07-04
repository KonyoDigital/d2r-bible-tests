import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v569 — two live findings (2026-07-04 ~22:15):
//  A) "reading 0/5" WEDGE: Konyo deleted every screenshot while a 5-shot batch was queued — a File whose
//     backing file is gone can hang the <img> blob decode with neither onload nor onerror, so every worker
//     awaited a ghost forever and _vIntakeBusy stayed true (auto-watch dead until reload). Now: _vPreflight
//     (touch first bytes → deleted file rejects instantly) + _vTimed (30s ceiling on image decodes) →
//     the batch COMPLETES with per-file errors instead of wedging.
//  B) FULL RESET now also UNLINKS the watched folder (Konyo: "if I reset, how come it still shows linked?")
//     — handle forgotten (IndexedDB), poll stopped, UI back to 📂 Connect.

test('A — a batch of ghost files (deleted from disk) completes with errors instead of wedging at 0/N', async ({ page }) => {
  await page.route('**/api/intake', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], unrecognized: [], usage: { in: 1, out: 1 } }) }));
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate(async () => {
    const w: any = window;
    localStorage.setItem('d2r_intakeUrl', 'https://intake.test/api/intake');
    w.switchTab('tools'); w.renderVault && w.renderVault();
    // a File-like whose bytes are GONE — .slice().arrayBuffer() rejects like a deleted disk file
    const ghost = (n: string) => ({
      name: n, lastModified: Date.now(), type: 'image/png', size: 12345,
      slice(){ return { arrayBuffer(){ return Promise.reject(new DOMException('backing file gone', 'NotFoundError')); } }; },
      arrayBuffer(){ return Promise.reject(new DOMException('backing file gone', 'NotFoundError')); },
    });
    const t0 = Date.now();
    await w.vaultIntake([ghost('g1.png'), ghost('g2.png'), ghost('g3.png')], { fromFolder: true });
    return {
      ms: Date.now() - t0,
      busy: !!w._vIntakeBusy,                                     // MUST be cleared — the wedge symptom
      report: (document.getElementById('vault-intake-report')?.textContent || '').slice(0, 200),
    };
  });
  expect(r.busy).toBe(false);                 // no wedge: the busy flag cleared
  expect(r.ms).toBeLessThan(20000);           // failed FAST via preflight, not a 30s+ decode stall
  expect(r.report).toMatch(/Last scan|read/i);// the batch finished and reported
});

test('B — 🧹 full reset unlinks the watched folder: handle forgotten, UI back to Connect', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate(async () => {
    const w: any = window;
    w.switchTab('tools'); w.renderVault && w.renderVault();
    // simulate a linked folder: persist a marker handle + flip the UI to connected
    const rq = indexedDB.open('d2r_vault_fs');
    const db: any = await new Promise((res) => { rq.onsuccess = () => res(rq.result); rq.onupgradeneeded = () => rq.result.createObjectStore('kv'); });
    await new Promise((res) => { const tx = db.transaction('kv', 'readwrite'); tx.objectStore('kv').put({ fake: 'handle' }, 'shotdir'); tx.oncomplete = res; });
    w._setFolderConnectedUI(true);
    const beforeScanBtn = (document.getElementById('vault-scan-btn') as HTMLElement).style.display;
    w.uiConfirm = async () => true;           // auto-accept the reset confirm
    await w.vaultClearHistory();
    const g = db.transaction('kv', 'readonly').objectStore('kv').get('shotdir');
    const handleAfter = await new Promise((res) => { g.onsuccess = () => res(g.result); });
    return {
      beforeScanBtn,
      handleAfter: handleAfter === undefined ? 'GONE' : 'still-there',
      connectBtn: (document.getElementById('vault-folder-btn') as HTMLElement).style.display,
      scanBtn: (document.getElementById('vault-scan-btn') as HTMLElement).style.display,
      unlinkFn: typeof w._vUnlinkFolder,
    };
  });
  expect(r.unlinkFn).toBe('function');
  expect(r.beforeScanBtn).toBe('');            // was showing as connected
  expect(r.handleAfter).toBe('GONE');          // stored handle forgotten
  expect(r.connectBtn).toBe('');               // 📂 Connect is back
  expect(r.scanBtn).toBe('none');              // watcher/scan hidden
});
