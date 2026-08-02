import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1554 — THE SESSIONS CROWN AND HERO, MEASURED.
//
// Konyo: "for baranars star in sessions is that really the best run? and it's a little bit too big
// visually, like it should be structured better."
//
// Both halves were fair.
//
// THE NUMBER IS RIGHT. Running the app's own path — _writeGrailFarm() exports each missing grail's
// best source at his real MF/players, /api/evrank ranks by expected hours at 50% confidence —
// Baranar's Star is #1 of 51 at 4.0h (Hell Mephisto), ahead of Bloodmoon's Light 4.2h and
// Earthshaker 4.7h. A naive raw-odds ranking says 6.4h and 40th; the naive one is the wrong one.
//
// THE LABEL OVERCLAIMED. _writeGrailFarm exports GRAIL-tier items only, so "your fastest find"
// was said over 51 of his 125 missing uniques. Umbral Disk is ~2h and is not in that universe at
// all. It now names the universe: "fastest of 51 grails".
//
// THE STRUCTURE WAS INVERTED. Measured at his real 1520px console:
//
//            before    after
//   MY HUNT    40px     23px     a running page title, and it was the largest thing on screen
//   the grail  36px     27px     the actual news
//   the ETA    38px     21px     a supporting statistic that was LARGER than its subject
//   hero box  136px    107px
//   stack     213px    176px     against a ~513px fold (v1467 records what that budget costs)
//
// name:eta went 0.95 → 1.29. The rule this pins is not the pixel values — those will move again —
// it is the ORDER: the thing he is being sent to hunt must outrank the room it is announced in.

const ORIGIN = 'http://tvd.console.test';
const UI = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

async function hero(page: any, w = 1520, h = 860) {
  await page.setViewportSize({ width: w, height: h });
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname.startsWith('/api/'), (r: any) => r.abort());
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(600);
  return page.evaluate(() => {
    document.body.dataset.view = 'sessions';
    const host = document.getElementById('hub-hero')!;
    host.className = 'hub-hero';
    host.innerHTML = '<div class="hh-main">'
      + '<div class="hh-eye"><span class="hh-dot"></span>the next grail · fastest of 51 grails</div>'
      + '<div class="hh-name">BARANAR\'S STAR</div>'
      + '<div class="hh-src">hunt at <b>Hell Mephisto</b></div></div>'
      + '<div class="hh-eta"><b>≈ 4h</b><span>to your next find</span></div>';
    const px = (sel: string) => {
      const e = document.querySelector(sel);
      return e ? Math.round(parseFloat(getComputedStyle(e).fontSize)) : 0;
    };
    const crown = document.querySelector('.hub-crown')!.getBoundingClientRect();
    const box = host.getBoundingClientRect();
    return {
      title: px('.hub-crest .hc-t'), name: px('.hh-name'), eta: px('.hh-eta b'),
      eyebrow: px('.hh-eye'), src: px('.hh-src'), etaLab: px('.hh-eta span'),
      heroH: Math.round(box.height), stackH: Math.round(box.bottom - crown.top),
      overflows: box.width < host.scrollWidth,
    };
  });
}

test.describe('v1554 — the lead outranks the room it is announced in', () => {
  test('★ THE ORDER: the grail beats the page title, and the title beats the stat', async ({ page }) => {
    const r = await hero(page);
    expect(r.name, 'the grail he is being sent to hunt must lead').toBeGreaterThan(r.title);
    expect(r.title, 'the page title must outrank the supporting number').toBeGreaterThan(r.eta);
    expect(r.name / r.eta, 'name:eta was 0.95 — two headlines competing').toBeGreaterThan(1.15);
  });

  test('★ the hero stops eating the fold', async ({ page }) => {
    const r = await hero(page);
    expect(r.heroH, 'the hero box was 136px at his console width').toBeLessThanOrEqual(115);
    expect(r.stackH, 'crown + hero together, against a ~513px fold').toBeLessThanOrEqual(190);
  });

  test('nothing in the block falls through the 13px console floor', async ({ page }) => {
    // the console is watched on a TV, not a laptop — the same rule TestV1504TypeFloor enforces
    const r = await hero(page);
    for (const [k, v] of Object.entries(r)) {
      if (['title', 'name', 'eta', 'eyebrow', 'src', 'etaLab'].includes(k)) {
        expect(v as number, k + ' is below the readable floor').toBeGreaterThanOrEqual(13);
      }
    }
  });

  test('★ the label names its universe instead of overclaiming', async () => {
    // "fastest find" over a grail-tier-only ranking is a wider claim than the data supports
    expect(UI, 'the old overclaim must be gone').not.toContain('your fastest find');
    expect(UI, 'and the universe named').toContain("fastest of '");
    expect(UI).toContain('data.ranked.length');
  });

  test('the composition still holds on a narrow console', async ({ page }) => {
    const r = await hero(page, 1024, 720);
    expect(r.name).toBeGreaterThan(r.eta);
    expect(r.overflows, 'the hero must not scroll sideways when it is squeezed').toBe(false);
    expect(r.name).toBeGreaterThanOrEqual(13);
  });

  test('and on a wide one — the clamps must not re-invert it', async ({ page }) => {
    const r = await hero(page, 2560, 1400);
    expect(r.name).toBeGreaterThan(r.title);
    expect(r.title).toBeGreaterThan(r.eta);
  });

  test('the ornament stops being taller than the box it sits in', async ({ page }) => {
    // --fs-display tops out at 150px inside a block now ~107px tall
    await hero(page);
    const r = await page.evaluate(() => {
      const host = document.getElementById('hub-hero')!;
      const cs = getComputedStyle(host, '::before');
      return { fs: parseFloat(cs.fontSize), h: host.getBoundingClientRect().height };
    });
    expect(r.fs, 'the ✦ must fit its own container').toBeLessThanOrEqual(r.h);
  });
});
