#!/usr/bin/env python3
"""THE MAP OF THIS SYSTEM, GENERATED FROM THE CODE SO IT CANNOT GO STALE.

★ Konyo: "we had a previous achilles project that we worked on with obsidian and we used blueprints
and reverse blueprints and DIAGRAM examples for future sessions and future and other LLMs working
on this repo. is there a way you can check it and also integrate that system maybe not exactly just
harness and extract whats needed for our current workflow".

WHAT WAS HARVESTED FROM ~/achilles-revival, and what was deliberately left there:

  TAKEN — the blueprint is GENERATED, not written. kai_blueprint_generator.py extracts routes and
          engines from the source after every backup, so the map cannot drift from the code. A
          hand-written architecture doc is out of date the first time anyone edits anything, and
          the version that is confidently wrong is worse than none.
  TAKEN — the REVERSE-blueprint doctrine, verbatim from KAI_REVERSE_BLUEPRINT.md: "Normal blueprint
          = design first, build after. Reverse-blueprint = audit what exists, map it truthfully,
          fix what's wrong... NEVER guess. ALWAYS trace." That is the discipline this repo already
          runs on; naming it makes it inheritable.
  LEFT   — the supervisord/SSH/proxy80 topology. That is Achilles' shape, not this one. Copying a
          reference's structure instead of its METHOD is how a map starts describing the wrong
          building. [[copy-drift]]

⚠ IT REPORTS, IT DOES NOT ASSERT. Every number here is counted from the tree at the moment it runs.
Where something cannot be counted it says so rather than printing a zero, because "0 lanes" and "I
could not read the lanes" are opposite facts. [[unknown-stays-unknown]]
"""
import io
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, "BLUEPRINT.md")


