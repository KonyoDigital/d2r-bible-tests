import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v143 — context-aware #arttip hover + the cross-platform duplicate-name fix.
//   - artOr() renders the art <img> with alt="" (decorative) and moves the
//     accessible name to the .d2art-wrap role=img aria-label. This stops the item
//     name leaking into copied text / broken-image alt as "Name Name".
//   - the #arttip delegation is now context-aware:
//       * hovering the TINY art thumbnail (.d2art-wrap[aria-label]) floats the
//         ENLARGED image only (#arttip.tip-art, no rich stat card).
//       * hovering an item NAME (data-art-logo / data-arttip) floats the rich
//         in-game description card (#arttip.tip-rich) as before.

test.describe('v143 context-aware art hover + dup-name fix', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);
  });

  test('artOr renders decorative alt="" + accessible name on the wrapper aria-label', async ({ page }) => {
    const r = await page.evaluate(() => {
      const html = (window as any).artOr("Andariel's Visage", '💀', 'sm');
      const wrap = document.createElement('div');
      wrap.innerHTML = html;
      const w = wrap.querySelector('.d2art-wrap') as HTMLElement;
      const img = wrap.querySelector('img') as HTMLImageElement | null;
      return {
        wrapAria: w?.getAttribute('aria-label'),
        wrapRole: w?.getAttribute('role'),
        imgAlt: img ? img.getAttribute('alt') : '__noimg__',
        unmappedAria: (() => { const d = document.createElement('div'); d.innerHTML = (window as any).artOr('Totally Not A Real Item XYZ', '❓', 'sm'); return (d.querySelector('.d2art-wrap') as HTMLElement)?.getAttribute('aria-label'); })(),
      };
    });
    expect(r.wrapRole).toBe('img');
    expect(r.wrapAria).toBe("Andariel's Visage");
    expect(r.imgAlt).toBe('');
    expect(r.unmappedAria).toBe('Totally Not A Real Item XYZ');
  });

  test('hovering a tiny art thumbnail floats the ENLARGED image (tip-art, image-only)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const host = document.createElement('div');
      host.innerHTML = (window as any).artOr("Andariel's Visage", '💀', 'sm');
      document.body.appendChild(host);
      const wrap = host.querySelector('.d2art-wrap[aria-label]') as HTMLElement;
      wrap.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 150, clientY: 150 }));
      const tip = document.getElementById('arttip')!;
      const img = tip.querySelector('img') as HTMLImageElement;
      const out = {
        on: tip.classList.contains('on'),
        art: tip.classList.contains('tip-art'),
        rich: tip.classList.contains('tip-rich'),
        hasImg: img.style.display !== 'none' && !!img.src,
        descEmpty: (tip.querySelector('.att-desc') as HTMLElement).innerHTML === '',
        name: (tip.querySelector('.att-name') as HTMLElement).textContent,
      };
      wrap.dispatchEvent(new MouseEvent('mouseout', { bubbles: true }));
      host.remove();
      return out;
    });
    expect(r.on).toBe(true);
    expect(r.art).toBe(true);
    expect(r.rich).toBe(false);
    expect(r.hasImg).toBe(true);
    expect(r.descEmpty).toBe(true);
    expect(r.name).toBe("Andariel's Visage");
  });

  test('hovering an item NAME floats the rich description card (not the enlarged image)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const el = document.createElement('span');
      el.setAttribute('data-art-logo', "Andariel's Visage");
      el.textContent = "Andariel's Visage";
      document.body.appendChild(el);
      el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 200, clientY: 200 }));
      const tip = document.getElementById('arttip')!;
      const out = {
        on: tip.classList.contains('on'),
        rich: tip.classList.contains('tip-rich'),
        art: tip.classList.contains('tip-art'),
        hasDesc: ((tip.querySelector('.att-desc') as HTMLElement).innerHTML || '').length > 0,
      };
      el.dispatchEvent(new MouseEvent('mouseout', { bubbles: true }));
      el.remove();
      return out;
    });
    expect(r.on).toBe(true);
    expect(r.rich).toBe(true);
    expect(r.art).toBe(false);
    expect(r.hasDesc).toBe(true);
  });

  test('switching from a thumbnail to a name clears tip-art (no stuck enlarged mode)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const host = document.createElement('div');
      host.innerHTML = (window as any).artOr("Andariel's Visage", '💀', 'sm');
      document.body.appendChild(host);
      const wrap = host.querySelector('.d2art-wrap[aria-label]') as HTMLElement;
      const name = document.createElement('span');
      name.setAttribute('data-art-logo', "Andariel's Visage"); name.textContent = "Andariel's Visage";
      document.body.appendChild(name);
      const tip = document.getElementById('arttip')!;
      wrap.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 150, clientY: 150 }));
      const afterArt = tip.classList.contains('tip-art');
      name.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 250, clientY: 250 }));
      const afterName = { art: tip.classList.contains('tip-art'), rich: tip.classList.contains('tip-rich') };
      host.remove(); name.remove();
      return { afterArt, afterName };
    });
    expect(r.afterArt).toBe(true);
    expect(r.afterName.art).toBe(false);
    expect(r.afterName.rich).toBe(true);
  });

  test('no console errors across the hover flow', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate(() => {
      const host = document.createElement('div');
      host.innerHTML = (window as any).artOr("Andariel's Visage", '💀', 'sm') + (window as any).artOr('Stone of Jordan', '💍', 'sm');
      document.body.appendChild(host);
      host.querySelectorAll('.d2art-wrap[aria-label]').forEach((w) => {
        w.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 120, clientY: 120 }));
        w.dispatchEvent(new MouseEvent('mouseout', { bubbles: true }));
      });
      host.remove();
    });
    await page.waitForTimeout(120);
    expect(errs).toEqual([]);
  });
});
