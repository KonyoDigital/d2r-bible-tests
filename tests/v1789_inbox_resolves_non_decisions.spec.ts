import { test, expect } from './_net_stub';
import * as path from 'path';
import { suppressOneShots } from './_oneshots';

// v1789 — MOST OF THE QUEUE WAS NEVER HIS DECISION.
//
// Konyo, looking at 49 pending rows: "these 49 items.. what exactly do they do they are like pending
// items that were chornicle read? and they want my approval? why? cant like an extra AI take care of
// it and cross reference it with specific and focused hunts for it to cross reference it here and
// automatically grail it.. and if it still cant then leave it for me to tick off."
//
// He was right. The server-side ledger was read by hand the day this shipped: of 36 held names, SIX
// were unresolved uniques. Six were OCR slips of items ALREADY in his grail ("Battlecage" for
// Rattlecage, "Naglring" for Nagelring). Twenty-four were reader debris — and the debris has a
// boring, specific cause that makes the rule obvious: THE CHRONICLE PRINTS THE BASE ITEM NAME FOR A
// ROW HE HAS NOT FOUND. "Templar Coat", "Bone Visage", "Wrist Sword" are not near-misses; they are
// the game stating the OPPOSITE of a find, written down faithfully by the reader.
//
// WHAT THIS SPEC PINS is the boundary, not the cleanup: a row that MIGHT be a real find is never
// dismissed. A wrong dismissal deletes a find silently, which is strictly worse than a queue that is
// too long — so "Toothrow", a roster unique he does not have, must survive every pass.
//
// The found-state here is written with the app's OWN writer (kaiChronicleAccept). An earlier version
// of this check seeded `d2r_foundLog` directly and read false back from `_gFound`: the real key is
// install-scoped ("I·<installId>·d2r_foundLog"), so the fixture was writing to a key nothing reads.
// Hardcoding that prefix in a test would put a second copy of the fork rule in the tree; asking the
// app to record the find keeps one.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* Seed the queue AND clear everything the resolver reads, because these specs share a `file://`
   origin with every other spec in the shard — including their own earlier tests.

   Measured twice, the hard way. First: other specs write the grail, so held names arrived already
   `found: true` and were retired as "already in your grail". Then v1790 added a KEEP-LIST for rows
   he puts back, and the put-back test wrote "Templar Coat" into it — after which every earlier test
   in the file stopped retiring that row and five assertions went red at once. A fixture that seeds
   only what it wants and inherits the rest is not testing the code, it is testing the run order. */
/* v1939 — BOOT AS A LATER LOAD. Every test in this file establishes the exact inbox state it
   measures, and then a boot one-shot edits the board underneath it. This file already carries the
   scar in prose — "the shard may have marked these found" — and ensureUnfound() was written to
   repair the damage after the fact. Suppressing the applies stops it happening. Derived from
   bible.html, never hand-listed (tests/_oneshots.ts). */
const BOOT_AS_LATER_LOAD = suppressOneShots();

async function seedInbox(page: any, names: string[]) {
  await page.addInitScript(([ns, flags]: [string[], Record<string, string>]) => {
    for (const k of Object.keys(flags)) localStorage.setItem(k, flags[k]);
    localStorage.removeItem('d2r_chronicleAutoRetired');
    localStorage.removeItem('d2r_chronicleKeepPending');
    localStorage.setItem('d2r_chronicleInbox', JSON.stringify(ns.map((n) => ({ name: n }))));
  }, [names, BOOT_AS_LATER_LOAD]);
}

// NOTE ON HOW THESE ASSERT, and the two corrections that got them here.
//
// (1) The first cut called kaiChronicleResolvePending({dryRun:true}) after page load and checked its
// return. It came back EMPTY on CI, and correctly: renderInboxFab runs the resolver AT LOAD — that is
// the whole point, "i dont want it pending my decisions at all if its not needed" — so by the time
// the test asked, the non-decisions were already retired.
//
// (2) The second cut asserted the dismissed list EXACTLY, and CI reported "Toothrow" dismissed as
// well, on all three tests, while a pristine local profile kept it every time. `Toothrow` resolves
// 'unique' and `_gFound('Toothrow')` is false locally, so the only branch that can retire it is
// "already in your grail" — which means something in the shard had already marked it found. These
// specs share a `file://` origin with every other spec in the shard, and several of them seed
// `d2r_foundLog` directly.
//
// Rather than guess at that, these now assert THE CLAIM instead of the whole world: the named
// non-decisions ARE retired for the stated reason, and a name is only required to survive when this
// page agrees it is not already found. A test that depends on global cleanliness it does not own is
// measuring the shard, not the code.