def _src(name):
    try:
        with io.open(os.path.join(HERE, name), encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except Exception:
        return ""


def _code_only(s):
    s = re.sub(r'"""(.*?)"""', "", s, flags=re.S)
    s = re.sub(r"'''(.*?)'''", "", s, flags=re.S)
    return re.sub(r"#[^\n]*", "", s)


def capture_doors():
    """The three ways a recording starts, and which checks each performs at its own door."""
    src = _code_only(_src("control_app.py"))
    if not src:
        return None
    doors = {}
    for door, anchor in (("ON AIR", '"/api/on":'), ("MINI", "def mini_start("),
                         ("shadow", "def shadow_watch_tick(")):
        i = src.find(anchor)
        if i < 0:
            doors[door] = None
            continue
        j = src.find("\ndef ", i + 10)
        body = src[i:j if j > 0 else i + 6000]
        doors[door] = {
            "preflight": "capture_preflight(" in body,
            "grant": "screenRecOk" in body,
            "ledger": "_capture_door_note(" in body,
            "floor": "ON_AIR_FLOOR_GB" in body,
        }
    return doors


def lanes():
    """Background loops — what runs without him touching anything."""
    src = _src("control_app.py")
    if not src:
        return None
    out = []
    for m in re.finditer(r"\ndef (_?[a-z_]*loop[a-z_]*)\(", src):
        name = m.group(1)
        j = src.find("\ndef ", m.start() + 1)
        body = src[m.start():j if j > 0 else m.start() + 2500]
        every = re.findall(r"time\.sleep\(([A-Z_0-9a-z\.]+)\)", body)
        out.append((name, ", ".join(every[:2]) or "?"))
    return sorted(out)


def ledgers():
    """Durable state this system keeps, and whether it exists yet."""
    out = []
    for f, why in (("capture_doors.json", "per-door Wilson: reels opened vs reels that held film"),
                   ("retro_gate.json", "every retro read graded on what / where / how"),
                   ("main_character.json", "what he wears, learned from repeated sightings"),
                   ("shadow_watch.json", "when the shadow watcher last looked, and what it saw"),
                   ("vault_seen.json", "vault sightings"),
                   ("chronicle_swept.json", "which reels the chronicle lane has read")):
        p = os.path.join(HERE, f)
        out.append((f, why, os.path.exists(p),
                    (os.path.getsize(p) if os.path.exists(p) else 0)))
    return out


def readers():
    """The two game readers and the surfaces they are declared to serve."""
    try:
        sys.path.insert(0, HERE)
        import surfaces as S
        rows = []
        for name, v in sorted(S.SURFACES.items()):
            e = v.get("enlarge") or ()
            rows.append((name, v.get("reader"), v.get("anchor"),
                         (e[0] if e else "-"), bool(v.get("tooltip"))))
        return rows
    except Exception:
        return None


def wilson_lanes():
    """Everywhere the same statistic is used, so nobody hand-rolls a fourth ratio."""
    out = []
    for f in sorted(os.listdir(HERE)):
        if not f.endswith(".py") or f.startswith("test_"):
            continue
        c = _code_only(_src(f))
        n = len(re.findall(r"\bwilson_lower\s*\(", c))
        if n:
            out.append((f, n))
    return out


def rulings():
    """HIS OWN WORDS, collected from the comments that already quote them. -> {file: [quote, ...]}

    ★ Konyo: "my brain is still processing everything when i start and look from bottom and up i
    keep reminding you :). but its fine its getting annoying to do lol the puzzle is fun but the
    complication is frustrating. so we need to organize and make it clearer".

    MEASURED: 752 quoted rulings across 75 files. His decision history is already IN this tree —
    every real change here carries the sentence that caused it — and it has never been collected,
    which is why he keeps having to say things twice.

    ⚠ THIS IS AN INDEX, NOT AN ARCHIVE. Dumping 752 fragments would swap one kind of overwhelm for
    another. It keeps a few per file so a session reading about a subsystem sees HIS words about
    THAT subsystem, and knows to open the file for the rest. The code stays the source; this is a
    way in.
    """
    import re as _re
    pat = _re.compile(r'(?:Konyo|his words|He ruled|his ruling)\s*[,:]?\s*["\u201c\u2018\']'
                      r'(.{25,170})', _re.I)
    out = {}
    for f in sorted(os.listdir(HERE)):
        if not (f.endswith(".py") or f.endswith(".html")) or f.startswith("test_"):
            continue
        txt = _src(f)
        if not txt:
            continue
        seen, keep = set(), []
        for m in pat.finditer(txt):
            q = " ".join(m.group(1).split()).strip(' "\u201c\u201d\'')
            q = q.split("  ")[0]
            k = q[:40].lower()
            if len(q) < 25 or k in seen:
                continue
            seen.add(k)
            keep.append(q[:150])
            if len(keep) >= 3:
                break
        if keep:
            out[f] = keep
    return out


def gate_count():
    src = _src("run_gates.py")
    return len(re.findall(r"\n    Gate\(", src)) if src else None


def render():
    L = []
    A = L.append
    A("# TV DIABLO — BLUEPRINT")
    A("")
    A("GENERATED by `tv/blueprint.py` from the code in this tree. Do not hand-edit: regenerate it.")
    A("A hand-written map is out of date the first time anyone edits anything, and the version that")
    A("is confidently wrong is worse than no map at all.")
    A("")
    A("    generated %s" % time.strftime("%Y-%m-%d %H:%M"))
    A("")
    A("## THE REVERSE-BLUEPRINT RULE (inherited from ~/achilles-revival)")
    A("")
    A("> Normal blueprint = design first, build after.")
    A("> Reverse-blueprint = audit what exists, map it truthfully, fix what's wrong.")
    A("> **NEVER guess. ALWAYS trace.**")
    A("")
    A("Trace, then change. In one session this rule killed three of my own confident diagnoses:")
    A("the reel size was not the lag, the PNG encoder was not on the primary path, and the tooltip")
    A("cropper was not starved of readers. Each was plausible and each was wrong, and the")
    A("measurement is what said so.")
    A("")
    A("## THE ARCHITECTURE — why every reading is read twice")
    A("")
    A("Konyo, after a defect I reported turned out not to be one: \"this is exactly why LAWS and")
    A("engines are built and secondary accuracy verifiers need and are built — whatever is gapped")
    A("needs to be added and integrated ... we need it properly architectured\".")
    A("")
    A("THE CASE THAT PROVES IT. A register said an item sat at loc=floor. I called that a WHERE")
    A("defect and said it belonged in his stash. Rendering the frame showed RUNE GRIP / RING as a")
    A("FLOOR DROP LABEL in the Rogue Encampment — no tooltip, no stash. The reader was right and")
    A("the reviewer was wrong, and only a SECOND, DIFFERENT look settled it.")
    A("")
    A("So nothing here trusts a single reading. Four independent kinds of check, and each answers a")
    A("question the others cannot:")
    A("")
    A("    LAW          needs no evidence at all. The Horadric Cube is furniture whether or not")
    A("                 anything has ever seen it. tv/inventory_law.py")
    A("    EVIDENCE     needs repetition, and refuses to conclude from thin data. Wilson, not a raw")
    A("                 ratio: 3-for-3 scores 0.438, not 1.00. tv/confidence.py, six lanes")
    A("    CONTRADICTION  two engines that must agree, asserted continuously. When they part, THAT")
    A("                 is the finding — never averaged. tv/corroborate.py")
    A("    A SECOND READ  the same frame read a second way, graded on WHAT it named, WHERE it")
    A("                 placed it and HOW it read it. tv/retro_gate.py")
    A("")
    A("And one rule underneath all four: an UNMEASURED thing stays unmeasured. `None` is not `0`.")
    A("\"nobody looked\" and \"we looked and found nothing\" are opposite facts, and every ledger")
    A("here keeps them apart.")
    A("")
    A("## CAPTURE — three doors into ONE recording")
    A("")
    A("A MINI *is* the live session wearing a focus and a deadline; all three doors spawn through")
    A("the same `start_agent()`. They differ only in what they check at their own door.")
    A("")
    d = capture_doors()
    if d is None:
        A("    (control_app.py could not be read — the doors are UNKNOWN, not absent)")
    else:
        A("    door      preflight  grant  door-ledger  floor")
        for k, v in d.items():
            if v is None:
                A("    %-9s (not found in the source)" % k)
            else:
                A("    %-9s %-10s %-6s %-12s %s"
                  % (k, v["preflight"], v["grant"], v["ledger"], v["floor"]))
    A("")
    A("## LANES — what runs without him pressing anything")
    A("")
    ln = lanes()
    if ln is None:
        A("    (UNKNOWN — control_app.py could not be read)")
    else:
        for name, every in ln:
            A("    %-26s every %s" % (name, every))
    A("")
    A("## READERS AND SURFACES")
    A("")
    A("Two readers, two coordinate laws, and they are NOT interchangeable: the difference is")
    A("geometry, not preference.")
    A("")
    r = readers()
    if r is None:
        A("    (UNKNOWN — surfaces.py could not be imported)")
    else:
        A("    surface            reader              anchor   enlarge            tooltip")
        for name, rd, anc, enl, tip in r:
            A("    %-18s %-19s %-8s %-18s %s" % (name, rd, anc, enl, tip))
    A("")
    A("## LEDGERS — the durable memory")
    A("")
    for f, why, exists, size in ledgers():
        A("    %-24s %-6s %8s  %s"
          % (f, ("live" if exists else "empty"), (("%d B" % size) if exists else "-"), why))
    A("")
    A("## WILSON — one statistic, every lane that scores itself")
    A("")
    for f, n in wilson_lanes():
        A("    %-24s x%d" % (f, n))
    A("")
    A("## HIS RULINGS, BY SUBSYSTEM")
    A("")
    A("Collected from the comments that already quote him — every real change in this tree carries")
    A("the sentence that caused it. This is an INDEX: a few per file, so you know which file holds")
    A("his words on a subject. The code stays the source.")
    A("")
    rl = rulings()
    A("    %d file(s) carry his words" % len(rl))
    A("")
    for f in sorted(rl):
        A("    %s" % f)
        for q in rl[f]:
            A('        "%s"' % q)
    A("")
    A("## GATES")
    A("")
    g = gate_count()
    A("    %s registered in tv/run_gates.py" % (g if g is not None else "UNKNOWN"))
    A("")
    return "\n".join(L) + "\n"


def main(argv=None):
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    txt = render()
    argv = argv or []
    if "--print" in argv:
        print(txt)
        return 0
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(txt)
    print("wrote %s (%d lines)" % (OUT, txt.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
