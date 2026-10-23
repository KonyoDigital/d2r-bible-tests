import { test } from '@playwright/test';
test('diag v3747 anni', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_ownerClaim', '*');
    Object.defineProperty(navigator, 'webdriver', { get: () => true });
    localStorage.setItem('d2r_owned', JSON.stringify(['The Stone of Jordan', 'Annihilus', 'Enigma', "Natalya's Totem", 'Nagelring']));
    localStorage.setItem('d2r_copies', '{}');
    localStorage.setItem('d2r_muleAssign', JSON.stringify({ 'The Stone of Jordan': 'uni-small', Annihilus: 'dead-mule-zzz', Enigma: 'runewords', "Natalya's Totem": 'sets-rest' }));
  });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any)._vaultRecordsHeader === 'function' && typeof (window as any).ownedPool === 'function');
  const out = await page.evaluate(() => {
    const w = window as any, o: any = {};
    const g = (k: string, f: () => any) => { try { o[k] = f(); } catch (e: any) { o[k] = 'THREW ' + e.message; } };
    g('pre_assign', () => JSON.parse(w.LSR.getItem('d2r_muleAssign') || 'null'));
    g('pending', () => w._rosterMapPending);
    g('held', () => w._vaultBasisHeld && w._vaultBasisHeld());
    g('provHeld', () => w._vaultProvHeld && w._vaultProvHeld());
    try { w.renderVault(); } catch (e) {}
    g('post_assign', () => JSON.parse(JSON.stringify(w._TAB_SYNC.d2r_muleAssign.get())));
    g('pending2', () => w._rosterMapPending);
    g('seam', () => w._vaultSeamHome ? w._vaultSeamHome('Annihilus') : 'no global');
    g('rec', () => (w._vaultRecords().records || []).find((r: any) => r && r.name === 'Annihilus'));
    g('sg', () => w.suggestMule ? w.suggestMule('Annihilus') : (typeof (window as any).suggestMule));
    g('roster', () => w._TAB_SYNC.d2r_muleRoster.get().map((m: any) => m.id));
    g('prov', () => w.LSR.getItem('d2r_vaultProv'));
    return o;
  });
  console.log('DIAG ' + JSON.stringify(out));
});
