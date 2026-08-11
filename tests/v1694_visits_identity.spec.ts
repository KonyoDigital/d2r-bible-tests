// v1694 — THE PROOF that the identity beacon (bible.html) actually reaches the dashboard
// (functions/visits.js), without ever being able to hurt the board it beacons from.
//
// His ask: "maybe for the visits i saw for the console ... more data to it, how many times each
// time my cuzin or me or anyone is on." The finding this ship exists for: functions/visits.js can
// see every browser page-view but not WHO (IP-inferred only); functions/api/console.js has real
// identity but only ever hears from the TV DIABLO app, never a browser. bible.html's new beacon
// (POST /api/hello) is supposed to join the two — but "supposed to" is not "does".
//
// THE JOIN IS PROVEN WITH THE REAL PAYLOAD, NOT AN INVENTED ONE. T4 loads bible.html in a real
// browser over http, captures the EXACT bytes its beacon posted, and feeds those bytes into the
// real functions/api/hello.js writer, whose output is then read by the real functions/visits.js
// renderer. No hand-rolled record anywhere in the chain — so a world where the board ships an
// empty `code` (hello.js:71-73 derives identity from `code || name` and writes NOTHING when both
// are empty) fails HERE, loudly, instead of shipping a dead feature with green tests.
//
// The rest: the beacon cannot regress the live board (T1a 500, T1b reset, T1c not in the critical
// path, T1d interactive while the request hangs), fires exactly once per load (T2), and carries
// identity only — no ledger data (T3). T4b proves the honest empty state, by asserting the literal
// sentence visits.js renders when nothing has beaconed.
import { test, expect } from '@playwright/test';
import * as http from 'http';
import type { AddressInfo } from 'net';
import * as fs from 'fs';
import * as path from 'path';

const REPO = path.resolve(__dirname, '..');
const BIBLE_HTML = fs.readFileSync(path.join(REPO, 'bible.html'), 'utf8');
const HELLO_FN = path.join(REPO, 'functions', 'api', 'hello.js');
const VISITS_FN = path.join(REPO, 'functions', 'visits.js');

// The literal empty state functions/visits.js renders when NOTHING has beaconed. Asserted both
// ways: present in T4b (zero beacons) and absent in T4 (one real beacon), so neither direction can
// pass by accident.
const EMPTY_STATE = 'No beaconed visitor identity yet';

type HelloMode = 'ok' | '500' | 'reset' | 'hang';

interface Srv { server: http.Server; port: number; hits: string[]; }

// A real HTTP server (not page.route) because bible.html's beacon deliberately no-ops on
// `location.protocol === 'file:'` — "automation / local file copies never beacon" is the guard
// line in bible.html itself. Testing it honestly means testing it over http, the way the live
// board actually runs.
function startServer(mode: HelloMode): Promise<Srv> {
  const hits: string[] = [];
  const server = http.createServer((req, res) => {
    if (req.url === '/api/hello') {
      let body = '';
      req.on('data', (c) => { body += c; });
      req.on('end', () => {
        hits.push(body);
        if (mode === '500') {
          res.writeHead(500, { 'content-type': 'application/json' });
          res.end('{"ok":false}');
        } else if (mode === 'reset') {
          req.socket.destroy();                       // hard reset -> a real network error client-side
        } else if (mode === 'hang') {
          // never respond — simulates unreachable/aborted
        } else {
          res.writeHead(200, { 'content-type': 'application/json' });
          res.end('{"ok":true}');
        }
      });
      return;
    }
    if (req.url === '/' || req.url === '/index.html') {
      res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      res.end(BIBLE_HTML);
      return;
    }
    // every other same-origin request (art/, /api/status, etc.) — 404 fast, never hang the page.
    res.writeHead(404, { 'content-type': 'text/plain' });
    res.end('nf');
  });
  return new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address() as AddressInfo;
      resolve({ server, port, hits });
    });
  });
}

