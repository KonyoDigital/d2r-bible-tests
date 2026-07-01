import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v528 — the Tools tab gets the same delightful floating legend as the Forge: a compass FAB (shown only on
// the Tools tab via body:has(#tab-tools.active)) that pops a clickable map of every section. Guard: it's
// built, the toggle/jump fns exist, and EVERY map row jumps to a real, existing Tools card.

test('Tools legend map: FAB + clickable map built, every jump target is a real card', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const targets = Array.from(document.querySelectorAll('#tools-legend-pop [onclick*="toolsLegendJump"]'))
      .map((e: any) => { const m = e.getAttribute('onclick').match(/toolsLegendJump\('([^']+)'\)/); return m ? m[1] : null; })
      .filter(Boolean);
    const deadTargets = targets.filter((id: string) => !document.getElementById(id));
    // exercise the jump: it should expand a collapsed card
    let jumpWorks = false;
    try {
      const card = document.getElementById('rw-chronicle-card');
      const wasCollapsed = card!.classList.contains('collapsed');
      w.toolsLegendJump('rw-chronicle-card');
      jumpWorks = wasCollapsed ? !card!.classList.contains('collapsed') : true;
    } catch (e) {}
    return {
      fab: !!document.getElementById('tools-legend-fab'),
      pop: !!document.getElementById('tools-legend-pop'),
      toggleFn: typeof w.toolsLegendToggle,
      jumpFn: typeof w.toolsLegendJump,
      itemCount: targets.length,
      deadTargets,
      jumpWorks,
    };
  });
  expect(r.fab).toBe(true);
  expect(r.pop).toBe(true);
  expect(r.toggleFn).toBe('function');
  expect(r.jumpFn).toBe('function');
  expect(r.itemCount).toBeGreaterThan(12);   // full map of sections
  expect(r.deadTargets).toEqual([]);          // every row points at a real card
  expect(r.jumpWorks).toBe(true);             // jumping opens the target card
});