/* v1794 — POLL, DO NOT RACE. renderInboxFab's auto-run is on a 900ms timer after `load`, so reading
   the receipt straight off `goto` is a coin flip that lands right only when the lines before it
   happen to be slow. Measured on this tree at v1793 (before any v1794 code existed): four of these
   tests failed with an EMPTY receipt on all three retries — not a wrong verdict, an unwritten one.
   Waiting for the automatic path is also the more honest test, because the automatic path is the
   feature: "i dont want it pending my decisions at all if its not needed." */
/* `require: false` for the one caller that is asserting a receipt should be EMPTY. A receipt is only
   written when the resolver actually retired something, so "no receipt" is the correct outcome of the
   safety-boundary test and waiting for one there would fail on the code behaving perfectly — the
   first version of this helper did exactly that. That caller drives renderInboxFab() by hand and has
   no race to lose. */
async function receiptOf(page: any, opts: { require?: boolean } = {}) {
  if (opts.require !== false) {
    await expect
      .poll(() => page.evaluate(() => !!(window as any)._inboxLastResolve), { timeout: 15000 })
      .toBe(true);
  }
  return await page.evaluate(() => (window as any)._inboxLastResolve || { dismissed: [], kept: [] });
}

/* Make these names NOT-FOUND on this page, whatever the shard left behind.
   Measured on CI: all six of the held names came back `found: true`, because these specs share a
   `file://` origin with every other spec in the shard and several of them write the grail. A test
   that needs a name to be unfound has to establish that itself — asking nicely and hoping is how a
   suite ends up measuring its neighbours. toggleOwned is the board's own writer, so this goes
   through the same door a click does and needs no knowledge of the install-scoped key. */
async function ensureUnfound(page: any, names: string[]) {
  await page.evaluate((ns: string[]) => {
    ns.forEach((n) => {
      for (let i = 0; i < 3 && (window as any)._gFound(n); i++) (window as any).toggleOwned(n);
    });
  }, names);
}

test('a base item name is retired — the Chronicle prints it for a row he has NOT found', async ({ page }) => {
  await seedInbox(page, ['Templar Coat', 'Bone Visage', 'Toothrow']);
  await page.goto(URL);
  const receipt = await receiptOf(page);
  const by = new Map<string, any>(receipt.dismissed.map((d: any) => [d.name, d]));
  const ctx = JSON.stringify(receipt);
  /* ASSERT THE MEANING, NOT THE SENTENCE — and then assert that the meaning is specific.

     v1793 moved the wording from "a base item name" to naming the unique he is still missing, and
     three specs pinned to the old string went red on a change that was entirely intended. So what
     must stay true is that the row is retired and says it is a not-found row.

     But "matches /NOT found/" alone would stay green if the panel stopped naming anything useful,
     which is the one thing v1793 existed to add ("it needs to tell me the UNIQUE name of the item
     itself not the BASE ITEM"). So the specific unique is pinned too. Two sessions arrived at this
     fix independently, from opposite ends; this is the union of both. */
  /* v1794 — ASSERTING THE v1793 BEHAVIOUR, which this line had never caught up with. v1793 made the
     retire name the UNIQUE instead of the base ("the base item is less relevant in this case" — his
     words), so a base the codex can resolve now retires as "the Chronicle shows this base for a
     unique you have NOT found" and carries that unique in `uni`. The old assertion still demanded
     the literal "base item name", which is now only the FALLBACK wording for a base the codex cannot
     resolve — so the test failed on the tree that shipped the improvement. Both branches are pinned
     below rather than one loose substring, because the fallback is the case that silently says less. */
  for (const n of ['Templar Coat', 'Bone Visage']) {
    const d = by.get(n);
    expect(d, ctx).toBeTruthy();
    expect(d.why, ctx).toContain('you have NOT found');
    expect(d.uni.length, ctx).toBeGreaterThan(0);
  }
  expect(by.get('Templar Coat').uni, ctx).toContain('Guardian Angel');
  expect(by.get('Bone Visage').uni, ctx).toContain('Giant Skull');
});

