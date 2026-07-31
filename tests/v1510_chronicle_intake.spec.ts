import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1510 — THE CHRONICLE INTAKE KINDS.
//
// Konyo: "when chronicle/menu is clicked ingame it should automatically know we are about to register
// and read and analyze the CHRONICLE lists ... SETS/ and UNIQUES completes SEPARATED accordingly."
//
// The `grail` kind already read a collection tracker, but it carries a rule that is safe for a human
// deliberately importing their tracker and DANGEROUS for this arc: "if the UI shows no found-state at
// all, treat EVERY readable name as found." The chronicle sweep runs UNATTENDED over sealed reels, so
// one misread page under that rule would mass-register a whole ledger. These kinds invert it.
//
// This spec runs the REAL worker with a stubbed upstream, so the honesty rules are exercised as code,
// not asserted as prose. That matters: everything downstream — the retro sweep, the two-lane read, the
// apply step — trusts this response shape to tell it when NOT to ground something.

const SRC = fs.readFileSync(path.resolve(__dirname, '..', 'functions', 'api', 'intake.js'), 'utf8');

const VOCAB = [
  "Harlequin Crest (Shako)", 'Windforce', 'Stormshield', 'Titan’s Revenge',
  "Tal Rasha's Howling Wind", "Tal Rasha's Lidless Eye", "Tal Rasha's Adjudication",
  "Immortal King's Soul Cage", "Immortal King's Detail",
];

/** Run the real worker against a canned model reply. */
async function call(kind: string, modelJSON: any, body: any = {}) {
  const upstream = async () => ({
    ok: true,
    json: async () => ({
      content: [{ type: 'text', text: JSON.stringify(modelJSON) }],
      usage: { input_tokens: 1, output_tokens: 1 },
    }),
  });
  const run = new Function(
    'fetch',
    `${SRC.replace(/export async function/g, 'async function')}\nreturn onRequestPost;`,
  )(upstream);
  const res = await run({
    request: { json: async () => ({ image: 'x'.repeat(64), media_type: 'image/jpeg', names: VOCAB, kind, ...body }) },
    env: { ANTHROPIC_API_KEY: 'test' },
  });
  return JSON.parse(await res.text());
}

test.describe('v1510 — the Chronicle reads as two ledgers, and refuses out loud', () => {
  test('uniques: found is resolved to the vocabulary, unfound is carried but never counted', async () => {
    const r = await call('chronicle-uniques', {
      found: ['Harlequin Crest', 'Windforce'],
      notFound: ['Stormshield'],
      printedFound: 2, printedTotal: 3, conf: 0.9,
    });
    expect(r.ledger).toBe('uniques');
    expect(r.found).toEqual(['Harlequin Crest (Shako)', 'Windforce']);   // suffix-stripped vocab match
    expect(r.notFound).toEqual(['Stormshield']);
    expect(r.read).toEqual({ found: 2, notFound: 1 });
  });

  test('★ no visible found-state ⇒ NOTHING is found, and it says why', async () => {
    // the whole reason these kinds exist rather than reusing `grail`
    const r = await call('chronicle-uniques', {
      found: ['Harlequin Crest', 'Windforce', 'Stormshield'],
      stateVisible: false,
    });
    expect(r.found).toEqual([]);
    expect(r.note).toBe('no-found-state');
    expect(r.stateVisible).toBe(false);
  });

  test('★ a Sets page opened as Uniques registers nothing — the ledgers never cross', async () => {
    // a Sets screen tallied as Uniques is worse than no tally at all: it writes into the other store
    const r = await call('chronicle-uniques', {
      found: ["Tal Rasha's Howling Wind", "Tal Rasha's Lidless Eye"],
      wrongTab: true,
    });
    expect(r.found).toEqual([]);
    expect(r.note).toBe('wrong-ledger');
  });

  test('sets: pieces come back grouped under their set name AND flat', async () => {
    const r = await call('chronicle-sets', {
      found: ["Tal Rasha's Howling Wind", "Immortal King's Soul Cage"],
      notFound: ["Tal Rasha's Adjudication"],
      sets: [
        { set: "Tal Rasha's Wrappings", pieces: ["Tal Rasha's Howling Wind"], complete: false },
        { set: "Immortal King's Stone Crusher", pieces: ["Immortal King's Soul Cage"] },
      ],
    });
    expect(r.ledger).toBe('sets');
    expect(r.sets).toHaveLength(2);
    expect(r.sets[0].set).toBe("Tal Rasha's Wrappings");
    expect(r.sets[0].pieces).toEqual(["Tal Rasha's Howling Wind"]);
    expect(r.sets[0].complete).toBe(false);
    expect(r.found).toContain("Immortal King's Soul Cage");
  });

  test('the screen’s own numbers are a SECOND WITNESS — agreement is earned, not assumed', async () => {
    const agree = await call('chronicle-uniques', {
      found: ['Harlequin Crest', 'Windforce'], notFound: ['Stormshield'],
      printedFound: 2, printedTotal: 3,
    });
    expect(agree.witness).toBe('agree');
    expect(agree.printed).toEqual({ found: 2, total: 3 });

    const differ = await call('chronicle-uniques', {
      found: ['Harlequin Crest'], notFound: ['Windforce', 'Stormshield'],
      printedFound: 2, printedTotal: 3,
    });
    expect(differ.witness, 'a disagreement must be SURFACED, never resolved in our favour').toBe('differ');
  });

  test('★ a PARTIAL page can never claim a witness', async () => {
    // the trap: the panel scrolls, so its printed total counts the whole ledger while the page shows a
    // slice. "printed 2 = read 2" on a partial page is a coincidence, not corroboration.
    const r = await call('chronicle-uniques', {
      found: ['Harlequin Crest', 'Windforce'],   // 2 read of a 403-item ledger
      notFound: [], printedFound: 2, printedTotal: 403,
    });
    expect(r.wholePage).toBe(false);
    expect(r.witness).toBe('none');
  });

  test('unreadable rows surface as a vocabulary gap instead of vanishing', async () => {
    const r = await call('chronicle-uniques', { found: ['Harlequin Crest', 'Some Modded Thing'], notFound: [] });
    expect(r.found).toEqual(['Harlequin Crest (Shako)']);
    expect(r.unrecognized).toContain('Some Modded Thing');
  });

  test('the chronicle path never leaks into the vault intake contract', async () => {
    // it returns its own shape and takes no part in the items/sockets/finds pipeline
    const r = await call('chronicle-uniques', { found: ['Windforce'], notFound: [] });
    expect(r.items).toBeUndefined();
    expect(r.finds).toBeUndefined();
    expect(r.tally).toBeUndefined();
    // and the vault path is unchanged by our edit
    const v = await call('items', { items: ['Windforce'], finds: [], sockets: [], unrecognized: [] });
    expect(v.items).toEqual(['Windforce']);
  });

  test('the prompts state the unattended-read danger in their own words', () => {
    expect(SRC).toContain('chronicle-uniques');
    expect(SRC).toContain('chronicle-sets');
    expect(SRC).toMatch(/runs unattended/);
    expect(SRC).toMatch(/Never invent a name to complete a set/);
  });
});
