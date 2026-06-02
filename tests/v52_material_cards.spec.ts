import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v52 — unified material ID cards. The keys / essences / organs / uber-charms /
// worldstone-shards that farming "feeds into" previously lived only as inline
// SPECIAL_DROPS strings + non-clickable feeds-into badges. This builds the same
// "click the drop → open its detail card" contract the grail items + bosses
// already have: every feeds-into badge whose label resolves to a SPECIAL_DROPS
// entry becomes a clickable golden material card (findMaterial → materialDetailHtml
// → openDrop), reachable from any boss/zone card on the site. Grail items still
// route to the calc golden card; only SPECIAL_DROPS materials get the new card.
// No new drop odds are fabricated — this is a wiring/unification layer.
test.describe('v52 unified material ID cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('findMaterial resolves keys/essences/organs/charms/shards (direction-tolerant), null for non-materials', async ({ page }) => {
    const r = await page.evaluate(() => {
      const fm = (window as any).findMaterial;
      const nm = (n: string) => { const m = fm(n); return m ? m.item.n : null; };
      return {
        isFn: typeof fm,
        key: nm('Key of Destruction'),
        essence: nm('Essence of Hatred'),
        organ: nm("Diablo's Horn"),
        torch: nm('Hellfire Torch'),
        anni: nm('Annihilus'),
        // feeds-into labels phrase shards as "Northern Worldstone Shard";
        // SPECIAL_DROPS stores "Worldstone Shard (Northern)" → must still resolve.
        shardNorth: nm('Northern Worldstone Shard'),
        shardWest: nm('Western Worldstone Shard'),
        // non-materials / not-in-SPECIAL_DROPS must NOT false-match
        ancient: nm('Colossal Ancient Statue'),
        nonsense: nm('Totally Not A Drop'),
        grailItem: nm('Harlequin Crest (Shako)'),
      };
    });
    expect(r.isFn).toBe('function');
    expect(r.key).toBe('Key of Destruction');
    expect(r.essence).toBe('Essence of Hatred');
    expect(r.organ).toBe("Diablo's Horn");
    expect(r.torch).toBe('Hellfire Torch');
    expect(r.anni).toBe('Annihilus');
    expect(r.shardNorth).toBe('Worldstone Shard (Northern)');
    expect(r.shardWest).toBe('Worldstone Shard (Western)');
    expect(r.ancient).toBe('Colossal Ancient Statue');   // v62: now a material card
    expect(r.nonsense).toBeNull();
    expect(r.grailItem).toBeNull(); // grail items are NOT materials (routed to calc card)
  });

  test('materialDetailHtml renders a complete card: where-it-drops, recipe, caveat, no undefined', async ({ page }) => {
    const r = await page.evaluate(() => {
      const html = (window as any).materialDetailHtml;
      const key = html('Key of Destruction');
      const shard = html('Northern Worldstone Shard');
      return {
        isFn: typeof html,
        keyHasName: /Key of Destruction/.test(key),
        keyHasFrom: /drops from/.test(key),
        keyHasRecipe: /Recipe \/ use|recipe/.test(key),
        keyHasWhere: /Where it drops/.test(key),
        keyHasCaveat: /not MF-scaled|not fabricated odds/.test(key),
        keyNoUndef: !/undefined/.test(key),
        shardHasName: /Worldstone Shard \(Northern\)/.test(shard),
        shardNoUndef: !/undefined/.test(shard),
        // every material card carries the honesty caveat
        allCaveated: (SPECIAL_DROPS && Object.values(SPECIAL_DROPS as any).every((cat: any) =>
          (cat.items || []).every((it: any) => /not fabricated odds/.test(html(it.n))))),
      };
    });
    expect(r.isFn).toBe('function');
    expect(r.keyHasName).toBe(true);
    expect(r.keyHasFrom).toBe(true);
    expect(r.keyHasRecipe).toBe(true);
    expect(r.keyHasWhere).toBe(true);
    expect(r.keyHasCaveat).toBe(true);
    expect(r.keyNoUndef).toBe(true);
    expect(r.shardHasName).toBe(true);
    expect(r.shardNoUndef).toBe(true);
    expect(r.allCaveated).toBe(true);
  });

  test('openDrop routes materials → material card, grail items → calc golden card', async ({ page }) => {
    const r = await page.evaluate(() => {
      const od = (window as any).openDrop;
      // material → #item-detail .material-card
      od('Key of Destruction');
      const matCard = document.querySelector('#item-detail .material-card');
      const matName = matCard ? (matCard.querySelector('.gic-name')?.textContent || '').trim() : '';
      const activeMat = (window as any).__activeMaterial;
      // grail item → calc golden aid-card (navigateToItem), NOT a material card
      od('Harlequin Crest (Shako)');
      const aid = document.querySelector('#item-detail .aid-card');
      const stillMat = document.querySelector('#item-detail .material-card');
      return {
        isFn: typeof od,
        matCardShown: !!matCard,
        matNameContains: /Key of Destruction/.test(matName),
        activeMatSet: activeMat === 'Key of Destruction',
        grailAidShown: !!aid,
        grailNotMaterial: !stillMat,
      };
    });
    expect(r.isFn).toBe('function');
    expect(r.matCardShown).toBe(true);
    expect(r.matNameContains).toBe(true);
    expect(r.activeMatSet).toBe(true);
    expect(r.grailAidShown).toBe(true);
    expect(r.grailNotMaterial).toBe(true);
  });

  test('closeDrop + ESC dismiss the material card', async ({ page }) => {
    const afterClose = await page.evaluate(() => {
      (window as any).openDrop('Annihilus');
      (window as any).closeDrop();
      return {
        gone: !document.querySelector('#item-detail .material-card'),
        cleared: !(window as any).__activeMaterial,
      };
    });
    expect(afterClose.gone).toBe(true);
    expect(afterClose.cleared).toBe(true);
    // ESC path
    await page.evaluate(() => (window as any).openDrop('Annihilus'));
    expect(await page.locator('#item-detail .material-card').count()).toBe(1);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(120);
    expect(await page.locator('#item-detail .material-card').count()).toBe(0);
    expect(await page.evaluate(() => !!(window as any).__activeMaterial)).toBe(false);
  });

  test('feeds-into badge on a boss card is clickable and opens the material card (real UI flow)', async ({ page }) => {
    await page.evaluate(() => (window as any).openBossDetail('countess'));
    await page.waitForTimeout(300);
    // Countess feeds Key of Terror → that badge must be clickable
    const badge = page.locator('.feeds-into-strip .fi-clickable', { hasText: 'Key of Terror' }).first();
    await expect(badge).toBeVisible();
    await badge.click();
    await page.waitForTimeout(300);
    const card = page.locator('#item-detail .material-card');
    await expect(card).toBeVisible();
    await expect(card.locator('.gic-name')).toContainText('Key of Terror');
    await expect(card).not.toContainText('undefined');
  });

  test('feeds-into labels that resolve to a material (Colossal Ancient Statue, Key of Terror) become clickable badges', async ({ page }) => {
    const r = await page.evaluate(() => {
      const strip = (window as any).feedsIntoStripHtml([
        { icon: '👑', tone: 'ancient', label: 'Colossal Ancient Statue', fr: 'Colossal Summit' },
        { icon: '🔑', tone: 'key', label: 'Key of Terror', fr: 'Uber Tristram' },
      ]);
      const div = document.createElement('div'); div.innerHTML = strip;
      const badges = [...div.querySelectorAll('.fi-badge')];
      return {
        ancientClickable: badges[0].classList.contains('fi-clickable'),
        ancientHasOnclick: !!badges[0].getAttribute('onclick'),
        keyClickable: badges[1].classList.contains('fi-clickable'),
        keyHasOnclick: /openDrop\('Key of Terror'\)/.test(badges[1].getAttribute('onclick') || ''),
      };
    });
    expect(r.ancientClickable).toBe(true);
    expect(r.ancientHasOnclick).toBe(true);
    expect(r.keyClickable).toBe(true);
    expect(r.keyHasOnclick).toBe(true);
  });

  test('each Sunder charm card has a "What it does" section describing the immunity-break mechanic', async ({ page }) => {
    const r = await page.evaluate(() => {
      const html = (window as any).materialDetailHtml;
      const fm = (window as any).findMaterial;
      const charms = ['Bone Break','Black Cleft','Crack of the Heavens','Cold Rupture','Flame Rift','Rotting Fissure'];
      return charms.map((n) => {
        const card = html(n);
        const m = fm(n);
        return {
          n,
          catKey: m ? m.catKey : null,
          hasWhatItDoes: /What it does/.test(card),
          describesSunder: /Sunders [A-Z]+ immunity/.test(card),
          mentionsFloor: /~95% resist/.test(card),
          noUndef: !/undefined/.test(card),
        };
      });
    });
    for (const c of r) {
      expect(c.catKey, c.n).toBe('sunder');
      expect(c.hasWhatItDoes, c.n).toBe(true);
      expect(c.describesSunder, c.n).toBe(true);
      expect(c.mentionsFloor, c.n).toBe(true);
      expect(c.noUndef, c.n).toBe(true);
    }
    // and the section surfaces in the real openDrop UI flow
    await page.evaluate(() => (window as any).openDrop('Bone Break'));
    await page.waitForTimeout(200);
    const card = page.locator('#item-detail .material-card');
    await expect(card).toBeVisible();
    await expect(card).toContainText('What it does');
    await expect(card).toContainText('Sunders PHYSICAL immunity');
    await expect(card).not.toContainText('undefined');
  });

  test('no console errors across the material-card flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => {
      (window as any).openDrop('Key of Destruction');
      (window as any).openDrop('Northern Worldstone Shard');
      (window as any).openDrop('Annihilus');
      (window as any).closeDrop();
    });
    await page.waitForTimeout(200);
    expect(errors).toEqual([]);
  });
});
