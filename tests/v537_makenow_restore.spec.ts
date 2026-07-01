import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v537 — Konyo: after ticking "✓ created" on a MAKE NOW task he wants the restore right there on the Make-now
// view, not only inside the Completed tab. The always-visible restore bar now carries a one-click
// "↩ Undo last: <name>" (un-marks the most-recently created runeword → it drops back into the task list).

test('completing a Make-now task shows "Undo last" ON the Make-now view, and it restores the task', async ({ page }) => {
  await page.addInitScript(() => {
    // Colossus Voulge (4os) + Insight runes (Ral+Tir+Tal+Sol) → a real Make-now forge.
    localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 1, Tir: 1, Tal: 1, Sol: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);

  const before = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Colossus Voulge (4os)');
    w.switchTab('forge'); w.forgeSetFilter('now'); w.renderForge();
    const f = document.getElementById('tab-forge')!;
    return {
      insightNow: [...f.querySelectorAll('.forge-sec-now .f-card.f-now')].some((c) => /Insight/.test(c.textContent || '')),
      undoFn: typeof w.forgeUndoLastDone,
    };
  });
  expect(before.insightNow).toBe(true);          // Insight is a Make-now task
  expect(before.undoFn).toBe('function');

  const afterComplete = await page.evaluate(() => {
    const w: any = window;
    w.rwToggleMade('Insight');            // the "✓ created" button
    w.forgeSetFilter('now'); w.renderForge();   // stay on the Make-now filter
    const f = document.getElementById('tab-forge')!;
    const bar = f.querySelector('.forge-restore-top');
    const undoBtn = bar ? [...bar.querySelectorAll('button')].find((b) => /Undo last/i.test(b.textContent || '')) : null;
    return {
      barVisibleOnNow: !!bar,
      undoText: undoBtn ? undoBtn.textContent!.replace(/\s+/g, ' ').trim() : '',
      insightStillNow: [...f.querySelectorAll('.forge-sec-now .f-card.f-now')].some((c) => /Insight/.test(c.textContent || '')),
    };
  });
  expect(afterComplete.barVisibleOnNow).toBe(true);            // restore bar is ON the Make-now view
  expect(afterComplete.undoText).toMatch(/Undo last:\s*Insight/i);   // one-click undo names the just-created task
  expect(afterComplete.insightStillNow).toBe(false);           // it left Make-now (created)

  const afterUndo = await page.evaluate(() => {
    const w: any = window;
    w.forgeUndoLastDone();                // click "↩ Undo last: Insight"
    w.forgeSetFilter('now'); w.renderForge();
    const f = document.getElementById('tab-forge')!;
    return {
      insightBackNow: [...f.querySelectorAll('.forge-sec-now .f-card.f-now')].some((c) => /Insight/.test(c.textContent || '')),
      made: !!JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')['Insight'],
    };
  });
  expect(afterUndo.insightBackNow).toBe(true);   // restored into Make-now, right from the Make-now view
  expect(afterUndo.made).toBe(false);            // no longer marked created
});

// v537.3 — the Undo bar is SESSION-scoped: it must NOT hover over your genuinely-last-created runeword on load;
// it appears ONLY after you create something in this session (Konyo: "make it only show after I complete something").
test('the Undo-last bar is hidden on load (pre-existing creations) and appears only after a session completion', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 1, Tir: 1, Tal: 1, Sol: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({ 'Enigma': 'Jun 28, 2026 · 20:13' }));  // a past creation
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const onLoad = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Colossus Voulge (4os)');
    w.switchTab('forge'); w.forgeSetFilter('now'); w.renderForge();
    const f = document.getElementById('tab-forge')!;
    return { bar: !!f.querySelector('.forge-restore-top'), madeCount: Object.keys(JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')).length };
  });
  expect(onLoad.madeCount).toBeGreaterThan(1);   // floor + Enigma are created…
  expect(onLoad.bar).toBe(false);                // …but the bar does NOT show for them (nothing done THIS session)

  const afterComplete = await page.evaluate(() => {
    const w: any = window;
    w.rwToggleMade('Insight'); w.forgeSetFilter('now'); w.renderForge();
    const f = document.getElementById('tab-forge')!;
    const bar = f.querySelector('.forge-restore-top');
    const undo = bar ? [...bar.querySelectorAll('button')].find((b) => /Undo last/i.test(b.textContent || '')) : null;
    return { bar: !!bar, undo: undo ? undo.textContent!.replace(/\s+/g, ' ').trim() : '' };
  });
  expect(afterComplete.bar).toBe(true);                        // now it appears
  expect(afterComplete.undo).toMatch(/Undo last:\s*Insight/i); // …naming the thing you just did (not Enigma)
});
