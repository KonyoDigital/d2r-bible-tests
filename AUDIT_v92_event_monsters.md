# AUDIT v92 — Event-Monster / Event-Card gbc-Parity

> Master goal: unify **every** drop-source ID card to the golden `.gbc-card`
> Baal-format design language. Constraints: **zero fabrication · additive-only
> (nothing cut) · clean eye-candy.** This audit scores the `#tab-ancients`
> "Pinnacle Events" entities + the loose drop-sources (Travincal, Pit, Cows)
> against the golden shell and sets the v92 scope.

## The golden target (reference shells already in the tree)
- **`.gbc-card`** → `.gbc-header` gradient banner [`artOr(name,emoji,'lg')` emblem
  + `.gbc-id-block` (`.gbc-name`/`.gbc-subtitle`/`.gbc-loc`) + `.gbc-tier` badge
  + `.gbc-close`] → `.gbc-body` of `.gbc-section`/`.gbc-section-label` blocks.
- Already gbc-parity (precedent): **Baal boss card**, **Herald card** (v88, L2422),
  **TZ-zone rich card** (v85.1, L4267), **super-unique rich card** (v91, L4367).

## Entity inventory — `#tab-ancients` (7 top-level `.event-card`s)

| # | Entity | id / line | Current shell | Emblem | Content quality | gbc gap |
|---|--------|-----------|---------------|--------|-----------------|---------|
| 1 | **Uber Tristram** | `event-uber-tristram` L2683 | `.event-card`/`.ec-*` | hardcoded `<img>` L2685 | RICH — 5 steps, holy-grail box, 3 tables, success/info/warning | header banner + tier badge + artOr |
| 2 | **Uber Boss ID Cards** (9) | `event-uber-id-cards` L2742 | `.event-card` wrapper → JS `.ubc-*` inner cards (L8811) | inner uses `artOr 'lg'` ✓ | RICH — full monster stat cards (mlvl/hp/def/block/immune/resists/abil/drop/strat) | outer head + inner `.ubc` shell ≠ gbc |
| 3 | **Colossal Endgame — Jewels & Statues** | `event-colossal-showcase` L2757 | `.event-card` wrapper → JS `.colossal-tile`/`.ct-*` index (L8866) | tiles use `artOr 'lg'` ✓ | index of clickable relic tiles (route to material cards) | outer head + tile shell ≠ gbc |
| 4 | **Secret Cow Level** | `event-cow-level` L2772 | `.event-card`/`.ec-*` | hardcoded `<img>` L2774 | RICH — 4 steps, what-you-farm box, cube recipe, Cow-King rule | header banner + tier badge + artOr |
| 5 | **Diablo Clone** | `event-diablo-clone` L2816 | `.event-card`/`.ec-*` | hardcoded `<img>` L2818 | RICH — spawn-stage table, stat-grid, counters, Anni stat-grid | header banner + tier badge + artOr |
| 6 | **Colossal Ancients** (preserved) | `event-colossal-ancients` L2880 | `.event-card`/`.ec-*` | hardcoded `<img>` | (preserved legacy) | header banner + tier badge + artOr |
| 7 | **22 Nights of Terror** | `event-22-nights` L2909 | `.event-card`/`.ec-*` | hardcoded `<img>` | seasonal-event info | header banner + tier badge + artOr |

## Loose drop-sources (not in `#tab-ancients`)
- **The Pit** — ✅ **already gbc-parity.** Rendered through the TZ-zone rich card
  (`.gbc-card tz-zone-card-rich`, L4267) as a permanent-lvl85 TZ crosslink
  (L593/L4970). **No action.**
- **Travincal Council** — ❌ **no dedicated detail card.** Exists only as Bind-tab
  tables (Ismail/Geleb/Toorc L3233-35), council-count facts (L3332), and rune-source
  prose (L3876-77). It IS a top-tier drop-source (best high-rune throughput in game).
  **Gap: it has rows, not a card.** Candidate for a future card — but see scope note.
- **Secret Cow Level** — also has a second presence as the Runes-tab "Cow Level"
  card (rune detail). The `#tab-ancients` event-card (#4 above) is the procedural one.

## Key finding — these are PROCEDURAL guides, not stat ID cards
Cards 1/4/5/6 are **multi-step how-to guides** (farm keys → cube → fight → reward),
structurally unlike the boss/super-unique/TZ **stat+drop reference** cards. The
unifiable surface is therefore the **SHELL** (header banner + section idiom), not a
forced stat-grid. The rich step bodies map cleanly onto `.gbc-section` /
`.gbc-section-label` (each existing `<h3>` step → a labelled section) with **zero
content loss** — pure additive re-wrap.

## Concrete gaps (what v92 should close)
1. **Emblem not via `artOr()`** — the 5 hardcoded-`<img>` heads (#1,4,5,6,7) bypass
   the `artOr` helper the #52 invariant wants every ID card to resolve through.
   (They do have an inline `onerror` d2art fallback, so behaviour ≈ artOr; it's the
   *helper-routing* parity that's missing.) Cards #2/#3 inner art already uses `artOr`.
2. **No `.gbc-header` gradient banner** — `.ec-titles`/`.ec-sub`/`.ec-chevron` vs
   `.gbc-name`/`.gbc-subtitle`/`.gbc-tier`. No mlvl/tier badge on the event heads.
3. **`.ec-*` / `.ubc-*` / `.ct-*` design languages** diverge from `.gbc-*`.

## Recommended v92 scope (additive, low-risk, high payoff)
**Convert the 7 top-level `.event-card` HEADERS → `.gbc-header` banner format**
(artOr emblem + `.gbc-name`/`.gbc-subtitle` + a `.gbc-tier` badge showing the
event's key stat — e.g. Uber Trist "mlvl 110", DClone "mlvl 110", Cows "Hell only").
Re-wrap each step body's `<h3>` into `.gbc-section`/`.gbc-section-label` — **content
verbatim, nothing cut.** Route emblems through `artOr()` to satisfy #52.

**Deliberately OUT of v92 scope (separate later passes):**
- Inner `.ubc` 9-boss cards + `.colossal-tile` index (#2/#3): already artOr'd and
  content-rich; their sub-card shells are a follow-up, not a blocker.
- **Travincal card creation** — it's a genuine gap but it's *new card authoring*
  (needs a content pass), not a *shell unification*; belongs in its own batch (v93)
  to keep v92 a clean refactor with no fabrication risk.

## Guard to add (#52 lock)
Extend the v83 sync audit with an invariant: **every `#tab-ancients .event-card`
head resolves an `artOr` emblem AND carries the `.gbc-header` contract** (gbc-name +
gbc-subtitle + tier badge). Pairs with the existing "gbc-format parity" guard so the
event cards can't silently drift back to `.ec-*`.

## Blast-radius / caution
- `toggleEventCard()` (L4450) keys off `.event-card-head` + `.event-card-body[hidden]`
  + the `data-tip`/anchor-open path at L8903. **Keep those class hooks/ids** when
  re-skinning the head, or wire the collapse to the new markup — do NOT break the
  expand contract (tests assert event-card expand).
- Run the FULL suite (shared `.event-card` CSS at L3068 + the artOr helper = site-wide
  reach per the central-helper rule).

---
*Audit by CC 2026-06-07. Next: implement v92 header-unification per scope above.*
