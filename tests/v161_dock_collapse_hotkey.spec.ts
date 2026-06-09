import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v161 — the bottom MF/P# command dock collapses behind a slim grab handle. Hotkey
// D (or clicking the handle) slides it down and reclaims the reserved bottom space;
// the state persists (d2r_dockCollapsed). R is UNCHANGED (still the routine widget) —
// D is its own registered shortcut, so it auto-appears in the ? help. Additive UI.
test.describe('v161 collapsible bottom dock (hotkey D)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.evaluate(() => localStorage.removeItem('d2r_dockCollapsed'));
    await page.reload();
    await page.waitForTimeout(700);
  });

  test('the dock has a grab handle and starts expanded', async ({ page }) => {
    const r = await page.evaluate(() => {
      const dock = document.getElementById('control-dock')!;
      return {
        hasHandle: !!dock.querySelector('.dock-handle'),
        handleInInner: !!dock.querySelector('.dock-inner > .dock-handle'),
        collapsed: dock.classList.contains('dock-collapsed'),
        toggleFn: typeof (window as any).toggleDock === 'function',
        ariaExpanded: dock.querySelector('.dock-handle')?.getAttribute('aria-expanded'),
      };
    });
    expect(r.hasHandle).toBe(true);
    expect(r.handleInInner).toBe(true);
    expect(r.collapsed).toBe(false);
    expect(r.toggleFn).toBe(true);
    expect(r.ariaExpanded).toBe('true');
  });

  test('pressing D collapses the dock + reclaims bottom space; D again expands', async ({ page }) => {
    const padOpen = await page.evaluate(() => parseInt(getComputedStyle(document.body).paddingBottom));
    await page.keyboard.press('d');
    await page.waitForTimeout(450);
    const collapsed = await page.evaluate(() => {
      const dock = document.getElementById('control-dock')!;
      const inner = dock.querySelector('.dock-inner') as HTMLElement;
      return {
        hasClass: dock.classList.contains('dock-collapsed'),
        translated: getComputedStyle(inner).transform !== 'none',
        pad: parseInt(getComputedStyle(document.body).paddingBottom),
        aria: dock.querySelector('.dock-handle')?.getAttribute('aria-expanded'),
        persisted: localStorage.getItem('d2r_dockCollapsed'),
      };
    });
    expect(collapsed.hasClass).toBe(true);
    expect(collapsed.translated).toBe(true);
    expect(collapsed.pad).toBeLessThan(padOpen);       // reclaimed reserved space
    expect(collapsed.aria).toBe('false');
    expect(collapsed.persisted).toBe('1');

    await page.keyboard.press('d');
    await page.waitForTimeout(450);
    const reopened = await page.evaluate(() => ({
      hasClass: document.getElementById('control-dock')!.classList.contains('dock-collapsed'),
      persisted: localStorage.getItem('d2r_dockCollapsed'),
    }));
    expect(reopened.hasClass).toBe(false);
    expect(reopened.persisted).toBe('0');
  });

  test('clicking the grab handle toggles the dock too', async ({ page }) => {
    await page.locator('#control-dock .dock-handle').click();
    await page.waitForTimeout(400);
    expect(await page.evaluate(() => document.getElementById('control-dock')!.classList.contains('dock-collapsed'))).toBe(true);
  });

  test('the collapsed state persists across reload', async ({ page }) => {
    await page.keyboard.press('d');
    await page.waitForTimeout(300);
    await page.reload();
    await page.waitForTimeout(700);
    expect(await page.evaluate(() => document.getElementById('control-dock')!.classList.contains('dock-collapsed'))).toBe(true);
  });

  test('D does NOT fire while typing in an input, and R stays on the routine widget (not the dock)', async ({ page }) => {
    // typing d in the search box must not collapse the dock
    await page.locator('#gsearch-input').focus();
    await page.keyboard.type('diablo');
    await page.waitForTimeout(150);
    const afterType = await page.evaluate(() => document.getElementById('control-dock')!.classList.contains('dock-collapsed'));
    expect(afterType).toBe(false);

    // R toggles the routine widget, never the dock
    await page.evaluate(() => (document.activeElement as HTMLElement)?.blur());
    await page.keyboard.press('R');
    await page.waitForTimeout(150);
    const afterR = await page.evaluate(() => document.getElementById('control-dock')!.classList.contains('dock-collapsed'));
    expect(afterR).toBe(false);
  });

  test('the D shortcut is documented in the ? keyboard help', async ({ page }) => {
    const inHelp = await page.evaluate(() => {
      (window as any).toggleKbdHelp();
      const modal = document.getElementById('kbd-help-modal');
      const txt = (modal?.textContent || '').toLowerCase();
      return txt.includes('dock');
    });
    expect(inHelp).toBe(true);
  });

  test('no console errors toggling the dock', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.keyboard.press('d');
    await page.waitForTimeout(300);
    await page.keyboard.press('d');
    await page.waitForTimeout(300);
    expect(errors).toEqual([]);
  });
});
