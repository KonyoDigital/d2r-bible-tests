// v1754 — through the shared net stub: this spec asserts `expect(errors).toEqual([])`, and a
// console error array collects RESOURCE 404s as well as JS faults. bible.html pulls its
// typeface from fonts.googleapis.com, so on a runner with slow or blocked outbound network
// the spec goes red on the weather rather than on the code. The fixture fulfils fonts with an
// empty stylesheet (never aborts — an abort is itself a failed request).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v66 — TZ cross-link cards. The Pit is a permanent lvl-85 zone that DOES fire TZ alerts but
// isn't in TZ_ZONES (it's catalogued as a permanent farm target in the Bosses tab). A user who
// gets the "S-TIER LIVE NOW · The Pit" Telegram alert and opens the TZ tab couldn't find it, and
// the global search only surfaced it as a boss. This ships a pure router card that:
//   1. renders in the TZ tab, bucketed into its storyline-act group (The Pit -> Act 1),
//   2. carries ZERO fabricated data — every field is read live from the BOSSES entry,
//   3. routes (openBossDetail) to the same canonical boss ID card the Bosses tab opens,
//   4. is searchable in the global search as a ZONE (not only as a boss).
// This spec locks the rendering, the act-bucketing, the data-fidelity, the routing, and search.
test.describe('v66 TZ cross-link cards (The Pit)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="tz"]');
    await page.waitForTimeout(150);
  });

  test('cross-link card renders in the TZ tab, reading every field live from BOSSES (no fabrication)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cl = (TZ_CROSSLINKS as any[])[0];
      const b = (BOSSES as any[]).find((x) => x.id === cl.bossId);
      const card = document.querySelector('.tz-crosslink-card[data-crosslink-boss-id="' + cl.bossId + '"]') as HTMLElement;
      return {
        clCount: (TZ_CROSSLINKS as any[]).length,
        bossId: cl.bossId,
        exists: !!card,
        name: card ? card.querySelector('.tz-zone-name')!.textContent!.trim() : null,
        tier: card ? card.querySelector('.tz-zone-tier')!.textContent!.trim() : null,
        bossName: b.name,
        bossTier: b.tierTag,
        // the card must NOT invent a zone: its name + tier must equal the boss's own fields
        notInTzZones: !(TZ_ZONES as any[]).some((z) => z.name === b.name),
        hasUndefined: card ? /undefined/.test(card.innerHTML) : true,
        routesToBoss: card ? /openBossDetail\('pit'\)/.test(card.getAttribute('onclick') || '') : false,
        helperFn: typeof (window as any).tzCrosslinkCardHtml,
      };
    });
    expect(r.clCount).toBeGreaterThanOrEqual(1);
    expect(r.bossId).toBe('pit');
    expect(r.exists).toBe(true);
    expect(r.name).toBe(r.bossName);          // card name === boss name (read live, not fabricated)
    expect(r.tier).toBe(r.bossTier);          // card tier === boss tier
    expect(r.notInTzZones).toBe(true);         // proves it's bridging a real gap (not in TZ_ZONES)
    expect(r.hasUndefined).toBe(false);
    expect(r.routesToBoss).toBe(true);
    expect(r.helperFn).toBe('function');
  });

  test('the cross-link card sits inside its storyline-act group (The Pit under Act 1)', async ({ page }) => {
    const r = await page.evaluate(() => {
      // walk the rendered children in order; track the current act head, find the act the
      // crosslink card lands under — it must equal the Act 1 group, not Other/another act.
      const kids = [...document.querySelectorAll('#tz-zones-container > *')] as HTMLElement[];
      let curAct: string | null = null;
      let pitAct: string | null = null;
      for (const el of kids) {
        if (el.classList.contains('tz-group-head')) curAct = el.querySelector('.tz-group-act')!.textContent!.trim();
        else if (el.classList.contains('tz-crosslink-card') && el.getAttribute('data-crosslink-boss-id') === 'pit') pitAct = curAct;
      }
      // every regular zone card still renders (crosslink uses a separate class, count unchanged)
      const zoneCards = document.querySelectorAll('#tz-zones-container .tz-zone-card').length;
      return { pitAct, zoneCards, zoneLen: (TZ_ZONES as any[]).length };
    });
    expect(r.pitAct).toBe('Act 1');
    expect(r.zoneCards).toBe(r.zoneLen);   // cross-links don't disturb the TZ_ZONES card count
  });

  test('clicking the cross-link routes to The Pit\'s canonical boss detail card', async ({ page }) => {
    await page.locator('.tz-crosslink-card[data-crosslink-boss-id="pit"]').click();
    await page.waitForTimeout(250);
    const r = await page.evaluate(() => {
      const onBosses = document.querySelector('.tab[data-tab="bosses"]')!.classList.contains('active');
      const panel = document.getElementById('boss-detail-panel');
      return {
        onBosses,
        panelShown: !!panel && panel.classList.contains('show'),
        inner: panel ? panel.innerHTML : '',
      };
    });
    expect(r.onBosses).toBe(true);              // routed to the Bosses tab
    expect(r.panelShown).toBe(true);            // the boss detail panel is open
    expect(r.inner).toMatch(/The Pit/);         // showing The Pit's card
  });

  test('searching "pit" / "the pit" surfaces it as a ZONE (closes the search gap)', async ({ page }) => {
    const results: Record<string, {lab: string, cat: string}[]> = {};
    for (const q of ['pit', 'the pit']) {
      await page.fill('#gsearch-input', '');
      await page.fill('#gsearch-input', q);
      await page.waitForTimeout(220);
      results[q] = await page.evaluate(() => [...document.querySelectorAll('#gsearch-results .gsearch-item')]
        .map((el) => ({
          lab: (el.querySelector('.gsearch-lab') as HTMLElement)?.textContent?.trim() || '',
          cat: (el.querySelector('.gsearch-cat') as HTMLElement)?.textContent?.trim() || '',
        })));
    }
    // "pit" must now return a zone-categorised The Pit hit (in addition to the boss hit)
    const pitZone = results['pit'].find((x) => /The Pit/.test(x.lab) && x.cat === 'zone');
    const thePitZone = results['the pit'].find((x) => /The Pit/.test(x.lab) && x.cat === 'zone');
    expect(pitZone).toBeTruthy();
    expect(thePitZone).toBeTruthy();
  });

  test('the zone search result routes into the TZ tab and scrolls to the cross-link card', async ({ page }) => {
    await page.fill('#gsearch-input', 'the pit');
    await page.waitForTimeout(220);
    // click the zone-categorised result
    const zoneItem = page.locator('#gsearch-results .gsearch-item', { hasText: 'The Pit' }).filter({ has: page.locator('.gsearch-cat', { hasText: 'zone' }) }).first();
    await zoneItem.click();
    await page.waitForTimeout(250);
    const r = await page.evaluate(() => ({
      onTz: document.querySelector('.tab[data-tab="tz"]')!.classList.contains('active'),
      cardExists: !!document.querySelector('.tz-crosslink-card[data-crosslink-boss-id="pit"]'),
    }));
    expect(r.onTz).toBe(true);
    expect(r.cardExists).toBe(true);
  });

  test('no console errors across the cross-link + search flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="tz"]');
    await page.waitForTimeout(150);
    await page.fill('#gsearch-input', 'pit');
    await page.waitForTimeout(220);
    // v708.1 — the card's center can sit under the fixed control dock at 1280×720 (pointer
    // intercepted; scrollIntoViewIfNeeded ignores scroll-margin). This spec guards CONSOLE
    // ERRORS in the flow, not pixel-click mechanics — fire the handler via evaluate, the
    // established BUG-013 / BUG-119 pattern for dock/header-covered targets.
    await page.evaluate(() => (document.querySelector('.tz-crosslink-card[data-crosslink-boss-id="pit"]') as HTMLElement)?.click());
    await page.waitForTimeout(200);
    expect(errors).toEqual([]);
  });
});
