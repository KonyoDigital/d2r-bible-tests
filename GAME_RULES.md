# D2R Bible — Game Rules & Facts (RoW canonical reference)

> **Living knowledge base.** The durable, game-truth facts the app encodes — so any
> agent (Claude Code, Claude Desktop) can build on a solid foundation without
> re-deriving the rules. Konyo plays **Reign of the Warlock (RoW / ROTW)**, NOT
> vanilla D2R. Sources: diablo2.io, Maxroll, silospen, in-game. **ZERO fabrication** —
> if a number isn't sourced, it's marked qualitative, never invented.
>
> Companion docs: `BUILD_LOG.md` (what shipped, dated), `BUGS.md` (regression log).

## Tabs / structure of bible.html
- Single-file HTML app. Top-level tabs: bosses, calc, tz, runes, rotw, ancients
  (events/uber), endgame (storyline "Road to the Hellfire Torch"), reference, binds.
- Central routers: `openDrop(name)` resolves a drop → its card
  (findHeraldTier → findRune → findMaterial → ITEMS); `switchTab(id)`;
  `artOr(name, fallbackHtml, size)` art helper (lg/sm). **Site-wide blast radius.**

---

## RoW endgame — the Colossal Ancients chain (pinnacle)

### Colossal Statues (cube material)
Five element-themed statues, each drops from a **TERRORIZED Hell act boss only**
(~1:8 to 1:15 per kill; **MF does NOT affect**; never drops un-terrorized):
| Statue | Drops from (terrorized Hell) |
|---|---|
| Talic's Anguish | Andariel |
| Korlic's Pain | Duriel |
| Madawc's Ire | Mephisto |
| Bul-Kathos' Nightmare | Diablo |
| Worusk's End | Baal |
Cube all 5 → **Colossal Summit** → Act 5 red portal → summon the **Colossal Ancients**.
Statues carry no equip stats — pure cube ingredient gating the whole RoW endgame.

### Colossal Ancients (the 3 bosses)
Buffed Ancient Barbarians; re-roll stats + **one random immunity each game** (like
vanilla Ancients — leave+remake to re-roll if all three share an unbreakable immunity).
mlvl Colossal (drop lvl-75 jewels), massively buffed HP/def. You receive the jewel
matching the Ancient you kill **LAST**.
| Ancient | Weapon / style | Drops (by last kill) |
|---|---|---|
| Talic | sword & shield · Whirlwind | Defender's Fire (fire) / Defender's Bile (poison) |
| Korlic | polearm · Leap Attack | Protector's Frost (cold) / Protector's Stone (physical) |
| Madawc | dual throwing axes · caster | Guardian's Thunder (lightning) / Guardian's Light (magic) |

### Colossal Ancient Jewels (endgame BiS — strictly better than Rainbow Facets)
ilvl 75. **1 per character** (you keep the one matching the last Ancient killed).
**Every** jewel shares: 1% chance-to-cast its element armor when struck · +its element
damage · +5-10% to that skill-damage type · -5-10% to enemy element resistance ·
+3-5% experience · +25-50% extra gold · +15-35% magic find.
| Jewel | Element | CtC armor (lvl) | +element damage |
|---|---|---|---|
| Defender's Bile | poison | Bone Armor (25) | +95 poison over 1s |
| Guardian's Thunder | lightning | Cyclone Armor (25) | +1-75 lightning |
| Protector's Frost | cold | Frozen Armor (25) | +10-30 cold |
| Defender's Fire | fire | Blaze (25) | +20-60 fire |
| Protector's Stone | physical | Fade (15) | +30-50% ED, +10-30 (min/max) · -5-10% enemy phys-dmg reduction |
| Guardian's Light | magic | Psychic Ward (25) | +15-35 magic |
(Protector's Stone is the physical variant: enhanced damage + flat damage instead of
+skill%, and its "enemy res" line is -enemy physical damage reduction.)

---

