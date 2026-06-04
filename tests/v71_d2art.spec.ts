import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v71 — d2art: real item/boss/rune artwork hotlinked from diablo2.io's avatar gallery, with a
// guaranteed emoji fallback so a card can NEVER render a broken-image box.
//   1. D2IO_ART is a top-level global map {name -> diablo2.io gallery URL}. Every URL was probed
//      live (HTTP 200 + image content-type) before shipping — zero fabricated/guessed URLs.
//   2. artOr(name, fallbackHtml, size) returns an <img> when we have a verified URL, else the
//      fallback markup verbatim. The <img> has an onerror that swaps to the emoji on load failure.
//   3. The item ID-card, boss ID-card, and rune-stash cells render the art (or fall back cleanly).
test.describe('v71 d2art artwork layer', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('D2IO_ART is a verified global map and artUrl/artOr are exposed helpers', async ({ page }) => {
    const r = await page.evaluate(() => {
      const m = (window as any).D2IO_ART;
      const names = m ? Object.keys(m) : [];
      return {
        type: typeof m,
        len: names.length,
        allDiablo2io: names.every((n) => /^https:\/\/diablo2\.io\/(images\/avatars\/gallery|styles\/zulu\/theme\/images\/items)\//.test(m[n])),
        allImageExt: names.every((n) => /\.(png|gif|jpe?g)$/i.test(m[n])),
        encoded: names.every((n) => !/ /.test(m[n])),           // spaces URL-encoded, no raw spaces
        hasItem: !!m['Arachnid Mesh'],
        hasRune: !!m['Ist'],
        hasBoss: !!m['The Countess'],
        fns: ['artUrl', 'artOr'].map((f) => typeof (window as any)[f]),
        // artUrl returns null for an unknown name, the URL for a known one
        unknownNull: (window as any).artUrl('Totally Not A Real Item ZZZ') === null,
        knownUrl: (window as any).artUrl('Ist'),
      };
    });
    expect(r.type).toBe('object');
    expect(r.len).toBeGreaterThanOrEqual(150);
    expect(r.allDiablo2io).toBe(true);
    expect(r.allImageExt).toBe(true);
    expect(r.encoded).toBe(true);
    expect(r.hasItem).toBe(true);
    expect(r.hasRune).toBe(true);
    expect(r.hasBoss).toBe(true);
    expect(r.fns.every((t) => t === 'function')).toBe(true);
    expect(r.unknownNull).toBe(true);
    expect(r.knownUrl).toMatch(/runeIst_icon\.png$/);
  });

  test('artOr emits an <img> with onerror fallback for mapped names, raw fallback for unmapped', async ({ page }) => {
    const r = await page.evaluate(() => ({
      mapped: (window as any).artOr('Ist', '<span class="x">FB</span>', 'sm'),
      unmapped: (window as any).artOr('No Such Thing 999', '<span class="x">FB</span>', 'lg'),
    }));
    // mapped → real <img> from diablo2.io, carries the alt + an onerror that reveals the fallback span
    expect(r.mapped).toMatch(/<img[^>]+class="d2art-img"/);
    expect(r.mapped).toMatch(/src="https:\/\/diablo2\.io\/images\/avatars\/gallery\//);
    expect(r.mapped).toMatch(/onerror="this\.parentNode\.classList\.add\('d2art-failed'\)"/);
    expect(r.mapped).toContain('d2art-fallback');
    expect(r.mapped).toContain('FB');                    // fallback still embedded for the error path
    // unmapped → just the fallback markup, no <img>
    expect(r.unmapped).toBe('<span class="x">FB</span>');
  });

  test('the item ID-card renders real artwork for a mapped item', async ({ page }) => {
    await page.evaluate(() => (window as any).renderItemDetailCard('Arachnid Mesh'));
    await page.waitForTimeout(150);
    const r = await page.evaluate(() => {
      const panel = document.getElementById('item-detail-panel');
      const img = panel?.querySelector('.gic-header .d2art-img') as HTMLImageElement | null;
      return {
        hasImg: !!img,
        src: img?.getAttribute('src') || '',
        // a fallback emoji span is present (revealed by onerror only if the image fails to load)
        hasFallback: !!img?.parentElement?.querySelector('.d2art-fallback'),
      };
    });
    expect(r.hasImg).toBe(true);
    expect(r.src).toMatch(/^https:\/\/diablo2\.io\/(images\/avatars\/gallery|styles\/zulu\/theme\/images\/items)\//);
    expect(r.hasFallback).toBe(true);
  });

  test('an UNmapped item keeps its emoji (no broken image)', async ({ page }) => {
    // find an UNmapped item that renders a real gic item-card (skip keys/organs that route to
    // material cards), then assert it falls back to the emoji with no <img> element at all
    const r = await page.evaluate(() => {
      const m = (window as any).D2IO_ART;
      const panel = document.getElementById('item-detail-panel');
      let unmapped = '', emoji = false, hasImg = true;
      for (const n of (ITEMS as any[]).map((x) => x.n)) {
        if (m[n]) continue;
        (window as any).renderItemDetailCard(n);
        const e = !!panel?.querySelector('.gic-header .gic-emoji');
        if (e) { unmapped = n; emoji = true; hasImg = !!panel?.querySelector('.gic-header .d2art-img'); break; }
      }
      return { unmapped, emoji, hasImg };
    });
    expect(r.unmapped).toBeTruthy();
    expect(r.emoji).toBe(true);      // emoji still shown
    expect(r.hasImg).toBe(false);    // and no image element at all
  });

  test('the boss ID-card renders artwork for a mapped boss (The Countess)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const b = (BOSSES as any[]).find((x) => x.name === 'The Countess');
      (window as any).renderBossDetailCard(b.id);
      const panel = document.getElementById('boss-detail-panel');
      const img = panel?.querySelector('.gbc-header .d2art-img') as HTMLImageElement | null;
      return { hasImg: !!img, src: img?.getAttribute('src') || '' };
    });
    expect(r.hasImg).toBe(true);
    expect(r.src).toContain('diablo2.io/images/avatars/gallery/');
    expect(r.src).toMatch(/Countess/);
  });

  test('rune-stash cells show rune icons for mapped runes, name-only for unmapped (Jah)', async ({ page }) => {
    await page.click('.tab[data-tab="runes"]');
    await page.waitForTimeout(200);
    const r = await page.evaluate(() => {
      const istCell = document.querySelector('.rune-stash-cell[data-rune="Ist"]');
      const jahCell = document.querySelector('.rune-stash-cell[data-rune="Jah"]');
      return {
        istImg: !!istCell?.querySelector('.d2art-img'),
        istSrc: (istCell?.querySelector('.d2art-img') as HTMLImageElement)?.getAttribute('src') || '',
        jahImg: !!jahCell?.querySelector('.d2art-img'),   // Jah was unverified → no icon, name only
        jahName: jahCell?.querySelector('.rs-name')?.textContent?.trim(),
      };
    });
    expect(r.istImg).toBe(true);
    expect(r.istSrc).toMatch(/runeIst_icon\.png$/);
    expect(r.jahImg).toBe(false);
    expect(r.jahName).toBe('Jah');
  });

  test('the material detail card renders artwork for a mapped sunder (Bone Break)', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openDrop('Bone Break');
      const panel = document.getElementById('item-detail');
      const img = panel?.querySelector('.material-card .gic-header .d2art-img') as HTMLImageElement | null;
      return { hasImg: !!img, src: img?.getAttribute('src') || '' };
    });
    expect(r.hasImg).toBe(true);
    expect(r.src).toContain('diablo2.io/styles/zulu/theme/images/items/');
    expect(r.src).toMatch(/bonebreakcharm/);
  });

  test('the rune detail card renders the rune icon for a mapped rune (Ist)', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openDrop('Ist');
      const panel = document.getElementById('item-detail');
      const img = panel?.querySelector('.rune-card .gic-header .d2art-img') as HTMLImageElement | null;
      return { hasImg: !!img, src: img?.getAttribute('src') || '' };
    });
    expect(r.hasImg).toBe(true);
    expect(r.src).toMatch(/runeIst_icon\.png$/);
  });

  test('the calc grid tiles show art thumbnails for mapped items', async ({ page }) => {
    await page.click('.tab[data-tab="calc"]');
    await page.waitForTimeout(200);
    const r = await page.evaluate(() => {
      const tile = document.querySelector('#item-grid .item-tile[data-name="Arachnid Mesh"]');
      const img = tile?.querySelector('.item-tile-row .d2art-img') as HTMLImageElement | null;
      // tiles still hold their name+tc text alongside the art
      return {
        hasImg: !!img,
        src: img?.getAttribute('src') || '',
        name: tile?.querySelector('.item-tile-name')?.textContent?.trim() || '',
        lazy: img?.getAttribute('loading') || '',
      };
    });
    expect(r.hasImg).toBe(true);
    expect(r.src).toContain('diablo2.io/');
    expect(r.name).toBe('Arachnid Mesh');
    expect(r.lazy).toBe('lazy');     // grid art is lazy-loaded, not a load-time storm
  });

  test('calc grid tiles are flat siblings — no recursive nesting (regression)', async ({ page }) => {
    // the art-thumbnail wrapper once dropped a </div>, so every .item-tile nested
    // inside the previous one (cascading card-in-card). Each tile must be a DIRECT
    // child of #item-grid, and no tile may contain another .item-tile.
    await page.click('.tab[data-tab="calc"]');
    await page.waitForTimeout(250);
    const r = await page.evaluate(() => {
      const grid = document.getElementById('item-grid')!;
      const tiles = [...grid.querySelectorAll('.item-tile')];
      const directChildren = [...grid.children].filter((c) => c.classList.contains('item-tile')).length;
      const nested = tiles.filter((t) => t.querySelector('.item-tile')).length;
      return { total: tiles.length, directChildren, nested };
    });
    expect(r.total).toBeGreaterThan(50);
    expect(r.directChildren).toBe(r.total); // every tile is a direct grid child
    expect(r.nested).toBe(0);               // no tile swallows another
  });

  test('the boss ID-card renders artwork for Baal and Pindleskin (newly mapped)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const out: any = {};
      for (const nm of ['Baal', 'Pindleskin']) {
        const b = (BOSSES as any[]).find((x) => x.name === nm);
        (window as any).renderBossDetailCard(b.id);
        const panel = document.getElementById('boss-detail-panel');
        const img = panel?.querySelector('.gbc-header .d2art-img') as HTMLImageElement | null;
        out[nm] = img?.getAttribute('src') || '';
      }
      return out;
    });
    expect(r.Baal).toMatch(/baal-opt_graphic\.png$/);
    expect(r.Pindleskin).toMatch(/reanimatedhorde-opt_graphic\.png$/);
  });

  test('no console errors when opening art-bearing cards', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => {
      (window as any).renderItemDetailCard('Arachnid Mesh');
      const b = (BOSSES as any[]).find((x) => x.name === 'The Countess');
      (window as any).renderBossDetailCard(b.id);
    });
    await page.click('.tab[data-tab="runes"]');
    await page.waitForTimeout(200);
    // network 404s on hotlinked images are NOT console errors; assert no JS errors
    expect(errors).toEqual([]);
  });
});