test('a truncated read is retired — the reader was quoting its own damage', async ({ page }) => {
  await seedInbox(page, ['Firel...', 'Heavas (partially obscured)', 'Toothrow']);
  await page.goto(URL);
  const receipt = await receiptOf(page);
  const why = new Map<string, string>(receipt.dismissed.map((d: any) => [d.name, d.why]));
  const ctx = JSON.stringify(receipt);
  for (const n of ['Firel...', 'Heavas (partially obscured)']) {
    expect(why.get(n), ctx).toContain('truncated');
  }
});

test('a name he already has is retired — there is nothing to rule on', async ({ page }) => {
  await seedInbox(page, ['Toothrow']);
  await page.goto(URL);
  // record the find with the app's OWN writer. Seeding d2r_foundLog directly does not work: the real
  // key is install-scoped ("I·<installId>·d2r_foundLog"), so _gFound reads false and the branch never
  // fires. Hardcoding that prefix here would put a second copy of the fork rule in the tree.
  await page.evaluate(() => {
    (window as any).kaiChronicleAccept('Rattlecage');
    localStorage.setItem('d2r_chronicleInbox', JSON.stringify([{ name: 'Rattlecage' }]));
    (window as any).renderInboxFab();
  });
  expect(await page.evaluate(() => !!(window as any)._gFound('Rattlecage'))).toBe(true);
  const receipt = await receiptOf(page);
  const why = new Map<string, string>(receipt.dismissed.map((d: any) => [d.name, d.why]));
  expect(why.get('Rattlecage'), JSON.stringify(receipt)).toContain('already in your grail');
});

test('a roster unique he does NOT have is never dismissed', async ({ page }) => {
  // THE SAFETY BOUNDARY. Every one of these six was later confirmed by eye to be a real find with a
  // date and a source monster, so a wrong dismissal here deletes a find silently — strictly worse
  // than a queue that is too long. Only names this page agrees are NOT already found are required to
  // survive; one that is already found is legitimately retired and proves nothing either way.
  const real = ['Latent Cold Rupture', 'Latent Crack of the Heavens', 'Latent Rotting Fissure',
                "Thundergod's Vigor", 'Toothrow', 'Witherstring'];
  await seedInbox(page, real);
  await page.goto(URL);
  await ensureUnfound(page, real);
  await page.evaluate((ns: string[]) => {
    localStorage.setItem('d2r_chronicleInbox', JSON.stringify(ns.map((n) => ({ name: n }))));
    (window as any)._inboxLastResolve = null;
    (window as any).renderInboxFab();
  }, real);
  const state = await page.evaluate((ns: string[]) => ns.map((n) => ({
    name: n,
    found: !!(window as any)._gFound(n),
    kind: ((window as any).d2rResolveItem(n) || {}).kind,
  })), real);
  // require:false — this test's whole claim is that NOTHING was retired, and a receipt is only
  // written when something was. renderInboxFab() above ran synchronously, so there is nothing to wait
  // for; waiting anyway would fail on the code being right.
  const receipt = await receiptOf(page, { require: false });
  const dismissed = new Set(receipt.dismissed.map((d: any) => d.name));
  const ctx = JSON.stringify({ state, receipt });
  const unfound = state.filter((s: any) => !s.found);
  expect(unfound.length, ctx).toBeGreaterThan(0);
  for (const s of unfound) {
    expect(s.kind, ctx).toBe('unique');
    expect(dismissed.has(s.name), ctx).toBe(false);
  }
});

