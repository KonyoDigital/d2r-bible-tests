/* tests/_palette.ts — the palette spine. Helper only: NO test() blocks live here.
 *
 * WHY THIS FILE EXISTS — two ships this project already paid for:
 *
 *   v1621  A spec pinned a literal, fully saturated green as the expected set-quality colour.
 *          When the palette was corrected to D2's real FontColorGreen — extracted from Konyo's
 *          own install, a hair darker than full saturation — the test WENT RED ON THE FIX. It was
 *          defending a value it had copied, not the rule that the board and the console must agree
 *          with the token they both claim to render. A test that must be edited whenever the app is
 *          corrected is not guarding the app; the app is guarding it.
 *
 *   v1622  --rar-unique shipped set to the console's own chrome gold — the frame/heading gold,
 *          not the game's unique-item gold. THREE tests passed straight over it, because every one
 *          of them only asserted that a rarity CLASS was present on the element. Not one asked what
 *          that class actually computed to. "Has the right class" and "paints the right colour" are
 *          different claims, and only the second one is the thing Konyo can see.
 *
 * THE RULE THIS ENCODES: the app owns the values; a spec READS them and asserts a RELATIONSHIP —
 * equal to the token the surface claims, DIFFERENT from the quality it must never be confused with,
 * unchanged across the two documents. No quality hex literal appears anywhere in this file, in code
 * or in prose, by design: P6 extends the hex guard over tests/ and this file must pass it. Colours
 * are described in words only.
 *
 * EVERY VALUE IS RESOLVED THROUGH THE BROWSER. A declaration is written onto a scratch element's
 * `color` and read back through getComputedStyle, so a short hex, a long hex and an rgb() triple
 * all normalise to one `rgb(r, g, b)` string — in the same colour space the render actually uses.
 * Comparing raw declaration text instead would call two spellings of one colour a mismatch.
 *
 * NULL IS LOAD-BEARING. A missing/renamed token resolves to null, and `null === null` is exactly
 * the assertion-that-cannot-fail this audit exists to kill: delete a token from both documents and
 * a naive equality check goes GREEN. So null is never silently comparable — assertTokens() must be
 * called before any comparison, and it throws a named error listing every key that is missing.
 *
 * Resolution technique copied from tests/v1625_tab_quality_tints.spec.ts (the tokens() helper),
 * including its NOT-DECLARED sentinel: an impossible colour is assigned first, and if the readback
 * is still that sentinel the declaration never took, so the property is not declared here.
 */

/* Board = bible.html :root. Key -> the custom property that key names. */
const BOARD_MAP: Record<string, string> = {
  unique:     '--q-unique',
  set:        '--q-set',
  orange:     '--q-orange',      /* crafted quality on the board */
  magic:      '--q-magic',
  rare:       '--q-rare',
  normal:     '--q-normal',
  runeword:   '--q-runeword',    /* declared as var(--q-unique); resolved, not string-matched */
  rune:       '--rune',
  goldBright: '--gold-bright',   /* board chrome gold — NOT an item quality */
  terror:     '--terror',
};

/* Console = tv/control_ui.html :root.
 * `gold` is the console's own chrome gold, declared there as plain `--gold` (that is the real
 * token name; it is not called --gold-bright on this side, though it holds the same colour as the
 * board's chrome gold). It is exported so a spec can assert the v1622 shape directly: a rarity
 * token must NOT equal the chrome gold. `goldChrome` is a documented alias for the same token so
 * callers reaching for either name get the value rather than an undefined key.
 * --rar-runeword deliberately holds the same colour as --rar-unique: the game paints a completed
 * runeword's NAME the same gold as a unique. That equality is intentional and specs assert it. */
const CONSOLE_MAP: Record<string, string> = {
  unique:     '--rar-unique',
  set:        '--rar-set',
  rare:       '--rar-rare',
  magic:      '--rar-magic',
  runeword:   '--rar-runeword',
  orange:     '--rar-orange',    /* crafted quality in the console */
  rune:       '--rar-rune',
  gold:       '--gold',          /* console chrome gold — NOT an item quality */
  goldChrome: '--gold',          /* alias of the line above, same token */
};

