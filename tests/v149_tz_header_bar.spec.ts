import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v149 — TZ zone titles adopt the Bosses-tab header-bar STRUCTURE (Konyo: identical in
// structure & font to RoTW / Runes / Bosses). Each .tz-zone-header is now a full-width
// gradient bar across the card top (mirrors .boss-header): bold 19px serif name + emblem
// + tier + chevron, pulled to the card edges. Parity is asserted against a real RoTW
// .sec-h-t (same Cinzel family + bold weight) so the two tabs can't drift apart.
test.describe('v149 TZ titles match the Bosses/RoTW header bar', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
  });

  test('the TZ zone header is a full-width gradient bar (not a bare flex row)', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const hdr = document.querySelector('#tz-zones-container .tz-zone-card > .tz-zone-header') as HTMLElement;
      const cs = getComputedStyle(hdr);
      return {
        hasBar: !!hdr,
        hasGradient: /gradient/.test(cs.backgroundImage),
        borderBottom: parseFloat(cs.borderBottomWidth) >= 1,
        // pulled to the card edges via negative margin (mirrors .boss-header spanning the card top)
        negTopMargin: parseFloat(cs.marginTop) < 0,
        padded: parseFloat(cs.paddingTop) >= 10,
      };
    });
    expect(r.hasBar).toBe(true);
    expect(r.hasGradient).toBe(true);
    expect(r.borderBottom).toBe(true);
    expect(r.negTopMargin).toBe(true);
    expect(r.padded).toBe(true);
  });

  test('the TZ title font matches a RoTW .sec-h-t (bold Cinzel, >=19px)', async ({ page }) => {
    // RoTW reference
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('rotw'));
    await page.waitForTimeout(250);
    const rotw = await page.evaluate(() => {
      const t = document.querySelector('#tab-rotw .sec-h .sec-h-t') as HTMLElement;
      const cs = getComputedStyle(t);
      return { fam: cs.fontFamily.split(',')[0].replace(/["']/g, ''), weight: cs.fontWeight };
    });
    // TZ title
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
    await page.waitForTimeout(250);
    const tz = await page.evaluate(() => {
      const t = document.querySelector('#tz-zones-container .tz-zone-card .tz-zone-name') as HTMLElement;
      const cs = getComputedStyle(t);
      return { fam: cs.fontFamily.split(',')[0].replace(/["']/g, ''), weight: cs.fontWeight, size: parseFloat(cs.fontSize) };
    });
    expect(tz.fam).toBe(rotw.fam);            // same serif-display (Cinzel)
    expect(tz.weight).toBe(rotw.weight);      // same bold weight (700)
    expect(tz.weight).toBe('700');
    expect(tz.size).toBeGreaterThanOrEqual(19);
  });

  test('the Pit cross-link card carries the same header bar', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const hdr = document.querySelector('.tz-crosslink-card > .tz-zone-header') as HTMLElement;
      if (!hdr) return { found: false };
      const cs = getComputedStyle(hdr);
      const name = hdr.querySelector('.tz-zone-name') as HTMLElement;
      return {
        found: true,
        hasGradient: /gradient/.test(cs.backgroundImage),
        nameWeight: name ? getComputedStyle(name).fontWeight : '',
      };
    });
    expect(r.found).toBe(true);
    expect(r.hasGradient).toBe(true);
    expect(r.nameWeight).toBe('700');
  });

  test('RoTW section headers also get the prominent Bosses/Runes bar (gradient + bold 19px)', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('rotw'));
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const h = document.querySelector('#tab-rotw .sec-h') as HTMLElement;
      const t = h?.querySelector('.sec-h-t') as HTMLElement;
      const cs = getComputedStyle(h);
      const tcs = getComputedStyle(t);
      return {
        hasGradient: /gradient/.test(cs.backgroundImage),
        padTop: parseFloat(cs.paddingTop),
        titleSize: parseFloat(tcs.fontSize),
        titleWeight: tcs.fontWeight,
      };
    });
    expect(r.hasGradient).toBe(true);
    expect(r.padTop).toBeGreaterThanOrEqual(13);
    expect(r.titleSize).toBeGreaterThanOrEqual(19);
    expect(r.titleWeight).toBe('700');
  });

  test('the shared .sec-h bars on the Reference tab are NOT enlarged (scope held)', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('ref'));
    await page.waitForTimeout(300);
    const size = await page.evaluate(() => {
      const t = document.querySelector('#tab-ref .sec-h.collapsed .sec-h-t') as HTMLElement;
      return t ? parseFloat(getComputedStyle(t).fontSize) : 0;
    });
    // Reference collapsed headers keep the original 17px editorial size (RoTW scope didn't leak)
    expect(size).toBeLessThanOrEqual(17);
  });

  test('no console errors rendering the restyled TZ tab', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
    await page.waitForTimeout(300);
    expect(errors).toEqual([]);
  });
});
