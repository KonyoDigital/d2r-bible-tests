// END-TO-END AUDIT v2 — all phases including Phase 6 (calc tab via API)
const { chromium } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGE: ' + e.message.substring(0, 180)));
  page.on('console', m => { if (m.type() === 'error') errors.push('CON: ' + m.text().substring(0, 180)); });
  // v1455: a bare "Failed to load resource: net::ERR_FILE_NOT_FOUND" console line names no URL, which cost
  // three blind rounds of guessing on a CI-only red. Record the URL of every failed request so the log says
  // WHICH file is missing (Linux CI checkout lacks gitignored dirs + is case-sensitive; the Mac hides both).
  const failedReqs = [];
  page.on('requestfailed', r => failedReqs.push(`${r.failure()?.errorText || 'failed'} ${r.resourceType()} ${r.url()}`));
  /* 2026-08-17 (after v1741 went red on nothing) — AND NAME THE 404s TOO. The note above was written because an unnamed missing file cost
     three blind rounds of guessing, and it hooks `requestfailed` — which an HTTP 404 never fires,
     because a 404 is a SUCCESSFUL response carrying a failure status. So a 404 still reached the
     log as the bare line "Failed to load resource: the server responded with a status of 404 ()",
     with no URL, which is the exact defect that note closed for a different failure mode.
     v1741 hit it: Routine G went red on three unnamed 404s and a Google-Fonts abort, and a rerun of
     the SAME COMMIT came back 8/8 green with zero failed requests. */
  const badResponses = [];
  page.on('response', r => { if (r.status() >= 400) badResponses.push(`HTTP ${r.status()} ${r.request().resourceType()} ${r.url()}`); });
  /* EXTERNAL hosts are recorded but do not gate the build. A missing file in THIS repo is a defect
     and must stay red; fonts.gstatic.com having a bad minute is weather. Keeping them in one bucket
     meant the gate cried wolf on network noise, and a gate that cries wolf gets ignored on the day
     it is right. */
  const isExternal = (u) => /^https?:\/\//i.test(u) && !/^https?:\/\/(127\.0\.0\.1|localhost)/i.test(u);
  
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(' END-TO-END AUDIT — Konyo D2R Bible v36');
  console.log('═══════════════════════════════════════════════════════════════\n');
  
  const t0 = Date.now();
  await page.goto('file://' + (process.argv[2] || path.resolve(__dirname, 'bible_routes.html')));
  await page.waitForTimeout(1000);
  console.log(`✓ Page loaded in ${Date.now()-t0}ms\n`);
  
  const audit = { tabs: {}, bosses: {}, items: {}, sliders: {}, sim_heavy: {}, wishlist: {}, tz_zones: {}, routing_smoothness: { passes: 0, fails: 0 } };
  
  // PHASE 1 — Main tabs
  console.log('───────────── PHASE 1 — Main tabs ─────────────');
  const TABS = ['bosses', 'calc', 'tz', 'runes', 'rotw', 'ancients', 'ref'];
  for (const tab of TABS) {
    const t = Date.now();
    await page.locator(`.tab[data-tab="${tab}"]`).click();
    await page.waitForTimeout(180);
    const childCount = await page.locator(`#tab-${tab} *`).count();
    const isActive = await page.evaluate(t => /\bactive\b/.test(document.querySelector(`#tab-${t}`)?.className || ''), tab);
    audit.tabs[tab] = { active: isActive, children: childCount, ms: Date.now()-t };
    console.log(`  ${isActive && childCount > 10 ? '✓' : '✗'} ${tab.padEnd(9)} ${childCount} children · ${Date.now()-t}ms`);
  }
  await page.locator('.tab[data-tab="bosses"]').click();
  await page.waitForTimeout(200);
  
  // PHASE 2 — All 11 boss chips
  console.log('\n───────────── PHASE 2 — All 11 boss chips ─────────────');
  const BOSSES = ['countess','andariel','duriel','mephisto','travincal','diablo','baal','pindle','nihl','cows','pit'];
  for (const b of BOSSES) {
    const t = Date.now();
    await page.evaluate((id) => window.openBossDetail(id), b);
    await page.waitForTimeout(150);
    const overlayHidden = await page.evaluate(() => document.getElementById('boss-detail-overlay')?.classList.contains('hidden'));
    const name = await page.locator('.boss-detail-header .bd-name').first().textContent().catch(() => '?');
    const pickCount = await page.locator('#hero-picks .hero-pick').count();
    await page.keyboard.press('Escape');
    await page.waitForTimeout(100);
    const closedOk = await page.evaluate(() => document.getElementById('boss-detail-overlay')?.classList.contains('hidden'));
    audit.bosses[b] = { opened: !overlayHidden, name, pick_count: pickCount, closed_via_esc: closedOk, ms: Date.now()-t };
    const pass = !overlayHidden && closedOk;
    console.log(`  ${pass ? '✓' : '✗'} ${b.padEnd(10)} → "${(name||'?').substring(0,18).padEnd(18)}" · ${pickCount} picks · Esc=${closedOk?'✓':'✗'} · ${Date.now()-t}ms`);
    if (pass) audit.routing_smoothness.passes++; else audit.routing_smoothness.fails++;
  }
  
  // PHASE 3 — Every item 1-by-1
  console.log('\n───────────── PHASE 3 — All items (1-by-1) ─────────────');
  const allItems = await page.evaluate(() => ITEMS.map(i => ({ n: i.n, sources: i.sources?.length || 0 })));
  console.log(`  Registry size: ${allItems.length}`);
  const itemFails = [];
  let opened = 0, withSim = 0, withSources = 0;
  const phaseT = Date.now();
  for (let i = 0; i < allItems.length; i++) {
    const item = allItems[i];
    try {
      await page.evaluate((name) => window.openItemDetail(name), item.n);
      await page.waitForTimeout(15);
      const state = await page.evaluate(() => {
        const panel = document.getElementById('item-detail-panel');
        return {
          cardOpen: panel && !panel.classList.contains('hidden') && panel.innerHTML.length > 100,
          simVisible: !!document.getElementById('gic-sim-runs'),
          sourceCells: document.querySelectorAll('.gic-source-cell').length
        };
      });
      audit.items.tested = (audit.items.tested || 0) + 1;
      if (state.cardOpen) {
        opened++;
        if (state.simVisible) withSim++;
        if (state.sourceCells > 0) withSources++;
      } else if (item.sources > 0) {
        itemFails.push({ name: item.n, sources: item.sources });
      }
      await page.evaluate(() => window.closeItemDetail && window.closeItemDetail());
      if ((i+1) % 60 === 0 || i === allItems.length - 1) {
        process.stdout.write(`\r  ${i+1}/${allItems.length} · ${opened} opened · ${withSim} sim · ${itemFails.length} fails`);
      }
    } catch (e) {
      itemFails.push({ name: item.n, error: e.message.substring(0, 80) });
    }
  }
  console.log(`\n  ✓ ${opened}/${allItems.length} opened · ${withSim} with sim · ${withSources} with sources · ${((Date.now()-phaseT)/1000).toFixed(1)}s`);
  audit.items = { tested: allItems.length, opened, sim_visible: withSim, sources_present: withSources, fail_count: itemFails.length, errors: itemFails.slice(0, 10) };
  
  // PHASE 4 — Sliders
  console.log('\n───────────── PHASE 4 — Sliders ─────────────');
  await page.evaluate(() => { const m = document.getElementById('mf'); m.value = '500'; m.dispatchEvent(new Event('input', {bubbles:true})); });
  await page.waitForTimeout(200);
  const mf500 = (await page.locator('#hero-sub').textContent()).match(/(\d+)% MF/)?.[1];
  audit.sliders.mf_500 = mf500 === '500';
  console.log(`  MF=500: ${mf500 === '500' ? '✓' : '✗'} reads "${mf500}%"`);
  
  await page.evaluate(() => { const m = document.getElementById('mf'); m.value = '1000'; m.dispatchEvent(new Event('input', {bubbles:true})); });
  await page.waitForTimeout(200);
  const mf1000 = (await page.locator('#hero-sub').textContent()).match(/(\d+)% MF/)?.[1];
  audit.sliders.mf_1000 = mf1000 === '1000';
  console.log(`  MF=1000 (max): ${mf1000 === '1000' ? '✓' : '✗'} reads "${mf1000}%"`);
  
  await page.evaluate(() => window.setMFPreset(699));
  await page.waitForTimeout(150);
  const mfAfter = await page.evaluate(() => document.getElementById('mf')?.value);
  audit.sliders.mf_preset_699 = mfAfter === '699';
  console.log(`  MF preset 699 (Konyolock): ${mfAfter === '699' ? '✓' : '✗'} slider reads "${mfAfter}"`);
  
  await page.evaluate(() => window.setMFPreset(553));
  await page.waitForTimeout(150);
  const mfAfter2 = await page.evaluate(() => document.getElementById('mf')?.value);
  audit.sliders.mf_preset_553 = mfAfter2 === '553';
  console.log(`  MF preset 553 (Konyolock MF-swap): ${mfAfter2 === '553' ? '✓' : '✗'} slider reads "${mfAfter2}"`);
  
  // PHASE 5 — Wishlist
  console.log('\n───────────── PHASE 5 — Wishlist Hunt Path ─────────────');
  const wishEmpty = await page.evaluate(() => {
    const card = document.getElementById('wishlist-hunt-path');
    return { hasSuggestions: card?.querySelectorAll('.wishlist-suggest-chip').length || 0 };
  });
  audit.wishlist.empty_state = wishEmpty.hasSuggestions > 0;
  console.log(`  Empty state: ${audit.wishlist.empty_state ? '✓' : '✗'} ${wishEmpty.hasSuggestions} quick-add chips`);
  
  await page.evaluate(() => {
    wishlist.add("Templar's Might"); wishlist.add("Andariel's Visage"); wishlist.add("Harlequin Crest (Shako)");
    window.renderWishlistHuntPath(); window.renderHero();
  });
  await page.waitForTimeout(250);
  const wishPop = await page.evaluate(() => {
    const card = document.getElementById('wishlist-hunt-path');
    return { items: card?.querySelectorAll('.wishlist-item').length || 0, statTiles: card?.querySelectorAll('.wishlist-summary-stat-val').length || 0 };
  });
  audit.wishlist.populated_state = wishPop.items >= 3;
  console.log(`  Populated (3 starred): ${audit.wishlist.populated_state ? '✓' : '✗'} ${wishPop.items} cards · ${wishPop.statTiles} stat tiles`);
  await page.evaluate(() => { wishlist.clear(); window.renderWishlistHuntPath(); window.renderHero(); });
  
  // PHASE 6 — Power User 2000-trial sim (calc tab via API, no DOM click)
  console.log('\n───────────── PHASE 6 — Power User 2000-trial sim ─────────────');
  await page.locator('.tab[data-tab="calc"]').click();
  await page.waitForTimeout(300);
  // Select item via API — set selectedItem and trigger renderDetail directly
  await page.evaluate(() => {
    selectedItem = "Harlequin Crest (Shako)";
    if (typeof renderDetail === 'function') renderDetail();
    if (typeof setActiveItem === 'function') setActiveItem(selectedItem);
  });
  await page.waitForTimeout(400);
  
  const puvExists = await page.evaluate(() => !!document.querySelector('.puv-deep-dive'));
  console.log(`  Power User panel: ${puvExists ? '✓' : '✗'}`);
  
  if (puvExists) {
    const confCells = await page.evaluate(() => document.querySelectorAll('.puv-conf-cell').length);
    const mfCells = await page.evaluate(() => document.querySelectorAll('.puv-mf-cell').length);
    const trialChips = await page.evaluate(() => document.querySelectorAll('.puv-trial-chip').length);
    console.log(`    Confidence cells: ${confCells}/7 · MF cells: ${mfCells} · Trial chips: ${trialChips}/4`);
    
    await page.evaluate(() => window.setPuvTrials(2000));
    await page.waitForTimeout(100);
    const simT = Date.now();
    await page.evaluate(() => document.querySelector('.puv-sim-btn').click());
    await page.waitForTimeout(3500); // 2000 × 500 = 1M Math.random
    const elapsed = Date.now() - simT;
    
    const simResult = await page.evaluate(() => ({
      bars: document.querySelectorAll('.puv-histo-col').length,
      stats: document.querySelectorAll('.puv-stat').length,
      meta: document.querySelector('.puv-sim-meta')?.textContent?.trim(),
      observedAvg: document.querySelectorAll('.puv-stat-val')[1]?.textContent
    }));
    audit.sim_heavy = { ran_ok: simResult.bars > 0 && simResult.stats >= 7, elapsed_ms: elapsed, bars: simResult.bars, stats: simResult.stats, conf_cells: confCells, mf_cells: mfCells };
    console.log(`    2000 trials × 500 runs (1M kills): ${audit.sim_heavy.ran_ok ? '✓' : '✗'}`);
    console.log(`    ${elapsed}ms · ${simResult.bars} histo bars · ${simResult.stats}/9 stats`);
    console.log(`    "${simResult.meta?.substring(0, 100)}"`);
    console.log(`    Observed avg drops: ${simResult.observedAvg}`);
  }
  
  // PHASE 7 — TZ subtab routing
  console.log('\n───────────── PHASE 7 — TZ zone routing ─────────────');
  await page.locator('.tab[data-tab="tz"]').click();
  await page.waitForTimeout(300);
  const tzZones = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('.tz-zone-card')).map(card => ({
      name: card.querySelector('.tz-zone-name')?.textContent?.trim(),
      bossId: card.getAttribute('data-boss-id'),
      hasOnclick: card.hasAttribute('onclick')
    }));
  });
  const tzRouted = tzZones.filter(z => z.bossId && z.hasOnclick).length;
  // Honest-affordance design (TZ_BOSS_MAP): ONLY zones where an 11-roster boss spawns get a
  // data-boss-id; density / super-unique-only zones intentionally have empty data-boss-id and
  // are non-routing. So `unrouted > 0` is EXPECTED, not a regression. The integrity check is:
  // no zone is half-mapped (a bossId present without a click handler).
  const tzHalfMapped = tzZones.filter(z => z.bossId && !z.hasOnclick).length;
  audit.tz_zones = { total: tzZones.length, routed: tzRouted, unrouted: tzZones.length - tzRouted, half_mapped: tzHalfMapped };
  console.log(`  ${tzRouted}/${tzZones.length} zones routed (rest are by-design density/super-unique, non-routing)${tzHalfMapped ? ` · ⚠ ${tzHalfMapped} half-mapped` : ''}`);
  
  // Test one click roundtrip: TZ zone → boss overlay
  if (tzZones.length > 0) {
    const tzFirst = tzZones.find(z => z.bossId);
    if (tzFirst) {
      await page.evaluate((id) => window.openBossDetail(id), tzFirst.bossId);
      await page.waitForTimeout(200);
      const overlayOpened = await page.evaluate(() => !document.getElementById('boss-detail-overlay')?.classList.contains('hidden'));
      console.log(`    TZ "${tzFirst.name}" → boss "${tzFirst.bossId}" overlay: ${overlayOpened ? '✓' : '✗'}`);
      audit.tz_zones.routing_works = overlayOpened;
      await page.keyboard.press('Escape');
    }
  }
  
  // ══════════ SUMMARY ══════════
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log(' AUDIT SUMMARY');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`Total time: ${((Date.now()-t0)/1000).toFixed(1)}s`);
  /* 2026-08-17 — a bare "Failed to load resource" console line is the SAME event the request tracking
     above already recorded, and it is the copy that carries no URL. Counting both meant one missing
     file scored twice and one EXTERNAL miss reddened the build with a line nobody could act on.
     The resource story is told once, by `Failed requests`, with the URL attached. */
  const resourceNoise = /Failed to load resource/i;
  const realErrors = errors.filter((e) => !resourceNoise.test(e));
  const droppedNoise = errors.length - realErrors.length;
  console.log(`Page errors: ${realErrors.length}${realErrors.length ? '\n  ' + realErrors.slice(0,3).join('\n  ') : ''}`
    + (droppedNoise ? `  (+${droppedNoise} resource-load line${droppedNoise===1?'':'s'} — see Failed requests, which names the URL)` : ''));
  const allFailed = [...new Set(failedReqs.concat(badResponses))];
  const uniqFailed = allFailed.filter(u => !isExternal(u.replace(/^\S+\s+\S+\s+/, '')));
  const externalFailed = allFailed.filter(u => isExternal(u.replace(/^\S+\s+\S+\s+/, '')));
  console.log(`Failed requests: ${uniqFailed.length}${uniqFailed.length ? '\n  ' + uniqFailed.slice(0,20).map(u => 'REQ: ' + u).join('\n  ') : ''}`);
  if (externalFailed.length) {
    console.log(`External (recorded, not gated): ${externalFailed.length}\n  ` + externalFailed.slice(0,10).map(u => 'EXT: ' + u).join('\n  '));
  }
  audit.failed_requests = uniqFailed;
  audit.external_failed_requests = externalFailed;
  
  const tabsOk = Object.values(audit.tabs).filter(t => t.active && t.children > 10).length;
  const slidersOk = audit.sliders.mf_500 && audit.sliders.mf_1000 && audit.sliders.mf_preset_699 && audit.sliders.mf_preset_553;
  const wishOk = audit.wishlist.empty_state && audit.wishlist.populated_state;
  
  console.log(`\nTabs (7):       ${tabsOk}/7 active+populated`);
  console.log(`Bosses (11):    ${audit.routing_smoothness.passes}/11 open+close cleanly`);
  console.log(`Items (${audit.items.tested}):   ${audit.items.opened} opened · ${audit.items.sim_visible} with sim · ${audit.items.fail_count} fails`);
  console.log(`Sliders:        MF=500 ${audit.sliders.mf_500?'✓':'✗'} · MF=1000 ${audit.sliders.mf_1000?'✓':'✗'} · 699 ${audit.sliders.mf_preset_699?'✓':'✗'} · 553 ${audit.sliders.mf_preset_553?'✓':'✗'}`);
  console.log(`Wishlist:       empty ${audit.wishlist.empty_state?'✓':'✗'} · populated ${audit.wishlist.populated_state?'✓':'✗'}`);
  console.log(`Heavy sim:      2000 trials in ${audit.sim_heavy.elapsed_ms||'?'}ms ${audit.sim_heavy.ran_ok?'✓':'✗'}`);
  // TZ category passes when the honest-affordance contract holds: no zone is half-mapped, and
  // when at least one zone maps the click→boss roundtrip works. Unrouted density zones are fine.
  const tzOk = (audit.tz_zones?.half_mapped === 0) && (audit.tz_zones?.routed === 0 || audit.tz_zones?.routing_works === true);
  console.log(`TZ routing:     ${audit.tz_zones?.routed}/${audit.tz_zones?.total} mapped ${tzOk ? '✓' : '✗'} · click→boss ${audit.tz_zones?.routing_works?'✓':'✗'} · (unrouted = by-design density zones)`);
  
  if (audit.items.fail_count > 0) {
    console.log(`\nFirst ${Math.min(10, audit.items.fail_count)} item fails:`);
    audit.items.errors.forEach(f => console.log(`  - "${f.name}" (${f.sources||'?'} sources)`));
  }
  
  const checks = [
    tabsOk === 7,
    audit.routing_smoothness.passes === 11,
    audit.items.fail_count === 0,
    slidersOk,
    wishOk,
    audit.sim_heavy.ran_ok,
    tzOk,
    /* 2026-08-17 — real page errors AND any LOCAL resource that failed to load. External hosts are
       reported but never gate: a CDN having a bad minute is weather, and v1741 went red on exactly
       that (three unnamed 404s + a Google-Fonts abort) while a rerun of the same commit was 8/8. */
    realErrors.length === 0 && uniqFailed.length === 0
  ];
  const passed = checks.filter(Boolean).length;
  console.log(`\n${passed === 8 ? '🎯 ALL 8 GREEN' : passed >= 6 ? '⚠️  MOSTLY GREEN' : '❌ ISSUES'} · ${passed}/8 categories passed`);
  
  fs.writeFileSync(path.resolve(__dirname, 'audit_v36_report.json'), JSON.stringify(audit, null, 2));
  console.log(`\n📄 Full report: audit_v36_report.json`);
  
  await browser.close();
})();
