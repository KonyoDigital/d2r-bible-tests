import { test, expect } from './_net_stub';
import * as path from 'path';

// REG-2250 — PERFECT SOCKETABLE BASES AUTO-MULE (his 2026-10-13 ruling).
//
// GrokBot #6197028243 confirmed the gap LIVE: filing a 4-socket Archon Plate and an ethereal
// Berserker Axe from the Vault planner were REFUSED with "<name> stays unfiled — a white, superior
// or low base is not given a mule from its name" (bible.html vaultPlannerFile, the q:'b' ELSE arm).
// His rule: a base at MAX or near-max SOCKETS for its type, or an ELITE ETHEREAL base, is a keeper
// that must be MULED, not left unfiled. A plain unsocketed white still stays unfiled.
//
// The signal is read from CB_DB, never memory: window._cbPerfectBaseMule(entry) compares the pick's
// actual sockets to window._cbMaxSock(code, ilvl) (max, or within one), OR flags an elite ethereal
// base, and is gated by window._isRunewordBase so white circlets / orbs / throwables stay out (his
// "only rare circlets" ruling). The planner then REGISTERS the perfect base as the socketed base it
// is (window._ensureSocketBaseEntry, so ownedPool / renderVault keep it — the v324 rule) and routes
// it through the same door every socketed base uses → the SOCKETED base mule.
//
// RED before the fix: the four perfect bases come back filed:false ("stays unfiled") and
// _cbPerfectBaseMule does not exist. GREEN after: each is filed and survives ownedPool; a plain
// 0-socket white still stays unfiled. Runs on GitHub CI only (never his Mac). Repo is PUBLIC — the
// page is loaded by a path relative to __dirname and every base CODE is looked up by name in-page,
// so no /Users path, id or token appears here.

const FILE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

type FileResult = {
  error?: string;
  filed?: boolean;
  ok?: boolean;
  mule?: string | null;
  why?: string;
  helperName?: string | null;
  helperIsFn?: boolean;
  inPool?: boolean;
  isRwBase?: boolean | null;
};

// Build the exact entry the planner's "+ Add an item" host hands vaultPlannerFile for a base pick
// (window._cbEntryFor of the base item), set the pick's sockets / ethereal, then file it and read
// back what stuck. The base CODE is resolved by name from CB_DB so nothing is hardcoded.
async function fileBase(
  page: any,
  name: string,
  opts: { sockets?: number; eth?: boolean }
): Promise<FileResult> {
  return page.evaluate(
    ({ name, opts }: { name: string; opts: { sockets?: number; eth?: boolean } }): FileResult => {
      const w = window as any;
      let code: string | undefined;
      try {
        const d = w._cbDb();
        code = Object.keys(d.b).find((c: string) => d.b[c][0] === name);
      } catch (e) {
        return { error: 'cbDb threw: ' + e };
      }
      if (!code) return { error: 'no base code for ' + name };
      let entry: any;
      try {
        entry = w._cbEntryFor(w._cbItem('b:' + code));
      } catch (e) {
        return { error: 'entryFor threw: ' + e };
      }
      entry.sockets = opts.sockets || 0;
      entry.eth = !!opts.eth;
      const helperIsFn = typeof w._cbPerfectBaseMule === 'function';
      let helperName: string | null = null;
      try {
        const h = helperIsFn ? w._cbPerfectBaseMule(entry) : null;
        helperName = h && h.name ? String(h.name) : null;
      } catch (e) {
        helperName = null;
      }
      let r: any;
      try {
        r = w.vaultPlannerFile(entry, 'vp-spec-' + Math.random().toString(36).slice(2));
      } catch (e) {
        return { error: 'vaultPlannerFile threw: ' + e, helperIsFn, helperName };
      }
      let inPool = false;
      try {
        const pool = w.ownedPool();
        inPool = !!(helperName && pool.indexOf(helperName) >= 0);
      } catch (e) {
        /* ownedPool unavailable — leave inPool false */
      }
      let isRwBase: boolean | null = null;
      try {
        isRwBase = typeof w._isRunewordBase === 'function' ? !!w._isRunewordBase(name) : null;
      } catch (e) {
        isRwBase = null;
      }
      return {
        filed: !!(r && r.filed),
        ok: !!(r && r.ok),
        mule: r ? r.mule : null,
        why: (r && r.why) || '',
        helperIsFn,
        helperName,
        inPool,
        isRwBase,
      };
    },
    { name, opts }
  );
}

// His four live examples: a 4-socket Monarch, a 4os Archon Plate, a 5os War Scepter (all at max
// sockets), and an ethereal Berserker Axe (the elite-ethereal signal, no sockets needed).
const PERFECT: Array<{ name: string; opts: { sockets?: number; eth?: boolean } }> = [
  { name: 'Monarch', opts: { sockets: 4 } },
  { name: 'Archon Plate', opts: { sockets: 4 } },
  { name: 'War Scepter', opts: { sockets: 5 } },
  { name: 'Berserker Axe', opts: { eth: true } },
];

