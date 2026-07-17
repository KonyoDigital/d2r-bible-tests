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
      // v733 recal — v731 semantics: auto-commit fires ONLY on agent-committed vault_names
      // (stash/hold-complete), never on a bare inventory glimpse. The mock now speaks v731.
      reads: [{ ts: Date.now() - 500, n: 1, area: 'Harrogath', scene: 'stash', intent: 'farmed',
                tz: [], ms: 2100, names: ['Ist Rune', 'Perfect Ruby'],
                vault_names: ['Ist Rune', 'Perfect Ruby'] }],
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

  test('v733 OCR honesty gate: garbled OCR text never chips; vocab-matched OCR does — provisional, never vaulted', async ({ page }) => {
    await page.route(BRIDGE + '**', (route) =>
      route.fulfill({ contentType: 'application/json', body: JSON.stringify(state({
        reads: [{ ts: Date.now() - 400, n: 1, area: '', scene: 'loot', lane: 'ocr', mode: 'ocr', ms: 30,
                  names: ['Ist Rune', 'LogginB it &6 evidEnre', 'tvlbinl just llPPEaTad', 'Harlequin Crest'] }],
      })) }));
    await page.goto(URL); await page.waitForTimeout(1500);
    await page.evaluate(() => (window as any).switchTab('tvd')); await page.waitForTimeout(300);
    await page.evaluate(() => (window as any)._tvdToggle());
    await page.waitForTimeout(1200);
    const r = await page.evaluate(() => ({
      chips: [...document.querySelectorAll('#tvb-feed .tvd-chip')].map((c) => c.textContent!.trim()),
      ist: (parseInt((window as any).runeStash['Ist'], 10) || 0),
    }));
    expect(r.chips.find((c) => c.includes('Ist Rune'))).toBeTruthy();          // vocab hit → chip
    expect(r.chips.find((c) => c.includes('Harlequin'))).toBeTruthy();         // vocab hit → chip
    expect(r.chips.find((c) => c.includes('LogginB'))).toBeFalsy();            // garble → DROPPED
    expect(r.chips.find((c) => c.includes('tvlbinl'))).toBeFalsy();            // garble → DROPPED
    expect(r.ist).toBe(0);                                                     // OCR NEVER auto-applies
  });

  test('v734 stash-tab auto-intake: deep runes tab feeds /frame into runeIntake once; OCR never fires', async ({ page }) => {
    // tiny 1x1 jpeg
    const jpeg = Buffer.from(
      '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAn/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAGcP//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAQUCf//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQMBAT8Bf//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQIBAT8Bf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEABj8Cf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAT8hf//Z',
      'base64'
    );
    let intakeCalls = 0;
    let frameHits = 0;
    await page.route('http://127.0.0.1:17771/frame**', async (route) => {
      frameHits++;
      await route.fulfill({ status: 200, contentType: 'image/jpeg', body: jpeg });
    });
    await page.route(BRIDGE + '**', (route) =>
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify(state({
          reads: [{
            ts: Date.now() - 300, n: 1, area: 'Rogue Encampment', scene: 'stash',
            stashTab: 'runes', lane: 'deep', mode: 'warm', ms: 4000,
            names: [], conf: 0.9, vault_names: [], farmed_names: [],
          }],
        })),
      }));
    await page.goto(URL); await page.waitForTimeout(1200);
    await page.evaluate(() => {
      (window as any).__runeIntakeCalls = 0;
      (window as any).runeIntake = async function(){ (window as any).__runeIntakeCalls++; };
      (window as any).gemIntake = async function(){ (window as any).__gemIntakeCalls = ((window as any).__gemIntakeCalls||0)+1; };
    });
    await page.evaluate(() => (window as any).switchTab('tvd')); await page.waitForTimeout(200);
    await page.evaluate(() => (window as any)._tvdToggle());
    await page.waitForTimeout(1500);
    const first = await page.evaluate(() => (window as any).__runeIntakeCalls || 0);
    expect(first).toBe(1);                       // locked runeIntake got the /frame File
    expect(frameHits).toBeGreaterThanOrEqual(1);

    // same visit, second poll with new ts + same tab → debounce (no second intake)
    await page.unroute(BRIDGE + '**');
    await page.route(BRIDGE + '**', (route) =>
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify(state({
          reads: [{
            ts: Date.now() - 50, n: 2, area: 'Rogue Encampment', scene: 'stash',
            stashTab: 'runes', lane: 'deep', mode: 'warm', ms: 3000,
            names: [], conf: 0.9, vault_names: [], farmed_names: [],
          }],
        })),
      }));
    await page.waitForTimeout(800);
    const second = await page.evaluate(() => (window as any).__runeIntakeCalls || 0);
    expect(second).toBe(1);

    // OCR stash claim must NEVER fire intake
    await page.evaluate(() => { (window as any).__runeIntakeCalls = 0; });
    await page.unroute(BRIDGE + '**');
    await page.route(BRIDGE + '**', (route) =>
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify(state({
          reads: [{
            ts: Date.now(), n: 3, area: '', scene: 'stash', stashTab: 'runes',
            lane: 'ocr', mode: 'ocr', provisional: true, ms: 40, names: ['Ist Rune'],
          }],
        })),
      }));
    await page.waitForTimeout(800);
    const ocrCalls = await page.evaluate(() => (window as any).__runeIntakeCalls || 0);
    expect(ocrCalls).toBe(0);
  });

  test('v735 history row carries frame thumb; open lightbox uses /frame?id=', async ({ page }) => {
    const jpeg = Buffer.from(
      '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAn/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAGcP//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAQUCf//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQMBAT8Bf//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQIBAT8Bf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEABj8Cf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAT8hf//Z',
      'base64'
    );
    let frameIdHits = 0;
    await page.route('http://127.0.0.1:17771/frame**', async (route) => {
      const u = route.request().url();
      if (u.includes('id=3_99')) frameIdHits++;
      await route.fulfill({ status: 200, contentType: 'image/jpeg', body: jpeg });
    });
    await page.route(BRIDGE + '**', (route) =>
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify(state({
          reads: [{
            ts: Date.now() - 200, n: 3, area: 'Cold Plains', scene: 'loot', lane: 'deep',
            frameId: '3_99', ms: 5000, names: ['Ist Rune'], conf: 0.9,
          }],
        })),
      }));
    await page.goto(URL); await page.waitForTimeout(1200);
    await page.evaluate(() => (window as any).switchTab('tvd')); await page.waitForTimeout(200);
    await page.evaluate(() => (window as any)._tvdToggle());
    await page.waitForTimeout(1200);
    // history thumb present with correct frame id
    const thumb = await page.evaluate(() => {
      const img = document.querySelector('#tvb-hist img.tvd-frame-thumb') as HTMLImageElement | null;
      return img ? { id: img.getAttribute('data-frame'), src: img.getAttribute('src') || '' } : null;
    });
    expect(thumb).toBeTruthy();
    expect(thumb!.id).toBe('3_99');
    expect(thumb!.src).toContain('id=3_99');
    // open lightbox
    await page.evaluate(() => (window as any)._tvdOpenFrame('3_99', { n: 3, scene: 'loot' }));
    await page.waitForTimeout(300);
    const lb = await page.evaluate(() => {
      const el = document.getElementById('tvd-frame-lb');
      const img = document.getElementById('tvd-frame-lb-img') as HTMLImageElement | null;
      return { open: el && !el.hidden, src: (img && img.src) || '' };
    });
    expect(lb.open).toBe(true);
    expect(lb.src).toContain('id=3_99');
    expect(frameIdHits).toBeGreaterThanOrEqual(1);
  });

  test('v744 RUN STORY strip: chapters + moments from the persisted session; click jumps + pulses the row', async ({ page }) => {
    const T = 1234567890000;
    await page.addInitScript((t: number) => {
      const reads = [
        { ts: t,        n: 1, area: '',                        scene: 'loot',      items: [{ kind: 'rune', key: 'Ist', label: 'Ist Rune', db: true }], names: ['Ist Rune'] },
        { ts: t + 8000, n: 2, area: 'Durance of Hate Level 2', scene: 'gameplay',  items: [] },
        { ts: t + 16000, n: 3, area: '', scene: 'transition', items: [], transition_from: 'Durance of Hate Level 2', note: 'through the portal — leaving Durance of Hate Level 2' },
        { ts: t + 24000, n: 4, area: 'Durance of Hate Level 2', scene: 'inventory', items: [{ kind: 'uni', key: 'Harlequin Crest', label: 'Harlequin Crest', db: true, holding: true, lc: 'holding' }], pending_names: ['Harlequin Crest'] },
        { ts: t + 32000, n: 5, area: '',                        scene: 'stash',     items: [{ kind: 'uni', key: 'Harlequin Crest', label: 'Harlequin Crest', db: true, vault: true, lc: 'vault' }], vault_names: ['Harlequin Crest'] },
      ];
      localStorage.setItem('d2r_tvdHist', JSON.stringify({ live: null, sessions: [{ agentStart: t, startedAt: t, endedAt: t + 40000, reads }] }));
    }, T);
    await page.route(BRIDGE + '**', (route) => route.abort());   // agent off — story reads persisted history
    await page.goto(URL); await page.waitForTimeout(1200);
    await page.evaluate(() => (window as any).switchTab('tvd')); await page.waitForTimeout(300);

    // v745 — the strip never goes dark: LIVE tab is empty (agent off), so the reel narrates
    // the newest ARCHIVED session, capped 📼 RUN STORY · LAST SESSION
    const fallback = await page.evaluate(() => {
      const el = document.getElementById('tvb-story')!;
      return { hidden: el.hidden, cap: el.querySelector('.st-cap')?.textContent || '' };
    });
    expect(fallback.hidden).toBe(false);
    expect(fallback.cap).toContain('RUN STORY');
    expect(fallback.cap).toContain('LAST SESSION');

    await page.click('#tvb-hist-last'); await page.waitForTimeout(600);

    // v745 — the history list is storylined too: 🗺 chapter dividers where the area changes
    const chapters = await page.evaluate(() =>
      [...document.querySelectorAll('#tvb-hist .tvd-chapter')].map((c) => c.textContent!.trim()));
    expect(chapters.length).toBe(1);
    expect(chapters[0]).toContain('Durance of Hate Level 2');

    // v746 — a transition read is honest about WHAT it is (Konyo: 'this photo is ENTERING a
    // PORTAL or ENTERING A NEW GAME') — never a 'nothing readable' shrug
    const transRow = await page.evaluate(() => {
      const rows = [...document.querySelectorAll('#tvb-hist .tvd-read')];
      const r = rows.find((x) => x.textContent!.includes('ENTERING'));
      return r ? { text: r.textContent!.slice(0, 200), shrug: r.textContent!.includes('nothing readable') } : null;
    });
    expect(transRow).toBeTruthy();
    expect(transRow!.text).toContain('through the portal — leaving Durance of Hate Level 2');
    expect(transRow!.shrug).toBe(false);

    const story = await page.evaluate(() => {
      const el = document.getElementById('tvb-story')!;
      return { hidden: el.hidden, nodes: [...el.querySelectorAll('.st-node')].map((n) => n.textContent!.trim()) };
    });
    expect(story.hidden).toBe(false);
    expect(story.nodes.some((n) => n.includes('1 seen'))).toBe(true);              // ⚔️ loot moment
    expect(story.nodes.some((n) => n.includes('Durance of Hate Level 2'))).toBe(true); // 🗺 chapter
    expect(story.nodes.some((n) => n.includes('1 held'))).toBe(true);              // 🎒 hold
    expect(story.nodes.some((n) => n.includes('1 vaulted'))).toBe(true);           // 🏦 commit

    // click the chapter node → the matching history row pulses into view
    await page.evaluate(() => {
      const nd = [...document.querySelectorAll('#tvb-story .st-node')].find((n) => n.textContent!.includes('Durance'))!;
      (nd as HTMLElement).click();
    });
    await page.waitForTimeout(500);
    const pulsed = await page.evaluate(() => {
      const r = document.querySelector('#tvb-hist .tvd-read.tool-jump-pulse');
      return r ? r.textContent!.slice(0, 120) : null;
    });
    expect(pulsed).toBeTruthy();
    expect(pulsed).toContain('Durance of Hate Level 2');
  });

  test('v739 THE VAULT MIRROR: every stashed class lands VISIBLE in the Vault Manager — unique, socketed base (throwout=tag), RotW custom', async ({ page }) => {
    const T = 1234567890;
    await page.route(BRIDGE + '**', (route) =>
      route.fulfill({ contentType: 'application/json', body: JSON.stringify(state({
        startedAt: T - 9000,
        reads: [{ ts: T, n: 1, area: 'Harrogath', scene: 'stash', intent: 'farmed', ms: 5000, mode: 'warm',
                  names: ['Harlequin Crest', 'Colossus Crossbow (5os)', 'Blood Shield', 'Ist Rune'],
                  vault_names: ['Harlequin Crest (Shako)', 'Colossus Crossbow (5os)', 'Blood Shield', 'Ist Rune'] }],
      })) }));
    await page.goto(URL); await page.waitForTimeout(1500);
    await page.evaluate(() => (window as any).switchTab('tvd'));
    await page.evaluate(() => (window as any)._tvdToggle());
    await page.waitForTimeout(2200);
    const r = await page.evaluate(() => {
      (window as any).renderVault && (window as any).renderVault();
      const html = (document.getElementById('mule-vault-card') || {}).innerHTML || '';
      return {
        ist: (parseInt((window as any).runeStash['Ist'], 10) || 0),
        harlequin: html.includes('Harlequin'),
        crossbow: html.includes('Colossus Crossbow'),
        blood: html.includes('Blood Shield'),
      };
    });
    expect(r.ist).toBe(1);            // dedupe: one read, one tally
    expect(r.harlequin).toBe(true);   // known unique
    expect(r.crossbow).toBe(true);    // socketed base — throwout is a TAG, never a disappearance
    expect(r.blood).toBe(true);       // RotW custom — universe guarantee
  });

  test('v747 NOW ON AIR stage: hidden off; live cast tiles + area caption + boss accent; honesty gate; lifecycle rings; transition portal; read # sync', async ({ page }) => {
    // Frozen read timestamps — route.fulfill fires every 250ms; a live Date.now() there would
    // mint an endless stream of "new" reads (the board-spec recurring bug). One read per ts.
    const T = 1_700_000_000_000;
    let body = JSON.stringify(state({
      reads: [{ ts: T, n: 7, area: 'Durance of Hate Level 2', scene: 'loot', intent: 'seen',
                tz: ['Durance of Hate'], ms: 3000,
                names: ['Ist Rune', 'Harlequin Crest', 'Superior Mage Plate'],
                pending_names: ['Harlequin Crest'] }],
    }));
    await page.route(BRIDGE + '**', (route) =>
      route.fulfill({ contentType: 'application/json', body }));
    await page.goto(URL);
    // v754 item 8 sweep — the v747 test flaked under workers=2 because every transition below waited a
    // FLAT 1200/1400ms for the 250ms poll to fetch the new body + re-render. Replace each with a
    // condition wait keyed on the stage read # (.tvn-read-n), which advances on every new read.
    const readIs = (n: number) => page.waitForFunction((num) => {
      const el = document.querySelector('#tvn-stage .tvn-read-n');
      return !!el && (el.textContent || '').trim().endsWith('#' + num);
    }, n, { timeout: 5000 });
    // receiver booted before we drive it
    await page.waitForFunction(() => typeof (window as any)._tvdToggle === 'function' && !!document.getElementById('tvn-stage'), undefined, { timeout: 5000 });
    await page.evaluate(() => (window as any).switchTab('tvd'));

    // (a) OFF → the stage is hidden entirely (the CRT static owns the off story)
    expect(await page.evaluate(() => document.getElementById('tvn-stage')!.hidden)).toBe(true);

    // ON → LIVE
    await page.evaluate(() => (window as any)._tvdToggle());
    await readIs(7);
    const live = await page.evaluate(() => {
      const st = document.getElementById('tvn-stage')!;
      return {
        hidden: st.hidden,
        area: (st.querySelector('.tvn-area') as HTMLElement)?.textContent || '',
        cap: (st.querySelector('.tvn-cap') as HTMLElement)?.textContent || '',
        readN: (st.querySelector('.tvn-read-n') as HTMLElement)?.textContent || '',
        names: [...st.querySelectorAll('.tvn-cast-tile .tvn-cast-name')].map((n) => n.textContent || ''),
        hold: !!st.querySelector('.tvn-cast-tile.tvn-lc-hold'),
        boss: (st.querySelector('.tvn-boss') as HTMLElement)?.textContent || '',
      };
    });
    // (b) visible with area caption + cast art tiles on a live read with named items
    expect(live.hidden).toBe(false);
    expect(live.area).toContain('Durance of Hate Level 2');         // AREA is the big headline
    expect(live.cap).toContain('floor loot');                        // caption narrates scene…
    expect(live.cap).toContain('eyes open');                         // …+ intent (no redundant area repeat)
    // (f) stage read # matches the newest feed entry
    expect(live.readN).toContain('7');
    expect(live.names.find((n) => n.includes('Ist'))).toBeTruthy();
    // v748 (Grok R10 #1) — the cast is CREDITS: the FULL name renders, never a mid-token ellipsis
    expect(live.names.find((n) => n.trim() === 'Harlequin Crest')).toBeTruthy();
    // (c) honesty gate — the note (📋 Superior Mage Plate, db:false) produces NO cast tile
    expect(live.names.find((n) => n.includes('Superior Mage Plate'))).toBeFalsy();
    // (d) lifecycle — pending → holding ring
    expect(live.hold).toBe(true);
    // (P2) boss zone accent — Durance of Hate → Mephisto portrait chip
    expect(live.boss).toContain('Mephisto');

    // (d) vault lifecycle ring — same agent session (startedAt unchanged) so FEED grows
    body = JSON.stringify(state({
      reads: [{ ts: T + 1000, n: 8, area: 'Harrogath', scene: 'stash', intent: 'farmed', ms: 2000,
                names: ['Harlequin Crest'], vault_names: ['Harlequin Crest'] }],
    }));
    await readIs(8);
    const vault = await page.evaluate(() => ({
      ring: !!document.querySelector('#tvn-stage .tvn-cast-tile.tvn-lc-vault'),
      readN: document.querySelector('#tvn-stage .tvn-read-n')?.textContent || '',
    }));
    expect(vault.ring).toBe(true);
    expect(vault.readN).toContain('8');

    // v749 (Grok R10 #2) — CHAPTER CAST MEMORY: an empty gameplay read in the SAME area must NOT
    // wipe the pile story; an area change starts a fresh chapter cast.
    body = JSON.stringify(state({
      reads: [{ ts: T + 1400, n: 9, area: 'Harrogath', scene: 'gameplay', ms: 1500, names: [] }],
    }));
    await readIs(9);
    const memory = await page.evaluate(() =>
      [...document.querySelectorAll('#tvn-stage .tvn-cast-tile .tvn-cast-name')].map((n) => n.textContent!.trim()));
    expect(memory.find((n) => n === 'Harlequin Crest')).toBeTruthy();   // still on stage
    body = JSON.stringify(state({
      reads: [{ ts: T + 1700, n: 10, area: 'Chaos Sanctuary', scene: 'gameplay', ms: 1500, names: [] }],
    }));
    await readIs(10);
    const fresh = await page.evaluate(() =>
      [...document.querySelectorAll('#tvn-stage .tvn-cast-tile:not(.tvn-ghost) .tvn-cast-name')].map((n) => n.textContent!.trim()));
    expect(fresh.length).toBe(0);                                       // new chapter, empty cast

    // (e) transition read → portal wash + honest note (never a "nothing readable" shrug)
    body = JSON.stringify(state({
      reads: [{ ts: T + 2000, n: 11, area: '', scene: 'transition', ms: 20, names: [],
                transition_from: 'Harrogath', note: 'through the portal — leaving Harrogath' }],
    }));
    await readIs(11);
    const trans = await page.evaluate(() => {
      const st = document.getElementById('tvn-stage')!;
      return {
        skin: !!st.querySelector('.tvn-skin-transition'),
        portal: !!st.querySelector('.tvn-portal'),
        text: st.textContent || '',
      };
    });
    expect(trans.skin).toBe(true);
    expect(trans.portal).toBe(true);
    expect(trans.text).toContain('through the portal — leaving Harrogath');
    // v750 (Grok R10 #3) — ONE hourglass on the whole stage (ENTERING flare folded)
    expect((trans.text.match(/⏳/g) || []).length).toBe(1);

    // v750 — the portal doesn't blink the chapter off: leaving a BOSS zone keeps the portrait chip
    body = JSON.stringify(state({
      reads: [{ ts: T + 2400, n: 12, area: '', scene: 'transition', ms: 20, names: [],
                transition_from: 'Durance of Hate Level 2',
                note: 'through the portal — leaving Durance of Hate Level 2' }],
    }));
    await page.waitForTimeout(1400);
    const bossThrough = await page.evaluate(() => ({
      boss: document.querySelector('#tvn-stage .tvn-boss')?.textContent || '',
      hg: (document.getElementById('tvn-stage')!.textContent!.match(/⏳/g) || []).length,
    }));
    expect(bossThrough.boss).toContain('Mephisto');
    expect(bossThrough.hg).toBe(1);

    // toggle OFF → stage hides again (v754 item 8: condition-wait, not a fixed 300ms that races slow CI)
    await page.evaluate(() => (window as any)._tvdToggle());
    await page.waitForFunction(() => document.getElementById('tvn-stage')!.hidden, undefined, { timeout: 5000 });
    expect(await page.evaluate(() => document.getElementById('tvn-stage')!.hidden)).toBe(true);
  });

  test('v754 TV-B7: cast tile ↗ affordance opens the card via openDrop; the tile body never routes', async ({ page }) => {
    const T = 1_700_000_000_000;
    const body = JSON.stringify(state({
      reads: [{ ts: T, n: 5, area: 'The Pit Level 1', scene: 'loot', intent: 'seen', ms: 3000,
                names: ['Ist Rune', 'Harlequin Crest'] }],
    }));
    await page.route(BRIDGE + '**', (route) =>
      route.fulfill({ contentType: 'application/json', body }));
    await page.goto(URL); await page.waitForTimeout(1200);
    await page.evaluate(() => (window as any).switchTab('tvd')); await page.waitForTimeout(300);
    await page.evaluate(() => (window as any)._tvdToggle());
    // condition-wait on the live render (item 8: no fixed wait that races slow CI)
    await page.waitForFunction(() => !!document.querySelector('#tvn-stage .tvn-cast-tile'), undefined, { timeout: 5000 });

    // the cast tile carries an explicit ↗ affordance + a data-open route name (never on notes)
    const aff = await page.evaluate(() => {
      const tile = document.querySelector('#tvn-stage .tvn-cast-tile') as HTMLElement | null;
      return tile ? {
        open: tile.getAttribute('data-open'),
        hasBtn: !!tile.querySelector('.tvn-open'),
        routeExists: typeof (window as any).findRune === 'function' && !!(window as any).findRune(tile.getAttribute('data-open') || ''),
      } : null;
    });
    expect(aff).toBeTruthy();
    expect(aff!.hasBtn).toBe(true);
    expect(aff!.open).toBe('Ist Rune');       // cast tile routes the full rune name (findRune normalizes it)
    expect(aff!.routeExists).toBe(true);      // routing target exists (Grok's ask: verify the card)

    // spy openDrop: a deliberate ↗ click routes; a click on the tile ART is CONTAINED (no route)
    await page.evaluate(() => {
      (window as any).__od = [];
      (window as any).openDrop = function(n: string){ (window as any).__od.push(n); };
    });
    await page.evaluate(() => (document.querySelector('#tvn-stage .tvn-cast-tile .tvn-cast-art, #tvn-stage .tvn-cast-tile .tvn-cast-glyph') as HTMLElement)?.click());
    await page.waitForTimeout(100);
    expect(await page.evaluate(() => (window as any).__od.length)).toBe(0);   // body click never routes
    await page.evaluate(() => (document.querySelector('#tvn-stage .tvn-cast-tile .tvn-open') as HTMLElement).click());
    await page.waitForFunction(() => (window as any).__od.length > 0, undefined, { timeout: 5000 });
    const routed = await page.evaluate(() => (window as any).__od);
    expect(routed).toEqual(['Ist Rune']);     // ONLY the affordance routes
  });

  test('v754 TV-B7: history chip ↗ affordance routes through the scoped #tvb-hist listener only', async ({ page }) => {
    const T = 1_700_000_000_000;
    await page.route(BRIDGE + '**', (route) => route.abort());   // agent off — read from persisted history
    await page.addInitScript((t: number) => {
      const reads = [{ ts: t, n: 1, area: 'The Pit Level 1', scene: 'loot', intent: 'seen', model: 'sonnet', ms: 2000,
        items: [
          { kind: 'rune', key: 'Ist', label: '🪨 Ist Rune', db: true },
          { kind: 'uni', key: 'Harlequin Crest (Shako)', label: '🏆 Harlequin Crest', db: true },
          { kind: 'note', key: 'Superior Mage Plate', label: '📋 Superior Mage Plate', db: false },
        ] }];
      localStorage.setItem('d2r_tvdHist', JSON.stringify({ live: null, sessions: [{ agentStart: t, startedAt: t, endedAt: t + 1000, reads }] }));
    }, T);
    await page.goto(URL); await page.waitForTimeout(1000);
    await page.evaluate(() => { (window as any).switchTab('tvd'); (window as any)._tvdHistTab('last'); });
    await page.waitForFunction(() => !!document.querySelector('#tvb-hist .tvd-open'), undefined, { timeout: 5000 });

    const chips = await page.evaluate(() => {
      const opens = [...document.querySelectorAll('#tvb-hist .tvd-open')].map((o) => o.getAttribute('data-open'));
      // note (db:false) must NOT get an affordance
      const noteChip = [...document.querySelectorAll('#tvb-hist .tvd-chip.tc-note')].some((c) => c.querySelector('.tvd-open'));
      return { opens, noteHasOpen: noteChip };
    });
    expect(chips.opens).toContain('Ist');
    expect(chips.opens).toContain('Harlequin Crest');
    expect(chips.noteHasOpen).toBe(false);

    await page.evaluate(() => { (window as any).__od = []; (window as any).openDrop = function(n: string){ (window as any).__od.push(n); }; });
    // a chip click that is NOT the affordance must not route
    await page.evaluate(() => (document.querySelector('#tvb-hist .tvd-chip') as HTMLElement)?.click());
    await page.waitForTimeout(80);
    expect(await page.evaluate(() => (window as any).__od.length)).toBe(0);
    // the ↗ affordance routes
    await page.evaluate(() => (document.querySelector('#tvb-hist .tvd-open') as HTMLElement).click());
    await page.waitForTimeout(80);
    expect(await page.evaluate(() => (window as any).__od.length)).toBe(1);
  });
});