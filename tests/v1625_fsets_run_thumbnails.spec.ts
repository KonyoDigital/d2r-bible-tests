import { test, expect } from './_net_stub';
import * as path from 'path';

// v1625 — ITEM 4: THE F-SETS RUN WEARS ITS BOSS TOO, THROUGH THE SAME HELPER.
//
// Konyo: "same for quick wins here in the tab F-SETS should match the upgraded version we just
// improved now to match the same logic in coding too".
//
// v1624 fixed this on the uniques side. F·Sets was still on the arbitrary picture. MEASURED on
// 6296e26 (v1624) BEFORE the fix, with a fresh profile:
//
//   #tab-fsets .f-card.f-pipe            = 3 cards  ("NM Pindleskin", "Hell TZ Pindleskin",
//                                                    "No verified farm source yet")
//   #tab-fsets .f-card.f-pipe .f-runart  = 0        (no control at all — an inert picture)
//   card 1 thumbnail                     = art/hd_amulet.png
//   card 1 first chip                    = "Tal Rasha's Adjudication (amulet)"
//   window._runBossArt('pindle',…).url   = art/reanimatedhorde-opt_graphic.png
//
// i.e. the picture was the FIRST SET PIECE in the drop list — the amulet — not the boss the row is
// about. bible.html:35347 built it with `art((g.items[0]?g.items[0].name:'')…,'🎯')`. Every
// assertion below is written so that expression FAILS it: the thumbnail must resolve to
// _runBossArt's url (reanimatedhorde), and hd_amulet.png is not that.
//
// THE HIGHEST-VALUE ASSERTION IS "NO SECOND COPY". The temptation here is to paste _runArtThumb
// next to the sets renderer; that is the drift v1615 spent a whole version deleting. Both call
// sites live inside the SAME IIFE (opens bible.html:34075), so the sets side can legitimately call
// the LEXICAL `_runArtThumb` and never touch `window._runArtThumb` — a window spy would then read
// zero for a perfectly correct implementation. So the load-bearing proofs of single-sourcing are:
//   (a) the definition appears EXACTLY ONCE in the shipped script text, and
//   (b) the two thumbnails are byte-identical markup once the boss id is normalised out.
// The window spy / in-page re-invocation is corroborating evidence and is REPORTED, not required —
// see the note in that test. A pasted copy trips (a); a drifted copy trips (b).
//
// Source-text checks use ^-anchored multiline regexes on purpose: a comment that QUOTES the old
// code is textually identical to the old code, and we have shipped that mistake before.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
// mutation-checking points this at a doctored copy; unset in CI and in normal local runs.
const TARGET = process.env.BIBLE_HTML ? 'file://' + path.resolve(process.env.BIBLE_HTML) : URL;

const NO_RUN = 'No verified farm source yet';

async function fsets(page: any) {
  await page.goto(TARGET);
  await page.waitForTimeout(2800);
  await page.evaluate(() => { try { (window as any).switchTab('fsets'); } catch (e) {} });
  await page.waitForTimeout(1800);
}

/* every run card on the sets board, with the boss id read from the card's OWN "📜 boss card"
   button — a source independent of the thumbnail we are judging. */