async function waitFor(cond: () => boolean, timeoutMs = 6000, stepMs = 50): Promise<boolean> {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    if (cond()) return true;
    await new Promise((r) => setTimeout(r, stepMs));
  }
  return cond();
}

interface Sig { tally: string; tabs: number; nodes: number; active: string; }

// A COUNT-BASED render signature, not a boolean "the page looks fine". This is what "renders
// identically to a clean load" is measured as: same grail tally text, same number of tabs, same
// total element count, same active tab. A beacon that painted anything, removed anything or threw
// mid-render moves one of these numbers.
async function signature(page: any): Promise<Sig> {
  return page.evaluate(() => {
    const peek = document.getElementById('grail-peek');
    const act = document.querySelector('.tab.active') as HTMLElement | null;
    return {
      tally: peek ? (peek.textContent || '').trim() : '<<#grail-peek missing>>',
      tabs: document.querySelectorAll('.tab[data-tab]').length,
      nodes: document.querySelectorAll('*').length,
      active: act ? (act.getAttribute('data-tab') || '') : '',
    };
  });
}

// The clean-load baseline every "cannot hurt the page" test compares against: the same build,
// served the same way, with a /api/hello that answers 200 immediately. Cached per worker.
let BASELINE: Sig | null = null;
async function baseline(page: any): Promise<Sig> {
  if (BASELINE) return BASELINE;
  const { server, port } = await startServer('ok');
  try {
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load' });
    await page.waitForTimeout(500);
    const sig = await signature(page);
    expect(sig.tally.length, 'baseline sanity: #grail-peek must render text, or every comparison below is vacuous').toBeGreaterThan(0);
    expect(sig.tabs, 'baseline sanity: the tab strip must exist').toBeGreaterThan(5);
    expect(sig.nodes, 'baseline sanity: the board must actually render a DOM').toBeGreaterThan(500);
    BASELINE = sig;
    return sig;
  } finally {
    server.close();
  }
}

// ── same loadFn/StubKV shape as v1596_console_page_render.spec.ts: evaluate the real Pages
// Function source (stripped of `export`, since this repo's package.json has no "type":"module")
// against an in-memory KV, so the assertions below run the ACTUAL server code, not a restatement
// of it. ──
function loadFn(file: string, name: string): any {
  const src = fs.readFileSync(file, 'utf8');
  if (/^\s*import\s+[^(]/m.test(src)) {
    throw new Error(`${file} now has top-level imports — this loader must become a real ESM import`);
  }
  const body = src
    .replace(/^export\s+default\s+/gm, '')
    .replace(/^export\s*\{[^}]*\}\s*;?\s*$/gm, '')
    .replace(/^export\s+(?=(async\s+)?function|const\b|let\b|var\b|class\b)/gm, '');
  // eslint-disable-next-line no-new-func
  return new Function(`${body}\nreturn typeof ${name} === 'function' ? ${name} : null;`)();
}

class StubKV {
  private store = new Map<string, string>();
  put(name: string, value: string) { this.store.set(name, value); }
  async get(name: string, type?: string) {
    const v = this.store.get(name);
    if (v == null) return null;
    return type === 'json' ? JSON.parse(v) : v;
  }
  async list(opts: any = {}) {
    const prefix = opts.prefix || '';
    const all = [...this.store.keys()].filter((k) => k.startsWith(prefix)).sort();
    return { keys: all.map((name) => ({ name })), list_complete: true, cursor: undefined };
  }
}

