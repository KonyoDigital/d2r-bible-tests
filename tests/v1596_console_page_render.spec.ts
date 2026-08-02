import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1596 — 🖥 LOOK AT /console THE WAY A HUMAN WOULD.
//
// Konyo: "are you sure the console tracker is working? … my cousin in the states used it as recently
// as yesterday and i DONT SEE IT and also my windows PC i dont see it here logged."
//
// He was right, and the reason was never that the machines were silent. functions/console.js listed
// the event log with `kv.list({ prefix: 'consolelog:', limit: 400 })`. Cloudflare KV returns keys in
// LEXICOGRAPHIC ASCENDING order and the keys are `consolelog:<ISO-ts>:<machine>`, so a bare `limit`
// returns the OLDEST 400 events, not the newest. Past 400 events inside the 30-day TTL, every
// RECENT machine falls off the end of the window and becomes invisible — exactly his cousin, exactly
// his Windows PC. Presence keys (`console:<machine>`, 600s TTL) cover only the last ten minutes, so
// once a box has been off for eleven minutes the event log is the ONLY thing that can still name it.
//
// The seed below reproduces that precisely: 600 log events, of which the NEWEST 200 belong to
// `cousin-pc` and `windows-pc`. Under the old oldest-first window those two paint NOWHERE on the
// page, and the assertions here go red. That is the point — this spec is the user-facing form of the
// bug, not a restatement of the patch.
//
// It is also deliberately a RENDER test rather than a DOM test. A row can exist in the markup and
// still be invisible to a human: zero-height, off-screen, clipped, or the same colour as the surface
// under it. Everything below measures painted geometry and computed colour, and it ends by writing a
// screenshot a person can actually open — a gate whose evidence nobody can inspect is a gate you
// have to take on faith.

const ORIGIN = 'https://bull-4-u.com/console';
const SECRET = 'test-visits-key';
// V1596_CONSOLE_FN lets this exact spec be pointed at the PRE-FIX console.js to prove it goes red
// there — `git show <sha>:functions/console.js > /tmp/old.js` then run with the env var set. A test
// that has never been shown failing is a test nobody has proved measures anything.
const FN = process.env.V1596_CONSOLE_FN || path.resolve(__dirname, '..', 'functions', 'console.js');
const SHOT_DIR = path.resolve(__dirname, '..', 'test-results');
const SHOT = path.join(SHOT_DIR, 'v1596-console-page.png');

/* ─────────────────────────────── loading the worker ───────────────────────────────
 * functions/console.js is an ES module, but this repo's package.json has no `"type":
 * "module"`, so Node's loader would read that `.js` as CommonJS and throw on the bare
 * `export` keyword. Rather than restructure deployed code to suit a test, strip the
 * top-level export markers and evaluate the source. If the file ever grows a real
 * `import`, this throws with a readable message instead of a mystery ReferenceError. */
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

/* ─────────────────────────────── the KV stub ───────────────────────────────
 * Same shape as the fixture in tv/test_console_fleet.py: an in-memory Map that lists keys
 * LEXICOGRAPHIC ASCENDING and honours `limit` + `cursor`. The ordering is the whole subject of
 * this spec, so it is modelled honestly rather than conveniently — and because it paginates, code
 * that walks the full cursor passes here under BOTH orderings while code that trusts a bare
 * `limit` does not. */
class StubKV {
  private store = new Map<string, any>();
  public listCalls: Array<{ prefix: string; limit?: number; cursor?: string }> = [];

  put(name: string, value: any) { this.store.set(name, value); }

  /** KV is allowed to return FEWER keys than `limit` and signal more with list_complete:false —
   *  correct code follows the cursor instead of trusting one page. This stub caps a page at 250 to
   *  model that, which is what makes the pagination test below discriminate: cursor-following code
   *  makes three calls for a 600-key prefix, bare-`limit` code makes one and sees a third of it. */
  async list(opts: any = {}) {
    const prefix = opts.prefix || '';
    const limit = Math.min(typeof opts.limit === 'number' ? opts.limit : 1000, 250);
    this.listCalls.push({ prefix, limit: opts.limit, cursor: opts.cursor });
    const all = [...this.store.keys()].filter((k) => k.startsWith(prefix)).sort();
    const start = opts.cursor ? Number(opts.cursor) : 0;
    const page = all.slice(start, start + limit);
    const end = start + page.length;
    const complete = end >= all.length;
    return {
      keys: page.map((name) => ({ name })),
      list_complete: complete,
      cursor: complete ? undefined : String(end),
    };
  }