function readRuns() {
  const abs = (u: string) => { try { return new URL(u, location.href).href; } catch (e) { return u; } };
  return Array.from(document.querySelectorAll('#tab-fsets .f-card.f-pipe')).map((c: any) => {
    const title = (c.querySelector('.f-rwbig') as any)?.textContent?.trim() || '';
    const btn: any = Array.from(c.querySelectorAll('.f-cta .f-btn'))
      .find((b: any) => /openBossDetail/.test(b.getAttribute('onclick') || ''));
    const bossId = ((btn?.getAttribute('onclick') || '').match(/openBossDetail\('([^']+)'\)/) || [])[1] || null;
    const artBox: any = c.querySelector('.f-cardart');
    const a: any = c.querySelector('.f-runart');
    const img: any = (a || artBox)?.querySelector('img');
    const glyph: any = (a || artBox)?.querySelector('.f-artglyph');
    const chip: any = c.querySelector('.gf-chips')?.firstElementChild;
    const expect_ = bossId && (window as any)._runBossArt
      ? (window as any)._runBossArt(bossId, title) : null;
    return {
      title, bossId,
      noRun: title === 'No verified farm source yet' || !bossId,
      // v1636 gave the BOSS run thumbnail `data-boss-tip` in place of `data-art-logo` (the item
      // thumbnail at bible.html:35458 still uses data-art-logo). The assertion's intent is that
      // SOMETHING binds the hover card — accept either, so this still fails when NEITHER is present.
      logo: a?.getAttribute('data-art-logo') ?? a?.getAttribute('data-boss-tip') ?? null,
      hasRunart: !!a,
      role: a?.getAttribute('role') ?? null,
      tabIndex: a ? a.tabIndex : null,
      onclick: a?.getAttribute('onclick') || '',
      onkeydown: a?.getAttribute('onkeydown') || '',
      imgSrc: img ? img.src : null,
      imgLoaded: img ? img.naturalWidth > 0 : false,
      glyph: glyph ? glyph.textContent : null,
      artHtml: artBox ? artBox.innerHTML.trim() : '',
      firstChip: chip ? chip.textContent.trim() : '',
      expectUrl: expect_ && expect_.url ? abs(expect_.url) : null,
      expectName: expect_ ? expect_.name : null,
      expectEmoji: expect_ ? expect_.emoji : null,
      width: a ? a.getBoundingClientRect().width : null
    };
  });
}

test.describe('v1625 — F·Sets best runs wear the boss, through the ONE helper', () => {

  test('★★★ every BEST RUN thumbnail is its BOSS — not the first set piece', async ({ page }) => {
    await fsets(page);
    const runs = await page.evaluate(readRuns);
    expect(runs.length, 'the sets board must actually have run cards to judge').toBeGreaterThan(1);

    const real = runs.filter((r: any) => !r.noRun);
    expect(real.length, `no sourced run card on the sets board (${runs.length} cards, all no-source?)`)
      .toBeGreaterThan(0);

    for (const r of real) {
      // it is a picture OF the boss the row is about
      expect(r.hasRunart, `${r.title}: no .f-runart wrapper — the thumbnail is still inert`).toBe(true);
      expect(r.logo, `${r.title}: no data-art-logo AND no data-boss-tip, so the board's hover card cannot bind`).toBeTruthy();
      // v1636: `data-boss-tip` carries the bossId ("pindle"), where `data-art-logo` carried the
      // display name ("Pindleskin"). Either one identifies the boss, so accept both — and this
      // stays falsifiable: an unrelated value matches NEITHER, and the line below independently
      // proves the identifier really belongs to THIS row's title.
      expect([r.expectName, r.bossId], `${r.title}: the logo names the boss`).toContain(r.logo);
      expect(r.title.toLowerCase()).toContain(String(r.logo).toLowerCase());

      // ...and it is NOT the arbitrary first drop. `art(g.items[0].name)` gave art/hd_amulet.png
      // here; _runBossArt gives art/reanimatedhorde-opt_graphic.png. This is the line that goes red.
      if (r.expectUrl) {
        expect(r.imgSrc, `${r.title}: thumbnail must BE the boss art (_runBossArt), got ${r.imgSrc}`)
          .toBe(r.expectUrl);
        expect(r.imgLoaded, `${r.title}: the boss art must actually decode`).toBe(true);
      } else {
        expect(r.glyph, `${r.title}: no boss url, so it degrades to the boss glyph`).toBe(r.expectEmoji);
      }
      expect(String(r.firstChip).toLowerCase(),
        `${r.title}: the picture must not be the first listed piece (${r.firstChip})`)
        .not.toContain(String(r.logo).toLowerCase());

      // and it opens the boss it is a picture of
      expect(r.onclick, `${r.title}: the thumbnail must open the boss card`).toContain('openBossDetail');
      expect(r.onclick).toContain(r.bossId);
    }
  });

  test('★★★ ONE helper — the sets path is not a pasted second copy', async ({ page }) => {
    await fsets(page);

    // (a) SOURCE: the definition exists exactly once in the shipped script text.
    const src = await page.evaluate(() => {
      const text = Array.from(document.scripts).map((s: any) => s.textContent || '').join('\n');
      const defs = (text.match(/^\s*(?:function\s+_runArtThumb\s*\(|(?:var|let|const)\s+_runArtThumb\s*=)/gm) || []).length;
      const uses = (text.match(/_runArtThumb\s*\(/g) || []).length;
      return { defs, uses, published: typeof (window as any)._runArtThumb };
    });
    expect(src.defs, `_runArtThumb must be defined ONCE — found ${src.defs} definitions (a second copy is the fork)`)
      .toBe(1);
    expect(src.uses - src.defs, `the helper must be CALLED from both boards — found ${src.uses - src.defs} call sites`)
      .toBeGreaterThanOrEqual(2);

    // (b) MARKUP: the sets thumbnail and the uniques thumbnail are byte-identical once the boss id
    //     is normalised out. A drifted copy fails here even if it dodges (a).
    const grab = async (tab: string, sel: string) => {
      await page.evaluate((t: string) => { try { (window as any).switchTab(t); } catch (e) {} }, tab);
      await page.waitForTimeout(1500);
      return page.evaluate((s: string) => {
        const a: any = document.querySelector(s);
        if (!a) return null;
        const norm = (x: string) => x.replace(/'[^']*'/g, "'ID'").replace(/\s+/g, ' ').trim();
        return {
          cls: a.className,
          attrs: a.getAttributeNames().sort().join(','),
          role: a.getAttribute('role'), tabIndex: a.tabIndex,
          onclick: norm(a.getAttribute('onclick') || ''),
          onkeydown: norm(a.getAttribute('onkeydown') || ''),
          picTag: a.firstElementChild ? a.firstElementChild.tagName : null,
          picCls: a.firstElementChild ? a.firstElementChild.className : null
        };
      }, sel);
    };
    const u = await grab('funi', '#tab-funi .f-card.f-pipe .f-runart');
    const s = await grab('fsets', '#tab-fsets .f-card.f-pipe .f-runart');
    expect(u, 'the uniques reference thumbnail must exist (v1624)').toBeTruthy();
    expect(s, 'the sets thumbnail must exist').toBeTruthy();
    expect(s!.cls, 'same wrapper class').toBe(u!.cls);
    expect(s!.attrs, 'same attribute set — data-art-logo, role, tabindex, handlers').toBe(u!.attrs);
    expect(s!.role).toBe('button');
    expect(s!.tabIndex).toBe(0);
    expect(s!.onclick, 'byte-identical click handler once the id is normalised').toBe(u!.onclick);
    expect(s!.onkeydown, 'byte-identical key handler once the id is normalised').toBe(u!.onkeydown);
    expect(s!.picTag).toBe(u!.picTag);
    expect(s!.picCls).toBe(u!.picCls);

    /* (c) CORROBORATION, reported not required. Both call sites are inside one IIFE, so calling the
       lexical binding is correct and leaves a window spy at zero. When the helper IS published we
       can do better than a spy: re-invoke it on the run the card was built from and demand the same
       markup back. Recorded either way so a future reader sees which path ran. */
    const corr = await page.evaluate(() => {
      const w: any = window;
      if (typeof w._runArtThumb !== 'function') return { path: 'lexical (not published)', match: null };
      const c: any = document.querySelector('#tab-fsets .f-card.f-pipe');
      const a: any = c && c.querySelector('.f-runart');
      const btn: any = c && Array.from(c.querySelectorAll('.f-cta .f-btn'))
        .find((b: any) => /openBossDetail/.test(b.getAttribute('onclick') || ''));
      const id = ((btn?.getAttribute('onclick') || '').match(/openBossDetail\('([^']+)'\)/) || [])[1] || null;
      const title = (c?.querySelector('.f-rwbig') as any)?.textContent?.trim() || '';
      if (!a || !id) return { path: 'published (no card to re-invoke)', match: null };
      let out = '';
      try { out = w._runArtThumb({ bossId: id, boss: title, items: [] }); } catch (e) { out = 'THREW: ' + e; }
      const box = document.createElement('div'); box.innerHTML = out;
      const re: any = box.querySelector('.f-runart');
      return { path: 'published', match: !!re && re.outerHTML === a.outerHTML, produced: out.slice(0, 200) };
    });
    console.log('[v1625] single-source corroboration:', JSON.stringify(corr));
    if (corr.match !== null) {
      expect(corr.match, `window._runArtThumb is published but re-invoking it does not reproduce the rendered sets thumbnail — that is a second implementation. produced=${(corr as any).produced}`)
        .toBe(true);
    }
  });

  test('★★ the thumbnail is a CONTROL — Enter opens the boss card, Space too', async ({ page }) => {
    const errs: string[] = [];
    page.on('pageerror', (e: any) => errs.push(String(e.message)));

    // pass A — real keyboard, no spy: watch the boss detail actually open.
    await fsets(page);
    /* .boss-detail-overlay is ALWAYS in the DOM — it is hidden, not absent. Counting nodes reads 1
       before anything is pressed, so "open" must mean VISIBLE. Measured: 0 visible before, 3 after
       (overlay + .boss-detail-panel.show + its header). */
    const OPEN = `(() => { const vis = (x) => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
      return Array.from(document.querySelectorAll('.boss-detail-panel.show, .boss-detail-overlay')).filter(vis).length; })()`;
    const before = await page.evaluate(`(() => {
      const a = document.querySelector('#tab-fsets .f-card.f-pipe .f-runart');
      if (a) a.focus();
      return { focused: !!a && document.activeElement === a, open: ${OPEN} };
    })()`) as any;
    expect(before.focused, 'the thumbnail must be reachable by keyboard focus (tabindex=0)').toBe(true);
    expect(before.open, 'no boss card open before we press anything').toBe(0);

    await page.keyboard.press('Enter');
    await page.waitForTimeout(700);
    const after = await page.evaluate(OPEN) as number;
    expect(after, 'Enter on the sets run thumbnail must OPEN the boss detail, not just fire a handler')
      .toBeGreaterThan(0);

    // pass B — fresh load, Space, and check it targets the RIGHT boss.
    await fsets(page);
    const spaced = await page.evaluate(() => {
      const w: any = window;
      const seen: string[] = [];
      const orig = w.openBossDetail;
      w.openBossDetail = function (id: string) { seen.push(id); return orig.apply(this, arguments as any); };
      const c: any = document.querySelector('#tab-fsets .f-card.f-pipe');
      const a: any = c && c.querySelector('.f-runart');
      const btn: any = c && Array.from(c.querySelectorAll('.f-cta .f-btn'))
        .find((b: any) => /openBossDetail/.test(b.getAttribute('onclick') || ''));
      const want = ((btn?.getAttribute('onclick') || '').match(/openBossDetail\('([^']+)'\)/) || [])[1] || null;
      a && a.focus();
      a && a.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true, cancelable: true }));
      w.openBossDetail = orig;
      return { seen, want };
    });
    expect(spaced.seen, `Space must open the boss card too (saw ${JSON.stringify(spaced.seen)})`)
      .toContain(spaced.want);
    expect(errs, `no page errors while driving the thumbnail: ${errs.join(' | ')}`).toEqual([]);
  });

  test('★ GRACEFUL DEGRADE — the no-source bucket still renders, and does not throw', async ({ page }) => {
    const errs: string[] = [];
    page.on('pageerror', (e: any) => errs.push(String(e.message)));
    await fsets(page);
    const runs = await page.evaluate(readRuns);
    const orphan = runs.find((r: any) => r.noRun);
    if (!orphan) {
      // legitimate state: every missing piece has a verified source. Say so rather than pass mutely.
      console.log('[v1625] no no-source bucket in this profile — degrade path not exercised');
      return;
    }
    expect(orphan.title, 'the no-source bucket keeps its label').toBe(NO_RUN);
    expect(orphan.artHtml.length,
      `the ${NO_RUN} card must still show SOMETHING in its art slot`).toBeGreaterThan(0);
    // exactly the uniques-side degrade: a picture, but not a control — there is no boss to open.
    expect(orphan.onclick, 'a bucket with no boss must not pretend to open one').not.toContain('openBossDetail');
    expect(orphan.role, 'and must not claim to be a button').not.toBe('button');
    expect(errs, `rendering the no-source bucket must not throw: ${errs.join(' | ')}`).toEqual([]);
  });

  test('★ the 430px hover guard — the anchor stays thumbnail-sized', async ({ page }) => {
    await fsets(page);
    const w = await page.evaluate(() =>
      Array.from(document.querySelectorAll('#tab-fsets .f-card.f-pipe .f-runart'))
        .map((a: any) => a.getBoundingClientRect().width));
    expect(w.length, 'nothing to measure — no sets run thumbnails rendered').toBeGreaterThan(0);
    const max = Math.max(...w);
    // the board's hover binding REFUSES anchors wider than 430px; wrap the thumbnail, never the row.
    expect(max, `widest sets run thumbnail is ${Math.round(max)}px — over 430 the hover card silently never binds`)
      .toBeLessThanOrEqual(430);
  });

  test('★★ COVERAGE — how many sets runs actually resolve a real boss picture', async ({ page }) => {
    await fsets(page);
    const runs = await page.evaluate(readRuns);
    const real = runs.filter((r: any) => !r.noRun);
    const withPic = real.filter((r: any) => r.imgLoaded).length;
    const msg = `${withPic}/${real.length} sourced sets runs resolve a real boss picture `
      + `(${runs.length} cards total, ${runs.length - real.length} no-source)`;
    console.log('[v1625] ' + msg);
    expect(real.length, `measured ${msg}`).toBeGreaterThanOrEqual(2);
    expect(withPic, `measured ${msg} — a resolver that silently blanks put the arbitrary-picture problem back under a new name`)
      .toBe(real.length);
  });
});
