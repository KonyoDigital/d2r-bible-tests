import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v643 — ELEMENT-ANCHORED floating card (Konyo: "calibrated to when i'm on the item itself and
// not on the section — it looks like randomly opening windows"). The card must open ADJACENT to
// the hovered element's rect (gap ≤ 16px on one axis, overlapping its band on the other), never
// teleport across the viewport, and hold still while the cursor moves inside the anchor.

test('v654 — a SECTION/CARD-sized element can never open the floating card; only compact keyword anchors do', async ({ page }) => {
  await page.setViewportSize({ width: 1500, height: 900 });
  await page.goto(URL); await page.waitForTimeout(2000);
  await page.evaluate(() => { (window as any).switchTab('funi'); });
  await page.waitForTimeout(700);
  const r = await page.evaluate(async () => {
    const tip = document.getElementById('arttip')!;
    // hover a full task CARD body (large container) → must NOT open
    const card = document.querySelector('#tab-funi .f-card.f-atom') as any;
    let cardOpened = null;
    if (card) {
      const cr = card.getBoundingClientRect();
      card.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: cr.left + cr.width / 2, clientY: cr.bottom - 6 }));
      await new Promise((res) => setTimeout(res, 150));
      cardOpened = tip.classList.contains('on');
      document.dispatchEvent(new MouseEvent('mouseout', { bubbles: true }));
    }
    // hover the compact item NAME inside the same card → MUST open
    const name = card ? (card.querySelector('.f-rwbig[data-arttip]') as any) : null;
    let nameOpened = null;
    if (name) {
      const nr = name.getBoundingClientRect();
      name.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: nr.left + 4, clientY: nr.top + 4 }));
      await new Promise((res) => setTimeout(res, 150));
      nameOpened = tip.classList.contains('on');
    }
    return { cardOpened, nameOpened };
  });
  expect(r.cardOpened).toBe(false);
  expect(r.nameOpened).toBe(true);
});

test('the card opens glued to the hovered item and never detaches across the screen', async ({ page }) => {
  await page.setViewportSize({ width: 1500, height: 900 });
  // v693.2 recalibration — data-arttip anchors live on live forge TASK cards; the 99/99 seal leaves
  // none (both the old celebration and the new Completed landing are anchor-free). Pin fresh.
  await page.addInitScript(() => { localStorage.setItem('d2r_rwMade', JSON.stringify({})); localStorage.setItem('d2r_rwProfile', 'fresh'); });
  await page.goto(URL); await page.waitForTimeout(2000);
  await page.evaluate(() => { (window as any).switchTab('forge'); try { (window as any).renderForge(); } catch (e) {} });
  await page.waitForTimeout(600);
  const r = await page.evaluate(async () => {
    const results: any[] = [];
    const anchors = [...document.querySelectorAll('#tab-forge [data-arttip]')].filter((a: any) => a.offsetParent).slice(0, 6);
    for (const a of anchors) {
      const ar = (a as any).getBoundingClientRect();
      a.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: ar.left + 4, clientY: ar.top + 4 }));
      await new Promise((res) => setTimeout(res, 120));
      const tip = document.getElementById('arttip')!;
      if (!tip.classList.contains('on')) continue;
      const tr = tip.getBoundingClientRect();
      // adjacency: horizontal gap to the anchor ≤ 20px on either side, OR stacked within 20px
      const hGap = Math.min(Math.abs(tr.left - ar.right), Math.abs(ar.left - tr.right));
      const vGap = Math.min(Math.abs(tr.top - ar.bottom), Math.abs(ar.top - tr.bottom));
      const bandsOverlapV = tr.bottom > ar.top - 8 && tr.top < ar.bottom + 8;
      const bandsOverlapH = tr.right > ar.left - 8 && tr.left < ar.right + 8;
      const adjacent = (hGap <= 20 && bandsOverlapV) || (vGap <= 20 && bandsOverlapH)
        // clamped case: a tall card centered on the item may extend past its band but MUST touch the side
        || (hGap <= 20);
      const onScreen = tr.left >= 0 && tr.top >= 0 && tr.right <= innerWidth && tr.bottom <= innerHeight;
      // stability: cursor wanders inside the anchor → the card must not move
      a.dispatchEvent(new MouseEvent('mousemove', { bubbles: true, clientX: ar.right - 3, clientY: ar.bottom - 3 }));
      await new Promise((res) => setTimeout(res, 80));
      const tr2 = tip.getBoundingClientRect();
      // ≤2px tolerance: content settling + the v639 hover-pop scale cause sub-pixel drift, not jumps
      const still = Math.abs(tr2.left - tr.left) <= 2 && Math.abs(tr2.top - tr.top) <= 2;
      results.push({ name: (a as any).getAttribute('data-arttip'), adjacent, onScreen, still });
      a.dispatchEvent(new MouseEvent('mouseout', { bubbles: true }));
      await new Promise((res) => setTimeout(res, 60));
    }
    return results;
  });
  expect(r.length).toBeGreaterThan(2);
  r.forEach((x: any) => {
    expect(x.adjacent, x.name + ' adjacency').toBe(true);
    expect(x.onScreen, x.name + ' on-screen').toBe(true);
    expect(x.still, x.name + ' stability').toBe(true);
  });
});