## Herald of Terror & Sunder Charms (RoW immunity-breaking)

### Herald ladder (5 Hell-TZ superunique rungs)
Spawn only in **Hell Terror Zones**. Two-step hidden token system:
1. **Draw its ire (~2%)** — every Champion/Unique/Superunique/Boss killed in the active
   Hell TZ has ~2% to bank a token ("You have drawn the ire of a Herald!"). Stacks ×5.
2. **Let it hunt you (~1%)** — while holding a token, each monster spawned on a fresh
   unexplored tile has ~1% to become a Herald. Reveal new ground, don't grind.
Each kill bumps the **next** Herald one tier: Fright → Dread → Fear → Horror → **Terror**.
Tiers reset to Fright if you exit to main menu. Once at Terror, all stay Terror that session.
Worldstone-Shard method: pop a shard to terrorize a whole act for continuous fresh tiles.
- **Herald of Terror** (apex) is the prime Sunder source — has a dedicated rich RotW ID
  card (`#herald-card`). All "Herald of Terror" routes funnel to it (`openHeraldCard()`);
  the 4 lower rungs use lean tier cards.

### The 6 Latent Sunder Charms (grand charms — each breaks ONE immunity to ~95%)
Drop from Hell-TZ Heralds. Only ONE Sunder active at a time. Hell only.
| Charm | Breaks | Best for (Konyo's build) | Renewed upgrade |
|---|---|---|---|
| Bone Break | physical | Konyolock (phys Assassin) | + Perf Amethyst + Pul + Northern shard |
| Black Cleft | magic | Konyodin (Hammerdin) | + Perf Diamond + Mal + Southern/Deep/Northern shards |
| Crack of the Heavens | lightning | Konyoress (light sorc) | + Perf Topaz + Fal + Southern shard |
| Cold Rupture | cold | Frozen Orb/Blizzard sorc | + Perf Sapphire + Lum + Eastern shard |
| Flame Rift | fire | Fireball/Meteor sorc | + Perf Ruby + Io + Deep shard |
| Rotting Fissure | poison | Poison Necromancer | + Perf Emerald + Ko + Western shard |
Renewed recipe (per charm): Latent Sunder + Perfect Gem + Rune + matching Worldstone Shard(s).

### Worldstone Shards (upgrade a Latent → Renewed Sunder; MF does NOT affect, ~1:500-1500)
Western=Act1 zones, Eastern=Act2, Southern=Act3, Deep=Act4, Northern=Act5.

---

## Pandemonium / Uber Tristram chain (→ Hellfire Torch)
- 3 Pandemonium keys (Terror=Hell Countess, Hate=Hell Summoner/Arcane Sanctuary,
  Destruction=Hell Nihlathak/Halls of Vaught), ~10% Hell /p3+. Cube 1 of each →
  one **random** mini-uber portal.
- 3 mini-ubers drop the 3 organs (100%/kill): Lilith→Diablo's Horn,
  Uber Izual→Mephisto's Brain, Uber Duriel→Baal's Eye. Cube 3 organs → Uber Tristram.
- Uber Tristram trio (Uber Meph/Diablo/Baal) → Standard of Heroes → **Hellfire Torch**
  (+3 random class skills, +10-20 all res, +10 all stats; 1 per character).
- **Diablo Clone (Über Diablo)** side-path: triggered by mass SoJ sales → drops **Annihilus**.

---

## Logging / TDD discipline (carried from the Kai/Achilles golden suite)
- **Every feature ships with a Playwright TDD spec** (write/extend the spec, confirm
  the assertion, then keep it green). Specs live in `tests/vNN_*.spec.ts`.
- **Every regression** → `BUGS.md` as `REG-NNN`: symptom · caught-by · root cause ·
  fix · prevention.
- **Every build session / decision** → dated `BUILD_LOG.md` entry.
- **Durable game facts** → here (`GAME_RULES.md`).
- Maintained continuously by CC's Obsidian logging loop (every ~2h).
