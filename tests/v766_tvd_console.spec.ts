import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const BRIDGE = 'http://127.0.0.1:17771/state';

// v766 — TV·D restructured to STRUCTURALLY MATCH the TV DIABLO control app (tv/control_ui.html).
// These locks assert the app architecture is present AND that the existing engine surfaces were
// RE-HOMED (not deleted): screen + meters live in the stage; RUN STORY + SYNAPSE live in the rail;
// the SIGNAL FEED archive stays below. Plus the ON/OFF-AIR bug follows bridge truth, and 🎞 THE
// THEATRE replays the board's own d2r_tvdHist sessions.

function state(over: any = {}) {
  return {
    online: true, startedAt: 1, now: Date.now(), readCount: 1,
    beat: { ts: Date.now(), phase: 'watching', motion: 0.08 },
    events: [{ ts: Date.now() - 1000, k: 'boot', t: 'scanner online' }],
    reads: [{ ts: Date.now() - 500, n: 1, area: 'The Pit Level 1', scene: 'loot', ms: 3000, names: ['Ist Rune'] }],
    ...over,
  };
}

test.describe('v766 TV·D console architecture', () => {
  test('app architecture present; engine surfaces re-homed (stage/rail/ticker), IDs intact', async ({ page }) => {
    await page.route(BRIDGE + '**', (route) => route.abort());
    await page.goto(URL); await page.waitForTimeout(400);
    await page.evaluate(() => (window as any).switchTab('tvd')); await page.waitForTimeout(200);

    const shape = await page.evaluate(() => {
      const inside = (sel: string, id: string) => {
        const host = document.querySelector(sel);
        const el = document.getElementById(id);
        return !!(host && el && host.contains(el));
      };
      const sw = document.querySelector('.tvz-head .tvd-switch') as HTMLElement | null;
      const bug = document.getElementById('tvz-bug') as HTMLElement | null;
      return {
        shell: !!document.getElementById('tvz-shell'),
        head: !!document.querySelector('.tvz-head'),
        brand: !!document.querySelector('.tvz-head .tvz-brand-h'),
        // the switch is RETAINED for the engine/specs but visually removed (no toggle look)
        switchRetained: !!(sw && sw.querySelector('.tvd-word')),
        switchHidden: !!(sw && getComputedStyle(sw).display === 'none'),
        // the ON/OFF-AIR bug pill is the visible status
        bugVisible: !!(bug && getComputedStyle(bug).display !== 'none'),
        bug: !!document.getElementById('tvz-bug-txt'),
        theatreBtn: !!document.getElementById('tvz-theatre-btn'),
        // GET THE APP install block
        getapp: !!document.querySelector('.tvz-getapp'),
        // the SESSION-cockpit lamp is ALSO converted: toggle hidden, ON/OFF-AIR pill visible
        scLampRetained: !!(document.getElementById('tvd-switch') && document.querySelector('#tvd-switch .tvd-word')),
        scLampHidden: getComputedStyle(document.getElementById('tvd-switch')!).display === 'none',
        scBugVisible: !!document.getElementById('tvd-sc-bug-txt'),
        // stage clones the app standby homescreen: giant phase word + breathing hero + lower-third meters
        screenInStage: inside('.tvz-stage', 'tvb-screen'),
        phaseWord: !!document.getElementById('tvz-phase'),
        kicker: !!document.getElementById('tvz-kicker'),
        hero: !!document.querySelector('.tvz-stagecrt .tvz-hero'),
        // meters live INSIDE the stage surface (the lower-third), not a sibling block
        metersInStage: !!document.querySelector('.tvz-stagecrt .tvb-meters #tvb-motion'),
        // rail owns RUN STORY + SYNAPSE brain log
        storyInRail: inside('.tvz-rail', 'tvb-story'),
        logInRail: inside('.tvz-rail', 'tvb-log'),
        // ticker + archive stay below
        ticker: !!document.querySelector('.tvz-ticker-h'),
        feed: !!document.getElementById('tvb-feed'),
        histwrap: !!document.getElementById('tvb-histwrap'),
        // every poll-targeted meter id survived the move
        meterIds: ['tvb-motion','tvb-interest','tvb-ap','tvb-reads','tvb-area','tvb-scene','tvb-tz'].every((id) => !!document.getElementById(id)),
      };
    });
    Object.entries(shape).forEach(([k, v]) => expect(v, k).toBe(true));
  });

  test('GET THE APP: Mac + Windows one-liners exact; copy button writes to clipboard + ✓ flash', async ({ page }) => {
    await page.route(BRIDGE + '**', (route) => route.abort());
    await page.goto(URL); await page.waitForTimeout(400);
    await page.evaluate(() => (window as any).switchTab('tvd')); await page.waitForTimeout(150);

    const cmds = await page.evaluate(() => ({
      mac: document.getElementById('tvz-ga-mac')!.textContent!.trim(),
      win: document.getElementById('tvz-ga-win')!.textContent!.trim(),
      copyBtns: document.querySelectorAll('.tvz-ga-copy').length,
    }));
    expect(cmds.mac).toBe('curl -fsSL https://bull-4-u.com/d2r/install-tvd.sh | bash');
    expect(cmds.win).toBe('irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex');
    expect(cmds.copyBtns).toBe(2);

    // stub the clipboard, click Mac copy → captured text + copied state
    const copied = await page.evaluate(async () => {
      (window as any).__clip = '';
      try { Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: (t: string) => { (window as any).__clip = t; return Promise.resolve(); } } }); } catch (e) {}
      const btn = document.querySelector('.tvz-ga-copy[data-copy="tvz-ga-mac"]') as HTMLElement;
      btn.click();
      await new Promise((r) => setTimeout(r, 120));
      return { clip: (window as any).__clip, flashed: btn.classList.contains('copied') };
    });
    expect(copied.clip).toBe('curl -fsSL https://bull-4-u.com/d2r/install-tvd.sh | bash');
    expect(copied.flashed).toBe(true);
  });

  test('ON/OFF-AIR bug + shell state-tint follow the bridge (off → live → offline)', async ({ page }) => {
    let mode: 'ok' | 'dead' = 'ok';
    await page.route(BRIDGE + '**', (route) => {
      if (mode === 'dead') return route.abort();
      route.fulfill({ contentType: 'application/json', body: JSON.stringify(state()) });
    });
    await page.goto(URL); await page.waitForTimeout(400);
    await page.evaluate(() => (window as any).switchTab('tvd')); await page.waitForTimeout(200);

    const off = await page.evaluate(() => ({
      st: document.getElementById('tvz-shell')!.getAttribute('data-tvstate'),
      bug: document.getElementById('tvz-bug-txt')!.textContent,
      phase: document.getElementById('tvz-phase')!.textContent,
    }));
    expect(off.st).toBe('off');
    expect(off.bug).toContain('OFF AIR');
    expect(off.phase).toBe('STANDBY');           // the app's standby homescreen headline

    await page.evaluate(() => (window as any)._tvdToggle());
    await page.waitForTimeout(1200);
    const live = await page.evaluate(() => ({
      st: document.getElementById('tvz-shell')!.getAttribute('data-tvstate'),
      bug: document.getElementById('tvz-bug-txt')!.textContent,
      phase: document.getElementById('tvz-phase')!.textContent,
    }));
    expect(live.st).toBe('live');
    expect(live.bug).toContain('ON AIR');
    expect(live.phase).toMatch(/LIVE|WATCHING|READING|SETTLING|HUNTING|LOADING/);  // giant phase rides the beat

    mode = 'dead';
    await page.waitForTimeout(4500);
    const dead = await page.evaluate(() => document.getElementById('tvz-shell')!.getAttribute('data-tvstate'));
    expect(dead).toBe('offline');
  });

  test('🎞 THE THEATRE replays d2r_tvdHist sessions: film/caption/timeline + pagination; honest empty', async ({ page }) => {
    const T = 1_700_000_000_000;
    await page.route(BRIDGE + '**', (route) => route.abort());   // agent off — theatre reads persisted history
    await page.route('http://127.0.0.1:17771/frame**', (route) => route.abort());  // no bridge frames → fallback/dim path
    await page.goto(URL); await page.waitForTimeout(400);
    await page.evaluate(() => (window as any).switchTab('tvd')); await page.waitForTimeout(150);

    // (a) honest empty state — no journaled sessions yet
    await page.evaluate(() => { try { localStorage.removeItem('d2r_tvdHist'); } catch (e) {} });
    await page.evaluate(() => document.getElementById('tvz-theatre-btn')!.click());
    await page.waitForTimeout(150);
    const empty = await page.evaluate(() => ({
      open: !document.getElementById('tvz-theatre')!.hidden,
      cap: document.getElementById('tvz-th-caption')!.textContent || '',
      beats: document.getElementById('tvz-th-timeline')!.children.length,
    }));
    expect(empty.open).toBe(true);
    expect(empty.cap).toMatch(/no journaled sessions/i);
    expect(empty.beats).toBe(0);
    await page.evaluate(() => document.getElementById('tvz-th-close')!.click());
    expect(await page.evaluate(() => document.getElementById('tvz-theatre')!.hidden)).toBe(true);

    // (b) seed TWO sessions with reads (frameId + named items) → the reel plays them
    await page.evaluate((t) => {
      const mk = (base: number, area: string) => ({
        agentStart: base, startedAt: base, endedAt: base + 20000,
        reads: [
          { ts: base + 1000, n: 1, area, scene: 'loot', frameId: '1_' + base,
            items: [{ kind: 'rune', key: 'Ist', label: '🪨 Ist Rune', db: true }], names: ['Ist Rune'] },
          { ts: base + 9000, n: 2, area, scene: 'stash',
            items: [{ kind: 'uni', key: 'Harlequin Crest (Shako)', label: '🏆 Harlequin Crest', db: true }],
            names: ['Harlequin Crest'] },
        ],
      });
      const payload = { live: null, sessions: [mk(t + 100000, 'Chaos Sanctuary'), mk(t, 'Durance of Hate Level 2')] };
      const s = JSON.stringify(payload);
      try { localStorage.setItem('d2r_tvdHist', s); } catch (e) {}
      try { (window as any).LSR && (window as any).LSR.setItem('d2r_tvdHist', s); } catch (e) {}
    }, T);

    await page.evaluate(() => document.getElementById('tvz-theatre-btn')!.click());
    await page.waitForTimeout(200);
    const play = await page.evaluate(() => ({
      open: !document.getElementById('tvz-theatre')!.hidden,
      beats: document.getElementById('tvz-th-timeline')!.children.length,
      sess: document.getElementById('tvz-th-sess')!.textContent || '',
      cap: document.getElementById('tvz-th-caption')!.innerHTML || '',
      chips: document.querySelectorAll('#tvz-th-caption .tvz-th-chip').length,
    }));
    expect(play.open).toBe(true);
    expect(play.beats).toBe(2);                         // two reads → two timeline beats
    expect(play.sess).toContain('session 1/2');         // newest session first, paginated
    expect(play.cap).toMatch(/Chaos Sanctuary|Ist|read #/i);

    // pagination → older session
    await page.evaluate(() => document.getElementById('tvz-th-prev-s')!.click());
    await page.waitForTimeout(150);
    const older = await page.evaluate(() => document.getElementById('tvz-th-sess')!.textContent || '');
    expect(older).toContain('session 2/2');

    // scrub the timeline to the last beat → the vaulted unique chip renders
    await page.evaluate(() => {
      const beats = document.querySelectorAll('#tvz-th-timeline .tvz-th-beat');
      (beats[beats.length - 1] as HTMLElement).click();
    });
    await page.waitForTimeout(150);
    const scrubbed = await page.evaluate(() => document.getElementById('tvz-th-caption')!.innerHTML || '');
    expect(scrubbed).toMatch(/Harlequin/);

    // Esc closes
    await page.keyboard.press('Escape');
    await page.waitForTimeout(100);
    expect(await page.evaluate(() => document.getElementById('tvz-theatre')!.hidden)).toBe(true);
  });

  // v768 (item 9) — an explicit #tvd hash is USER INTENT and must land on the TV·D tab UNCONDITIONALLY,
  // independent of any stored switch state (v764 made the switches passive lamps, so nothing sets
  // d2r_tvdOn — the old gate stole every deep link and always-landed-home). No-hash default unchanged.
  test('#tvd deep link lands on the TV·D tab with no stored switch state', async ({ page }) => {
    await page.route(BRIDGE + '**', (route) => route.abort());
    // fresh context: d2r_tvdOn is unset — reproduce Konyo's "routes me to the wrong page"
    await page.goto(URL + '#tvd');
    await page.waitForTimeout(700);   // boot reconcile: home @0ms, routeFromHash @250ms
    const active = await page.evaluate(() => {
      const t = document.querySelector('.tab.active') as HTMLElement | null;
      const stored = (() => { try { return localStorage.getItem('d2r_tvdOn'); } catch (e) { return null; } })();
      return { tab: t ? t.getAttribute('data-tab') : null, stored };
    });
    expect(active.stored).not.toBe('1');     // proves the gate isn't what carried us here
    expect(active.tab).toBe('tvd');

    // no-hash default is untouched: lands on the home tab (session), NOT tvd
    await page.goto(URL);
    await page.waitForTimeout(700);
    const home = await page.evaluate(() => {
      const t = document.querySelector('.tab.active') as HTMLElement | null;
      return t ? t.getAttribute('data-tab') : null;
    });
    expect(home).not.toBe('tvd');
  });
});
