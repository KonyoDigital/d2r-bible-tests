# 🔬 FULL AUDIT SWARM — findings + fix sequence (Konyo 2026-07-22, on v1256)

5-agent swarm (router · tally · retro-vs-photos · simulation · sync) audited the console/engine on Konyo's REAL
recent photos + re-ran frames through the live pipeline. Verdict: the swarm smoked out real bugs before Konyo did.

## FINDINGS (ranked)
- **F1 🚨 CATASTROPHIC — wallpaper sealed as Gems tab (69 frames, reels 81925+81294).** TCC drop captures the Mac
  desktop (HK skyline); vivid multi-hue lights trip the stash-gems grid signature → phantom tally:gems → reads 0
  (Konyo's "Gems tallied 0" MISS). Confirmed by opening the actual .jpg (Mac menu bar, no game). FIX A dispatched.
- **F1b 🚨 MECHANISM (router) — the gate's 2-witness check is FAKE for gems.** grid is the only real signal
  (sources=['grid','solo'], ocrTab=''), but control_app.py ~4175-4176 relabels the grid cls as a phantom votes['ocr']
  → _router_conf counts ONE detector as TWO classes → conf 2 → clears the gate. A lone (false) grid read self-
  certifies. THIS is why the wallpaper passed. FIX D (folded into FIX A): sanctioned grid-solo single-signal route
  w/ its own tighter threshold; don't naively drop the vote (kills TRUE gems, which is legitimately grid-only).
- **F2 🔴 HIGH — v1254-v1256 fixes don't reach ALREADY-SEALED reels.** Auto-rescan only on kaiVer<3; all code stamps
  kaiVer:3, so old reels never re-seal. Konyo's real Gems reel (92862) still shows 0 gems on disk. FIX B: bump
  kaiVer→4 + auto-resweep (folded into FIX A). Wallpaper reels QUARANTINED, not re-sealed as valid gems.
- **F3 🔴 HIGH — grail tooltips missed (Enigma, Harlequin Crest) in the real session.** Fully legible in-photo →
  reduced to OCR garble ("REQ", "eF GEtTINt MAGIC") → left UNNAMED (in missed[], not register). The flagship reads.
  FIX C (queued, engine): item-name extraction/grounding for grail tooltips.
- **F4 🟡 SYNC — live guess can render as the sealed verdict (control_ui.html:6976 _erOwnerVerdict).** Guard keys on
  owner-truthiness not frame-presence; a sealed owner=None frame falls through to liveRing → live guess shown
  authoritative during scrub. Presentation-only (disk artifact fine). FIX E (queued, polish-ui-2 UI): key on
  frame-presence `if (b && b.engineFrame)`; ideally route through the canonical _kai_engine_frame_effective (which
  is currently TEST-ONLY DEAD CODE — SEV-2, the drift enabler).
- **F5 🟡 persistence — some reels have no routing/register/engineFrames ledger** (2nd closer pass didn't finish);
  console gate strip blank/stale for older reels. Mostly resolved by FIX B re-seal.

## VERIFIED SOLID (don't touch)
Router decision logic (0 mis-routes, tooltips never→vault, dedup, hold/disagreement); tally reconcile math
(no zero/thin read clobbers a good count — _tab_best_total + never-zero guard); reconciler priority ladder +
honest-miss; ×3 stamp parity @ v1256; gems detection on REAL gems (5 recovered, 0 false positives on game frames).

## FIX ORDER
1. FIX A+D+B (engine, DISPATCHED) — panel-open/is-D2R guard + phantom-ocr gate honesty + kaiVer→4 re-seal.
2. FIX C (engine) — grail tooltip name extraction.
3. FIX E (UI, polish-ui-2) — sealed-wins frame-presence guard.
Each verified against the real reels (wallpaper→not-gems; real gems→still gems; Enigma/Harlequin→named).