test.describe('v1694 — the beacon cannot hurt the page', () => {
  test('T1a: a 500 from /api/hello renders identically to a clean load (same tally/tabs/nodes, 0 errors, 1 attempt)', async ({ page }) => {
    const base = await baseline(page);
    const { server, port, hits } = await startServer('500');
    try {
      const errors: string[] = [];
      page.on('pageerror', (e) => errors.push(e.message));
      await page.addInitScript(() => {
        (window as any).__rej = [];
        window.addEventListener('unhandledrejection', (e: any) => (window as any).__rej.push(String(e.reason)));
      });
      await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load' });

      const fired = await waitFor(() => hits.length >= 1);
      expect(fired, `beacon never reached the 500 server — hits=${hits.length}`).toBe(true);
      expect(hits.length, 'must attempt exactly once even though the server 500s').toBe(1);
      await page.waitForTimeout(500);   // give a badly-behaved error path time to touch the DOM

      const sig = await signature(page);
      expect(sig.tally, `the grail tally read "${sig.tally}" with a 500 beacon vs "${base.tally}" on a clean load`).toBe(base.tally);
      expect(sig.tabs, 'tab count changed under a failing beacon').toBe(base.tabs);
      expect(sig.nodes, `element count changed under a failing beacon: ${sig.nodes} vs baseline ${base.nodes}`).toBe(base.nodes);
      expect(sig.active, 'the active tab changed under a failing beacon').toBe(base.active);

      const rej = await page.evaluate(() => (window as any).__rej || []);
      expect(rej, 'unhandled rejection surfaced from a 500 beacon response').toEqual([]);
      expect(errors, 'page error surfaced from a 500 beacon response').toEqual([]);
    } finally {
      server.close();
    }
  });

  test('T1b: a reset connection renders identically to a clean load and raises no unhandled rejection', async ({ page }) => {
    const base = await baseline(page);
    const { server, port, hits } = await startServer('reset');
    try {
      const errors: string[] = [];
      page.on('pageerror', (e) => errors.push(e.message));
      await page.addInitScript(() => {
        (window as any).__rej = [];
        window.addEventListener('unhandledrejection', (e: any) => (window as any).__rej.push(String(e.reason)));
      });
      await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load' });

      const attempted = await waitFor(() => hits.length >= 1);
      expect(attempted, `beacon never attempted against the reset server — hits=${hits.length}`).toBe(true);
      await page.waitForTimeout(500);   // the TypeError from a killed socket lands asynchronously

      const sig = await signature(page);
      expect(sig.tally, `the grail tally read "${sig.tally}" with a reset beacon vs "${base.tally}" on a clean load`).toBe(base.tally);
      expect(sig.tabs, 'tab count changed under a reset connection').toBe(base.tabs);
      expect(sig.nodes, `element count changed under a reset connection: ${sig.nodes} vs baseline ${base.nodes}`).toBe(base.nodes);

      // RED-PROVED by deleting the beacon's `.catch(function(){})` in bible.html: this array then
      // fills with "TypeError: Failed to fetch" and the assertion fails on real content. The catch
      // is the only thing standing between a dropped connection and a rejection he would see.
      const rej = await page.evaluate(() => (window as any).__rej || []);
      expect(rej, 'unhandled rejection from a reset connection — the beacon lost its .catch()').toEqual([]);
      expect(errors, 'page error from a reset connection').toEqual([]);
    } finally {
      server.close();
    }
  });

  test('T1c: the beacon is NOT in the critical path — it starts after the load event, measured in ms', async ({ page }) => {
    const { server, port, hits } = await startServer('ok');
    try {
      await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load' });
      await waitFor(() => hits.length >= 1);

      // PerformanceResourceTiming is the only honest measurement here: a pending fetch() never
      // delays the load event, so "the page loaded fast" proves nothing. What CAN be wrong is the
      // beacon being issued during the critical path — this compares the two clocks directly.
      const t: any = await page.evaluate(async () => {
        const deadline = Date.now() + 6000;
        while (Date.now() < deadline) {
          const e: any = performance.getEntriesByType('resource').find((r: any) => r.name.indexOf('/api/hello') >= 0);
          const nav: any = performance.getEntriesByType('navigation')[0];
          if (e && nav && nav.loadEventEnd > 0) return { start: e.startTime, load: nav.loadEventEnd, dcl: nav.domContentLoadedEventEnd };
          await new Promise((r) => setTimeout(r, 50));
        }
        return null;
      });
      expect(t, 'no PerformanceResourceTiming entry for /api/hello — the beacon request was never observable from the page').not.toBeNull();
      expect(t.load, 'sanity: loadEventEnd must be a real positive timestamp or the comparison below is meaningless').toBeGreaterThan(0);
      // RED-PROVED by replacing `requestIdleCallback(beacon,{timeout:4000})` with a bare
      // `beacon()`: the start dropped to 396ms against a loadEventEnd of 477ms and this failed
      // with both real numbers printed.
      expect(t.start, `the beacon started at ${Math.round(t.start)}ms but the page's load event only finished at ${Math.round(t.load)}ms (DCL ${Math.round(t.dcl)}ms) — it is inside the critical path`).toBeGreaterThanOrEqual(t.load);
      expect(hits.length, 'exactly one attempt').toBe(1);
    } finally {
      server.close();
    }
  });

  test('T1d: while a hung /api/hello is still in flight, the board is fully interactive', async ({ page }) => {
    const base = await baseline(page);
    const { server, port, hits } = await startServer('hang');
    try {
      await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load' });
      const attempted = await waitFor(() => hits.length >= 1, 8000);
      expect(attempted, 'the beacon was expected to attempt against the hung server (it just never gets a response)').toBe(true);

      // The request is now open and will NEVER be answered. Everything below happens with it
      // pending — which is exactly the state a dead /api/hello leaves his board in.
      expect(await page.evaluate(() => document.readyState), 'document never reached "complete" with the beacon pending').toBe('complete');

      const target = await page.locator('.tab[data-tab]').nth(2).getAttribute('data-tab');
      // the click is allowed to FAIL — what must not happen is the board silently refusing to
      // switch. Swallowing the click error keeps the failure surfacing as the assertion below,
      // with the tab names printed, instead of as a bare locator timeout.
      let clickErr = '';
      try { await page.locator('.tab[data-tab]').nth(2).click({ timeout: 3000 }); }
      catch (e: any) { clickErr = String(e && e.message).split('\n')[0]; }
      const after = await page.evaluate(() => ({
        active: (document.querySelector('.tab.active') as HTMLElement | null)?.getAttribute('data-tab') || '',
        activeCount: document.querySelectorAll('.tab.active').length,
      }));
      expect(after.activeCount, 'exactly one tab must be active after a click with the beacon pending').toBe(1);
      expect(after.active, `clicking the "${target}" tab did not switch to it while the beacon hangs — active tab is still "${after.active}"${clickErr ? ` (the click itself failed: ${clickErr})` : ''}`).toBe(target);

      const sig = await signature(page);
      expect(sig.tally, `the grail tally read "${sig.tally}" with a hung beacon vs "${base.tally}" on a clean load`).toBe(base.tally);
      expect(sig.tabs, 'tab count changed under a hung beacon').toBe(base.tabs);
      expect(hits.length, 'a hung request must not be retried').toBe(1);
    } finally {
      server.close();
    }
  });
});

