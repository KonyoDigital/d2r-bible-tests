// ASYMMETRIC-ROTATION probe for the TZ panel.
// The render gate measured a 2-vs-2 rotation (his live one) and saw 0.00 everywhere. Grok's
// skeptic claims subgrid was applied to BOTH rows, so a slot with FEWER card-rows gets its cards
// stretched to the taller slot's zone track. This stubs /api/tz with asymmetric rotations and
// measures card heights in each slot. Run from repo root.
import { chromium } from 'playwright';

const PORT = process.env.TV_CONTROL_PORT || 17998;
const WIDTHS = (process.env.WIDTHS || '1440,1100,901').split(',').map(Number);

// zone-count pairs to exercise: [current, next]
const CASES = [
  { name: '2 vs 2 (his live rotation — what the gate saw)', cur: 2, nxt: 2 },
  { name: '2 vs 4 (LIVE short, NEXT tall)',                 cur: 2, nxt: 4 },
  { name: '4 vs 2 (LIVE tall, NEXT short)',                 cur: 4, nxt: 2 },
  { name: '1 vs 3',                                          cur: 1, nxt: 3 },
];

const ZONES = ['Crystalline Passage', 'Frozen River', 'Halls of Vaught', 'Tal Rasha\'s Tombs',
               'Worldstone Keep', 'Throne of Destruction', 'Nihlathak\'s Temple', 'Halls of Pain'];
const mk = (n, off) => ZONES.slice(off, off + n).join(', ');

const browser = await chromium.connectOverCDP('http://127.0.0.1:9225');
const ctx = browser.contexts()[0] || (await browser.newContext());

for (const c of CASES) {
  const page = await ctx.newPage();
  const payload = {
    current: mk(c.cur, 0), next: mk(c.nxt, 4),
    ts: '2026-08-13T19:30:00Z', stale: false,
  };
  await page.route('**/api/tz*', r => r.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify(payload) }));
  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForFunction(() => {
    const b = document.querySelector('.hd-tz .tz-body');
    return b && b.querySelectorAll('.tzz').length >= 2;
  }, null, { timeout: 30000 }).catch(() => {});

  console.log(`\n══════ ${c.name} ══════`);
  for (const w of WIDTHS) {
    await page.setViewportSize({ width: w, height: 1100 });
    await page.waitForTimeout(400);
    const m = await page.evaluate(() => {
      const R = e => { const b = e.getBoundingClientRect(); return { y: +b.y.toFixed(2), h: +b.height.toFixed(2) }; };
      const slot = s => {
        const el = document.querySelector(s); if (!el) return null;
        const lab = el.querySelector('.tz-lab'), zs = el.querySelector('.tz-zones');
        const cards = Array.from(el.querySelectorAll('.tzz')).map(R);
        return { lab: lab && R(lab), zones: zs && R(zs), n: cards.length,
                 cardH: cards.map(c => c.h), firstY: cards[0] && cards[0].y };
      };
      return { now: slot('.tz-slot.now'), next: slot('.tz-slot.next') };
    });
    if (!m.now || !m.next) { console.log(`  ${w}px — MISSING SLOT`); continue; }
    const uniq = a => [...new Set(a.map(x => x.toFixed(2)))];
    const nowH = uniq(m.now.cardH), nextH = uniq(m.next.cardH);
    const dLab = (m.next.lab.h - m.now.lab.h).toFixed(2);
    const dFirst = (m.next.firstY - m.now.firstY).toFixed(2);
    const dCard = (Math.max(...m.next.cardH) - Math.max(...m.now.cardH)).toFixed(2);
    const bad = Math.abs(+dCard) > 1.0;
    console.log(`  ${w}px  labΔ=${dLab}  firstCardΔ=${dFirst}  ` +
      `NOW ${m.now.n} cards h=[${nowH}] zonesH=${m.now.zones.h}  |  ` +
      `NEXT ${m.next.n} cards h=[${nextH}] zonesH=${m.next.zones.h}  cardHΔ=${dCard} ${bad ? '  <<<< CARDS DISAGREE' : ''}`);
  }
  await page.close();
}
await browser.close();
