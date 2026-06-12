/**
 * /api/intake — Pages Function proxy for the Vault's 📸 AI intake (v205).
 * Same-origin endpoint on bull-4-u.com — the Anthropic API key lives as a
 * Pages SECRET (wrangler pages secret put ANTHROPIC_API_KEY), never in the page.
 * POST { image: <base64>, media_type, names: [tracked item names] }
 *  -> Claude vision (env.MODEL || claude-haiku-4-5) with a structured-output
 *     schema, items constrained server-side to the provided vocabulary.
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
  const { image, media_type, names } = body || {};
  if (!image || typeof image !== 'string') return json({ error: 'missing image' }, 400);
  if (image.length > 1_800_000) return json({ error: 'image too large — downscale client-side' }, 413);
  if (!Array.isArray(names) || names.length < 10 || names.length > 600) return json({ error: 'names vocabulary required' }, 400);
  const mt = ['image/jpeg', 'image/png', 'image/webp'].includes(media_type) ? media_type : 'image/jpeg';

  const system = [{
    type: 'text',
    text: 'You read Diablo 2 Resurrected screenshots (stash tabs, inventories, loot on the ground, hover tooltips). '
      + 'Extract every ITEM NAME visible in the image. Match each against this exact vocabulary of tracked item names — '
      + 'return matches VERBATIM from the vocabulary in "items" (a vocabulary entry like "Harlequin Crest (Shako)" matches '
      + 'the in-game name "Harlequin Crest"). Names you can clearly read that are NOT in the vocabulary go in "unrecognized" '
      + 'as written. Ignore UI labels, gold amounts, potion/scroll clutter, and anything you cannot read with confidence. '
      + 'VOCABULARY:\n' + names.join('\n'),
    cache_control: { type: 'ephemeral' },
  }];

  const apiResp = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': env.ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: env.MODEL || 'claude-haiku-4-5',
      max_tokens: 1024,
      system,
      output_config: {
        format: {
          type: 'json_schema',
          schema: {
            type: 'object',
            properties: {
              items: { type: 'array', items: { type: 'string' } },
              unrecognized: { type: 'array', items: { type: 'string' } },
            },
            required: ['items', 'unrecognized'],
            additionalProperties: false,
          },
        },
      },
      messages: [{
        role: 'user',
        content: [
          { type: 'image', source: { type: 'base64', media_type: mt, data: image } },
          { type: 'text', text: 'Extract the item names from this screenshot.' },
        ],
      }],
    }),
  });

  if (!apiResp.ok) {
    const errText = await apiResp.text();
    return json({ error: 'upstream', status: apiResp.status, detail: errText.slice(0, 300) }, 502);
  }
  const data = await apiResp.json();
  if (data.stop_reason === 'refusal') return json({ items: [], unrecognized: [], note: 'refused' }, 200);
  const textBlock = (data.content || []).find((b) => b.type === 'text');
  let parsed = { items: [], unrecognized: [] };
  try { parsed = JSON.parse(textBlock ? textBlock.text : '{}'); } catch {}
  const vocab = new Set(names);
  return json({
    items: [...new Set((parsed.items || []).filter((n) => vocab.has(n)))],
    unrecognized: (parsed.unrecognized || []).slice(0, 40),
    usage: data.usage ? { in: data.usage.input_tokens, out: data.usage.output_tokens, cached: data.usage.cache_read_input_tokens } : null,
  }, 200);
}

function json(obj, status) {
  return new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json', ...CORS } });
}