test('the panel shows a receipt for the rows it cleared on its own', async ({ page }) => {
  await seedInbox(page, ['Templar Coat', 'Toothrow']);
  await page.goto(URL);
  await page.evaluate(() => {
    (window as any).renderInboxFab();
    const pop = document.getElementById('inbox-pop');
    if (pop && !pop.classList.contains('open')) (window as any).inboxPopTog();
  });
  const pop = page.locator('#inbox-pop');
  await expect(pop).toHaveClass(/open/);
  // a queue that silently got smaller is indistinguishable from a lost one
  // The .filter() is LOAD-BEARING as of v1794: the panel now renders a second .ibp-auto block for
  // the reader hand-off, so an unfiltered locator matches two elements and Playwright raises a
  // strict-mode violation instead of asserting anything.
  const cleared = pop.locator('.ibp-auto').filter({ hasText: 'cleared automatically' });
  await expect(cleared).toContainText('cleared automatically');
  // v1794 — and it names the UNIQUE, not the base. v1793 made that the point of the row: "it needs
  // to tell me the UNIQUE name of the item itself not the BASE ITEM." Asserting the old "base item
  // name" wording meant the panel could stop naming anything useful and this would stay green.
  await expect(cleared).toContainText('Guardian Angel');
  await expect(cleared).toContainText('shown as Templar Coat');
});

test('every pending row actually SHOWS its name and both buttons', async ({ page }) => {
  // v1789 — a GEOMETRY assertion, because no text assertion could have caught this. `.ibp-why` is
  // flex:0 0 100%, and in a row without flex-wrap it took the whole line and squeezed the item name
  // and both buttons to ZERO width. textContent was perfect the entire time: the name was in the
  // DOM, correctly escaped, with working handlers — and the panel rendered three rows reading
  // "unclear read" with nothing on them to act on. The one thing he needs from this panel is the
  // name. Only a screenshot showed it.
  const rowNames = ['Toothrow', 'Witherstring', "Thundergod's Vigor"];
  await seedInbox(page, rowNames);
  await page.goto(URL);
  // the shard may have marked these found, in which case the resolver retires them and there are no
  // rows left to measure — establish the state this test needs instead of inheriting it
  await ensureUnfound(page, rowNames);
  await page.evaluate((ns: string[]) => {
    localStorage.setItem('d2r_chronicleInbox', JSON.stringify(ns.map((n) => ({ name: n }))));
    (window as any).renderInboxFab();
  }, rowNames);
  await page.evaluate(() => (window as any).inboxPopTog());
  await expect(page.locator('#inbox-pop .ibp-row')).toHaveCount(3);

  /* v1939 — MEASURE THE WHOLE PANEL IN ONE EVALUATE, NOT THROUGH SIX LOCATOR ROUND-TRIPS.
     This used `await expect(nm).toBeVisible()` and then `await nm.boundingBox()` as two separate
     calls. The panel re-renders (the resolver runs on its own), so the element the first call
     verified is detached by the time the second measures it, and boundingBox() answers null for a
     row that is on screen and perfectly fine. It threw `Cannot read properties of null (reading
     'width')` on CI, passed twelve-for-twelve locally twice, then failed locally on the third run —
     a flake, not a layout defect.

     The geometry claim is unchanged and still a GEOMETRY claim, which is the whole point of this
     test: `.ibp-why` is flex:0 0 100% and once squeezed the name and both buttons to zero width
     while textContent stayed perfect. One synchronous pass over the live DOM cannot be raced.
     [[chrome-cdp-mac]] — "markers do not survive a re-render; make query and measure one atomic
     evaluate". */
  const measured = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('#inbox-pop .ibp-row')) as HTMLElement[];
    return rows.map((row, i) => {
      const nm = row.querySelector('.ibp-nm') as HTMLElement | null;
      const btns = (Array.from(row.querySelectorAll('button')) as HTMLElement[]).map((b) => ({
        text: (b.textContent || '').trim().toLowerCase(),
        w: b.getBoundingClientRect().width,
        display: getComputedStyle(b).display,
      }));
      return {
        i,
        nmText: nm ? (nm.textContent || '').trim().slice(0, 40) : null,
        nmW: nm ? nm.getBoundingClientRect().width : null,
        btns,
        html: row.innerHTML.slice(0, 200),
      };
    });
  });

  expect(measured.length, 'the panel did not render three rows').toBe(3);
  for (const r of measured) {
    expect(r.nmText, `row ${r.i} has no .ibp-nm at all — ${r.html}`).toBeTruthy();
    expect(r.nmW ?? 0, `row ${r.i} name "${r.nmText}" is squeezed to ${r.nmW}px — ${r.html}`)
      .toBeGreaterThan(40);
    for (const label of ['tick it', 'ignore']) {
      const b = r.btns.find((x) => x.text.includes(label));
      expect(b, `row ${r.i} has no "${label}" button — buttons were ${JSON.stringify(r.btns)}`)
        .toBeTruthy();
      expect(b!.w, `row ${r.i} "${label}" button is ${b!.w}px wide (display:${b!.display})`)
        .toBeGreaterThan(20);
    }
  }
});

