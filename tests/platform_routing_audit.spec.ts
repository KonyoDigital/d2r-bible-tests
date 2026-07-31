import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// ─────────────────────────────────────────────────────────────────────────────
// FULL-PLATFORM ROUTING AUDIT (2026-05-31)
//
// Konyo: "all subtabs tabs all items should be directing and routing relevant to
// each other ... this system should be perfect in and out."
//
// The calc item-grid bug (click rendered the detail 4000px below the fold with no
// scroll → looked like nothing happened) exposed a whole CLASS of bug that the
// existing specs miss: they assert a target gets class `show`/populates, but NOT
// that it is actually VISIBLE IN THE VIEWPORT. A routed detail that renders
// off-screen is, to the user, a dead click.
//
// This audit therefore asserts, for every navigation surface, that the routed
// target is genuinely in the viewport after the click — and sweeps for elements
// that advertise a click (cursor:pointer / .clickable / routing data-attrs) but
// produce no observable state change at all.
// ─────────────────────────────────────────────────────────────────────────────

const TABS = ['bosses', 'calc', 'tz', 'runes', 'rotw', 'ancients', 'binds', 'ref'];

// True iff the element is at least partially within the current viewport box.
async function elInViewport(page: any, selector: string): Promise<{ found: boolean; inView: boolean; top: number }> {
  return page.evaluate((sel: string) => {
    const el = document.querySelector(sel) as HTMLElement | null;
    if (!el) return { found: false, inView: false, top: NaN };
    const r = el.getBoundingClientRect();
    const inView = r.height > 0 && r.top < window.innerHeight && r.bottom > 0;
    return { found: true, inView, top: Math.round(r.top) };
  }, selector);
}

