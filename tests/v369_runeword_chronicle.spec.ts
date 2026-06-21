import { test, expect } from '@playwright/test';

// v369 — Chronicle: Runeword Maker. A Tools-tab section that tallies, per runeword:
//   • CAN MAKE NOW — synced live with the Rune Stash (canMakeNow against owned runes)
//   • ALREADY CREATED — a per-runeword toggle, persisted to d2r_rwMade (rides Backup & Share)
//   • LEFT TO MAKE — everything not yet created, with the exact missing runes.
// First run seeds Konyo's in-game Chronicle (7/100 created).

const URL = 'file://' + process.cwd() + '/bible.html';

test('Chronicle seeds 7 created, lists all 100, syncs makeable, toggles persist', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.addInitScript(() => {
    // enough runes to make Lore (Ort+Sol) + Spirit (Tal+Thul+Ort+Amn) now; leave d2r_rwMade unset → seeds
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ort: 2, Sol: 1, Tal: 1, Thul: 1, Amn: 1 }));
  });
  await page.goto(URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1400);
  await page.evaluate(() => (window as any).switchTab('tools'));
  await page.evaluate(() => { const c = document.getElementById('rw-chronicle-card'); if (c) c.classList.remove('collapsed'); (window as any).renderRunewordChronicle(); });
  await page.waitForTimeout(300);

  const r = await page.evaluate(() => {
    const made = JSON.parse(localStorage.getItem('d2r_rwMade') || '{}');
    const rows = Array.from(document.querySelectorAll('#rwc-list .rwc-row'));
    const find = (n: string) => {
      const el = rows.find((r) => (r.querySelector('.rwc-name')?.textContent || '') === n);
      return el ? { badge: el.querySelector('.rwc-badge')?.textContent || '', made: el.classList.contains('rwc-made') } : null;
    };
    return {
      madeKeys: Object.keys(made).sort(),
      rowCount: rows.length,
      prog: (document.getElementById('rwc-progress') || {}).textContent || '',
      lore: find('Lore'), spirit: find('Spirit'),
      beast: find('Beast'), enigma: find('Enigma'),
    };
  });

  expect(errs).toEqual([]);
  // seeded exactly the 7 in-game-created runewords
  expect(r.madeKeys).toEqual(['Beast', 'Chains of Honor', 'Dream', 'Duress', 'Fortitude', 'Infinity', 'Rhyme']);
  expect(r.rowCount).toBe(100);                 // all 100 runewords listed
  expect(r.prog).toContain('7 / 100');          // 7% created, matches the Chronicle
  expect(r.lore?.badge).toContain('Can make now');   // synced with the rune stash
  expect(r.spirit?.badge).toContain('Can make now');
  expect(r.beast?.made).toBe(true);             // a seeded one reads Created
  expect(r.enigma?.badge).toContain('Missing'); // Jah+Ith+Ber not owned

  // toggling "made" persists and updates the count
  const after = await page.evaluate(() => {
    (window as any).rwToggleMade('Steel');
    const made = JSON.parse(localStorage.getItem('d2r_rwMade') || '{}');
    return { steel: !!made['Steel'], count: Object.keys(made).length };
  });
  expect(after.steel).toBe(true);
  expect(after.count).toBe(8);
});
