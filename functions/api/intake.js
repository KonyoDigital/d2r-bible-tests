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
  const { image, media_type, names, kind, layout, cropped } = body || {};
  try {
  if (!image || typeof image !== 'string') return json({ error: 'missing image' }, 400);
  if (image.length > 1_800_000) return json({ error: 'image too large — downscale client-side' }, 413);
  const isLocate = kind === 'locate';   // v342 — return the hovered tooltip's bounding box (no vocab needed)
  // v354 — cap raised 600→2000: the grail vocab grew past 600 (off-grail uniques + RotW sets) which
  // 400'd EVERY read and hung the intake at 0/62. The vocab rides in the cached system prompt, so a
  // larger list is near-free; 2000 leaves ample headroom.
  if (!isLocate && (!Array.isArray(names) || names.length < 3 || names.length > 2000)) return json({ error: 'names vocabulary required' }, 400);
  const mt = ['image/jpeg', 'image/png', 'image/webp'].includes(media_type) ? media_type : 'image/jpeg';
  const isCraft = kind === 'craft';
  const isTally = (kind === 'tally' || isCraft) && !isLocate;   // craft shares the {tally} count contract

  const itemsText = 'You read Diablo 2 Resurrected screenshots (stash/inventory panels, ground loot, hover tooltips). '
    + 'Extract ITEM NAMES whose text is VISIBLE in the image and return vocabulary matches in "items". STRICT RULES: '
    + '(0) Report an item ONLY where its NAME is shown as clearly-readable TEXT — a hover tooltip, a '
    + 'stash/inventory/vendor/trade window label, a ground-loot label, OR a store/web listing line. NEVER report from '
    + 'item ARTWORK alone: if an item appears only as an icon/graphic with no readable name text next to it, skip it '
    + '(a wrong guess from art is far worse than a miss). '
    + '(0a) DEFAULT EXPECTATION — these screenshots are normally ONE hovered item: a single big tooltip floating over a '
    + 'stash/inventory grid. In that case report EXACTLY ONE thing TOTAL — the hovered tooltip — counting ACROSS every '
    + 'output array COMBINED (items + finds + sockets + unrecognized). The icons in the grid BEHIND the tooltip are bare '
    + 'artwork with NO readable name and NO readable socket text — do NOT enumerate them, do NOT scan the grid for extra '
    + 'items OR extra socketed bases, do NOT pad any list with them. Only the ONE tooltip with legible text counts. '
    + 'Report MORE than one ONLY when MULTIPLE separate, COMPLETE, legible NAME/STAT-TEXT tooltips are genuinely shown at '
    + 'once (rare — e.g. a vendor/trade list of text rows). A full stash with ONE tooltip = ONE result, never several. '
    + '(0b) NEVER report the same item twice from one image; NEVER turn an affix/stat line ("+2 to Skills", "Lightning '
    + 'Resist +30%") or a comparison/equipped tooltip\'s shared affixes into extra item names. If unsure whether two '
    + 'reads are the same item, report it ONCE. When in doubt about a second/third name, OMIT it — under-reporting is '
    + 'correct here, the user will re-screenshot anything missed. '
    + '(1) Report a vocabulary item ONLY if its name appears as readable text — NEVER fuzzy-match a similar-looking '
    + 'string (a base type like "Tyrant Club" is NOT "Tyrael\'s Might"). If text is too small or blurry to read with '
    + 'CERTAINTY, do not guess: omit it or put your literal best transcription in "unrecognized". A wrong match is far '
    + 'worse than a miss — the user can re-screenshot. '
    + '(2) In a tooltip, the ITEM NAME is the TOP line; the line under it is the BASE TYPE (e.g. "Bearded Axe", '
    + '"Bone Shield", "Tyrant Club") — base types are never items, do not report them anywhere. '
    + '(2b) SOCKETED BASES → the "sockets" array. A white/grey/SUPERIOR base whose tooltip shows legible "Socketed (N)" '
    + '/ "Sockets (N)" / "N Sockets" text is a tracked runeword/craft base. Add it to "sockets" as {base:"<the base-type '
    + 'name EXACTLY as printed, e.g. Breast Plate, Broad Sword, Ancient Armor, Grand Scepter, Monarch>", count:N, '
    + 'q:"normal"|"superior"|"magic", eth:true/false}. q = the name COLOUR / prefix: white or grey = "normal", a '
    + '"Superior" prefix = "superior", a BLUE name = "magic". eth = true only if the tooltip says "Ethereal". '
    + 'READ the base name, socket NUMBER, colour, and ethereal flag — do NOT classify the slot, the system does that. CRITICAL: only when the '
    + '"Socketed (N)" TEXT is genuinely legible (normally the ONE hovered tooltip) — NEVER infer sockets from holes drawn '
    + 'on an inventory ICON, and NEVER emit several from a grid of bare icons. v371 — if the ONE hovered tooltip is a '
    + 'white/grey/SUPERIOR/magic BASE that shows NO socket text, STILL report it in "sockets" with count:0 (the system '
    + 'keeps only worthwhile elite runeword bases to Larzuk later and ignores common junk) — but ONLY that single hovered '
    + 'tooltip, NEVER zero-socket bare grid icons. '
    + 'Do NOT also put a socketed base\'s name in "unrecognized". '
    + '(3) Ignore NPC name labels (Charsi, Kashya, Warriv, Akara, Gheed the NPC...), zone names, UI text, gold, potions. '
    + '(4) Item ART without readable name text is NOT enough — skip it. '
    + '(5) MAGIC & RARE KEEPERS → the "finds" array (NOT "items", NOT "unrecognized"). If the hovered item is '
    + 'a MAGIC (blue name), RARE (yellow name), or CRAFTED (orange name) item that is a CHARM (small/large/grand '
    + 'charm), a JEWEL, a RING, an AMULET, OR a notably-affixed rare/crafted weapon or armour a player would keep, '
    + 'add it to "finds" as {name:"<the full name text EXACTLY as printed>", q:"magic"|"rare"|"crafted", '
    + 'base:"<the BASE TYPE printed under the name, e.g. Grand Charm, Small Charm, Ring, Amulet, Jewel, Cryptic Axe, '
    + 'Circlet>", mods:["<each KEY stat line read VERBATIM off the tooltip>"]} (q from the name COLOUR: '
    + 'blue=magic, yellow=rare, orange=crafted; base = the grey base-type line). '
    + 'For "mods": transcribe the item\'s VISIBLE blue/affix stat lines exactly as printed, in order — e.g. '
    + '["+1 to Javelin and Spear Skills"], or ["+20% Faster Cast Rate","+45 to Life","All Resistances +12"]. '
    + 'This is what makes a skiller / rare worth keeping, so capture it. Only lines ACTUALLY printed on the tooltip '
    + '(never invent or infer a stat); if no stat lines are legible, use an empty array []. '
    + 'Do NOT put white/grey/superior or normal base items, '
    + 'potions, gold, gems, runes, or NPC names in "finds". A grail unique/set ALWAYS goes in "items", never "finds". '
    + 'EXTRA CARE for valuable uniques/sets: when a UNIQUE or SET name is legible, match it to "items" and never drop it '
    + 'into "unrecognized" or "finds" — re-read it against the vocabulary first (e.g. helms, rings, amulets like a demon-head '
    + 'helm, a frost ring, a caster amulet are high-value staples). Losing a legible valuable item is a costly error. '
    + 'Never list the same name in both "finds" and "unrecognized". '
    + 'Put a string in "unrecognized" ONLY when it is a FULLY-LEGIBLE, COMPLETE item name you read '
    + 'character-by-character that simply is not in the vocabulary AND is not a magic/rare keeper for "finds" — NEVER '
    + 'a partial read, an inferred/autocompleted name, or a guess. If you are not certain a real item name is printed '
    + 'there, omit it entirely. Inventing plausible-sounding names (fake set/unique names) is the worst possible error. '
    + 'VOCABULARY:\n' + names.join('\n');

  const tallyText = 'You read a Diablo 2 Resurrected screenshot showing RUNES and/or GEMS — usually a dedicated organized '
    + 'stash tab (the Runes tab or Gems tab), or a stash/inventory grid. Return a "tally" array of {name, count} for '
    + 'every rune/gem you can identify. '
    + 'TRANSCRIBE, NEVER FABRICATE: report ONLY the digits you can actually SEE printed in a cell. Never guess, estimate, '
    + 'round, average, or fill in a "likely" or "typical" count. If a number is hard to read, zoom your attention to that '
    + 'one cell and read it again — but report what is genuinely printed there, not a plausible guess. An accurate "I read '
    + 'a 7" beats a confident wrong number. '
    + 'HOW TO COUNT — THIS IS THE MOST IMPORTANT PART, READ CAREFULLY: '
    + '(1) In D2R\'s organized RUNES and GEMS stash tabs each rune/gem type sits in ONE fixed cell, and the QUANTITY you '
    + 'own is printed as a small STACK-COUNT NUMBER, usually in the lower-RIGHT corner of that cell (e.g. a Tal rune cell '
    + 'showing "23" means you own TWENTY-THREE Tal runes — NOT one). '
    + '(2) count = that printed stack number. READ THE DIGITS CAREFULLY — stack counts are frequently TWO DIGITS '
    + '(3, 7, 11, 15, 16, 17, 19, 22, 23 …). DO NOT assume every stack is 1 or 2 — that is the most common mistake. '
    + 'Look at each cell\'s corner number and transcribe exactly what is printed. '
    + '(3) THE COUNT IS THE PRINTED NUMBER (CRITICAL): in this organized stash, every rune/gem you OWN shows a stack count '
    + 'in its corner — YES, even a single one prints "1". So read the exact number printed and report that. Do NOT invent a '
    + 'count for a cell that shows none. '
    + '(4) If the SAME item also appears loose across several separate cells (a normal inventory), ADD those cells together. '
    + '(5) UNOWNED = NO NUMBER + GREYED/DIFFERENT TINT → count 0, SKIP IT (report nothing). An item you do NOT own is drawn as '
    + 'a DESATURATED, dull, GREYED-OUT placeholder with NO number — it visibly stands out as the only washed-out / different-tint '
    + 'icon among the vivid, saturated owned ones. A grey "ghost" gem with no number is ZERO — never report it as 1. (Classic '
    + 'case: a single grey Perfect Diamond placeholder sitting among vivid, numbered Perfect gems — that Diamond is 0.) '
    + 'IDENTIFY & COVERAGE: '
    + '(6) Identify each rune by its engraved glyph (gems by tint = type, cut = grade) and any readable name. '
    + 'SCAN THE ENTIRE GRID top-to-bottom and LEFT-to-right, including the rare high runes near the BOTTOM rows '
    + '(Vex, Ohm, Lo, Sur, Ber, Jah, Cham, Zod) — do not stop early. Report every cell that has a real (non-greyed) icon. '
    + 'CRITICAL — THE LAST ROW(S): the bottom rows hold the rare HIGH RUNES and are the most error-prone. Work the bottom '
    + 'rows LAST and SLOWEST: take each bottom cell one at a time, read its glyph, then read its corner stack-number on its '
    + 'own, and write that exact pair down. These high runes are the most valuable, so a wrong digit here matters most — '
    + 'do not rush or batch the final row. '
    + 'ISOLATED CORNER RUNES: the highest runes often sit ALONE in a bottom corner cell, set apart from the main grid by the '
    + 'central cube panel — never skip these. For each isolated/bottom rune the 1-vs-2 read is the classic slip: a stack of '
    + 'TWO prints a small "2" in the corner; report 1 ONLY if the badge is unmistakably "1" or truly absent. If you see any '
    + 'digit badge at all, read it as the number it shows (a faint "2" is still 2, not 1). Zoom your attention onto that '
    + 'corner number and commit to the digit you actually see. '
    + '(7) Only report a vocabulary entry you can identify with CONFIDENCE; if two look too similar to tell apart, put your '
    + 'best transcription in "unrecognized" rather than guessing the wrong rune. '
    + '(8) Only names from the vocabulary. Ignore gold, potions, UI text, non-rune/non-gem items. Readable-but-not-in-vocab → "unrecognized". '
    + '(9) DOUBLE-CHECK BEFORE RETURNING: re-read every stack number one more time, cell by cell. The single most common '
    + 'error is misreading ONE digit — 5 vs 6, 11 vs 17, 22 vs 23, 3 vs 8. Transcribe exactly the digits printed; never '
    + 'round, average, or estimate a stack you cannot read — leave it out rather than guess a number. '
    + (layout === 'runes'
      ? '(10) FIXED LAYOUT — IDENTIFY BY POSITION, NOT GLYPH: this is D2R\'s dedicated RUNES stash tab, where the 33 '
        + 'runes ALWAYS occupy these exact cells in this exact order (independent of which you own). Read each cell\'s '
        + 'POSITION to know which rune it is — do NOT rely on glyph similarity (Jah/Cham, Vex/Lo, Sur/Ber, Ohm/Ist look '
        + 'alike and are easily swapped by glyph, but NEVER by position):\n'
        + '  Row 1 (9 cells, left→right): El, Eld, Tir, Nef, Eth, Ith, Tal, Ral, Ort\n'
        + '  Row 2 (9 cells): Thul, Amn, Sol, Shael, Dol, Hel, Io, Lum, Ko\n'
        + '  Row 3 (9 cells): Fal, Lem, Pul, Um, Mal, Ist, Gul, Vex, Ohm\n'
        + '  Row 4: the central cube panel SPLITS this row. The two cells on the far LEFT are Lo then Sur. The two cells '
        + 'on the far RIGHT are Ber then Jah.\n'
        + '  Row 5: ONE lone cell on the far LEFT is Cham. ONE lone cell on the far RIGHT is Zod.\n'
        + 'So: the bottom-left lone rune is ALWAYS Cham; the bottom-right lone rune is ALWAYS Zod; the rightmost rune of '
        + 'row 4 is ALWAYS Jah. For each occupied cell, report the rune that owns that position + its stack number; skip '
        + 'empty/greyed cells. If the screenshot is clearly NOT this fixed runes-tab grid, fall back to glyph reading. '
      : layout === 'gems'
      ? '(10) FIXED LAYOUT — IDENTIFY BY POSITION: this is D2R\'s dedicated GEMS stash tab, a 7-COLUMN x 5-ROW grid. '
        + 'COLUMNS are gem TYPES, left→right: Diamond, Emerald, Ruby, Topaz, Amethyst, Sapphire, Skull. ROWS are GRADES, '
        + 'top→bottom: Chipped, Flawed, standard (NO grade word — e.g. just "Ruby"), Flawless, Perfect. So column 5 / '
        + 'row 5 = "Perfect Amethyst"; column 3 / row 1 = "Chipped Ruby"; column 1 / row 3 = "Diamond". Use the COLUMN '
        + 'to fix the type and the ROW to fix the grade — do NOT judge grade from the gem\'s cut/size, which makes '
        + 'chipped/flawed/flawless easy to confuse; the row position is exact. Type colours: Diamond=clear/white, '
        + 'Emerald=green, Ruby=red, Topaz=yellow, Amethyst=purple, Sapphire=blue, Skull=bone-grey. For each occupied '
        + 'cell, report the vocabulary name for that type+grade + its stack number; skip empty cells. '
        + 'BOTTOM (PERFECT) ROW — judge each of the 7 cells by whether it shows a NUMBER (rules 3 & 5): a vivid, saturated '
        + 'Perfect gem WITH a printed number = owned → report that number. A grey / desaturated / different-tint placeholder '
        + 'WITH NO number = NOT owned → 0, SKIP it. The unowned one is obvious: it is the single dull, washed-out gem sitting '
        + 'among the bright numbered ones. Common real case: Perfect Emerald/Ruby/Topaz/Amethyst/Sapphire/Skull each show "1" '
        + 'while Perfect DIAMOND is a grey ghost with no number → report the six as 1 and DROP the Diamond (0). Never count a '
        + 'numberless grey placeholder as 1. If the screenshot is clearly NOT this fixed 7x5 gems grid, fall back to visual reading. '
      : '')
    + 'VOCABULARY:\n' + names.join('\n');

  const craftText = 'You read Diablo 2 Resurrected screenshots to find CRAFTED ITEMS the player owns and classify each by its '
    + 'CRAFT TYPE and EQUIPMENT SLOT. A crafted item is a RARE item (yellow two-word random name) made in the Horadric '
    + 'Cube; it is identified ONLY by the GUARANTEED MODS its craft always rolls. Return a "tally" array of {name, count} '
    + 'where each name is exactly one vocabulary string of the form "<Craft> <Slot>" (e.g. "Caster Amulet", "Blood Ring"). '
    + 'YOU MUST READ AFFIX TEXT — a hover TOOLTIP (or a readable rare-item stat list) must be visible. If no readable stat '
    + 'text is present, return {"tally":[],"unrecognized":[]} — item ART alone is NEVER classifiable. '
    + 'THE FOUR CRAFTS — match by these telltale GUARANTEED mods (a craft must show its signature mod): '
    + '(A) CASTER → has BOTH "Faster Cast Rate" AND ("Regenerate Mana" or "+N to Mana"). '
    + '(B) BLOOD → has "Life Stolen per Hit" (life leech) AND ("+N to Life", often with "Crushing Blow" or "Open Wounds"). '
    + '(C) SAFETY → has "Magic Damage Reduced by N" AND "Damage Reduced by N" (flat physical DR). The Magic-Damage-Reduced line is the strongest tell. '
    + '(D) HIT POWER → has "Chance to Cast" a "Frost Nova" "when struck" AND "Attacker Takes Damage". '
    + 'If an item shows none of these signatures, it is NOT a crafted item — skip it (a normal magic/rare/unique drop is not crafted). '
    + 'THE SLOT — read the item BASE TYPE (the line under the name) and map it to ONE slot word: '
    + 'Amulet, Ring, Weapon (any sword/axe/mace/club/hammer/scepter/wand/staff/spear/javelin/bow/etc.), '
    + 'Shield (any shield), Helm (any helm/cap/crown/mask/circlet), "Body Armor" (any chest/plate/mail/armor), '
    + 'Gloves (gloves/gauntlets/bracers), Belt (belt/sash/girdle), Boots (boots/greaves). '
    + 'COUNT: if several separate crafted items share the same Craft+Slot, ADD them (each tooltip/cell = the items it shows). '
    + 'Only emit names that exist in the vocabulary. A readable crafted item whose craft you cannot confidently classify → "unrecognized". '
    + 'VOCABULARY:\n' + names.join('\n');

  const itemsSchema = {
    type: 'object',
    properties: {
      items: { type: 'array', items: { type: 'string' } },
      unrecognized: { type: 'array', items: { type: 'string' } },
      // v342.3 — magic/rare/crafted KEEPERS (charms, jewels, rings, amulets, notable rares). These have
      // randomly-rolled names so they can't be grail-DB entries; tracked in their own Magic & Rare bucket.
      finds: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            name: { type: 'string' },
            q: { type: 'string', enum: ['magic', 'rare', 'crafted'] },
            base: { type: 'string' },   // v342.8 — the base TYPE (Grand Charm, Ring, Cryptic Axe…) → drives the art sprite
            // v356 — the item's KEY visible stat lines read VERBATIM off the tooltip (e.g. the +skills on a
            // skiller). So a magic/rare keeper shows its real affixes, not a name-based guess.
            mods: { type: 'array', items: { type: 'string' } },
          },
          required: ['name', 'q', 'base', 'mods'],
          additionalProperties: false,
        },
      },
      sockets: {   // v342.12 — white/superior runeword/craft bases with readable "Socketed (N)" text
        type: 'array',
        items: {
          type: 'object',
          properties: {
            base: { type: 'string' },
            count: { type: 'integer' },
            q: { type: 'string', enum: ['normal', 'superior', 'magic'] },   // v342.13 — name colour
            eth: { type: 'boolean' },                                       // v342.13 — Ethereal?
          },
          required: ['base', 'count', 'q', 'eth'],
          additionalProperties: false,
        },
      },
    },
    required: ['items', 'unrecognized', 'finds', 'sockets'],
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

  // v342 — LOCATE mode: find the single hovered item DESCRIPTION TOOLTIP so the client can crop+enlarge
  // it (the runes/gems calibration, adapted — the tooltip floats instead of sitting in a fixed grid).
  const locateText = 'You are given ONE Diablo II Resurrected screenshot. The player is hovering the mouse '
    + 'over a SINGLE item, so the game draws ONE floating DESCRIPTION TOOLTIP: a dark, semi-transparent stat '
    + 'panel with the item NAME in a coloured header at the TOP and several stat lines below it. YOUR ONLY JOB '
    + 'is to return the bounding box of that hovered tooltip so it can be cropped out and enlarged for reading. '
    + 'Return found=true and x0,y0,x1,y1 as FRACTIONS of image width/height (0 = left/top, 1 = right/bottom) that '
    + 'enclose the WHOLE tooltip panel — the coloured name header AND every stat line down to the bottom edge. '
    + 'ERR GENEROUS: it is far better to include extra surrounding area than to clip ANY edge — never cut off the '
    + 'name header or the bottom stat line. If there is NO single floating item tooltip (a plain grid with nothing '
    + 'hovered, a vendor/trade list of text rows, or several tooltips at once), return found=false with zeros.';
  const locateSchema = {
    type: 'object',
    properties: {
      found: { type: 'boolean' },
      x0: { type: 'number' }, y0: { type: 'number' }, x1: { type: 'number' }, y1: { type: 'number' },
    },
    required: ['found', 'x0', 'y0', 'x1', 'y1'],
    additionalProperties: false,
  };

  const sysText = isLocate ? locateText : isCraft ? craftText : isTally ? tallyText : itemsText;
  const system = [{ type: 'text', text: sysText, cache_control: { type: 'ephemeral' } }];

  const apiResp = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': env.ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      // v341.66 — back to Sonnet for good. Opus reads digits more accurately (verified) BUT keeps
      // breaking the upload in this serverless worker — even capped at 2 passes it intermittently
      // hangs/fails ("not working", reported repeatedly). Reliability wins: Sonnet loads fast every
      // time. The Perfect/high row is handled by the tight crop + fixed-position ID + the ✓? verify-
      // flag + a one-tap −/+ nudge. env.MODEL=claude-opus-4-8 if you ever want to force Opus.
      // v342.2 — model per JOB:
      //  • LOCATE  → Haiku (just box-finding, no text).
      //  • ITEMS   → Haiku — the vault loot read is now an EASY task (we crop+enlarge to ONE clean tooltip),
      //              so the cheap model reads it fine at 3× lower cost. Konyo: "do haiku, more logical for these."
      //  • TALLY/CRAFT → Sonnet — digit COUNTING ("23" vs "2") is the error-prone job; keep the stronger,
      //              already-calibrated model. (env overrides: LOCATE_MODEL / ITEMS_MODEL / MODEL.)
      model: isLocate ? (env.LOCATE_MODEL || 'claude-haiku-4-5')
        : isTally ? (env.MODEL || 'claude-sonnet-4-6')
        : (env.ITEMS_MODEL || 'claude-haiku-4-5'),
      max_tokens: 2048,
      // v342.26 — temperature 0 (greedy decode) so the SAME screenshot reads the SAME way run-to-run.
      // The old default (1.0) sampled, so re-scanning a batch could re-assort borderline items
      // (e.g. a rare flipping magic&rare↔grail) differently each pass. For "read what's in this image"
      // we want the single most-likely answer, not a varied one. Not 100% bit-identical (inference-layer
      // non-determinism remains) but it removes the run-to-run wobble.
      temperature: 0,
      system,
      output_config: { format: { type: 'json_schema', schema: isLocate ? locateSchema : isTally ? tallySchema : itemsSchema } },
      messages: [{
        role: 'user',
        content: [
          { type: 'image', source: { type: 'base64', media_type: mt, data: image } },
          { type: 'text', text: isLocate ? 'Return the bounding box of the single hovered item description tooltip in this screenshot. Err generous so no edge is clipped.' : isCraft ? 'Find every CRAFTED item in this screenshot. For each one, read its visible mods, decide its craft type from the guaranteed-mod signatures, read its base type to get the slot, and tally it as "<Craft> <Slot>". Only count items whose stat text is readable and whose mods match a craft signature.' : isTally ? 'Tally every rune/gem in this screenshot. For each cell, READ the small stack-count number printed in its corner and use THAT as the count (it is often two digits like 11, 17, 23 — do not assume 1 or 2). Scan the whole grid including the high runes at the bottom.' : (cropped ? 'This image has been CROPPED to a SINGLE hovered item tooltip. Read and return EXACTLY ONE thing TOTAL across all arrays — the item in this tooltip. Any partial icons or grid art at the edges are background; ignore them completely.' : 'Extract the item names from this screenshot.') },
        ],
      }],
    }),
  });

  if (!apiResp.ok) {
    const errText = await apiResp.text();
    // v341.52 — return 200 (NOT 5xx): Cloudflare overwrites any 5xx the worker returns with its own
    // generic "error code: 502" page, which masks the real upstream reason and makes the upload look
    // dead. A 200 with error fields passes straight through so the client can read + show the reason.
    return json({ error: 'upstream', status: apiResp.status, detail: errText.slice(0, 300), tally: {}, items: [], unrecognized: [] }, 200);
  }
  const data = await apiResp.json();
  const usage = data.usage ? { in: data.usage.input_tokens, out: data.usage.output_tokens, cached: data.usage.cache_read_input_tokens } : null;
  if (data.stop_reason === 'refusal') return json(isLocate ? { found: false, box: [0, 0, 0, 0], note: 'refused' } : isTally ? { tally: {}, unrecognized: [], note: 'refused' } : { items: [], unrecognized: [], note: 'refused' }, 200);
  const textBlock = (data.content || []).find((b) => b.type === 'text');
  let parsed = {};
  try { parsed = JSON.parse(textBlock ? textBlock.text : '{}'); } catch {}

  if (isLocate) {
    const f = !!parsed.found;
    const num = (v) => { const n = Number(v); return isFinite(n) ? Math.min(1, Math.max(0, n)) : 0; };
    return json({ found: f, box: f ? [num(parsed.x0), num(parsed.y0), num(parsed.x1), num(parsed.y1)] : [0, 0, 0, 0], usage }, 200);
  }

  // Vocab matching — NEVER drop a read silently (the Frostburn lesson): resolve via
  // (1) exact, (2) normalized (case/punct-insensitive), (3) vocab-name-is-prefix at a
  // word boundary (min 6 chars, longest match wins). Unmatched → "unrecognized".
  const vocab = new Set(names);
  const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  const normMap = new Map(names.map((n) => [norm(n), n]));
  const sortedVocab = names.map((n) => [norm(n), n]).filter(([k]) => k.length >= 6)
    .sort((a, b) => b[0].length - a[0].length);
  // v342.10 — vocab names with a trailing "(base)" suffix ("Gull (dagger)", "Harlequin Crest (Shako)")
  // keyed by the SUFFIX-STRIPPED form, so a read of just "Gull" / "Harlequin Crest" resolves. First wins.
  const baseStripMap = new Map();
  names.forEach((n) => {
    const stripped = norm(n.replace(/\s*\([^)]*\)\s*$/, ''));
    if (stripped && stripped !== norm(n) && stripped.length >= 4 && !baseStripMap.has(stripped)) baseStripMap.set(stripped, n);
  });
  const resolve = (r) => {
    if (vocab.has(r)) return r;
    const nr = norm(r);
    if (normMap.has(nr)) return normMap.get(nr);
    if (baseStripMap.has(nr)) return baseStripMap.get(nr);
    const hit = sortedVocab.find(([k]) => nr === k || nr.startsWith(k + ' '));
    return hit ? hit[1] : null;
  };
  // v342.7 — reject garbage strings (JSON/prompt fragments, mojibake) the model occasionally leaks,
  // e.g. ">:", "FINDINGS ITEM=", "Defene([", "conce}},CKED (BONE". A real item name is mostly letters.
  const nameOk = (s) => {
    s = String(s == null ? '' : s).trim();
    if (s.length < 2 || s.length > 60) return false;
    if (!/[a-zA-Z]/.test(s)) return false;
    if (/[{}\[\]=<>|\\]/.test(s)) return false;
    const nonSpace = s.replace(/\s/g, '');
    const letters = (s.match(/[a-zA-Z]/g) || []).length;
    return nonSpace.length > 0 && letters >= nonSpace.length * 0.6;
  };
  // v342.12 — deterministically classify a SOCKETED base name → the generic "Socketed <slot> (Nos)" vocab
  // entry, so white/superior runeword bases register to the SOCKETED locker instead of dropping to unmatched.
  const socketGeneric = (base, count) => {
    const b = String(base || '').toLowerCase();
    if (!b) return null;
    const n = parseInt(count, 10);
    const os = (n >= 1 && n <= 6) ? ' (' + n + 'os)' : '';
    let kind = null;
    if (/shield|buckler|rondache|targe|aegis|\bward\b|scutum|defender|heater|luna|pavise|monarch|\bnest\b|kite|tower|spiked club shield|gothic shield|barbed shield|dragon shield|bone shield|grim shield|ancient shield|round shield|small shield|large shield/.test(b)) kind = 'Socketed Shield';
    else if (/helm|\bcap\b|crown|mask|circlet|coronet|tiara|diadem|casque|basinet|sallet|armet|visage|\bskull\b|shako|coif|cowl|\bhood\b|demon head|bone helm|war hat|sallet|winged helm|grand crown|spired helm/.test(b)) kind = 'Socketed Helm';
    else if (/armor|plate|mail|hauberk|tunic|jupon|cuirass|shroud|\bhide\b|pelt|shell|carapace|fleece|husk|scale|splint|\bfield\b|kraken|lacquered|wyrmhide|\bdusk\b|trellised|linked|tigulated|russet|breast|chaos|sacred armor|wire fleece|scarab husk|diamond mail|loricated|boneweave|great hauberk|balrog skin/.test(b)) kind = 'Socketed Body Armor';
    else if (/polearm|poleaxe|halberd|scythe|thresher|voulge|bardiche|partizan|\bbill\b|spear|pike|lance|trident|brandistock|spetum|fuscina|harpoon|stave|staff|\bbow\b|crossbow|maul|war hammer|two.?hand|great sword|zweihander|flamberge|colossus sword|colossus blade|tusk sword|espandon|great poleaxe|giant thresher|ogre axe|colossus voulge|war pike|ghost spear|stygian pike|mancatcher|war scythe|battle scythe|grim scythe|cryptic axe|great axe|glorious axe|ettin axe|small crescent|war spear/.test(b)) kind = 'Socketed 2H Weapon';
    else if (/sword|axe|mace|scepter|sceptre|wand|dagger|knife|club|hammer|flail|blade|saber|sabre|falchion|tulwar|cutlass|baton|crowbill|hatchet|cleaver|\bclaw\b|katar|morning star|war club|flanged mace|jagged star|knout|tomahawk|naga|military pick|gladius|rune sword|ataghan|elegant blade|legend sword|highland blade/.test(b)) kind = 'Socketed 1H Weapon';
    if (!kind) return null;
    // prefer the count-specific vocab entry, else the count-less generic
    return resolve(kind + os) || resolve(kind);
  };
  // v371 — a worthwhile base hovered with ZERO sockets = a LARZUK CANDIDATE (keep it, socket it later).
  // Reuse socketGeneric's slot classification, but emit a distinct "Larzuk <slot> Base" label so it reads
  // as UNSOCKETED in the SOCKETED locker. (Konyo's calibration: track elite 0-socket bases, ignore junk.)
  const larzukGeneric = (base) => {
    const g = socketGeneric(base, 0);   // → "Socketed Shield" / "Socketed 2H Weapon" / … (count-less)
    if (!g) return null;
    return g.replace(/^Socketed (.+)$/, 'Larzuk $1 Base');
  };
  // v342.13 — sunder charms are account-shared keepers (NOT muled, NOT rolled-name rares). Detect by type.
  const SUNDER_TYPES = ['Cold Rupture', 'Flame Rift', 'Crack of the Heavens', 'Rotting Fissure', 'Bone Break', 'Black Cleft'];
  const sunderOf = (s) => { const l = String(s || '').toLowerCase(); return SUNDER_TYPES.find((t) => l.includes(t.toLowerCase())) || null; };
  // v342.13 — only WORTHWHILE socketed bases register: elite / high-defense / notable runeword bases.
  // Low white junk (Breast Plate, Broad Sword, Ring Mail…) is skipped → goes to the unmatched review list.
  const GOOD_BASE = /archon plate|sacred armor|kraken shell|hellforge plate|lacquered plate|shadow plate|dusk shroud|wyrmhide|scarab husk|wire fleece|diamond mail|loricated mail|boneweave|great hauberk|balrog skin|mage plate|ornate plate|chaos armor|\bdiadem\b|\btiara\b|corona|spired helm|\barmet\b|giant conch|demon ?head|bone visage|conqueror crown|circlet|\bmonarch\b|\baegis\b|\bward\b|troll nest|grim shield|blade barrier|sacred targe|sacred rondache|\bhyperion\b|\bluna\b|phase blade|colossus blade|colossus sword|cryptic sword|mythical sword|legend sword|highland blade|balrog blade|champion sword|conquest sword|dimensional blade|cryptic axe|berserker axe|feral axe|silver.?edged axe|decapitator|champion axe|glorious axe|thunder maul|ogre maul|great poleaxe|giant thresher|\bthresher\b|colossus voulge|war pike|ghost spear|stygian pike|mancatcher|caduceus|mighty scepter|elder staff|archon staff/i;

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
  // v342.4 — also resolve the AI's OWN "unrecognized" strings: a "name + base type" read
  // ("Spectral Shard Blade") recovers into the real grail item (Spectral Shard) via the same
  // word-boundary prefix matcher, instead of being silently lost. No match → stays unrecognized.
  for (const r of (parsed.unrecognized || [])) {
    const nm = resolve(r);
    if (nm) { if (!items.includes(nm)) items.push(nm); } else unrec.push(r);
  }
  // v342.3 — magic/rare/crafted keepers: sanitize, dedupe by name, drop any that resolve to a real grail item
  // (those belong in items) or that are blank.
  const finds = [];
  const seenFind = new Set();
  for (const f of (parsed.finds || [])) {
    const nm = f && typeof f.name === 'string' ? f.name.trim() : '';
    if (!nm || !nameOk(nm) || seenFind.has(nm.toLowerCase())) continue;
    // v342.13 — sunder charms → items as their canonical type (shared-stash, never muled), NOT a magic find
    const sun = sunderOf(nm);
    if (sun) { if (!items.includes(sun)) items.push(sun); seenFind.add(nm.toLowerCase()); continue; }
    if (resolve(nm)) { if (!items.includes(resolve(nm))) items.push(resolve(nm)); continue; }
    seenFind.add(nm.toLowerCase());
    // v356 — carry the verbatim stat lines (max 8, sanitized) so the keeper card shows the real affixes.
    const mods = Array.isArray(f.mods)
      ? f.mods.map((m) => String(m == null ? '' : m).trim()).filter((m) => m && m.length <= 80).slice(0, 8)
      : [];
    finds.push({ name: nm.slice(0, 80), q: ['magic', 'rare', 'crafted'].includes(f.q) ? f.q : 'magic', base: typeof f.base === 'string' ? f.base.slice(0, 40) : '', mods });
  }
  // v342.12 — socketed runeword/craft bases → register the generic "Socketed <slot> (Nos)" entry (SOCKETED
  // locker). The AI read base+count; we classify the slot. Track the base names to scrub from unrecognized.
  const socketBaseLower = new Set();
  for (const s of (parsed.sockets || [])) {
    const base = s && typeof s.base === 'string' ? s.base.trim() : '';
    if (!base) continue;
    // v342.13 — only register WORTHWHILE bases: magic (affixes, for gemming) OR ethereal OR an elite/notable
    // runeword base (Archon Plate, Monarch, Cryptic Axe, Grim Shield…). Low white junk → unmatched review.
    // v368 — ALSO keep any HIGH-SOCKET base (5-6 sockets): those are rare (need high ilvl / Larzuk) and
    // enable top runewords regardless of base type — a 6os one-handed sword makes Breath of the Dying, etc.
    // (Konyo: "isn't a 6-socket Dimensional Blade a good runeword base?" — yes; the type-only filter was
    // discarding good high-socket bases. Socket count matters as much as base type.)
    const _sc = parseInt(s.count, 10);
    const cnt = isFinite(_sc) ? _sc : 0;
    const eliteOrMagic = s.q === 'magic' || s.eth === true || GOOD_BASE.test(base);
    // v371 — ZERO-socket base: keep ONLY an elite/magic/eth one as a LARZUK CANDIDATE (you'd socket it
    // later); ignore common 0-socket junk entirely (don't even surface it in throw-out review). Konyo's
    // "track elite, ignore junk" calibration. (Junk WITH sockets still goes to the low-base review below.)
    if (cnt <= 0) {
      if (!eliteOrMagic) continue;
      socketBaseLower.add(base.toLowerCase());
      const lg = larzukGeneric(base);
      if (lg && !items.includes(lg)) items.push(lg);
      continue;
    }
    const worth = eliteOrMagic || cnt >= 5;
    if (!worth) { unrec.push(base + ' (' + (s.count || '?') + 'os low base)'); continue; }
    socketBaseLower.add(base.toLowerCase());
    const gen = socketGeneric(base, s.count);
    if (gen && !items.includes(gen)) items.push(gen);
  }
  // v342.7 — clean unrecognized: drop garbage strings, anything already captured as a Magic & Rare find,
  // and any socketed-base name (the model sometimes echoes the base name into unrecognized too).
  const findLower = new Set(finds.map((f) => f.name.toLowerCase()));
  const cleanUnrec = [...new Set(unrec)].filter((u) => {
    const ul = String(u).toLowerCase();
    return nameOk(u) && !findLower.has(ul) && !socketBaseLower.has(ul);
  });
  let outItems = [...new Set(items)];
  let outFinds = finds.slice(0, 40);
  let outUnrec = cleanUnrec.slice(0, 40);
  // v343 — SINGLE-TOOLTIP DISCIPLINE: when the client cropped the image to ONE located tooltip
  // (cropped=true), the screenshot shows exactly ONE hovered item, so it must register exactly ONE
  // thing. Keep the single best read and discard the rest as background-grid noise — this is the
  // chronic over-count (62 single-item shots registering 65+ via phantom throw-out reads). Priority:
  // grail item > magic/rare find > socketed/unrecognized. NOT applied to full-image reads (cropped
  // false: LOCATE returns found=false for a vendor/trade list, which can legitimately hold many rows).
  if (cropped) {
    if (outItems.length) { outItems = outItems.slice(0, 1); outFinds = []; outUnrec = []; }
    else if (outFinds.length) { outFinds = outFinds.slice(0, 1); outUnrec = []; }
    else { outUnrec = outUnrec.slice(0, 1); }
  }
  return json({
    items: outItems,
    unrecognized: outUnrec,
    finds: outFinds,
    usage,
  }, 200);
  } catch (e) {
    // graceful 200 (not 5xx, which Cloudflare masks) so the client sees the real failure
    return json({ error: 'worker-exception', message: String((e && e.message) || e), tally: {}, items: [], unrecognized: [] }, 200);
  }
}

function json(obj, status) {
  return new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json', ...CORS } });
}
