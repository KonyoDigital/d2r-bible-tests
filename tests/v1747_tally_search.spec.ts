import { test, expect } from './_net_stub';
import * as path from 'path';

// v1747 — THE TALLY SEARCH BAR, IN BOTH GRAIL FORGES.
//
// Konyo: "for a tally version SEARCHBAR within each F-Uniques and F-Sets separately their own
// individual search bar to tally off... a search bar that i can sometimes casually while i farm one
// by one search for it and tally without needing to visually look for it. just a easy type it in
// style... with the colors sync and keyword items image floating HD cursor art same as the platform."
//
// ONE implementation, two callers (`window._tallySearch('uni'|'sets')`). A second copy is exactly how
// two lists start disagreeing about one collection — the defect this pair of tabs has been fixing all
// week. [[copy-drift]]
//
// IT WRITES THROUGH THE SAME FUNCTIONS HIS MANUAL ✓ USES — grailFoundUni for uniques,
// grailTogglePiece for pieces — so there is no second write path to drift, and an un-tick behaves
// like a tick. Measured end to end: found 246 -> 247, _gFound('Harlequin Crest') false -> true, the
// typed query survives the re-render so three items can be ticked without retyping.
//
// THE NAME IS THE HOVER ANCHOR, NEVER THE ROW. v654 refuses any arttip anchor wider than 430px —
// Konyo asked for that rule in those words ("only over the specific item keyword; it feels random")
// — and a result row is far wider. Measured: the name anchor is 63x16 and the floating card opens on
// it with the item's own HD art (Ravenlore -> hd_falcon_mask.png). Same rule that shaped the shopping
// list in v1739.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

async function openTab(page: any, tab: string) {
  await page.goto(URL);
  await page.waitForTimeout(2200);
  await page.evaluate((t: string) => { const w: any = window; try { w.switchTab && w.switchTab(t); } catch (e) {} }, tab);
  await page.waitForTimeout(1500);
}

async function typeQuery(page: any, tab: string, q: string) {
  return page.evaluate(async ([t, query]: [string, string]) => {
    const w: any = window;
    const inp = document.querySelector('#tab-' + t + ' .tsrch .tsrch-i') as HTMLInputElement | null;
    if (!inp) return { err: 'no search bar rendered in tab-' + t };
    inp.value = query;
    w._tallySearchRun(inp);
    await new Promise((r) => setTimeout(r, 220));
    const rows = [...document.querySelectorAll('#tab-' + t + ' .tsrch .tsrch-row')];
    return {
      rows: rows.length,
      count: (document.querySelector('#tab-' + t + ' .tsrch .tsrch-n') || {} as any).textContent,
      first: rows[0] ? (rows[0].textContent || '').replace(/\s+/g, ' ').trim() : null,
      anchors: document.querySelectorAll('#tab-' + t + ' .tsrch [data-arttip]').length,
      imgs: document.querySelectorAll('#tab-' + t + ' .tsrch img').length,
    };
  }, [tab, q]);
}

