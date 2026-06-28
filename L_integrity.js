const { chromium } = require('@playwright/test');
const path = require('path');
const fs = require('fs');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + (process.argv[2] || path.resolve(__dirname, 'bible.html')));
  await page.waitForTimeout(800);
  const data = await page.evaluate(() => {
    const probe = (name, bid) => {
      const it = ITEMS.find(i => i.n === name);
      if (!it) return {};
      const out = {};
      (it.sources || []).filter(s => s.bossId === bid).forEach(s => {
        out[s.diffKey] = s.chance;
      });
      return out;
    };
    return {
      items_count: ITEMS.length,
      bosses_count: BOSSES.length,
      probe_meph_shako: probe("Harlequin Crest (Shako)", 'mephisto'),
      probe_anda_soj: probe("Stone of Jordan", 'andariel'),
      probe_anda_bk: probe("Bul-Kathos' Wedding Band", 'andariel'),
      probe_countess_ist: probe("Ist rune", 'countess'),
    };
  });
  fs.writeFileSync('/tmp/L_result.json', JSON.stringify(data));
  await browser.close();
})();
