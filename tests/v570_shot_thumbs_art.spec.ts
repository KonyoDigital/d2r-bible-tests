import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v570 — two visual bugs from Konyo's live review (2026-07-04 22:23 screenshots):
//  A) "no shot" boxes: journal thumbnails were stripped from every session but the NEWEST, and the full-res
//     IndexedDB store was WIPED each scan — so the auto-watch's many small sessions (8 shots, then the late
//     9th on the next tick) left all earlier cards pictureless. Now: thumbs kept on the newest 6 sessions,
//     full-res pruned to the newest 100 instead of wiped.
//  B) "Colossus Voulge (Larzuk base)" rendered the corrupt blue-gem base_ placeholder ("like an Annihilus"):
//     artUrl now bypasses corrupt base_*.png by re-resolving the clean base name (elite→tier sprite).

const TINY_JPG = Buffer.from(
  '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==',
  'base64'
);

test('B — corrupt-base_ bypass: suffixed base labels resolve the clean name\'s HD art', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    // the live bug: the registered label carried the corrupt base_ art directly
    (w.D2IO_ART || {})['Colossus Voulge (Larzuk base)'] = 'art/base_colossusvoulge.png';
    return {
      suffixed: String(w.artUrl('Colossus Voulge (Larzuk base)')),
      clean: String(w.artUrl('Colossus Voulge')),
      unsuffixedMiss: String(w.artUrl('Colossus Voulge (4os)')),          // no direct entry → clean fallback
      legitBase: String(w.artUrl('Trident')),                              // clean-name direct resolution untouched
    };
  });
  expect(r.clean).toMatch(/hd_|_graphic|mr_/);          // the clean name has real art
  expect(r.suffixed).toBe(r.clean);                     // corrupt base_ bypassed → same real art
  expect(r.unsuffixedMiss).toBe(r.clean);               // suffixed miss falls back to the clean name
  expect(r.legitBase).toMatch(/^art\//);                 // clean names keep their own direct resolution
});

test('A — thumbnails survive on recent sessions (not just the newest) and full-res prunes instead of wiping', async ({ page }) => {
  await page.route('**/api/intake', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ items: ['The Stone of Jordan'], unrecognized: [], usage: { in: 1, out: 1 } }) }));
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate(async (jpgB64: string) => {
    const w: any = window;
    localStorage.setItem('d2r_intakeUrl', 'https://intake.test/api/intake');
    w.switchTab('tools'); w.renderVault && w.renderVault();
    const bytes = Uint8Array.from(atob(jpgB64), (c) => c.charCodeAt(0));   // a REAL decodable 1×1 JPEG → thumbnails generate
    const mk = (n: string) => new File([bytes], n, { type: 'image/jpeg', lastModified: Date.now() });
    await w.vaultIntake([mk('s1.png')], { fromFolder: true });   // session 1
    await w.vaultIntake([mk('s2.png')], { fromFolder: true });   // session 2 (newest)
    const j = JSON.parse(localStorage.getItem('d2r_intakeLog') || '[]');
    // prune keeps the newest N 'shot:' keys
    const rq = indexedDB.open('d2r_vault_fs');
    const db: any = await new Promise((res) => { rq.onsuccess = () => res(rq.result); });
    const put = (k: string) => new Promise((res) => { const tx = db.transaction('kv', 'readwrite'); tx.objectStore('kv').put('x', k); tx.oncomplete = res; });
    for (const k of ['shot:a.png', 'shot:b.png', 'shot:c.png', 'shot:d.png']) await put(k);
    await w._vPruneShots(2);
    const keys: string[] = await new Promise((res) => {
      const out: string[] = []; const cur = db.transaction('kv', 'readonly').objectStore('kv').openCursor();
      cur.onsuccess = () => { const c = cur.result; if (c) { if (String(c.key).startsWith('shot:')) out.push(String(c.key)); c.continue(); } else res(out); };
    });
    return {
      newestHasThumb: !!(j[0] && j[0].pf && j[0].pf[0] && j[0].pf[0].th),
      prevHasThumb: !!(j[1] && j[1].pf && j[1].pf[0] && j[1].pf[0].th),   // the v570 fix — was stripped before
      shotKeys: keys.sort(),
    };
  }, TINY_JPG.toString('base64'));
  expect(r.newestHasThumb).toBe(true);
  expect(r.prevHasThumb).toBe(true);                    // earlier session keeps its expandable shot
  // keys sort descending by name → the intake's own s1/s2 shots are newest; keep 2 = exactly those
  expect(r.shotKeys).toEqual(['shot:s1.png', 'shot:s2.png']);   // newest kept, a–d pruned
});
