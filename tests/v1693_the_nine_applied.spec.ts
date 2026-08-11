import { test, expect } from './_net_stub';
import * as path from 'path';

/* ══════════════════════════════════════════════════════════════════════════════════════════════
   v1693 — HIS RULING ON THE NINE, APPLIED: THE TALLY IS FINALLY THE NUMBER HE ACTUALLY HAS.

   v1692 surfaced nine names that print a "First Found:" line in his own Chronicle but live in his
   d2r_grailUnfound (his own un-tick, USER TRUTH) — SURFACED, never overruled: Gravepalm, Chance
   Guards, Blackbog's Sharp, Pluckeye, Lidless Wall, Hellslayer, Islestrike, Vampire Gaze,
   Sureshrill Frost. He has now READ that evidence and RULED: apply them. This ship executes that
   ruling, and adds The Diggler (a tenth name, honest date, not from d2r_grailUnfound) alongside it.

   THE DATA IS HIS, NOT A FIXTURE. Same read-only source as v1692: the WKWebView copy at LEDGER_DB
   (node:sqlite, readOnly:true — no write path in this file ever touches his live store) when it
   exists, otherwise the REAL_SNAPSHOT below, frozen from that same copy on 2026-08-11.

   HEAD def0da0 (committed) is v1692 — bible.html's WORKING TREE, uncommitted, already carries the
   v1693 implementation (two chronicleApply blocks: 'd2r_v1693RulingApplied' for the nine,
   'd2r_v1693DigglerApplied' for The Diggler). This file is the PROOF against that working tree, not
   a blind TDD-first spec — the numbers below were measured by running it, not guessed.

   ⚠ CONTRADICTION FOUND, REPORTED HERE RATHER THAN SILENTLY PICKED (both sides shown, not
   averaged): the ship brief named CHANCE GUARDS as carrying 'formatting-inference' provenance and
   PLUCKEYE as the one whose date is partial/omitted. THE BRIEF WAS WRONG ON BOTH COUNTS AND THE
   IMPLEMENTATION IS RIGHT: _GRAIL_SEED holds a real minute for all nine, Pluckeye's included
   ('Jul 9, 2026 · 18:51'), so bible.html passes an EXPLICIT seed date for every one of them —
   Chance Guards ('Jun 8, 2026 · 23:22', bible.html:36257) no differently from the other eight.
   Chance Guards is only the weakest READ (clipped frame, formatting-only recovery); the seed is
   its second witness, and the seed is what is stored.

   ⚠2 DO NOT "SIMPLIFY" BY DELETING THAT .date — that edit writes a fabricated date into his
   ledger, permanently. chronicleApply only overrides the stamp when a row CARRIES one, by swapping
   window._grailStamp for the length of that one add (bible.html:36099-36104). toggleOwned itself is
   `fl[name] = window._grailStamp()` (bible.html:18785) — a NOW-stamp, with NO _GRAIL_SEED fallback
   of any kind. Drop the date and today's date lands under a line reading "First Found:", and the
   boot floor that would otherwise supply the seed is one-shot (`if (!_gfl[n])`, bible.html:16934),
   so nothing can ever correct it. An earlier draft of this header claimed the opposite — that the
   apply passed no date and toggleOwned fell back to the seed — and cited bible.html prose that no
   longer exists; both halves were false. Test (4) pins the behaviour that actually happens and
   prints both strings when it does not.

   RED-PROVE SEAM: V1693_BIBLE=/abs/path/to/older/bible.html npx playwright test tests/v1693_*.spec.ts
   Run against HEAD's bible.html (committed v1692, no working-tree changes) via `git show
   HEAD:bible.html > /tmp/v1692_only.html && V1693_BIBLE=/tmp/v1692_only.html npx playwright test
   tests/v1693_*.spec.ts`: window.chronicleApply exists (v1692) but neither v1693 block does, so
   d2r_foundLog stops at 346 keys / 238 uniques, d2r_grailUnfound stays at its original 9 keys, and
   every assertion in tests (1)-(4) below goes RED with exactly those numbers — measured, not
   assumed. Against the CURRENT working tree (the default target, no env var) every test here is
   GREEN, with the numbers documented next to each assertion.
   ══════════════════════════════════════════════════════════════════════════════════════════════ */

const LEDGER_DB = '/private/tmp/claude-501/-Users-konyo/63b4ef22-a3c0-4f38-bb69-b17a7839a6ae/scratchpad/ls/1/localstorage.sqlite3';
const BIBLE = process.env.V1693_BIBLE || path.resolve(__dirname, '..', 'bible.html');
const URL = 'file://' + BIBLE;

// ── the measured magnitudes, stated before anything is read ──────────────────────────────────
const N_FOUNDLOG      = 346;  // keys in his d2r_foundLog, BEFORE any auto-apply
const N_SETPIECES     = 110;
const N_RAW_UNIQUES    = 236; // 346 - 110: his ledger before ANY of v1692/v1693 fire
const N_V1692_ONLY      = 238; // 236 + Fleshrender + Gloom's Trap — v1692 alone (the RED-PROVE floor)
const N_CONFLICTS      = 9;   // d2r_grailUnfound — his own un-ticks, going in this ship
const N_ADDED           = 12;  // Fleshrender + Gloom's Trap (2) + the nine (9) + The Diggler (1)
const N_AFTER           = 248; // 236 + 12, a full fresh boot with NO flags pre-set
const N_LEDGER_AFTER    = N_FOUNDLOG + N_ADDED; // 358
const THE_NINE = ["Gravepalm", "Chance Guards", "Blackbog's Sharp", "Pluckeye", "Lidless Wall",
  "Hellslayer", "Islestrike", "Vampire Gaze", "Sureshrill Frost"];
const DIGGLER = 'The Diggler';
// Eight of the nine corroborated dates the implementation actually stamps (matches _GRAIL_SEED's
// independent 2026-07-12 transcription). The ninth, Chance Guards, is pinned separately in test (4)
// against the live _GRAIL_SEED value rather than a literal, so a seed edit can never make that
// assertion silently vacuous — it is stamped from an explicit .date exactly like these eight.
const CORROBORATED_DATES: Record<string, string> = {
  "Blackbog's Sharp": 'Jul 12, 2026 · 20:46',
  'Islestrike':        'Jul 12, 2026 · 19:33',
  'Lidless Wall':      'Jul 13, 2026 · 22:12',
  'Sureshrill Frost':  'Jul 6, 2026 · 23:59',
  'Gravepalm':         'Jun 8, 2026 · 23:44',
  'Hellslayer':        'Jul 12, 2026 · 23:34',
  'Vampire Gaze':      'Jul 7, 2026 · 00:44',
  'Pluckeye':          'Jul 9, 2026 · 18:51',
};

