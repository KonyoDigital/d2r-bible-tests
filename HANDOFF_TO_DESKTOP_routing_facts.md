# HANDOFF → Desktop — Authoritative TZ→boss facts + routing decision

**From:** CC (terminal) · **Date:** 2026-05-30
**Scope:** answers Konyo's "make these facts authoritative & researched & accurately placed,"
including the **Duriel** question. CC stayed OUT of bible.html (Desktop is live in it).

---

## 1. DURIEL — yes, he is 100% a boss. Desktop's "no boss there" was imprecise.

- **Duriel is the Act 2 boss.** He spawns in **Duriel's Lair, inside Tal Rasha's Tomb**
  (reached via the Canyon of the Magi → the True Tomb).
- He is **NOT** in the **Arcane Sanctuary**. Arcane Sanctuary's resident super-unique is
  **The Summoner** (Horazon). So the bug is *only* the `Arcane Sanctuary → duriel` link —
  **keep Duriel as a boss**, just stop pretending Arcane Sanctuary == Duriel.
- The map already routes Duriel correctly elsewhere: `{re:/duriel|tomb/i, boss:'duriel'}`
  (line 4444) — any "Tomb" terror zone → Duriel is **correct**. Don't touch that rule.

## 2. Authoritative TZ-zone → actual content (the 10 zones in TZ_ZONES, 3088+)

| # | TZ zone (bible name) | Act | Real boss/super-unique IN the zone | Current link | Verdict |
|---|----------------------|-----|------------------------------------|--------------|---------|
| 1 | Flayer Dungeon L3 | 3 | **Witch Doctor Endugu** (super-unique) | travincal | ❌ wrong — Endugu ≠ the Council |
| 2 | Crystalline Passage + Frozen River | 5 | **Frozenstein** (Frozen River); Eldritch/Shenk are in Bloody Foothills | baal | ❌ wrong — Konyo's reported mis-route |
| 3 | Worldstone Keep L1-L3 | 5 | leads to Throne → **Baal** (canonical Baal-run zone) | baal | ✅ correct |
| 4 | Halls of Anguish/Pain/Vaught | 5 | **Nihlathak** (spawns in Halls of Vaught) | nihl | ✅ correct |
| 5 | Arcane Sanctuary | 2 | **The Summoner** (Horazon) — NOT Duriel | duriel | ❌ wrong (see §1) |
| 6 | River of Flame + Chaos approach | 4 | Chaos Sanctuary → **Diablo** | diablo | ✅ correct |
| 7 | Tristram (the town) | 1 | **Griswold, The Smith, Bone Ash, Rakanishu** | countess | ❌ wrong — Countess is in the Forgotten Tower (Black Marsh) |
| 8 | Burial Grounds + Crypt + Mausoleum | 1 | **Blood Raven** (Burial Grounds), Coldcrow (Cave) | andariel | ❌ loose — Andariel is in the Catacombs, not here |
| 9 | Spider Forest + Cavern | 3 | **Sszark the Burning** (Spider Cavern) | mephisto | ❌ loose — Mephisto is in the Durance |
| 10 | Catacombs L4 | 1 | **Andariel** literally spawns here | andariel | ✅ correct |

**4 genuinely correct links:** Worldstone Keep→baal, Halls→nihl, River of Flame→diablo,
Catacombs L4→andariel. These are zones where a card-backed boss actually spawns.

**6 wrong/loose links:** the zone's value is its OWN super-unique(s) that have no boss card
in the 11-boss list (Endugu, Frozenstein, Summoner, Griswold/Smith, Blood Raven, Sszark).

## 3. Recommended routing decision (honest, no-fabrication)

A TZ-zone card should open a boss detail **only when a card-backed boss genuinely spawns in
that zone** (the 4 correct rows). For the other 6, do NOT silently route to a same-act proxy
boss — that's the exact thing Konyo flagged. Two acceptable behaviors for the 6:
- **(preferred)** leave `data-boss-id` empty so the card is non-clickable (the onclick guard
  `if(this.dataset.bossId)` already no-ops on empty), and drop the misleading `cursor:pointer`
  / "click to see boss detail" title for those cards; OR
- show the zone's own super-unique name as the headline (no false boss card).

Do **not** delete Duriel, Mephisto, Countess, Travincal, Baal as bosses — they stay in BOSSES
and remain reachable via their chips. We're only removing the *false zone→boss associations*.

`TZ_BOSS_MAP` (lines 4433-4451) is the single place to fix: keep the 4 correct regexes,
remove/empty the 6 proxy regexes (crystalline/frozen, tristram, arcane sanctuary, spider,
flayer, burial-grounds/crypt/mausoleum). `tzZoneBoss()` returns null → `tagTzZonesWithBossId()`
(4523) leaves `data-boss-id` empty → card no-ops. Clean, reversible, one function.

## 4. Backend data scan (CC, read-only) — STRUCTURE IS CLEAN

- **312 unique items**, **0 bad tiers**, **0 cross-boss contradictions** (every item's
  tc/qlvl/tier is identical across every boss table it appears in).
- **Only 3 `v` (silospen-verified) anchors**: andariel×2, mephisto×1. No false "verified"
  badges, no `v` flag on a null cell.
- Open item (not a bug, a known model limitation): the drop-odds *magnitudes* are a scaled
  model (Mephisto rarity column × per-boss scalar) with only those 3 verified anchors. The
  silospen anchor pass (parked) is what makes the rest authoritative.

## 5. Coordination

- CC owns the test files and is shipping a **routing + data-integrity Playwright spec** that
  asserts the CORRECT card opens (catches the Crystalline-Passage class) and that every drop
  cell's rendered odds == `fmt(adjustChance(raw, mf))` (no render-time fabrication, ~20k cells).
- CC did NOT touch bible.html — Desktop owns the TZ_BOSS_MAP edit. Re-sync md5 across all 3
  copies after Desktop's edit, then CC re-locks the spec against the corrected mapping.