test('T2: the beacon fires exactly once per page-load — not on tab clicks, exactly once again on reload', async ({ page }) => {
  const { server, port, hits } = await startServer('ok');
  try {
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load' });
    const first = await waitFor(() => hits.length >= 1);
    expect(first, `beacon never fired on first load — hits=${hits.length}`).toBe(true);
    expect(hits.length, 'first load must beacon exactly once').toBe(1);

    const tabs = await page.locator('.tab[data-tab]').all();
    for (const t of tabs.slice(0, 6)) {
      try { await t.click({ timeout: 1000 }); } catch (e) { /* some tabs may be hidden/disabled — irrelevant here */ }
    }
    await page.waitForTimeout(1000);
    expect(hits.length, `tab clicks re-fired the beacon — hits=${hits.length}`).toBe(1);

    const before = hits.length;
    await page.reload({ waitUntil: 'load' });
    const again = await waitFor(() => hits.length >= before + 1);
    expect(again, 'reload never re-beaconed').toBe(true);
    expect(hits.length, 'a reload is a NEW page-load — it must beacon exactly once more, not zero, not twice').toBe(before + 1);
  } finally {
    server.close();
  }
});

test('T3: the beacon payload is identity only — id/name/code/machine, no ledger data', async ({ page }) => {
  const { server, port, hits } = await startServer('ok');
  try {
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load' });
    const fired = await waitFor(() => hits.length >= 1);
    expect(fired, `beacon never fired — hits=${hits.length}`).toBe(true);

    const raw = hits[0] || '';
    let body: any = {};
    try { body = JSON.parse(raw); } catch (e) { /* leave {} so the assertions below fail loudly */ }

    const clientIdentity = await page.evaluate(() => ({
      id: (window as any)._D2R_INSTALL || '',
      machine: (window as any).D2R_MACHINE || '',
      ver: ((window as any).D2R_BUILD && (window as any).D2R_BUILD.id) || '',
    }));
    expect(body.id, 'beaconed id must be the SAME stable identity the crest already paints from — no second id minted').toBe(clientIdentity.id);
    expect(body.id, 'sanity: the identity must be non-empty').not.toBe('');
    expect(body.machine).toBe(clientIdentity.machine);
    expect(typeof body.name).toBe('string');
    expect(typeof body.code).toBe('string');

    // `ver` is the build stamp hello.js already reads (body.ver) — identity/provenance, not ledger.
    // Asserted as an EXACT key set, so any future field has to come past this line deliberately.
    expect(body.ver, 'the beaconed build stamp must be the page\'s own D2R_BUILD.id, not a second version string').toBe(clientIdentity.ver);
    expect(body.ver, 'sanity: the build stamp must be non-empty or the dashboard cannot tell a stale cached build from a fresh one').not.toBe('');
    expect(Object.keys(body).sort(), 'payload must carry ONLY id/name/code/machine/ver').toEqual(['code', 'id', 'machine', 'name', 'ver']);

    for (const banned of ['foundLog', 'wishlist', 'runeStash', 'grailProgress', 'itemName', 'ownedItems', '"owned"']) {
      expect(raw.includes(banned), `payload leaked ledger data: "${banned}"`).toBe(false);
    }
  } finally {
    server.close();
  }
});

