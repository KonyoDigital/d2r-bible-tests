const { chromium } = require('@playwright/test');
const path = require('path');
async function measure() {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    const t0 = Date.now();
    await page.goto('file://' + path.resolve(__dirname, 'bible.html'));
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(500);
    const load_ms = Date.now() - t0;
    const t1 = Date.now();
    await page.evaluate(() => window.openBossDetail('pindle'));
    await page.waitForTimeout(50);
    const boss_ms = Date.now() - t1;
    await page.keyboard.press('Escape');
    await page.locator('.tab[data-tab="calc"]').click();
    await page.evaluate(() => { selectedItem = "Templar's Might"; if (typeof renderDetail==='function') renderDetail(); });
    await page.waitForTimeout(400);
    await page.evaluate(() => window.setPuvTrials(2000));
    const t2 = Date.now();
    await page.evaluate(() => document.querySelector('.puv-sim-btn').click());
    await page.waitForTimeout(4500);
    const sim_ms = Date.now() - t2;
    return { load_ms, boss_ms, sim_2000_ms: sim_ms };
  } finally {
    // a run that throws must still close its browser - the loop below catches and goes on, and a
    // leaked Chromium per failed pass is what the #231 eye found (REG-2034)
    await browser.close();
  }
}
(async () => {
  const runs = [];
  for (let i = 0; i < 3; i++) {
    try { runs.push(await measure()); } catch (e) { console.error('K_perf: run ' + (i + 1) + ' failed - ' + ((e && e.message) || e)); }
  }
  if (runs.length === 0) { console.log(JSON.stringify({ error: 'all runs failed' })); return; }
  // Take BEST result for each metric (lowest = fastest)
  const best = {
    load_ms: Math.min(...runs.map(r => r.load_ms)),
    boss_ms: Math.min(...runs.map(r => r.boss_ms)),
    sim_2000_ms: Math.min(...runs.map(r => r.sim_2000_ms)),
    runs: runs.length
  };
  console.log(JSON.stringify(best));
})();
