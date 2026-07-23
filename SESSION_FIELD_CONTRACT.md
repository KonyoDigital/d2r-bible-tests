# SESSION FIELD CONTRACT — what the UI (sessions-visual) can render

The engine (control_app.py) exposes session + live data on two payloads. Every field below is
**honest-absent**: when the data genuinely isn't there the engine sends `null`/omits it — the UI
must hide the element, never render a fake `0`/`—` as if it were real. This is the reference for
surfacing the Diablo-language (B4/B8) + Sessions-flagship (D-series) fields.

═══════════════════════════════════════════════════════════════════════════════
## `GET /api/sessions` → `{ sessions: [ {…}, … ] }`  (retro; newest first)
Each session object (from `_theatre_sessions`):

**Identity / counts**
- `n` int · `t0`,`t1` ms (start/end) · `sessionId` str · `reads`,`frames`,`named` int · `thumb` str|"" · `reeln` int

**📖 What KAI witnessed**
- `finds: [{name, tier, firstSeenTs, frameId, loc}]` · `topFind` obj|null · `registered` int

**Decision story (D5–D7)**
- `coverage: {read, total, gaps}` | **null** — read-completeness %; null when the reel had no item text.
- `classFrames: [{scene, thumb, frameId, ts, native}]` | **null** — one representative still per scene
  (montage). Each frame now carries **`native`** (B4) = `{kind, label, area}` for that frame's scene (area
  sourced from the nearest deep read ±5s; area-less label like "STASH"/"FARMING" when none is near). The B4
  **chapter ribbon** reads `classFrame.native`. `stash`/`stash-gems`/`stash-runes`/`stash-materials` → STASH;
  `gameplay` → FARMING; `transition` → ENTERING; `tooltip` → `unclear` (an item-read moment, not a location).
- `superRecovery: {recovered, missed}` | **null** · `missedFrames: […]` | **null**
- `sealMs` int | **null** (seal latency; null unless a clean ≤30min seal) · `regretItems: [{name,frameId,ts}]` | **null**
- `judged` int · `regrets` int

**Scene / Diablo-language (B4 + B8)**
- `sceneReads: {scene: count}` | null — raw read tally (stash/gameplay/transition/town/inventory/loot).
- `tabReads: {tab: count}` | null.
- **`sceneFingerprint`** | **null** (B8) — the Diablo-native session summary:
  ```
  { farmingReads:int, townReads:int, portals:int, townTrips:int,
    farmingPct:int|null, topArea:str|null, areas:[str], sceneReads:int }
  ```
  - `farmingPct` = farming / (farming + town) **reads** — **of-reads, NOT wall-time** (the reader
    reads panels more than gameplay). Label it "farming (of reads)" or show the counts; do NOT imply
    a time %. `null` when the session had 0 world reads (only stash/portal) — show portals/counts only.
  - `townTrips` = distinct town visits · `portals` = ENTERING/transition events · `topArea` = most-read
    FARMING area ("mostly Dark Wood"), `null` when no farming area was named.
- `areas: [str]` (first 6 areas seen) · `stub` bool (thin session).

**Per-frame routing rows** (from the reel report's `routing` / the reconcile map) each carry:
- **`native`** (B4) — `{ kind, label, area }` — the game-true scene label for that frame:
  - `kind ∈ entering | town | farming | menu | unclear`
  - `label` e.g. "ENTERING The Pit" · "TOWN · Harrogath" · "FARMING · Chaos Sanctuary" · "STASH · Harrogath" · "unclear"
  - `area` str|null. `unclear` = the frame carried no scene/area (never invents a location).

═══════════════════════════════════════════════════════════════════════════════
## `GET /api/status` → live payload  (polled by the D24 "recording now" banner)

**Live state**
- `mode` ("live"|"sim"|"off"|"stopping") · `agent`,`bridge`,`stopping` bool · `phase` str · `pid`,`capture`
- `readCount` int · `intakeRing`,`events`,`liveRing`,`eyes`,`mindStory`,`sessionHealth`,`driver`,`watchdog`

**Live scene / Diablo-language (B4-LIVE)**
- `scene` str|"" · `area` str|"" — the live agent beat's raw scene/area.
- **`native`** (B4-LIVE) — `{ kind, label, area }` | **null** — the LIVE frame's game-true label for
  the banner (e.g. "🏛 ENTERING The Pit" / "⚔ FARMING · Chaos Sanctuary"). **null** when off / no live
  scene/area (dark frame) — hide the banner label, don't show "unclear" live.
- `interest`,`motion`,`model` — live read signals.

═══════════════════════════════════════════════════════════════════════════════
## Rendering rules (honesty)
1. **null = hide**, never a fake zero/dash. (`sceneFingerprint`, `coverage`, `native`, `sealMs`, `regretItems`… all follow this.)
2. `farmingPct` is a **read-proportion, not time** — never label it "% of session".
3. `native.kind='unclear'` (retro) / `native=null` (live) = the frame genuinely didn't say where — say so, don't guess.
4. `topArea`/`areas` are what the reader NAMED — grails are NOT zone-pinned (same rule as the D16 heatmap).

Engine source: `_diablo_scene_label` + `_session_scene_fingerprint` + `status_payload` (tv/control_app.py).
Reader emits scene/area (tv_diablo.py); dark-frame `transition` detection is a queued reader-prompt round.