test.describe('platform routing audit — every route lands on a VISIBLE target', () => {
  test.beforeEach(async ({ page }) => {
    await page.evaluate(() => { try { localStorage.clear(); } catch {} }).catch(() => {});
    await page.goto(URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(2500);
  });

  test('every tab routes to a populated, visible panel', async ({ page }) => {
    for (const t of TABS) {
      await page.locator(`.tab[data-tab="${t}"]`).click();
      await page.waitForTimeout(150);
      const active = await page.evaluate(() => document.querySelector('.tab.active')?.getAttribute('data-tab'));
      expect(active, `tab ${t} should activate`).toBe(t);
      const panel = await page.evaluate((tab) => {
        const p = document.getElementById(`tab-${tab}`) as HTMLElement | null;
        if (!p) return { exists: false, visible: false, len: 0 };
        const r = p.getBoundingClientRect();
        return { exists: true, visible: r.height > 0, len: (p.textContent || '').trim().length };
      }, t);
      expect(panel.exists, `panel #tab-${t} exists`).toBe(true);
      expect(panel.visible, `panel #tab-${t} visible`).toBe(true);
      expect(panel.len, `panel #tab-${t} populated`).toBeGreaterThan(20);
    }
  });

  test('calc item-grid card click → item detail opens, populated, IN VIEWPORT (scroll-fix regression)', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab('calc'));
    await page.waitForTimeout(400);
    // pick a card that is NOT the first (so the detail is genuinely far below the fold)
    const target = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll('#item-grid .item-tile')) as HTMLElement[];
      if (cards.length < 5) return null;
      const el = cards[Math.min(40, cards.length - 1)];
      const name = el.dataset.name || el.getAttribute('data-name');
      el.click();
      return name;
    });
    expect(target, 'a calc card should be clickable').toBeTruthy();
    // wait for the smooth-scroll to actually bring #item-detail into the viewport
    await page.waitForFunction(() => {
      const d = document.getElementById('item-detail');
      if (!d || !d.classList.contains('show')) return false;
      const r = d.getBoundingClientRect();
      return r.height > 0 && r.top < window.innerHeight && r.bottom > 0;
    }, { timeout: 5000 }).catch(() => {});
    const detail = await page.evaluate(() => {
      const d = document.getElementById('item-detail') as HTMLElement | null;
      if (!d) return { show: false, len: 0, inView: false, top: NaN };
      const r = d.getBoundingClientRect();
      return {
        show: d.classList.contains('show'),
        len: (d.textContent || '').trim().length,
        inView: r.height > 0 && r.top < window.innerHeight && r.bottom > 0,
        top: Math.round(r.top),
      };
    });
    const sel = await page.evaluate(() => eval('typeof selectedItem!=="undefined"?selectedItem:null'));
    expect(detail.show, 'item-detail must be shown').toBe(true);
    expect(detail.len, 'item-detail must be populated').toBeGreaterThan(200);
    expect(sel, 'selectedItem must match the clicked card').toBe(target);
    expect(detail.inView, `item-detail must scroll INTO VIEW after click (was at top=${detail.top}px — off-screen = the bug)`).toBe(true);
  });

  test('calc search tile click → routes to its OWN item, detail visible', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab('calc'));
    await page.waitForTimeout(200);
    await page.locator('#item-search').fill('ring');
    await page.waitForTimeout(300);
    const clicked = await page.evaluate(() => {
      const tile = document.querySelector('.item-tile') as HTMLElement;
      const name = tile?.getAttribute('data-name');
      tile?.click();
      return name;
    });
    await page.waitForTimeout(700);
    const r = await page.evaluate(() => ({
      selected: eval('typeof selectedItem!=="undefined"?selectedItem:null'),
      detailInView: (() => { const d = document.getElementById('item-detail'); if (!d) return false; const b = d.getBoundingClientRect(); return d.classList.contains('show') && b.top < window.innerHeight && b.bottom > 0; })(),
    }));
    expect(r.selected, 'tile must route to its own item').toBe(clicked);
    expect(r.detailInView, 'detail must be visible after tile click').toBe(true);
  });

  test('hero pick → golden item card opens and is visible', async ({ page }) => {
    await page.waitForTimeout(400);
    const ok = await page.evaluate(() => {
      const pick = document.querySelector('.hero-pick') as HTMLElement;
      if (!pick) return { clicked: false };
      pick.click();
      return { clicked: true };
    });
    expect(ok.clicked, 'a hero-pick should exist').toBe(true);
    // openItemDetail unhides #item-detail-panel then smooth-scrolls to it (~50ms delay);
    // poll until the golden card is in the viewport rather than guessing a fixed wait.
    await page.waitForFunction(() => {
      const panel = document.getElementById('item-detail-panel');
      const gic = panel?.querySelector('.gic-card') as HTMLElement | null;
      if (!gic || panel?.classList.contains('hidden')) return false;
      const b = gic.getBoundingClientRect();
      return b.height > 0 && b.top < window.innerHeight && b.bottom > 0;
    }, { timeout: 5000 }).catch(() => {});
    const r = await page.evaluate(() => {
      const panel = document.getElementById('item-detail-panel');
      const gic = panel?.querySelector('.gic-card') as HTMLElement | null;
      const hidden = panel?.classList.contains('hidden');
      const b = gic?.getBoundingClientRect();
      return {
        gicExists: !!gic,
        panelShown: !hidden,
        gicInView: !!b && b.height > 0 && b.top < window.innerHeight && b.bottom > 0,
      };
    });
    expect(r.gicExists, 'hero-pick opens a golden item card').toBe(true);
    expect(r.panelShown, 'item-detail-panel not hidden').toBe(true);
    expect(r.gicInView, 'golden item card must be in viewport').toBe(true);
  });

  test('source chip → routes to a boss that ACTUALLY drops the item, boss card visible', async ({ page }) => {
    await page.evaluate(() => (window as any).navigateToItem('Harlequin Crest (Shako)'));
    await page.waitForTimeout(700);
    const chip = await page.evaluate(() => {
      const els = [...document.querySelectorAll('#item-detail .source-chip')] as HTMLElement[];
      for (const e of els) {
        const oc = e.getAttribute('onclick') || '';
        const m = oc.match(/setActiveItem\([^,]+,\s*'([a-z_]+)'/);
        if (m) { e.click(); return m[1]; }
      }
      return null;
    });
    test.skip(!chip, 'no parseable source-chip');
    // The per-boss full drop table lives in a collapsed <details>, so the genuinely
    // visible landing target is the BOSS CARD itself (header + diff summary), which the
    // chip scrolls into view. setActiveItem glows it (.has-item) and pulses the exact cell.
    await page.waitForFunction((bossId) => {
      const card = document.getElementById(bossId!) as HTMLElement | null;
      if (!card || !card.classList.contains('has-item')) return false;
      const r = card.getBoundingClientRect();
      return r.top < window.innerHeight && r.bottom > 0;
    }, chip, { timeout: 5000 }).catch(() => {});
    const r = await page.evaluate((bossId) => {
      const item = 'Harlequin Crest (Shako)';
      const boss = (BOSSES as any[]).find(b => b.id === bossId);
      const card = document.getElementById(bossId!) as HTMLElement | null;
      const b = card?.getBoundingClientRect();
      return {
        tab: document.querySelector('.tab.active')?.getAttribute('data-tab'),
        bossDropsItem: !!(boss && boss.dropTable.some((d: any) => d.n === item)),
        hasItemGlow: !!card?.classList.contains('has-item'),
        cardHasRow: !!card?.querySelector(`tr.clickable[data-item="${item}"]`),
        focusedCellInBoss: !!card?.querySelector('td.focused-cell'),
        cardInView: !!b && b.top < window.innerHeight && b.bottom > 0,
      };
    }, chip);
    expect(r.tab).toBe('bosses');
    expect(r.bossDropsItem, `source-chip boss "${chip}" must actually drop the item`).toBe(true);
    expect(r.hasItemGlow, 'routed boss card must be glowed as the active-item source').toBe(true);
    expect(r.cardHasRow, `routed boss must have a clickable row for the item`).toBe(true);
    expect(r.focusedCellInBoss, 'the exact (boss×difficulty) drop cell must be pulsed').toBe(true);
    expect(r.cardInView, 'the routed boss card must be scrolled into the viewport').toBe(true);
  });

  test('boss-nav chip → opens its own boss, detail card visible', async ({ page }) => {
    // v61: the bosses tab was split behind a new default-active Main tab. The boss-nav
    // chips and #boss-detail-panel live in #tab-bosses, which is display:none on load —
    // a panel rendered there has zero height and never enters the viewport. Activate the
    // bosses tab first so the chip routing renders into a visible container.
    await page.evaluate(() => (window as any).switchTab('bosses'));
    await page.waitForTimeout(150);
    const meta: { id: string; name: string }[] = await page.evaluate(() => (BOSSES as any[]).map(b => ({ id: b.id, name: b.name })));
    // sample first, middle, last to cover the spread
    for (const idx of [0, Math.floor(meta.length / 2), meta.length - 1]) {
      const { id, name } = meta[idx];
      await page.evaluate(() => { if ((window as any).clearActiveBoss) (window as any).clearActiveBoss(); });
      await page.waitForTimeout(150);
      await page.evaluate((bid) => {
        const chip = document.querySelector(`.boss-chip[data-boss-id="${bid}"]`) as HTMLElement;
        chip?.click();
      }, id);
      // setActiveBoss renders into #boss-detail-panel and smooth-scrolls THAT into view
      // (the #${id} element is the full drop table far down the page, not the routed target).
      await page.waitForFunction(() => {
        const p = document.getElementById('boss-detail-panel');
        if (!p || !p.classList.contains('show')) return false;
        const r = p.getBoundingClientRect();
        return r.height > 0 && r.top < window.innerHeight && r.bottom > 0;
      }, { timeout: 5000 }).catch(() => {});
      const r = await page.evaluate(() => {
        const active = (typeof activeBossId !== 'undefined') ? activeBossId : null;
        const p = document.getElementById('boss-detail-panel');
        const b = p?.getBoundingClientRect();
        const gbcName = (p?.querySelector('.gbc-name')?.textContent || '').trim();
        return {
          active,
          shown: !!p?.classList.contains('show'),
          inView: !!b && b.height > 0 && b.top < window.innerHeight && b.bottom > 0,
          top: b ? Math.round(b.top) : NaN,
          gbcName,
        };
      });
      expect(r.active, `chip ${id} sets activeBossId`).toBe(id);
      expect(r.shown, `boss-detail-panel shown for ${id}`).toBe(true);
      expect(r.gbcName, `routed card must be ${name}'s, not another boss's`).toBe(name);
      expect(r.inView, `boss detail card must be in viewport after chip click (top=${r.top})`).toBe(true);
    }
  });

  test('glossary opens a visible modal and closes cleanly', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab('ref'));
    await page.waitForTimeout(200);
    const opened = await page.evaluate(() => {
      if (typeof (window as any).openGlossary !== 'function') return { fn: false };
      (window as any).openGlossary();
      return { fn: true };
    });
    test.skip(!opened.fn, 'openGlossary not exposed');
    await page.waitForTimeout(300);
    const modal = await page.evaluate(() => {
      // glossary renders into some overlay; find any visible modal/overlay with content
      const candidates = ['#glossary', '#glossary-modal', '.glossary-modal', '.glossary-overlay', '#glossary-panel'];
      for (const sel of candidates) {
        const el = document.querySelector(sel) as HTMLElement | null;
        if (el) { const r = el.getBoundingClientRect(); if (r.height > 0 && r.top < window.innerHeight) return { sel, len: (el.textContent || '').length }; }
      }
      return null;
    });
    expect(modal, 'glossary should open a visible modal').toBeTruthy();
    expect(modal!.len, 'glossary modal populated').toBeGreaterThan(20);
    if (typeof await page.evaluate(() => (window as any).closeGlossary) === 'function') {
      await page.evaluate(() => (window as any).closeGlossary());
    }
  });

  // DEAD-CLICK SWEEP — across every tab, any element that LOOKS routable (a non-empty
  // routing data-attr, or .clickable, or .ic-card/.item-tile/.hero-pick/.source-chip)
  // must change observable state when clicked. A no-op is a dead click.
  test('dead-click sweep — no navigation element clicks into the void', async ({ page }) => {
    // 600s (was 360s, was 240s): the per-click captureSig + heavy renders on the 1MB
    // codex page make this the suite's single slowest test (~55s warm locally). On a
    // badly degraded CI runner it has crossed even 360s (a >6x slowdown), so this gives
    // ~10x warm-local headroom to kill the chronic slow-runner false-RED. The 35m job
    // ceiling accommodates it; isolated it always passes (it's never a real hang).
    test.setTimeout(600000);
    const captureSig = () => page.evaluate(() => {
      const g = (n: string) => { try { return eval(`typeof ${n}!=="undefined"?${n}:null`); } catch { return null; } };
      const detail = document.getElementById('item-detail');
      const gic = document.getElementById('item-detail-panel');
      return JSON.stringify({
        tab: document.querySelector('.tab.active')?.getAttribute('data-tab'),
        boss: g('activeBossId'),
        sel: g('selectedItem'),
        act: g('activeItem'),
        itemDetail: g('activeItemDetail'),
        detailShown: !!detail?.classList.contains('show'),
        // childElementCount is O(children); textContent.length is O(whole subtree)
        // and was the per-click hot-spot on the 1062KB codex page — swap it out.
        detailKids: detail?.childElementCount ?? 0,
        gicHidden: !!gic?.classList.contains('hidden'),
        gicKids: gic?.childElementCount ?? 0,
        showN: document.querySelectorAll('.show,.active,.open,.has-item').length,
        // CC 2026-06-01 unify: TZ zone / super-unique cards open an inline droppable
        // detail box (toggles the [hidden] attr, no .show class) — count open boxes so
        // that legit state change is observable and never mis-flagged as a dead click.
        openDetails: document.querySelectorAll('.tz-zone-detail:not([hidden]),.su-detail:not([hidden])').length,
        scrollY: Math.round(window.scrollY / 50),
      });
    });

    const dead: string[] = [];
    const SELECTORS = [
      '#item-grid .item-tile',
      '.item-tile',
      '.hero-pick',
      '.boss-chip[data-boss-id]:not([data-boss-id=""])',
      '.tz-zone-card[data-boss-id]:not([data-boss-id=""])',
      '.top-drop-row',
      'table.drops tbody tr.clickable',
      '#item-detail .source-chip',
    ];

    for (const tab of TABS) {
      await page.evaluate((t) => (window as any).switchTab(t), tab);
      await page.waitForTimeout(150);
      for (const sel of SELECTORS) {
        const count = await page.locator(sel).count();
        if (count === 0) continue;
        // sample first + last of this type on this tab
        const idxs = count <= 2 ? [...Array(count).keys()] : [0, count - 1];
        for (const i of idxs) {
          const before = await captureSig();
          const clicked = await page.evaluate(({ s, idx }) => {
            const els = document.querySelectorAll(s);
            const el = els[idx] as HTMLElement | undefined;
            if (!el) return false;
            // Many panels (e.g. the calc #item-grid) stay in the DOM while their tab is
            // hidden, so querySelectorAll matches tiles that are display:none on this tab.
            // A user can't click those — sweeping them wastes a heavy render AND mis-fires
            // "no state change" when idx 0 happens to already be the active selection.
            // Only sweep genuinely visible targets; reveal a collapsed <details> first.
            const det = el.closest('details');
            if (det && !det.open) det.setAttribute('open', '');
            if (!el.offsetParent && el.getClientRects().length === 0) return 'hidden';
            el.click();
            return true;
          }, { s: sel, idx: i });
          if (clicked === 'hidden' || !clicked) continue;
          // These click handlers mutate state (activeBossId/selectedItem/.show/showN)
          // SYNCHRONOUSLY, so capture immediately — a real click is already changed by
          // the time the eval returns. Only a genuine no-op falls through to the poll,
          // which tolerates the rare laggard (async scroll-binned scrollY) under parallel
          // load without making every click pay a fixed wait. This keeps the sweep well
          // under the timeout even on the heavier codex page.
          let after = await captureSig();
          for (let attempt = 0; after === before && attempt < 3; attempt++) {
            await page.waitForTimeout(100);
            after = await captureSig();
          }
          if (after === before) {
            const label = await page.evaluate(({ s, idx }) => {
              const el = document.querySelectorAll(s)[idx] as HTMLElement | undefined;
              return (el?.getAttribute('data-name') || el?.getAttribute('data-boss-id') || el?.getAttribute('data-item') || (el?.textContent || '').slice(0, 30)).trim();
            }, { s: sel, idx: i });
            // v1494 — IDEMPOTENT IS NOT DEAD, and the evidence rides along. This fired on CI for
            // exactly one tile, and the message said only "no state change" — so the first fix was a
            // guess, and the guess was wrong. With the signature printed, the answer was immediate:
            //   before: sel="Key of Hate" act="Key of Hate" detailShown:true
            // The sweep visits bosses before calc and Key of Hate is The Summoner's signature drop, so
            // that item was ALREADY open when the sweep reached calc tile #0. Re-clicking the item you
            // are already looking at cannot change state, and that is correct behaviour — the bug class
            // this sweep guards is a click that goes NOWHERE, not a click that goes where you already
            // are. The exemption is deliberately narrow: the target must be the live selection AND its
            // detail must be on screen, so a genuinely dead tile can't hide behind a name collision.
            const b4 = JSON.parse(before);
            const alreadyOpen = b4.detailShown === true && (b4.sel === label || b4.act === label);
            if (!alreadyOpen) {
              dead.push(`[${tab}] ${sel} #${i} ("${label}") → no state change\n      before: ${before}\n      after:  ${after}`);
            }
          }
          // a routing click can leave this tab (source-chip/tz-card → bosses); only
          // re-switch when that actually happened, to keep the sweep fast.
          const nowTab = JSON.parse(after).tab;
          if (nowTab !== tab) {
            await page.evaluate((t) => (window as any).switchTab(t), tab);
            await page.waitForTimeout(100);
          }
        }
      }
    }
    expect(dead, `dead navigation clicks found:\n${dead.join('\n')}`).toEqual([]);
  });
});