// REAL_SNAPSHOT — his real store, exported 2026-08-11 from the read-only copy above. Frozen, not
// synthetic. Only the five keys this ship reads; nothing here is written back anywhere.
const REAL_SNAPSHOT: Record<string, string> = {
  "d2r_foundLog": "{\"Wormskull\":\"Jun 22, 2026 · 02:00\",\"Wraith Flight\":\"Jun 18, 2026 · 19:29\",\"Witherstring\":\"Jul 1, 2026 · 21:09\",\"Wizardspike\":\"Jun 3, 2026 · 12:45\",\"Wizendraw\":\"May 20, 2026 · 21:15\",\"Wolfhowl\":\"Jun 5, 2026 · 00:45\",\"War Traveler\":\"Jun 4, 2026 · 01:24\",\"Windhammer\":\"May 22, 2026 · 01:17\",\"Venom Grip\":\"May 20, 2026 · 18:35\",\"Venom Ward\":\"May 18, 2026 · 21:07\",\"Verdungo's Hearty Cord\":\"Jun 22, 2026 · 02:10\",\"Wall of the Eyeless\":\"May 20, 2026 · 18:26\",\"Twitchthroe\":\"Jun 2, 2026 · 01:07\",\"Ume's Lament\":\"May 18, 2026 · 00:25\",\"Undead Crown\":\"May 17, 2026 · 01:45\",\"Tomb Reaver\":\"Jun 18, 2026 · 02:19\",\"Toothrow\":\"May 22, 2026 · 00:59\",\"Treads of Cthon\":\"May 20, 2026 · 19:21\",\"The Ward\":\"May 18, 2026 · 00:40\",\"Thundergod's Vigor\":\"May 20, 2026 · 02:19\",\"Tiamat's Rebuke\":\"May 15, 2026 · 18:24\",\"Todesfaelle Flamme\":\"Jun 4, 2026 · 01:23\",\"The Rising Sun\":\"Jun 3, 2026 · 00:48\",\"The Salamander\":\"May 18, 2026 · 01:26\",\"The Spirit Shroud\":\"Jun 6, 2026 · 20:49\",\"The Vile Husk\":\"Jun 30, 2026 · 21:17\",\"The Jade Tan Do\":\"May 19, 2026 · 23:44\",\"The Minotaur\":\"Jul 6, 2026 · 21:10\",\"The Patriarch\":\"May 15, 2026 · 01:19\",\"The Reaper's Toll\":\"May 18, 2026 · 21:15\",\"The Gavel of Pain\":\"Jun 10, 2026 · 01:57\",\"The General's Tan Do Li Ga\":\"May 17, 2026 · 01:37\",\"The Grandfather\":\"Jun 4, 2026 · 01:41\",\"The Grim Reaper\":\"May 17, 2026 · 01:43\",\"Tearhaunch\":\"May 15, 2026 · 18:36\",\"The Battlebranch\":\"May 26, 2026 · 00:14\",\"The Chieftain\":\"May 18, 2026 · 21:04\",\"The Face of Horror\":\"May 20, 2026 · 02:19\",\"Suicide Branch\":\"May 27, 2026 · 00:49\",\"Swordguard\":\"Jun 22, 2026 · 02:57\",\"Stoneraven\":\"Jun 4, 2026 · 01:22\",\"Stormguild\":\"May 18, 2026 · 01:40\",\"Stormshield\":\"May 27, 2026 · 19:51\",\"Stormspike\":\"Jun 18, 2026 · 00:14\",\"Stormstrike\":\"May 17, 2026 · 01:53\",\"Stoutnail\":\"Jun 22, 2026 · 02:25\",\"Steel Shade\":\"May 18, 2026 · 01:50\",\"Steelclash\":\"May 21, 2026 · 11:51\",\"Steeldriver\":\"May 18, 2026 · 02:03\",\"Spire of Honor\":\"May 27, 2026 · 20:16\",\"Spirit Forge\":\"Jun 18, 2026 · 01:03\",\"Stealskull\":\"May 31, 2026 · 21:37\",\"Snowclash\":\"May 19, 2026 · 16:12\",\"Sparking Mail\":\"May 15, 2026 · 20:58\",\"Spellsteel\":\"May 17, 2026 · 23:50\",\"Skystrike\":\"May 18, 2026 · 00:38\",\"Snakecord\":\"May 15, 2026 · 00:58\",\"Skin of the Vipermagi\":\"May 20, 2026 · 22:27\",\"Skullder's Ire\":\"May 22, 2026 · 01:21\",\"Serpent Lord\":\"May 17, 2026 · 01:43\",\"Shaftstop\":\"May 31, 2026 · 20:50\",\"Sandstorm Trek\":\"Jun 25, 2026 · 00:56\",\"Schaefer's Hammer\":\"Jun 4, 2026 · 00:26\",\"Riphook\":\"May 27, 2026 · 20:59\",\"Rockfleece\":\"May 18, 2026 · 23:17\",\"Rockstopper\":\"May 27, 2026 · 19:44\",\"Rogue's Bow\":\"May 19, 2026 · 00:25\",\"Rattlecage\":\"Jun 21, 2026 · 17:52\",\"Raven Claw\":\"Jun 4, 2026 · 01:32\",\"Raven Frost\":\"May 25, 2026 · 21:26\",\"Razortail\":\"May 21, 2026 · 01:03\",\"Ribcracker\":\"May 17, 2026 · 01:32\",\"Pierre Tombale Couant\":\"Jul 6, 2026 · 22:43\",\"Plague Bearer\":\"May 27, 2026 · 01:29\",\"Pompeii's Wrath\":\"May 27, 2026 · 00:51\",\"Que-Hegan's Wisdom\":\"Jun 4, 2026 · 01:22\",\"Peasant Crown\":\"May 15, 2026 · 21:22\",\"Pelta Lunata\":\"Jun 29, 2026 · 01:20\",\"Nature's Peace\":\"May 23, 2026 · 01:06\",\"Nightsmoke\":\"May 15, 2026 · 20:17\",\"Nightwing's Veil\":\"May 18, 2026 · 00:38\",\"Nokozan Relic\":\"Jun 18, 2026 · 20:37\",\"Nord's Tenderizer\":\"May 18, 2026 · 20:53\",\"Nosferatu's Coil\":\"Jun 18, 2026 · 18:57\",\"Messerschmidt's Reaver\":\"May 31, 2026 · 23:46\",\"Moser's Blessed Circle\":\"Jun 10, 2026 · 21:55\",\"Manald Heal\":\"May 18, 2026 · 23:53\",\"Mang Song's Lesson\":\"May 31, 2026 · 21:00\",\"Marrowwalk\":\"Jun 21, 2026 · 20:12\",\"Lightsabre\":\"May 22, 2026 · 01:17\",\"Maelstrom\":\"Jun 1, 2026 · 01:00\",\"Magefist\":\"May 18, 2026 · 00:43\",\"Magewrath\":\"May 26, 2026 · 01:52\",\"Lava Gout\":\"May 18, 2026 · 21:11\",\"Kuko Shakaku\":\"Jun 19, 2026 · 00:46\",\"Lacerator\":\"Jun 4, 2026 · 01:41\",\"Lance Guard\":\"May 19, 2026 · 20:29\",\"Lance of Yaggai\":\"May 17, 2026 · 00:57\",\"Kira's Guardian\":\"May 19, 2026 · 20:39\",\"Iceblink\":\"May 15, 2026 · 20:54\",\"Infernostride\":\"May 20, 2026 · 21:58\",\"Ironstone\":\"May 19, 2026 · 20:30\",\"Jalal's Mane\":\"Jun 10, 2026 · 12:46\",\"Hotspur\":\"Jun 24, 2026 · 17:59\",\"Howltusk\":\"Jun 10, 2026 · 12:28\",\"Hellrack\":\"Jun 19, 2026 · 00:14\",\"Hexfire\":\"May 23, 2026 · 18:25\",\"Homunculus\":\"May 27, 2026 · 19:54\",\"Hone Sundan\":\"May 22, 2026 · 01:11\",\"Heart Carver\":\"May 26, 2026 · 00:19\",\"Heavenly Garb\":\"May 25, 2026 · 21:25\",\"Gravenspine\":\"May 17, 2026 · 01:51\",\"Gore Rider\":\"Jun 1, 2026 · 00:08\",\"Gorefoot\":\"Jun 12, 2026 · 23:47\",\"Goldskin\":\"May 15, 2026 · 15:20\",\"Goldstrike Arch\":\"May 18, 2026 · 00:37\",\"Goldwrap\":\"Jun 22, 2026 · 02:34\",\"Gimmershred\":\"May 28, 2026 · 20:14\",\"Ginther's Rift\":\"May 18, 2026 · 23:32\",\"Ethereal Edge\":\"May 31, 2026 · 20:47\",\"Firelizard's Talons\":\"May 20, 2026 · 01:36\",\"Flamebellow\":\"May 31, 2026 · 20:57\",\"Fleshripper\":\"May 28, 2026 · 20:23\",\"Ghoulhide\":\"May 15, 2026 · 20:23\",\"Doomslinger\":\"Jun 10, 2026 · 23:51\",\"Duriel's Shell\":\"Jun 1, 2026 · 00:28\",\"Duskdeep\":\"Jun 22, 2026 · 02:51\",\"Demonhorn's Edge\":\"May 18, 2026 · 01:05\",\"Demon Limb\":\"Jun 2, 2026 · 01:09\",\"Demon Machine\":\"May 25, 2026 · 21:56\",\"Demon's Arch\":\"May 18, 2026 · 01:40\",\"Death Cleaver\":\"May 19, 2026 · 16:05\",\"Crow Caw\":\"May 20, 2026 · 01:36\",\"Crushflange\":\"Jun 15, 2026 · 02:37\",\"Coldkill\":\"Jun 4, 2026 · 11:27\",\"Crainte Vomir\":\"Jul 6, 2026 · 21:05\",\"Cranebeak\":\"Jun 1, 2026 · 00:29\",\"Cloudcrack\":\"Jun 4, 2026 · 01:24\",\"Coif of Glory\":\"May 15, 2026 · 20:02\",\"Bverrit Keep\":\"May 18, 2026 · 00:33\",\"Carin Shard\":\"Jun 10, 2026 · 22:36\",\"Cerebus' Bite\":\"Jun 24, 2026 · 17:27\",\"Boneflesh\":\"May 26, 2026 · 01:21\",\"Bonehew\":\"Jun 18, 2026 · 02:21\",\"Boneslayer Blade\":\"May 21, 2026 · 13:24\",\"Bonesnap\":\"Jun 4, 2026 · 01:45\",\"Brainhew\":\"Jun 4, 2026 · 01:24\",\"Buriza-Do Kyanon\":\"May 31, 2026 · 20:46\",\"Blastbark\":\"Jun 22, 2026 · 01:56\",\"Bloodfist\":\"Jun 19, 2026 · 21:36\",\"Bloodletter\":\"May 15, 2026 · 17:47\",\"Bloodrise\":\"May 24, 2026 · 02:09\",\"Blade of Ali Baba\":\"May 25, 2026 · 23:55\",\"Bladebuckle\":\"May 27, 2026 · 20:11\",\"Bing Sz Wang\":\"May 31, 2026 · 20:42\",\"Black Hades\":\"Jun 22, 2026 · 02:08\",\"Blackhorn's Face\":\"Jun 15, 2026 · 02:54\",\"Blackleach Blade\":\"Jun 15, 2026 · 02:48\",\"Atma's Scarab\":\"Jun 19, 2026 · 20:17\",\"Bartuc's Cut-Throat\":\"May 20, 2026 · 02:19\",\"Andariel's Visage\":\"May 25, 2026 · 21:32\",\"Arioc's Needle\":\"May 21, 2026 · 12:53\",\"Arm of King Leoric\":\"May 26, 2026 · 00:00\",\"Wraithstep\":\"Jul 6, 2026 · 22:06\",\"Zakarum's Hand\":\"May 23, 2026 · 18:22\",\"Woestave\":\"May 20, 2026 · 13:50\",\"Viperfork\":\"May 18, 2026 · 23:36\",\"The Scalper\":\"May 20, 2026 · 02:19\",\"The Tannr Gorerod\":\"Jun 1, 2026 · 02:09\",\"The Iron Jang Bong\":\"May 19, 2026 · 19:54\",\"The Mahim-Oak Curio\":\"May 18, 2026 · 00:15\",\"The Fetid Sprinkler\":\"May 23, 2026 · 18:03\",\"The Dragon Chang\":\"Jun 10, 2026 · 22:13\",\"Steelgoad\":\"May 20, 2026 · 22:29\",\"Stone Crusher\":\"May 29, 2026 · 00:28\",\"Spineripper\":\"May 18, 2026 · 01:35\",\"Soul Harvest\":\"May 31, 2026 · 21:18\",\"Soulflay\":\"May 25, 2026 · 19:04\",\"Spectral Shard\":\"May 24, 2026 · 21:45\",\"Skewer of Krintiz\":\"May 15, 2026 · 21:06\",\"Skull Splitter\":\"May 20, 2026 · 01:42\",\"Shadowfang\":\"May 27, 2026 · 23:48\",\"Ripsaw\":\"May 15, 2026 · 20:51\",\"Rune Master\":\"Jun 3, 2026 · 00:20\",\"Rusthandle\":\"May 31, 2026 · 20:39\",\"Razortine\":\"May 18, 2026 · 01:47\",\"Moonfall\":\"May 15, 2026 · 20:12\",\"Medusa's Gaze\":\"May 27, 2026 · 19:45\",\"Latent Black Cleft\":\"Jun 8, 2026 · 17:26\",\"Latent Cold Rupture\":\"Jun 12, 2026 · 00:40\",\"Latent Crack of the Heavens\":\"Jun 25, 2026 · 00:47\",\"Latent Rotting Fissure\":\"Jun 18, 2026 · 02:24\",\"Leadcrow\":\"Jun 4, 2026 · 00:40\",\"Langer Briser\":\"Jun 8, 2026 · 19:53\",\"Knell Striker\":\"Jun 29, 2026 · 00:57\",\"Kelpie Snare\":\"May 29, 2026 · 00:46\",\"Kinemil's Awl\":\"Jun 10, 2026 · 16:01\",\"Ichorsting\":\"May 18, 2026 · 00:17\",\"Iron Pelt\":\"Jun 4, 2026 · 20:41\",\"Horizon's Tornado\":\"May 31, 2026 · 21:23\",\"Humongous\":\"May 18, 2026 · 01:40\",\"Husoldal Evo\":\"May 19, 2026 · 20:29\",\"Hellcast\":\"May 17, 2026 · 23:53\",\"Hellplague\":\"May 15, 2026 · 00:04\",\"Herald of Zakarum\":\"May 27, 2026 · 22:31\",\"Griswold's Edge\":\"May 15, 2026 · 20:10\",\"Grim's Burning Dead\":\"Jun 24, 2026 · 17:57\",\"Goreshovel\":\"May 14, 2026 · 19:15\",\"Gleamscythe\":\"Jun 1, 2026 · 01:58\",\"Dreadfang\":\"May 25, 2026 · 21:35\",\"Dimoak's Hew\":\"May 25, 2026 · 23:47\",\"Dark Clan Crusher\":\"May 19, 2026 · 20:25\",\"Darkglow\":\"May 19, 2026 · 11:27\",\"Deathbit\":\"May 23, 2026 · 17:53\",\"Deathspade\":\"May 14, 2026 · 18:57\",\"Culwen's Point\":\"May 18, 2026 · 23:38\",\"Coldsteel Eye\":\"Jun 19, 2026 · 20:25\",\"Bloodpact Shard\":\"Jun 4, 2026 · 01:20\",\"Bloodthief\":\"May 14, 2026 · 18:53\",\"Bladebone\":\"May 12, 2026 · 00:43\",\"Blacktongue\":\"May 20, 2026 · 18:41\",\"Axe of Fechmar\":\"Jun 15, 2026 · 02:40\",\"Baezil's Vortex\":\"Jun 4, 2026 · 00:50\",\"Athena's Wrath\":\"May 19, 2026 · 00:19\",\"Nagelring\":\"May 19, 2026 · 16:08\",\"Djinn Slayer\":\"May 18, 2026 · 01:45\",\"Endlesshail\":\"Jun 24, 2026 · 17:56\",\"Hawkmail\":\"May 14, 2026 · 19:30\",\"Radament's Sphere\":\"May 18, 2026 · 23:24\",\"Rakescar\":\"May 25, 2026 · 23:49\",\"Skull Collector\":\"Jul 6, 2026 · 22:59\",\"Steel Carapace\":\"May 19, 2026 · 23:48\",\"String of Ears\":\"Jun 3, 2026 · 00:34\",\"Witchwild String\":\"Jun 2, 2026 · 01:04\",\"Aldur's Advance (boots)\":\"May 18, 2026 · 23:24\",\"Aldur's Rhythm (mace)\":\"May 18, 2026 · 23:39\",\"Aldur's Stony Gaze (helm)\":\"Jun 4, 2026 · 01:18\",\"Angelic Halo (ring)\":\"May 18, 2026 · 01:28\",\"Angelic Mantle (armor)\":\"May 14, 2026 · 18:27\",\"Angelic Sickle (sword)\":\"May 19, 2026 · 16:12\",\"Angelic Wings (amulet)\":\"May 19, 2026 · 23:47\",\"Arcanna's Deathwand (staff)\":\"May 15, 2026 · 20:47\",\"Arcanna's Flesh (armor)\":\"May 28, 2026 · 20:14\",\"Arcanna's Head (helm)\":\"May 14, 2026 · 20:17\",\"Arcanna's Sign (amulet)\":\"Jul 5, 2026 · 23:20\",\"Arctic Binding (belt)\":\"May 15, 2026 · 20:05\",\"Arctic Furs (armor)\":\"May 13, 2026 · 00:21\",\"Arctic Horn (bow)\":\"May 21, 2026 · 13:16\",\"Arctic Mitts (gloves)\":\"May 25, 2026 · 21:36\",\"Bane's Authority (belt)\":\"May 17, 2026 · 01:29\",\"Bane's Oathmaker (sword)\":\"May 19, 2026 · 20:30\",\"Bane's Wraithskin (armor)\":\"May 14, 2026 · 20:07\",\"Berserker's Hatchet (axe)\":\"May 18, 2026 · 23:14\",\"Berserker's Hauberk (armor)\":\"May 15, 2026 · 15:39\",\"Berserker's Headgear (helm)\":\"May 18, 2026 · 23:33\",\"Bul-Kathos' Sacred Charge (sword)\":\"May 18, 2026 · 02:25\",\"Cathan's Mesh (chainmail)\":\"May 15, 2026 · 14:23\",\"Cathan's Rule (rod)\":\"May 20, 2026 · 01:42\",\"Cathan's Seal (ring)\":\"May 16, 2026 · 01:20\",\"Cathan's Sigil (amulet)\":\"May 27, 2026 · 19:40\",\"Cathan's Visage (mask)\":\"May 18, 2026 · 00:45\",\"Civerb's Cudgel (scepter)\":\"Jun 4, 2026 · 12:57\",\"Civerb's Icon (amulet)\":\"May 19, 2026 · 23:43\",\"Civerb's Ward (shield)\":\"Jun 10, 2026 · 19:42\",\"Cleglaw's Claw (shield)\":\"May 27, 2026 · 19:30\",\"Cleglaw's Pincers (gloves)\":\"May 14, 2026 · 18:40\",\"Cleglaw's Tooth (sword)\":\"May 15, 2026 · 19:20\",\"Cow King's Hide (studded leather)\":\"May 20, 2026 · 01:50\",\"Cow King's Horns (war bonnet)\":\"May 17, 2026 · 01:56\",\"Credendum (mithril coil)\":\"May 18, 2026 · 23:22\",\"Dangoon's Teaching (reinforced mace)\":\"Jun 10, 2026 · 21:54\",\"Dark Adherent (dusk shroud)\":\"May 22, 2026 · 00:58\",\"Death's Touch (sword)\":\"May 15, 2026 · 18:10\",\"Griswold's Heart (armor)\":\"May 17, 2026 · 01:51\",\"Griswold's Valor (helm)\":\"Jun 8, 2026 · 16:10\",\"Guillaume's Face (winged helm)\":\"Jun 10, 2026 · 23:36\",\"Haemosu's Adamant (cuirass)\":\"May 18, 2026 · 00:32\",\"Horazon's Countenance (helm)\":\"May 19, 2026 · 21:06\",\"Horazon's Hold (gloves)\":\"May 15, 2026 · 20:03\",\"Horazon's Legacy (boots)\":\"May 19, 2026 · 00:23\",\"Hsarus' Iron Fist (shield)\":\"Jul 12, 2026 · 19:08\",\"Hsarus' Iron Heel (boots)\":\"May 25, 2026 · 01:50\",\"Hsarus' Iron Stay (belt)\":\"May 14, 2026 · 18:41\",\"Hwanin's Blessing (belt)\":\"May 14, 2026 · 23:38\",\"Hwanin's Justice (bill)\":\"Jun 3, 2026 · 21:44\",\"Hwanin's Refuge (tigulated mail)\":\"Jun 21, 2026 · 19:57\",\"Hwanin's Splendor (grand crown)\":\"May 29, 2026 · 00:52\",\"Immortal King's Detail (belt)\":\"May 18, 2026 · 23:34\",\"Immortal King's Forge (gloves)\":\"May 15, 2026 · 19:09\",\"Immortal King's Pillar (boots)\":\"Jun 2, 2026 · 01:06\",\"Immortal King's Stone Crusher (hammer)\":\"May 23, 2026 · 17:56\",\"Infernal Cranium (helm)\":\"Jun 29, 2026 · 01:31\",\"Infernal Sign (belt)\":\"May 15, 2026 · 18:36\",\"Infernal Torch (wand)\":\"May 27, 2026 · 23:58\",\"Iratha's Coil (helm)\":\"May 25, 2026 · 21:53\",\"Iratha's Collar (amulet)\":\"Jun 18, 2026 · 00:18\",\"Iratha's Cord (belt)\":\"May 14, 2026 · 23:56\",\"Iratha's Cuff (gloves)\":\"May 19, 2026 · 15:52\",\"Isenhart's Case (armor)\":\"May 15, 2026 · 20:06\",\"Isenhart's Horns (helm)\":\"May 17, 2026 · 01:29\",\"Isenhart's Lightbrand (sword)\":\"May 15, 2026 · 01:26\",\"Isenhart's Parry (shield)\":\"May 25, 2026 · 19:22\",\"M'avina's Caster (bow)\":\"Jun 10, 2026 · 21:12\",\"M'avina's Icy Clutch (gloves)\":\"May 18, 2026 · 23:22\",\"M'avina's Tenet (belt)\":\"May 19, 2026 · 00:18\",\"Magnus' Skin (sharkskin gloves)\":\"May 18, 2026 · 01:04\",\"Milabrega's Diadem (helm)\":\"May 27, 2026 · 00:51\",\"Milabrega's Orb (shield)\":\"May 15, 2026 · 18:02\",\"Milabrega's Robe (armor)\":\"May 19, 2026 · 22:59\",\"Milabrega's Rod (scepter)\":\"May 18, 2026 · 20:56\",\"Naj's Circlet (circlet)\":\"May 15, 2026 · 01:18\",\"Naj's Light Plate (hellforge plate)\":\"Jun 19, 2026 · 00:50\",\"Naj's Puzzler (elder staff)\":\"Jun 10, 2026 · 19:31\",\"Natalya's Shadow (armor)\":\"May 31, 2026 · 21:18\",\"Natalya's Soul (claws)\":\"May 27, 2026 · 01:02\",\"Ondal's Almighty (spired helm)\":\"May 18, 2026 · 00:58\",\"Rite of Passage (sharkskin boots)\":\"May 15, 2026 · 01:33\",\"Sander's Paragon (cap)\":\"Jun 7, 2026 · 23:03\",\"Sander's Riprap (heavy boots)\":\"May 15, 2026 · 01:19\",\"Sander's Superstition (bone wand)\":\"May 15, 2026 · 17:57\",\"Sander's Taboo (heavy gloves)\":\"May 18, 2026 · 01:45\",\"Sazabi's Cobalt Redeemer (cryptic sword)\":\"May 31, 2026 · 21:32\",\"Sigon's Gage (gloves)\":\"May 15, 2026 · 13:39\",\"Sigon's Guard (shield)\":\"May 20, 2026 · 12:43\",\"Sigon's Sabot (boots)\":\"May 15, 2026 · 01:29\",\"Sigon's Shelter (armor)\":\"May 15, 2026 · 01:00\",\"Sigon's Visor (helm)\":\"May 14, 2026 · 18:58\",\"Sigon's Wrap (belt)\":\"May 18, 2026 · 01:49\",\"Tal Rasha's Fine-Spun Cloth (belt)\":\"May 25, 2026 · 23:42\",\"Tal Rasha's Horadric Crest (helm)\":\"May 17, 2026 · 01:58\",\"Tal Rasha's Lidless Eye (orb)\":\"May 15, 2026 · 20:00\",\"Tancred's Crowbill (military pick)\":\"May 15, 2026 · 13:40\",\"Tancred's Skull (bone helm)\":\"May 15, 2026 · 15:24\",\"Tancred's Spine (full plate mail)\":\"May 15, 2026 · 17:46\",\"Tancred's Weird (amulet)\":\"May 18, 2026 · 00:23\",\"Trang-Oul's Guise (helm)\":\"May 29, 2026 · 00:46\",\"Trang-Oul's Scales (armor)\":\"May 26, 2026 · 00:17\",\"Vidala's Barb (bow)\":\"May 25, 2026 · 23:11\",\"Vidala's Fetlock (boots)\":\"May 15, 2026 · 17:59\",\"Vidala's Snare (amulet)\":\"May 19, 2026 · 16:08\",\"Whitstan's Guard (round shield)\":\"May 15, 2026 · 18:24\",\"Wilhelm's Pride (battle belt)\":\"Jun 25, 2026 · 00:24\",\"Natalya's Mark (boots)\":\"Aug 6, 2026 · 01:38\",\"Sazabi's Ghost Liberator (balrog skin)\":\"Aug 6, 2026 · 08:09\",\"Baranar's Star\":\"Aug 10, 2026 · 20:29\",\"Atma's Wail\":\"Aug 10, 2026 · 21:23\"}",
  "d2r_setPieces": "[\"Aldur's Advance (boots)\",\"Aldur's Rhythm (mace)\",\"Aldur's Stony Gaze (helm)\",\"Angelic Halo (ring)\",\"Angelic Mantle (armor)\",\"Angelic Sickle (sword)\",\"Angelic Wings (amulet)\",\"Arcanna's Deathwand (staff)\",\"Arcanna's Flesh (armor)\",\"Arcanna's Head (helm)\",\"Arcanna's Sign (amulet)\",\"Arctic Binding (belt)\",\"Arctic Furs (armor)\",\"Arctic Horn (bow)\",\"Arctic Mitts (gloves)\",\"Bane's Authority (belt)\",\"Bane's Oathmaker (sword)\",\"Bane's Wraithskin (armor)\",\"Berserker's Hatchet (axe)\",\"Berserker's Hauberk (armor)\",\"Berserker's Headgear (helm)\",\"Bul-Kathos' Sacred Charge (sword)\",\"Cathan's Mesh (chainmail)\",\"Cathan's Rule (rod)\",\"Cathan's Seal (ring)\",\"Cathan's Sigil (amulet)\",\"Cathan's Visage (mask)\",\"Civerb's Cudgel (scepter)\",\"Civerb's Icon (amulet)\",\"Civerb's Ward (shield)\",\"Cleglaw's Claw (shield)\",\"Cleglaw's Pincers (gloves)\",\"Cleglaw's Tooth (sword)\",\"Cow King's Hide (studded leather)\",\"Cow King's Horns (war bonnet)\",\"Credendum (mithril coil)\",\"Dangoon's Teaching (reinforced mace)\",\"Dark Adherent (dusk shroud)\",\"Death's Touch (sword)\",\"Griswold's Heart (armor)\",\"Griswold's Valor (helm)\",\"Guillaume's Face (winged helm)\",\"Haemosu's Adamant (cuirass)\",\"Horazon's Countenance (helm)\",\"Horazon's Hold (gloves)\",\"Horazon's Legacy (boots)\",\"Hsarus' Iron Fist (shield)\",\"Hsarus' Iron Heel (boots)\",\"Hsarus' Iron Stay (belt)\",\"Hwanin's Blessing (belt)\",\"Hwanin's Justice (bill)\",\"Hwanin's Refuge (tigulated mail)\",\"Hwanin's Splendor (grand crown)\",\"Immortal King's Detail (belt)\",\"Immortal King's Forge (gloves)\",\"Immortal King's Pillar (boots)\",\"Immortal King's Stone Crusher (hammer)\",\"Infernal Cranium (helm)\",\"Infernal Sign (belt)\",\"Infernal Torch (wand)\",\"Iratha's Coil (helm)\",\"Iratha's Collar (amulet)\",\"Iratha's Cord (belt)\",\"Iratha's Cuff (gloves)\",\"Isenhart's Case (armor)\",\"Isenhart's Horns (helm)\",\"Isenhart's Lightbrand (sword)\",\"Isenhart's Parry (shield)\",\"M'avina's Caster (bow)\",\"M'avina's Icy Clutch (gloves)\",\"M'avina's Tenet (belt)\",\"Magnus' Skin (sharkskin gloves)\",\"Milabrega's Diadem (helm)\",\"Milabrega's Orb (shield)\",\"Milabrega's Robe (armor)\",\"Milabrega's Rod (scepter)\",\"Naj's Circlet (circlet)\",\"Naj's Light Plate (hellforge plate)\",\"Naj's Puzzler (elder staff)\",\"Natalya's Shadow (armor)\",\"Natalya's Soul (claws)\",\"Ondal's Almighty (spired helm)\",\"Rite of Passage (sharkskin boots)\",\"Sander's Paragon (cap)\",\"Sander's Riprap (heavy boots)\",\"Sander's Superstition (bone wand)\",\"Sander's Taboo (heavy gloves)\",\"Sazabi's Cobalt Redeemer (cryptic sword)\",\"Sigon's Gage (gloves)\",\"Sigon's Guard (shield)\",\"Sigon's Sabot (boots)\",\"Sigon's Shelter (armor)\",\"Sigon's Visor (helm)\",\"Sigon's Wrap (belt)\",\"Tal Rasha's Fine-Spun Cloth (belt)\",\"Tal Rasha's Horadric Crest (helm)\",\"Tal Rasha's Lidless Eye (orb)\",\"Tancred's Crowbill (military pick)\",\"Tancred's Skull (bone helm)\",\"Tancred's Spine (full plate mail)\",\"Tancred's Weird (amulet)\",\"Trang-Oul's Guise (helm)\",\"Trang-Oul's Scales (armor)\",\"Vidala's Barb (bow)\",\"Vidala's Fetlock (boots)\",\"Vidala's Snare (amulet)\",\"Whitstan's Guard (round shield)\",\"Wilhelm's Pride (battle belt)\",\"Natalya's Mark (boots)\",\"Sazabi's Ghost Liberator (balrog skin)\"]",
  "d2r_grailUnfound": "{\"Gravepalm\":1,\"Chance Guards\":1,\"Blackbog's Sharp\":1,\"Pluckeye\":1,\"Lidless Wall\":1,\"Hellslayer\":1,\"Islestrike\":1,\"Vampire Gaze\":1,\"Sureshrill Frost\":1}",
  "d2r_owned": "[\"Andariel's Visage\",\"Bartuc's Cut-Throat\",\"Blade of Ali Baba\",\"Goldstrike Arch\",\"Gore Rider\",\"Atma's Wail\"]",
  "d2r_chronSyncMerged_v1": "1"
};

