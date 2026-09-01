#!/usr/bin/env python3
"""
VISUAL-LOCK invariant — freezes the tokenized TYPE SYSTEM so it can't silently drift.

Konyo's VISUAL-LOCK goal: after the weight type system was single-sourced onto CSS custom
properties (console + bible, v1288-v1321), lock it with an invariant test so no future edit
can quietly reintroduce a raw `font-weight:NNN` literal instead of a `var(--fw-*)` token.

Checks (both surfaces — bible.html + tv/control_ui.html):
  1. ZERO raw font-weight literals (`font-weight: NNN`, spaced or not) — every weight MUST be
     a `var(--fw-*)` token. Fails loudly naming file:line of any offender.
  2. The `--fw-*` token set is defined in :root (the source of truth for weights).
  3. STRUCTURE-LOCK (v1343, console only): the `--hd-*` spacing/structure token set is defined
     in :root — the region-gutter / card-pad / header-gap / console-card-radius rhythm the console
     structure is single-sourced onto. Their presence is locked (they can't be silently deleted);
     the values live in :root as the one place to tune the layout rhythm.

Run:  python3 visual_lock_invariant.py        (exit 0 = locked · exit 1 = drift, with details)
CI:   add to any gate — no deps, pure stdlib, ~instant.
Docs: LOCKED_TYPE_SYSTEM.md
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# Surfaces under lock + the --fw tokens each is expected to define in :root.
# (bible uses the full 6-weight range; the console uses the 4 it needs.)
SURFACES = {
    "bible.html":        {"path": os.path.join(ROOT, "bible.html"),
                          "fw": ["regular", "normal", "medium", "semibold", "bold", "black"],
                          # LS/LH-LOCK (v1344) — the bible's letter-spacing + line-height token scale
                          # (console-mirrored role names; the approved deliberate normalization).
                          "ls": ["tight", "snug", "normal", "wide", "label", "wider", "widest"],
                          "lh": ["none", "tightest", "tight", "snug", "normal", "relaxed", "loose"],
                          # v2133 — the HINT lane's floor. Both surfaces carry the same prose
                          # tooltip and the board is iframed INTO the console, so they share one
                          # screen and must share one floor.
                          "typeFloor": [("#arttip.tip-say .att-say", 13)]},
    "tv/control_ui.html": {"path": os.path.join(ROOT, "tv", "control_ui.html"),
                           "fw": ["normal", "medium", "semibold", "bold"],
                           # STRUCTURE-LOCK (v1343+): the console's shared spacing/structure rhythm —
                           # every padding tier (card · row · compact), the radius pair, header chrome.
                           "hd": ["gap", "gap-in", "gap-row", "pad-y", "pad-x", "head-mb",
                                  "head-ls", "head-size", "radius", "radius-in", "pad-row-y", "pad-row-x",
                                  "pad-compact-y", "pad-compact-x"],
                           # LS/LH-LOCK (v1347) — the console's letter-spacing + line-height scales,
                           # SAME role-names as the bible so both surfaces share one vocabulary.
                           "ls": ["tight", "snug", "normal", "wide", "label", "wider", "widest"],
                           "lh": ["none", "tightest", "tight", "snug", "normal", "relaxed", "loose"],
                           "typeFloor": [("#itip.tip-say .itip-say", 13)]},
}

RAW_WEIGHT = re.compile(r"font-weight: *[0-9]+")   # spaced or not; !important-agnostic
# v1324 — also catch the `font:` SHORTHAND weight (font: 700 11px/1 …), which the
# font-weight:-only pattern missed (a real blind spot found after v1321). Only the 6
# named weight values, boundary-terminated so `font: 14px`/`font: var(--fw-*)` never match.
RAW_SHORTHAND = re.compile(r"font: *(?:400|500|600|700|800|900)\b")


# ── SIZE-LOCK (v2405, rebuilt v2406 after a cold cross-family read) ─────────────────────────────
#
# The weight promise is enforced: ZERO raw font-weight literals on both surfaces. The SIZE promise
# was made in the same breath — nine --fs-* tokens — and nothing checked it until v2405.
#
# ⚠ v2405 SHIPPED THIS RULE OVER ONLY ONE OF THE TWO SURFACES, AND THE REASON WAS A NUMBER I NEVER
# CHECKED. I wrote that grandfathering bible.html "would be a 952-entry allowlist, which is not a
# lock, it is a wall of debt with a green light on it", and excluded it. A cold review asked whether
# that was defensible or "the rule quietly failing where the problem is worst". It was the latter,
# and one measurement settled it: 952 is the number of SITES. The number of DISTINCT VALUES is 136.
# 136 is enumerable. The exclusion was reasoning from the wrong quantity — a count of occurrences
# standing in for a count of things to decide about. [[feedback-suspect-the-instrument]]
#
# The same review caught a real hole: `font: var(--fw-bold) 1.05em/1 var(--serif)` sets a SIZE that
# a `font-size:`-only pattern never sees. The weight rule has carried RAW_SHORTHAND since v1324 for
# exactly this reason on its own axis; the size rule shipped without the equivalent. Measured: 6
# such sites on the console, 21 on the bible.
#
# It also claimed calc()/clamp() slip past. They do not — anything not starting `var(--fs` fails, so
# the rule FAILS CLOSED. Verified by planting `calc(1em + 2px)` and `clamp(9px,1vw,11px)`: both
# caught. Recorded because a refuted finding is worth as much as a confirmed one.
#
# ── TWO SURFACES, TWO INSTRUMENTS, ON PURPOSE ──
#
#   tv/control_ui.html  15 values / 20 sites  — ENUMERATED, each with a written reason and a CAP.
#   bible.html         136 values / 1039 sites — a RATCHET in size_debt.json: no new value, and no
#                       existing value may grow. Generated, not hand-written.
#
# ⚠ A CAP, NOT A BARE ALLOWLIST — this is the review's sharpest point and it was right. v2405
# allowed a value ANYWHERE once it appeared once, so `.78em` (justified for 3 sites in the receipt
# strip) was silently licensed for the whole file, and the exceptions could never be driven down.
# Pinning the COUNT means a new use fails even though the value is known.
#
# ⚠ AND A COUNT IS A RATCHET, NOT A LAW. A count pin cannot tell a new escape from an old one moving
# — remove one `.78em` and add another elsewhere and this still passes. That is the exact weakness
# [[regression-guard]] warns about, so it is named here rather than papered over. It is the right
# tool for DEBT (which only has to shrink) and the wrong tool for a LAW. The law is "no raw
# font-size"; these numbers are the distance still to travel.
RAW_SIZE = re.compile(r"font-size: *([^;}\n]+)")
#: the SHORTHAND's size slot — `font: <weight> <size>/<lh> <family>`. Boundary-anchored to a real
#: size token so `font: var(--fw-bold) var(--fs-sm)/1 …` never matches.
RAW_SHORTHAND_SIZE = re.compile(r"font: *([^;}\n]+)")
_SIZE_TOKEN = re.compile(r"(clamp\([^)]*\)|[0-9]*\.?[0-9]+(?:px|em|rem|%|pt))")

DEBT_PATH = os.path.join(ROOT, "size_debt.json")

#: value -> (cap, why). Exceeding the cap fails even though the value is known.
CONSOLE_SIZES = {
    "0":                    (1, "inline-block whitespace collapse on .zone — a technique, not a size"),
    ".78em":                (3, "the receipt strip (.rcpt) — em fractions, see the conversion note"),
    ".8em":                 (1, ".hd-hist-head:focus-visible"),
    ".82em":                (1, "#rcpt-full img"),
    ".86em":                (1, ".chron-waiting:hover .cw-go"),
    ".9em":                 (1, ".rcpt"),
    ".92em":                (1, ".dfp-farm"),
    ".95em":                (1, ".find-card .fc-name"),
    "1.05em":               (4, ".dl-trace / .bt / .dsr-chap:hover / .dsr-recov"),
    "1.08em":               (1, ".zone-banner:first-child"),
    "28px":                 (1, ".stage-hold[hidden]"),
    "34px":                 (1, ".hd-hist-empty"),
    "44px":                 (1, ".dsr-cover-fb"),
    "56px":                 (1, ".sh-empty-hero"),
    "clamp(26px,3vw,40px)": (1, ".intake-hero[hidden]"),
    "font:1.05em":                  (1, "shorthand, .bt — the size rides in the font: slot"),
    "font:12px":                    (1, "shorthand"),
    "font:clamp(15px,1.6vw,20px)":  (1, "shorthand, a display heading"),
    "font:clamp(17px,1.65vw,21px)": (1, "shorthand, a display heading"),
    "font:clamp(17px,1.8vw,23px)":  (1, "shorthand, a display heading"),
    "font:clamp(19px,2.1vw,27px)":  (1, "shorthand, a display heading"),
}
#: ⚠ CONVERTING AN em IS NOT A LOOKUP. `.78em` is 78% of whatever its parent computes to, and that
#: parent differs per site and per viewport — swapping it for an --fs-* clamp changes the rendered
#: size SILENTLY. Each is converted deliberately, rendered at 1440/1120/901/375/1120x628 before and
#: after and COMPARED. A find-and-replace here is a visual regression wearing a tidy diff.
#: [[visual-regression-detector]]


def _debt_size():
    try:
        with open(DEBT_PATH, encoding="utf-8") as fh:
            return len((json.load(fh) or {}).get("bible.html") or {})
    except Exception:
        return -1          # -1 reads as "could not be established", never as zero


def _raw_sizes(text):
    """-> Counter of normalised raw size values, from BOTH `font-size:` and the `font:` shorthand."""
    import collections
    c = collections.Counter()
    for m in RAW_SIZE.finditer(text):
        v = m.group(1).strip()
        if v.startswith("var(--fs"):
            continue
        c[re.sub(r"\s+", "", v)] += 1
    for m in RAW_SHORTHAND_SIZE.finditer(text):
        d = m.group(1)
        if "var(--fs" in d:
            continue
        mm = _SIZE_TOKEN.search(d)
        if mm:
            c["font:" + re.sub(r"\s+", "", mm.group(1))] += 1
    return c


def _sizes_are_tokenised(text, failures, surface):
    got = _raw_sizes(text)
    if surface == "tv/control_ui.html":
        for v, n in sorted(got.items()):
            cap = CONSOLE_SIZES.get(v)
            if cap is None:
                failures.append(
                    "%s: raw font-size `%s` (x%d) — every size here must be a var(--fs-*) token, "
                    "exactly as every weight must be var(--fw-*). If it is a genuinely new step in "
                    "the scale, ADD THE TOKEN; if it is a technique rather than a size, add it to "
                    "CONSOLE_SIZES with its reason and cap." % (surface, v, n))
            elif n > cap[0]:
                failures.append(
                    "%s: raw font-size `%s` used %d time(s), capped at %d (%s). The value is known "
                    "debt, not a licence — a new site must use a token even where an old one does "
                    "not." % (surface, v, n, cap[0], cap[1]))
        return
    if surface == "bible.html":
        # THE RATCHET. Generated snapshot; it may shrink freely and may never grow.
        try:
            with open(DEBT_PATH, encoding="utf-8") as fh:
                base = (json.load(fh) or {}).get("bible.html") or {}
        except Exception as e:
            failures.append("bible.html: size_debt.json could not be read (%s) — that is UNKNOWN, "
                            "not a clean surface. Regenerate with --snapshot and review the diff."
                            % e)
            return
        for v, n in sorted(got.items()):
            was = base.get(v)
            if was is None:
                failures.append(
                    "bible.html: NEW raw font-size `%s` (x%d). This surface is under a debt "
                    "RATCHET: the 136 values already here are recorded and may only shrink, but a "
                    "value that was not there before must be a var(--fs-*) token." % (v, n))
            elif n > was:
                failures.append(
                    "bible.html: raw font-size `%s` grew from %d to %d site(s). The ratchet only "
                    "turns one way." % (v, was, n))
        paid = sorted(k for k, v0 in base.items() if got.get(k, 0) < v0)
        if paid:
            print("   \u2139  size debt paid on %d value(s) since the snapshot (%s%s) — rerun with "
                  "--snapshot to tighten the ratchet."
                  % (len(paid), ", ".join(paid[:4]), " \u2026" if len(paid) > 4 else ""))


def _colour_carries_meaning(text, failures):
    """v2073 — LOCK THE COLOUR THAT CARRIES MEANING, not just the weight.

    Konyo, looking at both grail walls: "color sync for uniques / for set items... it was very
    pretty now its not as pretty". `_allGrid` renders the uniques wall AND the sets wall and took no
    rarity argument, so 120 item names printed in one flat cream on a page where every other surface
    colours an item by its rarity. A shared renderer with no rarity parameter CAN ONLY EVER PICK ONE
    COLOUR — and nothing failed, because this lock covered weight and structure and said nothing
    about colour. He was the detector. [[visual-regression-detector]]

    A rarity colour is the same KIND of promise as a weight token: it is meaning, not decoration.

    v2079 — AND IT LOCKED THE SPELLING RATHER THAN THE PROMISE. The first cut pinned the literal
    strings `.gf-piece .gp-nm-set{...}` and `' gp-nm-' + rar`, so collapsing those invented classes
    back onto the rule the page had carried since v1625 — a strictly better state — turned the lock
    RED while the pixels were correct. A lock that fails on a correct refactor spends the one thing
    it is for, his attention, on a lie, and the pressure it creates is to weaken it.

    So it asks the question the eye asks: DOES A MISSING ITEM NAME IN THIS TAB RESOLVE TO THIS TAB'S
    RARITY COLOUR? The class is read out of the renderer instead of being hardcoded here, so a
    rename passes and a deletion fails. [[source-reading-guard]] §1
    """
    m = re.search(r"gf-piece gf-miss.{0,400}?<span class=\"([a-z0-9 _-]+)\">'\+esc\(e\.n\)", text,
                  re.S)
    if not m:
        failures.append("bible.html: cannot find the class _allGrid puts on a wall item's NAME — "
                        "the renderer changed shape, so nothing below can be graded")
        return
    cls = (m.group(1).split() or [""])[-1]
    # v2120 (#43) — AND NOT INSIDE A COMMENT. This searched the raw file, so
    # `/* :is(#tab-forge) .f-craft{border-left-color:var(--q-orange)} */` satisfied it.
    # PROVEN BY SABOTAGE, not by reading: commenting out bible.html's only live .f-craft rule kept
    # this lock GREEN, while DELETING the same line correctly went red. The strip is
    # LENGTH-BOUNDED because an unbounded one once ate 16.9% of bible.html.
    # [[source-reading-guard]] [[feedback-comments-vs-code]]
    _uncommented = re.sub(r"/\*.{0,4000}?\*/", " ", text, flags=re.S)
    if len(_uncommented) < len(text) * 0.6:
        _uncommented = text          # the strip misfired — measure the real thing, never a ruin
    for tab, token, what in (("#tab-funi", "--q-unique", "UNIQUE in unique gold"),
                             ("#tab-fsets", "--q-set", "SET piece in set green")):
        # A rule that scopes to this tab, names the class the wall actually emits, and sets colour
        # from this tab's rarity token. All three in one declaration block, or the wall is flat.
        pat = re.compile(re.escape(tab) + r"[^{}]{0,200}\." + re.escape(cls)
                         + r"[^{}]{0,200}\{[^{}]{0,300}?color:\s*var\(" + re.escape(token) + r"\)")
        if not pat.search(_uncommented):
            failures.append("bible.html: the grail wall no longer names a %s — no rule under %s "
                            "binds .%s to var(%s)" % (what, tab, cls, token))
    # v2081 — EVERY CARD KIND IN THE FORGE FEED CARRIES A MEANING-BEARING RAIL, OR NONE DO.
    # Measured on a render with a full rune+gem stash: .f-now rgb(95,201,122), .f-pipe
    # rgb(91,159,208), .f-step rgb(205,177,87) — and .f-craft rgb(58,47,30), which is var(--border),
    # the fallback for a card with no rule at all. `.f-craft` appeared ZERO times as a selector while
    # `.f-craftrow`, `.f-craftacc` and `.f-craft-made` all existed, which is precisely why it read as
    # present. A cube craft sat in the same feed as a runeword carrying the ABSENCE of a colour.
    # The class is built dynamically ('f-card f-'+a.cls+' f-atom'), so no grep for the literal class
    # string finds it — this asks the STYLESHEET whether each kind has a rail.
    for kind, what in (("f-now", "a runeword you can forge NOW"),
                       ("f-pipe", "a chain one step away"),
                       ("f-step", "a step card"),
                       ("f-craft", "a CUBE CRAFT")):
        pat = re.compile(r"\.%s\s*\{[^{}]{0,200}?border-left-color\s*:" % re.escape(kind))
        if not pat.search(_uncommented):
            failures.append("bible.html: %s (.%s) has no border-left-color rule — it falls back to "
                            "var(--border) and its colour says nothing, beside siblings whose "
                            "colour is meaning" % (what, kind))

    # The glow means YOU HAVE IT. If it ever reaches the plain (missing) selector, colour and
    # ownership are being said with the same ink and neither reads.
    g = re.search(r"#tab-funi \.gf-piece \.[a-z0-9 ._,#-]{0,120}\{([^{}]{0,300})\}", text)
    if g and re.search(r"(?:^|[{;])\s*text-shadow\s*:", g.group(1)):
        failures.append("bible.html: the FOUND glow leaked onto every MISSING name in #tab-funi")


def _sealed_title_speaks_the_page(text, failures):
    """v2077 — the SEALED card is the proudest state on the board (99/99 runewords forged) and it
    was the only element speaking a different typographic language.

    MEASURED against h2 / .boss-name / .sec-h, all --serif-display:
        title   Cinzel 22px  weight 400   letter-spacing 4.4px   small-caps
        page    Cinzel 17px  weight 700   letter-spacing 0.34px  none

    Three departures at once — the only font-variant-caps on the page, the only --ls-wider display
    title (.20em, 13x the page's .34px), and NO declared weight so it fell to 400 beside siblings at
    700. Konyo read it exactly as it was: "something changed template style.. typography".

    Loud is fine. A DIFFERENT LANGUAGE is not. This pins the three departures, not the size.
    """
    import re as _re
    m = _re.search(r'\.forge-sealed \.fs-title\{([^}]*)\}', text)
    if not m:
        failures.append("bible.html: the .forge-sealed .fs-title rule is gone — the sealed card's "
                        "title now inherits whatever the page gives it")
        return
    rule = m.group(1)
    if "font-variant-caps" in rule:
        failures.append("bible.html: the SEALED title uses font-variant-caps, which nothing else on "
                        "this page does — that is what made it read as another template")
    if "--ls-wider" in rule:
        failures.append("bible.html: the SEALED title is tracked at --ls-wider (.20em); the page's "
                        "serif titles sit near .34px, so this sprawls beside every sibling")
    if "font-weight" not in rule:
        failures.append("bible.html: the SEALED title declares no font-weight, so it falls to 400 "
                        "while every other serif-display title on the page is 700")


def _no_orphaned_grid_card(text, failures):
    """v2075 — A CARD WITH NO AREA FALLS OUT OF THE LAYOUT AND NOBODY NOTICES.

    #tab-session's grid names its areas explicitly at >=960px. #sc-card-tvd was given NONE, so it
    auto-placed onto an implicit THIRD ROW and took one of three columns. MEASURED at 1440: row 3
    was 129.75px tall with tvd 561px wide in a 1395px grid — about 834x130px of nothing, every time
    he opened Sessions. Row 2 was 232.5px because `intel` is 233px while the TZ card is 105px,
    leaving ~127px of gap under it. Total 589px -> 462px once tvd had a home.

    Nothing failed, because CSS grid auto-placement is not an error — it is a silent fallback. So
    the lock is: every sc-card the grid holds must be NAMED in the template. A new card added
    without an area trips this instead of quietly landing in a row of its own.
    """
    import re as _re
    m = _re.search(r'#tab-session \.sc-grid-tf\{[^}]*grid-template-areas:([^;}]+)', text)
    if not m:
        failures.append("bible.html: #tab-session's grid no longer declares grid-template-areas — "
                        "every card then auto-places and the layout is whatever order the DOM is in")
        return
    areas = m.group(1)
    for card, area in (("#sc-card-tz", "tz"), ("#sc-card-intel", "intel"),
                       ("#sc-card-log", "log"), ("#sc-card-tvd", "tvd")):
        if ('"%s"' % area) not in areas and (" %s " % area) not in (" " + areas.replace('"', " ") + " "):
            failures.append("bible.html: %s has no place in the Sessions grid template — it will "
                            "auto-place onto a row of its own and leave the other columns empty"
                            % card)
        if ("%s{grid-area:%s}" % (card, area)) not in text.replace(" ", ""):
            failures.append("bible.html: %s is not assigned grid-area:%s — the template names the "
                            "area but nothing claims it" % (card, area))


def check():
    failures = []
    for name, cfg in SURFACES.items():
        try:
            with open(cfg["path"], encoding="utf-8") as fh:
                lines = fh.read().split("\n")
        except OSError as e:
            failures.append(f"{name}: cannot read ({e})")
            continue
        text = "\n".join(lines)
        if name.startswith("bible"):
            _colour_carries_meaning(text, failures)
            _no_orphaned_grid_card(text, failures)
            _sealed_title_speaks_the_page(text, failures)
        _sizes_are_tokenised(text, failures, name)
        # 1) no raw weight literals — every one must be var(--fw-*)
        for i, line in enumerate(lines, 1):
            for m in RAW_WEIGHT.finditer(line):
                failures.append(
                    f"{name}:{i}  RAW weight '{m.group(0).strip()}' — use var(--fw-*) instead")
            for m in RAW_SHORTHAND.finditer(line):
                failures.append(
                    f"{name}:{i}  RAW shorthand weight '{m.group(0).strip()}' — use font:var(--fw-*) instead")
        # 2) the --fw token set is defined
        for tok in cfg["fw"]:
            if not re.search(r"--fw-" + tok + r": *[0-9]+", text):
                failures.append(f"{name}  MISSING :root token --fw-{tok} (the weight source of truth)")
        # 3) STRUCTURE-LOCK — the --hd-* spacing/structure token set is defined (value-agnostic:
        #    px / clamp() / var() are all valid; we lock that the token EXISTS as the single source).
        for tok in cfg.get("hd", []):
            if not re.search(r"--hd-" + re.escape(tok) + r": *\S", text):
                failures.append(f"{name}  MISSING :root token --hd-{tok} (the structure rhythm source of truth)")
        # 4) LS/LH-LOCK — the letter-spacing / line-height token scales are defined (value-agnostic).
        for tok in cfg.get("ls", []):
            if not re.search(r"--ls-" + re.escape(tok) + r": *\S", text):
                failures.append(f"{name}  MISSING :root token --ls-{tok} (the letter-spacing scale source of truth)")
        for tok in cfg.get("lh", []):
            if not re.search(r"--lh-" + re.escape(tok) + r": *\S", text):
                failures.append(f"{name}  MISSING :root token --lh-{tok} (the line-height scale source of truth)")

        # ══ v2133 — THE HINT LANE HAS A TYPE FLOOR, AND NOTHING WAS CHECKING IT ══════════════════
        # The board's prose tooltip shipped on --fs-meta (a flat 11px) while the console's twin sits
        # on --fs-2xs = clamp(13px,1vw,15px) — 14.4px at 1440. #tvd-eng loads the BOARD inside the
        # CONSOLE, so with the shell open both are on one screen: a 14.4px hint above an 11px one,
        # the same sentence in two sizes. That is the "does not look like this console" complaint
        # the whole tooltip arc exists to answer, reintroduced by the fix for it.
        #
        # ⚠ NO EXISTING GATE COULD SEE IT, and that is the reason this check is here rather than a
        # note: TestV1504TypeFloor is console-ONLY by construction (its 13px mandate is written for
        # a fullscreen surface), and everything else in this file locks weight, structure, ls/lh and
        # the grail wall's colours — never SIZE. The board simply had no type floor to fail, so
        # `rc 0` was honest and blind at the same time. [[gate-blind-to-unexercised-input]]
        for sel, floor in cfg.get("typeFloor", []):
            m = re.search(re.escape(sel) + r"\s*\{[^}]*?font-size:\s*var\(\s*(--[a-z0-9-]+)\s*\)", text, re.S)
            if not m:
                failures.append(f"{name}  {sel} no longer sets font-size from a token — a raw value "
                                f"here is how the two hint lanes drifted apart in the first place")
                continue
            tok = m.group(1)
            tv = re.search(re.escape(tok) + r":\s*([^;]+);", text)
            if not tv:
                failures.append(f"{name}  {sel} reads {tok}, which :root does not define")
                continue
            raw = tv.group(1)
            # a clamp()'s FLOOR is its first argument; a flat value is its own floor
            px = re.search(r"clamp\(\s*([0-9.]+)px", raw) or re.search(r"([0-9.]+)px", raw)
            if not px:
                failures.append(f"{name}  {sel} reads {tok} = {raw.strip()!r}, which is not a px floor")
                continue
            got = float(px.group(1))
            if got < floor:
                failures.append(f"{name}  {sel} resolves to {got:g}px via {tok} — below the {floor:g}px "
                                f"hint floor the CONSOLE twin holds. The board is iframed INTO the "
                                f"console, so this puts the same sentence on one screen in two sizes")
    return failures


def _safe_console():
    """v1478 — a gate that cannot REPORT is a broken gate.

    This machine's console is Hebrew (cp1255). The check passed, reached the success branch, then
    died inside `print("✅ ...")` with UnicodeEncodeError -> exit 1. A plain run of a CLEAN tree
    reported RED, and had done so every time it was not run with PYTHONIOENCODING set by hand.
    Same failure mode as REG-054: the gate's verdict depended on the operator's shell, not the code.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main():
    _safe_console()
    failures = check()
    if failures:
        print("❌ VISUAL-LOCK DRIFT — the type system moved (%d issue%s):"
              % (len(failures), "" if len(failures) == 1 else "s"))
        for f in failures:
            print("   • " + f)
        # v2073 — ADVICE THAT MATCHES THE FAILURE. This footer printed weight advice under every
        # drift, including the colour checks added the same day — telling him to swap a
        # font-weight token when what broke was a rarity colour. A right instruction under the
        # wrong failure is worse than none: it sends the reader to the wrong file.
        if any("rarity" in f or "green" in f or "gold" in f or "colour" in f for f in failures):
            print("\nFix (colour): an item name carries MEANING in its colour — set pieces read "
                  "var(--q-set), uniques var(--q-unique). Restore the rarity class _allGrid stamps "
                  "and the binding under .gf-piece. See the visual-regression-detector skill.")
        # ⚠ MATCH THE MARKER, NOT THE PROSE. This read `"weight" in f`, and the size failure's own
        # explanation contains the phrase "exactly as every weight must be a var(--fw-*) one" — so
        # planting a raw font-size printed the font-weight fix note. A matcher that greps a message
        # for a word will be triggered by any sentence that happens to use it, including one I wrote
        # myself two functions away. [[source-reading-guard]] [[feedback-comments-vs-code]]
        if any("RAW weight" in f or "RAW shorthand" in f for f in failures):
            print("\nFix (weight): replace each raw font-weight:NNN with its token "
                  "(400=regular 500=normal 600=medium 700=semibold 800=bold 900=black), "
                  "e.g. font-weight:var(--fw-semibold). See LOCKED_TYPE_SYSTEM.md.")
        if any("raw font-size" in f for f in failures):
            print("\nFix (size): every size on tv/control_ui.html must be a var(--fs-*) token. "
                  "⚠ an em is NOT a lookup — .78em is 78% of whatever its parent computes to, so "
                  "swapping it for a token changes the rendered size SILENTLY. Render 1440/1120/"
                  "901/375 before and after and COMPARE. See SIZE_GRANDFATHERED for the 19 that "
                  "predate this lock, each named.")
        return 1
    print("✅ VISUAL-LOCK OK — 0 raw font-weight literals in both surfaces; "
          "--fw-* intact; console --hd-* structure rhythm + --ls-*/--lh-* scales defined "
          "(both surfaces share one vocabulary). Weight, structure, spacing + line-height are all locked. "
          "SIZE-LOCK: the console admits no raw font-size beyond %d capped values (%d sites), and "
          "bible.html is under a debt RATCHET of %d recorded values — new values refused, existing "
          "ones may only shrink. Both cover the `font:` shorthand's size slot."
          % (len(CONSOLE_SIZES), sum(c for c, _ in CONSOLE_SIZES.values()), _debt_size()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
