import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1975 — THE MANUAL AI-INTAKE DOORS ARE GONE; EACH LANE HAS AN ON/OFF MINI.
 *
 * Konyo: "all the AI INTAKE the manual ones… can we finally surgically remove them all and have like
 * a on/off for that specific MINI ON AIR that we already have coded for automated and AI reads…
 * that way it forces me and my cuzin also to just hit reel session instead of anything manual."
 *
 * WHAT WAS REMOVED is only the DOOR: the 📸 button and its hidden <input type="file"> for runes,
 * gems and materials. WHAT SURVIVES UNTOUCHED is every intake FUNCTION, because tvStashAutoIntake
 * dispatches to window[runeIntake|gemIntake|materialIntake] BY NAME and its own comment says it
 * "only supplies a File". Delete those and the automation this change exists to promote would break
 * — silently, since every call site is guarded with `window.x &&`. That is the first assertion here.
 *
 * Each section therefore keeps its OWN reading logic: runes still go through _runeSheetPrep, gems and
 * materials through _tallyPrepImage, and each still posts its own `kind` template.
 */

const LANES = ['runes', 'gems', 'materials', 'vault'];

test('every intake FUNCTION survives — only the manual door was removed', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    return {
      fns: ['runeIntake','gemIntake','materialIntake','vaultIntake','craftIntake','aicUpload']
        .map((f) => [f, typeof w[f]]),
      doors: document.querySelectorAll('#rune-intake-file,#gem-intake-file,#material-intake-file').length,
    };
  });
  for (const [name, t] of r.fns) {
    expect(t, `${name} must still exist — tvStashAutoIntake dispatches to it BY NAME`).toBe('function');
  }
  expect(r.doors, 'the manual file inputs for runes/gems/materials must be gone').toBe(0);
});

test('a lane nobody has touched is ON — doing nothing must yield automatic intake', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const on = await page.evaluate((ls) => ls.map((l: string) => (window as any)._miniOnAirOn(l)), LANES);
  /* The inverse of the v1737 bug, where a toggle defaulted to INCLUDE and only did anything once it
     had been switched off — a control that does nothing until you turn it off is backwards. */
  expect(on.every(Boolean), 'an unset lane must default ON').toBe(true);
});

test('OFF IS UNREACHABLE — a darkened lane in the store is ignored', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  /* ══ v3285 — THIS TEST WAS INVERTED ON PURPOSE ════════════════════════════════════════
     Until v3284 it asserted the opposite: that toggling a lane turned it OFF and that
     tvStashAutoIntake then refused with why:'lane-off'. That was the correct law while OFF
     was reachable. Konyo, 2026-09-18: "these should be toggled on by default no option to
     it". So the law is now that no route reaches OFF — including the one route the UI can
     no longer offer: a stale `false` already sitting in the store from an old click. */
  const r = await page.evaluate(async () => {
    const w: any = window;
    try { w.LSR && w.LSR.setItem && w.LSR.setItem('d2r_autoLanes', JSON.stringify({
      runes: false, gems: false, materials: false, vault: false })); } catch (e) {}
    w._miniOnAirToggle('runes');                    // the old way to darken a lane
    const got = await w.tvStashAutoIntake('runes');
    return {
      on: ['runes', 'gems', 'materials', 'vault'].map((l) => w._miniOnAirOn(l)),
      why: got && got.why,
    };
  });
  expect(r.on.every(Boolean), 'no lane may read OFF, even with false in the store').toBe(true);
  /* It may still refuse for a REAL reason (busy, no reel, lease) — it may never refuse
     because a lane was switched off, because that state no longer exists. */
  expect(r.why, 'lane-off must be unreachable').not.toBe('lane-off');
});

test('quickIntake keeps its name, and the lane it arms was never dark', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    const before = w._miniOnAirOn('gems');
    const res = w.quickIntake('gem');
    return { before, after: w._miniOnAirOn('gems'), res, fn: typeof w.quickIntake };
  });
  /* It MUST keep the name: every call site is `window.quickIntake && window.quickIntake(...)`, so a
     deleted function would have failed silently at four buttons at once. */
  expect(r.fn).toBe('function');
  expect(r.before, 'v3285 — there is no dark lane to arm').toBe(true);
  expect(r.after).toBe(true);
  expect(r.res.via).toBe('mini-on-air');
});