test('an auto-retired row can be put back, and it STAYS back', async ({ page }) => {
  // v1790 — Konyo: "how long after it retires when i dont click it? maybe like it should have a
  // certain timelimit for this." The honest answer was: no time at all. The resolver ran at page
  // load and the row was gone before he had opened the panel, with no way to reverse it.
  //
  // Retirement stays immediate — being asked is the thing he does not want — but it is reversible
  // for 7 days. A timer that merely expired would have been the wrong shape: it runs out while he
  // sleeps and changes nothing he can act on. What he needs is a way back AFTER it acted.
  //
  // The second assertion is the one that matters. Without the keep-list, the next render retires
  // the row again and the button looks broken while behaving exactly as designed.
  /* v1794 — THE ROW UNDER TEST IS A TRUNCATION NOW, and that is the fix, not a workaround. v1793
     removed the "put back" button from BASE rows on purpose: a grey Chronicle row is the game saying
     "not found", so the retire is CERTAIN and an undo would offer a decision that does not exist.
     This test had been driving the v1790 grace window through 'Templar Coat' — precisely the row
     v1793 made un-put-backable — so it was asserting a button the design had deliberately deleted.
     A truncated read is the honest subject: the reader was quoting its own damage, that is a
     JUDGEMENT rather than a certainty, and it is exactly the kind of retire he should be able to
     reverse. */
  await seedInbox(page, ['Firel...', 'Toothrow']);
  await page.goto(URL);
  await receiptOf(page);          // wait for the auto-run rather than racing its 900ms timer

  const retired = await page.evaluate(() => (window as any).kaiChronicleRetiredRecent());
  expect(retired.map((r: any) => r.name)).toContain('Firel...');
  expect(retired[0].why).toContain('truncated');
  expect(retired[0].ts).toBeGreaterThan(0);

  await page.evaluate(() => {
    const pop = document.getElementById('inbox-pop');
    if (pop && !pop.classList.contains('open')) (window as any).inboxPopTog();
  });
  const back = page.locator('#inbox-pop .ibp-rr-b').first();
  await expect(back).toBeVisible();
  expect((await back.boundingBox())!.width).toBeGreaterThan(20);
  await back.click();

  const names = () => page.evaluate(() =>
    ((window as any).kaiChronicleInbox({ sync: false }) || []).map((x: any) => x.name));
  expect(await names()).toContain('Firel...');

  // it must survive re-renders — this is where a naive undo silently loses
  await page.evaluate(() => { (window as any).renderInboxFab(); (window as any).renderInboxFab(); });
  expect(await names()).toContain('Firel...');
  const after = await page.evaluate(() => (window as any).kaiChronicleRetiredRecent());
  expect(after.map((r: any) => r.name)).not.toContain('Firel...');
});

test('a row retired longer ago than the grace window is no longer offered', async ({ page }) => {
  // the window has to actually bound something, or "kept for 7 days" is decoration
  await page.addInitScript(() => {
    localStorage.removeItem('d2r_chronicleKeepPending');
    const old = Date.now() - 9 * 864e5;
    localStorage.setItem('d2r_chronicleAutoRetired',
      JSON.stringify([{ name: 'Templar Coat', why: 'a base item name', ts: old }]));
    localStorage.setItem('d2r_chronicleInbox', JSON.stringify([{ name: 'Toothrow' }]));
  });
  await page.goto(URL);
  const recent = await page.evaluate(() => (window as any).kaiChronicleRetiredRecent());
  expect(recent.map((r: any) => r.name)).not.toContain('Templar Coat');
});

