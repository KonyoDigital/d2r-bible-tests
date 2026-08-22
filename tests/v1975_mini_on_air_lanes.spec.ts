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

test('OFF is a real refusal, not a decoration', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(async () => {
    const w: any = window;
    w._miniOnAirToggle('runes');                    // unset counts as ON, so this turns it OFF
    const off = await w.tvStashAutoIntake('runes');
    return { on: w._miniOnAirOn('runes'), why: off && off.why, ok: off && off.ok };
  });
  expect(r.on, 'the lane should now read OFF').toBe(false);
  expect(r.ok).toBe(false);
  /* A NAMED reason, so a lane he switched off is distinguishable from one that failed. "Nobody
     looked" and "we looked and found nothing" must never read alike. */
  expect(r.why, 'a skipped lane must say WHY it was skipped').toBe('lane-off');
});

test('quickIntake keeps its name and arms the lane instead of opening a picker', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._miniOnAirToggle('gems');                     // force it OFF first
    const before = w._miniOnAirOn('gems');
    const res = w.quickIntake('gem');
    return { before, after: w._miniOnAirOn('gems'), res, fn: typeof w.quickIntake };
  });
  /* It MUST keep the name: every call site is `window.quickIntake && window.quickIntake(...)`, so a
     deleted function would have failed silently at four buttons at once. */
  expect(r.fn).toBe('function');
  expect(r.before).toBe(false);
  expect(r.after, 'tapping a dark lane arms it').toBe(true);
  expect(r.res.via).toBe('mini-on-air');
});

test('the minis render, and both surfaces agree because they read one store', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._miniOnAirToggle('materials');                // OFF
    w._miniOnAirMount();
    const pills = [...document.querySelectorAll('.mini-onair[data-lane="materials"]')];
    return {
      total: document.querySelectorAll('.mini-onair').length,
      states: pills.map((p) => p.classList.contains('mini-off')),
    };
  });
  expect(r.total, 'lanes must actually render').toBeGreaterThan(0);
  /* If a lane ever renders in two places, they cannot disagree: the DOM is a view of the store, not
     the store. A second pill showing ON while the first shows OFF is how a user learns not to trust
     a switch. */
  expect(r.states.every((x) => x === true), 'every pill for one lane shows the same state').toBe(true);
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
