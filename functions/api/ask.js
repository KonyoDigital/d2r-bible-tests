/**
 * /api/ask — the "AI Diablo II Helper" (v331). A conversational Sonnet endpoint that answers
 * crafting / runeword / grail / "what can I make now and how" questions from the player's LIVE
 * stash snapshot (computed client-side by window.buildAskSnapshot). Mirrors intake.js: the
 * Anthropic key is a Pages SECRET, never in the page. Free-text answer (no image, no schema).
 *
 * POST { question:<string>, snapshot:<object>, history?:[{role,content}] }
 *   → { answer:<markdown-ish text>, usage }
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
  const { question, snapshot, history } = body || {};
  if (!question || typeof question !== 'string') return json({ error: 'missing question' }, 400);
  if (question.length > 2000) return json({ error: 'question too long' }, 413);
  const snap = (snapshot && typeof snapshot === 'object') ? snapshot : {};

  // ── persona + rules (cached system prefix — stays stable so the snapshot, which varies per
  //    call, lives in the USER turn and never busts the cache; same pattern as intake.js). ──
  const sysText =
    'You are the D2R Bible Assistant — an expert Diablo II: Resurrected crafting, runeword, Horadric-cube and Holy-Grail advisor embedded in Konyo\'s Farming Bible. You answer from the player\'s LIVE stash snapshot (provided each turn in the user message) plus your deep D2R knowledge. '
    + 'RULES: '
    + '(1) Be concrete and ACTIONABLE. When asked "what can I make / craft", lead with what is craftable RIGHT NOW from the snapshot (runewords whose runes are all in stock, crafts whose rune+gem are in stock), then what they are 1–2 items away from, with the exact missing item(s). '
    + '(2) Use the snapshot as ground truth for counts. The snapshot already lists completable runewords, craftable craft-slots, cubeable materials, and "close" items — trust those flags; do not re-derive them. If the snapshot is empty/sparse, say so and give general guidance. '
    + '(3) For runewords give the exact rune ORDER (runes must be inserted left-to-right in order) and the correct socket count + base type. For crafts give the recipe (magic base of the right type + the deciding gem + the rune) and the 2 universal guaranteed mods (the 3rd is slot-specific). '
    + '(4) Be ACCURATE to current D2R (Reign of the Warlock) mechanics — never invent runewords, recipes, or affixes. A rare amulet caps at +2 class skills; rings can\'t roll +class skills; Spirit goes in a 4-socket sword OR shield; Crescent Moon is axe/sword/polearm only; etc. If unsure, say so rather than guess. '
    + '(5) Keep answers tight — a few short paragraphs or a compact list. Plain text with simple markdown (•, **bold**). No preamble like "Great question". '
    + '(6) Stay on Diablo II. If asked something off-topic, briefly redirect to D2R.';
  const system = [{ type: 'text', text: sysText, cache_control: { type: 'ephemeral' } }];

  // history (optional prior turns) then the current turn carrying the snapshot
  const msgs = [];
  if (Array.isArray(history)) {
    for (const h of history.slice(-6)) {
      if (h && (h.role === 'user' || h.role === 'assistant') && typeof h.content === 'string') {
        msgs.push({ role: h.role, content: h.content.slice(0, 4000) });
      }
    }
  }
  const snapText = 'CURRENT STASH SNAPSHOT (the player\'s live tallies + what the bible computed is makeable):\n'
    + JSON.stringify(snap).slice(0, 24000)
    + '\n\nQUESTION: ' + question;
  msgs.push({ role: 'user', content: snapText });

  const apiResp = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': env.ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: env.MODEL || 'claude-sonnet-4-6',
      max_tokens: 1024,
      system,
      messages: msgs,
    }),
  });

  if (!apiResp.ok) {
    const errText = await apiResp.text();
    return json({ error: 'upstream', status: apiResp.status, detail: errText.slice(0, 300) }, 502);
  }
  const data = await apiResp.json();
  const usage = data.usage ? { in: data.usage.input_tokens, out: data.usage.output_tokens, cached: data.usage.cache_read_input_tokens } : null;
  if (data.stop_reason === 'refusal') return json({ answer: 'I can only help with Diablo II questions about your stash — try rephrasing.', note: 'refused', usage }, 200);
  const textBlock = (data.content || []).find((b) => b.type === 'text');
  const answer = textBlock ? textBlock.text : '(no answer)';
  return json({ answer, usage }, 200);
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'content-type': 'application/json', ...CORS },
  });
}