  async get(name: string, type?: string) {
    const v = this.store.get(name);
    if (v === undefined) return null;
    return type === 'json' ? JSON.parse(JSON.stringify(v)) : JSON.stringify(v);
  }
}

const NOW = Date.UTC(2026, 7, 2, 12, 0, 0);          // 2026-08-02T12:00:00Z, fixed so ISO keys sort
const iso = (ms: number) => new Date(ms).toISOString();

function seed(): StubKV {
  const kv = new StubKV();

  // ONE machine online right now — the only thing the presence window can still see.
  kv.put('console:mac', {
    machine: 'mac', user: 'konyo', platform: 'Darwin', ver: 'v1596',
    mode: 'live', reads: 41, country: 'IL', city: 'Jerusalem', t: iso(NOW - 60_000),
  });

  // Two machines that are OFF and therefore have no presence key at all. Konyo's cousin ran the
  // console yesterday; his Windows PC two days ago and its beacon has been FAILING the whole time.
  kv.put('lastseen:cousin-pc', {
    machine: 'cousin-pc', user: 'elran', platform: 'Windows', ver: 'v1588',
    mode: 'idle', country: 'US', city: 'Fair Lawn', t: iso(NOW - 26 * 3600_000),
    lastBeacon: { ok: true, t: iso(NOW - 26 * 3600_000) },
  });
  kv.put('lastseen:windows-pc', {
    machine: 'windows-pc', user: 'konyo', platform: 'Windows', ver: 'v1501',
    mode: 'idle', country: 'IL', city: 'Tel Aviv', t: iso(NOW - 50 * 3600_000),
    lastBeacon: { ok: false, err: 'timeout', t: iso(NOW - 50 * 3600_000) },
  });

  // 600 events. The OLDEST 400 belong to a retired box; the NEWEST 200 are the two machines above.
  // `limit: 400` with no cursor therefore returns nothing but `old-box`.
  const base = NOW - 600 * 60_000;
  for (let i = 0; i < 600; i += 1) {
    const t = iso(base + i * 60_000);
    const machine = i < 400 ? 'old-box' : (i % 2 === 0 ? 'cousin-pc' : 'windows-pc');
    kv.put(`consolelog:${t}:${machine}`, {
      machine, t, event: i % 3 === 0 ? 'boot' : (i % 3 === 1 ? 'onair' : 'off'),
      platform: machine === 'old-box' ? 'Darwin' : 'Windows',
      ver: machine === 'old-box' ? 'v1102' : 'v1588',
      mode: i % 3 === 1 ? 'live' : 'idle',
    });
  }
  return kv;
}

/** Render the Cloudflare Function straight into the page — no dev server, no network, no origin. */
async function renderConsole(page: any): Promise<string> {
  const onRequestGet = loadFn(FN, 'onRequestGet');
  expect(onRequestGet, 'functions/console.js must export onRequestGet').toBeTruthy();

  const kv = seed();
  const res = await onRequestGet({
    request: { url: `${ORIGIN}?k=${SECRET}` },
    env: { VISITS_KEY: SECRET, TZ_HISTORY: kv },
  });
  expect(res.status, 'the correct key must not 404').toBe(200);
  const html = await res.text();

  /* ⚠️ THE FONT TRAP — LEARNED THE HARD WAY, DO NOT "SIMPLIFY" THIS ROUTE HANDLER.
   * page.screenshot() WAITS ON FONT LOADING. If a route handler abort()s a request the page is
   * waiting on, that request NEVER resolves: the capture hangs for the FULL test timeout and
   * produces NO FILE AT ALL — a hang that reads like a slow machine, not like a bug. So every
   * non-API request is FULFILLED with an empty 200 rather than aborted. Same reason
   * `animations: 'disabled'` is mandatory below: this repo now carries infinite CSS animations,
   * and a fullPage capture can wait on them forever. */
  await page.route('**/*', (r: any) => {
    const u = new URL(r.request().url());
    if (u.pathname.startsWith('/api/')) {
      return r.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    }
    return r.fulfill({ status: 200, contentType: 'text/plain', body: '' });
  });

  await page.setContent(html, { waitUntil: 'load' });
  return html;
}

