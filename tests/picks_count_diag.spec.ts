// SKIPPED (audit 2026-06-12): dev diagnostic with zero expect()s — can only 'fail'
// by timing out under full-suite load (false red). Unskip locally when needed.
// Count picks per boss to see what dropped
// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';
import * as path from 'path';
const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const BOSSES = ['countess','andariel','duriel','mephisto','travincal','diablo','baal','pindle','nihl','cows','pit'];

test.skip('picks count per boss', async ({ page }) => {
  test.setTimeout(90000); // 11 bosses × ~3-5s under load; default 30s is too tight
  const errs: string[] = [];
  page.on('pageerror', e => errs.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push('console:' + m.text()); });
  await page.goto(BIBLE);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await page.waitForTimeout(900);
  for (const b of BOSSES) {
    const chip = page.locator(`.boss-chip[data-boss-id="${b}"]`).first();
    await chip.waitFor({ state: 'attached', timeout: 5000 });
    await chip.evaluate((el: any) => el.click());
    await page.waitForTimeout(500);
    const result = await page.evaluate((bossId) => {
      const picks = Array.from(document.querySelectorAll('.hero-pick'));
      const w = window as any;
      return {
        count: picks.length,
        items: picks.map(p => (p.textContent||'').split('\n').map(s=>s.trim()).filter(Boolean)[1]||'').slice(0, 20),
        activeBossId: w.activeBossId,
        heroPickCount: w.heroPickCount,
        mf: w.mf,
        bossSources: (w.ITEMS || []).filter((it: any) => (it.tier==='grail'||it.tier==='uber') && (it.sources||[]).some((s:any)=>s.bossId===bossId && s.chance>=100)).length,
      };
    }, b);
    console.log(`[${b}] n=${result.count} candidates=${result.bossSources}`);
    if (result.count === 0 || result.count < 10) {
      const dump = await page.evaluate((bossId) => {
        const w = window as any;
        const items = (w.ITEMS || []).filter((it: any) => (it.tier==='grail'||it.tier==='uber') && (it.sources||[]).some((s:any)=>s.bossId===bossId && s.chance>=100));
        const heroHtml = (document.getElementById('hero-picks')?.innerHTML || '').slice(0, 200);
        return { item_candidates: items.length, sample: items.slice(0,3).map((i:any)=>i.n), hero_html: heroHtml };
      }, b);
      console.log(`  [DUMP ${b}] candidates=${dump.item_candidates} sample=${dump.sample.join(',')} html=${dump.hero_html}`);
    }
  }
  if (errs.length) console.log('[ERRORS]', errs.slice(0, 5));
});
