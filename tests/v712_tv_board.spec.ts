import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const BRIDGE = 'http://127.0.0.1:17771/state';

// v712 — 📺 TV DIABLO board TDD (Grok night, R2). The receiver is driven through a MOCK bridge
// (page.route fulfills /state) — deterministic states, zero agent, zero vision cost. Locks:
//  · dual-render: ONE engine drives the session-card switch AND the flagship board
//  · CRT state machine: off → conn → live → offline, verbs + classes synced to bridge truth
//  · routing: all 5 kinds (🪨 rune · 💎 gem · 🏆 unique · 🧩 set · 📋 note) + review-first applies
//  · brain log renders agent events; meters ride the beat.

function state(over: any = {}) {
  return {
    online: true, startedAt: 1, now: Date.now(), readCount: 1,
    beat: { ts: Date.now(), phase: 'watching', motion: 0.08 },
    events: [{ ts: Date.now() - 1000, k: 'boot', t: 'scanner online' },
             { ts: Date.now() - 800, k: 'cap', t: 'vision timed out (90s) — fallback armed' }],
    reads: [{ ts: Date.now() - 500, n: 1, area: 'The Pit Level 1', scene: 'loot', tz: ['Spider Forest'], ms: 4200,
              names: ['Ist Rune', 'Perfect Ruby', 'Harlequin Crest', "Sigon's Guard", 'Superior Mage Plate'] }],
    ...over,
  };
}

