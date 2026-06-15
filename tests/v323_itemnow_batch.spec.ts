import { test, expect } from '@playwright/test';

// v323 — itemnow batch: Best Runeword Bases reference card + crafted name-example pools in the
// Workshop. 312 grail untouched; this grows the reference layer.

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any).RW_BASES && (window as any).CRAFT_NAME_EXAMPLES && (window as any)._cwRecipeRow);
});

test('Best Runeword Bases card renders rows with clickable orange runeword chips', async ({ page }) => {
  const r = await page.evaluate(() => {
    (window as any).renderRwBases();
    const list = document.getElementById('rw-bases-list')!;
    const rows = list.querySelectorAll('.rwb-row').length;
    const chip = list.querySelector('.rwb-rw') as HTMLElement | null;
    // base names read in-game white, runeword chips orange
    const base = list.querySelector('.rwb-base') as HTMLElement | null;
    document.body.appendChild(list); // ensure computed style resolves
    return {
      rows,
      chipText: chip ? chip.textContent : null,
      chipColor: chip ? getComputedStyle(chip).color : null,
      baseColor: base ? getComputedStyle(base).color : null,
    };
  });
  expect(r.rows).toBeGreaterThanOrEqual(15);     // 4 slots × several bases
  expect(r.chipText).toBeTruthy();
  expect(r.chipColor).toBe('rgb(255, 168, 0)');  // --q-orange runewords
  expect(r.baseColor).toBe('rgb(244, 244, 244)'); // --q-normal white bases
});

test('a runeword chip routes via openDrop to a real runeword card', async ({ page }) => {
  const ok = await page.evaluate(() => {
    (window as any).renderRwBases();
    const chip = document.querySelector('#rw-bases-list .rwb-rw') as HTMLElement;
    const name = chip.getAttribute('data-arttip') || chip.textContent || '';
    // every chip name must resolve as a runeword (findRuneword) so openDrop lands on a card
    return !!(window as any).findRuneword(name.trim());
  });
  expect(ok).toBe(true);
});

test('the Crafted Workshop shows in-game name examples per slot (Brimstone Grip on Gloves)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const crafts = (window as any).CRAFTS || (window as any).eval('CRAFTS');
    const blood = crafts.find((c: any) => c.key === 'Blood') || crafts[0];
    const html = (window as any)._cwRecipeRow(blood, 'Gloves', false);
    return { hasChip: html.includes('cw-name-ex'), hasName: html.includes('Brimstone Grip') };
  });
  expect(r.hasChip).toBe(true);
  expect(r.hasName).toBe(true);
});

test('every slot with name examples has at least 3 names', async ({ page }) => {
  const r = await page.evaluate(() => {
    const E = (window as any).CRAFT_NAME_EXAMPLES;
    return Object.keys(E).map(k => ({ k, n: E[k].length }));
  });
  for (const e of r) expect(e.n, e.k).toBeGreaterThanOrEqual(3);
});