test.describe('v1694 — the dashboard keeps the two populations separate', () => {
  const SECRET = 'test-visits-key-1694';

  async function writeHello(kv: StubKV, body: any) {
    const onRequestPost = loadFn(HELLO_FN, 'onRequestPost');
    expect(onRequestPost, 'functions/api/hello.js must export onRequestPost').toBeTruthy();
    const req = { text: async () => JSON.stringify(body), cf: { country: 'US', city: 'Monroe' } };
    return onRequestPost({ request: req, env: { TZ_HISTORY: kv } });
  }

  async function renderVisits(kv: StubKV) {
    const onRequestGet = loadFn(VISITS_FN, 'onRequestGet');
    expect(onRequestGet, 'functions/visits.js must export onRequestGet').toBeTruthy();
    const res: any = await onRequestGet({
      request: { url: `https://bull-4-u.com/visits?k=${SECRET}` },
      env: { VISITS_KEY: SECRET, TZ_HISTORY: kv },
    });
    return res.text() as Promise<string>;
  }

  // ⚠ ANCHORED ON THE <h2>, NOT ON THE WORDS. The page's intro paragraph mentions "Named visitors"
  // long before the table exists, so a bare /Named visitors/ match grabs the intro prose plus the
  // console-machines table — i.e. it would be judging the wrong DOM region. Caught by a red-prove:
  // the failure message printed the intro sentence, not the table.
  function sections(html: string) {
    const namedSection = (html.match(/<h2>Named visitors[\s\S]*?(?=<h2>Who)/) || [''])[0];
    const whoSection = (html.match(/<h2>Who[\s\S]*?(?=<h2>Raw log)/) || [''])[0];
    expect(namedSection.startsWith('<h2>Named visitors'), 'instrument check: the Named-visitors section must be sliced from its own heading').toBe(true);
    expect(whoSection.startsWith('<h2>Who'), 'instrument check: the Who section must be sliced from its own heading').toBe(true);
    return { namedSection, whoSection };
  }

  function fakeVisit(kv: StubKV, iso: string, user: string, ip: string) {
    kv.put('visit:' + iso + ':' + Math.random().toString(36).slice(2), JSON.stringify({
      t: iso, user, ip, ua: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) AppleWebKit/605 Safari/605',
      country: 'US', city: 'Monroe',
    }));
  }

  test('T4: the REAL browser payload survives hello.js and renders in Named visitors; the IP-inferred table still shows everyone', async ({ page }) => {
    // ── end 1: capture the exact bytes the real board beacons ────────────────────────────────
    const { server, port, hits } = await startServer('ok');
    let realPayload: any = null;
    let realRaw = '';
    try {
      await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load' });
      const fired = await waitFor(() => hits.length >= 1);
      expect(fired, `the board never beaconed — there is no real payload to join with (hits=${hits.length})`).toBe(true);
      realRaw = hits[0];
      realPayload = JSON.parse(realRaw);
    } finally {
      server.close();
    }

    const kv = new StubKV();
    const now = new Date().toISOString();

    // three real page-views — the IP-inferred population, which must exist with or without ANY beacon
    fakeVisit(kv, now, 'konyo', '1.1.1.1');
    fakeVisit(kv, now, '', '2.2.2.2');           // no login name typed -> falls back to IP
    fakeVisit(kv, now, 'cuz', '3.3.3.3');

    // ── end 2: the SAME bytes through the real writer. Nothing invented. If bible.html ever ships
    // an empty `code` AND an empty `name`, hello.js writes nothing at all (its `if (!label)` early
    // return) and this test fails right here rather than letting a dead feature ship green. ──
    const postRes: any = await writeHello(kv, realPayload);
    const postJson = await postRes.json();
    expect(postJson.ok, `the real /api/hello writer rejected the board's own payload: ${realRaw}`).toBe(true);
    expect(postJson.skipped, `hello.js SKIPPED the board's own beacon ("${postJson.skipped}") — the payload carries no identity it will store, so nothing would ever appear on the dashboard. Payload: ${realRaw}`).toBeUndefined();

    // ⚠ NAMED, NOT ASSUMED: hello.js:71-73 DISCARDS body.id (the durable install id) and keys the
    // record on the slugified `code || name` instead. This is pinned deliberately so the choice is
    // visible in the test file rather than silently true — a 4-hex sigil code is a 16-bit space,
    // so two installs CAN collide onto one row. That is a hello.js design question, not a spec bug.
    const expectedId = String(realPayload.code || realPayload.name).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    expect(expectedId.length, 'the board beaconed neither a code nor a name — hello.js would store nothing').toBeGreaterThan(0);
    expect(postJson.id, 'hello.js keys identity on code||name, not on the beaconed install id').toBe(expectedId);
    expect(postJson.count, 'first beacon from this identity must be visit #1').toBe(1);

    const html = await renderVisits(kv);
    const { namedSection, whoSection } = sections(html);
    expect(namedSection.length, 'could not even locate the Named visitors section on the rendered page').toBeGreaterThan(0);
    expect(whoSection.length, 'could not even locate the Who (IP-inferred) section on the rendered page').toBeGreaterThan(0);

    // THE REAL PROOF: the identity the live board actually sends, written by the real writer, read
    // by the real renderer. Real data through the real pipe, at both ends, not a boolean.
    expect(namedSection, `hello.js stored the board's own beacon as id "${expectedId}" but visits.js's Named-visitors section does not render it — the two files disagree on the key prefix or the record schema. Section: ${namedSection.slice(0, 500)}`)
      .toContain(expectedId);
    expect(namedSection, `the board's own sigil code ("${realPayload.code}") never rendered in the Named-visitors section`)
      .toContain(String(realPayload.code));
    expect(namedSection, 'a beacon exists, so the empty state must be GONE').not.toContain(EMPTY_STATE);
    expect(namedSection, 'with exactly one beaconed identity the heading must count it').toContain('1 identity');
    const namedRowCount = (namedSection.match(/<tbody>/g) || []).length;
    expect(namedRowCount, 'the Named-visitors table body never rendered').toBe(1);

    // the IP-inferred population is a DIFFERENT set and must be untouched by the beacon existing
    expect(whoSection, 'IP-inferred visitor "konyo" went missing once a beacon existed').toContain('konyo');
    expect(whoSection, 'IP-inferred visitor "cuz" went missing once a beacon existed').toContain('cuz');
    const whoRows = (whoSection.match(/<tr>/g) || []).length;
    expect(whoRows, `expected at least 3 rows (header + 3 people, or thereabouts) in the IP-inferred table, saw ${whoRows}`).toBeGreaterThanOrEqual(3);

    // THE TWO NUMBERS MUST STAY TWO: 1 beaconed identity vs 3 IP-inferred page-views. If anything
    // ever sums them, the page would show 4 here and both of these fail.
    expect(/Named identities:\s*<b>1<\/b>/.test(namedSection), `the beaconed identity count must read 1 on its own. Section: ${namedSection.slice(-700)}`).toBe(true);
    expect(/IP-inferred page-views:\s*<b>3<\/b>/.test(namedSection), `the IP-inferred page-view total must read 3, stated separately from the beaconed one. Section: ${namedSection.slice(-700)}`).toBe(true);

    // and the page must SAY it in words, not just imply it through layout.
    expect(html.toLowerCase(), 'the page never states in words that the two tables are different populations').toContain('different population');
  });

  test('T4b: with NO beacon at all, Named visitors renders its honest empty state and the Who table is unaffected', async () => {
    const kv = new StubKV();
    const now = new Date().toISOString();
    fakeVisit(kv, now, 'solo', '9.9.9.9');

    const html = await renderVisits(kv);
    const { namedSection, whoSection } = sections(html);
    expect(namedSection.length, 'could not locate the Named visitors section').toBeGreaterThan(0);

    // THE ASSERTION THIS TEST EXISTS FOR — the literal sentence visits.js renders when the
    // hvisitor: prefix is empty. RED-PROVED by rewording that `<div class="empty">` branch to
    // "Nothing to show yet": this failed on the missing string, printing the rendered section —
    // an assertion firing for its own reason, not a crash.
    expect(namedSection, `zero beacons must render the honest empty state "${EMPTY_STATE}". Section: ${namedSection.slice(0, 400)}`)
      .toContain(EMPTY_STATE);
    // ...and it must be an empty state, not a table with nothing in it.
    expect((namedSection.match(/<tbody>/g) || []).length, 'a Named-visitors table body rendered with zero beacons').toBe(0);
    expect(/&middot;\s*\d+\s*identit/.test(namedSection), `the heading claimed an identity count with zero beacons: ${namedSection.slice(0, 200)}`).toBe(false);

    expect(whoSection, 'the lone IP-inferred visitor must still show with zero beacons in play').toContain('solo');
    // must not fabricate a named-visitor row out of nothing
    expect(html, 'a beacon identity appeared with no beacon ever written — fabricated data').not.toContain('cuz-phone');
  });

  // ── v1694 render-gate blocker, pinned ──────────────────────────────────────────────────────
  // Every test above joins the two files on the DURABLE record (`hvisitor:`) and none of them ever
  // looked at the day columns — which are fed by the SEPARATE per-hit log (`hhit:`). So the whole
  // suite went green while hello.js wrote a FOUR-segment key (`hhit:<ISO>:<rand>:<id>`) and
  // visits.js parsed a THREE-segment one: 100% of hits were rejected and every day column read 0
  // or '—'. Half a join can pass a test suite. This test asserts the OTHER half.
  test('T4c: hits written by the REAL hello.js land in the day columns — nothing silently unparsed', async () => {
    const kv = new StubKV();
    const payload = { id: 'x'.repeat(32), name: 'Cousin Dean', code: 'a1b2', machine: 'cuz-pc', ver: 'v1694' };
    // one IP-inferred page-view so the "Who" heading exists — sections() slices the Named block by
    // looking AHEAD to it, and with zero visit: keys that whole section is (correctly) not rendered.
    fakeVisit(kv, new Date().toISOString(), 'dean', '4.4.4.4');

    // three page-loads by the same person, all today
    for (let i = 0; i < 3; i++) {
      const res: any = await writeHello(kv, payload);
      const j = await res.json();
      expect(j.ok, 'the real writer refused a well-formed beacon').toBe(true);
    }

    // INSTRUMENT CHECK FIRST: the writer really did produce hit keys. If this is 0, the test below
    // would "pass" for the wrong reason on a reader that reads nothing at all.
    const hitKeys = [...(kv as any).store.keys()].filter((k: string) => k.startsWith('hhit:'));
    expect(hitKeys.length, `hello.js wrote no hhit: keys at all — there is nothing for the day columns to count. Keys: ${[...(kv as any).store.keys()].join(', ')}`).toBe(3);

    const html = await renderVisits(kv);
    const { namedSection } = sections(html);

    // The page prints its own admission when a key does not parse. Its presence IS the blocker.
    expect(namedSection, `visits.js rejected hit keys that hello.js itself wrote — the two files disagree on the "hhit:" key shape. Keys written: ${hitKeys.join(' | ')}`)
      .not.toContain('did not match');

    const body = (namedSection.match(/<tbody>([\s\S]*?)<\/tbody>/) || ['', ''])[1];
    expect(body.length, 'the Named-visitors table body never rendered').toBeGreaterThan(0);
    const num = [...body.matchAll(/<td class="num">([\s\S]*?)<\/td>/g)].map((m) => m[1].trim());
    expect(num.length, `expected 4 numeric cells (visits, days-active, 7d, 30d) on the single row, saw ${num.length}: ${JSON.stringify(num)}`).toBe(4);

    expect(num[1], `DAYS ACTIVE (30d) rendered "${num[1]}" — three hits on one day must be 1 day, never an em-dash`).toBe('1');
    expect(num[2], `LAST 7D rendered "${num[2]}" — three beacons written by hello.js minutes ago must count 3`).toBe('3');
    expect(num[3], `LAST 30D rendered "${num[3]}" — three beacons written by hello.js minutes ago must count 3`).toBe('3');
  });

  // v1694 copy fix: the two headings were styled identically and the "different populations"
  // warning was small grey prose UNDER each table, so a skimmer could add the two totals. Each
  // heading now carries its own badge naming its population and saying it is never added.
  test('T4d: each people-table heading carries its own population badge', async () => {
    const kv = new StubKV();
    await writeHello(kv, { id: 'y'.repeat(32), name: 'Konyo', code: 'c0de', machine: 'mac', ver: 'v1694' });
    fakeVisit(kv, new Date().toISOString(), 'konyo', '1.1.1.1');

    const html = await renderVisits(kv);
    const { namedSection, whoSection } = sections(html);
    const namedHead = (namedSection.match(/<h2>[\s\S]*?<\/h2>/) || [''])[0];
    const whoHead = (whoSection.match(/<h2>[\s\S]*?<\/h2>/) || [''])[0];

    expect(namedHead, 'the Named-visitors heading carries no population badge').toContain('class="pop beacon"');
    expect(namedHead, 'the beacon badge does not name its population').toContain('POPULATION A');
    expect(namedHead, 'the beacon badge does not say the two totals are never added').toContain('never added to population B');
    expect(namedHead, 'the beacon badge must state the beaconed visit total on the heading itself').toMatch(/1 beaconed visit\b/);

    expect(whoHead, 'the IP-inferred heading carries no population badge').toContain('class="pop ipinf"');
    expect(whoHead, 'the IP-inferred badge does not name its population').toContain('POPULATION B');
    expect(whoHead, 'the IP-inferred badge does not say the two totals are never added').toContain('never added to population A');

    // and the two badges must be VISUALLY distinct, not just differently worded
    expect(html, 'the two population badges share one style — the whole point is that they look different').toContain('.pop.ipinf{');
  });
});