test.describe('v1747 — the tally search bar', () => {
  test('★★★ both forges render one, and each finds its own kind', async ({ page }) => {
    await openTab(page, 'funi');
    const uni = await typeQuery(page, 'funi', 'harle');
    expect((uni as any).err, (uni as any).err || '').toBeUndefined();
    expect(uni.rows, 'the uniques search found nothing for "harle"').toBeGreaterThan(0);
    expect(uni.first, 'the top uniques hit: ' + uni.first).toMatch(/Harlequin Crest/i);

    await openTab(page, 'fsets');
    const sets = await typeQuery(page, 'fsets', 'tal');
    expect((sets as any).err, (sets as any).err || '').toBeUndefined();
    expect(sets.rows, 'the sets search found nothing for "tal"').toBeGreaterThan(0);
    // a piece row carries its SET as the sub-label, which is what makes it identifiable
    expect(sets.first, 'the top sets hit: ' + sets.first).toMatch(/Tal Rasha/i);
  });

  test('★★★ tallying writes through the same path as the manual tick', async ({ page }) => {
    await openTab(page, 'funi');
    const r = await page.evaluate(async () => {
      const w: any = window;
      const before = { found: w.funiScan().found, has: !!(w._gFound && w._gFound('Harlequin Crest')) };
      const inp = document.querySelector('#tab-funi .tsrch .tsrch-i') as HTMLInputElement;
      inp.value = 'harlequin';
      w._tallySearchRun(inp);
      await new Promise((x) => setTimeout(x, 220));
      const go = document.querySelector('#tab-funi .tsrch .tsrch-go') as HTMLButtonElement | null;
      if (!go) return { err: 'no tally button' };
      go.click();
      await new Promise((x) => setTimeout(x, 1500));
      const inp2 = document.querySelector('#tab-funi .tsrch .tsrch-i') as HTMLInputElement | null;
      return {
        before,
        after: { found: w.funiScan().found, has: !!(w._gFound && w._gFound('Harlequin Crest')) },
        queryKept: inp2 ? inp2.value : null,
      };
    });
    expect((r as any).err, (r as any).err || '').toBeUndefined();
    // non-vacuity: it must have been UN-found first, or "it became found" proves nothing
    expect(r.before.has, 'Harlequin Crest was already found — the tick proves nothing').toBe(false);
    expect(r.after.has, 'tallying did not mark it found').toBe(true);
    expect(r.after.found, 'the found COUNT did not move').toBe(r.before.found + 1);
    // he ticks several in a row while farming — the query must survive the re-render
    expect(r.queryKept, 'the typed query was lost on re-render').toBe('harlequin');
  });

  test('★★★ the hover anchor is the keyword, so v654 cannot refuse it', async ({ page }) => {
    await openTab(page, 'funi');
    await typeQuery(page, 'funi', 'ravenlore');
    const a = await page.evaluate(() => {
      const els = [...document.querySelectorAll('#tab-funi .tsrch [data-arttip]')];
      return els.map((e) => {
        const r = e.getBoundingClientRect();
        return { w: Math.round(r.width), h: Math.round(r.height), ok: r.width <= 430 && r.height <= 120 };
      });
    });
    expect(a.length, 'the search rows carry no hover anchors at all').toBeGreaterThan(0);
    expect(a.filter((x) => !x.ok), 'anchors v654 will silently refuse: ' + JSON.stringify(a)).toEqual([]);

    // and the card must actually open, with the item's own art
    await page.locator('#tab-funi .tsrch .tsrch-nm[data-arttip]').first().hover({ timeout: 4000 });
    /* v1787 — POLL, DO NOT SNAPSHOT AT A FIXED DELAY. v1717 diagnosed this exact race in
       v1625 and fixed it THERE only: the card is raised by a delegated hover handler and
       `.on` is a transition class, so a single read at a fixed delay passes in one run and
       fails in the next. It cost two consecutive red Routine I runs on shard 3/6, on commits
       that changed no page code at all. Same defect, same remedy, applied to the class. The
       assertion below stays exactly as strict: if the card never comes up, this still goes red. */
    await page.waitForFunction(() => {
          const t = document.getElementById('arttip');
          return !!t && t.classList.contains('on');
        }, null, { timeout: 4000 }).catch(() => {});
    const tip = await page.evaluate(() => {
      const t = document.getElementById('arttip');
      if (!t) return { on: false, art: null as string | null, label: '' };
      const img = t.querySelector('img') as HTMLImageElement | null;
      return {
        on: t.classList.contains('on'),
        art: img && img.style.display !== 'none' && img.naturalWidth > 0 ? img.getAttribute('src') : null,
        label: (t.textContent || '').replace(/\s+/g, ' ').slice(0, 40),
      };
    });
    expect(tip.on, 'the floating card never opened on a search row').toBe(true);
    expect(tip.art, 'the floating card opened with no art').toBeTruthy();
    expect(tip.label, 'the card shows the wrong item: ' + tip.label).toMatch(/Ravenlore/i);
  });

  test('★★ a name nothing knows says so, rather than showing an empty box', async ({ page }) => {
    await openTab(page, 'funi');
    const r = await typeQuery(page, 'funi', 'zzzznotanitem');
    expect(r.rows, 'a nonsense query still rendered result rows').toBe(0);
    const txt = await page.evaluate(() =>
      (document.querySelector('#tab-funi .tsrch .tsrch-list') || { textContent: '' }).textContent || '');
    // an empty bordered box with no content is the exact thing the second eye is told to flag
    expect(txt.trim().length, 'the empty result state is a blank box with no words in it')
      .toBeGreaterThan(0);
  });
});