function loadRealLedger(): Record<string, string> | null {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { DatabaseSync } = require('node:sqlite');
    const db = new DatabaseSync(LEDGER_DB, { readOnly: true });
    try {
      const rows = db.prepare('SELECT key, value FROM ItemTable').all() as Array<{ key: unknown; value: unknown }>;
      const out: Record<string, string> = {};
      for (const row of rows) {
        // WKWebView stores both key and value as UTF-16LE bytes.
        const k = typeof row.key === 'string' ? row.key : Buffer.from(row.key as any).toString('utf16le');
        const v = typeof row.value === 'string' ? row.value : Buffer.from(row.value as any).toString('utf16le');
        out[k] = v;
      }
      if (!out.d2r_foundLog) return null;
      return out;
    } finally { db.close(); }
  } catch (e) { return null; }
}

const REAL = loadRealLedger();
const LEDGER: Record<string, string> = REAL
  ? { d2r_foundLog: REAL.d2r_foundLog, d2r_setPieces: REAL.d2r_setPieces, d2r_grailUnfound: REAL.d2r_grailUnfound,
      d2r_owned: REAL.d2r_owned, d2r_chronSyncMerged_v1: REAL.d2r_chronSyncMerged_v1 }
  : REAL_SNAPSHOT;

// Guard against addInitScript re-seeding on every page.reload() — it re-runs on EVERY navigation,
// and a naive re-seed would overwrite whatever the app just wrote, then report "did not survive"
// for a wipe this harness caused. Sentinel key makes the write-in fire exactly once per context.
// NO FLAGS ARE PRE-SET: this is deliberately his true first load, where v1692's two-name apply and
// v1693's ruling + Diggler applies all fire in the same boot, 236 → 248 in one measured jump.
async function seed(page: any, overrides: Record<string, string> = {}) {
  const data = { ...LEDGER, ...overrides };
  await page.addInitScript((d: Record<string, string>) => {
    if (!localStorage.getItem('__v1693_seeded')) {
      for (const k of Object.keys(d)) { if (d[k] != null) localStorage.setItem(k, d[k]); }
      localStorage.setItem('__v1693_seeded', '1');
    }
    try { (window as any).__seedFoundLogKeys = Object.keys(JSON.parse(localStorage.getItem('d2r_foundLog') || '{}')).length; } catch (e) { (window as any).__seedFoundLogKeys = -1; }
    try { (window as any).__seedSetPieces = JSON.parse(localStorage.getItem('d2r_setPieces') || '[]').length; } catch (e) { (window as any).__seedSetPieces = -1; }
  }, data);
  await page.goto(URL);
  await page.waitForTimeout(1500);
}

