// v191 — Windows deep-audit quick-wins lockdown.
// (1) Content fixes verified against the app's OWN ITEM_TIP props (zero fabrication):
//     Stormshield +60 cold res (not +35, no CBF), Coif of Glory "Light Strike" purged,
//     Griffon's +1 ALL skills, Smith mlvl 79, HotO run-on split, fixed-aura example
//     swapped off Hephasto (his aura is random — app states it in 5 places).
// (2) Routing: runes + gems are first-class in the global search palette (they had
//     clickable ID cards but were absent from the index — "Vex" returned no match).
// (3) Binds: Lister/Hephasto bind ID cards carry the aura-visibility disclaimer +
//     Lister's hunt protocol (research ship 2026-06-12, sources in commit v190).
import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v191 audit quick-wins', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2500);
  });

  // Poll-based: fixed 150/300ms waits flake under 4-worker suite load (caught on the
  // 2026-06-12 full run — passed isolated, failed in-suite). waitForFunction instead.
  const paletteHit = async (page: any, term: string) => {
    await page.evaluate(() => (window as any)._v42_openPalette && (window as any)._v42_openPalette());
    await page.locator('#v42-palette-input').fill(term);
    await page.waitForFunction(
      () => document.querySelectorAll('#v42-palette-list .v42-pal-item .v42-pal-label').length > 0,
      undefined, { timeout: 8000 }
    ).catch(() => {});
    const labels = await page.evaluate(() =>
      Array.from(document.querySelectorAll('#v42-palette-list .v42-pal-item .v42-pal-label'))
        .map((e: any) => e.textContent.trim()));
    await page.keyboard.press('Escape');
    await page.waitForTimeout(120);
    return labels as string[];
  };

  test('runes are globally searchable and route to their rune card', async ({ page }) => {
    expect((await paletteHit(page, 'vex')).some(l => l.startsWith('Vex Rune'))).toBe(true);
    expect((await paletteHit(page, 'ber')).some(l => l.startsWith('Ber Rune'))).toBe(true);
    // The PALETTE executes on bubbling click → data-v42Idx → v42Execute → action
    // fires in a setTimeout(80). (mousedown is the GSEARCH dropdown's convention —
    // v140 gotcha — NOT the palette's; confirmed against the wiring at the
    // #v42-palette-list click listener.)
    await page.evaluate(() => {
      (window as any)._v42_openPalette();
      const input = document.querySelector('#v42-palette-input') as HTMLInputElement;
      input.value = 'vex';
      input.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await page.waitForFunction(() =>
      [...document.querySelectorAll('#v42-palette-list .v42-pal-item .v42-pal-label')]
        .some(e => (e.textContent || '').trim().startsWith('Vex Rune')), undefined, { timeout: 8000 });
    const found = await page.evaluate(() => {
      const it = [...document.querySelectorAll('#v42-palette-list .v42-pal-item')]
        .find(e => (e.querySelector('.v42-pal-label')?.textContent || '').trim().startsWith('Vex Rune')) as HTMLElement;
      if (!it) return false;
      it.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      return true;
    });
    expect(found).toBe(true);
    await page.waitForTimeout(800); // action runs in a setTimeout(80) after palette close
    const card = await page.evaluate(() => document.querySelector('#item-detail .rune-card')?.textContent || '');
    expect(card).toContain('Vex');
  });

  test('all 33 runes + all 35 gem variants are in the palette index', async ({ page }) => {
    const counts = await page.evaluate(() => {
      (window as any)._v42_openPalette();
      const labels = (q: string) => {
        const input = document.querySelector('#v42-palette-input') as HTMLInputElement;
        input.value = q;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        return [...document.querySelectorAll('#v42-palette-list .v42-pal-item .v42-pal-label')]
          .map(e => (e.textContent || '').trim());
      };
      return {
        zod: labels('zod rune').some(l => l.startsWith('Zod Rune')),
        el: labels('el rune').some(l => l.startsWith('El Rune')),
        pskull: labels('perfect skull').some(l => l.startsWith('Perfect Skull')),
        chippedAme: labels('chipped amethyst').some(l => l.startsWith('Chipped Amethyst')),
      };
    });
    expect(counts.zod).toBe(true);
    expect(counts.el).toBe(true);
    expect(counts.pskull).toBe(true);
    expect(counts.chippedAme).toBe(true);
  });

  test('gems searchable and route to the gem card', async ({ page }) => {
    expect((await paletteHit(page, 'perfect topaz')).some(l => l.startsWith('Perfect Topaz'))).toBe(true);
    expect((await paletteHit(page, 'flawless skull')).some(l => l.startsWith('Flawless Skull'))).toBe(true);
  });

  test('content fixes: Stormshield +60 cold res / no CBF; Coif of Glory has no fabricated "Light Strike"; Griffon ALL skills', async ({ page }) => {
    const r = await page.evaluate(() => {
      const txt = document.body.textContent || '';
      return {
        storm60: txt.includes('+60 cold res'),
        stormStale: txt.includes('+35 cold res'),
        lightStrike: txt.includes('Light Strike'),
        griffonSorc: /\+1 sorc skills/.test(txt),
      };
    });
    expect(r.storm60).toBe(true);
    expect(r.stormStale).toBe(false);
    expect(r.lightStrike).toBe(false);
    expect(r.griffonSorc).toBe(false);
  });

  test('Smith mlvl unified to 79; fixed-aura example no longer cites Hephasto', async ({ page }) => {
    const r = await page.evaluate(() => {
      const bind = eval('BIND_SU').find((b: any) => b.name === 'The Smith');
      const su = eval('SUPER_UNIQUES').find((b: any) => b.name === 'The Smith');
      const txt = document.body.textContent || '';
      return {
        bindMlvl: bind?.mlvl, suMlvl: su?.mlvl,
        fixedExample: txt.includes('Fixed aura (The Smith, Lister, etc.)'),
        staleExample: txt.includes('Fixed aura (Hephasto, Lister, etc.)'),
      };
    });
    expect(r.bindMlvl).toBe(79);
    expect(r.suMlvl).toBe(79);
    expect(r.fixedExample).toBe(true);
    expect(r.staleExample).toBe(false);
  });

  test('Heart of the Oak RUNEWORD_TIP run-on split into two stats', async ({ page }) => {
    const lines = await page.evaluate(() => (window as any).RUNEWORD_TIP['Heart of the Oak'].l as string[]);
    expect(lines).toContain('+100 To Attack Rating Against Demons');
    expect(lines).toContain('Adds 3-14 Cold Damage, 3 sec. Duration');
    expect(lines.some(l => l.includes('DemonsAdds'))).toBe(false);
  });

  test('Lister + Hephasto bind cards render the aura-visibility disclaimer; Lister also the hunt protocol', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openBindSUByName('Lister the Tormentor');
      const lister = document.getElementById('bindsu-detail')?.textContent || '';
      (window as any).openBindSUByName('Hephasto the Armorer');
      const heph = document.getElementById('bindsu-detail')?.textContent || '';
      return {
        listerSight: lister.includes('AURA VISIBILITY'),
        listerBlindPart: lister.includes('ONLY blind part'),
        listerHunt: lister.includes('Hunt protocol'),
        listerStone: lister.includes('Immune to Physical, the tank-maker'),
        hephSight: heph.includes('AURA VISIBILITY'),
        hephAlways: heph.includes('ALWAYS Aura Enchanted'),
        hephNoHunt: !heph.includes('Hunt protocol'),
      };
    });
    expect(r.listerSight).toBe(true);
    expect(r.listerBlindPart).toBe(true);
    expect(r.listerHunt).toBe(true);
    expect(r.listerStone).toBe(true);
    expect(r.hephSight).toBe(true);
    expect(r.hephAlways).toBe(true);
    expect(r.hephNoHunt).toBe(true);
  });
});
