import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v552 — Forge flagship visual overhaul. Locks the application-style dashboard structure: HD-art hero with a
// big name, the Chronicle progress meter, dashboard KPI tiles, and HD-art task cards. Visual-only — the task
// logic is unchanged (guarded by v470/v545/v546/v550).

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 2, Tir: 2, Tal: 2, Sol: 2 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v580.2 — pin fresh (Insight/Wind joined the seed)
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  await page.evaluate(() => { const w: any = window; w._ensureSocketBaseEntry('Colossus Voulge (4os)'); w.switchTab('forge'); w.forgeSetFilter('all'); w.renderForge(); });
});

test('the hero has an HD art slot, a big name, and a CTA', async ({ page }) => {
  const r = await page.evaluate(() => {
    const hero = document.querySelector('#tab-forge .forge-hero');
    return {
      hero: !!hero,
      art: !!hero?.querySelector('.fh-art'),
      name: (hero?.querySelector('.fh-name')?.textContent || '').trim().length > 0,
      icobadge: !!hero?.querySelector('.fh-icobadge'),
      cta: !!hero?.querySelector('.fh-cta'),
      tone: (hero?.className || '').match(/forge-hero-(now|pipe|step)/) ? true : false,
    };
  });
  expect(r.hero).toBe(true);
  expect(r.art).toBe(true);
  expect(r.name).toBe(true);
  expect(r.icobadge).toBe(true);
  expect(r.cta).toBe(true);
  expect(r.tone).toBe(true);
});

test('the Chronicle progress meter renders with a fill and a made/total label', async ({ page }) => {
  const r = await page.evaluate(() => {
    const p = document.querySelector('#tab-forge .forge-progress');
    const fill = p?.querySelector('.fp-fill') as HTMLElement | null;
    return { present: !!p, hasFill: !!fill, width: fill ? fill.style.width : '', text: (p?.textContent || '').replace(/\s+/g, ' ') };
  });
  expect(r.present).toBe(true);
  expect(r.hasFill).toBe(true);
  expect(r.width).toMatch(/%$/);           // a percentage width
  expect(r.text).toMatch(/\/\s*100 forged/);
  expect(r.text).toMatch(/%/);
});

test('the sub-tab tiles are KPI dashboard tiles with counts', async ({ page }) => {
  const r = await page.evaluate(() => {
    const tabs = [...document.querySelectorAll('#tab-forge .forge-tabs .forge-tab')];
    const counts = tabs.map((t) => t.querySelector('.ft-ct')?.textContent || '');
    const active = document.querySelector('#tab-forge .forge-tab.on');
    return { tileCount: tabs.length, allHaveCounts: counts.every((c) => /\d/.test(c)), activeExists: !!active };
  });
  expect(r.tileCount).toBe(6);
  expect(r.allHaveCounts).toBe(true);
  expect(r.activeExists).toBe(true);
});

test('make-now task cards carry the item HD art (not a generic glyph) with an icon badge', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window; w.forgeSetFilter('now'); w.renderForge();
    const card = document.querySelector('#tab-forge .f-card.f-now');
    return {
      card: !!card,
      hdSlot: !!card?.querySelector('.f-cardart-hd'),
      img: !!card?.querySelector('.f-cardart-hd img'),
      badge: !!card?.querySelector('.f-cardart-badge'),
      arttip: !!card?.getAttribute('data-arttip'),
    };
  });
  expect(r.card).toBe(true);
  expect(r.hdSlot).toBe(true);
  expect(r.img).toBe(true);
  expect(r.badge).toBe(true);
  expect(r.arttip).toBe(true);
});
