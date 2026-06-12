import { test, expect } from '@playwright/test';
import * as path from 'path';
import { ENDGAME_RELICS_TOTAL } from './_data_locks';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v80 — the endgame "relic" pass. Two deliverables:
//  1. A dedicated top-level "endgame" tab — "The Road to the Hellfire Torch" — a
//     visual storyline flow (3 keys → mini-uber portals → 3 organs → Uber Tristram
//     → Hellfire Torch) with the Diablo Clone→Annihilus and Colossal→Jewels side
//     paths. Every node routes to its real card via openDrop / switchTab.
//  2. Site-wide SPECIAL emphasis on the pinnacle drops — Pandemonium keys, Uber
//     organs, Sunder charms, Torch, Annihilus, Colossal Jewels get a shared gold
//     pulse (.endgame-relic) wherever they appear, applied centrally by keying off
//     each element's openDrop() target (markEndgameRelics, no fabricated data). The
//     boss/level id card it falls from carries an upgraded SIGNATURE-DROP banner.
// The Events tab + Uber Boss ID Cards structure are intentionally left untouched.
test.describe('v80 endgame relics + Road-to-the-Torch tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('the relic set + helpers are exposed and honest (every name is a real openDrop target)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const S = [...((window as any).ENDGAME_RELICS as Set<string>)];
      // every relic name must already be a real, wired openDrop() target in the DOM —
      // i.e. an actual in-game drop the app routes, not an invented name.
      const hasLink = (n: string) =>
        [...document.querySelectorAll('[onclick*="openDrop"]')].some((el) => {
          const oc = (el.getAttribute('onclick') || '').replace(/\\/g, '');
          return oc.indexOf("openDrop('" + n + "')") !== -1;
        });
      const resolvable = hasLink;
      return {
        size: S.length,
        fns: ['markEndgameRelics', 'isEndgameRelic', 'renderEndgameRoad'].map((f) => typeof (window as any)[f]),
        hasKeys: ['Key of Terror', 'Key of Hate', 'Key of Destruction'].every((k) => S.includes(k)),
        hasOrgans: ["Diablo's Horn", "Mephisto's Brain", "Baal's Eye"].every((k) => S.includes(k)),
        hasTorchAnniJewels: ['Hellfire Torch', 'Annihilus', 'Colossal Ancient Jewels'].every((k) => S.includes(k)),
        hasSunders: ['Bone Break', 'Black Cleft', 'Crack of the Heavens', 'Cold Rupture', 'Flame Rift', 'Rotting Fissure'].every((k) => S.includes(k)),
        allResolvable: S.every(resolvable),
        flagsTorch: (window as any).isEndgameRelic('Hellfire Torch'),
        rejectsJunk: (window as any).isEndgameRelic('Shako'),
      };
    });
    expect(r.size).toBe(ENDGAME_RELICS_TOTAL);
    expect(r.fns.every((t) => t === 'function')).toBe(true);
    expect(r.hasKeys).toBe(true);
    expect(r.hasOrgans).toBe(true);
    expect(r.hasTorchAnniJewels).toBe(true);
    expect(r.hasSunders).toBe(true);
    expect(r.allResolvable).toBe(true);
    expect(r.flagsTorch).toBe(true);
    expect(r.rejectsJunk).toBe(false);
  });

  test('the new "endgame" tab exists, activates, and renders the Road flow', async ({ page }) => {
    await expect(page.locator('.tab[data-tab="endgame"]')).toHaveCount(1);
    await page.click('.tab[data-tab="endgame"]');
    await page.waitForTimeout(150);
    const tab = page.locator('#tab-endgame');
    await expect(tab).toHaveClass(/active/);
    await expect(tab.locator('.road-hero h1')).toContainText('Hellfire Torch');
    // 6 chain nodes (3 keys + 3 organs) + the final torch
    await expect(tab.locator('.road-node')).toHaveCount(6);
    await expect(tab.locator('.road-final .rf-name')).toContainText('Hellfire Torch');
    // both pinnacle side-paths present
    await expect(tab).toContainText('Diablo Clone → Annihilus');
    await expect(tab).toContainText('Colossal Ancients → Colossal Jewels');
    // and the other-relics row (Herald + Sunders) connects the rest of the story
    await expect(tab).toContainText('Herald of Terror');
    await expect(tab).toContainText('Sunder Charms');
  });

  test('Road nodes route to their real cards (key → material card in calc)', async ({ page }) => {
    await page.click('.tab[data-tab="endgame"]');
    await page.waitForTimeout(120);
    await page.locator('#tab-endgame .road-node', { hasText: 'Key of Terror' }).first().evaluate((e: any) => e.click());
    await page.waitForTimeout(150);
    await expect(page.locator('#tab-calc')).toHaveClass(/active/);
    await expect(page.locator('#item-detail')).toContainText('Key of Terror');
  });

  test('Road nodes carry the relic glow (art + name), including the organs', async ({ page }) => {
    await page.click('.tab[data-tab="endgame"]');
    await page.waitForTimeout(150);
    const r = await page.evaluate(() => {
      const nodes = [...document.querySelectorAll('#tab-endgame .road-node')] as HTMLElement[];
      const torch = document.querySelector('#tab-endgame .road-final') as HTMLElement;
      return {
        allGlow: nodes.every((n) => n.classList.contains('endgame-relic')),
        organGlow: !!nodes.find((n) => /Diablo's Horn/.test(n.textContent || ''))?.classList.contains('endgame-relic'),
        torchGlow: torch.classList.contains('endgame-relic'),
      };
    });
    expect(r.allGlow).toBe(true);
    expect(r.organGlow).toBe(true);
    expect(r.torchGlow).toBe(true);
  });

  test('site-wide: the events keys/organ openDrop links are tagged .endgame-relic', async ({ page }) => {
    const r = await page.evaluate(() => {
      const find = (name: string) =>
        [...document.querySelectorAll('[onclick*="openDrop"]')].find((el) => {
          const oc = (el.getAttribute('onclick') || '').replace(/\\/g, '');
          return oc.indexOf("openDrop('" + name + "')") !== -1;
        }) as HTMLElement | undefined;
      const check = (name: string) => { const el = find(name); return { found: !!el, glow: !!el && el.classList.contains('endgame-relic') }; };
      // a non-relic openDrop link must NOT be tagged (proves it is selective)
      const sunder = find('Cold Rupture');
      const nonRelic = [...document.querySelectorAll('[onclick*="openDrop"]')].find((el) => {
        const oc = (el.getAttribute('onclick') || '').replace(/\\/g, '');
        return oc.indexOf("openDrop('Essence of Hatred')") !== -1;
      }) as HTMLElement | undefined;
      return {
        terror: check('Key of Terror'),
        organ: check("Mephisto's Brain"),
        sunderGlow: !!sunder && sunder.classList.contains('endgame-relic'),
        nonRelicTagged: !!nonRelic && nonRelic.classList.contains('endgame-relic'),
      };
    });
    expect(r.terror.found).toBe(true);
    expect(r.terror.glow).toBe(true);
    expect(r.organ.found).toBe(true);
    expect(r.organ.glow).toBe(true);
    expect(r.sunderGlow).toBe(true);
    expect(r.nonRelicTagged).toBe(false);
  });

  test('boss id card carries the upgraded SIGNATURE-DROP banner (Countess → Key of Terror, with art + glow)', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).renderBossDetailCard('countess');
      const panel = document.getElementById('boss-detail-panel')!;
      const sig = panel.querySelector('.sig-drop') as HTMLElement | null;
      return {
        present: !!sig,
        isRelic: !!sig && sig.classList.contains('endgame-relic'),
        hasArt: !!sig && !!sig.querySelector('.sig-art .d2art-img'),
        badge: (sig?.querySelector('.sig-badge')?.textContent || '').trim(),
        name: (sig?.querySelector('.sig-name')?.textContent || '').trim(),
        routesTo: (sig?.getAttribute('onclick') || ''),
      };
    });
    expect(r.present).toBe(true);
    expect(r.isRelic).toBe(true);
    expect(r.hasArt).toBe(true);
    expect(r.badge).toMatch(/ONLY DROPS HERE/);
    expect(r.name).toMatch(/Key of Terror/);
    expect(r.routesTo).toMatch(/openDrop\('Key of Terror'\)/);
  });

  test('no console errors across tab activation + boss-card + routing', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="endgame"]');
    await page.waitForTimeout(120);
    await page.evaluate(() => { (window as any).renderBossDetailCard('nihl'); });
    await page.locator('#tab-endgame .road-node').first().evaluate((e: any) => e.click());
    await page.waitForTimeout(150);
    expect(errors).toEqual([]);
  });
});