test.describe('v712 TV DIABLO board (mock bridge)', () => {
  test('CRT + dual switches sync: off → live → offline; meters + brain log paint', async ({ page }) => {
    let mode: 'ok' | 'dead' = 'ok';
    await page.route(BRIDGE + '**', (route) => {
      if (mode === 'dead') return route.abort();
      route.fulfill({ contentType: 'application/json', body: JSON.stringify(state()) });
    });
    await page.goto(URL); await page.waitForTimeout(1500);
    // v715 weld: give the page a live-rotation stub so TZ SEEN can cross-check
    await page.evaluate(() => { (window as any)._tzPeek = () => ({ current: { zone: 'Spider Forest' } }); });
    await page.evaluate(() => (window as any).switchTab('tvd')); await page.waitForTimeout(400);

    // OFF: dead channel
    const off = await page.evaluate(() => ({
      scr: document.getElementById('tvb-screen')!.className,
      verb: document.getElementById('tvb-verb')!.textContent,
    }));
    expect(off.scr).toContain('tvb-off');
    expect(off.verb).toContain('DISCONNECTED');

    // ON → LIVE (mock answers)
    await page.evaluate(() => (window as any)._tvdToggle());
    await page.waitForTimeout(1200);
    const live = await page.evaluate(() => ({
      scr: document.getElementById('tvb-screen')!.className,
      words: [...document.querySelectorAll('.tvd-word')].map((w) => w.textContent),
      motion: (document.getElementById('tvb-motion') as HTMLElement).style.width,
      reads: document.getElementById('tvb-reads')!.textContent,
      area: document.getElementById('tvb-area')!.textContent,
      scene: document.getElementById('tvb-scene')!.textContent,
      tz: document.getElementById('tvb-tz')!.textContent,
      log: document.getElementById('tvb-log')!.textContent,
    }));
    expect(live.scr).toContain('tvb-live');
    live.words.forEach((w) => expect(w).toContain('LIVE'));      // BOTH switches (card + board)
    expect(parseInt(live.motion)).toBeGreaterThan(0);
    expect(live.reads).toMatch(/1 \/ (120|240)/);               // v722+ cap is 240; mock without cap → 240
    expect(live.reads).toContain('4.2s avg');                    // v713 latency meter (Grok P1-4)
    expect(live.area).toBe('The Pit Level 1');
    expect(live.scene).toBe('loot');
    expect(live.tz).toContain('Spider Forest');
    expect(live.tz).toContain('✓ tracker agrees');               // v715 — screen×tracker weld (two independent sources)
    expect(live.log).toContain('scanner online');                // brain log renders agent events
    expect(live.log).toContain('vision timed out');              // failures are NEVER silent on the board (Grok P1-5)

    // bridge dies → offline theatre within ~2 polls
    mode = 'dead';
    await page.waitForTimeout(4500);
    const dead = await page.evaluate(() => ({
      scr: document.getElementById('tvb-screen')!.className,
      verb: document.getElementById('tvb-verb')!.textContent,
    }));
    expect(dead.scr).toContain('tvb-offline');
    expect(dead.verb).toContain('NO SIGNAL');
  });

  test('routing: all 5 kinds chip correctly; applies are review-first and mutate the real engines', async ({ page }) => {
    await page.route(BRIDGE + '**', (route) =>
      route.fulfill({ contentType: 'application/json', body: JSON.stringify(state()) }));
    await page.goto(URL); await page.waitForTimeout(1500);
    await page.evaluate(() => (window as any).switchTab('tvd')); await page.waitForTimeout(300);
    await page.evaluate(() => (window as any)._tvdToggle());
    await page.waitForTimeout(1200);

    const chips = await page.evaluate(() =>
      [...document.querySelectorAll('#tvb-feed .tvd-chip')].map((c) => c.textContent!.trim()));
    expect(chips.find((c) => c.includes('🪨 Ist Rune'))).toBeTruthy();
    expect(chips.find((c) => c.includes('💎 Perfect Ruby'))).toBeTruthy();
    expect(chips.find((c) => c.includes('🏆 Harlequin Crest'))).toBeTruthy();
    expect(chips.find((c) => c.includes("🧩 Sigon's Guard"))).toBeTruthy();
    expect(chips.find((c) => c.includes('📋 Superior Mage Plate'))).toBeTruthy();   // honest note, no apply

    // nothing applied silently
    const before = await page.evaluate(() => ({
      ist: (parseInt((window as any).runeStash['Ist'], 10) || 0),
      ruby: (parseInt((window as any).gemStash['Perfect Ruby'], 10) || 0),
    }));
    expect(before.ist).toBe(0);
    expect(before.ruby).toBe(0);

    // apply-all on the read → rune + gem + unique + set tick through the REAL engines
    await page.evaluate(() => (document.querySelector('#tvb-feed .tvd-applyall') as HTMLElement).click());
    await page.waitForTimeout(600);
    const after = await page.evaluate(() => ({
      ist: (parseInt((window as any).runeStash['Ist'], 10) || 0),
      ruby: (parseInt((window as any).gemStash['Perfect Ruby'], 10) || 0),
      harle: typeof (window as any)._gFound === 'function' ? (window as any)._gFound('Harlequin Crest (Shako)') : null,
    }));
    expect(after.ist).toBe(1);
    expect(after.ruby).toBe(1);
    expect(after.harle).toBe(true);
  });

  test('v728 history scroll is not yanked to top on poll re-render', async ({ page }) => {
    // Fixed agent state so poll fingerprints stay stable; pre-seed tall history in LS.
    const base = 1_700_000_000_000;
    const histReads = Array.from({ length: 24 }, (_, i) => ({
      ts: base + i * 1000, n: i + 1, area: 'The Pit Level 1', scene: 'loot', intent: 'seen',
      model: 'sonnet', ms: 2000, conf: 0.9, auto: false,
      items: [
        { kind: 'rune', key: 'Ist', label: '🪨 Ist Rune', done: false, db: true, vault: false },
        { kind: 'uni', key: 'Harlequin Crest (Shako)', label: '🏆 Harlequin Crest', done: false, db: true, vault: false },
      ],
    }));
    await page.route(BRIDGE + '**', (route) => {
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify(state({
          startedAt: 9001, readCount: 1,
          reads: [{ ts: base + 999000, n: 1, area: 'The Pit Level 1', scene: 'gameplay', intent: 'context',
                    model: 'sonnet', ms: 1000, names: [] }],
        })),
      });
    });
    await page.goto(URL); await page.waitForTimeout(1000);
    await page.evaluate((reads) => {
      const payload = JSON.stringify({
        live: null,
        sessions: [{ agentStart: 9001, startedAt: reads[0].ts, endedAt: reads[reads.length - 1].ts, reads }],
      });
      try { localStorage.setItem('d2r_tvdHist', payload); } catch (e) {}
      try { (window as any).LSR && (window as any).LSR.setItem('d2r_tvdHist', payload); } catch (e) {}
      (window as any).switchTab('tvd');
      (window as any)._tvdHistTab('last');
    }, histReads);
    await page.waitForTimeout(500);
    await page.evaluate(() => (window as any)._tvdToggle());
    await page.waitForTimeout(1200);
    const before = await page.evaluate(() => {
      const el = document.getElementById('tvb-hist')!;
      // force overflow if content is short in headless (still exercises scroll preserve path)
      const pad = document.createElement('div');
      pad.id = 'tvb-hist-pad';
      pad.style.height = '900px';
      el.appendChild(pad);
      el.scrollTop = 260;
      return { top: el.scrollTop, h: el.scrollHeight, ch: el.clientHeight, kids: el.children.length };
    });
    expect(before.h).toBeGreaterThan(before.ch);
    expect(before.top).toBeGreaterThan(50);
    // poll keeps ticking — LAST SESSION fingerprint unchanged → body not rebuilt → pad stays + scroll holds
    await page.waitForTimeout(4500);
    const after = await page.evaluate(() => {
      const el = document.getElementById('tvb-hist')!;
      return { top: el.scrollTop, hasPad: !!document.getElementById('tvb-hist-pad') };
    });
    expect(after.hasPad).toBe(true); // full innerHTML wipe would destroy the pad
    expect(after.top).toBeGreaterThan(50);
  });

  test('v724 session history panel shows timed DB-matched items and survives mock reads', async ({ page }) => {
    await page.route(BRIDGE + '**', (route) =>
      route.fulfill({ contentType: 'application/json', body: JSON.stringify(state({
        startedAt: 9001,
        reads: [{ ts: Date.now() - 200, n: 1, area: 'The Pit Level 1', scene: 'loot', intent: 'seen',
                  model: 'haiku', ms: 3200, names: ['Ist Rune', 'Harlequin Crest'] }],
      })) }));
    await page.goto(URL); await page.waitForTimeout(1200);
    await page.evaluate(() => {
      try { localStorage.removeItem('d2r_tvdHist'); } catch (e) {}
      (window as any).switchTab('tvd');
    });
    await page.waitForTimeout(300);
    await page.evaluate(() => (window as any)._tvdToggle());
    await page.waitForTimeout(1400);
    const hist = await page.evaluate(() => {
      const meta = document.getElementById('tvb-hist-meta')!.textContent || '';
      const body = document.getElementById('tvb-hist')!.textContent || '';
      const wrap = !!document.getElementById('tvb-histwrap');
      const stored = localStorage.getItem('d2r_tvdHist') || '';
      return { meta, body, wrap, storedLen: stored.length };
    });
    expect(hist.wrap).toBe(true);
    expect(hist.meta).toMatch(/LIVE|read/i);
    expect(hist.body).toMatch(/Ist|Harlequin|SEEN/i);
    expect(hist.storedLen).toBeGreaterThan(20);
    // LAST SESSION tab is present and switchable
    await page.evaluate(() => (window as any)._tvdHistTab('last'));
    await page.waitForTimeout(200);
    const lastMeta = await page.evaluate(() => document.getElementById('tvb-hist-meta')!.textContent || '');
    expect(lastMeta.length).toBeGreaterThan(5);
  });

  test('v723 farmed inv/stash auto-applies; floor loot stays review-first', async ({ page }) => {
    const farmed = state({
      reads: [{ ts: Date.now() - 500, n: 1, area: 'Harrogath', scene: 'stash', intent: 'farmed',
                tz: [], ms: 2100, names: ['Ist Rune', 'Perfect Ruby'] }],
    });
    await page.route(BRIDGE + '**', (route) =>
      route.fulfill({ contentType: 'application/json', body: JSON.stringify(farmed) }));
    await page.goto(URL); await page.waitForTimeout(1200);
    await page.evaluate(() => (window as any).switchTab('tvd')); await page.waitForTimeout(300);
    await page.evaluate(() => (window as any)._tvdToggle());
    await page.waitForTimeout(1200);
    const farm = await page.evaluate(() => ({
      ist: (parseInt((window as any).runeStash['Ist'], 10) || 0),
      ruby: (parseInt((window as any).gemStash['Perfect Ruby'], 10) || 0),
      feed: document.getElementById('tvb-feed')!.textContent || '',
    }));
    expect(farm.ist).toBe(1);            // auto engine tick
    expect(farm.ruby).toBe(1);
    expect(farm.feed).toContain('FARMED');

    // floor SEEN must NOT auto-apply (reset stash first)
    await page.evaluate(() => {
      (window as any).runeStash['Ist'] = 0;
      (window as any).gemStash['Perfect Ruby'] = 0;
    });
    const floor = state({
      reads: [{ ts: Date.now(), n: 2, area: 'The Pit Level 1', scene: 'loot', intent: 'seen',
                tz: [], ms: 1800, names: ['Ist Rune'] }],
    });
    await page.unroute(BRIDGE + '**');
    await page.route(BRIDGE + '**', (route) =>
      route.fulfill({ contentType: 'application/json', body: JSON.stringify(floor) }));
    await page.waitForTimeout(2500);
    const seen = await page.evaluate(() => ({
      ist: (parseInt((window as any).runeStash['Ist'], 10) || 0),
      feed: document.getElementById('tvb-feed')!.textContent || '',
    }));
    expect(seen.ist).toBe(0);            // review-first on floor
    expect(seen.feed).toMatch(/SEEN|loot/i);
  });
});
