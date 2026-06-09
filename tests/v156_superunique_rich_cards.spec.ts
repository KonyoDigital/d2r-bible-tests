import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v156 — the bottom Super-Unique cards (#superunique-container) adopt the COLLAPSED
// rich-header look of the top TZ-zone cards (Konyo: "i want the bottom of the page also
// like this"): emblem + .tz-zone-title-block (gold-bright name + 🎯 italic role sub +
// act·immune loc) + tier badge + chevron, all in one gradient bar; tags collapse into a
// .tz-zone-collapse until the card opens (.zone-open). The two middle small-font prose
// blocks (Flayer answer + Super-Uniques blurb) move BELOW the card grid so the section
// titles flow one after the other symmetrically. ZERO fabrication — su data unchanged.
test.describe('v156 super-unique cards mirror the rich TZ-zone first-glance', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
    await page.waitForTimeout(300);
  });

  test('every su-card has the rich header block (emblem + title-block + tier + chevron)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#superunique-container .su-card')] as HTMLElement[];
      return {
        count: cards.length,
        withEmblem: cards.filter((c) => !!c.querySelector('.tz-zone-header .sec-h-art.tz-zone-emblem')).length,
        withBlock: cards.filter((c) => !!c.querySelector('.tz-zone-header .tz-zone-title-block')).length,
        nameIsSecHt: cards.filter((c) => !!c.querySelector('.tz-zone-name.sec-h-t')).length,
        withSub: cards.filter((c) => (c.querySelector('.tz-zone-sub')?.textContent || '').includes('🎯')).length,
        withLoc: cards.filter((c) => !!c.querySelector('.tz-zone-loc')).length,
        withTier: cards.filter((c) => (c.querySelector('.tz-zone-tier')?.textContent || '').startsWith('mlvl')).length,
        withChev: cards.filter((c) => !!c.querySelector('.tz-zone-chev.sec-chev')).length,
        withCollapse: cards.filter((c) => !!c.querySelector('.tz-zone-collapse')).length,
      };
    });
    expect(r.count).toBeGreaterThanOrEqual(6);
    expect(r.withEmblem).toBe(r.count);
    expect(r.withBlock).toBe(r.count);
    expect(r.nameIsSecHt).toBe(r.count);
    expect(r.withSub).toBe(r.count);
    expect(r.withLoc).toBe(r.count);
    expect(r.withTier).toBe(r.count);
    expect(r.withChev).toBe(r.count);
    expect(r.withCollapse).toBe(r.count);
  });

  test('the name is gold-bright + the header is a gradient bar (TZ-zone parity)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const card = document.querySelector('#superunique-container .su-card') as HTMLElement;
      const header = card.querySelector('.tz-zone-header') as HTMLElement;
      const name = card.querySelector('.tz-zone-name') as HTMLElement;
      return {
        nameColor: getComputedStyle(name).color,
        hasGradient: /gradient/.test(getComputedStyle(header).backgroundImage),
      };
    });
    expect(r.nameColor).toBe('rgb(240, 192, 96)');   // --gold-bright, like .tz-zone-name on the top cards
    expect(r.hasGradient).toBe(true);
  });

  test('the tags collapse stays hidden until the card opens (.zone-open)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const card = document.querySelector('#superunique-container .su-card') as HTMLElement;
      const collapse = card.querySelector('.tz-zone-collapse') as HTMLElement;
      const before = getComputedStyle(collapse).display;
      const openBefore = card.classList.contains('zone-open');
      card.click();
      const card2 = document.querySelector('#superunique-container .su-card') as HTMLElement;
      const collapse2 = card2.querySelector('.tz-zone-collapse') as HTMLElement;
      return {
        before, openBefore,
        afterDisplay: getComputedStyle(collapse2).display,
        openAfter: card2.classList.contains('zone-open'),
        detailShown: !card2.querySelector('.su-detail')!.hasAttribute('hidden'),
      };
    });
    expect(r.before).toBe('none');        // collapsed by default
    expect(r.openBefore).toBe(false);
    expect(r.afterDisplay).toBe('block'); // opens on click
    expect(r.openAfter).toBe(true);
    expect(r.detailShown).toBe(true);     // toggleSuperUnique still renders the detail box
  });

  test('the two prose blocks now sit BELOW the card grid (symmetric titles)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const container = document.getElementById('superunique-container') as HTMLElement;
      const head = container.previousElementSibling as HTMLElement;     // the .tz-group-head divider
      const next = container.nextElementSibling as HTMLElement;         // first relocated prose block
      const after = next?.nextElementSibling as HTMLElement;            // second relocated prose block
      const tab = document.getElementById('tab-tz') as HTMLElement;
      return {
        dividerIsGroupHead: head.classList.contains('tz-group-head'),
        dividerText: head.textContent || '',
        firstAfter: (next?.textContent || '').includes('Super-Uniques — the named bosses'),
        secondAfter: (after?.textContent || '').includes('Flayer Dungeon answer'),
        // both prose blocks come AFTER the container in DOM order (relocated below)
        proseBelow: !!next && !!after,
        // v51 verbatim phrase still present in the tab
        phrasePresent: /Super-Uniques — the named bosses/.test(tab.textContent || ''),
      };
    });
    expect(r.dividerIsGroupHead).toBe(true);
    expect(r.dividerText).toContain('Super-Uniques');
    expect(r.firstAfter).toBe(true);
    expect(r.secondAfter).toBe(true);
    expect(r.proseBelow).toBe(true);
    expect(r.phrasePresent).toBe(true);
  });

  test('no console errors rendering the restyled super-unique cards', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
    await page.waitForTimeout(300);
    expect(errors).toEqual([]);
  });
});
