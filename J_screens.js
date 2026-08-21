/**
 * Routine J — the four reference screenshots, and (v1910) the assertions that make them a GATE.
 *
 * WHAT WAS WRONG. This script captured four PNGs, printed "captured 4 screenshots" and exited 0 —
 * always. The workflow's own header says the shots are uploaded "for manual visual review", and
 * nobody downloads a 30-day artifact daily. So Routine J reported SUCCESS for a page that could be
 * rendering four black rectangles, four copies of the same unchanged view, or a calc panel with no
 * item selected. A green lamp with no judgement is the shape this whole arc has been about.
 *
 * WHY NOT A PIXEL BASELINE. The header proposed one ("can be layered on later"), and a committed
 * baseline goes flaky the moment CI's renderer, fonts or GPU flags move — it would either be
 * disabled within a month or start crying wolf. These checks are renderer-independent: they ask
 * whether the page PAINTED something, whether the four states are actually DIFFERENT from each
 * other, and whether the state the shot claims to show is the state the page was in.
 *
 * EVERY THRESHOLD BELOW WAS MEASURED FIRST, on this page, at this viewport, through CDP (never
 * Playwright on his Mac — browser suites run on GitHub):
 *     01 bosses 564722 · 02 travincal 547477 · 03 calc 751263 · 04 tz 688303 bytes, 4 distinct md5s
 *     data-active-tab: bosses → (detail) → calc → tz
 *     openBossDetail('travincal') grows body innerText 3467 → 6251
 * MIN_BYTES is 60000: an order of magnitude under the smallest real shot and an order of magnitude
 * OVER a blank 1600x1200 PNG, which compresses to a few kilobytes. A threshold outside the signal's
 * range is an absent one wearing a tuned face.
 *
 * ⚠ AND SHOT 01 WAS NEVER THE BOSSES. The page opens on the `session` tab, so `01_bosses.png` has
 * been a picture of the session cockpit for as long as this file has existed — a name that outlived
 * its referent. It clicks the bosses tab now, which restores the intent rather than renaming the
 * evidence.
 */
const { chromium } = require('@playwright/test');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const MIN_BYTES = 60000;

(async () => {
  const out = process.argv[2];
  const page_path = process.argv[3] || path.resolve(__dirname, 'bible.html');
  const shots = [];
  const fail = (msg) => { console.error('❌ ' + msg); process.exitCode = 1; };

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } });
  await page.goto('file://' + page_path);
  await page.waitForTimeout(800);

  const activeTab = () => page.evaluate(() => document.documentElement.getAttribute('data-active-tab'));
  const textLen = () => page.evaluate(() => (document.body.innerText || '').length);
  async function shoot(name) {
    const p = out + '/' + name;
    await page.screenshot({ path: p, fullPage: false });
    const buf = fs.readFileSync(p);
    shots.push({ name, bytes: buf.length, md5: crypto.createHash('md5').update(buf).digest('hex') });
    return buf.length;
  }

  // 01 — the BOSSES tab, which this shot has always claimed to be and never was.
  await page.locator('.tab[data-tab="bosses"]').click();
  await page.waitForTimeout(400);
  if (await activeTab() !== 'bosses') fail('01: the bosses tab did not become active');
  await shoot('01_bosses.png');

  // 02 — a boss detail actually OPENS. evaluate() throws if the function is gone; the text length
  // is what proves the call did something rather than returning quietly.
  const before = await textLen();
  await page.evaluate(() => window.openBossDetail('travincal'));
  await page.waitForTimeout(600);
  const after = await textLen();
  if (!(after > before)) fail(`02: openBossDetail('travincal') changed nothing (innerText ${before} → ${after})`);
  await shoot('02_travincal_open.png');

  // 03 — the calc tab, with an item actually selected. `renderDetail` was called behind an `if`
  // that swallowed its own absence; a missing renderer now says so.
  await page.keyboard.press('Escape');
  await page.locator('.tab[data-tab="calc"]').click();
  await page.waitForTimeout(300);
  if (await activeTab() !== 'calc') fail('03: the calc tab did not become active');
  const rendered = await page.evaluate(() => {
    window.selectedItem = 'Harlequin Crest (Shako)';
    if (typeof renderDetail !== 'function') return false;
    renderDetail();
    return true;
  });
  if (!rendered) fail('03: renderDetail is gone — the calc shot shows an empty panel');
  await page.waitForTimeout(400);
  await shoot('03_calc_shako.png');

  // 04 — the TZ tab.
  await page.locator('.tab[data-tab="tz"]').click();
  await page.waitForTimeout(300);
  if (await activeTab() !== 'tz') fail('04: the tz tab did not become active');
  await shoot('04_tz.png');

  await browser.close();

  // THE TWO CHECKS THAT MAKE THE ARTIFACT WORTH UPLOADING.
  for (const s of shots) {
    if (s.bytes < MIN_BYTES) {
      fail(`${s.name} is ${s.bytes} bytes — under ${MIN_BYTES}. A capture that succeeds and paints ` +
           `nothing is the classic failure here, and it looks exactly like a pass.`);
    }
  }
  const seen = new Map();
  for (const s of shots) {
    if (seen.has(s.md5)) {
      fail(`${s.name} is byte-identical to ${seen.get(s.md5)} — the page never changed between ` +
           `them, so one of these shots is showing a state that never happened.`);
    }
    seen.set(s.md5, s.name);
  }

  for (const s of shots) console.log(`  ${s.name.padEnd(24)} ${String(s.bytes).padStart(8)} bytes  ${s.md5.slice(0, 10)}`);
  if (process.exitCode) console.error('Routine J FAILED — the shots above are not what they claim to be.');
  else console.log('captured 4 screenshots, all painted, all different, each in the state it claims');
})();