async function openUniquesTab(page: any) {
  await page.click('.tab[data-tab="funi"]');
  await page.waitForTimeout(400);
  const txt = (await page.textContent('#funi-body')) || '';
  expect(txt.length, '#funi-body rendered nothing — every screen number below would be vacuous').toBeGreaterThan(50);
  return txt.replace(/\s+/g, ' ');
}

function namedCards(txt: string) {
  const m = txt.match(/named cards:\s*(\d+)\s*\/\s*(\d+)/);
  return m ? { found: Number(m[1]), total: Number(m[2]) } : { found: -1, total: -1 };
}

const scan = (page: any) => page.evaluate(() => {
  const w = window as any;
  const fl = JSON.parse(localStorage.getItem('d2r_foundLog') || '{}');
  const fu = (typeof w.funiScan === 'function') ? w.funiScan() : null;
  const unfound = JSON.parse(localStorage.getItem('d2r_grailUnfound') || '{}');
  return {
    bootFoundLogKeys: Object.keys(fl).length,
    seedFoundLogKeys: w.__seedFoundLogKeys,
    seedSetPieces: w.__seedSetPieces,
    // The page's OWN clock, formatted by the page's OWN stamper — the only value an undated find
    // is allowed to carry. Read here (not reconstructed in node) so a format change can't drift.
    stampNow: (typeof w._grailStamp === 'function') ? w._grailStamp() : null,
    // The v659 transcription of his own Chronicle screenshots, as the page holds it. This is the
    // SOURCE the apply's explicit .date strings were taken from — read live so test (4) compares
    // against the page's own copy rather than a literal that could drift out from under it.
    // NB: toggleOwned does NOT consult it (bible.html:18785 is a bare now-stamp); a name whose row
    // carries no .date gets TODAY, which is why every row in the v1693 apply carries one.
    seedDates: (() => { const g = w._GRAIL_SEED || {};
      return { 'Chance Guards': g['Chance Guards'] ?? null, 'The Diggler': g['The Diggler'] ?? null,
               size: Object.keys(g).length }; })(),
    found: fu ? fu.found : -1, total: fu ? fu.total : -1,
    foundLog: fl,
    grailUnfound: unfound,
    batches: JSON.parse(localStorage.getItem('d2r_chronApplied') || '[]'),
  };
});

