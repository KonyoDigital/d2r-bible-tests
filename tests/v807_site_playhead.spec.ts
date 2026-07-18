import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v807 (Grok R7 #3) — SITE THEATRE PLAYHEAD parity. The site theatre used to be a setTimeout
// slideshow while the app (tv/control_ui.html) shipped the v798 piecewise wall→theatre axis + rAF
// playhead. This spec locks the port: the thz- theatre now builds a proportional axis (THZ.P),
// runs an rAF playhead (THZ.p advances, THZ.timer stays null — no setTimeout), and shows the dual
// clock (T+mm:ss.mmm · wall). Cheap + deterministic: seed d2r_tvdHist, open, observe. No bridge.

function hist() {
  const t0 = Date.now() - 60000;
  const reads = [
    { ts: t0 + 0,     n: 1, area: 'Chaos Sanctuary', scene: 'gameplay',  frameId: 'f1' },
    { ts: t0 + 3000,  n: 2, area: 'Chaos Sanctuary', scene: 'loot',      frameId: 'f2', names: ['Ber Rune'] },
    { ts: t0 + 6000,  n: 3, area: 'Chaos Sanctuary', scene: 'gameplay',  frameId: 'f3' },
    { ts: t0 + 9000,  n: 4, area: 'River of Flame',  scene: 'gameplay',  frameId: 'f4' },
    { ts: t0 + 40000, n: 5, area: 'River of Flame',  scene: 'stash',     frameId: 'f5', names: ['Harlequin Crest'], vault_names: ['Harlequin Crest'] },
    { ts: t0 + 42000, n: 6, area: 'River of Flame',  scene: 'inventory', frameId: '' },
    { ts: t0 + 45000, n: 7, area: 'River of Flame',  scene: 'loot',      frameId: 'f7', discovered_names: ["Griffon's Eye"] },
  ];
  return { live: { agentStart: t0, startedAt: t0, endedAt: null, reads }, sessions: [] };
}

test.describe('v807 site theatre playhead (thz-)', () => {
  test('opens, builds a proportional axis, runs an rAF playhead + dual clock (no setTimeout slideshow)', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(600);

    // engine is exposed on window (parity hook) — the axis builder exists
    const eng = await page.evaluate(() => ({
      hasEngine: typeof (window as any)._thzEngine === 'object' && !!(window as any)._thzEngine,
      hasBuildAxis: typeof (window as any)._thzEngine?.buildAxis === 'function',
      hasBeatAt: typeof (window as any)._thzEngine?.beatAt === 'function',
      hasTheatre: typeof (window as any)._tvdTheatre?.open === 'function',
    }));
    expect(eng.hasEngine).toBe(true);
    expect(eng.hasBuildAxis).toBe(true);
    expect(eng.hasBeatAt).toBe(true);
    expect(eng.hasTheatre).toBe(true);

    // seed one journaled session where loadHist() actually reads (LSR honors profile keying), open it
    await page.evaluate((h) => {
      (window as any).LSR.setItem('d2r_tvdHist', JSON.stringify(h));
      (window as any).switchTab && (window as any).switchTab('tvd');
      (window as any)._tvdTheatre.open();
    }, hist());
    await page.waitForTimeout(150);

    // overlay is visible + axis built (P has one node per beat boundary)
    const opened = await page.evaluate(() => {
      const ov = document.getElementById('tvz-theatre');
      const st = (window as any)._tvdTheatre.state();
      return {
        hidden: ov ? ov.hidden : true,
        beats: st.beats.length,
        pLen: Array.isArray(st.P) ? st.P.length : -1,
        tplay: st.Tplay,
        p0: st.p,
        timer: st.timer,
      };
    });
    expect(opened.hidden).toBe(false);
    expect(opened.beats).toBeGreaterThan(1);
    expect(opened.pLen).toBe(opened.beats + 1);   // piecewise axis: a boundary after every beat
    expect(opened.tplay).toBeGreaterThan(0);
    expect(opened.timer).toBeNull();               // the setTimeout slideshow is GONE — rAF owns time

    // rAF advances the playhead; the beat index tracks it
    await page.waitForTimeout(700);
    const moved = await page.evaluate(() => {
      const st = (window as any)._tvdTheatre.state();
      return { p: st.p, i: st.i, timer: st.timer, clock: (document.getElementById('tvz-th-clock') || {} as any).textContent || '' };
    });
    expect(moved.p).toBeGreaterThan(opened.p0);    // playhead is running on real ms
    expect(moved.timer).toBeNull();                // still no setTimeout kicked in
    expect(moved.clock).toMatch(/^T\+\d+:\d{2}\.\d{3} · /);   // dual clock: theatre T+ · wall

    // proportional timeline: at least one beat carries an inline flex width (equal dots would lie)
    const widths = await page.evaluate(() => {
      const tl = document.getElementById('tvz-th-timeline');
      return tl ? [].slice.call(tl.children).filter((c: any) => /flex:\s*0\s*0/.test(c.getAttribute('style') || '')).length : 0;
    });
    expect(widths).toBeGreaterThan(0);

    // seeking the playhead: clicking a beat snaps p onto that beat's axis node (rAF won't rebound it)
    const seek = await page.evaluate(() => {
      const st = (window as any)._tvdTheatre.state();
      st.playing = false;                          // freeze so the read is stable
      const tl = document.getElementById('tvz-th-timeline')!;
      (tl.children[3] as HTMLElement).click();
      const s2 = (window as any)._tvdTheatre.state();
      return { i: s2.i, p: s2.p, node: s2.P[3] };
    });
    expect(seek.i).toBe(3);
    expect(seek.p).toBeCloseTo(seek.node, 0);
  });
});
