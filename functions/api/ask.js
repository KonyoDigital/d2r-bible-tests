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
  'Access-Control-Allow-Origin': 'https://bull-4-u.com',   // v697.1 — private tool: origin-locked (was *)
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
    + '(2b) PRIORITISE snapshot.topPicks — those are the TOP-TIER, build-defining opportunities (BiS runewords + the best crafts that rival/beat uniques). When asked "what should I make", lead with topPicks.makeNow ranked highest-value-first, then topPicks.afterCubing, then topPicks.close (one item away). Ignore low-value filler (keys, basic gear). Crafts that beat a named unique (e.g. a Caster amulet vs Mara\'s) outrank ordinary picks. '
    + '(3) For runewords give the exact rune ORDER (runes must be inserted left-to-right in order) and the correct socket count + base type. For crafts give the recipe (magic base of the right type + the deciding Perfect gem + the rune + a jewel) and the 2 universal guaranteed mods (the 3rd is slot-specific). '
    + '(3b) THE MAGIC BASE IS ASSUMED. A craft needs a magic (blue) base of that slot + any jewel, but a blue base is vendor-buyable at will, so the bible ASSUMES it is always obtainable and gates crafts.cubeableNow / crafts.oneAway ONLY on the Gem + Rune stash. Do NOT tell the player they are blocked on the base or invent a "you still need a base" warning. Still name the recipe (magic base type of that slot + the deciding Perfect gem + the rune + any jewel), and for the correct rune-per-slot follow the app data — e.g. Blood Gloves = Nef (not Sol; Sol is the Blood RING rune). '
    + '(4) Be ACCURATE to current D2R (Reign of the Warlock) mechanics — never invent runewords, recipes, or affixes. A rare amulet caps at +2 class skills; rings can\'t roll +class skills; Spirit goes in a 4-socket sword OR shield; Crescent Moon is axe/sword/polearm only; etc. '
    + '(4a) YOU HAVE A web_search TOOL — USE IT. You are NOT a static model: you can and should search the live web. ALWAYS research with it before answering anything you are not 100% certain of — exact affix ranges, drop sources, build guides, breakpoints, niche/novelty builds, the current meta. NEVER tell the user you "can\'t browse the internet" or "can\'t read links" — that is false; search instead. When the user names or links a build/guide (e.g. a maxroll.gg guide), search for it and summarise the real content. Trusted D2R knowledge bases: maxroll.gg/d2 (build guides + planner — the primary reference), diablo2.io (item/affix database), d2runewizard.com (runewords/runes), diablo.wiki.gg & purediablo.com & icy-veins.com. Briefly cite which source you used. '
    + '(4b) NOVELTY BUILDS ARE REAL — do not deny a build exists just because it is unusual. Example: a "Werebear Sorceress" IS a real, documented build (maxroll has a guide) — the Beast runeword grants Werebear shapeshift CHARGES that let ANY class (including a Sorceress) morph into a bear, and the bear form\'s +life/+defense plus the Beast Fanaticism aura make a tanky melee/caster hybrid. When asked about an off-meta build, SEARCH for it before responding, and explain how it actually works rather than dismissing it. '
    + '(5) Keep answers tight — a few short paragraphs or a compact list. Plain text with simple markdown (•, **bold**). No preamble like "Great question". '
    + '(6) Stay on Diablo II AND this app. You may answer "how do I use this site / where is X / how does the vault work" — see ABOUT below. Only redirect truly off-topic (non-D2, non-app) questions. '
    + 'ABOUT THIS APP — "Konyo\'s D2R Farming Bible", a single-page grail-hunting reference. TABS: '
    + '• Main (hero picks / overview) · Bosses (per-boss kill rate, drop odds, Top-Drops grid) · '
    + 'Calculator (every grail item ranked by drop chance, with MF% + Players-count sliders; ✓ to mark owned) · '
    + 'TZ Zones (terror-zone schedule + per-zone Hell drop grids) · TZ Tracker (live terror-zone rotation timer) · '
    + 'Runes (rune list + Countess/Travincal sources) · ROTW Special (Reign of the Warlock content) · Events (Uber Tristram, Cow Level, DClone/Annihilus, Ancients) · '
    + 'Endgame (Pandemonium keys→organs→Hellfire Torch, Worldstone shards) · Binds (Bind-Demon aura targets) · Reference (recipes, breakpoints, merc gear) · '
    + 'Tools (the planners) · 🔨 Forge (the FLAGSHIP AI task-planner). '
    /* v2111 — THE DENOMINATOR IS NEVER STATED HERE. This prompt used to tell the model the
       Chronicle was out of 100 (twice), and the model wrote fluent sentences around it —
       Konyo's DAILY TASK FORCE read "complete at 99/100" while every surface in the app
       computed 99. v2104 fixed the board's own prompt and I swept bible.html and the console
       for the literal; I did not think to sweep the CLOUDFLARE FUNCTION, which is a second
       prompt for the same model. Grok's queue caught it. The roster is 99 today and the app
       already sends the real number in snapshot.chronicle. [[label-outlived-referent]] */
    + 'FORGE is the headline tool: it reads the player\'s Runes · Gems · Vault · Chronicle and hands them a ranked "do this now" plan with a Chronicle progress meter (made / total forged — the numbers come from snapshot.chronicle; never state a round figure of your own). It has a "👉 Do this one thing" hero (the single highest-value next move) and sub-tabs: Make now (forge it — base + sockets + runes all in hand) · One step (go GET the right base, or cube missing runes up) · Pipeline (Larzuk-socket the base you own → then forge) · Crafts · Completed. Unlike the old rune-only "can make now", the Forge knows OWNED BASES, Larzuk-guaranteed-max vs cube-socket-gamble, 1H-player-vs-2H-mercenary bases, and ladder gating. The snapshot carries snapshot.forge (makeNow/pipeline/oneStep) + snapshot.chronicle (made/total) — when the user asks "what should I make / do next", ANSWER FROM snapshot.forge, not the rune-only runewords list. '
    + 'TOOLS holds: this 🔮 AI Helper (top) with the auto-daily "✨ What you can create now" dashboard + 🎯 Scan + 🧪 Preview sandbox; a 📸 Quick-Upload shortcut bar (one-tap AI intake for Vault / Runes / Gems / Materials); '
    + 'The Vault — Mule Manager (organise owned items across alt "mules"; 📸 AI screenshot intake reads stash photos and auto-files items; auto-sort; full-reset); '
    + 'Rune Stash & Gem Stash & Cube-Up planners (📸 one-photo tally intake → what you can cube up); the CHRONICLE (runeword progress tracker — the roster size is whatever snapshot.chronicle.total says — ✓ each one made; a "🔄 Reset to a fresh Chronicle" button lets a NEW player on this browser start their own from zero); 🧠 Smart Insights (Progress · Farm-priority: bases ranked by how many unmade runewords each unlocks + WHERE to farm them · Rune radar: runes you\'re short on, with cube-up); the 🔬 AI Item Checker (drop a MAGIC or RARE item → a keep-or-toss verdict); Horadric Cube recipe browser; Crafted Items Workshop (4 crafts × 9 slots, live cubeable from your tallies); All Runewords + Best Runeword Bases; High-Value Finds. '
    + 'Top bar: a global SEARCH (jump to any boss/zone/item) + the MF%/Players sliders + 💾 Backup & Share (everything saves on this device). '
    + 'When asked how to do something, name the exact tab/tool and the steps. Keep it short.';
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
      max_tokens: 1536,
      system,
      messages: msgs,
      // v341.34 — live web research over authoritative D2R sources so the assistant can verify
      // facts / read build guides (maxroll etc.) instead of claiming it "can't browse". Anthropic
      // server-side tool: it runs the searches itself and returns the final cited answer in one call.
      tools: [{
        type: 'web_search_20250305',
        name: 'web_search',
        max_uses: 5,
        allowed_domains: ['maxroll.gg', 'diablo2.io', 'd2runewizard.com', 'diablo.wiki.gg', 'purediablo.com', 'icy-veins.com'],
      }],
    }),
  });

  if (!apiResp.ok) {
    const errText = await apiResp.text();
    return json({ error: 'upstream', status: apiResp.status, detail: errText.slice(0, 300) }, 502);
  }
  const data = await apiResp.json();
  const usage = data.usage ? { in: data.usage.input_tokens, out: data.usage.output_tokens, cached: data.usage.cache_read_input_tokens } : null;
  if (data.stop_reason === 'refusal') return json({ answer: 'I can only help with Diablo II questions about your stash — try rephrasing.', note: 'refused', usage }, 200);
  // with web search the model interleaves search blocks + multiple text blocks — join them all.
  const answer = (data.content || [])
    .filter((b) => b.type === 'text' && b.text)
    .map((b) => b.text)
    .join('\n\n')
    .trim() || '(no answer)';
  return json({ answer, usage }, 200);
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'content-type': 'application/json', ...CORS },
  });
}
