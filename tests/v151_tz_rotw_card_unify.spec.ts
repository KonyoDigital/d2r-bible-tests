import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v151 — TZ-zone + RoTW cards adopt the Runes/Bosses/TOOLS first-glance: a clean stack
// of COLLAPSED rich-header cards. The TZ name + italic super-unique subtitle + small
// act/mlvl meta now live INSIDE the gradient header bar (mirrors .boss-header's title
// block); the prose body + tags collapse away until the card is opened. The 6 RoTW
// section headers gain the same Tools-style italic subtitle under each title.
test.describe('v151 TZ + RoTW cards replicate the Tools/Runes first-glance', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
  });

  test('the TZ header bar carries the rich title block (name + italic subtitle + small meta)', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const card = document.querySelector('#tz-zones-container .tz-zone-card') as HTMLElement;
      const block = card.querySelector('.tz-zone-header .tz-zone-title-block');
      const sub = card.querySelector('.tz-zone-header .tz-zone-sub') as HTMLElement;
      const loc = card.querySelector('.tz-zone-header .tz-zone-loc') as HTMLElement;
      const name = card.querySelector('.tz-zone-header .tz-zone-name') as HTMLElement;
      return {
        hasBlock: !!block,
        subInsideHeader: !!sub,
        locInsideHeader: !!loc,
        subItalic: sub ? getComputedStyle(sub).fontStyle : '',
        nameWeight: name ? getComputedStyle(name).fontWeight : '',
      };
    });
    expect(r.hasBlock).toBe(true);
    expect(r.subInsideHeader).toBe(true);   // super-unique subtitle lives in the bar (boss-header parity)
    expect(r.locInsideHeader).toBe(true);   // act/mlvl meta lives in the bar
    expect(r.subItalic).toBe('italic');
    expect(r.nameWeight).toBe('700');
  });

  test('TZ cards start COLLAPSED — the prose body is hidden until the card is opened', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
    await page.waitForTimeout(300);
    const collapsedHidden = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#tz-zones-container .tz-zone-card')] as HTMLElement[];
      return cards.every((c) => {
        const col = c.querySelector('.tz-zone-collapse') as HTMLElement | null;
        return !c.classList.contains('zone-open') && (!col || getComputedStyle(col).display === 'none');
      });
    });
    expect(collapsedHidden).toBe(true);

    // open the first zone → its collapse block + rich detail become visible
    await page.evaluate(() => (window as any).toggleZoneDetail(0));
    await page.waitForTimeout(250);
    const opened = await page.evaluate(() => {
      const card = document.querySelector('#tz-zones-container .tz-zone-card.zone-open') as HTMLElement;
      if (!card) return { open: false, bodyShown: false, detailShown: false };
      const col = card.querySelector('.tz-zone-collapse') as HTMLElement;
      const det = card.querySelector('.tz-zone-detail') as HTMLElement;
      return {
        open: true,
        bodyShown: getComputedStyle(col).display !== 'none',
        detailShown: !det.hasAttribute('hidden'),
      };
    });
    expect(opened.open).toBe(true);
    expect(opened.bodyShown).toBe(true);
    expect(opened.detailShown).toBe(true);
  });

  test('the collapsed TZ bar still passes the v149 bar probes (gradient + negative top margin)', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const hdr = document.querySelector('#tz-zones-container .tz-zone-card:not(.zone-open) > .tz-zone-header') as HTMLElement;
      const cs = getComputedStyle(hdr);
      return {
        hasGradient: /gradient/.test(cs.backgroundImage),
        negTopMargin: parseFloat(cs.marginTop) < 0,
        borderBottomWidth: parseFloat(cs.borderBottomWidth) >= 1,
      };
    });
    expect(r.hasGradient).toBe(true);
    expect(r.negTopMargin).toBe(true);
    expect(r.borderBottomWidth).toBe(true);
  });

  test('all 6 RoTW section headers carry a Tools-style italic subtitle', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('rotw'));
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const heads = [...document.querySelectorAll('#tab-rotw > .sec-h')] as HTMLElement[];
      const subs = heads.map((h) => h.querySelector('.sec-h-sub') as HTMLElement | null);
      const withSub = subs.filter(Boolean) as HTMLElement[];
      return {
        headCount: heads.length,
        subCount: withSub.length,
        allItalic: withSub.every((s) => getComputedStyle(s).fontStyle === 'italic'),
        titles: heads.map((h) => h.querySelector('.sec-h-t')?.textContent?.trim() || ''),
        sampleSub: heads[0]?.querySelector('.sec-h-sub')?.textContent?.trim() || '',
      };
    });
    expect(r.headCount).toBe(6);
    expect(r.subCount).toBe(6);
    expect(r.allItalic).toBe(true);
    expect(r.titles).toContain('Herald of Terror');
    expect(r.titles).toContain('Sunder Charms');
    expect(r.sampleSub).toMatch(/Sunder source/);
  });

  test('the RoTW subtitle sits in the same flex header bar as the title (sec-h-block)', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('rotw'));
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const h = document.querySelector('#tab-rotw > .sec-h') as HTMLElement;
      const block = h.querySelector('.sec-h-block') as HTMLElement;
      const t = block?.querySelector('.sec-h-t');
      const s = block?.querySelector('.sec-h-sub');
      return {
        hasBlock: !!block,
        blockColumn: block ? getComputedStyle(block).flexDirection : '',
        titleInBlock: !!t,
        subInBlock: !!s,
      };
    });
    expect(r.hasBlock).toBe(true);
    expect(r.blockColumn).toBe('column');
    expect(r.titleInBlock).toBe(true);
    expect(r.subInBlock).toBe(true);
  });

  test('no console errors rendering the restyled TZ + RoTW tabs', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
    await page.waitForTimeout(250);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('rotw'));
    await page.waitForTimeout(250);
    expect(errors).toEqual([]);
  });
});
