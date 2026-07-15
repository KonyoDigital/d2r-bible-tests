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
    events: [{ ts: Date.now() - 1000, k: 'boot', t: 'scanner online' }],
    reads: [{ ts: Date.now() - 500, n: 1, area: 'The Pit Level 1', scene: 'loot', tz: ['Spider Forest'],
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
    expect(live.reads).toContain('1 / 120');
    expect(live.area).toBe('The Pit Level 1');
    expect(live.scene).toBe('loot');
    expect(live.tz).toContain('Spider Forest');
    expect(live.log).toContain('scanner online');                // brain log renders agent events

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
});
