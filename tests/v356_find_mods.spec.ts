import { test, expect } from '@playwright/test';
import { seedIntake } from './_intake';

// v356 — magic/rare finds now carry the verbatim stat lines read off the screenshot tooltip, so a
// skiller shows its actual "+1 to <skill>" (read, not guessed) on the keeper card + hover.

const URL = 'file://' + process.cwd() + '/bible.html';
const TINY_JPG = Buffer.from('/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=', 'base64');

test('a magic find stores + renders its read stat lines (skiller +skills)', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('d2r_intakeUrl', 'https://intake.test/api/intake'));
  await page.route('**/api/intake', (route) => {
    const body = JSON.parse(route.request().postData() || '{}');
    if (body.kind === 'locate') return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ found: false, box: [0,0,0,0] }) });
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      items: [], unrecognized: [], usage: { in: 800, out: 30, cached: 0 },
      finds: [{ name: "Harpoönist's Grand Charm", q: 'magic', base: 'Grand Charm', mods: ['+1 to Javelin and Spear Skills', '+12 to Life'] }],
    }) });
  });
  await page.goto(URL); await page.waitForTimeout(1500);
  await page.evaluate(() => (window as any).switchTab('tools'));
  await seedIntake(page, 'vault', [{ name: 'skiller.jpg', mimeType: 'image/jpeg', buffer: TINY_JPG }]);
  await page.waitForFunction(() => (document.getElementById('vault-intake-report')?.textContent || '').includes('Last scan'), undefined, { timeout: 10000 });
  const r = await page.evaluate(() => {
    const w = window as any;
    const mf = eval('magicFinds')["Harpoönist's Grand Charm"];
    const tip = w._arttipResolve ? w._arttipResolve("Harpoönist's Grand Charm") : null;
    w.openDrop("Harpoönist's Grand Charm");
    const card = document.querySelector('#item-detail .magicfind-card')?.textContent || '';
    return { storedMods: mf && mf.mods, tipDesc: tip && tip.desc || '', card };
  });
  expect(r.storedMods).toContain('+1 to Javelin and Spear Skills');
  expect(r.tipDesc).toContain('Javelin and Spear');     // shown on hover
  expect(r.tipDesc).toContain('Skiller');                // still flagged
  expect(r.card).toContain('+1 to Javelin and Spear Skills');  // shown on the full card
  expect(r.card).toContain('read from your screenshot');
});
