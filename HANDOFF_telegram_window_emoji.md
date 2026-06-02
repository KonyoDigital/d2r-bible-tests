# HANDOFF → Terror-window Telegram bot (off-machine) — incoming vs live emoji change

**From:** CC (terminal) · **Date:** 2026-06-03
**Status:** SPEC ONLY — the generator is NOT in `d2r_bible_tests` nor anywhere on the
Mac (`grep -rl` over all of `/Users/konyo` for the message strings = 0 hits). The
"INCOMING IN 30 MIN" / "LIVE NOW — 30 MIN WINDOW" Mephisto/Durance alerts come from
an external scheduler/bot (the "TZ alert bot" referenced in the Bible TZ tab). Apply
this change wherever that bot's message template lives.

## Konyo's ask (verbatim)
> "we said we would change the emoji for incoming and also we NEED to change for fire
> too its and LIVE so wait needs to be more understanding that its a waiting and
> incoming before the live"

Intent: the **incoming/waiting** state and the **live** state must read as a clear
progression. Today both use heat-style emoji (⚡ incoming, 🔥 live) so the
waiting→live distinction is weak.

## The change
| State                         | Current header emoji | New header emoji | Rationale |
|-------------------------------|----------------------|------------------|-----------|
| Pre-window (T-30, "INCOMING") | ⚡                   | ⏳ (hourglass)   | reads as *waiting / not yet* |
| Window open ("LIVE NOW")      | 🔥                   | 🟢 (or keep 🔥, pair with clear LIVE marker) | reads as *go now* |

Recommended exact headers:
- `⏳ INCOMING IN 30 MIN` (was `⚡ INCOMING IN 30 MIN`)
- `🟢 LIVE NOW — 30 MIN WINDOW` (was `🔥 LIVE NOW — 30 MIN WINDOW`)

If 🟢 feels too flat for "live", keep 🔥 but prefix the incoming one with ⏳ so the
two are unmistakably different states (the key requirement is the **contrast**, not
the specific live glyph). Konyo's priority: the waiting state must telegraph
"not yet — stand by", clearly distinct from the live "drop everything, go" state.

Body fields (👺 boss, 📍 zone, ⏰ time, 🎮 Play: Konyolock, 💎 charged drop) stay
unchanged — only the leading state-header emoji changes.
