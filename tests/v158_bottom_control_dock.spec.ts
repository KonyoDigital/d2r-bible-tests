import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v158 — the MF + Players sliders, the eff-unique readout, and the MF quick-set
// presets are relocated (at parse time) out of the top sticky header into a glass
// "command dock" pinned to the BOTTOM of the viewport (Konyo: "i want the MF and
// Players bars on the bottom of the screen by default (sticky) ... and the main tabs
// structure nicely / more professional"). The nav tabs become a centered segmented
// control. ZERO behaviour change: every id (#mf/#players/#eff-mf/#mfNumberInput),
// onclick handler and data-tip is preserved — the controls are MOVED, not rebuilt,
// so all the slider wiring (which is by getElementById) keeps working.
test.describe('v158 bottom control dock + refined tab bar', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(800);
  });

  test('the dock exists, is fixed, and is pinned to the bottom of the viewport', async ({ page }) => {
    const r = await page.evaluate(() => {
      const dock = document.getElementById('control-dock') as HTMLElement;
      const inner = dock?.querySelector('.dock-inner') as HTMLElement;
      const dr = dock.getBoundingClientRect();
      return {
        exists: !!dock,
        position: getComputedStyle(dock).position,
        innerHasGradient: /gradient/.test(getComputedStyle(inner).backgroundImage),
        // bottom edge of the dock sits at (or within a px of) the viewport bottom
        bottomGap: Math.round(window.innerHeight - dr.bottom),
        // body reserves space so the dock never covers the last content
        bodyPadBottom: parseInt(getComputedStyle(document.body).paddingBottom) || 0,
      };
    });
    expect(r.exists).toBe(true);
    expect(r.position).toBe('fixed');
    expect(r.innerHasGradient).toBe(true);          // glass command-bar look
    expect(r.bottomGap).toBeLessThanOrEqual(2);     // pinned to the bottom edge
    expect(r.bodyPadBottom).toBeGreaterThanOrEqual(60);
  });

  test('the MF/P# sliders + eff readout + presets all live INSIDE the dock (moved out of the header)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const dock = document.getElementById('control-dock')!;
      const mf = document.getElementById('mf')!;
      const players = document.getElementById('players')!;
      const eff = document.getElementById('eff-mf')!;
      const numIn = document.getElementById('mfNumberInput')!;
      return {
        mfInDock: dock.contains(mf),
        playersInDock: dock.contains(players),
        effInDock: dock.contains(eff),
        numInInDock: dock.contains(numIn),
        chipsInDock: dock.querySelectorAll('.mf-preset-chip').length,
        // the controls are GONE from the top header
        mfStillInHeader: !!document.querySelector('.header #mf'),
        presetBarGone: !document.querySelector('.mf-preset-bar'),
      };
    });
    expect(r.mfInDock).toBe(true);
    expect(r.playersInDock).toBe(true);
    expect(r.effInDock).toBe(true);
    expect(r.numInInDock).toBe(true);
    expect(r.chipsInDock).toBe(8);                  // 0/100/250/400/553/699/800/1000
    expect(r.mfStillInHeader).toBe(false);
    expect(r.presetBarGone).toBe(true);
  });

  test('the relocated controls still WORK: slider + preset both drive eff-unique (wiring intact)', async ({ page }) => {
    const before = await page.locator('#eff-mf').textContent();
    // drive the slider directly
    await page.locator('#mf').fill('300');
    await page.locator('#mf').dispatchEvent('input');
    await page.waitForTimeout(120);
    const at300 = await page.locator('#eff-mf').textContent();
    // drive a preset chip (onclick=setMFPreset) inside the dock
    await page.locator('#control-dock .mf-preset-chip[data-mf="800"]').click();
    await page.waitForTimeout(120);
    const r = await page.evaluate(() => ({
      mfVal: (document.getElementById('mf') as HTMLInputElement).value,
      eff: document.getElementById('eff-mf')!.textContent,
      activeChip: document.querySelector('.mf-preset-chip[data-active="true"]')?.getAttribute('data-mf'),
    }));
    expect(before).toMatch(/%/);
    expect(at300).not.toBe(before);                 // slider moved the readout
    expect(r.mfVal).toBe('800');                    // preset moved the slider
    expect(r.activeChip).toBe('800');               // preset marked itself active
    expect(r.eff).toMatch(/%/);
  });

  test('the nav tabs are a centered segmented control and stay sticky inside the header', async ({ page }) => {
    const r = await page.evaluate(() => {
      const tabs = document.querySelector('.tabs') as HTMLElement;
      const cs = getComputedStyle(tabs);
      const tabBtns = document.querySelectorAll('.tabs .tab[data-tab]').length;
      // the segmented capsule carries a rounded border
      const radius = parseFloat(cs.borderTopLeftRadius) || 0;
      // tabs are nested in the sticky header (so they scroll-pin like before)
      const header = document.querySelector('.header') as HTMLElement;
      return {
        tabCount: tabBtns,
        radius,
        tabsInStickyHeader: header.contains(tabs) && getComputedStyle(header).position === 'sticky',
      };
    });
    expect(r.tabCount).toBe(11);
    expect(r.radius).toBeGreaterThanOrEqual(8);     // pill capsule, not square
    expect(r.tabsInStickyHeader).toBe(true);
  });

  test('no console errors loading the restyled header + bottom dock', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(URL);
    await page.waitForTimeout(900);
    expect(errors).toEqual([]);
  });
});
