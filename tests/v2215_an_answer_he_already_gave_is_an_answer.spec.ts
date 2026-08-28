import { test, expect } from './_net_stub';
import * as path from 'path';

// v2215 — "this was asking me this yeerday i ticked them off already."
//
// The inbox had TWO buttons and only ONE of them was durable:
//   · tick it → writes d2r_foundLog → kaiChronicleSettledWhy finds it → never queued again ✅
//   · ignore  → drops the row, logs status:'dismissed' → and the queueing path never consulted
//               that log, so the next sweep re-proposed it from the same footage. Forever. ❌
//
// A dismissed name is in neither d2r_foundLog nor d2r_grailUnfound, so every "is this settled?"
// test answered no. The inbox looked like it was working the whole time — the row went away when
// he pressed it, which is exactly what made the loop invisible until he recognised the names.
//
// ⚠ AND A DISMISSAL MUST NOT BE PERMANENT. It is a ruling about the EVIDENCE ("one blurry sighting,
// no"), not about the item for all time. If a later reel reads it properly, never asking again
// would silently withhold a real find — the opposite failure, and the worse one. So the suppression
// is conditional on the evidence being no better than what he already refused.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

const NAME = "Razor's Edge";

async function seed(page: any) {
  await page.goto(URL);
  await page.waitForTimeout(300);
  await page.evaluate(() => {
    localStorage.setItem('d2r_ownerClaim', '*');
    localStorage.setItem('d2r_chronicleInbox', '[]');
    localStorage.setItem('d2r_chronicleInboxLog', '[]');
  });
  await page.reload();
  await page.waitForTimeout(1400);
}

/** Feed the sweep one held sighting, the way a reel does. */
async function propose(page: any, name: string, gateHeld: boolean) {
  return page.evaluate(([n, held]: [string, boolean]) => {
    const reg = (window as any).kaiChroniclePropose;
    if (typeof reg !== 'function') return { err: 'kaiChroniclePropose is gone' };
    return reg([{ name: n, tier: 'grail', gateHeld: held,
                  gateWhy: held ? 'only 1 independent witness' : null,
                  frameId: 'f_1.jpg', sessionId: 'reel_test', firstSeenTs: 1 }]);
  }, [name, gateHeld]);
}

const queue = (page: any) => page.evaluate(() =>
  (JSON.parse(localStorage.getItem('d2r_chronicleInbox') || '[]') || [])
    .map((x: any) => x && x.name));

const logStatus = (page: any, n: string) => page.evaluate((nm: string) => {
  const rows = JSON.parse(localStorage.getItem('d2r_chronicleInboxLog') || '[]') || [];
  const hit = rows.filter((r: any) => r && r.name === nm).pop();
  return hit ? { status: hit.status, why: hit.why } : null;
}, n);

test.describe('v2215 an answer he already gave is an answer', () => {
  test('a name he IGNORED is not proposed again from the same evidence', async ({ page }) => {
    await seed(page);

    const first = await propose(page, NAME, true);
    expect(first.err).toBeUndefined();
    expect(await queue(page), 'the first sighting did not reach the inbox, so this test is not '
      + 'exercising the queue at all').toContain(NAME);

    await page.evaluate((n: string) => (window as any).kaiChronicleDismiss(n), NAME);
    expect(await queue(page), 'ignore did not remove the row').not.toContain(NAME);
    expect((await logStatus(page, NAME))!.status).toBe('dismissed');

    // the next sweep sees the same item again, exactly as his reels do
    await propose(page, NAME, true);
    expect(await queue(page),
      `"${NAME}" was queued AGAIN after he ignored it. He answered this yesterday; asking again `
      + `from the same footage is the loop he reported, and it is invisible because the row does `
      + `disappear each time he presses the button.`).not.toContain(NAME);

    const st = await logStatus(page, NAME);
    expect(st!.status).toBe('dismissed');
    expect(st!.why, 'the log does not say WHY it was skipped, so the suppression is unexplainable')
      .toContain('already ignored');
  });

  test('but STRONGER evidence earns one new ask', async ({ page }) => {
    // ⚠ THE HALF THAT KEEPS THIS HONEST. Without it a single "ignore" on a blurry frame would hide
    // a real find for good, which is a worse failure than being asked twice.
    await seed(page);
    await propose(page, NAME, true);          // held by the gate
    await page.evaluate((n: string) => (window as any).kaiChronicleDismiss(n), NAME);
    expect(await queue(page)).not.toContain(NAME);

    await propose(page, NAME, false);         // now it CLEARS the gate
    expect(await queue(page),
      'a sighting that now clears the gate was suppressed by an old dismissal — a wrong "ignore" '
      + 'would hide a real find forever').toContain(NAME);

    // ⚠ AND IT MUST ASK, NOT DECIDE. Measured while writing this: without the guard, a dismissed
    // name whose next sighting cleared the gate went STRAIGHT into d2r_foundLog as
    // `safe-auto-grail` — the machine silently overruling an explicit human "no". A wrong tick in
    // his grail is invisible; a question is not.
    const found = await page.evaluate((n: string) =>
      !!JSON.parse(localStorage.getItem('d2r_foundLog') || '{}')[n], NAME);
    expect(found, `"${NAME}" was auto-ticked into the found ledger after he had explicitly ignored `
      + `it. Better evidence earns him a QUESTION, never a decision made on his behalf.`)
      .toBe(false);

    const row = await page.evaluate((n: string) => {
      const q = JSON.parse(localStorage.getItem('d2r_chronicleInbox') || '[]') || [];
      return q.find((x: any) => x && x.name === n) || null;
    }, NAME);
    expect(row.triageWhy, 'the re-ask does not say why he is being asked again, so it looks like '
      + 'the loop he complained about').toContain('cleared the gate');
  });

  test('a name he TICKED is still never asked again', async ({ page }) => {
    // the path that already worked must keep working — the fix must not disturb it
    await seed(page);
    await propose(page, NAME, true);
    await page.evaluate((n: string) => (window as any).kaiChronicleAccept(n), NAME);
    expect(await queue(page)).not.toContain(NAME);
    await propose(page, NAME, true);
    expect(await queue(page), 'a name written into the found ledger came back into the inbox')
      .not.toContain(NAME);
  });

  test('a name he has never answered is still asked', async ({ page }) => {
    // the suppression must not become a blanket silence
    await seed(page);
    await propose(page, 'Windforce', true);
    expect(await queue(page), 'a brand-new proposal was suppressed — the inbox would go silent')
      .toContain('Windforce');
  });
});
