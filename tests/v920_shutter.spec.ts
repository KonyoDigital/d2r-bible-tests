// v920 — THE SHUTTER (Grok REAL EYES R1): "auto owns the shutter; manual 📸 is locked out
// until the SET's finally — busy lock, not queue, not dual skip." A manual upload landing
// while the auto SET is in flight could interleave with the _prev snapshot and be eaten or
// double-land — photo truth means counts NEVER depend on timing.
import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v920 shutter', () => {
  test('T1: manual 📸 is gated while the shutter is held (stash untouched, honest why)', async ({ page }) => {
    await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const r = await page.evaluate(async () => {
      const w = window as any;
      w.adjustRuneStash('Ist', 5 - ((JSON.parse(localStorage.getItem('d2r_runeStash') || '{}')['Ist']) || 0));
      const before = (JSON.parse(localStorage.getItem('d2r_runeStash') || '{}')['Ist']) || 0;
      w._stashShutter = true;   // auto in flight
      const man = await w.runeIntake([new File([new Uint8Array(64)], 's.jpg', { type: 'image/jpeg' })]);
      w._stashShutter = false;
      const after = (JSON.parse(localStorage.getItem('d2r_runeStash') || '{}')['Ist']) || 0;
      return { before, man, after };
    });
    expect(r.man && r.man.ok).toBe(false);
    expect(r.man.why).toBe('auto-busy');               // manual gate — distinct from auto's 'busy'
    expect(r.after).toBe(r.before);                    // nothing mutated
  });

  test('T2: a second auto entry is rejected with its own why while the shutter is held', async ({ page }) => {
    await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const r = await page.evaluate(async () => {
      const w = window as any;
      w._stashShutter = true;
      const second = await w.tvStashAutoIntake('runes', { frameId: 'shutter_t2' });
      w._stashShutter = false;
      return { second };
    });
    expect(r.second && r.second.ok).toBe(false);
    expect(r.second.why).toBe('busy');                 // auto self-guard — harness-distinct from 'auto-busy'
  });

  test('T3: the race frozen mid-flight — auto holds the shutter through its await; SET math lands once', async ({ page }) => {
    await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const r = await page.evaluate(async () => {
      const w = window as any;
      w.adjustRuneStash('Ist', 5 - ((JSON.parse(localStorage.getItem('d2r_runeStash') || '{}')['Ist']) || 0));
      // deferred stub: the auto lane blocks INSIDE its intake call — the real hole's window
      let release: any;
      const gate = new Promise((res) => { release = res; });
      const realIntake = w.runeIntake;
      w.runeIntake = async function () {
        const isAuto = !!w._stashShutterAuto; w._stashShutterAuto = false;   // stub mirrors the wrapper prologue
        if (w._stashShutter && !isAuto) return { ok: false, why: 'auto-busy', kind: 'runes' };
        await gate;
        w.adjustRuneStash('Ist', 3);
        return { ok: true, total: 3, added: { Ist: 3 }, errors: 0, kind: 'runes' };
      };
      // fake capture so the auto lane reaches its intake call without a live agent
      const realFetch = w.fetch;
      w.fetch = async (u: any, o: any) => {
        if (String(u).includes('/frame')) return { ok: true, blob: async () => new Blob([new Uint8Array(64)], { type: 'image/jpeg' }) } as any;
        return { ok: true, json: async () => ({}), text: async () => '' } as any;
      };
      const p = w.tvStashAutoIntake('runes', { frameId: 'shutter_t3' });
      await new Promise((res) => setTimeout(res, 150));   // auto is now parked on the gate
      const heldMidFlight = !!w._stashShutter;
      const man = await w.runeIntake([new File([new Uint8Array(64)], 's.jpg', { type: 'image/jpeg' })]);
      release();
      const auto = await p;
      const final = (JSON.parse(localStorage.getItem('d2r_runeStash') || '{}')['Ist']) || 0;
      w.runeIntake = realIntake; w.fetch = realFetch; w._stashShutter = false;
      return { heldMidFlight, man, auto, final };
    });
    expect(r.heldMidFlight).toBe(true);                // the shutter really spans the await
    expect(r.man && r.man.ok).toBe(false);
    expect(r.man.why).toBe('auto-busy');               // manual never interleaved
    expect(r.final).toBe(3);                           // SET truth exactly once — never 0 / 5 / 8
  });
});
