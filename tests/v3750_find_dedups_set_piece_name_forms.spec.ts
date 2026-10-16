import { test, expect } from '@playwright/test';

// #76 (slice 3) — FIND DEDUPS A SET PIECE STORED UNDER TWO NAME-FORMS.
// GrokBot read his live board (#230 6212587204): FIND "Natalya" returned 5 rows, with BOTH
// "Natalya's Totem" (bare) AND "Natalya's Totem (helm)" shown at different cells. The Natalya's Odium
// set has exactly ONE Totem (the helm), so these are the SAME item under two name strings — not two
// copies. vaultFind is name-based and _vaultFindMatches does not dedup, so two pool strings that share a
// canonical set-piece base rendered as two rows.
// FIX (read-only — no store written, his data untouched): _vfCanon maps a bare set-piece name to its
// roster slotted form (built from __allSets + _etherNorm, scoped to KNOWN set pieces so a unique/rune is
// never folded), and vaultFind dedups on that key, preferring the slotted form when he owns it.
// RED WITHOUT THE FIX: _vfCanon is undefined (unit test errors); vaultFind('Natalya') returns TWO rows
// containing "Totem" (integration test gets 2, expects 1). Verified locally: on the real roster the five
// Natalya matches collapse 5 -> 4 with the Totem shown as "Natalya's Totem (helm)". [[regression-guard]]

const URL = 'file://' + process.cwd() + '/bible.html';

async function seedLoad(page: any, owned: string[], copies: any, assign: any) {
  await page.addInitScript(({ owned, copies, assign }: any) => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      Object.defineProperty(navigator, 'webdriver', { get: () => true });
      localStorage.setItem('d2r_owned', JSON.stringify(owned));
      localStorage.setItem('d2r_copies', JSON.stringify(copies));
      localStorage.setItem('d2r_muleAssign', JSON.stringify(assign));
    } catch (e) {}
  }, { owned, copies, assign });
  await page.goto(URL);
  await page.waitForFunction(() =>
    (window as any).vaultFind && (window as any).switchTab && (window as any)._vfCanon);
}

test('_vfCanon collapses a set piece bare + slotted name-forms, never a non-set item (#76)', async ({ page }) => {
  await seedLoad(page, ['Raven Frost'], {}, {});
  const r = await page.evaluate(() => {
    const w = window as any;
    return {
      bare: w._vfCanon("Natalya's Totem"),
      slotted: w._vfCanon("Natalya's Totem (helm)"),
      unique: w._vfCanon('Raven Frost'),
    };
  });
  // both name-forms resolve to the SAME canonical slotted roster form
  expect(r.bare).toBe("Natalya's Totem (helm)");
  expect(r.slotted).toBe("Natalya's Totem (helm)");
  // a non-set item is never folded (scoped to known set pieces)
  expect(r.unique).toBe('Raven Frost');
});

test('vaultFind shows ONE row for a set piece owned under two name-forms (#76)', async ({ page }) => {
  // he owns both the bare and the slotted Totem (the real duplicate), a sibling piece, and a control unique
  const owned = ["Natalya's Totem", "Natalya's Totem (helm)", "Natalya's Mark (claws)", 'Raven Frost'];
  await seedLoad(page, owned, {}, {});
  await page.evaluate(() => (window as any).switchTab('tools'));
  const rows: string[] = await page.evaluate(() => {
    const w = window as any;
    w.vaultFind('Natalya');
    const els = Array.from(document.querySelectorAll('#vault-find-results .vfr-row'));
    return els.map((e) => {
      const n = e.querySelector('.vfr-name') as HTMLElement | null;
      return (n && n.textContent) || (e as HTMLElement).getAttribute('title') || '';
    });
  });
  // the seed must actually produce FIND rows (never a vacuous pass): the sibling piece is present
  expect(rows.some((n) => /Mark/.test(n)), 'the seeded Natalya pieces appear in FIND (seed is live)').toBe(true);
  const totem = rows.filter((n) => /Totem/.test(n));
  // GREEN: ONE Totem row, the canonical slotted form. RED (pre-fix): TWO Totem rows.
  expect(totem.length, 'a set piece owned under two name-forms shows ONE FIND row, not two (#76)').toBe(1);
  expect(totem[0]).toContain('(helm)');
});
