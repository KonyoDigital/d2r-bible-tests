// v455 — SOCKETED / LARZUK REVIEW: the throw-out review's runeword tool (_baseRWLine), now surfaced INLINE
// for the MULED socketed + Larzuk bases. Konyo: socketed items mule correctly but never showed their runeword
// potential like throw-out items do. This proves the new #vault-socketed section renders the SAME engine —
// exact-socket + base-TYPE match + already-created (Chronicle) split — without a click.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v455 socketed/larzuk runeword review', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForFunction(() => (window as any).EXTRA_ITEMS && (window as any)._baseRWLine);
    await page.evaluate(() => { (window as any).switchTab && (window as any).switchTab('tools'); });
    await page.waitForTimeout(1500);
  });

  test('section renders for a muled socketed base with exact-socket runewords', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      // a 4-socket Monarch is the classic Spirit-shield base
      w._ensureSocketBaseEntry('Monarch (4os)');
      eval('owned').add('Monarch (4os)');
      w.renderVault();
      const el = document.getElementById('vault-socketed');
      return { hidden: el!.hidden, html: el!.innerHTML };
    });
    expect(r.hidden).toBe(false);
    expect(r.html).toContain('Socketed &amp; Larzuk Review');
    expect(r.html).toContain('Monarch');
    // SAME _baseRWLine engine → exact-socket phrasing the throw-out card uses
    expect(r.html).toContain('makeable in your 4os now');
    // v455 — clarity: the to-do list is explicitly labelled "still to create"
    expect(r.html).toMatch(/still to create/);
    // base-TYPE match: a 4os SHIELD lists shield-class words (Exile/Phoenix/Spirit — created ones cancel out)
    // and must NOT list weapon-only words (the v377 no-cross-bleed guarantee).
    expect(r.html).toMatch(/Exile|Phoenix|Spirit|already created/);
    expect(r.html).not.toContain('Grief');   // Grief is a weapon runeword, must not show on a shield
    expect(r.html).not.toContain('Insight'); // Insight is a polearm/staff word, must not show on a shield
  });

  test('already-created runewords are cancelled out (Chronicle split)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w._ensureSocketBaseEntry('Monarch (4os)');
      eval('owned').add('Monarch (4os)');
      // mark Spirit as already forged in the Chronicle
      try { (eval('rwMade'))['Spirit'] = 'Jan 1, 2026'; } catch (e) {}
      w.renderVault();
      const el = document.getElementById('vault-socketed');
      return { html: el!.innerHTML };
    });
    // the "already created" tag the throw-out tool shows must appear here too
    expect(r.html).toMatch(/already created/);
  });

  test('Chronicle toggle LIVE-syncs the socketed desc + review (created/un-created)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w._ensureSocketBaseEntry('Crystal Sword (4os)');
      eval('owned').add('Crystal Sword (4os)');
      // make sure Spirit starts NOT created, then capture
      try { delete (eval('rwMade'))['Spirit']; } catch (e) {}
      w._resyncSocketedDescs();
      const before = (w.EXTRA_ITEMS['Crystal Sword (4os)'] || {}).desc || '';
      // create Spirit via the real Chronicle toggle → must resync the cached desc + re-render the section
      w.rwToggleMade('Spirit');
      const afterDesc = (w.EXTRA_ITEMS['Crystal Sword (4os)'] || {}).desc || '';
      const sec = document.getElementById('vault-socketed');
      // un-create it again → desc should drop back
      w.rwToggleMade('Spirit');
      const revertedDesc = (w.EXTRA_ITEMS['Crystal Sword (4os)'] || {}).desc || '';
      return { before, afterDesc, sectionHtml: sec ? sec.innerHTML : '', revertedDesc };
    });
    // a 4os Crystal Sword makes Spirit — before creating, it's in the to-do list; after, it's cancelled out
    expect(r.before).toContain('Spirit');
    expect(r.afterDesc).toContain('already created');
    expect(r.afterDesc).toContain('Spirit');          // named on the green "already created" line
    expect(r.sectionHtml).toContain('already created'); // the review section re-rendered live too
    expect(r.revertedDesc).toContain('Spirit');         // un-create restores it to the to-do list
  });

  test('unsocketed Larzuk base shows the socket-to-max guidance', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w._ensureSocketBaseEntry('Monarch (Larzuk base)');
      eval('owned').add('Monarch (Larzuk base)');
      w.renderVault();
      const el = document.getElementById('vault-socketed');
      return { hidden: el!.hidden, html: el!.innerHTML };
    });
    expect(r.hidden).toBe(false);
    expect(r.html).toContain('Larzuk');
    expect(r.html).toMatch(/socket it to its max/i);
  });

  test('section hides when no socketed/larzuk bases are owned', async ({ page }) => {
    const hidden = await page.evaluate(() => {
      const w = window as any;
      // ensure none of our test items are owned in this fresh page
      w.renderVault();
      const el = document.getElementById('vault-socketed');
      // only assert hidden if there are genuinely no socketed bases owned
      const any = Array.from(eval('owned')).some((n: any) => w.EXTRA_ITEMS[n] && w.EXTRA_ITEMS[n].cat === 'Socketed bases');
      return any ? false : el!.hidden;
    });
    expect(hidden).toBe(true);
  });

  test('throw-out section is untouched (still its own standalone section)', async ({ page }) => {
    const ok = await page.evaluate(() => {
      return !!document.getElementById('vault-throwout') && !!document.getElementById('vault-socketed')
        && document.getElementById('vault-throwout') !== document.getElementById('vault-socketed');
    });
    expect(ok).toBe(true);
  });
});
