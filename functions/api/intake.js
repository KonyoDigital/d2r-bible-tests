/**
 * /api/intake — Pages Function proxy for the Vault's 📸 AI intake (v205) and the
 * Tools "1-photo tally" intakes (v253: runes; later gems/special).
 * The Anthropic API key lives as a Pages SECRET (never in the page).
 *
 * POST { image:<base64>, media_type, names:[vocabulary], kind? }
 *   kind omitted / 'items' → returns { items:[names], unrecognized:[] }   (presence; tooltip-text only)
 *   kind === 'tally'       → returns { tally:{name:count}, unrecognized:[] } (icon-count of runes/gems/etc.)
 */
const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'content-type',
};

export async function onRequestOptions() {
  return new Response(null, { status: 204, headers: CORS });
}

export async function onRequestPost(context) {
  const { request, env } = context;
  let body;
  try { body = await request.json(); } catch { return json({ error: 'bad json' }, 400); }
  const { image, media_type, names, kind } = body || {};
  if (!image || typeof image !== 'string') return json({ error: 'missing image' }, 400);
  if (image.length > 1_800_000) return json({ error: 'image too large — downscale client-side' }, 413);
  if (!Array.isArray(names) || names.length < 3 || names.length > 600) return json({ error: 'names vocabulary required' }, 400);
  const mt = ['image/jpeg', 'image/png', 'image/webp'].includes(media_type) ? media_type : 'image/jpeg';
  const isTally = kind === 'tally';

  const itemsText = 'You read Diablo 2 Resurrected screenshots (stash/inventory panels, ground loot, hover tooltips). '
    + 'Extract ITEM NAMES whose text is VISIBLE in the image and return vocabulary matches in "items". STRICT RULES: '
    + '(0) FIRST check whether a hover-TOOLTIP panel (translucent dark box of colored stat lines) is open anywhere. '
    + 'If NO tooltip is open, return {"items":[],"unrecognized":[]} immediately — recognizable item ARTWORK alone is '
    + 'NEVER reportable, no matter how distinctive. '
    + '(1) Report a vocabulary item ONLY if its name appears as readable text — NEVER fuzzy-match a similar-looking '
    + 'string (a base type like "Tyrant Club" is NOT "Tyrael\'s Might"). If text is too small or blurry to read with '
    + 'CERTAINTY, do not guess: omit it or put your literal best transcription in "unrecognized". A wrong match is far '
    + 'worse than a miss — the user can re-screenshot. '
    + '(2) In a tooltip, the ITEM NAME is the TOP line; the line under it is the BASE TYPE (e.g. "Bearded Axe", '
    + '"Bone Shield", "Tyrant Club") — base types are never items, do not report them anywhere. '
    + '(3) Ignore NPC name labels (Charsi, Kashya, Warriv, Akara, Gheed the NPC...), zone names, UI text, gold, potions. '
    + '(4) Item ART without readable name text is NOT enough — skip it. '
    + 'Clearly readable item names NOT in the vocabulary go in "unrecognized" as written. '
    + 'VOCABULARY:\n' + names.join('\n');

  const tallyText = 'You read a Diablo 2 Resurrected screenshot showing RUNES and/or GEMS — usually a dedicated organized '
    + 'stash tab (the Runes tab or Gems tab), or a stash/inventory grid. Return a "tally" array of {name, count} for '
    + 'every rune/gem you can identify. '
    + 'HOW TO COUNT — THIS IS THE MOST IMPORTANT PART, READ CAREFULLY: '
    + '(1) In D2R\'s organized RUNES and GEMS stash tabs each rune/gem type sits in ONE fixed cell, and the QUANTITY you '
    + 'own is printed as a small STACK-COUNT NUMBER, usually in the lower-RIGHT corner of that cell (e.g. a Tal rune cell '
    + 'showing "23" means you own TWENTY-THREE Tal runes — NOT one). '
    + '(2) count = that printed stack number. READ THE DIGITS CAREFULLY — stack counts are frequently TWO DIGITS '
    + '(3, 7, 11, 15, 16, 17, 19, 22, 23 …). DO NOT assume every stack is 1 or 2 — that is the most common mistake. '
    + 'Look at each cell\'s corner number and transcribe exactly what is printed. '
    + '(3) If a cell shows an icon but NO printed number, count = 1. '
    + '(4) If the SAME item also appears loose across several separate cells (a normal inventory), ADD those cells together. '
    + '(5) A dark/empty cell, or a faint GREYED-OUT placeholder icon with no number, means you own ZERO of that rune — '
    + 'do NOT report it. '
    + 'IDENTIFY & COVERAGE: '
    + '(6) Identify each rune by its engraved glyph (gems by tint = type, cut = grade) and any readable name. '
    + 'SCAN THE ENTIRE GRID top-to-bottom and LEFT-to-right, including the rare high runes near the BOTTOM rows '
    + '(Vex, Ohm, Lo, Sur, Ber, Jah, Cham, Zod) — do not stop early. Report every cell that has a real (non-greyed) icon. '
    + '(7) Only report a vocabulary entry you can identify with CONFIDENCE; if two look too similar to tell apart, put your '
    + 'best transcription in "unrecognized" rather than guessing the wrong rune. '
    + '(8) Only names from the vocabulary. Ignore gold, potions, UI text, non-rune/non-gem items. Readable-but-not-in-vocab → "unrecognized". '
    + 'VOCABULARY:\n' + names.join('\n');

  const itemsSchema = {
    type: 'object',
    properties: {
      items: { type: 'array', items: { type: 'string' } },
      unrecognized: { type: 'array', items: { type: 'string' } },
    },
    required: ['items', 'unrecognized'],
    additionalProperties: false,
  };
  const tallySchema = {
    type: 'object',
    properties: {
      tally: {
        type: 'array',
        items: {
          type: 'object',
          properties: { name: { type: 'string' }, count: { type: 'integer' } },
          required: ['name', 'count'],
          additionalProperties: false,
        },
      },
      unrecognized: { type: 'array', items: { type: 'string' } },
    },
    required: ['tally', 'unrecognized'],
    additionalProperties: false,
  };

  const system = [{ type: 'text', text: isTally ? tallyText : itemsText, cache_control: { type: 'ephemeral' } }];

  const apiResp = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': env.ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      // Tally mode must read small printed stack-count DIGITS off each cell → use the stronger
      // vision model by default (Haiku misreads two-digit stacks as 1/2). Override via env.MODEL.
      model: env.MODEL || (isTally ? 'claude-sonnet-4-6' : 'claude-haiku-4-5'),
      max_tokens: 1024,
      system,
      output_config: { format: { type: 'json_schema', schema: isTally ? tallySchema : itemsSchema } },
      messages: [{
        role: 'user',
        content: [
          { type: 'image', source: { type: 'base64', media_type: mt, data: image } },
          { type: 'text', text: isTally ? 'Tally every rune/gem in this screenshot. For each cell, READ the small stack-count number printed in its corner and use THAT as the count (it is often two digits like 11, 17, 23 — do not assume 1 or 2). Scan the whole grid including the high runes at the bottom.' : 'Extract the item names from this screenshot.' },
        ],
      }],
    }),
  });

  if (!apiResp.ok) {
    const errText = await apiResp.text();
    return json({ error: 'upstream', status: apiResp.status, detail: errText.slice(0, 300) }, 502);
  }
  const data = await apiResp.json();
  const usage = data.usage ? { in: data.usage.input_tokens, out: data.usage.output_tokens, cached: data.usage.cache_read_input_tokens } : null;
  if (data.stop_reason === 'refusal') return json(isTally ? { tally: {}, unrecognized: [], note: 'refused' } : { items: [], unrecognized: [], note: 'refused' }, 200);
  const textBlock = (data.content || []).find((b) => b.type === 'text');
  let parsed = {};
  try { parsed = JSON.parse(textBlock ? textBlock.text : '{}'); } catch {}

  // Vocab matching — NEVER drop a read silently (the Frostburn lesson): resolve via
  // (1) exact, (2) normalized (case/punct-insensitive), (3) vocab-name-is-prefix at a
  // word boundary (min 6 chars, longest match wins). Unmatched → "unrecognized".
  const vocab = new Set(names);
  const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  const normMap = new Map(names.map((n) => [norm(n), n]));
  const sortedVocab = names.map((n) => [norm(n), n]).filter(([k]) => k.length >= 6)
    .sort((a, b) => b[0].length - a[0].length);
  const resolve = (r) => {
    if (vocab.has(r)) return r;
    const nr = norm(r);
    if (normMap.has(nr)) return normMap.get(nr);
    const hit = sortedVocab.find(([k]) => nr === k || nr.startsWith(k + ' '));
    return hit ? hit[1] : null;
  };

  if (isTally) {
    const tally = {};
    const unrec = [];
    for (const row of (parsed.tally || [])) {
      const nm = resolve(row && row.name);
      const c = parseInt(row && row.count, 10);
      if (nm && isFinite(c) && c > 0) tally[nm] = (tally[nm] || 0) + c;
      else if (row && row.name) unrec.push(String(row.name));
    }
    return json({
      tally,
      unrecognized: [...new Set([...unrec, ...(parsed.unrecognized || [])])].slice(0, 40),
      usage,
    }, 200);
  }

  const items = [], unrec = [];
  for (const r of (parsed.items || [])) {
    const nm = resolve(r);
    if (nm) items.push(nm); else unrec.push(r);
  }
  return json({
    items: [...new Set(items)],
    unrecognized: [...new Set([...unrec, ...(parsed.unrecognized || [])])].slice(0, 40),
    usage,
  }, 200);
}

function json(obj, status) {
  return new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json', ...CORS } });
}