/* ── (0) SANITY — his 346-key ledger loaded, the raw baseline it's built on is intact ──────────── */
test('(0) SANITY — his real 346-key ledger is in the page before any apply fires', async ({ page }) => {
  await seed(page);
  const s = await scan(page);
  expect(s.seedFoundLogKeys, 'HIS LEDGER DID NOT LOAD — every count below would be fiction').toBe(N_FOUNDLOG);
  expect(Object.keys(JSON.parse(LEDGER.d2r_grailUnfound)).length, 'd2r_grailUnfound going in').toBe(N_CONFLICTS);
  // Measured off the LOADED store, not constant-vs-constant: 346 keys minus the 110 set pieces the
  // page actually read back is the 236 raw-unique floor that 248 is built on. A constants-only
  // identity here could never go red and would prove nothing about the ledger in the page.
  expect(s.seedSetPieces, 'd2r_setPieces as the page read it').toBe(N_SETPIECES);
  expect(s.seedFoundLogKeys - s.seedSetPieces, 'his raw unique count as loaded — the number 248 is built on it').toBe(N_RAW_UNIQUES);
});

/* ── (1) FRESH LOAD — a true first boot, no flags pre-set: v1692's two + v1693's nine + The
   Diggler all fire in the same load, 236 → 248. RED against HEAD's committed bible.html (no
   working-tree changes): found stops at 238, none of the nine or Diggler land, d2r_grailUnfound
   stays at 9 keys — measured via the RED-PROVE seam in the header. */
