import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v76 — quest-item art backlog (G). The 3 Pandemonium keys (Terror/Hate/Destruction)
// and the 3 organs (Diablo's Horn / Baal's Eye / Mephisto's Brain) were clickable but
// rendered the emoji fallback (no D2IO_ART entry). Each now maps to its verified
// diablo2.io graphic: all 3 keys share questkey_graphic.png; the organs use
// horn/eye/brain_graphic.png. Routing is unchanged (openDrop → material card).
test.describe('v76 quest-item art (keys + organs)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  const EXPECT: Record<string, string> = {
    'Key of Terror': 'questkey_graphic.png',
    'Key of Hate': 'questkey_graphic.png',
    'Key of Destruction': 'questkey_graphic.png',
    "Diablo's Horn": 'horn_graphic.png',
    "Baal's Eye": 'eye_graphic.png',
    "Mephisto's Brain": 'brain_graphic.png',
  };

  test('D2IO_ART maps every key + organ to its verified diablo2.io graphic', async ({ page }) => {
    const map = await page.evaluate(() => (window as any).D2IO_ART);
    for (const [name, slug] of Object.entries(EXPECT)) {
      expect(map[name], name).toBeTruthy();
      expect(map[name]).toContain('diablo2.io');
      expect(map[name]).toContain(slug);
    }
  });

  test('opening each quest item renders its art image (no emoji fallback only)', async ({ page }) => {
    for (const [name, slug] of Object.entries(EXPECT)) {
      const src = await page.evaluate((n) => {
        (window as any).openDrop(n);
        const card = document.getElementById('item-detail');
        const img = card?.querySelector('.material-card .d2art-img') as HTMLImageElement | null;
        return img?.getAttribute('src') || '';
      }, name);
      expect(src, name).toContain(slug);
    }
  });

  test('no console errors opening quest-item cards', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    for (const name of Object.keys(EXPECT)) {
      await page.evaluate((n) => (window as any).openDrop(n), name);
      await page.waitForTimeout(100);
    }
    expect(errors).toEqual([]);
  });
});