test('the minis render as STATE, carrying no control affordance', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._miniOnAirMount();
    const pills = [...document.querySelectorAll('.mini-onair')];
    return {
      total: pills.length,
      anyOff:    pills.some((p) => p.classList.contains('mini-off')),
      anySwitch: pills.some((p) => p.getAttribute('role') === 'switch'),
      anyClick:  pills.some((p) => p.hasAttribute('onclick')),
      anyTab:    pills.some((p) => p.hasAttribute('tabindex')),
      anyKnob:   document.querySelectorAll('.mini-onair .mini-knob').length,
      words:     [...new Set(pills.map((p) => (p.querySelector('.mini-word') || {} as any).textContent))],
    };
  });
  expect(r.total, 'lanes must actually render').toBeGreaterThan(0);
  expect(r.anyOff, 'no pill may render in the OFF state').toBe(false);
  /* A track-and-knob that cannot move, or a role=switch with no handler, is a lie about what
     the surface offers — it invites a click that does nothing. [[the-unjoined-end]] */
  expect(r.anySwitch, 'no pill may claim role=switch').toBe(false);
  expect(r.anyClick,  'no pill may carry an onclick').toBe(false);
  expect(r.anyTab,    'no pill may be focusable as a control').toBe(false);
  expect(r.anyKnob,   'no pill may draw a knob it cannot move').toBe(0);
  expect(r.words, 'every pill reads AUTO').toEqual(['AUTO']);
});

/* v1976 — VAULT, SETS AND GRAIL LOST THEIR MANUAL DOORS TOO, but not in the same way, and the
   difference is the point.

   VAULT has a real auto lane — _startAutoWatch polls the linked folder every 12s into the same
   window.vaultIntake — so it gets a pill. Its webkitdirectory picker STAYS: that is the automation's
   setup, not a manual read, and deleting it would disarm the very lane being promoted.

   SETS and GRAIL got NO pill, deliberately. Their ticks are "review-first, never silent" — the panel
   says exactly that — and kaiChronicleAcceptAll/AcceptSession are called ZERO times inside this
   file; he accepts from the console. With no auto-apply to arm, a switch would control nothing, and
   a switch that controls nothing is the decoration the lane-off guard exists to prevent. */
test('only the craft door remains, and the vault automation is untouched', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => ({
    doors: [...document.querySelectorAll('input[type=file][id$="-intake-file"]')].map((x) => x.id),
    folder: !!document.getElementById('vault-dir-input'),
    watch: typeof (window as any)._startFolderAutoWatch,
    fns: ['vaultIntake','setIntake','grailIntake','craftIntake'].map((f) => [f, typeof (window as any)[f]]),
  }));
  expect(r.doors, 'craft is the only manual door left — he set it aside deliberately').toEqual(['craft-intake-file']);
  expect(r.folder, 'the folder picker is the auto-watch SETUP, not a manual door — it must survive').toBe(true);
  expect(r.watch, 'the vault folder auto-watch must still exist').toBe('function');
  for (const [n, t] of r.fns) {
    expect(t, `${n} must survive — the automation calls these by name`).toBe('function');
  }
});

test('sets and grail say where reads come from, instead of offering a switch that does nothing', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => ({
    notes: [...document.querySelectorAll('.rs-ai-note')].map((n) => n.textContent || ''),
    lanes: [...document.querySelectorAll('.mini-onair')].map((p) => p.getAttribute('data-lane')),
  }));
  expect(r.notes.length, 'both review-first sections must explain the new source').toBeGreaterThanOrEqual(2);
  expect(r.notes.join(' ')).toMatch(/reel session/i);
  /* The assertion that keeps this honest: no pill may exist for a lane with nothing to arm. */
  expect(r.lanes.includes('grail'), 'grail must NOT get a pill — nothing auto-applies there').toBe(false);
  expect(r.lanes.includes('sets'), 'sets must NOT get a pill — nothing auto-applies there').toBe(false);
});