test('a base name is dismissed at triage and NAMES the unique still to hunt', async ({ page }) => {
  // v1793 — Konyo: "the PUTBACK shouldnt even tell me anything in this case ... its accidentally
  // tallying or MAYBE tallying and is unsure of if it a chorincle.. but it cant be because it greyed
  // out." Both halves right. The in-game Chronicle prints the BASE name for a row he has NOT found —
  // grey, no date, no dropper — so the row is the game stating the OPPOSITE of a find. It reached the
  // queue because the register hands triage a bare NAME with no found-state, throwing away the one
  // fact that settles it.
  //
  // And the base is the wrong noun to show him: ITEM_CODEX knows the specific base per unique, so the
  // row resolves back to what he is actually missing. Two options for one base is the normal case,
  // not an edge one — the two grey "Thunder Maul" rows in his footage are Cranium Basher AND Earth
  // Shifter, which is also why a base can appear twice and look like a duplicate.
  await page.goto(URL);
  const verdicts = await page.evaluate(() =>
    ['Ancient Sword', 'Basinet', 'Thunder Maul', 'Toothrow'].map((n) => ({
      name: n, v: (window as any).kaiChronicleTriage({ name: n }),
    })));
  const by: any = Object.fromEntries(verdicts.map((x: any) => [x.name, x.v]));
  expect(by['Ancient Sword'].action).toBe('dismiss');
  expect(by['Ancient Sword'].why).toContain('The Atlantean');
  expect(by['Basinet'].why).toContain('Darksight Helm');
  // two uniques on one base — both named
  expect(by['Thunder Maul'].why).toContain('Cranium Basher');
  expect(by['Thunder Maul'].why).toContain('Earth Shifter');
  // a real unique is untouched by this rule
  expect(by['Toothrow'].action).toBe('accept');
});

test('when the game and the ledger disagree the row is HELD, never dismissed', async ({ page }) => {
  // The one case that must not be swallowed: the panel called this base unfound and the board says he
  // owns every unique built on it. Both cannot be true, and dismissing it destroys the only evidence
  // the disagreement exists. The contradiction IS the finding.
  await page.goto(URL);
  const before = await page.evaluate(() => (window as any).kaiChronicleTriage({ name: 'Ancient Sword' }));
  expect(before.action).toBe('dismiss');
  const after = await page.evaluate(() => {
    (window as any).kaiChronicleAccept('The Atlantean');
    return (window as any).kaiChronicleTriage({ name: 'Ancient Sword' });
  });
  expect(after.action).toBe('hold');
  expect(after.why).toContain('The Atlantean');
  const said = await page.evaluate((w: string) => (window as any)._chSayWhy(w), after.why);
  expect(said).toContain('disagree');
});

test('the humaniser is a real global, not one trapped inside a render function', async ({ page }) => {
  // v1793 — the first attempt to share it assigned window._chSayWhy INSIDE renderInbox, which had not
  // run, so the widget still printed the raw code. A shared thing defined inside a function nobody
  // called is not shared.
  await page.goto(URL);
  expect(await page.evaluate(() => typeof (window as any)._chSayWhy)).toBe('function');
  expect(await page.evaluate(() => (window as any)._chSayWhy('human-review')))
    .toContain('needs your eye');
});

test('a base row offers NO put back, because its retire is certain', async ({ page }) => {
  // v1793 — Konyo: "the PUTBACK shouldnt even tell me anything in this case ... it cant be because it
  // greyed out." A grey Chronicle row is the game stating the opposite of a find, so the retire can
  // never be wrong and an undo would imply a decision that does not exist. The row still SHOWS —
  // what it names is worth knowing — it just has nothing to press.
  await seedInbox(page, ['Templar Coat', 'Firel...', 'Toothrow']);
  await page.goto(URL);
  await page.evaluate(() => {
    (window as any).renderInboxFab();
    const pop = document.getElementById('inbox-pop');
    if (pop && !pop.classList.contains('open')) (window as any).inboxPopTog();
  });
  const rows = page.locator('#inbox-pop .ibp-rr');
  const texts = await rows.allTextContents();
  const baseRow = texts.find((t) => /Templar Coat/.test(t)) || '';
  expect(baseRow).toContain('still to hunt');
  expect(baseRow).not.toContain('put back');
  // the uncertain one keeps its undo
  const truncRow = texts.find((t) => /Firel/.test(t)) || '';
  expect(truncRow).toContain('put back');
});