test.describe('v3746 — perfect socketable bases auto-mule (REG-2250)', () => {
  test.beforeEach(async ({ page }: any) => {
    await page.goto(FILE);
    await page.waitForFunction(
      () =>
        typeof (window as any).vaultPlannerFile === 'function' &&
        typeof (window as any)._cbEntryFor === 'function' &&
        typeof (window as any)._cbDb === 'function' &&
        typeof (window as any)._cbItem === 'function' &&
        typeof (window as any).ownedPool === 'function',
      null,
      { timeout: 20000 }
    );
  });

  for (const pb of PERFECT) {
    const title = pb.opts.eth ? `eth ${pb.name}` : `${pb.opts.sockets}os ${pb.name}`;
    test(`a ${title} is filed to a mule, not left unfiled`, async ({ page }: any) => {
      const r = await fileBase(page, pb.name, pb.opts);
      expect(r.error, 'spec setup').toBeUndefined();
      // guard: the base is a real runeword base, or this test is asserting the wrong thing
      expect(r.isRwBase, `${pb.name} must be a runeword base in this build`).toBe(true);
      // the perfect-base router must exist and name the socketed keeper it files under
      expect(r.helperIsFn, 'window._cbPerfectBaseMule must exist (REG-2250)').toBe(true);
      expect(
        r.helperName,
        `_cbPerfectBaseMule must name a socketed keeper for a ${title} (REG-2250)`
      ).toEqual(expect.stringContaining(pb.name));
      // the live gap: this pick used to come back "stays unfiled". His ruling files it.
      expect(
        r.filed,
        `a ${title} is a perfect base — the planner must FILE it, not answer "stays unfiled" ` +
          `(GrokBot #6197028243). why was: ${r.why}`
      ).toBe(true);
      expect(r.mule, `a ${title} must land in a real mule`).toBeTruthy();
      // and it must STICK: registered as a socketed base, so ownedPool / renderVault keep it (v324).
      // Filing to a mule that renderVault then prunes would be a hollow fix.
      expect(
        r.inPool,
        `the filed ${title} ("${r.helperName}") must survive ownedPool — a perfect base kept in a ` +
          `mule that the next render prunes is not kept at all (v324)`
      ).toBe(true);
    });
  }

  test('a plain 0-socket white base still stays unfiled (his ruling, unchanged)', async ({
    page,
  }: any) => {
    // A plain unsocketed white Monarch: socketable, elite, runeword-capable — but with no sockets,
    // not ethereal, it is NOT perfect. His ruling keeps the "stays unfiled" sentence for it.
    const r = await fileBase(page, 'Monarch', { sockets: 0 });
    expect(r.error, 'spec setup').toBeUndefined();
    expect(
      r.filed,
      'a plain 0-socket white base must stay unfiled — his ruling only mules PERFECT bases'
    ).toBe(false);
    expect(r.why, 'the white/superior sentence stands for an actual plain base').toContain(
      'stays unfiled'
    );
  });

  test('_cbPerfectBaseMule: perfect bases name a socketed keeper, a plain white is null', async ({
    page,
  }: any) => {
    const out = await page.evaluate(() => {
      const w = window as any;
      if (typeof w._cbPerfectBaseMule !== 'function') return { missing: true };
      const d = w._cbDb();
      const codeOf = (nm: string) => Object.keys(d.b).find((c: string) => d.b[c][0] === nm);
      const entry = (nm: string, sockets: number, eth: boolean) => {
        const e = w._cbEntryFor(w._cbItem('b:' + codeOf(nm)));
        e.sockets = sockets;
        e.eth = eth;
        return e;
      };
      const nameOf = (e: any) => {
        const h = w._cbPerfectBaseMule(e);
        return h && h.name ? String(h.name) : null;
      };
      return {
        missing: false,
        monarch4: nameOf(entry('Monarch', 4, false)),
        monarch0: nameOf(entry('Monarch', 0, false)), // plain white — not perfect
        monarch1: nameOf(entry('Monarch', 1, false)), // 1 of 4 — not near max
        ethAxe: nameOf(entry('Berserker Axe', 0, true)),
      };
    });
    expect(out.missing, 'window._cbPerfectBaseMule must exist (REG-2250)').toBe(false);
    expect(out.monarch4, 'a 4-of-4-socket Monarch is perfect').toEqual(
      expect.stringContaining('Monarch')
    );
    expect(out.ethAxe, 'an elite ethereal Berserker Axe is perfect').toEqual(
      expect.stringContaining('Berserker Axe')
    );
    expect(out.monarch0, 'a plain 0-socket Monarch is not perfect → null').toBeNull();
    expect(out.monarch1, 'a 1-of-4-socket Monarch is not near max → null').toBeNull();
  });
});
