import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v622 — ART FIDELITY (Konyo's Spired Helm wearing the barbarian Fanged Helm's face). Game-file
// truth (armor.txt via CASC): Spired Helm invfile = invghm = the Great Helm sprite. Locks:
// (a) a keyword slot-fallback seeded onto a suffixed label never beats the clean name's HD art;
// (b) registered '(Larzuk base)' chips render the true sprite; (c) runeword chips on a base's card
// wear THAT base's sprite (context), not their generic iconic base.

test('Spired Helm (Larzuk base): chip + tip resolve the true in-game sprite, not fangedhelm', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Spired Helm (Larzuk base)', true);
    localStorage.setItem('d2r_owned', JSON.stringify(['Spired Helm (Larzuk base)']));
  });
  await page.reload(); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    w.switchTab('tools');
    const card = document.getElementById('mule-vault-card');
    if (card && card.classList.contains('collapsed') && w.toggleCardCollapse) w.toggleCardCollapse('mule-vault-card');
    w.renderVault();
    const chip = document.querySelector('.vault-chip[data-vault-item="Spired Helm (Larzuk base)"] img') as HTMLImageElement;
    localStorage.removeItem('d2r_owned');
    return { chipSrc: chip ? chip.getAttribute('src') : null, tipArt: w.artUrl('Spired Helm (Larzuk base)') };
  });
  expect(r.chipSrc).toBe('art/hd_great_helm.png');
  expect(r.tipArt).toBe('art/hd_great_helm.png');
});

test('tier law: hd_ beats _graphic beats base_ across label resolution', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    w.D2IO_ART['__t (Larzuk base)'] = 'art/fangedhelm_graphic.png';
    w.D2IO_ART['__t'] = 'art/hd_great_helm.png';
    const a = w.artUrl('__t (Larzuk base)');
    w.D2IO_ART['__u (Larzuk base)'] = 'art/hd_something.png';
    w.D2IO_ART['__u'] = 'art/other_graphic.png';
    const b = w.artUrl('__u (Larzuk base)');
    delete w.D2IO_ART['__t (Larzuk base)']; delete w.D2IO_ART['__t']; delete w.D2IO_ART['__u (Larzuk base)']; delete w.D2IO_ART['__u'];
    return { a, b };
  });
  expect(r.a).toBe('art/hd_great_helm.png');     // clean HD beats seeded keyword art
  expect(r.b).toBe('art/hd_something.png');      // a real direct HD is never downgraded
});

test('runeword chips on a base card wear the HOST base sprite (Strength on a Scissors Katar = claw art)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    localStorage.setItem('d2r_rwProfile', 'fresh');
    const line = String(w._baseRWLine('Scissors Katar', 2) || '');
    localStorage.removeItem('d2r_rwProfile');
    const m = line.match(/class="rwn-chip" data-arttip="(Strength|Wind)" data-arttip-ctx="([^"]+)"/);
    const imgM = line.match(/data-arttip="(?:Strength|Wind)"[^>]*>\s*<span class="d2art-wrap[^>]*aria-label="([^"]+)"/);
    return { ctx: m ? m[2] : null, artLabel: imgM ? imgM[1] : null };
  });
  expect(r.ctx).toBe('Scissors Katar');       // the hover will wear the claw
  expect(r.artLabel).toBe('Scissors Katar');  // the inline logo already does
});
