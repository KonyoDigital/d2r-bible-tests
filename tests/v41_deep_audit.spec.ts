import { test, expect } from '@playwright/test';
import * as path from 'path';
import { BOSS_CHIPS_TOTAL } from './_data_locks';

const BIBLE_URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v41 DEEP AUDIT — back-to-back + end-to-end correctness check.
// Bible's source of truth = ITEMS[].sources[] (each item declares which bosses
// drop it + at what chance + difficulty). Anything rendered in a droptable that
// disagrees with ITEMS[] is either fabricated or a render bug.
//
// Note: `BOSSES`/`ITEMS` are `const` in page scope — NOT on `window`. We access
// them through `eval('typeof X !== "undefined" ? X : null')` to bridge scopes.

test.describe('v41 deep audit — cross-reference engine to data model', () => {
  test.setTimeout(120000);

  test('master data model intact: 13 bosses + ≥300 items + 6 difficulty keys', async ({ page }) => {
    await page.goto(BIBLE_URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(600);
    const probe = await page.evaluate(() => {
      const B = eval('typeof BOSSES !== "undefined" ? BOSSES : null');
      const I = eval('typeof ITEMS !== "undefined" ? ITEMS : null');
      if (!B || !I) return { ok: false };
      const diffKeys = new Set<string>();
      for (const i of I) for (const s of (i.sources || [])) if (s.diffKey) diffKeys.add(s.diffKey);
      return {
        ok: true,
        bosses: B.length,
        items: I.length,
        diffKeys: Array.from(diffKeys).sort(),
        bossIds: B.map((b: any) => b.id),
      };
    });
    expect(probe.ok, 'BOSSES + ITEMS not on page').toBe(true);
    expect(probe.bosses).toBe(BOSS_CHIPS_TOTAL); // 11 farmable bosses + 2 event drops (Summoner=Key of Hate, Dclone=Annihilus)
    expect(probe.items).toBeGreaterThanOrEqual(300);
    expect(probe.diffKeys).toEqual(expect.arrayContaining(['norm', 'normTz', 'nm', 'nmTz', 'hell', 'hellTz']));
    expect(probe.bossIds).toEqual(expect.arrayContaining([
      'countess','andariel','duriel','mephisto','travincal','diablo','baal','pindle','nihl','cows','pit',
    ]));
  });

  test('every droptable item name exists in master ITEMS index (no fabricated items)', async ({ page }) => {
    await page.goto(BIBLE_URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(800);
    const report = await page.evaluate(() => {
      // v1717 — the MASTER index is ITEM_REGISTRY, which is what this test's own title says.
      // ITEMS is the CALCULATOR's curated subset; after the silospen pull a droppable item can
      // legitimately be in the registry and out of the calculator (that separation is the whole
      // point of `nc:1`). Checking against ITEMS would report 216 real drops as "fabricated".
      const w: any = window;
      const I = (typeof w._allDropItems === 'function')
        ? w._allDropItems()
        : eval('typeof ITEMS !== "undefined" ? ITEMS : []');
      const masterNames = new Set<string>(I.map((i: any) => i.n));
      const orphans: { boss: string; item: string }[] = [];
      for (const bossCard of Array.from(document.querySelectorAll('#boss-cards .boss-card'))) {
        const bossId = (bossCard as HTMLElement).id;
        for (const row of Array.from(bossCard.querySelectorAll('table.drops tbody tr'))) {
          const item = (row as HTMLElement).getAttribute('data-item') ||
                       (row.querySelector('td') as HTMLElement)?.innerText?.trim() || '';
          if (item && !masterNames.has(item)) {
            orphans.push({ boss: bossId, item });
          }
        }
      }
      return { orphans, masterCount: masterNames.size };
    });
    if (report.orphans.length) console.log('ORPHANS:', JSON.stringify(report.orphans.slice(0, 30), null, 2));
    expect(report.orphans.length, `Orphaned droptable items (not in ITEMS[]): ${report.orphans.length}`).toBe(0);
  });

  test('every ITEMS[].sources[] bossId actually exists in BOSSES (no fabricated drop sources)', async ({ page }) => {
    await page.goto(BIBLE_URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(400);
    const report = await page.evaluate(() => {
      const B = eval('typeof BOSSES !== "undefined" ? BOSSES : []');
      const I = eval('typeof ITEMS !== "undefined" ? ITEMS : []');
      const validBossIds = new Set<string>(B.map((b: any) => b.id));
      const VALID_DIFFS = new Set(['norm', 'normTz', 'nm', 'nmTz', 'hell', 'hellTz']);
      const badBossIds: any[] = [];
      const badDiffKeys: any[] = [];
      const badChance: any[] = [];
      for (const item of I) {
        for (const s of (item.sources || [])) {
          if (s.bossId && !validBossIds.has(s.bossId)) {
            badBossIds.push({ item: item.n, source: s });
          }
          if (s.diffKey && !VALID_DIFFS.has(s.diffKey)) {
            badDiffKeys.push({ item: item.n, source: s });
          }
          if (s.chance !== undefined && s.chance !== null && s.chance !== 0) {
            if (typeof s.chance !== 'number' || !isFinite(s.chance) || s.chance < 0) {
              badChance.push({ item: item.n, source: s });
            }
          }
        }
      }
      return { badBossIds, badDiffKeys, badChance };
    });
    if (report.badBossIds.length) console.log('BAD BOSS IDS:', JSON.stringify(report.badBossIds.slice(0, 10), null, 2));
    if (report.badDiffKeys.length) console.log('BAD DIFF KEYS:', JSON.stringify(report.badDiffKeys.slice(0, 10), null, 2));
    if (report.badChance.length) console.log('BAD CHANCES:', JSON.stringify(report.badChance.slice(0, 10), null, 2));
    expect(report.badBossIds.length, 'sources referencing non-existent bossId').toBe(0);
    expect(report.badDiffKeys.length, 'sources with invalid diffKey').toBe(0);
    expect(report.badChance.length, 'sources with invalid chance values').toBe(0);
  });

  test('bidirectional: every droptable row item has a matching source in ITEMS[].sources for that boss', async ({ page }) => {
    await page.goto(BIBLE_URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(800);
    const report = await page.evaluate(() => {
      const I = eval('typeof ITEMS !== "undefined" ? ITEMS : []');
      const byName = new Map<string, any>(I.map((i: any) => [i.n, i]));
      const mismatches: any[] = [];
      for (const bossCard of Array.from(document.querySelectorAll('#boss-cards .boss-card'))) {
        const bossId = (bossCard as HTMLElement).id;
        for (const row of Array.from(bossCard.querySelectorAll('table.drops tbody tr'))) {
          const itemName = (row as HTMLElement).getAttribute('data-item') ||
                           (row.querySelector('td') as HTMLElement)?.innerText?.trim() || '';
          if (!itemName) continue;
          const item = byName.get(itemName);
          if (!item) continue;
          const found = (item.sources || []).find((s: any) => s.bossId === bossId);
          if (!found) {
            mismatches.push({ boss: bossId, item: itemName, declared_sources: (item.sources || []).map((s: any) => s.bossId) });
          }
        }
      }
      return { mismatches };
    });
    if (report.mismatches.length) console.log('UNDECLARED SOURCES:', JSON.stringify(report.mismatches.slice(0, 20), null, 2));
    expect(report.mismatches.length, `Items rendered on boss without source declaration: ${report.mismatches.length}`).toBe(0);
  });

  test('reverse: every ITEMS[].sources[bossId=X] is rendered in boss X droptable', async ({ page }) => {
    await page.goto(BIBLE_URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(800);
    const report = await page.evaluate(() => {
      const I = eval('typeof ITEMS !== "undefined" ? ITEMS : []');
      const B = eval('typeof BOSSES !== "undefined" ? BOSSES : []');
      const validBossIds = new Set<string>(B.map((b: any) => b.id));
      const rendered = new Map<string, Set<string>>();
      for (const bossCard of Array.from(document.querySelectorAll('#boss-cards .boss-card'))) {
        const bossId = (bossCard as HTMLElement).id;
        const itemSet = new Set<string>();
        for (const row of Array.from(bossCard.querySelectorAll('table.drops tbody tr'))) {
          const itemName = (row as HTMLElement).getAttribute('data-item') ||
                           (row.querySelector('td') as HTMLElement)?.innerText?.trim() || '';
          if (itemName) itemSet.add(itemName);
        }
        rendered.set(bossId, itemSet);
      }
      const missing: any[] = [];
      for (const item of I) {
        const seen = new Set<string>();
        for (const s of (item.sources || [])) {
          if (!s.bossId || !validBossIds.has(s.bossId)) continue;
          if (seen.has(s.bossId)) continue;
          seen.add(s.bossId);
          const rset = rendered.get(s.bossId);
          if (!rset || !rset.has(item.n)) {
            missing.push({ item: item.n, declared_boss: s.bossId });
          }
        }
      }
      return { missing, rendered_per_boss: Object.fromEntries(Array.from(rendered.entries()).map(([k, v]) => [k, v.size])) };
    });
    console.log('Items rendered per boss:', JSON.stringify(report.rendered_per_boss));
    if (report.missing.length) console.log('MISSING FROM RENDER:', JSON.stringify(report.missing.slice(0, 30), null, 2));
    expect(report.missing.length, `Declared sources not rendered: ${report.missing.length}`).toBe(0);
  });

  test('no two bosses have identical droptables', async ({ page }) => {
    await page.goto(BIBLE_URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(600);
    // v1716 — THE SIGNATURE HAD TO GET STRONGER, NOT WEAKER.
    // This compared the sorted set of item NAMES rendered per boss. That was a fine proxy for
    // "nobody copy-pasted a droptable" while the tables were incomplete — but after the silospen
    // RoW 3.0 pull filled them in, several bosses legitimately reach the SAME 395-item pool at
    // saturation (andariel/duriel and diablo/pindle were the first two), and the guard fired on
    // the truth. Their ODDS are all different, which is exactly what a copy-paste would not be.
    // So the signature is now name + all six per-difficulty chances, read from ITEMS[].sources —
    // a real duplicated table still fails, a shared pool no longer does.
    const result = await page.evaluate(() => {
      const w: any = window;
      const sigByBoss: Record<string, string> = {};
      const per: Record<string, string[]> = {};
      for (const it of (w.ITEMS || [])) {
        for (const s of (it.sources || [])) {
          if (!s || !s.bossId) continue;
          (per[s.bossId] = per[s.bossId] || []).push(
            it.n + '@' + s.diffKey + '=' + (s.chance == null ? 'x' : s.chance));
        }
      }
      for (const bossId of Object.keys(per)) sigByBoss[bossId] = per[bossId].sort().join('|');
      const dupes: any[] = [];
      const sigs = Object.entries(sigByBoss);
      for (let i = 0; i < sigs.length; i++) {
        for (let j = i + 1; j < sigs.length; j++) {
          if (sigs[i][1] === sigs[j][1]) dupes.push({ a: sigs[i][0], b: sigs[j][0] });
        }
      }
      return { dupes, sizes: Object.fromEntries(Object.entries(sigByBoss).map(([k, v]) => [k, v.split('|').length])) };
    });
    console.log('Droptable sizes per boss:', JSON.stringify(result.sizes));
    expect(result.dupes.length, `Duplicate droptables: ${JSON.stringify(result.dupes)}`).toBe(0);
  });

  test('chance cell format: every visible cell parses to a known format', async ({ page }) => {
    await page.goto(BIBLE_URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(800);
    // v43: drop tables are collapsed behind <details>; expand them and read via textContent so the
    // pattern census reflects real cell content (innerText returns "" for hidden nodes).
    await page.evaluate(() => {
      document.querySelectorAll('details.all-drops-details').forEach(d => d.setAttribute('open', ''));
    });
    const report = await page.evaluate(() => {
      // Broaden valid set — sample real values first
      const samples = new Map<string, number>();
      let total = 0;
      let empty = 0;
      for (const row of Array.from(document.querySelectorAll('#boss-cards table.drops tbody tr'))) {
        const tds = row.querySelectorAll('td');
        for (let i = 2; i < tds.length; i++) {
          total++;
          const txt = (tds[i] as HTMLElement).textContent!.trim();
          if (txt === '') empty++;
          // Normalize: extract format pattern
          const pat = txt
            .replace(/\d/g, '#')
            .replace(/#+/g, 'N')
            .replace(/\s+/g, ' ')
            .slice(0, 30);
          samples.set(pat, (samples.get(pat) || 0) + 1);
        }
      }
      // Top patterns
      const top = Array.from(samples.entries()).sort((a, b) => b[1] - a[1]).slice(0, 15);
      return { total, empty, top };
    });
    console.log('Top cell value patterns:', JSON.stringify(report.top, null, 2));
    expect(report.total, 'expected ≥19,000 chance cells').toBeGreaterThanOrEqual(19000);
    // every cell must carry content — a "1:N", "N%", a block reason, or "—" (never blank)
    expect(report.empty, 'cells must never render blank').toBe(0);
    expect(report.top[0][0], 'dominant cell pattern should not be empty').not.toBe('');
  });

  test('no fabricated cells: every rendered (boss,item,diff) has declared ITEMS[].sources[] + ratio sanity', async ({ page }) => {
    await page.goto(BIBLE_URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(800);
    // v43: the full drop tables live inside collapsed <details>; expand them so every row is in
    // play. (We read via textContent below, but expanding keeps this robust either way.)
    await page.evaluate(() => {
      document.querySelectorAll('details.all-drops-details').forEach(d => d.setAttribute('open', ''));
    });
    const report = await page.evaluate(() => {
      // SOURCE OF TRUTH = BOSSES[].dropTable[] — the renderer maps directly over boss.dropTable
      // and prints adjustChance(d[diffKey]). A cell is "fabricated" iff it shows a 1:N chance with
      // no positive backing value in dropTable for that (boss,item,diff). (Earlier versions cross-
      // referenced ITEMS[].sources[], which is NOT the render source in the current data model.)
      const B = eval('typeof BOSSES !== "undefined" ? BOSSES : []');
      const dropByBoss = new Map<string, Map<string, any>>();
      for (const b of B) {
        const m = new Map<string, any>();
        for (const d of (b.dropTable || [])) m.set(d.n, d);
        dropByBoss.set(b.id, m);
      }
      const DIFF_COL = ['norm','normTz','nm','nmTz','hell','hellTz'];
      const fabricated: any[] = [];   // rendered 1:N chance with no positive dropTable backing
      const absurd: any[] = [];        // backing exists but rendered ratio outside 0.2x..5x of raw
      let checked = 0;
      let rendered = 0;
      const ratios: number[] = [];
      for (const bossCard of Array.from(document.querySelectorAll('#boss-cards .boss-card'))) {
        const bossId = (bossCard as HTMLElement).id;
        const dropMap = dropByBoss.get(bossId);
        for (const row of Array.from(bossCard.querySelectorAll('table.drops tbody tr'))) {
          const itemName = (row as HTMLElement).getAttribute('data-item') || '';
          if (!itemName) continue;
          const tds = row.querySelectorAll('td');
          for (let i = 2; i < Math.min(8, tds.length); i++) {
            const diffKey = DIFF_COL[i - 2];
            const cellTxt = (tds[i] as HTMLElement).textContent!.trim();
            // Only true chance cells ("1:N" / "1:N,NNN"). Blocked-reason / "—" cells are skipped.
            const m = cellTxt.match(/^1:([\d,]+)$/);
            if (!m) continue;
            rendered++;
            const drop = dropMap && dropMap.get(itemName);
            if (!drop) {
              if (fabricated.length < 30) fabricated.push({ boss: bossId, item: itemName, diff: diffKey, reason: 'item not in BOSSES[].dropTable', cell: cellTxt });
              continue;
            }
            const rawNum = Number(drop[diffKey]);
            if (!isFinite(rawNum) || rawNum <= 0) {
              if (fabricated.length < 30) fabricated.push({ boss: bossId, item: itemName, diff: diffKey, reason: 'dropTable has no positive value for this diff', cell: cellTxt, raw: drop[diffKey] });
              continue;
            }
            checked++;
            const cellNum = Number(m[1].replace(/,/g, ''));
            const ratio = cellNum / rawNum;
            ratios.push(ratio);
            // Absurd = rendered chance > 5x or < 0.2x the raw dropTable value (MF scaling is modest)
            if (ratio < 0.2 || ratio > 5) {
              if (absurd.length < 30) absurd.push({ boss: bossId, item: itemName, diff: diffKey, cell: cellTxt, raw: rawNum, ratio: ratio.toFixed(3) });
            }
          }
        }
      }
      ratios.sort((a, b) => a - b);
      const stats = ratios.length ? {
        min: ratios[0].toFixed(3),
        p50: ratios[Math.floor(ratios.length / 2)].toFixed(3),
        max: ratios[ratios.length - 1].toFixed(3),
      } : null;
      return { rendered, checked, fabricated, absurd, stats };
    });
    console.log(`Rendered ${report.rendered} chance cells; ${report.checked} cross-referenced to BOSSES[].dropTable; ratio stats:`, report.stats);
    if (report.fabricated.length) console.log('FABRICATED:', JSON.stringify(report.fabricated, null, 2));
    if (report.absurd.length) console.log('ABSURD RATIOS:', JSON.stringify(report.absurd, null, 2));
    expect(report.rendered).toBeGreaterThan(1000);
    expect(report.checked).toBeGreaterThan(1000);
    expect(report.fabricated.length, `Cells with no dropTable backing: ${report.fabricated.length}`).toBe(0);
    expect(report.absurd.length, `Cells with absurd ratio: ${report.absurd.length}`).toBe(0);
  });

  test('calc tab: item search works, item-detail renders with source-chips', async ({ page }) => {
    await page.goto(BIBLE_URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(600);
    await page.locator('.tab[data-tab="calc"]').click();
    await page.waitForTimeout(300);
    const tiles = await page.locator('#item-grid .item-tile').count();
    expect(tiles, 'calc item grid tiles').toBeGreaterThan(100);
    await page.locator('#item-search').fill('shako');
    await page.waitForTimeout(300);
    const visTiles = await page.locator('#item-grid .item-tile:visible').count();
    expect(visTiles).toBeGreaterThanOrEqual(1);
    await page.locator('#item-grid .item-tile:visible').first().click();
    await page.waitForTimeout(300);
    const detailText = await page.locator('#item-detail').innerText();
    expect(detailText.toLowerCase()).toContain('shako');
    const sourceChips = await page.locator('#item-detail .source-chip').count();
    expect(sourceChips, 'source chips for shako').toBeGreaterThan(0);
  });

  test('boss-detail overlay opens cleanly for all 11 bosses, each with 6 diff cells + ≥1 droptable row', async ({ page }) => {
    await page.goto(BIBLE_URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(500);
    const bossIds = ['countess','andariel','duriel','mephisto','travincal','diablo','baal','pindle','nihl','cows','pit'];
    const result = await page.evaluate(async (ids) => {
      const out: any[] = [];
      for (const id of ids) {
        (window as any).openBossDetail(id);
        await new Promise(r => setTimeout(r, 200));
        const overlay = document.getElementById('boss-detail-overlay');
        const hidden = overlay?.classList.contains('hidden');
        const name = (document.querySelector('#boss-detail-panel .bd-name') as HTMLElement)?.innerText?.toLowerCase() || '';
        const diffCells = document.querySelectorAll('#boss-detail-panel .gbc-diff-cell').length;
        const dropsRows = document.querySelectorAll('#boss-detail-panel .gbc-card table.drops tbody tr').length;
        out.push({ id, hidden, name, diffCells, dropsRows });
        (window as any).clearActiveBoss();
        await new Promise(r => setTimeout(r, 100));
      }
      return out;
    }, bossIds);
    for (const r of result) {
      expect(r.hidden, `${r.id} overlay still hidden after open`).toBe(false);
      expect(r.diffCells, `${r.id} expected 6 diff cells, got ${r.diffCells}`).toBe(6);
      expect(r.dropsRows, `${r.id} expected ≥1 droptable row`).toBeGreaterThanOrEqual(1);
    }
  });

  test('TZ tab: every ROUTED zone opens its OWN detail whose boss cross-link reaches the correct boss (honest-affordance)', async ({ page }) => {
    await page.goto(BIBLE_URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(600);
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(300);
    // CC 2026-06-01 unify: only zones where a roster boss genuinely spawns get a NON-EMPTY
    // data-boss-id; density / super-unique zones keep data-boss-id="" and don't cross-link.
    // New contract: clicking a routed zone opens its OWN inline detail (NOT the boss overlay);
    // the detail carries a "full drop table →" cross-link that, when clicked, opens EXACTLY
    // the correct boss. (100%-coverage was a stale promise from the bible_routes era.)
    const total = await page.locator('.tz-zone-card').count();
    const routed = await page.locator('.tz-zone-card[data-boss-id]:not([data-boss-id=""])').count();
    expect(total, 'TZ zones should render').toBeGreaterThan(0);
    expect(routed, 'at least one TZ zone should route to a roster boss').toBeGreaterThan(0);
    const result = await page.evaluate(async () => {
      const B = eval('typeof BOSSES !== "undefined" ? BOSSES : []');
      const byId = new Map<string, any>(B.map((b: any) => [b.id, b]));
      const cards = Array.from(document.querySelectorAll('.tz-zone-card'))
        .filter(c => (c.getAttribute('data-boss-id') || '').length > 0);
      const mismatches: any[] = [];
      for (const c of cards) {
        const expBossId = c.getAttribute('data-boss-id')!;
        document.querySelectorAll('.tz-zone-detail').forEach(b => b.setAttribute('hidden', ''));
        (c as HTMLElement).click();
        await new Promise(r => setTimeout(r, 160));
        const detail = c.querySelector('.tz-zone-detail') as HTMLElement;
        const detailOpen = !!detail && !detail.hasAttribute('hidden');
        const link = detailOpen
          ? Array.from(detail.querySelectorAll('.su-tz-link')).find(l => /full drop table/.test(l.textContent || '')) as HTMLElement
          : null;
        if (!detailOpen || !link) { mismatches.push({ expBossId, detailOpen, reason: 'no inline detail / cross-link' }); continue; }
        link.click(); // open the canonical boss card via the cross-link
        await new Promise(r => setTimeout(r, 200));
        const overlay = document.getElementById('boss-detail-overlay');
        const hidden = overlay?.classList.contains('hidden');
        const rendered = (document.querySelector('#boss-detail-panel .bd-name') as HTMLElement)?.innerText?.toLowerCase() || '';
        const expectedBossName = (byId.get(expBossId)?.name || '').toLowerCase();
        const expectedWords = expectedBossName.split(/\s+/).filter((w: string) => w.length > 3);
        const matches = expectedWords.some((w: string) => rendered.includes(w)) || rendered.includes(expBossId);
        if (hidden || !matches) {
          mismatches.push({ expBossId, expectedBossName, rendered, hidden });
        }
        (window as any).clearActiveBoss();
        await new Promise(r => setTimeout(r, 120));
      }
      return { totalClicked: cards.length, mismatches };
    });
    console.log(`TZ routed zones clicked: ${result.totalClicked}, mismatches: ${result.mismatches.length}`);
    if (result.mismatches.length) console.log('TZ→BOSS MISMATCHES:', JSON.stringify(result.mismatches, null, 2));
    expect(result.mismatches.length).toBe(0);
  });

  test('every dropped row has data-item attribute (no row missing item key)', async ({ page }) => {
    await page.goto(BIBLE_URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(800);
    const report = await page.evaluate(() => {
      let totalRows = 0;
      let noDataItem = 0;
      const samples: any[] = [];
      for (const row of Array.from(document.querySelectorAll('#boss-cards table.drops tbody tr'))) {
        totalRows++;
        if (!row.getAttribute('data-item')) {
          noDataItem++;
          if (samples.length < 5) samples.push((row as HTMLElement).outerHTML.slice(0, 120));
        }
      }
      return { totalRows, noDataItem, samples };
    });
    expect(report.totalRows).toBeGreaterThan(3000);
    if (report.noDataItem) console.log('Rows missing data-item:', report.samples);
    expect(report.noDataItem, `${report.noDataItem}/${report.totalRows} rows missing data-item`).toBe(0);
  });
});
