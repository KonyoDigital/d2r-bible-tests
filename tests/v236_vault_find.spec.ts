import { test, expect } from '@playwright/test';

// v236 — vault item finder. A search box in the vault: type an item name → which
// alt (mule) holds it. Searches everything ✓ owned; a hit shows the item + its
// mule (or "unsorted"), and clicking opens that mule's ID card.

const URL = 'file://' + process.cwd() + '/bible.html';

test.describe('v236 vault finder', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      // v681 — fresh profile skips the v677 grail floor + owner cleanse, so an explicitly-seeded
      // owned-but-unassigned grail item (Stormshield) survives the reload instead of being stripped
      // to the ledger. That's exactly what this finder test needs an "unsorted" item for.
      localStorage.setItem('d2r_rwProfile', 'fresh');
      localStorage.setItem('d2r_owned', JSON.stringify(['Windforce', 'Vampire Gaze', 'Stormshield']));
      localStorage.setItem('d2r_muleAssign', JSON.stringify({ Windforce: 'uni-weap', 'Vampire Gaze': 'uni-armor' }));
    });
    await page.setViewportSize({ width: 1500, height: 950 });
    await page.goto(URL);
    await page.waitForTimeout(1300);
    await page.evaluate(() => (window as any).switchTab('tools'));
  });

  test('the finder box + clear button exist in the vault', async ({ page }) => {
    const r = await page.evaluate(() => ({
      input: !!document.getElementById('vault-find-input'),
      results: !!document.getElementById('vault-find-results'),
      fn: typeof (window as any).vaultFind,
    }));
    expect(r.input).toBe(true);
    expect(r.results).toBe(true);
    expect(r.fn).toBe('function');
  });

  test('typing a name finds the item + names its mule; click opens that mule card', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).vaultFind('wind');
      const row = document.querySelector('#vault-find-results .vfr-row');
      const out = {
        rows: document.querySelectorAll('#vault-find-results .vfr-row').length,
        name: row?.querySelector('.vfr-name')?.textContent,
        mule: row?.querySelector('.vfr-mule')?.textContent,
      };
      (document.querySelector('#vault-find-results .vfr-row') as HTMLElement)?.click();
      return {
        ...out,
        cardOpen: !document.getElementById('vault-detail')?.hidden,
        cardName: document.querySelector('#vault-detail .vd-name')?.textContent,
      };
    });
    expect(r.rows).toBe(1);
    expect(r.name).toBe('Windforce');
    expect(r.mule).toContain('UNI-WEAPONS');
    expect(r.cardOpen).toBe(true);
    expect(r.cardName).toContain('UNI-WEAPONS');
  });

  test('an owned-but-unassigned item shows as "unsorted"; no match shows an empty note', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).vaultFind('stormshield');
      const loc = document.querySelector('#vault-find-results .vfr-row .vfr-loc')?.textContent || '';
      (window as any).vaultFind('zzzznope');
      const empty = (document.querySelector('#vault-find-results .vfr-empty')?.textContent || '').toLowerCase();
      (window as any).vaultFind('');
      const hiddenOnClear = document.getElementById('vault-find-results')?.hidden;
      return { loc, empty, hiddenOnClear };
    });
    expect(r.loc.toLowerCase()).toContain('unsorted');
    expect(r.empty).toContain('no vaulted item');
    expect(r.hiddenOnClear).toBe(true);
  });
});
