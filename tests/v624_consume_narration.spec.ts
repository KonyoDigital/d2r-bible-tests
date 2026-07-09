import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v624 — CONSUME NARRATION (Konyo: 'how can it propose Phoenix in the 4os Phase Blade I just used
// for Kingslayer?'). The consume HAD fired on one copy of his ×2 stack — the card just never said
// so. A task whose base label has consumed siblings now narrates them.

test('a task on a label with a consumed twin says so on the card', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1800);
  await page.evaluate(() => {
    localStorage.setItem('d2r_rwProfile', 'fresh');
    localStorage.setItem('d2r_rwMade', JSON.stringify({ Kingslayer: 'Jul 9' }));
    localStorage.setItem('d2r_owned', JSON.stringify(['Phase Blade (4os)']));
    localStorage.setItem('d2r_rwBaseUsed', JSON.stringify({ Kingslayer: { l: 'Phase Blade (4os)', copy: true } }));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Vex: 2, Lo: 1, Jah: 1 }));
  });
  await page.reload(); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    w.switchTab('forge'); try { w.renderForge(); } catch (e) {}
    const dom = (document.getElementById('forge-body') || document.body).innerHTML;
    ['d2r_rwProfile', 'd2r_rwMade', 'd2r_owned', 'd2r_rwBaseUsed', 'd2r_runeStash'].forEach((k) => localStorage.removeItem(k));
    return { narrated: /already became <b>Kingslayer<\/b>/.test(dom), remaining: /REMAINING/.test(dom) };
  });
  expect(r.narrated).toBe(true);
  expect(r.remaining).toBe(true);
});
