// v203 — THE VAULT mule manager (Tools centerpiece). Roster of mule "lockers"
// (default = the 10-mule warehouse blueprint), taxonomy auto-assign over the
// ✓ Owned pool (ITEM_CODEX base/rarity/setName + ITEM_TIP b/t fallback),
// drag-and-drop + click-assign, manifests export, and a 🏦 location badge on
// the item detail card. Persists d2r_muleRoster/d2r_muleAssign (rides backup).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const OWNED = ['Harlequin Crest (Shako)', 'The Stone of Jordan', 'Vampire Gaze',
  'Annihilus', 'Stormshield', 'Raven Frost', 'Tal Rasha set (any piece)', 'Windforce'];

test.describe('v203 the vault', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2200);
    await page.evaluate((names) => {
      localStorage.removeItem('d2r_muleRoster');
      localStorage.removeItem('d2r_muleAssign');
      names.forEach((n: string) => eval('owned').add(n));
      (window as any).switchTab('tools');
      (window as any).renderVault();
    }, OWNED);
  });

  test('default roster renders 10 lockers; owned items appear as dock chips', async ({ page }) => {
    const r = await page.evaluate(() => ({
      mules: document.querySelectorAll('.vault-mule').length,
      chips: document.querySelectorAll('.vault-dock .vault-chip').length,
      names: [...document.querySelectorAll('.vm-name')].map(e => e.textContent),
    }));
    expect(r.mules).toBe(10);
    expect(r.chips).toBe(OWNED.length);
    expect(r.names).toContain('SETS-TAL-IK');
    expect(r.names).toContain('UNI-SMALL');
  });

  test('taxonomy: sets→set lockers, jewelry→small, helms/shields→armor, uber→mats', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sug = (n: string) => (window as any).vaultSuggest(n).id;
      return {
        tal: sug('Tal Rasha set (any piece)'), soj: sug('The Stone of Jordan'),
        gaze: sug('Vampire Gaze'), storm: sug('Stormshield'),
        anni: sug('Annihilus'), wf: sug('Windforce'),
      };
    });
    expect(r.tal).toBe('sets-major');
    expect(r.soj).toBe('uni-small');
    expect(r.gaze).toBe('uni-armor');
    expect(r.storm).toBe('uni-armor');
    expect(r.anni).toBe('mats');
    expect(r.wf).toBe('uni-weap');
  });

  test('auto-assign empties the dock, persists, and survives reload', async ({ page }) => {
    await page.evaluate(() => (window as any).vaultAutoAssign());
    const r1 = await page.evaluate(() => ({
      chips: document.querySelectorAll('.vault-dock .vault-chip').length,
      stored: JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}'),
    }));
    expect(r1.chips).toBe(0);
    expect(r1.stored['The Stone of Jordan']).toBe('uni-small');
    // persist owned BEFORE reloading — the vault prunes assignments of
    // un-owned items at load (eval('owned').add bypasses persistence)
    await page.evaluate(() => localStorage.setItem('d2r_owned', JSON.stringify([...eval('owned')])));
    await page.reload();
    await page.waitForTimeout(2200);
    const r2 = await page.evaluate(() => {
      (window as any).renderVault();
      const card = document.querySelector('[data-vault-mule="uni-small"]')!;
      return { count: card.querySelector('.vm-count')!.textContent };
    });
    expect(Number(r2.count)).toBeGreaterThanOrEqual(2); // SoJ + Raven Frost
  });

  test('click-assign (chip → locker) and unassign round-trip', async ({ page }) => {
    await page.evaluate(() => {
      const chip = [...document.querySelectorAll('.vault-chip')].find(c => (c as HTMLElement).dataset.vaultItem === 'Windforce') as HTMLElement;
      chip.click();
    });
    await page.evaluate(() => {
      (document.querySelector('[data-vault-mule="wip"] .vm-plate') as HTMLElement).click();
    });
    const r = await page.evaluate(() => JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}'));
    expect(r['Windforce']).toBe('wip');
    await page.evaluate(() => (window as any).vaultUnassign('Windforce'));
    const r2 = await page.evaluate(() => JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}'));
    expect(r2['Windforce']).toBeUndefined();
  });

  test('the 🏦 location badge renders on the item detail card and jumps to the vault', async ({ page }) => {
    await page.evaluate(() => {
      (window as any).vaultAssign('Harlequin Crest (Shako)', 'uni-armor');
      (window as any).openItemDetail('Harlequin Crest (Shako)');
    });
    const badge = await page.evaluate(() => document.querySelector('#item-detail-panel .vault-loc-badge')?.textContent || '');
    expect(badge).toContain('UNI-ARMOR');
    await page.evaluate(() => (document.querySelector('#item-detail-panel .vault-loc-badge') as HTMLElement).click());
    await page.waitForTimeout(500);
    const tab = await page.evaluate(() => (document.querySelector('.tabs .tab.active') as HTMLElement)?.dataset.tab);
    expect(tab).toBe('tools');
  });

  test('manifests export copies markdown; add/rename/delete mule round-trip', async ({ page }) => {
    const r = await page.evaluate(async () => {
      (window as any).vaultAutoAssign();
      let copied = '';
      (navigator.clipboard as any).writeText = (t: string) => { copied = t; return Promise.resolve(); };
      (window as any).vaultExport();
      await new Promise(res => setTimeout(res, 100));
      (window as any).prompt = () => 'TEST-MULE';
      (window as any).vaultAddMule();
      const added = [...document.querySelectorAll('.vm-name')].some(e => e.textContent === 'TEST-MULE');
      (window as any).confirm = () => true;
      const id = JSON.parse(localStorage.getItem('d2r_muleRoster')!).find((m: any) => m.name === 'TEST-MULE').id;
      (window as any).vaultDeleteMule(id);
      const gone = ![...document.querySelectorAll('.vm-name')].some(e => e.textContent === 'TEST-MULE');
      return { copied: copied.slice(0, 200), added, gone };
    });
    expect(r.copied).toContain('# The Vault — mule manifests');
    expect(r.copied).toContain('SETS-TAL-IK');
    expect(r.added).toBe(true);
    expect(r.gone).toBe(true);
  });

  test('no console errors through the full vault flow', async ({ page }) => {
    const errs: string[] = [];
    page.on('pageerror', e => errs.push(e.message));
    await page.evaluate(() => {
      (window as any).vaultAutoAssign();
      (window as any).renderVault();
      (window as any).openItemDetail('Stormshield');
    });
    await page.waitForTimeout(500);
    expect(errs).toEqual([]);
  });
});