test('(1) UP — first load applies v1692 + the nine + The Diggler, 236 → 248, and each lands honestly', async ({ page }) => {
  await seed(page);
  const s = await scan(page);
  const txt = await openUniquesTab(page);
  expect(namedCards(txt).found, 'the screen after the boot auto-apply').toBe(N_AFTER);
  expect(s.found, 'funiScan().found after the boot auto-apply').toBe(N_AFTER);
  expect(s.bootFoundLogKeys, 'his ledger grew by exactly the twelve applied names (2 + 9 + 1)').toBe(N_LEDGER_AFTER);
  for (const n of THE_NINE) {
    expect(Object.prototype.hasOwnProperty.call(s.foundLog, n), n + ' must be written to d2r_foundLog').toBe(true);
    expect(Object.prototype.hasOwnProperty.call(s.grailUnfound, n), n + ' must be DELETED from d2r_grailUnfound once applied — a leftover un-tick re-surfaces a solved conflict').toBe(false);
  }
  expect(Object.prototype.hasOwnProperty.call(s.foundLog, DIGGLER), DIGGLER + ' must be written to d2r_foundLog').toBe(true);
  expect(Object.keys(s.grailUnfound).length, 'd2r_grailUnfound must be empty — all nine conflicts resolved').toBe(0);
});

