import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1558 — THE CHRONICLE READ HAD NO SCHEMA, SO IT COULD NOT ANSWER.
//
// Found by a 12-agent adversarial audit, and it is a defect in code I shipped this session.
//
// v1510 built the chronicle prompts, the worker handler and nine tests. v1540 gave them a caller.
// But the `output_config` chain never grew an `isChron` branch, so a Chronicle read fell through to
// `itemsSchema` — which can express `items` and `unrecognized` and nothing else. The handler reads
// parsed.found / notFound / sets / printedFound / stateVisible / wrongTab.
//
// A structured-output schema is a GRAMMAR. The model was not discouraged from emitting those keys,
// it was UNABLE to. So every "📜 Read my Chronicle" returned found:[] — and the board's panel,
// correctly refusing to invent anything from an empty read, reported it as a clean
// "Nothing to register". A read that cannot succeed, reporting success.

const SRC = fs.readFileSync(path.resolve(__dirname, '..', 'functions', 'api', 'intake.js'), 'utf8');

test.describe('v1558 — a read that cannot succeed must not report success', () => {
  test('★ the chronicle kinds get their OWN schema in the output_config chain', async () => {
    const chain = (SRC.match(/schema: isLocate[^\n]*/) || [''])[0];
    expect(chain, 'a chronicle read fell through to itemsSchema').toContain('isChron ? chronSchema');
    expect(SRC).toContain('const chronSchema');
  });

  test('★ the schema can express every key the handler READS', async () => {
    // the contract is: whatever the handler reaches for, the grammar must permit
    const schema = (SRC.match(/const chronSchema = \{[\s\S]*?\n  \};/) || [''])[0];
    expect(schema).toBeTruthy();
    for (const key of ['found', 'notFound', 'sets', 'printedFound', 'printedTotal',
                       'stateVisible', 'wrongTab', 'conf']) {
      expect(schema, 'the handler reads parsed.' + key + ' — the grammar must allow it')
        .toContain(key + ':');
    }
  });

  test('★ the sets rows carry set / pieces / complete', async () => {
    const schema = (SRC.match(/const chronSchema = \{[\s\S]*?\n  \};/) || [''])[0];
    expect(schema).toContain('set:');
    expect(schema).toContain('pieces:');
    expect(schema, 'v1530 expands a COMPLETE set into its pieces — it needs the flag')
      .toContain('complete:');
  });

  test('every OTHER kind still routes to the schema it always did', async () => {
    const chain = (SRC.match(/schema: isLocate[^\n]*/) || [''])[0];
    for (const [flag, sch] of [['isLocate', 'locateSchema'], ['isRaw', 'rawSchema'],
      ['isSock', 'sockSchema'], ['isGridCount', 'gridCountSchema'], ['isTally', 'tallySchema']]) {
      expect(chain, flag + ' must still reach ' + sch).toContain(flag + ' ? ' + sch);
    }
    expect(chain.trim().endsWith('itemsSchema } },')
      || chain.includes(': itemsSchema'), 'the default is unchanged').toBe(true);
  });

  test('★ chronicle is branched BEFORE tally — the two share no keys', async () => {
    // isTally is a broad flag; putting chronicle after it would let a chronicle read be graded by
    // the rune-tally grammar, which is the same class of silent failure one door along
    const chain = (SRC.match(/schema: isLocate[^\n]*/) || [''])[0];
    expect(chain.indexOf('isChron')).toBeLessThan(chain.indexOf('isTally ?'));
  });

  test('the schema is closed — no invented keys', async () => {
    const schema = (SRC.match(/const chronSchema = \{[\s\S]*?\n  \};/) || [''])[0];
    expect(schema).toContain('additionalProperties: false');
    expect(schema, 'found is the one thing a chronicle read must always return')
      .toContain("required: ['found']");
  });
});
