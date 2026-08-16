import { test } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';
const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');
/* SKIPPED (v1728, matching the audit 2026-06-12 convention applied to diag2.spec.ts and
   picks_count_diag.spec.ts): dev diagnostic with zero expect()s — it writes /tmp/rarity_audit.json
   and asserts nothing, so it can only ever fail by timing out under full-suite load, or on the
   Windows half of the dual-machine setup where /tmp does not exist. Both are false reds about
   nothing. It is the last survivor of the class that audit swept: it ran in the live 6-way shard
   because the leading underscore filters nothing — testDir is ./tests and no config excludes it.
   Kept rather than deleted: the diagnostic itself is useful when run deliberately. */
test.skip('rarity audit', async ({ page }) => {
  await page.goto(BIBLE);
  await page.waitForTimeout(600);
  const data = await page.evaluate(() => {
    const ITEMS = (window as any).ITEMS || [];
    const CODEX = (window as any).ITEM_CODEX || {};
    const ar = (window as any)._artRarity;
    const dist: Record<string, number> = {};
    const unclassified: string[] = [];
    const codexMissing: string[] = [];
    const rows: any[] = [];
    for (const it of ITEMS) {
      const n = it.n;
      const r = ar ? ar(n) : '';
      dist[r || '(none)'] = (dist[r || '(none)'] || 0) + 1;
      const cx = CODEX[n];
      if (!r) unclassified.push(n);
      if (!cx || !cx.rarity) codexMissing.push(n);
      rows.push({ n, rarity: r, codex: cx ? cx.rarity : null });
    }
    return { total: ITEMS.length, dist, unclassified, codexMissing, rows };
  });
  fs.writeFileSync('/tmp/rarity_audit.json', JSON.stringify(data, null, 2));
});