/* ── (2) SURVIVES RELOAD — the seed-floor must not re-suppress the applied names ─────────────── */
test('(2) RELOAD — the ten stay applied and d2r_grailUnfound stays empty after a real page reload', async ({ page }) => {
  await seed(page);
  await openUniquesTab(page); // let the first-load auto-apply run and render
  await page.reload();
  await page.waitForTimeout(1500);
  const s = await scan(page);
  const txt = await openUniquesTab(page);
  expect(namedCards(txt).found, 'the screen after reload — must NOT fall back to 238').toBe(N_AFTER);
  expect(s.found, 'funiScan().found after reload').toBe(N_AFTER);
  for (const n of THE_NINE) {
    expect(Object.prototype.hasOwnProperty.call(s.foundLog, n), n + ' survived the reload in d2r_foundLog').toBe(true);
  }
  expect(Object.keys(s.grailUnfound).length, 'd2r_grailUnfound stays empty across a reload — the seed floor did not resurrect the un-ticks').toBe(0);
});

/* ── (3) UNDO — this ship's own two batches (the nine, then The Diggler) reverse in full: two
   chronicleUndoLast() calls put the tally back at v1692's 238 floor AND restore all nine
   grailUnfound entries. Three batches were pushed at boot (v1692's two-name apply, THEN the ruling
   nine, THEN Diggler); undo pops LAST-IN-FIRST, so it takes exactly two calls to unwind this ship's
   part without touching v1692's — an undo that silently unwinds a PRIOR ship's write would be its
   own bug. A third call (not asserted here) would additionally undo v1692, which is out of scope
   for this ship's proof. ─────────────────────────────────────────────────────────────────────── */
