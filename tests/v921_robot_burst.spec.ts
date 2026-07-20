// v921 — ROBOT BURST (Grok: "prove funnel∩photo at robot burst; don't invent a second
// product path"). The v909 net-debt + v912 shot-clock law is cadence-AGNOSTIC: even with
// several vault events landing between the auto SET's snapshot and its photo (robot reads
// every 1.5s), every copy counts exactly once across consecutive shots.
import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v921 robot burst', () => {
  test('3 funnel vaults mid-flight + two consecutive photo SETs → every copy exactly once', async ({ page }) => {
    await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const r = await page.evaluate(async () => {
      const w = window as any;
      localStorage.removeItem('d2r_tvdTallyLog');
      w.LSR.setItem('d2r_tvdKeyDebt', '{}');
      w.adjustRuneStash('Ist', 0 - ((JSON.parse(localStorage.getItem('d2r_runeStash') || '{}')['Ist']) || 0));
      const ist = () => (JSON.parse(localStorage.getItem('d2r_runeStash') || '{}')['Ist']) || 0;
      const debt = () => (JSON.parse(w.LSR.getItem('d2r_tvdKeyDebt') || '{}')['rune:Ist'] || { n: 0 }).n;

      const realIntake = w.runeIntake, realFetch = w.fetch;
      w.fetch = async (u: any) => {
        if (String(u).includes('/frame')) return { ok: true, blob: async () => new Blob([new Uint8Array(64)], { type: 'image/jpeg' }) } as any;
        return { ok: true, json: async () => ({}), text: async () => '' } as any;
      };
      let release: any;
      let photo = 2;   // shot 1: the photographed stash holds 2 Ist
      w.runeIntake = async function () {
        const isAuto = !!w._stashShutterAuto; w._stashShutterAuto = false;
        if (w._stashShutter && !isAuto) return { ok: false, why: 'auto-busy', kind: 'runes' };
        await new Promise((res) => { release = res; });
        w.adjustRuneStash('Ist', photo);   // the locked pipeline ADDs what the photo shows
        return { ok: true, total: photo, added: { Ist: photo }, errors: 0, kind: 'runes' };
      };

      // ── SHOT 1: robot burst lands mid-flight ──
      const p1 = w.tvStashAutoIntake('runes', { frameId: 'burst_1' });
      await new Promise((res) => setTimeout(res, 150));   // parked inside intake (post-snapshot, post-shot-clock)
      for (let i = 0; i < 3; i++) w.tvToolsDelta('Ist Rune', 1, { sid: 's_burst', frameId: 'rb_' + i });
      const midStash = ist(), midDebt = debt();
      release(); await p1;
      const afterShot1 = { stash: ist(), debt: debt() };

      // ── SHOT 2: the next photo sees everything (2 photographed + 3 vaulted-in) ──
      photo = 5;
      const p2 = w.tvStashAutoIntake('runes', { frameId: 'burst_2' });
      await new Promise((res) => setTimeout(res, 150));
      release(); await p2;
      const afterShot2 = { stash: ist(), debt: debt() };

      w.runeIntake = realIntake; w.fetch = realFetch; w._stashShutter = false;
      return { midStash, midDebt, afterShot1, afterShot2 };
    });
    expect(r.midStash).toBe(3);            // the burst really landed mid-flight
    expect(r.midDebt).toBe(3);             // and stamped its post-shot debt
    expect(r.afterShot1.stash).toBe(5);    // photo 2 + 3 real post-shot vaults — nothing eaten
    expect(r.afterShot1.debt).toBe(3);     // post-shot debt SURVIVES (its copies weren't in shot 1)
    expect(r.afterShot2.stash).toBe(5);    // shot 2 supersedes: still 5 — never 8, never 2
    expect(r.afterShot2.debt).toBe(0);     // pre-shot debt retired by the shot-clock law
  });
});
