import { test, expect } from '@playwright/test';

// v369 — Chronicle: Runeword Maker. A Tools-tab section that tallies, per runeword:
//   • CAN MAKE NOW — synced live with the Rune Stash (canMakeNow against owned runes)
//   • ALREADY CREATED — a per-runeword toggle, persisted to d2r_rwMade (rides Backup & Share)
//   • LEFT TO MAKE — everything not yet created, with the exact missing runes.
// First run seeds Konyo's in-game Chronicle. v424: the seed is a DURABLE FLOOR of 30 created runewords.

const URL = 'file://' + process.cwd() + '/bible.html';

test('Chronicle seeds 99 created — COMPLETE, catalog is 99, lists all 99, syncs makeable, toggles persist', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.addInitScript(() => {
    // v673 — WRATH is the LAST unseeded word, so it plays BOTH badge probes: boot with an empty
    // stash → '⏳ Missing'; then its exact runes are stashed in-page and the re-render must flip
    // the same row to '✅ Can make now'.
    localStorage.setItem('d2r_runeStash', JSON.stringify({}));
  });
  await page.goto(URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1400);
  await page.evaluate(() => (window as any).switchTab('tools'));
  // v372 — default filter is now "⏳ Left"; switch to "All 100" so this test can see every row incl. created.
  await page.evaluate(() => { const c = document.getElementById('rw-chronicle-card'); if (c) c.classList.remove('collapsed'); (window as any).rwcSetFilter('all'); });
  await page.waitForTimeout(300);

  const r = await page.evaluate(() => {
    const w0: any = window;
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
      spirit: find('Spirit'), zephyr: find('Zephyr'),
      beast: find('Beast'), death: find('Death'), faith: find('Wrath'),  // read BEFORE the leaf() un-make probe runs
      leaf: (() => {   // v674 — NO unseeded word exists at 99/99: un-make Wrath in-page, stash its
        // recipe → the row must read Can make now; the re-make below restores the sealed Chronicle.
        (window as any).rwToggleMade('Wrath');
        const rec = ((w0.RUNEWORD_TIP['Wrath'] || {}).rec || []);
        const st: any = {}; rec.forEach((rn: string) => (st[rn] = (st[rn] || 0) + 1));
        localStorage.setItem('d2r_runeStash', JSON.stringify(st));
        try { if (w0.runeStash) Object.keys(st).forEach((k) => (w0.runeStash[k] = st[k])); } catch (e) {}
        try { (window as any).renderRunewordChronicle(); (window as any).rwcSetFilter('all'); } catch (e) {}
        const rows2 = Array.from(document.querySelectorAll('#rwc-list .rwc-row'));
        const el = rows2.find((r) => (r.querySelector('.rwc-name')?.textContent || '') === 'Wrath');
        const out = el ? { badge: el.querySelector('.rwc-badge')?.textContent || '', made: el.classList.contains('rwc-made') } : null;
        (window as any).rwToggleMade('Wrath');   // re-seal
        localStorage.removeItem('d2r_rwUnmade');
        return out;
      })(),
    };
  });

  expect(errs).toEqual([]);
  // seeded the 42-runeword durable floor (Konyo's actual created list, + Zephyr + Memory + Rift + Void as of v456-v463)
  expect(r.madeCount).toBe(99);   // v674 — 99/99, the Chronicle is COMPLETE
  ['Beast', 'Chains of Honor', 'Death', 'Mosaic', 'Edge', 'Lore', 'Pride', 'Destruction', "Ancients' Pledge", 'Spirit', 'Grief', 'Stone', 'Enigma', 'Doom', 'Plague', 'Treachery', 'Zephyr', 'Memory', 'Rift', 'Void', 'Fury', 'Gloom'].forEach((n) =>
    expect(r.madeKeys).toContain(n));
  expect(r.rowCount).toBe(99);                  // all 99 runewords listed (v658 recalibration — 99 since the v651 Hustle purge)
  expect(r.prog).toContain('99 / 99');          // v674 — sealed
  expect(r.spirit?.made).toBe(true);            // now a seeded forged RW → reads Created
  expect(r.zephyr?.made).toBe(true);            // v456 — Zephyr is now a seeded floor RW → reads Created
  expect(r.leaf?.badge).toContain('Can make now');   // v673 — the SAME Wrath row flips once its recipe is stashed
  expect(r.beast?.made).toBe(true);             // a seeded one reads Created
  expect(r.death?.made).toBe(true);             // a newly-seeded (v420) one reads Created
  expect(r.faith?.made).toBe(true);             // v674 — Wrath sealed the Chronicle

  // v674 — no unseeded word exists: the toggle contract is now the un-make/re-make ROUND-TRIP
  const after = await page.evaluate(() => {
    (window as any).rwToggleMade('Wrath');   // un-make (99 → 98, un-mark recorded)
    const mid = Object.keys(JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')).length;
    (window as any).rwToggleMade('Wrath');   // re-make (98 → 99, un-mark cleared)
    const made = JSON.parse(localStorage.getItem('d2r_rwMade') || '{}');
    localStorage.removeItem('d2r_rwUnmade');
    return { faith: !!made['Wrath'], count: Object.keys(made).length, mid };
  });
  expect(after.mid).toBe(98);
  expect(after.faith).toBe(true);
  expect(after.count).toBe(99);
});
