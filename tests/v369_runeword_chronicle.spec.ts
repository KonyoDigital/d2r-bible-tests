import { test, expect } from '@playwright/test';

// v369 — Chronicle: Runeword Maker. A Tools-tab section that tallies, per runeword:
//   • CAN MAKE NOW — synced live with the Rune Stash (canMakeNow against owned runes)
//   • ALREADY CREATED — a per-runeword toggle, persisted to d2r_rwMade (rides Backup & Share)
//   • LEFT TO MAKE — everything not yet created, with the exact missing runes.
// First run seeds Konyo's in-game Chronicle. v424: the seed is a DURABLE FLOOR of 30 created runewords.

const URL = 'file://' + process.cwd() + '/bible.html';

test('Chronicle seeds 75 created, lists all 100, syncs makeable, toggles persist', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.addInitScript(() => {
    // enough runes to make Radiance (Nef+Sol+Ith) now — an UN-seeded word for the "Can make now"
    // check (Leaf joined the seed in v581; King's Grace in v615 — pick from the truly-open tail).
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Nef: 1, Sol: 1, Ith: 1, Ort: 2, Tal: 1, Thul: 1, Amn: 1, Tir: 1, Ral: 1 }));
  });
  await page.goto(URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1400);
  await page.evaluate(() => (window as any).switchTab('tools'));
  // v372 — default filter is now "⏳ Left"; switch to "All 100" so this test can see every row incl. created.
  await page.evaluate(() => { const c = document.getElementById('rw-chronicle-card'); if (c) c.classList.remove('collapsed'); (window as any).rwcSetFilter('all'); });
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
      madeCount: Object.keys(made).length,
      rowCount: rows.length,
      prog: (document.getElementById('rwc-progress') || {}).textContent || '',
      spirit: find('Spirit'), zephyr: find('Zephyr'), leaf: find('Radiance'),
      beast: find('Beast'), death: find('Death'), faith: find('Faith'),
    };
  });

  expect(errs).toEqual([]);
  // seeded the 42-runeword durable floor (Konyo's actual created list, + Zephyr + Memory + Rift + Void as of v456-v463)
  expect(r.madeCount).toBe(75);   // v631.1 Jul 9 spree + Bulwark (Jul 10, ladder char)
  ['Beast', 'Chains of Honor', 'Death', 'Mosaic', 'Edge', 'Lore', 'Pride', 'Destruction', "Ancients' Pledge", 'Spirit', 'Grief', 'Stone', 'Enigma', 'Doom', 'Plague', 'Treachery', 'Zephyr', 'Memory', 'Rift', 'Void', 'Fury', 'Gloom'].forEach((n) =>
    expect(r.madeKeys).toContain(n));
  expect(r.rowCount).toBe(100);                 // all 100 runewords listed
  expect(r.prog).toContain('75 / 100');         // v631.1 spree + Bulwark
  expect(r.spirit?.made).toBe(true);            // now a seeded forged RW → reads Created
  expect(r.zephyr?.made).toBe(true);            // v456 — Zephyr is now a seeded floor RW → reads Created
  expect(r.leaf?.badge).toContain('Can make now');   // un-seeded, makeable (Nef+Sol+Ith) from the rune stash
  expect(r.beast?.made).toBe(true);             // a seeded one reads Created
  expect(r.death?.made).toBe(true);             // a newly-seeded (v420) one reads Created
  expect(r.faith?.badge).toContain('Missing');  // Ohm+Jah+Lem+Eld not owned, not seeded

  // toggling an UN-seeded runeword to created persists and bumps the count 75 → 76
  const after = await page.evaluate(() => {
    (window as any).rwToggleMade('Faith');
    const made = JSON.parse(localStorage.getItem('d2r_rwMade') || '{}');
    return { faith: !!made['Faith'], count: Object.keys(made).length };
  });
  expect(after.faith).toBe(true);
  expect(after.count).toBe(76);
});
