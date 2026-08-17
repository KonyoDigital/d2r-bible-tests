// v1754 — through the shared net stub: this spec asserts `expect(errors).toEqual([])`, and a
// console error array collects RESOURCE 404s as well as JS faults. bible.html pulls its
// typeface from fonts.googleapis.com, so on a runner with slow or blocked outbound network
// the spec goes red on the weather rather than on the code. The fixture fulfils fonts with an
// empty stylesheet (never aborts — an abort is itself a failed request).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v85 — TZ-zone ID cards enriched to the Baal-card depth (ADDITIVE, no cuts):
// every terror-zone detail now carries a dedicated SPECIAL-DROPS area (Sunder via
// Herald, the act-matched Worldstone Shard → its Renewed target, plus zone-specific
// Hellforge/Key/Griswold specials), a best-character module, and an action-plan —
// all derived from the single-source SPECIAL_DROPS / zone data (zero fabrication).
test.describe('v85 TZ zones carry the unified rich ID-card modules', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('every TZ zone detail renders the special-drops + best-char + action-plan modules', async ({ page }) => {
    const r = await page.evaluate(() => {
      const zones = (TZ_ZONES as any[]);
      const missing: string[] = [];
      zones.forEach((z: any) => {
        const h = (zoneDetailHtml as any)(z);
        const hasSpecial = /special drops/.test(h) && /Herald of Terror/.test(h);
        const hasBest = /best character/.test(h);
        const hasPlan = /action plan/.test(h) && /zd-plan/.test(h);
        if (!(hasSpecial && hasBest && hasPlan)) missing.push(z.name + ` [s:${hasSpecial} b:${hasBest} p:${hasPlan}]`);
      });
      return { count: zones.length, missing };
    });
    expect(r.count).toBeGreaterThanOrEqual(10);
    expect(r.missing, `zones missing a rich module: ${r.missing}`).toEqual([]);
  });

  test('the act-matched Worldstone Shard chip routes through openDrop (real material)', async ({ page }) => {
    // Act-1 zone (Tristram) → Western shard; Act-4 (River of Flame) → Deep shard.
    const r = await page.evaluate(() => {
      const zones = (TZ_ZONES as any[]);
      const tri = zones.find((z: any) => /tristram/i.test(z.name));
      const rof = zones.find((z: any) => /river of flame/i.test(z.name));
      return {
        triHtml: (zoneDetailHtml as any)(tri),
        rofHtml: (zoneDetailHtml as any)(rof),
      };
    });
    expect(r.triHtml).toMatch(/openDrop\('Worldstone Shard \(Western\)'\)/);
    expect(r.triHtml).toMatch(/Griswold's Legacy/);          // Tristram zone special
    expect(r.rofHtml).toMatch(/openDrop\('Worldstone Shard \(Deep\)'\)/);
    expect(r.rofHtml).toMatch(/Hellforge rune/);             // River of Flame zone special
  });

  test('Arcane → Key of Hate, Halls → Key of Destruction (zone-specific specials)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const zones = (TZ_ZONES as any[]);
      const arc = zones.find((z: any) => /arcane sanctuary/i.test(z.name));
      const halls = zones.find((z: any) => /halls of/i.test(z.name));
      return {
        arc: (zoneDetailHtml as any)(arc),
        halls: (zoneDetailHtml as any)(halls),
      };
    });
    expect(r.arc).toMatch(/openDrop\('Key of Hate'\)/);
    expect(r.halls).toMatch(/openDrop\('Key of Destruction'\)/);
  });

  test('the special-drops Herald chip actually opens the Herald card via openDrop', async ({ page }) => {
    await page.evaluate(() => {
      const box = document.getElementById('tz-zone-detail-0');
      if (box) { box.innerHTML = (zoneDetailHtml as any)((TZ_ZONES as any[])[0]); box.removeAttribute('hidden'); }
    });
    await page.waitForTimeout(150);
    await page.evaluate(() => (window as any).openDrop('Herald of Terror'));
    await page.waitForTimeout(400);
    const richName = await page.evaluate(() =>
      document.getElementById('herald-card')?.querySelector('.gic-name')?.textContent?.trim() || '');
    expect(richName).toMatch(/Herald of Terror/);
  });

  test('zone detail renders the golden .gbc-card shell with an artOr header (REG-001 lazy)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const h = (zoneDetailHtml as any)((TZ_ZONES as any[])[0]);
      return {
        full: h,
        head: h.slice(0, 600),
        hasShell: /class="gbc-card tz-zone-card-rich"/.test(h),
        hasHeader: /class="gbc-header/.test(h),
        hasTier: /gbc-tier-val/.test(h),
        hasBody: /class="gbc-body/.test(h),
      };
    });
    expect(r.hasShell, 'zone must render the unified golden gbc-card shell').toBe(true);
    expect(r.hasHeader).toBe(true);
    expect(r.hasTier).toBe(true);
    expect(r.hasBody).toBe(true);
    // emblem is artOr → either a lazy <img> (real art) or the gbc-emoji fallback
    expect(r.head).toMatch(/d2art-wrap|gbc-emoji/);
    if (/<img/.test(r.head)) expect(r.head).toMatch(/loading="lazy"/);
  });

  test('no console errors opening every TZ zone detail', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', e => errors.push(e.message));
    await page.click('.tab[data-tab="tz"]');
    await page.waitForTimeout(200);
    const n = await page.evaluate(() => (TZ_ZONES as any[]).length);
    for (let i = 0; i < n; i++) {
      await page.evaluate((zi) => (window as any).toggleZoneDetail(zi), i);
      await page.waitForTimeout(60);
    }
    expect(errors).toEqual([]);
  });
});