test('(3) UNDO — two chronicleUndoLast() calls return 238 AND restore all nine grailUnfound entries', async ({ page }) => {
  await seed(page);
  await openUniquesTab(page);
  const before = await scan(page);
  expect(before.found, 'sanity before undo').toBe(N_AFTER);
  expect(before.batches.length, 'three batches recorded at boot: v1692, the ruling nine, The Diggler').toBe(3);

  const u1 = await page.evaluate(() => (window as any).chronicleUndoLast()); // undoes Diggler (last pushed)
  const u2 = await page.evaluate(() => (window as any).chronicleUndoLast()); // undoes the ruling nine
  await page.click('.tab[data-tab="funi"]');
  await page.waitForTimeout(400);
  const after = await scan(page);
  const txt = (await page.textContent('#funi-body')) || '';

  expect(u1.undone, 'first undo reverses The Diggler batch').toBe(1);
  expect(u2.undone, 'second undo reverses the nine-name ruling batch').toBe(THE_NINE.length);
  expect(after.found, 'funiScan().found back to the v1692-only 238').toBe(N_V1692_ONLY);
  expect(namedCards(txt.replace(/\s+/g, ' ')).found, 'the screen back to 238').toBe(N_V1692_ONLY);
  expect(after.bootFoundLogKeys, 'his ledger back to the v1692-only key count').toBe(N_FOUNDLOG + 2);
  const restored = JSON.parse(LEDGER.d2r_grailUnfound);
  expect(after.grailUnfound, 'd2r_grailUnfound restored to exactly what it was before the apply — an undo that leaves the un-ticks cleared is not an undo').toEqual(restored);
  for (const n of THE_NINE) {
    expect(Object.prototype.hasOwnProperty.call(after.foundLog, n), n + ' removed from d2r_foundLog by the undo').toBe(false);
  }
  expect(Object.prototype.hasOwnProperty.call(after.foundLog, DIGGLER), DIGGLER + ' removed from d2r_foundLog by the undo').toBe(false);
  // Fleshrender and Gloom's Trap (v1692's OWN batch) must be untouched — this undo is scoped to
  // this ship's writes only, not a blanket rollback of everything ever applied.
  expect(Object.prototype.hasOwnProperty.call(after.foundLog, 'Fleshrender'), "v1692's Fleshrender must survive — this undo is not v1692's").toBe(true);
});

/* ── (4) HONEST DATES — the eight corroborated names carry their real, independently-verified
   dates; and the remaining two, Chance Guards and The Diggler, are pinned POSITIVELY to the exact
   value each is entitled to — not merely excluded from a list of eight neighbours.

   Why positively: an earlier draft asserted only `!CORROBORATED_DATES.includes(chanceGuards)`,
   which a mutant carrying a wholly fabricated 'Jul 4, 2026 · 03:11' passed. Every invented date in
   history passed it. The two pins below were then MEASURED against the working tree. CHANCE GUARDS
   is stamped 'Jun 8, 2026 · 23:22' because the apply passes that seed minute EXPLICITLY — nothing
   falls back to _GRAIL_SEED on its behalf (see header ⚠2) — so the honest pin is equality with the
   seed the value was taken from, which also goes red if that explicit date is ever removed. THE
   DIGGLER has no witness at all and is stored as the PARTIAL READING itself, so its pin is that the
   value stays unreadable — red on a completion, red on a now-stamp standing in for evidence. */
test('(4) PROVENANCE — the eight keep their real dates; Chance Guards = the seed verbatim, The Diggler stays unreadable, neither invented', async ({ page }) => {
  await seed(page);
  await openUniquesTab(page);
  const s = await scan(page);
  for (const [name, date] of Object.entries(CORROBORATED_DATES)) {
    expect(s.foundLog[name], name + " must carry its independently-corroborated First Found date, not a bare now-stamp").toBe(date);
  }

  // The page's own formatter is the reference. Two days are allowed only to absorb a midnight
  // rollover between the boot-time apply and this read (seconds apart); a fabricated date is
  // months away, so the tolerance cannot hide the defect this test exists to catch.
  const allowedDays: string[] = await page.evaluate(() => {
    const fmt = (d: Date) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    const now = new Date();
    return [fmt(now), fmt(new Date(now.getTime() - 6 * 3600 * 1000))];
  });
  // Instrument check first: if _grailStamp's format ever drifts from the line above, this fails
  // loudly instead of silently making the two assertions below unfalsifiable.
  expect(s.stampNow, 'window._grailStamp() must exist — without it there is no reference for "today"').toBeTruthy();
  expect(allowedDays, "the page's own _grailStamp() must agree with this test's day format").toContain(String(s.stampNow).split(' · ')[0]);

  for (const name of ['Chance Guards', DIGGLER]) {
    expect(s.foundLog[name], name + ' must be present in d2r_foundLog').toBeTruthy();
  }

  // CHANCE GUARDS — measured, not assumed: the apply passes the seed's own minute EXPLICITLY
  // (bible.html:36257, `date: 'Jun 8, 2026 · 23:22'`), and chronicleApply installs it by swapping
  // window._grailStamp for the length of that one add. There is NO seed fallback in toggleOwned —
  // bible.html:18785 is a bare now-stamp — so that explicit date is the ONLY thing keeping today's
  // date out of his ledger; deleting it fabricates one. The honest expectation is therefore
  // EQUALITY WITH THE SEED, byte for byte — a cited historical date, not a borrowed neighbour's
  // and not a fabrication. Anything else (a copied minute, a hand-typed date, a now-stamp where a
  // citation exists) fails here with both strings printed.
  expect(s.seedDates['Chance Guards'], '_GRAIL_SEED must actually hold Chance Guards, or the assertion below is unfalsifiable').toBeTruthy();
  expect(s.foundLog['Chance Guards'], "Chance Guards must carry the v659 _GRAIL_SEED transcription of his own Chronicle verbatim — no invented or borrowed date")
    .toBe(s.seedDates['Chance Guards']);

  // THE DIGGLER — the genuinely unreadable one. Its frame reads "?/27/2026, ?:15" with the month
  // and hour under a tooltip, and NO second witness exists (absent from _GRAIL_SEED, checked
  // below), so nothing in this repo knows its date. The stored value must therefore still be
  // UNREADABLE: the '?' markers for month AND hour intact, the readable fragments 27/2026 and :15
  // intact. This is the brief's named trap — a partial date must never become a whole one — and it
  // goes red three ways: on a completion ('Jul 27, 2026 · 03:15'), on a today-stamp standing in
  // for evidence ('Aug 11, 2026 · …' would lose the '?' and the fragments), and on a 1970/epoch
  // fallback. Asserted by shape, not verbatim, so re-wording the marker does not fake-fail it.
  expect(s.seedDates['The Diggler'], 'The Diggler must be ABSENT from _GRAIL_SEED — a second witness would change what "honest" means here').toBeNull();
  const dig = String(s.foundLog[DIGGLER]);
  expect(dig, "The Diggler's month is unreadable and must STAY unreadable — got: " + dig).toMatch(/\?\/27\/2026/);
  expect(dig, "The Diggler's hour is unreadable and must STAY unreadable — got: " + dig).toMatch(/\?:15/);
  expect(dig, 'The Diggler must NOT be completed into a whole stamped date — that would be invented history (got: ' + dig + ')')
    .not.toMatch(/^[A-Z][a-z]{2} \d{1,2}, \d{4} · \d{2}:\d{2}$/);
  expect(allowedDays.some(d => dig.startsWith(d)), 'The Diggler must NOT be silently now-stamped either — a today date here is a fabricated fact wearing today\'s clothes (got: ' + dig + ')').toBe(false);
});
