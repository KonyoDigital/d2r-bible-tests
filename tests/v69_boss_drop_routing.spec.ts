// v1754 — through the shared net stub, so this spec's measurements do not depend on the
// runner reaching fonts.googleapis.com. bible.html makes exactly FIVE external requests and
// all five are fonts; stubbing them removes the whole external surface.
//
// ⚠ NOT because a failed font collapses this layout — I checked, and it does not. Measured
// three ways, .set-card-header is 78px ONLINE, 78px OFFLINE and 78px STUBBED. The v1749
// note on _net_stub says a font failure makes that bar 0px; offline does not reproduce it,
// and the flake it was written about turned out to be a blind toggleCardCollapse leaving
// the card COLLAPSED (fixed in v1751, proven by forcing .collapsed). The honest reason to
// stub here is determinism, not a defect anyone has shown. [[inherited_claim_is_not_evidence]]
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v69 — regression lock for the "📦 top drops from this boss · click row to open in calc"
// table in every boss-detail card. Each row is wired onclick="navigateToItem('<name>', …)"
// and navigateToItem opens the calc golden card ONLY if the name resolves in ITEMS
// (renderDetail silently hides otherwise). A silent dead click == a row whose name isn't in
// ITEMS, or whose onclick string is malformed (e.g. an unescaped quote in the name). This
// sweeps EVERY boss + EVERY top-drop row for both failure modes, then spot-clicks real rows
// (incl. the apostrophe trap) to prove the card actually opens and lands in the viewport.
declare const BOSSES: any[];
declare const ITEMS: any[];

test.describe('v69 boss top-drop row → calc routing', () => {
  test('every boss top-drop row name resolves in ITEMS with a well-formed onclick (no silent dead clicks)', async ({ page }) => {
    await page.goto(URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(1200);
    const bossIds: string[] = await page.evaluate(() => (BOSSES as any[]).map((b) => b.id));
    const failures: any[] = [];
    for (const id of bossIds) {
      await page.evaluate((bid) => (window as any).renderBossDetailCard(bid), id);
      const rows = await page.evaluate(() => {
        const out: any[] = [];
        document.querySelectorAll('#boss-detail-panel table.drops tbody tr').forEach((tr) => {
          if (tr.children.length === 1) return; // colspan "no items" placeholder
          const name = (tr.querySelector('strong') as HTMLElement)?.textContent?.trim() || null;
          const onclick = tr.getAttribute('onclick') || '';
          // pull the first quoted arg out of navigateToItem('<arg>', …)
          const m = onclick.match(/navigateToItem\('((?:[^'\\]|\\.)*)'/);
          const argRaw = m ? m[1] : null;
          const arg = argRaw == null ? null : argRaw.replace(/\\'/g, "'");
          const inItems = name ? (ITEMS as any[]).some((x) => x.n === name) : false;
          out.push({ name, arg, inItems, wired: /navigateToItem\(/.test(onclick) });
        });
        return out;
      });
      for (const r of rows) {
        if (!r.wired || !r.inItems || r.arg !== r.name) failures.push({ boss: id, ...r });
      }
    }
    expect(failures).toEqual([]);
  });

  test('spot-click: real rows open the calc card in view, incl. the apostrophe trap', async ({ page }) => {
    const errs: string[] = [];
    page.on('pageerror', (e) => errs.push('PAGEERR: ' + e.message));
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(1200);
    const cases: { boss: string; text: string }[] = [
      { boss: 'mephisto', text: "The General's Tan Do Li Ga" }, // apostrophe escaping trap
      { boss: 'mephisto', text: 'Venom Ward' },
      { boss: 'andariel', text: '' },                            // first row, whatever it is
    ];
    for (const c of cases) {
      await page.click('.tab[data-tab="bosses"]');
      await page.waitForTimeout(120);
      await page.evaluate((bid) => (window as any).setActiveBoss(bid, undefined, { intent: 'open' }), c.boss);
      await page.waitForTimeout(180);
      const row = c.text
        ? page.locator('#boss-detail-panel table.drops tbody tr', { hasText: c.text })
        : page.locator('#boss-detail-panel table.drops tbody tr').first();
      const name = c.text || (await row.locator('strong').first().textContent())?.trim() || '';
      await row.first().click();
      await page.waitForTimeout(900);
      const r = await page.evaluate((nm) => {
        const det = document.getElementById('item-detail');
        const card = det?.querySelector('.aid-card') as HTMLElement | null;
        const rect = card?.getBoundingClientRect();
        return {
          calc: document.querySelector('.tab[data-tab="calc"]')?.classList.contains('active'),
          shown: !!det?.classList.contains('show'),
          mentions: (det?.innerHTML || '').includes(nm),
          cardInView: !!rect && rect.top > -60 && rect.top < 900,
        };
      }, name);
      expect(r, `routing ${c.boss}/${name}`).toEqual({ calc: true, shown: true, mentions: true, cardInView: true });
    }
    expect(errs).toEqual([]);
  });
});
