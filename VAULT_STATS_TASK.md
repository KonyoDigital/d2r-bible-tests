# 🏦📊 VAULT MANAGER — attach AI-Item-Checker stats to muled items (Konyo 2026-07-22)

> Konyo: "the console and up is the focus; the website/coding is pretty perfected already, might need a little
> finishing. Upgrade the vault manager to read accurate items after they get funneled a couple times through the
> AI ITEM CHECKER — that way the STATS are attached to the items that are MULED, compared to thrown out."

## SCOPE = bible.html (the website "little finishing"), NOT the console. Queue AFTER the console accuracy/audit arc.

## CURRENT STATE (grounded)
- **AI ITEM CHECKER** (bible.html ~4625): "Drop a magic/rare item — read or edit its affixes, then get a keep-or-toss
  verdict." Reads affixes/stats + verdict. Draft state = d2r_aicDraft. Result today is a verdict; the read affixes
  are NOT persisted onto the item.
- **THE VAULT / mule manager** (mule-vault-card ~4406, renderVault/vaultAddMule, d2r_owned): stores muled items by
  NAME, auto-assigns to mules by taxonomy, shows a 🏦 badge. Carries the item name + mule, NOT its stats.
- GAP: a kept item's real STATS (from the checker) don't ride onto the vaulted/muled entry. Muled items are
  name-only; you can't see the affixes of what you stored.

## THE UPGRADE
When the AI Item Checker gives a KEEP verdict and the item is muled/vaulted, ATTACH the checker's read stats
(affixes + verdict + confidence) to that vault entry, so:
- Muled items in the vault carry their real stats (viewable on the item's vault/detail card), distinguishing the
  KEPT/muled items (stats attached) from THROWN-OUT ones (not stored, or logged as thrown with no stats).
- "Funneled a couple times through the AI Item Checker" = optionally run the item through the checker 2x for
  accuracy before attaching (reconcile the reads, keep the confident stat set) — Konyo's accuracy standard.
- The checker → vault handoff: a "🏦 mule this (with stats)" action from the checker result that writes the item +
  its stats to d2r_owned/the vault entry.

## GUARDRAILS
TRUTHFUL — only attach stats the checker actually read (editable, like the checker already allows); honest
"unread" if a stat wasn't captured. Rides the existing bible.html persistence (d2r_owned + a stats field, forked in
_LP_FORKED). Don't disturb the console work / parked GHOST MODE. EDIT_LOCK protocol on bible.html (Desktop also edits).

## QUEUE: after the console DIABLO-LANGUAGE accuracy arc + the swarm-audit fixes land. This is the website finishing pass. 🏦📊
