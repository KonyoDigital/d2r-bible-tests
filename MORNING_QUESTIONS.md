# ☀️ MORNING QUESTIONS — for Konyo (nightly autonomous run 2026-07-23)

Anything I couldn't decide autonomously overnight lands here so I never block the chain. Check `ROADMAP_130.md` for the ✅ progress.

## ❓ Needs your call
1. **G4 Grok — your xAI key + model.** The whole G4 add-on is OFF by default and won't make a single Grok call until you (a) put your xAI key in the env as `XAI_API_KEY` on this Mac, and (b) flip the toggle ON. Default model is `grok-4-latest` (override with `G4_GROK_MODEL`). **Which model does your xAI account have access to?** Nothing fires until you confirm — the OFF path is proven byte-identical to today. When you're ready to try it: set the key, then toggle on (the button, or `TV_G4_GROK=1`, or `touch tv/g4_grok.state`), and the 3 cheap touchpoints go live.
2. **G4 live path is UNTESTED tonight** (by necessity — no key = can't hit xAI). Everything is verified on the OFF path (no-op, zero network, byte-identical). The live agree/disagree logic + the 3 touchpoints are wired but only exercise when you enable it. First real run in the morning is the live smoke test — I'll be around to fix anything the moment you flip it on.

## 🟢 Decisions I made autonomously (veto any in the morning)
- **G4 toggle UI → control_ui.html (the ops console).** Grok is an engine add-on and the g4_status/g4_toggle routes are control-server endpoints, so the switch belongs in the console's settings, not the bible board. The sessions-visual agent will add a small OFF-by-default toggle there. (It already works headless via env/state file, so this is just the convenience button.) Say the word if you'd rather it live elsewhere.
- **G3 sweep:** built exactly to your merge-max / review-gated / chronicle-vs-checker spec; nothing writes to your trackers until you open Tools → 🔄 Auto-route Sweep → Scan → review the diff → Apply. The sunder back-fill (4/6) is waiting there.
- **Visual work brought forward** (type system) ahead of the Phase C feature rounds, because you said the flagship LOOK was your #1 concern. Features resume after the type system is locked.
