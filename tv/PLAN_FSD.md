# TV DIABLO — Autopilot / “Tesla FSD” roadmap

> Not a game bot. **Screen Autopilot**: continuous perception → decide *when*
> vision is worth it → act only on farmed truth. Read-only by construction.

## Layers (FSD analogy)

| Layer | Tesla | TV DIABLO |
|-------|--------|-----------|
| L0 Sensors | cameras | `screencapture` @ 0.25s + frame sig |
| L1 Perception | nets | settle + scene/area/names (Claude) |
| L2 Prediction | agents/paths | **interest score** (motion→stop = loot moment) |
| L3 Planning | route | when to fire vision · which model · farmed vs seen |
| L4 Control | steering | engines + `tvVaultRegister` (farmed only) |
| L5 Shadow | fleet logs | SESSION HISTORY + brain log + `/frame` |

## Shipped
- L0–L1 baseline · subscription vision · Sonnet default · farmed/seen · vault wire · history
- **v727 Autopilot core:** interest scorer · priority gap after hard motion · adaptive stable ticks · `ap` on `/state`

## Next waves
| Ver | Focus |
|-----|--------|
| v728 | Multi-frame confirm (2 frames agree before vision) for low-interest only |
| v729 | Panel heuristics (bright UI bands) without full Claude |
| v730 | Shadow mode metrics: pile-to-chip p50 · empty rate · farmed rate |
| v731 | Board “Autopilot HUD” (Tesla-style stack viz) |
| later | Temporal name fusion · vault journal lines · public product |

## Non-goals
- No game memory/input injection  
- No silent floor→vault  
- No forge redesign  
