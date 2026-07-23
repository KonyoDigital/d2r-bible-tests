# ☀️ MORNING HANDOFF — TV DIABLO nightly autonomous run (2026-07-23)

The night's work, verified. HEAD at handoff ≈ v1329. Cross-refs: **`MORNING_QUESTIONS.md`** (your
decisions) · **`ROADMAP_130.md`** (per-round ✅ log) · **`LOCKED_TYPE_SYSTEM.md`** ·
**`SESSION_FIELD_CONTRACT.md`** · **`tv/G4_GROK_REMOVAL.md`** · **`BUGS.md`** (regression + cert log).

## ✅ What shipped (v1291 → v1329)

**G3 — unified auto-route / tally** (the sunder-tally back-fill you asked for)
- Read-only `/api/autoroute-sweep` (intake-lane inclusive, MAX-of-snapshot) + a "🔄 Auto-route
  Sweep" panel in bible Tools = **merge-max, review-gated apply** (nothing writes till you click Apply;
  provenance `d2r_g3Filled`). Three-outcome routing: chronicle→auto-tally · non-chronicle→🔬 Item
  Checker hand-off · unclear (0 real). Sunders 4/6 (Crack10/Rotting9/Bone6/Flame2; Black Cleft +
  Cold Rupture NEVER seen → omitted), runes 32, gems 33, statues 5/5.

**G4 — removable Grok accuracy layer** ("cheap fingers in a couple places, lifts out clean")
- `tv/g4_grok.py` self-contained; ON/OFF = switch AND key (OFF default, cousin-safe). 3 cheap seams
  (uncertain chronicle route · borderline keep/toss · grail-promotion) — all flag-never-override,
  OFF byte-identical. Toggle card + `/api/g4_flags` "🟣 Grok caught this" surface + daily/hourly caps
  + per-seam config. **Removal test PASSES** (rm module + fenced blocks → 0 traces). OFF until you key it.

**E1 — vault stats** · **Vault Integrity deepening**
- Checker verdict on muled items + **E1b** funnel-2× reconcile (2× confirmed / honest disputed) +
  **E1c** thrown-with-stats "Kept vs Tossed" panel. Vault Integrity checker now cross-references
  G3 provenance + E1 verdicts + the checker (2 new classes + origin tags).

**Diablo-language (engine)** — B4 labels + B8 fingerprint + B4-live
- `_diablo_scene_label` turns (scene, area) → **ENTERING/TOWN/FARMING + area** (town-vs-farming
  decided by a deterministic town list, not a guess). `_session_scene_fingerprint` → "89% farming ·
  1 town trip · 1 portal · mostly Throne of Destruction". Exposed **retro** (sessions routing rows'
  `native`) **+ live** (`/api/status.native`), **documented** in SESSION_FIELD_CONTRACT.md.

**Visual-lock (both surfaces)**
- Console weight type system single-sourced onto `--fw-*` (sessions-visual). **Bible weight system
  100% tokenized** (733→0 raw literals, 6 identity-swap passes) to match. **`visual_lock_invariant.py`**
  enforces 0 raw `font-weight` + the `--fw-*` set on BOTH files — GREEN now (it caught + got 3 real
  console stragglers folded). + `LOCKED_TYPE_SYSTEM.md`.

**Sessions flagship D-arc + console visual-lock** — sessions-visual (control_ui.html): D14–D25
(compare, heatmap, best-run, cinematic shelf card, beat chips, count-ups, seal stamp, recording-now
card, notes/naming) + the console typography lock.

## 🕒 Waiting for YOU (Konyo)
1. **🔄 Sweep Apply** — the sunder back-fill (4/6) + runes/gems/statues are staged. Open bible → Tools →
   🔄 Auto-route Sweep → Scan → review the merge-max diff → **Apply**. Nothing wrote to your trackers yet.
2. **G4 xAI key** — set `XAI_API_KEY` + confirm your model (default `grok-4-latest`), then toggle on.
   The OFF path is proven byte-identical; first live run is your morning smoke test.
3. **Decisions in `MORNING_QUESTIONS.md`:** ls/lh tokenization (needs your design eye — can't identity-fold) ·
   `!important` removal (careful per-rule) · wire visual_lock into pre-push/CI · **G3 live-forward** auto-route
   (daytime) · **reader-prompt B5/B7** dark-frame transition detection (daytime, changes live reader) ·
   small vetoes (D18 finds-strip · duration h:m format).

## 🔍 Clean-tree verification (this capstone, on current HEAD)
- **Node suites: 75/75** — G3 merge-max/3-bucket 23 · hand-off 12 · E1b 7 · E1c 8 · vault-integrity 9 ·
  G4 paint 5 · flags 6 · toggle 5.
- **Python: 41/41** — G4 13 · B4 15 · B8 8 · B4-live 5.
- **= 116 assertions, 0 failed.**
- py_compile (control_app.py + g4_grok.py) OK · 16 bible inline scripts compile ·
  **`visual_lock_invariant.py` GREEN both surfaces** · **G4 removal test still clean** (0 traces) ·
  every `SESSION_FIELD_CONTRACT.md` field present in the real `/api/sessions` + `/api/status` output.
- **Zero regressions.** The whole engine arc (G3/G4/E1/vault/B4/B8/B4-live) is complete + verified.

## Honesty notes
- `farmingPct` is **of-reads, not wall-time** (labeled in the contract).
- Sunders: only 4/6 witnessed — Black Cleft/Cold Rupture never seeded.
- Grails are **not zone-pinned** (heatmap + fingerprint say so).
- Two live paths (G4 xAI, G3 live-forward) + the reader-prompt round are deferred to daytime so you
  verify them live — not risked autonomously overnight.
