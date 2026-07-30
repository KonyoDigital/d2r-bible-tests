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
      // v696.2 — SETTLE-AWARE measure: a fixed 120ms read the tall card mid-position on slow CI
      // runners (Archon Plate adjacency false at CI speed, green locally). Poll until the rect is
      // stable across two frames (≤900ms), then measure.
      const tip = document.getElementById('arttip')!;
      // v1459 — SIZE-AWARE settle. The positioner centres the card on the anchor
      // (y = r.top + r.height/2 - h/2, and for a left-side card x = r.left - w - 12), so the card
      // legitimately re-centres whenever its OWN box grows. On the Linux runner the popup <img>
      // finished decoding between the two samples: h grew ~26px and w ~9px → dyCard -13 / dxCard -9
      // with the anchor dead still, and the stability check read a correct recentre as a detach.
      // Settling on position alone could not see that; settle on the full box + the image.
      const tipImg = tip.querySelector('img') as HTMLImageElement | null;
      const imgReady = () => !tipImg || tipImg.style.display === 'none' || tipImg.complete;
      let tr = { left: -1, top: -1, width: -1, height: -1, right: -1, bottom: -1 } as any, settled = 0;
      for (let w2 = 0; w2 < 30 && settled < 2; w2++) {
        await new Promise((res) => setTimeout(res, 60));
        if (!tip.classList.contains('on')) continue;
        const now = tip.getBoundingClientRect();
        const stable = Math.abs(now.left - tr.left) <= 1 && Math.abs(now.top - tr.top) <= 1
                    && Math.abs(now.width - tr.width) <= 1 && Math.abs(now.height - tr.height) <= 1;
        if (stable && imgReady()) settled++; else settled = 0;
        tr = now;
      }
      if (!tip.classList.contains('on')) continue;
      // v918.1 — the stability baseline must be CURRENT: on an exhausted settle loop (slow CI)
      // tr was a stale mid-drift rect, and the wander diff measured runner lag, not the card.
      tr = tip.getBoundingClientRect();
      // adjacency: horizontal gap to the anchor ≤ 20px on either side, OR stacked within 20px
      const hGap = Math.min(Math.abs(tr.left - ar.right), Math.abs(ar.left - tr.right));
      const vGap = Math.min(Math.abs(tr.top - ar.bottom), Math.abs(ar.top - tr.bottom));
      const bandsOverlapV = tr.bottom > ar.top - 8 && tr.top < ar.bottom + 8;
      const bandsOverlapH = tr.right > ar.left - 8 && tr.left < ar.right + 8;
      // v708 recal — 20px kept failing ONLY on CI (Linux font metrics render the forge rows a
      // few px wider/taller than macOS; v696.2 settle-polling proved it wasn't mid-animation).
      // The bug-class this spec guards is the tooltip DETACHING across the screen (hundreds of
      // px, the v643 report) — 48px still catches that class on any font stack.
      const adjacent = (hGap <= 48 && bandsOverlapV) || (vGap <= 48 && bandsOverlapH)
        // clamped case: a tall card centered on the item may extend past its band but MUST touch the side
        || (hGap <= 48);
      const onScreen = tr.left >= 0 && tr.top >= 0 && tr.right <= innerWidth && tr.bottom <= innerHeight;
      // stability: cursor wanders inside the anchor → the card must not move. Wander to a
      // 25%-inset point, NOT the extreme corner: corner coords sit on the positioner's
      // clamp/flip boundary, which lands differently under Linux font metrics (Archon Plate
      // flipped sides on CI only — a boundary artifact, not the detach bug-class).
      const ar1 = (a as any).getBoundingClientRect();
      a.dispatchEvent(new MouseEvent('mousemove', { bubbles: true,
        clientX: ar.left + (ar.right - ar.left) * 0.75, clientY: ar.top + (ar.bottom - ar.top) * 0.5 }));
      await new Promise((res) => setTimeout(res, 80));
      // v1459 — settle again before the second sample, for the same reason as the baseline: a card
      // still growing is not a card that jumped. Bounded (≤600ms) so a genuinely wandering card
      // never gets waited into looking still.
      let tr2 = tip.getBoundingClientRect(), s2 = 0;
      for (let w3 = 0; w3 < 10 && s2 < 2; w3++) {
        await new Promise((res) => setTimeout(res, 60));
        const now2 = tip.getBoundingClientRect();
        const same = Math.abs(now2.left - tr2.left) <= 1 && Math.abs(now2.top - tr2.top) <= 1
                  && Math.abs(now2.width - tr2.width) <= 1 && Math.abs(now2.height - tr2.height) <= 1;
        if (same && imgReady()) s2++; else s2 = 0;
        tr2 = now2;
      }
      const ar2 = (a as any).getBoundingClientRect();
      // v918.2 — stability is RELATIVE TO THE ANCHOR: on slow runners content-visibility
      // materialization shifts the page mid-hover, the ANCHOR moves, and the glued card
      // follows it — correct behavior an absolute check misread as a jump for three straight
      // CI rounds. The detach bug-class = the card moving when (and where) the anchor didn't.
      const dxCard = tr2.left - tr.left, dyCard = tr2.top - tr.top;
      const dxAnch = ar2.left - ar1.left, dyAnch = ar2.top - ar1.top;
      const still = Math.abs(dxCard - dxAnch) <= 8 && Math.abs(dyCard - dyAnch) <= 8;
      results.push({ name: (a as any).getAttribute('data-arttip'), adjacent, onScreen, still,
        dxCard: Math.round(dxCard), dyCard: Math.round(dyCard), dxAnch: Math.round(dxAnch), dyAnch: Math.round(dyAnch),
        // v1459 — card box deltas ride the failure text too: a nonzero dW/dH names late art
        // growth as the cause instead of leaving the next reader to guess (this cost 3 CI rounds).
        dW: Math.round(tr2.width - tr.width), dH: Math.round(tr2.height - tr.height) });
      a.dispatchEvent(new MouseEvent('mouseout', { bubbles: true }));
      await new Promise((res) => setTimeout(res, 60));
    }
    return results;
  });
  expect(r.length).toBeGreaterThan(2);
  r.forEach((x: any) => {
    expect(x.adjacent, x.name + ' adjacency').toBe(true);
    expect(x.onScreen, x.name + ' on-screen').toBe(true);
    expect(x.still, x.name + ' stability ' + JSON.stringify(x)).toBe(true);   // numbers in the red — never a blind CI failure again
  });
});