/** Painted box of a locator — fails loudly rather than returning a silent null. */
async function box(loc: any, what: string) {
  const b = await loc.boundingBox();
  expect(b, `${what} must have a painted box (it rendered with none)`).toBeTruthy();
  return b as { x: number; y: number; width: number; height: number };
}

test.describe('v1596 — the console page, as a human sees it', () => {
  test.beforeAll(() => { fs.mkdirSync(SHOT_DIR, { recursive: true }); });

  test('★ the scope banner says what this tracks AND where browser visits live', async ({ page }) => {
    // Konyo has two trackers and they answer different questions: /console is the TV-D console APP,
    // /visits is browser page-views of the site. The console app never appears in /visits BY DESIGN.
    // If neither page says so, "I don't see it here" is the only possible conclusion — so the scope
    // line is load-bearing, and it has to be VISIBLE, not merely present in the markup.
    await renderConsole(page);
    const banner = await page.evaluate(() => {
      const all = Array.from(document.body.querySelectorAll<HTMLElement>('*'));
      const holders = all.filter((e) => (e.textContent || '').includes('/visits'));
      let el = holders.length ? holders[holders.length - 1] : null;   // smallest holder
      for (let i = 0; el && i < 6; i += 1) {
        if (/console app|console APP/i.test(el.textContent || '')) break;
        el = el.parentElement;
      }
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      return {
        text: (el.textContent || '').replace(/\s+/g, ' ').trim(),
        w: r.width, h: r.height,
        shown: cs.display !== 'none' && cs.visibility !== 'hidden' && Number(cs.opacity) > 0,
      };
    });
    expect(banner, 'no scope banner mentioning /visits was rendered at all').toBeTruthy();
    expect(banner!.shown, 'the scope banner must actually be shown').toBe(true);
    expect(banner!.w, 'the scope banner must have width').toBeGreaterThan(0);
    expect(banner!.h, 'the scope banner must have height').toBeGreaterThan(0);
    expect(banner!.text, 'it must say this page tracks the CONSOLE APP').toMatch(/console app/i);
    expect(banner!.text, 'and it must point browser page-views at /visits').toMatch(/\/visits/);
    expect(banner!.text, 'and say plainly that browser visits are NOT here')
      .toMatch(/visit|page.?view|browser/i);
  });

  test('★ cousin-pc and windows-pc BOTH PAINT — the bug, in the form he reported it', async ({ page }) => {
    // Under `kv.list({ prefix: 'consolelog:', limit: 400 })` these two are inside the 30-day TTL,
    // have written 200 events between them, and appear NOWHERE on the page: the window returned the
    // oldest 400 keys, every one of them `old-box`. This is the assertion that goes red before the
    // fix and green after it.
    await renderConsole(page);
    for (const machine of ['cousin-pc', 'windows-pc']) {
      const loc = page.getByText(machine, { exact: false }).first();
      expect(await loc.count(), `${machine} must appear on the page (he ran it recently)`).toBe(1);
      await expect(loc, `${machine} must be VISIBLE, not merely in the DOM`).toBeVisible();
      const b = await box(loc, machine);
      expect(b.width, `${machine} must have painted width`).toBeGreaterThan(0);
      expect(b.height, `${machine} must have painted height`).toBeGreaterThan(0);
    }
    // …and the widened window must be spent on the NEWEST end. The page caps its printed event list
    // by design, so `old-box` legitimately falls off the bottom; what must never come back is the
    // ordering that made the cap discard the recent end instead. Read straight off the rendered
    // timestamps rather than trusting the sort in the source.
    // Scoped PER TABLE: the three layers each sort newest-first internally, but a machine online
    // right now and a 30-day-old boot event live in different tables, so a global sort would be
    // comparing across sections and would fail for a reason that is not a bug.
    const outOfOrder = await page.evaluate(() => {
      const bad: string[] = [];
      document.querySelectorAll('table').forEach((tbl, i) => {
        const ts = Array.from(tbl.querySelectorAll<HTMLElement>('[data-t]'))
          .map((e) => e.dataset.t || '');
        for (let j = 1; j < ts.length; j += 1) {
          if (ts[j] > ts[j - 1]) { bad.push(`table#${i} row ${j}: ${ts[j - 1]} then ${ts[j]}`); break; }
        }
      });
      return bad;
    });
    const nStamps = await page.locator('[data-t]').count();
    expect(nStamps, 'timestamps must be rendered machine-readably').toBeGreaterThan(2);
    expect(outOfOrder, `the log must print NEWEST-FIRST — that ordering is the whole fix: ${outOfOrder.join(' | ')}`)
      .toEqual([]);
  });

  test('★ a FAILED beacon renders as an error state, never a blank cell', async ({ page }) => {
    // The honesty defect underneath the whole report: the beacon is fire-and-forget behind a bare
    // `except Exception: pass`, so a machine whose beacon has failed every time for months looks
    // IDENTICAL to a machine that was never turned on. windows-pc carries {ok:false, err:'timeout'}
    // and the page has to SAY that rather than showing an empty column.
    await renderConsole(page);
    const row = page.locator('tr').filter({ hasText: 'windows-pc' }).filter({ hasText: /timeout/i });
    expect(await row.count(), "windows-pc's failed beacon must surface its error text")
      .toBeGreaterThan(0);
    const first = row.first();
    await expect(first).toBeVisible();
    const b = await box(first, 'the windows-pc row');
    expect(b.height, 'the failure row must have height').toBeGreaterThan(0);
    const txt = ((await first.textContent()) || '').replace(/\s+/g, ' ').trim();
    expect(txt, 'the failure must READ as a failure, not as a muted placeholder')
      .toMatch(/fail|error|err|✗|✕|⚠|🔴|unreachable|no beacon/i);
    // an em-dash-only beacon cell is exactly the "never turned on" look this test exists to forbid
    const cellTexts = await first.locator('td').allTextContents();
    expect(cellTexts.some((c) => /timeout/i.test(c)),
      'the error belongs in a cell of its own row, not only in a tooltip').toBe(true);
  });

  test('★ every section heading has a painted box', async ({ page }) => {
    await renderConsole(page);
    const heads = page.locator('h1, h2, h3');
    const n = await heads.count();
    expect(n, 'the page must have section headings').toBeGreaterThan(1);
    for (let i = 0; i < n; i += 1) {
      const h = heads.nth(i);
      const label = ((await h.textContent()) || `heading#${i}`).trim().slice(0, 40);
      const b = await box(h, `heading "${label}"`);
      expect(b.width, `heading "${label}" collapsed to zero width`).toBeGreaterThan(0);
      expect(b.height, `heading "${label}" collapsed to zero height`).toBeGreaterThan(0);
    }
  });

  test('★ nothing overflows the viewport horizontally', async ({ page }) => {
    await renderConsole(page);
    const over = await page.evaluate(() => {
      const d = document.documentElement;
      return { scroll: d.scrollWidth, client: d.clientWidth };
    });
    expect(over.scroll, `the page scrolls sideways (${over.scroll} > ${over.client})`)
      .toBeLessThanOrEqual(over.client + 1);
  });

  test('★ no table cell clips its own text — including the last-seen column', async ({ page }) => {
    // A last-seen timestamp that is present but half-cut is the same lie as one that is missing.
    // Swept across EVERY cell rather than just the one column: same failure shape, same fix.
    await renderConsole(page);
    const clipped = await page.evaluate(() => {
      const bad: string[] = [];
      document.querySelectorAll<HTMLElement>('td, th').forEach((c) => {
        const r = c.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) return;                 // not painted; other tests cover
        if (c.scrollWidth > c.clientWidth + 1) {
          bad.push(`"${(c.textContent || '').trim().slice(0, 32)}" ${c.scrollWidth}>${c.clientWidth}`);
        }
      });
      return bad.slice(0, 6);
    });
    expect(clipped, `cells clipping their text: ${clipped.join(' | ')}`).toEqual([]);
  });

  test('★ text is not the same colour as what it sits on', async ({ page }) => {
    // White-on-white passes every DOM assertion ever written. The background has to be resolved by
    // walking UP to the first OPAQUE ancestor — an element's own computed background-color is
    // rgba(0,0,0,0) by default, and comparing against that "passes" everything, vacuously.
    await renderConsole(page);
    const bad = await page.evaluate(() => {
      const parse = (s: string) => {
        const m = s.match(/rgba?\(([^)]+)\)/);
        if (!m) return null;
        const p = m[1].split(',').map((x) => parseFloat(x));
        return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
      };
      const opaqueBg = (el: HTMLElement | null) => {
        for (let e: HTMLElement | null = el; e; e = e.parentElement) {
          const c = parse(getComputedStyle(e).backgroundColor);
          if (c && c.a > 0.95) return c;
        }
        return { r: 255, g: 255, b: 255, a: 1 };                     // the canvas, if nothing paints
      };
      const out: string[] = [];
      const sel = 'h1, h2, h3, td, th, .muted, p, div';
      document.querySelectorAll<HTMLElement>(sel).forEach((el) => {
        const txt = (el.textContent || '').trim();
        if (!txt || el.children.length) return;                      // leaf text nodes only
        const r = el.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) return;
        const fg = parse(getComputedStyle(el).color);
        if (!fg || fg.a === 0) { out.push(`transparent text: "${txt.slice(0, 28)}"`); return; }
        const bg = opaqueBg(el);
        const dist = Math.abs(fg.r - bg.r) + Math.abs(fg.g - bg.g) + Math.abs(fg.b - bg.b);
        if (dist < 24) out.push(`"${txt.slice(0, 28)}" fg=${fg.r},${fg.g},${fg.b} bg=${bg.r},${bg.g},${bg.b}`);
      });
      return out.slice(0, 6);
    });
    expect(bad, `text indistinguishable from its background: ${bad.join(' | ')}`).toEqual([]);
  });

  test('★ SCREENSHOT — the evidence a human can open', async ({ page }) => {
    await renderConsole(page);
    try { fs.unlinkSync(SHOT); } catch { /* first run */ }

    // `animations: 'disabled'` is NOT cosmetic here — see the font-trap comment in renderConsole().
    // Infinite CSS animations can keep a fullPage capture waiting indefinitely.
    await page.screenshot({ path: SHOT, fullPage: true, animations: 'disabled' });

    // A capture that produced no file must FAIL, never pass silently — a gate that reports success
    // while writing nothing is worse than no gate, because it teaches you to stop looking.
    expect(fs.existsSync(SHOT), `no screenshot was written to ${SHOT}`).toBe(true);
    const size = fs.statSync(SHOT).size;
    expect(size, `screenshot at ${SHOT} is empty`).toBeGreaterThan(2048);
    // eslint-disable-next-line no-console
    console.log(`\n📸 v1596 console render captured (${size} bytes):\n   ${SHOT}\n`);
  });

  test('the log window is walked to its end, not truncated by a bare limit', async ({ page }) => {
    // The structural half of the first machine test: even if a future layout stops printing machine
    // names in a way getByText can find, reading fewer keys than exist is still the bug. A single
    // uncursored list() over `consolelog:` cannot be correct once the log outgrows one page.
    const onRequestGet = loadFn(FN, 'onRequestGet');
    const kv = seed();
    await onRequestGet({ request: { url: `${ORIGIN}?k=${SECRET}` }, env: { VISITS_KEY: SECRET, TZ_HISTORY: kv } });
    const logCalls = kv.listCalls.filter((c) => c.prefix === 'consolelog:');
    expect(logCalls.length, 'the 600-event log must be paged through, not read once').toBeGreaterThan(1);
    expect(logCalls.some((c) => c.cursor != null), 'pagination must use the cursor KV returns').toBe(true);
  });

  test('a wrong key still 404s — this page stays Konyo-only', async () => {
    // Whatever the fix widens, it must not widen the door. /console and /visits are gated by
    // VISITS_KEY and answer a bare 404 to anything else.
    const onRequestGet = loadFn(FN, 'onRequestGet');
    const res = await onRequestGet({
      request: { url: `${ORIGIN}?k=nope` },
      env: { VISITS_KEY: SECRET, TZ_HISTORY: seed() },
    });
    expect(res.status, 'a wrong key must 404').toBe(404);
    const bare = await res.text();
    expect(bare.length, 'and say nothing about what lives here').toBeLessThan(64);
  });
});
