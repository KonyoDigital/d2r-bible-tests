import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v124 — unify the RoTW Pandemonium flow (events tab) under the artOr / decorateItemLogos
// architecture + add the "top 3 bind affix buffs" podium under the aura best-roll section.
// (a) Essences "From" boss cells + Pandemonium Keys "Drops From" boss cells carry
//     data-art-logo so the decorator injects the verified boss portrait (emoji fallback).
// (b) Step-1 portal table mini-uber cells + Step-4 Uber Tristram trio cells are clickable
//     and route to their golden uber ID card via jumpToUberBoss; organ cells route via openDrop.
// (c) The best-roll section gains a researched Top-3 affix podium (Extra Strong / Cursed /
//     Extra Fast — Arreat Summit mechanics). Aura section + 593-style routing untouched.
test.describe('v124 Pandemonium unify + top-3 bind-affix podium', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('Essences + Keys boss cells carry their decorated portrait with emoji fallback', async ({ page }) => {
    const bosses = ['Andariel', 'Duriel', 'Mephisto', 'Diablo', 'Baal', 'The Countess', 'The Summoner', 'Nihlathak'];
    for (const name of bosses) {
      const r = await page.evaluate((n) => {
        const el = document.querySelector(`[data-art-logo="${n}"]`);
        if (!el) return { present: false };
        const img = el.querySelector(':scope > .d2art-wrap .d2art-img') as HTMLImageElement | null;
        const fb = el.querySelector(':scope > .d2art-wrap .d2art-fallback');
        return {
          present: true,
          src: img?.getAttribute('src') || '',
          lazy: img?.getAttribute('loading') === 'lazy',
          fallback: (fb?.textContent || '').trim().length > 0,
        };
      }, name);
      expect(r.present, `${name} tagged cell present`).toBe(true);
      expect(r.src, `${name} portrait src`).toContain('diablo2.io');
      expect(r.lazy, `${name} lazy`).toBe(true);
      expect(r.fallback, `${name} emoji fallback`).toBe(true);
    }
  });

  test('Step-1 portal table mini-uber cells route to their golden uber ID card', async ({ page }) => {
    const map: Record<string, string> = { 'Lilith': 'lilith', 'Uber Duriel': 'uber-duriel', 'Uber Izual': 'izual' };
    for (const [name, id] of Object.entries(map)) {
      const onclick = await page.evaluate((n) => {
        const el = document.querySelector(`[data-art-logo="${n}"]`);
        return el?.getAttribute('onclick') || '';
      }, name);
      expect(onclick, `${name} routes to jumpToUberBoss('${id}')`).toContain(`jumpToUberBoss('${id}')`);
    }
  });

  test('Step-4 Uber Tristram trio cells route to their golden uber ID card', async ({ page }) => {
    const map: Record<string, string> = { 'Uber Mephisto': 'uber-mephisto', 'Uber Diablo': 'uber-diablo', 'Uber Baal': 'uber-baal' };
    for (const [name, id] of Object.entries(map)) {
      const onclick = await page.evaluate((n) => {
        const el = document.querySelector(`[data-art-logo="${n}"]`);
        return el?.getAttribute('onclick') || '';
      }, name);
      expect(onclick, `${name} routes to jumpToUberBoss('${id}')`).toContain(`jumpToUberBoss('${id}')`);
    }
  });

  test('clicking an Uber Tristram cell opens its uber ID card', async ({ page }) => {
    await page.evaluate(() => (window as any).jumpToUberBoss('uber-baal'));
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const card = document.getElementById('uberboss-uber-baal');
      const body = card?.querySelector('.ubc-body');
      return { exists: !!card, open: !!(body && !body.hasAttribute('hidden')) };
    });
    expect(r.exists).toBe(true);
    expect(r.open).toBe(true);
  });

  test('portal-table organ cells still route via openDrop with a decorated logo', async ({ page }) => {
    const organs = ["Diablo's Horn", "Baal's Eye", "Mephisto's Brain"];
    for (const name of organs) {
      const r = await page.evaluate((n) => {
        const els = Array.from(document.querySelectorAll(`[data-art-logo="${n}"]`));
        // at least one of these cells routes via openDrop and has a decorated portrait
        const routed = els.some((e) => (e.getAttribute('onclick') || '').includes('openDrop('));
        const arted = els.some((e) => !!e.querySelector(':scope > .d2art-wrap .d2art-img'));
        return { count: els.length, routed, arted };
      }, name);
      expect(r.count, `${name} present`).toBeGreaterThan(0);
      expect(r.routed, `${name} openDrop routed`).toBe(true);
      expect(r.arted, `${name} decorated`).toBe(true);
    }
  });

  test('the top-3 bind-affix podium renders the 3 researched affixes in order', async ({ page }) => {
    const r = await page.evaluate(() => {
      const pod = document.querySelector('#binds-bestroll .aura-top3');
      const rows = pod ? Array.from(pod.querySelectorAll('.at3-row')) : [];
      const names = rows.map((r) => (r.querySelector('.at3-name')?.textContent || '').trim());
      const tiers = rows.map((r) => (r.querySelector('.at3-tier')?.textContent || '').trim());
      return {
        exists: !!pod,
        head: (pod?.querySelector('.at3-head')?.textContent || '').toLowerCase(),
        count: rows.length,
        names,
        firstIsTop: !!(rows[0] && rows[0].classList.contains('at3-rank-1')),
        tiers,
      };
    });
    expect(r.exists).toBe(true);
    expect(r.head).toContain('top 3');
    expect(r.count).toBe(3);
    expect(r.names).toEqual(['Extra Strong', 'Cursed', 'Extra Fast']);
    expect(r.firstIsTop).toBe(true);
    expect(r.tiers[0]).toBe('S');
  });

  test('the affix model now reflects the in-game health-bar (immunities + the 8-9 line note)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const txt = document.body.textContent || '';
      return {
        inGameModel: txt.includes("What the monster's health-bar actually shows"),
        eightNine: txt.includes('8–9 lines'),
        immPhys: txt.includes('Immune to Physical'),
        immCold: txt.includes('Immune to Cold'),
        survival: txt.includes('Best survival rolls'),
        dream: txt.includes('The dream bind'),
      };
    });
    expect(r.inGameModel).toBe(true);
    expect(r.eightNine).toBe(true);
    expect(r.immPhys).toBe(true);
    expect(r.immCold).toBe(true);
    expect(r.survival).toBe(true);
    expect(r.dream).toBe(true);
  });

  test("Lister's bind ID card renders his verified in-game health-bar", async ({ page }) => {
    const r = await page.evaluate(() => {
      const b = (window as any).BIND_SU.find((x: any) => x.name === 'Lister the Tormentor');
      const html = (window as any).bindSUDetailHtml(b);
      const wrap = document.createElement('div');
      wrap.innerHTML = html;
      const bar = wrap.querySelector('.su-hpbar-sec .hpbar');
      const title = (bar?.querySelector('.hpbar-title')?.textContent || '').trim();
      const mods = bar?.querySelector('.hpbar-mods')?.textContent || '';
      const imm = bar?.querySelector('.hpbar-imm')?.textContent || '';
      return {
        present: !!bar,
        title,
        extraStrong: mods.includes('Extra Strong'),
        auraEnchanted: mods.includes('Aura Enchanted'),
        immPhys: imm.includes('Immune to Physical'),
        immFire: imm.includes('Immune to Fire'),
        verified: (wrap.querySelector('.su-hpbar-sec .hpbar-cap')?.textContent || '').includes('screenshot-verified'),
      };
    });
    expect(r.present).toBe(true);
    expect(r.title).toBe('Lister the Tormentor');
    expect(r.extraStrong).toBe(true);
    expect(r.auraEnchanted).toBe(true);
    expect(r.immPhys).toBe(true);
    expect(r.immFire).toBe(true);
    expect(r.verified).toBe(true);
  });

  test("a still-derived card (Bremm Sparkfist) shows type + rerollable line but NO fabricated immunities", async ({ page }) => {
    const r = await page.evaluate(() => {
      const b = (window as any).BIND_SU.find((x: any) => x.name === 'Bremm Sparkfist');
      const html = (window as any).bindSUDetailHtml(b);
      const wrap = document.createElement('div');
      wrap.innerHTML = html;
      const bar = wrap.querySelector('.su-hpbar-sec .hpbar');
      const mods = bar?.querySelector('.hpbar-mods')?.textContent || '';
      const immEl = bar?.querySelector('.hpbar-imm');
      return {
        present: !!bar,
        demon: mods.includes('Demon'),
        auraEnchanted: mods.includes('Aura Enchanted'),
        noImmLine: !immEl, // immunities vary per spawn → must NOT be fabricated
        cap: (wrap.querySelector('.su-hpbar-sec .hpbar-cap')?.textContent || ''),
      };
    });
    expect(r.present).toBe(true);
    expect(r.demon).toBe(true);
    expect(r.auraEnchanted).toBe(true);
    expect(r.noImmLine).toBe(true);
    expect(r.cap).toContain("vary per spawn");
  });

  test("Hephasto's bind card renders his screenshot-verified TZ spawn (Fanaticism + Physical immune)", async ({ page }) => {
    const r = await page.evaluate(() => {
      const b = (window as any).BIND_SU.find((x: any) => x.name === 'Hephasto the Armorer');
      const html = (window as any).bindSUDetailHtml(b);
      const wrap = document.createElement('div');
      wrap.innerHTML = html;
      const bar = wrap.querySelector('.su-hpbar-sec .hpbar');
      const title = (bar?.querySelector('.hpbar-title')?.textContent || '').trim();
      const mods = bar?.querySelector('.hpbar-mods')?.textContent || '';
      const imm = bar?.querySelector('.hpbar-imm')?.textContent || '';
      const cap = wrap.querySelector('.su-hpbar-sec .hpbar-cap')?.textContent || '';
      return {
        present: !!bar,
        title,
        spectralHit: mods.includes('Spectral Hit'),
        extraStrong: mods.includes('Extra Strong'),
        stoneSkin: mods.includes('Stone Skin'),
        extraFast: mods.includes('Extra Fast'),
        auraEnchanted: mods.includes('Aura Enchanted'),
        immPhys: imm.includes('Immune to Physical'),
        // verified, but honestly labelled as a per-game-variable random-aura spawn
        verified: cap.includes('screenshot-verified'),
        fanaticism: cap.includes('Fanaticism'),
        reRolls: cap.includes('re-roll'),
      };
    });
    expect(r.present).toBe(true);
    expect(r.title).toBe('Hephasto the Armorer');
    expect(r.spectralHit).toBe(true);
    expect(r.extraStrong).toBe(true);
    expect(r.stoneSkin).toBe(true);
    expect(r.extraFast).toBe(true);
    expect(r.auraEnchanted).toBe(true);
    expect(r.immPhys).toBe(true);
    expect(r.verified).toBe(true);
    expect(r.fanaticism).toBe(true);
    expect(r.reRolls).toBe(true);
  });

  test('the top-3 immunity section renders 3 ranked profiles, phys+fire is #1/S', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sec = document.getElementById('binds-immroll');
      const pod = sec?.querySelector('.aura-top3');
      const rows = pod ? Array.from(pod.querySelectorAll('.at3-row')) : [];
      const names = rows.map((x) => (x.querySelector('.at3-name')?.textContent || '').replace(/\s+/g, ' ').trim());
      return {
        exists: !!sec,
        head: (pod?.querySelector('.at3-head')?.textContent || '').toLowerCase(),
        count: rows.length,
        names,
        firstIsTop: !!(rows[0] && rows[0].classList.contains('at3-rank-1')),
        firstTier: (rows[0]?.querySelector('.at3-tier')?.textContent || '').trim(),
      };
    });
    expect(r.exists).toBe(true);
    expect(r.head).toContain('immunity');
    expect(r.count).toBe(3);
    expect(r.names[0]).toContain('Immune to Physical');
    expect(r.names[0]).toContain('Immune to Fire');
    expect(r.names[1]).toContain('Immune to Cold');
    expect(r.names[2]).toContain('Immune to Lightning');
    expect(r.firstIsTop).toBe(true);
    expect(r.firstTier).toBe('S');
  });

  test('no console errors loading the events tab + opening an uber card', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate(() => (window as any).jumpToUberBoss('lilith'));
    await page.waitForTimeout(120);
    await page.evaluate(() => (window as any).decorateItemLogos());
    expect(errs).toEqual([]);
  });
});