/* Impossible as a palette value, so it can only ever mean "the declaration did not take". */
const SENTINEL = 'rgb(1, 2, 3)';

/* Resolve custom properties to normalised rgb() strings inside the page.
 * Returns null for any property that is not declared on :root, or that is declared but does not
 * resolve to a usable colour — either way there is nothing to compare, and callers must not. */
async function resolve(page: any, props: string[]): Promise<Record<string, string | null>> {
  return page.evaluate(({ props, sentinel }: { props: string[]; sentinel: string }) => {
    const cs = getComputedStyle(document.documentElement);
    const probe = document.createElement('span');
    probe.style.cssText = 'position:absolute;left:-9999px;top:-9999px';
    (document.body || document.documentElement).appendChild(probe);
    const out: Record<string, string | null> = {};
    try {
      for (const p of props) {
        const raw = cs.getPropertyValue(p).trim();
        if (!raw) { out[p] = null; continue; }        /* not declared at all */
        probe.style.color = sentinel;
        probe.style.color = raw;
        let got = getComputedStyle(probe).color;
        if (got === sentinel) {
          /* The computed value still carried an unresolved var() reference (a token declared as an
             alias of another). The token IS declared, so let the cascade substitute it instead of
             re-parsing the text ourselves — never string-match a var() chain. */
          probe.style.color = sentinel;
          probe.style.setProperty('color', 'var(' + p + ')');
          got = getComputedStyle(probe).color;
        }
        out[p] = got === sentinel ? null : got;
      }
    } finally {
      probe.remove();                                  /* no scratch element survives this call */
    }
    return out;
  }, { props, sentinel: SENTINEL });
}

async function byMap(page: any, map: Record<string, string>): Promise<Record<string, string | null>> {
  const keys = Object.keys(map);
  /* de-duplicated: `gold` and `goldChrome` are the same property, resolved once */
  const props = Array.from(new Set(keys.map(k => map[k])));
  const resolved = await resolve(page, props);
  const out: Record<string, string | null> = {};
  for (const k of keys) out[k] = resolved[map[k]] ?? null;
  return out;
}

/* bible.html's :root quality palette, resolved. Keys:
 * unique, set, orange, magic, rare, normal, runeword, rune, goldBright, terror */
export async function boardTokens(page: any): Promise<Record<string, string | null>> {
  return byMap(page, BOARD_MAP);
}

/* tv/control_ui.html's :root rarity palette, resolved. Keys:
 * unique, set, rare, magic, runeword, orange, rune, gold (= goldChrome, the console's chrome gold) */
export async function consoleTokens(page: any): Promise<Record<string, string | null>> {
  return byMap(page, CONSOLE_MAP);
}

/* Resolve ONE custom property by its real CSS name (e.g. '--q-set'), for tokens outside the two
 * maps above. Same normalisation, same null-means-not-declared contract. */
export async function tokenRGB(page: any, name: string): Promise<string | null> {
  const prop = name.startsWith('--') ? name : '--' + name;
  const got = await resolve(page, [prop]);
  return got[prop] ?? null;
}

export class PaletteTokenMissingError extends Error {
  readonly tokens: string[];
  constructor(missing: string[]) {
    super(
      'PALETTE TOKEN MISSING: ' + missing.map(k => '"' + k + '"').join(', ') +
      ' did not resolve to a colour. The token was renamed, deleted, or moved out of :root. ' +
      'This is a LOUD failure on purpose: comparing null to null is green and proves nothing ' +
      '(the v1622 shape). Fix the token or fix the key — do not compare around it.'
    );
    this.name = 'PaletteTokenMissingError';
    this.tokens = missing;
  }
}

/* Gate every comparison. Throws a named error naming EVERY missing key — a key absent from the
 * record (typo, renamed export) fails exactly as loudly as a key present with a null value. */
export function assertTokens(
  t: Record<string, string | null>,
  ...keys: string[]
): asserts t is Record<string, string> {
  const missing = keys.filter(k => !(k in t) || t[k] == null || t[k] === '');
  if (missing.length) throw new PaletteTokenMissingError(missing);
}
