import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1918 — THE PER-ITEM LEDGER EXISTED AND THE ACCEPT PATH COULD NOT REACH IT.
 *
 * Konyo: "make sure it does register the items properly timestamped based on when it did analyze it
 * and add it to the vault/chronicle or whatever else happened in ledger while its routing and
 * funneling and tallying dii language so its related to the game and understood whats happening so
 * that way we can surgically fix something going in the future when it wrongly routes or funnels or
 * analyzes."
 *
 * He is describing d2r_chronicleInboxLog, which the file's own comment already calls the "VISUAL
 * BACKEND — every KAI read forever for debug". It was IIFE-private, so chronicleApply could not
 * call it even though they live in the same file.
 *
 * MEASURED on the proposal sitting on his disk: 302 rows ready to apply, ALL 302 carrying `why` +
 * `witnesses[]` + `seen[{reel,frame,lane}]`, and chronicleApply read exactly three fields per row
 * (name, date, gameFound). Six provenance facts arrived; one survived.
 *
 * These tests pin the whole round trip, because every part of it has been broken before by a change
 * that looked unrelated: the publish, the routing answer (WHICH store), the Diablo wording, and the
 * refusal — which is the row most worth having and the one that used to vanish without trace.
 */
test.describe('v1918 — every applied item leaves a provenance row', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => window.localStorage.setItem('d2r_chronicleInboxLog', '[]'));
  });

  const PROPOSAL = {
    wouldAdd: {
      uniques: [{
        name: 'Harlequin Crest',
        why: 'corroborated by cross-lane, cross-reel',
        witnesses: ['cross-lane', 'cross-reel'],
        seen: [{ reel: 'reel_s_1786998496819_31092', frame: 'f_1786998503940.jpg', lane: 'claude' }],
        gameFound: { at: '08/16/2026, 02:18', by: 'Andariel' },
      }],
      sets: [
        {
          name: "Tancred's Skull (bone helm)",
          witnesses: ['cross-frame'],
          seen: [{ reel: 'reel_s_1787177267889_92273', frame: 'f_1.jpg', lane: 'grok' }],
        },
        { name: 'Totally Not A Set Piece', witnesses: ['cross-frame'], seen: [] },
      ],
    },
  };

  const rows = (page: any) => page.evaluate(() =>
    JSON.parse(window.localStorage.getItem('d2r_chronicleInboxLog') || '[]'));

  test('★★★ the row says WHERE it landed — the routing answer he wants to debug', async ({ page }) => {
    await page.evaluate((p) => (window as any).chronicleApply(p), PROPOSAL);
    const log = await rows(page);
    const uni = log.find((r: any) => r.name === 'Harlequin Crest');
    expect(uni, 'the accepted unique left no ledger row at all').toBeTruthy();
    expect(uni.store, 'the store is the routing fact — foundLog (grail ledger) vs owned (vault)').toBe('foundLog');
    expect(uni.ledger).toBe('uniques');
    expect(uni.status).toBe('accepted');

    const set = log.find((r: any) => r.name === "Tancred's Skull (bone helm)");
    expect(set.store, 'a set piece lands in setPieces, not the uniques ledger').toBe('setPieces');
    expect(set.ledger).toBe('sets');
  });

  test('★★★ a REFUSAL leaves a trace — it used to vanish silently', async ({ page }) => {
    await page.evaluate((p) => (window as any).chronicleApply(p), PROPOSAL);
    const log = await rows(page);
    const no = log.find((r: any) => r.name === 'Totally Not A Set Piece');
    expect(no, 'the refused name left nothing behind — a refusal and a name never proposed looked identical').toBeTruthy();
    expect(no.status).toBe('refused');
    expect(no.store).toBe('refused');
    expect(String(no.why).toLowerCase()).toContain('roster');
  });

  test('★★ the WHY is in his words, not the gate’s codes', async ({ page }) => {
    await page.evaluate((p) => (window as any).chronicleApply(p), PROPOSAL);
    const log = await rows(page);
    const uni = log.find((r: any) => r.name === 'Harlequin Crest');
    expect(uni.why).toContain('two different eyes read the same row');   // cross-lane
    expect(uni.why).toContain('two separate Chronicle visits');          // cross-reel
    expect(uni.why, 'the raw code leaked into the sentence').not.toContain('cross-lane');
  });

  test('★★ which photograph, which eye, and when the GAME says he found it', async ({ page }) => {
    await page.evaluate((p) => (window as any).chronicleApply(p), PROPOSAL);
    const log = await rows(page);
    const uni = log.find((r: any) => r.name === 'Harlequin Crest');
    expect(uni.reel).toBe('reel_s_1786998496819_31092');
    expect(uni.frameId).toBe('f_1786998503940.jpg');
    expect(uni.lane).toBe('claude');
    expect(uni.gameFoundAt, 'the in-game First Found stamp is the storyline fact').toBe('08/16/2026, 02:18');
    expect(uni.gameFoundBy).toBe('Andariel');
    expect(typeof uni.lastTs, 'when this board analyzed it — the ledger stamp, kept separate').toBe('number');
  });

  test('★★ nothing is invented for a row that carries no evidence', async ({ page }) => {
    await page.evaluate(() => (window as any).chronicleApply({
      wouldAdd: { uniques: [{ name: 'Stormshield' }], sets: [] },
    }));
    const log = await rows(page);
    const bare = log.find((r: any) => r.name === 'Stormshield');
    expect(bare, 'a bare row still deserves a ledger entry').toBeTruthy();
    expect(bare.store).toBe('foundLog');
    expect(bare.reel ?? null, 'a reel was invented for a row that named none').toBeNull();
    expect(bare.gameFoundAt ?? null, 'a game date was invented').toBeNull();
    expect(bare.why, 'with no witnesses it must still say something true').toBeTruthy();
  });

  test('★ the recorder is reachable from outside its IIFE — the join itself', async ({ page }) => {
    const kinds = await page.evaluate(() => [
      typeof (window as any).kaiChronicleRecord,
      typeof (window as any)._chRecordApplied,
      typeof (window as any)._chSayWitnesses,
    ]);
    expect(kinds, 'the recorder went private again and the accept path cannot reach it')
      .toEqual(['function', 'function', 'function']);
  });
});
