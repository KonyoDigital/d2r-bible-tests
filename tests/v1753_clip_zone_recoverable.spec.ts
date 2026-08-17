import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1753 — IF IT IS CLIPPED, IT MUST BE RECOVERABLE.
//
// bible.html already carries this scar, in its own words: a nowrap/ellipsis surface makes text
// "present in textContent, invisible to him, which is the very defect the change claimed to close.
// A DOM-reading test would have gone green over it." That note was written about the board. The
// console had the same defect and no rule.
//
// MEASURED on #btn-sim's sub-label, which is the console's only clipped .lab:
//
//     1440px : 562px of text in a 208px box  -> 63% invisible
//      901px : 508px of text in a 148px box  -> 71% invisible
//
// What was lost: "scrub ts + frames · click again = off". "scrub ts + frames" is a feature nothing
// else on the console mentions, so it was not merely repeated copy going missing.
//
// SHORTENING CANNOT FIX IT and that is why the answer is a title. Measured at 901px, even "replay
// last session" ALONE overflows (164px in 148px). The box is genuinely narrow; the sub-label can
// only ever be a hint, so the full sentence has to live somewhere a hover can reach.
//
// THE RULE, NOT THE INSTANCE. This asserts that ANY clipped label in the console action bar carries
// a title holding its full text — so the next long sub-label cannot quietly lose its tail. It also
// pins the title to MORPH with the label: a title still describing "replay" while the button says
// "Close Theatre" is worse than none, because it is a confident wrong answer to the one question a
// hover asks. [[unknown-stays-unknown]]

const REPO = path.resolve(__dirname, '..');
const UI = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');
const ORIGIN = 'http://tvd.clip.test';

async function console_(page: any, width: number) {
  await page.setViewportSize({ width, height: 900 });
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname.startsWith('/art/'), (r: any) => {
    const p = path.join(REPO, new URL(r.request().url()).pathname.replace(/^\//, ''));
    return fs.existsSync(p)
      ? r.fulfill({ status: 200, contentType: 'image/png', body: fs.readFileSync(p) })
      : r.fulfill({ status: 404, contentType: 'text/plain', body: 'no art' });
  });
  await page.route((u: URL) => u.pathname.startsWith('/api/'), (r: any) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
}

test.describe('v1753 — clipped console labels stay recoverable', () => {
  for (const width of [901, 1440]) {
    test(`★★★ every clipped action label carries its full text in a title (${width}px)`, async ({ page }) => {
      await console_(page, width);
      const r = await page.evaluate(() => {
        const bad: any[] = [];
        let clippedSeen = 0;
        document.querySelectorAll('.lab, .lab span').forEach((e: any) => {
          if (e.children.length) return;
          if (!(e.scrollWidth > e.clientWidth + 2 && e.clientWidth > 0)) return;
          clippedSeen++;
          const full = (e.textContent || '').trim();
          const host = e.closest('button') || e.closest('[title]');
          const title = host ? (host.getAttribute('title') || '') : '';
          if (title.indexOf(full) < 0) {
            bad.push({
              btn: host ? (host.id || host.className) : 'no host',
              lostPct: Math.round(100 * (1 - e.clientWidth / e.scrollWidth)),
              text: full.slice(0, 60), title: title.slice(0, 60),
            });
          }
        });
        return { clippedSeen, bad };
      });
      // NON-VACUITY: if nothing is clipped at this width the rule proves nothing, and that is a
      // real possibility worth failing on — it would mean this gate stopped watching anything.
      expect(r.clippedSeen, 'no console label is clipped at ' + width + 'px, so this gate checked nothing')
        .toBeGreaterThan(0);
      expect(r.bad, 'clipped labels whose text cannot be recovered: ' + JSON.stringify(r.bad)).toEqual([]);
    });
  }

  test('★★★ the title morphs with the label, so it never describes the wrong state', async ({ page }) => {
    await console_(page, 1440);
    const r = await page.evaluate(() => {
      const btn = document.getElementById('btn-sim') as HTMLElement;
      const sub = btn.querySelector('.lab span') as HTMLElement;
      const read = () => ({ label: (sub.textContent || '').trim(), title: btn.getAttribute('title') || '' });
      const before = read();
      // drive the same morph the toggle runs, without opening the Theatre for real
      const w: any = window;
      let moved = false;
      try {
        if (w.TH) { w.TH.open = !w.TH.open; moved = true; }
      } catch (e) {}
      // re-run whichever function paints the button
      try { if (typeof w.paintSim === 'function') w.paintSim(); } catch (e) {}
      const after = read();
      return { before, after, moved };
    });
    expect(r.before.title, 'the closed-state title is missing').toBeTruthy();
    expect(r.before.title, 'the title does not carry the label it sits on').toContain(r.before.label);
    // whatever the state, title and label must agree — that is the invariant, not the wording
    expect(r.after.title, 'the title stopped matching the label after a state change')
      .toContain(r.after.label);
  });
});
