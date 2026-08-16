const { chromium } = require('@playwright/test');
const path = require('path');
const fs = require('fs');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(__dirname, 'bible.html'));
  await page.waitForTimeout(800);
  const data = await page.evaluate(() => {
    const probe = (name, bid) => {
      const it = ITEMS.find(i => i.n === name);
      // 2026-08-16 (v1716) — A PROBE THAT CANNOT FIND ITS ITEM MUST NOT LOOK LIKE A CLEAN READ.
      // probe_anda_soj and probe_anda_bk had BOTH been returning {} since the day they were
      // written — the rows are called "The Stone of Jordan" and "Bul-Kathos Wedding Band"
      // (no apostrophe), so `i.n === name` never matched — and {} was then committed into
      // baseline/integrity_baseline.json as the expected value. Two of this gate's four probes
      // were guarding nothing, permanently, and the baseline said they agreed.
      if (!it) return { __NOT_FOUND: name };
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
      probe_anda_soj: probe("The Stone of Jordan", 'andariel'),
      probe_anda_bk: probe("Bul-Kathos Wedding Band", 'andariel'),
      probe_countess_ist: probe("Ist rune", 'countess'),
    };
  });
  fs.writeFileSync('/tmp/L_result.json', JSON.stringify(data));
  await browser.close();
})();
